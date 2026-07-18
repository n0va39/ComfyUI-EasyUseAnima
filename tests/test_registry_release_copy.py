from __future__ import annotations

import json
import re
import tomllib
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
METADATA_PATH = ROOT / ".github" / "registry" / "metadata.json"
RELEASE_PATH = ROOT / "RELEASE.md"


class RegistryReleaseCopyTests(unittest.TestCase):
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
