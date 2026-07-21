"""Prompt Studio and NAIA resolution selection policy."""

from __future__ import annotations

import re
from math import gcd, log

from ..common.values import _as_float, _as_int, _single_value


ADVANCED_RESOLUTION_BUCKETS = {
    "512": (
        (256, 1024), (1024, 256),
        (288, 896), (896, 288),
        (384, 672), (672, 384),
        (448, 672), (672, 448),
        (512, 512),
        (448, 576), (576, 448),
    ),
    "768": (
        (384, 1440), (1440, 384),
        (480, 1152), (1152, 480),
        (576, 960), (960, 576),
        (640, 960), (960, 640),
        (640, 864), (864, 640),
        (768, 768),
    ),
    "896": (
        (448, 1728), (1728, 448),
        (480, 1600), (1600, 480),
        (576, 1344), (1344, 576),
        (672, 1152), (1152, 672),
        (704, 1056), (1056, 704),
        (800, 960), (960, 800),
        (896, 896),
    ),
    "1024": (
        (512, 2016), (2016, 512),
        (576, 1792), (1792, 576),
        (672, 1536), (1536, 672),
        (672, 1600), (1600, 672),
        (768, 1344), (1344, 768),
        (800, 1344), (1344, 800),
        (832, 1248), (1248, 832),
        (896, 1152), (1152, 896),
        (960, 1120), (1120, 960),
        (1024, 1024),
    ),
    "1280": (
        (672, 2400), (2400, 672),
        (800, 2016), (2016, 800),
        (1024, 1536), (1536, 1024),
        (1024, 1600), (1600, 1024),
        (1120, 1440), (1440, 1120),
        (1280, 1280),
    ),
    "1536": (
        (1440, 1536), (1536, 1440),
        (1280, 1728), (1728, 1280),
        (1152, 1920), (1920, 1152),
        (1280, 1920), (1920, 1280),
        (1024, 2176), (2176, 1024),
        (960, 2304), (2304, 960),
        (864, 2560), (2560, 864),
        (768, 2880), (2880, 768),
        (1536, 1536),
    ),
}
CUSTOM_ADVANCED_RESOLUTION_BUCKET = "Custom"
NAIA_ADVANCED_RESOLUTION_BUCKET = "NAIA"
DEFAULT_ADVANCED_RESOLUTION_BUCKET = "1024"
DEFAULT_ADVANCED_RESOLUTION_SIZE = "1024 * 1024 (1:1)"
NAIA_RESOLUTION_MODE_SCALE = "scale"
NAIA_RESOLUTION_MODE_BUCKET = "bucket"

_RESOLUTION_LABEL_RE = re.compile(r"(\d+)\s*(?:\*|x|×)\s*(\d+)")


def _ratio_label(width: int, height: int) -> str:
    divisor = gcd(max(1, int(width)), max(1, int(height)))
    return f"{int(width) // divisor}:{int(height) // divisor}"


def _resolution_label(width: int, height: int) -> str:
    return f"{int(width)} * {int(height)} ({_ratio_label(width, height)})"


def _sorted_resolution_options(bucket: str) -> list[tuple[int, int]]:
    values = ADVANCED_RESOLUTION_BUCKETS.get(bucket) or ADVANCED_RESOLUTION_BUCKETS[DEFAULT_ADVANCED_RESOLUTION_BUCKET]
    return sorted(values, key=lambda item: (item[0] / item[1], item[0], item[1]))


def _normalize_resolution_bucket(value) -> str:
    value = str(_single_value(value) or "").strip()
    if value in {CUSTOM_ADVANCED_RESOLUTION_BUCKET, NAIA_ADVANCED_RESOLUTION_BUCKET}:
        return value
    return value if value in ADVANCED_RESOLUTION_BUCKETS else DEFAULT_ADVANCED_RESOLUTION_BUCKET


def _snap_resolution_32(value, default: int = 1024) -> int:
    raw = _as_int(value, default)
    if raw <= 0:
        raw = default
    return max(32, int(round(raw / 32)) * 32)


def _resolve_naia_resolution_scale(naia_settings: dict | None) -> float:
    value = _as_float((naia_settings or {}).get("resolution_scale", 1.0), 1.0)
    return max(0.25, min(4.0, value))


def _resolve_naia_resolution_max_long_edge(naia_settings: dict | None) -> int:
    value = _as_int((naia_settings or {}).get("resolution_max_long_edge", 0), 0)
    if value <= 0:
        return 0
    return max(32, min(16384, value))


def _resolve_naia_resolution_mode(naia_settings: dict | None) -> str:
    value = str(
        _single_value((naia_settings or {}).get("resolution_mode", NAIA_RESOLUTION_MODE_SCALE)) or ""
    ).strip().lower()
    if value == "bucket_fit":
        return NAIA_RESOLUTION_MODE_BUCKET
    return value if value in {NAIA_RESOLUTION_MODE_SCALE, NAIA_RESOLUTION_MODE_BUCKET} else NAIA_RESOLUTION_MODE_SCALE


def _resolve_naia_resolution_bucket(naia_settings: dict | None) -> str:
    bucket = _normalize_resolution_bucket((naia_settings or {}).get("resolution_bucket", DEFAULT_ADVANCED_RESOLUTION_BUCKET))
    return bucket if bucket in ADVANCED_RESOLUTION_BUCKETS else DEFAULT_ADVANCED_RESOLUTION_BUCKET


def _snap_scaled_resolution_32(value: float, max_value: int = 0, default: int = 1024) -> int:
    raw = _as_float(value, float(default))
    if raw <= 0:
        raw = float(default)
    snapped = max(32, int(round(raw / 32)) * 32)
    if max_value > 0 and snapped > max_value:
        snapped = max(32, int(max_value // 32) * 32)
    return snapped


def _scale_naia_resolution(
    width: int,
    height: int,
    naia_settings: dict | None,
) -> tuple[int, int]:
    scale = _resolve_naia_resolution_scale(naia_settings)
    max_long_edge = _resolve_naia_resolution_max_long_edge(naia_settings)
    scaled_width = max(1.0, _as_float(width, 1024.0) * scale)
    scaled_height = max(1.0, _as_float(height, 1024.0) * scale)

    if max_long_edge > 0:
        long_edge = max(scaled_width, scaled_height)
        if long_edge > max_long_edge:
            ratio = max_long_edge / long_edge
            scaled_width *= ratio
            scaled_height *= ratio

    return (
        _snap_scaled_resolution_32(scaled_width, max_long_edge, 1024),
        _snap_scaled_resolution_32(scaled_height, max_long_edge, 1024),
    )


def _fit_naia_resolution_to_bucket(
    width: int,
    height: int,
    naia_settings: dict | None,
) -> tuple[int, int]:
    bucket = _resolve_naia_resolution_bucket(naia_settings)
    source_width = max(1.0, _as_float(width, 1024.0))
    source_height = max(1.0, _as_float(height, 1024.0))
    source_ratio = source_width / source_height
    options = ADVANCED_RESOLUTION_BUCKETS.get(bucket) or ADVANCED_RESOLUTION_BUCKETS[DEFAULT_ADVANCED_RESOLUTION_BUCKET]

    return min(
        options,
        key=lambda item: abs(log((item[0] / item[1]) / source_ratio)),
    )


def _resolve_naia_resolution(
    width: int,
    height: int,
    naia_settings: dict | None,
) -> tuple[int, int]:
    if _resolve_naia_resolution_mode(naia_settings) == NAIA_RESOLUTION_MODE_BUCKET:
        return _fit_naia_resolution_to_bucket(width, height, naia_settings)
    return _scale_naia_resolution(width, height, naia_settings)


def _advanced_resolution_from_selection(
    bucket,
    size,
    custom_width: int | str = 1024,
    custom_height: int | str = 1024,
) -> tuple[int, int]:
    bucket_name = _normalize_resolution_bucket(bucket)
    if bucket_name in {CUSTOM_ADVANCED_RESOLUTION_BUCKET, NAIA_ADVANCED_RESOLUTION_BUCKET}:
        return (
            _snap_resolution_32(custom_width, 1024),
            _snap_resolution_32(custom_height, 1024),
        )
    raw_size = str(_single_value(size) or "").strip()
    match = _RESOLUTION_LABEL_RE.search(raw_size)
    if match:
        width, height = int(match.group(1)), int(match.group(2))
        if (width, height) in ADVANCED_RESOLUTION_BUCKETS.get(bucket_name, ()):
            return width, height
    default_width, default_height = 1024, 1024
    if (default_width, default_height) in ADVANCED_RESOLUTION_BUCKETS.get(bucket_name, ()):
        return default_width, default_height
    return _sorted_resolution_options(bucket_name)[0]

__all__ = ()
