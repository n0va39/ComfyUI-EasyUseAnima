"""Advanced Prompt Studio field normalization and sequence services."""

from __future__ import annotations

import json
import re
from collections.abc import Sequence
from typing import TypeVar, cast

from ..common.values import _as_bool, _as_int, _single_value
from .artist_mix_primitives import (
    _artist_mix_inline_prompt,
    _join_artist_mix_source_prompts,
)
from .contracts import AdvancedField, PromptField
from .fields import (
    DEFAULT_QUALITY_TAGS,
    DEFAULT_TRAILING_QUALITY_TAGS,
    _correct_builder_prompt,
    _join_prompt_tokens,
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

_ADVANCED_FIELD_SOCKET_PREFIX = "field_"
_ADVANCED_FIELD_SOCKET_RE = re.compile(r"[^A-Za-z0-9_]")
_PromptFieldT = TypeVar("_PromptFieldT", bound=PromptField)


def _advanced_default_fields() -> list[AdvancedField]:
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


def _advanced_fields_json(fields: list[AdvancedField] | None = None) -> str:
    return json.dumps(
        fields if fields is not None else _advanced_default_fields(),
        ensure_ascii=False,
        separators=(",", ":"),
    )


def _as_advanced_height(value, default: int = 72) -> int:
    return max(36, _as_int(value, default))


def _normalize_advanced_fields(value: str | list | None) -> list[AdvancedField]:
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

    fields: list[AdvancedField] = []
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


def _clone_advanced_fields(fields: list[AdvancedField]) -> list[AdvancedField]:
    return [cast(AdvancedField, dict(field)) for field in fields]


def _advanced_field_socket_name(field: PromptField) -> str:
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


def _apply_advanced_field_inputs(
    fields: list[AdvancedField],
    field_inputs: dict,
) -> list[AdvancedField]:
    values = _advanced_field_input_values(field_inputs)
    if not values:
        return _clone_advanced_fields(fields)

    effective = _clone_advanced_fields(fields)
    for field in effective:
        name = _advanced_field_socket_name(field)
        if name in values:
            field["text"] = values[name]
    return effective


def _advanced_pane_parts(
    fields: list[AdvancedField],
    pane: str,
) -> dict[str, list[str]]:
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


def _advanced_enabled_pane_fields(
    fields: list[_PromptFieldT],
    pane: str,
) -> list[_PromptFieldT]:
    return [
        field
        for field in fields
        if _as_bool(field.get("enabled"), True) and field.get("pane") == pane
    ]


def _correct_advanced_field_sequence(
    fields: Sequence[PromptField],
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


def _advanced_artist_field_prompt(fields: Sequence[PromptField], pane: str) -> str:
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
    fields: list[AdvancedField],
    artist_prompt: str,
) -> list[AdvancedField]:
    artist_text = _join_prompt_tokens(artist_prompt)
    output: list[AdvancedField] = []
    inserted = False
    for field in fields:
        if field.get("type") == "artist":
            if artist_text and not inserted:
                item = cast(AdvancedField, dict(field))
                item["text"] = artist_text
                output.append(item)
                inserted = True
            continue
        output.append(cast(AdvancedField, dict(field)))

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
    fields: list[AdvancedField],
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


__all__ = ()
