"""Danbooru-style prompt parsing."""

from __future__ import annotations

import re

from .models import ParsedPrompt

_SENTENCE_COUNT_SPLIT_RE = re.compile(
    r"(?<=[.!?])\s+(?=(?:"
    r"solo|no humans|multiple boys|multiple girls|multiple others|"
    r"[1-6]\+?\s*(?:boys?|girls?|others?)"
    r")\b)",
    re.IGNORECASE,
)


def parse_prompt(text: str, *, profile: str = "prompt") -> ParsedPrompt:
    """Parse prompt text into raw tag tokens.

    ComfyUI/NovelAI prompt parentheses are syntax unless escaped. Commas inside
    unescaped parentheses are kept in the same token so weighted prompt groups
    are not split incorrectly.
    """

    profile = (profile or "prompt").strip().lower()
    delimiter = ", "
    tokens = _split_prompt_tokens(text)
    tokens = _split_sentence_count_tokens(tokens)
    tokens = [part for part in tokens if part]
    return ParsedPrompt(
        text=text,
        tokens=tuple(tokens),
        delimiter=delimiter,
        profile=profile,
    )


def _is_escaped(text: str, index: int) -> bool:
    slash_count = 0
    cursor = index - 1
    while cursor >= 0 and text[cursor] == "\\":
        slash_count += 1
        cursor -= 1
    return slash_count % 2 == 1


def _split_prompt_tokens(text: str) -> list[str]:
    tokens: list[str] = []
    start = 0
    depth = 0
    for index, char in enumerate(text):
        if char == "(" and not _is_escaped(text, index):
            depth += 1
        elif char == ")" and not _is_escaped(text, index):
            depth = max(0, depth - 1)
        elif char == "," and depth == 0:
            tokens.append(text[start:index].strip())
            start = index + 1
    tokens.append(text[start:].strip())
    return tokens


def _split_sentence_count_tokens(tokens: list[str]) -> list[str]:
    split_tokens: list[str] = []
    for token in tokens:
        parts = [part.strip() for part in _SENTENCE_COUNT_SPLIT_RE.split(token) if part.strip()]
        split_tokens.extend(parts or [token])
    return split_tokens


def render_tags(tags: list[str], delimiter: str) -> str:
    return ", ".join(tags)
