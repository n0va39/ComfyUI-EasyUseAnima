"""Narrow process autocomplete service port."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol


class AutocompletePort(Protocol):
    def resolve_source(self, source: str | None = None) -> tuple[str, Path]: ...

    def available_sources(self, selected: str | None = None) -> list[dict]: ...

    def status(self, path: Path) -> dict: ...

    def search(
        self,
        query: str,
        limit: int = 20,
        path: Path | None = None,
        category: str | None = None,
    ) -> dict: ...

    def classify(
        self,
        text: str,
        limit: int = 240,
        path: Path | None = None,
    ) -> dict: ...


__all__ = ()
