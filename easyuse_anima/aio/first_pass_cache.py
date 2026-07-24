"""Current AiO first-pass cache state and helpers."""

from __future__ import annotations

import time
from dataclasses import dataclass, replace
from typing import Any

from ..common.serialization import _stable_change_key
from ..prompt.data import _prompt_data_json_safe
from .model_preparation import _aio_lora_stack_signature

AIO_FIRST_PASS_CACHE_MAX_ENTRIES = 2
AIO_FIRST_PASS_CACHE_MAX_BYTES = 512 * 1024 * 1024
AIO_FIRST_PASS_CACHE_MAX_ENTRY_BYTES = 256 * 1024 * 1024
AIO_FIRST_PASS_CACHE_TTL_SECONDS = 300.0
_AIO_FIRST_PASS_CACHE_ENABLED = True


@dataclass(frozen=True, slots=True)
class _AIOFirstPassCacheEntry:
    latent: Any
    image: Any
    size_bytes: int
    created_at: float
    last_access_at: float

    @classmethod
    def capture(
        cls,
        latent,
        image,
        *,
        now: float,
    ) -> _AIOFirstPassCacheEntry:
        latent_snapshot = _clone_aio_cache_value(latent)
        image_snapshot = _clone_aio_cache_value(image)
        return cls(
            latent=latent_snapshot,
            image=image_snapshot,
            size_bytes=_aio_cache_pair_size_bytes(
                latent_snapshot,
                image_snapshot,
            ),
            created_at=now,
            last_access_at=now,
        )

    def checkout(self):
        return (
            _clone_aio_cache_value(self.latent),
            _clone_aio_cache_value(self.image),
        )


_AIO_FIRST_PASS_CACHE: dict[
    str,
    _AIOFirstPassCacheEntry | dict[str, Any],
] = {}
_AIO_FIRST_PASS_CACHE_ORDER: list[str] = []


def _clone_aio_cache_value(value):
    if isinstance(value, dict):
        return {
            key: _clone_aio_cache_value(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [_clone_aio_cache_value(item) for item in value]
    if isinstance(value, tuple):
        return tuple(_clone_aio_cache_value(item) for item in value)
    detach = getattr(value, "detach", None)
    clone = getattr(value, "clone", None)
    if callable(detach) and callable(clone):
        tensor: Any = detach()
        tensor = tensor.clone()
        cpu = getattr(tensor, "cpu", None)
        if callable(cpu):
            try:
                tensor = cpu()
            except Exception:
                pass
        return tensor
    return value


def _aio_cache_value_size_bytes(
    value,
    *,
    _seen: set[int] | None = None,
) -> int:
    seen = set() if _seen is None else _seen
    identity = id(value)
    if identity in seen:
        return 0
    seen.add(identity)

    if isinstance(value, dict):
        return sum(
            _aio_cache_value_size_bytes(item, _seen=seen)
            for item in value.values()
        )
    if isinstance(value, (list, tuple)):
        return sum(
            _aio_cache_value_size_bytes(item, _seen=seen)
            for item in value
        )
    if isinstance(value, (bytes, bytearray)):
        return len(value)
    if isinstance(value, memoryview):
        return value.nbytes

    try:
        numel = getattr(value, "numel", None)
        element_size = getattr(value, "element_size", None)
    except Exception:
        numel = None
        element_size = None
    if callable(numel) and callable(element_size):
        try:
            count = numel()
            item_bytes = element_size()
            if (
                isinstance(count, int)
                and not isinstance(count, bool)
                and isinstance(item_bytes, int)
                and not isinstance(item_bytes, bool)
                and count >= 0
                and item_bytes >= 0
            ):
                return count * item_bytes
        except Exception:
            pass

    try:
        nbytes = getattr(value, "nbytes", None)
    except Exception:
        nbytes = None
    if callable(nbytes):
        try:
            nbytes = nbytes()
        except Exception:
            nbytes = None
    if isinstance(nbytes, int) and not isinstance(nbytes, bool):
        return max(0, nbytes)
    return 0


def _aio_cache_pair_size_bytes(latent, image) -> int:
    seen: set[int] = set()
    return (
        _aio_cache_value_size_bytes(latent, _seen=seen)
        + _aio_cache_value_size_bytes(image, _seen=seen)
    )


def _aio_first_pass_cache_entry_size_bytes(entry) -> int:
    if isinstance(entry, _AIOFirstPassCacheEntry):
        return entry.size_bytes
    if isinstance(entry, dict):
        return _aio_cache_pair_size_bytes(
            entry.get("latent"),
            entry.get("image"),
        )
    return 0


def _aio_first_pass_cache_total_bytes() -> int:
    return sum(
        _aio_first_pass_cache_entry_size_bytes(entry)
        for entry in _AIO_FIRST_PASS_CACHE.values()
    )


def _clear_aio_first_pass_cache() -> None:
    _AIO_FIRST_PASS_CACHE.clear()
    _AIO_FIRST_PASS_CACHE_ORDER.clear()


def _set_aio_first_pass_cache_enabled(enabled: bool) -> None:
    global _AIO_FIRST_PASS_CACHE_ENABLED

    _AIO_FIRST_PASS_CACHE_ENABLED = bool(enabled)
    if not _AIO_FIRST_PASS_CACHE_ENABLED:
        _clear_aio_first_pass_cache()


def _aio_first_pass_cache_now() -> float:
    return time.monotonic()


def _aio_first_pass_cache_key(
    *,
    cache_scope: str,
    context: dict[str, Any],
    prompt_data: dict[str, Any],
    lora_stack,
    settings: dict[str, Any],
    positive_prompt: str,
    negative_prompt: str,
    quality_tags: str,
    quality_neg: str,
    use_anima_mod_guidance: bool,
    use_negative_anima_mod_guidance: bool,
    width: int,
    height: int,
) -> str:
    return _stable_change_key({
        "schema": "easyuse_anima_aio_first_pass_cache",
        "version": 1,
        "scope": str(cache_scope or ""),
        "mode": settings.get("mode"),
        "resource_info": _prompt_data_json_safe(
            context.get("resource_info", {})
        ),
        "input_settings": _prompt_data_json_safe(
            context.get("input_settings", {})
        ),
        "prompt_data": _prompt_data_json_safe(prompt_data),
        "lora_stack": _aio_lora_stack_signature(lora_stack),
        "sampler": _prompt_data_json_safe(
            settings.get("sampler", {})
        ),
        "model_patches": _prompt_data_json_safe(
            settings.get("model_patches", {})
        ),
        "mod_guidance": _prompt_data_json_safe(
            settings.get("mod_guidance", {})
        ),
        "artist_mix": _prompt_data_json_safe(
            settings.get("artist_mix", {})
        ),
        "positive_prompt": str(positive_prompt or ""),
        "negative_prompt": str(negative_prompt or ""),
        "quality_tags": str(quality_tags or ""),
        "quality_neg": str(quality_neg or ""),
        "use_anima_mod_guidance": bool(use_anima_mod_guidance),
        "use_negative_anima_mod_guidance": bool(use_negative_anima_mod_guidance),
        "width": int(width),
        "height": int(height),
    })


def _get_aio_first_pass_cache(cache_key: str):
    if not _AIO_FIRST_PASS_CACHE_ENABLED:
        return None
    entry = _AIO_FIRST_PASS_CACHE.get(cache_key)
    if not entry:
        return None
    if isinstance(entry, _AIOFirstPassCacheEntry):
        now = _aio_first_pass_cache_now()
        if now - entry.created_at >= AIO_FIRST_PASS_CACHE_TTL_SECONDS:
            _AIO_FIRST_PASS_CACHE.pop(cache_key, None)
            if cache_key in _AIO_FIRST_PASS_CACHE_ORDER:
                _AIO_FIRST_PASS_CACHE_ORDER.remove(cache_key)
            return None
        entry = replace(entry, last_access_at=now)
        _AIO_FIRST_PASS_CACHE[cache_key] = entry
    if cache_key in _AIO_FIRST_PASS_CACHE_ORDER:
        _AIO_FIRST_PASS_CACHE_ORDER.remove(cache_key)
    _AIO_FIRST_PASS_CACHE_ORDER.append(cache_key)
    if isinstance(entry, _AIOFirstPassCacheEntry):
        return entry.checkout()
    return (
        _clone_aio_cache_value(entry["latent"]),
        _clone_aio_cache_value(entry["image"]),
    )


def _put_aio_first_pass_cache(cache_key: str, latent, image) -> None:
    if not _AIO_FIRST_PASS_CACHE_ENABLED:
        return
    if (
        _aio_cache_pair_size_bytes(latent, image)
        > AIO_FIRST_PASS_CACHE_MAX_ENTRY_BYTES
    ):
        return
    entry = _AIOFirstPassCacheEntry.capture(
        latent,
        image,
        now=_aio_first_pass_cache_now(),
    )
    if entry.size_bytes > AIO_FIRST_PASS_CACHE_MAX_ENTRY_BYTES:
        return
    _AIO_FIRST_PASS_CACHE[cache_key] = entry
    if cache_key in _AIO_FIRST_PASS_CACHE_ORDER:
        _AIO_FIRST_PASS_CACHE_ORDER.remove(cache_key)
    _AIO_FIRST_PASS_CACHE_ORDER.append(cache_key)
    while _AIO_FIRST_PASS_CACHE_ORDER and (
        len(_AIO_FIRST_PASS_CACHE_ORDER) > AIO_FIRST_PASS_CACHE_MAX_ENTRIES
        or _aio_first_pass_cache_total_bytes() > AIO_FIRST_PASS_CACHE_MAX_BYTES
    ):
        old_key = _AIO_FIRST_PASS_CACHE_ORDER.pop(0)
        _AIO_FIRST_PASS_CACHE.pop(old_key, None)


__all__ = ()
