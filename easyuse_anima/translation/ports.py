"""Narrow process translation service port."""

from __future__ import annotations

from typing import Protocol

from .contracts import PromptTranslationSettings


class PromptTranslationPort(Protocol):
    def translate_prompt(
        self,
        text: str,
        settings: PromptTranslationSettings | None = None,
    ) -> str: ...

    def close(self) -> None: ...


__all__ = ()
