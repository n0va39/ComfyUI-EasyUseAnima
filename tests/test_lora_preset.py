import json
import os
import tempfile
import unittest
from unittest.mock import patch

from nodes import EasyUseAnimaLoraPreset


def unwrap_result(response):
    return response["result"]


def unwrap_ui(response):
    return response["ui"]["lora_preset_profile"][0]


class LoraPresetTests(unittest.TestCase):
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
        self.assertEqual(result[1], [(os.path.join(os.sep, "loras", "style", "foo.safetensors"), 0.75, 0.75)])
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
