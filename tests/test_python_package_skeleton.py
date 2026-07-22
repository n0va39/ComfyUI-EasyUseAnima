from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKAGE_MODULES = (
    "easyuse_anima",
    "easyuse_anima.aio",
    "easyuse_anima.aio.conditioning",
    "easyuse_anima.aio.first_pass_cache",
    "easyuse_anima.aio.legacy_generation",
    "easyuse_anima.aio.generation_normalization",
    "easyuse_anima.aio.generation_values",
    "easyuse_anima.aio.model_preparation",
    "easyuse_anima.aio.output",
    "easyuse_anima.aio.preview",
    "easyuse_anima.aio.sampling",
    "easyuse_anima.aio.generation_sampling",
    "easyuse_anima.aio.generation_features",
    "easyuse_anima.aio.generation_detailer",
    "easyuse_anima.aio.generation_output",
    "easyuse_anima.aio.generation_migrations",
    "easyuse_anima.aio.generation_settings",
    "easyuse_anima.aio.resources",
    "easyuse_anima.common",
    "easyuse_anima.common.values",
    "easyuse_anima.common.serialization",
    "easyuse_anima.image",
    "easyuse_anima.image.geometry",
    "easyuse_anima.image.sam3",
    "easyuse_anima.infrastructure",
    "easyuse_anima.infrastructure.comfy",
    "easyuse_anima.infrastructure.comfy.capabilities",
    "easyuse_anima.infrastructure.comfy.invocation",
    "easyuse_anima.infrastructure.comfy.resources",
    "easyuse_anima.lora",
    "easyuse_anima.naia",
    "easyuse_anima.nodes",
    "easyuse_anima.nodes.aio_nodes",
    "easyuse_anima.nodes.impact_detailer_nodes",
    "easyuse_anima.nodes.prompt_advanced_nodes",
    "easyuse_anima.nodes.prompt_data_nodes",
    "easyuse_anima.nodes.regional_nodes",
    "easyuse_anima.nodes.sam3_nodes",
    "easyuse_anima.profiles",
    "easyuse_anima.profiles.contract",
    "easyuse_anima.profiles.mutation",
    "easyuse_anima.prompt",
    "easyuse_anima.prompt.advanced",
    "easyuse_anima.prompt.artist_mix",
    "easyuse_anima.prompt.conditioning",
    "easyuse_anima.prompt.data",
    "easyuse_anima.prompt.regional",
)


class PythonPackageSkeletonTests(unittest.TestCase):
    def test_direct_imports_have_empty_surface_and_no_runtime_side_effects(self):
        script = f"""
import importlib
import json
import os
import socket
import sys
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, {str(ROOT)!r})
sys.dont_write_bytecode = True
modules = {json.dumps(PACKAGE_MODULES)}
forbidden_roots = {{
    "aiohttp",
    "comfy",
    "folder_paths",
    "numpy",
    "requests",
    "server",
    "torch",
}}
before = set(sys.modules)

def blocked(name):
    def fail(*_args, **_kwargs):
        raise AssertionError(f"package import attempted {{name}}")
    return fail

with ExitStack() as stack:
    for owner, name in (
        (os, "makedirs"),
        (os, "mkdir"),
        (os, "remove"),
        (os, "rename"),
        (os, "replace"),
        (os, "unlink"),
        (Path, "mkdir"),
        (Path, "rename"),
        (Path, "replace"),
        (Path, "touch"),
        (Path, "unlink"),
        (Path, "write_bytes"),
        (Path, "write_text"),
        (socket, "create_connection"),
        (socket.socket, "connect"),
    ):
        stack.enter_context(patch.object(owner, name, blocked(f"{{owner}}.{{name}}")))
    imported = [importlib.import_module(name) for name in modules]

new_forbidden = sorted(
    root
    for root in forbidden_roots
    if root in sys.modules and root not in before
)
print(json.dumps({{
    "declared_all": [module.__all__ for module in imported],
    "modules": [module.__name__ for module in imported],
    "new_forbidden": new_forbidden,
}}))
"""
        result = subprocess.run(
            [sys.executable, "-I", "-B", "-c", script],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=10,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["modules"], list(PACKAGE_MODULES))
        expected_all = [[] for _ in PACKAGE_MODULES]
        expected_all[PACKAGE_MODULES.index("easyuse_anima.nodes.aio_nodes")] = [
            "EasyUseAnimaInput"
        ]
        self.assertEqual(payload["declared_all"], expected_all)
        self.assertEqual(payload["new_forbidden"], [])


if __name__ == "__main__":
    unittest.main()
