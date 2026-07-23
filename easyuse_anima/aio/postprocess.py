"""AiO postprocess size-planning policy."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, TypeAlias

_RuntimeResolver: TypeAlias = Callable[[str], Any]
_RUNTIME_RESOLVER: _RuntimeResolver | None = None


def _bind_aio_postprocess_runtime(*, resolve_helper: _RuntimeResolver) -> None:
    """Bind root compatibility helpers without importing the root module."""

    global _RUNTIME_RESOLVER
    _RUNTIME_RESOLVER = resolve_helper


def _runtime_helper(name: str) -> Any:
    resolver = _RUNTIME_RESOLVER
    if resolver is None:
        raise RuntimeError(
            f"[EasyUseAnima] AiO postprocess runtime helper is not bound: {name}"
        )
    return resolver(name)


def _aio_final_fit_size(
    width: int,
    height: int,
    fit_settings: dict[str, Any],
) -> tuple[int, int, float]:
    width = max(1, int(width))
    height = max(1, int(height))
    if not _runtime_helper("_as_bool")(fit_settings.get("enabled"), False):
        return width, height, 1.0
    mode = str(fit_settings.get("mode") or "max_long_edge")
    scale = 1.0
    if mode == "megapixels":
        max_pixels = max(
            1.0,
            _runtime_helper("_as_float")(
                fit_settings.get("max_megapixels"),
                4.0,
            )
            * 1_000_000.0,
        )
        pixels = float(width * height)
        if pixels > max_pixels:
            scale = _runtime_helper("sqrt")(max_pixels / pixels)
    else:
        max_long_edge = max(
            1,
            _runtime_helper("_as_int")(
                fit_settings.get("max_long_edge"),
                2048,
            ),
        )
        long_edge = max(width, height)
        if long_edge > max_long_edge:
            scale = max_long_edge / long_edge
    if scale >= 1.0:
        return width, height, 1.0
    target_width = _runtime_helper("_align_down")(
        round(width * scale),
        _runtime_helper("LATENT_ALIGN"),
    )
    target_height = _runtime_helper("_align_down")(
        round(height * scale),
        _runtime_helper("LATENT_ALIGN"),
    )
    return max(1, target_width), max(1, target_height), scale


__all__ = ()
