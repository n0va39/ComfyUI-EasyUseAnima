"""Private SAM3 and Impact detailer execution operations."""

from __future__ import annotations

import logging

from ..common.values import _as_bool
from ..infrastructure.comfy.invocation import _node_output_tuple
from ..infrastructure.comfy.wiring import resolve_comfy_host_helper
from .detailer import _EasyUseAnimaAlignedDetailerHook
from .geometry import _alignment_value
from .sam3 import (
    _call_impact_detailer,
    _context_value,
    _empty_mask_for_image,
    _empty_segs_for_image,
    _find_impact_detailer_class,
    _find_impact_mask_to_segs_class,
    _find_sam3_detect_class,
    _format_sam3_detection_prompt,
    _segs_has_items,
)

logger = logging.getLogger("ComfyUI-EasyUseAnima")


def _missing_host_helper(name: str):
    raise RuntimeError(f"SAM3 node Comfy host helper is unavailable: {name}")


def _encode_with_comfy_clip(clip, text: str):
    helper = resolve_comfy_host_helper(
        "_encode_with_comfy_clip",
        _missing_host_helper,
    )
    return helper(clip, text)


def _run_impact_detailer(
    image,
    segs,
    model,
    clip,
    vae,
    guide_size,
    guide_size_for,
    max_size,
    seed,
    steps,
    cfg,
    sampler_name,
    scheduler,
    positive,
    negative,
    denoise,
    feather,
    noise_mask,
    force_inpaint,
    wildcard,
    cycle=1,
    alignment="impact",
    preserve_conditioning_metadata=True,
    fail_on_unsupported_opt=False,
    detailer_hook=None,
    inpaint_model=False,
    noise_mask_feather=0,
    scheduler_func_opt=None,
    tiled_encode=False,
    tiled_decode=False,
):
    alignment_text = str(alignment or "impact")
    alignment_int = _alignment_value(alignment_text)

    if not _as_bool(preserve_conditioning_metadata, True):
        logger.warning(
            "[EasyUseAnima] preserve_conditioning_metadata=false is reserved for a native backend; "
            "the Impact backend leaves conditioning handling to Impact Pack."
        )

    effective_detailer_hook = detailer_hook
    if alignment_int is not None:
        effective_detailer_hook = _EasyUseAnimaAlignedDetailerHook(detailer_hook, alignment_int)

    detailer_cls = _find_impact_detailer_class()
    detailer = detailer_cls()
    result = _call_impact_detailer(
        detailer,
        image=image,
        segs=segs,
        model=model,
        clip=clip,
        vae=vae,
        guide_size=guide_size,
        guide_size_for=guide_size_for,
        max_size=max_size,
        seed=seed,
        steps=steps,
        cfg=cfg,
        sampler_name=sampler_name,
        scheduler=scheduler,
        positive=positive,
        negative=negative,
        denoise=denoise,
        feather=feather,
        noise_mask=noise_mask,
        force_inpaint=force_inpaint,
        wildcard=wildcard,
        cycle=cycle,
        detailer_hook=effective_detailer_hook,
        inpaint_model=inpaint_model,
        noise_mask_feather=noise_mask_feather,
        scheduler_func_opt=scheduler_func_opt,
        tiled_encode=tiled_encode,
        tiled_decode=tiled_decode,
    )
    if isinstance(result, dict):
        value = result.get("result")
        if isinstance(value, tuple) and value:
            return (value[0],)
    if isinstance(result, tuple):
        if not result:
            raise RuntimeError("[EasyUseAnima] Impact DetailerForEach returned an empty tuple.")
        return (result[0],)
    return (result,)


def _run_sam3_detailer(
    enabled,
    image,
    ctx_SAM3,
    detect_prompt,
    detect_count,
    threshold,
    refine_iterations,
    individual_masks,
    combined,
    crop_factor,
    bbox_fill,
    drop_size,
    contour_fill,
    model,
    clip,
    vae,
    guide_size,
    guide_size_for,
    max_size,
    seed,
    steps,
    cfg,
    sampler_name,
    scheduler,
    positive,
    negative,
    denoise,
    feather,
    noise_mask,
    force_inpaint,
    wildcard,
    cycle=1,
    alignment="impact",
    preserve_conditioning_metadata=True,
    fail_on_unsupported_opt=False,
    detailer_hook=None,
    inpaint_model=False,
    noise_mask_feather=0,
    scheduler_func_opt=None,
    tiled_encode=False,
    tiled_decode=False,
):
    empty_mask = _empty_mask_for_image(image)
    empty_segs = _empty_segs_for_image(image)
    if not _as_bool(enabled, True):
        return (image, empty_segs, empty_mask, image)

    sam3_model = _context_value(ctx_SAM3, "model")
    sam3_clip = _context_value(ctx_SAM3, "clip")
    if sam3_model is None or sam3_clip is None:
        raise RuntimeError(
            "[EasyUseAnima] ctx_SAM3 must contain SAM3 model and CLIP. "
            "Use the AiO SAM3 detailer path or a compatible rgthree context."
        )

    sam3_text = _format_sam3_detection_prompt(detect_prompt, detect_count)
    conditioning = _encode_with_comfy_clip(sam3_clip, sam3_text)

    sam3_cls = _find_sam3_detect_class()
    sam3_result = sam3_cls.execute(
        model=sam3_model,
        image=image,
        conditioning=conditioning,
        threshold=float(threshold),
        refine_iterations=int(refine_iterations),
        individual_masks=_as_bool(individual_masks, False),
    )
    sam3_values = _node_output_tuple(sam3_result)
    if len(sam3_values) < 1:
        raise RuntimeError("[EasyUseAnima] SAM3_Detect returned no mask.")
    mask = sam3_values[0]

    mask_to_segs_cls = _find_impact_mask_to_segs_class()
    mask_to_segs_result = mask_to_segs_cls.doit(
        mask,
        _as_bool(combined, False),
        float(crop_factor),
        _as_bool(bbox_fill, False),
        int(drop_size),
        _as_bool(contour_fill, False),
    )
    segs_values = _node_output_tuple(mask_to_segs_result)
    if len(segs_values) < 1:
        raise RuntimeError("[EasyUseAnima] MaskToSEGS returned no SEGS.")
    segs = segs_values[0]

    if not _segs_has_items(segs):
        logger.info("[EasyUseAnima] SAM3 Detailer detected no SEGS for prompt %r.", sam3_text)
        return (image, segs, mask, image)

    detailed_image = _run_impact_detailer(
        image=image,
        segs=segs,
        model=model,
        clip=clip,
        vae=vae,
        guide_size=guide_size,
        guide_size_for=guide_size_for,
        max_size=max_size,
        seed=seed,
        steps=steps,
        cfg=cfg,
        sampler_name=sampler_name,
        scheduler=scheduler,
        positive=positive,
        negative=negative,
        denoise=denoise,
        feather=feather,
        noise_mask=noise_mask,
        force_inpaint=force_inpaint,
        wildcard=wildcard,
        cycle=cycle,
        alignment=alignment,
        preserve_conditioning_metadata=preserve_conditioning_metadata,
        fail_on_unsupported_opt=fail_on_unsupported_opt,
        detailer_hook=detailer_hook,
        inpaint_model=inpaint_model,
        noise_mask_feather=noise_mask_feather,
        scheduler_func_opt=scheduler_func_opt,
        tiled_encode=tiled_encode,
        tiled_decode=tiled_decode,
    )[0]

    return (detailed_image, segs, mask, image)


__all__ = ()
