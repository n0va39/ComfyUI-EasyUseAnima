from __future__ import annotations

import os
import sqlite3
import subprocess
import tempfile
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import patch

import autocomplete_dataset as dataset
import autocomplete_index
from easyuse_anima.autocomplete import index as autocomplete_index_impl


ROOT = Path(__file__).resolve().parents[1]


class AutocompleteIndexTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory(
            prefix="easyuse-anima-index-test-"
        )
        self.root = Path(self.temporary_directory.name)
        self.index_root = self.root / "index"

    def tearDown(self) -> None:
        with dataset._CACHE_LOCK:
            dataset._CACHE.clear()
            dataset._INFLIGHT.clear()
        self.temporary_directory.cleanup()

    def _write(self, name: str, rows: list[str]) -> Path:
        path = self.root / name
        path.write_text("\n".join(rows) + "\n", encoding="utf-8")
        return path

    def _search(self, query: str, *, path: Path, limit: int = 20, category: str = ""):
        with patch.object(dataset, "_AUTOCOMPLETE_INDEX_DIR", self.index_root):
            return dataset._search_autocomplete_with_diagnostics(
                query,
                limit=limit,
                path=path,
                category=category,
            )

    def _reference(self, query: str, *, path: Path, limit: int, category: str):
        entries = dataset._load_entries(path)
        categories = {item.strip() for item in category.split(",") if item.strip()}
        matches = dataset._top_autocomplete_matches(
            entries,
            dataset._normalize(query),
            categories,
            max(1, min(limit, 100)),
        )
        return [
            {
                "tag": entry.tag,
                "category": entry.category,
                "count": entry.count,
                "description": entry.description,
            }
            for _, entry in matches
        ]

    def test_index_preserves_exact_ranking_category_filter_and_top_n(self):
        path = self._write(
            "parity.csv",
            [
                'needle prefix high,0,900,"[일반] prefix"',
                'needle prefix artist,1,850,"[작가] prefix"',
                'popular needle middle,0,800,"[일반] substring"',
                'description only,0,700,"[일반] needle description"',
                'needle,0,1,"[일반] exact low count"',
                'needle,1,2,"[작가] duplicate exact"',
                'percent 100% ready,0,600,"[일반] literal percent"',
                'korean description,0,500,"[일반] 한글 설명 검색"',
                'literal under score,0,490,"[일반] normalized underscore"',
                'glob*star literal,0,480,"[일반] literal asterisk"',
                'glob?question literal,0,470,"[일반] literal question"',
                'glob[bracket literal,0,460,"[일반] literal bracket"',
                '"quote ""and"" or literal",0,450,"[일반] quote operator"',
            ],
        )

        cases = [
            ("needle", 3, "", "needle"),
            ("needle", 6, "artist", "needle"),
            ("needle", 100, "artist,general", "needle"),
            ("100%", 20, "", "percent 100% ready"),
            ("한글 설명", 20, "general", "korean description"),
            ("literal_under", 20, "", "literal under score"),
            ("glob*star", 20, "", "glob*star literal"),
            ("glob?question", 20, "", "glob?question literal"),
            ("glob[bracket", 20, "", "glob[bracket literal"),
            ('quote "and" OR', 20, "", 'quote "and" or literal'),
        ]
        outcomes = []
        for query, limit, category, expected_first in cases:
            with self.subTest(query=query, limit=limit, category=category):
                result, diagnostics = self._search(
                    query,
                    path=path,
                    limit=limit,
                    category=category,
                )
                outcomes.append(diagnostics.outcome)
                self.assertEqual(
                    result["results"],
                    self._reference(
                        query,
                        path=path,
                        limit=limit,
                        category=category,
                    ),
                )
                self.assertLessEqual(len(result["results"]), max(1, min(limit, 100)))
                self.assertEqual(result["results"][0]["tag"], expected_first)

        self.assertEqual(outcomes[0], "rebuild")
        self.assertTrue(all(outcome == "hit" for outcome in outcomes[1:]))

        with patch.object(
            dataset,
            "_load_entries",
            side_effect=AssertionError("warm indexed search must not load or scan CSV entries"),
        ):
            warm, diagnostics = self._search("needle", path=path, limit=2)
        self.assertEqual(diagnostics.outcome, "hit")
        self.assertEqual(len(warm["results"]), 2)

    def test_glob_candidate_pattern_is_literal_and_uses_the_trigram_plan(self):
        self.assertEqual(
            autocomplete_index_impl._glob_pattern('%_"OR"*?[literal'),
            '*%_"OR"[*][?][[]literal*',
        )
        path = self._write(
            "query-plan.csv",
            [
                f'candidate tag {index:04d},0,{2000 - index},"[일반] indexed candidate"'
                for index in range(1000)
            ],
        )
        _result, diagnostics = self._search("candidate tag 050", path=path)
        self.assertEqual(diagnostics.backend, "fts5_trigram")
        self.assertIsNotNone(diagnostics.index_path)
        assert diagnostics.index_path is not None

        connection = sqlite3.connect(diagnostics.index_path)
        try:
            plan = connection.execute(
                "EXPLAIN QUERY PLAN "
                "SELECT e.tag FROM autocomplete_entries_fts AS f "
                "JOIN autocomplete_entries AS e ON e.id = f.rowid "
                "WHERE f.tag_key GLOB ? AND instr(e.tag_key, ?) > 0",
                (
                    autocomplete_index_impl._glob_pattern("candidate tag 050"),
                    "candidate tag 050",
                ),
            ).fetchall()
        finally:
            connection.close()

        details = [str(row[3]) for row in plan]
        self.assertTrue(
            any("VIRTUAL TABLE INDEX 0:G0" in detail for detail in details),
            details,
        )

    def test_source_revision_change_rebuilds_the_same_index(self):
        path = self._write(
            "revision.csv",
            ['alpha tag,0,100,"[일반] alpha"'],
        )
        first, first_diagnostics = self._search("alpha", path=path)
        second, second_diagnostics = self._search("alpha", path=path)
        with patch.object(
            dataset,
            "_validate_index_source",
            side_effect=[dataset._AutocompleteSourceChanged(str(path)), None],
        ) as validate_source:
            retried, retried_diagnostics = self._search("alpha", path=path)

        previous_stat = path.stat()
        path.write_text(
            'beta replacement tag,0,90,"[일반] beta replacement"\n',
            encoding="utf-8",
        )
        next_mtime = previous_stat.st_mtime_ns + 1_000_000_000
        os.utime(path, ns=(next_mtime, next_mtime))
        third, third_diagnostics = self._search("beta", path=path)

        self.assertEqual(first["results"][0]["tag"], "alpha tag")
        self.assertEqual(second_diagnostics.outcome, "hit")
        self.assertEqual(retried["results"], second["results"])
        self.assertEqual(retried_diagnostics.outcome, "hit")
        self.assertEqual(validate_source.call_count, 2)
        self.assertEqual(third["results"][0]["tag"], "beta replacement tag")
        self.assertEqual(third_diagnostics.outcome, "rebuild")
        self.assertEqual(third_diagnostics.reason, "source_revision_mismatch")
        self.assertNotEqual(
            first_diagnostics.source_revision,
            third_diagnostics.source_revision,
        )
        self.assertEqual(first_diagnostics.index_path, third_diagnostics.index_path)

    def test_corrupt_and_schema_mismatch_indexes_rebuild_safely(self):
        path = self._write(
            "rebuild.csv",
            ['recoverable tag,0,100,"[일반] recoverable"'],
        )
        expected, initial = self._search("recoverable", path=path)
        self.assertIsNotNone(initial.index_path)
        index_path = initial.index_path
        assert index_path is not None

        index_path.write_bytes(b"not a sqlite database")
        recovered, corrupt = self._search("recoverable", path=path)
        self.assertEqual(recovered["results"], expected["results"])
        self.assertEqual(corrupt.outcome, "rebuild")
        self.assertIn(corrupt.reason, {"corrupt", "unreadable"})

        connection = sqlite3.connect(index_path)
        try:
            connection.execute(
                "UPDATE autocomplete_index_metadata "
                "SET schema_version = 'not-an-integer' WHERE id = 1"
            )
            connection.commit()
        finally:
            connection.close()
        malformed_result, malformed = self._search("recoverable", path=path)
        self.assertEqual(malformed_result["results"], expected["results"])
        self.assertEqual(malformed.outcome, "rebuild")
        self.assertEqual(malformed.reason, "corrupt")

        connection = sqlite3.connect(index_path)
        try:
            connection.execute(
                "UPDATE autocomplete_index_metadata SET schema_version = 0 WHERE id = 1"
            )
            connection.commit()
        finally:
            connection.close()
        upgraded, schema = self._search("recoverable", path=path)
        self.assertEqual(upgraded["results"], expected["results"])
        self.assertEqual(schema.outcome, "rebuild")
        self.assertEqual(schema.reason, "schema_mismatch")

    def test_concurrent_first_access_coalesces_and_locked_read_falls_back(self):
        path = self._write(
            "concurrent.csv",
            [f'shared tag {index:03d},0,{1000 - index},"[일반] shared"' for index in range(80)],
        )
        start = threading.Barrier(7)

        def search_once():
            start.wait(timeout=5)
            return dataset._search_autocomplete_with_diagnostics("shared", path=path)

        with patch.object(dataset, "_AUTOCOMPLETE_INDEX_DIR", self.index_root):
            with ThreadPoolExecutor(max_workers=6) as executor:
                futures = [executor.submit(search_once) for _ in range(6)]
                start.wait(timeout=5)
                searched = [future.result(timeout=10) for future in futures]

        outcomes = [diagnostics.outcome for _, diagnostics in searched]
        observations = [
            (diagnostics.outcome, diagnostics.reason)
            for _, diagnostics in searched
        ]
        self.assertEqual(outcomes.count("rebuild"), 1, observations)
        self.assertEqual(outcomes.count("hit"), 5, observations)
        self.assertTrue(all(result["results"] for result, _ in searched))

        with patch.object(
            autocomplete_index_impl,
            "_query_index",
            side_effect=sqlite3.OperationalError("database is locked"),
        ):
            fallback, diagnostics = self._search("shared", path=path, limit=4)

        self.assertEqual(diagnostics.outcome, "fallback")
        self.assertEqual(diagnostics.reason, "locked")
        self.assertEqual(
            fallback["results"],
            self._reference("shared", path=path, limit=4, category=""),
        )

    def test_custom_csv_keeps_exact_fallback_when_persistent_index_is_disabled(self):
        path = self._write(
            "custom-header.csv",
            [
                "name,category,post_count,description",
                'custom character,4,90,"[캐릭터] 사용자 정의 설명"',
                'custom general,0,100,"[일반] 사용자 정의 일반"',
            ],
        )
        with patch.object(dataset, "_AUTOCOMPLETE_INDEX_DIR", None):
            result, diagnostics = dataset._search_autocomplete_with_diagnostics(
                "사용자 정의",
                path=path,
                category="character",
            )

        self.assertEqual(diagnostics.outcome, "fallback")
        self.assertEqual(diagnostics.reason, "disabled")
        self.assertEqual(result["results"][0]["tag"], "custom character")
        self.assertEqual(result["results"][0]["category"], "character")
        self.assertEqual(result["status"]["count"], 2)

    def test_index_module_is_inside_registry_package_closure(self):
        source = (ROOT / "autocomplete_dataset.py").read_text(encoding="utf-8")
        self.assertIn(
            "from .easyuse_anima.autocomplete.index import (",
            source,
        )
        self.assertIn(
            "from easyuse_anima.autocomplete.index import (",
            source,
        )
        ignored = subprocess.run(
            [
                "git",
                "ls-files",
                "--others",
                "--ignored",
                "--exclude-from=.comfyignore",
                "--",
                "autocomplete_index.py",
                "easyuse_anima/autocomplete/__init__.py",
                "easyuse_anima/autocomplete/index.py",
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(ignored.returncode, 0, ignored.stdout + ignored.stderr)
        self.assertEqual(ignored.stdout.strip(), "", ignored.stdout + ignored.stderr)

    def test_root_index_module_is_an_explicit_canonical_identity_shim(self):
        expected = (
            "AUTOCOMPLETE_INDEX_SCHEMA_VERSION",
            "AutocompleteIndexSource",
            "IndexedAutocompleteEntry",
            "AutocompleteIndexDiagnostics",
            "AutocompleteIndexResult",
            "AutocompleteIndexUnavailable",
            "search_autocomplete_index",
        )
        self.assertEqual(autocomplete_index.__all__, expected)
        self.assertEqual(autocomplete_index_impl.__all__, expected)
        for name in expected:
            with self.subTest(name=name):
                self.assertIs(
                    getattr(autocomplete_index, name),
                    getattr(autocomplete_index_impl, name),
                )


if __name__ == "__main__":
    unittest.main()
