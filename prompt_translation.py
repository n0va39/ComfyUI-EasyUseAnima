from __future__ import annotations

import html
from dataclasses import dataclass


PROMPT_TRANSLATION_PROVIDER_OFF = "off"
PROMPT_TRANSLATION_PROVIDER_GOOGLE = "google"
PROMPT_TRANSLATION_PROVIDERS = {
    PROMPT_TRANSLATION_PROVIDER_OFF,
    PROMPT_TRANSLATION_PROVIDER_GOOGLE,
}
DEFAULT_PROMPT_TRANSLATION_SOURCE = "auto"
DEFAULT_PROMPT_TRANSLATION_TARGET = "en"
PROMPT_TRANSLATION_MARKER_LABEL = "translation"


@dataclass(frozen=True)
class PromptTranslationSettings:
    provider: str = PROMPT_TRANSLATION_PROVIDER_OFF
    source: str = DEFAULT_PROMPT_TRANSLATION_SOURCE
    target: str = DEFAULT_PROMPT_TRANSLATION_TARGET


class _TranslationResult:
    def __init__(self, text: str = ""):
        self.text = text


def normalize_prompt_translation_provider(value) -> str:
    provider = str(value or PROMPT_TRANSLATION_PROVIDER_OFF).strip().lower()
    if provider in PROMPT_TRANSLATION_PROVIDERS:
        return provider
    return PROMPT_TRANSLATION_PROVIDER_OFF


def normalize_prompt_translation_language(value, default: str) -> str:
    text = str(value or default).strip().lower()
    return text[:16] or default


def _is_escaped(value: str, index: int) -> bool:
    count = 0
    for cursor in range(index - 1, -1, -1):
        if value[cursor] != "\\":
            break
        count += 1
    return count % 2 == 1


def iter_prompt_translation_markers(text: str):
    value = str(text or "")
    cursor = 0
    while cursor < len(value):
        start = value.find("%{", cursor)
        if start < 0:
            break
        if _is_escaped(value, start):
            cursor = start + 2
            continue
        end = -1
        scan = start + 2
        while scan < len(value):
            if value[scan] == "}" and not _is_escaped(value, scan):
                end = scan + 1
                break
            scan += 1
        if end < 0:
            break
        yield start, end, value[start + 2 : end - 1]
        cursor = end


def has_prompt_translation_markers(text: str) -> bool:
    return next(iter_prompt_translation_markers(text), None) is not None


def strip_prompt_translation_markers(text: str) -> str:
    return translate_prompt_markers(
        text,
        PromptTranslationSettings(provider=PROMPT_TRANSLATION_PROVIDER_OFF),
    )


def _google_translate_with_googletrans(text: str, source: str, target: str) -> _TranslationResult:
    try:
        from googletrans import Translator  # type: ignore
    except ImportError as exc:
        raise RuntimeError(
            "Google prompt translation requires googletrans-py and explicit Google provider selection."
        ) from exc
    translated = Translator().translate(text, src=source or "auto", dest=target or "en")
    return _TranslationResult(html.unescape(str(getattr(translated, "text", "") or "")))


def google_translate_text(text: str, source: str = "auto", target: str = "en") -> str:
    value = str(text or "")
    if not value.strip():
        return value
    source = normalize_prompt_translation_language(source, DEFAULT_PROMPT_TRANSLATION_SOURCE)
    target = normalize_prompt_translation_language(target, DEFAULT_PROMPT_TRANSLATION_TARGET)
    # External translation is opt-in through the prompt translation provider
    # setting. No API keys are read from environment variables and no response is
    # executed as code.
    result = _google_translate_with_googletrans(value, source, target)
    return result.text


def _translate_segment(segment: str, settings: PromptTranslationSettings) -> str:
    if settings.provider == PROMPT_TRANSLATION_PROVIDER_OFF:
        return str(segment or "")
    if settings.provider == PROMPT_TRANSLATION_PROVIDER_GOOGLE:
        return google_translate_text(segment, settings.source, settings.target)
    return str(segment or "")


def translate_prompt_markers(text: str, settings: PromptTranslationSettings | None = None) -> str:
    value = str(text or "")
    markers = list(iter_prompt_translation_markers(value))
    if not markers:
        return value
    settings = settings or PromptTranslationSettings()
    settings = PromptTranslationSettings(
        provider=normalize_prompt_translation_provider(settings.provider),
        source=normalize_prompt_translation_language(settings.source, DEFAULT_PROMPT_TRANSLATION_SOURCE),
        target=normalize_prompt_translation_language(settings.target, DEFAULT_PROMPT_TRANSLATION_TARGET),
    )

    output: list[str] = []
    cursor = 0
    for start, end, segment in markers:
        output.append(value[cursor:start])
        output.append(_translate_segment(segment.strip(), settings))
        cursor = end
    output.append(value[cursor:])
    return "".join(output)
