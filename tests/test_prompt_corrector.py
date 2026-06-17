from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from nodes import (
    DEFAULT_QUALITY_TAGS,
    DEFAULT_TRAILING_QUALITY_TAGS,
    EasyUseAnimaAnimaDexDatasetDownload,
    EasyUseAnimaPromptBuilder,
    EasyUseAnimaPromptCorrector,
    EasyUseAnimaPromptStudio,
)
from autocomplete_dataset import (
    autocomplete_status,
    available_autocomplete_sources,
    classify_prompt_text,
    search_autocomplete,
)
from animadex_dataset import dataset_status
from settings import public_settings


class PromptCorrectorTests(unittest.TestCase):
    def test_corrects_without_animadex_data(self):
        corrected, report = EasyUseAnimaPromptCorrector().correct(
            "long_hair, 1girl, long_hair",
            True,
            "",
            "",
            "",
            "",
            "",
            "",
        )

        self.assertEqual(corrected, "1girl, long hair")
        data = json.loads(report)
        self.assertEqual(data["duplicate_tags"], ["long hair"])

    def test_preserves_prompt_weight_syntax_and_escapes_literal_parentheses(self):
        corrected, report = EasyUseAnimaPromptCorrector().correct(
            "(long_hair:1.2), character_\\(series\\), 1girl, foo_(bar)",
            True,
            "",
            "",
            "",
            "",
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
            False,
            "",
            "",
            "",
            "",
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

    def test_uses_animadex_indexes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            character_index = root / "character_index.jsonl"
            artist_index = root / "artist_index.jsonl"
            character_index.write_text(
                json.dumps(
                    {
                        "character": "hatsune miku",
                        "copyright": "vocaloid",
                        "trigger": "hatsune miku, vocaloid",
                        "trigger_character": "hatsune miku",
                        "trigger_copyright": "vocaloid",
                        "core_tags": ["1girl"],
                        "count": 1,
                        "url": "",
                    },
                    ensure_ascii=False,
                )
                + "\n",
                encoding="utf-8",
            )
            artist_index.write_text(
                json.dumps(
                    {
                        "artist": "artist name",
                        "trigger": "artist name",
                        "count": 1,
                        "url": "",
                    },
                    ensure_ascii=False,
                )
                + "\n",
                encoding="utf-8",
            )

            corrected, report = EasyUseAnimaPromptCorrector().correct(
                "long_hair, vocaloid, @artist_name, hatsune_miku, 1girl",
                True,
                "",
                "",
                "",
                "",
                str(character_index),
                str(artist_index),
            )

        self.assertEqual(
            corrected,
            "1girl, hatsune miku, vocaloid, @artist_name, long hair",
        )
        data = json.loads(report)
        self.assertEqual(
            data["sections"],
            ["count", "character", "copyright", "artist", "unknown"],
        )


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

        self.assertEqual(studio_output, builder_output)


class AnimaDexDatasetDownloadTests(unittest.TestCase):
    def test_dataset_status_reports_downloaded_indexes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            index = root / "index"
            index.mkdir(parents=True)
            character_index = index / "character_index.jsonl"
            artist_index = index / "artist_index.jsonl"
            character_index.write_text("", encoding="utf-8")
            artist_index.write_text("", encoding="utf-8")

            with patch("animadex_dataset.PACKAGE_DATA_DIR", root):
                status = dataset_status()

        self.assertTrue(status["downloaded"])
        self.assertTrue(status["character_index"]["exists"])
        self.assertTrue(status["artist_index"]["exists"])

    def test_public_settings_does_not_expose_token_file(self):
        self.assertNotIn("animadex.token_file", public_settings())
        self.assertIn("prompt.metadata_filter_words", public_settings())
        self.assertIn("autocomplete.source", public_settings())

    def test_cached_dataset_does_not_require_token(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            index = root / "index"
            index.mkdir(parents=True)
            character_index = index / "character_index.jsonl"
            artist_index = index / "artist_index.jsonl"
            character_index.write_text("", encoding="utf-8")
            artist_index.write_text("", encoding="utf-8")

            with patch("nodes.PACKAGE_DATA_DIR", root):
                status, report, char_path, artist_path = (
                    EasyUseAnimaAnimaDexDatasetDownload().download(
                        "",
                        False,
                        False,
                    )
                )

        self.assertEqual(status, "cached")
        self.assertEqual(char_path, str(character_index))
        self.assertEqual(artist_path, str(artist_index))
        self.assertEqual(json.loads(report)["status"], "cached")

    def test_missing_dataset_requires_token(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch("nodes.PACKAGE_DATA_DIR", Path(tmp)):
                with self.assertRaisesRegex(RuntimeError, "export token is required"):
                    EasyUseAnimaAnimaDexDatasetDownload().download(
                        "",
                        False,
                        False,
                    )


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

    def test_lists_autocomplete_sources(self):
        sources = available_autocomplete_sources("localsmile_kr_wiki")

        self.assertTrue(any(source["key"] == "kr_modified" for source in sources))
        self.assertTrue(
            any(
                source["key"] == "localsmile_kr_wiki" and source["selected"]
                for source in sources
            )
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
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            result = classify_prompt_text(
                (
                    "1girl, (hatsune miku:0.7), series name, "
                    "(A highly aesthetic Pixiv style illustration, clean composition.:0.6), "
                    "unknown tag"
                ),
                path=path,
            )

        sections = [token["section"] for token in result["tokens"]]
        self.assertEqual(sections, ["count", "character", "copyright", "natural", "unknown"])
        self.assertTrue(result["tokens"][0]["learned"])
        self.assertTrue(result["tokens"][1]["learned"])
        self.assertEqual(result["tokens"][1]["base"], "hatsune miku")
        self.assertEqual(result["tokens"][3]["base"], "A highly aesthetic Pixiv style illustration, clean composition.")
        self.assertFalse(result["tokens"][4]["learned"])


if __name__ == "__main__":
    unittest.main()
