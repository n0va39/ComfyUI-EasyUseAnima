"""ComfyUI adapters for composing public AiO hook definitions."""

from __future__ import annotations

from ..aio.hooks import (
    EASYUSE_ANIMA_AIO_HOOK_TYPE,
    combine_aio_hooks,
)


class EasyUseAnimaAIOHookCombine:
    """Compose explicitly connected AiO hook definitions in socket order."""

    DESCRIPTION = (
        "Combines AiO hook definitions. Before callbacks run from hook_a to hook_d; "
        "after callbacks and cleanup run in reverse order."
    )
    OUTPUT_TOOLTIPS = (
        "Combined EASYUSE_ANIMA_AIO_HOOK value for Anima AiO Generator.",
    )

    @classmethod
    def INPUT_TYPES(cls):
        socket = (
            EASYUSE_ANIMA_AIO_HOOK_TYPE,
            {"forceInput": True},
        )
        return {
            "required": {"hook_a": socket, "hook_b": socket},
            "optional": {"hook_c": socket, "hook_d": socket},
        }

    RETURN_TYPES = (EASYUSE_ANIMA_AIO_HOOK_TYPE,)
    RETURN_NAMES = ("aio_hook",)
    FUNCTION = "combine"
    CATEGORY = "EasyUse Anima/AiO/Extensions"

    def combine(self, hook_a, hook_b, hook_c=None, hook_d=None):
        return (combine_aio_hooks(hook_a, hook_b, hook_c, hook_d),)


__all__ = ("EasyUseAnimaAIOHookCombine",)
