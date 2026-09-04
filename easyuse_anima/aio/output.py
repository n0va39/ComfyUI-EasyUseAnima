"""AiO image-saving adapters and output metadata helpers."""

from __future__ import annotations

import logging
import os
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any

from ..common.values import _as_bool, _as_float, _as_int, _single_value
from ..infrastructure.comfy.wiring import resolve_comfy_host_helper
from ..lora.preset import _format_strength
from .generation_defaults import AIO_GENERATION_DEFAULT_SETTINGS
from .output_settings import (
    _normalize_aio_civitai_hash_fetchers as _normalize_aio_civitai_hash_fetchers,
)
from .output_settings import (
    _normalize_aio_hash_bundles as _normalize_aio_hash_bundles,
)
from .sampling import _resolve_aio_runtime_seed

logger = logging.getLogger("ComfyUI-EasyUseAnima")

_IMAGE_SAVER_SAFE_TIME_FORMAT = "%Y-%m-%d-%H%M%S"
_IMAGE_SAVER_CUSTOM_TIME_RE = re.compile(r"%time_format<([^>]*)>")
_IMAGE_SAVER_CUSTOM_COUNTER_RE = re.compile(r"%counter<([0-9]+)>")
_OUTPUT_CONTROL_RE = re.compile(r"[\x00-\x1f\x7f]")


@dataclass(frozen=True, slots=True)
class _ImageSaverRuntime:
    settings: dict[str, Any]
    defaults: dict[str, Any]
    modelname: str
    steps: int
    cfg: float
    sampler_name: str
    scheduler_name: str
    seed: int
    width: int
    height: int
    counter: int
    denoise: float
    clip_skip: int
    custom: str
    path: str
    filename: str
    extension: str


def _missing_host_helper(name: str):
    raise RuntimeError(
        f"[EasyUseAnima] AiO output Comfy host helper is unavailable: {name}"
    )


def _find_comfy_node_class(node_id: str):
    helper = resolve_comfy_host_helper(
        "_find_comfy_node_class",
        _missing_host_helper,
    )
    return helper(node_id)


def _require_custom_node_class(
    node_id: str,
    node_pack: str,
    install_hint: str,
):
    helper = resolve_comfy_host_helper(
        "_require_custom_node_class",
        _missing_host_helper,
    )
    return helper(node_id, node_pack, install_hint)


def _comfy_output_directory() -> Path:
    try:
        import folder_paths  # type: ignore
    except Exception as exc:
        raise RuntimeError(
            "[EasyUseAnima] ComfyUI output directory is unavailable."
        ) from exc

    get_output_directory = getattr(folder_paths, "get_output_directory", None)
    value = (
        get_output_directory()
        if callable(get_output_directory)
        else getattr(folder_paths, "output_directory", None)
    )
    if not value:
        raise RuntimeError(
            "[EasyUseAnima] ComfyUI output directory is unavailable."
        )
    return Path(str(value)).resolve(strict=False)


def _output_path_parts(value: str, *, field: str, allow_empty: bool) -> list[str]:
    text = str(value or "").strip()
    if not text:
        if allow_empty:
            return []
        raise RuntimeError(f"[EasyUseAnima] AiO save {field} must not be empty.")
    if len(text) > 1024 or _OUTPUT_CONTROL_RE.search(text):
        raise RuntimeError(f"[EasyUseAnima] AiO save {field} is invalid.")

    posix_path = PurePosixPath(text)
    windows_path = PureWindowsPath(text)
    if posix_path.is_absolute() or windows_path.drive or windows_path.root:
        raise RuntimeError(
            f"[EasyUseAnima] AiO save {field} must be relative to the ComfyUI output directory."
        )

    parts = [part for part in re.split(r"[\\/]", text) if part]
    if (
        not parts
        or any(part in {".", ".."} for part in parts)
        or any(":" in part for part in parts)
    ):
        raise RuntimeError(
            f"[EasyUseAnima] AiO save {field} must stay within the ComfyUI output directory."
        )
    return parts


def _validated_output_subpath(
    value: str,
    *,
    field: str,
    allow_empty: bool = False,
    filename: bool = False,
) -> str:
    parts = _output_path_parts(value, field=field, allow_empty=allow_empty)
    if not parts:
        return ""
    if filename and (len(parts) != 1 or len(parts[0]) > 255):
        raise RuntimeError(
            "[EasyUseAnima] AiO save filename must be a single filename component."
        )

    output_root = _comfy_output_directory()
    candidate = output_root.joinpath(*parts).resolve(strict=False)
    try:
        candidate.relative_to(output_root)
    except ValueError as exc:
        raise RuntimeError(
            f"[EasyUseAnima] AiO save {field} must stay within the ComfyUI output directory."
        ) from exc
    return "/".join(parts)


def _image_saver_model_names(modelname: str) -> tuple[str, str]:
    filename = str(modelname or "").replace("\\", "/").rsplit("/", 1)[-1]
    root, extension = os.path.splitext(filename)
    try:
        import folder_paths  # type: ignore

        supported = set(getattr(folder_paths, "supported_pt_extensions", ()))
    except Exception:
        supported = {".safetensors", ".pt", ".ckpt", ".bin", ".pth"}
    basename = root if extension.casefold() in supported | {".gguf"} else filename
    return filename, basename


def _image_saver_timestamp(now: datetime, time_format: str) -> str:
    try:
        return now.strftime(time_format)
    except (OSError, ValueError):
        return now.strftime(_IMAGE_SAVER_SAFE_TIME_FORMAT)


def _render_image_saver_template(
    pattern: str,
    *,
    now: datetime,
    width: int,
    height: int,
    seed: int,
    modelname: str,
    counter: int,
    time_format: str,
    sampler_name: str,
    steps: int,
    cfg: float,
    scheduler_name: str,
    denoise: float,
    clip_skip: int,
    custom: str,
) -> str:
    value = str(pattern or "")
    if len(value) > 1024 or len(str(time_format or "")) > 256:
        raise RuntimeError("[EasyUseAnima] AiO save template is too long.")

    def replace_time(match: re.Match[str]) -> str:
        return _image_saver_timestamp(now, match.group(1))

    def replace_counter(match: re.Match[str]) -> str:
        padding = int(match.group(1))
        if padding > 32:
            raise RuntimeError(
                "[EasyUseAnima] AiO save counter padding must be 32 or less."
            )
        return f"{counter:0{padding}d}"

    model_filename, base_model_name = _image_saver_model_names(modelname)
    value = _IMAGE_SAVER_CUSTOM_TIME_RE.sub(replace_time, value)
    value = _IMAGE_SAVER_CUSTOM_COUNTER_RE.sub(replace_counter, value)
    replacements = (
        ("%date", _image_saver_timestamp(now, "%Y-%m-%d")),
        ("%time", _image_saver_timestamp(now, time_format)),
        ("%model", model_filename),
        ("%width", str(width)),
        ("%height", str(height)),
        ("%seed", str(seed)),
        ("%counter", str(counter)),
        ("%sampler_name", sampler_name),
        ("%steps", str(steps)),
        ("%cfg", str(cfg)),
        ("%scheduler_name", scheduler_name),
        ("%basemodelname", base_model_name),
        ("%denoise", str(denoise)),
        ("%clip_skip", str(clip_skip)),
        ("%custom", custom),
    )
    for token, replacement in replacements:
        value = value.replace(token, replacement)
    if "%" in value:
        raise RuntimeError(
            "[EasyUseAnima] AiO save template contains an unsupported placeholder."
        )
    if len(value) > 1024:
        raise RuntimeError("[EasyUseAnima] AiO save template result is too long.")
    return value


def _resolve_image_saver_runtime(
    save_settings: dict[str, Any],
    *,
    width: int,
    height: int,
    sampler_settings: dict[str, Any],
    resource_info: dict[str, Any] | None,
) -> _ImageSaverRuntime:
    image_saver = save_settings.get("image_saver", {})
    if not isinstance(image_saver, dict):
        image_saver = {}
    defaults = AIO_GENERATION_DEFAULT_SETTINGS["save"]["image_saver"]
    modelname = str((resource_info or {}).get("unet_name") or "")
    steps = _as_int(sampler_settings.get("steps"), 28)
    cfg = _as_float(sampler_settings.get("cfg"), 5.0)
    sampler_name = str(sampler_settings.get("sampler_name") or "")
    scheduler_name = str(sampler_settings.get("scheduler") or "normal")
    seed = _resolve_aio_runtime_seed(sampler_settings.get("seed"))
    safe_width = _as_int(width, 512)
    safe_height = _as_int(height, 512)
    counter = max(0, _as_int(image_saver.get("counter"), defaults["counter"]))
    denoise = _as_float(sampler_settings.get("denoise"), 1.0)
    clip_skip = _as_int(image_saver.get("clip_skip"), defaults["clip_skip"])
    time_format = str(image_saver.get("time_format") or defaults["time_format"])
    custom = str(image_saver.get("custom") or "")
    now = datetime.now()
    template_values = {
        "now": now,
        "width": safe_width,
        "height": safe_height,
        "seed": seed,
        "modelname": modelname,
        "counter": counter,
        "time_format": time_format,
        "sampler_name": sampler_name,
        "steps": steps,
        "cfg": cfg,
        "scheduler_name": scheduler_name,
        "denoise": denoise,
        "clip_skip": clip_skip,
        "custom": custom,
    }
    rendered_path = _render_image_saver_template(
        str(image_saver.get("path") or defaults["path"]),
        **template_values,
    )
    rendered_filename = _render_image_saver_template(
        str(image_saver.get("filename") or defaults["filename"]),
        **template_values,
    )
    if not rendered_filename:
        rendered_filename = _image_saver_timestamp(now, time_format)
    safe_path = _validated_output_subpath(
        rendered_path,
        field="path",
        allow_empty=True,
    )
    safe_filename = _validated_output_subpath(
        rendered_filename,
        field="filename",
        filename=True,
    )
    extension = str(image_saver.get("extension") or defaults["extension"]).casefold()
    if extension not in {"png", "jpeg", "jpg", "webp"}:
        raise RuntimeError("[EasyUseAnima] AiO save extension is invalid.")
    return _ImageSaverRuntime(
        settings=image_saver,
        defaults=defaults,
        modelname=modelname,
        steps=steps,
        cfg=cfg,
        sampler_name=sampler_name,
        scheduler_name=scheduler_name,
        seed=seed,
        width=safe_width,
        height=safe_height,
        counter=counter,
        denoise=denoise,
        clip_skip=clip_skip,
        custom=custom,
        path=safe_path,
        filename=safe_filename,
        extension=extension,
    )


def _aio_image_saver_civitai_hash_fetcher_entries(
    image_saver: dict[str, Any],
) -> list[str]:
    fetcher_settings = [
        item
        for item in _normalize_aio_civitai_hash_fetchers(
            image_saver.get("civitai_hash_fetchers")
        )
        if _as_bool(item.get("enabled"), True)
    ]
    if not fetcher_settings:
        return []

    fetcher_cls = _require_custom_node_class(
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
            logger.warning(
                "[EasyUseAnima] Civitai Hash Fetcher failed for '%s/%s'%s; skipping metadata hash: %s",
                username,
                model_name,
                f" version '{version}'" if version else "",
                exc,
            )
            continue
        hash_value = _single_value(result)
        hash_text = str(hash_value or "").strip()
        if (
            not hash_text
            or hash_text.lower().startswith("error:")
            or hash_text.lower().startswith("no ")
        ):
            logger.warning(
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
        _normalize_aio_hash_bundles(image_saver.get("additional_hash_bundles"))
    )
    parts.extend(
        _aio_image_saver_civitai_hash_fetcher_entries(image_saver)
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
        name = _aio_lora_metadata_name(str(item.get("name") or ""))
        if not name:
            continue
        strength = _format_strength(_as_float(item.get("strength_model"), 1.0))
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
    safe_prefix = _validated_output_subpath(
        str(filename_prefix or "EasyUseAnima/AiO"),
        field="filename prefix",
    )
    save_cls = _find_comfy_node_class("SaveImage")
    if save_cls is None:
        raise RuntimeError("[EasyUseAnima] Could not find ComfyUI SaveImage.")
    saver = save_cls()
    save_images = getattr(saver, "save_images", None)
    if save_images is None:
        raise RuntimeError("[EasyUseAnima] SaveImage does not expose save_images().")
    return save_images(
        images,
        safe_prefix,
        prompt=workflow_prompt,
        extra_pnginfo=extra_pnginfo,
    )


def _aio_save_filename_prefix(save_settings: dict[str, Any]) -> str:
    image_saver = save_settings.get("image_saver", {})
    if not isinstance(image_saver, dict):
        image_saver = {}
    defaults = AIO_GENERATION_DEFAULT_SETTINGS["save"]["image_saver"]
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
    runtime = _resolve_image_saver_runtime(
        save_settings,
        width=width,
        height=height,
        sampler_settings=sampler_settings,
        resource_info=resource_info,
    )

    image_saver_cls = _require_custom_node_class(
        "Image Saver",
        "ComfyUI-Image-Saver",
        "Repository: https://github.com/alexopus/ComfyUI-Image-Saver",
    )
    saver = image_saver_cls()
    save_files = getattr(saver, "save_files", None)
    if save_files is None:
        raise RuntimeError("[EasyUseAnima] Image Saver node does not expose save_files().")

    save_prompt_metadata = _as_bool(
        runtime.settings.get("save_prompt_metadata"),
        runtime.defaults["save_prompt_metadata"],
    )
    metadata_positive = (
        _aio_prompt_with_lora_metadata(
            str(positive_prompt or "unknown"), applied_loras
        )
        if save_prompt_metadata
        else ""
    )
    metadata_negative = str(negative_prompt or "unknown") if save_prompt_metadata else ""
    return save_files(
        images=images,
        filename=runtime.filename,
        path=runtime.path,
        extension=runtime.extension,
        steps=runtime.steps,
        cfg=runtime.cfg,
        modelname=runtime.modelname,
        sampler_name=runtime.sampler_name,
        scheduler_name=runtime.scheduler_name,
        positive=metadata_positive,
        negative=metadata_negative,
        seed_value=runtime.seed,
        width=runtime.width,
        height=runtime.height,
        lossless_webp=_as_bool(
            runtime.settings.get("lossless_webp"), runtime.defaults["lossless_webp"]
        ),
        quality_jpeg_or_webp=max(
            1,
            min(
                100,
                _as_int(
                    runtime.settings.get("quality_jpeg_or_webp"),
                    runtime.defaults["quality_jpeg_or_webp"],
                ),
            ),
        ),
        optimize_png=_as_bool(
            runtime.settings.get("optimize_png"), runtime.defaults["optimize_png"]
        ),
        counter=runtime.counter,
        denoise=runtime.denoise,
        clip_skip=runtime.clip_skip,
        time_format=_IMAGE_SAVER_SAFE_TIME_FORMAT,
        save_workflow_as_json=_as_bool(
            runtime.settings.get("save_workflow_as_json"),
            runtime.defaults["save_workflow_as_json"],
        ),
        embed_workflow=_as_bool(
            runtime.settings.get("embed_workflow"),
            runtime.defaults["embed_workflow"],
        ),
        additional_hashes=_aio_image_saver_additional_hashes(runtime.settings),
        download_civitai_data=_as_bool(
            runtime.settings.get("download_civitai_data"),
            runtime.defaults["download_civitai_data"],
        ),
        easy_remix=_as_bool(
            runtime.settings.get("easy_remix"), runtime.defaults["easy_remix"]
        ),
        show_preview=False,
        custom=runtime.custom,
        prompt=workflow_prompt,
        extra_pnginfo=extra_pnginfo,
    )


__all__ = ()
