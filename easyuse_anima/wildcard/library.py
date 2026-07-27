"""Wildcard snapshot lookup and expansion diagnostics."""

from __future__ import annotations

from collections.abc import Sequence
from fnmatch import fnmatchcase

from . import sources as _wildcard_sources
from .models import WildcardOption
from .snapshot import _WildcardSnapshot

__all__ = ()


class _WildcardLibrary:
    def __init__(self, snapshot: _WildcardSnapshot):
        self.mapping = snapshot.mapping
        self.used: list[str] = []
        self.missing: list[str] = []

    def _record_used(self, key: str) -> None:
        if key not in self.used:
            self.used.append(key)

    def _record_missing(self, key: str) -> None:
        if key not in self.missing:
            self.missing.append(key)

    def options_for(self, raw_key: str) -> Sequence[WildcardOption]:
        key = _wildcard_sources._normalize_wildcard_key(raw_key)
        if key is None:
            return []
        options = self._options_for_normalized_key(key)
        if options:
            self._record_used(key)
        else:
            self._record_missing(key)
        return options

    def _options_for_normalized_key(self, key: str) -> Sequence[WildcardOption]:
        if key in self.mapping:
            return self.mapping[key]
        if "/" not in key and "*" not in key:
            nested = self._options_for_pattern(f"*/{key}", include_basename=True)
            if nested:
                return nested
        if "*" in key:
            return self._options_for_pattern(key, include_basename=False)
        return []

    def _options_for_pattern(
        self,
        pattern: str,
        include_basename: bool,
    ) -> list[WildcardOption]:
        options: list[WildcardOption] = []
        for key in sorted(self.mapping):
            if fnmatchcase(key, pattern) or (
                include_basename
                and (key == pattern[2:] or key.endswith(f"/{pattern[2:]}"))
            ):
                options.extend(self.mapping[key])
        return options
