"""AiO resource selection and loading helpers."""

from __future__ import annotations

from typing import Any

from ..common.values import _as_int, _choice
from ..image.sam3 import _sam3_context
from ..infrastructure.comfy.invocation import _node_output_tuple
from ..infrastructure.comfy.resources import (
    _comfy_clip_loader_types as _adapter_comfy_clip_loader_types,
)
from ..infrastructure.comfy.resources import (
    _comfy_diffusion_model_names as _adapter_comfy_diffusion_model_names,
)
from ..infrastructure.comfy.resources import (
    _comfy_text_encoder_names as _adapter_comfy_text_encoder_names,
)
from ..infrastructure.comfy.resources import (
    _comfy_vae_names as _adapter_comfy_vae_names,
)
from ..infrastructure.comfy.resources import _folder_path_names
from ..infrastructure.comfy.wiring import resolve_comfy_host_helper
from .generation_normalization import _merge_versioned_settings
from .input_defaults import (
    AIO_INPUT_DEFAULT_SETTINGS,
    ANIMA_CLIP_DEVICES,
    ANIMA_CLIP_TYPES,
    ANIMA_DEFAULT_CLIP_CANDIDATES,
    ANIMA_DEFAULT_DIFFUSION_MODEL_CANDIDATES,
    ANIMA_DEFAULT_VAE_CANDIDATES,
    ANIMA_UNET_WEIGHT_DTYPES,
    EASY_USE_ANIMA_INPUT_SCHEMA,
    EASY_USE_ANIMA_INPUT_SETTINGS_VERSION,
)


def _missing_host_helper(name: str):
    raise RuntimeError(
        f"[EasyUseAnima] AiO resource Comfy host helper is unavailable: {name}"
    )


def _find_comfy_node_class(node_id: str):
    helper = resolve_comfy_host_helper(
        "_find_comfy_node_class",
        _missing_host_helper,
    )
    return helper(node_id)


def _normalize_aio_input_settings(value) -> dict[str, Any]:
    settings = _merge_versioned_settings(
        AIO_INPUT_DEFAULT_SETTINGS,
        value,
    )
    settings["schema"] = EASY_USE_ANIMA_INPUT_SCHEMA
    settings["version"] = _as_int(
        settings.get("version"),
        EASY_USE_ANIMA_INPUT_SETTINGS_VERSION,
    )
    resources = settings.setdefault("resources", {})
    if not isinstance(resources, dict):
        resources = {}
        settings["resources"] = resources
    resources["loader_mode"] = "split"
    resources["clip_loader"] = _choice(
        resources.get("clip_loader"),
        ("single",),
        "single",
    )
    resources["unet_weight_dtype"] = _choice(
        resources.get("unet_weight_dtype"),
        ANIMA_UNET_WEIGHT_DTYPES,
        "default",
    )
    resources["clip_device"] = _choice(
        resources.get("clip_device"),
        ANIMA_CLIP_DEVICES,
        "default",
    )
    return settings


def _comfy_diffusion_model_names() -> list[str]:
    return _adapter_comfy_diffusion_model_names(
        ANIMA_DEFAULT_DIFFUSION_MODEL_CANDIDATES,
        _folder_path_names,
    )


def _comfy_text_encoder_names() -> list[str]:
    return _adapter_comfy_text_encoder_names(
        ANIMA_DEFAULT_CLIP_CANDIDATES,
        _folder_path_names,
    )


def _comfy_vae_names() -> list[str]:
    return _adapter_comfy_vae_names(
        ANIMA_DEFAULT_VAE_CANDIDATES,
        _find_comfy_node_class,
        _folder_path_names,
    )


def _comfy_clip_loader_types() -> list[str]:
    return _adapter_comfy_clip_loader_types(
        ANIMA_CLIP_TYPES,
        _find_comfy_node_class,
    )


def _preferred_name_default(names: list[str], candidates: tuple[str, ...]) -> str:
    if not names:
        return candidates[0] if candidates else ""
    for candidate in candidates:
        if candidate in names:
            return candidate
    normalized = {
        str(name).replace("/", "\\").rsplit("\\", 1)[-1].lower(): str(name)
        for name in names
    }
    for candidate in candidates:
        basename = candidate.replace("/", "\\").rsplit("\\", 1)[-1].lower()
        if basename in normalized:
            return normalized[basename]
    return names[0]


def _preferred_checkpoint_default(names: list[str], preferred: str) -> str:
    return preferred if preferred in names else names[0]


def _preferred_clip_type_default(names: list[str]) -> str:
    if "qwen_image" in names:
        return "qwen_image"
    return _choice("", names, "stable_diffusion")


def _load_checkpoint_with_comfy(ckpt_name: str):
    loader_cls = _find_comfy_node_class("CheckpointLoaderSimple")
    if loader_cls is None:
        raise RuntimeError("[EasyUseAnima] Could not find ComfyUI CheckpointLoaderSimple.")
    loader = loader_cls()
    method = getattr(loader, "load_checkpoint", None)
    if method is None:
        raise RuntimeError("[EasyUseAnima] CheckpointLoaderSimple does not expose load_checkpoint.")
    return method(ckpt_name)


def _load_diffusion_model_with_comfy(unet_name: str, weight_dtype: str = "default"):
    loader_cls = _find_comfy_node_class("UNETLoader")
    if loader_cls is None:
        raise RuntimeError("[EasyUseAnima] Could not find ComfyUI UNETLoader.")
    loader = loader_cls()
    method = getattr(loader, "load_unet", None)
    if method is None:
        raise RuntimeError("[EasyUseAnima] UNETLoader does not expose load_unet.")
    values = _node_output_tuple(method(str(unet_name), str(weight_dtype or "default")))
    if not values:
        raise RuntimeError("[EasyUseAnima] UNETLoader returned no MODEL.")
    return values[0]


def _load_vae_with_comfy(vae_name: str):
    loader_cls = _find_comfy_node_class("VAELoader")
    if loader_cls is None:
        raise RuntimeError("[EasyUseAnima] Could not find ComfyUI VAELoader.")
    loader = loader_cls()
    method = getattr(loader, "load_vae", None)
    if method is None:
        raise RuntimeError("[EasyUseAnima] VAELoader does not expose load_vae.")
    values = _node_output_tuple(method(str(vae_name)))
    if not values:
        raise RuntimeError("[EasyUseAnima] VAELoader returned no VAE.")
    return values[0]


def _load_clip_with_comfy(
    clip_name: str,
    clip_type: str = "qwen_image",
    device: str = "default",
):
    loader_cls = _find_comfy_node_class("CLIPLoader")
    if loader_cls is None:
        raise RuntimeError("[EasyUseAnima] Could not find ComfyUI CLIPLoader.")
    loader = loader_cls()
    method = getattr(loader, "load_clip", None)
    if method is None:
        raise RuntimeError("[EasyUseAnima] CLIPLoader does not expose load_clip.")
    values = _node_output_tuple(
        method(
            str(clip_name),
            str(clip_type or "qwen_image"),
            str(device or "default"),
        )
    )
    if not values:
        raise RuntimeError("[EasyUseAnima] CLIPLoader returned no CLIP.")
    return values[0]


def _load_upscale_model_with_comfy(model_name: str):
    model_name = str(model_name or "").strip()
    if not model_name:
        raise RuntimeError(
            "[EasyUseAnima] USDU final upscale requires an upscale_model_name. "
            "Choose a model from ComfyUI models/upscale_models."
        )
    loader_cls = _find_comfy_node_class("UpscaleModelLoader")
    if loader_cls is None:
        try:
            from comfy_extras.nodes_upscale_model import (  # pyright: ignore[reportMissingImports]
                UpscaleModelLoader,
            )

            loader_cls = UpscaleModelLoader
        except Exception:
            loader_cls = None
    if loader_cls is None:
        raise RuntimeError("[EasyUseAnima] Could not find ComfyUI UpscaleModelLoader.")
    loader = loader_cls()
    method = getattr(loader, "load_model", None) or getattr(loader, "execute", None)
    if method is None:
        raise RuntimeError("[EasyUseAnima] UpscaleModelLoader does not expose load_model().")
    values = _node_output_tuple(method(model_name))
    if not values:
        raise RuntimeError("[EasyUseAnima] UpscaleModelLoader returned no UPSCALE_MODEL.")
    return values[0]


def _load_aio_sam3_context(detailer_settings: dict[str, Any]) -> dict[str, Any]:
    sam3 = detailer_settings.get("sam3", {})
    if not isinstance(sam3, dict):
        sam3 = {}
    checkpoint = str(sam3.get("checkpoint") or "sam3.1_multiplex_fp16.safetensors")
    model, clip, vae = _load_checkpoint_with_comfy(checkpoint)
    return _sam3_context(model, clip, vae, checkpoint)


def _load_aio_resources_from_input_context(context: dict[str, Any]):
    resource_info = context.get("resource_info", {})
    if not isinstance(resource_info, dict):
        resource_info = {}
    settings = _normalize_aio_input_settings(context.get("input_settings", {}))
    resources = settings.get("resources", {})
    if not isinstance(resources, dict):
        resources = {}

    unet_name = str(resource_info.get("unet_name") or "").strip()
    vae_name = str(resource_info.get("vae_name") or "").strip()
    clip_name = str(resource_info.get("clip_name") or "").strip()
    clip_type = str(resource_info.get("clip_type") or "qwen_image")
    missing = [
        label
        for label, value in (
            ("unet_name", unet_name),
            ("vae_name", vae_name),
            ("clip_name", clip_name),
        )
        if not value
    ]
    if missing:
        raise RuntimeError(
            "[EasyUseAnima] easy use anima input resource_info is missing required value(s): "
            + ", ".join(missing)
        )

    model = _load_diffusion_model_with_comfy(
        unet_name,
        str(
            resources.get("unet_weight_dtype")
            or resource_info.get("unet_weight_dtype")
            or "default"
        ),
    )
    vae = _load_vae_with_comfy(vae_name)
    clip = _load_clip_with_comfy(
        clip_name,
        clip_type,
        str(
            resources.get("clip_device")
            or resource_info.get("clip_device")
            or "default"
        ),
    )
    return model, clip, vae


__all__ = ()
