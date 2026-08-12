from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from easyuse_anima.aio import prompt_lora
from easyuse_anima.lora import prompt_syntax
from easyuse_anima.nodes.aio_nodes import EasyUseAnimaAIOGenerator
from easyuse_anima.nodes.prompt_advanced_nodes import (
    EasyUseAnimaPromptStudioAdvanced,
    EasyUseAnimaPromptStudioAdvancedV2,
)
from easyuse_anima.nodes.prompt_lora_nodes import EasyUseAnimaPromptStudioAdvancedLora
from easyuse_anima.nodes.wildcard_nodes import (
    EasyUseAnimaWildcard,
    EasyUseAnimaWildcardLora,
)
from easyuse_anima.registration import NODE_CLASS_MAPPINGS
from easyuse_anima.settings import repository as settings_repository
from easyuse_anima.settings import service as settings_service
from easyuse_anima.settings.schema import (
    COMFY_SETTING_KEYS,
    DEFAULT_SETTINGS,
    PROMPT_STUDIO_COLOR_KEYS,
)


ROOT = Path(__file__).resolve().parents[1]


def _field(
    field_id: str,
    text: str,
    *,
    pane: str = "positive",
    field_type: str = "general",
    enabled: bool = True,
) -> dict[str, object]:
    return {
        "id": field_id,
        "pane": pane,
        "type": field_type,
        "label": field_id,
        "text": text,
        "height": 72,
        "enabled": enabled,
    }


def _advanced_build_kwargs(fields: list[dict[str, object]]) -> dict[str, object]:
    return {
        "use_naia": False,
        "consume_naia_on_queue": True,
        "use_anima_mod_guidance": False,
        "pin_trigger_tags_to_front": False,
        "advanced_fields": json.dumps(fields),
        "wildcard_mode": "일반",
        "wildcard_seed": 7,
        "wildcard_seed_after_generate": "fixed",
    }


class A1111LoraPromptSyntaxTests(unittest.TestCase):
    def test_parser_removes_valid_tags_and_preserves_order(self):
        cleaned, directives = prompt_syntax._parse_a1111_lora_tags(
            "subject, <lora:styles/first:0.75>, detail <<LORA:second:-1.25:0.4>"
        )

        self.assertEqual(cleaned, "subject, detail")
        self.assertEqual(
            directives,
            [
                {
                    "name": "styles/first",
                    "strength_model": 0.75,
                    "strength_clip": 0.75,
                },
                {
                    "name": "second",
                    "strength_model": -1.25,
                    "strength_clip": 0.4,
                },
            ],
        )

    def test_parser_leaves_malformed_and_unrelated_angle_text_unchanged(self):
        source = (
            "subject, <lora:missing_weight>, <lora:model:not-a-number>, "
            "<embedding:name>, <lora::1.0>"
        )

        self.assertEqual(prompt_syntax._parse_a1111_lora_tags(source), (source, []))

    def test_parser_does_not_confuse_angle_pipe_tags_with_lora_syntax(self):
        source = "<|> <|>, <|start_of_text|> subject <|end_of_text|>"

        self.assertEqual(prompt_syntax._parse_a1111_lora_tags(source), (source, []))

    def test_field_extraction_only_reads_enabled_positive_fields(self):
        fields, directives = prompt_syntax._extract_a1111_loras_from_fields(
            [
                _field("positive", "subject, <lora:active:0.5>"),
                _field("negative", "bad, <lora:negative:0.7>", pane="negative"),
                _field("disabled", "<lora:disabled:0.9>", enabled=False),
            ]
        )

        self.assertEqual(fields[0]["text"], "subject")
        self.assertIn("<lora:negative:0.7>", fields[1]["text"])
        self.assertIn("<lora:disabled:0.9>", fields[2]["text"])
        self.assertEqual([item["name"] for item in directives], ["active"])

    def test_filename_resolution_prefers_relative_path_then_unique_basename(self):
        inventory = [
            "styles/detail.safetensors",
            "characters/hero.safetensors",
        ]

        self.assertEqual(
            prompt_syntax._resolve_a1111_lora_name("styles/detail", inventory),
            "styles/detail.safetensors",
        )
        self.assertEqual(
            prompt_syntax._resolve_a1111_lora_name("hero", inventory),
            "characters/hero.safetensors",
        )

    def test_filename_resolution_rejects_ambiguous_or_missing_names(self):
        inventory = [
            "one/shared.safetensors",
            "two/shared.safetensors",
        ]

        with self.assertRaisesRegex(RuntimeError, "ambiguous"):
            prompt_syntax._resolve_a1111_lora_name("shared", inventory)
        with self.assertRaisesRegex(RuntimeError, "was not found"):
            prompt_syntax._resolve_a1111_lora_name("missing", inventory)

    def test_prompt_data_merge_does_not_parse_raw_positive_text(self):
        prompt_data = {
            "positive_prompt": "subject, <lora:raw_only:1.0>",
            "lora": {
                "syntax": "a1111",
                "directives": [
                    {
                        "name": "structured",
                        "strength_model": 0.6,
                        "strength_clip": 0.6,
                    }
                ],
            },
        }

        merged = prompt_syntax._merge_prompt_data_lora_stack(
            [("base.safetensors", 0.8, 0.7)],
            prompt_data,
            ["raw_only.safetensors", "structured.safetensors"],
        )

        self.assertEqual(
            merged,
            [
                ("base.safetensors", 0.8, 0.7),
                ("structured.safetensors", 0.6, 0.6),
            ],
        )
        self.assertNotIn("raw_only.safetensors", [item[0] for item in merged])

    def test_aio_adapter_preserves_stack_until_structured_loras_require_merge(self):
        sentinel_stack = object()
        plain_prompt_data = {"fields": []}

        normalized, effective_stack = prompt_lora._prepare_aio_prompt_loras(
            plain_prompt_data,
            sentinel_stack,
            normalize_prompt_data=lambda value: value,
        )

        self.assertIs(normalized, plain_prompt_data)
        self.assertIs(effective_stack, sentinel_stack)

        structured_prompt_data = {
            "fields": [],
            "lora": {
                "syntax": "a1111",
                "directives": [
                    {
                        "name": "prompt-style",
                        "strength_model": 0.65,
                        "strength_clip": 0.45,
                    }
                ],
            },
        }
        with patch.object(
            prompt_syntax,
            "_lora_combo_values",
            return_value=["None", "styles/prompt-style.safetensors"],
        ):
            _, effective_stack = prompt_lora._prepare_aio_prompt_loras(
                structured_prompt_data,
                [("base.safetensors", 0.9, 0.8)],
                normalize_prompt_data=lambda value: value,
            )

        self.assertEqual(
            effective_stack,
            [
                ("base.safetensors", 0.9, 0.8),
                (os.path.join("styles", "prompt-style.safetensors"), 0.65, 0.45),
            ],
        )

    def test_lora_autocomplete_setting_is_public_and_color_is_configurable(self):
        self.assertEqual(DEFAULT_SETTINGS["prompt_studio.lora_autocomplete"], "true")
        self.assertEqual(
            COMFY_SETTING_KEYS["EasyUseAnima.Prompt.LoraAutocomplete"],
            "prompt_studio.lora_autocomplete",
        )
        self.assertIn("lora", PROMPT_STUDIO_COLOR_KEYS)
        with patch.object(settings_service, "get_settings", return_value={}):
            self.assertEqual(
                settings_service.public_settings()[
                    "prompt_studio.lora_autocomplete"
                ],
                "true",
            )


class LoraPromptNodeIntegrationTests(unittest.TestCase):
    def test_advanced_v2_writes_clean_prompt_and_structured_lora_data(self):
        fields = [
            _field(
                "positive",
                "subject, {<lora:style:0.5>|<lora:other:0.6>}",
            ),
            _field(
                "negative",
                "bad anatomy, <lora:negative_is_text:0.4>",
                pane="negative",
            ),
        ]

        output = EasyUseAnimaPromptStudioAdvancedV2().build(
            **_advanced_build_kwargs(fields)
        )
        prompt_data = output["result"][0]

        self.assertNotIn("<lora:", prompt_data["positive_prompt"].lower())
        self.assertIn("<lora:negative_is_text:0.4>", prompt_data["negative_prompt"])
        self.assertEqual(prompt_data["lora"]["syntax"], "a1111")
        self.assertEqual(len(prompt_data["lora"]["directives"]), 1)
        self.assertIn(
            prompt_data["lora"]["directives"][0]["name"],
            {"style", "other"},
        )
        self.assertIn("<lora:", prompt_data["saved_fields"][0]["text"].lower())
        self.assertNotIn("<lora:", prompt_data["fields"][0]["text"].lower())
        self.assertNotIn(
            "<lora:",
            prompt_data["outputs"]["positive_prompt"].lower(),
        )

    def test_advanced_v2_applies_lora_emitted_by_file_wildcard_through_aio(self):
        source = "subject, __prompt_lora__"
        fields = [_field("positive", source)]
        input_stack = [("base.safetensors", 0.9, 0.8)]

        with tempfile.TemporaryDirectory() as temp:
            wildcard_root = Path(temp)
            (wildcard_root / "prompt_lora.txt").write_text(
                "<lora:styles/wildcard-style:0.7:0.4>\n",
                encoding="utf-8",
            )
            with (
                patch.object(
                    settings_repository,
                    "get_settings",
                    return_value={"wildcard.extra_paths": str(wildcard_root)},
                ),
                patch.object(
                    prompt_syntax,
                    "_lora_combo_values",
                    return_value=[
                        "None",
                        "styles/wildcard-style.safetensors",
                    ],
                ),
            ):
                output = EasyUseAnimaPromptStudioAdvancedV2().build(
                    **_advanced_build_kwargs(fields)
                )
                prompt_data = output["result"][0]
                normalized, effective_stack = prompt_lora._prepare_aio_prompt_loras(
                    prompt_data,
                    input_stack,
                    normalize_prompt_data=lambda value: value,
                )

        self.assertIs(normalized, prompt_data)
        self.assertEqual(prompt_data["saved_fields"][0]["text"], source)
        self.assertEqual(prompt_data["wildcard"]["used_keys"], ["prompt_lora"])
        self.assertEqual(prompt_data["positive_prompt"], "subject")
        self.assertEqual(prompt_data["fields"][0]["text"], "subject")
        self.assertEqual(
            prompt_data["lora"],
            {
                "syntax": "a1111",
                "directives": [
                    {
                        "name": "styles/wildcard-style",
                        "strength_model": 0.7,
                        "strength_clip": 0.4,
                    }
                ],
            },
        )
        self.assertEqual(
            effective_stack,
            [
                *input_stack,
                (
                    os.path.join("styles", "wildcard-style.safetensors"),
                    0.7,
                    0.4,
                ),
            ],
        )

    def test_advanced_lora_reuses_advanced_contract_and_appends_stack(self):
        fields = [
            _field(
                "positive",
                "subject, <lora:styles/detail:0.75:0.25>",
            )
        ]
        input_stack = [("base.safetensors", 0.9, 0.8)]

        with patch.object(
            prompt_syntax,
            "_lora_combo_values",
            return_value=["None", "styles/detail.safetensors"],
        ):
            output = EasyUseAnimaPromptStudioAdvancedLora().build(
                **_advanced_build_kwargs(fields),
                lora_stack=input_stack,
            )

        self.assertEqual(
            output["result"][:-1],
            (
                "subject",
                "",
                "",
                "",
                False,
                False,
                "subject",
                "",
                1024,
                1024,
            ),
        )
        self.assertEqual(
            output["result"][-1],
            [
                ("base.safetensors", 0.9, 0.8),
                (os.path.join("styles", "detail.safetensors"), 0.75, 0.25),
            ],
        )
        self.assertEqual(
            EasyUseAnimaPromptStudioAdvancedLora.RETURN_TYPES,
            (*EasyUseAnimaPromptStudioAdvanced.RETURN_TYPES, "LORA_STACK"),
        )
        self.assertEqual(
            EasyUseAnimaPromptStudioAdvancedLora.INPUT_TYPES()["optional"][
                "lora_stack"
            ][0],
            "LORA_STACK",
        )

    def test_wildcard_lora_keeps_populated_source_and_outputs_clean_text(self):
        source = "subject, <<lora:wild/style:0.4>"

        with patch.object(
            prompt_syntax,
            "_lora_combo_values",
            return_value=["None", "wild/style.safetensors"],
        ):
            output = EasyUseAnimaWildcardLora().generate(
                text=source,
                populated_text="",
                mode="일반",
                seed=3,
                lora_stack=[("base.safetensors", 1.0, 1.0)],
            )

        self.assertEqual(output["result"][0], "subject")
        self.assertEqual(output["ui"]["wildcard"][0]["populated_text"], source)
        self.assertEqual(
            output["result"][2],
            [
                ("base.safetensors", 1.0, 1.0),
                (os.path.join("wild", "style.safetensors"), 0.4, 0.4),
            ],
        )
        self.assertEqual(
            EasyUseAnimaWildcardLora.RETURN_TYPES,
            (*EasyUseAnimaWildcard.RETURN_TYPES, "LORA_STACK"),
        )

    def test_aio_change_key_tracks_structured_directives(self):
        context = {
            "schema": "easyuse_anima_input",
            "version": 1,
            "resource_info": {},
            "input_settings": {},
            "prompt_data": {
                "positive_prompt": "subject",
                "lora": {"syntax": "a1111", "directives": []},
            },
        }
        changed_context = json.loads(json.dumps(context))
        changed_context["prompt_data"]["lora"]["directives"].append(
            {
                "name": "style",
                "strength_model": 0.5,
                "strength_clip": 0.5,
            }
        )

        self.assertNotEqual(
            EasyUseAnimaAIOGenerator.IS_CHANGED(easy_use_anima_input=context),
            EasyUseAnimaAIOGenerator.IS_CHANGED(
                easy_use_anima_input=changed_context
            ),
        )

    def test_registration_and_frontend_aliases_cover_both_new_nodes(self):
        self.assertIs(
            NODE_CLASS_MAPPINGS["EasyUseAnimaPromptStudioAdvancedLora"],
            EasyUseAnimaPromptStudioAdvancedLora,
        )
        self.assertIs(
            NODE_CLASS_MAPPINGS["EasyUseAnimaWildcardLora"],
            EasyUseAnimaWildcardLora,
        )
        constants = (
            ROOT / "web" / "js" / "prompt_studio" / "constants.js"
        ).read_text(encoding="utf-8")
        hooks = (
            ROOT / "web" / "js" / "prompt_studio" / "node_hooks.js"
        ).read_text(encoding="utf-8")
        autocomplete = (
            ROOT / "web" / "js" / "easyuse_anima_autocomplete.js"
        ).read_text(encoding="utf-8")
        settings = (
            ROOT / "web" / "js" / "settings" / "definitions.js"
        ).read_text(encoding="utf-8")

        for node_id in (
            "EasyUseAnimaPromptStudioAdvancedLora",
            "EasyUseAnimaWildcardLora",
        ):
            self.assertIn(node_id, constants)
        self.assertIn("isWildcardNodeName(nodeName)", hooks)
        self.assertIn("EasyUseAnimaWildcardLora: new Set", autocomplete)
        self.assertIn("EasyUseAnima.Prompt.LoraAutocomplete", settings)
        self.assertIn('"EasyUseAnimaPromptStudioAdvancedV2"', autocomplete)
        self.assertIn('"EasyUseAnimaPromptStudioAdvancedLora"', autocomplete)


if __name__ == "__main__":
    unittest.main()
