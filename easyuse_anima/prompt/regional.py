"""Regional Prompt Studio schema and service helpers."""

from __future__ import annotations

import json
import re
from typing import Any, cast

from ..common.values import _as_bool, _as_float, _as_int, _single_value
from ..naia.resolution import _ratio_label
from .advanced import (
    _advanced_default_fields,
    _advanced_field_input_values,
    _advanced_field_socket_name,
    _as_advanced_height,
    _correct_advanced_field_sequence,
)
from .contracts import RegionalField
from ..settings.service import resolve_metadata_filter_words
from .fields import _filter_metadata_prompt, _join_prompt_tokens


REGIONAL_FIELDS_WORKFLOW_PROPERTY = "easyuse_anima_regional_fields"
REGIONAL_CONFIG_WORKFLOW_PROPERTY = "easyuse_anima_regional_config"
REGIONAL_FIELD_TYPES = {"quality", "artist", "trigger", "general"}
REGIONAL_CONFIG_VERSION = 1
REGIONAL_PROMPT_DATA_TYPE = "EASYUSE_ANIMA_REGIONAL_PROMPT_DATA"
REGIONAL_PROMPT_DATA_SCHEMA = "easyuse_anima_prompt_studio_regional"
REGIONAL_PROMPT_BUNDLE_SCHEMA = "easyuse_anima_prompt_studio_regional_bundle"

ADVANCED_FIELD_PANES = {"positive", "negative"}
ADVANCED_FIELD_LABELS = {
    "quality": "Quality Tags",
    "artist": "Artist Tags",
    "trigger": "Trigger Words",
    "general": "General Tags",
}


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


def _normalize_mask_ids(value) -> list[int]:
    value = _single_value(value)
    if value is None:
        return []
    if isinstance(value, str):
        raw_values = re.split(r"[,;\s]+", value.strip())
    elif isinstance(value, (list, tuple, set)):
        raw_values = list(value)
    else:
        raw_values = [value]

    mask_ids: list[int] = []
    for raw in raw_values:
        mask_id = _as_int(raw, 0)
        if mask_id > 0 and mask_id not in mask_ids:
            mask_ids.append(mask_id)
    return mask_ids


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


def _normalize_mask_geometry(value) -> dict[str, float]:
    if not isinstance(value, dict):
        value = {}
    shape = str(value.get("type") or "rect").strip().lower()
    if shape not in {"rect", "ellipse"}:
        shape = "rect"
    x = max(0.0, min(0.99, _as_float(value.get("x"), 0.1)))
    y = max(0.0, min(0.99, _as_float(value.get("y"), 0.1)))
    width = max(0.01, min(1.0, _as_float(value.get("width"), 0.35)))
    height = max(0.01, min(1.0, _as_float(value.get("height"), 0.35)))
    if x + width > 1.0:
        width = max(0.01, 1.0 - x)
    if y + height > 1.0:
        height = max(0.01, 1.0 - y)
    return {
        "type": shape,
        "x": round(x, 6),
        "y": round(y, 6),
        "width": round(width, 6),
        "height": round(height, 6),
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


def _regional_field_prompt(field: RegionalField, artist_overrides: str = "") -> str:
    return _correct_advanced_field_sequence(
        [field],
        include_quality=True,
        artist_overrides=artist_overrides,
        force_pin_triggers=True,
    )


def _build_regional_outputs(
    fields: list[RegionalField],
    config: dict[str, Any],
    width: int,
    height: int,
) -> tuple[str, str, str, str, dict[str, Any]]:
    positive_fields = [
        field
        for field in fields
        if field.get("pane") == "positive" and _as_bool(field.get("enabled"), True)
    ]
    negative_fields = [
        field
        for field in fields
        if field.get("pane") == "negative" and _as_bool(field.get("enabled"), True)
    ]
    global_positive_fields = [
        field for field in positive_fields if not _normalize_mask_ids(field.get("mask_ids"))
    ]
    mask_positive_fields = [
        field for field in positive_fields if _normalize_mask_ids(field.get("mask_ids"))
    ]

    global_artist_prompt = _join_prompt_tokens(
        *(str(field.get("text") or "") for field in global_positive_fields if field.get("type") == "artist")
    )
    all_artist_prompt = _join_prompt_tokens(
        *(str(field.get("text") or "") for field in positive_fields if field.get("type") == "artist")
    )
    negative_artist_prompt = _join_prompt_tokens(
        *(str(field.get("text") or "") for field in negative_fields if field.get("type") == "artist")
    )

    positive_prompt = _correct_advanced_field_sequence(
        global_positive_fields,
        include_quality=True,
        artist_overrides=global_artist_prompt,
        force_pin_triggers=True,
    )
    negative_prompt = _correct_advanced_field_sequence(
        negative_fields,
        include_quality=True,
        artist_overrides=negative_artist_prompt,
    )
    metadata_prompt = _correct_advanced_field_sequence(
        positive_fields,
        include_quality=True,
        artist_overrides=all_artist_prompt,
        force_pin_triggers=True,
    )

    filter_words = resolve_metadata_filter_words()
    metadata_prompt = _filter_metadata_prompt(metadata_prompt, filter_words)
    metadata_negative_prompt = _filter_metadata_prompt(negative_prompt, filter_words)

    masks = config.get("masks") if isinstance(config.get("masks"), list) else []
    enabled_mask_ids = {
        _as_int(mask.get("mask_id"), 0)
        for mask in masks
        if isinstance(mask, dict) and _as_bool(mask.get("enabled"), True)
    }
    assignments: list[dict[str, Any]] = []
    mask_prompts: list[dict[str, Any]] = []
    for field in mask_positive_fields:
        mask_ids = _normalize_mask_ids(field.get("mask_ids"))
        valid_mask_ids = [mask_id for mask_id in mask_ids if mask_id in enabled_mask_ids]
        missing_mask_ids = [mask_id for mask_id in mask_ids if mask_id not in enabled_mask_ids]
        prompt = _regional_field_prompt(field, all_artist_prompt)
        assignments.append({
            "field_id": str(field.get("id") or ""),
            "mask_ids": mask_ids,
            "valid_mask_ids": valid_mask_ids,
            "missing_mask_ids": missing_mask_ids,
        })
        mask_prompts.append({
            "field_id": str(field.get("id") or ""),
            "type": str(field.get("type") or "general"),
            "label": str(field.get("label") or ""),
            "text": str(field.get("text") or ""),
            "prompt": prompt,
            "mask_ids": mask_ids,
            "valid_mask_ids": valid_mask_ids,
            "missing_mask_ids": missing_mask_ids,
        })

    regional_enabled = any(entry["valid_mask_ids"] for entry in mask_prompts)
    regional_prompt_data = {
        **config,
        "version": REGIONAL_CONFIG_VERSION,
        "schema": REGIONAL_PROMPT_BUNDLE_SCHEMA,
        "canvas": {
            "width": int(width),
            "height": int(height),
            "aspect_ratio": _ratio_label(width, height),
            "source": "resolution_fields",
        },
        "global_prompt": positive_prompt,
        "negative_prompt": negative_prompt,
        "metadata_prompt": metadata_prompt,
        "metadata_negative_prompt": metadata_negative_prompt,
        "masks": masks,
        "regional_enabled": regional_enabled,
        "mask_prompts": mask_prompts,
        "assignments": assignments,
    }
    model_patch_data = {
        "version": REGIONAL_CONFIG_VERSION,
        "regional_attention": {
            "enabled": regional_enabled,
            "assignments": assignments,
            "masks": [
                {
                    "mask_id": mask.get("mask_id"),
                    "label": mask.get("label"),
                    "name": mask.get("name"),
                    "enabled": _as_bool(mask.get("enabled"), True),
                }
                for mask in masks
                if isinstance(mask, dict)
            ],
        },
        "layout_control": {
            "canvas": regional_prompt_data["canvas"],
        },
        "global_mod_guidance": {},
        "artist_mix": config.get("artist_mix") if isinstance(config.get("artist_mix"), dict) else {},
        "compatibility": {
            "schema": REGIONAL_PROMPT_DATA_SCHEMA,
            "version": REGIONAL_CONFIG_VERSION,
            "mask_scoped_prompts": True,
        },
    }
    regional_prompt_data["model_patch_data"] = model_patch_data
    return (
        positive_prompt,
        negative_prompt,
        metadata_prompt,
        metadata_negative_prompt,
        regional_prompt_data,
    )


def _parse_json_object(value: str | dict | None) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value or "{}")
        except json.JSONDecodeError as exc:
            raise ValueError("[EasyUseAnima] regional_prompt_data is not valid JSON.") from exc
        if isinstance(parsed, dict):
            return parsed
    return {}


def _regional_payload_canvas(payload: dict[str, Any]) -> tuple[int, int]:
    canvas = payload.get("canvas") if isinstance(payload.get("canvas"), dict) else {}
    width = max(8, _as_int(canvas.get("width"), 1024))
    height = max(8, _as_int(canvas.get("height"), 1024))
    return width, height


def _conditioning_set_values(conditioning, values: dict[str, Any]) -> list:
    out = []
    for item in conditioning or []:
        if isinstance(item, (list, tuple)) and len(item) >= 2 and isinstance(item[1], dict):
            metadata = dict(item[1])
            metadata.update(values)
            out.append([item[0], metadata])
        else:
            out.append(item)
    return out


def _regional_union_mask_for_ids(
    payload: dict[str, Any],
    mask_ids: list[int],
    width: int,
    height: int,
):
    try:
        import torch  # type: ignore
    except Exception as exc:
        raise RuntimeError("[EasyUseAnima] torch is required to convert regional masks to conditioning.") from exc

    selected_ids = set(mask_ids)
    mask_tensor = torch.zeros((height, width), dtype=torch.float32)
    masks = payload.get("masks") if isinstance(payload.get("masks"), list) else []
    for mask in masks:
        if not isinstance(mask, dict) or not _as_bool(mask.get("enabled"), True):
            continue
        mask_id = _as_int(mask.get("mask_id"), 0)
        if mask_id not in selected_ids:
            continue
        geometry = _normalize_mask_geometry(mask.get("geometry"))
        x0 = max(0, min(width - 1, int(round(geometry["x"] * width))))
        y0 = max(0, min(height - 1, int(round(geometry["y"] * height))))
        x1 = max(x0 + 1, min(width, int(round((geometry["x"] + geometry["width"]) * width))))
        y1 = max(y0 + 1, min(height, int(round((geometry["y"] + geometry["height"]) * height))))
        if geometry["type"] == "ellipse":
            yy = torch.arange(y0, y1, dtype=torch.float32).unsqueeze(1)
            xx = torch.arange(x0, x1, dtype=torch.float32).unsqueeze(0)
            cx = (x0 + x1 - 1) / 2.0
            cy = (y0 + y1 - 1) / 2.0
            rx = max(0.5, (x1 - x0) / 2.0)
            ry = max(0.5, (y1 - y0) / 2.0)
            ellipse = (((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2) <= 1.0
            mask_tensor[y0:y1, x0:x1] = torch.maximum(mask_tensor[y0:y1, x0:x1], ellipse.to(torch.float32))
        else:
            mask_tensor[y0:y1, x0:x1] = 1.0
    return mask_tensor.unsqueeze(0)


def _regional_mask_bounds_area(
    mask,
    canvas_width: int | None = None,
    canvas_height: int | None = None,
) -> tuple | None:
    try:
        import torch  # type: ignore
    except Exception:
        return None

    if not hasattr(mask, "shape"):
        return None
    if len(mask.shape) == 3:
        mask_2d = torch.max(torch.abs(mask), dim=0).values
    elif len(mask.shape) == 2:
        mask_2d = mask
    else:
        return None

    if mask_2d.numel() == 0 or torch.max(mask_2d != 0) == False:
        return None
    y, x = torch.where(mask_2d != 0)
    height = max(1, int(canvas_height or mask_2d.shape[-2]))
    width = max(1, int(canvas_width or mask_2d.shape[-1]))
    y0 = int(torch.min(y).item())
    y1 = int(torch.max(y).item())
    x0 = int(torch.min(x).item())
    x1 = int(torch.max(x).item())
    latent_height = max(1, height // 8)
    latent_width = max(1, width // 8)
    area_y = max(0, min(latent_height - 1, round(y0 / height * latent_height)))
    area_x = max(0, min(latent_width - 1, round(x0 / width * latent_width)))
    area_height = max(1, round((y1 - y0 + 1) / height * latent_height))
    area_width = max(1, round((x1 - x0 + 1) / width * latent_width))
    area_height = min(area_height, latent_height - area_y)
    area_width = min(area_width, latent_width - area_x)
    return (
        area_height,
        area_width,
        area_y,
        area_x,
    )


__all__ = ()
