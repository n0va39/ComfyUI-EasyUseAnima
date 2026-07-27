"""Compatibility exports for :mod:`easyuse_anima.prompt.anima.models`."""

try:
    from ..easyuse_anima.prompt.anima.models import (
        CorrectionResult,
        ParsedPrompt,
        TagInfo,
        TagSection,
        TagToken,
    )
except ImportError:
    from easyuse_anima.prompt.anima.models import (
        CorrectionResult,
        ParsedPrompt,
        TagInfo,
        TagSection,
        TagToken,
    )

__all__ = [
    "CorrectionResult",
    "ParsedPrompt",
    "TagInfo",
    "TagSection",
    "TagToken",
]
