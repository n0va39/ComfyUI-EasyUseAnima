"""Autocomplete source metadata, CSV snapshots, cache, and status."""

from __future__ import annotations

import csv
import itertools
import re
import stat
import threading
import unicodedata
from collections.abc import Callable, Mapping
from concurrent.futures import Future
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType

from ..infrastructure.filesystem.paths import PACKAGE_DATA_DIR

DBR_TAG_ARCHIVE_SOURCE = "https://github.com/DraconicDragon/dbr-e621-lists-archive"


DBR_TAG_ARCHIVE_LICENSE = "Unlicense"


DBR_DANBOORU_AUTOCOMPLETE_CSV = PACKAGE_DATA_DIR / "danbooru_2025-09-01.csv"


DBR_E621_AUTOCOMPLETE_CSV = PACKAGE_DATA_DIR / "e621_2025-09-01.csv"


DBR_MERGED_AUTOCOMPLETE_CSV = PACKAGE_DATA_DIR / "danbooru_e621_merged_2025-09-01.csv"


LOCALSMILE_AUTOCOMPLETE_CSV = PACKAGE_DATA_DIR / "danbooru_tags_classified.csv"


AUTOCOMPLETE_CSV = DBR_DANBOORU_AUTOCOMPLETE_CSV


DEFAULT_AUTOCOMPLETE_SOURCE = "dbr_danbooru_2025_09_01"
_KOREAN_AUTOCOMPLETE_SOURCE = "localsmile_kr_wiki"


AUTOCOMPLETE_SOURCES = {
    "dbr_danbooru_2025_09_01": {
        "label": "Danbooru 2025-09-01 (recommended)",
        "path": DBR_DANBOORU_AUTOCOMPLETE_CSV,
        "entry_count": 183174,
        "source": DBR_TAG_ARCHIVE_SOURCE,
        "license": DBR_TAG_ARCHIVE_LICENSE,
    },
    "dbr_e621_2025_09_01": {
        "label": "e621 2025-09-01",
        "path": DBR_E621_AUTOCOMPLETE_CSV,
        "entry_count": 129525,
        "source": DBR_TAG_ARCHIVE_SOURCE,
        "license": DBR_TAG_ARCHIVE_LICENSE,
    },
    "dbr_danbooru_e621_merged_2025_09_01": {
        "label": "Danbooru + e621 merged 2025-09-01 (merge-risk)",
        "path": DBR_MERGED_AUTOCOMPLETE_CSV,
        "entry_count": 295050,
        "source": DBR_TAG_ARCHIVE_SOURCE,
        "license": DBR_TAG_ARCHIVE_LICENSE,
    },
    "localsmile_kr_wiki": {
        "label": "Localsmile Danbooru KR wiki tag search (Korean)",
        "path": LOCALSMILE_AUTOCOMPLETE_CSV,
        "entry_count": 114092,
        "source": "https://github.com/Localsmile/danbooru_KR_wiki_tag_search",
    },
}


_INLINE_SPACE_RE = re.compile(r"[ \t]+")


_DANBOORU_CATEGORY_NAMES = {
    "0": "general",
    "1": "artist",
    "3": "copyright",
    "4": "character",
    "5": "meta",
}


_E621_CATEGORY_NAMES = {
    "0": "general",
    "1": "artist",
    "3": "copyright",
    "4": "character",
    "5": "general",
    "7": "meta",
    "8": "general",
}


_MERGED_E621_CATEGORY_NAMES = {
    "7": "general",
    "8": "artist",
    "10": "copyright",
    "11": "character",
    "12": "general",
    "14": "meta",
    "15": "general",
}
_DESCRIPTION_PREFIX_RE = re.compile(r"^\[([^\]]+)\]")


_AUTOCOMPLETE_CACHE_SCHEMA_VERSION = 1


_AUTOCOMPLETE_CACHE_LOAD_ATTEMPTS = 4


_MISSING_FILE_STAT = -1


@dataclass(frozen=True, slots=True)
class AutocompleteEntry:
    tag: str
    tag_key: str
    category: str
    count: int
    description: str
    search: str


@dataclass(frozen=True, slots=True)
class _AutocompleteCacheKey:
    resolved_path: str
    mtime_ns: int
    size: int
    schema_version: int


@dataclass(frozen=True, slots=True)
class _AutocompleteSnapshot:
    key: _AutocompleteCacheKey
    entries: tuple[AutocompleteEntry, ...]
    entry_map: Mapping[str, AutocompleteEntry]


class _AutocompleteSourceChanged(RuntimeError):
    pass


class _AutocompleteSnapshotStore:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._cache: dict[str, _AutocompleteSnapshot] = {}
        self._inflight: dict[
            _AutocompleteCacheKey,
            Future[_AutocompleteSnapshot],
        ] = {}

    def clear(self) -> None:
        with self._lock:
            self._cache.clear()

    def cached_snapshot_for_key(
        self,
        key: _AutocompleteCacheKey,
    ) -> _AutocompleteSnapshot | None:
        with self._lock:
            snapshot = self._cache.get(key.resolved_path)
            if snapshot is not None and snapshot.key == key:
                return snapshot
        return None

    def snapshot_for_key(
        self,
        key: _AutocompleteCacheKey,
    ) -> _AutocompleteSnapshot:
        with self._lock:
            cached = self._cache.get(key.resolved_path)
            if cached is not None and cached.key == key:
                return cached
            future = self._inflight.get(key)
            is_loader = future is None
            if future is None:
                future = Future()
                self._inflight[key] = future

        if not is_loader:
            return _await_snapshot(future)

        try:
            try:
                snapshot = _build_snapshot(key)
            except Exception as load_error:
                current_key = _cache_key_from_resolved_path(
                    Path(key.resolved_path)
                )
                if current_key != key:
                    raise _AutocompleteSourceChanged(
                        key.resolved_path
                    ) from load_error
                raise
            current_key = _cache_key_from_resolved_path(
                Path(key.resolved_path)
            )
            if current_key != key:
                raise _AutocompleteSourceChanged(key.resolved_path)
            with self._lock:
                current_cached = self._cache.get(key.resolved_path)
                if current_cached is not cached and (
                    current_cached is not None and current_cached.key != key
                ):
                    raise _AutocompleteSourceChanged(key.resolved_path)
                self._cache[key.resolved_path] = snapshot
                self._inflight.pop(key, None)
        except BaseException as error:
            with self._lock:
                if self._inflight.get(key) is future:
                    self._inflight.pop(key, None)
            future.set_exception(error)
            raise

        future.set_result(snapshot)
        return snapshot


_DEFAULT_AUTOCOMPLETE_SNAPSHOTS = _AutocompleteSnapshotStore()


def resolve_autocomplete_source(source: str | None = None) -> tuple[str, Path]:
    key = str(source or "").strip() or DEFAULT_AUTOCOMPLETE_SOURCE
    if key not in AUTOCOMPLETE_SOURCES:
        key = DEFAULT_AUTOCOMPLETE_SOURCE
    path = Path(AUTOCOMPLETE_SOURCES[key]["path"])
    if key == _KOREAN_AUTOCOMPLETE_SOURCE and not path.is_file():
        key = DEFAULT_AUTOCOMPLETE_SOURCE
        path = Path(AUTOCOMPLETE_SOURCES[key]["path"])
    return key, path


def available_autocomplete_sources(selected: str | None = None) -> list[dict]:
    selected_key, _ = resolve_autocomplete_source(selected)
    sources = []
    for key, data in AUTOCOMPLETE_SOURCES.items():
        path = Path(data["path"])
        sources.append(
            {
                "key": key,
                "label": data["label"],
                "source": data.get("source", ""),
                "license": data.get("license", ""),
                "path": str(path),
                "exists": path.is_file(),
                "selected": key == selected_key,
            }
        )
    return sources


def _normalize(value: str) -> str:
    value = unicodedata.normalize("NFKC", str(value or ""))
    value = re.sub(r"\\(.)", r"\1", value)
    value = value.replace("_", " ").casefold()
    value = _INLINE_SPACE_RE.sub(" ", value)
    return value.strip()


def _display_description(value: str, max_length: int = 160) -> str:
    value = _INLINE_SPACE_RE.sub(" ", str(value or "").strip())
    if len(value) <= max_length:
        return value
    return value[: max_length - 1].rstrip() + "..."


def _category_from_description(category: str, description: str) -> str:
    if category != "general":
        return category
    match = _DESCRIPTION_PREFIX_RE.match(description)
    if not match:
        return category
    prefix = match.group(1)
    if "캐릭터" in prefix:
        return "character"
    if "저작권" in prefix or "작품" in prefix or "시리즈" in prefix:
        return "copyright"
    if "작가" in prefix or "아티스트" in prefix:
        return "artist"
    if "메타" in prefix:
        return "meta"
    return category


def _safe_count(value: str) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _source_kind_from_path(path: Path) -> str:
    filename = path.name.casefold()
    if filename.startswith("e621_"):
        return "e621"
    if "e621_merged" in filename:
        return "merged"
    return "danbooru"


def _normalize_category(value: str, source_kind: str = "danbooru") -> str:
    value = str(value or "").strip()
    if source_kind == "e621":
        return _E621_CATEGORY_NAMES.get(value, "general")
    if source_kind == "merged":
        return (
            _DANBOORU_CATEGORY_NAMES.get(value)
            or _MERGED_E621_CATEGORY_NAMES.get(value)
            or "general"
        )
    return _DANBOORU_CATEGORY_NAMES.get(value, value or "general")


def _entry_from_parts(
    tag: str,
    category: str,
    count: str,
    description: str,
    source_kind: str = "danbooru",
) -> AutocompleteEntry | None:
    tag = str(tag or "").strip()
    if not tag:
        return None
    category = _normalize_category(category, source_kind)
    count_value = _safe_count(count)
    description = _display_description(description)
    category = _category_from_description(category, description)
    search = _normalize(" ".join((tag, description)))
    tag_key = _normalize(tag)
    return AutocompleteEntry(
        tag=tag,
        tag_key=tag_key,
        category=category,
        count=count_value,
        description=description,
        search=search,
    )


def _looks_like_header(row: list[str]) -> bool:
    normalized = {str(column or "").strip().casefold() for column in row}
    return bool({"name", "tag", "category"} & normalized) and (
        "category" in normalized or "post_count" in normalized
    )


def _load_entries(path: Path = AUTOCOMPLETE_CSV) -> tuple[AutocompleteEntry, ...]:
    entries: list[AutocompleteEntry] = []
    if not path.is_file():
        return ()
    source_kind = _source_kind_from_path(path)

    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle)
        rows = iter(reader)
        first_row = next(rows, None)
        if first_row is None:
            return ()

        if _looks_like_header(first_row):
            fieldnames = [str(column or "").strip() for column in first_row]
            dict_reader = csv.DictReader(handle, fieldnames=fieldnames)
            for row in dict_reader:
                entry = _entry_from_parts(
                    row.get("name") or row.get("tag") or "",
                    row.get("category") or "",
                    row.get("post_count") or row.get("count") or "",
                    row.get("description") or row.get("wiki") or "",
                    source_kind,
                )
                if entry:
                    entries.append(entry)
        else:
            for row in itertools.chain((first_row,), rows):
                if len(row) < 4:
                    continue
                entry = _entry_from_parts(row[0], row[1], row[2], row[3], source_kind)
                if entry:
                    entries.append(entry)
    entries.sort(key=lambda entry: entry.count, reverse=True)
    return tuple(entries)


def _cache_key_from_resolved_path(path: Path) -> _AutocompleteCacheKey:
    try:
        file_stat = path.stat()
    except (FileNotFoundError, NotADirectoryError):
        mtime_ns = _MISSING_FILE_STAT
        size = _MISSING_FILE_STAT
    else:
        if stat.S_ISREG(file_stat.st_mode):
            mtime_ns = file_stat.st_mtime_ns
            size = file_stat.st_size
        else:
            mtime_ns = _MISSING_FILE_STAT
            size = _MISSING_FILE_STAT
    return _AutocompleteCacheKey(
        resolved_path=str(path),
        mtime_ns=mtime_ns,
        size=size,
        schema_version=_AUTOCOMPLETE_CACHE_SCHEMA_VERSION,
    )


def _cache_key(path: Path) -> _AutocompleteCacheKey:
    return _cache_key_from_resolved_path(Path(path).resolve(strict=False))


def _build_snapshot(key: _AutocompleteCacheKey) -> _AutocompleteSnapshot:
    if key.mtime_ns == _MISSING_FILE_STAT:
        entries: tuple[AutocompleteEntry, ...] = ()
    else:
        entries = _load_entries(Path(key.resolved_path))
    entry_map = MappingProxyType({entry.tag_key: entry for entry in entries})
    return _AutocompleteSnapshot(key=key, entries=entries, entry_map=entry_map)


def _await_snapshot(future: Future[_AutocompleteSnapshot]) -> _AutocompleteSnapshot:
    return future.result()


def _snapshot_for_key(key: _AutocompleteCacheKey) -> _AutocompleteSnapshot:
    return _DEFAULT_AUTOCOMPLETE_SNAPSHOTS.snapshot_for_key(key)


def _snapshot_with_owner(
    path: Path,
    *,
    snapshot_for_key: Callable[[_AutocompleteCacheKey], _AutocompleteSnapshot],
) -> _AutocompleteSnapshot:
    for _attempt in range(_AUTOCOMPLETE_CACHE_LOAD_ATTEMPTS):
        key = _cache_key(path)
        try:
            return snapshot_for_key(key)
        except _AutocompleteSourceChanged:
            continue
    resolved_path = Path(path).resolve(strict=False)
    raise RuntimeError(
        f"Autocomplete dataset changed repeatedly while loading: {resolved_path}"
    ) from None


def _snapshot(path: Path = AUTOCOMPLETE_CSV) -> _AutocompleteSnapshot:
    return _snapshot_with_owner(
        path,
        snapshot_for_key=_snapshot_for_key,
    )


def _entries(path: Path = AUTOCOMPLETE_CSV) -> tuple[AutocompleteEntry, ...]:
    return _snapshot(path).entries


def _entry_map(path: Path = AUTOCOMPLETE_CSV) -> Mapping[str, AutocompleteEntry]:
    return _snapshot(path).entry_map


def _status_from_key(key: _AutocompleteCacheKey, path: Path, count: int) -> dict:
    exists = key.mtime_ns != _MISSING_FILE_STAT
    return {
        "path": str(path),
        "exists": exists,
        "count": count,
        "mtime": key.mtime_ns / 1_000_000_000 if exists else 0,
    }


def _snapshot_status(snapshot: _AutocompleteSnapshot, path: Path) -> dict:
    return _status_from_key(snapshot.key, path, len(snapshot.entries))


def _cached_snapshot_for_key(
    key: _AutocompleteCacheKey,
) -> _AutocompleteSnapshot | None:
    return _DEFAULT_AUTOCOMPLETE_SNAPSHOTS.cached_snapshot_for_key(key)


def _builtin_manifest_entry_count(key: _AutocompleteCacheKey) -> int | None:
    resolved_path = Path(key.resolved_path)
    for source in AUTOCOMPLETE_SOURCES.values():
        if Path(source["path"]).resolve(strict=False) != resolved_path:
            continue
        # Built-in paths identify release-owned assets. Do not bind the fast
        # path to byte size because Git EOL conversion can vary by checkout;
        # tools/benchmark_autocomplete.py verifies parser counts before release.
        entry_count = source.get("entry_count")
        if type(entry_count) is int and entry_count >= 0:
            return entry_count
        return None
    return None


def _autocomplete_status_with_owner(
    path: Path,
    *,
    cached_snapshot_for_key: Callable[
        [_AutocompleteCacheKey],
        _AutocompleteSnapshot | None,
    ],
    snapshot: Callable[[Path], _AutocompleteSnapshot],
) -> dict:
    key = _cache_key(path)
    if key.mtime_ns == _MISSING_FILE_STAT:
        return _status_from_key(key, path, 0)

    cached = cached_snapshot_for_key(key)
    if cached is not None:
        return _snapshot_status(cached, path)

    manifest_count = _builtin_manifest_entry_count(key)
    if manifest_count is not None:
        return _status_from_key(key, path, manifest_count)

    # Public helper callers may provide arbitrary paths. Preserve their exact
    # count semantics when no verified built-in manifest applies.
    return _snapshot_status(snapshot(path), path)


def autocomplete_status(path: Path = AUTOCOMPLETE_CSV) -> dict:
    return _autocomplete_status_with_owner(
        path,
        cached_snapshot_for_key=_cached_snapshot_for_key,
        snapshot=_snapshot,
    )


__all__ = (
    "DBR_TAG_ARCHIVE_SOURCE",
    "DBR_TAG_ARCHIVE_LICENSE",
    "DBR_DANBOORU_AUTOCOMPLETE_CSV",
    "DBR_E621_AUTOCOMPLETE_CSV",
    "DBR_MERGED_AUTOCOMPLETE_CSV",
    "LOCALSMILE_AUTOCOMPLETE_CSV",
    "AUTOCOMPLETE_CSV",
    "DEFAULT_AUTOCOMPLETE_SOURCE",
    "AUTOCOMPLETE_SOURCES",
    "AutocompleteEntry",
    "resolve_autocomplete_source",
    "available_autocomplete_sources",
    "autocomplete_status",
)
