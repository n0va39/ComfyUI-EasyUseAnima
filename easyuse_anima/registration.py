"""Pure ComfyUI node mapping composition for EasyUse Anima."""

from .nodes.aio_hook_nodes import EasyUseAnimaAIOHookCombine
from .nodes.aio_nodes import EasyUseAnimaAIOGenerator, EasyUseAnimaInput
from .nodes.anima_29b_nodes import EasyUseAnima29BLoraStackLoader
from .nodes.civitai_nodes import EasyUseAnimaCivitaiLookup
from .nodes.image_nodes import (
    EasyUseAnimaDetailerAlignHook,
    EasyUseAnimaImageScaleByMultiple,
)
from .nodes.image_output_nodes import EasyUseAnimaImageMetadata, EasyUseAnimaSaveImage
from .nodes.lora_nodes import EasyUseAnimaLoraPreset
from .nodes.naia_nodes import EasyUseAnimaNAIARandomPrompt
from .nodes.prompt_advanced_nodes import (
    EasyUseAnimaPromptStudioAdvanced,
    EasyUseAnimaPromptStudioAdvancedV2,
)
from .nodes.prompt_data_nodes import (
    EasyUseAnimaArtistMixConditioning,
    EasyUseAnimaPromptDataConditioning,
    EasyUseAnimaPromptDataUnpack,
)
from .nodes.prompt_lora_nodes import EasyUseAnimaPromptStudioAdvancedLora
from .nodes.prompt_nodes import (
    EasyUseAnimaPromptBuilder,
    EasyUseAnimaPromptCorrector,
    EasyUseAnimaPromptCorrectorSimple,
    EasyUseAnimaPromptStudio,
)
from .nodes.regional_nodes import (
    EasyUseAnimaPromptStudioRegional,
    EasyUseAnimaRegionalConditioning,
)
from .nodes.wildcard_nodes import EasyUseAnimaWildcard, EasyUseAnimaWildcardLora

NODE_CLASS_MAPPINGS = {
    "EasyUseAnima29BLoraStackLoader": EasyUseAnima29BLoraStackLoader,
    "EasyUseAnimaAIOGenerator": EasyUseAnimaAIOGenerator,
    "EasyUseAnimaAIOHookCombine": EasyUseAnimaAIOHookCombine,
    "EasyUseAnimaDetailerAlignHook": EasyUseAnimaDetailerAlignHook,
    "EasyUseAnimaArtistMixConditioning": EasyUseAnimaArtistMixConditioning,
    "EasyUseAnimaInput": EasyUseAnimaInput,
    "EasyUseAnimaImageScaleByMultiple": EasyUseAnimaImageScaleByMultiple,
    "EasyUseAnimaImageMetadata": EasyUseAnimaImageMetadata,
    "EasyUseAnimaCivitaiLookup": EasyUseAnimaCivitaiLookup,
    "EasyUseAnimaSaveImage": EasyUseAnimaSaveImage,
    "EasyUseAnimaLoraPreset": EasyUseAnimaLoraPreset,
    "EasyUseAnimaNAIARandomPrompt": EasyUseAnimaNAIARandomPrompt,
    "EasyUseAnimaPromptDataConditioning": EasyUseAnimaPromptDataConditioning,
    "EasyUseAnimaPromptDataUnpack": EasyUseAnimaPromptDataUnpack,
    "EasyUseAnimaPromptBuilder": EasyUseAnimaPromptBuilder,
    "EasyUseAnimaPromptCorrector": EasyUseAnimaPromptCorrector,
    "EasyUseAnimaPromptCorrectorSimple": EasyUseAnimaPromptCorrectorSimple,
    "EasyUseAnimaPromptStudio": EasyUseAnimaPromptStudio,
    "EasyUseAnimaPromptStudioAdvanced": EasyUseAnimaPromptStudioAdvanced,
    "EasyUseAnimaPromptStudioAdvancedLora": EasyUseAnimaPromptStudioAdvancedLora,
    "EasyUseAnimaPromptStudioAdvancedV2": EasyUseAnimaPromptStudioAdvancedV2,
    "EasyUseAnimaPromptStudioRegional": EasyUseAnimaPromptStudioRegional,
    "EasyUseAnimaRegionalConditioning": EasyUseAnimaRegionalConditioning,
    "EasyUseAnimaWildcard": EasyUseAnimaWildcard,
    "EasyUseAnimaWildcardLora": EasyUseAnimaWildcardLora,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "EasyUseAnima29BLoraStackLoader": "Anima 2.9B LoRA Stack Loader",
    "EasyUseAnimaAIOGenerator": "Anima AiO Generator",
    "EasyUseAnimaAIOHookCombine": "Anima AiO Hook Combine",
    "EasyUseAnimaDetailerAlignHook": "Anima Detailer Align Hook",
    "EasyUseAnimaArtistMixConditioning": "Anima Artist Mix Conditioning",
    "EasyUseAnimaInput": "Easy Use Anima Input",
    "EasyUseAnimaImageScaleByMultiple": "Anima Image Scale By Multiple",
    "EasyUseAnimaImageMetadata": "Easy Image Metadata",
    "EasyUseAnimaCivitaiLookup": "Easy Civitai Lookup",
    "EasyUseAnimaSaveImage": "Easy Save Image",
    "EasyUseAnimaLoraPreset": "Anima LoRA Preset",
    "EasyUseAnimaNAIARandomPrompt": "Anima NAIA Random Prompt",
    "EasyUseAnimaPromptDataConditioning": "Anima Prompt Data Conditioning",
    "EasyUseAnimaPromptDataUnpack": "EASYUSE_ANIMA_PROMPT_DATA",
    "EasyUseAnimaPromptBuilder": "Anima Prompt Builder",
    "EasyUseAnimaPromptCorrector": "Anima Prompt Corrector",
    "EasyUseAnimaPromptCorrectorSimple": "Anima Prompt Corrector Simple",
    "EasyUseAnimaPromptStudio": "Anima Prompt Studio",
    "EasyUseAnimaPromptStudioAdvanced": "Anima Prompt Studio Advanced",
    "EasyUseAnimaPromptStudioAdvancedLora": "Anima Prompt Studio Advanced LoRA",
    "EasyUseAnimaPromptStudioAdvancedV2": "Anima Prompt Studio Advanced v2",
    "EasyUseAnimaPromptStudioRegional": "Anima Prompt Studio Regional",
    "EasyUseAnimaRegionalConditioning": "Anima Regional Conditioning",
    "EasyUseAnimaWildcard": "Anima Wildcard",
    "EasyUseAnimaWildcardLora": "Anima Wildcard LoRA",
}

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"]
