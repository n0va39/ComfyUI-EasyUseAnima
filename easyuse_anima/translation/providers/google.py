"""Lazy Google prompt translation provider adapter."""

from __future__ import annotations

import html
import threading
from collections.abc import Callable
from typing import Protocol

from ..contracts import (
    DEFAULT_PROMPT_TRANSLATION_SOURCE,
    DEFAULT_PROMPT_TRANSLATION_TARGET,
    PROMPT_TRANSLATION_PROVIDER_TIMEOUT_SECONDS,
    PromptTranslationError,
    TranslationProviderUnavailableError,
    TranslationTimeoutError,
    TranslationUpstreamError,
)


class _TranslatorClient(Protocol):
    def translate(self, text: str, *, src: str, dest: str) -> object: ...


def _looks_like_timeout(exc: Exception) -> bool:
    if isinstance(exc, TimeoutError):
        return True
    return any("timeout" in cls.__name__.lower() for cls in type(exc).__mro__)


class GoogleTranslationProvider:
    """Lazy, reusable wrapper around the optional googletrans-py client."""

    def __init__(
        self,
        translator_factory: Callable[[], _TranslatorClient] | None = None,
        *,
        timeout_seconds: float = PROMPT_TRANSLATION_PROVIDER_TIMEOUT_SECONDS,
    ):
        self._translator_factory = translator_factory
        self._timeout_seconds = max(0.001, float(timeout_seconds))
        self._translator: _TranslatorClient | None = None
        self._lock = threading.RLock()

    def _create_translator(self) -> _TranslatorClient:
        if self._translator_factory is not None:
            return self._translator_factory()
        try:
            from googletrans import Translator  # type: ignore
        except ImportError as exc:
            raise TranslationProviderUnavailableError() from exc
        # googletrans-py forwards this value to its httpx.Client transport.
        return Translator(timeout=self._timeout_seconds)

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


__all__ = ("GoogleTranslationProvider",)
