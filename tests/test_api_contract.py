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

from tests.api_test_support import replace_sys_modules

ROOT = Path(__file__).resolve().parents[1]
_LOAD_COUNTER = count()


class RouteRegistry:
    def __init__(self):
        self.handlers = {}
        self.registrations = []

    def _route(self, method, path):
        def register(handler):
            key = (method, path)
            if key in self.registrations:
                raise AssertionError(f"duplicate route registration: {method} {path}")
            self.registrations.append(key)
            self.handlers[path] = handler
            return handler

        return register

    def get(self, path):
        return self._route("GET", path)

    def post(self, path):
        return self._route("POST", path)


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


def load_api_routes(*, register=True, routes=None):
    package_name = f"easyuse_anima_api_contract_test_package_{next(_LOAD_COUNTER)}"
    package = types.ModuleType(package_name)
    package.__path__ = [str(ROOT)]
    sys.modules[package_name] = package

    routes = RouteRegistry() if routes is None else routes
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
    with replace_sys_modules({"server": fake_server, "aiohttp": fake_aiohttp}):
        spec.loader.exec_module(module)
        if register:
            module.register_routes()
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


def profile_directory_owner(api, directory_name):
    if directory_name == "AIO_PROFILE_DIR":
        return api._aio_profiles
    if directory_name == "LORA_PROFILE_DIR":
        return api._lora_profiles
    raise AssertionError(f"Unknown profile directory: {directory_name}")


class ApiRequestCorrelationTests(unittest.TestCase):
    ROUTE_SEQUENCE = (
        ("GET", "/easyuse_anima/settings"),
        ("POST", "/easyuse_anima/set_setting"),
        ("GET", "/easyuse_anima/long_text_settings"),
        ("GET", "/easyuse_anima/wildcards"),
        ("POST", "/easyuse_anima/long_text_settings/save"),
        ("GET", "/easyuse_anima/autocomplete_status"),
        ("GET", "/easyuse_anima/autocomplete"),
        ("POST", "/easyuse_anima/classify_prompt"),
        ("POST", "/easyuse_anima/translate_prompt"),
        ("POST", "/easyuse_anima/aio/torch-compile/recommend"),
        ("GET", "/easyuse_anima/lora_preview"),
        ("GET", "/easyuse_anima/loras"),
        ("GET", "/easyuse_anima/lora_profiles"),
        ("POST", "/easyuse_anima/lora_profiles/save"),
        ("GET", "/easyuse_anima/lora_profiles/load"),
        ("GET", "/easyuse_anima/aio_profiles"),
        ("POST", "/easyuse_anima/aio_profiles/save"),
        ("GET", "/easyuse_anima/aio_profiles/load"),
        ("POST", "/easyuse_anima/aio_profiles/delete"),
        ("POST", "/easyuse_anima/aio_profiles/rename"),
        ("POST", "/easyuse_anima/lora_profiles/fix"),
    )
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
        "/easyuse_anima/aio/torch-compile/recommend",
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
        api, routes = load_api_routes()
        self.assertEqual(api._ROUTE_SIGNATURE, self.ROUTE_SEQUENCE)
        self.assertEqual(tuple(routes.registrations), self.ROUTE_SEQUENCE)
        self.assertEqual(set(routes.handlers), self.ROUTES)
        for path, handler in routes.handlers.items():
            with self.subTest(path=path):
                self.assertTrue(
                    getattr(handler, "_easyuse_anima_request_correlation", False)
                )

    def test_import_is_registration_free_and_same_table_registration_is_idempotent(self):
        api, routes = load_api_routes(register=False)

        self.assertEqual(routes.registrations, [])
        self.assertTrue(api.register_routes())
        self.assertEqual(tuple(routes.registrations), self.ROUTE_SEQUENCE)
        self.assertTrue(api.register_routes())
        self.assertEqual(tuple(routes.registrations), self.ROUTE_SEQUENCE)

    def test_each_new_route_table_receives_the_exact_route_set(self):
        api, first_routes = load_api_routes()
        second_routes = RouteRegistry()

        self.assertTrue(api.register_routes(second_routes))
        self.assertEqual(tuple(first_routes.registrations), self.ROUTE_SEQUENCE)
        self.assertEqual(tuple(second_routes.registrations), self.ROUTE_SEQUENCE)

    def test_new_package_namespace_reuses_the_route_table_signature_marker(self):
        first_api, routes = load_api_routes()
        first_handlers = dict(routes.handlers)

        second_api, same_routes = load_api_routes(routes=routes)

        self.assertIs(same_routes, routes)
        self.assertIsNot(first_api, second_api)
        self.assertEqual(tuple(routes.registrations), self.ROUTE_SEQUENCE)
        self.assertEqual(routes.handlers, first_handlers)

    def test_unavailable_route_table_can_be_registered_on_a_later_attempt(self):
        api, routes = load_api_routes(register=False)
        later_routes = RouteRegistry()

        with patch.object(api, "_get_prompt_routes", return_value=None):
            self.assertFalse(api.register_routes())
            self.assertIsNone(api.routes)
        self.assertTrue(api.register_routes(later_routes))
        self.assertEqual(tuple(routes.registrations), ())
        self.assertEqual(tuple(later_routes.registrations), self.ROUTE_SEQUENCE)

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

        self.assertIs(api.lora_preview_handler, handler)
        self.assertEqual(handler.__name__, "lora_preview_handler")
        self.assertTrue(
            handler.__module__.endswith(
                ".easyuse_anima.api.routes.lora_preview"
            )
        )
        self.assertTrue(handler._easyuse_anima_request_correlation)

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


class ApiLoraCatalogRouteTests(unittest.TestCase):
    def test_route_handler_is_owned_by_the_canonical_factory(self):
        api, routes = load_api_routes()
        handler = routes.handlers["/easyuse_anima/loras"]

        self.assertIs(api.loras_handler, handler)
        self.assertEqual(handler.__name__, "loras_handler")
        self.assertTrue(
            handler.__module__.endswith(
                ".easyuse_anima.api.routes.lora_catalog"
            )
        )
        self.assertTrue(handler._easyuse_anima_request_correlation)

    def test_route_keeps_dynamic_list_seam_and_payload_shape(self):
        api, routes = load_api_routes()
        loras = ["style/foo.safetensors", "artist/bar.safetensors"]

        with patch.object(api, "_list_loras", return_value=loras) as list_loras:
            response = asyncio.run(
                routes.handlers["/easyuse_anima/loras"](JsonRequest())
            )

        self.assertEqual(response["status"], 200)
        self.assertEqual(response["payload"], {"loras": loras})
        list_loras.assert_called_once_with()


class ApiProfileListRouteTests(unittest.TestCase):
    def test_route_handlers_are_owned_by_the_canonical_factory(self):
        api, routes = load_api_routes()
        cases = (
            ("lora_profiles_handler", "/easyuse_anima/lora_profiles"),
            ("aio_profiles_handler", "/easyuse_anima/aio_profiles"),
        )

        for name, path in cases:
            with self.subTest(path=path):
                handler = routes.handlers[path]
                self.assertIs(getattr(api, name), handler)
                self.assertEqual(handler.__name__, name)
                self.assertTrue(
                    handler.__module__.endswith(
                        ".easyuse_anima.api.routes.profile_lists"
                    )
                )
                self.assertTrue(handler._easyuse_anima_request_correlation)

    def test_routes_keep_dynamic_list_seams_and_legacy_success_shapes(self):
        api, routes = load_api_routes()
        profiles = [
            {
                "name": "Portrait",
                "profile_id": "22345678-1234-4567-89ab-1234567890ab",
                "revision": 3,
            }
        ]
        cases = (
            (
                "/easyuse_anima/lora_profiles",
                "_list_lora_profiles",
                {"profiles": profiles},
            ),
            (
                "/easyuse_anima/aio_profiles",
                "_list_aio_profiles",
                {"status": "ok", "profiles": profiles},
            ),
        )

        for path, operation_name, expected_payload in cases:
            with self.subTest(path=path), patch.object(
                api,
                operation_name,
                return_value=profiles,
            ) as list_profiles:
                response = asyncio.run(routes.handlers[path](JsonRequest()))

            self.assertEqual(response["status"], 200)
            self.assertEqual(response["payload"], expected_payload)
            list_profiles.assert_called_once_with()

    def test_routes_map_only_stored_profile_errors(self):
        api, routes = load_api_routes()
        cases = (
            ("/easyuse_anima/lora_profiles", "_list_lora_profiles"),
            ("/easyuse_anima/aio_profiles", "_list_aio_profiles"),
        )

        for path, operation_name in cases:
            with self.subTest(path=path), patch.object(
                api,
                operation_name,
                side_effect=api.InvalidProfileDataError("private path"),
            ):
                response = asyncio.run(routes.handlers[path](JsonRequest()))

            self.assertEqual(response["status"], 422)
            self.assertEqual(response["payload"]["code"], "invalid_profile_data")
            self.assertNotIn("private path", json.dumps(response["payload"]))


class ApiProfileLoadRouteTests(unittest.TestCase):
    def test_route_handlers_are_owned_by_the_canonical_factory(self):
        api, routes = load_api_routes()
        cases = (
            (
                "load_lora_profile_handler",
                "/easyuse_anima/lora_profiles/load",
            ),
            (
                "load_aio_profile_handler",
                "/easyuse_anima/aio_profiles/load",
            ),
        )

        for name, path in cases:
            with self.subTest(path=path):
                handler = routes.handlers[path]
                self.assertIs(getattr(api, name), handler)
                self.assertEqual(handler.__name__, name)
                self.assertTrue(
                    handler.__module__.endswith(
                        ".easyuse_anima.api.routes.profile_loads"
                    )
                )
                self.assertTrue(handler._easyuse_anima_request_correlation)

    def test_routes_keep_dynamic_load_seams_query_contract_and_success_shape(self):
        api, routes = load_api_routes()
        profile = {
            "name": "Portrait",
            "profile_id": "32345678-1234-4567-89ab-1234567890ab",
            "revision": 4,
        }
        cases = (
            (
                "/easyuse_anima/lora_profiles/load",
                "_load_lora_profile",
                JsonRequest(query={"name": "Portrait"}),
                "Portrait",
            ),
            (
                "/easyuse_anima/aio_profiles/load",
                "_load_aio_profile",
                JsonRequest(),
                "",
            ),
        )

        for path, operation_name, request, expected_name in cases:
            with self.subTest(path=path), patch.object(
                api,
                operation_name,
                return_value=profile,
            ) as load_profile:
                response = asyncio.run(routes.handlers[path](request))

            self.assertEqual(response["status"], 200)
            self.assertEqual(
                response["payload"],
                {"status": "ok", "profile": profile},
            )
            load_profile.assert_called_once_with(expected_name)

    def test_routes_preserve_mapped_load_error_boundaries(self):
        api, routes = load_api_routes()
        cases = (
            (
                "/easyuse_anima/lora_profiles/load",
                "_load_lora_profile",
                FileNotFoundError("C:\\private\\missing.json"),
                404,
                "profile_not_found",
            ),
            (
                "/easyuse_anima/aio_profiles/load",
                "_load_aio_profile",
                FileNotFoundError("/home/alice/missing.json"),
                404,
                "profile_not_found",
            ),
            (
                "/easyuse_anima/lora_profiles/load",
                "_load_lora_profile",
                json.JSONDecodeError("private json", "{", 0),
                422,
                "invalid_profile_data",
            ),
            (
                "/easyuse_anima/aio_profiles/load",
                "_load_aio_profile",
                api.InvalidProfileDataError("private profile"),
                422,
                "invalid_profile_data",
            ),
        )

        for path, operation_name, error, status, code in cases:
            with self.subTest(path=path, code=code), patch.object(
                api,
                operation_name,
                side_effect=error,
            ):
                response = asyncio.run(
                    routes.handlers[path](JsonRequest(query={"name": "Broken"}))
                )

            self.assertEqual(response["status"], status)
            self.assertEqual(response["payload"]["code"], code)
            serialized = json.dumps(response["payload"])
            for forbidden in ("private", "/home/", "alice"):
                self.assertNotIn(forbidden, serialized)


class ApiWildcardRouteTests(unittest.TestCase):
    def test_route_handler_is_owned_by_the_canonical_factory(self):
        api, routes = load_api_routes()
        handler = routes.handlers["/easyuse_anima/wildcards"]

        self.assertIs(api.get_wildcards_handler, handler)
        self.assertEqual(handler.__name__, "get_wildcards_handler")
        self.assertTrue(
            handler.__module__.endswith(
                ".easyuse_anima.api.routes.wildcards"
            )
        )
        self.assertTrue(handler._easyuse_anima_request_correlation)

    def test_route_keeps_dynamic_payload_seam(self):
        api, routes = load_api_routes()
        payload = {
            "status": "ok",
            "items": ["artist/name"],
            "roots": ["wildcard:1"],
            "sources": [],
        }

        with patch.object(
            api,
            "_wildcards_payload_sync",
            return_value=payload,
        ) as wildcards_payload:
            response = asyncio.run(
                routes.handlers["/easyuse_anima/wildcards"](JsonRequest())
            )

        self.assertEqual(response["status"], 200)
        self.assertEqual(response["payload"], payload)
        wildcards_payload.assert_called_once_with()


class ApiLongTextSettingsRouteTests(unittest.TestCase):
    def test_route_handlers_are_owned_by_the_canonical_factory(self):
        api, routes = load_api_routes()
        cases = (
            (
                "get_long_text_settings_handler",
                "/easyuse_anima/long_text_settings",
            ),
            (
                "save_long_text_settings_handler",
                "/easyuse_anima/long_text_settings/save",
            ),
        )

        for name, path in cases:
            with self.subTest(path=path):
                handler = routes.handlers[path]
                self.assertIs(getattr(api, name), handler)
                self.assertEqual(handler.__name__, name)
                self.assertTrue(
                    handler.__module__.endswith(
                        ".easyuse_anima.api.routes.long_text_settings"
                    )
                )
                self.assertTrue(handler._easyuse_anima_request_correlation)

    def test_get_route_keeps_dynamic_payload_seam(self):
        api, routes = load_api_routes()
        payload = {
            "status": "ok",
            "values": {"naia.pre_prompt": "quality"},
            "settings": {"naia.pre_prompt": "quality"},
        }

        with patch.object(
            api,
            "_get_long_text_settings_payload_sync",
            return_value=payload,
        ) as get_payload:
            response = asyncio.run(
                routes.handlers["/easyuse_anima/long_text_settings"](
                    JsonRequest()
                )
            )

        self.assertEqual(response["status"], 200)
        self.assertEqual(response["payload"], payload)
        get_payload.assert_called_once_with()

    def test_save_route_preserves_wrapped_and_legacy_payloads(self):
        api, routes = load_api_routes()
        handler = routes.handlers["/easyuse_anima/long_text_settings/save"]
        values = {"naia.pre_prompt": "quality"}
        cases = (
            ({"values": values}, values),
            (values, values),
        )

        for request_payload, expected_values in cases:
            with self.subTest(request_payload=request_payload):
                payload = {
                    "status": "ok",
                    "values": expected_values,
                    "settings": expected_values,
                }
                with patch.object(
                    api,
                    "_save_long_text_settings_payload_sync",
                    return_value=payload,
                ) as save_payload:
                    response = asyncio.run(
                        handler(JsonRequest(request_payload))
                    )

                self.assertEqual(response["status"], 200)
                self.assertEqual(response["payload"], payload)
                save_payload.assert_called_once_with(expected_values)


class ApiAutocompleteRouteTests(unittest.TestCase):
    def test_read_only_route_handlers_are_owned_by_the_canonical_factory(self):
        api, routes = load_api_routes()
        cases = (
            ("autocomplete_status_handler", "/easyuse_anima/autocomplete_status"),
            ("autocomplete_handler", "/easyuse_anima/autocomplete"),
        )

        for name, path in cases:
            with self.subTest(path=path):
                handler = routes.handlers[path]
                self.assertIs(getattr(api, name), handler)
                self.assertEqual(handler.__name__, name)
                self.assertTrue(
                    handler.__module__.endswith(
                        ".easyuse_anima.api.routes.autocomplete"
                    )
                )
                self.assertTrue(handler._easyuse_anima_request_correlation)

    def test_search_route_keeps_dynamic_payload_seam_and_category_mapping(self):
        api, routes = load_api_routes()
        handler = routes.handlers["/easyuse_anima/autocomplete"]
        cases = (
            ("artist", "artist"),
            ("artist_or_general", "artist,general"),
            ("general", None),
        )

        for category, expected_filter in cases:
            with self.subTest(category=category):
                with patch.object(
                    api,
                    "_search_autocomplete_payload_sync",
                    return_value={"query": "cat", "results": []},
                ) as search_payload:
                    response = asyncio.run(
                        handler(
                            JsonRequest(
                                query={
                                    "q": "cat",
                                    "limit": "17",
                                    "category": category,
                                }
                            )
                        )
                    )

                self.assertEqual(response["status"], 200)
                search_payload.assert_called_once_with(
                    "cat",
                    "17",
                    expected_filter,
                )

    def test_classify_route_handler_is_owned_by_the_canonical_factory(self):
        api, routes = load_api_routes()
        handler = routes.handlers["/easyuse_anima/classify_prompt"]

        self.assertIs(api.classify_prompt_handler, handler)
        self.assertEqual(handler.__name__, "classify_prompt_handler")
        self.assertTrue(
            handler.__module__.endswith(
                ".easyuse_anima.api.routes.autocomplete"
            )
        )
        self.assertTrue(handler._easyuse_anima_request_correlation)

    def test_classify_route_keeps_dynamic_payload_seam_and_limit_contract(self):
        api, routes = load_api_routes()
        handler = routes.handlers["/easyuse_anima/classify_prompt"]
        cases = (
            ({"text": "cat"}, 240),
            ({"text": "cat", "limit": 17}, 17),
        )

        for payload, expected_limit in cases:
            with self.subTest(payload=payload):
                with patch.object(
                    api,
                    "_classify_prompt_payload_sync",
                    return_value={"tokens": [], "status": {}},
                ) as classify_payload:
                    response = asyncio.run(handler(JsonRequest(payload)))

                self.assertEqual(response["status"], 200)
                classify_payload.assert_called_once_with(
                    "cat",
                    expected_limit,
                )


class ApiTorchCompileDiagnosticsTests(unittest.TestCase):
    def test_route_handler_is_owned_by_the_canonical_factory(self):
        api, routes = load_api_routes()
        handler = routes.handlers["/easyuse_anima/aio/torch-compile/recommend"]

        self.assertIs(api.aio_torch_compile_recommend_handler, handler)
        self.assertEqual(
            handler.__name__,
            "aio_torch_compile_recommend_handler",
        )
        self.assertTrue(
            handler.__module__.endswith(
                ".easyuse_anima.api.routes.aio_torch_compile"
            )
        )
        self.assertTrue(handler._easyuse_anima_request_correlation)

    def test_route_composes_diagnostics_and_policy_with_request_correlation(self):
        api, routes = load_api_routes()
        diagnostics = {
            "schema_version": 1,
            "policy_version": "diagnostics-v1",
            "supported": False,
            "profile": "unsupported",
            "values": {},
            "environment": {"accelerator": "cpu"},
            "reason_codes": ["cuda_unavailable"],
            "warnings": ["recommendation_policy_pending"],
        }
        recommendation = {
            **diagnostics,
            "policy_version": "recommendation-v1",
            "warnings": ["recommendation_unavailable"],
        }
        handler = routes.handlers["/easyuse_anima/aio/torch-compile/recommend"]
        generation_settings = {"prompt": "must not be reflected"}
        request = JsonRequest(
            {
                "generation_settings": generation_settings,
                "resolution": {"width": 1024, "height": 1024},
                "batch_size": 1,
            }
        )

        with (
            patch.object(
                api,
                "_collect_torch_compile_diagnostics",
                return_value=diagnostics,
            ) as collect,
            patch.object(
                api,
                "_recommend_torch_compile",
                return_value=recommendation,
            ) as recommend,
            patch.object(api, "_run_file_io") as file_io,
        ):
            response = asyncio.run(handler(request))

        self.assertEqual(response["status"], 200)
        self.assertEqual(response["payload"], recommendation)
        self.assertIn("X-Request-ID", response.headers)
        collect.assert_called_once_with()
        recommend.assert_called_once_with(
            diagnostics,
            generation_settings,
            {"width": 1024, "height": 1024},
            1,
        )
        file_io.assert_not_called()
        self.assertNotIn("must not be reflected", json.dumps(response["payload"]))

    def test_route_rejects_invalid_workload_contract_before_diagnostics(self):
        api, routes = load_api_routes()
        handler = routes.handlers["/easyuse_anima/aio/torch-compile/recommend"]
        cases = (
            ({"generation_settings": []}, "generation_settings"),
            ({"resolution": []}, "resolution"),
            ({"resolution": {"width": "1024"}}, "width"),
            ({"resolution": {"width": 0}}, "width"),
            ({"resolution": {"height": 16385}}, "height"),
            ({"batch_size": "1"}, "batch_size"),
            ({"batch_size": 0}, "batch_size"),
        )

        with (
            patch.object(api, "_collect_torch_compile_diagnostics") as collect,
            patch.object(api, "_recommend_torch_compile") as recommend,
        ):
            for payload, field in cases:
                with self.subTest(payload=payload):
                    response = asyncio.run(handler(JsonRequest(payload)))
                    self.assertEqual(response["status"], 422)
                    self.assertEqual(response["payload"]["code"], "invalid_request")
                    self.assertEqual(response["payload"]["details"]["field"], field)

        collect.assert_not_called()
        recommend.assert_not_called()


class ApiRequestContractTests(unittest.TestCase):
    POST_ROUTES = (
        "/easyuse_anima/set_setting",
        "/easyuse_anima/long_text_settings/save",
        "/easyuse_anima/classify_prompt",
        "/easyuse_anima/translate_prompt",
        "/easyuse_anima/aio/torch-compile/recommend",
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

    def test_profile_cas_errors_keep_request_correlation_and_safe_details(self):
        api, routes = load_api_routes()
        cases = (
            (428, "profile_precondition_required", "Profile precondition is required"),
            (409, "profile_identity_mismatch", "Profile identity does not match"),
            (409, "profile_revision_conflict", "Profile revision does not match"),
        )

        for status, code, message in cases:
            with self.subTest(code=code), patch.object(
                api,
                "_save_aio_profile",
                side_effect=api.ProfileMutationError(
                    status=status,
                    code=code,
                    message=message,
                    details={"profile": "source"},
                ),
            ):
                response = asyncio.run(
                    routes.handlers["/easyuse_anima/aio_profiles/save"](
                        JsonRequest({"name": "Saved", "settings": {}})
                    )
                )

            self.assertEqual(response.status, status)
            self.assertEqual(response["payload"]["code"], code)
            self.assertEqual(response["payload"]["details"], {"profile": "source"})
            self.assertEqual(
                response["payload"]["request_id"],
                response.headers["X-Request-ID"],
            )
            serialized = json.dumps(response["payload"])
            self.assertNotIn("C:\\", serialized)
            self.assertNotIn("/home/", serialized)
            self.assertNotIn("secret", serialized)

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
                    with patch.object(
                        profile_directory_owner(api, directory_name),
                        directory_name,
                        root,
                    ):
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
                    with patch.object(
                        profile_directory_owner(api, directory_name),
                        directory_name,
                        root,
                    ):
                        response = asyncio.run(
                            routes.handlers[route](JsonRequest(query={"name": "Invalid"}))
                        )
                    self.assertEqual(response["status"], 422)
                    self.assertEqual(response["payload"]["code"], "invalid_profile_data")
                    self.assertEqual(
                        response["payload"]["message"],
                        "Profile data is invalid",
                    )

    def test_invalid_profile_envelope_taxonomy_keeps_422_and_request_id_contract(self):
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
            (
                "/easyuse_anima/lora_profiles/load",
                "LORA_PROFILE_DIR",
                {
                    "version": 2,
                    "profile_id": "12345678-1234-4234-9234-1234567890ab",
                    "profile_data": {},
                },
            ),
            (
                "/easyuse_anima/aio_profiles/load",
                "AIO_PROFILE_DIR",
                {"version": 2, "name": "Incomplete", "settings": {}},
            ),
            (
                "/easyuse_anima/lora_profiles",
                "LORA_PROFILE_DIR",
                {"version": 2, "revision": 1, "profile_data": {}},
            ),
            (
                "/easyuse_anima/aio_profiles",
                "AIO_PROFILE_DIR",
                {"version": 2, "revision": 1, "settings": {}},
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
                        patch.object(
                            profile_directory_owner(api, directory_name),
                            directory_name,
                            root,
                        ),
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
                    with patch.object(
                        profile_directory_owner(api, directory_name),
                        directory_name,
                        root,
                    ):
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

                with patch.object(api._aio_profiles, "AIO_PROFILE_DIR", root):
                    response = asyncio.run(
                        handler(
                            JsonRequest(
                                {
                                    "old_name": "Source",
                                    "new_name": "Target",
                                    "profile_id": api.legacy_profile_id(
                                        api.PROFILE_KIND_AIO,
                                        "Source",
                                    ),
                                    "revision": 0,
                                }
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

            with patch.object(api._lora_profiles, "LORA_PROFILE_DIR", root):
                lora_response = asyncio.run(
                    routes.handlers["/easyuse_anima/lora_profiles/load"](
                        JsonRequest(query={"name": "Empty"})
                    )
                )
            self.assertEqual(lora_response["status"], 200)
            self.assertEqual(lora_response["payload"]["profile"]["profile_data"], {})
            self.assertEqual(lora_response["payload"]["profile"]["profile_count"], 1)

            with patch.object(api._aio_profiles, "AIO_PROFILE_DIR", root):
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
            with patch.object(api._lora_profiles, "LORA_PROFILE_DIR", root):
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

    def test_profile_list_does_not_mask_arbitrary_value_error_as_invalid_request(self):
        api, routes = load_api_routes()
        cases = (
            ("/easyuse_anima/lora_profiles", "_list_lora_profiles"),
            ("/easyuse_anima/aio_profiles", "_list_aio_profiles"),
        )

        for route, operation_name in cases:
            with (
                self.subTest(route=route),
                patch.object(
                    api,
                    operation_name,
                    side_effect=ValueError("storage programming error"),
                ),
                patch.object(api._LOGGER, "exception") as log_exception,
            ):
                response = asyncio.run(routes.handlers[route](JsonRequest()))

            self.assertEqual(response["status"], 500)
            self.assertEqual(response["payload"]["code"], "internal_error")
            self.assertNotEqual(response["payload"]["code"], "invalid_request")
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
