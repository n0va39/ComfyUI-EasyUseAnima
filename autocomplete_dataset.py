from __future__ import annotations

import csv
import re
import time
import unicodedata
from dataclasses import dataclass
from pathlib import Path

try:
    from .anima_prompt.knowledge import PACKAGE_DATA_DIR
except ImportError:
    from anima_prompt.knowledge import PACKAGE_DATA_DIR

AUTOCOMPLETE_CSV = PACKAGE_DATA_DIR / "KR_danbooru_tags_with_description v3_modified.csv"

_INLINE_SPACE_RE = re.compile(r"[ \t]+")
_CATEGORY_NAMES = {
    "0": "general",
    "1": "artist",
    "3": "copyright",
    "4": "character",
    "5": "meta",
}
_CACHE = {
    "path": None,
    "mtime": None,
    "entries": None,
}


@dataclass(frozen=True)
class AutocompleteEntry:
    tag: str
    category: str
    count: int
    description: str
    search: str


def _normalize(value: str) -> str:
    value = unicodedata.normalize("NFKC", str(value or ""))
    value = value.replace("_", " ").casefold()
    value = _INLINE_SPACE_RE.sub(" ", value)
    return value.strip()


def _display_description(value: str, max_length: int = 160) -> str:
    value = _INLINE_SPACE_RE.sub(" ", str(value or "").strip())
    if len(value) <= max_length:
        return value
    return value[: max_length - 1].rstrip() + "..."


def _safe_count(value: str) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _load_entries(path: Path = AUTOCOMPLETE_CSV) -> list[AutocompleteEntry]:
    entries: list[AutocompleteEntry] = []
    if not path.is_file():
        return entries

    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle)
        for row in reader:
            if len(row) < 4:
                continue
            tag = row[0].strip()
            if not tag:
                continue
            category = _CATEGORY_NAMES.get(row[1].strip(), row[1].strip())
            count = _safe_count(row[2])
            description = _display_description(row[3])
            search = _normalize(" ".join((tag, description)))
            entries.append(
                AutocompleteEntry(
                    tag=tag,
                    category=category,
                    count=count,
                    description=description,
                    search=search,
                )
            )
    entries.sort(key=lambda entry: entry.count, reverse=True)
    return entries


def _entries(path: Path = AUTOCOMPLETE_CSV) -> list[AutocompleteEntry]:
    mtime = path.stat().st_mtime if path.is_file() else 0
    if (
        _CACHE["entries"] is None
        or _CACHE["path"] != str(path)
        or _CACHE["mtime"] != mtime
    ):
        _CACHE["path"] = str(path)
        _CACHE["mtime"] = mtime
        _CACHE["entries"] = _load_entries(path)
    return list(_CACHE["entries"] or [])


def autocomplete_status(path: Path = AUTOCOMPLETE_CSV) -> dict:
    exists = path.is_file()
    entries = _entries(path) if exists else []
    return {
        "path": str(path),
        "exists": exists,
        "count": len(entries),
        "mtime": path.stat().st_mtime if exists else 0,
    }


def search_autocomplete(query: str, limit: int = 20, path: Path = AUTOCOMPLETE_CSV) -> dict:
    started = time.perf_counter()
    normalized_query = _normalize(query)
    if not normalized_query:
        return {
            "query": query,
            "results": [],
            "status": autocomplete_status(path),
            "elapsed_ms": 0,
        }

    results: list[tuple[int, AutocompleteEntry]] = []
    for entry in _entries(path):
        tag_key = _normalize(entry.tag)
        if tag_key == normalized_query:
            score = 0
        elif tag_key.startswith(normalized_query):
            score = 1
        elif normalized_query in tag_key:
            score = 2
        elif normalized_query in entry.search:
            score = 3
        else:
            continue
        results.append((score, entry))
        if len(results) >= max(limit * 8, limit):
            break

    results.sort(key=lambda item: (item[0], -item[1].count, item[1].tag))
    limited = results[: max(1, min(limit, 50))]
    return {
        "query": query,
        "results": [
            {
                "tag": entry.tag,
                "category": entry.category,
                "count": entry.count,
                "description": entry.description,
            }
            for _, entry in limited
        ],
        "status": autocomplete_status(path),
        "elapsed_ms": round((time.perf_counter() - started) * 1000, 2),
    }
