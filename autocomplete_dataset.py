from __future__ import annotations

import csv
import heapq
import itertools
import re
import stat
import threading
import time
import unicodedata
from concurrent.futures import Future
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Mapping

try:
    from .easyuse_anima.autocomplete.index import (
        AutocompleteIndexDiagnostics,
        AutocompleteIndexSource,
        AutocompleteIndexUnavailable,
        search_autocomplete_index,
    )
    from .anima_prompt.knowledge import PACKAGE_DATA_DIR
    from .anima_prompt.models import TagSection
    from .anima_prompt.ordering import builtin_tag_section
    from .anima_prompt.parser import parse_prompt
    from .easyuse_anima.translation.markers import (
        iter_prompt_translation_markers,
    )
    from .easyuse_anima.infrastructure.filesystem.paths import (
        PACKAGE_DATA_DIR as STORAGE_PACKAGE_DATA_DIR,
    )
    from .easyuse_anima.infrastructure.filesystem.paths import USER_DATA_DIR
except ImportError:
    from easyuse_anima.autocomplete.index import (
        AutocompleteIndexDiagnostics,
        AutocompleteIndexSource,
        AutocompleteIndexUnavailable,
        search_autocomplete_index,
    )
    from anima_prompt.knowledge import PACKAGE_DATA_DIR
    from anima_prompt.models import TagSection
    from anima_prompt.ordering import builtin_tag_section
    from anima_prompt.parser import parse_prompt
    from easyuse_anima.translation.markers import (
        iter_prompt_translation_markers,
    )
    from easyuse_anima.infrastructure.filesystem.paths import (
        PACKAGE_DATA_DIR as STORAGE_PACKAGE_DATA_DIR,
    )
    from easyuse_anima.infrastructure.filesystem.paths import USER_DATA_DIR

DBR_TAG_ARCHIVE_SOURCE = "https://github.com/DraconicDragon/dbr-e621-lists-archive"
DBR_TAG_ARCHIVE_LICENSE = "Unlicense"
DBR_DANBOORU_AUTOCOMPLETE_CSV = PACKAGE_DATA_DIR / "danbooru_2025-09-01.csv"
DBR_E621_AUTOCOMPLETE_CSV = PACKAGE_DATA_DIR / "e621_2025-09-01.csv"
DBR_MERGED_AUTOCOMPLETE_CSV = PACKAGE_DATA_DIR / "danbooru_e621_merged_2025-09-01.csv"
LOCALSMILE_AUTOCOMPLETE_CSV = PACKAGE_DATA_DIR / "danbooru_tags_classified.csv"
AUTOCOMPLETE_CSV = DBR_DANBOORU_AUTOCOMPLETE_CSV

DEFAULT_AUTOCOMPLETE_SOURCE = "dbr_danbooru_2025_09_01"
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
_AUTOCOMPLETE_CACHE_SCHEMA_VERSION = 1
_AUTOCOMPLETE_CACHE_LOAD_ATTEMPTS = 4
_MISSING_FILE_STAT = -1


def _default_autocomplete_index_dir() -> Path | None:
    user_data_dir = Path(USER_DATA_DIR).resolve(strict=False)
    package_data_dir = Path(STORAGE_PACKAGE_DATA_DIR).resolve(strict=False)
    if user_data_dir == package_data_dir:
        # Standalone imports do not have a ComfyUI-owned writable user-data
        # boundary. Keep the source/package tree immutable in that case.
        return None
    return user_data_dir / "autocomplete_index"


_AUTOCOMPLETE_INDEX_DIR = _default_autocomplete_index_dir()
_COUNT_RE = re.compile(
    r"^\d+\s*(girl|girls|boy|boys|person|people|other|others|animal|animals|"
    r"female|females|male|males|child|children)s?$",
    re.IGNORECASE,
)
_WEIGHT_NUMBER_RE = re.compile(r"^[+-]?(?:\d+(?:\.\d*)?|\.\d+)$")
_WEIGHTED_TOKEN_RE = re.compile(r"^\((.*):[+-]?(?:\d+(?:\.\d*)?|\.\d+)\)$")
_WILDCARD_TOKEN_RE = re.compile(r"^(?:\d+#)?__[\w.\-+/*\\]+__$", re.IGNORECASE)
_WILDCARD_SYNTAX_RE = re.compile(r"(?:\d+#)?__[\w.\-+/*\\]+?__", re.IGNORECASE)
_DYNAMIC_PROMPT_TOKEN_RE = re.compile(r"^(?<!\\)\{(?:[^{}]|(?<=\\)[{}])*?(?<!\\)\}$")
_DYNAMIC_PROMPT_SYNTAX_RE = re.compile(r"(?<!\\)\{(?:[^{}]|(?<=\\)[{}])*?(?<!\\)\}")
_DESCRIPTION_PREFIX_RE = re.compile(r"^\[([^\]]+)\]")
_COMMENT_RE = re.compile(r"^[ \t]*#[^\n]*", re.MULTILINE)

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


_CACHE_LOCK = threading.Lock()
_CACHE: dict[str, _AutocompleteSnapshot] = {}
_INFLIGHT: dict[_AutocompleteCacheKey, Future[_AutocompleteSnapshot]] = {}


def resolve_autocomplete_source(source: str | None = None) -> tuple[str, Path]:
    key = str(source or "").strip() or DEFAULT_AUTOCOMPLETE_SOURCE
    if key not in AUTOCOMPLETE_SOURCES:
        key = DEFAULT_AUTOCOMPLETE_SOURCE
    return key, Path(AUTOCOMPLETE_SOURCES[key]["path"])


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
    with _CACHE_LOCK:
        cached = _CACHE.get(key.resolved_path)
        if cached is not None and cached.key == key:
            return cached
        future = _INFLIGHT.get(key)
        is_loader = future is None
        if future is None:
            future = Future()
            _INFLIGHT[key] = future

    if not is_loader:
        return _await_snapshot(future)

    try:
        try:
            snapshot = _build_snapshot(key)
        except Exception as load_error:
            current_key = _cache_key_from_resolved_path(Path(key.resolved_path))
            if current_key != key:
                raise _AutocompleteSourceChanged(key.resolved_path) from load_error
            raise
        current_key = _cache_key_from_resolved_path(Path(key.resolved_path))
        if current_key != key:
            raise _AutocompleteSourceChanged(key.resolved_path)
        with _CACHE_LOCK:
            current_cached = _CACHE.get(key.resolved_path)
            if current_cached is not cached and (
                current_cached is None or current_cached.key != key
            ):
                raise _AutocompleteSourceChanged(key.resolved_path)
            _CACHE[key.resolved_path] = snapshot
            _INFLIGHT.pop(key, None)
    except BaseException as error:
        with _CACHE_LOCK:
            if _INFLIGHT.get(key) is future:
                _INFLIGHT.pop(key, None)
        future.set_exception(error)
        raise

    future.set_result(snapshot)
    return snapshot


def _snapshot(path: Path = AUTOCOMPLETE_CSV) -> _AutocompleteSnapshot:
    for _attempt in range(_AUTOCOMPLETE_CACHE_LOAD_ATTEMPTS):
        key = _cache_key(path)
        try:
            return _snapshot_for_key(key)
        except _AutocompleteSourceChanged:
            continue
    resolved_path = Path(path).resolve(strict=False)
    raise RuntimeError(
        f"Autocomplete dataset changed repeatedly while loading: {resolved_path}"
    ) from None


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
    with _CACHE_LOCK:
        snapshot = _CACHE.get(key.resolved_path)
        if snapshot is not None and snapshot.key == key:
            return snapshot
    return None


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


def _token_base(token: str) -> str:
    token = str(token or "").strip()
    weighted = _WEIGHTED_TOKEN_RE.match(token)
    if weighted:
        token = weighted.group(1).strip(" ,\n\t")
    token = token.rstrip(":").strip()
    token = re.sub(r"\\(.)", r"\1", token)
    if token.startswith("@"):
        return token[1:].strip()
    return token


def _is_artist_request(token: str) -> bool:
    token = str(token or "").strip()
    if token.startswith("@"):
        return True
    weighted = _WEIGHTED_TOKEN_RE.match(token)
    return bool(weighted and weighted.group(1).strip().startswith("@"))


def _is_weighted_token(token: str) -> bool:
    return bool(_WEIGHTED_TOKEN_RE.match(str(token or "").strip()))


def _is_escaped(value: str, index: int) -> bool:
    slash_count = 0
    cursor = index - 1
    while cursor >= 0 and value[cursor] == "\\":
        slash_count += 1
        cursor -= 1
    return slash_count % 2 == 1


def _has_unbalanced_parentheses(token: str) -> bool:
    depth = 0
    value = str(token or "")
    for index, char in enumerate(value):
        if char == "(" and not _is_escaped(value, index):
            depth += 1
        elif char == ")" and not _is_escaped(value, index):
            if depth <= 0:
                return True
            depth -= 1
    return depth != 0


def _top_level_colon(value: str) -> int:
    depth = 0
    colon = -1
    escaped = False
    for index, char in enumerate(str(value or "")):
        if escaped:
            escaped = False
            continue
        if char == "\\":
            escaped = True
            continue
        if char == "(":
            depth += 1
            continue
        if char == ")" and depth > 0:
            depth -= 1
            continue
        if char == ":" and depth == 0:
            colon = index
    return colon


def _artist_mix_group_inner(group: str) -> tuple[str, bool]:
    text = str(group or "").strip()
    if not (text.startswith("[[") and text.endswith("]]")):
        return text, True
    inner = text[2:-2].strip(" ,\n\t")
    colon = _top_level_colon(inner)
    if colon >= 0:
        weight = inner[colon + 1 :].strip()
        if not _WEIGHT_NUMBER_RE.match(weight):
            return group, True
        inner = inner[:colon].strip(" ,\n\t")
    return inner, False


def _has_invalid_weight_syntax(token: str) -> bool:
    text = str(token or "").strip()
    if not (text.startswith("(") and text.endswith(")")):
        return False
    inner = text[1:-1].strip()
    colon = _top_level_colon(inner)
    if colon < 0:
        return False
    weight = inner[colon + 1 :].strip()
    return not bool(weight and _WEIGHT_NUMBER_RE.match(weight))


def _plain_parenthesized_inner(token: str) -> str | None:
    text = str(token or "").strip()
    if not (text.startswith("(") and text.endswith(")")):
        return None
    inner = text[1:-1].strip(" ,\n\t")
    if not inner or _top_level_colon(inner) >= 0:
        return None
    return inner


def _classification_tokens(token: str) -> list[tuple[str, bool, bool]]:
    token = _INLINE_SPACE_RE.sub(" ", str(token).strip(" ,\n\t"))
    if not token:
        return []
    if _has_unbalanced_parentheses(token):
        return [(token, False, True)]
    if _has_invalid_weight_syntax(token):
        return [(token, False, True)]
    plain_inner = _plain_parenthesized_inner(token)
    if plain_inner is not None:
        parts = [
            _INLINE_SPACE_RE.sub(" ", part.strip(" ,\n\t"))
            for part in parse_prompt(plain_inner, profile="prompt").tokens
        ]
        return [(part, False, False) for part in parts if part]
    weighted = _WEIGHTED_TOKEN_RE.match(token)
    if not weighted:
        return [(token, False, False)]
    inner = weighted.group(1).strip(" ,\n\t")
    parts = [
        _INLINE_SPACE_RE.sub(" ", part.strip(" ,\n\t"))
        for part in parse_prompt(inner, profile="prompt").tokens
    ]
    return [(part, True, False) for part in parts if part]


def _classification_tokens_from_prompt_text(text: str) -> list[tuple[str, bool, bool]]:
    result: list[tuple[str, bool, bool]] = []
    for token in parse_prompt(text, profile="prompt").tokens:
        result.extend(_classification_tokens(token))
    return result


def _classification_tokens_from_artist_group(group: str) -> list[tuple[str, bool, bool]]:
    inner, syntax_error = _artist_mix_group_inner(group)
    if syntax_error:
        return [(str(group or "").strip(), False, True)]
    return _classification_tokens_from_prompt_text(inner)


def _next_prompt_syntax_range(value: str, cursor: int) -> tuple[str, int, int] | None:
    ranges: list[tuple[str, int, int]] = []
    artist_start = value.find("[[", cursor)
    if artist_start >= 0:
        artist_end = value.find("]]", artist_start + 2)
        ranges.append(("artist_group", artist_start, artist_end + 2 if artist_end >= 0 else len(value)))
    for start, end, _segment in iter_prompt_translation_markers(value[cursor:]):
        ranges.append(("translation", cursor + start, cursor + end))
        break
    for kind, pattern in (
        ("dynamic", _DYNAMIC_PROMPT_SYNTAX_RE),
        ("wildcard", _WILDCARD_SYNTAX_RE),
    ):
        match = pattern.search(value, cursor)
        if match:
            ranges.append((kind, match.start(), match.end()))
    if not ranges:
        return None
    return min(ranges, key=lambda item: item[1])


def _classification_tokens_from_chunk(text: str) -> list[tuple[str, bool, bool]]:
    result: list[tuple[str, bool, bool]] = []
    value = str(text or "")
    cursor = 0
    while cursor < len(value):
        syntax_range = _next_prompt_syntax_range(value, cursor)
        if not syntax_range:
            result.extend(_classification_tokens_from_prompt_text(value[cursor:]))
            break
        kind, start, end = syntax_range
        if start > cursor:
            result.extend(_classification_tokens_from_prompt_text(value[cursor:start]))
        if kind == "artist_group" and not value[start:end].endswith("]]"):
            tail = value[start:].strip(" ,\n\t")
            if tail:
                result.append((tail, False, True))
            break
        if kind == "artist_group":
            result.extend(_classification_tokens_from_artist_group(value[start:end]))
        elif kind == "translation":
            token = value[start:end].strip(" ,\n\t")
            if token:
                result.append((token, False, False))
        else:
            token = value[start:end].strip(" ,\n\t")
            if token:
                result.append((token, False, False))
        cursor = end
    return result


def _token_section(token: str, entry: AutocompleteEntry | None) -> tuple[str, str]:
    marker = str(token or "").strip()
    if marker.startswith("%{") and marker.endswith("}"):
        return ("translation", "번역")
    base = _token_base(token)
    is_artist_request = _is_artist_request(token)
    if _WILDCARD_TOKEN_RE.match(base) or _DYNAMIC_PROMPT_TOKEN_RE.match(base):
        return ("wildcard", "와일드카드")
    if _COUNT_RE.match(_normalize(base)):
        return ("count", "인원수")
    if is_artist_request:
        if entry:
            return ("artist", "작가")
        return ("artist_unknown", "미등록 작가")
    builtin_section = builtin_tag_section(base)
    if builtin_section is TagSection.QUALITY:
        return ("quality", "품질")
    if builtin_section is TagSection.META:
        return ("meta", "메타")
    if builtin_section is TagSection.YEAR:
        return ("year", "연도")
    if builtin_section is TagSection.SAFETY:
        return ("safety", "등급")
    if builtin_section is TagSection.COUNT:
        return ("count", "인원수")
    if entry:
        labels = {
            "quality": "품질",
            "character": "캐릭터",
            "artist": "작가",
            "copyright": "작품",
            "meta": "메타",
            "general": "학습 태그",
        }
        return (entry.category, labels.get(entry.category, entry.category or "태그"))
    if len(base) >= 32 or re.search(r"[.!?]", base):
        return ("natural", "자연어")
    return ("unknown", "미확인")


def classify_prompt_text(text: str, limit: int = 240, path: Path = AUTOCOMPLETE_CSV) -> dict:
    snapshot = _snapshot(path)
    entries = snapshot.entry_map
    tokens: list[tuple[str, bool, bool, bool]] = []

    last_idx = 0
    chunks = []
    for match in _COMMENT_RE.finditer(text or ""):
        start, end = match.span()
        if start > last_idx:
            chunks.append((text[last_idx:start], False))
        chunks.append((text[start:end], True))
        last_idx = end
    if last_idx < len(text or ""):
        chunks.append((text[last_idx:], False))

    for chunk_text, is_comment in chunks:
        if is_comment:
            tokens.append((chunk_text, False, False, True))
        else:
            normalized = str(chunk_text).replace("\r\n", "\n").replace("\r", "\n")
            normalized = normalized.replace("，", ",").replace("\n", ",")
            tokens.extend(
                (classified_token, weighted, syntax_error, False)
                for classified_token, weighted, syntax_error in _classification_tokens_from_chunk(normalized)
            )

        max_limit = max(1, min(limit, 500))
        if len(tokens) >= max_limit:
            tokens = tokens[:max_limit]
            break

    classified = []
    for token, weighted, syntax_error, is_comment in tokens:
        if syntax_error:
            classified.append({
                "token": token,
                "base": token,
                "section": "syntax",
                "label": "문법 오류",
                "learned": False,
                "weighted": False,
                "count": 0,
                "description": "Unbalanced prompt parentheses",
            })
            continue
        if is_comment:
            classified.append({
                "token": token,
                "base": token.strip(),
                "section": "comment",
                "label": "주석",
                "learned": False,
                "weighted": False,
                "count": 0,
                "description": "",
            })
            continue
        base = _token_base(token)
        key = _normalize(base)
        entry = entries.get(key)
        section, label = _token_section(token, entry)
        classified.append({
            "token": token,
            "base": base,
            "section": section,
            "label": label,
            "learned": entry is not None,
            "weighted": weighted or _is_weighted_token(token),
            "count": entry.count if entry else 0,
            "description": entry.description if entry else "",
        })

    return {
        "tokens": classified,
        "status": _snapshot_status(snapshot, path),
    }


def autocomplete_status(path: Path = AUTOCOMPLETE_CSV) -> dict:
    key = _cache_key(path)
    if key.mtime_ns == _MISSING_FILE_STAT:
        return _status_from_key(key, path, 0)

    cached = _cached_snapshot_for_key(key)
    if cached is not None:
        return _snapshot_status(cached, path)

    manifest_count = _builtin_manifest_entry_count(key)
    if manifest_count is not None:
        return _status_from_key(key, path, manifest_count)

    # Public helper callers may provide arbitrary paths. Preserve their exact
    # count semantics when no verified built-in manifest applies.
    return _snapshot_status(_snapshot(path), path)


def _autocomplete_match_score(
    entry: AutocompleteEntry,
    normalized_query: str,
) -> int | None:
    if entry.tag_key == normalized_query:
        return 0
    if entry.tag_key.startswith(normalized_query):
        return 1
    if normalized_query in entry.tag_key:
        return 2
    if normalized_query in entry.search:
        return 3
    return None


def _top_autocomplete_matches(
    entries: tuple[AutocompleteEntry, ...],
    normalized_query: str,
    categories: set[str],
    limit: int,
) -> list[tuple[int, AutocompleteEntry]]:
    def matches():
        for entry in entries:
            if categories and entry.category not in categories:
                continue
            score = _autocomplete_match_score(entry, normalized_query)
            if score is not None:
                yield (score, entry)

    return heapq.nsmallest(
        limit,
        matches(),
        key=lambda item: (item[0], -item[1].count, item[1].tag),
    )


def _index_source(key: _AutocompleteCacheKey) -> AutocompleteIndexSource:
    return AutocompleteIndexSource(
        resolved_path=key.resolved_path,
        revision=f"{key.schema_version}:{key.mtime_ns}:{key.size}",
    )


def _validate_index_source(key: _AutocompleteCacheKey) -> None:
    if _cache_key_from_resolved_path(Path(key.resolved_path)) != key:
        raise _AutocompleteSourceChanged(key.resolved_path)


def _fallback_index_diagnostics(
    key: _AutocompleteCacheKey,
    snapshot: _AutocompleteSnapshot,
    reason: str,
) -> AutocompleteIndexDiagnostics:
    return AutocompleteIndexDiagnostics(
        outcome="fallback",
        reason=reason,
        backend="python_snapshot",
        source_revision=_index_source(key).revision,
        entry_count=len(snapshot.entries),
        index_path=None,
    )


def _search_autocomplete_with_diagnostics(
    query: str,
    limit: int = 20,
    path: Path = AUTOCOMPLETE_CSV,
    category: str | None = None,
) -> tuple[dict, AutocompleteIndexDiagnostics]:
    started = time.perf_counter()
    effective_limit = max(1, min(limit, 100))
    normalized_query = _normalize(query)
    category = str(category or "").strip()
    categories = {item.strip() for item in category.split(",") if item.strip()}

    for _attempt in range(_AUTOCOMPLETE_CACHE_LOAD_ATTEMPTS):
        key = _cache_key(path)
        if key.mtime_ns == _MISSING_FILE_STAT:
            snapshot = _snapshot(path)
            key = snapshot.key
            if key.mtime_ns != _MISSING_FILE_STAT:
                continue
            diagnostics = _fallback_index_diagnostics(key, snapshot, "missing_source")
            limited: list[tuple[int, AutocompleteEntry]] = []
            entry_count = 0
            indexed_entries = None
            break

        try:
            indexed = search_autocomplete_index(
                root=_AUTOCOMPLETE_INDEX_DIR,
                source=_index_source(key),
                normalized_query=normalized_query,
                categories=categories,
                limit=effective_limit,
                load_entries=lambda: _load_entries(Path(key.resolved_path)),
                validate_source=lambda: _validate_index_source(key),
            )
        except _AutocompleteSourceChanged:
            continue
        except AutocompleteIndexUnavailable as error:
            snapshot = _snapshot(path)
            key = snapshot.key
            diagnostics = _fallback_index_diagnostics(key, snapshot, error.reason)
            limited = _top_autocomplete_matches(
                snapshot.entries,
                normalized_query,
                categories,
                effective_limit,
            )
            entry_count = len(snapshot.entries)
            indexed_entries = None
        else:
            try:
                _validate_index_source(key)
            except _AutocompleteSourceChanged:
                continue
            diagnostics = indexed.diagnostics
            limited = []
            entry_count = indexed.diagnostics.entry_count
            indexed_entries = indexed.entries
        break
    else:
        resolved_path = Path(path).resolve(strict=False)
        raise RuntimeError(
            f"Autocomplete dataset changed repeatedly while loading: {resolved_path}"
        ) from None

    if indexed_entries is None:
        result_entries = [entry for _, entry in limited]
    else:
        result_entries = indexed_entries

    payload = {
        "query": query,
        "category": category,
        "results": [
            {
                "tag": entry.tag,
                "category": entry.category,
                "count": entry.count,
                "description": entry.description,
            }
            for entry in result_entries
        ],
        "status": _status_from_key(key, path, entry_count),
        "elapsed_ms": round((time.perf_counter() - started) * 1000, 2),
    }
    return payload, diagnostics


def search_autocomplete(
    query: str,
    limit: int = 20,
    path: Path = AUTOCOMPLETE_CSV,
    category: str | None = None,
) -> dict:
    normalized_query = _normalize(query)
    if not normalized_query:
        return {
            "query": query,
            "results": [],
            "status": autocomplete_status(path),
            "elapsed_ms": 0,
        }
    payload, _diagnostics = _search_autocomplete_with_diagnostics(
        query,
        limit=limit,
        path=path,
        category=category,
    )
    return payload
