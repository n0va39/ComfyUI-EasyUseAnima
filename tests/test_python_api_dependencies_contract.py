from __future__ import annotations

import ast
import asyncio
import copy
import importlib.util
import sys
import unittest
from dataclasses import fields
from pathlib import Path
from unittest.mock import patch

from tests.test_api_contract import JsonRequest, RouteRegistry, load_api_routes

ROOT = Path(__file__).resolve().parents[1]


class PythonApiDependenciesContractTests(unittest.TestCase):
    EXPECTED_LEAVES = {
        "host": (
            "server",
            "web",
            "get_prompt_routes",
            "route_definitions",
            "route_signature",
            "register_route_definitions",
        ),
        "request": (
            "create_request_id",
            "run_file_io",
            "error_response",
            "contract_error_response",
            "profile_error_response",
            "profile_mutation_error_type",
            "safe_profile_validation_messages",
        ),
        "settings": (
            "public_settings",
            "save_setting",
            "load_long_text_settings",
            "save_long_text_settings",
            "get_settings_payload",
            "save_setting_payload",
            "get_long_text_settings_payload",
            "save_long_text_settings_payload",
        ),
        "wildcard_autocomplete": (
            "get_runtime",
            "resolve_wildcard_roots",
            "list_wildcards",
            "resolve_autocomplete_source",
            "resolve_autocomplete_source_path",
            "resolve_autocomplete_limit",
            "available_autocomplete_sources",
            "autocomplete_status",
            "search_autocomplete",
            "classify_prompt_text",
            "wildcards_payload",
            "autocomplete_status_payload",
            "search_autocomplete_payload",
            "classify_prompt_payload",
            "public_autocomplete_status",
            "public_autocomplete_payload",
        ),
        "profiles": (
            "list_loras",
            "list_lora_profiles",
            "list_aio_profiles",
            "load_lora_profile",
            "load_aio_profile",
            "save_lora_profile",
            "save_aio_profile",
            "delete_aio_profile",
            "rename_aio_profile",
            "fix_lora_profile_payload",
            "resolve_lora_preview_path",
        ),
        "translation": (
            "translate_prompt_markers",
            "resolve_prompt_translation_settings",
            "route_timeout_seconds",
            "prompt_translation_error_type",
            "prompt_translation_error_response",
        ),
        "torch_compile": (
            "collect_diagnostics",
            "recommend_torch_compile",
        ),
    }

    def test_canonical_module_is_private_import_pure_and_initially_unbound(self):
        source_path = ROOT / "easyuse_anima" / "api" / "dependencies.py"
        tree = ast.parse(source_path.read_text(encoding="utf-8"))
        imports = {
            alias.name
            for node in tree.body
            if isinstance(node, ast.Import)
            for alias in node.names
        }
        imports.update(
            node.module
            for node in tree.body
            if isinstance(node, ast.ImportFrom) and node.module is not None
        )
        self.assertEqual(
            imports,
            {"__future__", "collections.abc", "dataclasses", "typing"},
        )

        module_name = "easyuse_anima_api_dependencies_import_probe"
        spec = importlib.util.spec_from_file_location(module_name, source_path)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        try:
            spec.loader.exec_module(module)
            self.assertEqual(module.__all__, ())
            self.assertIsNone(module._APPLICATION_DEPENDENCIES)
        finally:
            sys.modules.pop(module_name, None)

    def test_bundle_has_exact_typed_families_and_leaf_inventory(self):
        api, _routes = load_api_routes(register=False)
        dependencies = api._APPLICATION_DEPENDENCIES

        self.assertEqual(
            tuple(field.name for field in fields(dependencies)),
            tuple(self.EXPECTED_LEAVES),
        )
        for family_name, expected_leaves in self.EXPECTED_LEAVES.items():
            with self.subTest(family=family_name):
                family = getattr(dependencies, family_name)
                self.assertEqual(
                    tuple(field.name for field in fields(family)),
                    expected_leaves,
                )

    def test_root_and_canonical_cell_share_one_publish_once_identity(self):
        api, _routes = load_api_routes(register=False)
        dependencies = api._APPLICATION_DEPENDENCIES
        owner = sys.modules[type(dependencies).__module__]

        self.assertIs(owner._APPLICATION_DEPENDENCIES, dependencies)
        self.assertIs(owner._publish_application_dependencies(dependencies), dependencies)
        with self.assertRaisesRegex(
            RuntimeError,
            "API application dependencies already installed",
        ):
            owner._publish_application_dependencies(copy.copy(dependencies))
        self.assertIs(owner._APPLICATION_DEPENDENCIES, dependencies)

    def test_request_and_registration_consumers_observe_named_leaves_at_call_time(self):
        api, routes = load_api_routes()
        dependencies = api._APPLICATION_DEPENDENCIES
        request_id = "12345678-1234-4567-89ab-1234567890ab"
        payload = {"future": {"kept": True}}

        with (
            patch.object(api, "_APPLICATION_DEPENDENCIES", object()),
            patch.object(
                dependencies.request,
                "create_request_id",
                return_value=request_id,
            ),
            patch.object(
                dependencies.settings,
                "get_settings_payload",
                return_value=payload,
            ),
        ):
            response = asyncio.run(
                routes.handlers["/easyuse_anima/settings"](JsonRequest())
            )

        self.assertEqual(response["payload"], payload)
        self.assertEqual(response.headers["X-Request-ID"], request_id)

        target = RouteRegistry()
        definitions = (("get", "/replacement", object()),)
        signature = (("GET", "/replacement"),)
        with (
            patch.object(dependencies.host, "route_definitions", definitions),
            patch.object(dependencies.host, "route_signature", signature),
            patch.object(
                dependencies.host,
                "register_route_definitions",
                return_value=True,
            ) as register,
        ):
            self.assertTrue(api.register_routes(target))

        register.assert_called_once_with(
            target,
            definitions,
            signature=signature,
            marker=api._ROUTE_REGISTRATION_MARKER,
        )


if __name__ == "__main__":
    unittest.main()
