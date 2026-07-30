from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from easyuse_anima.autocomplete import dataset
from easyuse_anima.autocomplete.index import _AutocompleteIndexStore
from easyuse_anima.autocomplete.ports import AutocompletePort
from easyuse_anima.autocomplete.service import _AutocompleteService


class AutocompleteServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        dataset._DEFAULT_AUTOCOMPLETE_SNAPSHOTS.clear()

    def tearDown(self) -> None:
        dataset._DEFAULT_AUTOCOMPLETE_SNAPSHOTS.clear()

    def test_isolated_service_uses_only_its_injected_snapshot_and_index_owners(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory(
            prefix="easyuse-anima-autocomplete-service-"
        ) as temporary_directory:
            root = Path(temporary_directory)
            path = root / "tags.csv"
            path.write_text(
                'owned service tag,0,100,"[일반] owned service"\n',
                encoding="utf-8",
            )
            snapshots = dataset._AutocompleteSnapshotStore()
            index_store = _AutocompleteIndexStore(root / "index")
            service = _AutocompleteService(
                snapshots=snapshots,
                index_store=index_store,
            )
            port: AutocompletePort = service
            key = dataset._cache_key(path)

            status = port.status(path)
            searched = port.search("owned service", path=path)
            classified = port.classify("owned service tag", path=path)
            empty = port.search("", path=path)

            with snapshots._lock:
                self.assertIn(key.resolved_path, snapshots._cache)
            with dataset._DEFAULT_AUTOCOMPLETE_SNAPSHOTS._lock:
                self.assertNotIn(
                    key.resolved_path,
                    dataset._DEFAULT_AUTOCOMPLETE_SNAPSHOTS._cache,
                )

            index_files = tuple((root / "index").glob("*.sqlite3"))

        self.assertIs(service.snapshots, snapshots)
        self.assertIs(service.index_store, index_store)
        self.assertEqual(status["count"], 1)
        self.assertEqual(searched["results"][0]["tag"], "owned service tag")
        self.assertTrue(classified["tokens"][0]["learned"])
        self.assertEqual(empty["status"]["count"], 1)
        self.assertEqual(len(index_files), 1)


if __name__ == "__main__":
    unittest.main()
