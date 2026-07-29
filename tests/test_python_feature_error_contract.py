from __future__ import annotations

import ast
import builtins
import importlib
import json
import unittest
from functools import cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PATH = (
    ROOT / "tests" / "fixtures" / "python_feature_error_contract.v1.json"
)
CONTRACT_DOC = (
    ROOT
    / "docs"
    / "architecture"
    / "python-feature-error-taxonomy-contract.md"
)


@cache
def _tree(source: str) -> ast.Module:
    path = ROOT / source
    return ast.parse(
        path.read_text(encoding="utf-8-sig"),
        filename=str(path),
    )


def _class_def(source: str, name: str) -> ast.ClassDef:
    for statement in _tree(source).body:
        if isinstance(statement, ast.ClassDef) and statement.name == name:
            return statement
    raise AssertionError(f"{source} has no class {name}")


def _base_name(node: ast.expr) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return f"{_base_name(node.value)}.{node.attr}"
    raise AssertionError(f"Unsupported class base: {ast.dump(node)}")


def _test_owner(target: str) -> tuple[str, str]:
    module, _, class_name = target.rpartition(".")
    if not module.startswith("tests.") or not class_name:
        raise AssertionError(f"Invalid test owner: {target}")
    return f"{module.replace('.', '/')}.py", class_name


class PythonFeatureErrorContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

    def test_schema_scope_and_evidence_are_complete(self):
        self.assertEqual(
            set(self.fixture),
            {
                "base_sha",
                "canonical_taxonomy",
                "classification",
                "completion_audit",
                "current_authority",
                "direct_test_owners",
                "evidence",
                "excluded_errors",
                "feature_errors",
                "http_mappings",
                "implementation_sequence",
                "inventory_modules",
                "preserved_invariants",
                "production_changes",
                "schema_version",
                "stop_conditions",
            },
        )
        self.assertEqual(self.fixture["schema_version"], 1)
        self.assertEqual(self.fixture["classification"], "Contract")
        self.assertEqual(self.fixture["production_changes"], 11)
        self.assertEqual(
            self.fixture["base_sha"],
            "878a86f739a37a000a56b9e76ee2179aa86271f1",
        )
        self.assertTrue(CONTRACT_DOC.is_file())
        for source in self.fixture["evidence"]:
            self.assertTrue((ROOT / source).is_file(), source)

    def test_completion_audit_records_zero_unmapped_feature_errors(self):
        audit = self.fixture["completion_audit"]
        self.assertEqual(
            audit["audited_base_sha"],
            "d618bb705f9ec28f89fdbce8ba80a94847932c92",
        )
        self.assertEqual(
            audit["canonical_category_count"],
            len(self.fixture["canonical_taxonomy"]["categories"]),
        )
        self.assertEqual(
            audit["feature_error_count"],
            len(self.fixture["feature_errors"]),
        )
        self.assertEqual(
            audit["excluded_adapter_or_private_error_count"],
            len(self.fixture["excluded_errors"]),
        )
        self.assertEqual(
            audit["http_mapping_count"],
            len(self.fixture["http_mappings"]),
        )
        self.assertEqual(
            audit["inventory_module_count"],
            len(self.fixture["inventory_modules"]),
        )

        discovered = set()
        for source in self.fixture["inventory_modules"]:
            for statement in _tree(source).body:
                if isinstance(statement, ast.ClassDef) and (
                    statement.name.endswith(("Error", "Unavailable", "NotFound"))
                    or statement.name.startswith("_Invalid")
                ):
                    discovered.add((source, statement.name))
        classified = {
            (item["source"], item["name"])
            for key in ("feature_errors", "excluded_errors")
            for item in self.fixture[key]
        }
        self.assertEqual(
            audit["unmapped_feature_errors"],
            sorted(f"{source}:{name}" for source, name in discovered - classified),
        )
        self.assertEqual(audit["phase_f_status"], "complete")
        self.assertEqual(audit["next_task"], "G-04A")

    def test_canonical_taxonomy_matches_the_documented_hierarchy(self):
        taxonomy = self.fixture["canonical_taxonomy"]
        categories = taxonomy["categories"]
        self.assertEqual(taxonomy["module"], "easyuse_anima/errors.py")
        self.assertEqual(taxonomy["root_exports"], [])
        self.assertEqual(
            [item["name"] for item in categories],
            [
                "EasyUseAnimaError",
                "ValidationError",
                "ConflictError",
                "NotFoundError",
                "CapabilityUnavailableError",
                "UpstreamTimeoutError",
                "StorageError",
            ],
        )
        self.assertEqual(
            taxonomy["module_exports"],
            [item["name"] for item in categories],
        )
        taxonomy_module = importlib.import_module("easyuse_anima.errors")
        self.assertEqual(
            list(taxonomy_module.__all__),
            taxonomy["module_exports"],
        )
        self.assertEqual(categories[0]["parent"], "Exception")
        self.assertEqual(
            {item["parent"] for item in categories[1:]},
            {"EasyUseAnimaError"},
        )

    def test_inventory_covers_every_current_feature_and_adapter_error(self):
        discovered = set()
        for source in self.fixture["inventory_modules"]:
            for statement in _tree(source).body:
                if isinstance(statement, ast.ClassDef) and (
                    statement.name.endswith(("Error", "Unavailable", "NotFound"))
                    or statement.name.startswith("_Invalid")
                ):
                    discovered.add((source, statement.name))

        contracted = {
            (item["source"], item["name"])
            for item in self.fixture["feature_errors"]
        }
        excluded = {
            (item["source"], item["name"])
            for item in self.fixture["excluded_errors"]
        }
        self.assertEqual(discovered, contracted | excluded)
        self.assertFalse(contracted & excluded)

    def test_current_bases_and_builtin_catches_are_preserved_inputs(self):
        category_names = {
            item["name"]
            for item in self.fixture["canonical_taxonomy"]["categories"]
        }
        taxonomy_module = importlib.import_module("easyuse_anima.errors")
        for item in self.fixture["feature_errors"]:
            with self.subTest(error=item["name"]):
                class_def = _class_def(item["source"], item["name"])
                self.assertEqual(
                    [_base_name(base) for base in class_def.bases],
                    item["current_direct_bases"],
                )
                error_type = getattr(
                    importlib.import_module(item["module"]),
                    item["name"],
                )
                for builtin_name in item["builtin_compatibility"]:
                    builtin_type = getattr(builtins, builtin_name)
                    self.assertTrue(
                        issubclass(error_type, builtin_type),
                        f"{item['name']} no longer catches as {builtin_name}",
                    )
                self.assertIn(item["target_category"], category_names)
                self.assertTrue(
                    issubclass(
                        error_type,
                        getattr(taxonomy_module, item["target_category"]),
                    ),
                    f"{item['name']} lacks {item['target_category']}",
                )

    def test_http_mapping_is_exhaustive_and_current_payloads_are_frozen(self):
        http_errors = {
            item["name"]
            for item in self.fixture["feature_errors"]
            if item["adapter"] == "http"
        }
        mappings = {
            item["name"]: item for item in self.fixture["http_mappings"]
        }
        self.assertEqual(set(mappings), http_errors)

        feature_errors = {
            item["name"]: item for item in self.fixture["feature_errors"]
        }
        for name, mapping in mappings.items():
            with self.subTest(error=name):
                self.assertEqual(mapping["target_authority"], "api-adapter")
                self.assertTrue(mapping["owner"].startswith("easyuse_anima.api."))
                if mapping["mapping_policy"] == "dynamic-compatibility":
                    self.assertEqual(
                        mapping["adapter_inputs"],
                        ["status", "code", "message", "details"],
                    )
                elif name.startswith("Profile"):
                    self.assertEqual(mapping["adapter_inputs"], ["details"])
                elif name == "InvalidProfileDataError":
                    self.assertEqual(mapping["adapter_inputs"], [])
                else:
                    self.assertEqual(mapping["adapter_inputs"], ["message-text"])
                if mapping["current_metadata_owner"] == "api-adapter":
                    continue
                error = feature_errors[name]
                error_type = getattr(
                    importlib.import_module(error["module"]),
                    name,
                )
                constructor = mapping.get("constructor", {})
                instance = error_type(
                    *constructor.get("args", []),
                    **constructor.get("kwargs", {}),
                )
                self.assertEqual(instance.status, mapping["status"])
                self.assertEqual(instance.code, mapping["code"])
                self.assertEqual(instance.message, mapping["default_message"])
                self.assertEqual(
                    getattr(instance, "details", None),
                    mapping["details"],
                )

    def test_api_authority_and_named_compatibility_inputs_are_current(self):
        authority = self.fixture["current_authority"]
        self.assertEqual(
            (ROOT / self.fixture["canonical_taxonomy"]["module"]).is_file(),
            authority["canonical_module_exists"],
        )
        self.assertEqual(
            authority["policy_fields"],
            ["status", "code", "default_message"],
        )
        self.assertEqual(
            authority["static_resolution"],
            "ordered-specific-isinstance-exact-base-then-dynamic-derived-base",
        )
        self.assertEqual(
            authority["profile_dynamic_compatibility"],
            {
                "adapter_inputs": ["status", "code", "message", "details"],
                "scope": "generic-or-injected-ProfileMutationError",
            },
        )
        self.assertEqual(
            authority["translation_dynamic_compatibility"],
            {
                "adapter_inputs": ["status", "code", "message"],
                "scope": "unregistered-or-root-derived-PromptTranslationError",
            },
        )
        for prefix in ("profile", "translation"):
            source = (ROOT / authority[f"{prefix}_mapper_source"]).read_text(
                encoding="utf-8"
            )
            for expression in authority[f"{prefix}_mapper_required_reads"]:
                self.assertIn(expression, source)
            for expression in authority[f"{prefix}_mapper_forbidden_reads"]:
                self.assertNotIn(expression, source)

    def test_direct_test_owners_and_ordered_implementation_exist(self):
        for target in self.fixture["direct_test_owners"]:
            with self.subTest(target=target):
                source, class_name = _test_owner(target)
                _class_def(source, class_name)

        sequence = self.fixture["implementation_sequence"]
        self.assertEqual(
            [item["id"] for item in sequence],
            ["F-02f", "F-02g", "F-02h"],
        )
        self.assertEqual(
            [item["classification"] for item in sequence],
            ["CONTRACT", "ADAPTER", "CONTRACT"],
        )
        for item in sequence:
            self.assertTrue(item["scope"].strip())

    def test_contract_forbids_silent_compatibility_loss(self):
        self.assertEqual(
            set(self.fixture["stop_conditions"]),
            {
                "public-or-root-export-change",
                "concrete-exception-identity-change",
                "built-in-catch-compatibility-change",
                "api-payload-or-correlation-change",
                "profile-dynamic-seam-change",
                "feature-behavior-or-migration-change",
                "root-shim-import-from-canonical-code",
            },
        )
        self.assertIn(
            "profile-and-translation-status-code-message-details-payloads",
            self.fixture["preserved_invariants"],
        )
        self.assertIn(
            "profile-dynamic-compatibility-adapter-inputs",
            self.fixture["preserved_invariants"],
        )
        self.assertIn(
            "translation-derived-dynamic-compatibility-adapter-inputs",
            self.fixture["preserved_invariants"],
        )


if __name__ == "__main__":
    unittest.main()
