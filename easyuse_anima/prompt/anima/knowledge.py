"""Minimal prompt knowledge loading for ANIMA prompt correction."""

from __future__ import annotations

from dataclasses import dataclass

from ...errors import NotFoundError
from ...infrastructure.filesystem.paths import PACKAGE_DATA_DIR
from .models import TagInfo
from .normalize import lookup_key
from .ordering import TagSection, builtin_tag_section


class KnowledgeBaseNotFound(NotFoundError, FileNotFoundError):
    """Compatibility exception for older callers."""


@dataclass
class PromptKnowledgeBase:
    @classmethod
    def empty(cls) -> "PromptKnowledgeBase":
        return cls()

    def lookup(self, tag: str) -> TagInfo | None:
        key = lookup_key(tag)
        section = builtin_tag_section(key)
        if section is TagSection.COUNT:
            return TagInfo(tag=key, category_path=("인물", "인원수"), source="anima_builtin")
        if section is TagSection.QUALITY:
            return TagInfo(tag=key, category_path=("품질",), source="anima_builtin")
        if section is TagSection.META:
            return TagInfo(tag=key, category_path=("메타",), source="anima_builtin")
        if section is TagSection.YEAR:
            return TagInfo(tag=key, category_path=("연도",), source="anima_builtin")
        if section is TagSection.SAFETY:
            return TagInfo(tag=key, category_path=("등급",), source="anima_builtin")
        return None


def load_knowledge_base(*, allow_missing: bool = False, **_ignored) -> PromptKnowledgeBase:
    """Return built-in ANIMA prompt knowledge.

    Extra keyword arguments are accepted for compatibility with older workflows
    or scripts.
    """

    return PromptKnowledgeBase.empty()
