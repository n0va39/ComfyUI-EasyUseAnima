from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import settings as easyuse_settings
from nodes import (
    ADVANCED_RESOLUTION_BUCKETS,
    DEFAULT_QUALITY_TAGS,
    DEFAULT_TRAILING_QUALITY_TAGS,
    EasyUseAnimaPromptBuilder,
    EasyUseAnimaPromptCorrector,
    EasyUseAnimaPromptStudio,
    EasyUseAnimaPromptStudioAdvanced,
    EasyUseAnimaPromptStudioExtend,
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
    resolve_autocomplete_limit,
    resolve_autocomplete_mode,
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

        positive, negative, _quality, _use_amg, _metadata, metadata_negative, _width, _height = result["result"]
        self.assertEqual(positive, "score_8, score_7")
        self.assertEqual(negative, "score_5, score_4")
        self.assertEqual(metadata_negative, "score_5, score_4")


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

        positive, negative, quality, use_amg, metadata, metadata_negative, width, height = result["result"]
        self.assertNotIn("masterpiece", positive)
        self.assertEqual(quality, "masterpiece")
        self.assertTrue(use_amg)
        self.assertEqual(negative, "low quality, bad hands")
        self.assertIn("masterpiece", metadata)
        self.assertEqual(metadata_negative, negative)
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
        self.assertEqual(result["result"][-2:], (992, 768))
        self.assertFalse(workflow_prompt["9"]["inputs"]["use_naia"])
        self.assertEqual(workflow_prompt["9"]["inputs"]["resolution_bucket"], "Custom")
        self.assertEqual(workflow_prompt["9"]["inputs"]["resolution_custom_width"], 992)
        self.assertEqual(workflow_prompt["9"]["inputs"]["resolution_custom_height"], 768)
        self.assertEqual(payload["resolution_bucket"], "Custom")
        self.assertEqual(payload["resolution_custom_width"], 992)
        self.assertEqual(payload["resolution_custom_height"], 768)
        self.assertFalse(extra_pnginfo["workflow"]["nodes"][0]["widgets_values"][0])
        self.assertEqual(extra_pnginfo["workflow"]["nodes"][0]["widgets_values"][3], "Custom")
        self.assertEqual(extra_pnginfo["workflow"]["nodes"][0]["widgets_values"][5], 992)
        self.assertEqual(extra_pnginfo["workflow"]["nodes"][0]["widgets_values"][6], 768)

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

        self.assertEqual(result["result"][-2:], (896, 1152))

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

        self.assertEqual(result["result"][-2:], (992, 768))

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

        positive, negative, quality, use_amg, metadata, metadata_negative = result["result"]
        payload = result["ui"]["prompt_studio_slots"][0]

        self.assertTrue(use_amg)
        self.assertEqual(quality, "masterpiece, best quality")
        self.assertNotIn("masterpiece", positive)
        self.assertIn("1girl", positive)
        self.assertIn("location", positive)
        self.assertEqual(negative, "low quality, bad hands")
        self.assertIn("masterpiece", metadata)
        self.assertEqual(metadata_negative, negative)
        self.assertEqual(payload["naia_prompt_3"], "1girl")

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

        positive, negative, quality, use_amg, metadata, metadata_negative = result["result"]
        payload = result["ui"]["prompt_studio_slots"][0]

        self.assertFalse(use_amg)
        self.assertEqual(positive, "visible general")
        self.assertEqual(metadata, "visible general")
        self.assertEqual(negative, "")
        self.assertEqual(metadata_negative, "")
        self.assertEqual(quality, "")
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
                "lora_preset.name_display",
                "prompt_studio.typo_indicator",
                "prompt_studio.colors",
                "prompt_studio.naia_general_above_auto_toggle",
                "naia.host",
                "naia.port",
                "naia.use_naia_settings",
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

    def test_comfy_settings_override_legacy_settings(self):
        with (
            patch.object(easyuse_settings, "_read_json_file", return_value={}),
            patch.object(
                easyuse_settings,
                "_load_comfy_settings",
                return_value={
                    "EasyUseAnima.Prompt.AutocompleteLimit": "7",
                    "EasyUseAnima.Prompt.TypoIndicator": "false",
                    "EasyUseAnima.LoraPreset.NameDisplay": "path",
                    "EasyUseAnima.NAIA.Port": "8123",
                },
            ),
        ):
            settings = easyuse_settings.public_settings()

        self.assertEqual(settings["autocomplete.limit"], 7)
        self.assertEqual(settings["prompt_studio.typo_indicator"], "false")
        self.assertEqual(settings["lora_preset.name_display"], "path")
        self.assertEqual(settings["naia.port"], 8123)

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
                },
            ),
        ):
            settings = easyuse_settings.public_settings()

        colors = json.loads(settings["prompt_studio.colors"])
        self.assertEqual(colors["quality"], "#222222")
        self.assertEqual(colors["artist"], "#333333")

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
