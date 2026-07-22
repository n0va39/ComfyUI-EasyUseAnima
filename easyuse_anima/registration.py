"""Pure ComfyUI node mapping composition for EasyUse Anima."""

from .nodes.aio_nodes import EasyUseAnimaAIOGenerator, EasyUseAnimaInput
from .nodes.image_nodes import (
    EasyUseAnimaDetailerAlignHook,
    EasyUseAnimaImageScaleByMultiple,
)
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
from .nodes.wildcard_nodes import EasyUseAnimaWildcard


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

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"]
