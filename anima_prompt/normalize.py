"""Compatibility exports for :mod:`easyuse_anima.prompt.anima.normalize`."""

try:
    from ..easyuse_anima.prompt.anima.normalize import (
        lookup_key,
        normalize_tag,
        render_artist_tag,
    )
except ImportError:
    from easyuse_anima.prompt.anima.normalize import (
        lookup_key,
        normalize_tag,
        render_artist_tag,
    )

__all__ = ["lookup_key", "normalize_tag", "render_artist_tag"]
