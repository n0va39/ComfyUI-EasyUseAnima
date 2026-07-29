"""Structured Prompt Studio data helpers."""
from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any, cast

from ..common.values import _as_bool, _as_int
from .contracts import JsonValue, PromptDataCompatResult, PromptDataRead

PROMPT_DATA_VERSION = 1
PROMPT_DATA_TYPE = "EASYUSE_ANIMA_PROMPT_DATA"
PROMPT_DATA_SCHEMA = "easyuse_anima_prompt_studio_advanced_v2"

PROMPT_DATA_COMPAT_RETURN_TYPES = (
    "STRING", "STRING", "STRING", "STRING", "BOOLEAN",
    "BOOLEAN", "STRING", "STRING", "INT", "INT",
)
PROMPT_DATA_COMPAT_RETURN_NAMES = (
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
PROMPT_DATA_COMPAT_OUTPUT_TOOLTIPS = (
    "Final positive prompt assembled from enabled positive fields.",
    "Final negative prompt assembled from enabled negative fields.",
    "Positive quality fields routed to Anima Mod Guidance.",
    "Negative quality fields routed to Anima Mod Guidance.",
    "Boolean flag passed through for Anima Mod Guidance workflow control.",
    "Boolean flag passed through for negative Anima Mod Guidance workflow control.",
    "Positive metadata prompt with metadata filters applied.",
    "Negative metadata prompt with metadata filters applied.",
    "Selected latent width.",
    "Selected latent height.",
)

def _normalize_prompt_data(value: str | dict | None) -> dict[str, object]:
    if isinstance(value, dict):
        return cast(dict[str, object], dict(value))
    if isinstance(value, str):
        try:
            parsed = json.loads(value or "{}")
        except json.JSONDecodeError:
            parsed = {}
        if isinstance(parsed, dict):
            return cast(dict[str, object], parsed)
    return {}

def _prompt_data_nested(data: PromptDataRead, key: str) -> PromptDataRead:
    value = data.get(key)
    return cast(dict[str, object], value) if isinstance(value, dict) else {}

def _prompt_data_output(
    data: PromptDataRead,
    name: str,
    default: object = None,
) -> object:
    outputs = _prompt_data_nested(data, "outputs")
    if name in outputs:
        return outputs[name]
    if name in data:
        return data[name]

    mod_guidance = _prompt_data_nested(data, "mod_guidance")
    anima_mod_guidance = _prompt_data_nested(data, "anima_mod_guidance")
    resolution = _prompt_data_nested(data, "resolution")
    fallbacks = {
        "positive_prompt": data.get("prompt", default),
        "anima_mod_guidance_quality_tags": mod_guidance.get(
            "quality_tags",
            anima_mod_guidance.get("quality_tags", default),
        ),
        "anima_mod_guidance_negative_prompt": mod_guidance.get(
            "negative_prompt",
            anima_mod_guidance.get("negative_prompt", default),
        ),
        "use_anima_mod_guidance": mod_guidance.get(
            "enabled",
            anima_mod_guidance.get("use_positive", default),
        ),
        "use_negative_anima_mod_guidance": mod_guidance.get(
            "negative_enabled",
            anima_mod_guidance.get("use_negative", default),
        ),
        "width": resolution.get("width", default),
        "height": resolution.get("height", default),
    }
    return fallbacks.get(name, default)

def _prompt_data_input_default(input_spec):
    if not isinstance(input_spec, tuple):
        return None
    options = input_spec[1] if len(input_spec) > 1 and isinstance(input_spec[1], dict) else {}
    if "default" in options:
        return options["default"]
    input_type = input_spec[0] if input_spec else None
    if isinstance(input_type, (list, tuple)) and input_type:
        return input_type[0]
    if input_type == "BOOLEAN":
        return False
    if input_type == "INT":
        return 0
    if input_type == "FLOAT":
        return 0.0
    if input_type == "STRING":
        return ""
    return None

def _prompt_data_json_safe(value: object) -> JsonValue:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, (list, tuple)):
        return [_prompt_data_json_safe(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _prompt_data_json_safe(item) for key, item in value.items()}
    return str(value)

def _prompt_data_parameter_snapshot(
    input_defs: dict[str, Any],
    values: dict[str, Any],
    ui_payload: dict[str, Any] | None = None,
) -> dict[str, JsonValue]:
    ui_payload = ui_payload if isinstance(ui_payload, dict) else {}
    snapshot: dict[str, JsonValue] = {}
    for name, input_spec in input_defs.items():
        if name in ui_payload:
            value = ui_payload[name]
        elif name in values:
            value = values[name]
        else:
            value = _prompt_data_input_default(input_spec)
        snapshot[name] = _prompt_data_json_safe(value)
    return snapshot

def _advanced_outputs_from_prompt_data(
    value: str | dict | None,
) -> PromptDataCompatResult:
    data = _normalize_prompt_data(value)
    return (
        str(_prompt_data_output(data, "positive_prompt", "") or ""),
        str(_prompt_data_output(data, "negative_prompt", "") or ""),
        str(_prompt_data_output(data, "anima_mod_guidance_quality_tags", "") or ""),
        str(_prompt_data_output(data, "anima_mod_guidance_negative_prompt", "") or ""),
        _as_bool(_prompt_data_output(data, "use_anima_mod_guidance", False), False),
        _as_bool(_prompt_data_output(data, "use_negative_anima_mod_guidance", False), False),
        str(_prompt_data_output(data, "metadata_prompt", "") or ""),
        str(_prompt_data_output(data, "metadata_negative_prompt", "") or ""),
        _as_int(_prompt_data_output(data, "width", 1024), 1024),
        _as_int(_prompt_data_output(data, "height", 1024), 1024),
    )

def _copy_prompt_data_for_update(value: str | dict | None) -> dict[str, object]:
    data = dict(_normalize_prompt_data(value))
    for key in ("outputs", "mod_guidance", "anima_mod_guidance", "resolution"):
        nested = data.get(key)
        if isinstance(nested, dict):
            data[key] = dict(nested)
    return data

def _set_prompt_data_output(
    data: dict[str, object],
    name: str,
    value: object,
) -> None:
    outputs = data.setdefault("outputs", {})
    if not isinstance(outputs, dict):
        outputs = {}
        data["outputs"] = outputs
    outputs[name] = value

    if name == "positive_prompt":
        data["positive_prompt"] = str(value or "")
        data["prompt"] = data["positive_prompt"]
    elif name == "negative_prompt":
        data["negative_prompt"] = str(value or "")
    elif name == "metadata_prompt":
        data["metadata_prompt"] = str(value or "")
    elif name == "metadata_negative_prompt":
        data["metadata_negative_prompt"] = str(value or "")
    elif name == "width":
        width = _as_int(value, 1024)
        data["width"] = width
        resolution = data.setdefault("resolution", {})
        if isinstance(resolution, dict):
            resolution["width"] = width
    elif name == "height":
        height = _as_int(value, 1024)
        data["height"] = height
        resolution = data.setdefault("resolution", {})
        if isinstance(resolution, dict):
            resolution["height"] = height
    elif name == "anima_mod_guidance_quality_tags":
        mod_guidance = data.setdefault("mod_guidance", {})
        anima_mod_guidance = data.setdefault("anima_mod_guidance", {})
        if isinstance(mod_guidance, dict):
            mod_guidance["quality_tags"] = str(value or "")
        if isinstance(anima_mod_guidance, dict):
            anima_mod_guidance["quality_tags"] = str(value or "")
    elif name == "anima_mod_guidance_negative_prompt":
        mod_guidance = data.setdefault("mod_guidance", {})
        anima_mod_guidance = data.setdefault("anima_mod_guidance", {})
        if isinstance(mod_guidance, dict):
            mod_guidance["negative_prompt"] = str(value or "")
        if isinstance(anima_mod_guidance, dict):
            anima_mod_guidance["negative_prompt"] = str(value or "")
    elif name == "use_anima_mod_guidance":
        enabled = _as_bool(value, False)
        mod_guidance = data.setdefault("mod_guidance", {})
        anima_mod_guidance = data.setdefault("anima_mod_guidance", {})
        if isinstance(mod_guidance, dict):
            mod_guidance["enabled"] = enabled
        if isinstance(anima_mod_guidance, dict):
            anima_mod_guidance["use_positive"] = enabled
    elif name == "use_negative_anima_mod_guidance":
        enabled = _as_bool(value, False)
        mod_guidance = data.setdefault("mod_guidance", {})
        anima_mod_guidance = data.setdefault("anima_mod_guidance", {})
        if isinstance(mod_guidance, dict):
            mod_guidance["negative_enabled"] = enabled
        if isinstance(anima_mod_guidance, dict):
            anima_mod_guidance["use_negative"] = enabled

def _apply_prompt_data_overrides(
    value: str | dict | None,
    overrides: Mapping[str, object],
) -> dict[str, object]:
    data = _copy_prompt_data_for_update(value)
    for name in PROMPT_DATA_COMPAT_RETURN_NAMES:
        if name not in overrides:
            continue
        _set_prompt_data_output(data, name, overrides[name])
    return data

__all__ = ()
