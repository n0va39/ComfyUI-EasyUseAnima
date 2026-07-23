"""Advanced Prompt Studio field and prompt-data services."""

from __future__ import annotations

import json
import re
from typing import Any

from ..common.values import _as_bool, _as_int, _single_value
from ..naia.resolution import (
    DEFAULT_ADVANCED_RESOLUTION_BUCKET,
    NAIA_ADVANCED_RESOLUTION_BUCKET,
    _normalize_resolution_bucket,
)
from .artist_mix import (
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
    _join_artist_mix_source_prompts,
    _normalize_artist_mix_mode,
    _parse_artist_mix_items,
)
from .correction import _translate_prompt_text
from .data import PROMPT_DATA_SCHEMA, PROMPT_DATA_TYPE, PROMPT_DATA_VERSION
from .fields import (
    DEFAULT_QUALITY_TAGS,
    DEFAULT_TRAILING_QUALITY_TAGS,
    _correct_builder_prompt,
    _filter_metadata_prompt,
    _join_prompt_tokens,
)

try:
    from ...prompt_translation import has_prompt_translation_markers
    from ...settings import resolve_metadata_filter_words
    from ...wildcard_engine import (
        expand_wildcard_texts,
        has_wildcard_syntax,
        normalize_prompt_studio_wildcard_mode,
        normalize_seed,
    )
except ImportError:
    from prompt_translation import has_prompt_translation_markers
    from settings import resolve_metadata_filter_words
    from wildcard_engine import (
        expand_wildcard_texts,
        has_wildcard_syntax,
        normalize_prompt_studio_wildcard_mode,
        normalize_seed,
    )

ADVANCED_FIELD_TYPES = {"quality", "artist", "trigger", "general", "naia"}
ADVANCED_FIELD_PANES = {"positive", "negative"}
ADVANCED_FIELD_LABELS = {
    "quality": "Quality Tags",
    "artist": "Artist Tags",
    "trigger": "Trigger Words",
    "general": "General Tags",
    "naia": "NAIA Prompt",
}
ADVANCED_FIELDS_WORKFLOW_PROPERTY = "easyuse_anima_advanced_fields"
PROMPT_STUDIO_WILDCARD_MODE_LABELS = ("일반", "순차")
SEED_CONTROL_FIXED = "fixed"
SEED_CONTROL_RANDOMIZE = "randomize"
SEED_CONTROL_INCREMENT = "increment"
WILDCARD_MODE_FIXED = "fixed"
PROMPT_STUDIO_WILDCARD_SEED_CONTROL_ALIASES = {
    "fixed": SEED_CONTROL_FIXED,
    "고정": SEED_CONTROL_FIXED,
    "random": SEED_CONTROL_RANDOMIZE,
    "randomize": SEED_CONTROL_RANDOMIZE,
    "매번 랜덤": SEED_CONTROL_RANDOMIZE,
    "increase": SEED_CONTROL_INCREMENT,
    "increment": SEED_CONTROL_INCREMENT,
    "증가": SEED_CONTROL_INCREMENT,
}
PROMPT_STUDIO_LEGACY_FIXED_WILDCARD_MODES = {
    WILDCARD_MODE_FIXED,
    "고정",
    "reproduce",
    "재현",
}
EXTEND_PROMPT_SLOT_SPECS = [
    ("quality_tags_1", "positive", "quality", "Quality Tags 1", DEFAULT_QUALITY_TAGS, 72),
    ("quality_tags_2", "positive", "quality", "Quality Tags 2", "", 72),
    ("naia_prompt_3", "positive", "general", "NAIA Prompt 3", "", 150),
    ("general_tags_4", "positive", "general", "General Tags 4", "", 120),
    ("general_tags_5", "positive", "general", "General Tags 5", "", 120),
    ("general_tags_6", "positive", "general", "General Tags 6", "", 120),
    ("general_tags_7", "positive", "general", "General Tags 7", "", 120),
    ("general_tags_8", "positive", "general", "General Tags 8", "", 120),
    ("general_tags_9", "positive", "general", "General Tags 9", "", 120),
    (
        "trailing_tags_10",
        "positive",
        "general",
        "Trailing Quality Tags 10",
        DEFAULT_TRAILING_QUALITY_TAGS,
        72,
    ),
    ("trailing_tags_11", "positive", "general", "Trailing Quality Tags 11", "", 72),
    ("negative_prompt_1", "negative", "quality", "Negative Prompt 1", "", 120),
    ("negative_prompt_2", "negative", "quality", "Negative Prompt 2", "", 120),
    ("negative_prompt_3", "negative", "general", "Negative Prompt 3", "", 120),
    ("negative_prompt_4", "negative", "general", "Negative Prompt 4", "", 120),
]
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

_ADVANCED_FIELD_SOCKET_PREFIX = "field_"
_ADVANCED_FIELD_SOCKET_RE = re.compile(r"[^A-Za-z0-9_]")


def _normalize_prompt_studio_wildcard_seed_control(
    value: Any,
    wildcard_mode: Any = None,
) -> str:
    loaded_mode = str(wildcard_mode or "").strip().lower()
    if loaded_mode in PROMPT_STUDIO_LEGACY_FIXED_WILDCARD_MODES:
        return SEED_CONTROL_FIXED
    return PROMPT_STUDIO_WILDCARD_SEED_CONTROL_ALIASES.get(
        str(value or "").strip().lower(),
        SEED_CONTROL_FIXED,
    )


def _translate_prompt_fields(fields: list[dict]) -> list[dict]:
    translated: list[dict] = []
    for field in fields:
        item = dict(field)
        text = str(item.get("text") or "")
        if text and has_prompt_translation_markers(text):
            item["text"] = _translate_prompt_text(text)
        translated.append(item)
    return translated


def _advanced_default_fields() -> list[dict]:
    return [
        {
            "id": "positive_quality",
            "pane": "positive",
            "type": "quality",
            "label": ADVANCED_FIELD_LABELS["quality"],
            "text": DEFAULT_QUALITY_TAGS,
            "height": 72,
            "enabled": True,
        },
        {
            "id": "positive_artist",
            "pane": "positive",
            "type": "artist",
            "label": ADVANCED_FIELD_LABELS["artist"],
            "text": "",
            "height": 72,
            "enabled": True,
        },
        {
            "id": "positive_trigger",
            "pane": "positive",
            "type": "trigger",
            "label": ADVANCED_FIELD_LABELS["trigger"],
            "text": "",
            "height": 72,
            "enabled": True,
            "pin": True,
        },
        {
            "id": "positive_general",
            "pane": "positive",
            "type": "general",
            "label": ADVANCED_FIELD_LABELS["general"],
            "text": "",
            "height": 150,
            "enabled": True,
        },
        {
            "id": "positive_trailing",
            "pane": "positive",
            "type": "general",
            "label": ADVANCED_FIELD_LABELS["general"],
            "text": DEFAULT_TRAILING_QUALITY_TAGS,
            "height": 72,
            "enabled": True,
        },
        {
            "id": "negative_general",
            "pane": "negative",
            "type": "general",
            "label": ADVANCED_FIELD_LABELS["general"],
            "text": "",
            "height": 120,
            "enabled": True,
        },
    ]


def _advanced_fields_json(fields: list[dict] | None = None) -> str:
    return json.dumps(
        fields if fields is not None else _advanced_default_fields(),
        ensure_ascii=False,
        separators=(",", ":"),
    )


def _as_advanced_height(value, default: int = 72) -> int:
    return max(36, _as_int(value, default))


def _normalize_advanced_fields(value: str | list | None) -> list[dict]:
    raw = value
    if isinstance(value, str):
        try:
            raw = json.loads(value or "[]")
        except json.JSONDecodeError:
            raw = []
    if not isinstance(raw, list):
        raw = []
    if not raw:
        raw = _advanced_default_fields()

    fields: list[dict] = []
    seen_naia_panes: set[str] = set()
    seen_trigger = False
    for index, item in enumerate(raw):
        if not isinstance(item, dict):
            continue
        pane = str(item.get("pane") or "positive").strip().lower()
        if pane not in ADVANCED_FIELD_PANES:
            pane = "positive"
        field_type = str(item.get("type") or "general").strip().lower()
        if field_type not in ADVANCED_FIELD_TYPES:
            field_type = "general"
        if pane == "negative" and field_type == "trigger":
            field_type = "general"
        if field_type == "naia":
            if pane in seen_naia_panes:
                continue
            seen_naia_panes.add(pane)
        if field_type == "trigger":
            if seen_trigger:
                continue
            seen_trigger = True
            pane = "positive"
        default_label = ADVANCED_FIELD_LABELS.get(
            field_type,
            ADVANCED_FIELD_LABELS["general"],
        )
        label = str(item.get("label") or default_label).strip() or default_label
        field_id = str(item.get("id") or f"{pane}_{field_type}_{index + 1}").strip()
        if not field_id:
            field_id = f"{pane}_{field_type}_{index + 1}"
        fields.append(
            {
                "id": field_id,
                "pane": pane,
                "type": field_type,
                "label": label,
                "text": str(item.get("text") or ""),
                "height": _as_advanced_height(item.get("height"), 72),
                "enabled": _as_bool(item.get("enabled"), True),
                "pin": _as_bool(item.get("pin"), field_type == "trigger"),
            }
        )

    return fields or _advanced_default_fields()


def _clone_advanced_fields(fields: list[dict]) -> list[dict]:
    return [dict(field) for field in fields]


def _advanced_field_socket_name(field: dict) -> str:
    raw = _ADVANCED_FIELD_SOCKET_RE.sub(
        "_",
        str(field.get("id") or "field"),
    ).strip("_")
    return f"{_ADVANCED_FIELD_SOCKET_PREFIX}{raw or 'field'}"


def _advanced_field_input_values(field_inputs: dict) -> dict[str, str]:
    values: dict[str, str] = {}
    for key, value in field_inputs.items():
        if not str(key).startswith(_ADVANCED_FIELD_SOCKET_PREFIX):
            continue
        single = _single_value(value)
        if single is None:
            continue
        values[str(key)] = str(single)
    return values


def _apply_advanced_field_inputs(fields: list[dict], field_inputs: dict) -> list[dict]:
    values = _advanced_field_input_values(field_inputs)
    if not values:
        return _clone_advanced_fields(fields)

    effective = _clone_advanced_fields(fields)
    for field in effective:
        name = _advanced_field_socket_name(field)
        if name in values:
            field["text"] = values[name]
    return effective


def _advanced_enabled_naia_panes(fields: list[dict]) -> set[str]:
    return {
        str(field.get("pane") or "positive")
        for field in fields
        if field.get("type") == "naia" and field.get("enabled") is not False
    }


def _advanced_has_enabled_naia(fields: list[dict]) -> bool:
    return bool(_advanced_enabled_naia_panes(fields))


def _advanced_uses_naia_resolution(bucket) -> bool:
    return _normalize_resolution_bucket(bucket) == NAIA_ADVANCED_RESOLUTION_BUCKET


def _set_naia_field_text(fields: list[dict], pane: str, prompt: str) -> list[dict]:
    normalized = _normalize_advanced_fields(fields)
    for field in normalized:
        if field["pane"] == pane and field["type"] == "naia":
            field["text"] = prompt
            field["enabled"] = True
            return normalized
    return normalized


def _advanced_pane_parts(fields: list[dict], pane: str) -> dict[str, list[str]]:
    parts = {
        "quality": [],
        "artist": [],
        "trigger_fixed": [],
        "trigger_auto": [],
        "body": [],
    }
    for field in fields:
        if not _as_bool(field.get("enabled"), True):
            continue
        if field.get("pane") != pane:
            continue
        field_type = field.get("type")
        text = str(field.get("text") or "")
        if field_type == "quality":
            parts["quality"].append(text)
        elif field_type == "artist":
            parts["artist"].append(_artist_mix_inline_prompt(text))
        elif field_type == "trigger":
            if _as_bool(field.get("pin"), True):
                parts["trigger_fixed"].append(text)
            else:
                parts["trigger_auto"].append(text)
        else:
            parts["body"].append(text)
    return parts


def _advanced_enabled_pane_fields(fields: list[dict], pane: str) -> list[dict]:
    return [
        field
        for field in fields
        if _as_bool(field.get("enabled"), True) and field.get("pane") == pane
    ]


def _correct_advanced_field_sequence(
    fields: list[dict],
    include_quality: bool,
    artist_overrides: str,
    force_pin_triggers: bool = False,
) -> str:
    chunks: list[str] = []
    pending: list[str] = []

    def flush_pending() -> None:
        if not pending:
            return
        corrected = _correct_builder_prompt(
            _join_prompt_tokens(*pending),
            artist_overrides=artist_overrides,
        )
        if corrected:
            chunks.append(corrected)
        pending.clear()

    for field in fields:
        field_type = field.get("type")
        text = str(field.get("text") or "")
        if field_type == "quality" and not include_quality:
            continue
        if field_type == "artist":
            text = _artist_mix_inline_prompt(text)
        if field_type == "trigger" and (
            _as_bool(field.get("pin"), True) or force_pin_triggers
        ):
            flush_pending()
            trigger_prompt = _join_prompt_tokens(text)
            if trigger_prompt:
                chunks.append(trigger_prompt)
            continue
        pending.append(text)

    flush_pending()
    return _join_prompt_tokens(*chunks)


def _build_advanced_prompts(
    fields: list[dict],
    use_anima_mod_guidance: bool,
    use_negative_anima_mod_guidance: bool,
    pin_trigger_tags_to_front: bool,
) -> tuple[str, str, str, str, bool, bool, str, str]:
    use_amg = _as_bool(use_anima_mod_guidance, False)
    use_negative_amg = _as_bool(use_negative_anima_mod_guidance, False)
    force_pin_triggers = _as_bool(pin_trigger_tags_to_front, False)
    positive = _advanced_pane_parts(fields, "positive")
    negative = _advanced_pane_parts(fields, "negative")
    positive_fields = _advanced_enabled_pane_fields(fields, "positive")
    negative_fields = _advanced_enabled_pane_fields(fields, "negative")

    quality_prompt = _join_prompt_tokens(*positive["quality"])
    artist_prompt = _join_prompt_tokens(*positive["artist"])
    regular_prompt = _correct_advanced_field_sequence(
        positive_fields,
        include_quality=True,
        artist_overrides=artist_prompt,
        force_pin_triggers=force_pin_triggers,
    )
    amg_prompt = _correct_advanced_field_sequence(
        positive_fields,
        include_quality=False,
        artist_overrides=artist_prompt,
        force_pin_triggers=force_pin_triggers,
    )
    metadata_prompt = regular_prompt

    negative_quality_prompt = _join_prompt_tokens(*negative["quality"])
    negative_artist_prompt = _join_prompt_tokens(*negative["artist"])
    negative_regular_prompt = _correct_advanced_field_sequence(
        negative_fields,
        include_quality=True,
        artist_overrides=negative_artist_prompt,
    )
    negative_amg_prompt = _correct_advanced_field_sequence(
        negative_fields,
        include_quality=False,
        artist_overrides=negative_artist_prompt,
    )

    filter_words = resolve_metadata_filter_words()
    metadata_prompt = _filter_metadata_prompt(metadata_prompt, filter_words)
    metadata_negative_prompt = _filter_metadata_prompt(negative_regular_prompt, filter_words)
    output_prompt = amg_prompt if use_amg else regular_prompt
    output_negative_prompt = negative_amg_prompt if use_negative_amg else negative_regular_prompt
    return (
        output_prompt,
        output_negative_prompt,
        quality_prompt,
        negative_quality_prompt,
        use_amg,
        use_negative_amg,
        metadata_prompt,
        metadata_negative_prompt,
    )


def _expand_advanced_wildcard_fields(
    fields: list[dict],
    seed: int,
    mode: str,
) -> tuple[list[dict], dict[str, Any]]:
    mode_key = normalize_prompt_studio_wildcard_mode(mode)
    expanded_fields = _clone_advanced_fields(fields)

    wildcard_fields = []
    wildcard_texts = []
    for field in expanded_fields:
        text = str(field.get("text") or "")
        if has_wildcard_syntax(text):
            wildcard_fields.append(field)
            wildcard_texts.append(text)

    expansions = expand_wildcard_texts(
        wildcard_texts,
        seed=seed,
        mode=mode_key,
    )
    changed = False
    used_keys: list[str] = []
    missing_keys: list[str] = []
    for field, text, result in zip(
        wildcard_fields,
        wildcard_texts,
        expansions,
        strict=True,
    ):
        if result.text != text:
            field["text"] = result.text
            changed = True
        for key in result.used_keys:
            if key not in used_keys:
                used_keys.append(key)
        for key in result.missing_keys:
            if key not in missing_keys:
                missing_keys.append(key)

    return expanded_fields, {
        "changed": changed,
        "used_keys": tuple(used_keys),
        "missing_keys": tuple(missing_keys),
    }


def _advanced_prompt_data_fields(fields: list[dict]) -> list[dict[str, Any]]:
    output = []
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


def _advanced_artist_field_prompt(fields: list[dict], pane: str) -> str:
    # Artist data is sourced only from Advanced artist fields, not from @ tags in other fields.
    return _join_artist_mix_source_prompts(
        *(
            str(field.get("text") or "")
            for field in fields
            if field.get("pane") == pane
            and field.get("type") == "artist"
            and _as_bool(field.get("enabled"), True)
        )
    )


def _advanced_fields_with_artist_override(
    fields: list[dict],
    artist_prompt: str,
) -> list[dict]:
    artist_text = _join_prompt_tokens(artist_prompt)
    output: list[dict] = []
    inserted = False
    for field in fields:
        if field.get("type") == "artist":
            if artist_text and not inserted:
                item = dict(field)
                item["text"] = artist_text
                output.append(item)
                inserted = True
            continue
        output.append(dict(field))

    if artist_text and not inserted:
        insert_at = 0
        for index, field in enumerate(output):
            if field.get("type") == "quality":
                insert_at = index + 1
        output.insert(
            insert_at,
            {
                "id": "artist_mix_override",
                "pane": "positive",
                "type": "artist",
                "label": ADVANCED_FIELD_LABELS["artist"],
                "text": artist_text,
                "height": 72,
                "enabled": True,
                "pin": False,
            },
        )
    return output


def _advanced_prompt_with_artist_override(
    fields: list[dict],
    artist_prompt: str,
    include_quality: bool,
    force_pin_triggers: bool = False,
) -> str:
    return _correct_advanced_field_sequence(
        _advanced_fields_with_artist_override(fields, artist_prompt),
        include_quality=include_quality,
        artist_overrides=artist_prompt,
        force_pin_triggers=force_pin_triggers,
    )


def _build_advanced_prompt_data(
    compat_result: tuple,
    effective_fields: list[dict],
    saved_fields: list[dict],
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
    parameters: dict[str, Any] | None = None,
    artist_mix_mode: str = ARTIST_MIX_MODE_OFF,
    artist_mix_start_percent: float = ARTIST_MIX_DEFAULT_START_PERCENT,
    artist_mix_strength_scale: float = ARTIST_MIX_DEFAULT_STRENGTH_SCALE,
    artist_mix_style_gain: float = ARTIST_MIX_DEFAULT_STYLE_GAIN,
    artist_mix_rms_scale_cap: float = ARTIST_MIX_DEFAULT_RMS_SCALE_CAP,
    artist_mix_exact_top_k: int = ARTIST_MIX_DEFAULT_EXACT_TOP_K,
    artist_mix_cluster_count: int = ARTIST_MIX_DEFAULT_CLUSTER_COUNT,
    artist_mix_dominant_isolation: bool = ARTIST_MIX_DEFAULT_DOMINANT_ISOLATION,
    artist_mix_dominant_threshold: float = ARTIST_MIX_DEFAULT_DOMINANT_THRESHOLD,
) -> dict[str, Any]:
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
    outputs = {
        name: value
        for name, value in zip(PROMPT_STUDIO_ADVANCED_RETURN_NAMES, compat_result)
    }
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
    return {
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


__all__ = ()
