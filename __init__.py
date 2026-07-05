# -*- coding: utf-8 -*-
import logging

from .nodes import (
    EasyUseAnimaAIOGenerator,
    EasyUseAnimaDetailerAlignHook,
    EasyUseAnimaArtistMixConditioning,
    EasyUseAnimaInput,
    EasyUseAnimaImageScaleByMultiple,
    EasyUseAnimaLoraPreset,
    EasyUseAnimaNAIARandomPrompt,
    EasyUseAnimaPromptDataConditioning,
    EasyUseAnimaPromptDataUnpack,
    EasyUseAnimaPromptBuilder,
    EasyUseAnimaPromptCorrector,
    EasyUseAnimaPromptCorrectorSimple,
    EasyUseAnimaPromptStudio,
    EasyUseAnimaPromptStudioAdvanced,
    EasyUseAnimaPromptStudioAdvancedV2,
    EasyUseAnimaPromptStudioRegional,
    EasyUseAnimaRegionalConditioning,
    EasyUseAnimaWildcard,
)
from . import api  # noqa: F401 - registers ComfyUI HTTP routes
from .wildcard_engine import ensure_default_wildcard_root

logger = logging.getLogger("ComfyUI-EasyUseAnima")

try:
    ensure_default_wildcard_root()
except OSError as exc:
    logger.warning("EasyUse Anima wildcard folder could not be initialized: %s", exc)

NODE_CLASS_MAPPINGS = {
    "EasyUseAnimaAIOGenerator": EasyUseAnimaAIOGenerator,
    "EasyUseAnimaDetailerAlignHook": EasyUseAnimaDetailerAlignHook,
    "EasyUseAnimaArtistMixConditioning": EasyUseAnimaArtistMixConditioning,
    "EasyUseAnimaInput": EasyUseAnimaInput,
    "EasyUseAnimaImageScaleByMultiple": EasyUseAnimaImageScaleByMultiple,
    "EasyUseAnimaLoraPreset": EasyUseAnimaLoraPreset,
    "EasyUseAnimaNAIARandomPrompt": EasyUseAnimaNAIARandomPrompt,
    "EasyUseAnimaPromptDataConditioning": EasyUseAnimaPromptDataConditioning,
    "EasyUseAnimaPromptDataUnpack": EasyUseAnimaPromptDataUnpack,
    "EasyUseAnimaPromptBuilder": EasyUseAnimaPromptBuilder,
    "EasyUseAnimaPromptCorrector": EasyUseAnimaPromptCorrector,
    "EasyUseAnimaPromptCorrectorSimple": EasyUseAnimaPromptCorrectorSimple,
    "EasyUseAnimaPromptStudio": EasyUseAnimaPromptStudio,
    "EasyUseAnimaPromptStudioAdvanced": EasyUseAnimaPromptStudioAdvanced,
    "EasyUseAnimaPromptStudioAdvancedV2": EasyUseAnimaPromptStudioAdvancedV2,
    "EasyUseAnimaPromptStudioRegional": EasyUseAnimaPromptStudioRegional,
    "EasyUseAnimaRegionalConditioning": EasyUseAnimaRegionalConditioning,
    "EasyUseAnimaWildcard": EasyUseAnimaWildcard,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "EasyUseAnimaAIOGenerator": "Anima AiO Generator",
    "EasyUseAnimaDetailerAlignHook": "Anima Detailer Align Hook",
    "EasyUseAnimaArtistMixConditioning": "Anima Artist Mix Conditioning",
    "EasyUseAnimaInput": "Easy Use Anima Input",
    "EasyUseAnimaImageScaleByMultiple": "Anima Image Scale By Multiple",
    "EasyUseAnimaLoraPreset": "Anima LoRA Preset",
    "EasyUseAnimaNAIARandomPrompt": "Anima NAIA Random Prompt",
    "EasyUseAnimaPromptDataConditioning": "Anima Prompt Data Conditioning",
    "EasyUseAnimaPromptDataUnpack": "EASYUSE_ANIMA_PROMPT_DATA",
    "EasyUseAnimaPromptBuilder": "Anima Prompt Builder",
    "EasyUseAnimaPromptCorrector": "Anima Prompt Corrector",
    "EasyUseAnimaPromptCorrectorSimple": "Anima Prompt Corrector Simple",
    "EasyUseAnimaPromptStudio": "Anima Prompt Studio",
    "EasyUseAnimaPromptStudioAdvanced": "Anima Prompt Studio Advanced",
    "EasyUseAnimaPromptStudioAdvancedV2": "Anima Prompt Studio Advanced v2",
    "EasyUseAnimaPromptStudioRegional": "Anima Prompt Studio Regional",
    "EasyUseAnimaRegionalConditioning": "Anima Regional Conditioning",
    "EasyUseAnimaWildcard": "Anima Wildcard",
}

WEB_DIRECTORY = "./web"

__all__ = [
    "NODE_CLASS_MAPPINGS",
    "NODE_DISPLAY_NAME_MAPPINGS",
    "WEB_DIRECTORY",
]
