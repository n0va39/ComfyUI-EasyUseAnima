"""Execution adapter for the standalone Artist Mix conditioning node."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from ..common.values import _as_bool
from ..prompt.artist_mix import (
    ARTIST_MIX_DEFAULT_CLUSTER_COUNT,
    ARTIST_MIX_DEFAULT_DOMINANT_ISOLATION,
    ARTIST_MIX_DEFAULT_DOMINANT_THRESHOLD,
    ARTIST_MIX_DEFAULT_EXACT_TOP_K,
    ARTIST_MIX_DEFAULT_RMS_SCALE_CAP,
    ARTIST_MIX_DEFAULT_START_PERCENT,
    ARTIST_MIX_DEFAULT_STRENGTH_SCALE,
    ARTIST_MIX_DEFAULT_STYLE_GAIN,
    ARTIST_MIX_MODE_PROMPT,
    _artist_mix_inline_prompt,
    _artist_prompt_with_position,
    _bounded_artist_mix_float,
    _bounded_artist_mix_int,
    _join_artist_mix_source_prompts,
    _normalize_artist_mix_mode,
    _normalize_artist_tag_position,
)
from ..prompt.fields import _join_prompt_tokens

_ConditioningEncoder = Callable[..., Any]


def _encode_artist_mix_conditioning(
    clip: Any,
    prompt: str,
    artist_tags: str,
    artist_position: str,
    artist_mix_mode: str,
    artist_mix_start_percent: float,
    artist_mix_strength_scale: float,
    artist_mix_style_gain: float,
    artist_mix_rms_scale_cap: float,
    artist_mix_exact_top_k: int,
    artist_mix_cluster_count: int,
    artist_mix_dominant_isolation: bool,
    artist_mix_dominant_threshold: float,
    *,
    encode_with_comfy_clip: _ConditioningEncoder,
    encode_prompt_data_positive_conditioning: _ConditioningEncoder,
):
    position = _normalize_artist_tag_position(artist_position)
    mode = _normalize_artist_mix_mode(artist_mix_mode, ARTIST_MIX_MODE_PROMPT)
    base_prompt = _join_prompt_tokens(prompt)
    artist_prompt = _join_artist_mix_source_prompts(artist_tags)
    if mode == ARTIST_MIX_MODE_PROMPT:
        return (
            encode_with_comfy_clip(
                clip,
                _artist_prompt_with_position(
                    base_prompt,
                    _artist_mix_inline_prompt(artist_prompt),
                    position,
                ),
            ),
        )

    prompt_data = {
        "positive_prompt": base_prompt,
        "positive_without_artist_section": base_prompt,
        "artist_position": position,
        "artist_mix": {
            "enabled": True,
            "mode": mode,
            "artist_position": position,
            "base_source": "positive_without_artist_section",
            "base_prompt": base_prompt,
            "artist_prompt": artist_prompt,
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
        },
    }
    return (
        encode_prompt_data_positive_conditioning(
            clip,
            prompt_data,
            base_prompt,
            artist_mix_mode=mode,
            artist_mix_start_percent=artist_mix_start_percent,
            artist_mix_strength_scale=artist_mix_strength_scale,
            artist_mix_style_gain=artist_mix_style_gain,
            artist_mix_rms_scale_cap=artist_mix_rms_scale_cap,
            artist_mix_exact_top_k=artist_mix_exact_top_k,
            artist_mix_cluster_count=artist_mix_cluster_count,
            artist_mix_dominant_isolation=artist_mix_dominant_isolation,
            artist_mix_dominant_threshold=artist_mix_dominant_threshold,
        ),
    )


__all__ = ()
