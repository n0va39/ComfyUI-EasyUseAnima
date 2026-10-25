"""Feature policy and reviewed provider contracts, independent of model defaults."""

from __future__ import annotations

import inspect
from typing import Any

from ..infrastructure.comfy.wiring import resolve_comfy_host_helper
from .optimization import optimization_manifest, optimization_provider

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
    "moss_image": (*_COMMON_FEATURES, "negpip", "dave", "torch_compile"),
    "krea2": (*_COMMON_FEATURES, "torch_compile"),
}

NATIVE_MOSS_SPECTRUM_NODE = "NativeMossSpectrumPatch"
MOSS_SPECTRUM_CONTRACT = {
    "contract_version": 1,
    "model_family": "moss_image",
    "loader": "comfy_native",
    "features": ["forecast"],
    "stages": ["sampler"],
}
NATIVE_MOSS_SPECTRUM_CONTRACT = MOSS_SPECTRUM_CONTRACT
# AiO owns the reviewed model/stage mapping. Canonical providers need only the
# public MODEL patch contract; older providers may further restrict its stages.
SPECTRUM_MODEL_PATCHES = {
    "moss_image": {
        "node_ids": ("SpectrumMossModelPatch", NATIVE_MOSS_SPECTRUM_NODE),
        "contract": MOSS_SPECTRUM_CONTRACT,
        "stages": SAMPLING_STAGES,
        "reason_prefix": "native_moss_adapter",  # Preserve existing API reason codes.
    },
    "krea2": {
        "node_ids": ("SpectrumKrea2ModelPatch", "NativeKrea2SpectrumPatch"),
        "contract": {**MOSS_SPECTRUM_CONTRACT, "model_family": "krea2"},
        "stages": SAMPLING_STAGES,
        "reason_prefix": "krea2_model_patch",
    },
}
_SPECTRUM_PATCH_INPUT_TYPES = {
    "model": "MODEL", "steps": "INT", "window_size": "FLOAT", "flex_window": "FLOAT",
    "warmup_steps": "INT", "tail_actual_steps": "INT", "blend_w": "FLOAT",
    "cheby_degree": "INT", "ridge_lambda": "FLOAT", "history_size": "INT",
    "enabled": "BOOLEAN", "one_sampler_only": "BOOLEAN", "verbose": "BOOLEAN",
    "compat_policy": ("legacy", "conservative", "strict"),
}
SPECTRUM_PATCH_INPUTS = tuple(_SPECTRUM_PATCH_INPUT_TYPES)


def _find_provider(node_id: str):
    lookup = resolve_comfy_host_helper("_find_comfy_node_class", lambda _name: None)
    return lookup(node_id)


def spectrum_model_patch_provider(family: str, node_lookup=None):
    """Return the selected node ID, validated MODEL patch, and availability.

    Prefer the canonical ID. Only try a legacy ID when it is absent, never to
    bypass an incompatible canonical provider.
    """
    spec = SPECTRUM_MODEL_PATCHES.get(family)
    if spec is None:
        return "", None, "unsupported"
    lookup = node_lookup or _find_provider
    node_id = spec["node_ids"][0]
    node = None
    for candidate in spec["node_ids"]:
        node = lookup(candidate)
        if node is not None:
            node_id = candidate
            break
    provider, status = _validate_spectrum_model_patch(
        node, spec["contract"], require_marker=node_id != spec["node_ids"][0],
    )
    return node_id, provider, status


def native_moss_spectrum_provider(node_lookup=None):
    """Compatibility entry point for callers of the original MOSS resolver."""
    _, node, status = spectrum_model_patch_provider("moss_image", node_lookup)
    return node, status


def _spectrum_patch_inputs(node):
    inputs = node.INPUT_TYPES()
    return {**inputs.get("required", {}), **inputs.get("optional", {})}


def _spectrum_patch_markers(node, inputs):
    markers = []
    if hasattr(node, "SPECTRUM_CAPABILITIES"):
        markers.append(node.SPECTRUM_CAPABILITIES)
    model_spec = inputs["model"]
    if len(model_spec) > 1 and isinstance(model_spec[1], dict):
        if "spectrum_capabilities" in model_spec[1]:
            markers.append(model_spec[1]["spectrum_capabilities"])
    return markers


def _spectrum_marker_matches(marker, contract):
    if not isinstance(marker, dict) or any(
        marker.get(key) != value
        for key, value in contract.items()
        if key not in ("features", "stages")
    ):
        return False
    return all(
        isinstance(marker.get(key), (list, tuple))
        and all(value in marker[key] for value in contract[key])
        for key in ("features", "stages")
    )


def _validate_spectrum_model_patch(node, contract, *, require_marker=False):
    if node is None:
        return None, "missing_dependency"
    if getattr(node, "RETURN_TYPES", None) != ("MODEL",) or getattr(node, "FUNCTION", None) != "patch":
        return None, "incompatible"
    patch = getattr(node, "patch", None)
    if not callable(patch):
        return None, "incompatible"
    try:
        inputs = _spectrum_patch_inputs(node)
        for name, expected in _SPECTRUM_PATCH_INPUT_TYPES.items():
            field = inputs[name]
            if not isinstance(field, (list, tuple)) or not field:
                return None, "incompatible"
            actual = field[0]
            if isinstance(expected, tuple):
                if not isinstance(actual, (list, tuple)) or not all(value in actual for value in expected):
                    return None, "incompatible"
            elif actual != expected:
                return None, "incompatible"
        markers = _spectrum_patch_markers(node, inputs)
        if require_marker and not hasattr(node, "SPECTRUM_CAPABILITIES"):
            return None, "incompatible"
        if any(not _spectrum_marker_matches(marker, contract) for marker in markers):
            return None, "incompatible"
        signature = inspect.signature(patch)
        # Explicit inputs are required: **kwargs alone is not an ABI guarantee.
        if not all(
            name in signature.parameters and signature.parameters[name].kind in (
                inspect.Parameter.POSITIONAL_OR_KEYWORD, inspect.Parameter.KEYWORD_ONLY,
            )
            for name in SPECTRUM_PATCH_INPUTS
        ):
            return None, "incompatible"
        signature.bind(None, **dict.fromkeys(SPECTRUM_PATCH_INPUTS))
    except (AttributeError, KeyError, TypeError, ValueError):
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
    if family == "moss_image" and feature in ("dave", "torch_compile"):
        provider_id = "anima_dave" if feature == "dave" else "kj"
        _, status = optimization_provider(family, feature, provider_id, node_lookup or _find_provider)
        supported = status == "available" and stage in SAMPLING_STAGES
        result.update(
            supported=supported, status=status,
            stages=list(SAMPLING_STAGES) if status == "available" else [],
            provider="ComfyUI-Anima-DAVE" if feature == "dave" else "ComfyUI-KJNodes",
            adapter="AnimaDAVE" if feature == "dave" else "TorchCompileModelAdvanced",
            reason_code="" if supported else f"{feature}_provider_{status}",
        )
    if family in SPECTRUM_MODEL_PATCHES and feature == "spectrum":
        node_id, node, status = spectrum_model_patch_provider(family, node_lookup)
        spec = SPECTRUM_MODEL_PATCHES[family]
        reason_prefix = spec["reason_prefix"]
        markers = _spectrum_patch_markers(node, _spectrum_patch_inputs(node)) if node is not None else []
        stages = [
            name for name in spec["stages"]
            if node is not None and all(name in marker["stages"] for marker in markers)
        ]
        supported = status == "available" and stage in stages
        result.update(
            supported=supported,
            status="unsupported" if status == "available" and not supported else status,
            stages=stages,
            provider="ComfyUI-Spectrum-KSampler",
            adapter=node_id,
            reason_code=(
                "" if supported else
                "stage_not_supported" if status == "available" else
                f"{reason_prefix}_missing" if status == "missing_dependency" else
                f"{reason_prefix}_incompatible"
            ),
        )
    return result


def aio_capability_manifest(family: str, *, node_lookup=None) -> dict[str, Any]:
    return {
        "contract_version": CAPABILITY_CONTRACT_VERSION,
        "model_family": family,
        "optimization_providers": optimization_manifest(family, node_lookup or _find_provider),
        "features": {
            feature: aio_feature_support(family, feature, node_lookup=node_lookup)
            for feature in _ANIMA_FEATURES
        },
    }


__all__ = ()
