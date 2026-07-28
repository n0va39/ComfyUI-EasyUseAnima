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
    / "python_repository_filesystem_contract.v1.json"
)
CONTRACT_DOC = (
    ROOT
    / "docs"
    / "architecture"
    / "python-runtime-e03-repository-filesystem-contract.md"
)


@lru_cache(maxsize=None)
def _tree(module: str) -> ast.Module:
    path = ROOT / module
    return ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path))


def _top_level_function(module: str, name: str) -> ast.FunctionDef:
    for statement in _tree(module).body:
        if isinstance(statement, ast.FunctionDef) and statement.name == name:
            return statement
    raise AssertionError(f"{module} has no top-level function {name}")


def _top_level_class(module: str, name: str) -> ast.ClassDef:
    for statement in _tree(module).body:
        if isinstance(statement, ast.ClassDef) and statement.name == name:
            return statement
    raise AssertionError(f"{module} has no top-level class {name}")


def _assignment_expression(module: str, name: str) -> str:
    for statement in _tree(module).body:
        if isinstance(statement, ast.Assign):
            if any(
                isinstance(target, ast.Name) and target.id == name
                for target in statement.targets
            ):
                return ast.unparse(statement.value)
        if (
            isinstance(statement, ast.AnnAssign)
            and isinstance(statement.target, ast.Name)
            and statement.target.id == name
            and statement.value is not None
        ):
            return ast.unparse(statement.value)
    raise AssertionError(f"{module} has no top-level assignment {name}")


def _expression_name(expression: ast.expr) -> str:
    if isinstance(expression, ast.Name):
        return expression.id
    if isinstance(expression, ast.Attribute):
        owner = _expression_name(expression.value)
        return f"{owner}.{expression.attr}" if owner else expression.attr
    if isinstance(expression, ast.Call):
        owner = _expression_name(expression.func)
        return f"{owner}()" if owner else ""
    return ""


def _function_calls(module: str, name: str) -> set[str]:
    function = _top_level_function(module, name)
    return {
        call_name
        for node in ast.walk(function)
        if isinstance(node, ast.Call)
        if (call_name := _expression_name(node.func))
    }


def _function_parameters(module: str, name: str) -> set[str]:
    function = _top_level_function(module, name)
    return {
        argument.arg
        for argument in (
            *function.args.posonlyargs,
            *function.args.args,
            *function.args.kwonlyargs,
        )
    }


def _class_methods(module: str, name: str) -> dict[str, ast.FunctionDef]:
    return {
        statement.name: statement
        for statement in _top_level_class(module, name).body
        if isinstance(statement, ast.FunctionDef)
    }


def _import_source(module: str, symbol: str) -> str | None:
    for statement in _tree(module).body:
        if not isinstance(statement, ast.ImportFrom):
            continue
        for alias in statement.names:
            if (alias.asname or alias.name) == symbol:
                return f"{'.' * statement.level}{statement.module or ''}"
    return None


def _normalized_source(path: Path) -> str:
    return "".join(path.read_text(encoding="utf-8-sig").split())


def _normalized_source_token(value: str) -> str:
    return "".join(value.split())


class PythonRepositoryFilesystemContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

    def test_schema_ids_and_evidence_are_complete(self):
        self.assertEqual(
            set(self.fixture),
            {
                "compatibility_bindings",
                "decisions",
                "lock_order",
                "monkeypatch_seams",
                "move_queue",
                "owners",
                "repository_lanes",
                "schema_version",
                "scope",
            },
        )
        self.assertEqual(self.fixture["schema_version"], 1)
        self.assertEqual(
            [owner["id"] for owner in self.fixture["owners"]],
            ["atomic-json-store", "profile-directory-coordinator"],
        )
        self.assertEqual(
            [lane["id"] for lane in self.fixture["repository_lanes"]],
            ["settings", "profile-shared", "lora-profile", "aio-profile"],
        )
        self.assertEqual(
            [move["id"] for move in self.fixture["move_queue"]],
            ["E-03b", "E-03c", "E-03d", "E-03e"],
        )
        self.assertEqual(
            [move["status"] for move in self.fixture["move_queue"]],
            ["complete", "ready", "pending", "pending"],
        )

        evidence = {
            path
            for owner in self.fixture["owners"]
            for path in owner["test_evidence"]
        }
        evidence.update(
            path
            for lane in self.fixture["repository_lanes"]
            for path in lane["test_evidence"]
        )
        evidence.update(
            path
            for lock in self.fixture["lock_order"]
            for path in lock["evidence"]
        )
        evidence.update(
            seam["evidence"] for seam in self.fixture["monkeypatch_seams"]
        )
        for path in sorted(evidence):
            with self.subTest(evidence=path):
                self.assertTrue((ROOT / path).is_file(), path)

    def test_current_owners_keep_constructor_methods_and_symbols(self):
        atomic = self.fixture["owners"][0]
        atomic_methods = _class_methods(atomic["module"], "AtomicJsonStore")
        self.assertEqual(set(atomic["methods"]) - set(atomic_methods), set())
        constructor = atomic_methods["__init__"]
        parameters = [
            argument.arg
            for argument in (
                *constructor.args.posonlyargs,
                *constructor.args.args,
                *constructor.args.kwonlyargs,
            )
            if argument.arg != "self"
        ]
        self.assertEqual(parameters, atomic["constructor"]["parameters"])
        self.assertEqual(
            ast.unparse(constructor.args.kw_defaults[0]),
            atomic["constructor"]["backup_default"],
        )
        self.assertEqual(
            _assignment_expression(atomic["module"], "_PATH_LOCKS"),
            "{}",
        )
        self.assertEqual(
            _assignment_expression(atomic["module"], "_PATH_LOCKS_GUARD"),
            "threading.Lock()",
        )
        self.assertEqual(atomic["factory"], "create_atomic_json_store")
        self.assertEqual(
            {"AtomicJsonStore"}
            - _function_calls(atomic["module"], atomic["factory"]),
            set(),
        )

        profile = self.fixture["owners"][1]
        profile_methods = _class_methods(
            profile["module"],
            "DirectoryMutationCoordinator",
        )
        self.assertEqual(set(profile["methods"]) - set(profile_methods), set())
        self.assertEqual(
            _assignment_expression(
                profile["module"],
                "PROFILE_MUTATION_COORDINATOR",
            ),
            "DirectoryMutationCoordinator()",
        )

    def test_repository_paths_parameters_and_calls_match_current_source(self):
        for lane in self.fixture["repository_lanes"]:
            module = lane["module"]
            for path_input in lane["path_inputs"]:
                with self.subTest(lane=lane["id"], path=path_input["symbol"]):
                    self.assertEqual(
                        _assignment_expression(module, path_input["symbol"]),
                        path_input["expression"],
                    )
            for optional in lane.get("optional_path_parameters", []):
                with self.subTest(lane=lane["id"], parameter=optional):
                    self.assertIn(
                        optional["parameter"],
                        _function_parameters(module, optional["function"]),
                    )
            for contract in lane["function_contracts"]:
                with self.subTest(lane=lane["id"], function=contract["function"]):
                    self.assertEqual(
                        set(contract["required_calls"])
                        - _function_calls(module, contract["function"]),
                        set(),
                    )
            module_source = _normalized_source(ROOT / module)
            for dependency in lane["dynamic_dependencies"]:
                with self.subTest(
                    lane=lane["id"],
                    dependency=dependency["dependency"],
                ):
                    self.assertIn(
                        _normalized_source_token(dependency["token"]),
                        module_source,
                    )

    def test_root_compatibility_bindings_and_patch_seams_are_preserved(self):
        for binding in self.fixture["compatibility_bindings"]:
            with self.subTest(symbol=binding["symbol"]):
                if binding["kind"] == "assignment":
                    self.assertEqual(
                        _assignment_expression(
                            binding["module"],
                            binding["symbol"],
                        ),
                        binding["expression"],
                    )
                else:
                    self.assertEqual(
                        _import_source(binding["module"], binding["symbol"]),
                        binding["source"],
                    )

        for seam in self.fixture["monkeypatch_seams"]:
            with self.subTest(target=seam["target"]):
                self.assertIn(
                    _normalized_source_token(seam["token"]),
                    _normalized_source(ROOT / seam["evidence"]),
                )

    def test_decisions_lock_order_and_next_moves_are_explicit(self):
        self.assertEqual(
            set(self.fixture["decisions"]),
            {
                "dynamic_host_dependencies",
                "filesystem_factory",
                "path_lock_owner",
                "profile_directory_owner",
                "runtime_access",
            },
        )
        for decision in self.fixture["decisions"].values():
            self.assertTrue(decision.strip())
        self.assertEqual(
            [entry["id"] for entry in self.fixture["lock_order"]],
            [
                "atomic-multi-path",
                "profile-mutation",
                "settings-reentrant-path",
            ],
        )
        self.assertEqual(
            [move["classification"] for move in self.fixture["move_queue"]],
            ["Move", "Move", "Move", "Contract"],
        )

    def test_contract_document_is_linked_from_maintained_entries(self):
        self.assertTrue(CONTRACT_DOC.is_file())
        link = CONTRACT_DOC.name
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
