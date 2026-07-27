from __future__ import annotations

import ast
import importlib
import sys
import types
import unittest
from pathlib import Path

import autocomplete_dataset
from easyuse_anima.autocomplete import classification, dataset, search


ROOT = Path(__file__).resolve().parents[1]
API_PATH = ROOT / "api.py"
EXPECTED_EXPORTS = [
    "DBR_TAG_ARCHIVE_SOURCE",
    "DBR_TAG_ARCHIVE_LICENSE",
    "DBR_DANBOORU_AUTOCOMPLETE_CSV",
    "DBR_E621_AUTOCOMPLETE_CSV",
    "DBR_MERGED_AUTOCOMPLETE_CSV",
    "LOCALSMILE_AUTOCOMPLETE_CSV",
    "AUTOCOMPLETE_CSV",
    "DEFAULT_AUTOCOMPLETE_SOURCE",
    "AUTOCOMPLETE_SOURCES",
    "AutocompleteEntry",
    "resolve_autocomplete_source",
    "available_autocomplete_sources",
    "autocomplete_status",
    "search_autocomplete",
    "classify_prompt_text",
]


def canonical_exports(dataset_module, search_module, classification_module):
    return {
        **{name: getattr(dataset_module, name) for name in dataset_module.__all__},
        "search_autocomplete": search_module.search_autocomplete,
        "classify_prompt_text": classification_module.classify_prompt_text,
    }


class AutocompleteDatasetCompatibilityTests(unittest.TestCase):
    def test_root_public_surface_is_an_exact_identity_shim(self):
        expected = canonical_exports(dataset, search, classification)
        self.assertEqual(autocomplete_dataset.__all__, EXPECTED_EXPORTS)
        self.assertEqual(set(expected), set(EXPECTED_EXPORTS))
        for name, value in expected.items():
            with self.subTest(name=name):
                self.assertIs(getattr(autocomplete_dataset, name), value)
        for private_name in ("_normalize", "_snapshot", "_classification_tokens"):
            self.assertFalse(hasattr(autocomplete_dataset, private_name))

    def test_package_relative_import_mode_preserves_identity(self):
        parent_name = "_autocomplete_dataset_compat_parent"
        parent = types.ModuleType(parent_name)
        parent.__path__ = [str(ROOT)]
        sys.modules[parent_name] = parent
        try:
            root_module = importlib.import_module(
                f"{parent_name}.autocomplete_dataset"
            )
            dataset_module = importlib.import_module(
                f"{parent_name}.easyuse_anima.autocomplete.dataset"
            )
            search_module = importlib.import_module(
                f"{parent_name}.easyuse_anima.autocomplete.search"
            )
            classification_module = importlib.import_module(
                f"{parent_name}.easyuse_anima.autocomplete.classification"
            )
            expected = canonical_exports(
                dataset_module,
                search_module,
                classification_module,
            )
            self.assertEqual(root_module.__all__, EXPECTED_EXPORTS)
            for name, value in expected.items():
                with self.subTest(name=name):
                    self.assertIs(getattr(root_module, name), value)
        finally:
            for name in tuple(sys.modules):
                if name == parent_name or name.startswith(f"{parent_name}."):
                    sys.modules.pop(name, None)

    def test_api_imports_the_canonical_classification_owner(self):
        tree = ast.parse(API_PATH.read_text(encoding="utf-8"), filename=str(API_PATH))
        imports = [node for node in tree.body if isinstance(node, ast.ImportFrom)]
        self.assertTrue(
            any(
                node.level == 1
                and node.module == "easyuse_anima.autocomplete.classification"
                and any(alias.name == "classify_prompt_text" for alias in node.names)
                for node in imports
            )
        )
        self.assertFalse(
            any(
                node.module == "autocomplete_dataset"
                and any(alias.name == "classify_prompt_text" for alias in node.names)
                for node in imports
            )
        )


if __name__ == "__main__":
    unittest.main()
