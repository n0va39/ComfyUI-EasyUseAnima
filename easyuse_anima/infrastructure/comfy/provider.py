"""ComfyUI host-discovery contract."""

from __future__ import annotations

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


def _load_comfy_nodes() -> object | None:
    try:
        import nodes as comfy_nodes  # type: ignore
    except Exception:
        return None
    return comfy_nodes


class DefaultComfyHostProvider:
    """Discover host capabilities lazily without caching ComfyUI state."""

    def max_resolution(self) -> int:
        return _comfy_max_resolution(_load_comfy_nodes())

    def find_node_class(self, node_id: str) -> type[object] | None:
        return _find_comfy_node_class(node_id, _load_comfy_nodes())

    def find_node_mapping_class(self, node_id: str) -> type[object] | None:
        try:
            mappings = getattr(_load_comfy_nodes(), "NODE_CLASS_MAPPINGS", {})
            return mappings.get(node_id)
        except Exception:
            return None

    def find_loaded_node_class(self, node_id: str) -> type[object] | None:
        return _find_loaded_node_class(node_id, self.find_node_class)


__all__ = ("ComfyHostProvider", "DefaultComfyHostProvider")
