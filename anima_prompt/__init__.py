"""Compatibility exports for the canonical ANIMA prompt core."""

try:
    from ..easyuse_anima.prompt.anima import (
        CorrectionResult,
        KnowledgeBaseNotFound,
        ParsedPrompt,
        PromptKnowledgeBase,
        TagInfo,
        TagToken,
        correct_prompt,
        inspect_prompt,
        load_knowledge_base,
    )
except ImportError:
    from easyuse_anima.prompt.anima import (
        CorrectionResult,
        KnowledgeBaseNotFound,
        ParsedPrompt,
        PromptKnowledgeBase,
        TagInfo,
        TagToken,
        correct_prompt,
        inspect_prompt,
        load_knowledge_base,
    )

__all__ = [
    "CorrectionResult",
    "KnowledgeBaseNotFound",
    "ParsedPrompt",
    "PromptKnowledgeBase",
    "TagInfo",
    "TagToken",
    "correct_prompt",
    "inspect_prompt",
    "load_knowledge_base",
]
