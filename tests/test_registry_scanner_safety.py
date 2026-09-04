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
    "easyuse_anima/aio/conditioning.py",
    "easyuse_anima/aio/first_pass_cache.py",
    "easyuse_anima/aio/generation_values.py",
    "easyuse_anima/aio/generation_sampling.py",
    "easyuse_anima/aio/generation_features.py",
    "easyuse_anima/aio/generation_detailer.py",
    "easyuse_anima/aio/generation_output.py",
    "easyuse_anima/aio/generation_migrations.py",
    "easyuse_anima/aio/generation_settings.py",
    "easyuse_anima/aio/model_preparation.py",
    "easyuse_anima/aio/output.py",
    "easyuse_anima/aio/preview.py",
    "easyuse_anima/aio/resources.py",
    "easyuse_anima/aio/sampling.py",
    "easyuse_anima/api/__init__.py",
    "easyuse_anima/api/errors.py",
    "easyuse_anima/api/requests.py",
    "easyuse_anima/api/responses.py",
    "easyuse_anima/api/routes/__init__.py",
    "easyuse_anima/api/routes/aio_torch_compile.py",
    "easyuse_anima/api/routes/autocomplete.py",
    "easyuse_anima/api/routes/translation.py",
    "easyuse_anima/api/routes/translation_execution.py",
    "easyuse_anima/api/routes/wildcards.py",
    "easyuse_anima/autocomplete/__init__.py",
    "easyuse_anima/autocomplete/dataset.py",
    "easyuse_anima/autocomplete/index.py",
    "easyuse_anima/autocomplete/search.py",
    "easyuse_anima/bootstrap.py",
    "easyuse_anima/workflow.py",
    "easyuse_anima/common/__init__.py",
    "easyuse_anima/common/serialization.py",
    "easyuse_anima/common/values.py",
    "easyuse_anima/image/__init__.py",
    "easyuse_anima/image/detailer.py",
    "easyuse_anima/image/geometry.py",
    "easyuse_anima/image/sam3.py",
    "easyuse_anima/image/scaling.py",
    "easyuse_anima/infrastructure/__init__.py",
    "easyuse_anima/infrastructure/comfy/__init__.py",
    "easyuse_anima/infrastructure/comfy/capabilities.py",
    "easyuse_anima/infrastructure/comfy/invocation.py",
    "easyuse_anima/infrastructure/comfy/resources.py",
    "easyuse_anima/infrastructure/filesystem/__init__.py",
    "easyuse_anima/infrastructure/filesystem/atomic_json.py",
    "easyuse_anima/infrastructure/filesystem/paths.py",
    "easyuse_anima/lora/__init__.py",
    "easyuse_anima/lora/metadata.py",
    "easyuse_anima/lora/preset.py",
    "easyuse_anima/naia/__init__.py",
    "easyuse_anima/naia/client.py",
    "easyuse_anima/naia/resolution.py",
    "easyuse_anima/nodes/__init__.py",
    "easyuse_anima/nodes/aio_nodes.py",
    "easyuse_anima/nodes/image_nodes.py",
    "easyuse_anima/nodes/input_types.py",
    "easyuse_anima/nodes/lora_nodes.py",
    "easyuse_anima/nodes/naia_nodes.py",
    "easyuse_anima/nodes/prompt_data_nodes.py",
    "easyuse_anima/nodes/prompt_nodes.py",
    "easyuse_anima/nodes/wildcard_nodes.py",
    "easyuse_anima/profiles/__init__.py",
    "easyuse_anima/profiles/aio.py",
    "easyuse_anima/profiles/contract.py",
    "easyuse_anima/profiles/lora.py",
    "easyuse_anima/profiles/mutation.py",
    "easyuse_anima/profiles/repository.py",
    "easyuse_anima/settings/__init__.py",
    "easyuse_anima/settings/repository.py",
    "easyuse_anima/settings/schema.py",
    "easyuse_anima/settings/service.py",
    "easyuse_anima/wildcard/__init__.py",
    "easyuse_anima/wildcard/mode.py",
    "easyuse_anima/wildcard/models.py",
    "easyuse_anima/wildcard/seed.py",
    "easyuse_anima/wildcard/selector.py",
    "easyuse_anima/wildcard/snapshot.py",
    "easyuse_anima/wildcard/sources.py",
    "easyuse_anima/registration.py",
    "easyuse_anima/prompt/__init__.py",
    "easyuse_anima/prompt/correction.py",
    "easyuse_anima/prompt/artist_mix.py",
    "easyuse_anima/prompt/conditioning.py",
    "easyuse_anima/prompt/data.py",
    "easyuse_anima/prompt/fields.py",
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
            "torch.load(",
            "yaml.load(",
            "base64.b64decode",
            "GOOGLE_TRANSLATION_API_KEY",
            "os.environ",
        )
        runtime_python = (
            ROOT / "__init__.py",
            *sorted((ROOT / "easyuse_anima").rglob("*.py")),
        )
        for source_path in runtime_python:
            filename = source_path.relative_to(ROOT).as_posix()
            source = source_path.read_text(encoding="utf-8")
            for pattern in patterns:
                with self.subTest(filename=filename, pattern=pattern):
                    self.assertNotIn(pattern, source)

    def test_naia_is_only_documented_runtime_post_call(self):
        runtime_files = (
            "easyuse_anima/naia/client.py",
            "easyuse_anima/nodes/naia_nodes.py",
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
            "pyrightconfig.json",
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

    def test_api_contract_runtime_modules_are_in_registry_package_surface(self):
        runtime_paths = {
            "easyuse_anima/api/__init__.py",
            "easyuse_anima/api/application.py",
            "easyuse_anima/api/errors.py",
            "easyuse_anima/api/requests.py",
            "easyuse_anima/api/responses.py",
            "easyuse_anima/bootstrap.py",
        }
        for runtime_path in runtime_paths:
            with self.subTest(runtime_path=runtime_path):
                self.assertTrue((ROOT / runtime_path).is_file())

        import_owners = {
            "errors": "application_routes.py",
            "requests": "application_routes.py",
            "responses": "application.py",
        }
        for module, owner in import_owners.items():
            owner_source = (ROOT / "easyuse_anima" / "api" / owner).read_text(
                encoding="utf-8"
            )
            self.assertIn(f"from .{module} import", owner_source)

        tracked = _git_paths("ls-files", "--cached")
        self.assertFalse(runtime_paths - tracked)

        ignored = _git_paths(
            "ls-files",
            "--cached",
            "--ignored",
            "--exclude-from=.comfyignore",
        )
        self.assertFalse(runtime_paths & ignored)

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
        self.assertIn("same-authority", safety)
        self.assertIn("ComfyUI output root", safety)
        self.assertIn("issue #679", safety)
        self.assertIn('web/js -g "!easyuse_anima_api.js"', safety)
