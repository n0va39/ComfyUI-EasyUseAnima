"""Small helpers for isolated API-module tests."""

from __future__ import annotations

import sys
from collections.abc import Generator, Mapping
from contextlib import contextmanager
from types import ModuleType


@contextmanager
def replace_sys_modules(
    replacements: Mapping[str, ModuleType],
) -> Generator[None, None, None]:
    """Replace exact modules without rolling back unrelated imports."""

    missing = object()
    previous = {
        name: sys.modules.get(name, missing)
        for name in replacements
    }
    sys.modules.update(replacements)
    try:
        yield
    finally:
        for name, module in previous.items():
            if module is missing:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = module


__all__ = ("replace_sys_modules",)
