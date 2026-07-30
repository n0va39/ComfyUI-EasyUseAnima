from __future__ import annotations

import atexit
import importlib
import importlib.util
import sys
import types
import unittest
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
PACKAGE_NAME = "_easyuse_anima_entrypoint_lifecycle_contract"


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
    node_class = type("EasyUseAnimaTestNode", (), {})
    module.NODE_CLASS_MAPPINGS = {"EasyUseAnimaTestNode": node_class}
    module.NODE_DISPLAY_NAME_MAPPINGS = {
        "EasyUseAnimaTestNode": "EasyUse Anima Test Node"
    }
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
    host_nodes = types.ModuleType("nodes")
    host_nodes.MAX_RESOLUTION = 16384
    bootstrap = None

    try:
        with (
            patch.dict(
                sys.modules,
                {"aiohttp": aiohttp, "nodes": host_nodes, "server": server},
            ),
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
                yield package, routes, register_atexit, bootstrap
    finally:
        try:
            if bootstrap is not None:
                bootstrap.shutdown()
        finally:
            for name in list(sys.modules):
                if name == PACKAGE_NAME or name.startswith(prefix):
                    sys.modules.pop(name, None)


class PythonEntrypointLifecycleContractTests(unittest.TestCase):
    def test_entrypoint_uses_one_canonical_application_and_runtime(self):
        with _loaded_package_entrypoint() as (
            package,
            routes,
            register_atexit,
            bootstrap,
        ):
            application_owner = importlib.import_module(
                f"{PACKAGE_NAME}.easyuse_anima.api.application"
            )
            runtime_owner = importlib.import_module(
                f"{PACKAGE_NAME}.easyuse_anima.runtime"
            )
            application = application_owner._get_application()
            runtime = runtime_owner.get_runtime()
            cleanup_plan = runtime._cleanup_plan
            executor = application.translation_executor
            registrations = tuple(routes.registrations)

            self.assertEqual(
                package.__all__,
                [
                    "NODE_CLASS_MAPPINGS",
                    "NODE_DISPLAY_NAME_MAPPINGS",
                    "WEB_DIRECTORY",
                ],
            )
            self.assertNotIn("api", vars(package))
            self.assertFalse(hasattr(package, "EasyUseAnimaTestNode"))
            self.assertEqual(len(registrations), 21)
            self.assertIs(bootstrap._TRANSLATION_ROUTE_EXECUTOR, executor)
            self.assertEqual(len(cleanup_plan._callbacks), 7)
            self.assertIs(cleanup_plan._callbacks[0].__self__, executor)
            register_atexit.assert_called_once_with(bootstrap.shutdown)

            bootstrap._initialize_package()

            self.assertIs(application_owner._get_application(), application)
            self.assertIs(runtime_owner.get_runtime(), runtime)
            self.assertIs(runtime._cleanup_plan, cleanup_plan)
            self.assertEqual(tuple(routes.registrations), registrations)
            register_atexit.assert_called_once_with(bootstrap.shutdown)

            with self.assertRaises(ModuleNotFoundError):
                importlib.import_module(f"{PACKAGE_NAME}.api")


if __name__ == "__main__":
    unittest.main()
