"""ANIMA tag classification and ordering rules."""

from __future__ import annotations

import re

from .models import TagInfo, TagSection
from .normalize import lookup_key

QUALITY_TAGS = frozenset(
    {
        "masterpiece",
        "best quality",
        "great quality",
        "good quality",
        "high quality",
        "normal quality",
        "average quality",
        "low quality",
        "bad quality",
        "worst quality",
        "high score",
        "great score",
        "good score",
        "average score",
        "bad score",
        "low score",
        "score_9",
        "score_8",
        "score_7",
        "score_7:",
        "score_6",
        "score_5",
        "score_4",
        "very aesthetic",
        "aesthetic",
        "displeasing",
        "very displeasing",
    }
)
META_TAGS = frozenset(
    {
        "highres",
        "absurdres",
        "lowres",
        "official art",
        "scan",
        "source anime",
        "source pony",
        "source furry",
        "source cartoon",
    }
)
YEAR_TAGS = frozenset(
    {
        "oldest",
        "old",
        "early",
        "mid",
        "recent",
        "newest",
    }
)
SAFETY_TAGS = frozenset(
    {
        "safe",
        "sensitive",
        "nsfw",
        "questionable",
        "explicit",
        "rating safe",
        "rating questionable",
        "rating explicit",
    }
)
YEAR_TAG_PATTERN = re.compile(r"^year\s+\d+$")

ANIMA_PERSON_COUNT_TAGS = frozenset(
    {
        "solo",
        "no humans",
        "multiple boys",
        "multiple girls",
        "multiple others",
        "1boy",
        "2boys",
        "3boys",
        "4boys",
        "5boys",
        "6+boys",
        "1girl",
        "2girls",
        "3girls",
        "4girls",
        "5girls",
        "6+girls",
        "1other",
        "2others",
        "3others",
        "4others",
        "5others",
        "6+others",
    }
)

SECTION_ORDER = {
    TagSection.QUALITY: 0,
    TagSection.META: 1,
    TagSection.YEAR: 2,
    TagSection.SAFETY: 3,
    TagSection.COUNT: 4,
    TagSection.CHARACTER: 5,
    TagSection.COPYRIGHT: 6,
    TagSection.ARTIST: 7,
    TagSection.GENERAL: 8,
    TagSection.UNKNOWN: 8,
}

BUILTIN_TAG_SECTIONS = {
    **{tag: TagSection.QUALITY for tag in QUALITY_TAGS},
    **{tag: TagSection.META for tag in META_TAGS},
    **{tag: TagSection.YEAR for tag in YEAR_TAGS},
    **{tag: TagSection.SAFETY for tag in SAFETY_TAGS},
    **{tag: TagSection.COUNT for tag in ANIMA_PERSON_COUNT_TAGS},
}


def builtin_tag_section(tag: str) -> TagSection | None:
    key = lookup_key(tag)
    if key in BUILTIN_TAG_SECTIONS:
        return BUILTIN_TAG_SECTIONS[key]
    if YEAR_TAG_PATTERN.match(key):
        return TagSection.YEAR
    return None


def classify_tag(tag: str, info: TagInfo | None = None) -> TagSection:
    section = builtin_tag_section(tag)
    if section is not None:
        return section
    if tag.strip().startswith("@"):
        return TagSection.ARTIST

    category_path = info.category_path if info else ()
    root = category_path[0] if category_path else ""
    if root == "캐릭터":
        return TagSection.CHARACTER
    if root in {"작품", "미디어"}:
        return TagSection.COPYRIGHT
    if root == "작가":
        return TagSection.ARTIST
    if root == "인물" and any(part == "인원수" for part in category_path):
        return TagSection.COUNT
    return TagSection.GENERAL if info is not None else TagSection.UNKNOWN


def section_sort_key(index: int, section: TagSection) -> tuple[int, int]:
    return (SECTION_ORDER.get(section, SECTION_ORDER[TagSection.UNKNOWN]), index)
