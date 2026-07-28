"""Prompt translation provider reuse, cache, and service ownership."""

from __future__ import annotations

import threading
import time
from collections import OrderedDict
from collections.abc import Callable
from contextlib import contextmanager
from dataclasses import dataclass

from .contracts import (
    DEFAULT_PROMPT_TRANSLATION_SOURCE,
    DEFAULT_PROMPT_TRANSLATION_TARGET,
    MAX_PROMPT_TRANSLATION_MARKER_CHARACTERS,
    MAX_PROMPT_TRANSLATION_MARKERS,
    MAX_PROMPT_TRANSLATION_TOTAL_CHARACTERS,
    PROMPT_TRANSLATION_CACHE_MAX_ENTRIES,
    PROMPT_TRANSLATION_CACHE_TTL_SECONDS,
    PROMPT_TRANSLATION_PROVIDER_GOOGLE,
    PROMPT_TRANSLATION_PROVIDER_OFF,
    PromptTranslationSettings,
    TranslationCacheKey,
    TranslationMarkerCountError,
    TranslationMarkerSizeError,
    TranslationProvider,
    TranslationTotalSizeError,
    normalize_prompt_translation_language,
    normalize_prompt_translation_provider,
)
from .markers import iter_prompt_translation_markers
from .ports import PromptTranslationPort
from .provider_registry import _TranslationProviderRegistry
from .providers.google import GoogleTranslationProvider

_DEFAULT_TRANSLATION_PROVIDER_REGISTRY = _TranslationProviderRegistry(
    {
        PROMPT_TRANSLATION_PROVIDER_GOOGLE: GoogleTranslationProvider,
    }
)


def get_translation_provider(provider: str) -> TranslationProvider:
    return _DEFAULT_TRANSLATION_PROVIDER_REGISTRY.get(provider)


def google_translate_text(
    text: str,
    source: str = "auto",
    target: str = "en",
) -> str:
    value = str(text or "")
    if not value.strip():
        return value
    source = normalize_prompt_translation_language(
        source,
        DEFAULT_PROMPT_TRANSLATION_SOURCE,
    )
    target = normalize_prompt_translation_language(
        target,
        DEFAULT_PROMPT_TRANSLATION_TARGET,
    )
    # External translation is opt-in through the provider setting. The optional
    # dependency is imported only after this function is reached.
    return get_translation_provider(
        PROMPT_TRANSLATION_PROVIDER_GOOGLE
    ).translate(
        value,
        source,
        target,
    )


def _translate_segment(
    segment: str,
    settings: PromptTranslationSettings,
) -> str:
    if settings.provider == PROMPT_TRANSLATION_PROVIDER_OFF:
        return str(segment or "")
    if settings.provider == PROMPT_TRANSLATION_PROVIDER_GOOGLE:
        return google_translate_text(
            segment,
            settings.source,
            settings.target,
        )
    return str(segment or "")


_CACHE_MISS = object()


@dataclass
class _TranslationFlight:
    lock: threading.Lock
    users: int = 0


class BoundedTranslationCache:
    def __init__(
        self,
        max_entries: int = PROMPT_TRANSLATION_CACHE_MAX_ENTRIES,
        ttl_seconds: float = PROMPT_TRANSLATION_CACHE_TTL_SECONDS,
        time_func: Callable[[], float] = time.monotonic,
    ):
        self.max_entries = max(0, int(max_entries))
        self.ttl_seconds = max(0.0, float(ttl_seconds))
        self._time_func = time_func
        self._entries: OrderedDict[
            TranslationCacheKey,
            tuple[float, str],
        ] = OrderedDict()
        self._lock = threading.RLock()

    def get(self, key: TranslationCacheKey):
        with self._lock:
            entry = self._entries.get(key)
            if entry is None:
                return _CACHE_MISS
            expires_at, value = entry
            if expires_at <= self._time_func():
                self._entries.pop(key, None)
                return _CACHE_MISS
            self._entries.move_to_end(key)
            return value

    def put(self, key: TranslationCacheKey, value: str) -> None:
        if self.max_entries == 0 or self.ttl_seconds == 0:
            return
        with self._lock:
            self._entries[key] = (
                self._time_func() + self.ttl_seconds,
                str(value),
            )
            self._entries.move_to_end(key)
            while len(self._entries) > self.max_entries:
                self._entries.popitem(last=False)

    def clear(self) -> None:
        with self._lock:
            self._entries.clear()

    def __len__(self) -> int:
        with self._lock:
            return len(self._entries)


class PromptTranslationService:
    def __init__(
        self,
        *,
        cache: BoundedTranslationCache | None = None,
        max_markers: int = MAX_PROMPT_TRANSLATION_MARKERS,
        max_marker_characters: int = (
            MAX_PROMPT_TRANSLATION_MARKER_CHARACTERS
        ),
        max_total_characters: int = (
            MAX_PROMPT_TRANSLATION_TOTAL_CHARACTERS
        ),
    ):
        self.cache = (
            cache
            if cache is not None
            else BoundedTranslationCache()
        )
        self.max_markers = max(1, int(max_markers))
        self.max_marker_characters = max(
            1,
            int(max_marker_characters),
        )
        self.max_total_characters = max(
            1,
            int(max_total_characters),
        )
        self._flights: dict[
            TranslationCacheKey,
            _TranslationFlight,
        ] = {}
        self._flights_lock = threading.RLock()

    @contextmanager
    def _single_flight(self, key: TranslationCacheKey):
        with self._flights_lock:
            flight = self._flights.get(key)
            if flight is None:
                flight = _TranslationFlight(lock=threading.Lock())
                self._flights[key] = flight
            flight.users += 1
        try:
            with flight.lock:
                yield
        finally:
            with self._flights_lock:
                flight.users -= 1
                if (
                    flight.users == 0
                    and self._flights.get(key) is flight
                ):
                    self._flights.pop(key, None)

    def _validate_markers(
        self,
        markers: list[tuple[int, int, str]],
    ) -> None:
        if len(markers) > self.max_markers:
            raise TranslationMarkerCountError(
                "Prompt translation supports at most "
                f"{self.max_markers} markers per request."
            )
        for _start, _end, segment in markers:
            if len(segment) > self.max_marker_characters:
                raise TranslationMarkerSizeError(
                    "Prompt translation supports at most "
                    f"{self.max_marker_characters} characters "
                    "in one marker."
                )
        total_characters = sum(
            len(segment)
            for _start, _end, segment in markers
        )
        if total_characters > self.max_total_characters:
            raise TranslationTotalSizeError(
                "Prompt translation supports at most "
                f"{self.max_total_characters} marker characters "
                "per request."
            )

    def _translate_cached(
        self,
        text: str,
        settings: PromptTranslationSettings,
    ) -> str:
        key = (
            settings.provider,
            settings.source,
            settings.target,
            text,
        )
        cached = self.cache.get(key)
        if cached is not _CACHE_MISS:
            return str(cached)
        with self._single_flight(key):
            cached = self.cache.get(key)
            if cached is not _CACHE_MISS:
                return str(cached)
            translated = _translate_segment(text, settings)
            self.cache.put(key, translated)
            return translated

    def translate_prompt(
        self,
        text: str,
        settings: PromptTranslationSettings | None = None,
    ) -> str:
        value = str(text or "")
        markers = list(iter_prompt_translation_markers(value))
        if not markers:
            return value
        settings = settings or PromptTranslationSettings()
        settings = PromptTranslationSettings(
            provider=normalize_prompt_translation_provider(
                settings.provider
            ),
            source=normalize_prompt_translation_language(
                settings.source,
                DEFAULT_PROMPT_TRANSLATION_SOURCE,
            ),
            target=normalize_prompt_translation_language(
                settings.target,
                DEFAULT_PROMPT_TRANSLATION_TARGET,
            ),
        )

        if settings.provider == PROMPT_TRANSLATION_PROVIDER_OFF:
            translated_segments = {
                segment.strip(): segment.strip()
                for _, _, segment in markers
            }
        else:
            self._validate_markers(markers)
            translated_segments: dict[str, str] = {}
            for _start, _end, segment in markers:
                marker_text = segment.strip()
                if marker_text not in translated_segments:
                    translated_segments[marker_text] = (
                        self._translate_cached(
                            marker_text,
                            settings,
                        )
                        if marker_text
                        else ""
                    )

        output: list[str] = []
        cursor = 0
        for start, end, segment in markers:
            output.append(value[cursor:start])
            output.append(translated_segments[segment.strip()])
            cursor = end
        output.append(value[cursor:])
        return "".join(output)

    def close(self) -> None:
        self.cache.clear()


_DEFAULT_TRANSLATION_SERVICE: PromptTranslationPort = (
    PromptTranslationService()
)


def _install_default_translation_service(
    translation: PromptTranslationPort,
) -> PromptTranslationPort:
    global _DEFAULT_TRANSLATION_SERVICE

    previous = _DEFAULT_TRANSLATION_SERVICE
    _DEFAULT_TRANSLATION_SERVICE = translation
    return previous


def _restore_default_translation_service(
    expected: PromptTranslationPort,
    replacement: PromptTranslationPort,
) -> bool:
    """Restore the facade only while it still names the expected service."""

    global _DEFAULT_TRANSLATION_SERVICE

    if _DEFAULT_TRANSLATION_SERVICE is not expected:
        return False
    _DEFAULT_TRANSLATION_SERVICE = replacement
    return True


def strip_prompt_translation_markers(text: str) -> str:
    return translate_prompt_markers(
        text,
        PromptTranslationSettings(
            provider=PROMPT_TRANSLATION_PROVIDER_OFF
        ),
    )


def translate_prompt_markers(
    text: str,
    settings: PromptTranslationSettings | None = None,
) -> str:
    """Compatibility facade used by synchronous ComfyUI node execution."""

    return _DEFAULT_TRANSLATION_SERVICE.translate_prompt(text, settings)


__all__ = (
    "BoundedTranslationCache",
    "PromptTranslationService",
    "get_translation_provider",
    "google_translate_text",
    "strip_prompt_translation_markers",
    "translate_prompt_markers",
)
