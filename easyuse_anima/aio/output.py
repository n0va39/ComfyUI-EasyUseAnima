"""AiO image-saving adapters and output metadata helpers."""

from __future__ import annotations

import os
from collections.abc import Callable
from typing import Any, TypeAlias

from .output_settings import (
    _normalize_aio_civitai_hash_fetchers,
    _normalize_aio_hash_bundles,
)

_RuntimeResolver: TypeAlias = Callable[[str], Any]
_RUNTIME_RESOLVER: _RuntimeResolver | None = None


def _bind_aio_output_runtime(*, resolve_helper: _RuntimeResolver) -> None:
    """Bind root compatibility helpers without importing the root module."""

    global _RUNTIME_RESOLVER
    _RUNTIME_RESOLVER = resolve_helper


def _runtime_helper(name: str) -> Any:
    resolver = _RUNTIME_RESOLVER
    if resolver is None:
        raise RuntimeError(
            f"[EasyUseAnima] AiO output runtime helper is not bound: {name}"
        )
    return resolver(name)


def _aio_image_saver_civitai_hash_fetcher_entries(
    image_saver: dict[str, Any],
) -> list[str]:
    fetcher_settings = [
        item
        for item in _runtime_helper("_normalize_aio_civitai_hash_fetchers")(
            image_saver.get("civitai_hash_fetchers")
        )
        if _runtime_helper("_as_bool")(item.get("enabled"), True)
    ]
    if not fetcher_settings:
        return []

    fetcher_cls = _runtime_helper("_require_custom_node_class")(
        "Civitai Hash Fetcher (Image Saver)",
        "ComfyUI-Image-Saver",
        "Required for AiO Save Options > Civitai Hash Fetcher rows.",
    )
    fetcher = fetcher_cls()
    get_hash = getattr(fetcher, "get_autov3_hash", None)
    if get_hash is None:
        raise RuntimeError(
            "[EasyUseAnima] Civitai Hash Fetcher (Image Saver) does not expose get_autov3_hash()."
        )

    entries: list[str] = []
    for item in fetcher_settings:
        username = str(item.get("username") or "").strip()
        model_name = str(item.get("model_name") or "").strip()
        version = str(item.get("version") or "").strip()
        if not username and not model_name:
            continue
        if not username or not model_name:
            raise RuntimeError(
                "[EasyUseAnima] Civitai Hash Fetcher requires both username and model_name."
            )
        try:
            result = get_hash(username, model_name, version)
        except Exception as exc:
            _runtime_helper("logger").warning(
                "[EasyUseAnima] Civitai Hash Fetcher failed for '%s/%s'%s; skipping metadata hash: %s",
                username,
                model_name,
                f" version '{version}'" if version else "",
                exc,
            )
            continue
        hash_value = _runtime_helper("_single_value")(result)
        hash_text = str(hash_value or "").strip()
        if (
            not hash_text
            or hash_text.lower().startswith("error:")
            or hash_text.lower().startswith("no ")
        ):
            _runtime_helper("logger").warning(
                "[EasyUseAnima] Civitai Hash Fetcher returned no usable hash for '%s/%s'%s; "
                "skipping metadata hash: %s",
                username,
                model_name,
                f" version '{version}'" if version else "",
                hash_text or "empty hash",
            )
            continue
        entries.append(f"{model_name}:{hash_text}")
    return entries


def _aio_image_saver_additional_hashes(image_saver: dict[str, Any]) -> str:
    parts = []
    base = str(image_saver.get("additional_hashes") or "").strip(" ,\n\r\t")
    if base:
        parts.append(base)
    parts.extend(
        _runtime_helper("_normalize_aio_hash_bundles")(
            image_saver.get("additional_hash_bundles")
        )
    )
    parts.extend(
        _runtime_helper("_aio_image_saver_civitai_hash_fetcher_entries")(image_saver)
    )
    return ",".join(part for part in parts if part)


def _aio_lora_metadata_name(name: str) -> str:
    value = str(name or "").strip().replace("\\", "/").strip("/")
    if not value:
        return ""
    root, ext = os.path.splitext(value)
    try:
        import folder_paths  # type: ignore

        supported = set(getattr(folder_paths, "supported_pt_extensions", ()))
    except Exception:
        supported = {".safetensors", ".pt", ".ckpt", ".bin", ".pth"}
    if ext.lower() in supported:
        value = root
    return value


def _aio_prompt_with_lora_metadata(prompt: str, applied_loras) -> str:
    tags: list[str] = []
    if not isinstance(applied_loras, list):
        applied_loras = []
    for item in applied_loras:
        if not isinstance(item, dict):
            continue
        name = _runtime_helper("_aio_lora_metadata_name")(
            str(item.get("name") or "")
        )
        if not name:
            continue
        strength = _runtime_helper("_format_strength")(
            _runtime_helper("_as_float")(item.get("strength_model"), 1.0)
        )
        tags.append(f"<lora:{name}:{strength}>")
    if not tags:
        return str(prompt or "")
    base = str(prompt or "").strip()
    suffix = " ".join(tags)
    return f"{base} {suffix}".strip() if base else suffix


def _save_image_with_comfy(
    images,
    filename_prefix: str,
    workflow_prompt=None,
    extra_pnginfo=None,
):
    save_cls = _runtime_helper("_find_comfy_node_class")("SaveImage")
    if save_cls is None:
        raise RuntimeError("[EasyUseAnima] Could not find ComfyUI SaveImage.")
    saver = save_cls()
    save_images = getattr(saver, "save_images", None)
    if save_images is None:
        raise RuntimeError("[EasyUseAnima] SaveImage does not expose save_images().")
    return save_images(
        images,
        str(filename_prefix or "EasyUseAnima/AiO"),
        prompt=workflow_prompt,
        extra_pnginfo=extra_pnginfo,
    )


def _aio_save_filename_prefix(save_settings: dict[str, Any]) -> str:
    image_saver = save_settings.get("image_saver", {})
    if not isinstance(image_saver, dict):
        image_saver = {}
    defaults = _runtime_helper("AIO_GENERATION_DEFAULT_SETTINGS")["save"]["image_saver"]
    path = str(image_saver.get("path") or defaults["path"]).strip().strip("/\\")
    filename = str(image_saver.get("filename") or defaults["filename"]).strip().strip("/\\")
    if path and filename:
        return f"{path}/{filename}"
    return filename or path or f"{defaults['path']}/{defaults['filename']}"


def _save_image_with_image_saver(
    images,
    save_settings: dict[str, Any],
    positive_prompt: str,
    negative_prompt: str,
    width: int,
    height: int,
    sampler_settings: dict[str, Any],
    applied_loras=None,
    resource_info: dict[str, Any] | None = None,
    workflow_prompt=None,
    extra_pnginfo=None,
):
    image_saver_cls = _runtime_helper("_require_custom_node_class")(
        "Image Saver",
        "ComfyUI-Image-Saver",
        "Repository: https://github.com/alexopus/ComfyUI-Image-Saver",
    )
    saver = image_saver_cls()
    save_files = getattr(saver, "save_files", None)
    if save_files is None:
        raise RuntimeError("[EasyUseAnima] Image Saver node does not expose save_files().")

    image_saver = save_settings.get("image_saver", {})
    if not isinstance(image_saver, dict):
        image_saver = {}
    defaults = _runtime_helper("AIO_GENERATION_DEFAULT_SETTINGS")["save"]["image_saver"]
    modelname = str((resource_info or {}).get("unet_name") or "")
    save_prompt_metadata = _runtime_helper("_as_bool")(
        image_saver.get("save_prompt_metadata"),
        defaults["save_prompt_metadata"],
    )
    metadata_positive = (
        _runtime_helper("_aio_prompt_with_lora_metadata")(
            str(positive_prompt or "unknown"), applied_loras
        )
        if save_prompt_metadata
        else ""
    )
    metadata_negative = str(negative_prompt or "unknown") if save_prompt_metadata else ""
    return save_files(
        images=images,
        filename=str(image_saver.get("filename") or defaults["filename"]),
        path=str(image_saver.get("path") or defaults["path"]),
        extension=str(image_saver.get("extension") or defaults["extension"]),
        steps=_runtime_helper("_as_int")(sampler_settings.get("steps"), 28),
        cfg=_runtime_helper("_as_float")(sampler_settings.get("cfg"), 5.0),
        modelname=modelname,
        sampler_name=str(sampler_settings.get("sampler_name") or ""),
        scheduler_name=str(sampler_settings.get("scheduler") or "normal"),
        positive=metadata_positive,
        negative=metadata_negative,
        seed_value=_runtime_helper("_resolve_aio_runtime_seed")(
            sampler_settings.get("seed")
        ),
        width=_runtime_helper("_as_int")(width, 512),
        height=_runtime_helper("_as_int")(height, 512),
        lossless_webp=_runtime_helper("_as_bool")(
            image_saver.get("lossless_webp"), defaults["lossless_webp"]
        ),
        quality_jpeg_or_webp=max(
            1,
            min(
                100,
                _runtime_helper("_as_int")(
                    image_saver.get("quality_jpeg_or_webp"),
                    defaults["quality_jpeg_or_webp"],
                ),
            ),
        ),
        optimize_png=_runtime_helper("_as_bool")(
            image_saver.get("optimize_png"), defaults["optimize_png"]
        ),
        counter=max(
            0,
            _runtime_helper("_as_int")(
                image_saver.get("counter"), defaults["counter"]
            ),
        ),
        denoise=_runtime_helper("_as_float")(sampler_settings.get("denoise"), 1.0),
        clip_skip=_runtime_helper("_as_int")(
            image_saver.get("clip_skip"), defaults["clip_skip"]
        ),
        time_format=str(image_saver.get("time_format") or defaults["time_format"]),
        save_workflow_as_json=_runtime_helper("_as_bool")(
            image_saver.get("save_workflow_as_json"),
            defaults["save_workflow_as_json"],
        ),
        embed_workflow=_runtime_helper("_as_bool")(
            image_saver.get("embed_workflow"), defaults["embed_workflow"]
        ),
        additional_hashes=_runtime_helper("_aio_image_saver_additional_hashes")(
            image_saver
        ),
        download_civitai_data=_runtime_helper("_as_bool")(
            image_saver.get("download_civitai_data"),
            defaults["download_civitai_data"],
        ),
        easy_remix=_runtime_helper("_as_bool")(
            image_saver.get("easy_remix"), defaults["easy_remix"]
        ),
        show_preview=False,
        custom=str(image_saver.get("custom") or ""),
        prompt=workflow_prompt,
        extra_pnginfo=extra_pnginfo,
    )


__all__ = ()
