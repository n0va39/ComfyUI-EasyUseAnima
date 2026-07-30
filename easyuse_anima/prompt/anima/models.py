"""Small data models for prompt correction."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class TagSection(str, Enum):
    QUALITY = "quality"
    META = "meta"
    YEAR = "year"
    SAFETY = "safety"
    COUNT = "count"
    CHARACTER = "character"
    COPYRIGHT = "copyright"
    ARTIST = "artist"
    GENERAL = "general"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class TagInfo:
    tag: str
    category_path: tuple[str, ...] = ()
    post_count: int | None = None
    source: str = "general"


@dataclass(frozen=True)
class TagToken:
    raw: str
    normalized: str
    lookup_key: str
    text: str
    known: bool = False
    section: TagSection = TagSection.UNKNOWN
    category_path: tuple[str, ...] = ()
    source: str | None = None


@dataclass(frozen=True)
class ParsedPrompt:
    text: str
    tokens: tuple[str, ...]
    delimiter: str
    profile: str


@dataclass(frozen=True)
class CorrectionResult:
    text: str
    original_text: str
    tokens: tuple[TagToken, ...]
    unknown_tags: tuple[str, ...] = ()
    duplicate_tags: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    changed: bool = False
    report: dict[str, object] = field(default_factory=dict)
