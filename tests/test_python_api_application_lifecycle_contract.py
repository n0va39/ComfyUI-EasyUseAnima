from __future__ import annotations

import ast
import atexit
import copy
import subprocess
import sys
import unittest
from dataclasses import FrozenInstanceError, fields
from pathlib import Path
from unittest.mock import Mock, patch

from tests.test_api_contract import load_api_routes

ROOT = Path(__file__).resolve().parents[1]
APPLICATION_MODULES = (
    "easyuse_anima/api/application.py",
    "easyuse_anima/api/application_compatibility.py",
    "easyuse_anima/api/application_routes.py",
)
APPLICATION_FIELDS = (
    "dependencies",
    "translation_executor",
    "handlers",
    "route_definitions",
    "route_signature",
    "register_routes",
    "compatibility",
)
HANDLER_FIELDS = (
    "get_settings_handler",
    "set_setting_handler",
    "get_long_text_settings_handler",
    "get_wildcards_handler",
    "save_long_text_settings_handler",
    "autocomplete_status_handler",
    "autocomplete_handler",
    "classify_prompt_handler",
    "translate_prompt_handler",
    "aio_torch_compile_recommend_handler",
    "lora_preview_handler",
    "loras_handler",
    "lora_profiles_handler",
    "save_lora_profile_handler",
    "load_lora_profile_handler",
    "aio_profiles_handler",
    "save_aio_profile_handler",
    "load_aio_profile_handler",
    "delete_aio_profile_handler",
    "rename_aio_profile_handler",
    "fix_lora_profile_handler",
)


def _imports(module: str) -> set[str]:
    tree = ast.parse((ROOT / module).read_text(encoding="utf-8-sig"))
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
    return imports


class PythonApiApplicationLifecycleContractTests(unittest.TestCase):
    def test_canonical_modules_are_private_acyclic_and_import_pure(self):
        for module in APPLICATION_MODULES:
            with self.subTest(module=module):
                imports = _imports(module)
                self.assertNotIn("bootstrap", imports)
                self.assertNotIn("api", imports)

        script = """
import atexit
import sys
from unittest.mock import patch

with patch.object(atexit, "register") as register_atexit:
    import easyuse_anima.api.application as application
    import easyuse_anima.api.application_compatibility as compatibility
    import easyuse_anima.api.application_routes as routes
    import easyuse_anima.api.dependencies as dependencies
    import easyuse_anima.bootstrap as bootstrap

assert application.__all__ == ()
assert compatibility.__all__ == ()
assert routes.__all__ == ()
assert application._APPLICATION is None
assert dependencies._APPLICATION_DEPENDENCIES is None
assert bootstrap._TRANSLATION_ROUTE_EXECUTOR is None
assert bootstrap._DEFAULT_RUNTIME is None
assert bootstrap._ATEXIT_REGISTERED is False
assert "api" not in sys.modules
register_atexit.assert_not_called()
"""
        result = subprocess.run(
            [sys.executable, "-B", "-X", "utf8", "-c", script],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr or result.stdout)

    def test_root_aliases_one_frozen_application_and_exact_handler_order(self):
        api, _routes = load_api_routes(register=False)
        application = api._APPLICATION
        owner = sys.modules[type(application).__module__]

        self.assertIs(owner._APPLICATION, application)
        self.assertIs(application.dependencies, api._APPLICATION_DEPENDENCIES)
        self.assertIs(application.translation_executor, api._PROMPT_TRANSLATION_WORKER)
        self.assertIs(application.route_definitions, api._ROUTE_DEFINITIONS)
        self.assertIs(application.route_signature, api._ROUTE_SIGNATURE)
        self.assertIs(application.register_routes, api.register_routes)
        self.assertEqual(tuple(field.name for field in fields(application)), APPLICATION_FIELDS)
        self.assertEqual(
            tuple(field.name for field in fields(application.handlers)),
            HANDLER_FIELDS,
        )
        self.assertEqual(len(application.route_definitions), 21)
        for name in HANDLER_FIELDS:
            with self.subTest(handler=name):
                self.assertIs(getattr(api, name), getattr(application.handlers, name))
        with self.assertRaises(FrozenInstanceError):
            application.translation_executor = object()

    def test_publish_once_and_bootstrap_composition_use_exact_identities(self):
        api, _routes = load_api_routes(register=False)
        application = api._APPLICATION
        owner = sys.modules[type(application).__module__]
        bootstrap = sys.modules[api._compose_api_application.__module__]

        self.assertIs(owner._publish_application(application), application)
        with self.assertRaisesRegex(RuntimeError, "API application already installed"):
            owner._publish_application(copy.copy(application))

        sentinel = object()
        with patch.object(bootstrap, "_build_api_application", return_value=sentinel) as build:
            self.assertIs(
                bootstrap._compose_api_application(
                    logger=api._LOGGER,
                    publish_routes=api._publish_routes,
                ),
                sentinel,
            )
        build.assert_called_once_with(
            logger=api._LOGGER,
            publish_routes=api._publish_routes,
            build_settings_route_group=bootstrap.build_settings_route_group,
            build_wildcard_autocomplete_route_group=(
                bootstrap.build_wildcard_autocomplete_route_group
            ),
            build_translation_route_runtime=bootstrap.build_translation_route_runtime,
            build_translation_route_handler=bootstrap.build_translation_route_handler,
            build_aio_torch_compile_route_handler=(
                bootstrap.build_aio_torch_compile_route_handler
            ),
            build_lora_read_route_group=bootstrap.build_lora_read_route_group,
            build_profile_list_route_group=bootstrap.build_profile_list_route_group,
            build_profile_route_group=bootstrap.build_profile_route_group,
        )

    def test_executor_is_bootstrap_identity_and_cleanup_item_one(self):
        api, routes = load_api_routes(register=False)
        bootstrap = sys.modules[api._compose_api_application.__module__]
        runtime_module = sys.modules[api._get_runtime.__module__]
        try:
            with patch.object(atexit, "register"):
                bootstrap.initialize(
                    register_routes=api.register_routes,
                    initialize_wildcards=Mock(return_value=object()),
                )
            runtime = runtime_module.get_runtime()
            executor = api._APPLICATION.translation_executor

            self.assertIs(bootstrap._TRANSLATION_ROUTE_EXECUTOR, executor)
            self.assertEqual(len(runtime._cleanup_plan._callbacks), 7)
            self.assertIs(runtime._cleanup_plan._callbacks[0].__self__, executor)
            self.assertEqual(len(routes.registrations), 21)
        finally:
            bootstrap.shutdown()


if __name__ == "__main__":
    unittest.main()
