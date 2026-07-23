from __future__ import annotations

import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from easyuse_anima.infrastructure.comfy.provider import DefaultComfyHostProvider


class DefaultComfyHostProviderTests(unittest.TestCase):
    def setUp(self):
        self.provider = DefaultComfyHostProvider()

    @staticmethod
    def host_module(**attributes):
        module = types.ModuleType("nodes")
        for name, value in attributes.items():
            setattr(module, name, value)
        return module

    def test_max_resolution_preserves_delayed_lookup_and_fallbacks(self):
        with patch.dict(sys.modules, {"nodes": None}):
            self.assertEqual(self.provider.max_resolution(), 16384)

        host = self.host_module(MAX_RESOLUTION="8192")
        with patch.dict(sys.modules, {"nodes": host}):
            self.assertEqual(self.provider.max_resolution(), 8192)

        host.MAX_RESOLUTION = "invalid"
        with patch.dict(sys.modules, {"nodes": host}):
            self.assertEqual(self.provider.max_resolution(), 16384)

        missing = self.host_module()
        with patch.dict(sys.modules, {"nodes": missing}):
            self.assertEqual(self.provider.max_resolution(), 16384)

    def test_node_lookup_preserves_mapping_attribute_and_loaded_module_order(self):
        mapping_id = "EasyUseAnimaProviderMappingNode"
        attribute_id = "EasyUseAnimaProviderAttributeNode"
        loaded_id = "EasyUseAnimaProviderLoadedNode"
        mapping_class = type("MappingNode", (), {})
        attribute_class = type("AttributeNode", (), {})
        loaded_class = type("LoadedNode", (), {})
        host = self.host_module(NODE_CLASS_MAPPINGS={mapping_id: mapping_class})
        setattr(host, mapping_id, attribute_class)
        setattr(host, attribute_id, attribute_class)
        loaded_module = types.ModuleType("easyuse_anima_provider_loaded_nodes")
        loaded_module.NODE_CLASS_MAPPINGS = {loaded_id: loaded_class}

        with patch.dict(
            sys.modules,
            {
                "nodes": host,
                loaded_module.__name__: loaded_module,
            },
        ):
            self.assertIs(self.provider.find_node_class(mapping_id), mapping_class)
            self.assertIs(self.provider.find_node_class(attribute_id), attribute_class)
            self.assertIs(self.provider.find_node_class(loaded_id), loaded_class)

    def test_mapping_lookup_uses_only_the_host_mapping(self):
        node_id = "EasyUseAnimaProviderMappingOnlyNode"
        mapping_class = type("MappingOnlyNode", (), {})
        attribute_class = type("AttributeOnlyNode", (), {})
        host = self.host_module(NODE_CLASS_MAPPINGS={node_id: mapping_class})
        setattr(host, node_id, attribute_class)

        with patch.dict(sys.modules, {"nodes": host}):
            self.assertIs(
                self.provider.find_node_mapping_class(node_id),
                mapping_class,
            )
            host.NODE_CLASS_MAPPINGS = {}
            self.assertIsNone(self.provider.find_node_mapping_class(node_id))

    def test_loaded_lookup_preserves_explicit_lookup_before_module_scan(self):
        node_id = "EasyUseAnimaProviderLoadedFallbackNode"
        direct_class = type("DirectNode", (), {})
        loaded_class = type("LoadedFallbackNode", (), {})
        loaded_module = types.ModuleType("easyuse_anima_provider_loaded_fallback")
        loaded_module.NODE_CLASS_MAPPINGS = {node_id: loaded_class}

        with (
            patch.dict(sys.modules, {loaded_module.__name__: loaded_module}),
            patch.object(
                self.provider,
                "find_node_class",
                side_effect=(direct_class, None),
            ) as find_node_class,
        ):
            self.assertIs(self.provider.find_loaded_node_class(node_id), direct_class)
            self.assertIs(self.provider.find_loaded_node_class(node_id), loaded_class)

        self.assertEqual(find_node_class.call_args_list[0].args, (node_id,))
        self.assertEqual(find_node_class.call_args_list[1].args, (node_id,))

    def test_loaded_lookup_uses_first_loaded_mapping(self):
        node_id = "EasyUseAnimaProviderLoadedOrderNode"
        first_class = type("FirstLoadedNode", (), {})
        second_class = type("SecondLoadedNode", (), {})
        first_module = types.ModuleType("easyuse_anima_provider_loaded_first")
        first_module.NODE_CLASS_MAPPINGS = {node_id: first_class}
        second_module = types.ModuleType("easyuse_anima_provider_loaded_second")
        second_module.NODE_CLASS_MAPPINGS = {node_id: second_class}

        with (
            patch.dict(
                sys.modules,
                {
                    first_module.__name__: first_module,
                    second_module.__name__: second_module,
                },
            ),
            patch.object(self.provider, "find_node_class", return_value=None),
        ):
            self.assertIs(self.provider.find_loaded_node_class(node_id), first_class)

    def test_lookup_is_not_cached_between_host_updates(self):
        node_id = "EasyUseAnimaProviderDynamicNode"
        first_class = type("FirstNode", (), {})
        second_class = type("SecondNode", (), {})

        with patch.dict(
            sys.modules,
            {"nodes": self.host_module(NODE_CLASS_MAPPINGS={node_id: first_class})},
        ):
            self.assertIs(self.provider.find_node_class(node_id), first_class)

        with patch.dict(
            sys.modules,
            {"nodes": self.host_module(NODE_CLASS_MAPPINGS={node_id: second_class})},
        ):
            self.assertIs(self.provider.find_node_class(node_id), second_class)


if __name__ == "__main__":
    unittest.main()
