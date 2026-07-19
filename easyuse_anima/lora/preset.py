"""LoRA preset profile selection and formatting helpers."""

from __future__ import annotations

import json
from typing import Any

from ..common.values import _as_int

def _unbound_correct_builder_prompt(*_args, **_kwargs):
    raise RuntimeError("LoRA preset prompt-correction dependency is not bound.")


_correct_builder_prompt = _unbound_correct_builder_prompt


def _default_resolve_helper(name):
    return globals()[name]


_resolve_helper = _default_resolve_helper


def _runtime_helper(name):
    return _resolve_helper(name)


def _bind_lora_preset_runtime(*, correct_builder_prompt, resolve_helper) -> None:
    global _correct_builder_prompt, _resolve_helper
    _correct_builder_prompt = correct_builder_prompt
    _resolve_helper = resolve_helper


def _profile_key(profile_index: int) -> str:
    return str(max(1, _runtime_helper("_as_int")(profile_index, 1)))


def _wrap_profile_index(profile_index: int, profile_count: int) -> int:
    count = max(1, min(16, _runtime_helper("_as_int")(profile_count, 1)))
    index = max(1, _runtime_helper("_as_int")(profile_index, 1))
    return ((index - 1) % count) + 1


def _load_profile_data(profile_data: Any) -> dict[str, dict]:
    if isinstance(profile_data, dict):
        raw = profile_data
    else:
        try:
            raw = json.loads(str(profile_data or "{}"))
        except (TypeError, ValueError):
            raw = {}
    if not isinstance(raw, dict):
        return {}
    profiles: dict[str, dict] = {}
    for key, value in raw.items():
        if isinstance(value, dict):
            profiles[str(key)] = value
    return profiles


def _get_loras_list(kwargs: dict) -> list[dict]:
    loras_data = kwargs.get("loras")
    if isinstance(loras_data, dict) and "__value__" in loras_data:
        loras_data = loras_data["__value__"]
    if isinstance(loras_data, str):
        try:
            loras_data = json.loads(loras_data or "[]")
        except (TypeError, ValueError):
            loras_data = []
    if not isinstance(loras_data, list):
        return []
    return [item for item in loras_data if isinstance(item, dict)]


def _correct_style_prompt(prompt: str) -> str:
    return _correct_builder_prompt(prompt)


def _format_strength(value: float) -> str:
    text = f"{float(value):.6f}".rstrip("0").rstrip(".")
    return text or "0"


def _select_profile_values(
    profile_index: int,
    profile_count: int,
    profile_data: str,
    style_prompt: str,
    kwargs: dict,
) -> tuple[str, list[dict], int]:
    selected_index = _runtime_helper("_wrap_profile_index")(profile_index, profile_count)
    profile = _runtime_helper("_load_profile_data")(profile_data).get(
        _runtime_helper("_profile_key")(selected_index),
        {},
    )
    selected_style = str(profile.get("style_prompt", style_prompt or ""))
    profile_loras = profile.get("loras")
    if isinstance(profile_loras, list):
        loras = [item for item in profile_loras if isinstance(item, dict)]
    else:
        loras = _runtime_helper("_get_loras_list")(kwargs)
    return selected_style, loras, selected_index


__all__ = ()
