"""ComfyUI adapter for wildcard expansion."""

from __future__ import annotations

from ..common.serialization import _stable_change_key
from ..common.values import _single_value
from ..lora.prompt_syntax import (
    _lora_stack_signature,
    _merge_lora_stack,
    _parse_a1111_lora_tags,
    _resolve_a1111_lora_directives,
)
from ..wildcard.mode import (
    WILDCARD_MODE_FIXED,
    WILDCARD_MODE_LABELS,
    WILDCARD_MODE_POPULATE,
    WILDCARD_MODE_REPRODUCE,
    WILDCARD_MODE_SEQUENTIAL,
    normalize_wildcard_mode,
)
from ..wildcard.seed import MAX_SEED, PUBLIC_MAX_SEED, normalize_seed
from ..wildcard.service import expand_wildcards, wildcard_sources_signature
from ..workflow import _get_workflow_node
from .input_types import _FlexibleOptionalInputType

WILDCARD_SEED_RANGE_NOTE = (
    f"Browser/public editing and next-seed range: 0..{PUBLIC_MAX_SEED}. The Python "
    "backend continues accepting uint64 values for legacy workflow validation, but "
    "values above the public maximum are best-effort in the browser because JavaScript "
    "may already have lost integer precision. ComfyUI's native seed control owns any "
    "post-queue randomize, increment, or decrement behavior."
)
WILDCARD_MODE_DISPLAY_LABELS = {
    WILDCARD_MODE_POPULATE: WILDCARD_MODE_LABELS[0],
    WILDCARD_MODE_FIXED: WILDCARD_MODE_LABELS[1],
    WILDCARD_MODE_SEQUENTIAL: WILDCARD_MODE_LABELS[2],
    WILDCARD_MODE_REPRODUCE: WILDCARD_MODE_LABELS[3],
}


class EasyUseAnimaWildcard:
    """Expand Impact Pack compatible wildcard and dynamic prompt syntax."""

    DESCRIPTION = (
        "Expands EasyUse Anima wildcard files and dynamic prompt syntax with Impact Pack "
        "compatible populated_text lifecycle plus deterministic Sequential selection."
    )
    OUTPUT_TOOLTIPS = (
        "Expanded prompt text.",
        "Seed used for this expansion.",
    )

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "text": ("STRING", {
                    "multiline": True,
                    "default": "",
                    "tooltip": (
                        "Source prompt expanded by General and Sequential modes. Syntax: "
                        "__name__; {a|b|c}; weighted N::item; {n$$...} or "
                        "{min-max$$separator$$...}; N#__name__; and nested combinations. Wildcard "
                        "names ignore case and support * glob collections. Only lines whose first "
                        "non-space character is # are removed as comments."
                    ),
                }),
                "populated_text": ("STRING", {
                    "multiline": True,
                    "default": "",
                    "tooltip": (
                        "Expanded-result cache used like Impact Pack's populated_text. General "
                        "and Sequential replace it from text; Fixed and Reproduce ignore text and "
                        "process this value with the same wildcard engine, including file wildcards."
                    ),
                }),
                "mode": (WILDCARD_MODE_LABELS, {
                    "default": WILDCARD_MODE_LABELS[0],
                    "tooltip": (
                        "General (일반): expand text with deterministic seed-based choices and cache "
                        "the result in populated_text. Fixed (고정): ignore text and process "
                        "populated_text with the same wildcard engine. Sequential (순차): expand text "
                        "with seed modulo each option count. Reproduce (재현): process populated_text "
                        "once, then return the live and saved mode to General like Impact Pack."
                    ),
                }),
                "seed": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": MAX_SEED,
                    "control_after_generate": True,
                    "tooltip": (
                        "Seed for deterministic weighted random selection. The same text and seed "
                        "produce the same result. "
                        f"{WILDCARD_SEED_RANGE_NOTE}"
                    ),
                }),
            },
            "hidden": {
                "workflow_prompt": "PROMPT",
                "extra_pnginfo": "EXTRA_PNGINFO",
                "unique_id": "UNIQUE_ID",
            },
            "optional": _FlexibleOptionalInputType("STRING"),
        }

    RETURN_TYPES = ("STRING", "INT")
    RETURN_NAMES = ("text", "seed")
    FUNCTION = "generate"
    CATEGORY = "EasyUse Anima/Prompt"

    @classmethod
    def _widget_input_names(cls):
        return tuple(cls.INPUT_TYPES().get("required", {}).keys())

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        return _stable_change_key({
            "mode": "wildcard",
            "wildcard_sources": wildcard_sources_signature(),
            **{key: str(value) for key, value in sorted(kwargs.items())},
        })

    @classmethod
    def _update_metadata_cache(
        cls,
        workflow_prompt,
        extra_pnginfo,
        unique_id,
        populated_text: str,
        mode: str,
        seed: int,
    ) -> None:
        node_id = _single_value(unique_id)
        if node_id is None:
            return
        node_id = str(node_id)
        updates = {
            "populated_text": populated_text,
            "mode": mode,
            "seed": int(seed),
        }

        if isinstance(workflow_prompt, dict):
            prompt_node = workflow_prompt.get(node_id)
            if isinstance(prompt_node, dict):
                inputs = prompt_node.setdefault("inputs", {})
                for name, value in updates.items():
                    inputs[name] = value

        workflow_node = _get_workflow_node(extra_pnginfo, node_id)
        if workflow_node is None:
            return

        input_names = cls._widget_input_names()
        widgets_values = workflow_node.setdefault("widgets_values", [])
        for name, value in updates.items():
            if name not in input_names:
                continue
            index = input_names.index(name)
            while len(widgets_values) <= index:
                widgets_values.append(None)
            widgets_values[index] = value
        native_seed_control_index = len(input_names)
        if len(widgets_values) > native_seed_control_index:
            widgets_values[native_seed_control_index] = "fixed"

    @staticmethod
    def _ui(
        populated_text: str,
        mode: str,
        seed: int,
        status: str,
        used_keys: tuple[str, ...],
        missing_keys: tuple[str, ...],
    ):
        return {
            "wildcard": [{
                "populated_text": populated_text,
                "mode": mode,
                "seed": seed,
                "status": status,
                "used_keys": list(used_keys),
                "missing_keys": list(missing_keys),
            }]
        }

    @staticmethod
    def _transform_output_text(text: str):
        return text, None

    def generate(
        self,
        text: str,
        populated_text: str,
        mode: str,
        seed: int,
        workflow_prompt=None,
        extra_pnginfo=None,
        unique_id=None,
        **reservation_inputs,
    ):
        mode_key = normalize_wildcard_mode(mode)
        seed_value = normalize_seed(seed)
        used_keys: tuple[str, ...] = ()
        missing_keys: tuple[str, ...] = ()

        source_text = (
            populated_text
            if mode_key in {WILDCARD_MODE_FIXED, WILDCARD_MODE_REPRODUCE}
            else text
        )
        expansion = expand_wildcards(str(source_text or ""), seed=seed_value, mode=mode_key)
        populated_output_text = expansion.text
        output_text, transform_result = self._transform_output_text(
            populated_output_text
        )
        used_keys = expansion.used_keys
        missing_keys = expansion.missing_keys
        status = mode_key
        next_mode_key = (
            WILDCARD_MODE_POPULATE
            if mode_key == WILDCARD_MODE_REPRODUCE
            else mode_key
        )
        next_mode_label = WILDCARD_MODE_DISPLAY_LABELS[next_mode_key]
        self._update_metadata_cache(
            workflow_prompt,
            extra_pnginfo,
            unique_id,
            populated_output_text,
            next_mode_label,
            seed_value,
        )
        output = {
            "ui": self._ui(
                populated_output_text,
                next_mode_label,
                seed_value,
                status,
                used_keys,
                missing_keys,
            ),
            "result": (output_text, seed_value),
        }
        if transform_result is not None:
            output["_transform_result"] = transform_result
        return output


class EasyUseAnimaWildcardLora(EasyUseAnimaWildcard):
    """Wildcard expansion with A1111 LoRA tag extraction and stack output."""

    DESCRIPTION = (
        "Anima Wildcard with the same populated_text lifecycle, plus A1111 "
        "and LoraManager <lora:name:model[:clip]> extraction and an appended "
        "LORA_STACK output."
    )
    OUTPUT_TOOLTIPS = (
        *EasyUseAnimaWildcard.OUTPUT_TOOLTIPS,
        "Input LoRA stack followed by LoRAs extracted after wildcard expansion.",
    )
    RETURN_TYPES = (*EasyUseAnimaWildcard.RETURN_TYPES, "LORA_STACK")
    RETURN_NAMES = (*EasyUseAnimaWildcard.RETURN_NAMES, "LORA_STACK")

    @classmethod
    def INPUT_TYPES(cls):
        base = EasyUseAnimaWildcard.INPUT_TYPES()
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
                                "Optional LoRA stack. Wildcard-expanded prompt LoRAs "
                                "are appended in prompt order."
                            ),
                        },
                    ),
                },
            ),
        }

    @staticmethod
    def _transform_output_text(text: str):
        return _parse_a1111_lora_tags(text)

    @classmethod
    def IS_CHANGED(cls, lora_stack=None, **kwargs):
        return _stable_change_key(
            {
                "base": EasyUseAnimaWildcard.IS_CHANGED(**kwargs),
                "lora_stack": _lora_stack_signature(lora_stack),
            }
        )

    def generate(self, *args, lora_stack=None, **kwargs):
        output = super().generate(*args, **kwargs)
        directives = output.pop("_transform_result", [])
        prompt_stack = _resolve_a1111_lora_directives(directives)
        output["result"] = (
            *tuple(output.get("result") or ()),
            _merge_lora_stack(lora_stack, prompt_stack),
        )
        return output

__all__ = ("EasyUseAnimaWildcard", "EasyUseAnimaWildcardLora")
