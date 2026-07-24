# -*- coding: utf-8 -*-
from __future__ import annotations

try:
    from .easyuse_anima.aio.first_pass_cache import (
        AIO_FIRST_PASS_CACHE_MAX_ENTRIES as AIO_FIRST_PASS_CACHE_MAX_ENTRIES,
        _AIO_FIRST_PASS_CACHE as _AIO_FIRST_PASS_CACHE,
        _AIO_FIRST_PASS_CACHE_ORDER as _AIO_FIRST_PASS_CACHE_ORDER,
        _aio_first_pass_cache_key as _aio_first_pass_cache_key,
        # B-10b7 retires the test-only root cache-clear function alias.
        _clone_aio_cache_value as _clone_aio_cache_value,
        _get_aio_first_pass_cache as _get_aio_first_pass_cache,
        _put_aio_first_pass_cache as _put_aio_first_pass_cache,
    )
    from .easyuse_anima.aio.legacy_generation import (
        _run_aio_detailer_stage as _run_aio_detailer_stage,
        _run_aio_detailer_target as _run_aio_detailer_target,
        _run_aio_highres_stage as _run_aio_highres_stage,
        _run_aio_legacy_generation as _run_aio_legacy_generation,
        _run_aio_resshift_upscale_stage as _run_aio_resshift_upscale_stage,
        _run_aio_upscale_stage as _run_aio_upscale_stage,
        _run_aio_usdu_upscale_stage as _run_aio_usdu_upscale_stage,
    )
    from .easyuse_anima.aio.generation_normalization import (
        _AIO_DETAILER_CUSTOM_RE as _AIO_DETAILER_CUSTOM_RE,
        _AIO_DETAILER_RESERVED_KEYS as _AIO_DETAILER_RESERVED_KEYS,
        _aio_detailer_has_enabled_targets as _aio_detailer_has_enabled_targets,
        _aio_detailer_target_defaults as _aio_detailer_target_defaults,
        _aio_detailer_target_order as _aio_detailer_target_order,
        _is_aio_detailer_target_name as _is_aio_detailer_target_name,
        _merge_versioned_settings as _merge_versioned_settings,
        _normalize_aio_dit_corrections_settings as _normalize_aio_dit_corrections_settings,
        _normalize_aio_generation_settings as _normalize_aio_generation_settings,
        _normalize_aio_seed as _normalize_aio_seed,
        _normalize_aio_spectrum_settings as _normalize_aio_spectrum_settings,
    )
    from .easyuse_anima.aio.generation_defaults import (
        AIO_FINAL_FIT_MODES as AIO_FINAL_FIT_MODES,
        AIO_FINAL_UPSCALE_BACKENDS as AIO_FINAL_UPSCALE_BACKENDS,
        AIO_GENERATION_DEFAULT_SETTINGS as AIO_GENERATION_DEFAULT_SETTINGS,
        AIO_GENERATION_SETTINGS_SCHEMA as AIO_GENERATION_SETTINGS_SCHEMA,
        AIO_GENERATION_SETTINGS_VERSION as AIO_GENERATION_SETTINGS_VERSION,
        AIO_RESHIFT_DTYPES as AIO_RESHIFT_DTYPES,
        AIO_RESHIFT_SCALES as AIO_RESHIFT_SCALES,
        AIO_SPECIAL_SEEDS as AIO_SPECIAL_SEEDS,
        AIO_SPECIAL_SEED_DECREMENT as AIO_SPECIAL_SEED_DECREMENT,
        AIO_SPECIAL_SEED_INCREMENT as AIO_SPECIAL_SEED_INCREMENT,
        AIO_SPECIAL_SEED_RANDOM as AIO_SPECIAL_SEED_RANDOM,
        AIO_USDU_MODE_TYPES as AIO_USDU_MODE_TYPES,
        AIO_USDU_PROMPT_FULL as AIO_USDU_PROMPT_FULL,
        AIO_USDU_PROMPT_MODES as AIO_USDU_PROMPT_MODES,
        AIO_USDU_PROMPT_NO_GENERAL as AIO_USDU_PROMPT_NO_GENERAL,
        AIO_USDU_SEAM_FIX_MODES as AIO_USDU_SEAM_FIX_MODES,
    )
    from .easyuse_anima.aio.generation_settings import (
        round_trip_aio_generation_settings as _round_trip_aio_generation_settings,
    )
    from .easyuse_anima.aio.input_defaults import (
        AIO_INPUT_DEFAULT_SETTINGS as AIO_INPUT_DEFAULT_SETTINGS,
        ANIMA_CLIP_DEVICES as ANIMA_CLIP_DEVICES,
        ANIMA_CLIP_TYPES as ANIMA_CLIP_TYPES,
        ANIMA_DEFAULT_CLIP_CANDIDATES as ANIMA_DEFAULT_CLIP_CANDIDATES,
        ANIMA_DEFAULT_DIFFUSION_MODEL_CANDIDATES as ANIMA_DEFAULT_DIFFUSION_MODEL_CANDIDATES,
        ANIMA_DEFAULT_VAE_CANDIDATES as ANIMA_DEFAULT_VAE_CANDIDATES,
        ANIMA_UNET_WEIGHT_DTYPES as ANIMA_UNET_WEIGHT_DTYPES,
        EASY_USE_ANIMA_INPUT_SCHEMA as EASY_USE_ANIMA_INPUT_SCHEMA,
        EASY_USE_ANIMA_INPUT_SETTINGS_VERSION as EASY_USE_ANIMA_INPUT_SETTINGS_VERSION,
    )
    from .easyuse_anima.aio.input_context import (
        _easy_use_anima_input_signature as _easy_use_anima_input_signature,
        _require_easy_use_anima_input as _require_easy_use_anima_input,
    )
    from .easyuse_anima.aio.usdu import (
        _aio_usdu_auto_tile_dimension as _aio_usdu_auto_tile_dimension,
        _aio_usdu_tile_plan as _aio_usdu_tile_plan,
    )
    from .easyuse_anima.aio.postprocess import (
        _apply_aio_final_fit as _apply_aio_final_fit,
        _aio_final_fit_size as _aio_final_fit_size,
        _resize_image_to_size_if_needed as _resize_image_to_size_if_needed,
        _run_aio_postprocess_stage as _run_aio_postprocess_stage,
    )
    from .easyuse_anima.aio.conditioning import (
        _aio_prompt_data_fields_for_usdu as _aio_prompt_data_fields_for_usdu,
        _aio_usdu_conditioning as _aio_usdu_conditioning,
        _aio_usdu_prompt_without_general as _aio_usdu_prompt_without_general,
    )
    from .easyuse_anima.aio.model_preparation import (
        _aio_lora_stack_signature as _aio_lora_stack_signature,
        _apply_aio_anima_dave_patch as _apply_aio_anima_dave_patch,
        _apply_aio_kj_model_patches as _apply_aio_kj_model_patches,
        _apply_aio_lora_stack as _apply_aio_lora_stack,
        _apply_aio_model_patches as _apply_aio_model_patches,
        _apply_aio_safe_pag_patch as _apply_aio_safe_pag_patch,
        _apply_aio_spectrum_correction_patch_for_comfy_sampler as _apply_aio_spectrum_correction_patch_for_comfy_sampler,
        _apply_aio_spectrum_forecast_patch_for_comfy_sampler as _apply_aio_spectrum_forecast_patch_for_comfy_sampler,
        _apply_aio_spectrum_model_patches_for_comfy_sampler as _apply_aio_spectrum_model_patches_for_comfy_sampler,
        _cleanup_aio_ephemeral_model as _cleanup_aio_ephemeral_model,
        _normalize_aio_lora_stack as _normalize_aio_lora_stack,
        _patch_model_sampling_aura_flow as _patch_model_sampling_aura_flow,
    )
    from .easyuse_anima.aio.sampling import (
        _aio_highres_effective_backend as _aio_highres_effective_backend,
        _aio_stage_sampler_settings as _aio_stage_sampler_settings,
        _decode_latent_with_comfy as _decode_latent_with_comfy,
        _encode_image_with_comfy_vae as _encode_image_with_comfy_vae,
        _generate_empty_latent_with_comfy as _generate_empty_latent_with_comfy,
        _new_aio_random_seed as _new_aio_random_seed,
        _resolve_aio_runtime_seed as _resolve_aio_runtime_seed,
        _sample_latent_with_aio_backend as _sample_latent_with_aio_backend,
        _sample_latent_with_comfy as _sample_latent_with_comfy,
        _sample_latent_with_spectrum_mod_guidance_advanced as _sample_latent_with_spectrum_mod_guidance_advanced,
        _sample_latent_with_spectrum_spd as _sample_latent_with_spectrum_spd,
    )
    from .easyuse_anima.aio.preview import (
        AIO_PREVIEW_CACHE_FORMAT as AIO_PREVIEW_CACHE_FORMAT,
        AIO_PREVIEW_CACHE_QUALITY as AIO_PREVIEW_CACHE_QUALITY,
        AIO_PREVIEW_EVENT as AIO_PREVIEW_EVENT,
        AIO_PREVIEW_STAGE_LABELS as AIO_PREVIEW_STAGE_LABELS,
        _aio_preview_base_directory as _aio_preview_base_directory,
        _aio_preview_file_size_bytes as _aio_preview_file_size_bytes,
        _save_aio_temp_preview_image as _save_aio_temp_preview_image,
        _send_aio_preview_event as _send_aio_preview_event,
        _tag_aio_preview_images as _tag_aio_preview_images,
    )
    from .easyuse_anima.aio.output import (
        _aio_image_saver_additional_hashes as _aio_image_saver_additional_hashes,
        _aio_image_saver_civitai_hash_fetcher_entries as _aio_image_saver_civitai_hash_fetcher_entries,
        _aio_lora_metadata_name as _aio_lora_metadata_name,
        _aio_prompt_with_lora_metadata as _aio_prompt_with_lora_metadata,
        _aio_save_filename_prefix as _aio_save_filename_prefix,
        _save_image_with_comfy as _save_image_with_comfy,
        _save_image_with_image_saver as _save_image_with_image_saver,
    )
    from .easyuse_anima.aio.output_settings import (
        _normalize_aio_civitai_hash_fetchers as _normalize_aio_civitai_hash_fetchers,
        _normalize_aio_hash_bundles as _normalize_aio_hash_bundles,
    )
    from .easyuse_anima.aio.resources import (
        _comfy_clip_loader_types as _comfy_clip_loader_types,
        _comfy_diffusion_model_names as _comfy_diffusion_model_names,
        _comfy_text_encoder_names as _comfy_text_encoder_names,
        _comfy_vae_names as _comfy_vae_names,
        _load_aio_resources_from_input_context as _load_aio_resources_from_input_context,
        _load_aio_sam3_context as _load_aio_sam3_context,
        _load_checkpoint_with_comfy as _load_checkpoint_with_comfy,
        _load_clip_with_comfy as _load_clip_with_comfy,
        _load_diffusion_model_with_comfy as _load_diffusion_model_with_comfy,
        _load_upscale_model_with_comfy as _load_upscale_model_with_comfy,
        _load_vae_with_comfy as _load_vae_with_comfy,
        _normalize_aio_input_settings as _normalize_aio_input_settings,
        _preferred_checkpoint_default as _preferred_checkpoint_default,
        _preferred_clip_type_default as _preferred_clip_type_default,
        _preferred_name_default as _preferred_name_default,
    )
    from .easyuse_anima.common.serialization import (
        _json_clone as _json_clone,
        _json_object as _json_object,
        _stable_change_key as _stable_change_key,
    )
    from .easyuse_anima.common.values import (
        _as_bool as _as_bool,
        _as_float as _as_float,
        _as_int as _as_int,
        _choice as _choice,
        _single_value as _single_value,
    )
    from .easyuse_anima.seed.compatibility import (
        WILDCARD_QUEUE_MAX_SAFE_SEED as WILDCARD_QUEUE_MAX_SAFE_SEED,
        WILDCARD_RESERVED_NEXT_SEED_INPUT as WILDCARD_RESERVED_NEXT_SEED_INPUT,
        _consume_reserved_wildcard_next_seed as _consume_reserved_wildcard_next_seed,
    )
    from .easyuse_anima.workflow import _get_workflow_node as _get_workflow_node
    from .easyuse_anima.prompt.correction import (
        _prompt_translation_change_key as _prompt_translation_change_key,
        _split_tag_text as _split_tag_text,
        _translate_prompt_text as _translate_prompt_text,
    )
    from .easyuse_anima.prompt.fields import (
        # B-10b10 retires the two prompt-default root aliases.
        # Canonical prompt consumers import their immutable defaults directly.
        _HASH_COMMENT_RE as _HASH_COMMENT_RE,
        _INLINE_SPACE_RE as _INLINE_SPACE_RE,
        _WEIGHTED_TOKEN_RE as _WEIGHTED_TOKEN_RE,
        _correct_builder_prompt as _correct_builder_prompt,
        _filter_metadata_prompt as _filter_metadata_prompt,
        _join_prompt_tokens as _join_prompt_tokens,
        _metadata_filter_key as _metadata_filter_key,
        _metadata_filter_keys as _metadata_filter_keys,
        _prompt_tokens as _prompt_tokens,
    )
    from .easyuse_anima.prompt.data import (
        # B-10b12 retires nine unsupported prompt-data root aliases.
        # Canonical schema, tuple, and helper consumers import their owner directly.
        # Socket tooltip/name/type tuples stay canonical.
        # Schema and version values stay canonical.
        # Input-default resolution stays canonical.
        # Nested/output fallback stays canonical.
        # Dict output mutation stays canonical.
        # Retained type and runtime-resolver helpers stay root seams.
        # Mapped prompt-data adapters stay unchanged.
        PROMPT_DATA_TYPE as PROMPT_DATA_TYPE,
        _advanced_outputs_from_prompt_data as _advanced_outputs_from_prompt_data,
        _apply_prompt_data_overrides as _apply_prompt_data_overrides,
        _copy_prompt_data_for_update as _copy_prompt_data_for_update,
        _normalize_prompt_data as _normalize_prompt_data,
        _prompt_data_json_safe as _prompt_data_json_safe,
        _prompt_data_parameter_snapshot as _prompt_data_parameter_snapshot,
    )
    from .easyuse_anima.prompt.advanced import (
        # B-10b16: nine unsupported Advanced contract constants are canonical-only.
        # B-10b16: field workflow-property metadata remains canonical-only.
        # B-10b16: field labels and panes remain canonical-only.
        # B-10b16: field types and legacy Extend slot specs remain canonical-only.
        # B-10b16: Advanced return names/types remain canonical-only.
        # B-10b16: wildcard seed-control aliases remain canonical-only.
        # B-10b16: legacy fixed wildcard modes remain canonical-only.
        # B-10b16: canonical adapters consume these objects directly.
        # B-10b16: root runtime has no caller for the retired constants.
        _advanced_artist_field_prompt as _advanced_artist_field_prompt,
        _advanced_default_fields as _advanced_default_fields,
        _advanced_enabled_naia_panes as _advanced_enabled_naia_panes,
        _advanced_enabled_pane_fields as _advanced_enabled_pane_fields,
        _advanced_field_input_values as _advanced_field_input_values,
        _advanced_field_socket_name as _advanced_field_socket_name,
        _advanced_fields_json as _advanced_fields_json,
        # B-10b16: artist-field override expansion remains canonical-only.
        _advanced_has_enabled_naia as _advanced_has_enabled_naia,
        # B-10b16: pane-part assembly remains canonical-only.
        # B-10b16: prompt-data field serialization remains canonical-only.
        _advanced_prompt_with_artist_override as _advanced_prompt_with_artist_override,
        _advanced_uses_naia_resolution as _advanced_uses_naia_resolution,
        _apply_advanced_field_inputs as _apply_advanced_field_inputs,
        _as_advanced_height as _as_advanced_height,
        _build_advanced_prompt_data as _build_advanced_prompt_data,
        _build_advanced_prompts as _build_advanced_prompts,
        _clone_advanced_fields as _clone_advanced_fields,
        _correct_advanced_field_sequence as _correct_advanced_field_sequence,
        _expand_advanced_wildcard_fields as _expand_advanced_wildcard_fields,
        _normalize_advanced_fields as _normalize_advanced_fields,
        _normalize_prompt_studio_wildcard_seed_control as _normalize_prompt_studio_wildcard_seed_control,
        _set_naia_field_text as _set_naia_field_text,
        _translate_prompt_fields as _translate_prompt_fields,
    )
    from .easyuse_anima.prompt.regional import (
        # B-10b17: seven unsupported Regional contract constants are canonical-only.
        # B-10b17: config version and workflow properties remain canonical-only.
        # B-10b17: field types remain canonical-only.
        # B-10b17: bundle/data schemas remain canonical-only.
        # B-10b17: the Regional prompt-data socket type remains canonical-only.
        # B-10b17: canonical adapters consume these objects directly.
        # B-10b17: root runtime has no caller for the retired constants.
        _apply_regional_field_inputs as _apply_regional_field_inputs,
        _build_regional_outputs as _build_regional_outputs,
        _clone_regional_fields as _clone_regional_fields,
        _conditioning_set_values as _conditioning_set_values,
        # B-10b17: mask geometry normalization remains canonical-only.
        _normalize_mask_ids as _normalize_mask_ids,
        _normalize_regional_config as _normalize_regional_config,
        _normalize_regional_fields as _normalize_regional_fields,
        # B-10b17: Regional mask normalization remains canonical-only.
        _parse_json_object as _parse_json_object,
        _regional_config_json as _regional_config_json,
        # B-10b17: default config and fields remain canonical-only.
        # B-10b17: field prompt assembly remains canonical-only.
        # B-10b17: twelve unsupported Regional aliases were retired.
        _regional_fields_json as _regional_fields_json,
        _regional_mask_bounds_area as _regional_mask_bounds_area,
        _regional_payload_canvas as _regional_payload_canvas,
        _regional_union_mask_for_ids as _regional_union_mask_for_ids,
    )
    from .easyuse_anima.prompt.conditioning import (
        ANIMA_MOD_GUIDANCE_DEFAULT_PROFILE as ANIMA_MOD_GUIDANCE_DEFAULT_PROFILE,
        ANIMA_MOD_GUIDANCE_MODES as ANIMA_MOD_GUIDANCE_MODES,
        # B-10b15: disabled/enabled mode constants remain canonical-only.
        # B-10b15: profile choices remain canonical-only.
        ANIMA_MOD_GUIDANCE_MODE_FROM_PROMPT_DATA as ANIMA_MOD_GUIDANCE_MODE_FROM_PROMPT_DATA,
        # B-10b15: the warning-once state remains canonical-only.
        ANIMA_MOD_GUIDANCE_PROFILE_OFF as ANIMA_MOD_GUIDANCE_PROFILE_OFF,
        # B-10b15: warning dispatch remains canonical-only.
        _apply_spectrum_anima_mod_guidance as _apply_spectrum_anima_mod_guidance,
        _find_spectrum_anima_mod_guidance_class as _find_spectrum_anima_mod_guidance_class,
        _normalize_anima_mod_guidance_profile as _normalize_anima_mod_guidance_profile,
        _resolve_anima_mod_guidance_enabled as _resolve_anima_mod_guidance_enabled,
        # B-10b15: five unsupported conditioning aliases were retired.
    )
    from .easyuse_anima.prompt.artist_mix import (
        ARTIST_MIX_DEFAULT_CLUSTER_COUNT as ARTIST_MIX_DEFAULT_CLUSTER_COUNT,
        ARTIST_MIX_DEFAULT_DOMINANT_ISOLATION as ARTIST_MIX_DEFAULT_DOMINANT_ISOLATION,
        ARTIST_MIX_DEFAULT_DOMINANT_THRESHOLD as ARTIST_MIX_DEFAULT_DOMINANT_THRESHOLD,
        ARTIST_MIX_DEFAULT_EXACT_TOP_K as ARTIST_MIX_DEFAULT_EXACT_TOP_K,
        ARTIST_MIX_DEFAULT_RMS_SCALE_CAP as ARTIST_MIX_DEFAULT_RMS_SCALE_CAP,
        ARTIST_MIX_DEFAULT_START_PERCENT as ARTIST_MIX_DEFAULT_START_PERCENT,
        ARTIST_MIX_DEFAULT_STRENGTH_SCALE as ARTIST_MIX_DEFAULT_STRENGTH_SCALE,
        ARTIST_MIX_DEFAULT_STYLE_GAIN as ARTIST_MIX_DEFAULT_STYLE_GAIN,
        ARTIST_MIX_INPUT_MODES as ARTIST_MIX_INPUT_MODES,
        ARTIST_MIX_MODE_FROM_PROMPT_DATA as ARTIST_MIX_MODE_FROM_PROMPT_DATA,
        # B-10b19 retired root alias: ARTIST_MIX_CONTROL_KEY.
        # B-10b19 retired root alias: ARTIST_MIX_EXACT_KEY.
        # B-10b19 retired root alias: ARTIST_MIX_MODES.
        # B-10b19 retired root alias: ARTIST_MIX_MODE_AVERAGE.
        # B-10b19 retired root alias: ARTIST_MIX_MODE_AVERAGE_LATE_EXACT.
        # B-10b19 retired root alias: ARTIST_MIX_MODE_CLUSTERED.
        # B-10b19 retired root alias: ARTIST_MIX_MODE_COMPOSITE_EXACT.
        # B-10b19 retired root alias: ARTIST_MIX_MODE_DELTA_RMS.
        # B-10b19 retired root alias: ARTIST_MIX_MODE_DESCRIPTIONS.
        # B-10b19 retired root alias: ARTIST_MIX_MODE_EXACT.
        # B-10b19 retired root alias: ARTIST_MIX_MODE_HYBRID.
        # B-10b19 retired root alias: ARTIST_MIX_MODE_LATE_EXACT.
        # B-10b19 retired root alias: ARTIST_MIX_MODE_OFF.
        # B-10b19 retired root alias: ARTIST_MIX_MODE_PROMPT.
        # B-10b19 retired root alias: ARTIST_MIX_MODE_SCHEDULED_AVERAGE.
        # B-10b19 retired root alias: ARTIST_MIX_SCHEDULE_KEY.
        # B-10b19 retired root alias: ARTIST_MIX_STUDIO_MODES.
        # B-10b19 retired root alias: ARTIST_TAG_POSITION_BACK.
        # B-10b19 retired root alias: ARTIST_TAG_POSITION_CORRECT.
        # B-10b19 retired root alias: ARTIST_TAG_POSITION_FRONT.
        # B-10b19 retired root alias: ARTIST_TAG_POSITION_MODES.
        # B-10b20 retired root alias: _artist_conditioning_feature.
        # B-10b20 retired root alias: _artist_delta_rms_from_encoded.
        # B-10b18: artist group-token parsing remains canonical-only.
        _artist_mix_inline_prompt as _artist_mix_inline_prompt,
        _artist_mix_mode_tooltip as _artist_mix_mode_tooltip,
        # B-10b18: parsed prompt tags remain canonical-only.
        _artist_prompt_with_position as _artist_prompt_with_position,
        _artist_tags_from_prompt as _artist_tags_from_prompt,
        # B-10b18: prompt-data artist variants remain canonical-only.
        _blend_conditionings as _blend_conditionings,
        _bounded_artist_mix_float as _bounded_artist_mix_float,
        _bounded_artist_mix_int as _bounded_artist_mix_int,
        # B-10b18: parsed item coalescing remains canonical-only.
        # B-10b20 retired root alias: _conditionings_with_range.
        # B-10b20 retired root alias: _conditionings_with_strength.
        # B-10b20 retired root alias: _conditionings_with_values.
        # B-10b20 retired root alias: _copy_conditioning_metadata.
        # B-10b20 retired root alias: _encode_artist_average.
        # B-10b20 retired root alias: _encode_artist_average_late_exact.
        _encode_artist_clustered as _encode_artist_clustered,
        # B-10b20 retired root alias: _encode_artist_composite_exact.
        _encode_artist_delta_rms as _encode_artist_delta_rms,
        # B-10b20 retired root alias: _encode_artist_exact.
        # B-10b20 retired root alias: _encode_artist_hybrid.
        # B-10b20 retired root alias: _encode_artist_scheduled_average.
        _encode_prompt_data_positive_conditioning as _encode_prompt_data_positive_conditioning,
        # B-10b20 retired root alias: _encoded_artist_conditionings.
        # B-10b20 retired root alias: _equal_artist_weights.
        # B-10b20 retired root alias: _fallback_artist_average_or_exact.
        # B-10b20 retired root alias: _greedy_cluster_encoded_artists.
        # B-10b20 retired root alias: _interpolate_artist_weights.
        _join_artist_mix_source_prompts as _join_artist_mix_source_prompts,
        # B-10b20 retired root alias: _mark_artist_mix_conditioning.
        _normalize_artist_mix_mode as _normalize_artist_mix_mode,
        _normalize_artist_tag_position as _normalize_artist_tag_position,
        # B-10b20 retired root alias: _normalize_weight_values.
        # B-10b20 retired root alias: _normalized_artist_weights.
        # B-10b20 retired root alias: _pad_conditioning_tensor.
        # B-10b18: Artist Mix entry parsing remains canonical-only.
        # B-10b18: Artist Mix group parsing remains canonical-only.
        _parse_artist_mix_items as _parse_artist_mix_items,
        # B-10b18: prompt-data artist base prompt remains canonical-only.
        # B-10b18: prompt-data Artist Mix config remains canonical-only.
        # B-10b18: prompt-data positive fields remain canonical-only.
        # B-10b18: Artist Mix block splitting remains canonical-only.
        # B-10b18: Artist Mix item splitting remains canonical-only.
    )
    from .easyuse_anima.nodes.prompt_data_nodes import (
        EasyUseAnimaArtistMixConditioning as EasyUseAnimaArtistMixConditioning,
        EasyUseAnimaPromptDataConditioning as EasyUseAnimaPromptDataConditioning,
        EasyUseAnimaPromptDataUnpack as EasyUseAnimaPromptDataUnpack,
    )
    from .easyuse_anima.nodes.input_types import (
        _ANY_TYPE as _ANY_TYPE,
        _AnyType as _AnyType,
        _FlexibleOptionalInputType as _FlexibleOptionalInputType,
    )
    from .easyuse_anima.nodes.prompt_advanced_nodes import (
        EasyUseAnimaPromptStudioAdvanced as EasyUseAnimaPromptStudioAdvanced,
        EasyUseAnimaPromptStudioAdvancedV2 as EasyUseAnimaPromptStudioAdvancedV2,
        # B-10b11 retires the unmapped legacy Extend root alias.
    )
    from .easyuse_anima.nodes.aio_nodes import (
        EASY_USE_ANIMA_INPUT_TYPE as EASY_USE_ANIMA_INPUT_TYPE,
        EasyUseAnimaAIOGenerator as EasyUseAnimaAIOGenerator,
        EasyUseAnimaInput as EasyUseAnimaInput,
        _aio_generation_settings_json as _aio_generation_settings_json,
        _aio_input_settings_json as _aio_input_settings_json,
    )
    from .easyuse_anima.image.geometry import (
        _align_down as _align_down,
        _align_nearest as _align_nearest,
        _image_tensor_size as _image_tensor_size,
        # B-10b5 retires three root image-geometry aliases.
        # Canonical image/scaling/detailer consumers import geometry directly.
        # _align_nearest/_align_down stay for root residual runtime.
    )
    # B-10b2 deliberately omits the retired root Detailer hook alias.
    # Canonical image and Impact Detailer adapters import the owner directly.
    # The root module no longer re-exports this unsupported private helper.
    from .easyuse_anima.image.sam3 import (
        # B-10b9 retires seven root SAM3 helper aliases.
        _context_value as _context_value,
        # Canonical SAM3 and Impact adapters import the owner directly.
        # Prompt formatting and detection behavior stay canonical.
        # Mask and empty-SEGS helpers stay canonical.
        # Optional-node resolver behavior stays canonical.
        # Context/state helpers remain root runtime seams.
        # SAM3 class aliases stay unchanged.
        _sam3_context as _sam3_context,
        _segs_has_items as _segs_has_items,
    )
    from .easyuse_anima.image.scaling import (
        IMAGE_SCALE_MULTIPLES as IMAGE_SCALE_MULTIPLES,
        IMAGE_UPSCALE_METHODS as IMAGE_UPSCALE_METHODS,
        # B-10b6 retires four root image-scaling helper aliases.
        # The canonical image adapter imports scaling helpers directly.
        # Constants stay for the AiO generation-normalization resolver.
        # The public mapped node class remains a root re-export.
    )
    from .easyuse_anima.infrastructure.comfy.capabilities import (
        _comfy_sampler_names as _comfy_sampler_names,
        _comfy_scheduler_names as _comfy_scheduler_names,
        # B-10b4 omits the retired root _impact_core_module alias.
        _impact_scheduler_names as _impact_scheduler_names,
    )
    from .easyuse_anima.infrastructure.comfy.invocation import (
        _call_with_supported_kwargs as _call_with_supported_kwargs,
        _common_upscale_image as _common_upscale_image,
        _node_output_tuple as _node_output_tuple,
    )
    from .easyuse_anima.infrastructure.comfy.resources import (
        # B-10b1 deliberately omits the retired root _comfy_checkpoint_names alias.
        _comfy_clip_loader_types as _adapter_comfy_clip_loader_types,
        _comfy_diffusion_model_names as _adapter_comfy_diffusion_model_names,
        _comfy_text_encoder_names as _adapter_comfy_text_encoder_names,
        _comfy_vae_names as _adapter_comfy_vae_names,
        _folder_path_names as _folder_path_names,
    )
    from .easyuse_anima.nodes.image_nodes import (
        EasyUseAnimaDetailerAlignHook as EasyUseAnimaDetailerAlignHook,
        EasyUseAnimaImageScaleByMultiple as EasyUseAnimaImageScaleByMultiple,
    )
    from .easyuse_anima.nodes.sam3_nodes import (
        EasyUseAnimaSAM3Context as EasyUseAnimaSAM3Context,
        EasyUseAnimaSAM3Detailer as EasyUseAnimaSAM3Detailer,
    )
    from .easyuse_anima.nodes.prompt_nodes import (
        EasyUseAnimaPromptBuilder as EasyUseAnimaPromptBuilder,
        EasyUseAnimaPromptCorrector as EasyUseAnimaPromptCorrector,
        EasyUseAnimaPromptCorrectorSimple as EasyUseAnimaPromptCorrectorSimple,
        EasyUseAnimaPromptStudio as EasyUseAnimaPromptStudio,
    )
    from .easyuse_anima.nodes.regional_nodes import (
        EasyUseAnimaPromptStudioRegional as EasyUseAnimaPromptStudioRegional,
        EasyUseAnimaRegionalConditioning as EasyUseAnimaRegionalConditioning,
    )
    from .easyuse_anima.naia.client import (
        # B-10b13 retires 13 unsupported NAIA client root aliases.
        # Canonical client and node-adapter consumers import their owner directly.
        # Host and port defaults stay canonical.
        # Local-host and remote opt-in policy stays canonical.
        # Request timeout values stay canonical.
        # Resolution bounds and 1MP fitting stay canonical.
        # Preprocessing keys and choices stay canonical.
        # URL construction and host validation stay canonical.
        # Prompt cleanup stays canonical.
        # Repository tests use the canonical owner for retired names.
        # Retained runtime values stay direct root seams.
        # Response parsing and HTTP posting remain bound at call time.
        # Mapped NAIA node identity and workflows stay unchanged.
        LATENT_ALIGN as LATENT_ALIGN,
        _parse_random_response as _parse_random_response,
        _post_random as _post_random,
    )
    from .easyuse_anima.naia.resolution import (
        # B-10b14 retires 16 unsupported NAIA resolution root aliases.
        # Canonical resolution and adapter consumers import their owner directly.
        # Bucket data and insertion order stay canonical.
        # Custom, NAIA, and default labels stay canonical.
        # Scale and bucket mode values stay canonical.
        # Bucket-fit selection stays canonical.
        # Resolution scale and max-long-edge policy stays canonical.
        # Resolution-mode normalization stays canonical.
        # Bucket-name normalization stays canonical.
        # Scaled-resolution calculation stays canonical.
        # 32-pixel snapping stays canonical.
        # Sorted option generation stays canonical.
        # Repository tests use the canonical owner for retired names.
        # Retained labels and selection helpers stay root seams.
        # Runtime-resolved final NAIA resolution stays a root seam.
        # Mapped node identities and workflows stay unchanged.
        _advanced_resolution_from_selection as _advanced_resolution_from_selection,
        _normalize_resolution_bucket as _normalize_resolution_bucket,
        _ratio_label as _ratio_label,
        _resolution_label as _resolution_label,
        _resolve_naia_resolution as _resolve_naia_resolution,
    )
    from .easyuse_anima.nodes.naia_nodes import (
        EasyUseAnimaNAIARandomPrompt as EasyUseAnimaNAIARandomPrompt,
    )
    from .easyuse_anima.nodes.wildcard_nodes import (
        EasyUseAnimaWildcard as EasyUseAnimaWildcard,
        # B-10b8 retires the test-only root wildcard-note alias.
    )
    from .easyuse_anima.lora.metadata import (
        _apply_lora_syntax_format as _apply_lora_syntax_format,
        _dedupe_text_values as _dedupe_text_values,
        _fallback_lora_path as _fallback_lora_path,
        _get_lora_info as _get_lora_info,
        _get_lora_manager_trigger_words as _get_lora_manager_trigger_words,
        _load_lora_manager_metadata as _load_lora_manager_metadata,
        _lora_combo_values as _lora_combo_values,
        _lora_manager_trigger_words_from_metadata as _lora_manager_trigger_words_from_metadata,
        _lora_model_exists as _lora_model_exists,
        _lora_stack_name as _lora_stack_name,
        _metadata_json_paths_for_lora as _metadata_json_paths_for_lora,
        _missing_lora_display_name as _missing_lora_display_name,
        _raise_missing_loras as _raise_missing_loras,
        _trigger_words_from_value as _trigger_words_from_value,
    )
    from .easyuse_anima.lora.preset import (
        _correct_style_prompt as _correct_style_prompt,
        _format_strength as _format_strength,
        _get_loras_list as _get_loras_list,
        _load_profile_data as _load_profile_data,
        _profile_key as _profile_key,
        _select_profile_values as _select_profile_values,
        _wrap_profile_index as _wrap_profile_index,
    )
    from .easyuse_anima.nodes.lora_nodes import (
        EasyUseAnimaLoraPreset as EasyUseAnimaLoraPreset,
    )
    from .anima_prompt import correct_prompt, load_knowledge_base
    from .anima_prompt.parser import parse_prompt
    from .settings import (
        resolve_metadata_filter_words,
        resolve_naia_settings,
        resolve_prompt_translation_settings,
    )
    from .easyuse_anima.translation.markers import (
        has_prompt_translation_markers,
    )
    from .easyuse_anima.translation.service import (
        translate_prompt_markers,
    )
    from .wildcard_engine import (
        MAX_SEED,
        PUBLIC_MAX_SEED,
        PROMPT_STUDIO_WILDCARD_MODE_LABELS,
        SEED_CONTROL_DECREMENT,
        SEED_CONTROL_FIXED,
        SEED_CONTROL_INCREMENT,
        SEED_CONTROL_MODES,
        SEED_CONTROL_RANDOMIZE,
        WILDCARD_MODE_FIXED,
        WILDCARD_MODE_POPULATE,
        WILDCARD_MODE_SEQUENTIAL,
        expand_wildcard_texts,
        expand_wildcards,
        has_wildcard_syntax,
        next_seed,
        normalize_seed,
        normalize_prompt_studio_wildcard_mode,
        normalize_wildcard_mode,
        wildcard_sources_signature,
    )
except ImportError:  # allows simple local import tests outside ComfyUI's package loader
    from easyuse_anima.aio.first_pass_cache import (
        AIO_FIRST_PASS_CACHE_MAX_ENTRIES as AIO_FIRST_PASS_CACHE_MAX_ENTRIES,
        _AIO_FIRST_PASS_CACHE as _AIO_FIRST_PASS_CACHE,
        _AIO_FIRST_PASS_CACHE_ORDER as _AIO_FIRST_PASS_CACHE_ORDER,
        _aio_first_pass_cache_key as _aio_first_pass_cache_key,
        # B-10b7 retires the test-only root cache-clear function alias.
        _clone_aio_cache_value as _clone_aio_cache_value,
        _get_aio_first_pass_cache as _get_aio_first_pass_cache,
        _put_aio_first_pass_cache as _put_aio_first_pass_cache,
    )
    from easyuse_anima.aio.legacy_generation import (
        _run_aio_detailer_stage as _run_aio_detailer_stage,
        _run_aio_detailer_target as _run_aio_detailer_target,
        _run_aio_highres_stage as _run_aio_highres_stage,
        _run_aio_legacy_generation as _run_aio_legacy_generation,
        _run_aio_resshift_upscale_stage as _run_aio_resshift_upscale_stage,
        _run_aio_upscale_stage as _run_aio_upscale_stage,
        _run_aio_usdu_upscale_stage as _run_aio_usdu_upscale_stage,
    )
    from easyuse_anima.aio.generation_normalization import (
        _AIO_DETAILER_CUSTOM_RE as _AIO_DETAILER_CUSTOM_RE,
        _AIO_DETAILER_RESERVED_KEYS as _AIO_DETAILER_RESERVED_KEYS,
        _aio_detailer_has_enabled_targets as _aio_detailer_has_enabled_targets,
        _aio_detailer_target_defaults as _aio_detailer_target_defaults,
        _aio_detailer_target_order as _aio_detailer_target_order,
        _is_aio_detailer_target_name as _is_aio_detailer_target_name,
        _merge_versioned_settings as _merge_versioned_settings,
        _normalize_aio_dit_corrections_settings as _normalize_aio_dit_corrections_settings,
        _normalize_aio_generation_settings as _normalize_aio_generation_settings,
        _normalize_aio_seed as _normalize_aio_seed,
        _normalize_aio_spectrum_settings as _normalize_aio_spectrum_settings,
    )
    from easyuse_anima.aio.generation_defaults import (
        AIO_FINAL_FIT_MODES as AIO_FINAL_FIT_MODES,
        AIO_FINAL_UPSCALE_BACKENDS as AIO_FINAL_UPSCALE_BACKENDS,
        AIO_GENERATION_DEFAULT_SETTINGS as AIO_GENERATION_DEFAULT_SETTINGS,
        AIO_GENERATION_SETTINGS_SCHEMA as AIO_GENERATION_SETTINGS_SCHEMA,
        AIO_GENERATION_SETTINGS_VERSION as AIO_GENERATION_SETTINGS_VERSION,
        AIO_RESHIFT_DTYPES as AIO_RESHIFT_DTYPES,
        AIO_RESHIFT_SCALES as AIO_RESHIFT_SCALES,
        AIO_SPECIAL_SEEDS as AIO_SPECIAL_SEEDS,
        AIO_SPECIAL_SEED_DECREMENT as AIO_SPECIAL_SEED_DECREMENT,
        AIO_SPECIAL_SEED_INCREMENT as AIO_SPECIAL_SEED_INCREMENT,
        AIO_SPECIAL_SEED_RANDOM as AIO_SPECIAL_SEED_RANDOM,
        AIO_USDU_MODE_TYPES as AIO_USDU_MODE_TYPES,
        AIO_USDU_PROMPT_FULL as AIO_USDU_PROMPT_FULL,
        AIO_USDU_PROMPT_MODES as AIO_USDU_PROMPT_MODES,
        AIO_USDU_PROMPT_NO_GENERAL as AIO_USDU_PROMPT_NO_GENERAL,
        AIO_USDU_SEAM_FIX_MODES as AIO_USDU_SEAM_FIX_MODES,
    )
    from easyuse_anima.aio.generation_settings import (
        round_trip_aio_generation_settings as _round_trip_aio_generation_settings,
    )
    from easyuse_anima.aio.input_defaults import (
        AIO_INPUT_DEFAULT_SETTINGS as AIO_INPUT_DEFAULT_SETTINGS,
        ANIMA_CLIP_DEVICES as ANIMA_CLIP_DEVICES,
        ANIMA_CLIP_TYPES as ANIMA_CLIP_TYPES,
        ANIMA_DEFAULT_CLIP_CANDIDATES as ANIMA_DEFAULT_CLIP_CANDIDATES,
        ANIMA_DEFAULT_DIFFUSION_MODEL_CANDIDATES as ANIMA_DEFAULT_DIFFUSION_MODEL_CANDIDATES,
        ANIMA_DEFAULT_VAE_CANDIDATES as ANIMA_DEFAULT_VAE_CANDIDATES,
        ANIMA_UNET_WEIGHT_DTYPES as ANIMA_UNET_WEIGHT_DTYPES,
        EASY_USE_ANIMA_INPUT_SCHEMA as EASY_USE_ANIMA_INPUT_SCHEMA,
        EASY_USE_ANIMA_INPUT_SETTINGS_VERSION as EASY_USE_ANIMA_INPUT_SETTINGS_VERSION,
    )
    from easyuse_anima.aio.input_context import (
        _easy_use_anima_input_signature as _easy_use_anima_input_signature,
        _require_easy_use_anima_input as _require_easy_use_anima_input,
    )
    from easyuse_anima.aio.usdu import (
        _aio_usdu_auto_tile_dimension as _aio_usdu_auto_tile_dimension,
        _aio_usdu_tile_plan as _aio_usdu_tile_plan,
    )
    from easyuse_anima.aio.postprocess import (
        _apply_aio_final_fit as _apply_aio_final_fit,
        _aio_final_fit_size as _aio_final_fit_size,
        _resize_image_to_size_if_needed as _resize_image_to_size_if_needed,
        _run_aio_postprocess_stage as _run_aio_postprocess_stage,
    )
    from easyuse_anima.aio.conditioning import (
        _aio_prompt_data_fields_for_usdu as _aio_prompt_data_fields_for_usdu,
        _aio_usdu_conditioning as _aio_usdu_conditioning,
        _aio_usdu_prompt_without_general as _aio_usdu_prompt_without_general,
    )
    from easyuse_anima.aio.model_preparation import (
        _aio_lora_stack_signature as _aio_lora_stack_signature,
        _apply_aio_anima_dave_patch as _apply_aio_anima_dave_patch,
        _apply_aio_kj_model_patches as _apply_aio_kj_model_patches,
        _apply_aio_lora_stack as _apply_aio_lora_stack,
        _apply_aio_model_patches as _apply_aio_model_patches,
        _apply_aio_safe_pag_patch as _apply_aio_safe_pag_patch,
        _apply_aio_spectrum_correction_patch_for_comfy_sampler as _apply_aio_spectrum_correction_patch_for_comfy_sampler,
        _apply_aio_spectrum_forecast_patch_for_comfy_sampler as _apply_aio_spectrum_forecast_patch_for_comfy_sampler,
        _apply_aio_spectrum_model_patches_for_comfy_sampler as _apply_aio_spectrum_model_patches_for_comfy_sampler,
        _cleanup_aio_ephemeral_model as _cleanup_aio_ephemeral_model,
        _normalize_aio_lora_stack as _normalize_aio_lora_stack,
        _patch_model_sampling_aura_flow as _patch_model_sampling_aura_flow,
    )
    from easyuse_anima.aio.sampling import (
        _aio_highres_effective_backend as _aio_highres_effective_backend,
        _aio_stage_sampler_settings as _aio_stage_sampler_settings,
        _decode_latent_with_comfy as _decode_latent_with_comfy,
        _encode_image_with_comfy_vae as _encode_image_with_comfy_vae,
        _generate_empty_latent_with_comfy as _generate_empty_latent_with_comfy,
        _new_aio_random_seed as _new_aio_random_seed,
        _resolve_aio_runtime_seed as _resolve_aio_runtime_seed,
        _sample_latent_with_aio_backend as _sample_latent_with_aio_backend,
        _sample_latent_with_comfy as _sample_latent_with_comfy,
        _sample_latent_with_spectrum_mod_guidance_advanced as _sample_latent_with_spectrum_mod_guidance_advanced,
        _sample_latent_with_spectrum_spd as _sample_latent_with_spectrum_spd,
    )
    from easyuse_anima.aio.preview import (
        AIO_PREVIEW_CACHE_FORMAT as AIO_PREVIEW_CACHE_FORMAT,
        AIO_PREVIEW_CACHE_QUALITY as AIO_PREVIEW_CACHE_QUALITY,
        AIO_PREVIEW_EVENT as AIO_PREVIEW_EVENT,
        AIO_PREVIEW_STAGE_LABELS as AIO_PREVIEW_STAGE_LABELS,
        _aio_preview_base_directory as _aio_preview_base_directory,
        _aio_preview_file_size_bytes as _aio_preview_file_size_bytes,
        _save_aio_temp_preview_image as _save_aio_temp_preview_image,
        _send_aio_preview_event as _send_aio_preview_event,
        _tag_aio_preview_images as _tag_aio_preview_images,
    )
    from easyuse_anima.aio.output import (
        _aio_image_saver_additional_hashes as _aio_image_saver_additional_hashes,
        _aio_image_saver_civitai_hash_fetcher_entries as _aio_image_saver_civitai_hash_fetcher_entries,
        _aio_lora_metadata_name as _aio_lora_metadata_name,
        _aio_prompt_with_lora_metadata as _aio_prompt_with_lora_metadata,
        _aio_save_filename_prefix as _aio_save_filename_prefix,
        _save_image_with_comfy as _save_image_with_comfy,
        _save_image_with_image_saver as _save_image_with_image_saver,
    )
    from easyuse_anima.aio.output_settings import (
        _normalize_aio_civitai_hash_fetchers as _normalize_aio_civitai_hash_fetchers,
        _normalize_aio_hash_bundles as _normalize_aio_hash_bundles,
    )
    from easyuse_anima.aio.resources import (
        _comfy_clip_loader_types as _comfy_clip_loader_types,
        _comfy_diffusion_model_names as _comfy_diffusion_model_names,
        _comfy_text_encoder_names as _comfy_text_encoder_names,
        _comfy_vae_names as _comfy_vae_names,
        _load_aio_resources_from_input_context as _load_aio_resources_from_input_context,
        _load_aio_sam3_context as _load_aio_sam3_context,
        _load_checkpoint_with_comfy as _load_checkpoint_with_comfy,
        _load_clip_with_comfy as _load_clip_with_comfy,
        _load_diffusion_model_with_comfy as _load_diffusion_model_with_comfy,
        _load_upscale_model_with_comfy as _load_upscale_model_with_comfy,
        _load_vae_with_comfy as _load_vae_with_comfy,
        _normalize_aio_input_settings as _normalize_aio_input_settings,
        _preferred_checkpoint_default as _preferred_checkpoint_default,
        _preferred_clip_type_default as _preferred_clip_type_default,
        _preferred_name_default as _preferred_name_default,
    )
    from easyuse_anima.common.serialization import (
        _json_clone as _json_clone,
        _json_object as _json_object,
        _stable_change_key as _stable_change_key,
    )
    from easyuse_anima.common.values import (
        _as_bool as _as_bool,
        _as_float as _as_float,
        _as_int as _as_int,
        _choice as _choice,
        _single_value as _single_value,
    )
    from easyuse_anima.seed.compatibility import (
        WILDCARD_QUEUE_MAX_SAFE_SEED as WILDCARD_QUEUE_MAX_SAFE_SEED,
        WILDCARD_RESERVED_NEXT_SEED_INPUT as WILDCARD_RESERVED_NEXT_SEED_INPUT,
        _consume_reserved_wildcard_next_seed as _consume_reserved_wildcard_next_seed,
    )
    from easyuse_anima.workflow import _get_workflow_node as _get_workflow_node
    from easyuse_anima.prompt.correction import (
        _prompt_translation_change_key as _prompt_translation_change_key,
        _split_tag_text as _split_tag_text,
        _translate_prompt_text as _translate_prompt_text,
    )
    from easyuse_anima.prompt.fields import (
        # B-10b10 retires the two prompt-default root aliases.
        # Canonical prompt consumers import their immutable defaults directly.
        _HASH_COMMENT_RE as _HASH_COMMENT_RE,
        _INLINE_SPACE_RE as _INLINE_SPACE_RE,
        _WEIGHTED_TOKEN_RE as _WEIGHTED_TOKEN_RE,
        _correct_builder_prompt as _correct_builder_prompt,
        _filter_metadata_prompt as _filter_metadata_prompt,
        _join_prompt_tokens as _join_prompt_tokens,
        _metadata_filter_key as _metadata_filter_key,
        _metadata_filter_keys as _metadata_filter_keys,
        _prompt_tokens as _prompt_tokens,
    )
    from easyuse_anima.prompt.data import (
        # B-10b12 retires nine unsupported prompt-data root aliases.
        # Canonical schema, tuple, and helper consumers import their owner directly.
        # Socket tooltip/name/type tuples stay canonical.
        # Schema and version values stay canonical.
        # Input-default resolution stays canonical.
        # Nested/output fallback stays canonical.
        # Dict output mutation stays canonical.
        # Retained type and runtime-resolver helpers stay root seams.
        # Mapped prompt-data adapters stay unchanged.
        PROMPT_DATA_TYPE as PROMPT_DATA_TYPE,
        _advanced_outputs_from_prompt_data as _advanced_outputs_from_prompt_data,
        _apply_prompt_data_overrides as _apply_prompt_data_overrides,
        _copy_prompt_data_for_update as _copy_prompt_data_for_update,
        _normalize_prompt_data as _normalize_prompt_data,
        _prompt_data_json_safe as _prompt_data_json_safe,
        _prompt_data_parameter_snapshot as _prompt_data_parameter_snapshot,
    )
    from easyuse_anima.prompt.advanced import (
        # B-10b16: nine unsupported Advanced contract constants are canonical-only.
        # B-10b16: field workflow-property metadata remains canonical-only.
        # B-10b16: field labels and panes remain canonical-only.
        # B-10b16: field types and legacy Extend slot specs remain canonical-only.
        # B-10b16: Advanced return names/types remain canonical-only.
        # B-10b16: wildcard seed-control aliases remain canonical-only.
        # B-10b16: legacy fixed wildcard modes remain canonical-only.
        # B-10b16: canonical adapters consume these objects directly.
        # B-10b16: root runtime has no caller for the retired constants.
        _advanced_artist_field_prompt as _advanced_artist_field_prompt,
        _advanced_default_fields as _advanced_default_fields,
        _advanced_enabled_naia_panes as _advanced_enabled_naia_panes,
        _advanced_enabled_pane_fields as _advanced_enabled_pane_fields,
        _advanced_field_input_values as _advanced_field_input_values,
        _advanced_field_socket_name as _advanced_field_socket_name,
        _advanced_fields_json as _advanced_fields_json,
        # B-10b16: artist-field override expansion remains canonical-only.
        _advanced_has_enabled_naia as _advanced_has_enabled_naia,
        # B-10b16: pane-part assembly remains canonical-only.
        # B-10b16: prompt-data field serialization remains canonical-only.
        _advanced_prompt_with_artist_override as _advanced_prompt_with_artist_override,
        _advanced_uses_naia_resolution as _advanced_uses_naia_resolution,
        _apply_advanced_field_inputs as _apply_advanced_field_inputs,
        _as_advanced_height as _as_advanced_height,
        _build_advanced_prompt_data as _build_advanced_prompt_data,
        _build_advanced_prompts as _build_advanced_prompts,
        _clone_advanced_fields as _clone_advanced_fields,
        _correct_advanced_field_sequence as _correct_advanced_field_sequence,
        _expand_advanced_wildcard_fields as _expand_advanced_wildcard_fields,
        _normalize_advanced_fields as _normalize_advanced_fields,
        _normalize_prompt_studio_wildcard_seed_control as _normalize_prompt_studio_wildcard_seed_control,
        _set_naia_field_text as _set_naia_field_text,
        _translate_prompt_fields as _translate_prompt_fields,
    )
    from easyuse_anima.prompt.regional import (
        # B-10b17: seven unsupported Regional contract constants are canonical-only.
        # B-10b17: config version and workflow properties remain canonical-only.
        # B-10b17: field types remain canonical-only.
        # B-10b17: bundle/data schemas remain canonical-only.
        # B-10b17: the Regional prompt-data socket type remains canonical-only.
        # B-10b17: canonical adapters consume these objects directly.
        # B-10b17: root runtime has no caller for the retired constants.
        _apply_regional_field_inputs as _apply_regional_field_inputs,
        _build_regional_outputs as _build_regional_outputs,
        _clone_regional_fields as _clone_regional_fields,
        _conditioning_set_values as _conditioning_set_values,
        # B-10b17: mask geometry normalization remains canonical-only.
        _normalize_mask_ids as _normalize_mask_ids,
        _normalize_regional_config as _normalize_regional_config,
        _normalize_regional_fields as _normalize_regional_fields,
        # B-10b17: Regional mask normalization remains canonical-only.
        _parse_json_object as _parse_json_object,
        _regional_config_json as _regional_config_json,
        # B-10b17: default config and fields remain canonical-only.
        # B-10b17: field prompt assembly remains canonical-only.
        # B-10b17: twelve unsupported Regional aliases were retired.
        _regional_fields_json as _regional_fields_json,
        _regional_mask_bounds_area as _regional_mask_bounds_area,
        _regional_payload_canvas as _regional_payload_canvas,
        _regional_union_mask_for_ids as _regional_union_mask_for_ids,
    )
    from easyuse_anima.prompt.conditioning import (
        ANIMA_MOD_GUIDANCE_DEFAULT_PROFILE as ANIMA_MOD_GUIDANCE_DEFAULT_PROFILE,
        ANIMA_MOD_GUIDANCE_MODES as ANIMA_MOD_GUIDANCE_MODES,
        # B-10b15: disabled/enabled mode constants remain canonical-only.
        # B-10b15: profile choices remain canonical-only.
        ANIMA_MOD_GUIDANCE_MODE_FROM_PROMPT_DATA as ANIMA_MOD_GUIDANCE_MODE_FROM_PROMPT_DATA,
        # B-10b15: the warning-once state remains canonical-only.
        ANIMA_MOD_GUIDANCE_PROFILE_OFF as ANIMA_MOD_GUIDANCE_PROFILE_OFF,
        # B-10b15: warning dispatch remains canonical-only.
        _apply_spectrum_anima_mod_guidance as _apply_spectrum_anima_mod_guidance,
        _find_spectrum_anima_mod_guidance_class as _find_spectrum_anima_mod_guidance_class,
        _normalize_anima_mod_guidance_profile as _normalize_anima_mod_guidance_profile,
        _resolve_anima_mod_guidance_enabled as _resolve_anima_mod_guidance_enabled,
        # B-10b15: five unsupported conditioning aliases were retired.
    )
    from easyuse_anima.prompt.artist_mix import (
        ARTIST_MIX_DEFAULT_CLUSTER_COUNT as ARTIST_MIX_DEFAULT_CLUSTER_COUNT,
        ARTIST_MIX_DEFAULT_DOMINANT_ISOLATION as ARTIST_MIX_DEFAULT_DOMINANT_ISOLATION,
        ARTIST_MIX_DEFAULT_DOMINANT_THRESHOLD as ARTIST_MIX_DEFAULT_DOMINANT_THRESHOLD,
        ARTIST_MIX_DEFAULT_EXACT_TOP_K as ARTIST_MIX_DEFAULT_EXACT_TOP_K,
        ARTIST_MIX_DEFAULT_RMS_SCALE_CAP as ARTIST_MIX_DEFAULT_RMS_SCALE_CAP,
        ARTIST_MIX_DEFAULT_START_PERCENT as ARTIST_MIX_DEFAULT_START_PERCENT,
        ARTIST_MIX_DEFAULT_STRENGTH_SCALE as ARTIST_MIX_DEFAULT_STRENGTH_SCALE,
        ARTIST_MIX_DEFAULT_STYLE_GAIN as ARTIST_MIX_DEFAULT_STYLE_GAIN,
        ARTIST_MIX_INPUT_MODES as ARTIST_MIX_INPUT_MODES,
        ARTIST_MIX_MODE_FROM_PROMPT_DATA as ARTIST_MIX_MODE_FROM_PROMPT_DATA,
        # B-10b19 retired root alias: ARTIST_MIX_CONTROL_KEY.
        # B-10b19 retired root alias: ARTIST_MIX_EXACT_KEY.
        # B-10b19 retired root alias: ARTIST_MIX_MODES.
        # B-10b19 retired root alias: ARTIST_MIX_MODE_AVERAGE.
        # B-10b19 retired root alias: ARTIST_MIX_MODE_AVERAGE_LATE_EXACT.
        # B-10b19 retired root alias: ARTIST_MIX_MODE_CLUSTERED.
        # B-10b19 retired root alias: ARTIST_MIX_MODE_COMPOSITE_EXACT.
        # B-10b19 retired root alias: ARTIST_MIX_MODE_DELTA_RMS.
        # B-10b19 retired root alias: ARTIST_MIX_MODE_DESCRIPTIONS.
        # B-10b19 retired root alias: ARTIST_MIX_MODE_EXACT.
        # B-10b19 retired root alias: ARTIST_MIX_MODE_HYBRID.
        # B-10b19 retired root alias: ARTIST_MIX_MODE_LATE_EXACT.
        # B-10b19 retired root alias: ARTIST_MIX_MODE_OFF.
        # B-10b19 retired root alias: ARTIST_MIX_MODE_PROMPT.
        # B-10b19 retired root alias: ARTIST_MIX_MODE_SCHEDULED_AVERAGE.
        # B-10b19 retired root alias: ARTIST_MIX_SCHEDULE_KEY.
        # B-10b19 retired root alias: ARTIST_MIX_STUDIO_MODES.
        # B-10b19 retired root alias: ARTIST_TAG_POSITION_BACK.
        # B-10b19 retired root alias: ARTIST_TAG_POSITION_CORRECT.
        # B-10b19 retired root alias: ARTIST_TAG_POSITION_FRONT.
        # B-10b19 retired root alias: ARTIST_TAG_POSITION_MODES.
        # B-10b20 retired root alias: _artist_conditioning_feature.
        # B-10b20 retired root alias: _artist_delta_rms_from_encoded.
        # B-10b18: artist group-token parsing remains canonical-only.
        _artist_mix_inline_prompt as _artist_mix_inline_prompt,
        _artist_mix_mode_tooltip as _artist_mix_mode_tooltip,
        # B-10b18: parsed prompt tags remain canonical-only.
        _artist_prompt_with_position as _artist_prompt_with_position,
        _artist_tags_from_prompt as _artist_tags_from_prompt,
        # B-10b18: prompt-data artist variants remain canonical-only.
        _blend_conditionings as _blend_conditionings,
        _bounded_artist_mix_float as _bounded_artist_mix_float,
        _bounded_artist_mix_int as _bounded_artist_mix_int,
        # B-10b18: parsed item coalescing remains canonical-only.
        # B-10b20 retired root alias: _conditionings_with_range.
        # B-10b20 retired root alias: _conditionings_with_strength.
        # B-10b20 retired root alias: _conditionings_with_values.
        # B-10b20 retired root alias: _copy_conditioning_metadata.
        # B-10b20 retired root alias: _encode_artist_average.
        # B-10b20 retired root alias: _encode_artist_average_late_exact.
        _encode_artist_clustered as _encode_artist_clustered,
        # B-10b20 retired root alias: _encode_artist_composite_exact.
        _encode_artist_delta_rms as _encode_artist_delta_rms,
        # B-10b20 retired root alias: _encode_artist_exact.
        # B-10b20 retired root alias: _encode_artist_hybrid.
        # B-10b20 retired root alias: _encode_artist_scheduled_average.
        _encode_prompt_data_positive_conditioning as _encode_prompt_data_positive_conditioning,
        # B-10b20 retired root alias: _encoded_artist_conditionings.
        # B-10b20 retired root alias: _equal_artist_weights.
        # B-10b20 retired root alias: _fallback_artist_average_or_exact.
        # B-10b20 retired root alias: _greedy_cluster_encoded_artists.
        # B-10b20 retired root alias: _interpolate_artist_weights.
        _join_artist_mix_source_prompts as _join_artist_mix_source_prompts,
        # B-10b20 retired root alias: _mark_artist_mix_conditioning.
        _normalize_artist_mix_mode as _normalize_artist_mix_mode,
        _normalize_artist_tag_position as _normalize_artist_tag_position,
        # B-10b20 retired root alias: _normalize_weight_values.
        # B-10b20 retired root alias: _normalized_artist_weights.
        # B-10b20 retired root alias: _pad_conditioning_tensor.
        # B-10b18: Artist Mix entry parsing remains canonical-only.
        # B-10b18: Artist Mix group parsing remains canonical-only.
        _parse_artist_mix_items as _parse_artist_mix_items,
        # B-10b18: prompt-data artist base prompt remains canonical-only.
        # B-10b18: prompt-data Artist Mix config remains canonical-only.
        # B-10b18: prompt-data positive fields remain canonical-only.
        # B-10b18: Artist Mix block splitting remains canonical-only.
        # B-10b18: Artist Mix item splitting remains canonical-only.
    )
    from easyuse_anima.nodes.prompt_data_nodes import (
        EasyUseAnimaArtistMixConditioning as EasyUseAnimaArtistMixConditioning,
        EasyUseAnimaPromptDataConditioning as EasyUseAnimaPromptDataConditioning,
        EasyUseAnimaPromptDataUnpack as EasyUseAnimaPromptDataUnpack,
    )
    from easyuse_anima.nodes.input_types import (
        _ANY_TYPE as _ANY_TYPE,
        _AnyType as _AnyType,
        _FlexibleOptionalInputType as _FlexibleOptionalInputType,
    )
    from easyuse_anima.nodes.prompt_advanced_nodes import (
        EasyUseAnimaPromptStudioAdvanced as EasyUseAnimaPromptStudioAdvanced,
        EasyUseAnimaPromptStudioAdvancedV2 as EasyUseAnimaPromptStudioAdvancedV2,
        # B-10b11 retires the unmapped legacy Extend root alias.
    )
    from easyuse_anima.nodes.aio_nodes import (
        EASY_USE_ANIMA_INPUT_TYPE as EASY_USE_ANIMA_INPUT_TYPE,
        EasyUseAnimaAIOGenerator as EasyUseAnimaAIOGenerator,
        EasyUseAnimaInput as EasyUseAnimaInput,
        _aio_generation_settings_json as _aio_generation_settings_json,
        _aio_input_settings_json as _aio_input_settings_json,
    )
    from easyuse_anima.image.geometry import (
        _align_down as _align_down,
        _align_nearest as _align_nearest,
        _image_tensor_size as _image_tensor_size,
        # B-10b5 retires three root image-geometry aliases.
        # Canonical image/scaling/detailer consumers import geometry directly.
        # _align_nearest/_align_down stay for root residual runtime.
    )
    # B-10b2 deliberately omits the retired root Detailer hook alias.
    # Canonical image and Impact Detailer adapters import the owner directly.
    # The root module no longer re-exports this unsupported private helper.
    from easyuse_anima.image.sam3 import (
        # B-10b9 retires seven root SAM3 helper aliases.
        _context_value as _context_value,
        # Canonical SAM3 and Impact adapters import the owner directly.
        # Prompt formatting and detection behavior stay canonical.
        # Mask and empty-SEGS helpers stay canonical.
        # Optional-node resolver behavior stays canonical.
        # Context/state helpers remain root runtime seams.
        # SAM3 class aliases stay unchanged.
        _sam3_context as _sam3_context,
        _segs_has_items as _segs_has_items,
    )
    from easyuse_anima.image.scaling import (
        IMAGE_SCALE_MULTIPLES as IMAGE_SCALE_MULTIPLES,
        IMAGE_UPSCALE_METHODS as IMAGE_UPSCALE_METHODS,
        # B-10b6 retires four root image-scaling helper aliases.
        # The canonical image adapter imports scaling helpers directly.
        # Constants stay for the AiO generation-normalization resolver.
        # The public mapped node class remains a root re-export.
    )
    from easyuse_anima.infrastructure.comfy.capabilities import (
        _comfy_sampler_names as _comfy_sampler_names,
        _comfy_scheduler_names as _comfy_scheduler_names,
        # B-10b4 omits the retired root _impact_core_module alias.
        _impact_scheduler_names as _impact_scheduler_names,
    )
    from easyuse_anima.infrastructure.comfy.invocation import (
        _call_with_supported_kwargs as _call_with_supported_kwargs,
        _common_upscale_image as _common_upscale_image,
        _node_output_tuple as _node_output_tuple,
    )
    from easyuse_anima.infrastructure.comfy.resources import (
        # B-10b1 deliberately omits the retired root _comfy_checkpoint_names alias.
        _comfy_clip_loader_types as _adapter_comfy_clip_loader_types,
        _comfy_diffusion_model_names as _adapter_comfy_diffusion_model_names,
        _comfy_text_encoder_names as _adapter_comfy_text_encoder_names,
        _comfy_vae_names as _adapter_comfy_vae_names,
        _folder_path_names as _folder_path_names,
    )
    from easyuse_anima.nodes.image_nodes import (
        EasyUseAnimaDetailerAlignHook as EasyUseAnimaDetailerAlignHook,
        EasyUseAnimaImageScaleByMultiple as EasyUseAnimaImageScaleByMultiple,
    )
    from easyuse_anima.nodes.sam3_nodes import (
        EasyUseAnimaSAM3Context as EasyUseAnimaSAM3Context,
        EasyUseAnimaSAM3Detailer as EasyUseAnimaSAM3Detailer,
    )
    from easyuse_anima.nodes.prompt_nodes import (
        EasyUseAnimaPromptBuilder as EasyUseAnimaPromptBuilder,
        EasyUseAnimaPromptCorrector as EasyUseAnimaPromptCorrector,
        EasyUseAnimaPromptCorrectorSimple as EasyUseAnimaPromptCorrectorSimple,
        EasyUseAnimaPromptStudio as EasyUseAnimaPromptStudio,
    )
    from easyuse_anima.nodes.regional_nodes import (
        EasyUseAnimaPromptStudioRegional as EasyUseAnimaPromptStudioRegional,
        EasyUseAnimaRegionalConditioning as EasyUseAnimaRegionalConditioning,
    )
    from easyuse_anima.naia.client import (
        # B-10b13 retires 13 unsupported NAIA client root aliases.
        # Canonical client and node-adapter consumers import their owner directly.
        # Host and port defaults stay canonical.
        # Local-host and remote opt-in policy stays canonical.
        # Request timeout values stay canonical.
        # Resolution bounds and 1MP fitting stay canonical.
        # Preprocessing keys and choices stay canonical.
        # URL construction and host validation stay canonical.
        # Prompt cleanup stays canonical.
        # Repository tests use the canonical owner for retired names.
        # Retained runtime values stay direct root seams.
        # Response parsing and HTTP posting remain bound at call time.
        # Mapped NAIA node identity and workflows stay unchanged.
        LATENT_ALIGN as LATENT_ALIGN,
        _parse_random_response as _parse_random_response,
        _post_random as _post_random,
    )
    from easyuse_anima.naia.resolution import (
        # B-10b14 retires 16 unsupported NAIA resolution root aliases.
        # Canonical resolution and adapter consumers import their owner directly.
        # Bucket data and insertion order stay canonical.
        # Custom, NAIA, and default labels stay canonical.
        # Scale and bucket mode values stay canonical.
        # Bucket-fit selection stays canonical.
        # Resolution scale and max-long-edge policy stays canonical.
        # Resolution-mode normalization stays canonical.
        # Bucket-name normalization stays canonical.
        # Scaled-resolution calculation stays canonical.
        # 32-pixel snapping stays canonical.
        # Sorted option generation stays canonical.
        # Repository tests use the canonical owner for retired names.
        # Retained labels and selection helpers stay root seams.
        # Runtime-resolved final NAIA resolution stays a root seam.
        # Mapped node identities and workflows stay unchanged.
        _advanced_resolution_from_selection as _advanced_resolution_from_selection,
        _normalize_resolution_bucket as _normalize_resolution_bucket,
        _ratio_label as _ratio_label,
        _resolution_label as _resolution_label,
        _resolve_naia_resolution as _resolve_naia_resolution,
    )
    from easyuse_anima.nodes.naia_nodes import (
        EasyUseAnimaNAIARandomPrompt as EasyUseAnimaNAIARandomPrompt,
    )
    from easyuse_anima.nodes.wildcard_nodes import (
        EasyUseAnimaWildcard as EasyUseAnimaWildcard,
        # B-10b8 retires the test-only root wildcard-note alias.
    )
    from easyuse_anima.lora.metadata import (
        _apply_lora_syntax_format as _apply_lora_syntax_format,
        _dedupe_text_values as _dedupe_text_values,
        _fallback_lora_path as _fallback_lora_path,
        _get_lora_info as _get_lora_info,
        _get_lora_manager_trigger_words as _get_lora_manager_trigger_words,
        _load_lora_manager_metadata as _load_lora_manager_metadata,
        _lora_combo_values as _lora_combo_values,
        _lora_manager_trigger_words_from_metadata as _lora_manager_trigger_words_from_metadata,
        _lora_model_exists as _lora_model_exists,
        _lora_stack_name as _lora_stack_name,
        _metadata_json_paths_for_lora as _metadata_json_paths_for_lora,
        _missing_lora_display_name as _missing_lora_display_name,
        _raise_missing_loras as _raise_missing_loras,
        _trigger_words_from_value as _trigger_words_from_value,
    )
    from easyuse_anima.lora.preset import (
        _correct_style_prompt as _correct_style_prompt,
        _format_strength as _format_strength,
        _get_loras_list as _get_loras_list,
        _load_profile_data as _load_profile_data,
        _profile_key as _profile_key,
        _select_profile_values as _select_profile_values,
        _wrap_profile_index as _wrap_profile_index,
    )
    from easyuse_anima.nodes.lora_nodes import (
        EasyUseAnimaLoraPreset as EasyUseAnimaLoraPreset,
    )
    from anima_prompt import correct_prompt, load_knowledge_base
    from anima_prompt.parser import parse_prompt
    from settings import (
        resolve_metadata_filter_words,
        resolve_naia_settings,
        resolve_prompt_translation_settings,
    )
    from easyuse_anima.translation.markers import (
        has_prompt_translation_markers,
    )
    from easyuse_anima.translation.service import (
        translate_prompt_markers,
    )
    from wildcard_engine import (
        MAX_SEED,
        PUBLIC_MAX_SEED,
        PROMPT_STUDIO_WILDCARD_MODE_LABELS,
        SEED_CONTROL_DECREMENT,
        SEED_CONTROL_FIXED,
        SEED_CONTROL_INCREMENT,
        SEED_CONTROL_MODES,
        SEED_CONTROL_RANDOMIZE,
        WILDCARD_MODE_FIXED,
        WILDCARD_MODE_POPULATE,
        WILDCARD_MODE_SEQUENTIAL,
        expand_wildcard_texts,
        expand_wildcards,
        has_wildcard_syntax,
        next_seed,
        normalize_seed,
        normalize_prompt_studio_wildcard_mode,
        normalize_wildcard_mode,
        wildcard_sources_signature,
    )

__all__ = [
    "EasyUseAnimaAIOGenerator",
    "EasyUseAnimaDetailerAlignHook",
    "EasyUseAnimaArtistMixConditioning",
    "EasyUseAnimaInput",
    "EasyUseAnimaImageScaleByMultiple",
    "EasyUseAnimaLoraPreset",
    "EasyUseAnimaNAIARandomPrompt",
    "EasyUseAnimaPromptDataConditioning",
    "EasyUseAnimaPromptDataUnpack",
    "EasyUseAnimaPromptBuilder",
    "EasyUseAnimaPromptCorrector",
    "EasyUseAnimaPromptCorrectorSimple",
    "EasyUseAnimaPromptStudio",
    "EasyUseAnimaPromptStudioAdvanced",
    "EasyUseAnimaPromptStudioAdvancedV2",
    "EasyUseAnimaPromptStudioRegional",
    "EasyUseAnimaRegionalConditioning",
    "EasyUseAnimaWildcard",
]
