"""EasyUse-owned image output, A1111 metadata, and Civitai hash helpers."""

from __future__ import annotations

import json
import logging
import re
import threading
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path, PurePosixPath, PureWindowsPath
from types import MappingProxyType
from typing import cast

from .native_civitai import (
    CivitaiLookupBudget,
    CivitaiLookupBudgetExhausted,
    _fetch_civitai_resource_by_hash,
)
from .native_civitai import (
    _fetch_civitai_autov3_hash as _fetch_civitai_autov3_hash,
)
from .native_output_publication import (
    OutputDirectoryBinding,
    PublicationCollision,
    publish_image_transaction,
)
from .native_resource_hashes import (
    _EMBEDDING_RE,
    _HEX_HASH_RE,
    _local_resource_hashes,
    _manual_resource_hashes,
    _resource_name,
    _ResourceHash,
)

logger = logging.getLogger("ComfyUI-EasyUseAnima")

_JPEG_EXIF_LIMIT = 65_000
_MAX_REMOTE_RESOURCES = 32
_USER_COMMENT_PREFIX = b"UNICODE\0"
_LORA_TAG_RE = re.compile(r"<lora:([^>:]+)(?::([^>]+))?>", re.IGNORECASE)
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
    *,
    budget: CivitaiLookupBudget | None = None,
) -> list[dict[str, str | float | int]]:
    entries: list[dict[str, str | float | int]] = []
    seen_hashes: set[str] = set()
    seen_identifiers: set[str] = set()
    attempts = 0
    for resource in resources:
        normalized_hash = resource.sha256.casefold()
        if (
            not _HEX_HASH_RE.fullmatch(normalized_hash)
            or normalized_hash in seen_hashes
        ):
            continue
        if attempts >= _MAX_REMOTE_RESOURCES:
            break
        seen_hashes.add(normalized_hash)
        attempts += 1
        try:
            if budget is None:
                descriptor = _fetch_civitai_resource_by_hash(resource.sha256)
            else:
                descriptor = _fetch_civitai_resource_by_hash(
                    resource.sha256,
                    budget=budget,
                )
        except CivitaiLookupBudgetExhausted as exc:
            logger.warning(
                "[EasyUseAnima] Civitai resource enrichment budget ended; "
                "saving with available metadata: %s",
                exc,
            )
            break
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
            identifier = f"air:{descriptor.air.casefold()}"
        elif descriptor.model_version_id is not None:
            entry["modelVersionId"] = descriptor.model_version_id
            identifier = f"version:{descriptor.model_version_id}"
        else:
            continue
        if identifier not in seen_identifiers:
            seen_identifiers.add(identifier)
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
    civitai_budget: CivitaiLookupBudget | None = None,
) -> NativeImageMetadata:
    local_resources = _local_resource_hashes(
        modelname,
        applied_loras,
        (positive, negative),
    )
    manual_resources = _manual_resource_hashes(additional_hashes)
    resources = [*local_resources, *manual_resources]

    hashes: dict[str, str] = {}
    final_parts: list[str] = []
    seen_hashes: set[str] = set()
    seen_metadata_keys: set[str] = set()
    for resource in resources:
        metadata_hash = resource.metadata_hash
        normalized_hash = resource.sha256.casefold()
        normalized_key = resource.metadata_key.casefold()
        if (
            not metadata_hash
            or normalized_hash in seen_hashes
            or normalized_key in seen_metadata_keys
        ):
            if normalized_key in seen_metadata_keys and resource.preserve_hash:
                logger.warning(
                    "[EasyUseAnima] Skipping manual hash %r because that metadata key "
                    "was already emitted; verified local resources and the first "
                    "manual entry take precedence.",
                    resource.metadata_key,
                )
            continue
        seen_hashes.add(normalized_hash)
        seen_metadata_keys.add(normalized_key)
        hashes[resource.metadata_key] = metadata_hash
        weight = (
            f":{resource.weight:g}"
            if resource.weight is not None
            else ""
        )
        final_parts.append(f"{resource.display_name}:{metadata_hash}{weight}")

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
        civitai_resources = _civitai_resource_entries(
            resources,
            budget=civitai_budget,
        )
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
    allow_plain: bool = True,
) -> list[str]:
    def occupied(name: str) -> bool:
        image_path = output_folder / name
        return image_path.exists() or (
            sidecar_required and image_path.with_suffix(".json").exists()
        )

    plain = f"{filename}.{extension}"
    if count == 1 and allow_plain and not occupied(plain):
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
    with _SAVE_LOCK, OutputDirectoryBinding(resolved_folder) as directory:
        pending_names = _allocate_filenames(
            resolved_folder,
            filename,
            safe_extension,
            len(batch),
            sidecar_required=sidecar_required,
        )
        collision_count = 0
        index = 0
        while index < len(batch):
            image_value = batch[index]
            final_name = pending_names[index]
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
            try:
                publish_image_transaction(
                    directory,
                    image,
                    target_name=final_name,
                    image_format=image_format,
                    options=options,
                    sidecar_text=(
                        serialized.workflow_json
                        if sidecar_required
                        else None
                    ),
                )
            except PublicationCollision:
                collision_count += 1
                if collision_count > 64:
                    raise RuntimeError(
                        "[EasyUseAnima] AiO output names kept changing during save."
                    ) from None
                directory.assert_current()
                pending_names[index:] = _allocate_filenames(
                    resolved_folder,
                    filename,
                    safe_extension,
                    len(batch) - index,
                    sidecar_required=sidecar_required,
                    allow_plain=len(batch) == 1,
                )
                continue
            results.append(
                {
                    "filename": final_name,
                    "subfolder": "" if str(relative_folder) == "." else relative_folder.as_posix(),
                    "type": "output",
                }
            )
            index += 1

    return {
        "ui": {"images": results},
        "result": (metadata.final_hashes, metadata.parameters),
    }


__all__ = ()
