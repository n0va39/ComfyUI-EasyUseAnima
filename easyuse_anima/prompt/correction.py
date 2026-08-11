"""Prompt correction and translation helpers."""

from __future__ import annotations

from collections.abc import Callable
from csv import Error as CsvError

from ..autocomplete.dataset import (
    AutocompleteEntry,
    autocomplete_entry_lookup,
)
from ..autocomplete.dataset import (
    resolve_autocomplete_source as resolve_autocomplete_source_path,
)
from ..settings.service import (
    resolve_autocomplete_source,
    resolve_prompt_translation_settings,
)
from ..translation.markers import has_prompt_translation_markers
from ..translation.service import translate_prompt_markers
from .anima import PromptKnowledgeBase, TagInfo


class _AutocompletePromptKnowledgeBase(PromptKnowledgeBase):
    def __init__(
        self,
        lookup_entry: Callable[[str], AutocompleteEntry | None],
    ) -> None:
        self._lookup_entry = lookup_entry

    def lookup(self, tag: str) -> TagInfo | None:
        builtin = super().lookup(tag)
        if builtin is not None:
            return builtin
        entry: AutocompleteEntry | None = self._lookup_entry(tag)
        if entry is None:
            return None
        return TagInfo(
            tag=entry.tag_key,
            category_path=(entry.category,),
            post_count=entry.count,
            source="autocomplete",
        )


def _load_prompt_knowledge_base() -> PromptKnowledgeBase:
    try:
        selected = resolve_autocomplete_source()
        _source, path = resolve_autocomplete_source_path(selected)
        lookup_entry = autocomplete_entry_lookup(path)
    except (CsvError, OSError, RuntimeError, UnicodeError):
        return PromptKnowledgeBase.empty()
    return _AutocompletePromptKnowledgeBase(lookup_entry)


def _split_tag_text(value: str) -> list[str]:
    if not value:
        return []
    parts: list[str] = []
    for line in str(value).splitlines():
        parts.extend(part.strip() for part in line.split(","))
    return [part for part in parts if part]


def _translate_prompt_text(value: str) -> str:
    text = str(value or "")
    if not text or not has_prompt_translation_markers(text):
        return text
    return translate_prompt_markers(text, resolve_prompt_translation_settings())


def _prompt_translation_change_key() -> dict[str, str]:
    settings = resolve_prompt_translation_settings()
    return {
        "provider": settings.provider,
        "source": settings.source,
        "target": settings.target,
    }


__all__ = ()
