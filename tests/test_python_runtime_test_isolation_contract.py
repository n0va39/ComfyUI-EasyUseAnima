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
    / "python_runtime_test_isolation_contract.v1.json"
)
E01_FIXTURE_PATH = (
    ROOT / "tests" / "fixtures" / "python_runtime_state_ownership.v1.json"
)
E09_FIXTURE_PATH = (
    ROOT / "tests" / "fixtures" / "python_runtime_lifecycle_contract.v1.json"
)
CONTRACT_DOC = (
    ROOT
    / "docs"
    / "architecture"
    / "python-runtime-e10-test-isolation-contract.md"
)
ROADMAP = ROOT / "docs" / "architecture" / "backend-roadmap-resume-0.6.2.md"

_PRIVATE_RUNTIME_STATE = {
    "_ATEXIT_REGISTERED",
    "_DEFAULT_RUNTIME",
    "_DEFAULT_TRANSLATION_SERVICE",
    "_RUNTIME_SERVICES",
    "_SHUTDOWN",
    "_TRANSLATION_ROUTE_EXECUTOR",
    "_WILDCARDS_INITIALIZED",
}


@lru_cache(maxsize=None)
def _tree(path: Path) -> ast.Module:
    return ast.parse(
        path.read_text(encoding="utf-8-sig"),
        filename=str(path),
    )


def _relative(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def _private_mutation_sites() -> dict[str, list[str]]:
    sites: dict[str, set[str]] = {}
    for path in sorted((ROOT / "tests").rglob("*.py")):
        symbols: set[str] = set()
        for node in ast.walk(_tree(path)):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr == "object"
                and len(node.args) >= 2
                and isinstance(node.args[1], ast.Constant)
                and node.args[1].value in _PRIVATE_RUNTIME_STATE
            ):
                symbols.add(node.args[1].value)
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id == "setattr"
                and len(node.args) >= 2
                and isinstance(node.args[1], ast.Constant)
                and node.args[1].value in _PRIVATE_RUNTIME_STATE
            ):
                symbols.add(node.args[1].value)
            targets: list[ast.expr] = []
            if isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
                targets = (
                    list(node.targets)
                    if isinstance(node, ast.Assign)
                    else [node.target]
                )
            for target in targets:
                if (
                    isinstance(target, ast.Attribute)
                    and target.attr in _PRIVATE_RUNTIME_STATE
                ):
                    symbols.add(target.attr)
        if symbols:
            sites[_relative(path)] = symbols
    return {
        module: sorted(symbols)
        for module, symbols in sorted(sites.items())
    }


def _module_reload_sites() -> list[str]:
    sites = []
    for path in sorted((ROOT / "tests").rglob("*.py")):
        for node in ast.walk(_tree(path)):
            if not isinstance(node, ast.Call):
                continue
            if isinstance(node.func, ast.Name) and node.func.id == "reload":
                sites.append(_relative(path))
                break
            if (
                isinstance(node.func, ast.Attribute)
                and node.func.attr == "reload"
            ):
                sites.append(_relative(path))
                break
    return sites


def _top_level_functions(module: str) -> set[str]:
    return {
        node.name
        for node in _tree(ROOT / module).body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }


class PythonRuntimeTestIsolationContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
        cls.e01_fixture = json.loads(
            E01_FIXTURE_PATH.read_text(encoding="utf-8")
        )
        cls.e09_fixture = json.loads(
            E09_FIXTURE_PATH.read_text(encoding="utf-8")
        )

    def test_schema_queue_and_evidence_are_complete(self):
        self.assertEqual(
            set(self.fixture),
            {
                "base_sha",
                "classification",
                "current_inventory",
                "evidence",
                "implementation_boundary",
                "production_changes",
                "queue",
                "schema_version",
                "scope",
                "target_fixture",
            },
        )
        self.assertEqual(self.fixture["schema_version"], 1)
        self.assertEqual(self.fixture["classification"], "Contract")
        self.assertEqual(self.fixture["production_changes"], 0)
        self.assertEqual(
            [item["id"] for item in self.fixture["queue"]],
            ["E-10a", "E-10b", "E-10c"],
        )
        self.assertEqual(
            [item["classification"] for item in self.fixture["queue"]],
            ["Contract", "Move", "Contract"],
        )
        self.assertEqual(
            [item["status"] for item in self.fixture["queue"]],
            ["complete", "ready", "blocked-on-E-10b"],
        )
        for evidence in self.fixture["evidence"]:
            self.assertTrue((ROOT / evidence).is_file(), evidence)

    def test_current_reload_and_private_mutation_inventory_is_exact(self):
        inventory = self.fixture["current_inventory"]
        expected_mutations = {
            item["module"]: item["symbols"]
            for item in inventory["private_mutation_sites"]
        }
        self.assertEqual(_module_reload_sites(), inventory["module_reload_sites"])
        self.assertEqual(_private_mutation_sites(), expected_mutations)
        self.assertEqual(inventory["module_reload_sites"], [])

    def test_target_fixture_has_one_test_only_serialized_owner(self):
        target = self.fixture["target_fixture"]
        self.assertTrue(target["single_owner"])
        self.assertEqual(target["module"], "tests/runtime_test_support.py")
        self.assertEqual(target["production_reset_api"], "forbidden")
        self.assertIn("RLock", target["synchronization"])
        self.assertEqual(
            set(target["private_mutation_symbols"]),
            _PRIVATE_RUNTIME_STATE,
        )
        modes = {item["id"]: item for item in target["modes"]}
        self.assertEqual(
            set(modes),
            {
                "bootstrap-lifecycle",
                "constructed-runtime",
                "installed-runtime",
            },
        )
        self.assertEqual(
            modes["constructed-runtime"]["parallelism"],
            "parallel-safe",
        )
        self.assertEqual(
            {
                modes["installed-runtime"]["parallelism"],
                modes["bootstrap-lifecycle"]["parallelism"],
            },
            {"serialized-process-global"},
        )

    def test_production_reset_and_hot_reinitialize_remain_forbidden(self):
        boundary = self.fixture["implementation_boundary"]
        self.assertEqual(boundary["production_changes"], 0)
        self.assertIn("production-reset-api", boundary["forbidden"])
        self.assertIn("hot-shutdown-reinitialize", boundary["forbidden"])
        for module in ("easyuse_anima/runtime.py", "easyuse_anima/bootstrap.py"):
            with self.subTest(module=module):
                self.assertNotIn("reset_runtime", _top_level_functions(module))
        self.assertEqual(
            self.e09_fixture["lifecycle_owner"]["shutdown_state"],
            "terminal",
        )
        self.assertEqual(
            self.e09_fixture["lifecycle_owner"]["initialize_after_shutdown"],
            "raise-before-callbacks",
        )

    def test_e09_and_e01_are_complete_before_test_fixture_migration(self):
        self.assertEqual(
            [item["status"] for item in self.e09_fixture["sequence"]],
            ["complete", "complete", "complete"],
        )
        self.assertEqual(
            self.e09_fixture["completion_audit"]["ambiguous_state_owners"],
            [],
        )
        self.assertNotIn(
            "E-09",
            {
                entry["target_phase"]
                for entry in self.e01_fixture["entries"]
            },
        )

    def test_contract_document_and_current_queue_are_linked(self):
        self.assertTrue(CONTRACT_DOC.is_file())
        architecture_entry = (
            ROOT / "docs" / "architecture" / "README.md"
        ).read_text(encoding="utf-8")
        development_entry = (
            ROOT / "docs" / "development" / "README.md"
        ).read_text(encoding="utf-8")
        roadmap = ROADMAP.read_text(encoding="utf-8")
        self.assertIn(CONTRACT_DOC.name, architecture_entry)
        self.assertIn(
            f"../architecture/{CONTRACT_DOC.name}",
            development_entry,
        )
        for task_id in ("E-10a", "E-10b", "E-10c"):
            self.assertIn(task_id, roadmap)
        self.assertIn("E-10b is the next READY task", roadmap)


if __name__ == "__main__":
    unittest.main()
