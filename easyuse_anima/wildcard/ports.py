"""Narrow process wildcard snapshot capability."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from pathlib import Path
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from .snapshot import _WildcardSnapshot
    from .sources import _WildcardSourceState


class WildcardSnapshotPort(Protocol):
    def snapshot_for_roots(
        self,
        roots: Iterable[Path],
        *,
        scan_sources: Callable[[tuple[Path, ...]], _WildcardSourceState],
        build_snapshot: Callable[[_WildcardSourceState], _WildcardSnapshot],
    ) -> _WildcardSnapshot: ...


__all__ = ()
