# -*- coding: utf-8 -*-
from .nodes import EasyUseAnimaNAIARandomPrompt

NODE_CLASS_MAPPINGS = {
    "EasyUseAnimaNAIARandomPrompt": EasyUseAnimaNAIARandomPrompt,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "EasyUseAnimaNAIARandomPrompt": "EasyUse Anima NAIA Random Prompt",
}

WEB_DIRECTORY = "./web"

__all__ = [
    "NODE_CLASS_MAPPINGS",
    "NODE_DISPLAY_NAME_MAPPINGS",
    "WEB_DIRECTORY",
]
