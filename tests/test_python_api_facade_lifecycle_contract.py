from __future__ import annotations

import atexit
import importlib
import importlib.util
import sys
import types
import unittest
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import Mock, patch


ROOT = Path(__file__).resolve().parents[1]
PACKAGE_NAME = "_easyuse_anima_api_facade_lifecycle_contract"
MAPPED_CLASS_NAMES = (
    "EasyUseAnimaAIOGenerator",
    "EasyUseAnimaArtistMixConditioning",
    "EasyUseAnimaDetailerAlignHook",
    "EasyUseAnimaImageScaleByMultiple",
    "EasyUseAnimaInput",
    "EasyUseAnimaLoraPreset",
    "EasyUseAnimaNAIARandomPrompt",
    "EasyUseAnimaPromptBuilder",
    "EasyUseAnimaPromptCorrector",
    "EasyUseAnimaPromptCorrectorSimple",
    "EasyUseAnimaPromptDataConditioning",
    "EasyUseAnimaPromptDataUnpack",
    "EasyUseAnimaPromptStudio",
    "EasyUseAnimaPromptStudioAdvanced",
    "EasyUseAnimaPromptStudioAdvancedV2",
    "EasyUseAnimaPromptStudioRegional",
    "EasyUseAnimaRegionalConditioning",
    "EasyUseAnimaWildcard",
)


class _RouteRegistry:
    def __init__(self) -> None:
        self.registrations: list[tuple[str, str, object]] = []

    def get(self, path: str):
        return self._decorator("GET", path)

    def post(self, path: str):
        return self._decorator("POST", path)

    def _decorator(self, method: str, path: str):
        def register(handler):
            self.registrations.append((method, path, handler))
            return handler

        return register


class _Response:
    pass


def _registration_stub() -> types.ModuleType:
    module = types.ModuleType(f"{PACKAGE_NAME}.easyuse_anima.registration")
    mapped_classes = {}
    for name in MAPPED_CLASS_NAMES:
        value = type(name, (), {})
        setattr(module, name, value)
        mapped_classes[name] = value
    module.NODE_CLASS_MAPPINGS = mapped_classes
    module.NODE_DISPLAY_NAME_MAPPINGS = {}
    return module


@contextmanager
def _loaded_package_entrypoint():
    prefix = f"{PACKAGE_NAME}."
    if any(name == PACKAGE_NAME or name.startswith(prefix) for name in sys.modules):
        raise AssertionError(f"Synthetic package namespace is already loaded: {PACKAGE_NAME}")

    spec = importlib.util.spec_from_file_location(
        PACKAGE_NAME,
        ROOT / "__init__.py",
        submodule_search_locations=[str(ROOT)],
    )
    if spec is None or spec.loader is None:
        raise AssertionError("Could not create package entrypoint spec")
    package = importlib.util.module_from_spec(spec)
    sys.modules[PACKAGE_NAME] = package
    sys.modules[f"{PACKAGE_NAME}.easyuse_anima.registration"] = _registration_stub()

    routes = _RouteRegistry()
    server = types.ModuleType("server")
    server.PromptServer = type(
        "PromptServer",
        (),
        {"instance": types.SimpleNamespace(routes=routes)},
    )
    web = types.SimpleNamespace(
        FileResponse=_Response,
        HTTPException=Exception,
        Response=_Response,
        json_response=lambda payload, status=200: (payload, status),
    )
    aiohttp = types.ModuleType("aiohttp")
    aiohttp.web = web
    bootstrap = None

    try:
        with (
            patch.dict(sys.modules, {"aiohttp": aiohttp, "server": server}),
            patch.object(atexit, "register") as register_atexit,
        ):
            wildcard_sources = importlib.import_module(
                f"{PACKAGE_NAME}.easyuse_anima.wildcard.sources"
            )
            with patch.object(
                wildcard_sources,
                "ensure_default_wildcard_root",
                return_value=object(),
            ):
                spec.loader.exec_module(package)
            bootstrap = sys.modules[f"{PACKAGE_NAME}.easyuse_anima.bootstrap"]
            yield package, routes, register_atexit
    finally:
        try:
            if bootstrap is not None:
                bootstrap.shutdown()
        finally:
            for name in list(sys.modules):
                if name == PACKAGE_NAME or name.startswith(prefix):
                    sys.modules.pop(name, None)


class PythonApiFacadeLifecycleContractTests(unittest.TestCase):
    def test_package_then_late_api_import_reuses_every_application_identity(self):
        with _loaded_package_entrypoint() as (package, routes, register_atexit):
            api = package.api
            bootstrap = sys.modules[f"{PACKAGE_NAME}.easyuse_anima.bootstrap"]
            runtime_module = sys.modules[f"{PACKAGE_NAME}.easyuse_anima.runtime"]
            translation_service = sys.modules[
                f"{PACKAGE_NAME}.easyuse_anima.translation.service"
            ]

            runtime = runtime_module.get_runtime()
            cleanup_plan = runtime._cleanup_plan
            executor = api._PROMPT_TRANSLATION_WORKER
            handlers = tuple(
                handler for _method, _path, handler in api._ROUTE_DEFINITIONS
            )
            definitions = api._ROUTE_DEFINITIONS
            registrar = api.register_routes
            marker = getattr(routes, api._ROUTE_REGISTRATION_MARKER)
            registrations = tuple(routes.registrations)

            self.assertIs(bootstrap._TRANSLATION_ROUTE_EXECUTOR, executor)
            self.assertEqual(len(cleanup_plan._callbacks), 7)
            self.assertIs(cleanup_plan._callbacks[0].__self__, executor)
            self.assertIs(
                translation_service._DEFAULT_TRANSLATION_SERVICE,
                runtime.translation,
            )
            self.assertEqual(len(registrations), 21)
            register_atexit.assert_called_once_with(bootstrap.shutdown)

            late_api = importlib.import_module(f"{PACKAGE_NAME}.api")

            self.assertIs(late_api, api)
            self.assertIs(late_api._PROMPT_TRANSLATION_WORKER, executor)
            self.assertIs(late_api._ROUTE_DEFINITIONS, definitions)
            self.assertEqual(
                tuple(handler for _method, _path, handler in late_api._ROUTE_DEFINITIONS),
                handlers,
            )
            self.assertIs(late_api.register_routes, registrar)
            self.assertIs(runtime_module.get_runtime(), runtime)
            self.assertIs(runtime._cleanup_plan, cleanup_plan)
            self.assertEqual(tuple(routes.registrations), registrations)
            self.assertEqual(getattr(routes, api._ROUTE_REGISTRATION_MARKER), marker)
            register_atexit.assert_called_once_with(bootstrap.shutdown)

            bootstrap.initialize(
                register_routes=late_api.register_routes,
                initialize_wildcards=Mock(return_value=object()),
            )

            self.assertIs(runtime_module.get_runtime(), runtime)
            self.assertEqual(tuple(routes.registrations), registrations)
            register_atexit.assert_called_once_with(bootstrap.shutdown)


if __name__ == "__main__":
    unittest.main()
