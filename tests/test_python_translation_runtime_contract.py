from __future__ import annotations

import ast
import json
import unittest
from functools import lru_cache
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PATH = (
    ROOT / "tests" / "fixtures" / "python_translation_runtime_contract.v1.json"
)
E01_FIXTURE_PATH = (
    ROOT / "tests" / "fixtures" / "python_runtime_state_ownership.v1.json"
)
CONTRACT_DOC = (
    ROOT
    / "docs"
    / "architecture"
    / "python-runtime-e04-translation-contract.md"
)


@lru_cache(maxsize=None)
def _tree(module: str) -> ast.Module:
    path = ROOT / module
    return ast.parse(
        path.read_text(encoding="utf-8-sig"),
        filename=str(path),
    )


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


def _expression_name(expression: ast.expr) -> str:
    if isinstance(expression, ast.Name):
        return expression.id
    if isinstance(expression, ast.Attribute):
        return expression.attr
    return ""


def _function_references(module: str, function_name: str) -> set[str]:
    function = _top_level_function(module, function_name)
    return {
        node.id
        for node in ast.walk(function)
        if isinstance(node, ast.Name)
    }


def _instance_assignments(module: str, class_name: str) -> set[str]:
    class_node = _top_level_class(module, class_name)
    assigned: set[str] = set()
    for node in ast.walk(class_node):
        target = None
        if isinstance(node, ast.Assign):
            for candidate in node.targets:
                if (
                    isinstance(candidate, ast.Attribute)
                    and isinstance(candidate.value, ast.Name)
                    and candidate.value.id == "self"
                ):
                    assigned.add(candidate.attr)
        elif isinstance(node, ast.AnnAssign):
            target = node.target
        if (
            isinstance(target, ast.Attribute)
            and isinstance(target.value, ast.Name)
            and target.value.id == "self"
        ):
            assigned.add(target.attr)
    return assigned


def _class_methods(module: str, class_name: str) -> set[str]:
    return {
        statement.name
        for statement in _top_level_class(module, class_name).body
        if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef))
    }


def _tuple_assignment_call(module: str, assigned_name: str) -> str:
    for statement in _tree(module).body:
        if not isinstance(statement, ast.Assign):
            continue
        if not any(assigned_name in _target_names(target) for target in statement.targets):
            continue
        if isinstance(statement.value, ast.Call):
            return _expression_name(statement.value.func)
    raise AssertionError(f"{module} has no call assignment for {assigned_name}")


class PythonTranslationRuntimeContractTests(unittest.TestCase):
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
        self.assertEqual(self.fixture["production_changes"], 8)
        self.assertEqual(
            [move["id"] for move in self.fixture["move_queue"]],
            ["E-04a", "E-04b", "E-04c", "E-04d", "E-04e"],
        )
        self.assertEqual(
            [move["status"] for move in self.fixture["move_queue"]],
            ["complete", "complete", "complete", "complete", "ready"],
        )
        self.assertEqual(
            [move["classification"] for move in self.fixture["move_queue"]],
            ["Contract", "Move", "Move", "Move", "Contract"],
        )
        for owner in self.fixture["owners"]:
            with self.subTest(owner=owner["id"]):
                self.assertTrue(owner["evidence"])
                for evidence in owner["evidence"]:
                    self.assertTrue((ROOT / evidence).is_file(), evidence)

    def test_e01_translation_entries_reconcile_to_exact_future_moves(self):
        e01_entries = {
            entry["id"]: entry for entry in self.e01_fixture["entries"]
        }
        owners = self.fixture["owners"]
        self.assertEqual(
            [owner["id"] for owner in owners],
            ["route-executor", "default-service", "provider-registry-client"],
        )
        self.assertEqual(
            {owner["e01_entry"] for owner in owners},
            {
                "root-translation-route-worker",
                "translation-default-service",
                "translation-provider-registry",
            },
        )
        for owner in owners:
            with self.subTest(owner=owner["id"]):
                e01 = e01_entries[owner["e01_entry"]]
                self.assertEqual(e01["module"], owner["module"])
                self.assertEqual(e01["owner"], owner["current_owner"])
                self.assertEqual(e01["target_phase"], owner["target_phase"])
                self.assertEqual(
                    set(owner["state_symbols"]) - set(e01["symbols"]),
                    set(),
                )
        declarative = {
            (entry["module"], symbol)
            for entry in self.e01_fixture["declarative_mutable_globals"]
            for symbol in entry["symbols"]
        }
        self.assertNotIn(
            (
                "easyuse_anima/translation/service.py",
                "_TRANSLATION_PROVIDER_FACTORIES",
            ),
            declarative,
        )

    def test_current_owner_components_bind_exact_shipped_state(self):
        for owner in self.fixture["owners"]:
            with self.subTest(owner=owner["id"]):
                self.assertEqual(
                    set(owner["state_symbols"])
                    - _top_level_bindings(owner["module"]),
                    set(),
                )
            for component in owner["components"]:
                with self.subTest(
                    owner=owner["id"],
                    component=component.get("class", component["module"]),
                ):
                    if component["state_kind"] == "top_level":
                        actual = _top_level_bindings(component["module"])
                    else:
                        actual = _instance_assignments(
                            component["module"],
                            component["class"],
                        )
                    self.assertEqual(
                        set(component["state_symbols"]) - actual,
                        set(),
                    )

        self.assertEqual(
            _tuple_assignment_call("api.py", "_PROMPT_TRANSLATION_WORKER"),
            "_build_translation_route_runtime",
        )
        bootstrap_runtime_references = _function_references(
            "easyuse_anima/bootstrap.py",
            "build_translation_route_runtime",
        )
        self.assertTrue(
            {
                "_PromptTranslationRouteExecutor",
                "_build_translation_runtime",
                "TranslationBusyError",
                "TranslationCancelledError",
                "TranslationTimeoutError",
                "atexit",
            }
            <= bootstrap_runtime_references
        )
        self.assertIn(
            "shutdown",
            _class_methods(
                "easyuse_anima/api/routes/translation_execution.py",
                "PromptTranslationRouteExecutor",
            ),
        )
        self.assertIn(
            "clear",
            _class_methods(
                "easyuse_anima/translation/service.py",
                "BoundedTranslationCache",
            ),
        )
        self.assertIn(
            "close",
            _class_methods(
                "easyuse_anima/translation/service.py",
                "PromptTranslationService",
            ),
        )
        self.assertNotIn(
            "close",
            _class_methods(
                "easyuse_anima/translation/providers/google.py",
                "GoogleTranslationProvider",
            ),
        )
        self.assertEqual(
            _class_methods(
                "easyuse_anima/translation/provider_registry.py",
                "_TranslationProviderRegistry",
            ),
            {"__init__", "get"},
        )

    def test_production_callers_and_dynamic_compatibility_seams_are_current(self):
        owner_ids = {owner["id"] for owner in self.fixture["owners"]}
        for caller in self.fixture["production_callers"]:
            with self.subTest(caller=caller["entry"]):
                self.assertIn(caller["owner"], owner_ids)
                references = _function_references(
                    caller["module"],
                    caller.get("function", caller["entry"]),
                )
                self.assertEqual(set(caller["uses"]) - references, set())

        for surface in self.fixture["compatibility_surfaces"]:
            with self.subTest(surface=surface["id"]):
                self.assertEqual(
                    set(surface["symbols"])
                    - _top_level_bindings(surface["module"]),
                    set(),
                )

        root_references = _function_references(
            "easyuse_anima/api/routes/translation.py",
            "build_translation_runtime",
        )
        self.assertTrue(
            {
                "get_worker",
                "get_translate_prompt_sync",
                "get_timeout_seconds",
                "register_shutdown",
            }
            <= root_references
        )

    def test_optional_client_stays_lazy_and_no_generic_runtime_port_exists(self):
        provider_tree = _tree(
            "easyuse_anima/translation/providers/google.py"
        )
        top_level_googletrans_imports = [
            statement
            for statement in provider_tree.body
            if isinstance(statement, (ast.Import, ast.ImportFrom))
            and any(
                alias.name.startswith("googletrans")
                for alias in statement.names
            )
        ]
        self.assertEqual(top_level_googletrans_imports, [])

        create_translator = None
        for statement in _top_level_class(
            "easyuse_anima/translation/providers/google.py",
            "GoogleTranslationProvider",
        ).body:
            if (
                isinstance(statement, ast.FunctionDef)
                and statement.name == "_create_translator"
            ):
                create_translator = statement
                break
        self.assertIsNotNone(create_translator)
        local_imports = [
            node
            for node in ast.walk(create_translator)
            if isinstance(node, ast.ImportFrom)
            and node.module == "googletrans"
        ]
        self.assertEqual(len(local_imports), 1)

        runtime = _top_level_class("easyuse_anima/runtime.py", "RuntimeServices")
        runtime_fields = {
            statement.target.id
            for statement in runtime.body
            if isinstance(statement, ast.AnnAssign)
            and isinstance(statement.target, ast.Name)
        }
        self.assertEqual(
            runtime_fields,
            {
                "clock",
                "comfy",
                "config",
                "seed_reservations",
                "translation",
            },
        )
        self.assertEqual(
            _class_methods(
                "easyuse_anima/translation/ports.py",
                "PromptTranslationPort",
            ),
            {"close", "translate_prompt"},
        )
        bootstrap_references = _function_references(
            "easyuse_anima/bootstrap.py",
            "initialize",
        )
        self.assertTrue(
            {
                "BoundedTranslationCache",
                "PromptTranslationService",
                "RuntimeServices",
                "_install_default_translation_service",
            }
            <= bootstrap_references
        )
        self.assertEqual(
            self.fixture["decisions"]["generic_executor_client_port"],
            "rejected",
        )
        for module in (
            "easyuse_anima/translation/service.py",
            "easyuse_anima/translation/providers/google.py",
        ):
            imports = [
                node.module
                for node in ast.walk(_tree(module))
                if isinstance(node, ast.ImportFrom)
            ]
            self.assertNotIn("runtime", imports)

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
