"""Wildcard snapshot values, materialization, and private lifecycle ownership."""

from __future__ import annotations

import threading
from collections import OrderedDict
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType

from . import sources as _wildcard_sources
from .models import WildcardOption
from .sources import _WildcardSourceFile, _WildcardSourceState

__all__ = ()

_SNAPSHOT_CACHE_LIMIT = 16


@dataclass(frozen=True)
class _WildcardSnapshot:
    cache_key: tuple
    mapping: Mapping[str, tuple[WildcardOption, ...]]
    wildcard_names: tuple[str, ...]
    roots: tuple[str, ...]
    files: tuple[_WildcardSourceFile, ...]
    cacheable: bool

    def public_signature(self) -> dict:
        return {
            "roots": list(self.roots),
            "files": [
                {
                    "root": source.root,
                    "path": source.relative_path,
                    "mtime_ns": source.mtime_ns,
                    "size": source.size,
                }
                for source in self.files
            ],
        }


class _WildcardSnapshotStore:
    def __init__(self, *, cache_limit: int = _SNAPSHOT_CACHE_LIMIT) -> None:
        self._cache_limit = cache_limit
        self._condition = threading.Condition()
        self._cache: OrderedDict[tuple, _WildcardSnapshot] = OrderedDict()
        self._building: set[tuple] = set()

    def clear(self) -> None:
        with self._condition:
            self._cache.clear()

    def snapshot_for_roots(
        self,
        roots: Iterable[Path],
        *,
        scan_sources: Callable[[tuple[Path, ...]], _WildcardSourceState],
        build_snapshot: Callable[[_WildcardSourceState], _WildcardSnapshot],
    ) -> _WildcardSnapshot:
        resolved_roots = tuple(Path(root) for root in roots)
        while True:
            source_state = scan_sources(resolved_roots)
            cache_key = source_state.cache_key
            with self._condition:
                cached = self._cache.get(cache_key)
                if cached is not None:
                    self._cache.move_to_end(cache_key)
                    return cached
                if cache_key in self._building:
                    self._condition.wait()
                    continue
                self._building.add(cache_key)

            snapshot: _WildcardSnapshot | None = None
            failure: BaseException | None = None
            try:
                candidate = build_snapshot(source_state)
                verified_state = scan_sources(resolved_roots)
                if verified_state.cache_key == cache_key:
                    snapshot = candidate
            except BaseException as exc:
                failure = exc
            finally:
                with self._condition:
                    self._building.discard(cache_key)
                    if snapshot is not None and snapshot.cacheable:
                        self._cache[cache_key] = snapshot
                        self._cache.move_to_end(cache_key)
                        while len(self._cache) > self._cache_limit:
                            self._cache.popitem(last=False)
                    self._condition.notify_all()

            if failure is not None:
                raise failure
            if snapshot is not None:
                return snapshot


def _build_wildcard_snapshot(
    source_state: _WildcardSourceState,
) -> _WildcardSnapshot:
    mapping: dict[str, list[WildcardOption]] = {}
    cacheable = True
    for source in source_state.files:
        root = source_state.roots[source.root_index]
        try:
            entries = _wildcard_sources._load_wildcard_file(root, source.path)
        except OSError:
            cacheable = False
            continue
        for key, options in entries.items():
            if key not in mapping and options:
                mapping[key] = options

    frozen_mapping = MappingProxyType(
        {key: tuple(options) for key, options in mapping.items()}
    )
    return _WildcardSnapshot(
        cache_key=source_state.cache_key,
        mapping=frozen_mapping,
        wildcard_names=tuple(sorted(frozen_mapping)),
        roots=tuple(str(root) for root in source_state.roots),
        files=source_state.files,
        cacheable=cacheable,
    )


_DEFAULT_WILDCARD_SNAPSHOTS = _WildcardSnapshotStore()
