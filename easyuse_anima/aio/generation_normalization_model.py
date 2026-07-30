from __future__ import annotations

from collections.abc import Callable
from typing import Any

from .generation_defaults import (
    AIO_GENERATION_DEFAULT_SETTINGS,
    AIO_GENERATION_STAGE_IDS,
)

ValueHelper = Callable[..., Any]


def _normalize_aio_dit_corrections_settings(
    value,
    defaults: dict[str, Any],
    *,
    as_bool: ValueHelper,
    as_float: ValueHelper,
    as_int: ValueHelper,
    choice: ValueHelper,
) -> dict[str, Any]:
    corrections = value if isinstance(value, dict) else {}

    def bounded_float(key: str, lower: float, upper: float, fallback: float) -> float:
        return max(
            lower,
            min(
                upper,
                as_float(
                    corrections.get(key),
                    as_float(defaults.get(key), fallback),
                ),
            ),
        )

    def bounded_int(key: str, lower: int, upper: int, fallback: int) -> int:
        return max(
            lower,
            min(
                upper,
                as_int(
                    corrections.get(key),
                    as_int(defaults.get(key), fallback),
                ),
            ),
        )

    corrections["enabled"] = as_bool(
        corrections.get("enabled"),
        as_bool(defaults.get("enabled"), False),
    )
    corrections["dcw_mode"] = choice(
        corrections.get("dcw_mode"),
        ("off", "manual", "auto"),
        str(defaults.get("dcw_mode") or "off"),
    )
    corrections["dcw_lambda"] = bounded_float("dcw_lambda", -1.0, 1.0, 0.01)
    corrections["dcw_band_mask"] = choice(
        corrections.get("dcw_band_mask"),
        ("LL", "all", "HH", "LH+HL+HH"),
        str(defaults.get("dcw_band_mask") or "LL"),
    )
    corrections["dcw_calibrator"] = str(
        corrections.get("dcw_calibrator")
        or defaults.get("dcw_calibrator")
        or "(auto-download default)"
    )
    corrections["smc_cfg"] = as_bool(
        corrections.get("smc_cfg"),
        as_bool(defaults.get("smc_cfg"), False),
    )
    corrections["adaptive_smc_alpha"] = bounded_float(
        "adaptive_smc_alpha", 0.0, 1.0, 0.0
    )
    corrections["smc_cfg_lambda"] = bounded_float(
        "smc_cfg_lambda", 0.0, 20.0, 6.0
    )
    corrections["cfgpp"] = as_bool(
        corrections.get("cfgpp"),
        as_bool(defaults.get("cfgpp"), False),
    )
    corrections["cfgpp_lambda"] = bounded_float("cfgpp_lambda", 0.0, 8.0, 0.0)
    corrections["fsg"] = as_bool(
        corrections.get("fsg"),
        as_bool(defaults.get("fsg"), False),
    )
    corrections["fsg_band_lo"] = bounded_float("fsg_band_lo", 0.0, 1.0, 0.59)
    corrections["fsg_band_hi"] = bounded_float("fsg_band_hi", 0.0, 1.0, 0.75)
    corrections["fsg_k"] = bounded_int("fsg_k", 0, 32, 3)
    corrections["fsg_d_sigma"] = bounded_float("fsg_d_sigma", 0.0, 1.0, 0.1)
    corrections["fsg_gamma"] = bounded_float("fsg_gamma", 0.0, 10.0, 0.0)
    corrections["replace_existing_cfg"] = as_bool(
        corrections.get("replace_existing_cfg"),
        as_bool(defaults.get("replace_existing_cfg"), False),
    )
    return corrections


def _normalize_dave_settings(
    model_patches: dict[str, Any],
    *,
    as_bool: ValueHelper,
    as_float: ValueHelper,
) -> None:
    aura_flow = model_patches.setdefault("aura_flow", {})
    if not isinstance(aura_flow, dict):
        aura_flow = {}
        model_patches["aura_flow"] = aura_flow
    aura_flow.pop("enabled", None)
    aura_flow["shift"] = max(1.0, min(10.0, as_float(aura_flow.get("shift"), 3.0)))

    dave = model_patches.setdefault("dave", {})
    if not isinstance(dave, dict):
        dave = {}
        model_patches["dave"] = dave
    defaults = AIO_GENERATION_DEFAULT_SETTINGS["model_patches"]["dave"]
    dave["enabled"] = as_bool(dave.get("enabled"), defaults["enabled"])
    dave["mask"] = str(dave.get("mask") or defaults["mask"])
    dave["strength"] = max(
        0.0,
        min(1.0, as_float(dave.get("strength"), defaults["strength"])),
    )
    dave["tau"] = max(0.0, min(1.0, as_float(dave.get("tau"), defaults["tau"])))
    stage_scope = dave.setdefault("stage_scope", {})
    if not isinstance(stage_scope, dict):
        stage_scope = {}
        dave["stage_scope"] = stage_scope
    default_scope = defaults["stage_scope"]
    for stage_id in AIO_GENERATION_STAGE_IDS:
        stage_scope[stage_id] = as_bool(
            stage_scope.get(stage_id),
            default_scope[stage_id],
        )


def _normalize_safe_pag_settings(
    model_patches: dict[str, Any],
    *,
    as_bool: ValueHelper,
    as_float: ValueHelper,
    choice: ValueHelper,
) -> None:
    safe_pag = model_patches.setdefault("safe_pag", {})
    if not isinstance(safe_pag, dict):
        safe_pag = {}
        model_patches["safe_pag"] = safe_pag
    defaults = AIO_GENERATION_DEFAULT_SETTINGS["model_patches"]["safe_pag"]
    safe_pag["enabled"] = as_bool(safe_pag.get("enabled"), defaults["enabled"])
    safe_pag["scale"] = max(
        0.0,
        min(100.0, as_float(safe_pag.get("scale"), defaults["scale"])),
    )
    safe_pag["block_indices"] = str(
        safe_pag.get("block_indices") or defaults["block_indices"]
    )
    safe_pag["perturbation_strength"] = max(
        0.0,
        min(
            1.0,
            as_float(
                safe_pag.get("perturbation_strength"),
                defaults["perturbation_strength"],
            ),
        ),
    )
    safe_pag["head_indices"] = str(
        safe_pag.get("head_indices") or defaults["head_indices"]
    )
    safe_pag["start_percent"] = max(
        0.0,
        min(1.0, as_float(safe_pag.get("start_percent"), defaults["start_percent"])),
    )
    safe_pag["end_percent"] = max(
        0.0,
        min(1.0, as_float(safe_pag.get("end_percent"), defaults["end_percent"])),
    )
    safe_pag["rescale"] = max(
        0.0,
        min(1.0, as_float(safe_pag.get("rescale"), defaults["rescale"])),
    )
    safe_pag["rescale_mode"] = choice(
        safe_pag.get("rescale_mode"), ("full", "partial"), "full"
    )
    stage_scope = safe_pag.setdefault("stage_scope", {})
    if not isinstance(stage_scope, dict):
        stage_scope = {stage_id: False for stage_id in AIO_GENERATION_STAGE_IDS}
        safe_pag["stage_scope"] = stage_scope
    for stage_id in AIO_GENERATION_STAGE_IDS:
        stage_scope[stage_id] = as_bool(stage_scope.get(stage_id), False)


def _normalize_kj_settings(
    model_patches: dict[str, Any],
    *,
    as_bool: ValueHelper,
    as_int: ValueHelper,
    choice: ValueHelper,
) -> None:
    kj = model_patches.setdefault("kj", {})
    if not isinstance(kj, dict):
        kj = {}
        model_patches["kj"] = kj
    kj["fp16_accumulation"] = as_bool(kj.get("fp16_accumulation"), False)
    kj["sage_attention"] = choice(
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
    kj["sage_allow_compile"] = as_bool(kj.get("sage_allow_compile"), False)
    stage_scope = kj.setdefault("sage_stage_scope", {})
    if not isinstance(stage_scope, dict):
        stage_scope = {stage_id: False for stage_id in AIO_GENERATION_STAGE_IDS}
        kj["sage_stage_scope"] = stage_scope
    for stage_id in AIO_GENERATION_STAGE_IDS:
        stage_scope[stage_id] = as_bool(stage_scope.get(stage_id), False)

    torch_compile = kj.setdefault("torch_compile", {})
    if not isinstance(torch_compile, dict):
        torch_compile = {}
        kj["torch_compile"] = torch_compile
    torch_compile["enabled"] = as_bool(torch_compile.get("enabled"), False)
    torch_compile["backend"] = choice(
        torch_compile.get("backend"), ("inductor", "cudagraphs"), "inductor"
    )
    torch_compile["fullgraph"] = as_bool(torch_compile.get("fullgraph"), False)
    torch_compile["mode"] = choice(
        torch_compile.get("mode"),
        ("default", "max-autotune", "max-autotune-no-cudagraphs", "reduce-overhead"),
        "max-autotune-no-cudagraphs",
    )
    torch_compile["dynamic"] = choice(
        torch_compile.get("dynamic"), ("auto", "true", "false"), "false"
    )
    torch_compile["compile_transformer_blocks_only"] = as_bool(
        torch_compile.get("compile_transformer_blocks_only"), True
    )
    torch_compile["dynamo_cache_size_limit"] = max(
        0,
        min(1024, as_int(torch_compile.get("dynamo_cache_size_limit"), 64)),
    )
    torch_compile["debug_compile_keys"] = as_bool(
        torch_compile.get("debug_compile_keys"), False
    )
    torch_compile["disable_dynamic_vram"] = as_bool(
        torch_compile.get("disable_dynamic_vram"), True
    )


def normalize_model_settings(
    settings: dict[str, Any],
    *,
    as_bool: ValueHelper,
    as_float: ValueHelper,
    as_int: ValueHelper,
    choice: ValueHelper,
) -> None:
    model_patches = settings.setdefault("model_patches", {})
    if not isinstance(model_patches, dict):
        model_patches = {}
        settings["model_patches"] = model_patches
    _normalize_dave_settings(model_patches, as_bool=as_bool, as_float=as_float)
    _normalize_safe_pag_settings(
        model_patches,
        as_bool=as_bool,
        as_float=as_float,
        choice=choice,
    )
    _normalize_kj_settings(
        model_patches,
        as_bool=as_bool,
        as_int=as_int,
        choice=choice,
    )


__all__ = ()
