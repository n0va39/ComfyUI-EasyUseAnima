"""Compatibility exports for :mod:`easyuse_anima.prompt.anima.knowledge`."""

try:
    from ..easyuse_anima.prompt.anima.knowledge import (
        PACKAGE_DATA_DIR,
        KnowledgeBaseNotFound,
        PromptKnowledgeBase,
        load_knowledge_base,
    )
except ImportError:
    from easyuse_anima.prompt.anima.knowledge import (
        PACKAGE_DATA_DIR,
        KnowledgeBaseNotFound,
        PromptKnowledgeBase,
        load_knowledge_base,
    )

__all__ = [
    "PACKAGE_DATA_DIR",
    "KnowledgeBaseNotFound",
    "PromptKnowledgeBase",
    "load_knowledge_base",
]
