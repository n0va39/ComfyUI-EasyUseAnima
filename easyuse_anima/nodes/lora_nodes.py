"""ComfyUI adapter for LoRA preset profiles and metadata services."""

from __future__ import annotations

import os

from ..common.serialization import _stable_change_key
from ..common.values import _as_bool
from ..lora.metadata import (
    _apply_lora_syntax_format,
    _get_lora_info,
    _lora_combo_values,
    _lora_model_exists,
    _lora_stack_name,
    _missing_lora_display_name,
    _raise_missing_loras,
)
from ..lora.preset import _correct_style_prompt, _format_strength, _select_profile_values


class _AnyType(str):
    def __ne__(self, __value: object) -> bool:
        return False


class _FlexibleOptionalInputType(dict):
    def __init__(self, input_type):
        self.input_type = input_type

    def __getitem__(self, key):
        return (self.input_type,)

    def __contains__(self, key):
        return True


_ANY_TYPE = _AnyType("*")


def _bind_lora_node_runtime(*, resolve_helper, flexible_optional_input_type, any_type) -> None:
    global _as_bool, _stable_change_key
    global _apply_lora_syntax_format, _get_lora_info, _lora_combo_values
    global _lora_model_exists, _lora_stack_name, _missing_lora_display_name
    global _raise_missing_loras, _correct_style_prompt, _format_strength
    global _select_profile_values, _FlexibleOptionalInputType, _ANY_TYPE

    def runtime_helper(name):
        def call(*args, **kwargs):
            return resolve_helper(name)(*args, **kwargs)

        return call

    _as_bool = runtime_helper("_as_bool")
    _stable_change_key = runtime_helper("_stable_change_key")
    _apply_lora_syntax_format = runtime_helper("_apply_lora_syntax_format")
    _get_lora_info = runtime_helper("_get_lora_info")
    _lora_combo_values = runtime_helper("_lora_combo_values")
    _lora_model_exists = runtime_helper("_lora_model_exists")
    _lora_stack_name = runtime_helper("_lora_stack_name")
    _missing_lora_display_name = runtime_helper("_missing_lora_display_name")
    _raise_missing_loras = runtime_helper("_raise_missing_loras")
    _correct_style_prompt = runtime_helper("_correct_style_prompt")
    _format_strength = runtime_helper("_format_strength")
    _select_profile_values = runtime_helper("_select_profile_values")
    _FlexibleOptionalInputType = flexible_optional_input_type
    _ANY_TYPE = any_type


class EasyUseAnimaLoraPreset:
    """Multi-profile LoRA stack preset node for ANIMA style prompts."""

    DESCRIPTION = (
        "Stores multiple ANIMA LoRA preset profiles, builds a LoRA stack, emits trigger words, "
        "and preserves profile data in workflow metadata."
    )
    OUTPUT_TOOLTIPS = (
        "Corrected style prompt for artist tags, model triggers, or short style directions.",
        "LoRA stack compatible with LoRA stack loaders.",
        "Trigger words collected from selected LoRA metadata.",
        "Text representation of enabled LoRAs and strengths.",
        "Currently selected profile index after wrapping to the available profile count.",
    )

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "style_prompt": ("STRING", {
                    "multiline": True,
                    "default": "",
                    "tooltip": "Style prompt for artist tags, model triggers, or short style directions.",
                }),
                "profile_index": ("INT", {
                    "default": 1,
                    "min": 1,
                    "max": 16,
                    "step": 1,
                    "tooltip": "Selected LoRA preset profile. Can be connected from another node.",
                }),
                "profile_count": ("STRING", {
                    "default": "4",
                    "tooltip": "Internal profile count managed by the front-end profile buttons.",
                }),
                "lora_name": (_lora_combo_values(), {
                    "default": "None",
                    "tooltip": "Internal LoRA selector source. Hidden by the EasyUse Anima front-end.",
                }),
                "loras": ("STRING", {
                    "multiline": True,
                    "default": "[]",
                    "tooltip": "Internal serialized LoRA rows for the selected profile.",
                }),
                "profile_data": ("STRING", {
                    "multiline": True,
                    "default": "{}",
                    "tooltip": "Internal serialized profile data.",
                }),
            },
            "optional": _FlexibleOptionalInputType(_ANY_TYPE),
        }

    RETURN_TYPES = ("STRING", "LORA_STACK", "STRING", "STRING", "INT")
    RETURN_NAMES = ("style_prompt", "LORA_STACK", "trigger_words", "active_loras", "profile_index")
    FUNCTION = "build"
    CATEGORY = "EasyUse Anima/LoRA"

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        return _stable_change_key({
            "mode": "lora_preset",
            **{key: str(value) for key, value in sorted(kwargs.items())},
        })

    def build(
        self,
        style_prompt: str,
        profile_index: int,
        profile_count=4,
        lora_name: str = "None",
        loras="[]",
        profile_data: str = "{}",
        **kwargs,
    ):
        kwargs = dict(kwargs)
        if loras is not None:
            kwargs["loras"] = loras

        selected_style, selected_loras, selected_index = _select_profile_values(
            profile_index,
            profile_count,
            profile_data,
            style_prompt,
            kwargs,
        )
        corrected_style = _correct_style_prompt(selected_style)

        stack = []
        trigger_words: list[str] = []
        active_loras: list[tuple[str, float, float]] = []

        lora_stack = kwargs.get("lora_stack")
        if lora_stack:
            stack.extend(lora_stack)
            for lora_path, _model_strength, _clip_strength in lora_stack:
                lora_base = os.path.splitext(os.path.basename(str(lora_path).replace("\\", "/")))[0]
                _path, existing_trigger_words = _get_lora_info(lora_base)
                trigger_words.extend(existing_trigger_words)

        seen: set[tuple[str, float, float]] = set()
        missing_loras: list[str] = []
        for lora in selected_loras:
            enabled_value = lora.get("on", lora.get("active", True))
            if not _as_bool(enabled_value, True):
                continue
            raw_name = str(lora.get("name", lora.get("lora", ""))).strip()
            if not raw_name or raw_name == "None":
                continue
            lora_name = raw_name.replace("\\", "/")
            active_lora_name = _apply_lora_syntax_format(lora_name)
            try:
                model_strength = float(lora.get("strength", 1.0))
            except (TypeError, ValueError):
                model_strength = 1.0
            clip_raw = lora.get("strengthTwo", lora.get("clipStrength", model_strength))
            try:
                clip_strength = float(clip_raw if clip_raw is not None else model_strength)
            except (TypeError, ValueError):
                clip_strength = model_strength

            stack_lora_name = _lora_stack_name(lora_name)
            dedupe_key = (stack_lora_name, model_strength, clip_strength)
            if dedupe_key in seen:
                continue
            seen.add(dedupe_key)

            if _lora_model_exists(stack_lora_name) is False:
                missing_loras.append(_missing_lora_display_name(raw_name, stack_lora_name))
                continue

            _lora_path, lora_trigger_words = _get_lora_info(lora_name)
            stack.append((stack_lora_name, model_strength, clip_strength))
            trigger_words.extend(lora_trigger_words)
            active_loras.append((active_lora_name, model_strength, clip_strength))

        _raise_missing_loras(selected_index, missing_loras)

        active_loras_text_parts = []
        for name, model_strength, clip_strength in active_loras:
            model_text = _format_strength(model_strength)
            clip_text = _format_strength(clip_strength)
            if abs(model_strength - clip_strength) > 0.001:
                active_loras_text_parts.append(f"<lora:{name}:{model_text}:{clip_text}>")
            else:
                active_loras_text_parts.append(f"<lora:{name}:{model_text}>")

        return {
            "ui": {
                "lora_preset_profile": [{
                    "profile_index": selected_index,
                }],
            },
            "result": (
                corrected_style,
                stack,
                ", ".join(trigger_words) if trigger_words else "",
                " ".join(active_loras_text_parts),
                selected_index,
            ),
        }


__all__ = ("EasyUseAnimaLoraPreset",)
