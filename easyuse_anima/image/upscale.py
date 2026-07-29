"""Private image upscale operations shared by feature and node adapters."""

from __future__ import annotations

from ..infrastructure.comfy.invocation import _common_upscale_image
from .scaling import _image_scale_by_multiple_size, _normalize_image_scale_options


def _upscale_image_by_multiple(
    image,
    scale_by=1.5,
    upscale_method="bicubic",
    multiple="32",
    max_long_edge=0,
):
    upscale_method, multiple, max_long_edge = _normalize_image_scale_options(
        upscale_method,
        multiple,
        max_long_edge,
    )
    samples = image.movedim(-1, 1)
    width, height, applied_scale = _image_scale_by_multiple_size(
        int(samples.shape[3]),
        int(samples.shape[2]),
        scale_by,
        multiple,
        max_long_edge,
    )
    scaled = _common_upscale_image(samples, width, height, str(upscale_method))
    return (scaled.movedim(1, -1), width, height, applied_scale)


__all__ = ()
