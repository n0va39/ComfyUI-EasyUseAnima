"""Package and user data path discovery."""

from __future__ import annotations

import os
from pathlib import Path
from typing import cast

PACKAGE_ROOT = Path(__file__).resolve().parents[3]
PACKAGE_DATA_DIR = PACKAGE_ROOT / "__easyuse_anima__"
SYSTEM_USER_NAME = "easyuse_anima"


def _resolve_user_data_dir() -> Path:
    try:
        import folder_paths  # type: ignore

        get_system_user_directory = getattr(
            folder_paths,
            "get_system_user_directory",
            None,
        )
        if callable(get_system_user_directory):
            return Path(
                cast(
                    str | os.PathLike[str],
                    get_system_user_directory(SYSTEM_USER_NAME),
                )
            )

        get_user_directory = getattr(folder_paths, "get_user_directory", None)
        if callable(get_user_directory):
            return Path(
                cast(str | os.PathLike[str], get_user_directory())
            ) / f"__{SYSTEM_USER_NAME}"
    except Exception:
        pass
    return PACKAGE_DATA_DIR


USER_DATA_DIR = _resolve_user_data_dir()


__all__ = (
    "PACKAGE_DATA_DIR",
    "PACKAGE_ROOT",
    "SYSTEM_USER_NAME",
    "USER_DATA_DIR",
)
