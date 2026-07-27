"""Compatibility exports for :mod:`easyuse_anima.prompt.anima.parser`."""

try:
    from ..easyuse_anima.prompt.anima.parser import parse_prompt, render_tags
except ImportError:
    from easyuse_anima.prompt.anima.parser import parse_prompt, render_tags

__all__ = ["parse_prompt", "render_tags"]
