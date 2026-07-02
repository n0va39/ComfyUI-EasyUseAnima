from __future__ import annotations

import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import settings as easyuse_settings
from nodes import (
    ADVANCED_FIELDS_WORKFLOW_PROPERTY,
    ADVANCED_RESOLUTION_BUCKETS,
    DEFAULT_QUALITY_TAGS,
    DEFAULT_TRAILING_QUALITY_TAGS,
    PROMPT_DATA_SCHEMA,
    PROMPT_DATA_TYPE,
    EasyUseAnimaDetailerAlignHook,
    EasyUseAnimaPromptDataUnpack,
    EasyUseAnimaPromptBuilder,
    EasyUseAnimaPromptCorrector,
    EasyUseAnimaPromptStudio,
    EasyUseAnimaPromptStudioAdvanced,
    EasyUseAnimaPromptStudioAdvancedV2,
    EasyUseAnimaPromptStudioExtend,
    _clean_prompt,
    _prompt_tokens,
)
from autocomplete_dataset import (
    autocomplete_status,
    available_autocomplete_sources,
    classify_prompt_text,
    resolve_autocomplete_source,
    search_autocomplete,
)
from settings import (
    NAIA_PREPROCESSING_KEYS,
    public_settings,
    resolve_autocomplete_commit_key,
    resolve_autocomplete_limit,
    resolve_autocomplete_mode,
    resolve_lora_preset_menu_mode,
    resolve_lora_preset_strength_button_step,
    resolve_lora_preset_strength_drag_pixels,
    resolve_lora_preset_strength_drag_step,
    resolve_naia_resolution_bucket,
    resolve_naia_resolution_max_long_edge,
    resolve_naia_resolution_mode,
    resolve_naia_resolution_scale,
)


class PromptCorrectorTests(unittest.TestCase):
    def test_corrects_without_external_data(self):
        corrected, report = EasyUseAnimaPromptCorrector().correct(
            "long_hair, 1girl, long_hair",
            "",
            "",
        )

        self.assertEqual(corrected, "1girl, long hair")
        data = json.loads(report)
        self.assertEqual(data["duplicate_tags"], ["long hair"])

    def test_preserves_prompt_weight_syntax_and_escapes_literal_parentheses(self):
        corrected, report = EasyUseAnimaPromptCorrector().correct(
            "(long_hair:1.2), character_\\(series\\), 1girl, foo_(bar)",
            "",
            "",
        )

        self.assertEqual(
            corrected,
            "1girl, (long hair:1.2), character \\(series\\), foo \\(bar\\)",
        )
        data = json.loads(report)
        self.assertIn("long hair", data["unknown_tags"])
        self.assertIn("character \\(series\\)", data["unknown_tags"])

    def test_preserves_natural_language_case_and_splits_sentence_count_tag(self):
        corrected, report = EasyUseAnimaPromptCorrector().correct(
            (
                "(@akazawa kureha:0.35), "
                "An intelligent and neat girl with long silver hair. 1girl, "
                "(A highly aesthetic Pixiv style illustration, clean composition.:0.6)"
            ),
            "",
            "",
        )

        self.assertEqual(
            corrected,
            (
                "1girl, (@akazawa kureha:0.35), "
                "An intelligent and neat girl with long silver hair., "
                "(A highly aesthetic Pixiv style illustration, clean composition.:0.6)"
            ),
        )
        data = json.loads(report)
        self.assertEqual(data["sections"][0], "count")

    def test_prompt_correction_only_keeps_underscores_for_pony_scores(self):
        corrected, _report = EasyUseAnimaPromptCorrector().correct(
            "@artist_name, score 8, rating_safe, very_aesthetic",
            "",
            "",
        )

        self.assertEqual(corrected, "score_8, very aesthetic, rating safe, @artist name")

    def test_builtin_meta_quality_tags_are_known_without_external_data(self):
        corrected, report = EasyUseAnimaPromptCorrector().correct(
            "1girl, lowres, year_2024, rating_safe, score_7:, very_aesthetic, source_anime",
            "",
            "",
        )

        self.assertEqual(
            corrected,
            "score_7:, very aesthetic, lowres, source anime, year 2024, rating safe, 1girl",
        )
        data = json.loads(report)
        self.assertEqual(
            data["sections"],
            ["quality", "quality", "meta", "meta", "year", "safety", "count"],
        )
        self.assertEqual(data["unknown_tags"], [])

    def test_preserves_pony_score_underscores_in_positive_and_negative_outputs(self):
        corrected, _report = EasyUseAnimaPromptCorrector().correct(
            "1girl, score_8, score_7:, score 6",
            "",
            "",
        )

        self.assertEqual(corrected, "score_8, score_7:, score_6, 1girl")

        fields = [
            {
                "id": "positive_quality",
                "pane": "positive",
                "type": "quality",
                "label": "Quality Tags",
                "text": "score_8, score 7",
                "height": 72,
            },
            {
                "id": "negative_quality",
                "pane": "negative",
                "type": "quality",
                "label": "Quality Tags",
                "text": "score_5, score 4",
                "height": 72,
            },
        ]
        result = EasyUseAnimaPromptStudioAdvanced().build(
            False,
            True,
            False,
            False,
            json.dumps(fields),
        )

        (
            positive,
            negative,
            _quality,
            _negative_amg,
            _use_amg,
            _use_negative_amg,
            _metadata,
            metadata_negative,
            _width,
            _height,
        ) = result["result"]
        self.assertEqual(positive, "score_8, score_7")
        self.assertEqual(negative, "score_5, score_4")
        self.assertEqual(metadata_negative, "score_5, score_4")

    def test_manual_override_trigger_text_keeps_literal_underscores(self):
        corrected, report = EasyUseAnimaPromptCorrector().correct(
            "1girl, model_trigger, custom_lora_token",
            "model_trigger\ncustom_lora_token",
            "",
        )

        self.assertEqual(corrected, "1girl, model_trigger, custom_lora_token")
        data = json.loads(report)
        self.assertNotIn("model trigger", data["unknown_tags"])
        self.assertNotIn("custom lora token", data["unknown_tags"])


class PromptBuilderTests(unittest.TestCase):
    def test_prompt_builder_and_studio_default_quality_tags(self):
        builder_inputs = EasyUseAnimaPromptBuilder.INPUT_TYPES()["required"]
        studio_inputs = EasyUseAnimaPromptStudio.INPUT_TYPES()["required"]

        self.assertEqual(builder_inputs["quality_tags"][1]["default"], DEFAULT_QUALITY_TAGS)
        self.assertEqual(
            builder_inputs["trailing_quality_tags"][1]["default"],
            DEFAULT_TRAILING_QUALITY_TAGS,
        )
        self.assertEqual(studio_inputs["quality_tags"][1]["default"], DEFAULT_QUALITY_TAGS)
        self.assertEqual(
            studio_inputs["trailing_quality_tags"][1]["default"],
            DEFAULT_TRAILING_QUALITY_TAGS,
        )

    def test_builds_amg_prompt_and_metadata_prompt(self):
        prompt, quality, use_amg, metadata = EasyUseAnimaPromptBuilder().build(
            True,
            False,
            "masterpiece,, best quality\n",
            "@artist_name\nmodel_trigger",
            "lora trigger",
            "A Girl  with  Sword,, 1girl",
            "(high detail:0.6)",
        )

        self.assertTrue(use_amg)
        self.assertEqual(
            prompt,
            (
                "1girl, @artist_name, model_trigger, lora trigger, "
                "A Girl with Sword, (high detail:0.6)"
            ),
        )
        self.assertEqual(quality, "masterpiece, best quality")
        self.assertEqual(
            metadata,
            (
                "masterpiece, best quality, 1girl, @artist_name, model_trigger, "
                "lora trigger, A Girl with Sword, (high detail:0.6)"
            ),
        )

    def test_can_pin_trigger_tags_before_quality_tags(self):
        prompt, quality, use_amg, metadata = EasyUseAnimaPromptBuilder().build(
            False,
            True,
            "masterpiece",
            "@artist_name",
            "lora trigger",
            "1girl",
            "best quality",
        )

        self.assertFalse(use_amg)
        self.assertEqual(quality, "masterpiece")
        self.assertEqual(
            prompt,
            "@artist_name, lora trigger, masterpiece, 1girl, best quality",
        )
        self.assertEqual(prompt, metadata)

    def test_lora_trigger_field_keeps_literal_underscores(self):
        prompt, quality, use_amg, metadata = EasyUseAnimaPromptBuilder().build(
            False,
            False,
            "masterpiece",
            "model_trigger",
            "lora_model_trigger",
            "1girl",
            "",
        )

        self.assertFalse(use_amg)
        self.assertEqual(quality, "masterpiece")
        self.assertEqual(prompt, "masterpiece, 1girl, model_trigger, lora_model_trigger")
        self.assertEqual(metadata, prompt)

    def test_metadata_filter_only_changes_metadata_prompt(self):
        with patch("nodes.resolve_metadata_filter_words", return_value="best quality\nhigh detail"):
            prompt, quality, use_amg, metadata = EasyUseAnimaPromptBuilder().build(
                False,
                False,
                "masterpiece, best quality",
                "@artist_name",
                "",
                "1girl, long hair",
                "(high detail:0.6)",
            )

        self.assertFalse(use_amg)
        self.assertEqual(quality, "masterpiece, best quality")
        self.assertEqual(
            prompt,
            "masterpiece, best quality, 1girl, @artist_name, long hair, (high detail:0.6)",
        )
        self.assertEqual(
            metadata,
            "masterpiece, 1girl, @artist_name, long hair",
        )

    def test_prompt_studio_matches_builder_outputs(self):
        builder_output = EasyUseAnimaPromptBuilder().build(
            True,
            False,
            "masterpiece",
            "@artist_name",
            "lora trigger",
            "1girl, long hair",
            "best quality",
        )
        studio_output = EasyUseAnimaPromptStudio().build(
            True,
            False,
            "masterpiece",
            "@artist_name",
            "lora trigger",
            "1girl, long hair",
            "best quality",
        )

        self.assertEqual(studio_output["result"], builder_output)
        self.assertEqual(
            studio_output["ui"]["prompt_studio_inputs"][0]["prompt"],
            "1girl, long hair",
        )

    def test_prompt_studio_advanced_defaults_include_negative_output(self):
        result = EasyUseAnimaPromptStudioAdvanced().build(
            False,
            True,
            False,
            False,
            "",
        )

        fields = json.loads(result["ui"]["prompt_studio_advanced"][0]["advanced_fields"])
        self.assertTrue(any(field["pane"] == "positive" for field in fields))
        self.assertTrue(any(field["pane"] == "negative" for field in fields))
        self.assertEqual(result["result"][1], "")
        self.assertIn("masterpiece", result["result"][0])
        self.assertIn("location", result["result"][0])

    def test_prompt_studio_advanced_output_socket_order_groups_related_outputs(self):
        self.assertEqual(
            EasyUseAnimaPromptStudioAdvanced.RETURN_NAMES,
            (
                "positive_prompt",
                "negative_prompt",
                "anima_mod_guidance_quality_tags",
                "anima_mod_guidance_negative_prompt",
                "use_anima_mod_guidance",
                "use_negative_anima_mod_guidance",
                "metadata_prompt",
                "metadata_negative_prompt",
                "width",
                "height",
            ),
        )

    def test_prompt_studio_advanced_v2_outputs_only_prompt_data_socket(self):
        self.assertEqual(EasyUseAnimaPromptStudioAdvancedV2.RETURN_TYPES, (PROMPT_DATA_TYPE,))
        self.assertEqual(EasyUseAnimaPromptStudioAdvancedV2.RETURN_NAMES, (PROMPT_DATA_TYPE,))

    def test_prompt_data_unpack_uses_prompt_data_type_as_socket_name(self):
        input_types = EasyUseAnimaPromptDataUnpack.INPUT_TYPES()
        self.assertIn(PROMPT_DATA_TYPE, input_types["required"])
        for name in EasyUseAnimaPromptStudioAdvanced.RETURN_NAMES:
            self.assertIn(name, input_types["optional"])
        self.assertEqual(EasyUseAnimaPromptDataUnpack.RETURN_TYPES[0], PROMPT_DATA_TYPE)
        self.assertEqual(EasyUseAnimaPromptDataUnpack.RETURN_NAMES[0], PROMPT_DATA_TYPE)

    def test_prompt_studio_advanced_v2_returns_structured_prompt_data(self):
        fields = [
            {
                "id": "artist",
                "pane": "positive",
                "type": "artist",
                "label": "Artist Tags",
                "text": "artist_a, artist_b",
                "height": 72,
            },
            {
                "id": "general",
                "pane": "positive",
                "type": "general",
                "label": "General Tags",
                "text": "1girl",
                "height": 120,
            },
            {
                "id": "negative",
                "pane": "negative",
                "type": "general",
                "label": "General Tags",
                "text": "bad hands",
                "height": 120,
            },
        ]
        result = EasyUseAnimaPromptStudioAdvancedV2().build(
            False,
            True,
            False,
            False,
            json.dumps(fields),
            resolution_bucket="1024",
            resolution_size="896 * 1152 (7:9)",
        )

        prompt_data = result["result"][0]
        self.assertIsInstance(prompt_data, dict)
        self.assertEqual(len(result["result"]), 1)
        self.assertEqual(prompt_data["schema"], PROMPT_DATA_SCHEMA)
        self.assertEqual(prompt_data["type"], PROMPT_DATA_TYPE)
        self.assertEqual(prompt_data["outputs"]["positive_prompt"], prompt_data["positive_prompt"])
        self.assertEqual(prompt_data["outputs"]["negative_prompt"], prompt_data["negative_prompt"])
        self.assertEqual(prompt_data["negative_prompt"], "bad hands")
        self.assertEqual(prompt_data["artist"]["positive_prompt"], "artist_a, artist_b")
        self.assertFalse(prompt_data["artist_mix"]["enabled"])
        self.assertEqual(prompt_data["artist_mix"]["mode"], "prompt")
        self.assertEqual(prompt_data["artist_mix"]["artist_prompt"], "artist_a, artist_b")
        self.assertEqual(prompt_data["width"], 896)
        self.assertEqual(prompt_data["height"], 1152)
        self.assertEqual(prompt_data["resolution"]["width"], 896)
        self.assertEqual(prompt_data["resolution"]["height"], 1152)

    def test_prompt_data_unpack_expands_context_style_prompt_data(self):
        result = EasyUseAnimaPromptStudioAdvancedV2().build(
            False,
            True,
            True,
            False,
            json.dumps([
                {
                    "id": "quality",
                    "pane": "positive",
                    "type": "quality",
                    "label": "Quality Tags",
                    "text": "masterpiece",
                    "height": 72,
                },
                {
                    "id": "general",
                    "pane": "positive",
                    "type": "general",
                    "label": "General Tags",
                    "text": "1girl",
                    "height": 120,
                },
            ]),
            resolution_bucket="1024",
            resolution_size="896 * 1152 (7:9)",
        )
        prompt_data = result["result"][0]

        unpacked = EasyUseAnimaPromptDataUnpack().unpack(prompt_data)

        self.assertEqual(unpacked[0], prompt_data)
        self.assertEqual(unpacked[1:], tuple(prompt_data["outputs"][name] for name in EasyUseAnimaPromptStudioAdvanced.RETURN_NAMES))
        self.assertEqual(unpacked[1], prompt_data["positive_prompt"])
        self.assertEqual(unpacked[3], "masterpiece")
        self.assertTrue(unpacked[5])
        self.assertEqual(unpacked[9:11], (896, 1152))

    def test_prompt_data_unpack_uses_key_fallbacks(self):
        prompt_data = {
            "schema": PROMPT_DATA_SCHEMA,
            "positive_prompt": "1girl",
            "negative_prompt": "bad hands",
            "mod_guidance": {
                "enabled": True,
                "quality_tags": "masterpiece",
                "negative_enabled": False,
                "negative_prompt": "",
            },
            "resolution": {
                "width": 832,
                "height": 1216,
            },
        }

        unpacked = EasyUseAnimaPromptDataUnpack().unpack(prompt_data)

        self.assertEqual(unpacked[1], "1girl")
        self.assertEqual(unpacked[2], "bad hands")
        self.assertEqual(unpacked[3], "masterpiece")
        self.assertTrue(unpacked[5])
        self.assertFalse(unpacked[6])
        self.assertEqual(unpacked[9:11], (832, 1216))

    def test_prompt_data_unpack_optional_inputs_override_prompt_data(self):
        prompt_data = {
            "schema": PROMPT_DATA_SCHEMA,
            "positive_prompt": "old positive",
            "negative_prompt": "old negative",
            "outputs": {
                "positive_prompt": "old positive",
                "negative_prompt": "old negative",
                "anima_mod_guidance_quality_tags": "",
                "anima_mod_guidance_negative_prompt": "",
                "use_anima_mod_guidance": False,
                "use_negative_anima_mod_guidance": False,
                "metadata_prompt": "old positive",
                "metadata_negative_prompt": "old negative",
                "width": 1024,
                "height": 1024,
            },
            "resolution": {
                "width": 1024,
                "height": 1024,
            },
        }

        unpacked = EasyUseAnimaPromptDataUnpack().unpack(
            prompt_data,
            positive_prompt="new positive",
            negative_prompt="new negative",
            anima_mod_guidance_quality_tags="masterpiece",
            use_anima_mod_guidance=True,
            width=768,
            height=1152,
        )
        updated = unpacked[0]

        self.assertEqual(updated["positive_prompt"], "new positive")
        self.assertEqual(updated["prompt"], "new positive")
        self.assertEqual(updated["negative_prompt"], "new negative")
        self.assertEqual(updated["outputs"]["positive_prompt"], "new positive")
        self.assertEqual(updated["outputs"]["anima_mod_guidance_quality_tags"], "masterpiece")
        self.assertTrue(updated["outputs"]["use_anima_mod_guidance"])
        self.assertEqual(updated["resolution"]["width"], 768)
        self.assertEqual(updated["resolution"]["height"], 1152)
        self.assertEqual(unpacked[1], "new positive")
        self.assertEqual(unpacked[2], "new negative")
        self.assertEqual(unpacked[3], "masterpiece")
        self.assertTrue(unpacked[5])
        self.assertEqual(unpacked[9:11], (768, 1152))

    def test_prompt_studio_advanced_v2_artist_data_uses_artist_field_not_at_prefix(self):
        fields = [
            {
                "id": "general",
                "pane": "positive",
                "type": "general",
                "label": "General Tags",
                "text": "@looks_like_artist, 1girl",
                "height": 120,
            },
        ]
        result = EasyUseAnimaPromptStudioAdvancedV2().build(
            False,
            True,
            False,
            False,
            json.dumps(fields),
        )

        prompt_data = result["result"][0]
        self.assertIn("1girl", prompt_data["positive_prompt"])
        self.assertEqual(prompt_data["artist"]["positive_prompt"], "")
        self.assertEqual(prompt_data["artist_mix"]["artist_prompt"], "")

    def test_prompt_studio_advanced_splits_positive_negative_and_amg_quality(self):
        fields = [
            {
                "id": "q",
                "pane": "positive",
                "type": "quality",
                "label": "Quality Tags",
                "text": "masterpiece",
                "height": 72,
            },
            {
                "id": "a",
                "pane": "positive",
                "type": "artist",
                "label": "Artist Tags",
                "text": "@artist_name",
                "height": 72,
            },
            {
                "id": "p",
                "pane": "positive",
                "type": "general",
                "label": "General Tags",
                "text": "1girl, long hair",
                "height": 120,
            },
            {
                "id": "n",
                "pane": "negative",
                "type": "general",
                "label": "General Tags",
                "text": "low quality, bad hands",
                "height": 120,
            },
        ]
        result = EasyUseAnimaPromptStudioAdvanced().build(
            False,
            True,
            True,
            False,
            json.dumps(fields),
        )

        (
            positive,
            negative,
            quality,
            negative_amg,
            use_amg,
            use_negative_amg,
            metadata,
            metadata_negative,
            width,
            height,
        ) = result["result"]
        self.assertNotIn("masterpiece", positive)
        self.assertEqual(quality, "masterpiece")
        self.assertTrue(use_amg)
        self.assertEqual(negative, "low quality, bad hands")
        self.assertIn("masterpiece", metadata)
        self.assertEqual(metadata_negative, negative)
        self.assertEqual(negative_amg, "")
        self.assertFalse(use_negative_amg)
        self.assertEqual((width, height), (1024, 1024))

    def test_prompt_studio_advanced_can_route_negative_quality_to_amg(self):
        fields = [
            {
                "id": "positive_general",
                "pane": "positive",
                "type": "general",
                "label": "General Tags",
                "text": "1girl",
                "height": 120,
            },
            {
                "id": "negative_quality",
                "pane": "negative",
                "type": "quality",
                "label": "Quality Tags",
                "text": "low quality",
                "height": 72,
            },
            {
                "id": "negative_general",
                "pane": "negative",
                "type": "general",
                "label": "General Tags",
                "text": "bad hands",
                "height": 120,
            },
        ]
        result = EasyUseAnimaPromptStudioAdvanced().build(
            False,
            True,
            False,
            False,
            json.dumps(fields),
            True,
        )

        (
            positive,
            negative,
            quality,
            negative_amg,
            use_amg,
            use_negative_amg,
            metadata,
            metadata_negative,
            width,
            height,
        ) = result["result"]
        self.assertEqual(positive, "1girl")
        self.assertEqual(quality, "")
        self.assertFalse(use_amg)
        self.assertEqual(negative, "bad hands")
        self.assertEqual(negative_amg, "low quality")
        self.assertTrue(use_negative_amg)
        self.assertEqual(metadata, "1girl")
        self.assertEqual(metadata_negative, "low quality, bad hands")
        self.assertEqual((width, height), (1024, 1024))

    def test_prompt_studio_advanced_keeps_one_naia_field_per_pane(self):
        fields = [
            {
                "id": "negative_naia",
                "pane": "negative",
                "type": "naia",
                "label": "NAIA Prompt",
                "text": "bad prompt",
                "height": 120,
            },
            {
                "id": "negative_naia_duplicate",
                "pane": "negative",
                "type": "naia",
                "label": "NAIA Prompt",
                "text": "duplicate",
                "height": 120,
            },
        ]
        result = EasyUseAnimaPromptStudioAdvanced().build(
            False,
            True,
            False,
            False,
            json.dumps(fields),
        )

        normalized = json.loads(result["ui"]["prompt_studio_advanced"][0]["advanced_fields"])
        self.assertEqual(normalized[0]["pane"], "negative")
        self.assertEqual(normalized[0]["type"], "naia")
        self.assertEqual(len([field for field in normalized if field["type"] == "naia"]), 1)

    def test_prompt_studio_advanced_disabled_field_is_skipped(self):
        fields = [
            {
                "id": "enabled",
                "pane": "positive",
                "type": "general",
                "label": "General Tags",
                "text": "1girl",
                "height": 72,
                "enabled": True,
            },
            {
                "id": "disabled",
                "pane": "positive",
                "type": "general",
                "label": "General Tags",
                "text": "bad prompt",
                "height": 72,
                "enabled": False,
            },
        ]
        result = EasyUseAnimaPromptStudioAdvanced().build(
            False,
            True,
            False,
            False,
            json.dumps(fields),
        )

        self.assertEqual(result["result"][0], "1girl")
        normalized = json.loads(result["ui"]["prompt_studio_advanced"][0]["advanced_fields"])
        self.assertFalse(normalized[1]["enabled"])

    def test_prompt_studio_advanced_field_socket_overrides_output_without_saving(self):
        fields = [
            {
                "id": "positive_general",
                "pane": "positive",
                "type": "general",
                "label": "General Tags",
                "text": "old prompt",
                "height": 120,
            }
        ]
        result = EasyUseAnimaPromptStudioAdvanced().build(
            False,
            True,
            False,
            False,
            json.dumps(fields),
            field_positive_general="1girl, long hair",
        )

        self.assertEqual(result["result"][0], "1girl, long hair")
        saved = json.loads(result["ui"]["prompt_studio_advanced"][0]["advanced_fields"])
        self.assertEqual(saved[0]["text"], "old prompt")
        self.assertEqual(
            result["ui"]["prompt_studio_advanced"][0]["field_inputs"],
            {"field_positive_general": "1girl, long hair"},
        )

    def test_prompt_studio_advanced_trigger_field_is_socket_only_and_pinned(self):
        fields = [
            {
                "id": "before",
                "pane": "positive",
                "type": "general",
                "label": "General Tags",
                "text": "1girl",
                "height": 72,
            },
            {
                "id": "trigger_words",
                "pane": "positive",
                "type": "trigger",
                "label": "Trigger Words",
                "text": "",
                "height": 72,
                "pin": True,
            },
            {
                "id": "after",
                "pane": "positive",
                "type": "general",
                "label": "General Tags",
                "text": "long hair",
                "height": 72,
            },
        ]
        result = EasyUseAnimaPromptStudioAdvanced().build(
            False,
            True,
            False,
            False,
            json.dumps(fields),
            field_trigger_words="@model_trigger",
        )

        self.assertEqual(result["result"][0], "1girl, @model_trigger, long hair")
        saved = json.loads(result["ui"]["prompt_studio_advanced"][0]["advanced_fields"])
        self.assertEqual(saved[1]["type"], "trigger")
        self.assertEqual(saved[1]["text"], "")
        self.assertTrue(saved[1]["pin"])
        self.assertEqual(
            result["ui"]["prompt_studio_advanced"][0]["field_inputs"],
            {"field_trigger_words": "@model_trigger"},
        )

    def test_prompt_studio_advanced_trigger_field_keeps_literal_underscores(self):
        fields = [
            {
                "id": "trigger_words",
                "pane": "positive",
                "type": "trigger",
                "label": "Trigger Words",
                "text": "model_trigger_lora",
                "height": 72,
                "pin": True,
            },
            {
                "id": "body",
                "pane": "positive",
                "type": "general",
                "label": "General Tags",
                "text": "1girl",
                "height": 72,
            },
        ]
        result = EasyUseAnimaPromptStudioAdvanced().build(
            False,
            True,
            False,
            False,
            json.dumps(fields),
        )

        self.assertEqual(result["result"][0], "model_trigger_lora, 1girl")

    def test_prompt_studio_advanced_keeps_only_one_positive_trigger_field(self):
        fields = [
            {
                "id": "trigger_a",
                "pane": "positive",
                "type": "trigger",
                "label": "Trigger Words",
                "text": "@a",
                "height": 72,
            },
            {
                "id": "trigger_b",
                "pane": "positive",
                "type": "trigger",
                "label": "Trigger Words",
                "text": "@b",
                "height": 72,
            },
        ]
        result = EasyUseAnimaPromptStudioAdvanced().build(
            False,
            True,
            False,
            False,
            json.dumps(fields),
        )

        saved = json.loads(result["ui"]["prompt_studio_advanced"][0]["advanced_fields"])
        trigger_fields = [field for field in saved if field["type"] == "trigger"]
        self.assertEqual(len(trigger_fields), 1)
        self.assertEqual(trigger_fields[0]["text"], "@a")

    def test_prompt_studio_advanced_naia_fill_stays_enabled_but_saved_metadata_is_off(self):
        fields = [
            {
                "id": "positive_naia",
                "pane": "positive",
                "type": "naia",
                "label": "NAIA Prompt",
                "text": "old prompt",
                "height": 120,
                "enabled": True,
            }
        ]
        workflow_prompt = {
            "7": {
                "inputs": {
                    "use_naia": True,
                    "advanced_fields": json.dumps(fields),
                }
            }
        }
        extra_pnginfo = {
            "workflow": {
                "nodes": [
                    {
                        "id": 7,
                        "widgets_values": [True, True, False, False, json.dumps(fields)],
                    }
                ]
            }
        }
        settings = {
            "host": "127.0.0.1",
            "port": 8188,
            "use_naia_settings": True,
            "pre_prompt": "",
            "post_prompt": "",
            "auto_hide": "",
            "preprocessing": {},
        }

        with (
            patch("nodes.resolve_naia_settings", return_value=settings),
            patch(
                "nodes._post_random",
                return_value={
                    "ok": True,
                    "prompt": "1girl, silver hair",
                    "negative_prompt": "",
                    "width": 1024,
                    "height": 1024,
                },
            ),
        ):
            result = EasyUseAnimaPromptStudioAdvanced().build(
                True,
                True,
                False,
                False,
                json.dumps(fields),
                workflow_prompt=workflow_prompt,
                extra_pnginfo=extra_pnginfo,
                unique_id="7",
            )

        payload = result["ui"]["prompt_studio_advanced"][0]
        saved_fields = json.loads(payload["advanced_fields"])
        saved_image_fields = json.loads(extra_pnginfo["workflow"]["nodes"][0]["widgets_values"][8])

        self.assertTrue(payload["use_naia"])
        self.assertEqual(saved_fields[0]["text"], "1girl, silver hair")
        self.assertEqual(result["result"][0], "1girl, silver hair")
        self.assertFalse(workflow_prompt["7"]["inputs"]["use_naia"])
        self.assertFalse(extra_pnginfo["workflow"]["nodes"][0]["widgets_values"][0])
        self.assertEqual(saved_image_fields[0]["text"], "1girl, silver hair")

    def test_prompt_studio_advanced_naia_fill_updates_workflow_property_backup(self):
        previous_image_fields = [
            {
                "id": "positive_naia",
                "pane": "positive",
                "type": "naia",
                "label": "NAIA Prompt",
                "text": "previous image prompt",
                "height": 120,
                "enabled": True,
            }
        ]
        fields = [
            {
                "id": "positive_naia",
                "pane": "positive",
                "type": "naia",
                "label": "NAIA Prompt",
                "text": "old prompt",
                "height": 120,
                "enabled": True,
            }
        ]
        workflow_prompt = {
            "7": {
                "inputs": {
                    "use_naia": True,
                    "advanced_fields": json.dumps(fields),
                }
            }
        }
        extra_pnginfo = {
            "workflow": {
                "nodes": [
                    {
                        "id": 7,
                        "properties": {
                            ADVANCED_FIELDS_WORKFLOW_PROPERTY: json.dumps(previous_image_fields),
                        },
                        "widgets_values": [
                            True,
                            True,
                            False,
                            "1024",
                            "1024 * 1024 (1:1)",
                            1024,
                            1024,
                            False,
                            json.dumps(fields),
                        ],
                    }
                ]
            }
        }
        settings = {
            "host": "127.0.0.1",
            "port": 8188,
            "use_naia_settings": True,
            "pre_prompt": "",
            "post_prompt": "",
            "auto_hide": "",
            "preprocessing": {},
        }

        with (
            patch("nodes.resolve_naia_settings", return_value=settings),
            patch(
                "nodes._post_random",
                return_value={
                    "ok": True,
                    "prompt": "current image prompt",
                    "negative_prompt": "",
                    "width": 1024,
                    "height": 1024,
                },
            ),
        ):
            EasyUseAnimaPromptStudioAdvanced().build(
                True,
                True,
                False,
                False,
                json.dumps(fields),
                workflow_prompt=workflow_prompt,
                extra_pnginfo=extra_pnginfo,
                unique_id="7",
            )

        workflow_node = extra_pnginfo["workflow"]["nodes"][0]
        property_fields = json.loads(workflow_node["properties"][ADVANCED_FIELDS_WORKFLOW_PROPERTY])
        widget_fields = json.loads(workflow_node["widgets_values"][8])

        self.assertEqual(property_fields[0]["text"], "current image prompt")
        self.assertEqual(widget_fields[0]["text"], "current image prompt")
        self.assertEqual(workflow_prompt["7"]["inputs"]["advanced_fields"], workflow_node["widgets_values"][8])

    def test_prompt_studio_advanced_uses_one_naia_request_for_fields_and_resolution(self):
        fields = [
            {
                "id": "positive_naia",
                "pane": "positive",
                "type": "naia",
                "label": "NAIA Prompt",
                "text": "old positive",
                "height": 120,
                "enabled": True,
            },
            {
                "id": "negative_naia",
                "pane": "negative",
                "type": "naia",
                "label": "NAIA Prompt",
                "text": "old negative",
                "height": 120,
                "enabled": True,
            },
        ]
        workflow_prompt = {
            "9": {
                "inputs": {
                    "use_naia": True,
                    "advanced_fields": json.dumps(fields),
                    "resolution_bucket": "NAIA",
                }
            }
        }
        extra_pnginfo = {
            "workflow": {
                "nodes": [
                    {
                        "id": 9,
                        "widgets_values": [True, True, False, "NAIA", "", 1024, 1024, False, json.dumps(fields)],
                    }
                ]
            }
        }
        settings = {
            "host": "127.0.0.1",
            "port": 8188,
            "use_naia_settings": True,
            "pre_prompt": "",
            "post_prompt": "",
            "auto_hide": "",
            "preprocessing": {},
        }
        calls = []

        def fake_post(host, port, body):
            calls.append((host, port, body))
            return {
                "ok": True,
                "prompt": "1girl, silver hair",
                "negative_prompt": "low quality, bad hands",
                "width": 1000,
                "height": 777,
            }

        with (
            patch("nodes.resolve_naia_settings", return_value=settings),
            patch("nodes._post_random", fake_post),
        ):
            result = EasyUseAnimaPromptStudioAdvanced().build(
                True,
                True,
                False,
                False,
                json.dumps(fields),
                resolution_bucket="NAIA",
                resolution_size="1024 * 1024 (1:1)",
                resolution_custom_width=1024,
                resolution_custom_height=1024,
                workflow_prompt=workflow_prompt,
                extra_pnginfo=extra_pnginfo,
                unique_id="9",
            )

        payload = result["ui"]["prompt_studio_advanced"][0]
        saved_fields = json.loads(payload["advanced_fields"])
        saved_by_id = {field["id"]: field for field in saved_fields}
        saved_image_fields = json.loads(extra_pnginfo["workflow"]["nodes"][0]["widgets_values"][8])
        saved_image_by_id = {field["id"]: field for field in saved_image_fields}

        self.assertEqual(len(calls), 1)
        self.assertEqual(saved_by_id["positive_naia"]["text"], "1girl, silver hair")
        self.assertEqual(saved_by_id["negative_naia"]["text"], "low quality, bad hands")
        self.assertEqual(saved_image_by_id["negative_naia"]["text"], "low quality, bad hands")
        self.assertEqual(result["result"][0], "1girl, silver hair")
        self.assertEqual(result["result"][1], "low quality, bad hands")
        self.assertEqual(result["result"][8:10], (992, 768))
        self.assertFalse(workflow_prompt["9"]["inputs"]["use_naia"])
        self.assertEqual(workflow_prompt["9"]["inputs"]["resolution_bucket"], "Custom")
        self.assertEqual(workflow_prompt["9"]["inputs"]["resolution_size"], "992 * 768 (31:24)")
        self.assertEqual(workflow_prompt["9"]["inputs"]["resolution_custom_width"], 992)
        self.assertEqual(workflow_prompt["9"]["inputs"]["resolution_custom_height"], 768)
        self.assertTrue(payload["use_naia"])
        self.assertEqual(payload["resolution_bucket"], "NAIA")
        self.assertEqual(payload["resolution_size"], "992 * 768 (31:24)")
        self.assertEqual(payload["resolution_custom_width"], 992)
        self.assertEqual(payload["resolution_custom_height"], 768)
        self.assertFalse(extra_pnginfo["workflow"]["nodes"][0]["widgets_values"][0])
        self.assertEqual(extra_pnginfo["workflow"]["nodes"][0]["widgets_values"][3], "Custom")
        self.assertEqual(extra_pnginfo["workflow"]["nodes"][0]["widgets_values"][4], "992 * 768 (31:24)")
        self.assertEqual(extra_pnginfo["workflow"]["nodes"][0]["widgets_values"][5], 992)
        self.assertEqual(extra_pnginfo["workflow"]["nodes"][0]["widgets_values"][6], 768)

    def test_prompt_studio_advanced_keeps_naia_resolution_live_after_execution(self):
        calls = []
        responses = [
            {
                "ok": True,
                "prompt": "first prompt",
                "negative_prompt": "first negative",
                "width": 1000,
                "height": 777,
            },
            {
                "ok": True,
                "prompt": "second prompt",
                "negative_prompt": "second negative",
                "width": 1216,
                "height": 832,
            },
        ]
        settings = {
            "host": "127.0.0.1",
            "port": 8188,
            "use_naia_settings": True,
            "pre_prompt": "",
            "post_prompt": "",
            "auto_hide": "",
            "preprocessing": {},
        }

        def fake_post(host, port, body):
            calls.append((host, port, body))
            return responses[len(calls) - 1]

        with (
            patch("nodes.resolve_naia_settings", return_value=settings),
            patch("nodes._post_random", fake_post),
        ):
            first = EasyUseAnimaPromptStudioAdvanced().build(
                True,
                True,
                False,
                False,
                "[]",
                resolution_bucket="NAIA",
                resolution_size="1024 * 1024 (1:1)",
                resolution_custom_width=1024,
                resolution_custom_height=1024,
            )
            first_payload = first["ui"]["prompt_studio_advanced"][0]
            second = EasyUseAnimaPromptStudioAdvanced().build(
                first_payload["use_naia"],
                True,
                False,
                False,
                first_payload["advanced_fields"],
                resolution_bucket=first_payload["resolution_bucket"],
                resolution_size=first_payload["resolution_size"],
                resolution_custom_width=first_payload["resolution_custom_width"],
                resolution_custom_height=first_payload["resolution_custom_height"],
            )

        self.assertEqual(len(calls), 2)
        self.assertEqual(first["result"][8:10], (992, 768))
        self.assertEqual(second["result"][8:10], (1216, 832))
        self.assertEqual(first_payload["resolution_bucket"], "NAIA")
        self.assertEqual(second["ui"]["prompt_studio_advanced"][0]["resolution_bucket"], "NAIA")

    def test_prompt_studio_advanced_scales_naia_resolution_and_caps_long_edge(self):
        workflow_prompt = {
            "9": {
                "inputs": {
                    "use_naia": True,
                    "advanced_fields": "[]",
                    "resolution_bucket": "NAIA",
                }
            }
        }
        extra_pnginfo = {
            "workflow": {
                "nodes": [
                    {
                        "id": 9,
                        "widgets_values": [True, True, False, "NAIA", "", 1024, 1024, False, "[]"],
                    }
                ]
            }
        }
        settings = {
            "host": "127.0.0.1",
            "port": 8188,
            "use_naia_settings": True,
            "resolution_scale": 1.5,
            "resolution_max_long_edge": 1280,
            "pre_prompt": "",
            "post_prompt": "",
            "auto_hide": "",
            "preprocessing": {},
        }

        def fake_post(_host, _port, _body):
            return {
                "ok": True,
                "prompt": "prompt",
                "negative_prompt": "negative",
                "width": 1000,
                "height": 777,
            }

        with (
            patch("nodes.resolve_naia_settings", return_value=settings),
            patch("nodes._post_random", fake_post),
        ):
            result = EasyUseAnimaPromptStudioAdvanced().build(
                True,
                True,
                False,
                False,
                "[]",
                resolution_bucket="NAIA",
                resolution_size="1024 * 1024 (1:1)",
                resolution_custom_width=1024,
                resolution_custom_height=1024,
                workflow_prompt=workflow_prompt,
                extra_pnginfo=extra_pnginfo,
                unique_id="9",
            )

        payload = result["ui"]["prompt_studio_advanced"][0]
        self.assertEqual(result["result"][8:10], (1280, 992))
        self.assertEqual(payload["resolution_bucket"], "NAIA")
        self.assertEqual(payload["resolution_size"], "1280 * 992 (40:31)")
        self.assertEqual(payload["resolution_custom_width"], 1280)
        self.assertEqual(payload["resolution_custom_height"], 992)
        self.assertEqual(workflow_prompt["9"]["inputs"]["resolution_bucket"], "Custom")
        self.assertEqual(workflow_prompt["9"]["inputs"]["resolution_size"], "1280 * 992 (40:31)")
        self.assertEqual(extra_pnginfo["workflow"]["nodes"][0]["widgets_values"][5], 1280)
        self.assertEqual(extra_pnginfo["workflow"]["nodes"][0]["widgets_values"][6], 992)

    def test_prompt_studio_advanced_fits_naia_resolution_to_configured_bucket(self):
        workflow_prompt = {
            "9": {
                "inputs": {
                    "use_naia": True,
                    "advanced_fields": "[]",
                    "resolution_bucket": "NAIA",
                }
            }
        }
        extra_pnginfo = {
            "workflow": {
                "nodes": [
                    {
                        "id": 9,
                        "widgets_values": [True, True, False, "NAIA", "", 1024, 1024, False, "[]"],
                    }
                ]
            }
        }
        settings = {
            "host": "127.0.0.1",
            "port": 8188,
            "use_naia_settings": True,
            "resolution_mode": "bucket",
            "resolution_bucket": "1536",
            "resolution_scale": 4.0,
            "resolution_max_long_edge": 512,
            "pre_prompt": "",
            "post_prompt": "",
            "auto_hide": "",
            "preprocessing": {},
        }

        def fake_post(_host, _port, _body):
            return {
                "ok": True,
                "prompt": "prompt",
                "negative_prompt": "negative",
                "width": 1000,
                "height": 777,
            }

        with (
            patch("nodes.resolve_naia_settings", return_value=settings),
            patch("nodes._post_random", fake_post),
        ):
            result = EasyUseAnimaPromptStudioAdvanced().build(
                True,
                True,
                False,
                False,
                "[]",
                resolution_bucket="NAIA",
                resolution_size="1024 * 1024 (1:1)",
                resolution_custom_width=1024,
                resolution_custom_height=1024,
                workflow_prompt=workflow_prompt,
                extra_pnginfo=extra_pnginfo,
                unique_id="9",
            )

        payload = result["ui"]["prompt_studio_advanced"][0]
        self.assertEqual(result["result"][8:10], (1728, 1280))
        self.assertEqual(payload["resolution_bucket"], "NAIA")
        self.assertEqual(payload["resolution_size"], "1728 * 1280 (27:20)")
        self.assertEqual(payload["resolution_custom_width"], 1728)
        self.assertEqual(payload["resolution_custom_height"], 1280)
        self.assertEqual(workflow_prompt["9"]["inputs"]["resolution_bucket"], "Custom")
        self.assertEqual(workflow_prompt["9"]["inputs"]["resolution_size"], "1728 * 1280 (27:20)")
        self.assertEqual(extra_pnginfo["workflow"]["nodes"][0]["widgets_values"][5], 1728)
        self.assertEqual(extra_pnginfo["workflow"]["nodes"][0]["widgets_values"][6], 1280)

    def test_prompt_studio_advanced_naia_resolution_cap_does_not_round_past_limit(self):
        settings = {
            "host": "127.0.0.1",
            "port": 8188,
            "use_naia_settings": True,
            "resolution_scale": 2,
            "resolution_max_long_edge": 1000,
            "pre_prompt": "",
            "post_prompt": "",
            "auto_hide": "",
            "preprocessing": {},
        }

        def fake_post(_host, _port, _body):
            return {
                "ok": True,
                "prompt": "prompt",
                "negative_prompt": "negative",
                "width": 1216,
                "height": 832,
            }

        with (
            patch("nodes.resolve_naia_settings", return_value=settings),
            patch("nodes._post_random", fake_post),
        ):
            result = EasyUseAnimaPromptStudioAdvanced().build(
                True,
                True,
                False,
                False,
                "[]",
                resolution_bucket="NAIA",
                resolution_size="1024 * 1024 (1:1)",
                resolution_custom_width=1024,
                resolution_custom_height=1024,
            )

        width, height = result["result"][8:10]
        self.assertEqual((width, height), (992, 672))
        self.assertLessEqual(max(width, height), 1000)
        self.assertEqual(width % 32, 0)
        self.assertEqual(height % 32, 0)

    def test_prompt_studio_advanced_outputs_selected_resolution(self):
        result = EasyUseAnimaPromptStudioAdvanced().build(
            False,
            True,
            False,
            False,
            "",
            resolution_bucket="1024",
            resolution_size="896 * 1152 (7:9)",
        )

        self.assertEqual(result["result"][8:10], (896, 1152))

    def test_prompt_studio_advanced_outputs_custom_resolution_snapped_to_32(self):
        result = EasyUseAnimaPromptStudioAdvanced().build(
            False,
            True,
            False,
            False,
            "",
            resolution_bucket="Custom",
            resolution_size="1000 * 777 (1000:777)",
            resolution_custom_width=1000,
            resolution_custom_height=777,
        )

        self.assertEqual(result["result"][8:10], (992, 768))

    def test_prompt_studio_advanced_resolution_buckets_are_32_aligned(self):
        for values in ADVANCED_RESOLUTION_BUCKETS.values():
            for width, height in values:
                self.assertEqual(width % 32, 0)
                self.assertEqual(height % 32, 0)

    def test_prompt_studio_advanced_resolution_buckets_have_mirrors(self):
        for bucket, values in ADVANCED_RESOLUTION_BUCKETS.items():
            value_set = set(values)
            for width, height in values:
                self.assertIn((height, width), value_set, (bucket, width, height))

    def test_prompt_studio_advanced_resolution_buckets_use_nearest_area_tier(self):
        bucket_edges = sorted(int(bucket) for bucket in ADVANCED_RESOLUTION_BUCKETS)
        for bucket, values in ADVANCED_RESOLUTION_BUCKETS.items():
            expected_edge = int(bucket)
            for width, height in values:
                area = width * height
                nearest_edge = min(
                    bucket_edges,
                    key=lambda edge: (abs(area - edge * edge), edge),
                )
                self.assertEqual(nearest_edge, expected_edge, (bucket, width, height))

    def test_prompt_studio_advanced_1024_by_1536_belongs_to_1280_bucket(self):
        self.assertIn((1024, 1536), ADVANCED_RESOLUTION_BUCKETS["1280"])
        self.assertIn((1536, 1024), ADVANCED_RESOLUTION_BUCKETS["1280"])
        self.assertNotIn((1024, 1536), ADVANCED_RESOLUTION_BUCKETS["1536"])
        self.assertNotIn((1536, 1024), ADVANCED_RESOLUTION_BUCKETS["1536"])

    def test_prompt_studio_extend_uses_numbered_slot_order(self):
        result = EasyUseAnimaPromptStudioExtend().build(
            False,
            True,
            False,
            quality_tags_1="masterpiece",
            quality_tags_2="best quality",
            naia_prompt_3="1girl",
            general_tags_4="silver hair",
            general_tags_5="grey eyes",
            general_tags_6="",
            general_tags_7="",
            general_tags_8="",
            general_tags_9="",
            trailing_tags_10="location",
            trailing_tags_11="highres",
            negative_prompt_1="low quality",
            negative_prompt_2="bad hands",
            negative_prompt_3="",
            negative_prompt_4="",
        )

        (
            positive,
            negative,
            quality,
            negative_amg,
            use_amg,
            use_negative_amg,
            metadata,
            metadata_negative,
        ) = result["result"]
        payload = result["ui"]["prompt_studio_slots"][0]

        self.assertTrue(use_amg)
        self.assertEqual(quality, "masterpiece, best quality")
        self.assertNotIn("masterpiece", positive)
        self.assertIn("1girl", positive)
        self.assertIn("location", positive)
        self.assertEqual(negative, "low quality, bad hands")
        self.assertIn("masterpiece", metadata)
        self.assertEqual(metadata_negative, negative)
        self.assertEqual(negative_amg, "low quality, bad hands")
        self.assertFalse(use_negative_amg)
        self.assertEqual(payload["naia_prompt_3"], "1girl")

    def test_prompt_studio_extend_output_socket_order_matches_advanced_prompt_outputs(self):
        self.assertEqual(
            EasyUseAnimaPromptStudioExtend.RETURN_NAMES,
            (
                "positive_prompt",
                "negative_prompt",
                "anima_mod_guidance_quality_tags",
                "anima_mod_guidance_negative_prompt",
                "use_anima_mod_guidance",
                "use_negative_anima_mod_guidance",
                "metadata_prompt",
                "metadata_negative_prompt",
            ),
        )

    def test_prompt_studio_extend_can_route_negative_quality_slots_to_amg(self):
        result = EasyUseAnimaPromptStudioExtend().build(
            False,
            False,
            False,
            True,
            quality_tags_1="masterpiece",
            quality_tags_2="",
            naia_prompt_3="1girl",
            general_tags_4="",
            general_tags_5="",
            general_tags_6="",
            general_tags_7="",
            general_tags_8="",
            general_tags_9="",
            trailing_tags_10="",
            trailing_tags_11="",
            negative_prompt_1="low quality",
            negative_prompt_2="bad hands",
            negative_prompt_3="bad anatomy",
            negative_prompt_4="",
        )

        (
            positive,
            negative,
            quality,
            negative_amg,
            use_amg,
            use_negative_amg,
            metadata,
            metadata_negative,
        ) = result["result"]

        self.assertEqual(positive, "masterpiece, 1girl")
        self.assertEqual(quality, "masterpiece")
        self.assertFalse(use_amg)
        self.assertEqual(negative, "bad anatomy")
        self.assertEqual(negative_amg, "low quality, bad hands")
        self.assertTrue(use_negative_amg)
        self.assertEqual(metadata, "masterpiece, 1girl")
        self.assertEqual(metadata_negative, "low quality, bad hands, bad anatomy")

    def test_prompt_studio_extend_active_slots_exclude_hidden_values(self):
        result = EasyUseAnimaPromptStudioExtend().build(
            False,
            False,
            False,
            active_slots=json.dumps(["general_tags_4"]),
            quality_tags_1="masterpiece",
            naia_prompt_3="hidden naia",
            general_tags_4="visible general",
            trailing_tags_10="hidden trailing",
            negative_prompt_1="hidden negative",
        )

        (
            positive,
            negative,
            quality,
            negative_amg,
            use_amg,
            use_negative_amg,
            metadata,
            metadata_negative,
        ) = result["result"]
        payload = result["ui"]["prompt_studio_slots"][0]

        self.assertFalse(use_amg)
        self.assertFalse(use_negative_amg)
        self.assertEqual(positive, "visible general")
        self.assertEqual(metadata, "visible general")
        self.assertEqual(negative, "")
        self.assertEqual(metadata_negative, "")
        self.assertEqual(quality, "")
        self.assertEqual(negative_amg, "")
        self.assertEqual(payload["active_slots"], json.dumps(["general_tags_4"]))

    def test_prompt_studio_extend_naia_fill_stays_enabled_but_saved_metadata_is_off(self):
        workflow_prompt = {
            "11": {
                "inputs": {
                    "fill_naia_prompt": True,
                    "naia_prompt_3": "old prompt",
                }
            }
        }
        extra_pnginfo = {
            "workflow": {
                "nodes": [
                    {
                        "id": 11,
                        "widgets_values": [True, False, False, "", "", "old prompt"],
                    }
                ]
            }
        }
        settings = {
            "host": "127.0.0.1",
            "port": 8188,
            "use_naia_settings": True,
            "pre_prompt": "",
            "post_prompt": "",
            "auto_hide": "",
            "preprocessing": {},
        }

        with (
            patch("nodes.resolve_naia_settings", return_value=settings),
            patch(
                "nodes._post_random",
                return_value={
                    "ok": True,
                    "prompt": "1girl, blue eyes",
                    "negative_prompt": "",
                    "width": 1024,
                    "height": 1024,
                },
            ),
        ):
            result = EasyUseAnimaPromptStudioExtend().build(
                True,
                False,
                False,
                workflow_prompt=workflow_prompt,
                extra_pnginfo=extra_pnginfo,
                unique_id="11",
                naia_prompt_3="old prompt",
            )

        payload = result["ui"]["prompt_studio_slots"][0]
        self.assertTrue(payload["fill_naia_prompt"])
        self.assertEqual(payload["naia_prompt_3"], "1girl, blue eyes")
        self.assertIn("1girl", result["result"][0])
        self.assertFalse(workflow_prompt["11"]["inputs"]["fill_naia_prompt"])
        self.assertEqual(workflow_prompt["11"]["inputs"]["naia_prompt_3"], "1girl, blue eyes")
        self.assertFalse(extra_pnginfo["workflow"]["nodes"][0]["widgets_values"][0])
        self.assertEqual(extra_pnginfo["workflow"]["nodes"][0]["widgets_values"][5], "1girl, blue eyes")


class SettingsTests(unittest.TestCase):
    def test_public_settings_does_not_expose_token_file(self):
        settings = public_settings()
        self.assertEqual(
            set(settings),
            {
                "prompt.metadata_filter_words",
                "autocomplete.source",
                "autocomplete.limit",
                "autocomplete.mode",
                "autocomplete.commit_key",
                "autocomplete.append_separator",
                "autocomplete.no_comma_after_period",
                "autocomplete.detect_natural_sentences",
                "lora_preset.name_display",
                "lora_preset.menu_mode",
                "lora_preset.strength_button_step",
                "lora_preset.strength_drag_step",
                "lora_preset.strength_drag_pixels",
                "prompt_studio.typo_indicator",
                "prompt_studio.comment_italic",
                "prompt_studio.colors",
                "prompt_studio.naia_general_above_auto_toggle",
                "wildcard.extra_paths",
                "naia.host",
                "naia.port",
                "naia.use_naia_settings",
                "naia.resolution_mode",
                "naia.resolution_bucket",
                "naia.resolution_scale",
                "naia.resolution_max_long_edge",
                "naia.pre_prompt",
                "naia.post_prompt",
                "naia.auto_hide",
                *{f"naia.{key}" for key in NAIA_PREPROCESSING_KEYS},
            },
        )

    def test_autocomplete_limit_is_clamped(self):
        self.assertEqual(resolve_autocomplete_limit({"autocomplete.limit": "0"}), 1)
        self.assertEqual(resolve_autocomplete_limit({"autocomplete.limit": "37"}), 37)
        self.assertEqual(resolve_autocomplete_limit({"autocomplete.limit": "200"}), 100)
        self.assertEqual(resolve_autocomplete_limit({"autocomplete.limit": "bad"}), 20)

    def test_autocomplete_mode_is_validated(self):
        self.assertEqual(
            resolve_autocomplete_mode({"autocomplete.mode": "off"}),
            "off",
        )
        self.assertEqual(
            resolve_autocomplete_mode({"autocomplete.mode": "easyuse_nodes"}),
            "easyuse_nodes",
        )
        self.assertEqual(
            resolve_autocomplete_mode({"autocomplete.mode": "compatible_global"}),
            "compatible_global",
        )
        self.assertEqual(
            resolve_autocomplete_mode({"autocomplete.mode": "bad"}),
            "compatible_global",
        )

    def test_autocomplete_commit_key_is_validated(self):
        self.assertEqual(
            resolve_autocomplete_commit_key({"autocomplete.commit_key": "enter"}),
            "enter",
        )
        self.assertEqual(
            resolve_autocomplete_commit_key({"autocomplete.commit_key": "tab"}),
            "tab",
        )
        self.assertEqual(
            resolve_autocomplete_commit_key({"autocomplete.commit_key": "bad"}),
            "enter",
        )

    def test_lora_preset_strength_drag_step_is_clamped(self):
        self.assertEqual(
            resolve_lora_preset_strength_drag_step({"lora_preset.strength_drag_step": "0"}),
            0.001,
        )
        self.assertEqual(
            resolve_lora_preset_strength_drag_step({"lora_preset.strength_drag_step": "0.012"}),
            0.012,
        )
        self.assertEqual(
            resolve_lora_preset_strength_drag_step({"lora_preset.strength_drag_step": "1"}),
            0.2,
        )
        self.assertEqual(
            resolve_lora_preset_strength_drag_step({"lora_preset.strength_drag_step": "bad"}),
            0.05,
        )

    def test_lora_preset_strength_button_step_is_clamped(self):
        self.assertEqual(
            resolve_lora_preset_strength_button_step({"lora_preset.strength_button_step": "0"}),
            0.001,
        )
        self.assertEqual(
            resolve_lora_preset_strength_button_step({"lora_preset.strength_button_step": "0.125"}),
            0.125,
        )
        self.assertEqual(
            resolve_lora_preset_strength_button_step({"lora_preset.strength_button_step": "1"}),
            0.5,
        )
        self.assertEqual(
            resolve_lora_preset_strength_button_step({"lora_preset.strength_button_step": "bad"}),
            0.05,
        )

    def test_lora_preset_strength_drag_pixels_is_clamped(self):
        self.assertEqual(
            resolve_lora_preset_strength_drag_pixels({"lora_preset.strength_drag_pixels": "0"}),
            1,
        )
        self.assertEqual(
            resolve_lora_preset_strength_drag_pixels({"lora_preset.strength_drag_pixels": "12"}),
            12,
        )
        self.assertEqual(
            resolve_lora_preset_strength_drag_pixels({"lora_preset.strength_drag_pixels": "200"}),
            100,
        )
        self.assertEqual(
            resolve_lora_preset_strength_drag_pixels({"lora_preset.strength_drag_pixels": "bad"}),
            8,
        )

    def test_lora_preset_menu_mode_is_validated(self):
        self.assertEqual(
            resolve_lora_preset_menu_mode({"lora_preset.menu_mode": "tree"}),
            "tree",
        )
        self.assertEqual(
            resolve_lora_preset_menu_mode({"lora_preset.menu_mode": "list"}),
            "list",
        )
        self.assertEqual(
            resolve_lora_preset_menu_mode({"lora_preset.menu_mode": "bad"}),
            "tree",
        )

    def test_naia_resolution_mode_is_validated(self):
        self.assertEqual(
            resolve_naia_resolution_mode({"naia.resolution_mode": "scale"}),
            "scale",
        )
        self.assertEqual(
            resolve_naia_resolution_mode({"naia.resolution_mode": "bucket"}),
            "bucket",
        )
        self.assertEqual(
            resolve_naia_resolution_mode({"naia.resolution_mode": "bucket_fit"}),
            "bucket",
        )
        self.assertEqual(
            resolve_naia_resolution_mode({"naia.resolution_mode": "bad"}),
            "scale",
        )

    def test_naia_resolution_bucket_is_validated(self):
        self.assertEqual(
            resolve_naia_resolution_bucket({"naia.resolution_bucket": "1536"}),
            "1536",
        )
        self.assertEqual(
            resolve_naia_resolution_bucket({"naia.resolution_bucket": "Custom"}),
            "1024",
        )
        self.assertEqual(
            resolve_naia_resolution_bucket({"naia.resolution_bucket": "bad"}),
            "1024",
        )

    def test_naia_resolution_scale_is_clamped(self):
        self.assertEqual(
            resolve_naia_resolution_scale({"naia.resolution_scale": "0"}),
            0.25,
        )
        self.assertEqual(
            resolve_naia_resolution_scale({"naia.resolution_scale": "1.5"}),
            1.5,
        )
        self.assertEqual(
            resolve_naia_resolution_scale({"naia.resolution_scale": "9"}),
            4.0,
        )
        self.assertEqual(
            resolve_naia_resolution_scale({"naia.resolution_scale": "bad"}),
            1.0,
        )

    def test_naia_resolution_max_long_edge_is_clamped(self):
        self.assertEqual(
            resolve_naia_resolution_max_long_edge({"naia.resolution_max_long_edge": "0"}),
            0,
        )
        self.assertEqual(
            resolve_naia_resolution_max_long_edge({"naia.resolution_max_long_edge": "17"}),
            32,
        )
        self.assertEqual(
            resolve_naia_resolution_max_long_edge({"naia.resolution_max_long_edge": "1280"}),
            1280,
        )
        self.assertEqual(
            resolve_naia_resolution_max_long_edge({"naia.resolution_max_long_edge": "99999"}),
            16384,
        )
        self.assertEqual(
            resolve_naia_resolution_max_long_edge({"naia.resolution_max_long_edge": "bad"}),
            0,
        )

    def test_comfy_settings_override_legacy_settings(self):
        with (
            patch.object(easyuse_settings, "_read_json_file", return_value={}),
            patch.object(
                easyuse_settings,
                "_load_comfy_settings",
                return_value={
                    "EasyUseAnima.Prompt.AutocompleteLimit": "7",
                    "EasyUseAnima.Prompt.AutocompleteCommitKey": "tab",
                    "EasyUseAnima.Prompt.AutocompleteAppendSeparator": "true",
                    "EasyUseAnima.Prompt.AutocompleteNoCommaAfterPeriod": "false",
                    "EasyUseAnima.Prompt.AutocompleteDetectNaturalSentences": "false",
                    "EasyUseAnima.Prompt.TypoIndicator": "false",
                    "EasyUseAnima.Prompt.CommentItalic": "false",
                    "EasyUseAnima.LoraPreset.NameDisplay": "path",
                    "EasyUseAnima.LoraPreset.MenuMode": "list",
                    "EasyUseAnima.LoraPreset.StrengthButtonStep": "0.025",
                    "EasyUseAnima.LoraPreset.StrengthDragStep": "0.012",
                    "EasyUseAnima.LoraPreset.StrengthDragPixels": "12",
                    "EasyUseAnima.NAIA.Port": "8123",
                    "EasyUseAnima.NAIA.ResolutionMode": "bucket",
                    "EasyUseAnima.NAIA.ResolutionBucket": "1536",
                    "EasyUseAnima.NAIA.ResolutionScale": "1.5",
                    "EasyUseAnima.NAIA.ResolutionMaxLongEdge": "1280",
                },
            ),
        ):
            settings = easyuse_settings.public_settings()

        self.assertEqual(settings["autocomplete.limit"], 7)
        self.assertEqual(settings["autocomplete.commit_key"], "tab")
        self.assertEqual(settings["autocomplete.append_separator"], "true")
        self.assertEqual(settings["autocomplete.no_comma_after_period"], "false")
        self.assertEqual(settings["autocomplete.detect_natural_sentences"], "false")
        self.assertEqual(settings["prompt_studio.typo_indicator"], "false")
        self.assertEqual(settings["prompt_studio.comment_italic"], "false")
        self.assertEqual(settings["lora_preset.name_display"], "path")
        self.assertEqual(settings["lora_preset.menu_mode"], "list")
        self.assertEqual(settings["lora_preset.strength_button_step"], 0.025)
        self.assertEqual(settings["lora_preset.strength_drag_step"], 0.012)
        self.assertEqual(settings["lora_preset.strength_drag_pixels"], 12)
        self.assertEqual(settings["naia.port"], 8123)
        self.assertEqual(settings["naia.resolution_mode"], "bucket")
        self.assertEqual(settings["naia.resolution_bucket"], "1536")
        self.assertEqual(settings["naia.resolution_scale"], 1.5)
        self.assertEqual(settings["naia.resolution_max_long_edge"], 1280)

    def test_comfy_color_settings_merge_into_prompt_studio_colors(self):
        with (
            patch.object(
                easyuse_settings,
                "_read_json_file",
                return_value={"prompt_studio.colors": '{"quality":"#111111"}'},
            ),
            patch.object(
                easyuse_settings,
                "_load_comfy_settings",
                return_value={
                    "EasyUseAnima.Prompt.HighlightColor.quality": "#222222",
                    "EasyUseAnima.Prompt.HighlightColor.artist": "#333333",
                    "EasyUseAnima.Prompt.HighlightColor.wildcard": "#444444",
                },
            ),
        ):
            settings = easyuse_settings.public_settings()

        colors = json.loads(settings["prompt_studio.colors"])
        self.assertEqual(colors["quality"], "#222222")
        self.assertEqual(colors["artist"], "#333333")
        self.assertEqual(colors["wildcard"], "#444444")

    def test_long_text_settings_override_comfy_settings(self):
        root = Path(__file__).resolve().parents[1] / "__pycache__" / "long_text_settings_test"
        shutil.rmtree(root, ignore_errors=True)
        root.mkdir(parents=True, exist_ok=True)
        try:
            with (
                patch.object(easyuse_settings, "SETTINGS_FILE", root / "settings.json"),
                patch.object(
                    easyuse_settings,
                    "LONG_TEXT_SETTINGS_FILE",
                    root / "long_text_settings.json",
                ),
                patch.object(
                    easyuse_settings,
                    "_load_comfy_settings",
                    return_value={
                        "EasyUseAnima.Prompt.MetadataFilter": "comfy filter",
                        "EasyUseAnima.NAIA.pre_prompt": "comfy pre",
                        "EasyUseAnima.NAIA.post_prompt": "comfy post",
                        "EasyUseAnima.NAIA.auto_hide": "comfy hide",
                    },
                ),
            ):
                easyuse_settings.save_long_text_settings(
                    {
                        "prompt.metadata_filter_words": "file filter",
                        "naia.pre_prompt": "file pre",
                        "naia.post_prompt": "file post",
                        "naia.auto_hide": "file hide",
                    }
                )
                settings = easyuse_settings.public_settings()
                naia_settings = easyuse_settings.resolve_naia_settings()
        finally:
            shutil.rmtree(root, ignore_errors=True)

        self.assertEqual(settings["prompt.metadata_filter_words"], "file filter")
        self.assertEqual(settings["naia.pre_prompt"], "file pre")
        self.assertEqual(settings["naia.post_prompt"], "file post")
        self.assertEqual(settings["naia.auto_hide"], "file hide")
        self.assertEqual(naia_settings["pre_prompt"], "file pre")
        self.assertEqual(naia_settings["post_prompt"], "file post")
        self.assertEqual(naia_settings["auto_hide"], "file hide")


class DetailerHookTests(unittest.TestCase):
    def test_detailer_align_hook_alignment_values(self):
        expected_sizes = {
            "none": (1052, 1232),
            "8": (1056, 1232),
            "16": (1056, 1232),
            "32": (1056, 1248),
            "64": (1088, 1280),
        }

        for alignment, expected in expected_sizes.items():
            with self.subTest(alignment=alignment):
                hook, = EasyUseAnimaDetailerAlignHook().build(alignment)
                self.assertEqual(hook.touch_scaled_size(1052, 1232), expected)


class AutocompleteDatasetTests(unittest.TestCase):
    def test_searches_english_tags_and_korean_descriptions(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "tags.csv"
            path.write_text(
                "\n".join(
                    [
                        '1girl,0,100,"[인물] 여성 캐릭터 한 명. 키워드: 여자 1명"',
                        'long hair,0,90,"[패션] 긴 머리, 장발"',
                        'blue eyes,0,80,"[신체] 파란 눈, 벽안"',
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            english = search_autocomplete("long", path=path)
            korean = search_autocomplete("장발", path=path)
            status = autocomplete_status(path)

        self.assertEqual(english["results"][0]["tag"], "long hair")
        self.assertEqual(korean["results"][0]["tag"], "long hair")
        self.assertTrue(status["exists"])
        self.assertEqual(status["count"], 3)

    def test_searches_header_csv_format(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "tags.csv"
            path.write_text(
                "\n".join(
                    [
                        "name,category,post_count,description",
                        '1girl,0,100,"[인물 > 인원수] 여성 캐릭터 한 명. 키워드: 여자 1명"',
                        'hatsune miku,4,90,"[캐릭터] 하츠네 미쿠"',
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            korean = search_autocomplete("하츠네", path=path)
            status = autocomplete_status(path)

        self.assertEqual(korean["results"][0]["tag"], "hatsune miku")
        self.assertEqual(korean["results"][0]["category"], "character")
        self.assertEqual(status["count"], 2)

    def test_autocomplete_cache_reloads_when_csv_mtime_changes(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "tags.csv"
            path.write_text('alpha tag,0,100,"[일반] 첫 태그"\n', encoding="utf-8")

            first = search_autocomplete("alpha", path=path)
            path.write_text('beta tag,0,100,"[일반] 두 번째 태그"\n', encoding="utf-8")
            next_mtime = path.stat().st_mtime_ns + 1_000_000_000
            os.utime(path, ns=(next_mtime, next_mtime))
            second = search_autocomplete("beta", path=path)

        self.assertEqual(first["results"][0]["tag"], "alpha tag")
        self.assertEqual(second["results"][0]["tag"], "beta tag")

    def test_can_limit_autocomplete_to_artist_tags(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "tags.csv"
            path.write_text(
                "\n".join(
                    [
                        'same name,0,100,"[일반] 일반 태그"',
                        'same name artist,1,80,"[작가] 작가 태그"',
                        'artist hit,1,70,"[작가] 검색 대상"',
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            result = search_autocomplete("artist", path=path, category="artist")
            fallback = search_autocomplete("same", path=path, category="artist,general")

        self.assertTrue(result["results"])
        self.assertTrue(all(item["category"] == "artist" for item in result["results"]))
        self.assertTrue({item["category"] for item in fallback["results"]} <= {"artist", "general"})

    def test_lists_autocomplete_sources(self):
        sources = available_autocomplete_sources("localsmile_kr_wiki")

        self.assertTrue(any(source["key"] == "kr_modified" for source in sources))
        self.assertTrue(
            any(
                source["key"] == "localsmile_kr_wiki" and source["selected"]
                for source in sources
            )
        )

    def test_default_autocomplete_source_uses_classified_csv(self):
        key, path = resolve_autocomplete_source("")

        self.assertEqual(key, "localsmile_kr_wiki")
        self.assertEqual(path.name, "danbooru_tags_classified.csv")

    def test_classifies_count_character_and_learned_tags(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "tags.csv"
            path.write_text(
                "\n".join(
                    [
                        '1girl,0,100,"[인물] 여성 캐릭터 한 명"',
                        'hatsune miku,4,90,"[캐릭터] 하츠네 미쿠"',
                        'long hair,0,80,"[헤어] 장발"',
                        'series name,0,70,"[저작권 > 게임] 작품명"',
                        'registered artist,1,60,"[작가] 등록 작가"',
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            result = classify_prompt_text(
                (
                    "1girl, (hatsune miku:0.7), series name, "
                    "(@registered_artist:0.5), @long_hair, "
                    "(@unregistered_artist:0.5), "
                    "(A highly aesthetic Pixiv style illustration, clean composition.:0.6), "
                    "unknown tag"
                ),
                path=path,
            )

        sections = [token["section"] for token in result["tokens"]]
        self.assertEqual(
            sections,
            [
                "count",
                "character",
                "copyright",
                "artist",
                "general",
                "artist_unknown",
                "natural",
                "natural",
                "unknown",
            ],
        )
        self.assertTrue(result["tokens"][0]["learned"])
        self.assertTrue(result["tokens"][1]["learned"])
        self.assertEqual(result["tokens"][1]["base"], "hatsune miku")
        self.assertEqual(result["tokens"][3]["base"], "registered_artist")
        self.assertTrue(result["tokens"][3]["weighted"])
        self.assertEqual(result["tokens"][4]["base"], "long_hair")
        self.assertTrue(result["tokens"][4]["learned"])
        self.assertEqual(result["tokens"][5]["base"], "unregistered_artist")
        self.assertTrue(result["tokens"][5]["weighted"])
        self.assertEqual(result["tokens"][6]["base"], "A highly aesthetic Pixiv style illustration")
        self.assertEqual(result["tokens"][7]["base"], "clean composition.")
        self.assertTrue(result["tokens"][6]["weighted"])
        self.assertTrue(result["tokens"][7]["weighted"])
        self.assertFalse(result["tokens"][8]["learned"])

    def test_line_start_hash_comments_are_classified_and_removed_from_prompt_tokens(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "tags.csv"
            path.write_text('blue eyes,0,100,"[신체] 파란 눈"\n', encoding="utf-8")
            prompt = "# memo, with comma\n1girl, blue eyes\n  # second memo"

            classified = classify_prompt_text(prompt, path=path)

        self.assertEqual(
            [(token["token"], token["section"]) for token in classified["tokens"]],
            [
                ("# memo, with comma", "comment"),
                ("1girl", "count"),
                ("blue eyes", "general"),
                ("  # second memo", "comment"),
            ],
        )
        self.assertEqual(_prompt_tokens(prompt), ["1girl", "blue eyes"])

    def test_inline_hash_and_slash_sequences_stay_in_prompt_text(self):
        prompt = "1girl, # not a line comment\nhttp://example.com/ref, foo//bar"
        classified = classify_prompt_text(prompt)

        self.assertNotIn("comment", [token["section"] for token in classified["tokens"]])
        self.assertEqual(
            _prompt_tokens(prompt),
            ["1girl", "# not a line comment", "http://example.com/ref", "foo//bar"],
        )
        self.assertEqual(_clean_prompt(prompt), prompt)

    def test_classifies_count_after_natural_language_sentence(self):
        result = classify_prompt_text(
            (
                "An intelligent and neat girl with long silver hair and grey eyes wearing glasses "
                "and an elegant white fantasy academy uniform. She has a sharp sword sheathed "
                "at her waist, standing calmly inside a grand academy principal office next to "
                "a large desk. The shot is captured from the thighs up. 1girl, silver hair"
            )
        )

        sections = [token["section"] for token in result["tokens"][:4]]
        self.assertEqual(sections, ["natural", "natural", "count", "unknown"])
        self.assertEqual(result["tokens"][2]["base"], "1girl")

    def test_builtin_meta_quality_tags_are_classified_but_not_autocompleted(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "tags.csv"
            path.write_text(
                'unrelated tag,0,1,"[일반] 자동완성 테스트"\n',
                encoding="utf-8",
            )

            classified = classify_prompt_text(
                "rating_safe, score_9, score_7:, year_2024, source_anime, lowres, very_aesthetic",
                path=path,
            )
            autocomplete = search_autocomplete("score", path=path)

        self.assertEqual(
            [token["section"] for token in classified["tokens"]],
            ["safety", "quality", "quality", "year", "meta", "meta", "quality"],
        )
        self.assertEqual(classified["tokens"][2]["base"], "score_7")
        self.assertEqual([token["learned"] for token in classified["tokens"]], [False] * 7)
        self.assertEqual(autocomplete["results"], [])

    def test_weighted_group_classifies_each_comma_separated_token(self):
        classified = classify_prompt_text("(highres, absurdres, very aesthetic:0.8)")

        self.assertEqual(
            [token["base"] for token in classified["tokens"]],
            ["highres", "absurdres", "very aesthetic"],
        )
        self.assertEqual(
            [token["section"] for token in classified["tokens"]],
            ["meta", "meta", "quality"],
        )
        self.assertEqual([token["weighted"] for token in classified["tokens"]], [True, True, True])

    def test_prompt_escape_characters_are_ignored_for_tag_matching(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "tags.csv"
            path.write_text(
                'western comics (style),0,10,"[일반] western comics style"\n',
                encoding="utf-8",
            )

            classified = classify_prompt_text(r"western comics \(style\)", path=path)

        self.assertEqual(classified["tokens"][0]["base"], "western comics (style)")
        self.assertEqual(classified["tokens"][0]["section"], "general")
        self.assertTrue(classified["tokens"][0]["learned"])

    def test_unbalanced_parentheses_are_syntax_errors(self):
        classified = classify_prompt_text("(highres, absurdres")

        self.assertEqual(len(classified["tokens"]), 1)
        self.assertEqual(classified["tokens"][0]["section"], "syntax")
        self.assertEqual(classified["tokens"][0]["label"], "문법 오류")


if __name__ == "__main__":
    unittest.main()
