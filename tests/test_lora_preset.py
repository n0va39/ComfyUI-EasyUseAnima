import json
import os
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from nodes import EasyUseAnimaLoraPreset, _lora_combo_values


def unwrap_result(response):
    return response["result"]


def unwrap_ui(response):
    return response["ui"]["lora_preset_profile"][0]


class LoraPresetTests(unittest.TestCase):
    def test_lora_combo_values_always_include_none_first(self):
        folder_paths = SimpleNamespace(
            get_filename_list=lambda _category: [
                "style/foo.safetensors",
                "None",
                "style/bar.safetensors",
            ]
        )

        with patch.dict(sys.modules, {"folder_paths": folder_paths}):
            values = _lora_combo_values()

        self.assertEqual(values[0], "None")
        self.assertEqual(values.count("None"), 1)
        self.assertIn("style/foo.safetensors", values)
        self.assertIn("style/bar.safetensors", values)

    def test_build_wraps_profile_index_and_outputs_enabled_loras(self):
        profile_data = {
            "1": {"name": "One", "style_prompt": "style one", "loras": []},
            "2": {
                "name": "Two",
                "style_prompt": "@artist",
                "loras": [
                    {"name": "style/foo.safetensors", "on": True, "strength": 0.75},
                    {"name": "style/off.safetensors", "on": False, "strength": 1.0},
                ],
            },
        }

        with (
            patch("nodes._get_lora_info", lambda name: (f"/loras/{name}", [f"{name}_trigger"])),
            patch("nodes._apply_lora_syntax_format", lambda name: name.replace(".safetensors", "")),
        ):
            response = EasyUseAnimaLoraPreset().build(
                style_prompt="fallback",
                profile_index=4,
                profile_count=2,
                lora_name="None",
                loras="[]",
                profile_data=json.dumps(profile_data),
            )

        result = unwrap_result(response)
        self.assertEqual(result[0], "@artist")
        self.assertEqual(result[1], [(os.path.join("style", "foo.safetensors"), 0.75, 0.75)])
        self.assertEqual(result[2], "style/foo.safetensors_trigger")
        self.assertEqual(result[3], "<lora:style/foo:0.75>")
        self.assertEqual(result[4], 2)
        self.assertEqual(unwrap_ui(response)["profile_index"], 2)

    def test_build_accepts_active_and_clip_strength_aliases(self):
        loras = [
            {"name": "foo.safetensors", "active": True, "strength": 1.0, "clipStrength": 0.5},
        ]

        with (
            patch("nodes._get_lora_info", lambda name: (name, [])),
            patch("nodes._apply_lora_syntax_format", lambda name: "foo"),
        ):
            response = EasyUseAnimaLoraPreset().build(
                style_prompt="style",
                profile_index=1,
                profile_count=1,
                lora_name="None",
                loras=json.dumps(loras),
                profile_data="{}",
            )

        result = unwrap_result(response)
        self.assertEqual(result[1], [("foo.safetensors", 1.0, 0.5)])
        self.assertEqual(result[3], "<lora:foo:1:0.5>")

    def test_build_outputs_relative_lora_stack_paths_for_absolute_inputs(self):
        loras_root = os.path.join("D:\\", "ComfyUI", "ComfyUI_main", "models", "loras")
        absolute_lora = os.path.join(loras_root, "style", "foo.safetensors")
        loras = [
            {"name": absolute_lora, "on": True, "strength": 0.8},
        ]

        with (
            patch("nodes._get_lora_info", lambda name: (name, [])),
            patch("nodes._apply_lora_syntax_format", lambda name: "foo"),
        ):
            response = EasyUseAnimaLoraPreset().build(
                style_prompt="style",
                profile_index=1,
                profile_count=1,
                lora_name="None",
                loras=json.dumps(loras),
                profile_data="{}",
            )

        result = unwrap_result(response)
        self.assertEqual(result[1], [(os.path.join("style", "foo.safetensors"), 0.8, 0.8)])

    def test_build_accepts_missing_internal_profile_count(self):
        response = EasyUseAnimaLoraPreset().build(
            style_prompt="style",
            profile_index=1,
            profile_count=None,
            lora_name="None",
            loras="[]",
            profile_data="{}",
        )

        result = unwrap_result(response)
        self.assertEqual(result[0], "style")
        self.assertEqual(result[4], 1)
        self.assertEqual(unwrap_ui(response)["profile_index"], 1)

    def test_build_ignores_legacy_hidden_lora_name_widget(self):
        response = EasyUseAnimaLoraPreset().build(
            style_prompt="style",
            profile_index=1,
            profile_count=1,
            lora_name="ANIMA_merge\\anima_SN0VA_Mix_BASE.safetensors",
            loras="[]",
            profile_data=json.dumps({"1": {"style_prompt": "style", "loras": []}}),
        )

        result = unwrap_result(response)
        self.assertEqual(result[1], [])
        self.assertEqual(result[2], "")
        self.assertEqual(result[3], "")

    def test_build_reports_missing_profile_lora_names(self):
        loras = [
            {"name": "style/missing_lora.safetensors", "on": True, "strength": 1.0},
            {"name": "style/disabled_missing.safetensors", "on": False, "strength": 1.0},
            {
                "name": "D:/ComfyUI/ComfyUI_main/models/loras/style/missing_abs.safetensors",
                "on": True,
                "strength": 0.5,
            },
        ]

        with patch("nodes._lora_model_exists", lambda _name: False):
            with self.assertLogs("ComfyUI-EasyUseAnima", level="ERROR") as logs:
                with self.assertRaises(RuntimeError) as raised:
                    EasyUseAnimaLoraPreset().build(
                        style_prompt="style",
                        profile_index=1,
                        profile_count=1,
                        lora_name="None",
                        loras=json.dumps(loras),
                        profile_data="{}",
                    )

        message = str(raised.exception)
        self.assertIn("LoRA Preset profile 1", message)
        self.assertIn("missing_lora.safetensors", message)
        self.assertIn("missing_abs.safetensors", message)
        self.assertIn("input: D:/ComfyUI/ComfyUI_main/models/loras/style/missing_abs.safetensors", message)
        self.assertNotIn("disabled_missing.safetensors", message)
        self.assertIn("missing_abs.safetensors", "\n".join(logs.output))

    def test_build_corrects_style_prompt_output(self):
        with patch("nodes._correct_style_prompt", lambda prompt: f"corrected: {prompt}"):
            response = EasyUseAnimaLoraPreset().build(
                style_prompt="@artist, style",
                profile_index=1,
                profile_count=1,
                lora_name="None",
                loras="[]",
                profile_data="{}",
            )

        result = unwrap_result(response)
        self.assertEqual(result[0], "corrected: @artist, style")

    def test_build_reads_lora_manager_metadata_trigger_words(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            lora_path = os.path.join(temp_dir, "foo.safetensors")
            metadata_path = os.path.join(temp_dir, "foo.metadata.json")
            with open(metadata_path, "w", encoding="utf-8") as handle:
                json.dump({"civitai": {"trainedWords": ["@foo", "@bar"]}}, handle)

            loras = [{"name": "style/foo.safetensors", "on": True, "strength": 1.0}]
            with (
                patch("nodes._fallback_lora_path", lambda _name: lora_path),
                patch("nodes._apply_lora_syntax_format", lambda name: "foo"),
            ):
                response = EasyUseAnimaLoraPreset().build(
                    style_prompt="style",
                    profile_index=1,
                    profile_count=1,
                    lora_name="None",
                    loras=json.dumps(loras),
                    profile_data="{}",
                )

        result = unwrap_result(response)
        self.assertEqual(result[2], "@foo, @bar")


if __name__ == "__main__":
    unittest.main()
