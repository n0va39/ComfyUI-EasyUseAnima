"""Immutable wildcard snapshot values and stateless materialization."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType

from . import sources as _wildcard_sources
from .models import WildcardOption
from .sources import _WildcardSourceFile, _WildcardSourceState

__all__ = ()


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
