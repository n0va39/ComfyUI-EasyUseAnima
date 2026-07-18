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
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
PRESETS_JS = ROOT / "web" / "js" / "aio" / "presets.js"


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
    with patch.dict(sys.modules, {"server": fake_server, "aiohttp": fake_aiohttp}):
        api = load_api_module()
    return api, routes


class AIOProfileStorageTests(unittest.TestCase):
    def test_save_load_list_rename_and_delete_profile(self):
        api = load_api_module()
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(api, "AIO_PROFILE_DIR", Path(tmp)):
                saved = api._save_aio_profile(
                    "My: Profile",
                    {
                        "settings": {
                            "schema": "easyuse_anima_aio_generation_settings",
                            "future_section": {"kept": True},
                        }
                    },
                )
                self.assertEqual(saved["name"], "My_ Profile")
                self.assertTrue((Path(tmp) / "My_ Profile.json").is_file())
                self.assertEqual(
                    [profile["name"] for profile in api._list_aio_profiles()],
                    ["My_ Profile"],
                )
                self.assertTrue(
                    api._load_aio_profile("my_ profile")["settings"]["future_section"]["kept"]
                )

                renamed = api._rename_aio_profile("My_ Profile", "Production")
                self.assertEqual(renamed["name"], "Production")
                self.assertFalse((Path(tmp) / "My_ Profile.json").exists())
                self.assertTrue((Path(tmp) / "Production.json").is_file())

                deleted = api._delete_aio_profile("production")
                self.assertEqual(deleted["name"], "Production")
                self.assertEqual(api._list_aio_profiles(), [])

    def test_delete_removes_profile_primary_and_backup(self):
        api = load_api_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with patch.object(api, "AIO_PROFILE_DIR", root):
                api._save_aio_profile("Delete Me", {"settings": {"value": "old"}})
                api._save_aio_profile(
                    "Delete Me",
                    {"settings": {"value": "current"}},
                    overwrite=True,
                )
                primary = root / "Delete Me.json"
                backup = root / "Delete Me.json.bak"
                self.assertTrue(primary.is_file())
                self.assertTrue(backup.is_file())

                deleted = api._delete_aio_profile("delete me")

                self.assertEqual(deleted["name"], "Delete Me")
                self.assertFalse(primary.exists())
                self.assertFalse(backup.exists())

    def test_delete_backup_failure_preserves_profile_primary(self):
        api = load_api_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with patch.object(api, "AIO_PROFILE_DIR", root):
                api._save_aio_profile("Preserved", {"settings": {"value": "old"}})
                api._save_aio_profile(
                    "Preserved",
                    {"settings": {"value": "current"}},
                    overwrite=True,
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
                        api._delete_aio_profile("Preserved")

                self.assertEqual(api._load_aio_profile("Preserved")["settings"]["value"], "current")
                self.assertTrue(primary.is_file())
                self.assertTrue(backup.is_file())

    def test_deleted_backup_cannot_recover_after_same_name_recreation(self):
        api = load_api_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with patch.object(api, "AIO_PROFILE_DIR", root):
                api._save_aio_profile("Recreated", {"settings": {"value": "old"}})
                api._save_aio_profile(
                    "Recreated",
                    {"settings": {"value": "current"}},
                    overwrite=True,
                )
                api._delete_aio_profile("Recreated")

                api._save_aio_profile("Recreated", {"settings": {"value": "recreated"}})
                primary = root / "Recreated.json"
                backup = root / "Recreated.json.bak"
                self.assertFalse(backup.exists())
                primary.write_text("{", encoding="utf-8")

                with self.assertRaisesRegex(ValueError, "Profile data is invalid"):
                    api._load_aio_profile("Recreated")

    def test_delete_waits_for_in_progress_write_on_same_profile_path(self):
        api = load_api_module()
        profile_storage = sys.modules[api.AtomicJsonStore.__module__]
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

            with patch.object(api, "AIO_PROFILE_DIR", root):
                api._save_aio_profile("Concurrent Delete", {"settings": {"value": "old"}})

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
                        )
                    except BaseException as exc:
                        errors.append(exc)

                def delete_profile():
                    delete_started.set()
                    try:
                        deleted.append(api._delete_aio_profile("Concurrent Delete"))
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
                self.assertEqual(errors, [])
                self.assertEqual(deleted, [{"name": "Concurrent Delete"}])
                self.assertFalse(profile_path.exists())
                self.assertFalse((root / "Concurrent Delete.json.bak").exists())

    def test_delete_waits_for_in_progress_rename_on_target_profile_path(self):
        api = load_api_module()
        profile_storage = sys.modules[api.AtomicJsonStore.__module__]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = (root / "Source.json").resolve()
            target = (root / "Target.json").resolve()
            move_ready = threading.Event()
            release_move = threading.Event()
            delete_started = threading.Event()
            delete_done = threading.Event()
            errors: list[BaseException] = []
            real_replace = profile_storage.os.replace

            with patch.object(api, "AIO_PROFILE_DIR", root):
                api._save_aio_profile("Source", {"settings": {"value": "source"}})
                api._save_aio_profile("Target", {"settings": {"value": "target"}})

                def block_profile_move(current, destination):
                    if Path(current) == source and Path(destination) == target:
                        move_ready.set()
                        if not release_move.wait(2):
                            raise AssertionError("profile move was not released")
                    return real_replace(current, destination)

                def rename_profile():
                    try:
                        api._rename_aio_profile("Source", "Target", overwrite=True)
                    except BaseException as exc:
                        errors.append(exc)

                def delete_target():
                    delete_started.set()
                    try:
                        api._delete_aio_profile("Target")
                    except BaseException as exc:
                        errors.append(exc)
                    finally:
                        delete_done.set()

                with patch.object(profile_storage.os, "replace", side_effect=block_profile_move):
                    renamer = threading.Thread(target=rename_profile)
                    deleter = threading.Thread(target=delete_target)
                    renamer.start()
                    self.assertTrue(move_ready.wait(2))
                    deleter.start()
                    self.assertTrue(delete_started.wait(2))
                    self.assertFalse(delete_done.wait(0.05))
                    release_move.set()
                    renamer.join(2)
                    deleter.join(2)

                self.assertFalse(renamer.is_alive())
                self.assertFalse(deleter.is_alive())
                self.assertEqual(errors, [])
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
                    with patch.object(api, "AIO_PROFILE_DIR", Path(tmp)):
                        api._save_aio_profile(
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
            with patch.object(api, "AIO_PROFILE_DIR", Path(tmp)):
                (Path(tmp) / "Broken.json").write_text("{", encoding="utf-8")
                with self.assertRaisesRegex(ValueError, "Profile data is invalid"):
                    api._load_aio_profile("Broken")

    def test_empty_profile_preserves_legacy_payload_validation_contract(self):
        api = load_api_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with patch.object(api, "AIO_PROFILE_DIR", root):
                (root / "Empty.json").write_text("", encoding="utf-8")

                with self.assertRaisesRegex(ValueError, "Profile settings must be an object"):
                    api._load_aio_profile("Empty")

    def test_invalid_primary_recovers_last_valid_backup(self):
        api = load_api_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with patch.object(api, "AIO_PROFILE_DIR", root):
                api._save_aio_profile("Recoverable", {"settings": {"value": "first"}})
                api._save_aio_profile(
                    "Recoverable",
                    {"settings": {"value": "second"}},
                    overwrite=True,
                )
                (root / "Recoverable.json").write_text("{", encoding="utf-8")

                recovered = api._load_aio_profile("Recoverable")

        self.assertEqual(recovered["name"], "Recoverable")
        self.assertEqual(recovered["settings"]["value"], "first")

    def test_concurrent_profile_publish_never_exposes_partial_json(self):
        api = load_api_module()
        profile_storage = sys.modules[api.AtomicJsonStore.__module__]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile_path = (root / "Concurrent.json").resolve()
            publish_ready = threading.Event()
            release_publish = threading.Event()
            errors: list[BaseException] = []
            real_replace = profile_storage.os.replace

            with patch.object(api, "AIO_PROFILE_DIR", root):
                api._save_aio_profile("Concurrent", {"settings": {"value": "old"}})

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
            ("array", []),
            ("empty object", {}),
            ("non-object settings", {"settings": []}),
        )

        for label, invalid_payload in invalid_payloads:
            with self.subTest(label=label), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                source = root / "Source.json"
                target = root / "Target.json"
                source.write_text(
                    json.dumps(invalid_payload, ensure_ascii=False),
                    encoding="utf-8",
                )
                source_bytes = source.read_bytes()

                with patch.object(api, "AIO_PROFILE_DIR", root):
                    with self.assertRaisesRegex(ValueError, "Profile settings must be an object"):
                        api._rename_aio_profile("Source", "Target")

                self.assertEqual(source.read_bytes(), source_bytes)
                self.assertFalse(target.exists())
                self.assertFalse((root / "Target.json.bak").exists())

    def test_rename_invalid_schema_preserves_overwrite_target_and_existing_backup(self):
        api = load_api_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with patch.object(api, "AIO_PROFILE_DIR", root):
                api._save_aio_profile("Target", {"settings": {"value": "old target"}})
                api._save_aio_profile(
                    "Target",
                    {"settings": {"value": "current target"}},
                    overwrite=True,
                )
                source = root / "Source.json"
                target = root / "Target.json"
                backup = root / "Target.json.bak"
                source.write_text('{"settings": []}', encoding="utf-8")
                source_bytes = source.read_bytes()
                target_bytes = target.read_bytes()
                backup_bytes = backup.read_bytes()

                with self.assertRaisesRegex(ValueError, "Profile settings must be an object"):
                    api._rename_aio_profile("Source", "Target", overwrite=True)

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
            with patch.object(api, "AIO_PROFILE_DIR", root):
                api._save_aio_profile("Source", {"settings": {"value": "source"}})
                api._save_aio_profile("Target", {"settings": {"value": "target"}})

                renamed = api._rename_aio_profile("Source", "Target", overwrite=True)

                backup = json.loads((root / "Target.json.bak").read_text(encoding="utf-8"))
                self.assertEqual(renamed["name"], "Target")
                self.assertEqual(renamed["settings"]["value"], "source")
                self.assertEqual(backup["settings"]["value"], "target")
                self.assertFalse((root / "Source.json").exists())

    def test_rename_move_failure_preserves_source_target_and_backup(self):
        api = load_api_module()
        profile_storage = sys.modules[api.AtomicJsonStore.__module__]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = (root / "Source.json").resolve()
            target = (root / "Target.json").resolve()
            real_replace = profile_storage.os.replace

            with patch.object(api, "AIO_PROFILE_DIR", root):
                api._save_aio_profile("Source", {"settings": {"value": "source"}})
                api._save_aio_profile("Target", {"settings": {"value": "target"}})

                def fail_move(current, destination):
                    if Path(current) == source and Path(destination) == target:
                        raise OSError("rename move failed")
                    return real_replace(current, destination)

                with patch.object(profile_storage.os, "replace", side_effect=fail_move):
                    with self.assertRaisesRegex(OSError, "rename move failed"):
                        api._rename_aio_profile("Source", "Target", overwrite=True)

                self.assertEqual(api._load_aio_profile("Source")["settings"]["value"], "source")
                self.assertEqual(api._load_aio_profile("Target")["settings"]["value"], "target")
                backup = json.loads((root / "Target.json.bak").read_text(encoding="utf-8"))
                self.assertEqual(backup["settings"]["value"], "target")
                self.assertEqual([path for path in root.iterdir() if path.name.endswith(".tmp")], [])

    def test_rename_target_backup_failure_preserves_source_and_target(self):
        api = load_api_module()
        profile_storage = sys.modules[api.AtomicJsonStore.__module__]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            backup_path = (root / "Target.json.bak").resolve()
            real_replace = profile_storage.os.replace

            with patch.object(api, "AIO_PROFILE_DIR", root):
                api._save_aio_profile("Source", {"settings": {"value": "source"}})
                api._save_aio_profile("Target", {"settings": {"value": "target"}})

                def fail_backup(current, destination):
                    if Path(destination) == backup_path:
                        raise OSError("target backup failed")
                    return real_replace(current, destination)

                with patch.object(profile_storage.os, "replace", side_effect=fail_backup):
                    with self.assertRaisesRegex(OSError, "target backup failed"):
                        api._rename_aio_profile("Source", "Target", overwrite=True)

                self.assertEqual(api._load_aio_profile("Source")["settings"]["value"], "source")
                self.assertEqual(api._load_aio_profile("Target")["settings"]["value"], "target")
                self.assertEqual([path for path in root.iterdir() if path.name.endswith(".tmp")], [])

    def test_rename_does_not_depend_on_a_separate_unlink(self):
        api = load_api_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with patch.object(api, "AIO_PROFILE_DIR", root):
                api._save_aio_profile("Source", {"settings": {"value": "source"}})

                with patch.object(Path, "unlink", side_effect=OSError("unlink failed")):
                    renamed = api._rename_aio_profile("Source", "Renamed")

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

                    self.assertEqual(response["status"], 400)
                    self.assertEqual(
                        response["payload"]["message"],
                        "overwrite must be a JSON boolean",
                    )
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
                    {"status": "error", "message": "Profile already exists"},
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
            {"status": "error", "message": "Profile not found"},
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
