from __future__ import annotations

import logging
import random
from dataclasses import replace
from typing import Any, cast

from ..common.values import _as_bool, _as_float, _as_int, _single_value
from ..image.geometry import _image_tensor_size
from ..image.sam3 import _context_value, _segs_has_items
from ..image.sam3_detailer import _run_sam3_detailer
from ..image.upscale import _upscale_image_by_multiple
from ..infrastructure.comfy.invocation import _node_output_tuple
from ..infrastructure.comfy.wiring import resolve_comfy_host_helper
from ..prompt.artist_mix import _encode_prompt_data_positive_conditioning
from ..prompt.conditioning import (
    ANIMA_MOD_GUIDANCE_PROFILE_OFF,
    _apply_spectrum_anima_mod_guidance,
    _normalize_anima_mod_guidance_profile,
    _resolve_anima_mod_guidance_enabled,
)
from ..prompt.data import (
    _advanced_outputs_from_prompt_data,
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
    StageModelVariantResolver,
    StageModelVariantRuntime,
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
from .hooks import AioHookRun, AioStage, prepare_aio_hook
from .input_context import _require_easy_use_anima_input
from .legacy_detailer import (
    run_aio_detailer_stage as _run_aio_detailer_stage_impl,
)
from .legacy_detailer import (
    run_aio_detailer_target as _run_aio_detailer_target_impl,
)
from .legacy_upscale import (
    run_aio_resshift_upscale_stage as _run_aio_resshift_upscale_stage_impl,
)
from .legacy_upscale import (
    run_aio_upscale_stage as _run_aio_upscale_stage_impl,
)
from .legacy_upscale import (
    run_aio_usdu_upscale_stage as _run_aio_usdu_upscale_stage_impl,
)
from .model_preparation import (
    _aio_stage_model_patch_plan,
    _apply_aio_lora_stack,
    _apply_aio_spectrum_model_patches_for_comfy_sampler,
    _apply_aio_stage_model_patch_plan,
    _cleanup_aio_ephemeral_model,
)
from .negpip import (
    _aio_negpip_execution_prompts,
    _aio_negpip_metadata,
    _aio_negpip_mode,
    apply_aio_negpip,
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
from .prompt_lora import _normalize_prompt_data, _prepare_aio_prompt_loras
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
    scaled_image, width, height, applied_scale = _upscale_image_by_multiple(
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
    return _run_aio_detailer_stage_impl(
        model,
        clip,
        vae,
        positive,
        negative,
        image,
        sampler_settings,
        detailer_settings,
        preview_callback,
        as_bool=_as_bool,
        detailer_target_order=_aio_detailer_target_order,
        load_sam3_context=_load_aio_sam3_context,
        run_detailer_target=_run_aio_detailer_target,
        context_value=_context_value,
    )


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
    return _run_aio_detailer_target_impl(
        target_name,
        target_settings,
        image,
        model,
        clip,
        vae,
        positive,
        negative,
        sampler_settings,
        sam3_context,
        as_bool=_as_bool,
        as_float=_as_float,
        as_int=_as_int,
        stage_sampler_settings=_aio_stage_sampler_settings,
        apply_model_patches=_apply_aio_spectrum_model_patches_for_comfy_sampler,
        run_sam3_detailer=_run_sam3_detailer,
        cleanup_model=_cleanup_aio_ephemeral_model,
        segs_has_items=_segs_has_items,
        prompt_data_json_safe=_prompt_data_json_safe,
    )


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
    negpip_mode: str = "off",
) -> tuple[Any, dict[str, Any]]:
    return _run_aio_usdu_upscale_stage_impl(
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
        logger=logger,
        usdu_prompt_full=AIO_USDU_PROMPT_FULL,
        require_custom_node_class=_require_custom_node_class,
        load_upscale_model=_load_upscale_model_with_comfy,
        stage_sampler_settings=_aio_stage_sampler_settings,
        as_bool=_as_bool,
        as_float=_as_float,
        as_int=_as_int,
        usdu_tile_plan=_aio_usdu_tile_plan,
        usdu_conditioning=_aio_usdu_conditioning,
        apply_model_patches=_apply_aio_spectrum_model_patches_for_comfy_sampler,
        resolve_runtime_seed=_resolve_aio_runtime_seed,
        cleanup_model=_cleanup_aio_ephemeral_model,
        node_output_tuple=_node_output_tuple,
        image_tensor_size=_image_tensor_size,
        prompt_data_json_safe=_prompt_data_json_safe,
    )


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
    return _run_aio_resshift_upscale_stage_impl(
        image,
        sampler_settings,
        upscale_settings,
        quality_tags,
        quality_neg,
        prompt_data,
        exclude_positive_quality,
        exclude_negative_quality,
        require_custom_node_class=_require_custom_node_class,
        node_output_tuple=_node_output_tuple,
        resolve_runtime_seed=_resolve_aio_runtime_seed,
        as_int=_as_int,
        image_tensor_size=_image_tensor_size,
    )


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
    negpip_mode: str = "off",
) -> tuple[Any, dict[str, Any]]:
    return _run_aio_upscale_stage_impl(
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
        as_bool=_as_bool,
        run_usdu_upscale_stage=_run_aio_usdu_upscale_stage,
        run_resshift_upscale_stage=_run_aio_resshift_upscale_stage,
    )


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
    return _run_aio_generation_pipeline(
        generator,
        context,
        settings,
        lora_stack,
        workflow_prompt,
        extra_pnginfo,
        unique_id,
    )


def _run_aio_generation_pipeline(
    generator,
    context: dict[str, Any],
    settings: dict[str, Any],
    lora_stack=None,
    workflow_prompt=None,
    extra_pnginfo=None,
    unique_id=None, aio_hook=None,
):
    if settings["mode"] != "txt2img":
        raise RuntimeError("[EasyUseAnima] AiO Generator draft currently supports txt2img only.")
    generation_config, prepared_aio_hook = _aio_generation_config_from_dict(settings), prepare_aio_hook(aio_hook)
    prompt_data, effective_lora_stack = _prepare_aio_prompt_loras(context["prompt_data"], lora_stack, normalize_prompt_data=_normalize_prompt_data)
    base_model, base_clip, vae = _load_aio_resources_from_input_context(context)
    model_with_lora, clip, applied_loras = _apply_aio_lora_stack(
        base_model,
        base_clip,
        effective_lora_stack,
    )
    negpip_mode = _aio_negpip_mode(settings.get("negpip"))
    model_lineage_base = model_with_lora
    try:
        model_lineage_base, clip = apply_aio_negpip(
            model_with_lora,
            clip,
            negpip_mode,
        )
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
        (
            _positive_execution_prompt,
            negative_execution_prompt,
            _derived_negative_contribution,
        ) = _aio_negpip_execution_prompts(
            positive_prompt,
            negative_prompt,
            negpip_mode,
        )
        artist_mix = settings["artist_mix"]
        positive = _encode_prompt_data_positive_conditioning(
            clip,
            prompt_data,
            positive_prompt,
            positive_execution_suffix=_derived_negative_contribution,
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
        negative = _encode_with_comfy_clip(clip, negative_execution_prompt)
    except BaseException:
        if model_lineage_base is not model_with_lora:
            _cleanup_aio_ephemeral_model(model_lineage_base, base_model)
        _cleanup_aio_ephemeral_model(model_with_lora, base_model)
        raise
    sampler = settings["sampler"]
    mod_guidance = settings["mod_guidance"]
    will_run_highres = _as_bool(settings["highres"].get("enabled"), False)
    will_run_detailer = _aio_detailer_has_enabled_targets(settings["detailer"])
    will_run_upscale = _as_bool(settings["upscale"].get("enabled"), False)
    will_run_usdu = (
        will_run_upscale
        and str(settings["upscale"].get("backend") or "usdu") == "usdu"
    )
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
        model_with_lora=model_with_lora,
    )
    if model_lineage_base is not model_with_lora:
        model_registry.register_model(model_lineage_base)
    stage_models = StageModelVariantResolver(
        runtime=StageModelVariantRuntime(
            build_plan=_aio_stage_model_patch_plan,
            apply_plan=_apply_aio_stage_model_patch_plan,
        ),
        registry=model_registry,
        model_with_lora=model_lineage_base,
        settings=settings,
    )
    model_variant_runtime = ModelVariantRuntime(
        apply_standalone_mod_guidance=_apply_spectrum_anima_mod_guidance,
        apply_comfy_sampler_patches=(
            _apply_aio_spectrum_model_patches_for_comfy_sampler
        ),
    )
    model_variant_resolvers: dict[int, ModelVariantResolver] = {}
    def variants_for(stage_model: object) -> ModelVariantResolver:
        model_id = id(stage_model)
        existing = model_variant_resolvers.get(model_id)
        if existing is not None and existing.model is stage_model:
            return existing
        resolver = ModelVariantResolver(
            runtime=model_variant_runtime,
            registry=model_registry,
            model=stage_model,
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
        model_variant_resolvers[model_id] = resolver
        return resolver
    try:
        first_pass_model = stage_models.resolve("first_pass")
        first_pass_variants = variants_for(first_pass_model)
        base_sample_model, base_use_mod_guidance = (
            first_pass_variants.prepare_first_pass(sampler_backend, sampler)
        )
    except BaseException:
        model_registry.close()
        raise
    generation_state = GenerationState(
        latent=None,
        image=None,
        width=width,
        height=height,
    )
    model_patches_by_stage = {
        "first_pass": list(stage_models.patch_ids("first_pass")),
        "highres": [],
        "detailer": [],
        "upscale": [],
    }
    generation_state.metadata["model_patches_by_stage"] = model_patches_by_stage
    negpip_metadata = _aio_negpip_metadata(
        negpip_mode,
        negative_prompt=negative_prompt,
    )
    if negpip_metadata is not None:
        generation_state.metadata["negpip"] = negpip_metadata
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
        lora_stack=effective_lora_stack,
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
            model_with_lora=model_lineage_base,
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
            lora_stack=effective_lora_stack,
            workflow_prompt=workflow_prompt,
            extra_pnginfo=extra_pnginfo,
            unique_id=unique_id,
            cache_scope=cache_scope,
        ),
    )
    first_pass_hook_enabled = any(point.stage is AioStage.FIRST_PASS for prepared in prepared_aio_hook for point in prepared.points)
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
        use_cache=not first_pass_hook_enabled,
        add_preview=(
            preview_collector.add
            if preview_settings["intermediate_images"]
            else None
        ),
    )
    try:
        with AioHookRun(prepared_aio_hook, generation_request, generation_state, preview_run_id, preview_collector.add) as hook_run:
            hook_run.run_stage(first_pass_stage, generation_request, generation_state, {"sampler_backend": sampler_backend})
            if will_run_highres:
                highres_stage_model = stage_models.resolve("highres")
                model_patches_by_stage["highres"] = list(
                    stage_models.patch_ids("highres")
                )
                highres_model, highres_use_mod_guidance = (
                    variants_for(highres_stage_model).for_backend(highres_backend)
                )
            else:
                highres_model, highres_use_mod_guidance = first_pass_model, False
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
            if will_run_detailer:
                detailer_stage_model = stage_models.resolve("detailer")
                model_patches_by_stage["detailer"] = list(
                    stage_models.patch_ids("detailer")
                )
                detailer_model = variants_for(detailer_stage_model).standalone_model()
            else:
                detailer_model = first_pass_model
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
            if will_run_usdu:
                upscale_stage_model = stage_models.resolve("upscale")
                model_patches_by_stage["upscale"] = list(
                    stage_models.patch_ids("upscale")
                )
                upscale_model = variants_for(upscale_stage_model).standalone_model()
            else:
                upscale_model = first_pass_model
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
            generation_request = hook_run.run_stage(postprocess_stage, generation_request, generation_state, {})
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
