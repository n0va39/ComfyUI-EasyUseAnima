from __future__ import annotations

import copy
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHECKER_PATH = ROOT / "tools" / "check_python_size_complexity.py"
CONTRACT_PATH = (
    ROOT / "tests" / "fixtures" / "python_size_complexity_contract.v1.json"
)


def load_checker():
    spec = importlib.util.spec_from_file_location(
        "easyuse_anima_python_size_complexity_checker",
        CHECKER_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load checker: {CHECKER_PATH.name}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


checker = load_checker()


def contract_document(*, modules=(), functions=()):
    return {
        "schema_version": 1,
        "thresholds": {
            "module_lines": 800,
            "adapter_module_lines": 400,
            "function_lines": 120,
        },
        "adapter_paths": {
            "exact": [
                "__init__.py",
                "easyuse_anima/bootstrap.py",
                "easyuse_anima/registration.py",
            ],
            "prefixes": [
                "easyuse_anima/api/",
                "easyuse_anima/infrastructure/",
                "easyuse_anima/nodes/",
            ],
        },
        "module_exceptions": list(modules),
        "function_exceptions": list(functions),
    }


def exception(path, baseline_loc, *, qualified_name=None):
    record = {
        "path": path,
        "baseline_loc": baseline_loc,
        "owner_issue": 188,
        "decomposition_boundary": (
            "split only at the named adapter or service ownership boundary"
        ),
    }
    if qualified_name is not None:
        record["qualified_name"] = qualified_name
    return record


def function_source(loc):
    return "def oversized():\n" + "    pass\n" * (loc - 1)


class PythonSizeComplexityContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.document = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
        cls.contract = checker.validate_contract(cls.document)

    def test_current_repository_has_zero_size_growth_violations(self):
        self.assertEqual(checker.check_repository(ROOT, CONTRACT_PATH), [])

    def test_checked_in_ledger_exactly_freezes_current_overages(self):
        report = checker.analyzer.analyze_repository(ROOT)
        exact_paths = self.contract["adapter_paths"]["exact"]
        prefixes = tuple(self.contract["adapter_paths"]["prefixes"])
        current_modules = {}
        current_functions = {}
        for module in report["inventory"]["modules"]:
            path = module["path"]
            module_threshold = (
                400 if path in exact_paths or path.startswith(prefixes) else 800
            )
            if module["loc"] > module_threshold:
                current_modules[path] = module["loc"]
            for function in module["functions"]:
                if function["loc"] > 120:
                    current_functions[(path, function["qualified_name"])] = function[
                        "loc"
                    ]

        ledger_modules = {
            record["path"]: record["baseline_loc"]
            for record in self.contract["module_exceptions"]
        }
        ledger_functions = {
            (record["path"], record["qualified_name"]): record["baseline_loc"]
            for record in self.contract["function_exceptions"]
        }
        self.assertEqual(ledger_modules, current_modules)
        self.assertEqual(ledger_functions, current_functions)

    def test_new_adapter_module_general_module_and_function_overages_fail(self):
        report = checker.analyzer.analyze_source_set(
            {
                "__init__.py": "VALUE = 1\n",
                "easyuse_anima/bootstrap.py": "# adapter\n" * 401,
                "easyuse_anima/service.py": "# service\n" * 801,
                "easyuse_anima/small.py": function_source(121),
            }
        )

        violations = checker.check_report(
            report,
            checker.validate_contract(contract_document()),
        )

        self.assertEqual(
            {violation["rule"] for violation in violations},
            {
                "unreviewed-function-overage",
                "unreviewed-module-overage",
            },
        )
        self.assertEqual(
            {(item["path"], item["symbol"]) for item in violations},
            {
                ("easyuse_anima/bootstrap.py", "<module>"),
                ("easyuse_anima/service.py", "<module>"),
                ("easyuse_anima/small.py", "oversized"),
            },
        )

    def test_reviewed_baseline_decrease_passes_but_growth_fails(self):
        document = contract_document(
            functions=[
                exception(
                    "easyuse_anima/service.py",
                    125,
                    qualified_name="oversized",
                )
            ]
        )
        contract = checker.validate_contract(document)
        decreased = checker.analyzer.analyze_source_set(
            {
                "__init__.py": "VALUE = 1\n",
                "easyuse_anima/service.py": function_source(124),
            }
        )
        grown = checker.analyzer.analyze_source_set(
            {
                "__init__.py": "VALUE = 1\n",
                "easyuse_anima/service.py": function_source(126),
            }
        )

        self.assertEqual(checker.check_report(decreased, contract), [])
        self.assertEqual(
            checker.check_report(grown, contract),
            [
                {
                    "rule": "function-overage-growth",
                    "path": "easyuse_anima/service.py",
                    "symbol": "oversized",
                    "current_loc": 126,
                    "baseline_loc": 125,
                }
            ],
        )

    def test_reviewed_module_baseline_decrease_passes_but_growth_fails(self):
        document = contract_document(
            modules=[exception("easyuse_anima/service.py", 805)]
        )
        contract = checker.validate_contract(document)
        decreased = checker.analyzer.analyze_source_set(
            {
                "__init__.py": "VALUE = 1\n",
                "easyuse_anima/service.py": "# service\n" * 804,
            }
        )
        grown = checker.analyzer.analyze_source_set(
            {
                "__init__.py": "VALUE = 1\n",
                "easyuse_anima/service.py": "# service\n" * 806,
            }
        )

        self.assertEqual(checker.check_report(decreased, contract), [])
        self.assertEqual(
            checker.check_report(grown, contract),
            [
                {
                    "rule": "module-overage-growth",
                    "path": "easyuse_anima/service.py",
                    "symbol": "<module>",
                    "current_loc": 806,
                    "baseline_loc": 805,
                }
            ],
        )

    def test_path_or_function_rename_requires_same_pr_ledger_update(self):
        document = contract_document(
            modules=[exception("easyuse_anima/old.py", 801)],
            functions=[
                exception(
                    "easyuse_anima/old.py",
                    121,
                    qualified_name="old_function",
                )
            ],
        )
        report = checker.analyzer.analyze_source_set(
            {
                "__init__.py": "VALUE = 1\n",
                "easyuse_anima/new.py": function_source(121),
            }
        )

        violations = checker.check_report(
            report,
            checker.validate_contract(document),
        )

        self.assertEqual(
            {violation["rule"] for violation in violations},
            {
                "stale-function-exception",
                "stale-module-exception",
                "unreviewed-function-overage",
            },
        )

    def test_contract_rejects_weaker_thresholds_unsorted_and_ownerless_exceptions(self):
        mutations = []

        weaker_threshold = contract_document()
        weaker_threshold["thresholds"]["function_lines"] = 121
        mutations.append(weaker_threshold)

        unsorted_paths = contract_document()
        unsorted_paths["adapter_paths"]["exact"].reverse()
        mutations.append(unsorted_paths)

        missing_adapter = contract_document()
        missing_adapter["adapter_paths"]["exact"].remove("__init__.py")
        mutations.append(missing_adapter)

        ownerless = contract_document(
            functions=[
                exception(
                    "easyuse_anima/service.py",
                    121,
                    qualified_name="oversized",
                )
            ]
        )
        ownerless["function_exceptions"][0]["owner_issue"] = 0
        mutations.append(ownerless)

        vague_boundary = copy.deepcopy(ownerless)
        vague_boundary["function_exceptions"][0]["owner_issue"] = 188
        vague_boundary["function_exceptions"][0]["decomposition_boundary"] = "later"
        mutations.append(vague_boundary)

        for mutation in mutations:
            with self.subTest(mutation=mutation):
                with self.assertRaises(checker.ContractError):
                    checker.validate_contract(mutation)


if __name__ == "__main__":
    unittest.main()
