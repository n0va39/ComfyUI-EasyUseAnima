"""SAM3 detection and Impact Detailer integration helpers."""

from __future__ import annotations

import inspect
import re
import sys
from typing import Any


def _unbound_runtime(*_args, **_kwargs) -> Any:
    raise RuntimeError("SAM3 runtime dependencies are not bound.")


_find_comfy_node_class = _unbound_runtime
_find_comfy_node_mapping_class = _unbound_runtime


def _bind_sam3_runtime(*, resolve_helper) -> None:
    global _find_comfy_node_class, _find_comfy_node_mapping_class

    def runtime_helper(name):
        def call(*args, **kwargs):
            return resolve_helper(name)(*args, **kwargs)

        return call

    _find_comfy_node_class = runtime_helper("_find_comfy_node_class")
    _find_comfy_node_mapping_class = runtime_helper("_find_comfy_node_mapping_class")


def _find_impact_detailer_class():
    cls = _find_comfy_node_mapping_class("DetailerForEach")
    if cls is not None:
        return cls

    for module in list(sys.modules.values()):
        mappings = getattr(module, "NODE_CLASS_MAPPINGS", None)
        if isinstance(mappings, dict):
            cls = mappings.get("DetailerForEach")
            if cls is not None:
                return cls

    try:
        from impact.impact_pack import DetailerForEach  # type: ignore

        return DetailerForEach
    except Exception:
        pass
    try:
        from modules.impact.impact_pack import DetailerForEach  # type: ignore

        return DetailerForEach
    except Exception:
        pass

    raise RuntimeError(
        "[EasyUseAnima] SAM3 Detailer requires ComfyUI Impact Pack's DetailerForEach. "
        "Install/enable ComfyUI-Impact-Pack, then restart ComfyUI."
    )


def _find_sam3_detect_class():
    cls = _find_comfy_node_class("SAM3_Detect")
    if cls is not None:
        return cls
    # Optional ComfyUI native node integration.
    # This imports only the built-in comfy_extras.nodes_sam3.SAM3_Detect class.
    # It does not load user-provided modules or execute dynamic code.
    try:
        from comfy_extras.nodes_sam3 import SAM3_Detect  # type: ignore

        return SAM3_Detect
    except Exception:
        pass
    raise RuntimeError(
        "[EasyUseAnima] SAM3_Detect was not found. "
        "Use a ComfyUI build with native SAM3 support, then restart ComfyUI."
    )


def _find_impact_mask_to_segs_class():
    cls = _find_comfy_node_class("MaskToSEGS")
    if cls is not None:
        return cls

    for module in list(sys.modules.values()):
        mappings = getattr(module, "NODE_CLASS_MAPPINGS", None)
        if isinstance(mappings, dict):
            cls = mappings.get("MaskToSEGS")
            if cls is not None:
                return cls

    try:
        from impact.segs_nodes import MaskToSEGS  # type: ignore

        return MaskToSEGS
    except Exception:
        pass
    try:
        from modules.impact.segs_nodes import MaskToSEGS  # type: ignore

        return MaskToSEGS
    except Exception:
        pass
    try:
        from impact.impact_pack import MaskToSEGS  # type: ignore

        return MaskToSEGS
    except Exception:
        pass
    try:
        from modules.impact.impact_pack import MaskToSEGS  # type: ignore

        return MaskToSEGS
    except Exception:
        pass

    raise RuntimeError(
        "[EasyUseAnima] Anima SAM3 Detailer requires ComfyUI Impact Pack's MaskToSEGS. "
        "Install/enable ComfyUI-Impact-Pack, then restart ComfyUI."
    )


def _format_sam3_detection_prompt(detect_prompt: str, detect_count: int) -> str:
    prompt = str(detect_prompt or "").strip()
    if not prompt:
        raise ValueError("[EasyUseAnima] SAM3 detect prompt is empty.")

    max_det = max(1, int(detect_count))
    parts = [part.strip() for part in re.split(r"[,\n]+", prompt) if part.strip()]
    formatted = []
    for part in parts:
        if re.search(r":\s*[\d.]+\s*$", part):
            formatted.append(part)
        else:
            formatted.append(f"{part}:{max_det}")
    return ", ".join(formatted)


def _sam3_context(model, clip, vae, ckpt_name: str = "") -> dict[str, Any]:
    return {
        "model": model,
        "clip": clip,
        "vae": vae,
        "ckpt_name": ckpt_name,
    }


def _context_value(ctx, key: str):
    if isinstance(ctx, dict):
        return ctx.get(key)
    return None


def _empty_mask_for_image(image):
    try:
        import torch  # type: ignore
    except Exception as exc:
        raise RuntimeError("[EasyUseAnima] torch is required to create an empty mask.") from exc

    batch = int(image.shape[0])
    height = int(image.shape[1])
    width = int(image.shape[2])
    device = getattr(image, "device", None)
    return torch.zeros((batch, height, width), dtype=torch.float32, device=device)


def _empty_segs_for_image(image):
    return ((int(image.shape[1]), int(image.shape[2])), [])


def _segs_has_items(segs) -> bool:
    try:
        return len(segs[1]) > 0
    except Exception:
        return False


def _call_impact_detailer(detailer, **kwargs):
    method = getattr(detailer, "doit", None)
    if method is None:
        raise RuntimeError("[EasyUseAnima] Impact DetailerForEach does not expose a doit method.")
    signature = inspect.signature(method)
    parameters = signature.parameters
    accepts_kwargs = any(param.kind == inspect.Parameter.VAR_KEYWORD for param in parameters.values())
    call_kwargs = kwargs if accepts_kwargs else {key: value for key, value in kwargs.items() if key in parameters}
    return method(**call_kwargs)


__all__ = ()
