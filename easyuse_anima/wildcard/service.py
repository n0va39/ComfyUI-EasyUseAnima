"""Snapshot-backed wildcard service facade."""

from __future__ import annotations

from collections.abc import Callable, Iterable, Sequence
from pathlib import Path

from . import sources as _wildcard_sources
from .library import _WildcardLibrary as _WildcardLibraryCore
from .mode import (
    WILDCARD_MODE_POPULATE,
    WILDCARD_MODE_SEQUENTIAL,
    normalize_wildcard_mode,
)
from .models import (
    WildcardExpansionBudget,
    WildcardExpansionResult,
    WildcardOption,
)
from .seed import normalize_seed
from .snapshot import (
    _DEFAULT_WILDCARD_SNAPSHOTS,
    _build_wildcard_snapshot,
    _WildcardSnapshot,
)
from .sources import resolve_wildcard_roots

__all__ = ()


_SnapshotResolver = Callable[[Iterable[Path]], _WildcardSnapshot]


def _wildcard_snapshot(roots: Iterable[Path]) -> _WildcardSnapshot:
    return _DEFAULT_WILDCARD_SNAPSHOTS.snapshot_for_roots(
        roots,
        scan_sources=_wildcard_sources._scan_wildcard_sources,
        build_snapshot=_build_wildcard_snapshot,
    )


def _load_wildcard_map_with(
    roots: Iterable[Path],
    *,
    snapshot_for_roots: _SnapshotResolver,
) -> dict[str, list[WildcardOption]]:
    snapshot = snapshot_for_roots(roots)
    return {key: list(options) for key, options in snapshot.mapping.items()}


def _load_wildcard_map(roots: Iterable[Path]) -> dict[str, list[WildcardOption]]:
    return _load_wildcard_map_with(
        roots,
        snapshot_for_roots=_wildcard_snapshot,
    )


def _list_wildcards_with(
    extra_paths: str | None = None,
    roots: Iterable[Path] | None = None,
    *,
    snapshot_for_roots: _SnapshotResolver,
) -> list[str]:
    snapshot = snapshot_for_roots(
        roots if roots is not None else resolve_wildcard_roots(extra_paths)
    )
    return list(snapshot.wildcard_names)


def list_wildcards(
    extra_paths: str | None = None,
    roots: Iterable[Path] | None = None,
) -> list[str]:
    return _list_wildcards_with(
        extra_paths,
        roots,
        snapshot_for_roots=_wildcard_snapshot,
    )


def _wildcard_sources_signature_with(
    extra_paths: str | None = None,
    roots: Iterable[Path] | None = None,
    *,
    snapshot_for_roots: _SnapshotResolver,
) -> dict:
    snapshot = snapshot_for_roots(
        roots if roots is not None else resolve_wildcard_roots(extra_paths)
    )
    return snapshot.public_signature()


def wildcard_sources_signature(
    extra_paths: str | None = None,
    roots: Iterable[Path] | None = None,
) -> dict:
    return _wildcard_sources_signature_with(
        extra_paths,
        roots,
        snapshot_for_roots=_wildcard_snapshot,
    )


class _WildcardLibrary(_WildcardLibraryCore):
    def __init__(
        self,
        roots: Iterable[Path] | None = None,
        *,
        snapshot: _WildcardSnapshot | None = None,
    ):
        if snapshot is None:
            snapshot = _wildcard_snapshot(roots or ())
        super().__init__(snapshot)


def _expand_wildcard_texts_with(
    texts: Sequence[str],
    seed=0,
    mode: str = WILDCARD_MODE_POPULATE,
    extra_paths: str | None = None,
    roots: Iterable[Path] | None = None,
    budget: WildcardExpansionBudget | None = None,
    *,
    snapshot_for_roots: _SnapshotResolver,
) -> tuple[WildcardExpansionResult, ...]:
    """Expand ordered texts through one deterministic selector stream."""

    from .expansion import _expand_snapshot_texts
    from .selector import _Selector

    sources = tuple(str(text or "") for text in texts)
    if not sources:
        return ()

    mode = normalize_wildcard_mode(mode)
    selector = _Selector(
        normalize_seed(seed),
        sequential=mode == WILDCARD_MODE_SEQUENTIAL,
    )
    resolved_roots = tuple(
        Path(root)
        for root in (
            roots if roots is not None else resolve_wildcard_roots(extra_paths)
        )
    )
    snapshot = snapshot_for_roots(resolved_roots)
    expansion_budget = (
        budget
        if isinstance(budget, WildcardExpansionBudget)
        else WildcardExpansionBudget()
    )
    return _expand_snapshot_texts(
        sources,
        selector,
        snapshot,
        expansion_budget,
    )


def expand_wildcard_texts(
    texts: Sequence[str],
    seed=0,
    mode: str = WILDCARD_MODE_POPULATE,
    extra_paths: str | None = None,
    roots: Iterable[Path] | None = None,
    budget: WildcardExpansionBudget | None = None,
) -> tuple[WildcardExpansionResult, ...]:
    """Expand ordered texts through one deterministic selector stream.

    Each text keeps its existing recursion and safety budget, while expansion
    stages run across the texts in order. This matches expanding one Prompt
    Studio prompt without joining fields through a lossy delimiter.
    """

    return _expand_wildcard_texts_with(
        texts,
        seed=seed,
        mode=mode,
        extra_paths=extra_paths,
        roots=roots,
        budget=budget,
        snapshot_for_roots=_wildcard_snapshot,
    )


def expand_wildcards(
    text: str,
    seed=0,
    mode: str = WILDCARD_MODE_POPULATE,
    extra_paths: str | None = None,
    roots: Iterable[Path] | None = None,
    budget: WildcardExpansionBudget | None = None,
) -> WildcardExpansionResult:
    return expand_wildcard_texts(
        (text,),
        seed=seed,
        mode=mode,
        extra_paths=extra_paths,
        roots=roots,
        budget=budget,
    )[0]
