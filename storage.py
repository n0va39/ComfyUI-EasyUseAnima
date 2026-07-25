"""Compatibility shim for canonical filesystem storage."""

from __future__ import annotations

try:
    from .easyuse_anima.infrastructure.filesystem.atomic_json import AtomicJsonStore
    from .easyuse_anima.infrastructure.filesystem.paths import (
        PACKAGE_DATA_DIR,
        PACKAGE_ROOT,
        SYSTEM_USER_NAME,
        USER_DATA_DIR,
    )
except ImportError:
    from easyuse_anima.infrastructure.filesystem.atomic_json import AtomicJsonStore
    from easyuse_anima.infrastructure.filesystem.paths import (
        PACKAGE_DATA_DIR,
        PACKAGE_ROOT,
        SYSTEM_USER_NAME,
        USER_DATA_DIR,
    )


__all__ = (
    "AtomicJsonStore",
    "PACKAGE_DATA_DIR",
    "PACKAGE_ROOT",
    "SYSTEM_USER_NAME",
    "USER_DATA_DIR",
)
