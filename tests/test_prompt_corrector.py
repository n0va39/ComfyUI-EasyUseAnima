from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from nodes import (
    DEFAULT_QUALITY_TAGS,
    DEFAULT_TRAILING_QUALITY_TAGS,
    EasyUseAnimaPromptBuilder,
    EasyUseAnimaPromptCorrector,
    EasyUseAnimaPromptStudio,
)
from autocomplete_dataset import (
    autocomplete_status,
    available_autocomplete_sources,
    classify_prompt_text,
    resolve_autocomplete_source,
    search_autocomplete,
)
from settings import NAIA_PREPROCESSING_KEYS, public_settings, resolve_autocomplete_limit


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
                "1girl, (@akazawa_kureha:0.35), "
                "An intelligent and neat girl with long silver hair., "
                "(A highly aesthetic Pixiv style illustration, clean composition.:0.6)"
            ),
        )
        data = json.loads(report)
        self.assertEqual(data["sections"][0], "count")

    def test_builtin_meta_quality_tags_are_known_without_external_data(self):
        corrected, report = EasyUseAnimaPromptCorrector().correct(
            "1girl, lowres, year_2024, rating_safe, score_7:, very_aesthetic, source_anime",
            "",
            "",
        )

        self.assertEqual(
            corrected,
            "score 7:, very aesthetic, lowres, source anime, year 2024, rating safe, 1girl",
        )
        data = json.loads(report)
        self.assertEqual(
            data["sections"],
            ["quality", "quality", "meta", "meta", "year", "safety", "count"],
        )
        self.assertEqual(data["unknown_tags"], [])


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


class SettingsTests(unittest.TestCase):
    def test_public_settings_does_not_expose_token_file(self):
        settings = public_settings()
        self.assertEqual(
            set(settings),
            {
                "prompt.metadata_filter_words",
                "autocomplete.source",
                "autocomplete.limit",
                "prompt_studio.typo_indicator",
                "prompt_studio.colors",
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
        self.assertEqual(result["tokens"][6]["base"], "A highly aesthetic Pixiv style illustration, clean composition.")
        self.assertFalse(result["tokens"][7]["learned"])

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
                "rating_safe, score_9, year_2024, source_anime, lowres, very_aesthetic",
                path=path,
            )
            autocomplete = search_autocomplete("score", path=path)

        self.assertEqual(
            [token["section"] for token in classified["tokens"]],
            ["safety", "quality", "year", "meta", "meta", "quality"],
        )
        self.assertEqual([token["learned"] for token in classified["tokens"]], [False] * 6)
        self.assertEqual(autocomplete["results"], [])


if __name__ == "__main__":
    unittest.main()
