from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class ValidationContractTests(unittest.TestCase):
    def test_project_check_owns_the_unittest_and_frontend_contract(self):
        source = (ROOT / "tools" / "check_project.ps1").read_text(encoding="utf-8")

        self.assertIn("-m unittest discover -s tests", source)
        self.assertIn('Join-Path $PSScriptRoot "check_frontend.ps1"', source)
        self.assertIn("-m compileall -q .", source)
        self.assertIn("git diff --check", source)
        self.assertIn("git diff --cached --check", source)
        self.assertNotIn("-m pytest", source)

    def test_maintainer_guide_uses_the_checked_in_project_check(self):
        source = (ROOT / "MAINTAINING.md").read_text(encoding="utf-8")

        self.assertIn("tools\\check_project.ps1 -Profile full", source)
        self.assertIn("unittest", source)
        self.assertIn("pytest", source)
        self.assertNotIn("tools\\check_custom_node.ps1", source)

    def test_frontend_roadmap_records_the_runner_decision(self):
        source = (
            ROOT / "docs" / "development" / "frontend-maintenance-roadmap.md"
        ).read_text(encoding="utf-8")

        self.assertIn("공식 Python full suite는 `unittest discover`", source)
        self.assertIn("`pytest`는 공식 runner로 지원하지 않는다", source)

    def test_contributor_guides_use_discovery_for_focused_workflow_tests(self):
        for name in ("CONTRIBUTING.md", "CONTRIBUTING.ko.md"):
            with self.subTest(name=name):
                source = (ROOT / name).read_text(encoding="utf-8")
                self.assertIn(
                    "python -m unittest discover -s tests -p test_workflows.py",
                    source,
                )
                self.assertNotIn("python -m unittest tests.test_workflows", source)


if __name__ == "__main__":
    unittest.main()
