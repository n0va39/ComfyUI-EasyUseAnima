"""EasyUse-owned image output, A1111 metadata, and Civitai hash helpers."""

from __future__ import annotations

import hashlib
import json
import logging
import math
import os
import re
import tempfile
import threading
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path, PurePosixPath, PureWindowsPath
from types import MappingProxyType
from typing import cast

from .native_civitai import (
    _fetch_civitai_autov3_hash as _fetch_civitai_autov3_hash,
)
from .native_civitai import _fetch_civitai_resource_by_hash

logger = logging.getLogger("ComfyUI-EasyUseAnima")

_JPEG_EXIF_LIMIT = 65_000
_MAX_REMOTE_RESOURCES = 32
_MAX_MANUAL_HASHES = 30
_MAX_MANUAL_HASH_TEXT = 8_192
_USER_COMMENT_PREFIX = b"UNICODE\0"
_LORA_TAG_RE = re.compile(r"<lora:([^>:]+)(?::([^>]+))?>", re.IGNORECASE)
_EMBEDDING_RE = re.compile(r"embedding:([^,\s()]+)", re.IGNORECASE)
_SAFE_HASH_RE = re.compile(r"^[A-Za-z0-9_-]{1,128}$")
_CONTROL_RE = re.compile(r"[\x00-\x1f\x7f]")
_SAVE_LOCK = threading.Lock()

_CIVITAI_SAMPLER_NAMES = MappingProxyType({
    "euler_ancestral": "Euler a", "euler": "Euler",
    "lms": "LMS", "heun": "Heun",
    "dpm_2": "DPM2", "dpm_2_ancestral": "DPM2 a",
    "dpmpp_2s_ancestral": "DPM++ 2S a", "dpmpp_2m": "DPM++ 2M",
    "dpmpp_sde": "DPM++ SDE", "dpmpp_2m_sde": "DPM++ 2M SDE",
    "dpmpp_3m_sde": "DPM++ 3M SDE", "dpm_fast": "DPM fast",
    "dpm_adaptive": "DPM adaptive", "ddim": "DDIM",
    "plms": "PLMS", "uni_pc_bh2": "UniPC", "uni_pc": "UniPC", "lcm": "LCM",
})


@dataclass(frozen=True, slots=True)
class NativeImageMetadata:
    parameters: str
    final_hashes: str
    hashes: dict[str, str]


@dataclass(frozen=True, slots=True)
class _ResourceHash:
    display_name: str
    metadata_key: str
    path: Path | None
    sha256: str
    weight: float | None = None

    @property
    def short_hash(self) -> str:
        return self.sha256[:10]


@dataclass(frozen=True, slots=True)
class _SerializedMetadata:
    pnginfo: object | None
    exif_bytes: bytes | None
    workflow_json: str | None
    force_workflow_sidecar: bool


def _compact_json(value: object, *, ascii_only: bool) -> str:
    return json.dumps(
        value,
        allow_nan=False,
        ensure_ascii=ascii_only,
        separators=(",", ":"),
    )


def _supported_model_extensions() -> set[str]:
    try:
        import folder_paths  # type: ignore

        return set(getattr(folder_paths, "supported_pt_extensions", ())) | {".gguf"}
    except Exception:
        return {".safetensors", ".pt", ".ckpt", ".bin", ".pth", ".gguf"}


def _resource_name(value: str) -> str:
    filename = str(value or "").strip().replace("\\", "/").strip("/").rsplit("/", 1)[-1]
    stem, extension = os.path.splitext(filename)
    return stem if extension.casefold() in _supported_model_extensions() else filename


def _lora_metadata_name(value: str) -> str:
    normalized = str(value or "").strip().replace("\\", "/").strip("/")
    stem, extension = os.path.splitext(normalized)
    return stem if extension.casefold() in _supported_model_extensions() else normalized


def _resolve_resource_path(folder_names: Sequence[str], name: str) -> Path | None:
    if not str(name or "").strip():
        return None
    try:
        import folder_paths  # type: ignore
    except Exception:
        return None

    get_full_path = getattr(folder_paths, "get_full_path", None)
    if not callable(get_full_path):
        return None
    for folder_name in folder_names:
        try:
            value = get_full_path(folder_name, name)
        except Exception as exc:
            logger.warning(
                "[EasyUseAnima] Could not resolve %s resource %r: %s",
                folder_name,
                name,
                exc,
            )
            continue
        if not value:
            continue
        path = Path(str(value)).resolve(strict=False)
        if path.is_file():
            return path
    return None


@lru_cache(maxsize=128)
def _hash_file_revision(path_text: str, size: int, modified_ns: int) -> str:
    del size, modified_ns
    digest = hashlib.sha256()
    with Path(path_text).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _hash_file(path: Path) -> str:
    stat = path.stat()
    return _hash_file_revision(str(path), stat.st_size, stat.st_mtime_ns)


def _local_resource_hashes(
    modelname: str,
    applied_loras: object,
) -> list[_ResourceHash]:
    resources: list[_ResourceHash] = []
    model_path = _resolve_resource_path(("diffusion_models", "checkpoints"), modelname)
    if model_path is not None:
        try:
            resources.append(
                _ResourceHash(
                    display_name=_resource_name(modelname),
                    metadata_key="model",
                    path=model_path,
                    sha256=_hash_file(model_path),
                )
            )
        except OSError as exc:
            logger.warning(
                "[EasyUseAnima] Could not hash model %r; continuing without its hash: %s",
                modelname,
                exc,
            )

    values = applied_loras if isinstance(applied_loras, (list, tuple)) else ()
    seen_names: set[str] = set()
    for item in values:
        if not isinstance(item, Mapping):
            continue
        source_name = str(item.get("name") or "").strip()
        metadata_name = _lora_metadata_name(source_name)
        if not metadata_name or metadata_name.casefold() in seen_names:
            continue
        seen_names.add(metadata_name.casefold())
        lora_path = _resolve_resource_path(("loras",), source_name)
        if lora_path is None:
            logger.warning(
                "[EasyUseAnima] Could not locate LoRA %r; continuing without its Civitai hash.",
                source_name,
            )
            continue
        try:
            strength = float(item.get("strength_model", 1.0))
        except (TypeError, ValueError):
            strength = 1.0
        if not math.isfinite(strength):
            strength = 1.0
        try:
            sha256 = _hash_file(lora_path)
        except OSError as exc:
            logger.warning(
                "[EasyUseAnima] Could not hash LoRA %r; continuing without its hash: %s",
                source_name,
                exc,
            )
            continue
        resources.append(
            _ResourceHash(
                display_name=metadata_name,
                metadata_key=f"LORA:{metadata_name}",
                path=lora_path,
                sha256=sha256,
                weight=strength,
            )
        )
    return resources


def _manual_resource_hashes(value: str) -> list[_ResourceHash]:
    text = str(value or "")[:_MAX_MANUAL_HASH_TEXT]
    resources: list[_ResourceHash] = []
    unnamed_index = 0
    seen_hashes: set[str] = set()
    for raw_entry in text.replace("\r", "\n").replace("\n", ",").split(","):
        entry = raw_entry.strip()
        if not entry:
            continue
        pieces = [part.strip() for part in entry.split(":")]
        if not all(pieces):
            logger.warning(
                "[EasyUseAnima] Skipping malformed additional Civitai hash entry: %r",
                entry,
            )
            continue

        weight: float | None = None
        if len(pieces) >= 2:
            try:
                weight = float(pieces[-1])
            except ValueError:
                pass
            else:
                if not math.isfinite(weight):
                    logger.warning(
                        "[EasyUseAnima] Skipping non-finite additional Civitai hash weight: %r",
                        entry,
                    )
                    continue
                pieces = pieces[:-1]

        if len(pieces) > 2:
            logger.warning(
                "[EasyUseAnima] Skipping ambiguous additional Civitai hash entry: %r",
                entry,
            )
            continue

        if len(pieces) == 1:
            unnamed_index += 1
            name = f"manual{unnamed_index}"
            hash_value = pieces[0]
        else:
            name = ":".join(pieces[:-1]).strip()
            hash_value = pieces[-1]
        if (
            not name
            or _CONTROL_RE.search(name)
            or not _SAFE_HASH_RE.fullmatch(hash_value)
        ):
            logger.warning(
                "[EasyUseAnima] Skipping invalid additional Civitai hash entry: %r",
                entry,
            )
            continue
        normalized_hash = hash_value.casefold()
        if normalized_hash in seen_hashes:
            continue
        seen_hashes.add(normalized_hash)
        resources.append(
            _ResourceHash(
                display_name=name,
                metadata_key=name,
                path=None,
                sha256=hash_value,
                weight=weight,
            )
        )
        if len(resources) >= _MAX_MANUAL_HASHES:
            break
    return resources


def _clean_prompt_for_remix(prompt: str) -> str:
    value = _LORA_TAG_RE.sub("", str(prompt or ""))

    def simplify_embedding(match: re.Match[str]) -> str:
        name = match.group(1).replace("\\", "/").rsplit("/", 1)[-1]
        return f"embedding:{name}"

    return re.sub(r"\s{2,}", " ", _EMBEDDING_RE.sub(simplify_embedding, value)).strip()


def _civitai_sampler_name(sampler_name: str, scheduler_name: str) -> str:
    sampler = str(sampler_name or "").replace("_gpu", "")
    scheduler = str(scheduler_name or "normal")
    mapped = _CIVITAI_SAMPLER_NAMES.get(sampler, sampler)
    if scheduler == "karras":
        return f"{mapped} Karras"
    if scheduler == "exponential":
        return f"{mapped} Exponential"
    if scheduler != "normal" and sampler not in _CIVITAI_SAMPLER_NAMES:
        return f"{sampler}_{scheduler}"
    return mapped


def _civitai_resource_entries(
    resources: Sequence[_ResourceHash],
) -> list[dict[str, str | float | int]]:
    entries: list[dict[str, str | float | int]] = []
    for resource in resources[:_MAX_REMOTE_RESOURCES]:
        if len(resource.sha256) != 64:
            continue
        descriptor = _fetch_civitai_resource_by_hash(resource.sha256)
        if descriptor is None:
            continue
        entry: dict[str, str | float | int] = {}
        if descriptor.model_name:
            entry["modelName"] = descriptor.model_name
        if descriptor.version_name:
            entry["versionName"] = descriptor.version_name
        if resource.weight is not None:
            entry["weight"] = resource.weight
        if descriptor.air:
            entry["air"] = descriptor.air
        elif descriptor.model_version_id is not None:
            entry["modelVersionId"] = descriptor.model_version_id
        if "air" in entry or "modelVersionId" in entry:
            entries.append(entry)
    return entries


def _build_native_metadata(
    *,
    modelname: str,
    positive: str,
    negative: str,
    width: int,
    height: int,
    seed: int,
    steps: int,
    cfg: float,
    sampler_name: str,
    scheduler_name: str,
    denoise: float,
    clip_skip: int,
    custom: str,
    additional_hashes: str,
    applied_loras: object,
    download_civitai_data: bool,
    easy_remix: bool,
) -> NativeImageMetadata:
    local_resources = _local_resource_hashes(modelname, applied_loras)
    manual_resources = _manual_resource_hashes(additional_hashes)
    resources = [*local_resources, *manual_resources]

    hashes: dict[str, str] = {}
    final_parts: list[str] = []
    seen_hashes: set[str] = set()
    for resource in resources:
        short_hash = resource.short_hash
        normalized_hash = short_hash.casefold()
        if not short_hash or normalized_hash in seen_hashes:
            continue
        seen_hashes.add(normalized_hash)
        hashes[resource.metadata_key] = short_hash
        weight = (
            f":{resource.weight:g}"
            if resource.weight is not None
            else ""
        )
        final_parts.append(f"{resource.display_name}:{short_hash}{weight}")

    model_hash = hashes.get("model", "")
    visible_positive = (
        _clean_prompt_for_remix(positive) if easy_remix else str(positive or "").strip()
    )
    visible_negative = (
        _clean_prompt_for_remix(negative) if easy_remix else str(negative or "").strip()
    )
    lines = [visible_positive] if visible_positive else []
    if visible_negative:
        lines.append(f"Negative prompt: {visible_negative}")
    fields = [
        f"Steps: {steps}",
        f"Sampler: {_civitai_sampler_name(sampler_name, scheduler_name)}",
        f"CFG scale: {cfg}",
        f"Seed: {seed}",
        f"Size: {width}x{height}",
    ]
    if denoise != 1.0:
        fields.append(f"Denoising strength: {denoise:g}")
    if clip_skip:
        fields.append(f"Clip skip: {abs(clip_skip)}")
    if str(custom or "").strip():
        fields.append(str(custom).strip().strip(", "))
    if model_hash:
        fields.append(f"Model hash: {model_hash}")
    fields.append(f"Model: {_resource_name(modelname)}")
    if hashes:
        fields.append(f"Hashes: {_compact_json(hashes, ascii_only=False)}")
    fields.append("Version: ComfyUI")
    if download_civitai_data:
        civitai_resources = _civitai_resource_entries(local_resources)
        if civitai_resources:
            fields.append(
                f"Civitai resources: {_compact_json(civitai_resources, ascii_only=False)}"
            )
    lines.append(", ".join(fields))
    return NativeImageMetadata(
        parameters="\n".join(lines),
        final_hashes=",".join(final_parts),
        hashes=hashes,
    )


def _comfy_metadata_enabled() -> bool:
    try:
        from comfy.cli_args import args  # type: ignore

        return not bool(getattr(args, "disable_metadata", False))
    except Exception:
        return True


def _encode_user_comment(value: str) -> bytes:
    return _USER_COMMENT_PREFIX + str(value or "").encode("utf-16-be")


def _build_exif_bytes(
    parameters: str,
    prompt_json: str | None,
    extra_json: Sequence[tuple[str, str]],
) -> bytes:
    from PIL import ExifTags, Image  # pyright: ignore[reportMissingImports]

    exif = Image.Exif()
    if parameters:
        exif.get_ifd(ExifTags.IFD.Exif)[0x9286] = _encode_user_comment(parameters)
    if prompt_json is not None:
        exif[0x0110] = f"prompt:{prompt_json}"
    for index, (key, value) in enumerate(extra_json):
        tag = 0x010F - index
        if tag <= 0:
            break
        exif[tag] = f"{key}:{value}"
    return exif.tobytes()


def _serialize_metadata(
    *,
    extension: str,
    parameters: str,
    prompt: object | None,
    extra_pnginfo: Mapping[str, object] | None,
    embed_workflow: bool,
    save_workflow_as_json: bool,
    write_metadata: bool,
) -> _SerializedMetadata:
    if not write_metadata:
        return _SerializedMetadata(None, None, None, False)

    workflow = (
        extra_pnginfo.get("workflow")
        if isinstance(extra_pnginfo, Mapping)
        else None
    )
    workflow_json = (
        json.dumps(workflow, allow_nan=False, ensure_ascii=False, indent=2)
        if workflow is not None and (embed_workflow or save_workflow_as_json)
        else None
    )
    prompt_json = (
        _compact_json(prompt, ascii_only=True)
        if embed_workflow and prompt is not None
        else None
    )
    extra_json: list[tuple[str, str]] = []
    if embed_workflow:
        for key, value in cast(Mapping[str, object], extra_pnginfo or {}).items():
            key_text = str(key)
            if key_text in {"parameters", "prompt"}:
                logger.warning(
                    "[EasyUseAnima] Ignoring reserved extra_pnginfo key %r.",
                    key_text,
                )
                continue
            extra_json.append((key_text, _compact_json(value, ascii_only=True)))

    if extension == "png":
        from PIL.PngImagePlugin import PngInfo  # pyright: ignore[reportMissingImports]

        pnginfo = PngInfo()
        if parameters:
            pnginfo.add_text("parameters", parameters)
        if prompt_json is not None:
            pnginfo.add_text("prompt", prompt_json)
        for key, value in extra_json:
            pnginfo.add_text(key, value)
        return _SerializedMetadata(pnginfo, None, workflow_json, False)

    exif_bytes = _build_exif_bytes(parameters, prompt_json, extra_json)
    force_sidecar = False
    if extension in {"jpg", "jpeg"} and len(exif_bytes) > _JPEG_EXIF_LIMIT:
        exif_bytes = _build_exif_bytes(parameters, None, extra_json)
        if len(exif_bytes) > _JPEG_EXIF_LIMIT:
            exif_bytes = _build_exif_bytes(parameters, None, ())
            force_sidecar = workflow_json is not None
        if len(exif_bytes) > _JPEG_EXIF_LIMIT:
            raise RuntimeError(
                "[EasyUseAnima] A1111 metadata is too large for JPEG EXIF; use PNG/WebP or shorten the prompt."
            )
        logger.warning(
            "[EasyUseAnima] JPEG workflow metadata exceeded EXIF limits; preserving A1111 parameters and writing a workflow JSON sidecar."
        )
    return _SerializedMetadata(None, exif_bytes, workflow_json, force_sidecar)


def _tensor_to_pil(image: object):
    import numpy as np  # pyright: ignore[reportMissingImports]
    from PIL import Image  # pyright: ignore[reportMissingImports]

    value = image
    detach = getattr(value, "detach", None)
    if callable(detach):
        value = detach()
    cpu = getattr(value, "cpu", None)
    if callable(cpu):
        value = cpu()
    numpy_method = getattr(value, "numpy", None)
    array = numpy_method() if callable(numpy_method) else np.asarray(value)
    array = np.asarray(array)
    if array.ndim == 3 and array.shape[-1] == 1:
        array = array[..., 0]
    if array.ndim not in {2, 3}:
        raise RuntimeError("[EasyUseAnima] AiO image output must be an HxW or HxWxC tensor.")
    pixels = np.clip(array * 255.0, 0, 255).astype(np.uint8)
    return Image.fromarray(pixels)


def _allocate_filenames(
    output_folder: Path,
    filename: str,
    extension: str,
    count: int,
    *,
    sidecar_required: bool,
) -> list[str]:
    def occupied(name: str) -> bool:
        image_path = output_folder / name
        return image_path.exists() or (
            sidecar_required and image_path.with_suffix(".json").exists()
        )

    plain = f"{filename}.{extension}"
    if count == 1 and not occupied(plain):
        return [plain]

    patterns = [
        re.compile(
            rf"^{re.escape(filename)}_(\d+)\.{re.escape(extension)}$",
            re.IGNORECASE,
        )
    ]
    if sidecar_required:
        patterns.append(
            re.compile(rf"^{re.escape(filename)}_(\d+)\.json$", re.IGNORECASE)
        )
    suffixes: list[int] = []
    for existing in output_folder.iterdir():
        if not existing.is_file():
            continue
        for pattern in patterns:
            match = pattern.fullmatch(existing.name)
            if match is not None:
                suffixes.append(int(match.group(1)))
                break
    suffix = max(suffixes, default=0) + 1
    names: list[str] = []
    while len(names) < count:
        candidate = f"{filename}_{suffix:02d}.{extension}"
        if not occupied(candidate):
            names.append(candidate)
        suffix += 1
    return names


def _atomic_save_image(image: object, target: Path, *, image_format: str, options: dict[str, object]) -> None:
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=".easyuse-anima-",
        suffix=".tmp",
        dir=target.parent,
    )
    os.close(descriptor)
    temporary = Path(temporary_name)
    try:
        save = getattr(image, "save", None)
        if not callable(save):
            raise RuntimeError("[EasyUseAnima] Pillow image writer is unavailable.")
        save(str(temporary), format=image_format, **options)
        os.replace(temporary, target)
    finally:
        temporary.unlink(missing_ok=True)


def _atomic_write_text(target: Path, value: str) -> None:
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=".easyuse-anima-",
        suffix=".tmp",
        dir=target.parent,
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(value)
        os.replace(temporary, target)
    finally:
        temporary.unlink(missing_ok=True)


def _resolve_native_output_folder(output_root: Path, path: str) -> tuple[Path, Path]:
    raw_path = str(path or "").strip()
    if len(raw_path) > 1024 or _CONTROL_RE.search(raw_path):
        raise RuntimeError("[EasyUseAnima] AiO save path is invalid.")
    posix_path = PurePosixPath(raw_path)
    windows_path = PureWindowsPath(raw_path)
    parts = [part for part in re.split(r"[\\/]", raw_path) if part]
    if (
        posix_path.is_absolute()
        or windows_path.drive
        or windows_path.root
        or any(part in {".", ".."} or ":" in part for part in parts)
    ):
        raise RuntimeError(
            "[EasyUseAnima] AiO save path must stay within the ComfyUI output directory."
        )

    root = Path(output_root).resolve(strict=False)
    root.mkdir(parents=True, exist_ok=True)
    root = root.resolve(strict=True)
    candidate = root.joinpath(*parts).resolve(strict=False)
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise RuntimeError(
            "[EasyUseAnima] AiO save path must stay within the ComfyUI output directory."
        ) from exc
    candidate.mkdir(parents=True, exist_ok=True)
    resolved = candidate.resolve(strict=True)
    try:
        return resolved, resolved.relative_to(root)
    except ValueError as exc:
        raise RuntimeError(
            "[EasyUseAnima] AiO save path must stay within the ComfyUI output directory."
        ) from exc


def _image_save_options(
    image_format: str,
    *,
    quality: int,
    lossless_webp: bool,
    optimize_png: bool,
    serialized: _SerializedMetadata,
) -> dict[str, object]:
    if image_format == "PNG":
        return {"optimize": bool(optimize_png), "pnginfo": serialized.pnginfo}
    if image_format == "WEBP":
        options: dict[str, object] = {
            "quality": quality,
            "lossless": bool(lossless_webp),
            "method": 4,
        }
    else:
        options = {"quality": quality, "optimize": True}
    if serialized.exif_bytes:
        options["exif"] = serialized.exif_bytes
    return options


def _save_native_images(
    images: Iterable[object],
    *,
    output_root: Path,
    path: str,
    filename: str,
    extension: str,
    quality_jpeg_or_webp: int,
    lossless_webp: bool,
    optimize_png: bool,
    embed_workflow: bool,
    save_workflow_as_json: bool,
    metadata: NativeImageMetadata,
    prompt: object | None,
    extra_pnginfo: Mapping[str, object] | None,
) -> dict[str, object]:
    batch = list(images)
    if not batch:
        raise RuntimeError("[EasyUseAnima] AiO image output received an empty image batch.")

    safe_extension = str(extension or "").casefold()
    if safe_extension not in {"png", "jpg", "jpeg", "webp"}:
        raise RuntimeError("[EasyUseAnima] AiO save extension is invalid.")
    if (
        not filename
        or filename in {".", ".."}
        or len(f"{filename}.{safe_extension}") > 255
        or "/" in filename
        or "\\" in filename
        or ":" in filename
        or _CONTROL_RE.search(filename)
    ):
        raise RuntimeError("[EasyUseAnima] AiO save filename is invalid.")
    resolved_folder, relative_folder = _resolve_native_output_folder(output_root, path)

    serialized = _serialize_metadata(
        extension=safe_extension,
        parameters=metadata.parameters,
        prompt=prompt,
        extra_pnginfo=extra_pnginfo,
        embed_workflow=embed_workflow,
        save_workflow_as_json=save_workflow_as_json,
        write_metadata=_comfy_metadata_enabled(),
    )
    quality = max(1, min(100, int(quality_jpeg_or_webp)))
    image_format = {
        "png": "PNG",
        "jpg": "JPEG",
        "jpeg": "JPEG",
        "webp": "WEBP",
    }[safe_extension]
    results: list[dict[str, str]] = []
    sidecar_required = serialized.workflow_json is not None and (
        save_workflow_as_json or serialized.force_workflow_sidecar
    )
    with _SAVE_LOCK:
        names = _allocate_filenames(
            resolved_folder,
            filename,
            safe_extension,
            len(batch),
            sidecar_required=sidecar_required,
        )
        for image_value, final_name in zip(batch, names, strict=True):
            image = _tensor_to_pil(image_value)
            if image_format == "JPEG" and getattr(image, "mode", "") not in {"RGB", "L"}:
                image = image.convert("RGB")
            options = _image_save_options(
                image_format,
                quality=quality,
                lossless_webp=lossless_webp,
                optimize_png=optimize_png,
                serialized=serialized,
            )

            target = resolved_folder / final_name
            image_committed = False
            try:
                _atomic_save_image(
                    image,
                    target,
                    image_format=image_format,
                    options=options,
                )
                image_committed = True
                if sidecar_required and serialized.workflow_json is not None:
                    _atomic_write_text(
                        target.with_suffix(".json"),
                        serialized.workflow_json,
                    )
            except Exception:
                if image_committed:
                    target.unlink(missing_ok=True)
                raise
            results.append(
                {
                    "filename": final_name,
                    "subfolder": "" if str(relative_folder) == "." else relative_folder.as_posix(),
                    "type": "output",
                }
            )

    return {
        "ui": {"images": results},
        "result": (metadata.final_hashes, metadata.parameters),
    }


__all__ = ()
