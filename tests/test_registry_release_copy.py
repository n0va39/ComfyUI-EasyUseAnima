from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import re
import tempfile
import tomllib
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
METADATA_PATH = ROOT / ".github" / "registry" / "metadata.json"
RELEASE_PATH = ROOT / "RELEASE.md"


class RegistryPublishVersionTests(unittest.TestCase):
    def setUp(self) -> None:
        spec = importlib.util.spec_from_file_location(
            "extract_release_changelog", ROOT / ".github/scripts/extract_release_changelog.py",
        )
        self.extractor = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.extractor)
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.pyproject = self.root / "pyproject.toml"
        self.pyproject.write_text('[project]\nversion = "3.2.1"\n', encoding="utf-8")
        self.changelogs = self.root / "changelogs"
        self.changelogs.mkdir()
        (self.changelogs / "3.2.1.txt").write_text("Current release notes\n", encoding="utf-8")
        (self.changelogs / "3.2.0.txt").write_text("Older release notes\n", encoding="utf-8")
        self.output = self.root / "output.txt"

    def _run(self, version: str | None = None) -> int:
        arguments = [
            "--pyproject", str(self.pyproject),
            "--registry-changelog-dir", str(self.changelogs),
            "--output", str(self.output),
        ]
        if version is not None:
            arguments.extend(["--version", version])
        with contextlib.redirect_stdout(io.StringIO()):
            return self.extractor.main(arguments)

    def test_omitted_or_matching_version_extracts_package_changelog(self) -> None:
        for version in (None, "", "3.2.1", " 3.2.1 "):
            with self.subTest(version=version):
                self.assertEqual(self._run(version), 0)
                self.assertEqual(self.output.read_text(encoding="utf-8"), "Current release notes\n")

    def test_mismatched_version_cannot_overwrite_output_with_old_changelog(self) -> None:
        self.output.write_text("Existing output\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "does not match.*3.2.1"):
            self._run("3.2.0")
        self.assertEqual(self.output.read_text(encoding="utf-8"), "Existing output\n")

    def test_explicit_version_cannot_skip_package_identity(self) -> None:
        self.pyproject.unlink()
        with self.assertRaises(FileNotFoundError):
            self._run("3.2.1")
        self.assertFalse(self.output.exists())


class RegistryReleaseCopyTests(unittest.TestCase):
    def test_historical_registry_omissions_are_explicit_and_not_synced(self) -> None:
        metadata = json.loads(METADATA_PATH.read_text(encoding="utf-8"))
        synced_versions = {item["version"] for item in metadata["versions"]}
        omissions = metadata.get("omitted_versions", [])

        self.assertIn("0.6.1", {item["version"] for item in omissions})
        for item in omissions:
            with self.subTest(version=item.get("version")):
                self.assertEqual(set(item), {"version", "reason"})
                self.assertNotIn(item["version"], synced_versions)
                self.assertTrue(item["reason"].strip())
                self.assertTrue(
                    (METADATA_PATH.parent / "changelogs" / f"{item['version']}.txt").is_file()
                )

    def test_only_current_registry_version_is_not_deprecated(self) -> None:
        project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
        current_version = project["project"]["version"]
        metadata = json.loads(METADATA_PATH.read_text(encoding="utf-8"))

        current = [
            item["version"]
            for item in metadata["versions"]
            if not item.get("deprecated", False)
        ]
        self.assertEqual(current, [current_version])

    def test_current_version_uses_user_facing_plain_text_changelog(self) -> None:
        project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
        version = project["project"]["version"]
        metadata = json.loads(METADATA_PATH.read_text(encoding="utf-8"))

        entry = next(item for item in metadata["versions"] if item["version"] == version)
        self.assertNotIn("changelog", entry)
        relative_path = Path(entry["changelog_file"])
        self.assertFalse(relative_path.is_absolute())

        registry_root = METADATA_PATH.parent.resolve()
        changelog_path = (registry_root / relative_path).resolve()
        self.assertTrue(changelog_path.is_relative_to(registry_root))
        self.assertTrue(changelog_path.is_file(), changelog_path)

        text = changelog_path.read_text(encoding="utf-8").strip()
        self.assertTrue(text.startswith(f"EasyUse Anima {version} "))
        self.assertIn("\n\nChanges:\n", text)
        self.assertIn("\n\nAction required:\n", text)
        self.assertNotRegex(text, re.compile(r"(?m)^#{1,6}\s"))
        self.assertNotRegex(text, re.compile(r"(?m)^[-*]\s"))
        self.assertNotRegex(text, re.compile(r"\[[^\]]+\]\([^)]+\)"))
        self.assertNotIn("`", text)

        lowered = text.lower()
        for internal_phrase in (
            ".comfyignore",
            "registry archive",
            "package validation",
            "pull request",
            "commit sha",
            "semantic smoke",
            "typescript",
            "module extraction",
            "scanner finding",
            "release bookkeeping",
        ):
            with self.subTest(internal_phrase=internal_phrase):
                self.assertNotIn(internal_phrase, lowered)

    def test_current_github_release_section_is_user_facing(self) -> None:
        project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
        version = project["project"]["version"]
        release_text = RELEASE_PATH.read_text(encoding="utf-8")
        match = re.search(
            rf"(?ms)^## {re.escape(version)}\s*$.*?(?=^## \S|\Z)",
            release_text,
        )
        self.assertIsNotNone(match, f"missing RELEASE.md section for {version}")
        section = match.group(0)
        self.assertIn("### Fixed", section)
        self.assertIn("### Update", section)

        lowered = section.lower()
        for internal_phrase in (
            "validation notes",
            "python unittest",
            "typescript",
            "diff check",
            "pull request",
            "commit sha",
            "scanner finding",
            "module extraction",
            "release bookkeeping",
        ):
            with self.subTest(internal_phrase=internal_phrase):
                self.assertNotIn(internal_phrase, lowered)


if __name__ == "__main__":
    unittest.main()
