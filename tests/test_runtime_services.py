from __future__ import annotations

import subprocess
import sys
import unittest
from dataclasses import FrozenInstanceError
from pathlib import Path
from unittest.mock import Mock, patch


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from easyuse_anima import bootstrap, runtime as runtime_module
from easyuse_anima.infrastructure.comfy.provider import DefaultComfyHostProvider
from easyuse_anima.runtime import RuntimeServices, get_runtime, install_runtime


class FakeComfyHostProvider:
    def max_resolution(self) -> int:
        return 16384

    def find_node_class(self, node_id: str) -> type[object] | None:
        return None

    def find_node_mapping_class(self, node_id: str) -> type[object] | None:
        return None

    def find_loaded_node_class(self, node_id: str) -> type[object] | None:
        return None


class RuntimeServicesTests(unittest.TestCase):
    def setUp(self):
        self.runtime_state = patch.object(runtime_module, "_RUNTIME_SERVICES", None)
        self.runtime_state.start()
        self.default_runtime_state = patch.object(bootstrap, "_DEFAULT_RUNTIME", None)
        self.default_runtime_state.start()

    def tearDown(self):
        self.default_runtime_state.stop()
        self.runtime_state.stop()

    @staticmethod
    def make_runtime() -> RuntimeServices:
        return RuntimeServices(comfy=FakeComfyHostProvider())

    def test_runtime_value_is_frozen(self):
        runtime = self.make_runtime()

        with self.assertRaises(FrozenInstanceError):
            runtime.comfy = FakeComfyHostProvider()

    def test_isolated_construction_does_not_install_runtime(self):
        self.make_runtime()

        with self.assertRaisesRegex(
            RuntimeError,
            r"^\[EasyUseAnima\] RuntimeServices has not been installed\.$",
        ):
            get_runtime()

    def test_first_install_is_returned_and_available(self):
        runtime = self.make_runtime()

        self.assertIs(install_runtime(runtime), runtime)
        self.assertIs(get_runtime(), runtime)

    def test_reinstalling_same_runtime_identity_is_safe(self):
        runtime = self.make_runtime()
        install_runtime(runtime)

        self.assertIs(install_runtime(runtime), runtime)
        self.assertIs(get_runtime(), runtime)

    def test_conflicting_runtime_is_rejected_without_replacing_first(self):
        first = self.make_runtime()
        second = self.make_runtime()
        install_runtime(first)

        with self.assertRaisesRegex(
            RuntimeError,
            (
                r"^\[EasyUseAnima\] A different RuntimeServices instance "
                r"is already installed\.$"
            ),
        ):
            install_runtime(second)

        self.assertIs(get_runtime(), first)

    def test_bootstrap_installs_and_reuses_the_default_runtime(self):
        register_routes = Mock(return_value=True)
        initialize_wildcards = Mock(return_value=object())
        host = type("Host", (), {"MAX_RESOLUTION": "8192"})()
        load_comfy_nodes = Mock(return_value=host)

        with patch.object(bootstrap, "_WILDCARDS_INITIALIZED", False):
            bootstrap.initialize(
                register_routes=register_routes,
                initialize_wildcards=initialize_wildcards,
                load_comfy_nodes=load_comfy_nodes,
            )
            first = get_runtime()
            bootstrap.initialize(
                register_routes=register_routes,
                initialize_wildcards=initialize_wildcards,
                load_comfy_nodes=load_comfy_nodes,
            )

        self.assertIs(first, bootstrap._DEFAULT_RUNTIME)
        self.assertIsInstance(first.comfy, DefaultComfyHostProvider)
        self.assertEqual(first.comfy.max_resolution(), 8192)
        self.assertIs(get_runtime(), first)
        load_comfy_nodes.assert_called_once_with()
        self.assertEqual(register_routes.call_count, 2)
        initialize_wildcards.assert_called_once_with()

    def test_bootstrap_rejects_conflicting_runtime_before_startup_callbacks(self):
        runtime = self.make_runtime()
        register_routes = Mock(return_value=True)
        initialize_wildcards = Mock(return_value=object())
        install_runtime(runtime)

        with (
            patch.object(bootstrap, "_WILDCARDS_INITIALIZED", False),
            self.assertRaisesRegex(
                RuntimeError,
                (
                    r"^\[EasyUseAnima\] A different RuntimeServices instance "
                    r"is already installed\.$"
                ),
            ),
        ):
            bootstrap.initialize(
                register_routes=register_routes,
                initialize_wildcards=initialize_wildcards,
            )

        self.assertIs(get_runtime(), runtime)
        register_routes.assert_not_called()
        initialize_wildcards.assert_not_called()

    def test_import_does_not_require_comfyui_host_modules(self):
        script = """
import builtins

real_import = builtins.__import__
forbidden = {"comfy", "folder_paths", "nodes", "server"}

def guarded_import(name, globals=None, locals=None, fromlist=(), level=0):
    if name.split(".", 1)[0] in forbidden:
        raise AssertionError(f"unexpected host import: {name}")
    return real_import(name, globals, locals, fromlist, level)

builtins.__import__ = guarded_import

from easyuse_anima.infrastructure.comfy.provider import ComfyHostProvider
from easyuse_anima.infrastructure.comfy.provider import DefaultComfyHostProvider
from easyuse_anima.runtime import RuntimeServices, get_runtime, install_runtime
from easyuse_anima.bootstrap import initialize
"""
        result = subprocess.run(
            [sys.executable, "-c", script],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
