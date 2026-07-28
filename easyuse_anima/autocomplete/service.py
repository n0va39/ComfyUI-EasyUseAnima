"""Owner-bound autocomplete service used by bootstrap composition."""

from __future__ import annotations

from pathlib import Path

from .classification import _classify_prompt_text_from_snapshot
from .dataset import (
    AUTOCOMPLETE_CSV,
    _AutocompleteSnapshot,
    _AutocompleteSnapshotStore,
    _autocomplete_status_with_owner,
    _snapshot_with_owner,
    available_autocomplete_sources,
    resolve_autocomplete_source,
)
from .index import _AutocompleteIndexStore
from .search import _search_autocomplete_with_owners


class _AutocompleteService:
    __slots__ = ("_index_store", "_snapshots")

    def __init__(
        self,
        *,
        snapshots: _AutocompleteSnapshotStore,
        index_store: _AutocompleteIndexStore,
    ) -> None:
        self._snapshots = snapshots
        self._index_store = index_store

    @property
    def snapshots(self) -> _AutocompleteSnapshotStore:
        return self._snapshots

    @property
    def index_store(self) -> _AutocompleteIndexStore:
        return self._index_store

    def resolve_source(self, source: str | None = None) -> tuple[str, Path]:
        return resolve_autocomplete_source(source)

    def available_sources(self, selected: str | None = None) -> list[dict]:
        return available_autocomplete_sources(selected)

    def _snapshot(self, path: Path) -> _AutocompleteSnapshot:
        return _snapshot_with_owner(
            path,
            snapshot_for_key=self._snapshots.snapshot_for_key,
        )

    def status(self, path: Path = AUTOCOMPLETE_CSV) -> dict:
        return _autocomplete_status_with_owner(
            path,
            cached_snapshot_for_key=self._snapshots.cached_snapshot_for_key,
            snapshot=self._snapshot,
        )

    def search(
        self,
        query: str,
        limit: int = 20,
        path: Path | None = None,
        category: str | None = None,
    ) -> dict:
        effective_path = AUTOCOMPLETE_CSV if path is None else Path(path)
        return _search_autocomplete_with_owners(
            query,
            limit=limit,
            path=effective_path,
            category=category,
            status=self.status,
            snapshot=self._snapshot,
            index_store=self._index_store,
        )

    def classify(
        self,
        text: str,
        limit: int = 240,
        path: Path | None = None,
    ) -> dict:
        effective_path = AUTOCOMPLETE_CSV if path is None else Path(path)
        return _classify_prompt_text_from_snapshot(
            text,
            limit=limit,
            path=effective_path,
            snapshot=self._snapshot(effective_path),
        )


__all__ = ()
