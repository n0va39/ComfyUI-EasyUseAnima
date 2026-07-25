"""Pure normalization helpers for AiO output settings."""

from __future__ import annotations

import json
from typing import Any

from ..common.values import _as_bool


def _normalize_aio_hash_bundles(value) -> list[str]:
    if isinstance(value, str):
        try:
            value = json.loads(value or "[]")
        except json.JSONDecodeError:
            value = [value]
    if not isinstance(value, list):
        return []
    bundles: list[str] = []
    for item in value:
        text = str(item or "").strip(" ,\n\r\t")
        if text:
            bundles.append(text)
    return bundles


def _normalize_aio_civitai_hash_fetchers(value) -> list[dict[str, Any]]:
    if isinstance(value, str):
        try:
            value = json.loads(value or "[]")
        except json.JSONDecodeError:
            value = []
    if not isinstance(value, list):
        return []
    fetchers: list[dict[str, Any]] = []
    for item in value:
        if not isinstance(item, dict):
            continue
        username = str(item.get("username") or "").strip()
        model_name = str(item.get("model_name") or "").strip()
        version = str(item.get("version") or "").strip()
        if not any((username, model_name, version)):
            continue
        fetchers.append({
            "enabled": _as_bool(item.get("enabled"), True),
            "username": username,
            "model_name": model_name,
            "version": version,
        })
    return fetchers


__all__ = ()
