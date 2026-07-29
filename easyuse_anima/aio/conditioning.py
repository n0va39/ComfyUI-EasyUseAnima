"""AiO conditioning preparation helpers."""

from __future__ import annotations

from typing import Any

from ..common.values import _as_bool
from ..infrastructure.comfy.wiring import resolve_comfy_host_helper
from ..prompt.advanced import (
    _advanced_artist_field_prompt,
    _advanced_enabled_pane_fields,
    _correct_advanced_field_sequence,
    _normalize_advanced_fields,
)
from ..prompt.contracts import AdvancedField
from ..prompt.data import _normalize_prompt_data
from .generation_defaults import AIO_USDU_PROMPT_FULL, AIO_USDU_PROMPT_NO_GENERAL
from .negpip import _aio_negpip_execution_prompts


def _missing_host_helper(name: str):
    raise RuntimeError(
        f"[EasyUseAnima] AiO conditioning Comfy host helper is unavailable: {name}"
    )


def _encode_with_comfy_clip(clip, text: str):
    helper = resolve_comfy_host_helper(
        "_encode_with_comfy_clip",
        _missing_host_helper,
    )
    return helper(clip, text)


def _aio_prompt_data_fields_for_usdu(
    prompt_data: str | dict | None,
) -> list[AdvancedField]:
    data = _normalize_prompt_data(prompt_data)
    fields = data.get("fields")
    if not isinstance(fields, list):
        fields = data.get("saved_fields")
    return _normalize_advanced_fields(fields)


def _aio_usdu_prompt_without_general(
    prompt_data: str | dict | None,
    pane: str,
    include_quality: bool,
) -> tuple[str, bool]:
    fields = _aio_prompt_data_fields_for_usdu(prompt_data)
    if not fields:
        return "", False
    allowed_types = {"artist", "trigger"}
    if include_quality:
        allowed_types.add("quality")
    selected = [
        field
        for field in _advanced_enabled_pane_fields(fields, pane)
        if field.get("type") in allowed_types
    ]
    if not selected:
        return "", True
    artist_prompt = _advanced_artist_field_prompt(selected, pane)
    force_pin_triggers = _as_bool(
        _normalize_prompt_data(prompt_data).get("pin_trigger_tags_to_front"),
        False,
    )
    return (
        _correct_advanced_field_sequence(
            selected,
            include_quality=include_quality,
            artist_overrides=artist_prompt,
            force_pin_triggers=force_pin_triggers,
        ),
        True,
    )


def _aio_usdu_conditioning(
    clip,
    positive,
    negative,
    usdu_settings: dict[str, Any],
    quality_tags: str,
    quality_neg: str,
    prompt_data: str | dict | None = None,
    exclude_positive_quality: bool = False,
    exclude_negative_quality: bool = False,
    negpip_mode: str = "off",
):
    prompt_full = AIO_USDU_PROMPT_FULL
    prompt_no_general = AIO_USDU_PROMPT_NO_GENERAL
    prompt_mode = str(usdu_settings.get("prompt_mode") or prompt_full)
    if prompt_mode == "quality_tags_only":
        prompt_mode = prompt_no_general
    if prompt_mode != prompt_no_general:
        return positive, negative
    prompt, has_fields = _aio_usdu_prompt_without_general(
        prompt_data,
        "positive",
        include_quality=not _as_bool(exclude_positive_quality, False),
    )
    negative_prompt, has_negative_fields = _aio_usdu_prompt_without_general(
        prompt_data,
        "negative",
        include_quality=not _as_bool(exclude_negative_quality, False),
    )
    if not has_fields and not prompt:
        prompt = (
            ""
            if _as_bool(exclude_positive_quality, False)
            else str(quality_tags or "highres, best quality")
        )
    if not has_negative_fields and not negative_prompt:
        negative_prompt = (
            ""
            if _as_bool(exclude_negative_quality, False)
            else str(quality_neg or "")
        )
    prompt, negative_prompt, _derived = _aio_negpip_execution_prompts(
        prompt,
        negative_prompt,
        negpip_mode,
    )
    positive_conditioning = _encode_with_comfy_clip(clip, prompt)
    negative_conditioning = _encode_with_comfy_clip(clip, negative_prompt)
    return positive_conditioning, negative_conditioning


__all__ = ()
