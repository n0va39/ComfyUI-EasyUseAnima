"""Domain-neutral ComfyUI capability and node-discovery adapters."""

from __future__ import annotations

import sys
from collections.abc import Callable
from typing import Any


def _comfy_max_resolution(comfy_nodes) -> int:
    try:
        return int(getattr(comfy_nodes, "MAX_RESOLUTION", 16384))
    except Exception:
        return 16384


def _comfy_sampler_names() -> list[str]:
    try:
        import comfy.samplers  # type: ignore

        return list(comfy.samplers.KSampler.SAMPLERS)
    except Exception:
        return [
            "er_sde",
            "euler",
            "euler_ancestral",
            "heun",
            "dpm_2",
            "dpm_2_ancestral",
            "dpmpp_2m",
            "dpmpp_sde",
            "ddim",
        ]


def _comfy_scheduler_names() -> list[str]:
    try:
        import comfy.samplers  # type: ignore

        return list(comfy.samplers.KSampler.SCHEDULERS)
    except Exception:
        return [
            "simple",
            "sgm_uniform",
            "karras",
            "exponential",
            "ddim_uniform",
            "beta",
            "normal",
            "linear_quadratic",
            "kl_optimal",
            "AYS SDXL",
            "AYS SD1",
            "AYS SVD",
            "GITS[coeff=1.2]",
            "LTXV[default]",
            "OSS FLUX",
            "OSS Wan",
            "OSS Chroma",
        ]


def _impact_core_module():
    module = sys.modules.get("impact.core")
    if module is not None:
        return module
    try:
        import impact.core as core  # type: ignore

        return core
    except Exception:
        pass
    try:
        from modules.impact import core  # type: ignore

        return core
    except Exception:
        pass
    return None


def _impact_scheduler_names() -> list[str]:
    core = _impact_core_module()
    if core is not None:
        try:
            return list(core.get_schedulers())
        except Exception:
            pass
    try:
        import comfy.samplers  # type: ignore

        return list(comfy.samplers.KSampler.SCHEDULERS)
    except Exception:
        return ["normal", "karras", "exponential", "sgm_uniform", "simple", "ddim_uniform"]


def _find_comfy_node_class(node_id: str, comfy_nodes=None):
    if comfy_nodes is not None:
        try:
            mappings = getattr(comfy_nodes, "NODE_CLASS_MAPPINGS", {})
            cls = mappings.get(node_id)
            if cls is not None:
                return cls
            cls = getattr(comfy_nodes, node_id, None)
            if cls is not None:
                return cls
        except Exception:
            pass
    for module in list(sys.modules.values()):
        try:
            mappings = getattr(module, "NODE_CLASS_MAPPINGS", None)
        except Exception:
            continue
        if isinstance(mappings, dict):
            cls = mappings.get(node_id)
            if cls is not None:
                return cls
    return None


def _require_custom_node_class(
    node_id: str,
    node_pack: str,
    install_hint: str,
    find_node_class: Callable[[str], Any] = _find_comfy_node_class,
):
    cls = find_node_class(node_id)
    if cls is not None:
        return cls
    raise RuntimeError(
        f"[EasyUseAnima] Missing required custom node '{node_id}'. "
        f"Install/enable {node_pack}, then restart ComfyUI. {install_hint}"
    )


def _require_any_custom_node_class(
    node_ids: tuple[str, ...],
    node_pack: str,
    install_hint: str,
    find_node_class: Callable[[str], Any] = _find_comfy_node_class,
):
    for node_id in node_ids:
        cls = find_node_class(node_id)
        if cls is not None:
            return node_id, cls
    joined = "', '".join(node_ids)
    raise RuntimeError(
        f"[EasyUseAnima] Missing required custom node. Tried '{joined}'. "
        f"Install/enable {node_pack}, then restart ComfyUI. {install_hint}"
    )


def _find_loaded_node_class(
    node_id: str,
    find_node_class: Callable[[str], Any] = _find_comfy_node_class,
):
    cls = find_node_class(node_id)
    if cls is not None:
        return cls

    for module in list(sys.modules.values()):
        try:
            mappings = getattr(module, "NODE_CLASS_MAPPINGS", None)
        except Exception:
            continue
        if isinstance(mappings, dict):
            cls = mappings.get(node_id)
            if cls is not None:
                return cls
    return None


__all__ = ()
