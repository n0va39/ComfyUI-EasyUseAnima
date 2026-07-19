"""Public adapters for prompt data and artist-mix conditioning."""
from __future__ import annotations

from ..common.serialization import _stable_change_key
from ..common.values import _as_bool
from ..prompt.artist_mix import (
    ARTIST_MIX_DEFAULT_CLUSTER_COUNT,
    ARTIST_MIX_DEFAULT_DOMINANT_ISOLATION,
    ARTIST_MIX_DEFAULT_DOMINANT_THRESHOLD,
    ARTIST_MIX_DEFAULT_EXACT_TOP_K,
    ARTIST_MIX_DEFAULT_RMS_SCALE_CAP,
    ARTIST_MIX_DEFAULT_START_PERCENT,
    ARTIST_MIX_DEFAULT_STRENGTH_SCALE,
    ARTIST_MIX_DEFAULT_STYLE_GAIN,
    ARTIST_MIX_INPUT_MODES,
    ARTIST_MIX_MODES,
    ARTIST_MIX_MODE_FROM_PROMPT_DATA,
    ARTIST_MIX_MODE_PROMPT,
    ARTIST_TAG_POSITION_CORRECT,
    ARTIST_TAG_POSITION_MODES,
    _artist_mix_inline_prompt,
    _artist_mix_mode_tooltip,
    _artist_prompt_with_position,
    _bounded_artist_mix_float,
    _bounded_artist_mix_int,
    _encode_prompt_data_positive_conditioning,
    _join_artist_mix_source_prompts,
    _normalize_artist_mix_mode,
    _normalize_artist_tag_position,
)
from ..prompt.conditioning import (
    ANIMA_MOD_GUIDANCE_DEFAULT_PROFILE,
    ANIMA_MOD_GUIDANCE_MODES,
    ANIMA_MOD_GUIDANCE_MODE_FROM_PROMPT_DATA,
    ANIMA_MOD_GUIDANCE_PROFILES,
    ANIMA_MOD_GUIDANCE_PROFILE_OFF,
    _apply_spectrum_anima_mod_guidance,
    _normalize_anima_mod_guidance_profile,
    _resolve_anima_mod_guidance_enabled,
)
from ..prompt.data import (
    PROMPT_DATA_COMPAT_OUTPUT_TOOLTIPS,
    PROMPT_DATA_COMPAT_RETURN_NAMES,
    PROMPT_DATA_COMPAT_RETURN_TYPES,
    PROMPT_DATA_TYPE,
    _advanced_outputs_from_prompt_data,
    _apply_prompt_data_overrides,
    _normalize_prompt_data,
)

_RUNTIME_RESOLVER = None
_RUNTIME_HELPER_DEFAULTS = {
    "_as_bool": _as_bool,
    "_advanced_outputs_from_prompt_data": _advanced_outputs_from_prompt_data,
    "_apply_prompt_data_overrides": _apply_prompt_data_overrides,
    "_apply_spectrum_anima_mod_guidance": _apply_spectrum_anima_mod_guidance,
    "_artist_mix_inline_prompt": _artist_mix_inline_prompt,
    "_artist_mix_mode_tooltip": _artist_mix_mode_tooltip,
    "_artist_prompt_with_position": _artist_prompt_with_position,
    "_bounded_artist_mix_float": _bounded_artist_mix_float,
    "_bounded_artist_mix_int": _bounded_artist_mix_int,
    "_encode_prompt_data_positive_conditioning": _encode_prompt_data_positive_conditioning,
    "_join_artist_mix_source_prompts": _join_artist_mix_source_prompts,
    "_normalize_anima_mod_guidance_profile": _normalize_anima_mod_guidance_profile,
    "_normalize_artist_mix_mode": _normalize_artist_mix_mode,
    "_normalize_artist_tag_position": _normalize_artist_tag_position,
    "_normalize_prompt_data": _normalize_prompt_data,
    "_resolve_anima_mod_guidance_enabled": _resolve_anima_mod_guidance_enabled,
    "_stable_change_key": _stable_change_key,
}
_RUNTIME_ONLY_HELPERS = (
    "_encode_with_comfy_clip",
    "_generate_empty_latent_with_comfy",
    "_join_prompt_tokens",
)

def _runtime_proxy(name: str):
    def invoke(*args, **kwargs):
        if _RUNTIME_RESOLVER is not None:
            return _RUNTIME_RESOLVER(name)(*args, **kwargs)
        helper = _RUNTIME_HELPER_DEFAULTS.get(name)
        if helper is None:
            raise RuntimeError(f"[EasyUseAnima] Prompt data node runtime helper is not bound: {name}")
        return helper(*args, **kwargs)
    return invoke

def _bind_prompt_data_node_runtime(*, resolve_helper) -> None:
    global _RUNTIME_RESOLVER
    _RUNTIME_RESOLVER = resolve_helper
    for name in (*_RUNTIME_HELPER_DEFAULTS, *_RUNTIME_ONLY_HELPERS):
        globals()[name] = _runtime_proxy(name)

class EasyUseAnimaPromptDataUnpack:
    """Expand EASYUSE_ANIMA_PROMPT_DATA into compatibility outputs."""

    DESCRIPTION = (
        "Expands an EASYUSE_ANIMA_PROMPT_DATA dict into Prompt Studio compatibility "
        "outputs, accepts optional override inputs, and passes prompt data through "
        "for context-style chaining."
    )
    OUTPUT_TOOLTIPS = (
        "Pass-through prompt data for downstream prompt-data nodes.",
        *PROMPT_DATA_COMPAT_OUTPUT_TOOLTIPS,
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

    RETURN_TYPES = (PROMPT_DATA_TYPE, *PROMPT_DATA_COMPAT_RETURN_TYPES)
    RETURN_NAMES = (PROMPT_DATA_TYPE, *PROMPT_DATA_COMPAT_RETURN_NAMES)
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
                    "tooltip": (
                        "Comma- or newline-separated artist tags. (artist:1.2) sets a mix weight. "
                        "[[artist_a, artist_b:0.7]] keeps multiple artists in one mix branch."
                    ),
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
        artist_prompt = _join_artist_mix_source_prompts(artist_tags)
        if mode == ARTIST_MIX_MODE_PROMPT:
            return (_encode_with_comfy_clip(
                clip,
                _artist_prompt_with_position(base_prompt, _artist_mix_inline_prompt(artist_prompt), position),
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

__all__ = ()
