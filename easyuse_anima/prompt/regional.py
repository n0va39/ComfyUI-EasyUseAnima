"""Regional Prompt Studio schema and service facade."""

from __future__ import annotations

import json
import re
from typing import Any, cast

from ..common.values import _as_bool, _as_int
from ..naia.resolution import _ratio_label
from .advanced_fields import (
    ADVANCED_FIELD_LABELS,
    ADVANCED_FIELD_PANES,
    _advanced_default_fields,
    _advanced_field_input_values,
    _advanced_field_socket_name,
    _as_advanced_height,
)
from .contracts import RegionalField
from .regional_builder import (
    REGIONAL_CONFIG_VERSION,
    _normalize_mask_geometry,
    _normalize_mask_ids,
)
from .regional_builder import (
    REGIONAL_PROMPT_BUNDLE_SCHEMA as REGIONAL_PROMPT_BUNDLE_SCHEMA,
)
from .regional_builder import (
    REGIONAL_PROMPT_DATA_SCHEMA as REGIONAL_PROMPT_DATA_SCHEMA,
)
from .regional_builder import (
    REGIONAL_PROMPT_DATA_TYPE as REGIONAL_PROMPT_DATA_TYPE,
)
from .regional_builder import (
    _build_regional_outputs as _build_regional_outputs,
)
from .regional_builder import (
    _conditioning_set_values as _conditioning_set_values,
)
from .regional_builder import (
    _parse_json_object as _parse_json_object,
)
from .regional_builder import (
    _regional_field_prompt as _regional_field_prompt,
)
from .regional_builder import (
    _regional_mask_bounds_area as _regional_mask_bounds_area,
)
from .regional_builder import (
    _regional_payload_canvas as _regional_payload_canvas,
)
from .regional_builder import (
    _regional_union_mask_for_ids as _regional_union_mask_for_ids,
)

REGIONAL_FIELDS_WORKFLOW_PROPERTY = "easyuse_anima_regional_fields"
REGIONAL_CONFIG_WORKFLOW_PROPERTY = "easyuse_anima_regional_config"
REGIONAL_FIELD_TYPES = {"quality", "artist", "trigger", "general"}


def _regional_default_fields() -> list[RegionalField]:
    fields: list[RegionalField] = []
    for field in _advanced_default_fields():
        if field.get("type") == "naia":
            continue
        item = cast(RegionalField, dict(field))
        item["mask_ids"] = []
        fields.append(item)
    return fields


def _regional_fields_json(fields: list[RegionalField] | None = None) -> str:
    return json.dumps(
        fields if fields is not None else _regional_default_fields(),
        ensure_ascii=False,
        separators=(",", ":"),
    )


def _normalize_regional_fields(value: str | list | None) -> list[RegionalField]:
    raw = value
    if isinstance(value, str):
        try:
            raw = json.loads(value or "[]")
        except json.JSONDecodeError:
            raw = []
    if not isinstance(raw, list):
        raw = []
    if not raw:
        raw = _regional_default_fields()

    fields: list[RegionalField] = []
    seen_trigger = False
    for index, item in enumerate(raw):
        if not isinstance(item, dict):
            continue
        pane = str(item.get("pane") or "positive").strip().lower()
        if pane not in ADVANCED_FIELD_PANES:
            pane = "positive"
        field_type = str(item.get("type") or "general").strip().lower()
        if field_type not in REGIONAL_FIELD_TYPES:
            field_type = "general"
        if pane == "negative" and field_type == "trigger":
            field_type = "general"
        if field_type == "trigger":
            if seen_trigger:
                continue
            seen_trigger = True
            pane = "positive"
        default_label = ADVANCED_FIELD_LABELS.get(field_type, ADVANCED_FIELD_LABELS["general"])
        label = str(item.get("label") or default_label).strip() or default_label
        field_id = str(item.get("id") or f"{pane}_{field_type}_{index + 1}").strip()
        if not field_id:
            field_id = f"{pane}_{field_type}_{index + 1}"
        mask_ids = _normalize_mask_ids(item.get("mask_ids"))
        if pane != "positive":
            mask_ids = []
        fields.append({
            "id": field_id,
            "pane": pane,
            "type": field_type,
            "label": label,
            "text": str(item.get("text") or ""),
            "height": _as_advanced_height(item.get("height"), 72),
            "enabled": _as_bool(item.get("enabled"), True),
            "pin": _as_bool(item.get("pin"), field_type == "trigger"),
            "collapsed": _as_bool(item.get("collapsed"), False),
            "mask_ids": mask_ids,
        })

    return fields or _regional_default_fields()


def _clone_regional_fields(fields: list[RegionalField]) -> list[RegionalField]:
    return [
        cast(RegionalField, {
            **dict(field),
            "mask_ids": list(field.get("mask_ids") or []),
        })
        for field in fields
    ]


def _apply_regional_field_inputs(
    fields: list[RegionalField],
    field_inputs: dict,
) -> list[RegionalField]:
    values = _advanced_field_input_values(field_inputs)
    if not values:
        return _clone_regional_fields(fields)

    effective = _clone_regional_fields(fields)
    for field in effective:
        name = _advanced_field_socket_name(field)
        if name in values:
            field["text"] = values[name]
    return effective


def _regional_default_config(width: int = 1024, height: int = 1024) -> dict[str, Any]:
    return {
        "version": REGIONAL_CONFIG_VERSION,
        "canvas": {
            "width": int(width),
            "height": int(height),
            "aspect_ratio": _ratio_label(width, height),
            "source": "resolution_fields",
        },
        "mask_authoring": {
            "render_space": "image_pixels",
            "storage_space": "normalized_canvas",
            "preview_enabled": True,
        },
        "global_prompt": "",
        "negative_prompt": "",
        "next_mask_id": 1,
        "masks": [],
        "regional_enabled": False,
        "mask_prompts": [],
        "assignments": [],
        "artist_mix": {},
        "conditioning_settings": {},
        "regional_settings": {},
    }


def _normalize_regional_mask(value, fallback_id: int) -> dict[str, Any] | None:
    if not isinstance(value, dict):
        return None
    mask_id = _as_int(value.get("mask_id", value.get("id")), fallback_id)
    if mask_id <= 0:
        return None
    default_label = f"Mask {mask_id}"
    name = str(value.get("name") or "").strip()
    label = str(value.get("label") or name or default_label).strip() or default_label
    color = str(value.get("color") or "#3b82f6").strip() or "#3b82f6"
    if not re.fullmatch(r"#[0-9A-Fa-f]{6}", color):
        color = "#3b82f6"
    mask = {
        "mask_id": mask_id,
        "label": label,
        "name": name,
        "color": color,
        "enabled": _as_bool(value.get("enabled"), True),
        "geometry": _normalize_mask_geometry(value.get("geometry")),
    }
    if isinstance(value.get("strokes"), list):
        mask["strokes"] = value["strokes"]
    if isinstance(value.get("shapes"), list):
        mask["shapes"] = value["shapes"]
    return mask


def _normalize_regional_config(
    value: str | dict | None,
    width: int = 1024,
    height: int = 1024,
) -> dict[str, Any]:
    raw = value
    if isinstance(value, str):
        try:
            raw = json.loads(value or "{}")
        except json.JSONDecodeError:
            raw = {}
    if not isinstance(raw, dict):
        raw = {}

    config = _regional_default_config(width, height)
    for key in ("artist_mix", "conditioning_settings", "regional_settings"):
        if isinstance(raw.get(key), dict):
            config[key] = raw[key]
    authoring = raw.get("mask_authoring")
    if isinstance(authoring, dict):
        merged = dict(config["mask_authoring"])
        merged.update({k: v for k, v in authoring.items() if isinstance(k, str)})
        config["mask_authoring"] = merged

    masks: list[dict[str, Any]] = []
    used_ids: set[int] = set()
    raw_masks = raw.get("masks")
    if not isinstance(raw_masks, list):
        raw_masks = raw.get("regions") if isinstance(raw.get("regions"), list) else []
    for index, item in enumerate(raw_masks):
        mask = _normalize_regional_mask(item, index + 1)
        if mask is None or mask["mask_id"] in used_ids:
            continue
        used_ids.add(mask["mask_id"])
        masks.append(mask)
    next_mask_id = max([_as_int(raw.get("next_mask_id"), 1), 1, *(mask["mask_id"] + 1 for mask in masks)])
    config["next_mask_id"] = next_mask_id
    config["masks"] = masks
    config["canvas"] = {
        "width": int(width),
        "height": int(height),
        "aspect_ratio": _ratio_label(width, height),
        "source": "resolution_fields",
    }
    return config


def _regional_config_json(config: dict[str, Any] | None = None) -> str:
    return json.dumps(
        config if config is not None else _regional_default_config(),
        ensure_ascii=False,
        separators=(",", ":"),
    )


__all__ = ()
