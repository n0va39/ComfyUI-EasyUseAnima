"""Private acyclic Artist Mix constants and parsing primitives."""

from __future__ import annotations

import re
from math import isfinite
from typing import Any

from ..common.values import _as_float, _as_int
from .contracts import PromptDataArtistTag
from .fields import _join_prompt_tokens

ARTIST_MIX_MODE_FROM_PROMPT_DATA = "prompt_data"
ARTIST_MIX_MODE_OFF = "off"
ARTIST_MIX_MODE_PROMPT = "prompt"
ARTIST_MIX_MODE_AVERAGE = "average"
ARTIST_MIX_MODE_DELTA_RMS = "delta_rms"
ARTIST_MIX_MODE_HYBRID = "hybrid"
ARTIST_MIX_MODE_CLUSTERED = "clustered"
ARTIST_MIX_MODE_EXACT = "exact"
ARTIST_MIX_MODE_COMPOSITE_EXACT = "composite_exact"
ARTIST_MIX_MODE_LATE_EXACT = "late_exact"
ARTIST_MIX_MODE_AVERAGE_LATE_EXACT = "average_late_exact"
ARTIST_MIX_MODE_SCHEDULED_AVERAGE = "scheduled_average"
ARTIST_MIX_MODES = (
    ARTIST_MIX_MODE_PROMPT,
    ARTIST_MIX_MODE_AVERAGE,
    ARTIST_MIX_MODE_DELTA_RMS,
    ARTIST_MIX_MODE_HYBRID,
    ARTIST_MIX_MODE_CLUSTERED,
    ARTIST_MIX_MODE_EXACT,
    ARTIST_MIX_MODE_COMPOSITE_EXACT,
    ARTIST_MIX_MODE_LATE_EXACT,
    ARTIST_MIX_MODE_AVERAGE_LATE_EXACT,
    ARTIST_MIX_MODE_SCHEDULED_AVERAGE,
)
ARTIST_MIX_DEFAULT_START_PERCENT = 0.5
ARTIST_MIX_DEFAULT_STRENGTH_SCALE = 1.0
ARTIST_MIX_DEFAULT_STYLE_GAIN = 1.35
ARTIST_MIX_DEFAULT_RMS_SCALE_CAP = 2.0
ARTIST_MIX_DEFAULT_EXACT_TOP_K = 4
ARTIST_MIX_DEFAULT_CLUSTER_COUNT = 4
ARTIST_MIX_DEFAULT_DOMINANT_ISOLATION = True
ARTIST_MIX_DEFAULT_DOMINANT_THRESHOLD = 0.25
_WEIGHTED_ARTIST_RE = re.compile(
    r"^\(\s*(?P<tag>.*?)\s*:\s*(?P<weight>[+-]?(?:\d+(?:\.\d*)?|\.\d+))\s*\)$"
)
_ARTIST_GROUP_RE = re.compile(
    r"^\s*\[\[\s*(?P<tag>.*?)(?:\s*:\s*(?P<weight>[+-]?(?:\d+(?:\.\d*)?|\.\d+)))?\s*\]\]\s*$",
    re.DOTALL,
)
_SECTION_SEPARATOR_RE = re.compile(r"^\s*-{6,}\s*$", re.MULTILINE)


def _split_artist_mix_items(text: str) -> list[str]:
    items: list[str] = []
    buffer: list[str] = []
    paren_depth = 0
    square_depth = 0
    escaped = False
    source = str(text or "")
    index = 0
    while index < len(source):
        char = source[index]
        if escaped:
            buffer.append(char)
            escaped = False
            index += 1
            continue
        if char == "\\":
            buffer.append(char)
            escaped = True
            index += 1
            continue
        if char == "(":
            paren_depth += 1
        elif char == ")" and paren_depth > 0:
            paren_depth -= 1
        elif char == "[" and index + 1 < len(source) and source[index + 1] == "[":
            square_depth += 1
            buffer.append(char)
            index += 1
            char = source[index]
        elif (
            char == "]"
            and index + 1 < len(source)
            and source[index + 1] == "]"
            and square_depth > 0
        ):
            square_depth -= 1
            buffer.append(char)
            index += 1
            char = source[index]
        if (char == "," or char == "\n") and paren_depth == 0 and square_depth == 0:
            item = "".join(buffer).strip()
            if item:
                items.append(item)
            buffer = []
            index += 1
            continue
        buffer.append(char)
        index += 1
    item = "".join(buffer).strip()
    if item:
        items.append(item)
    return items


def _split_artist_mix_blocks(text: str) -> list[str]:
    source = str(text or "").replace("\r\n", "\n").replace("\r", "\n")
    if not _SECTION_SEPARATOR_RE.search(source):
        return []
    blocks: list[str] = []
    current: list[str] = []
    for line in source.split("\n"):
        if _SECTION_SEPARATOR_RE.match(line):
            block = "\n".join(current).strip(" ,\n")
            if block:
                blocks.append(block)
            current = []
            continue
        current.append(line)
    block = "\n".join(current).strip(" ,\n")
    if block:
        blocks.append(block)
    return blocks


def _parse_artist_mix_group(raw_tag: str) -> tuple[str, float] | None:
    text = str(raw_tag or "").strip()
    match = _ARTIST_GROUP_RE.match(text)
    if not match and text.startswith("(") and text.endswith(")"):
        match = _ARTIST_GROUP_RE.match(text[1:-1].strip())
    if not match:
        return None
    tag = _join_prompt_tokens(match.group("tag") or "")
    weight = (
        _as_float(match.group("weight"), 1.0)
        if match.group("weight") is not None
        else 1.0
    )
    if not tag or not isfinite(weight) or weight <= 0:
        return None
    return tag, weight


def _artist_group_token(tag: str, weight: float) -> str:
    tag_text = _join_prompt_tokens(tag)
    if not tag_text:
        return ""
    if abs(float(weight) - 1.0) >= 0.001:
        return f"[[{tag_text}:{float(weight):g}]]"
    return f"[[{tag_text}]]"


def _join_artist_mix_source_prompts(*parts: str) -> str:
    items: list[str] = []
    for part in parts:
        for raw_item in _split_artist_mix_items(str(part or "")):
            group = _parse_artist_mix_group(raw_item)
            if group is not None:
                grouped_tag, grouped_weight = group
                token = _artist_group_token(grouped_tag, grouped_weight)
            else:
                token = _join_prompt_tokens(raw_item)
            if token:
                items.append(token)
    return ", ".join(items)


def _artist_mix_inline_prompt(text: str) -> str:
    items: list[str] = []
    for raw_item in _split_artist_mix_items(str(text or "")):
        group = _parse_artist_mix_group(raw_item)
        item = group[0] if group is not None else raw_item
        token = _join_prompt_tokens(item)
        if token:
            items.append(token)
    return ", ".join(items)


def _parse_artist_mix_entries(text: str) -> list[dict[str, Any]]:
    parsed: list[dict[str, Any]] = []
    blocks = _split_artist_mix_blocks(text)
    source_items = blocks or _split_artist_mix_items(text)
    for item in source_items:
        raw_tag = item.strip()
        weight = 1.0
        grouped = False
        group = _parse_artist_mix_group(raw_tag)
        if group is not None:
            tag, weight = group
            grouped = True
            parsed.append({"tag": tag, "weight": weight, "grouped": grouped})
            continue
        weight_source = raw_tag
        if blocks:
            block_parts = _split_artist_mix_items(raw_tag)
            if block_parts:
                weight_source = block_parts[0].strip()
        match = _WEIGHTED_ARTIST_RE.match(weight_source)
        if match:
            tag = raw_tag if blocks else match.group("tag").strip()
            weight = _as_float(match.group("weight"), 1.0)
        elif raw_tag.startswith("(") and raw_tag.endswith(")"):
            tag = raw_tag[1:-1].strip()
        else:
            tag = raw_tag
        tag = (
            _artist_mix_inline_prompt(tag)
            if _ARTIST_GROUP_RE.search(tag)
            else _join_prompt_tokens(tag)
        )
        if tag and isfinite(weight) and weight > 0:
            parsed.append({"tag": tag, "weight": weight, "grouped": grouped})
    return parsed


def _parse_artist_mix_items(text: str) -> list[tuple[str, float]]:
    return [
        (str(entry["tag"]), float(entry["weight"]))
        for entry in _parse_artist_mix_entries(text)
    ]


def _artist_tags_from_prompt(
    text: str,
    source: str = "artist_field",
) -> list[PromptDataArtistTag]:
    return [
        {
            "tag": str(entry["tag"]),
            "weight": float(entry["weight"]),
            "source": source,
            "grouped": bool(entry.get("grouped")),
        }
        for entry in _parse_artist_mix_entries(text)
    ]


def _bounded_artist_mix_float(
    value,
    default: float,
    minimum: float,
    maximum: float,
) -> float:
    result = _as_float(value, default)
    if not isfinite(result):
        result = default
    return max(minimum, min(maximum, result))


def _bounded_artist_mix_int(
    value,
    default: int,
    minimum: int,
    maximum: int,
) -> int:
    return max(minimum, min(maximum, _as_int(value, default)))


def _normalize_artist_mix_mode(
    value,
    default: str = ARTIST_MIX_MODE_PROMPT,
) -> str:
    mode = str(value or default)
    if mode == ARTIST_MIX_MODE_OFF:
        return ARTIST_MIX_MODE_OFF
    return mode if mode in ARTIST_MIX_MODES else default


__all__ = ()
