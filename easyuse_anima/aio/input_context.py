"""Pure helpers for the serialized AiO input context."""

from __future__ import annotations

from typing import Any

from ..prompt.data import _prompt_data_json_safe


def _easy_use_anima_input_signature(value) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {"type": str(type(value).__name__)}
    return {
        "schema": value.get("schema"),
        "version": value.get("version"),
        "resource_info": _prompt_data_json_safe(value.get("resource_info", {})),
        "input_settings": _prompt_data_json_safe(value.get("input_settings", {})),
        "prompt_data": _prompt_data_json_safe(value.get("prompt_data", {})),
    }


def _require_easy_use_anima_input(value) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise RuntimeError("[EasyUseAnima] easy use anima input is missing or invalid.")
    missing = [
        key
        for key in ("prompt_data", "resource_info", "input_settings")
        if key not in value
    ]
    if missing:
        raise RuntimeError(
            "[EasyUseAnima] easy use anima input is missing required value(s): "
            + ", ".join(missing)
        )
    return value


__all__ = ()
