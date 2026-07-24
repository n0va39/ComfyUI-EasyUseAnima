"""Prompt translation settings, limits, and error contracts."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

PROMPT_TRANSLATION_PROVIDER_OFF = "off"
PROMPT_TRANSLATION_PROVIDER_GOOGLE = "google"
PROMPT_TRANSLATION_PROVIDERS = {
    PROMPT_TRANSLATION_PROVIDER_OFF,
    PROMPT_TRANSLATION_PROVIDER_GOOGLE,
}
DEFAULT_PROMPT_TRANSLATION_SOURCE = "auto"
DEFAULT_PROMPT_TRANSLATION_TARGET = "en"

MAX_PROMPT_TRANSLATION_MARKERS = 64
MAX_PROMPT_TRANSLATION_MARKER_CHARACTERS = 1024
MAX_PROMPT_TRANSLATION_TOTAL_CHARACTERS = 4096
PROMPT_TRANSLATION_CACHE_MAX_ENTRIES = 256
PROMPT_TRANSLATION_CACHE_TTL_SECONDS = 300.0
PROMPT_TRANSLATION_PROVIDER_TIMEOUT_SECONDS = 10.0

TranslationCacheKey = tuple[str, str, str, str]


@dataclass(frozen=True)
class PromptTranslationSettings:
    provider: str = PROMPT_TRANSLATION_PROVIDER_OFF
    source: str = DEFAULT_PROMPT_TRANSLATION_SOURCE
    target: str = DEFAULT_PROMPT_TRANSLATION_TARGET


class PromptTranslationError(RuntimeError):
    code = "translation_error"
    status = 500
    default_message = "Prompt translation failed."

    def __init__(self, message: str | None = None):
        super().__init__(message or self.default_message)
        self.message = message or self.default_message


class PromptTranslationLimitError(PromptTranslationError):
    status = 413


class TranslationMarkerCountError(PromptTranslationLimitError):
    code = "translation_marker_count_exceeded"


class TranslationMarkerSizeError(PromptTranslationLimitError):
    code = "translation_marker_too_long"


class TranslationTotalSizeError(PromptTranslationLimitError):
    code = "translation_marker_characters_exceeded"


class TranslationProviderUnavailableError(PromptTranslationError):
    code = "translation_provider_unavailable"
    status = 503
    default_message = "The selected translation provider is unavailable."


class TranslationTimeoutError(PromptTranslationError):
    code = "translation_timeout"
    status = 504
    default_message = "The translation provider timed out."


class TranslationCancelledError(PromptTranslationError):
    code = "translation_cancelled"
    status = 499
    default_message = "The translation request was cancelled."


class TranslationBusyError(PromptTranslationError):
    code = "translation_busy"
    status = 503
    default_message = "A prompt translation request is already in progress."


class TranslationUpstreamError(PromptTranslationError):
    code = "translation_upstream_error"
    status = 502
    default_message = "The translation provider request failed."


class TranslationProvider(Protocol):
    def translate(self, text: str, source: str, target: str) -> str:
        """Translate one marker value and return plain text."""
        ...


def normalize_prompt_translation_provider(value) -> str:
    provider = str(value or PROMPT_TRANSLATION_PROVIDER_OFF).strip().lower()
    if provider in PROMPT_TRANSLATION_PROVIDERS:
        return provider
    return PROMPT_TRANSLATION_PROVIDER_OFF


def normalize_prompt_translation_language(value, default: str) -> str:
    text = str(value or default).strip().lower()
    return text[:16] or default


__all__ = (
    "DEFAULT_PROMPT_TRANSLATION_SOURCE",
    "DEFAULT_PROMPT_TRANSLATION_TARGET",
    "MAX_PROMPT_TRANSLATION_MARKER_CHARACTERS",
    "MAX_PROMPT_TRANSLATION_MARKERS",
    "MAX_PROMPT_TRANSLATION_TOTAL_CHARACTERS",
    "PROMPT_TRANSLATION_CACHE_MAX_ENTRIES",
    "PROMPT_TRANSLATION_CACHE_TTL_SECONDS",
    "PROMPT_TRANSLATION_PROVIDER_GOOGLE",
    "PROMPT_TRANSLATION_PROVIDER_OFF",
    "PROMPT_TRANSLATION_PROVIDER_TIMEOUT_SECONDS",
    "PROMPT_TRANSLATION_PROVIDERS",
    "PromptTranslationError",
    "PromptTranslationLimitError",
    "PromptTranslationSettings",
    "TranslationBusyError",
    "TranslationCacheKey",
    "TranslationCancelledError",
    "TranslationMarkerCountError",
    "TranslationMarkerSizeError",
    "TranslationProvider",
    "TranslationProviderUnavailableError",
    "TranslationTimeoutError",
    "TranslationTotalSizeError",
    "TranslationUpstreamError",
    "normalize_prompt_translation_language",
    "normalize_prompt_translation_provider",
)
