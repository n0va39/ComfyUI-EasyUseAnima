"""Shared profile filename, JSON repository, and list metadata helpers."""

from __future__ import annotations

import json
import re
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from ..errors import ValidationError
from ..infrastructure.filesystem.atomic_json import (
    AtomicJsonStore,
    create_atomic_json_store,
)
from .contract import (
    ProfileContractError,
    interpret_profile_document,
    legacy_profile_id,
    normalize_profile_filename_identity,
)
from .mutation import DirectoryMutationCoordinator

INVALID_PROFILE_NAME_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]+')
WINDOWS_RESERVED_FILE_BASENAMES = {
    "con",
    "prn",
    "aux",
    "nul",
    *(f"com{index}" for index in range(1, 10)),
    *(f"lpt{index}" for index in range(1, 10)),
    *(f"com{index}" for index in ("¹", "²", "³")),
    *(f"lpt{index}" for index in ("¹", "²", "³")),
}


class InvalidProfileDataError(ValidationError, ValueError):
    pass


@dataclass(frozen=True, slots=True)
class _ProfileRepository:
    profile_dir: Path
    store_factory: Callable[..., AtomicJsonStore]
    mutation_coordinator: DirectoryMutationCoordinator

    def store(
        self,
        path: Path,
        *,
        backup: bool | str | Path = True,
    ) -> AtomicJsonStore:
        return self.store_factory(path, backup=backup)

    def locked(self):
        return self.mutation_coordinator.locked(self.profile_dir)


def _windows_profile_filename_identity(name: str) -> str:
    return normalize_profile_filename_identity(name)


def _sanitize_profile_name(name: str) -> str:
    safe_name = INVALID_PROFILE_NAME_CHARS.sub("_", str(name or "")).strip(" ._")
    if not safe_name:
        raise ValueError("Profile name is required")
    safe_name = safe_name[:80].rstrip(" .")
    if not safe_name:
        raise ValueError("Profile name is required")
    windows_basename = safe_name.split(".", 1)[0].casefold()
    if windows_basename in WINDOWS_RESERVED_FILE_BASENAMES:
        raise ValueError("Profile name is reserved on Windows")
    return safe_name


def _read_profile_json(path: Path):
    store = create_atomic_json_store(path)
    with store.locked():
        try:
            return store.read()
        except json.JSONDecodeError:
            if path.read_text(encoding="utf-8") == "":
                return {}
            raise


def _profile_list_item(profile_kind: str, path: Path) -> dict:
    try:
        data = _read_profile_json(path)
        if not isinstance(data, dict):
            raise ProfileContractError("Profile data is invalid")
        interpreted = interpret_profile_document(profile_kind, path.stem, data)
        profile_id = interpreted["profile_id"]
        revision = interpreted["revision"]
    except ProfileContractError as exc:
        raise InvalidProfileDataError(str(exc)) from exc
    except (
        OSError,
        UnicodeError,
        json.JSONDecodeError,
    ):
        profile_id = legacy_profile_id(profile_kind, path.stem)
        revision = 0
    return {
        "name": path.stem,
        "modified": int(path.stat().st_mtime),
        "profile_id": profile_id,
        "revision": revision,
    }


__all__ = ()
