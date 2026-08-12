"""ComfyUI adapters for the isolated Anima 2.9B compatibility feature."""

from __future__ import annotations

from ..anima_29b.lora import (
    ANIMA_29B_LORA_LAYOUT_LEGACY,
    _apply_anima_29b_lora_stack,
)
from ..lora.prompt_syntax import _normalize_lora_stack


class EasyUseAnima29BLoraStackLoader:
    """Apply legacy 28-block Anima LoRAs to an Anima 2.9B model patcher."""

    DESCRIPTION = (
        "Experimentally remaps a regular 28-block Anima LoRA stack onto the 28 "
        "inherited block positions of Anima 2.9B. Results can differ from the "
        "original model; native 2.9B LoRA training is recommended."
    )
    OUTPUT_TOOLTIPS = (
        "Anima 2.9B model with the experimental legacy LoRA remap applied.",
        "CLIP model with any text-encoder LoRA patches applied.",
    )

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "model": (
                    "MODEL",
                    {
                        "tooltip": "A 40-block Anima 2.9B diffusion model loaded by Easy Use Anima."
                    },
                ),
                "clip": (
                    "CLIP",
                    {"tooltip": "The CLIP model paired with the Anima model."},
                ),
                "lora_stack": (
                    "LORA_STACK",
                    {
                        "tooltip": "A regular 28-block Anima LoRA stack to remap experimentally and apply in order."
                    },
                ),
            }
        }

    RETURN_TYPES = ("MODEL", "CLIP")
    RETURN_NAMES = ("model", "clip")
    FUNCTION = "apply"
    CATEGORY = "EasyUse Anima/LoRA"

    def apply(self, model, clip, lora_stack):
        patched_model, patched_clip, _applied = _apply_anima_29b_lora_stack(
            model,
            clip,
            _normalize_lora_stack(lora_stack),
            source_layout=ANIMA_29B_LORA_LAYOUT_LEGACY,
        )
        return patched_model, patched_clip


__all__ = ("EasyUseAnima29BLoraStackLoader",)
