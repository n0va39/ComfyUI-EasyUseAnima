"""Artist Mix CONDITIONING encoding and dispatch services."""

from __future__ import annotations

from ..common.values import _as_bool
from ..infrastructure.comfy.wiring import resolve_comfy_host_helper
from . import artist_mix_planning as _planning
from .artist_mix_config import (
    ARTIST_MIX_CONTROL_KEY,
    ARTIST_MIX_DEFAULT_CLUSTER_COUNT,
    ARTIST_MIX_DEFAULT_DOMINANT_ISOLATION,
    ARTIST_MIX_DEFAULT_DOMINANT_THRESHOLD,
    ARTIST_MIX_DEFAULT_EXACT_TOP_K,
    ARTIST_MIX_DEFAULT_RMS_SCALE_CAP,
    ARTIST_MIX_DEFAULT_START_PERCENT,
    ARTIST_MIX_DEFAULT_STRENGTH_SCALE,
    ARTIST_MIX_DEFAULT_STYLE_GAIN,
    ARTIST_MIX_MODE_AVERAGE,
    ARTIST_MIX_MODE_AVERAGE_LATE_EXACT,
    ARTIST_MIX_MODE_CLUSTERED,
    ARTIST_MIX_MODE_COMPOSITE_EXACT,
    ARTIST_MIX_MODE_DELTA_RMS,
    ARTIST_MIX_MODE_EXACT,
    ARTIST_MIX_MODE_FROM_PROMPT_DATA,
    ARTIST_MIX_MODE_HYBRID,
    ARTIST_MIX_MODE_LATE_EXACT,
    ARTIST_MIX_MODE_PROMPT,
    ARTIST_MIX_MODE_SCHEDULED_AVERAGE,
    _artist_mix_prompt_tags,
    _artist_variant_prompt_from_prompt_data,
    _bounded_artist_mix_float,
    _bounded_artist_mix_int,
    _coalesce_artist_mix_items,
    _join_prompt_tokens,
    _normalize_artist_mix_mode,
    _normalized_artist_weights,
    _parse_artist_mix_items,
    _prompt_data_artist_base_prompt,
    _prompt_data_artist_mix_config,
)
from .contracts import PromptDataRead


def _missing_host_helper(name: str):
    raise RuntimeError(f"Artist Mix Comfy host helper is unavailable: {name}")


def _encode_with_comfy_clip(*args, **kwargs):
    helper = resolve_comfy_host_helper(
        "_encode_with_comfy_clip",
        _missing_host_helper,
    )
    return helper(*args, **kwargs)

def _encoded_artist_conditionings(
    clip,
    data: PromptDataRead,
    base_prompt: str,
    artists: list[tuple[str, float]],
) -> list:
    return [
        (
            tag,
            float(weight),
            _encode_with_comfy_clip(
                clip,
                _artist_variant_prompt_from_prompt_data(data, base_prompt, tag),
            ),
        )
        for tag, weight in artists
    ]


def _artist_delta_rms_from_encoded(
    base_conditioning,
    encoded_artists: list,
    weights: list[float],
    composite_conditioning=None,
    style_gain: float = ARTIST_MIX_DEFAULT_STYLE_GAIN,
    rms_scale_cap: float = ARTIST_MIX_DEFAULT_RMS_SCALE_CAP,
    branch_strength: float | None = None,
) -> list | None:
    if not encoded_artists or len(base_conditioning) != 1:
        return None
    if any(len(conditioning) != 1 for _tag, _weight, conditioning in encoded_artists):
        return None

    try:
        import torch  # type: ignore
    except Exception as exc:
        raise RuntimeError(
            "[EasyUseAnima] torch is required for artist mix delta_rms conditioning."
        ) from exc

    base_tensor, base_meta = base_conditioning[0]
    if not torch.is_tensor(base_tensor) or base_tensor.ndim != 3:
        return None
    artist_tensors = [
        conditioning[0][0] for _tag, _weight, conditioning in encoded_artists
    ]
    if any(
        not torch.is_tensor(tensor)
        or tensor.ndim != 3
        or tensor.shape[0] != base_tensor.shape[0]
        or tensor.shape[2] != base_tensor.shape[2]
        for tensor in artist_tensors
    ):
        return None

    max_length = max(
        [base_tensor.shape[1], *(tensor.shape[1] for tensor in artist_tensors)]
    )
    base_padded = _planning._pad_conditioning_tensor(base_tensor, max_length)
    mixed_delta = torch.zeros_like(base_padded)
    target_rms = None
    for (_tag, _weight, conditioning), alpha in zip(encoded_artists, weights):
        cond_padded = _planning._pad_conditioning_tensor(
            conditioning[0][0], max_length
        )
        delta = cond_padded - base_padded
        mixed_delta = mixed_delta + delta * float(alpha)
        rms = delta.float().pow(2).mean().sqrt()
        target_rms = (
            rms * float(alpha)
            if target_rms is None
            else target_rms + rms * float(alpha)
        )

    if target_rms is None:
        return None
    actual_rms = mixed_delta.float().pow(2).mean().sqrt().clamp_min(1e-6)
    rms_scale = torch.clamp(
        target_rms / actual_rms,
        1.0,
        max(1.0, float(rms_scale_cap)),
    )
    mixed_tensor = base_padded + mixed_delta * float(style_gain) * rms_scale

    metadata_source = (
        composite_conditioning[0][1]
        if composite_conditioning and len(composite_conditioning) == 1
        else base_meta
    )
    metadata = _planning._copy_conditioning_metadata(metadata_source)
    metadata.pop("strength", None)
    if branch_strength is not None:
        metadata["strength"] = max(0.0, float(branch_strength))

    base_pool = base_meta.get("pooled_output") if isinstance(base_meta, dict) else None
    artist_pools = [
        conditioning[0][1].get("pooled_output")
        for _tag, _weight, conditioning in encoded_artists
        if isinstance(conditioning[0][1], dict)
    ]
    if (
        torch.is_tensor(base_pool)
        and len(artist_pools) == len(encoded_artists)
        and all(
            torch.is_tensor(pool) and pool.shape == base_pool.shape
            for pool in artist_pools
        )
    ):
        mixed_pool_delta = torch.zeros_like(base_pool)
        target_pool_rms = None
        for pool, alpha in zip(artist_pools, weights):
            delta = pool - base_pool
            mixed_pool_delta = mixed_pool_delta + delta * float(alpha)
            rms = delta.float().pow(2).mean().sqrt()
            target_pool_rms = (
                rms * float(alpha)
                if target_pool_rms is None
                else target_pool_rms + rms * float(alpha)
            )
        if target_pool_rms is not None:
            actual_pool_rms = (
                mixed_pool_delta.float().pow(2).mean().sqrt().clamp_min(1e-6)
            )
            pool_scale = torch.clamp(
                target_pool_rms / actual_pool_rms,
                1.0,
                max(1.0, float(rms_scale_cap)),
            )
            metadata["pooled_output"] = (
                base_pool + mixed_pool_delta * float(style_gain) * pool_scale
            )
    elif isinstance(metadata, dict):
        metadata.pop("pooled_output", None)

    return [[mixed_tensor, metadata]]


def _fallback_artist_average_or_exact(
    clip,
    data: PromptDataRead,
    base_prompt: str,
    artists: list[tuple[str, float]],
) -> list:
    try:
        return _planning._encode_artist_average(
            clip,
            data,
            base_prompt,
            artists,
            _encode_with_comfy_clip_override=_encode_with_comfy_clip,
        )
    except Exception:
        return _planning._encode_artist_exact(
            clip,
            data,
            base_prompt,
            artists,
            _encode_with_comfy_clip_override=_encode_with_comfy_clip,
        )


def _encode_artist_delta_rms(
    clip,
    data: PromptDataRead,
    base_prompt: str,
    artists: list[tuple[str, float]],
    weights: list[float] | None = None,
    style_gain: float = ARTIST_MIX_DEFAULT_STYLE_GAIN,
    rms_scale_cap: float = ARTIST_MIX_DEFAULT_RMS_SCALE_CAP,
    branch_strength: float | None = None,
) -> list:
    artists = _coalesce_artist_mix_items(artists)
    if not artists:
        return _encode_with_comfy_clip(clip, base_prompt)
    mix_weights = (
        list(weights) if weights is not None else _normalized_artist_weights(artists)
    )
    try:
        base_conditioning = _encode_with_comfy_clip(clip, base_prompt)
        encoded = _encoded_artist_conditionings(clip, data, base_prompt, artists)
        composite_prompt = _artist_variant_prompt_from_prompt_data(
            data,
            base_prompt,
            _artist_mix_prompt_tags(artists, include_weights=True),
        )
        composite = _encode_with_comfy_clip(clip, composite_prompt)
        result = _artist_delta_rms_from_encoded(
            base_conditioning,
            encoded,
            mix_weights,
            composite if len(composite) == 1 else None,
            style_gain=style_gain,
            rms_scale_cap=rms_scale_cap,
            branch_strength=branch_strength,
        )
        if result is not None:
            return result
    except Exception:
        pass
    fallback = _fallback_artist_average_or_exact(clip, data, base_prompt, artists)
    if branch_strength is not None:
        return _planning._conditionings_with_strength(fallback, branch_strength)
    return fallback

def _encode_artist_clustered(
    clip,
    data: PromptDataRead,
    base_prompt: str,
    artists: list[tuple[str, float]],
    cluster_count: int = ARTIST_MIX_DEFAULT_CLUSTER_COUNT,
    style_gain: float = ARTIST_MIX_DEFAULT_STYLE_GAIN,
    rms_scale_cap: float = ARTIST_MIX_DEFAULT_RMS_SCALE_CAP,
    dominant_isolation: bool = ARTIST_MIX_DEFAULT_DOMINANT_ISOLATION,
    dominant_threshold: float = ARTIST_MIX_DEFAULT_DOMINANT_THRESHOLD,
    strength_scale: float = ARTIST_MIX_DEFAULT_STRENGTH_SCALE,
) -> list:
    artists = _coalesce_artist_mix_items(artists)
    if not artists:
        return _encode_with_comfy_clip(clip, base_prompt)
    total_weight = sum(weight for _tag, weight in artists)
    if total_weight <= 0:
        return _encode_with_comfy_clip(clip, base_prompt)

    threshold = _bounded_artist_mix_float(
        dominant_threshold,
        ARTIST_MIX_DEFAULT_DOMINANT_THRESHOLD,
        0.0,
        1.0,
    )
    dominant = [
        (tag, weight)
        for tag, weight in artists
        if dominant_isolation and (weight / total_weight) >= threshold
    ]
    remaining = [
        (tag, weight)
        for tag, weight in artists
        if not dominant_isolation or (weight / total_weight) < threshold
    ]
    target_cluster_count = _bounded_artist_mix_int(
        cluster_count,
        ARTIST_MIX_DEFAULT_CLUSTER_COUNT,
        1,
        32,
    )
    output = []
    if dominant:
        output.extend(
            _planning._encode_artist_exact(
                clip,
                data,
                base_prompt,
                dominant,
                branch_strengths=[
                    (weight / total_weight) * float(strength_scale)
                    for _tag, weight in dominant
                ],
                _encode_with_comfy_clip_override=_encode_with_comfy_clip,
            )
        )
    if not remaining:
        return output or _planning._encode_artist_exact(
            clip,
            data,
            base_prompt,
            artists,
            strength_scale=strength_scale,
            _encode_with_comfy_clip_override=_encode_with_comfy_clip,
        )
    if len(remaining) <= target_cluster_count:
        output.extend(
            _planning._encode_artist_exact(
                clip,
                data,
                base_prompt,
                remaining,
                branch_strengths=[
                    (weight / total_weight) * float(strength_scale)
                    for _tag, weight in remaining
                ],
                _encode_with_comfy_clip_override=_encode_with_comfy_clip,
            )
        )
        return output

    try:
        import torch  # type: ignore

        base_conditioning = _encode_with_comfy_clip(clip, base_prompt)
        encoded = _encoded_artist_conditionings(clip, data, base_prompt, remaining)
        base_meta = base_conditioning[0][1] if len(base_conditioning) == 1 else {}
        base_pool = (
            base_meta.get("pooled_output") if isinstance(base_meta, dict) else None
        )
        use_pooled = torch.is_tensor(base_pool) and all(
            len(encoded_artist[2]) == 1
            and isinstance(encoded_artist[2][0][1], dict)
            and torch.is_tensor(encoded_artist[2][0][1].get("pooled_output"))
            and encoded_artist[2][0][1].get("pooled_output").shape == base_pool.shape
            for encoded_artist in encoded
        )
        features = [
            _planning._artist_conditioning_feature(
                torch, base_conditioning, encoded_artist, use_pooled
            )
            for encoded_artist in encoded
        ]
        if any(feature is None for feature in features):
            raise RuntimeError("missing cluster feature")
        clusters = _planning._greedy_cluster_encoded_artists(
            torch, encoded, features, target_cluster_count
        )
        for cluster in clusters:
            cluster_weight = max(0.0, float(cluster["weight"]))
            if cluster_weight <= 0:
                continue
            cluster_result = _artist_delta_rms_from_encoded(
                base_conditioning,
                cluster["items"],
                [item[1] / cluster_weight for item in cluster["items"]],
                None,
                style_gain=style_gain,
                rms_scale_cap=rms_scale_cap,
                branch_strength=(cluster_weight / total_weight) * float(strength_scale),
            )
            if cluster_result is None:
                raise RuntimeError("cluster delta_rms failed")
            output.extend(cluster_result)
        return output or _planning._encode_artist_hybrid(
            clip,
            data,
            base_prompt,
            artists,
            exact_top_k=ARTIST_MIX_DEFAULT_EXACT_TOP_K,
            style_gain=style_gain,
            rms_scale_cap=rms_scale_cap,
            strength_scale=strength_scale,
            _encode_artist_delta_rms_override=_encode_artist_delta_rms,
            _encode_with_comfy_clip_override=_encode_with_comfy_clip,
        )
    except Exception:
        return _planning._encode_artist_hybrid(
            clip,
            data,
            base_prompt,
            artists,
            exact_top_k=ARTIST_MIX_DEFAULT_EXACT_TOP_K,
            style_gain=style_gain,
            rms_scale_cap=rms_scale_cap,
            strength_scale=strength_scale,
            _encode_artist_delta_rms_override=_encode_artist_delta_rms,
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
    *,
    _blend_conditionings_override=None,
    _encode_artist_delta_rms_override=None,
    _encode_artist_clustered_override=None,
) -> list:
    blend_conditionings = (
        _blend_conditionings_override or _planning._blend_conditionings
    )
    encode_artist_delta_rms = (
        _encode_artist_delta_rms_override or _encode_artist_delta_rms
    )
    encode_artist_clustered = (
        _encode_artist_clustered_override or _encode_artist_clustered
    )
    execution_suffix = _join_prompt_tokens(positive_execution_suffix)
    execution_positive_prompt = _join_prompt_tokens(
        positive_prompt,
        execution_suffix,
    )
    if execution_suffix:
        data = {
            **data,
            "_artist_mix_execution_positive_suffix": execution_suffix,
        }
    artist_mix = _prompt_data_artist_mix_config(
        data,
        artist_mix_mode,
        artist_mix_start_percent,
        artist_mix_strength_scale,
        artist_mix_style_gain,
        artist_mix_rms_scale_cap,
        artist_mix_exact_top_k,
        artist_mix_cluster_count,
        artist_mix_dominant_isolation,
        artist_mix_dominant_threshold,
    )
    artists = _coalesce_artist_mix_items(
        _parse_artist_mix_items(str(artist_mix.get("artist_prompt") or ""))
    )
    if (
        not artist_mix.get("enabled")
        or artist_mix.get("mode") == ARTIST_MIX_MODE_PROMPT
    ):
        return _encode_with_comfy_clip(clip, execution_positive_prompt)

    base_prompt = _join_prompt_tokens(
        _prompt_data_artist_base_prompt(data, positive_prompt),
        execution_suffix,
    )
    if not artists:
        return _encode_with_comfy_clip(clip, base_prompt)

    mode = _normalize_artist_mix_mode(artist_mix.get("mode"), ARTIST_MIX_MODE_PROMPT)
    if mode == ARTIST_MIX_MODE_AVERAGE:
        return _planning._encode_artist_average(
            clip,
            data,
            base_prompt,
            artists,
            _blend_conditionings_override=blend_conditionings,
            _encode_with_comfy_clip_override=_encode_with_comfy_clip,
        )
    if mode == ARTIST_MIX_MODE_DELTA_RMS:
        return _planning._mark_artist_mix_conditioning(
            encode_artist_delta_rms(
                clip,
                data,
                base_prompt,
                artists,
                style_gain=_bounded_artist_mix_float(
                    artist_mix.get("style_gain"),
                    ARTIST_MIX_DEFAULT_STYLE_GAIN,
                    0.0,
                    3.0,
                ),
                rms_scale_cap=_bounded_artist_mix_float(
                    artist_mix.get("rms_scale_cap"),
                    ARTIST_MIX_DEFAULT_RMS_SCALE_CAP,
                    1.0,
                    5.0,
                ),
            ),
            ARTIST_MIX_CONTROL_KEY,
        )
    if mode == ARTIST_MIX_MODE_HYBRID:
        return _planning._mark_artist_mix_conditioning(
            _planning._encode_artist_hybrid(
                clip,
                data,
                base_prompt,
                artists,
                exact_top_k=_bounded_artist_mix_int(
                    artist_mix.get("exact_top_k"),
                    ARTIST_MIX_DEFAULT_EXACT_TOP_K,
                    0,
                    64,
                ),
                style_gain=_bounded_artist_mix_float(
                    artist_mix.get("style_gain"),
                    ARTIST_MIX_DEFAULT_STYLE_GAIN,
                    0.0,
                    3.0,
                ),
                rms_scale_cap=_bounded_artist_mix_float(
                    artist_mix.get("rms_scale_cap"),
                    ARTIST_MIX_DEFAULT_RMS_SCALE_CAP,
                    1.0,
                    5.0,
                ),
                strength_scale=_bounded_artist_mix_float(
                    artist_mix.get("strength_scale"),
                    ARTIST_MIX_DEFAULT_STRENGTH_SCALE,
                    0.0,
                    5.0,
                ),
                _encode_artist_delta_rms_override=encode_artist_delta_rms,
                _encode_with_comfy_clip_override=_encode_with_comfy_clip,
            ),
            ARTIST_MIX_CONTROL_KEY,
        )
    if mode == ARTIST_MIX_MODE_CLUSTERED:
        return _planning._mark_artist_mix_conditioning(
            encode_artist_clustered(
                clip,
                data,
                base_prompt,
                artists,
                cluster_count=_bounded_artist_mix_int(
                    artist_mix.get("cluster_count"),
                    ARTIST_MIX_DEFAULT_CLUSTER_COUNT,
                    1,
                    32,
                ),
                style_gain=_bounded_artist_mix_float(
                    artist_mix.get("style_gain"),
                    ARTIST_MIX_DEFAULT_STYLE_GAIN,
                    0.0,
                    3.0,
                ),
                rms_scale_cap=_bounded_artist_mix_float(
                    artist_mix.get("rms_scale_cap"),
                    ARTIST_MIX_DEFAULT_RMS_SCALE_CAP,
                    1.0,
                    5.0,
                ),
                dominant_isolation=_as_bool(
                    artist_mix.get("dominant_isolation"),
                    ARTIST_MIX_DEFAULT_DOMINANT_ISOLATION,
                ),
                dominant_threshold=_bounded_artist_mix_float(
                    artist_mix.get("dominant_threshold"),
                    ARTIST_MIX_DEFAULT_DOMINANT_THRESHOLD,
                    0.0,
                    1.0,
                ),
                strength_scale=_bounded_artist_mix_float(
                    artist_mix.get("strength_scale"),
                    ARTIST_MIX_DEFAULT_STRENGTH_SCALE,
                    0.0,
                    5.0,
                ),
            ),
            ARTIST_MIX_CONTROL_KEY,
        )
    if mode == ARTIST_MIX_MODE_EXACT:
        return _planning._mark_artist_mix_conditioning(
            _planning._encode_artist_exact(
                clip,
                data,
                base_prompt,
                artists,
                strength_scale=_bounded_artist_mix_float(
                    artist_mix.get("strength_scale"),
                    ARTIST_MIX_DEFAULT_STRENGTH_SCALE,
                    0.0,
                    5.0,
                ),
                _encode_with_comfy_clip_override=_encode_with_comfy_clip,
            ),
            ARTIST_MIX_CONTROL_KEY,
        )
    if mode == ARTIST_MIX_MODE_COMPOSITE_EXACT:
        return _planning._mark_artist_mix_conditioning(
            _planning._encode_artist_composite_exact(
                clip,
                data,
                base_prompt,
                artists,
                strength_scale=_bounded_artist_mix_float(
                    artist_mix.get("strength_scale"),
                    ARTIST_MIX_DEFAULT_STRENGTH_SCALE,
                    0.0,
                    5.0,
                ),
                _encode_with_comfy_clip_override=_encode_with_comfy_clip,
            ),
            ARTIST_MIX_CONTROL_KEY,
        )
    if mode == ARTIST_MIX_MODE_LATE_EXACT:
        return _planning._mark_artist_mix_conditioning(
            _encode_with_comfy_clip(clip, base_prompt)
            + _planning._encode_artist_exact(
                clip,
                data,
                base_prompt,
                artists,
                start_percent=_bounded_artist_mix_float(
                    artist_mix.get("start_percent"),
                    ARTIST_MIX_DEFAULT_START_PERCENT,
                    0.0,
                    1.0,
                ),
                end_percent=1.0,
                strength_scale=_bounded_artist_mix_float(
                    artist_mix.get("strength_scale"),
                    ARTIST_MIX_DEFAULT_STRENGTH_SCALE,
                    0.0,
                    5.0,
                ),
                _encode_with_comfy_clip_override=_encode_with_comfy_clip,
            ),
            ARTIST_MIX_CONTROL_KEY,
        )
    if mode == ARTIST_MIX_MODE_AVERAGE_LATE_EXACT:
        return _planning._mark_artist_mix_conditioning(
            _planning._encode_artist_average_late_exact(
                clip,
                data,
                base_prompt,
                artists,
                artist_mix,
                _encode_with_comfy_clip_override=_encode_with_comfy_clip,
            ),
            ARTIST_MIX_CONTROL_KEY,
        )
    if mode == ARTIST_MIX_MODE_SCHEDULED_AVERAGE:
        return _planning._mark_artist_mix_conditioning(
            _planning._encode_artist_scheduled_average(
                clip,
                data,
                base_prompt,
                artists,
                artist_mix,
                _encode_with_comfy_clip_override=_encode_with_comfy_clip,
            ),
            ARTIST_MIX_CONTROL_KEY,
        )
    return _encode_with_comfy_clip(clip, execution_positive_prompt)


__all__ = ()
