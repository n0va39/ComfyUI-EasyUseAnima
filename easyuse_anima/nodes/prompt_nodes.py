"""ComfyUI adapters for ANIMA prompt correction."""

from __future__ import annotations

import json

from ..common.serialization import _stable_change_key
from ..prompt.correction import (
    _prompt_translation_change_key,
    _split_tag_text,
    _translate_prompt_text,
)

try:
    from ...anima_prompt import correct_prompt, load_knowledge_base
except ImportError:
    from anima_prompt import correct_prompt, load_knowledge_base


def _bind_prompt_node_runtime(*, resolve_helper) -> None:
    global _stable_change_key, _prompt_translation_change_key
    global _split_tag_text, _translate_prompt_text, correct_prompt, load_knowledge_base

    def runtime_helper(name):
        def call(*args, **kwargs):
            return resolve_helper(name)(*args, **kwargs)

        return call

    _stable_change_key = runtime_helper("_stable_change_key")
    _prompt_translation_change_key = runtime_helper("_prompt_translation_change_key")
    _split_tag_text = runtime_helper("_split_tag_text")
    _translate_prompt_text = runtime_helper("_translate_prompt_text")
    correct_prompt = runtime_helper("correct_prompt")
    load_knowledge_base = runtime_helper("load_knowledge_base")


def _correct_prompt_with_report(
    prompt: str,
    artist_overrides: str,
    artist_exclusions: str,
) -> tuple[str, str]:
    prompt = _translate_prompt_text(prompt)
    try:
        kb = load_knowledge_base(allow_missing=True)
        result = correct_prompt(
            str(prompt or ""),
            profile="prompt",
            knowledge_base=kb,
            validate_artist_tags=False,
            artist_overrides=_split_tag_text(artist_overrides),
            artist_exclusions=_split_tag_text(artist_exclusions),
        )
    except Exception as exc:
        raise RuntimeError(f"[EasyUse Anima] prompt correction failed: {exc}") from exc

    report = {
        "changed": result.changed,
        "unknown_tags": list(result.unknown_tags),
        "duplicate_tags": list(result.duplicate_tags),
        "warnings": list(result.warnings),
        "sections": result.report.get("sections", []),
    }
    return (
        result.text,
        json.dumps(report, ensure_ascii=False, indent=2),
    )


class EasyUseAnimaPromptCorrector:
    """ANIMA prompt order correction node."""

    DESCRIPTION = (
        "Normalizes ANIMA prompt text, keeps natural-language casing, reorders known "
        "ANIMA sections, and reports unknown or duplicate tags."
    )
    OUTPUT_TOOLTIPS = (
        "Prompt text after ANIMA ordering and syntax cleanup.",
        "JSON report containing changed state, unknown tags, duplicate tags, warnings, and sections.",
    )

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "prompt": ("STRING", {
                    "multiline": True,
                    "default": "",
                    "tooltip": "Comma-separated prompt text to normalize and reorder for ANIMA.",
                }),
                "artist_overrides": ("STRING", {
                    "multiline": True,
                    "default": "",
                    "tooltip": "Comma- or newline-separated manual triggers to treat like artist tags.",
                }),
                "artist_exclusions": ("STRING", {
                    "multiline": True,
                    "default": "",
                    "tooltip": "Comma- or newline-separated triggers that must not be treated as artists.",
                }),
            }
        }

    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("corrected_prompt", "report")
    FUNCTION = "correct"
    CATEGORY = "EasyUse Anima/Prompt"

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        return _stable_change_key({
            "mode": "prompt_corrector",
            "prompt_translation": _prompt_translation_change_key(),
            **{key: str(value) for key, value in sorted(kwargs.items())},
        })

    def correct(
        self,
        prompt: str,
        artist_overrides: str,
        artist_exclusions: str,
    ):
        return _correct_prompt_with_report(prompt, artist_overrides, artist_exclusions)


class EasyUseAnimaPromptCorrectorSimple:
    """Single-input ANIMA prompt correction node."""

    DESCRIPTION = (
        "Simplified ANIMA prompt correction node. It accepts one multiline prompt "
        "and returns only the corrected prompt string."
    )
    OUTPUT_TOOLTIPS = (
        "Prompt text after ANIMA ordering and syntax cleanup.",
    )

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "prompt": ("STRING", {
                    "multiline": True,
                    "default": "",
                    "tooltip": "Comma-separated prompt text to normalize and reorder for ANIMA.",
                }),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("prompt",)
    FUNCTION = "correct"
    CATEGORY = "EasyUse Anima/Prompt"

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        return _stable_change_key({
            "mode": "prompt_corrector_simple",
            "prompt_translation": _prompt_translation_change_key(),
            **{key: str(value) for key, value in sorted(kwargs.items())},
        })

    def correct(self, prompt: str):
        corrected, _report = _correct_prompt_with_report(prompt, "", "")
        return (corrected,)


__all__ = ("EasyUseAnimaPromptCorrector", "EasyUseAnimaPromptCorrectorSimple")
