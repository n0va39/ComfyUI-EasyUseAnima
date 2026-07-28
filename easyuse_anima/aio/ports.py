"""Narrow process AiO first-pass cache capability."""

from __future__ import annotations

from typing import Any, Protocol


class AIOFirstPassCachePort(Protocol):
    def get(self, cache_key: str) -> tuple[Any, Any] | None: ...

    def put(self, cache_key: str, latent: Any, image: Any) -> None: ...


__all__ = ()
