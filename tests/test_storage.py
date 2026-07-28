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

import storage as root_storage
from easyuse_anima.infrastructure.filesystem import atomic_json as storage
from easyuse_anima.infrastructure.filesystem import paths as storage_paths
from easyuse_anima.infrastructure.filesystem.atomic_json import (
    AtomicJsonStore,
    create_atomic_json_store,
)


ROOT = Path(__file__).resolve().parents[1]


def load_paths_module(folder_paths_module=None):
    missing = object()
    previous_folder_paths = sys.modules.get("folder_paths", missing)
    if folder_paths_module is not None:
        sys.modules["folder_paths"] = folder_paths_module
    elif "folder_paths" in sys.modules:
        del sys.modules["folder_paths"]

    spec = importlib.util.spec_from_file_location(
        "easyuse_anima_filesystem_paths_under_test",
        ROOT / "easyuse_anima" / "infrastructure" / "filesystem" / "paths.py",
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    try:
        spec.loader.exec_module(module)
        return module
    finally:
        sys.modules.pop(spec.name, None)
        if previous_folder_paths is not missing:
            sys.modules["folder_paths"] = previous_folder_paths
        else:
            sys.modules.pop("folder_paths", None)


class StorageCompatibilityTests(unittest.TestCase):
    def test_root_exports_are_identical_canonical_objects(self):
        canonical = {
            "AtomicJsonStore": AtomicJsonStore,
            "PACKAGE_DATA_DIR": storage_paths.PACKAGE_DATA_DIR,
            "PACKAGE_ROOT": storage_paths.PACKAGE_ROOT,
            "SYSTEM_USER_NAME": storage_paths.SYSTEM_USER_NAME,
            "USER_DATA_DIR": storage_paths.USER_DATA_DIR,
        }

        self.assertEqual(tuple(root_storage.__all__), tuple(canonical))
        for name, value in canonical.items():
            with self.subTest(name=name):
                self.assertIs(getattr(root_storage, name), value)


class StoragePathTests(unittest.TestCase):
    def test_uses_comfyui_system_user_directory_when_available(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            fake_folder_paths = types.SimpleNamespace(
                get_system_user_directory=lambda name: str(root / f"__{name}")
            )
            loaded_storage = load_paths_module(fake_folder_paths)

            self.assertEqual(loaded_storage.USER_DATA_DIR, root / "__easyuse_anima")

    def test_falls_back_to_package_data_dir_without_comfyui_folder_paths(self):
        loaded_storage = load_paths_module()

        self.assertEqual(loaded_storage.PACKAGE_ROOT, ROOT)
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

    def test_delete_removes_primary_and_backup(self):
        store = self._store()
        store.write({"value": "old"})
        store.write({"value": "current"})
        self.assertTrue(store.path.is_file())
        self.assertTrue(store.backup_path.is_file())

        store.delete()

        self.assertFalse(store.path.exists())
        self.assertFalse(store.backup_path.exists())

    def test_backup_unlink_failure_preserves_primary(self):
        store = self._store()
        store.write({"value": "old"})
        store.write({"value": "current"})
        primary = store.path.read_bytes()
        backup = store.backup_path.read_bytes()
        real_unlink = Path.unlink

        def fail_backup_unlink(path, *args, **kwargs):
            if Path(path) == store.backup_path:
                raise OSError("backup unlink failed")
            return real_unlink(path, *args, **kwargs)

        with patch.object(Path, "unlink", autospec=True, side_effect=fail_backup_unlink):
            with self.assertRaisesRegex(OSError, "backup unlink failed"):
                store.delete()

        self.assertEqual(store.path.read_bytes(), primary)
        self.assertEqual(store.backup_path.read_bytes(), backup)

    def test_primary_unlink_failure_is_propagated_after_backup_removal(self):
        store = self._store()
        store.write({"value": "old"})
        store.write({"value": "current"})
        primary = store.path.read_bytes()
        real_unlink = Path.unlink

        def fail_primary_unlink(path, *args, **kwargs):
            if Path(path) == store.path:
                raise OSError("primary unlink failed")
            return real_unlink(path, *args, **kwargs)

        with patch.object(Path, "unlink", autospec=True, side_effect=fail_primary_unlink):
            with self.assertRaisesRegex(OSError, "primary unlink failed"):
                store.delete()

        self.assertEqual(store.path.read_bytes(), primary)
        self.assertFalse(store.backup_path.exists())

    def test_backup_directory_fsync_failure_preserves_primary_and_reports_state(self):
        store = self._store()
        store.write({"value": "old"})
        store.write({"value": "current"})
        primary = store.path.read_bytes()

        with patch.object(
            storage,
            "_fsync_directory",
            side_effect=OSError("directory fsync failed"),
        ):
            with self.assertRaisesRegex(OSError, "directory fsync failed"):
                store.delete()

        self.assertEqual(store.path.read_bytes(), primary)
        self.assertFalse(store.backup_path.exists())

    def test_primary_directory_fsync_failure_reports_deleted_primary(self):
        store = self._store()
        store.write({"value": "current"})
        self.assertFalse(store.backup_path.exists())

        with patch.object(
            storage,
            "_fsync_directory",
            side_effect=OSError("directory fsync failed"),
        ):
            with self.assertRaisesRegex(OSError, "directory fsync failed"):
                store.delete()

        self.assertFalse(store.path.exists())

    def test_replace_transform_failure_preserves_source_target_and_backup(self):
        source = AtomicJsonStore(self.root / "source.json")
        target = AtomicJsonStore(self.root / "target.json")
        source.write({"settings": {"value": "old source"}})
        source.write({"settings": {"value": "source"}})
        target.write({"settings": {"value": "old target"}})
        target.write({"settings": {"value": "current target"}})
        source_bytes = source.path.read_bytes()
        source_backup_bytes = source.backup_path.read_bytes()
        target_bytes = target.path.read_bytes()
        backup_bytes = target.backup_path.read_bytes()

        def reject_source(value):
            self.assertEqual(value, {"settings": {"value": "source"}})
            raise ValueError("source schema is invalid")

        with self.assertRaisesRegex(ValueError, "source schema is invalid"):
            target.replace_from(source, transform=reject_source)

        self.assertEqual(source.path.read_bytes(), source_bytes)
        self.assertEqual(source.backup_path.read_bytes(), source_backup_bytes)
        self.assertEqual(target.path.read_bytes(), target_bytes)
        self.assertEqual(target.backup_path.read_bytes(), backup_bytes)
        self.assertEqual(self._temp_files(), [])

    def test_replace_transform_persists_returned_value_and_exact_target_backup(self):
        source = AtomicJsonStore(self.root / "source.json")
        target = AtomicJsonStore(self.root / "target.json")
        source.write({"settings": {"value": "old source"}})
        source.write({"settings": {"value": "source"}})
        target.write({"settings": {"value": "old target"}})
        target.write({"settings": {"value": "target"}})
        target_bytes = target.path.read_bytes()

        transformed = target.replace_from(
            source,
            transform=lambda value: {
                "version": 2,
                "name": "target",
                **value,
            },
        )

        self.assertEqual(target.read(), transformed)
        self.assertFalse(source.path.exists())
        self.assertFalse(source.backup_path.exists())
        self.assertEqual(target.backup_path.read_bytes(), target_bytes)
        self.assertEqual(self._temp_files(), [])

    def test_replace_source_backup_removal_failure_preserves_all_files(self):
        source = AtomicJsonStore(self.root / "source.json")
        target = AtomicJsonStore(self.root / "target.json")
        source.write({"settings": {"value": "old source"}})
        source.write({"settings": {"value": "source"}})
        target.write({"settings": {"value": "target"}})
        source_bytes = source.path.read_bytes()
        source_backup_bytes = source.backup_path.read_bytes()
        target_bytes = target.path.read_bytes()
        real_unlink = Path.unlink

        def fail_source_backup_removal(path, *args, **kwargs):
            if Path(path) == source.backup_path:
                raise OSError("source backup removal failed")
            return real_unlink(path, *args, **kwargs)

        with patch.object(
            Path,
            "unlink",
            autospec=True,
            side_effect=fail_source_backup_removal,
        ):
            with self.assertRaisesRegex(OSError, "source backup removal failed"):
                target.replace_from(
                    source,
                    transform=lambda value: {"version": 2, **value},
                )

        self.assertEqual(source.path.read_bytes(), source_bytes)
        self.assertEqual(source.backup_path.read_bytes(), source_backup_bytes)
        self.assertEqual(target.path.read_bytes(), target_bytes)
        self.assertFalse(target.backup_path.exists())
        self.assertEqual(self._temp_files(), [])

    def test_replace_transform_publication_failure_rolls_back_and_cleans_temps(self):
        source = AtomicJsonStore(self.root / "source.json")
        target = AtomicJsonStore(self.root / "target.json")
        source.write({"settings": {"value": "old source"}})
        source.write({"settings": {"value": "source"}})
        target.write({"settings": {"value": "old target"}})
        target.write({"settings": {"value": "current target"}})
        source_bytes = source.path.read_bytes()
        source_backup_bytes = source.backup_path.read_bytes()
        target_bytes = target.path.read_bytes()
        target_backup_bytes = target.backup_path.read_bytes()
        real_replace = storage.os.replace
        state = {"source_moved": False, "publication_failed": False}

        def fail_transformed_publication(current, destination):
            current_path = Path(current)
            destination_path = Path(destination)
            if current_path == source.path and destination_path == target.path:
                state["source_moved"] = True
                return real_replace(current, destination)
            if (
                state["source_moved"]
                and not state["publication_failed"]
                and destination_path == target.path
            ):
                state["publication_failed"] = True
                raise OSError("transformed publication failed")
            return real_replace(current, destination)

        with patch.object(storage.os, "replace", side_effect=fail_transformed_publication):
            with self.assertRaisesRegex(OSError, "transformed publication failed"):
                target.replace_from(
                    source,
                    transform=lambda value: {"version": 2, **value},
                )

        self.assertEqual(source.path.read_bytes(), source_bytes)
        self.assertEqual(source.backup_path.read_bytes(), source_backup_bytes)
        self.assertEqual(target.path.read_bytes(), target_bytes)
        self.assertEqual(target.backup_path.read_bytes(), target_backup_bytes)
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

    def test_direct_and_factory_stores_share_the_same_resolved_path_lock(self):
        first_store = AtomicJsonStore(self.root / "nested" / ".." / "state.json")
        second_store = create_atomic_json_store(self.root / "state.json")
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

    def test_factory_forwards_backup_policy_to_canonical_store(self):
        without_backup = create_atomic_json_store(
            self.root / "without_backup.json",
            backup=False,
        )
        custom_backup = self.root / "custom.backup"
        with_backup = create_atomic_json_store(
            self.root / "with_backup.json",
            backup=custom_backup,
        )

        self.assertIsInstance(without_backup, AtomicJsonStore)
        self.assertIsNone(without_backup.backup_path)
        self.assertEqual(with_backup.backup_path, custom_backup.resolve())

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
