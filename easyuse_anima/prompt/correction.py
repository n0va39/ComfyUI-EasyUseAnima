"""Prompt correction and translation helpers."""

from __future__ import annotations

try:
    from ...prompt_translation import has_prompt_translation_markers, translate_prompt_markers
    from ...settings import resolve_prompt_translation_settings
except ImportError:
    from prompt_translation import has_prompt_translation_markers, translate_prompt_markers
    from settings import resolve_prompt_translation_settings


def _bind_prompt_correction_runtime(*, resolve_helper) -> None:
    global has_prompt_translation_markers, translate_prompt_markers
    global resolve_prompt_translation_settings

    def runtime_helper(name):
        def call(*args, **kwargs):
            return resolve_helper(name)(*args, **kwargs)

        return call

    has_prompt_translation_markers = runtime_helper("has_prompt_translation_markers")
    translate_prompt_markers = runtime_helper("translate_prompt_markers")
    resolve_prompt_translation_settings = runtime_helper(
        "resolve_prompt_translation_settings"
    )


def _split_tag_text(value: str) -> list[str]:
    if not value:
        return []
    parts: list[str] = []
    for line in str(value).splitlines():
        parts.extend(part.strip() for part in line.split(","))
    return [part for part in parts if part]


def _translate_prompt_text(value: str) -> str:
    text = str(value or "")
    if not text or not has_prompt_translation_markers(text):
        return text
    return translate_prompt_markers(text, resolve_prompt_translation_settings())


def _prompt_translation_change_key() -> dict[str, str]:
    settings = resolve_prompt_translation_settings()
    return {
        "provider": settings.provider,
        "source": settings.source,
        "target": settings.target,
    }


__all__ = ()
