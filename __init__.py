# -*- coding: utf-8 -*-
from .nodes import (
    EasyUseAnimaLoraPreset,
    EasyUseAnimaNAIARandomPrompt,
    EasyUseAnimaPromptBuilder,
    EasyUseAnimaPromptCorrector,
    EasyUseAnimaPromptStudio,
    EasyUseAnimaPromptStudioAdvanced,
)
from . import api  # noqa: F401 - registers ComfyUI HTTP routes

NODE_CLASS_MAPPINGS = {
    "EasyUseAnimaLoraPreset": EasyUseAnimaLoraPreset,
    "EasyUseAnimaNAIARandomPrompt": EasyUseAnimaNAIARandomPrompt,
    "EasyUseAnimaPromptBuilder": EasyUseAnimaPromptBuilder,
    "EasyUseAnimaPromptCorrector": EasyUseAnimaPromptCorrector,
    "EasyUseAnimaPromptStudio": EasyUseAnimaPromptStudio,
    "EasyUseAnimaPromptStudioAdvanced": EasyUseAnimaPromptStudioAdvanced,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "EasyUseAnimaLoraPreset": "Anima LoRA Preset",
    "EasyUseAnimaNAIARandomPrompt": "Anima NAIA Random Prompt",
    "EasyUseAnimaPromptBuilder": "Anima Prompt Builder",
    "EasyUseAnimaPromptCorrector": "Anima Prompt Corrector",
    "EasyUseAnimaPromptStudio": "Anima Prompt Studio",
    "EasyUseAnimaPromptStudioAdvanced": "Anima Prompt Studio Advanced",
}

WEB_DIRECTORY = "./web"

__all__ = [
    "NODE_CLASS_MAPPINGS",
    "NODE_DISPLAY_NAME_MAPPINGS",
    "WEB_DIRECTORY",
]
