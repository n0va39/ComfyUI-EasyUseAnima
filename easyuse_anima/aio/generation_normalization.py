from __future__ import annotations

import re
from typing import Any

from ..common.serialization import _json_clone, _json_object
from ..common.values import _as_bool, _as_float, _as_int, _choice
from ..image.scaling import IMAGE_SCALE_MULTIPLES, IMAGE_UPSCALE_METHODS
from ..infrastructure.comfy.capabilities import (
    _comfy_sampler_names,
    _comfy_scheduler_names,
    _impact_scheduler_names,
)
from ..infrastructure.comfy.wiring import resolve_comfy_host_helper
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
    _bounded_artist_mix_float,
    _bounded_artist_mix_int,
)
from ..prompt.conditioning import (
    ANIMA_MOD_GUIDANCE_DEFAULT_PROFILE,
    ANIMA_MOD_GUIDANCE_MODE_FROM_PROMPT_DATA,
    ANIMA_MOD_GUIDANCE_MODES,
    _normalize_anima_mod_guidance_profile,
)
from ..prompt.data import _prompt_data_json_safe
from ..seed.reservation import (
    SEED_CONTROL_FIXED,
    SEED_SELECTION_DECREMENT,
    SEED_SELECTION_INCREMENT,
    SEED_SELECTION_RANDOMIZE,
)
from .generation_defaults import (
    AIO_FINAL_FIT_MODES,
    AIO_FINAL_UPSCALE_BACKENDS,
    AIO_GENERATION_DEFAULT_SETTINGS,
    AIO_GENERATION_SETTINGS_SCHEMA,
    AIO_GENERATION_SETTINGS_VERSION,
    AIO_GENERATION_STAGE_IDS,
    AIO_RESHIFT_DTYPES,
    AIO_RESHIFT_SCALES,
    AIO_SPECIAL_SEED_DECREMENT,
    AIO_SPECIAL_SEED_RANDOM,
    AIO_USDU_MODE_TYPES,
    AIO_USDU_PROMPT_MODES,
    AIO_USDU_PROMPT_NO_GENERAL,
    AIO_USDU_SEAM_FIX_MODES,
)
from .generation_defaults import (
    AIO_SPECIAL_SEED_INCREMENT as AIO_SPECIAL_SEED_INCREMENT,
)
from .generation_defaults import (
    AIO_SPECIAL_SEEDS as AIO_SPECIAL_SEEDS,
)
from .generation_migrations import migrate_aio_generation_settings
from .generation_settings import (
    round_trip_aio_generation_settings as _round_trip_aio_generation_settings,
)
from .output_settings import (
    _normalize_aio_civitai_hash_fetchers,
    _normalize_aio_hash_bundles,
)

# Exact legacy backend clamp retained locally until the shared seed constants
# receive their own Contract lane. Importing wildcard_engine here would also
# import NumPy during side-effect-free package discovery.
MAX_SEED = 0xFFFFFFFFFFFFFFFF
SEED_CONTROL_MODES = (
    SEED_CONTROL_FIXED,
    SEED_SELECTION_RANDOMIZE,
    SEED_SELECTION_INCREMENT,
    SEED_SELECTION_DECREMENT,
)


def _missing_host_helper(name: str):
    raise RuntimeError(
        f"[EasyUseAnima] AiO generation normalization Comfy host helper is unavailable: {name}"
    )


def _comfy_max_resolution() -> int:
    helper = resolve_comfy_host_helper(
        "_comfy_max_resolution",
        _missing_host_helper,
    )
    return helper()

_AIO_DETAILER_RESERVED_KEYS = {"enabled", "order", "sam3"}
_AIO_DETAILER_CUSTOM_RE = re.compile(r"^custom_\d+$")


def _is_aio_detailer_target_name(name: str) -> bool:
    return name in ("face", "eye") or bool(_AIO_DETAILER_CUSTOM_RE.fullmatch(name))


def _aio_detailer_target_defaults(target_name: str) -> dict[str, Any]:
    if target_name == "eye":
        return _json_clone(AIO_GENERATION_DEFAULT_SETTINGS["detailer"]["eye"])
    defaults = _json_clone(
        AIO_GENERATION_DEFAULT_SETTINGS["detailer"]["face"]
    )
    if target_name not in ("face", "eye"):
        suffix = target_name.rsplit("_", 1)[-1]
        defaults["label"] = (
            f"Detailer Block {suffix}" if suffix.isdigit() else "Detailer Block"
        )
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


def _aio_detailer_has_enabled_targets(detailer_settings: dict[str, Any]) -> bool:
    if not _as_bool(
        detailer_settings.get("enabled"),
        False,
    ):
        return False
    return any(
        isinstance(detailer_settings.get(name), dict)
        and _as_bool(
            detailer_settings[name].get("enabled"),
            False,
        )
        for name in _aio_detailer_target_order(detailer_settings)
    )


def _normalize_aio_seed(value, default: int = AIO_SPECIAL_SEED_RANDOM) -> int:
    return max(AIO_SPECIAL_SEED_DECREMENT, min(MAX_SEED, _as_int(value, default)))


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


def _migrate_supported_aio_generation_settings(value):
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
    return migrate_aio_generation_settings(value)


def _normalize_aio_spectrum_settings(
    value,
    defaults: dict[str, Any],
) -> dict[str, Any]:
    spectrum = value if isinstance(value, dict) else {}
    spectrum["enabled"] = _as_bool(
        spectrum.get("enabled"),
        _as_bool(defaults.get("enabled"), False),
    )
    spectrum["window_size"] = max(
        1.0,
        min(
            10.0,
            _as_float(
                spectrum.get("window_size"),
                _as_float(defaults.get("window_size"), 2.0),
            ),
        ),
    )
    spectrum["flex_window"] = max(
        0.0,
        min(
            2.0,
            _as_float(
                spectrum.get("flex_window"),
                _as_float(defaults.get("flex_window"), 0.25),
            ),
        ),
    )
    spectrum["warmup_steps"] = max(
        0,
        min(
            10000,
            _as_int(
                spectrum.get("warmup_steps"),
                _as_int(defaults.get("warmup_steps"), 6),
            ),
        ),
    )
    spectrum["tail_actual_steps"] = max(
        0,
        min(
            10000,
            _as_int(
                spectrum.get("tail_actual_steps"),
                _as_int(defaults.get("tail_actual_steps"), 3),
            ),
        ),
    )
    spectrum["blend_w"] = max(
        0.0,
        min(
            1.0,
            _as_float(
                spectrum.get("blend_w"),
                _as_float(defaults.get("blend_w"), 0.3),
            ),
        ),
    )
    spectrum["cheby_degree"] = max(
        1,
        min(
            10,
            _as_int(
                spectrum.get("cheby_degree"),
                _as_int(defaults.get("cheby_degree"), 3),
            ),
        ),
    )
    spectrum["ridge_lambda"] = max(
        0.001,
        min(
            10.0,
            _as_float(
                spectrum.get("ridge_lambda"),
                _as_float(defaults.get("ridge_lambda"), 0.1),
            ),
        ),
    )
    spectrum["history_size"] = max(
        5,
        min(
            10000,
            _as_int(
                spectrum.get("history_size"),
                _as_int(defaults.get("history_size"), 100),
            ),
        ),
    )
    spectrum["one_sampler_only"] = _as_bool(
        spectrum.get("one_sampler_only"),
        _as_bool(defaults.get("one_sampler_only"), False),
    )
    spectrum["verbose"] = _as_bool(
        spectrum.get("verbose"),
        _as_bool(defaults.get("verbose"), False),
    )
    spectrum["compat_policy"] = _choice(
        spectrum.get("compat_policy"),
        ("legacy", "conservative", "strict"),
        str(defaults.get("compat_policy") or "conservative"),
    )
    return spectrum


def _normalize_aio_dit_corrections_settings(
    value,
    defaults: dict[str, Any],
) -> dict[str, Any]:
    corrections = value if isinstance(value, dict) else {}
    corrections["enabled"] = _as_bool(
        corrections.get("enabled"),
        _as_bool(defaults.get("enabled"), False),
    )
    corrections["dcw_mode"] = _choice(
        corrections.get("dcw_mode"),
        ("off", "manual", "auto"),
        str(defaults.get("dcw_mode") or "off"),
    )
    corrections["dcw_lambda"] = max(
        -1.0,
        min(
            1.0,
            _as_float(
                corrections.get("dcw_lambda"),
                _as_float(defaults.get("dcw_lambda"), 0.01),
            ),
        ),
    )
    corrections["dcw_band_mask"] = _choice(
        corrections.get("dcw_band_mask"),
        ("LL", "all", "HH", "LH+HL+HH"),
        str(defaults.get("dcw_band_mask") or "LL"),
    )
    corrections["dcw_calibrator"] = str(
        corrections.get("dcw_calibrator")
        or defaults.get("dcw_calibrator")
        or "(auto-download default)"
    )
    corrections["smc_cfg"] = _as_bool(
        corrections.get("smc_cfg"),
        _as_bool(defaults.get("smc_cfg"), False),
    )
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
        min(
            20.0,
            _as_float(
                corrections.get("smc_cfg_lambda"),
                _as_float(defaults.get("smc_cfg_lambda"), 6.0),
            ),
        ),
    )
    corrections["cfgpp"] = _as_bool(
        corrections.get("cfgpp"),
        _as_bool(defaults.get("cfgpp"), False),
    )
    corrections["cfgpp_lambda"] = max(
        0.0,
        min(
            8.0,
            _as_float(
                corrections.get("cfgpp_lambda"),
                _as_float(defaults.get("cfgpp_lambda"), 0.0),
            ),
        ),
    )
    corrections["fsg"] = _as_bool(
        corrections.get("fsg"),
        _as_bool(defaults.get("fsg"), False),
    )
    corrections["fsg_band_lo"] = max(
        0.0,
        min(
            1.0,
            _as_float(
                corrections.get("fsg_band_lo"),
                _as_float(defaults.get("fsg_band_lo"), 0.59),
            ),
        ),
    )
    corrections["fsg_band_hi"] = max(
        0.0,
        min(
            1.0,
            _as_float(
                corrections.get("fsg_band_hi"),
                _as_float(defaults.get("fsg_band_hi"), 0.75),
            ),
        ),
    )
    corrections["fsg_k"] = max(
        0,
        min(
            32,
            _as_int(
                corrections.get("fsg_k"),
                _as_int(defaults.get("fsg_k"), 3),
            ),
        ),
    )
    corrections["fsg_d_sigma"] = max(
        0.0,
        min(
            1.0,
            _as_float(
                corrections.get("fsg_d_sigma"),
                _as_float(defaults.get("fsg_d_sigma"), 0.1),
            ),
        ),
    )
    corrections["fsg_gamma"] = max(
        0.0,
        min(
            10.0,
            _as_float(
                corrections.get("fsg_gamma"),
                _as_float(defaults.get("fsg_gamma"), 0.0),
            ),
        ),
    )
    corrections["replace_existing_cfg"] = _as_bool(
        corrections.get("replace_existing_cfg"),
        _as_bool(defaults.get("replace_existing_cfg"), False),
    )
    return corrections


def _normalize_aio_generation_settings(value) -> dict[str, Any]:
    settings = _merge_versioned_settings(
        AIO_GENERATION_DEFAULT_SETTINGS,
        _migrate_supported_aio_generation_settings(value),
    )
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
    stage_scope = dave.setdefault("stage_scope", {})
    if not isinstance(stage_scope, dict):
        stage_scope = {}
        dave["stage_scope"] = stage_scope
    default_stage_scope = default_dave["stage_scope"]
    for stage_id in AIO_GENERATION_STAGE_IDS:
        stage_scope[stage_id] = _as_bool(
            stage_scope.get(stage_id),
            default_stage_scope[stage_id],
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
    return _round_trip_aio_generation_settings(settings)


__all__ = ()
