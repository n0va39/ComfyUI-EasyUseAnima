"""Prompt translation marker parsing."""

from __future__ import annotations

PROMPT_TRANSLATION_MARKER_LABEL = "translation"


def _is_escaped(value: str, index: int) -> bool:
    count = 0
    for cursor in range(index - 1, -1, -1):
        if value[cursor] != "\\":
            break
        count += 1
    return count % 2 == 1


def iter_prompt_translation_markers(text: str):
    value = str(text or "")
    cursor = 0
    while cursor < len(value):
        start = value.find("%{", cursor)
        if start < 0:
            break
        if _is_escaped(value, start):
            cursor = start + 2
            continue
        end = -1
        scan = start + 2
        while scan < len(value):
            if value[scan] == "}" and not _is_escaped(value, scan):
                end = scan + 1
                break
            scan += 1
        if end < 0:
            break
        yield start, end, value[start + 2 : end - 1]
        cursor = end


def has_prompt_translation_markers(text: str) -> bool:
    return next(iter_prompt_translation_markers(text), None) is not None


__all__ = (
    "PROMPT_TRANSLATION_MARKER_LABEL",
    "has_prompt_translation_markers",
    "iter_prompt_translation_markers",
)
