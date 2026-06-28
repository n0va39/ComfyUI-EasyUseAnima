# -*- coding: utf-8 -*-
from .nodes import (
    EasyUseAnimaDetailerAlignHook,
    EasyUseAnimaLoraPreset,
    EasyUseAnimaNAIARandomPrompt,
    EasyUseAnimaPromptBuilder,
    EasyUseAnimaPromptCorrector,
    EasyUseAnimaPromptStudio,
    EasyUseAnimaPromptStudioAdvanced,
    EasyUseAnimaSAM3Context,
    EasyUseAnimaSAM3Detailer,
)
from . import api  # noqa: F401 - registers ComfyUI HTTP routes

NODE_CLASS_MAPPINGS = {
    "EasyUseAnimaDetailerAlignHook": EasyUseAnimaDetailerAlignHook,
    "EasyUseAnimaLoraPreset": EasyUseAnimaLoraPreset,
    "EasyUseAnimaNAIARandomPrompt": EasyUseAnimaNAIARandomPrompt,
    "EasyUseAnimaPromptBuilder": EasyUseAnimaPromptBuilder,
    "EasyUseAnimaPromptCorrector": EasyUseAnimaPromptCorrector,
    "EasyUseAnimaPromptStudio": EasyUseAnimaPromptStudio,
    "EasyUseAnimaPromptStudioAdvanced": EasyUseAnimaPromptStudioAdvanced,
    "EasyUseAnimaSAM3Context": EasyUseAnimaSAM3Context,
    "EasyUseAnimaSAM3Detailer": EasyUseAnimaSAM3Detailer,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "EasyUseAnimaDetailerAlignHook": "Anima Detailer Align Hook",
    "EasyUseAnimaLoraPreset": "Anima LoRA Preset",
    "EasyUseAnimaNAIARandomPrompt": "Anima NAIA Random Prompt",
    "EasyUseAnimaPromptBuilder": "Anima Prompt Builder",
    "EasyUseAnimaPromptCorrector": "Anima Prompt Corrector",
    "EasyUseAnimaPromptStudio": "Anima Prompt Studio",
    "EasyUseAnimaPromptStudioAdvanced": "Anima Prompt Studio Advanced",
    "EasyUseAnimaSAM3Context": "Anima SAM3 Context",
    "EasyUseAnimaSAM3Detailer": "Anima SAM3 Detailer",
}

WEB_DIRECTORY = "./web"

__all__ = [
    "NODE_CLASS_MAPPINGS",
    "NODE_DISPLAY_NAME_MAPPINGS",
    "WEB_DIRECTORY",
]
