"""Copyable third-party AiO hook example for ComfyUI-EasyUseAnima."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

# A sibling custom node can be imported before ComfyUI-EasyUseAnima. Keep the
# socket identifier local and import the public Python API only when this node
# executes, after all custom nodes have finished loading.
EASYUSE_ANIMA_AIO_HOOK_TYPE = "EASYUSE_ANIMA_AIO_HOOK"


@lru_cache(maxsize=1)
def _definition_type():
    from easyuse_anima.extensions.aio import (
        AIO_HOOK_API_VERSION,
        AioHookDescriptor,
        AioHookPatch,
        AioHookPoint,
        AioHookSessionBase,
        AioStage,
        AioStagePhase,
    )

    after_postprocess = frozenset({
        AioHookPoint(AioStage.POSTPROCESS, AioStagePhase.AFTER)
    })

    class _BrightnessSession(AioHookSessionBase):
        def __init__(self, context, strength: float, emit_preview: bool) -> None:
            self._services = context.services
            self._strength = strength
            self._emit_preview = emit_preview
            self._closed = False

        def after_stage(self, event):
            if self._closed:
                raise RuntimeError("brightness hook session is already closed")
            image = event.state.image.mul(self._strength).clamp(0.0, 1.0)
            if self._emit_preview:
                self._services.emit_preview(event.stage, image, "brightness")
            return AioHookPatch(
                image=image,
                metadata={
                    "strength": self._strength,
                    "preview_emitted": self._emit_preview,
                },
            )

        def close(self) -> None:
            self._closed = True

    @dataclass(frozen=True, slots=True)
    class _BrightnessDefinition:
        strength: float
        emit_preview: bool

        def describe(self):
            return AioHookDescriptor(
                hook_id="example.brightness",
                hook_version="1.0.0",
                api_version=AIO_HOOK_API_VERSION,
                points=after_postprocess,
                fingerprint={
                    "strength": self.strength,
                    "emit_preview": self.emit_preview,
                    "algorithm": "multiply-clamp-v1",
                },
            )

        def create_session(self, context):
            return _BrightnessSession(context, self.strength, self.emit_preview)

    return _BrightnessDefinition


class ExampleEasyUseAnimaBrightnessHook:
    DESCRIPTION = (
        "Example AiO hook that multiplies the final image without changing shape."
    )

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "strength": (
                    "FLOAT",
                    {"default": 1.0, "min": 0.0, "max": 2.0, "step": 0.01},
                ),
                "emit_preview": ("BOOLEAN", {"default": False}),
            }
        }

    RETURN_TYPES = (EASYUSE_ANIMA_AIO_HOOK_TYPE,)
    RETURN_NAMES = ("aio_hook",)
    FUNCTION = "build"
    CATEGORY = "Example/EasyUse Anima"

    def build(self, strength, emit_preview):
        definition_type = _definition_type()
        return (definition_type(float(strength), bool(emit_preview)),)


NODE_CLASS_MAPPINGS = {
    "ExampleEasyUseAnimaBrightnessHook": ExampleEasyUseAnimaBrightnessHook,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ExampleEasyUseAnimaBrightnessHook": "Example AiO Brightness Hook",
}

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"]
