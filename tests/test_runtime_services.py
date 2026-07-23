from __future__ import annotations

import subprocess
import sys
import unittest
from dataclasses import FrozenInstanceError
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from easyuse_anima import runtime as runtime_module
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

    def tearDown(self):
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
from easyuse_anima.runtime import RuntimeServices, get_runtime, install_runtime
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
