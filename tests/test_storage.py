from __future__ import annotations

import importlib.util
import json
import shutil
import sys
import tempfile
import threading
import types
import unittest
from pathlib import Path
from unittest.mock import patch

import storage
from storage import AtomicJsonStore


ROOT = Path(__file__).resolve().parents[1]


def load_storage_module(folder_paths_module=None):
    package_name = "easyuse_anima_storage_test_package"
    package = types.ModuleType(package_name)
    package.__path__ = [str(ROOT)]
    sys.modules[package_name] = package

    previous_folder_paths = sys.modules.get("folder_paths")
    if folder_paths_module is not None:
        sys.modules["folder_paths"] = folder_paths_module
    elif "folder_paths" in sys.modules:
        del sys.modules["folder_paths"]

    try:
        spec = importlib.util.spec_from_file_location(
            f"{package_name}.storage",
            ROOT / "storage.py",
        )
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        return module
    finally:
        if previous_folder_paths is not None:
            sys.modules["folder_paths"] = previous_folder_paths
        elif "folder_paths" in sys.modules:
            del sys.modules["folder_paths"]


class StoragePathTests(unittest.TestCase):
    def test_uses_comfyui_system_user_directory_when_available(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            fake_folder_paths = types.SimpleNamespace(
                get_system_user_directory=lambda name: str(root / f"__{name}")
            )
            loaded_storage = load_storage_module(fake_folder_paths)

            self.assertEqual(loaded_storage.USER_DATA_DIR, root / "__easyuse_anima")

    def test_falls_back_to_package_data_dir_without_comfyui_folder_paths(self):
        loaded_storage = load_storage_module()

        self.assertEqual(loaded_storage.USER_DATA_DIR, loaded_storage.PACKAGE_DATA_DIR)


class AtomicJsonStoreTests(unittest.TestCase):
    def setUp(self):
        self.root = ROOT / "__pycache__" / "atomic_json_store_tests" / self._testMethodName
        shutil.rmtree(self.root, ignore_errors=True)
        self.root.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def _store(self) -> AtomicJsonStore:
        return AtomicJsonStore(self.root / "state.json")

    def _temp_files(self) -> list[Path]:
        return [path for path in self.root.iterdir() if path.name.endswith(".tmp")]

    def test_replace_failure_preserves_primary_bytes_and_cleans_temps(self):
        store = self._store()
        store.write({"value": "old"}, trailing_newline=True)
        original = store.path.read_bytes()
        real_replace = storage.os.replace
        primary_temp_paths: list[Path] = []

        def fail_primary_publish(source, target):
            if Path(target) == store.path:
                primary_temp_paths.append(Path(source))
                raise OSError("primary publish failed")
            return real_replace(source, target)

        with patch.object(storage.os, "replace", side_effect=fail_primary_publish):
            with self.assertRaisesRegex(OSError, "primary publish failed"):
                store.write({"value": "new"}, trailing_newline=True)

        self.assertEqual(store.path.read_bytes(), original)
        self.assertEqual(store.read(), {"value": "old"})
        self.assertEqual(json.loads(store.backup_path.read_text(encoding="utf-8")), {"value": "old"})
        self.assertEqual([path.parent for path in primary_temp_paths], [store.path.parent])
        self.assertEqual(self._temp_files(), [])

    def test_temp_fsync_failure_preserves_primary_and_cleans_temp(self):
        store = self._store()
        store.write({"value": "old"})
        original = store.path.read_bytes()

        with patch.object(storage.os, "fsync", side_effect=OSError("data fsync failed")):
            with self.assertRaisesRegex(OSError, "data fsync failed"):
                store.write({"value": "new"})

        self.assertEqual(store.path.read_bytes(), original)
        self.assertEqual(self._temp_files(), [])

    def test_temp_creation_failure_preserves_primary(self):
        store = self._store()
        store.write({"value": "old"})
        original = store.path.read_bytes()

        with patch.object(storage.tempfile, "mkstemp", side_effect=OSError("temp create failed")):
            with self.assertRaisesRegex(OSError, "temp create failed"):
                store.write({"value": "new"})

        self.assertEqual(store.path.read_bytes(), original)
        self.assertEqual(self._temp_files(), [])

    def test_backup_publish_failure_preserves_primary_and_previous_backup(self):
        store = self._store()
        store.write({"value": "first"})
        store.write({"value": "second"})
        primary = store.path.read_bytes()
        backup = store.backup_path.read_bytes()
        real_replace = storage.os.replace

        def fail_backup_publish(source, target):
            if Path(target) == store.backup_path:
                raise OSError("backup publish failed")
            return real_replace(source, target)

        with patch.object(storage.os, "replace", side_effect=fail_backup_publish):
            with self.assertRaisesRegex(OSError, "backup publish failed"):
                store.write({"value": "third"})

        self.assertEqual(store.path.read_bytes(), primary)
        self.assertEqual(store.backup_path.read_bytes(), backup)
        self.assertEqual(self._temp_files(), [])

    def test_invalid_or_missing_primary_reads_valid_backup_without_repair(self):
        store = self._store()
        store.path.write_text("{", encoding="utf-8")
        store.backup_path.write_text('{"value": "backup"}', encoding="utf-8")

        self.assertEqual(store.read(), {"value": "backup"})
        self.assertEqual(store.path.read_text(encoding="utf-8"), "{")

        store.path.unlink()
        self.assertEqual(store.read(), {"value": "backup"})
        self.assertFalse(store.path.exists())

    def test_invalid_backup_uses_explicit_error_or_default_contract(self):
        store = self._store()
        store.path.write_text("{", encoding="utf-8")
        store.backup_path.write_text("[", encoding="utf-8")

        with self.assertRaises(json.JSONDecodeError):
            store.read()
        self.assertEqual(store.read(default={"fallback": True}), {"fallback": True})

        store.path.unlink()
        with self.assertRaises(json.JSONDecodeError):
            store.read()

    def test_store_instances_share_the_same_resolved_path_lock(self):
        first_store = AtomicJsonStore(self.root / "nested" / ".." / "state.json")
        second_store = self._store()
        first_entered = threading.Event()
        release_first = threading.Event()
        second_attempted = threading.Event()
        second_entered = threading.Event()

        def hold_first_lock():
            with first_store.locked():
                first_entered.set()
                self.assertTrue(release_first.wait(2))

        def enter_second_lock():
            self.assertTrue(first_entered.wait(2))
            second_attempted.set()
            with second_store.locked():
                second_entered.set()

        first = threading.Thread(target=hold_first_lock)
        second = threading.Thread(target=enter_second_lock)
        first.start()
        second.start()
        self.assertTrue(first_entered.wait(2))
        self.assertTrue(second_attempted.wait(2))
        self.assertFalse(second_entered.wait(0.05))
        release_first.set()
        first.join(2)
        second.join(2)

        self.assertFalse(first.is_alive())
        self.assertFalse(second.is_alive())
        self.assertTrue(second_entered.is_set())

    def test_reader_sees_complete_primary_while_publish_is_blocked(self):
        writer_store = self._store()
        reader_store = AtomicJsonStore(self.root / "." / "state.json")
        writer_store.write({"value": "old", "items": list(range(100))})
        publish_ready = threading.Event()
        release_publish = threading.Event()
        errors: list[BaseException] = []
        real_replace = storage.os.replace

        def block_primary_publish(source, target):
            if Path(target) == writer_store.path:
                publish_ready.set()
                if not release_publish.wait(2):
                    raise AssertionError("publish release was not signaled")
            return real_replace(source, target)

        def write_new_value():
            try:
                writer_store.write({"value": "new", "items": list(range(1000))})
            except BaseException as exc:
                errors.append(exc)

        with patch.object(storage.os, "replace", side_effect=block_primary_publish):
            writer = threading.Thread(target=write_new_value)
            writer.start()
            self.assertTrue(publish_ready.wait(2))
            visible = json.loads(writer_store.path.read_text(encoding="utf-8"))
            self.assertEqual(visible["value"], "old")
            release_publish.set()
            writer.join(2)

        self.assertFalse(writer.is_alive())
        self.assertEqual(errors, [])
        self.assertEqual(reader_store.read()["value"], "new")
        self.assertEqual(self._temp_files(), [])


if __name__ == "__main__":
    unittest.main()
