"""Compatibility exports for :mod:`easyuse_anima.prompt.anima.ordering`."""

try:
    from ..easyuse_anima.prompt.anima.ordering import (
        ANIMA_PERSON_COUNT_TAGS,
        BUILTIN_TAG_SECTIONS,
        META_TAGS,
        QUALITY_TAGS,
        SAFETY_TAGS,
        SECTION_ORDER,
        YEAR_TAG_PATTERN,
        YEAR_TAGS,
        builtin_tag_section,
        classify_tag,
        section_sort_key,
    )
except ImportError:
    from easyuse_anima.prompt.anima.ordering import (
        ANIMA_PERSON_COUNT_TAGS,
        BUILTIN_TAG_SECTIONS,
        META_TAGS,
        QUALITY_TAGS,
        SAFETY_TAGS,
        SECTION_ORDER,
        YEAR_TAG_PATTERN,
        YEAR_TAGS,
        builtin_tag_section,
        classify_tag,
        section_sort_key,
    )

__all__ = [
    "ANIMA_PERSON_COUNT_TAGS",
    "BUILTIN_TAG_SECTIONS",
    "META_TAGS",
    "QUALITY_TAGS",
    "SAFETY_TAGS",
    "SECTION_ORDER",
    "YEAR_TAG_PATTERN",
    "YEAR_TAGS",
    "builtin_tag_section",
    "classify_tag",
    "section_sort_key",
]
