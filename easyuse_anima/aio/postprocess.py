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


def _apply_aio_final_fit(
    image,
    postprocess_settings: dict[str, Any],
) -> tuple[Any, dict[str, Any]]:
    fit_settings = postprocess_settings.get("fit", {})
    if not isinstance(fit_settings, dict):
        fit_settings = {}
    fit_settings = dict(fit_settings)
    fit_settings["enabled"] = _runtime_helper("_as_bool")(
        postprocess_settings.get("enabled"),
        False,
    )
    width, height = _runtime_helper("_image_tensor_size")(image, 0, 0)
    target_width, target_height, scale = _runtime_helper("_aio_final_fit_size")(
        width,
        height,
        fit_settings,
    )
    metadata = {
        "enabled": _runtime_helper("_as_bool")(
            postprocess_settings.get("enabled"),
            False,
        ),
        "mode": str(fit_settings.get("mode") or "max_long_edge"),
        "max_long_edge": _runtime_helper("_as_int")(
            fit_settings.get("max_long_edge"),
            2048,
        ),
        "max_megapixels": _runtime_helper("_as_float")(
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
    output, resized = _runtime_helper("_resize_image_to_size_if_needed")(
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
    if not _runtime_helper("_as_bool")(
        postprocess_settings.get("enabled"),
        False,
    ):
        width, height = _runtime_helper("_image_tensor_size")(image, 0, 0)
        return image, {
            "enabled": False,
            "width": int(width),
            "height": int(height),
        }
    output, fit_metadata = _runtime_helper("_apply_aio_final_fit")(
        image,
        postprocess_settings,
    )
    width, height = _runtime_helper("_image_tensor_size")(
        output,
        fit_metadata.get("target_width", 0),
        fit_metadata.get("target_height", 0),
    )
    limit = (
        f"{fit_metadata.get('max_megapixels')}MP"
        if fit_metadata.get("mode") == "megapixels"
        else f"{fit_metadata.get('max_long_edge')}px"
    )
    _runtime_helper("logger").info(
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
