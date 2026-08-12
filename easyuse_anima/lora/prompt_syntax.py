"""A1111 LoRA prompt syntax and shared LoRA stack helpers."""

from __future__ import annotations

import json
import math
import re
from collections.abc import Iterable, Mapping
from typing import Any, TypedDict, TypeVar, cast

from ..common.values import _as_float
from .metadata import _lora_combo_values, _lora_stack_name


class LoraPromptDirective(TypedDict):
    name: str
    strength_model: float
    strength_clip: float


_LoraFieldT = TypeVar("_LoraFieldT", bound=Mapping[str, Any])


_LORA_WEIGHT_PATTERN = r"[+-]?(?:(?:\d+(?:\.\d*)?)|(?:\.\d+))(?:[eE][+-]?\d+)?"
_A1111_LORA_TAG_RE = re.compile(
    rf"(?:<<|<)lora:([^:<>\r\n]+):\s*({_LORA_WEIGHT_PATTERN})"
    rf"(?:\s*:\s*({_LORA_WEIGHT_PATTERN}))?\s*>",
    re.IGNORECASE,
)
_LORA_FILE_EXTENSIONS = (".safetensors", ".ckpt", ".pt")


def _clean_prompt_after_lora_removal(text: str) -> str:
    cleaned = re.sub(r",(?:[ \t]*,)+", ",", text)
    cleaned = re.sub(r"(?m)^[ \t]*,[ \t]*", "", cleaned)
    cleaned = re.sub(r"(?m)[ \t]*,[ \t]*$", "", cleaned)
    cleaned = re.sub(r"[ \t]{2,}", " ", cleaned)
    return cleaned.strip()


def _parse_a1111_lora_tags(text: object) -> tuple[str, list[LoraPromptDirective]]:
    source = str(text or "")
    directives: list[LoraPromptDirective] = []

    def replace(match: re.Match[str]) -> str:
        name = match.group(1).strip()
        try:
            model_strength = float(match.group(2))
            clip_strength = (
                float(match.group(3))
                if match.group(3) is not None
                else model_strength
            )
        except (TypeError, ValueError):
            return match.group(0)
        if (
            not name
            or not math.isfinite(model_strength)
            or not math.isfinite(clip_strength)
        ):
            return match.group(0)
        directives.append(
            {
                "name": name.replace("\\", "/"),
                "strength_model": model_strength,
                "strength_clip": clip_strength,
            }
        )
        return ""

    cleaned = _A1111_LORA_TAG_RE.sub(replace, source)
    if directives:
        cleaned = _clean_prompt_after_lora_removal(cleaned)
    return cleaned, directives


def _extract_a1111_loras_from_fields(
    fields: Iterable[_LoraFieldT],
) -> tuple[list[_LoraFieldT], list[LoraPromptDirective]]:
    extracted: list[LoraPromptDirective] = []
    output: list[_LoraFieldT] = []
    for field in fields:
        item = dict(field)
        if (
            str(item.get("pane") or "positive") == "positive"
            and item.get("enabled") is not False
        ):
            item["text"], directives = _parse_a1111_lora_tags(item.get("text"))
            extracted.extend(directives)
        output.append(cast(_LoraFieldT, item))
    return output, extracted


def _normalize_lora_stack(lora_stack) -> list[tuple[str, float, float]]:
    if isinstance(lora_stack, dict) and "__value__" in lora_stack:
        lora_stack = lora_stack["__value__"]
    if isinstance(lora_stack, str):
        try:
            lora_stack = json.loads(lora_stack or "[]")
        except json.JSONDecodeError:
            lora_stack = []
    if not isinstance(lora_stack, list):
        return []

    entries: list[tuple[str, float, float]] = []
    for item in lora_stack:
        if isinstance(item, dict):
            raw_name = item.get("name", item.get("lora", item.get("lora_name", "")))
            model_strength = item.get(
                "strength_model", item.get("model_strength", item.get("strength", 1.0))
            )
            clip_strength = item.get(
                "strength_clip",
                item.get("clip_strength", item.get("strengthTwo", model_strength)),
            )
        elif isinstance(item, (list, tuple)) and len(item) >= 3:
            raw_name, model_strength, clip_strength = item[:3]
        else:
            continue
        name = str(raw_name or "").strip()
        if not name or name.lower() == "none":
            continue
        entries.append(
            (
                _lora_stack_name(name),
                _as_float(model_strength, 1.0),
                _as_float(clip_strength, _as_float(model_strength, 1.0)),
            )
        )
    return entries


def _lora_stack_signature(lora_stack) -> list[dict[str, Any]]:
    return [
        {
            "name": name,
            "strength_model": model_strength,
            "strength_clip": clip_strength,
        }
        for name, model_strength, clip_strength in _normalize_lora_stack(lora_stack)
    ]


def _normalized_lora_name(value: object) -> str:
    return str(value or "").strip().replace("\\", "/").strip("/")


def _without_lora_extension(value: str) -> str:
    lowered = value.casefold()
    for extension in _LORA_FILE_EXTENSIONS:
        if lowered.endswith(extension):
            return value[: -len(extension)]
    return value


def _resolve_a1111_lora_name(
    requested_name: object,
    available_names: Iterable[object] | None = None,
) -> str:
    requested = _normalized_lora_name(requested_name)
    if not requested:
        raise RuntimeError("[EasyUse Anima] A1111 LoRA tag contains an empty filename.")

    if available_names is None:
        available_names = _lora_combo_values()[1:]
    available = [
        str(name)
        for name in available_names
        if _normalized_lora_name(name).casefold() != "none"
    ]
    requested_key = requested.casefold()
    requested_stem_key = _without_lora_extension(requested).casefold()

    exact = [
        name
        for name in available
        if _normalized_lora_name(name).casefold() == requested_key
        or _without_lora_extension(_normalized_lora_name(name)).casefold()
        == requested_stem_key
    ]
    if len(exact) == 1:
        return exact[0]
    if len(exact) > 1:
        choices = ", ".join(sorted(exact, key=str.casefold))
        raise RuntimeError(
            f"[EasyUse Anima] A1111 LoRA name '{requested}' is ambiguous: {choices}"
        )

    requested_basename = _without_lora_extension(requested).rsplit("/", 1)[-1].casefold()
    basename_matches = [
        name
        for name in available
        if _without_lora_extension(_normalized_lora_name(name))
        .rsplit("/", 1)[-1]
        .casefold()
        == requested_basename
    ]
    if len(basename_matches) == 1:
        return basename_matches[0]
    if len(basename_matches) > 1:
        choices = ", ".join(sorted(basename_matches, key=str.casefold))
        raise RuntimeError(
            f"[EasyUse Anima] A1111 LoRA filename '{requested}' is ambiguous: {choices}. "
            "Use its relative LoRA path in the prompt tag."
        )
    raise RuntimeError(
        f"[EasyUse Anima] A1111 LoRA '{requested}' was not found under ComfyUI/models/loras."
    )


def _resolve_a1111_lora_directives(
    directives: Iterable[Mapping[str, Any]],
    available_names: Iterable[object] | None = None,
) -> list[tuple[str, float, float]]:
    inventory = None if available_names is None else list(available_names)
    resolved: list[tuple[str, float, float]] = []
    for directive in directives:
        name = _resolve_a1111_lora_name(directive.get("name"), inventory)
        model_strength = _as_float(directive.get("strength_model"), 1.0)
        clip_strength = _as_float(directive.get("strength_clip"), model_strength)
        if not math.isfinite(model_strength) or not math.isfinite(clip_strength):
            raise RuntimeError(
                f"[EasyUse Anima] A1111 LoRA '{name}' has a non-finite strength."
            )
        resolved.append((name, model_strength, clip_strength))
    return resolved


def _lora_directives_from_prompt_data(
    prompt_data: Mapping[str, Any] | None,
) -> list[LoraPromptDirective]:
    if not isinstance(prompt_data, Mapping):
        return []
    lora_data = prompt_data.get("lora")
    if not isinstance(lora_data, Mapping) or lora_data.get("syntax") != "a1111":
        return []
    raw_directives = lora_data.get("directives")
    if not isinstance(raw_directives, list):
        return []

    directives: list[LoraPromptDirective] = []
    for raw in raw_directives:
        if not isinstance(raw, Mapping):
            raise RuntimeError("[EasyUse Anima] Prompt Data contains an invalid LoRA directive.")
        name = str(raw.get("name") or "").strip()
        model_strength = _as_float(raw.get("strength_model"), 1.0)
        clip_strength = _as_float(raw.get("strength_clip"), model_strength)
        if not name or not math.isfinite(model_strength) or not math.isfinite(clip_strength):
            raise RuntimeError("[EasyUse Anima] Prompt Data contains an invalid LoRA directive.")
        directives.append(
            {
                "name": name,
                "strength_model": model_strength,
                "strength_clip": clip_strength,
            }
        )
    return directives


def _lora_stack_from_prompt_data(
    prompt_data: Mapping[str, Any] | None,
    available_names: Iterable[object] | None = None,
) -> list[tuple[str, float, float]]:
    return _resolve_a1111_lora_directives(
        _lora_directives_from_prompt_data(prompt_data),
        available_names,
    )


def _merge_prompt_data_lora_stack(
    lora_stack,
    prompt_data: Mapping[str, Any] | None,
    available_names: Iterable[object] | None = None,
) -> list[tuple[str, float, float]]:
    return _merge_lora_stack(
        lora_stack,
        _lora_stack_from_prompt_data(prompt_data, available_names),
    )


def _merge_lora_stack(lora_stack, additions) -> list[tuple[str, float, float]]:
    return [
        *_normalize_lora_stack(lora_stack),
        *_normalize_lora_stack(additions),
    ]


__all__ = ()
