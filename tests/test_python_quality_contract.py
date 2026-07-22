from pathlib import Path
import tomllib
import unittest


ROOT = Path(__file__).resolve().parents[1]


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

    def test_project_runner_calls_g01_before_profile_specific_full_tests(self):
        source = (
            ROOT / "tools" / "check_project.ps1"
        ).read_text(encoding="utf-8")

        quality_call = (
            '& (Join-Path $PSScriptRoot "check_python_quality.ps1") '
            "-RuffVersion $RuffVersion"
        )
        self.assertIn('[string]$RuffVersion = "0.15.22"', source)
        self.assertIn(quality_call, source)
        self.assertLess(
            source.index(quality_call),
            source.index('if ($Profile -eq "full")'),
        )


if __name__ == "__main__":
    unittest.main()
