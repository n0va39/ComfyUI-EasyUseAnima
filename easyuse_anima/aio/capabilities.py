"""Feature policy and reviewed provider contracts, independent of model defaults."""

from __future__ import annotations

import inspect
from typing import Any

from ..infrastructure.comfy.wiring import resolve_comfy_host_helper

CAPABILITY_CONTRACT_VERSION = 1
SAMPLING_STAGES = ("sampler", "highres", "detailer", "upscale")
_COMMON_FEATURES = (
    "highres", "detailer", "upscale", "sage_attention", "fp16_accumulation",
    "artist_mix", "aio_hook",
)
_ANIMA_FEATURES = (
    *_COMMON_FEATURES, "mod_guidance", "negpip", "dave", "safe_pag",
    "torch_compile", "spectrum", "dit_corrections",
)
_MODEL_FEATURES = {
    "anima": _ANIMA_FEATURES,
    "moss_image": (*_COMMON_FEATURES, "negpip"),
    "krea2": (*_COMMON_FEATURES, "torch_compile"),
}

NATIVE_MOSS_SPECTRUM_NODE = "NativeMossSpectrumPatch"
NATIVE_MOSS_SPECTRUM_CONTRACT = {
    "contract_version": 1,
    "model_family": "moss_image",
    "loader": "comfy_native",
    "features": ["forecast"],
    "stages": ["sampler"],
}
SPECTRUM_PATCH_INPUTS = (
    "model", "steps", "window_size", "flex_window", "warmup_steps",
    "tail_actual_steps", "blend_w", "cheby_degree", "ridge_lambda",
    "history_size", "enabled", "one_sampler_only", "verbose", "compat_policy",
)


def _find_provider(node_id: str):
    lookup = resolve_comfy_host_helper("_find_comfy_node_class", lambda _name: None)
    return lookup(node_id)


def native_moss_spectrum_provider(node_lookup=None):
    """Resolve only the implemented native adapter ABI, never the legacy sampler."""
    node = (node_lookup or _find_provider)(NATIVE_MOSS_SPECTRUM_NODE)
    if node is None:
        return None, "missing_dependency"
    if getattr(node, "RETURN_TYPES", None) != ("MODEL",) or getattr(node, "FUNCTION", None) != "patch":
        return None, "incompatible"
    marker = getattr(node, "SPECTRUM_CAPABILITIES", None)
    if not isinstance(marker, dict) or any(
        marker.get(key) != value
        for key, value in NATIVE_MOSS_SPECTRUM_CONTRACT.items()
        if key not in ("features", "stages")
    ):
        return None, "incompatible"
    for key in ("features", "stages"):
        values = marker.get(key)
        if not isinstance(values, (list, tuple)) or not all(
            value in values for value in NATIVE_MOSS_SPECTRUM_CONTRACT[key]
        ):
            return None, "incompatible"
    patch = getattr(node, "patch", None)
    if not callable(patch):
        return None, "incompatible"
    try:
        signature = inspect.signature(patch)
        # Explicit inputs are required: **kwargs alone is not an ABI guarantee.
        if not all(name in signature.parameters for name in SPECTRUM_PATCH_INPUTS):
            return None, "incompatible"
        signature.bind(None, **dict.fromkeys(SPECTRUM_PATCH_INPUTS))
    except (TypeError, ValueError):
        return None, "incompatible"
    return node, "available"


def aio_feature_support(
    family: str, feature: str, stage: str = "sampler", *, node_lookup=None,
) -> dict[str, Any]:
    """Return install-dependent support without mutating any saved settings."""
    supported = feature in _MODEL_FEATURES.get(family, ()) and stage in SAMPLING_STAGES
    result = {
        "supported": supported,
        "status": "available" if supported else "unsupported",
        "stages": list(SAMPLING_STAGES) if feature in _MODEL_FEATURES.get(family, ()) else [],
        "provider": "",
        "adapter": "",
        "reason_code": "" if supported else "model_feature_unsupported",
    }
    if family == "moss_image" and feature == "spectrum":
        node, status = native_moss_spectrum_provider(node_lookup)
        stages = [
            name for name in SAMPLING_STAGES
            if node is not None and name in node.SPECTRUM_CAPABILITIES["stages"]
        ]
        supported = status == "available" and stage in stages
        result.update(
            supported=supported,
            status="unsupported" if status == "available" and not supported else status,
            stages=stages,
            provider="ComfyUI-Spectrum-KSampler",
            adapter=NATIVE_MOSS_SPECTRUM_NODE,
            reason_code=(
                "" if supported else
                "stage_not_supported" if status == "available" else
                "native_moss_adapter_missing" if status == "missing_dependency" else
                "native_moss_adapter_incompatible"
            ),
        )
    return result


def aio_capability_manifest(family: str, *, node_lookup=None) -> dict[str, Any]:
    return {
        "contract_version": CAPABILITY_CONTRACT_VERSION,
        "model_family": family,
        "features": {
            feature: aio_feature_support(family, feature, node_lookup=node_lookup)
            for feature in _ANIMA_FEATURES
        },
    }


__all__ = ()
