"""Artist-mix prompt and CONDITIONING services."""
from __future__ import annotations

import re
from math import isfinite
from typing import Any, cast

from ..common.values import _as_bool, _as_float, _as_int
from ..infrastructure.comfy.wiring import resolve_comfy_host_helper
from .contracts import AdvancedField, PromptDataArtistTag, PromptDataRead
from .data import _normalize_prompt_data, _prompt_data_nested, _prompt_data_output
from .fields import _correct_builder_prompt, _join_prompt_tokens

ARTIST_MIX_MODE_FROM_PROMPT_DATA = "prompt_data"
ARTIST_MIX_MODE_OFF = "off"
ARTIST_MIX_MODE_PROMPT = "prompt"
ARTIST_MIX_MODE_AVERAGE = "average"
ARTIST_MIX_MODE_DELTA_RMS = "delta_rms"
ARTIST_MIX_MODE_HYBRID = "hybrid"
ARTIST_MIX_MODE_CLUSTERED = "clustered"
ARTIST_MIX_MODE_EXACT = "exact"
ARTIST_MIX_MODE_COMPOSITE_EXACT = "composite_exact"
ARTIST_MIX_MODE_LATE_EXACT = "late_exact"
ARTIST_MIX_MODE_AVERAGE_LATE_EXACT = "average_late_exact"
ARTIST_MIX_MODE_SCHEDULED_AVERAGE = "scheduled_average"
ARTIST_MIX_MODES = (
    ARTIST_MIX_MODE_PROMPT,
    ARTIST_MIX_MODE_AVERAGE,
    ARTIST_MIX_MODE_DELTA_RMS,
    ARTIST_MIX_MODE_HYBRID,
    ARTIST_MIX_MODE_CLUSTERED,
    ARTIST_MIX_MODE_EXACT,
    ARTIST_MIX_MODE_COMPOSITE_EXACT,
    ARTIST_MIX_MODE_LATE_EXACT,
    ARTIST_MIX_MODE_AVERAGE_LATE_EXACT,
    ARTIST_MIX_MODE_SCHEDULED_AVERAGE,
)
ARTIST_MIX_INPUT_MODES = (
    ARTIST_MIX_MODE_FROM_PROMPT_DATA,
    ARTIST_MIX_MODE_OFF,
    *ARTIST_MIX_MODES,
)
ARTIST_MIX_STUDIO_MODES = (
    ARTIST_MIX_MODE_OFF,
    ARTIST_MIX_MODE_AVERAGE,
    ARTIST_MIX_MODE_DELTA_RMS,
    ARTIST_MIX_MODE_HYBRID,
    ARTIST_MIX_MODE_CLUSTERED,
    ARTIST_MIX_MODE_EXACT,
    ARTIST_MIX_MODE_COMPOSITE_EXACT,
    ARTIST_MIX_MODE_LATE_EXACT,
    ARTIST_MIX_MODE_AVERAGE_LATE_EXACT,
    ARTIST_MIX_MODE_SCHEDULED_AVERAGE,
)
ARTIST_MIX_DEFAULT_START_PERCENT = 0.5
ARTIST_MIX_DEFAULT_STRENGTH_SCALE = 1.0
ARTIST_MIX_DEFAULT_STYLE_GAIN = 1.35
ARTIST_MIX_DEFAULT_RMS_SCALE_CAP = 2.0
ARTIST_MIX_DEFAULT_EXACT_TOP_K = 4
ARTIST_MIX_DEFAULT_CLUSTER_COUNT = 4
ARTIST_MIX_DEFAULT_DOMINANT_ISOLATION = True
ARTIST_MIX_DEFAULT_DOMINANT_THRESHOLD = 0.25
ARTIST_MIX_CONTROL_KEY = "anima_prompt_artist_mix_control"
ARTIST_MIX_EXACT_KEY = "anima_prompt_artist_mix_exact"
ARTIST_MIX_SCHEDULE_KEY = "anima_prompt_artist_mix_schedule"

ARTIST_TAG_POSITION_CORRECT = "correct"
ARTIST_TAG_POSITION_FRONT = "front"
ARTIST_TAG_POSITION_BACK = "back"
ARTIST_TAG_POSITION_MODES = (
    ARTIST_TAG_POSITION_CORRECT,
    ARTIST_TAG_POSITION_FRONT,
    ARTIST_TAG_POSITION_BACK,
)
ARTIST_MIX_MODE_DESCRIPTIONS = {
    ARTIST_MIX_MODE_OFF: "Cost: 1 positive branch. Keeps artist-field text inline in the positive prompt.",
    ARTIST_MIX_MODE_PROMPT: "Cost: 1 positive branch. Keeps artist-field text inline in the positive prompt.",
    ARTIST_MIX_MODE_AVERAGE: "Cost: 1 positive branch. Weighted average of artist conditionings; fastest stable mix.",
    ARTIST_MIX_MODE_DELTA_RMS: (
        "Cost: 1 positive branch. Mixes artist deltas from the base prompt and restores RMS style energy; "
        "usually stronger than average."
    ),
    ARTIST_MIX_MODE_HYBRID: (
        "Cost: top_k + 1 positive branches. Keeps strongest artists as exact branches and compresses the tail "
        "with delta_rms; recommended balance."
    ),
    ARTIST_MIX_MODE_CLUSTERED: (
        "Cost: about cluster_count plus dominant artists. Groups similar artist deltas and compresses each "
        "cluster; useful for many artists."
    ),
    ARTIST_MIX_MODE_EXACT: "Cost: N positive branches. Most faithful artist-specific model output mix.",
    ARTIST_MIX_MODE_COMPOSITE_EXACT: (
        "Cost: N + 1 positive branches. Adds one composite prompt branch plus exact artist branches."
    ),
    ARTIST_MIX_MODE_LATE_EXACT: "Cost: base + N late exact branches. Applies exact mixing only after start.",
    ARTIST_MIX_MODE_AVERAGE_LATE_EXACT: (
        "Cost: 1 average branch plus N late exact branches. Fast early mix, exact late refinement."
    ),
    ARTIST_MIX_MODE_SCHEDULED_AVERAGE: (
        "Cost: scheduled average branches. Changes artist weights across timestep ranges."
    ),
}

_WEIGHTED_ARTIST_RE = re.compile(
    r"^\(\s*(?P<tag>.*?)\s*:\s*(?P<weight>[+-]?(?:\d+(?:\.\d*)?|\.\d+))\s*\)$"
)
_ARTIST_GROUP_RE = re.compile(
    r"^\s*\[\[\s*(?P<tag>.*?)(?:\s*:\s*(?P<weight>[+-]?(?:\d+(?:\.\d*)?|\.\d+)))?\s*\]\]\s*$",
    re.DOTALL,
)
_SECTION_SEPARATOR_RE = re.compile(r"^\s*-{6,}\s*$", re.MULTILINE)


def _missing_host_helper(name: str):
    raise RuntimeError(f"Artist Mix Comfy host helper is unavailable: {name}")


def _encode_with_comfy_clip(*args, **kwargs):
    helper = resolve_comfy_host_helper(
        "_encode_with_comfy_clip",
        _missing_host_helper,
    )
    return helper(*args, **kwargs)


def _advanced_enabled_pane_fields(*args, **kwargs):
    from .advanced import _advanced_enabled_pane_fields as helper

    return helper(*args, **kwargs)


def _advanced_prompt_with_artist_override(*args, **kwargs):
    from .advanced import _advanced_prompt_with_artist_override as helper

    return helper(*args, **kwargs)


def _normalize_advanced_fields(*args, **kwargs):
    from .advanced import _normalize_advanced_fields as helper

    return helper(*args, **kwargs)

def _split_artist_mix_items(text: str) -> list[str]:
    items: list[str] = []
    buffer: list[str] = []
    paren_depth = 0
    square_depth = 0
    escaped = False
    source = str(text or "")
    index = 0
    while index < len(source):
        char = source[index]
        if escaped:
            buffer.append(char)
            escaped = False
            index += 1
            continue
        if char == "\\":
            buffer.append(char)
            escaped = True
            index += 1
            continue
        if char == "(":
            paren_depth += 1
        elif char == ")" and paren_depth > 0:
            paren_depth -= 1
        elif char == "[" and index + 1 < len(source) and source[index + 1] == "[":
            square_depth += 1
            buffer.append(char)
            index += 1
            char = source[index]
        elif char == "]" and index + 1 < len(source) and source[index + 1] == "]" and square_depth > 0:
            square_depth -= 1
            buffer.append(char)
            index += 1
            char = source[index]
        if (char == "," or char == "\n") and paren_depth == 0 and square_depth == 0:
            item = "".join(buffer).strip()
            if item:
                items.append(item)
            buffer = []
            index += 1
            continue
        buffer.append(char)
        index += 1
    item = "".join(buffer).strip()
    if item:
        items.append(item)
    return items

def _split_artist_mix_blocks(text: str) -> list[str]:
    source = str(text or "").replace("\r\n", "\n").replace("\r", "\n")
    if not _SECTION_SEPARATOR_RE.search(source):
        return []
    blocks: list[str] = []
    current: list[str] = []
    for line in source.split("\n"):
        if _SECTION_SEPARATOR_RE.match(line):
            block = "\n".join(current).strip(" ,\n")
            if block:
                blocks.append(block)
            current = []
            continue
        current.append(line)
    block = "\n".join(current).strip(" ,\n")
    if block:
        blocks.append(block)
    return blocks

def _parse_artist_mix_group(raw_tag: str) -> tuple[str, float] | None:
    text = str(raw_tag or "").strip()
    match = _ARTIST_GROUP_RE.match(text)
    if not match and text.startswith("(") and text.endswith(")"):
        match = _ARTIST_GROUP_RE.match(text[1:-1].strip())
    if not match:
        return None
    tag = _join_prompt_tokens(match.group("tag") or "")
    weight = _as_float(match.group("weight"), 1.0) if match.group("weight") is not None else 1.0
    if not tag or not isfinite(weight) or weight <= 0:
        return None
    return tag, weight

def _artist_group_token(tag: str, weight: float) -> str:
    tag_text = _join_prompt_tokens(tag)
    if not tag_text:
        return ""
    if abs(float(weight) - 1.0) >= 0.001:
        return f"[[{tag_text}:{float(weight):g}]]"
    return f"[[{tag_text}]]"

def _join_artist_mix_source_prompts(*parts: str) -> str:
    items: list[str] = []
    for part in parts:
        for raw_item in _split_artist_mix_items(str(part or "")):
            group = _parse_artist_mix_group(raw_item)
            if group is not None:
                grouped_tag, grouped_weight = group
                token = _artist_group_token(grouped_tag, grouped_weight)
            else:
                token = _join_prompt_tokens(raw_item)
            if token:
                items.append(token)
    return ", ".join(items)

def _artist_mix_inline_prompt(text: str) -> str:
    items: list[str] = []
    for raw_item in _split_artist_mix_items(str(text or "")):
        group = _parse_artist_mix_group(raw_item)
        item = group[0] if group is not None else raw_item
        token = _join_prompt_tokens(item)
        if token:
            items.append(token)
    return ", ".join(items)

def _parse_artist_mix_entries(text: str) -> list[dict[str, Any]]:
    parsed: list[dict[str, Any]] = []
    blocks = _split_artist_mix_blocks(text)
    source_items = blocks or _split_artist_mix_items(text)
    for item in source_items:
        raw_tag = item.strip()
        weight = 1.0
        grouped = False
        group = _parse_artist_mix_group(raw_tag)
        if group is not None:
            tag, weight = group
            grouped = True
            parsed.append({"tag": tag, "weight": weight, "grouped": grouped})
            continue
        weight_source = raw_tag
        if blocks:
            block_parts = _split_artist_mix_items(raw_tag)
            if block_parts:
                weight_source = block_parts[0].strip()
        match = _WEIGHTED_ARTIST_RE.match(weight_source)
        if match:
            tag = raw_tag if blocks else match.group("tag").strip()
            weight = _as_float(match.group("weight"), 1.0)
        elif raw_tag.startswith("(") and raw_tag.endswith(")"):
            tag = raw_tag[1:-1].strip()
        else:
            tag = raw_tag
        tag = _artist_mix_inline_prompt(tag) if _ARTIST_GROUP_RE.search(tag) else _join_prompt_tokens(tag)
        if tag and isfinite(weight) and weight > 0:
            parsed.append({"tag": tag, "weight": weight, "grouped": grouped})
    return parsed

def _parse_artist_mix_items(text: str) -> list[tuple[str, float]]:
    return [
        (str(entry["tag"]), float(entry["weight"]))
        for entry in _parse_artist_mix_entries(text)
    ]

def _artist_tags_from_prompt(
    text: str,
    source: str = "artist_field",
) -> list[PromptDataArtistTag]:
    return [
        {
            "tag": str(entry["tag"]),
            "weight": float(entry["weight"]),
            "source": source,
            "grouped": bool(entry.get("grouped")),
        }
        for entry in _parse_artist_mix_entries(text)
    ]

def _bounded_artist_mix_float(value, default: float, minimum: float, maximum: float) -> float:
    result = _as_float(value, default)
    if not isfinite(result):
        result = default
    return max(minimum, min(maximum, result))

def _bounded_artist_mix_int(value, default: int, minimum: int, maximum: int) -> int:
    return max(minimum, min(maximum, _as_int(value, default)))

def _normalize_artist_mix_mode(value, default: str = ARTIST_MIX_MODE_PROMPT) -> str:
    mode = str(value or default)
    if mode == ARTIST_MIX_MODE_OFF:
        return ARTIST_MIX_MODE_OFF
    return mode if mode in ARTIST_MIX_MODES else default

def _normalize_artist_tag_position(value: str) -> str:
    mode = str(value or ARTIST_TAG_POSITION_CORRECT)
    return mode if mode in ARTIST_TAG_POSITION_MODES else ARTIST_TAG_POSITION_CORRECT

def _artist_mix_mode_tooltip(include_prompt_data: bool = False) -> str:
    lines = []
    if include_prompt_data:
        lines.append("prompt_data follows EASYUSE_ANIMA_PROMPT_DATA, off/prompt keeps artists inline.")
    lines.append(f"{ARTIST_MIX_MODE_OFF}: {ARTIST_MIX_MODE_DESCRIPTIONS[ARTIST_MIX_MODE_OFF]}")
    for mode in ARTIST_MIX_MODES:
        lines.append(f"{mode}: {ARTIST_MIX_MODE_DESCRIPTIONS[mode]}")
    return "\n".join(lines)

def _coalesce_artist_mix_items(artists: list[tuple[str, float]]) -> list[tuple[str, float]]:
    coalesced: dict[str, float] = {}
    order: list[str] = []
    for tag, weight in artists:
        normalized_tag = str(tag or "").strip()
        if not normalized_tag:
            continue
        value = float(weight)
        if not isfinite(value) or value <= 0:
            continue
        if normalized_tag not in coalesced:
            order.append(normalized_tag)
            coalesced[normalized_tag] = 0.0
        coalesced[normalized_tag] += value
    return [
        (tag, weight)
        for tag in order
        if (weight := coalesced.get(tag, 0.0)) > 0
    ]

def _artist_mix_prompt_tags(artists: list[tuple[str, float]], include_weights: bool) -> str:
    tags: list[str] = []
    for tag, weight in artists:
        if include_weights and "," not in tag and "\n" not in tag and abs(float(weight) - 1.0) >= 0.001:
            tags.append(f"({tag}:{float(weight):g})")
        else:
            tags.append(tag)
    return _join_prompt_tokens(*tags)

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
        if _normalize_artist_tag_position(artist_position) == ARTIST_TAG_POSITION_CORRECT:
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

def _normalized_artist_weights(artists: list[tuple[str, float]]) -> list[float]:
    total = sum(weight for _tag, weight in artists)
    if total <= 0:
        return [1.0 / len(artists) for _tag, _weight in artists] if artists else []
    return [weight / total for _tag, weight in artists]

def _equal_artist_weights(artists: list[tuple[str, float]]) -> list[float]:
    return [1.0 / len(artists) for _tag, _weight in artists] if artists else []

def _normalize_weight_values(values) -> list[float]:
    kept = [max(0.0, float(value)) for value in values]
    total = sum(kept)
    if total <= 0:
        return [1.0 / len(kept) for _value in kept] if kept else []
    return [value / total for value in kept]

def _interpolate_artist_weights(start_weights: list[float], end_weights: list[float], amount: float) -> list[float]:
    amount = max(0.0, min(1.0, float(amount)))
    return _normalize_weight_values(
        (1.0 - amount) * float(start) + amount * float(end)
        for start, end in zip(start_weights, end_weights)
    )

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
        raise RuntimeError("[EasyUseAnima] torch is required for artist mix conditioning.") from exc
    padding = torch.zeros(
        (tensor.shape[0], target_length - tensor.shape[1], tensor.shape[2]),
        dtype=tensor.dtype,
        device=tensor.device,
    )
    return torch.cat([tensor, padding], dim=1)

def _blend_conditionings(conditionings: list, weights: list[float], composite_conditioning=None) -> list:
    if not conditionings:
        return []
    if len(conditionings) == 1:
        return list(conditionings[0])
    expected_len = len(conditionings[0])
    if any(len(conditioning) != expected_len for conditioning in conditionings):
        raise RuntimeError("[EasyUseAnima] artist mix average requires CLIP conditionings with the same length.")

    try:
        import torch  # type: ignore
    except Exception as exc:
        raise RuntimeError("[EasyUseAnima] torch is required for artist mix conditioning.") from exc

    blended = []
    for entry_index in range(expected_len):
        first_tensor = conditionings[0][entry_index][0]
        max_length = max(conditioning[entry_index][0].shape[1] for conditioning in conditionings)
        if any(
            conditioning[entry_index][0].shape[0] != first_tensor.shape[0]
            or conditioning[entry_index][0].shape[2] != first_tensor.shape[2]
            for conditioning in conditionings
        ):
            raise RuntimeError("[EasyUseAnima] artist mix average requires matching CLIP embedding sizes.")

        tensor = torch.zeros(
            (first_tensor.shape[0], max_length, first_tensor.shape[2]),
            dtype=first_tensor.dtype,
            device=first_tensor.device,
        )
        for conditioning, weight in zip(conditionings, weights):
            tensor = tensor + _pad_conditioning_tensor(conditioning[entry_index][0], max_length) * float(weight)

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
        if pooled_candidates and all(torch.is_tensor(value) for value in pooled_candidates):
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
        raise RuntimeError("[EasyUseAnima] torch is required for artist mix delta_rms conditioning.") from exc

    base_tensor, base_meta = base_conditioning[0]
    if not torch.is_tensor(base_tensor) or base_tensor.ndim != 3:
        return None
    artist_tensors = [conditioning[0][0] for _tag, _weight, conditioning in encoded_artists]
    if any(
        not torch.is_tensor(tensor)
        or tensor.ndim != 3
        or tensor.shape[0] != base_tensor.shape[0]
        or tensor.shape[2] != base_tensor.shape[2]
        for tensor in artist_tensors
    ):
        return None

    max_length = max([base_tensor.shape[1], *(tensor.shape[1] for tensor in artist_tensors)])
    base_padded = _pad_conditioning_tensor(base_tensor, max_length)
    mixed_delta = torch.zeros_like(base_padded)
    target_rms = None
    for (_tag, _weight, conditioning), alpha in zip(encoded_artists, weights):
        cond_padded = _pad_conditioning_tensor(conditioning[0][0], max_length)
        delta = cond_padded - base_padded
        mixed_delta = mixed_delta + delta * float(alpha)
        rms = delta.float().pow(2).mean().sqrt()
        target_rms = rms * float(alpha) if target_rms is None else target_rms + rms * float(alpha)

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
    metadata = _copy_conditioning_metadata(metadata_source)
    metadata.pop("strength", None)
    if branch_strength is not None:
        metadata["strength"] = max(0.0, float(branch_strength))

    base_pool = base_meta.get("pooled_output") if isinstance(base_meta, dict) else None
    artist_pools = [
        conditioning[0][1].get("pooled_output")
        for _tag, _weight, conditioning in encoded_artists
        if isinstance(conditioning[0][1], dict)
    ]
    if torch.is_tensor(base_pool) and len(artist_pools) == len(encoded_artists) and all(
        torch.is_tensor(pool) and pool.shape == base_pool.shape for pool in artist_pools
    ):
        mixed_pool_delta = torch.zeros_like(base_pool)
        target_pool_rms = None
        for pool, alpha in zip(artist_pools, weights):
            delta = pool - base_pool
            mixed_pool_delta = mixed_pool_delta + delta * float(alpha)
            rms = delta.float().pow(2).mean().sqrt()
            target_pool_rms = rms * float(alpha) if target_pool_rms is None else target_pool_rms + rms * float(alpha)
        if target_pool_rms is not None:
            actual_pool_rms = mixed_pool_delta.float().pow(2).mean().sqrt().clamp_min(1e-6)
            pool_scale = torch.clamp(
                target_pool_rms / actual_pool_rms,
                1.0,
                max(1.0, float(rms_scale_cap)),
            )
            metadata["pooled_output"] = base_pool + mixed_pool_delta * float(style_gain) * pool_scale
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
        return _encode_artist_average(clip, data, base_prompt, artists)
    except Exception:
        return _encode_artist_exact(clip, data, base_prompt, artists)

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
    mix_weights = list(weights) if weights is not None else _normalized_artist_weights(artists)
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
        return _conditionings_with_strength(fallback, branch_strength)
    return fallback

def _conditionings_with_values(conditioning, values: dict[str, Any]) -> list:
    output = []
    for tensor, metadata in conditioning or []:
        item_metadata = _copy_conditioning_metadata(metadata)
        item_metadata.update(values)
        output.append([tensor, item_metadata])
    return output

def _conditionings_with_range(conditioning, start_percent: float, end_percent: float = 1.0) -> list:
    start = max(0.0, min(1.0, float(start_percent)))
    end = max(start, min(1.0, float(end_percent)))
    return _conditionings_with_values(conditioning, {"start_percent": start, "end_percent": end})

def _conditionings_with_strength(conditioning, strength: float) -> list:
    return _conditionings_with_values(conditioning, {"strength": max(0.0, float(strength))})

def _mark_artist_mix_conditioning(conditioning, key: str) -> list:
    return _conditionings_with_values(conditioning, {key: True})

def _prompt_data_positive_fields(data: PromptDataRead) -> list[AdvancedField]:
    fields = data.get("fields")
    if not isinstance(fields, list) or not fields:
        return []
    return _advanced_enabled_pane_fields(_normalize_advanced_fields(fields), "positive")

def _prompt_data_artist_base_prompt(data: PromptDataRead, positive_prompt: str) -> str:
    artist = _prompt_data_nested(data, "artist")
    artist_mix = _prompt_data_nested(data, "artist_mix")
    for source in (
        artist_mix.get("base_prompt"),
        data.get("positive_without_artist_section") if "positive_without_artist_section" in data else None,
        data.get("global_prompt") if "global_prompt" in data else None,
        artist.get("positive_prompt_without_artist") if "positive_prompt_without_artist" in artist else None,
    ):
        if source is not None:
            return str(source or "")
    return str(positive_prompt or "")

def _artist_variant_prompt_from_prompt_data(
    data: PromptDataRead,
    base_prompt: str,
    artist_prompt: str,
) -> str:
    artist_text = _join_prompt_tokens(artist_prompt)
    base_text = _join_prompt_tokens(base_prompt)
    if not artist_text:
        return base_text
    artist_mix = _prompt_data_nested(data, "artist_mix")
    artist_position = _normalize_artist_tag_position(
        cast(
            str,
            artist_mix.get(
                "artist_position",
                data.get("artist_position", ARTIST_TAG_POSITION_CORRECT),
            ),
        )
    )
    if not base_text:
        return _artist_prompt_with_position("", artist_text, artist_position)

    fields = _prompt_data_positive_fields(data)
    if artist_position == ARTIST_TAG_POSITION_CORRECT and fields:
        prompt = _advanced_prompt_with_artist_override(
            fields,
            artist_text,
            include_quality=not _as_bool(_prompt_data_output(data, "use_anima_mod_guidance", False), False),
            force_pin_triggers=_as_bool(data.get("pin_trigger_tags_to_front"), False),
        )
        if prompt:
            return _join_prompt_tokens(
                prompt,
                str(data.get("_artist_mix_execution_positive_suffix") or ""),
            )
    return _artist_prompt_with_position(base_text, artist_text, artist_position)

def _prompt_data_artist_mix_config(
    data: PromptDataRead,
    artist_mix_mode: str,
    artist_mix_start_percent: float,
    artist_mix_strength_scale: float,
    artist_mix_style_gain: float,
    artist_mix_rms_scale_cap: float,
    artist_mix_exact_top_k: int,
    artist_mix_cluster_count: int,
    artist_mix_dominant_isolation: bool,
    artist_mix_dominant_threshold: float,
) -> dict[str, Any]:
    source = _prompt_data_nested(data, "artist_mix")
    artist = _prompt_data_nested(data, "artist")
    mode = _normalize_artist_mix_mode(source.get("mode", ARTIST_MIX_MODE_PROMPT))
    enabled = _as_bool(source.get("enabled"), False)
    if mode == ARTIST_MIX_MODE_OFF:
        mode = ARTIST_MIX_MODE_PROMPT
        enabled = False

    config = {
        "enabled": enabled,
        "mode": mode,
        "base_source": str(source.get("base_source") or "positive_without_artist_section"),
        "start_percent": _bounded_artist_mix_float(
            source.get("start_percent"),
            ARTIST_MIX_DEFAULT_START_PERCENT,
            0.0,
            1.0,
        ),
        "strength_scale": _bounded_artist_mix_float(
            source.get("strength_scale"),
            ARTIST_MIX_DEFAULT_STRENGTH_SCALE,
            0.0,
            5.0,
        ),
        "style_gain": _bounded_artist_mix_float(
            source.get("style_gain"),
            ARTIST_MIX_DEFAULT_STYLE_GAIN,
            0.0,
            3.0,
        ),
        "rms_scale_cap": _bounded_artist_mix_float(
            source.get("rms_scale_cap"),
            ARTIST_MIX_DEFAULT_RMS_SCALE_CAP,
            1.0,
            5.0,
        ),
        "exact_top_k": _bounded_artist_mix_int(
            source.get("exact_top_k"),
            ARTIST_MIX_DEFAULT_EXACT_TOP_K,
            0,
            64,
        ),
        "cluster_count": _bounded_artist_mix_int(
            source.get("cluster_count"),
            ARTIST_MIX_DEFAULT_CLUSTER_COUNT,
            1,
            32,
        ),
        "dominant_isolation": _as_bool(
            source.get("dominant_isolation"),
            ARTIST_MIX_DEFAULT_DOMINANT_ISOLATION,
        ),
        "dominant_threshold": _bounded_artist_mix_float(
            source.get("dominant_threshold"),
            ARTIST_MIX_DEFAULT_DOMINANT_THRESHOLD,
            0.0,
            1.0,
        ),
        "artist_prompt": str(
            source.get("artist_prompt")
            or artist.get("weighted_text")
            or artist.get("text")
            or artist.get("positive_prompt")
            or ""
        ),
    }

    override_mode = str(artist_mix_mode or ARTIST_MIX_MODE_FROM_PROMPT_DATA)
    if override_mode != ARTIST_MIX_MODE_FROM_PROMPT_DATA:
        override_mode = _normalize_artist_mix_mode(override_mode, ARTIST_MIX_MODE_OFF)
        if override_mode == ARTIST_MIX_MODE_OFF:
            config["enabled"] = False
            config["mode"] = ARTIST_MIX_MODE_PROMPT
        elif override_mode == ARTIST_MIX_MODE_PROMPT:
            config["enabled"] = False
            config["mode"] = ARTIST_MIX_MODE_PROMPT
        else:
            config["enabled"] = True
            config["mode"] = override_mode
        config["start_percent"] = _bounded_artist_mix_float(
            artist_mix_start_percent,
            ARTIST_MIX_DEFAULT_START_PERCENT,
            0.0,
            1.0,
        )
        config["strength_scale"] = _bounded_artist_mix_float(
            artist_mix_strength_scale,
            ARTIST_MIX_DEFAULT_STRENGTH_SCALE,
            0.0,
            5.0,
        )
        config["style_gain"] = _bounded_artist_mix_float(
            artist_mix_style_gain,
            ARTIST_MIX_DEFAULT_STYLE_GAIN,
            0.0,
            3.0,
        )
        config["rms_scale_cap"] = _bounded_artist_mix_float(
            artist_mix_rms_scale_cap,
            ARTIST_MIX_DEFAULT_RMS_SCALE_CAP,
            1.0,
            5.0,
        )
        config["exact_top_k"] = _bounded_artist_mix_int(
            artist_mix_exact_top_k,
            ARTIST_MIX_DEFAULT_EXACT_TOP_K,
            0,
            64,
        )
        config["cluster_count"] = _bounded_artist_mix_int(
            artist_mix_cluster_count,
            ARTIST_MIX_DEFAULT_CLUSTER_COUNT,
            1,
            32,
        )
        config["dominant_isolation"] = _as_bool(
            artist_mix_dominant_isolation,
            ARTIST_MIX_DEFAULT_DOMINANT_ISOLATION,
        )
        config["dominant_threshold"] = _bounded_artist_mix_float(
            artist_mix_dominant_threshold,
            ARTIST_MIX_DEFAULT_DOMINANT_THRESHOLD,
            0.0,
            1.0,
        )
    return config

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
    exact = []
    strengths = (
        [max(0.0, float(value)) for value in branch_strengths]
        if branch_strengths is not None
        else [float(weight) * float(strength_scale) for weight in _normalized_artist_weights(artists)]
    )
    for (tag, _weight), strength in zip(artists, strengths):
        variant_prompt = _artist_variant_prompt_from_prompt_data(data, base_prompt, tag)
        for tensor, metadata in _encode_with_comfy_clip(clip, variant_prompt):
            item_metadata = _copy_conditioning_metadata(metadata)
            item_metadata["strength"] = float(strength)
            if start_percent is not None:
                item_metadata["start_percent"] = max(0.0, min(1.0, float(start_percent)))
            if end_percent is not None:
                item_metadata["end_percent"] = max(
                    item_metadata.get("start_percent", 0.0),
                    min(1.0, float(end_percent)),
                )
            item_metadata[ARTIST_MIX_EXACT_KEY] = True
            exact.append([tensor, item_metadata])
    return exact or _encode_with_comfy_clip(clip, base_prompt)

def _encode_artist_average(
    clip,
    data: PromptDataRead,
    base_prompt: str,
    artists: list[tuple[str, float]],
    weights: list[float] | None = None,
) -> list:
    mix_weights = list(weights) if weights is not None else _normalized_artist_weights(artists)
    encoded = [
        _encode_with_comfy_clip(
            clip,
            _artist_variant_prompt_from_prompt_data(data, base_prompt, tag),
        )
        for tag, _weight in artists
    ]
    if any(len(conditioning) != 1 for conditioning in encoded):
        return _encode_artist_exact(clip, data, base_prompt, artists)

    composite_prompt = _artist_variant_prompt_from_prompt_data(
        data,
        base_prompt,
        _artist_mix_prompt_tags(artists, include_weights=True),
    )
    composite = _encode_with_comfy_clip(clip, composite_prompt)
    if len(composite) != 1:
        composite = None
    return _blend_conditionings(encoded, mix_weights, composite)

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
    artists = _coalesce_artist_mix_items(artists)
    if not artists:
        return _encode_with_comfy_clip(clip, base_prompt)
    total_weight = sum(weight for _tag, weight in artists)
    if total_weight <= 0:
        return _encode_with_comfy_clip(clip, base_prompt)

    sorted_artists = sorted(artists, key=lambda item: item[1], reverse=True)
    top_k = _bounded_artist_mix_int(exact_top_k, ARTIST_MIX_DEFAULT_EXACT_TOP_K, 0, 64)
    if top_k >= len(sorted_artists):
        return _encode_artist_exact(clip, data, base_prompt, sorted_artists, strength_scale=strength_scale)

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
            )
        )
    if tail:
        tail_total = sum(weight for _tag, weight in tail)
        if tail_total <= 0:
            return _encode_artist_exact(clip, data, base_prompt, sorted_artists, strength_scale=strength_scale)
        try:
            output.extend(
                _encode_artist_delta_rms(
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
            return _encode_artist_exact(clip, data, base_prompt, sorted_artists, strength_scale=strength_scale)
    return output or _encode_artist_exact(clip, data, base_prompt, sorted_artists, strength_scale=strength_scale)

def _artist_conditioning_feature(torch, base_conditioning, encoded_artist, use_pooled: bool):
    if len(base_conditioning) != 1 or len(encoded_artist[2]) != 1:
        return None
    base_tensor, base_meta = base_conditioning[0]
    cond_tensor, metadata = encoded_artist[2][0]
    if not torch.is_tensor(base_tensor) or not torch.is_tensor(cond_tensor):
        return None
    base_pool = base_meta.get("pooled_output") if isinstance(base_meta, dict) else None
    pool = metadata.get("pooled_output") if isinstance(metadata, dict) else None
    if use_pooled and torch.is_tensor(base_pool) and torch.is_tensor(pool) and base_pool.shape == pool.shape:
        feature = (pool - base_pool).float().flatten()
    elif (
        base_tensor.ndim == 3
        and cond_tensor.ndim == 3
        and base_tensor.shape[0] == cond_tensor.shape[0]
        and base_tensor.shape[2] == cond_tensor.shape[2]
    ):
        max_length = max(base_tensor.shape[1], cond_tensor.shape[1])
        feature = (
            _pad_conditioning_tensor(cond_tensor, max_length)
            - _pad_conditioning_tensor(base_tensor, max_length)
        ).float().mean(dim=1).flatten()
    else:
        return None
    norm = torch.linalg.vector_norm(feature).clamp_min(1e-6)
    return feature / norm

def _greedy_cluster_encoded_artists(torch, encoded_artists: list, features: list, cluster_count: int) -> list:
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
                similarity = torch.dot(clusters[left]["feature"], clusters[right]["feature"]).item()
                if best_similarity is None or similarity > best_similarity:
                    best_similarity = similarity
                    best_pair = (left, right)
        left, right = best_pair
        first = clusters[left]
        second = clusters[right]
        merged_weight = first["weight"] + second["weight"]
        merged_feature = first["feature"] * first["weight"] + second["feature"] * second["weight"]
        merged_norm = torch.linalg.vector_norm(merged_feature).clamp_min(1e-6)
        clusters[left] = {
            "items": [*first["items"], *second["items"]],
            "weight": merged_weight,
            "feature": merged_feature / merged_norm,
        }
        del clusters[right]
    return clusters

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
            _encode_artist_exact(
                clip,
                data,
                base_prompt,
                dominant,
                branch_strengths=[
                    (weight / total_weight) * float(strength_scale)
                    for _tag, weight in dominant
                ],
            )
        )
    if not remaining:
        return output or _encode_artist_exact(clip, data, base_prompt, artists, strength_scale=strength_scale)
    if len(remaining) <= target_cluster_count:
        output.extend(
            _encode_artist_exact(
                clip,
                data,
                base_prompt,
                remaining,
                branch_strengths=[
                    (weight / total_weight) * float(strength_scale)
                    for _tag, weight in remaining
                ],
            )
        )
        return output

    try:
        import torch  # type: ignore

        base_conditioning = _encode_with_comfy_clip(clip, base_prompt)
        encoded = _encoded_artist_conditionings(clip, data, base_prompt, remaining)
        base_meta = base_conditioning[0][1] if len(base_conditioning) == 1 else {}
        base_pool = base_meta.get("pooled_output") if isinstance(base_meta, dict) else None
        use_pooled = torch.is_tensor(base_pool) and all(
            len(encoded_artist[2]) == 1
            and isinstance(encoded_artist[2][0][1], dict)
            and torch.is_tensor(encoded_artist[2][0][1].get("pooled_output"))
            and encoded_artist[2][0][1].get("pooled_output").shape == base_pool.shape
            for encoded_artist in encoded
        )
        features = [
            _artist_conditioning_feature(torch, base_conditioning, encoded_artist, use_pooled)
            for encoded_artist in encoded
        ]
        if any(feature is None for feature in features):
            raise RuntimeError("missing cluster feature")
        clusters = _greedy_cluster_encoded_artists(torch, encoded, features, target_cluster_count)
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
        return output or _encode_artist_hybrid(
            clip,
            data,
            base_prompt,
            artists,
            exact_top_k=ARTIST_MIX_DEFAULT_EXACT_TOP_K,
            style_gain=style_gain,
            rms_scale_cap=rms_scale_cap,
            strength_scale=strength_scale,
        )
    except Exception:
        return _encode_artist_hybrid(
            clip,
            data,
            base_prompt,
            artists,
            exact_top_k=ARTIST_MIX_DEFAULT_EXACT_TOP_K,
            style_gain=style_gain,
            rms_scale_cap=rms_scale_cap,
            strength_scale=strength_scale,
        )

def _encode_artist_composite_exact(
    clip,
    data: PromptDataRead,
    base_prompt: str,
    artists: list[tuple[str, float]],
    start_percent: float | None = None,
    strength_scale: float = 1.0,
) -> list:
    composite_prompt = _artist_variant_prompt_from_prompt_data(
        data,
        base_prompt,
        _artist_mix_prompt_tags(artists, include_weights=True),
    )
    composite = _conditionings_with_strength(_encode_with_comfy_clip(clip, composite_prompt), 1.0)
    exact = _encode_artist_exact(
        clip,
        data,
        base_prompt,
        artists,
        start_percent=start_percent,
        end_percent=1.0 if start_percent is not None else None,
        strength_scale=strength_scale,
    )
    return composite + exact

def _encode_artist_average_late_exact(
    clip,
    data: PromptDataRead,
    base_prompt: str,
    artists: list[tuple[str, float]],
    artist_mix: dict[str, Any],
) -> list:
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
    return _encode_artist_average(clip, data, base_prompt, artists) + _encode_artist_exact(
        clip,
        data,
        base_prompt,
        artists,
        start_percent=late_start,
        end_percent=1.0,
        strength_scale=strength_scale,
    )

def _encode_artist_scheduled_average(
    clip,
    data: PromptDataRead,
    base_prompt: str,
    artists: list[tuple[str, float]],
    artist_mix: dict[str, Any],
) -> list:
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
                    _encode_artist_average(clip, data, base_prompt, artists, weights=equal_weights),
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
            _conditionings_with_strength(_encode_with_comfy_clip(clip, base_prompt), 1.0),
            segment_start,
            segment_end,
        )
        artist_only = _conditionings_with_range(
            _conditionings_with_strength(
                _encode_artist_average(clip, {}, "", artists, weights=weights),
                max(0.0, strength_scale) * amount,
            ),
            segment_start,
            segment_end,
        )
        scheduled.extend(_mark_artist_mix_conditioning(base + artist_only, ARTIST_MIX_SCHEDULE_KEY))
    return scheduled

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
    artists = _coalesce_artist_mix_items(_parse_artist_mix_items(str(artist_mix.get("artist_prompt") or "")))
    if not artist_mix.get("enabled") or artist_mix.get("mode") == ARTIST_MIX_MODE_PROMPT:
        return _encode_with_comfy_clip(clip, execution_positive_prompt)

    base_prompt = _join_prompt_tokens(
        _prompt_data_artist_base_prompt(data, positive_prompt),
        execution_suffix,
    )
    if not artists:
        return _encode_with_comfy_clip(clip, base_prompt)

    mode = _normalize_artist_mix_mode(artist_mix.get("mode"), ARTIST_MIX_MODE_PROMPT)
    if mode == ARTIST_MIX_MODE_AVERAGE:
        return _encode_artist_average(clip, data, base_prompt, artists)
    if mode == ARTIST_MIX_MODE_DELTA_RMS:
        return _mark_artist_mix_conditioning(
            _encode_artist_delta_rms(
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
        return _mark_artist_mix_conditioning(
            _encode_artist_hybrid(
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
            ),
            ARTIST_MIX_CONTROL_KEY,
        )
    if mode == ARTIST_MIX_MODE_CLUSTERED:
        return _mark_artist_mix_conditioning(
            _encode_artist_clustered(
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
        return _mark_artist_mix_conditioning(
            _encode_artist_exact(
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
            ),
            ARTIST_MIX_CONTROL_KEY,
        )
    if mode == ARTIST_MIX_MODE_COMPOSITE_EXACT:
        return _mark_artist_mix_conditioning(
            _encode_artist_composite_exact(
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
            ),
            ARTIST_MIX_CONTROL_KEY,
        )
    if mode == ARTIST_MIX_MODE_LATE_EXACT:
        return _mark_artist_mix_conditioning(
            _encode_with_comfy_clip(clip, base_prompt) + _encode_artist_exact(
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
            ),
            ARTIST_MIX_CONTROL_KEY,
        )
    if mode == ARTIST_MIX_MODE_AVERAGE_LATE_EXACT:
        return _mark_artist_mix_conditioning(
            _encode_artist_average_late_exact(clip, data, base_prompt, artists, artist_mix),
            ARTIST_MIX_CONTROL_KEY,
        )
    if mode == ARTIST_MIX_MODE_SCHEDULED_AVERAGE:
        return _mark_artist_mix_conditioning(
            _encode_artist_scheduled_average(clip, data, base_prompt, artists, artist_mix),
            ARTIST_MIX_CONTROL_KEY,
        )
    return _encode_with_comfy_clip(clip, execution_positive_prompt)

__all__ = ()
