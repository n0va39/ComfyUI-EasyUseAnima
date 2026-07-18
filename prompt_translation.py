from __future__ import annotations

import html
import threading
import time
from collections import OrderedDict
from dataclasses import dataclass
from typing import Callable, Protocol


PROMPT_TRANSLATION_PROVIDER_OFF = "off"
PROMPT_TRANSLATION_PROVIDER_GOOGLE = "google"
PROMPT_TRANSLATION_PROVIDERS = {
    PROMPT_TRANSLATION_PROVIDER_OFF,
    PROMPT_TRANSLATION_PROVIDER_GOOGLE,
}
DEFAULT_PROMPT_TRANSLATION_SOURCE = "auto"
DEFAULT_PROMPT_TRANSLATION_TARGET = "en"
PROMPT_TRANSLATION_MARKER_LABEL = "translation"

MAX_PROMPT_TRANSLATION_MARKERS = 64
MAX_PROMPT_TRANSLATION_MARKER_CHARACTERS = 1024
MAX_PROMPT_TRANSLATION_TOTAL_CHARACTERS = 4096
PROMPT_TRANSLATION_CACHE_MAX_ENTRIES = 256
PROMPT_TRANSLATION_CACHE_TTL_SECONDS = 300.0


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


class TranslationUpstreamError(PromptTranslationError):
    code = "translation_upstream_error"
    status = 502
    default_message = "The translation provider request failed."


class TranslationProvider(Protocol):
    def translate(self, text: str, source: str, target: str) -> str:
        """Translate one marker value and return plain text."""


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


def _looks_like_timeout(exc: Exception) -> bool:
    if isinstance(exc, TimeoutError):
        return True
    return any("timeout" in cls.__name__.lower() for cls in type(exc).__mro__)


class GoogleTranslationProvider:
    """Lazy, reusable wrapper around the optional googletrans-py client."""

    def __init__(self, translator_factory: Callable[[], object] | None = None):
        self._translator_factory = translator_factory
        self._translator = None
        self._lock = threading.RLock()

    def _create_translator(self):
        if self._translator_factory is not None:
            return self._translator_factory()
        try:
            from googletrans import Translator  # type: ignore
        except ImportError as exc:
            raise TranslationProviderUnavailableError() from exc
        return Translator()

    def translate(self, text: str, source: str, target: str) -> str:
        value = str(text or "")
        if not value.strip():
            return value
        try:
            with self._lock:
                if self._translator is None:
                    self._translator = self._create_translator()
                translated = self._translator.translate(
                    value,
                    src=source or DEFAULT_PROMPT_TRANSLATION_SOURCE,
                    dest=target or DEFAULT_PROMPT_TRANSLATION_TARGET,
                )
        except PromptTranslationError:
            raise
        except ImportError as exc:
            raise TranslationProviderUnavailableError() from exc
        except Exception as exc:
            if _looks_like_timeout(exc):
                raise TranslationTimeoutError() from exc
            raise TranslationUpstreamError() from exc
        return html.unescape(str(getattr(translated, "text", "") or ""))


_TRANSLATION_PROVIDER_FACTORIES: dict[str, Callable[[], TranslationProvider]] = {
    PROMPT_TRANSLATION_PROVIDER_GOOGLE: GoogleTranslationProvider,
}
_TRANSLATION_PROVIDER_INSTANCES: dict[str, TranslationProvider] = {}
_TRANSLATION_PROVIDER_LOCK = threading.RLock()


def get_translation_provider(provider: str) -> TranslationProvider:
    name = str(provider or "").strip().lower()
    with _TRANSLATION_PROVIDER_LOCK:
        instance = _TRANSLATION_PROVIDER_INSTANCES.get(name)
        if instance is not None:
            return instance
        factory = _TRANSLATION_PROVIDER_FACTORIES.get(name)
        if factory is None:
            raise TranslationProviderUnavailableError()
        try:
            instance = factory()
        except PromptTranslationError:
            raise
        except Exception as exc:
            raise TranslationProviderUnavailableError() from exc
        _TRANSLATION_PROVIDER_INSTANCES[name] = instance
        return instance


def google_translate_text(text: str, source: str = "auto", target: str = "en") -> str:
    value = str(text or "")
    if not value.strip():
        return value
    source = normalize_prompt_translation_language(source, DEFAULT_PROMPT_TRANSLATION_SOURCE)
    target = normalize_prompt_translation_language(target, DEFAULT_PROMPT_TRANSLATION_TARGET)
    # External translation is opt-in through the provider setting. The optional
    # dependency is imported only after this function is reached.
    return get_translation_provider(PROMPT_TRANSLATION_PROVIDER_GOOGLE).translate(
        value,
        source,
        target,
    )


def _translate_segment(segment: str, settings: PromptTranslationSettings) -> str:
    if settings.provider == PROMPT_TRANSLATION_PROVIDER_OFF:
        return str(segment or "")
    if settings.provider == PROMPT_TRANSLATION_PROVIDER_GOOGLE:
        return google_translate_text(segment, settings.source, settings.target)
    return str(segment or "")


_CACHE_MISS = object()
TranslationCacheKey = tuple[str, str, str, str]


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
        self._entries: OrderedDict[TranslationCacheKey, tuple[float, str]] = OrderedDict()
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
            self._entries[key] = (self._time_func() + self.ttl_seconds, str(value))
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
        max_marker_characters: int = MAX_PROMPT_TRANSLATION_MARKER_CHARACTERS,
        max_total_characters: int = MAX_PROMPT_TRANSLATION_TOTAL_CHARACTERS,
    ):
        self.cache = cache if cache is not None else BoundedTranslationCache()
        self.max_markers = max(1, int(max_markers))
        self.max_marker_characters = max(1, int(max_marker_characters))
        self.max_total_characters = max(1, int(max_total_characters))
        self._translation_lock = threading.RLock()

    def _validate_markers(self, markers: list[tuple[int, int, str]]) -> None:
        if len(markers) > self.max_markers:
            raise TranslationMarkerCountError(
                f"Prompt translation supports at most {self.max_markers} markers per request."
            )
        for _start, _end, segment in markers:
            if len(segment) > self.max_marker_characters:
                raise TranslationMarkerSizeError(
                    "Prompt translation supports at most "
                    f"{self.max_marker_characters} characters in one marker."
                )
        total_characters = sum(len(segment) for _start, _end, segment in markers)
        if total_characters > self.max_total_characters:
            raise TranslationTotalSizeError(
                "Prompt translation supports at most "
                f"{self.max_total_characters} marker characters per request."
            )

    def _translate_cached(self, text: str, settings: PromptTranslationSettings) -> str:
        key = (settings.provider, settings.source, settings.target, text)
        with self._translation_lock:
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
            provider=normalize_prompt_translation_provider(settings.provider),
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
            translated_segments = {segment.strip(): segment.strip() for _, _, segment in markers}
        else:
            self._validate_markers(markers)
            translated_segments: dict[str, str] = {}
            for _start, _end, segment in markers:
                marker_text = segment.strip()
                if marker_text not in translated_segments:
                    translated_segments[marker_text] = (
                        self._translate_cached(marker_text, settings) if marker_text else ""
                    )

        output: list[str] = []
        cursor = 0
        for start, end, segment in markers:
            output.append(value[cursor:start])
            output.append(translated_segments[segment.strip()])
            cursor = end
        output.append(value[cursor:])
        return "".join(output)


_DEFAULT_TRANSLATION_SERVICE = PromptTranslationService()


def strip_prompt_translation_markers(text: str) -> str:
    return translate_prompt_markers(
        text,
        PromptTranslationSettings(provider=PROMPT_TRANSLATION_PROVIDER_OFF),
    )


def translate_prompt_markers(text: str, settings: PromptTranslationSettings | None = None) -> str:
    """Compatibility facade used by synchronous ComfyUI node execution."""

    return _DEFAULT_TRANSLATION_SERVICE.translate_prompt(text, settings)
