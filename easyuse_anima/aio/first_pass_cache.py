"""Current AiO first-pass cache state and helpers."""

from __future__ import annotations

from typing import Any

from ..common.serialization import _stable_change_key
from ..prompt.data import _prompt_data_json_safe
from .model_preparation import _aio_lora_stack_signature

AIO_FIRST_PASS_CACHE_MAX_ENTRIES = 2
_AIO_FIRST_PASS_CACHE: dict[str, dict[str, Any]] = {}
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


def _clear_aio_first_pass_cache() -> None:
    _AIO_FIRST_PASS_CACHE.clear()
    _AIO_FIRST_PASS_CACHE_ORDER.clear()


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
    entry = _AIO_FIRST_PASS_CACHE.get(cache_key)
    if not entry:
        return None
    if cache_key in _AIO_FIRST_PASS_CACHE_ORDER:
        _AIO_FIRST_PASS_CACHE_ORDER.remove(cache_key)
    _AIO_FIRST_PASS_CACHE_ORDER.append(cache_key)
    return (
        _clone_aio_cache_value(entry["latent"]),
        _clone_aio_cache_value(entry["image"]),
    )


def _put_aio_first_pass_cache(cache_key: str, latent, image) -> None:
    entry = {
        "latent": _clone_aio_cache_value(latent),
        "image": _clone_aio_cache_value(image),
    }
    _AIO_FIRST_PASS_CACHE[cache_key] = entry
    if cache_key in _AIO_FIRST_PASS_CACHE_ORDER:
        _AIO_FIRST_PASS_CACHE_ORDER.remove(cache_key)
    _AIO_FIRST_PASS_CACHE_ORDER.append(cache_key)
    while len(_AIO_FIRST_PASS_CACHE_ORDER) > AIO_FIRST_PASS_CACHE_MAX_ENTRIES:
        old_key = _AIO_FIRST_PASS_CACHE_ORDER.pop(0)
        _AIO_FIRST_PASS_CACHE.pop(old_key, None)


__all__ = ()
