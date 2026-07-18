from __future__ import annotations

import asyncio
import gc
import importlib.util
import json
import re
import sys
import tempfile
import threading
import time
import types
import unittest
import uuid
import weakref
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


class FakeJsonResponse(dict):
    def __init__(self, payload, status=200):
        super().__init__(payload=payload, status=status)
        self.status = status
        self.headers = {}
        self.content_type = "application/json"

    @property
    def text(self):
        return json.dumps(self["payload"])

    @text.setter
    def text(self, value):
        self["payload"] = json.loads(value)


class FakeResponse:
    def __init__(self, *, status=200, headers=None, body=b""):
        self.status = status
        self.headers = dict(headers or {})
        self.body = body
        self.content_type = "application/octet-stream"


class FakeFileResponse(FakeResponse):
    def __init__(self, path, *, headers=None):
        super().__init__(headers=headers)
        self.path = path


class FakeHTTPException(Exception):
    def __init__(self, *, status=400, body=b""):
        super().__init__(f"HTTP {status}")
        self.status = status
        self.body = body
        self.headers = {}
        self.content_type = "text/plain"


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
        json_response=FakeJsonResponse,
        Response=FakeResponse,
        FileResponse=FakeFileResponse,
        HTTPException=FakeHTTPException,
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


class ApiRequestCorrelationTests(unittest.TestCase):
    ROUTES = {
        "/easyuse_anima/settings",
        "/easyuse_anima/set_setting",
        "/easyuse_anima/long_text_settings",
        "/easyuse_anima/wildcards",
        "/easyuse_anima/long_text_settings/save",
        "/easyuse_anima/autocomplete_status",
        "/easyuse_anima/autocomplete",
        "/easyuse_anima/classify_prompt",
        "/easyuse_anima/translate_prompt",
        "/easyuse_anima/lora_preview",
        "/easyuse_anima/loras",
        "/easyuse_anima/lora_profiles",
        "/easyuse_anima/lora_profiles/save",
        "/easyuse_anima/lora_profiles/load",
        "/easyuse_anima/aio_profiles",
        "/easyuse_anima/aio_profiles/save",
        "/easyuse_anima/aio_profiles/load",
        "/easyuse_anima/aio_profiles/delete",
        "/easyuse_anima/aio_profiles/rename",
        "/easyuse_anima/lora_profiles/fix",
    }

    def test_every_owned_route_has_source_and_registration_correlation(self):
        source = (ROOT / "api.py").read_text(encoding="utf-8")
        decorated_paths = set(
            re.findall(
                r'@routes\.(?:get|post)\("(/easyuse_anima/[^"\n]+)"\)\s+'
                r"@_request_correlated",
                source,
            )
        )
        self.assertEqual(decorated_paths, self.ROUTES)

        _api, routes = load_api_routes()
        self.assertEqual(set(routes.handlers), self.ROUTES)
        for path, handler in routes.handlers.items():
            with self.subTest(path=path):
                self.assertTrue(
                    getattr(handler, "_easyuse_anima_request_correlation", False)
                )

    def test_json_error_body_and_header_share_one_uuid(self):
        api, routes = load_api_routes()
        request_id = "12345678-1234-4567-89ab-1234567890ab"
        with patch.object(api, "create_request_id", return_value=request_id):
            response = asyncio.run(
                routes.handlers["/easyuse_anima/set_setting"](JsonRequest([]))
            )

        self.assertEqual(response["status"], 400)
        self.assertEqual(response["payload"]["code"], "json_object_required")
        self.assertEqual(response["payload"]["request_id"], request_id)
        self.assertEqual(response.headers["X-Request-ID"], request_id)
        self.assertEqual(str(uuid.UUID(response["payload"]["request_id"])), request_id)

    def test_real_aiohttp_json_response_keeps_correlated_header_and_body(self):
        from aiohttp import web as aiohttp_web

        api, _routes = load_api_routes()
        request_id = "17345678-1234-4567-89ab-1234567890ab"
        response = aiohttp_web.json_response(
            {
                "status": "error",
                "code": "invalid_request",
                "message": "Request validation failed",
                "details": {"field": "name"},
            },
            status=422,
        )

        correlated = api.correlate_response(response, request_id)

        self.assertIs(correlated, response)
        self.assertEqual(response.headers["X-Request-ID"], request_id)
        self.assertEqual(json.loads(response.text)["request_id"], request_id)
        self.assertEqual(response.status, 422)
        self.assertEqual(response.content_type, "application/json")

    def test_success_response_has_header_without_body_contract_change(self):
        api, routes = load_api_routes()
        request_id = "22345678-1234-4567-89ab-1234567890ab"
        payload = {"future": {"kept": True}}
        with (
            patch.object(api, "create_request_id", return_value=request_id),
            patch.object(api, "_get_settings_payload_sync", return_value=payload),
        ):
            response = asyncio.run(
                routes.handlers["/easyuse_anima/settings"](JsonRequest())
            )

        self.assertEqual(response["payload"], payload)
        self.assertNotIn("request_id", response["payload"])
        self.assertEqual(response.headers["X-Request-ID"], request_id)

    def test_translation_status_taxonomy_keeps_request_correlation(self):
        api, routes = load_api_routes()

        class TranslationUpstreamTestError(api.PromptTranslationError):
            status = 502
            code = "translation_upstream_error"

        cases = (
            (api.TranslationCancelledError(), 499, "translation_cancelled"),
            (TranslationUpstreamTestError(), 502, "translation_upstream_error"),
            (api.TranslationBusyError(), 503, "translation_busy"),
            (api.TranslationTimeoutError(), 504, "translation_timeout"),
        )
        handler = routes.handlers["/easyuse_anima/translate_prompt"]

        for error, status, code in cases:
            with self.subTest(code=code), patch.object(
                api,
                "_translate_prompt_for_route",
                side_effect=error,
            ):
                response = asyncio.run(handler(JsonRequest({"text": "%{text}"})))
            self.assertEqual(response["status"], status)
            self.assertEqual(response["payload"]["code"], code)
            self.assertEqual(
                response["payload"]["request_id"],
                response.headers["X-Request-ID"],
            )

    def test_unexpected_exception_is_safe_500_and_logged_with_request_id(self):
        api, routes = load_api_routes()
        request_id = "32345678-1234-4567-89ab-1234567890ab"
        secret = r"C:\Users\alice\secret.json API_TOKEN=top-secret"
        with (
            patch.object(api, "create_request_id", return_value=request_id),
            patch.object(api, "_list_aio_profiles", side_effect=RuntimeError(secret)),
            patch.object(api._LOGGER, "exception") as log_exception,
        ):
            response = asyncio.run(
                routes.handlers["/easyuse_anima/aio_profiles"](JsonRequest())
            )

        self.assertEqual(response["status"], 500)
        self.assertEqual(
            response["payload"],
            {
                "status": "error",
                "code": "internal_error",
                "message": "An unexpected server error occurred.",
                "request_id": request_id,
            },
        )
        self.assertEqual(response.headers["X-Request-ID"], request_id)
        log_exception.assert_called_once()
        self.assertEqual(log_exception.call_args.args[1], request_id)
        serialized = json.dumps(response["payload"])
        for forbidden in ("alice", "secret.json", "API_TOKEN", "top-secret", "Traceback"):
            self.assertNotIn(forbidden, serialized)

    def test_cancelled_request_is_not_normalized_or_logged(self):
        api, routes = load_api_routes()
        with (
            patch.object(api, "_run_file_io", side_effect=asyncio.CancelledError()),
            patch.object(api._LOGGER, "exception") as log_exception,
        ):
            with self.assertRaises(asyncio.CancelledError):
                asyncio.run(
                    routes.handlers["/easyuse_anima/aio_profiles"](JsonRequest())
                )
        log_exception.assert_not_called()

    def test_http_exception_preserves_control_flow_and_body_with_header(self):
        from aiohttp import web as aiohttp_web

        api, _routes = load_api_routes()
        request_id = "42345678-1234-4567-89ab-1234567890ab"
        original = aiohttp_web.HTTPNotFound(text="not found")

        @api._request_correlated
        async def raises_http_exception(_request):
            raise original

        with (
            patch.object(api, "create_request_id", return_value=request_id),
            patch.object(api.web, "HTTPException", aiohttp_web.HTTPException),
            patch.object(api._LOGGER, "exception") as log_exception,
        ):
            with self.assertRaises(aiohttp_web.HTTPNotFound) as raised:
                asyncio.run(raises_http_exception(JsonRequest()))

        self.assertEqual(raised.exception.status, 404)
        self.assertEqual(raised.exception.text, "not found")
        self.assertEqual(raised.exception.headers["X-Request-ID"], request_id)
        log_exception.assert_not_called()

    def test_lora_preview_keeps_raw_and_binary_contracts_with_header(self):
        api, routes = load_api_routes()
        handler = routes.handlers["/easyuse_anima/lora_preview"]

        with patch.object(api, "_resolve_lora_preview_path", return_value=None):
            missing = asyncio.run(handler(JsonRequest(query={"name": "missing"})))
        self.assertIsInstance(missing, FakeResponse)
        self.assertEqual(missing.status, 404)
        self.assertEqual(missing.body, b"")
        self.assertIn("X-Request-ID", missing.headers)

        preview_path = r"C:\safe-test\preview.webp"
        with patch.object(
            api,
            "_resolve_lora_preview_path",
            return_value=preview_path,
        ):
            found = asyncio.run(handler(JsonRequest(query={"name": "preview"})))
        self.assertIsInstance(found, FakeFileResponse)
        self.assertEqual(found.path, preview_path)
        self.assertEqual(
            found.headers["Content-Disposition"],
            'filename="preview.webp"',
        )
        self.assertIn("X-Request-ID", found.headers)


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

    def test_stored_profile_shape_errors_have_stable_422_code(self):
        api, routes = load_api_routes()
        cases = (
            (
                "/easyuse_anima/lora_profiles/load",
                "LORA_PROFILE_DIR",
                "[]",
            ),
            (
                "/easyuse_anima/lora_profiles/load",
                "LORA_PROFILE_DIR",
                '{"profile_data": []}',
            ),
            (
                "/easyuse_anima/aio_profiles/load",
                "AIO_PROFILE_DIR",
                "null",
            ),
            (
                "/easyuse_anima/aio_profiles/load",
                "AIO_PROFILE_DIR",
                '{"settings": []}',
            ),
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for route, directory_name, content in cases:
                with self.subTest(route=route, content=content):
                    (root / "Invalid.json").write_text(content, encoding="utf-8")
                    with patch.object(api, directory_name, root):
                        response = asyncio.run(
                            routes.handlers[route](JsonRequest(query={"name": "Invalid"}))
                        )
                    self.assertEqual(response["status"], 422)
                    self.assertEqual(response["payload"]["code"], "invalid_profile_data")
                    self.assertEqual(
                        response["payload"]["message"],
                        "Profile data is invalid",
                    )

    def test_invalid_profile_version_taxonomy_keeps_422_and_request_id_contract(self):
        api, routes = load_api_routes()
        request_id = "52345678-1234-4567-89ab-1234567890ab"
        cases = (
            (
                "/easyuse_anima/lora_profiles/load",
                "LORA_PROFILE_DIR",
                {"version": True, "profile_data": {}},
            ),
            (
                "/easyuse_anima/aio_profiles/load",
                "AIO_PROFILE_DIR",
                {"version": 2.0, "settings": {}},
            ),
        )

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for route, directory_name, stored in cases:
                with self.subTest(route=route):
                    (root / "InvalidVersion.json").write_text(
                        json.dumps(stored),
                        encoding="utf-8",
                    )
                    with (
                        patch.object(api, directory_name, root),
                        patch.object(api, "create_request_id", return_value=request_id),
                    ):
                        response = asyncio.run(
                            routes.handlers[route](
                                JsonRequest(query={"name": "InvalidVersion"})
                            )
                        )

                    self.assertEqual(response["status"], 422)
                    self.assertEqual(response["payload"]["code"], "invalid_profile_data")
                    self.assertEqual(response["payload"]["request_id"], request_id)
                    self.assertEqual(response.headers["X-Request-ID"], request_id)

    def test_invalid_utf8_profile_files_have_stable_redacted_422_code(self):
        api, routes = load_api_routes()
        cases = (
            ("/easyuse_anima/lora_profiles/load", "LORA_PROFILE_DIR"),
            ("/easyuse_anima/aio_profiles/load", "AIO_PROFILE_DIR"),
        )
        secret_bytes = b"\xffC:\\Users\\alice\\secret.json API_TOKEN=top-secret"
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for route, directory_name in cases:
                with self.subTest(route=route):
                    (root / "BrokenUtf8.json").write_bytes(secret_bytes)
                    with patch.object(api, directory_name, root):
                        response = asyncio.run(
                            routes.handlers[route](
                                JsonRequest(query={"name": "BrokenUtf8"})
                            )
                        )
                    self.assertEqual(response["status"], 422)
                    self.assertEqual(response["payload"]["code"], "invalid_profile_data")
                    self.assertEqual(
                        response["payload"]["message"],
                        "Profile data is invalid",
                    )
                    serialized = json.dumps(response["payload"])
                    for forbidden in (
                        "alice",
                        "secret.json",
                        "API_TOKEN",
                        "top-secret",
                        str(root),
                    ):
                        self.assertNotIn(forbidden, serialized)

    def test_aio_rename_rejects_stored_corruption_without_moving_source(self):
        api, routes = load_api_routes()
        cases = (
            ("non-object root", b"[]"),
            ("invalid settings", b'{"settings": []}'),
            ("invalid JSON", b"{"),
            (
                "invalid UTF-8",
                b"\xffC:\\Users\\alice\\secret.json API_TOKEN=top-secret",
            ),
        )
        handler = routes.handlers["/easyuse_anima/aio_profiles/rename"]

        for label, source_bytes in cases:
            with self.subTest(label=label), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                source = root / "Source.json"
                target = root / "Target.json"
                source.write_bytes(source_bytes)

                with patch.object(api, "AIO_PROFILE_DIR", root):
                    response = asyncio.run(
                        handler(
                            JsonRequest(
                                {"old_name": "Source", "new_name": "Target"}
                            )
                        )
                    )

                self.assertEqual(response["status"], 422)
                self.assertEqual(response["payload"]["code"], "invalid_profile_data")
                self.assertEqual(
                    response["payload"]["message"],
                    "Profile data is invalid",
                )
                self.assertEqual(source.read_bytes(), source_bytes)
                self.assertFalse(target.exists())
                self.assertFalse((root / "Target.json.bak").exists())
                serialized = json.dumps(response["payload"])
                for forbidden in (
                    "alice",
                    "secret.json",
                    "API_TOKEN",
                    "top-secret",
                ):
                    self.assertNotIn(forbidden, serialized)

    def test_empty_profile_file_compatibility_boundary_is_preserved(self):
        api, routes = load_api_routes()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "Empty.json").write_text("", encoding="utf-8")

            with patch.object(api, "LORA_PROFILE_DIR", root):
                lora_response = asyncio.run(
                    routes.handlers["/easyuse_anima/lora_profiles/load"](
                        JsonRequest(query={"name": "Empty"})
                    )
                )
            self.assertEqual(lora_response["status"], 200)
            self.assertEqual(lora_response["payload"]["profile"]["profile_data"], {})
            self.assertEqual(lora_response["payload"]["profile"]["profile_count"], 1)

            with patch.object(api, "AIO_PROFILE_DIR", root):
                aio_response = asyncio.run(
                    routes.handlers["/easyuse_anima/aio_profiles/load"](
                        JsonRequest(query={"name": "Empty"})
                    )
                )
            self.assertEqual(aio_response["status"], 422)
            self.assertEqual(aio_response["payload"]["code"], "invalid_profile_data")

    def test_legacy_lora_profile_data_json_string_remains_compatible(self):
        api, routes = load_api_routes()
        stored = {
            "profile_data": json.dumps(
                {"1": {"style_prompt": "legacy", "loras": []}}
            )
        }
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "Legacy.json").write_text(
                json.dumps(stored),
                encoding="utf-8",
            )
            with patch.object(api, "LORA_PROFILE_DIR", root):
                response = asyncio.run(
                    routes.handlers["/easyuse_anima/lora_profiles/load"](
                        JsonRequest(query={"name": "Legacy"})
                    )
                )

        self.assertEqual(response["status"], 200)
        self.assertEqual(
            response["payload"]["profile"]["profile_data"]["1"]["style_prompt"],
            "legacy",
        )

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

    def test_unexpected_worker_exception_is_normalized_only_at_route_boundary(self):
        api, routes = load_api_routes()
        with (
            patch.object(
                api,
                "_list_aio_profiles",
                side_effect=RuntimeError("storage programming error"),
            ),
            patch.object(api._LOGGER, "exception") as log_exception,
        ):
            response = asyncio.run(
                routes.handlers["/easyuse_anima/aio_profiles"](JsonRequest())
            )
        self.assertEqual(response["status"], 500)
        self.assertEqual(response["payload"]["code"], "internal_error")
        self.assertEqual(
            response["payload"]["request_id"],
            response.headers["X-Request-ID"],
        )
        log_exception.assert_called_once()

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
        serialized = json.dumps(payload, ensure_ascii=False)
        self.assertIsNone(re.search(r"[A-Za-z]:[\\/]", serialized), serialized)
        self.assertNotIn("/home/", serialized)
        self.assertNotIn("/Users/", serialized)

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

    def test_autocomplete_search_redacts_nested_status_path_only(self):
        api, routes = load_api_routes()
        produced = {
            "query": "cat",
            "results": [{"tag": "cat", "score": 7}],
            "status": {
                "path": r"C:\Users\alice\secret.csv",
                "exists": True,
                "count": 5,
                "mtime": 1,
            },
            "future": {"kept": True},
        }
        with (
            patch.object(api, "resolve_autocomplete_limit", return_value=20),
            patch.object(api, "resolve_autocomplete_source", return_value="selected"),
            patch.object(
                api,
                "resolve_autocomplete_source_path",
                return_value=("selected", Path(r"C:\Users\alice\secret.csv")),
            ),
            patch.object(api, "search_autocomplete", return_value=produced),
        ):
            response = asyncio.run(
                routes.handlers["/easyuse_anima/autocomplete"](
                    JsonRequest(query={"q": "cat", "limit": "10"})
                )
            )

        payload = response["payload"]
        self.assertEqual(payload["query"], produced["query"])
        self.assertEqual(payload["results"], produced["results"])
        self.assertEqual(payload["future"], produced["future"])
        self.assertEqual(
            payload["status"],
            {"exists": True, "count": 5, "mtime": 1},
        )
        self.assert_no_absolute_path(payload)

    def test_classify_prompt_redacts_nested_status_path_only(self):
        api, routes = load_api_routes()
        produced = {
            "tokens": [{"text": "cat", "category": "general"}],
            "status": {
                "path": "/home/alice/secret.csv",
                "exists": True,
                "count": 9,
                "mtime": 2,
            },
            "future": ["kept"],
        }
        with (
            patch.object(api, "resolve_autocomplete_source", return_value="selected"),
            patch.object(
                api,
                "resolve_autocomplete_source_path",
                return_value=("selected", Path("/home/alice/secret.csv")),
            ),
            patch.object(api, "classify_prompt_text", return_value=produced),
        ):
            response = asyncio.run(
                routes.handlers["/easyuse_anima/classify_prompt"](
                    JsonRequest({"text": "cat", "limit": 10})
                )
            )

        payload = response["payload"]
        self.assertEqual(payload["tokens"], produced["tokens"])
        self.assertEqual(payload["future"], produced["future"])
        self.assertEqual(
            payload["status"],
            {"exists": True, "count": 9, "mtime": 2},
        )
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
    def test_closed_loop_limiter_registry_converges_after_gc(self):
        api, _routes = load_api_routes()
        loop_refs = []

        async def bind_limiter_to_loop():
            loop_refs.append(weakref.ref(asyncio.get_running_loop()))
            limiter = api._file_io_limiter()
            for _index in range(api.FILE_IO_MAX_IN_FLIGHT):
                await limiter.acquire()
            waiter = asyncio.create_task(limiter.acquire())
            await asyncio.sleep(0)
            self.assertFalse(waiter.done())
            limiter.release()
            await waiter
            for _index in range(api.FILE_IO_MAX_IN_FLIGHT):
                limiter.release()

        for _index in range(12):
            asyncio.run(bind_limiter_to_loop())

        for _index in range(3):
            gc.collect()

        self.assertTrue(all(loop_ref() is None for loop_ref in loop_refs))
        self.assertEqual(len(api._FILE_IO_LIMITERS), 0)

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
