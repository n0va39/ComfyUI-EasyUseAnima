"""Call-time wiring from root runtime resolvers to the Comfy host provider."""

from __future__ import annotations

from collections.abc import Callable
from functools import partial
from typing import Any

from ...runtime import get_runtime
from .capabilities import (
    _require_any_custom_node_class,
    _require_custom_node_class,
)
from .invocation import _encode_with_comfy_clip


def resolve_comfy_host_helper(
    name: str,
    fallback: Callable[[str], Any],
) -> Any:
    """Resolve the seven E-07 host seams without importing the root shim."""

    if name == "_comfy_max_resolution":
        return get_runtime().comfy.max_resolution
    if name == "_find_comfy_node_class":
        return get_runtime().comfy.find_node_class
    if name == "_find_comfy_node_mapping_class":
        return get_runtime().comfy.find_node_mapping_class
    if name == "_find_loaded_node_class":
        return get_runtime().comfy.find_loaded_node_class
    if name == "_require_custom_node_class":
        return partial(
            _require_custom_node_class,
            find_node_class=get_runtime().comfy.find_node_class,
        )
    if name == "_require_any_custom_node_class":
        return partial(
            _require_any_custom_node_class,
            find_node_class=get_runtime().comfy.find_node_class,
        )
    if name == "_encode_with_comfy_clip":
        return partial(
            _encode_with_comfy_clip,
            find_node_class=get_runtime().comfy.find_node_class,
        )
    return fallback(name)


__all__ = ()
