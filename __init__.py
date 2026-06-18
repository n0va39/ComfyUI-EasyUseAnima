# -*- coding: utf-8 -*-
from .nodes import (
    EasyUseAnimaNAIARandomPrompt,
    EasyUseAnimaPromptBuilder,
    EasyUseAnimaPromptCorrector,
    EasyUseAnimaPromptStudio,
)
from . import api  # noqa: F401 - registers ComfyUI HTTP routes

NODE_CLASS_MAPPINGS = {
    "EasyUseAnimaNAIARandomPrompt": EasyUseAnimaNAIARandomPrompt,
    "EasyUseAnimaPromptBuilder": EasyUseAnimaPromptBuilder,
    "EasyUseAnimaPromptCorrector": EasyUseAnimaPromptCorrector,
    "EasyUseAnimaPromptStudio": EasyUseAnimaPromptStudio,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "EasyUseAnimaNAIARandomPrompt": "Anima NAIA Random Prompt",
    "EasyUseAnimaPromptBuilder": "Anima Prompt Builder",
    "EasyUseAnimaPromptCorrector": "Anima Prompt Corrector",
    "EasyUseAnimaPromptStudio": "Anima Prompt Studio",
}

WEB_DIRECTORY = "./web"

__all__ = [
    "NODE_CLASS_MAPPINGS",
    "NODE_DISPLAY_NAME_MAPPINGS",
    "WEB_DIRECTORY",
]
