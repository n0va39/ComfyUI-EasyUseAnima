"""Domain-neutral ComfyUI node-invocation adapters."""

from __future__ import annotations

import inspect
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


__all__ = ()
