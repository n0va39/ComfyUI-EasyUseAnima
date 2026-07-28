"""Indexed autocomplete search and exact Python fallback ranking."""

from __future__ import annotations

import heapq
import time
from pathlib import Path

from .dataset import (
    AUTOCOMPLETE_CSV,
    AutocompleteEntry,
    _AUTOCOMPLETE_CACHE_LOAD_ATTEMPTS,
    _AutocompleteCacheKey,
    _AutocompleteSnapshot,
    _AutocompleteSourceChanged,
    _MISSING_FILE_STAT,
    _cache_key,
    _cache_key_from_resolved_path,
    _load_entries,
    _normalize,
    _snapshot,
    _status_from_key,
    autocomplete_status,
)
from .index import (
    AutocompleteIndexDiagnostics,
    AutocompleteIndexSource,
    AutocompleteIndexUnavailable,
    _DEFAULT_AUTOCOMPLETE_INDEX_STORE,
)


def _autocomplete_match_score(
    entry: AutocompleteEntry,
    normalized_query: str,
) -> int | None:
    if entry.tag_key == normalized_query:
        return 0
    if entry.tag_key.startswith(normalized_query):
        return 1
    if normalized_query in entry.tag_key:
        return 2
    if normalized_query in entry.search:
        return 3
    return None


def _top_autocomplete_matches(
    entries: tuple[AutocompleteEntry, ...],
    normalized_query: str,
    categories: set[str],
    limit: int,
) -> list[tuple[int, AutocompleteEntry]]:
    def matches():
        for entry in entries:
            if categories and entry.category not in categories:
                continue
            score = _autocomplete_match_score(entry, normalized_query)
            if score is not None:
                yield (score, entry)

    return heapq.nsmallest(
        limit,
        matches(),
        key=lambda item: (item[0], -item[1].count, item[1].tag),
    )


def _index_source(key: _AutocompleteCacheKey) -> AutocompleteIndexSource:
    return AutocompleteIndexSource(
        resolved_path=key.resolved_path,
        revision=f"{key.schema_version}:{key.mtime_ns}:{key.size}",
    )


def _validate_index_source(key: _AutocompleteCacheKey) -> None:
    if _cache_key_from_resolved_path(Path(key.resolved_path)) != key:
        raise _AutocompleteSourceChanged(key.resolved_path)


def _fallback_index_diagnostics(
    key: _AutocompleteCacheKey,
    snapshot: _AutocompleteSnapshot,
    reason: str,
) -> AutocompleteIndexDiagnostics:
    return AutocompleteIndexDiagnostics(
        outcome="fallback",
        reason=reason,
        backend="python_snapshot",
        source_revision=_index_source(key).revision,
        entry_count=len(snapshot.entries),
        index_path=None,
    )


def _search_autocomplete_with_diagnostics(
    query: str,
    limit: int = 20,
    path: Path = AUTOCOMPLETE_CSV,
    category: str | None = None,
) -> tuple[dict, AutocompleteIndexDiagnostics]:
    started = time.perf_counter()
    effective_limit = max(1, min(limit, 100))
    normalized_query = _normalize(query)
    category = str(category or "").strip()
    categories = {item.strip() for item in category.split(",") if item.strip()}

    for _attempt in range(_AUTOCOMPLETE_CACHE_LOAD_ATTEMPTS):
        key = _cache_key(path)
        if key.mtime_ns == _MISSING_FILE_STAT:
            snapshot = _snapshot(path)
            key = snapshot.key
            if key.mtime_ns != _MISSING_FILE_STAT:
                continue
            diagnostics = _fallback_index_diagnostics(key, snapshot, "missing_source")
            limited: list[tuple[int, AutocompleteEntry]] = []
            entry_count = 0
            indexed_entries = None
            break

        try:
            indexed = _DEFAULT_AUTOCOMPLETE_INDEX_STORE.search(
                source=_index_source(key),
                normalized_query=normalized_query,
                categories=categories,
                limit=effective_limit,
                load_entries=lambda: _load_entries(  # pyright: ignore[reportArgumentType]
                    Path(key.resolved_path)
                ),
                validate_source=lambda: _validate_index_source(key),
            )
        except _AutocompleteSourceChanged:
            continue
        except AutocompleteIndexUnavailable as error:
            snapshot = _snapshot(path)
            key = snapshot.key
            diagnostics = _fallback_index_diagnostics(key, snapshot, error.reason)
            limited = _top_autocomplete_matches(
                snapshot.entries,
                normalized_query,
                categories,
                effective_limit,
            )
            entry_count = len(snapshot.entries)
            indexed_entries = None
        else:
            try:
                _validate_index_source(key)
            except _AutocompleteSourceChanged:
                continue
            diagnostics = indexed.diagnostics
            limited = []
            entry_count = indexed.diagnostics.entry_count
            indexed_entries = indexed.entries
        break
    else:
        resolved_path = Path(path).resolve(strict=False)
        raise RuntimeError(
            f"Autocomplete dataset changed repeatedly while loading: {resolved_path}"
        ) from None

    if indexed_entries is None:
        result_entries = [entry for _, entry in limited]
    else:
        result_entries = indexed_entries

    payload = {
        "query": query,
        "category": category,
        "results": [
            {
                "tag": entry.tag,
                "category": entry.category,
                "count": entry.count,
                "description": entry.description,
            }
            for entry in result_entries
        ],
        "status": _status_from_key(key, path, entry_count),
        "elapsed_ms": round((time.perf_counter() - started) * 1000, 2),
    }
    return payload, diagnostics


def search_autocomplete(
    query: str,
    limit: int = 20,
    path: Path = AUTOCOMPLETE_CSV,
    category: str | None = None,
) -> dict:
    normalized_query = _normalize(query)
    if not normalized_query:
        return {
            "query": query,
            "results": [],
            "status": autocomplete_status(path),
            "elapsed_ms": 0,
        }
    payload, _diagnostics = _search_autocomplete_with_diagnostics(
        query,
        limit=limit,
        path=path,
        category=category,
    )
    return payload


__all__ = ("search_autocomplete",)
