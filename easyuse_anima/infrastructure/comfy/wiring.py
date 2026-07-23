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
from .provider import DefaultComfyHostProvider


def _default_max_resolution() -> int:
    return DefaultComfyHostProvider().max_resolution()


def _default_node_mapping_class(node_id: str):
    return DefaultComfyHostProvider().find_node_mapping_class(node_id)


def _default_loaded_node_class(node_id: str):
    return DefaultComfyHostProvider().find_loaded_node_class(node_id)


def _default_require_custom_node_class(
    node_id: str,
    node_pack: str,
    install_hint: str,
):
    return _require_custom_node_class(
        node_id,
        node_pack,
        install_hint,
        find_node_class=DefaultComfyHostProvider().find_node_class,
    )


def _default_require_any_custom_node_class(
    node_ids: tuple[str, ...],
    node_pack: str,
    install_hint: str,
):
    return _require_any_custom_node_class(
        node_ids,
        node_pack,
        install_hint,
        find_node_class=DefaultComfyHostProvider().find_node_class,
    )


def _default_encode_with_comfy_clip(clip, text: str):
    return _encode_with_comfy_clip(
        clip,
        text,
        find_node_class=DefaultComfyHostProvider().find_node_class,
    )


def resolve_comfy_host_helper(
    name: str,
    fallback: Callable[[str], Any],
) -> Any:
    """Resolve the seven E-07 host seams without importing the root shim."""

    if name not in (
        "_comfy_max_resolution",
        "_find_comfy_node_class",
        "_find_comfy_node_mapping_class",
        "_find_loaded_node_class",
        "_require_custom_node_class",
        "_require_any_custom_node_class",
        "_encode_with_comfy_clip",
    ):
        return fallback(name)

    try:
        provider = get_runtime().comfy
    except RuntimeError:
        # Flat ``nodes`` imports used by local tooling do not execute package
        # bootstrap. Retired host seams use their canonical default provider;
        # the remaining B-11 seams keep their existing root resolver.
        if name == "_comfy_max_resolution":
            return _default_max_resolution
        if name == "_find_comfy_node_mapping_class":
            return _default_node_mapping_class
        if name == "_find_loaded_node_class":
            return _default_loaded_node_class
        if name == "_require_custom_node_class":
            return _default_require_custom_node_class
        if name == "_require_any_custom_node_class":
            return _default_require_any_custom_node_class
        if name == "_encode_with_comfy_clip":
            return _default_encode_with_comfy_clip
        return fallback(name)

    if name == "_comfy_max_resolution":
        return provider.max_resolution
    if name == "_find_comfy_node_class":
        return provider.find_node_class
    if name == "_find_comfy_node_mapping_class":
        return provider.find_node_mapping_class
    if name == "_find_loaded_node_class":
        return provider.find_loaded_node_class
    if name == "_require_custom_node_class":
        return partial(
            _require_custom_node_class,
            find_node_class=provider.find_node_class,
        )
    if name == "_require_any_custom_node_class":
        return partial(
            _require_any_custom_node_class,
            find_node_class=provider.find_node_class,
        )
    return partial(
        _encode_with_comfy_clip,
        find_node_class=provider.find_node_class,
    )


__all__ = ()
