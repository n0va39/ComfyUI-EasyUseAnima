"""ComfyUI adapters for Regional Prompt Studio."""

from __future__ import annotations

from typing import Any

from ..naia.resolution import (
    DEFAULT_ADVANCED_RESOLUTION_BUCKET,
    DEFAULT_ADVANCED_RESOLUTION_SIZE,
)
from ..prompt.regional import (
    REGIONAL_CONFIG_WORKFLOW_PROPERTY,
    REGIONAL_FIELDS_WORKFLOW_PROPERTY,
    REGIONAL_PROMPT_DATA_TYPE,
)
from .input_types import _FlexibleOptionalInputType


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


def _unbound_runtime(*_args, **_kwargs):
    raise RuntimeError("Regional node runtime dependencies are not bound.")


_regional_fields_json = _unbound_runtime
_regional_config_json = _unbound_runtime
_advanced_resolution_from_selection = _unbound_runtime
_normalize_regional_fields = _unbound_runtime
_normalize_regional_config = _unbound_runtime
_apply_regional_field_inputs = _unbound_runtime
normalize_prompt_studio_wildcard_mode = _unbound_runtime
_normalize_prompt_studio_wildcard_seed_control = _unbound_runtime
_stable_change_key = _unbound_runtime
resolve_metadata_filter_words = _unbound_runtime
_prompt_translation_change_key = _unbound_runtime
wildcard_sources_signature = _unbound_runtime
normalize_seed = _unbound_runtime
_single_value = _unbound_runtime
_get_workflow_node = _unbound_runtime
_advanced_field_input_values = _unbound_runtime
_clone_regional_fields = _unbound_runtime
_consume_reserved_wildcard_next_seed = _unbound_runtime
_expand_advanced_wildcard_fields = _unbound_runtime
_translate_prompt_fields = _unbound_runtime
next_seed = _unbound_runtime
_build_regional_outputs = _unbound_runtime
_parse_json_object = _unbound_runtime
_regional_payload_canvas = _unbound_runtime
_encode_with_comfy_clip = _unbound_runtime
_as_bool = _unbound_runtime
_normalize_mask_ids = _unbound_runtime
_regional_union_mask_for_ids = _unbound_runtime
_as_float = _unbound_runtime
_regional_mask_bounds_area = _unbound_runtime
_conditioning_set_values = _unbound_runtime


def _bind_regional_node_runtime(*, resolve_helper, flexible_optional_input_type) -> None:
    global _FlexibleOptionalInputType
    global _regional_fields_json, _regional_config_json, _advanced_resolution_from_selection
    global _normalize_regional_fields, _normalize_regional_config
    global _apply_regional_field_inputs, normalize_prompt_studio_wildcard_mode
    global _normalize_prompt_studio_wildcard_seed_control
    global _stable_change_key, resolve_metadata_filter_words
    global _prompt_translation_change_key, wildcard_sources_signature, normalize_seed
    global _single_value, _get_workflow_node, _advanced_field_input_values
    global _clone_regional_fields
    global _consume_reserved_wildcard_next_seed, _expand_advanced_wildcard_fields
    global _translate_prompt_fields, next_seed
    global _build_regional_outputs, _parse_json_object, _regional_payload_canvas
    global _encode_with_comfy_clip, _as_bool, _normalize_mask_ids
    global _regional_union_mask_for_ids, _as_float, _regional_mask_bounds_area
    global _conditioning_set_values

    def runtime_helper(name):
        def call(*args, **kwargs):
            return resolve_helper(name)(*args, **kwargs)

        return call

    _FlexibleOptionalInputType = flexible_optional_input_type
    for name in (
        "_regional_fields_json",
        "_regional_config_json",
        "_advanced_resolution_from_selection",
        "_normalize_regional_fields",
        "_normalize_regional_config",
        "_apply_regional_field_inputs",
        "normalize_prompt_studio_wildcard_mode",
        "_normalize_prompt_studio_wildcard_seed_control",
        "_stable_change_key",
        "resolve_metadata_filter_words",
        "_prompt_translation_change_key",
        "wildcard_sources_signature",
        "normalize_seed",
        "_single_value",
        "_get_workflow_node",
        "_advanced_field_input_values",
        "_clone_regional_fields",
        "_consume_reserved_wildcard_next_seed",
        "_expand_advanced_wildcard_fields",
        "_translate_prompt_fields",
        "next_seed",
        "_build_regional_outputs",
        "_parse_json_object",
        "_regional_payload_canvas",
        "_encode_with_comfy_clip",
        "_as_bool",
        "_normalize_mask_ids",
        "_regional_union_mask_for_ids",
        "_as_float",
        "_regional_mask_bounds_area",
        "_conditioning_set_values",
    ):
        globals()[name] = runtime_helper(name)


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
        reserved_next_wildcard_seed = _consume_reserved_wildcard_next_seed(
            field_inputs,
            workflow_prompt,
            unique_id,
            wildcard_seed_value,
            wildcard_mode_key,
            wildcard_effective_seed_control,
        )
        ui_updates: dict[str, Any] = {}
        metadata_updates: dict[str, Any] = {}

        effective_fields, effective_wildcard = _expand_advanced_wildcard_fields(
            effective_fields,
            wildcard_seed_value,
            wildcard_mode_key,
        )
        effective_fields = _translate_prompt_fields(effective_fields)
        next_wildcard_seed = (
            reserved_next_wildcard_seed
            if reserved_next_wildcard_seed is not None
            else next_seed(wildcard_seed_value, wildcard_effective_seed_control)
        )
        ui_updates.update({
            "wildcard_mode": wildcard_mode_label,
            "wildcard_seed": next_wildcard_seed,
            "wildcard_seed_after_generate": wildcard_effective_seed_control,
            "wildcard_used_keys": list(effective_wildcard["used_keys"]),
            "wildcard_missing_keys": list(effective_wildcard["missing_keys"]),
        })
        metadata_updates.update({
            "wildcard_mode": wildcard_mode_label,
            "wildcard_seed": wildcard_seed_value,
            "wildcard_seed_after_generate": SEED_CONTROL_FIXED,
        })

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
            positive_prompt,
            negative_prompt,
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
        payload = _parse_json_object(regional_prompt_data)
        width, height = _regional_payload_canvas(payload)
        positive_prompt = str(payload.get("global_prompt") or payload.get("positive_prompt") or "")
        negative_prompt = str(payload.get("negative_prompt") or "")

        positive = list(_encode_with_comfy_clip(clip, positive_prompt))
        negative = _encode_with_comfy_clip(clip, negative_prompt)

        if _as_bool(payload.get("regional_enabled"), False):
            use_mask_bounds = str(set_cond_area or "mask bounds") != "default"
            mask_prompts = payload.get("mask_prompts") if isinstance(payload.get("mask_prompts"), list) else []
            for entry in mask_prompts:
                if not isinstance(entry, dict):
                    continue
                valid_mask_ids = _normalize_mask_ids(entry.get("valid_mask_ids") or entry.get("mask_ids"))
                prompt = str(entry.get("prompt") or entry.get("text") or "").strip()
                if not valid_mask_ids or not prompt:
                    continue
                mask = _regional_union_mask_for_ids(payload, valid_mask_ids, width, height)
                regional_conditioning = _encode_with_comfy_clip(clip, prompt)
                conditioning_values = {
                    "mask": mask,
                    "set_area_to_bounds": False,
                    "mask_strength": _as_float(mask_strength, 1.0),
                    "easyuse_anima_region": {
                        "field_id": str(entry.get("field_id") or ""),
                        "mask_ids": valid_mask_ids,
                    },
                }
                if use_mask_bounds:
                    area = _regional_mask_bounds_area(mask, width, height)
                    if area is not None:
                        conditioning_values["area"] = area
                positive.extend(_conditioning_set_values(regional_conditioning, conditioning_values))

        return (positive, negative)


__all__ = ()
