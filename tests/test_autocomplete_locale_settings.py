from __future__ import annotations

import json
import shutil
import unittest
from pathlib import Path
from unittest.mock import patch

from easyuse_anima.autocomplete import dataset
from easyuse_anima.settings import repository


ROOT = Path(__file__).resolve().parents[1]
TEST_ROOT = ROOT / "__pycache__" / "rel_feat_01_locale_settings"
DANBOORU_SOURCE = "dbr_danbooru_2025_09_01"
E621_SOURCE = "dbr_e621_2025_09_01"
MERGED_SOURCE = "dbr_danbooru_e621_merged_2025_09_01"
KOREAN_SOURCE = "localsmile_kr_wiki"


class AutocompleteLocaleSettingsTests(unittest.TestCase):
    def setUp(self):
        shutil.rmtree(TEST_ROOT, ignore_errors=True)
        TEST_ROOT.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        shutil.rmtree(TEST_ROOT, ignore_errors=True)

    def _case_paths(self, name: str) -> tuple[Path, Path]:
        root = TEST_ROOT / name
        root.mkdir(parents=True, exist_ok=True)
        return root / "settings.json", root / "long_text_settings.json"

    def _get_settings(
        self,
        name: str,
        comfy_settings: dict,
    ) -> tuple[dict, Path]:
        settings_file, long_text_file = self._case_paths(name)
        with (
            patch.object(repository, "SETTINGS_FILE", settings_file),
            patch.object(
                repository,
                "LONG_TEXT_SETTINGS_FILE",
                long_text_file,
            ),
            patch.object(
                repository,
                "_load_comfy_settings",
                return_value=comfy_settings,
            ),
        ):
            settings = repository.get_settings()
        return settings, settings_file

    def test_missing_source_initializes_from_locale_and_persists(self):
        settings, settings_file = self._get_settings("missing-locale", {})
        self.assertEqual(settings["autocomplete.source"], DANBOORU_SOURCE)
        self.assertEqual(
            json.loads(settings_file.read_text(encoding="utf-8")),
            {
                "version": 1,
                "values": {"autocomplete.source": DANBOORU_SOURCE},
            },
        )

        cases = (
            ("ko", KOREAN_SOURCE),
            ("ko-KR", KOREAN_SOURCE),
            ("Korean", KOREAN_SOURCE),
            ("한국어", KOREAN_SOURCE),
            ("", DANBOORU_SOURCE),
            ("en-US", DANBOORU_SOURCE),
            ("unknown", DANBOORU_SOURCE),
        )
        for index, (locale, expected) in enumerate(cases):
            with self.subTest(locale=locale):
                settings, settings_file = self._get_settings(
                    f"missing-{index}",
                    {"Comfy.Locale": locale},
                )
                persisted = json.loads(settings_file.read_text(encoding="utf-8"))

                self.assertEqual(settings["autocomplete.source"], expected)
                self.assertEqual(
                    persisted,
                    {
                        "version": 1,
                        "values": {"autocomplete.source": expected},
                    },
                )

    def test_explicit_internal_sources_are_preserved(self):
        sources = (
            DANBOORU_SOURCE,
            E621_SOURCE,
            MERGED_SOURCE,
            KOREAN_SOURCE,
        )
        for index, source in enumerate(sources):
            with self.subTest(source=source):
                settings_file, long_text_file = self._case_paths(
                    f"explicit-internal-{index}"
                )
                stored = {
                    "autocomplete.source": source,
                    "autocomplete.limit": "17",
                }
                settings_file.write_text(
                    json.dumps(stored),
                    encoding="utf-8",
                )
                with (
                    patch.object(repository, "SETTINGS_FILE", settings_file),
                    patch.object(
                        repository,
                        "LONG_TEXT_SETTINGS_FILE",
                        long_text_file,
                    ),
                    patch.object(
                        repository,
                        "_load_comfy_settings",
                        return_value={"Comfy.Locale": "ko"},
                    ),
                ):
                    settings = repository.get_settings()

                self.assertEqual(settings["autocomplete.source"], source)
                self.assertEqual(
                    json.loads(settings_file.read_text(encoding="utf-8")),
                    stored,
                )

    def test_explicit_comfy_sources_are_preserved_without_internal_write(self):
        sources = (
            DANBOORU_SOURCE,
            E621_SOURCE,
            MERGED_SOURCE,
            KOREAN_SOURCE,
        )
        for index, source in enumerate(sources):
            with self.subTest(source=source):
                settings, settings_file = self._get_settings(
                    f"explicit-comfy-{index}",
                    {
                        "Comfy.Locale": "ko",
                        "EasyUseAnima.Prompt.AutocompleteSource": source,
                    },
                )

                self.assertEqual(settings["autocomplete.source"], source)
                self.assertFalse(settings_file.exists())

    def test_explicit_comfy_source_precedes_internal_source(self):
        settings_file, long_text_file = self._case_paths("precedence")
        stored = {"autocomplete.source": KOREAN_SOURCE}
        settings_file.write_text(json.dumps(stored), encoding="utf-8")
        with (
            patch.object(repository, "SETTINGS_FILE", settings_file),
            patch.object(
                repository,
                "LONG_TEXT_SETTINGS_FILE",
                long_text_file,
            ),
            patch.object(
                repository,
                "_load_comfy_settings",
                return_value={
                    "Comfy.Locale": "ko",
                    "EasyUseAnima.Prompt.AutocompleteSource": MERGED_SOURCE,
                },
            ),
        ):
            settings = repository.get_settings()

        self.assertEqual(settings["autocomplete.source"], MERGED_SOURCE)
        self.assertEqual(
            json.loads(settings_file.read_text(encoding="utf-8")),
            stored,
        )

    def test_persisted_initial_source_survives_locale_change(self):
        settings_file, long_text_file = self._case_paths("locale-change")
        comfy_settings = {"Comfy.Locale": "ko"}
        with (
            patch.object(repository, "SETTINGS_FILE", settings_file),
            patch.object(
                repository,
                "LONG_TEXT_SETTINGS_FILE",
                long_text_file,
            ),
            patch.object(
                repository,
                "_load_comfy_settings",
                side_effect=lambda: dict(comfy_settings),
            ),
        ):
            first = repository.get_settings()
            comfy_settings["Comfy.Locale"] = "en"
            second = repository.get_settings()

        self.assertEqual(first["autocomplete.source"], KOREAN_SOURCE)
        self.assertEqual(second["autocomplete.source"], KOREAN_SOURCE)
        self.assertEqual(
            json.loads(settings_file.read_text(encoding="utf-8")),
            {
                "version": 1,
                "values": {"autocomplete.source": KOREAN_SOURCE},
            },
        )

    def test_persistence_failure_keeps_locale_derived_runtime_value(self):
        settings_file, long_text_file = self._case_paths("write-failure")
        with (
            patch.object(repository, "SETTINGS_FILE", settings_file),
            patch.object(
                repository,
                "LONG_TEXT_SETTINGS_FILE",
                long_text_file,
            ),
            patch.object(
                repository,
                "_load_comfy_settings",
                return_value={"Comfy.Locale": "ko"},
            ),
            patch.object(
                repository.AtomicJsonStore,
                "update",
                side_effect=OSError("read-only"),
            ),
        ):
            settings = repository.get_settings()

        self.assertEqual(settings["autocomplete.source"], KOREAN_SOURCE)
        self.assertFalse(settings_file.exists())

    def test_missing_korean_csv_falls_back_without_changing_setting(self):
        settings_file, long_text_file = self._case_paths("missing-korean")
        default_csv = settings_file.parent / "danbooru.csv"
        missing_korean_csv = settings_file.parent / "missing-korean.csv"
        default_csv.write_text("sample_tag,0,1,\n", encoding="utf-8")
        stored = {"autocomplete.source": KOREAN_SOURCE}
        settings_file.write_text(json.dumps(stored), encoding="utf-8")
        sources = {
            DANBOORU_SOURCE: {
                "label": "Danbooru",
                "path": default_csv,
                "entry_count": 1,
            },
            KOREAN_SOURCE: {
                "label": "Korean",
                "path": missing_korean_csv,
                "entry_count": 1,
            },
        }

        with (
            patch.object(repository, "SETTINGS_FILE", settings_file),
            patch.object(
                repository,
                "LONG_TEXT_SETTINGS_FILE",
                long_text_file,
            ),
            patch.object(
                repository,
                "_load_comfy_settings",
                return_value={},
            ),
            patch.object(dataset, "AUTOCOMPLETE_SOURCES", sources),
        ):
            settings = repository.get_settings()
            source_key, source_path = dataset.resolve_autocomplete_source(
                settings["autocomplete.source"]
            )
            available = dataset.available_autocomplete_sources(
                settings["autocomplete.source"]
            )

        self.assertEqual(settings["autocomplete.source"], KOREAN_SOURCE)
        self.assertEqual((source_key, source_path), (DANBOORU_SOURCE, default_csv))
        self.assertTrue(
            next(item for item in available if item["key"] == DANBOORU_SOURCE)[
                "selected"
            ]
        )
        self.assertEqual(
            json.loads(settings_file.read_text(encoding="utf-8")),
            stored,
        )


if __name__ == "__main__":
    unittest.main()
