# -*- coding: utf-8 -*-
from __future__ import annotations

import importlib
import inspect
import json
import logging
import os
import random
import re
import sys
from math import gcd, isfinite, lcm, log
from typing import Any, Optional

try:
    from .anima_prompt import correct_prompt, load_knowledge_base
    from .anima_prompt.parser import parse_prompt
    from .settings import resolve_metadata_filter_words, resolve_naia_settings
    from .wildcard_engine import (
        MAX_SEED,
        SEED_CONTROL_FIXED,
        SEED_CONTROL_INCREMENT,
        SEED_CONTROL_MODES,
        SEED_CONTROL_RANDOMIZE,
        WILDCARD_MODE_FIXED,
        WILDCARD_MODE_LABELS,
        WILDCARD_MODE_POPULATE,
        WILDCARD_MODE_REPRODUCE,
        WILDCARD_MODE_SEQUENTIAL,
        expand_wildcards,
        has_wildcard_syntax,
        next_seed,
        normalize_seed,
        normalize_wildcard_mode,
        wildcard_sources_signature,
    )
except ImportError:  # allows simple local import tests outside ComfyUI's package loader
    from anima_prompt import correct_prompt, load_knowledge_base
    from anima_prompt.parser import parse_prompt
    from settings import resolve_metadata_filter_words, resolve_naia_settings
    from wildcard_engine import (
        MAX_SEED,
        SEED_CONTROL_FIXED,
        SEED_CONTROL_INCREMENT,
        SEED_CONTROL_MODES,
        SEED_CONTROL_RANDOMIZE,
        WILDCARD_MODE_FIXED,
        WILDCARD_MODE_LABELS,
        WILDCARD_MODE_POPULATE,
        WILDCARD_MODE_REPRODUCE,
        WILDCARD_MODE_SEQUENTIAL,
        expand_wildcards,
        has_wildcard_syntax,
        next_seed,
        normalize_seed,
        normalize_wildcard_mode,
        wildcard_sources_signature,
    )

logger = logging.getLogger("ComfyUI-EasyUseAnima")

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 7243
DEFAULT_QUALITY_TAGS = (
    "newest, masterpiece, best quality, score_8, score_7:, highres, absurdres, very aesthetic"
)
DEFAULT_TRAILING_QUALITY_TAGS = (
    "location, (A highly aesthetic Pixiv style illustration, clean composition, "
    "high-quality digital art, detailed background, sharp focus on facial expressions.:0.6)"
)
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
REGIONAL_FIELDS_WORKFLOW_PROPERTY = "easyuse_anima_regional_fields"
REGIONAL_CONFIG_WORKFLOW_PROPERTY = "easyuse_anima_regional_config"
REGIONAL_FIELD_TYPES = {"quality", "artist", "trigger", "general"}
REGIONAL_CONFIG_VERSION = 1
PROMPT_DATA_VERSION = 1
PROMPT_DATA_TYPE = "EASYUSE_ANIMA_PROMPT_DATA"
PROMPT_DATA_SCHEMA = "easyuse_anima_prompt_studio_advanced_v2"
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
ANIMA_MOD_GUIDANCE_MODE_FROM_PROMPT_DATA = "prompt_data"
ANIMA_MOD_GUIDANCE_MODE_ENABLED = "enabled"
ANIMA_MOD_GUIDANCE_MODE_DISABLED = "disabled"
ANIMA_MOD_GUIDANCE_MODES = (
    ANIMA_MOD_GUIDANCE_MODE_FROM_PROMPT_DATA,
    ANIMA_MOD_GUIDANCE_MODE_ENABLED,
    ANIMA_MOD_GUIDANCE_MODE_DISABLED,
)
ANIMA_MOD_GUIDANCE_PROFILE_OFF = "off"
ANIMA_MOD_GUIDANCE_DEFAULT_PROFILE = "step_i8_skip27"
ANIMA_MOD_GUIDANCE_PROFILES = (
    ANIMA_MOD_GUIDANCE_PROFILE_OFF,
    ANIMA_MOD_GUIDANCE_DEFAULT_PROFILE,
    "step_i14",
    "uniform_w3",
)
ARTIST_MIX_MODE_FROM_PROMPT_DATA = "prompt_data"
ARTIST_MIX_MODE_OFF = "off"
ARTIST_MIX_MODE_PROMPT = "prompt"
ARTIST_MIX_MODE_AVERAGE = "average"
ARTIST_MIX_MODE_DELTA_RMS = "delta_rms"
ARTIST_MIX_MODE_HYBRID = "hybrid"
ARTIST_MIX_MODE_CLUSTERED = "clustered"
ARTIST_MIX_MODE_EXACT = "exact"
ARTIST_MIX_MODE_COMPOSITE_EXACT = "composite_exact"
ARTIST_MIX_MODE_LATE_EXACT = "late_exact"
ARTIST_MIX_MODE_AVERAGE_LATE_EXACT = "average_late_exact"
ARTIST_MIX_MODE_SCHEDULED_AVERAGE = "scheduled_average"
ARTIST_MIX_MODES = (
    ARTIST_MIX_MODE_PROMPT,
    ARTIST_MIX_MODE_AVERAGE,
    ARTIST_MIX_MODE_DELTA_RMS,
    ARTIST_MIX_MODE_HYBRID,
    ARTIST_MIX_MODE_CLUSTERED,
    ARTIST_MIX_MODE_EXACT,
    ARTIST_MIX_MODE_COMPOSITE_EXACT,
    ARTIST_MIX_MODE_LATE_EXACT,
    ARTIST_MIX_MODE_AVERAGE_LATE_EXACT,
    ARTIST_MIX_MODE_SCHEDULED_AVERAGE,
)
ARTIST_MIX_INPUT_MODES = (
    ARTIST_MIX_MODE_FROM_PROMPT_DATA,
    ARTIST_MIX_MODE_OFF,
    *ARTIST_MIX_MODES,
)
ARTIST_MIX_STUDIO_MODES = (
    ARTIST_MIX_MODE_OFF,
    ARTIST_MIX_MODE_AVERAGE,
    ARTIST_MIX_MODE_DELTA_RMS,
    ARTIST_MIX_MODE_HYBRID,
    ARTIST_MIX_MODE_CLUSTERED,
    ARTIST_MIX_MODE_EXACT,
    ARTIST_MIX_MODE_COMPOSITE_EXACT,
    ARTIST_MIX_MODE_LATE_EXACT,
    ARTIST_MIX_MODE_AVERAGE_LATE_EXACT,
    ARTIST_MIX_MODE_SCHEDULED_AVERAGE,
)
ARTIST_MIX_DEFAULT_START_PERCENT = 0.5
ARTIST_MIX_DEFAULT_STRENGTH_SCALE = 1.0
ARTIST_MIX_DEFAULT_STYLE_GAIN = 1.35
ARTIST_MIX_DEFAULT_RMS_SCALE_CAP = 2.0
ARTIST_MIX_DEFAULT_EXACT_TOP_K = 4
ARTIST_MIX_DEFAULT_CLUSTER_COUNT = 4
ARTIST_MIX_DEFAULT_DOMINANT_ISOLATION = True
ARTIST_MIX_DEFAULT_DOMINANT_THRESHOLD = 0.25
ARTIST_MIX_CONTROL_KEY = "anima_prompt_artist_mix_control"
ARTIST_MIX_EXACT_KEY = "anima_prompt_artist_mix_exact"
ARTIST_MIX_SCHEDULE_KEY = "anima_prompt_artist_mix_schedule"
_SPECTRUM_ANIMA_MOD_GUIDANCE_OLD_SIGNATURE_WARNED: set[str] = set()
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
            "enabled": True,
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
ARTIST_TAG_POSITION_CORRECT = "correct"
ARTIST_TAG_POSITION_FRONT = "front"
ARTIST_TAG_POSITION_BACK = "back"
ARTIST_TAG_POSITION_MODES = (
    ARTIST_TAG_POSITION_CORRECT,
    ARTIST_TAG_POSITION_FRONT,
    ARTIST_TAG_POSITION_BACK,
)
ARTIST_MIX_MODE_DESCRIPTIONS = {
    ARTIST_MIX_MODE_OFF: "Cost: 1 positive branch. Keeps artist-field text inline in the positive prompt.",
    ARTIST_MIX_MODE_PROMPT: "Cost: 1 positive branch. Keeps artist-field text inline in the positive prompt.",
    ARTIST_MIX_MODE_AVERAGE: "Cost: 1 positive branch. Weighted average of artist conditionings; fastest stable mix.",
    ARTIST_MIX_MODE_DELTA_RMS: (
        "Cost: 1 positive branch. Mixes artist deltas from the base prompt and restores RMS style energy; "
        "usually stronger than average."
    ),
    ARTIST_MIX_MODE_HYBRID: (
        "Cost: top_k + 1 positive branches. Keeps strongest artists as exact branches and compresses the tail "
        "with delta_rms; recommended balance."
    ),
    ARTIST_MIX_MODE_CLUSTERED: (
        "Cost: about cluster_count plus dominant artists. Groups similar artist deltas and compresses each "
        "cluster; useful for many artists."
    ),
    ARTIST_MIX_MODE_EXACT: "Cost: N positive branches. Most faithful artist-specific model output mix.",
    ARTIST_MIX_MODE_COMPOSITE_EXACT: (
        "Cost: N + 1 positive branches. Adds one composite prompt branch plus exact artist branches."
    ),
    ARTIST_MIX_MODE_LATE_EXACT: "Cost: base + N late exact branches. Applies exact mixing only after start.",
    ARTIST_MIX_MODE_AVERAGE_LATE_EXACT: (
        "Cost: 1 average branch plus N late exact branches. Fast early mix, exact late refinement."
    ),
    ARTIST_MIX_MODE_SCHEDULED_AVERAGE: (
        "Cost: scheduled average branches. Changes artist weights across timestep ranges."
    ),
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
NAIA_REQUEST_TIMEOUT = 30.0
HTTP_TIMEOUT = NAIA_REQUEST_TIMEOUT + 5.0

NAI_1MP = 1024 * 1024
LATENT_ALIGN = 8
IMAGE_UPSCALE_METHODS = ["nearest-exact", "bilinear", "area", "bicubic", "lanczos"]
IMAGE_SCALE_MULTIPLES = ["8", "16", "32", "64"]
ADVANCED_RESOLUTION_BUCKETS = {
    "512": (
        (256, 1024), (1024, 256),
        (288, 896), (896, 288),
        (384, 672), (672, 384),
        (512, 512),
        (448, 576), (576, 448),
    ),
    "768": (
        (384, 1440), (1440, 384),
        (480, 1152), (1152, 480),
        (576, 960), (960, 576),
        (640, 864), (864, 640),
        (768, 768),
    ),
    "896": (
        (448, 1728), (1728, 448),
        (480, 1600), (1600, 480),
        (576, 1344), (1344, 576),
        (672, 1152), (1152, 672),
        (800, 960), (960, 800),
        (896, 896),
    ),
    "1024": (
        (512, 2016), (2016, 512),
        (576, 1792), (1792, 576),
        (672, 1536), (1536, 672),
        (672, 1600), (1600, 672),
        (768, 1344), (1344, 768),
        (800, 1344), (1344, 800),
        (896, 1152), (1152, 896),
        (960, 1120), (1120, 960),
        (1024, 1024),
    ),
    "1280": (
        (672, 2400), (2400, 672),
        (800, 2016), (2016, 800),
        (1024, 1536), (1536, 1024),
        (1024, 1600), (1600, 1024),
        (1120, 1440), (1440, 1120),
        (1280, 1280),
    ),
    "1536": (
        (1440, 1536), (1536, 1440),
        (1280, 1728), (1728, 1280),
        (1152, 1920), (1920, 1152),
        (1024, 2176), (2176, 1024),
        (960, 2304), (2304, 960),
        (864, 2560), (2560, 864),
        (768, 2880), (2880, 768),
        (1536, 1536),
    ),
}
CUSTOM_ADVANCED_RESOLUTION_BUCKET = "Custom"
NAIA_ADVANCED_RESOLUTION_BUCKET = "NAIA"
DEFAULT_ADVANCED_RESOLUTION_BUCKET = "1024"
DEFAULT_ADVANCED_RESOLUTION_SIZE = "1024 * 1024 (1:1)"
NAIA_RESOLUTION_MODE_SCALE = "scale"
NAIA_RESOLUTION_MODE_BUCKET = "bucket"

PREPROCESSING_KEYS = [
    "remove_author",
    "remove_work_title",
    "remove_character_name",
    "remove_character_features",
    "remove_clothes",
    "remove_color",
    "remove_location_and_background_color",
    "remove_expression",
    "remove_pose_action",
    "remove_meta_tags",
    "remove_object_tags",
    "remove_noise_tags",
    "e621_auto_boost",
    "danbooru_auto_weight",
    "tag_implication_compression",
]
PP_STATE_CHOICES = ["skip", "on", "off"]

_HASH_COMMENT_RE = re.compile(r"^[ \t]*#[^\n]*", re.MULTILINE)
_MULTI_COMMA_RE = re.compile(r"(\s*,){2,}")
_INLINE_SPACE_RE = re.compile(r"[ \t]+")
_WEIGHTED_TOKEN_RE = re.compile(r"^\(([^(),]+):[-+]?\d+(?:\.\d+)?\)$")
_WEIGHTED_ARTIST_RE = re.compile(
    r"^\(\s*(?P<tag>.*?)\s*:\s*(?P<weight>[+-]?(?:\d+(?:\.\d*)?|\.\d+))\s*\)$"
)
_SECTION_SEPARATOR_RE = re.compile(r"^\s*-{6,}\s*$", re.MULTILINE)
_RESOLUTION_LABEL_RE = re.compile(r"(\d+)\s*(?:\*|x|×)\s*(\d+)")
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


def _single_value(value):
    if isinstance(value, (list, tuple)):
        if not value:
            return None
        return value[0]
    return value


def _as_bool(value, default: bool = False) -> bool:
    value = _single_value(value)
    if value is None:
        return default
    if isinstance(value, str):
        return value.strip().lower() in ("true", "1", "yes", "on", "enable", "enabled")
    return bool(value)


def _as_int(value, default: int = 0) -> int:
    value = _single_value(value)
    if value is None:
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _normalize_aio_seed(value, default: int = AIO_SPECIAL_SEED_RANDOM) -> int:
    return max(AIO_SPECIAL_SEED_DECREMENT, min(MAX_SEED, _as_int(value, default)))


def _new_aio_random_seed() -> int:
    return random.randint(0, MAX_SEED)


def _resolve_aio_runtime_seed(value) -> int:
    seed = _normalize_aio_seed(value)
    if seed in AIO_SPECIAL_SEEDS:
        return _new_aio_random_seed()
    return max(0, min(MAX_SEED, seed))


def _as_float(value, default: float = 0.0) -> float:
    value = _single_value(value)
    if value is None:
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _ratio_label(width: int, height: int) -> str:
    divisor = gcd(max(1, int(width)), max(1, int(height)))
    return f"{int(width) // divisor}:{int(height) // divisor}"


def _resolution_label(width: int, height: int) -> str:
    return f"{int(width)} * {int(height)} ({_ratio_label(width, height)})"


def _sorted_resolution_options(bucket: str) -> list[tuple[int, int]]:
    values = ADVANCED_RESOLUTION_BUCKETS.get(bucket) or ADVANCED_RESOLUTION_BUCKETS[DEFAULT_ADVANCED_RESOLUTION_BUCKET]
    return sorted(values, key=lambda item: (item[0] / item[1], item[0], item[1]))


def _normalize_resolution_bucket(value) -> str:
    value = str(_single_value(value) or "").strip()
    if value in {CUSTOM_ADVANCED_RESOLUTION_BUCKET, NAIA_ADVANCED_RESOLUTION_BUCKET}:
        return value
    return value if value in ADVANCED_RESOLUTION_BUCKETS else DEFAULT_ADVANCED_RESOLUTION_BUCKET


def _snap_resolution_32(value, default: int = 1024) -> int:
    raw = _as_int(value, default)
    if raw <= 0:
        raw = default
    return max(32, int(round(raw / 32)) * 32)


def _resolve_naia_resolution_scale(naia_settings: dict | None) -> float:
    value = _as_float((naia_settings or {}).get("resolution_scale", 1.0), 1.0)
    return max(0.25, min(4.0, value))


def _resolve_naia_resolution_max_long_edge(naia_settings: dict | None) -> int:
    value = _as_int((naia_settings or {}).get("resolution_max_long_edge", 0), 0)
    if value <= 0:
        return 0
    return max(32, min(16384, value))


def _resolve_naia_resolution_mode(naia_settings: dict | None) -> str:
    value = str(
        _single_value((naia_settings or {}).get("resolution_mode", NAIA_RESOLUTION_MODE_SCALE)) or ""
    ).strip().lower()
    if value == "bucket_fit":
        return NAIA_RESOLUTION_MODE_BUCKET
    return value if value in {NAIA_RESOLUTION_MODE_SCALE, NAIA_RESOLUTION_MODE_BUCKET} else NAIA_RESOLUTION_MODE_SCALE


def _resolve_naia_resolution_bucket(naia_settings: dict | None) -> str:
    bucket = _normalize_resolution_bucket((naia_settings or {}).get("resolution_bucket", DEFAULT_ADVANCED_RESOLUTION_BUCKET))
    return bucket if bucket in ADVANCED_RESOLUTION_BUCKETS else DEFAULT_ADVANCED_RESOLUTION_BUCKET


def _snap_scaled_resolution_32(value: float, max_value: int = 0, default: int = 1024) -> int:
    raw = _as_float(value, float(default))
    if raw <= 0:
        raw = float(default)
    snapped = max(32, int(round(raw / 32)) * 32)
    if max_value > 0 and snapped > max_value:
        snapped = max(32, int(max_value // 32) * 32)
    return snapped


def _scale_naia_resolution(
    width: int,
    height: int,
    naia_settings: dict | None,
) -> tuple[int, int]:
    scale = _resolve_naia_resolution_scale(naia_settings)
    max_long_edge = _resolve_naia_resolution_max_long_edge(naia_settings)
    scaled_width = max(1.0, _as_float(width, 1024.0) * scale)
    scaled_height = max(1.0, _as_float(height, 1024.0) * scale)

    if max_long_edge > 0:
        long_edge = max(scaled_width, scaled_height)
        if long_edge > max_long_edge:
            ratio = max_long_edge / long_edge
            scaled_width *= ratio
            scaled_height *= ratio

    return (
        _snap_scaled_resolution_32(scaled_width, max_long_edge, 1024),
        _snap_scaled_resolution_32(scaled_height, max_long_edge, 1024),
    )


def _fit_naia_resolution_to_bucket(
    width: int,
    height: int,
    naia_settings: dict | None,
) -> tuple[int, int]:
    bucket = _resolve_naia_resolution_bucket(naia_settings)
    source_width = max(1.0, _as_float(width, 1024.0))
    source_height = max(1.0, _as_float(height, 1024.0))
    source_ratio = source_width / source_height
    options = ADVANCED_RESOLUTION_BUCKETS.get(bucket) or ADVANCED_RESOLUTION_BUCKETS[DEFAULT_ADVANCED_RESOLUTION_BUCKET]

    return min(
        options,
        key=lambda item: abs(log((item[0] / item[1]) / source_ratio)),
    )


def _resolve_naia_resolution(
    width: int,
    height: int,
    naia_settings: dict | None,
) -> tuple[int, int]:
    if _resolve_naia_resolution_mode(naia_settings) == NAIA_RESOLUTION_MODE_BUCKET:
        return _fit_naia_resolution_to_bucket(width, height, naia_settings)
    return _scale_naia_resolution(width, height, naia_settings)


def _advanced_resolution_from_selection(
    bucket,
    size,
    custom_width: int | str = 1024,
    custom_height: int | str = 1024,
) -> tuple[int, int]:
    bucket_name = _normalize_resolution_bucket(bucket)
    if bucket_name in {CUSTOM_ADVANCED_RESOLUTION_BUCKET, NAIA_ADVANCED_RESOLUTION_BUCKET}:
        return (
            _snap_resolution_32(custom_width, 1024),
            _snap_resolution_32(custom_height, 1024),
        )
    raw_size = str(_single_value(size) or "").strip()
    match = _RESOLUTION_LABEL_RE.search(raw_size)
    if match:
        width, height = int(match.group(1)), int(match.group(2))
        if (width, height) in ADVANCED_RESOLUTION_BUCKETS.get(bucket_name, ()):
            return width, height
    default_width, default_height = 1024, 1024
    if (default_width, default_height) in ADVANCED_RESOLUTION_BUCKETS.get(bucket_name, ()):
        return default_width, default_height
    return _sorted_resolution_options(bucket_name)[0]


def _clean_prompt(value: str) -> str:
    if not value:
        return value
    value = _HASH_COMMENT_RE.sub("", value)
    value = _MULTI_COMMA_RE.sub(",", value)
    return value.strip(" ,\n\t")


def _stable_change_key(payload: dict) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _json_clone(value):
    return json.loads(json.dumps(value, ensure_ascii=False))


def _json_object(value) -> dict[str, Any]:
    if isinstance(value, dict):
        return dict(value)
    if isinstance(value, str):
        try:
            parsed = json.loads(value or "{}")
        except json.JSONDecodeError:
            parsed = {}
        if isinstance(parsed, dict):
            return parsed
    return {}


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


def _choice(value, choices, default: str) -> str:
    choices = tuple(choices or ())
    value = str(_single_value(value) or "").strip()
    if value in choices:
        return value
    if default in choices:
        return default
    return choices[0] if choices else default


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

    for key in ("highres", "detailer", "save"):
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
    detailer = settings["detailer"]
    sam3 = detailer.setdefault("sam3", {})
    if not isinstance(sam3, dict):
        sam3 = {}
        detailer["sam3"] = sam3
    order = detailer.get("order")
    if not isinstance(order, list):
        order = AIO_GENERATION_DEFAULT_SETTINGS["detailer"]["order"]
    normalized_order = []
    for name in order:
        text = str(name or "").strip()
        if text in ("face", "eye") and text not in normalized_order:
            normalized_order.append(text)
    for name in ("face", "eye"):
        if name not in normalized_order:
            normalized_order.append(name)
    detailer["order"] = normalized_order
    sam3["context"] = _choice(sam3.get("context"), ("load_checkpoint",), "load_checkpoint")
    sam3["checkpoint"] = str(sam3.get("checkpoint") or "sam3.1_multiplex_fp16.safetensors")
    for target_name, defaults in (
        ("face", AIO_GENERATION_DEFAULT_SETTINGS["detailer"]["face"]),
        ("eye", AIO_GENERATION_DEFAULT_SETTINGS["detailer"]["eye"]),
    ):
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
        result = get_hash(username, model_name, version)
        hash_value = _single_value(result)
        hash_text = str(hash_value or "").strip()
        if (
            not hash_text
            or hash_text.lower().startswith("error:")
            or hash_text.lower().startswith("no ")
        ):
            raise RuntimeError(
                "[EasyUseAnima] Civitai Hash Fetcher failed for "
                f"'{username}/{model_name}'"
                + (f" version '{version}'" if version else "")
                + f": {hash_text or 'empty hash'}"
            )
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

        return int(getattr(comfy_nodes, "MAX_RESOLUTION", 16384))
    except Exception:
        return 16384


def _comfy_sampler_names() -> list[str]:
    try:
        import comfy.samplers  # type: ignore

        return list(comfy.samplers.KSampler.SAMPLERS)
    except Exception:
        return [
            "er_sde",
            "euler",
            "euler_ancestral",
            "heun",
            "dpm_2",
            "dpm_2_ancestral",
            "dpmpp_2m",
            "dpmpp_sde",
            "ddim",
        ]


def _comfy_scheduler_names() -> list[str]:
    try:
        import comfy.samplers  # type: ignore

        return list(comfy.samplers.KSampler.SCHEDULERS)
    except Exception:
        return [
            "simple",
            "sgm_uniform",
            "karras",
            "exponential",
            "ddim_uniform",
            "beta",
            "normal",
            "linear_quadratic",
            "kl_optimal",
            "AYS SDXL",
            "AYS SD1",
            "AYS SVD",
            "GITS[coeff=1.2]",
            "LTXV[default]",
            "OSS FLUX",
            "OSS Wan",
            "OSS Chroma",
        ]


def _comfy_checkpoint_names() -> list[str]:
    try:
        import folder_paths  # type: ignore

        names = [str(name) for name in folder_paths.get_filename_list("checkpoints")]
        if names:
            return names
    except Exception:
        pass
    return ["sam3.1_multiplex_fp16.safetensors"]


def _folder_path_names(folder_name: str, fallback: list[str]) -> list[str]:
    try:
        import folder_paths  # type: ignore

        names = [str(name) for name in folder_paths.get_filename_list(folder_name)]
        if names:
            return names
    except Exception:
        pass
    return list(fallback)


def _comfy_diffusion_model_names() -> list[str]:
    return _folder_path_names("diffusion_models", list(ANIMA_DEFAULT_DIFFUSION_MODEL_CANDIDATES))


def _comfy_text_encoder_names() -> list[str]:
    return _folder_path_names("text_encoders", list(ANIMA_DEFAULT_CLIP_CANDIDATES))


def _comfy_vae_names() -> list[str]:
    loader_cls = _find_comfy_node_class("VAELoader")
    if loader_cls is not None:
        try:
            required = loader_cls.INPUT_TYPES().get("required", {})
            names = [str(name) for name in required.get("vae_name", ([],))[0]]
            if names:
                return names
        except Exception:
            pass
    return _folder_path_names("vae", list(ANIMA_DEFAULT_VAE_CANDIDATES))


def _comfy_clip_loader_types() -> list[str]:
    loader_cls = _find_comfy_node_class("CLIPLoader")
    if loader_cls is not None:
        try:
            required = loader_cls.INPUT_TYPES().get("required", {})
            names = [str(name) for name in required.get("type", ([],))[0]]
            if names:
                return names
        except Exception:
            pass
    return list(ANIMA_CLIP_TYPES)


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
    for module_name in ("impact.core", "modules.impact.core"):
        try:
            return importlib.import_module(module_name)
        except Exception:
            continue
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

    for module_name in ("impact.impact_pack", "modules.impact.impact_pack"):
        try:
            module = importlib.import_module(module_name)
        except Exception:
            continue
        cls = getattr(module, "DetailerForEach", None)
        if cls is not None:
            return cls

    raise RuntimeError(
        "[EasyUseAnima] SAM3 Detailer requires ComfyUI Impact Pack's DetailerForEach. "
        "Install/enable ComfyUI-Impact-Pack, then restart ComfyUI."
    )


def _find_comfy_node_class(node_id: str):
    try:
        import nodes as comfy_nodes  # type: ignore

        mappings = getattr(comfy_nodes, "NODE_CLASS_MAPPINGS", {})
        cls = mappings.get(node_id)
        if cls is not None:
            return cls
        cls = getattr(comfy_nodes, node_id, None)
        if cls is not None:
            return cls
    except Exception:
        pass
    for module in list(sys.modules.values()):
        mappings = getattr(module, "NODE_CLASS_MAPPINGS", None)
        if isinstance(mappings, dict):
            cls = mappings.get(node_id)
            if cls is not None:
                return cls
    return None


def _require_custom_node_class(node_id: str, node_pack: str, install_hint: str):
    cls = _find_comfy_node_class(node_id)
    if cls is not None:
        return cls
    raise RuntimeError(
        f"[EasyUseAnima] Missing required custom node '{node_id}'. "
        f"Install/enable {node_pack}, then restart ComfyUI. {install_hint}"
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
    try:
        module = importlib.import_module("comfy_extras.nodes_sam3")
        cls = getattr(module, "SAM3_Detect", None)
        if cls is not None:
            return cls
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

    for module_name in ("impact.segs_nodes", "modules.impact.segs_nodes", "impact.impact_pack", "modules.impact.impact_pack"):
        try:
            module = importlib.import_module(module_name)
        except Exception:
            continue
        cls = getattr(module, "MaskToSEGS", None)
        if cls is not None:
            return cls

    raise RuntimeError(
        "[EasyUseAnima] Anima SAM3 Detailer requires ComfyUI Impact Pack's MaskToSEGS. "
        "Install/enable ComfyUI-Impact-Pack, then restart ComfyUI."
    )


def _node_output_tuple(result) -> tuple:
    value = getattr(result, "result", None)
    if value is not None:
        return tuple(value)
    if isinstance(result, dict) and "result" in result:
        return tuple(result["result"])
    if isinstance(result, tuple):
        return result
    return (result,)


def _find_loaded_node_class(node_id: str):
    cls = _find_comfy_node_class(node_id)
    if cls is not None:
        return cls

    for module in list(sys.modules.values()):
        mappings = getattr(module, "NODE_CLASS_MAPPINGS", None)
        if isinstance(mappings, dict):
            cls = mappings.get(node_id)
            if cls is not None:
                return cls
    return None


def _find_spectrum_anima_mod_guidance_class():
    cls = _find_loaded_node_class("AnimaModGuidance")
    if cls is not None:
        return cls
    raise RuntimeError(
        "[EasyUseAnima] Anima Prompt Data Conditioning requires "
        "comfyui-spectrum-ksampler's AnimaModGuidance node. "
        "Install/enable comfyui-spectrum-ksampler, then restart ComfyUI."
    )


def _resolve_anima_mod_guidance_enabled(prompt_data_enabled: bool, mode: str) -> bool:
    mode = str(mode or ANIMA_MOD_GUIDANCE_MODE_FROM_PROMPT_DATA)
    if mode == ANIMA_MOD_GUIDANCE_MODE_ENABLED:
        return True
    if mode == ANIMA_MOD_GUIDANCE_MODE_DISABLED:
        return False
    return bool(prompt_data_enabled)


def _normalize_anima_mod_guidance_profile(profile: str) -> str:
    profile = str(profile or ANIMA_MOD_GUIDANCE_DEFAULT_PROFILE)
    if profile not in ANIMA_MOD_GUIDANCE_PROFILES:
        return ANIMA_MOD_GUIDANCE_DEFAULT_PROFILE
    return profile


def _warn_old_spectrum_anima_mod_guidance_once(patcher_cls) -> None:
    class_name = getattr(patcher_cls, "__qualname__", getattr(patcher_cls, "__name__", "AnimaModGuidance"))
    module_name = getattr(patcher_cls, "__module__", "")
    warning_key = f"{module_name}.{class_name}"
    if warning_key in _SPECTRUM_ANIMA_MOD_GUIDANCE_OLD_SIGNATURE_WARNED:
        return
    _SPECTRUM_ANIMA_MOD_GUIDANCE_OLD_SIGNATURE_WARNED.add(warning_key)
    logger.warning(
        "[EasyUseAnima] Installed comfyui-spectrum-ksampler AnimaModGuidance "
        "uses an old patch() signature without separate negative quality-tag "
        "support. Generation will continue, but negative Mod Guidance quality "
        "tags are ignored by the model patch. Update comfyui-spectrum-ksampler "
        "to enable separate negative quality tags."
    )


def _apply_spectrum_anima_mod_guidance(
    model,
    clip,
    positive,
    negative,
    quality_tags: str,
    quality_neg: str,
    mod_w_profile: str,
):
    patcher_cls = _find_spectrum_anima_mod_guidance_class()
    patcher = patcher_cls()
    patch = getattr(patcher, "patch", None)
    if patch is None:
        raise RuntimeError(
            "[EasyUseAnima] comfyui-spectrum-ksampler AnimaModGuidance does not expose patch()."
        )
    quality_tags = str(quality_tags or "")
    quality_neg = str(quality_neg or "")
    mod_w_profile = str(mod_w_profile or ANIMA_MOD_GUIDANCE_DEFAULT_PROFILE)
    patch_parameters = inspect.signature(patch).parameters
    patch_parameter_values = list(patch_parameters.values())
    patch_positional_count = sum(
        1 for param in patch_parameter_values
        if param.kind in (inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD)
    )
    patch_accepts_quality_neg = (
        any(name in patch_parameters for name in ("quality_neg", "quality_negative", "negative_quality_tags"))
        or any(param.kind == inspect.Parameter.VAR_POSITIONAL for param in patch_parameter_values)
        or patch_positional_count >= 7
    )
    if patch_accepts_quality_neg:
        result = patch(
            model,
            clip,
            quality_tags,
            quality_neg,
            mod_w_profile,
            positive,
            negative,
        )
    else:
        _warn_old_spectrum_anima_mod_guidance_once(patcher_cls)
        result = patch(
            model,
            clip,
            quality_tags,
            mod_w_profile,
            positive,
            negative,
        )
    values = _node_output_tuple(result)
    if not values:
        raise RuntimeError("[EasyUseAnima] AnimaModGuidance returned no MODEL.")
    return values[0]


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
    patch_cls = _require_custom_node_class(
        "DiTSpectrumPatchAdvanced",
        "ComfyUI-Spectrum-KSampler",
        "Repository: https://github.com/blepping/ComfyUI-Spectrum-KSampler",
    )
    values = _node_output_tuple(
        patch_cls().patch(
            model,
            _as_int(sampler_settings.get("steps"), 28),
            _as_float(spectrum.get("window_size"), 2.0),
            _as_float(spectrum.get("flex_window"), 0.25),
            _as_int(spectrum.get("warmup_steps"), 6),
            _as_int(spectrum.get("tail_actual_steps"), 3),
            _as_float(spectrum.get("blend_w"), 0.3),
            _as_int(spectrum.get("cheby_degree"), 3),
            _as_float(spectrum.get("ridge_lambda"), 0.1),
            _as_int(spectrum.get("history_size"), 100),
            True,
            _as_bool(spectrum.get("one_sampler_only"), False),
            _as_bool(spectrum.get("verbose"), False),
            str(spectrum.get("compat_policy") or "conservative"),
        )
    )
    if not values:
        raise RuntimeError("[EasyUseAnima] DiTSpectrumPatchAdvanced returned no MODEL.")
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
    values = _node_output_tuple(
        sampler_cls().sample(
            model,
            clip,
            _resolve_aio_runtime_seed(sampler_settings.get("seed")),
            _as_int(sampler_settings.get("steps"), 28),
            _as_float(sampler_settings.get("cfg"), 5.0),
            str(sampler_settings.get("sampler_name") or "euler_ancestral"),
            str(sampler_settings.get("scheduler") or "normal"),
            positive,
            negative,
            latent_image,
            str(advanced_mod.get("adapter") or "(auto-download default)"),
            str(quality_tags or advanced_mod.get("quality_tags") or ""),
            mod_w,
            quality_neg=str(quality_neg or ""),
            mod_start_layer=_as_int(advanced_mod.get("mod_start_layer"), 8),
            mod_end_layer=_as_int(advanced_mod.get("mod_end_layer"), 27),
            mod_taper=_as_int(advanced_mod.get("mod_taper"), 0),
            mod_taper_scale=_as_float(advanced_mod.get("mod_taper_scale"), 0.25),
            mod_final_w=_as_float(advanced_mod.get("mod_final_w"), 0.0),
            denoise=_as_float(sampler_settings.get("denoise"), 1.0),
            window_size=_as_float(spectrum.get("window_size"), 2.0),
            flex_window=_as_float(spectrum.get("flex_window"), 0.25),
            warmup_steps=_as_int(spectrum.get("warmup_steps"), 6),
            blend_w=_as_float(spectrum.get("blend_w"), 0.3),
            cheby_degree=_as_int(spectrum.get("cheby_degree"), 3),
            ridge_lambda=_as_float(spectrum.get("ridge_lambda"), 0.1),
            dcw_mode=str(corrections.get("dcw_mode") or "off") if use_corrections else "off",
            dcw_lambda=_as_float(corrections.get("dcw_lambda"), 0.01) if use_corrections else 0.0,
            dcw_band_mask=str(corrections.get("dcw_band_mask") or "LL") if use_corrections else "LL",
            dcw_calibrator=str(corrections.get("dcw_calibrator") or "(auto-download default)"),
            cfgpp_lambda=_as_float(corrections.get("cfgpp_lambda"), 0.0) if use_cfgpp else 0.0,
            fsg=use_fsg,
            fsg_band_lo=_as_float(corrections.get("fsg_band_lo"), 0.59) if use_fsg else 0.59,
            fsg_band_hi=_as_float(corrections.get("fsg_band_hi"), 0.75) if use_fsg else 0.75,
            fsg_k=_as_int(corrections.get("fsg_k"), 3) if use_fsg else 3,
            fsg_d_sigma=_as_float(corrections.get("fsg_d_sigma"), 0.1) if use_fsg else 0.1,
            fsg_gamma=_as_float(corrections.get("fsg_gamma"), 0.0) if use_fsg else 0.0,
            adaptive_smc_alpha=_as_float(corrections.get("adaptive_smc_alpha"), 0.0) if use_smc else 0.0,
            smc_cfg_lambda=_as_float(corrections.get("smc_cfg_lambda"), 5.0) if use_smc else 0.0,
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
    values = _node_output_tuple(
        spd_cls().sample(
            model,
            _resolve_aio_runtime_seed(sampler_settings.get("seed")),
            _as_int(sampler_settings.get("steps"), 28),
            _as_float(sampler_settings.get("cfg"), 5.0),
            sampler_name,
            str(sampler_settings.get("scheduler") or "simple"),
            positive,
            negative,
            latent_image,
            str(spd.get("split_mode") or "single"),
            _as_float(spd.get("scale"), 0.5),
            _as_float(spd.get("sigma"), 0.7),
            denoise=_as_float(sampler_settings.get("denoise"), 1.0),
            adaptive_smc_alpha=_as_float(spd.get("adaptive_smc_alpha"), 0.0),
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


def _aio_stage_sampler_settings(
    base_sampler: dict[str, Any],
    stage_settings: dict[str, Any],
    *,
    scheduler_default: str,
) -> dict[str, Any]:
    inherit_sampler = _as_bool(stage_settings.get("inherit_sampler_settings"), False)
    return {
        "backend": "comfy_ksampler",
        "seed": _resolve_aio_runtime_seed(base_sampler.get("seed")),
        "seed_after_generate": SEED_CONTROL_FIXED,
        "steps": _as_int(stage_settings.get("steps"), _as_int(base_sampler.get("steps"), 28)),
        "cfg": (
            _as_float(base_sampler.get("cfg"), 5.0)
            if inherit_sampler
            else _as_float(stage_settings.get("cfg"), _as_float(base_sampler.get("cfg"), 5.0))
        ),
        "sampler_name": (
            str(base_sampler.get("sampler_name") or "euler")
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
    }


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
) -> tuple[Any, Any, int, int, dict[str, Any]]:
    if not _as_bool(highres_settings.get("enabled"), False):
        return base_latent, image, int(base_width), int(base_height), {"enabled": False}

    scaled_image, width, height, applied_scale = EasyUseAnimaImageScaleByMultiple().upscale(
        image,
        highres_settings.get("scale_by", 1.25),
        highres_settings.get("upscale_method", "bicubic"),
        highres_settings.get("multiple", "32"),
        highres_settings.get("max_long_edge", 2560),
    )
    latent_image = _encode_image_with_comfy_vae(vae, scaled_image)
    stage_sampler = _aio_stage_sampler_settings(
        sampler_settings,
        highres_settings,
        scheduler_default="simple",
    )
    stage_model = _apply_aio_spectrum_model_patches_for_comfy_sampler(
        model,
        clip,
        positive,
        stage_sampler,
    )
    try:
        latent = _sample_latent_with_comfy(
            stage_model,
            stage_sampler["seed"],
            stage_sampler["steps"],
            stage_sampler["cfg"],
            stage_sampler["sampler_name"],
            stage_sampler["scheduler"],
            positive,
            negative,
            latent_image,
            stage_sampler["denoise"],
        )
    finally:
        _cleanup_aio_ephemeral_model(stage_model, model)
    decoded = _decode_latent_with_comfy(vae, latent)
    return latent, decoded, int(width), int(height), {
        "enabled": True,
        "width": int(width),
        "height": int(height),
        "applied_scale": float(applied_scale),
        "sampler": _prompt_data_json_safe(stage_sampler),
    }


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
    enabled_targets = [
        name
        for name in ("face", "eye")
        if isinstance(detailer_settings.get(name), dict)
        and _as_bool(detailer_settings[name].get("enabled"), False)
    ]
    if not enabled_targets:
        return image, {"enabled": False, "reason": "no target enabled"}

    sam3_context = _load_aio_sam3_context(detailer_settings)
    output = image
    target_results: dict[str, Any] = {}
    for target_name in detailer_settings.get("order", ("face", "eye")):
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
        "order": list(detailer_settings.get("order", ("face", "eye"))),
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
        for name in ("face", "eye")
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
        positive=_aio_prompt_with_lora_metadata(
            str(positive_prompt or "unknown"),
            applied_loras,
        ),
        negative=str(negative_prompt or "unknown"),
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


def _alignment_value(value) -> Optional[int]:
    text = str(_single_value(value) or "").strip().lower()
    if text in ("", "impact", "none", "0"):
        return None
    try:
        alignment = int(text)
    except ValueError:
        return None
    return alignment if alignment > 1 else None


def _align_up(value: int, alignment: int) -> int:
    value = int(value)
    alignment = int(alignment)
    return max(alignment, ((value + alignment - 1) // alignment) * alignment)


def _align_nearest(value: int, alignment: int) -> int:
    value = max(1, int(value))
    alignment = max(1, int(alignment))
    lower = max(alignment, (value // alignment) * alignment)
    upper = _align_up(value, alignment)
    if (value - lower) < (upper - value):
        return lower
    return upper


def _scale_by_value(value, default: float = 1.0) -> float:
    scale = _as_float(value, default)
    if not isfinite(scale):
        scale = default
    return max(0.01, min(8.0, scale))


def _max_long_edge_value(value) -> int:
    max_long_edge = _as_int(value, 0)
    if max_long_edge <= 0:
        return 0
    return max(1, min(16384, max_long_edge))


def _aligned_size_near_scale(
    source_width: int,
    source_height: int,
    scale: float,
    alignment: int,
    max_long_edge: int,
) -> Optional[tuple[int, int, float]]:
    source_long_edge = max(source_width, source_height)
    target_scale = scale
    if max_long_edge > 0 and source_long_edge * target_scale > max_long_edge:
        target_scale = max_long_edge / source_long_edge
    if target_scale <= 0:
        return None

    target_width = max(1, round(source_width * target_scale))
    target_height = max(1, round(source_height * target_scale))
    width_candidates = {
        max(alignment, (target_width // alignment) * alignment),
        _align_up(target_width, alignment),
    }
    height_candidates = {
        max(alignment, (target_height // alignment) * alignment),
        _align_up(target_height, alignment),
    }

    candidates: list[tuple[int, int, float]] = []
    for candidate_width in width_candidates:
        for candidate_height in height_candidates:
            if max_long_edge > 0 and max(candidate_width, candidate_height) > max_long_edge:
                continue
            if scale > 1.0 and max_long_edge > source_long_edge:
                if candidate_width <= source_width or candidate_height <= source_height:
                    continue
            applied_scale = (candidate_width / source_width + candidate_height / source_height) / 2.0
            candidates.append((candidate_width, candidate_height, applied_scale))
    if not candidates:
        return None

    source_ratio = source_width / source_height
    return min(
        candidates,
        key=lambda item: (
            abs((item[0] / source_width) - target_scale) + abs((item[1] / source_height) - target_scale),
            abs((item[0] / item[1]) - source_ratio),
            -item[0] * item[1],
        ),
    )


def _image_scale_by_multiple_size(
    width: int,
    height: int,
    scale_by,
    multiple,
    max_long_edge=0,
) -> tuple[int, int, float]:
    source_width = max(1, int(width))
    source_height = max(1, int(height))
    scale = _scale_by_value(scale_by, 1.0)
    max_long_edge = _max_long_edge_value(max_long_edge)
    alignment = _alignment_value(multiple)
    if alignment is None:
        applied_scale = scale
        if max_long_edge > 0:
            applied_scale = min(applied_scale, max_long_edge / max(source_width, source_height))
        target_width = max(1, round(source_width * applied_scale))
        target_height = max(1, round(source_height * applied_scale))
        if max_long_edge > 0 and max(target_width, target_height) > max_long_edge:
            applied_scale = max_long_edge / max(target_width, target_height) * applied_scale
            target_width = max(1, round(source_width * applied_scale))
            target_height = max(1, round(source_height * applied_scale))
        return target_width, target_height, applied_scale

    ratio_gcd = gcd(source_width, source_height)
    base_width = source_width // ratio_gcd
    base_height = source_height // ratio_gcd
    base_long_edge = max(base_width, base_height)
    width_unit = alignment // gcd(base_width, alignment)
    height_unit = alignment // gcd(base_height, alignment)
    valid_unit_step = lcm(width_unit, height_unit)

    max_valid_unit = int((ratio_gcd * 8.0) // valid_unit_step)
    if max_long_edge > 0:
        max_valid_unit = min(max_valid_unit, max_long_edge // (base_long_edge * valid_unit_step))
    if max_valid_unit >= 1:
        desired_unit = (ratio_gcd * scale) / valid_unit_step
        lower_unit = max(1, min(max_valid_unit, int(desired_unit)))
        candidates = {lower_unit}
        if lower_unit < max_valid_unit:
            candidates.add(lower_unit + 1)
        if lower_unit > 1:
            candidates.add(lower_unit - 1)

        valid_unit = min(
            candidates,
            key=lambda unit: (
                abs(((unit * valid_unit_step) / ratio_gcd) - scale),
                -unit,
            ),
        )
        applied_scale = (valid_unit * valid_unit_step) / ratio_gcd
        candidate = (
            base_width * valid_unit * valid_unit_step,
            base_height * valid_unit * valid_unit_step,
            applied_scale,
        )
        if max_long_edge > 0:
            aligned_candidate = _aligned_size_near_scale(
                source_width,
                source_height,
                scale,
                alignment,
                max_long_edge,
            )
            if aligned_candidate is not None:
                source_long_edge = max(source_width, source_height)
                target_long_edge = min(source_long_edge * scale, max_long_edge)
                candidate_long_error = abs(max(candidate[0], candidate[1]) - target_long_edge)
                aligned_long_error = abs(max(aligned_candidate[0], aligned_candidate[1]) - target_long_edge)
                candidate_upscales = candidate[0] > source_width and candidate[1] > source_height
                aligned_upscales = aligned_candidate[0] > source_width and aligned_candidate[1] > source_height
                if scale > 1.0 and aligned_upscales and not candidate_upscales:
                    return aligned_candidate
                if aligned_long_error < candidate_long_error:
                    return aligned_candidate
            if max(source_width, source_height) * scale > max_long_edge and aligned_candidate is not None:
                return aligned_candidate
        return candidate

    aligned_candidate = _aligned_size_near_scale(
        source_width,
        source_height,
        scale,
        alignment,
        max_long_edge,
    )
    if aligned_candidate is not None:
        return aligned_candidate

    target_width = _align_nearest(round(source_width * scale), alignment)
    target_height = _align_nearest(round(source_height * scale), alignment)
    applied_scale = (target_width / source_width + target_height / source_height) / 2.0
    return target_width, target_height, applied_scale


def _normalize_image_scale_options(upscale_method, multiple, max_long_edge):
    method = str(_single_value(upscale_method) or "").strip()
    size_multiple = str(_single_value(multiple) or "").strip()
    max_edge = max_long_edge

    # Compatibility for workflows created before max_long_edge existed, or while it was inserted
    # before upscale_method: widget values can shift into the wrong input names.
    if size_multiple in IMAGE_UPSCALE_METHODS and str(_single_value(max_long_edge) or "").strip() in IMAGE_SCALE_MULTIPLES:
        shifted_max_edge = upscale_method
        method = size_multiple
        size_multiple = str(_single_value(max_long_edge) or "").strip()
        max_edge = shifted_max_edge
    if str(_single_value(max_long_edge) or "").strip() in IMAGE_UPSCALE_METHODS:
        shifted_method = str(_single_value(max_long_edge) or "").strip()
        if method in IMAGE_SCALE_MULTIPLES:
            size_multiple = method
        method = shifted_method
        max_edge = 0

    if method not in IMAGE_UPSCALE_METHODS:
        method = "bicubic"
    if size_multiple not in IMAGE_SCALE_MULTIPLES:
        size_multiple = "32"
    return method, size_multiple, max_edge


def _common_upscale_image(samples, width: int, height: int, upscale_method: str):
    try:
        import comfy.utils  # type: ignore

        return comfy.utils.common_upscale(samples, width, height, upscale_method, "disabled")
    except Exception:
        import torch.nn.functional as F  # type: ignore

        method = "bicubic" if str(upscale_method) == "lanczos" else str(upscale_method)
        if method in {"bilinear", "bicubic"}:
            return F.interpolate(samples, size=(height, width), mode=method, align_corners=False)
        return F.interpolate(samples, size=(height, width), mode=method)


class _EasyUseAnimaAlignedDetailerHook:
    def __init__(self, base_hook, alignment: Optional[int]):
        self.base_hook = base_hook
        self.alignment = int(alignment) if alignment is not None else None

    def __getattr__(self, name):
        if self.base_hook is not None:
            return getattr(self.base_hook, name)
        raise AttributeError(name)

    def touch_scaled_size(self, width, height):
        if self.base_hook is not None and hasattr(self.base_hook, "touch_scaled_size"):
            width, height = self.base_hook.touch_scaled_size(width, height)
        if self.alignment is None:
            return width, height
        aligned_width = _align_up(width, self.alignment)
        aligned_height = _align_up(height, self.alignment)
        if aligned_width != width or aligned_height != height:
            logger.info(
                "[EasyUseAnima] Detailer hook aligned crop size %sx%s -> %sx%s (alignment=%s)",
                width,
                height,
                aligned_width,
                aligned_height,
                self.alignment,
            )
        return aligned_width, aligned_height

    def post_upscale(self, image, noise_mask):
        if self.base_hook is not None and hasattr(self.base_hook, "post_upscale"):
            return self.base_hook.post_upscale(image, noise_mask)
        return image

    def get_skip_sampling(self):
        if self.base_hook is not None and hasattr(self.base_hook, "get_skip_sampling"):
            return self.base_hook.get_skip_sampling()
        return False

    def post_encode(self, latent):
        if self.base_hook is not None and hasattr(self.base_hook, "post_encode"):
            return self.base_hook.post_encode(latent)
        return latent

    def get_custom_sampler(self):
        if self.base_hook is not None and hasattr(self.base_hook, "get_custom_sampler"):
            return self.base_hook.get_custom_sampler()
        return None

    def set_steps(self, steps):
        if self.base_hook is not None and hasattr(self.base_hook, "set_steps"):
            return self.base_hook.set_steps(steps)
        return None

    def cycle_latent(self, latent):
        if self.base_hook is not None and hasattr(self.base_hook, "cycle_latent"):
            return self.base_hook.cycle_latent(latent)
        return latent

    def pre_ksample(self, model, seed, steps, cfg, sampler_name, scheduler, positive, negative, latent, denoise):
        if self.base_hook is not None and hasattr(self.base_hook, "pre_ksample"):
            return self.base_hook.pre_ksample(
                model, seed, steps, cfg, sampler_name, scheduler, positive, negative, latent, denoise
            )
        return model, seed, steps, cfg, sampler_name, scheduler, positive, negative, latent, denoise

    def get_custom_noise(self, seed, noise, is_touched):
        if self.base_hook is not None and hasattr(self.base_hook, "get_custom_noise"):
            return self.base_hook.get_custom_noise(seed, noise, is_touched)
        return noise, is_touched

    def pre_decode(self, latent):
        if self.base_hook is not None and hasattr(self.base_hook, "pre_decode"):
            return self.base_hook.pre_decode(latent)
        return latent

    def post_decode(self, image):
        if self.base_hook is not None and hasattr(self.base_hook, "post_decode"):
            return self.base_hook.post_decode(image)
        return image

    def post_paste(self, image):
        if self.base_hook is not None and hasattr(self.base_hook, "post_paste"):
            return self.base_hook.post_paste(image)
        return image


def _split_tag_text(value: str) -> list[str]:
    if not value:
        return []
    parts: list[str] = []
    for line in str(value).splitlines():
        parts.extend(part.strip() for part in line.split(","))
    return [part for part in parts if part]


def _prompt_tokens(value: str) -> list[str]:
    if not value:
        return []
    cleaned_val = _HASH_COMMENT_RE.sub("", value)
    normalized = str(cleaned_val).replace("\r\n", "\n").replace("\r", "\n")
    normalized = normalized.replace("，", ",").replace("\n", ",")
    tokens: list[str] = []
    for token in parse_prompt(normalized, profile="prompt").tokens:
        cleaned = _INLINE_SPACE_RE.sub(" ", str(token).strip(" ,\n\t"))
        if cleaned:
            tokens.append(cleaned)
    return tokens


def _join_prompt_tokens(*parts: str) -> str:
    tokens: list[str] = []
    for part in parts:
        tokens.extend(_prompt_tokens(part))
    return ", ".join(tokens)


def _correct_builder_prompt(prompt: str, artist_overrides: str = "") -> str:
    if not prompt:
        return ""
    result = correct_prompt(
        prompt,
        profile="prompt",
        knowledge_base=load_knowledge_base(allow_missing=True),
        validate_artist_tags=False,
        artist_overrides=_prompt_tokens(artist_overrides),
    )
    return result.text


def _metadata_filter_key(value: str) -> str:
    value = _INLINE_SPACE_RE.sub(" ", str(value or "").strip(" ,\n\t"))
    return value.replace("_", " ").casefold()


def _metadata_filter_keys(value: str) -> set[str]:
    keys = {_metadata_filter_key(value)}
    weighted = _WEIGHTED_TOKEN_RE.match(str(value or "").strip())
    if weighted:
        keys.add(_metadata_filter_key(weighted.group(1)))
    return {key for key in keys if key}


def _filter_metadata_prompt(prompt: str, filter_words: str) -> str:
    filter_keys: set[str] = set()
    for word in _prompt_tokens(filter_words):
        filter_keys.update(_metadata_filter_keys(word))
    if not prompt or not filter_keys:
        return prompt

    kept = [
        token
        for token in _prompt_tokens(prompt)
        if _metadata_filter_keys(token).isdisjoint(filter_keys)
    ]
    return ", ".join(kept)


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
            parts["artist"].append(text)
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
    mode_key = normalize_wildcard_mode(mode)
    expanded_fields = _clone_advanced_fields(fields)
    if mode_key == WILDCARD_MODE_REPRODUCE:
        return expanded_fields, {
            "changed": False,
            "used_keys": (),
            "missing_keys": (),
        }

    changed = False
    used_keys: list[str] = []
    missing_keys: list[str] = []
    for field in expanded_fields:
        text = str(field.get("text") or "")
        if not has_wildcard_syntax(text):
            continue
        result = expand_wildcards(text, seed=seed, mode=mode_key)
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
    return _join_prompt_tokens(
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


def _split_artist_mix_items(text: str) -> list[str]:
    items: list[str] = []
    buffer: list[str] = []
    depth = 0
    escaped = False
    for char in str(text or ""):
        if escaped:
            buffer.append(char)
            escaped = False
            continue
        if char == "\\":
            buffer.append(char)
            escaped = True
            continue
        if char == "(":
            depth += 1
        elif char == ")" and depth > 0:
            depth -= 1
        if (char == "," or char == "\n") and depth == 0:
            item = "".join(buffer).strip()
            if item:
                items.append(item)
            buffer = []
            continue
        buffer.append(char)
    item = "".join(buffer).strip()
    if item:
        items.append(item)
    return items


def _split_artist_mix_blocks(text: str) -> list[str]:
    source = str(text or "").replace("\r\n", "\n").replace("\r", "\n")
    if not _SECTION_SEPARATOR_RE.search(source):
        return []
    blocks: list[str] = []
    current: list[str] = []
    for line in source.split("\n"):
        if _SECTION_SEPARATOR_RE.match(line):
            block = "\n".join(current).strip(" ,\n")
            if block:
                blocks.append(block)
            current = []
            continue
        current.append(line)
    block = "\n".join(current).strip(" ,\n")
    if block:
        blocks.append(block)
    return blocks


def _parse_artist_mix_items(text: str) -> list[tuple[str, float]]:
    parsed: list[tuple[str, float]] = []
    blocks = _split_artist_mix_blocks(text)
    source_items = blocks or _split_artist_mix_items(text)
    for item in source_items:
        raw_tag = item.strip()
        weight = 1.0
        weight_source = raw_tag
        if blocks:
            block_parts = _split_artist_mix_items(raw_tag)
            if block_parts:
                weight_source = block_parts[0].strip()
        match = _WEIGHTED_ARTIST_RE.match(weight_source)
        if match:
            tag = raw_tag if blocks else match.group("tag").strip()
            weight = _as_float(match.group("weight"), 1.0)
        elif raw_tag.startswith("(") and raw_tag.endswith(")"):
            tag = raw_tag[1:-1].strip()
        else:
            tag = raw_tag
        if tag and isfinite(weight) and weight > 0:
            parsed.append((tag, weight))
    return parsed


def _artist_tags_from_prompt(text: str, source: str = "artist_field") -> list[dict[str, Any]]:
    return [
        {
            "tag": tag,
            "weight": float(weight),
            "source": source,
        }
        for tag, weight in _parse_artist_mix_items(text)
    ]


def _bounded_artist_mix_float(value, default: float, minimum: float, maximum: float) -> float:
    result = _as_float(value, default)
    if not isfinite(result):
        result = default
    return max(minimum, min(maximum, result))


def _bounded_artist_mix_int(value, default: int, minimum: int, maximum: int) -> int:
    return max(minimum, min(maximum, _as_int(value, default)))


def _normalize_artist_mix_mode(value, default: str = ARTIST_MIX_MODE_PROMPT) -> str:
    mode = str(value or default)
    if mode == ARTIST_MIX_MODE_OFF:
        return ARTIST_MIX_MODE_OFF
    return mode if mode in ARTIST_MIX_MODES else default


def _normalize_artist_tag_position(value: str) -> str:
    mode = str(value or ARTIST_TAG_POSITION_CORRECT)
    return mode if mode in ARTIST_TAG_POSITION_MODES else ARTIST_TAG_POSITION_CORRECT


def _artist_mix_mode_tooltip(include_prompt_data: bool = False) -> str:
    lines = []
    if include_prompt_data:
        lines.append("prompt_data follows EASYUSE_ANIMA_PROMPT_DATA, off/prompt keeps artists inline.")
    lines.append(f"{ARTIST_MIX_MODE_OFF}: {ARTIST_MIX_MODE_DESCRIPTIONS[ARTIST_MIX_MODE_OFF]}")
    for mode in ARTIST_MIX_MODES:
        lines.append(f"{mode}: {ARTIST_MIX_MODE_DESCRIPTIONS[mode]}")
    return "\n".join(lines)


def _coalesce_artist_mix_items(artists: list[tuple[str, float]]) -> list[tuple[str, float]]:
    coalesced: dict[str, float] = {}
    order: list[str] = []
    for tag, weight in artists:
        normalized_tag = str(tag or "").strip()
        if not normalized_tag:
            continue
        value = float(weight)
        if not isfinite(value) or value <= 0:
            continue
        if normalized_tag not in coalesced:
            order.append(normalized_tag)
            coalesced[normalized_tag] = 0.0
        coalesced[normalized_tag] += value
    return [
        (tag, weight)
        for tag in order
        if (weight := coalesced.get(tag, 0.0)) > 0
    ]


def _artist_mix_prompt_tags(artists: list[tuple[str, float]], include_weights: bool) -> str:
    tags: list[str] = []
    for tag, weight in artists:
        if include_weights and "," not in tag and "\n" not in tag and abs(float(weight) - 1.0) >= 0.001:
            tags.append(f"({tag}:{float(weight):g})")
        else:
            tags.append(tag)
    return _join_prompt_tokens(*tags)


def _artist_prompt_with_position(
    base_prompt: str,
    artist_prompt: str,
    artist_position: str = ARTIST_TAG_POSITION_CORRECT,
) -> str:
    artist_text = _join_prompt_tokens(artist_prompt)
    base_text = _join_prompt_tokens(base_prompt)
    if not artist_text:
        return base_text
    if not base_text:
        if _normalize_artist_tag_position(artist_position) == ARTIST_TAG_POSITION_CORRECT:
            return _correct_builder_prompt(artist_text, artist_overrides=artist_text)
        return artist_text

    position = _normalize_artist_tag_position(artist_position)
    if position == ARTIST_TAG_POSITION_FRONT:
        return _join_prompt_tokens(artist_text, base_text)
    if position == ARTIST_TAG_POSITION_BACK:
        return _join_prompt_tokens(base_text, artist_text)
    return _correct_builder_prompt(
        _join_prompt_tokens(base_text, artist_text),
        artist_overrides=artist_text,
    )


def _normalized_artist_weights(artists: list[tuple[str, float]]) -> list[float]:
    total = sum(weight for _tag, weight in artists)
    if total <= 0:
        return [1.0 / len(artists) for _tag, _weight in artists] if artists else []
    return [weight / total for _tag, weight in artists]


def _equal_artist_weights(artists: list[tuple[str, float]]) -> list[float]:
    return [1.0 / len(artists) for _tag, _weight in artists] if artists else []


def _normalize_weight_values(values) -> list[float]:
    kept = [max(0.0, float(value)) for value in values]
    total = sum(kept)
    if total <= 0:
        return [1.0 / len(kept) for _value in kept] if kept else []
    return [value / total for value in kept]


def _interpolate_artist_weights(start_weights: list[float], end_weights: list[float], amount: float) -> list[float]:
    amount = max(0.0, min(1.0, float(amount)))
    return _normalize_weight_values(
        (1.0 - amount) * float(start) + amount * float(end)
        for start, end in zip(start_weights, end_weights)
    )


def _copy_conditioning_metadata(metadata) -> dict[str, Any]:
    try:
        import torch  # type: ignore
    except Exception:
        torch = None  # type: ignore

    result = dict(metadata or {})
    if torch is None:
        return result
    for key, value in list(result.items()):
        if torch.is_tensor(value):
            result[key] = value.clone()
    return result


def _pad_conditioning_tensor(tensor, target_length: int):
    if tensor.shape[1] >= target_length:
        return tensor[:, :target_length]
    try:
        import torch  # type: ignore
    except Exception as exc:
        raise RuntimeError("[EasyUseAnima] torch is required for artist mix conditioning.") from exc
    padding = torch.zeros(
        (tensor.shape[0], target_length - tensor.shape[1], tensor.shape[2]),
        dtype=tensor.dtype,
        device=tensor.device,
    )
    return torch.cat([tensor, padding], dim=1)


def _blend_conditionings(conditionings: list, weights: list[float], composite_conditioning=None) -> list:
    if not conditionings:
        return []
    if len(conditionings) == 1:
        return list(conditionings[0])
    expected_len = len(conditionings[0])
    if any(len(conditioning) != expected_len for conditioning in conditionings):
        raise RuntimeError("[EasyUseAnima] artist mix average requires CLIP conditionings with the same length.")

    try:
        import torch  # type: ignore
    except Exception as exc:
        raise RuntimeError("[EasyUseAnima] torch is required for artist mix conditioning.") from exc

    blended = []
    for entry_index in range(expected_len):
        first_tensor = conditionings[0][entry_index][0]
        max_length = max(conditioning[entry_index][0].shape[1] for conditioning in conditionings)
        if any(
            conditioning[entry_index][0].shape[0] != first_tensor.shape[0]
            or conditioning[entry_index][0].shape[2] != first_tensor.shape[2]
            for conditioning in conditionings
        ):
            raise RuntimeError("[EasyUseAnima] artist mix average requires matching CLIP embedding sizes.")

        tensor = torch.zeros(
            (first_tensor.shape[0], max_length, first_tensor.shape[2]),
            dtype=first_tensor.dtype,
            device=first_tensor.device,
        )
        for conditioning, weight in zip(conditionings, weights):
            tensor = tensor + _pad_conditioning_tensor(conditioning[entry_index][0], max_length) * float(weight)

        metadata_source = (
            composite_conditioning[entry_index][1]
            if composite_conditioning and len(composite_conditioning) > entry_index
            else conditionings[0][entry_index][1]
        )
        metadata = _copy_conditioning_metadata(metadata_source)
        pooled_candidates = [
            conditioning[entry_index][1].get("pooled_output")
            for conditioning in conditionings
            if isinstance(conditioning[entry_index][1], dict)
        ]
        if pooled_candidates and all(torch.is_tensor(value) for value in pooled_candidates):
            pooled_shape = pooled_candidates[0].shape
            if all(value.shape == pooled_shape for value in pooled_candidates):
                pooled_output = torch.zeros_like(pooled_candidates[0])
                for value, weight in zip(pooled_candidates, weights):
                    pooled_output = pooled_output + value * float(weight)
                metadata["pooled_output"] = pooled_output
        elif torch.is_tensor(metadata.get("pooled_output")):
            metadata.pop("pooled_output", None)
        metadata.pop("strength", None)
        blended.append([tensor, metadata])
    return blended


def _encoded_artist_conditionings(clip, data: dict[str, Any], base_prompt: str, artists: list[tuple[str, float]]) -> list:
    return [
        (
            tag,
            float(weight),
            _encode_with_comfy_clip(
                clip,
                _artist_variant_prompt_from_prompt_data(data, base_prompt, tag),
            ),
        )
        for tag, weight in artists
    ]


def _artist_delta_rms_from_encoded(
    base_conditioning,
    encoded_artists: list,
    weights: list[float],
    composite_conditioning=None,
    style_gain: float = ARTIST_MIX_DEFAULT_STYLE_GAIN,
    rms_scale_cap: float = ARTIST_MIX_DEFAULT_RMS_SCALE_CAP,
    branch_strength: float | None = None,
) -> list | None:
    if not encoded_artists or len(base_conditioning) != 1:
        return None
    if any(len(conditioning) != 1 for _tag, _weight, conditioning in encoded_artists):
        return None

    try:
        import torch  # type: ignore
    except Exception as exc:
        raise RuntimeError("[EasyUseAnima] torch is required for artist mix delta_rms conditioning.") from exc

    base_tensor, base_meta = base_conditioning[0]
    if not torch.is_tensor(base_tensor) or base_tensor.ndim != 3:
        return None
    artist_tensors = [conditioning[0][0] for _tag, _weight, conditioning in encoded_artists]
    if any(
        not torch.is_tensor(tensor)
        or tensor.ndim != 3
        or tensor.shape[0] != base_tensor.shape[0]
        or tensor.shape[2] != base_tensor.shape[2]
        for tensor in artist_tensors
    ):
        return None

    max_length = max([base_tensor.shape[1], *(tensor.shape[1] for tensor in artist_tensors)])
    base_padded = _pad_conditioning_tensor(base_tensor, max_length)
    mixed_delta = torch.zeros_like(base_padded)
    target_rms = None
    for (_tag, _weight, conditioning), alpha in zip(encoded_artists, weights):
        cond_padded = _pad_conditioning_tensor(conditioning[0][0], max_length)
        delta = cond_padded - base_padded
        mixed_delta = mixed_delta + delta * float(alpha)
        rms = delta.float().pow(2).mean().sqrt()
        target_rms = rms * float(alpha) if target_rms is None else target_rms + rms * float(alpha)

    if target_rms is None:
        return None
    actual_rms = mixed_delta.float().pow(2).mean().sqrt().clamp_min(1e-6)
    rms_scale = torch.clamp(
        target_rms / actual_rms,
        1.0,
        max(1.0, float(rms_scale_cap)),
    )
    mixed_tensor = base_padded + mixed_delta * float(style_gain) * rms_scale

    metadata_source = (
        composite_conditioning[0][1]
        if composite_conditioning and len(composite_conditioning) == 1
        else base_meta
    )
    metadata = _copy_conditioning_metadata(metadata_source)
    metadata.pop("strength", None)
    if branch_strength is not None:
        metadata["strength"] = max(0.0, float(branch_strength))

    base_pool = base_meta.get("pooled_output") if isinstance(base_meta, dict) else None
    artist_pools = [
        conditioning[0][1].get("pooled_output")
        for _tag, _weight, conditioning in encoded_artists
        if isinstance(conditioning[0][1], dict)
    ]
    if torch.is_tensor(base_pool) and len(artist_pools) == len(encoded_artists) and all(
        torch.is_tensor(pool) and pool.shape == base_pool.shape for pool in artist_pools
    ):
        mixed_pool_delta = torch.zeros_like(base_pool)
        target_pool_rms = None
        for pool, alpha in zip(artist_pools, weights):
            delta = pool - base_pool
            mixed_pool_delta = mixed_pool_delta + delta * float(alpha)
            rms = delta.float().pow(2).mean().sqrt()
            target_pool_rms = rms * float(alpha) if target_pool_rms is None else target_pool_rms + rms * float(alpha)
        if target_pool_rms is not None:
            actual_pool_rms = mixed_pool_delta.float().pow(2).mean().sqrt().clamp_min(1e-6)
            pool_scale = torch.clamp(
                target_pool_rms / actual_pool_rms,
                1.0,
                max(1.0, float(rms_scale_cap)),
            )
            metadata["pooled_output"] = base_pool + mixed_pool_delta * float(style_gain) * pool_scale
    elif isinstance(metadata, dict):
        metadata.pop("pooled_output", None)

    return [[mixed_tensor, metadata]]


def _fallback_artist_average_or_exact(
    clip,
    data: dict[str, Any],
    base_prompt: str,
    artists: list[tuple[str, float]],
) -> list:
    try:
        return _encode_artist_average(clip, data, base_prompt, artists)
    except Exception:
        return _encode_artist_exact(clip, data, base_prompt, artists)


def _encode_artist_delta_rms(
    clip,
    data: dict[str, Any],
    base_prompt: str,
    artists: list[tuple[str, float]],
    weights: list[float] | None = None,
    style_gain: float = ARTIST_MIX_DEFAULT_STYLE_GAIN,
    rms_scale_cap: float = ARTIST_MIX_DEFAULT_RMS_SCALE_CAP,
    branch_strength: float | None = None,
) -> list:
    artists = _coalesce_artist_mix_items(artists)
    if not artists:
        return _encode_with_comfy_clip(clip, base_prompt)
    mix_weights = list(weights) if weights is not None else _normalized_artist_weights(artists)
    try:
        base_conditioning = _encode_with_comfy_clip(clip, base_prompt)
        encoded = _encoded_artist_conditionings(clip, data, base_prompt, artists)
        composite_prompt = _artist_variant_prompt_from_prompt_data(
            data,
            base_prompt,
            _artist_mix_prompt_tags(artists, include_weights=True),
        )
        composite = _encode_with_comfy_clip(clip, composite_prompt)
        result = _artist_delta_rms_from_encoded(
            base_conditioning,
            encoded,
            mix_weights,
            composite if len(composite) == 1 else None,
            style_gain=style_gain,
            rms_scale_cap=rms_scale_cap,
            branch_strength=branch_strength,
        )
        if result is not None:
            return result
    except Exception:
        pass
    fallback = _fallback_artist_average_or_exact(clip, data, base_prompt, artists)
    if branch_strength is not None:
        return _conditionings_with_strength(fallback, branch_strength)
    return fallback


def _conditionings_with_values(conditioning, values: dict[str, Any]) -> list:
    output = []
    for tensor, metadata in conditioning or []:
        item_metadata = _copy_conditioning_metadata(metadata)
        item_metadata.update(values)
        output.append([tensor, item_metadata])
    return output


def _conditionings_with_range(conditioning, start_percent: float, end_percent: float = 1.0) -> list:
    start = max(0.0, min(1.0, float(start_percent)))
    end = max(start, min(1.0, float(end_percent)))
    return _conditionings_with_values(conditioning, {"start_percent": start, "end_percent": end})


def _conditionings_with_strength(conditioning, strength: float) -> list:
    return _conditionings_with_values(conditioning, {"strength": max(0.0, float(strength))})


def _mark_artist_mix_conditioning(conditioning, key: str) -> list:
    return _conditionings_with_values(conditioning, {key: True})


def _normalize_prompt_data(value: str | dict | None) -> dict[str, Any]:
    if isinstance(value, dict):
        return dict(value)
    if isinstance(value, str):
        try:
            parsed = json.loads(value or "{}")
        except json.JSONDecodeError:
            parsed = {}
        if isinstance(parsed, dict):
            return parsed
    return {}


def _prompt_data_nested(data: dict[str, Any], key: str) -> dict[str, Any]:
    value = data.get(key)
    return value if isinstance(value, dict) else {}


def _prompt_data_output(data: dict[str, Any], name: str, default=None):
    outputs = _prompt_data_nested(data, "outputs")
    if name in outputs:
        return outputs[name]
    if name in data:
        return data[name]

    mod_guidance = _prompt_data_nested(data, "mod_guidance")
    anima_mod_guidance = _prompt_data_nested(data, "anima_mod_guidance")
    resolution = _prompt_data_nested(data, "resolution")
    fallbacks = {
        "positive_prompt": data.get("prompt", default),
        "anima_mod_guidance_quality_tags": mod_guidance.get(
            "quality_tags",
            anima_mod_guidance.get("quality_tags", default),
        ),
        "anima_mod_guidance_negative_prompt": mod_guidance.get(
            "negative_prompt",
            anima_mod_guidance.get("negative_prompt", default),
        ),
        "use_anima_mod_guidance": mod_guidance.get(
            "enabled",
            anima_mod_guidance.get("use_positive", default),
        ),
        "use_negative_anima_mod_guidance": mod_guidance.get(
            "negative_enabled",
            anima_mod_guidance.get("use_negative", default),
        ),
        "width": resolution.get("width", default),
        "height": resolution.get("height", default),
    }
    return fallbacks.get(name, default)


def _prompt_data_input_default(input_spec):
    if not isinstance(input_spec, tuple):
        return None
    options = input_spec[1] if len(input_spec) > 1 and isinstance(input_spec[1], dict) else {}
    if "default" in options:
        return options["default"]
    input_type = input_spec[0] if input_spec else None
    if isinstance(input_type, (list, tuple)) and input_type:
        return input_type[0]
    if input_type == "BOOLEAN":
        return False
    if input_type == "INT":
        return 0
    if input_type == "FLOAT":
        return 0.0
    if input_type == "STRING":
        return ""
    return None


def _prompt_data_json_safe(value):
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, (list, tuple)):
        return [_prompt_data_json_safe(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _prompt_data_json_safe(item) for key, item in value.items()}
    return str(value)


def _prompt_data_parameter_snapshot(
    input_defs: dict[str, Any],
    values: dict[str, Any],
    ui_payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    ui_payload = ui_payload if isinstance(ui_payload, dict) else {}
    snapshot: dict[str, Any] = {}
    for name, input_spec in input_defs.items():
        if name in ui_payload:
            value = ui_payload[name]
        elif name in values:
            value = values[name]
        else:
            value = _prompt_data_input_default(input_spec)
        snapshot[name] = _prompt_data_json_safe(value)
    return snapshot


def _advanced_outputs_from_prompt_data(value: str | dict | None) -> tuple:
    data = _normalize_prompt_data(value)
    return (
        str(_prompt_data_output(data, "positive_prompt", "") or ""),
        str(_prompt_data_output(data, "negative_prompt", "") or ""),
        str(_prompt_data_output(data, "anima_mod_guidance_quality_tags", "") or ""),
        str(_prompt_data_output(data, "anima_mod_guidance_negative_prompt", "") or ""),
        _as_bool(_prompt_data_output(data, "use_anima_mod_guidance", False), False),
        _as_bool(_prompt_data_output(data, "use_negative_anima_mod_guidance", False), False),
        str(_prompt_data_output(data, "metadata_prompt", "") or ""),
        str(_prompt_data_output(data, "metadata_negative_prompt", "") or ""),
        _as_int(_prompt_data_output(data, "width", 1024), 1024),
        _as_int(_prompt_data_output(data, "height", 1024), 1024),
    )


def _copy_prompt_data_for_update(value: str | dict | None) -> dict[str, Any]:
    data = dict(_normalize_prompt_data(value))
    for key in ("outputs", "mod_guidance", "anima_mod_guidance", "resolution"):
        nested = data.get(key)
        if isinstance(nested, dict):
            data[key] = dict(nested)
    return data


def _set_prompt_data_output(data: dict[str, Any], name: str, value) -> None:
    outputs = data.setdefault("outputs", {})
    if not isinstance(outputs, dict):
        outputs = {}
        data["outputs"] = outputs
    outputs[name] = value

    if name == "positive_prompt":
        data["positive_prompt"] = str(value or "")
        data["prompt"] = data["positive_prompt"]
    elif name == "negative_prompt":
        data["negative_prompt"] = str(value or "")
    elif name == "metadata_prompt":
        data["metadata_prompt"] = str(value or "")
    elif name == "metadata_negative_prompt":
        data["metadata_negative_prompt"] = str(value or "")
    elif name == "width":
        width = _as_int(value, 1024)
        data["width"] = width
        resolution = data.setdefault("resolution", {})
        if isinstance(resolution, dict):
            resolution["width"] = width
    elif name == "height":
        height = _as_int(value, 1024)
        data["height"] = height
        resolution = data.setdefault("resolution", {})
        if isinstance(resolution, dict):
            resolution["height"] = height
    elif name == "anima_mod_guidance_quality_tags":
        mod_guidance = data.setdefault("mod_guidance", {})
        anima_mod_guidance = data.setdefault("anima_mod_guidance", {})
        if isinstance(mod_guidance, dict):
            mod_guidance["quality_tags"] = str(value or "")
        if isinstance(anima_mod_guidance, dict):
            anima_mod_guidance["quality_tags"] = str(value or "")
    elif name == "anima_mod_guidance_negative_prompt":
        mod_guidance = data.setdefault("mod_guidance", {})
        anima_mod_guidance = data.setdefault("anima_mod_guidance", {})
        if isinstance(mod_guidance, dict):
            mod_guidance["negative_prompt"] = str(value or "")
        if isinstance(anima_mod_guidance, dict):
            anima_mod_guidance["negative_prompt"] = str(value or "")
    elif name == "use_anima_mod_guidance":
        enabled = _as_bool(value, False)
        mod_guidance = data.setdefault("mod_guidance", {})
        anima_mod_guidance = data.setdefault("anima_mod_guidance", {})
        if isinstance(mod_guidance, dict):
            mod_guidance["enabled"] = enabled
        if isinstance(anima_mod_guidance, dict):
            anima_mod_guidance["use_positive"] = enabled
    elif name == "use_negative_anima_mod_guidance":
        enabled = _as_bool(value, False)
        mod_guidance = data.setdefault("mod_guidance", {})
        anima_mod_guidance = data.setdefault("anima_mod_guidance", {})
        if isinstance(mod_guidance, dict):
            mod_guidance["negative_enabled"] = enabled
        if isinstance(anima_mod_guidance, dict):
            anima_mod_guidance["use_negative"] = enabled


def _apply_prompt_data_overrides(
    value: str | dict | None,
    overrides: dict[str, Any],
) -> dict[str, Any]:
    data = _copy_prompt_data_for_update(value)
    for name in EasyUseAnimaPromptStudioAdvanced.RETURN_NAMES:
        if name not in overrides:
            continue
        _set_prompt_data_output(data, name, overrides[name])
    return data


def _prompt_data_positive_fields(data: dict[str, Any]) -> list[dict]:
    fields = data.get("fields")
    if not isinstance(fields, list) or not fields:
        return []
    return _advanced_enabled_pane_fields(_normalize_advanced_fields(fields), "positive")


def _prompt_data_artist_base_prompt(data: dict[str, Any], positive_prompt: str) -> str:
    artist = _prompt_data_nested(data, "artist")
    artist_mix = _prompt_data_nested(data, "artist_mix")
    for source in (
        artist_mix.get("base_prompt"),
        data.get("positive_without_artist_section") if "positive_without_artist_section" in data else None,
        data.get("global_prompt") if "global_prompt" in data else None,
        artist.get("positive_prompt_without_artist") if "positive_prompt_without_artist" in artist else None,
    ):
        if source is not None:
            return str(source or "")
    return str(positive_prompt or "")


def _artist_variant_prompt_from_prompt_data(
    data: dict[str, Any],
    base_prompt: str,
    artist_prompt: str,
) -> str:
    artist_text = _join_prompt_tokens(artist_prompt)
    base_text = _join_prompt_tokens(base_prompt)
    if not artist_text:
        return base_text
    artist_mix = _prompt_data_nested(data, "artist_mix")
    artist_position = _normalize_artist_tag_position(
        artist_mix.get("artist_position", data.get("artist_position", ARTIST_TAG_POSITION_CORRECT))
    )
    if not base_text:
        return _artist_prompt_with_position("", artist_text, artist_position)

    fields = _prompt_data_positive_fields(data)
    if artist_position == ARTIST_TAG_POSITION_CORRECT and fields:
        prompt = _advanced_prompt_with_artist_override(
            fields,
            artist_text,
            include_quality=not _as_bool(_prompt_data_output(data, "use_anima_mod_guidance", False), False),
            force_pin_triggers=_as_bool(data.get("pin_trigger_tags_to_front"), False),
        )
        if prompt:
            return prompt
    return _artist_prompt_with_position(base_text, artist_text, artist_position)


def _prompt_data_artist_mix_config(
    data: dict[str, Any],
    artist_mix_mode: str,
    artist_mix_start_percent: float,
    artist_mix_strength_scale: float,
    artist_mix_style_gain: float,
    artist_mix_rms_scale_cap: float,
    artist_mix_exact_top_k: int,
    artist_mix_cluster_count: int,
    artist_mix_dominant_isolation: bool,
    artist_mix_dominant_threshold: float,
) -> dict[str, Any]:
    source = _prompt_data_nested(data, "artist_mix")
    artist = _prompt_data_nested(data, "artist")
    mode = _normalize_artist_mix_mode(source.get("mode", ARTIST_MIX_MODE_PROMPT))
    enabled = _as_bool(source.get("enabled"), False)
    if mode == ARTIST_MIX_MODE_OFF:
        mode = ARTIST_MIX_MODE_PROMPT
        enabled = False

    config = {
        "enabled": enabled,
        "mode": mode,
        "base_source": str(source.get("base_source") or "positive_without_artist_section"),
        "start_percent": _bounded_artist_mix_float(
            source.get("start_percent"),
            ARTIST_MIX_DEFAULT_START_PERCENT,
            0.0,
            1.0,
        ),
        "strength_scale": _bounded_artist_mix_float(
            source.get("strength_scale"),
            ARTIST_MIX_DEFAULT_STRENGTH_SCALE,
            0.0,
            5.0,
        ),
        "style_gain": _bounded_artist_mix_float(
            source.get("style_gain"),
            ARTIST_MIX_DEFAULT_STYLE_GAIN,
            0.0,
            3.0,
        ),
        "rms_scale_cap": _bounded_artist_mix_float(
            source.get("rms_scale_cap"),
            ARTIST_MIX_DEFAULT_RMS_SCALE_CAP,
            1.0,
            5.0,
        ),
        "exact_top_k": _bounded_artist_mix_int(
            source.get("exact_top_k"),
            ARTIST_MIX_DEFAULT_EXACT_TOP_K,
            0,
            64,
        ),
        "cluster_count": _bounded_artist_mix_int(
            source.get("cluster_count"),
            ARTIST_MIX_DEFAULT_CLUSTER_COUNT,
            1,
            32,
        ),
        "dominant_isolation": _as_bool(
            source.get("dominant_isolation"),
            ARTIST_MIX_DEFAULT_DOMINANT_ISOLATION,
        ),
        "dominant_threshold": _bounded_artist_mix_float(
            source.get("dominant_threshold"),
            ARTIST_MIX_DEFAULT_DOMINANT_THRESHOLD,
            0.0,
            1.0,
        ),
        "artist_prompt": str(
            source.get("artist_prompt")
            or artist.get("weighted_text")
            or artist.get("text")
            or artist.get("positive_prompt")
            or ""
        ),
    }

    override_mode = str(artist_mix_mode or ARTIST_MIX_MODE_FROM_PROMPT_DATA)
    if override_mode != ARTIST_MIX_MODE_FROM_PROMPT_DATA:
        override_mode = _normalize_artist_mix_mode(override_mode, ARTIST_MIX_MODE_OFF)
        if override_mode == ARTIST_MIX_MODE_OFF:
            config["enabled"] = False
            config["mode"] = ARTIST_MIX_MODE_PROMPT
        elif override_mode == ARTIST_MIX_MODE_PROMPT:
            config["enabled"] = False
            config["mode"] = ARTIST_MIX_MODE_PROMPT
        else:
            config["enabled"] = True
            config["mode"] = override_mode
        config["start_percent"] = _bounded_artist_mix_float(
            artist_mix_start_percent,
            ARTIST_MIX_DEFAULT_START_PERCENT,
            0.0,
            1.0,
        )
        config["strength_scale"] = _bounded_artist_mix_float(
            artist_mix_strength_scale,
            ARTIST_MIX_DEFAULT_STRENGTH_SCALE,
            0.0,
            5.0,
        )
        config["style_gain"] = _bounded_artist_mix_float(
            artist_mix_style_gain,
            ARTIST_MIX_DEFAULT_STYLE_GAIN,
            0.0,
            3.0,
        )
        config["rms_scale_cap"] = _bounded_artist_mix_float(
            artist_mix_rms_scale_cap,
            ARTIST_MIX_DEFAULT_RMS_SCALE_CAP,
            1.0,
            5.0,
        )
        config["exact_top_k"] = _bounded_artist_mix_int(
            artist_mix_exact_top_k,
            ARTIST_MIX_DEFAULT_EXACT_TOP_K,
            0,
            64,
        )
        config["cluster_count"] = _bounded_artist_mix_int(
            artist_mix_cluster_count,
            ARTIST_MIX_DEFAULT_CLUSTER_COUNT,
            1,
            32,
        )
        config["dominant_isolation"] = _as_bool(
            artist_mix_dominant_isolation,
            ARTIST_MIX_DEFAULT_DOMINANT_ISOLATION,
        )
        config["dominant_threshold"] = _bounded_artist_mix_float(
            artist_mix_dominant_threshold,
            ARTIST_MIX_DEFAULT_DOMINANT_THRESHOLD,
            0.0,
            1.0,
        )
    return config


def _encode_artist_exact(
    clip,
    data: dict[str, Any],
    base_prompt: str,
    artists: list[tuple[str, float]],
    start_percent: float | None = None,
    end_percent: float | None = None,
    strength_scale: float = 1.0,
    branch_strengths: list[float] | None = None,
) -> list:
    exact = []
    strengths = (
        [max(0.0, float(value)) for value in branch_strengths]
        if branch_strengths is not None
        else [float(weight) * float(strength_scale) for weight in _normalized_artist_weights(artists)]
    )
    for (tag, _weight), strength in zip(artists, strengths):
        variant_prompt = _artist_variant_prompt_from_prompt_data(data, base_prompt, tag)
        for tensor, metadata in _encode_with_comfy_clip(clip, variant_prompt):
            item_metadata = _copy_conditioning_metadata(metadata)
            item_metadata["strength"] = float(strength)
            if start_percent is not None:
                item_metadata["start_percent"] = max(0.0, min(1.0, float(start_percent)))
            if end_percent is not None:
                item_metadata["end_percent"] = max(
                    item_metadata.get("start_percent", 0.0),
                    min(1.0, float(end_percent)),
                )
            item_metadata[ARTIST_MIX_EXACT_KEY] = True
            exact.append([tensor, item_metadata])
    return exact or _encode_with_comfy_clip(clip, base_prompt)


def _encode_artist_average(
    clip,
    data: dict[str, Any],
    base_prompt: str,
    artists: list[tuple[str, float]],
    weights: list[float] | None = None,
) -> list:
    mix_weights = list(weights) if weights is not None else _normalized_artist_weights(artists)
    encoded = [
        _encode_with_comfy_clip(
            clip,
            _artist_variant_prompt_from_prompt_data(data, base_prompt, tag),
        )
        for tag, _weight in artists
    ]
    if any(len(conditioning) != 1 for conditioning in encoded):
        return _encode_artist_exact(clip, data, base_prompt, artists)

    composite_prompt = _artist_variant_prompt_from_prompt_data(
        data,
        base_prompt,
        _artist_mix_prompt_tags(artists, include_weights=True),
    )
    composite = _encode_with_comfy_clip(clip, composite_prompt)
    if len(composite) != 1:
        composite = None
    return _blend_conditionings(encoded, mix_weights, composite)


def _encode_artist_hybrid(
    clip,
    data: dict[str, Any],
    base_prompt: str,
    artists: list[tuple[str, float]],
    exact_top_k: int = ARTIST_MIX_DEFAULT_EXACT_TOP_K,
    style_gain: float = ARTIST_MIX_DEFAULT_STYLE_GAIN,
    rms_scale_cap: float = ARTIST_MIX_DEFAULT_RMS_SCALE_CAP,
    strength_scale: float = ARTIST_MIX_DEFAULT_STRENGTH_SCALE,
) -> list:
    artists = _coalesce_artist_mix_items(artists)
    if not artists:
        return _encode_with_comfy_clip(clip, base_prompt)
    total_weight = sum(weight for _tag, weight in artists)
    if total_weight <= 0:
        return _encode_with_comfy_clip(clip, base_prompt)

    sorted_artists = sorted(artists, key=lambda item: item[1], reverse=True)
    top_k = _bounded_artist_mix_int(exact_top_k, ARTIST_MIX_DEFAULT_EXACT_TOP_K, 0, 64)
    if top_k >= len(sorted_artists):
        return _encode_artist_exact(clip, data, base_prompt, sorted_artists, strength_scale=strength_scale)

    top = sorted_artists[:top_k]
    tail = sorted_artists[top_k:]
    output = []
    if top:
        output.extend(
            _encode_artist_exact(
                clip,
                data,
                base_prompt,
                top,
                branch_strengths=[
                    (weight / total_weight) * float(strength_scale)
                    for _tag, weight in top
                ],
            )
        )
    if tail:
        tail_total = sum(weight for _tag, weight in tail)
        if tail_total <= 0:
            return _encode_artist_exact(clip, data, base_prompt, sorted_artists, strength_scale=strength_scale)
        try:
            output.extend(
                _encode_artist_delta_rms(
                    clip,
                    data,
                    base_prompt,
                    tail,
                    weights=[weight / tail_total for _tag, weight in tail],
                    style_gain=style_gain,
                    rms_scale_cap=rms_scale_cap,
                    branch_strength=(tail_total / total_weight) * float(strength_scale),
                )
            )
        except Exception:
            return _encode_artist_exact(clip, data, base_prompt, sorted_artists, strength_scale=strength_scale)
    return output or _encode_artist_exact(clip, data, base_prompt, sorted_artists, strength_scale=strength_scale)


def _artist_conditioning_feature(torch, base_conditioning, encoded_artist, use_pooled: bool):
    if len(base_conditioning) != 1 or len(encoded_artist[2]) != 1:
        return None
    base_tensor, base_meta = base_conditioning[0]
    cond_tensor, metadata = encoded_artist[2][0]
    if not torch.is_tensor(base_tensor) or not torch.is_tensor(cond_tensor):
        return None
    base_pool = base_meta.get("pooled_output") if isinstance(base_meta, dict) else None
    pool = metadata.get("pooled_output") if isinstance(metadata, dict) else None
    if use_pooled and torch.is_tensor(base_pool) and torch.is_tensor(pool) and base_pool.shape == pool.shape:
        feature = (pool - base_pool).float().flatten()
    elif (
        base_tensor.ndim == 3
        and cond_tensor.ndim == 3
        and base_tensor.shape[0] == cond_tensor.shape[0]
        and base_tensor.shape[2] == cond_tensor.shape[2]
    ):
        max_length = max(base_tensor.shape[1], cond_tensor.shape[1])
        feature = (
            _pad_conditioning_tensor(cond_tensor, max_length)
            - _pad_conditioning_tensor(base_tensor, max_length)
        ).float().mean(dim=1).flatten()
    else:
        return None
    norm = torch.linalg.vector_norm(feature).clamp_min(1e-6)
    return feature / norm


def _greedy_cluster_encoded_artists(torch, encoded_artists: list, features: list, cluster_count: int) -> list:
    clusters = [
        {
            "items": [encoded],
            "weight": max(0.0, float(encoded[1])),
            "feature": feature,
        }
        for encoded, feature in zip(encoded_artists, features)
    ]
    target_count = max(1, min(int(cluster_count), len(clusters)))
    while len(clusters) > target_count:
        best_pair = (0, 1)
        best_similarity = None
        for left in range(len(clusters)):
            for right in range(left + 1, len(clusters)):
                similarity = torch.dot(clusters[left]["feature"], clusters[right]["feature"]).item()
                if best_similarity is None or similarity > best_similarity:
                    best_similarity = similarity
                    best_pair = (left, right)
        left, right = best_pair
        first = clusters[left]
        second = clusters[right]
        merged_weight = first["weight"] + second["weight"]
        merged_feature = first["feature"] * first["weight"] + second["feature"] * second["weight"]
        merged_norm = torch.linalg.vector_norm(merged_feature).clamp_min(1e-6)
        clusters[left] = {
            "items": [*first["items"], *second["items"]],
            "weight": merged_weight,
            "feature": merged_feature / merged_norm,
        }
        del clusters[right]
    return clusters


def _encode_artist_clustered(
    clip,
    data: dict[str, Any],
    base_prompt: str,
    artists: list[tuple[str, float]],
    cluster_count: int = ARTIST_MIX_DEFAULT_CLUSTER_COUNT,
    style_gain: float = ARTIST_MIX_DEFAULT_STYLE_GAIN,
    rms_scale_cap: float = ARTIST_MIX_DEFAULT_RMS_SCALE_CAP,
    dominant_isolation: bool = ARTIST_MIX_DEFAULT_DOMINANT_ISOLATION,
    dominant_threshold: float = ARTIST_MIX_DEFAULT_DOMINANT_THRESHOLD,
    strength_scale: float = ARTIST_MIX_DEFAULT_STRENGTH_SCALE,
) -> list:
    artists = _coalesce_artist_mix_items(artists)
    if not artists:
        return _encode_with_comfy_clip(clip, base_prompt)
    total_weight = sum(weight for _tag, weight in artists)
    if total_weight <= 0:
        return _encode_with_comfy_clip(clip, base_prompt)

    threshold = _bounded_artist_mix_float(
        dominant_threshold,
        ARTIST_MIX_DEFAULT_DOMINANT_THRESHOLD,
        0.0,
        1.0,
    )
    dominant = [
        (tag, weight)
        for tag, weight in artists
        if dominant_isolation and (weight / total_weight) >= threshold
    ]
    remaining = [
        (tag, weight)
        for tag, weight in artists
        if not dominant_isolation or (weight / total_weight) < threshold
    ]
    target_cluster_count = _bounded_artist_mix_int(
        cluster_count,
        ARTIST_MIX_DEFAULT_CLUSTER_COUNT,
        1,
        32,
    )
    output = []
    if dominant:
        output.extend(
            _encode_artist_exact(
                clip,
                data,
                base_prompt,
                dominant,
                branch_strengths=[
                    (weight / total_weight) * float(strength_scale)
                    for _tag, weight in dominant
                ],
            )
        )
    if not remaining:
        return output or _encode_artist_exact(clip, data, base_prompt, artists, strength_scale=strength_scale)
    if len(remaining) <= target_cluster_count:
        output.extend(
            _encode_artist_exact(
                clip,
                data,
                base_prompt,
                remaining,
                branch_strengths=[
                    (weight / total_weight) * float(strength_scale)
                    for _tag, weight in remaining
                ],
            )
        )
        return output

    try:
        import torch  # type: ignore

        base_conditioning = _encode_with_comfy_clip(clip, base_prompt)
        encoded = _encoded_artist_conditionings(clip, data, base_prompt, remaining)
        base_meta = base_conditioning[0][1] if len(base_conditioning) == 1 else {}
        base_pool = base_meta.get("pooled_output") if isinstance(base_meta, dict) else None
        use_pooled = torch.is_tensor(base_pool) and all(
            len(encoded_artist[2]) == 1
            and isinstance(encoded_artist[2][0][1], dict)
            and torch.is_tensor(encoded_artist[2][0][1].get("pooled_output"))
            and encoded_artist[2][0][1].get("pooled_output").shape == base_pool.shape
            for encoded_artist in encoded
        )
        features = [
            _artist_conditioning_feature(torch, base_conditioning, encoded_artist, use_pooled)
            for encoded_artist in encoded
        ]
        if any(feature is None for feature in features):
            raise RuntimeError("missing cluster feature")
        clusters = _greedy_cluster_encoded_artists(torch, encoded, features, target_cluster_count)
        for cluster in clusters:
            cluster_weight = max(0.0, float(cluster["weight"]))
            if cluster_weight <= 0:
                continue
            cluster_result = _artist_delta_rms_from_encoded(
                base_conditioning,
                cluster["items"],
                [item[1] / cluster_weight for item in cluster["items"]],
                None,
                style_gain=style_gain,
                rms_scale_cap=rms_scale_cap,
                branch_strength=(cluster_weight / total_weight) * float(strength_scale),
            )
            if cluster_result is None:
                raise RuntimeError("cluster delta_rms failed")
            output.extend(cluster_result)
        return output or _encode_artist_hybrid(
            clip,
            data,
            base_prompt,
            artists,
            exact_top_k=ARTIST_MIX_DEFAULT_EXACT_TOP_K,
            style_gain=style_gain,
            rms_scale_cap=rms_scale_cap,
            strength_scale=strength_scale,
        )
    except Exception:
        return _encode_artist_hybrid(
            clip,
            data,
            base_prompt,
            artists,
            exact_top_k=ARTIST_MIX_DEFAULT_EXACT_TOP_K,
            style_gain=style_gain,
            rms_scale_cap=rms_scale_cap,
            strength_scale=strength_scale,
        )


def _encode_artist_composite_exact(
    clip,
    data: dict[str, Any],
    base_prompt: str,
    artists: list[tuple[str, float]],
    start_percent: float | None = None,
    strength_scale: float = 1.0,
) -> list:
    composite_prompt = _artist_variant_prompt_from_prompt_data(
        data,
        base_prompt,
        _artist_mix_prompt_tags(artists, include_weights=True),
    )
    composite = _conditionings_with_strength(_encode_with_comfy_clip(clip, composite_prompt), 1.0)
    exact = _encode_artist_exact(
        clip,
        data,
        base_prompt,
        artists,
        start_percent=start_percent,
        end_percent=1.0 if start_percent is not None else None,
        strength_scale=strength_scale,
    )
    return composite + exact


def _encode_artist_average_late_exact(
    clip,
    data: dict[str, Any],
    base_prompt: str,
    artists: list[tuple[str, float]],
    artist_mix: dict[str, Any],
) -> list:
    late_start = _bounded_artist_mix_float(
        artist_mix.get("start_percent"),
        ARTIST_MIX_DEFAULT_START_PERCENT,
        0.0,
        1.0,
    )
    strength_scale = _bounded_artist_mix_float(
        artist_mix.get("strength_scale"),
        ARTIST_MIX_DEFAULT_STRENGTH_SCALE,
        0.0,
        5.0,
    )
    return _encode_artist_average(clip, data, base_prompt, artists) + _encode_artist_exact(
        clip,
        data,
        base_prompt,
        artists,
        start_percent=late_start,
        end_percent=1.0,
        strength_scale=strength_scale,
    )


def _encode_artist_scheduled_average(
    clip,
    data: dict[str, Any],
    base_prompt: str,
    artists: list[tuple[str, float]],
    artist_mix: dict[str, Any],
) -> list:
    late_start = _bounded_artist_mix_float(
        artist_mix.get("start_percent"),
        ARTIST_MIX_DEFAULT_START_PERCENT,
        0.0,
        1.0,
    )
    strength_scale = _bounded_artist_mix_float(
        artist_mix.get("strength_scale"),
        ARTIST_MIX_DEFAULT_STRENGTH_SCALE,
        0.0,
        5.0,
    )
    equal_weights = _equal_artist_weights(artists)
    target_weights = _normalized_artist_weights(artists)
    scheduled = []
    if late_start > 0.0:
        scheduled.extend(
            _mark_artist_mix_conditioning(
                _conditionings_with_range(
                    _encode_artist_average(clip, data, base_prompt, artists, weights=equal_weights),
                    0.0,
                    late_start,
                ),
                ARTIST_MIX_SCHEDULE_KEY,
            )
        )

    segments = 4
    span = max(0.0, 1.0 - late_start)
    for index in range(segments):
        segment_start = late_start + span * (index / segments)
        segment_end = late_start + span * ((index + 1) / segments)
        amount = (index + 1) / segments
        weights = _interpolate_artist_weights(equal_weights, target_weights, amount)
        base = _conditionings_with_range(
            _conditionings_with_strength(_encode_with_comfy_clip(clip, base_prompt), 1.0),
            segment_start,
            segment_end,
        )
        artist_only = _conditionings_with_range(
            _conditionings_with_strength(
                _encode_artist_average(clip, {}, "", artists, weights=weights),
                max(0.0, strength_scale) * amount,
            ),
            segment_start,
            segment_end,
        )
        scheduled.extend(_mark_artist_mix_conditioning(base + artist_only, ARTIST_MIX_SCHEDULE_KEY))
    return scheduled


def _encode_prompt_data_positive_conditioning(
    clip,
    data: dict[str, Any],
    positive_prompt: str,
    artist_mix_mode: str = ARTIST_MIX_MODE_FROM_PROMPT_DATA,
    artist_mix_start_percent: float = ARTIST_MIX_DEFAULT_START_PERCENT,
    artist_mix_strength_scale: float = ARTIST_MIX_DEFAULT_STRENGTH_SCALE,
    artist_mix_style_gain: float = ARTIST_MIX_DEFAULT_STYLE_GAIN,
    artist_mix_rms_scale_cap: float = ARTIST_MIX_DEFAULT_RMS_SCALE_CAP,
    artist_mix_exact_top_k: int = ARTIST_MIX_DEFAULT_EXACT_TOP_K,
    artist_mix_cluster_count: int = ARTIST_MIX_DEFAULT_CLUSTER_COUNT,
    artist_mix_dominant_isolation: bool = ARTIST_MIX_DEFAULT_DOMINANT_ISOLATION,
    artist_mix_dominant_threshold: float = ARTIST_MIX_DEFAULT_DOMINANT_THRESHOLD,
) -> list:
    artist_mix = _prompt_data_artist_mix_config(
        data,
        artist_mix_mode,
        artist_mix_start_percent,
        artist_mix_strength_scale,
        artist_mix_style_gain,
        artist_mix_rms_scale_cap,
        artist_mix_exact_top_k,
        artist_mix_cluster_count,
        artist_mix_dominant_isolation,
        artist_mix_dominant_threshold,
    )
    artists = _coalesce_artist_mix_items(_parse_artist_mix_items(str(artist_mix.get("artist_prompt") or "")))
    if not artist_mix.get("enabled") or artist_mix.get("mode") == ARTIST_MIX_MODE_PROMPT:
        return _encode_with_comfy_clip(clip, positive_prompt)

    base_prompt = _prompt_data_artist_base_prompt(data, positive_prompt)
    if not artists:
        return _encode_with_comfy_clip(clip, base_prompt)

    mode = _normalize_artist_mix_mode(artist_mix.get("mode"), ARTIST_MIX_MODE_PROMPT)
    if mode == ARTIST_MIX_MODE_AVERAGE:
        return _encode_artist_average(clip, data, base_prompt, artists)
    if mode == ARTIST_MIX_MODE_DELTA_RMS:
        return _mark_artist_mix_conditioning(
            _encode_artist_delta_rms(
                clip,
                data,
                base_prompt,
                artists,
                style_gain=_bounded_artist_mix_float(
                    artist_mix.get("style_gain"),
                    ARTIST_MIX_DEFAULT_STYLE_GAIN,
                    0.0,
                    3.0,
                ),
                rms_scale_cap=_bounded_artist_mix_float(
                    artist_mix.get("rms_scale_cap"),
                    ARTIST_MIX_DEFAULT_RMS_SCALE_CAP,
                    1.0,
                    5.0,
                ),
            ),
            ARTIST_MIX_CONTROL_KEY,
        )
    if mode == ARTIST_MIX_MODE_HYBRID:
        return _mark_artist_mix_conditioning(
            _encode_artist_hybrid(
                clip,
                data,
                base_prompt,
                artists,
                exact_top_k=_bounded_artist_mix_int(
                    artist_mix.get("exact_top_k"),
                    ARTIST_MIX_DEFAULT_EXACT_TOP_K,
                    0,
                    64,
                ),
                style_gain=_bounded_artist_mix_float(
                    artist_mix.get("style_gain"),
                    ARTIST_MIX_DEFAULT_STYLE_GAIN,
                    0.0,
                    3.0,
                ),
                rms_scale_cap=_bounded_artist_mix_float(
                    artist_mix.get("rms_scale_cap"),
                    ARTIST_MIX_DEFAULT_RMS_SCALE_CAP,
                    1.0,
                    5.0,
                ),
                strength_scale=_bounded_artist_mix_float(
                    artist_mix.get("strength_scale"),
                    ARTIST_MIX_DEFAULT_STRENGTH_SCALE,
                    0.0,
                    5.0,
                ),
            ),
            ARTIST_MIX_CONTROL_KEY,
        )
    if mode == ARTIST_MIX_MODE_CLUSTERED:
        return _mark_artist_mix_conditioning(
            _encode_artist_clustered(
                clip,
                data,
                base_prompt,
                artists,
                cluster_count=_bounded_artist_mix_int(
                    artist_mix.get("cluster_count"),
                    ARTIST_MIX_DEFAULT_CLUSTER_COUNT,
                    1,
                    32,
                ),
                style_gain=_bounded_artist_mix_float(
                    artist_mix.get("style_gain"),
                    ARTIST_MIX_DEFAULT_STYLE_GAIN,
                    0.0,
                    3.0,
                ),
                rms_scale_cap=_bounded_artist_mix_float(
                    artist_mix.get("rms_scale_cap"),
                    ARTIST_MIX_DEFAULT_RMS_SCALE_CAP,
                    1.0,
                    5.0,
                ),
                dominant_isolation=_as_bool(
                    artist_mix.get("dominant_isolation"),
                    ARTIST_MIX_DEFAULT_DOMINANT_ISOLATION,
                ),
                dominant_threshold=_bounded_artist_mix_float(
                    artist_mix.get("dominant_threshold"),
                    ARTIST_MIX_DEFAULT_DOMINANT_THRESHOLD,
                    0.0,
                    1.0,
                ),
                strength_scale=_bounded_artist_mix_float(
                    artist_mix.get("strength_scale"),
                    ARTIST_MIX_DEFAULT_STRENGTH_SCALE,
                    0.0,
                    5.0,
                ),
            ),
            ARTIST_MIX_CONTROL_KEY,
        )
    if mode == ARTIST_MIX_MODE_EXACT:
        return _mark_artist_mix_conditioning(
            _encode_artist_exact(
                clip,
                data,
                base_prompt,
                artists,
                strength_scale=_bounded_artist_mix_float(
                    artist_mix.get("strength_scale"),
                    ARTIST_MIX_DEFAULT_STRENGTH_SCALE,
                    0.0,
                    5.0,
                ),
            ),
            ARTIST_MIX_CONTROL_KEY,
        )
    if mode == ARTIST_MIX_MODE_COMPOSITE_EXACT:
        return _mark_artist_mix_conditioning(
            _encode_artist_composite_exact(
                clip,
                data,
                base_prompt,
                artists,
                strength_scale=_bounded_artist_mix_float(
                    artist_mix.get("strength_scale"),
                    ARTIST_MIX_DEFAULT_STRENGTH_SCALE,
                    0.0,
                    5.0,
                ),
            ),
            ARTIST_MIX_CONTROL_KEY,
        )
    if mode == ARTIST_MIX_MODE_LATE_EXACT:
        return _mark_artist_mix_conditioning(
            _encode_with_comfy_clip(clip, base_prompt) + _encode_artist_exact(
                clip,
                data,
                base_prompt,
                artists,
                start_percent=_bounded_artist_mix_float(
                    artist_mix.get("start_percent"),
                    ARTIST_MIX_DEFAULT_START_PERCENT,
                    0.0,
                    1.0,
                ),
                end_percent=1.0,
                strength_scale=_bounded_artist_mix_float(
                    artist_mix.get("strength_scale"),
                    ARTIST_MIX_DEFAULT_STRENGTH_SCALE,
                    0.0,
                    5.0,
                ),
            ),
            ARTIST_MIX_CONTROL_KEY,
        )
    if mode == ARTIST_MIX_MODE_AVERAGE_LATE_EXACT:
        return _mark_artist_mix_conditioning(
            _encode_artist_average_late_exact(clip, data, base_prompt, artists, artist_mix),
            ARTIST_MIX_CONTROL_KEY,
        )
    if mode == ARTIST_MIX_MODE_SCHEDULED_AVERAGE:
        return _mark_artist_mix_conditioning(
            _encode_artist_scheduled_average(clip, data, base_prompt, artists, artist_mix),
            ARTIST_MIX_CONTROL_KEY,
        )
    return _encode_with_comfy_clip(clip, positive_prompt)


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
            "text": positive_artist_prompt,
            "weighted_text": positive_artist_prompt,
            "tags": _artist_tags_from_prompt(positive_artist_prompt),
            "positive_prompt": positive_artist_prompt,
            "negative_prompt": negative_artist_prompt,
            "positive_prompt_without_artist": positive_without_artist,
            "negative_prompt_without_artist": negative_without_artist,
            "positive_count_hint": len(_prompt_tokens(positive_artist_prompt)),
            "negative_count_hint": len(_prompt_tokens(negative_artist_prompt)),
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
            "artist_count_hint": len(_prompt_tokens(positive_artist_prompt)),
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
            "mode": str(wildcard_mode or WILDCARD_MODE_LABELS[1]),
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


def _fit_to_1mp(width: int, height: int) -> tuple[int, int]:
    if width <= 0 or height <= 0:
        return width, height
    if width * height <= NAI_1MP:
        return width, height

    ratio = width / height
    target_w = (NAI_1MP * ratio) ** 0.5
    target_h = (NAI_1MP / ratio) ** 0.5
    new_w = max(LATENT_ALIGN, round(target_w / LATENT_ALIGN) * LATENT_ALIGN)
    new_h = max(LATENT_ALIGN, round(target_h / LATENT_ALIGN) * LATENT_ALIGN)
    while new_w * new_h > NAI_1MP and new_w > LATENT_ALIGN and new_h > LATENT_ALIGN:
        if new_w >= new_h:
            new_w -= LATENT_ALIGN
        else:
            new_h -= LATENT_ALIGN
    return new_w, new_h


def _post_random(host: str, port: int, body: dict) -> dict:
    try:
        import requests
    except ImportError:
        raise RuntimeError("[EasyUse Anima] requests is not installed. Install requirements.txt.")

    url = f"http://{host}:{int(port)}/api/comfyui/random"
    try:
        response = requests.post(url, json=body, timeout=HTTP_TIMEOUT)
    except requests.RequestException as exc:
        raise RuntimeError(f"[EasyUse Anima] NAIA API request failed: {exc}")

    if not response.ok:
        raise RuntimeError(
            f"[EasyUse Anima] NAIA API error HTTP {response.status_code}: {response.text[:300]}"
        )
    try:
        data = response.json()
    except ValueError:
        raise RuntimeError(f"[EasyUse Anima] NAIA API returned non-JSON: {response.text[:300]}")

    if not data.get("ok", True):
        raise RuntimeError(f"[EasyUse Anima] NAIA API returned error: {data}")
    return data


def _parse_random_response(resp: dict) -> tuple[str, str, int, int]:
    prompt = _clean_prompt(resp.get("prompt", "") or "")
    negative = _clean_prompt(resp.get("negative_prompt", "") or "")
    w_raw, h_raw = resp.get("width"), resp.get("height")
    if w_raw is None or h_raw is None:
        raise RuntimeError("[EasyUse Anima] NAIA response is missing width/height.")
    try:
        raw_width, raw_height = int(w_raw), int(h_raw)
    except (TypeError, ValueError):
        raise RuntimeError(f"[EasyUse Anima] Invalid NAIA width/height: {w_raw!r}, {h_raw!r}")
    width, height = _fit_to_1mp(raw_width, raw_height)
    return prompt, negative, width, height


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


def _profile_key(profile_index: int) -> str:
    return str(max(1, _as_int(profile_index, 1)))


def _wrap_profile_index(profile_index: int, profile_count: int) -> int:
    count = max(1, min(16, _as_int(profile_count, 1)))
    index = max(1, _as_int(profile_index, 1))
    return ((index - 1) % count) + 1


def _load_profile_data(profile_data: Any) -> dict[str, dict]:
    if isinstance(profile_data, dict):
        raw = profile_data
    else:
        try:
            raw = json.loads(str(profile_data or "{}"))
        except (TypeError, ValueError):
            raw = {}
    if not isinstance(raw, dict):
        return {}
    profiles: dict[str, dict] = {}
    for key, value in raw.items():
        if isinstance(value, dict):
            profiles[str(key)] = value
    return profiles


def _get_loras_list(kwargs: dict) -> list[dict]:
    loras_data = kwargs.get("loras")
    if isinstance(loras_data, dict) and "__value__" in loras_data:
        loras_data = loras_data["__value__"]
    if isinstance(loras_data, str):
        try:
            loras_data = json.loads(loras_data or "[]")
        except (TypeError, ValueError):
            loras_data = []
    if not isinstance(loras_data, list):
        return []
    return [item for item in loras_data if isinstance(item, dict)]


def _apply_lora_syntax_format(name: str) -> str:
    try:
        from py.nodes.utils import apply_lora_syntax_format  # type: ignore

        return str(apply_lora_syntax_format(name))
    except Exception:
        base_name = str(name).replace("\\", "/").rstrip("/").split("/")[-1]
        return os.path.splitext(base_name)[0]


def _fallback_lora_path(lora_name: str) -> str:
    try:
        import folder_paths  # type: ignore

        for candidate in (
            lora_name,
            f"{lora_name}.safetensors",
            f"{lora_name}.pt",
            f"{lora_name}.ckpt",
        ):
            path = folder_paths.get_full_path("loras", candidate)
            if path:
                return path
    except Exception:
        pass
    return lora_name


def _lora_stack_name(lora_name: str) -> str:
    value = str(lora_name or "").strip()
    if not value:
        return value

    try:
        import folder_paths  # type: ignore

        absolute_value = os.path.abspath(value)
        for root in folder_paths.get_folder_paths("loras"):
            absolute_root = os.path.abspath(root)
            try:
                relative = os.path.relpath(absolute_value, absolute_root)
            except ValueError:
                continue
            if relative == "." or relative.startswith(f"..{os.sep}") or relative == "..":
                continue
            return relative.replace("/", os.sep)
    except Exception:
        pass

    normalized = value.replace("\\", "/")
    marker = "/models/loras/"
    marker_index = normalized.casefold().rfind(marker)
    if marker_index >= 0:
        normalized = normalized[marker_index + len(marker):]
    return normalized.replace("/", os.sep)


def _dedupe_text_values(values) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        text = str(value or "").strip()
        if not text:
            continue
        key = text.casefold()
        if key in seen:
            continue
        seen.add(key)
        result.append(text)
    return result


def _trigger_words_from_value(value) -> list[str]:
    if isinstance(value, str):
        return _dedupe_text_values(_prompt_tokens(value))
    if isinstance(value, dict):
        for key in ("word", "name", "tag", "text"):
            if key in value:
                return _trigger_words_from_value(value.get(key))
        return []
    if isinstance(value, (list, tuple, set)):
        words: list[str] = []
        for item in value:
            words.extend(_trigger_words_from_value(item))
        return _dedupe_text_values(words)
    return []


def _metadata_json_paths_for_lora(lora_path: str) -> list[str]:
    path = str(lora_path or "").strip()
    if not path:
        return []
    base, _ext = os.path.splitext(path)
    candidates = [f"{base}.metadata.json", f"{path}.metadata.json"]
    return _dedupe_text_values(candidates)


def _load_lora_manager_metadata(lora_path: str) -> dict:
    for metadata_path in _metadata_json_paths_for_lora(lora_path):
        if not os.path.isfile(metadata_path):
            continue
        try:
            with open(metadata_path, "r", encoding="utf-8") as handle:
                data = json.load(handle)
        except (OSError, json.JSONDecodeError) as exc:
            logger.warning("[EasyUse Anima] failed to read LoRA metadata JSON %s: %s", metadata_path, exc)
            continue
        if isinstance(data, dict):
            return data
    return {}


def _lora_manager_trigger_words_from_metadata(metadata: dict) -> list[str]:
    if not isinstance(metadata, dict):
        return []

    words: list[str] = []
    for key in _TRIGGER_WORD_KEYS:
        words.extend(_trigger_words_from_value(metadata.get(key)))

    civitai = metadata.get("civitai")
    if isinstance(civitai, dict):
        for key in _TRIGGER_WORD_KEYS:
            words.extend(_trigger_words_from_value(civitai.get(key)))

    return _dedupe_text_values(words)


def _get_lora_manager_trigger_words(lora_path: str) -> list[str]:
    return _lora_manager_trigger_words_from_metadata(_load_lora_manager_metadata(lora_path))


def _get_lora_info(lora_name: str) -> tuple[str, list[str]]:
    fallback_path = _fallback_lora_path(lora_name)
    trigger_words = _get_lora_manager_trigger_words(fallback_path)
    if trigger_words:
        return fallback_path, trigger_words

    try:
        from py.utils.utils import get_lora_info  # type: ignore

        path, trigger_words = get_lora_info(lora_name)
        if not isinstance(trigger_words, list):
            trigger_words = []
        trigger_words = _dedupe_text_values(trigger_words)
        if trigger_words:
            return str(path), trigger_words
        json_trigger_words = _get_lora_manager_trigger_words(str(path))
        return str(path), json_trigger_words
    except Exception:
        return fallback_path, []


def _correct_style_prompt(prompt: str) -> str:
    return _correct_builder_prompt(prompt)



def _format_strength(value: float) -> str:
    text = f"{float(value):.6f}".rstrip("0").rstrip(".")
    return text or "0"


def _select_profile_values(
    profile_index: int,
    profile_count: int,
    profile_data: str,
    style_prompt: str,
    kwargs: dict,
) -> tuple[str, list[dict], int]:
    selected_index = _wrap_profile_index(profile_index, profile_count)
    profile = _load_profile_data(profile_data).get(_profile_key(selected_index), {})
    selected_style = str(profile.get("style_prompt", style_prompt or ""))
    profile_loras = profile.get("loras")
    if isinstance(profile_loras, list):
        loras = [item for item in profile_loras if isinstance(item, dict)]
    else:
        loras = _get_loras_list(kwargs)
    return selected_style, loras, selected_index


def _lora_combo_values() -> list[str]:
    try:
        import folder_paths  # type: ignore

        names = [str(name) for name in folder_paths.get_filename_list("loras")]
    except Exception:
        names = []
    values = ["None"]
    seen = {"none"}
    for name in names:
        text = str(name or "").strip()
        if not text:
            continue
        key = text.casefold()
        if key in seen:
            continue
        seen.add(key)
        values.append(text)
    return values


def _lora_model_exists(lora_name: str) -> bool | None:
    name = str(lora_name or "").strip()
    if not name or name == "None":
        return True

    try:
        import folder_paths  # type: ignore
    except Exception:
        return None

    candidates = _dedupe_text_values((
        name,
        name.replace("\\", "/"),
        name.replace("/", os.sep),
    ))
    for candidate in candidates:
        if folder_paths.get_full_path("loras", candidate):
            return True
    return False


def _missing_lora_display_name(input_name: str, stack_name: str) -> str:
    input_text = str(input_name or "").strip()
    stack_text = str(stack_name or "").strip()
    if not input_text or input_text == stack_text:
        return stack_text
    normalized_input = input_text.replace("\\", "/").casefold()
    normalized_stack = stack_text.replace("\\", "/").casefold()
    if normalized_input == normalized_stack:
        return stack_text
    return f"{stack_text} (input: {input_text})"


def _raise_missing_loras(profile_index: int, missing_loras: list[str]):
    if not missing_loras:
        return
    lines = "\n".join(f"- {name}" for name in missing_loras)
    message = (
        "[EasyUse Anima] LoRA Preset profile "
        f"{profile_index} contains missing LoRA model(s):\n"
        f"{lines}\n"
        "Install the missing file under ComfyUI/models/loras or remove it from the profile."
    )
    logger.error(message)
    raise RuntimeError(message)


class EasyUseAnimaPromptCorrector:
    """ANIMA prompt order correction node."""

    DESCRIPTION = (
        "Normalizes ANIMA prompt text, keeps natural-language casing, reorders known "
        "ANIMA sections, and reports unknown or duplicate tags."
    )
    OUTPUT_TOOLTIPS = (
        "Prompt text after ANIMA ordering and syntax cleanup.",
        "JSON report containing changed state, unknown tags, duplicate tags, warnings, and sections.",
    )

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "prompt": ("STRING", {
                    "multiline": True,
                    "default": "",
                    "tooltip": "Comma-separated prompt text to normalize and reorder for ANIMA.",
                }),
                "artist_overrides": ("STRING", {
                    "multiline": True,
                    "default": "",
                    "tooltip": "Comma- or newline-separated manual triggers to treat like artist tags.",
                }),
                "artist_exclusions": ("STRING", {
                    "multiline": True,
                    "default": "",
                    "tooltip": "Comma- or newline-separated triggers that must not be treated as artists.",
                }),
            }
        }

    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("corrected_prompt", "report")
    FUNCTION = "correct"
    CATEGORY = "EasyUse Anima/Prompt"

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        return _stable_change_key({
            "mode": "prompt_corrector",
            **{key: str(value) for key, value in sorted(kwargs.items())},
        })

    def correct(
        self,
        prompt: str,
        artist_overrides: str,
        artist_exclusions: str,
    ):
        try:
            kb = load_knowledge_base(allow_missing=True)
            result = correct_prompt(
                str(prompt or ""),
                profile="prompt",
                knowledge_base=kb,
                validate_artist_tags=False,
                artist_overrides=_split_tag_text(artist_overrides),
                artist_exclusions=_split_tag_text(artist_exclusions),
            )
        except Exception as exc:
            raise RuntimeError(f"[EasyUse Anima] prompt correction failed: {exc}") from exc

        report = {
            "changed": result.changed,
            "unknown_tags": list(result.unknown_tags),
            "duplicate_tags": list(result.duplicate_tags),
            "warnings": list(result.warnings),
            "sections": result.report.get("sections", []),
        }
        return (
            result.text,
            json.dumps(report, ensure_ascii=False, indent=2),
        )


class EasyUseAnimaWildcard:
    """Expand Impact Pack compatible wildcard and dynamic prompt syntax."""

    DESCRIPTION = (
        "Expands EasyUse Anima wildcard files and dynamic prompt syntax with fixed, sequential, "
        "and reproducible modes."
    )
    OUTPUT_TOOLTIPS = (
        "Expanded prompt text.",
        "Seed after applying the seed control option.",
    )

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "text": ("STRING", {
                    "multiline": True,
                    "default": "",
                    "tooltip": "Prompt text with wildcard syntax such as __style__ or {2::a|5::b|c}.",
                }),
                "populated_text": ("STRING", {
                    "multiline": True,
                    "default": "",
                    "tooltip": "Cached expanded prompt used by fixed and reproduce modes.",
                }),
                "mode": (WILDCARD_MODE_LABELS, {
                    "default": WILDCARD_MODE_LABELS[0],
                    "tooltip": (
                        "일반 채우기: seed-based random fill. 고정/재현: cached text. "
                        "순차: seed modulo each wildcard option count."
                    ),
                }),
                "seed": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": MAX_SEED,
                    "tooltip": "Wildcard seed. Sequential mode uses seed % option_count for each wildcard.",
                }),
                "seed_after_generate": (SEED_CONTROL_MODES, {
                    "default": SEED_CONTROL_FIXED,
                    "tooltip": "Seed control after generation: fixed, randomize, increment, or decrement.",
                }),
            },
            "hidden": {
                "workflow_prompt": "PROMPT",
                "extra_pnginfo": "EXTRA_PNGINFO",
                "unique_id": "UNIQUE_ID",
            },
        }

    RETURN_TYPES = ("STRING", "INT")
    RETURN_NAMES = ("text", "seed")
    FUNCTION = "generate"
    CATEGORY = "EasyUse Anima/Prompt"

    @classmethod
    def _widget_input_names(cls):
        return tuple(cls.INPUT_TYPES().get("required", {}).keys())

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        mode = normalize_wildcard_mode(kwargs.get("mode", WILDCARD_MODE_LABELS[0]))
        seed_control = str(kwargs.get("seed_after_generate", SEED_CONTROL_FIXED) or "")
        text = str(kwargs.get("text", "") or "")
        if (
            mode in {WILDCARD_MODE_POPULATE, WILDCARD_MODE_FIXED, WILDCARD_MODE_SEQUENTIAL}
            and seed_control == SEED_CONTROL_RANDOMIZE
            and has_wildcard_syntax(text)
        ):
            return float("nan")
        return _stable_change_key({
            "mode": "wildcard",
            "wildcard_sources": wildcard_sources_signature(),
            **{key: str(value) for key, value in sorted(kwargs.items())},
        })

    @classmethod
    def _update_metadata_cache(
        cls,
        workflow_prompt,
        extra_pnginfo,
        unique_id,
        populated_text: str,
        mode: str,
        seed: int,
    ) -> None:
        node_id = _single_value(unique_id)
        if node_id is None:
            return
        node_id = str(node_id)
        updates = {
            "populated_text": populated_text,
            "mode": mode,
            "seed": int(seed),
        }

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
    def _ui(
        populated_text: str,
        mode: str,
        seed: int,
        status: str,
        used_keys: tuple[str, ...],
        missing_keys: tuple[str, ...],
    ):
        return {
            "wildcard": [{
                "populated_text": populated_text,
                "mode": mode,
                "seed": seed,
                "status": status,
                "used_keys": list(used_keys),
                "missing_keys": list(missing_keys),
            }]
        }

    def generate(
        self,
        text: str,
        populated_text: str,
        mode: str,
        seed: int,
        seed_after_generate: str,
        workflow_prompt=None,
        extra_pnginfo=None,
        unique_id=None,
    ):
        mode_key = normalize_wildcard_mode(mode)
        seed_value = normalize_seed(seed)
        used_keys: tuple[str, ...] = ()
        missing_keys: tuple[str, ...] = ()

        if mode_key == WILDCARD_MODE_REPRODUCE:
            output_text = str(populated_text if populated_text else text or "")
            status = mode_key
            metadata_mode = str(mode or WILDCARD_MODE_LABELS[3])
        else:
            expansion = expand_wildcards(str(text or ""), seed=seed_value, mode=mode_key)
            output_text = expansion.text
            used_keys = expansion.used_keys
            missing_keys = expansion.missing_keys
            status = WILDCARD_MODE_SEQUENTIAL if mode_key == WILDCARD_MODE_SEQUENTIAL else mode_key
            metadata_mode = WILDCARD_MODE_LABELS[3]

        effective_seed_control = (
            SEED_CONTROL_INCREMENT
            if mode_key == WILDCARD_MODE_SEQUENTIAL
            else seed_after_generate
        )
        next_seed_value = next_seed(seed_value, effective_seed_control)
        self._update_metadata_cache(
            workflow_prompt,
            extra_pnginfo,
            unique_id,
            output_text,
            metadata_mode,
            seed_value,
        )
        return {
            "ui": self._ui(
                output_text,
                str(mode or WILDCARD_MODE_LABELS[0]),
                next_seed_value,
                status,
                used_keys,
                missing_keys,
            ),
            "result": (output_text, next_seed_value),
        }


class EasyUseAnimaPromptBuilder:
    """Build cleaned ANIMA prompts for NAIA and Anima Mod Guidance workflows."""

    DESCRIPTION = (
        "Combines quality, trigger, LoRA trigger, body, and trailing prompt fields into "
        "ANIMA-friendly prompt outputs, including metadata and Mod Guidance outputs."
    )
    OUTPUT_TOOLTIPS = (
        "Final positive prompt. When Mod Guidance is enabled, leading quality tags are excluded.",
        "Quality prompt text intended for Anima Mod Guidance.",
        "Boolean flag passed through for Anima Mod Guidance workflow control.",
        "Prompt text for metadata, independent from Mod Guidance routing and metadata filters.",
    )

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "use_anima_mod_guidance": ("BOOLEAN", {
                    "default": False,
                    "tooltip": (
                        "true: output prompt excludes quality fields and sends them "
                        "through anima_mod_guidance_quality_tags."
                    ),
                }),
                "pin_trigger_tags_to_front": ("BOOLEAN", {
                    "default": False,
                    "tooltip": (
                        "true: keep trigger/artist and LoRA trigger fields at the very front "
                        "instead of placing quality tags before them."
                    ),
                }),
                "lora_trigger_tags": ("STRING", {
                    "multiline": False,
                    "default": "",
                    "tooltip": "One-line trigger tags received from a LoRA manager or pasted manually.",
                }),
                "quality_tags": ("STRING", {
                    "multiline": True,
                    "default": DEFAULT_QUALITY_TAGS,
                    "tooltip": "Leading quality tags. With AMG enabled, these are excluded from prompt output.",
                }),
                "trigger_and_artist_tags": ("STRING", {
                    "multiline": True,
                    "default": "",
                    "tooltip": "Manual model triggers and @artist tags.",
                }),
                "prompt": ("STRING", {
                    "multiline": True,
                    "default": "",
                    "tooltip": "Main prompt body. This is the expected place for NAIA output.",
                }),
                "trailing_quality_tags": ("STRING", {
                    "multiline": True,
                    "default": DEFAULT_TRAILING_QUALITY_TAGS,
                    "tooltip": "Trailing quality or style tags.",
                }),
            }
        }

    RETURN_TYPES = ("STRING", "STRING", "BOOLEAN", "STRING")
    RETURN_NAMES = (
        "prompt",
        "anima_mod_guidance_quality_tags",
        "use_anima_mod_guidance",
        "metadata_prompt",
    )
    FUNCTION = "build"
    CATEGORY = "EasyUse Anima/Prompt"

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        return _stable_change_key({
            "mode": "prompt_builder",
            "metadata_filter_words": resolve_metadata_filter_words(),
            **{key: str(value) for key, value in sorted(kwargs.items())},
        })

    def build(
        self,
        use_anima_mod_guidance: bool,
        pin_trigger_tags_to_front: bool,
        quality_tags: str,
        trigger_and_artist_tags: str,
        lora_trigger_tags: str,
        prompt: str,
        trailing_quality_tags: str,
    ):
        use_amg = _as_bool(use_anima_mod_guidance, False)
        pin_triggers = _as_bool(pin_trigger_tags_to_front, False)

        trigger_prompt = _join_prompt_tokens(trigger_and_artist_tags, lora_trigger_tags)
        quality_prompt = _join_prompt_tokens(quality_tags)
        body_prompt = _join_prompt_tokens(prompt)
        trailing_prompt = _join_prompt_tokens(trailing_quality_tags)

        if pin_triggers:
            metadata_body = _correct_builder_prompt(
                _join_prompt_tokens(quality_tags, body_prompt)
            )
            regular_prompt = _join_prompt_tokens(trigger_prompt, metadata_body, trailing_prompt)
            amg_prompt = _join_prompt_tokens(
                trigger_prompt,
                _correct_builder_prompt(body_prompt),
                trailing_prompt,
            )
            metadata_prompt = regular_prompt
        else:
            metadata_core = _correct_builder_prompt(
                _join_prompt_tokens(
                    quality_tags,
                    trigger_prompt,
                    body_prompt,
                ),
                artist_overrides=trigger_prompt,
            )
            metadata_prompt = _join_prompt_tokens(metadata_core, trailing_prompt)
            regular_prompt = metadata_prompt
            amg_core = _correct_builder_prompt(
                _join_prompt_tokens(trigger_prompt, body_prompt),
                artist_overrides=trigger_prompt,
            )
            amg_prompt = _join_prompt_tokens(amg_core, trailing_prompt)

        metadata_prompt = _filter_metadata_prompt(
            metadata_prompt,
            resolve_metadata_filter_words(),
        )
        output_prompt = amg_prompt if use_amg else regular_prompt

        return (
            output_prompt,
            quality_prompt,
            use_amg,
            metadata_prompt,
        )


class EasyUseAnimaPromptStudio(EasyUseAnimaPromptBuilder):
    """Prompt Builder variant with enhanced front-end editing helpers."""

    DESCRIPTION = (
        "An enhanced Prompt Builder with front-end editing, autocomplete, and tag highlighting helpers."
    )

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "use_anima_mod_guidance": ("BOOLEAN", {
                    "default": False,
                    "tooltip": (
                        "true: output prompt excludes quality fields and sends them "
                        "through anima_mod_guidance_quality_tags."
                    ),
                }),
                "pin_trigger_tags_to_front": ("BOOLEAN", {
                    "default": False,
                    "tooltip": (
                        "true: keep trigger/artist and LoRA trigger fields at the very front "
                        "instead of placing quality tags before them."
                    ),
                }),
                "lora_trigger_tags": ("STRING", {
                    "multiline": False,
                    "default": "",
                    "tooltip": "One-line trigger tags received from a LoRA manager or pasted manually.",
                }),
                "quality_tags": ("STRING", {
                    "multiline": True,
                    "default": DEFAULT_QUALITY_TAGS,
                    "tooltip": "Leading quality tags. With AMG enabled, these are excluded from prompt output.",
                }),
                "trigger_and_artist_tags": ("STRING", {
                    "multiline": True,
                    "default": "",
                    "tooltip": "Manual model triggers and @artist tags.",
                }),
                "prompt": ("STRING", {
                    "multiline": True,
                    "default": "",
                    "tooltip": "Main prompt body. This is the expected place for NAIA output.",
                }),
                "trailing_quality_tags": ("STRING", {
                    "multiline": True,
                    "default": DEFAULT_TRAILING_QUALITY_TAGS,
                    "tooltip": "Trailing quality or style tags.",
                }),
            }
        }

    CATEGORY = "EasyUse Anima/Prompt"

    def build(
        self,
        use_anima_mod_guidance: bool,
        pin_trigger_tags_to_front: bool,
        quality_tags: str,
        trigger_and_artist_tags: str,
        lora_trigger_tags: str,
        prompt: str,
        trailing_quality_tags: str,
    ):
        result = super().build(
            use_anima_mod_guidance,
            pin_trigger_tags_to_front,
            quality_tags,
            trigger_and_artist_tags,
            lora_trigger_tags,
            prompt,
            trailing_quality_tags,
        )
        return {
            "ui": {
                "prompt_studio_inputs": [{
                    "lora_trigger_tags": str(lora_trigger_tags or ""),
                    "quality_tags": str(quality_tags or ""),
                    "trigger_and_artist_tags": str(trigger_and_artist_tags or ""),
                    "prompt": str(prompt or ""),
                    "trailing_quality_tags": str(trailing_quality_tags or ""),
                }]
            },
            "result": result,
        }


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
                "wildcard_mode": (WILDCARD_MODE_LABELS, {
                    "default": WILDCARD_MODE_LABELS[1],
                    "tooltip": "Wildcard mode. 고정 is the compatibility default; 순차 uses seed % option_count and increments seed after queue.",
                }),
                "wildcard_seed": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": MAX_SEED,
                    "tooltip": "Wildcard seed used by Advanced Prompt Studio fields.",
                }),
                "wildcard_seed_after_generate": (SEED_CONTROL_MODES, {
                    "default": SEED_CONTROL_FIXED,
                    "tooltip": "Seed control after wildcard generation.",
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
        wildcard_mode: str = WILDCARD_MODE_LABELS[1],
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
        wildcard_mode_key = normalize_wildcard_mode(wildcard_mode)
        wildcard_active = wildcard_mode_key in {WILDCARD_MODE_POPULATE, WILDCARD_MODE_FIXED, WILDCARD_MODE_SEQUENTIAL}
        wildcard_text = "\n".join(str(field.get("text") or "") for field in effective_fields)
        if (
            wildcard_active
            and str(wildcard_seed_after_generate or "") == SEED_CONTROL_RANDOMIZE
            and has_wildcard_syntax(wildcard_text)
        ):
            return float("nan")
        return _stable_change_key({
            "mode": "prompt_studio_advanced",
            "metadata_filter_words": resolve_metadata_filter_words(),
            "wildcard_sources": wildcard_sources_signature() if wildcard_active else {},
            "wildcard_mode": wildcard_mode_key,
            "wildcard_seed": normalize_seed(wildcard_seed),
            "wildcard_seed_after_generate": str(wildcard_seed_after_generate or SEED_CONTROL_FIXED),
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
        wildcard_mode: str = WILDCARD_MODE_LABELS[1],
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
        effective_fields = _apply_advanced_field_inputs(fields, field_inputs)
        effective_field_inputs = _advanced_field_input_values(field_inputs)
        requested_use_naia = _as_bool(use_naia, False)
        enabled_naia_panes = _advanced_enabled_naia_panes(fields)
        use_naia_resolution = _advanced_uses_naia_resolution(resolution_bucket)
        live_use_naia = requested_use_naia and (bool(enabled_naia_panes) or use_naia_resolution)
        metadata_use_naia = live_use_naia
        metadata_updates: dict[str, Any] = {}
        ui_updates: dict[str, Any] = {}
        wildcard_mode_key = normalize_wildcard_mode(wildcard_mode)
        wildcard_seed_value = normalize_seed(wildcard_seed)
        wildcard_effective_seed_control = (
            SEED_CONTROL_INCREMENT
            if wildcard_mode_key == WILDCARD_MODE_SEQUENTIAL
            else str(wildcard_seed_after_generate or SEED_CONTROL_FIXED)
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
            resp = _post_random(naia_settings["host"], naia_settings["port"], body)
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
        saved_fields, saved_wildcard = _expand_advanced_wildcard_fields(
            saved_fields,
            wildcard_seed_value,
            wildcard_mode_key,
        )
        effective_fields, effective_wildcard = _expand_advanced_wildcard_fields(
            effective_fields,
            wildcard_seed_value,
            wildcard_mode_key,
        )
        wildcard_changed = bool(saved_wildcard["changed"] or effective_wildcard["changed"])
        if wildcard_mode_key in {WILDCARD_MODE_POPULATE, WILDCARD_MODE_FIXED, WILDCARD_MODE_SEQUENTIAL}:
            next_wildcard_seed = next_seed(wildcard_seed_value, wildcard_effective_seed_control)
            ui_updates.update({
                "wildcard_mode": str(wildcard_mode or WILDCARD_MODE_LABELS[1]),
                "wildcard_seed": next_wildcard_seed,
                "wildcard_seed_after_generate": wildcard_effective_seed_control,
                "wildcard_used_keys": list(effective_wildcard["used_keys"]),
                "wildcard_missing_keys": list(effective_wildcard["missing_keys"]),
            })
            if wildcard_changed:
                metadata_updates.update({
                    "wildcard_mode": WILDCARD_MODE_LABELS[3],
                    "wildcard_seed": wildcard_seed_value,
                    "wildcard_seed_after_generate": SEED_CONTROL_FIXED,
                })

        fields_json = _advanced_fields_json(saved_fields)
        ui_fields_json = _advanced_fields_json(ui_fields if wildcard_changed else saved_fields)
        if live_use_naia or wildcard_changed:
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
        wildcard_mode: str = WILDCARD_MODE_LABELS[1],
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
        wildcard_mode: str = WILDCARD_MODE_LABELS[1],
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
        effective_fields = _apply_advanced_field_inputs(saved_fields, effective_field_inputs)
        effective_fields, _wildcard = _expand_advanced_wildcard_fields(
            effective_fields,
            normalize_seed(wildcard_seed),
            normalize_wildcard_mode(wildcard_mode),
        )
        prompt_data_parameters = _prompt_data_parameter_snapshot(
            self.INPUT_TYPES().get("required", {}),
            {
                "use_naia": use_naia,
                "consume_naia_on_queue": consume_naia_on_queue,
                "use_anima_mod_guidance": use_anima_mod_guidance,
                "pin_trigger_tags_to_front": pin_trigger_tags_to_front,
                "advanced_fields": advanced_fields,
                "use_negative_anima_mod_guidance": use_negative_anima_mod_guidance,
                "wildcard_mode": wildcard_mode,
                "wildcard_seed": wildcard_seed,
                "wildcard_seed_after_generate": wildcard_seed_after_generate,
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


class EasyUseAnimaPromptDataUnpack:
    """Expand EASYUSE_ANIMA_PROMPT_DATA into compatibility outputs."""

    DESCRIPTION = (
        "Expands an EASYUSE_ANIMA_PROMPT_DATA dict into Prompt Studio compatibility "
        "outputs, accepts optional override inputs, and passes prompt data through "
        "for context-style chaining."
    )
    OUTPUT_TOOLTIPS = (
        "Pass-through prompt data for downstream prompt-data nodes.",
        *EasyUseAnimaPromptStudioAdvanced.OUTPUT_TOOLTIPS,
    )

    @classmethod
    def INPUT_TYPES(cls):
        optional = {
            "positive_prompt": ("STRING", {
                "forceInput": True,
                "tooltip": "Optional override for prompt_data positive_prompt.",
            }),
            "negative_prompt": ("STRING", {
                "forceInput": True,
                "tooltip": "Optional override for prompt_data negative_prompt.",
            }),
            "anima_mod_guidance_quality_tags": ("STRING", {
                "forceInput": True,
                "tooltip": "Optional override for prompt_data Mod Guidance quality tags.",
            }),
            "anima_mod_guidance_negative_prompt": ("STRING", {
                "forceInput": True,
                "tooltip": "Optional override for prompt_data Mod Guidance negative prompt.",
            }),
            "use_anima_mod_guidance": ("BOOLEAN", {
                "forceInput": True,
                "tooltip": "Optional override for prompt_data Mod Guidance enabled flag.",
            }),
            "use_negative_anima_mod_guidance": ("BOOLEAN", {
                "forceInput": True,
                "tooltip": "Optional override for prompt_data negative Mod Guidance enabled flag.",
            }),
            "metadata_prompt": ("STRING", {
                "forceInput": True,
                "tooltip": "Optional override for prompt_data metadata_prompt.",
            }),
            "metadata_negative_prompt": ("STRING", {
                "forceInput": True,
                "tooltip": "Optional override for prompt_data metadata_negative_prompt.",
            }),
            "width": ("INT", {
                "forceInput": True,
                "tooltip": "Optional override for prompt_data latent width.",
            }),
            "height": ("INT", {
                "forceInput": True,
                "tooltip": "Optional override for prompt_data latent height.",
            }),
        }
        return {
            "required": {
                PROMPT_DATA_TYPE: (PROMPT_DATA_TYPE, {
                    "forceInput": True,
                    "tooltip": "Structured prompt data from Anima Prompt Studio Advanced v2.",
                }),
            },
            "optional": optional,
        }

    RETURN_TYPES = (PROMPT_DATA_TYPE, *EasyUseAnimaPromptStudioAdvanced.RETURN_TYPES)
    RETURN_NAMES = (PROMPT_DATA_TYPE, *EasyUseAnimaPromptStudioAdvanced.RETURN_NAMES)
    FUNCTION = "unpack"
    CATEGORY = "EasyUse Anima/Prompt"

    @classmethod
    def IS_CHANGED(
        cls,
        EASYUSE_ANIMA_PROMPT_DATA: str | dict | None = None,
        prompt_data: str | dict | None = None,
        **kwargs,
    ):
        data = EASYUSE_ANIMA_PROMPT_DATA if EASYUSE_ANIMA_PROMPT_DATA is not None else prompt_data
        return _stable_change_key({
            "mode": "prompt_data_unpack",
            "prompt_data": _apply_prompt_data_overrides(data, kwargs),
        })

    def unpack(
        self,
        EASYUSE_ANIMA_PROMPT_DATA: str | dict | None = None,
        prompt_data: str | dict | None = None,
        **overrides,
    ):
        data = _apply_prompt_data_overrides(
            EASYUSE_ANIMA_PROMPT_DATA if EASYUSE_ANIMA_PROMPT_DATA is not None else prompt_data,
            overrides,
        )
        return (data, *_advanced_outputs_from_prompt_data(data))


class EasyUseAnimaArtistMixConditioning:
    """Standalone artist-tag positioning and artist mix CONDITIONING node."""

    DESCRIPTION = (
        "Applies artist tags to a regular prompt, positions them with ANIMA ordering "
        "or fixed front/back placement, and outputs positive CONDITIONING. Artist mix "
        "modes can be used without Prompt Studio prompt data."
    )
    OUTPUT_TOOLTIPS = (
        "Positive CONDITIONING encoded from prompt plus artist tags.",
    )

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "clip": ("CLIP", {
                    "tooltip": "CLIP used to encode the prompt and artist tags.",
                }),
                "prompt": ("STRING", {
                    "multiline": True,
                    "default": "",
                    "tooltip": "Base positive prompt without the standalone artist tags.",
                }),
                "artist_tags": ("STRING", {
                    "multiline": True,
                    "default": "",
                    "tooltip": "Comma- or newline-separated artist tags. Weighted syntax such as (artist:1.2) is supported.",
                }),
                "artist_position": (list(ARTIST_TAG_POSITION_MODES), {
                    "default": ARTIST_TAG_POSITION_CORRECT,
                    "tooltip": (
                        "correct applies ANIMA prompt ordering, front pins artists before "
                        "the prompt, and back pins artists after the prompt."
                    ),
                }),
                "artist_mix_mode": (list(ARTIST_MIX_MODES), {
                    "default": ARTIST_MIX_MODE_PROMPT,
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
            },
        }

    RETURN_TYPES = ("CONDITIONING",)
    RETURN_NAMES = ("positive",)
    FUNCTION = "encode"
    CATEGORY = "EasyUse Anima/Prompt"

    @classmethod
    def IS_CHANGED(
        cls,
        prompt: str = "",
        artist_tags: str = "",
        artist_position: str = ARTIST_TAG_POSITION_CORRECT,
        artist_mix_mode: str = ARTIST_MIX_MODE_PROMPT,
        artist_mix_start_percent: float = ARTIST_MIX_DEFAULT_START_PERCENT,
        artist_mix_strength_scale: float = ARTIST_MIX_DEFAULT_STRENGTH_SCALE,
        artist_mix_style_gain: float = ARTIST_MIX_DEFAULT_STYLE_GAIN,
        artist_mix_rms_scale_cap: float = ARTIST_MIX_DEFAULT_RMS_SCALE_CAP,
        artist_mix_exact_top_k: int = ARTIST_MIX_DEFAULT_EXACT_TOP_K,
        artist_mix_cluster_count: int = ARTIST_MIX_DEFAULT_CLUSTER_COUNT,
        artist_mix_dominant_isolation: bool = ARTIST_MIX_DEFAULT_DOMINANT_ISOLATION,
        artist_mix_dominant_threshold: float = ARTIST_MIX_DEFAULT_DOMINANT_THRESHOLD,
        **_kwargs,
    ):
        return _stable_change_key({
            "mode": "artist_mix_conditioning",
            "prompt": str(prompt or ""),
            "artist_tags": str(artist_tags or ""),
            "artist_position": _normalize_artist_tag_position(artist_position),
            "artist_mix_mode": _normalize_artist_mix_mode(artist_mix_mode, ARTIST_MIX_MODE_PROMPT),
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

    def encode(
        self,
        clip,
        prompt: str = "",
        artist_tags: str = "",
        artist_position: str = ARTIST_TAG_POSITION_CORRECT,
        artist_mix_mode: str = ARTIST_MIX_MODE_PROMPT,
        artist_mix_start_percent: float = ARTIST_MIX_DEFAULT_START_PERCENT,
        artist_mix_strength_scale: float = ARTIST_MIX_DEFAULT_STRENGTH_SCALE,
        artist_mix_style_gain: float = ARTIST_MIX_DEFAULT_STYLE_GAIN,
        artist_mix_rms_scale_cap: float = ARTIST_MIX_DEFAULT_RMS_SCALE_CAP,
        artist_mix_exact_top_k: int = ARTIST_MIX_DEFAULT_EXACT_TOP_K,
        artist_mix_cluster_count: int = ARTIST_MIX_DEFAULT_CLUSTER_COUNT,
        artist_mix_dominant_isolation: bool = ARTIST_MIX_DEFAULT_DOMINANT_ISOLATION,
        artist_mix_dominant_threshold: float = ARTIST_MIX_DEFAULT_DOMINANT_THRESHOLD,
    ):
        position = _normalize_artist_tag_position(artist_position)
        mode = _normalize_artist_mix_mode(artist_mix_mode, ARTIST_MIX_MODE_PROMPT)
        base_prompt = _join_prompt_tokens(prompt)
        artist_prompt = _join_prompt_tokens(artist_tags)
        if mode == ARTIST_MIX_MODE_PROMPT:
            return (_encode_with_comfy_clip(
                clip,
                _artist_prompt_with_position(base_prompt, artist_prompt, position),
            ),)

        prompt_data = {
            "positive_prompt": base_prompt,
            "positive_without_artist_section": base_prompt,
            "artist_position": position,
            "artist_mix": {
                "enabled": True,
                "mode": mode,
                "artist_position": position,
                "base_source": "positive_without_artist_section",
                "base_prompt": base_prompt,
                "artist_prompt": artist_prompt,
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
            },
        }
        return (_encode_prompt_data_positive_conditioning(
            clip,
            prompt_data,
            base_prompt,
            artist_mix_mode=mode,
            artist_mix_start_percent=artist_mix_start_percent,
            artist_mix_strength_scale=artist_mix_strength_scale,
            artist_mix_style_gain=artist_mix_style_gain,
            artist_mix_rms_scale_cap=artist_mix_rms_scale_cap,
            artist_mix_exact_top_k=artist_mix_exact_top_k,
            artist_mix_cluster_count=artist_mix_cluster_count,
            artist_mix_dominant_isolation=artist_mix_dominant_isolation,
            artist_mix_dominant_threshold=artist_mix_dominant_threshold,
        ),)


class EasyUseAnimaPromptDataConditioning:
    """Encode EASYUSE_ANIMA_PROMPT_DATA and apply prompt-driven model patches."""

    DESCRIPTION = (
        "Reads EASYUSE_ANIMA_PROMPT_DATA by dict keys, encodes positive and negative "
        "CONDITIONING with CLIP, and applies comfyui-spectrum-ksampler Anima Mod "
        "Guidance to the MODEL when enabled. It also creates an empty latent image "
        "from prompt-data width and height with batch size fixed to 1. Artist mix "
        "modes use Advanced artist fields as artist data and rebuild artist variants "
        "through the Anima prompt ordering rules."
    )
    OUTPUT_TOOLTIPS = (
        "MODEL after prompt-data model patches.",
        "Positive CONDITIONING encoded from prompt data.",
        "Negative CONDITIONING encoded from prompt data.",
        "Empty latent image created from prompt-data width and height with batch size 1.",
    )

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "model": ("MODEL", {
                    "tooltip": "MODEL to pass through or patch with Anima Mod Guidance.",
                }),
                "clip": ("CLIP", {
                    "tooltip": "CLIP used to encode prompt data and Mod Guidance quality tags.",
                }),
                PROMPT_DATA_TYPE: (PROMPT_DATA_TYPE, {
                    "forceInput": True,
                    "tooltip": "Structured prompt data from Anima Prompt Studio Advanced v2.",
                }),
                "mod_guidance_mode": (list(ANIMA_MOD_GUIDANCE_MODES), {
                    "default": ANIMA_MOD_GUIDANCE_MODE_FROM_PROMPT_DATA,
                    "tooltip": (
                        "prompt_data uses the prompt-data boolean, enabled forces Anima "
                        "Mod Guidance on, and disabled bypasses the model patch."
                    ),
                }),
                "mod_w_profile": (list(ANIMA_MOD_GUIDANCE_PROFILES), {
                    "default": ANIMA_MOD_GUIDANCE_DEFAULT_PROFILE,
                    "tooltip": (
                        "Spectrum AnimaModGuidance per-block profile. off bypasses "
                        "the model patch."
                    ),
                }),
                "artist_mix_mode": (list(ARTIST_MIX_INPUT_MODES), {
                    "default": ARTIST_MIX_MODE_FROM_PROMPT_DATA,
                    "tooltip": _artist_mix_mode_tooltip(include_prompt_data=True),
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
            },
        }

    RETURN_TYPES = ("MODEL", "CONDITIONING", "CONDITIONING", "LATENT")
    RETURN_NAMES = ("model", "positive", "negative", "latent_image")
    FUNCTION = "apply"
    CATEGORY = "EasyUse Anima/Prompt"

    @classmethod
    def IS_CHANGED(
        cls,
        EASYUSE_ANIMA_PROMPT_DATA: str | dict | None = None,
        mod_guidance_mode: str = ANIMA_MOD_GUIDANCE_MODE_FROM_PROMPT_DATA,
        mod_w_profile: str = ANIMA_MOD_GUIDANCE_DEFAULT_PROFILE,
        artist_mix_mode: str = ARTIST_MIX_MODE_FROM_PROMPT_DATA,
        artist_mix_start_percent: float = ARTIST_MIX_DEFAULT_START_PERCENT,
        artist_mix_strength_scale: float = ARTIST_MIX_DEFAULT_STRENGTH_SCALE,
        artist_mix_style_gain: float = ARTIST_MIX_DEFAULT_STYLE_GAIN,
        artist_mix_rms_scale_cap: float = ARTIST_MIX_DEFAULT_RMS_SCALE_CAP,
        artist_mix_exact_top_k: int = ARTIST_MIX_DEFAULT_EXACT_TOP_K,
        artist_mix_cluster_count: int = ARTIST_MIX_DEFAULT_CLUSTER_COUNT,
        artist_mix_dominant_isolation: bool = ARTIST_MIX_DEFAULT_DOMINANT_ISOLATION,
        artist_mix_dominant_threshold: float = ARTIST_MIX_DEFAULT_DOMINANT_THRESHOLD,
        **kwargs,
    ):
        return _stable_change_key({
            "mode": "prompt_data_conditioning",
            "prompt_data": _normalize_prompt_data(EASYUSE_ANIMA_PROMPT_DATA),
            "mod_guidance_mode": str(mod_guidance_mode or ANIMA_MOD_GUIDANCE_MODE_FROM_PROMPT_DATA),
            "mod_w_profile": _normalize_anima_mod_guidance_profile(mod_w_profile),
            "artist_mix_mode": str(artist_mix_mode or ARTIST_MIX_MODE_FROM_PROMPT_DATA),
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

    def apply(
        self,
        model,
        clip,
        EASYUSE_ANIMA_PROMPT_DATA: str | dict,
        mod_guidance_mode: str = ANIMA_MOD_GUIDANCE_MODE_FROM_PROMPT_DATA,
        mod_w_profile: str = ANIMA_MOD_GUIDANCE_DEFAULT_PROFILE,
        artist_mix_mode: str = ARTIST_MIX_MODE_FROM_PROMPT_DATA,
        artist_mix_start_percent: float = ARTIST_MIX_DEFAULT_START_PERCENT,
        artist_mix_strength_scale: float = ARTIST_MIX_DEFAULT_STRENGTH_SCALE,
        artist_mix_style_gain: float = ARTIST_MIX_DEFAULT_STYLE_GAIN,
        artist_mix_rms_scale_cap: float = ARTIST_MIX_DEFAULT_RMS_SCALE_CAP,
        artist_mix_exact_top_k: int = ARTIST_MIX_DEFAULT_EXACT_TOP_K,
        artist_mix_cluster_count: int = ARTIST_MIX_DEFAULT_CLUSTER_COUNT,
        artist_mix_dominant_isolation: bool = ARTIST_MIX_DEFAULT_DOMINANT_ISOLATION,
        artist_mix_dominant_threshold: float = ARTIST_MIX_DEFAULT_DOMINANT_THRESHOLD,
    ):
        prompt_data = _normalize_prompt_data(EASYUSE_ANIMA_PROMPT_DATA)
        (
            positive_prompt,
            negative_prompt,
            quality_tags,
            quality_neg,
            use_anima_mod_guidance,
            use_negative_anima_mod_guidance,
            _metadata_prompt,
            _metadata_negative_prompt,
            width,
            height,
        ) = _advanced_outputs_from_prompt_data(EASYUSE_ANIMA_PROMPT_DATA)

        positive = _encode_prompt_data_positive_conditioning(
            clip,
            prompt_data,
            positive_prompt,
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
        negative = _encode_with_comfy_clip(clip, negative_prompt)
        latent_image = _generate_empty_latent_with_comfy(width, height)
        profile = _normalize_anima_mod_guidance_profile(mod_w_profile)
        use_mod_guidance = _resolve_anima_mod_guidance_enabled(
            use_anima_mod_guidance,
            str(mod_guidance_mode or ANIMA_MOD_GUIDANCE_MODE_FROM_PROMPT_DATA),
        )

        patched_model = model
        if use_mod_guidance and profile != ANIMA_MOD_GUIDANCE_PROFILE_OFF:
            patched_model = _apply_spectrum_anima_mod_guidance(
                model,
                clip,
                positive,
                negative,
                quality_tags,
                quality_neg if use_negative_anima_mod_guidance else "",
                profile,
            )

        return (patched_model, positive, negative, latent_image)


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
            _metadata_prompt,
            _metadata_negative_prompt,
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
        profile = _normalize_anima_mod_guidance_profile(mod_guidance["profile"])
        use_mod_guidance = _resolve_anima_mod_guidance_enabled(
            use_anima_mod_guidance,
            mod_guidance["mode"],
        )
        sampler_backend = str(sampler.get("backend") or "comfy_ksampler")
        needs_standalone_mod_guidance_model = (
            sampler_backend != "spectrum_mod_guidance_advanced"
            or will_run_highres
            or will_run_detailer
        )
        mod_guidance_model = model
        if (
            use_mod_guidance
            and profile != ANIMA_MOD_GUIDANCE_PROFILE_OFF
            and needs_standalone_mod_guidance_model
        ):
            mod_guidance_model = _apply_spectrum_anima_mod_guidance(
                model,
                clip,
                positive,
                negative,
                quality_tags,
                quality_neg if use_negative_anima_mod_guidance else "",
                profile,
            )
        base_sample_model = model if sampler_backend == "spectrum_mod_guidance_advanced" else mod_guidance_model
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
                    use_mod_guidance,
                    quality_tags,
                    quality_neg if use_negative_anima_mod_guidance else "",
                )
                image = _decode_latent_with_comfy(vae, latent)
                try:
                    _put_aio_first_pass_cache(first_pass_cache_key, latent, image)
                except Exception as exc:
                    logger.debug("[EasyUseAnima] failed to store AiO first-pass cache: %s", exc)
            stage_metadata["first_pass"] = {"cache_hit": first_pass_cache_hit}
            if preview_settings["intermediate_images"]:
                add_preview("first_pass", image)
            latent, image, width, height, highres_metadata = _run_aio_highres_stage(
                mod_guidance_model,
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
            )
            stage_metadata["highres"] = highres_metadata
            if highres_metadata.get("enabled") and isinstance(highres_metadata.get("sampler"), dict):
                if preview_settings["intermediate_images"] and will_run_detailer:
                    add_preview("highres", image)
            image, detailer_metadata = _run_aio_detailer_stage(
                mod_guidance_model,
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
                    positive_prompt=positive_prompt,
                    negative_prompt=negative_prompt,
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
                "wildcard_mode": (WILDCARD_MODE_LABELS, {
                    "default": WILDCARD_MODE_LABELS[1],
                    "tooltip": "Wildcard mode for prompt fields.",
                }),
                "wildcard_seed": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": MAX_SEED,
                    "tooltip": "Wildcard seed used by Regional Prompt Studio fields.",
                }),
                "wildcard_seed_after_generate": (SEED_CONTROL_MODES, {
                    "default": SEED_CONTROL_FIXED,
                    "tooltip": "Seed control after wildcard generation.",
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
        wildcard_mode: str = WILDCARD_MODE_LABELS[1],
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
        wildcard_mode_key = normalize_wildcard_mode(wildcard_mode)
        wildcard_active = wildcard_mode_key in {WILDCARD_MODE_POPULATE, WILDCARD_MODE_FIXED, WILDCARD_MODE_SEQUENTIAL}
        wildcard_text = "\n".join(str(field.get("text") or "") for field in effective_fields)
        if (
            wildcard_active
            and str(wildcard_seed_after_generate or "") == SEED_CONTROL_RANDOMIZE
            and has_wildcard_syntax(wildcard_text)
        ):
            return float("nan")
        return _stable_change_key({
            "mode": "prompt_studio_regional",
            "metadata_filter_words": resolve_metadata_filter_words(),
            "wildcard_sources": wildcard_sources_signature() if wildcard_active else {},
            "wildcard_mode": wildcard_mode_key,
            "wildcard_seed": normalize_seed(wildcard_seed),
            "wildcard_seed_after_generate": str(wildcard_seed_after_generate or SEED_CONTROL_FIXED),
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
        wildcard_mode: str = WILDCARD_MODE_LABELS[1],
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
        effective_fields = _apply_regional_field_inputs(fields, field_inputs)
        effective_field_inputs = _advanced_field_input_values(field_inputs)
        config = _normalize_regional_config(regional_config, width, height)

        wildcard_mode_key = normalize_wildcard_mode(wildcard_mode)
        wildcard_seed_value = normalize_seed(wildcard_seed)
        wildcard_effective_seed_control = (
            SEED_CONTROL_INCREMENT
            if wildcard_mode_key == WILDCARD_MODE_SEQUENTIAL
            else str(wildcard_seed_after_generate or SEED_CONTROL_FIXED)
        )
        ui_updates: dict[str, Any] = {}
        metadata_updates: dict[str, Any] = {}

        saved_fields, saved_wildcard = _expand_advanced_wildcard_fields(
            saved_fields,
            wildcard_seed_value,
            wildcard_mode_key,
        )
        effective_fields, effective_wildcard = _expand_advanced_wildcard_fields(
            effective_fields,
            wildcard_seed_value,
            wildcard_mode_key,
        )
        wildcard_changed = bool(saved_wildcard["changed"] or effective_wildcard["changed"])
        if wildcard_mode_key in {WILDCARD_MODE_POPULATE, WILDCARD_MODE_FIXED, WILDCARD_MODE_SEQUENTIAL}:
            next_wildcard_seed = next_seed(wildcard_seed_value, wildcard_effective_seed_control)
            ui_updates.update({
                "wildcard_mode": str(wildcard_mode or WILDCARD_MODE_LABELS[1]),
                "wildcard_seed": next_wildcard_seed,
                "wildcard_seed_after_generate": wildcard_effective_seed_control,
                "wildcard_used_keys": list(effective_wildcard["used_keys"]),
                "wildcard_missing_keys": list(effective_wildcard["missing_keys"]),
            })
            if wildcard_changed:
                metadata_updates.update({
                    "wildcard_mode": WILDCARD_MODE_LABELS[3],
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
            resp = _post_random(naia_settings["host"], naia_settings["port"], body)
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

        result = _build_advanced_prompts(
            self._fields_from_slots(values, active_slots),
            use_anima_mod_guidance,
            use_negative_anima_mod_guidance,
            pin_trigger_tags_to_front,
        )
        return {
            "ui": self._ui(values, live_fill_naia, active_slots),
            "result": result,
        }


class EasyUseAnimaLoraPreset:
    """Multi-profile LoRA stack preset node for ANIMA style prompts."""

    DESCRIPTION = (
        "Stores multiple ANIMA LoRA preset profiles, builds a LoRA stack, emits trigger words, "
        "and preserves profile data in workflow metadata."
    )
    OUTPUT_TOOLTIPS = (
        "Corrected style prompt for artist tags, model triggers, or short style directions.",
        "LoRA stack compatible with LoRA stack loaders.",
        "Trigger words collected from selected LoRA metadata.",
        "Text representation of enabled LoRAs and strengths.",
        "Currently selected profile index after wrapping to the available profile count.",
    )

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "style_prompt": ("STRING", {
                    "multiline": True,
                    "default": "",
                    "tooltip": "Style prompt for artist tags, model triggers, or short style directions.",
                }),
                "profile_index": ("INT", {
                    "default": 1,
                    "min": 1,
                    "max": 16,
                    "step": 1,
                    "tooltip": "Selected LoRA preset profile. Can be connected from another node.",
                }),
                "profile_count": ("STRING", {
                    "default": "4",
                    "tooltip": "Internal profile count managed by the front-end profile buttons.",
                }),
                "lora_name": (_lora_combo_values(), {
                    "default": "None",
                    "tooltip": "Internal LoRA selector source. Hidden by the EasyUse Anima front-end.",
                }),
                "loras": ("STRING", {
                    "multiline": True,
                    "default": "[]",
                    "tooltip": "Internal serialized LoRA rows for the selected profile.",
                }),
                "profile_data": ("STRING", {
                    "multiline": True,
                    "default": "{}",
                    "tooltip": "Internal serialized profile data.",
                }),
            },
            "optional": _FlexibleOptionalInputType(_ANY_TYPE),
        }

    RETURN_TYPES = ("STRING", "LORA_STACK", "STRING", "STRING", "INT")
    RETURN_NAMES = ("style_prompt", "LORA_STACK", "trigger_words", "active_loras", "profile_index")
    FUNCTION = "build"
    CATEGORY = "EasyUse Anima/LoRA"

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        return _stable_change_key({
            "mode": "lora_preset",
            **{key: str(value) for key, value in sorted(kwargs.items())},
        })

    def build(
        self,
        style_prompt: str,
        profile_index: int,
        profile_count=4,
        lora_name: str = "None",
        loras="[]",
        profile_data: str = "{}",
        **kwargs,
    ):
        kwargs = dict(kwargs)
        if loras is not None:
            kwargs["loras"] = loras

        selected_style, selected_loras, selected_index = _select_profile_values(
            profile_index,
            profile_count,
            profile_data,
            style_prompt,
            kwargs,
        )
        corrected_style = _correct_style_prompt(selected_style)

        stack = []
        trigger_words: list[str] = []
        active_loras: list[tuple[str, float, float]] = []

        lora_stack = kwargs.get("lora_stack")
        if lora_stack:
            stack.extend(lora_stack)
            for lora_path, _model_strength, _clip_strength in lora_stack:
                lora_base = os.path.splitext(os.path.basename(str(lora_path).replace("\\", "/")))[0]
                _path, existing_trigger_words = _get_lora_info(lora_base)
                trigger_words.extend(existing_trigger_words)

        seen: set[tuple[str, float, float]] = set()
        missing_loras: list[str] = []
        for lora in selected_loras:
            enabled_value = lora.get("on", lora.get("active", True))
            if not _as_bool(enabled_value, True):
                continue
            raw_name = str(lora.get("name", lora.get("lora", ""))).strip()
            if not raw_name or raw_name == "None":
                continue
            lora_name = raw_name.replace("\\", "/")
            active_lora_name = _apply_lora_syntax_format(lora_name)
            try:
                model_strength = float(lora.get("strength", 1.0))
            except (TypeError, ValueError):
                model_strength = 1.0
            clip_raw = lora.get("strengthTwo", lora.get("clipStrength", model_strength))
            try:
                clip_strength = float(clip_raw if clip_raw is not None else model_strength)
            except (TypeError, ValueError):
                clip_strength = model_strength

            stack_lora_name = _lora_stack_name(lora_name)
            dedupe_key = (stack_lora_name, model_strength, clip_strength)
            if dedupe_key in seen:
                continue
            seen.add(dedupe_key)

            if _lora_model_exists(stack_lora_name) is False:
                missing_loras.append(_missing_lora_display_name(raw_name, stack_lora_name))
                continue

            _lora_path, lora_trigger_words = _get_lora_info(lora_name)
            stack.append((stack_lora_name, model_strength, clip_strength))
            trigger_words.extend(lora_trigger_words)
            active_loras.append((active_lora_name, model_strength, clip_strength))

        _raise_missing_loras(selected_index, missing_loras)

        active_loras_text_parts = []
        for name, model_strength, clip_strength in active_loras:
            model_text = _format_strength(model_strength)
            clip_text = _format_strength(clip_strength)
            if abs(model_strength - clip_strength) > 0.001:
                active_loras_text_parts.append(f"<lora:{name}:{model_text}:{clip_text}>")
            else:
                active_loras_text_parts.append(f"<lora:{name}:{model_text}>")

        return {
            "ui": {
                "lora_preset_profile": [{
                    "profile_index": selected_index,
                }],
            },
            "result": (
                corrected_style,
                stack,
                ", ".join(trigger_words) if trigger_words else "",
                " ".join(active_loras_text_parts),
                selected_index,
            ),
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


class EasyUseAnimaImageScaleByMultiple:
    """Scale an image by the nearest ratio that produces valid size multiples."""

    DESCRIPTION = (
        "Scales an IMAGE by the nearest valid ratio that keeps the source aspect ratio and makes "
        "the output width and height multiples of the selected size. The optional max long edge "
        "limits the selected valid output size. Use multiple 32 for highres or optimization nodes "
        "that require 32-multiple sizes."
    )
    OUTPUT_TOOLTIPS = (
        "Scaled image using the nearest valid ratio.",
        "Final valid image width.",
        "Final valid image height.",
        "Actual scale ratio applied to the image.",
    )

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE", {
                    "tooltip": "Input image to upscale.",
                }),
                "scale_by": ("FLOAT", {
                    "default": 1.5,
                    "min": 0.01,
                    "max": 8.0,
                    "step": 0.01,
                    "tooltip": "Requested image scale ratio. The node uses the nearest valid ratio for the selected multiple.",
                }),
                "upscale_method": (IMAGE_UPSCALE_METHODS, {
                    "default": "bicubic",
                    "tooltip": "Interpolation method used for resizing.",
                }),
                "multiple": (IMAGE_SCALE_MULTIPLES, {
                    "default": "32",
                    "tooltip": "Output width and height must be multiples of this value.",
                }),
                "max_long_edge": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 16384,
                    "step": 32,
                    "tooltip": "Maximum output long edge. Set 0 to disable this limit.",
                }),
            },
        }

    RETURN_TYPES = ("IMAGE", "INT", "INT", "FLOAT")
    RETURN_NAMES = ("image", "width", "height", "applied_scale")
    FUNCTION = "upscale"
    CATEGORY = "EasyUse Anima/Image"

    def upscale(self, image, scale_by=1.5, upscale_method="bicubic", multiple="32", max_long_edge=0):
        upscale_method, multiple, max_long_edge = _normalize_image_scale_options(
            upscale_method,
            multiple,
            max_long_edge,
        )
        samples = image.movedim(-1, 1)
        width, height, applied_scale = _image_scale_by_multiple_size(
            int(samples.shape[3]),
            int(samples.shape[2]),
            scale_by,
            multiple,
            max_long_edge,
        )
        scaled = _common_upscale_image(samples, width, height, str(upscale_method))
        return (scaled.movedim(1, -1), width, height, applied_scale)


class EasyUseAnimaDetailerAlignHook:
    """Impact Pack DETAILER_HOOK that aligns detail crop sampling sizes upward."""

    DESCRIPTION = (
        "Creates an Impact Pack compatible DETAILER_HOOK that aligns the detailer crop sampling "
        "size upward to a selected multiple. Use alignment 32 for ANIMA/Spectrum workflows that "
        "require 32-multiple latent-safe crop sizes."
    )
    OUTPUT_TOOLTIPS = (
        "Impact Pack compatible DETAILER_HOOK. Connect it to an Impact DetailerForEach-compatible detailer_hook input.",
    )

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "alignment": (["none", "8", "16", "32", "64"], {
                    "default": "32",
                    "tooltip": (
                        "Crop sampling size alignment. 32 is recommended for ANIMA/Spectrum safety; "
                        "none keeps the original Impact Pack size."
                    ),
                }),
            },
            "optional": {
                "detailer_hook": ("DETAILER_HOOK", {
                    "tooltip": "Optional existing Impact Pack detailer hook. It runs before the alignment adjustment.",
                }),
            },
        }

    RETURN_TYPES = ("DETAILER_HOOK",)
    RETURN_NAMES = ("detailer_hook",)
    FUNCTION = "build"
    CATEGORY = "EasyUse Anima/Detailer"

    def build(self, alignment="32", detailer_hook=None):
        alignment_int = _alignment_value(alignment)
        return (_EasyUseAnimaAlignedDetailerHook(detailer_hook, alignment_int),)


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
                "tooltip": "ctx_SAM3 from Anima SAM3 Context or a compatible rgthree context containing model and clip.",
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
                "Use the Anima SAM3 Context node or a compatible rgthree context."
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


class EasyUseAnimaNAIARandomPrompt:
    """NAIA random prompt node with bypass and frozen-output cache."""

    DESCRIPTION = (
        "Requests a random prompt from NAIA Remote API, supports bypass and frozen output reuse, "
        "and stores generated values so saved-image workflows can reproduce the same result."
    )
    OUTPUT_TOOLTIPS = (
        "Prompt text from NAIA or the original input when bypassed or not overridden.",
        "Negative prompt text from NAIA or the original input when bypassed or not overridden.",
        "Width from NAIA or the original input when bypassed or not overridden.",
        "Height from NAIA or the original input when bypassed or not overridden.",
    )

    @classmethod
    def INPUT_TYPES(cls):
        required = {
            "use_naia_bridge": ("BOOLEAN", {
                "default": True,
                "tooltip": (
                    "false: bypass NAIA and return prompt/negative_prompt/width/height as-is. "
                    "This mode keeps ComfyUI cache stable when inputs are unchanged."
                ),
            }),
            "freeze_naia_output": ("BOOLEAN", {
                "default": False,
                "tooltip": (
                    "true: if cached output is valid, return it without calling NAIA. "
                    "Saved-image workflows are written with this enabled."
                ),
            }),
            "show_preview": ("BOOLEAN", {
                "default": True,
                "tooltip": "Show the large read-only preview widget in the node UI.",
            }),
            "cached_prompt": ("STRING", {
                "multiline": True,
                "default": "",
                "tooltip": "Stored prompt used for frozen output and saved-image reproduction.",
            }),
            "cached_negative_prompt": ("STRING", {
                "multiline": True,
                "default": "",
                "tooltip": "Stored negative prompt used for frozen output and saved-image reproduction.",
            }),
            "cached_width": ("INT", {
                "default": 0, "min": 0, "max": 8192, "step": 8,
                "tooltip": "Stored width used for frozen output and saved-image reproduction.",
            }),
            "cached_height": ("INT", {
                "default": 0, "min": 0, "max": 8192, "step": 8,
                "tooltip": "Stored height used for frozen output and saved-image reproduction.",
            }),
            "cached_signature": ("STRING", {
                "multiline": True,
                "default": "",
                "tooltip": "Internal signature for validating cached output.",
            }),
            "prompt": ("STRING", {
                "multiline": False,
                "default": "",
                "placeholder": "prompt",
                "tooltip": "Returned as-is when bypassed or when override_prompt is false.",
            }),
            "override_prompt": ("BOOLEAN", {
                "default": True,
                "tooltip": "true: use NAIA prompt. false: preserve input prompt.",
            }),
            "negative_prompt": ("STRING", {
                "multiline": False,
                "default": "",
                "placeholder": "negative_prompt",
                "tooltip": "Returned as-is when bypassed or when override_negative is false.",
            }),
            "override_negative": ("BOOLEAN", {
                "default": True,
                "tooltip": "true: use NAIA negative prompt. false: preserve input negative_prompt.",
            }),
            "width": ("INT", {
                "default": 1024, "min": 64, "max": 8192, "step": 8,
                "tooltip": "Returned as-is when bypassed or when override_width is false.",
            }),
            "override_width": ("BOOLEAN", {
                "default": True,
                "tooltip": "true: use NAIA width. false: preserve input width.",
            }),
            "height": ("INT", {
                "default": 1024, "min": 64, "max": 8192, "step": 8,
                "tooltip": "Returned as-is when bypassed or when override_height is false.",
            }),
            "override_height": ("BOOLEAN", {
                "default": True,
                "tooltip": "true: use NAIA height. false: preserve input height.",
            }),
            "use_naia_settings": ("BOOLEAN", {
                "default": True,
                "tooltip": (
                    "true: use NAIA desktop Prompt Engineering settings. "
                    "false: send this node's pre/post/auto_hide and preprocessing options."
                ),
            }),
            "pre_prompt": ("STRING", {
                "multiline": True,
                "default": "",
                "placeholder": "pre_prompt",
                "tooltip": "Used only when use_naia_settings is false.",
            }),
            "post_prompt": ("STRING", {
                "multiline": True,
                "default": "",
                "placeholder": "post_prompt",
                "tooltip": "Used only when use_naia_settings is false.",
            }),
            "auto_hide": ("STRING", {
                "multiline": True,
                "default": "",
                "placeholder": "auto_hide",
                "tooltip": "Used only when use_naia_settings is false.",
            }),
        }

        pp_tooltip = (
            "Used only when use_naia_settings is false.\n"
            "skip: do not send this key\n"
            "on: remove this category\n"
            "off: explicitly keep this category"
        )
        for key in PREPROCESSING_KEYS:
            required[key] = (PP_STATE_CHOICES, {
                "default": "skip",
                "tooltip": pp_tooltip,
                "advanced": key.startswith("remove_"),
                "socketless": key.startswith("remove_"),
            })

        required["host"] = ("STRING", {
            "default": DEFAULT_HOST,
            "tooltip": "NAIA Remote API host.",
        })
        required["port"] = ("INT", {
            "default": DEFAULT_PORT, "min": 1, "max": 65535,
            "tooltip": "NAIA Remote API port.",
        })
        return {
            "required": required,
            "hidden": {
                "workflow_prompt": "PROMPT",
                "extra_pnginfo": "EXTRA_PNGINFO",
                "unique_id": "UNIQUE_ID",
            },
        }

    RETURN_TYPES = ("STRING", "STRING", "INT", "INT")
    RETURN_NAMES = ("prompt", "negative_prompt", "width", "height")
    FUNCTION = "request"
    CATEGORY = "NAIA Bridge/API"

    def __init__(self):
        self._cache_signature: Optional[str] = None
        self._cache_value: Optional[tuple[str, str, int, int]] = None

    @classmethod
    def IS_CHANGED(
        cls,
        use_naia_bridge: bool = True,
        freeze_naia_output: bool = False,
        show_preview: bool = True,
        cached_prompt: str = "",
        cached_negative_prompt: str = "",
        cached_width: int = 0,
        cached_height: int = 0,
        cached_signature: str = "",
        prompt: str = "",
        override_prompt: bool = True,
        negative_prompt: str = "",
        override_negative: bool = True,
        width: int = 1024,
        override_width: bool = True,
        height: int = 1024,
        override_height: bool = True,
        use_naia_settings: bool = True,
        pre_prompt: str = "",
        post_prompt: str = "",
        auto_hide: str = "",
        host: str = DEFAULT_HOST,
        port: int = DEFAULT_PORT,
        **kwargs,
    ):
        naia_settings = resolve_naia_settings()
        use_naia_settings = naia_settings["use_naia_settings"]
        pre_prompt = naia_settings["pre_prompt"]
        post_prompt = naia_settings["post_prompt"]
        auto_hide = naia_settings["auto_hide"]
        host = naia_settings["host"]
        port = naia_settings["port"]
        pp_kwargs = naia_settings["preprocessing"]

        if not _as_bool(use_naia_bridge, True):
            return _stable_change_key({
                "mode": "disabled",
                "prompt": str(prompt),
                "negative_prompt": str(negative_prompt),
                "width": _as_int(width, 1024),
                "height": _as_int(height, 1024),
            })

        signature = cls._make_signature(
            prompt,
            override_prompt,
            negative_prompt,
            override_negative,
            width,
            override_width,
            height,
            override_height,
            use_naia_settings,
            pre_prompt,
            post_prompt,
            auto_hide,
            host,
            port,
            pp_kwargs,
        )

        if _as_bool(freeze_naia_output, False):
            cached = cls._cached_tuple(
                cached_prompt,
                cached_negative_prompt,
                cached_width,
                cached_height,
            )
            if cached is not None and str(cached_signature) == signature:
                return _stable_change_key({
                    "mode": "frozen",
                    "signature": signature,
                    "prompt": cached[0],
                    "negative_prompt": cached[1],
                    "width": cached[2],
                    "height": cached[3],
                })
            return float("nan")

        return float("nan")

    @staticmethod
    def _cached_tuple(
        cached_prompt: str,
        cached_negative_prompt: str,
        cached_width: int,
        cached_height: int,
    ) -> Optional[tuple[str, str, int, int]]:
        width = _as_int(cached_width, 0)
        height = _as_int(cached_height, 0)
        if width <= 0 or height <= 0:
            return None
        if not cached_prompt and not cached_negative_prompt:
            return None
        return (str(cached_prompt), str(cached_negative_prompt), width, height)

    @classmethod
    def _widget_input_names(cls) -> list[str]:
        return list(cls.INPUT_TYPES()["required"].keys())

    @staticmethod
    def _make_signature(
        prompt: str,
        override_prompt: bool,
        negative_prompt: str,
        override_negative: bool,
        width: int,
        override_width: bool,
        height: int,
        override_height: bool,
        use_naia_settings: bool,
        pre_prompt: str,
        post_prompt: str,
        auto_hide: str,
        host: str,
        port: int,
        pp_kwargs: dict,
    ) -> str:
        use_settings = _as_bool(use_naia_settings, True)
        preprocessing = {}
        if not use_settings:
            preprocessing = {
                key: str(pp_kwargs.get(key, "skip"))
                for key in PREPROCESSING_KEYS
            }
        payload = {
            "prompt": str(prompt),
            "override_prompt": _as_bool(override_prompt, True),
            "negative_prompt": str(negative_prompt),
            "override_negative": _as_bool(override_negative, True),
            "width": _as_int(width, 1024),
            "override_width": _as_bool(override_width, True),
            "height": _as_int(height, 1024),
            "override_height": _as_bool(override_height, True),
            "use_naia_settings": use_settings,
            "pre_prompt": "" if use_settings else str(pre_prompt),
            "post_prompt": "" if use_settings else str(post_prompt),
            "auto_hide": "" if use_settings else str(auto_hide),
            "preprocessing": preprocessing,
            "host": str(host),
            "port": _as_int(port, DEFAULT_PORT),
        }
        return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))

    @staticmethod
    def _make_request_body(
        use_naia_settings: bool,
        pre_prompt: str,
        post_prompt: str,
        auto_hide: str,
        pp_kwargs: dict,
    ) -> dict:
        body = {
            "timeout": NAIA_REQUEST_TIMEOUT,
            "respect_naia_autogen": True,
            "force_naia_skip_generate": False,
        }
        if not use_naia_settings:
            preprocessing_options = {}
            for key in PREPROCESSING_KEYS:
                state = pp_kwargs.get(key, "skip")
                if state == "on":
                    preprocessing_options[key] = True
                elif state == "off":
                    preprocessing_options[key] = False
            body["peng_override"] = {
                "pre_prompt": pre_prompt,
                "post_prompt": post_prompt,
                "auto_hide": auto_hide,
                "preprocessing_options": preprocessing_options,
            }
        return body

    @staticmethod
    def _apply_overrides(
        naia_value: tuple[str, str, int, int],
        prompt: str,
        override_prompt: bool,
        negative_prompt: str,
        override_negative: bool,
        width: int,
        override_width: bool,
        height: int,
        override_height: bool,
    ) -> tuple[str, str, int, int]:
        naia_prompt, naia_negative, naia_width, naia_height = naia_value
        return (
            naia_prompt if override_prompt else str(prompt),
            naia_negative if override_negative else str(negative_prompt),
            naia_width if override_width else _as_int(width, 1024),
            naia_height if override_height else _as_int(height, 1024),
        )

    @classmethod
    def _update_metadata_cache(
        cls,
        workflow_prompt,
        extra_pnginfo,
        unique_id,
        output_value: tuple[str, str, int, int],
        signature: str,
    ) -> None:
        node_id = _single_value(unique_id)
        if node_id is None:
            return
        node_id = str(node_id)
        out_prompt, out_negative, out_width, out_height = output_value
        updates = {
            "use_naia_bridge": True,
            "freeze_naia_output": True,
            "cached_prompt": out_prompt,
            "cached_negative_prompt": out_negative,
            "cached_width": int(out_width),
            "cached_height": int(out_height),
            "cached_signature": signature,
        }

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
    def _ui(prompt: str, negative: str, width: int, height: int, status: str, signature: str):
        return {
            "prompt": [prompt],
            "negative_prompt": [negative],
            "width": [width],
            "height": [height],
            "status": [status],
            "cached_signature": [signature],
        }

    def request(
        self,
        use_naia_bridge: bool,
        freeze_naia_output: bool,
        show_preview: bool,
        cached_prompt: str,
        cached_negative_prompt: str,
        cached_width: int,
        cached_height: int,
        cached_signature: str,
        prompt: str,
        override_prompt: bool,
        negative_prompt: str,
        override_negative: bool,
        width: int,
        override_width: bool,
        height: int,
        override_height: bool,
        use_naia_settings: bool,
        pre_prompt: str,
        post_prompt: str,
        auto_hide: str,
        host: str,
        port: int,
        workflow_prompt=None,
        extra_pnginfo=None,
        unique_id=None,
        **pp_kwargs,
    ):
        naia_settings = resolve_naia_settings()
        use_naia_settings = naia_settings["use_naia_settings"]
        pre_prompt = naia_settings["pre_prompt"]
        post_prompt = naia_settings["post_prompt"]
        auto_hide = naia_settings["auto_hide"]
        host = naia_settings["host"]
        port = naia_settings["port"]
        pp_kwargs = naia_settings["preprocessing"]

        bridge_enabled = _as_bool(use_naia_bridge, True)
        freeze_output = _as_bool(freeze_naia_output, False)
        use_settings = _as_bool(use_naia_settings, True)
        override_prompt = _as_bool(override_prompt, True)
        override_negative = _as_bool(override_negative, True)
        override_width = _as_bool(override_width, True)
        override_height = _as_bool(override_height, True)

        signature = self._make_signature(
            prompt,
            override_prompt,
            negative_prompt,
            override_negative,
            width,
            override_width,
            height,
            override_height,
            use_settings,
            pre_prompt,
            post_prompt,
            auto_hide,
            host,
            port,
            pp_kwargs,
        )

        if not bridge_enabled:
            out_prompt = str(prompt)
            out_negative = str(negative_prompt)
            out_width = _as_int(width, 1024)
            out_height = _as_int(height, 1024)
            return {
                "ui": self._ui(out_prompt, out_negative, out_width, out_height, "disabled", signature),
                "result": (out_prompt, out_negative, out_width, out_height),
            }

        saved_cache = self._cached_tuple(
            cached_prompt,
            cached_negative_prompt,
            cached_width,
            cached_height,
        )
        if freeze_output and saved_cache is not None and str(cached_signature) == signature:
            out_prompt, out_negative, out_width, out_height = saved_cache
            return {
                "ui": self._ui(out_prompt, out_negative, out_width, out_height, "frozen", signature),
                "result": (out_prompt, out_negative, out_width, out_height),
            }

        if self._cache_signature != signature:
            self._cache_signature = signature
            self._cache_value = (
                saved_cache if saved_cache is not None and str(cached_signature) == signature else None
            )

        if self._cache_value is None or not freeze_output:
            body = self._make_request_body(use_settings, pre_prompt, post_prompt, auto_hide, pp_kwargs)
            resp = _post_random(host, port, body)
            naia_value = _parse_random_response(resp)
            self._cache_value = self._apply_overrides(
                naia_value,
                prompt,
                override_prompt,
                negative_prompt,
                override_negative,
                width,
                override_width,
                height,
                override_height,
            )
            logger.debug(
                "request_id=%s prompt_len=%d size=%dx%d use_naia_settings=%s",
                resp.get("request_id"),
                len(self._cache_value[0]),
                self._cache_value[2],
                self._cache_value[3],
                use_settings,
            )

        if self._cache_value is None:
            raise RuntimeError("[EasyUse Anima] Internal cache creation failed.")

        out_prompt, out_negative, out_width, out_height = self._cache_value
        self._update_metadata_cache(
            workflow_prompt,
            extra_pnginfo,
            unique_id,
            (out_prompt, out_negative, out_width, out_height),
            signature,
        )
        return {
            "ui": self._ui(out_prompt, out_negative, out_width, out_height, "fresh", signature),
            "result": (out_prompt, out_negative, out_width, out_height),
        }
