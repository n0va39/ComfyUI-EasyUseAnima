from __future__ import annotations

from collections.abc import Callable
from typing import Any


def run_aio_detailer_stage(
    model,
    clip,
    vae,
    positive,
    negative,
    image,
    sampler_settings: dict[str, Any],
    detailer_settings: dict[str, Any],
    preview_callback=None,
    *,
    as_bool: Callable[..., bool],
    detailer_target_order: Callable[..., list[str]],
    load_sam3_context: Callable[..., dict[str, Any]],
    run_detailer_target: Callable[..., tuple[Any, dict[str, Any]]],
    context_value: Callable[..., Any],
) -> tuple[Any, dict[str, Any]]:
    if not as_bool(detailer_settings.get("enabled"), False):
        return image, {"enabled": False}
    target_order = detailer_target_order(detailer_settings)
    enabled_targets = [
        name
        for name in target_order
        if isinstance(detailer_settings.get(name), dict)
        and as_bool(detailer_settings[name].get("enabled"), False)
    ]
    if not enabled_targets:
        return image, {"enabled": False, "reason": "no target enabled"}

    sam3_context = load_sam3_context(detailer_settings)
    output = image
    target_results: dict[str, Any] = {}
    for target_name in target_order:
        if target_name not in enabled_targets:
            continue
        output, target_results[target_name] = run_detailer_target(
            target_name,
            detailer_settings[target_name],
            output,
            model,
            clip,
            vae,
            positive,
            negative,
            sampler_settings,
            sam3_context,
        )
        if preview_callback is not None:
            preview_callback(f"detailer_{target_name}", output)
    return output, {
        "enabled": True,
        "sam3_checkpoint": context_value(sam3_context, "ckpt_name"),
        "order": target_order,
        "targets": target_results,
    }


def run_aio_detailer_target(
    target_name: str,
    target_settings: dict[str, Any],
    image,
    model,
    clip,
    vae,
    positive,
    negative,
    sampler_settings: dict[str, Any],
    sam3_context: dict[str, Any],
    *,
    as_bool: Callable[..., bool],
    as_float: Callable[..., float],
    as_int: Callable[..., int],
    stage_sampler_settings: Callable[..., dict[str, Any]],
    apply_model_patches: Callable[..., Any],
    run_sam3_detailer: Callable[..., tuple[Any, ...]],
    cleanup_model: Callable[..., None],
    segs_has_items: Callable[..., bool],
    prompt_data_json_safe: Callable[..., Any],
) -> tuple[Any, dict[str, Any]]:
    if not as_bool(target_settings.get("enabled"), False):
        return image, {"enabled": False}

    stage_sampler = stage_sampler_settings(
        sampler_settings,
        target_settings,
        scheduler_default="sgm_uniform",
    )
    stage_model = apply_model_patches(
        model,
        clip,
        positive,
        stage_sampler,
    )
    try:
        result = run_sam3_detailer(
            enabled=True,
            image=image,
            ctx_SAM3=sam3_context,
            detect_prompt=target_settings.get("detect_prompt", target_name),
            detect_count=as_int(target_settings.get("detect_count"), 1),
            threshold=as_float(target_settings.get("threshold"), 0.5),
            refine_iterations=as_int(
                target_settings.get("refine_iterations"), 2
            ),
            individual_masks=as_bool(
                target_settings.get("individual_masks"), True
            ),
            combined=as_bool(target_settings.get("combined"), False),
            crop_factor=as_float(target_settings.get("crop_factor"), 4.0),
            bbox_fill=as_bool(target_settings.get("bbox_fill"), False),
            drop_size=as_int(target_settings.get("drop_size"), 100),
            contour_fill=as_bool(target_settings.get("contour_fill"), True),
            model=stage_model,
            clip=clip,
            vae=vae,
            guide_size=as_int(target_settings.get("guide_size"), 1024),
            guide_size_for=as_bool(
                target_settings.get("guide_size_for"), False
            ),
            max_size=as_int(target_settings.get("max_size"), 2048),
            seed=stage_sampler["seed"],
            steps=stage_sampler["steps"],
            cfg=stage_sampler["cfg"],
            sampler_name=stage_sampler["sampler_name"],
            scheduler=stage_sampler["scheduler"],
            positive=positive,
            negative=negative,
            denoise=stage_sampler["denoise"],
            feather=as_int(target_settings.get("feather"), 5),
            noise_mask=as_bool(target_settings.get("noise_mask"), True),
            force_inpaint=as_bool(
                target_settings.get("force_inpaint"), True
            ),
            wildcard=str(target_settings.get("wildcard") or ""),
            cycle=as_int(target_settings.get("cycle"), 1),
            alignment=str(target_settings.get("alignment") or "32"),
            preserve_conditioning_metadata=True,
            fail_on_unsupported_opt=False,
            detailer_hook=None,
            inpaint_model=as_bool(
                target_settings.get("inpaint_model"), False
            ),
            noise_mask_feather=as_int(
                target_settings.get("noise_mask_feather"), 0
            ),
            scheduler_func_opt=None,
            tiled_encode=as_bool(target_settings.get("tiled_encode"), False),
            tiled_decode=as_bool(target_settings.get("tiled_decode"), False),
        )
    finally:
        cleanup_model(stage_model, model)

    detailed_image = result[0]
    segs = result[1] if len(result) > 1 else None
    return detailed_image, {
        "enabled": True,
        "detected": segs_has_items(segs),
        "sampler": prompt_data_json_safe(stage_sampler),
    }


__all__ = ()
