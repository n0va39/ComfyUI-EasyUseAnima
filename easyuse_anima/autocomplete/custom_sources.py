"""Read-only CSV catalog confined to the server-owned user data directory."""

from __future__ import annotations

import hashlib
import io
import os
import stat
from pathlib import Path

from ..infrastructure.filesystem.paths import USER_DATA_DIR

MAX_CUSTOM_CSV_BYTES = 64 * 1024 * 1024


def _root() -> Path:
    return USER_DATA_DIR.resolve() / "autocomplete"


def _plain_stat(path: Path) -> os.stat_result:
    value = path.lstat()
    if stat.S_ISLNK(value.st_mode) or getattr(value, "st_file_attributes", 0) & 0x400:
        raise ValueError("Custom CSV links and reparse points are not supported")
    return value


def validate_custom_csv(path: Path) -> os.stat_result:
    root = _root()
    if path.parent != root or path.suffix.lower() != ".csv":
        raise ValueError("Custom CSV must be directly inside the autocomplete folder")
    if not stat.S_ISDIR(_plain_stat(root).st_mode):
        raise ValueError("Custom CSV folder is not a directory")
    value = _plain_stat(path)
    if not stat.S_ISREG(value.st_mode) or value.st_nlink != 1:
        raise ValueError("Custom CSV must be a regular file without links")
    if value.st_size > MAX_CUSTOM_CSV_BYTES:
        raise ValueError("Custom CSV exceeds the 64 MiB limit")
    return value


def is_custom_csv(path: Path) -> bool:
    # Keep the lexical path until validation; resolving a link first would lose
    # the information that it came from the user catalog.
    return path.absolute().parent == _root()


def custom_csv_sources() -> dict[str, Path]:
    root = _root()
    try:
        if not stat.S_ISDIR(_plain_stat(root).st_mode):
            return {}
        paths = sorted(root.iterdir(), key=lambda path: path.name)
    except (OSError, ValueError):
        return {}
    sources: dict[str, Path] = {}
    for path in paths:
        try:
            validate_custom_csv(path)
        except (OSError, ValueError):
            continue
        # Only catalog lookups accept these IDs. Never turn a client value
        # into a filesystem path, even if it looks like a filename or URL.
        key = "custom:" + hashlib.sha256(path.name.encode("utf-8")).hexdigest()
        sources[key] = path
    return sources


def read_custom_csv(path: Path) -> io.StringIO:
    before = validate_custom_csv(path)
    with path.open("rb") as handle:
        opened = os.fstat(handle.fileno())
        current = validate_custom_csv(path)
        identity = (before.st_dev, before.st_ino)
        if identity != (opened.st_dev, opened.st_ino) or identity != (
            current.st_dev, current.st_ino
        ):
            raise ValueError("Custom CSV changed while opening")
        content = handle.read(MAX_CUSTOM_CSV_BYTES + 1)
        validate_custom_csv(path)
    if len(content) > MAX_CUSTOM_CSV_BYTES:
        raise ValueError("Custom CSV exceeds the 64 MiB limit")
    return io.StringIO(content.decode("utf-8-sig"), newline="")
