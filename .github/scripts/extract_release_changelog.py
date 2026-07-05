#!/usr/bin/env python3
"""Extract one version section from RELEASE.md for `comfy node publish`."""

from __future__ import annotations

import argparse
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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pyproject", type=Path, default=Path("pyproject.toml"))
    parser.add_argument("--release", type=Path, default=Path("RELEASE.md"))
    parser.add_argument("--version", default="", help="Version to extract. Defaults to pyproject version.")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)

    version = args.version.strip() or _pyproject_version(args.pyproject)
    changelog = _extract_section(args.release, version)
    args.output.write_text(changelog, encoding="utf-8")
    print(f"Extracted RELEASE.md changelog for {version} to {args.output}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1)
