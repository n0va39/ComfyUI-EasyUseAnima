from __future__ import annotations

import re
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch

from easyuse_anima import runtime as runtime_module
from easyuse_anima.infrastructure.comfy.wiring import resolve_comfy_host_helper
from easyuse_anima.runtime import RuntimeServices
from tests.comfy_host_fakes import FakeComfyHostProvider


class ClipTextEncode:
    def encode(self, clip, text):
        return (f"{clip}:{text}",)


class ComfyHostWiringTests(unittest.TestCase):
    def setUp(self):
        self.runtime_state = patch.object(runtime_module, "_RUNTIME_SERVICES", None)
        self.runtime_state.start()

    def tearDown(self):
        self.runtime_state.stop()

    @staticmethod
    def _fallback(name: str):
        return lambda *args: (name, args)

    def test_unknown_helper_uses_fallback_without_installed_runtime(self):
        helper = resolve_comfy_host_helper("_other_helper", self._fallback)

        self.assertEqual(helper(1, 2), ("_other_helper", (1, 2)))

    def test_runtime_access_stays_in_runtime_and_comfy_wiring_adapter(self):
        package_root = Path(__file__).resolve().parents[1] / "easyuse_anima"
        access_files = {
            path.relative_to(package_root.parent).as_posix()
            for path in package_root.rglob("*.py")
            if re.search(r"\bget_runtime\b", path.read_text(encoding="utf-8"))
        }

        self.assertEqual(
            access_files,
            {
                "easyuse_anima/infrastructure/comfy/wiring.py",
                "easyuse_anima/runtime.py",
            },
        )

    def test_known_helper_uses_flat_import_fallback_before_runtime_install(self):
        helper = resolve_comfy_host_helper(
            "_find_comfy_node_class",
            self._fallback,
        )

        self.assertEqual(
            helper("Example"),
            ("_find_comfy_node_class", ("Example",)),
        )

    def test_retired_max_resolution_uses_default_provider_before_runtime_install(self):
        comfy_nodes = types.ModuleType("nodes")
        comfy_nodes.MAX_RESOLUTION = "8192"

        def unexpected_fallback(name: str):
            self.fail(f"retired helper reached root fallback: {name}")

        with patch.dict(sys.modules, {"nodes": comfy_nodes}):
            helper = resolve_comfy_host_helper(
                "_comfy_max_resolution",
                unexpected_fallback,
            )

            self.assertEqual(helper(), 8192)

    def test_retired_mapping_lookup_uses_default_provider_before_runtime_install(self):
        mapping_class = object()
        comfy_nodes = types.ModuleType("nodes")
        comfy_nodes.NODE_CLASS_MAPPINGS = {"MappingOnly": mapping_class}
        comfy_nodes.MappingOnly = object()

        def unexpected_fallback(name: str):
            self.fail(f"retired helper reached root fallback: {name}")

        with patch.dict(sys.modules, {"nodes": comfy_nodes}):
            helper = resolve_comfy_host_helper(
                "_find_comfy_node_mapping_class",
                unexpected_fallback,
            )

            self.assertIs(helper("MappingOnly"), mapping_class)
            comfy_nodes.NODE_CLASS_MAPPINGS = {}
            self.assertIsNone(helper("MappingOnly"))
            comfy_nodes.NODE_CLASS_MAPPINGS = object()
            self.assertIsNone(helper("MappingOnly"))

    def test_retired_loaded_lookup_uses_default_provider_before_runtime_install(self):
        direct_class = object()
        loaded_class = object()
        comfy_nodes = types.ModuleType("nodes")
        comfy_nodes.NODE_CLASS_MAPPINGS = {"Direct": direct_class}
        loaded_nodes = types.ModuleType("easyuse_anima_test_loaded_nodes")
        loaded_nodes.NODE_CLASS_MAPPINGS = {"Loaded": loaded_class}

        def unexpected_fallback(name: str):
            self.fail(f"retired helper reached root fallback: {name}")

        with patch.dict(
            sys.modules,
            {
                "nodes": comfy_nodes,
                loaded_nodes.__name__: loaded_nodes,
            },
        ):
            helper = resolve_comfy_host_helper(
                "_find_loaded_node_class",
                unexpected_fallback,
            )

            self.assertIs(helper("Direct"), direct_class)
            comfy_nodes.NODE_CLASS_MAPPINGS = {}
            self.assertIs(helper("Loaded"), loaded_class)
            loaded_nodes.NODE_CLASS_MAPPINGS = {}
            self.assertIsNone(helper("Missing"))

    def test_provider_owned_helpers_delegate_to_narrow_methods(self):
        direct = object()
        mapping = object()
        loaded = object()
        provider = FakeComfyHostProvider(
            max_resolution=8192,
            node_classes={"Direct": direct},
            mapping_classes={"Mapping": mapping},
            loaded_classes={"Loaded": loaded},
        )
        runtime_module._RUNTIME_SERVICES = RuntimeServices(comfy=provider)

        self.assertEqual(
            resolve_comfy_host_helper(
                "_comfy_max_resolution",
                self._fallback,
            )(),
            8192,
        )
        self.assertIs(
            resolve_comfy_host_helper(
                "_find_comfy_node_class",
                self._fallback,
            )("Direct"),
            direct,
        )
        self.assertIs(
            resolve_comfy_host_helper(
                "_find_comfy_node_mapping_class",
                self._fallback,
            )("Mapping"),
            mapping,
        )
        self.assertIs(
            resolve_comfy_host_helper(
                "_find_loaded_node_class",
                self._fallback,
            )("Loaded"),
            loaded,
        )

    def test_pure_helpers_receive_only_provider_node_lookup(self):
        custom = object()
        other = object()
        provider = FakeComfyHostProvider(
            node_classes={
                "Custom": custom,
                "Other": other,
                "CLIPTextEncode": ClipTextEncode,
            },
        )
        runtime_module._RUNTIME_SERVICES = RuntimeServices(comfy=provider)

        require = resolve_comfy_host_helper(
            "_require_custom_node_class",
            self._fallback,
        )
        require_any = resolve_comfy_host_helper(
            "_require_any_custom_node_class",
            self._fallback,
        )
        encode = resolve_comfy_host_helper(
            "_encode_with_comfy_clip",
            self._fallback,
        )

        self.assertIs(require("Custom", "Pack", "Hint"), custom)
        self.assertEqual(
            require_any(("Missing", "Other"), "Pack", "Hint"),
            ("Other", other),
        )
        self.assertEqual(encode("clip", "prompt"), "clip:prompt")


if __name__ == "__main__":
    unittest.main()
