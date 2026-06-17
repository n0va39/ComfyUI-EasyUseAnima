from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from nodes import (
    EasyUseAnimaAnimaDexDatasetDownload,
    EasyUseAnimaPromptBuilder,
    EasyUseAnimaPromptCorrector,
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
            "1girl, @artist_name, model_trigger, lora trigger, A Girl with Sword",
        )
        self.assertEqual(quality, "masterpiece, best quality, (high detail:0.6)")
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
        self.assertEqual(quality, "masterpiece, best quality")
        self.assertEqual(
            prompt,
            "@artist_name, lora trigger, masterpiece, best quality, 1girl",
        )
        self.assertEqual(prompt, metadata)


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


if __name__ == "__main__":
    unittest.main()
