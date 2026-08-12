"""LoRA-stack Prompt Studio node adapters."""

from __future__ import annotations

from ..common.serialization import _stable_change_key
from ..lora.prompt_syntax import (
    _extract_a1111_loras_from_fields,
    _lora_stack_signature,
    _merge_lora_stack,
    _resolve_a1111_lora_directives,
)
from .input_types import _FlexibleOptionalInputType
from .prompt_advanced_nodes import EasyUseAnimaPromptStudioAdvanced


class EasyUseAnimaPromptStudioAdvancedLora(EasyUseAnimaPromptStudioAdvanced):
    """Advanced Prompt Studio with A1111 LoRA extraction and stack output."""

    DESCRIPTION = (
        "Advanced Prompt Studio with the same editor and execution lifecycle, plus "
        "A1111/LoraManager <lora:name:model[:clip]> extraction and an appended "
        "LORA_STACK output."
    )
    OUTPUT_TOOLTIPS = (
        *EasyUseAnimaPromptStudioAdvanced.OUTPUT_TOOLTIPS,
        "Input LoRA stack followed by LoRAs extracted from enabled positive fields.",
    )
    RETURN_TYPES = (*EasyUseAnimaPromptStudioAdvanced.RETURN_TYPES, "LORA_STACK")
    RETURN_NAMES = (*EasyUseAnimaPromptStudioAdvanced.RETURN_NAMES, "LORA_STACK")

    @classmethod
    def INPUT_TYPES(cls):
        base = EasyUseAnimaPromptStudioAdvanced.INPUT_TYPES()
        return {
            **base,
            "optional": _FlexibleOptionalInputType(
                "STRING",
                {
                    "lora_stack": (
                        "LORA_STACK",
                        {
                            "forceInput": True,
                            "tooltip": (
                                "Optional LoRA stack. Prompt-tag LoRAs are appended in "
                                "positive-field order."
                            ),
                        },
                    ),
                },
            ),
        }

    @staticmethod
    def _transform_effective_fields(fields):
        return _extract_a1111_loras_from_fields(fields)

    @classmethod
    def IS_CHANGED(cls, lora_stack=None, **kwargs):
        base_key = EasyUseAnimaPromptStudioAdvanced.IS_CHANGED(**kwargs)
        if base_key != base_key:
            return base_key
        return _stable_change_key(
            {
                "base": base_key,
                "lora_stack": _lora_stack_signature(lora_stack),
            }
        )

    def build(self, *args, lora_stack=None, **kwargs):
        output = super().build(*args, **kwargs)
        directives = output.pop("_transform_result", [])
        prompt_stack = _resolve_a1111_lora_directives(directives)
        output["result"] = (
            *tuple(output.get("result") or ()),
            _merge_lora_stack(lora_stack, prompt_stack),
        )
        return output


__all__ = ("EasyUseAnimaPromptStudioAdvancedLora",)
