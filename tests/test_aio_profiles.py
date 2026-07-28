from __future__ import annotations

import asyncio
import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
import textwrap
import threading
import types
import unittest
import uuid
from pathlib import Path
from unittest.mock import patch

from tests.api_test_support import replace_sys_modules

ROOT = Path(__file__).resolve().parents[1]
PRESETS_JS = ROOT / "web" / "js" / "aio" / "presets.js"


def profile_tokens(profile: dict, *, prefix: str = "") -> dict:
    return {
        f"{prefix}profile_id": profile["profile_id"],
        f"{prefix}revision": profile["revision"],
    }


def directory_snapshot(root: Path) -> dict:
    return {
        path.name: (path.read_bytes(), path.stat().st_mtime_ns)
        for path in root.iterdir()
        if path.is_file()
    }


def load_api_module():
    package_name = "easyuse_anima_aio_profile_test_package"
    package = types.ModuleType(package_name)
    package.__path__ = [str(ROOT)]
    sys.modules[package_name] = package

    spec = importlib.util.spec_from_file_location(
        f"{package_name}.api",
        ROOT / "api.py",
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class RouteRegistry:
    def __init__(self):
        self.handlers = {}

    def get(self, path):
        def register(handler):
            self.handlers[path] = handler
            return handler

        return register

    def post(self, path):
        return self.get(path)


class JsonRequest:
    def __init__(self, payload):
        self.payload = payload

    async def json(self):
        return self.payload


def load_api_routes():
    routes = RouteRegistry()
    fake_server = types.ModuleType("server")
    fake_server.PromptServer = type(
        "PromptServer",
        (),
        {"instance": types.SimpleNamespace(routes=routes)},
    )
    fake_aiohttp = types.ModuleType("aiohttp")
    fake_aiohttp.web = types.SimpleNamespace(
        json_response=lambda payload, status=200: {"payload": payload, "status": status},
    )
    with replace_sys_modules({"server": fake_server, "aiohttp": fake_aiohttp}):
        api = load_api_module()
        api.register_routes()
    return api, routes


class AIOProfileStorageTests(unittest.TestCase):
    def test_root_profile_aliases_are_identical_to_canonical_owners(self):
        api = load_api_module()

        self.assertIs(api.InvalidProfileDataError, api._profile_repository.InvalidProfileDataError)
        self.assertIs(
            api.PROFILE_MUTATION_COORDINATOR,
            api._profile_mutation.PROFILE_MUTATION_COORDINATOR,
        )
        self.assertIs(
            api._lora_profiles.PROFILE_MUTATION_COORDINATOR,
            api.PROFILE_MUTATION_COORDINATOR,
        )
        self.assertIs(
            api._aio_profiles.PROFILE_MUTATION_COORDINATOR,
            api.PROFILE_MUTATION_COORDINATOR,
        )
        self.assertIs(
            api._lora_profiles.AtomicJsonStore,
            api._profile_repository.AtomicJsonStore,
        )
        self.assertIs(
            api._aio_profiles.AtomicJsonStore,
            api._profile_repository.AtomicJsonStore,
        )
        self.assertIs(api.legacy_profile_id, api._profile_contract.legacy_profile_id)
        self.assertIs(api._read_profile_json, api._profile_repository._read_profile_json)
        self.assertIs(api._save_aio_profile, api._aio_profiles._save_aio_profile)
        self.assertIs(api._load_aio_profile, api._aio_profiles._load_aio_profile)
        self.assertIs(api._list_aio_profiles, api._aio_profiles._list_aio_profiles)
        self.assertIs(api._delete_aio_profile, api._aio_profiles._delete_aio_profile)
        self.assertIs(api._rename_aio_profile, api._aio_profiles._rename_aio_profile)
        self.assertIs(api._save_lora_profile, api._lora_profiles._save_lora_profile)
        self.assertIs(api._load_lora_profile, api._lora_profiles._load_lora_profile)
        self.assertIs(api._list_lora_profiles, api._lora_profiles._list_lora_profiles)
        self.assertIs(
            api._fix_lora_profile_payload,
            api._lora_profiles._fix_lora_profile_payload,
        )

    def test_repository_dependency_uses_current_aio_dir_factory_and_coordinator(self):
        api = load_api_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with (
                patch.object(api._aio_profiles, "AIO_PROFILE_DIR", root),
                patch.object(
                    api._aio_profiles,
                    "create_atomic_json_store",
                ) as store_factory,
                patch.object(
                    api._aio_profiles,
                    "PROFILE_MUTATION_COORDINATOR",
                ) as coordinator,
            ):
                repository = api._aio_profiles._current_aio_profile_repository()
                store = repository.store(root / "profile.json", backup=False)
                locked = repository.locked()

            self.assertEqual(repository.profile_dir, root)
            self.assertIs(repository.store_factory, store_factory)
            self.assertIs(repository.mutation_coordinator, coordinator)
            self.assertIs(store, store_factory.return_value)
            self.assertIs(locked, coordinator.locked.return_value)
            store_factory.assert_called_once_with(
                root / "profile.json",
                backup=False,
            )
            coordinator.locked.assert_called_once_with(root)

    def test_save_load_list_rename_and_delete_profile(self):
        api = load_api_module()
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(api._aio_profiles, "AIO_PROFILE_DIR", Path(tmp)):
                saved = api._save_aio_profile(
                    "My: Profile",
                    {
                        "settings": {
                            "schema": "easyuse_anima_aio_generation_settings",
                            "model_patches": {
                                "kj": {
                                    "sage_stage_scope": {
                                        "first_pass": False,
                                        "highres": True,
                                        "detailer": True,
                                        "upscale": False,
                                    }
                                }
                            },
                            "future_section": {"kept": True},
                        }
                    },
                )
                self.assertEqual(saved["name"], "My_ Profile")
                self.assertEqual(saved["version"], 2)
                self.assertEqual(saved["revision"], 1)
                self.assertEqual(uuid.UUID(saved["profile_id"]).version, 4)
                self.assertTrue((Path(tmp) / "My_ Profile.json").is_file())
                profiles = api._list_aio_profiles()
                self.assertEqual([profile["name"] for profile in profiles], ["My_ Profile"])
                self.assertEqual(profiles[0]["profile_id"], saved["profile_id"])
                self.assertEqual(profiles[0]["revision"], 1)
                self.assertTrue(
                    api._load_aio_profile("my_ profile")["settings"]["future_section"]["kept"]
                )
                self.assertEqual(
                    api._load_aio_profile("my_ profile")["settings"]["model_patches"]["kj"][
                        "sage_stage_scope"
                    ],
                    {
                        "first_pass": False,
                        "highres": True,
                        "detailer": True,
                        "upscale": False,
                    },
                )

                renamed = api._rename_aio_profile(
                    "My_ Profile",
                    "Production",
                    **profile_tokens(saved),
                )
                self.assertEqual(renamed["name"], "Production")
                self.assertEqual(renamed["profile_id"], saved["profile_id"])
                self.assertEqual(renamed["revision"], 1)
                self.assertFalse((Path(tmp) / "My_ Profile.json").exists())
                self.assertTrue((Path(tmp) / "Production.json").is_file())
                self.assertEqual(
                    json.loads((Path(tmp) / "Production.json").read_text(encoding="utf-8")),
                    renamed,
                )

                deleted = api._delete_aio_profile(
                    "production",
                    **profile_tokens(renamed),
                )
                self.assertEqual(deleted["name"], "Production")
                self.assertEqual(deleted["profile_id"], saved["profile_id"])
                self.assertEqual(deleted["revision"], 1)
                self.assertEqual(api._list_aio_profiles(), [])

    def test_delete_removes_profile_primary_and_backup(self):
        api = load_api_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with patch.object(api._aio_profiles, "AIO_PROFILE_DIR", root):
                first = api._save_aio_profile("Delete Me", {"settings": {"value": "old"}})
                current = api._save_aio_profile(
                    "Delete Me",
                    {"settings": {"value": "current"}},
                    overwrite=True,
                    **profile_tokens(first),
                )
                primary = root / "Delete Me.json"
                backup = root / "Delete Me.json.bak"
                self.assertTrue(primary.is_file())
                self.assertTrue(backup.is_file())

                deleted = api._delete_aio_profile(
                    "delete me",
                    **profile_tokens(current),
                )

                self.assertEqual(deleted["name"], "Delete Me")
                self.assertFalse(primary.exists())
                self.assertFalse(backup.exists())

    def test_delete_backup_failure_preserves_profile_primary(self):
        api = load_api_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with patch.object(api._aio_profiles, "AIO_PROFILE_DIR", root):
                first = api._save_aio_profile("Preserved", {"settings": {"value": "old"}})
                current = api._save_aio_profile(
                    "Preserved",
                    {"settings": {"value": "current"}},
                    overwrite=True,
                    **profile_tokens(first),
                )
                primary = (root / "Preserved.json").resolve()
                backup = (root / "Preserved.json.bak").resolve()
                real_unlink = Path.unlink

                def fail_backup_unlink(path, *args, **kwargs):
                    if Path(path) == backup:
                        raise OSError("backup unlink failed")
                    return real_unlink(path, *args, **kwargs)

                with patch.object(Path, "unlink", autospec=True, side_effect=fail_backup_unlink):
                    with self.assertRaisesRegex(OSError, "backup unlink failed"):
                        api._delete_aio_profile(
                            "Preserved",
                            **profile_tokens(current),
                        )

                self.assertEqual(api._load_aio_profile("Preserved")["settings"]["value"], "current")
                self.assertTrue(primary.is_file())
                self.assertTrue(backup.is_file())

    def test_deleted_backup_cannot_recover_after_same_name_recreation(self):
        api = load_api_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with patch.object(api._aio_profiles, "AIO_PROFILE_DIR", root):
                first = api._save_aio_profile("Recreated", {"settings": {"value": "old"}})
                current = api._save_aio_profile(
                    "Recreated",
                    {"settings": {"value": "current"}},
                    overwrite=True,
                    **profile_tokens(first),
                )
                api._delete_aio_profile("Recreated", **profile_tokens(current))

                api._save_aio_profile("Recreated", {"settings": {"value": "recreated"}})
                primary = root / "Recreated.json"
                backup = root / "Recreated.json.bak"
                self.assertFalse(backup.exists())
                primary.write_text("{", encoding="utf-8")

                with self.assertRaisesRegex(ValueError, "Profile data is invalid"):
                    api._load_aio_profile("Recreated")

    def test_rename_removes_source_backup_before_old_name_recreation(self):
        api = load_api_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "Source.json"
            source_backup = root / "Source.json.bak"
            with patch.object(api._aio_profiles, "AIO_PROFILE_DIR", root):
                first = api._save_aio_profile("Source", {"settings": {"value": "old"}})
                current = api._save_aio_profile(
                    "Source",
                    {"settings": {"value": "current"}},
                    overwrite=True,
                    **profile_tokens(first),
                )
                renamed = api._rename_aio_profile(
                    "Source",
                    "Renamed",
                    **profile_tokens(current),
                )

                self.assertEqual(renamed["profile_id"], current["profile_id"])
                self.assertFalse(source_backup.exists())

                recreated = api._save_aio_profile(
                    "Source",
                    {"settings": {"value": "replacement"}},
                )
                source.write_text("{", encoding="utf-8")

                with self.assertRaises(api.InvalidProfileDataError):
                    api._load_aio_profile("Source")
                self.assertNotEqual(recreated["profile_id"], renamed["profile_id"])

    def test_overwrite_delete_race_allows_exactly_one_same_revision_success(self):
        api = load_api_module()
        profile_storage = sys.modules[api._aio_profiles.AtomicJsonStore.__module__]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile_path = (root / "Concurrent Delete.json").resolve()
            publish_ready = threading.Event()
            release_publish = threading.Event()
            delete_started = threading.Event()
            delete_done = threading.Event()
            errors: list[BaseException] = []
            deleted: list[dict] = []
            real_replace = profile_storage.os.replace

            with patch.object(api._aio_profiles, "AIO_PROFILE_DIR", root):
                original = api._save_aio_profile(
                    "Concurrent Delete",
                    {"settings": {"value": "old"}},
                )

                def block_primary_publish(source, target):
                    if Path(target) == profile_path:
                        publish_ready.set()
                        if not release_publish.wait(2):
                            raise AssertionError("profile publish was not released")
                    return real_replace(source, target)

                def overwrite_profile():
                    try:
                        api._save_aio_profile(
                            "Concurrent Delete",
                            {"settings": {"value": "new"}},
                            overwrite=True,
                            **profile_tokens(original),
                        )
                    except BaseException as exc:
                        errors.append(exc)

                def delete_profile():
                    delete_started.set()
                    try:
                        deleted.append(
                            api._delete_aio_profile(
                                "Concurrent Delete",
                                **profile_tokens(original),
                            )
                        )
                    except BaseException as exc:
                        errors.append(exc)
                    finally:
                        delete_done.set()

                with patch.object(profile_storage.os, "replace", side_effect=block_primary_publish):
                    writer = threading.Thread(target=overwrite_profile)
                    deleter = threading.Thread(target=delete_profile)
                    writer.start()
                    self.assertTrue(publish_ready.wait(2))
                    deleter.start()
                    self.assertTrue(delete_started.wait(2))
                    self.assertFalse(delete_done.wait(0.05))
                    release_publish.set()
                    writer.join(2)
                    deleter.join(2)

                self.assertFalse(writer.is_alive())
                self.assertFalse(deleter.is_alive())
                self.assertEqual(len(deleted), 0)
                self.assertEqual(len(errors), 1)
                self.assertEqual(errors[0].code, "profile_revision_conflict")
                current = api._load_aio_profile("Concurrent Delete")
                self.assertEqual(current["revision"], 2)
                self.assertEqual(current["settings"]["value"], "new")
                self.assertTrue(profile_path.exists())

    def test_delete_metadata_snapshot_and_delete_share_one_directory_lock(self):
        api = load_api_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            metadata_ready = threading.Event()
            release_metadata = threading.Event()
            overwrite_started = threading.Event()
            overwrite_done = threading.Event()
            errors: list[BaseException] = []
            deleted: list[dict] = []
            overwritten: list[dict] = []
            real_verify = api._aio_profiles.verify_profile_precondition

            with patch.object(api._aio_profiles, "AIO_PROFILE_DIR", root):
                original = api._save_aio_profile(
                    "Snapshot",
                    {"settings": {"value": "original"}},
                )

                def block_after_metadata_read(profile_kind, filename, document, **kwargs):
                    result = real_verify(profile_kind, filename, document, **kwargs)
                    if filename == "Snapshot":
                        metadata_ready.set()
                        if not release_metadata.wait(2):
                            raise AssertionError("delete metadata read was not released")
                    return result

                def delete_profile():
                    try:
                        deleted.append(
                            api._delete_aio_profile(
                                "Snapshot",
                                **profile_tokens(original),
                            )
                        )
                    except BaseException as exc:
                        errors.append(exc)

                def overwrite_profile():
                    overwrite_started.set()
                    try:
                        overwritten.append(
                            api._save_aio_profile(
                                "Snapshot",
                                {"settings": {"value": "replacement"}},
                                overwrite=True,
                                **profile_tokens(original),
                            )
                        )
                    except BaseException as exc:
                        errors.append(exc)
                    finally:
                        overwrite_done.set()

                with patch.object(
                    api._aio_profiles,
                    "verify_profile_precondition",
                    side_effect=block_after_metadata_read,
                ):
                    deleter = threading.Thread(target=delete_profile)
                    overwriter = threading.Thread(target=overwrite_profile)
                    deleter.start()
                    self.assertTrue(metadata_ready.wait(2))
                    overwriter.start()
                    self.assertTrue(overwrite_started.wait(2))
                    self.assertFalse(overwrite_done.wait(0.05))
                    release_metadata.set()
                    deleter.join(2)
                    overwriter.join(2)

                self.assertFalse(deleter.is_alive())
                self.assertFalse(overwriter.is_alive())
                self.assertEqual(len(errors), 1)
                self.assertIsInstance(errors[0], FileNotFoundError)
                self.assertEqual(deleted[0]["profile_id"], original["profile_id"])
                self.assertEqual(deleted[0]["revision"], original["revision"])
                self.assertEqual(overwritten, [])
                self.assertFalse((root / "Snapshot.json").exists())

    def test_same_name_rename_serializes_transform_and_publish_with_overwrite(self):
        api = load_api_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile_path = (root / "Same.json").resolve()
            transform_ready = threading.Event()
            release_transform = threading.Event()
            overwrite_started = threading.Event()
            errors: list[BaseException] = []
            renamed_profiles: list[dict] = []
            overwritten_profiles: list[dict] = []
            real_rename_payload = api._aio_profiles._rename_aio_profile_payload

            with patch.object(api._aio_profiles, "AIO_PROFILE_DIR", root):
                profile_path.write_text(
                    json.dumps({"version": 1, "settings": {"value": "legacy"}}),
                    encoding="utf-8",
                )
                legacy_id = api.legacy_profile_id(api.PROFILE_KIND_AIO, "Same")

                def block_after_transform(source_name, target_name, data):
                    result = real_rename_payload(source_name, target_name, data)
                    transform_ready.set()
                    if not release_transform.wait(2):
                        raise AssertionError("same-name transform was not released")
                    return result

                def rename_same_name():
                    try:
                        renamed_profiles.append(
                            api._rename_aio_profile(
                                "Same",
                                "Same",
                                profile_id=legacy_id,
                                revision=0,
                            )
                        )
                    except BaseException as exc:
                        errors.append(exc)

                def overwrite_profile():
                    overwrite_started.set()
                    try:
                        overwritten_profiles.append(
                            api._save_aio_profile(
                                "Same",
                                {"settings": {"value": "replacement"}},
                                overwrite=True,
                                profile_id=legacy_id,
                                revision=0,
                            )
                        )
                    except BaseException as exc:
                        errors.append(exc)

                with patch.object(
                    api._aio_profiles,
                    "_rename_aio_profile_payload",
                    side_effect=block_after_transform,
                ):
                    renamer = threading.Thread(target=rename_same_name)
                    overwriter = threading.Thread(target=overwrite_profile)
                    renamer.start()
                    self.assertTrue(transform_ready.wait(2))
                    directory_lock = api.PROFILE_MUTATION_COORDINATOR._lock(root)
                    lock_was_available = directory_lock.acquire(blocking=False)
                    if lock_was_available:
                        directory_lock.release()
                    overwriter.start()
                    self.assertTrue(overwrite_started.wait(2))
                    release_transform.set()
                    renamer.join(2)
                    overwriter.join(2)

                self.assertFalse(renamer.is_alive())
                self.assertFalse(overwriter.is_alive())
                self.assertFalse(lock_was_available)
                self.assertEqual(errors, [])
                self.assertEqual(renamed_profiles[0]["profile_id"], legacy_id)
                self.assertEqual(renamed_profiles[0]["revision"], 0)
                self.assertEqual(overwritten_profiles[0]["profile_id"], legacy_id)
                self.assertEqual(overwritten_profiles[0]["revision"], 1)
                self.assertEqual(
                    api._load_aio_profile("Same")["settings"]["value"],
                    "replacement",
                )

    def test_reader_observes_transformed_rename_before_joint_lock_release(self):
        api = load_api_module()
        profile_storage = sys.modules[api._aio_profiles.AtomicJsonStore.__module__]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = (root / "Source.json").resolve()
            target = (root / "Target.json").resolve()
            move_ready = threading.Event()
            release_move = threading.Event()
            transaction_done = threading.Event()
            release_api_return = threading.Event()
            reader_started = threading.Event()
            reader_done = threading.Event()
            errors: list[BaseException] = []
            renamed_profiles: list[dict] = []
            loaded_profiles: list[dict] = []
            listed_profiles: list[dict] = []
            real_replace = profile_storage.os.replace
            real_replace_from = api._aio_profiles.AtomicJsonStore.replace_from

            with patch.object(api._aio_profiles, "AIO_PROFILE_DIR", root):
                source.write_text(
                    json.dumps({"version": 1, "settings": {"value": "source"}}),
                    encoding="utf-8",
                )
                source_profile_id = api.legacy_profile_id(api.PROFILE_KIND_AIO, "Source")
                target_profile = api._save_aio_profile(
                    "Target",
                    {"settings": {"value": "target"}},
                )
                target_bytes = target.read_bytes()

                def block_after_source_move(current, destination):
                    result = real_replace(current, destination)
                    if Path(current) == source and Path(destination) == target:
                        move_ready.set()
                        if not release_move.wait(2):
                            raise AssertionError("profile move was not released")
                    return result

                def pause_after_transaction(store, source_store, *args, **kwargs):
                    result = real_replace_from(store, source_store, *args, **kwargs)
                    transaction_done.set()
                    if not release_api_return.wait(2):
                        raise AssertionError("rename return was not released")
                    return result

                def rename_profile():
                    try:
                        renamed_profiles.append(
                            api._rename_aio_profile(
                                "Source",
                                "Target",
                                overwrite=True,
                                profile_id=source_profile_id,
                                revision=0,
                                **profile_tokens(target_profile, prefix="target_"),
                            )
                        )
                    except BaseException as exc:
                        errors.append(exc)

                def load_target():
                    reader_started.set()
                    try:
                        loaded_profiles.append(api._load_aio_profile("Target"))
                        listed_profiles.append(
                            next(
                                profile
                                for profile in api._list_aio_profiles()
                                if profile["name"] == "Target"
                            )
                        )
                    except BaseException as exc:
                        errors.append(exc)
                    finally:
                        reader_done.set()

                with (
                    patch.object(
                        profile_storage.os,
                        "replace",
                        side_effect=block_after_source_move,
                    ),
                    patch.object(
                        api._aio_profiles.AtomicJsonStore,
                        "replace_from",
                        autospec=True,
                        side_effect=pause_after_transaction,
                    ),
                ):
                    renamer = threading.Thread(target=rename_profile)
                    reader = threading.Thread(target=load_target)
                    renamer.start()
                    self.assertTrue(move_ready.wait(2))
                    reader.start()
                    self.assertTrue(reader_started.wait(2))
                    self.assertFalse(reader_done.wait(0.05))
                    release_move.set()
                    self.assertTrue(transaction_done.wait(2))
                    self.assertTrue(reader_done.wait(2))
                    release_api_return.set()
                    renamer.join(2)
                    reader.join(2)

                self.assertFalse(renamer.is_alive())
                self.assertFalse(reader.is_alive())
                self.assertEqual(errors, [])
                self.assertEqual(loaded_profiles, renamed_profiles)
                self.assertEqual(loaded_profiles[0]["profile_id"], source_profile_id)
                self.assertEqual(loaded_profiles[0]["revision"], 0)
                self.assertEqual(loaded_profiles[0]["name"], "Target")
                self.assertEqual(listed_profiles[0]["profile_id"], source_profile_id)
                self.assertEqual(listed_profiles[0]["revision"], 0)
                self.assertEqual(
                    json.loads(target.read_text(encoding="utf-8")),
                    renamed_profiles[0],
                )
                self.assertFalse(source.exists())
                self.assertEqual((root / "Target.json.bak").read_bytes(), target_bytes)

    def test_delete_cannot_enter_rename_transaction_or_be_undone_after_return(self):
        api = load_api_module()
        profile_storage = sys.modules[api._aio_profiles.AtomicJsonStore.__module__]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = (root / "Source.json").resolve()
            target = (root / "Target.json").resolve()
            move_ready = threading.Event()
            release_move = threading.Event()
            transaction_done = threading.Event()
            release_api_return = threading.Event()
            delete_started = threading.Event()
            delete_done = threading.Event()
            errors: list[BaseException] = []
            deleted: list[dict] = []
            real_replace = profile_storage.os.replace
            real_replace_from = api._aio_profiles.AtomicJsonStore.replace_from

            with patch.object(api._aio_profiles, "AIO_PROFILE_DIR", root):
                source_profile = api._save_aio_profile(
                    "Source",
                    {"settings": {"value": "source"}},
                )
                target_profile = api._save_aio_profile(
                    "Target",
                    {"settings": {"value": "target"}},
                )

                def block_after_profile_move(current, destination):
                    result = real_replace(current, destination)
                    if Path(current) == source and Path(destination) == target:
                        move_ready.set()
                        if not release_move.wait(2):
                            raise AssertionError("profile move was not released")
                    return result

                def pause_after_transaction(store, source_store, *args, **kwargs):
                    result = real_replace_from(store, source_store, *args, **kwargs)
                    transaction_done.set()
                    if not release_api_return.wait(2):
                        raise AssertionError("rename return was not released")
                    return result

                def rename_profile():
                    try:
                        api._rename_aio_profile(
                            "Source",
                            "Target",
                            overwrite=True,
                            **profile_tokens(source_profile),
                            **profile_tokens(target_profile, prefix="target_"),
                        )
                    except BaseException as exc:
                        errors.append(exc)

                def delete_target():
                    delete_started.set()
                    try:
                        deleted.append(
                            api._delete_aio_profile(
                                "Target",
                                **profile_tokens(source_profile),
                            )
                        )
                    except BaseException as exc:
                        errors.append(exc)
                    finally:
                        delete_done.set()

                with (
                    patch.object(
                        profile_storage.os,
                        "replace",
                        side_effect=block_after_profile_move,
                    ),
                    patch.object(
                        api._aio_profiles.AtomicJsonStore,
                        "replace_from",
                        autospec=True,
                        side_effect=pause_after_transaction,
                    ),
                ):
                    renamer = threading.Thread(target=rename_profile)
                    deleter = threading.Thread(target=delete_target)
                    renamer.start()
                    self.assertTrue(move_ready.wait(2))
                    deleter.start()
                    self.assertTrue(delete_started.wait(2))
                    self.assertFalse(delete_done.wait(0.05))
                    release_move.set()
                    self.assertTrue(transaction_done.wait(2))
                    self.assertFalse(delete_done.wait(0.05))
                    release_api_return.set()
                    self.assertTrue(delete_done.wait(2))
                    renamer.join(2)
                    deleter.join(2)

                self.assertFalse(renamer.is_alive())
                self.assertFalse(deleter.is_alive())
                self.assertEqual(errors, [])
                self.assertEqual(deleted[0]["profile_id"], source_profile["profile_id"])
                self.assertEqual(deleted[0]["revision"], source_profile["revision"])
                self.assertFalse(source.exists())
                self.assertFalse(target.exists())
                self.assertFalse((root / "Target.json.bak").exists())

    def test_filename_identity_collisions_require_explicit_overwrite(self):
        api = load_api_module()
        collision_cases = (
            ("foo?bar", "foo*bar", "foo_bar"),
            (f"{'t' * 80}a", f"{'t' * 80}b", "t" * 80),
            ("Portrait", "portrait", "Portrait"),
            ("Windows Name", "Windows Name. ", "Windows Name"),
        )

        for original_name, colliding_name, filename in collision_cases:
            with self.subTest(original_name=original_name, colliding_name=colliding_name):
                with tempfile.TemporaryDirectory() as tmp:
                    with patch.object(api._aio_profiles, "AIO_PROFILE_DIR", Path(tmp)):
                        created = api._save_aio_profile(
                            original_name,
                            {"settings": {"sampler": {"steps": 30}}},
                        )
                        for overwrite_kwargs in ({}, {"overwrite": False}):
                            with self.subTest(overwrite_kwargs=overwrite_kwargs):
                                with self.assertRaisesRegex(FileExistsError, "Profile already exists"):
                                    api._save_aio_profile(
                                        colliding_name,
                                        {"settings": {"sampler": {"steps": 10}}},
                                        **overwrite_kwargs,
                                    )

                        preserved = api._load_aio_profile(colliding_name)
                        self.assertEqual(preserved["settings"]["sampler"]["steps"], 30)
                        self.assertEqual(preserved["name"], filename)

                        overwritten = api._save_aio_profile(
                            colliding_name,
                            {"settings": {"sampler": {"steps": 10}}},
                            overwrite=True,
                            **profile_tokens(created),
                        )
                        self.assertEqual(overwritten["name"], filename)
                        self.assertEqual(overwritten["settings"]["sampler"]["steps"], 10)
                        self.assertEqual(
                            api._load_aio_profile(original_name)["settings"]["sampler"]["steps"],
                            10,
                        )
                        self.assertEqual(
                            [path.name for path in Path(tmp).glob("*.json")],
                            [f"{filename}.json"],
                        )

    def test_save_delete_and_rename_require_strict_source_preconditions(self):
        api = load_api_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with patch.object(api._aio_profiles, "AIO_PROFILE_DIR", root):
                created = api._save_aio_profile("Strict", {"settings": {}})
                operations = (
                    lambda: api._save_aio_profile(
                        "Strict",
                        {"settings": {}},
                        overwrite=True,
                    ),
                    lambda: api._delete_aio_profile("Strict"),
                    lambda: api._rename_aio_profile("Strict", "Renamed"),
                )

                for operation in operations:
                    with self.assertRaises(api.ProfileMutationError) as required:
                        operation()
                    self.assertEqual(
                        required.exception.code,
                        "profile_precondition_required",
                    )

                (root / "Strict.json").unlink()
                with self.assertRaises(FileNotFoundError):
                    api._save_aio_profile(
                        "Strict",
                        {"settings": {}},
                        overwrite=True,
                        **profile_tokens(created),
                    )

    def test_delete_and_rename_mismatches_preserve_bytes_backups_mtime_and_temps(self):
        api = load_api_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with patch.object(api._aio_profiles, "AIO_PROFILE_DIR", root):
                source_v1 = api._save_aio_profile(
                    "Source",
                    {"settings": {"value": "source-v1"}},
                )
                source = api._save_aio_profile(
                    "Source",
                    {"settings": {"value": "source-v2"}},
                    overwrite=True,
                    **profile_tokens(source_v1),
                )
                target_v1 = api._save_aio_profile(
                    "Target",
                    {"settings": {"value": "target-v1"}},
                )
                target = api._save_aio_profile(
                    "Target",
                    {"settings": {"value": "target-v2"}},
                    overwrite=True,
                    **profile_tokens(target_v1),
                )
                wrong_id = "00000000-0000-4000-8000-000000000000"
                cases = (
                    (
                        "delete identity",
                        lambda: api._delete_aio_profile(
                            "Source",
                            profile_id=wrong_id,
                            revision=source["revision"] - 1,
                        ),
                        "profile_identity_mismatch",
                    ),
                    (
                        "delete revision",
                        lambda: api._delete_aio_profile(
                            "Source",
                            profile_id=source["profile_id"],
                            revision=source["revision"] - 1,
                        ),
                        "profile_revision_conflict",
                    ),
                    (
                        "rename source identity",
                        lambda: api._rename_aio_profile(
                            "Source",
                            "Target",
                            overwrite=True,
                            profile_id=wrong_id,
                            revision=source["revision"] - 1,
                            **profile_tokens(target, prefix="target_"),
                        ),
                        "profile_identity_mismatch",
                    ),
                    (
                        "rename source revision",
                        lambda: api._rename_aio_profile(
                            "Source",
                            "Target",
                            overwrite=True,
                            profile_id=source["profile_id"],
                            revision=source["revision"] - 1,
                            **profile_tokens(target, prefix="target_"),
                        ),
                        "profile_revision_conflict",
                    ),
                    (
                        "rename target identity",
                        lambda: api._rename_aio_profile(
                            "Source",
                            "Target",
                            overwrite=True,
                            **profile_tokens(source),
                            target_profile_id=wrong_id,
                            target_revision=target["revision"] - 1,
                        ),
                        "profile_identity_mismatch",
                    ),
                    (
                        "rename target revision",
                        lambda: api._rename_aio_profile(
                            "Source",
                            "Target",
                            overwrite=True,
                            **profile_tokens(source),
                            target_profile_id=target["profile_id"],
                            target_revision=target["revision"] - 1,
                        ),
                        "profile_revision_conflict",
                    ),
                )

                for label, operation, code in cases:
                    with self.subTest(label=label):
                        before = directory_snapshot(root)
                        with self.assertRaises(api.ProfileMutationError) as mismatch:
                            operation()
                        self.assertEqual(mismatch.exception.code, code)
                        self.assertEqual(directory_snapshot(root), before)

    def test_rename_target_rules_preserve_profile_exists_and_detect_disappearance(self):
        api = load_api_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with patch.object(api._aio_profiles, "AIO_PROFILE_DIR", root):
                source = api._save_aio_profile("Source", {"settings": {}})
                target = api._save_aio_profile("Target", {"settings": {}})

                with self.assertRaises(FileExistsError):
                    api._rename_aio_profile(
                        "Source",
                        "Target",
                        **profile_tokens(source),
                    )

                with self.assertRaises(api.ProfileMutationError) as required:
                    api._rename_aio_profile(
                        "Source",
                        "Target",
                        overwrite=True,
                        **profile_tokens(source),
                    )
                self.assertEqual(
                    required.exception.code,
                    "profile_precondition_required",
                )

                (root / "Target.json").unlink()
                before = directory_snapshot(root)
                with self.assertRaises(api.ProfileMutationError) as disappeared:
                    api._rename_aio_profile(
                        "Source",
                        "Target",
                        overwrite=True,
                        **profile_tokens(source),
                        **profile_tokens(target, prefix="target_"),
                    )
                self.assertEqual(
                    disappeared.exception.code,
                    "profile_revision_conflict",
                )
                self.assertEqual(disappeared.exception.details, {"profile": "target"})
                self.assertEqual(directory_snapshot(root), before)

    def test_same_name_v2_rename_verifies_source_without_unnecessary_write(self):
        api = load_api_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with patch.object(api._aio_profiles, "AIO_PROFILE_DIR", root):
                source = api._save_aio_profile(
                    "Same",
                    {"settings": {"value": "stable"}},
                )
                before = directory_snapshot(root)

                renamed = api._rename_aio_profile(
                    "same. ",
                    "SAME",
                    **profile_tokens(source),
                )

                self.assertEqual(renamed, source)
                self.assertEqual(directory_snapshot(root), before)

    def test_windows_reserved_profile_names_are_rejected(self):
        api = load_api_module()
        for name in ("CON", "con.txt", "LPT9", "COM¹.txt", "aux."):
            with self.subTest(name=name), self.assertRaisesRegex(ValueError, "reserved on Windows"):
                api._sanitize_aio_profile_name(name)

    def test_profile_paths_remain_within_the_configured_root(self):
        api = load_api_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            for name in ("../outside", r"C:\outside", r"\\server\share\outside"):
                with self.subTest(name=name):
                    self.assertEqual(api._aio_profile_path(name, root).parent, root)

    def test_builtin_names_and_invalid_payloads_are_rejected(self):
        api = load_api_module()
        for name in ("Normal", "터보", "최적화", "Custom", "커스텀"):
            with self.subTest(name=name), self.assertRaises(ValueError):
                api._sanitize_aio_profile_name(name)
        with self.assertRaises(ValueError):
            api._normalize_aio_profile_payload("custom", {"settings": []})

    def test_invalid_saved_json_is_reported_as_profile_error(self):
        api = load_api_module()
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(api._aio_profiles, "AIO_PROFILE_DIR", Path(tmp)):
                broken = Path(tmp) / "Broken.json"
                broken.write_text("{", encoding="utf-8")
                before = (broken.read_bytes(), broken.stat().st_mtime_ns)

                listed = api._list_aio_profiles()
                self.assertEqual(listed[0]["name"], "Broken")
                self.assertEqual(listed[0]["revision"], 0)
                self.assertEqual((broken.read_bytes(), broken.stat().st_mtime_ns), before)
                with self.assertRaisesRegex(ValueError, "Profile data is invalid"):
                    api._load_aio_profile("Broken")

    def test_incomplete_v2_delete_is_rejected_without_mutating_the_file(self):
        api = load_api_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = root / "Incomplete.json"
            profile.write_text(
                json.dumps(
                    {
                        "version": 2,
                        "name": "Incomplete",
                        "settings": {"value": "preserved"},
                    }
                ),
                encoding="utf-8",
            )
            before = profile.read_bytes()

            with patch.object(api._aio_profiles, "AIO_PROFILE_DIR", root):
                with self.assertRaises(api.InvalidProfileDataError):
                    api._delete_aio_profile(
                        "Incomplete",
                        profile_id="00000000-0000-4000-8000-000000000000",
                        revision=0,
                    )

            self.assertEqual(profile.read_bytes(), before)

    def test_empty_profile_preserves_legacy_payload_validation_contract(self):
        api = load_api_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with patch.object(api._aio_profiles, "AIO_PROFILE_DIR", root):
                (root / "Empty.json").write_text("", encoding="utf-8")

                with self.assertRaisesRegex(ValueError, "Profile settings must be an object"):
                    api._load_aio_profile("Empty")

    def test_legacy_near_limit_profile_remains_loadable_after_additive_view(self):
        api = load_api_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            stored = {
                "version": 1,
                "name": "Near Limit",
                "settings": {"blob": "x" * 32},
            }
            legacy_payload = api._normalize_aio_profile_payload("Near Limit", stored)
            legacy_size = len(
                json.dumps(legacy_payload, ensure_ascii=False, indent=2).encode("utf-8")
            )
            (root / "Near Limit.json").write_text(
                json.dumps(stored, ensure_ascii=False),
                encoding="utf-8",
            )

            with (
                patch.object(api._aio_profiles, "AIO_PROFILE_DIR", root),
                patch.object(api._aio_profiles, "MAX_AIO_PROFILE_BYTES", legacy_size),
            ):
                loaded = api._load_aio_profile("Near Limit")

            additive_size = len(
                json.dumps(loaded, ensure_ascii=False, indent=2).encode("utf-8")
            )
            self.assertGreater(additive_size, legacy_size)
            self.assertEqual(loaded["settings"]["blob"], "x" * 32)
            self.assertEqual(loaded["revision"], 0)

    def test_legacy_list_and_load_are_pure_and_overwrite_promotes_to_v2(self):
        api = load_api_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            primary = root / "Legacy.json"
            backup = root / "Legacy.json.bak"
            primary.write_text(
                json.dumps(
                    {
                        "version": 1,
                        "name": "Legacy",
                        "settings": {"future_section": {"kept": True}},
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            backup.write_text('{"sentinel":true}', encoding="utf-8")
            primary_before = (primary.read_bytes(), primary.stat().st_mtime_ns)
            backup_before = (backup.read_bytes(), backup.stat().st_mtime_ns)

            with patch.object(api._aio_profiles, "AIO_PROFILE_DIR", root):
                listed = api._list_aio_profiles()[0]
                loaded = api._load_aio_profile("legacy")

                self.assertEqual(listed["profile_id"], loaded["profile_id"])
                self.assertEqual(listed["revision"], 0)
                self.assertTrue(loaded["settings"]["future_section"]["kept"])
                self.assertEqual(
                    (primary.read_bytes(), primary.stat().st_mtime_ns),
                    primary_before,
                )
                self.assertEqual(
                    (backup.read_bytes(), backup.stat().st_mtime_ns),
                    backup_before,
                )

                promoted = api._save_aio_profile(
                    "Legacy",
                    {"settings": {"future_section": {"kept": "updated"}}},
                    overwrite=True,
                    **profile_tokens(listed),
                )

            self.assertEqual(promoted["profile_id"], listed["profile_id"])
            self.assertEqual(promoted["revision"], 1)
            self.assertEqual(json.loads(primary.read_text(encoding="utf-8")), promoted)

    def test_v2_overwrite_preserves_id_and_advances_matching_revision(self):
        api = load_api_module()
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(api._aio_profiles, "AIO_PROFILE_DIR", Path(tmp)):
                created = api._save_aio_profile("Updated", {"settings": {"value": 1}})
                updated = api._save_aio_profile(
                    "Updated",
                    {"settings": {"value": 2}},
                    overwrite=True,
                    **profile_tokens(created),
                )

        self.assertEqual(updated["profile_id"], created["profile_id"])
        self.assertEqual(updated["revision"], 2)
        self.assertEqual(updated["settings"]["value"], 2)

    def test_invalid_primary_recovers_last_valid_backup(self):
        api = load_api_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with patch.object(api._aio_profiles, "AIO_PROFILE_DIR", root):
                first = api._save_aio_profile(
                    "Recoverable",
                    {"settings": {"value": "first"}},
                )
                api._save_aio_profile(
                    "Recoverable",
                    {"settings": {"value": "second"}},
                    overwrite=True,
                    **profile_tokens(first),
                )
                (root / "Recoverable.json").write_text("{", encoding="utf-8")

                recovered = api._load_aio_profile("Recoverable")

        self.assertEqual(recovered["name"], "Recoverable")
        self.assertEqual(recovered["settings"]["value"], "first")

    def test_concurrent_profile_publish_never_exposes_partial_json(self):
        api = load_api_module()
        profile_storage = sys.modules[api._aio_profiles.AtomicJsonStore.__module__]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile_path = (root / "Concurrent.json").resolve()
            publish_ready = threading.Event()
            release_publish = threading.Event()
            errors: list[BaseException] = []
            real_replace = profile_storage.os.replace

            with patch.object(api._aio_profiles, "AIO_PROFILE_DIR", root):
                original = api._save_aio_profile(
                    "Concurrent",
                    {"settings": {"value": "old"}},
                )

                def block_primary_publish(source, target):
                    if Path(target) == profile_path:
                        publish_ready.set()
                        if not release_publish.wait(2):
                            raise AssertionError("profile publish was not released")
                    return real_replace(source, target)

                def overwrite_profile():
                    try:
                        api._save_aio_profile(
                            "Concurrent",
                            {"settings": {"value": "new", "items": list(range(1000))}},
                            overwrite=True,
                            **profile_tokens(original),
                        )
                    except BaseException as exc:
                        errors.append(exc)

                with patch.object(profile_storage.os, "replace", side_effect=block_primary_publish):
                    writer = threading.Thread(target=overwrite_profile)
                    writer.start()
                    self.assertTrue(publish_ready.wait(2))
                    visible = json.loads(profile_path.read_text(encoding="utf-8"))
                    self.assertEqual(visible["settings"]["value"], "old")
                    release_publish.set()
                    writer.join(2)

                self.assertFalse(writer.is_alive())
                self.assertEqual(errors, [])
                self.assertEqual(api._load_aio_profile("Concurrent")["settings"]["value"], "new")

    def test_rename_rejects_invalid_source_schema_before_publish(self):
        api = load_api_module()
        invalid_payloads = (
            ("array", [], "Profile data is invalid"),
            ("empty object", {}, "Profile settings must be an object"),
            (
                "non-object settings",
                {"settings": []},
                "Profile settings must be an object",
            ),
        )

        for label, invalid_payload, message in invalid_payloads:
            with self.subTest(label=label), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                source = root / "Source.json"
                target = root / "Target.json"
                source.write_text(
                    json.dumps(invalid_payload, ensure_ascii=False),
                    encoding="utf-8",
                )
                source_bytes = source.read_bytes()

                with patch.object(api._aio_profiles, "AIO_PROFILE_DIR", root):
                    with self.assertRaisesRegex(api.InvalidProfileDataError, message):
                        api._rename_aio_profile(
                            "Source",
                            "Target",
                            profile_id=api.legacy_profile_id(
                                api.PROFILE_KIND_AIO,
                                "Source",
                            ),
                            revision=0,
                        )

                self.assertEqual(source.read_bytes(), source_bytes)
                self.assertFalse(target.exists())
                self.assertFalse((root / "Target.json.bak").exists())

    def test_rename_invalid_schema_preserves_overwrite_target_and_existing_backup(self):
        api = load_api_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with patch.object(api._aio_profiles, "AIO_PROFILE_DIR", root):
                first_target = api._save_aio_profile(
                    "Target",
                    {"settings": {"value": "old target"}},
                )
                target_profile = api._save_aio_profile(
                    "Target",
                    {"settings": {"value": "current target"}},
                    overwrite=True,
                    **profile_tokens(first_target),
                )
                source = root / "Source.json"
                target = root / "Target.json"
                backup = root / "Target.json.bak"
                source.write_text('{"settings": []}', encoding="utf-8")
                source_bytes = source.read_bytes()
                target_bytes = target.read_bytes()
                backup_bytes = backup.read_bytes()

                with self.assertRaisesRegex(ValueError, "Profile settings must be an object"):
                    api._rename_aio_profile(
                        "Source",
                        "Target",
                        overwrite=True,
                        profile_id=api.legacy_profile_id(api.PROFILE_KIND_AIO, "Source"),
                        revision=0,
                        **profile_tokens(target_profile, prefix="target_"),
                    )

                self.assertEqual(source.read_bytes(), source_bytes)
                self.assertEqual(target.read_bytes(), target_bytes)
                self.assertEqual(backup.read_bytes(), backup_bytes)
                self.assertEqual(
                    [path for path in root.iterdir() if path.name.endswith(".tmp")],
                    [],
                )

    def test_rename_overwrite_atomically_moves_source_and_keeps_target_backup(self):
        api = load_api_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with patch.object(api._aio_profiles, "AIO_PROFILE_DIR", root):
                source_profile = api._save_aio_profile(
                    "Source",
                    {"settings": {"value": "source"}},
                )
                target_profile = api._save_aio_profile(
                    "Target",
                    {"settings": {"value": "target"}},
                )

                renamed = api._rename_aio_profile(
                    "Source",
                    "Target",
                    overwrite=True,
                    **profile_tokens(source_profile),
                    **profile_tokens(target_profile, prefix="target_"),
                )

                backup = json.loads((root / "Target.json.bak").read_text(encoding="utf-8"))
                self.assertEqual(renamed["name"], "Target")
                self.assertEqual(renamed["settings"]["value"], "source")
                self.assertEqual(backup["settings"]["value"], "target")
                self.assertFalse((root / "Source.json").exists())

    def test_legacy_rename_writes_v2_source_identity_and_discards_target_id(self):
        api = load_api_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "Source.json"
            with patch.object(api._aio_profiles, "AIO_PROFILE_DIR", root):
                source.write_text(
                    json.dumps(
                        {
                            "version": 1,
                            "name": "Source",
                            "settings": {"future_section": {"kept": True}},
                        }
                    ),
                    encoding="utf-8",
                )
                source_id = api.legacy_profile_id(api.PROFILE_KIND_AIO, "Source")
                target = api._save_aio_profile("Target", {"settings": {"value": "target"}})

                renamed = api._rename_aio_profile(
                    "Source",
                    "Target",
                    overwrite=True,
                    profile_id=source_id,
                    revision=0,
                    target_profile_id=target["profile_id"],
                    target_revision=target["revision"],
                )

            stored = json.loads((root / "Target.json").read_text(encoding="utf-8"))
            target_backup = json.loads(
                (root / "Target.json.bak").read_text(encoding="utf-8")
            )
            self.assertEqual(renamed["version"], 2)
            self.assertEqual(renamed["profile_id"], source_id)
            self.assertNotEqual(renamed["profile_id"], target["profile_id"])
            self.assertEqual(renamed["revision"], 0)
            self.assertEqual(renamed["name"], "Target")
            self.assertTrue(renamed["settings"]["future_section"]["kept"])
            self.assertEqual(stored, renamed)
            self.assertEqual(target_backup["profile_id"], target["profile_id"])

    def test_rename_move_failure_preserves_source_target_and_backup(self):
        api = load_api_module()
        profile_storage = sys.modules[api._aio_profiles.AtomicJsonStore.__module__]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = (root / "Source.json").resolve()
            target = (root / "Target.json").resolve()
            real_replace = profile_storage.os.replace

            with patch.object(api._aio_profiles, "AIO_PROFILE_DIR", root):
                first_source = api._save_aio_profile(
                    "Source",
                    {"settings": {"value": "old source"}},
                )
                source_profile = api._save_aio_profile(
                    "Source",
                    {"settings": {"value": "source"}},
                    overwrite=True,
                    **profile_tokens(first_source),
                )
                target_profile = api._save_aio_profile(
                    "Target",
                    {"settings": {"value": "target"}},
                )
                source_backup_bytes = (root / "Source.json.bak").read_bytes()

                def fail_move(current, destination):
                    if Path(current) == source and Path(destination) == target:
                        raise OSError("rename move failed")
                    return real_replace(current, destination)

                with patch.object(profile_storage.os, "replace", side_effect=fail_move):
                    with self.assertRaisesRegex(OSError, "rename move failed"):
                        api._rename_aio_profile(
                            "Source",
                            "Target",
                            overwrite=True,
                            **profile_tokens(source_profile),
                            **profile_tokens(target_profile, prefix="target_"),
                        )

                self.assertEqual(api._load_aio_profile("Source")["settings"]["value"], "source")
                self.assertEqual(api._load_aio_profile("Target")["settings"]["value"], "target")
                self.assertEqual(
                    (root / "Source.json.bak").read_bytes(),
                    source_backup_bytes,
                )
                self.assertFalse((root / "Target.json.bak").exists())
                self.assertEqual([path for path in root.iterdir() if path.name.endswith(".tmp")], [])

    def test_rename_target_backup_failure_preserves_source_and_target(self):
        api = load_api_module()
        profile_storage = sys.modules[api._aio_profiles.AtomicJsonStore.__module__]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            backup_path = (root / "Target.json.bak").resolve()
            real_replace = profile_storage.os.replace

            with patch.object(api._aio_profiles, "AIO_PROFILE_DIR", root):
                source_profile = api._save_aio_profile(
                    "Source",
                    {"settings": {"value": "source"}},
                )
                target_profile = api._save_aio_profile(
                    "Target",
                    {"settings": {"value": "target"}},
                )

                def fail_backup(current, destination):
                    if Path(destination) == backup_path:
                        raise OSError("target backup failed")
                    return real_replace(current, destination)

                with patch.object(profile_storage.os, "replace", side_effect=fail_backup):
                    with self.assertRaisesRegex(OSError, "target backup failed"):
                        api._rename_aio_profile(
                            "Source",
                            "Target",
                            overwrite=True,
                            **profile_tokens(source_profile),
                            **profile_tokens(target_profile, prefix="target_"),
                        )

                self.assertEqual(api._load_aio_profile("Source")["settings"]["value"], "source")
                self.assertEqual(api._load_aio_profile("Target")["settings"]["value"], "target")
                self.assertEqual([path for path in root.iterdir() if path.name.endswith(".tmp")], [])

    def test_rename_does_not_depend_on_a_separate_unlink(self):
        api = load_api_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with patch.object(api._aio_profiles, "AIO_PROFILE_DIR", root):
                source_profile = api._save_aio_profile(
                    "Source",
                    {"settings": {"value": "source"}},
                )

                with patch.object(Path, "unlink", side_effect=OSError("unlink failed")):
                    renamed = api._rename_aio_profile(
                        "Source",
                        "Renamed",
                        **profile_tokens(source_profile),
                    )

                self.assertEqual(renamed["name"], "Renamed")
                self.assertFalse((root / "Source.json").exists())
                self.assertTrue((root / "Renamed.json").is_file())


class AIOProfileApiRouteTests(unittest.TestCase):
    ENDPOINTS = (
        (
            "/easyuse_anima/aio_profiles/save",
            {"name": "Saved", "settings": {}},
            "_save_aio_profile",
        ),
        (
            "/easyuse_anima/aio_profiles/rename",
            {"old_name": "Old", "new_name": "Renamed"},
            "_rename_aio_profile",
        ),
    )

    def test_profile_overwrite_accepts_json_booleans_and_defaults_false(self):
        api, routes = load_api_routes()
        overwrite_cases = (({}, False), ({"overwrite": False}, False), ({"overwrite": True}, True))

        for path, base_payload, function_name in self.ENDPOINTS:
            handler = routes.handlers[path]
            for overwrite_payload, expected in overwrite_cases:
                with self.subTest(path=path, overwrite=overwrite_payload):
                    with patch.object(
                        api,
                        function_name,
                        return_value={"name": "Saved"},
                    ) as operation:
                        response = asyncio.run(
                            handler(JsonRequest({**base_payload, **overwrite_payload}))
                        )

                    self.assertEqual(response["status"], 200)
                    self.assertIs(operation.call_args.kwargs["overwrite"], expected)

    def test_profile_overwrite_rejects_non_boolean_json_scalars_and_containers(self):
        api, routes = load_api_routes()
        invalid_values = ("false", "true", 0, 1, "", None, [], {})

        for path, base_payload, function_name in self.ENDPOINTS:
            handler = routes.handlers[path]
            for overwrite in invalid_values:
                with self.subTest(path=path, overwrite=overwrite):
                    with patch.object(api, function_name) as operation:
                        response = asyncio.run(
                            handler(JsonRequest({**base_payload, "overwrite": overwrite}))
                        )

                    self.assertEqual(response["status"], 422)
                    self.assertEqual(response["payload"]["code"], "invalid_request")
                    self.assertEqual(
                        response["payload"]["message"],
                        "overwrite must be a JSON boolean.",
                    )
                    operation.assert_not_called()

    def test_optional_concurrency_tokens_are_typed_and_forwarded_without_enforcement(self):
        api, routes = load_api_routes()
        source_id = "12345678-1234-4234-9234-1234567890AB"
        target_id = "22345678-1234-4234-9234-1234567890AB"
        cases = (
            (
                "/easyuse_anima/aio_profiles/save",
                {
                    "name": "Saved",
                    "settings": {},
                    "profile_id": source_id,
                    "revision": 7,
                },
                "_save_aio_profile",
                {
                    "profile_id": source_id.lower(),
                    "revision": 7,
                },
            ),
            (
                "/easyuse_anima/aio_profiles/delete",
                {"name": "Saved", "profile_id": source_id, "revision": 7},
                "_delete_aio_profile",
                {
                    "profile_id": source_id.lower(),
                    "revision": 7,
                },
            ),
            (
                "/easyuse_anima/aio_profiles/rename",
                {
                    "old_name": "Old",
                    "new_name": "Renamed",
                    "profile_id": source_id,
                    "revision": 7,
                    "target_profile_id": target_id,
                    "target_revision": 11,
                },
                "_rename_aio_profile",
                {
                    "profile_id": source_id.lower(),
                    "revision": 7,
                    "target_profile_id": target_id.lower(),
                    "target_revision": 11,
                },
            ),
        )

        for path, payload, operation_name, expected in cases:
            with self.subTest(path=path), patch.object(
                api,
                operation_name,
                return_value={"name": "Saved"},
            ) as operation:
                response = asyncio.run(routes.handlers[path](JsonRequest(payload)))

                self.assertEqual(response["status"], 200)
                for field, value in expected.items():
                    self.assertEqual(operation.call_args.kwargs[field], value)

    def test_optional_concurrency_tokens_reject_invalid_json_types(self):
        api, routes = load_api_routes()
        cases = (
            (
                "/easyuse_anima/aio_profiles/save",
                {"name": "Saved", "settings": {}, "profile_id": "not-a-uuid"},
                "_save_aio_profile",
                "profile_id",
            ),
            (
                "/easyuse_anima/aio_profiles/delete",
                {"name": "Saved", "revision": True},
                "_delete_aio_profile",
                "revision",
            ),
            (
                "/easyuse_anima/aio_profiles/rename",
                {
                    "old_name": "Old",
                    "new_name": "Renamed",
                    "target_profile_id": 3,
                },
                "_rename_aio_profile",
                "target_profile_id",
            ),
            (
                "/easyuse_anima/aio_profiles/rename",
                {
                    "old_name": "Old",
                    "new_name": "Renamed",
                    "target_revision": -1,
                },
                "_rename_aio_profile",
                "target_revision",
            ),
        )

        for path, payload, operation_name, field in cases:
            with self.subTest(path=path, field=field), patch.object(
                api,
                operation_name,
            ) as operation:
                response = asyncio.run(routes.handlers[path](JsonRequest(payload)))

                self.assertEqual(response["status"], 422)
                self.assertEqual(response["payload"]["code"], "invalid_request")
                self.assertEqual(response["payload"]["details"], {"field": field})
                operation.assert_not_called()

    def test_profile_conflicts_use_existing_error_json_shape_with_409_status(self):
        api, routes = load_api_routes()

        for path, base_payload, function_name in self.ENDPOINTS:
            handler = routes.handlers[path]
            with self.subTest(path=path):
                with patch.object(
                    api,
                    function_name,
                    side_effect=FileExistsError("Profile already exists"),
                ):
                    response = asyncio.run(handler(JsonRequest(base_payload)))

                self.assertEqual(response["status"], 409)
                self.assertEqual(
                    response["payload"],
                    {
                        "status": "error",
                        "code": "profile_exists",
                        "message": "Profile already exists",
                    },
                )

    def test_delete_missing_profile_preserves_404_response_contract(self):
        api, routes = load_api_routes()
        handler = routes.handlers["/easyuse_anima/aio_profiles/delete"]

        with patch.object(
            api,
            "_delete_aio_profile",
            side_effect=FileNotFoundError("Profile not found"),
        ):
            response = asyncio.run(handler(JsonRequest({"name": "Missing"})))

        self.assertEqual(response["status"], 404)
        self.assertEqual(
            response["payload"],
            {
                "status": "error",
                "code": "profile_not_found",
                "message": "Profile not found",
            },
        )

    def test_actual_routes_enforce_source_and_target_cas_taxonomy(self):
        api, routes = load_api_routes()
        save_handler = routes.handlers["/easyuse_anima/aio_profiles/save"]
        delete_handler = routes.handlers["/easyuse_anima/aio_profiles/delete"]
        rename_handler = routes.handlers["/easyuse_anima/aio_profiles/rename"]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with patch.object(api._aio_profiles, "AIO_PROFILE_DIR", root):
                source = asyncio.run(
                    save_handler(JsonRequest({"name": "Source", "settings": {}}))
                )["payload"]["profile"]
                target = asyncio.run(
                    save_handler(JsonRequest({"name": "Target", "settings": {}}))
                )["payload"]["profile"]

                for handler, payload in (
                    (
                        save_handler,
                        {"name": "Source", "settings": {}, "overwrite": True},
                    ),
                    (delete_handler, {"name": "Source"}),
                    (
                        rename_handler,
                        {"old_name": "Source", "new_name": "Renamed"},
                    ),
                ):
                    with self.subTest(payload=payload):
                        response = asyncio.run(handler(JsonRequest(payload)))
                        self.assertEqual(response["status"], 428)
                        self.assertEqual(
                            response["payload"]["code"],
                            "profile_precondition_required",
                        )

                exists = asyncio.run(
                    rename_handler(
                        JsonRequest(
                            {
                                "old_name": "Source",
                                "new_name": "Target",
                                **profile_tokens(source),
                            }
                        )
                    )
                )
                self.assertEqual(exists["status"], 409)
                self.assertEqual(exists["payload"]["code"], "profile_exists")

                target_required = asyncio.run(
                    rename_handler(
                        JsonRequest(
                            {
                                "old_name": "Source",
                                "new_name": "Target",
                                "overwrite": True,
                                **profile_tokens(source),
                            }
                        )
                    )
                )
                self.assertEqual(target_required["status"], 428)
                self.assertEqual(
                    target_required["payload"]["code"],
                    "profile_precondition_required",
                )
                self.assertEqual(
                    target_required["payload"]["details"]["profile"],
                    "target",
                )

                (root / "Target.json").unlink()
                disappeared = asyncio.run(
                    rename_handler(
                        JsonRequest(
                            {
                                "old_name": "Source",
                                "new_name": "Target",
                                "overwrite": True,
                                **profile_tokens(source),
                                **profile_tokens(target, prefix="target_"),
                            }
                        )
                    )
                )
                self.assertEqual(disappeared["status"], 409)
                self.assertEqual(
                    disappeared["payload"]["code"],
                    "profile_revision_conflict",
                )

                identity = asyncio.run(
                    delete_handler(
                        JsonRequest(
                            {
                                "name": "Source",
                                "profile_id": "00000000-0000-4000-8000-000000000000",
                                "revision": source["revision"] - 1,
                            }
                        )
                    )
                )
                self.assertEqual(identity["status"], 409)
                self.assertEqual(
                    identity["payload"]["code"],
                    "profile_identity_mismatch",
                )

                revision = asyncio.run(
                    delete_handler(
                        JsonRequest(
                            {
                                "name": "Source",
                                "profile_id": source["profile_id"],
                                "revision": source["revision"] - 1,
                            }
                        )
                    )
                )
                self.assertEqual(revision["status"], 409)
                self.assertEqual(
                    revision["payload"]["code"],
                    "profile_revision_conflict",
                )


class AIOBuiltinProfileTests(unittest.TestCase):
    def test_builtin_profiles_follow_normal_turbo_and_optimized_contract(self):
        node_bin = shutil.which("node")
        if not node_bin:
            self.skipTest("node executable is not available")

        runner = textwrap.dedent(
            r"""
            const assert = require("assert");
            const fs = require("fs");
            let source = fs.readFileSync(process.argv[1], "utf8");
            source = source.replaceAll("export function ", "function ");
            source += "\nglobalThis.__aioPresetExports = {"
              + " aioBuiltinProfileIdForSettings,"
              + " aioBuiltinProfileSettings,"
              + " aioProfileSettingsFingerprint"
              + " };\n";
            eval(source);
            const makeDefaults = () => ({
              sampler: {
                steps: 32,
                cfg: 5,
                sampler_name: "er_sde",
                scheduler: "simple",
                spectrum: { enabled: true },
                dit_corrections: {
                  enabled: true,
                  dcw_mode: "manual",
                  smc_cfg: true,
                  cfgpp: true,
                  fsg: true,
                  replace_existing_cfg: true,
                },
              },
              model_patches: {
                dave: { enabled: true },
                safe_pag: { enabled: true },
                kj: {
                  fp16_accumulation: false,
                  sage_attention: "disabled",
                  sage_allow_compile: false,
                  sage_stage_scope: {
                    first_pass: true,
                    highres: false,
                    detailer: true,
                    upscale: false,
                  },
                  torch_compile: {
                    enabled: false,
                    mode: "max-autotune-no-cudagraphs",
                  },
                },
              },
              highres: {
                spectrum: { enabled: true },
                dit_corrections: { enabled: true, dcw_mode: "manual" },
              },
              upscale: {
                spectrum: { enabled: true },
                dit_corrections: { enabled: true, dcw_mode: "manual" },
              },
              detailer: {
                enabled: false,
                order: ["face"],
                sam3: {},
                face: {
                  spectrum: { enabled: true },
                  dit_corrections: { enabled: true, dcw_mode: "manual" },
                },
              },
            });
            const defaults = makeDefaults();
            const build = globalThis.__aioPresetExports.aioBuiltinProfileSettings;
            const identify = globalThis.__aioPresetExports.aioBuiltinProfileIdForSettings;
            const fingerprint = globalThis.__aioPresetExports.aioProfileSettingsFingerprint;

            const normal = build("normal", defaults);
            for (const target of [normal.sampler, normal.highres, normal.upscale, normal.detailer.face]) {
              assert.strictEqual(target.spectrum.enabled, false);
              assert.strictEqual(target.dit_corrections.enabled, false);
              assert.strictEqual(target.dit_corrections.dcw_mode, "off");
            }
            assert.strictEqual(normal.model_patches.dave.enabled, false);
            assert.strictEqual(normal.model_patches.safe_pag.enabled, false);
            assert.strictEqual(normal.model_patches.kj.fp16_accumulation, false);
            assert.strictEqual(normal.model_patches.kj.sage_attention, "disabled");
            assert.deepStrictEqual(
              normal.model_patches.kj.sage_stage_scope,
              defaults.model_patches.kj.sage_stage_scope,
            );
            assert.strictEqual(normal.model_patches.kj.torch_compile.enabled, false);

            const turbo = build("turbo", defaults);
            assert.deepStrictEqual(
              [turbo.sampler.steps, turbo.sampler.cfg, turbo.sampler.sampler_name, turbo.sampler.scheduler],
              [10, 1, "er_sde", "simple"],
            );

            const optimized = build("optimized", defaults);
            for (const target of [optimized.sampler, optimized.highres, optimized.upscale, optimized.detailer.face]) {
              assert.strictEqual(target.spectrum.enabled, true);
              assert.strictEqual(target.dit_corrections.enabled, true);
              assert.strictEqual(target.dit_corrections.dcw_mode, "auto");
            }
            assert.strictEqual(optimized.model_patches.kj.fp16_accumulation, true);
            assert.strictEqual(optimized.model_patches.kj.sage_attention, "auto");
            assert.strictEqual(optimized.model_patches.kj.sage_allow_compile, true);
            assert.deepStrictEqual(
              optimized.model_patches.kj.sage_stage_scope,
              defaults.model_patches.kj.sage_stage_scope,
            );
            assert.strictEqual(optimized.model_patches.kj.torch_compile.enabled, true);
            assert.strictEqual(
              optimized.model_patches.kj.torch_compile.mode,
              "max-autotune-no-cudagraphs",
            );
            assert.strictEqual(optimized.model_patches.dave.enabled, false);
            assert.strictEqual(optimized.model_patches.safe_pag.enabled, false);

            assert.strictEqual(identify(normal, defaults), "normal");
            assert.strictEqual(identify(turbo, defaults), "turbo");
            assert.strictEqual(identify(optimized, defaults), "optimized");
            const changed = JSON.parse(JSON.stringify(normal));
            changed.sampler.cfg = 4.5;
            assert.strictEqual(identify(changed, defaults), "");
            assert.strictEqual(
              fingerprint({ b: 2, a: { d: 4, c: 3 } }),
              fingerprint({ a: { c: 3, d: 4 }, b: 2 }),
            );
            assert.notStrictEqual(fingerprint(normal), fingerprint(changed));

            assert.strictEqual(defaults.sampler.spectrum.enabled, true);
            assert.throws(() => build("missing", defaults), /Unknown AiO built-in profile/);
            """
        )
        completed = subprocess.run(
            [node_bin, "-e", runner, str(PRESETS_JS)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(
            completed.returncode,
            0,
            f"stdout:\n{completed.stdout}\nstderr:\n{completed.stderr}",
        )


if __name__ == "__main__":
    unittest.main()
