"""Scoped ComfyUI compatibility for the 40-block Anima 2.9B architecture."""

from __future__ import annotations

from contextlib import contextmanager
from functools import wraps
from threading import RLock

ANIMA_BASE_BLOCK_COUNT = 28
ANIMA_29B_BLOCK_COUNT = 40
# New-index positions recorded by the model's expand_manifest.json.
ANIMA_29B_INSERTION_POSITIONS = (
    2,
    5,
    8,
    11,
    14,
    17,
    21,
    24,
    27,
    30,
    33,
    36,
)
ANIMA_29B_LEGACY_BLOCK_MAP = tuple(
    block_index
    for block_index in range(ANIMA_29B_BLOCK_COUNT)
    if block_index not in ANIMA_29B_INSERTION_POSITIONS
)

_DETECTION_LOCK = RLock()


def _state_dict_anima_block_count(state_dict, key_prefix: str = "") -> int | None:
    prefix = f"{key_prefix}blocks."
    indices: set[int] = set()
    for raw_key in state_dict:
        key = str(raw_key)
        if not key.startswith(prefix):
            continue
        block_text = key[len(prefix):].partition(".")[0]
        if block_text.isdigit():
            indices.add(int(block_text))
    if indices == set(range(ANIMA_29B_BLOCK_COUNT)):
        return ANIMA_29B_BLOCK_COUNT
    return None


def _patch_anima_29b_detected_config(config, state_dict, key_prefix: str):
    if not isinstance(config, dict) or config.get("image_model") != "anima":
        return config
    if _state_dict_anima_block_count(state_dict, key_prefix) != ANIMA_29B_BLOCK_COUNT:
        return config
    if config.get("num_blocks") == ANIMA_29B_BLOCK_COUNT:
        return config
    patched = dict(config)
    patched["num_blocks"] = ANIMA_29B_BLOCK_COUNT
    return patched


@contextmanager
def _scoped_anima_29b_model_detection():
    """Patch model detection only while EasyUse loads an AiO diffusion model."""

    try:
        from comfy import model_detection  # type: ignore
    except ImportError:
        yield
        return

    with _DETECTION_LOCK:
        previous = getattr(model_detection, "detect_unet_config", None)
        if not callable(previous):
            yield
            return

        @wraps(previous)
        def detect_unet_config(state_dict, key_prefix, *args, **kwargs):
            config = previous(state_dict, key_prefix, *args, **kwargs)
            return _patch_anima_29b_detected_config(
                config,
                state_dict,
                str(key_prefix or ""),
            )

        model_detection.detect_unet_config = detect_unet_config
        try:
            yield
        finally:
            if getattr(model_detection, "detect_unet_config", None) is detect_unet_config:
                model_detection.detect_unet_config = previous


def _anima_unet_config(model):
    base_model = getattr(model, "model", model)
    model_config = getattr(base_model, "model_config", None)
    config = getattr(model_config, "unet_config", None)
    return config if isinstance(config, dict) else None


def _is_anima_29b_model(model) -> bool:
    config = _anima_unet_config(model)
    return bool(
        config
        and config.get("image_model") == "anima"
        and config.get("num_blocks") == ANIMA_29B_BLOCK_COUNT
    )


def _reload_anima_29b_model(factory, factory_args, **kwargs):
    with _scoped_anima_29b_model_detection():
        model = factory(*factory_args, **kwargs)
    return _install_anima_29b_cached_reload(model)


def _install_anima_29b_cached_reload(model):
    """Keep 40-block detection active when ComfyUI deep-clones a disk-backed model."""

    if not _is_anima_29b_model(model):
        return model
    cached = getattr(model, "cached_patcher_init", None)
    if not isinstance(cached, tuple) or len(cached) != 2:
        return model
    factory, factory_args = cached
    if factory is _reload_anima_29b_model:
        return model
    if not callable(factory) or not isinstance(factory_args, (list, tuple)):
        return model
    model.cached_patcher_init = (
        _reload_anima_29b_model,
        (factory, tuple(factory_args)),
    )
    return model


def _load_model_with_anima_29b_support(loader):
    with _scoped_anima_29b_model_detection():
        model = loader()
    return _install_anima_29b_cached_reload(model)


__all__ = ()
