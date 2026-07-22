# -*- coding: utf-8 -*-
import logging

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
from .easyuse_anima.registration import (
    NODE_CLASS_MAPPINGS,
    NODE_DISPLAY_NAME_MAPPINGS,
)
from . import api  # noqa: F401 - registers ComfyUI HTTP routes
from .wildcard_engine import ensure_default_wildcard_root

logger = logging.getLogger("ComfyUI-EasyUseAnima")

try:
    ensure_default_wildcard_root()
except OSError as exc:
    logger.warning("EasyUse Anima wildcard folder could not be initialized: %s", exc)

WEB_DIRECTORY = "./web"

__all__ = [
    "NODE_CLASS_MAPPINGS",
    "NODE_DISPLAY_NAME_MAPPINGS",
    "WEB_DIRECTORY",
]
