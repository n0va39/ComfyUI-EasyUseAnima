from __future__ import annotations

import re
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AUTOCOMPLETE_ENTRY = ROOT / "web" / "js" / "easyuse_anima_autocomplete.js"
EXPECTED_AUTOCOMPLETE_MODULES = {
    "web/js/autocomplete/data_adapter.js",
    "web/js/autocomplete/input_binding.js",
    "web/js/autocomplete/input_controller.js",
    "web/js/autocomplete/popup_geometry.js",
    "web/js/autocomplete/text_model.js",
}
EXPECTED_PYTHON_PACKAGE_FILES = {
    "easyuse_anima/__init__.py",
    "easyuse_anima/aio/__init__.py",
    "easyuse_anima/common/__init__.py",
    "easyuse_anima/common/serialization.py",
    "easyuse_anima/common/values.py",
    "easyuse_anima/image/__init__.py",
    "easyuse_anima/image/detailer.py",
    "easyuse_anima/image/geometry.py",
    "easyuse_anima/image/scaling.py",
    "easyuse_anima/infrastructure/__init__.py",
    "easyuse_anima/infrastructure/comfy/__init__.py",
    "easyuse_anima/infrastructure/comfy/capabilities.py",
    "easyuse_anima/infrastructure/comfy/invocation.py",
    "easyuse_anima/infrastructure/comfy/resources.py",
    "easyuse_anima/naia/__init__.py",
    "easyuse_anima/naia/client.py",
    "easyuse_anima/naia/resolution.py",
    "easyuse_anima/nodes/__init__.py",
    "easyuse_anima/nodes/image_nodes.py",
    "easyuse_anima/nodes/naia_nodes.py",
    "easyuse_anima/nodes/wildcard_nodes.py",
    "easyuse_anima/profiles/__init__.py",
    "easyuse_anima/profiles/contract.py",
    "easyuse_anima/prompt/__init__.py",
}
STATIC_IMPORT_FROM_RE = re.compile(
    r"""
    ^[ \t]*(?:import|export)[ \t\r\n]+
    (?:(?!;).)*?\bfrom[ \t\r\n]*
    (?P<quote>["'])
    (?P<specifier>\.{1,2}/[^"']+)
    (?P=quote)[ \t\r\n]*;
    """,
    re.MULTILINE | re.DOTALL | re.VERBOSE,
)
STATIC_SIDE_EFFECT_IMPORT_RE = re.compile(
    r"""
    ^[ \t]*import[ \t\r\n]+
    (?P<quote>["'])
    (?P<specifier>\.{1,2}/[^"']+)
    (?P=quote)[ \t\r\n]*;
    """,
    re.MULTILINE | re.VERBOSE,
)


def _static_relative_imports(source: str) -> set[str]:
    imports = set()
    for pattern in (STATIC_IMPORT_FROM_RE, STATIC_SIDE_EFFECT_IMPORT_RE):
        imports.update(match.group("specifier") for match in pattern.finditer(source))
    return imports


def _repository_static_import_closure(entry: Path) -> set[str]:
    root = ROOT.resolve()
    pending = [entry.resolve()]
    visited: set[Path] = set()

    while pending:
        source_path = pending.pop()
        if source_path in visited:
            continue
        try:
            source_path.relative_to(root)
        except ValueError:
            continue
        if not source_path.is_file():
            raise AssertionError(f"missing static import source: {source_path}")
        visited.add(source_path)

        source = source_path.read_text(encoding="utf-8")
        for specifier in _static_relative_imports(source):
            imported_path = (source_path.parent / specifier).resolve()
            try:
                imported_path.relative_to(root)
            except ValueError:
                continue
            if not imported_path.is_file():
                raise AssertionError(
                    f"missing repository static import: {source_path} -> {specifier}"
                )
            pending.append(imported_path)

    return {path.relative_to(root).as_posix() for path in visited}


def _git_paths(*args: str) -> set[str]:
    result = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=10,
    )
    return {line for line in result.stdout.splitlines() if line}


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
        for filename in (
            "__init__.py",
            "api.py",
            "api_contract.py",
            "easyuse_anima/infrastructure/comfy/capabilities.py",
            "easyuse_anima/infrastructure/comfy/invocation.py",
            "easyuse_anima/infrastructure/comfy/resources.py",
            "easyuse_anima/image/detailer.py",
            "easyuse_anima/image/scaling.py",
            "easyuse_anima/naia/client.py",
            "easyuse_anima/naia/resolution.py",
            "easyuse_anima/nodes/image_nodes.py",
            "easyuse_anima/nodes/naia_nodes.py",
            "easyuse_anima/nodes/wildcard_nodes.py",
            "nodes.py",
            "prompt_translation.py",
            "settings.py",
        ):
            source = (ROOT / filename).read_text(encoding="utf-8")
            for pattern in patterns:
                with self.subTest(filename=filename, pattern=pattern):
                    self.assertNotIn(pattern, source)

    def test_naia_is_only_documented_runtime_post_call(self):
        runtime_files = (
            "api.py",
            "api_contract.py",
            "easyuse_anima/naia/client.py",
            "easyuse_anima/nodes/naia_nodes.py",
            "nodes.py",
            "prompt_translation.py",
            "settings.py",
        )
        matches = []
        for filename in runtime_files:
            source = (ROOT / filename).read_text(encoding="utf-8")
            if "requests.post" in source:
                matches.append(filename)

        self.assertEqual(matches, ["easyuse_anima/naia/client.py"])
        source = (ROOT / "easyuse_anima" / "naia" / "client.py").read_text(encoding="utf-8")
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
            ".agents/",
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

    def test_static_relative_import_parser_covers_supported_forms(self):
        source = """
            import defaultExport from "./default.js";
            import {
              namedExport,
            } from '../named.js';
            export { forwarded } from "./forwarded.js";
            export * from "../export_all.js";
            import "./side_effect.js";
            import external from "external-package";
            import "/absolute.js";
            const dynamic = import("./dynamic.js");
        """
        self.assertEqual(
            _static_relative_imports(source),
            {
                "./default.js",
                "../named.js",
                "./forwarded.js",
                "../export_all.js",
                "./side_effect.js",
            },
        )

    def test_autocomplete_static_import_closure_is_in_registry_package_surface(self):
        closure = _repository_static_import_closure(AUTOCOMPLETE_ENTRY)
        self.assertFalse(
            EXPECTED_AUTOCOMPLETE_MODULES - closure,
            f"expected autocomplete modules missing from static import closure: "
            f"{sorted(EXPECTED_AUTOCOMPLETE_MODULES - closure)}",
        )

        tracked = _git_paths("ls-files", "--cached")
        self.assertFalse(
            closure - tracked,
            f"autocomplete static import closure is not tracked: {sorted(closure - tracked)}",
        )

        ignored = _git_paths(
            "ls-files",
            "--cached",
            "--ignored",
            "--exclude-from=.comfyignore",
        )
        self.assertFalse(
            closure & ignored,
            f"autocomplete static import closure is excluded from the Registry package: "
            f"{sorted(closure & ignored)}",
        )

    def test_api_contract_runtime_module_is_in_registry_package_surface(self):
        runtime_path = "api_contract.py"
        self.assertTrue((ROOT / runtime_path).is_file())
        self.assertIn("from .api_contract import (", (ROOT / "api.py").read_text(encoding="utf-8"))

        tracked = _git_paths("ls-files", "--cached")
        self.assertIn(runtime_path, tracked)

        ignored = _git_paths(
            "ls-files",
            "--cached",
            "--ignored",
            "--exclude-from=.comfyignore",
        )
        self.assertNotIn(runtime_path, ignored)

    def test_python_package_skeleton_is_in_registry_package_surface(self):
        for runtime_path in EXPECTED_PYTHON_PACKAGE_FILES:
            with self.subTest(runtime_path=runtime_path):
                self.assertTrue((ROOT / runtime_path).is_file())

        tracked = _git_paths("ls-files", "--cached")
        self.assertFalse(
            EXPECTED_PYTHON_PACKAGE_FILES - tracked,
            "package skeleton is not tracked: "
            f"{sorted(EXPECTED_PYTHON_PACKAGE_FILES - tracked)}",
        )

        ignored = _git_paths(
            "ls-files",
            "--cached",
            "--ignored",
            "--exclude-from=.comfyignore",
        )
        self.assertFalse(
            EXPECTED_PYTHON_PACKAGE_FILES & ignored,
            "package skeleton is excluded from the Registry package: "
            f"{sorted(EXPECTED_PYTHON_PACKAGE_FILES & ignored)}",
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
