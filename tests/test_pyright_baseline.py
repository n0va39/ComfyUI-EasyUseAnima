from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHECKER_PATH = ROOT / "tools" / "check_pyright_baseline.py"
BASELINE_PATH = ROOT / "tests" / "fixtures" / "pyright_baseline.json"
CONFIG_PATH = ROOT / "pyrightconfig.json"


def _load_checker():
    spec = importlib.util.spec_from_file_location(
        "easyuse_anima_pyright_baseline_checker",
        CHECKER_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load checker: {CHECKER_PATH.name}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


checker = _load_checker()


def _baseline() -> dict:
    return json.loads(BASELINE_PATH.read_text(encoding="utf-8"))


def _config() -> dict:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def _report_from_baseline(baseline: dict, *, version: str | None = None) -> dict:
    diagnostics = []
    for entry in baseline["diagnostics"]:
        for _ in range(entry["count"]):
            diagnostics.append(
                {
                    "file": str(ROOT / entry["path"]),
                    "severity": entry["severity"],
                    "rule": entry["rule"],
                    "message": "baseline diagnostic",
                    "range": {
                        "start": {"line": 0, "character": 0},
                        "end": {"line": 0, "character": 1},
                    },
                }
            )
    return {
        "version": version or baseline["tool"]["version"],
        "generalDiagnostics": diagnostics,
        "summary": {
            "filesAnalyzed": 41,
            "errorCount": sum(
                item["severity"] == "error" for item in diagnostics
            ),
            "warningCount": sum(
                item["severity"] == "warning" for item in diagnostics
            ),
            "informationCount": sum(
                item["severity"] == "information" for item in diagnostics
            ),
            "timeInSec": 0.1,
        },
    }


class PyrightBaselineTests(unittest.TestCase):
    def test_checked_in_fixture_is_internally_consistent(self):
        baseline = _baseline()
        report = _report_from_baseline(baseline)

        summary, failures = checker.compare_report(report, baseline, _config(), ROOT)

        self.assertEqual(failures, [])
        self.assertEqual(summary["totals"], baseline["totals"])
        self.assertEqual(sum(baseline["totals"].values()), 60)

    def test_decreased_diagnostic_group_passes_without_rewriting_baseline(self):
        baseline = _baseline()
        report = _report_from_baseline(baseline)
        report["generalDiagnostics"].pop()
        report["summary"]["errorCount"] -= 1

        _summary, failures = checker.compare_report(report, baseline, _config(), ROOT)

        self.assertEqual(failures, [])

    def test_increased_existing_group_and_new_group_fail(self):
        baseline = _baseline()
        report = _report_from_baseline(baseline)
        report["generalDiagnostics"].extend(
            [
                dict(report["generalDiagnostics"][0]),
                {
                    "file": str(ROOT / "easyuse_anima" / "new_module.py"),
                    "severity": "error",
                    "rule": "reportAssignmentType",
                    "message": "new diagnostic",
                    "range": {
                        "start": {"line": 0, "character": 0},
                        "end": {"line": 0, "character": 1},
                    },
                },
            ]
        )
        report["summary"]["errorCount"] += 2

        _summary, failures = checker.compare_report(report, baseline, _config(), ROOT)

        self.assertTrue(any("allowed 1, got 2" in failure for failure in failures))
        self.assertTrue(any("new_module.py" in failure for failure in failures))
        self.assertTrue(any("total error diagnostics" in failure for failure in failures))

    def test_version_change_fails_even_when_diagnostics_match(self):
        baseline = _baseline()
        report = _report_from_baseline(baseline, version="9.9.9")

        _summary, failures = checker.compare_report(report, baseline, _config(), ROOT)

        self.assertEqual(len(failures), 1)
        self.assertIn("Pyright version changed", failures[0])

    def test_summary_must_match_diagnostic_severities(self):
        baseline = _baseline()
        report = _report_from_baseline(baseline)
        report["summary"]["errorCount"] -= 1

        with self.assertRaisesRegex(ValueError, "summary totals do not match"):
            checker.summarize_report(report, ROOT)

    def test_baseline_rejects_path_escape_and_zero_count(self):
        baseline = _baseline()
        report = _report_from_baseline(baseline)
        baseline["diagnostics"][0]["path"] = "../outside.py"

        with self.assertRaisesRegex(ValueError, "canonical repository-relative POSIX"):
            checker.compare_report(report, baseline, _config(), ROOT)

        baseline = _baseline()
        baseline["diagnostics"][0]["count"] = 0
        with self.assertRaisesRegex(ValueError, "count must be positive"):
            checker.compare_report(report, baseline, _config(), ROOT)

    def test_weakened_or_unreviewed_config_fails(self):
        baseline = _baseline()
        report = _report_from_baseline(baseline)
        config = _config()
        config["typeCheckingMode"] = "off"
        config["ignore"] = ["easyuse_anima"]

        _summary, failures = checker.compare_report(report, baseline, config, ROOT)

        self.assertTrue(any("config fields changed" in failure for failure in failures))
        self.assertTrue(any("typeCheckingMode changed" in failure for failure in failures))


if __name__ == "__main__":
    unittest.main()
