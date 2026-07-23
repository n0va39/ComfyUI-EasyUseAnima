from __future__ import annotations

from collections.abc import Callable
from typing import Any

from .input_context import _require_easy_use_anima_input

_RuntimeResolver = Callable[[str], Any]

_RUNTIME_RESOLVER: _RuntimeResolver | None = None


def _bind_aio_legacy_generation_runtime(*, resolve_helper: _RuntimeResolver) -> None:
    global _RUNTIME_RESOLVER

    _RUNTIME_RESOLVER = resolve_helper


def _runtime_helper(name: str) -> Any:
    resolver = _RUNTIME_RESOLVER
    if resolver is None:
        raise RuntimeError("AiO legacy generation runtime is not bound.")
    return resolver(name)


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
    if not _runtime_helper("_as_bool")(
        highres_settings.get("enabled"), False
    ):
        return base_latent, image, int(base_width), int(base_height), {"enabled": False}

    stage_sampler = _runtime_helper("_aio_stage_sampler_settings")(
        sampler_settings,
        highres_settings,
        scheduler_default="simple",
        inherit_backend=True,
    )
    scaled_image, width, height, applied_scale = _runtime_helper(
        "EasyUseAnimaImageScaleByMultiple"
    )().upscale(
        image,
        highres_settings.get("scale_by", 1.25),
        highres_settings.get("upscale_method", "bicubic"),
        highres_settings.get("multiple", "32"),
        highres_settings.get("max_long_edge", 2560),
    )
    latent_image = _runtime_helper("_encode_image_with_comfy_vae")(
        vae, scaled_image
    )
    stage_model = model
    if stage_sampler.get("backend") == "comfy_ksampler":
        stage_model = _runtime_helper(
            "_apply_aio_spectrum_model_patches_for_comfy_sampler"
        )(
            model,
            clip,
            positive,
            stage_sampler,
        )
    try:
        latent = _runtime_helper("_sample_latent_with_aio_backend")(
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
        _runtime_helper("_cleanup_aio_ephemeral_model")(stage_model, model)
    decoded = _runtime_helper("_decode_latent_with_comfy")(vae, latent)
    decoded, resized = _runtime_helper("_resize_image_to_size_if_needed")(
        decoded,
        width,
        height,
        highres_settings.get("upscale_method", "bicubic"),
    )
    if resized:
        latent = _runtime_helper("_encode_image_with_comfy_vae")(vae, decoded)
    return latent, decoded, int(width), int(height), {
        "enabled": True,
        "width": int(width),
        "height": int(height),
        "applied_scale": float(applied_scale),
        "sampler": _runtime_helper("_prompt_data_json_safe")(stage_sampler),
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
    if not _runtime_helper("_as_bool")(
        detailer_settings.get("enabled"), False
    ):
        return image, {"enabled": False}
    target_order = _runtime_helper("_aio_detailer_target_order")(detailer_settings)
    enabled_targets = [
        name
        for name in target_order
        if isinstance(detailer_settings.get(name), dict)
        and _runtime_helper("_as_bool")(
            detailer_settings[name].get("enabled"), False
        )
    ]
    if not enabled_targets:
        return image, {"enabled": False, "reason": "no target enabled"}

    sam3_context = _runtime_helper("_load_aio_sam3_context")(detailer_settings)
    output = image
    target_results: dict[str, Any] = {}
    for target_name in target_order:
        if target_name not in enabled_targets:
            continue
        output, target_results[target_name] = _runtime_helper(
            "_run_aio_detailer_target"
        )(
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
        "sam3_checkpoint": _runtime_helper("_context_value")(
            sam3_context, "ckpt_name"
        ),
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
    if not _runtime_helper("_as_bool")(
        target_settings.get("enabled"), False
    ):
        return image, {"enabled": False}

    stage_sampler = _runtime_helper("_aio_stage_sampler_settings")(
        sampler_settings,
        target_settings,
        scheduler_default="sgm_uniform",
    )
    stage_model = _runtime_helper(
        "_apply_aio_spectrum_model_patches_for_comfy_sampler"
    )(
        model,
        clip,
        positive,
        stage_sampler,
    )
    try:
        result = _runtime_helper("EasyUseAnimaSAM3Detailer")().doit(
            enabled=True,
            image=image,
            ctx_SAM3=sam3_context,
            detect_prompt=target_settings.get("detect_prompt", target_name),
            detect_count=_runtime_helper("_as_int")(
                target_settings.get("detect_count"), 1
            ),
            threshold=_runtime_helper("_as_float")(
                target_settings.get("threshold"), 0.5
            ),
            refine_iterations=_runtime_helper("_as_int")(
                target_settings.get("refine_iterations"), 2
            ),
            individual_masks=_runtime_helper("_as_bool")(
                target_settings.get("individual_masks"), True
            ),
            combined=_runtime_helper("_as_bool")(
                target_settings.get("combined"), False
            ),
            crop_factor=_runtime_helper("_as_float")(
                target_settings.get("crop_factor"), 4.0
            ),
            bbox_fill=_runtime_helper("_as_bool")(
                target_settings.get("bbox_fill"), False
            ),
            drop_size=_runtime_helper("_as_int")(
                target_settings.get("drop_size"), 100
            ),
            contour_fill=_runtime_helper("_as_bool")(
                target_settings.get("contour_fill"), True
            ),
            model=stage_model,
            clip=clip,
            vae=vae,
            guide_size=_runtime_helper("_as_int")(
                target_settings.get("guide_size"), 1024
            ),
            guide_size_for=_runtime_helper("_as_bool")(
                target_settings.get("guide_size_for"), False
            ),
            max_size=_runtime_helper("_as_int")(
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
            feather=_runtime_helper("_as_int")(
                target_settings.get("feather"), 5
            ),
            noise_mask=_runtime_helper("_as_bool")(
                target_settings.get("noise_mask"), True
            ),
            force_inpaint=_runtime_helper("_as_bool")(
                target_settings.get("force_inpaint"), True
            ),
            wildcard=str(target_settings.get("wildcard") or ""),
            cycle=_runtime_helper("_as_int")(
                target_settings.get("cycle"), 1
            ),
            alignment=str(target_settings.get("alignment") or "32"),
            preserve_conditioning_metadata=True,
            fail_on_unsupported_opt=False,
            detailer_hook=None,
            inpaint_model=_runtime_helper("_as_bool")(
                target_settings.get("inpaint_model"), False
            ),
            noise_mask_feather=_runtime_helper("_as_int")(
                target_settings.get("noise_mask_feather"), 0
            ),
            scheduler_func_opt=None,
            tiled_encode=_runtime_helper("_as_bool")(
                target_settings.get("tiled_encode"), False
            ),
            tiled_decode=_runtime_helper("_as_bool")(
                target_settings.get("tiled_decode"), False
            ),
        )
    finally:
        _runtime_helper("_cleanup_aio_ephemeral_model")(stage_model, model)

    detailed_image = result[0]
    segs = result[1] if len(result) > 1 else None
    return detailed_image, {
        "enabled": True,
        "detected": _runtime_helper("_segs_has_items")(segs),
        "sampler": _runtime_helper("_prompt_data_json_safe")(stage_sampler),
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
    usdu_cls = _runtime_helper("_require_custom_node_class")(
        "UltimateSDUpscale",
        "ComfyUI_UltimateSDUpscale",
        "Required for AiO Generator final Upscale > USDU.",
    )
    upscale_model = _runtime_helper("_load_upscale_model_with_comfy")(
        str(usdu_settings.get("upscale_model_name") or "")
    )
    stage_sampler = _runtime_helper("_aio_stage_sampler_settings")(
        sampler_settings,
        upscale_settings,
        scheduler_default="simple",
    )
    scale_by = _runtime_helper("_as_float")(
        upscale_settings.get("scale_by"), 2.0
    )
    tile_plan = _runtime_helper("_aio_usdu_tile_plan")(
        image, scale_by, usdu_settings
    )
    tile_width = int(tile_plan["tile_width"])
    tile_height = int(tile_plan["tile_height"])
    if tile_plan.get("auto"):
        _runtime_helper("logger").info(
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
        _runtime_helper("logger").info(
            "[EasyUseAnima][AiO] USDU manual tile: input=%sx%s scale_by=%.3g expected=%sx%s tile=%sx%s",
            tile_plan.get("input_width"),
            tile_plan.get("input_height"),
            scale_by,
            tile_plan.get("target_width"),
            tile_plan.get("target_height"),
            tile_width,
            tile_height,
        )
    _runtime_helper("logger").info(
        "[EasyUseAnima][AiO] USDU sampler: steps=%s denoise=%.3f cfg=%.3g sampler=%s scheduler=%s",
        _runtime_helper("_as_int")(stage_sampler.get("steps"), 20),
        _runtime_helper("_as_float")(stage_sampler.get("denoise"), 0.2),
        _runtime_helper("_as_float")(stage_sampler.get("cfg"), 8.0),
        str(stage_sampler.get("sampler_name") or "euler"),
        str(stage_sampler.get("scheduler") or "simple"),
    )
    usdu_positive, usdu_negative = _runtime_helper("_aio_usdu_conditioning")(
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
    stage_model = _runtime_helper(
        "_apply_aio_spectrum_model_patches_for_comfy_sampler"
    )(
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
            seed=_runtime_helper("_resolve_aio_runtime_seed")(
                stage_sampler.get("seed")
            ),
            steps=_runtime_helper("_as_int")(stage_sampler.get("steps"), 20),
            cfg=_runtime_helper("_as_float")(stage_sampler.get("cfg"), 8.0),
            sampler_name=str(stage_sampler.get("sampler_name") or "euler"),
            scheduler=str(stage_sampler.get("scheduler") or "simple"),
            denoise=_runtime_helper("_as_float")(
                stage_sampler.get("denoise"), 0.2
            ),
            upscale_model=upscale_model,
            mode_type=str(usdu_settings.get("mode_type") or "Linear"),
            tile_width=tile_width,
            tile_height=tile_height,
            mask_blur=_runtime_helper("_as_int")(
                usdu_settings.get("mask_blur"), 8
            ),
            tile_padding=_runtime_helper("_as_int")(
                usdu_settings.get("tile_padding"), 32
            ),
            seam_fix_mode=str(usdu_settings.get("seam_fix_mode") or "None"),
            seam_fix_denoise=_runtime_helper("_as_float")(
                usdu_settings.get("seam_fix_denoise"), 1.0
            ),
            seam_fix_mask_blur=_runtime_helper("_as_int")(
                usdu_settings.get("seam_fix_mask_blur"), 8
            ),
            seam_fix_width=_runtime_helper("_as_int")(
                usdu_settings.get("seam_fix_width"), 64
            ),
            seam_fix_padding=_runtime_helper("_as_int")(
                usdu_settings.get("seam_fix_padding"), 16
            ),
            force_uniform_tiles=_runtime_helper("_as_bool")(
                usdu_settings.get("force_uniform_tiles"), True
            ),
            tiled_decode=_runtime_helper("_as_bool")(
                usdu_settings.get("tiled_decode"), False
            ),
            batch_size=_runtime_helper("_as_int")(
                usdu_settings.get("batch_size"), 1
            ),
        )
    finally:
        _runtime_helper("_cleanup_aio_ephemeral_model")(stage_model, model)
    values = _runtime_helper("_node_output_tuple")(result)
    if not values:
        raise RuntimeError("[EasyUseAnima] UltimateSDUpscale returned no IMAGE.")
    output = values[0]
    width, height = _runtime_helper("_image_tensor_size")(output, 0, 0)
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
            or _runtime_helper("AIO_USDU_PROMPT_FULL")
        ),
        "sampler": _runtime_helper("_prompt_data_json_safe")(stage_sampler),
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
    loader_cls = _runtime_helper("_require_custom_node_class")(
        "ResShiftLoader",
        "ComfyUI-Distilled-ResShift",
        "Required for AiO Generator final Upscale > ResShift.",
    )
    upscale_cls = _runtime_helper("_require_custom_node_class")(
        "ResShiftUpscale",
        "ComfyUI-Distilled-ResShift",
        "Required for AiO Generator final Upscale > ResShift.",
    )
    loader = loader_cls()
    load = getattr(loader, "load", None)
    if load is None:
        raise RuntimeError("[EasyUseAnima] ResShiftLoader does not expose load().")
    model_values = _runtime_helper("_node_output_tuple")(
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
    values = _runtime_helper("_node_output_tuple")(
        upscale(
            model_values[0],
            image,
            _runtime_helper("_resolve_aio_runtime_seed")(sampler_settings.get("seed")),
            _runtime_helper("_as_int")(resshift_settings.get("chop"), 512),
            _runtime_helper("_as_int")(resshift_settings.get("overlap"), 64),
            _runtime_helper("_as_int")(resshift_settings.get("tile_batch"), 4),
        )
    )
    if not values:
        raise RuntimeError("[EasyUseAnima] ResShiftUpscale returned no IMAGE.")
    output = values[0]
    width, height = _runtime_helper("_image_tensor_size")(output, 0, 0)
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
    if not _runtime_helper("_as_bool")(
        upscale_settings.get("enabled"), False
    ):
        return image, {"enabled": False}
    backend = str(upscale_settings.get("backend") or "usdu")
    if backend == "usdu":
        output, metadata = _runtime_helper("_run_aio_usdu_upscale_stage")(
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
        output, metadata = _runtime_helper("_run_aio_resshift_upscale_stage")(
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
    settings = _runtime_helper("_normalize_aio_generation_settings")(generation_settings)
    settings["sampler"]["seed"] = _runtime_helper("_resolve_aio_runtime_seed")(
        settings["sampler"].get("seed")
    )
    if settings["mode"] != "txt2img":
        raise RuntimeError("[EasyUseAnima] AiO Generator draft currently supports txt2img only.")

    base_model, base_clip, vae = _runtime_helper(
        "_load_aio_resources_from_input_context"
    )(context)
    model_with_lora, clip, applied_loras = _runtime_helper("_apply_aio_lora_stack")(
        base_model,
        base_clip,
        lora_stack,
    )
    model = _runtime_helper("_apply_aio_model_patches")(model_with_lora, settings)
    prompt_data = _runtime_helper("_normalize_prompt_data")(context["prompt_data"])
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
    ) = _runtime_helper("_advanced_outputs_from_prompt_data")(prompt_data)
    image_saver_positive_prompt = metadata_prompt or positive_prompt
    image_saver_negative_prompt = metadata_negative_prompt or negative_prompt

    artist_mix = settings["artist_mix"]
    positive = _runtime_helper("_encode_prompt_data_positive_conditioning")(
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
    negative = _runtime_helper("_encode_with_comfy_clip")(clip, negative_prompt)

    sampler = settings["sampler"]
    mod_guidance = settings["mod_guidance"]
    will_run_highres = _runtime_helper("_as_bool")(
        settings["highres"].get("enabled"), False
    )
    will_run_detailer = _runtime_helper("_aio_detailer_has_enabled_targets")(
        settings["detailer"]
    )
    will_run_upscale = _runtime_helper("_as_bool")(
        settings["upscale"].get("enabled"), False
    )
    will_run_postprocess = _runtime_helper("_as_bool")(
        settings["postprocess"].get("enabled"), False
    )
    profile = _runtime_helper("_normalize_anima_mod_guidance_profile")(
        mod_guidance["profile"]
    )
    use_mod_guidance = _runtime_helper("_resolve_anima_mod_guidance_enabled")(
        use_anima_mod_guidance,
        mod_guidance["mode"],
    )
    sampler_backend = str(sampler.get("backend") or "comfy_ksampler")
    highres_backend = _runtime_helper("_aio_highres_effective_backend")(
        sampler, settings["highres"]
    )
    mod_guidance_model = model
    can_apply_standalone_mod_guidance = (
        use_mod_guidance
        and profile != _runtime_helper("ANIMA_MOD_GUIDANCE_PROFILE_OFF")
    )

    def ensure_standalone_mod_guidance_model():
        nonlocal mod_guidance_model
        if not can_apply_standalone_mod_guidance or mod_guidance_model is not model:
            return mod_guidance_model
        mod_guidance_model = _runtime_helper("_apply_spectrum_anima_mod_guidance")(
            model,
            clip,
            positive,
            negative,
            quality_tags,
            quality_neg if use_negative_anima_mod_guidance else "",
            profile,
        )
        return mod_guidance_model

    def model_and_mod_guidance_flag_for_backend(backend: str):
        if backend == "spectrum_mod_guidance_advanced":
            if mod_guidance_model is not model:
                return mod_guidance_model, False
            return model, use_mod_guidance
        return ensure_standalone_mod_guidance_model(), False

    base_sample_model, base_use_mod_guidance = model_and_mod_guidance_flag_for_backend(
        sampler_backend
    )
    if sampler_backend == "comfy_ksampler":
        base_sample_model = _runtime_helper(
            "_apply_aio_spectrum_model_patches_for_comfy_sampler"
        )(
            base_sample_model,
            clip,
            positive,
            sampler,
        )

    stage_metadata: dict[str, Any] = {}
    preview_settings = settings["preview"]
    preview_images: list[dict[str, Any]] = []
    preview_node_id = _runtime_helper("_single_value")(unique_id)
    preview_run_id = (
        f"{preview_node_id or 'aio'}:"
        f"{_runtime_helper('random').getrandbits(64):016x}"
    )
    first_pass_cache_key = _runtime_helper("_aio_first_pass_cache_key")(
        cache_scope=str(unique_id or id(generator)),
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
    first_pass_cache_hit = False

    def add_preview(stage: str, stage_image):
        images = _runtime_helper("_save_aio_temp_preview_image")(
            stage_image,
            stage,
            workflow_prompt=workflow_prompt,
            extra_pnginfo=extra_pnginfo,
        )
        if images:
            preview_images.extend(images)
            _runtime_helper("_send_aio_preview_event")(
                preview_node_id, preview_run_id, stage, images
            )

    try:
        cached_first_pass = _runtime_helper("_get_aio_first_pass_cache")(
            first_pass_cache_key
        )
        if cached_first_pass is not None:
            latent, image = cached_first_pass
            first_pass_cache_hit = True
        else:
            latent_image = _runtime_helper("_generate_empty_latent_with_comfy")(
                width, height
            )
            latent = _runtime_helper("_sample_latent_with_aio_backend")(
                base_sample_model,
                clip,
                positive,
                negative,
                latent_image,
                sampler,
                mod_guidance,
                base_use_mod_guidance,
                quality_tags,
                quality_neg if use_negative_anima_mod_guidance else "",
            )
            image = _runtime_helper("_decode_latent_with_comfy")(vae, latent)
        image, first_pass_resized = _runtime_helper(
            "_resize_image_to_size_if_needed"
        )(
            image,
            width,
            height,
            "bicubic",
        )
        if first_pass_resized:
            latent = _runtime_helper("_encode_image_with_comfy_vae")(vae, image)
        if not first_pass_cache_hit or first_pass_resized:
            try:
                _runtime_helper("_put_aio_first_pass_cache")(
                    first_pass_cache_key, latent, image
                )
            except Exception as exc:
                _runtime_helper("logger").debug(
                    "[EasyUseAnima] failed to store AiO first-pass cache: %s", exc
                )
        stage_metadata["first_pass"] = {"cache_hit": first_pass_cache_hit}
        if preview_settings["intermediate_images"]:
            add_preview("first_pass", image)
        highres_model, highres_use_mod_guidance = (
            model_and_mod_guidance_flag_for_backend(highres_backend)
            if will_run_highres
            else (model, False)
        )
        latent, image, width, height, highres_metadata = _runtime_helper(
            "_run_aio_highres_stage"
        )(
            highres_model,
            clip,
            vae,
            positive,
            negative,
            image,
            latent,
            width,
            height,
            sampler,
            settings["highres"],
            mod_guidance,
            highres_use_mod_guidance,
            quality_tags,
            quality_neg if use_negative_anima_mod_guidance else "",
        )
        stage_metadata["highres"] = highres_metadata
        if highres_metadata.get("enabled") and isinstance(
            highres_metadata.get("sampler"), dict
        ):
            if preview_settings["intermediate_images"] and will_run_detailer:
                add_preview("highres", image)
        image, detailer_metadata = _runtime_helper("_run_aio_detailer_stage")(
            ensure_standalone_mod_guidance_model()
            if will_run_detailer
            else mod_guidance_model,
            clip,
            vae,
            positive,
            negative,
            image,
            sampler,
            settings["detailer"],
            add_preview if preview_settings["intermediate_images"] else None,
        )
        stage_metadata["detailer"] = detailer_metadata
        if detailer_metadata.get("enabled"):
            width, height = _runtime_helper("_image_tensor_size")(image, width, height)
        image, upscale_metadata = _runtime_helper("_run_aio_upscale_stage")(
            ensure_standalone_mod_guidance_model()
            if will_run_upscale
            else mod_guidance_model,
            clip,
            vae,
            positive,
            negative,
            image,
            sampler,
            settings["upscale"],
            quality_tags,
            quality_neg,
            prompt_data,
            exclude_positive_quality=can_apply_standalone_mod_guidance,
            exclude_negative_quality=(
                can_apply_standalone_mod_guidance and use_negative_anima_mod_guidance
            ),
        )
        stage_metadata["upscale"] = upscale_metadata
        if upscale_metadata.get("enabled"):
            width, height = _runtime_helper("_image_tensor_size")(image, width, height)
            latent = _runtime_helper("_encode_image_with_comfy_vae")(vae, image)
            if preview_settings["intermediate_images"]:
                add_preview("upscale", image)
        image, postprocess_metadata = _runtime_helper("_run_aio_postprocess_stage")(
            image,
            settings["postprocess"],
        )
        stage_metadata["postprocess"] = postprocess_metadata
        if postprocess_metadata.get("enabled"):
            width, height = _runtime_helper("_image_tensor_size")(image, width, height)
            postprocess_changed = _runtime_helper("_as_bool")(
                (postprocess_metadata.get("fit") or {}).get("applied"),
                False,
            )
            if postprocess_changed:
                latent = _runtime_helper("_encode_image_with_comfy_vae")(vae, image)
            if (
                preview_settings["intermediate_images"]
                and postprocess_changed
                and will_run_postprocess
            ):
                add_preview("postprocess", image)
    finally:
        seen_model_ids: set[int] = set()
        for ephemeral_model in (
            base_sample_model,
            mod_guidance_model,
            model,
            model_with_lora,
        ):
            if ephemeral_model is None:
                continue
            key = id(ephemeral_model)
            if key in seen_model_ids:
                continue
            seen_model_ids.add(key)
            _runtime_helper("_cleanup_aio_ephemeral_model")(
                ephemeral_model, base_model
            )

    save_settings = settings["save"]
    save_ui = {}
    if save_settings.get("enabled"):
        if save_settings.get("backend") == "image_saver":
            save_result = _runtime_helper("_save_image_with_image_saver")(
                image,
                save_settings,
                positive_prompt=image_saver_positive_prompt,
                negative_prompt=image_saver_negative_prompt,
                width=width,
                height=height,
                sampler_settings=sampler,
                applied_loras=applied_loras,
                resource_info=context.get("resource_info", {}),
                workflow_prompt=workflow_prompt,
                extra_pnginfo=extra_pnginfo,
            )
        else:
            save_result = _runtime_helper("_save_image_with_comfy")(
                image,
                _runtime_helper("_aio_save_filename_prefix")(save_settings),
                workflow_prompt=workflow_prompt,
                extra_pnginfo=extra_pnginfo,
            )
        if isinstance(save_result, dict) and isinstance(save_result.get("ui"), dict):
            save_ui = save_result["ui"]
    final_preview = _runtime_helper("_tag_aio_preview_images")(
        save_ui.get("images", []), "final", width=width, height=height
    )
    if not final_preview:
        final_preview = _runtime_helper("_save_aio_temp_preview_image")(
            image,
            "final",
            workflow_prompt=workflow_prompt,
            extra_pnginfo=extra_pnginfo,
        )
    if (
        final_preview
        and preview_images
        and str(preview_images[-1].get("stage") or "").startswith("detailer_")
    ):
        preview_images[-1] = final_preview[0]
        final_preview = final_preview[1:]

    metadata = {
        "schema": "easyuse_anima_aio_generation_result",
        "version": 1,
        "width": int(width),
        "height": int(height),
        "resource_info": _runtime_helper("_prompt_data_json_safe")(
            context.get("resource_info", {})
        ),
        "input_settings": _runtime_helper("_prompt_data_json_safe")(
            context.get("input_settings", {})
        ),
        "lora_stack": _runtime_helper("_prompt_data_json_safe")(applied_loras),
        "generation_settings": _runtime_helper("_prompt_data_json_safe")(settings),
        "stages": _runtime_helper("_prompt_data_json_safe")(stage_metadata),
        "prompt_data": _runtime_helper("_prompt_data_json_safe")(prompt_data),
    }
    metadata_json = _runtime_helper("json").dumps(
        metadata, ensure_ascii=False, sort_keys=True
    )
    ui = {
        "status": ["generated"],
        "width": [int(width)],
        "height": [int(height)],
        "unet_name": [str(context.get("resource_info", {}).get("unet_name", ""))],
        "sampler_backend": [str(sampler.get("backend") or "comfy_ksampler")],
        "easyuse_anima_run_id": [preview_run_id],
    }
    preview_payload = preview_images + final_preview
    if final_preview:
        ui["images"] = final_preview
    if preview_payload:
        ui["easyuse_anima_preview"] = preview_payload
    return {
        "ui": ui,
        "result": (image, latent, metadata_json),
    }


__all__ = ()
