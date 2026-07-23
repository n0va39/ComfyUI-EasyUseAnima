# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import logging
import random
from math import ceil, sqrt

try:
    from .easyuse_anima.aio.first_pass_cache import (
        AIO_FIRST_PASS_CACHE_MAX_ENTRIES as AIO_FIRST_PASS_CACHE_MAX_ENTRIES,
        _AIO_FIRST_PASS_CACHE as _AIO_FIRST_PASS_CACHE,
        _AIO_FIRST_PASS_CACHE_ORDER as _AIO_FIRST_PASS_CACHE_ORDER,
        _aio_first_pass_cache_key as _aio_first_pass_cache_key,
        _bind_aio_first_pass_cache_runtime as _bind_aio_first_pass_cache_runtime,
        # B-10b7 retires the test-only root cache-clear function alias.
        _clone_aio_cache_value as _clone_aio_cache_value,
        _get_aio_first_pass_cache as _get_aio_first_pass_cache,
        _put_aio_first_pass_cache as _put_aio_first_pass_cache,
    )
    from .easyuse_anima.aio.legacy_generation import (
        _bind_aio_legacy_generation_runtime as _bind_aio_legacy_generation_runtime,
        _run_aio_detailer_stage as _run_aio_detailer_stage,
        _run_aio_detailer_target as _run_aio_detailer_target,
        _run_aio_highres_stage as _run_aio_highres_stage,
        _run_aio_legacy_generation as _run_aio_legacy_generation,
        _run_aio_resshift_upscale_stage as _run_aio_resshift_upscale_stage,
        _run_aio_upscale_stage as _run_aio_upscale_stage,
        _run_aio_usdu_upscale_stage as _run_aio_usdu_upscale_stage,
    )
    from .easyuse_anima.aio.generation_normalization import (
        AIO_SPECIAL_SEEDS as AIO_SPECIAL_SEEDS,
        AIO_SPECIAL_SEED_DECREMENT as AIO_SPECIAL_SEED_DECREMENT,
        AIO_SPECIAL_SEED_INCREMENT as AIO_SPECIAL_SEED_INCREMENT,
        AIO_SPECIAL_SEED_RANDOM as AIO_SPECIAL_SEED_RANDOM,
        _AIO_DETAILER_CUSTOM_RE as _AIO_DETAILER_CUSTOM_RE,
        _AIO_DETAILER_RESERVED_KEYS as _AIO_DETAILER_RESERVED_KEYS,
        _aio_detailer_has_enabled_targets as _aio_detailer_has_enabled_targets,
        _aio_detailer_target_defaults as _aio_detailer_target_defaults,
        _aio_detailer_target_order as _aio_detailer_target_order,
        _bind_aio_generation_normalization_runtime as _bind_aio_generation_normalization_runtime,
        _is_aio_detailer_target_name as _is_aio_detailer_target_name,
        _merge_versioned_settings as _merge_versioned_settings,
        _normalize_aio_dit_corrections_settings as _normalize_aio_dit_corrections_settings,
        _normalize_aio_generation_settings as _normalize_aio_generation_settings,
        _normalize_aio_seed as _normalize_aio_seed,
        _normalize_aio_spectrum_settings as _normalize_aio_spectrum_settings,
    )
    from .easyuse_anima.aio.generation_settings import (
        round_trip_aio_generation_settings as _round_trip_aio_generation_settings,
    )
    from .easyuse_anima.aio.usdu import (
        _aio_usdu_auto_tile_dimension as _aio_usdu_auto_tile_dimension,
        _aio_usdu_tile_plan as _aio_usdu_tile_plan,
        _bind_aio_usdu_planning_runtime as _bind_aio_usdu_planning_runtime,
    )
    from .easyuse_anima.aio.postprocess import (
        _apply_aio_final_fit as _apply_aio_final_fit,
        _aio_final_fit_size as _aio_final_fit_size,
        _bind_aio_postprocess_runtime as _bind_aio_postprocess_runtime,
        _resize_image_to_size_if_needed as _resize_image_to_size_if_needed,
        _run_aio_postprocess_stage as _run_aio_postprocess_stage,
    )
    from .easyuse_anima.aio.conditioning import (
        _aio_prompt_data_fields_for_usdu as _aio_prompt_data_fields_for_usdu,
        _aio_usdu_conditioning as _aio_usdu_conditioning,
        _aio_usdu_prompt_without_general as _aio_usdu_prompt_without_general,
        _bind_aio_conditioning_runtime as _bind_aio_conditioning_runtime,
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
        _bind_aio_model_preparation_runtime as _bind_aio_model_preparation_runtime,
        _cleanup_aio_ephemeral_model as _cleanup_aio_ephemeral_model,
        _normalize_aio_lora_stack as _normalize_aio_lora_stack,
        _patch_model_sampling_aura_flow as _patch_model_sampling_aura_flow,
    )
    from .easyuse_anima.aio.sampling import (
        _aio_highres_effective_backend as _aio_highres_effective_backend,
        _aio_stage_sampler_settings as _aio_stage_sampler_settings,
        _bind_aio_sampling_runtime as _bind_aio_sampling_runtime,
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
        _bind_aio_preview_runtime as _bind_aio_preview_runtime,
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
        _bind_aio_output_runtime as _bind_aio_output_runtime,
        _normalize_aio_civitai_hash_fetchers as _normalize_aio_civitai_hash_fetchers,
        _normalize_aio_hash_bundles as _normalize_aio_hash_bundles,
        _save_image_with_comfy as _save_image_with_comfy,
        _save_image_with_image_saver as _save_image_with_image_saver,
    )
    from .easyuse_anima.aio.resources import (
        _bind_aio_resource_runtime as _bind_aio_resource_runtime,
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
        _bind_prompt_advanced_node_runtime as _bind_prompt_advanced_node_runtime,
    )
    from .easyuse_anima.nodes.aio_nodes import (
        EasyUseAnimaAIOGenerator as EasyUseAnimaAIOGenerator,
        EasyUseAnimaInput as EasyUseAnimaInput,
        _aio_generation_settings_json as _aio_generation_settings_json,
        _aio_input_settings_json as _aio_input_settings_json,
        _bind_aio_node_runtime as _bind_aio_node_runtime,
        _easy_use_anima_input_signature as _easy_use_anima_input_signature,
        _require_easy_use_anima_input as _require_easy_use_anima_input,
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
    from .easyuse_anima.infrastructure.comfy.wiring import (
        resolve_comfy_host_helper as _resolve_comfy_host_helper,
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
        _bind_regional_node_runtime as _bind_regional_node_runtime,
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
        _bind_naia_node_runtime as _bind_naia_node_runtime,
    )
    from .easyuse_anima.nodes.wildcard_nodes import (
        EasyUseAnimaWildcard as EasyUseAnimaWildcard,
        # B-10b8 retires the test-only root wildcard-note alias.
        _bind_wildcard_node_runtime as _bind_wildcard_node_runtime,
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
    from .prompt_translation import has_prompt_translation_markers, translate_prompt_markers
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
        _bind_aio_first_pass_cache_runtime as _bind_aio_first_pass_cache_runtime,
        # B-10b7 retires the test-only root cache-clear function alias.
        _clone_aio_cache_value as _clone_aio_cache_value,
        _get_aio_first_pass_cache as _get_aio_first_pass_cache,
        _put_aio_first_pass_cache as _put_aio_first_pass_cache,
    )
    from easyuse_anima.aio.legacy_generation import (
        _bind_aio_legacy_generation_runtime as _bind_aio_legacy_generation_runtime,
        _run_aio_detailer_stage as _run_aio_detailer_stage,
        _run_aio_detailer_target as _run_aio_detailer_target,
        _run_aio_highres_stage as _run_aio_highres_stage,
        _run_aio_legacy_generation as _run_aio_legacy_generation,
        _run_aio_resshift_upscale_stage as _run_aio_resshift_upscale_stage,
        _run_aio_upscale_stage as _run_aio_upscale_stage,
        _run_aio_usdu_upscale_stage as _run_aio_usdu_upscale_stage,
    )
    from easyuse_anima.aio.generation_normalization import (
        AIO_SPECIAL_SEEDS as AIO_SPECIAL_SEEDS,
        AIO_SPECIAL_SEED_DECREMENT as AIO_SPECIAL_SEED_DECREMENT,
        AIO_SPECIAL_SEED_INCREMENT as AIO_SPECIAL_SEED_INCREMENT,
        AIO_SPECIAL_SEED_RANDOM as AIO_SPECIAL_SEED_RANDOM,
        _AIO_DETAILER_CUSTOM_RE as _AIO_DETAILER_CUSTOM_RE,
        _AIO_DETAILER_RESERVED_KEYS as _AIO_DETAILER_RESERVED_KEYS,
        _aio_detailer_has_enabled_targets as _aio_detailer_has_enabled_targets,
        _aio_detailer_target_defaults as _aio_detailer_target_defaults,
        _aio_detailer_target_order as _aio_detailer_target_order,
        _bind_aio_generation_normalization_runtime as _bind_aio_generation_normalization_runtime,
        _is_aio_detailer_target_name as _is_aio_detailer_target_name,
        _merge_versioned_settings as _merge_versioned_settings,
        _normalize_aio_dit_corrections_settings as _normalize_aio_dit_corrections_settings,
        _normalize_aio_generation_settings as _normalize_aio_generation_settings,
        _normalize_aio_seed as _normalize_aio_seed,
        _normalize_aio_spectrum_settings as _normalize_aio_spectrum_settings,
    )
    from easyuse_anima.aio.generation_settings import (
        round_trip_aio_generation_settings as _round_trip_aio_generation_settings,
    )
    from easyuse_anima.aio.usdu import (
        _aio_usdu_auto_tile_dimension as _aio_usdu_auto_tile_dimension,
        _aio_usdu_tile_plan as _aio_usdu_tile_plan,
        _bind_aio_usdu_planning_runtime as _bind_aio_usdu_planning_runtime,
    )
    from easyuse_anima.aio.postprocess import (
        _apply_aio_final_fit as _apply_aio_final_fit,
        _aio_final_fit_size as _aio_final_fit_size,
        _bind_aio_postprocess_runtime as _bind_aio_postprocess_runtime,
        _resize_image_to_size_if_needed as _resize_image_to_size_if_needed,
        _run_aio_postprocess_stage as _run_aio_postprocess_stage,
    )
    from easyuse_anima.aio.conditioning import (
        _aio_prompt_data_fields_for_usdu as _aio_prompt_data_fields_for_usdu,
        _aio_usdu_conditioning as _aio_usdu_conditioning,
        _aio_usdu_prompt_without_general as _aio_usdu_prompt_without_general,
        _bind_aio_conditioning_runtime as _bind_aio_conditioning_runtime,
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
        _bind_aio_model_preparation_runtime as _bind_aio_model_preparation_runtime,
        _cleanup_aio_ephemeral_model as _cleanup_aio_ephemeral_model,
        _normalize_aio_lora_stack as _normalize_aio_lora_stack,
        _patch_model_sampling_aura_flow as _patch_model_sampling_aura_flow,
    )
    from easyuse_anima.aio.sampling import (
        _aio_highres_effective_backend as _aio_highres_effective_backend,
        _aio_stage_sampler_settings as _aio_stage_sampler_settings,
        _bind_aio_sampling_runtime as _bind_aio_sampling_runtime,
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
        _bind_aio_preview_runtime as _bind_aio_preview_runtime,
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
        _bind_aio_output_runtime as _bind_aio_output_runtime,
        _normalize_aio_civitai_hash_fetchers as _normalize_aio_civitai_hash_fetchers,
        _normalize_aio_hash_bundles as _normalize_aio_hash_bundles,
        _save_image_with_comfy as _save_image_with_comfy,
        _save_image_with_image_saver as _save_image_with_image_saver,
    )
    from easyuse_anima.aio.resources import (
        _bind_aio_resource_runtime as _bind_aio_resource_runtime,
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
        _bind_prompt_advanced_node_runtime as _bind_prompt_advanced_node_runtime,
    )
    from easyuse_anima.nodes.aio_nodes import (
        EasyUseAnimaAIOGenerator as EasyUseAnimaAIOGenerator,
        EasyUseAnimaInput as EasyUseAnimaInput,
        _aio_generation_settings_json as _aio_generation_settings_json,
        _aio_input_settings_json as _aio_input_settings_json,
        _bind_aio_node_runtime as _bind_aio_node_runtime,
        _easy_use_anima_input_signature as _easy_use_anima_input_signature,
        _require_easy_use_anima_input as _require_easy_use_anima_input,
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
    from easyuse_anima.infrastructure.comfy.wiring import (
        resolve_comfy_host_helper as _resolve_comfy_host_helper,
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
        _bind_regional_node_runtime as _bind_regional_node_runtime,
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
        _bind_naia_node_runtime as _bind_naia_node_runtime,
    )
    from easyuse_anima.nodes.wildcard_nodes import (
        EasyUseAnimaWildcard as EasyUseAnimaWildcard,
        # B-10b8 retires the test-only root wildcard-note alias.
        _bind_wildcard_node_runtime as _bind_wildcard_node_runtime,
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
    from prompt_translation import has_prompt_translation_markers, translate_prompt_markers
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

logger = logging.getLogger("ComfyUI-EasyUseAnima")

WILDCARD_RESERVED_NEXT_SEED_INPUT = "easyuse_anima_reserved_wildcard_next_seed"
WILDCARD_QUEUE_MAX_SAFE_SEED = PUBLIC_MAX_SEED
EASY_USE_ANIMA_INPUT_TYPE = "EASY_USE_ANIMA_INPUT"
EASY_USE_ANIMA_INPUT_SCHEMA = "easy_use_anima_input"
EASY_USE_ANIMA_INPUT_SETTINGS_VERSION = 1
AIO_GENERATION_SETTINGS_SCHEMA = "easyuse_anima_aio_generation_settings"
AIO_GENERATION_SETTINGS_VERSION = 1
ANIMA_DEFAULT_DIFFUSION_MODEL_CANDIDATES = (
    "anima-base-v1.0.safetensors",
    "ANIMA\\anima_baseV10.safetensors",
)
ANIMA_DEFAULT_VAE_CANDIDATES = (
    "qwen_image_vae.safetensors",
)
ANIMA_DEFAULT_CLIP_CANDIDATES = (
    "qwen_3_06b_base.safetensors",
)
ANIMA_CLIP_TYPES = (
    "stable_diffusion",
    "stable_cascade",
    "sd3",
    "stable_audio",
    "mochi",
    "ltxv",
    "pixart",
    "cosmos",
    "lumina2",
    "wan",
    "hidream",
    "chroma",
    "ace",
    "omnigen2",
    "qwen_image",
    "hunyuan_image",
    "flux2",
    "ovis",
    "longcat_image",
    "cogvideox",
    "lens",
    "pixeldit",
    "ideogram4",
)
ANIMA_UNET_WEIGHT_DTYPES = (
    "default",
    "fp8_e4m3fn",
    "fp8_e4m3fn_fast",
    "fp8_e5m2",
)
ANIMA_CLIP_DEVICES = ("default", "cpu")
AIO_INPUT_DEFAULT_SETTINGS = {
    "schema": EASY_USE_ANIMA_INPUT_SCHEMA,
    "version": EASY_USE_ANIMA_INPUT_SETTINGS_VERSION,
    "resources": {
        "loader_mode": "split",
        "clip_loader": "single",
        "unet_weight_dtype": "default",
        "clip_device": "default",
    },
    "metadata": {},
}
AIO_GENERATION_DEFAULT_SETTINGS = {
    "schema": AIO_GENERATION_SETTINGS_SCHEMA,
    "version": AIO_GENERATION_SETTINGS_VERSION,
    "mode": "txt2img",
    "sampler": {
        "backend": "comfy_ksampler",
        "seed": AIO_SPECIAL_SEED_RANDOM,
        "seed_after_generate": SEED_CONTROL_FIXED,
        "steps": 32,
        "cfg": 5.0,
        "sampler_name": "er_sde",
        "scheduler": "simple",
        "denoise": 1.0,
        "spectrum": {
            "enabled": False,
            "window_size": 2.0,
            "flex_window": 0.25,
            "warmup_steps": 6,
            "tail_actual_steps": 3,
            "blend_w": 0.3,
            "cheby_degree": 3,
            "ridge_lambda": 0.1,
            "history_size": 100,
            "one_sampler_only": False,
            "verbose": False,
            "compat_policy": "conservative",
        },
        "spd": {
            "split_mode": "single",
            "scale": 0.5,
            "sigma": 0.7,
            "adaptive_smc_alpha": 0.0,
        },
        "spectrum_extra": {},
        "spd_extra": {},
        "dit_corrections": {
            "enabled": False,
            "dcw_mode": "off",
            "dcw_lambda": 0.01,
            "dcw_band_mask": "LL",
            "dcw_calibrator": "(auto-download default)",
            "smc_cfg": False,
            "adaptive_smc_alpha": 0.0,
            "smc_cfg_lambda": 6.0,
            "cfgpp": False,
            "cfgpp_lambda": 0.0,
            "fsg": False,
            "fsg_band_lo": 0.59,
            "fsg_band_hi": 0.75,
            "fsg_k": 3,
            "fsg_d_sigma": 0.1,
            "fsg_gamma": 0.0,
            "replace_existing_cfg": False,
        },
    },
    "model_patches": {
        "aura_flow": {
            "shift": 3.0,
        },
        "dave": {
            "enabled": False,
            "mask": "dave_alpha.npz",
            "strength": 0.30,
            "tau": 0.10,
        },
        "safe_pag": {
            "enabled": False,
            "scale": 4.0,
            "block_indices": "18",
            "perturbation_strength": 0.75,
            "head_indices": "",
            "start_percent": 0.0,
            "end_percent": 0.7,
            "rescale": 0.2,
            "rescale_mode": "full",
        },
        "kj": {
            "fp16_accumulation": False,
            "sage_attention": "disabled",
            "sage_allow_compile": False,
            "torch_compile": {
                "enabled": False,
                "backend": "inductor",
                "fullgraph": False,
                "mode": "max-autotune-no-cudagraphs",
                "dynamic": "false",
                "compile_transformer_blocks_only": True,
                "dynamo_cache_size_limit": 64,
                "debug_compile_keys": False,
                "disable_dynamic_vram": True,
            },
        },
    },
    "mod_guidance": {
        "mode": ANIMA_MOD_GUIDANCE_MODE_FROM_PROMPT_DATA,
        "profile": ANIMA_MOD_GUIDANCE_DEFAULT_PROFILE,
        "advanced": {
            "adapter": "(auto-download default)",
            "quality_tags": "highres, best quality, score_7",
            "quality_neg": "score_1, score_2, score_3, worst quality, lowres, old, bad hands, bad anatomy",
            "mod_w": 3.0,
            "mod_start_layer": 8,
            "mod_end_layer": 27,
            "mod_taper": 0,
            "mod_taper_scale": 0.25,
            "mod_final_w": 0.0,
        },
    },
    "artist_mix": {
        "mode": ARTIST_MIX_MODE_FROM_PROMPT_DATA,
        "start_percent": ARTIST_MIX_DEFAULT_START_PERCENT,
        "strength_scale": ARTIST_MIX_DEFAULT_STRENGTH_SCALE,
        "style_gain": ARTIST_MIX_DEFAULT_STYLE_GAIN,
        "rms_scale_cap": ARTIST_MIX_DEFAULT_RMS_SCALE_CAP,
        "exact_top_k": ARTIST_MIX_DEFAULT_EXACT_TOP_K,
        "cluster_count": ARTIST_MIX_DEFAULT_CLUSTER_COUNT,
        "dominant_isolation": ARTIST_MIX_DEFAULT_DOMINANT_ISOLATION,
        "dominant_threshold": ARTIST_MIX_DEFAULT_DOMINANT_THRESHOLD,
    },
    "highres": {
        "enabled": False,
        "scale_by": 1.5,
        "upscale_method": "bicubic",
        "multiple": "32",
        "max_long_edge": 2560,
        "steps": 20,
        "inherit_sampler_settings": True,
        "cfg": 8.0,
        "sampler_name": "euler",
        "scheduler": "simple",
        "denoise": 0.25,
        "spectrum": {
            "enabled": False,
            "window_size": 2.0,
            "flex_window": 0.2,
            "warmup_steps": 7,
            "tail_actual_steps": 4,
            "blend_w": 0.3,
            "cheby_degree": 3,
            "ridge_lambda": 0.1,
            "history_size": 100,
            "one_sampler_only": False,
            "verbose": False,
            "compat_policy": "conservative",
        },
        "dit_corrections": {
            "enabled": False,
            "dcw_mode": "off",
            "dcw_lambda": 0.02,
            "dcw_band_mask": "LL",
            "dcw_calibrator": "(auto-download default)",
            "smc_cfg": False,
            "adaptive_smc_alpha": 0.0,
            "smc_cfg_lambda": 6.0,
            "cfgpp": False,
            "cfgpp_lambda": 0.0,
            "fsg": False,
            "fsg_band_lo": 0.59,
            "fsg_band_hi": 0.75,
            "fsg_k": 3,
            "fsg_d_sigma": 0.1,
            "fsg_gamma": 0.0,
            "replace_existing_cfg": False,
        },
    },
    "upscale": {
        "enabled": False,
        "backend": "usdu",
        "scale_by": 2.0,
        "steps": 20,
        "inherit_sampler_settings": True,
        "cfg": 8.0,
        "sampler_name": "euler",
        "scheduler": "simple",
        "denoise": 0.2,
        "spectrum": {
            "enabled": False,
            "window_size": 2.0,
            "flex_window": 0.2,
            "warmup_steps": 7,
            "tail_actual_steps": 4,
            "blend_w": 0.3,
            "cheby_degree": 3,
            "ridge_lambda": 0.1,
            "history_size": 100,
            "one_sampler_only": False,
            "verbose": False,
            "compat_policy": "conservative",
        },
        "dit_corrections": {
            "enabled": False,
            "dcw_mode": "off",
            "dcw_lambda": 0.02,
            "dcw_band_mask": "LL",
            "dcw_calibrator": "(auto-download default)",
            "smc_cfg": False,
            "adaptive_smc_alpha": 0.0,
            "smc_cfg_lambda": 6.0,
            "cfgpp": False,
            "cfgpp_lambda": 0.0,
            "fsg": False,
            "fsg_band_lo": 0.59,
            "fsg_band_hi": 0.75,
            "fsg_k": 3,
            "fsg_d_sigma": 0.1,
            "fsg_gamma": 0.0,
            "replace_existing_cfg": False,
        },
        "usdu": {
            "upscale_model_name": "2x-AnimeSharpV4_Fast_RCAN_PU.safetensors",
            "auto_tile_size": True,
            "prompt_mode": "full",
            "mode_type": "Linear",
            "auto_tile_target": 1024,
            "auto_tile_min": 512,
            "auto_tile_max": 2048,
            "tile_width": 512,
            "tile_height": 512,
            "mask_blur": 8,
            "tile_padding": 32,
            "seam_fix_mode": "None",
            "seam_fix_denoise": 1.0,
            "seam_fix_width": 64,
            "seam_fix_mask_blur": 8,
            "seam_fix_padding": 16,
            "force_uniform_tiles": True,
            "tiled_decode": False,
            "batch_size": 1,
        },
        "resshift": {
            "scale": "x2",
            "student_name": "(auto-download)",
            "dtype": "bf16",
            "chop": 512,
            "overlap": 64,
            "tile_batch": 4,
        },
    },
    "postprocess": {
        "enabled": False,
        "fit": {
            "mode": "max_long_edge",
            "max_long_edge": 2048,
            "max_megapixels": 4.0,
            "method": "bicubic",
        },
    },
    "detailer": {
        "enabled": False,
        "order": ["face", "eye"],
        "sam3": {
            "context": "load_checkpoint",
            "checkpoint": "sam3.1_multiplex_fp16.safetensors",
        },
        "face": {
            "label": "Face Detailer",
            "enabled": False,
            "detect_prompt": "face",
            "detect_count": 1,
            "threshold": 0.52,
            "refine_iterations": 2,
            "individual_masks": True,
            "combined": False,
            "crop_factor": 4.0,
            "bbox_fill": False,
            "drop_size": 100,
            "contour_fill": True,
            "guide_size": 1024,
            "guide_size_for": False,
            "max_size": 2048,
            "steps": 20,
            "inherit_sampler_settings": True,
            "cfg": 8.0,
            "sampler_name": "euler",
            "scheduler": "sgm_uniform",
            "denoise": 0.33,
            "feather": 5,
            "noise_mask": True,
            "force_inpaint": True,
            "wildcard": "",
            "cycle": 1,
            "alignment": "32",
            "inpaint_model": False,
            "noise_mask_feather": 10,
            "tiled_encode": False,
            "tiled_decode": False,
            "spectrum": {
                "enabled": True,
                "window_size": 2.0,
                "flex_window": 0.15,
                "warmup_steps": 6,
                "tail_actual_steps": 3,
                "blend_w": 0.3,
                "cheby_degree": 3,
                "ridge_lambda": 0.1,
                "history_size": 100,
                "one_sampler_only": False,
                "verbose": False,
                "compat_policy": "conservative",
            },
            "dit_corrections": {
                "enabled": False,
                "dcw_mode": "off",
                "dcw_lambda": 0.02,
                "dcw_band_mask": "LL",
                "dcw_calibrator": "(auto-download default)",
                "smc_cfg": False,
                "adaptive_smc_alpha": 0.0,
                "smc_cfg_lambda": 6.0,
                "cfgpp": False,
                "cfgpp_lambda": 0.0,
                "fsg": False,
                "fsg_band_lo": 0.59,
                "fsg_band_hi": 0.75,
                "fsg_k": 3,
                "fsg_d_sigma": 0.1,
                "fsg_gamma": 0.0,
                "replace_existing_cfg": False,
            },
        },
        "eye": {
            "label": "Eye Detailer",
            "enabled": False,
            "detect_prompt": "eyes",
            "detect_count": 1,
            "threshold": 0.5,
            "refine_iterations": 2,
            "individual_masks": True,
            "combined": False,
            "crop_factor": 6.0,
            "bbox_fill": False,
            "drop_size": 40,
            "contour_fill": True,
            "guide_size": 1024,
            "guide_size_for": False,
            "max_size": 2048,
            "steps": 20,
            "inherit_sampler_settings": True,
            "cfg": 8.0,
            "sampler_name": "euler",
            "scheduler": "sgm_uniform",
            "denoise": 0.29,
            "feather": 6,
            "noise_mask": True,
            "force_inpaint": True,
            "wildcard": "",
            "cycle": 1,
            "alignment": "32",
            "inpaint_model": False,
            "noise_mask_feather": 20,
            "tiled_encode": False,
            "tiled_decode": False,
            "spectrum": {
                "enabled": True,
                "window_size": 2.0,
                "flex_window": 0.15,
                "warmup_steps": 6,
                "tail_actual_steps": 3,
                "blend_w": 0.3,
                "cheby_degree": 3,
                "ridge_lambda": 0.1,
                "history_size": 100,
                "one_sampler_only": False,
                "verbose": False,
                "compat_policy": "conservative",
            },
            "dit_corrections": {
                "enabled": False,
                "dcw_mode": "off",
                "dcw_lambda": 0.02,
                "dcw_band_mask": "LL",
                "dcw_calibrator": "(auto-download default)",
                "smc_cfg": False,
                "adaptive_smc_alpha": 0.0,
                "smc_cfg_lambda": 6.0,
                "cfgpp": False,
                "cfgpp_lambda": 0.0,
                "fsg": False,
                "fsg_band_lo": 0.59,
                "fsg_band_hi": 0.75,
                "fsg_k": 3,
                "fsg_d_sigma": 0.1,
                "fsg_gamma": 0.0,
                "replace_existing_cfg": False,
            },
        },
    },
    "save": {
        "enabled": True,
        "backend": "image_saver",
        "image_saver": {
            "filename": "%time_%basemodelname",
            "path": "EasyUseAnima/AiO",
            "extension": "webp",
            "lossless_webp": False,
            "quality_jpeg_or_webp": 97,
            "optimize_png": True,
            "counter": 0,
            "clip_skip": 0,
            "time_format": "%Y-%m-%d-%H%M%S",
            "save_workflow_as_json": False,
            "embed_workflow": True,
            "save_prompt_metadata": True,
            "additional_hashes": "",
            "additional_hash_bundles": [],
            "civitai_hash_fetchers": [],
            "download_civitai_data": True,
            "easy_remix": True,
            "custom": "",
        },
    },
    "preview": {
        "intermediate_images": False,
        "compare_previous": False,
        "image_feed": True,
        "feed_count": 12,
    },
}
AIO_FINAL_UPSCALE_BACKENDS = ("usdu", "resshift")
AIO_USDU_MODE_TYPES = ("Linear", "Chess", "None")
AIO_USDU_SEAM_FIX_MODES = ("None", "Band Pass", "Half Tile", "Half Tile + Intersections")
AIO_USDU_PROMPT_FULL = "full"
AIO_USDU_PROMPT_NO_GENERAL = "no_general"
AIO_USDU_PROMPT_MODES = (AIO_USDU_PROMPT_FULL, AIO_USDU_PROMPT_NO_GENERAL)
AIO_FINAL_FIT_MODES = ("max_long_edge", "megapixels")
AIO_RESHIFT_SCALES = ("x2", "x4")
AIO_RESHIFT_DTYPES = ("bf16", "fp32")


_TRIGGER_WORD_KEYS = ("trainedWords", "trained_words", "trigger_words", "activation_text")


def _consume_reserved_wildcard_next_seed(
    reservation_inputs,
    workflow_prompt,
    node_id,
    current_seed,
    wildcard_mode,
    seed_control,
):
    if not isinstance(reservation_inputs, dict):
        return None
    raw_reservation = _single_value(
        reservation_inputs.pop(WILDCARD_RESERVED_NEXT_SEED_INPUT, None)
    )
    node_id = _single_value(node_id)
    if isinstance(workflow_prompt, dict) and node_id is not None:
        prompt_node = workflow_prompt.get(str(node_id))
        prompt_inputs = prompt_node.get("inputs") if isinstance(prompt_node, dict) else None
        if isinstance(prompt_inputs, dict):
            prompt_inputs.pop(WILDCARD_RESERVED_NEXT_SEED_INPUT, None)
    if not isinstance(raw_reservation, str):
        return None
    try:
        reservation = json.loads(raw_reservation)
    except (TypeError, ValueError, json.JSONDecodeError):
        return None
    if (
        not isinstance(reservation, dict)
        or isinstance(reservation.get("version"), bool)
        or reservation.get("version") != 1
    ):
        return None
    required_keys = {"current_seed", "next_seed", "mode", "control"}
    if not required_keys.issubset(reservation):
        return None

    def reserved_seed(value):
        if isinstance(value, bool) or not isinstance(value, int):
            return None
        return value if 0 <= value <= WILDCARD_QUEUE_MAX_SAFE_SEED else None

    reservation_current_seed = reserved_seed(reservation.get("current_seed"))
    reservation_next_seed = reserved_seed(reservation.get("next_seed"))
    if reservation_current_seed is None or reservation_next_seed is None:
        return None
    reservation_mode = str(reservation.get("mode") or "")
    if reservation_mode not in {
        WILDCARD_MODE_POPULATE,
        WILDCARD_MODE_FIXED,
        WILDCARD_MODE_SEQUENTIAL,
    }:
        return None
    reservation_control = str(reservation.get("control") or "")
    if reservation_control not in set(SEED_CONTROL_MODES):
        return None
    if reservation_current_seed != normalize_seed(current_seed):
        return None
    if reservation_mode != normalize_wildcard_mode(wildcard_mode):
        return None
    if reservation_control != str(seed_control or SEED_CONTROL_FIXED):
        return None
    if reservation_control == SEED_CONTROL_RANDOMIZE:
        return reservation_next_seed
    if reservation_control == SEED_CONTROL_FIXED:
        expected_next_seed = reservation_current_seed
    elif reservation_control == SEED_CONTROL_INCREMENT:
        expected_next_seed = (
            0
            if reservation_current_seed >= WILDCARD_QUEUE_MAX_SAFE_SEED
            else reservation_current_seed + 1
        )
    elif reservation_control == SEED_CONTROL_DECREMENT:
        expected_next_seed = (
            WILDCARD_QUEUE_MAX_SAFE_SEED
            if reservation_current_seed <= 0
            else reservation_current_seed - 1
        )
    else:
        return None
    return reservation_next_seed if reservation_next_seed == expected_next_seed else None


_bind_aio_first_pass_cache_runtime(
    resolve_helper=lambda name: globals()[name],
)
_bind_aio_legacy_generation_runtime(
    resolve_helper=lambda name: _resolve_comfy_host_helper(
        name,
        lambda fallback_name: globals()[fallback_name],
    ),
)
_bind_aio_generation_normalization_runtime(
    resolve_helper=lambda name: _resolve_comfy_host_helper(
        name,
        lambda fallback_name: globals()[fallback_name],
    ),
)
_bind_aio_usdu_planning_runtime(
    resolve_helper=lambda name: globals()[name],
)
_bind_aio_postprocess_runtime(
    resolve_helper=lambda name: globals()[name],
)
_bind_aio_resource_runtime(
    resolve_helper=lambda name: _resolve_comfy_host_helper(
        name,
        lambda fallback_name: globals()[fallback_name],
    ),
)
_bind_aio_model_preparation_runtime(
    resolve_helper=lambda name: _resolve_comfy_host_helper(
        name,
        lambda fallback_name: globals()[fallback_name],
    ),
)
_bind_aio_sampling_runtime(
    resolve_helper=lambda name: _resolve_comfy_host_helper(
        name,
        lambda fallback_name: globals()[fallback_name],
    ),
)
_bind_aio_preview_runtime(
    resolve_helper=lambda name: _resolve_comfy_host_helper(
        name,
        lambda fallback_name: globals()[fallback_name],
    ),
)
_bind_aio_output_runtime(
    resolve_helper=lambda name: _resolve_comfy_host_helper(
        name,
        lambda fallback_name: globals()[fallback_name],
    ),
)
_bind_aio_conditioning_runtime(
    resolve_helper=lambda name: _resolve_comfy_host_helper(
        name,
        lambda fallback_name: globals()[fallback_name],
    ),
)
_bind_regional_node_runtime(
    resolve_helper=lambda name: _resolve_comfy_host_helper(
        name,
        lambda fallback_name: globals()[fallback_name],
    ),
    flexible_optional_input_type=_FlexibleOptionalInputType,
)
_bind_prompt_advanced_node_runtime(
    resolve_helper=lambda name: globals()[name],
    flexible_optional_input_type=_FlexibleOptionalInputType,
)
_bind_aio_node_runtime(
    resolve_helper=lambda name: globals()[name],
)
_bind_wildcard_node_runtime(
    get_workflow_node=lambda *args, **kwargs: _get_workflow_node(*args, **kwargs),
    expand=lambda *args, **kwargs: expand_wildcards(*args, **kwargs),
    normalize_seed_value=lambda *args, **kwargs: normalize_seed(*args, **kwargs),
    normalize_mode=lambda *args, **kwargs: normalize_wildcard_mode(*args, **kwargs),
    sources_signature=lambda *args, **kwargs: wildcard_sources_signature(*args, **kwargs),
)
_bind_naia_node_runtime(
    resolve_settings=lambda: resolve_naia_settings(),
    get_workflow_node=lambda *args, **kwargs: _get_workflow_node(*args, **kwargs),
    post_random=lambda *args, **kwargs: _post_random(*args, **kwargs),
    parse_random_response=lambda *args, **kwargs: _parse_random_response(*args, **kwargs),
)
