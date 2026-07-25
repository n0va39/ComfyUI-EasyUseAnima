"""Compatibility shim for the canonical prompt translation feature."""

from __future__ import annotations

try:
    from .easyuse_anima.translation.contracts import (
        DEFAULT_PROMPT_TRANSLATION_SOURCE,
        DEFAULT_PROMPT_TRANSLATION_TARGET,
        MAX_PROMPT_TRANSLATION_MARKER_CHARACTERS,
        MAX_PROMPT_TRANSLATION_MARKERS,
        MAX_PROMPT_TRANSLATION_TOTAL_CHARACTERS,
        PROMPT_TRANSLATION_CACHE_MAX_ENTRIES,
        PROMPT_TRANSLATION_CACHE_TTL_SECONDS,
        PROMPT_TRANSLATION_PROVIDER_GOOGLE,
        PROMPT_TRANSLATION_PROVIDER_OFF,
        PROMPT_TRANSLATION_PROVIDER_TIMEOUT_SECONDS,
        PROMPT_TRANSLATION_PROVIDERS,
        PromptTranslationError,
        PromptTranslationLimitError,
        PromptTranslationSettings,
        TranslationBusyError,
        TranslationCacheKey,
        TranslationCancelledError,
        TranslationMarkerCountError,
        TranslationMarkerSizeError,
        TranslationProvider,
        TranslationProviderUnavailableError,
        TranslationTimeoutError,
        TranslationTotalSizeError,
        TranslationUpstreamError,
        normalize_prompt_translation_language,
        normalize_prompt_translation_provider,
    )
    from .easyuse_anima.translation.markers import (
        PROMPT_TRANSLATION_MARKER_LABEL,
        has_prompt_translation_markers,
        iter_prompt_translation_markers,
    )
    from .easyuse_anima.translation.providers.google import (
        GoogleTranslationProvider,
    )
    from .easyuse_anima.translation.service import (
        BoundedTranslationCache,
        PromptTranslationService,
        get_translation_provider,
        google_translate_text,
        strip_prompt_translation_markers,
        translate_prompt_markers,
    )
except ImportError:
    from easyuse_anima.translation.contracts import (
        DEFAULT_PROMPT_TRANSLATION_SOURCE,
        DEFAULT_PROMPT_TRANSLATION_TARGET,
        MAX_PROMPT_TRANSLATION_MARKER_CHARACTERS,
        MAX_PROMPT_TRANSLATION_MARKERS,
        MAX_PROMPT_TRANSLATION_TOTAL_CHARACTERS,
        PROMPT_TRANSLATION_CACHE_MAX_ENTRIES,
        PROMPT_TRANSLATION_CACHE_TTL_SECONDS,
        PROMPT_TRANSLATION_PROVIDER_GOOGLE,
        PROMPT_TRANSLATION_PROVIDER_OFF,
        PROMPT_TRANSLATION_PROVIDER_TIMEOUT_SECONDS,
        PROMPT_TRANSLATION_PROVIDERS,
        PromptTranslationError,
        PromptTranslationLimitError,
        PromptTranslationSettings,
        TranslationBusyError,
        TranslationCacheKey,
        TranslationCancelledError,
        TranslationMarkerCountError,
        TranslationMarkerSizeError,
        TranslationProvider,
        TranslationProviderUnavailableError,
        TranslationTimeoutError,
        TranslationTotalSizeError,
        TranslationUpstreamError,
        normalize_prompt_translation_language,
        normalize_prompt_translation_provider,
    )
    from easyuse_anima.translation.markers import (
        PROMPT_TRANSLATION_MARKER_LABEL,
        has_prompt_translation_markers,
        iter_prompt_translation_markers,
    )
    from easyuse_anima.translation.providers.google import (
        GoogleTranslationProvider,
    )
    from easyuse_anima.translation.service import (
        BoundedTranslationCache,
        PromptTranslationService,
        get_translation_provider,
        google_translate_text,
        strip_prompt_translation_markers,
        translate_prompt_markers,
    )


__all__ = (
    "BoundedTranslationCache",
    "DEFAULT_PROMPT_TRANSLATION_SOURCE",
    "DEFAULT_PROMPT_TRANSLATION_TARGET",
    "GoogleTranslationProvider",
    "MAX_PROMPT_TRANSLATION_MARKER_CHARACTERS",
    "MAX_PROMPT_TRANSLATION_MARKERS",
    "MAX_PROMPT_TRANSLATION_TOTAL_CHARACTERS",
    "PROMPT_TRANSLATION_CACHE_MAX_ENTRIES",
    "PROMPT_TRANSLATION_CACHE_TTL_SECONDS",
    "PROMPT_TRANSLATION_MARKER_LABEL",
    "PROMPT_TRANSLATION_PROVIDER_GOOGLE",
    "PROMPT_TRANSLATION_PROVIDER_OFF",
    "PROMPT_TRANSLATION_PROVIDER_TIMEOUT_SECONDS",
    "PROMPT_TRANSLATION_PROVIDERS",
    "PromptTranslationError",
    "PromptTranslationLimitError",
    "PromptTranslationService",
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
    "get_translation_provider",
    "google_translate_text",
    "has_prompt_translation_markers",
    "iter_prompt_translation_markers",
    "normalize_prompt_translation_language",
    "normalize_prompt_translation_provider",
    "strip_prompt_translation_markers",
    "translate_prompt_markers",
)
