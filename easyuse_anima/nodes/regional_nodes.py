"""ComfyUI adapters for Regional Prompt Studio."""

from __future__ import annotations

from typing import Any

from ..common.serialization import _stable_change_key
from ..common.values import _as_float, _single_value
from ..infrastructure.comfy.wiring import resolve_comfy_host_helper
from ..naia.resolution import (
    DEFAULT_ADVANCED_RESOLUTION_BUCKET,
    DEFAULT_ADVANCED_RESOLUTION_SIZE,
    _advanced_resolution_from_selection,
)
from ..prompt.advanced import (
    _advanced_field_input_values,
    _expand_advanced_wildcard_fields,
    _normalize_prompt_studio_wildcard_seed_control,
    _translate_prompt_fields,
    normalize_prompt_studio_wildcard_mode,
    normalize_seed,
)
from ..prompt.correction import _prompt_translation_change_key
from ..prompt.regional import (
    REGIONAL_CONFIG_WORKFLOW_PROPERTY,
    REGIONAL_FIELDS_WORKFLOW_PROPERTY,
    REGIONAL_PROMPT_DATA_TYPE,
    _apply_regional_field_inputs,
    _build_regional_outputs,
    _clone_regional_fields,
    _normalize_regional_config,
    _normalize_regional_fields,
    _regional_config_json,
    _regional_fields_json,
)
from ..seed.compatibility import _scrub_reserved_wildcard_next_seed
from ..settings.service import resolve_metadata_filter_words
from ..wildcard.seed import next_seed
from ..wildcard.service import wildcard_sources_signature
from ..workflow import _get_workflow_node
from .input_types import _FlexibleOptionalInputType
from .regional_conditioning_adapter import _encode_regional_conditioning
from .seed_adapters import (
    PROMPT_STUDIO_REGIONAL_SEED_FEATURE,
    prompt_studio_seed_execution,
)

WILDCARD_MODE_SEQUENTIAL = "sequential"
PROMPT_STUDIO_WILDCARD_MODE_LABELS = ("일반", "순차")
SEED_CONTROL_FIXED = "fixed"
SEED_CONTROL_RANDOMIZE = "randomize"
SEED_CONTROL_INCREMENT = "increment"
SEED_CONTROL_DECREMENT = "decrement"
SEED_CONTROL_MODES = (
    SEED_CONTROL_FIXED,
    SEED_CONTROL_RANDOMIZE,
    SEED_CONTROL_INCREMENT,
    SEED_CONTROL_DECREMENT,
)
MAX_SEED = 0xFFFFFFFFFFFFFFFF
PUBLIC_MAX_SEED = (1 << 53) - 1
WILDCARD_SEED_RANGE_NOTE = (
    f"Browser/public editing and next-seed range: 0..{PUBLIC_MAX_SEED}. The Python "
    "backend continues accepting uint64 values for legacy workflow validation, but "
    "values above the public maximum are best-effort in the browser because JavaScript "
    "may already have lost integer precision. Fixed does not intentionally advance a "
    "legacy value; increment, decrement, and randomize return the next seed to the "
    "public range."
)


def _missing_host_helper(name: str):
    raise RuntimeError(f"Regional Comfy host helper is unavailable: {name}")


def _encode_with_comfy_clip(*args, **kwargs):
    helper = resolve_comfy_host_helper(
        "_encode_with_comfy_clip",
        _missing_host_helper,
    )
    return helper(*args, **kwargs)


class EasyUseAnimaPromptStudioRegional:
    """Mask-scoped Prompt Studio with serialized prompt fields and mask config."""

    DESCRIPTION = (
        "Regional Prompt Studio that stores numbered user masks and applies selected "
        "positive prompt fields only inside those masks. Connect regional_prompt_data "
        "to Anima Regional Conditioning to create KSampler-ready conditionings."
    )
    OUTPUT_TOOLTIPS = (
        "Metadata positive prompt with global and mask-scoped prompt fields included.",
        "Metadata negative prompt with metadata filters applied.",
        "Selected latent width used by the mask editor canvas.",
        "Selected latent height used by the mask editor canvas.",
        "Bundled regional prompt, mask, and model-patch data for Anima Regional Conditioning.",
    )

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "regional_fields": ("STRING", {
                    "multiline": True,
                    "default": _regional_fields_json(),
                    "tooltip": "Internal JSON payload for Regional Prompt Studio fields.",
                }),
                "regional_config": ("STRING", {
                    "multiline": True,
                    "default": _regional_config_json(),
                    "tooltip": "Internal JSON payload for numbered masks and mask editor settings.",
                }),
                "resolution_bucket": ("STRING", {
                    "default": DEFAULT_ADVANCED_RESOLUTION_BUCKET,
                    "tooltip": "Internal selected latent resolution bucket.",
                }),
                "resolution_size": ("STRING", {
                    "default": DEFAULT_ADVANCED_RESOLUTION_SIZE,
                    "tooltip": "Internal selected latent resolution, formatted as width * height (ratio).",
                }),
                "resolution_custom_width": ("INT", {
                    "default": 1024,
                    "min": 32,
                    "max": 8192,
                    "step": 32,
                    "tooltip": "Internal custom latent width. Values are snapped to multiples of 32.",
                }),
                "resolution_custom_height": ("INT", {
                    "default": 1024,
                    "min": 32,
                    "max": 8192,
                    "step": 32,
                    "tooltip": "Internal custom latent height. Values are snapped to multiples of 32.",
                }),
                "wildcard_mode": (PROMPT_STUDIO_WILDCARD_MODE_LABELS, {
                    "default": PROMPT_STUDIO_WILDCARD_MODE_LABELS[0],
                    "tooltip": "General expands deterministically; Sequential uses seed % option_count. Seed control independently decides the next seed.",
                }),
                "wildcard_seed": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": MAX_SEED,
                    "tooltip": (
                        "Wildcard seed used by Regional Prompt Studio fields. "
                        f"{WILDCARD_SEED_RANGE_NOTE}"
                    ),
                }),
                "wildcard_seed_after_generate": (SEED_CONTROL_MODES, {
                    "default": SEED_CONTROL_FIXED,
                    "tooltip": "After an accepted queue: keep the seed fixed, randomize it, or increment it by one.",
                }),
            },
            "optional": _FlexibleOptionalInputType("STRING"),
            "hidden": {
                "workflow_prompt": "PROMPT",
                "extra_pnginfo": "EXTRA_PNGINFO",
                "unique_id": "UNIQUE_ID",
            },
        }

    RETURN_TYPES = (
        "STRING",
        "STRING",
        "INT",
        "INT",
        REGIONAL_PROMPT_DATA_TYPE,
    )
    RETURN_NAMES = (
        "metadata_prompt",
        "metadata_negative_prompt",
        "width",
        "height",
        "regional_prompt_data",
    )
    FUNCTION = "build"
    CATEGORY = "EasyUse Anima/Prompt"

    @classmethod
    def _widget_input_names(cls) -> list[str]:
        return list(cls.INPUT_TYPES()["required"].keys())

    @classmethod
    def IS_CHANGED(
        cls,
        regional_fields: str = "",
        regional_config: str = "",
        resolution_bucket: str = DEFAULT_ADVANCED_RESOLUTION_BUCKET,
        resolution_size: str = DEFAULT_ADVANCED_RESOLUTION_SIZE,
        resolution_custom_width: int = 1024,
        resolution_custom_height: int = 1024,
        wildcard_mode: str = PROMPT_STUDIO_WILDCARD_MODE_LABELS[0],
        wildcard_seed: int = 0,
        wildcard_seed_after_generate: str = SEED_CONTROL_FIXED,
        **kwargs,
    ):
        width, height = _advanced_resolution_from_selection(
            resolution_bucket,
            resolution_size,
            resolution_custom_width,
            resolution_custom_height,
        )
        fields = _normalize_regional_fields(regional_fields)
        effective_fields = _apply_regional_field_inputs(fields, kwargs)
        config = _normalize_regional_config(regional_config, width, height)
        wildcard_mode_key = normalize_prompt_studio_wildcard_mode(wildcard_mode)
        wildcard_active = True
        wildcard_seed_control = _normalize_prompt_studio_wildcard_seed_control(
            wildcard_seed_after_generate,
            wildcard_mode,
        )
        if wildcard_seed_control != SEED_CONTROL_FIXED:
            return float("nan")
        return _stable_change_key({
            "mode": "prompt_studio_regional",
            "metadata_filter_words": resolve_metadata_filter_words(),
            "prompt_translation": _prompt_translation_change_key(),
            "wildcard_sources": wildcard_sources_signature() if wildcard_active else {},
            "wildcard_mode": wildcard_mode_key,
            "wildcard_seed": normalize_seed(wildcard_seed),
            "wildcard_seed_after_generate": wildcard_seed_control,
            "resolution": (width, height),
            "regional_fields": _regional_fields_json(effective_fields),
            "regional_config": _regional_config_json(config),
        })

    @classmethod
    def _update_metadata_fields(
        cls,
        workflow_prompt,
        extra_pnginfo,
        unique_id,
        regional_fields: str,
        regional_config: str,
        extra_updates: dict[str, Any] | None = None,
    ) -> None:
        node_id = _single_value(unique_id)
        if node_id is None:
            return
        node_id = str(node_id)
        updates = {
            "regional_fields": regional_fields,
            "regional_config": regional_config,
        }
        if extra_updates:
            updates.update(extra_updates)

        if isinstance(workflow_prompt, dict):
            prompt_node = workflow_prompt.get(node_id)
            if isinstance(prompt_node, dict):
                inputs = prompt_node.setdefault("inputs", {})
                for name, value in updates.items():
                    inputs[name] = value

        workflow_node = _get_workflow_node(extra_pnginfo, node_id)
        if workflow_node is None:
            return

        properties = workflow_node.setdefault("properties", {})
        if not isinstance(properties, dict):
            properties = {}
            workflow_node["properties"] = properties
        properties[REGIONAL_FIELDS_WORKFLOW_PROPERTY] = regional_fields
        properties[REGIONAL_CONFIG_WORKFLOW_PROPERTY] = regional_config

        input_names = cls._widget_input_names()
        widgets_values = workflow_node.setdefault("widgets_values", [])
        for name, value in updates.items():
            if name not in input_names:
                continue
            index = input_names.index(name)
            while len(widgets_values) <= index:
                widgets_values.append(None)
            widgets_values[index] = value

    @staticmethod
    def _ui(
        regional_fields: str,
        regional_config: str,
        field_inputs: dict | None = None,
        extra_payload: dict[str, Any] | None = None,
    ):
        payload = {
            "prompt_studio_regional": [{
                "regional_fields": regional_fields,
                "regional_config": regional_config,
                "field_inputs": field_inputs or {},
            }]
        }
        if extra_payload:
            payload["prompt_studio_regional"][0].update(extra_payload)
        return payload

    def build(
        self,
        regional_fields: str,
        regional_config: str,
        resolution_bucket: str = DEFAULT_ADVANCED_RESOLUTION_BUCKET,
        resolution_size: str = DEFAULT_ADVANCED_RESOLUTION_SIZE,
        resolution_custom_width: int = 1024,
        resolution_custom_height: int = 1024,
        wildcard_mode: str = PROMPT_STUDIO_WILDCARD_MODE_LABELS[0],
        wildcard_seed: int = 0,
        wildcard_seed_after_generate: str = SEED_CONTROL_FIXED,
        workflow_prompt=None,
        extra_pnginfo=None,
        unique_id=None,
        **field_inputs,
    ):
        width, height = _advanced_resolution_from_selection(
            resolution_bucket,
            resolution_size,
            resolution_custom_width,
            resolution_custom_height,
        )
        fields = _normalize_regional_fields(regional_fields)
        saved_fields = _clone_regional_fields(fields)
        effective_field_inputs = _advanced_field_input_values(field_inputs)
        config = _normalize_regional_config(regional_config, width, height)

        wildcard_mode_key = normalize_prompt_studio_wildcard_mode(wildcard_mode)
        wildcard_mode_label = (
            PROMPT_STUDIO_WILDCARD_MODE_LABELS[1]
            if wildcard_mode_key == WILDCARD_MODE_SEQUENTIAL
            else PROMPT_STUDIO_WILDCARD_MODE_LABELS[0]
        )
        effective_fields = _apply_regional_field_inputs(fields, effective_field_inputs)
        wildcard_seed_value = normalize_seed(wildcard_seed)
        wildcard_effective_seed_control = _normalize_prompt_studio_wildcard_seed_control(
            wildcard_seed_after_generate,
            wildcard_mode,
        )
        _scrub_reserved_wildcard_next_seed(
            field_inputs,
            workflow_prompt,
            unique_id,
        )
        with prompt_studio_seed_execution(
            feature=PROMPT_STUDIO_REGIONAL_SEED_FEATURE,
            unique_id=unique_id,
            seed=wildcard_seed_value,
            after_generate=wildcard_effective_seed_control,
            fallback_next_seed=lambda: next_seed(
                wildcard_seed_value,
                wildcard_effective_seed_control,
            ),
        ) as seed_execution:
            effective_fields, effective_wildcard = _expand_advanced_wildcard_fields(
                effective_fields,
                seed_execution.execution_seed,
                wildcard_mode_key,
            )
            effective_fields = _translate_prompt_fields(effective_fields)
            ui_updates: dict[str, Any] = {
                "wildcard_mode": wildcard_mode_label,
                "wildcard_execution_seed": seed_execution.execution_seed,
                "wildcard_seed": seed_execution.next_seed,
                "wildcard_seed_after_generate": wildcard_effective_seed_control,
                "wildcard_used_keys": list(effective_wildcard["used_keys"]),
                "wildcard_missing_keys": list(effective_wildcard["missing_keys"]),
            }
            metadata_updates: dict[str, Any] = {
                "wildcard_mode": wildcard_mode_label,
                "wildcard_seed": seed_execution.execution_seed,
                "wildcard_seed_after_generate": SEED_CONTROL_FIXED,
            }

            fields_json = _regional_fields_json(saved_fields)
            config_json = _regional_config_json(config)
            self._update_metadata_fields(
                workflow_prompt,
                extra_pnginfo,
                unique_id,
                fields_json,
                config_json,
                metadata_updates,
            )

            (
                _positive_prompt,
                _negative_prompt,
                metadata_prompt,
                metadata_negative_prompt,
                regional_prompt_data,
            ) = _build_regional_outputs(effective_fields, config, width, height)

            return {
                "ui": self._ui(fields_json, config_json, effective_field_inputs, ui_updates),
                "result": (
                    metadata_prompt,
                    metadata_negative_prompt,
                    width,
                    height,
                    regional_prompt_data,
                ),
            }


class EasyUseAnimaRegionalConditioning:
    """Convert Regional Prompt Studio JSON into KSampler-ready conditionings."""

    DESCRIPTION = (
        "Encodes Anima Prompt Studio Regional data with CLIP and attaches mask metadata "
        "to mask-scoped positive conditioning entries."
    )
    OUTPUT_TOOLTIPS = (
        "Positive conditioning containing the global prompt plus mask-scoped regional entries.",
        "Negative conditioning encoded from the bundled negative prompt.",
    )

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "clip": ("CLIP", {
                    "tooltip": "CLIP model used to encode the bundled global and regional prompts.",
                }),
                "regional_prompt_data": (REGIONAL_PROMPT_DATA_TYPE, {
                    "forceInput": True,
                    "tooltip": "Bundled structured data from Anima Prompt Studio Regional.",
                }),
                "mask_strength": ("FLOAT", {
                    "default": 1.0,
                    "min": 0.0,
                    "max": 10.0,
                    "step": 0.01,
                    "tooltip": "Strength applied to mask-scoped conditioning entries.",
                }),
                "set_cond_area": (["mask bounds", "default"], {
                    "default": "mask bounds",
                    "tooltip": "mask bounds mirrors ComfyUI ConditioningSetMask area behavior.",
                }),
            },
        }

    RETURN_TYPES = ("CONDITIONING", "CONDITIONING")
    RETURN_NAMES = ("positive", "negative")
    FUNCTION = "encode"
    CATEGORY = "EasyUse Anima/Prompt"

    @classmethod
    def IS_CHANGED(
        cls,
        regional_prompt_data: str | dict = "",
        mask_strength: float = 1.0,
        set_cond_area: str = "mask bounds",
        **kwargs,
    ):
        return _stable_change_key({
            "mode": "regional_conditioning",
            "regional_prompt_data": (
                regional_prompt_data
                if isinstance(regional_prompt_data, dict)
                else str(regional_prompt_data or "")
            ),
            "mask_strength": _as_float(mask_strength, 1.0),
            "set_cond_area": str(set_cond_area or "mask bounds"),
        })

    def encode(
        self,
        regional_prompt_data: str | dict,
        clip,
        mask_strength: float = 1.0,
        set_cond_area: str = "mask bounds",
    ):
        return _encode_regional_conditioning(
            regional_prompt_data,
            clip,
            mask_strength,
            set_cond_area,
            encode_with_comfy_clip=_encode_with_comfy_clip,
        )


__all__ = ()
