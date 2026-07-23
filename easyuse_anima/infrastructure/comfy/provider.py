"""ComfyUI host-discovery contract."""

from __future__ import annotations

from typing import Protocol


class ComfyHostProvider(Protocol):
    """Narrow port for discovering capabilities exposed by the ComfyUI host."""

    def max_resolution(self) -> int: ...

    def find_node_class(self, node_id: str) -> type[object] | None: ...

    def find_node_mapping_class(self, node_id: str) -> type[object] | None: ...

    def find_loaded_node_class(self, node_id: str) -> type[object] | None: ...


__all__ = ("ComfyHostProvider",)
