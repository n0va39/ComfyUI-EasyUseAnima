"""Bounded, fixed-host Civitai metadata lookups for native image output."""

from __future__ import annotations

import json
import logging
import re
import threading
import time
from collections.abc import Callable, Mapping
from contextvars import ContextVar
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Any, cast

logger = logging.getLogger("ComfyUI-EasyUseAnima")

_CIVITAI_API_ROOT = "https://civitai.com/api/v1"
_CIVITAI_RESPONSE_LIMIT = 2 * 1024 * 1024
_CIVITAI_ENRICHMENT_TIMEOUT_SECONDS = 12.0
_CIVITAI_HTTP_CALL_LIMIT = 16
_MAX_REMOTE_FILES = 256
_CONTROL_RE = re.compile(r"[\x00-\x1f\x7f]")
_SAFE_HASH_RE = re.compile(r"^[A-Za-z0-9_-]{1,128}$")
_LOOKUP_HASH_RE = re.compile(r"^[0-9a-f]{8,128}$")
_SAFE_AIR_RE = re.compile(r"^urn:air:[A-Za-z0-9][A-Za-z0-9._~:@%+\-]{0,503}$")
_CIVITAI_REQUEST_SLOT = threading.BoundedSemaphore(1)


class CivitaiLookupBudgetExhausted(RuntimeError):
    """The optional network-enrichment budget for one save was exhausted."""


@dataclass(slots=True)
class CivitaiLookupBudget:
    """Shared deadline and HTTP-call allowance for one image-save operation."""

    timeout_seconds: float = _CIVITAI_ENRICHMENT_TIMEOUT_SECONDS
    http_call_limit: int = _CIVITAI_HTTP_CALL_LIMIT
    clock: Callable[[], float] = time.monotonic
    _deadline: float | None = field(default=None, init=False, repr=False)
    _calls_started: int = field(default=0, init=False, repr=False)
    _lock: Any = field(default_factory=threading.Lock, init=False, repr=False)

    @property
    def calls_started(self) -> int:
        with self._lock:
            return self._calls_started

    def reserve_http_call(self) -> float:
        """Consume one call and return its remaining wall-clock allowance."""

        with self._lock:
            now = float(self.clock())
            if self._deadline is None:
                self._deadline = now + max(0.0, float(self.timeout_seconds))
            if now >= self._deadline:
                raise CivitaiLookupBudgetExhausted(
                    "Civitai enrichment deadline was exhausted"
                )
            if self._calls_started >= max(0, int(self.http_call_limit)):
                raise CivitaiLookupBudgetExhausted(
                    "Civitai enrichment HTTP-call budget was exhausted"
                )
            self._calls_started += 1
            return self._deadline - now

    def require_time_remaining(self) -> float:
        with self._lock:
            if self._deadline is None:
                return max(0.0, float(self.timeout_seconds))
            remaining = self._deadline - float(self.clock())
        if remaining <= 0:
            raise CivitaiLookupBudgetExhausted(
                "Civitai enrichment deadline was exhausted"
            )
        return remaining


_ACTIVE_CIVITAI_BUDGET: ContextVar[CivitaiLookupBudget | None] = ContextVar(
    "easyuse_anima_civitai_budget",
    default=None,
)


@dataclass(frozen=True, slots=True)
class CivitaiResourceDescriptor:
    """Small validated subset retained from a model-version response."""

    model_name: str
    version_name: str
    air: str
    model_version_id: int | None


@dataclass(frozen=True, slots=True)
class _CivitaiModelLookup:
    """Preserve first-request spelling while comparing normalized cache keys."""

    username_key: str
    model_name_key: str
    version_key: str
    username: str = field(compare=False)
    model_name: str = field(compare=False)
    version: str = field(compare=False)


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


def _response_proves_hash(data: Mapping[str, object], normalized_hash: str) -> bool:
    """Require an exact file-hash match before trusting a by-hash response."""

    files = data.get("files")
    if not isinstance(files, list):
        return False
    for item in files[:_MAX_REMOTE_FILES]:
        if not isinstance(item, Mapping):
            continue
        hashes = item.get("hashes")
        if not isinstance(hashes, Mapping):
            continue
        for value in hashes.values():
            candidate = _remote_text(value, max_length=128).casefold()
            if candidate == normalized_hash:
                return True
    return False


def _default_civitai_transport(
    endpoint: str,
    *,
    params: Mapping[str, str | int] | None,
    timeout: tuple[float, float],
) -> Any:
    import requests

    return requests.get(
        endpoint,
        params=dict(params or {}),
        headers={
            "Accept": "application/json",
            "User-Agent": "ComfyUI-EasyUseAnima/native-image-output",
        },
        timeout=timeout,
        allow_redirects=False,
        stream=True,
    )


def _read_civitai_response(
    response: Any,
    *,
    budget: CivitaiLookupBudget,
) -> dict[str, Any]:
    try:
        budget.require_time_remaining()
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
            budget.require_time_remaining()
            if not chunk:
                continue
            if len(chunk) > _CIVITAI_RESPONSE_LIMIT - len(payload):
                raise RuntimeError(
                    "Civitai response exceeded the metadata size limit"
                )
            payload.extend(chunk)
        budget.require_time_remaining()
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


def _request_civitai_json(
    endpoint: str,
    *,
    params: Mapping[str, str | int] | None = None,
    budget: CivitaiLookupBudget | None = None,
    transport: Callable[..., Any] | None = None,
) -> dict[str, Any]:
    if not endpoint.startswith(f"{_CIVITAI_API_ROOT}/"):
        raise RuntimeError("[EasyUseAnima] Refusing a non-Civitai metadata endpoint.")

    active_budget = budget or _ACTIVE_CIVITAI_BUDGET.get() or CivitaiLookupBudget()
    remaining = active_budget.reserve_http_call()
    if not _CIVITAI_REQUEST_SLOT.acquire(blocking=False):
        raise CivitaiLookupBudgetExhausted(
            "A previous Civitai request is still draining after its deadline"
        )

    outcome: dict[str, object] = {}
    completed = threading.Event()
    request_transport = transport or _default_civitai_transport
    timeout = (
        max(0.001, min(3.05, remaining)),
        max(0.001, min(10.0, remaining)),
    )

    def worker() -> None:
        try:
            try:
                response = request_transport(
                    endpoint,
                    params=params,
                    timeout=timeout,
                )
            except Exception as exc:
                raise RuntimeError(
                    f"Civitai request failed ({type(exc).__name__})"
                ) from exc
            outcome["value"] = _read_civitai_response(
                response,
                budget=active_budget,
            )
        except Exception as exc:
            outcome["error"] = exc
        finally:
            _CIVITAI_REQUEST_SLOT.release()
            completed.set()

    thread = threading.Thread(
        target=worker,
        name="EasyUseAnima-Civitai",
        daemon=True,
    )
    try:
        thread.start()
    except Exception as exc:
        _CIVITAI_REQUEST_SLOT.release()
        raise RuntimeError(
            f"Civitai request worker failed ({type(exc).__name__})"
        ) from exc

    if not completed.wait(timeout=remaining):
        raise CivitaiLookupBudgetExhausted(
            "Civitai enrichment deadline was exhausted"
        )
    active_budget.require_time_remaining()
    error = outcome.get("error")
    if isinstance(error, BaseException):
        raise error
    value = outcome.get("value")
    if not isinstance(value, dict):
        raise RuntimeError("Civitai returned an invalid metadata object")
    return cast(dict[str, Any], value)


@lru_cache(maxsize=128)
def _cached_civitai_resource_by_hash(
    normalized_hash: str,
) -> CivitaiResourceDescriptor | None:
    data = _request_civitai_json(
        f"{_CIVITAI_API_ROOT}/model-versions/by-hash/{normalized_hash}"
    )
    if not _response_proves_hash(data, normalized_hash):
        return None
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
    resource_hash: str,
    *,
    budget: CivitaiLookupBudget | None = None,
) -> CivitaiResourceDescriptor | None:
    normalized = str(resource_hash or "").strip().casefold()
    if not _LOOKUP_HASH_RE.fullmatch(normalized):
        return None
    token = (
        _ACTIVE_CIVITAI_BUDGET.set(budget)
        if budget is not None
        else None
    )
    try:
        return _cached_civitai_resource_by_hash(normalized)
    except CivitaiLookupBudgetExhausted:
        raise
    except RuntimeError as exc:
        logger.warning(
            "[EasyUseAnima] Civitai resource lookup failed for hash %.10s; "
            "preserving local hash metadata: %s",
            normalized,
            exc,
        )
        return None
    finally:
        if token is not None:
            _ACTIVE_CIVITAI_BUDGET.reset(token)


@lru_cache(maxsize=128)
def _cached_civitai_autov3_hash(
    lookup: _CivitaiModelLookup,
) -> str | None:
    data = _request_civitai_json(
        f"{_CIVITAI_API_ROOT}/models",
        params={
            "username": lookup.username,
            "query": lookup.model_name,
            "limit": 20,
            "nsfw": "true",
        },
    )
    items = data.get("items")
    if not isinstance(items, list):
        return None
    target = lookup.model_name_key
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
                if lookup.version_key
                in _remote_text(item.get("name"), max_length=200).casefold()
            ),
            None,
        )
        if lookup.version_key
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


def _fetch_civitai_autov3_hash(
    username: str,
    model_name: str,
    version: str = "",
    *,
    budget: CivitaiLookupBudget | None = None,
) -> str | None:
    values = tuple(
        str(value or "").strip()
        for value in (username, model_name, version)
    )
    safe_username, safe_model_name, safe_version = values
    if (
        not safe_username
        or not safe_model_name
        or any(len(value) > 200 or _CONTROL_RE.search(value) for value in values)
    ):
        raise RuntimeError(
            "Civitai hash lookup fields must contain 1-200 printable characters."
        )
    normalized = tuple(value.casefold() for value in values)
    if any(len(value) > 200 for value in normalized):
        raise RuntimeError(
            "Civitai hash lookup fields must contain 1-200 printable characters."
        )
    lookup = _CivitaiModelLookup(
        username_key=normalized[0],
        model_name_key=normalized[1],
        version_key=normalized[2],
        username=safe_username,
        model_name=safe_model_name,
        version=safe_version,
    )

    token = (
        _ACTIVE_CIVITAI_BUDGET.set(budget)
        if budget is not None
        else None
    )
    try:
        return _cached_civitai_autov3_hash(lookup)
    finally:
        if token is not None:
            _ACTIVE_CIVITAI_BUDGET.reset(token)


setattr(
    _fetch_civitai_autov3_hash,
    "cache_clear",
    _cached_civitai_autov3_hash.cache_clear,
)


__all__ = ()
