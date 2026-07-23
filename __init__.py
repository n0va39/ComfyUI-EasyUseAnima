# -*- coding: utf-8 -*-

from .easyuse_anima.registration import (  # noqa: F401 - mapped class attributes stay public
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
    NODE_CLASS_MAPPINGS,
    NODE_DISPLAY_NAME_MAPPINGS,
)
from . import api
from .easyuse_anima.bootstrap import initialize as _initialize
from .wildcard_engine import ensure_default_wildcard_root


def _load_comfy_nodes():
    try:
        import nodes as comfy_nodes  # type: ignore
    except Exception:
        return None
    return comfy_nodes


_initialize(
    register_routes=api.register_routes,
    initialize_wildcards=ensure_default_wildcard_root,
    load_comfy_nodes=_load_comfy_nodes,
)

WEB_DIRECTORY = "./web"

__all__ = [
    "NODE_CLASS_MAPPINGS",
    "NODE_DISPLAY_NAME_MAPPINGS",
    "WEB_DIRECTORY",
]
