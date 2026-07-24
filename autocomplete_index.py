"""Compatibility shim for the canonical autocomplete index implementation."""

from __future__ import annotations

try:
    from .easyuse_anima.autocomplete.index import (
        AUTOCOMPLETE_INDEX_SCHEMA_VERSION,
        AutocompleteIndexDiagnostics,
        AutocompleteIndexResult,
        AutocompleteIndexSource,
        AutocompleteIndexUnavailable,
        IndexedAutocompleteEntry,
        search_autocomplete_index,
    )
except ImportError:
    from easyuse_anima.autocomplete.index import (
        AUTOCOMPLETE_INDEX_SCHEMA_VERSION,
        AutocompleteIndexDiagnostics,
        AutocompleteIndexResult,
        AutocompleteIndexSource,
        AutocompleteIndexUnavailable,
        IndexedAutocompleteEntry,
        search_autocomplete_index,
    )


__all__ = (
    "AUTOCOMPLETE_INDEX_SCHEMA_VERSION",
    "AutocompleteIndexSource",
    "IndexedAutocompleteEntry",
    "AutocompleteIndexDiagnostics",
    "AutocompleteIndexResult",
    "AutocompleteIndexUnavailable",
    "search_autocomplete_index",
)
