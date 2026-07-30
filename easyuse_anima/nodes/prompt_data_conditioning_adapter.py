"""Execution adapter for Prompt Data conditioning and model patching."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from ..prompt.artist_mix import (
    ARTIST_MIX_DEFAULT_CLUSTER_COUNT,
    ARTIST_MIX_DEFAULT_DOMINANT_ISOLATION,
    ARTIST_MIX_DEFAULT_DOMINANT_THRESHOLD,
    ARTIST_MIX_DEFAULT_EXACT_TOP_K,
    ARTIST_MIX_DEFAULT_RMS_SCALE_CAP,
    ARTIST_MIX_DEFAULT_START_PERCENT,
    ARTIST_MIX_DEFAULT_STRENGTH_SCALE,
    ARTIST_MIX_DEFAULT_STYLE_GAIN,
)
from ..prompt.conditioning import (
    ANIMA_MOD_GUIDANCE_MODE_FROM_PROMPT_DATA,
    ANIMA_MOD_GUIDANCE_PROFILE_OFF,
    _normalize_anima_mod_guidance_profile,
    _resolve_anima_mod_guidance_enabled,
)
from ..prompt.data import _advanced_outputs_from_prompt_data, _normalize_prompt_data

_Adapter = Callable[..., Any]


def _apply_prompt_data_conditioning(
    model: Any,
    clip: Any,
    prompt_data_value: str | dict,
    mod_guidance_mode: str,
    mod_w_profile: str,
    artist_mix_mode: str,
    artist_mix_start_percent: float = ARTIST_MIX_DEFAULT_START_PERCENT,
    artist_mix_strength_scale: float = ARTIST_MIX_DEFAULT_STRENGTH_SCALE,
    artist_mix_style_gain: float = ARTIST_MIX_DEFAULT_STYLE_GAIN,
    artist_mix_rms_scale_cap: float = ARTIST_MIX_DEFAULT_RMS_SCALE_CAP,
    artist_mix_exact_top_k: int = ARTIST_MIX_DEFAULT_EXACT_TOP_K,
    artist_mix_cluster_count: int = ARTIST_MIX_DEFAULT_CLUSTER_COUNT,
    artist_mix_dominant_isolation: bool = ARTIST_MIX_DEFAULT_DOMINANT_ISOLATION,
    artist_mix_dominant_threshold: float = ARTIST_MIX_DEFAULT_DOMINANT_THRESHOLD,
    *,
    encode_prompt_data_positive_conditioning: _Adapter,
    encode_with_comfy_clip: _Adapter,
    generate_empty_latent_with_comfy: _Adapter,
    apply_spectrum_anima_mod_guidance: _Adapter,
):
    prompt_data = _normalize_prompt_data(prompt_data_value)
    (
        positive_prompt,
        negative_prompt,
        quality_tags,
        quality_neg,
        use_anima_mod_guidance,
        use_negative_anima_mod_guidance,
        _metadata_prompt,
        _metadata_negative_prompt,
        width,
        height,
    ) = _advanced_outputs_from_prompt_data(prompt_data_value)

    positive = encode_prompt_data_positive_conditioning(
        clip,
        prompt_data,
        positive_prompt,
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
    negative = encode_with_comfy_clip(clip, negative_prompt)
    latent_image = generate_empty_latent_with_comfy(width, height)
    profile = _normalize_anima_mod_guidance_profile(mod_w_profile)
    use_mod_guidance = _resolve_anima_mod_guidance_enabled(
        use_anima_mod_guidance,
        str(mod_guidance_mode or ANIMA_MOD_GUIDANCE_MODE_FROM_PROMPT_DATA),
    )

    patched_model = model
    if use_mod_guidance and profile != ANIMA_MOD_GUIDANCE_PROFILE_OFF:
        patched_model = apply_spectrum_anima_mod_guidance(
            model,
            clip,
            positive,
            negative,
            quality_tags,
            quality_neg if use_negative_anima_mod_guidance else "",
            profile,
        )

    return (patched_model, positive, negative, latent_image)


__all__ = ()
