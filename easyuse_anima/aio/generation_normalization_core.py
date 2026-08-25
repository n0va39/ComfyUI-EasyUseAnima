from __future__ import annotations

from collections.abc import Callable
from typing import Any

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
    ARTIST_MIX_MODE_FROM_PROMPT_DATA,
)
from ..prompt.conditioning import (
    ANIMA_MOD_GUIDANCE_DEFAULT_PROFILE,
    ANIMA_MOD_GUIDANCE_MODE_FROM_PROMPT_DATA,
    ANIMA_MOD_GUIDANCE_MODES,
)
from ..seed.reservation import SEED_CONTROL_FIXED
from .generation_defaults import (
    AIO_GENERATION_DEFAULT_SETTINGS,
    AIO_GENERATION_SETTINGS_SCHEMA,
    AIO_GENERATION_SETTINGS_VERSION,
    AIO_SAMPLER_CFG_MAX,
    AIO_SAMPLER_CFG_MIN,
    AIO_SAMPLER_STEPS_MAX,
    AIO_SAMPLER_STEPS_MIN,
    AIO_SPECIAL_SEED_RANDOM,
)

ValueHelper = Callable[..., Any]


def merge_versioned_settings(
    defaults: dict[str, Any],
    value,
    *,
    json_clone: ValueHelper,
    json_object: ValueHelper,
    json_safe: ValueHelper,
) -> dict[str, Any]:
    merged = json_clone(defaults)
    incoming = json_object(value)

    def merge_dict(base: dict[str, Any], update: dict[str, Any]) -> dict[str, Any]:
        for key, update_value in update.items():
            base_value = base.get(key)
            if isinstance(base_value, dict) and isinstance(update_value, dict):
                base[key] = merge_dict(dict(base_value), update_value)
            else:
                base[key] = json_safe(update_value)
        return base

    return merge_dict(merged, incoming)


def migrate_supported_aio_generation_settings(
    value,
    *,
    migrate: ValueHelper,
):
    """Migrate explicit supported versions without tightening the legacy facade."""

    if not isinstance(value, dict):
        return value
    version = value.get("version")
    if (
        value.get("schema") != AIO_GENERATION_SETTINGS_SCHEMA
        or isinstance(version, bool)
        or not isinstance(version, int)
        or version < 1
        or version > AIO_GENERATION_SETTINGS_VERSION
    ):
        return value
    return migrate(value)


def normalize_aio_seed(
    value,
    default: int = AIO_SPECIAL_SEED_RANDOM,
    *,
    as_int: ValueHelper,
    max_seed: int,
    min_seed: int,
) -> int:
    return max(min_seed, min(max_seed, as_int(value, default)))


def normalize_aio_spectrum_settings(
    value,
    defaults: dict[str, Any],
    *,
    as_bool: ValueHelper,
    as_float: ValueHelper,
    as_int: ValueHelper,
    choice: ValueHelper,
) -> dict[str, Any]:
    spectrum = value if isinstance(value, dict) else {}
    spectrum["enabled"] = as_bool(
        spectrum.get("enabled"),
        as_bool(defaults.get("enabled"), False),
    )
    spectrum["window_size"] = max(
        1.0,
        min(
            10.0,
            as_float(
                spectrum.get("window_size"),
                as_float(defaults.get("window_size"), 2.0),
            ),
        ),
    )
    spectrum["flex_window"] = max(
        0.0,
        min(
            2.0,
            as_float(
                spectrum.get("flex_window"),
                as_float(defaults.get("flex_window"), 0.25),
            ),
        ),
    )
    spectrum["warmup_steps"] = max(
        0,
        min(
            10000,
            as_int(
                spectrum.get("warmup_steps"),
                as_int(defaults.get("warmup_steps"), 6),
            ),
        ),
    )
    spectrum["tail_actual_steps"] = max(
        0,
        min(
            10000,
            as_int(
                spectrum.get("tail_actual_steps"),
                as_int(defaults.get("tail_actual_steps"), 3),
            ),
        ),
    )
    spectrum["blend_w"] = max(
        0.0,
        min(
            1.0,
            as_float(
                spectrum.get("blend_w"),
                as_float(defaults.get("blend_w"), 0.3),
            ),
        ),
    )
    spectrum["cheby_degree"] = max(
        1,
        min(
            10,
            as_int(
                spectrum.get("cheby_degree"),
                as_int(defaults.get("cheby_degree"), 3),
            ),
        ),
    )
    spectrum["ridge_lambda"] = max(
        0.001,
        min(
            10.0,
            as_float(
                spectrum.get("ridge_lambda"),
                as_float(defaults.get("ridge_lambda"), 0.1),
            ),
        ),
    )
    spectrum["history_size"] = max(
        5,
        min(
            10000,
            as_int(
                spectrum.get("history_size"),
                as_int(defaults.get("history_size"), 100),
            ),
        ),
    )
    spectrum["one_sampler_only"] = as_bool(
        spectrum.get("one_sampler_only"),
        as_bool(defaults.get("one_sampler_only"), False),
    )
    spectrum["verbose"] = as_bool(
        spectrum.get("verbose"),
        as_bool(defaults.get("verbose"), False),
    )
    spectrum["compat_policy"] = choice(
        spectrum.get("compat_policy"),
        ("legacy", "conservative", "strict"),
        str(defaults.get("compat_policy") or "conservative"),
    )
    return spectrum


def normalize_sampler_settings(
    settings: dict[str, Any],
    *,
    as_bool: ValueHelper,
    as_float: ValueHelper,
    as_int: ValueHelper,
    choice: ValueHelper,
    json_clone: ValueHelper,
    sampler_names: ValueHelper,
    scheduler_names: ValueHelper,
    normalize_seed: ValueHelper,
    normalize_spectrum: ValueHelper,
    normalize_corrections: ValueHelper,
    seed_control_modes: tuple[str, ...],
) -> None:
    settings["schema"] = AIO_GENERATION_SETTINGS_SCHEMA
    settings["version"] = as_int(
        settings.get("version"),
        AIO_GENERATION_SETTINGS_VERSION,
    )
    settings["mode"] = choice(
        settings.get("mode"),
        ("txt2img", "img2img", "inpaint"),
        "txt2img",
    )

    sampler = settings.setdefault("sampler", {})
    if not isinstance(sampler, dict):
        sampler = {}
        settings["sampler"] = sampler
    sampler["backend"] = choice(
        sampler.get("backend"),
        ("comfy_ksampler", "spectrum_mod_guidance_advanced", "spectrum_spd_speed"),
        "comfy_ksampler",
    )
    sampler["seed"] = normalize_seed(sampler.get("seed"))
    sampler["seed_after_generate"] = choice(
        sampler.get("seed_after_generate"),
        seed_control_modes,
        SEED_CONTROL_FIXED,
    )
    defaults = AIO_GENERATION_DEFAULT_SETTINGS["sampler"]
    sampler["steps"] = max(
        AIO_SAMPLER_STEPS_MIN,
        min(
            AIO_SAMPLER_STEPS_MAX,
            as_int(sampler.get("steps"), defaults["steps"]),
        ),
    )
    sampler["cfg"] = max(
        AIO_SAMPLER_CFG_MIN,
        min(
            AIO_SAMPLER_CFG_MAX,
            as_float(sampler.get("cfg"), defaults["cfg"]),
        ),
    )
    sampler["denoise"] = max(
        0.0,
        min(1.0, as_float(sampler.get("denoise"), defaults["denoise"])),
    )
    sampler["sampler_name"] = choice(
        sampler.get("sampler_name"),
        sampler_names(),
        defaults["sampler_name"],
    )
    sampler["scheduler"] = choice(
        sampler.get("scheduler"),
        scheduler_names(),
        defaults["scheduler"],
    )
    sampler["spectrum"] = normalize_spectrum(
        sampler.get("spectrum"),
        defaults["spectrum"],
    )
    spd = sampler.setdefault("spd", {})
    if not isinstance(spd, dict):
        spd = {}
        sampler["spd"] = spd
    spd["split_mode"] = choice(spd.get("split_mode"), ("single",), "single")
    spd["scale"] = max(0.25, min(1.0, as_float(spd.get("scale"), 0.5)))
    spd["sigma"] = max(0.0, min(1.0, as_float(spd.get("sigma"), 0.7)))
    spd["adaptive_smc_alpha"] = max(
        0.0,
        min(1.0, as_float(spd.get("adaptive_smc_alpha"), 0.0)),
    )
    sampler["spectrum_extra"] = (
        json_clone(sampler.get("spectrum_extra"))
        if isinstance(sampler.get("spectrum_extra"), dict)
        else {}
    )
    sampler["spd_extra"] = (
        json_clone(sampler.get("spd_extra"))
        if isinstance(sampler.get("spd_extra"), dict)
        else {}
    )
    sampler.pop("dave", None)
    sampler["dit_corrections"] = normalize_corrections(
        sampler.get("dit_corrections"),
        defaults["dit_corrections"],
    )

    negpip = settings.setdefault("negpip", {})
    if not isinstance(negpip, dict):
        negpip = {}
        settings["negpip"] = negpip
    negpip["mode"] = choice(negpip.get("mode"), ("off", "on", "turbo"), "off")


def normalize_prompt_settings(
    settings: dict[str, Any],
    *,
    as_bool: ValueHelper,
    as_float: ValueHelper,
    as_int: ValueHelper,
    choice: ValueHelper,
    normalize_mod_profile: ValueHelper,
    bounded_artist_float: ValueHelper,
    bounded_artist_int: ValueHelper,
) -> None:
    mod_guidance = settings.setdefault("mod_guidance", {})
    if not isinstance(mod_guidance, dict):
        mod_guidance = {}
        settings["mod_guidance"] = mod_guidance
    mod_guidance["mode"] = choice(
        mod_guidance.get("mode"),
        ANIMA_MOD_GUIDANCE_MODES,
        ANIMA_MOD_GUIDANCE_MODE_FROM_PROMPT_DATA,
    )
    mod_guidance["profile"] = normalize_mod_profile(
        mod_guidance.get("profile", ANIMA_MOD_GUIDANCE_DEFAULT_PROFILE)
    )
    advanced = mod_guidance.setdefault("advanced", {})
    if not isinstance(advanced, dict):
        advanced = {}
        mod_guidance["advanced"] = advanced
    defaults = AIO_GENERATION_DEFAULT_SETTINGS["mod_guidance"]["advanced"]
    advanced["adapter"] = str(advanced.get("adapter") or defaults["adapter"])
    advanced["quality_tags"] = str(advanced.get("quality_tags") or defaults["quality_tags"])
    advanced["quality_neg"] = str(advanced.get("quality_neg") or defaults["quality_neg"])
    advanced["mod_w"] = max(-20.0, min(20.0, as_float(advanced.get("mod_w"), 3.0)))
    advanced["mod_start_layer"] = max(0, min(999, as_int(advanced.get("mod_start_layer"), 8)))
    advanced["mod_end_layer"] = max(-1, min(999, as_int(advanced.get("mod_end_layer"), 27)))
    advanced["mod_taper"] = max(0, min(999, as_int(advanced.get("mod_taper"), 0)))
    advanced["mod_taper_scale"] = max(
        0.0,
        min(1.0, as_float(advanced.get("mod_taper_scale"), 0.25)),
    )
    advanced["mod_final_w"] = max(
        -20.0,
        min(20.0, as_float(advanced.get("mod_final_w"), 0.0)),
    )

    artist_mix = settings.setdefault("artist_mix", {})
    if not isinstance(artist_mix, dict):
        artist_mix = {}
        settings["artist_mix"] = artist_mix
    artist_mix["mode"] = choice(
        artist_mix.get("mode"),
        ARTIST_MIX_INPUT_MODES,
        ARTIST_MIX_MODE_FROM_PROMPT_DATA,
    )
    artist_mix["start_percent"] = bounded_artist_float(
        artist_mix.get("start_percent"), ARTIST_MIX_DEFAULT_START_PERCENT, 0.0, 1.0
    )
    artist_mix["strength_scale"] = bounded_artist_float(
        artist_mix.get("strength_scale"), ARTIST_MIX_DEFAULT_STRENGTH_SCALE, 0.0, 5.0
    )
    artist_mix["style_gain"] = bounded_artist_float(
        artist_mix.get("style_gain"), ARTIST_MIX_DEFAULT_STYLE_GAIN, 0.0, 3.0
    )
    artist_mix["rms_scale_cap"] = bounded_artist_float(
        artist_mix.get("rms_scale_cap"), ARTIST_MIX_DEFAULT_RMS_SCALE_CAP, 1.0, 5.0
    )
    artist_mix["exact_top_k"] = bounded_artist_int(
        artist_mix.get("exact_top_k"), ARTIST_MIX_DEFAULT_EXACT_TOP_K, 0, 64
    )
    artist_mix["cluster_count"] = bounded_artist_int(
        artist_mix.get("cluster_count"), ARTIST_MIX_DEFAULT_CLUSTER_COUNT, 1, 32
    )
    artist_mix["dominant_isolation"] = as_bool(
        artist_mix.get("dominant_isolation"),
        ARTIST_MIX_DEFAULT_DOMINANT_ISOLATION,
    )
    artist_mix["dominant_threshold"] = bounded_artist_float(
        artist_mix.get("dominant_threshold"),
        ARTIST_MIX_DEFAULT_DOMINANT_THRESHOLD,
        0.0,
        1.0,
    )


__all__ = ()
