"""Hash and versioned AIR lookup with compact successful-result caching."""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from functools import lru_cache

from .native_civitai import (
    _CIVITAI_API_ROOT,
    _CONTROL_RE,
    _LOOKUP_HASH_RE,
    _MAX_REMOTE_FILES,
    _positive_int,
    _remote_text,
    _request_civitai_json,
)

_VERSIONED_CIVITAI_AIR_RE = re.compile(
    r"urn:air:[a-z0-9][a-z0-9._-]{0,63}:[a-z0-9][a-z0-9._-]{0,63}:"
    r"civitai:(?P<model_id>[1-9][0-9]{0,19})@(?P<version_id>[1-9][0-9]{0,19})"
)
_MAX_LOOKUP_TRIGGER_TEXT = 4096


@dataclass(frozen=True, slots=True)
class CivitaiLookupFields:
    """Bounded strings from one verified file; never retain the API response."""

    autov3_hash: str
    sha256: str
    air: str
    model_name: str
    version_name: str
    trigger_words: str
    resource_hash: str


def _lookup_civitai_file(
    data: Mapping[str, object], normalized_hash: str,
) -> Mapping[str, object]:
    files = data.get("files")
    if isinstance(files, list):
        for item in files[:_MAX_REMOTE_FILES]:
            if not isinstance(item, Mapping):
                continue
            if not normalized_hash:
                if item.get("primary") is True:
                    return item
                continue
            hashes = item.get("hashes")
            if isinstance(hashes, Mapping) and any(
                _remote_text(value, max_length=128).casefold() == normalized_hash
                for value in hashes.values()
            ):
                return item
    if normalized_hash:
        raise RuntimeError("Civitai response did not contain the exact requested file hash.")
    raise RuntimeError("Civitai response did not contain a primary model file.")


def _lookup_trigger_words(value: object) -> str:
    if not isinstance(value, list):
        return ""
    words: list[str] = []
    length = 0
    for item in value[:128]:
        word = _remote_text(item)
        if not word:
            continue
        length += len(word) + (2 if words else 0)
        if length > _MAX_LOOKUP_TRIGGER_TEXT:
            break
        words.append(word)
    return ", ".join(words)


@lru_cache(maxsize=128)
def _cached_civitai_lookup(identifier: str) -> CivitaiLookupFields:
    """Cache successful compact selections independently of optional AiO enrichment."""

    requested_air = _VERSIONED_CIVITAI_AIR_RE.fullmatch(identifier)
    endpoint = (
        f"model-versions/{requested_air['version_id']}"
        if requested_air
        else f"model-versions/by-hash/{identifier}"
    )
    data = _request_civitai_json(f"{_CIVITAI_API_ROOT}/{endpoint}")
    identity = (_positive_int(data.get("modelId")), _positive_int(data.get("id")))
    if None in identity:
        raise RuntimeError("Civitai returned an invalid model/version identity.")
    if requested_air and identity != (
        int(requested_air["model_id"]), int(requested_air["version_id"]),
    ):
        raise RuntimeError("Civitai response model/version IDs did not match the requested AIR.")

    air = _remote_text(data.get("air"))
    if data.get("air") not in (None, ""):
        response_air = _VERSIONED_CIVITAI_AIR_RE.fullmatch(air.casefold())
        if response_air is None or identity != (
            int(response_air["model_id"]), int(response_air["version_id"]),
        ):
            raise RuntimeError("Civitai response AIR did not match its model/version IDs.")
    elif requested_air:
        air = identifier

    selected = _lookup_civitai_file(data, "" if requested_air else identifier)
    hashes = selected.get("hashes")
    if not isinstance(hashes, Mapping):
        raise RuntimeError("Civitai selected file did not contain hashes.")
    autov3 = _remote_text(hashes.get("AutoV3"), max_length=128)
    if not _LOOKUP_HASH_RE.fullmatch(autov3.casefold()):
        autov3 = ""
    sha256 = _remote_text(hashes.get("SHA256"), max_length=64)
    if not re.fullmatch(r"[0-9a-f]{64}", sha256.casefold()):
        sha256 = ""
    resource_hash = autov3 or sha256 or ("" if requested_air else identifier)
    if not resource_hash:
        raise RuntimeError("Civitai selected file did not contain an AutoV3 or SHA256 hash.")
    model = data.get("model")
    return CivitaiLookupFields(
        autov3_hash=autov3,
        sha256=sha256,
        air=air,
        model_name=_remote_text(model.get("name")) if isinstance(model, Mapping) else "",
        version_name=_remote_text(data.get("name")),
        trigger_words=_lookup_trigger_words(data.get("trainedWords")),
        resource_hash=resource_hash,
    )


def lookup_civitai_identifier(identifier: str) -> CivitaiLookupFields:
    """Resolve a hex hash or full versioned Civitai AIR using fixed API endpoints."""

    if not isinstance(identifier, str) or len(identifier) > 512 or _CONTROL_RE.search(identifier):
        raise ValueError("Civitai identifier must be a hex hash or a versioned Civitai AIR.")
    normalized = identifier.strip().casefold()
    if not (
        _LOOKUP_HASH_RE.fullmatch(normalized)
        or _VERSIONED_CIVITAI_AIR_RE.fullmatch(normalized)
    ):
        raise ValueError(
            "Civitai identifier must be an 8-128 character hex hash or "
            "urn:air:ecosystem:type:civitai:modelId@versionId."
        )
    return _cached_civitai_lookup(normalized)
