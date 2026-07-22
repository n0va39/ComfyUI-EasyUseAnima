# -*- coding: utf-8 -*-

from .nodes import (  # noqa: F401 - root class attributes stay public until B-11c
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
from . import api
from .easyuse_anima.bootstrap import initialize as _initialize
from .easyuse_anima.registration import (
    NODE_CLASS_MAPPINGS,
    NODE_DISPLAY_NAME_MAPPINGS,
)
from .wildcard_engine import ensure_default_wildcard_root

_initialize(
    register_routes=api.register_routes,
    initialize_wildcards=ensure_default_wildcard_root,
)

WEB_DIRECTORY = "./web"

__all__ = [
    "NODE_CLASS_MAPPINGS",
    "NODE_DISPLAY_NAME_MAPPINGS",
    "WEB_DIRECTORY",
]
