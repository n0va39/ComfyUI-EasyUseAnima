# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import logging
import random
import re
from math import ceil, sqrt
from typing import Any

try:
    from .easyuse_anima.aio.generation_normalization import (
        _bind_aio_generation_normalization_runtime as _bind_aio_generation_normalization_runtime,
        _merge_versioned_settings as _merge_versioned_settings,
        _normalize_aio_generation_settings as _normalize_aio_generation_settings,
    )
    from .easyuse_anima.aio.generation_settings import (
        round_trip_aio_generation_settings as _round_trip_aio_generation_settings,
    )
    from .easyuse_anima.aio.conditioning import (
        _aio_prompt_data_fields_for_usdu as _aio_prompt_data_fields_for_usdu,
        _aio_usdu_conditioning as _aio_usdu_conditioning,
        _aio_usdu_prompt_without_general as _aio_usdu_prompt_without_general,
        _bind_aio_conditioning_runtime as _bind_aio_conditioning_runtime,
    )
    from .easyuse_anima.aio.model_preparation import (
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
        _load_aio_resources_from_input_context as _load_aio_resources_from_input_context,
        _load_aio_sam3_context as _load_aio_sam3_context,
        _load_checkpoint_with_comfy as _load_checkpoint_with_comfy,
        _load_clip_with_comfy as _load_clip_with_comfy,
        _load_diffusion_model_with_comfy as _load_diffusion_model_with_comfy,
        _load_upscale_model_with_comfy as _load_upscale_model_with_comfy,
        _load_vae_with_comfy as _load_vae_with_comfy,
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
    from .easyuse_anima.prompt.correction import (
        _bind_prompt_correction_runtime as _bind_prompt_correction_runtime,
        _prompt_translation_change_key as _prompt_translation_change_key,
        _split_tag_text as _split_tag_text,
        _translate_prompt_text as _translate_prompt_text,
    )
    from .easyuse_anima.prompt.fields import (
        DEFAULT_QUALITY_TAGS as DEFAULT_QUALITY_TAGS,
        DEFAULT_TRAILING_QUALITY_TAGS as DEFAULT_TRAILING_QUALITY_TAGS,
        _HASH_COMMENT_RE as _HASH_COMMENT_RE,
        _INLINE_SPACE_RE as _INLINE_SPACE_RE,
        _WEIGHTED_TOKEN_RE as _WEIGHTED_TOKEN_RE,
        _bind_prompt_fields_runtime as _bind_prompt_fields_runtime,
        _correct_builder_prompt as _correct_builder_prompt,
        _filter_metadata_prompt as _filter_metadata_prompt,
        _join_prompt_tokens as _join_prompt_tokens,
        _metadata_filter_key as _metadata_filter_key,
        _metadata_filter_keys as _metadata_filter_keys,
        _prompt_tokens as _prompt_tokens,
    )
    from .easyuse_anima.prompt.data import (
        PROMPT_DATA_COMPAT_OUTPUT_TOOLTIPS as PROMPT_DATA_COMPAT_OUTPUT_TOOLTIPS,
        PROMPT_DATA_COMPAT_RETURN_NAMES as PROMPT_DATA_COMPAT_RETURN_NAMES,
        PROMPT_DATA_COMPAT_RETURN_TYPES as PROMPT_DATA_COMPAT_RETURN_TYPES,
        PROMPT_DATA_SCHEMA as PROMPT_DATA_SCHEMA,
        PROMPT_DATA_TYPE as PROMPT_DATA_TYPE,
        PROMPT_DATA_VERSION as PROMPT_DATA_VERSION,
        _advanced_outputs_from_prompt_data as _advanced_outputs_from_prompt_data,
        _apply_prompt_data_overrides as _apply_prompt_data_overrides,
        _copy_prompt_data_for_update as _copy_prompt_data_for_update,
        _normalize_prompt_data as _normalize_prompt_data,
        _prompt_data_input_default as _prompt_data_input_default,
        _prompt_data_json_safe as _prompt_data_json_safe,
        _prompt_data_nested as _prompt_data_nested,
        _prompt_data_output as _prompt_data_output,
        _prompt_data_parameter_snapshot as _prompt_data_parameter_snapshot,
        _set_prompt_data_output as _set_prompt_data_output,
    )
    from .easyuse_anima.prompt.advanced import (
        ADVANCED_FIELDS_WORKFLOW_PROPERTY as ADVANCED_FIELDS_WORKFLOW_PROPERTY,
        ADVANCED_FIELD_LABELS as ADVANCED_FIELD_LABELS,
        ADVANCED_FIELD_PANES as ADVANCED_FIELD_PANES,
        ADVANCED_FIELD_TYPES as ADVANCED_FIELD_TYPES,
        EXTEND_PROMPT_SLOT_SPECS as EXTEND_PROMPT_SLOT_SPECS,
        PROMPT_STUDIO_LEGACY_FIXED_WILDCARD_MODES as PROMPT_STUDIO_LEGACY_FIXED_WILDCARD_MODES,
        PROMPT_STUDIO_ADVANCED_RETURN_NAMES as PROMPT_STUDIO_ADVANCED_RETURN_NAMES,
        PROMPT_STUDIO_ADVANCED_RETURN_TYPES as PROMPT_STUDIO_ADVANCED_RETURN_TYPES,
        PROMPT_STUDIO_WILDCARD_SEED_CONTROL_ALIASES as PROMPT_STUDIO_WILDCARD_SEED_CONTROL_ALIASES,
        _advanced_artist_field_prompt as _advanced_artist_field_prompt,
        _advanced_default_fields as _advanced_default_fields,
        _advanced_enabled_naia_panes as _advanced_enabled_naia_panes,
        _advanced_enabled_pane_fields as _advanced_enabled_pane_fields,
        _advanced_field_input_values as _advanced_field_input_values,
        _advanced_field_socket_name as _advanced_field_socket_name,
        _advanced_fields_json as _advanced_fields_json,
        _advanced_fields_with_artist_override as _advanced_fields_with_artist_override,
        _advanced_has_enabled_naia as _advanced_has_enabled_naia,
        _advanced_pane_parts as _advanced_pane_parts,
        _advanced_prompt_data_fields as _advanced_prompt_data_fields,
        _advanced_prompt_with_artist_override as _advanced_prompt_with_artist_override,
        _advanced_uses_naia_resolution as _advanced_uses_naia_resolution,
        _apply_advanced_field_inputs as _apply_advanced_field_inputs,
        _as_advanced_height as _as_advanced_height,
        _bind_advanced_runtime as _bind_advanced_runtime,
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
        REGIONAL_CONFIG_VERSION as REGIONAL_CONFIG_VERSION,
        REGIONAL_CONFIG_WORKFLOW_PROPERTY as REGIONAL_CONFIG_WORKFLOW_PROPERTY,
        REGIONAL_FIELDS_WORKFLOW_PROPERTY as REGIONAL_FIELDS_WORKFLOW_PROPERTY,
        REGIONAL_FIELD_TYPES as REGIONAL_FIELD_TYPES,
        REGIONAL_PROMPT_BUNDLE_SCHEMA as REGIONAL_PROMPT_BUNDLE_SCHEMA,
        REGIONAL_PROMPT_DATA_SCHEMA as REGIONAL_PROMPT_DATA_SCHEMA,
        REGIONAL_PROMPT_DATA_TYPE as REGIONAL_PROMPT_DATA_TYPE,
        _apply_regional_field_inputs as _apply_regional_field_inputs,
        _bind_regional_runtime as _bind_regional_runtime,
        _build_regional_outputs as _build_regional_outputs,
        _clone_regional_fields as _clone_regional_fields,
        _conditioning_set_values as _conditioning_set_values,
        _normalize_mask_geometry as _normalize_mask_geometry,
        _normalize_mask_ids as _normalize_mask_ids,
        _normalize_regional_config as _normalize_regional_config,
        _normalize_regional_fields as _normalize_regional_fields,
        _normalize_regional_mask as _normalize_regional_mask,
        _parse_json_object as _parse_json_object,
        _regional_config_json as _regional_config_json,
        _regional_default_config as _regional_default_config,
        _regional_default_fields as _regional_default_fields,
        _regional_field_prompt as _regional_field_prompt,
        _regional_fields_json as _regional_fields_json,
        _regional_mask_bounds_area as _regional_mask_bounds_area,
        _regional_payload_canvas as _regional_payload_canvas,
        _regional_union_mask_for_ids as _regional_union_mask_for_ids,
    )
    from .easyuse_anima.prompt.conditioning import (
        ANIMA_MOD_GUIDANCE_DEFAULT_PROFILE as ANIMA_MOD_GUIDANCE_DEFAULT_PROFILE,
        ANIMA_MOD_GUIDANCE_MODES as ANIMA_MOD_GUIDANCE_MODES,
        ANIMA_MOD_GUIDANCE_MODE_DISABLED as ANIMA_MOD_GUIDANCE_MODE_DISABLED,
        ANIMA_MOD_GUIDANCE_MODE_ENABLED as ANIMA_MOD_GUIDANCE_MODE_ENABLED,
        ANIMA_MOD_GUIDANCE_MODE_FROM_PROMPT_DATA as ANIMA_MOD_GUIDANCE_MODE_FROM_PROMPT_DATA,
        ANIMA_MOD_GUIDANCE_PROFILES as ANIMA_MOD_GUIDANCE_PROFILES,
        ANIMA_MOD_GUIDANCE_PROFILE_OFF as ANIMA_MOD_GUIDANCE_PROFILE_OFF,
        _SPECTRUM_ANIMA_MOD_GUIDANCE_OLD_SIGNATURE_WARNED as _SPECTRUM_ANIMA_MOD_GUIDANCE_OLD_SIGNATURE_WARNED,
        _apply_spectrum_anima_mod_guidance as _apply_spectrum_anima_mod_guidance,
        _bind_conditioning_runtime as _bind_conditioning_runtime,
        _find_spectrum_anima_mod_guidance_class as _find_spectrum_anima_mod_guidance_class,
        _normalize_anima_mod_guidance_profile as _normalize_anima_mod_guidance_profile,
        _resolve_anima_mod_guidance_enabled as _resolve_anima_mod_guidance_enabled,
        _warn_old_spectrum_anima_mod_guidance_once as _warn_old_spectrum_anima_mod_guidance_once,
    )
    from .easyuse_anima.prompt.artist_mix import (
        ARTIST_MIX_CONTROL_KEY as ARTIST_MIX_CONTROL_KEY,
        ARTIST_MIX_DEFAULT_CLUSTER_COUNT as ARTIST_MIX_DEFAULT_CLUSTER_COUNT,
        ARTIST_MIX_DEFAULT_DOMINANT_ISOLATION as ARTIST_MIX_DEFAULT_DOMINANT_ISOLATION,
        ARTIST_MIX_DEFAULT_DOMINANT_THRESHOLD as ARTIST_MIX_DEFAULT_DOMINANT_THRESHOLD,
        ARTIST_MIX_DEFAULT_EXACT_TOP_K as ARTIST_MIX_DEFAULT_EXACT_TOP_K,
        ARTIST_MIX_DEFAULT_RMS_SCALE_CAP as ARTIST_MIX_DEFAULT_RMS_SCALE_CAP,
        ARTIST_MIX_DEFAULT_START_PERCENT as ARTIST_MIX_DEFAULT_START_PERCENT,
        ARTIST_MIX_DEFAULT_STRENGTH_SCALE as ARTIST_MIX_DEFAULT_STRENGTH_SCALE,
        ARTIST_MIX_DEFAULT_STYLE_GAIN as ARTIST_MIX_DEFAULT_STYLE_GAIN,
        ARTIST_MIX_EXACT_KEY as ARTIST_MIX_EXACT_KEY,
        ARTIST_MIX_INPUT_MODES as ARTIST_MIX_INPUT_MODES,
        ARTIST_MIX_MODES as ARTIST_MIX_MODES,
        ARTIST_MIX_MODE_AVERAGE as ARTIST_MIX_MODE_AVERAGE,
        ARTIST_MIX_MODE_AVERAGE_LATE_EXACT as ARTIST_MIX_MODE_AVERAGE_LATE_EXACT,
        ARTIST_MIX_MODE_CLUSTERED as ARTIST_MIX_MODE_CLUSTERED,
        ARTIST_MIX_MODE_COMPOSITE_EXACT as ARTIST_MIX_MODE_COMPOSITE_EXACT,
        ARTIST_MIX_MODE_DELTA_RMS as ARTIST_MIX_MODE_DELTA_RMS,
        ARTIST_MIX_MODE_DESCRIPTIONS as ARTIST_MIX_MODE_DESCRIPTIONS,
        ARTIST_MIX_MODE_EXACT as ARTIST_MIX_MODE_EXACT,
        ARTIST_MIX_MODE_FROM_PROMPT_DATA as ARTIST_MIX_MODE_FROM_PROMPT_DATA,
        ARTIST_MIX_MODE_HYBRID as ARTIST_MIX_MODE_HYBRID,
        ARTIST_MIX_MODE_LATE_EXACT as ARTIST_MIX_MODE_LATE_EXACT,
        ARTIST_MIX_MODE_OFF as ARTIST_MIX_MODE_OFF,
        ARTIST_MIX_MODE_PROMPT as ARTIST_MIX_MODE_PROMPT,
        ARTIST_MIX_MODE_SCHEDULED_AVERAGE as ARTIST_MIX_MODE_SCHEDULED_AVERAGE,
        ARTIST_MIX_SCHEDULE_KEY as ARTIST_MIX_SCHEDULE_KEY,
        ARTIST_MIX_STUDIO_MODES as ARTIST_MIX_STUDIO_MODES,
        ARTIST_TAG_POSITION_BACK as ARTIST_TAG_POSITION_BACK,
        ARTIST_TAG_POSITION_CORRECT as ARTIST_TAG_POSITION_CORRECT,
        ARTIST_TAG_POSITION_FRONT as ARTIST_TAG_POSITION_FRONT,
        ARTIST_TAG_POSITION_MODES as ARTIST_TAG_POSITION_MODES,
        _artist_conditioning_feature as _artist_conditioning_feature,
        _artist_delta_rms_from_encoded as _artist_delta_rms_from_encoded,
        _artist_group_token as _artist_group_token,
        _artist_mix_inline_prompt as _artist_mix_inline_prompt,
        _artist_mix_mode_tooltip as _artist_mix_mode_tooltip,
        _artist_mix_prompt_tags as _artist_mix_prompt_tags,
        _artist_prompt_with_position as _artist_prompt_with_position,
        _artist_tags_from_prompt as _artist_tags_from_prompt,
        _artist_variant_prompt_from_prompt_data as _artist_variant_prompt_from_prompt_data,
        _bind_artist_mix_runtime as _bind_artist_mix_runtime,
        _blend_conditionings as _blend_conditionings,
        _bounded_artist_mix_float as _bounded_artist_mix_float,
        _bounded_artist_mix_int as _bounded_artist_mix_int,
        _coalesce_artist_mix_items as _coalesce_artist_mix_items,
        _conditionings_with_range as _conditionings_with_range,
        _conditionings_with_strength as _conditionings_with_strength,
        _conditionings_with_values as _conditionings_with_values,
        _copy_conditioning_metadata as _copy_conditioning_metadata,
        _encode_artist_average as _encode_artist_average,
        _encode_artist_average_late_exact as _encode_artist_average_late_exact,
        _encode_artist_clustered as _encode_artist_clustered,
        _encode_artist_composite_exact as _encode_artist_composite_exact,
        _encode_artist_delta_rms as _encode_artist_delta_rms,
        _encode_artist_exact as _encode_artist_exact,
        _encode_artist_hybrid as _encode_artist_hybrid,
        _encode_artist_scheduled_average as _encode_artist_scheduled_average,
        _encode_prompt_data_positive_conditioning as _encode_prompt_data_positive_conditioning,
        _encoded_artist_conditionings as _encoded_artist_conditionings,
        _equal_artist_weights as _equal_artist_weights,
        _fallback_artist_average_or_exact as _fallback_artist_average_or_exact,
        _greedy_cluster_encoded_artists as _greedy_cluster_encoded_artists,
        _interpolate_artist_weights as _interpolate_artist_weights,
        _join_artist_mix_source_prompts as _join_artist_mix_source_prompts,
        _mark_artist_mix_conditioning as _mark_artist_mix_conditioning,
        _normalize_artist_mix_mode as _normalize_artist_mix_mode,
        _normalize_artist_tag_position as _normalize_artist_tag_position,
        _normalize_weight_values as _normalize_weight_values,
        _normalized_artist_weights as _normalized_artist_weights,
        _pad_conditioning_tensor as _pad_conditioning_tensor,
        _parse_artist_mix_entries as _parse_artist_mix_entries,
        _parse_artist_mix_group as _parse_artist_mix_group,
        _parse_artist_mix_items as _parse_artist_mix_items,
        _prompt_data_artist_base_prompt as _prompt_data_artist_base_prompt,
        _prompt_data_artist_mix_config as _prompt_data_artist_mix_config,
        _prompt_data_positive_fields as _prompt_data_positive_fields,
        _split_artist_mix_blocks as _split_artist_mix_blocks,
        _split_artist_mix_items as _split_artist_mix_items,
    )
    from .easyuse_anima.nodes.prompt_data_nodes import (
        EasyUseAnimaArtistMixConditioning as EasyUseAnimaArtistMixConditioning,
        EasyUseAnimaPromptDataConditioning as EasyUseAnimaPromptDataConditioning,
        EasyUseAnimaPromptDataUnpack as EasyUseAnimaPromptDataUnpack,
        _bind_prompt_data_node_runtime as _bind_prompt_data_node_runtime,
    )
    from .easyuse_anima.nodes.prompt_advanced_nodes import (
        EasyUseAnimaPromptStudioAdvanced as EasyUseAnimaPromptStudioAdvanced,
        EasyUseAnimaPromptStudioAdvancedV2 as EasyUseAnimaPromptStudioAdvancedV2,
        EasyUseAnimaPromptStudioExtend as EasyUseAnimaPromptStudioExtend,
        _bind_prompt_advanced_node_runtime as _bind_prompt_advanced_node_runtime,
    )
    from .easyuse_anima.image.geometry import (
        _align_down as _align_down,
        _align_nearest as _align_nearest,
        _align_up as _align_up,
        _aligned_size_near_scale as _aligned_size_near_scale,
        _alignment_value as _alignment_value,
    )
    from .easyuse_anima.image.detailer import (
        _EasyUseAnimaAlignedDetailerHook as _EasyUseAnimaAlignedDetailerHook,
    )
    from .easyuse_anima.image.sam3 import (
        _bind_sam3_runtime as _bind_sam3_runtime,
        _call_impact_detailer as _call_impact_detailer,
        _context_value as _context_value,
        _empty_mask_for_image as _empty_mask_for_image,
        _empty_segs_for_image as _empty_segs_for_image,
        _find_impact_detailer_class as _find_impact_detailer_class,
        _find_impact_mask_to_segs_class as _find_impact_mask_to_segs_class,
        _find_sam3_detect_class as _find_sam3_detect_class,
        _format_sam3_detection_prompt as _format_sam3_detection_prompt,
        _sam3_context as _sam3_context,
        _segs_has_items as _segs_has_items,
    )
    from .easyuse_anima.image.scaling import (
        IMAGE_SCALE_MULTIPLES as IMAGE_SCALE_MULTIPLES,
        IMAGE_UPSCALE_METHODS as IMAGE_UPSCALE_METHODS,
        _image_scale_by_multiple_size as _image_scale_by_multiple_size,
        _max_long_edge_value as _max_long_edge_value,
        _normalize_image_scale_options as _normalize_image_scale_options,
        _scale_by_value as _scale_by_value,
    )
    from .easyuse_anima.infrastructure.comfy.capabilities import (
        _comfy_max_resolution as _adapter_comfy_max_resolution,
        _comfy_sampler_names as _comfy_sampler_names,
        _comfy_scheduler_names as _comfy_scheduler_names,
        _find_comfy_node_class as _adapter_find_comfy_node_class,
        _find_loaded_node_class as _adapter_find_loaded_node_class,
        _impact_core_module as _impact_core_module,
        _impact_scheduler_names as _impact_scheduler_names,
        _require_any_custom_node_class as _adapter_require_any_custom_node_class,
        _require_custom_node_class as _adapter_require_custom_node_class,
    )
    from .easyuse_anima.infrastructure.comfy.invocation import (
        _call_with_supported_kwargs as _call_with_supported_kwargs,
        _common_upscale_image as _common_upscale_image,
        _encode_with_comfy_clip as _adapter_encode_with_comfy_clip,
        _node_output_tuple as _node_output_tuple,
    )
    from .easyuse_anima.infrastructure.comfy.resources import (
        _comfy_checkpoint_names as _comfy_checkpoint_names,
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
    from .easyuse_anima.nodes.impact_detailer_nodes import (
        _EasyUseAnimaImpactDetailerDelegate as _EasyUseAnimaImpactDetailerDelegate,
        _bind_impact_detailer_node_runtime as _bind_impact_detailer_node_runtime,
    )
    from .easyuse_anima.nodes.sam3_nodes import (
        EasyUseAnimaSAM3Context as EasyUseAnimaSAM3Context,
        EasyUseAnimaSAM3Detailer as EasyUseAnimaSAM3Detailer,
        _bind_sam3_node_runtime as _bind_sam3_node_runtime,
    )
    from .easyuse_anima.nodes.prompt_nodes import (
        EasyUseAnimaPromptBuilder as EasyUseAnimaPromptBuilder,
        EasyUseAnimaPromptCorrector as EasyUseAnimaPromptCorrector,
        EasyUseAnimaPromptCorrectorSimple as EasyUseAnimaPromptCorrectorSimple,
        EasyUseAnimaPromptStudio as EasyUseAnimaPromptStudio,
        _bind_prompt_node_runtime as _bind_prompt_node_runtime,
    )
    from .easyuse_anima.nodes.regional_nodes import (
        EasyUseAnimaPromptStudioRegional as EasyUseAnimaPromptStudioRegional,
        EasyUseAnimaRegionalConditioning as EasyUseAnimaRegionalConditioning,
        _bind_regional_node_runtime as _bind_regional_node_runtime,
    )
    from .easyuse_anima.naia.client import (
        DEFAULT_HOST as DEFAULT_HOST,
        DEFAULT_PORT as DEFAULT_PORT,
        HTTP_TIMEOUT as HTTP_TIMEOUT,
        LATENT_ALIGN as LATENT_ALIGN,
        NAI_1MP as NAI_1MP,
        NAIA_LOCAL_HOSTS as NAIA_LOCAL_HOSTS,
        NAIA_MAX_RESOLUTION as NAIA_MAX_RESOLUTION,
        NAIA_REQUEST_TIMEOUT as NAIA_REQUEST_TIMEOUT,
        PP_STATE_CHOICES as PP_STATE_CHOICES,
        PREPROCESSING_KEYS as PREPROCESSING_KEYS,
        _build_naia_random_url as _build_naia_random_url,
        _clean_prompt as _clean_prompt,
        _fit_to_1mp as _fit_to_1mp,
        _is_local_naia_host as _is_local_naia_host,
        _parse_random_response as _parse_random_response,
        _post_random as _post_random,
    )
    from .easyuse_anima.naia.resolution import (
        ADVANCED_RESOLUTION_BUCKETS as ADVANCED_RESOLUTION_BUCKETS,
        CUSTOM_ADVANCED_RESOLUTION_BUCKET as CUSTOM_ADVANCED_RESOLUTION_BUCKET,
        DEFAULT_ADVANCED_RESOLUTION_BUCKET as DEFAULT_ADVANCED_RESOLUTION_BUCKET,
        DEFAULT_ADVANCED_RESOLUTION_SIZE as DEFAULT_ADVANCED_RESOLUTION_SIZE,
        NAIA_ADVANCED_RESOLUTION_BUCKET as NAIA_ADVANCED_RESOLUTION_BUCKET,
        NAIA_RESOLUTION_MODE_BUCKET as NAIA_RESOLUTION_MODE_BUCKET,
        NAIA_RESOLUTION_MODE_SCALE as NAIA_RESOLUTION_MODE_SCALE,
        _advanced_resolution_from_selection as _advanced_resolution_from_selection,
        _fit_naia_resolution_to_bucket as _fit_naia_resolution_to_bucket,
        _normalize_resolution_bucket as _normalize_resolution_bucket,
        _ratio_label as _ratio_label,
        _resolution_label as _resolution_label,
        _resolve_naia_resolution as _resolve_naia_resolution,
        _resolve_naia_resolution_bucket as _resolve_naia_resolution_bucket,
        _resolve_naia_resolution_max_long_edge as _resolve_naia_resolution_max_long_edge,
        _resolve_naia_resolution_mode as _resolve_naia_resolution_mode,
        _resolve_naia_resolution_scale as _resolve_naia_resolution_scale,
        _scale_naia_resolution as _scale_naia_resolution,
        _snap_resolution_32 as _snap_resolution_32,
        _snap_scaled_resolution_32 as _snap_scaled_resolution_32,
        _sorted_resolution_options as _sorted_resolution_options,
    )
    from .easyuse_anima.nodes.naia_nodes import (
        EasyUseAnimaNAIARandomPrompt as EasyUseAnimaNAIARandomPrompt,
        _bind_naia_node_runtime as _bind_naia_node_runtime,
    )
    from .easyuse_anima.nodes.wildcard_nodes import (
        EasyUseAnimaWildcard as EasyUseAnimaWildcard,
        WILDCARD_SEED_RANGE_NOTE as WILDCARD_SEED_RANGE_NOTE,
        _bind_wildcard_node_runtime as _bind_wildcard_node_runtime,
    )
    from .easyuse_anima.lora.metadata import (
        _apply_lora_syntax_format as _apply_lora_syntax_format,
        _bind_lora_metadata_runtime as _bind_lora_metadata_runtime,
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
        _bind_lora_preset_runtime as _bind_lora_preset_runtime,
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
        _bind_lora_node_runtime as _bind_lora_node_runtime,
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
    from easyuse_anima.aio.generation_normalization import (
        _bind_aio_generation_normalization_runtime as _bind_aio_generation_normalization_runtime,
        _merge_versioned_settings as _merge_versioned_settings,
        _normalize_aio_generation_settings as _normalize_aio_generation_settings,
    )
    from easyuse_anima.aio.generation_settings import (
        round_trip_aio_generation_settings as _round_trip_aio_generation_settings,
    )
    from easyuse_anima.aio.conditioning import (
        _aio_prompt_data_fields_for_usdu as _aio_prompt_data_fields_for_usdu,
        _aio_usdu_conditioning as _aio_usdu_conditioning,
        _aio_usdu_prompt_without_general as _aio_usdu_prompt_without_general,
        _bind_aio_conditioning_runtime as _bind_aio_conditioning_runtime,
    )
    from easyuse_anima.aio.model_preparation import (
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
        _load_aio_resources_from_input_context as _load_aio_resources_from_input_context,
        _load_aio_sam3_context as _load_aio_sam3_context,
        _load_checkpoint_with_comfy as _load_checkpoint_with_comfy,
        _load_clip_with_comfy as _load_clip_with_comfy,
        _load_diffusion_model_with_comfy as _load_diffusion_model_with_comfy,
        _load_upscale_model_with_comfy as _load_upscale_model_with_comfy,
        _load_vae_with_comfy as _load_vae_with_comfy,
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
    from easyuse_anima.prompt.correction import (
        _bind_prompt_correction_runtime as _bind_prompt_correction_runtime,
        _prompt_translation_change_key as _prompt_translation_change_key,
        _split_tag_text as _split_tag_text,
        _translate_prompt_text as _translate_prompt_text,
    )
    from easyuse_anima.prompt.fields import (
        DEFAULT_QUALITY_TAGS as DEFAULT_QUALITY_TAGS,
        DEFAULT_TRAILING_QUALITY_TAGS as DEFAULT_TRAILING_QUALITY_TAGS,
        _HASH_COMMENT_RE as _HASH_COMMENT_RE,
        _INLINE_SPACE_RE as _INLINE_SPACE_RE,
        _WEIGHTED_TOKEN_RE as _WEIGHTED_TOKEN_RE,
        _bind_prompt_fields_runtime as _bind_prompt_fields_runtime,
        _correct_builder_prompt as _correct_builder_prompt,
        _filter_metadata_prompt as _filter_metadata_prompt,
        _join_prompt_tokens as _join_prompt_tokens,
        _metadata_filter_key as _metadata_filter_key,
        _metadata_filter_keys as _metadata_filter_keys,
        _prompt_tokens as _prompt_tokens,
    )
    from easyuse_anima.prompt.data import (
        PROMPT_DATA_COMPAT_OUTPUT_TOOLTIPS as PROMPT_DATA_COMPAT_OUTPUT_TOOLTIPS,
        PROMPT_DATA_COMPAT_RETURN_NAMES as PROMPT_DATA_COMPAT_RETURN_NAMES,
        PROMPT_DATA_COMPAT_RETURN_TYPES as PROMPT_DATA_COMPAT_RETURN_TYPES,
        PROMPT_DATA_SCHEMA as PROMPT_DATA_SCHEMA,
        PROMPT_DATA_TYPE as PROMPT_DATA_TYPE,
        PROMPT_DATA_VERSION as PROMPT_DATA_VERSION,
        _advanced_outputs_from_prompt_data as _advanced_outputs_from_prompt_data,
        _apply_prompt_data_overrides as _apply_prompt_data_overrides,
        _copy_prompt_data_for_update as _copy_prompt_data_for_update,
        _normalize_prompt_data as _normalize_prompt_data,
        _prompt_data_input_default as _prompt_data_input_default,
        _prompt_data_json_safe as _prompt_data_json_safe,
        _prompt_data_nested as _prompt_data_nested,
        _prompt_data_output as _prompt_data_output,
        _prompt_data_parameter_snapshot as _prompt_data_parameter_snapshot,
        _set_prompt_data_output as _set_prompt_data_output,
    )
    from easyuse_anima.prompt.advanced import (
        ADVANCED_FIELDS_WORKFLOW_PROPERTY as ADVANCED_FIELDS_WORKFLOW_PROPERTY,
        ADVANCED_FIELD_LABELS as ADVANCED_FIELD_LABELS,
        ADVANCED_FIELD_PANES as ADVANCED_FIELD_PANES,
        ADVANCED_FIELD_TYPES as ADVANCED_FIELD_TYPES,
        EXTEND_PROMPT_SLOT_SPECS as EXTEND_PROMPT_SLOT_SPECS,
        PROMPT_STUDIO_LEGACY_FIXED_WILDCARD_MODES as PROMPT_STUDIO_LEGACY_FIXED_WILDCARD_MODES,
        PROMPT_STUDIO_ADVANCED_RETURN_NAMES as PROMPT_STUDIO_ADVANCED_RETURN_NAMES,
        PROMPT_STUDIO_ADVANCED_RETURN_TYPES as PROMPT_STUDIO_ADVANCED_RETURN_TYPES,
        PROMPT_STUDIO_WILDCARD_SEED_CONTROL_ALIASES as PROMPT_STUDIO_WILDCARD_SEED_CONTROL_ALIASES,
        _advanced_artist_field_prompt as _advanced_artist_field_prompt,
        _advanced_default_fields as _advanced_default_fields,
        _advanced_enabled_naia_panes as _advanced_enabled_naia_panes,
        _advanced_enabled_pane_fields as _advanced_enabled_pane_fields,
        _advanced_field_input_values as _advanced_field_input_values,
        _advanced_field_socket_name as _advanced_field_socket_name,
        _advanced_fields_json as _advanced_fields_json,
        _advanced_fields_with_artist_override as _advanced_fields_with_artist_override,
        _advanced_has_enabled_naia as _advanced_has_enabled_naia,
        _advanced_pane_parts as _advanced_pane_parts,
        _advanced_prompt_data_fields as _advanced_prompt_data_fields,
        _advanced_prompt_with_artist_override as _advanced_prompt_with_artist_override,
        _advanced_uses_naia_resolution as _advanced_uses_naia_resolution,
        _apply_advanced_field_inputs as _apply_advanced_field_inputs,
        _as_advanced_height as _as_advanced_height,
        _bind_advanced_runtime as _bind_advanced_runtime,
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
        REGIONAL_CONFIG_VERSION as REGIONAL_CONFIG_VERSION,
        REGIONAL_CONFIG_WORKFLOW_PROPERTY as REGIONAL_CONFIG_WORKFLOW_PROPERTY,
        REGIONAL_FIELDS_WORKFLOW_PROPERTY as REGIONAL_FIELDS_WORKFLOW_PROPERTY,
        REGIONAL_FIELD_TYPES as REGIONAL_FIELD_TYPES,
        REGIONAL_PROMPT_BUNDLE_SCHEMA as REGIONAL_PROMPT_BUNDLE_SCHEMA,
        REGIONAL_PROMPT_DATA_SCHEMA as REGIONAL_PROMPT_DATA_SCHEMA,
        REGIONAL_PROMPT_DATA_TYPE as REGIONAL_PROMPT_DATA_TYPE,
        _apply_regional_field_inputs as _apply_regional_field_inputs,
        _bind_regional_runtime as _bind_regional_runtime,
        _build_regional_outputs as _build_regional_outputs,
        _clone_regional_fields as _clone_regional_fields,
        _conditioning_set_values as _conditioning_set_values,
        _normalize_mask_geometry as _normalize_mask_geometry,
        _normalize_mask_ids as _normalize_mask_ids,
        _normalize_regional_config as _normalize_regional_config,
        _normalize_regional_fields as _normalize_regional_fields,
        _normalize_regional_mask as _normalize_regional_mask,
        _parse_json_object as _parse_json_object,
        _regional_config_json as _regional_config_json,
        _regional_default_config as _regional_default_config,
        _regional_default_fields as _regional_default_fields,
        _regional_field_prompt as _regional_field_prompt,
        _regional_fields_json as _regional_fields_json,
        _regional_mask_bounds_area as _regional_mask_bounds_area,
        _regional_payload_canvas as _regional_payload_canvas,
        _regional_union_mask_for_ids as _regional_union_mask_for_ids,
    )
    from easyuse_anima.prompt.conditioning import (
        ANIMA_MOD_GUIDANCE_DEFAULT_PROFILE as ANIMA_MOD_GUIDANCE_DEFAULT_PROFILE,
        ANIMA_MOD_GUIDANCE_MODES as ANIMA_MOD_GUIDANCE_MODES,
        ANIMA_MOD_GUIDANCE_MODE_DISABLED as ANIMA_MOD_GUIDANCE_MODE_DISABLED,
        ANIMA_MOD_GUIDANCE_MODE_ENABLED as ANIMA_MOD_GUIDANCE_MODE_ENABLED,
        ANIMA_MOD_GUIDANCE_MODE_FROM_PROMPT_DATA as ANIMA_MOD_GUIDANCE_MODE_FROM_PROMPT_DATA,
        ANIMA_MOD_GUIDANCE_PROFILES as ANIMA_MOD_GUIDANCE_PROFILES,
        ANIMA_MOD_GUIDANCE_PROFILE_OFF as ANIMA_MOD_GUIDANCE_PROFILE_OFF,
        _SPECTRUM_ANIMA_MOD_GUIDANCE_OLD_SIGNATURE_WARNED as _SPECTRUM_ANIMA_MOD_GUIDANCE_OLD_SIGNATURE_WARNED,
        _apply_spectrum_anima_mod_guidance as _apply_spectrum_anima_mod_guidance,
        _bind_conditioning_runtime as _bind_conditioning_runtime,
        _find_spectrum_anima_mod_guidance_class as _find_spectrum_anima_mod_guidance_class,
        _normalize_anima_mod_guidance_profile as _normalize_anima_mod_guidance_profile,
        _resolve_anima_mod_guidance_enabled as _resolve_anima_mod_guidance_enabled,
        _warn_old_spectrum_anima_mod_guidance_once as _warn_old_spectrum_anima_mod_guidance_once,
    )
    from easyuse_anima.prompt.artist_mix import (
        ARTIST_MIX_CONTROL_KEY as ARTIST_MIX_CONTROL_KEY,
        ARTIST_MIX_DEFAULT_CLUSTER_COUNT as ARTIST_MIX_DEFAULT_CLUSTER_COUNT,
        ARTIST_MIX_DEFAULT_DOMINANT_ISOLATION as ARTIST_MIX_DEFAULT_DOMINANT_ISOLATION,
        ARTIST_MIX_DEFAULT_DOMINANT_THRESHOLD as ARTIST_MIX_DEFAULT_DOMINANT_THRESHOLD,
        ARTIST_MIX_DEFAULT_EXACT_TOP_K as ARTIST_MIX_DEFAULT_EXACT_TOP_K,
        ARTIST_MIX_DEFAULT_RMS_SCALE_CAP as ARTIST_MIX_DEFAULT_RMS_SCALE_CAP,
        ARTIST_MIX_DEFAULT_START_PERCENT as ARTIST_MIX_DEFAULT_START_PERCENT,
        ARTIST_MIX_DEFAULT_STRENGTH_SCALE as ARTIST_MIX_DEFAULT_STRENGTH_SCALE,
        ARTIST_MIX_DEFAULT_STYLE_GAIN as ARTIST_MIX_DEFAULT_STYLE_GAIN,
        ARTIST_MIX_EXACT_KEY as ARTIST_MIX_EXACT_KEY,
        ARTIST_MIX_INPUT_MODES as ARTIST_MIX_INPUT_MODES,
        ARTIST_MIX_MODES as ARTIST_MIX_MODES,
        ARTIST_MIX_MODE_AVERAGE as ARTIST_MIX_MODE_AVERAGE,
        ARTIST_MIX_MODE_AVERAGE_LATE_EXACT as ARTIST_MIX_MODE_AVERAGE_LATE_EXACT,
        ARTIST_MIX_MODE_CLUSTERED as ARTIST_MIX_MODE_CLUSTERED,
        ARTIST_MIX_MODE_COMPOSITE_EXACT as ARTIST_MIX_MODE_COMPOSITE_EXACT,
        ARTIST_MIX_MODE_DELTA_RMS as ARTIST_MIX_MODE_DELTA_RMS,
        ARTIST_MIX_MODE_DESCRIPTIONS as ARTIST_MIX_MODE_DESCRIPTIONS,
        ARTIST_MIX_MODE_EXACT as ARTIST_MIX_MODE_EXACT,
        ARTIST_MIX_MODE_FROM_PROMPT_DATA as ARTIST_MIX_MODE_FROM_PROMPT_DATA,
        ARTIST_MIX_MODE_HYBRID as ARTIST_MIX_MODE_HYBRID,
        ARTIST_MIX_MODE_LATE_EXACT as ARTIST_MIX_MODE_LATE_EXACT,
        ARTIST_MIX_MODE_OFF as ARTIST_MIX_MODE_OFF,
        ARTIST_MIX_MODE_PROMPT as ARTIST_MIX_MODE_PROMPT,
        ARTIST_MIX_MODE_SCHEDULED_AVERAGE as ARTIST_MIX_MODE_SCHEDULED_AVERAGE,
        ARTIST_MIX_SCHEDULE_KEY as ARTIST_MIX_SCHEDULE_KEY,
        ARTIST_MIX_STUDIO_MODES as ARTIST_MIX_STUDIO_MODES,
        ARTIST_TAG_POSITION_BACK as ARTIST_TAG_POSITION_BACK,
        ARTIST_TAG_POSITION_CORRECT as ARTIST_TAG_POSITION_CORRECT,
        ARTIST_TAG_POSITION_FRONT as ARTIST_TAG_POSITION_FRONT,
        ARTIST_TAG_POSITION_MODES as ARTIST_TAG_POSITION_MODES,
        _artist_conditioning_feature as _artist_conditioning_feature,
        _artist_delta_rms_from_encoded as _artist_delta_rms_from_encoded,
        _artist_group_token as _artist_group_token,
        _artist_mix_inline_prompt as _artist_mix_inline_prompt,
        _artist_mix_mode_tooltip as _artist_mix_mode_tooltip,
        _artist_mix_prompt_tags as _artist_mix_prompt_tags,
        _artist_prompt_with_position as _artist_prompt_with_position,
        _artist_tags_from_prompt as _artist_tags_from_prompt,
        _artist_variant_prompt_from_prompt_data as _artist_variant_prompt_from_prompt_data,
        _bind_artist_mix_runtime as _bind_artist_mix_runtime,
        _blend_conditionings as _blend_conditionings,
        _bounded_artist_mix_float as _bounded_artist_mix_float,
        _bounded_artist_mix_int as _bounded_artist_mix_int,
        _coalesce_artist_mix_items as _coalesce_artist_mix_items,
        _conditionings_with_range as _conditionings_with_range,
        _conditionings_with_strength as _conditionings_with_strength,
        _conditionings_with_values as _conditionings_with_values,
        _copy_conditioning_metadata as _copy_conditioning_metadata,
        _encode_artist_average as _encode_artist_average,
        _encode_artist_average_late_exact as _encode_artist_average_late_exact,
        _encode_artist_clustered as _encode_artist_clustered,
        _encode_artist_composite_exact as _encode_artist_composite_exact,
        _encode_artist_delta_rms as _encode_artist_delta_rms,
        _encode_artist_exact as _encode_artist_exact,
        _encode_artist_hybrid as _encode_artist_hybrid,
        _encode_artist_scheduled_average as _encode_artist_scheduled_average,
        _encode_prompt_data_positive_conditioning as _encode_prompt_data_positive_conditioning,
        _encoded_artist_conditionings as _encoded_artist_conditionings,
        _equal_artist_weights as _equal_artist_weights,
        _fallback_artist_average_or_exact as _fallback_artist_average_or_exact,
        _greedy_cluster_encoded_artists as _greedy_cluster_encoded_artists,
        _interpolate_artist_weights as _interpolate_artist_weights,
        _join_artist_mix_source_prompts as _join_artist_mix_source_prompts,
        _mark_artist_mix_conditioning as _mark_artist_mix_conditioning,
        _normalize_artist_mix_mode as _normalize_artist_mix_mode,
        _normalize_artist_tag_position as _normalize_artist_tag_position,
        _normalize_weight_values as _normalize_weight_values,
        _normalized_artist_weights as _normalized_artist_weights,
        _pad_conditioning_tensor as _pad_conditioning_tensor,
        _parse_artist_mix_entries as _parse_artist_mix_entries,
        _parse_artist_mix_group as _parse_artist_mix_group,
        _parse_artist_mix_items as _parse_artist_mix_items,
        _prompt_data_artist_base_prompt as _prompt_data_artist_base_prompt,
        _prompt_data_artist_mix_config as _prompt_data_artist_mix_config,
        _prompt_data_positive_fields as _prompt_data_positive_fields,
        _split_artist_mix_blocks as _split_artist_mix_blocks,
        _split_artist_mix_items as _split_artist_mix_items,
    )
    from easyuse_anima.nodes.prompt_data_nodes import (
        EasyUseAnimaArtistMixConditioning as EasyUseAnimaArtistMixConditioning,
        EasyUseAnimaPromptDataConditioning as EasyUseAnimaPromptDataConditioning,
        EasyUseAnimaPromptDataUnpack as EasyUseAnimaPromptDataUnpack,
        _bind_prompt_data_node_runtime as _bind_prompt_data_node_runtime,
    )
    from easyuse_anima.nodes.prompt_advanced_nodes import (
        EasyUseAnimaPromptStudioAdvanced as EasyUseAnimaPromptStudioAdvanced,
        EasyUseAnimaPromptStudioAdvancedV2 as EasyUseAnimaPromptStudioAdvancedV2,
        EasyUseAnimaPromptStudioExtend as EasyUseAnimaPromptStudioExtend,
        _bind_prompt_advanced_node_runtime as _bind_prompt_advanced_node_runtime,
    )
    from easyuse_anima.image.geometry import (
        _align_down as _align_down,
        _align_nearest as _align_nearest,
        _align_up as _align_up,
        _aligned_size_near_scale as _aligned_size_near_scale,
        _alignment_value as _alignment_value,
    )
    from easyuse_anima.image.detailer import (
        _EasyUseAnimaAlignedDetailerHook as _EasyUseAnimaAlignedDetailerHook,
    )
    from easyuse_anima.image.sam3 import (
        _bind_sam3_runtime as _bind_sam3_runtime,
        _call_impact_detailer as _call_impact_detailer,
        _context_value as _context_value,
        _empty_mask_for_image as _empty_mask_for_image,
        _empty_segs_for_image as _empty_segs_for_image,
        _find_impact_detailer_class as _find_impact_detailer_class,
        _find_impact_mask_to_segs_class as _find_impact_mask_to_segs_class,
        _find_sam3_detect_class as _find_sam3_detect_class,
        _format_sam3_detection_prompt as _format_sam3_detection_prompt,
        _sam3_context as _sam3_context,
        _segs_has_items as _segs_has_items,
    )
    from easyuse_anima.image.scaling import (
        IMAGE_SCALE_MULTIPLES as IMAGE_SCALE_MULTIPLES,
        IMAGE_UPSCALE_METHODS as IMAGE_UPSCALE_METHODS,
        _image_scale_by_multiple_size as _image_scale_by_multiple_size,
        _max_long_edge_value as _max_long_edge_value,
        _normalize_image_scale_options as _normalize_image_scale_options,
        _scale_by_value as _scale_by_value,
    )
    from easyuse_anima.infrastructure.comfy.capabilities import (
        _comfy_max_resolution as _adapter_comfy_max_resolution,
        _comfy_sampler_names as _comfy_sampler_names,
        _comfy_scheduler_names as _comfy_scheduler_names,
        _find_comfy_node_class as _adapter_find_comfy_node_class,
        _find_loaded_node_class as _adapter_find_loaded_node_class,
        _impact_core_module as _impact_core_module,
        _impact_scheduler_names as _impact_scheduler_names,
        _require_any_custom_node_class as _adapter_require_any_custom_node_class,
        _require_custom_node_class as _adapter_require_custom_node_class,
    )
    from easyuse_anima.infrastructure.comfy.invocation import (
        _call_with_supported_kwargs as _call_with_supported_kwargs,
        _common_upscale_image as _common_upscale_image,
        _encode_with_comfy_clip as _adapter_encode_with_comfy_clip,
        _node_output_tuple as _node_output_tuple,
    )
    from easyuse_anima.infrastructure.comfy.resources import (
        _comfy_checkpoint_names as _comfy_checkpoint_names,
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
    from easyuse_anima.nodes.impact_detailer_nodes import (
        _EasyUseAnimaImpactDetailerDelegate as _EasyUseAnimaImpactDetailerDelegate,
        _bind_impact_detailer_node_runtime as _bind_impact_detailer_node_runtime,
    )
    from easyuse_anima.nodes.sam3_nodes import (
        EasyUseAnimaSAM3Context as EasyUseAnimaSAM3Context,
        EasyUseAnimaSAM3Detailer as EasyUseAnimaSAM3Detailer,
        _bind_sam3_node_runtime as _bind_sam3_node_runtime,
    )
    from easyuse_anima.nodes.prompt_nodes import (
        EasyUseAnimaPromptBuilder as EasyUseAnimaPromptBuilder,
        EasyUseAnimaPromptCorrector as EasyUseAnimaPromptCorrector,
        EasyUseAnimaPromptCorrectorSimple as EasyUseAnimaPromptCorrectorSimple,
        EasyUseAnimaPromptStudio as EasyUseAnimaPromptStudio,
        _bind_prompt_node_runtime as _bind_prompt_node_runtime,
    )
    from easyuse_anima.nodes.regional_nodes import (
        EasyUseAnimaPromptStudioRegional as EasyUseAnimaPromptStudioRegional,
        EasyUseAnimaRegionalConditioning as EasyUseAnimaRegionalConditioning,
        _bind_regional_node_runtime as _bind_regional_node_runtime,
    )
    from easyuse_anima.naia.client import (
        DEFAULT_HOST as DEFAULT_HOST,
        DEFAULT_PORT as DEFAULT_PORT,
        HTTP_TIMEOUT as HTTP_TIMEOUT,
        LATENT_ALIGN as LATENT_ALIGN,
        NAI_1MP as NAI_1MP,
        NAIA_LOCAL_HOSTS as NAIA_LOCAL_HOSTS,
        NAIA_MAX_RESOLUTION as NAIA_MAX_RESOLUTION,
        NAIA_REQUEST_TIMEOUT as NAIA_REQUEST_TIMEOUT,
        PP_STATE_CHOICES as PP_STATE_CHOICES,
        PREPROCESSING_KEYS as PREPROCESSING_KEYS,
        _build_naia_random_url as _build_naia_random_url,
        _clean_prompt as _clean_prompt,
        _fit_to_1mp as _fit_to_1mp,
        _is_local_naia_host as _is_local_naia_host,
        _parse_random_response as _parse_random_response,
        _post_random as _post_random,
    )
    from easyuse_anima.naia.resolution import (
        ADVANCED_RESOLUTION_BUCKETS as ADVANCED_RESOLUTION_BUCKETS,
        CUSTOM_ADVANCED_RESOLUTION_BUCKET as CUSTOM_ADVANCED_RESOLUTION_BUCKET,
        DEFAULT_ADVANCED_RESOLUTION_BUCKET as DEFAULT_ADVANCED_RESOLUTION_BUCKET,
        DEFAULT_ADVANCED_RESOLUTION_SIZE as DEFAULT_ADVANCED_RESOLUTION_SIZE,
        NAIA_ADVANCED_RESOLUTION_BUCKET as NAIA_ADVANCED_RESOLUTION_BUCKET,
        NAIA_RESOLUTION_MODE_BUCKET as NAIA_RESOLUTION_MODE_BUCKET,
        NAIA_RESOLUTION_MODE_SCALE as NAIA_RESOLUTION_MODE_SCALE,
        _advanced_resolution_from_selection as _advanced_resolution_from_selection,
        _fit_naia_resolution_to_bucket as _fit_naia_resolution_to_bucket,
        _normalize_resolution_bucket as _normalize_resolution_bucket,
        _ratio_label as _ratio_label,
        _resolution_label as _resolution_label,
        _resolve_naia_resolution as _resolve_naia_resolution,
        _resolve_naia_resolution_bucket as _resolve_naia_resolution_bucket,
        _resolve_naia_resolution_max_long_edge as _resolve_naia_resolution_max_long_edge,
        _resolve_naia_resolution_mode as _resolve_naia_resolution_mode,
        _resolve_naia_resolution_scale as _resolve_naia_resolution_scale,
        _scale_naia_resolution as _scale_naia_resolution,
        _snap_resolution_32 as _snap_resolution_32,
        _snap_scaled_resolution_32 as _snap_scaled_resolution_32,
        _sorted_resolution_options as _sorted_resolution_options,
    )
    from easyuse_anima.nodes.naia_nodes import (
        EasyUseAnimaNAIARandomPrompt as EasyUseAnimaNAIARandomPrompt,
        _bind_naia_node_runtime as _bind_naia_node_runtime,
    )
    from easyuse_anima.nodes.wildcard_nodes import (
        EasyUseAnimaWildcard as EasyUseAnimaWildcard,
        WILDCARD_SEED_RANGE_NOTE as WILDCARD_SEED_RANGE_NOTE,
        _bind_wildcard_node_runtime as _bind_wildcard_node_runtime,
    )
    from easyuse_anima.lora.metadata import (
        _apply_lora_syntax_format as _apply_lora_syntax_format,
        _bind_lora_metadata_runtime as _bind_lora_metadata_runtime,
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
        _bind_lora_preset_runtime as _bind_lora_preset_runtime,
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
        _bind_lora_node_runtime as _bind_lora_node_runtime,
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
AIO_SPECIAL_SEED_RANDOM = -1
AIO_SPECIAL_SEED_INCREMENT = -2
AIO_SPECIAL_SEED_DECREMENT = -3
AIO_SPECIAL_SEEDS = {
    AIO_SPECIAL_SEED_RANDOM,
    AIO_SPECIAL_SEED_INCREMENT,
    AIO_SPECIAL_SEED_DECREMENT,
}
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
class _AnyType(str):
    def __ne__(self, __value: object) -> bool:
        return False


class _FlexibleOptionalInputType(dict):
    def __init__(self, input_type):
        self.input_type = input_type

    def __getitem__(self, key):
        return (self.input_type,)

    def __contains__(self, key):
        return True


_ANY_TYPE = _AnyType("*")


def _normalize_aio_seed(value, default: int = AIO_SPECIAL_SEED_RANDOM) -> int:
    return max(AIO_SPECIAL_SEED_DECREMENT, min(MAX_SEED, _as_int(value, default)))


def _new_aio_random_seed() -> int:
    return random.randint(0, MAX_SEED)


def _resolve_aio_runtime_seed(value) -> int:
    seed = _normalize_aio_seed(value)
    if seed in AIO_SPECIAL_SEEDS:
        return _new_aio_random_seed()
    return max(0, min(MAX_SEED, seed))






def _settings_json(defaults: dict[str, Any]) -> str:
    return json.dumps(defaults, ensure_ascii=False, indent=2)


def _normalize_aio_input_settings(value) -> dict[str, Any]:
    settings = _merge_versioned_settings(AIO_INPUT_DEFAULT_SETTINGS, value)
    settings["schema"] = EASY_USE_ANIMA_INPUT_SCHEMA
    settings["version"] = _as_int(
        settings.get("version"),
        EASY_USE_ANIMA_INPUT_SETTINGS_VERSION,
    )
    resources = settings.setdefault("resources", {})
    if not isinstance(resources, dict):
        resources = {}
        settings["resources"] = resources
    resources["loader_mode"] = "split"
    resources["clip_loader"] = _choice(resources.get("clip_loader"), ("single",), "single")
    resources["unet_weight_dtype"] = _choice(
        resources.get("unet_weight_dtype"),
        ANIMA_UNET_WEIGHT_DTYPES,
        "default",
    )
    resources["clip_device"] = _choice(
        resources.get("clip_device"),
        ANIMA_CLIP_DEVICES,
        "default",
    )
    return settings


def _normalize_aio_spectrum_settings(value, defaults: dict[str, Any]) -> dict[str, Any]:
    spectrum = value if isinstance(value, dict) else {}
    spectrum["enabled"] = _as_bool(spectrum.get("enabled"), _as_bool(defaults.get("enabled"), False))
    spectrum["window_size"] = max(
        1.0,
        min(10.0, _as_float(spectrum.get("window_size"), _as_float(defaults.get("window_size"), 2.0))),
    )
    spectrum["flex_window"] = max(
        0.0,
        min(2.0, _as_float(spectrum.get("flex_window"), _as_float(defaults.get("flex_window"), 0.25))),
    )
    spectrum["warmup_steps"] = max(
        0,
        min(10000, _as_int(spectrum.get("warmup_steps"), _as_int(defaults.get("warmup_steps"), 6))),
    )
    spectrum["tail_actual_steps"] = max(
        0,
        min(10000, _as_int(spectrum.get("tail_actual_steps"), _as_int(defaults.get("tail_actual_steps"), 3))),
    )
    spectrum["blend_w"] = max(
        0.0,
        min(1.0, _as_float(spectrum.get("blend_w"), _as_float(defaults.get("blend_w"), 0.3))),
    )
    spectrum["cheby_degree"] = max(
        1,
        min(10, _as_int(spectrum.get("cheby_degree"), _as_int(defaults.get("cheby_degree"), 3))),
    )
    spectrum["ridge_lambda"] = max(
        0.001,
        min(10.0, _as_float(spectrum.get("ridge_lambda"), _as_float(defaults.get("ridge_lambda"), 0.1))),
    )
    spectrum["history_size"] = max(
        5,
        min(10000, _as_int(spectrum.get("history_size"), _as_int(defaults.get("history_size"), 100))),
    )
    spectrum["one_sampler_only"] = _as_bool(
        spectrum.get("one_sampler_only"),
        _as_bool(defaults.get("one_sampler_only"), False),
    )
    spectrum["verbose"] = _as_bool(spectrum.get("verbose"), _as_bool(defaults.get("verbose"), False))
    spectrum["compat_policy"] = _choice(
        spectrum.get("compat_policy"),
        ("legacy", "conservative", "strict"),
        str(defaults.get("compat_policy") or "conservative"),
    )
    return spectrum


def _normalize_aio_dit_corrections_settings(value, defaults: dict[str, Any]) -> dict[str, Any]:
    corrections = value if isinstance(value, dict) else {}
    corrections["enabled"] = _as_bool(corrections.get("enabled"), _as_bool(defaults.get("enabled"), False))
    corrections["dcw_mode"] = _choice(
        corrections.get("dcw_mode"),
        ("off", "manual", "auto"),
        str(defaults.get("dcw_mode") or "off"),
    )
    corrections["dcw_lambda"] = max(
        -1.0,
        min(1.0, _as_float(corrections.get("dcw_lambda"), _as_float(defaults.get("dcw_lambda"), 0.01))),
    )
    corrections["dcw_band_mask"] = _choice(
        corrections.get("dcw_band_mask"),
        ("LL", "all", "HH", "LH+HL+HH"),
        str(defaults.get("dcw_band_mask") or "LL"),
    )
    corrections["dcw_calibrator"] = str(
        corrections.get("dcw_calibrator") or defaults.get("dcw_calibrator") or "(auto-download default)"
    )
    corrections["smc_cfg"] = _as_bool(corrections.get("smc_cfg"), _as_bool(defaults.get("smc_cfg"), False))
    corrections["adaptive_smc_alpha"] = max(
        0.0,
        min(
            1.0,
            _as_float(
                corrections.get("adaptive_smc_alpha"),
                _as_float(defaults.get("adaptive_smc_alpha"), 0.0),
            ),
        ),
    )
    corrections["smc_cfg_lambda"] = max(
        0.0,
        min(20.0, _as_float(corrections.get("smc_cfg_lambda"), _as_float(defaults.get("smc_cfg_lambda"), 6.0))),
    )
    corrections["cfgpp"] = _as_bool(corrections.get("cfgpp"), _as_bool(defaults.get("cfgpp"), False))
    corrections["cfgpp_lambda"] = max(
        0.0,
        min(8.0, _as_float(corrections.get("cfgpp_lambda"), _as_float(defaults.get("cfgpp_lambda"), 0.0))),
    )
    corrections["fsg"] = _as_bool(corrections.get("fsg"), _as_bool(defaults.get("fsg"), False))
    corrections["fsg_band_lo"] = max(
        0.0,
        min(1.0, _as_float(corrections.get("fsg_band_lo"), _as_float(defaults.get("fsg_band_lo"), 0.59))),
    )
    corrections["fsg_band_hi"] = max(
        0.0,
        min(1.0, _as_float(corrections.get("fsg_band_hi"), _as_float(defaults.get("fsg_band_hi"), 0.75))),
    )
    corrections["fsg_k"] = max(0, min(32, _as_int(corrections.get("fsg_k"), _as_int(defaults.get("fsg_k"), 3))))
    corrections["fsg_d_sigma"] = max(
        0.0,
        min(1.0, _as_float(corrections.get("fsg_d_sigma"), _as_float(defaults.get("fsg_d_sigma"), 0.1))),
    )
    corrections["fsg_gamma"] = max(
        0.0,
        min(10.0, _as_float(corrections.get("fsg_gamma"), _as_float(defaults.get("fsg_gamma"), 0.0))),
    )
    corrections["replace_existing_cfg"] = _as_bool(
        corrections.get("replace_existing_cfg"),
        _as_bool(defaults.get("replace_existing_cfg"), False),
    )
    return corrections


_AIO_DETAILER_RESERVED_KEYS = {"enabled", "order", "sam3"}
_AIO_DETAILER_CUSTOM_RE = re.compile(r"^custom_\d+$")


def _is_aio_detailer_target_name(name: str) -> bool:
    return name in ("face", "eye") or bool(_AIO_DETAILER_CUSTOM_RE.fullmatch(name))


def _aio_detailer_target_defaults(target_name: str) -> dict[str, Any]:
    if target_name == "eye":
        return _json_clone(AIO_GENERATION_DEFAULT_SETTINGS["detailer"]["eye"])
    defaults = _json_clone(AIO_GENERATION_DEFAULT_SETTINGS["detailer"]["face"])
    if target_name not in ("face", "eye"):
        suffix = target_name.rsplit("_", 1)[-1]
        defaults["label"] = f"Detailer Block {suffix}" if suffix.isdigit() else "Detailer Block"
    return defaults


def _aio_detailer_target_order(detailer_settings: dict[str, Any]) -> list[str]:
    output: list[str] = []

    def append_target(name) -> None:
        text = str(name or "").strip()
        if _is_aio_detailer_target_name(text) and text not in output:
            output.append(text)

    order = detailer_settings.get("order")
    if isinstance(order, list):
        for name in order:
            append_target(name)
    for name, value in detailer_settings.items():
        if name in _AIO_DETAILER_RESERVED_KEYS or not isinstance(value, dict):
            continue
        append_target(name)
    for name in ("face", "eye"):
        append_target(name)
    return output




def _aio_input_settings_json() -> str:
    return json.dumps(AIO_INPUT_DEFAULT_SETTINGS, ensure_ascii=False, separators=(",", ":"))


def _aio_generation_settings_json() -> str:
    return json.dumps(AIO_GENERATION_DEFAULT_SETTINGS, ensure_ascii=False, separators=(",", ":"))


def _comfy_max_resolution() -> int:
    try:
        import nodes as comfy_nodes  # type: ignore
    except Exception:
        comfy_nodes = None
    return _adapter_comfy_max_resolution(comfy_nodes)


def _comfy_diffusion_model_names() -> list[str]:
    return _adapter_comfy_diffusion_model_names(
        ANIMA_DEFAULT_DIFFUSION_MODEL_CANDIDATES,
        _folder_path_names,
    )


def _comfy_text_encoder_names() -> list[str]:
    return _adapter_comfy_text_encoder_names(
        ANIMA_DEFAULT_CLIP_CANDIDATES,
        _folder_path_names,
    )


def _comfy_vae_names() -> list[str]:
    return _adapter_comfy_vae_names(
        ANIMA_DEFAULT_VAE_CANDIDATES,
        _find_comfy_node_class,
        _folder_path_names,
    )


def _comfy_clip_loader_types() -> list[str]:
    return _adapter_comfy_clip_loader_types(
        ANIMA_CLIP_TYPES,
        _find_comfy_node_class,
    )


def _find_comfy_node_class(node_id: str):
    try:
        import nodes as comfy_nodes  # type: ignore
    except Exception:
        comfy_nodes = None
    return _adapter_find_comfy_node_class(node_id, comfy_nodes)


def _find_comfy_node_mapping_class(node_id: str):
    try:
        import nodes as comfy_nodes  # type: ignore

        return getattr(comfy_nodes, "NODE_CLASS_MAPPINGS", {}).get(node_id)
    except Exception:
        return None


def _require_custom_node_class(node_id: str, node_pack: str, install_hint: str):
    return _adapter_require_custom_node_class(
        node_id,
        node_pack,
        install_hint,
        _find_comfy_node_class,
    )


def _require_any_custom_node_class(node_ids: tuple[str, ...], node_pack: str, install_hint: str):
    return _adapter_require_any_custom_node_class(
        node_ids,
        node_pack,
        install_hint,
        _find_comfy_node_class,
    )


def _encode_with_comfy_clip(clip, text: str):
    return _adapter_encode_with_comfy_clip(clip, text, _find_comfy_node_class)


def _find_loaded_node_class(node_id: str):
    return _adapter_find_loaded_node_class(node_id, _find_comfy_node_class)




def _aio_lora_stack_signature(lora_stack) -> list[dict[str, Any]]:
    return [
        {
            "name": name,
            "strength_model": model_strength,
            "strength_clip": clip_strength,
        }
        for name, model_strength, clip_strength in _normalize_aio_lora_stack(lora_stack)
    ]


def _clone_aio_cache_value(value):
    if isinstance(value, dict):
        return {key: _clone_aio_cache_value(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_clone_aio_cache_value(item) for item in value]
    if isinstance(value, tuple):
        return tuple(_clone_aio_cache_value(item) for item in value)
    detach = getattr(value, "detach", None)
    clone = getattr(value, "clone", None)
    if callable(detach) and callable(clone):
        tensor = detach().clone()
        cpu = getattr(tensor, "cpu", None)
        if callable(cpu):
            try:
                tensor = cpu()
            except Exception:
                pass
        return tensor
    return value


def _clear_aio_first_pass_cache() -> None:
    _AIO_FIRST_PASS_CACHE.clear()
    _AIO_FIRST_PASS_CACHE_ORDER.clear()


def _aio_first_pass_cache_key(
    *,
    cache_scope: str,
    context: dict[str, Any],
    prompt_data: dict[str, Any],
    lora_stack,
    settings: dict[str, Any],
    positive_prompt: str,
    negative_prompt: str,
    quality_tags: str,
    quality_neg: str,
    use_anima_mod_guidance: bool,
    use_negative_anima_mod_guidance: bool,
    width: int,
    height: int,
) -> str:
    return _stable_change_key({
        "schema": "easyuse_anima_aio_first_pass_cache",
        "version": 1,
        "scope": str(cache_scope or ""),
        "mode": settings.get("mode"),
        "resource_info": _prompt_data_json_safe(context.get("resource_info", {})),
        "input_settings": _prompt_data_json_safe(context.get("input_settings", {})),
        "prompt_data": _prompt_data_json_safe(prompt_data),
        "lora_stack": _aio_lora_stack_signature(lora_stack),
        "sampler": _prompt_data_json_safe(settings.get("sampler", {})),
        "model_patches": _prompt_data_json_safe(settings.get("model_patches", {})),
        "mod_guidance": _prompt_data_json_safe(settings.get("mod_guidance", {})),
        "artist_mix": _prompt_data_json_safe(settings.get("artist_mix", {})),
        "positive_prompt": str(positive_prompt or ""),
        "negative_prompt": str(negative_prompt or ""),
        "quality_tags": str(quality_tags or ""),
        "quality_neg": str(quality_neg or ""),
        "use_anima_mod_guidance": bool(use_anima_mod_guidance),
        "use_negative_anima_mod_guidance": bool(use_negative_anima_mod_guidance),
        "width": int(width),
        "height": int(height),
    })


def _get_aio_first_pass_cache(cache_key: str):
    entry = _AIO_FIRST_PASS_CACHE.get(cache_key)
    if not entry:
        return None
    if cache_key in _AIO_FIRST_PASS_CACHE_ORDER:
        _AIO_FIRST_PASS_CACHE_ORDER.remove(cache_key)
    _AIO_FIRST_PASS_CACHE_ORDER.append(cache_key)
    return (
        _clone_aio_cache_value(entry["latent"]),
        _clone_aio_cache_value(entry["image"]),
    )


def _put_aio_first_pass_cache(cache_key: str, latent, image) -> None:
    _AIO_FIRST_PASS_CACHE[cache_key] = {
        "latent": _clone_aio_cache_value(latent),
        "image": _clone_aio_cache_value(image),
    }
    if cache_key in _AIO_FIRST_PASS_CACHE_ORDER:
        _AIO_FIRST_PASS_CACHE_ORDER.remove(cache_key)
    _AIO_FIRST_PASS_CACHE_ORDER.append(cache_key)
    while len(_AIO_FIRST_PASS_CACHE_ORDER) > AIO_FIRST_PASS_CACHE_MAX_ENTRIES:
        old_key = _AIO_FIRST_PASS_CACHE_ORDER.pop(0)
        _AIO_FIRST_PASS_CACHE.pop(old_key, None)


def _image_tensor_size(image, fallback_width: int, fallback_height: int) -> tuple[int, int]:
    try:
        return int(image.shape[2]), int(image.shape[1])
    except Exception:
        return int(fallback_width), int(fallback_height)


def _resize_image_to_size_if_needed(
    image,
    target_width: int,
    target_height: int,
    upscale_method: str = "bicubic",
) -> tuple[Any, bool]:
    target_width = max(1, int(target_width))
    target_height = max(1, int(target_height))
    width, height = _image_tensor_size(image, target_width, target_height)
    if width == target_width and height == target_height:
        return image, False
    samples = image.movedim(-1, 1)
    resized = _common_upscale_image(samples, target_width, target_height, str(upscale_method or "bicubic"))
    return resized.movedim(1, -1), True


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


def _aio_usdu_auto_tile_dimension(
    target_size: int,
    preferred_size: int = 1024,
    min_size: int = 512,
    max_size: int = 2048,
) -> int:
    target_size = max(1, int(target_size))
    min_size = max(64, int(min_size))
    max_size = max(min_size, int(max_size))
    preferred = max(min_size, min(max_size, int(preferred_size)))
    tile_count = max(1, ceil(target_size / preferred))
    tile_size = ceil(target_size / tile_count)
    tile_size = _align_nearest(tile_size, 64)
    return max(min_size, min(max_size, tile_size))


def _aio_usdu_tile_plan(image, scale_by: float, usdu_settings: dict[str, Any]) -> dict[str, Any]:
    width, height = _image_tensor_size(image, 512, 512)
    target_width = max(1, int(round(width * max(0.05, float(scale_by)))))
    target_height = max(1, int(round(height * max(0.05, float(scale_by)))))
    auto_tile = _as_bool(usdu_settings.get("auto_tile_size"), True)
    if not auto_tile:
        return {
            "auto": False,
            "input_width": int(width),
            "input_height": int(height),
            "target_width": int(target_width),
            "target_height": int(target_height),
            "tile_width": _as_int(usdu_settings.get("tile_width"), 512),
            "tile_height": _as_int(usdu_settings.get("tile_height"), 512),
        }
    preferred = _as_int(usdu_settings.get("auto_tile_target"), 1024)
    min_size = _as_int(usdu_settings.get("auto_tile_min"), 512)
    max_size = _as_int(usdu_settings.get("auto_tile_max"), 2048)
    return {
        "auto": True,
        "input_width": int(width),
        "input_height": int(height),
        "target_width": int(target_width),
        "target_height": int(target_height),
        "preferred": int(preferred),
        "min": int(min_size),
        "max": int(max_size),
        "tile_width": _aio_usdu_auto_tile_dimension(target_width, preferred, min_size, max_size),
        "tile_height": _aio_usdu_auto_tile_dimension(target_height, preferred, min_size, max_size),
    }


def _aio_usdu_tile_size(image, scale_by: float, usdu_settings: dict[str, Any]) -> tuple[int, int]:
    tile_plan = _aio_usdu_tile_plan(image, scale_by, usdu_settings)
    return int(tile_plan["tile_width"]), int(tile_plan["tile_height"])


def _aio_final_fit_size(width: int, height: int, fit_settings: dict[str, Any]) -> tuple[int, int, float]:
    width = max(1, int(width))
    height = max(1, int(height))
    if not _as_bool(fit_settings.get("enabled"), False):
        return width, height, 1.0
    mode = str(fit_settings.get("mode") or "max_long_edge")
    scale = 1.0
    if mode == "megapixels":
        max_pixels = max(1.0, _as_float(fit_settings.get("max_megapixels"), 4.0) * 1_000_000.0)
        pixels = float(width * height)
        if pixels > max_pixels:
            scale = sqrt(max_pixels / pixels)
    else:
        max_long_edge = max(1, _as_int(fit_settings.get("max_long_edge"), 2048))
        long_edge = max(width, height)
        if long_edge > max_long_edge:
            scale = max_long_edge / long_edge
    if scale >= 1.0:
        return width, height, 1.0
    target_width = _align_down(round(width * scale), LATENT_ALIGN)
    target_height = _align_down(round(height * scale), LATENT_ALIGN)
    return max(1, target_width), max(1, target_height), scale


def _apply_aio_final_fit(image, postprocess_settings: dict[str, Any]) -> tuple[Any, dict[str, Any]]:
    fit_settings = postprocess_settings.get("fit", {})
    if not isinstance(fit_settings, dict):
        fit_settings = {}
    fit_settings = dict(fit_settings)
    fit_settings["enabled"] = _as_bool(postprocess_settings.get("enabled"), False)
    width, height = _image_tensor_size(image, 0, 0)
    target_width, target_height, scale = _aio_final_fit_size(width, height, fit_settings)
    metadata = {
        "enabled": _as_bool(postprocess_settings.get("enabled"), False),
        "mode": str(fit_settings.get("mode") or "max_long_edge"),
        "max_long_edge": _as_int(fit_settings.get("max_long_edge"), 2048),
        "max_megapixels": _as_float(fit_settings.get("max_megapixels"), 4.0),
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
    output, resized = _resize_image_to_size_if_needed(
        image,
        target_width,
        target_height,
        str(fit_settings.get("method") or "bicubic"),
    )
    metadata["applied"] = bool(resized)
    return output, metadata


def _run_aio_postprocess_stage(image, postprocess_settings: dict[str, Any]) -> tuple[Any, dict[str, Any]]:
    if not _as_bool(postprocess_settings.get("enabled"), False):
        width, height = _image_tensor_size(image, 0, 0)
        return image, {
            "enabled": False,
            "width": int(width),
            "height": int(height),
        }
    output, fit_metadata = _apply_aio_final_fit(image, postprocess_settings)
    width, height = _image_tensor_size(output, fit_metadata.get("target_width", 0), fit_metadata.get("target_height", 0))
    limit = (
        f"{fit_metadata.get('max_megapixels')}MP"
        if fit_metadata.get("mode") == "megapixels"
        else f"{fit_metadata.get('max_long_edge')}px"
    )
    logger.info(
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
    upscale_model = _load_upscale_model_with_comfy(str(usdu_settings.get("upscale_model_name") or ""))
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
            seam_fix_denoise=_as_float(usdu_settings.get("seam_fix_denoise"), 1.0),
            seam_fix_mask_blur=_as_int(usdu_settings.get("seam_fix_mask_blur"), 8),
            seam_fix_width=_as_int(usdu_settings.get("seam_fix_width"), 64),
            seam_fix_padding=_as_int(usdu_settings.get("seam_fix_padding"), 16),
            force_uniform_tiles=_as_bool(usdu_settings.get("force_uniform_tiles"), True),
            tiled_decode=_as_bool(usdu_settings.get("tiled_decode"), False),
            batch_size=_as_int(usdu_settings.get("batch_size"), 1),
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
        "prompt_mode": str(usdu_settings.get("prompt_mode") or AIO_USDU_PROMPT_FULL),
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
    model_values = _node_output_tuple(load(
        str(resshift_settings.get("scale") or "x2"),
        str(resshift_settings.get("student_name") or "(auto-download)"),
        str(resshift_settings.get("dtype") or "bf16"),
    ))
    if not model_values:
        raise RuntimeError("[EasyUseAnima] ResShiftLoader returned no RESSHIFT_MODEL.")
    upscaler = upscale_cls()
    upscale = getattr(upscaler, "upscale", None)
    if upscale is None:
        raise RuntimeError("[EasyUseAnima] ResShiftUpscale does not expose upscale().")
    values = _node_output_tuple(upscale(
        model_values[0],
        image,
        _resolve_aio_runtime_seed(sampler_settings.get("seed")),
        _as_int(resshift_settings.get("chop"), 512),
        _as_int(resshift_settings.get("overlap"), 64),
        _as_int(resshift_settings.get("tile_batch"), 4),
    ))
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
        raise RuntimeError(f"[EasyUseAnima] Unsupported final upscale backend: {backend}")
    return output, metadata


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
            detect_count=_as_int(target_settings.get("detect_count"), 1),
            threshold=_as_float(target_settings.get("threshold"), 0.5),
            refine_iterations=_as_int(target_settings.get("refine_iterations"), 2),
            individual_masks=_as_bool(target_settings.get("individual_masks"), True),
            combined=_as_bool(target_settings.get("combined"), False),
            crop_factor=_as_float(target_settings.get("crop_factor"), 4.0),
            bbox_fill=_as_bool(target_settings.get("bbox_fill"), False),
            drop_size=_as_int(target_settings.get("drop_size"), 100),
            contour_fill=_as_bool(target_settings.get("contour_fill"), True),
            model=stage_model,
            clip=clip,
            vae=vae,
            guide_size=_as_int(target_settings.get("guide_size"), 1024),
            guide_size_for=_as_bool(target_settings.get("guide_size_for"), False),
            max_size=_as_int(target_settings.get("max_size"), 2048),
            seed=stage_sampler["seed"],
            steps=stage_sampler["steps"],
            cfg=stage_sampler["cfg"],
            sampler_name=stage_sampler["sampler_name"],
            scheduler=stage_sampler["scheduler"],
            positive=positive,
            negative=negative,
            denoise=stage_sampler["denoise"],
            feather=_as_int(target_settings.get("feather"), 5),
            noise_mask=_as_bool(target_settings.get("noise_mask"), True),
            force_inpaint=_as_bool(target_settings.get("force_inpaint"), True),
            wildcard=str(target_settings.get("wildcard") or ""),
            cycle=_as_int(target_settings.get("cycle"), 1),
            alignment=str(target_settings.get("alignment") or "32"),
            preserve_conditioning_metadata=True,
            fail_on_unsupported_opt=False,
            detailer_hook=None,
            inpaint_model=_as_bool(target_settings.get("inpaint_model"), False),
            noise_mask_feather=_as_int(target_settings.get("noise_mask_feather"), 0),
            scheduler_func_opt=None,
            tiled_encode=_as_bool(target_settings.get("tiled_encode"), False),
            tiled_decode=_as_bool(target_settings.get("tiled_decode"), False),
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


AIO_FIRST_PASS_CACHE_MAX_ENTRIES = 2
_AIO_FIRST_PASS_CACHE: dict[str, dict[str, Any]] = {}
_AIO_FIRST_PASS_CACHE_ORDER: list[str] = []


def _aio_detailer_has_enabled_targets(detailer_settings: dict[str, Any]) -> bool:
    if not _as_bool(detailer_settings.get("enabled"), False):
        return False
    return any(
        isinstance(detailer_settings.get(name), dict)
        and _as_bool(detailer_settings[name].get("enabled"), False)
        for name in _aio_detailer_target_order(detailer_settings)
    )


def _get_workflow_node(extra_pnginfo, node_id: str):
    pnginfo = _single_value(extra_pnginfo)
    if not isinstance(pnginfo, dict):
        return None
    workflow = pnginfo.get("workflow")
    if not isinstance(workflow, dict):
        return None

    node_ids = str(node_id).split(":")
    nodes_list = workflow.get("nodes", [])
    definitions = workflow.get("definitions", {})
    if not isinstance(definitions, dict):
        definitions = {}
    subgraphs = definitions.get("subgraphs", [])
    if not isinstance(subgraphs, list):
        subgraphs = []

    found = None
    for individual_node_id in node_ids:
        if not isinstance(nodes_list, list):
            return None
        found = next(
            (
                node
                for node in nodes_list
                if isinstance(node, dict) and str(node.get("id")) == individual_node_id
            ),
            None,
        )
        if isinstance(found, dict):
            subgraph = next(
                (
                    graph
                    for graph in subgraphs
                    if isinstance(graph, dict) and str(graph.get("id")) == str(found.get("type"))
                ),
                None,
            )
            if isinstance(subgraph, dict) and isinstance(subgraph.get("nodes"), list):
                nodes_list = subgraph["nodes"]
    return found


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


_bind_aio_generation_normalization_runtime(
    resolve_helper=lambda name: globals()[name],
)
_bind_aio_resource_runtime(
    resolve_helper=lambda name: globals()[name],
)
_bind_aio_model_preparation_runtime(
    resolve_helper=lambda name: globals()[name],
)
_bind_aio_sampling_runtime(
    resolve_helper=lambda name: globals()[name],
)
_bind_aio_preview_runtime(
    resolve_helper=lambda name: globals()[name],
)
_bind_aio_output_runtime(
    resolve_helper=lambda name: globals()[name],
)
_bind_aio_conditioning_runtime(
    resolve_helper=lambda name: globals()[name],
)
_bind_sam3_runtime(
    resolve_helper=lambda name: globals()[name],
)
_bind_impact_detailer_node_runtime(
    resolve_helper=lambda name: globals()[name],
)
_bind_sam3_node_runtime(
    resolve_helper=lambda name: globals()[name],
)
_bind_regional_runtime(
    resolve_helper=lambda name: globals()[name],
)
_bind_regional_node_runtime(
    resolve_helper=lambda name: globals()[name],
    flexible_optional_input_type=_FlexibleOptionalInputType,
)
_bind_advanced_runtime(
    resolve_helper=lambda name: globals()[name],
)
_bind_prompt_advanced_node_runtime(
    resolve_helper=lambda name: globals()[name],
    flexible_optional_input_type=_FlexibleOptionalInputType,
)
_bind_conditioning_runtime(
    resolve_helper=lambda name: globals()[name],
    resolve_logger=lambda: logger,
)
_bind_artist_mix_runtime(
    resolve_helper=lambda name: globals()[name],
)
_bind_prompt_data_node_runtime(
    resolve_helper=lambda name: globals()[name],
)
_bind_prompt_fields_runtime(
    resolve_helper=lambda name: globals()[name],
)
_bind_prompt_correction_runtime(
    resolve_helper=lambda name: globals()[name],
)
_bind_prompt_node_runtime(
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
_bind_lora_metadata_runtime(
    prompt_tokens=lambda *args, **kwargs: _prompt_tokens(*args, **kwargs),
    resolve_helper=lambda name: globals()[name],
    resolve_logger=lambda: logger,
)
_bind_lora_preset_runtime(
    correct_builder_prompt=lambda *args, **kwargs: _correct_builder_prompt(*args, **kwargs),
    resolve_helper=lambda name: globals()[name],
)
_bind_lora_node_runtime(
    resolve_helper=lambda name: globals()[name],
    flexible_optional_input_type=_FlexibleOptionalInputType,
    any_type=_ANY_TYPE,
)


def _easy_use_anima_input_signature(value) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {"type": str(type(value).__name__)}
    return {
        "schema": value.get("schema"),
        "version": value.get("version"),
        "resource_info": _prompt_data_json_safe(value.get("resource_info", {})),
        "input_settings": _prompt_data_json_safe(value.get("input_settings", {})),
        "prompt_data": _prompt_data_json_safe(value.get("prompt_data", {})),
    }


def _require_easy_use_anima_input(value) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise RuntimeError("[EasyUseAnima] easy use anima input is missing or invalid.")
    missing = [key for key in ("prompt_data", "resource_info", "input_settings") if key not in value]
    if missing:
        raise RuntimeError(
            "[EasyUseAnima] easy use anima input is missing required value(s): "
            + ", ".join(missing)
        )
    return value


class EasyUseAnimaInput:
    """Bundle prompt data and resource loader settings for the AiO generator."""

    DESCRIPTION = (
        "Receives EASYUSE_ANIMA_PROMPT_DATA and selected ANIMA resource names, then returns "
        "one dedicated easy use anima input context. The context stores only serializable "
        "prompt/resource data; the AiO Generator loads MODEL, CLIP, and VAE at execution "
        "time so model patches and Torch compile do not live inside a custom dict socket."
    )
    OUTPUT_TOOLTIPS = (
        "Dedicated context containing prompt data, resource metadata, and versioned loader settings.",
    )

    @classmethod
    def INPUT_TYPES(cls):
        unet_names = _comfy_diffusion_model_names()
        vae_names = _comfy_vae_names()
        clip_names = _comfy_text_encoder_names()
        clip_types = _comfy_clip_loader_types()
        return {
            "required": {
                PROMPT_DATA_TYPE: (PROMPT_DATA_TYPE, {
                    "forceInput": True,
                    "tooltip": "Structured prompt data from Anima Prompt Studio Advanced v2.",
                }),
                "unet_name": (unet_names, {
                    "default": _preferred_name_default(unet_names, ANIMA_DEFAULT_DIFFUSION_MODEL_CANDIDATES),
                    "tooltip": "ANIMA diffusion model loaded with ComfyUI UNETLoader.",
                }),
                "vae_name": (vae_names, {
                    "default": _preferred_name_default(vae_names, ANIMA_DEFAULT_VAE_CANDIDATES),
                    "tooltip": "VAE loaded with ComfyUI VAELoader.",
                }),
                "clip_name": (clip_names, {
                    "default": _preferred_name_default(clip_names, ANIMA_DEFAULT_CLIP_CANDIDATES),
                    "tooltip": "Text encoder loaded with ComfyUI CLIPLoader.",
                }),
                "clip_type": (clip_types, {
                    "default": _preferred_clip_type_default(clip_types),
                    "tooltip": "ComfyUI CLIPLoader type. Core ANIMA uses qwen_image.",
                }),
                "input_settings": ("STRING", {
                    "multiline": True,
                    "default": _aio_input_settings_json(),
                    "hidden": True,
                    "tooltip": "Hidden versioned JSON storage for future resource settings. Kept serialized for workflow compatibility.",
                }),
            },
        }

    RETURN_TYPES = (EASY_USE_ANIMA_INPUT_TYPE,)
    RETURN_NAMES = ("easy use anima input",)
    FUNCTION = "build"
    CATEGORY = "EasyUse Anima/AiO"

    @classmethod
    def IS_CHANGED(
        cls,
        EASYUSE_ANIMA_PROMPT_DATA: str | dict | None = None,
        unet_name: str = "",
        vae_name: str = "",
        clip_name: str = "",
        clip_type: str = "",
        input_settings: str | dict | None = None,
        **kwargs,
    ):
        return _stable_change_key({
            "mode": "easy_use_anima_input",
            "prompt_data": _prompt_data_json_safe(_normalize_prompt_data(EASYUSE_ANIMA_PROMPT_DATA)),
            "unet_name": str(unet_name or ""),
            "vae_name": str(vae_name or ""),
            "clip_name": str(clip_name or ""),
            "clip_type": str(clip_type or ""),
            "input_settings": _normalize_aio_input_settings(input_settings),
        })

    def build(
        self,
        EASYUSE_ANIMA_PROMPT_DATA: str | dict,
        unet_name: str,
        vae_name: str,
        clip_name: str,
        clip_type: str = "qwen_image",
        input_settings: str | dict | None = None,
    ):
        settings = _normalize_aio_input_settings(input_settings)
        prompt_data = _copy_prompt_data_for_update(EASYUSE_ANIMA_PROMPT_DATA)
        resources = settings.get("resources", {})
        resource_info = {
            "loader_mode": "split",
            "unet_name": str(unet_name),
            "vae_name": str(vae_name),
            "clip_name": str(clip_name),
            "clip_type": str(clip_type or "qwen_image"),
            "unet_weight_dtype": str(resources.get("unet_weight_dtype") or "default"),
            "clip_device": str(resources.get("clip_device") or "default"),
        }
        prompt_data["easy_use_anima_input"] = {
            "schema": EASY_USE_ANIMA_INPUT_SCHEMA,
            "version": EASY_USE_ANIMA_INPUT_SETTINGS_VERSION,
            "resource_info": dict(resource_info),
        }
        return ({
            "schema": EASY_USE_ANIMA_INPUT_SCHEMA,
            "version": EASY_USE_ANIMA_INPUT_SETTINGS_VERSION,
            "prompt_data": prompt_data,
            "resource_info": resource_info,
            "input_settings": settings,
        },)


class EasyUseAnimaAIOGenerator:
    """Draft all-in-one generator that consumes one easy use anima input context."""

    DESCRIPTION = (
        "Consumes the dedicated easy use anima input context and runs the base txt2img "
        "generation path: prompt-data conditioning, optional Mod Guidance model patch, "
        "KSampler, VAE decode, and optional image saving. Generation options are stored in "
        "one versioned JSON field for future-compatible popup settings."
    )
    OUTPUT_TOOLTIPS = (
        "Decoded generated image.",
        "Sampled latent image.",
        "JSON metadata summary for debugging or downstream integration.",
    )

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "easy_use_anima_input": (EASY_USE_ANIMA_INPUT_TYPE, {
                    "forceInput": True,
                    "tooltip": "Context from Easy Use Anima Input.",
                }),
                "generation_settings": ("STRING", {
                    "multiline": True,
                    "default": _aio_generation_settings_json(),
                    "hidden": True,
                    "tooltip": "Hidden versioned JSON storage for popup generation settings. Keep this field serialized.",
                }),
            },
            "hidden": {
                "workflow_prompt": "PROMPT",
                "extra_pnginfo": "EXTRA_PNGINFO",
                "unique_id": "UNIQUE_ID",
            },
            "optional": {
                "lora_stack": ("LORA_STACK", {
                    "forceInput": True,
                    "tooltip": "Optional LoRA stack applied to MODEL and CLIP before conditioning and sampling.",
                }),
            },
        }

    RETURN_TYPES = ("IMAGE", "LATENT", "STRING")
    RETURN_NAMES = ("image", "latent", "metadata_json")
    FUNCTION = "generate"
    OUTPUT_NODE = True
    CATEGORY = "EasyUse Anima/AiO"

    @classmethod
    def IS_CHANGED(
        cls,
        easy_use_anima_input=None,
        lora_stack=None,
        generation_settings: str | dict | None = None,
        **kwargs,
    ):
        settings = _normalize_aio_generation_settings(generation_settings)
        if settings.get("sampler", {}).get("seed") in AIO_SPECIAL_SEEDS:
            change_settings = _json_clone(settings)
            change_settings["sampler"]["seed"] = _resolve_aio_runtime_seed(
                change_settings["sampler"].get("seed")
            )
        else:
            change_settings = settings
        return _stable_change_key({
            "mode": "easy_use_anima_generator",
            "input": _easy_use_anima_input_signature(easy_use_anima_input),
            "lora_stack": _aio_lora_stack_signature(lora_stack),
            "generation_settings": change_settings,
        })

    def generate(
        self,
        easy_use_anima_input,
        generation_settings: str | dict | None = None,
        lora_stack=None,
        workflow_prompt=None,
        extra_pnginfo=None,
        unique_id=None,
    ):
        context = _require_easy_use_anima_input(easy_use_anima_input)
        settings = _normalize_aio_generation_settings(generation_settings)
        settings["sampler"]["seed"] = _resolve_aio_runtime_seed(settings["sampler"].get("seed"))
        if settings["mode"] != "txt2img":
            raise RuntimeError("[EasyUseAnima] AiO Generator draft currently supports txt2img only.")

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
        image_saver_positive_prompt = metadata_prompt or positive_prompt
        image_saver_negative_prompt = metadata_negative_prompt or negative_prompt

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
        profile = _normalize_anima_mod_guidance_profile(mod_guidance["profile"])
        use_mod_guidance = _resolve_anima_mod_guidance_enabled(
            use_anima_mod_guidance,
            mod_guidance["mode"],
        )
        sampler_backend = str(sampler.get("backend") or "comfy_ksampler")
        highres_backend = _aio_highres_effective_backend(sampler, settings["highres"])
        mod_guidance_model = model
        can_apply_standalone_mod_guidance = (
            use_mod_guidance
            and profile != ANIMA_MOD_GUIDANCE_PROFILE_OFF
        )

        def ensure_standalone_mod_guidance_model():
            nonlocal mod_guidance_model
            if not can_apply_standalone_mod_guidance or mod_guidance_model is not model:
                return mod_guidance_model
            mod_guidance_model = _apply_spectrum_anima_mod_guidance(
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

        base_sample_model, base_use_mod_guidance = model_and_mod_guidance_flag_for_backend(sampler_backend)
        if sampler_backend == "comfy_ksampler":
            base_sample_model = _apply_aio_spectrum_model_patches_for_comfy_sampler(
                base_sample_model,
                clip,
                positive,
                sampler,
            )

        stage_metadata: dict[str, Any] = {}
        preview_settings = settings["preview"]
        preview_images: list[dict[str, Any]] = []
        preview_node_id = _single_value(unique_id)
        preview_run_id = f"{preview_node_id or 'aio'}:{random.getrandbits(64):016x}"
        first_pass_cache_key = _aio_first_pass_cache_key(
            cache_scope=str(unique_id or id(self)),
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
            images = _save_aio_temp_preview_image(
                stage_image,
                stage,
                workflow_prompt=workflow_prompt,
                extra_pnginfo=extra_pnginfo,
            )
            if images:
                preview_images.extend(images)
                _send_aio_preview_event(preview_node_id, preview_run_id, stage, images)

        try:
            cached_first_pass = _get_aio_first_pass_cache(first_pass_cache_key)
            if cached_first_pass is not None:
                latent, image = cached_first_pass
                first_pass_cache_hit = True
            else:
                latent_image = _generate_empty_latent_with_comfy(width, height)
                latent = _sample_latent_with_aio_backend(
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
                image = _decode_latent_with_comfy(vae, latent)
            image, first_pass_resized = _resize_image_to_size_if_needed(
                image,
                width,
                height,
                "bicubic",
            )
            if first_pass_resized:
                latent = _encode_image_with_comfy_vae(vae, image)
            if not first_pass_cache_hit or first_pass_resized:
                try:
                    _put_aio_first_pass_cache(first_pass_cache_key, latent, image)
                except Exception as exc:
                    logger.debug("[EasyUseAnima] failed to store AiO first-pass cache: %s", exc)
            stage_metadata["first_pass"] = {"cache_hit": first_pass_cache_hit}
            if preview_settings["intermediate_images"]:
                add_preview("first_pass", image)
            highres_model, highres_use_mod_guidance = (
                model_and_mod_guidance_flag_for_backend(highres_backend)
                if will_run_highres
                else (model, False)
            )
            latent, image, width, height, highres_metadata = _run_aio_highres_stage(
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
            if highres_metadata.get("enabled") and isinstance(highres_metadata.get("sampler"), dict):
                if preview_settings["intermediate_images"] and will_run_detailer:
                    add_preview("highres", image)
            image, detailer_metadata = _run_aio_detailer_stage(
                ensure_standalone_mod_guidance_model() if will_run_detailer else mod_guidance_model,
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
                width, height = _image_tensor_size(image, width, height)
            image, upscale_metadata = _run_aio_upscale_stage(
                ensure_standalone_mod_guidance_model() if will_run_upscale else mod_guidance_model,
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
                exclude_negative_quality=can_apply_standalone_mod_guidance and use_negative_anima_mod_guidance,
            )
            stage_metadata["upscale"] = upscale_metadata
            if upscale_metadata.get("enabled"):
                width, height = _image_tensor_size(image, width, height)
                latent = _encode_image_with_comfy_vae(vae, image)
                if preview_settings["intermediate_images"]:
                    add_preview("upscale", image)
            image, postprocess_metadata = _run_aio_postprocess_stage(
                image,
                settings["postprocess"],
            )
            stage_metadata["postprocess"] = postprocess_metadata
            if postprocess_metadata.get("enabled"):
                width, height = _image_tensor_size(image, width, height)
                postprocess_changed = _as_bool(
                    (postprocess_metadata.get("fit") or {}).get("applied"),
                    False,
                )
                if postprocess_changed:
                    latent = _encode_image_with_comfy_vae(vae, image)
                if preview_settings["intermediate_images"] and postprocess_changed and will_run_postprocess:
                    add_preview("postprocess", image)
        finally:
            seen_model_ids: set[int] = set()
            for ephemeral_model in (base_sample_model, mod_guidance_model, model, model_with_lora):
                if ephemeral_model is None:
                    continue
                key = id(ephemeral_model)
                if key in seen_model_ids:
                    continue
                seen_model_ids.add(key)
                _cleanup_aio_ephemeral_model(ephemeral_model, base_model)

        save_settings = settings["save"]
        save_ui = {}
        if save_settings.get("enabled"):
            if save_settings.get("backend") == "image_saver":
                save_result = _save_image_with_image_saver(
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
                save_result = _save_image_with_comfy(
                    image,
                    _aio_save_filename_prefix(save_settings),
                    workflow_prompt=workflow_prompt,
                    extra_pnginfo=extra_pnginfo,
                )
            if isinstance(save_result, dict) and isinstance(save_result.get("ui"), dict):
                save_ui = save_result["ui"]
        final_preview = _tag_aio_preview_images(save_ui.get("images", []), "final", width=width, height=height)
        if not final_preview:
            final_preview = _save_aio_temp_preview_image(
                image,
                "final",
                workflow_prompt=workflow_prompt,
                extra_pnginfo=extra_pnginfo,
            )
        if final_preview and preview_images and str(preview_images[-1].get("stage") or "").startswith("detailer_"):
            preview_images[-1] = final_preview[0]
            final_preview = final_preview[1:]

        metadata = {
            "schema": "easyuse_anima_aio_generation_result",
            "version": 1,
            "width": int(width),
            "height": int(height),
            "resource_info": _prompt_data_json_safe(context.get("resource_info", {})),
            "input_settings": _prompt_data_json_safe(context.get("input_settings", {})),
            "lora_stack": _prompt_data_json_safe(applied_loras),
            "generation_settings": _prompt_data_json_safe(settings),
            "stages": _prompt_data_json_safe(stage_metadata),
            "prompt_data": _prompt_data_json_safe(prompt_data),
        }
        metadata_json = json.dumps(metadata, ensure_ascii=False, sort_keys=True)
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
