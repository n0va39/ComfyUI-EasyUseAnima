from __future__ import annotations

import tempfile
import unittest
import json
from pathlib import Path
from unittest.mock import patch

from nodes import EasyUseAnimaPromptStudioAdvanced, EasyUseAnimaWildcard
from settings import public_settings
import wildcard_engine
from wildcard_engine import (
    DEFAULT_TEST_WILDCARD_FILE,
    WildcardExpansionResult,
    ensure_default_wildcard_root,
    expand_wildcards,
    list_wildcards,
)


class WildcardEngineTests(unittest.TestCase):
    def test_default_root_is_created_with_test_wildcard(self):
        with tempfile.TemporaryDirectory() as temp:
            with patch.object(wildcard_engine, "USER_DATA_DIR", Path(temp)):
                root = ensure_default_wildcard_root()

                self.assertTrue(root.is_dir())
                self.assertEqual(root, Path(temp) / "wildcards")
                self.assertTrue((root / DEFAULT_TEST_WILDCARD_FILE).is_file())

    def test_dynamic_prompt_weight_prefixes_are_stripped(self):
        result = expand_wildcards("{0::a|1::b}", seed=0)

        self.assertEqual(result.text, "b")
        self.assertNotIn("::", result.text)

    def test_extra_roots_override_default_roots(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            extra = root / "extra"
            default = root / "default"
            extra.mkdir()
            default.mkdir()
            (extra / "style.txt").write_text("extra style\n", encoding="utf-8")
            (default / "style.txt").write_text("default style\n", encoding="utf-8")

            result = expand_wildcards("__style__", seed=0, roots=[extra, default])

        self.assertEqual(result.text, "extra style")
        self.assertEqual(result.used_keys, ("style",))

    def test_sequential_mode_uses_seed_modulo_option_count(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "color.txt").write_text("red\nblue\ngreen\n", encoding="utf-8")
            (root / "hair.txt").write_text("short hair\nlong hair\n", encoding="utf-8")

            result = expand_wildcards(
                "__color__, __hair__",
                seed=4,
                mode="순차",
                roots=[root],
            )

        self.assertEqual(result.text, "blue, short hair")

    def test_bare_wildcard_falls_back_to_nested_file_name(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            nested = root / "character"
            nested.mkdir()
            (nested / "hair.txt").write_text("black hair\n", encoding="utf-8")

            result = expand_wildcards("__hair__", seed=0, roots=[root])

        self.assertEqual(result.text, "black hair")

    def test_multiselect_can_expand_wildcard_options(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "color.txt").write_text("red\nblue\ngreen\n", encoding="utf-8")

            result = expand_wildcards("{2$$__color__}", seed=0, roots=[root])

        values = [part.strip() for part in result.text.split(",")]
        self.assertEqual(len(values), 2)
        self.assertEqual(len(set(values)), 2)

    def test_list_wildcards_returns_relative_keys_only(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "style.txt").write_text("painterly\n", encoding="utf-8")

            items = list_wildcards(roots=[root])

        self.assertEqual(items, ["style"])


class WildcardNodeTests(unittest.TestCase):
    def test_node_stores_reproduce_metadata_for_saved_workflow(self):
        workflow_prompt = {
            "7": {
                "inputs": {
                    "text": "__style__",
                    "populated_text": "",
                    "mode": "일반 채우기",
                    "seed": 5,
                    "seed_after_generate": "increment",
                }
            }
        }
        extra_pnginfo = {
            "workflow": {
                "nodes": [
                    {
                        "id": 7,
                        "widgets_values": ["__style__", "", "일반 채우기", 5, "increment"],
                    }
                ]
            }
        }

        with patch(
            "nodes.expand_wildcards",
            return_value=WildcardExpansionResult(
                text="expanded style",
                changed=True,
                used_keys=("style",),
                missing_keys=(),
            ),
        ):
            result = EasyUseAnimaWildcard().generate(
                "__style__",
                "",
                "일반 채우기",
                5,
                "increment",
                workflow_prompt=workflow_prompt,
                extra_pnginfo=extra_pnginfo,
                unique_id="7",
            )

        self.assertEqual(result["result"], ("expanded style", 6))
        self.assertEqual(workflow_prompt["7"]["inputs"]["populated_text"], "expanded style")
        self.assertEqual(workflow_prompt["7"]["inputs"]["mode"], "재현")
        self.assertEqual(workflow_prompt["7"]["inputs"]["seed"], 5)
        self.assertEqual(extra_pnginfo["workflow"]["nodes"][0]["widgets_values"][1], "expanded style")
        self.assertEqual(extra_pnginfo["workflow"]["nodes"][0]["widgets_values"][2], "재현")
        self.assertEqual(extra_pnginfo["workflow"]["nodes"][0]["widgets_values"][3], 5)

    def test_fixed_mode_expands_inline_multiselect(self):
        result = EasyUseAnimaWildcard().generate(
            "{2$$red|blue|green}",
            "",
            "고정",
            0,
            "fixed",
        )

        self.assertNotEqual(result["result"][0], "{2$$red|blue|green}")
        self.assertEqual(len([part.strip() for part in result["result"][0].split(",")]), 2)
        self.assertEqual(result["ui"]["wildcard"][0]["status"], "fixed")

    def test_public_settings_include_wildcard_extra_paths(self):
        self.assertIn("wildcard.extra_paths", public_settings())

    def test_prompt_studio_advanced_saves_reproduce_metadata_but_keeps_live_wildcard_text(self):
        fields = [
            {
                "id": "positive_general",
                "pane": "positive",
                "type": "general",
                "label": "General Tags",
                "text": "__style__",
                "height": 120,
                "enabled": True,
            }
        ]
        workflow_prompt = {
            "9": {
                "inputs": {
                    "advanced_fields": json.dumps(fields),
                    "wildcard_mode": "일반 채우기",
                    "wildcard_seed": 2,
                    "wildcard_seed_after_generate": "increment",
                }
            }
        }
        extra_pnginfo = {
            "workflow": {
                "nodes": [
                    {
                        "id": 9,
                        "widgets_values": [
                            False,
                            True,
                            False,
                            "1024",
                            "1024 * 1024 (1:1)",
                            1024,
                            1024,
                            False,
                            json.dumps(fields),
                            False,
                            "일반 채우기",
                            2,
                            "increment",
                        ],
                    }
                ]
            }
        }

        with patch(
            "nodes.expand_wildcards",
            return_value=WildcardExpansionResult(
                text="expanded style",
                changed=True,
                used_keys=("style",),
                missing_keys=(),
            ),
        ):
            result = EasyUseAnimaPromptStudioAdvanced().build(
                False,
                True,
                False,
                False,
                json.dumps(fields),
                wildcard_mode="일반 채우기",
                wildcard_seed=2,
                wildcard_seed_after_generate="increment",
                workflow_prompt=workflow_prompt,
                extra_pnginfo=extra_pnginfo,
                unique_id="9",
            )

        payload_fields = json.loads(result["ui"]["prompt_studio_advanced"][0]["advanced_fields"])
        saved_fields = json.loads(workflow_prompt["9"]["inputs"]["advanced_fields"])
        saved_image_fields = json.loads(extra_pnginfo["workflow"]["nodes"][0]["widgets_values"][8])

        self.assertEqual(result["result"][0], "expanded style")
        self.assertEqual(payload_fields[0]["text"], "__style__")
        self.assertEqual(saved_fields[0]["text"], "expanded style")
        self.assertEqual(saved_image_fields[0]["text"], "expanded style")
        self.assertEqual(workflow_prompt["9"]["inputs"]["wildcard_mode"], "재현")
        self.assertEqual(workflow_prompt["9"]["inputs"]["wildcard_seed"], 2)
        self.assertEqual(result["ui"]["prompt_studio_advanced"][0]["wildcard_seed"], 3)

    def test_prompt_studio_advanced_fixed_mode_expands_inline_multiselect(self):
        fields = [
            {
                "id": "positive_general",
                "pane": "positive",
                "type": "general",
                "label": "General Tags",
                "text": "{2$$red|blue|green}",
                "height": 120,
                "enabled": True,
            }
        ]

        result = EasyUseAnimaPromptStudioAdvanced().build(
            False,
            True,
            False,
            False,
            json.dumps(fields),
            wildcard_mode="고정",
            wildcard_seed=0,
            wildcard_seed_after_generate="fixed",
        )

        prompt = result["result"][0]
        self.assertNotEqual(prompt, "{2$$red|blue|green}")
        self.assertEqual(len([part.strip() for part in prompt.split(",")]), 2)
        self.assertEqual(result["ui"]["prompt_studio_advanced"][0]["wildcard_seed"], 0)


if __name__ == "__main__":
    unittest.main()
