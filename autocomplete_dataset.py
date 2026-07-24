from __future__ import annotations

import re
from pathlib import Path

try:
    from .anima_prompt.models import TagSection
    from .anima_prompt.ordering import builtin_tag_section
    from .anima_prompt.parser import parse_prompt
    from .easyuse_anima.autocomplete.dataset import (
        AUTOCOMPLETE_CSV,
        AUTOCOMPLETE_SOURCES,
        DBR_DANBOORU_AUTOCOMPLETE_CSV,
        DBR_E621_AUTOCOMPLETE_CSV,
        DBR_MERGED_AUTOCOMPLETE_CSV,
        DBR_TAG_ARCHIVE_LICENSE,
        DBR_TAG_ARCHIVE_SOURCE,
        DEFAULT_AUTOCOMPLETE_SOURCE,
        LOCALSMILE_AUTOCOMPLETE_CSV,
        AutocompleteEntry,
        _INLINE_SPACE_RE,
        _normalize,
        _snapshot,
        _snapshot_status,
        autocomplete_status,
        available_autocomplete_sources,
        resolve_autocomplete_source,
    )
    from .easyuse_anima.autocomplete.search import search_autocomplete
    from .easyuse_anima.translation.markers import (
        iter_prompt_translation_markers,
    )
except ImportError:
    from anima_prompt.models import TagSection
    from anima_prompt.ordering import builtin_tag_section
    from anima_prompt.parser import parse_prompt
    from easyuse_anima.autocomplete.dataset import (
        AUTOCOMPLETE_CSV,
        AUTOCOMPLETE_SOURCES,
        DBR_DANBOORU_AUTOCOMPLETE_CSV,
        DBR_E621_AUTOCOMPLETE_CSV,
        DBR_MERGED_AUTOCOMPLETE_CSV,
        DBR_TAG_ARCHIVE_LICENSE,
        DBR_TAG_ARCHIVE_SOURCE,
        DEFAULT_AUTOCOMPLETE_SOURCE,
        LOCALSMILE_AUTOCOMPLETE_CSV,
        AutocompleteEntry,
        _INLINE_SPACE_RE,
        _normalize,
        _snapshot,
        _snapshot_status,
        autocomplete_status,
        available_autocomplete_sources,
        resolve_autocomplete_source,
    )
    from easyuse_anima.autocomplete.search import search_autocomplete
    from easyuse_anima.translation.markers import (
        iter_prompt_translation_markers,
    )

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


_COMMENT_RE = re.compile(r"^[ \t]*#[^\n]*", re.MULTILINE)


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


def _classification_tokens_from_artist_group(
    group: str,
) -> list[tuple[str, bool, bool]]:
    inner, syntax_error = _artist_mix_group_inner(group)
    if syntax_error:
        return [(str(group or "").strip(), False, True)]
    return _classification_tokens_from_prompt_text(inner)


def _next_prompt_syntax_range(value: str, cursor: int) -> tuple[str, int, int] | None:
    ranges: list[tuple[str, int, int]] = []
    artist_start = value.find("[[", cursor)
    if artist_start >= 0:
        artist_end = value.find("]]", artist_start + 2)
        ranges.append(
            (
                "artist_group",
                artist_start,
                artist_end + 2 if artist_end >= 0 else len(value),
            )
        )
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


def classify_prompt_text(
    text: str, limit: int = 240, path: Path = AUTOCOMPLETE_CSV
) -> dict:
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
                for classified_token, weighted, syntax_error in _classification_tokens_from_chunk(
                    normalized
                )
            )

        max_limit = max(1, min(limit, 500))
        if len(tokens) >= max_limit:
            tokens = tokens[:max_limit]
            break

    classified = []
    for token, weighted, syntax_error, is_comment in tokens:
        if syntax_error:
            classified.append(
                {
                    "token": token,
                    "base": token,
                    "section": "syntax",
                    "label": "문법 오류",
                    "learned": False,
                    "weighted": False,
                    "count": 0,
                    "description": "Unbalanced prompt parentheses",
                }
            )
            continue
        if is_comment:
            classified.append(
                {
                    "token": token,
                    "base": token.strip(),
                    "section": "comment",
                    "label": "주석",
                    "learned": False,
                    "weighted": False,
                    "count": 0,
                    "description": "",
                }
            )
            continue
        base = _token_base(token)
        key = _normalize(base)
        entry = entries.get(key)
        section, label = _token_section(token, entry)
        classified.append(
            {
                "token": token,
                "base": base,
                "section": section,
                "label": label,
                "learned": entry is not None,
                "weighted": weighted or _is_weighted_token(token),
                "count": entry.count if entry else 0,
                "description": entry.description if entry else "",
            }
        )

    return {
        "tokens": classified,
        "status": _snapshot_status(snapshot, path),
    }
