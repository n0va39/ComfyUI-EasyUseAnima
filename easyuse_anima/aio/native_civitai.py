"""Bounded, fixed-host Civitai metadata lookups for native image output."""

from __future__ import annotations

import json
import logging
import re
from collections.abc import Mapping
from dataclasses import dataclass
from functools import lru_cache
from typing import Any, cast

logger = logging.getLogger("ComfyUI-EasyUseAnima")

_CIVITAI_API_ROOT = "https://civitai.com/api/v1"
_CIVITAI_RESPONSE_LIMIT = 2 * 1024 * 1024
_CONTROL_RE = re.compile(r"[\x00-\x1f\x7f]")
_SAFE_HASH_RE = re.compile(r"^[A-Za-z0-9_-]{1,128}$")
_SAFE_AIR_RE = re.compile(r"^urn:air:[A-Za-z0-9][A-Za-z0-9._~:@%+\-]{0,503}$")


@dataclass(frozen=True, slots=True)
class CivitaiResourceDescriptor:
    """Small validated subset retained from a model-version response."""

    model_name: str
    version_name: str
    air: str
    model_version_id: int | None


def _remote_text(value: object, *, max_length: int = 512) -> str:
    if not isinstance(value, str):
        return ""
    text = value.strip()
    if not text or len(text) > max_length or _CONTROL_RE.search(text):
        return ""
    return text


def _positive_int(value: object) -> int | None:
    if isinstance(value, bool):
        return None
    text = str(value or "").strip()
    if not re.fullmatch(r"[0-9]{1,20}", text):
        return None
    result = int(text)
    return result if result > 0 else None


def _request_civitai_json(
    endpoint: str,
    *,
    params: Mapping[str, str | int] | None = None,
) -> dict[str, Any]:
    if not endpoint.startswith(f"{_CIVITAI_API_ROOT}/"):
        raise RuntimeError("[EasyUseAnima] Refusing a non-Civitai metadata endpoint.")

    try:
        import requests

        response = requests.get(
            endpoint,
            params=dict(params or {}),
            headers={
                "Accept": "application/json",
                "User-Agent": "ComfyUI-EasyUseAnima/native-image-output",
            },
            timeout=(3.05, 10),
            allow_redirects=False,
            stream=True,
        )
    except Exception as exc:
        raise RuntimeError(
            f"Civitai request failed ({type(exc).__name__})"
        ) from exc

    try:
        if response.status_code != 200:
            raise RuntimeError(f"Civitai returned HTTP {response.status_code}")
        length_header = response.headers.get("Content-Length")
        if length_header:
            try:
                if int(length_header) > _CIVITAI_RESPONSE_LIMIT:
                    raise RuntimeError(
                        "Civitai response exceeded the metadata size limit"
                    )
            except ValueError:
                pass

        payload = bytearray()
        for chunk in response.iter_content(chunk_size=64 * 1024):
            if not chunk:
                continue
            if len(chunk) > _CIVITAI_RESPONSE_LIMIT - len(payload):
                raise RuntimeError(
                    "Civitai response exceeded the metadata size limit"
                )
            payload.extend(chunk)
        value = json.loads(payload.decode("utf-8"))
    except RuntimeError:
        raise
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeError("Civitai returned invalid JSON metadata") from exc
    except Exception as exc:
        raise RuntimeError(
            f"Civitai response could not be read ({type(exc).__name__})"
        ) from exc
    finally:
        try:
            response.close()
        except Exception as exc:
            logger.warning(
                "[EasyUseAnima] Civitai response cleanup failed (%s); continuing.",
                type(exc).__name__,
            )

    if not isinstance(value, dict):
        raise RuntimeError("Civitai returned an invalid metadata object")
    return cast(dict[str, Any], value)


@lru_cache(maxsize=128)
def _cached_civitai_resource_by_hash(
    normalized_sha256: str,
) -> CivitaiResourceDescriptor | None:
    data = _request_civitai_json(
        f"{_CIVITAI_API_ROOT}/model-versions/by-hash/{normalized_sha256}"
    )
    air = _remote_text(data.get("air"))
    if air and not _SAFE_AIR_RE.fullmatch(air):
        air = ""
    version_id = _positive_int(data.get("id"))
    if not air and version_id is None:
        return None
    model = data.get("model")
    model_name = (
        _remote_text(cast(Mapping[str, object], model).get("name"))
        if isinstance(model, Mapping)
        else ""
    )
    return CivitaiResourceDescriptor(
        model_name=model_name,
        version_name=_remote_text(data.get("name")),
        air=air,
        model_version_id=version_id,
    )


def _fetch_civitai_resource_by_hash(
    sha256: str,
) -> CivitaiResourceDescriptor | None:
    normalized = str(sha256 or "").strip().casefold()
    if not re.fullmatch(r"[0-9a-f]{64}", normalized):
        return None
    try:
        return _cached_civitai_resource_by_hash(normalized)
    except RuntimeError as exc:
        logger.warning(
            "[EasyUseAnima] Civitai resource lookup failed for hash %.10s; "
            "preserving local hash metadata: %s",
            normalized,
            exc,
        )
        return None


@lru_cache(maxsize=128)
def _fetch_civitai_autov3_hash(
    username: str,
    model_name: str,
    version: str = "",
) -> str | None:
    safe_username = str(username or "").strip()
    safe_model_name = str(model_name or "").strip()
    safe_version = str(version or "").strip()
    values = (safe_username, safe_model_name, safe_version)
    if (
        not safe_username
        or not safe_model_name
        or any(len(value) > 200 or _CONTROL_RE.search(value) for value in values)
    ):
        raise RuntimeError(
            "Civitai hash lookup fields must contain 1-200 printable characters."
        )

    data = _request_civitai_json(
        f"{_CIVITAI_API_ROOT}/models",
        params={
            "username": safe_username,
            "query": safe_model_name,
            "limit": 20,
            "nsfw": "true",
        },
    )
    items = data.get("items")
    if not isinstance(items, list):
        return None
    target = safe_model_name.casefold()
    candidates = [item for item in items if isinstance(item, dict)]
    model = next(
        (
            item
            for item in candidates
            if _remote_text(item.get("name"), max_length=200).casefold() == target
        ),
        None,
    )
    if model is None:
        model = next(
            (
                item
                for item in candidates
                if target in _remote_text(item.get("name"), max_length=200).casefold()
            ),
            None,
        )
    if model is None:
        return None

    versions = model.get("modelVersions")
    if not isinstance(versions, list):
        return None
    version_candidates = [item for item in versions if isinstance(item, dict)]
    chosen = (
        next(
            (
                item
                for item in version_candidates
                if safe_version.casefold()
                in _remote_text(item.get("name"), max_length=200).casefold()
            ),
            None,
        )
        if safe_version
        else (version_candidates[0] if version_candidates else None)
    )
    if chosen is None:
        return None
    version_id = _positive_int(chosen.get("id"))
    if version_id is None:
        return None
    detail = _request_civitai_json(
        f"{_CIVITAI_API_ROOT}/model-versions/{version_id}"
    )
    files = detail.get("files")
    if not isinstance(files, list):
        return None
    for item in files:
        if not isinstance(item, dict) or not isinstance(item.get("hashes"), dict):
            continue
        hashes = cast(dict[str, object], item["hashes"])
        hash_value = str(hashes.get("AutoV3") or "").strip()
        if _SAFE_HASH_RE.fullmatch(hash_value):
            return hash_value
    return None


__all__ = ()
