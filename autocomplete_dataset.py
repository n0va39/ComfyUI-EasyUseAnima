from __future__ import annotations

import csv
import itertools
import re
import time
import unicodedata
from dataclasses import dataclass
from pathlib import Path

try:
    from .anima_prompt.knowledge import PACKAGE_DATA_DIR
    from .anima_prompt.models import TagSection
    from .anima_prompt.ordering import builtin_tag_section
    from .anima_prompt.parser import parse_prompt
except ImportError:
    from anima_prompt.knowledge import PACKAGE_DATA_DIR
    from anima_prompt.models import TagSection
    from anima_prompt.ordering import builtin_tag_section
    from anima_prompt.parser import parse_prompt

AUTOCOMPLETE_CSV = PACKAGE_DATA_DIR / "KR_danbooru_tags_with_description v3_modified.csv"
LOCALSMILE_AUTOCOMPLETE_CSV = PACKAGE_DATA_DIR / "danbooru_tags_classified.csv"

DEFAULT_AUTOCOMPLETE_SOURCE = "localsmile_kr_wiki"
AUTOCOMPLETE_SOURCES = {
    "kr_modified": {
        "label": "KR danbooru tags with description v3 modified",
        "path": AUTOCOMPLETE_CSV,
        "source": "Bundled with author permission",
    },
    "localsmile_kr_wiki": {
        "label": "Localsmile danbooru KR wiki tag search",
        "path": LOCALSMILE_AUTOCOMPLETE_CSV,
        "source": "https://github.com/Localsmile/danbooru_KR_wiki_tag_search",
    },
}

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
    "entry_map": None,
}
_COUNT_RE = re.compile(
    r"^\d+\s*(girl|girls|boy|boys|person|people|other|others|animal|animals|"
    r"female|females|male|males|child|children)s?$",
    re.IGNORECASE,
)
_WEIGHTED_TOKEN_RE = re.compile(r"^\((.*):[-+]?\d+(?:\.\d+)?\)$")
_DESCRIPTION_PREFIX_RE = re.compile(r"^\[([^\]]+)\]")
_COMMENT_RE = re.compile(r"^[ \t]*#[^\n]*", re.MULTILINE)

@dataclass(frozen=True)
class AutocompleteEntry:
    tag: str
    tag_key: str
    category: str
    count: int
    description: str
    search: str


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


def _normalize_category(value: str) -> str:
    value = str(value or "").strip()
    return _CATEGORY_NAMES.get(value, value or "general")


def _entry_from_parts(tag: str, category: str, count: str, description: str) -> AutocompleteEntry | None:
    tag = str(tag or "").strip()
    if not tag:
        return None
    category = _normalize_category(category)
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
                )
                if entry:
                    entries.append(entry)
        else:
            for row in itertools.chain((first_row,), rows):
                if len(row) < 4:
                    continue
                entry = _entry_from_parts(row[0], row[1], row[2], row[3])
                if entry:
                    entries.append(entry)
    entries.sort(key=lambda entry: entry.count, reverse=True)
    return tuple(entries)


def _entries(path: Path = AUTOCOMPLETE_CSV) -> tuple[AutocompleteEntry, ...]:
    mtime = path.stat().st_mtime_ns if path.is_file() else 0
    if (
        _CACHE["entries"] is None
        or _CACHE["path"] != str(path)
        or _CACHE["mtime"] != mtime
    ):
        _CACHE["path"] = str(path)
        _CACHE["mtime"] = mtime
        _CACHE["entries"] = _load_entries(path)
        _CACHE["entry_map"] = None
    return _CACHE["entries"] or ()


def _entry_map(path: Path = AUTOCOMPLETE_CSV) -> dict[str, AutocompleteEntry]:
    _entries(path)
    if _CACHE["entry_map"] is None:
        _CACHE["entry_map"] = {
            _normalize(entry.tag): entry
            for entry in (_CACHE["entries"] or [])
        }
    return _CACHE["entry_map"] or {}


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


def _classification_tokens(token: str) -> list[tuple[str, bool, bool]]:
    token = _INLINE_SPACE_RE.sub(" ", str(token).strip(" ,\n\t"))
    if not token:
        return []
    if _has_unbalanced_parentheses(token):
        return [(token, False, True)]
    weighted = _WEIGHTED_TOKEN_RE.match(token)
    if not weighted:
        return [(token, False, False)]
    inner = weighted.group(1).strip(" ,\n\t")
    parts = [
        _INLINE_SPACE_RE.sub(" ", part.strip(" ,\n\t"))
        for part in parse_prompt(inner, profile="prompt").tokens
    ]
    return [(part, True, False) for part in parts if part]


def _token_section(token: str, entry: AutocompleteEntry | None) -> tuple[str, str]:
    base = _token_base(token)
    is_artist_request = _is_artist_request(token)
    if _COUNT_RE.match(_normalize(base)):
        return ("count", "인원수")
    if is_artist_request:
        if entry and entry.category == "artist":
            return ("artist", "작가")
        if entry:
            labels = {
                "character": "캐릭터",
                "copyright": "작품",
                "meta": "메타",
                "general": "학습 태그",
            }
            return (entry.category, labels.get(entry.category, entry.category or "태그"))
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
    entries = _entry_map(path)
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
            for token in parse_prompt(normalized, profile="prompt").tokens:
                tokens.extend(
                    (classified_token, weighted, syntax_error, False)
                    for classified_token, weighted, syntax_error in _classification_tokens(token)
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
        "status": autocomplete_status(path),
    }


def autocomplete_status(path: Path = AUTOCOMPLETE_CSV) -> dict:
    exists = path.is_file()
    entries = _entries(path) if exists else []
    return {
        "path": str(path),
        "exists": exists,
        "count": len(entries),
        "mtime": path.stat().st_mtime if exists else 0,
    }


def search_autocomplete(
    query: str,
    limit: int = 20,
    path: Path = AUTOCOMPLETE_CSV,
    category: str | None = None,
) -> dict:
    started = time.perf_counter()
    normalized_query = _normalize(query)
    category = str(category or "").strip()
    categories = {item.strip() for item in category.split(",") if item.strip()}
    if not normalized_query:
        return {
            "query": query,
            "results": [],
            "status": autocomplete_status(path),
            "elapsed_ms": 0,
        }

    results: list[tuple[int, AutocompleteEntry]] = []
    for entry in _entries(path):
        if categories and entry.category not in categories:
            continue
        tag_key = entry.tag_key
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
        "category": category,
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
