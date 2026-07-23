"""ComfyUI host-discovery contract."""

from __future__ import annotations

import sys
from collections.abc import Callable
from typing import Protocol

from .capabilities import (
    _comfy_max_resolution,
    _find_comfy_node_class,
    _find_loaded_node_class,
)


class ComfyHostProvider(Protocol):
    """Narrow port for discovering capabilities exposed by the ComfyUI host."""

    def max_resolution(self) -> int: ...

    def find_node_class(self, node_id: str) -> type[object] | None: ...

    def find_node_mapping_class(self, node_id: str) -> type[object] | None: ...

    def find_loaded_node_class(self, node_id: str) -> type[object] | None: ...


def _loaded_comfy_nodes() -> object | None:
    return sys.modules.get("nodes")


class DefaultComfyHostProvider:
    """Discover host capabilities lazily without caching ComfyUI state."""

    def __init__(
        self,
        load_comfy_nodes: Callable[[], object | None] = _loaded_comfy_nodes,
    ) -> None:
        self._load_comfy_nodes = load_comfy_nodes

    def _comfy_nodes(self) -> object | None:
        try:
            return self._load_comfy_nodes()
        except Exception:
            return None

    def max_resolution(self) -> int:
        return _comfy_max_resolution(self._comfy_nodes())

    def find_node_class(self, node_id: str) -> type[object] | None:
        return _find_comfy_node_class(node_id, self._comfy_nodes())

    def find_node_mapping_class(self, node_id: str) -> type[object] | None:
        try:
            mappings = getattr(self._comfy_nodes(), "NODE_CLASS_MAPPINGS", {})
            return mappings.get(node_id)
        except Exception:
            return None

    def find_loaded_node_class(self, node_id: str) -> type[object] | None:
        return _find_loaded_node_class(node_id, self.find_node_class)


__all__ = ("ComfyHostProvider", "DefaultComfyHostProvider")
