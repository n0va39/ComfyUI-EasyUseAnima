"""Image scaling policy and legacy option normalization."""

from __future__ import annotations

from math import gcd, isfinite, lcm

from ..common.values import _as_float, _as_int, _single_value
from .geometry import _aligned_size_near_scale, _alignment_value, _align_nearest


IMAGE_UPSCALE_METHODS = ["nearest-exact", "bilinear", "area", "bicubic", "lanczos"]
IMAGE_SCALE_MULTIPLES = ["8", "16", "32", "64"]


def _scale_by_value(value, default: float = 1.0) -> float:
    scale = _as_float(value, default)
    if not isfinite(scale):
        scale = default
    return max(0.01, min(8.0, scale))


def _max_long_edge_value(value) -> int:
    max_long_edge = _as_int(value, 0)
    if max_long_edge <= 0:
        return 0
    return max(1, min(16384, max_long_edge))


def _image_scale_by_multiple_size(
    width: int,
    height: int,
    scale_by,
    multiple,
    max_long_edge=0,
) -> tuple[int, int, float]:
    source_width = max(1, int(width))
    source_height = max(1, int(height))
    scale = _scale_by_value(scale_by, 1.0)
    max_long_edge = _max_long_edge_value(max_long_edge)
    alignment = _alignment_value(multiple)
    if alignment is None:
        applied_scale = scale
        if max_long_edge > 0:
            applied_scale = min(applied_scale, max_long_edge / max(source_width, source_height))
        target_width = max(1, round(source_width * applied_scale))
        target_height = max(1, round(source_height * applied_scale))
        if max_long_edge > 0 and max(target_width, target_height) > max_long_edge:
            applied_scale = max_long_edge / max(target_width, target_height) * applied_scale
            target_width = max(1, round(source_width * applied_scale))
            target_height = max(1, round(source_height * applied_scale))
        return target_width, target_height, applied_scale

    ratio_gcd = gcd(source_width, source_height)
    base_width = source_width // ratio_gcd
    base_height = source_height // ratio_gcd
    base_long_edge = max(base_width, base_height)
    width_unit = alignment // gcd(base_width, alignment)
    height_unit = alignment // gcd(base_height, alignment)
    valid_unit_step = lcm(width_unit, height_unit)

    max_valid_unit = int((ratio_gcd * 8.0) // valid_unit_step)
    if max_long_edge > 0:
        max_valid_unit = min(max_valid_unit, max_long_edge // (base_long_edge * valid_unit_step))
    if max_valid_unit >= 1:
        desired_unit = (ratio_gcd * scale) / valid_unit_step
        lower_unit = max(1, min(max_valid_unit, int(desired_unit)))
        candidates = {lower_unit}
        if lower_unit < max_valid_unit:
            candidates.add(lower_unit + 1)
        if lower_unit > 1:
            candidates.add(lower_unit - 1)

        valid_unit = min(
            candidates,
            key=lambda unit: (
                abs(((unit * valid_unit_step) / ratio_gcd) - scale),
                -unit,
            ),
        )
        applied_scale = (valid_unit * valid_unit_step) / ratio_gcd
        candidate = (
            base_width * valid_unit * valid_unit_step,
            base_height * valid_unit * valid_unit_step,
            applied_scale,
        )
        if max_long_edge > 0:
            aligned_candidate = _aligned_size_near_scale(
                source_width,
                source_height,
                scale,
                alignment,
                max_long_edge,
            )
            if aligned_candidate is not None:
                source_long_edge = max(source_width, source_height)
                target_long_edge = min(source_long_edge * scale, max_long_edge)
                candidate_long_error = abs(max(candidate[0], candidate[1]) - target_long_edge)
                aligned_long_error = abs(max(aligned_candidate[0], aligned_candidate[1]) - target_long_edge)
                candidate_upscales = candidate[0] > source_width and candidate[1] > source_height
                aligned_upscales = aligned_candidate[0] > source_width and aligned_candidate[1] > source_height
                if scale > 1.0 and aligned_upscales and not candidate_upscales:
                    return aligned_candidate
                if aligned_long_error < candidate_long_error:
                    return aligned_candidate
            if max(source_width, source_height) * scale > max_long_edge and aligned_candidate is not None:
                return aligned_candidate
        return candidate

    aligned_candidate = _aligned_size_near_scale(
        source_width,
        source_height,
        scale,
        alignment,
        max_long_edge,
    )
    if aligned_candidate is not None:
        return aligned_candidate

    target_width = _align_nearest(round(source_width * scale), alignment)
    target_height = _align_nearest(round(source_height * scale), alignment)
    applied_scale = (target_width / source_width + target_height / source_height) / 2.0
    return target_width, target_height, applied_scale


def _normalize_image_scale_options(upscale_method, multiple, max_long_edge):
    method = str(_single_value(upscale_method) or "").strip()
    size_multiple = str(_single_value(multiple) or "").strip()
    max_edge = max_long_edge

    # Compatibility for workflows created before max_long_edge existed, or while it was inserted
    # before upscale_method: widget values can shift into the wrong input names.
    if size_multiple in IMAGE_UPSCALE_METHODS and str(_single_value(max_long_edge) or "").strip() in IMAGE_SCALE_MULTIPLES:
        shifted_max_edge = upscale_method
        method = size_multiple
        size_multiple = str(_single_value(max_long_edge) or "").strip()
        max_edge = shifted_max_edge
    if str(_single_value(max_long_edge) or "").strip() in IMAGE_UPSCALE_METHODS:
        shifted_method = str(_single_value(max_long_edge) or "").strip()
        if method in IMAGE_SCALE_MULTIPLES:
            size_multiple = method
        method = shifted_method
        max_edge = 0

    if method not in IMAGE_UPSCALE_METHODS:
        method = "bicubic"
    if size_multiple not in IMAGE_SCALE_MULTIPLES:
        size_multiple = "32"
    return method, size_multiple, max_edge


__all__ = (
    "IMAGE_SCALE_MULTIPLES",
    "IMAGE_UPSCALE_METHODS",
)
