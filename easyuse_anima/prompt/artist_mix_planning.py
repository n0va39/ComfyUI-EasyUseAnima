"""Artist Mix strategy planning and scheduled composition services."""

from __future__ import annotations

from typing import Any

from .artist_mix_config import (
    ARTIST_MIX_DEFAULT_EXACT_TOP_K,
    ARTIST_MIX_DEFAULT_RMS_SCALE_CAP,
    ARTIST_MIX_DEFAULT_START_PERCENT,
    ARTIST_MIX_DEFAULT_STRENGTH_SCALE,
    ARTIST_MIX_DEFAULT_STYLE_GAIN,
    ARTIST_MIX_EXACT_KEY,
    ARTIST_MIX_SCHEDULE_KEY,
    _artist_mix_prompt_tags,
    _artist_variant_prompt_from_prompt_data,
    _bounded_artist_mix_float,
    _bounded_artist_mix_int,
    _coalesce_artist_mix_items,
    _equal_artist_weights,
    _interpolate_artist_weights,
    _normalized_artist_weights,
)
from .contracts import PromptDataRead


def _require_callback(callback, name: str):
    if callback is None:
        raise RuntimeError(f"Artist Mix planning callback is required: {name}")
    return callback


def _copy_conditioning_metadata(metadata) -> dict[str, Any]:
    try:
        import torch  # type: ignore
    except Exception:
        torch = None  # type: ignore

    result = dict(metadata or {})
    if torch is None:
        return result
    for key, value in list(result.items()):
        if torch.is_tensor(value):
            result[key] = value.clone()
    return result


def _pad_conditioning_tensor(tensor, target_length: int):
    if tensor.shape[1] >= target_length:
        return tensor[:, :target_length]
    try:
        import torch  # type: ignore
    except Exception as exc:
        raise RuntimeError(
            "[EasyUseAnima] torch is required for artist mix conditioning."
        ) from exc
    padding = torch.zeros(
        (tensor.shape[0], target_length - tensor.shape[1], tensor.shape[2]),
        dtype=tensor.dtype,
        device=tensor.device,
    )
    return torch.cat([tensor, padding], dim=1)


def _blend_conditionings(
    conditionings: list, weights: list[float], composite_conditioning=None
) -> list:
    if not conditionings:
        return []
    if len(conditionings) == 1:
        return list(conditionings[0])
    expected_len = len(conditionings[0])
    if any(len(conditioning) != expected_len for conditioning in conditionings):
        raise RuntimeError(
            "[EasyUseAnima] artist mix average requires CLIP conditionings with the same length."
        )

    try:
        import torch  # type: ignore
    except Exception as exc:
        raise RuntimeError(
            "[EasyUseAnima] torch is required for artist mix conditioning."
        ) from exc

    blended = []
    for entry_index in range(expected_len):
        first_tensor = conditionings[0][entry_index][0]
        max_length = max(
            conditioning[entry_index][0].shape[1] for conditioning in conditionings
        )
        if any(
            conditioning[entry_index][0].shape[0] != first_tensor.shape[0]
            or conditioning[entry_index][0].shape[2] != first_tensor.shape[2]
            for conditioning in conditionings
        ):
            raise RuntimeError(
                "[EasyUseAnima] artist mix average requires matching CLIP embedding sizes."
            )

        tensor = torch.zeros(
            (first_tensor.shape[0], max_length, first_tensor.shape[2]),
            dtype=first_tensor.dtype,
            device=first_tensor.device,
        )
        for conditioning, weight in zip(conditionings, weights):
            tensor = tensor + _pad_conditioning_tensor(
                conditioning[entry_index][0], max_length
            ) * float(weight)

        metadata_source = (
            composite_conditioning[entry_index][1]
            if composite_conditioning and len(composite_conditioning) > entry_index
            else conditionings[0][entry_index][1]
        )
        metadata = _copy_conditioning_metadata(metadata_source)
        pooled_candidates = [
            conditioning[entry_index][1].get("pooled_output")
            for conditioning in conditionings
            if isinstance(conditioning[entry_index][1], dict)
        ]
        if pooled_candidates and all(
            torch.is_tensor(value) for value in pooled_candidates
        ):
            pooled_shape = pooled_candidates[0].shape
            if all(value.shape == pooled_shape for value in pooled_candidates):
                pooled_output = torch.zeros_like(pooled_candidates[0])
                for value, weight in zip(pooled_candidates, weights):
                    pooled_output = pooled_output + value * float(weight)
                metadata["pooled_output"] = pooled_output
        elif torch.is_tensor(metadata.get("pooled_output")):
            metadata.pop("pooled_output", None)
        metadata.pop("strength", None)
        blended.append([tensor, metadata])
    return blended




def _conditionings_with_values(conditioning, values: dict[str, Any]) -> list:
    output = []
    for tensor, metadata in conditioning or []:
        item_metadata = _copy_conditioning_metadata(metadata)
        item_metadata.update(values)
        output.append([tensor, item_metadata])
    return output


def _conditionings_with_range(
    conditioning, start_percent: float, end_percent: float = 1.0
) -> list:
    start = max(0.0, min(1.0, float(start_percent)))
    end = max(start, min(1.0, float(end_percent)))
    return _conditionings_with_values(
        conditioning, {"start_percent": start, "end_percent": end}
    )


def _conditionings_with_strength(conditioning, strength: float) -> list:
    return _conditionings_with_values(
        conditioning, {"strength": max(0.0, float(strength))}
    )


def _mark_artist_mix_conditioning(conditioning, key: str) -> list:
    return _conditionings_with_values(conditioning, {key: True})


# Imported after low-level encoders so either module remains directly importable.


def _encode_artist_exact(
    clip,
    data: PromptDataRead,
    base_prompt: str,
    artists: list[tuple[str, float]],
    start_percent: float | None = None,
    end_percent: float | None = None,
    strength_scale: float = 1.0,
    branch_strengths: list[float] | None = None,
    *,
    _encode_with_comfy_clip_override=None,
) -> list:
    encode_with_comfy_clip = _require_callback(
        _encode_with_comfy_clip_override,
        "_encode_with_comfy_clip",
    )
    exact = []
    strengths = (
        [max(0.0, float(value)) for value in branch_strengths]
        if branch_strengths is not None
        else [
            float(weight) * float(strength_scale)
            for weight in _normalized_artist_weights(artists)
        ]
    )
    for (tag, _weight), strength in zip(artists, strengths):
        variant_prompt = _artist_variant_prompt_from_prompt_data(data, base_prompt, tag)
        for tensor, metadata in encode_with_comfy_clip(clip, variant_prompt):
            item_metadata = _copy_conditioning_metadata(metadata)
            item_metadata["strength"] = float(strength)
            if start_percent is not None:
                item_metadata["start_percent"] = max(
                    0.0, min(1.0, float(start_percent))
                )
            if end_percent is not None:
                item_metadata["end_percent"] = max(
                    item_metadata.get("start_percent", 0.0),
                    min(1.0, float(end_percent)),
                )
            item_metadata[ARTIST_MIX_EXACT_KEY] = True
            exact.append([tensor, item_metadata])
    return exact or encode_with_comfy_clip(clip, base_prompt)


def _encode_artist_average(
    clip,
    data: PromptDataRead,
    base_prompt: str,
    artists: list[tuple[str, float]],
    weights: list[float] | None = None,
    *,
    _blend_conditionings_override=None,
    _encode_with_comfy_clip_override=None,
) -> list:
    encode_with_comfy_clip = _require_callback(
        _encode_with_comfy_clip_override,
        "_encode_with_comfy_clip",
    )
    mix_weights = (
        list(weights) if weights is not None else _normalized_artist_weights(artists)
    )
    encoded = [
        encode_with_comfy_clip(
            clip,
            _artist_variant_prompt_from_prompt_data(data, base_prompt, tag),
        )
        for tag, _weight in artists
    ]
    if any(len(conditioning) != 1 for conditioning in encoded):
        return _encode_artist_exact(
            clip,
            data,
            base_prompt,
            artists,
            _encode_with_comfy_clip_override=encode_with_comfy_clip,
        )

    composite_prompt = _artist_variant_prompt_from_prompt_data(
        data,
        base_prompt,
        _artist_mix_prompt_tags(artists, include_weights=True),
    )
    composite = encode_with_comfy_clip(clip, composite_prompt)
    if len(composite) != 1:
        composite = None
    blend_conditionings = _blend_conditionings_override or _blend_conditionings
    return blend_conditionings(encoded, mix_weights, composite)


def _encode_artist_hybrid(
    clip,
    data: PromptDataRead,
    base_prompt: str,
    artists: list[tuple[str, float]],
    exact_top_k: int = ARTIST_MIX_DEFAULT_EXACT_TOP_K,
    style_gain: float = ARTIST_MIX_DEFAULT_STYLE_GAIN,
    rms_scale_cap: float = ARTIST_MIX_DEFAULT_RMS_SCALE_CAP,
    strength_scale: float = ARTIST_MIX_DEFAULT_STRENGTH_SCALE,
    *,
    _encode_artist_delta_rms_override=None,
    _encode_with_comfy_clip_override=None,
) -> list:
    encode_artist_delta_rms = _require_callback(
        _encode_artist_delta_rms_override,
        "_encode_artist_delta_rms",
    )
    encode_with_comfy_clip = _require_callback(
        _encode_with_comfy_clip_override,
        "_encode_with_comfy_clip",
    )
    artists = _coalesce_artist_mix_items(artists)
    if not artists:
        return encode_with_comfy_clip(clip, base_prompt)
    total_weight = sum(weight for _tag, weight in artists)
    if total_weight <= 0:
        return encode_with_comfy_clip(clip, base_prompt)

    sorted_artists = sorted(artists, key=lambda item: item[1], reverse=True)
    top_k = _bounded_artist_mix_int(exact_top_k, ARTIST_MIX_DEFAULT_EXACT_TOP_K, 0, 64)
    if top_k >= len(sorted_artists):
        return _encode_artist_exact(
            clip,
            data,
            base_prompt,
            sorted_artists,
            strength_scale=strength_scale,
            _encode_with_comfy_clip_override=encode_with_comfy_clip,
        )

    top = sorted_artists[:top_k]
    tail = sorted_artists[top_k:]
    output = []
    if top:
        output.extend(
            _encode_artist_exact(
                clip,
                data,
                base_prompt,
                top,
                branch_strengths=[
                    (weight / total_weight) * float(strength_scale)
                    for _tag, weight in top
                ],
                _encode_with_comfy_clip_override=encode_with_comfy_clip,
            )
        )
    if tail:
        tail_total = sum(weight for _tag, weight in tail)
        if tail_total <= 0:
            return _encode_artist_exact(
                clip,
                data,
                base_prompt,
                sorted_artists,
                strength_scale=strength_scale,
                _encode_with_comfy_clip_override=encode_with_comfy_clip,
            )
        try:
            output.extend(
                encode_artist_delta_rms(
                    clip,
                    data,
                    base_prompt,
                    tail,
                    weights=[weight / tail_total for _tag, weight in tail],
                    style_gain=style_gain,
                    rms_scale_cap=rms_scale_cap,
                    branch_strength=(tail_total / total_weight) * float(strength_scale),
                )
            )
        except Exception:
            return _encode_artist_exact(
                clip,
                data,
                base_prompt,
                sorted_artists,
                strength_scale=strength_scale,
                _encode_with_comfy_clip_override=encode_with_comfy_clip,
            )
    return output or _encode_artist_exact(
        clip,
        data,
        base_prompt,
        sorted_artists,
        strength_scale=strength_scale,
        _encode_with_comfy_clip_override=encode_with_comfy_clip,
    )


def _artist_conditioning_feature(
    torch, base_conditioning, encoded_artist, use_pooled: bool
):
    if len(base_conditioning) != 1 or len(encoded_artist[2]) != 1:
        return None
    base_tensor, base_meta = base_conditioning[0]
    cond_tensor, metadata = encoded_artist[2][0]
    if not torch.is_tensor(base_tensor) or not torch.is_tensor(cond_tensor):
        return None
    base_pool = base_meta.get("pooled_output") if isinstance(base_meta, dict) else None
    pool = metadata.get("pooled_output") if isinstance(metadata, dict) else None
    if (
        use_pooled
        and torch.is_tensor(base_pool)
        and torch.is_tensor(pool)
        and base_pool.shape == pool.shape
    ):
        feature = (pool - base_pool).float().flatten()
    elif (
        base_tensor.ndim == 3
        and cond_tensor.ndim == 3
        and base_tensor.shape[0] == cond_tensor.shape[0]
        and base_tensor.shape[2] == cond_tensor.shape[2]
    ):
        max_length = max(base_tensor.shape[1], cond_tensor.shape[1])
        feature = (
            (
                _pad_conditioning_tensor(cond_tensor, max_length)
                - _pad_conditioning_tensor(base_tensor, max_length)
            )
            .float()
            .mean(dim=1)
            .flatten()
        )
    else:
        return None
    norm = torch.linalg.vector_norm(feature).clamp_min(1e-6)
    return feature / norm


def _greedy_cluster_encoded_artists(
    torch, encoded_artists: list, features: list, cluster_count: int
) -> list:
    clusters = [
        {
            "items": [encoded],
            "weight": max(0.0, float(encoded[1])),
            "feature": feature,
        }
        for encoded, feature in zip(encoded_artists, features)
    ]
    target_count = max(1, min(int(cluster_count), len(clusters)))
    while len(clusters) > target_count:
        best_pair = (0, 1)
        best_similarity = None
        for left in range(len(clusters)):
            for right in range(left + 1, len(clusters)):
                similarity = torch.dot(
                    clusters[left]["feature"], clusters[right]["feature"]
                ).item()
                if best_similarity is None or similarity > best_similarity:
                    best_similarity = similarity
                    best_pair = (left, right)
        left, right = best_pair
        first = clusters[left]
        second = clusters[right]
        merged_weight = first["weight"] + second["weight"]
        merged_feature = (
            first["feature"] * first["weight"] + second["feature"] * second["weight"]
        )
        merged_norm = torch.linalg.vector_norm(merged_feature).clamp_min(1e-6)
        clusters[left] = {
            "items": [*first["items"], *second["items"]],
            "weight": merged_weight,
            "feature": merged_feature / merged_norm,
        }
        del clusters[right]
    return clusters


def _encode_artist_composite_exact(
    clip,
    data: PromptDataRead,
    base_prompt: str,
    artists: list[tuple[str, float]],
    start_percent: float | None = None,
    strength_scale: float = 1.0,
    *,
    _encode_with_comfy_clip_override=None,
) -> list:
    encode_with_comfy_clip = _require_callback(
        _encode_with_comfy_clip_override,
        "_encode_with_comfy_clip",
    )
    composite_prompt = _artist_variant_prompt_from_prompt_data(
        data,
        base_prompt,
        _artist_mix_prompt_tags(artists, include_weights=True),
    )
    composite = _conditionings_with_strength(
        encode_with_comfy_clip(clip, composite_prompt), 1.0
    )
    exact = _encode_artist_exact(
        clip,
        data,
        base_prompt,
        artists,
        start_percent=start_percent,
        end_percent=1.0 if start_percent is not None else None,
        strength_scale=strength_scale,
        _encode_with_comfy_clip_override=encode_with_comfy_clip,
    )
    return composite + exact


def _encode_artist_average_late_exact(
    clip,
    data: PromptDataRead,
    base_prompt: str,
    artists: list[tuple[str, float]],
    artist_mix: dict[str, Any],
    *,
    _encode_with_comfy_clip_override=None,
) -> list:
    encode_with_comfy_clip = _require_callback(
        _encode_with_comfy_clip_override,
        "_encode_with_comfy_clip",
    )
    late_start = _bounded_artist_mix_float(
        artist_mix.get("start_percent"),
        ARTIST_MIX_DEFAULT_START_PERCENT,
        0.0,
        1.0,
    )
    strength_scale = _bounded_artist_mix_float(
        artist_mix.get("strength_scale"),
        ARTIST_MIX_DEFAULT_STRENGTH_SCALE,
        0.0,
        5.0,
    )
    return _encode_artist_average(
        clip,
        data,
        base_prompt,
        artists,
        _encode_with_comfy_clip_override=encode_with_comfy_clip,
    ) + _encode_artist_exact(
        clip,
        data,
        base_prompt,
        artists,
        start_percent=late_start,
        end_percent=1.0,
        strength_scale=strength_scale,
        _encode_with_comfy_clip_override=encode_with_comfy_clip,
    )


def _encode_artist_scheduled_average(
    clip,
    data: PromptDataRead,
    base_prompt: str,
    artists: list[tuple[str, float]],
    artist_mix: dict[str, Any],
    *,
    _encode_with_comfy_clip_override=None,
) -> list:
    encode_with_comfy_clip = _require_callback(
        _encode_with_comfy_clip_override,
        "_encode_with_comfy_clip",
    )
    late_start = _bounded_artist_mix_float(
        artist_mix.get("start_percent"),
        ARTIST_MIX_DEFAULT_START_PERCENT,
        0.0,
        1.0,
    )
    strength_scale = _bounded_artist_mix_float(
        artist_mix.get("strength_scale"),
        ARTIST_MIX_DEFAULT_STRENGTH_SCALE,
        0.0,
        5.0,
    )
    equal_weights = _equal_artist_weights(artists)
    target_weights = _normalized_artist_weights(artists)
    scheduled = []
    if late_start > 0.0:
        scheduled.extend(
            _mark_artist_mix_conditioning(
                _conditionings_with_range(
                    _encode_artist_average(
                        clip,
                        data,
                        base_prompt,
                        artists,
                        weights=equal_weights,
                        _encode_with_comfy_clip_override=encode_with_comfy_clip,
                    ),
                    0.0,
                    late_start,
                ),
                ARTIST_MIX_SCHEDULE_KEY,
            )
        )

    segments = 4
    span = max(0.0, 1.0 - late_start)
    for index in range(segments):
        segment_start = late_start + span * (index / segments)
        segment_end = late_start + span * ((index + 1) / segments)
        amount = (index + 1) / segments
        weights = _interpolate_artist_weights(equal_weights, target_weights, amount)
        base = _conditionings_with_range(
            _conditionings_with_strength(
                encode_with_comfy_clip(clip, base_prompt), 1.0
            ),
            segment_start,
            segment_end,
        )
        artist_only = _conditionings_with_range(
            _conditionings_with_strength(
                _encode_artist_average(
                    clip,
                    {},
                    "",
                    artists,
                    weights=weights,
                    _encode_with_comfy_clip_override=encode_with_comfy_clip,
                ),
                max(0.0, strength_scale) * amount,
            ),
            segment_start,
            segment_end,
        )
        scheduled.extend(
            _mark_artist_mix_conditioning(base + artist_only, ARTIST_MIX_SCHEDULE_KEY)
        )
    return scheduled


__all__ = ()
