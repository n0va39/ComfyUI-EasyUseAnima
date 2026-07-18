from __future__ import annotations

import asyncio
import importlib.util
import json
import re
import sys
import tempfile
import threading
import time
import types
import unittest
from itertools import count
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
_LOAD_COUNTER = count()


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
    def __init__(self, payload=None, *, error=None, query=None):
        self.payload = payload
        self.error = error
        self.query = query or {}

    async def json(self):
        if self.error is not None:
            raise self.error
        return self.payload


def load_api_routes():
    package_name = f"easyuse_anima_api_contract_test_package_{next(_LOAD_COUNTER)}"
    package = types.ModuleType(package_name)
    package.__path__ = [str(ROOT)]
    sys.modules[package_name] = package

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

    spec = importlib.util.spec_from_file_location(
        f"{package_name}.api",
        ROOT / "api.py",
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    with patch.dict(sys.modules, {"server": fake_server, "aiohttp": fake_aiohttp}):
        spec.loader.exec_module(module)
    return module, routes


def response_strings(value):
    if isinstance(value, dict):
        for key, item in value.items():
            yield str(key)
            yield from response_strings(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            yield from response_strings(item)
    elif isinstance(value, str):
        yield value


class ApiRequestContractTests(unittest.TestCase):
    POST_ROUTES = (
        "/easyuse_anima/set_setting",
        "/easyuse_anima/long_text_settings/save",
        "/easyuse_anima/classify_prompt",
        "/easyuse_anima/translate_prompt",
        "/easyuse_anima/lora_profiles/save",
        "/easyuse_anima/aio_profiles/save",
        "/easyuse_anima/aio_profiles/delete",
        "/easyuse_anima/aio_profiles/rename",
        "/easyuse_anima/lora_profiles/fix",
    )

    def test_all_json_routes_reject_malformed_and_non_object_bodies_before_submit(self):
        api, routes = load_api_routes()
        malformed = json.JSONDecodeError("C:\\Users\\alice\\secret", "{", 1)
        cases = (
            (JsonRequest(error=malformed), "malformed_json"),
            (JsonRequest([]), "json_object_required"),
            (JsonRequest(None), "json_object_required"),
            (JsonRequest("scalar"), "json_object_required"),
            (JsonRequest(7), "json_object_required"),
        )

        with (
            patch.object(api.asyncio, "to_thread") as submit,
            patch.object(api, "_translate_prompt_for_route") as translate,
        ):
            for route in self.POST_ROUTES:
                for request, code in cases:
                    with self.subTest(route=route, code=code, body=request.payload):
                        response = asyncio.run(routes.handlers[route](request))
                        self.assertEqual(response["status"], 400)
                        self.assertEqual(response["payload"]["status"], "error")
                        self.assertEqual(response["payload"]["code"], code)
                        self.assertNotIn("secret", json.dumps(response["payload"]))

            submit.assert_not_called()
            translate.assert_not_called()

    def test_endpoint_field_type_errors_are_422_before_submit(self):
        api, routes = load_api_routes()
        cases = (
            ("/easyuse_anima/set_setting", {"key": 1}, "key"),
            ("/easyuse_anima/long_text_settings/save", {"values": []}, "values"),
            ("/easyuse_anima/classify_prompt", {"text": []}, "text"),
            ("/easyuse_anima/classify_prompt", {"text": "x", "limit": "10"}, "limit"),
            ("/easyuse_anima/translate_prompt", {"text": None}, "text"),
            ("/easyuse_anima/lora_profiles/save", {"name": 3}, "name"),
            (
                "/easyuse_anima/lora_profiles/save",
                {"name": "Preset", "profile_data": []},
                "profile_data",
            ),
            (
                "/easyuse_anima/lora_profiles/save",
                {"name": "Preset", "overwrite": "false"},
                "overwrite",
            ),
            (
                "/easyuse_anima/aio_profiles/save",
                {"name": "Preset", "settings": []},
                "settings",
            ),
            ("/easyuse_anima/aio_profiles/delete", {"name": 4}, "name"),
            (
                "/easyuse_anima/aio_profiles/rename",
                {"old_name": "Old", "new_name": []},
                "new_name",
            ),
            (
                "/easyuse_anima/lora_profiles/fix",
                {"profile_data": []},
                "profile_data",
            ),
        )

        with (
            patch.object(api.asyncio, "to_thread") as submit,
            patch.object(api, "_translate_prompt_for_route") as translate,
        ):
            for route, payload, field in cases:
                with self.subTest(route=route, field=field):
                    response = asyncio.run(routes.handlers[route](JsonRequest(payload)))
                    self.assertEqual(response["status"], 422)
                    self.assertEqual(response["payload"]["code"], "invalid_request")
                    self.assertEqual(response["payload"]["details"], {"field": field})

            submit.assert_not_called()
            translate.assert_not_called()

    def test_profile_conflict_not_found_and_delete_race_have_stable_codes(self):
        api, routes = load_api_routes()
        cases = (
            (
                "/easyuse_anima/aio_profiles/save",
                JsonRequest({"name": "Saved", "settings": {}}),
                "_save_aio_profile",
                FileExistsError("C:\\private\\existing.json"),
                409,
                "profile_exists",
            ),
            (
                "/easyuse_anima/aio_profiles/load",
                JsonRequest(query={"name": "Missing"}),
                "_load_aio_profile",
                FileNotFoundError("/home/alice/missing.json"),
                404,
                "profile_not_found",
            ),
            (
                "/easyuse_anima/aio_profiles/delete",
                JsonRequest({"name": "Raced"}),
                "_delete_aio_profile",
                FileNotFoundError("deleted after lookup"),
                404,
                "profile_not_found",
            ),
        )

        for route, request, operation_name, error, status, code in cases:
            with self.subTest(route=route, code=code):
                with patch.object(api, operation_name, side_effect=error):
                    response = asyncio.run(routes.handlers[route](request))
                self.assertEqual(response["status"], status)
                self.assertEqual(response["payload"]["code"], code)
                serialized = json.dumps(response["payload"])
                self.assertNotIn("private", serialized)
                self.assertNotIn("/home/", serialized)

    def test_invalid_profile_json_files_have_stable_422_code(self):
        api, routes = load_api_routes()
        cases = (
            ("/easyuse_anima/aio_profiles/load", "AIO_PROFILE_DIR"),
            ("/easyuse_anima/lora_profiles/load", "LORA_PROFILE_DIR"),
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for route, directory_name in cases:
                with self.subTest(route=route):
                    (root / "Broken.json").write_text("{", encoding="utf-8")
                    with patch.object(api, directory_name, root):
                        response = asyncio.run(
                            routes.handlers[route](JsonRequest(query={"name": "Broken"}))
                        )
                    self.assertEqual(response["status"], 422)
                    self.assertEqual(response["payload"]["code"], "invalid_profile_data")
                    self.assertEqual(response["payload"]["message"], "Profile data is invalid")

    def test_public_validation_error_does_not_echo_path_stack_or_secret(self):
        api, routes = load_api_routes()
        secret = "C:\\Users\\alice\\profile.json API_TOKEN=top-secret"
        with patch.object(api, "_save_aio_profile", side_effect=ValueError(secret)):
            response = asyncio.run(
                routes.handlers["/easyuse_anima/aio_profiles/save"](
                    JsonRequest({"name": "Safe", "settings": {}})
                )
            )

        self.assertEqual(response["status"], 422)
        self.assertEqual(response["payload"]["code"], "invalid_request")
        self.assertEqual(response["payload"]["message"], "Request validation failed")
        serialized = json.dumps(response["payload"])
        for forbidden in ("alice", "profile.json", "API_TOKEN", "top-secret", "Traceback"):
            self.assertNotIn(forbidden, serialized)

    def test_unexpected_worker_exception_is_not_reclassified(self):
        api, routes = load_api_routes()
        with patch.object(
            api,
            "_list_aio_profiles",
            side_effect=RuntimeError("storage programming error"),
        ):
            with self.assertRaisesRegex(RuntimeError, "storage programming error"):
                asyncio.run(routes.handlers["/easyuse_anima/aio_profiles"](JsonRequest()))

    def test_normal_settings_and_profile_success_payloads_remain_compatible(self):
        api, routes = load_api_routes()
        settings_payload = {
            "autocomplete.source": "dbr_danbooru_2025_09_01",
            "autocomplete.limit": 20,
        }
        with patch.object(api, "_get_settings_payload_sync", return_value=settings_payload):
            settings_response = asyncio.run(
                routes.handlers["/easyuse_anima/settings"](JsonRequest())
            )
        self.assertEqual(settings_response, {"payload": settings_payload, "status": 200})

        saved_profile = {"name": "Saved", "settings": {"future": {"kept": True}}}
        with patch.object(api, "_save_aio_profile", return_value=saved_profile):
            profile_response = asyncio.run(
                routes.handlers["/easyuse_anima/aio_profiles/save"](
                    JsonRequest({"name": "Saved", "settings": saved_profile["settings"]})
                )
            )
        self.assertEqual(
            profile_response,
            {
                "payload": {"status": "ok", "profile": saved_profile},
                "status": 200,
            },
        )


class ApiPathRedactionTests(unittest.TestCase):
    def assert_no_absolute_path(self, payload):
        for value in response_strings(payload):
            self.assertIsNone(re.match(r"^[A-Za-z]:[\\/]", value), value)
            self.assertFalse(value.startswith("/home/"), value)
            self.assertFalse(value.startswith("/Users/"), value)

    def test_autocomplete_status_replaces_all_paths_with_public_source_metadata(self):
        api, routes = load_api_routes()
        with (
            patch.object(api, "resolve_autocomplete_source", return_value="selected"),
            patch.object(
                api,
                "resolve_autocomplete_source_path",
                return_value=("selected", Path(r"C:\Users\alice\secret.csv")),
            ),
            patch.object(
                api,
                "autocomplete_status",
                return_value={
                    "path": r"C:\Users\alice\secret.csv",
                    "exists": True,
                    "count": 5,
                    "mtime": 1,
                },
            ),
            patch.object(
                api,
                "available_autocomplete_sources",
                return_value=[
                    {
                        "key": "selected",
                        "label": "Selected dataset",
                        "path": "/home/alice/secret.csv",
                        "exists": True,
                        "selected": True,
                    }
                ],
            ),
        ):
            response = asyncio.run(
                routes.handlers["/easyuse_anima/autocomplete_status"](JsonRequest())
            )

        payload = response["payload"]
        self.assertEqual(payload["source"], "selected")
        self.assertEqual(payload["source_label"], "Selected dataset")
        self.assertNotIn("path", payload)
        self.assertTrue(all("path" not in source for source in payload["sources"]))
        self.assert_no_absolute_path(payload)

    def test_wildcard_roots_keep_string_list_compatibility_without_paths(self):
        api, routes = load_api_routes()
        secret_roots = [Path(r"C:\Users\alice\wildcards"), Path("/home/alice/wildcards")]
        with (
            patch.object(
                api,
                "public_settings",
                return_value={
                    "wildcard.extra_paths": "C:\\Users\\alice\\wildcards\n/home/alice/wildcards"
                },
            ),
            patch.object(api, "resolve_wildcard_roots", return_value=secret_roots),
            patch.object(api, "list_wildcards", return_value=["artist/name"]),
        ):
            response = asyncio.run(
                routes.handlers["/easyuse_anima/wildcards"](JsonRequest())
            )

        payload = response["payload"]
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["items"], ["artist/name"])
        self.assertEqual(payload["roots"], ["wildcard:1", "wildcard:2"])
        self.assertTrue(all(isinstance(root, str) for root in payload["roots"]))
        self.assertEqual(
            [source["label"] for source in payload["sources"]],
            ["Wildcard source 1", "Wildcard source 2"],
        )
        self.assert_no_absolute_path(payload)


class ApiFileIoOffloadTests(unittest.TestCase):
    def test_slow_scan_save_and_stat_leave_event_loop_heartbeat_running(self):
        api, routes = load_api_routes()
        cases = (
            (
                "/easyuse_anima/autocomplete_status",
                JsonRequest(),
                "_autocomplete_status_payload_sync",
                {"source": "safe", "source_label": "Safe", "sources": []},
            ),
            (
                "/easyuse_anima/aio_profiles/save",
                JsonRequest({"name": "Saved", "settings": {}}),
                "_save_aio_profile",
                {"name": "Saved", "settings": {}},
            ),
            (
                "/easyuse_anima/aio_profiles",
                JsonRequest(),
                "_list_aio_profiles",
                [],
            ),
        )

        for route, request, operation_name, result in cases:
            started = threading.Event()

            def slow_operation(*_args, owned_result=result, **_kwargs):
                started.set()
                time.sleep(0.05)
                return owned_result

            async def exercise():
                heartbeat = 0
                task = asyncio.create_task(routes.handlers[route](request))
                while not started.is_set():
                    await asyncio.sleep(0)
                while not task.done():
                    heartbeat += 1
                    await asyncio.sleep(0.002)
                return await task, heartbeat

            with self.subTest(route=route):
                with patch.object(api, operation_name, side_effect=slow_operation):
                    response, heartbeat = asyncio.run(exercise())
                self.assertEqual(response["status"], 200)
                self.assertGreaterEqual(heartbeat, 3)

    def test_file_io_result_exception_and_cancellation_meanings_are_preserved(self):
        api, _routes = load_api_routes()

        self.assertEqual(asyncio.run(api._run_file_io(lambda: "ok")), "ok")
        with self.assertRaisesRegex(RuntimeError, "worker failed"):
            asyncio.run(
                api._run_file_io(
                    lambda: (_ for _ in ()).throw(RuntimeError("worker failed"))
                )
            )

        started = threading.Event()
        release = threading.Event()
        completed = threading.Event()

        def slow_worker():
            started.set()
            release.wait(timeout=1)
            completed.set()

        async def cancel_wait_only():
            task = asyncio.create_task(api._run_file_io(slow_worker))
            while not started.is_set():
                await asyncio.sleep(0)
            task.cancel()
            with self.assertRaises(asyncio.CancelledError):
                await task
            self.assertFalse(completed.is_set())
            release.set()
            deadline = asyncio.get_running_loop().time() + 1
            while not completed.is_set() and asyncio.get_running_loop().time() < deadline:
                await asyncio.sleep(0.001)
            self.assertTrue(completed.is_set())

        asyncio.run(cancel_wait_only())

    def test_repeated_cancellation_does_not_release_slots_before_workers_finish(self):
        api, _routes = load_api_routes()
        submitted = 0
        active = 0
        peak_active = 0

        async def exercise():
            nonlocal submitted, active, peak_active
            release = asyncio.Event()

            async def fake_to_thread(_function, *_args, **_kwargs):
                nonlocal submitted, active, peak_active
                submitted += 1
                active += 1
                peak_active = max(peak_active, active)
                try:
                    await release.wait()
                finally:
                    active -= 1

            with patch.object(api.asyncio, "to_thread", new=fake_to_thread):
                first = [
                    asyncio.create_task(api._run_file_io(lambda: None))
                    for _index in range(20)
                ]
                while submitted < api.FILE_IO_MAX_IN_FLIGHT:
                    await asyncio.sleep(0)
                for task in first:
                    task.cancel()
                await asyncio.gather(*first, return_exceptions=True)

                repeated = [
                    asyncio.create_task(api._run_file_io(lambda: None))
                    for _index in range(20)
                ]
                for _index in range(20):
                    await asyncio.sleep(0)

                self.assertEqual(submitted, api.FILE_IO_MAX_IN_FLIGHT)
                self.assertEqual(active, api.FILE_IO_MAX_IN_FLIGHT)
                self.assertEqual(peak_active, api.FILE_IO_MAX_IN_FLIGHT)

                for task in repeated:
                    task.cancel()
                await asyncio.gather(*repeated, return_exceptions=True)
                release.set()
                deadline = asyncio.get_running_loop().time() + 1
                while active and asyncio.get_running_loop().time() < deadline:
                    await asyncio.sleep(0)
                self.assertEqual(active, 0)
                self.assertEqual(submitted, api.FILE_IO_MAX_IN_FLIGHT)

        asyncio.run(exercise())


if __name__ == "__main__":
    unittest.main()
