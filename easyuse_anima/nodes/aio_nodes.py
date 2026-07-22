"""ComfyUI adapters for the AiO input context."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, TypeAlias

_RuntimeResolver: TypeAlias = Callable[[str], Any]
_RUNTIME_RESOLVER: _RuntimeResolver | None = None


def _bind_aio_node_runtime(*, resolve_helper: _RuntimeResolver) -> None:
    """Bind root compatibility helpers without importing the root module."""

    global _RUNTIME_RESOLVER
    _RUNTIME_RESOLVER = resolve_helper


def _runtime_helper(name: str) -> Any:
    resolver = _RUNTIME_RESOLVER
    if resolver is None:
        raise RuntimeError(
            f"[EasyUseAnima] AiO node runtime helper is not bound: {name}"
        )
    return resolver(name)


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
        unet_names = _runtime_helper("_comfy_diffusion_model_names")()
        vae_names = _runtime_helper("_comfy_vae_names")()
        clip_names = _runtime_helper("_comfy_text_encoder_names")()
        clip_types = _runtime_helper("_comfy_clip_loader_types")()
        return {
            "required": {
                _runtime_helper("PROMPT_DATA_TYPE"): (_runtime_helper("PROMPT_DATA_TYPE"), {
                    "forceInput": True,
                    "tooltip": "Structured prompt data from Anima Prompt Studio Advanced v2.",
                }),
                "unet_name": (unet_names, {
                    "default": _runtime_helper("_preferred_name_default")(
                        unet_names,
                        _runtime_helper("ANIMA_DEFAULT_DIFFUSION_MODEL_CANDIDATES"),
                    ),
                    "tooltip": "ANIMA diffusion model loaded with ComfyUI UNETLoader.",
                }),
                "vae_name": (vae_names, {
                    "default": _runtime_helper("_preferred_name_default")(
                        vae_names,
                        _runtime_helper("ANIMA_DEFAULT_VAE_CANDIDATES"),
                    ),
                    "tooltip": "VAE loaded with ComfyUI VAELoader.",
                }),
                "clip_name": (clip_names, {
                    "default": _runtime_helper("_preferred_name_default")(
                        clip_names,
                        _runtime_helper("ANIMA_DEFAULT_CLIP_CANDIDATES"),
                    ),
                    "tooltip": "Text encoder loaded with ComfyUI CLIPLoader.",
                }),
                "clip_type": (clip_types, {
                    "default": _runtime_helper("_preferred_clip_type_default")(clip_types),
                    "tooltip": "ComfyUI CLIPLoader type. Core ANIMA uses qwen_image.",
                }),
                "input_settings": ("STRING", {
                    "multiline": True,
                    "default": _runtime_helper("_aio_input_settings_json")(),
                    "hidden": True,
                    "tooltip": "Hidden versioned JSON storage for future resource settings. Kept serialized for workflow compatibility.",
                }),
            },
        }

    RETURN_TYPES = ("EASY_USE_ANIMA_INPUT",)
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
        return _runtime_helper("_stable_change_key")({
            "mode": "easy_use_anima_input",
            "prompt_data": _runtime_helper("_prompt_data_json_safe")(
                _runtime_helper("_normalize_prompt_data")(
                    EASYUSE_ANIMA_PROMPT_DATA
                )
            ),
            "unet_name": str(unet_name or ""),
            "vae_name": str(vae_name or ""),
            "clip_name": str(clip_name or ""),
            "clip_type": str(clip_type or ""),
            "input_settings": _runtime_helper("_normalize_aio_input_settings")(
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
        settings = _runtime_helper("_normalize_aio_input_settings")(input_settings)
        prompt_data = _runtime_helper("_copy_prompt_data_for_update")(
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
            "schema": _runtime_helper("EASY_USE_ANIMA_INPUT_SCHEMA"),
            "version": _runtime_helper("EASY_USE_ANIMA_INPUT_SETTINGS_VERSION"),
            "resource_info": dict(resource_info),
        }
        return ({
            "schema": _runtime_helper("EASY_USE_ANIMA_INPUT_SCHEMA"),
            "version": _runtime_helper("EASY_USE_ANIMA_INPUT_SETTINGS_VERSION"),
            "prompt_data": prompt_data,
            "resource_info": resource_info,
            "input_settings": settings,
        },)


__all__ = ("EasyUseAnimaInput",)
