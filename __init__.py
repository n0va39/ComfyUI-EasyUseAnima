# -*- coding: utf-8 -*-
import logging

from .nodes import (
    EasyUseAnimaDetailerAlignHook,
    EasyUseAnimaArtistMixConditioning,
    EasyUseAnimaImageScaleByMultiple,
    EasyUseAnimaLoraPreset,
    EasyUseAnimaNAIARandomPrompt,
    EasyUseAnimaPromptDataConditioning,
    EasyUseAnimaPromptDataStrings,
    EasyUseAnimaPromptDataUnpack,
    EasyUseAnimaPromptBuilder,
    EasyUseAnimaPromptCorrector,
    EasyUseAnimaPromptStudio,
    EasyUseAnimaPromptStudioAdvanced,
    EasyUseAnimaPromptStudioAdvancedV2,
    EasyUseAnimaPromptStudioRegional,
    EasyUseAnimaRegionalConditioning,
    EasyUseAnimaWildcard,
    EasyUseAnimaSAM3Context,
    EasyUseAnimaSAM3Detailer,
)
from . import api  # noqa: F401 - registers ComfyUI HTTP routes
from .wildcard_engine import ensure_default_wildcard_root

logger = logging.getLogger("ComfyUI-EasyUseAnima")

try:
    ensure_default_wildcard_root()
except OSError as exc:
    logger.warning("EasyUse Anima wildcard folder could not be initialized: %s", exc)

NODE_CLASS_MAPPINGS = {
    "EasyUseAnimaDetailerAlignHook": EasyUseAnimaDetailerAlignHook,
    "EasyUseAnimaArtistMixConditioning": EasyUseAnimaArtistMixConditioning,
    "EasyUseAnimaImageScaleByMultiple": EasyUseAnimaImageScaleByMultiple,
    "EasyUseAnimaLoraPreset": EasyUseAnimaLoraPreset,
    "EasyUseAnimaNAIARandomPrompt": EasyUseAnimaNAIARandomPrompt,
    "EasyUseAnimaPromptDataConditioning": EasyUseAnimaPromptDataConditioning,
    "EasyUseAnimaPromptDataStrings": EasyUseAnimaPromptDataStrings,
    "EasyUseAnimaPromptDataUnpack": EasyUseAnimaPromptDataUnpack,
    "EasyUseAnimaPromptBuilder": EasyUseAnimaPromptBuilder,
    "EasyUseAnimaPromptCorrector": EasyUseAnimaPromptCorrector,
    "EasyUseAnimaPromptStudio": EasyUseAnimaPromptStudio,
    "EasyUseAnimaPromptStudioAdvanced": EasyUseAnimaPromptStudioAdvanced,
    "EasyUseAnimaPromptStudioAdvancedV2": EasyUseAnimaPromptStudioAdvancedV2,
    "EasyUseAnimaPromptStudioRegional": EasyUseAnimaPromptStudioRegional,
    "EasyUseAnimaRegionalConditioning": EasyUseAnimaRegionalConditioning,
    "EasyUseAnimaWildcard": EasyUseAnimaWildcard,
    "EasyUseAnimaSAM3Context": EasyUseAnimaSAM3Context,
    "EasyUseAnimaSAM3Detailer": EasyUseAnimaSAM3Detailer,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "EasyUseAnimaDetailerAlignHook": "Anima Detailer Align Hook",
    "EasyUseAnimaArtistMixConditioning": "Anima Artist Mix Conditioning",
    "EasyUseAnimaImageScaleByMultiple": "Anima Image Scale By Multiple",
    "EasyUseAnimaLoraPreset": "Anima LoRA Preset",
    "EasyUseAnimaNAIARandomPrompt": "Anima NAIA Random Prompt",
    "EasyUseAnimaPromptDataConditioning": "Anima Prompt Data Conditioning",
    "EasyUseAnimaPromptDataStrings": "Anima Prompt Data Strings",
    "EasyUseAnimaPromptDataUnpack": "EASYUSE_ANIMA_PROMPT_DATA",
    "EasyUseAnimaPromptBuilder": "Anima Prompt Builder",
    "EasyUseAnimaPromptCorrector": "Anima Prompt Corrector",
    "EasyUseAnimaPromptStudio": "Anima Prompt Studio",
    "EasyUseAnimaPromptStudioAdvanced": "Anima Prompt Studio Advanced",
    "EasyUseAnimaPromptStudioAdvancedV2": "Anima Prompt Studio Advanced v2",
    "EasyUseAnimaPromptStudioRegional": "Anima Prompt Studio Regional",
    "EasyUseAnimaRegionalConditioning": "Anima Regional Conditioning",
    "EasyUseAnimaWildcard": "Anima Wildcard",
    "EasyUseAnimaSAM3Context": "Anima SAM3 Context",
    "EasyUseAnimaSAM3Detailer": "Anima SAM3 Detailer",
}

WEB_DIRECTORY = "./web"

__all__ = [
    "NODE_CLASS_MAPPINGS",
    "NODE_DISPLAY_NAME_MAPPINGS",
    "WEB_DIRECTORY",
]
