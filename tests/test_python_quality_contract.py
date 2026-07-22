import json
import unittest
from pathlib import Path

import tomllib

ROOT = Path(__file__).resolve().parents[1]
PYRIGHT_BASELINE_PATH = ROOT / "tests" / "fixtures" / "pyright_baseline.json"


class PythonQualityContractTests(unittest.TestCase):
    def test_ruff_version_and_initial_rules_are_pinned(self):
        pyproject = tomllib.loads(
            (ROOT / "pyproject.toml").read_text(encoding="utf-8")
        )

        ruff = pyproject["tool"]["ruff"]
        self.assertEqual(ruff["target-version"], "py310")
        self.assertEqual(
            set(ruff["extend-exclude"]),
            {".github", "tests", "tools"},
        )
        self.assertEqual(
            ruff["lint"]["select"],
            ["E4", "E7", "E9", "F", "I", "UP"],
        )

    def test_pyright_basic_canonical_package_contract_is_pinned(self):
        pyright = json.loads(
            (ROOT / "pyrightconfig.json").read_text(encoding="utf-8")
        )

        self.assertEqual(pyright["include"], ["easyuse_anima"])
        self.assertEqual(pyright["pythonVersion"], "3.10")
        self.assertEqual(pyright["pythonPlatform"], "All")
        self.assertEqual(pyright["typeCheckingMode"], "basic")
        self.assertEqual(pyright["reportMissingModuleSource"], "none")
        self.assertNotIn("exclude", pyright)
        self.assertNotIn("ignore", pyright)
        self.assertNotIn("reportMissingImports", pyright)

        baseline = json.loads(PYRIGHT_BASELINE_PATH.read_text(encoding="utf-8"))
        self.assertEqual(baseline["tool"], {"name": "pyright", "version": "1.1.411"})
        self.assertEqual(
            baseline["config"],
            {
                "include": pyright["include"],
                "python_platform": pyright["pythonPlatform"],
                "python_version": pyright["pythonVersion"],
                "report_missing_module_source": pyright["reportMissingModuleSource"],
                "type_checking_mode": pyright["typeCheckingMode"],
            },
        )

    def test_dedicated_runner_reports_findings_without_enabling_fixes(self):
        source = (
            ROOT / "tools" / "check_python_quality.ps1"
        ).read_text(encoding="utf-8")

        self.assertIn('[string]$RuffVersion = "0.15.22"', source)
        self.assertIn('"ruff@$RuffVersion"', source)
        self.assertIn('"--exit-zero"', source)
        self.assertIn('"--no-cache"', source)
        self.assertIn('"--output-format"', source)
        self.assertNotIn('"--fix"', source)
        self.assertNotIn('"format"', source)

    def test_dedicated_runner_keeps_execution_failures_blocking(self):
        source = (
            ROOT / "tools" / "check_python_quality.ps1"
        ).read_text(encoding="utf-8")

        self.assertIn("$ruffExitCode = $LASTEXITCODE", source)
        self.assertIn("if ($ruffExitCode -ne 0)", source)
        self.assertIn("Ruff report execution failed", source)

    def test_dedicated_runner_pins_pyright_and_ratchets_json_report(self):
        source = (
            ROOT / "tools" / "check_python_quality.ps1"
        ).read_text(encoding="utf-8")

        self.assertIn('[string]$PyrightVersion = "1.1.411"', source)
        self.assertIn('"pyright@$PyrightVersion"', source)
        self.assertIn('"--prefer-offline"', source)
        self.assertIn('if ($Offline) { "--offline" }', source)
        self.assertIn('"--outputjson"', source)
        self.assertIn('"pyrightconfig.json"', source)
        self.assertIn('"check_pyright_baseline.py"', source)
        self.assertIn("if ($pyrightExitCode -notin @(0, 1))", source)
        self.assertIn("Pyright execution failed", source)
        self.assertIn("Pyright baseline ratchet failed", source)

    def test_project_runner_calls_g01_before_profile_specific_full_tests(self):
        source = (
            ROOT / "tools" / "check_project.ps1"
        ).read_text(encoding="utf-8")

        quality_call = '& (Join-Path $PSScriptRoot "check_python_quality.ps1")'
        self.assertIn('[string]$RuffVersion = "0.15.22"', source)
        self.assertIn('[string]$PyrightVersion = "1.1.411"', source)
        self.assertIn(quality_call, source)
        self.assertIn("-RuffVersion $RuffVersion", source)
        self.assertIn("-PyrightVersion $PyrightVersion", source)
        self.assertIn("-Python $pythonCommand", source)
        self.assertIn("-Offline:$OfflineMaintenanceTools", source)
        self.assertLess(
            source.index(quality_call),
            source.index('if ($Profile -eq "full")'),
        )


if __name__ == "__main__":
    unittest.main()
