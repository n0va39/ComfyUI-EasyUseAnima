"""Current AiO first-pass cache state and helpers."""

from __future__ import annotations

import time
from dataclasses import dataclass, replace
from threading import RLock
from typing import Any

from ..common.serialization import _stable_change_key
from ..infrastructure.comfy.resources import _comfy_resource_file_revision
from ..prompt.data import _prompt_data_json_safe
from .generation_migrations import (
    AIO_MODEL_PATCH_ORDER_REVISION,
    AIO_MODEL_PATCH_PRECEDENCE,
)
from .model_preparation import _aio_lora_stack_signature, _aio_safe_pag_in_stage
from .negpip import _aio_negpip_cache_signature

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


@dataclass(frozen=True, slots=True)
class _AIOFirstPassCacheMetrics:
    hits: int
    misses: int
    skips: int
    evictions: int


_AIO_FIRST_PASS_CACHE: dict[
    str,
    _AIOFirstPassCacheEntry | dict[str, Any],
] = {}
_AIO_FIRST_PASS_CACHE_ORDER: list[str] = []
_AIO_FIRST_PASS_CACHE_LOCK = RLock()
_AIO_FIRST_PASS_CACHE_GENERATION = 0
_AIO_FIRST_PASS_CACHE_METRICS = {
    "hits": 0,
    "misses": 0,
    "skips": 0,
    "evictions": 0,
}


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
    with _AIO_FIRST_PASS_CACHE_LOCK:
        return sum(
            _aio_first_pass_cache_entry_size_bytes(entry)
            for entry in _AIO_FIRST_PASS_CACHE.values()
        )


def _aio_first_pass_cache_metrics_snapshot() -> _AIOFirstPassCacheMetrics:
    with _AIO_FIRST_PASS_CACHE_LOCK:
        return _AIOFirstPassCacheMetrics(
            hits=_AIO_FIRST_PASS_CACHE_METRICS["hits"],
            misses=_AIO_FIRST_PASS_CACHE_METRICS["misses"],
            skips=_AIO_FIRST_PASS_CACHE_METRICS["skips"],
            evictions=_AIO_FIRST_PASS_CACHE_METRICS["evictions"],
        )


def _reset_aio_first_pass_cache_metrics() -> None:
    with _AIO_FIRST_PASS_CACHE_LOCK:
        for name in _AIO_FIRST_PASS_CACHE_METRICS:
            _AIO_FIRST_PASS_CACHE_METRICS[name] = 0


def _record_aio_first_pass_cache_metric(name: str) -> None:
    with _AIO_FIRST_PASS_CACHE_LOCK:
        _AIO_FIRST_PASS_CACHE_METRICS[name] += 1


def _clear_aio_first_pass_cache() -> None:
    global _AIO_FIRST_PASS_CACHE_GENERATION

    with _AIO_FIRST_PASS_CACHE_LOCK:
        _AIO_FIRST_PASS_CACHE_GENERATION += 1
        _AIO_FIRST_PASS_CACHE.clear()
        _AIO_FIRST_PASS_CACHE_ORDER.clear()


def _set_aio_first_pass_cache_enabled(enabled: bool) -> None:
    global _AIO_FIRST_PASS_CACHE_ENABLED, _AIO_FIRST_PASS_CACHE_GENERATION

    next_enabled = bool(enabled)
    with _AIO_FIRST_PASS_CACHE_LOCK:
        if next_enabled != _AIO_FIRST_PASS_CACHE_ENABLED:
            _AIO_FIRST_PASS_CACHE_GENERATION += 1
        _AIO_FIRST_PASS_CACHE_ENABLED = next_enabled
        if not _AIO_FIRST_PASS_CACHE_ENABLED:
            _AIO_FIRST_PASS_CACHE.clear()
            _AIO_FIRST_PASS_CACHE_ORDER.clear()


def _aio_first_pass_cache_now() -> float:
    return time.monotonic()


def _aio_first_pass_resource_revision(
    resource_info,
    lora_signature,
) -> dict[str, Any]:
    info = resource_info if isinstance(resource_info, dict) else {}

    def revision(folder_name: str, value) -> dict[str, int | str] | None:
        name = str(value or "").strip()
        if not name:
            return None
        return _comfy_resource_file_revision(folder_name, name)

    lora_revisions = []
    if isinstance(lora_signature, list):
        for entry in lora_signature:
            name = entry.get("name") if isinstance(entry, dict) else ""
            lora_revisions.append(revision("loras", name))

    return {
        "unet": revision("diffusion_models", info.get("unet_name")),
        "vae": revision("vae", info.get("vae_name")),
        "clip": revision("text_encoders", info.get("clip_name")),
        "loras": lora_revisions,
    }


def _aio_first_pass_model_patch_plan(model_patches) -> dict[str, Any]:
    """Return only normalized patch inputs that can affect the first pass."""

    source = model_patches if isinstance(model_patches, dict) else {}
    patches: dict[str, Any] = {}

    aura_flow = source.get("aura_flow")
    if isinstance(aura_flow, dict):
        patches["aura_flow"] = {"shift": aura_flow.get("shift")}

    kj = source.get("kj")
    if isinstance(kj, dict):
        if bool(kj.get("fp16_accumulation")):
            patches["kj.fp16_accumulation"] = {"enabled": True}
        sage_attention = str(kj.get("sage_attention") or "disabled")
        if sage_attention != "disabled":
            patches["kj.sage_attention"] = {
                "mode": sage_attention,
                "allow_compile": bool(kj.get("sage_allow_compile")),
            }
        torch_compile = kj.get("torch_compile")
        if isinstance(torch_compile, dict) and bool(torch_compile.get("enabled")):
            patches["kj.torch_compile"] = {
                key: torch_compile.get(key)
                for key in (
                    "backend",
                    "fullgraph",
                    "mode",
                    "dynamic",
                    "compile_transformer_blocks_only",
                    "dynamo_cache_size_limit",
                    "debug_compile_keys",
                    "disable_dynamic_vram",
                )
            }

    dave = source.get("dave")
    if isinstance(dave, dict) and bool(dave.get("enabled")):
        stage_scope = dave.get("stage_scope")
        applies_to_first_pass = (
            bool(stage_scope.get("first_pass", True))
            if isinstance(stage_scope, dict)
            else True
        )
        if applies_to_first_pass:
            patches["dave"] = {
                "mask": dave.get("mask"),
                "strength": dave.get("strength"),
                "tau": dave.get("tau"),
                "stage_scope": {"first_pass": True},
            }

    safe_pag = source.get("safe_pag")
    if isinstance(safe_pag, dict) and _aio_safe_pag_in_stage(
        safe_pag,
        "first_pass",
    ):
        patches["safe_pag"] = {
            key: safe_pag.get(key)
            for key in (
                "scale",
                "block_indices",
                "perturbation_strength",
                "head_indices",
                "start_percent",
                "end_percent",
                "rescale",
                "rescale_mode",
            )
        }
        patches["safe_pag"]["stage_scope"] = {"first_pass": True}

    return {
        "order_revision": AIO_MODEL_PATCH_ORDER_REVISION,
        "precedence": [list(edge) for edge in AIO_MODEL_PATCH_PRECEDENCE],
        "patches": patches,
    }


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
    resource_info = context.get("resource_info", {})
    lora_signature = _aio_lora_stack_signature(lora_stack)
    payload = {
        "schema": "easyuse_anima_aio_first_pass_cache",
        "version": 3,
        "scope": str(cache_scope or ""),
        "mode": settings.get("mode"),
        "resource_info": _prompt_data_json_safe(resource_info),
        "resource_revision": _aio_first_pass_resource_revision(
            resource_info,
            lora_signature,
        ),
        "input_settings": _prompt_data_json_safe(
            context.get("input_settings", {})
        ),
        "prompt_data": _prompt_data_json_safe(prompt_data),
        "lora_stack": lora_signature,
        "sampler": _prompt_data_json_safe(
            settings.get("sampler", {})
        ),
        "model_patch_plan": _prompt_data_json_safe(
            _aio_first_pass_model_patch_plan(settings.get("model_patches", {}))
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
    }
    negpip_signature = _aio_negpip_cache_signature(
        settings.get("negpip"),
        negative_prompt=str(negative_prompt or ""),
    )
    if negpip_signature is not None:
        payload["negpip"] = negpip_signature
    return _stable_change_key(payload)


def _get_aio_first_pass_cache(cache_key: str):
    with _AIO_FIRST_PASS_CACHE_LOCK:
        if not _AIO_FIRST_PASS_CACHE_ENABLED:
            _AIO_FIRST_PASS_CACHE_METRICS["skips"] += 1
            return None
        entry = _AIO_FIRST_PASS_CACHE.get(cache_key)
        if not entry:
            _AIO_FIRST_PASS_CACHE_METRICS["misses"] += 1
            return None
        if isinstance(entry, _AIOFirstPassCacheEntry):
            now = _aio_first_pass_cache_now()
            if now - entry.created_at >= AIO_FIRST_PASS_CACHE_TTL_SECONDS:
                _AIO_FIRST_PASS_CACHE.pop(cache_key, None)
                if cache_key in _AIO_FIRST_PASS_CACHE_ORDER:
                    _AIO_FIRST_PASS_CACHE_ORDER.remove(cache_key)
                _AIO_FIRST_PASS_CACHE_METRICS["misses"] += 1
                _AIO_FIRST_PASS_CACHE_METRICS["evictions"] += 1
                return None
            entry = replace(entry, last_access_at=now)
            _AIO_FIRST_PASS_CACHE[cache_key] = entry
        if cache_key in _AIO_FIRST_PASS_CACHE_ORDER:
            _AIO_FIRST_PASS_CACHE_ORDER.remove(cache_key)
        _AIO_FIRST_PASS_CACHE_ORDER.append(cache_key)
        _AIO_FIRST_PASS_CACHE_METRICS["hits"] += 1
    if isinstance(entry, _AIOFirstPassCacheEntry):
        return entry.checkout()
    return (
        _clone_aio_cache_value(entry["latent"]),
        _clone_aio_cache_value(entry["image"]),
    )


def _put_aio_first_pass_cache(cache_key: str, latent, image) -> None:
    with _AIO_FIRST_PASS_CACHE_LOCK:
        if not _AIO_FIRST_PASS_CACHE_ENABLED:
            _AIO_FIRST_PASS_CACHE_METRICS["skips"] += 1
            return
        generation = _AIO_FIRST_PASS_CACHE_GENERATION
    if (
        _aio_cache_pair_size_bytes(latent, image)
        > AIO_FIRST_PASS_CACHE_MAX_ENTRY_BYTES
    ):
        _record_aio_first_pass_cache_metric("skips")
        return
    entry = _AIOFirstPassCacheEntry.capture(
        latent,
        image,
        now=_aio_first_pass_cache_now(),
    )
    if entry.size_bytes > AIO_FIRST_PASS_CACHE_MAX_ENTRY_BYTES:
        _record_aio_first_pass_cache_metric("skips")
        return
    with _AIO_FIRST_PASS_CACHE_LOCK:
        if (
            not _AIO_FIRST_PASS_CACHE_ENABLED
            or generation != _AIO_FIRST_PASS_CACHE_GENERATION
        ):
            _AIO_FIRST_PASS_CACHE_METRICS["skips"] += 1
            return
        _AIO_FIRST_PASS_CACHE[cache_key] = entry
        if cache_key in _AIO_FIRST_PASS_CACHE_ORDER:
            _AIO_FIRST_PASS_CACHE_ORDER.remove(cache_key)
        _AIO_FIRST_PASS_CACHE_ORDER.append(cache_key)
        while _AIO_FIRST_PASS_CACHE_ORDER and (
            len(_AIO_FIRST_PASS_CACHE_ORDER)
            > AIO_FIRST_PASS_CACHE_MAX_ENTRIES
            or _aio_first_pass_cache_total_bytes()
            > AIO_FIRST_PASS_CACHE_MAX_BYTES
        ):
            old_key = _AIO_FIRST_PASS_CACHE_ORDER.pop(0)
            _AIO_FIRST_PASS_CACHE.pop(old_key, None)
            _AIO_FIRST_PASS_CACHE_METRICS["evictions"] += 1


__all__ = ()
