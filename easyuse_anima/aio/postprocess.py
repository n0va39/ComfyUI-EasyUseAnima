"""AiO postprocess size-planning policy."""

from __future__ import annotations

import logging
from math import sqrt
from typing import Any

from ..common.values import _as_bool, _as_float, _as_int
from ..image.geometry import _align_down, _image_tensor_size
from ..infrastructure.comfy.invocation import _common_upscale_image
from ..naia.client import LATENT_ALIGN

logger = logging.getLogger("ComfyUI-EasyUseAnima")


def _resize_image_to_size_if_needed(
    image,
    target_width: int,
    target_height: int,
    upscale_method: str = "bicubic",
) -> tuple[Any, bool]:
    target_width = max(1, int(target_width))
    target_height = max(1, int(target_height))
    width, height = _image_tensor_size(
        image,
        target_width,
        target_height,
    )
    if width == target_width and height == target_height:
        return image, False
    samples = image.movedim(-1, 1)
    resized = _common_upscale_image(
        samples,
        target_width,
        target_height,
        str(upscale_method or "bicubic"),
    )
    return resized.movedim(1, -1), True


def _aio_final_fit_size(
    width: int,
    height: int,
    fit_settings: dict[str, Any],
) -> tuple[int, int, float]:
    width = max(1, int(width))
    height = max(1, int(height))
    if not _as_bool(fit_settings.get("enabled"), False):
        return width, height, 1.0
    mode = str(fit_settings.get("mode") or "max_long_edge")
    scale = 1.0
    if mode == "megapixels":
        max_pixels = max(
            1.0,
            _as_float(
                fit_settings.get("max_megapixels"),
                4.0,
            )
            * 1_000_000.0,
        )
        pixels = float(width * height)
        if pixels > max_pixels:
            scale = sqrt(max_pixels / pixels)
    else:
        max_long_edge = max(
            1,
            _as_int(
                fit_settings.get("max_long_edge"),
                2048,
            ),
        )
        long_edge = max(width, height)
        if long_edge > max_long_edge:
            scale = max_long_edge / long_edge
    if scale >= 1.0:
        return width, height, 1.0
    target_width = _align_down(
        round(width * scale),
        LATENT_ALIGN,
    )
    target_height = _align_down(
        round(height * scale),
        LATENT_ALIGN,
    )
    return max(1, target_width), max(1, target_height), scale


def _apply_aio_final_fit(
    image,
    postprocess_settings: dict[str, Any],
) -> tuple[Any, dict[str, Any]]:
    fit_settings = postprocess_settings.get("fit", {})
    if not isinstance(fit_settings, dict):
        fit_settings = {}
    fit_settings = dict(fit_settings)
    fit_settings["enabled"] = _as_bool(
        postprocess_settings.get("enabled"),
        False,
    )
    width, height = _image_tensor_size(image, 0, 0)
    target_width, target_height, scale = _aio_final_fit_size(
        width,
        height,
        fit_settings,
    )
    metadata = {
        "enabled": _as_bool(
            postprocess_settings.get("enabled"),
            False,
        ),
        "mode": str(fit_settings.get("mode") or "max_long_edge"),
        "max_long_edge": _as_int(
            fit_settings.get("max_long_edge"),
            2048,
        ),
        "max_megapixels": _as_float(
            fit_settings.get("max_megapixels"),
            4.0,
        ),
        "method": str(fit_settings.get("method") or "bicubic"),
        "applied": scale < 1.0,
        "scale": float(scale),
        "width": int(width),
        "height": int(height),
        "target_width": int(target_width),
        "target_height": int(target_height),
    }
    if scale >= 1.0:
        return image, metadata
    output, resized = _resize_image_to_size_if_needed(
        image,
        target_width,
        target_height,
        str(fit_settings.get("method") or "bicubic"),
    )
    metadata["applied"] = bool(resized)
    return output, metadata


def _run_aio_postprocess_stage(
    image,
    postprocess_settings: dict[str, Any],
) -> tuple[Any, dict[str, Any]]:
    if not _as_bool(
        postprocess_settings.get("enabled"),
        False,
    ):
        width, height = _image_tensor_size(image, 0, 0)
        return image, {
            "enabled": False,
            "width": int(width),
            "height": int(height),
        }
    output, fit_metadata = _apply_aio_final_fit(
        image,
        postprocess_settings,
    )
    width, height = _image_tensor_size(
        output,
        fit_metadata.get("target_width", 0),
        fit_metadata.get("target_height", 0),
    )
    limit = (
        f"{fit_metadata.get('max_megapixels')}MP"
        if fit_metadata.get("mode") == "megapixels"
        else f"{fit_metadata.get('max_long_edge')}px"
    )
    logger.info(
        "[EasyUseAnima][AiO] Postprocess final fit: input=%sx%s mode=%s limit=%s method=%s applied=%s output=%sx%s",
        fit_metadata.get("width"),
        fit_metadata.get("height"),
        fit_metadata.get("mode"),
        limit,
        fit_metadata.get("method"),
        bool(fit_metadata.get("applied")),
        width,
        height,
    )
    return output, {
        "enabled": True,
        "width": int(width),
        "height": int(height),
        "fit": fit_metadata,
    }


__all__ = ()
