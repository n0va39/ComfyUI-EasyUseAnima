"""Prompt inspection and correction."""

from __future__ import annotations

import re
from dataclasses import dataclass

from .knowledge import PromptKnowledgeBase
from .models import CorrectionResult, TagToken
from .normalize import lookup_key, normalize_tag, render_artist_tag
from .ordering import classify_tag, section_sort_key
from .parser import parse_prompt, render_tags

_WORD_RE = re.compile(r"[A-Za-z]+")


@dataclass(frozen=True)
class PromptSyntax:
    tag_text: str
    prefix: str = ""
    weight_suffix: str = ""
    suffix: str = ""


def _is_escaped(text: str, index: int) -> bool:
    slash_count = 0
    cursor = index - 1
    while cursor >= 0 and text[cursor] == "\\":
        slash_count += 1
        cursor -= 1
    return slash_count % 2 == 1


def _outer_parens_span(text: str) -> bool:
    if not text.startswith("("):
        return False
    depth = 0
    for index, char in enumerate(text):
        if char == "(" and not _is_escaped(text, index):
            depth += 1
        elif char == ")" and not _is_escaped(text, index):
            depth -= 1
            if depth == 0 and index != len(text) - 1:
                return False
    return depth == 0


def _last_unescaped_colon(text: str) -> int:
    for index in range(len(text) - 1, -1, -1):
        if text[index] == ":" and not _is_escaped(text, index):
            return index
    return -1


def _prompt_syntax(raw: str) -> PromptSyntax:
    text = str(raw or "").strip()
    prefix = ""
    suffix = ""
    while _outer_parens_span(text):
        prefix += "("
        suffix = ")" + suffix
        text = text[1:-1].strip()

    colon_index = _last_unescaped_colon(text) if prefix else -1
    if colon_index > 0 and colon_index < len(text) - 1:
        weight_suffix = text[colon_index:].strip()
        text = text[:colon_index].strip()
    else:
        weight_suffix = ""

    return PromptSyntax(
        tag_text=text,
        prefix=prefix,
        weight_suffix=weight_suffix,
        suffix=suffix,
    )


def _escape_literal_parentheses(text: str) -> str:
    chars: list[str] = []
    for index, char in enumerate(text):
        if char in "()" and not _is_escaped(text, index):
            chars.append("\\")
        chars.append(char)
    return "".join(chars)


def _is_natural_language_token(text: str) -> bool:
    stripped = str(text or "").strip()
    if not stripped or stripped.startswith("@"):
        return False
    if any(char.isupper() for char in stripped):
        return True
    if any(char in stripped for char in ".!?"):
        return True
    if "," in stripped:
        return True
    return len(_WORD_RE.findall(stripped)) >= 6


def _render_token(raw: str, section_name: str, *, preserve_text: bool = False) -> str:
    if preserve_text:
        return _escape_literal_parentheses(str(raw or "").strip())
    if section_name == "artist":
        return _escape_literal_parentheses(render_artist_tag(raw))
    return _escape_literal_parentheses(normalize_tag(raw))


def _render_prompt_token(
    syntax: PromptSyntax,
    normalized: str,
    section_name: str,
    *,
    preserve_override_text: bool = False,
) -> str:
    preserve_text = preserve_override_text or _is_natural_language_token(syntax.tag_text)
    rendered = _render_token(
        syntax.tag_text if preserve_text else normalized,
        section_name,
        preserve_text=preserve_text,
    )
    return f"{syntax.prefix}{rendered}{syntax.weight_suffix}{syntax.suffix}"


def _tag_key_set(tags) -> set[str]:
    return {lookup_key(str(tag)) for tag in tags or () if str(tag).strip()}


def _classify_with_artist_options(
    normalized: str,
    *,
    info,
    kb: PromptKnowledgeBase,
    validate_artist_tags: bool,
    artist_overrides: set[str],
    artist_exclusions: set[str],
):
    key = lookup_key(normalized)
    if key in artist_exclusions:
        return classify_tag(normalized.lstrip("@"), None)
    if key in artist_overrides:
        return classify_tag(f"@{key}", info)
    if normalized.strip().startswith("@"):
        if not validate_artist_tags:
            return classify_tag(normalized, info)
        if key in kb.animadex.artists:
            return classify_tag(normalized, info)
        return classify_tag(normalized.lstrip("@"), None)
    return classify_tag(normalized, info)


def inspect_prompt(
    text: str,
    *,
    profile: str = "prompt",
    knowledge_base: PromptKnowledgeBase | None = None,
    validate_artist_tags: bool = False,
    artist_overrides=(),
    artist_exclusions=(),
) -> CorrectionResult:
    """Parse and classify a prompt without reordering it."""

    kb = knowledge_base or PromptKnowledgeBase.empty()
    override_keys = _tag_key_set(artist_overrides)
    exclusion_keys = _tag_key_set(artist_exclusions)
    parsed = parse_prompt(text, profile=profile)
    tokens: list[TagToken] = []
    unknown: list[str] = []
    seen: set[str] = set()
    duplicates: list[str] = []

    for raw in parsed.tokens:
        syntax = _prompt_syntax(raw)
        normalized = normalize_tag(syntax.tag_text)
        key = lookup_key(normalized)
        info = kb.lookup(normalized)
        manual_known = key in override_keys
        preserve_override_text = manual_known and not normalized.strip().startswith("@")
        section = _classify_with_artist_options(
            normalized,
            info=info,
            kb=kb,
            validate_artist_tags=validate_artist_tags,
            artist_overrides=override_keys,
            artist_exclusions=exclusion_keys,
        )
        dedupe_key = key
        if dedupe_key in seen:
            duplicates.append(normalized)
        else:
            seen.add(dedupe_key)
        if info is None and not manual_known:
            unknown.append(normalized)
        tokens.append(
            TagToken(
                raw=raw,
                normalized=normalized,
                lookup_key=key,
                text=_render_prompt_token(
                    syntax,
                    normalized,
                    section.value,
                    preserve_override_text=preserve_override_text,
                ),
                known=info is not None or manual_known,
                section=section,
                category_path=info.category_path if info else (),
                source=info.source if info else None,
            )
        )

    return CorrectionResult(
        text=text,
        original_text=text,
        tokens=tuple(tokens),
        unknown_tags=tuple(unknown),
        duplicate_tags=tuple(duplicates),
        warnings=(),
        changed=False,
        report={
            "profile": parsed.profile,
            "delimiter": parsed.delimiter,
            "sections": [token.section.value for token in tokens],
        },
    )


def correct_prompt(
    text: str,
    *,
    profile: str = "prompt",
    knowledge_base: PromptKnowledgeBase | None = None,
    validate_artist_tags: bool = False,
    artist_overrides=(),
    artist_exclusions=(),
) -> CorrectionResult:
    """Normalize, deduplicate, classify, and reorder a prompt for ANIMA."""

    kb = knowledge_base or PromptKnowledgeBase.empty()
    parsed = parse_prompt(text, profile=profile)
    inspected = inspect_prompt(
        text,
        profile=profile,
        knowledge_base=kb,
        validate_artist_tags=validate_artist_tags,
        artist_overrides=artist_overrides,
        artist_exclusions=artist_exclusions,
    )

    kept: list[tuple[int, TagToken]] = []
    seen: set[str] = set()
    duplicates: list[str] = []
    for index, token in enumerate(inspected.tokens):
        if token.lookup_key in seen:
            duplicates.append(token.normalized)
            continue
        seen.add(token.lookup_key)
        kept.append((index, token))

    kept.sort(key=lambda item: section_sort_key(item[0], item[1].section))
    ordered = [token.text for _, token in kept]
    corrected = render_tags(ordered, parsed.delimiter)
    warnings: list[str] = []
    if inspected.unknown_tags:
        warnings.append(f"unknown tags: {', '.join(inspected.unknown_tags)}")
    if duplicates:
        warnings.append(f"duplicate tags removed: {', '.join(duplicates)}")

    return CorrectionResult(
        text=corrected,
        original_text=text,
        tokens=tuple(token for _, token in kept),
        unknown_tags=inspected.unknown_tags,
        duplicate_tags=tuple(duplicates),
        warnings=tuple(warnings),
        changed=corrected != text,
        report={
            "profile": parsed.profile,
            "delimiter": parsed.delimiter,
            "sections": [token.section.value for _, token in kept],
            "removed_duplicates": duplicates,
        },
    )
