"""Minimal prompt knowledge loading for ANIMA prompt correction."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .models import TagInfo
from .normalize import lookup_key
from .ordering import ANIMA_PERSON_COUNT_TAGS

PACKAGE_DATA_DIR = Path(__file__).resolve().parents[1] / "__easyuse_anima__"


class KnowledgeBaseNotFound(FileNotFoundError):
    """Compatibility exception for older callers."""


@dataclass
class PromptKnowledgeBase:
    @classmethod
    def empty(cls) -> "PromptKnowledgeBase":
        return cls()

    def lookup(self, tag: str) -> TagInfo | None:
        key = lookup_key(tag)
        if key in ANIMA_PERSON_COUNT_TAGS:
            return TagInfo(tag=key, category_path=("인물", "인원수"), source="anima_builtin")
        return None


def load_knowledge_base(*, allow_missing: bool = False, **_ignored) -> PromptKnowledgeBase:
    """Return built-in ANIMA prompt knowledge.

    Extra keyword arguments are accepted for compatibility with older workflows
    or scripts.
    """

    return PromptKnowledgeBase.empty()
