from __future__ import annotations

from collections.abc import Callable
from typing import Any


def run_aio_usdu_upscale_stage(
    model,
    clip,
    vae,
    positive,
    negative,
    image,
    sampler_settings: dict[str, Any],
    upscale_settings: dict[str, Any],
    quality_tags: str = "",
    quality_neg: str = "",
    prompt_data: str | dict | None = None,
    exclude_positive_quality: bool = False,
    exclude_negative_quality: bool = False,
    negpip_mode: str = "off",
    *,
    logger: Any,
    usdu_prompt_full: str,
    require_custom_node_class: Callable[..., Any],
    load_upscale_model: Callable[..., Any],
    stage_sampler_settings: Callable[..., dict[str, Any]],
    as_bool: Callable[..., bool],
    as_float: Callable[..., float],
    as_int: Callable[..., int],
    usdu_tile_plan: Callable[..., dict[str, Any]],
    usdu_conditioning: Callable[..., tuple[Any, Any]],
    apply_model_patches: Callable[..., Any],
    resolve_runtime_seed: Callable[..., int],
    cleanup_model: Callable[..., None],
    node_output_tuple: Callable[..., tuple[Any, ...]],
    image_tensor_size: Callable[..., tuple[int, int]],
    prompt_data_json_safe: Callable[..., Any],
) -> tuple[Any, dict[str, Any]]:
    usdu_settings = upscale_settings.get("usdu", {})
    if not isinstance(usdu_settings, dict):
        usdu_settings = {}
    usdu_cls = require_custom_node_class(
        "UltimateSDUpscale",
        "ComfyUI_UltimateSDUpscale",
        "Required for AiO Generator final Upscale > USDU.",
    )
    upscale_model = load_upscale_model(
        str(usdu_settings.get("upscale_model_name") or "")
    )
    stage_sampler = stage_sampler_settings(
        sampler_settings,
        upscale_settings,
        scheduler_default="simple",
    )
    scale_by = as_float(upscale_settings.get("scale_by"), 2.0)
    tile_plan = usdu_tile_plan(image, scale_by, usdu_settings)
    tile_width = int(tile_plan["tile_width"])
    tile_height = int(tile_plan["tile_height"])
    if tile_plan.get("auto"):
        logger.info(
            "[EasyUseAnima][AiO] USDU auto tile: input=%sx%s scale_by=%.3g expected=%sx%s target/min/max=%s/%s/%s resolved_tile=%sx%s",
            tile_plan.get("input_width"),
            tile_plan.get("input_height"),
            scale_by,
            tile_plan.get("target_width"),
            tile_plan.get("target_height"),
            tile_plan.get("preferred"),
            tile_plan.get("min"),
            tile_plan.get("max"),
            tile_width,
            tile_height,
        )
    else:
        logger.info(
            "[EasyUseAnima][AiO] USDU manual tile: input=%sx%s scale_by=%.3g expected=%sx%s tile=%sx%s",
            tile_plan.get("input_width"),
            tile_plan.get("input_height"),
            scale_by,
            tile_plan.get("target_width"),
            tile_plan.get("target_height"),
            tile_width,
            tile_height,
        )
    logger.info(
        "[EasyUseAnima][AiO] USDU sampler: steps=%s denoise=%.3f cfg=%.3g sampler=%s scheduler=%s",
        as_int(stage_sampler.get("steps"), 20),
        as_float(stage_sampler.get("denoise"), 0.2),
        as_float(stage_sampler.get("cfg"), 8.0),
        str(stage_sampler.get("sampler_name") or "euler"),
        str(stage_sampler.get("scheduler") or "simple"),
    )
    usdu_positive, usdu_negative = usdu_conditioning(
        clip,
        positive,
        negative,
        usdu_settings,
        quality_tags,
        quality_neg,
        prompt_data,
        exclude_positive_quality,
        exclude_negative_quality,
        negpip_mode,
    )
    stage_model = apply_model_patches(
        model,
        clip,
        usdu_positive,
        stage_sampler,
    )
    try:
        result = usdu_cls().upscale(
            image=image,
            model=stage_model,
            positive=usdu_positive,
            negative=usdu_negative,
            vae=vae,
            upscale_by=scale_by,
            seed=resolve_runtime_seed(stage_sampler.get("seed")),
            steps=as_int(stage_sampler.get("steps"), 20),
            cfg=as_float(stage_sampler.get("cfg"), 8.0),
            sampler_name=str(stage_sampler.get("sampler_name") or "euler"),
            scheduler=str(stage_sampler.get("scheduler") or "simple"),
            denoise=as_float(stage_sampler.get("denoise"), 0.2),
            upscale_model=upscale_model,
            mode_type=str(usdu_settings.get("mode_type") or "Linear"),
            tile_width=tile_width,
            tile_height=tile_height,
            mask_blur=as_int(usdu_settings.get("mask_blur"), 8),
            tile_padding=as_int(usdu_settings.get("tile_padding"), 32),
            seam_fix_mode=str(usdu_settings.get("seam_fix_mode") or "None"),
            seam_fix_denoise=as_float(
                usdu_settings.get("seam_fix_denoise"), 1.0
            ),
            seam_fix_mask_blur=as_int(
                usdu_settings.get("seam_fix_mask_blur"), 8
            ),
            seam_fix_width=as_int(usdu_settings.get("seam_fix_width"), 64),
            seam_fix_padding=as_int(usdu_settings.get("seam_fix_padding"), 16),
            force_uniform_tiles=as_bool(
                usdu_settings.get("force_uniform_tiles"), True
            ),
            tiled_decode=as_bool(usdu_settings.get("tiled_decode"), False),
            batch_size=as_int(usdu_settings.get("batch_size"), 1),
        )
    finally:
        cleanup_model(stage_model, model)
    values = node_output_tuple(result)
    if not values:
        raise RuntimeError("[EasyUseAnima] UltimateSDUpscale returned no IMAGE.")
    output = values[0]
    width, height = image_tensor_size(output, 0, 0)
    return output, {
        "enabled": True,
        "backend": "usdu",
        "width": int(width),
        "height": int(height),
        "scale_by": scale_by,
        "tile_width": int(tile_width),
        "tile_height": int(tile_height),
        "tile_auto": bool(tile_plan.get("auto")),
        "tile_target_width": int(tile_plan.get("target_width") or 0),
        "tile_target_height": int(tile_plan.get("target_height") or 0),
        "prompt_mode": str(usdu_settings.get("prompt_mode") or usdu_prompt_full),
        "sampler": prompt_data_json_safe(stage_sampler),
    }


def run_aio_resshift_upscale_stage(
    image,
    sampler_settings: dict[str, Any],
    upscale_settings: dict[str, Any],
    quality_tags: str = "",
    quality_neg: str = "",
    prompt_data: str | dict | None = None,
    exclude_positive_quality: bool = False,
    exclude_negative_quality: bool = False,
    *,
    require_custom_node_class: Callable[..., Any],
    node_output_tuple: Callable[..., tuple[Any, ...]],
    resolve_runtime_seed: Callable[..., int],
    as_int: Callable[..., int],
    image_tensor_size: Callable[..., tuple[int, int]],
) -> tuple[Any, dict[str, Any]]:
    resshift_settings = upscale_settings.get("resshift", {})
    if not isinstance(resshift_settings, dict):
        resshift_settings = {}
    loader_cls = require_custom_node_class(
        "ResShiftLoader",
        "ComfyUI-Distilled-ResShift",
        "Required for AiO Generator final Upscale > ResShift.",
    )
    upscale_cls = require_custom_node_class(
        "ResShiftUpscale",
        "ComfyUI-Distilled-ResShift",
        "Required for AiO Generator final Upscale > ResShift.",
    )
    loader = loader_cls()
    load = getattr(loader, "load", None)
    if load is None:
        raise RuntimeError("[EasyUseAnima] ResShiftLoader does not expose load().")
    model_values = node_output_tuple(
        load(
            str(resshift_settings.get("scale") or "x2"),
            str(resshift_settings.get("student_name") or "(auto-download)"),
            str(resshift_settings.get("dtype") or "bf16"),
        )
    )
    if not model_values:
        raise RuntimeError("[EasyUseAnima] ResShiftLoader returned no RESSHIFT_MODEL.")
    upscaler = upscale_cls()
    upscale = getattr(upscaler, "upscale", None)
    if upscale is None:
        raise RuntimeError("[EasyUseAnima] ResShiftUpscale does not expose upscale().")
    values = node_output_tuple(
        upscale(
            model_values[0],
            image,
            resolve_runtime_seed(sampler_settings.get("seed")),
            as_int(resshift_settings.get("chop"), 512),
            as_int(resshift_settings.get("overlap"), 64),
            as_int(resshift_settings.get("tile_batch"), 4),
        )
    )
    if not values:
        raise RuntimeError("[EasyUseAnima] ResShiftUpscale returned no IMAGE.")
    output = values[0]
    width, height = image_tensor_size(output, 0, 0)
    return output, {
        "enabled": True,
        "backend": "resshift",
        "width": int(width),
        "height": int(height),
        "scale": str(resshift_settings.get("scale") or "x2"),
    }


def run_aio_upscale_stage(
    model,
    clip,
    vae,
    positive,
    negative,
    image,
    sampler_settings: dict[str, Any],
    upscale_settings: dict[str, Any],
    quality_tags: str = "",
    quality_neg: str = "",
    prompt_data: str | dict | None = None,
    exclude_positive_quality: bool = False,
    exclude_negative_quality: bool = False,
    negpip_mode: str = "off",
    *,
    as_bool: Callable[..., bool],
    run_usdu_upscale_stage: Callable[..., tuple[Any, dict[str, Any]]],
    run_resshift_upscale_stage: Callable[..., tuple[Any, dict[str, Any]]],
) -> tuple[Any, dict[str, Any]]:
    if not as_bool(upscale_settings.get("enabled"), False):
        return image, {"enabled": False}
    backend = str(upscale_settings.get("backend") or "usdu")
    if backend == "usdu":
        output, metadata = run_usdu_upscale_stage(
            model,
            clip,
            vae,
            positive,
            negative,
            image,
            sampler_settings,
            upscale_settings,
            quality_tags,
            quality_neg,
            prompt_data,
            exclude_positive_quality,
            exclude_negative_quality,
            negpip_mode,
        )
    elif backend == "resshift":
        output, metadata = run_resshift_upscale_stage(
            image,
            sampler_settings,
            upscale_settings,
            quality_tags,
            quality_neg,
            prompt_data,
            exclude_positive_quality,
            exclude_negative_quality,
        )
    else:
        raise RuntimeError(
            f"[EasyUseAnima] Unsupported final upscale backend: {backend}"
        )
    return output, metadata


__all__ = ()
