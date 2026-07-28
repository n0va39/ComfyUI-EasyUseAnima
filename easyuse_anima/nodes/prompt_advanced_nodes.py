"""ComfyUI adapters for Advanced and legacy Extend Prompt Studio."""

from __future__ import annotations

import json
from contextlib import nullcontext
from typing import Any

from ..common.serialization import _stable_change_key
from ..common.values import _as_bool, _as_int, _single_value
from ..naia.client import _parse_random_response, _post_random
from ..naia.resolution import (
    CUSTOM_ADVANCED_RESOLUTION_BUCKET,
    DEFAULT_ADVANCED_RESOLUTION_BUCKET,
    DEFAULT_ADVANCED_RESOLUTION_SIZE,
    NAIA_ADVANCED_RESOLUTION_BUCKET,
    _advanced_resolution_from_selection,
    _resolution_label,
    _resolve_naia_resolution,
)
from ..prompt.advanced import (
    ADVANCED_FIELDS_WORKFLOW_PROPERTY,
    EXTEND_PROMPT_SLOT_SPECS,
    PROMPT_STUDIO_ADVANCED_RETURN_NAMES,
    PROMPT_STUDIO_ADVANCED_RETURN_TYPES,
    _advanced_enabled_naia_panes,
    _advanced_field_input_values,
    _advanced_fields_json,
    _advanced_has_enabled_naia,
    _advanced_naia_field_updates,
    _advanced_uses_naia_resolution,
    _apply_advanced_field_inputs,
    _build_advanced_prompt_data,
    _build_advanced_prompts,
    _clone_advanced_fields,
    _expand_advanced_wildcard_fields,
    _normalize_advanced_fields,
    _normalize_prompt_studio_wildcard_seed_control,
    _set_naia_field_text,
    _translate_prompt_fields,
    normalize_prompt_studio_wildcard_mode,
    normalize_seed,
)
from ..prompt.artist_mix import (
    ARTIST_MIX_DEFAULT_CLUSTER_COUNT,
    ARTIST_MIX_DEFAULT_DOMINANT_ISOLATION,
    ARTIST_MIX_DEFAULT_DOMINANT_THRESHOLD,
    ARTIST_MIX_DEFAULT_EXACT_TOP_K,
    ARTIST_MIX_DEFAULT_RMS_SCALE_CAP,
    ARTIST_MIX_DEFAULT_START_PERCENT,
    ARTIST_MIX_DEFAULT_STRENGTH_SCALE,
    ARTIST_MIX_DEFAULT_STYLE_GAIN,
    ARTIST_MIX_MODE_OFF,
    ARTIST_MIX_STUDIO_MODES,
    _artist_mix_mode_tooltip,
    _bounded_artist_mix_float,
    _bounded_artist_mix_int,
    _normalize_artist_mix_mode,
)
from ..prompt.correction import (
    _prompt_translation_change_key,
    _translate_prompt_text,
)
from ..prompt.data import PROMPT_DATA_TYPE, _prompt_data_parameter_snapshot
from ..seed.compatibility import _scrub_reserved_wildcard_next_seed
from ..settings.service import (
    resolve_metadata_filter_words,
    resolve_naia_settings,
)
from ..wildcard.seed import next_seed
from ..wildcard.service import wildcard_sources_signature
from ..workflow import _get_workflow_node
from .input_types import _FlexibleOptionalInputType
from .naia_nodes import EasyUseAnimaNAIARandomPrompt
from .seed_adapters import (
    PROMPT_STUDIO_ADVANCED_SEED_FEATURE,
    PromptStudioSeedExecution,
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


class EasyUseAnimaPromptStudioAdvanced:
    """Dynamic positive/negative Prompt Studio with serialized field blocks."""

    DESCRIPTION = (
        "Advanced Prompt Studio with reorderable positive and negative fields, NAIA fill support, "
        "trigger input handling, Mod Guidance routing, metadata outputs, and latent resolution output."
    )
    OUTPUT_TOOLTIPS = (
        "Final positive prompt assembled from enabled positive fields.",
        "Final negative prompt assembled from enabled negative fields.",
        "Positive quality fields routed to Anima Mod Guidance.",
        "Negative quality fields routed to Anima Mod Guidance.",
        "Boolean flag passed through for Anima Mod Guidance workflow control.",
        "Boolean flag passed through for negative Anima Mod Guidance workflow control.",
        "Positive metadata prompt with metadata filters applied.",
        "Negative metadata prompt with metadata filters applied.",
        "Selected latent width.",
        "Selected latent height.",
    )

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "use_naia": ("BOOLEAN", {
                    "default": False,
                    "tooltip": (
                        "Internal request flag. The front-end exposes this as the NAIA Prompt field's "
                        "'Fill from NAIA' button, which fills that field with a fresh NAIA random prompt."
                    ),
                }),
                "consume_naia_on_queue": ("BOOLEAN", {
                    "default": True,
                    "tooltip": (
                        "Internal one-shot mode. Successful NAIA fills are saved with the request flag off "
                        "so loaded workflows reuse the stored prompt."
                    ),
                }),
                "use_anima_mod_guidance": ("BOOLEAN", {
                    "default": False,
                    "tooltip": (
                        "true: positive output excludes quality fields and sends them "
                        "through the mod guidance quality output."
                    ),
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
                "pin_trigger_tags_to_front": ("BOOLEAN", {
                    "default": False,
                    "tooltip": "Legacy internal flag. Trigger field Pin buttons control trigger placement.",
                }),
                "advanced_fields": ("STRING", {
                    "multiline": True,
                    "default": _advanced_fields_json(),
                    "tooltip": "Internal JSON payload for Advanced Prompt Studio fields.",
                }),
                "use_negative_anima_mod_guidance": ("BOOLEAN", {
                    "default": False,
                    "tooltip": (
                        "true: negative output excludes negative quality fields and sends them "
                        "through the negative Mod Guidance output."
                    ),
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
                        "Wildcard seed used by Advanced Prompt Studio fields. "
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

    RETURN_TYPES = PROMPT_STUDIO_ADVANCED_RETURN_TYPES
    RETURN_NAMES = PROMPT_STUDIO_ADVANCED_RETURN_NAMES
    FUNCTION = "build"
    CATEGORY = "EasyUse Anima/Prompt"

    @classmethod
    def _widget_input_names(cls) -> list[str]:
        return list(cls.INPUT_TYPES()["required"].keys())

    @classmethod
    def IS_CHANGED(
        cls,
        use_naia: bool = False,
        consume_naia_on_queue: bool = True,
        use_anima_mod_guidance: bool = False,
        pin_trigger_tags_to_front: bool = False,
        use_negative_anima_mod_guidance: bool = False,
        advanced_fields: str = "",
        resolution_bucket: str = DEFAULT_ADVANCED_RESOLUTION_BUCKET,
        resolution_size: str = DEFAULT_ADVANCED_RESOLUTION_SIZE,
        resolution_custom_width: int = 1024,
        resolution_custom_height: int = 1024,
        wildcard_mode: str = PROMPT_STUDIO_WILDCARD_MODE_LABELS[0],
        wildcard_seed: int = 0,
        wildcard_seed_after_generate: str = SEED_CONTROL_FIXED,
        **kwargs,
    ):
        fields = _normalize_advanced_fields(advanced_fields)
        if _as_bool(use_naia, False) and (
            _advanced_has_enabled_naia(fields)
            or _advanced_uses_naia_resolution(resolution_bucket)
        ):
            return float("nan")
        effective_fields = _apply_advanced_field_inputs(fields, kwargs)
        wildcard_mode_key = normalize_prompt_studio_wildcard_mode(wildcard_mode)
        wildcard_active = True
        wildcard_seed_control = _normalize_prompt_studio_wildcard_seed_control(
            wildcard_seed_after_generate,
            wildcard_mode,
        )
        if wildcard_seed_control != SEED_CONTROL_FIXED:
            return float("nan")
        return _stable_change_key({
            "mode": "prompt_studio_advanced",
            "metadata_filter_words": resolve_metadata_filter_words(),
            "prompt_translation": _prompt_translation_change_key(),
            "wildcard_sources": wildcard_sources_signature() if wildcard_active else {},
            "wildcard_mode": wildcard_mode_key,
            "wildcard_seed": normalize_seed(wildcard_seed),
            "wildcard_seed_after_generate": wildcard_seed_control,
            "use_anima_mod_guidance": _as_bool(use_anima_mod_guidance, False),
            "use_negative_anima_mod_guidance": _as_bool(use_negative_anima_mod_guidance, False),
            "resolution": _advanced_resolution_from_selection(
                resolution_bucket,
                resolution_size,
                resolution_custom_width,
                resolution_custom_height,
            ),
            "pin_trigger_tags_to_front": _as_bool(pin_trigger_tags_to_front, False),
            "advanced_fields": _advanced_fields_json(effective_fields),
        })

    @classmethod
    def _update_metadata_fields(
        cls,
        workflow_prompt,
        extra_pnginfo,
        unique_id,
        advanced_fields: str,
        use_naia: bool,
        extra_updates: dict[str, Any] | None = None,
    ) -> None:
        node_id = _single_value(unique_id)
        if node_id is None:
            return
        node_id = str(node_id)
        updates = {
            "use_naia": _as_bool(use_naia, False),
            "advanced_fields": advanced_fields,
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

        if "advanced_fields" in updates:
            properties = workflow_node.setdefault("properties", {})
            if not isinstance(properties, dict):
                properties = {}
                workflow_node["properties"] = properties
            properties[ADVANCED_FIELDS_WORKFLOW_PROPERTY] = updates["advanced_fields"]

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
        advanced_fields: str,
        use_naia: bool,
        field_inputs: dict | None = None,
        extra_payload: dict[str, Any] | None = None,
    ):
        payload = {
            "prompt_studio_advanced": [{
                "advanced_fields": advanced_fields,
                "use_naia": _as_bool(use_naia, False),
                "field_inputs": field_inputs or {},
            }]
        }
        if extra_payload:
            payload["prompt_studio_advanced"][0].update(extra_payload)
        return payload

    def build(
        self,
        use_naia: bool,
        consume_naia_on_queue: bool,
        use_anima_mod_guidance: bool,
        pin_trigger_tags_to_front: bool,
        advanced_fields: str,
        use_negative_anima_mod_guidance: bool = False,
        wildcard_mode: str = PROMPT_STUDIO_WILDCARD_MODE_LABELS[0],
        wildcard_seed: int = 0,
        wildcard_seed_after_generate: str = SEED_CONTROL_FIXED,
        resolution_bucket: str = DEFAULT_ADVANCED_RESOLUTION_BUCKET,
        resolution_size: str = DEFAULT_ADVANCED_RESOLUTION_SIZE,
        resolution_custom_width: int = 1024,
        resolution_custom_height: int = 1024,
        workflow_prompt=None,
        extra_pnginfo=None,
        unique_id=None,
        _seed_execution: PromptStudioSeedExecution | None = None,
        **field_inputs,
    ):
        fields = _normalize_advanced_fields(advanced_fields)
        saved_fields = _clone_advanced_fields(fields)
        effective_field_inputs = _advanced_field_input_values(field_inputs)
        requested_use_naia = _as_bool(use_naia, False)
        enabled_naia_panes = _advanced_enabled_naia_panes(fields)
        use_naia_resolution = _advanced_uses_naia_resolution(resolution_bucket)
        live_use_naia = requested_use_naia and (bool(enabled_naia_panes) or use_naia_resolution)
        metadata_use_naia = live_use_naia
        metadata_updates: dict[str, Any] = {}
        ui_updates: dict[str, Any] = {}
        wildcard_mode_key = normalize_prompt_studio_wildcard_mode(wildcard_mode)
        wildcard_mode_label = (
            PROMPT_STUDIO_WILDCARD_MODE_LABELS[1]
            if wildcard_mode_key == WILDCARD_MODE_SEQUENTIAL
            else PROMPT_STUDIO_WILDCARD_MODE_LABELS[0]
        )
        effective_fields = _apply_advanced_field_inputs(fields, effective_field_inputs)
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
        width, height = _advanced_resolution_from_selection(
            resolution_bucket,
            resolution_size,
            resolution_custom_width,
            resolution_custom_height,
        )

        seed_context = (
            nullcontext(_seed_execution)
            if _seed_execution is not None
            else prompt_studio_seed_execution(
                feature=PROMPT_STUDIO_ADVANCED_SEED_FEATURE,
                unique_id=unique_id,
                seed=wildcard_seed_value,
                after_generate=wildcard_effective_seed_control,
                fallback_next_seed=lambda: next_seed(
                    wildcard_seed_value,
                    wildcard_effective_seed_control,
                ),
            )
        )
        with seed_context as seed_execution:
            execution_seed = seed_execution.execution_seed
            if live_use_naia:
                naia_settings = resolve_naia_settings()
                body = EasyUseAnimaNAIARandomPrompt._make_request_body(
                    _as_bool(naia_settings["use_naia_settings"], True),
                    naia_settings["pre_prompt"],
                    naia_settings["post_prompt"],
                    naia_settings["auto_hide"],
                    naia_settings["preprocessing"],
                )
                resp = _post_random(
                    naia_settings["host"],
                    naia_settings["port"],
                    body,
                    allow_remote_api=bool(naia_settings.get("allow_remote_api", False)),
                )
                naia_prompt, naia_negative, naia_width, naia_height = _parse_random_response(resp)
                naia_field_updates = _advanced_naia_field_updates(
                    fields,
                    {
                        "positive": naia_prompt,
                        "negative": naia_negative,
                    },
                )
                if naia_field_updates:
                    ui_updates["naia_field_updates"] = naia_field_updates
                if "positive" in enabled_naia_panes:
                    saved_fields = _set_naia_field_text(saved_fields, "positive", naia_prompt)
                    effective_fields = _set_naia_field_text(effective_fields, "positive", naia_prompt)
                if "negative" in enabled_naia_panes:
                    saved_fields = _set_naia_field_text(saved_fields, "negative", naia_negative)
                    effective_fields = _set_naia_field_text(effective_fields, "negative", naia_negative)
                if use_naia_resolution:
                    width, height = _resolve_naia_resolution(naia_width, naia_height, naia_settings)
                    ui_updates["naia_resolution_update"] = {
                        "width": width,
                        "height": height,
                    }
                    resolution_label = _resolution_label(width, height)
                    metadata_updates.update({
                        "resolution_bucket": CUSTOM_ADVANCED_RESOLUTION_BUCKET,
                        "resolution_size": resolution_label,
                        "resolution_custom_width": width,
                        "resolution_custom_height": height,
                    })
                    ui_updates.update({
                        "resolution_bucket": NAIA_ADVANCED_RESOLUTION_BUCKET,
                        "resolution_size": resolution_label,
                        "resolution_custom_width": width,
                        "resolution_custom_height": height,
                    })
                metadata_use_naia = False

            ui_fields = _clone_advanced_fields(saved_fields)
            effective_fields, effective_wildcard = _expand_advanced_wildcard_fields(
                effective_fields,
                execution_seed,
                wildcard_mode_key,
            )
            effective_fields = _translate_prompt_fields(effective_fields)
            ui_updates.update({
                "wildcard_mode": wildcard_mode_label,
                "wildcard_execution_seed": execution_seed,
                "wildcard_seed": seed_execution.next_seed,
                "wildcard_seed_after_generate": wildcard_effective_seed_control,
                "wildcard_used_keys": list(effective_wildcard["used_keys"]),
                "wildcard_missing_keys": list(effective_wildcard["missing_keys"]),
            })
            metadata_updates.update({
                "wildcard_mode": wildcard_mode_label,
                "wildcard_seed": execution_seed,
                "wildcard_seed_after_generate": SEED_CONTROL_FIXED,
            })

            fields_json = _advanced_fields_json(saved_fields)
            ui_fields_json = _advanced_fields_json(ui_fields)
            if live_use_naia or metadata_updates:
                self._update_metadata_fields(
                    workflow_prompt,
                    extra_pnginfo,
                    unique_id,
                    fields_json,
                    metadata_use_naia,
                    metadata_updates,
                )

            result = _build_advanced_prompts(
                effective_fields,
                use_anima_mod_guidance,
                use_negative_anima_mod_guidance,
                pin_trigger_tags_to_front,
            )
            return {
                "ui": self._ui(
                    ui_fields_json,
                    requested_use_naia,
                    effective_field_inputs,
                    ui_updates,
                ),
                "result": (*result, width, height),
            }


class EasyUseAnimaPromptStudioAdvancedV2(EasyUseAnimaPromptStudioAdvanced):
    """Advanced Prompt Studio v2 with structured prompt data output."""

    DESCRIPTION = (
        "Advanced Prompt Studio v2. It outputs a single EASYUSE_ANIMA_PROMPT_DATA "
        "dict socket for downstream nodes."
    )
    OUTPUT_TOOLTIPS = ("Structured prompt data dict for downstream EasyUse Anima nodes.",)
    RETURN_TYPES = (PROMPT_DATA_TYPE,)
    RETURN_NAMES = (PROMPT_DATA_TYPE,)

    @classmethod
    def INPUT_TYPES(cls):
        base = EasyUseAnimaPromptStudioAdvanced.INPUT_TYPES()
        required = dict(base["required"])
        required.update({
            "artist_mix_mode": (list(ARTIST_MIX_STUDIO_MODES), {
                "default": ARTIST_MIX_MODE_OFF,
                "tooltip": _artist_mix_mode_tooltip(),
            }),
            "artist_mix_start_percent": ("FLOAT", {
                "default": ARTIST_MIX_DEFAULT_START_PERCENT,
                "min": 0.0,
                "max": 1.0,
                "step": 0.01,
                "tooltip": "Start percent used by late/scheduled artist mix modes.",
            }),
            "artist_mix_strength_scale": ("FLOAT", {
                "default": ARTIST_MIX_DEFAULT_STRENGTH_SCALE,
                "min": 0.0,
                "max": 5.0,
                "step": 0.01,
                "tooltip": "Strength multiplier used by exact artist mix modes.",
            }),
            "artist_mix_style_gain": ("FLOAT", {
                "default": ARTIST_MIX_DEFAULT_STYLE_GAIN,
                "min": 0.0,
                "max": 3.0,
                "step": 0.01,
                "tooltip": "Style delta gain used by delta_rms, hybrid tail, and clustered compressed branches.",
            }),
            "artist_mix_rms_scale_cap": ("FLOAT", {
                "default": ARTIST_MIX_DEFAULT_RMS_SCALE_CAP,
                "min": 1.0,
                "max": 5.0,
                "step": 0.01,
                "tooltip": "Maximum RMS energy restore scale for delta_rms compressed artist branches.",
            }),
            "artist_mix_exact_top_k": ("INT", {
                "default": ARTIST_MIX_DEFAULT_EXACT_TOP_K,
                "min": 0,
                "max": 64,
                "tooltip": "Hybrid mode keeps this many strongest artists as exact positive branches.",
            }),
            "artist_mix_cluster_count": ("INT", {
                "default": ARTIST_MIX_DEFAULT_CLUSTER_COUNT,
                "min": 1,
                "max": 32,
                "tooltip": "Clustered mode compresses non-dominant artists into this many positive branches.",
            }),
            "artist_mix_dominant_isolation": ("BOOLEAN", {
                "default": ARTIST_MIX_DEFAULT_DOMINANT_ISOLATION,
                "tooltip": "Clustered mode keeps artists above the dominant threshold as exact branches.",
            }),
            "artist_mix_dominant_threshold": ("FLOAT", {
                "default": ARTIST_MIX_DEFAULT_DOMINANT_THRESHOLD,
                "min": 0.0,
                "max": 1.0,
                "step": 0.01,
                "tooltip": "Clustered dominant isolation threshold based on normalized artist weight.",
            }),
        })
        return {
            **base,
            "required": required,
        }

    @classmethod
    def IS_CHANGED(
        cls,
        use_naia: bool = False,
        consume_naia_on_queue: bool = True,
        use_anima_mod_guidance: bool = False,
        pin_trigger_tags_to_front: bool = False,
        use_negative_anima_mod_guidance: bool = False,
        advanced_fields: str = "",
        resolution_bucket: str = DEFAULT_ADVANCED_RESOLUTION_BUCKET,
        resolution_size: str = DEFAULT_ADVANCED_RESOLUTION_SIZE,
        resolution_custom_width: int = 1024,
        resolution_custom_height: int = 1024,
        wildcard_mode: str = PROMPT_STUDIO_WILDCARD_MODE_LABELS[0],
        wildcard_seed: int = 0,
        wildcard_seed_after_generate: str = SEED_CONTROL_FIXED,
        artist_mix_mode: str = ARTIST_MIX_MODE_OFF,
        artist_mix_start_percent: float = ARTIST_MIX_DEFAULT_START_PERCENT,
        artist_mix_strength_scale: float = ARTIST_MIX_DEFAULT_STRENGTH_SCALE,
        artist_mix_style_gain: float = ARTIST_MIX_DEFAULT_STYLE_GAIN,
        artist_mix_rms_scale_cap: float = ARTIST_MIX_DEFAULT_RMS_SCALE_CAP,
        artist_mix_exact_top_k: int = ARTIST_MIX_DEFAULT_EXACT_TOP_K,
        artist_mix_cluster_count: int = ARTIST_MIX_DEFAULT_CLUSTER_COUNT,
        artist_mix_dominant_isolation: bool = ARTIST_MIX_DEFAULT_DOMINANT_ISOLATION,
        artist_mix_dominant_threshold: float = ARTIST_MIX_DEFAULT_DOMINANT_THRESHOLD,
        **field_inputs,
    ):
        base_key = EasyUseAnimaPromptStudioAdvanced.IS_CHANGED(
            use_naia=use_naia,
            consume_naia_on_queue=consume_naia_on_queue,
            use_anima_mod_guidance=use_anima_mod_guidance,
            pin_trigger_tags_to_front=pin_trigger_tags_to_front,
            use_negative_anima_mod_guidance=use_negative_anima_mod_guidance,
            advanced_fields=advanced_fields,
            resolution_bucket=resolution_bucket,
            resolution_size=resolution_size,
            resolution_custom_width=resolution_custom_width,
            resolution_custom_height=resolution_custom_height,
            wildcard_mode=wildcard_mode,
            wildcard_seed=wildcard_seed,
            wildcard_seed_after_generate=wildcard_seed_after_generate,
            **field_inputs,
        )
        if base_key != base_key:
            return base_key
        return _stable_change_key({
            "base": base_key,
            "artist_mix_mode": _normalize_artist_mix_mode(artist_mix_mode, ARTIST_MIX_MODE_OFF),
            "artist_mix_start_percent": _bounded_artist_mix_float(
                artist_mix_start_percent,
                ARTIST_MIX_DEFAULT_START_PERCENT,
                0.0,
                1.0,
            ),
            "artist_mix_strength_scale": _bounded_artist_mix_float(
                artist_mix_strength_scale,
                ARTIST_MIX_DEFAULT_STRENGTH_SCALE,
                0.0,
                5.0,
            ),
            "artist_mix_style_gain": _bounded_artist_mix_float(
                artist_mix_style_gain,
                ARTIST_MIX_DEFAULT_STYLE_GAIN,
                0.0,
                3.0,
            ),
            "artist_mix_rms_scale_cap": _bounded_artist_mix_float(
                artist_mix_rms_scale_cap,
                ARTIST_MIX_DEFAULT_RMS_SCALE_CAP,
                1.0,
                5.0,
            ),
            "artist_mix_exact_top_k": _bounded_artist_mix_int(
                artist_mix_exact_top_k,
                ARTIST_MIX_DEFAULT_EXACT_TOP_K,
                0,
                64,
            ),
            "artist_mix_cluster_count": _bounded_artist_mix_int(
                artist_mix_cluster_count,
                ARTIST_MIX_DEFAULT_CLUSTER_COUNT,
                1,
                32,
            ),
            "artist_mix_dominant_isolation": _as_bool(
                artist_mix_dominant_isolation,
                ARTIST_MIX_DEFAULT_DOMINANT_ISOLATION,
            ),
            "artist_mix_dominant_threshold": _bounded_artist_mix_float(
                artist_mix_dominant_threshold,
                ARTIST_MIX_DEFAULT_DOMINANT_THRESHOLD,
                0.0,
                1.0,
            ),
        })

    def build(
        self,
        use_naia: bool,
        consume_naia_on_queue: bool,
        use_anima_mod_guidance: bool,
        pin_trigger_tags_to_front: bool,
        advanced_fields: str,
        use_negative_anima_mod_guidance: bool = False,
        wildcard_mode: str = PROMPT_STUDIO_WILDCARD_MODE_LABELS[0],
        wildcard_seed: int = 0,
        wildcard_seed_after_generate: str = SEED_CONTROL_FIXED,
        resolution_bucket: str = DEFAULT_ADVANCED_RESOLUTION_BUCKET,
        resolution_size: str = DEFAULT_ADVANCED_RESOLUTION_SIZE,
        resolution_custom_width: int = 1024,
        resolution_custom_height: int = 1024,
        artist_mix_mode: str = ARTIST_MIX_MODE_OFF,
        artist_mix_start_percent: float = ARTIST_MIX_DEFAULT_START_PERCENT,
        artist_mix_strength_scale: float = ARTIST_MIX_DEFAULT_STRENGTH_SCALE,
        artist_mix_style_gain: float = ARTIST_MIX_DEFAULT_STYLE_GAIN,
        artist_mix_rms_scale_cap: float = ARTIST_MIX_DEFAULT_RMS_SCALE_CAP,
        artist_mix_exact_top_k: int = ARTIST_MIX_DEFAULT_EXACT_TOP_K,
        artist_mix_cluster_count: int = ARTIST_MIX_DEFAULT_CLUSTER_COUNT,
        artist_mix_dominant_isolation: bool = ARTIST_MIX_DEFAULT_DOMINANT_ISOLATION,
        artist_mix_dominant_threshold: float = ARTIST_MIX_DEFAULT_DOMINANT_THRESHOLD,
        workflow_prompt=None,
        extra_pnginfo=None,
        unique_id=None,
        **field_inputs,
    ):
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
            feature=PROMPT_STUDIO_ADVANCED_SEED_FEATURE,
            unique_id=unique_id,
            seed=wildcard_seed_value,
            after_generate=wildcard_effective_seed_control,
            fallback_next_seed=lambda: next_seed(
                wildcard_seed_value,
                wildcard_effective_seed_control,
            ),
        ) as seed_execution:
            return self._build_with_seed(
                use_naia,
                consume_naia_on_queue,
                use_anima_mod_guidance,
                pin_trigger_tags_to_front,
                advanced_fields,
                use_negative_anima_mod_guidance=use_negative_anima_mod_guidance,
                wildcard_mode=wildcard_mode,
                wildcard_seed=wildcard_seed,
                wildcard_seed_after_generate=wildcard_seed_after_generate,
                resolution_bucket=resolution_bucket,
                resolution_size=resolution_size,
                resolution_custom_width=resolution_custom_width,
                resolution_custom_height=resolution_custom_height,
                artist_mix_mode=artist_mix_mode,
                artist_mix_start_percent=artist_mix_start_percent,
                artist_mix_strength_scale=artist_mix_strength_scale,
                artist_mix_style_gain=artist_mix_style_gain,
                artist_mix_rms_scale_cap=artist_mix_rms_scale_cap,
                artist_mix_exact_top_k=artist_mix_exact_top_k,
                artist_mix_cluster_count=artist_mix_cluster_count,
                artist_mix_dominant_isolation=artist_mix_dominant_isolation,
                artist_mix_dominant_threshold=artist_mix_dominant_threshold,
                workflow_prompt=workflow_prompt,
                extra_pnginfo=extra_pnginfo,
                unique_id=unique_id,
                _seed_execution=seed_execution,
                **field_inputs,
            )

    def _build_with_seed(
        self,
        use_naia: bool,
        consume_naia_on_queue: bool,
        use_anima_mod_guidance: bool,
        pin_trigger_tags_to_front: bool,
        advanced_fields: str,
        use_negative_anima_mod_guidance: bool = False,
        wildcard_mode: str = PROMPT_STUDIO_WILDCARD_MODE_LABELS[0],
        wildcard_seed: int = 0,
        wildcard_seed_after_generate: str = SEED_CONTROL_FIXED,
        resolution_bucket: str = DEFAULT_ADVANCED_RESOLUTION_BUCKET,
        resolution_size: str = DEFAULT_ADVANCED_RESOLUTION_SIZE,
        resolution_custom_width: int = 1024,
        resolution_custom_height: int = 1024,
        artist_mix_mode: str = ARTIST_MIX_MODE_OFF,
        artist_mix_start_percent: float = ARTIST_MIX_DEFAULT_START_PERCENT,
        artist_mix_strength_scale: float = ARTIST_MIX_DEFAULT_STRENGTH_SCALE,
        artist_mix_style_gain: float = ARTIST_MIX_DEFAULT_STYLE_GAIN,
        artist_mix_rms_scale_cap: float = ARTIST_MIX_DEFAULT_RMS_SCALE_CAP,
        artist_mix_exact_top_k: int = ARTIST_MIX_DEFAULT_EXACT_TOP_K,
        artist_mix_cluster_count: int = ARTIST_MIX_DEFAULT_CLUSTER_COUNT,
        artist_mix_dominant_isolation: bool = ARTIST_MIX_DEFAULT_DOMINANT_ISOLATION,
        artist_mix_dominant_threshold: float = ARTIST_MIX_DEFAULT_DOMINANT_THRESHOLD,
        workflow_prompt=None,
        extra_pnginfo=None,
        unique_id=None,
        _seed_execution: PromptStudioSeedExecution | None = None,
        **field_inputs,
    ):
        if _seed_execution is None:
            raise RuntimeError("Advanced v2 seed execution was not reserved")
        base = super().build(
            use_naia,
            consume_naia_on_queue,
            use_anima_mod_guidance,
            pin_trigger_tags_to_front,
            advanced_fields,
            use_negative_anima_mod_guidance=use_negative_anima_mod_guidance,
            wildcard_mode=wildcard_mode,
            wildcard_seed=wildcard_seed,
            wildcard_seed_after_generate=wildcard_seed_after_generate,
            resolution_bucket=resolution_bucket,
            resolution_size=resolution_size,
            resolution_custom_width=resolution_custom_width,
            resolution_custom_height=resolution_custom_height,
            workflow_prompt=workflow_prompt,
            extra_pnginfo=extra_pnginfo,
            unique_id=unique_id,
            _seed_execution=_seed_execution,
            **field_inputs,
        )
        compat_result = tuple(base.get("result") or ())
        ui_payloads = base.get("ui", {}).get("prompt_studio_advanced", [])
        ui_payload = ui_payloads[0] if ui_payloads and isinstance(ui_payloads[0], dict) else {}
        if isinstance(ui_payload, dict):
            ui_payload.update({
                "artist_mix_mode": _normalize_artist_mix_mode(artist_mix_mode, ARTIST_MIX_MODE_OFF),
                "artist_mix_start_percent": _bounded_artist_mix_float(
                    artist_mix_start_percent,
                    ARTIST_MIX_DEFAULT_START_PERCENT,
                    0.0,
                    1.0,
                ),
                "artist_mix_strength_scale": _bounded_artist_mix_float(
                    artist_mix_strength_scale,
                    ARTIST_MIX_DEFAULT_STRENGTH_SCALE,
                    0.0,
                    5.0,
                ),
                "artist_mix_style_gain": _bounded_artist_mix_float(
                    artist_mix_style_gain,
                    ARTIST_MIX_DEFAULT_STYLE_GAIN,
                    0.0,
                    3.0,
                ),
                "artist_mix_rms_scale_cap": _bounded_artist_mix_float(
                    artist_mix_rms_scale_cap,
                    ARTIST_MIX_DEFAULT_RMS_SCALE_CAP,
                    1.0,
                    5.0,
                ),
                "artist_mix_exact_top_k": _bounded_artist_mix_int(
                    artist_mix_exact_top_k,
                    ARTIST_MIX_DEFAULT_EXACT_TOP_K,
                    0,
                    64,
                ),
                "artist_mix_cluster_count": _bounded_artist_mix_int(
                    artist_mix_cluster_count,
                    ARTIST_MIX_DEFAULT_CLUSTER_COUNT,
                    1,
                    32,
                ),
                "artist_mix_dominant_isolation": _as_bool(
                    artist_mix_dominant_isolation,
                    ARTIST_MIX_DEFAULT_DOMINANT_ISOLATION,
                ),
                "artist_mix_dominant_threshold": _bounded_artist_mix_float(
                    artist_mix_dominant_threshold,
                    ARTIST_MIX_DEFAULT_DOMINANT_THRESHOLD,
                    0.0,
                    1.0,
                ),
            })
        saved_fields = _normalize_advanced_fields(ui_payload.get("advanced_fields", advanced_fields))
        effective_field_inputs = _advanced_field_input_values(ui_payload.get("field_inputs") or field_inputs)
        wildcard_mode_key = normalize_prompt_studio_wildcard_mode(wildcard_mode)
        effective_fields = _apply_advanced_field_inputs(saved_fields, effective_field_inputs)
        effective_fields, _wildcard = _expand_advanced_wildcard_fields(
            effective_fields,
            _seed_execution.execution_seed,
            wildcard_mode_key,
        )
        effective_fields = _translate_prompt_fields(effective_fields)
        prompt_data_parameters = _prompt_data_parameter_snapshot(
            self.INPUT_TYPES().get("required", {}),
            {
                "use_naia": use_naia,
                "consume_naia_on_queue": consume_naia_on_queue,
                "use_anima_mod_guidance": use_anima_mod_guidance,
                "pin_trigger_tags_to_front": pin_trigger_tags_to_front,
                "advanced_fields": advanced_fields,
                "use_negative_anima_mod_guidance": use_negative_anima_mod_guidance,
                "wildcard_mode": (
                    PROMPT_STUDIO_WILDCARD_MODE_LABELS[1]
                    if wildcard_mode_key == WILDCARD_MODE_SEQUENTIAL
                    else PROMPT_STUDIO_WILDCARD_MODE_LABELS[0]
                ),
                "wildcard_seed": wildcard_seed,
                "wildcard_seed_after_generate": _normalize_prompt_studio_wildcard_seed_control(
                    wildcard_seed_after_generate,
                    wildcard_mode,
                ),
                "resolution_bucket": resolution_bucket,
                "resolution_size": resolution_size,
                "resolution_custom_width": resolution_custom_width,
                "resolution_custom_height": resolution_custom_height,
                "artist_mix_mode": artist_mix_mode,
                "artist_mix_start_percent": artist_mix_start_percent,
                "artist_mix_strength_scale": artist_mix_strength_scale,
                "artist_mix_style_gain": artist_mix_style_gain,
                "artist_mix_rms_scale_cap": artist_mix_rms_scale_cap,
                "artist_mix_exact_top_k": artist_mix_exact_top_k,
                "artist_mix_cluster_count": artist_mix_cluster_count,
                "artist_mix_dominant_isolation": artist_mix_dominant_isolation,
                "artist_mix_dominant_threshold": artist_mix_dominant_threshold,
                **field_inputs,
            },
            ui_payload,
        )
        prompt_data_parameters["wildcard_seed"] = _seed_execution.execution_seed
        prompt_data = _build_advanced_prompt_data(
            compat_result,
            effective_fields,
            saved_fields,
            effective_field_inputs,
            str(ui_payload.get("resolution_bucket", resolution_bucket)),
            str(ui_payload.get("resolution_size", resolution_size)),
            _as_int(ui_payload.get("resolution_custom_width", resolution_custom_width), resolution_custom_width),
            _as_int(ui_payload.get("resolution_custom_height", resolution_custom_height), resolution_custom_height),
            str(ui_payload.get("wildcard_mode", wildcard_mode)),
            _seed_execution.execution_seed,
            str(ui_payload.get("wildcard_seed_after_generate", wildcard_seed_after_generate)),
            ui_payload,
            pin_trigger_tags_to_front,
            parameters=prompt_data_parameters,
            artist_mix_mode=artist_mix_mode,
            artist_mix_start_percent=artist_mix_start_percent,
            artist_mix_strength_scale=artist_mix_strength_scale,
            artist_mix_style_gain=artist_mix_style_gain,
            artist_mix_rms_scale_cap=artist_mix_rms_scale_cap,
            artist_mix_exact_top_k=artist_mix_exact_top_k,
            artist_mix_cluster_count=artist_mix_cluster_count,
            artist_mix_dominant_isolation=artist_mix_dominant_isolation,
            artist_mix_dominant_threshold=artist_mix_dominant_threshold,
        )
        return {
            **base,
            "result": (prompt_data,),
        }


class EasyUseAnimaPromptStudioExtend:
    """Extended Prompt Studio with numbered positive/negative prompt rows."""

    @classmethod
    def INPUT_TYPES(cls):
        required = {
            "fill_naia_prompt": ("BOOLEAN", {
                "default": False,
                "tooltip": (
                    "When enabled, slot 3 is filled from NAIA on each queue. "
                    "Saved-image workflows are written with this off and the current slot 3 text stored."
                ),
            }),
            "use_anima_mod_guidance": ("BOOLEAN", {
                "default": False,
                "tooltip": (
                    "true: positive output excludes slots 1-2 quality tags and sends them "
                    "through anima_mod_guidance_quality_tags."
                ),
            }),
            "pin_trigger_tags_to_front": ("BOOLEAN", {
                "default": False,
                "tooltip": "true: keep prompt correction trigger-like tags at the front where applicable.",
            }),
        }
        for name, _pane, _field_type, label, default, height in EXTEND_PROMPT_SLOT_SPECS:
            required[name] = ("STRING", {
                "multiline": True,
                "default": default,
                "tooltip": label,
                "placeholder": label,
                "height": height,
            })
        required["active_slots"] = ("STRING", {
            "default": json.dumps(["quality_tags_1", "general_tags_4", "trailing_tags_10"]),
            "tooltip": "Internal Prompt Studio Extend visible slot state.",
        })
        required["use_negative_anima_mod_guidance"] = ("BOOLEAN", {
            "default": False,
            "tooltip": (
                "true: negative output excludes negative quality slots and sends them "
                "through the negative Mod Guidance output."
            ),
        })
        return {
            "required": required,
            "hidden": {
                "workflow_prompt": "PROMPT",
                "extra_pnginfo": "EXTRA_PNGINFO",
                "unique_id": "UNIQUE_ID",
            },
        }

    RETURN_TYPES = (
        "STRING",
        "STRING",
        "STRING",
        "STRING",
        "BOOLEAN",
        "BOOLEAN",
        "STRING",
        "STRING",
    )
    RETURN_NAMES = (
        "positive_prompt",
        "negative_prompt",
        "anima_mod_guidance_quality_tags",
        "anima_mod_guidance_negative_prompt",
        "use_anima_mod_guidance",
        "use_negative_anima_mod_guidance",
        "metadata_prompt",
        "metadata_negative_prompt",
    )
    FUNCTION = "build"
    CATEGORY = "EasyUse Anima/Prompt"

    @classmethod
    def _widget_input_names(cls) -> list[str]:
        return list(cls.INPUT_TYPES()["required"].keys())

    @classmethod
    def IS_CHANGED(
        cls,
        fill_naia_prompt: bool = False,
        use_anima_mod_guidance: bool = False,
        pin_trigger_tags_to_front: bool = False,
        use_negative_anima_mod_guidance: bool = False,
        **kwargs,
    ):
        if _as_bool(fill_naia_prompt, False):
            return float("nan")
        return _stable_change_key({
            "mode": "prompt_studio_extend",
            "metadata_filter_words": resolve_metadata_filter_words(),
            "prompt_translation": _prompt_translation_change_key(),
            "use_anima_mod_guidance": _as_bool(use_anima_mod_guidance, False),
            "use_negative_anima_mod_guidance": _as_bool(use_negative_anima_mod_guidance, False),
            "pin_trigger_tags_to_front": _as_bool(pin_trigger_tags_to_front, False),
            "active_slots": str(kwargs.get("active_slots", "")),
            **{
                name: str(kwargs.get(name, ""))
                for name, *_rest in EXTEND_PROMPT_SLOT_SPECS
            },
        })

    @classmethod
    def _update_metadata_slots(
        cls,
        workflow_prompt,
        extra_pnginfo,
        unique_id,
        updates: dict[str, Any],
    ) -> None:
        node_id = _single_value(unique_id)
        if node_id is None:
            return
        node_id = str(node_id)

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

    @staticmethod
    @staticmethod
    def _active_slot_set(active_slots: Any) -> set[str] | None:
        if active_slots is None:
            return None
        parsed = active_slots
        if isinstance(active_slots, str):
            if not active_slots.strip():
                return None
            try:
                parsed = json.loads(active_slots)
            except json.JSONDecodeError:
                return None
        if not isinstance(parsed, list):
            return None
        valid_names = {name for name, *_rest in EXTEND_PROMPT_SLOT_SPECS}
        return {str(name) for name in parsed if str(name) in valid_names}

    @staticmethod
    def _fields_from_slots(values: dict[str, str], active_slots: Any = None) -> list[dict]:
        active_slot_names = EasyUseAnimaPromptStudioExtend._active_slot_set(active_slots)
        fields = []
        for name, pane, field_type, label, _default, height in EXTEND_PROMPT_SLOT_SPECS:
            if active_slot_names is not None and name not in active_slot_names:
                continue
            text = str(values.get(name, "") or "")
            fields.append({
                "id": name,
                "pane": pane,
                "type": field_type,
                "label": label,
                "text": text,
                "height": height,
                "enabled": bool(text.strip()),
            })
        return fields

    @staticmethod
    def _ui(slot_values: dict[str, str], fill_naia_prompt: bool, active_slots: Any = None):
        return {
            "prompt_studio_slots": [{
                **slot_values,
                "fill_naia_prompt": _as_bool(fill_naia_prompt, False),
                "active_slots": active_slots,
            }]
        }

    def build(
        self,
        fill_naia_prompt: bool,
        use_anima_mod_guidance: bool,
        pin_trigger_tags_to_front: bool,
        use_negative_anima_mod_guidance: bool = False,
        workflow_prompt=None,
        extra_pnginfo=None,
        unique_id=None,
        **slot_values,
    ):
        active_slots = slot_values.get("active_slots")
        values = {
            name: str(slot_values.get(name, default) or "")
            for name, _pane, _field_type, _label, default, _height in EXTEND_PROMPT_SLOT_SPECS
        }
        live_fill_naia = _as_bool(fill_naia_prompt, False)
        metadata_fill_naia = live_fill_naia

        if live_fill_naia:
            naia_settings = resolve_naia_settings()
            body = EasyUseAnimaNAIARandomPrompt._make_request_body(
                _as_bool(naia_settings["use_naia_settings"], True),
                naia_settings["pre_prompt"],
                naia_settings["post_prompt"],
                naia_settings["auto_hide"],
                naia_settings["preprocessing"],
            )
            resp = _post_random(
                naia_settings["host"],
                naia_settings["port"],
                body,
                allow_remote_api=bool(naia_settings.get("allow_remote_api", False)),
            )
            naia_prompt, _naia_negative, _naia_width, _naia_height = _parse_random_response(resp)
            values["naia_prompt_3"] = naia_prompt
            metadata_fill_naia = False

        if live_fill_naia:
            self._update_metadata_slots(
                workflow_prompt,
                extra_pnginfo,
                unique_id,
                {
                    "fill_naia_prompt": metadata_fill_naia,
                    "naia_prompt_3": values["naia_prompt_3"],
                },
            )

        effective_values = {
            name: _translate_prompt_text(value)
            for name, value in values.items()
        }
        result = _build_advanced_prompts(
            self._fields_from_slots(effective_values, active_slots),
            use_anima_mod_guidance,
            use_negative_anima_mod_guidance,
            pin_trigger_tags_to_front,
        )
        return {
            "ui": self._ui(values, live_fill_naia, active_slots),
            "result": result,
        }

__all__ = ()
