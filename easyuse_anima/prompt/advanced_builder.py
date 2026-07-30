"""Advanced Prompt Studio typed Prompt Data assembly."""

from __future__ import annotations

from typing import Any, cast

from ..common.values import _as_bool, _as_int
from ..naia.resolution import DEFAULT_ADVANCED_RESOLUTION_BUCKET
from ..settings.service import resolve_metadata_filter_words
from ..wildcard.seed import normalize_seed
from .advanced_fields import (
    _advanced_artist_field_prompt,
    _advanced_enabled_pane_fields,
    _advanced_prompt_with_artist_override,
    _as_advanced_height,
)
from .artist_mix_primitives import (
    ARTIST_MIX_DEFAULT_CLUSTER_COUNT,
    ARTIST_MIX_DEFAULT_DOMINANT_ISOLATION,
    ARTIST_MIX_DEFAULT_DOMINANT_THRESHOLD,
    ARTIST_MIX_DEFAULT_EXACT_TOP_K,
    ARTIST_MIX_DEFAULT_RMS_SCALE_CAP,
    ARTIST_MIX_DEFAULT_START_PERCENT,
    ARTIST_MIX_DEFAULT_STRENGTH_SCALE,
    ARTIST_MIX_DEFAULT_STYLE_GAIN,
    ARTIST_MIX_MODE_OFF,
    ARTIST_MIX_MODE_PROMPT,
    _artist_mix_inline_prompt,
    _artist_tags_from_prompt,
    _bounded_artist_mix_float,
    _bounded_artist_mix_int,
    _normalize_artist_mix_mode,
    _parse_artist_mix_items,
)
from .contracts import (
    AdvancedField,
    JsonValue,
    PromptData,
    PromptDataCompatResult,
    PromptDataOutputs,
)
from .data import PROMPT_DATA_SCHEMA, PROMPT_DATA_TYPE, PROMPT_DATA_VERSION
from .fields import _filter_metadata_prompt

PROMPT_STUDIO_WILDCARD_MODE_LABELS = ("일반", "순차")
SEED_CONTROL_FIXED = "fixed"
SEED_CONTROL_RANDOMIZE = "randomize"
SEED_CONTROL_INCREMENT = "increment"

PROMPT_STUDIO_ADVANCED_RETURN_TYPES = (
    "STRING",
    "STRING",
    "STRING",
    "STRING",
    "BOOLEAN",
    "BOOLEAN",
    "STRING",
    "STRING",
    "INT",
    "INT",
)
PROMPT_STUDIO_ADVANCED_RETURN_NAMES = (
    "positive_prompt",
    "negative_prompt",
    "anima_mod_guidance_quality_tags",
    "anima_mod_guidance_negative_prompt",
    "use_anima_mod_guidance",
    "use_negative_anima_mod_guidance",
    "metadata_prompt",
    "metadata_negative_prompt",
    "width",
    "height",
)

def _advanced_prompt_data_fields(fields: list[AdvancedField]) -> list[AdvancedField]:
    output: list[AdvancedField] = []
    for field in fields:
        output.append(
            {
                "id": str(field.get("id") or ""),
                "pane": str(field.get("pane") or "positive"),
                "type": str(field.get("type") or "general"),
                "label": str(field.get("label") or ""),
                "text": str(field.get("text") or ""),
                "height": _as_advanced_height(field.get("height"), 72),
                "enabled": _as_bool(field.get("enabled"), True),
                "pin": _as_bool(field.get("pin"), field.get("type") == "trigger"),
            }
        )
    return output


def _build_advanced_prompt_data(
    compat_result: PromptDataCompatResult,
    effective_fields: list[AdvancedField],
    saved_fields: list[AdvancedField],
    field_inputs: dict[str, str],
    resolution_bucket: str,
    resolution_size: str,
    resolution_custom_width: int,
    resolution_custom_height: int,
    wildcard_mode: str,
    wildcard_seed: int,
    wildcard_seed_after_generate: str,
    wildcard_updates: dict[str, Any] | None = None,
    pin_trigger_tags_to_front: bool = False,
    parameters: dict[str, JsonValue] | None = None,
    artist_mix_mode: str = ARTIST_MIX_MODE_OFF,
    artist_mix_start_percent: float = ARTIST_MIX_DEFAULT_START_PERCENT,
    artist_mix_strength_scale: float = ARTIST_MIX_DEFAULT_STRENGTH_SCALE,
    artist_mix_style_gain: float = ARTIST_MIX_DEFAULT_STYLE_GAIN,
    artist_mix_rms_scale_cap: float = ARTIST_MIX_DEFAULT_RMS_SCALE_CAP,
    artist_mix_exact_top_k: int = ARTIST_MIX_DEFAULT_EXACT_TOP_K,
    artist_mix_cluster_count: int = ARTIST_MIX_DEFAULT_CLUSTER_COUNT,
    artist_mix_dominant_isolation: bool = ARTIST_MIX_DEFAULT_DOMINANT_ISOLATION,
    artist_mix_dominant_threshold: float = ARTIST_MIX_DEFAULT_DOMINANT_THRESHOLD,
) -> PromptData:
    (
        positive_prompt,
        negative_prompt,
        quality_tags,
        negative_quality_tags,
        use_anima_mod_guidance,
        use_negative_anima_mod_guidance,
        metadata_prompt,
        metadata_negative_prompt,
        width,
        height,
    ) = compat_result
    outputs = cast(
        PromptDataOutputs,
        {
            name: value
            for name, value in zip(PROMPT_STUDIO_ADVANCED_RETURN_NAMES, compat_result)
        },
    )
    positive_fields = _advanced_enabled_pane_fields(effective_fields, "positive")
    negative_fields = _advanced_enabled_pane_fields(effective_fields, "negative")
    positive_artist_prompt = _advanced_artist_field_prompt(effective_fields, "positive")
    negative_artist_prompt = _advanced_artist_field_prompt(effective_fields, "negative")
    positive_artist_inline_prompt = _artist_mix_inline_prompt(positive_artist_prompt)
    negative_artist_inline_prompt = _artist_mix_inline_prompt(negative_artist_prompt)
    force_pin_triggers = _as_bool(pin_trigger_tags_to_front, False)
    positive_without_artist = _advanced_prompt_with_artist_override(
        positive_fields,
        "",
        include_quality=not bool(use_anima_mod_guidance),
        force_pin_triggers=force_pin_triggers,
    )
    metadata_prompt_without_artist = _filter_metadata_prompt(
        _advanced_prompt_with_artist_override(
            positive_fields,
            "",
            include_quality=True,
            force_pin_triggers=force_pin_triggers,
        ),
        resolve_metadata_filter_words(),
    )
    negative_without_artist = _advanced_prompt_with_artist_override(
        negative_fields,
        "",
        include_quality=not bool(use_negative_anima_mod_guidance),
    )
    selected_artist_mix_mode = _normalize_artist_mix_mode(
        artist_mix_mode,
        ARTIST_MIX_MODE_OFF,
    )
    artist_mix_enabled = selected_artist_mix_mode not in {
        ARTIST_MIX_MODE_OFF,
        ARTIST_MIX_MODE_PROMPT,
    }
    prompt_data_artist_mix_mode = (
        ARTIST_MIX_MODE_PROMPT
        if selected_artist_mix_mode == ARTIST_MIX_MODE_OFF
        else selected_artist_mix_mode
    )
    prompt_data_positive_prompt = (
        positive_without_artist if artist_mix_enabled else positive_prompt
    )
    outputs["positive_prompt"] = prompt_data_positive_prompt
    wildcard_updates = wildcard_updates or {}
    parameters = parameters or {}
    prompt_data: PromptData = {
        "schema": PROMPT_DATA_SCHEMA,
        "version": PROMPT_DATA_VERSION,
        "type": PROMPT_DATA_TYPE,
        "source": "EasyUseAnimaPromptStudioAdvancedV2",
        "parameters": dict(parameters),
        "prompt": prompt_data_positive_prompt,
        "positive_prompt": prompt_data_positive_prompt,
        "global_prompt": positive_without_artist,
        "positive_without_artist_section": positive_without_artist,
        "negative_prompt": negative_prompt,
        "negative_without_artist_section": negative_without_artist,
        "metadata_prompt": metadata_prompt,
        "metadata_prompt_without_artist": metadata_prompt_without_artist,
        "metadata_negative_prompt": metadata_negative_prompt,
        "width": int(width),
        "height": int(height),
        "pin_trigger_tags_to_front": force_pin_triggers,
        "outputs": outputs,
        "mod_guidance": {
            "enabled": bool(use_anima_mod_guidance),
            "negative_enabled": bool(use_negative_anima_mod_guidance),
            "quality_tags": quality_tags,
            "negative_prompt": negative_quality_tags,
        },
        "anima_mod_guidance": {
            "use_positive": bool(use_anima_mod_guidance),
            "use_negative": bool(use_negative_anima_mod_guidance),
            "quality_tags": quality_tags,
            "negative_prompt": negative_quality_tags,
        },
        "artist": {
            "source": "advanced_artist_field",
            "handling": "separate" if artist_mix_enabled else "inline",
            "conditioning_mode": (
                prompt_data_artist_mix_mode if artist_mix_enabled else "none"
            ),
            "include_in_positive": not artist_mix_enabled,
            "text": positive_artist_inline_prompt,
            "weighted_text": positive_artist_prompt,
            "tags": _artist_tags_from_prompt(positive_artist_prompt),
            "positive_prompt": positive_artist_inline_prompt,
            "negative_prompt": negative_artist_inline_prompt,
            "positive_prompt_without_artist": positive_without_artist,
            "negative_prompt_without_artist": negative_without_artist,
            "positive_count_hint": len(_parse_artist_mix_items(positive_artist_prompt)),
            "negative_count_hint": len(_parse_artist_mix_items(negative_artist_prompt)),
        },
        "artist_mix": {
            "enabled": artist_mix_enabled,
            "mode": prompt_data_artist_mix_mode,
            "base_source": "positive_without_artist_section",
            "base_prompt": positive_without_artist,
            "start_percent": _bounded_artist_mix_float(
                artist_mix_start_percent,
                ARTIST_MIX_DEFAULT_START_PERCENT,
                0.0,
                1.0,
            ),
            "strength_scale": _bounded_artist_mix_float(
                artist_mix_strength_scale,
                ARTIST_MIX_DEFAULT_STRENGTH_SCALE,
                0.0,
                5.0,
            ),
            "style_gain": _bounded_artist_mix_float(
                artist_mix_style_gain,
                ARTIST_MIX_DEFAULT_STYLE_GAIN,
                0.0,
                3.0,
            ),
            "rms_scale_cap": _bounded_artist_mix_float(
                artist_mix_rms_scale_cap,
                ARTIST_MIX_DEFAULT_RMS_SCALE_CAP,
                1.0,
                5.0,
            ),
            "exact_top_k": _bounded_artist_mix_int(
                artist_mix_exact_top_k,
                ARTIST_MIX_DEFAULT_EXACT_TOP_K,
                0,
                64,
            ),
            "cluster_count": _bounded_artist_mix_int(
                artist_mix_cluster_count,
                ARTIST_MIX_DEFAULT_CLUSTER_COUNT,
                1,
                32,
            ),
            "dominant_isolation": _as_bool(
                artist_mix_dominant_isolation,
                ARTIST_MIX_DEFAULT_DOMINANT_ISOLATION,
            ),
            "dominant_threshold": _bounded_artist_mix_float(
                artist_mix_dominant_threshold,
                ARTIST_MIX_DEFAULT_DOMINANT_THRESHOLD,
                0.0,
                1.0,
            ),
            "artist_prompt": positive_artist_prompt,
            "artist_count_hint": len(_parse_artist_mix_items(positive_artist_prompt)),
        },
        "resolution": {
            "width": int(width),
            "height": int(height),
            "bucket": str(resolution_bucket or DEFAULT_ADVANCED_RESOLUTION_BUCKET),
            "size": str(resolution_size or ""),
            "custom_width": _as_int(resolution_custom_width, int(width)),
            "custom_height": _as_int(resolution_custom_height, int(height)),
        },
        "naia": {
            "use_naia": _as_bool(parameters.get("use_naia"), False),
            "consume_on_queue": _as_bool(
                parameters.get("consume_naia_on_queue"),
                True,
            ),
            "resolution_bucket": str(parameters.get("resolution_bucket") or ""),
        },
        "fields": _advanced_prompt_data_fields(effective_fields),
        "saved_fields": _advanced_prompt_data_fields(saved_fields),
        "field_inputs": dict(field_inputs),
        "wildcard": {
            "mode": str(wildcard_mode or PROMPT_STUDIO_WILDCARD_MODE_LABELS[0]),
            "seed": normalize_seed(wildcard_seed),
            "seed_after_generate": str(
                wildcard_seed_after_generate or SEED_CONTROL_FIXED
            ),
            "next_seed": wildcard_updates.get("wildcard_seed"),
            "used_keys": list(wildcard_updates.get("wildcard_used_keys") or []),
            "missing_keys": list(wildcard_updates.get("wildcard_missing_keys") or []),
        },
        "compatibility": {
            "return_names": list(PROMPT_STUDIO_ADVANCED_RETURN_NAMES),
            "return_types": list(PROMPT_STUDIO_ADVANCED_RETURN_TYPES),
        },
    }
    return prompt_data


__all__ = ()
