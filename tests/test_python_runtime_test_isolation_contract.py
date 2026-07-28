from __future__ import annotations

import ast
import json
import threading
import unittest
from functools import lru_cache
from pathlib import Path

from easyuse_anima import bootstrap, runtime as runtime_module
from easyuse_anima.translation import service as translation_service
from tests.runtime_test_support import (
    build_runtime_services,
    isolated_bootstrap_runtime,
    isolated_installed_runtime,
    isolated_translation_facade,
)


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
                "completion_audit",
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
            ["complete", "complete", "complete"],
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
        helper = self.fixture["target_fixture"]["module"]
        self.assertEqual(
            {
                module: symbols
                for module, symbols in expected_mutations.items()
                if module != helper
            },
            {},
        )

    def test_completion_audit_closes_phase_e_without_new_behavior(self):
        audit = self.fixture["completion_audit"]
        self.assertEqual(audit["ambiguous_test_reset_owners"], [])
        self.assertEqual(
            audit["direct_private_mutation_sites_outside_helper"],
            [],
        )
        self.assertEqual(audit["module_reload_sites"], [])
        self.assertEqual(audit["phase_e_status"], "complete")
        self.assertEqual(audit["production_changes"], 0)
        self.assertIn(
            "inspect private state",
            audit["retained_read_only_assertion_policy"],
        )

    def test_target_fixture_has_one_test_only_serialized_owner(self):
        target = self.fixture["target_fixture"]
        self.assertTrue(target["single_owner"])
        self.assertEqual(target["module"], "tests/runtime_test_support.py")
        self.assertTrue((ROOT / target["module"]).is_file())
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
        self.assertIn("Phase E is complete", roadmap)
        self.assertIn("E-10c", roadmap)


class PythonRuntimeTestSupportTests(unittest.TestCase):
    def test_constructed_runtimes_are_independent_and_not_installed(self):
        prior = runtime_module._RUNTIME_SERVICES
        values = {
            "comfy": object(),
            "seed_reservations": object(),
            "config": object(),
            "clock": object(),
            "translation": object(),
            "autocomplete": object(),
            "wildcard_snapshots": object(),
            "aio_first_pass_cache": object(),
        }

        first = build_runtime_services(runtime_module, **values)
        second = build_runtime_services(runtime_module, **values)

        self.assertIsNot(first, second)
        self.assertIs(runtime_module._RUNTIME_SERVICES, prior)

    def test_installed_runtime_context_is_nested_and_identity_restoring(self):
        prior = runtime_module._RUNTIME_SERVICES
        first = object()
        second = object()

        with self.assertRaisesRegex(RuntimeError, "stop"):
            with isolated_installed_runtime(runtime_module, first):
                self.assertIs(runtime_module._RUNTIME_SERVICES, first)
                with isolated_installed_runtime(runtime_module, second):
                    self.assertIs(runtime_module._RUNTIME_SERVICES, second)
                self.assertIs(runtime_module._RUNTIME_SERVICES, first)
                raise RuntimeError("stop")

        self.assertIs(runtime_module._RUNTIME_SERVICES, prior)

    def test_bootstrap_context_suppresses_atexit_and_restores_exact_state(self):
        prior = {
            "runtime": runtime_module._RUNTIME_SERVICES,
            "default_runtime": bootstrap._DEFAULT_RUNTIME,
            "executor": bootstrap._TRANSLATION_ROUTE_EXECUTOR,
            "atexit_registered": bootstrap._ATEXIT_REGISTERED,
            "shutdown": bootstrap._SHUTDOWN,
            "wildcards": bootstrap._WILDCARDS_INITIALIZED,
            "facade": translation_service._DEFAULT_TRANSLATION_SERVICE,
            "register": bootstrap.atexit.register,
        }

        with self.assertRaisesRegex(RuntimeError, "stop"):
            with isolated_bootstrap_runtime(
                bootstrap,
                runtime_module,
                translation_service,
            ):
                self.assertIsNone(runtime_module._RUNTIME_SERVICES)
                self.assertIsNone(bootstrap._DEFAULT_RUNTIME)
                self.assertIsNone(bootstrap._TRANSLATION_ROUTE_EXECUTOR)
                self.assertFalse(bootstrap._ATEXIT_REGISTERED)
                self.assertFalse(bootstrap._SHUTDOWN)
                self.assertFalse(bootstrap._WILDCARDS_INITIALIZED)
                self.assertIsNot(
                    translation_service._DEFAULT_TRANSLATION_SERVICE,
                    prior["facade"],
                )
                self.assertIsNot(bootstrap.atexit.register, prior["register"])
                raise RuntimeError("stop")

        self.assertIs(runtime_module._RUNTIME_SERVICES, prior["runtime"])
        self.assertIs(bootstrap._DEFAULT_RUNTIME, prior["default_runtime"])
        self.assertIs(
            bootstrap._TRANSLATION_ROUTE_EXECUTOR,
            prior["executor"],
        )
        self.assertIs(bootstrap._ATEXIT_REGISTERED, prior["atexit_registered"])
        self.assertIs(bootstrap._SHUTDOWN, prior["shutdown"])
        self.assertIs(bootstrap._WILDCARDS_INITIALIZED, prior["wildcards"])
        self.assertIs(
            translation_service._DEFAULT_TRANSLATION_SERVICE,
            prior["facade"],
        )
        self.assertIs(bootstrap.atexit.register, prior["register"])

    def test_translation_facade_context_restores_after_failure(self):
        prior = translation_service._DEFAULT_TRANSLATION_SERVICE
        replacement = object()

        with self.assertRaisesRegex(RuntimeError, "stop"):
            with isolated_translation_facade(
                translation_service,
                replacement,
            ):
                self.assertIs(
                    translation_service._DEFAULT_TRANSLATION_SERVICE,
                    replacement,
                )
                raise RuntimeError("stop")

        self.assertIs(
            translation_service._DEFAULT_TRANSLATION_SERVICE,
            prior,
        )

    def test_process_global_contexts_are_serialized_for_full_lifetime(self):
        first_entered = threading.Event()
        release_first = threading.Event()
        second_entered = threading.Event()

        def hold_first():
            with isolated_installed_runtime(runtime_module, object()):
                first_entered.set()
                release_first.wait(timeout=1)

        def enter_second():
            first_entered.wait(timeout=1)
            with isolated_installed_runtime(runtime_module, object()):
                second_entered.set()

        first = threading.Thread(target=hold_first)
        second = threading.Thread(target=enter_second)
        first.start()
        second.start()
        try:
            self.assertTrue(first_entered.wait(timeout=1))
            self.assertFalse(second_entered.wait(timeout=0.05))
        finally:
            release_first.set()
            first.join(timeout=1)
            second.join(timeout=1)

        self.assertFalse(first.is_alive())
        self.assertFalse(second.is_alive())
        self.assertTrue(second_entered.is_set())


if __name__ == "__main__":
    unittest.main()
