"""ComfyUI adapters for the AiO input context."""

from __future__ import annotations

import json

from ..aio.generation_defaults import (
    AIO_GENERATION_DEFAULT_SETTINGS,
    AIO_SPECIAL_SEEDS,
)
from ..aio.generation_normalization import _normalize_aio_generation_settings
from ..aio.input_context import (
    _easy_use_anima_input_signature as _easy_use_anima_input_signature,
)
from ..aio.input_context import (
    _require_easy_use_anima_input as _require_easy_use_anima_input,
)
from ..aio.input_defaults import (
    AIO_INPUT_DEFAULT_SETTINGS,
    ANIMA_DEFAULT_CLIP_CANDIDATES,
    ANIMA_DEFAULT_DIFFUSION_MODEL_CANDIDATES,
    ANIMA_DEFAULT_VAE_CANDIDATES,
    EASY_USE_ANIMA_INPUT_SCHEMA,
    EASY_USE_ANIMA_INPUT_SETTINGS_VERSION,
)
from ..aio.legacy_generation import _run_aio_legacy_generation
from ..aio.model_preparation import _aio_lora_stack_signature
from ..aio.resources import (
    _comfy_clip_loader_types,
    _comfy_diffusion_model_names,
    _comfy_text_encoder_names,
    _comfy_vae_names,
    _normalize_aio_input_settings,
    _preferred_clip_type_default,
    _preferred_name_default,
)
from ..aio.sampling import _resolve_aio_runtime_seed
from ..common.serialization import _json_clone, _stable_change_key
from ..prompt.data import (
    PROMPT_DATA_TYPE,
    _copy_prompt_data_for_update,
    _normalize_prompt_data,
    _prompt_data_json_safe,
)

EASY_USE_ANIMA_INPUT_TYPE = "EASY_USE_ANIMA_INPUT"


def _aio_input_settings_json() -> str:
    return json.dumps(
        AIO_INPUT_DEFAULT_SETTINGS,
        ensure_ascii=False,
        separators=(",", ":"),
    )


def _aio_generation_settings_json() -> str:
    return json.dumps(
        AIO_GENERATION_DEFAULT_SETTINGS,
        ensure_ascii=False,
        separators=(",", ":"),
    )


class EasyUseAnimaInput:
    """Bundle prompt data and resource loader settings for the AiO generator."""

    DESCRIPTION = (
        "Receives EASYUSE_ANIMA_PROMPT_DATA and selected ANIMA resource names, then returns "
        "one dedicated easy use anima input context. The context stores only serializable "
        "prompt/resource data; the AiO Generator loads MODEL, CLIP, and VAE at execution "
        "time so model patches and Torch compile do not live inside a custom dict socket."
    )
    OUTPUT_TOOLTIPS = (
        "Dedicated context containing prompt data, resource metadata, and versioned loader settings.",
    )

    @classmethod
    def INPUT_TYPES(cls):
        unet_names = _comfy_diffusion_model_names()
        vae_names = _comfy_vae_names()
        clip_names = _comfy_text_encoder_names()
        clip_types = _comfy_clip_loader_types()
        return {
            "required": {
                PROMPT_DATA_TYPE: (PROMPT_DATA_TYPE, {
                    "forceInput": True,
                    "tooltip": "Structured prompt data from Anima Prompt Studio Advanced v2.",
                }),
                "unet_name": (unet_names, {
                    "default": _preferred_name_default(
                        unet_names,
                        ANIMA_DEFAULT_DIFFUSION_MODEL_CANDIDATES,
                    ),
                    "tooltip": "ANIMA diffusion model loaded with ComfyUI UNETLoader.",
                }),
                "vae_name": (vae_names, {
                    "default": _preferred_name_default(
                        vae_names,
                        ANIMA_DEFAULT_VAE_CANDIDATES,
                    ),
                    "tooltip": "VAE loaded with ComfyUI VAELoader.",
                }),
                "clip_name": (clip_names, {
                    "default": _preferred_name_default(
                        clip_names,
                        ANIMA_DEFAULT_CLIP_CANDIDATES,
                    ),
                    "tooltip": "Text encoder loaded with ComfyUI CLIPLoader.",
                }),
                "clip_type": (clip_types, {
                    "default": _preferred_clip_type_default(clip_types),
                    "tooltip": "ComfyUI CLIPLoader type. Core ANIMA uses qwen_image.",
                }),
                "input_settings": ("STRING", {
                    "multiline": True,
                    "default": _aio_input_settings_json(),
                    "hidden": True,
                    "tooltip": "Hidden versioned JSON storage for future resource settings. Kept serialized for workflow compatibility.",
                }),
            },
        }

    RETURN_TYPES = (EASY_USE_ANIMA_INPUT_TYPE,)
    RETURN_NAMES = ("easy use anima input",)
    FUNCTION = "build"
    CATEGORY = "EasyUse Anima/AiO"

    @classmethod
    def IS_CHANGED(
        cls,
        EASYUSE_ANIMA_PROMPT_DATA: str | dict | None = None,
        unet_name: str = "",
        vae_name: str = "",
        clip_name: str = "",
        clip_type: str = "",
        input_settings: str | dict | None = None,
        **kwargs,
    ):
        return _stable_change_key({
            "mode": "easy_use_anima_input",
            "prompt_data": _prompt_data_json_safe(
                _normalize_prompt_data(
                    EASYUSE_ANIMA_PROMPT_DATA
                )
            ),
            "unet_name": str(unet_name or ""),
            "vae_name": str(vae_name or ""),
            "clip_name": str(clip_name or ""),
            "clip_type": str(clip_type or ""),
            "input_settings": _normalize_aio_input_settings(
                input_settings
            ),
        })

    def build(
        self,
        EASYUSE_ANIMA_PROMPT_DATA: str | dict,
        unet_name: str,
        vae_name: str,
        clip_name: str,
        clip_type: str = "qwen_image",
        input_settings: str | dict | None = None,
    ):
        settings = _normalize_aio_input_settings(input_settings)
        prompt_data = _copy_prompt_data_for_update(
            EASYUSE_ANIMA_PROMPT_DATA
        )
        resources = settings.get("resources", {})
        resource_info = {
            "loader_mode": "split",
            "unet_name": str(unet_name),
            "vae_name": str(vae_name),
            "clip_name": str(clip_name),
            "clip_type": str(clip_type or "qwen_image"),
            "unet_weight_dtype": str(resources.get("unet_weight_dtype") or "default"),
            "clip_device": str(resources.get("clip_device") or "default"),
        }
        prompt_data["easy_use_anima_input"] = {
            "schema": EASY_USE_ANIMA_INPUT_SCHEMA,
            "version": EASY_USE_ANIMA_INPUT_SETTINGS_VERSION,
            "resource_info": dict(resource_info),
        }
        return ({
            "schema": EASY_USE_ANIMA_INPUT_SCHEMA,
            "version": EASY_USE_ANIMA_INPUT_SETTINGS_VERSION,
            "prompt_data": prompt_data,
            "resource_info": resource_info,
            "input_settings": settings,
        },)


class EasyUseAnimaAIOGenerator:
    """Draft all-in-one generator that consumes one easy use anima input context."""

    DESCRIPTION = (
        "Consumes the dedicated easy use anima input context and runs the base txt2img "
        "generation path: prompt-data conditioning, optional Mod Guidance model patch, "
        "KSampler, VAE decode, and optional image saving. Generation options are stored in "
        "one versioned JSON field for future-compatible popup settings."
    )
    OUTPUT_TOOLTIPS = (
        "Decoded generated image.",
        "Sampled latent image.",
        "JSON metadata summary for debugging or downstream integration.",
    )

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "easy_use_anima_input": (
                    EASY_USE_ANIMA_INPUT_TYPE,
                    {
                        "forceInput": True,
                        "tooltip": "Context from Easy Use Anima Input.",
                    },
                ),
                "generation_settings": (
                    "STRING",
                    {
                        "multiline": True,
                        "default": _aio_generation_settings_json(),
                        "hidden": True,
                        "tooltip": "Hidden versioned JSON storage for popup generation settings. Keep this field serialized.",
                    },
                ),
            },
            "hidden": {
                "workflow_prompt": "PROMPT",
                "extra_pnginfo": "EXTRA_PNGINFO",
                "unique_id": "UNIQUE_ID",
            },
            "optional": {
                "lora_stack": (
                    "LORA_STACK",
                    {
                        "forceInput": True,
                        "tooltip": "Optional LoRA stack applied to MODEL and CLIP before conditioning and sampling.",
                    },
                ),
            },
        }

    RETURN_TYPES = ("IMAGE", "LATENT", "STRING")
    RETURN_NAMES = ("image", "latent", "metadata_json")
    FUNCTION = "generate"
    OUTPUT_NODE = True
    CATEGORY = "EasyUse Anima/AiO"

    @classmethod
    def IS_CHANGED(
        cls,
        easy_use_anima_input=None,
        lora_stack=None,
        generation_settings: str | dict | None = None,
        **kwargs,
    ):
        settings = _normalize_aio_generation_settings(
            generation_settings
        )
        if settings.get("sampler", {}).get("seed") in AIO_SPECIAL_SEEDS:
            change_settings = _json_clone(settings)
            change_settings["sampler"]["seed"] = _resolve_aio_runtime_seed(
                change_settings["sampler"].get("seed")
            )
        else:
            change_settings = settings
        return _stable_change_key({
            "mode": "easy_use_anima_generator",
            "input": _easy_use_anima_input_signature(easy_use_anima_input),
            "lora_stack": _aio_lora_stack_signature(lora_stack),
            "generation_settings": change_settings,
        })

    def generate(
        self,
        easy_use_anima_input,
        generation_settings: str | dict | None = None,
        lora_stack=None,
        workflow_prompt=None,
        extra_pnginfo=None,
        unique_id=None,
    ):
        return _run_aio_legacy_generation(
            self,
            easy_use_anima_input,
            generation_settings,
            lora_stack,
            workflow_prompt,
            extra_pnginfo,
            unique_id,
        )


__all__ = ("EasyUseAnimaInput", "EasyUseAnimaAIOGenerator")
