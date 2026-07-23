"""AiO preview path, tagging, event, and temporary-image helpers."""

from __future__ import annotations

import logging
import os
import random
from typing import Any

from ..common.values import _single_value
from ..image.geometry import _image_tensor_size
from ..infrastructure.comfy.wiring import resolve_comfy_host_helper
from ..prompt.data import _prompt_data_json_safe

AIO_PREVIEW_STAGE_LABELS = {
    "first_pass": "First pass",
    "highres": "Highres",
    "detailer_face": "Detailer: face",
    "detailer_eye": "Detailer: eye",
    "upscale": "Upscale",
    "postprocess": "Postprocess",
    "final": "Final",
}
AIO_PREVIEW_EVENT = "easyuse-anima-aio-preview"
AIO_PREVIEW_CACHE_FORMAT = "webp"
AIO_PREVIEW_CACHE_QUALITY = 90

logger = logging.getLogger("ComfyUI-EasyUseAnima")


def _missing_host_helper(name: str):
    raise RuntimeError(
        f"[EasyUseAnima] AiO preview Comfy host helper is unavailable: {name}"
    )


def _find_comfy_node_class(node_id: str):
    helper = resolve_comfy_host_helper(
        "_find_comfy_node_class",
        _missing_host_helper,
    )
    return helper(node_id)


def _aio_preview_base_directory(image_type: str) -> str:
    try:
        import folder_paths  # type: ignore

        if image_type == "temp":
            return folder_paths.get_temp_directory()
        if image_type == "input":
            return folder_paths.get_input_directory()
        return folder_paths.get_output_directory()
    except Exception:
        return ""


def _aio_preview_file_size_bytes(image_info: dict[str, Any]) -> int:
    filename = str(image_info.get("filename") or "")
    if not filename:
        return 0
    base_dir = _aio_preview_base_directory(str(image_info.get("type") or "output"))
    if not base_dir:
        return 0
    subfolder = str(image_info.get("subfolder") or "")
    path = os.path.join(base_dir, subfolder, filename)
    try:
        return os.path.getsize(path) if os.path.isfile(path) else 0
    except OSError:
        return 0


def _tag_aio_preview_images(
    images,
    stage: str,
    *,
    width: int = 0,
    height: int = 0,
) -> list[dict[str, Any]]:
    label = AIO_PREVIEW_STAGE_LABELS.get(stage, stage)
    tagged: list[dict[str, Any]] = []
    for image in images or ():
        if not isinstance(image, dict):
            continue
        item = dict(image)
        item["stage"] = stage
        item["label"] = label
        if width > 0:
            item["width"] = int(width)
        if height > 0:
            item["height"] = int(height)
        file_size = _aio_preview_file_size_bytes(item)
        if file_size > 0:
            item["bytes"] = int(file_size)
        tagged.append(item)
    return tagged


def _send_aio_preview_event(
    node_id,
    run_id: str,
    stage: str,
    images: list[dict[str, Any]],
) -> None:
    node_id = _single_value(node_id)
    if node_id is None or not images:
        return
    try:
        from server import PromptServer  # type: ignore

        prompt_server = getattr(PromptServer, "instance", None)
        send_sync = getattr(prompt_server, "send_sync", None)
        if prompt_server is None or send_sync is None:
            return
        payload = {
            "node": str(node_id),
            "run_id": str(run_id),
            "stage": str(stage),
            "images": _prompt_data_json_safe(images),
        }
        client_id = getattr(prompt_server, "client_id", None)
        send_sync(AIO_PREVIEW_EVENT, payload, client_id)
    except Exception as exc:
        logger.debug(
            "[EasyUseAnima] failed to send AiO preview event: %s", exc
        )


def _save_aio_temp_preview_image(
    image,
    stage: str,
    *,
    workflow_prompt=None,
    extra_pnginfo=None,
) -> list[dict[str, Any]]:
    width, height = _image_tensor_size(image, 0, 0)
    try:
        import folder_paths  # type: ignore
        import numpy as np  # type: ignore
        from PIL import Image  # type: ignore

        temp_dir = folder_paths.get_temp_directory()
        prefix = f"EasyUseAnima_AiO_{stage}_temp_{''.join(random.choice('abcdefghijklmnopqrstupvxyz') for _ in range(5))}"
        full_output_folder, filename, counter, subfolder, _ = (
            folder_paths.get_save_image_path(
                prefix,
                temp_dir,
                width,
                height,
            )
        )
        results: list[dict[str, Any]] = []
        for batch_number, batch_image in enumerate(image):
            pixels = 255.0 * batch_image.detach().cpu().numpy()
            img = Image.fromarray(np.clip(pixels, 0, 255).astype(np.uint8))
            filename_with_batch_num = filename.replace(
                "%batch_num%", str(batch_number)
            )
            file = (
                f"{filename_with_batch_num}_{counter:05}_."
                f"{AIO_PREVIEW_CACHE_FORMAT}"
            )
            path = os.path.join(full_output_folder, file)
            img.save(
                path,
                format="WEBP",
                quality=AIO_PREVIEW_CACHE_QUALITY,
                method=4,
            )
            results.append(
                {
                    "filename": file,
                    "subfolder": subfolder,
                    "type": "temp",
                }
            )
            counter += 1
        if results:
            return _tag_aio_preview_images(
                results, stage, width=width, height=height
            )
    except Exception as exc:
        logger.warning(
            "[EasyUseAnima] Failed to save AiO WebP preview stage %s; falling back to ComfyUI PreviewImage PNG: %s",
            stage,
            exc,
        )

    preview_cls = _find_comfy_node_class("PreviewImage")
    if preview_cls is None:
        logger.warning(
            "[EasyUseAnima] Could not find ComfyUI PreviewImage for AiO preview stage %s.",
            stage,
        )
        return []
    saver = preview_cls()
    save_images = getattr(saver, "save_images", None)
    if save_images is None:
        logger.warning(
            "[EasyUseAnima] PreviewImage does not expose save_images() for AiO preview stage %s.",
            stage,
        )
        return []
    try:
        result = save_images(
            image,
            filename_prefix=f"EasyUseAnima_AiO_{stage}",
            prompt=workflow_prompt,
            extra_pnginfo=extra_pnginfo,
        )
    except TypeError:
        try:
            result = save_images(image)
        except Exception as exc:
            logger.warning(
                "[EasyUseAnima] Failed to save AiO preview stage %s: %s",
                stage,
                exc,
            )
            return []
    except Exception as exc:
        logger.warning(
            "[EasyUseAnima] Failed to save AiO preview stage %s: %s", stage, exc
        )
        return []
    if not isinstance(result, dict):
        return []
    ui = result.get("ui", {})
    if not isinstance(ui, dict):
        return []
    return _tag_aio_preview_images(
        ui.get("images", []), stage, width=width, height=height
    )


__all__ = ()
