#!/usr/bin/env python3
"""Extract one version section from RELEASE.md for `comfy node publish`."""

from __future__ import annotations

import argparse
import json
import re
import sys
import tomllib
from pathlib import Path


def _pyproject_version(path: Path) -> str:
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    version = data.get("project", {}).get("version")
    if not isinstance(version, str) or not version:
        raise ValueError(f"Could not read [project].version from {path}")
    return version


def _extract_section(release_path: Path, version: str) -> str:
    text = release_path.read_text(encoding="utf-8")
    heading = re.compile(rf"^##\s+{re.escape(version)}\s*$", re.MULTILINE)
    match = heading.search(text)
    if match is None:
        raise ValueError(f"Could not find RELEASE.md section for version {version}")

    next_heading = re.compile(r"^##\s+\S+", re.MULTILINE).search(text, match.end())
    end = next_heading.start() if next_heading else len(text)
    section = text[match.end() : end].strip()
    if not section:
        raise ValueError(f"RELEASE.md section for version {version} is empty")
    return section + "\n"


def _registry_changelog_file(changelog_dir: Path, version: str) -> str | None:
    path = changelog_dir / f"{version}.txt"
    if not path.exists():
        return None
    changelog = path.read_text(encoding="utf-8").strip()
    return changelog + "\n" if changelog else None


def _read_metadata_changelog_file(metadata_path: Path, value: str) -> str:
    path = Path(value)
    if not path.is_absolute():
        path = metadata_path.parent / path
    return path.read_text(encoding="utf-8").strip()


def _metadata_changelog(metadata_path: Path, version: str) -> str | None:
    if not metadata_path.exists():
        return None
    data = json.loads(metadata_path.read_text(encoding="utf-8"))
    versions = data.get("versions")
    if not isinstance(versions, list):
        return None
    for item in versions:
        if not isinstance(item, dict) or str(item.get("version") or "") != version:
            continue
        changelog_file = item.get("changelog_file")
        if isinstance(changelog_file, str) and changelog_file.strip():
            changelog = _read_metadata_changelog_file(metadata_path, changelog_file)
            return changelog + "\n" if changelog else None
        changelog = str(item.get("changelog") or "").strip()
        return changelog + "\n" if changelog else None
    return None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pyproject", type=Path, default=Path("pyproject.toml"))
    parser.add_argument("--release", type=Path, default=Path("RELEASE.md"))
    parser.add_argument("--metadata", type=Path, default=Path(".github/registry/metadata.json"))
    parser.add_argument("--registry-changelog-dir", type=Path, default=Path(".github/registry/changelogs"))
    parser.add_argument("--version", default="", help="Expected package version. Must match pyproject.toml.")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)

    package_version = _pyproject_version(args.pyproject)
    version = args.version.strip() or package_version
    if version != package_version:
        raise ValueError(
            f"Requested version {version} does not match package version {package_version}"
        )
    changelog = (
        _registry_changelog_file(args.registry_changelog_dir, version)
        or _metadata_changelog(args.metadata, version)
        or _extract_section(args.release, version)
    )
    args.output.write_text(changelog, encoding="utf-8")
    print(f"Extracted Registry changelog for {version} to {args.output}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1)
