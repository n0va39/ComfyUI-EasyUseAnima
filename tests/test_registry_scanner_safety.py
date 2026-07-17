from __future__ import annotations

import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AUTOCOMPLETE_RUNTIME_PATHS = {
    "web/js/easyuse_anima_autocomplete.js",
    "web/js/autocomplete/data_adapter.js",
    "web/js/autocomplete/input_controller.js",
    "web/js/autocomplete/popup_geometry.js",
    "web/js/autocomplete/text_model.js",
}


class RegistryScannerSafetyTests(unittest.TestCase):
    def test_runtime_python_avoids_high_risk_scanner_patterns(self):
        patterns = (
            "importlib.import_module",
            "__import__(",
            "eval(",
            "exec(",
            "os.system",
            "subprocess",
            "pickle.loads",
            "marshal.loads",
            "base64.b64decode",
            "GOOGLE_TRANSLATION_API_KEY",
            "os.environ",
        )
        for filename in ("__init__.py", "api.py", "nodes.py", "prompt_translation.py", "settings.py"):
            source = (ROOT / filename).read_text(encoding="utf-8")
            for pattern in patterns:
                with self.subTest(filename=filename, pattern=pattern):
                    self.assertNotIn(pattern, source)

    def test_naia_is_only_documented_runtime_post_call(self):
        runtime_files = ("api.py", "nodes.py", "prompt_translation.py", "settings.py")
        matches = []
        for filename in runtime_files:
            source = (ROOT / filename).read_text(encoding="utf-8")
            if "requests.post" in source:
                matches.append(filename)

        self.assertEqual(matches, ["nodes.py"])
        source = (ROOT / "nodes.py").read_text(encoding="utf-8")
        self.assertIn("allow_remote_api=True", source)
        self.assertIn("localhost-only", source)
        self.assertIn("timeout=HTTP_TIMEOUT", source)

    def test_comfyignore_excludes_development_scanner_surface(self):
        ignore = (ROOT / ".comfyignore").read_text(encoding="utf-8")
        for entry in (
            ".github/",
            "docs/",
            "tests/",
            "example_workflows/",
            "examples/",
            "samples/",
            "CONTRIBUTING.md",
            "MAINTAINING.md",
            "RELEASE.md",
            "jsconfig.json",
            ".gitignore",
            ".gitattributes",
            ".gitmodules",
            ".tracking",
            "install.bat",
            "install.sh",
            "install.ps1",
            "*.mp4",
            "*.png",
            "*.jpg",
            "*.html",
            "tools/",
            "workflow/",
            "workflows/",
            "wildcards/",
            "styles/",
            "/autocomplete/",
            "web_beta/",
            "web_version/dev/",
            "*.cache",
            "*.ini",
            "*.bak",
            "config.yaml",
            "*.log",
            ".venv/",
        ):
            with self.subTest(entry=entry):
                self.assertIn(entry, ignore)
        ignored_lines = {
            line.strip()
            for line in ignore.splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        }
        for required_readme in ("README.md", "README.en.md", "README.ko.md", "*.md"):
            with self.subTest(required_readme=required_readme):
                self.assertNotIn(required_readme, ignored_lines)
        self.assertNotIn("autocomplete/", ignored_lines)

    def test_autocomplete_runtime_imports_are_in_registry_package_surface(self):
        entry = ROOT / "web" / "js" / "easyuse_anima_autocomplete.js"
        source = entry.read_text(encoding="utf-8")
        for runtime_path in sorted(AUTOCOMPLETE_RUNTIME_PATHS - {entry.relative_to(ROOT).as_posix()}):
            module = Path(runtime_path)
            self.assertTrue((ROOT / module).is_file())
            specifier = f"./{module.relative_to('web/js').as_posix()}"
            with self.subTest(specifier=specifier):
                self.assertIn(f'from "{specifier}"', source)

        result = subprocess.run(
            [
                "git",
                "ls-files",
                "--cached",
                "--ignored",
                "--exclude-from=.comfyignore",
            ],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        ignored = {line for line in result.stdout.splitlines() if line}
        self.assertFalse(
            AUTOCOMPLETE_RUNTIME_PATHS & ignored,
            f"autocomplete runtime imports are excluded from the Registry package: "
            f"{sorted(AUTOCOMPLETE_RUNTIME_PATHS & ignored)}",
        )

    def test_registry_safety_doc_is_linked_from_development_entry(self):
        entry = (ROOT / "docs" / "development" / "README.md").read_text(encoding="utf-8")
        safety = (ROOT / "docs" / "development" / "registry-scanner-safety.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("docs/development/registry-scanner-safety.md", entry)
        self.assertIn("comfy node validate", safety)
        self.assertIn("NAIA `requests.post`", safety)
        self.assertIn('web/js -g "!easyuse_anima_api.js"', safety)
