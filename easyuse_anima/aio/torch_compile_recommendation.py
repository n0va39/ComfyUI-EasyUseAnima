"""Pure Torch Compile workload classification and recommendation policy."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

AIO_TORCH_COMPILE_RECOMMENDATION_POLICY_VERSION = "recommendation-v1"

_LOW_VRAM_LIMIT_MB = 8192
_HIGH_VRAM_MINIMUM_MB = 15360
_COMMON_VALUES = {
    "enabled": True,
    "backend": "inductor",
    "fullgraph": False,
    "mode": "default",
    "dynamic": "auto",
    "compile_transformer_blocks_only": True,
    "dynamo_cache_size_limit": 64,
    "debug_compile_keys": False,
    "disable_dynamic_vram": False,
}


def _mapping(value: object) -> Mapping[str, object] | None:
    return value if isinstance(value, Mapping) else None


def _enabled_section(
    settings: Mapping[str, object],
    name: str,
) -> tuple[bool | None, Mapping[str, object] | None]:
    section = _mapping(settings.get(name))
    if section is None or type(section.get("enabled")) is not bool:
        return None, section
    return bool(section["enabled"]), section


def classify_torch_compile_workload(
    generation_settings: Mapping[str, object],
    resolution: Mapping[str, object],
    batch_size: int,
) -> dict[str, object]:
    """Classify shape stability from the explicit AiO stage configuration."""

    width = resolution.get("width")
    height = resolution.get("height")
    resolution_known = (
        type(width) is int
        and type(height) is int
        and width > 0
        and height > 0
    )
    batch_known = type(batch_size) is int and batch_size > 0
    highres_enabled, _highres = _enabled_section(generation_settings, "highres")
    detailer_enabled, _detailer = _enabled_section(generation_settings, "detailer")
    upscale_enabled, upscale = _enabled_section(generation_settings, "upscale")

    active_shape_stages: list[str] = []
    reasons: list[str] = []
    stage_contract_known = None not in (
        highres_enabled,
        detailer_enabled,
        upscale_enabled,
    )
    if highres_enabled:
        active_shape_stages.append("highres")
        reasons.append("highres_changes_shape")
    if detailer_enabled:
        active_shape_stages.append("detailer")
        reasons.append("detailer_uses_variable_crops")
    if upscale_enabled:
        backend = upscale.get("backend") if upscale is not None else None
        if backend == "usdu":
            active_shape_stages.append("upscale")
            reasons.append("usdu_uses_tiles")
        elif backend == "resshift":
            reasons.append("resshift_has_no_sampling_model")
        else:
            stage_contract_known = False
            reasons.append("upscale_backend_unknown")

    if not resolution_known:
        reasons.append("base_resolution_unknown")
    if not batch_known:
        reasons.append("batch_size_unknown")
    if not stage_contract_known:
        reasons.append("stage_shape_contract_unknown")

    if not resolution_known or not batch_known or not stage_contract_known:
        shape_class = "unknown"
    elif active_shape_stages:
        shape_class = "variable_shapes"
    else:
        shape_class = "fixed_shapes"

    return {
        "shape_class": shape_class,
        "active_shape_stages": active_shape_stages,
        "resolution": (
            {"width": width, "height": height}
            if resolution_known
            else None
        ),
        "batch_size": batch_size if batch_known else None,
        "reason_codes": reasons,
    }


def classify_torch_compile_vram(total_vram_mb: object) -> str:
    if type(total_vram_mb) is not int or total_vram_mb <= 0:
        return "unknown"
    if total_vram_mb < _LOW_VRAM_LIMIT_MB:
        return "low"
    if total_vram_mb < _HIGH_VRAM_MINIMUM_MB:
        return "medium"
    return "high"


def _choice_values(environment: Mapping[str, object], name: str) -> list[str]:
    input_options = _mapping(environment.get("input_options"))
    values = input_options.get(name) if input_options is not None else None
    if not isinstance(values, Sequence) or isinstance(values, (str, bytes)):
        return []
    return [value for value in values if isinstance(value, str)]


def _supported_input_names(environment: Mapping[str, object]) -> set[str]:
    values = environment.get("supported_inputs")
    if not isinstance(values, Sequence) or isinstance(values, (str, bytes)):
        return set()
    return {value for value in values if isinstance(value, str)}


def _string_list(value: object) -> list[str]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return []
    return [item for item in value if isinstance(item, str)]


def _profile(shape_class: str, vram_tier: str) -> str:
    if vram_tier == "low":
        return "conservative_low_vram"
    if vram_tier == "unknown":
        return "conservative_unknown"
    if shape_class == "fixed_shapes":
        return "stable_fixed_shapes"
    if shape_class == "variable_shapes":
        return "stable_variable_shapes"
    return "conservative_unknown"


def recommend_torch_compile(
    diagnostics: Mapping[str, object],
    generation_settings: Mapping[str, object],
    resolution: Mapping[str, object],
    batch_size: int,
) -> dict[str, object]:
    """Return a deterministic recommendation without importing or invoking torch."""

    environment = dict(_mapping(diagnostics.get("environment")) or {})
    workload = classify_torch_compile_workload(
        generation_settings,
        resolution,
        batch_size,
    )
    vram_tier = classify_torch_compile_vram(environment.get("total_vram_mb"))
    workload["vram_tier"] = vram_tier

    reason_codes = _string_list(diagnostics.get("reason_codes"))
    warnings = [
        value
        for value in _string_list(diagnostics.get("warnings"))
        if value != "recommendation_policy_pending"
    ]
    reason_codes.extend(_string_list(workload.get("reason_codes")))
    reason_codes.extend((f"workload_{workload['shape_class']}", f"vram_{vram_tier}"))

    payload = {
        **diagnostics,
        "policy_version": AIO_TORCH_COMPILE_RECOMMENDATION_POLICY_VERSION,
        "environment": environment,
        "workload": {
            key: value for key, value in workload.items() if key != "reason_codes"
        },
        "reason_codes": list(dict.fromkeys(reason_codes)),
        "warnings": warnings,
    }
    if diagnostics.get("supported") is not True:
        payload.update(
            {
                "supported": False,
                "profile": "unsupported",
                "values": {},
                "warnings": list(dict.fromkeys(warnings + ["recommendation_unavailable"])),
            }
        )
        return payload

    supported_inputs = _supported_input_names(environment)
    required_inputs = set(_COMMON_VALUES) - {"enabled"}
    if not required_inputs.issubset(supported_inputs):
        payload.update(
            {
                "supported": False,
                "profile": "unsupported",
                "values": {},
                "reason_codes": list(
                    dict.fromkeys(reason_codes + ["kj_recommendation_input_drift"])
                ),
                "warnings": list(dict.fromkeys(warnings + ["recommendation_unavailable"])),
            }
        )
        return payload

    backend_options = _choice_values(environment, "backend")
    mode_options = _choice_values(environment, "mode")
    dynamic_options = _choice_values(environment, "dynamic")
    if "inductor" not in backend_options or "default" not in mode_options:
        payload.update(
            {
                "supported": False,
                "profile": "unsupported",
                "values": {},
                "reason_codes": list(
                    dict.fromkeys(reason_codes + ["kj_safe_choice_unavailable"])
                ),
                "warnings": list(dict.fromkeys(warnings + ["recommendation_unavailable"])),
            }
        )
        return payload

    values = dict(_COMMON_VALUES)
    target_dynamic = "false" if workload["shape_class"] == "fixed_shapes" else "auto"
    if target_dynamic not in dynamic_options:
        if target_dynamic != "false" or "auto" not in dynamic_options:
            payload.update(
                {
                    "supported": False,
                    "profile": "unsupported",
                    "values": {},
                    "reason_codes": list(
                        dict.fromkeys(reason_codes + ["kj_safe_choice_unavailable"])
                    ),
                    "warnings": list(
                        dict.fromkeys(warnings + ["recommendation_unavailable"])
                    ),
                }
            )
            return payload
        target_dynamic = "auto"
        warnings.append("dynamic_choice_conservative_fallback")
    values["dynamic"] = target_dynamic

    if workload["shape_class"] == "variable_shapes":
        warnings.append("shape_changes_may_recompile")
    elif workload["shape_class"] == "unknown":
        warnings.append("workload_shape_unknown")
    if vram_tier == "low":
        warnings.append("low_vram_peak_risk")
    elif vram_tier == "unknown":
        warnings.append("vram_unknown")
    if isinstance(workload["batch_size"], int) and workload["batch_size"] > 1:
        warnings.append("batch_size_increases_memory")
    warnings.append("first_compile_may_be_slow")

    payload.update(
        {
            "supported": True,
            "profile": _profile(str(workload["shape_class"]), vram_tier),
            "values": values,
            "reason_codes": list(dict.fromkeys(reason_codes)),
            "warnings": list(dict.fromkeys(warnings)),
        }
    )
    return payload


__all__ = [
    "AIO_TORCH_COMPILE_RECOMMENDATION_POLICY_VERSION",
    "classify_torch_compile_vram",
    "classify_torch_compile_workload",
    "recommend_torch_compile",
]
