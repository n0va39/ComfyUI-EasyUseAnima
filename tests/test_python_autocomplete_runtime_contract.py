from __future__ import annotations

import ast
import json
import unittest
from functools import lru_cache
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PATH = (
    ROOT / "tests" / "fixtures" / "python_autocomplete_runtime_contract.v1.json"
)
E01_FIXTURE_PATH = (
    ROOT / "tests" / "fixtures" / "python_runtime_state_ownership.v1.json"
)
CONTRACT_DOC = (
    ROOT
    / "docs"
    / "architecture"
    / "python-runtime-e05-autocomplete-contract.md"
)


@lru_cache(maxsize=None)
def _tree(module: str) -> ast.Module:
    path = ROOT / module
    return ast.parse(
        path.read_text(encoding="utf-8-sig"),
        filename=str(path),
    )


def _target_names(target: ast.expr) -> set[str]:
    if isinstance(target, ast.Name):
        return {target.id}
    if isinstance(target, (ast.List, ast.Tuple)):
        return {
            name
            for element in target.elts
            for name in _target_names(element)
        }
    return set()


def _top_level_bindings(module: str) -> set[str]:
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

    collect(_tree(module).body)
    return names


def _top_level_function(
    module: str,
    function_name: str,
) -> ast.FunctionDef | ast.AsyncFunctionDef:
    for statement in _tree(module).body:
        if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if statement.name == function_name:
                return statement
    raise AssertionError(f"{module} has no top-level function {function_name}")


def _top_level_class(module: str, class_name: str) -> ast.ClassDef:
    for statement in _tree(module).body:
        if isinstance(statement, ast.ClassDef) and statement.name == class_name:
            return statement
    raise AssertionError(f"{module} has no top-level class {class_name}")


def _class_method(
    module: str,
    class_name: str,
    method_name: str,
) -> ast.FunctionDef | ast.AsyncFunctionDef:
    for statement in _top_level_class(module, class_name).body:
        if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if statement.name == method_name:
                return statement
    raise AssertionError(f"{class_name} has no method {method_name}")


def _instance_assignments(module: str, class_name: str) -> set[str]:
    assigned: set[str] = set()
    for node in ast.walk(_top_level_class(module, class_name)):
        targets: list[ast.expr] = []
        if isinstance(node, ast.Assign):
            targets = node.targets
        elif isinstance(node, ast.AnnAssign):
            targets = [node.target]
        for target in targets:
            if (
                isinstance(target, ast.Attribute)
                and isinstance(target.value, ast.Name)
                and target.value.id == "self"
            ):
                assigned.add(target.attr)
    return assigned


def _function_references(module: str, function_name: str) -> set[str]:
    return {
        node.id
        for node in ast.walk(_top_level_function(module, function_name))
        if isinstance(node, ast.Name)
    }


def _called_attributes(module: str, function_name: str) -> set[str]:
    called: set[str] = set()
    for node in ast.walk(_top_level_function(module, function_name)):
        if not isinstance(node, ast.Call):
            continue
        function = node.func
        if isinstance(function, ast.Attribute):
            called.add(function.attr)
        elif isinstance(function, ast.Name):
            called.add(function.id)
    return called


def _top_level_assignment_call(module: str, assigned_name: str) -> str:
    for statement in _tree(module).body:
        if not isinstance(statement, (ast.Assign, ast.AnnAssign)):
            continue
        targets = (
            statement.targets
            if isinstance(statement, ast.Assign)
            else [statement.target]
        )
        if not any(assigned_name in _target_names(target) for target in targets):
            continue
        value = statement.value
        if isinstance(value, ast.Call):
            if isinstance(value.func, ast.Name):
                return value.func.id
            if isinstance(value.func, ast.Attribute):
                return value.func.attr
    raise AssertionError(f"{module} has no call assignment for {assigned_name}")


class PythonAutocompleteRuntimeContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
        cls.e01_fixture = json.loads(
            E01_FIXTURE_PATH.read_text(encoding="utf-8")
        )

    def test_schema_queue_and_evidence_are_complete(self):
        self.assertEqual(
            set(self.fixture),
            {
                "classification",
                "compatibility_surfaces",
                "decisions",
                "declarative_policy",
                "move_queue",
                "owners",
                "production_callers",
                "production_changes",
                "schema_version",
                "scope",
            },
        )
        self.assertEqual(self.fixture["schema_version"], 1)
        self.assertEqual(self.fixture["classification"], "Contract")
        self.assertEqual(self.fixture["production_changes"], 1)
        self.assertEqual(
            [move["id"] for move in self.fixture["move_queue"]],
            ["E-05a", "E-05b", "E-05c", "E-05d", "E-05e"],
        )
        self.assertEqual(
            [move["classification"] for move in self.fixture["move_queue"]],
            ["Contract", "Move", "Move", "Move", "Contract"],
        )
        self.assertEqual(
            [owner["id"] for owner in self.fixture["owners"]],
            ["dataset-snapshots", "index-store"],
        )
        for owner in self.fixture["owners"]:
            with self.subTest(owner=owner["id"]):
                self.assertTrue(owner["evidence"])
                for evidence in owner["evidence"]:
                    self.assertTrue((ROOT / evidence).is_file(), evidence)

    def test_e01_entries_reconcile_to_two_exact_future_owners(self):
        e01_entries = {
            entry["id"]: entry for entry in self.e01_fixture["entries"]
        }
        owners = {owner["id"]: owner for owner in self.fixture["owners"]}
        self.assertEqual(
            {
                e01_entry
                for owner in owners.values()
                for e01_entry in owner["e01_entries"]
            },
            {
                "autocomplete-dataset-cache",
                "autocomplete-index-locks",
                "autocomplete-index-root",
            },
        )

        dataset_owner = owners["dataset-snapshots"]
        dataset_entry = e01_entries["autocomplete-dataset-cache"]
        self.assertEqual(dataset_entry["owner"], dataset_owner["current_owner"])
        self.assertEqual(dataset_entry["target_phase"], "E-05b-complete")
        self.assertEqual(
            set(dataset_entry["symbols"]),
            set(dataset_owner["state_symbols"]),
        )

        index_owner = owners["index-store"]
        current_owners = {
            item["e01_entry"]: item["owner"]
            for item in index_owner["current_owners"]
        }
        for entry_id in (
            "autocomplete-index-locks",
            "autocomplete-index-root",
        ):
            with self.subTest(entry=entry_id):
                self.assertEqual(
                    e01_entries[entry_id]["owner"],
                    current_owners[entry_id],
                )
                self.assertEqual(
                    e01_entries[entry_id]["target_phase"],
                    "E-05c",
                )

    def test_source_metadata_remains_declarative_and_separate(self):
        expected = {
            (policy["e01_module"], symbol)
            for policy in self.fixture["declarative_policy"]
            for symbol in policy["symbols"]
        }
        actual = {
            (entry["module"], symbol)
            for entry in self.e01_fixture["declarative_mutable_globals"]
            for symbol in entry["symbols"]
        }
        self.assertEqual(expected - actual, set())
        self.assertEqual(
            self.fixture["decisions"]["generic_cache_lock_port"],
            "rejected",
        )
        partition = self.fixture["decisions"]["resource_partition"].lower()
        self.assertIn("one owner", partition)
        self.assertIn("second owner", partition)

    def test_dataset_snapshot_state_and_single_flight_contract_are_current(self):
        module = "easyuse_anima/autocomplete/dataset.py"
        bindings = _top_level_bindings(
            module
        )
        self.assertTrue(
            {
                "_AutocompleteSnapshotStore",
                "_DEFAULT_AUTOCOMPLETE_SNAPSHOTS",
            }
            <= bindings
        )
        self.assertEqual(
            {"_CACHE", "_CACHE_LOCK", "_INFLIGHT"} & bindings,
            set(),
        )
        self.assertEqual(
            _instance_assignments(module, "_AutocompleteSnapshotStore"),
            {"_cache", "_inflight", "_lock"},
        )
        owner_methods = {
            statement.name
            for statement in _top_level_class(
                module,
                "_AutocompleteSnapshotStore",
            ).body
            if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef))
        }
        self.assertEqual(
            owner_methods,
            {
                "__init__",
                "cached_snapshot_for_key",
                "clear",
                "snapshot_for_key",
            },
        )
        snapshot_method = _class_method(
            module,
            "_AutocompleteSnapshotStore",
            "snapshot_for_key",
        )
        snapshot_references = {
            node.id
            for node in ast.walk(snapshot_method)
            if isinstance(node, ast.Name)
        }
        self.assertTrue(
            {
                "Future",
                "_await_snapshot",
                "_build_snapshot",
                "_cache_key_from_resolved_path",
            }
            <= snapshot_references
        )
        snapshot_attributes = {
            node.attr
            for node in ast.walk(snapshot_method)
            if isinstance(node, ast.Attribute)
        }
        self.assertTrue(
            {"_cache", "_inflight", "_lock", "set_exception", "set_result"}
            <= snapshot_attributes
        )
        clear_attributes = {
            node.attr
            for node in ast.walk(
                _class_method(
                    module,
                    "_AutocompleteSnapshotStore",
                    "clear",
                )
            )
            if isinstance(node, ast.Attribute)
        }
        self.assertIn("_cache", clear_attributes)
        self.assertNotIn("_inflight", clear_attributes)
        self.assertTrue(
            {"_DEFAULT_AUTOCOMPLETE_SNAPSHOTS", "key"}
            <= _function_references(module, "_snapshot_for_key")
        )
        self.assertTrue(
            {"_DEFAULT_AUTOCOMPLETE_SNAPSHOTS", "key"}
            <= _function_references(module, "_cached_snapshot_for_key")
        )
        self.assertIn(
            "_AUTOCOMPLETE_CACHE_LOAD_ATTEMPTS",
            _function_references(
                module,
                "_snapshot",
            ),
        )
        self.assertTrue(
            {"_cached_snapshot_for_key", "_snapshot"}
            <= _function_references(
                module,
                "autocomplete_status",
            )
        )

    def test_index_root_and_path_publication_lock_contract_are_current(self):
        index_bindings = _top_level_bindings(
            "easyuse_anima/autocomplete/index.py"
        )
        self.assertTrue(
            {"_INDEX_LOCKS", "_INDEX_LOCKS_GUARD"} <= index_bindings
        )
        lock_references = _function_references(
            "easyuse_anima/autocomplete/index.py",
            "_index_lock",
        )
        self.assertTrue(
            {"_INDEX_LOCKS", "_INDEX_LOCKS_GUARD", "os"} <= lock_references
        )
        called = _called_attributes(
            "easyuse_anima/autocomplete/index.py",
            "_index_lock",
        )
        self.assertTrue({"abspath", "normcase"} <= called)
        self.assertNotIn("resolve", called)
        self.assertIn(
            "_index_lock",
            _function_references(
                "easyuse_anima/autocomplete/index.py",
                "search_autocomplete_index",
            ),
        )

        self.assertEqual(
            _top_level_assignment_call(
                "easyuse_anima/autocomplete/search.py",
                "_AUTOCOMPLETE_INDEX_DIR",
            ),
            "_default_autocomplete_index_dir",
        )
        root_references = _function_references(
            "easyuse_anima/autocomplete/search.py",
            "_default_autocomplete_index_dir",
        )
        self.assertTrue(
            {"USER_DATA_DIR", "STORAGE_PACKAGE_DATA_DIR", "Path"}
            <= root_references
        )
        self.assertTrue(
            {
                "_AUTOCOMPLETE_INDEX_DIR",
                "_snapshot",
                "search_autocomplete_index",
            }
            <= _function_references(
                "easyuse_anima/autocomplete/search.py",
                "_search_autocomplete_with_diagnostics",
            )
        )

    def test_production_callers_and_compatibility_surfaces_are_current(self):
        owner_ids = {owner["id"] for owner in self.fixture["owners"]}
        for caller in self.fixture["production_callers"]:
            with self.subTest(caller=caller["entry"]):
                claimed = set(caller.get("owners", [caller.get("owner")]))
                self.assertEqual(claimed - owner_ids, set())
                self.assertEqual(
                    set(caller["uses"])
                    - _function_references(
                        caller["module"],
                        caller["function"],
                    ),
                    set(),
                )
        for surface in self.fixture["compatibility_surfaces"]:
            with self.subTest(surface=surface["id"]):
                self.assertEqual(
                    set(surface["symbols"])
                    - _top_level_bindings(surface["module"]),
                    set(),
                )

    def test_feature_modules_do_not_depend_on_runtime_or_outer_adapters(self):
        forbidden = {
            "api",
            "autocomplete_dataset",
            "autocomplete_index",
            "easyuse_anima.api",
            "easyuse_anima.bootstrap",
            "easyuse_anima.runtime",
        }
        for module in (
            "easyuse_anima/autocomplete/classification.py",
            "easyuse_anima/autocomplete/dataset.py",
            "easyuse_anima/autocomplete/index.py",
            "easyuse_anima/autocomplete/search.py",
        ):
            imports = {
                node.module
                for node in ast.walk(_tree(module))
                if isinstance(node, ast.ImportFrom) and node.module
            }
            with self.subTest(module=module):
                self.assertEqual(imports & forbidden, set())

        runtime = next(
            statement
            for statement in _tree("easyuse_anima/runtime.py").body
            if isinstance(statement, ast.ClassDef)
            and statement.name == "RuntimeServices"
        )
        fields = {
            statement.target.id
            for statement in runtime.body
            if isinstance(statement, ast.AnnAssign)
            and isinstance(statement.target, ast.Name)
        }
        self.assertNotIn("autocomplete", fields)

    def test_contract_document_is_linked_from_maintained_entries(self):
        self.assertTrue(CONTRACT_DOC.is_file())
        architecture_entry = (
            ROOT / "docs" / "architecture" / "README.md"
        ).read_text(encoding="utf-8")
        development_entry = (
            ROOT / "docs" / "development" / "README.md"
        ).read_text(encoding="utf-8")
        self.assertIn(CONTRACT_DOC.name, architecture_entry)
        self.assertIn(
            f"../architecture/{CONTRACT_DOC.name}",
            development_entry,
        )


if __name__ == "__main__":
    unittest.main()
