"""Tag normalization utilities for Danbooru-style prompts."""

from __future__ import annotations

import re

_SPACE_RE = re.compile(r"\s+")
_PONY_SCORE_RE = re.compile(r"^score[\s_]+(\d+)(:?)$", re.IGNORECASE)


def _normalize_pony_score_tag(tag: str) -> str | None:
    match = _PONY_SCORE_RE.match(tag.strip())
    if not match:
        return None
    return f"score_{match.group(1)}{match.group(2)}"


def normalize_tag(tag: str) -> str:
    """Normalize a tag for lookup and duplicate detection.

    Danbooru tags are case-insensitive in practice and frequently appear with
    either underscores or spaces. A leading ``@`` is kept because ANIMA uses it
    to mark artist tags.
    """

    text = tag.strip().lower()
    text = _SPACE_RE.sub(" ", text)
    pony_score = _normalize_pony_score_tag(text)
    if pony_score:
        return pony_score
    text = text.replace("_", " ")
    if text.startswith("@"):
        text = "@" + text[1:].strip()
    return text


def lookup_key(tag: str) -> str:
    """Return the canonical DB lookup key, without ANIMA's artist marker."""

    normalized = normalize_tag(tag)
    return normalized[1:].strip() if normalized.startswith("@") else normalized


def render_artist_tag(tag: str) -> str:
    """Render an ANIMA artist tag with ``@`` and prompt-style spacing."""

    key = lookup_key(tag)
    return "@" + key
