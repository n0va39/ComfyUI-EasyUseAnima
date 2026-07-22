"""Current AiO first-pass cache state and helpers."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, TypeAlias

AIO_FIRST_PASS_CACHE_MAX_ENTRIES = 2
_AIO_FIRST_PASS_CACHE: dict[str, dict[str, Any]] = {}
_AIO_FIRST_PASS_CACHE_ORDER: list[str] = []

_RuntimeResolver: TypeAlias = Callable[[str], Any]
_RUNTIME_RESOLVER: _RuntimeResolver | None = None


def _bind_aio_first_pass_cache_runtime(*, resolve_helper: _RuntimeResolver) -> None:
    """Bind root compatibility helpers and state without importing the root module."""

    global _RUNTIME_RESOLVER
    _RUNTIME_RESOLVER = resolve_helper


def _runtime_helper(name: str) -> Any:
    resolver = _RUNTIME_RESOLVER
    if resolver is None:
        raise RuntimeError(
            f"[EasyUseAnima] AiO first-pass cache runtime helper is not bound: {name}"
        )
    return resolver(name)


def _clone_aio_cache_value(value):
    if isinstance(value, dict):
        return {
            key: _runtime_helper("_clone_aio_cache_value")(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [_runtime_helper("_clone_aio_cache_value")(item) for item in value]
    if isinstance(value, tuple):
        return tuple(
            _runtime_helper("_clone_aio_cache_value")(item) for item in value
        )
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
    _runtime_helper("_AIO_FIRST_PASS_CACHE").clear()
    _runtime_helper("_AIO_FIRST_PASS_CACHE_ORDER").clear()


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
    return _runtime_helper("_stable_change_key")({
        "schema": "easyuse_anima_aio_first_pass_cache",
        "version": 1,
        "scope": str(cache_scope or ""),
        "mode": settings.get("mode"),
        "resource_info": _runtime_helper("_prompt_data_json_safe")(
            context.get("resource_info", {})
        ),
        "input_settings": _runtime_helper("_prompt_data_json_safe")(
            context.get("input_settings", {})
        ),
        "prompt_data": _runtime_helper("_prompt_data_json_safe")(prompt_data),
        "lora_stack": _runtime_helper("_aio_lora_stack_signature")(lora_stack),
        "sampler": _runtime_helper("_prompt_data_json_safe")(
            settings.get("sampler", {})
        ),
        "model_patches": _runtime_helper("_prompt_data_json_safe")(
            settings.get("model_patches", {})
        ),
        "mod_guidance": _runtime_helper("_prompt_data_json_safe")(
            settings.get("mod_guidance", {})
        ),
        "artist_mix": _runtime_helper("_prompt_data_json_safe")(
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
    entry = _runtime_helper("_AIO_FIRST_PASS_CACHE").get(cache_key)
    if not entry:
        return None
    if cache_key in _runtime_helper("_AIO_FIRST_PASS_CACHE_ORDER"):
        _runtime_helper("_AIO_FIRST_PASS_CACHE_ORDER").remove(cache_key)
    _runtime_helper("_AIO_FIRST_PASS_CACHE_ORDER").append(cache_key)
    return (
        _runtime_helper("_clone_aio_cache_value")(entry["latent"]),
        _runtime_helper("_clone_aio_cache_value")(entry["image"]),
    )


def _put_aio_first_pass_cache(cache_key: str, latent, image) -> None:
    entry = {
        "latent": _runtime_helper("_clone_aio_cache_value")(latent),
        "image": _runtime_helper("_clone_aio_cache_value")(image),
    }
    _runtime_helper("_AIO_FIRST_PASS_CACHE")[cache_key] = entry
    if cache_key in _runtime_helper("_AIO_FIRST_PASS_CACHE_ORDER"):
        _runtime_helper("_AIO_FIRST_PASS_CACHE_ORDER").remove(cache_key)
    _runtime_helper("_AIO_FIRST_PASS_CACHE_ORDER").append(cache_key)
    while len(_runtime_helper("_AIO_FIRST_PASS_CACHE_ORDER")) > _runtime_helper(
        "AIO_FIRST_PASS_CACHE_MAX_ENTRIES"
    ):
        old_key = _runtime_helper("_AIO_FIRST_PASS_CACHE_ORDER").pop(0)
        _runtime_helper("_AIO_FIRST_PASS_CACHE").pop(old_key, None)


__all__ = ()
