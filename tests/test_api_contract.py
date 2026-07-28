from __future__ import annotations

import ast
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
from unittest.mock import Mock, patch

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


class ApiRouteRegistrationOwnerTests(unittest.TestCase):
    def test_public_facade_delegates_to_the_canonical_router_owner(self):
        api, _routes = load_api_routes(register=False)
        target = RouteRegistry()
        owner = sys.modules[api.register_routes.__module__]

        self.assertTrue(
            api._get_prompt_routes.__module__.endswith(
                ".easyuse_anima.api.router"
            )
        )
        self.assertTrue(
            api.register_routes.__module__.endswith(
                ".easyuse_anima.api.router"
            )
        )
        self.assertEqual(api._get_prompt_routes.__name__, "_get_prompt_routes")
        self.assertEqual(api.register_routes.__name__, "register_routes")
        self.assertEqual(api.register_routes.__code__.co_argcount, 1)
        self.assertTrue(
            api._build_route_signature.__module__.endswith(
                ".easyuse_anima.api.router"
            )
        )
        self.assertTrue(
            api._build_route_definitions.__module__.endswith(
                ".easyuse_anima.api.router"
            )
        )
        self.assertTrue(
            api._build_settings_route_group.__module__.endswith(
                ".easyuse_anima.bootstrap"
            )
        )
        self.assertNotIn(
            "build_settings_route_group",
            sys.modules[api._build_settings_route_group.__module__].__all__,
        )
        self.assertTrue(
            api._build_wildcard_autocomplete_route_group.__module__.endswith(
                ".easyuse_anima.bootstrap"
            )
        )
        self.assertNotIn(
            "build_wildcard_autocomplete_route_group",
            sys.modules[
                api._build_wildcard_autocomplete_route_group.__module__
            ].__all__,
        )
        self.assertTrue(
            api._build_translation_route_handler.__module__.endswith(
                ".easyuse_anima.bootstrap"
            )
        )
        self.assertNotIn(
            "build_translation_route_handler",
            sys.modules[
                api._build_translation_route_handler.__module__
            ].__all__,
        )
        self.assertTrue(
            api._build_translation_route_runtime.__module__.endswith(
                ".easyuse_anima.bootstrap"
            )
        )
        self.assertNotIn(
            "build_translation_route_runtime",
            sys.modules[
                api._build_translation_route_runtime.__module__
            ].__all__,
        )
        self.assertTrue(
            api._build_aio_torch_compile_route_handler.__module__.endswith(
                ".easyuse_anima.bootstrap"
            )
        )
        self.assertNotIn(
            "build_aio_torch_compile_route_handler",
            sys.modules[
                api._build_aio_torch_compile_route_handler.__module__
            ].__all__,
        )
        self.assertTrue(
            api._build_lora_read_route_group.__module__.endswith(
                ".easyuse_anima.bootstrap"
            )
        )
        self.assertNotIn(
            "build_lora_read_route_group",
            sys.modules[api._build_lora_read_route_group.__module__].__all__,
        )
        self.assertTrue(
            api._build_profile_list_route_group.__module__.endswith(
                ".easyuse_anima.bootstrap"
            )
        )
        self.assertNotIn(
            "build_profile_list_route_group",
            sys.modules[
                api._build_profile_list_route_group.__module__
            ].__all__,
        )
        self.assertTrue(
            api._build_profile_route_group.__module__.endswith(
                ".easyuse_anima.bootstrap"
            )
        )
        self.assertNotIn(
            "build_profile_route_group",
            sys.modules[api._build_profile_route_group.__module__].__all__,
        )
        self.assertTrue(
            api._register_route_definitions.__module__.endswith(
                ".easyuse_anima.api.router"
            )
        )
        self.assertEqual(
            api._ROUTE_REGISTRATION_MARKER,
            "_easyuse_anima_registered_routes_v1",
        )
        self.assertEqual(
            api._ROUTE_SIGNATURE,
            api._build_route_signature(api._ROUTE_DEFINITIONS),
        )
        self.assertEqual(
            owner.__all__,
            (
                "ROUTE_REGISTRATION_MARKER",
                "build_route_signature",
                "register_route_definitions",
            ),
        )
        handlers = {
            handler.__name__: handler
            for _method, _path, handler in api._ROUTE_DEFINITIONS
        }
        self.assertEqual(
            api._build_route_definitions(**handlers),
            api._ROUTE_DEFINITIONS,
        )

        with patch.object(
            api,
            "_register_route_definitions",
            return_value=True,
        ) as register:
            self.assertTrue(api.register_routes(target))

        self.assertIs(api.routes, target)
        register.assert_called_once_with(
            target,
            api._ROUTE_DEFINITIONS,
            signature=api._ROUTE_SIGNATURE,
            marker=api._ROUTE_REGISTRATION_MARKER,
        )

    def test_resolver_and_registrar_keep_root_dependencies_late_bound(self):
        api, routes = load_api_routes(register=False)
        replacement_routes = RouteRegistry()
        replacement_server = types.SimpleNamespace(
            PromptServer=types.SimpleNamespace(
                instance=types.SimpleNamespace(routes=replacement_routes)
            )
        )

        with patch.object(api, "server", None):
            self.assertIsNone(api._get_prompt_routes())
        with patch.object(api, "server", replacement_server):
            self.assertIs(api._get_prompt_routes(), replacement_routes)

        with patch.object(api, "web", None):
            self.assertFalse(api.register_routes(routes))
            self.assertIs(api.routes, routes)
        self.assertEqual(routes.registrations, [])

        replacement_definitions = (("get", "/replacement", object()),)
        replacement_signature = (("GET", "/replacement"),)
        with (
            patch.object(api, "_ROUTE_DEFINITIONS", replacement_definitions),
            patch.object(api, "_ROUTE_SIGNATURE", replacement_signature),
            patch.object(
                api,
                "_register_route_definitions",
                return_value=True,
            ) as register,
        ):
            self.assertTrue(api.register_routes(routes))

        register.assert_called_once_with(
            routes,
            replacement_definitions,
            signature=replacement_signature,
            marker=api._ROUTE_REGISTRATION_MARKER,
        )

    def test_signature_mismatch_fails_before_any_registration(self):
        api, _routes = load_api_routes(register=False)
        target = RouteRegistry()
        other_signature = (("GET", "/easyuse_anima/other"),)
        setattr(target, api._ROUTE_REGISTRATION_MARKER, other_signature)

        with self.assertRaisesRegex(
            RuntimeError,
            "route registration signature mismatch",
        ):
            api.register_routes(target)

        self.assertEqual(target.registrations, [])
        self.assertEqual(
            getattr(target, api._ROUTE_REGISTRATION_MARKER),
            other_signature,
        )

    def test_partial_registration_failure_does_not_publish_the_marker(self):
        api, _routes = load_api_routes(register=False)

        class FailingRouteRegistry(RouteRegistry):
            def post(self, path):
                def fail(_handler):
                    raise RuntimeError("registration failed")

                return fail

        target = FailingRouteRegistry()
        definitions = (
            ("get", "/first", object()),
            ("post", "/second", object()),
        )
        signature = api._build_route_signature(definitions)

        with self.assertRaisesRegex(RuntimeError, "registration failed"):
            api._register_route_definitions(
                target,
                definitions,
                signature=signature,
                marker=api._ROUTE_REGISTRATION_MARKER,
            )

        self.assertEqual(target.registrations, [("GET", "/first")])
        self.assertFalse(hasattr(target, api._ROUTE_REGISTRATION_MARKER))


class ApiIntegratedRouteCompositionContractTests(unittest.TestCase):
    ROUTE_CONTRACT = (
        (
            "get",
            "/easyuse_anima/settings",
            "get_settings_handler",
            ".easyuse_anima.api.routes.settings",
        ),
        (
            "post",
            "/easyuse_anima/set_setting",
            "set_setting_handler",
            ".easyuse_anima.api.routes.settings",
        ),
        (
            "get",
            "/easyuse_anima/long_text_settings",
            "get_long_text_settings_handler",
            ".easyuse_anima.api.routes.long_text_settings",
        ),
        (
            "get",
            "/easyuse_anima/wildcards",
            "get_wildcards_handler",
            ".easyuse_anima.api.routes.wildcards",
        ),
        (
            "post",
            "/easyuse_anima/long_text_settings/save",
            "save_long_text_settings_handler",
            ".easyuse_anima.api.routes.long_text_settings",
        ),
        (
            "get",
            "/easyuse_anima/autocomplete_status",
            "autocomplete_status_handler",
            ".easyuse_anima.api.routes.autocomplete",
        ),
        (
            "get",
            "/easyuse_anima/autocomplete",
            "autocomplete_handler",
            ".easyuse_anima.api.routes.autocomplete",
        ),
        (
            "post",
            "/easyuse_anima/classify_prompt",
            "classify_prompt_handler",
            ".easyuse_anima.api.routes.autocomplete",
        ),
        (
            "post",
            "/easyuse_anima/translate_prompt",
            "translate_prompt_handler",
            ".easyuse_anima.api.routes.translation",
        ),
        (
            "post",
            "/easyuse_anima/aio/torch-compile/recommend",
            "aio_torch_compile_recommend_handler",
            ".easyuse_anima.api.routes.aio_torch_compile",
        ),
        (
            "get",
            "/easyuse_anima/lora_preview",
            "lora_preview_handler",
            ".easyuse_anima.api.routes.lora_preview",
        ),
        (
            "get",
            "/easyuse_anima/loras",
            "loras_handler",
            ".easyuse_anima.api.routes.lora_catalog",
        ),
        (
            "get",
            "/easyuse_anima/lora_profiles",
            "lora_profiles_handler",
            ".easyuse_anima.api.routes.profile_lists",
        ),
        (
            "post",
            "/easyuse_anima/lora_profiles/save",
            "save_lora_profile_handler",
            ".easyuse_anima.api.routes.profile_saves",
        ),
        (
            "get",
            "/easyuse_anima/lora_profiles/load",
            "load_lora_profile_handler",
            ".easyuse_anima.api.routes.profile_loads",
        ),
        (
            "get",
            "/easyuse_anima/aio_profiles",
            "aio_profiles_handler",
            ".easyuse_anima.api.routes.profile_lists",
        ),
        (
            "post",
            "/easyuse_anima/aio_profiles/save",
            "save_aio_profile_handler",
            ".easyuse_anima.api.routes.profile_saves",
        ),
        (
            "get",
            "/easyuse_anima/aio_profiles/load",
            "load_aio_profile_handler",
            ".easyuse_anima.api.routes.profile_loads",
        ),
        (
            "post",
            "/easyuse_anima/aio_profiles/delete",
            "delete_aio_profile_handler",
            ".easyuse_anima.api.routes.aio_profile_mutations",
        ),
        (
            "post",
            "/easyuse_anima/aio_profiles/rename",
            "rename_aio_profile_handler",
            ".easyuse_anima.api.routes.aio_profile_mutations",
        ),
        (
            "post",
            "/easyuse_anima/lora_profiles/fix",
            "fix_lora_profile_handler",
            ".easyuse_anima.api.routes.lora_profile_fix",
        ),
    )
    FACTORY_OWNER_BY_ALIAS = {
        "_build_settings_handlers": "build_settings_route_group",
        "_build_long_text_settings_handlers": "build_settings_route_group",
        "_build_wildcards_handler": "build_wildcard_autocomplete_route_group",
        "_build_autocomplete_handlers": "build_wildcard_autocomplete_route_group",
        "_build_classify_prompt_handler": "build_wildcard_autocomplete_route_group",
        "_build_translate_prompt_handler": "build_translation_route_handler",
        "_build_aio_torch_compile_recommend_handler": (
            "build_aio_torch_compile_route_handler"
        ),
        "_build_lora_preview_handler": "build_lora_read_route_group",
        "_build_loras_handler": "build_lora_read_route_group",
        "_build_profile_list_handlers": "build_profile_list_route_group",
        "_build_profile_load_handlers": "build_profile_route_group",
        "_build_profile_save_handlers": "build_profile_route_group",
        "_build_aio_profile_mutation_handlers": "build_profile_route_group",
        "_build_lora_profile_fix_handler": "build_profile_route_group",
    }
    FACTORY_IMPORTS = {
        (
            "api.routes.aio_profile_mutations",
            "build_aio_profile_mutation_handlers",
            "_build_aio_profile_mutation_handlers",
        ),
        (
            "api.routes.aio_torch_compile",
            "build_aio_torch_compile_recommend_handler",
            "_build_aio_torch_compile_recommend_handler",
        ),
        (
            "api.routes.autocomplete",
            "build_autocomplete_handlers",
            "_build_autocomplete_handlers",
        ),
        (
            "api.routes.autocomplete",
            "build_classify_prompt_handler",
            "_build_classify_prompt_handler",
        ),
        (
            "api.routes.long_text_settings",
            "build_long_text_settings_handlers",
            "_build_long_text_settings_handlers",
        ),
        (
            "api.routes.lora_catalog",
            "build_loras_handler",
            "_build_loras_handler",
        ),
        (
            "api.routes.lora_preview",
            "build_lora_preview_handler",
            "_build_lora_preview_handler",
        ),
        (
            "api.routes.lora_profile_fix",
            "build_lora_profile_fix_handler",
            "_build_lora_profile_fix_handler",
        ),
        (
            "api.routes.profile_lists",
            "build_profile_list_handlers",
            "_build_profile_list_handlers",
        ),
        (
            "api.routes.profile_loads",
            "build_profile_load_handlers",
            "_build_profile_load_handlers",
        ),
        (
            "api.routes.profile_saves",
            "build_profile_save_handlers",
            "_build_profile_save_handlers",
        ),
        (
            "api.routes.settings",
            "build_settings_handlers",
            "_build_settings_handlers",
        ),
        (
            "api.routes.translation",
            "build_translate_prompt_handler",
            "_build_translate_prompt_handler",
        ),
        (
            "api.routes.wildcards",
            "build_wildcards_handler",
            "_build_wildcards_handler",
        ),
    }
    ROOT_HELPER_IMPORTS = {
        (
            "easyuse_anima.bootstrap",
            "build_aio_torch_compile_route_handler",
            "_build_aio_torch_compile_route_handler",
        ),
        (
            "easyuse_anima.bootstrap",
            "build_lora_read_route_group",
            "_build_lora_read_route_group",
        ),
        (
            "easyuse_anima.bootstrap",
            "build_profile_list_route_group",
            "_build_profile_list_route_group",
        ),
        (
            "easyuse_anima.bootstrap",
            "build_profile_route_group",
            "_build_profile_route_group",
        ),
        (
            "easyuse_anima.bootstrap",
            "build_settings_route_group",
            "_build_settings_route_group",
        ),
        (
            "easyuse_anima.bootstrap",
            "build_translation_route_handler",
            "_build_translation_route_handler",
        ),
        (
            "easyuse_anima.bootstrap",
            "build_translation_route_runtime",
            "_build_translation_route_runtime",
        ),
        (
            "easyuse_anima.bootstrap",
            "build_wildcard_autocomplete_route_group",
            "_build_wildcard_autocomplete_route_group",
        ),
    }

    @staticmethod
    def _tree(relative_path):
        path = ROOT / relative_path
        return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))

    @staticmethod
    def _from_imports(tree):
        return {
            (node.module or "", alias.name, alias.asname)
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
            for alias in node.names
        }

    @staticmethod
    def _named_calls(tree):
        return [
            node.func.id
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
        ]

    def test_all_21_routes_keep_exact_canonical_factory_identity_and_order(self):
        api, routes = load_api_routes()

        self.assertEqual(len(api._ROUTE_DEFINITIONS), 21)
        for definition, expected in zip(
            api._ROUTE_DEFINITIONS,
            self.ROUTE_CONTRACT,
            strict=True,
        ):
            method, path, handler = definition
            expected_method, expected_path, expected_name, expected_owner = expected
            with self.subTest(path=path):
                self.assertEqual((method, path), (expected_method, expected_path))
                self.assertEqual(handler.__name__, expected_name)
                self.assertTrue(handler.__module__.endswith(expected_owner))
                self.assertTrue(handler._easyuse_anima_request_correlation)
                self.assertIs(routes.handlers[path], handler)

    def test_concrete_factories_are_private_bootstrap_owned_without_backrefs(self):
        root_tree = self._tree("api.py")
        bootstrap_tree = self._tree("easyuse_anima/bootstrap.py")
        router_tree = self._tree("easyuse_anima/api/router.py")
        factory_names = {
            imported_name
            for _module, imported_name, _alias in self.FACTORY_IMPORTS
        }

        bootstrap_factory_imports = {
            imported
            for imported in self._from_imports(bootstrap_tree)
            if imported[1] in factory_names
        }
        self.assertEqual(bootstrap_factory_imports, self.FACTORY_IMPORTS)

        root_factory_imports = {
            imported
            for imported in self._from_imports(root_tree)
            if imported[1] in factory_names
        }
        self.assertEqual(root_factory_imports, set())

        router_route_imports = {
            (node.level, node.module)
            for node in ast.walk(router_tree)
            if isinstance(node, ast.ImportFrom)
            and node.module is not None
            and (
                node.module == "routes"
                or node.module.startswith("routes.")
                or node.module.startswith("api.routes")
            )
        }
        self.assertEqual(router_route_imports, set())

        bootstrap_root_api_imports = {
            (node.level, node.module, alias.name)
            for node in ast.walk(bootstrap_tree)
            if isinstance(node, ast.ImportFrom)
            for alias in node.names
            if node.level >= 2
            and (
                node.module in (None, "api")
                or (node.module is not None and node.module.startswith("api."))
            )
        }
        self.assertEqual(bootstrap_root_api_imports, set())

    def test_each_factory_and_root_composition_helper_has_one_owner_call_site(self):
        root_tree = self._tree("api.py")
        bootstrap_tree = self._tree("easyuse_anima/bootstrap.py")
        root_helper_imports = {
            imported
            for imported in self._from_imports(root_tree)
            if imported[0] == "easyuse_anima.bootstrap"
        }
        self.assertEqual(root_helper_imports, self.ROOT_HELPER_IMPORTS)

        root_calls = self._named_calls(root_tree)
        for _module, _name, alias in self.ROOT_HELPER_IMPORTS:
            with self.subTest(root_helper=alias):
                self.assertEqual(root_calls.count(alias), 1)

        factory_call_owners = {}
        helper_definitions = {
            node.name: node
            for node in bootstrap_tree.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        }
        for helper_name, helper in helper_definitions.items():
            helper_calls = self._named_calls(helper)
            for factory_alias in self.FACTORY_OWNER_BY_ALIAS:
                if factory_alias in helper_calls:
                    factory_call_owners[factory_alias] = helper_name

        self.assertEqual(
            factory_call_owners,
            self.FACTORY_OWNER_BY_ALIAS,
        )
        for helper_name in {
            owner for owner in self.FACTORY_OWNER_BY_ALIAS.values()
        }:
            with self.subTest(bootstrap_helper=helper_name):
                helper = helper_definitions[helper_name]
                self.assertIn(
                    "request_correlated",
                    [argument.arg for argument in helper.args.kwonlyargs],
                )
                self.assertEqual(
                    self._named_calls(helper).count("request_correlated"),
                    1,
                )

        api, _routes = load_api_routes(register=False)
        bootstrap = sys.modules[api._build_profile_route_group.__module__]
        self.assertEqual(bootstrap.__all__, ["initialize", "shutdown"])


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

    def test_root_boundaries_are_owned_by_canonical_responses_builders(self):
        api, _routes = load_api_routes(register=False)
        owner_suffix = ".easyuse_anima.api.responses"

        self.assertTrue(api._error_response.__module__.endswith(owner_suffix))
        self.assertTrue(
            api._contract_error_response.__module__.endswith(owner_suffix)
        )
        self.assertTrue(api._request_correlated.__module__.endswith(owner_suffix))
        self.assertEqual(api._error_response.__name__, "_error_response")
        self.assertEqual(
            api._contract_error_response.__name__,
            "_contract_error_response",
        )
        self.assertEqual(api._request_correlated.__name__, "_request_correlated")
        self.assertEqual(
            sys.modules[api._request_correlated.__module__].__all__,
            (
                "REQUEST_ID_HEADER",
                "error_payload",
                "create_request_id",
                "attach_request_id_header",
                "correlate_response",
            ),
        )

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


class ApiProfileErrorResponseTests(unittest.TestCase):
    def test_profile_error_boundary_is_owned_by_canonical_responses(self):
        api, _routes = load_api_routes(register=False)
        owner = sys.modules[api._profile_error_response.__module__]

        self.assertEqual(
            api._profile_error_response.__name__,
            "_profile_error_response",
        )
        self.assertTrue(
            api._profile_error_response.__module__.endswith(
                ".easyuse_anima.api.responses"
            )
        )
        self.assertEqual(api._profile_error_response.__code__.co_argcount, 1)
        self.assertEqual(
            api._SAFE_PROFILE_VALIDATION_MESSAGES,
            frozenset(
                {
                    "Profile name is required",
                    "Profile name is reserved on Windows",
                    "Invalid profile path",
                    "System profile names are reserved",
                    "Profile settings must be an object",
                    "Profile settings are too large",
                    f"A maximum of {api.MAX_AIO_PROFILES} profiles can be saved",
                }
            ),
        )
        self.assertEqual(
            owner.__all__,
            (
                "REQUEST_ID_HEADER",
                "error_payload",
                "create_request_id",
                "attach_request_id_header",
                "correlate_response",
            ),
        )

    def test_profile_error_boundary_preserves_mapping_order_and_redaction(self):
        api, _routes = load_api_routes(register=False)
        mutation = api.ProfileMutationError(
            status=409,
            code="profile_revision_conflict",
            message="Profile revision does not match",
            details={"profile": "target"},
        )
        invalid_json = json.JSONDecodeError("private", "{", 0)
        invalid_unicode = UnicodeDecodeError("utf-8", b"\xff", 0, 1, "private")
        cases = (
            (
                mutation,
                (
                    409,
                    "profile_revision_conflict",
                    "Profile revision does not match",
                ),
                {"details": {"profile": "target"}},
            ),
            (
                FileExistsError("private"),
                (409, "profile_exists", "Profile already exists"),
                {},
            ),
            (
                FileNotFoundError("private"),
                (404, "profile_not_found", "Profile not found"),
                {},
            ),
            (
                invalid_json,
                (422, "invalid_profile_data", "Profile data is invalid"),
                {},
            ),
            (
                invalid_unicode,
                (422, "invalid_profile_data", "Profile data is invalid"),
                {},
            ),
            (
                api.InvalidProfileDataError("private"),
                (422, "invalid_profile_data", "Profile data is invalid"),
                {},
            ),
            (
                ValueError("Profile name is required"),
                (422, "invalid_request", "Profile name is required"),
                {},
            ),
            (
                ValueError("C:\\private\\secret.json"),
                (422, "invalid_request", "Request validation failed"),
                {},
            ),
        )

        for error, expected_args, expected_kwargs in cases:
            expected_response = object()
            with self.subTest(error=type(error).__name__), patch.object(
                api,
                "_error_response",
                return_value=expected_response,
            ) as error_response:
                response = api._profile_error_response(error)

            self.assertIs(response, expected_response)
            error_response.assert_called_once_with(
                *expected_args,
                **expected_kwargs,
            )

        unexpected = RuntimeError("unexpected")
        with self.assertRaises(RuntimeError) as raised:
            api._profile_error_response(unexpected)
        self.assertIs(raised.exception, unexpected)

    def test_profile_error_boundary_keeps_dynamic_root_dependencies(self):
        api, _routes = load_api_routes(register=False)

        class DynamicMutationError(ValueError):
            status = 428
            code = "dynamic_precondition"
            message = "Dynamic precondition"
            details = {"profile": "dynamic"}

        mutation = DynamicMutationError("private")
        expected_response = object()
        with (
            patch.object(api, "ProfileMutationError", DynamicMutationError),
            patch.object(
                api,
                "_SAFE_PROFILE_VALIDATION_MESSAGES",
                frozenset({"dynamic-safe"}),
            ),
            patch.object(
                api,
                "_error_response",
                return_value=expected_response,
            ) as error_response,
        ):
            response = api._profile_error_response(mutation)
            safe_response = api._profile_error_response(ValueError("dynamic-safe"))

        self.assertIs(response, expected_response)
        self.assertIs(safe_response, expected_response)
        self.assertEqual(
            error_response.call_args_list,
            [
                unittest.mock.call(
                    428,
                    "dynamic_precondition",
                    "Dynamic precondition",
                    details={"profile": "dynamic"},
                ),
                unittest.mock.call(422, "invalid_request", "dynamic-safe"),
            ],
        )


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


class ApiProfileSaveRouteTests(unittest.TestCase):
    def test_route_handlers_are_owned_by_the_canonical_factory(self):
        api, routes = load_api_routes()
        cases = (
            (
                "save_lora_profile_handler",
                "/easyuse_anima/lora_profiles/save",
            ),
            (
                "save_aio_profile_handler",
                "/easyuse_anima/aio_profiles/save",
            ),
        )

        for name, path in cases:
            with self.subTest(path=path):
                handler = routes.handlers[path]
                self.assertIs(getattr(api, name), handler)
                self.assertEqual(handler.__name__, name)
                self.assertTrue(
                    handler.__module__.endswith(
                        ".easyuse_anima.api.routes.profile_saves"
                    )
                )
                self.assertTrue(handler._easyuse_anima_request_correlation)

    def test_routes_keep_dynamic_save_seams_payloads_kwargs_and_success_shape(self):
        api, routes = load_api_routes()
        profile_id = "42345678-1234-4567-89ab-1234567890ab"
        cases = (
            (
                "/easyuse_anima/lora_profiles/save",
                "_save_lora_profile",
                {
                    "name": "Portrait",
                    "overwrite": True,
                    "profile_data": {"1": {"style_prompt": "soft"}},
                    "profile_id": profile_id,
                    "revision": 5,
                },
            ),
            (
                "/easyuse_anima/aio_profiles/save",
                "_save_aio_profile",
                {
                    "name": "Portrait",
                    "overwrite": True,
                    "settings": {"future": {"kept": True}},
                    "profile_id": profile_id,
                    "revision": 5,
                },
            ),
        )

        for path, operation_name, data in cases:
            saved = {
                "name": data["name"],
                "profile_id": profile_id,
                "revision": 6,
            }
            with self.subTest(path=path), patch.object(
                api,
                operation_name,
                return_value=saved,
            ) as save_profile:
                response = asyncio.run(routes.handlers[path](JsonRequest(data)))

            self.assertEqual(response["status"], 200)
            self.assertEqual(
                response["payload"],
                {"status": "ok", "profile": saved},
            )
            save_profile.assert_called_once_with(
                "Portrait",
                data,
                overwrite=True,
                profile_id=profile_id,
                revision=5,
            )

    def test_aio_route_requires_settings_before_file_io(self):
        api, routes = load_api_routes()
        with patch.object(api, "_save_aio_profile") as save_profile:
            response = asyncio.run(
                routes.handlers["/easyuse_anima/aio_profiles/save"](
                    JsonRequest({"name": "Portrait"})
                )
            )

        self.assertEqual(response["status"], 422)
        self.assertEqual(response["payload"]["code"], "invalid_request")
        self.assertEqual(response["payload"]["details"], {"field": "settings"})
        save_profile.assert_not_called()

    def test_routes_preserve_profile_error_mapping_and_redaction(self):
        api, routes = load_api_routes()
        cases = (
            (
                "/easyuse_anima/lora_profiles/save",
                "_save_lora_profile",
                {"name": "Portrait", "profile_data": {}},
                FileNotFoundError("C:\\private\\missing.json"),
                404,
                "profile_not_found",
                None,
            ),
            (
                "/easyuse_anima/aio_profiles/save",
                "_save_aio_profile",
                {"name": "Portrait", "settings": {}},
                FileExistsError("/home/alice/existing.json"),
                409,
                "profile_exists",
                None,
            ),
            (
                "/easyuse_anima/aio_profiles/save",
                "_save_aio_profile",
                {"name": "Portrait", "settings": {}},
                api.ProfileMutationError(
                    status=409,
                    code="profile_revision_conflict",
                    message="Profile revision does not match",
                    details={"profile": "source"},
                ),
                409,
                "profile_revision_conflict",
                {"profile": "source"},
            ),
        )

        for path, operation_name, data, error, status, code, details in cases:
            with self.subTest(path=path, code=code), patch.object(
                api,
                operation_name,
                side_effect=error,
            ):
                response = asyncio.run(routes.handlers[path](JsonRequest(data)))

            self.assertEqual(response["status"], status)
            self.assertEqual(response["payload"]["code"], code)
            if details is not None:
                self.assertEqual(response["payload"]["details"], details)
            serialized = json.dumps(response["payload"])
            for forbidden in ("private", "/home/", "alice"):
                self.assertNotIn(forbidden, serialized)


class ApiAioProfileMutationRouteTests(unittest.TestCase):
    def test_route_handlers_are_owned_by_the_canonical_factory(self):
        api, routes = load_api_routes()
        cases = (
            (
                "delete_aio_profile_handler",
                "/easyuse_anima/aio_profiles/delete",
            ),
            (
                "rename_aio_profile_handler",
                "/easyuse_anima/aio_profiles/rename",
            ),
        )

        for name, path in cases:
            with self.subTest(path=path):
                handler = routes.handlers[path]
                self.assertIs(getattr(api, name), handler)
                self.assertEqual(handler.__name__, name)
                self.assertTrue(
                    handler.__module__.endswith(
                        ".easyuse_anima.api.routes.aio_profile_mutations"
                    )
                )
                self.assertTrue(handler._easyuse_anima_request_correlation)

    def test_routes_keep_dynamic_operation_seams_kwargs_and_success_shape(self):
        api, routes = load_api_routes()
        source_id = "52345678-1234-4567-89ab-1234567890ab"
        target_id = "62345678-1234-4567-89ab-1234567890ab"
        cases = (
            (
                "/easyuse_anima/aio_profiles/delete",
                "_delete_aio_profile",
                {
                    "name": "Portrait",
                    "profile_id": source_id,
                    "revision": 7,
                },
                ("Portrait",),
                {"profile_id": source_id, "revision": 7},
            ),
            (
                "/easyuse_anima/aio_profiles/rename",
                "_rename_aio_profile",
                {
                    "old_name": "Portrait",
                    "new_name": "Portrait 2",
                    "overwrite": True,
                    "profile_id": source_id,
                    "revision": 7,
                    "target_profile_id": target_id,
                    "target_revision": 3,
                },
                ("Portrait", "Portrait 2"),
                {
                    "overwrite": True,
                    "profile_id": source_id,
                    "revision": 7,
                    "target_profile_id": target_id,
                    "target_revision": 3,
                },
            ),
        )

        for path, operation_name, data, expected_args, expected_kwargs in cases:
            changed = {
                "name": data.get("new_name", data.get("name")),
                "profile_id": source_id,
                "revision": 8,
            }
            with self.subTest(path=path), patch.object(
                api,
                operation_name,
                return_value=changed,
            ) as operation:
                response = asyncio.run(routes.handlers[path](JsonRequest(data)))

            self.assertEqual(response["status"], 200)
            self.assertEqual(
                response["payload"],
                {"status": "ok", "profile": changed},
            )
            operation.assert_called_once_with(*expected_args, **expected_kwargs)

    def test_rename_rejects_invalid_target_revision_before_file_io(self):
        api, routes = load_api_routes()
        with patch.object(api, "_rename_aio_profile") as rename_profile:
            response = asyncio.run(
                routes.handlers["/easyuse_anima/aio_profiles/rename"](
                    JsonRequest(
                        {
                            "old_name": "Portrait",
                            "new_name": "Portrait 2",
                            "target_revision": -1,
                        }
                    )
                )
            )

        self.assertEqual(response["status"], 422)
        self.assertEqual(response["payload"]["code"], "invalid_request")
        self.assertEqual(
            response["payload"]["details"],
            {"field": "target_revision"},
        )
        rename_profile.assert_not_called()

    def test_routes_preserve_error_mapping_target_details_and_redaction(self):
        api, routes = load_api_routes()
        cases = (
            (
                "/easyuse_anima/aio_profiles/delete",
                "_delete_aio_profile",
                {"name": "Portrait"},
                FileNotFoundError("C:\\private\\missing.json"),
                404,
                "profile_not_found",
                None,
            ),
            (
                "/easyuse_anima/aio_profiles/rename",
                "_rename_aio_profile",
                {"old_name": "Portrait", "new_name": "Portrait 2"},
                FileExistsError("/home/alice/existing.json"),
                409,
                "profile_exists",
                None,
            ),
            (
                "/easyuse_anima/aio_profiles/rename",
                "_rename_aio_profile",
                {"old_name": "Portrait", "new_name": "Portrait 2"},
                api.ProfileMutationError(
                    status=409,
                    code="profile_revision_conflict",
                    message="Profile revision does not match",
                    details={"profile": "target"},
                ),
                409,
                "profile_revision_conflict",
                {"profile": "target"},
            ),
        )

        for path, operation_name, data, error, status, code, details in cases:
            with self.subTest(path=path, code=code), patch.object(
                api,
                operation_name,
                side_effect=error,
            ):
                response = asyncio.run(routes.handlers[path](JsonRequest(data)))

            self.assertEqual(response["status"], status)
            self.assertEqual(response["payload"]["code"], code)
            if details is not None:
                self.assertEqual(response["payload"]["details"], details)
            serialized = json.dumps(response["payload"])
            for forbidden in ("private", "/home/", "alice"):
                self.assertNotIn(forbidden, serialized)


class ApiLoraProfileFixRouteTests(unittest.TestCase):
    def test_route_handler_is_owned_by_the_canonical_factory(self):
        api, routes = load_api_routes()
        handler = routes.handlers["/easyuse_anima/lora_profiles/fix"]

        self.assertIs(api.fix_lora_profile_handler, handler)
        self.assertEqual(handler.__name__, "fix_lora_profile_handler")
        self.assertTrue(
            handler.__module__.endswith(
                ".easyuse_anima.api.routes.lora_profile_fix"
            )
        )
        self.assertTrue(handler._easyuse_anima_request_correlation)

    def test_route_keeps_dynamic_operation_seam_original_data_and_success_shape(self):
        api, routes = load_api_routes()
        cases = (
            {"profile_count": 1, "profile_index": 1},
            {
                "profile_count": 1,
                "profile_index": 1,
                "profile_data": {"1": {"loras": []}},
                "future": {"kept": True},
            },
        )

        for data in cases:
            changed = {**data, "fixed": [], "unresolved": []}
            before = json.dumps(data, sort_keys=True)
            with self.subTest(profile_data="profile_data" in data), patch.object(
                api,
                "_fix_lora_profile_payload",
                return_value=changed,
            ) as operation:
                response = asyncio.run(
                    routes.handlers["/easyuse_anima/lora_profiles/fix"](
                        JsonRequest(data)
                    )
                )

            self.assertEqual(response["status"], 200)
            self.assertEqual(
                response["payload"],
                {"status": "ok", "profile": changed},
            )
            operation.assert_called_once_with(data)
            self.assertIs(operation.call_args.args[0], data)
            self.assertEqual(json.dumps(data, sort_keys=True), before)

    def test_invalid_profile_data_is_rejected_before_file_io(self):
        api, routes = load_api_routes()
        with (
            patch.object(api, "_fix_lora_profile_payload") as operation,
            patch.object(api, "_run_file_io") as file_io,
        ):
            response = asyncio.run(
                routes.handlers["/easyuse_anima/lora_profiles/fix"](
                    JsonRequest({"profile_data": []})
                )
            )

        self.assertEqual(response["status"], 422)
        self.assertEqual(response["payload"]["code"], "invalid_request")
        self.assertEqual(response["payload"]["details"], {"field": "profile_data"})
        operation.assert_not_called()
        file_io.assert_not_called()

    def test_domain_failure_stays_on_correlated_safe_500_boundary(self):
        api, routes = load_api_routes()
        secret = "C:\\Users\\alice\\profile.json API_TOKEN=top-secret"
        with (
            patch.object(
                api,
                "_fix_lora_profile_payload",
                side_effect=ValueError(secret),
            ),
            patch.object(api._LOGGER, "exception") as log_exception,
        ):
            response = asyncio.run(
                routes.handlers["/easyuse_anima/lora_profiles/fix"](
                    JsonRequest({"profile_data": {}})
                )
            )

        self.assertEqual(response["status"], 500)
        self.assertEqual(response["payload"]["code"], "internal_error")
        self.assertEqual(
            response["payload"]["request_id"],
            response.headers["X-Request-ID"],
        )
        uuid.UUID(response["payload"]["request_id"])
        serialized = json.dumps(response["payload"])
        for forbidden in ("alice", "profile.json", "API_TOKEN", "top-secret"):
            self.assertNotIn(forbidden, serialized)
        log_exception.assert_called_once()


class ApiWildcardRouteTests(unittest.TestCase):
    def test_payload_helper_is_owned_by_the_canonical_factory(self):
        api, _routes = load_api_routes()
        helper = api._wildcards_payload_sync

        self.assertEqual(helper.__name__, "_wildcards_payload_sync")
        self.assertTrue(
            helper.__module__.endswith(
                ".easyuse_anima.api.routes.wildcards"
            )
        )
        self.assertEqual(helper.__code__.co_argcount, 0)
        owner = sys.modules[helper.__module__]
        self.assertEqual(owner.__all__, ("build_wildcards_handler",))

    def test_payload_helper_keeps_dynamic_dependencies_order_and_redaction(self):
        api, _routes = load_api_routes()
        calls = []

        class RootProbe:
            def __init__(self, label, exists):
                self.label = label
                self.exists = exists

            def is_dir(self):
                calls.append(("is_dir", self.label))
                return self.exists

        resolved_roots = [
            RootProbe("private-a", True),
            RootProbe("private-b", False),
        ]
        items = ["artist/name"]
        extra_paths = "C:\\Users\\alice\\wildcards\n/home/alice/wildcards"

        def public_settings():
            calls.append(("settings",))
            return {"wildcard.extra_paths": extra_paths}

        def resolve_wildcard_roots(received):
            calls.append(("resolve", received))
            return resolved_roots

        def list_wildcards(*, roots):
            calls.append(("list", roots))
            return items

        with (
            patch.object(api, "public_settings", side_effect=public_settings),
            patch.object(
                api,
                "resolve_wildcard_roots",
                side_effect=resolve_wildcard_roots,
            ),
            patch.object(api, "list_wildcards", side_effect=list_wildcards),
        ):
            payload = api._wildcards_payload_sync()

        self.assertEqual(
            calls,
            [
                ("settings",),
                ("resolve", extra_paths),
                ("is_dir", "private-a"),
                ("is_dir", "private-b"),
                ("list", resolved_roots),
            ],
        )
        self.assertIs(calls[-1][1], resolved_roots)
        self.assertIs(payload["items"], items)
        self.assertEqual(payload["roots"], ["wildcard:1", "wildcard:2"])
        self.assertEqual(
            payload["sources"],
            [
                {
                    "id": "wildcard:1",
                    "label": "Wildcard source 1",
                    "exists": True,
                },
                {
                    "id": "wildcard:2",
                    "label": "Wildcard source 2",
                    "exists": False,
                },
            ],
        )
        serialized = json.dumps(payload)
        for forbidden in ("alice", "private-a", "private-b", "/home"):
            self.assertNotIn(forbidden, serialized)

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


class ApiSettingsRouteTests(unittest.TestCase):
    def test_payload_helpers_are_owned_by_the_canonical_factory(self):
        api, _routes = load_api_routes()
        cases = (
            ("_get_settings_payload_sync", 0),
            ("_save_setting_payload_sync", 2),
        )

        for name, argument_count in cases:
            with self.subTest(name=name):
                helper = getattr(api, name)
                self.assertEqual(helper.__name__, name)
                self.assertTrue(
                    helper.__module__.endswith(
                        ".easyuse_anima.api.routes.settings"
                    )
                )
                self.assertEqual(helper.__code__.co_argcount, argument_count)

        owner = sys.modules[api._get_settings_payload_sync.__module__]
        self.assertEqual(owner.__all__, ("build_settings_handlers",))

    def test_payload_helpers_keep_dynamic_dependencies_and_merge_order(self):
        api, _routes = load_api_routes()
        get_payload = {"future": {"kept": True}}
        with patch.object(api, "public_settings", return_value=get_payload) as read:
            result = api._get_settings_payload_sync()

        self.assertIs(result, get_payload)
        read.assert_called_once_with()

        calls = []
        saved_settings = {
            "status": "future-status",
            "autocomplete.limit": 37,
        }

        def save_setting(key, value):
            calls.append(("save", key, value))

        def public_settings():
            calls.append(("public",))
            return saved_settings

        with (
            patch.object(api, "save_setting", side_effect=save_setting),
            patch.object(api, "public_settings", side_effect=public_settings),
        ):
            result = api._save_setting_payload_sync(
                "future.setting",
                {"raw": [None, True]},
            )

        self.assertEqual(
            calls,
            [
                ("save", "future.setting", {"raw": [None, True]}),
                ("public",),
            ],
        )
        self.assertEqual(
            result,
            {
                "status": "future-status",
                "autocomplete.limit": 37,
            },
        )
        self.assertIsNot(result, saved_settings)

    def test_route_handlers_are_owned_by_the_canonical_factory(self):
        api, routes = load_api_routes()
        cases = (
            ("get_settings_handler", "/easyuse_anima/settings"),
            ("set_setting_handler", "/easyuse_anima/set_setting"),
        )

        for name, path in cases:
            with self.subTest(path=path):
                handler = routes.handlers[path]
                self.assertIs(getattr(api, name), handler)
                self.assertEqual(handler.__name__, name)
                self.assertTrue(
                    handler.__module__.endswith(
                        ".easyuse_anima.api.routes.settings"
                    )
                )
                self.assertTrue(handler._easyuse_anima_request_correlation)

    def test_get_keeps_dynamic_payload_seam_and_legacy_success_shape(self):
        api, routes = load_api_routes()
        payload = {
            "autocomplete.limit": 20,
            "wildcard.extra_paths": ["D:\\private\\wildcards"],
        }
        with patch.object(
            api,
            "_get_settings_payload_sync",
            return_value=payload,
        ) as get_payload:
            response = asyncio.run(
                routes.handlers["/easyuse_anima/settings"](JsonRequest())
            )

        self.assertEqual(response["status"], 200)
        self.assertIs(response["payload"], payload)
        get_payload.assert_called_once_with()

    def test_set_keeps_dynamic_seam_raw_value_default_and_success_shape(self):
        api, routes = load_api_routes()
        cases = (
            ({"key": "autocomplete.limit"}, ""),
            ({"key": "autocomplete.limit", "value": None}, None),
            (
                {
                    "key": "wildcard.extra_paths",
                    "value": {"future": {"kept": True}},
                },
                {"future": {"kept": True}},
            ),
        )

        for data, expected_value in cases:
            payload = {"status": "ok", "saved": expected_value}
            with self.subTest(data=data), patch.object(
                api,
                "_save_setting_payload_sync",
                return_value=payload,
            ) as save_payload:
                response = asyncio.run(
                    routes.handlers["/easyuse_anima/set_setting"](
                        JsonRequest(data)
                    )
                )

            self.assertEqual(response["status"], 200)
            self.assertIs(response["payload"], payload)
            save_payload.assert_called_once_with(
                data["key"],
                expected_value,
            )

    def test_invalid_key_is_rejected_before_file_io(self):
        api, routes = load_api_routes()
        with (
            patch.object(api, "_save_setting_payload_sync") as save_payload,
            patch.object(api, "_run_file_io") as file_io,
        ):
            response = asyncio.run(
                routes.handlers["/easyuse_anima/set_setting"](
                    JsonRequest({"key": []})
                )
            )

        self.assertEqual(response["status"], 422)
        self.assertEqual(response["payload"]["code"], "invalid_request")
        self.assertEqual(response["payload"]["details"], {"field": "key"})
        save_payload.assert_not_called()
        file_io.assert_not_called()

    def test_unknown_setting_keeps_fixed_422_taxonomy_and_redaction(self):
        api, routes = load_api_routes()
        secret = "C:\\Users\\alice\\settings.json API_TOKEN=top-secret"
        with patch.object(
            api,
            "_save_setting_payload_sync",
            side_effect=KeyError(secret),
        ):
            response = asyncio.run(
                routes.handlers["/easyuse_anima/set_setting"](
                    JsonRequest({"key": "future.setting", "value": secret})
                )
            )

        self.assertEqual(response["status"], 422)
        self.assertEqual(
            response["payload"],
            {
                "status": "error",
                "code": "unknown_setting",
                "message": "Unknown setting",
                "request_id": response.headers["X-Request-ID"],
            },
        )
        serialized = json.dumps(response["payload"])
        for forbidden in ("alice", "settings.json", "API_TOKEN", "top-secret"):
            self.assertNotIn(forbidden, serialized)

    def test_unexpected_save_failure_stays_on_correlated_safe_500_boundary(self):
        api, routes = load_api_routes()
        secret = "C:\\Users\\alice\\settings.json API_TOKEN=top-secret"
        with (
            patch.object(
                api,
                "_save_setting_payload_sync",
                side_effect=ValueError(secret),
            ),
            patch.object(api._LOGGER, "exception") as log_exception,
        ):
            response = asyncio.run(
                routes.handlers["/easyuse_anima/set_setting"](
                    JsonRequest({"key": "future.setting", "value": secret})
                )
            )

        self.assertEqual(response["status"], 500)
        self.assertEqual(response["payload"]["code"], "internal_error")
        self.assertEqual(
            response["payload"]["request_id"],
            response.headers["X-Request-ID"],
        )
        uuid.UUID(response["payload"]["request_id"])
        serialized = json.dumps(response["payload"])
        for forbidden in ("alice", "settings.json", "API_TOKEN", "top-secret"):
            self.assertNotIn(forbidden, serialized)
        log_exception.assert_called_once()


class ApiLongTextSettingsRouteTests(unittest.TestCase):
    def test_payload_helpers_are_owned_by_the_canonical_factory(self):
        api, _routes = load_api_routes()
        cases = (
            ("_get_long_text_settings_payload_sync", 0),
            ("_save_long_text_settings_payload_sync", 1),
        )

        for name, argument_count in cases:
            with self.subTest(name=name):
                helper = getattr(api, name)
                self.assertEqual(helper.__name__, name)
                self.assertTrue(
                    helper.__module__.endswith(
                        ".easyuse_anima.api.routes.long_text_settings"
                    )
                )
                self.assertEqual(helper.__code__.co_argcount, argument_count)

        owner = sys.modules[api._get_long_text_settings_payload_sync.__module__]
        self.assertEqual(owner.__all__, ("build_long_text_settings_handlers",))

    def test_payload_helpers_keep_dynamic_dependencies_call_order_and_identity(self):
        api, _routes = load_api_routes()
        calls = []
        loaded_values = {"naia.pre_prompt": "loaded"}
        public_payload = {"naia.pre_prompt": "loaded", "future": True}

        def load_long_text_settings():
            calls.append(("load",))
            return loaded_values

        def public_settings():
            calls.append(("public",))
            return public_payload

        with (
            patch.object(
                api,
                "load_long_text_settings",
                side_effect=load_long_text_settings,
            ),
            patch.object(api, "public_settings", side_effect=public_settings),
        ):
            result = api._get_long_text_settings_payload_sync()

        self.assertEqual(calls, [("load",), ("public",)])
        self.assertEqual(result["status"], "ok")
        self.assertIs(result["values"], loaded_values)
        self.assertIs(result["settings"], public_payload)

        calls.clear()
        values = {"naia.pre_prompt": {"raw": [None, True]}}
        saved_values = {"naia.pre_prompt": "saved"}

        def save_long_text_settings(received):
            calls.append(("save", received))
            return saved_values

        with (
            patch.object(
                api,
                "save_long_text_settings",
                side_effect=save_long_text_settings,
            ),
            patch.object(api, "public_settings", side_effect=public_settings),
        ):
            result = api._save_long_text_settings_payload_sync(values)

        self.assertEqual(calls, [("save", values), ("public",)])
        self.assertIs(calls[0][1], values)
        self.assertEqual(result["status"], "ok")
        self.assertIs(result["values"], saved_values)
        self.assertIs(result["settings"], public_payload)

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
    def test_root_autocomplete_facades_resolve_the_installed_narrow_port(self):
        api, _routes = load_api_routes()
        port = Mock()
        port.resolve_source.return_value = ("source", object())
        port.available_sources.return_value = [{"key": "source"}]
        port.status.return_value = {"count": 1}
        port.search.return_value = {"results": []}
        port.classify.return_value = {"tokens": []}
        runtime = type("Runtime", (), {"autocomplete": port})()
        path = object()

        with patch.object(api, "_get_runtime", return_value=runtime):
            self.assertEqual(
                api.resolve_autocomplete_source_path("selected")[0],
                "source",
            )
            self.assertEqual(
                api.available_autocomplete_sources("selected"),
                [{"key": "source"}],
            )
            self.assertEqual(api.autocomplete_status(path), {"count": 1})
            self.assertEqual(
                api.search_autocomplete(
                    "cat",
                    limit=17,
                    path=path,
                    category="artist",
                ),
                {"results": []},
            )
            self.assertEqual(
                api.classify_prompt_text("cat", limit=19, path=path),
                {"tokens": []},
            )

        port.resolve_source.assert_called_once_with("selected")
        port.available_sources.assert_called_once_with("selected")
        port.status.assert_called_once_with(path)
        port.search.assert_called_once_with(
            "cat",
            limit=17,
            path=path,
            category="artist",
        )
        port.classify.assert_called_once_with(
            "cat",
            limit=19,
            path=path,
        )

    def test_root_autocomplete_facades_keep_preinitialize_canonical_fallback(self):
        api, _routes = load_api_routes()
        unavailable = RuntimeError(
            "[EasyUseAnima] RuntimeServices has not been installed."
        )
        path = object()

        with (
            patch.object(api, "_get_runtime", side_effect=unavailable),
            patch.object(
                api,
                "_canonical_resolve_autocomplete_source_path",
                return_value=("source", path),
            ) as resolve_source,
            patch.object(
                api,
                "_canonical_available_autocomplete_sources",
                return_value=[{"key": "source"}],
            ) as available_sources,
            patch.object(
                api,
                "_canonical_autocomplete_status",
                return_value={"count": 1},
            ) as status,
            patch.object(
                api,
                "_canonical_search_autocomplete",
                return_value={"results": []},
            ) as search,
            patch.object(
                api,
                "_canonical_classify_prompt_text",
                return_value={"tokens": []},
            ) as classify,
        ):
            self.assertEqual(
                api.resolve_autocomplete_source_path("selected"),
                ("source", path),
            )
            self.assertEqual(
                api.available_autocomplete_sources("selected"),
                [{"key": "source"}],
            )
            self.assertEqual(api.autocomplete_status(path), {"count": 1})
            self.assertEqual(
                api.search_autocomplete("cat", path=path),
                {"results": []},
            )
            self.assertEqual(
                api.classify_prompt_text("cat", path=path),
                {"tokens": []},
            )

        resolve_source.assert_called_once_with("selected")
        available_sources.assert_called_once_with("selected")
        status.assert_called_once_with(path)
        search.assert_called_once_with(
            "cat",
            limit=20,
            path=path,
            category=None,
        )
        classify.assert_called_once_with("cat", limit=240, path=path)

    def test_payload_helpers_are_owned_by_the_canonical_factory(self):
        api, _routes = load_api_routes()
        cases = (
            ("_autocomplete_status_payload_sync", 0),
            ("_public_autocomplete_status", 1),
            ("_public_autocomplete_payload", 1),
            ("_search_autocomplete_payload_sync", 3),
            ("_classify_prompt_payload_sync", 2),
        )

        for name, argcount in cases:
            with self.subTest(name=name):
                helper = getattr(api, name)
                self.assertEqual(helper.__name__, name)
                self.assertTrue(
                    helper.__module__.endswith(
                        ".easyuse_anima.api.routes.autocomplete"
                    )
                )
                self.assertEqual(helper.__code__.co_argcount, argcount)

        owner = sys.modules[api._autocomplete_status_payload_sync.__module__]
        self.assertEqual(
            owner.__all__,
            (
                "build_autocomplete_handlers",
                "build_classify_prompt_handler",
            ),
        )

    def test_public_payload_helpers_copy_and_keep_dynamic_redaction_seam(self):
        api, _routes = load_api_routes()
        future = {"kept": True}
        status = {
            "path": r"C:\Users\alice\secret.csv",
            "exists": True,
            "future": future,
        }

        public_status = api._public_autocomplete_status(status)

        self.assertEqual(
            public_status,
            {"exists": True, "future": future},
        )
        self.assertIs(public_status["future"], future)
        self.assertIn("path", status)
        self.assertEqual(api._public_autocomplete_status(None), {})
        self.assertEqual(api._public_autocomplete_payload(None), {})

        private_status = object()
        produced = {"status": private_status, "future": future}
        redacted = {"redacted": True}
        with patch.object(
            api,
            "_public_autocomplete_status",
            return_value=redacted,
        ) as public_status_helper:
            public_payload = api._public_autocomplete_payload(produced)

        self.assertIsNot(public_payload, produced)
        self.assertIs(public_payload["status"], redacted)
        self.assertIs(public_payload["future"], future)
        self.assertIs(produced["status"], private_status)
        public_status_helper.assert_called_once_with(private_status)

    def test_status_payload_keeps_dependency_order_identity_and_merge_shape(self):
        api, _routes = load_api_routes()
        calls = []
        selected_source = "configured"
        source_key = "resolved"
        path = object()
        future = {"kept": True}
        status = {
            "path": r"C:\Users\alice\secret.csv",
            "count": 5,
            "source": "private-source",
            "source_label": "Private source",
            "sources": ["private-source"],
            "future": future,
        }
        source = {
            "key": source_key,
            "label": "Resolved source",
            "path": "/home/alice/secret.csv",
            "exists": True,
            "selected": True,
            "future": future,
        }

        def resolve_source():
            calls.append(("source",))
            return selected_source

        def resolve_path(source_name):
            calls.append(("path", source_name))
            return source_key, path

        def read_status(status_path):
            calls.append(("status", status_path))
            return status

        def list_sources(selected):
            calls.append(("sources", selected))
            return [source]

        with (
            patch.object(
                api,
                "resolve_autocomplete_source",
                side_effect=resolve_source,
            ),
            patch.object(
                api,
                "resolve_autocomplete_source_path",
                side_effect=resolve_path,
            ),
            patch.object(api, "autocomplete_status", side_effect=read_status),
            patch.object(
                api,
                "available_autocomplete_sources",
                side_effect=list_sources,
            ),
        ):
            payload = api._autocomplete_status_payload_sync()

        self.assertEqual(
            calls,
            [
                ("source",),
                ("path", selected_source),
                ("status", path),
                ("sources", source_key),
            ],
        )
        self.assertEqual(payload["source"], source_key)
        self.assertEqual(payload["source_label"], "Resolved source")
        self.assertEqual(payload["count"], 5)
        self.assertIs(payload["future"], future)
        self.assertEqual(len(payload["sources"]), 1)
        self.assertIsNot(payload["sources"][0], source)
        self.assertNotIn("path", payload["sources"][0])
        self.assertIn("path", status)
        self.assertIn("path", source)

        redacted = {"count": 9}
        with (
            patch.object(
                api,
                "resolve_autocomplete_source",
                return_value=selected_source,
            ),
            patch.object(
                api,
                "resolve_autocomplete_source_path",
                return_value=(source_key, path),
            ),
            patch.object(api, "autocomplete_status", return_value=status),
            patch.object(api, "available_autocomplete_sources", return_value=[]),
            patch.object(
                api,
                "_public_autocomplete_status",
                return_value=redacted,
            ) as public_status_helper,
        ):
            dynamically_redacted = api._autocomplete_status_payload_sync()

        self.assertEqual(dynamically_redacted["count"], 9)
        public_status_helper.assert_called_once_with(status)

    def test_search_payload_keeps_limit_fallback_and_dynamic_public_seam(self):
        api, _routes = load_api_routes()
        selected_source = "configured"
        path = object()
        produced = {"status": {"path": "private"}}
        public = {"status": {}}

        for requested_limit, expected_limit in (
            (None, 37),
            ("bad", 37),
            ("19", 19),
        ):
            calls = []

            def default_limit():
                calls.append(("limit",))
                return 37

            def resolve_source():
                calls.append(("source",))
                return selected_source

            def resolve_path(source_name):
                calls.append(("path", source_name))
                return "resolved", path

            def search(query, *, limit, path: object, category):
                calls.append(("search", query, limit, path, category))
                return produced

            def redact(payload):
                calls.append(("public", payload))
                return public

            with self.subTest(requested_limit=requested_limit):
                with (
                    patch.object(
                        api,
                        "resolve_autocomplete_limit",
                        side_effect=default_limit,
                    ),
                    patch.object(
                        api,
                        "resolve_autocomplete_source",
                        side_effect=resolve_source,
                    ),
                    patch.object(
                        api,
                        "resolve_autocomplete_source_path",
                        side_effect=resolve_path,
                    ),
                    patch.object(api, "search_autocomplete", side_effect=search),
                    patch.object(
                        api,
                        "_public_autocomplete_payload",
                        side_effect=redact,
                    ),
                ):
                    payload = api._search_autocomplete_payload_sync(
                        "cat",
                        requested_limit,
                        "artist,general",
                    )

                self.assertIs(payload, public)
                self.assertEqual(
                    calls,
                    [
                        ("limit",),
                        ("source",),
                        ("path", selected_source),
                        (
                            "search",
                            "cat",
                            expected_limit,
                            path,
                            "artist,general",
                        ),
                        ("public", produced),
                    ],
                )

    def test_classify_payload_keeps_dependency_identity_and_public_seam(self):
        api, _routes = load_api_routes()
        calls = []
        path = object()
        produced = {"status": {"path": "private"}}
        public = {"status": {}}

        def resolve_source():
            calls.append(("source",))
            return "configured"

        def resolve_path(source_name):
            calls.append(("path", source_name))
            return "resolved", path

        def classify(text, *, limit, path: object):
            calls.append(("classify", text, limit, path))
            return produced

        def redact(payload):
            calls.append(("public", payload))
            return public

        with (
            patch.object(
                api,
                "resolve_autocomplete_source",
                side_effect=resolve_source,
            ),
            patch.object(
                api,
                "resolve_autocomplete_source_path",
                side_effect=resolve_path,
            ),
            patch.object(api, "classify_prompt_text", side_effect=classify),
            patch.object(
                api,
                "_public_autocomplete_payload",
                side_effect=redact,
            ),
        ):
            payload = api._classify_prompt_payload_sync("cat", 17)

        self.assertIs(payload, public)
        self.assertEqual(
            calls,
            [
                ("source",),
                ("path", "configured"),
                ("classify", "cat", 17, path),
                ("public", produced),
            ],
        )

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
    def test_root_compatibility_symbols_share_the_canonical_owner_state(self):
        api, _routes = load_api_routes()
        owner = sys.modules[api._run_file_io.__module__]

        self.assertTrue(
            api._run_file_io.__module__.endswith(
                ".easyuse_anima.api.file_io"
            )
        )
        self.assertIs(api._file_io_limiter, owner.file_io_limiter)
        self.assertIs(api._release_file_io_slot, owner.release_file_io_slot)
        self.assertIs(api._run_file_io, owner.run_file_io)
        self.assertIs(api._FILE_IO_LIMITERS_LOCK, owner._FILE_IO_LIMITERS_LOCK)
        self.assertIs(api._FILE_IO_LIMITERS, owner._FILE_IO_LIMITERS)
        self.assertIs(api.asyncio, owner.asyncio)
        self.assertEqual(api.FILE_IO_MAX_IN_FLIGHT, owner.FILE_IO_MAX_IN_FLIGHT)

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
