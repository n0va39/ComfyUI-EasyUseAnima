"""Anima Mod Guidance conditioning policy and adapter."""
from __future__ import annotations

import inspect

from ..infrastructure.comfy.invocation import _node_output_tuple

ANIMA_MOD_GUIDANCE_MODE_FROM_PROMPT_DATA = "prompt_data"
ANIMA_MOD_GUIDANCE_MODE_ENABLED = "enabled"
ANIMA_MOD_GUIDANCE_MODE_DISABLED = "disabled"
ANIMA_MOD_GUIDANCE_MODES = (
    ANIMA_MOD_GUIDANCE_MODE_FROM_PROMPT_DATA,
    ANIMA_MOD_GUIDANCE_MODE_ENABLED,
    ANIMA_MOD_GUIDANCE_MODE_DISABLED,
)
ANIMA_MOD_GUIDANCE_PROFILE_OFF = "off"
ANIMA_MOD_GUIDANCE_DEFAULT_PROFILE = "step_i8_skip27"
ANIMA_MOD_GUIDANCE_PROFILES = (
    ANIMA_MOD_GUIDANCE_PROFILE_OFF,
    ANIMA_MOD_GUIDANCE_DEFAULT_PROFILE,
    "step_i14",
    "uniform_w3",
)

_SPECTRUM_ANIMA_MOD_GUIDANCE_OLD_SIGNATURE_WARNED: set[str] = set()
_RUNTIME_RESOLVER = None
_RUNTIME_LOGGER_RESOLVER = None

def _bind_conditioning_runtime(*, resolve_helper, resolve_logger) -> None:
    global _RUNTIME_RESOLVER, _RUNTIME_LOGGER_RESOLVER
    _RUNTIME_RESOLVER = resolve_helper
    _RUNTIME_LOGGER_RESOLVER = resolve_logger

def _runtime_helper(name: str):
    if _RUNTIME_RESOLVER is None:
        raise RuntimeError(f"[EasyUseAnima] Conditioning runtime helper is not bound: {name}")
    return _RUNTIME_RESOLVER(name)

def _runtime_logger():
    if _RUNTIME_LOGGER_RESOLVER is None:
        raise RuntimeError("[EasyUseAnima] Conditioning logger is not bound.")
    return _RUNTIME_LOGGER_RESOLVER()

def _find_spectrum_anima_mod_guidance_class():
    cls = _runtime_helper("_find_loaded_node_class")("AnimaModGuidance")
    if cls is not None:
        return cls
    raise RuntimeError(
        "[EasyUseAnima] Anima Prompt Data Conditioning requires "
        "comfyui-spectrum-ksampler's AnimaModGuidance node. "
        "Install/enable comfyui-spectrum-ksampler, then restart ComfyUI."
    )

def _resolve_anima_mod_guidance_enabled(prompt_data_enabled: bool, mode: str) -> bool:
    mode = str(mode or ANIMA_MOD_GUIDANCE_MODE_FROM_PROMPT_DATA)
    if mode == ANIMA_MOD_GUIDANCE_MODE_ENABLED:
        return True
    if mode == ANIMA_MOD_GUIDANCE_MODE_DISABLED:
        return False
    return bool(prompt_data_enabled)

def _normalize_anima_mod_guidance_profile(profile: str) -> str:
    profile = str(profile or ANIMA_MOD_GUIDANCE_DEFAULT_PROFILE)
    if profile not in ANIMA_MOD_GUIDANCE_PROFILES:
        return ANIMA_MOD_GUIDANCE_DEFAULT_PROFILE
    return profile

def _warn_old_spectrum_anima_mod_guidance_once(patcher_cls) -> None:
    class_name = getattr(patcher_cls, "__qualname__", getattr(patcher_cls, "__name__", "AnimaModGuidance"))
    module_name = getattr(patcher_cls, "__module__", "")
    warning_key = f"{module_name}.{class_name}"
    if warning_key in _SPECTRUM_ANIMA_MOD_GUIDANCE_OLD_SIGNATURE_WARNED:
        return
    _SPECTRUM_ANIMA_MOD_GUIDANCE_OLD_SIGNATURE_WARNED.add(warning_key)
    _runtime_logger().warning(
        "[EasyUseAnima] Installed comfyui-spectrum-ksampler AnimaModGuidance "
        "uses an old patch() signature without separate negative quality-tag "
        "support. Generation will continue, but negative Mod Guidance quality "
        "tags are ignored by the model patch. Update comfyui-spectrum-ksampler "
        "to enable separate negative quality tags."
    )

def _apply_spectrum_anima_mod_guidance(
    model,
    clip,
    positive,
    negative,
    quality_tags: str,
    quality_neg: str,
    mod_w_profile: str,
):
    patcher_cls = _runtime_helper("_find_spectrum_anima_mod_guidance_class")()
    patcher = patcher_cls()
    patch = getattr(patcher, "patch", None)
    if patch is None:
        raise RuntimeError(
            "[EasyUseAnima] comfyui-spectrum-ksampler AnimaModGuidance does not expose patch()."
        )
    quality_tags = str(quality_tags or "")
    quality_neg = str(quality_neg or "")
    mod_w_profile = str(mod_w_profile or ANIMA_MOD_GUIDANCE_DEFAULT_PROFILE)
    patch_parameters = inspect.signature(patch).parameters
    patch_parameter_values = list(patch_parameters.values())
    patch_positional_count = sum(
        1 for param in patch_parameter_values
        if param.kind in (inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD)
    )
    patch_accepts_quality_neg = (
        any(name in patch_parameters for name in ("quality_neg", "quality_negative", "negative_quality_tags"))
        or any(param.kind == inspect.Parameter.VAR_POSITIONAL for param in patch_parameter_values)
        or patch_positional_count >= 7
    )
    if patch_accepts_quality_neg:
        result = patch(
            model,
            clip,
            quality_tags,
            quality_neg,
            mod_w_profile,
            positive,
            negative,
        )
    else:
        _warn_old_spectrum_anima_mod_guidance_once(patcher_cls)
        result = patch(
            model,
            clip,
            quality_tags,
            mod_w_profile,
            positive,
            negative,
        )
    values = _node_output_tuple(result)
    if not values:
        raise RuntimeError("[EasyUseAnima] AnimaModGuidance returned no MODEL.")
    return values[0]

__all__ = ()
