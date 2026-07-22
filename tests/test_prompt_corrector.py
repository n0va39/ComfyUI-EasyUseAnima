from __future__ import annotations

import itertools
import json
import os
import shutil
import tempfile
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import patch

import autocomplete_dataset
import settings as easyuse_settings
from easyuse_anima.nodes.prompt_advanced_nodes import EasyUseAnimaPromptStudioExtend
from easyuse_anima.prompt.fields import (
    DEFAULT_QUALITY_TAGS,
    DEFAULT_TRAILING_QUALITY_TAGS,
)
from nodes import (
    ADVANCED_FIELDS_WORKFLOW_PROPERTY,
    ADVANCED_RESOLUTION_BUCKETS,
    ARTIST_MIX_CONTROL_KEY,
    ARTIST_MIX_EXACT_KEY,
    ARTIST_MIX_MODE_CLUSTERED,
    ARTIST_MIX_MODE_DELTA_RMS,
    ARTIST_MIX_MODE_FROM_PROMPT_DATA,
    ARTIST_MIX_MODE_HYBRID,
    ARTIST_MIX_MODE_PROMPT,
    ARTIST_TAG_POSITION_BACK,
    ARTIST_TAG_POSITION_CORRECT,
    ARTIST_TAG_POSITION_FRONT,
    PROMPT_DATA_SCHEMA,
    PROMPT_DATA_TYPE,
    EasyUseAnimaArtistMixConditioning,
    EasyUseAnimaDetailerAlignHook,
    EasyUseAnimaPromptDataConditioning,
    EasyUseAnimaPromptDataUnpack,
    EasyUseAnimaPromptBuilder,
    EasyUseAnimaPromptCorrector,
    EasyUseAnimaPromptCorrectorSimple,
    EasyUseAnimaPromptStudio,
    EasyUseAnimaPromptStudioAdvanced,
    EasyUseAnimaPromptStudioAdvancedV2,
    _SPECTRUM_ANIMA_MOD_GUIDANCE_OLD_SIGNATURE_WARNED,
    _clean_prompt,
    _generate_empty_latent_with_comfy,
    _prompt_tokens,
)
from autocomplete_dataset import (
    autocomplete_status,
    available_autocomplete_sources,
    classify_prompt_text,
    resolve_autocomplete_source,
    search_autocomplete,
)
from prompt_translation import (
    PROMPT_TRANSLATION_PROVIDER_GOOGLE,
    PROMPT_TRANSLATION_PROVIDER_OFF,
    PromptTranslationSettings,
    normalize_prompt_translation_provider,
    strip_prompt_translation_markers,
    translate_prompt_markers,
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
    resolve_prompt_studio_font_family,
    resolve_prompt_studio_font_size,
)
from wildcard_engine import expand_wildcards


class PromptCorrectorTests(unittest.TestCase):
    def test_simple_node_has_single_prompt_input_and_output(self):
        input_types = EasyUseAnimaPromptCorrectorSimple.INPUT_TYPES()

        self.assertEqual(list(input_types["required"].keys()), ["prompt"])
        self.assertEqual(EasyUseAnimaPromptCorrectorSimple.RETURN_TYPES, ("STRING",))
        self.assertEqual(EasyUseAnimaPromptCorrectorSimple.RETURN_NAMES, ("prompt",))

    def test_simple_node_uses_same_correction_rules_without_report(self):
        prompt = "long_hair, 1girl, long_hair"

        simple = EasyUseAnimaPromptCorrectorSimple().correct(prompt)[0]
        full = EasyUseAnimaPromptCorrector().correct(prompt, "", "")[0]

        self.assertEqual(simple, full)
        self.assertEqual(simple, "1girl, long hair")

    def test_corrects_without_external_data(self):
        corrected, report = EasyUseAnimaPromptCorrector().correct(
            "long_hair, 1girl, long_hair",
            "",
            "",
        )

        self.assertEqual(corrected, "1girl, long hair")
        data = json.loads(report)
        self.assertEqual(data["duplicate_tags"], ["long hair"])

    def test_prompt_translation_marker_translates_only_wrapped_text(self):
        def fake_translate(text, source="auto", target="en"):
            self.assertEqual(source, "ko")
            self.assertEqual(target, "en")
            return {"빨간 머리의 소녀": "girl with red hair"}[text]

        with patch("prompt_translation.google_translate_text", side_effect=fake_translate):
            translated = translate_prompt_markers(
                "1girl, %{빨간 머리의 소녀}, blue eyes",
                PromptTranslationSettings(
                    provider=PROMPT_TRANSLATION_PROVIDER_GOOGLE,
                    source="ko",
                    target="en",
                ),
            )

        self.assertEqual(translated, "1girl, girl with red hair, blue eyes")

    def test_prompt_translation_marker_off_mode_unwraps_without_external_call(self):
        self.assertEqual(
            strip_prompt_translation_markers(r"1girl, %{검은 드레스}, \%{literal}"),
            r"1girl, 검은 드레스, \%{literal}",
        )

    def test_prompt_translation_defaults_off_and_does_not_auto_read_api_keys(self):
        self.assertEqual(PromptTranslationSettings().provider, PROMPT_TRANSLATION_PROVIDER_OFF)
        self.assertEqual(normalize_prompt_translation_provider("unknown"), PROMPT_TRANSLATION_PROVIDER_OFF)
        source = (Path(__file__).resolve().parents[1] / "prompt_translation.py").read_text(
            encoding="utf-8"
        )
        self.assertNotIn("GOOGLE_TRANSLATION_API_KEY", source)
        self.assertNotIn("requests.post", source)

    def test_sync_node_output_and_translation_change_key_contracts_are_preserved(self):
        off_settings = PromptTranslationSettings(
            provider=PROMPT_TRANSLATION_PROVIDER_OFF,
            source="auto",
            target="en",
        )
        google_settings = PromptTranslationSettings(
            provider=PROMPT_TRANSLATION_PROVIDER_GOOGLE,
            source="ko",
            target="ja",
        )

        with patch("nodes.resolve_prompt_translation_settings", return_value=off_settings):
            result = EasyUseAnimaPromptCorrectorSimple().correct("%{long_hair, 1girl}")
            off_key = EasyUseAnimaPromptCorrectorSimple.IS_CHANGED(
                prompt="%{long_hair, 1girl}"
            )
            repeated_off_key = EasyUseAnimaPromptCorrectorSimple.IS_CHANGED(
                prompt="%{long_hair, 1girl}"
            )

        with patch("nodes.resolve_prompt_translation_settings", return_value=google_settings):
            google_key = EasyUseAnimaPromptCorrectorSimple.IS_CHANGED(
                prompt="%{long_hair, 1girl}"
            )

        self.assertEqual(result, ("1girl, long hair",))
        self.assertEqual(EasyUseAnimaPromptCorrectorSimple.RETURN_TYPES, ("STRING",))
        self.assertEqual(EasyUseAnimaPromptCorrectorSimple.RETURN_NAMES, ("prompt",))
        self.assertEqual(off_key, repeated_off_key)
        self.assertNotEqual(off_key, google_key)
        self.assertEqual(
            json.loads(off_key)["prompt_translation"],
            {"provider": "off", "source": "auto", "target": "en"},
        )
        self.assertEqual(
            json.loads(google_key)["prompt_translation"],
            {"provider": "google", "source": "ko", "target": "ja"},
        )

    def test_prompt_correctors_translate_marked_text_before_correction(self):
        with (
            patch(
                "nodes.resolve_prompt_translation_settings",
                return_value=PromptTranslationSettings(
                    provider=PROMPT_TRANSLATION_PROVIDER_GOOGLE,
                    source="ko",
                    target="en",
                ),
            ),
            patch("prompt_translation.google_translate_text", return_value="long_hair, 1girl"),
        ):
            corrected, report = EasyUseAnimaPromptCorrector().correct("%{긴 머리 소녀}", "", "")
            simple = EasyUseAnimaPromptCorrectorSimple().correct("%{긴 머리 소녀}")[0]

        self.assertEqual(corrected, "1girl, long hair")
        self.assertEqual(simple, "1girl, long hair")
        self.assertTrue(json.loads(report)["changed"])

    def test_prompt_builder_translates_marked_text_before_correction(self):
        with (
            patch(
                "nodes.resolve_prompt_translation_settings",
                return_value=PromptTranslationSettings(
                    provider=PROMPT_TRANSLATION_PROVIDER_GOOGLE,
                    source="ko",
                    target="en",
                ),
            ),
            patch("prompt_translation.google_translate_text", return_value="girl with red hair"),
        ):
            prompt, _quality, _use_amg, metadata_prompt = EasyUseAnimaPromptBuilder().build(
                False,
                False,
                "",
                "",
                "",
                "%{빨간 머리의 소녀}",
                "",
            )

        self.assertEqual(prompt, "girl with red hair")
        self.assertEqual(metadata_prompt, "girl with red hair")

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
        required_names = list(EasyUseAnimaPromptStudioAdvancedV2.INPUT_TYPES()["required"])
        self.assertEqual(
            required_names[-9:],
            [
                "artist_mix_mode",
                "artist_mix_start_percent",
                "artist_mix_strength_scale",
                "artist_mix_style_gain",
                "artist_mix_rms_scale_cap",
                "artist_mix_exact_top_k",
                "artist_mix_cluster_count",
                "artist_mix_dominant_isolation",
                "artist_mix_dominant_threshold",
            ],
        )
        self.assertEqual(
            EasyUseAnimaPromptStudioAdvancedV2.INPUT_TYPES()["required"]["artist_mix_mode"][1]["default"],
            "off",
        )

    def test_prompt_data_unpack_uses_prompt_data_type_as_socket_name(self):
        input_types = EasyUseAnimaPromptDataUnpack.INPUT_TYPES()
        self.assertIn(PROMPT_DATA_TYPE, input_types["required"])
        for name in EasyUseAnimaPromptStudioAdvanced.RETURN_NAMES:
            self.assertIn(name, input_types["optional"])
        self.assertEqual(EasyUseAnimaPromptDataUnpack.RETURN_TYPES[0], PROMPT_DATA_TYPE)
        self.assertEqual(EasyUseAnimaPromptDataUnpack.RETURN_NAMES[0], PROMPT_DATA_TYPE)

    def test_prompt_data_conditioning_uses_prompt_data_socket_and_sampler_outputs(self):
        input_types = EasyUseAnimaPromptDataConditioning.INPUT_TYPES()

        self.assertIn(PROMPT_DATA_TYPE, input_types["required"])
        self.assertEqual(input_types["required"][PROMPT_DATA_TYPE][0], PROMPT_DATA_TYPE)
        self.assertTrue(input_types["required"][PROMPT_DATA_TYPE][1]["forceInput"])
        self.assertIn("artist_mix_mode", input_types["required"])
        self.assertEqual(input_types["required"]["artist_mix_mode"][1]["default"], ARTIST_MIX_MODE_FROM_PROMPT_DATA)
        self.assertEqual(EasyUseAnimaPromptDataConditioning.RETURN_TYPES, ("MODEL", "CONDITIONING", "CONDITIONING", "LATENT"))
        self.assertEqual(EasyUseAnimaPromptDataConditioning.RETURN_NAMES, ("model", "positive", "negative", "latent_image"))

    def test_artist_mix_conditioning_node_uses_standalone_prompt_inputs(self):
        input_types = EasyUseAnimaArtistMixConditioning.INPUT_TYPES()

        for name in (
            "clip",
            "prompt",
            "artist_tags",
            "artist_position",
            "artist_mix_mode",
        ):
            self.assertIn(name, input_types["required"])
        self.assertEqual(
            input_types["required"]["artist_position"][1]["default"],
            ARTIST_TAG_POSITION_CORRECT,
        )
        self.assertEqual(
            input_types["required"]["artist_mix_mode"][1]["default"],
            ARTIST_MIX_MODE_PROMPT,
        )
        self.assertEqual(EasyUseAnimaArtistMixConditioning.RETURN_TYPES, ("CONDITIONING",))
        self.assertEqual(EasyUseAnimaArtistMixConditioning.RETURN_NAMES, ("positive",))

    def test_artist_mix_conditioning_prompt_mode_uses_position_policy(self):
        encoded_texts = []

        def fake_encode(_clip, text):
            encoded_texts.append(text)
            return [[f"cond:{text}", {"encoded_text": text}]]

        with patch("nodes._encode_with_comfy_clip", fake_encode):
            with patch("nodes._correct_builder_prompt", return_value="corrected prompt") as correct_mock:
                positive = EasyUseAnimaArtistMixConditioning().encode(
                    object(),
                    prompt="1girl",
                    artist_tags="artist_a",
                    artist_position=ARTIST_TAG_POSITION_CORRECT,
                    artist_mix_mode=ARTIST_MIX_MODE_PROMPT,
                )[0]

        self.assertEqual(positive[0][1]["encoded_text"], "corrected prompt")
        correct_mock.assert_called_once_with("1girl, artist_a", artist_overrides="artist_a")

        encoded_texts.clear()
        with patch("nodes._encode_with_comfy_clip", fake_encode):
            with patch("nodes._correct_builder_prompt") as correct_mock:
                front_positive = EasyUseAnimaArtistMixConditioning().encode(
                    object(),
                    prompt="1girl",
                    artist_tags="artist_a",
                    artist_position=ARTIST_TAG_POSITION_FRONT,
                    artist_mix_mode=ARTIST_MIX_MODE_PROMPT,
                )[0]
                back_positive = EasyUseAnimaArtistMixConditioning().encode(
                    object(),
                    prompt="1girl",
                    artist_tags="artist_a",
                    artist_position=ARTIST_TAG_POSITION_BACK,
                    artist_mix_mode=ARTIST_MIX_MODE_PROMPT,
                )[0]

        correct_mock.assert_not_called()
        self.assertEqual(front_positive[0][1]["encoded_text"], "artist_a, 1girl")
        self.assertEqual(back_positive[0][1]["encoded_text"], "1girl, artist_a")

    def test_artist_mix_conditioning_exact_mode_keeps_position_policy(self):
        encoded_texts = []

        def fake_encode(_clip, text):
            encoded_texts.append(text)
            return [[f"cond:{text}", {"encoded_text": text}]]

        with patch("nodes._encode_with_comfy_clip", fake_encode):
            positive = EasyUseAnimaArtistMixConditioning().encode(
                object(),
                prompt="1girl",
                artist_tags="artist_a, artist_b",
                artist_position=ARTIST_TAG_POSITION_FRONT,
                artist_mix_mode="exact",
            )[0]

        self.assertEqual(len(positive), 2)
        self.assertTrue(all(item[1][ARTIST_MIX_CONTROL_KEY] for item in positive))
        self.assertTrue(all(item[1][ARTIST_MIX_EXACT_KEY] for item in positive))
        self.assertEqual(encoded_texts[:2], ["artist_a, 1girl", "artist_b, 1girl"])

    def test_artist_mix_conditioning_groups_multiple_artists_in_one_branch(self):
        encoded_texts = []

        def fake_encode(_clip, text):
            encoded_texts.append(text)
            return [[f"cond:{text}", {"encoded_text": text}]]

        with patch("nodes._encode_with_comfy_clip", fake_encode):
            positive = EasyUseAnimaArtistMixConditioning().encode(
                object(),
                prompt="1girl",
                artist_tags="[[artist_a, artist_b:0.25]], artist_c",
                artist_position=ARTIST_TAG_POSITION_FRONT,
                artist_mix_mode="exact",
            )[0]

        self.assertEqual(len(positive), 2)
        self.assertEqual(encoded_texts[:2], ["artist_a, artist_b, 1girl", "artist_c, 1girl"])
        self.assertAlmostEqual(positive[0][1]["strength"], 0.2)
        self.assertAlmostEqual(positive[1][1]["strength"], 0.8)
        self.assertTrue(all(item[1][ARTIST_MIX_EXACT_KEY] for item in positive))

    def test_artist_mix_conditioning_prompt_mode_flattens_group_weight(self):
        encoded_texts = []

        def fake_encode(_clip, text):
            encoded_texts.append(text)
            return [[f"cond:{text}", {"encoded_text": text}]]

        with patch("nodes._encode_with_comfy_clip", fake_encode):
            EasyUseAnimaArtistMixConditioning().encode(
                object(),
                prompt="1girl",
                artist_tags="[[artist_a, artist_b:0.25]], artist_c",
                artist_position=ARTIST_TAG_POSITION_FRONT,
                artist_mix_mode=ARTIST_MIX_MODE_PROMPT,
            )

        self.assertEqual(encoded_texts[:1], ["artist_a, artist_b, artist_c, 1girl"])

    def test_empty_latent_generation_uses_comfy_node_with_batch_size_one(self):
        calls = []

        class FakeEmptyLatentImage:
            def generate(self, width, height, batch_size=1):
                calls.append((width, height, batch_size))
                return ({"samples": "latent"},)

        with patch("nodes._find_comfy_node_class", lambda node_id: FakeEmptyLatentImage if node_id == "EmptyLatentImage" else None):
            latent = _generate_empty_latent_with_comfy(832, 1216)

        self.assertEqual(latent, {"samples": "latent"})
        self.assertEqual(calls, [(832, 1216, 1)])

    def test_prompt_data_conditioning_encodes_prompt_data_without_mod_guidance(self):
        model = object()
        prompt_data = {
            "positive_prompt": "1girl",
            "negative_prompt": "bad hands",
            "width": 832,
            "height": 1216,
            "mod_guidance": {
                "enabled": False,
            },
        }

        with patch("nodes._encode_with_comfy_clip", lambda clip, text: [[f"cond:{text}", {"encoded_text": text}]]):
            with patch("nodes._generate_empty_latent_with_comfy", lambda width, height: {"samples": (width, height, 1)}):
                patched_model, positive, negative, latent_image = EasyUseAnimaPromptDataConditioning().apply(
                    model,
                    clip=object(),
                    EASYUSE_ANIMA_PROMPT_DATA=prompt_data,
                )

        self.assertIs(patched_model, model)
        self.assertEqual(positive[0][1]["encoded_text"], "1girl")
        self.assertEqual(negative[0][1]["encoded_text"], "bad hands")
        self.assertEqual(latent_image, {"samples": (832, 1216, 1)})

    def test_prompt_data_conditioning_applies_spectrum_mod_guidance(self):
        calls = []

        class FakeAnimaModGuidance:
            def patch(
                self,
                model,
                clip,
                quality_tags,
                mod_w_profile,
                positive,
                negative,
            ):
                calls.append({
                    "model": model,
                    "clip": clip,
                    "quality_tags": quality_tags,
                    "mod_w_profile": mod_w_profile,
                    "positive": positive,
                    "negative": negative,
                })
                return ("patched-model",)

        model = object()
        clip = object()
        prompt_data = {
            "positive_prompt": "1girl",
            "negative_prompt": "bad hands",
            "mod_guidance": {
                "enabled": True,
                "negative_enabled": True,
                "quality_tags": "masterpiece",
                "negative_prompt": "worst quality",
            },
        }

        _SPECTRUM_ANIMA_MOD_GUIDANCE_OLD_SIGNATURE_WARNED.clear()
        with patch("nodes._encode_with_comfy_clip", lambda clip, text: [[f"cond:{text}", {"encoded_text": text}]]):
            with patch("nodes._generate_empty_latent_with_comfy", lambda width, height: {"samples": (width, height, 1)}):
                with patch("nodes._find_spectrum_anima_mod_guidance_class", lambda: FakeAnimaModGuidance):
                    with patch("nodes.logger.warning") as warning_mock:
                        patched_model, positive, negative, latent_image = EasyUseAnimaPromptDataConditioning().apply(
                            model,
                            clip=clip,
                            EASYUSE_ANIMA_PROMPT_DATA=prompt_data,
                            mod_w_profile="step_i14",
                        )

        self.assertEqual(patched_model, "patched-model")
        self.assertEqual(latent_image, {"samples": (1024, 1024, 1)})
        self.assertEqual(len(calls), 1)
        self.assertIs(calls[0]["model"], model)
        self.assertIs(calls[0]["clip"], clip)
        self.assertEqual(calls[0]["quality_tags"], "masterpiece")
        self.assertEqual(calls[0]["mod_w_profile"], "step_i14")
        self.assertEqual(calls[0]["positive"], positive)
        self.assertEqual(calls[0]["negative"], negative)
        warning_mock.assert_called_once()
        self.assertIn("old patch() signature", warning_mock.call_args.args[0])

    def test_prompt_data_conditioning_supports_future_mod_guidance_quality_neg(self):
        calls = []

        class FakeAnimaModGuidance:
            def patch(
                self,
                model,
                clip,
                quality_tags,
                quality_neg,
                mod_w_profile,
                positive,
                negative,
            ):
                calls.append({
                    "quality_tags": quality_tags,
                    "quality_neg": quality_neg,
                    "mod_w_profile": mod_w_profile,
                })
                return ("patched-model",)

        prompt_data = {
            "positive_prompt": "1girl",
            "negative_prompt": "bad hands",
            "mod_guidance": {
                "enabled": True,
                "negative_enabled": True,
                "quality_tags": "masterpiece",
                "negative_prompt": "worst quality",
            },
        }

        _SPECTRUM_ANIMA_MOD_GUIDANCE_OLD_SIGNATURE_WARNED.clear()
        with patch("nodes._encode_with_comfy_clip", lambda clip, text: [[f"cond:{text}", {"encoded_text": text}]]):
            with patch("nodes._generate_empty_latent_with_comfy", lambda width, height: {"samples": (width, height, 1)}):
                with patch("nodes._find_spectrum_anima_mod_guidance_class", lambda: FakeAnimaModGuidance):
                    with patch("nodes.logger.warning") as warning_mock:
                        patched_model, _positive, _negative, _latent_image = EasyUseAnimaPromptDataConditioning().apply(
                            object(),
                            clip=object(),
                            EASYUSE_ANIMA_PROMPT_DATA=prompt_data,
                            mod_w_profile="step_i14",
                        )

        self.assertEqual(patched_model, "patched-model")
        self.assertEqual(calls, [{
            "quality_tags": "masterpiece",
            "quality_neg": "worst quality",
            "mod_w_profile": "step_i14",
        }])
        warning_mock.assert_not_called()

    def test_prompt_data_conditioning_average_artist_mix_rebuilds_artist_position(self):
        fields = [
            {
                "id": "quality",
                "pane": "positive",
                "type": "quality",
                "label": "Quality Tags",
                "text": "masterpiece",
                "height": 72,
            },
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
                "id": "trailing",
                "pane": "positive",
                "type": "general",
                "label": "General Tags",
                "text": "location",
                "height": 72,
            },
        ]
        prompt_data = EasyUseAnimaPromptStudioAdvancedV2().build(
            False,
            True,
            False,
            False,
            json.dumps(fields),
        )["result"][0]
        encoded_texts = []

        def fake_encode(_clip, text):
            encoded_texts.append(text)
            return [[f"cond:{text}", {"encoded_text": text}]]

        def fake_blend(conditionings, weights, composite_conditioning=None):
            return [[
                "blended",
                {
                    "weights": tuple(weights),
                    "composite": composite_conditioning[0][1]["encoded_text"],
                    "encoded_text": conditionings[0][0][1]["encoded_text"],
                },
            ]]

        with patch("nodes._encode_with_comfy_clip", fake_encode):
            with patch("nodes._blend_conditionings", fake_blend):
                with patch("nodes._generate_empty_latent_with_comfy", lambda width, height: {"samples": (width, height, 1)}):
                    _model, positive, _negative, _latent = EasyUseAnimaPromptDataConditioning().apply(
                        object(),
                        clip=object(),
                        EASYUSE_ANIMA_PROMPT_DATA=prompt_data,
                        artist_mix_mode="average",
                    )

        self.assertEqual(len(positive), 1)
        self.assertIn("artist_a", encoded_texts[0])
        self.assertIn("1girl", encoded_texts[0])
        self.assertIn("location", encoded_texts[0])
        self.assertLess(encoded_texts[0].index("1girl"), encoded_texts[0].index("artist_a"))
        self.assertLess(encoded_texts[0].index("artist_a"), encoded_texts[0].index("location"))
        self.assertNotIn("artist_a", prompt_data["positive_without_artist_section"])
        self.assertEqual(encoded_texts[-1], "")

    def test_prompt_data_conditioning_exact_artist_mix_marks_conditioning(self):
        prompt_data = {
            "positive_prompt": "masterpiece, artist_a, 1girl",
            "negative_prompt": "bad hands",
            "positive_without_artist_section": "masterpiece, 1girl",
            "artist_mix": {
                "enabled": True,
                "mode": "exact",
                "base_source": "positive_without_artist_section",
                "artist_prompt": "(artist_a:2), artist_b",
                "strength_scale": 2.0,
            },
        }
        encoded_texts = []

        def fake_encode(_clip, text):
            encoded_texts.append(text)
            return [[f"cond:{text}", {"encoded_text": text}]]

        with patch("nodes._encode_with_comfy_clip", fake_encode):
            with patch("nodes._generate_empty_latent_with_comfy", lambda width, height: {"samples": (width, height, 1)}):
                _model, positive, _negative, _latent = EasyUseAnimaPromptDataConditioning().apply(
                    object(),
                    clip=object(),
                    EASYUSE_ANIMA_PROMPT_DATA=prompt_data,
                    artist_mix_mode=ARTIST_MIX_MODE_FROM_PROMPT_DATA,
                    artist_mix_strength_scale=0.25,
                )

        self.assertEqual(len(positive), 2)
        self.assertTrue(all(item[1][ARTIST_MIX_CONTROL_KEY] for item in positive))
        self.assertTrue(all(item[1][ARTIST_MIX_EXACT_KEY] for item in positive))
        self.assertAlmostEqual(positive[0][1]["strength"], 4.0 / 3.0)
        self.assertAlmostEqual(positive[1][1]["strength"], 2.0 / 3.0)
        self.assertIn("masterpiece", encoded_texts[0])
        self.assertIn("1girl", encoded_texts[0])
        self.assertIn("artist_a", encoded_texts[0])

    def test_prompt_data_conditioning_exact_artist_mix_coalesces_duplicate_artists(self):
        prompt_data = {
            "positive_prompt": "masterpiece, 1girl",
            "negative_prompt": "",
            "positive_without_artist_section": "masterpiece, 1girl",
            "artist_mix": {
                "enabled": True,
                "mode": "exact",
                "artist_prompt": "(artist_a:2), artist_a, artist_b",
            },
        }
        encoded_texts = []

        def fake_encode(_clip, text):
            encoded_texts.append(text)
            return [[f"cond:{text}", {"encoded_text": text}]]

        with patch("nodes._encode_with_comfy_clip", fake_encode):
            with patch("nodes._generate_empty_latent_with_comfy", lambda width, height: {"samples": (width, height, 1)}):
                _model, positive, _negative, _latent = EasyUseAnimaPromptDataConditioning().apply(
                    object(),
                    clip=object(),
                    EASYUSE_ANIMA_PROMPT_DATA=prompt_data,
                    artist_mix_mode=ARTIST_MIX_MODE_FROM_PROMPT_DATA,
                )

        self.assertEqual(len(positive), 2)
        self.assertAlmostEqual(positive[0][1]["strength"], 0.75)
        self.assertAlmostEqual(positive[1][1]["strength"], 0.25)
        self.assertEqual(sum("artist_a" in text for text in encoded_texts), 1)

    def test_prompt_data_conditioning_hybrid_artist_mix_keeps_top_k_and_compresses_tail(self):
        prompt_data = {
            "positive_prompt": "masterpiece, 1girl",
            "negative_prompt": "",
            "positive_without_artist_section": "masterpiece, 1girl",
            "artist_mix": {
                "enabled": True,
                "mode": "exact",
                "artist_prompt": "(artist_a:4), (artist_b:3), (artist_c:2), artist_d",
            },
        }
        delta_calls = []

        def fake_encode(_clip, text):
            return [[f"cond:{text}", {"encoded_text": text}]]

        def fake_delta(_clip, _data, _base_prompt, artists, weights=None, **kwargs):
            delta_calls.append((artists, list(weights or []), kwargs))
            return [["tail", {"strength": kwargs.get("branch_strength")}]]

        with patch("nodes._encode_with_comfy_clip", fake_encode):
            with patch("nodes._encode_artist_delta_rms", fake_delta):
                with patch("nodes._generate_empty_latent_with_comfy", lambda width, height: {"samples": (width, height, 1)}):
                    _model, positive, _negative, _latent = EasyUseAnimaPromptDataConditioning().apply(
                        object(),
                        clip=object(),
                        EASYUSE_ANIMA_PROMPT_DATA=prompt_data,
                        artist_mix_mode=ARTIST_MIX_MODE_HYBRID,
                        artist_mix_exact_top_k=2,
                    )

        self.assertEqual(len(positive), 3)
        self.assertTrue(all(item[1][ARTIST_MIX_CONTROL_KEY] for item in positive))
        self.assertTrue(positive[0][1][ARTIST_MIX_EXACT_KEY])
        self.assertTrue(positive[1][1][ARTIST_MIX_EXACT_KEY])
        self.assertAlmostEqual(positive[0][1]["strength"], 0.4)
        self.assertAlmostEqual(positive[1][1]["strength"], 0.3)
        self.assertAlmostEqual(positive[2][1]["strength"], 0.3)
        self.assertEqual(delta_calls[0][0], [("artist_c", 2.0), ("artist_d", 1.0)])
        self.assertAlmostEqual(delta_calls[0][1][0], 2.0 / 3.0)
        self.assertAlmostEqual(delta_calls[0][1][1], 1.0 / 3.0)

    def test_prompt_data_conditioning_new_artist_mix_modes_route_to_approximation_helpers(self):
        prompt_data = {
            "positive_prompt": "masterpiece, 1girl",
            "negative_prompt": "",
            "positive_without_artist_section": "masterpiece, 1girl",
            "artist_mix": {
                "enabled": True,
                "mode": "prompt",
                "artist_prompt": "artist_a, artist_b",
            },
        }
        calls = []

        def fake_encode(_clip, text):
            return [[f"cond:{text}", {"encoded_text": text}]]

        def fake_delta(*_args, **kwargs):
            calls.append(("delta", kwargs))
            return [["delta", {}]]

        def fake_clustered(*_args, **kwargs):
            calls.append(("clustered", kwargs))
            return [["clustered", {}]]

        with patch("nodes._encode_with_comfy_clip", fake_encode):
            with patch("nodes._encode_artist_delta_rms", fake_delta):
                with patch("nodes._encode_artist_clustered", fake_clustered):
                    with patch("nodes._generate_empty_latent_with_comfy", lambda width, height: {"samples": (width, height, 1)}):
                        _model, delta_positive, _negative, _latent = EasyUseAnimaPromptDataConditioning().apply(
                            object(),
                            clip=object(),
                            EASYUSE_ANIMA_PROMPT_DATA=prompt_data,
                            artist_mix_mode=ARTIST_MIX_MODE_DELTA_RMS,
                            artist_mix_style_gain=1.5,
                            artist_mix_rms_scale_cap=2.5,
                        )
                        _model, clustered_positive, _negative, _latent = EasyUseAnimaPromptDataConditioning().apply(
                            object(),
                            clip=object(),
                            EASYUSE_ANIMA_PROMPT_DATA=prompt_data,
                            artist_mix_mode=ARTIST_MIX_MODE_CLUSTERED,
                            artist_mix_cluster_count=5,
                            artist_mix_dominant_isolation=False,
                            artist_mix_dominant_threshold=0.2,
                        )

        self.assertEqual(delta_positive[0][0], "delta")
        self.assertEqual(clustered_positive[0][0], "clustered")
        self.assertEqual(calls[0][0], "delta")
        self.assertEqual(calls[0][1]["style_gain"], 1.5)
        self.assertEqual(calls[0][1]["rms_scale_cap"], 2.5)
        self.assertEqual(calls[1][0], "clustered")
        self.assertEqual(calls[1][1]["cluster_count"], 5)
        self.assertFalse(calls[1][1]["dominant_isolation"])
        self.assertEqual(calls[1][1]["dominant_threshold"], 0.2)

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
        self.assertEqual(prompt_data["artist"]["text"], "artist_a, artist_b")
        self.assertEqual(prompt_data["artist"]["weighted_text"], "artist_a, artist_b")
        self.assertEqual([entry["tag"] for entry in prompt_data["artist"]["tags"]], ["artist_a", "artist_b"])
        self.assertTrue(prompt_data["artist"]["include_in_positive"])
        self.assertEqual(prompt_data["artist"]["positive_prompt_without_artist"], prompt_data["positive_without_artist_section"])
        self.assertIn("1girl", prompt_data["positive_without_artist_section"])
        self.assertNotIn("artist_a", prompt_data["positive_without_artist_section"])
        self.assertEqual(prompt_data["global_prompt"], prompt_data["positive_without_artist_section"])
        self.assertFalse(prompt_data["artist_mix"]["enabled"])
        self.assertEqual(prompt_data["artist_mix"]["mode"], "prompt")
        self.assertEqual(prompt_data["artist_mix"]["base_source"], "positive_without_artist_section")
        self.assertEqual(prompt_data["artist_mix"]["start_percent"], 0.5)
        self.assertEqual(prompt_data["artist_mix"]["strength_scale"], 1.0)
        self.assertEqual(prompt_data["artist_mix"]["style_gain"], 1.35)
        self.assertEqual(prompt_data["artist_mix"]["rms_scale_cap"], 2.0)
        self.assertEqual(prompt_data["artist_mix"]["exact_top_k"], 4)
        self.assertEqual(prompt_data["artist_mix"]["cluster_count"], 4)
        self.assertTrue(prompt_data["artist_mix"]["dominant_isolation"])
        self.assertEqual(prompt_data["artist_mix"]["dominant_threshold"], 0.25)
        self.assertEqual(prompt_data["artist_mix"]["artist_prompt"], "artist_a, artist_b")
        self.assertEqual(prompt_data["width"], 896)
        self.assertEqual(prompt_data["height"], 1152)
        self.assertEqual(prompt_data["resolution"]["width"], 896)
        self.assertEqual(prompt_data["resolution"]["height"], 1152)

    def test_prompt_studio_advanced_v2_translates_marked_text_in_prompt_data(self):
        fields = [
            {
                "id": "general",
                "pane": "positive",
                "type": "general",
                "label": "General Tags",
                "text": "1girl, %{빨간 머리의 소녀}",
                "height": 120,
            },
        ]
        with (
            patch(
                "nodes.resolve_prompt_translation_settings",
                return_value=PromptTranslationSettings(
                    provider=PROMPT_TRANSLATION_PROVIDER_GOOGLE,
                    source="ko",
                    target="en",
                ),
            ),
            patch("prompt_translation.google_translate_text", return_value="girl with red hair"),
        ):
            result = EasyUseAnimaPromptStudioAdvancedV2().build(
                False,
                False,
                False,
                False,
                json.dumps(fields),
            )

        prompt_data = result["result"][0]
        ui_fields = json.loads(result["ui"]["prompt_studio_advanced"][0]["advanced_fields"])
        self.assertIn("girl with red hair", prompt_data["positive_prompt"])
        self.assertNotIn("%{", prompt_data["positive_prompt"])
        self.assertEqual(ui_fields[0]["text"], "1girl, %{빨간 머리의 소녀}")

    def test_prompt_studio_advanced_v2_tracks_required_parameters_in_prompt_data(self):
        fields = [
            {
                "id": "general",
                "pane": "positive",
                "type": "general",
                "label": "General Tags",
                "text": "1girl",
                "height": 120,
            },
        ]
        result = EasyUseAnimaPromptStudioAdvancedV2().build(
            True,
            False,
            True,
            True,
            json.dumps(fields),
            use_negative_anima_mod_guidance=True,
            wildcard_mode="순차",
            wildcard_seed=123,
            wildcard_seed_after_generate="increment",
            resolution_bucket="1024",
            resolution_size="896 * 1152 (7:9)",
            artist_mix_mode=ARTIST_MIX_MODE_CLUSTERED,
            artist_mix_start_percent=0.25,
            artist_mix_strength_scale=1.5,
            artist_mix_style_gain=1.6,
            artist_mix_rms_scale_cap=2.5,
            artist_mix_exact_top_k=3,
            artist_mix_cluster_count=5,
            artist_mix_dominant_isolation=False,
            artist_mix_dominant_threshold=0.2,
        )

        prompt_data = result["result"][0]
        required_inputs = set(EasyUseAnimaPromptStudioAdvancedV2.INPUT_TYPES()["required"])

        self.assertFalse(required_inputs - set(prompt_data["parameters"]))
        self.assertTrue(prompt_data["parameters"]["use_naia"])
        self.assertFalse(prompt_data["parameters"]["consume_naia_on_queue"])
        self.assertTrue(prompt_data["parameters"]["use_anima_mod_guidance"])
        self.assertTrue(prompt_data["parameters"]["use_negative_anima_mod_guidance"])
        self.assertTrue(prompt_data["parameters"]["pin_trigger_tags_to_front"])
        self.assertEqual(prompt_data["parameters"]["resolution_bucket"], "1024")
        self.assertEqual(prompt_data["parameters"]["resolution_size"], "896 * 1152 (7:9)")
        self.assertEqual(prompt_data["parameters"]["wildcard_mode"], "순차")
        self.assertEqual(prompt_data["parameters"]["wildcard_seed"], 123)
        self.assertEqual(prompt_data["wildcard"]["seed"], 123)
        self.assertEqual(prompt_data["wildcard"]["next_seed"], 124)
        self.assertEqual(prompt_data["parameters"]["artist_mix_mode"], ARTIST_MIX_MODE_CLUSTERED)
        self.assertEqual(prompt_data["parameters"]["artist_mix_cluster_count"], 5)
        self.assertFalse(prompt_data["parameters"]["artist_mix_dominant_isolation"])
        self.assertTrue(prompt_data["naia"]["use_naia"])
        self.assertFalse(prompt_data["naia"]["consume_on_queue"])

    def test_prompt_studio_advanced_v2_consumes_reserved_queue_next_seed(self):
        fields = [
            {
                "id": "general",
                "pane": "positive",
                "type": "general",
                "label": "General Tags",
                "text": "1girl",
                "height": 120,
            },
        ]
        reservation_key = "easyuse_anima_reserved_wildcard_next_seed"
        reservation_value = json.dumps({
            "version": 1,
            "current_seed": 123,
            "next_seed": 124,
            "mode": "sequential",
            "control": "increment",
        })
        workflow_prompt = {
            "42": {"inputs": {reservation_key: reservation_value}}
        }
        extra_pnginfo = {
            "workflow": {
                "nodes": [
                    {
                        "id": 42,
                        "widgets_values": [],
                    }
                ]
            }
        }

        result = EasyUseAnimaPromptStudioAdvancedV2().build(
            False,
            False,
            False,
            False,
            json.dumps(fields),
            wildcard_mode="순차",
            wildcard_seed=123,
            wildcard_seed_after_generate="increment",
            workflow_prompt=workflow_prompt,
            extra_pnginfo=extra_pnginfo,
            unique_id="42",
            **{reservation_key: reservation_value},
        )

        prompt_data = result["result"][0]
        self.assertEqual(prompt_data["parameters"]["wildcard_seed"], 123)
        self.assertEqual(prompt_data["wildcard"]["seed"], 123)
        self.assertEqual(prompt_data["wildcard"]["next_seed"], 124)
        self.assertEqual(result["ui"]["prompt_studio_advanced"][0]["wildcard_seed"], 124)
        self.assertNotIn(
            reservation_key,
            extra_pnginfo["workflow"]["nodes"][0].get("properties", {}),
        )
        self.assertNotIn(reservation_key, workflow_prompt["42"]["inputs"])

        malformed_pnginfo = {
            "workflow": {
                "nodes": [
                    {
                        "id": 42,
                        "widgets_values": [],
                    }
                ]
            }
        }
        mismatched_value = json.dumps({
            "version": 1,
            "current_seed": 123,
            "next_seed": 456,
            "mode": "sequential",
            "control": "increment",
        })
        malformed_prompt = {
            "42": {"inputs": {reservation_key: mismatched_value}}
        }
        fallback = EasyUseAnimaPromptStudioAdvancedV2().build(
            False,
            False,
            False,
            False,
            json.dumps(fields),
            wildcard_mode="순차",
            wildcard_seed=123,
            wildcard_seed_after_generate="increment",
            workflow_prompt=malformed_prompt,
            extra_pnginfo=malformed_pnginfo,
            unique_id="42",
            **{reservation_key: mismatched_value},
        )
        self.assertEqual(fallback["result"][0]["wildcard"]["next_seed"], 124)
        self.assertNotIn(
            reservation_key,
            malformed_pnginfo["workflow"]["nodes"][0].get("properties", {}),
        )
        self.assertNotIn(reservation_key, malformed_prompt["42"]["inputs"])

    def test_prompt_studio_advanced_v2_artist_mix_mode_separates_artist_prompt(self):
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
        ]
        result = EasyUseAnimaPromptStudioAdvancedV2().build(
            False,
            True,
            False,
            False,
            json.dumps(fields),
            artist_mix_mode="average",
            artist_mix_start_percent=0.25,
            artist_mix_strength_scale=1.5,
        )

        prompt_data = result["result"][0]
        self.assertEqual(prompt_data["positive_prompt"], prompt_data["positive_without_artist_section"])
        self.assertEqual(prompt_data["outputs"]["positive_prompt"], prompt_data["positive_without_artist_section"])
        self.assertNotIn("artist_a", prompt_data["positive_prompt"])
        self.assertIn("artist_a", prompt_data["artist_mix"]["artist_prompt"])
        self.assertFalse(prompt_data["artist"]["include_in_positive"])
        self.assertEqual(prompt_data["artist"]["handling"], "separate")
        self.assertTrue(prompt_data["artist_mix"]["enabled"])
        self.assertEqual(prompt_data["artist_mix"]["mode"], "average")
        self.assertEqual(prompt_data["artist_mix"]["start_percent"], 0.25)
        self.assertEqual(prompt_data["artist_mix"]["strength_scale"], 1.5)
        ui_payload = result["ui"]["prompt_studio_advanced"][0]
        self.assertEqual(ui_payload["artist_mix_mode"], "average")

    def test_prompt_studio_advanced_v2_preserves_artist_mix_group_syntax_only_for_mix(self):
        fields = [
            {
                "id": "artist",
                "pane": "positive",
                "type": "artist",
                "label": "Artist Tags",
                "text": "[[artist_a, artist_b:0.25]], artist_c",
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
        ]
        result = EasyUseAnimaPromptStudioAdvancedV2().build(
            False,
            True,
            False,
            False,
            json.dumps(fields),
            artist_mix_mode="average",
        )

        prompt_data = result["result"][0]
        self.assertEqual(prompt_data["artist"]["text"], "artist_a, artist_b, artist_c")
        self.assertEqual(prompt_data["artist"]["weighted_text"], "[[artist_a, artist_b:0.25]], artist_c")
        self.assertEqual(prompt_data["artist_mix"]["artist_prompt"], "[[artist_a, artist_b:0.25]], artist_c")
        self.assertEqual(
            [(entry["tag"], entry["weight"], entry["grouped"]) for entry in prompt_data["artist"]["tags"]],
            [("artist_a, artist_b", 0.25, True), ("artist_c", 1.0, False)],
        )
        self.assertEqual(prompt_data["artist_mix"]["artist_count_hint"], 2)
        self.assertNotIn("[[", prompt_data["positive_without_artist_section"])

    def test_prompt_studio_advanced_v2_artist_mix_tuning_values_are_stored(self):
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
        ]
        result = EasyUseAnimaPromptStudioAdvancedV2().build(
            False,
            True,
            False,
            False,
            json.dumps(fields),
            artist_mix_mode=ARTIST_MIX_MODE_HYBRID,
            artist_mix_style_gain=1.5,
            artist_mix_rms_scale_cap=2.5,
            artist_mix_exact_top_k=3,
            artist_mix_cluster_count=5,
            artist_mix_dominant_isolation=False,
            artist_mix_dominant_threshold=0.2,
        )

        prompt_data = result["result"][0]
        self.assertTrue(prompt_data["artist_mix"]["enabled"])
        self.assertEqual(prompt_data["artist_mix"]["mode"], ARTIST_MIX_MODE_HYBRID)
        self.assertEqual(prompt_data["artist_mix"]["style_gain"], 1.5)
        self.assertEqual(prompt_data["artist_mix"]["rms_scale_cap"], 2.5)
        self.assertEqual(prompt_data["artist_mix"]["exact_top_k"], 3)
        self.assertEqual(prompt_data["artist_mix"]["cluster_count"], 5)
        self.assertFalse(prompt_data["artist_mix"]["dominant_isolation"])
        self.assertEqual(prompt_data["artist_mix"]["dominant_threshold"], 0.2)
        ui_payload = result["ui"]["prompt_studio_advanced"][0]
        self.assertEqual(ui_payload["artist_mix_exact_top_k"], 3)
        self.assertEqual(ui_payload["artist_mix_cluster_count"], 5)

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

        def fake_post(host, port, body, **kwargs):
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

        def fake_post(host, port, body, **kwargs):
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

        def fake_post(_host, _port, _body, **kwargs):
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

        def fake_post(_host, _port, _body, **kwargs):
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

        def fake_post(_host, _port, _body, **kwargs):
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

    def test_prompt_studio_advanced_resolution_buckets_cover_two_by_three(self):
        expected = {
            "512": (448, 672),
            "768": (640, 960),
            "896": (704, 1056),
            "1024": (832, 1248),
            "1280": (1024, 1536),
            "1536": (1280, 1920),
        }
        for bucket, portrait in expected.items():
            with self.subTest(bucket=bucket):
                values = set(ADVANCED_RESOLUTION_BUCKETS[bucket])
                self.assertIn(portrait, values)
                self.assertIn((portrait[1], portrait[0]), values)
                self.assertEqual(portrait[0] * 3, portrait[1] * 2)

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
    def test_save_setting_round_trips_false_zero_empty_string_and_null(self):
        with tempfile.TemporaryDirectory() as tmp:
            settings_file = Path(tmp) / "settings.json"
            long_text_settings_file = Path(tmp) / "long_text_settings.json"
            cases = (
                ("autocomplete.append_separator", False, "false"),
                ("autocomplete.limit", 0, "0"),
                ("prompt_studio.font_family", "", ""),
                ("prompt_studio.font_family", None, ""),
            )

            with (
                patch.object(easyuse_settings, "SETTINGS_FILE", settings_file),
                patch.object(
                    easyuse_settings,
                    "LONG_TEXT_SETTINGS_FILE",
                    long_text_settings_file,
                ),
                patch.object(easyuse_settings, "_load_comfy_settings", return_value={}),
            ):
                for key, value, expected in cases:
                    with self.subTest(key=key, value=value):
                        saved = easyuse_settings.save_setting(key, value)
                        persisted = json.loads(settings_file.read_text(encoding="utf-8"))
                        reloaded = easyuse_settings.get_settings()

                        self.assertEqual(saved[key], expected)
                        self.assertEqual(persisted[key], expected)
                        self.assertEqual(reloaded[key], expected)

    def test_parallel_save_setting_updates_do_not_lose_different_keys(self):
        root = Path(__file__).resolve().parents[1] / "__pycache__" / "parallel_settings_test"
        shutil.rmtree(root, ignore_errors=True)
        root.mkdir(parents=True, exist_ok=True)
        settings_file = root / "settings.json"
        long_text_settings_file = root / "long_text_settings.json"
        first_read = threading.Event()
        release_first = threading.Event()
        second_started = threading.Event()
        second_done = threading.Event()
        errors: list[BaseException] = []
        original_read = easyuse_settings._read_json_file

        def coordinated_read(path: Path) -> dict:
            data = original_read(path)
            if Path(path) == settings_file and threading.current_thread().name == "first-setting":
                first_read.set()
                if not release_first.wait(2):
                    raise AssertionError("first settings read was not released")
            return data

        def save_first():
            try:
                easyuse_settings.save_setting("autocomplete.limit", 33)
            except BaseException as exc:
                errors.append(exc)

        def save_second():
            second_started.set()
            try:
                easyuse_settings.save_setting("prompt_studio.font_family", "Inter")
            except BaseException as exc:
                errors.append(exc)
            finally:
                second_done.set()

        try:
            with (
                patch.object(easyuse_settings, "SETTINGS_FILE", settings_file),
                patch.object(easyuse_settings, "LONG_TEXT_SETTINGS_FILE", long_text_settings_file),
                patch.object(easyuse_settings, "_load_comfy_settings", return_value={}),
                patch.object(easyuse_settings, "_read_json_file", side_effect=coordinated_read),
            ):
                first = threading.Thread(target=save_first, name="first-setting")
                second = threading.Thread(target=save_second, name="second-setting")
                first.start()
                self.assertTrue(first_read.wait(2))
                second.start()
                self.assertTrue(second_started.wait(2))
                self.assertFalse(second_done.wait(0.05))
                release_first.set()
                first.join(2)
                second.join(2)

            self.assertFalse(first.is_alive())
            self.assertFalse(second.is_alive())
            self.assertEqual(errors, [])
            persisted = json.loads(settings_file.read_text(encoding="utf-8"))
            self.assertEqual(persisted["autocomplete.limit"], "33")
            self.assertEqual(persisted["prompt_studio.font_family"], "Inter")
        finally:
            release_first.set()
            shutil.rmtree(root, ignore_errors=True)

    def test_parallel_long_text_updates_do_not_lose_different_keys(self):
        root = Path(__file__).resolve().parents[1] / "__pycache__" / "parallel_long_text_test"
        shutil.rmtree(root, ignore_errors=True)
        root.mkdir(parents=True, exist_ok=True)
        long_text_settings_file = root / "long_text_settings.json"
        first_read = threading.Event()
        release_first = threading.Event()
        second_started = threading.Event()
        second_done = threading.Event()
        errors: list[BaseException] = []
        store_class = easyuse_settings.AtomicJsonStore
        original_read = store_class._read_unlocked

        def coordinated_read(store, *args, **kwargs):
            data = original_read(store, *args, **kwargs)
            if (
                store.path == long_text_settings_file.resolve()
                and threading.current_thread().name == "first-long-text"
            ):
                first_read.set()
                if not release_first.wait(2):
                    raise AssertionError("first long-text read was not released")
            return data

        def save_first():
            try:
                easyuse_settings.save_long_text_settings(
                    {"prompt.metadata_filter_words": "metadata"}
                )
            except BaseException as exc:
                errors.append(exc)

        def save_second():
            second_started.set()
            try:
                easyuse_settings.save_long_text_settings({"naia.pre_prompt": "prefix"})
            except BaseException as exc:
                errors.append(exc)
            finally:
                second_done.set()

        try:
            with (
                patch.object(
                    easyuse_settings,
                    "LONG_TEXT_SETTINGS_FILE",
                    long_text_settings_file,
                ),
                patch.object(
                    store_class,
                    "_read_unlocked",
                    autospec=True,
                    side_effect=coordinated_read,
                ),
            ):
                first = threading.Thread(target=save_first, name="first-long-text")
                second = threading.Thread(target=save_second, name="second-long-text")
                first.start()
                self.assertTrue(first_read.wait(2))
                second.start()
                self.assertTrue(second_started.wait(2))
                self.assertFalse(second_done.wait(0.05))
                release_first.set()
                first.join(2)
                second.join(2)

            self.assertFalse(first.is_alive())
            self.assertFalse(second.is_alive())
            self.assertEqual(errors, [])
            persisted = json.loads(long_text_settings_file.read_text(encoding="utf-8"))
            self.assertEqual(persisted["values"]["prompt.metadata_filter_words"], "metadata")
            self.assertEqual(persisted["values"]["naia.pre_prompt"], "prefix")
        finally:
            release_first.set()
            shutil.rmtree(root, ignore_errors=True)

    def test_save_setting_preserves_unknown_key_rejection_contract(self):
        with self.assertRaisesRegex(KeyError, "Unknown setting"):
            easyuse_settings.save_setting("future.unknown", "value")

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
                "autocomplete.preview_completion",
                "autocomplete.preview_closing_brackets",
                "lora_preset.name_display",
                "lora_preset.menu_mode",
                "lora_preset.strength_button_step",
                "lora_preset.strength_drag_step",
                "lora_preset.strength_drag_pixels",
                "prompt_studio.typo_indicator",
                "prompt_studio.weight_syntax_underline",
                "prompt_studio.comment_italic",
                "prompt_studio.font_override",
                "prompt_studio.font_family",
                "prompt_studio.font_size",
                "prompt_studio.colors",
                "prompt_studio.trained_tag_tooltip",
                "prompt_studio.naia_general_above_auto_toggle",
                "prompt_translation.provider",
                "prompt_translation.source",
                "prompt_translation.target",
                "wildcard.extra_paths",
                "naia.host",
                "naia.port",
                "naia.allow_remote_api",
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

    def test_prompt_studio_font_size_is_clamped(self):
        self.assertEqual(resolve_prompt_studio_font_size({"prompt_studio.font_size": "4"}), 8)
        self.assertEqual(resolve_prompt_studio_font_size({"prompt_studio.font_size": "16"}), 16)
        self.assertEqual(resolve_prompt_studio_font_size({"prompt_studio.font_size": "99"}), 24)
        self.assertEqual(resolve_prompt_studio_font_size({"prompt_studio.font_size": "bad"}), 12)

    def test_prompt_studio_font_family_strips_css_control_chars(self):
        self.assertEqual(
            resolve_prompt_studio_font_family({"prompt_studio.font_family": 'Arial; color:red\n'}),
            "Arial color:red",
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
                    "EasyUseAnima.Prompt.FontOverride": "true",
                    "EasyUseAnima.Prompt.FontFamily": "Arial",
                    "EasyUseAnima.Prompt.FontSize": "16",
                    "EasyUseAnima.Prompt.TrainedTagTooltip": "false",
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
        self.assertEqual(settings["prompt_studio.font_override"], "true")
        self.assertEqual(settings["prompt_studio.font_family"], "Arial")
        self.assertEqual(settings["prompt_studio.font_size"], 16)
        self.assertEqual(settings["prompt_studio.trained_tag_tooltip"], "false")
        self.assertEqual(settings["lora_preset.name_display"], "path")
        self.assertEqual(settings["lora_preset.menu_mode"], "list")
        self.assertEqual(settings["lora_preset.strength_button_step"], 0.025)
        self.assertEqual(settings["lora_preset.strength_drag_step"], 0.012)
        self.assertEqual(settings["lora_preset.strength_drag_pixels"], 12)
        self.assertEqual(settings["prompt_translation.provider"], PROMPT_TRANSLATION_PROVIDER_OFF)
        self.assertEqual(settings["naia.port"], 8123)
        self.assertEqual(settings["naia.allow_remote_api"], "false")
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

    def test_prompt_studio_highlight_colors_prefer_aggregate_comfy_setting(self):
        with (
            patch.object(easyuse_settings, "_read_json_file", return_value={}),
            patch.object(
                easyuse_settings,
                "_load_comfy_settings",
                return_value={
                    "EasyUseAnima.Prompt.HighlightColors": '{"quality":"#111111"}',
                    "EasyUseAnima.Prompt.HighlightColor.quality": "#222222",
                },
            ),
        ):
            settings = easyuse_settings.public_settings()

        colors = json.loads(settings["prompt_studio.colors"])
        self.assertEqual(colors["quality"], "#111111")

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

    def test_detailer_align_hook_delegates_before_applying_alignment(self):
        class BaseHook:
            marker = "wrapped"

            def __init__(self):
                self.calls = []

            def touch_scaled_size(self, width, height):
                self.calls.append(("touch_scaled_size", width, height))
                return width + 1, height + 2

            def post_upscale(self, image, noise_mask):
                return "post_upscale", image, noise_mask

            def get_skip_sampling(self):
                return True

            def post_encode(self, latent):
                return "post_encode", latent

            def get_custom_sampler(self):
                return "custom_sampler"

            def set_steps(self, steps):
                return "set_steps", steps

            def cycle_latent(self, latent):
                return "cycle_latent", latent

            def pre_ksample(self, *args):
                return "pre_ksample", *args

            def get_custom_noise(self, seed, noise, is_touched):
                return "custom_noise", seed, noise, is_touched

            def pre_decode(self, latent):
                return "pre_decode", latent

            def post_decode(self, image):
                return "post_decode", image

            def post_paste(self, image):
                return "post_paste", image

        base_hook = BaseHook()
        hook, = EasyUseAnimaDetailerAlignHook().build("32", base_hook)
        pre_ksample_args = (
            "model", 7, 20, 6.5, "sampler", "scheduler",
            "positive", "negative", "latent", 0.5,
        )

        self.assertEqual(hook.marker, "wrapped")
        self.assertEqual(hook.touch_scaled_size(64, 95), (96, 128))
        self.assertEqual(base_hook.calls, [("touch_scaled_size", 64, 95)])
        self.assertEqual(hook.post_upscale("image", "mask"), ("post_upscale", "image", "mask"))
        self.assertTrue(hook.get_skip_sampling())
        self.assertEqual(hook.post_encode("latent"), ("post_encode", "latent"))
        self.assertEqual(hook.get_custom_sampler(), "custom_sampler")
        self.assertEqual(hook.set_steps(20), ("set_steps", 20))
        self.assertEqual(hook.cycle_latent("latent"), ("cycle_latent", "latent"))
        self.assertEqual(hook.pre_ksample(*pre_ksample_args), ("pre_ksample", *pre_ksample_args))
        self.assertEqual(
            hook.get_custom_noise(7, "noise", True),
            ("custom_noise", 7, "noise", True),
        )
        self.assertEqual(hook.pre_decode("latent"), ("pre_decode", "latent"))
        self.assertEqual(hook.post_decode("image"), ("post_decode", "image"))
        self.assertEqual(hook.post_paste("image"), ("post_paste", "image"))

    def test_detailer_align_hook_preserves_no_base_fallbacks(self):
        hook, = EasyUseAnimaDetailerAlignHook().build("none")
        pre_ksample_args = (
            "model", 7, 20, 6.5, "sampler", "scheduler",
            "positive", "negative", "latent", 0.5,
        )

        self.assertEqual(hook.touch_scaled_size(65, 95), (65, 95))
        self.assertEqual(hook.post_upscale("image", "mask"), "image")
        self.assertFalse(hook.get_skip_sampling())
        self.assertEqual(hook.post_encode("latent"), "latent")
        self.assertIsNone(hook.get_custom_sampler())
        self.assertIsNone(hook.set_steps(20))
        self.assertEqual(hook.cycle_latent("latent"), "latent")
        self.assertEqual(hook.pre_ksample(*pre_ksample_args), pre_ksample_args)
        self.assertEqual(hook.get_custom_noise(7, "noise", True), ("noise", True))
        self.assertEqual(hook.pre_decode("latent"), "latent")
        self.assertEqual(hook.post_decode("image"), "image")
        self.assertEqual(hook.post_paste("image"), "image")
        with self.assertRaises(AttributeError):
            _ = hook.missing_attribute


class AutocompleteDatasetTests(unittest.TestCase):
    def test_search_autocomplete_ranks_exact_before_prefix_substring_and_description(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "tags.csv"
            path.write_text(
                "\n".join(
                    [
                        'target prefix popular,0,1000,"[일반] prefix"',
                        'popular target middle,0,900,"[일반] substring"',
                        'description only,0,800,"[일반] target description"',
                        'target,0,1,"[일반] exact"',
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            result = search_autocomplete("target", limit=4, path=path)

        self.assertEqual(
            [item["tag"] for item in result["results"]],
            [
                "target",
                "target prefix popular",
                "popular target middle",
                "description only",
            ],
        )
        self.assertEqual(result["results"][0]["count"], 1)

    def test_search_autocomplete_normalizes_limit_and_matches_exhaustive_reference(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "tags.csv"
            path.write_text(
                "\n".join(
                    f'limit match {index:03d},0,{1000 - index},"[일반] 제한 테스트"'
                    for index in range(120)
                )
                + "\n",
                encoding="utf-8",
            )

            for requested_limit in (1, 50, 51, 100):
                with self.subTest(requested_limit=requested_limit):
                    result = search_autocomplete("limit match", limit=requested_limit, path=path)
                    self.assertEqual(len(result["results"]), requested_limit)

            self.assertEqual(len(search_autocomplete("limit match", limit=0, path=path)["results"]), 1)
            self.assertEqual(len(search_autocomplete("limit match", limit=-1, path=path)["results"]), 1)
            self.assertEqual(len(search_autocomplete("limit match", limit=10_000, path=path)["results"]), 100)

            path.write_text(
                "\n".join(
                    itertools.chain(
                        ('needle,0,1,"[일반] low count exact"',),
                        (
                            f'needle prefix {index:03d},{index % 2},{2000 - index},"[일반] prefix"'
                            for index in range(130)
                        ),
                        (
                            f'popular needle middle {index:03d},{index % 2},{1800 - index},"[일반] substring"'
                            for index in range(130)
                        ),
                        (
                            f'description only {index:03d},{index % 2},{1600 - index},"[일반] needle description"'
                            for index in range(130)
                        ),
                    )
                )
                + "\n",
                encoding="utf-8",
            )
            next_mtime = path.stat().st_mtime_ns + 1_000_000_000
            os.utime(path, ns=(next_mtime, next_mtime))

            entries = autocomplete_dataset._entries(path)

            def exhaustive(query, requested_limit, category=""):
                normalized_query = autocomplete_dataset._normalize(query)
                categories = {item.strip() for item in category.split(",") if item.strip()}
                ranked = []
                for entry in entries:
                    if categories and entry.category not in categories:
                        continue
                    if entry.tag_key == normalized_query:
                        score = 0
                    elif entry.tag_key.startswith(normalized_query):
                        score = 1
                    elif normalized_query in entry.tag_key:
                        score = 2
                    elif normalized_query in entry.search:
                        score = 3
                    else:
                        continue
                    ranked.append((score, entry))
                ranked.sort(key=lambda item: (item[0], -item[1].count, item[1].tag))
                limit = max(1, min(requested_limit, 100))
                return [
                    {
                        "tag": entry.tag,
                        "category": entry.category,
                        "count": entry.count,
                        "description": entry.description,
                    }
                    for _, entry in ranked[:limit]
                ]

            for requested_limit, category in ((1, ""), (7, "artist"), (100, "artist,general")):
                with self.subTest(requested_limit=requested_limit, category=category):
                    optimized = search_autocomplete(
                        "needle",
                        limit=requested_limit,
                        path=path,
                        category=category,
                    )["results"]
                    self.assertEqual(
                        optimized,
                        exhaustive("needle", requested_limit, category),
                    )

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
            korean_spaced = search_autocomplete("하츠네 미쿠", path=path)
            status = autocomplete_status(path)

        self.assertEqual(korean["results"][0]["tag"], "hatsune miku")
        self.assertEqual(korean_spaced["results"][0]["tag"], "hatsune miku")
        self.assertEqual(korean["results"][0]["category"], "character")
        self.assertEqual(status["count"], 2)

    def test_autocomplete_status_uses_builtin_manifest_without_loading_dataset(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "built-in.csv"
            path.write_text(
                'first tag,0,100,"[일반] first"\nsecond tag,0,90,"[일반] second"\n',
                encoding="utf-8",
            )
            expected_mtime = path.stat().st_mtime_ns / 1_000_000_000
            sources = {
                "fixture": {
                    "label": "Fixture",
                    "path": path,
                    "entry_count": 2,
                }
            }

            with (
                patch.object(autocomplete_dataset, "AUTOCOMPLETE_SOURCES", sources),
                patch.object(
                    autocomplete_dataset,
                    "_snapshot",
                    side_effect=AssertionError("status must not load a snapshot"),
                ) as snapshot,
                patch.object(
                    autocomplete_dataset,
                    "_load_entries",
                    side_effect=AssertionError("status must not load entries"),
                ) as load_entries,
            ):
                status = autocomplete_status(path)

        self.assertEqual(set(status), {"path", "exists", "count", "mtime"})
        self.assertEqual(status["path"], str(path))
        self.assertTrue(status["exists"])
        self.assertEqual(status["count"], 2)
        self.assertEqual(status["mtime"], expected_mtime)
        snapshot.assert_not_called()
        load_entries.assert_not_called()

    def test_autocomplete_status_builtin_missing_and_non_file_preserve_policy(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            targets = (root / "missing.csv", root)
            for target in targets:
                with self.subTest(target=target):
                    sources = {
                        "fixture": {
                            "label": "Fixture",
                            "path": target,
                            "entry_count": 99,
                        }
                    }
                    with (
                        patch.object(
                            autocomplete_dataset,
                            "AUTOCOMPLETE_SOURCES",
                            sources,
                        ),
                        patch.object(
                            autocomplete_dataset,
                            "_snapshot",
                            side_effect=AssertionError("missing status must stay metadata-only"),
                        ) as snapshot,
                        patch.object(
                            autocomplete_dataset,
                            "_load_entries",
                            side_effect=AssertionError("missing status must not load entries"),
                        ) as load_entries,
                    ):
                        status = autocomplete_status(target)

                    self.assertEqual(
                        status,
                        {
                            "path": str(target),
                            "exists": False,
                            "count": 0,
                            "mtime": 0,
                        },
                    )
                    snapshot.assert_not_called()
                    load_entries.assert_not_called()

    def test_autocomplete_status_custom_path_preserves_exact_snapshot_fallback(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "custom.csv"
            path.write_text('first tag,0,100,"[일반] first"\n', encoding="utf-8")
            original_load = autocomplete_dataset._load_entries

            with (
                patch.object(autocomplete_dataset, "AUTOCOMPLETE_SOURCES", {}),
                patch.object(
                    autocomplete_dataset,
                    "_load_entries",
                    wraps=original_load,
                ) as load_entries,
            ):
                first = autocomplete_status(path)
                first_stat = path.stat()
                path.write_text(
                    'second tag,0,100,"[일반] second"\n'
                    'third longer tag,0,90,"[일반] third"\n',
                    encoding="utf-8",
                )
                next_mtime = first_stat.st_mtime_ns + 1_000_000_000
                os.utime(path, ns=(next_mtime, next_mtime))
                second = autocomplete_status(path)

        self.assertEqual(first["count"], 1)
        self.assertEqual(second["count"], 2)
        self.assertEqual(load_entries.call_count, 2)

    def test_search_classify_and_status_report_the_same_snapshot_status(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "built-in.csv"
            path.write_text(
                'shared tag,0,100,"[일반] shared"\n'
                'other tag,0,90,"[일반] other"\n',
                encoding="utf-8",
            )
            sources = {
                "fixture": {
                    "label": "Fixture",
                    "path": path,
                    "entry_count": 2,
                }
            }

            with patch.object(
                autocomplete_dataset,
                "AUTOCOMPLETE_SOURCES",
                sources,
            ):
                searched = search_autocomplete("shared", path=path)
                classified = classify_prompt_text("shared tag", path=path)
                status = autocomplete_status(path)

        self.assertEqual(searched["status"], classified["status"])
        self.assertEqual(searched["status"], status)
        self.assertEqual(status["count"], 2)

    def test_autocomplete_snapshot_records_use_slots(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "slots.csv"
            path.write_text('slotted tag,0,100,"[일반] slotted"\n', encoding="utf-8")
            snapshot = autocomplete_dataset._snapshot(path)

        self.assertFalse(hasattr(snapshot, "__dict__"))
        self.assertFalse(hasattr(snapshot.key, "__dict__"))
        self.assertFalse(hasattr(snapshot.entries[0], "__dict__"))

    def test_searches_escaped_literal_parentheses(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "tags.csv"
            path.write_text(
                'asuna (blue archive),4,100,"[캐릭터] asuna blue archive"\n',
                encoding="utf-8",
            )

            result = search_autocomplete(r"\(blue archive\)", path=path)

        self.assertEqual(result["results"][0]["tag"], "asuna (blue archive)")

    def test_autocomplete_cache_key_and_mtime_or_size_invalidation(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "tags.csv"
            path.write_text('alpha tag,0,100,"[일반] 첫 태그"\n', encoding="utf-8")

            first = search_autocomplete("alpha", path=path)
            first_stat = path.stat()
            first_key = autocomplete_dataset._cache_key(path.parent / "." / path.name)

            path.write_text('beta longer tag,0,100,"[일반] 두 번째 태그"\n', encoding="utf-8")
            os.utime(path, ns=(first_stat.st_atime_ns, first_stat.st_mtime_ns))
            second = search_autocomplete("beta", path=path)
            second_stat = path.stat()
            second_key = autocomplete_dataset._cache_key(path)

            path.write_text('zeta longer tag,0,100,"[일반] 세 번째 태그"\n', encoding="utf-8")
            next_mtime = second_stat.st_mtime_ns + 1_000_000_000
            os.utime(path, ns=(next_mtime, next_mtime))
            third = search_autocomplete("zeta", path=path)

            with patch.object(
                autocomplete_dataset,
                "_AUTOCOMPLETE_CACHE_SCHEMA_VERSION",
                first_key.schema_version + 1,
            ):
                schema_key = autocomplete_dataset._cache_key(path)

        self.assertEqual(first["results"][0]["tag"], "alpha tag")
        self.assertEqual(second["results"][0]["tag"], "beta longer tag")
        self.assertEqual(third["results"][0]["tag"], "zeta longer tag")
        self.assertEqual(first_key.resolved_path, str(path.resolve(strict=False)))
        self.assertEqual(first_key.mtime_ns, second_key.mtime_ns)
        self.assertNotEqual(first_key.size, second_key.size)
        self.assertEqual(schema_key.schema_version, first_key.schema_version + 1)

    def test_autocomplete_cache_coalesces_concurrent_same_key_loads(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "tags.csv"
            path.write_text('shared tag,0,100,"[일반] shared"\n', encoding="utf-8")
            start = threading.Barrier(3)
            load_started = threading.Event()
            waiter_joined = threading.Event()
            release_load = threading.Event()
            original_load = autocomplete_dataset._load_entries
            original_await = autocomplete_dataset._await_snapshot

            def blocking_load(load_path):
                load_started.set()
                if not release_load.wait(timeout=5):
                    raise AssertionError("timed out waiting to release dataset load")
                return original_load(load_path)

            def observed_await(future):
                waiter_joined.set()
                return original_await(future)

            def fetch_entries():
                start.wait(timeout=5)
                return autocomplete_dataset._entries(path)

            with (
                patch.object(
                    autocomplete_dataset,
                    "_load_entries",
                    side_effect=blocking_load,
                ) as load_entries,
                patch.object(
                    autocomplete_dataset,
                    "_await_snapshot",
                    side_effect=observed_await,
                ),
                ThreadPoolExecutor(max_workers=2) as executor,
            ):
                futures = [executor.submit(fetch_entries) for _ in range(2)]
                start.wait(timeout=5)
                self.assertTrue(load_started.wait(timeout=5))
                try:
                    self.assertTrue(waiter_joined.wait(timeout=5))
                finally:
                    release_load.set()
                loaded = [future.result(timeout=5) for future in futures]

        self.assertEqual(load_entries.call_count, 1)
        self.assertIs(loaded[0], loaded[1])
        self.assertEqual(loaded[0][0].tag, "shared tag")

    def test_autocomplete_cache_loads_different_sources_in_parallel_without_pollution(self):
        with tempfile.TemporaryDirectory() as tmp:
            first_path = Path(tmp) / "first.csv"
            second_path = Path(tmp) / "second.csv"
            first_path.write_text('first tag,0,100,"[일반] first"\n', encoding="utf-8")
            second_path.write_text('second tag,0,90,"[일반] second"\n', encoding="utf-8")
            loads_meet = threading.Barrier(2)
            original_load = autocomplete_dataset._load_entries

            def parallel_load(load_path):
                loads_meet.wait(timeout=5)
                return original_load(load_path)

            with (
                patch.object(
                    autocomplete_dataset,
                    "_load_entries",
                    side_effect=parallel_load,
                ) as load_entries,
                ThreadPoolExecutor(max_workers=2) as executor,
            ):
                first_future = executor.submit(autocomplete_dataset._snapshot, first_path)
                second_future = executor.submit(autocomplete_dataset._snapshot, second_path)
                first_snapshot = first_future.result(timeout=5)
                second_snapshot = second_future.result(timeout=5)

        self.assertEqual(load_entries.call_count, 2)
        self.assertEqual([entry.tag for entry in first_snapshot.entries], ["first tag"])
        self.assertEqual([entry.tag for entry in second_snapshot.entries], ["second tag"])
        self.assertEqual(set(first_snapshot.entry_map), {"first tag"})
        self.assertEqual(set(second_snapshot.entry_map), {"second tag"})
        self.assertIsInstance(first_snapshot.entries, tuple)
        with self.assertRaises(TypeError):
            first_snapshot.entry_map["mutated"] = first_snapshot.entries[0]

    def test_autocomplete_cache_retries_replacement_and_treats_deletion_as_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            replacement_path = Path(tmp) / "replacement.csv"
            replacement_path.write_text('old tag,0,100,"[일반] old"\n', encoding="utf-8")
            replacement_started = threading.Event()
            replacement_done = threading.Event()
            original_load = autocomplete_dataset._load_entries
            load_count = 0
            load_count_lock = threading.Lock()

            def replacement_load(load_path):
                nonlocal load_count
                with load_count_lock:
                    load_count += 1
                    current_load = load_count
                if current_load == 1:
                    replacement_started.set()
                    if not replacement_done.wait(timeout=5):
                        raise AssertionError("timed out waiting for dataset replacement")
                return original_load(load_path)

            with (
                patch.object(
                    autocomplete_dataset,
                    "_load_entries",
                    side_effect=replacement_load,
                ),
                ThreadPoolExecutor(max_workers=1) as executor,
            ):
                replacement_future = executor.submit(
                    search_autocomplete,
                    "new replacement",
                    20,
                    replacement_path,
                )
                self.assertTrue(replacement_started.wait(timeout=5))
                replacement_path.write_text(
                    'new replacement tag,0,80,"[일반] replacement with a different size"\n',
                    encoding="utf-8",
                )
                replacement_done.set()
                replacement = replacement_future.result(timeout=5)

            deletion_path = Path(tmp) / "deletion.csv"
            deletion_path.write_text('deleted tag,0,100,"[일반] delete"\n', encoding="utf-8")
            deletion_started = threading.Event()
            deletion_done = threading.Event()
            deletion_load_count = 0

            def deletion_load(load_path):
                nonlocal deletion_load_count
                deletion_load_count += 1
                if deletion_load_count == 1:
                    deletion_started.set()
                    if not deletion_done.wait(timeout=5):
                        raise AssertionError("timed out waiting for dataset deletion")
                    raise FileNotFoundError(load_path)
                return original_load(load_path)

            with (
                patch.object(
                    autocomplete_dataset,
                    "_load_entries",
                    side_effect=deletion_load,
                ),
                ThreadPoolExecutor(max_workers=1) as executor,
            ):
                deletion_future = executor.submit(
                    search_autocomplete,
                    "deleted",
                    20,
                    deletion_path,
                )
                self.assertTrue(deletion_started.wait(timeout=5))
                deletion_path.unlink()
                deletion_done.set()
                deletion = deletion_future.result(timeout=5)

        self.assertEqual(load_count, 2)
        self.assertEqual(replacement["results"][0]["tag"], "new replacement tag")
        self.assertTrue(replacement["status"]["exists"])
        self.assertEqual(deletion_load_count, 1)
        self.assertEqual(deletion["results"], [])
        self.assertFalse(deletion["status"]["exists"])
        self.assertEqual(deletion["status"]["count"], 0)

    def test_autocomplete_cache_has_a_bounded_repeated_change_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "unstable.csv"
            path.write_text('unstable tag,0,100,"[일반] unstable"\n', encoding="utf-8")
            with patch.object(
                autocomplete_dataset,
                "_snapshot_for_key",
                side_effect=autocomplete_dataset._AutocompleteSourceChanged(str(path)),
            ) as snapshot_for_key:
                with self.assertRaisesRegex(
                    RuntimeError,
                    "Autocomplete dataset changed repeatedly while loading",
                ):
                    autocomplete_dataset._snapshot(path)

        self.assertEqual(
            snapshot_for_key.call_count,
            autocomplete_dataset._AUTOCOMPLETE_CACHE_LOAD_ATTEMPTS,
        )

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

        self.assertEqual(
            [source["key"] for source in sources],
            [
                "dbr_danbooru_2025_09_01",
                "dbr_e621_2025_09_01",
                "dbr_danbooru_e621_merged_2025_09_01",
                "localsmile_kr_wiki",
            ],
        )
        self.assertTrue(
            any(
                source["key"] == "localsmile_kr_wiki" and source["selected"]
                for source in sources
            )
        )
        self.assertEqual(sources[0]["license"], "Unlicense")

    def test_default_autocomplete_source_uses_dbr_danbooru_csv(self):
        key, path = resolve_autocomplete_source("")

        self.assertEqual(key, "dbr_danbooru_2025_09_01")
        self.assertEqual(path.name, "danbooru_2025-09-01.csv")

    def test_e621_categories_map_to_supported_highlight_sections(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "e621_2025-09-01.csv"
            path.write_text(
                "\n".join(
                    [
                        'mammal,5,100,"mammals"',
                        'artist wolf,1,80,"artist alias"',
                        'e621 meta marker,7,70,"meta alias"',
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            classified = classify_prompt_text("mammal, @artist_wolf, e621 meta marker", path=path)

        self.assertEqual(
            [token["section"] for token in classified["tokens"]],
            ["general", "artist", "meta"],
        )

    def test_merged_e621_offset_categories_map_to_supported_sections(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "danbooru_e621_merged_2025-09-01.csv"
            path.write_text(
                "\n".join(
                    [
                        'danbooru artist,1,100,"danbooru artist"',
                        'e621 artist,8,80,"e621 artist"',
                        'e621 character,11,70,"e621 character"',
                        'e621 mammal,12,60,"e621 species"',
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            artists = search_autocomplete("artist", path=path, category="artist")
            classified = classify_prompt_text("e621 character, e621 mammal", path=path)

        self.assertEqual(
            {item["tag"] for item in artists["results"]},
            {"danbooru artist", "e621 artist"},
        )
        self.assertEqual(
            [token["section"] for token in classified["tokens"]],
            ["character", "general"],
        )

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
                "artist",
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

    def test_wildcard_syntax_is_classified_for_highlighting(self):
        classified = classify_prompt_text("__하츠__, 3#__style__, {red|blue}, {1-3$$, $$red|blue}")

        self.assertEqual(
            [(token["base"], token["section"]) for token in classified["tokens"]],
            [
                ("__하츠__", "wildcard"),
                ("3#__style__", "wildcard"),
                ("{red|blue}", "wildcard"),
                ("{1-3$$, $$red|blue}", "wildcard"),
            ],
        )

    def test_translation_marker_syntax_is_classified_for_highlighting(self):
        classified = classify_prompt_text("1girl, %{빨간 머리의 소녀}, blue eyes")

        self.assertEqual(
            [(token["base"], token["section"]) for token in classified["tokens"]],
            [
                ("1girl", "count"),
                ("%{빨간 머리의 소녀}", "translation"),
                ("blue eyes", "general"),
            ],
        )

    def test_translation_marker_is_not_expanded_as_dynamic_prompt(self):
        expanded = expand_wildcards("1girl, %{red hair|blue hair}, {smile|serious}", seed=0)

        self.assertIn("%{red hair|blue hair}", expanded.text)
        self.assertNotIn("{smile|serious}", expanded.text)

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

    def test_plain_parenthesized_artist_tag_is_classified(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "tags.csv"
            path.write_text(
                'ningen mame,1,10,"[작가] ningen mame"\n',
                encoding="utf-8",
            )
            classified = classify_prompt_text("(@ningen mame)", path=path)

        self.assertEqual(
            [(token["base"], token["section"], token["weighted"]) for token in classified["tokens"]],
            [("ningen mame", "artist", False)],
        )

    def test_plain_parenthesized_group_classifies_all_inner_tag_types(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "tags.csv"
            path.write_text(
                'hatsune miku,4,90,"[캐릭터] hatsune miku"\n'
                'long hair,0,80,"[일반] long hair"\n'
                'ningen mame,1,70,"[작가] ningen mame"\n',
                encoding="utf-8",
            )
            classified = classify_prompt_text(
                "(highres, hatsune miku, long hair, @ningen mame)",
                path=path,
            )

        self.assertEqual(
            [(token["base"], token["section"], token["weighted"]) for token in classified["tokens"]],
            [
                ("highres", "meta", False),
                ("hatsune miku", "character", False),
                ("long hair", "general", False),
                ("ningen mame", "artist", False),
            ],
        )

    def test_artist_mix_group_classifies_inner_artist_tokens(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "tags.csv"
            path.write_text(
                'sushispin,1,10,"[작가] sushispin"\n'
                'ningen mame,1,10,"[작가] ningen mame"\n',
                encoding="utf-8",
            )
            classified = classify_prompt_text("[[(@sushispin:0.35), @ningen mame, ]]", path=path)

        self.assertEqual(
            [(token["base"], token["section"], token["weighted"]) for token in classified["tokens"]],
            [
                ("sushispin", "artist", True),
                ("ningen mame", "artist", False),
            ],
        )

    def test_artist_mix_group_weight_suffix_is_not_a_prompt_weight(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "tags.csv"
            path.write_text(
                'sushispin,1,10,"[작가] sushispin"\n'
                'ningen mame,1,10,"[작가] ningen mame"\n',
                encoding="utf-8",
            )
            classified = classify_prompt_text("[[ @sushispin, @ningen mame:0.7 ]]", path=path)

        self.assertEqual(
            [(token["base"], token["section"], token["weighted"]) for token in classified["tokens"]],
            [
                ("sushispin", "artist", False),
                ("ningen mame", "artist", False),
            ],
        )

    def test_invalid_weight_syntax_is_classified_as_syntax_error(self):
        for prompt in ["(@sushispin:bad)", "[[@sushispin, @ningen mame:bad]]", "[[@sushispin"]:
            with self.subTest(prompt=prompt):
                classified = classify_prompt_text(prompt)
                self.assertEqual(classified["tokens"][0]["section"], "syntax")

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
