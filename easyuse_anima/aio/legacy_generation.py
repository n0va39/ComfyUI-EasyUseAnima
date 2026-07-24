from __future__ import annotations

import logging
import random
from dataclasses import replace
from typing import Any, cast

from ..common.values import _as_bool, _as_float, _as_int, _single_value
from ..image.geometry import _image_tensor_size
from ..image.sam3 import _context_value, _segs_has_items
from ..infrastructure.comfy.invocation import _node_output_tuple
from ..infrastructure.comfy.wiring import resolve_comfy_host_helper
from ..nodes.image_nodes import EasyUseAnimaImageScaleByMultiple
from ..nodes.sam3_nodes import EasyUseAnimaSAM3Detailer
from ..prompt.artist_mix import _encode_prompt_data_positive_conditioning
from ..prompt.conditioning import (
    ANIMA_MOD_GUIDANCE_PROFILE_OFF,
    _apply_spectrum_anima_mod_guidance,
    _normalize_anima_mod_guidance_profile,
    _resolve_anima_mod_guidance_enabled,
)
from ..prompt.data import (
    _advanced_outputs_from_prompt_data,
    _normalize_prompt_data,
    _prompt_data_json_safe,
)
from .conditioning import _aio_usdu_conditioning
from .first_pass_cache import (
    _aio_first_pass_cache_key,
    _get_aio_first_pass_cache,
    _put_aio_first_pass_cache,
)
from .generation_defaults import AIO_USDU_PROMPT_FULL
from .generation_detailer_stage import AIODetailerStage, DetailerRuntime
from .generation_first_pass import AIOFirstPassStage, FirstPassRuntime
from .generation_highres import AIOHighresStage, HighresRuntime
from .generation_lifecycle import (
    EphemeralModelRegistry,
    ModelVariantResolver,
    ModelVariantRuntime,
    PreviewCollector,
    PreviewRuntime,
)
from .generation_normalization import (
    _aio_detailer_has_enabled_targets,
    _aio_detailer_target_order,
    _normalize_aio_generation_settings,
)
from .generation_pipeline import (
    ConditioningBundle,
    GenerationRequest,
    GenerationState,
    PromptExecutionData,
    ResourceBundle,
    WorkflowContext,
)
from .generation_postprocess_stage import (
    AIOPostprocessStage,
    PostprocessRuntime,
)
from .generation_save_output_stage import (
    AIOSaveOutputStage,
    SaveOutputRuntime,
)
from .generation_settings import _aio_generation_config_from_dict
from .generation_upscale_stage import AIOUpscaleStage, UpscaleRuntime
from .input_context import _require_easy_use_anima_input
from .model_preparation import (
    _apply_aio_lora_stack,
    _apply_aio_model_patches,
    _apply_aio_spectrum_model_patches_for_comfy_sampler,
    _cleanup_aio_ephemeral_model,
)
from .output import (
    _aio_save_filename_prefix,
    _save_image_with_comfy,
    _save_image_with_image_saver,
)
from .postprocess import (
    _resize_image_to_size_if_needed,
    _run_aio_postprocess_stage,
)
from .preview import (
    _save_aio_temp_preview_image,
    _send_aio_preview_event,
    _tag_aio_preview_images,
)
from .resources import (
    _load_aio_resources_from_input_context,
    _load_aio_sam3_context,
    _load_upscale_model_with_comfy,
)
from .sampling import (
    _aio_highres_effective_backend,
    _aio_stage_sampler_settings,
    _decode_latent_with_comfy,
    _encode_image_with_comfy_vae,
    _generate_empty_latent_with_comfy,
    _resolve_aio_runtime_seed,
    _sample_latent_with_aio_backend,
)
from .usdu import _aio_usdu_tile_plan

logger = logging.getLogger("ComfyUI-EasyUseAnima")


def _missing_host_helper(name: str):
    raise RuntimeError(
        f"[EasyUseAnima] AiO legacy generation Comfy host helper is unavailable: {name}"
    )


def _encode_with_comfy_clip(clip, text: str):
    helper = resolve_comfy_host_helper(
        "_encode_with_comfy_clip",
        _missing_host_helper,
    )
    return helper(clip, text)


def _require_custom_node_class(
    node_id: str,
    node_pack: str,
    install_hint: str,
):
    helper = resolve_comfy_host_helper(
        "_require_custom_node_class",
        _missing_host_helper,
    )
    return helper(node_id, node_pack, install_hint)


def _run_aio_highres_stage(
    model,
    clip,
    vae,
    positive,
    negative,
    image,
    base_latent,
    base_width: int,
    base_height: int,
    sampler_settings: dict[str, Any],
    highres_settings: dict[str, Any],
    mod_guidance_settings: dict[str, Any] | None = None,
    use_mod_guidance: bool = False,
    quality_tags: str = "",
    quality_neg: str = "",
) -> tuple[Any, Any, int, int, dict[str, Any]]:
    if not _as_bool(highres_settings.get("enabled"), False):
        return base_latent, image, int(base_width), int(base_height), {"enabled": False}

    stage_sampler = _aio_stage_sampler_settings(
        sampler_settings,
        highres_settings,
        scheduler_default="simple",
        inherit_backend=True,
    )
    scaled_image, width, height, applied_scale = EasyUseAnimaImageScaleByMultiple().upscale(
        image,
        highres_settings.get("scale_by", 1.25),
        highres_settings.get("upscale_method", "bicubic"),
        highres_settings.get("multiple", "32"),
        highres_settings.get("max_long_edge", 2560),
    )
    latent_image = _encode_image_with_comfy_vae(vae, scaled_image)
    stage_model = model
    if stage_sampler.get("backend") == "comfy_ksampler":
        stage_model = _apply_aio_spectrum_model_patches_for_comfy_sampler(
            model,
            clip,
            positive,
            stage_sampler,
        )
    try:
        latent = _sample_latent_with_aio_backend(
            stage_model,
            clip,
            positive,
            negative,
            latent_image,
            stage_sampler,
            mod_guidance_settings or {},
            use_mod_guidance,
            quality_tags,
            quality_neg,
        )
    finally:
        _cleanup_aio_ephemeral_model(stage_model, model)
    decoded = _decode_latent_with_comfy(vae, latent)
    decoded, resized = _resize_image_to_size_if_needed(
        decoded,
        width,
        height,
        highres_settings.get("upscale_method", "bicubic"),
    )
    if resized:
        latent = _encode_image_with_comfy_vae(vae, decoded)
    return latent, decoded, int(width), int(height), {
        "enabled": True,
        "width": int(width),
        "height": int(height),
        "applied_scale": float(applied_scale),
        "sampler": _prompt_data_json_safe(stage_sampler),
    }


def _run_aio_detailer_stage(
    model,
    clip,
    vae,
    positive,
    negative,
    image,
    sampler_settings: dict[str, Any],
    detailer_settings: dict[str, Any],
    preview_callback=None,
) -> tuple[Any, dict[str, Any]]:
    if not _as_bool(detailer_settings.get("enabled"), False):
        return image, {"enabled": False}
    target_order = _aio_detailer_target_order(detailer_settings)
    enabled_targets = [
        name
        for name in target_order
        if isinstance(detailer_settings.get(name), dict)
        and _as_bool(detailer_settings[name].get("enabled"), False)
    ]
    if not enabled_targets:
        return image, {"enabled": False, "reason": "no target enabled"}

    sam3_context = _load_aio_sam3_context(detailer_settings)
    output = image
    target_results: dict[str, Any] = {}
    for target_name in target_order:
        if target_name not in enabled_targets:
            continue
        output, target_results[target_name] = _run_aio_detailer_target(
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
        "sam3_checkpoint": _context_value(sam3_context, "ckpt_name"),
        "order": target_order,
        "targets": target_results,
    }


def _run_aio_detailer_target(
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
) -> tuple[Any, dict[str, Any]]:
    if not _as_bool(target_settings.get("enabled"), False):
        return image, {"enabled": False}

    stage_sampler = _aio_stage_sampler_settings(
        sampler_settings,
        target_settings,
        scheduler_default="sgm_uniform",
    )
    stage_model = _apply_aio_spectrum_model_patches_for_comfy_sampler(
        model,
        clip,
        positive,
        stage_sampler,
    )
    try:
        result = EasyUseAnimaSAM3Detailer().doit(
            enabled=True,
            image=image,
            ctx_SAM3=sam3_context,
            detect_prompt=target_settings.get("detect_prompt", target_name),
            detect_count=_as_int(
                target_settings.get("detect_count"), 1
            ),
            threshold=_as_float(
                target_settings.get("threshold"), 0.5
            ),
            refine_iterations=_as_int(
                target_settings.get("refine_iterations"), 2
            ),
            individual_masks=_as_bool(
                target_settings.get("individual_masks"), True
            ),
            combined=_as_bool(
                target_settings.get("combined"), False
            ),
            crop_factor=_as_float(
                target_settings.get("crop_factor"), 4.0
            ),
            bbox_fill=_as_bool(
                target_settings.get("bbox_fill"), False
            ),
            drop_size=_as_int(
                target_settings.get("drop_size"), 100
            ),
            contour_fill=_as_bool(
                target_settings.get("contour_fill"), True
            ),
            model=stage_model,
            clip=clip,
            vae=vae,
            guide_size=_as_int(
                target_settings.get("guide_size"), 1024
            ),
            guide_size_for=_as_bool(
                target_settings.get("guide_size_for"), False
            ),
            max_size=_as_int(
                target_settings.get("max_size"), 2048
            ),
            seed=stage_sampler["seed"],
            steps=stage_sampler["steps"],
            cfg=stage_sampler["cfg"],
            sampler_name=stage_sampler["sampler_name"],
            scheduler=stage_sampler["scheduler"],
            positive=positive,
            negative=negative,
            denoise=stage_sampler["denoise"],
            feather=_as_int(
                target_settings.get("feather"), 5
            ),
            noise_mask=_as_bool(
                target_settings.get("noise_mask"), True
            ),
            force_inpaint=_as_bool(
                target_settings.get("force_inpaint"), True
            ),
            wildcard=str(target_settings.get("wildcard") or ""),
            cycle=_as_int(
                target_settings.get("cycle"), 1
            ),
            alignment=str(target_settings.get("alignment") or "32"),
            preserve_conditioning_metadata=True,
            fail_on_unsupported_opt=False,
            detailer_hook=None,
            inpaint_model=_as_bool(
                target_settings.get("inpaint_model"), False
            ),
            noise_mask_feather=_as_int(
                target_settings.get("noise_mask_feather"), 0
            ),
            scheduler_func_opt=None,
            tiled_encode=_as_bool(
                target_settings.get("tiled_encode"), False
            ),
            tiled_decode=_as_bool(
                target_settings.get("tiled_decode"), False
            ),
        )
    finally:
        _cleanup_aio_ephemeral_model(stage_model, model)

    detailed_image = result[0]
    segs = result[1] if len(result) > 1 else None
    return detailed_image, {
        "enabled": True,
        "detected": _segs_has_items(segs),
        "sampler": _prompt_data_json_safe(stage_sampler),
    }


def _run_aio_usdu_upscale_stage(
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
) -> tuple[Any, dict[str, Any]]:
    usdu_settings = upscale_settings.get("usdu", {})
    if not isinstance(usdu_settings, dict):
        usdu_settings = {}
    usdu_cls = _require_custom_node_class(
        "UltimateSDUpscale",
        "ComfyUI_UltimateSDUpscale",
        "Required for AiO Generator final Upscale > USDU.",
    )
    upscale_model = _load_upscale_model_with_comfy(
        str(usdu_settings.get("upscale_model_name") or "")
    )
    stage_sampler = _aio_stage_sampler_settings(
        sampler_settings,
        upscale_settings,
        scheduler_default="simple",
    )
    scale_by = _as_float(upscale_settings.get("scale_by"), 2.0)
    tile_plan = _aio_usdu_tile_plan(image, scale_by, usdu_settings)
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
        _as_int(stage_sampler.get("steps"), 20),
        _as_float(stage_sampler.get("denoise"), 0.2),
        _as_float(stage_sampler.get("cfg"), 8.0),
        str(stage_sampler.get("sampler_name") or "euler"),
        str(stage_sampler.get("scheduler") or "simple"),
    )
    usdu_positive, usdu_negative = _aio_usdu_conditioning(
        clip,
        positive,
        negative,
        usdu_settings,
        quality_tags,
        quality_neg,
        prompt_data,
        exclude_positive_quality,
        exclude_negative_quality,
    )
    stage_model = _apply_aio_spectrum_model_patches_for_comfy_sampler(
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
            seed=_resolve_aio_runtime_seed(stage_sampler.get("seed")),
            steps=_as_int(stage_sampler.get("steps"), 20),
            cfg=_as_float(stage_sampler.get("cfg"), 8.0),
            sampler_name=str(stage_sampler.get("sampler_name") or "euler"),
            scheduler=str(stage_sampler.get("scheduler") or "simple"),
            denoise=_as_float(stage_sampler.get("denoise"), 0.2),
            upscale_model=upscale_model,
            mode_type=str(usdu_settings.get("mode_type") or "Linear"),
            tile_width=tile_width,
            tile_height=tile_height,
            mask_blur=_as_int(usdu_settings.get("mask_blur"), 8),
            tile_padding=_as_int(usdu_settings.get("tile_padding"), 32),
            seam_fix_mode=str(usdu_settings.get("seam_fix_mode") or "None"),
            seam_fix_denoise=_as_float(
                usdu_settings.get("seam_fix_denoise"), 1.0
            ),
            seam_fix_mask_blur=_as_int(
                usdu_settings.get("seam_fix_mask_blur"), 8
            ),
            seam_fix_width=_as_int(
                usdu_settings.get("seam_fix_width"), 64
            ),
            seam_fix_padding=_as_int(
                usdu_settings.get("seam_fix_padding"), 16
            ),
            force_uniform_tiles=_as_bool(
                usdu_settings.get("force_uniform_tiles"), True
            ),
            tiled_decode=_as_bool(
                usdu_settings.get("tiled_decode"), False
            ),
            batch_size=_as_int(
                usdu_settings.get("batch_size"), 1
            ),
        )
    finally:
        _cleanup_aio_ephemeral_model(stage_model, model)
    values = _node_output_tuple(result)
    if not values:
        raise RuntimeError("[EasyUseAnima] UltimateSDUpscale returned no IMAGE.")
    output = values[0]
    width, height = _image_tensor_size(output, 0, 0)
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
        "prompt_mode": str(
            usdu_settings.get("prompt_mode")
            or AIO_USDU_PROMPT_FULL
        ),
        "sampler": _prompt_data_json_safe(stage_sampler),
    }


def _run_aio_resshift_upscale_stage(
    image,
    sampler_settings: dict[str, Any],
    upscale_settings: dict[str, Any],
    quality_tags: str = "",
    quality_neg: str = "",
    prompt_data: str | dict | None = None,
    exclude_positive_quality: bool = False,
    exclude_negative_quality: bool = False,
) -> tuple[Any, dict[str, Any]]:
    resshift_settings = upscale_settings.get("resshift", {})
    if not isinstance(resshift_settings, dict):
        resshift_settings = {}
    loader_cls = _require_custom_node_class(
        "ResShiftLoader",
        "ComfyUI-Distilled-ResShift",
        "Required for AiO Generator final Upscale > ResShift.",
    )
    upscale_cls = _require_custom_node_class(
        "ResShiftUpscale",
        "ComfyUI-Distilled-ResShift",
        "Required for AiO Generator final Upscale > ResShift.",
    )
    loader = loader_cls()
    load = getattr(loader, "load", None)
    if load is None:
        raise RuntimeError("[EasyUseAnima] ResShiftLoader does not expose load().")
    model_values = _node_output_tuple(
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
    values = _node_output_tuple(
        upscale(
            model_values[0],
            image,
            _resolve_aio_runtime_seed(sampler_settings.get("seed")),
            _as_int(resshift_settings.get("chop"), 512),
            _as_int(resshift_settings.get("overlap"), 64),
            _as_int(resshift_settings.get("tile_batch"), 4),
        )
    )
    if not values:
        raise RuntimeError("[EasyUseAnima] ResShiftUpscale returned no IMAGE.")
    output = values[0]
    width, height = _image_tensor_size(output, 0, 0)
    return output, {
        "enabled": True,
        "backend": "resshift",
        "width": int(width),
        "height": int(height),
        "scale": str(resshift_settings.get("scale") or "x2"),
    }


def _run_aio_upscale_stage(
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
) -> tuple[Any, dict[str, Any]]:
    if not _as_bool(upscale_settings.get("enabled"), False):
        return image, {"enabled": False}
    backend = str(upscale_settings.get("backend") or "usdu")
    if backend == "usdu":
        output, metadata = _run_aio_usdu_upscale_stage(
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
        )
    elif backend == "resshift":
        output, metadata = _run_aio_resshift_upscale_stage(
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


def _run_aio_legacy_generation(
    generator,
    easy_use_anima_input,
    generation_settings: str | dict | None = None,
    lora_stack=None,
    workflow_prompt=None,
    extra_pnginfo=None,
    unique_id=None,
):
    context = _require_easy_use_anima_input(easy_use_anima_input)
    settings = _normalize_aio_generation_settings(generation_settings)
    settings["sampler"]["seed"] = _resolve_aio_runtime_seed(
        settings["sampler"].get("seed")
    )
    return _run_aio_normalized_legacy_generation(
        generator,
        context,
        settings,
        lora_stack,
        workflow_prompt,
        extra_pnginfo,
        unique_id,
    )


def _run_aio_normalized_legacy_generation(
    generator,
    context: dict[str, Any],
    settings: dict[str, Any],
    lora_stack=None,
    workflow_prompt=None,
    extra_pnginfo=None,
    unique_id=None,
):
    if settings["mode"] != "txt2img":
        raise RuntimeError("[EasyUseAnima] AiO Generator draft currently supports txt2img only.")
    generation_config = _aio_generation_config_from_dict(settings)

    base_model, base_clip, vae = _load_aio_resources_from_input_context(context)
    model_with_lora, clip, applied_loras = _apply_aio_lora_stack(
        base_model,
        base_clip,
        lora_stack,
    )
    model = _apply_aio_model_patches(model_with_lora, settings)
    prompt_data = _normalize_prompt_data(context["prompt_data"])
    (
        positive_prompt,
        negative_prompt,
        quality_tags,
        quality_neg,
        use_anima_mod_guidance,
        use_negative_anima_mod_guidance,
        metadata_prompt,
        metadata_negative_prompt,
        width,
        height,
    ) = _advanced_outputs_from_prompt_data(prompt_data)
    artist_mix = settings["artist_mix"]
    positive = _encode_prompt_data_positive_conditioning(
        clip,
        prompt_data,
        positive_prompt,
        artist_mix_mode=artist_mix["mode"],
        artist_mix_start_percent=artist_mix["start_percent"],
        artist_mix_strength_scale=artist_mix["strength_scale"],
        artist_mix_style_gain=artist_mix["style_gain"],
        artist_mix_rms_scale_cap=artist_mix["rms_scale_cap"],
        artist_mix_exact_top_k=artist_mix["exact_top_k"],
        artist_mix_cluster_count=artist_mix["cluster_count"],
        artist_mix_dominant_isolation=artist_mix["dominant_isolation"],
        artist_mix_dominant_threshold=artist_mix["dominant_threshold"],
    )
    negative = _encode_with_comfy_clip(clip, negative_prompt)

    sampler = settings["sampler"]
    mod_guidance = settings["mod_guidance"]
    will_run_highres = _as_bool(settings["highres"].get("enabled"), False)
    will_run_detailer = _aio_detailer_has_enabled_targets(settings["detailer"])
    will_run_upscale = _as_bool(settings["upscale"].get("enabled"), False)
    will_run_postprocess = _as_bool(settings["postprocess"].get("enabled"), False)
    profile = _normalize_anima_mod_guidance_profile(
        mod_guidance["profile"]
    )
    use_mod_guidance = _resolve_anima_mod_guidance_enabled(
        use_anima_mod_guidance,
        mod_guidance["mode"],
    )
    sampler_backend = str(sampler.get("backend") or "comfy_ksampler")
    highres_backend = _aio_highres_effective_backend(
        sampler, settings["highres"]
    )
    can_apply_standalone_mod_guidance = (
        use_mod_guidance
        and profile != ANIMA_MOD_GUIDANCE_PROFILE_OFF
    )
    model_registry = EphemeralModelRegistry(
        base_model=base_model,
        cleanup_model=_cleanup_aio_ephemeral_model,
        model=model,
        model_with_lora=model_with_lora,
    )
    model_variants = ModelVariantResolver(
        runtime=ModelVariantRuntime(
            apply_standalone_mod_guidance=_apply_spectrum_anima_mod_guidance,
            apply_comfy_sampler_patches=(
                _apply_aio_spectrum_model_patches_for_comfy_sampler
            ),
        ),
        registry=model_registry,
        model=model,
        clip=clip,
        positive=positive,
        negative=negative,
        quality_tags=quality_tags,
        quality_negative=(
            quality_neg if use_negative_anima_mod_guidance else ""
        ),
        profile=profile,
        use_mod_guidance=use_mod_guidance,
        can_apply_standalone_mod_guidance=(
            can_apply_standalone_mod_guidance
        ),
    )
    base_sample_model, base_use_mod_guidance = (
        model_variants.prepare_first_pass(sampler_backend, sampler)
    )

    generation_state = GenerationState(
        latent=None,
        image=None,
        width=width,
        height=height,
    )
    preview_settings = settings["preview"]
    preview_node_id = _single_value(unique_id)
    preview_run_id = (
        f"{preview_node_id or 'aio'}:"
        f"{random.getrandbits(64):016x}"
    )
    preview_collector = PreviewCollector(
        runtime=PreviewRuntime(
            save_temp_preview=_save_aio_temp_preview_image,
            send_preview_event=_send_aio_preview_event,
        ),
        previews=generation_state.previews,
        node_id=preview_node_id,
        run_id=preview_run_id,
        workflow_prompt=workflow_prompt,
        extra_pnginfo=extra_pnginfo,
    )
    cache_scope = str(unique_id or id(generator))
    first_pass_cache_key = _aio_first_pass_cache_key(
        cache_scope=cache_scope,
        context=context,
        prompt_data=prompt_data,
        lora_stack=lora_stack,
        settings=settings,
        positive_prompt=positive_prompt,
        negative_prompt=negative_prompt,
        quality_tags=quality_tags,
        quality_neg=quality_neg,
        use_anima_mod_guidance=use_anima_mod_guidance,
        use_negative_anima_mod_guidance=use_negative_anima_mod_guidance,
        width=width,
        height=height,
    )
    generation_request = GenerationRequest(
        config=generation_config,
        prompts=PromptExecutionData(
            prompt_data=prompt_data,
            positive_prompt=positive_prompt,
            negative_prompt=negative_prompt,
            quality_tags=quality_tags,
            quality_negative=quality_neg,
            metadata_positive_prompt=metadata_prompt,
            metadata_negative_prompt=metadata_negative_prompt,
            use_anima_mod_guidance=use_anima_mod_guidance,
            use_negative_anima_mod_guidance=(
                use_negative_anima_mod_guidance
            ),
        ),
        resources=ResourceBundle(
            base_model=base_model,
            base_clip=base_clip,
            model_with_lora=model_with_lora,
            model=base_sample_model,
            clip=clip,
            vae=vae,
            applied_loras=tuple(applied_loras),
        ),
        conditioning=ConditioningBundle(
            positive=positive,
            negative=negative,
        ),
        workflow=WorkflowContext(
            input_context=context,
            lora_stack=lora_stack,
            workflow_prompt=workflow_prompt,
            extra_pnginfo=extra_pnginfo,
            unique_id=unique_id,
            cache_scope=cache_scope,
        ),
    )

    first_pass_stage = AIOFirstPassStage(
        runtime=FirstPassRuntime(
            get_cache=_get_aio_first_pass_cache,
            put_cache=_put_aio_first_pass_cache,
            generate_empty_latent=_generate_empty_latent_with_comfy,
            sample_latent=_sample_latent_with_aio_backend,
            decode_latent=_decode_latent_with_comfy,
            resize_image=_resize_image_to_size_if_needed,
            encode_image=_encode_image_with_comfy_vae,
        ),
        cache_key=first_pass_cache_key,
        use_mod_guidance=base_use_mod_guidance,
        add_preview=(
            preview_collector.add
            if preview_settings["intermediate_images"]
            else None
        ),
    )

    try:
        first_pass_stage.validate(
            generation_request,
            {"sampler_backend": sampler_backend},
        )
        first_pass_stage.run(generation_request, generation_state)
        highres_model, highres_use_mod_guidance = (
            model_variants.for_backend(highres_backend)
            if will_run_highres
            else (model, False)
        )
        highres_request = replace(
            generation_request,
            resources=replace(
                generation_request.resources,
                model=highres_model,
            ),
        )
        highres_stage = AIOHighresStage(
            runtime=HighresRuntime(
                run_highres=_run_aio_highres_stage,
            ),
            use_mod_guidance=highres_use_mod_guidance,
            add_preview=preview_collector.add,
            preview_before_detailer=will_run_detailer,
        )
        highres_stage.validate(
            highres_request,
            {"sampler_backend": highres_backend},
        )
        highres_stage.run(highres_request, generation_state)
        detailer_model = (
            model_variants.standalone_model()
            if will_run_detailer
            else model_variants.mod_guidance_model
        )
        detailer_request = replace(
            generation_request,
            resources=replace(
                generation_request.resources,
                model=detailer_model,
            ),
        )
        detailer_stage = AIODetailerStage(
            runtime=DetailerRuntime(
                run_detailer=_run_aio_detailer_stage,
                image_size=_image_tensor_size,
            ),
            add_preview=preview_collector.add,
        )
        detailer_stage.validate(detailer_request, {})
        detailer_stage.run(detailer_request, generation_state)
        upscale_model = (
            model_variants.standalone_model()
            if will_run_upscale
            else model_variants.mod_guidance_model
        )
        upscale_request = replace(
            generation_request,
            resources=replace(
                generation_request.resources,
                model=upscale_model,
            ),
        )
        upscale_stage = AIOUpscaleStage(
            runtime=UpscaleRuntime(
                run_upscale=_run_aio_upscale_stage,
                image_size=_image_tensor_size,
                encode_image=_encode_image_with_comfy_vae,
            ),
            exclude_positive_quality=can_apply_standalone_mod_guidance,
            exclude_negative_quality=(
                can_apply_standalone_mod_guidance
                and use_negative_anima_mod_guidance
            ),
            add_preview=preview_collector.add,
        )
        upscale_stage.validate(upscale_request, {})
        upscale_stage.run(upscale_request, generation_state)
        postprocess_stage = AIOPostprocessStage(
            runtime=PostprocessRuntime(
                run_postprocess=_run_aio_postprocess_stage,
                as_bool=_as_bool,
                image_size=_image_tensor_size,
                encode_image=_encode_image_with_comfy_vae,
            ),
            will_run_postprocess=will_run_postprocess,
            add_preview=preview_collector.add,
        )
        postprocess_stage.validate(generation_request, {})
        postprocess_stage.run(generation_request, generation_state)
    finally:
        model_registry.close()

    save_output_stage = AIOSaveOutputStage(
        runtime=SaveOutputRuntime(
            save_comfy=_save_image_with_comfy,
            save_image_saver=_save_image_with_image_saver,
            filename_prefix=_aio_save_filename_prefix,
            tag_images=_tag_aio_preview_images,
            save_temp_preview=_save_aio_temp_preview_image,
            json_safe=_prompt_data_json_safe,
        ),
        applied_loras=applied_loras,
        preview_run_id=preview_run_id,
    )
    save_output_stage.validate(generation_request, {})
    save_output_stage.run(generation_request, generation_state)
    return cast(dict[str, Any], save_output_stage.output)


__all__ = ()
