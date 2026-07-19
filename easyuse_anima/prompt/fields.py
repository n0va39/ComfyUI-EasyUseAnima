"""Classic Prompt Builder field assembly helpers."""

from __future__ import annotations

import re

try:
    from ...anima_prompt import correct_prompt, load_knowledge_base
    from ...anima_prompt.parser import parse_prompt
except ImportError:
    from anima_prompt import correct_prompt, load_knowledge_base
    from anima_prompt.parser import parse_prompt


DEFAULT_QUALITY_TAGS = (
    "newest, masterpiece, best quality, score_8, score_7:, highres, absurdres, very aesthetic"
)
DEFAULT_TRAILING_QUALITY_TAGS = (
    "location, (A highly aesthetic Pixiv style illustration, clean composition, "
    "high-quality digital art, detailed background, sharp focus on facial expressions.:0.6)"
)

_HASH_COMMENT_RE = re.compile(r"^[ \t]*#[^\n]*", re.MULTILINE)
_INLINE_SPACE_RE = re.compile(r"[ \t]+")
_WEIGHTED_TOKEN_RE = re.compile(r"^\(([^(),]+):[-+]?\d+(?:\.\d+)?\)$")
_RUNTIME_HELPER_RESOLVER = None


def _bind_prompt_fields_runtime(*, resolve_helper) -> None:
    global _RUNTIME_HELPER_RESOLVER
    _RUNTIME_HELPER_RESOLVER = resolve_helper


def _runtime_helper(name, fallback):
    if _RUNTIME_HELPER_RESOLVER is None:
        return fallback
    return _RUNTIME_HELPER_RESOLVER(name)


def _prompt_tokens(value: str) -> list[str]:
    if not value:
        return []
    hash_comment_re = _runtime_helper("_HASH_COMMENT_RE", _HASH_COMMENT_RE)
    inline_space_re = _runtime_helper("_INLINE_SPACE_RE", _INLINE_SPACE_RE)
    prompt_parser = _runtime_helper("parse_prompt", parse_prompt)
    cleaned_val = hash_comment_re.sub("", value)
    normalized = str(cleaned_val).replace("\r\n", "\n").replace("\r", "\n")
    normalized = normalized.replace("，", ",").replace("\n", ",")
    tokens: list[str] = []
    for token in prompt_parser(normalized, profile="prompt").tokens:
        cleaned = inline_space_re.sub(" ", str(token).strip(" ,\n\t"))
        if cleaned:
            tokens.append(cleaned)
    return tokens


def _join_prompt_tokens(*parts: str) -> str:
    prompt_tokens = _runtime_helper("_prompt_tokens", _prompt_tokens)
    tokens: list[str] = []
    for part in parts:
        tokens.extend(prompt_tokens(part))
    return ", ".join(tokens)


def _correct_builder_prompt(prompt: str, artist_overrides: str = "") -> str:
    if not prompt:
        return ""
    correction = _runtime_helper("correct_prompt", correct_prompt)
    knowledge_base_loader = _runtime_helper("load_knowledge_base", load_knowledge_base)
    prompt_tokens = _runtime_helper("_prompt_tokens", _prompt_tokens)
    result = correction(
        prompt,
        profile="prompt",
        knowledge_base=knowledge_base_loader(allow_missing=True),
        validate_artist_tags=False,
        artist_overrides=prompt_tokens(artist_overrides),
    )
    return result.text


def _metadata_filter_key(value: str) -> str:
    inline_space_re = _runtime_helper("_INLINE_SPACE_RE", _INLINE_SPACE_RE)
    value = inline_space_re.sub(" ", str(value or "").strip(" ,\n\t"))
    return value.replace("_", " ").casefold()


def _metadata_filter_keys(value: str) -> set[str]:
    metadata_filter_key = _runtime_helper("_metadata_filter_key", _metadata_filter_key)
    weighted_token_re = _runtime_helper("_WEIGHTED_TOKEN_RE", _WEIGHTED_TOKEN_RE)
    keys = {metadata_filter_key(value)}
    weighted = weighted_token_re.match(str(value or "").strip())
    if weighted:
        keys.add(metadata_filter_key(weighted.group(1)))
    return {key for key in keys if key}


def _filter_metadata_prompt(prompt: str, filter_words: str) -> str:
    prompt_tokens = _runtime_helper("_prompt_tokens", _prompt_tokens)
    metadata_filter_keys = _runtime_helper("_metadata_filter_keys", _metadata_filter_keys)
    filter_keys: set[str] = set()
    for word in prompt_tokens(filter_words):
        filter_keys.update(metadata_filter_keys(word))
    if not prompt or not filter_keys:
        return prompt

    kept = [
        token
        for token in prompt_tokens(prompt)
        if metadata_filter_keys(token).isdisjoint(filter_keys)
    ]
    return ", ".join(kept)


__all__ = ()
