"""Narrow process autocomplete service port."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from .contracts import (
    AutocompleteClassificationPayload,
    AutocompleteSearchPayload,
    AutocompleteSourcePayload,
    AutocompleteStatusPayload,
)


class AutocompletePort(Protocol):
    def resolve_source(self, source: str | None = None) -> tuple[str, Path]: ...

    def available_sources(
        self,
        selected: str | None = None,
    ) -> list[AutocompleteSourcePayload]: ...

    def status(self, path: Path) -> AutocompleteStatusPayload: ...

    def search(
        self,
        query: str,
        limit: int = 20,
        path: Path | None = None,
        category: str | None = None,
    ) -> AutocompleteSearchPayload: ...

    def classify(
        self,
        text: str,
        limit: int = 240,
        path: Path | None = None,
    ) -> AutocompleteClassificationPayload: ...


__all__ = ()
