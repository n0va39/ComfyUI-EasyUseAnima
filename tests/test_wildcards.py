from __future__ import annotations

import tempfile
import unittest
import json
from pathlib import Path
from unittest.mock import patch

from nodes import (
    EasyUseAnimaPromptStudioAdvanced,
    EasyUseAnimaPromptStudioRegional,
    EasyUseAnimaWildcard,
)
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

    def test_extra_paths_are_parsed_one_path_per_line(self):
        self.assertEqual(
            wildcard_engine.parse_wildcard_extra_paths('D:/wildcards;E:/ignored\n"custom/wildcards"'),
            ["D:/wildcards;E:/ignored", "custom/wildcards"],
        )

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

    def test_random_multiselect_excludes_zero_weight_options_in_both_backends(self):
        numpy_module = wildcard_engine.np
        self.assertIsNotNone(numpy_module)

        for backend_name, backend in (("numpy", numpy_module), ("python", None)):
            with self.subTest(backend=backend_name), patch.object(wildcard_engine, "np", backend):
                result = expand_wildcards("{2$$0::zero|1::positive}", seed=0)

            self.assertEqual(result.text, "positive")

    def test_all_zero_weights_use_the_full_pool_deterministically_in_both_backends(self):
        numpy_module = wildcard_engine.np
        self.assertIsNotNone(numpy_module)
        source = "{5$$0::red|0::blue|0::green}"

        for backend_name, backend in (("numpy", numpy_module), ("python", None)):
            with self.subTest(backend=backend_name), patch.object(wildcard_engine, "np", backend):
                first = expand_wildcards(source, seed=7)
                second = expand_wildcards(source, seed=7)

            self.assertEqual(first.text, second.text)
            values = [part.strip() for part in first.text.split(",")]
            self.assertEqual(len(values), 3)
            self.assertEqual(set(values), {"red", "blue", "green"})

    def test_sequential_multiselect_keeps_zero_weight_candidates(self):
        result = expand_wildcards(
            "{3$$0::zero|1::positive}",
            seed=0,
            mode="순차",
        )

        self.assertEqual(result.text, "zero, positive")

    def test_malformed_count_ranges_preserve_the_original_expression(self):
        for source in (
            "{a-b$$red|blue}",
            "{1-x$$red|blue}",
            "{-x$$red|blue}",
            "{1-2-3$$red|blue}",
        ):
            with self.subTest(source=source):
                result = expand_wildcards(source, seed=0)

            self.assertEqual(result.text, source)
            self.assertFalse(result.changed)

    def test_list_wildcards_returns_relative_keys_only(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "style.txt").write_text("painterly\n", encoding="utf-8")

            items = list_wildcards(roots=[root])

        self.assertEqual(items, ["style"])

    def test_korean_wildcard_keys_can_be_listed_and_expanded(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "하츠.txt").write_text("hatsune option\n", encoding="utf-8")

            items = list_wildcards(roots=[root])
            result = expand_wildcards("__하츠__", seed=0, roots=[root])

        self.assertEqual(items, ["하츠"])
        self.assertEqual(result.text, "hatsune option")


class WildcardSeedContractTests(unittest.TestCase):
    def test_public_seed_controls_share_the_javascript_safe_range(self):
        public_max = wildcard_engine.PUBLIC_MAX_SEED

        self.assertEqual(public_max, (1 << 53) - 1)
        self.assertEqual(wildcard_engine.next_seed(0, "fixed"), 0)
        self.assertEqual(wildcard_engine.next_seed(public_max, "fixed"), public_max)
        self.assertEqual(wildcard_engine.next_seed(public_max, "increment"), 0)
        self.assertEqual(wildcard_engine.next_seed(0, "decrement"), public_max)
        self.assertEqual(
            wildcard_engine.next_seed(public_max, "decrement"),
            public_max - 1,
        )
        with patch("wildcard_engine.random.SystemRandom") as system_random:
            system_random.return_value.randrange.return_value = public_max

            self.assertEqual(
                wildcard_engine.next_seed(123, "randomize"),
                public_max,
            )

            system_random.return_value.randrange.assert_called_once_with(
                0,
                public_max + 1,
            )

    def test_legacy_uint64_seed_is_preserved_until_a_control_advances_it(self):
        public_max = wildcard_engine.PUBLIC_MAX_SEED
        legacy_max = wildcard_engine.MAX_SEED

        self.assertEqual(wildcard_engine.normalize_seed(legacy_max), legacy_max)
        self.assertEqual(wildcard_engine.normalize_seed(legacy_max + 1), legacy_max)
        self.assertEqual(wildcard_engine.next_seed(legacy_max, "fixed"), legacy_max)
        self.assertEqual(wildcard_engine.next_seed(legacy_max + 1, "fixed"), legacy_max)
        self.assertEqual(wildcard_engine.next_seed(legacy_max, "increment"), 0)
        self.assertEqual(
            wildcard_engine.next_seed(legacy_max, "decrement"),
            public_max - 1,
        )

    def test_node_inputs_advertise_public_range_without_rejecting_legacy_workflows(self):
        node_inputs = (
            (EasyUseAnimaWildcard, "seed"),
            (EasyUseAnimaPromptStudioAdvanced, "wildcard_seed"),
            (EasyUseAnimaPromptStudioRegional, "wildcard_seed"),
        )

        for node_class, input_name in node_inputs:
            with self.subTest(node=node_class.__name__):
                _input_type, config = node_class.INPUT_TYPES()["required"][input_name]
                self.assertEqual(config["max"], wildcard_engine.MAX_SEED)
                self.assertIn(str(wildcard_engine.PUBLIC_MAX_SEED), config["tooltip"])
                self.assertIn("legacy", config["tooltip"].lower())

    def test_all_wildcard_node_surfaces_publish_the_public_decrement_wrap(self):
        public_max = wildcard_engine.PUBLIC_MAX_SEED
        wildcard = EasyUseAnimaWildcard().generate(
            "",
            "",
            "일반 채우기",
            0,
            "decrement",
        )
        advanced = EasyUseAnimaPromptStudioAdvanced().build(
            False,
            True,
            False,
            False,
            "[]",
            wildcard_mode="일반 채우기",
            wildcard_seed=0,
            wildcard_seed_after_generate="decrement",
        )
        regional = EasyUseAnimaPromptStudioRegional().build(
            "[]",
            "{}",
            wildcard_mode="일반 채우기",
            wildcard_seed=0,
            wildcard_seed_after_generate="decrement",
        )

        self.assertEqual(wildcard["ui"]["wildcard"][0]["seed"], public_max)
        self.assertEqual(
            advanced["ui"]["prompt_studio_advanced"][0]["wildcard_seed"],
            public_max,
        )
        self.assertEqual(
            regional["ui"]["prompt_studio_regional"][0]["wildcard_seed"],
            public_max,
        )

    def test_legacy_current_seed_is_used_before_next_seed_reenters_public_range(self):
        legacy_max = wildcard_engine.MAX_SEED
        expansion = WildcardExpansionResult(
            text="expanded style",
            changed=True,
            used_keys=("style",),
            missing_keys=(),
        )

        with patch("nodes.expand_wildcards", return_value=expansion) as expand:
            result = EasyUseAnimaWildcard().generate(
                "__style__",
                "",
                "일반 채우기",
                legacy_max,
                "increment",
            )

        self.assertEqual(expand.call_args.kwargs["seed"], legacy_max)
        self.assertEqual(result["result"], ("expanded style", 0))


class WildcardNodeTests(unittest.TestCase):
    def test_native_wildcard_consumes_reserved_queue_seed_and_scrubs_token(self):
        reservation = json.dumps({
            "version": 1,
            "current_seed": 2,
            "next_seed": 47,
            "mode": "populate",
            "control": "randomize",
        })
        workflow_prompt = {
            "7": {
                "inputs": {
                    "text": "__style__",
                    "populated_text": "",
                    "mode": "일반 채우기",
                    "seed": 2,
                    "seed_after_generate": "randomize",
                    "easyuse_anima_reserved_wildcard_next_seed": reservation,
                }
            }
        }
        extra_pnginfo = {
            "workflow": {
                "nodes": [{
                    "id": 7,
                    "widgets_values": ["__style__", "", "일반 채우기", 2, "randomize"],
                }]
            }
        }

        with (
            patch(
                "nodes.expand_wildcards",
                return_value=WildcardExpansionResult(
                    text="expanded style",
                    changed=True,
                    used_keys=("style",),
                    missing_keys=(),
                ),
            ),
            patch("nodes.next_seed") as backend_next_seed,
        ):
            result = EasyUseAnimaWildcard().generate(
                "__style__",
                "",
                "일반 채우기",
                2,
                "randomize",
                workflow_prompt=workflow_prompt,
                extra_pnginfo=extra_pnginfo,
                unique_id="7",
                easyuse_anima_reserved_wildcard_next_seed=reservation,
            )

        backend_next_seed.assert_not_called()
        self.assertEqual(result["result"], ("expanded style", 47))
        self.assertEqual(result["ui"]["wildcard"][0]["seed"], 47)
        self.assertNotIn(
            "easyuse_anima_reserved_wildcard_next_seed",
            workflow_prompt["7"]["inputs"],
        )
        self.assertEqual(workflow_prompt["7"]["inputs"]["seed"], 2)
        self.assertEqual(extra_pnginfo["workflow"]["nodes"][0]["widgets_values"][3], 2)

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
                    "wildcard_seed_after_generate": "randomize",
                    "easyuse_anima_reserved_wildcard_next_seed": json.dumps({
                        "version": 1,
                        "current_seed": 2,
                        "next_seed": 47,
                        "mode": "populate",
                        "control": "randomize",
                    }),
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
                            "randomize",
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
                wildcard_seed_after_generate="randomize",
                workflow_prompt=workflow_prompt,
                extra_pnginfo=extra_pnginfo,
                unique_id="9",
                easyuse_anima_reserved_wildcard_next_seed=json.dumps({
                    "version": 1,
                    "current_seed": 2,
                    "next_seed": 47,
                    "mode": "populate",
                    "control": "randomize",
                }),
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
        self.assertNotIn(
            "easyuse_anima_reserved_wildcard_next_seed",
            workflow_prompt["9"]["inputs"],
        )
        self.assertEqual(extra_pnginfo["workflow"]["nodes"][0]["widgets_values"][11], 2)
        self.assertEqual(result["ui"]["prompt_studio_advanced"][0]["wildcard_seed"], 47)

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
