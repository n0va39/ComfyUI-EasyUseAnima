from __future__ import annotations

import ast
import json
import unittest
from functools import lru_cache
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PATH = (
    ROOT
    / "tests"
    / "fixtures"
    / "python_aio_first_pass_cache_contract.v1.json"
)
E01_FIXTURE_PATH = (
    ROOT / "tests" / "fixtures" / "python_runtime_state_ownership.v1.json"
)
CONTRACT_DOC = (
    ROOT
    / "docs"
    / "architecture"
    / "python-runtime-e08-aio-cache-contract.md"
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
    raise AssertionError(f"{module} has no {class_name}.{method_name}")


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


def _self_attributes(
    function: ast.FunctionDef | ast.AsyncFunctionDef,
) -> set[str]:
    return {
        node.attr
        for node in ast.walk(function)
        if isinstance(node, ast.Attribute)
        and isinstance(node.value, ast.Name)
        and node.value.id == "self"
    }


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


def _imported_modules(module: str) -> set[str]:
    return {
        node.module
        for node in ast.walk(_tree(module))
        if isinstance(node, ast.ImportFrom) and node.module
    } | {
        alias.name
        for node in ast.walk(_tree(module))
        if isinstance(node, ast.Import)
        for alias in node.names
    }


class PythonAIOFirstPassCacheContractTests(unittest.TestCase):
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
                "adapter_boundary",
                "classification",
                "compatibility_surfaces",
                "completion_audit",
                "decisions",
                "import_direction",
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
        self.assertEqual(self.fixture["production_changes"], 4)
        self.assertEqual(
            [move["id"] for move in self.fixture["move_queue"]],
            ["E-08a", "E-08b", "E-08c", "E-08d"],
        )
        self.assertEqual(
            [move["classification"] for move in self.fixture["move_queue"]],
            ["Contract", "Move", "Move", "Contract"],
        )
        self.assertEqual(
            [move["status"] for move in self.fixture["move_queue"]],
            ["complete", "complete", "complete", "complete"],
        )
        self.assertEqual(
            [owner["id"] for owner in self.fixture["owners"]],
            ["aio-first-pass-cache"],
        )
        for evidence in self.fixture["owners"][0]["evidence"]:
            self.assertTrue((ROOT / evidence).is_file(), evidence)

    def test_completion_audit_reconciles_cleanup_import_root_and_runtime(self):
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
            "E-09 runtime shutdown and cleanup Contract",
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
            cleanup["aio-first-pass-cache"]["status"],
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
            with self.subTest(module=module):
                self.assertEqual(
                    _imported_modules(module) & forbidden,
                    set(),
                )

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

        runtime_binding = audit["runtime_binding"]
        runtime_port = self.fixture["runtime_port"]
        self.assertEqual(
            runtime_binding["bootstrap_owner"],
            runtime_port["owner"],
        )
        self.assertEqual(
            runtime_binding["interface"],
            "easyuse_anima.aio.ports.AIOFirstPassCachePort",
        )
        self.assertEqual(
            runtime_binding["runtime_field"],
            runtime_port["runtime"]["field"],
        )

    def test_e01_entry_reconciles_to_one_exact_target_owner(self):
        owner = self.fixture["owners"][0]
        entries = {
            entry["id"]: entry for entry in self.e01_fixture["entries"]
        }
        self.assertEqual(owner["e01_entries"], ["aio-first-pass-cache"])
        entry = entries["aio-first-pass-cache"]
        self.assertEqual(entry["module"], owner["module"])
        self.assertEqual(entry["owner"], owner["current_owner"])
        self.assertEqual(entry["target_phase"], "E-08b-complete")
        self.assertEqual(set(entry["symbols"]), set(owner["state_symbols"]))
        self.assertEqual(owner["target_phase"], "E-08b-complete")
        self.assertEqual(
            owner["target_owner"],
            "easyuse_anima.aio.first_pass_cache._DEFAULT_AIO_FIRST_PASS_CACHE",
        )
        self.assertEqual(
            self.fixture["decisions"]["generic_cache_lock_port"],
            "rejected",
        )

    def test_default_owner_holds_all_cache_specific_mutable_state(self):
        module = "easyuse_anima/aio/first_pass_cache.py"
        owner = self.fixture["owners"][0]
        bindings = _top_level_bindings(module)
        self.assertEqual(set(owner["state_symbols"]) - bindings, set())
        self.assertEqual(set(owner["policy_symbols"]) - bindings, set())
        self.assertEqual(
            _assignment_call(module, "_DEFAULT_AIO_FIRST_PASS_CACHE"),
            "_AIOFirstPassCacheStore",
        )
        self.assertEqual(
            ast.unparse(_assignment_value(module, "_AIO_FIRST_PASS_CACHE")),
            "_DEFAULT_AIO_FIRST_PASS_CACHE._cache",
        )
        self.assertEqual(
            ast.unparse(
                _assignment_value(module, "_AIO_FIRST_PASS_CACHE_ORDER")
            ),
            "_DEFAULT_AIO_FIRST_PASS_CACHE._order",
        )

        component = owner["components"][0]
        initializer = _class_method(
            module,
            component["class"],
            "__init__",
        )
        self.assertEqual(
            _self_attributes(initializer),
            set(component["state_symbols"]),
        )
        self.assertIn("RLock", _called(initializer))
        self.assertEqual(
            {
                "_AIO_FIRST_PASS_CACHE_ENABLED",
                "_AIO_FIRST_PASS_CACHE_GENERATION",
                "_AIO_FIRST_PASS_CACHE_LOCK",
                "_AIO_FIRST_PASS_CACHE_METRICS",
            }
            & bindings,
            set(),
        )

        method_attributes: set[str] = set()
        for method_name in (
            "_collections",
            "total_bytes",
            "metrics_snapshot",
            "reset_metrics",
            "record_metric",
            "clear",
            "set_enabled",
            "get",
            "put",
        ):
            method_attributes.update(
                _self_attributes(
                    _class_method(
                        module,
                        component["class"],
                        method_name,
                    )
                )
            )
        self.assertEqual(
            set(component["state_symbols"]) - method_attributes,
            set(),
        )

    def test_cleanup_and_metrics_dispositions_are_current(self):
        module = "easyuse_anima/aio/first_pass_cache.py"
        owner_class = self.fixture["owners"][0]["components"][0]["class"]
        clear = _class_method(module, owner_class, "clear")
        self.assertTrue(
            {"_generation", "_lock"} <= _self_attributes(clear)
        )
        self.assertEqual(
            {"_enabled", "_metrics"} & _self_attributes(clear),
            set(),
        )
        self.assertIn("clear", _called(clear))

        enable = _class_method(
            module,
            owner_class,
            "set_enabled",
        )
        self.assertTrue(
            {"_enabled", "_generation", "_lock"}
            <= _self_attributes(enable)
        )
        self.assertNotIn(
            "_metrics",
            _self_attributes(enable),
        )

        reset = _class_method(
            module,
            owner_class,
            "reset_metrics",
        )
        self.assertTrue(
            {"_lock", "_metrics"} <= _self_attributes(reset)
        )
        self.assertEqual(
            {"_cache", "_enabled", "_generation", "_order"}
            & _self_attributes(reset),
            set(),
        )

        for facade in (
            "_aio_first_pass_cache_total_bytes",
            "_aio_first_pass_cache_metrics_snapshot",
            "_reset_aio_first_pass_cache_metrics",
            "_record_aio_first_pass_cache_metric",
            "_clear_aio_first_pass_cache",
            "_set_aio_first_pass_cache_enabled",
            "_get_aio_first_pass_cache",
            "_put_aio_first_pass_cache",
        ):
            with self.subTest(facade=facade):
                self.assertIn(
                    "_DEFAULT_AIO_FIRST_PASS_CACHE",
                    _references(_top_level_function(module, facade)),
                )

    def test_entry_policy_and_module_import_boundary_are_current(self):
        module = "easyuse_anima/aio/first_pass_cache.py"
        expected_policy = {
            "AIO_FIRST_PASS_CACHE_MAX_ENTRIES": "2",
            "AIO_FIRST_PASS_CACHE_MAX_BYTES": "512 * 1024 * 1024",
            "AIO_FIRST_PASS_CACHE_MAX_ENTRY_BYTES": "256 * 1024 * 1024",
            "AIO_FIRST_PASS_CACHE_TTL_SECONDS": "300.0",
        }
        for name, expected in expected_policy.items():
            with self.subTest(policy=name):
                self.assertEqual(
                    ast.unparse(_assignment_value(module, name)),
                    expected,
                )

        entry = _top_level_class(module, "_AIOFirstPassCacheEntry")
        dataclass_decorator = next(
            decorator
            for decorator in entry.decorator_list
            if isinstance(decorator, ast.Call)
            and isinstance(decorator.func, ast.Name)
            and decorator.func.id == "dataclass"
        )
        self.assertEqual(
            {
                keyword.arg: keyword.value.value
                for keyword in dataclass_decorator.keywords
                if keyword.arg
                and isinstance(keyword.value, ast.Constant)
            },
            {"frozen": True, "slots": True},
        )
        all_value = _assignment_value(module, "__all__")
        self.assertIsInstance(all_value, ast.Tuple)
        self.assertEqual(all_value.elts, [])

        forbidden = set(
            self.fixture["import_direction"]["forbidden_imports"]
        )
        for feature_module in self.fixture["import_direction"][
            "feature_modules"
        ]:
            with self.subTest(module=feature_module):
                self.assertEqual(
                    _imported_modules(feature_module) & forbidden,
                    set(),
                )

    def test_canonical_first_pass_adapter_uses_injected_cache_callables(self):
        adapter = self.fixture["adapter_boundary"]
        runtime = adapter["runtime_record"]
        runtime_fields = {
            statement.target.id
            for statement in _top_level_class(
                runtime["module"],
                runtime["class"],
            ).body
            if isinstance(statement, ast.AnnAssign)
            and isinstance(statement.target, ast.Name)
        }
        self.assertTrue(set(runtime["fields"]) <= runtime_fields)

        stage = adapter["stage"]
        stage_method = _class_method(
            stage["module"],
            stage["class"],
            stage["method"],
        )
        self.assertEqual(set(stage["calls"]) - _called(stage_method), set())

        composition = adapter["composition"]
        composition_function = _top_level_function(
            composition["module"],
            composition["function"],
        )
        self.assertEqual(
            set(composition["uses"]) - _references(composition_function),
            set(),
        )

        for caller in self.fixture["production_callers"]:
            self.assertEqual(
                set(caller["uses"])
                - _references(
                    _top_level_function(
                        caller["module"],
                        caller["function"],
                    )
                ),
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
        all_value = _assignment_value(interface["module"], "__all__")
        self.assertIsInstance(all_value, ast.Tuple)
        self.assertEqual(all_value.elts, [])

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
            "easyuse_anima.aio.first_pass_cache._DEFAULT_AIO_FIRST_PASS_CACHE",
        )

        forbidden_modules = {"runtime", "bootstrap", "nodes"}
        for module in self.fixture["import_direction"]["feature_modules"]:
            with self.subTest(module=module):
                self.assertEqual(
                    {
                        imported_module
                        for imported_module in _imported_modules(module)
                        if imported_module.split(".")[-1] in forbidden_modules
                    },
                    set(),
                )

    def test_canonical_patch_seams_remain_and_root_facade_is_retired(self):
        surface = next(
            surface
            for surface in self.fixture["compatibility_surfaces"]
            if surface["kind"] == "dynamic_reference"
        )
        bindings = _top_level_bindings(surface["module"])
        self.assertEqual(set(surface["symbols"]) - bindings, set())
        self.assertFalse((ROOT / "nodes.py").exists())

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
