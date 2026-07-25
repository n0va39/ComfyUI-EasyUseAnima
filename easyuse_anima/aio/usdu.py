"""Ultimate SD Upscale tile-planning policy."""

from __future__ import annotations

from math import ceil
from typing import Any

from ..common.values import _as_bool, _as_int
from ..image.geometry import _align_nearest, _image_tensor_size


def _aio_usdu_auto_tile_dimension(
    target_size: int,
    preferred_size: int = 1024,
    min_size: int = 512,
    max_size: int = 2048,
) -> int:
    target_size = max(1, int(target_size))
    min_size = max(64, int(min_size))
    max_size = max(min_size, int(max_size))
    preferred = max(min_size, min(max_size, int(preferred_size)))
    tile_count = max(1, ceil(target_size / preferred))
    tile_size = ceil(target_size / tile_count)
    tile_size = _align_nearest(tile_size, 64)
    return max(min_size, min(max_size, tile_size))


def _aio_usdu_tile_plan(
    image,
    scale_by: float,
    usdu_settings: dict[str, Any],
) -> dict[str, Any]:
    width, height = _image_tensor_size(image, 512, 512)
    target_width = max(1, int(round(width * max(0.05, float(scale_by)))))
    target_height = max(1, int(round(height * max(0.05, float(scale_by)))))
    auto_tile = _as_bool(
        usdu_settings.get("auto_tile_size"),
        True,
    )
    if not auto_tile:
        return {
            "auto": False,
            "input_width": int(width),
            "input_height": int(height),
            "target_width": int(target_width),
            "target_height": int(target_height),
            "tile_width": _as_int(
                usdu_settings.get("tile_width"),
                512,
            ),
            "tile_height": _as_int(
                usdu_settings.get("tile_height"),
                512,
            ),
        }
    preferred = _as_int(
        usdu_settings.get("auto_tile_target"),
        1024,
    )
    min_size = _as_int(
        usdu_settings.get("auto_tile_min"),
        512,
    )
    max_size = _as_int(
        usdu_settings.get("auto_tile_max"),
        2048,
    )
    return {
        "auto": True,
        "input_width": int(width),
        "input_height": int(height),
        "target_width": int(target_width),
        "target_height": int(target_height),
        "preferred": int(preferred),
        "min": int(min_size),
        "max": int(max_size),
        "tile_width": _aio_usdu_auto_tile_dimension(
            target_width,
            preferred,
            min_size,
            max_size,
        ),
        "tile_height": _aio_usdu_auto_tile_dimension(
            target_height,
            preferred,
            min_size,
            max_size,
        ),
    }


__all__ = ()
