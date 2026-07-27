"""Compatibility exports for the canonical autocomplete package."""

from __future__ import annotations

try:
    from .easyuse_anima.autocomplete.classification import classify_prompt_text
    from .easyuse_anima.autocomplete.dataset import (
        AUTOCOMPLETE_CSV,
        AUTOCOMPLETE_SOURCES,
        DBR_DANBOORU_AUTOCOMPLETE_CSV,
        DBR_E621_AUTOCOMPLETE_CSV,
        DBR_MERGED_AUTOCOMPLETE_CSV,
        DBR_TAG_ARCHIVE_LICENSE,
        DBR_TAG_ARCHIVE_SOURCE,
        DEFAULT_AUTOCOMPLETE_SOURCE,
        LOCALSMILE_AUTOCOMPLETE_CSV,
        AutocompleteEntry,
        autocomplete_status,
        available_autocomplete_sources,
        resolve_autocomplete_source,
    )
    from .easyuse_anima.autocomplete.search import search_autocomplete
except ImportError:
    from easyuse_anima.autocomplete.classification import classify_prompt_text
    from easyuse_anima.autocomplete.dataset import (
        AUTOCOMPLETE_CSV,
        AUTOCOMPLETE_SOURCES,
        DBR_DANBOORU_AUTOCOMPLETE_CSV,
        DBR_E621_AUTOCOMPLETE_CSV,
        DBR_MERGED_AUTOCOMPLETE_CSV,
        DBR_TAG_ARCHIVE_LICENSE,
        DBR_TAG_ARCHIVE_SOURCE,
        DEFAULT_AUTOCOMPLETE_SOURCE,
        LOCALSMILE_AUTOCOMPLETE_CSV,
        AutocompleteEntry,
        autocomplete_status,
        available_autocomplete_sources,
        resolve_autocomplete_source,
    )
    from easyuse_anima.autocomplete.search import search_autocomplete

__all__ = [
    "DBR_TAG_ARCHIVE_SOURCE",
    "DBR_TAG_ARCHIVE_LICENSE",
    "DBR_DANBOORU_AUTOCOMPLETE_CSV",
    "DBR_E621_AUTOCOMPLETE_CSV",
    "DBR_MERGED_AUTOCOMPLETE_CSV",
    "LOCALSMILE_AUTOCOMPLETE_CSV",
    "AUTOCOMPLETE_CSV",
    "DEFAULT_AUTOCOMPLETE_SOURCE",
    "AUTOCOMPLETE_SOURCES",
    "AutocompleteEntry",
    "resolve_autocomplete_source",
    "available_autocomplete_sources",
    "autocomplete_status",
    "search_autocomplete",
    "classify_prompt_text",
]
