from __future__ import annotations

import copy
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOL_PATH = ROOT / "tools" / "check_python_support_ownership.py"
CONTRACT_PATH = (
    ROOT / "tests" / "fixtures" / "python_support_ownership_contract.v1.json"
)
OWNER_PATH = ROOT / "tests" / "fixtures" / "python_test_ownership_contract.v1.json"


def _load_checker():
    spec = importlib.util.spec_from_file_location(
        "easyuse_anima_support_ownership_checker", TOOL_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load support-ownership checker")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


checker = _load_checker()


class PythonSupportOwnershipContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.document = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
        cls.owner_document = json.loads(OWNER_PATH.read_text(encoding="utf-8"))

    def validate(self, document):
        return checker.validate_contract(
            document,
            owner_document=self.owner_document,
            repository_root=ROOT,
        )

    def test_repository_contract_has_zero_unclassified_or_orphan_artifacts(self):
        self.assertEqual(checker.check_repository(ROOT, CONTRACT_PATH), [])
        contract = self.validate(self.document)
        self.assertEqual(contract["expected_files"], len(contract["entries"]))
        self.assertEqual(
            set(contract["owner_groups"]),
            {
                group
                for entry in contract["entries"]
                for group in entry["production_groups"]
                if group != checker.SPECIAL_GROUP
            },
        )

    def test_exact_inventory_rejects_missing_duplicate_and_unknown_artifacts(self):
        missing = copy.deepcopy(self.document)
        missing["entries"].pop()
        missing["inventory"]["expected_files"] -= 1
        contract = self.validate(missing)
        violations = checker.check_current_inventory(
            checker.discover_support_paths(ROOT, self.owner_document), contract
        )
        self.assertIn(
            "unclassified-support-artifact",
            {violation["rule"] for violation in violations},
        )

        duplicate = copy.deepcopy(self.document)
        duplicate["entries"].insert(1, copy.deepcopy(duplicate["entries"][0]))
        duplicate["inventory"]["expected_files"] += 1
        with self.assertRaises(checker.ContractError):
            self.validate(duplicate)

        actual = set(checker.discover_support_paths(ROOT, self.owner_document))
        expected = {entry["path"] for entry in self.document["entries"]}
        self.assertEqual(actual, expected)
        violations = checker.check_current_inventory(
            sorted(actual | {"tests/not-classified.py"}), self.validate(self.document)
        )
        self.assertIn(
            "unclassified-support-artifact",
            {violation["rule"] for violation in violations},
        )

    def test_owner_group_mode_and_generated_fields_fail_closed(self):
        orphan = copy.deepcopy(self.document)
        orphan["entries"][0]["owner"] = "tests/not-an-owner.py"
        with self.assertRaises(checker.ContractError):
            self.validate(orphan)

        fixture_owner = copy.deepcopy(self.document)
        fixture_entries = [
            entry
            for entry in fixture_owner["entries"]
            if entry["kind"] in {"generated_baseline", "test_fixture"}
        ]
        fixture_entries[0]["owner"] = fixture_entries[1]["path"]
        with self.assertRaises(checker.ContractError):
            self.validate(fixture_owner)

        invalid_group = copy.deepcopy(self.document)
        invalid_group["entries"][0]["production_groups"] = ["not-a-group"]
        with self.assertRaises(checker.ContractError):
            self.validate(invalid_group)

        invalid_mode = copy.deepcopy(self.document)
        test_entry = next(
            entry for entry in invalid_mode["entries"] if entry["kind"] == "test"
        )
        test_entry["execution_mode"] = "fixture-input"
        with self.assertRaises(checker.ContractError):
            self.validate(invalid_mode)

        invalid_generated = copy.deepcopy(self.document)
        baseline = next(
            entry
            for entry in invalid_generated["entries"]
            if entry["kind"] == "generated_baseline"
        )
        baseline["generated"] = False
        with self.assertRaises(checker.ContractError):
            self.validate(invalid_generated)

    def test_manual_live_scope_reuses_g06_and_runner_registers_gate(self):
        contract = self.validate(self.document)
        manual_paths = {
            entry["path"]
            for entry in contract["entries"]
            if entry["kind"] == "manual_live_matrix"
        }
        expected = {
            matrix["owner"]
            for matrix in self.owner_document["matrices"]
            if matrix["mode"] == "manual-on-trigger"
        }
        self.assertEqual(manual_paths, expected)

        runner = (ROOT / "tools" / "check_python_quality.ps1").read_text(
            encoding="utf-8-sig"
        )
        invocation = '(Join-Path $PSScriptRoot "check_python_support_ownership.py")'
        self.assertEqual(runner.count(invocation), 1)


if __name__ == "__main__":
    unittest.main()
