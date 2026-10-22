"""Model-aware public optimization-node contracts; providers own execution."""

from __future__ import annotations

import inspect

from ..infrastructure.comfy.wiring import resolve_comfy_host_helper

TORCH_COMPILE_DEFAULTS = {
    "enabled": False, "provider": "kj", "backend": "inductor", "fullgraph": False,
    "mode": "default", "dynamic": "auto", "compile_transformer_blocks_only": True,
    "dynamo_cache_size_limit": 64, "debug_compile_keys": False, "disable_dynamic_vram": False,
}
OPTIMIZATION_PROVIDERS = {
    "torch_compile": (
        ("kj", "TorchCompileModelAdvanced", ("anima", "moss_image", "krea2")),
        ("anima_block_compile", "AnimaBlockCompile", ("anima",)),
    ),
    "dave": (("anima_dave", "AnimaDAVE", ("anima", "moss_image")),),
}


def optimization_provider(family, feature, provider_id, node_lookup=None):
    spec = next((item for item in OPTIMIZATION_PROVIDERS.get(feature, ())
                 if item[0] == provider_id), None)
    if spec is None or family not in spec[2]:
        return None, "unsupported"
    lookup = node_lookup or resolve_comfy_host_helper("_find_comfy_node_class", lambda _name: None)
    node = lookup(spec[1])
    if node is None:
        return None, "missing_dependency"
    if getattr(node, "RETURN_TYPES", None) != ("MODEL",) or getattr(node, "FUNCTION", None) != "patch":
        return None, "incompatible"
    try:
        inputs = node.INPUT_TYPES()
        required = inputs.get("required", {})
        parameters = inspect.signature(node.patch).parameters
        if feature == "dave":
            names = ("model", "mask", "strength", "tau")
            masks = required["mask"][0]
            if family == "moss_image" and "moss_dave_alpha.npz" not in masks:
                return None, "incompatible"
        elif provider_id == "anima_block_compile":
            names = ("model",)
        else:
            names = ("model", "backend", "fullgraph", "mode", "dynamic",
                     "dynamo_cache_size_limit", "compile_transformer_blocks_only", "debug_compile_keys")
        if not all(name in parameters and name in required for name in names):
            return None, "incompatible"
        call_names = names
        if provider_id == "kj":
            # AiO passes this optional KJ input as well as the required controls.
            optional = inputs.get("optional", {})
            if "disable_dynamic_vram" not in required and "disable_dynamic_vram" not in optional:
                return None, "incompatible"
            call_names = (*names, "disable_dynamic_vram")
        inspect.signature(node.patch).bind(None, **dict.fromkeys(call_names))
    except (AttributeError, KeyError, TypeError, ValueError):
        return None, "incompatible"
    return node, "available"


def optimization_manifest(family, node_lookup):
    return {
        feature: [
            {"id": provider_id, "node_id": node_id, "models": list(models),
             "status": optimization_provider(family, feature, provider_id, node_lookup)[1]}
            for provider_id, node_id, models in providers
        ]
        for feature, providers in OPTIMIZATION_PROVIDERS.items()
    }


def resolve_dave_mask(node, family, mask):
    """Use model-specific upstream masks without rewriting saved explicit masks."""
    selected = str(mask or "auto")
    if selected == "auto":
        masks = node.INPUT_TYPES()["required"]["mask"][0]
        if "auto" not in masks:
            selected = "moss_dave_alpha.npz" if family == "moss_image" else "dave_alpha.npz"
    if family == "moss_image" and selected == "dave_alpha.npz":
        raise ValueError("[EasyUseAnima] MOSS DAVE requires auto or a MOSS mask; the saved Anima mask is incompatible.")
    return selected

__all__ = ()
