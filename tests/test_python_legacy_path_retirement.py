from __future__ import annotations

import ast
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEGACY_PATHS = (
    "anima_prompt/__init__.py",
    "anima_prompt/correction.py",
    "anima_prompt/knowledge.py",
    "anima_prompt/models.py",
    "anima_prompt/normalize.py",
    "anima_prompt/ordering.py",
    "anima_prompt/parser.py",
    "api.py",
    "api_contract.py",
    "autocomplete_dataset.py",
    "autocomplete_index.py",
    "nodes.py",
    "prompt_translation.py",
    "settings.py",
    "storage.py",
    "wildcard_engine.py",
)


class PythonLegacyPathRetirementTests(unittest.TestCase):
    def test_exact_legacy_paths_are_absent(self):
        self.assertEqual(len(LEGACY_PATHS), 16)
        for relative_path in LEGACY_PATHS:
            with self.subTest(path=relative_path):
                self.assertFalse((ROOT / relative_path).exists())

    def test_root_entrypoint_imports_only_canonical_startup_owners(self):
        tree = ast.parse((ROOT / "__init__.py").read_text(encoding="utf-8-sig"))
        imports = {
            (node.level, node.module, alias.name)
            for node in tree.body
            if isinstance(node, ast.ImportFrom)
            for alias in node.names
        }
        self.assertEqual(
            imports,
            {
                (1, "easyuse_anima.bootstrap", "_initialize_package"),
                (1, "easyuse_anima.registration", "NODE_CLASS_MAPPINGS"),
                (
                    1,
                    "easyuse_anima.registration",
                    "NODE_DISPLAY_NAME_MAPPINGS",
                ),
            },
        )

    def test_canonical_packages_do_not_recreate_legacy_imports(self):
        for path in (ROOT / "easyuse_anima").rglob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    names = [alias.name for alias in node.names]
                elif isinstance(node, ast.ImportFrom) and node.module is not None:
                    names = [node.module]
                else:
                    continue
                with self.subTest(path=path.relative_to(ROOT), names=names):
                    self.assertFalse(any(name == "anima_prompt" for name in names))


if __name__ == "__main__":
    unittest.main()
