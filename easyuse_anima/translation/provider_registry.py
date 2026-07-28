"""Private prompt translation provider registry ownership."""

from __future__ import annotations

import threading
from collections.abc import Callable, Mapping

from .contracts import (
    PromptTranslationError,
    TranslationProvider,
    TranslationProviderUnavailableError,
)


class _TranslationProviderRegistry:
    def __init__(
        self,
        factories: Mapping[str, Callable[[], TranslationProvider]],
    ):
        self._factories = dict(factories)
        self._instances: dict[str, TranslationProvider] = {}
        self._lock = threading.RLock()

    def get(self, provider: str) -> TranslationProvider:
        name = str(provider or "").strip().lower()
        with self._lock:
            instance = self._instances.get(name)
            if instance is not None:
                return instance
            factory = self._factories.get(name)
            if factory is None:
                raise TranslationProviderUnavailableError()
            try:
                instance = factory()
            except PromptTranslationError:
                raise
            except Exception as exc:
                raise TranslationProviderUnavailableError() from exc
            self._instances[name] = instance
            return instance


__all__ = ()
