# -*- coding: utf-8 -*-
from __future__ import annotations

import inspect
import json
import logging
import os
import random
import re
import sys
from math import ceil, isfinite, sqrt
from typing import Any, Optional

try:
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
        _require_any_custom_node_class as _adapter_require_any_custom_node_class,
        _require_custom_node_class as _adapter_require_custom_node_class,
    )
    from .easyuse_anima.infrastructure.comfy.invocation import (
        _call_with_supported_kwargs as _call_with_supported_kwargs,
        _common_upscale_image as _common_upscale_image,
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
    from .easyuse_anima.nodes.prompt_nodes import (
        EasyUseAnimaPromptBuilder as EasyUseAnimaPromptBuilder,
        EasyUseAnimaPromptCorrector as EasyUseAnimaPromptCorrector,
        EasyUseAnimaPromptCorrectorSimple as EasyUseAnimaPromptCorrectorSimple,
        EasyUseAnimaPromptStudio as EasyUseAnimaPromptStudio,
        _bind_prompt_node_runtime as _bind_prompt_node_runtime,
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
        _require_any_custom_node_class as _adapter_require_any_custom_node_class,
        _require_custom_node_class as _adapter_require_custom_node_class,
    )
    from easyuse_anima.infrastructure.comfy.invocation import (
        _call_with_supported_kwargs as _call_with_supported_kwargs,
        _common_upscale_image as _common_upscale_image,
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
    from easyuse_anima.nodes.prompt_nodes import (
        EasyUseAnimaPromptBuilder as EasyUseAnimaPromptBuilder,
        EasyUseAnimaPromptCorrector as EasyUseAnimaPromptCorrector,
        EasyUseAnimaPromptCorrectorSimple as EasyUseAnimaPromptCorrectorSimple,
        EasyUseAnimaPromptStudio as EasyUseAnimaPromptStudio,
        _bind_prompt_node_runtime as _bind_prompt_node_runtime,
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

ADVANCED_FIELD_TYPES = {"quality", "artist", "trigger", "general", "naia"}
ADVANCED_FIELD_PANES = {"positive", "negative"}
ADVANCED_FIELD_LABELS = {
    "quality": "Quality Tags",
    "artist": "Artist Tags",
    "trigger": "Trigger Words",
    "general": "General Tags",
    "naia": "NAIA Prompt",
}
ADVANCED_FIELDS_WORKFLOW_PROPERTY = "easyuse_anima_advanced_fields"
WILDCARD_RESERVED_NEXT_SEED_INPUT = "easyuse_anima_reserved_wildcard_next_seed"
WILDCARD_QUEUE_MAX_SAFE_SEED = PUBLIC_MAX_SEED
PROMPT_STUDIO_WILDCARD_SEED_CONTROL_ALIASES = {
    "fixed": SEED_CONTROL_FIXED,
    "고정": SEED_CONTROL_FIXED,
    "random": SEED_CONTROL_RANDOMIZE,
    "randomize": SEED_CONTROL_RANDOMIZE,
    "매번 랜덤": SEED_CONTROL_RANDOMIZE,
    "increase": SEED_CONTROL_INCREMENT,
    "increment": SEED_CONTROL_INCREMENT,
    "증가": SEED_CONTROL_INCREMENT,
}
PROMPT_STUDIO_LEGACY_FIXED_WILDCARD_MODES = {
    WILDCARD_MODE_FIXED,
    "고정",
    "reproduce",
    "재현",
}
REGIONAL_FIELDS_WORKFLOW_PROPERTY = "easyuse_anima_regional_fields"
REGIONAL_CONFIG_WORKFLOW_PROPERTY = "easyuse_anima_regional_config"
REGIONAL_FIELD_TYPES = {"quality", "artist", "trigger", "general"}
REGIONAL_CONFIG_VERSION = 1
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
REGIONAL_PROMPT_DATA_TYPE = "EASYUSE_ANIMA_REGIONAL_PROMPT_DATA"
REGIONAL_PROMPT_DATA_SCHEMA = "easyuse_anima_prompt_studio_regional"
REGIONAL_PROMPT_BUNDLE_SCHEMA = "easyuse_anima_prompt_studio_regional_bundle"
EXTEND_PROMPT_SLOT_SPECS = [
    ("quality_tags_1", "positive", "quality", "Quality Tags 1", DEFAULT_QUALITY_TAGS, 72),
    ("quality_tags_2", "positive", "quality", "Quality Tags 2", "", 72),
    ("naia_prompt_3", "positive", "general", "NAIA Prompt 3", "", 150),
    ("general_tags_4", "positive", "general", "General Tags 4", "", 120),
    ("general_tags_5", "positive", "general", "General Tags 5", "", 120),
    ("general_tags_6", "positive", "general", "General Tags 6", "", 120),
    ("general_tags_7", "positive", "general", "General Tags 7", "", 120),
    ("general_tags_8", "positive", "general", "General Tags 8", "", 120),
    ("general_tags_9", "positive", "general", "General Tags 9", "", 120),
    ("trailing_tags_10", "positive", "general", "Trailing Quality Tags 10", DEFAULT_TRAILING_QUALITY_TAGS, 72),
    ("trailing_tags_11", "positive", "general", "Trailing Quality Tags 11", "", 72),
    ("negative_prompt_1", "negative", "quality", "Negative Prompt 1", "", 120),
    ("negative_prompt_2", "negative", "quality", "Negative Prompt 2", "", 120),
    ("negative_prompt_3", "negative", "general", "Negative Prompt 3", "", 120),
    ("negative_prompt_4", "negative", "general", "Negative Prompt 4", "", 120),
]
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
_ADVANCED_FIELD_SOCKET_PREFIX = "field_"
_ADVANCED_FIELD_SOCKET_RE = re.compile(r"[^A-Za-z0-9_]")


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




def _merge_versioned_settings(defaults: dict[str, Any], value) -> dict[str, Any]:
    merged = _json_clone(defaults)
    incoming = _json_object(value)

    def merge_dict(base: dict[str, Any], update: dict[str, Any]) -> dict[str, Any]:
        for key, update_value in update.items():
            base_value = base.get(key)
            if isinstance(base_value, dict) and isinstance(update_value, dict):
                base[key] = merge_dict(dict(base_value), update_value)
            else:
                base[key] = _prompt_data_json_safe(update_value)
        return base

    return merge_dict(merged, incoming)


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


def _normalize_aio_generation_settings(value) -> dict[str, Any]:
    settings = _merge_versioned_settings(AIO_GENERATION_DEFAULT_SETTINGS, value)
    settings["schema"] = AIO_GENERATION_SETTINGS_SCHEMA
    settings["version"] = _as_int(
        settings.get("version"),
        AIO_GENERATION_SETTINGS_VERSION,
    )
    settings["mode"] = _choice(settings.get("mode"), ("txt2img", "img2img", "inpaint"), "txt2img")

    sampler = settings.setdefault("sampler", {})
    if not isinstance(sampler, dict):
        sampler = {}
        settings["sampler"] = sampler
    sampler["backend"] = _choice(
        sampler.get("backend"),
        ("comfy_ksampler", "spectrum_mod_guidance_advanced", "spectrum_spd_speed"),
        "comfy_ksampler",
    )
    sampler["seed"] = _normalize_aio_seed(sampler.get("seed"))
    sampler["seed_after_generate"] = _choice(
        sampler.get("seed_after_generate"),
        SEED_CONTROL_MODES,
        SEED_CONTROL_FIXED,
    )
    default_sampler = AIO_GENERATION_DEFAULT_SETTINGS["sampler"]
    sampler["steps"] = max(1, min(75, _as_int(sampler.get("steps"), default_sampler["steps"])))
    sampler["cfg"] = max(1.0, min(10.0, _as_float(sampler.get("cfg"), default_sampler["cfg"])))
    sampler["denoise"] = max(0.0, min(1.0, _as_float(sampler.get("denoise"), default_sampler["denoise"])))
    sampler["sampler_name"] = _choice(
        sampler.get("sampler_name"),
        _comfy_sampler_names(),
        default_sampler["sampler_name"],
    )
    sampler["scheduler"] = _choice(
        sampler.get("scheduler"),
        _comfy_scheduler_names(),
        default_sampler["scheduler"],
    )
    spectrum = sampler.setdefault("spectrum", {})
    if not isinstance(spectrum, dict):
        spectrum = {}
        sampler["spectrum"] = spectrum
    default_spectrum = AIO_GENERATION_DEFAULT_SETTINGS["sampler"]["spectrum"]
    spectrum["enabled"] = _as_bool(spectrum.get("enabled"), default_spectrum["enabled"])
    spectrum["window_size"] = max(1.0, min(10.0, _as_float(spectrum.get("window_size"), 2.0)))
    spectrum["flex_window"] = max(0.0, min(2.0, _as_float(spectrum.get("flex_window"), 0.25)))
    spectrum["warmup_steps"] = max(0, min(10000, _as_int(spectrum.get("warmup_steps"), 6)))
    spectrum["tail_actual_steps"] = max(0, min(10000, _as_int(spectrum.get("tail_actual_steps"), 3)))
    spectrum["blend_w"] = max(0.0, min(1.0, _as_float(spectrum.get("blend_w"), 0.3)))
    spectrum["cheby_degree"] = max(1, min(10, _as_int(spectrum.get("cheby_degree"), 3)))
    spectrum["ridge_lambda"] = max(0.001, min(10.0, _as_float(spectrum.get("ridge_lambda"), 0.1)))
    spectrum["history_size"] = max(5, min(10000, _as_int(spectrum.get("history_size"), 100)))
    spectrum["one_sampler_only"] = _as_bool(
        spectrum.get("one_sampler_only"),
        default_spectrum["one_sampler_only"],
    )
    spectrum["verbose"] = _as_bool(spectrum.get("verbose"), default_spectrum["verbose"])
    spectrum["compat_policy"] = _choice(
        spectrum.get("compat_policy"),
        ("legacy", "conservative", "strict"),
        default_spectrum["compat_policy"],
    )
    spd = sampler.setdefault("spd", {})
    if not isinstance(spd, dict):
        spd = {}
        sampler["spd"] = spd
    spd["split_mode"] = _choice(spd.get("split_mode"), ("single",), "single")
    spd["scale"] = max(0.25, min(1.0, _as_float(spd.get("scale"), 0.5)))
    spd["sigma"] = max(0.0, min(1.0, _as_float(spd.get("sigma"), 0.7)))
    spd["adaptive_smc_alpha"] = max(0.0, min(1.0, _as_float(spd.get("adaptive_smc_alpha"), 0.0)))
    sampler["spectrum_extra"] = (
        _json_clone(sampler.get("spectrum_extra"))
        if isinstance(sampler.get("spectrum_extra"), dict)
        else {}
    )
    sampler["spd_extra"] = (
        _json_clone(sampler.get("spd_extra"))
        if isinstance(sampler.get("spd_extra"), dict)
        else {}
    )
    sampler.pop("dave", None)
    corrections = sampler.setdefault("dit_corrections", {})
    if not isinstance(corrections, dict):
        corrections = {}
        sampler["dit_corrections"] = corrections
    default_corrections = AIO_GENERATION_DEFAULT_SETTINGS["sampler"]["dit_corrections"]
    corrections["enabled"] = _as_bool(corrections.get("enabled"), default_corrections["enabled"])
    corrections["dcw_mode"] = _choice(corrections.get("dcw_mode"), ("off", "manual", "auto"), "off")
    corrections["dcw_lambda"] = max(-1.0, min(1.0, _as_float(corrections.get("dcw_lambda"), 0.01)))
    corrections["dcw_band_mask"] = _choice(
        corrections.get("dcw_band_mask"),
        ("LL", "all", "HH", "LH+HL+HH"),
        "LL",
    )
    corrections["dcw_calibrator"] = str(
        corrections.get("dcw_calibrator") or default_corrections["dcw_calibrator"]
    )
    corrections["smc_cfg"] = _as_bool(corrections.get("smc_cfg"), default_corrections["smc_cfg"])
    corrections["adaptive_smc_alpha"] = max(
        0.0,
        min(1.0, _as_float(corrections.get("adaptive_smc_alpha"), 0.0)),
    )
    corrections["smc_cfg_lambda"] = max(0.0, min(20.0, _as_float(corrections.get("smc_cfg_lambda"), 6.0)))
    corrections["cfgpp"] = _as_bool(corrections.get("cfgpp"), default_corrections["cfgpp"])
    corrections["cfgpp_lambda"] = max(0.0, min(8.0, _as_float(corrections.get("cfgpp_lambda"), 0.0)))
    corrections["fsg"] = _as_bool(corrections.get("fsg"), default_corrections["fsg"])
    corrections["fsg_band_lo"] = max(0.0, min(1.0, _as_float(corrections.get("fsg_band_lo"), 0.59)))
    corrections["fsg_band_hi"] = max(0.0, min(1.0, _as_float(corrections.get("fsg_band_hi"), 0.75)))
    corrections["fsg_k"] = max(0, min(32, _as_int(corrections.get("fsg_k"), 3)))
    corrections["fsg_d_sigma"] = max(0.0, min(1.0, _as_float(corrections.get("fsg_d_sigma"), 0.1)))
    corrections["fsg_gamma"] = max(0.0, min(10.0, _as_float(corrections.get("fsg_gamma"), 0.0)))
    corrections["replace_existing_cfg"] = _as_bool(
        corrections.get("replace_existing_cfg"),
        default_corrections["replace_existing_cfg"],
    )

    model_patches = settings.setdefault("model_patches", {})
    if not isinstance(model_patches, dict):
        model_patches = {}
        settings["model_patches"] = model_patches
    aura_flow = model_patches.setdefault("aura_flow", {})
    if not isinstance(aura_flow, dict):
        aura_flow = {}
        model_patches["aura_flow"] = aura_flow
    aura_flow.pop("enabled", None)
    aura_flow["shift"] = max(1.0, min(10.0, _as_float(aura_flow.get("shift"), 3.0)))
    dave = model_patches.setdefault("dave", {})
    if not isinstance(dave, dict):
        dave = {}
        model_patches["dave"] = dave
    default_dave = AIO_GENERATION_DEFAULT_SETTINGS["model_patches"]["dave"]
    dave["enabled"] = _as_bool(dave.get("enabled"), default_dave["enabled"])
    dave["mask"] = str(dave.get("mask") or default_dave["mask"])
    dave["strength"] = max(
        0.0,
        min(1.0, _as_float(dave.get("strength"), default_dave["strength"])),
    )
    dave["tau"] = max(
        0.0,
        min(1.0, _as_float(dave.get("tau"), default_dave["tau"])),
    )
    safe_pag = model_patches.setdefault("safe_pag", {})
    if not isinstance(safe_pag, dict):
        safe_pag = {}
        model_patches["safe_pag"] = safe_pag
    default_safe_pag = AIO_GENERATION_DEFAULT_SETTINGS["model_patches"]["safe_pag"]
    safe_pag["enabled"] = _as_bool(safe_pag.get("enabled"), default_safe_pag["enabled"])
    safe_pag["scale"] = max(
        0.0,
        min(100.0, _as_float(safe_pag.get("scale"), default_safe_pag["scale"])),
    )
    safe_pag["block_indices"] = str(safe_pag.get("block_indices") or default_safe_pag["block_indices"])
    safe_pag["perturbation_strength"] = max(
        0.0,
        min(
            1.0,
            _as_float(safe_pag.get("perturbation_strength"), default_safe_pag["perturbation_strength"]),
        ),
    )
    safe_pag["head_indices"] = str(safe_pag.get("head_indices") or default_safe_pag["head_indices"])
    safe_pag["start_percent"] = max(
        0.0,
        min(1.0, _as_float(safe_pag.get("start_percent"), default_safe_pag["start_percent"])),
    )
    safe_pag["end_percent"] = max(
        0.0,
        min(1.0, _as_float(safe_pag.get("end_percent"), default_safe_pag["end_percent"])),
    )
    safe_pag["rescale"] = max(
        0.0,
        min(1.0, _as_float(safe_pag.get("rescale"), default_safe_pag["rescale"])),
    )
    safe_pag["rescale_mode"] = _choice(safe_pag.get("rescale_mode"), ("full", "partial"), "full")
    kj = model_patches.setdefault("kj", {})
    if not isinstance(kj, dict):
        kj = {}
        model_patches["kj"] = kj
    kj["fp16_accumulation"] = _as_bool(kj.get("fp16_accumulation"), False)
    kj["sage_attention"] = _choice(
        kj.get("sage_attention"),
        (
            "disabled",
            "auto",
            "sageattn_qk_int8_pv_fp16_cuda",
            "sageattn_qk_int8_pv_fp16_triton",
            "sageattn_qk_int8_pv_fp8_cuda",
            "sageattn_qk_int8_pv_fp8_cuda++",
            "sageattn3",
            "sageattn3_per_block_mean",
        ),
        "disabled",
    )
    kj["sage_allow_compile"] = _as_bool(kj.get("sage_allow_compile"), False)
    torch_compile = kj.setdefault("torch_compile", {})
    if not isinstance(torch_compile, dict):
        torch_compile = {}
        kj["torch_compile"] = torch_compile
    torch_compile["enabled"] = _as_bool(torch_compile.get("enabled"), False)
    torch_compile["backend"] = _choice(torch_compile.get("backend"), ("inductor", "cudagraphs"), "inductor")
    torch_compile["fullgraph"] = _as_bool(torch_compile.get("fullgraph"), False)
    torch_compile["mode"] = _choice(
        torch_compile.get("mode"),
        ("default", "max-autotune", "max-autotune-no-cudagraphs", "reduce-overhead"),
        "max-autotune-no-cudagraphs",
    )
    torch_compile["dynamic"] = _choice(torch_compile.get("dynamic"), ("auto", "true", "false"), "false")
    torch_compile["compile_transformer_blocks_only"] = _as_bool(
        torch_compile.get("compile_transformer_blocks_only"),
        True,
    )
    torch_compile["dynamo_cache_size_limit"] = max(
        0,
        min(1024, _as_int(torch_compile.get("dynamo_cache_size_limit"), 64)),
    )
    torch_compile["debug_compile_keys"] = _as_bool(torch_compile.get("debug_compile_keys"), False)
    torch_compile["disable_dynamic_vram"] = _as_bool(torch_compile.get("disable_dynamic_vram"), True)

    mod_guidance = settings.setdefault("mod_guidance", {})
    if not isinstance(mod_guidance, dict):
        mod_guidance = {}
        settings["mod_guidance"] = mod_guidance
    mod_guidance["mode"] = _choice(
        mod_guidance.get("mode"),
        ANIMA_MOD_GUIDANCE_MODES,
        ANIMA_MOD_GUIDANCE_MODE_FROM_PROMPT_DATA,
    )
    mod_guidance["profile"] = _normalize_anima_mod_guidance_profile(
        mod_guidance.get("profile", ANIMA_MOD_GUIDANCE_DEFAULT_PROFILE)
    )
    advanced_mod = mod_guidance.setdefault("advanced", {})
    if not isinstance(advanced_mod, dict):
        advanced_mod = {}
        mod_guidance["advanced"] = advanced_mod
    default_advanced_mod = AIO_GENERATION_DEFAULT_SETTINGS["mod_guidance"]["advanced"]
    advanced_mod["adapter"] = str(advanced_mod.get("adapter") or default_advanced_mod["adapter"])
    advanced_mod["quality_tags"] = str(advanced_mod.get("quality_tags") or default_advanced_mod["quality_tags"])
    advanced_mod["quality_neg"] = str(advanced_mod.get("quality_neg") or default_advanced_mod["quality_neg"])
    advanced_mod["mod_w"] = max(-20.0, min(20.0, _as_float(advanced_mod.get("mod_w"), 3.0)))
    advanced_mod["mod_start_layer"] = max(0, min(999, _as_int(advanced_mod.get("mod_start_layer"), 8)))
    advanced_mod["mod_end_layer"] = max(-1, min(999, _as_int(advanced_mod.get("mod_end_layer"), 27)))
    advanced_mod["mod_taper"] = max(0, min(999, _as_int(advanced_mod.get("mod_taper"), 0)))
    advanced_mod["mod_taper_scale"] = max(
        0.0,
        min(1.0, _as_float(advanced_mod.get("mod_taper_scale"), 0.25)),
    )
    advanced_mod["mod_final_w"] = max(-20.0, min(20.0, _as_float(advanced_mod.get("mod_final_w"), 0.0)))

    artist_mix = settings.setdefault("artist_mix", {})
    if not isinstance(artist_mix, dict):
        artist_mix = {}
        settings["artist_mix"] = artist_mix
    artist_mix["mode"] = _choice(
        artist_mix.get("mode"),
        ARTIST_MIX_INPUT_MODES,
        ARTIST_MIX_MODE_FROM_PROMPT_DATA,
    )
    artist_mix["start_percent"] = _bounded_artist_mix_float(
        artist_mix.get("start_percent"),
        ARTIST_MIX_DEFAULT_START_PERCENT,
        0.0,
        1.0,
    )
    artist_mix["strength_scale"] = _bounded_artist_mix_float(
        artist_mix.get("strength_scale"),
        ARTIST_MIX_DEFAULT_STRENGTH_SCALE,
        0.0,
        5.0,
    )
    artist_mix["style_gain"] = _bounded_artist_mix_float(
        artist_mix.get("style_gain"),
        ARTIST_MIX_DEFAULT_STYLE_GAIN,
        0.0,
        3.0,
    )
    artist_mix["rms_scale_cap"] = _bounded_artist_mix_float(
        artist_mix.get("rms_scale_cap"),
        ARTIST_MIX_DEFAULT_RMS_SCALE_CAP,
        1.0,
        5.0,
    )
    artist_mix["exact_top_k"] = _bounded_artist_mix_int(
        artist_mix.get("exact_top_k"),
        ARTIST_MIX_DEFAULT_EXACT_TOP_K,
        0,
        64,
    )
    artist_mix["cluster_count"] = _bounded_artist_mix_int(
        artist_mix.get("cluster_count"),
        ARTIST_MIX_DEFAULT_CLUSTER_COUNT,
        1,
        32,
    )
    artist_mix["dominant_isolation"] = _as_bool(
        artist_mix.get("dominant_isolation"),
        ARTIST_MIX_DEFAULT_DOMINANT_ISOLATION,
    )
    artist_mix["dominant_threshold"] = _bounded_artist_mix_float(
        artist_mix.get("dominant_threshold"),
        ARTIST_MIX_DEFAULT_DOMINANT_THRESHOLD,
        0.0,
        1.0,
    )

    for key in ("highres", "detailer", "upscale", "postprocess", "save"):
        section = settings.setdefault(key, {})
        if not isinstance(section, dict):
            section = {}
            settings[key] = section
        section["enabled"] = _as_bool(section.get("enabled"), False)
    highres = settings["highres"]
    default_highres = AIO_GENERATION_DEFAULT_SETTINGS["highres"]
    highres["scale_by"] = max(0.01, min(8.0, _as_float(highres.get("scale_by"), default_highres["scale_by"])))
    highres["upscale_method"] = _choice(
        highres.get("upscale_method"),
        IMAGE_UPSCALE_METHODS,
        default_highres["upscale_method"],
    )
    highres["multiple"] = _choice(highres.get("multiple"), IMAGE_SCALE_MULTIPLES, default_highres["multiple"])
    highres["max_long_edge"] = max(
        0,
        min(16384, _as_int(highres.get("max_long_edge"), default_highres["max_long_edge"])),
    )
    highres["steps"] = max(1, min(75, _as_int(highres.get("steps"), default_highres["steps"])))
    highres["inherit_sampler_settings"] = _as_bool(
        highres.get("inherit_sampler_settings"),
        default_highres["inherit_sampler_settings"],
    )
    highres["cfg"] = max(1.0, min(10.0, _as_float(highres.get("cfg"), default_highres["cfg"])))
    highres["sampler_name"] = _choice(
        highres.get("sampler_name"),
        _comfy_sampler_names(),
        default_highres["sampler_name"],
    )
    highres["scheduler"] = _choice(
        highres.get("scheduler"),
        _comfy_scheduler_names(),
        default_highres["scheduler"],
    )
    highres["denoise"] = max(0.0, min(1.0, _as_float(highres.get("denoise"), default_highres["denoise"])))
    highres["spectrum"] = _normalize_aio_spectrum_settings(
        highres.get("spectrum"),
        default_highres["spectrum"],
    )
    highres["dit_corrections"] = _normalize_aio_dit_corrections_settings(
        highres.get("dit_corrections"),
        default_highres["dit_corrections"],
    )
    upscale = settings["upscale"]
    default_upscale = AIO_GENERATION_DEFAULT_SETTINGS["upscale"]
    upscale["backend"] = _choice(
        upscale.get("backend"),
        AIO_FINAL_UPSCALE_BACKENDS,
        default_upscale["backend"],
    )
    upscale["scale_by"] = max(0.05, min(4.0, _as_float(upscale.get("scale_by"), default_upscale["scale_by"])))
    upscale["steps"] = max(1, min(1000, _as_int(upscale.get("steps"), default_upscale["steps"])))
    upscale["inherit_sampler_settings"] = _as_bool(
        upscale.get("inherit_sampler_settings"),
        default_upscale["inherit_sampler_settings"],
    )
    upscale["cfg"] = max(0.0, min(100.0, _as_float(upscale.get("cfg"), default_upscale["cfg"])))
    upscale["sampler_name"] = _choice(
        upscale.get("sampler_name"),
        _comfy_sampler_names(),
        default_upscale["sampler_name"],
    )
    upscale["scheduler"] = _choice(
        upscale.get("scheduler"),
        _comfy_scheduler_names(),
        default_upscale["scheduler"],
    )
    upscale["denoise"] = max(0.0, min(1.0, _as_float(upscale.get("denoise"), default_upscale["denoise"])))
    max_resolution = _comfy_max_resolution()
    legacy_upscale_fit = upscale.pop("fit", None)
    upscale["spectrum"] = _normalize_aio_spectrum_settings(
        upscale.get("spectrum"),
        default_upscale["spectrum"],
    )
    upscale["dit_corrections"] = _normalize_aio_dit_corrections_settings(
        upscale.get("dit_corrections"),
        default_upscale["dit_corrections"],
    )
    usdu = upscale.setdefault("usdu", {})
    if not isinstance(usdu, dict):
        usdu = {}
        upscale["usdu"] = usdu
    default_usdu = default_upscale["usdu"]
    usdu["upscale_model_name"] = str(
        usdu.get("upscale_model_name") or default_usdu["upscale_model_name"]
    )
    usdu["auto_tile_size"] = _as_bool(usdu.get("auto_tile_size"), default_usdu["auto_tile_size"])
    prompt_mode = str(usdu.get("prompt_mode") or default_usdu["prompt_mode"])
    if prompt_mode == "quality_tags_only":
        prompt_mode = AIO_USDU_PROMPT_NO_GENERAL
    usdu["prompt_mode"] = _choice(prompt_mode, AIO_USDU_PROMPT_MODES, default_usdu["prompt_mode"])
    usdu["mode_type"] = _choice(usdu.get("mode_type"), AIO_USDU_MODE_TYPES, default_usdu["mode_type"])
    auto_tile_target = max(
        64,
        min(max_resolution, _as_int(usdu.get("auto_tile_target"), default_usdu["auto_tile_target"])),
    )
    auto_tile_min = max(
        64,
        min(max_resolution, _as_int(usdu.get("auto_tile_min"), default_usdu["auto_tile_min"])),
    )
    auto_tile_max = max(
        auto_tile_min,
        min(max_resolution, _as_int(usdu.get("auto_tile_max"), default_usdu["auto_tile_max"])),
    )
    if auto_tile_target < auto_tile_min:
        auto_tile_min = auto_tile_target
    if auto_tile_target > auto_tile_max:
        auto_tile_max = auto_tile_target
    usdu["auto_tile_target"] = auto_tile_target
    usdu["auto_tile_min"] = auto_tile_min
    usdu["auto_tile_max"] = max(auto_tile_min, auto_tile_max)
    usdu["tile_width"] = max(64, min(max_resolution, _as_int(usdu.get("tile_width"), default_usdu["tile_width"])))
    usdu["tile_height"] = max(64, min(max_resolution, _as_int(usdu.get("tile_height"), default_usdu["tile_height"])))
    usdu["mask_blur"] = max(0, min(64, _as_int(usdu.get("mask_blur"), default_usdu["mask_blur"])))
    usdu["tile_padding"] = max(0, min(max_resolution, _as_int(usdu.get("tile_padding"), default_usdu["tile_padding"])))
    usdu["seam_fix_mode"] = _choice(
        usdu.get("seam_fix_mode"),
        AIO_USDU_SEAM_FIX_MODES,
        default_usdu["seam_fix_mode"],
    )
    usdu["seam_fix_denoise"] = max(
        0.0,
        min(1.0, _as_float(usdu.get("seam_fix_denoise"), default_usdu["seam_fix_denoise"])),
    )
    usdu["seam_fix_width"] = max(
        0,
        min(max_resolution, _as_int(usdu.get("seam_fix_width"), default_usdu["seam_fix_width"])),
    )
    usdu["seam_fix_mask_blur"] = max(
        0,
        min(64, _as_int(usdu.get("seam_fix_mask_blur"), default_usdu["seam_fix_mask_blur"])),
    )
    usdu["seam_fix_padding"] = max(
        0,
        min(max_resolution, _as_int(usdu.get("seam_fix_padding"), default_usdu["seam_fix_padding"])),
    )
    usdu["force_uniform_tiles"] = _as_bool(usdu.get("force_uniform_tiles"), default_usdu["force_uniform_tiles"])
    usdu["tiled_decode"] = _as_bool(usdu.get("tiled_decode"), default_usdu["tiled_decode"])
    usdu["batch_size"] = max(1, min(4096, _as_int(usdu.get("batch_size"), default_usdu["batch_size"])))
    resshift = upscale.setdefault("resshift", {})
    if not isinstance(resshift, dict):
        resshift = {}
        upscale["resshift"] = resshift
    default_resshift = default_upscale["resshift"]
    resshift["scale"] = _choice(resshift.get("scale"), AIO_RESHIFT_SCALES, default_resshift["scale"])
    resshift["student_name"] = str(resshift.get("student_name") or default_resshift["student_name"])
    resshift["dtype"] = _choice(resshift.get("dtype"), AIO_RESHIFT_DTYPES, default_resshift["dtype"])
    resshift["chop"] = max(256, min(4096, _as_int(resshift.get("chop"), default_resshift["chop"])))
    resshift["overlap"] = max(0, min(512, _as_int(resshift.get("overlap"), default_resshift["overlap"])))
    resshift["tile_batch"] = max(1, min(32, _as_int(resshift.get("tile_batch"), default_resshift["tile_batch"])))
    postprocess = settings.setdefault("postprocess", {})
    if not isinstance(postprocess, dict):
        postprocess = {}
        settings["postprocess"] = postprocess
    default_postprocess = AIO_GENERATION_DEFAULT_SETTINGS["postprocess"]
    fit = postprocess.setdefault("fit", {})
    if not isinstance(fit, dict):
        fit = {}
        postprocess["fit"] = fit
    default_fit = default_postprocess["fit"]
    if isinstance(legacy_upscale_fit, dict):
        if _as_bool(legacy_upscale_fit.get("enabled"), False):
            postprocess["enabled"] = True
        for key in ("mode", "max_long_edge", "max_megapixels", "method"):
            if key in legacy_upscale_fit and fit.get(key) == default_fit.get(key):
                fit[key] = legacy_upscale_fit[key]
    postprocess["enabled"] = _as_bool(postprocess.get("enabled"), default_postprocess["enabled"])
    fit["mode"] = _choice(fit.get("mode"), AIO_FINAL_FIT_MODES, default_fit["mode"])
    fit["max_long_edge"] = max(
        64,
        min(max_resolution, _as_int(fit.get("max_long_edge"), default_fit["max_long_edge"])),
    )
    fit["max_megapixels"] = max(
        0.1,
        min(256.0, _as_float(fit.get("max_megapixels"), default_fit["max_megapixels"])),
    )
    fit["method"] = _choice(fit.get("method"), IMAGE_UPSCALE_METHODS, default_fit["method"])
    detailer = settings["detailer"]
    sam3 = detailer.setdefault("sam3", {})
    if not isinstance(sam3, dict):
        sam3 = {}
        detailer["sam3"] = sam3
    normalized_order = _aio_detailer_target_order(detailer)
    detailer["order"] = normalized_order
    sam3["context"] = _choice(sam3.get("context"), ("load_checkpoint",), "load_checkpoint")
    sam3["checkpoint"] = str(sam3.get("checkpoint") or "sam3.1_multiplex_fp16.safetensors")
    for target_name in normalized_order:
        defaults = _aio_detailer_target_defaults(target_name)
        target = detailer.setdefault(target_name, {})
        if not isinstance(target, dict):
            target = {}
            detailer[target_name] = target
        target["label"] = str(target.get("label") or defaults.get("label") or target_name.title())
        target["enabled"] = _as_bool(target.get("enabled"), defaults["enabled"])
        target["detect_prompt"] = str(target.get("detect_prompt") or defaults["detect_prompt"])
        target["detect_count"] = max(1, min(20, _as_int(target.get("detect_count"), defaults["detect_count"])))
        target["threshold"] = max(0.0, min(1.0, _as_float(target.get("threshold"), defaults["threshold"])))
        target["refine_iterations"] = max(
            0,
            min(16, _as_int(target.get("refine_iterations"), defaults["refine_iterations"])),
        )
        target["individual_masks"] = _as_bool(target.get("individual_masks"), defaults["individual_masks"])
        target["combined"] = _as_bool(target.get("combined"), defaults["combined"])
        target["crop_factor"] = max(1.0, min(16.0, _as_float(target.get("crop_factor"), defaults["crop_factor"])))
        target["bbox_fill"] = _as_bool(target.get("bbox_fill"), defaults["bbox_fill"])
        target["drop_size"] = max(1, min(4096, _as_int(target.get("drop_size"), defaults["drop_size"])))
        target["contour_fill"] = _as_bool(target.get("contour_fill"), defaults["contour_fill"])
        target["guide_size"] = max(64, min(4096, _as_int(target.get("guide_size"), defaults["guide_size"])))
        target["guide_size_for"] = _as_bool(target.get("guide_size_for"), defaults["guide_size_for"])
        target["max_size"] = max(64, min(8192, _as_int(target.get("max_size"), defaults["max_size"])))
        target["steps"] = max(1, min(75, _as_int(target.get("steps"), defaults["steps"])))
        target["inherit_sampler_settings"] = _as_bool(
            target.get("inherit_sampler_settings"),
            defaults["inherit_sampler_settings"],
        )
        target["cfg"] = max(1.0, min(10.0, _as_float(target.get("cfg"), defaults["cfg"])))
        target["sampler_name"] = _choice(
            target.get("sampler_name"),
            _comfy_sampler_names(),
            defaults["sampler_name"],
        )
        target["scheduler"] = _choice(
            target.get("scheduler"),
            _impact_scheduler_names(),
            defaults["scheduler"],
        )
        target["denoise"] = max(0.0, min(1.0, _as_float(target.get("denoise"), defaults["denoise"])))
        target["feather"] = max(0, min(256, _as_int(target.get("feather"), defaults["feather"])))
        target["noise_mask"] = _as_bool(target.get("noise_mask"), defaults["noise_mask"])
        target["force_inpaint"] = _as_bool(target.get("force_inpaint"), defaults["force_inpaint"])
        target["wildcard"] = str(target.get("wildcard") or "")
        target["cycle"] = max(1, min(16, _as_int(target.get("cycle"), defaults["cycle"])))
        target["alignment"] = _choice(str(target.get("alignment") or defaults["alignment"]), ("impact", "none", "32", "64"), "32")
        target["inpaint_model"] = _as_bool(target.get("inpaint_model"), defaults["inpaint_model"])
        target["noise_mask_feather"] = max(
            0,
            min(256, _as_int(target.get("noise_mask_feather"), defaults["noise_mask_feather"])),
        )
        target["tiled_encode"] = _as_bool(target.get("tiled_encode"), defaults["tiled_encode"])
        target["tiled_decode"] = _as_bool(target.get("tiled_decode"), defaults["tiled_decode"])
        target["spectrum"] = _normalize_aio_spectrum_settings(target.get("spectrum"), defaults["spectrum"])
        target["dit_corrections"] = _normalize_aio_dit_corrections_settings(
            target.get("dit_corrections"),
            defaults["dit_corrections"],
        )
    settings["save"]["backend"] = _choice(
        settings["save"].get("backend"),
        ("image_saver", "comfy_save_image"),
        "image_saver",
    )
    settings["save"].pop("filename_prefix", None)
    image_saver = settings["save"].setdefault("image_saver", {})
    if not isinstance(image_saver, dict):
        image_saver = {}
        settings["save"]["image_saver"] = image_saver
    default_image_saver = AIO_GENERATION_DEFAULT_SETTINGS["save"]["image_saver"]
    image_saver["filename"] = str(image_saver.get("filename") or default_image_saver["filename"])
    image_saver["path"] = str(image_saver.get("path") or default_image_saver["path"])
    image_saver["extension"] = _choice(
        image_saver.get("extension"),
        ("png", "jpeg", "jpg", "webp"),
        default_image_saver["extension"],
    )
    image_saver["lossless_webp"] = _as_bool(
        image_saver.get("lossless_webp"),
        default_image_saver["lossless_webp"],
    )
    image_saver["quality_jpeg_or_webp"] = max(
        1,
        min(100, _as_int(image_saver.get("quality_jpeg_or_webp"), default_image_saver["quality_jpeg_or_webp"])),
    )
    image_saver["optimize_png"] = _as_bool(
        image_saver.get("optimize_png"),
        default_image_saver["optimize_png"],
    )
    image_saver["counter"] = max(0, _as_int(image_saver.get("counter"), default_image_saver["counter"]))
    image_saver["clip_skip"] = max(
        -24,
        min(24, _as_int(image_saver.get("clip_skip"), default_image_saver["clip_skip"])),
    )
    image_saver["time_format"] = str(image_saver.get("time_format") or default_image_saver["time_format"])
    image_saver["save_workflow_as_json"] = _as_bool(
        image_saver.get("save_workflow_as_json"),
        default_image_saver["save_workflow_as_json"],
    )
    image_saver["embed_workflow"] = _as_bool(
        image_saver.get("embed_workflow"),
        default_image_saver["embed_workflow"],
    )
    image_saver["save_prompt_metadata"] = _as_bool(
        image_saver.get("save_prompt_metadata"),
        default_image_saver["save_prompt_metadata"],
    )
    image_saver["additional_hashes"] = str(image_saver.get("additional_hashes") or "")
    image_saver["additional_hash_bundles"] = _normalize_aio_hash_bundles(
        image_saver.get("additional_hash_bundles")
    )
    image_saver["civitai_hash_fetchers"] = _normalize_aio_civitai_hash_fetchers(
        image_saver.get("civitai_hash_fetchers")
    )
    image_saver["download_civitai_data"] = _as_bool(
        image_saver.get("download_civitai_data"),
        default_image_saver["download_civitai_data"],
    )
    image_saver["easy_remix"] = _as_bool(
        image_saver.get("easy_remix"),
        default_image_saver["easy_remix"],
    )
    image_saver.pop("show_preview", None)
    image_saver["custom"] = str(image_saver.get("custom") or "")
    preview = settings.setdefault("preview", {})
    if not isinstance(preview, dict):
        preview = {}
        settings["preview"] = preview
    default_preview = AIO_GENERATION_DEFAULT_SETTINGS["preview"]
    preview["intermediate_images"] = _as_bool(
        preview.get("intermediate_images"),
        default_preview["intermediate_images"],
    )
    preview["compare_previous"] = _as_bool(
        preview.get("compare_previous"),
        default_preview["compare_previous"],
    )
    preview["image_feed"] = _as_bool(
        preview.get("image_feed"),
        default_preview["image_feed"],
    )
    preview["feed_count"] = max(
        1,
        min(100, _as_int(preview.get("feed_count"), default_preview["feed_count"])),
    )
    return settings


def _normalize_aio_hash_bundles(value) -> list[str]:
    if isinstance(value, str):
        try:
            value = json.loads(value or "[]")
        except json.JSONDecodeError:
            value = [value]
    if not isinstance(value, list):
        return []
    bundles: list[str] = []
    for item in value:
        text = str(item or "").strip(" ,\n\r\t")
        if text:
            bundles.append(text)
    return bundles


def _normalize_aio_civitai_hash_fetchers(value) -> list[dict[str, Any]]:
    if isinstance(value, str):
        try:
            value = json.loads(value or "[]")
        except json.JSONDecodeError:
            value = []
    if not isinstance(value, list):
        return []
    fetchers: list[dict[str, Any]] = []
    for item in value:
        if not isinstance(item, dict):
            continue
        username = str(item.get("username") or "").strip()
        model_name = str(item.get("model_name") or "").strip()
        version = str(item.get("version") or "").strip()
        if not any((username, model_name, version)):
            continue
        fetchers.append({
            "enabled": _as_bool(item.get("enabled"), True),
            "username": username,
            "model_name": model_name,
            "version": version,
        })
    return fetchers


def _aio_image_saver_civitai_hash_fetcher_entries(image_saver: dict[str, Any]) -> list[str]:
    fetcher_settings = [
        item
        for item in _normalize_aio_civitai_hash_fetchers(image_saver.get("civitai_hash_fetchers"))
        if _as_bool(item.get("enabled"), True)
    ]
    if not fetcher_settings:
        return []

    fetcher_cls = _require_custom_node_class(
        "Civitai Hash Fetcher (Image Saver)",
        "ComfyUI-Image-Saver",
        "Required for AiO Save Options > Civitai Hash Fetcher rows.",
    )
    fetcher = fetcher_cls()
    get_hash = getattr(fetcher, "get_autov3_hash", None)
    if get_hash is None:
        raise RuntimeError(
            "[EasyUseAnima] Civitai Hash Fetcher (Image Saver) does not expose get_autov3_hash()."
        )

    entries: list[str] = []
    for item in fetcher_settings:
        username = str(item.get("username") or "").strip()
        model_name = str(item.get("model_name") or "").strip()
        version = str(item.get("version") or "").strip()
        if not username and not model_name:
            continue
        if not username or not model_name:
            raise RuntimeError(
                "[EasyUseAnima] Civitai Hash Fetcher requires both username and model_name."
            )
        try:
            result = get_hash(username, model_name, version)
        except Exception as exc:
            logger.warning(
                "[EasyUseAnima] Civitai Hash Fetcher failed for '%s/%s'%s; skipping metadata hash: %s",
                username,
                model_name,
                f" version '{version}'" if version else "",
                exc,
            )
            continue
        hash_value = _single_value(result)
        hash_text = str(hash_value or "").strip()
        if (
            not hash_text
            or hash_text.lower().startswith("error:")
            or hash_text.lower().startswith("no ")
        ):
            logger.warning(
                "[EasyUseAnima] Civitai Hash Fetcher returned no usable hash for '%s/%s'%s; "
                "skipping metadata hash: %s",
                username,
                model_name,
                f" version '{version}'" if version else "",
                hash_text or "empty hash",
            )
            continue
        entries.append(f"{model_name}:{hash_text}")
    return entries


def _aio_image_saver_additional_hashes(image_saver: dict[str, Any]) -> str:
    parts = []
    base = str(image_saver.get("additional_hashes") or "").strip(" ,\n\r\t")
    if base:
        parts.append(base)
    parts.extend(_normalize_aio_hash_bundles(image_saver.get("additional_hash_bundles")))
    parts.extend(_aio_image_saver_civitai_hash_fetcher_entries(image_saver))
    return ",".join(part for part in parts if part)


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


def _preferred_name_default(names: list[str], candidates: tuple[str, ...]) -> str:
    if not names:
        return candidates[0] if candidates else ""
    for candidate in candidates:
        if candidate in names:
            return candidate
    normalized = {
        str(name).replace("/", "\\").rsplit("\\", 1)[-1].lower(): str(name)
        for name in names
    }
    for candidate in candidates:
        basename = candidate.replace("/", "\\").rsplit("\\", 1)[-1].lower()
        if basename in normalized:
            return normalized[basename]
    return names[0]


def _preferred_checkpoint_default(names: list[str], preferred: str) -> str:
    return preferred if preferred in names else names[0]


def _preferred_clip_type_default(names: list[str]) -> str:
    return "qwen_image" if "qwen_image" in names else _choice("", names, "stable_diffusion")


def _impact_core_module():
    module = sys.modules.get("impact.core")
    if module is not None:
        return module
    try:
        import impact.core as core  # type: ignore

        return core
    except Exception:
        pass
    try:
        from modules.impact import core  # type: ignore

        return core
    except Exception:
        pass
    return None


def _impact_scheduler_names() -> list[str]:
    core = _impact_core_module()
    if core is not None:
        try:
            return list(core.get_schedulers())
        except Exception:
            pass
    try:
        import comfy.samplers  # type: ignore

        return list(comfy.samplers.KSampler.SCHEDULERS)
    except Exception:
        return ["normal", "karras", "exponential", "sgm_uniform", "simple", "ddim_uniform"]


def _find_impact_detailer_class():
    try:
        import nodes as comfy_nodes  # type: ignore

        cls = getattr(comfy_nodes, "NODE_CLASS_MAPPINGS", {}).get("DetailerForEach")
        if cls is not None:
            return cls
    except Exception:
        pass

    for module in list(sys.modules.values()):
        mappings = getattr(module, "NODE_CLASS_MAPPINGS", None)
        if isinstance(mappings, dict):
            cls = mappings.get("DetailerForEach")
            if cls is not None:
                return cls

    try:
        from impact.impact_pack import DetailerForEach  # type: ignore

        return DetailerForEach
    except Exception:
        pass
    try:
        from modules.impact.impact_pack import DetailerForEach  # type: ignore

        return DetailerForEach
    except Exception:
        pass

    raise RuntimeError(
        "[EasyUseAnima] SAM3 Detailer requires ComfyUI Impact Pack's DetailerForEach. "
        "Install/enable ComfyUI-Impact-Pack, then restart ComfyUI."
    )


def _find_comfy_node_class(node_id: str):
    try:
        import nodes as comfy_nodes  # type: ignore
    except Exception:
        comfy_nodes = None
    return _adapter_find_comfy_node_class(node_id, comfy_nodes)


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


def _load_checkpoint_with_comfy(ckpt_name: str):
    loader_cls = _find_comfy_node_class("CheckpointLoaderSimple")
    if loader_cls is None:
        raise RuntimeError("[EasyUseAnima] Could not find ComfyUI CheckpointLoaderSimple.")
    loader = loader_cls()
    method = getattr(loader, "load_checkpoint", None)
    if method is None:
        raise RuntimeError("[EasyUseAnima] CheckpointLoaderSimple does not expose load_checkpoint.")
    return method(ckpt_name)


def _load_diffusion_model_with_comfy(unet_name: str, weight_dtype: str = "default"):
    loader_cls = _find_comfy_node_class("UNETLoader")
    if loader_cls is None:
        raise RuntimeError("[EasyUseAnima] Could not find ComfyUI UNETLoader.")
    loader = loader_cls()
    method = getattr(loader, "load_unet", None)
    if method is None:
        raise RuntimeError("[EasyUseAnima] UNETLoader does not expose load_unet.")
    values = _node_output_tuple(method(str(unet_name), str(weight_dtype or "default")))
    if not values:
        raise RuntimeError("[EasyUseAnima] UNETLoader returned no MODEL.")
    return values[0]


def _load_vae_with_comfy(vae_name: str):
    loader_cls = _find_comfy_node_class("VAELoader")
    if loader_cls is None:
        raise RuntimeError("[EasyUseAnima] Could not find ComfyUI VAELoader.")
    loader = loader_cls()
    method = getattr(loader, "load_vae", None)
    if method is None:
        raise RuntimeError("[EasyUseAnima] VAELoader does not expose load_vae.")
    values = _node_output_tuple(method(str(vae_name)))
    if not values:
        raise RuntimeError("[EasyUseAnima] VAELoader returned no VAE.")
    return values[0]


def _load_clip_with_comfy(clip_name: str, clip_type: str = "qwen_image", device: str = "default"):
    loader_cls = _find_comfy_node_class("CLIPLoader")
    if loader_cls is None:
        raise RuntimeError("[EasyUseAnima] Could not find ComfyUI CLIPLoader.")
    loader = loader_cls()
    method = getattr(loader, "load_clip", None)
    if method is None:
        raise RuntimeError("[EasyUseAnima] CLIPLoader does not expose load_clip.")
    values = _node_output_tuple(method(str(clip_name), str(clip_type or "qwen_image"), str(device or "default")))
    if not values:
        raise RuntimeError("[EasyUseAnima] CLIPLoader returned no CLIP.")
    return values[0]


def _encode_with_comfy_clip(clip, text: str):
    encoder_cls = _find_comfy_node_class("CLIPTextEncode")
    if encoder_cls is None:
        raise RuntimeError("[EasyUseAnima] Could not find ComfyUI CLIPTextEncode.")
    encoder = encoder_cls()
    method = getattr(encoder, "encode", None)
    if method is None:
        raise RuntimeError("[EasyUseAnima] CLIPTextEncode does not expose encode.")
    result = method(clip, text)
    if not isinstance(result, tuple) or not result:
        raise RuntimeError("[EasyUseAnima] CLIPTextEncode returned no conditioning.")
    return result[0]


def _find_sam3_detect_class():
    cls = _find_comfy_node_class("SAM3_Detect")
    if cls is not None:
        return cls
    # Optional ComfyUI native node integration.
    # This imports only the built-in comfy_extras.nodes_sam3.SAM3_Detect class.
    # It does not load user-provided modules or execute dynamic code.
    try:
        from comfy_extras.nodes_sam3 import SAM3_Detect  # type: ignore

        return SAM3_Detect
    except Exception:
        pass
    raise RuntimeError(
        "[EasyUseAnima] SAM3_Detect was not found. "
        "Use a ComfyUI build with native SAM3 support, then restart ComfyUI."
    )


def _find_impact_mask_to_segs_class():
    cls = _find_comfy_node_class("MaskToSEGS")
    if cls is not None:
        return cls

    for module in list(sys.modules.values()):
        mappings = getattr(module, "NODE_CLASS_MAPPINGS", None)
        if isinstance(mappings, dict):
            cls = mappings.get("MaskToSEGS")
            if cls is not None:
                return cls

    try:
        from impact.segs_nodes import MaskToSEGS  # type: ignore

        return MaskToSEGS
    except Exception:
        pass
    try:
        from modules.impact.segs_nodes import MaskToSEGS  # type: ignore

        return MaskToSEGS
    except Exception:
        pass
    try:
        from impact.impact_pack import MaskToSEGS  # type: ignore

        return MaskToSEGS
    except Exception:
        pass
    try:
        from modules.impact.impact_pack import MaskToSEGS  # type: ignore

        return MaskToSEGS
    except Exception:
        pass

    raise RuntimeError(
        "[EasyUseAnima] Anima SAM3 Detailer requires ComfyUI Impact Pack's MaskToSEGS. "
        "Install/enable ComfyUI-Impact-Pack, then restart ComfyUI."
    )


def _find_loaded_node_class(node_id: str):
    return _adapter_find_loaded_node_class(node_id, _find_comfy_node_class)




def _generate_empty_latent_with_comfy(width: int, height: int):
    latent_cls = _find_comfy_node_class("EmptyLatentImage")
    if latent_cls is None:
        raise RuntimeError("[EasyUseAnima] Could not find ComfyUI EmptyLatentImage.")
    latent_node = latent_cls()
    generate = getattr(latent_node, "generate", None)
    if generate is None:
        raise RuntimeError("[EasyUseAnima] EmptyLatentImage does not expose generate().")
    result = generate(max(16, int(width)), max(16, int(height)), 1)
    values = _node_output_tuple(result)
    if not values:
        raise RuntimeError("[EasyUseAnima] EmptyLatentImage returned no LATENT.")
    return values[0]


def _sample_latent_with_comfy(
    model,
    seed: int,
    steps: int,
    cfg: float,
    sampler_name: str,
    scheduler: str,
    positive,
    negative,
    latent_image,
    denoise: float,
):
    sampler_cls = _find_comfy_node_class("KSampler")
    if sampler_cls is None:
        raise RuntimeError("[EasyUseAnima] Could not find ComfyUI KSampler.")
    sampler = sampler_cls()
    sample = getattr(sampler, "sample", None)
    if sample is None:
        raise RuntimeError("[EasyUseAnima] KSampler does not expose sample().")
    result = sample(
        model,
        _resolve_aio_runtime_seed(seed),
        max(1, int(steps)),
        float(cfg),
        str(sampler_name),
        str(scheduler),
        positive,
        negative,
        latent_image,
        float(denoise),
    )
    values = _node_output_tuple(result)
    if not values:
        raise RuntimeError("[EasyUseAnima] KSampler returned no LATENT.")
    return values[0]


def _patch_model_sampling_aura_flow(model, aura_settings: dict[str, Any]):
    aura_cls = _find_comfy_node_class("ModelSamplingAuraFlow")
    if aura_cls is None:
        raise RuntimeError(
            "[EasyUseAnima] Missing required core node 'ModelSamplingAuraFlow'. "
            "Use a ComfyUI build that includes ModelSamplingAuraFlow, then restart ComfyUI."
        )
    patcher = aura_cls()
    patch = getattr(patcher, "patch_aura", None)
    if patch is None:
        raise RuntimeError("[EasyUseAnima] ModelSamplingAuraFlow does not expose patch_aura().")
    values = _node_output_tuple(patch(model, _as_float(aura_settings.get("shift"), 3.0)))
    if not values:
        raise RuntimeError("[EasyUseAnima] ModelSamplingAuraFlow returned no MODEL.")
    return values[0]


def _apply_aio_kj_model_patches(model, kj_settings: dict[str, Any]):
    patched = model
    if kj_settings.get("fp16_accumulation"):
        torch_settings_cls = _require_custom_node_class(
            "ModelPatchTorchSettings",
            "ComfyUI-KJNodes",
            "Repository: https://github.com/kijai/ComfyUI-KJNodes",
        )
        values = _node_output_tuple(
            torch_settings_cls().patch(patched, True)
        )
        if not values:
            raise RuntimeError("[EasyUseAnima] ModelPatchTorchSettings returned no MODEL.")
        patched = values[0]

    sage_attention = str(kj_settings.get("sage_attention") or "disabled")
    if sage_attention != "disabled":
        sage_cls = _require_custom_node_class(
            "PathchSageAttentionKJ",
            "ComfyUI-KJNodes",
            "Repository: https://github.com/kijai/ComfyUI-KJNodes",
        )
        values = _node_output_tuple(
            sage_cls().patch(
                patched,
                sage_attention,
                _as_bool(kj_settings.get("sage_allow_compile"), False),
            )
        )
        if not values:
            raise RuntimeError("[EasyUseAnima] PathchSageAttentionKJ returned no MODEL.")
        patched = values[0]

    compile_settings = kj_settings.get("torch_compile", {})
    if isinstance(compile_settings, dict) and compile_settings.get("enabled"):
        compile_cls = _require_custom_node_class(
            "TorchCompileModelAdvanced",
            "ComfyUI-KJNodes",
            "Repository: https://github.com/kijai/ComfyUI-KJNodes",
        )
        values = _node_output_tuple(
            compile_cls().patch(
                patched,
                str(compile_settings.get("backend") or "inductor"),
                _as_bool(compile_settings.get("fullgraph"), False),
                str(compile_settings.get("mode") or "default"),
                str(compile_settings.get("dynamic") or "auto"),
                _as_int(compile_settings.get("dynamo_cache_size_limit"), 64),
                _as_bool(compile_settings.get("compile_transformer_blocks_only"), True),
                _as_bool(compile_settings.get("debug_compile_keys"), False),
                _as_bool(compile_settings.get("disable_dynamic_vram"), False),
            )
        )
        if not values:
            raise RuntimeError("[EasyUseAnima] TorchCompileModelAdvanced returned no MODEL.")
        patched = values[0]
    return patched


def _apply_aio_model_patches(model, settings: dict[str, Any]):
    model_patches = settings.get("model_patches", {})
    if not isinstance(model_patches, dict):
        return model
    patched = _patch_model_sampling_aura_flow(
        model,
        model_patches.get("aura_flow", {}) if isinstance(model_patches.get("aura_flow"), dict) else {},
    )
    dave_settings = model_patches.get("dave", {})
    if isinstance(dave_settings, dict) and _as_bool(dave_settings.get("enabled"), False):
        patched = _apply_aio_anima_dave_patch(patched, dave_settings)
    safe_pag_settings = model_patches.get("safe_pag", {})
    if isinstance(safe_pag_settings, dict) and _as_bool(safe_pag_settings.get("enabled"), False):
        patched = _apply_aio_safe_pag_patch(patched, safe_pag_settings)
    kj_settings = model_patches.get("kj", {})
    if isinstance(kj_settings, dict):
        patched = _apply_aio_kj_model_patches(patched, kj_settings)
    return patched


def _normalize_aio_lora_stack(lora_stack) -> list[tuple[str, float, float]]:
    if isinstance(lora_stack, dict) and "__value__" in lora_stack:
        lora_stack = lora_stack["__value__"]
    if isinstance(lora_stack, str):
        try:
            lora_stack = json.loads(lora_stack or "[]")
        except json.JSONDecodeError:
            lora_stack = []
    if not isinstance(lora_stack, list):
        return []

    entries: list[tuple[str, float, float]] = []
    for item in lora_stack:
        if isinstance(item, dict):
            raw_name = item.get("name", item.get("lora", item.get("lora_name", "")))
            model_strength = item.get("strength_model", item.get("model_strength", item.get("strength", 1.0)))
            clip_strength = item.get("strength_clip", item.get("clip_strength", item.get("strengthTwo", model_strength)))
        elif isinstance(item, (list, tuple)) and len(item) >= 3:
            raw_name, model_strength, clip_strength = item[:3]
        else:
            continue
        name = str(raw_name or "").strip()
        if not name or name.lower() == "none":
            continue
        entries.append((
            _lora_stack_name(name),
            _as_float(model_strength, 1.0),
            _as_float(clip_strength, _as_float(model_strength, 1.0)),
        ))
    return entries


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


def _apply_aio_lora_stack(model, clip, lora_stack):
    entries = _normalize_aio_lora_stack(lora_stack)
    if not entries:
        return model, clip, []

    loader_cls = _find_comfy_node_class("LoraLoader")
    if loader_cls is None:
        raise RuntimeError("[EasyUseAnima] Could not find ComfyUI core LoraLoader.")
    loader = loader_cls()
    load_lora = getattr(loader, "load_lora", None)
    if load_lora is None:
        raise RuntimeError("[EasyUseAnima] LoraLoader does not expose load_lora().")

    patched_model = model
    patched_clip = clip
    applied: list[dict[str, Any]] = []
    for name, model_strength, clip_strength in entries:
        if model_strength == 0 and clip_strength == 0:
            continue
        values = _node_output_tuple(load_lora(patched_model, patched_clip, name, model_strength, clip_strength))
        if len(values) < 2:
            raise RuntimeError("[EasyUseAnima] LoraLoader returned no MODEL/CLIP pair.")
        patched_model, patched_clip = values[0], values[1]
        applied.append({
            "name": name,
            "strength_model": model_strength,
            "strength_clip": clip_strength,
        })
    return patched_model, patched_clip, applied


def _aio_lora_metadata_name(name: str) -> str:
    value = str(name or "").strip().replace("\\", "/").strip("/")
    if not value:
        return ""
    root, ext = os.path.splitext(value)
    try:
        import folder_paths  # type: ignore

        supported = set(getattr(folder_paths, "supported_pt_extensions", ()))
    except Exception:
        supported = {".safetensors", ".pt", ".ckpt", ".bin", ".pth"}
    if ext.lower() in supported:
        value = root
    return value


def _aio_prompt_with_lora_metadata(prompt: str, applied_loras) -> str:
    tags: list[str] = []
    if not isinstance(applied_loras, list):
        applied_loras = []
    for item in applied_loras:
        if not isinstance(item, dict):
            continue
        name = _aio_lora_metadata_name(str(item.get("name") or ""))
        if not name:
            continue
        strength = _format_strength(_as_float(item.get("strength_model"), 1.0))
        tags.append(f"<lora:{name}:{strength}>")
    if not tags:
        return str(prompt or "")
    base = str(prompt or "").strip()
    suffix = " ".join(tags)
    return f"{base} {suffix}".strip() if base else suffix


def _cleanup_aio_ephemeral_model(model, base_model=None) -> None:
    if model is None or model is base_model:
        return
    detach = getattr(model, "detach", None)
    if callable(detach):
        try:
            detach(unpatch_all=False)
            return
        except Exception as exc:
            logger.debug("[EasyUseAnima] failed to detach ephemeral AiO model clone: %s", exc)
    try:
        import comfy.model_management as model_management  # type: ignore

        unload = getattr(model_management, "unload_model_and_clones", None)
        if callable(unload):
            unload(model, unload_additional_models=True)
            return
    except Exception as exc:
        logger.debug("[EasyUseAnima] failed to unload ephemeral AiO model clone: %s", exc)


def _apply_aio_spectrum_correction_patch_for_comfy_sampler(
    model,
    clip,
    positive,
    sampler_settings: dict[str, Any],
):
    corrections = sampler_settings.get("dit_corrections", {})
    if not isinstance(corrections, dict) or not _as_bool(corrections.get("enabled"), False):
        return model
    patch_cls = _require_custom_node_class(
        "DiTCFGFSGPatch",
        "ComfyUI-Spectrum-KSampler",
        "Repository: https://github.com/blepping/ComfyUI-Spectrum-KSampler",
    )
    use_smc = _as_bool(corrections.get("smc_cfg"), False)
    use_cfgpp = _as_bool(corrections.get("cfgpp"), False)
    use_fsg = _as_bool(corrections.get("fsg"), False)
    values = _node_output_tuple(
        patch_cls().patch(
            model,
            True,
            str(corrections.get("dcw_mode") or "off"),
            _as_float(corrections.get("dcw_lambda"), 0.01),
            str(corrections.get("dcw_band_mask") or "LL"),
            str(corrections.get("dcw_calibrator") or "(auto-download default)"),
            use_smc,
            _as_float(corrections.get("adaptive_smc_alpha"), 0.0) if use_smc else 0.0,
            _as_float(corrections.get("smc_cfg_lambda"), 6.0) if use_smc else 0.0,
            use_cfgpp,
            _as_float(corrections.get("cfgpp_lambda"), 0.0) if use_cfgpp else 0.0,
            use_fsg,
            _as_float(corrections.get("fsg_band_lo"), 0.59),
            _as_float(corrections.get("fsg_band_hi"), 0.75),
            _as_int(corrections.get("fsg_k"), 3),
            _as_float(corrections.get("fsg_d_sigma"), 0.1),
            _as_float(corrections.get("fsg_gamma"), 0.0),
            _as_bool(corrections.get("replace_existing_cfg"), False),
            steps=_as_int(sampler_settings.get("steps"), 28),
            cfg=_as_float(sampler_settings.get("cfg"), 5.0),
            sampler_name=str(sampler_settings.get("sampler_name") or "euler_ancestral"),
            scheduler=str(sampler_settings.get("scheduler") or "normal"),
            denoise=_as_float(sampler_settings.get("denoise"), 1.0),
            clip=clip,
            positive=positive,
        )
    )
    if not values:
        raise RuntimeError("[EasyUseAnima] DiTCFGFSGPatch returned no MODEL.")
    return values[0]


def _apply_aio_spectrum_forecast_patch_for_comfy_sampler(
    model,
    sampler_settings: dict[str, Any],
):
    spectrum = sampler_settings.get("spectrum", {})
    if not isinstance(spectrum, dict) or not _as_bool(spectrum.get("enabled"), False):
        return model
    node_id, patch_cls = _require_any_custom_node_class(
        ("DiTSpectrumPatchAdvanced", "DiTSpectrumPatch"),
        "ComfyUI-Spectrum-KSampler",
        "Repository: https://github.com/blepping/ComfyUI-Spectrum-KSampler",
    )
    patcher = patch_cls()
    patch = getattr(patcher, "patch", None)
    if patch is None:
        raise RuntimeError(f"[EasyUseAnima] {node_id} does not expose patch().")
    patch_kwargs = {
        "model": model,
        "steps": _as_int(sampler_settings.get("steps"), 28),
        "window_size": _as_float(spectrum.get("window_size"), 2.0),
        "flex_window": _as_float(spectrum.get("flex_window"), 0.25),
        "warmup_steps": _as_int(spectrum.get("warmup_steps"), 6),
        "tail_actual_steps": _as_int(spectrum.get("tail_actual_steps"), 3),
        "blend_w": _as_float(spectrum.get("blend_w"), 0.3),
        "cheby_degree": _as_int(spectrum.get("cheby_degree"), 3),
        "ridge_lambda": _as_float(spectrum.get("ridge_lambda"), 0.1),
        "history_size": _as_int(spectrum.get("history_size"), 100),
        "enabled": True,
        "one_sampler_only": _as_bool(spectrum.get("one_sampler_only"), False),
        "verbose": _as_bool(spectrum.get("verbose"), False),
        "compat_policy": str(spectrum.get("compat_policy") or "conservative"),
    }
    values = _node_output_tuple(
        _call_with_supported_kwargs(
            patch,
            (),
            patch_kwargs,
            f"{node_id}.patch()",
        )
    )
    if not values:
        raise RuntimeError(f"[EasyUseAnima] {node_id} returned no MODEL.")
    return values[0]


def _apply_aio_spectrum_model_patches_for_comfy_sampler(
    model,
    clip,
    positive,
    sampler_settings: dict[str, Any],
):
    patched = _apply_aio_spectrum_correction_patch_for_comfy_sampler(
        model,
        clip,
        positive,
        sampler_settings,
    )
    return _apply_aio_spectrum_forecast_patch_for_comfy_sampler(
        patched,
        sampler_settings,
    )


def _sample_latent_with_spectrum_mod_guidance_advanced(
    model,
    clip,
    sampler_settings: dict[str, Any],
    mod_guidance_settings: dict[str, Any],
    use_mod_guidance: bool,
    positive,
    negative,
    latent_image,
    quality_tags: str,
    quality_neg: str,
):
    sampler_cls = _require_custom_node_class(
        "SpectrumKSamplerAdvanced",
        "ComfyUI-Spectrum-KSampler",
        "Repository: https://github.com/blepping/ComfyUI-Spectrum-KSampler",
    )
    spectrum = sampler_settings.get("spectrum", {})
    if not isinstance(spectrum, dict):
        spectrum = {}
    corrections = sampler_settings.get("dit_corrections", {})
    if not isinstance(corrections, dict):
        corrections = {}
    use_corrections = _as_bool(corrections.get("enabled"), False)
    use_smc = use_corrections and _as_bool(corrections.get("smc_cfg"), False)
    use_cfgpp = use_corrections and _as_bool(corrections.get("cfgpp"), False)
    use_fsg = use_corrections and _as_bool(corrections.get("fsg"), False)
    advanced_mod = mod_guidance_settings.get("advanced", {})
    if not isinstance(advanced_mod, dict):
        advanced_mod = {}
    profile = _normalize_anima_mod_guidance_profile(
        mod_guidance_settings.get("profile", ANIMA_MOD_GUIDANCE_DEFAULT_PROFILE)
    )
    mod_w = _as_float(advanced_mod.get("mod_w"), 3.0)
    if not use_mod_guidance or profile == ANIMA_MOD_GUIDANCE_PROFILE_OFF:
        mod_w = 0.0
    sampler = sampler_cls()
    sampler_kwargs = {
        "model": model,
        "clip": clip,
        "seed": _resolve_aio_runtime_seed(sampler_settings.get("seed")),
        "steps": _as_int(sampler_settings.get("steps"), 28),
        "cfg": _as_float(sampler_settings.get("cfg"), 5.0),
        "sampler_name": str(sampler_settings.get("sampler_name") or "euler_ancestral"),
        "scheduler": str(sampler_settings.get("scheduler") or "normal"),
        "positive": positive,
        "negative": negative,
        "latent_image": latent_image,
        "adapter": str(advanced_mod.get("adapter") or "(auto-download default)"),
        "quality_tags": str(quality_tags or advanced_mod.get("quality_tags") or ""),
        "mod_w": mod_w,
        "quality_neg": str(quality_neg or ""),
        "mod_start_layer": _as_int(advanced_mod.get("mod_start_layer"), 8),
        "mod_end_layer": _as_int(advanced_mod.get("mod_end_layer"), 27),
        "mod_taper": _as_int(advanced_mod.get("mod_taper"), 0),
        "mod_taper_scale": _as_float(advanced_mod.get("mod_taper_scale"), 0.25),
        "mod_final_w": _as_float(advanced_mod.get("mod_final_w"), 0.0),
        "denoise": _as_float(sampler_settings.get("denoise"), 1.0),
        "window_size": _as_float(spectrum.get("window_size"), 2.0),
        "flex_window": _as_float(spectrum.get("flex_window"), 0.25),
        "warmup_steps": _as_int(spectrum.get("warmup_steps"), 6),
        "blend_w": _as_float(spectrum.get("blend_w"), 0.3),
        "cheby_degree": _as_int(spectrum.get("cheby_degree"), 3),
        "ridge_lambda": _as_float(spectrum.get("ridge_lambda"), 0.1),
        "dcw_mode": str(corrections.get("dcw_mode") or "off") if use_corrections else "off",
        "dcw_lambda": _as_float(corrections.get("dcw_lambda"), 0.01) if use_corrections else 0.0,
        "dcw_band_mask": str(corrections.get("dcw_band_mask") or "LL") if use_corrections else "LL",
        "dcw_calibrator": str(corrections.get("dcw_calibrator") or "(auto-download default)"),
        "cfgpp_lambda": _as_float(corrections.get("cfgpp_lambda"), 0.0) if use_cfgpp else 0.0,
        "fsg": use_fsg,
        "fsg_band_lo": _as_float(corrections.get("fsg_band_lo"), 0.59) if use_fsg else 0.59,
        "fsg_band_hi": _as_float(corrections.get("fsg_band_hi"), 0.75) if use_fsg else 0.75,
        "fsg_k": _as_int(corrections.get("fsg_k"), 3) if use_fsg else 3,
        "fsg_d_sigma": _as_float(corrections.get("fsg_d_sigma"), 0.1) if use_fsg else 0.1,
        "fsg_gamma": _as_float(corrections.get("fsg_gamma"), 0.0) if use_fsg else 0.0,
        "adaptive_smc_alpha": _as_float(corrections.get("adaptive_smc_alpha"), 0.0) if use_smc else 0.0,
        "smc_cfg_lambda": _as_float(corrections.get("smc_cfg_lambda"), 5.0) if use_smc else 0.0,
    }
    extra = sampler_settings.get("spectrum_extra")
    if isinstance(extra, dict):
        for key, value in extra.items():
            text_key = str(key or "")
            if text_key and text_key not in sampler_kwargs:
                sampler_kwargs[text_key] = value
    values = _node_output_tuple(
        _call_with_supported_kwargs(
            sampler.sample,
            (),
            sampler_kwargs,
            "SpectrumKSamplerAdvanced.sample()",
        )
    )
    if not values:
        raise RuntimeError("[EasyUseAnima] SpectrumKSamplerAdvanced returned no LATENT.")
    return values[0]


def _sample_latent_with_spectrum_spd(
    model,
    sampler_settings: dict[str, Any],
    positive,
    negative,
    latent_image,
):
    spd_cls = _require_custom_node_class(
        "SpectrumSPDKSampler",
        "ComfyUI-Spectrum-KSampler",
        "Repository: https://github.com/blepping/ComfyUI-Spectrum-KSampler",
    )
    spd = sampler_settings.get("spd", {})
    if not isinstance(spd, dict):
        spd = {}
    # Spectrum SPEED/SPD is Euler-only. Normalize before calling the node so
    # saved workflows do not emit a misleading "ignoring requested sampler" warning.
    sampler_name = "euler"
    sampler = spd_cls()
    sampler_kwargs = {
        "model": model,
        "seed": _resolve_aio_runtime_seed(sampler_settings.get("seed")),
        "steps": _as_int(sampler_settings.get("steps"), 28),
        "cfg": _as_float(sampler_settings.get("cfg"), 5.0),
        "sampler_name": sampler_name,
        "scheduler": str(sampler_settings.get("scheduler") or "simple"),
        "positive": positive,
        "negative": negative,
        "latent_image": latent_image,
        "split_mode": str(spd.get("split_mode") or "single"),
        "spd_scale": _as_float(spd.get("scale"), 0.5),
        "spd_sigma": _as_float(spd.get("sigma"), 0.7),
        "denoise": _as_float(sampler_settings.get("denoise"), 1.0),
        "adaptive_smc_alpha": _as_float(spd.get("adaptive_smc_alpha"), 0.0),
    }
    extra = sampler_settings.get("spd_extra")
    if isinstance(extra, dict):
        for key, value in extra.items():
            text_key = str(key or "")
            if text_key and text_key not in sampler_kwargs:
                sampler_kwargs[text_key] = value
    values = _node_output_tuple(
        _call_with_supported_kwargs(
            sampler.sample,
            (),
            sampler_kwargs,
            "SpectrumSPDKSampler.sample()",
        )
    )
    if not values:
        raise RuntimeError("[EasyUseAnima] SpectrumSPDKSampler returned no LATENT.")
    return values[0]


def _apply_aio_anima_dave_patch(model, dave_settings: dict[str, Any]):
    dave_cls = _require_custom_node_class(
        "AnimaDAVE",
        "ComfyUI-Anima-DAVE",
        "Repository: https://github.com/sorryhyun/ComfyUI-Anima-DAVE",
    )
    if not isinstance(dave_settings, dict):
        dave_settings = {}
    patcher = dave_cls()
    patch = getattr(patcher, "patch", None)
    if patch is None:
        raise RuntimeError("[EasyUseAnima] AnimaDAVE does not expose patch().")
    result = patch(
        model,
        str(dave_settings.get("mask") or "dave_alpha.npz"),
        _as_float(dave_settings.get("strength"), 0.30),
        _as_float(dave_settings.get("tau"), 0.10),
    )
    values = _node_output_tuple(result)
    if not values:
        raise RuntimeError("[EasyUseAnima] AnimaDAVE returned no MODEL.")
    return values[0]


def _apply_aio_safe_pag_patch(model, safe_pag_settings: dict[str, Any]):
    safe_pag_cls = _require_custom_node_class(
        "AnimaSafePAG",
        "Anima Safe PAG",
        "Repository: https://github.com/iljung1106/comfyui-anima-safe-pag",
    )
    if not isinstance(safe_pag_settings, dict):
        safe_pag_settings = {}
    result = safe_pag_cls().patch(
        model,
        _as_float(safe_pag_settings.get("scale"), 4.0),
        str(safe_pag_settings.get("block_indices") or "18"),
        _as_float(safe_pag_settings.get("perturbation_strength"), 0.75),
        str(safe_pag_settings.get("head_indices") or ""),
        _as_float(safe_pag_settings.get("start_percent"), 0.0),
        _as_float(safe_pag_settings.get("end_percent"), 0.7),
        _as_float(safe_pag_settings.get("rescale"), 0.2),
        str(safe_pag_settings.get("rescale_mode") or "full"),
    )
    values = _node_output_tuple(result)
    if not values:
        raise RuntimeError("[EasyUseAnima] AnimaSafePAG returned no MODEL.")
    return values[0]


def _sample_latent_with_aio_backend(
    model,
    clip,
    positive,
    negative,
    latent_image,
    sampler_settings: dict[str, Any],
    mod_guidance_settings: dict[str, Any],
    use_mod_guidance: bool,
    quality_tags: str,
    quality_neg: str,
):
    backend = str(sampler_settings.get("backend") or "comfy_ksampler")
    if backend == "spectrum_mod_guidance_advanced":
        return _sample_latent_with_spectrum_mod_guidance_advanced(
            model,
            clip,
            sampler_settings,
            mod_guidance_settings,
            use_mod_guidance,
            positive,
            negative,
            latent_image,
            quality_tags,
            quality_neg,
        )
    if backend == "spectrum_spd_speed":
        return _sample_latent_with_spectrum_spd(
            model,
            sampler_settings,
            positive,
            negative,
            latent_image,
        )
    return _sample_latent_with_comfy(
        model,
        sampler_settings["seed"],
        sampler_settings["steps"],
        sampler_settings["cfg"],
        sampler_settings["sampler_name"],
        sampler_settings["scheduler"],
        positive,
        negative,
        latent_image,
        sampler_settings["denoise"],
    )


def _decode_latent_with_comfy(vae, samples):
    decoder_cls = _find_comfy_node_class("VAEDecode")
    if decoder_cls is None:
        raise RuntimeError("[EasyUseAnima] Could not find ComfyUI VAEDecode.")
    decoder = decoder_cls()
    decode = getattr(decoder, "decode", None)
    if decode is None:
        raise RuntimeError("[EasyUseAnima] VAEDecode does not expose decode().")
    result = decode(vae, samples)
    values = _node_output_tuple(result)
    if not values:
        raise RuntimeError("[EasyUseAnima] VAEDecode returned no IMAGE.")
    return values[0]


def _encode_image_with_comfy_vae(vae, image):
    encoder_cls = _find_comfy_node_class("VAEEncode")
    if encoder_cls is None:
        raise RuntimeError("[EasyUseAnima] Could not find ComfyUI VAEEncode.")
    encoder = encoder_cls()
    encode = getattr(encoder, "encode", None)
    if encode is None:
        raise RuntimeError("[EasyUseAnima] VAEEncode does not expose encode().")
    values = _node_output_tuple(encode(vae, image))
    if not values:
        raise RuntimeError("[EasyUseAnima] VAEEncode returned no LATENT.")
    return values[0]


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


def _load_upscale_model_with_comfy(model_name: str):
    model_name = str(model_name or "").strip()
    if not model_name:
        raise RuntimeError(
            "[EasyUseAnima] USDU final upscale requires an upscale_model_name. "
            "Choose a model from ComfyUI models/upscale_models."
        )
    loader_cls = _find_comfy_node_class("UpscaleModelLoader")
    if loader_cls is None:
        try:
            from comfy_extras.nodes_upscale_model import UpscaleModelLoader  # type: ignore

            loader_cls = UpscaleModelLoader
        except Exception:
            loader_cls = None
    if loader_cls is None:
        raise RuntimeError("[EasyUseAnima] Could not find ComfyUI UpscaleModelLoader.")
    loader = loader_cls()
    method = getattr(loader, "load_model", None) or getattr(loader, "execute", None)
    if method is None:
        raise RuntimeError("[EasyUseAnima] UpscaleModelLoader does not expose load_model().")
    values = _node_output_tuple(method(model_name))
    if not values:
        raise RuntimeError("[EasyUseAnima] UpscaleModelLoader returned no UPSCALE_MODEL.")
    return values[0]


def _aio_stage_sampler_settings(
    base_sampler: dict[str, Any],
    stage_settings: dict[str, Any],
    *,
    scheduler_default: str,
    inherit_backend: bool = False,
) -> dict[str, Any]:
    inherit_sampler = _as_bool(stage_settings.get("inherit_sampler_settings"), False)
    inherited_spd_fallback = False
    if inherit_backend and inherit_sampler:
        inherited_backend = str(base_sampler.get("backend") or "comfy_ksampler")
        if inherited_backend == "spectrum_spd_speed":
            backend = "comfy_ksampler"
            inherited_spd_fallback = True
        else:
            backend = inherited_backend
    elif inherit_backend:
        backend = "comfy_ksampler"
    else:
        backend = "comfy_ksampler"
    return {
        "backend": backend,
        "seed": _resolve_aio_runtime_seed(base_sampler.get("seed")),
        "seed_after_generate": SEED_CONTROL_FIXED,
        "steps": _as_int(stage_settings.get("steps"), _as_int(base_sampler.get("steps"), 28)),
        "cfg": (
            _as_float(base_sampler.get("cfg"), 5.0)
            if inherit_sampler
            else _as_float(stage_settings.get("cfg"), _as_float(base_sampler.get("cfg"), 5.0))
        ),
        "sampler_name": (
            ("euler" if inherited_spd_fallback else str(base_sampler.get("sampler_name") or "euler"))
            if inherit_sampler
            else str(stage_settings.get("sampler_name") or base_sampler.get("sampler_name") or "euler")
        ),
        "scheduler": (
            str(base_sampler.get("scheduler") or scheduler_default)
            if inherit_sampler
            else str(stage_settings.get("scheduler") or scheduler_default)
        ),
        "denoise": _as_float(stage_settings.get("denoise"), 1.0),
        "spectrum": _json_clone(stage_settings.get("spectrum") or {}),
        "dit_corrections": _json_clone(stage_settings.get("dit_corrections") or {}),
        "spd": _json_clone(stage_settings.get("spd") or {}),
        "spectrum_extra": {},
        "spd_extra": {},
    }


def _aio_highres_effective_backend(
    sampler_settings: dict[str, Any],
    highres_settings: dict[str, Any],
) -> str:
    if not _as_bool(highres_settings.get("enabled"), False):
        return ""
    if _as_bool(highres_settings.get("inherit_sampler_settings"), False):
        backend = str(sampler_settings.get("backend") or "comfy_ksampler")
        return "comfy_ksampler" if backend == "spectrum_spd_speed" else backend
    return "comfy_ksampler"


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


def _aio_prompt_data_fields_for_usdu(prompt_data: str | dict | None) -> list[dict]:
    data = _normalize_prompt_data(prompt_data)
    fields = data.get("fields")
    if not isinstance(fields, list):
        fields = data.get("saved_fields")
    return _normalize_advanced_fields(fields)


def _aio_usdu_prompt_without_general(
    prompt_data: str | dict | None,
    pane: str,
    include_quality: bool,
) -> tuple[str, bool]:
    fields = _aio_prompt_data_fields_for_usdu(prompt_data)
    if not fields:
        return "", False
    allowed_types = {"artist", "trigger"}
    if include_quality:
        allowed_types.add("quality")
    selected = [
        field
        for field in _advanced_enabled_pane_fields(fields, pane)
        if field.get("type") in allowed_types
    ]
    if not selected:
        return "", True
    artist_prompt = _advanced_artist_field_prompt(selected, pane)
    force_pin_triggers = _as_bool(_normalize_prompt_data(prompt_data).get("pin_trigger_tags_to_front"), False)
    return (
        _correct_advanced_field_sequence(
            selected,
            include_quality=include_quality,
            artist_overrides=artist_prompt,
            force_pin_triggers=force_pin_triggers,
        ),
        True,
    )


def _aio_usdu_conditioning(
    clip,
    positive,
    negative,
    usdu_settings: dict[str, Any],
    quality_tags: str,
    quality_neg: str,
    prompt_data: str | dict | None = None,
    exclude_positive_quality: bool = False,
    exclude_negative_quality: bool = False,
):
    prompt_mode = str(usdu_settings.get("prompt_mode") or AIO_USDU_PROMPT_FULL)
    if prompt_mode == "quality_tags_only":
        prompt_mode = AIO_USDU_PROMPT_NO_GENERAL
    if prompt_mode != AIO_USDU_PROMPT_NO_GENERAL:
        return positive, negative
    prompt, has_fields = _aio_usdu_prompt_without_general(
        prompt_data,
        "positive",
        include_quality=not _as_bool(exclude_positive_quality, False),
    )
    negative_prompt, has_negative_fields = _aio_usdu_prompt_without_general(
        prompt_data,
        "negative",
        include_quality=not _as_bool(exclude_negative_quality, False),
    )
    if not has_fields and not prompt:
        prompt = "" if _as_bool(exclude_positive_quality, False) else str(quality_tags or "highres, best quality")
    if not has_negative_fields and not negative_prompt:
        negative_prompt = "" if _as_bool(exclude_negative_quality, False) else str(quality_neg or "")
    return _encode_with_comfy_clip(clip, prompt), _encode_with_comfy_clip(clip, negative_prompt)


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


def _load_aio_sam3_context(detailer_settings: dict[str, Any]) -> dict[str, Any]:
    sam3 = detailer_settings.get("sam3", {})
    if not isinstance(sam3, dict):
        sam3 = {}
    checkpoint = str(sam3.get("checkpoint") or "sam3.1_multiplex_fp16.safetensors")
    model, clip, vae = _load_checkpoint_with_comfy(checkpoint)
    return _sam3_context(model, clip, vae, checkpoint)


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


def _save_image_with_comfy(images, filename_prefix: str, workflow_prompt=None, extra_pnginfo=None):
    save_cls = _find_comfy_node_class("SaveImage")
    if save_cls is None:
        raise RuntimeError("[EasyUseAnima] Could not find ComfyUI SaveImage.")
    saver = save_cls()
    save_images = getattr(saver, "save_images", None)
    if save_images is None:
        raise RuntimeError("[EasyUseAnima] SaveImage does not expose save_images().")
    return save_images(
        images,
        str(filename_prefix or "EasyUseAnima/AiO"),
        prompt=workflow_prompt,
        extra_pnginfo=extra_pnginfo,
    )


AIO_PREVIEW_STAGE_LABELS = {
    "first_pass": "First pass",
    "highres": "Highres",
    "detailer_face": "Detailer: face",
    "detailer_eye": "Detailer: eye",
    "upscale": "Upscale",
    "postprocess": "Postprocess",
    "final": "Final",
}
AIO_PREVIEW_EVENT = "easyuse-anima-aio-preview"
AIO_PREVIEW_CACHE_FORMAT = "webp"
AIO_PREVIEW_CACHE_QUALITY = 90
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


def _aio_preview_base_directory(image_type: str) -> str:
    try:
        import folder_paths  # type: ignore

        if image_type == "temp":
            return folder_paths.get_temp_directory()
        if image_type == "input":
            return folder_paths.get_input_directory()
        return folder_paths.get_output_directory()
    except Exception:
        return ""


def _aio_preview_file_size_bytes(image_info: dict[str, Any]) -> int:
    filename = str(image_info.get("filename") or "")
    if not filename:
        return 0
    base_dir = _aio_preview_base_directory(str(image_info.get("type") or "output"))
    if not base_dir:
        return 0
    subfolder = str(image_info.get("subfolder") or "")
    path = os.path.join(base_dir, subfolder, filename)
    try:
        return os.path.getsize(path) if os.path.isfile(path) else 0
    except OSError:
        return 0


def _tag_aio_preview_images(
    images,
    stage: str,
    *,
    width: int = 0,
    height: int = 0,
) -> list[dict[str, Any]]:
    label = AIO_PREVIEW_STAGE_LABELS.get(stage, stage)
    tagged: list[dict[str, Any]] = []
    for image in images or ():
        if not isinstance(image, dict):
            continue
        item = dict(image)
        item["stage"] = stage
        item["label"] = label
        if width > 0:
            item["width"] = int(width)
        if height > 0:
            item["height"] = int(height)
        file_size = _aio_preview_file_size_bytes(item)
        if file_size > 0:
            item["bytes"] = int(file_size)
        tagged.append(item)
    return tagged


def _send_aio_preview_event(
    node_id,
    run_id: str,
    stage: str,
    images: list[dict[str, Any]],
) -> None:
    node_id = _single_value(node_id)
    if node_id is None or not images:
        return
    try:
        from server import PromptServer  # type: ignore

        prompt_server = getattr(PromptServer, "instance", None)
        send_sync = getattr(prompt_server, "send_sync", None)
        if prompt_server is None or send_sync is None:
            return
        payload = {
            "node": str(node_id),
            "run_id": str(run_id),
            "stage": str(stage),
            "images": _prompt_data_json_safe(images),
        }
        client_id = getattr(prompt_server, "client_id", None)
        send_sync(AIO_PREVIEW_EVENT, payload, client_id)
    except Exception as exc:
        logger.debug("[EasyUseAnima] failed to send AiO preview event: %s", exc)


def _save_aio_temp_preview_image(
    image,
    stage: str,
    *,
    workflow_prompt=None,
    extra_pnginfo=None,
) -> list[dict[str, Any]]:
    width, height = _image_tensor_size(image, 0, 0)
    try:
        import folder_paths  # type: ignore
        import numpy as np  # type: ignore
        from PIL import Image  # type: ignore

        temp_dir = folder_paths.get_temp_directory()
        prefix = f"EasyUseAnima_AiO_{stage}_temp_{''.join(random.choice('abcdefghijklmnopqrstupvxyz') for _ in range(5))}"
        full_output_folder, filename, counter, subfolder, _ = folder_paths.get_save_image_path(
            prefix,
            temp_dir,
            width,
            height,
        )
        results: list[dict[str, Any]] = []
        for batch_number, batch_image in enumerate(image):
            pixels = 255.0 * batch_image.detach().cpu().numpy()
            img = Image.fromarray(np.clip(pixels, 0, 255).astype(np.uint8))
            filename_with_batch_num = filename.replace("%batch_num%", str(batch_number))
            file = f"{filename_with_batch_num}_{counter:05}_.{AIO_PREVIEW_CACHE_FORMAT}"
            path = os.path.join(full_output_folder, file)
            img.save(path, format="WEBP", quality=AIO_PREVIEW_CACHE_QUALITY, method=4)
            results.append({
                "filename": file,
                "subfolder": subfolder,
                "type": "temp",
            })
            counter += 1
        if results:
            return _tag_aio_preview_images(results, stage, width=width, height=height)
    except Exception as exc:
        logger.warning(
            "[EasyUseAnima] Failed to save AiO WebP preview stage %s; falling back to ComfyUI PreviewImage PNG: %s",
            stage,
            exc,
        )

    preview_cls = _find_comfy_node_class("PreviewImage")
    if preview_cls is None:
        logger.warning("[EasyUseAnima] Could not find ComfyUI PreviewImage for AiO preview stage %s.", stage)
        return []
    saver = preview_cls()
    save_images = getattr(saver, "save_images", None)
    if save_images is None:
        logger.warning("[EasyUseAnima] PreviewImage does not expose save_images() for AiO preview stage %s.", stage)
        return []
    try:
        result = save_images(
            image,
            filename_prefix=f"EasyUseAnima_AiO_{stage}",
            prompt=workflow_prompt,
            extra_pnginfo=extra_pnginfo,
        )
    except TypeError:
        try:
            result = save_images(image)
        except Exception as exc:
            logger.warning("[EasyUseAnima] Failed to save AiO preview stage %s: %s", stage, exc)
            return []
    except Exception as exc:
        logger.warning("[EasyUseAnima] Failed to save AiO preview stage %s: %s", stage, exc)
        return []
    if not isinstance(result, dict):
        return []
    ui = result.get("ui", {})
    if not isinstance(ui, dict):
        return []
    return _tag_aio_preview_images(ui.get("images", []), stage, width=width, height=height)


def _aio_save_filename_prefix(save_settings: dict[str, Any]) -> str:
    image_saver = save_settings.get("image_saver", {})
    if not isinstance(image_saver, dict):
        image_saver = {}
    defaults = AIO_GENERATION_DEFAULT_SETTINGS["save"]["image_saver"]
    path = str(image_saver.get("path") or defaults["path"]).strip().strip("/\\")
    filename = str(image_saver.get("filename") or defaults["filename"]).strip().strip("/\\")
    if path and filename:
        return f"{path}/{filename}"
    return filename or path or f"{defaults['path']}/{defaults['filename']}"


def _save_image_with_image_saver(
    images,
    save_settings: dict[str, Any],
    positive_prompt: str,
    negative_prompt: str,
    width: int,
    height: int,
    sampler_settings: dict[str, Any],
    applied_loras=None,
    resource_info: dict[str, Any] | None = None,
    workflow_prompt=None,
    extra_pnginfo=None,
):
    image_saver_cls = _require_custom_node_class(
        "Image Saver",
        "ComfyUI-Image-Saver",
        "Repository: https://github.com/alexopus/ComfyUI-Image-Saver",
    )
    saver = image_saver_cls()
    save_files = getattr(saver, "save_files", None)
    if save_files is None:
        raise RuntimeError("[EasyUseAnima] Image Saver node does not expose save_files().")

    image_saver = save_settings.get("image_saver", {})
    if not isinstance(image_saver, dict):
        image_saver = {}
    defaults = AIO_GENERATION_DEFAULT_SETTINGS["save"]["image_saver"]
    modelname = str((resource_info or {}).get("unet_name") or "")
    save_prompt_metadata = _as_bool(
        image_saver.get("save_prompt_metadata"),
        defaults["save_prompt_metadata"],
    )
    metadata_positive = (
        _aio_prompt_with_lora_metadata(str(positive_prompt or "unknown"), applied_loras)
        if save_prompt_metadata
        else ""
    )
    metadata_negative = str(negative_prompt or "unknown") if save_prompt_metadata else ""
    return save_files(
        images=images,
        filename=str(image_saver.get("filename") or defaults["filename"]),
        path=str(image_saver.get("path") or defaults["path"]),
        extension=str(image_saver.get("extension") or defaults["extension"]),
        steps=_as_int(sampler_settings.get("steps"), 28),
        cfg=_as_float(sampler_settings.get("cfg"), 5.0),
        modelname=modelname,
        sampler_name=str(sampler_settings.get("sampler_name") or ""),
        scheduler_name=str(sampler_settings.get("scheduler") or "normal"),
        positive=metadata_positive,
        negative=metadata_negative,
        seed_value=_resolve_aio_runtime_seed(sampler_settings.get("seed")),
        width=_as_int(width, 512),
        height=_as_int(height, 512),
        lossless_webp=_as_bool(image_saver.get("lossless_webp"), defaults["lossless_webp"]),
        quality_jpeg_or_webp=max(
            1,
            min(100, _as_int(image_saver.get("quality_jpeg_or_webp"), defaults["quality_jpeg_or_webp"])),
        ),
        optimize_png=_as_bool(image_saver.get("optimize_png"), defaults["optimize_png"]),
        counter=max(0, _as_int(image_saver.get("counter"), defaults["counter"])),
        denoise=_as_float(sampler_settings.get("denoise"), 1.0),
        clip_skip=_as_int(image_saver.get("clip_skip"), defaults["clip_skip"]),
        time_format=str(image_saver.get("time_format") or defaults["time_format"]),
        save_workflow_as_json=_as_bool(
            image_saver.get("save_workflow_as_json"),
            defaults["save_workflow_as_json"],
        ),
        embed_workflow=_as_bool(image_saver.get("embed_workflow"), defaults["embed_workflow"]),
        additional_hashes=_aio_image_saver_additional_hashes(image_saver),
        download_civitai_data=_as_bool(
            image_saver.get("download_civitai_data"),
            defaults["download_civitai_data"],
        ),
        easy_remix=_as_bool(image_saver.get("easy_remix"), defaults["easy_remix"]),
        show_preview=False,
        custom=str(image_saver.get("custom") or ""),
        prompt=workflow_prompt,
        extra_pnginfo=extra_pnginfo,
    )


def _format_sam3_detection_prompt(detect_prompt: str, detect_count: int) -> str:
    prompt = str(detect_prompt or "").strip()
    if not prompt:
        raise ValueError("[EasyUseAnima] SAM3 detect prompt is empty.")

    max_det = max(1, int(detect_count))
    parts = [part.strip() for part in re.split(r"[,\n]+", prompt) if part.strip()]
    formatted = []
    for part in parts:
        if re.search(r":\s*[\d.]+\s*$", part):
            formatted.append(part)
        else:
            formatted.append(f"{part}:{max_det}")
    return ", ".join(formatted)


def _sam3_context(model, clip, vae, ckpt_name: str = "") -> dict[str, Any]:
    return {
        "model": model,
        "clip": clip,
        "vae": vae,
        "ckpt_name": ckpt_name,
    }


def _context_value(ctx, key: str):
    if isinstance(ctx, dict):
        return ctx.get(key)
    return None


def _empty_mask_for_image(image):
    try:
        import torch  # type: ignore
    except Exception as exc:
        raise RuntimeError("[EasyUseAnima] torch is required to create an empty mask.") from exc

    batch = int(image.shape[0])
    height = int(image.shape[1])
    width = int(image.shape[2])
    device = getattr(image, "device", None)
    return torch.zeros((batch, height, width), dtype=torch.float32, device=device)


def _empty_segs_for_image(image):
    return ((int(image.shape[1]), int(image.shape[2])), [])


def _segs_has_items(segs) -> bool:
    try:
        return len(segs[1]) > 0
    except Exception:
        return False


def _call_impact_detailer(detailer, **kwargs):
    method = getattr(detailer, "doit", None)
    if method is None:
        raise RuntimeError("[EasyUseAnima] Impact DetailerForEach does not expose a doit method.")
    signature = inspect.signature(method)
    parameters = signature.parameters
    accepts_kwargs = any(param.kind == inspect.Parameter.VAR_KEYWORD for param in parameters.values())
    call_kwargs = kwargs if accepts_kwargs else {key: value for key, value in kwargs.items() if key in parameters}
    return method(**call_kwargs)


def _translate_prompt_fields(fields: list[dict]) -> list[dict]:
    translated: list[dict] = []
    for field in fields:
        item = dict(field)
        text = str(item.get("text") or "")
        if text and has_prompt_translation_markers(text):
            item["text"] = _translate_prompt_text(text)
        translated.append(item)
    return translated


def _advanced_default_fields() -> list[dict]:
    return [
        {
            "id": "positive_quality",
            "pane": "positive",
            "type": "quality",
            "label": ADVANCED_FIELD_LABELS["quality"],
            "text": DEFAULT_QUALITY_TAGS,
            "height": 72,
            "enabled": True,
        },
        {
            "id": "positive_artist",
            "pane": "positive",
            "type": "artist",
            "label": ADVANCED_FIELD_LABELS["artist"],
            "text": "",
            "height": 72,
            "enabled": True,
        },
        {
            "id": "positive_trigger",
            "pane": "positive",
            "type": "trigger",
            "label": ADVANCED_FIELD_LABELS["trigger"],
            "text": "",
            "height": 72,
            "enabled": True,
            "pin": True,
        },
        {
            "id": "positive_general",
            "pane": "positive",
            "type": "general",
            "label": ADVANCED_FIELD_LABELS["general"],
            "text": "",
            "height": 150,
            "enabled": True,
        },
        {
            "id": "positive_trailing",
            "pane": "positive",
            "type": "general",
            "label": ADVANCED_FIELD_LABELS["general"],
            "text": DEFAULT_TRAILING_QUALITY_TAGS,
            "height": 72,
            "enabled": True,
        },
        {
            "id": "negative_general",
            "pane": "negative",
            "type": "general",
            "label": ADVANCED_FIELD_LABELS["general"],
            "text": "",
            "height": 120,
            "enabled": True,
        },
    ]


def _advanced_fields_json(fields: list[dict] | None = None) -> str:
    return json.dumps(
        fields if fields is not None else _advanced_default_fields(),
        ensure_ascii=False,
        separators=(",", ":"),
    )


def _as_advanced_height(value, default: int = 72) -> int:
    return max(36, _as_int(value, default))


def _normalize_advanced_fields(value: str | list | None) -> list[dict]:
    raw = value
    if isinstance(value, str):
        try:
            raw = json.loads(value or "[]")
        except json.JSONDecodeError:
            raw = []
    if not isinstance(raw, list):
        raw = []
    if not raw:
        raw = _advanced_default_fields()

    fields: list[dict] = []
    seen_naia_panes: set[str] = set()
    seen_trigger = False
    for index, item in enumerate(raw):
        if not isinstance(item, dict):
            continue
        pane = str(item.get("pane") or "positive").strip().lower()
        if pane not in ADVANCED_FIELD_PANES:
            pane = "positive"
        field_type = str(item.get("type") or "general").strip().lower()
        if field_type not in ADVANCED_FIELD_TYPES:
            field_type = "general"
        if pane == "negative" and field_type == "trigger":
            field_type = "general"
        if field_type == "naia":
            if pane in seen_naia_panes:
                continue
            seen_naia_panes.add(pane)
        if field_type == "trigger":
            if seen_trigger:
                continue
            seen_trigger = True
            pane = "positive"
        default_label = ADVANCED_FIELD_LABELS.get(field_type, ADVANCED_FIELD_LABELS["general"])
        label = str(item.get("label") or default_label).strip() or default_label
        field_id = str(item.get("id") or f"{pane}_{field_type}_{index + 1}").strip()
        if not field_id:
            field_id = f"{pane}_{field_type}_{index + 1}"
        fields.append({
            "id": field_id,
            "pane": pane,
            "type": field_type,
            "label": label,
            "text": str(item.get("text") or ""),
            "height": _as_advanced_height(item.get("height"), 72),
            "enabled": _as_bool(item.get("enabled"), True),
            "pin": _as_bool(item.get("pin"), field_type == "trigger"),
        })

    return fields or _advanced_default_fields()


def _clone_advanced_fields(fields: list[dict]) -> list[dict]:
    return [dict(field) for field in fields]


def _advanced_field_socket_name(field: dict) -> str:
    raw = _ADVANCED_FIELD_SOCKET_RE.sub("_", str(field.get("id") or "field")).strip("_")
    return f"{_ADVANCED_FIELD_SOCKET_PREFIX}{raw or 'field'}"


def _advanced_field_input_values(field_inputs: dict) -> dict[str, str]:
    values: dict[str, str] = {}
    for key, value in field_inputs.items():
        if not str(key).startswith(_ADVANCED_FIELD_SOCKET_PREFIX):
            continue
        single = _single_value(value)
        if single is None:
            continue
        values[str(key)] = str(single)
    return values


def _apply_advanced_field_inputs(fields: list[dict], field_inputs: dict) -> list[dict]:
    values = _advanced_field_input_values(field_inputs)
    if not values:
        return _clone_advanced_fields(fields)

    effective = _clone_advanced_fields(fields)
    for field in effective:
        name = _advanced_field_socket_name(field)
        if name in values:
            field["text"] = values[name]
    return effective


def _advanced_enabled_naia_panes(fields: list[dict]) -> set[str]:
    return {
        str(field.get("pane") or "positive")
        for field in fields
        if field.get("type") == "naia" and field.get("enabled") is not False
    }


def _advanced_has_enabled_naia(fields: list[dict]) -> bool:
    return bool(_advanced_enabled_naia_panes(fields))


def _advanced_uses_naia_resolution(bucket) -> bool:
    return _normalize_resolution_bucket(bucket) == NAIA_ADVANCED_RESOLUTION_BUCKET


def _set_naia_field_text(fields: list[dict], pane: str, prompt: str) -> list[dict]:
    normalized = _normalize_advanced_fields(fields)
    for field in normalized:
        if field["pane"] == pane and field["type"] == "naia":
            field["text"] = prompt
            field["enabled"] = True
            return normalized
    return normalized


def _advanced_pane_parts(fields: list[dict], pane: str) -> dict[str, list[str]]:
    parts = {"quality": [], "artist": [], "trigger_fixed": [], "trigger_auto": [], "body": []}
    for field in fields:
        if not _as_bool(field.get("enabled"), True):
            continue
        if field.get("pane") != pane:
            continue
        field_type = field.get("type")
        text = str(field.get("text") or "")
        if field_type == "quality":
            parts["quality"].append(text)
        elif field_type == "artist":
            parts["artist"].append(_artist_mix_inline_prompt(text))
        elif field_type == "trigger":
            if _as_bool(field.get("pin"), True):
                parts["trigger_fixed"].append(text)
            else:
                parts["trigger_auto"].append(text)
        else:
            parts["body"].append(text)
    return parts


def _advanced_enabled_pane_fields(fields: list[dict], pane: str) -> list[dict]:
    return [
        field
        for field in fields
        if _as_bool(field.get("enabled"), True) and field.get("pane") == pane
    ]


def _correct_advanced_field_sequence(
    fields: list[dict],
    include_quality: bool,
    artist_overrides: str,
    force_pin_triggers: bool = False,
) -> str:
    chunks: list[str] = []
    pending: list[str] = []

    def flush_pending() -> None:
        if not pending:
            return
        corrected = _correct_builder_prompt(
            _join_prompt_tokens(*pending),
            artist_overrides=artist_overrides,
        )
        if corrected:
            chunks.append(corrected)
        pending.clear()

    for field in fields:
        field_type = field.get("type")
        text = str(field.get("text") or "")
        if field_type == "quality" and not include_quality:
            continue
        if field_type == "artist":
            text = _artist_mix_inline_prompt(text)
        if field_type == "trigger" and (
            _as_bool(field.get("pin"), True) or force_pin_triggers
        ):
            flush_pending()
            trigger_prompt = _join_prompt_tokens(text)
            if trigger_prompt:
                chunks.append(trigger_prompt)
            continue
        pending.append(text)

    flush_pending()
    return _join_prompt_tokens(*chunks)


def _build_advanced_prompts(
    fields: list[dict],
    use_anima_mod_guidance: bool,
    use_negative_anima_mod_guidance: bool,
    pin_trigger_tags_to_front: bool,
) -> tuple[str, str, str, str, bool, bool, str, str]:
    use_amg = _as_bool(use_anima_mod_guidance, False)
    use_negative_amg = _as_bool(use_negative_anima_mod_guidance, False)
    force_pin_triggers = _as_bool(pin_trigger_tags_to_front, False)
    positive = _advanced_pane_parts(fields, "positive")
    negative = _advanced_pane_parts(fields, "negative")
    positive_fields = _advanced_enabled_pane_fields(fields, "positive")
    negative_fields = _advanced_enabled_pane_fields(fields, "negative")

    quality_prompt = _join_prompt_tokens(*positive["quality"])
    artist_prompt = _join_prompt_tokens(*positive["artist"])
    regular_prompt = _correct_advanced_field_sequence(
        positive_fields,
        include_quality=True,
        artist_overrides=artist_prompt,
        force_pin_triggers=force_pin_triggers,
    )
    amg_prompt = _correct_advanced_field_sequence(
        positive_fields,
        include_quality=False,
        artist_overrides=artist_prompt,
        force_pin_triggers=force_pin_triggers,
    )
    metadata_prompt = regular_prompt

    negative_quality_prompt = _join_prompt_tokens(*negative["quality"])
    negative_artist_prompt = _join_prompt_tokens(*negative["artist"])
    negative_regular_prompt = _correct_advanced_field_sequence(
        negative_fields,
        include_quality=True,
        artist_overrides=negative_artist_prompt,
    )
    negative_amg_prompt = _correct_advanced_field_sequence(
        negative_fields,
        include_quality=False,
        artist_overrides=negative_artist_prompt,
    )

    filter_words = resolve_metadata_filter_words()
    metadata_prompt = _filter_metadata_prompt(metadata_prompt, filter_words)
    metadata_negative_prompt = _filter_metadata_prompt(negative_regular_prompt, filter_words)
    output_prompt = amg_prompt if use_amg else regular_prompt
    output_negative_prompt = negative_amg_prompt if use_negative_amg else negative_regular_prompt
    return (
        output_prompt,
        output_negative_prompt,
        quality_prompt,
        negative_quality_prompt,
        use_amg,
        use_negative_amg,
        metadata_prompt,
        metadata_negative_prompt,
    )


def _expand_advanced_wildcard_fields(
    fields: list[dict],
    seed: int,
    mode: str,
) -> tuple[list[dict], dict[str, Any]]:
    mode_key = normalize_prompt_studio_wildcard_mode(mode)
    expanded_fields = _clone_advanced_fields(fields)

    wildcard_fields = []
    wildcard_texts = []
    for field in expanded_fields:
        text = str(field.get("text") or "")
        if has_wildcard_syntax(text):
            wildcard_fields.append(field)
            wildcard_texts.append(text)

    expansions = expand_wildcard_texts(
        wildcard_texts,
        seed=seed,
        mode=mode_key,
    )
    changed = False
    used_keys: list[str] = []
    missing_keys: list[str] = []
    for field, text, result in zip(
        wildcard_fields,
        wildcard_texts,
        expansions,
        strict=True,
    ):
        if result.text != text:
            field["text"] = result.text
            changed = True
        for key in result.used_keys:
            if key not in used_keys:
                used_keys.append(key)
        for key in result.missing_keys:
            if key not in missing_keys:
                missing_keys.append(key)

    return expanded_fields, {
        "changed": changed,
        "used_keys": tuple(used_keys),
        "missing_keys": tuple(missing_keys),
    }


def _advanced_prompt_data_fields(fields: list[dict]) -> list[dict[str, Any]]:
    output = []
    for field in fields:
        output.append({
            "id": str(field.get("id") or ""),
            "pane": str(field.get("pane") or "positive"),
            "type": str(field.get("type") or "general"),
            "label": str(field.get("label") or ""),
            "text": str(field.get("text") or ""),
            "height": _as_advanced_height(field.get("height"), 72),
            "enabled": _as_bool(field.get("enabled"), True),
            "pin": _as_bool(field.get("pin"), field.get("type") == "trigger"),
        })
    return output


def _advanced_artist_field_prompt(fields: list[dict], pane: str) -> str:
    # Artist data is sourced only from Advanced artist fields, not from @ tags in other fields.
    return _join_artist_mix_source_prompts(
        *(
            str(field.get("text") or "")
            for field in fields
            if field.get("pane") == pane
            and field.get("type") == "artist"
            and _as_bool(field.get("enabled"), True)
        )
    )


def _advanced_fields_with_artist_override(fields: list[dict], artist_prompt: str) -> list[dict]:
    artist_text = _join_prompt_tokens(artist_prompt)
    output: list[dict] = []
    inserted = False
    for field in fields:
        if field.get("type") == "artist":
            if artist_text and not inserted:
                item = dict(field)
                item["text"] = artist_text
                output.append(item)
                inserted = True
            continue
        output.append(dict(field))

    if artist_text and not inserted:
        insert_at = 0
        for index, field in enumerate(output):
            if field.get("type") == "quality":
                insert_at = index + 1
        output.insert(insert_at, {
            "id": "artist_mix_override",
            "pane": "positive",
            "type": "artist",
            "label": ADVANCED_FIELD_LABELS["artist"],
            "text": artist_text,
            "height": 72,
            "enabled": True,
            "pin": False,
        })
    return output


def _advanced_prompt_with_artist_override(
    fields: list[dict],
    artist_prompt: str,
    include_quality: bool,
    force_pin_triggers: bool = False,
) -> str:
    return _correct_advanced_field_sequence(
        _advanced_fields_with_artist_override(fields, artist_prompt),
        include_quality=include_quality,
        artist_overrides=artist_prompt,
        force_pin_triggers=force_pin_triggers,
    )




















def _build_advanced_prompt_data(
    compat_result: tuple,
    effective_fields: list[dict],
    saved_fields: list[dict],
    field_inputs: dict[str, str],
    resolution_bucket: str,
    resolution_size: str,
    resolution_custom_width: int,
    resolution_custom_height: int,
    wildcard_mode: str,
    wildcard_seed: int,
    wildcard_seed_after_generate: str,
    wildcard_updates: dict[str, Any] | None = None,
    pin_trigger_tags_to_front: bool = False,
    parameters: dict[str, Any] | None = None,
    artist_mix_mode: str = ARTIST_MIX_MODE_OFF,
    artist_mix_start_percent: float = ARTIST_MIX_DEFAULT_START_PERCENT,
    artist_mix_strength_scale: float = ARTIST_MIX_DEFAULT_STRENGTH_SCALE,
    artist_mix_style_gain: float = ARTIST_MIX_DEFAULT_STYLE_GAIN,
    artist_mix_rms_scale_cap: float = ARTIST_MIX_DEFAULT_RMS_SCALE_CAP,
    artist_mix_exact_top_k: int = ARTIST_MIX_DEFAULT_EXACT_TOP_K,
    artist_mix_cluster_count: int = ARTIST_MIX_DEFAULT_CLUSTER_COUNT,
    artist_mix_dominant_isolation: bool = ARTIST_MIX_DEFAULT_DOMINANT_ISOLATION,
    artist_mix_dominant_threshold: float = ARTIST_MIX_DEFAULT_DOMINANT_THRESHOLD,
) -> dict[str, Any]:
    (
        positive_prompt,
        negative_prompt,
        quality_tags,
        negative_quality_tags,
        use_anima_mod_guidance,
        use_negative_anima_mod_guidance,
        metadata_prompt,
        metadata_negative_prompt,
        width,
        height,
    ) = compat_result
    outputs = {
        name: value
        for name, value in zip(EasyUseAnimaPromptStudioAdvanced.RETURN_NAMES, compat_result)
    }
    positive_fields = _advanced_enabled_pane_fields(effective_fields, "positive")
    negative_fields = _advanced_enabled_pane_fields(effective_fields, "negative")
    positive_artist_prompt = _advanced_artist_field_prompt(effective_fields, "positive")
    negative_artist_prompt = _advanced_artist_field_prompt(effective_fields, "negative")
    positive_artist_inline_prompt = _artist_mix_inline_prompt(positive_artist_prompt)
    negative_artist_inline_prompt = _artist_mix_inline_prompt(negative_artist_prompt)
    force_pin_triggers = _as_bool(pin_trigger_tags_to_front, False)
    positive_without_artist = _advanced_prompt_with_artist_override(
        positive_fields,
        "",
        include_quality=not bool(use_anima_mod_guidance),
        force_pin_triggers=force_pin_triggers,
    )
    metadata_prompt_without_artist = _filter_metadata_prompt(
        _advanced_prompt_with_artist_override(
            positive_fields,
            "",
            include_quality=True,
            force_pin_triggers=force_pin_triggers,
        ),
        resolve_metadata_filter_words(),
    )
    negative_without_artist = _advanced_prompt_with_artist_override(
        negative_fields,
        "",
        include_quality=not bool(use_negative_anima_mod_guidance),
    )
    selected_artist_mix_mode = _normalize_artist_mix_mode(artist_mix_mode, ARTIST_MIX_MODE_OFF)
    artist_mix_enabled = selected_artist_mix_mode not in {ARTIST_MIX_MODE_OFF, ARTIST_MIX_MODE_PROMPT}
    prompt_data_artist_mix_mode = (
        ARTIST_MIX_MODE_PROMPT
        if selected_artist_mix_mode == ARTIST_MIX_MODE_OFF
        else selected_artist_mix_mode
    )
    prompt_data_positive_prompt = positive_without_artist if artist_mix_enabled else positive_prompt
    outputs["positive_prompt"] = prompt_data_positive_prompt
    wildcard_updates = wildcard_updates or {}
    parameters = parameters or {}
    return {
        "schema": PROMPT_DATA_SCHEMA,
        "version": PROMPT_DATA_VERSION,
        "type": PROMPT_DATA_TYPE,
        "source": "EasyUseAnimaPromptStudioAdvancedV2",
        "parameters": dict(parameters),
        "prompt": prompt_data_positive_prompt,
        "positive_prompt": prompt_data_positive_prompt,
        "global_prompt": positive_without_artist,
        "positive_without_artist_section": positive_without_artist,
        "negative_prompt": negative_prompt,
        "negative_without_artist_section": negative_without_artist,
        "metadata_prompt": metadata_prompt,
        "metadata_prompt_without_artist": metadata_prompt_without_artist,
        "metadata_negative_prompt": metadata_negative_prompt,
        "width": int(width),
        "height": int(height),
        "pin_trigger_tags_to_front": force_pin_triggers,
        "outputs": outputs,
        "mod_guidance": {
            "enabled": bool(use_anima_mod_guidance),
            "negative_enabled": bool(use_negative_anima_mod_guidance),
            "quality_tags": quality_tags,
            "negative_prompt": negative_quality_tags,
        },
        "anima_mod_guidance": {
            "use_positive": bool(use_anima_mod_guidance),
            "use_negative": bool(use_negative_anima_mod_guidance),
            "quality_tags": quality_tags,
            "negative_prompt": negative_quality_tags,
        },
        "artist": {
            "source": "advanced_artist_field",
            "handling": "separate" if artist_mix_enabled else "inline",
            "conditioning_mode": prompt_data_artist_mix_mode if artist_mix_enabled else "none",
            "include_in_positive": not artist_mix_enabled,
            "text": positive_artist_inline_prompt,
            "weighted_text": positive_artist_prompt,
            "tags": _artist_tags_from_prompt(positive_artist_prompt),
            "positive_prompt": positive_artist_inline_prompt,
            "negative_prompt": negative_artist_inline_prompt,
            "positive_prompt_without_artist": positive_without_artist,
            "negative_prompt_without_artist": negative_without_artist,
            "positive_count_hint": len(_parse_artist_mix_items(positive_artist_prompt)),
            "negative_count_hint": len(_parse_artist_mix_items(negative_artist_prompt)),
        },
        "artist_mix": {
            "enabled": artist_mix_enabled,
            "mode": prompt_data_artist_mix_mode,
            "base_source": "positive_without_artist_section",
            "base_prompt": positive_without_artist,
            "start_percent": _bounded_artist_mix_float(
                artist_mix_start_percent,
                ARTIST_MIX_DEFAULT_START_PERCENT,
                0.0,
                1.0,
            ),
            "strength_scale": _bounded_artist_mix_float(
                artist_mix_strength_scale,
                ARTIST_MIX_DEFAULT_STRENGTH_SCALE,
                0.0,
                5.0,
            ),
            "style_gain": _bounded_artist_mix_float(
                artist_mix_style_gain,
                ARTIST_MIX_DEFAULT_STYLE_GAIN,
                0.0,
                3.0,
            ),
            "rms_scale_cap": _bounded_artist_mix_float(
                artist_mix_rms_scale_cap,
                ARTIST_MIX_DEFAULT_RMS_SCALE_CAP,
                1.0,
                5.0,
            ),
            "exact_top_k": _bounded_artist_mix_int(
                artist_mix_exact_top_k,
                ARTIST_MIX_DEFAULT_EXACT_TOP_K,
                0,
                64,
            ),
            "cluster_count": _bounded_artist_mix_int(
                artist_mix_cluster_count,
                ARTIST_MIX_DEFAULT_CLUSTER_COUNT,
                1,
                32,
            ),
            "dominant_isolation": _as_bool(
                artist_mix_dominant_isolation,
                ARTIST_MIX_DEFAULT_DOMINANT_ISOLATION,
            ),
            "dominant_threshold": _bounded_artist_mix_float(
                artist_mix_dominant_threshold,
                ARTIST_MIX_DEFAULT_DOMINANT_THRESHOLD,
                0.0,
                1.0,
            ),
            "artist_prompt": positive_artist_prompt,
            "artist_count_hint": len(_parse_artist_mix_items(positive_artist_prompt)),
        },
        "resolution": {
            "width": int(width),
            "height": int(height),
            "bucket": str(resolution_bucket or DEFAULT_ADVANCED_RESOLUTION_BUCKET),
            "size": str(resolution_size or ""),
            "custom_width": _as_int(resolution_custom_width, int(width)),
            "custom_height": _as_int(resolution_custom_height, int(height)),
        },
        "naia": {
            "use_naia": _as_bool(parameters.get("use_naia"), False),
            "consume_on_queue": _as_bool(parameters.get("consume_naia_on_queue"), True),
            "resolution_bucket": str(parameters.get("resolution_bucket") or ""),
        },
        "fields": _advanced_prompt_data_fields(effective_fields),
        "saved_fields": _advanced_prompt_data_fields(saved_fields),
        "field_inputs": dict(field_inputs),
        "wildcard": {
            "mode": str(wildcard_mode or PROMPT_STUDIO_WILDCARD_MODE_LABELS[0]),
            "seed": normalize_seed(wildcard_seed),
            "seed_after_generate": str(wildcard_seed_after_generate or SEED_CONTROL_FIXED),
            "next_seed": wildcard_updates.get("wildcard_seed"),
            "used_keys": list(wildcard_updates.get("wildcard_used_keys") or []),
            "missing_keys": list(wildcard_updates.get("wildcard_missing_keys") or []),
        },
        "compatibility": {
            "return_names": list(EasyUseAnimaPromptStudioAdvanced.RETURN_NAMES),
            "return_types": list(EasyUseAnimaPromptStudioAdvanced.RETURN_TYPES),
        },
    }


def _regional_default_fields() -> list[dict]:
    fields = []
    for field in _advanced_default_fields():
        if field.get("type") == "naia":
            continue
        item = dict(field)
        item["mask_ids"] = []
        fields.append(item)
    return fields


def _regional_fields_json(fields: list[dict] | None = None) -> str:
    return json.dumps(
        fields if fields is not None else _regional_default_fields(),
        ensure_ascii=False,
        separators=(",", ":"),
    )


def _normalize_mask_ids(value) -> list[int]:
    value = _single_value(value)
    if value is None:
        return []
    if isinstance(value, str):
        raw_values = re.split(r"[,;\s]+", value.strip())
    elif isinstance(value, (list, tuple, set)):
        raw_values = list(value)
    else:
        raw_values = [value]

    mask_ids: list[int] = []
    for raw in raw_values:
        mask_id = _as_int(raw, 0)
        if mask_id > 0 and mask_id not in mask_ids:
            mask_ids.append(mask_id)
    return mask_ids


def _normalize_regional_fields(value: str | list | None) -> list[dict]:
    raw = value
    if isinstance(value, str):
        try:
            raw = json.loads(value or "[]")
        except json.JSONDecodeError:
            raw = []
    if not isinstance(raw, list):
        raw = []
    if not raw:
        raw = _regional_default_fields()

    fields: list[dict] = []
    seen_trigger = False
    for index, item in enumerate(raw):
        if not isinstance(item, dict):
            continue
        pane = str(item.get("pane") or "positive").strip().lower()
        if pane not in ADVANCED_FIELD_PANES:
            pane = "positive"
        field_type = str(item.get("type") or "general").strip().lower()
        if field_type not in REGIONAL_FIELD_TYPES:
            field_type = "general"
        if pane == "negative" and field_type == "trigger":
            field_type = "general"
        if field_type == "trigger":
            if seen_trigger:
                continue
            seen_trigger = True
            pane = "positive"
        default_label = ADVANCED_FIELD_LABELS.get(field_type, ADVANCED_FIELD_LABELS["general"])
        label = str(item.get("label") or default_label).strip() or default_label
        field_id = str(item.get("id") or f"{pane}_{field_type}_{index + 1}").strip()
        if not field_id:
            field_id = f"{pane}_{field_type}_{index + 1}"
        mask_ids = _normalize_mask_ids(item.get("mask_ids"))
        if pane != "positive":
            mask_ids = []
        fields.append({
            "id": field_id,
            "pane": pane,
            "type": field_type,
            "label": label,
            "text": str(item.get("text") or ""),
            "height": _as_advanced_height(item.get("height"), 72),
            "enabled": _as_bool(item.get("enabled"), True),
            "pin": _as_bool(item.get("pin"), field_type == "trigger"),
            "collapsed": _as_bool(item.get("collapsed"), False),
            "mask_ids": mask_ids,
        })

    return fields or _regional_default_fields()


def _clone_regional_fields(fields: list[dict]) -> list[dict]:
    return [
        {
            **dict(field),
            "mask_ids": list(field.get("mask_ids") or []),
        }
        for field in fields
    ]


def _apply_regional_field_inputs(fields: list[dict], field_inputs: dict) -> list[dict]:
    values = _advanced_field_input_values(field_inputs)
    if not values:
        return _clone_regional_fields(fields)

    effective = _clone_regional_fields(fields)
    for field in effective:
        name = _advanced_field_socket_name(field)
        if name in values:
            field["text"] = values[name]
    return effective


def _regional_default_config(width: int = 1024, height: int = 1024) -> dict[str, Any]:
    return {
        "version": REGIONAL_CONFIG_VERSION,
        "canvas": {
            "width": int(width),
            "height": int(height),
            "aspect_ratio": _ratio_label(width, height),
            "source": "resolution_fields",
        },
        "mask_authoring": {
            "render_space": "image_pixels",
            "storage_space": "normalized_canvas",
            "preview_enabled": True,
        },
        "global_prompt": "",
        "negative_prompt": "",
        "next_mask_id": 1,
        "masks": [],
        "regional_enabled": False,
        "mask_prompts": [],
        "assignments": [],
        "artist_mix": {},
        "conditioning_settings": {},
        "regional_settings": {},
    }


def _normalize_mask_geometry(value) -> dict[str, float]:
    if not isinstance(value, dict):
        value = {}
    shape = str(value.get("type") or "rect").strip().lower()
    if shape not in {"rect", "ellipse"}:
        shape = "rect"
    x = max(0.0, min(0.99, _as_float(value.get("x"), 0.1)))
    y = max(0.0, min(0.99, _as_float(value.get("y"), 0.1)))
    width = max(0.01, min(1.0, _as_float(value.get("width"), 0.35)))
    height = max(0.01, min(1.0, _as_float(value.get("height"), 0.35)))
    if x + width > 1.0:
        width = max(0.01, 1.0 - x)
    if y + height > 1.0:
        height = max(0.01, 1.0 - y)
    return {
        "type": shape,
        "x": round(x, 6),
        "y": round(y, 6),
        "width": round(width, 6),
        "height": round(height, 6),
    }


def _normalize_regional_mask(value, fallback_id: int) -> dict[str, Any] | None:
    if not isinstance(value, dict):
        return None
    mask_id = _as_int(value.get("mask_id", value.get("id")), fallback_id)
    if mask_id <= 0:
        return None
    default_label = f"Mask {mask_id}"
    name = str(value.get("name") or "").strip()
    label = str(value.get("label") or name or default_label).strip() or default_label
    color = str(value.get("color") or "#3b82f6").strip() or "#3b82f6"
    if not re.fullmatch(r"#[0-9A-Fa-f]{6}", color):
        color = "#3b82f6"
    mask = {
        "mask_id": mask_id,
        "label": label,
        "name": name,
        "color": color,
        "enabled": _as_bool(value.get("enabled"), True),
        "geometry": _normalize_mask_geometry(value.get("geometry")),
    }
    if isinstance(value.get("strokes"), list):
        mask["strokes"] = value["strokes"]
    if isinstance(value.get("shapes"), list):
        mask["shapes"] = value["shapes"]
    return mask


def _normalize_regional_config(
    value: str | dict | None,
    width: int = 1024,
    height: int = 1024,
) -> dict[str, Any]:
    raw = value
    if isinstance(value, str):
        try:
            raw = json.loads(value or "{}")
        except json.JSONDecodeError:
            raw = {}
    if not isinstance(raw, dict):
        raw = {}

    config = _regional_default_config(width, height)
    for key in ("artist_mix", "conditioning_settings", "regional_settings"):
        if isinstance(raw.get(key), dict):
            config[key] = raw[key]
    authoring = raw.get("mask_authoring")
    if isinstance(authoring, dict):
        merged = dict(config["mask_authoring"])
        merged.update({k: v for k, v in authoring.items() if isinstance(k, str)})
        config["mask_authoring"] = merged

    masks: list[dict[str, Any]] = []
    used_ids: set[int] = set()
    raw_masks = raw.get("masks")
    if not isinstance(raw_masks, list):
        raw_masks = raw.get("regions") if isinstance(raw.get("regions"), list) else []
    for index, item in enumerate(raw_masks):
        mask = _normalize_regional_mask(item, index + 1)
        if mask is None or mask["mask_id"] in used_ids:
            continue
        used_ids.add(mask["mask_id"])
        masks.append(mask)
    next_mask_id = max([_as_int(raw.get("next_mask_id"), 1), 1, *(mask["mask_id"] + 1 for mask in masks)])
    config["next_mask_id"] = next_mask_id
    config["masks"] = masks
    config["canvas"] = {
        "width": int(width),
        "height": int(height),
        "aspect_ratio": _ratio_label(width, height),
        "source": "resolution_fields",
    }
    return config


def _regional_config_json(config: dict[str, Any] | None = None) -> str:
    return json.dumps(
        config if config is not None else _regional_default_config(),
        ensure_ascii=False,
        separators=(",", ":"),
    )


def _regional_field_prompt(field: dict, artist_overrides: str = "") -> str:
    return _correct_advanced_field_sequence(
        [field],
        include_quality=True,
        artist_overrides=artist_overrides,
        force_pin_triggers=True,
    )


def _build_regional_outputs(
    fields: list[dict],
    config: dict[str, Any],
    width: int,
    height: int,
) -> tuple[str, str, str, str, dict[str, Any]]:
    positive_fields = [
        field
        for field in fields
        if field.get("pane") == "positive" and _as_bool(field.get("enabled"), True)
    ]
    negative_fields = [
        field
        for field in fields
        if field.get("pane") == "negative" and _as_bool(field.get("enabled"), True)
    ]
    global_positive_fields = [
        field for field in positive_fields if not _normalize_mask_ids(field.get("mask_ids"))
    ]
    mask_positive_fields = [
        field for field in positive_fields if _normalize_mask_ids(field.get("mask_ids"))
    ]

    global_artist_prompt = _join_prompt_tokens(
        *(str(field.get("text") or "") for field in global_positive_fields if field.get("type") == "artist")
    )
    all_artist_prompt = _join_prompt_tokens(
        *(str(field.get("text") or "") for field in positive_fields if field.get("type") == "artist")
    )
    negative_artist_prompt = _join_prompt_tokens(
        *(str(field.get("text") or "") for field in negative_fields if field.get("type") == "artist")
    )

    positive_prompt = _correct_advanced_field_sequence(
        global_positive_fields,
        include_quality=True,
        artist_overrides=global_artist_prompt,
        force_pin_triggers=True,
    )
    negative_prompt = _correct_advanced_field_sequence(
        negative_fields,
        include_quality=True,
        artist_overrides=negative_artist_prompt,
    )
    metadata_prompt = _correct_advanced_field_sequence(
        positive_fields,
        include_quality=True,
        artist_overrides=all_artist_prompt,
        force_pin_triggers=True,
    )

    filter_words = resolve_metadata_filter_words()
    metadata_prompt = _filter_metadata_prompt(metadata_prompt, filter_words)
    metadata_negative_prompt = _filter_metadata_prompt(negative_prompt, filter_words)

    masks = config.get("masks") if isinstance(config.get("masks"), list) else []
    enabled_mask_ids = {
        _as_int(mask.get("mask_id"), 0)
        for mask in masks
        if isinstance(mask, dict) and _as_bool(mask.get("enabled"), True)
    }
    assignments: list[dict[str, Any]] = []
    mask_prompts: list[dict[str, Any]] = []
    for field in mask_positive_fields:
        mask_ids = _normalize_mask_ids(field.get("mask_ids"))
        valid_mask_ids = [mask_id for mask_id in mask_ids if mask_id in enabled_mask_ids]
        missing_mask_ids = [mask_id for mask_id in mask_ids if mask_id not in enabled_mask_ids]
        prompt = _regional_field_prompt(field, all_artist_prompt)
        assignments.append({
            "field_id": str(field.get("id") or ""),
            "mask_ids": mask_ids,
            "valid_mask_ids": valid_mask_ids,
            "missing_mask_ids": missing_mask_ids,
        })
        mask_prompts.append({
            "field_id": str(field.get("id") or ""),
            "type": str(field.get("type") or "general"),
            "label": str(field.get("label") or ""),
            "text": str(field.get("text") or ""),
            "prompt": prompt,
            "mask_ids": mask_ids,
            "valid_mask_ids": valid_mask_ids,
            "missing_mask_ids": missing_mask_ids,
        })

    regional_enabled = any(entry["valid_mask_ids"] for entry in mask_prompts)
    regional_prompt_data = {
        **config,
        "version": REGIONAL_CONFIG_VERSION,
        "schema": REGIONAL_PROMPT_BUNDLE_SCHEMA,
        "canvas": {
            "width": int(width),
            "height": int(height),
            "aspect_ratio": _ratio_label(width, height),
            "source": "resolution_fields",
        },
        "global_prompt": positive_prompt,
        "negative_prompt": negative_prompt,
        "metadata_prompt": metadata_prompt,
        "metadata_negative_prompt": metadata_negative_prompt,
        "masks": masks,
        "regional_enabled": regional_enabled,
        "mask_prompts": mask_prompts,
        "assignments": assignments,
    }
    model_patch_data = {
        "version": REGIONAL_CONFIG_VERSION,
        "regional_attention": {
            "enabled": regional_enabled,
            "assignments": assignments,
            "masks": [
                {
                    "mask_id": mask.get("mask_id"),
                    "label": mask.get("label"),
                    "name": mask.get("name"),
                    "enabled": _as_bool(mask.get("enabled"), True),
                }
                for mask in masks
                if isinstance(mask, dict)
            ],
        },
        "layout_control": {
            "canvas": regional_prompt_data["canvas"],
        },
        "global_mod_guidance": {},
        "artist_mix": config.get("artist_mix") if isinstance(config.get("artist_mix"), dict) else {},
        "compatibility": {
            "schema": REGIONAL_PROMPT_DATA_SCHEMA,
            "version": REGIONAL_CONFIG_VERSION,
            "mask_scoped_prompts": True,
        },
    }
    regional_prompt_data["model_patch_data"] = model_patch_data
    return (
        positive_prompt,
        negative_prompt,
        metadata_prompt,
        metadata_negative_prompt,
        regional_prompt_data,
    )


def _parse_json_object(value: str | dict | None) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value or "{}")
        except json.JSONDecodeError as exc:
            raise ValueError("[EasyUseAnima] regional_prompt_data is not valid JSON.") from exc
        if isinstance(parsed, dict):
            return parsed
    return {}


def _regional_payload_canvas(payload: dict[str, Any]) -> tuple[int, int]:
    canvas = payload.get("canvas") if isinstance(payload.get("canvas"), dict) else {}
    width = max(8, _as_int(canvas.get("width"), 1024))
    height = max(8, _as_int(canvas.get("height"), 1024))
    return width, height


def _conditioning_set_values(conditioning, values: dict[str, Any]) -> list:
    out = []
    for item in conditioning or []:
        if isinstance(item, (list, tuple)) and len(item) >= 2 and isinstance(item[1], dict):
            metadata = dict(item[1])
            metadata.update(values)
            out.append([item[0], metadata])
        else:
            out.append(item)
    return out


def _regional_union_mask_for_ids(
    payload: dict[str, Any],
    mask_ids: list[int],
    width: int,
    height: int,
):
    try:
        import torch  # type: ignore
    except Exception as exc:
        raise RuntimeError("[EasyUseAnima] torch is required to convert regional masks to conditioning.") from exc

    selected_ids = set(mask_ids)
    mask_tensor = torch.zeros((height, width), dtype=torch.float32)
    masks = payload.get("masks") if isinstance(payload.get("masks"), list) else []
    for mask in masks:
        if not isinstance(mask, dict) or not _as_bool(mask.get("enabled"), True):
            continue
        mask_id = _as_int(mask.get("mask_id"), 0)
        if mask_id not in selected_ids:
            continue
        geometry = _normalize_mask_geometry(mask.get("geometry"))
        x0 = max(0, min(width - 1, int(round(geometry["x"] * width))))
        y0 = max(0, min(height - 1, int(round(geometry["y"] * height))))
        x1 = max(x0 + 1, min(width, int(round((geometry["x"] + geometry["width"]) * width))))
        y1 = max(y0 + 1, min(height, int(round((geometry["y"] + geometry["height"]) * height))))
        if geometry["type"] == "ellipse":
            yy = torch.arange(y0, y1, dtype=torch.float32).unsqueeze(1)
            xx = torch.arange(x0, x1, dtype=torch.float32).unsqueeze(0)
            cx = (x0 + x1 - 1) / 2.0
            cy = (y0 + y1 - 1) / 2.0
            rx = max(0.5, (x1 - x0) / 2.0)
            ry = max(0.5, (y1 - y0) / 2.0)
            ellipse = (((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2) <= 1.0
            mask_tensor[y0:y1, x0:x1] = torch.maximum(mask_tensor[y0:y1, x0:x1], ellipse.to(torch.float32))
        else:
            mask_tensor[y0:y1, x0:x1] = 1.0
    return mask_tensor.unsqueeze(0)


def _regional_mask_bounds_area(mask, canvas_width: int | None = None, canvas_height: int | None = None) -> tuple | None:
    try:
        import torch  # type: ignore
    except Exception:
        return None

    if not hasattr(mask, "shape"):
        return None
    if len(mask.shape) == 3:
        mask_2d = torch.max(torch.abs(mask), dim=0).values
    elif len(mask.shape) == 2:
        mask_2d = mask
    else:
        return None

    if mask_2d.numel() == 0 or torch.max(mask_2d != 0) == False:
        return None
    y, x = torch.where(mask_2d != 0)
    height = max(1, int(canvas_height or mask_2d.shape[-2]))
    width = max(1, int(canvas_width or mask_2d.shape[-1]))
    y0 = int(torch.min(y).item())
    y1 = int(torch.max(y).item())
    x0 = int(torch.min(x).item())
    x1 = int(torch.max(x).item())
    latent_height = max(1, height // 8)
    latent_width = max(1, width // 8)
    area_y = max(0, min(latent_height - 1, round(y0 / height * latent_height)))
    area_x = max(0, min(latent_width - 1, round(x0 / width * latent_width)))
    area_height = max(1, round((y1 - y0 + 1) / height * latent_height))
    area_width = max(1, round((x1 - x0 + 1) / width * latent_width))
    area_height = min(area_height, latent_height - area_y)
    area_width = min(area_width, latent_width - area_x)
    return (
        area_height,
        area_width,
        area_y,
        area_x,
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


def _normalize_prompt_studio_wildcard_seed_control(value, wildcard_mode=None) -> str:
    loaded_mode = str(wildcard_mode or "").strip().lower()
    if loaded_mode in PROMPT_STUDIO_LEGACY_FIXED_WILDCARD_MODES:
        return SEED_CONTROL_FIXED
    return PROMPT_STUDIO_WILDCARD_SEED_CONTROL_ALIASES.get(
        str(value or "").strip().lower(),
        SEED_CONTROL_FIXED,
    )


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


class EasyUseAnimaPromptStudioAdvanced:
    """Dynamic positive/negative Prompt Studio with serialized field blocks."""

    DESCRIPTION = (
        "Advanced Prompt Studio with reorderable positive and negative fields, NAIA fill support, "
        "trigger input handling, Mod Guidance routing, metadata outputs, and latent resolution output."
    )
    OUTPUT_TOOLTIPS = (
        "Final positive prompt assembled from enabled positive fields.",
        "Final negative prompt assembled from enabled negative fields.",
        "Positive quality fields routed to Anima Mod Guidance.",
        "Negative quality fields routed to Anima Mod Guidance.",
        "Boolean flag passed through for Anima Mod Guidance workflow control.",
        "Boolean flag passed through for negative Anima Mod Guidance workflow control.",
        "Positive metadata prompt with metadata filters applied.",
        "Negative metadata prompt with metadata filters applied.",
        "Selected latent width.",
        "Selected latent height.",
    )

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "use_naia": ("BOOLEAN", {
                    "default": False,
                    "tooltip": (
                        "Internal request flag. The front-end exposes this as the NAIA Prompt field's "
                        "'Fill from NAIA' button, which fills that field with a fresh NAIA random prompt."
                    ),
                }),
                "consume_naia_on_queue": ("BOOLEAN", {
                    "default": True,
                    "tooltip": (
                        "Internal one-shot mode. Successful NAIA fills are saved with the request flag off "
                        "so loaded workflows reuse the stored prompt."
                    ),
                }),
                "use_anima_mod_guidance": ("BOOLEAN", {
                    "default": False,
                    "tooltip": (
                        "true: positive output excludes quality fields and sends them "
                        "through the mod guidance quality output."
                    ),
                }),
                "resolution_bucket": ("STRING", {
                    "default": DEFAULT_ADVANCED_RESOLUTION_BUCKET,
                    "tooltip": "Internal selected latent resolution bucket.",
                }),
                "resolution_size": ("STRING", {
                    "default": DEFAULT_ADVANCED_RESOLUTION_SIZE,
                    "tooltip": "Internal selected latent resolution, formatted as width * height (ratio).",
                }),
                "resolution_custom_width": ("INT", {
                    "default": 1024,
                    "min": 32,
                    "max": 8192,
                    "step": 32,
                    "tooltip": "Internal custom latent width. Values are snapped to multiples of 32.",
                }),
                "resolution_custom_height": ("INT", {
                    "default": 1024,
                    "min": 32,
                    "max": 8192,
                    "step": 32,
                    "tooltip": "Internal custom latent height. Values are snapped to multiples of 32.",
                }),
                "pin_trigger_tags_to_front": ("BOOLEAN", {
                    "default": False,
                    "tooltip": "Legacy internal flag. Trigger field Pin buttons control trigger placement.",
                }),
                "advanced_fields": ("STRING", {
                    "multiline": True,
                    "default": _advanced_fields_json(),
                    "tooltip": "Internal JSON payload for Advanced Prompt Studio fields.",
                }),
                "use_negative_anima_mod_guidance": ("BOOLEAN", {
                    "default": False,
                    "tooltip": (
                        "true: negative output excludes negative quality fields and sends them "
                        "through the negative Mod Guidance output."
                    ),
                }),
                "wildcard_mode": (PROMPT_STUDIO_WILDCARD_MODE_LABELS, {
                    "default": PROMPT_STUDIO_WILDCARD_MODE_LABELS[0],
                    "tooltip": "General expands deterministically; Sequential uses seed % option_count. Seed control independently decides the next seed.",
                }),
                "wildcard_seed": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": MAX_SEED,
                    "tooltip": (
                        "Wildcard seed used by Advanced Prompt Studio fields. "
                        f"{WILDCARD_SEED_RANGE_NOTE}"
                    ),
                }),
                "wildcard_seed_after_generate": (SEED_CONTROL_MODES, {
                    "default": SEED_CONTROL_FIXED,
                    "tooltip": "After an accepted queue: keep the seed fixed, randomize it, or increment it by one.",
                }),
            },
            "optional": _FlexibleOptionalInputType("STRING"),
            "hidden": {
                "workflow_prompt": "PROMPT",
                "extra_pnginfo": "EXTRA_PNGINFO",
                "unique_id": "UNIQUE_ID",
            },
        }

    RETURN_TYPES = (
        "STRING",
        "STRING",
        "STRING",
        "STRING",
        "BOOLEAN",
        "BOOLEAN",
        "STRING",
        "STRING",
        "INT",
        "INT",
    )
    RETURN_NAMES = (
        "positive_prompt",
        "negative_prompt",
        "anima_mod_guidance_quality_tags",
        "anima_mod_guidance_negative_prompt",
        "use_anima_mod_guidance",
        "use_negative_anima_mod_guidance",
        "metadata_prompt",
        "metadata_negative_prompt",
        "width",
        "height",
    )
    FUNCTION = "build"
    CATEGORY = "EasyUse Anima/Prompt"

    @classmethod
    def _widget_input_names(cls) -> list[str]:
        return list(cls.INPUT_TYPES()["required"].keys())

    @classmethod
    def IS_CHANGED(
        cls,
        use_naia: bool = False,
        consume_naia_on_queue: bool = True,
        use_anima_mod_guidance: bool = False,
        pin_trigger_tags_to_front: bool = False,
        use_negative_anima_mod_guidance: bool = False,
        advanced_fields: str = "",
        resolution_bucket: str = DEFAULT_ADVANCED_RESOLUTION_BUCKET,
        resolution_size: str = DEFAULT_ADVANCED_RESOLUTION_SIZE,
        resolution_custom_width: int = 1024,
        resolution_custom_height: int = 1024,
        wildcard_mode: str = PROMPT_STUDIO_WILDCARD_MODE_LABELS[0],
        wildcard_seed: int = 0,
        wildcard_seed_after_generate: str = SEED_CONTROL_FIXED,
        **kwargs,
    ):
        fields = _normalize_advanced_fields(advanced_fields)
        if _as_bool(use_naia, False) and (
            _advanced_has_enabled_naia(fields)
            or _advanced_uses_naia_resolution(resolution_bucket)
        ):
            return float("nan")
        effective_fields = _apply_advanced_field_inputs(fields, kwargs)
        wildcard_mode_key = normalize_prompt_studio_wildcard_mode(wildcard_mode)
        wildcard_active = True
        wildcard_seed_control = _normalize_prompt_studio_wildcard_seed_control(
            wildcard_seed_after_generate,
            wildcard_mode,
        )
        return _stable_change_key({
            "mode": "prompt_studio_advanced",
            "metadata_filter_words": resolve_metadata_filter_words(),
            "prompt_translation": _prompt_translation_change_key(),
            "wildcard_sources": wildcard_sources_signature() if wildcard_active else {},
            "wildcard_mode": wildcard_mode_key,
            "wildcard_seed": normalize_seed(wildcard_seed),
            "wildcard_seed_after_generate": wildcard_seed_control,
            "use_anima_mod_guidance": _as_bool(use_anima_mod_guidance, False),
            "use_negative_anima_mod_guidance": _as_bool(use_negative_anima_mod_guidance, False),
            "resolution": _advanced_resolution_from_selection(
                resolution_bucket,
                resolution_size,
                resolution_custom_width,
                resolution_custom_height,
            ),
            "pin_trigger_tags_to_front": _as_bool(pin_trigger_tags_to_front, False),
            "advanced_fields": _advanced_fields_json(effective_fields),
        })

    @classmethod
    def _update_metadata_fields(
        cls,
        workflow_prompt,
        extra_pnginfo,
        unique_id,
        advanced_fields: str,
        use_naia: bool,
        extra_updates: dict[str, Any] | None = None,
    ) -> None:
        node_id = _single_value(unique_id)
        if node_id is None:
            return
        node_id = str(node_id)
        updates = {
            "use_naia": _as_bool(use_naia, False),
            "advanced_fields": advanced_fields,
        }
        if extra_updates:
            updates.update(extra_updates)

        if isinstance(workflow_prompt, dict):
            prompt_node = workflow_prompt.get(node_id)
            if isinstance(prompt_node, dict):
                inputs = prompt_node.setdefault("inputs", {})
                for name, value in updates.items():
                    inputs[name] = value

        workflow_node = _get_workflow_node(extra_pnginfo, node_id)
        if workflow_node is None:
            return

        if "advanced_fields" in updates:
            properties = workflow_node.setdefault("properties", {})
            if not isinstance(properties, dict):
                properties = {}
                workflow_node["properties"] = properties
            properties[ADVANCED_FIELDS_WORKFLOW_PROPERTY] = updates["advanced_fields"]

        input_names = cls._widget_input_names()
        widgets_values = workflow_node.setdefault("widgets_values", [])
        for name, value in updates.items():
            if name not in input_names:
                continue
            index = input_names.index(name)
            while len(widgets_values) <= index:
                widgets_values.append(None)
            widgets_values[index] = value

    @staticmethod
    def _ui(
        advanced_fields: str,
        use_naia: bool,
        field_inputs: dict | None = None,
        extra_payload: dict[str, Any] | None = None,
    ):
        payload = {
            "prompt_studio_advanced": [{
                "advanced_fields": advanced_fields,
                "use_naia": _as_bool(use_naia, False),
                "field_inputs": field_inputs or {},
            }]
        }
        if extra_payload:
            payload["prompt_studio_advanced"][0].update(extra_payload)
        return payload

    def build(
        self,
        use_naia: bool,
        consume_naia_on_queue: bool,
        use_anima_mod_guidance: bool,
        pin_trigger_tags_to_front: bool,
        advanced_fields: str,
        use_negative_anima_mod_guidance: bool = False,
        wildcard_mode: str = PROMPT_STUDIO_WILDCARD_MODE_LABELS[0],
        wildcard_seed: int = 0,
        wildcard_seed_after_generate: str = SEED_CONTROL_FIXED,
        resolution_bucket: str = DEFAULT_ADVANCED_RESOLUTION_BUCKET,
        resolution_size: str = DEFAULT_ADVANCED_RESOLUTION_SIZE,
        resolution_custom_width: int = 1024,
        resolution_custom_height: int = 1024,
        workflow_prompt=None,
        extra_pnginfo=None,
        unique_id=None,
        **field_inputs,
    ):
        fields = _normalize_advanced_fields(advanced_fields)
        saved_fields = _clone_advanced_fields(fields)
        effective_field_inputs = _advanced_field_input_values(field_inputs)
        requested_use_naia = _as_bool(use_naia, False)
        enabled_naia_panes = _advanced_enabled_naia_panes(fields)
        use_naia_resolution = _advanced_uses_naia_resolution(resolution_bucket)
        live_use_naia = requested_use_naia and (bool(enabled_naia_panes) or use_naia_resolution)
        metadata_use_naia = live_use_naia
        metadata_updates: dict[str, Any] = {}
        ui_updates: dict[str, Any] = {}
        wildcard_mode_key = normalize_prompt_studio_wildcard_mode(wildcard_mode)
        wildcard_mode_label = (
            PROMPT_STUDIO_WILDCARD_MODE_LABELS[1]
            if wildcard_mode_key == WILDCARD_MODE_SEQUENTIAL
            else PROMPT_STUDIO_WILDCARD_MODE_LABELS[0]
        )
        effective_fields = _apply_advanced_field_inputs(fields, effective_field_inputs)
        wildcard_seed_value = normalize_seed(wildcard_seed)
        wildcard_effective_seed_control = _normalize_prompt_studio_wildcard_seed_control(
            wildcard_seed_after_generate,
            wildcard_mode,
        )
        reserved_next_wildcard_seed = _consume_reserved_wildcard_next_seed(
            field_inputs,
            workflow_prompt,
            unique_id,
            wildcard_seed_value,
            wildcard_mode_key,
            wildcard_effective_seed_control,
        )
        width, height = _advanced_resolution_from_selection(
            resolution_bucket,
            resolution_size,
            resolution_custom_width,
            resolution_custom_height,
        )

        if live_use_naia:
            naia_settings = resolve_naia_settings()
            body = EasyUseAnimaNAIARandomPrompt._make_request_body(
                _as_bool(naia_settings["use_naia_settings"], True),
                naia_settings["pre_prompt"],
                naia_settings["post_prompt"],
                naia_settings["auto_hide"],
                naia_settings["preprocessing"],
            )
            resp = _post_random(
                naia_settings["host"],
                naia_settings["port"],
                body,
                allow_remote_api=bool(naia_settings.get("allow_remote_api", False)),
            )
            naia_prompt, naia_negative, naia_width, naia_height = _parse_random_response(resp)
            if "positive" in enabled_naia_panes:
                saved_fields = _set_naia_field_text(saved_fields, "positive", naia_prompt)
                effective_fields = _set_naia_field_text(effective_fields, "positive", naia_prompt)
            if "negative" in enabled_naia_panes:
                saved_fields = _set_naia_field_text(saved_fields, "negative", naia_negative)
                effective_fields = _set_naia_field_text(effective_fields, "negative", naia_negative)
            if use_naia_resolution:
                width, height = _resolve_naia_resolution(naia_width, naia_height, naia_settings)
                resolution_label = _resolution_label(width, height)
                metadata_updates.update({
                    "resolution_bucket": CUSTOM_ADVANCED_RESOLUTION_BUCKET,
                    "resolution_size": resolution_label,
                    "resolution_custom_width": width,
                    "resolution_custom_height": height,
                })
                ui_updates.update({
                    "resolution_bucket": NAIA_ADVANCED_RESOLUTION_BUCKET,
                    "resolution_size": resolution_label,
                    "resolution_custom_width": width,
                    "resolution_custom_height": height,
                })
            metadata_use_naia = False

        ui_fields = _clone_advanced_fields(saved_fields)
        effective_fields, effective_wildcard = _expand_advanced_wildcard_fields(
            effective_fields,
            wildcard_seed_value,
            wildcard_mode_key,
        )
        effective_fields = _translate_prompt_fields(effective_fields)
        next_wildcard_seed = (
            reserved_next_wildcard_seed
            if reserved_next_wildcard_seed is not None
            else next_seed(wildcard_seed_value, wildcard_effective_seed_control)
        )
        ui_updates.update({
            "wildcard_mode": wildcard_mode_label,
            "wildcard_seed": next_wildcard_seed,
            "wildcard_seed_after_generate": wildcard_effective_seed_control,
            "wildcard_used_keys": list(effective_wildcard["used_keys"]),
            "wildcard_missing_keys": list(effective_wildcard["missing_keys"]),
        })
        metadata_updates.update({
            "wildcard_mode": wildcard_mode_label,
            "wildcard_seed": wildcard_seed_value,
            "wildcard_seed_after_generate": SEED_CONTROL_FIXED,
        })

        fields_json = _advanced_fields_json(saved_fields)
        ui_fields_json = _advanced_fields_json(ui_fields)
        if live_use_naia or metadata_updates:
            self._update_metadata_fields(
                workflow_prompt,
                extra_pnginfo,
                unique_id,
                fields_json,
                metadata_use_naia,
                metadata_updates,
            )

        result = _build_advanced_prompts(
            effective_fields,
            use_anima_mod_guidance,
            use_negative_anima_mod_guidance,
            pin_trigger_tags_to_front,
        )
        return {
            "ui": self._ui(ui_fields_json, requested_use_naia, effective_field_inputs, ui_updates),
            "result": (*result, width, height),
        }


class EasyUseAnimaPromptStudioAdvancedV2(EasyUseAnimaPromptStudioAdvanced):
    """Advanced Prompt Studio v2 with structured prompt data output."""

    DESCRIPTION = (
        "Advanced Prompt Studio v2. It outputs a single EASYUSE_ANIMA_PROMPT_DATA "
        "dict socket for downstream nodes."
    )
    OUTPUT_TOOLTIPS = ("Structured prompt data dict for downstream EasyUse Anima nodes.",)
    RETURN_TYPES = (PROMPT_DATA_TYPE,)
    RETURN_NAMES = (PROMPT_DATA_TYPE,)

    @classmethod
    def INPUT_TYPES(cls):
        base = EasyUseAnimaPromptStudioAdvanced.INPUT_TYPES()
        required = dict(base["required"])
        required.update({
            "artist_mix_mode": (list(ARTIST_MIX_STUDIO_MODES), {
                "default": ARTIST_MIX_MODE_OFF,
                "tooltip": _artist_mix_mode_tooltip(),
            }),
            "artist_mix_start_percent": ("FLOAT", {
                "default": ARTIST_MIX_DEFAULT_START_PERCENT,
                "min": 0.0,
                "max": 1.0,
                "step": 0.01,
                "tooltip": "Start percent used by late/scheduled artist mix modes.",
            }),
            "artist_mix_strength_scale": ("FLOAT", {
                "default": ARTIST_MIX_DEFAULT_STRENGTH_SCALE,
                "min": 0.0,
                "max": 5.0,
                "step": 0.01,
                "tooltip": "Strength multiplier used by exact artist mix modes.",
            }),
            "artist_mix_style_gain": ("FLOAT", {
                "default": ARTIST_MIX_DEFAULT_STYLE_GAIN,
                "min": 0.0,
                "max": 3.0,
                "step": 0.01,
                "tooltip": "Style delta gain used by delta_rms, hybrid tail, and clustered compressed branches.",
            }),
            "artist_mix_rms_scale_cap": ("FLOAT", {
                "default": ARTIST_MIX_DEFAULT_RMS_SCALE_CAP,
                "min": 1.0,
                "max": 5.0,
                "step": 0.01,
                "tooltip": "Maximum RMS energy restore scale for delta_rms compressed artist branches.",
            }),
            "artist_mix_exact_top_k": ("INT", {
                "default": ARTIST_MIX_DEFAULT_EXACT_TOP_K,
                "min": 0,
                "max": 64,
                "tooltip": "Hybrid mode keeps this many strongest artists as exact positive branches.",
            }),
            "artist_mix_cluster_count": ("INT", {
                "default": ARTIST_MIX_DEFAULT_CLUSTER_COUNT,
                "min": 1,
                "max": 32,
                "tooltip": "Clustered mode compresses non-dominant artists into this many positive branches.",
            }),
            "artist_mix_dominant_isolation": ("BOOLEAN", {
                "default": ARTIST_MIX_DEFAULT_DOMINANT_ISOLATION,
                "tooltip": "Clustered mode keeps artists above the dominant threshold as exact branches.",
            }),
            "artist_mix_dominant_threshold": ("FLOAT", {
                "default": ARTIST_MIX_DEFAULT_DOMINANT_THRESHOLD,
                "min": 0.0,
                "max": 1.0,
                "step": 0.01,
                "tooltip": "Clustered dominant isolation threshold based on normalized artist weight.",
            }),
        })
        return {
            **base,
            "required": required,
        }

    @classmethod
    def IS_CHANGED(
        cls,
        use_naia: bool = False,
        consume_naia_on_queue: bool = True,
        use_anima_mod_guidance: bool = False,
        pin_trigger_tags_to_front: bool = False,
        use_negative_anima_mod_guidance: bool = False,
        advanced_fields: str = "",
        resolution_bucket: str = DEFAULT_ADVANCED_RESOLUTION_BUCKET,
        resolution_size: str = DEFAULT_ADVANCED_RESOLUTION_SIZE,
        resolution_custom_width: int = 1024,
        resolution_custom_height: int = 1024,
        wildcard_mode: str = PROMPT_STUDIO_WILDCARD_MODE_LABELS[0],
        wildcard_seed: int = 0,
        wildcard_seed_after_generate: str = SEED_CONTROL_FIXED,
        artist_mix_mode: str = ARTIST_MIX_MODE_OFF,
        artist_mix_start_percent: float = ARTIST_MIX_DEFAULT_START_PERCENT,
        artist_mix_strength_scale: float = ARTIST_MIX_DEFAULT_STRENGTH_SCALE,
        artist_mix_style_gain: float = ARTIST_MIX_DEFAULT_STYLE_GAIN,
        artist_mix_rms_scale_cap: float = ARTIST_MIX_DEFAULT_RMS_SCALE_CAP,
        artist_mix_exact_top_k: int = ARTIST_MIX_DEFAULT_EXACT_TOP_K,
        artist_mix_cluster_count: int = ARTIST_MIX_DEFAULT_CLUSTER_COUNT,
        artist_mix_dominant_isolation: bool = ARTIST_MIX_DEFAULT_DOMINANT_ISOLATION,
        artist_mix_dominant_threshold: float = ARTIST_MIX_DEFAULT_DOMINANT_THRESHOLD,
        **field_inputs,
    ):
        base_key = EasyUseAnimaPromptStudioAdvanced.IS_CHANGED(
            use_naia=use_naia,
            consume_naia_on_queue=consume_naia_on_queue,
            use_anima_mod_guidance=use_anima_mod_guidance,
            pin_trigger_tags_to_front=pin_trigger_tags_to_front,
            use_negative_anima_mod_guidance=use_negative_anima_mod_guidance,
            advanced_fields=advanced_fields,
            resolution_bucket=resolution_bucket,
            resolution_size=resolution_size,
            resolution_custom_width=resolution_custom_width,
            resolution_custom_height=resolution_custom_height,
            wildcard_mode=wildcard_mode,
            wildcard_seed=wildcard_seed,
            wildcard_seed_after_generate=wildcard_seed_after_generate,
            **field_inputs,
        )
        if base_key != base_key:
            return base_key
        return _stable_change_key({
            "base": base_key,
            "artist_mix_mode": _normalize_artist_mix_mode(artist_mix_mode, ARTIST_MIX_MODE_OFF),
            "artist_mix_start_percent": _bounded_artist_mix_float(
                artist_mix_start_percent,
                ARTIST_MIX_DEFAULT_START_PERCENT,
                0.0,
                1.0,
            ),
            "artist_mix_strength_scale": _bounded_artist_mix_float(
                artist_mix_strength_scale,
                ARTIST_MIX_DEFAULT_STRENGTH_SCALE,
                0.0,
                5.0,
            ),
            "artist_mix_style_gain": _bounded_artist_mix_float(
                artist_mix_style_gain,
                ARTIST_MIX_DEFAULT_STYLE_GAIN,
                0.0,
                3.0,
            ),
            "artist_mix_rms_scale_cap": _bounded_artist_mix_float(
                artist_mix_rms_scale_cap,
                ARTIST_MIX_DEFAULT_RMS_SCALE_CAP,
                1.0,
                5.0,
            ),
            "artist_mix_exact_top_k": _bounded_artist_mix_int(
                artist_mix_exact_top_k,
                ARTIST_MIX_DEFAULT_EXACT_TOP_K,
                0,
                64,
            ),
            "artist_mix_cluster_count": _bounded_artist_mix_int(
                artist_mix_cluster_count,
                ARTIST_MIX_DEFAULT_CLUSTER_COUNT,
                1,
                32,
            ),
            "artist_mix_dominant_isolation": _as_bool(
                artist_mix_dominant_isolation,
                ARTIST_MIX_DEFAULT_DOMINANT_ISOLATION,
            ),
            "artist_mix_dominant_threshold": _bounded_artist_mix_float(
                artist_mix_dominant_threshold,
                ARTIST_MIX_DEFAULT_DOMINANT_THRESHOLD,
                0.0,
                1.0,
            ),
        })

    def build(
        self,
        use_naia: bool,
        consume_naia_on_queue: bool,
        use_anima_mod_guidance: bool,
        pin_trigger_tags_to_front: bool,
        advanced_fields: str,
        use_negative_anima_mod_guidance: bool = False,
        wildcard_mode: str = PROMPT_STUDIO_WILDCARD_MODE_LABELS[0],
        wildcard_seed: int = 0,
        wildcard_seed_after_generate: str = SEED_CONTROL_FIXED,
        resolution_bucket: str = DEFAULT_ADVANCED_RESOLUTION_BUCKET,
        resolution_size: str = DEFAULT_ADVANCED_RESOLUTION_SIZE,
        resolution_custom_width: int = 1024,
        resolution_custom_height: int = 1024,
        artist_mix_mode: str = ARTIST_MIX_MODE_OFF,
        artist_mix_start_percent: float = ARTIST_MIX_DEFAULT_START_PERCENT,
        artist_mix_strength_scale: float = ARTIST_MIX_DEFAULT_STRENGTH_SCALE,
        artist_mix_style_gain: float = ARTIST_MIX_DEFAULT_STYLE_GAIN,
        artist_mix_rms_scale_cap: float = ARTIST_MIX_DEFAULT_RMS_SCALE_CAP,
        artist_mix_exact_top_k: int = ARTIST_MIX_DEFAULT_EXACT_TOP_K,
        artist_mix_cluster_count: int = ARTIST_MIX_DEFAULT_CLUSTER_COUNT,
        artist_mix_dominant_isolation: bool = ARTIST_MIX_DEFAULT_DOMINANT_ISOLATION,
        artist_mix_dominant_threshold: float = ARTIST_MIX_DEFAULT_DOMINANT_THRESHOLD,
        workflow_prompt=None,
        extra_pnginfo=None,
        unique_id=None,
        **field_inputs,
    ):
        base = super().build(
            use_naia,
            consume_naia_on_queue,
            use_anima_mod_guidance,
            pin_trigger_tags_to_front,
            advanced_fields,
            use_negative_anima_mod_guidance=use_negative_anima_mod_guidance,
            wildcard_mode=wildcard_mode,
            wildcard_seed=wildcard_seed,
            wildcard_seed_after_generate=wildcard_seed_after_generate,
            resolution_bucket=resolution_bucket,
            resolution_size=resolution_size,
            resolution_custom_width=resolution_custom_width,
            resolution_custom_height=resolution_custom_height,
            workflow_prompt=workflow_prompt,
            extra_pnginfo=extra_pnginfo,
            unique_id=unique_id,
            **field_inputs,
        )
        compat_result = tuple(base.get("result") or ())
        ui_payloads = base.get("ui", {}).get("prompt_studio_advanced", [])
        ui_payload = ui_payloads[0] if ui_payloads and isinstance(ui_payloads[0], dict) else {}
        if isinstance(ui_payload, dict):
            ui_payload.update({
                "artist_mix_mode": _normalize_artist_mix_mode(artist_mix_mode, ARTIST_MIX_MODE_OFF),
                "artist_mix_start_percent": _bounded_artist_mix_float(
                    artist_mix_start_percent,
                    ARTIST_MIX_DEFAULT_START_PERCENT,
                    0.0,
                    1.0,
                ),
                "artist_mix_strength_scale": _bounded_artist_mix_float(
                    artist_mix_strength_scale,
                    ARTIST_MIX_DEFAULT_STRENGTH_SCALE,
                    0.0,
                    5.0,
                ),
                "artist_mix_style_gain": _bounded_artist_mix_float(
                    artist_mix_style_gain,
                    ARTIST_MIX_DEFAULT_STYLE_GAIN,
                    0.0,
                    3.0,
                ),
                "artist_mix_rms_scale_cap": _bounded_artist_mix_float(
                    artist_mix_rms_scale_cap,
                    ARTIST_MIX_DEFAULT_RMS_SCALE_CAP,
                    1.0,
                    5.0,
                ),
                "artist_mix_exact_top_k": _bounded_artist_mix_int(
                    artist_mix_exact_top_k,
                    ARTIST_MIX_DEFAULT_EXACT_TOP_K,
                    0,
                    64,
                ),
                "artist_mix_cluster_count": _bounded_artist_mix_int(
                    artist_mix_cluster_count,
                    ARTIST_MIX_DEFAULT_CLUSTER_COUNT,
                    1,
                    32,
                ),
                "artist_mix_dominant_isolation": _as_bool(
                    artist_mix_dominant_isolation,
                    ARTIST_MIX_DEFAULT_DOMINANT_ISOLATION,
                ),
                "artist_mix_dominant_threshold": _bounded_artist_mix_float(
                    artist_mix_dominant_threshold,
                    ARTIST_MIX_DEFAULT_DOMINANT_THRESHOLD,
                    0.0,
                    1.0,
                ),
            })
        saved_fields = _normalize_advanced_fields(ui_payload.get("advanced_fields", advanced_fields))
        effective_field_inputs = _advanced_field_input_values(ui_payload.get("field_inputs") or field_inputs)
        wildcard_mode_key = normalize_prompt_studio_wildcard_mode(wildcard_mode)
        effective_fields = _apply_advanced_field_inputs(saved_fields, effective_field_inputs)
        effective_fields, _wildcard = _expand_advanced_wildcard_fields(
            effective_fields,
            normalize_seed(wildcard_seed),
            wildcard_mode_key,
        )
        effective_fields = _translate_prompt_fields(effective_fields)
        prompt_data_parameters = _prompt_data_parameter_snapshot(
            self.INPUT_TYPES().get("required", {}),
            {
                "use_naia": use_naia,
                "consume_naia_on_queue": consume_naia_on_queue,
                "use_anima_mod_guidance": use_anima_mod_guidance,
                "pin_trigger_tags_to_front": pin_trigger_tags_to_front,
                "advanced_fields": advanced_fields,
                "use_negative_anima_mod_guidance": use_negative_anima_mod_guidance,
                "wildcard_mode": (
                    PROMPT_STUDIO_WILDCARD_MODE_LABELS[1]
                    if wildcard_mode_key == WILDCARD_MODE_SEQUENTIAL
                    else PROMPT_STUDIO_WILDCARD_MODE_LABELS[0]
                ),
                "wildcard_seed": wildcard_seed,
                "wildcard_seed_after_generate": _normalize_prompt_studio_wildcard_seed_control(
                    wildcard_seed_after_generate,
                    wildcard_mode,
                ),
                "resolution_bucket": resolution_bucket,
                "resolution_size": resolution_size,
                "resolution_custom_width": resolution_custom_width,
                "resolution_custom_height": resolution_custom_height,
                "artist_mix_mode": artist_mix_mode,
                "artist_mix_start_percent": artist_mix_start_percent,
                "artist_mix_strength_scale": artist_mix_strength_scale,
                "artist_mix_style_gain": artist_mix_style_gain,
                "artist_mix_rms_scale_cap": artist_mix_rms_scale_cap,
                "artist_mix_exact_top_k": artist_mix_exact_top_k,
                "artist_mix_cluster_count": artist_mix_cluster_count,
                "artist_mix_dominant_isolation": artist_mix_dominant_isolation,
                "artist_mix_dominant_threshold": artist_mix_dominant_threshold,
                **field_inputs,
            },
            ui_payload,
        )
        prompt_data_parameters["wildcard_seed"] = normalize_seed(wildcard_seed)
        prompt_data = _build_advanced_prompt_data(
            compat_result,
            effective_fields,
            saved_fields,
            effective_field_inputs,
            str(ui_payload.get("resolution_bucket", resolution_bucket)),
            str(ui_payload.get("resolution_size", resolution_size)),
            _as_int(ui_payload.get("resolution_custom_width", resolution_custom_width), resolution_custom_width),
            _as_int(ui_payload.get("resolution_custom_height", resolution_custom_height), resolution_custom_height),
            str(ui_payload.get("wildcard_mode", wildcard_mode)),
            normalize_seed(wildcard_seed),
            str(ui_payload.get("wildcard_seed_after_generate", wildcard_seed_after_generate)),
            ui_payload,
            pin_trigger_tags_to_front,
            parameters=prompt_data_parameters,
            artist_mix_mode=artist_mix_mode,
            artist_mix_start_percent=artist_mix_start_percent,
            artist_mix_strength_scale=artist_mix_strength_scale,
            artist_mix_style_gain=artist_mix_style_gain,
            artist_mix_rms_scale_cap=artist_mix_rms_scale_cap,
            artist_mix_exact_top_k=artist_mix_exact_top_k,
            artist_mix_cluster_count=artist_mix_cluster_count,
            artist_mix_dominant_isolation=artist_mix_dominant_isolation,
            artist_mix_dominant_threshold=artist_mix_dominant_threshold,
        )
        return {
            **base,
            "result": (prompt_data,),
        }








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


def _load_aio_resources_from_input_context(context: dict[str, Any]):
    resource_info = context.get("resource_info", {})
    if not isinstance(resource_info, dict):
        resource_info = {}
    settings = _normalize_aio_input_settings(context.get("input_settings", {}))
    resources = settings.get("resources", {})
    if not isinstance(resources, dict):
        resources = {}

    unet_name = str(resource_info.get("unet_name") or "").strip()
    vae_name = str(resource_info.get("vae_name") or "").strip()
    clip_name = str(resource_info.get("clip_name") or "").strip()
    clip_type = str(resource_info.get("clip_type") or "qwen_image")
    missing = [
        label
        for label, value in (
            ("unet_name", unet_name),
            ("vae_name", vae_name),
            ("clip_name", clip_name),
        )
        if not value
    ]
    if missing:
        raise RuntimeError(
            "[EasyUseAnima] easy use anima input resource_info is missing required value(s): "
            + ", ".join(missing)
        )

    model = _load_diffusion_model_with_comfy(
        unet_name,
        str(resources.get("unet_weight_dtype") or resource_info.get("unet_weight_dtype") or "default"),
    )
    vae = _load_vae_with_comfy(vae_name)
    clip = _load_clip_with_comfy(
        clip_name,
        clip_type,
        str(resources.get("clip_device") or resource_info.get("clip_device") or "default"),
    )
    return model, clip, vae


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


class EasyUseAnimaPromptStudioRegional:
    """Mask-scoped Prompt Studio with serialized prompt fields and mask config."""

    DESCRIPTION = (
        "Regional Prompt Studio that stores numbered user masks and applies selected "
        "positive prompt fields only inside those masks. Connect regional_prompt_data "
        "to Anima Regional Conditioning to create KSampler-ready conditionings."
    )
    OUTPUT_TOOLTIPS = (
        "Metadata positive prompt with global and mask-scoped prompt fields included.",
        "Metadata negative prompt with metadata filters applied.",
        "Selected latent width used by the mask editor canvas.",
        "Selected latent height used by the mask editor canvas.",
        "Bundled regional prompt, mask, and model-patch data for Anima Regional Conditioning.",
    )

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "regional_fields": ("STRING", {
                    "multiline": True,
                    "default": _regional_fields_json(),
                    "tooltip": "Internal JSON payload for Regional Prompt Studio fields.",
                }),
                "regional_config": ("STRING", {
                    "multiline": True,
                    "default": _regional_config_json(),
                    "tooltip": "Internal JSON payload for numbered masks and mask editor settings.",
                }),
                "resolution_bucket": ("STRING", {
                    "default": DEFAULT_ADVANCED_RESOLUTION_BUCKET,
                    "tooltip": "Internal selected latent resolution bucket.",
                }),
                "resolution_size": ("STRING", {
                    "default": DEFAULT_ADVANCED_RESOLUTION_SIZE,
                    "tooltip": "Internal selected latent resolution, formatted as width * height (ratio).",
                }),
                "resolution_custom_width": ("INT", {
                    "default": 1024,
                    "min": 32,
                    "max": 8192,
                    "step": 32,
                    "tooltip": "Internal custom latent width. Values are snapped to multiples of 32.",
                }),
                "resolution_custom_height": ("INT", {
                    "default": 1024,
                    "min": 32,
                    "max": 8192,
                    "step": 32,
                    "tooltip": "Internal custom latent height. Values are snapped to multiples of 32.",
                }),
                "wildcard_mode": (PROMPT_STUDIO_WILDCARD_MODE_LABELS, {
                    "default": PROMPT_STUDIO_WILDCARD_MODE_LABELS[0],
                    "tooltip": "General expands deterministically; Sequential uses seed % option_count. Seed control independently decides the next seed.",
                }),
                "wildcard_seed": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": MAX_SEED,
                    "tooltip": (
                        "Wildcard seed used by Regional Prompt Studio fields. "
                        f"{WILDCARD_SEED_RANGE_NOTE}"
                    ),
                }),
                "wildcard_seed_after_generate": (SEED_CONTROL_MODES, {
                    "default": SEED_CONTROL_FIXED,
                    "tooltip": "After an accepted queue: keep the seed fixed, randomize it, or increment it by one.",
                }),
            },
            "optional": _FlexibleOptionalInputType("STRING"),
            "hidden": {
                "workflow_prompt": "PROMPT",
                "extra_pnginfo": "EXTRA_PNGINFO",
                "unique_id": "UNIQUE_ID",
            },
        }

    RETURN_TYPES = (
        "STRING",
        "STRING",
        "INT",
        "INT",
        REGIONAL_PROMPT_DATA_TYPE,
    )
    RETURN_NAMES = (
        "metadata_prompt",
        "metadata_negative_prompt",
        "width",
        "height",
        "regional_prompt_data",
    )
    FUNCTION = "build"
    CATEGORY = "EasyUse Anima/Prompt"

    @classmethod
    def _widget_input_names(cls) -> list[str]:
        return list(cls.INPUT_TYPES()["required"].keys())

    @classmethod
    def IS_CHANGED(
        cls,
        regional_fields: str = "",
        regional_config: str = "",
        resolution_bucket: str = DEFAULT_ADVANCED_RESOLUTION_BUCKET,
        resolution_size: str = DEFAULT_ADVANCED_RESOLUTION_SIZE,
        resolution_custom_width: int = 1024,
        resolution_custom_height: int = 1024,
        wildcard_mode: str = PROMPT_STUDIO_WILDCARD_MODE_LABELS[0],
        wildcard_seed: int = 0,
        wildcard_seed_after_generate: str = SEED_CONTROL_FIXED,
        **kwargs,
    ):
        width, height = _advanced_resolution_from_selection(
            resolution_bucket,
            resolution_size,
            resolution_custom_width,
            resolution_custom_height,
        )
        fields = _normalize_regional_fields(regional_fields)
        effective_fields = _apply_regional_field_inputs(fields, kwargs)
        config = _normalize_regional_config(regional_config, width, height)
        wildcard_mode_key = normalize_prompt_studio_wildcard_mode(wildcard_mode)
        wildcard_active = True
        wildcard_seed_control = _normalize_prompt_studio_wildcard_seed_control(
            wildcard_seed_after_generate,
            wildcard_mode,
        )
        return _stable_change_key({
            "mode": "prompt_studio_regional",
            "metadata_filter_words": resolve_metadata_filter_words(),
            "prompt_translation": _prompt_translation_change_key(),
            "wildcard_sources": wildcard_sources_signature() if wildcard_active else {},
            "wildcard_mode": wildcard_mode_key,
            "wildcard_seed": normalize_seed(wildcard_seed),
            "wildcard_seed_after_generate": wildcard_seed_control,
            "resolution": (width, height),
            "regional_fields": _regional_fields_json(effective_fields),
            "regional_config": _regional_config_json(config),
        })

    @classmethod
    def _update_metadata_fields(
        cls,
        workflow_prompt,
        extra_pnginfo,
        unique_id,
        regional_fields: str,
        regional_config: str,
        extra_updates: dict[str, Any] | None = None,
    ) -> None:
        node_id = _single_value(unique_id)
        if node_id is None:
            return
        node_id = str(node_id)
        updates = {
            "regional_fields": regional_fields,
            "regional_config": regional_config,
        }
        if extra_updates:
            updates.update(extra_updates)

        if isinstance(workflow_prompt, dict):
            prompt_node = workflow_prompt.get(node_id)
            if isinstance(prompt_node, dict):
                inputs = prompt_node.setdefault("inputs", {})
                for name, value in updates.items():
                    inputs[name] = value

        workflow_node = _get_workflow_node(extra_pnginfo, node_id)
        if workflow_node is None:
            return

        properties = workflow_node.setdefault("properties", {})
        if not isinstance(properties, dict):
            properties = {}
            workflow_node["properties"] = properties
        properties[REGIONAL_FIELDS_WORKFLOW_PROPERTY] = regional_fields
        properties[REGIONAL_CONFIG_WORKFLOW_PROPERTY] = regional_config

        input_names = cls._widget_input_names()
        widgets_values = workflow_node.setdefault("widgets_values", [])
        for name, value in updates.items():
            if name not in input_names:
                continue
            index = input_names.index(name)
            while len(widgets_values) <= index:
                widgets_values.append(None)
            widgets_values[index] = value

    @staticmethod
    def _ui(
        regional_fields: str,
        regional_config: str,
        field_inputs: dict | None = None,
        extra_payload: dict[str, Any] | None = None,
    ):
        payload = {
            "prompt_studio_regional": [{
                "regional_fields": regional_fields,
                "regional_config": regional_config,
                "field_inputs": field_inputs or {},
            }]
        }
        if extra_payload:
            payload["prompt_studio_regional"][0].update(extra_payload)
        return payload

    def build(
        self,
        regional_fields: str,
        regional_config: str,
        resolution_bucket: str = DEFAULT_ADVANCED_RESOLUTION_BUCKET,
        resolution_size: str = DEFAULT_ADVANCED_RESOLUTION_SIZE,
        resolution_custom_width: int = 1024,
        resolution_custom_height: int = 1024,
        wildcard_mode: str = PROMPT_STUDIO_WILDCARD_MODE_LABELS[0],
        wildcard_seed: int = 0,
        wildcard_seed_after_generate: str = SEED_CONTROL_FIXED,
        workflow_prompt=None,
        extra_pnginfo=None,
        unique_id=None,
        **field_inputs,
    ):
        width, height = _advanced_resolution_from_selection(
            resolution_bucket,
            resolution_size,
            resolution_custom_width,
            resolution_custom_height,
        )
        fields = _normalize_regional_fields(regional_fields)
        saved_fields = _clone_regional_fields(fields)
        effective_field_inputs = _advanced_field_input_values(field_inputs)
        config = _normalize_regional_config(regional_config, width, height)

        wildcard_mode_key = normalize_prompt_studio_wildcard_mode(wildcard_mode)
        wildcard_mode_label = (
            PROMPT_STUDIO_WILDCARD_MODE_LABELS[1]
            if wildcard_mode_key == WILDCARD_MODE_SEQUENTIAL
            else PROMPT_STUDIO_WILDCARD_MODE_LABELS[0]
        )
        effective_fields = _apply_regional_field_inputs(fields, effective_field_inputs)
        wildcard_seed_value = normalize_seed(wildcard_seed)
        wildcard_effective_seed_control = _normalize_prompt_studio_wildcard_seed_control(
            wildcard_seed_after_generate,
            wildcard_mode,
        )
        reserved_next_wildcard_seed = _consume_reserved_wildcard_next_seed(
            field_inputs,
            workflow_prompt,
            unique_id,
            wildcard_seed_value,
            wildcard_mode_key,
            wildcard_effective_seed_control,
        )
        ui_updates: dict[str, Any] = {}
        metadata_updates: dict[str, Any] = {}

        effective_fields, effective_wildcard = _expand_advanced_wildcard_fields(
            effective_fields,
            wildcard_seed_value,
            wildcard_mode_key,
        )
        effective_fields = _translate_prompt_fields(effective_fields)
        next_wildcard_seed = (
            reserved_next_wildcard_seed
            if reserved_next_wildcard_seed is not None
            else next_seed(wildcard_seed_value, wildcard_effective_seed_control)
        )
        ui_updates.update({
            "wildcard_mode": wildcard_mode_label,
            "wildcard_seed": next_wildcard_seed,
            "wildcard_seed_after_generate": wildcard_effective_seed_control,
            "wildcard_used_keys": list(effective_wildcard["used_keys"]),
            "wildcard_missing_keys": list(effective_wildcard["missing_keys"]),
        })
        metadata_updates.update({
            "wildcard_mode": wildcard_mode_label,
            "wildcard_seed": wildcard_seed_value,
            "wildcard_seed_after_generate": SEED_CONTROL_FIXED,
        })

        fields_json = _regional_fields_json(saved_fields)
        config_json = _regional_config_json(config)
        self._update_metadata_fields(
            workflow_prompt,
            extra_pnginfo,
            unique_id,
            fields_json,
            config_json,
            metadata_updates,
        )

        (
            positive_prompt,
            negative_prompt,
            metadata_prompt,
            metadata_negative_prompt,
            regional_prompt_data,
        ) = _build_regional_outputs(effective_fields, config, width, height)

        return {
            "ui": self._ui(fields_json, config_json, effective_field_inputs, ui_updates),
            "result": (
                metadata_prompt,
                metadata_negative_prompt,
                width,
                height,
                regional_prompt_data,
            ),
        }


class EasyUseAnimaRegionalConditioning:
    """Convert Regional Prompt Studio JSON into KSampler-ready conditionings."""

    DESCRIPTION = (
        "Encodes Anima Prompt Studio Regional data with CLIP and attaches mask metadata "
        "to mask-scoped positive conditioning entries."
    )
    OUTPUT_TOOLTIPS = (
        "Positive conditioning containing the global prompt plus mask-scoped regional entries.",
        "Negative conditioning encoded from the bundled negative prompt.",
    )

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "clip": ("CLIP", {
                    "tooltip": "CLIP model used to encode the bundled global and regional prompts.",
                }),
                "regional_prompt_data": (REGIONAL_PROMPT_DATA_TYPE, {
                    "forceInput": True,
                    "tooltip": "Bundled structured data from Anima Prompt Studio Regional.",
                }),
                "mask_strength": ("FLOAT", {
                    "default": 1.0,
                    "min": 0.0,
                    "max": 10.0,
                    "step": 0.01,
                    "tooltip": "Strength applied to mask-scoped conditioning entries.",
                }),
                "set_cond_area": (["mask bounds", "default"], {
                    "default": "mask bounds",
                    "tooltip": "mask bounds mirrors ComfyUI ConditioningSetMask area behavior.",
                }),
            },
        }

    RETURN_TYPES = ("CONDITIONING", "CONDITIONING")
    RETURN_NAMES = ("positive", "negative")
    FUNCTION = "encode"
    CATEGORY = "EasyUse Anima/Prompt"

    @classmethod
    def IS_CHANGED(
        cls,
        regional_prompt_data: str | dict = "",
        mask_strength: float = 1.0,
        set_cond_area: str = "mask bounds",
        **kwargs,
    ):
        return _stable_change_key({
            "mode": "regional_conditioning",
            "regional_prompt_data": (
                regional_prompt_data
                if isinstance(regional_prompt_data, dict)
                else str(regional_prompt_data or "")
            ),
            "mask_strength": _as_float(mask_strength, 1.0),
            "set_cond_area": str(set_cond_area or "mask bounds"),
        })

    def encode(
        self,
        regional_prompt_data: str | dict,
        clip,
        mask_strength: float = 1.0,
        set_cond_area: str = "mask bounds",
    ):
        payload = _parse_json_object(regional_prompt_data)
        width, height = _regional_payload_canvas(payload)
        positive_prompt = str(payload.get("global_prompt") or payload.get("positive_prompt") or "")
        negative_prompt = str(payload.get("negative_prompt") or "")

        positive = list(_encode_with_comfy_clip(clip, positive_prompt))
        negative = _encode_with_comfy_clip(clip, negative_prompt)

        if _as_bool(payload.get("regional_enabled"), False):
            use_mask_bounds = str(set_cond_area or "mask bounds") != "default"
            mask_prompts = payload.get("mask_prompts") if isinstance(payload.get("mask_prompts"), list) else []
            for entry in mask_prompts:
                if not isinstance(entry, dict):
                    continue
                valid_mask_ids = _normalize_mask_ids(entry.get("valid_mask_ids") or entry.get("mask_ids"))
                prompt = str(entry.get("prompt") or entry.get("text") or "").strip()
                if not valid_mask_ids or not prompt:
                    continue
                mask = _regional_union_mask_for_ids(payload, valid_mask_ids, width, height)
                regional_conditioning = _encode_with_comfy_clip(clip, prompt)
                conditioning_values = {
                    "mask": mask,
                    "set_area_to_bounds": False,
                    "mask_strength": _as_float(mask_strength, 1.0),
                    "easyuse_anima_region": {
                        "field_id": str(entry.get("field_id") or ""),
                        "mask_ids": valid_mask_ids,
                    },
                }
                if use_mask_bounds:
                    area = _regional_mask_bounds_area(mask, width, height)
                    if area is not None:
                        conditioning_values["area"] = area
                positive.extend(_conditioning_set_values(regional_conditioning, conditioning_values))

        return (positive, negative)


class EasyUseAnimaPromptStudioExtend:
    """Extended Prompt Studio with numbered positive/negative prompt rows."""

    @classmethod
    def INPUT_TYPES(cls):
        required = {
            "fill_naia_prompt": ("BOOLEAN", {
                "default": False,
                "tooltip": (
                    "When enabled, slot 3 is filled from NAIA on each queue. "
                    "Saved-image workflows are written with this off and the current slot 3 text stored."
                ),
            }),
            "use_anima_mod_guidance": ("BOOLEAN", {
                "default": False,
                "tooltip": (
                    "true: positive output excludes slots 1-2 quality tags and sends them "
                    "through anima_mod_guidance_quality_tags."
                ),
            }),
            "pin_trigger_tags_to_front": ("BOOLEAN", {
                "default": False,
                "tooltip": "true: keep prompt correction trigger-like tags at the front where applicable.",
            }),
        }
        for name, _pane, _field_type, label, default, height in EXTEND_PROMPT_SLOT_SPECS:
            required[name] = ("STRING", {
                "multiline": True,
                "default": default,
                "tooltip": label,
                "placeholder": label,
                "height": height,
            })
        required["active_slots"] = ("STRING", {
            "default": json.dumps(["quality_tags_1", "general_tags_4", "trailing_tags_10"]),
            "tooltip": "Internal Prompt Studio Extend visible slot state.",
        })
        required["use_negative_anima_mod_guidance"] = ("BOOLEAN", {
            "default": False,
            "tooltip": (
                "true: negative output excludes negative quality slots and sends them "
                "through the negative Mod Guidance output."
            ),
        })
        return {
            "required": required,
            "hidden": {
                "workflow_prompt": "PROMPT",
                "extra_pnginfo": "EXTRA_PNGINFO",
                "unique_id": "UNIQUE_ID",
            },
        }

    RETURN_TYPES = (
        "STRING",
        "STRING",
        "STRING",
        "STRING",
        "BOOLEAN",
        "BOOLEAN",
        "STRING",
        "STRING",
    )
    RETURN_NAMES = (
        "positive_prompt",
        "negative_prompt",
        "anima_mod_guidance_quality_tags",
        "anima_mod_guidance_negative_prompt",
        "use_anima_mod_guidance",
        "use_negative_anima_mod_guidance",
        "metadata_prompt",
        "metadata_negative_prompt",
    )
    FUNCTION = "build"
    CATEGORY = "EasyUse Anima/Prompt"

    @classmethod
    def _widget_input_names(cls) -> list[str]:
        return list(cls.INPUT_TYPES()["required"].keys())

    @classmethod
    def IS_CHANGED(
        cls,
        fill_naia_prompt: bool = False,
        use_anima_mod_guidance: bool = False,
        pin_trigger_tags_to_front: bool = False,
        use_negative_anima_mod_guidance: bool = False,
        **kwargs,
    ):
        if _as_bool(fill_naia_prompt, False):
            return float("nan")
        return _stable_change_key({
            "mode": "prompt_studio_extend",
            "metadata_filter_words": resolve_metadata_filter_words(),
            "prompt_translation": _prompt_translation_change_key(),
            "use_anima_mod_guidance": _as_bool(use_anima_mod_guidance, False),
            "use_negative_anima_mod_guidance": _as_bool(use_negative_anima_mod_guidance, False),
            "pin_trigger_tags_to_front": _as_bool(pin_trigger_tags_to_front, False),
            "active_slots": str(kwargs.get("active_slots", "")),
            **{
                name: str(kwargs.get(name, ""))
                for name, *_rest in EXTEND_PROMPT_SLOT_SPECS
            },
        })

    @classmethod
    def _update_metadata_slots(
        cls,
        workflow_prompt,
        extra_pnginfo,
        unique_id,
        updates: dict[str, Any],
    ) -> None:
        node_id = _single_value(unique_id)
        if node_id is None:
            return
        node_id = str(node_id)

        if isinstance(workflow_prompt, dict):
            prompt_node = workflow_prompt.get(node_id)
            if isinstance(prompt_node, dict):
                inputs = prompt_node.setdefault("inputs", {})
                for name, value in updates.items():
                    inputs[name] = value

        workflow_node = _get_workflow_node(extra_pnginfo, node_id)
        if workflow_node is None:
            return

        input_names = cls._widget_input_names()
        widgets_values = workflow_node.setdefault("widgets_values", [])
        for name, value in updates.items():
            if name not in input_names:
                continue
            index = input_names.index(name)
            while len(widgets_values) <= index:
                widgets_values.append(None)
            widgets_values[index] = value

    @staticmethod
    @staticmethod
    def _active_slot_set(active_slots: Any) -> set[str] | None:
        if active_slots is None:
            return None
        parsed = active_slots
        if isinstance(active_slots, str):
            if not active_slots.strip():
                return None
            try:
                parsed = json.loads(active_slots)
            except json.JSONDecodeError:
                return None
        if not isinstance(parsed, list):
            return None
        valid_names = {name for name, *_rest in EXTEND_PROMPT_SLOT_SPECS}
        return {str(name) for name in parsed if str(name) in valid_names}

    @staticmethod
    def _fields_from_slots(values: dict[str, str], active_slots: Any = None) -> list[dict]:
        active_slot_names = EasyUseAnimaPromptStudioExtend._active_slot_set(active_slots)
        fields = []
        for name, pane, field_type, label, _default, height in EXTEND_PROMPT_SLOT_SPECS:
            if active_slot_names is not None and name not in active_slot_names:
                continue
            text = str(values.get(name, "") or "")
            fields.append({
                "id": name,
                "pane": pane,
                "type": field_type,
                "label": label,
                "text": text,
                "height": height,
                "enabled": bool(text.strip()),
            })
        return fields

    @staticmethod
    def _ui(slot_values: dict[str, str], fill_naia_prompt: bool, active_slots: Any = None):
        return {
            "prompt_studio_slots": [{
                **slot_values,
                "fill_naia_prompt": _as_bool(fill_naia_prompt, False),
                "active_slots": active_slots,
            }]
        }

    def build(
        self,
        fill_naia_prompt: bool,
        use_anima_mod_guidance: bool,
        pin_trigger_tags_to_front: bool,
        use_negative_anima_mod_guidance: bool = False,
        workflow_prompt=None,
        extra_pnginfo=None,
        unique_id=None,
        **slot_values,
    ):
        active_slots = slot_values.get("active_slots")
        values = {
            name: str(slot_values.get(name, default) or "")
            for name, _pane, _field_type, _label, default, _height in EXTEND_PROMPT_SLOT_SPECS
        }
        live_fill_naia = _as_bool(fill_naia_prompt, False)
        metadata_fill_naia = live_fill_naia

        if live_fill_naia:
            naia_settings = resolve_naia_settings()
            body = EasyUseAnimaNAIARandomPrompt._make_request_body(
                _as_bool(naia_settings["use_naia_settings"], True),
                naia_settings["pre_prompt"],
                naia_settings["post_prompt"],
                naia_settings["auto_hide"],
                naia_settings["preprocessing"],
            )
            resp = _post_random(
                naia_settings["host"],
                naia_settings["port"],
                body,
                allow_remote_api=bool(naia_settings.get("allow_remote_api", False)),
            )
            naia_prompt, _naia_negative, _naia_width, _naia_height = _parse_random_response(resp)
            values["naia_prompt_3"] = naia_prompt
            metadata_fill_naia = False

        if live_fill_naia:
            self._update_metadata_slots(
                workflow_prompt,
                extra_pnginfo,
                unique_id,
                {
                    "fill_naia_prompt": metadata_fill_naia,
                    "naia_prompt_3": values["naia_prompt_3"],
                },
            )

        effective_values = {
            name: _translate_prompt_text(value)
            for name, value in values.items()
        }
        result = _build_advanced_prompts(
            self._fields_from_slots(effective_values, active_slots),
            use_anima_mod_guidance,
            use_negative_anima_mod_guidance,
            pin_trigger_tags_to_front,
        )
        return {
            "ui": self._ui(values, live_fill_naia, active_slots),
            "result": result,
        }


class EasyUseAnimaSAM3Context:
    """Load a native ComfyUI SAM3 checkpoint and expose it as ctx_SAM3."""

    DESCRIPTION = (
        "Loads a SAM3 checkpoint with ComfyUI's native checkpoint loader and returns "
        "an rgthree-compatible context containing the SAM3 model, CLIP, and VAE."
    )
    OUTPUT_TOOLTIPS = (
        "Context dict containing SAM3 model, CLIP, VAE, and checkpoint name.",
        "SAM3 model loaded from the selected checkpoint.",
        "SAM3 CLIP loaded from the selected checkpoint.",
        "VAE loaded from the selected checkpoint.",
    )

    @classmethod
    def INPUT_TYPES(cls):
        checkpoint_names = _comfy_checkpoint_names()
        return {
            "required": {
                "ckpt_name": (checkpoint_names, {
                    "default": _preferred_checkpoint_default(checkpoint_names, "sam3.1_multiplex_fp16.safetensors"),
                    "tooltip": "SAM3 checkpoint to load, for example sam3.1_multiplex_fp16.safetensors.",
                }),
            },
        }

    RETURN_TYPES = ("RGTHREE_CONTEXT", "MODEL", "CLIP", "VAE")
    RETURN_NAMES = ("ctx_SAM3", "sam3_model", "sam3_clip", "sam3_vae")
    FUNCTION = "load"
    CATEGORY = "EasyUse Anima/Detailer"

    def load(self, ckpt_name):
        model, clip, vae = _load_checkpoint_with_comfy(str(ckpt_name))
        return (_sam3_context(model, clip, vae, str(ckpt_name)), model, clip, vae)


class _EasyUseAnimaImpactDetailerDelegate:
    """Internal Impact Pack DetailerForEach delegate used by SAM3 nodes."""

    DESCRIPTION = (
        "Internal Impact Pack DetailerForEach delegate used by EasyUse Anima SAM3 nodes."
    )
    OUTPUT_TOOLTIPS = (
        "Enhanced image returned by Impact Pack DetailerForEach.",
    )

    @classmethod
    def INPUT_TYPES(cls):
        max_resolution = _comfy_max_resolution()
        return {
            "required": {
                "image": ("IMAGE",),
                "segs": ("SEGS",),
                "model": ("MODEL", {
                    "tooltip": "Model passed through to Impact Pack DetailerForEach.",
                }),
                "clip": ("CLIP",),
                "vae": ("VAE",),
                "guide_size": ("FLOAT", {
                    "default": 512,
                    "min": 64,
                    "max": max_resolution,
                    "step": 8,
                    "tooltip": "Target guide size for the detailed crop.",
                }),
                "guide_size_for": ("BOOLEAN", {
                    "default": True,
                    "label_on": "bbox",
                    "label_off": "crop_region",
                    "tooltip": "Use the bbox or crop region as the guide-size basis.",
                }),
                "max_size": ("FLOAT", {
                    "default": 1024,
                    "min": 64,
                    "max": max_resolution,
                    "step": 8,
                    "tooltip": "Maximum crop size before sampling.",
                }),
                "seed": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 0xffffffffffffffff,
                }),
                "steps": ("INT", {
                    "default": 20,
                    "min": 1,
                    "max": 10000,
                }),
                "cfg": ("FLOAT", {
                    "default": 8.0,
                    "min": 0.0,
                    "max": 100.0,
                }),
                "sampler_name": (_comfy_sampler_names(),),
                "scheduler": (_impact_scheduler_names(),),
                "positive": ("CONDITIONING",),
                "negative": ("CONDITIONING",),
                "denoise": ("FLOAT", {
                    "default": 0.5,
                    "min": 0.0001,
                    "max": 1.0,
                    "step": 0.01,
                }),
                "feather": ("INT", {
                    "default": 5,
                    "min": 0,
                    "max": 100,
                    "step": 1,
                }),
                "noise_mask": ("BOOLEAN", {
                    "default": True,
                    "label_on": "enabled",
                    "label_off": "disabled",
                }),
                "force_inpaint": ("BOOLEAN", {
                    "default": True,
                    "label_on": "enabled",
                    "label_off": "disabled",
                }),
                "wildcard": ("STRING", {
                    "multiline": True,
                    "default": "",
                    "dynamicPrompts": False,
                }),
                "cycle": ("INT", {
                    "default": 1,
                    "min": 1,
                    "max": 10,
                    "step": 1,
                }),
                "alignment": (["impact", "none", "8", "16", "32", "64"], {
                    "default": "impact",
                    "tooltip": (
                        "Align the Impact detail crop sampling size upward. "
                        "Use 32 for ANIMA/Spectrum safety, or impact/none for pass-through."
                    ),
                }),
                "preserve_conditioning_metadata": ("BOOLEAN", {
                    "default": True,
                    "tooltip": (
                        "Reserved safety flag for the native ANIMA backend. "
                        "The current Impact backend passes conditioning through to Impact Pack."
                    ),
                }),
                "fail_on_unsupported_opt": ("BOOLEAN", {
                    "default": False,
                    "tooltip": "Raise an error instead of warning when a native-backend-only option is requested.",
                }),
            },
            "optional": {
                "detailer_hook": ("DETAILER_HOOK",),
                "inpaint_model": ("BOOLEAN", {
                    "default": False,
                    "label_on": "enabled",
                    "label_off": "disabled",
                }),
                "noise_mask_feather": ("INT", {
                    "default": 20,
                    "min": 0,
                    "max": 100,
                    "step": 1,
                }),
                "scheduler_func_opt": ("SCHEDULER_FUNC",),
                "tiled_encode": ("BOOLEAN", {
                    "default": False,
                    "label_on": "enabled",
                    "label_off": "disabled",
                }),
                "tiled_decode": ("BOOLEAN", {
                    "default": False,
                    "label_on": "enabled",
                    "label_off": "disabled",
                }),
            },
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("image",)
    FUNCTION = "doit"
    CATEGORY = "EasyUse Anima/Detailer"

    def doit(
        self,
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


class EasyUseAnimaSAM3Detailer:
    """Native SAM3 detection + Impact MaskToSEGS + ANIMA detailer."""

    DESCRIPTION = (
        "Runs native ComfyUI SAM3 text detection, converts the resulting mask to Impact Pack SEGS, "
        "then delegates detailing to Impact Pack DetailerForEach."
    )
    OUTPUT_TOOLTIPS = (
        "Detailed image. If disabled or no SEGS are detected, this is the original image.",
        "Impact-compatible SEGS generated from the SAM3 mask.",
        "SAM3 mask used to build SEGS.",
        "Original input image before detailing.",
    )

    @classmethod
    def INPUT_TYPES(cls):
        max_resolution = _comfy_max_resolution()
        detailer_inputs = _EasyUseAnimaImpactDetailerDelegate.INPUT_TYPES()
        required = {
            "enabled": ("BOOLEAN", {
                "default": True,
                "label_on": "enabled",
                "label_off": "bypass",
                "tooltip": "Disable to return the original image and an empty SEGS output.",
            }),
            "image": ("IMAGE",),
            "ctx_SAM3": ("RGTHREE_CONTEXT", {
                "tooltip": "ctx_SAM3 from the AiO SAM3 detailer path or a compatible rgthree context containing model and clip.",
            }),
            "detect_prompt": ("STRING", {
                "default": "face",
                "multiline": False,
                "dynamicPrompts": False,
                "tooltip": "SAM3 text target. Use comma-separated targets or target:count for per-target detection count.",
            }),
            "detect_count": ("INT", {
                "default": 1,
                "min": 1,
                "max": 64,
                "step": 1,
                "tooltip": "Maximum detections per target when detect_prompt does not already include :count.",
            }),
            "threshold": ("FLOAT", {
                "default": 0.5,
                "min": 0.0,
                "max": 1.0,
                "step": 0.01,
                "tooltip": "SAM3 detection threshold.",
            }),
            "refine_iterations": ("INT", {
                "default": 2,
                "min": 0,
                "max": 5,
                "step": 1,
                "tooltip": "SAM decoder refinement passes. 0 uses raw detector masks.",
            }),
            "individual_masks": ("BOOLEAN", {
                "default": False,
                "label_on": "enabled",
                "label_off": "combined",
                "tooltip": "Ask SAM3 for per-object masks. MaskToSEGS can still split a combined mask by contours.",
            }),
            "combined": ("BOOLEAN", {
                "default": False,
                "label_on": "combined",
                "label_off": "separate",
                "tooltip": "Impact MaskToSEGS combined option.",
            }),
            "crop_factor": ("FLOAT", {
                "default": 3.0,
                "min": 1.0,
                "max": 100.0,
                "step": 0.1,
                "tooltip": "Impact MaskToSEGS crop factor.",
            }),
            "bbox_fill": ("BOOLEAN", {
                "default": False,
                "label_on": "enabled",
                "label_off": "disabled",
                "tooltip": "Impact MaskToSEGS bbox_fill option.",
            }),
            "drop_size": ("INT", {
                "default": 10,
                "min": 1,
                "max": max_resolution,
                "step": 1,
                "tooltip": "Drop detected regions smaller than this size.",
            }),
            "contour_fill": ("BOOLEAN", {
                "default": False,
                "label_on": "enabled",
                "label_off": "disabled",
                "tooltip": "Impact MaskToSEGS contour_fill option.",
            }),
        }

        for key, value in detailer_inputs["required"].items():
            if key in ("image", "segs"):
                continue
            required[key] = value

        return {
            "required": required,
            "optional": detailer_inputs.get("optional", {}),
        }

    RETURN_TYPES = ("IMAGE", "SEGS", "MASK", "IMAGE")
    RETURN_NAMES = ("image", "segs", "mask", "raw_image")
    FUNCTION = "doit"
    CATEGORY = "EasyUse Anima/Detailer"

    def doit(
        self,
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

        detailed_image = _EasyUseAnimaImpactDetailerDelegate().doit(
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
