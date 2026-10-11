from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from easyuse_anima.autocomplete import custom_sources, dataset
from easyuse_anima.autocomplete.index import _AutocompleteIndexStore
from easyuse_anima.autocomplete.service import _AutocompleteService
from easyuse_anima.api.routes.autocomplete import build_autocomplete_payloads


class CustomAutocompleteCsvTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="easyuse-custom-csv-")
        self.addCleanup(temporary.cleanup)
        self.user = Path(temporary.name).resolve()
        self.root = self.user / "autocomplete"
        self.addCleanup(patch.stopall)
        patch.object(custom_sources, "USER_DATA_DIR", self.user).start()
        self.service = _AutocompleteService(
            snapshots=dataset._AutocompleteSnapshotStore(),
            index_store=_AutocompleteIndexStore(self.user / "cache"),
        )

    def write_csv(self, name="내 태그.csv", text=None):
        self.root.mkdir(exist_ok=True)
        path = self.root / name
        path.write_text(
            text if text is not None else
            'name,category,post_count,description\ncustom_hair,0,42,"나만의 머리"\n',
            encoding="utf-8-sig",
        )
        return path

    def test_absent_folder_is_read_only_and_bundled_defaults_are_unchanged(self):
        sources = self.service.available_sources()
        self.assertEqual([row["key"] for row in sources], list(dataset.AUTOCOMPLETE_SOURCES))
        self.assertEqual(self.service.resolve_source()[0], dataset.DEFAULT_AUTOCOMPLETE_SOURCE)
        self.assertFalse(self.root.exists())

    def test_custom_choice_search_highlight_reload_and_removal(self):
        path = self.write_csv()
        custom = self.service.available_sources()[-1]
        key = custom["key"]
        self.assertRegex(key, r"^custom:[0-9a-f]{64}$")
        self.assertEqual(custom["label"], "Custom: 내 태그.csv")
        self.assertEqual(self.service.resolve_source(key), (key, path))
        self.assertTrue(self.service.available_sources(key)[-1]["selected"])
        self.assertEqual(self.service.search("나만의", path=path)["results"][0]["tag"], "custom_hair")
        self.assertTrue(self.service.classify("custom hair", path=path)["tokens"][0]["learned"])
        self.assertEqual(self.service.status(path)["count"], 1)
        self.write_csv(text='new_artist,1,99,"추가한 작가"\n')
        self.assertEqual(self.service.resolve_source(key)[0], key)
        self.assertEqual(self.service.search("추가한", path=path, category="artist")["results"][0]["tag"], "new_artist")
        path.unlink()
        self.assertEqual(self.service.resolve_source(key)[0], dataset.DEFAULT_AUTOCOMPLETE_SOURCE)

    def test_client_paths_and_urls_cannot_select_files(self):
        self.write_csv()
        for value in ["../private.csv", "custom:../private.csv", "custom:내 태그.csv",
                      "custom:" + "a" * 64, str(self.root / "내 태그.csv"),
                      "https://example.com/tags.csv", "\\\\server\\share\\tags.csv"]:
            with self.subTest(value=value):
                self.assertEqual(self.service.resolve_source(value)[0], dataset.DEFAULT_AUTOCOMPLETE_SOURCE)

    def test_non_csv_nested_hardlinks_and_oversized_files_are_excluded(self):
        path = self.write_csv("valid.csv")
        self.write_csv("ignored.txt")
        nested = self.root / "nested"
        nested.mkdir()
        (nested / "hidden.csv").write_text("secret,0,1,private", encoding="utf-8")
        external = self.user / "private.csv"
        external.write_text("private,0,1,private", encoding="utf-8")
        os.link(external, self.root / "linked.csv")
        oversized = self.write_csv("large.csv", "x" * 2048)
        with patch.object(custom_sources, "MAX_CUSTOM_CSV_BYTES", 1024):
            self.assertEqual(list(custom_sources.custom_csv_sources().values()), [path])
            with self.assertRaises(ValueError):
                dataset._load_entries(oversized)

    def test_reparse_file_and_folder_are_rejected(self):
        path = self.write_csv()
        original = Path.lstat
        for redirected in [path, self.root]:
            def lstat(candidate):
                value = original(candidate)
                if candidate == redirected:
                    return SimpleNamespace(st_mode=value.st_mode, st_file_attributes=0x400)
                return value
            with self.subTest(path=redirected), patch.object(Path, "lstat", lstat):
                self.assertEqual(custom_sources.custom_csv_sources(), {})
                with self.assertRaises(ValueError):
                    custom_sources.read_custom_csv(path)

    def test_file_replacement_after_selection_is_checked_before_read(self):
        path = self.write_csv()
        selected = self.service.resolve_source(self.service.available_sources()[-1]["key"])[1]
        external = self.user / "private.csv"
        external.write_text("private,0,1,secret", encoding="utf-8")
        path.unlink()
        os.link(external, path)
        with self.assertRaises(ValueError):
            self.service.search("private", path=selected)

    def test_invalid_utf8_keeps_public_catalog_available_without_paths(self):
        path = self.write_csv()
        key = self.service.available_sources()[-1]["key"]
        path.write_bytes(b"\xff\xff")
        status_payload, _, _, _, _ = build_autocomplete_payloads(
            resolve_autocomplete_source=lambda: key,
            resolve_autocomplete_source_path=self.service.resolve_source,
            autocomplete_status=self.service.status,
            available_autocomplete_sources=self.service.available_sources,
            resolve_autocomplete_limit=lambda: 20,
            search_autocomplete=self.service.search,
            classify_prompt_text=self.service.classify,
            public_autocomplete_status=lambda value: {
                field: item for field, item in value.items() if field != "path"
            },
            public_autocomplete_payload=lambda value: value,
        )
        payload = status_payload()
        self.assertIn("error", payload)
        self.assertEqual(payload["sources"][-1]["key"], key)
        self.assertNotIn(str(self.user), str(payload))


if __name__ == "__main__":
    unittest.main()
