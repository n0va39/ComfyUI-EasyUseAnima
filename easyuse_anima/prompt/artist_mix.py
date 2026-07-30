"""Compatibility facade for Artist Mix prompt and CONDITIONING services."""

from __future__ import annotations

from typing import Any

from .artist_mix_conditioning import (
    _artist_delta_rms_from_encoded as _artist_delta_rms_from_encoded,
)
from .artist_mix_conditioning import (
    _encode_artist_clustered as _encode_artist_clustered,
)
from .artist_mix_conditioning import (
    _encode_artist_delta_rms as _encode_artist_delta_rms,
)
from .artist_mix_conditioning import (
    _encode_prompt_data_positive_conditioning as _canonical_encode_prompt_data_positive_conditioning,
)
from .artist_mix_conditioning import (
    _encode_with_comfy_clip as _encode_with_comfy_clip,
)
from .artist_mix_conditioning import (
    _encoded_artist_conditionings as _encoded_artist_conditionings,
)
from .artist_mix_conditioning import (
    _fallback_artist_average_or_exact as _fallback_artist_average_or_exact,
)
from .artist_mix_conditioning import (
    _missing_host_helper as _missing_host_helper,
)
from .artist_mix_config import (
    _ARTIST_GROUP_RE as _ARTIST_GROUP_RE,
)
from .artist_mix_config import (
    _SECTION_SEPARATOR_RE as _SECTION_SEPARATOR_RE,
)
from .artist_mix_config import (
    _WEIGHTED_ARTIST_RE as _WEIGHTED_ARTIST_RE,
)
from .artist_mix_config import (
    ARTIST_MIX_CONTROL_KEY as ARTIST_MIX_CONTROL_KEY,
)
from .artist_mix_config import (
    ARTIST_MIX_DEFAULT_CLUSTER_COUNT as ARTIST_MIX_DEFAULT_CLUSTER_COUNT,
)
from .artist_mix_config import (
    ARTIST_MIX_DEFAULT_DOMINANT_ISOLATION as ARTIST_MIX_DEFAULT_DOMINANT_ISOLATION,
)
from .artist_mix_config import (
    ARTIST_MIX_DEFAULT_DOMINANT_THRESHOLD as ARTIST_MIX_DEFAULT_DOMINANT_THRESHOLD,
)
from .artist_mix_config import (
    ARTIST_MIX_DEFAULT_EXACT_TOP_K as ARTIST_MIX_DEFAULT_EXACT_TOP_K,
)
from .artist_mix_config import (
    ARTIST_MIX_DEFAULT_RMS_SCALE_CAP as ARTIST_MIX_DEFAULT_RMS_SCALE_CAP,
)
from .artist_mix_config import (
    ARTIST_MIX_DEFAULT_START_PERCENT as ARTIST_MIX_DEFAULT_START_PERCENT,
)
from .artist_mix_config import (
    ARTIST_MIX_DEFAULT_STRENGTH_SCALE as ARTIST_MIX_DEFAULT_STRENGTH_SCALE,
)
from .artist_mix_config import (
    ARTIST_MIX_DEFAULT_STYLE_GAIN as ARTIST_MIX_DEFAULT_STYLE_GAIN,
)
from .artist_mix_config import (
    ARTIST_MIX_EXACT_KEY as ARTIST_MIX_EXACT_KEY,
)
from .artist_mix_config import (
    ARTIST_MIX_INPUT_MODES as ARTIST_MIX_INPUT_MODES,
)
from .artist_mix_config import (
    ARTIST_MIX_MODE_AVERAGE as ARTIST_MIX_MODE_AVERAGE,
)
from .artist_mix_config import (
    ARTIST_MIX_MODE_AVERAGE_LATE_EXACT as ARTIST_MIX_MODE_AVERAGE_LATE_EXACT,
)
from .artist_mix_config import (
    ARTIST_MIX_MODE_CLUSTERED as ARTIST_MIX_MODE_CLUSTERED,
)
from .artist_mix_config import (
    ARTIST_MIX_MODE_COMPOSITE_EXACT as ARTIST_MIX_MODE_COMPOSITE_EXACT,
)
from .artist_mix_config import (
    ARTIST_MIX_MODE_DELTA_RMS as ARTIST_MIX_MODE_DELTA_RMS,
)
from .artist_mix_config import (
    ARTIST_MIX_MODE_DESCRIPTIONS as ARTIST_MIX_MODE_DESCRIPTIONS,
)
from .artist_mix_config import (
    ARTIST_MIX_MODE_EXACT as ARTIST_MIX_MODE_EXACT,
)
from .artist_mix_config import (
    ARTIST_MIX_MODE_FROM_PROMPT_DATA as ARTIST_MIX_MODE_FROM_PROMPT_DATA,
)
from .artist_mix_config import (
    ARTIST_MIX_MODE_HYBRID as ARTIST_MIX_MODE_HYBRID,
)
from .artist_mix_config import (
    ARTIST_MIX_MODE_LATE_EXACT as ARTIST_MIX_MODE_LATE_EXACT,
)
from .artist_mix_config import (
    ARTIST_MIX_MODE_OFF as ARTIST_MIX_MODE_OFF,
)
from .artist_mix_config import (
    ARTIST_MIX_MODE_PROMPT as ARTIST_MIX_MODE_PROMPT,
)
from .artist_mix_config import (
    ARTIST_MIX_MODE_SCHEDULED_AVERAGE as ARTIST_MIX_MODE_SCHEDULED_AVERAGE,
)
from .artist_mix_config import (
    ARTIST_MIX_MODES as ARTIST_MIX_MODES,
)
from .artist_mix_config import (
    ARTIST_MIX_SCHEDULE_KEY as ARTIST_MIX_SCHEDULE_KEY,
)
from .artist_mix_config import (
    ARTIST_MIX_STUDIO_MODES as ARTIST_MIX_STUDIO_MODES,
)
from .artist_mix_config import (
    ARTIST_TAG_POSITION_BACK as ARTIST_TAG_POSITION_BACK,
)
from .artist_mix_config import (
    ARTIST_TAG_POSITION_CORRECT as ARTIST_TAG_POSITION_CORRECT,
)
from .artist_mix_config import (
    ARTIST_TAG_POSITION_FRONT as ARTIST_TAG_POSITION_FRONT,
)
from .artist_mix_config import (
    ARTIST_TAG_POSITION_MODES as ARTIST_TAG_POSITION_MODES,
)
from .artist_mix_config import (
    _advanced_enabled_pane_fields as _advanced_enabled_pane_fields,
)
from .artist_mix_config import (
    _advanced_prompt_with_artist_override as _advanced_prompt_with_artist_override,
)
from .artist_mix_config import (
    _artist_group_token as _artist_group_token,
)
from .artist_mix_config import (
    _artist_mix_inline_prompt as _artist_mix_inline_prompt,
)
from .artist_mix_config import (
    _artist_mix_mode_tooltip as _artist_mix_mode_tooltip,
)
from .artist_mix_config import (
    _artist_mix_prompt_tags as _artist_mix_prompt_tags,
)
from .artist_mix_config import (
    _artist_tags_from_prompt as _artist_tags_from_prompt,
)
from .artist_mix_config import (
    _artist_variant_prompt_from_prompt_data as _artist_variant_prompt_from_prompt_data,
)
from .artist_mix_config import (
    _bounded_artist_mix_float as _bounded_artist_mix_float,
)
from .artist_mix_config import (
    _bounded_artist_mix_int as _bounded_artist_mix_int,
)
from .artist_mix_config import (
    _coalesce_artist_mix_items as _coalesce_artist_mix_items,
)
from .artist_mix_config import (
    _equal_artist_weights as _equal_artist_weights,
)
from .artist_mix_config import (
    _interpolate_artist_weights as _interpolate_artist_weights,
)
from .artist_mix_config import (
    _join_artist_mix_source_prompts as _join_artist_mix_source_prompts,
)
from .artist_mix_config import (
    _normalize_advanced_fields as _normalize_advanced_fields,
)
from .artist_mix_config import (
    _normalize_artist_mix_mode as _normalize_artist_mix_mode,
)
from .artist_mix_config import (
    _normalize_artist_tag_position as _normalize_artist_tag_position,
)
from .artist_mix_config import (
    _normalize_weight_values as _normalize_weight_values,
)
from .artist_mix_config import (
    _normalized_artist_weights as _normalized_artist_weights,
)
from .artist_mix_config import (
    _parse_artist_mix_entries as _parse_artist_mix_entries,
)
from .artist_mix_config import (
    _parse_artist_mix_group as _parse_artist_mix_group,
)
from .artist_mix_config import (
    _parse_artist_mix_items as _parse_artist_mix_items,
)
from .artist_mix_config import (
    _prompt_data_artist_base_prompt as _prompt_data_artist_base_prompt,
)
from .artist_mix_config import (
    _prompt_data_artist_mix_config as _prompt_data_artist_mix_config,
)
from .artist_mix_config import (
    _prompt_data_positive_fields as _prompt_data_positive_fields,
)
from .artist_mix_config import (
    _split_artist_mix_blocks as _split_artist_mix_blocks,
)
from .artist_mix_config import (
    _split_artist_mix_items as _split_artist_mix_items,
)
from .artist_mix_planning import (
    _artist_conditioning_feature as _artist_conditioning_feature,
)
from .artist_mix_planning import (
    _blend_conditionings as _blend_conditionings,
)
from .artist_mix_planning import (
    _conditionings_with_range as _conditionings_with_range,
)
from .artist_mix_planning import (
    _conditionings_with_strength as _conditionings_with_strength,
)
from .artist_mix_planning import (
    _conditionings_with_values as _conditionings_with_values,
)
from .artist_mix_planning import (
    _copy_conditioning_metadata as _copy_conditioning_metadata,
)
from .artist_mix_planning import (
    _encode_artist_average as _canonical_encode_artist_average,
)
from .artist_mix_planning import (
    _encode_artist_average_late_exact as _canonical_encode_artist_average_late_exact,
)
from .artist_mix_planning import (
    _encode_artist_composite_exact as _canonical_encode_artist_composite_exact,
)
from .artist_mix_planning import (
    _encode_artist_exact as _canonical_encode_artist_exact,
)
from .artist_mix_planning import (
    _encode_artist_hybrid as _canonical_encode_artist_hybrid,
)
from .artist_mix_planning import (
    _encode_artist_scheduled_average as _canonical_encode_artist_scheduled_average,
)
from .artist_mix_planning import (
    _greedy_cluster_encoded_artists as _greedy_cluster_encoded_artists,
)
from .artist_mix_planning import (
    _mark_artist_mix_conditioning as _mark_artist_mix_conditioning,
)
from .artist_mix_planning import (
    _pad_conditioning_tensor as _pad_conditioning_tensor,
)
from .contracts import PromptDataRead
from .data import _normalize_prompt_data as _normalize_prompt_data
from .fields import (
    _correct_builder_prompt as _correct_builder_prompt,
)
from .fields import (
    _join_prompt_tokens as _join_prompt_tokens,
)


def _artist_prompt_with_position(
    base_prompt: str,
    artist_prompt: str,
    artist_position: str = ARTIST_TAG_POSITION_CORRECT,
) -> str:
    artist_text = _join_prompt_tokens(artist_prompt)
    base_text = _join_prompt_tokens(base_prompt)
    if not artist_text:
        return base_text
    if not base_text:
        if (
            _normalize_artist_tag_position(artist_position)
            == ARTIST_TAG_POSITION_CORRECT
        ):
            return _correct_builder_prompt(artist_text, artist_overrides=artist_text)
        return artist_text

    position = _normalize_artist_tag_position(artist_position)
    if position == ARTIST_TAG_POSITION_FRONT:
        return _join_prompt_tokens(artist_text, base_text)
    if position == ARTIST_TAG_POSITION_BACK:
        return _join_prompt_tokens(base_text, artist_text)
    return _correct_builder_prompt(
        _join_prompt_tokens(base_text, artist_text),
        artist_overrides=artist_text,
    )


def _encode_artist_average(
    clip,
    data: PromptDataRead,
    base_prompt: str,
    artists: list[tuple[str, float]],
    weights: list[float] | None = None,
) -> list:
    return _canonical_encode_artist_average(
        clip,
        data,
        base_prompt,
        artists,
        weights,
        _blend_conditionings_override=_blend_conditionings,
        _encode_with_comfy_clip_override=_encode_with_comfy_clip,
    )


def _encode_artist_hybrid(
    clip,
    data: PromptDataRead,
    base_prompt: str,
    artists: list[tuple[str, float]],
    exact_top_k: int = ARTIST_MIX_DEFAULT_EXACT_TOP_K,
    style_gain: float = ARTIST_MIX_DEFAULT_STYLE_GAIN,
    rms_scale_cap: float = ARTIST_MIX_DEFAULT_RMS_SCALE_CAP,
    strength_scale: float = ARTIST_MIX_DEFAULT_STRENGTH_SCALE,
) -> list:
    return _canonical_encode_artist_hybrid(
        clip,
        data,
        base_prompt,
        artists,
        exact_top_k,
        style_gain,
        rms_scale_cap,
        strength_scale,
        _encode_artist_delta_rms_override=_encode_artist_delta_rms,
        _encode_with_comfy_clip_override=_encode_with_comfy_clip,
    )


def _encode_artist_exact(
    clip,
    data: PromptDataRead,
    base_prompt: str,
    artists: list[tuple[str, float]],
    start_percent: float | None = None,
    end_percent: float | None = None,
    strength_scale: float = 1.0,
    branch_strengths: list[float] | None = None,
) -> list:
    return _canonical_encode_artist_exact(
        clip,
        data,
        base_prompt,
        artists,
        start_percent,
        end_percent,
        strength_scale,
        branch_strengths,
        _encode_with_comfy_clip_override=_encode_with_comfy_clip,
    )


def _encode_artist_composite_exact(
    clip,
    data: PromptDataRead,
    base_prompt: str,
    artists: list[tuple[str, float]],
    start_percent: float | None = None,
    strength_scale: float = 1.0,
) -> list:
    return _canonical_encode_artist_composite_exact(
        clip,
        data,
        base_prompt,
        artists,
        start_percent,
        strength_scale,
        _encode_with_comfy_clip_override=_encode_with_comfy_clip,
    )


def _encode_artist_average_late_exact(
    clip,
    data: PromptDataRead,
    base_prompt: str,
    artists: list[tuple[str, float]],
    artist_mix: dict[str, Any],
) -> list:
    return _canonical_encode_artist_average_late_exact(
        clip,
        data,
        base_prompt,
        artists,
        artist_mix,
        _encode_with_comfy_clip_override=_encode_with_comfy_clip,
    )


def _encode_artist_scheduled_average(
    clip,
    data: PromptDataRead,
    base_prompt: str,
    artists: list[tuple[str, float]],
    artist_mix: dict[str, Any],
) -> list:
    return _canonical_encode_artist_scheduled_average(
        clip,
        data,
        base_prompt,
        artists,
        artist_mix,
        _encode_with_comfy_clip_override=_encode_with_comfy_clip,
    )


def _encode_prompt_data_positive_conditioning(
    clip,
    data: PromptDataRead,
    positive_prompt: str,
    artist_mix_mode: str = ARTIST_MIX_MODE_FROM_PROMPT_DATA,
    artist_mix_start_percent: float = ARTIST_MIX_DEFAULT_START_PERCENT,
    artist_mix_strength_scale: float = ARTIST_MIX_DEFAULT_STRENGTH_SCALE,
    artist_mix_style_gain: float = ARTIST_MIX_DEFAULT_STYLE_GAIN,
    artist_mix_rms_scale_cap: float = ARTIST_MIX_DEFAULT_RMS_SCALE_CAP,
    artist_mix_exact_top_k: int = ARTIST_MIX_DEFAULT_EXACT_TOP_K,
    artist_mix_cluster_count: int = ARTIST_MIX_DEFAULT_CLUSTER_COUNT,
    artist_mix_dominant_isolation: bool = ARTIST_MIX_DEFAULT_DOMINANT_ISOLATION,
    artist_mix_dominant_threshold: float = ARTIST_MIX_DEFAULT_DOMINANT_THRESHOLD,
    positive_execution_suffix: str = "",
) -> list:
    return _canonical_encode_prompt_data_positive_conditioning(
        clip,
        data,
        positive_prompt,
        artist_mix_mode,
        artist_mix_start_percent,
        artist_mix_strength_scale,
        artist_mix_style_gain,
        artist_mix_rms_scale_cap,
        artist_mix_exact_top_k,
        artist_mix_cluster_count,
        artist_mix_dominant_isolation,
        artist_mix_dominant_threshold,
        positive_execution_suffix,
        _blend_conditionings_override=_blend_conditionings,
        _encode_artist_delta_rms_override=_encode_artist_delta_rms,
        _encode_artist_clustered_override=_encode_artist_clustered,
    )


__all__ = ()
