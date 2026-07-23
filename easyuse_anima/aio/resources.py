"""AiO resource selection and loading helpers."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, TypeAlias

_RuntimeResolver: TypeAlias = Callable[[str], Any]
_RUNTIME_RESOLVER: _RuntimeResolver | None = None


def _bind_aio_resource_runtime(*, resolve_helper: _RuntimeResolver) -> None:
    """Bind root compatibility helpers without importing the root module."""

    global _RUNTIME_RESOLVER
    _RUNTIME_RESOLVER = resolve_helper


def _runtime_helper(name: str) -> Any:
    resolver = _RUNTIME_RESOLVER
    if resolver is None:
        raise RuntimeError(
            f"[EasyUseAnima] AiO resource runtime helper is not bound: {name}"
        )
    return resolver(name)


def _normalize_aio_input_settings(value) -> dict[str, Any]:
    settings = _runtime_helper("_merge_versioned_settings")(
        _runtime_helper("AIO_INPUT_DEFAULT_SETTINGS"),
        value,
    )
    settings["schema"] = _runtime_helper("EASY_USE_ANIMA_INPUT_SCHEMA")
    settings["version"] = _runtime_helper("_as_int")(
        settings.get("version"),
        _runtime_helper("EASY_USE_ANIMA_INPUT_SETTINGS_VERSION"),
    )
    resources = settings.setdefault("resources", {})
    if not isinstance(resources, dict):
        resources = {}
        settings["resources"] = resources
    resources["loader_mode"] = "split"
    resources["clip_loader"] = _runtime_helper("_choice")(
        resources.get("clip_loader"),
        ("single",),
        "single",
    )
    resources["unet_weight_dtype"] = _runtime_helper("_choice")(
        resources.get("unet_weight_dtype"),
        _runtime_helper("ANIMA_UNET_WEIGHT_DTYPES"),
        "default",
    )
    resources["clip_device"] = _runtime_helper("_choice")(
        resources.get("clip_device"),
        _runtime_helper("ANIMA_CLIP_DEVICES"),
        "default",
    )
    return settings


def _comfy_diffusion_model_names() -> list[str]:
    return _runtime_helper("_adapter_comfy_diffusion_model_names")(
        _runtime_helper("ANIMA_DEFAULT_DIFFUSION_MODEL_CANDIDATES"),
        _runtime_helper("_folder_path_names"),
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
    choice = _runtime_helper("_choice")
    return choice("", names, "stable_diffusion")


def _load_checkpoint_with_comfy(ckpt_name: str):
    find_node_class = _runtime_helper("_find_comfy_node_class")
    loader_cls = find_node_class("CheckpointLoaderSimple")
    if loader_cls is None:
        raise RuntimeError("[EasyUseAnima] Could not find ComfyUI CheckpointLoaderSimple.")
    loader = loader_cls()
    method = getattr(loader, "load_checkpoint", None)
    if method is None:
        raise RuntimeError("[EasyUseAnima] CheckpointLoaderSimple does not expose load_checkpoint.")
    return method(ckpt_name)


def _load_diffusion_model_with_comfy(unet_name: str, weight_dtype: str = "default"):
    find_node_class = _runtime_helper("_find_comfy_node_class")
    loader_cls = find_node_class("UNETLoader")
    if loader_cls is None:
        raise RuntimeError("[EasyUseAnima] Could not find ComfyUI UNETLoader.")
    loader = loader_cls()
    method = getattr(loader, "load_unet", None)
    if method is None:
        raise RuntimeError("[EasyUseAnima] UNETLoader does not expose load_unet.")
    node_output_tuple = _runtime_helper("_node_output_tuple")
    values = node_output_tuple(method(str(unet_name), str(weight_dtype or "default")))
    if not values:
        raise RuntimeError("[EasyUseAnima] UNETLoader returned no MODEL.")
    return values[0]


def _load_vae_with_comfy(vae_name: str):
    find_node_class = _runtime_helper("_find_comfy_node_class")
    loader_cls = find_node_class("VAELoader")
    if loader_cls is None:
        raise RuntimeError("[EasyUseAnima] Could not find ComfyUI VAELoader.")
    loader = loader_cls()
    method = getattr(loader, "load_vae", None)
    if method is None:
        raise RuntimeError("[EasyUseAnima] VAELoader does not expose load_vae.")
    node_output_tuple = _runtime_helper("_node_output_tuple")
    values = node_output_tuple(method(str(vae_name)))
    if not values:
        raise RuntimeError("[EasyUseAnima] VAELoader returned no VAE.")
    return values[0]


def _load_clip_with_comfy(
    clip_name: str,
    clip_type: str = "qwen_image",
    device: str = "default",
):
    find_node_class = _runtime_helper("_find_comfy_node_class")
    loader_cls = find_node_class("CLIPLoader")
    if loader_cls is None:
        raise RuntimeError("[EasyUseAnima] Could not find ComfyUI CLIPLoader.")
    loader = loader_cls()
    method = getattr(loader, "load_clip", None)
    if method is None:
        raise RuntimeError("[EasyUseAnima] CLIPLoader does not expose load_clip.")
    node_output_tuple = _runtime_helper("_node_output_tuple")
    values = node_output_tuple(
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
    find_node_class = _runtime_helper("_find_comfy_node_class")
    loader_cls = find_node_class("UpscaleModelLoader")
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
    node_output_tuple = _runtime_helper("_node_output_tuple")
    values = node_output_tuple(method(model_name))
    if not values:
        raise RuntimeError("[EasyUseAnima] UpscaleModelLoader returned no UPSCALE_MODEL.")
    return values[0]


def _load_aio_sam3_context(detailer_settings: dict[str, Any]) -> dict[str, Any]:
    sam3 = detailer_settings.get("sam3", {})
    if not isinstance(sam3, dict):
        sam3 = {}
    checkpoint = str(sam3.get("checkpoint") or "sam3.1_multiplex_fp16.safetensors")
    load_checkpoint = _runtime_helper("_load_checkpoint_with_comfy")
    model, clip, vae = load_checkpoint(checkpoint)
    sam3_context = _runtime_helper("_sam3_context")
    return sam3_context(model, clip, vae, checkpoint)


def _load_aio_resources_from_input_context(context: dict[str, Any]):
    resource_info = context.get("resource_info", {})
    if not isinstance(resource_info, dict):
        resource_info = {}
    normalize_input_settings = _runtime_helper("_normalize_aio_input_settings")
    settings = normalize_input_settings(context.get("input_settings", {}))
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

    model = _runtime_helper("_load_diffusion_model_with_comfy")(
        unet_name,
        str(
            resources.get("unet_weight_dtype")
            or resource_info.get("unet_weight_dtype")
            or "default"
        ),
    )
    vae = _runtime_helper("_load_vae_with_comfy")(vae_name)
    clip = _runtime_helper("_load_clip_with_comfy")(
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
