from __future__ import annotations

import ast
import importlib
import sys
import types
import unittest
from pathlib import Path

import anima_prompt
from easyuse_anima.infrastructure.filesystem import paths as storage_paths
from easyuse_anima.prompt import anima


ROOT = Path(__file__).resolve().parents[1]
MODULE_PAIRS = (
    ("anima_prompt.correction", "easyuse_anima.prompt.anima.correction"),
    ("anima_prompt.knowledge", "easyuse_anima.prompt.anima.knowledge"),
    ("anima_prompt.models", "easyuse_anima.prompt.anima.models"),
    ("anima_prompt.normalize", "easyuse_anima.prompt.anima.normalize"),
    ("anima_prompt.ordering", "easyuse_anima.prompt.anima.ordering"),
    ("anima_prompt.parser", "easyuse_anima.prompt.anima.parser"),
)
INTERNAL_CONSUMERS = (
    ROOT / "autocomplete_dataset.py",
    ROOT / "easyuse_anima" / "nodes" / "prompt_nodes.py",
    ROOT / "easyuse_anima" / "prompt" / "fields.py",
    ROOT / "nodes.py",
)


class AnimaPromptCompatibilityTests(unittest.TestCase):
    def test_root_package_exports_canonical_objects(self):
        self.assertEqual(anima_prompt.__all__, anima.__all__)
        for name in anima.__all__:
            with self.subTest(name=name):
                self.assertIs(getattr(anima_prompt, name), getattr(anima, name))

    def test_root_submodules_export_canonical_objects(self):
        for root_name, canonical_name in MODULE_PAIRS:
            root_module = importlib.import_module(root_name)
            canonical_module = importlib.import_module(canonical_name)
            with self.subTest(module=root_name):
                for name in root_module.__all__:
                    self.assertIs(
                        getattr(root_module, name),
                        getattr(canonical_module, name),
                    )

    def test_package_relative_import_mode_preserves_identity(self):
        parent_name = "_anima_prompt_compat_parent"
        parent = types.ModuleType(parent_name)
        parent.__path__ = [str(ROOT)]
        sys.modules[parent_name] = parent
        try:
            root_package = importlib.import_module(f"{parent_name}.anima_prompt")
            canonical_package = importlib.import_module(
                f"{parent_name}.easyuse_anima.prompt.anima"
            )
            self.assertEqual(root_package.__all__, canonical_package.__all__)
            for name in canonical_package.__all__:
                with self.subTest(name=name):
                    self.assertIs(
                        getattr(root_package, name),
                        getattr(canonical_package, name),
                    )
        finally:
            for name in tuple(sys.modules):
                if name == parent_name or name.startswith(f"{parent_name}."):
                    sys.modules.pop(name, None)

    def test_data_path_and_representative_behavior_are_preserved(self):
        root_knowledge = importlib.import_module("anima_prompt.knowledge")
        root_parser = importlib.import_module("anima_prompt.parser")
        root_normalize = importlib.import_module("anima_prompt.normalize")
        root_ordering = importlib.import_module("anima_prompt.ordering")

        self.assertIs(root_knowledge.PACKAGE_DATA_DIR, storage_paths.PACKAGE_DATA_DIR)
        self.assertEqual(root_knowledge.PACKAGE_DATA_DIR, ROOT / "__easyuse_anima__")
        parsed = root_parser.parse_prompt("1girl, best quality, 1girl")
        self.assertEqual(
            parsed.tokens,
            ("1girl", "best quality", "1girl"),
        )
        self.assertEqual(root_normalize.normalize_tag(" 1GIRL "), "1girl")
        self.assertEqual(root_ordering.classify_tag("best quality").value, "quality")
        self.assertEqual(
            anima.correct_prompt("1girl, best quality, 1girl"),
            anima_prompt.correct_prompt("1girl, best quality, 1girl"),
        )

    def test_internal_consumers_import_only_the_canonical_package(self):
        violations = []
        for path in INTERNAL_CONSUMERS:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imports_root = any(
                        alias.name == "anima_prompt"
                        or alias.name.startswith("anima_prompt.")
                        for alias in node.names
                    )
                elif isinstance(node, ast.ImportFrom):
                    imports_root = bool(
                        node.module
                        and (
                            node.module == "anima_prompt"
                            or node.module.startswith("anima_prompt.")
                        )
                    )
                else:
                    continue
                if imports_root:
                    violations.append(f"{path.relative_to(ROOT)}:{node.lineno}")
        self.assertEqual(violations, [])


if __name__ == "__main__":
    unittest.main()
