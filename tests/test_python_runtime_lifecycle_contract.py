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
    / "python_runtime_lifecycle_contract.v1.json"
)
E01_FIXTURE_PATH = (
    ROOT / "tests" / "fixtures" / "python_runtime_state_ownership.v1.json"
)
CONTRACT_DOC = (
    ROOT
    / "docs"
    / "architecture"
    / "python-runtime-e09-lifecycle-contract.md"
)
ROADMAP = ROOT / "docs" / "architecture" / "backend-roadmap-resume-0.6.2.md"


@lru_cache(maxsize=None)
def _tree(module: str) -> ast.Module:
    path = ROOT / module
    return ast.parse(
        path.read_text(encoding="utf-8-sig"),
        filename=str(path),
    )


def _top_level_function_names(module: str) -> set[str]:
    return {
        statement.name
        for statement in _tree(module).body
        if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef))
    }


def _class_method_names(module: str, class_name: str) -> set[str]:
    for statement in _tree(module).body:
        if isinstance(statement, ast.ClassDef) and statement.name == class_name:
            return {
                member.name
                for member in statement.body
                if isinstance(member, (ast.FunctionDef, ast.AsyncFunctionDef))
            }
    raise AssertionError(f"{module} has no class {class_name}")


def _assignment_value(module: str, name: str) -> ast.expr:
    for statement in _tree(module).body:
        if isinstance(statement, ast.Assign):
            if any(
                isinstance(target, ast.Name) and target.id == name
                for target in statement.targets
            ):
                return statement.value
        elif (
            isinstance(statement, ast.AnnAssign)
            and isinstance(statement.target, ast.Name)
            and statement.target.id == name
        ):
            return statement.value
    raise AssertionError(f"{module} has no assignment for {name}")


def _literal_string_sequence(module: str, name: str) -> list[str]:
    value = _assignment_value(module, name)
    if not isinstance(value, (ast.List, ast.Tuple)):
        raise AssertionError(f"{module}.{name} is not a literal sequence")
    return [
        element.value
        for element in value.elts
        if isinstance(element, ast.Constant) and isinstance(element.value, str)
    ]


def _name_reference_count(module: str, name: str) -> int:
    return sum(
        1
        for node in ast.walk(_tree(module))
        if isinstance(node, ast.Name) and node.id == name
    )


class PythonRuntimeLifecycleContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
        cls.e01_fixture = json.loads(
            E01_FIXTURE_PATH.read_text(encoding="utf-8")
        )

    def test_schema_sequence_and_evidence_are_complete(self):
        self.assertEqual(
            set(self.fixture),
            {
                "base_sha",
                "classification",
                "cleanup_order",
                "completion_audit",
                "current_state",
                "e01_dispositions",
                "evidence",
                "implementation_boundary",
                "lifecycle_owner",
                "preserved_initialize",
                "production_changes",
                "public_surface",
                "retained_noops",
                "rollback_contract",
                "schema_version",
                "scope",
                "sequence",
                "warning_dedupe",
            },
        )
        self.assertEqual(self.fixture["schema_version"], 1)
        self.assertEqual(self.fixture["classification"], "Contract")
        self.assertEqual(self.fixture["production_changes"], 5)
        self.assertEqual(
            [item["id"] for item in self.fixture["sequence"]],
            ["E-09a", "E-09b", "E-09c"],
        )
        self.assertEqual(
            [item["classification"] for item in self.fixture["sequence"]],
            ["Contract", "LIFECYCLE", "Contract"],
        )
        self.assertEqual(
            [item["status"] for item in self.fixture["sequence"]],
            ["complete", "complete", "complete"],
        )
        for evidence in self.fixture["evidence"]:
            self.assertTrue((ROOT / evidence).is_file(), evidence)

    def test_e01_completed_entries_have_exact_dispositions(self):
        expected = [
            "api-file-io-limiters",
            "bootstrap-initialize-state",
            "package-bootstrap-effect",
            "prompt-artist-mix-warning-dedupe",
            "prompt-conditioning-warning-dedupe",
            "root-route-registration",
            "runtime-services",
        ]
        completed = [
            entry["id"]
            for entry in self.e01_fixture["entries"]
            if entry["target_phase"] == "E-09-complete"
        ]
        dispositions = [
            item["id"]
            for item in self.fixture["e01_dispositions"]
        ]
        self.assertEqual(completed, expected)
        self.assertEqual(dispositions, expected)
        self.assertEqual(len(set(dispositions)), len(dispositions))

    def test_completion_audit_records_zero_ambiguous_owners(self):
        audit = self.fixture["completion_audit"]
        entries = {
            entry["id"]: entry for entry in self.e01_fixture["entries"]
        }
        dispositions = {
            item["id"]: item["decision"]
            for item in self.fixture["e01_dispositions"]
        }
        reconciliations = {
            item["e01_entry"]: item
            for item in audit["e01_reconciliation"]
        }

        self.assertEqual(audit["classification"], "Contract")
        self.assertEqual(audit["production_changes"], 0)
        self.assertEqual(audit["ambiguous_state_owners"], [])
        self.assertEqual(
            audit["base_sha"],
            "05fc20eb366be8376a6d3a47a79d2b5d00654a08",
        )
        self.assertEqual(audit["next_phase"], "E-10 task card only")
        self.assertEqual(set(reconciliations), set(dispositions))
        self.assertNotIn(
            "E-09",
            {entry["target_phase"] for entry in entries.values()},
        )
        for entry_id, reconciliation in reconciliations.items():
            with self.subTest(entry=entry_id):
                self.assertEqual(
                    entries[entry_id]["target_phase"],
                    reconciliation["completed_phase"],
                )
                self.assertEqual(
                    reconciliation["decision"],
                    dispositions[entry_id],
                )
        self.assertEqual(
            audit["verified_cleanup_order"],
            [item["id"] for item in self.fixture["cleanup_order"]],
        )
        self.assertEqual(
            set(audit["verified_noops"]),
            {item["id"] for item in self.fixture["retained_noops"]},
        )
        for surface in audit["reused_evidence"]["surfaces"]:
            self.assertTrue(surface.strip())

    def test_cleanup_order_reconciles_completed_feature_owners(self):
        expected_order = [
            "translation-route-executor",
            "aio-first-pass-cache",
            "wildcard-snapshot-cache",
            "autocomplete-index-store",
            "autocomplete-snapshot-store",
            "translation-default-facade",
            "translation-service-cache",
        ]
        cleanup = self.fixture["cleanup_order"]
        self.assertEqual([item["id"] for item in cleanup], expected_order)

        entries = {
            entry["id"]: entry for entry in self.e01_fixture["entries"]
        }
        expected_e01 = {
            "root-translation-route-worker",
            "aio-first-pass-cache",
            "wildcard-snapshot-cache",
            "autocomplete-index-locks",
            "autocomplete-dataset-cache",
            "translation-default-service",
        }
        self.assertEqual(
            {item["e01_entry"] for item in cleanup},
            expected_e01,
        )
        for item in cleanup:
            self.assertIn(item["e01_entry"], entries)
            self.assertNotEqual(entries[item["e01_entry"]]["target_phase"], "E-09")

    def test_current_lifecycle_matches_the_implemented_contract(self):
        current = self.fixture["current_state"]
        bootstrap_functions = _top_level_function_names(
            "easyuse_anima/bootstrap.py"
        )
        runtime_methods = _class_method_names(
            "easyuse_anima/runtime.py",
            "RuntimeServices",
        )
        self.assertEqual(
            "shutdown" in bootstrap_functions,
            current["bootstrap_has_shutdown"],
        )
        self.assertEqual(
            "close" in runtime_methods,
            current["runtime_services_has_close"],
        )
        self.assertEqual(
            _literal_string_sequence("easyuse_anima/bootstrap.py", "__all__"),
            current["bootstrap_exports"],
        )

        translation_factory = (
            ROOT / "easyuse_anima" / "api" / "routes" / "translation.py"
        ).read_text(encoding="utf-8")
        bootstrap_source = (
            ROOT / "easyuse_anima" / "bootstrap.py"
        ).read_text(encoding="utf-8")
        self.assertNotIn("register_shutdown", translation_factory)
        self.assertIn("atexit.register(shutdown)", bootstrap_source)
        package_source = (ROOT / "__init__.py").read_text(encoding="utf-8")
        self.assertEqual(
            current["package_entry_calls"],
            "easyuse_anima.bootstrap._initialize_package",
        )
        self.assertIn("_initialize_package()", package_source)
        self.assertFalse(current["translation_worker_registers_own_atexit"])

    def test_target_lifecycle_is_terminal_serialized_and_compatible(self):
        lifecycle = self.fixture["lifecycle_owner"]
        self.assertEqual(lifecycle["module"], "easyuse_anima/bootstrap.py")
        self.assertEqual(
            lifecycle["serialization"],
            "initialize and shutdown share _INITIALIZE_LOCK",
        )
        self.assertEqual(lifecycle["shutdown_state"], "terminal")
        self.assertEqual(
            lifecycle["initialize_after_shutdown"],
            "raise-before-callbacks",
        )
        self.assertEqual(
            lifecycle["atexit_registration"],
            "bootstrap-owned-once",
        )
        self.assertEqual(
            lifecycle["expected_identity_detach"],
            [
                "easyuse_anima.bootstrap._DEFAULT_RUNTIME",
                "easyuse_anima.runtime._RUNTIME_SERVICES",
            ],
        )
        self.assertEqual(
            self.fixture["public_surface"]["bootstrap_all_after_e09b"],
            ["initialize", "shutdown"],
        )
        self.assertEqual(
            self.fixture["public_surface"]["root_all_unchanged"],
            _literal_string_sequence("__init__.py", "__all__"),
        )
        self.assertEqual(
            self.fixture["public_surface"]["runtime_all_unchanged"],
            _literal_string_sequence("easyuse_anima/runtime.py", "__all__"),
        )
        boundary = self.fixture["implementation_boundary"]
        self.assertEqual(
            boundary["allowed_production"],
            [
                "easyuse_anima/runtime.py",
                "easyuse_anima/bootstrap.py",
                "easyuse_anima/api/routes/translation.py",
                "easyuse_anima/translation/service.py",
                "easyuse_anima/prompt/artist_mix.py",
                "__init__.py",
            ],
        )
        self.assertEqual(
            set(boundary["forbidden"]),
            {
                "active-request-drain",
                "file-io-limiter-clear-cancel-release",
                "hot-shutdown-reinitialize",
                "provider-client-close",
                "root-public-export-change",
                "route-deregistration",
                "route-side-effect-rollback",
            },
        )

    def test_initialize_retry_and_rollback_contracts_are_bounded(self):
        preserved = self.fixture["preserved_initialize"]
        self.assertEqual(
            preserved["route_false"],
            "nonterminal and retryable",
        )
        self.assertEqual(
            preserved["wildcard_oserror"],
            "warn, retain runtime, and retry wildcard initialization later",
        )
        self.assertEqual(preserved["wildcard_success"], "initialize once")

        rollback = self.fixture["rollback_contract"]
        self.assertTrue(rollback["continue_cleanup"])
        self.assertTrue(rollback["preserve_startup_exception"])
        self.assertEqual(
            rollback["triggers"],
            [
                "unexpected-register-routes-exception",
                "unexpected-wildcard-initializer-exception",
            ],
        )
        self.assertEqual(
            set(rollback["rollback_only"]),
            {
                "attempt-created-runtime-services",
                "attempt-installed-runtime-identity",
                "attempt-published-bootstrap-runtime",
                "attempt-replaced-translation-facade",
            },
        )
        self.assertEqual(
            set(rollback["non_rollback"]),
            {
                "directories",
                "global-feature-cache-owners",
                "pre-created-translation-route-executor",
                "registered-route-side-effects",
            },
        )

    def test_file_io_routes_and_provider_are_explicit_noops(self):
        retained = {
            item["id"]: item for item in self.fixture["retained_noops"]
        }
        self.assertEqual(
            set(retained),
            {
                "api-file-io-limiters",
                "prompt-conditioning-warning-dedupe",
                "root-route-registration",
                "translation-provider-registry",
            },
        )

        file_io = (
            ROOT / "easyuse_anima" / "api" / "file_io.py"
        ).read_text(encoding="utf-8")
        self.assertIn("weakref.WeakKeyDictionary", file_io)
        self.assertIn("weakref.ref(limiter)", file_io)
        self.assertIn("asyncio.Semaphore", file_io)
        self.assertIn("asyncio.to_thread", file_io)

        router = (
            ROOT / "easyuse_anima" / "api" / "router.py"
        ).read_text(encoding="utf-8")
        self.assertNotIn("deregister", router)
        self.assertNotIn("remove_route", router)
        self.assertIn("ROUTE_REGISTRATION_MARKER", router)

    def test_warning_dedupe_partition_matches_current_callers(self):
        name = "_SPECTRUM_ANIMA_MOD_GUIDANCE_OLD_SIGNATURE_WARNED"
        warning_decisions = {
            item["id"]: item for item in self.fixture["warning_dedupe"]
        }
        self.assertEqual(
            warning_decisions["prompt-artist-mix-warning-dedupe"]["action"],
            "remove",
        )
        self.assertEqual(
            warning_decisions["prompt-conditioning-warning-dedupe"]["action"],
            "retain-process-lifetime",
        )
        self.assertEqual(
            _name_reference_count("easyuse_anima/prompt/artist_mix.py", name),
            0,
        )
        self.assertGreaterEqual(
            _name_reference_count("easyuse_anima/prompt/conditioning.py", name),
            3,
        )

    def test_current_feature_cleanup_methods_support_the_plan(self):
        required = {
            ("easyuse_anima/api/routes/translation_execution.py", "PromptTranslationRouteExecutor"): "shutdown",
            ("easyuse_anima/aio/first_pass_cache.py", "_AIOFirstPassCacheStore"): "clear",
            ("easyuse_anima/wildcard/snapshot.py", "_WildcardSnapshotStore"): "clear",
            ("easyuse_anima/autocomplete/index.py", "_AutocompleteIndexStore"): "close",
            ("easyuse_anima/autocomplete/dataset.py", "_AutocompleteSnapshotStore"): "clear",
            ("easyuse_anima/translation/service.py", "PromptTranslationService"): "close",
        }
        for (module, class_name), method in required.items():
            with self.subTest(module=module, class_name=class_name):
                self.assertIn(method, _class_method_names(module, class_name))

    def test_contract_document_and_roadmap_queue_are_linked(self):
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
        for task_id in ("E-09a", "E-09b", "E-09c"):
            self.assertIn(task_id, roadmap)
        self.assertIn("E-09 is complete", roadmap)
        self.assertIn("Phase E is complete", roadmap)


if __name__ == "__main__":
    unittest.main()
