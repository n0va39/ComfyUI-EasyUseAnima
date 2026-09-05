"""Domain-independent image geometry helpers."""

from typing import Optional

from ..common.values import _single_value


def _alignment_value(value) -> Optional[int]:
    text = str(_single_value(value) or "").strip().lower()
    if text in ("", "impact", "none", "0"):
        return None
    try:
        alignment = int(text)
    except ValueError:
        return None
    return alignment if alignment > 1 else None


def _align_up(value: int, alignment: int) -> int:
    value = int(value)
    alignment = int(alignment)
    return max(alignment, ((value + alignment - 1) // alignment) * alignment)


def _align_nearest(value: int, alignment: int) -> int:
    value = max(1, int(value))
    alignment = max(1, int(alignment))
    lower = max(alignment, (value // alignment) * alignment)
    upper = _align_up(value, alignment)
    if (value - lower) < (upper - value):
        return lower
    return upper


def _align_down(value: int, alignment: int) -> int:
    value = max(1, int(value))
    alignment = max(1, int(alignment))
    return max(1, (value // alignment) * alignment)


def _image_tensor_size(image, fallback_width: int, fallback_height: int) -> tuple[int, int]:
    try:
        return int(image.shape[2]), int(image.shape[1])
    except Exception:
        return int(fallback_width), int(fallback_height)


def _aligned_size_near_scale(
    source_width: int,
    source_height: int,
    scale: float,
    alignment: int,
    max_long_edge: int,
) -> Optional[tuple[int, int, float]]:
    source_long_edge = max(source_width, source_height)
    target_scale = scale
    if max_long_edge > 0 and source_long_edge * target_scale > max_long_edge:
        target_scale = max_long_edge / source_long_edge
    if target_scale <= 0:
        return None

    target_width = max(1, round(source_width * target_scale))
    target_height = max(1, round(source_height * target_scale))
    width_candidates = {
        max(alignment, (target_width // alignment) * alignment),
        _align_up(target_width, alignment),
    }
    height_candidates = {
        max(alignment, (target_height // alignment) * alignment),
        _align_up(target_height, alignment),
    }

    candidates: list[tuple[int, int, float]] = []
    for candidate_width in width_candidates:
        for candidate_height in height_candidates:
            if max_long_edge > 0 and max(candidate_width, candidate_height) > max_long_edge:
                continue
            applied_scale = (candidate_width / source_width + candidate_height / source_height) / 2.0
            candidates.append((candidate_width, candidate_height, applied_scale))
    if not candidates:
        return None

    if scale > 1.0 and max_long_edge > source_long_edge:
        upscaled_candidates = [
            item for item in candidates
            if item[0] > source_width and item[1] > source_height
        ]
        if upscaled_candidates:
            candidates = upscaled_candidates

    source_ratio = source_width / source_height
    return min(
        candidates,
        key=lambda item: (
            abs((item[0] / source_width) - target_scale) + abs((item[1] / source_height) - target_scale),
            abs((item[0] / item[1]) - source_ratio),
            -item[0] * item[1],
        ),
    )


__all__ = ()
