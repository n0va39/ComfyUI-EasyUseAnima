"""Compatibility exports for :mod:`easyuse_anima.prompt.anima.correction`."""

try:
    from ..easyuse_anima.prompt.anima.correction import (
        PromptSyntax,
        correct_prompt,
        inspect_prompt,
    )
except ImportError:
    from easyuse_anima.prompt.anima.correction import (
        PromptSyntax,
        correct_prompt,
        inspect_prompt,
    )

__all__ = ["PromptSyntax", "correct_prompt", "inspect_prompt"]
