from __future__ import annotations

import ast
import json
import unittest
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PATH = (
    ROOT / "tests" / "fixtures" / "python_wildcard_runtime_contract.v1.json"
)
E01_FIXTURE_PATH = (
    ROOT / "tests" / "fixtures" / "python_runtime_state_ownership.v1.json"
)
CONTRACT_DOC = (
    ROOT
    / "docs"
    / "architecture"
    / "python-runtime-e06-wildcard-contract.md"
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
    for statement in _tree(module).body:
        if not isinstance(statement, ast.ClassDef) or statement.name != class_name:
            continue
        for member in statement.body:
            if isinstance(member, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if member.name == method_name:
                    return member
    raise AssertionError(f"{module} has no {class_name}.{method_name}")


def _instance_assignments(module: str, class_name: str) -> set[str]:
    initializer = _class_method(module, class_name, "__init__")
    assignments: set[str] = set()
    for node in ast.walk(initializer):
        targets: list[ast.expr] = []
        if isinstance(node, ast.Assign):
            targets.extend(node.targets)
        elif isinstance(node, ast.AnnAssign):
            targets.append(node.target)
        for target in targets:
            if (
                isinstance(target, ast.Attribute)
                and isinstance(target.value, ast.Name)
                and target.value.id == "self"
            ):
                assignments.add(target.attr)
    return assignments


def _references(function: ast.FunctionDef | ast.AsyncFunctionDef) -> set[str]:
    return {
        node.id
        for node in ast.walk(function)
        if isinstance(node, ast.Name)
    }


def _called(function: ast.FunctionDef | ast.AsyncFunctionDef) -> set[str]:
    called: set[str] = set()
    for node in ast.walk(function):
        if not isinstance(node, ast.Call):
            continue
        if isinstance(node.func, ast.Name):
            called.add(node.func.id)
        elif isinstance(node.func, ast.Attribute):
            called.add(node.func.attr)
    return called


def _assignment_value(module: str, assigned_name: str) -> ast.expr:
    for statement in _tree(module).body:
        if not isinstance(statement, (ast.Assign, ast.AnnAssign)):
            continue
        targets = (
            statement.targets
            if isinstance(statement, ast.Assign)
            else [statement.target]
        )
        if any(assigned_name in _target_names(target) for target in targets):
            return statement.value
    raise AssertionError(f"{module} has no assignment for {assigned_name}")


def _assignment_call(module: str, assigned_name: str) -> str:
    value = _assignment_value(module, assigned_name)
    if not isinstance(value, ast.Call):
        raise AssertionError(f"{module}.{assigned_name} is not call-initialized")
    if isinstance(value.func, ast.Name):
        return value.func.id
    if isinstance(value.func, ast.Attribute):
        return value.func.attr
    raise AssertionError(f"{module}.{assigned_name} has an unknown call target")


def _imported_names(module: str) -> set[tuple[str, str]]:
    return {
        (node.module, alias.name)
        for node in ast.walk(_tree(module))
        if isinstance(node, ast.ImportFrom) and node.module
        for alias in node.names
    }


class PythonWildcardRuntimeContractTests(unittest.TestCase):
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
                "completion_audit",
                "decisions",
                "internal_consumers",
                "move_queue",
                "owners",
                "post_e06_facade_move",
                "production_callers",
                "production_changes",
                "runtime_port",
                "schema_version",
                "scope",
            },
        )
        self.assertEqual(self.fixture["schema_version"], 1)
        self.assertEqual(self.fixture["classification"], "Contract")
        self.assertEqual(self.fixture["production_changes"], 12)
        self.assertEqual(
            [move["id"] for move in self.fixture["move_queue"]],
            ["E-06a", "E-06b", "E-06c", "E-06d", "E-06e"],
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
            ["wildcard-snapshots"],
        )
        for owner in self.fixture["owners"]:
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
            "E-08a AiO first-pass cache ownership Contract",
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
            cleanup["wildcard-snapshots"]["status"],
            "feature-cleanup-complete",
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
            } | {
                alias.name
                for node in ast.walk(_tree(module))
                if isinstance(node, ast.Import)
                for alias in node.names
            }
            with self.subTest(module=module):
                self.assertEqual(imports & forbidden, set())

        identity_surfaces: dict[str, set[str]] = {}
        for surface in self.fixture["compatibility_surfaces"]:
            if surface["kind"] != "identity_reexport":
                continue
            identity_surfaces.setdefault(surface["module"], set()).update(
                surface["symbols"]
            )
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

    def test_e01_entry_reconciles_to_one_exact_target_owner(self):
        owner = self.fixture["owners"][0]
        entries = {
            entry["id"]: entry for entry in self.e01_fixture["entries"]
        }
        self.assertEqual(owner["e01_entries"], ["wildcard-snapshot-cache"])
        entry = entries["wildcard-snapshot-cache"]
        self.assertEqual(entry["module"], owner["module"])
        self.assertEqual(entry["owner"], owner["current_owner"])
        self.assertEqual(entry["target_phase"], "E-06b-complete")
        self.assertEqual(set(entry["symbols"]), set(owner["state_symbols"]))
        self.assertEqual(owner["target_phase"], "E-06b-complete")
        self.assertEqual(
            owner["target_owner"],
            "easyuse_anima.wildcard.snapshot._DEFAULT_WILDCARD_SNAPSHOTS",
        )
        self.assertEqual(
            self.fixture["decisions"]["generic_cache_condition_port"],
            "rejected",
        )

    def test_default_owner_condition_lru_and_building_state_are_exact(self):
        module = "easyuse_anima/wildcard/snapshot.py"
        owner = self.fixture["owners"][0]
        bindings = _top_level_bindings(module)
        self.assertEqual(set(owner["state_symbols"]) - bindings, set())
        self.assertEqual(
            _assignment_call(module, "_DEFAULT_WILDCARD_SNAPSHOTS"),
            "_WildcardSnapshotStore",
        )
        self.assertEqual(
            _instance_assignments(module, "_WildcardSnapshotStore"),
            {"_building", "_cache", "_cache_limit", "_condition"},
        )
        self.assertEqual(owner["policy_attributes"], ["_cache_limit"])
        self.assertEqual(owner["policy_symbols"], ["_SNAPSHOT_CACHE_LIMIT"])
        limit = _assignment_value(module, "_SNAPSHOT_CACHE_LIMIT")
        self.assertIsInstance(limit, ast.Constant)
        self.assertEqual(limit.value, 16)

        lifecycle = _class_method(
            module,
            "_WildcardSnapshotStore",
            "snapshot_for_roots",
        )
        lifecycle_attributes = {
            node.attr
            for node in ast.walk(lifecycle)
            if isinstance(node, ast.Attribute)
        }
        self.assertTrue(
            {
                "_building",
                "_cache",
                "_cache_limit",
                "_condition",
            }
            <= lifecycle_attributes
        )
        self.assertTrue(
            {
                "add",
                "discard",
                "move_to_end",
                "notify_all",
                "popitem",
                "wait",
            }
            <= _called(lifecycle)
        )

        clear = _class_method(module, "_WildcardSnapshotStore", "clear")
        clear_attributes = {
            node.attr
            for node in ast.walk(clear)
            if isinstance(node, ast.Attribute)
        }
        self.assertEqual(
            clear_attributes,
            {"_cache", "_condition", "clear"},
        )

        self.assertFalse((ROOT / "wildcard_engine.py").exists())

    def test_canonical_snapshot_value_remains_immutable_and_root_independent(self):
        module = "easyuse_anima/wildcard/snapshot.py"
        self.assertTrue(
            {
                "_DEFAULT_WILDCARD_SNAPSHOTS",
                "_SNAPSHOT_CACHE_LIMIT",
                "_WildcardSnapshot",
                "_WildcardSnapshotStore",
                "_build_wildcard_snapshot",
                "__all__",
            }
            <= _top_level_bindings(module)
        )
        all_value = _assignment_value(module, "__all__")
        self.assertIsInstance(all_value, ast.Tuple)
        self.assertEqual(all_value.elts, [])
        imports = {
            node.module
            for node in ast.walk(_tree(module))
            if isinstance(node, ast.ImportFrom) and node.module
        }
        self.assertNotIn("wildcard_engine", imports)
        call_initialized_state: set[str] = set()
        for statement in _tree(module).body:
            if isinstance(statement, ast.Assign):
                if not isinstance(statement.value, ast.Call):
                    continue
                for target in statement.targets:
                    call_initialized_state.update(_target_names(target))
            elif isinstance(statement, ast.AnnAssign):
                if not isinstance(statement.value, ast.Call):
                    continue
                call_initialized_state.update(_target_names(statement.target))
        self.assertEqual(
            call_initialized_state,
            {"_DEFAULT_WILDCARD_SNAPSHOTS"},
        )

    def test_production_callers_resolve_the_one_snapshot_facade(self):
        owner_ids = {owner["id"] for owner in self.fixture["owners"]}
        for caller in self.fixture["production_callers"]:
            with self.subTest(caller=caller["function"]):
                self.assertIn(caller["owner"], owner_ids)
                if caller["kind"] == "method":
                    function = _class_method(
                        caller["module"],
                        caller["class"],
                        caller["function"],
                    )
                else:
                    function = _top_level_function(
                        caller["module"],
                        caller["function"],
                    )
                self.assertEqual(
                    set(caller["uses"]) - _references(function),
                    set(),
                )

    def test_canonical_service_and_internal_import_direction_are_current(self):
        service_module = "easyuse_anima/wildcard/service.py"
        lifecycle = _top_level_function(service_module, "_wildcard_snapshot")
        self.assertTrue(
            {
                "_DEFAULT_WILDCARD_SNAPSHOTS",
                "_build_wildcard_snapshot",
                "_wildcard_sources",
            }
            <= _references(lifecycle)
        )
        self.assertIn("snapshot_for_roots", _called(lifecycle))

        forbidden_modules = {"wildcard_engine", "runtime", "bootstrap"}
        for module in (service_module, *(
            consumer["module"]
            for consumer in self.fixture["internal_consumers"]
        )):
            with self.subTest(module=module):
                imported = _imported_names(module)
                self.assertEqual(
                    {
                        imported_module
                        for imported_module, _ in imported
                        if imported_module.split(".")[-1] in forbidden_modules
                    },
                    set(),
                )

        for consumer in self.fixture["internal_consumers"]:
            imported = _imported_names(consumer["module"])
            with self.subTest(consumer=consumer["module"]):
                self.assertEqual(
                    {
                        tuple(binding)
                        for binding in consumer["canonical_imports"]
                    }
                    - imported,
                    set(),
                )

    def test_runtime_port_composes_the_exact_default_owner(self):
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

        runtime = runtime_port["runtime"]
        runtime_field = next(
            statement
            for statement in _top_level_class(
                runtime["module"], "RuntimeServices"
            ).body
            if isinstance(statement, ast.AnnAssign)
            and isinstance(statement.target, ast.Name)
            and statement.target.id == runtime["field"]
        )
        self.assertIsInstance(runtime_field.annotation, ast.Name)
        self.assertEqual(runtime_field.annotation.id, interface["class"])

        bootstrap = runtime_port["bootstrap"]
        self.assertEqual(
            set(bootstrap["uses"])
            - _references(
                _top_level_function(
                    bootstrap["module"],
                    bootstrap["function"],
                )
            ),
            set(),
        )
        self.assertEqual(
            runtime_port["owner"],
            "easyuse_anima.wildcard.snapshot._DEFAULT_WILDCARD_SNAPSHOTS",
        )

        forbidden_modules = {"runtime", "bootstrap"}
        for module in (
            "easyuse_anima/wildcard/ports.py",
            "easyuse_anima/wildcard/service.py",
            *(
                consumer["module"]
                for consumer in self.fixture["internal_consumers"]
            ),
        ):
            with self.subTest(module=module):
                self.assertEqual(
                    {
                        imported_module
                        for imported_module, _ in _imported_names(module)
                        if imported_module.split(".")[-1]
                        in forbidden_modules
                    },
                    set(),
                )

    def test_canonical_dynamic_seams_are_current_and_root_is_retired(self):
        for surface in self.fixture["compatibility_surfaces"]:
            bindings = _top_level_bindings(surface["module"])
            with self.subTest(surface=surface["id"]):
                self.assertEqual(set(surface["symbols"]) - bindings, set())
        self.assertFalse((ROOT / "wildcard_engine.py").exists())

        dynamic = next(
            surface
            for surface in self.fixture["compatibility_surfaces"]
            if surface["kind"] == "dynamic_reference"
        )
        lifecycle_references = _references(
            _top_level_function(dynamic["module"], "_wildcard_snapshot")
        )
        self.assertEqual(set(dynamic["symbols"]) - lifecycle_references, set())

    def test_post_e06_historical_facade_paths_are_now_retired(self):
        move = self.fixture["post_e06_facade_move"]
        self.assertEqual(move["id"], "P-WC-02")
        self.assertEqual(move["classification"], "Move")
        self.assertEqual(move["status"], "complete")
        self.assertEqual(move["next_task"], "P-API-01")
        self.assertEqual(
            move["production_files"],
            ["api.py", "nodes.py", "wildcard_engine.py"],
        )

        for retired_path in move["production_files"]:
            self.assertFalse((ROOT / retired_path).exists(), retired_path)

        canonical_owner = move["canonical_private_patch_owner"]
        bindings = _top_level_bindings(canonical_owner["module"])
        self.assertEqual(set(canonical_owner["symbols"]) - bindings, set())

        patch_owner = move["canonical_private_patch_owner"]
        lifecycle_references = _references(
            _top_level_function(patch_owner["module"], "_wildcard_snapshot")
        )
        self.assertEqual(
            set(patch_owner["symbols"]) - lifecycle_references,
            {"_wildcard_snapshot"},
        )

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
