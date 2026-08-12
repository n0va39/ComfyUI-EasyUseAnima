from __future__ import annotations

import copy
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOL_PATH = ROOT / "tools" / "check_python_file_dispositions.py"
CONTRACT_PATH = (
    ROOT / "tests" / "fixtures" / "python_file_disposition_contract.v1.json"
)


def _load_checker():
    spec = importlib.util.spec_from_file_location(
        "easyuse_anima_file_disposition_checker", TOOL_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load file-disposition checker")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


checker = _load_checker()


class PythonFileDispositionContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.document = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
        linked = cls.document["linked_contracts"]
        cls.owner_document = json.loads(
            (ROOT / linked["import_owner_map"]).read_text(encoding="utf-8")
        )
        cls.size_document = json.loads(
            (ROOT / linked["size_ledger"]).read_text(encoding="utf-8")
        )
        cls.compatibility_text = (ROOT / linked["compatibility_registry"]).read_text(
            encoding="utf-8"
        )
        cls.inventory_document = json.loads(
            (ROOT / cls.document["inventory_owner"]["path"]).read_text(
                encoding="utf-8"
            )
        )

    def validate(self, document):
        return checker.validate_contract(
            document,
            owner_document=self.owner_document,
            size_document=self.size_document,
            compatibility_text=self.compatibility_text,
            repository_root=ROOT,
        )

    def test_repository_contract_passes_with_zero_unclassified_files(self):
        self.assertEqual(checker.check_repository(ROOT, CONTRACT_PATH), [])
        contract = self.validate(self.document)
        self.assertEqual(contract["expected_baseline_files"], 189)
        self.assertEqual(contract["expected_target_files"], 195)
        self.assertEqual(len(contract["entries"]), 189)
        self.assertEqual(len(contract["target_paths"]), 195)

    def test_inventory_requires_every_source_exactly_once(self):
        missing = copy.deepcopy(self.document)
        missing["entries"].pop()
        with self.assertRaises(checker.ContractError):
            self.validate(missing)

        duplicate = copy.deepcopy(self.document)
        duplicate["entries"].insert(1, copy.deepcopy(duplicate["entries"][0]))
        with self.assertRaises(checker.ContractError):
            self.validate(duplicate)

    def test_all_size_exceptions_require_exact_path_and_final_owner(self):
        mutation = copy.deepcopy(self.document)
        entry = next(
            item
            for item in mutation["entries"]
            if item["path"] == "easyuse_anima/bootstrap.py"
        )
        entry["size_exception_verdicts"].pop()
        with self.assertRaises(checker.ContractError):
            self.validate(mutation)

        mutation = copy.deepcopy(self.document)
        entry = next(
            item
            for item in mutation["entries"]
            if item["path"] == "easyuse_anima/prompt/artist_mix.py"
        )
        entry["size_exception_verdicts"][0]["final_owner"] = (
            "easyuse_anima/prompt/not-a-target.py"
        )
        with self.assertRaises(checker.ContractError):
            self.validate(mutation)

        mutation = copy.deepcopy(self.document)
        entry = next(
            item
            for item in mutation["entries"]
            if item["path"] == "easyuse_anima/aio/legacy_generation.py"
        )
        moved_exception = next(
            item
            for item in entry["size_exception_verdicts"]
            if item["id"].startswith(
                "function:easyuse_anima/aio/legacy_upscale.py::"
            )
        )
        moved_exception["final_owner"] = "easyuse_anima/aio/legacy_detailer.py"
        with self.assertRaises(checker.ContractError):
            self.validate(mutation)

    def test_ptc10_size_closure_has_no_pending_exceptions(self):
        contract = self.validate(self.document)
        verdicts = [
            (entry["status"], verdict["id"])
            for entry in contract["entries"]
            for verdict in entry["size_exception_verdicts"]
        ]
        self.assertEqual(len(self.size_document["module_exceptions"]), 6)
        self.assertEqual(len(self.size_document["function_exceptions"]), 14)
        self.assertEqual(len(verdicts), 20)
        self.assertEqual(
            [item for item in verdicts if item[0] == "planned"],
            [],
        )

    def test_compatibility_entries_reference_authoritative_registry(self):
        mutation = copy.deepcopy(self.document)
        entry = next(item for item in mutation["entries"] if item["path"] == "api.py")
        entry["compatibility_registry_key"] = "missing-root-facade.py"
        with self.assertRaises(checker.ContractError):
            self.validate(mutation)

    def test_target_owner_and_generic_bucket_fail_closed(self):
        owner_mismatch = copy.deepcopy(self.document)
        entry = next(
            item
            for item in owner_mismatch["entries"]
            if item["path"] == "easyuse_anima/nodes/naia_nodes.py"
        )
        entry["targets"][1]["owner_group"] = "prompt"
        with self.assertRaises(checker.ContractError):
            self.validate(owner_mismatch)

        generic_target = copy.deepcopy(self.document)
        entry = next(
            item
            for item in generic_target["entries"]
            if item["path"] == "easyuse_anima/prompt/advanced.py"
        )
        entry["targets"][1]["path"] = "easyuse_anima/prompt/helpers2.py"
        generic_target["inventory_owner"]["expected_target_files"] = 181
        with self.assertRaises(checker.ContractError):
            self.validate(generic_target)

    def test_planned_target_cannot_land_without_status_update(self):
        mutation = copy.deepcopy(self.document)
        entry = next(
            item
            for item in mutation["entries"]
            if item["path"] == "easyuse_anima/nodes/prompt_data_nodes.py"
        )
        entry["status"] = "planned"
        contract = self.validate(mutation)
        violations = checker.check_current_inventory(self.inventory_document, contract)
        self.assertIn(
            "planned-target-already-present",
            {violation["rule"] for violation in violations},
        )


if __name__ == "__main__":
    unittest.main()
