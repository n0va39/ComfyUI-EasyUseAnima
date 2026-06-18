import json
import os
import unittest
from unittest.mock import patch

from nodes import EasyUseAnimaLoraPreset


class LoraPresetTests(unittest.TestCase):
    def test_lora_preset_uses_selected_profile(self):
        profile_data = json.dumps({
            "1": {
                "style_prompt": "@profile_one",
                "loras": [
                    {"name": "profile_one_lora", "strength": 0.4, "clipStrength": 0.4, "active": True}
                ],
            },
            "2": {
                "style_prompt": "@profile_two",
                "loras": [
                    {"name": "profile_two_lora", "strength": 0.7, "clipStrength": 0.5, "active": True}
                ],
            },
        })

        with (
            patch("nodes._get_lora_info", lambda name: (f"loras/{name}.safetensors", [f"{name} trigger"])),
            patch("nodes._apply_lora_syntax_format", lambda name: name),
        ):
            result = EasyUseAnimaLoraPreset().build(
                style_prompt="@visible",
                profile_index=2,
                profile_count=4,
                lora_name="None",
                loras=[],
                profile_data=profile_data,
            )

        self.assertEqual(result, (
            "@profile_two",
            [(f"loras{os.sep}profile_two_lora.safetensors", 0.7, 0.5)],
            "profile_two_lora trigger",
            "<lora:profile_two_lora:0.7:0.5>",
            2,
        ))

    def test_lora_preset_uses_loras_widget_when_profile_has_no_loras(self):
        with (
            patch("nodes._get_lora_info", lambda name: (f"loras/{name}.safetensors", [])),
            patch("nodes._apply_lora_syntax_format", lambda name: name),
        ):
            result = EasyUseAnimaLoraPreset().build(
                style_prompt="@artist",
                profile_index=1,
                profile_count=4,
                lora_name="None",
                loras=json.dumps([{"name": "test_lora", "strength": 1.2, "clipStrength": 1.2, "active": True}]),
                profile_data="{}",
            )

        self.assertEqual(result[0], "@artist")
        self.assertEqual(result[1], [(f"loras{os.sep}test_lora.safetensors", 1.2, 1.2)])
        self.assertEqual(result[3], "<lora:test_lora:1.2>")
        self.assertEqual(result[4], 1)

    def test_lora_preset_wraps_profile_index_by_profile_count(self):
        profile_data = json.dumps({
            "1": {
                "name": "First",
                "style_prompt": "@profile_one",
                "loras": [],
            },
            "2": {
                "name": "Second",
                "style_prompt": "@profile_two",
                "loras": [],
            },
        })

        result = EasyUseAnimaLoraPreset().build(
            style_prompt="@visible",
            profile_index=9,
            profile_count=2,
            lora_name="None",
            loras=[],
            profile_data=profile_data,
        )

        self.assertEqual(result[0], "@profile_one")
        self.assertEqual(result[4], 1)


if __name__ == "__main__":
    unittest.main()
