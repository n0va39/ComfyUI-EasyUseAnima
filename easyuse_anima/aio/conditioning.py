"""AiO conditioning preparation helpers."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, TypeAlias

_RuntimeResolver: TypeAlias = Callable[[str], Any]
_RUNTIME_RESOLVER: _RuntimeResolver | None = None


def _bind_aio_conditioning_runtime(*, resolve_helper: _RuntimeResolver) -> None:
    """Bind root compatibility helpers without importing the root module."""

    global _RUNTIME_RESOLVER
    _RUNTIME_RESOLVER = resolve_helper


def _runtime_helper(name: str) -> Any:
    resolver = _RUNTIME_RESOLVER
    if resolver is None:
        raise RuntimeError(
            f"[EasyUseAnima] AiO conditioning runtime helper is not bound: {name}"
        )
    return resolver(name)


def _aio_prompt_data_fields_for_usdu(prompt_data: str | dict | None) -> list[dict]:
    data = _runtime_helper("_normalize_prompt_data")(prompt_data)
    fields = data.get("fields")
    if not isinstance(fields, list):
        fields = data.get("saved_fields")
    return _runtime_helper("_normalize_advanced_fields")(fields)


def _aio_usdu_prompt_without_general(
    prompt_data: str | dict | None,
    pane: str,
    include_quality: bool,
) -> tuple[str, bool]:
    fields = _runtime_helper("_aio_prompt_data_fields_for_usdu")(prompt_data)
    if not fields:
        return "", False
    allowed_types = {"artist", "trigger"}
    if include_quality:
        allowed_types.add("quality")
    selected = [
        field
        for field in _runtime_helper("_advanced_enabled_pane_fields")(fields, pane)
        if field.get("type") in allowed_types
    ]
    if not selected:
        return "", True
    artist_prompt = _runtime_helper("_advanced_artist_field_prompt")(selected, pane)
    force_pin_triggers = _runtime_helper("_as_bool")(
        _runtime_helper("_normalize_prompt_data")(prompt_data).get(
            "pin_trigger_tags_to_front"
        ),
        False,
    )
    return (
        _runtime_helper("_correct_advanced_field_sequence")(
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
):
    prompt_full = _runtime_helper("AIO_USDU_PROMPT_FULL")
    prompt_no_general = _runtime_helper("AIO_USDU_PROMPT_NO_GENERAL")
    prompt_mode = str(usdu_settings.get("prompt_mode") or prompt_full)
    if prompt_mode == "quality_tags_only":
        prompt_mode = prompt_no_general
    if prompt_mode != prompt_no_general:
        return positive, negative
    prompt, has_fields = _runtime_helper("_aio_usdu_prompt_without_general")(
        prompt_data,
        "positive",
        include_quality=not _runtime_helper("_as_bool")(
            exclude_positive_quality, False
        ),
    )
    negative_prompt, has_negative_fields = _runtime_helper(
        "_aio_usdu_prompt_without_general"
    )(
        prompt_data,
        "negative",
        include_quality=not _runtime_helper("_as_bool")(
            exclude_negative_quality, False
        ),
    )
    if not has_fields and not prompt:
        prompt = (
            ""
            if _runtime_helper("_as_bool")(exclude_positive_quality, False)
            else str(quality_tags or "highres, best quality")
        )
    if not has_negative_fields and not negative_prompt:
        negative_prompt = (
            ""
            if _runtime_helper("_as_bool")(exclude_negative_quality, False)
            else str(quality_neg or "")
        )
    positive_conditioning = _runtime_helper("_encode_with_comfy_clip")(clip, prompt)
    negative_conditioning = _runtime_helper("_encode_with_comfy_clip")(
        clip, negative_prompt
    )
    return positive_conditioning, negative_conditioning


__all__ = ()
