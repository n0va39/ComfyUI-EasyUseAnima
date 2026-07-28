from __future__ import annotations

import ast
import importlib.util
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ANALYZER_PATH = ROOT / "tools" / "analyze_python_backend.py"
FIXTURE_PATH = (
    ROOT / "tests" / "fixtures" / "python_runtime_state_ownership.v1.json"
)
INVENTORY_DOC = (
    ROOT / "docs" / "architecture" / "python-runtime-state-inventory.md"
)


def load_analyzer():
    spec = importlib.util.spec_from_file_location(
        "easyuse_anima_python_backend_analyzer_for_state_contract",
        ANALYZER_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load analyzer: {ANALYZER_PATH.name}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _target_names(target: ast.expr) -> set[str]:
    if isinstance(target, ast.Name):
        return {target.id}
    if isinstance(target, (ast.List, ast.Tuple)):
        return {
            name
            for item in target.elts
            for name in _target_names(item)
        }
    return set()


def module_bindings(path: Path) -> set[str]:
    tree = ast.parse(
        path.read_text(encoding="utf-8-sig"),
        filename=str(path),
    )
    names: set[str] = set()

    def collect(statements: list[ast.stmt]) -> None:
        for statement in statements:
            if isinstance(
                statement,
                (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef),
            ):
                names.add(statement.name)
            elif isinstance(statement, ast.Assign):
                for target in statement.targets:
                    names.update(_target_names(target))
            elif isinstance(statement, ast.AnnAssign):
                names.update(_target_names(statement.target))
            elif isinstance(statement, (ast.Import, ast.ImportFrom)):
                for alias in statement.names:
                    if alias.name == "*":
                        continue
                    names.add(alias.asname or alias.name.split(".", 1)[0])
            elif isinstance(statement, ast.If):
                collect(statement.body)
                collect(statement.orelse)
            elif isinstance(statement, ast.Try):
                collect(statement.body)
                for handler in statement.handlers:
                    collect(handler.body)
                collect(statement.orelse)
                collect(statement.finalbody)

    collect(tree.body)
    return names


analyzer = load_analyzer()


class PythonRuntimeStateOwnershipContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
        cls.report = analyzer.analyze_repository(ROOT)

    def test_fixture_schema_owner_fields_and_evidence_are_complete(self):
        self.assertEqual(
            set(self.fixture),
            {
                "declarative_mutable_globals",
                "entries",
                "ignored_mutable_global_names",
                "schema_version",
                "scope",
            },
        )
        self.assertEqual(self.fixture["schema_version"], 1)
        self.assertEqual(
            self.fixture["ignored_mutable_global_names"],
            ["__all__"],
        )

        entries = self.fixture["entries"]
        ids = [entry["id"] for entry in entries]
        self.assertEqual(len(ids), len(set(ids)))

        required_fields = {
            "categories",
            "cleanup",
            "id",
            "lifetime",
            "module",
            "owner",
            "symbols",
            "target_phase",
            "test_evidence",
            "thread_safety",
        }
        for entry in entries:
            with self.subTest(entry=entry["id"]):
                self.assertEqual(set(entry), required_fields)
                for field in (
                    "cleanup",
                    "lifetime",
                    "module",
                    "owner",
                    "target_phase",
                    "thread_safety",
                ):
                    self.assertTrue(str(entry[field]).strip())
                self.assertEqual(
                    entry["categories"],
                    sorted(set(entry["categories"])),
                )
                self.assertEqual(
                    entry["symbols"],
                    sorted(set(entry["symbols"])),
                )
                self.assertEqual(
                    entry["test_evidence"],
                    sorted(set(entry["test_evidence"])),
                )
                self.assertTrue(entry["test_evidence"])
                for evidence in entry["test_evidence"]:
                    self.assertTrue((ROOT / evidence).is_file(), evidence)

        declarative_pairs: set[tuple[str, str]] = set()
        for disposition in self.fixture["declarative_mutable_globals"]:
            with self.subTest(declarative=disposition["module"]):
                self.assertEqual(
                    set(disposition),
                    {"module", "reason", "symbols"},
                )
                self.assertTrue(disposition["reason"].strip())
                self.assertEqual(
                    disposition["symbols"],
                    sorted(set(disposition["symbols"])),
                )
                module_path = ROOT / disposition["module"]
                self.assertTrue(module_path.is_file())
                self.assertEqual(
                    set(disposition["symbols"]) - module_bindings(module_path),
                    set(),
                )
                for symbol in disposition["symbols"]:
                    pair = (disposition["module"], symbol)
                    self.assertNotIn(pair, declarative_pairs)
                    declarative_pairs.add(pair)

    def test_runtime_entries_bind_existing_shipped_symbols(self):
        for entry in self.fixture["entries"]:
            module_path = ROOT / entry["module"]
            with self.subTest(
                entry=entry["id"],
                module=entry["module"],
            ):
                self.assertTrue(module_path.is_file())
                bindings = module_bindings(module_path)
                self.assertEqual(
                    set(entry["symbols"]) - bindings,
                    set(),
                    f"{entry['id']} has stale symbols",
                )

    def test_analyzer_mutable_globals_have_one_explicit_disposition(self):
        ignored = set(self.fixture["ignored_mutable_global_names"])
        mutable_globals = {
            (item["module"], item["name"])
            for item in self.report["state"]["mutable_globals"]
            if item["name"] not in ignored
        }
        runtime_owned = {
            (entry["module"], symbol)
            for entry in self.fixture["entries"]
            for symbol in entry["symbols"]
        }
        declarative = {
            (entry["module"], symbol)
            for entry in self.fixture["declarative_mutable_globals"]
            for symbol in entry["symbols"]
        }

        self.assertFalse(runtime_owned & declarative)
        self.assertEqual(declarative - mutable_globals, set())
        self.assertEqual(
            mutable_globals,
            (mutable_globals & runtime_owned) | declarative,
        )

        owner_candidates = {
            (item["module"], item["name"])
            for item in self.report["state"]["owner_candidates"]
        }
        self.assertEqual(owner_candidates - runtime_owned, set())

    def test_manual_resource_and_import_effect_inventory_covers_analyzer_gaps(
        self,
    ):
        runtime_owned = {
            (entry["module"], symbol)
            for entry in self.fixture["entries"]
            for symbol in entry["symbols"]
        }
        required = {
            ("__init__.py", "_initialize"),
            ("api.py", "_PROMPT_TRANSLATION_WORKER"),
            ("api.py", "register_routes"),
            (
                "easyuse_anima/aio/first_pass_cache.py",
                "_AIO_FIRST_PASS_CACHE_ENABLED",
            ),
            (
                "easyuse_anima/aio/first_pass_cache.py",
                "_AIO_FIRST_PASS_CACHE_GENERATION",
            ),
            ("easyuse_anima/api/file_io.py", "_FILE_IO_LIMITERS"),
            (
                "easyuse_anima/autocomplete/dataset.py",
                "_DEFAULT_AUTOCOMPLETE_SNAPSHOTS",
            ),
            (
                "easyuse_anima/autocomplete/index.py",
                "_DEFAULT_AUTOCOMPLETE_INDEX_STORE",
            ),
            ("easyuse_anima/bootstrap.py", "_DEFAULT_RUNTIME"),
            ("easyuse_anima/bootstrap.py", "_WILDCARDS_INITIALIZED"),
            (
                "easyuse_anima/infrastructure/filesystem/atomic_json.py",
                "_PATH_LOCKS_GUARD",
            ),
            (
                "easyuse_anima/infrastructure/filesystem/paths.py",
                "USER_DATA_DIR",
            ),
            (
                "easyuse_anima/profiles/mutation.py",
                "PROFILE_MUTATION_COORDINATOR",
            ),
            (
                "easyuse_anima/prompt/artist_mix.py",
                "_SPECTRUM_ANIMA_MOD_GUIDANCE_OLD_SIGNATURE_WARNED",
            ),
            (
                "easyuse_anima/prompt/conditioning.py",
                "_SPECTRUM_ANIMA_MOD_GUIDANCE_OLD_SIGNATURE_WARNED",
            ),
            ("easyuse_anima/runtime.py", "_RUNTIME_SERVICES"),
            (
                "easyuse_anima/translation/service.py",
                "_DEFAULT_TRANSLATION_SERVICE",
            ),
            ("wildcard_engine.py", "_SNAPSHOT_CONDITION"),
        }
        self.assertEqual(required - runtime_owned, set())

    def test_inventory_document_is_linked_from_maintained_entries(self):
        self.assertTrue(INVENTORY_DOC.is_file())
        link = "python-runtime-state-inventory.md"
        architecture_entry = (
            ROOT / "docs" / "architecture" / "README.md"
        ).read_text(encoding="utf-8")
        development_entry = (
            ROOT / "docs" / "development" / "README.md"
        ).read_text(encoding="utf-8")
        self.assertIn(link, architecture_entry)
        self.assertIn(f"../architecture/{link}", development_entry)


if __name__ == "__main__":
    unittest.main()
