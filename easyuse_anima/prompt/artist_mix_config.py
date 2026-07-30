"""Artist Mix configuration and prompt projection services."""

from __future__ import annotations

from math import isfinite
from typing import Any, cast

from ..common.values import _as_bool
from . import artist_mix_primitives as _artist_mix_primitives
from .contracts import AdvancedField, PromptDataRead
from .data import _prompt_data_nested, _prompt_data_output
from .fields import _correct_builder_prompt, _join_prompt_tokens

ARTIST_MIX_DEFAULT_CLUSTER_COUNT = (
    _artist_mix_primitives.ARTIST_MIX_DEFAULT_CLUSTER_COUNT
)
ARTIST_MIX_DEFAULT_DOMINANT_ISOLATION = (
    _artist_mix_primitives.ARTIST_MIX_DEFAULT_DOMINANT_ISOLATION
)
ARTIST_MIX_DEFAULT_DOMINANT_THRESHOLD = (
    _artist_mix_primitives.ARTIST_MIX_DEFAULT_DOMINANT_THRESHOLD
)
ARTIST_MIX_DEFAULT_EXACT_TOP_K = _artist_mix_primitives.ARTIST_MIX_DEFAULT_EXACT_TOP_K
ARTIST_MIX_DEFAULT_RMS_SCALE_CAP = (
    _artist_mix_primitives.ARTIST_MIX_DEFAULT_RMS_SCALE_CAP
)
ARTIST_MIX_DEFAULT_START_PERCENT = (
    _artist_mix_primitives.ARTIST_MIX_DEFAULT_START_PERCENT
)
ARTIST_MIX_DEFAULT_STRENGTH_SCALE = (
    _artist_mix_primitives.ARTIST_MIX_DEFAULT_STRENGTH_SCALE
)
ARTIST_MIX_DEFAULT_STYLE_GAIN = _artist_mix_primitives.ARTIST_MIX_DEFAULT_STYLE_GAIN
ARTIST_MIX_MODE_AVERAGE = _artist_mix_primitives.ARTIST_MIX_MODE_AVERAGE
ARTIST_MIX_MODE_AVERAGE_LATE_EXACT = (
    _artist_mix_primitives.ARTIST_MIX_MODE_AVERAGE_LATE_EXACT
)
ARTIST_MIX_MODE_CLUSTERED = _artist_mix_primitives.ARTIST_MIX_MODE_CLUSTERED
ARTIST_MIX_MODE_COMPOSITE_EXACT = _artist_mix_primitives.ARTIST_MIX_MODE_COMPOSITE_EXACT
ARTIST_MIX_MODE_DELTA_RMS = _artist_mix_primitives.ARTIST_MIX_MODE_DELTA_RMS
ARTIST_MIX_MODE_EXACT = _artist_mix_primitives.ARTIST_MIX_MODE_EXACT
ARTIST_MIX_MODE_FROM_PROMPT_DATA = (
    _artist_mix_primitives.ARTIST_MIX_MODE_FROM_PROMPT_DATA
)
ARTIST_MIX_MODE_HYBRID = _artist_mix_primitives.ARTIST_MIX_MODE_HYBRID
ARTIST_MIX_MODE_LATE_EXACT = _artist_mix_primitives.ARTIST_MIX_MODE_LATE_EXACT
ARTIST_MIX_MODE_OFF = _artist_mix_primitives.ARTIST_MIX_MODE_OFF
ARTIST_MIX_MODE_PROMPT = _artist_mix_primitives.ARTIST_MIX_MODE_PROMPT
ARTIST_MIX_MODE_SCHEDULED_AVERAGE = (
    _artist_mix_primitives.ARTIST_MIX_MODE_SCHEDULED_AVERAGE
)
ARTIST_MIX_MODES = _artist_mix_primitives.ARTIST_MIX_MODES
_ARTIST_GROUP_RE = _artist_mix_primitives._ARTIST_GROUP_RE
_SECTION_SEPARATOR_RE = _artist_mix_primitives._SECTION_SEPARATOR_RE
_WEIGHTED_ARTIST_RE = _artist_mix_primitives._WEIGHTED_ARTIST_RE
_artist_group_token = _artist_mix_primitives._artist_group_token
_artist_mix_inline_prompt = _artist_mix_primitives._artist_mix_inline_prompt
_artist_tags_from_prompt = _artist_mix_primitives._artist_tags_from_prompt
_bounded_artist_mix_float = _artist_mix_primitives._bounded_artist_mix_float
_bounded_artist_mix_int = _artist_mix_primitives._bounded_artist_mix_int
_join_artist_mix_source_prompts = _artist_mix_primitives._join_artist_mix_source_prompts
_normalize_artist_mix_mode = _artist_mix_primitives._normalize_artist_mix_mode
_parse_artist_mix_entries = _artist_mix_primitives._parse_artist_mix_entries
_parse_artist_mix_group = _artist_mix_primitives._parse_artist_mix_group
_parse_artist_mix_items = _artist_mix_primitives._parse_artist_mix_items
_split_artist_mix_blocks = _artist_mix_primitives._split_artist_mix_blocks
_split_artist_mix_items = _artist_mix_primitives._split_artist_mix_items

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


def _advanced_enabled_pane_fields(*args, **kwargs):
    from .advanced import _advanced_enabled_pane_fields as helper

    return helper(*args, **kwargs)


def _advanced_prompt_with_artist_override(*args, **kwargs):
    from .advanced import _advanced_prompt_with_artist_override as helper

    return helper(*args, **kwargs)


def _normalize_advanced_fields(*args, **kwargs):
    from .advanced import _normalize_advanced_fields as helper

    return helper(*args, **kwargs)


def _normalize_artist_tag_position(value: str) -> str:
    mode = str(value or ARTIST_TAG_POSITION_CORRECT)
    return mode if mode in ARTIST_TAG_POSITION_MODES else ARTIST_TAG_POSITION_CORRECT


def _artist_mix_mode_tooltip(include_prompt_data: bool = False) -> str:
    lines = []
    if include_prompt_data:
        lines.append(
            "prompt_data follows EASYUSE_ANIMA_PROMPT_DATA, off/prompt keeps artists inline."
        )
    lines.append(
        f"{ARTIST_MIX_MODE_OFF}: {ARTIST_MIX_MODE_DESCRIPTIONS[ARTIST_MIX_MODE_OFF]}"
    )
    for mode in ARTIST_MIX_MODES:
        lines.append(f"{mode}: {ARTIST_MIX_MODE_DESCRIPTIONS[mode]}")
    return "\n".join(lines)


def _coalesce_artist_mix_items(
    artists: list[tuple[str, float]],
) -> list[tuple[str, float]]:
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
    return [(tag, weight) for tag in order if (weight := coalesced.get(tag, 0.0)) > 0]


def _artist_mix_prompt_tags(
    artists: list[tuple[str, float]], include_weights: bool
) -> str:
    tags: list[str] = []
    for tag, weight in artists:
        if (
            include_weights
            and "," not in tag
            and "\n" not in tag
            and abs(float(weight) - 1.0) >= 0.001
        ):
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


def _interpolate_artist_weights(
    start_weights: list[float], end_weights: list[float], amount: float
) -> list[float]:
    amount = max(0.0, min(1.0, float(amount)))
    return _normalize_weight_values(
        (1.0 - amount) * float(start) + amount * float(end)
        for start, end in zip(start_weights, end_weights)
    )


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
        data.get("positive_without_artist_section")
        if "positive_without_artist_section" in data
        else None,
        data.get("global_prompt") if "global_prompt" in data else None,
        artist.get("positive_prompt_without_artist")
        if "positive_prompt_without_artist" in artist
        else None,
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
            include_quality=not _as_bool(
                _prompt_data_output(data, "use_anima_mod_guidance", False), False
            ),
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
        "base_source": str(
            source.get("base_source") or "positive_without_artist_section"
        ),
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


__all__ = ()
