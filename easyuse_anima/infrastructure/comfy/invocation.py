"""Domain-neutral ComfyUI node-invocation adapters."""

from __future__ import annotations

import inspect
from collections.abc import Callable
from typing import Any


def _node_output_tuple(result) -> tuple:
    value = getattr(result, "result", None)
    if value is not None:
        return tuple(value)
    if isinstance(result, dict) and "result" in result:
        return tuple(result["result"])
    if isinstance(result, tuple):
        return result
    return (result,)


def _call_with_supported_kwargs(method, args: tuple[Any, ...], kwargs: dict[str, Any], label: str):
    try:
        parameters = inspect.signature(method).parameters
    except (TypeError, ValueError):
        return method(*args, **kwargs)
    accepts_kwargs = any(param.kind == inspect.Parameter.VAR_KEYWORD for param in parameters.values())
    if accepts_kwargs:
        return method(*args, **kwargs)
    supported_kwargs = {key: value for key, value in kwargs.items() if key in parameters}
    missing_required = []
    consumed_positionals = len(args)
    for index, (name, param) in enumerate(parameters.items()):
        if index < consumed_positionals:
            continue
        if name in supported_kwargs:
            continue
        if param.default is inspect.Parameter.empty and param.kind in (
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
            inspect.Parameter.KEYWORD_ONLY,
        ):
            missing_required.append(name)
    if missing_required:
        raise RuntimeError(
            f"[EasyUseAnima] {label} requires unsupported new input(s): "
            f"{', '.join(missing_required)}. Update ComfyUI-EasyUseAnima or disable that node option."
        )
    return method(*args, **supported_kwargs)


def _common_upscale_image(samples, width: int, height: int, upscale_method: str):
    try:
        import comfy.utils  # type: ignore

        return comfy.utils.common_upscale(samples, width, height, upscale_method, "disabled")
    except Exception:
        import torch.nn.functional as F  # type: ignore

        method = "bicubic" if str(upscale_method) == "lanczos" else str(upscale_method)
        if method in {"bilinear", "bicubic"}:
            return F.interpolate(samples, size=(height, width), mode=method, align_corners=False)
        return F.interpolate(samples, size=(height, width), mode=method)


def _encode_with_comfy_clip(
    clip,
    text: str,
    find_node_class: Callable[[str], Any],
):
    encoder_cls = find_node_class("CLIPTextEncode")
    if encoder_cls is None:
        raise RuntimeError("[EasyUseAnima] Could not find ComfyUI CLIPTextEncode.")
    encoder = encoder_cls()
    method = getattr(encoder, "encode", None)
    if method is None:
        raise RuntimeError("[EasyUseAnima] CLIPTextEncode does not expose encode.")
    result = method(clip, text)
    if not isinstance(result, tuple) or not result:
        raise RuntimeError("[EasyUseAnima] CLIPTextEncode returned no conditioning.")
    return result[0]


__all__ = ()
