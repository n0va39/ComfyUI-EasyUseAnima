"""AiO image-saving adapters and output metadata helpers."""

from __future__ import annotations

import logging
import os
import re
import unicodedata
from collections.abc import Callable, Iterator, Mapping
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any

from ..common.values import _as_bool, _as_float, _as_int
from ..infrastructure.comfy.wiring import resolve_comfy_host_helper
from ..lora.preset import _format_strength
from .generation_defaults import AIO_GENERATION_DEFAULT_SETTINGS
from .native_civitai import CivitaiLookupBudget, CivitaiLookupBudgetExhausted
from .native_image_output import (
    NativeImageMetadata,
    _build_native_metadata,
    _comfy_metadata_enabled,
    _fetch_civitai_autov3_hash,
    _is_windows_safe_output_component,
    _sanitize_native_output_filename,
    _save_native_images,
)
from .native_metadata_budget import _validate_parameter_sources
from .output_settings import (
    _MAX_SAVED_HASH_ROWS,
)
from .output_settings import (
    _normalize_aio_civitai_hash_fetchers as _normalize_aio_civitai_hash_fetchers,
)
from .output_settings import (
    _normalize_aio_hash_bundles as _normalize_aio_hash_bundles,
)
from .output_settings import _normalize_aio_hash_text as _normalize_aio_hash_text
from .sampling import _resolve_aio_runtime_seed

logger = logging.getLogger("ComfyUI-EasyUseAnima")

_IMAGE_SAVER_SAFE_TIME_FORMAT = "%Y-%m-%d-%H%M%S"
_IMAGE_SAVER_CUSTOM_TIME_RE = re.compile(r"%time_format<([^>]*)>")
_IMAGE_SAVER_CUSTOM_COUNTER_RE = re.compile(r"%counter<([0-9]+)>")
_OUTPUT_CONTROL_RE = re.compile(r"[\x00-\x1f\x7f]")
_MAX_OUTPUT_TEMPLATE_LENGTH = 1024
_MAX_OUTPUT_TIME_FORMAT_LENGTH = 256
_STRFTIME_DIRECTIVE_PREFIX_CHARS = frozenset("-_0^#:EO0123456789")
_MAX_CIVITAI_HASH_FETCHERS = _MAX_SAVED_HASH_ROWS
_MAX_JOINED_HASH_BYTES = 8 * 1024
_MAX_CIVITAI_LOG_CHARACTERS = 80
_UNSAFE_LOG_CATEGORIES = frozenset({"Cc", "Cf", "Cs", "Zl", "Zp"})


@dataclass(frozen=True, slots=True)
class _ImageSaverRuntime:
    output_root: Path
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
        or any(not _is_windows_safe_output_component(part) for part in parts)
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
    output_root: Path | None = None,
) -> str:
    parts = _output_path_parts(value, field=field, allow_empty=allow_empty)
    if not parts:
        return ""
    if filename and (len(parts) != 1 or len(parts[0]) > 255):
        raise RuntimeError(
            "[EasyUseAnima] AiO save filename must be a single filename component."
        )

    root = output_root or _comfy_output_directory()
    candidate = root.joinpath(*parts).resolve(strict=False)
    try:
        candidate.relative_to(root)
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


def _iter_strftime_segments(time_format: str) -> Iterator[tuple[str, bool]]:
    cursor = 0
    while cursor < len(time_format):
        percent = time_format.find("%", cursor)
        if percent < 0:
            yield time_format[cursor:], False
            return
        if percent > cursor:
            yield time_format[cursor:percent], False

        end = percent + 1
        if end < len(time_format) and time_format[end] == "%":
            end += 1
        else:
            while (
                end < len(time_format)
                and time_format[end] in _STRFTIME_DIRECTIVE_PREFIX_CHARS
            ):
                end += 1
            if end < len(time_format):
                end += 1
        yield time_format[percent:end], True
        cursor = end


def _render_strftime_bounded(
    now: datetime,
    time_format: str,
    max_length: int,
) -> str:
    pieces: list[str] = []
    result_length = 0
    for segment, is_directive in _iter_strftime_segments(time_format):
        remaining = max_length - result_length
        if remaining < 0:
            raise RuntimeError("[EasyUseAnima] AiO save template result is too long.")
        if is_directive:
            if any(
                int(width) > remaining
                for width in re.findall(r"[0-9]+", segment[1:])
            ):
                raise RuntimeError(
                    "[EasyUseAnima] AiO save template result is too long."
                )
            rendered = now.strftime(segment)
        else:
            rendered = segment
        if len(rendered) > remaining:
            raise RuntimeError("[EasyUseAnima] AiO save template result is too long.")
        pieces.append(rendered)
        result_length += len(rendered)
    return "".join(pieces)


def _bounded_image_saver_timestamp(
    now: datetime,
    time_format: str,
    max_length: int,
) -> str:
    try:
        return _render_strftime_bounded(now, time_format, max_length)
    except (OSError, ValueError):
        return _render_strftime_bounded(
            now,
            _IMAGE_SAVER_SAFE_TIME_FORMAT,
            max_length,
        )


def _bounded_integer_text(value: int, max_length: int, *, padding: int = 0) -> str:
    sign_length = int(value < 0)
    digit_limit = max_length - sign_length
    if digit_limit < 1 or padding > max_length or abs(value) >= 10**digit_limit:
        raise RuntimeError("[EasyUseAnima] AiO save template result is too long.")
    rendered = f"{value:0{padding}d}" if padding else str(value)
    if len(rendered) > max_length:
        raise RuntimeError("[EasyUseAnima] AiO save template result is too long.")
    return rendered


def _bounded_template_replace_with(
    value: str,
    token: str,
    replacement: Callable[[int], str],
) -> str:
    count = value.count(token)
    if not count:
        return value
    fixed_length = len(value) - count * len(token)
    if fixed_length > _MAX_OUTPUT_TEMPLATE_LENGTH:
        raise RuntimeError("[EasyUseAnima] AiO save template result is too long.")
    replacement_limit = (_MAX_OUTPUT_TEMPLATE_LENGTH - fixed_length) // count
    rendered = replacement(replacement_limit)
    if len(rendered) > replacement_limit:
        raise RuntimeError("[EasyUseAnima] AiO save template result is too long.")
    return value.replace(token, rendered)


def _bounded_template_replace(value: str, token: str, replacement: str) -> str:
    return _bounded_template_replace_with(
        value,
        token,
        lambda _max_length: replacement,
    )


def _bounded_template_sub(
    pattern: re.Pattern[str],
    replacement: Callable[[re.Match[str], int], str],
    value: str,
) -> str:
    pieces: list[str] = []
    cursor = 0
    result_length = 0
    matched = False
    for match in pattern.finditer(value):
        matched = True
        literal = value[cursor : match.start()]
        replacement_limit = _MAX_OUTPUT_TEMPLATE_LENGTH - result_length - len(literal)
        if replacement_limit < 0:
            raise RuntimeError("[EasyUseAnima] AiO save template result is too long.")
        rendered = replacement(match, replacement_limit)
        if len(rendered) > replacement_limit:
            raise RuntimeError("[EasyUseAnima] AiO save template result is too long.")
        pieces.extend((literal, rendered))
        result_length += len(literal) + len(rendered)
        cursor = match.end()
    if not matched:
        return value
    tail = value[cursor:]
    if result_length + len(tail) > _MAX_OUTPUT_TEMPLATE_LENGTH:
        raise RuntimeError("[EasyUseAnima] AiO save template result is too long.")
    pieces.append(tail)
    return "".join(pieces)


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
    if (
        len(value) > _MAX_OUTPUT_TEMPLATE_LENGTH
        or len(str(time_format or "")) > _MAX_OUTPUT_TIME_FORMAT_LENGTH
    ):
        raise RuntimeError("[EasyUseAnima] AiO save template is too long.")

    def replace_time(match: re.Match[str], max_length: int) -> str:
        return _bounded_image_saver_timestamp(now, match.group(1), max_length)

    def replace_counter(match: re.Match[str], max_length: int) -> str:
        padding = int(match.group(1))
        if padding > 32:
            raise RuntimeError(
                "[EasyUseAnima] AiO save counter padding must be 32 or less."
            )
        return _bounded_integer_text(counter, max_length, padding=padding)

    model_filename, base_model_name = _image_saver_model_names(modelname)
    value = _bounded_template_sub(_IMAGE_SAVER_CUSTOM_TIME_RE, replace_time, value)
    value = _bounded_template_sub(_IMAGE_SAVER_CUSTOM_COUNTER_RE, replace_counter, value)
    replacements = (
        ("%date", lambda limit: _bounded_image_saver_timestamp(now, "%Y-%m-%d", limit)),
        ("%time", lambda limit: _bounded_image_saver_timestamp(now, time_format, limit)),
        ("%model", lambda _limit: model_filename),
        ("%width", lambda limit: _bounded_integer_text(width, limit)),
        ("%height", lambda limit: _bounded_integer_text(height, limit)),
        ("%seed", lambda limit: _bounded_integer_text(seed, limit)),
        ("%counter", lambda limit: _bounded_integer_text(counter, limit)),
        ("%sampler_name", lambda _limit: sampler_name),
        ("%steps", lambda limit: _bounded_integer_text(steps, limit)),
        ("%cfg", lambda _limit: str(cfg)),
        ("%scheduler_name", lambda _limit: scheduler_name),
        ("%basemodelname", lambda _limit: base_model_name),
        ("%denoise", lambda _limit: str(denoise)),
        ("%clip_skip", lambda limit: _bounded_integer_text(clip_skip, limit)),
        ("%custom", lambda _limit: custom),
    )
    for token, replacement in replacements:
        value = _bounded_template_replace_with(value, token, replacement)
    if "%" in value:
        raise RuntimeError(
            "[EasyUseAnima] AiO save template contains an unsupported placeholder."
        )
    if len(value) > _MAX_OUTPUT_TEMPLATE_LENGTH:
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
        rendered_filename = _bounded_image_saver_timestamp(
            now,
            time_format,
            _MAX_OUTPUT_TEMPLATE_LENGTH,
        )
    rendered_filename = _sanitize_native_output_filename(rendered_filename)
    output_root = _comfy_output_directory()
    safe_path = _validated_output_subpath(
        rendered_path,
        field="path",
        allow_empty=True,
        output_root=output_root,
    )
    safe_filename = _validated_output_subpath(
        rendered_filename,
        field="filename",
        filename=True,
        output_root=output_root,
    )
    extension = str(image_saver.get("extension") or defaults["extension"]).casefold()
    if extension not in {"png", "jpeg", "jpg", "webp"}:
        raise RuntimeError("[EasyUseAnima] AiO save extension is invalid.")
    return _ImageSaverRuntime(
        output_root=output_root,
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
    *,
    budget: CivitaiLookupBudget | None = None,
) -> list[str]:
    raw_settings = image_saver.get("civitai_hash_fetchers")
    if isinstance(raw_settings, list) and len(raw_settings) > _MAX_CIVITAI_HASH_FETCHERS:
        logger.warning(
            "[EasyUseAnima] Civitai Hash Fetcher row limit is %s; ignoring %s excess rows.",
            _MAX_CIVITAI_HASH_FETCHERS,
            len(raw_settings) - _MAX_CIVITAI_HASH_FETCHERS,
        )
    enabled_settings = [
        item
        for item in _normalize_aio_civitai_hash_fetchers(
            raw_settings
        )
        if _as_bool(item.get("enabled"), True)
    ]
    if not enabled_settings:
        return []

    entries: list[str] = []
    for item in enabled_settings:
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
            if budget is None:
                fetched_hash = _fetch_civitai_autov3_hash(
                    username,
                    model_name,
                    version,
                )
            else:
                fetched_hash = _fetch_civitai_autov3_hash(
                    username,
                    model_name,
                    version,
                    budget=budget,
                )
            hash_text = str(fetched_hash or "").strip()
        except CivitaiLookupBudgetExhausted as exc:
            logger.warning(
                "[EasyUseAnima] Civitai Hash Fetcher budget ended; "
                "saving with available metadata: %s",
                _safe_civitai_log_value(exc),
            )
            break
        except Exception as exc:
            logger.warning(
                "[EasyUseAnima] Civitai Hash Fetcher failed for username=%r model=%r version=%r; skipping metadata hash: %s",
                _safe_civitai_log_value(username),
                _safe_civitai_log_value(model_name),
                _safe_civitai_log_value(version),
                _safe_civitai_log_value(exc),
            )
            continue
        if not hash_text:
            logger.warning(
                "[EasyUseAnima] Civitai Hash Fetcher returned no usable hash for username=%r model=%r version=%r; "
                "skipping metadata hash: %s",
                _safe_civitai_log_value(username),
                _safe_civitai_log_value(model_name),
                _safe_civitai_log_value(version),
                "empty hash",
            )
            continue
        entries.append(f"{model_name}:{hash_text}")
    return entries


def _safe_civitai_log_value(value) -> str:
    try:
        text = str(value or "")
    except Exception:
        return "<unprintable>"
    truncated = len(text) > _MAX_CIVITAI_LOG_CHARACTERS
    text = text[:_MAX_CIVITAI_LOG_CHARACTERS]
    text = "".join(
        "?"
        if unicodedata.category(character) in _UNSAFE_LOG_CATEGORIES
        else character
        for character in text
    )
    return f"{text}..." if truncated else text


def _join_aio_hash_parts(parts) -> str:
    kept: list[str] = []
    used_bytes = 0
    for part in parts:
        if not isinstance(part, str) or not part:
            continue
        try:
            part_bytes = len(part.encode("utf-8"))
        except UnicodeEncodeError:
            continue
        required_bytes = part_bytes + int(bool(kept))
        if used_bytes + required_bytes > _MAX_JOINED_HASH_BYTES:
            break
        kept.append(part)
        used_bytes += required_bytes
    return ",".join(kept)


def _aio_image_saver_additional_hashes(
    image_saver: dict[str, Any],
    *,
    budget: CivitaiLookupBudget | None = None,
) -> str:
    parts = []
    base = _normalize_aio_hash_text(image_saver.get("additional_hashes"))
    if base:
        parts.append(base)
    parts.extend(
        _normalize_aio_hash_bundles(image_saver.get("additional_hash_bundles"))
    )
    if budget is None:
        parts.extend(_aio_image_saver_civitai_hash_fetcher_entries(image_saver))
    else:
        parts.extend(
            _aio_image_saver_civitai_hash_fetcher_entries(
                image_saver,
                budget=budget,
            )
        )
    return _join_aio_hash_parts(parts)


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
    values = applied_loras if isinstance(applied_loras, (list, tuple)) else ()
    for item in values:
        if not isinstance(item, Mapping):
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

    if _comfy_metadata_enabled():
        _validate_parameter_sources(
            positive_prompt,
            negative_prompt,
            runtime.custom,
        )
        civitai_budget = CivitaiLookupBudget()
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
        metadata_negative = (
            str(negative_prompt or "unknown") if save_prompt_metadata else ""
        )
        download_civitai_data = _as_bool(
            runtime.settings.get("download_civitai_data"),
            runtime.defaults["download_civitai_data"],
        )
        metadata = _build_native_metadata(
            modelname=runtime.modelname,
            positive=metadata_positive,
            negative=metadata_negative,
            width=runtime.width,
            height=runtime.height,
            seed=runtime.seed,
            steps=runtime.steps,
            cfg=runtime.cfg,
            sampler_name=runtime.sampler_name,
            scheduler_name=runtime.scheduler_name,
            denoise=runtime.denoise,
            clip_skip=runtime.clip_skip,
            custom=runtime.custom,
            additional_hashes=_aio_image_saver_additional_hashes(
                runtime.settings,
                budget=civitai_budget,
            ),
            applied_loras=applied_loras,
            download_civitai_data=download_civitai_data,
            easy_remix=_as_bool(
                runtime.settings.get("easy_remix"), runtime.defaults["easy_remix"]
            ),
            civitai_budget=civitai_budget,
        )
    else:
        metadata = NativeImageMetadata(parameters="", final_hashes="", hashes={})
    return _save_native_images(
        images,
        output_root=runtime.output_root,
        path=runtime.path,
        filename=runtime.filename,
        extension=runtime.extension,
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
        save_workflow_as_json=_as_bool(
            runtime.settings.get("save_workflow_as_json"),
            runtime.defaults["save_workflow_as_json"],
        ),
        embed_workflow=_as_bool(
            runtime.settings.get("embed_workflow"),
            runtime.defaults["embed_workflow"],
        ),
        metadata=metadata,
        prompt=workflow_prompt,
        extra_pnginfo=extra_pnginfo,
    )


__all__ = ()
