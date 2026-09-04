"""Pure normalization helpers for AiO output settings."""

from __future__ import annotations

import json
import unicodedata
from typing import Any

from ..common.values import _as_bool

_MAX_SAVED_HASH_ROWS = 32
_MAX_SAVED_HASH_CANDIDATES = 64
_MAX_SAVED_HASH_JSON_BYTES = 512 * 1024
_MAX_HASH_BUNDLE_BYTES = 8 * 1024
_MAX_CIVITAI_FIELD_CHARACTERS = 200
_MAX_CIVITAI_FIELD_BYTES = 800
_UNSAFE_TEXT_CATEGORIES = frozenset({"Cc", "Cf", "Cs", "Zl", "Zp"})


def _fits_utf8_limit(value: str, *, max_characters: int, max_bytes: int) -> bool:
    if len(value) > max_characters:
        return False
    try:
        return len(value.encode("utf-8")) <= max_bytes
    except UnicodeEncodeError:
        return False


def _load_saved_list(value, *, fallback_plain_text: bool) -> list[Any] | None:
    if isinstance(value, str):
        if not _fits_utf8_limit(
            value,
            max_characters=_MAX_SAVED_HASH_JSON_BYTES,
            max_bytes=_MAX_SAVED_HASH_JSON_BYTES,
        ):
            return None
        try:
            value = json.loads(value or "[]")
        except json.JSONDecodeError:
            value = [value] if fallback_plain_text else None
        except (RecursionError, ValueError):
            value = None
    return value if isinstance(value, list) else None


def _bounded_scalar_text(
    value,
    *,
    max_characters: int,
    max_bytes: int,
    strip_characters: str | None = None,
    reject_controls: bool = False,
) -> str | None:
    if value is None:
        return ""
    if not isinstance(value, str):
        return None
    text = value
    if not _fits_utf8_limit(
        text,
        max_characters=max_characters,
        max_bytes=max_bytes,
    ):
        return None
    text = text.strip(strip_characters) if strip_characters is not None else text.strip()
    if reject_controls and any(
        unicodedata.category(character) in _UNSAFE_TEXT_CATEGORIES
        for character in text
    ):
        return None
    if not _fits_utf8_limit(
        text,
        max_characters=max_characters,
        max_bytes=max_bytes,
    ):
        return None
    return text


def _normalize_aio_hash_text(value) -> str:
    return (
        _bounded_scalar_text(
            value,
            max_characters=_MAX_HASH_BUNDLE_BYTES,
            max_bytes=_MAX_HASH_BUNDLE_BYTES,
            strip_characters=" ,\n\r\t",
        )
        or ""
    )


def _normalize_aio_hash_bundles(value) -> list[str]:
    values = _load_saved_list(value, fallback_plain_text=True)
    if values is None:
        return []
    bundles: list[str] = []
    for item in values[:_MAX_SAVED_HASH_CANDIDATES]:
        text = _normalize_aio_hash_text(item)
        if text:
            bundles.append(text)
            if len(bundles) >= _MAX_SAVED_HASH_ROWS:
                break
    return bundles


def _normalize_aio_civitai_hash_fetchers(value) -> list[dict[str, Any]]:
    values = _load_saved_list(value, fallback_plain_text=False)
    if values is None:
        return []
    fetchers: list[dict[str, Any]] = []
    for item in values[:_MAX_SAVED_HASH_CANDIDATES]:
        if not isinstance(item, dict):
            continue
        fields = tuple(
            _bounded_scalar_text(
                item.get(field),
                max_characters=_MAX_CIVITAI_FIELD_CHARACTERS,
                max_bytes=_MAX_CIVITAI_FIELD_BYTES,
                reject_controls=True,
            )
            for field in ("username", "model_name", "version")
        )
        if any(field is None for field in fields):
            continue
        username, model_name, version = fields
        if not any((username, model_name, version)):
            continue
        fetchers.append({
            "enabled": _as_bool(item.get("enabled"), True),
            "username": username,
            "model_name": model_name,
            "version": version,
        })
        if len(fetchers) >= _MAX_SAVED_HASH_ROWS:
            break
    return fetchers


__all__ = ()
