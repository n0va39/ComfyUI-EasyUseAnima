"""ComfyUI adapters for ANIMA prompt correction."""

from __future__ import annotations

import json

from ..common.serialization import _stable_change_key
from ..common.values import _as_bool
from ..prompt.correction import (
    _prompt_translation_change_key,
    _split_tag_text,
    _translate_prompt_text,
)
from ..prompt.fields import (
    DEFAULT_QUALITY_TAGS,
    DEFAULT_TRAILING_QUALITY_TAGS,
    _correct_builder_prompt,
    _filter_metadata_prompt,
    _join_prompt_tokens,
)
from ..settings.service import resolve_metadata_filter_words
from ..prompt.anima import correct_prompt, load_knowledge_base


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


class EasyUseAnimaPromptBuilder:
    """Build cleaned ANIMA prompts for NAIA and Anima Mod Guidance workflows."""

    DESCRIPTION = (
        "Combines quality, trigger, LoRA trigger, body, and trailing prompt fields into "
        "ANIMA-friendly prompt outputs, including metadata and Mod Guidance outputs."
    )
    OUTPUT_TOOLTIPS = (
        "Final positive prompt. When Mod Guidance is enabled, leading quality tags are excluded.",
        "Quality prompt text intended for Anima Mod Guidance.",
        "Boolean flag passed through for Anima Mod Guidance workflow control.",
        "Prompt text for metadata, independent from Mod Guidance routing and metadata filters.",
    )

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "use_anima_mod_guidance": ("BOOLEAN", {
                    "default": False,
                    "tooltip": (
                        "true: output prompt excludes quality fields and sends them "
                        "through anima_mod_guidance_quality_tags."
                    ),
                }),
                "pin_trigger_tags_to_front": ("BOOLEAN", {
                    "default": False,
                    "tooltip": (
                        "true: keep trigger/artist and LoRA trigger fields at the very front "
                        "instead of placing quality tags before them."
                    ),
                }),
                "lora_trigger_tags": ("STRING", {
                    "multiline": False,
                    "default": "",
                    "tooltip": "One-line trigger tags received from a LoRA manager or pasted manually.",
                }),
                "quality_tags": ("STRING", {
                    "multiline": True,
                    "default": DEFAULT_QUALITY_TAGS,
                    "tooltip": "Leading quality tags. With AMG enabled, these are excluded from prompt output.",
                }),
                "trigger_and_artist_tags": ("STRING", {
                    "multiline": True,
                    "default": "",
                    "tooltip": "Manual model triggers and @artist tags.",
                }),
                "prompt": ("STRING", {
                    "multiline": True,
                    "default": "",
                    "tooltip": "Main prompt body. This is the expected place for NAIA output.",
                }),
                "trailing_quality_tags": ("STRING", {
                    "multiline": True,
                    "default": DEFAULT_TRAILING_QUALITY_TAGS,
                    "tooltip": "Trailing quality or style tags.",
                }),
            }
        }

    RETURN_TYPES = ("STRING", "STRING", "BOOLEAN", "STRING")
    RETURN_NAMES = (
        "prompt",
        "anima_mod_guidance_quality_tags",
        "use_anima_mod_guidance",
        "metadata_prompt",
    )
    FUNCTION = "build"
    CATEGORY = "EasyUse Anima/Prompt"

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        return _stable_change_key({
            "mode": "prompt_builder",
            "metadata_filter_words": resolve_metadata_filter_words(),
            "prompt_translation": _prompt_translation_change_key(),
            **{key: str(value) for key, value in sorted(kwargs.items())},
        })

    def build(
        self,
        use_anima_mod_guidance: bool,
        pin_trigger_tags_to_front: bool,
        quality_tags: str,
        trigger_and_artist_tags: str,
        lora_trigger_tags: str,
        prompt: str,
        trailing_quality_tags: str,
    ):
        use_amg = _as_bool(use_anima_mod_guidance, False)
        pin_triggers = _as_bool(pin_trigger_tags_to_front, False)
        quality_tags = _translate_prompt_text(quality_tags)
        trigger_and_artist_tags = _translate_prompt_text(trigger_and_artist_tags)
        lora_trigger_tags = _translate_prompt_text(lora_trigger_tags)
        prompt = _translate_prompt_text(prompt)
        trailing_quality_tags = _translate_prompt_text(trailing_quality_tags)

        trigger_prompt = _join_prompt_tokens(trigger_and_artist_tags, lora_trigger_tags)
        quality_prompt = _join_prompt_tokens(quality_tags)
        body_prompt = _join_prompt_tokens(prompt)
        trailing_prompt = _join_prompt_tokens(trailing_quality_tags)

        if pin_triggers:
            metadata_body = _correct_builder_prompt(
                _join_prompt_tokens(quality_tags, body_prompt)
            )
            regular_prompt = _join_prompt_tokens(trigger_prompt, metadata_body, trailing_prompt)
            amg_prompt = _join_prompt_tokens(
                trigger_prompt,
                _correct_builder_prompt(body_prompt),
                trailing_prompt,
            )
            metadata_prompt = regular_prompt
        else:
            metadata_core = _correct_builder_prompt(
                _join_prompt_tokens(
                    quality_tags,
                    trigger_prompt,
                    body_prompt,
                ),
                artist_overrides=trigger_prompt,
            )
            metadata_prompt = _join_prompt_tokens(metadata_core, trailing_prompt)
            regular_prompt = metadata_prompt
            amg_core = _correct_builder_prompt(
                _join_prompt_tokens(trigger_prompt, body_prompt),
                artist_overrides=trigger_prompt,
            )
            amg_prompt = _join_prompt_tokens(amg_core, trailing_prompt)

        metadata_prompt = _filter_metadata_prompt(
            metadata_prompt,
            resolve_metadata_filter_words(),
        )
        output_prompt = amg_prompt if use_amg else regular_prompt

        return (
            output_prompt,
            quality_prompt,
            use_amg,
            metadata_prompt,
        )


class EasyUseAnimaPromptStudio(EasyUseAnimaPromptBuilder):
    """Prompt Builder variant with enhanced front-end editing helpers."""

    DESCRIPTION = (
        "An enhanced Prompt Builder with front-end editing, autocomplete, and tag highlighting helpers."
    )

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "use_anima_mod_guidance": ("BOOLEAN", {
                    "default": False,
                    "tooltip": (
                        "true: output prompt excludes quality fields and sends them "
                        "through anima_mod_guidance_quality_tags."
                    ),
                }),
                "pin_trigger_tags_to_front": ("BOOLEAN", {
                    "default": False,
                    "tooltip": (
                        "true: keep trigger/artist and LoRA trigger fields at the very front "
                        "instead of placing quality tags before them."
                    ),
                }),
                "lora_trigger_tags": ("STRING", {
                    "multiline": False,
                    "default": "",
                    "tooltip": "One-line trigger tags received from a LoRA manager or pasted manually.",
                }),
                "quality_tags": ("STRING", {
                    "multiline": True,
                    "default": DEFAULT_QUALITY_TAGS,
                    "tooltip": "Leading quality tags. With AMG enabled, these are excluded from prompt output.",
                }),
                "trigger_and_artist_tags": ("STRING", {
                    "multiline": True,
                    "default": "",
                    "tooltip": "Manual model triggers and @artist tags.",
                }),
                "prompt": ("STRING", {
                    "multiline": True,
                    "default": "",
                    "tooltip": "Main prompt body. This is the expected place for NAIA output.",
                }),
                "trailing_quality_tags": ("STRING", {
                    "multiline": True,
                    "default": DEFAULT_TRAILING_QUALITY_TAGS,
                    "tooltip": "Trailing quality or style tags.",
                }),
            }
        }

    CATEGORY = "EasyUse Anima/Prompt"

    def build(
        self,
        use_anima_mod_guidance: bool,
        pin_trigger_tags_to_front: bool,
        quality_tags: str,
        trigger_and_artist_tags: str,
        lora_trigger_tags: str,
        prompt: str,
        trailing_quality_tags: str,
    ):
        result = super().build(
            use_anima_mod_guidance,
            pin_trigger_tags_to_front,
            quality_tags,
            trigger_and_artist_tags,
            lora_trigger_tags,
            prompt,
            trailing_quality_tags,
        )
        return {
            "ui": {
                "prompt_studio_inputs": [{
                    "lora_trigger_tags": str(lora_trigger_tags or ""),
                    "quality_tags": str(quality_tags or ""),
                    "trigger_and_artist_tags": str(trigger_and_artist_tags or ""),
                    "prompt": str(prompt or ""),
                    "trailing_quality_tags": str(trailing_quality_tags or ""),
                }]
            },
            "result": result,
        }


__all__ = (
    "EasyUseAnimaPromptBuilder",
    "EasyUseAnimaPromptCorrector",
    "EasyUseAnimaPromptCorrectorSimple",
    "EasyUseAnimaPromptStudio",
)
