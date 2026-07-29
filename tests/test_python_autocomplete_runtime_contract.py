from __future__ import annotations

import ast
import importlib.util
import json
import typing
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
TYPED_CONTRACTS_PATH = (
    ROOT / "easyuse_anima" / "autocomplete" / "contracts.py"
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


def _nested_function(
    module: str,
    parent_name: str,
    function_name: str,
) -> ast.FunctionDef | ast.AsyncFunctionDef:
    parent = _top_level_function(module, parent_name)
    for statement in ast.walk(parent):
        if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if statement.name == function_name:
                return statement
    raise AssertionError(
        f"{module}:{parent_name} has no nested function {function_name}"
    )


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


def _imported_names(module: str) -> set[tuple[str, str]]:
    return {
        (node.module, alias.name)
        for node in ast.walk(_tree(module))
        if isinstance(node, ast.ImportFrom) and node.module
        for alias in node.names
    }


@lru_cache(maxsize=1)
def _typed_contracts():
    spec = importlib.util.spec_from_file_location(
        "easyuse_anima_autocomplete_typed_contracts",
        TYPED_CONTRACTS_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load {TYPED_CONTRACTS_PATH.name}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _return_annotation(
    function: ast.FunctionDef | ast.AsyncFunctionDef,
) -> str | None:
    if function.returns is None:
        return None
    return ast.unparse(function.returns)


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
                "completion_audit",
                "compatibility_surfaces",
                "decisions",
                "declarative_policy",
                "move_queue",
                "owners",
                "production_callers",
                "production_changes",
                "runtime_port",
                "schema_version",
                "scope",
            },
        )
        self.assertEqual(self.fixture["schema_version"], 1)
        self.assertEqual(self.fixture["classification"], "Contract")
        self.assertEqual(self.fixture["production_changes"], 8)
        self.assertEqual(
            [move["id"] for move in self.fixture["move_queue"]],
            ["E-05a", "E-05b", "E-05c", "E-05d", "E-05e"],
        )
        self.assertEqual(
            [move["classification"] for move in self.fixture["move_queue"]],
            ["Contract", "Move", "Move", "Move", "Contract"],
        )
        self.assertEqual(
            [move["status"] for move in self.fixture["move_queue"]],
            ["complete", "complete", "complete", "complete", "complete"],
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

    def test_completion_audit_reconciles_cleanup_import_and_root_identity(self):
        audit = self.fixture["completion_audit"]
        owners = {owner["id"]: owner for owner in self.fixture["owners"]}
        e01_entries = {
            entry["id"]: entry for entry in self.e01_fixture["entries"]
        }

        self.assertEqual(audit["classification"], "Contract")
        self.assertEqual(audit["production_changes"], 0)
        self.assertEqual(audit["ambiguous_state_owners"], [])
        self.assertEqual(
            len({owner["current_owner"] for owner in owners.values()}),
            len(owners),
        )
        self.assertEqual(
            audit["next_phase"],
            "E-06a wildcard snapshot ownership Contract",
        )

        reconciliations = {
            item["e01_entry"]: item
            for item in audit["e01_reconciliation"]
        }
        self.assertEqual(
            set(reconciliations),
            {
                e01_entry
                for owner in owners.values()
                for e01_entry in owner["e01_entries"]
            },
        )
        for e01_entry, reconciliation in reconciliations.items():
            with self.subTest(e01_entry=e01_entry):
                owner = owners[reconciliation["owner"]]
                self.assertIn(e01_entry, owner["e01_entries"])
                self.assertEqual(
                    e01_entries[e01_entry]["owner"],
                    owner["current_owner"],
                )
                self.assertEqual(
                    e01_entries[e01_entry]["target_phase"],
                    reconciliation["completed_phase"],
                )

        cleanup = {
            item["owner"]: item
            for item in audit["cleanup_dispositions"]
        }
        self.assertEqual(set(cleanup), set(owners))
        self.assertEqual(
            cleanup["dataset-snapshots"]["status"],
            "feature-cleanup-complete",
        )
        self.assertEqual(
            cleanup["index-store"]["status"],
            "intentional-no-op-close",
        )
        self.assertEqual(
            {item["remaining_phase"] for item in cleanup.values()},
            {"E-09"},
        )

        import_safety = audit["import_safety"]
        self.assertFalse(import_safety["host_io_at_import"])
        for evidence in import_safety["evidence"]:
            self.assertTrue((ROOT / evidence).is_file(), evidence)
        forbidden = set(import_safety["forbidden_imports"])
        for module in import_safety["feature_modules"]:
            imports = {
                node.module
                for node in ast.walk(_tree(module))
                if isinstance(node, ast.ImportFrom) and node.module
            }
            with self.subTest(module=module):
                self.assertEqual(imports & forbidden, set())

        identity_surfaces = {
            surface["module"]: set(surface["symbols"])
            for surface in self.fixture["compatibility_surfaces"]
            if surface["kind"] == "identity_reexport"
        }
        audited_bindings: dict[str, set[str]] = {}
        for binding in audit["root_identity_bindings"]:
            root_module = binding["root_module"]
            expected = {
                (binding["canonical_module"], symbol)
                for symbol in binding["symbols"]
            }
            with self.subTest(root_module=root_module):
                self.assertEqual(
                    expected - _imported_names(root_module),
                    set(),
                )
            audited_bindings.setdefault(root_module, set()).update(
                binding["symbols"]
            )
        self.assertEqual(audited_bindings, identity_surfaces)

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
        for entry_id in (
            "autocomplete-index-locks",
            "autocomplete-index-root",
        ):
            with self.subTest(entry=entry_id):
                self.assertEqual(
                    e01_entries[entry_id]["owner"],
                    index_owner["current_owner"],
                )
                self.assertEqual(
                    e01_entries[entry_id]["target_phase"],
                    "E-05c-complete",
                )
                self.assertEqual(
                    set(e01_entries[entry_id]["symbols"]),
                    {
                        symbol
                        for symbols in index_owner["state_symbols"].values()
                        for symbol in symbols
                    },
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

    def test_typed_result_contracts_freeze_core_and_public_payload_shapes(self):
        contracts = _typed_contracts()
        expected = {
            "AutocompleteSourcePayload": (
                {
                    "key",
                    "label",
                    "source",
                    "license",
                    "path",
                    "exists",
                    "selected",
                },
                set(),
            ),
            "AutocompletePublicSourcePayload": (
                {
                    "key",
                    "label",
                    "source",
                    "license",
                    "exists",
                    "selected",
                },
                set(),
            ),
            "AutocompleteStatusPayload": (
                {"path", "exists", "count", "mtime"},
                set(),
            ),
            "AutocompletePublicStatusPayload": (
                {"exists", "count", "mtime"},
                set(),
            ),
            "AutocompletePublicStatusResultPayload": (
                {
                    "exists",
                    "count",
                    "mtime",
                    "source",
                    "source_label",
                    "sources",
                },
                set(),
            ),
            "AutocompleteSearchEntryPayload": (
                {"tag", "category", "count", "description"},
                set(),
            ),
            "AutocompleteSearchPayload": (
                {"query", "results", "status", "elapsed_ms"},
                {"category"},
            ),
            "AutocompletePublicSearchPayload": (
                {"query", "results", "status", "elapsed_ms"},
                {"category"},
            ),
            "AutocompleteClassificationTokenPayload": (
                {
                    "token",
                    "base",
                    "section",
                    "label",
                    "learned",
                    "weighted",
                    "count",
                    "description",
                },
                set(),
            ),
            "AutocompleteClassificationPayload": (
                {"tokens", "status"},
                set(),
            ),
            "AutocompletePublicClassificationPayload": (
                {"tokens", "status"},
                set(),
            ),
        }

        self.assertEqual(contracts.__all__, ())
        for name, (required, optional) in expected.items():
            with self.subTest(contract=name):
                contract = getattr(contracts, name)
                self.assertTrue(typing.is_typeddict(contract))
                self.assertEqual(set(contract.__required_keys__), required)
                self.assertEqual(set(contract.__optional_keys__), optional)

    def test_typed_results_are_applied_to_port_service_core_and_api_adapter(self):
        function_annotations = {
            (
                "easyuse_anima/autocomplete/dataset.py",
                "available_autocomplete_sources",
            ): "list[AutocompleteSourcePayload]",
            (
                "easyuse_anima/autocomplete/dataset.py",
                "autocomplete_status",
            ): "AutocompleteStatusPayload",
            (
                "easyuse_anima/autocomplete/search.py",
                "search_autocomplete",
            ): "AutocompleteSearchPayload",
            (
                "easyuse_anima/autocomplete/classification.py",
                "classify_prompt_text",
            ): "AutocompleteClassificationPayload",
        }
        for (module, function_name), expected in function_annotations.items():
            with self.subTest(module=module, function=function_name):
                self.assertEqual(
                    _return_annotation(_top_level_function(module, function_name)),
                    expected,
                )

        method_annotations = {
            ("AutocompletePort", "available_sources"): (
                "list[AutocompleteSourcePayload]"
            ),
            ("AutocompletePort", "status"): "AutocompleteStatusPayload",
            ("AutocompletePort", "search"): "AutocompleteSearchPayload",
            ("AutocompletePort", "classify"): (
                "AutocompleteClassificationPayload"
            ),
            ("_AutocompleteService", "available_sources"): (
                "list[AutocompleteSourcePayload]"
            ),
            ("_AutocompleteService", "status"): "AutocompleteStatusPayload",
            ("_AutocompleteService", "search"): "AutocompleteSearchPayload",
            ("_AutocompleteService", "classify"): (
                "AutocompleteClassificationPayload"
            ),
        }
        method_modules = {
            "AutocompletePort": "easyuse_anima/autocomplete/ports.py",
            "_AutocompleteService": "easyuse_anima/autocomplete/service.py",
        }
        for (class_name, method_name), expected in method_annotations.items():
            with self.subTest(owner=class_name, method=method_name):
                self.assertEqual(
                    _return_annotation(
                        _class_method(
                            method_modules[class_name],
                            class_name,
                            method_name,
                        )
                    ),
                    expected,
                )

        api_references = _function_references(
            "easyuse_anima/api/routes/autocomplete.py",
            "build_autocomplete_payloads",
        )
        self.assertTrue(
            {
                "AutocompleteSourcePayload",
                "AutocompleteStatusPayload",
                "AutocompletePublicStatusResultPayload",
                "AutocompletePublicSourcePayload",
                "AutocompletePublicStatusPayload",
                "AutocompletePublicSearchPayload",
                "AutocompletePublicClassificationPayload",
            }
            <= api_references
        )

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
                "_snapshot_with_owner",
            ),
        )
        self.assertTrue(
            {
                "_autocomplete_status_with_owner",
                "_cached_snapshot_for_key",
                "_snapshot",
            }
            <= _function_references(
                module,
                "autocomplete_status",
            )
        )

    def test_index_root_and_path_publication_lock_contract_are_current(self):
        module = "easyuse_anima/autocomplete/index.py"
        index_bindings = _top_level_bindings(
            module
        )
        self.assertTrue(
            {
                "_AutocompleteIndexStore",
                "_DEFAULT_AUTOCOMPLETE_INDEX_STORE",
                "_default_autocomplete_index_dir",
            }
            <= index_bindings
        )
        self.assertEqual(
            {"_INDEX_LOCKS", "_INDEX_LOCKS_GUARD"} & index_bindings,
            set(),
        )
        self.assertEqual(
            _instance_assignments(module, "_AutocompleteIndexStore"),
            {"_locks", "_locks_guard", "_root"},
        )
        owner_methods = {
            statement.name
            for statement in _top_level_class(
                module,
                "_AutocompleteIndexStore",
            ).body
            if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef))
        }
        self.assertEqual(
            owner_methods,
            {
                "__init__",
                "_index_lock",
                "_search_at_root",
                "close",
                "root",
                "search",
            },
        )
        lock_method = _class_method(
            module,
            "_AutocompleteIndexStore",
            "_index_lock",
        )
        lock_references = {
            node.id
            for node in ast.walk(lock_method)
            if isinstance(node, ast.Name)
        }
        self.assertTrue(
            {"os", "threading"} <= lock_references
        )
        called = {
            node.func.attr
            for node in ast.walk(lock_method)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
        }
        self.assertTrue({"abspath", "normcase"} <= called)
        self.assertNotIn("resolve", called)
        search_method = _class_method(
            module,
            "_AutocompleteIndexStore",
            "_search_at_root",
        )
        self.assertIn(
            "_index_lock",
            {
                node.attr
                for node in ast.walk(search_method)
                if isinstance(node, ast.Attribute)
            },
        )
        self.assertEqual(
            _top_level_assignment_call(
                module,
                "_DEFAULT_AUTOCOMPLETE_INDEX_STORE",
            ),
            "_AutocompleteIndexStore",
        )

        root_references = _function_references(
            module,
            "_default_autocomplete_index_dir",
        )
        self.assertTrue(
            {"USER_DATA_DIR", "STORAGE_PACKAGE_DATA_DIR", "Path"}
            <= root_references
        )
        self.assertTrue(
            {
                "_DEFAULT_AUTOCOMPLETE_INDEX_STORE",
                "_snapshot",
                "_search_autocomplete_diagnostics_with_owners",
            }
            <= _function_references(
                "easyuse_anima/autocomplete/search.py",
                "_search_autocomplete_with_diagnostics",
            )
        )
        self.assertIn(
            "_DEFAULT_AUTOCOMPLETE_INDEX_STORE",
            _function_references(module, "search_autocomplete_index"),
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

    def test_runtime_port_composition_and_root_adapter_are_current(self):
        runtime_port = self.fixture["runtime_port"]
        interface = runtime_port["interface"]
        interface_methods = {
            statement.name
            for statement in _top_level_class(
                interface["module"],
                interface["class"],
            ).body
            if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef))
        }
        self.assertEqual(interface_methods, set(interface["methods"]))

        service = runtime_port["service"]
        self.assertEqual(
            _instance_assignments(service["module"], service["class"]),
            set(service["owner_fields"]),
        )

        runtime = runtime_port["runtime"]
        runtime_class = _top_level_class(
            runtime["module"],
            "RuntimeServices",
        )
        runtime_field = next(
            statement
            for statement in runtime_class.body
            if isinstance(statement, ast.AnnAssign)
            and isinstance(statement.target, ast.Name)
            and statement.target.id == runtime["field"]
        )
        self.assertIsInstance(runtime_field.annotation, ast.Name)
        self.assertEqual(runtime_field.annotation.id, interface["class"])

        bootstrap = runtime_port["bootstrap"]
        self.assertEqual(
            set(bootstrap["uses"])
            - _function_references(
                bootstrap["module"],
                bootstrap["function"],
            ),
            set(),
        )

        root_adapter = runtime_port["root_adapter"]
        builder = root_adapter["builder"]
        resolver = _nested_function(
            root_adapter["module"],
            builder,
            root_adapter["resolver"],
        )
        self.assertIn(
            root_adapter["runtime_getter"],
            {
                node.id
                for node in ast.walk(resolver)
                if isinstance(node, ast.Name)
            },
        )
        dependency_reads = {
            tuple(argument.value for argument in node.args)
            for node in ast.walk(resolver)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == root_adapter["runtime_getter"]
            and all(isinstance(argument, ast.Constant) for argument in node.args)
        }
        self.assertIn(
            (
                root_adapter["runtime_family"],
                root_adapter["runtime_leaf"],
            ),
            dependency_reads,
        )
        for adapter in runtime_port["adapters"]:
            with self.subTest(adapter=adapter["function"]):
                function = _nested_function(
                    root_adapter["module"],
                    builder,
                    adapter["function"],
                )
                references = {
                    node.id
                    for node in ast.walk(function)
                    if isinstance(node, ast.Name)
                }
                self.assertTrue(
                    {
                        adapter["canonical_fallback"],
                        root_adapter["resolver"],
                    }
                    <= references
                )
                self.assertIn(
                    adapter["port_method"],
                    {
                        node.func.attr
                        for node in ast.walk(function)
                        if isinstance(node, ast.Call)
                        and isinstance(node.func, ast.Attribute)
                    },
                )

    def test_feature_modules_do_not_depend_on_runtime_or_outer_adapters(self):
        import_safety = self.fixture["completion_audit"]["import_safety"]
        forbidden = set(import_safety["forbidden_imports"])
        for module in import_safety["feature_modules"]:
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
        self.assertIn("autocomplete", fields)

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
