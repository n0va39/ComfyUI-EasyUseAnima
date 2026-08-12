"""Execution adapter for Advanced Prompt Studio v2 structured output."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, cast

from ..common.values import _as_bool, _as_int
from ..lora.prompt_syntax import _extract_a1111_loras_from_fields
from ..prompt.advanced import (
    _build_advanced_prompt_data,
    _build_advanced_prompts,
    _normalize_advanced_fields,
    _normalize_prompt_studio_wildcard_seed_control,
    normalize_prompt_studio_wildcard_mode,
)
from ..prompt.artist_mix import (
    ARTIST_MIX_DEFAULT_CLUSTER_COUNT,
    ARTIST_MIX_DEFAULT_DOMINANT_ISOLATION,
    ARTIST_MIX_DEFAULT_DOMINANT_THRESHOLD,
    ARTIST_MIX_DEFAULT_EXACT_TOP_K,
    ARTIST_MIX_DEFAULT_RMS_SCALE_CAP,
    ARTIST_MIX_DEFAULT_START_PERCENT,
    ARTIST_MIX_DEFAULT_STRENGTH_SCALE,
    ARTIST_MIX_DEFAULT_STYLE_GAIN,
    ARTIST_MIX_MODE_OFF,
    _bounded_artist_mix_float,
    _bounded_artist_mix_int,
    _normalize_artist_mix_mode,
)
from ..prompt.contracts import PromptDataCompatResult
from ..prompt.data import _prompt_data_parameter_snapshot
from .prompt_advanced_execution import (
    _AdvancedBuildRequest,
    _AdvancedExecutionSnapshot,
)

_WILDCARD_MODE_SEQUENTIAL = "sequential"
_WILDCARD_MODE_LABELS = ("일반", "순차")

_Callback = Callable[..., Any]


@dataclass(frozen=True)
class _AdvancedV2BuildRequest:
    base: _AdvancedBuildRequest
    artist_mix_mode: str
    artist_mix_start_percent: float
    artist_mix_strength_scale: float
    artist_mix_style_gain: float
    artist_mix_rms_scale_cap: float
    artist_mix_exact_top_k: int
    artist_mix_cluster_count: int
    artist_mix_dominant_isolation: bool
    artist_mix_dominant_threshold: float


def _artist_mix_ui_values(request: _AdvancedV2BuildRequest) -> dict[str, Any]:
    return {
        "artist_mix_mode": _normalize_artist_mix_mode(request.artist_mix_mode, ARTIST_MIX_MODE_OFF),
        "artist_mix_start_percent": _bounded_artist_mix_float(
            request.artist_mix_start_percent, ARTIST_MIX_DEFAULT_START_PERCENT, 0.0, 1.0
        ),
        "artist_mix_strength_scale": _bounded_artist_mix_float(
            request.artist_mix_strength_scale, ARTIST_MIX_DEFAULT_STRENGTH_SCALE, 0.0, 5.0
        ),
        "artist_mix_style_gain": _bounded_artist_mix_float(
            request.artist_mix_style_gain, ARTIST_MIX_DEFAULT_STYLE_GAIN, 0.0, 3.0
        ),
        "artist_mix_rms_scale_cap": _bounded_artist_mix_float(
            request.artist_mix_rms_scale_cap, ARTIST_MIX_DEFAULT_RMS_SCALE_CAP, 1.0, 5.0
        ),
        "artist_mix_exact_top_k": _bounded_artist_mix_int(
            request.artist_mix_exact_top_k, ARTIST_MIX_DEFAULT_EXACT_TOP_K, 0, 64
        ),
        "artist_mix_cluster_count": _bounded_artist_mix_int(
            request.artist_mix_cluster_count, ARTIST_MIX_DEFAULT_CLUSTER_COUNT, 1, 32
        ),
        "artist_mix_dominant_isolation": _as_bool(
            request.artist_mix_dominant_isolation, ARTIST_MIX_DEFAULT_DOMINANT_ISOLATION
        ),
        "artist_mix_dominant_threshold": _bounded_artist_mix_float(
            request.artist_mix_dominant_threshold, ARTIST_MIX_DEFAULT_DOMINANT_THRESHOLD, 0.0, 1.0
        ),
    }


def _base_build(
    request: _AdvancedV2BuildRequest,
    base_build: _Callback,
    execution_capture: Callable[[_AdvancedExecutionSnapshot], None],
) -> dict[str, Any]:
    base = request.base
    return base_build(
        base.use_naia,
        base.consume_naia_on_queue,
        base.use_anima_mod_guidance,
        base.pin_trigger_tags_to_front,
        base.advanced_fields,
        use_negative_anima_mod_guidance=base.use_negative_anima_mod_guidance,
        wildcard_mode=base.wildcard_mode,
        wildcard_seed=base.wildcard_seed,
        wildcard_seed_after_generate=base.wildcard_seed_after_generate,
        resolution_bucket=base.resolution_bucket,
        resolution_size=base.resolution_size,
        resolution_custom_width=base.resolution_custom_width,
        resolution_custom_height=base.resolution_custom_height,
        workflow_prompt=base.workflow_prompt,
        extra_pnginfo=base.extra_pnginfo,
        unique_id=base.unique_id,
        _seed_execution=base.seed_execution,
        _execution_capture=execution_capture,
        **base.field_inputs,
    )


def _v2_parameter_snapshot(
    request: _AdvancedV2BuildRequest,
    ui_payload: dict[str, Any],
    input_types: _Callback,
) -> dict[str, Any]:
    base = request.base
    wildcard_mode_key = normalize_prompt_studio_wildcard_mode(base.wildcard_mode)
    parameters = _prompt_data_parameter_snapshot(
        input_types().get("required", {}),
        {
            "use_naia": base.use_naia,
            "consume_naia_on_queue": base.consume_naia_on_queue,
            "use_anima_mod_guidance": base.use_anima_mod_guidance,
            "pin_trigger_tags_to_front": base.pin_trigger_tags_to_front,
            "advanced_fields": base.advanced_fields,
            "use_negative_anima_mod_guidance": base.use_negative_anima_mod_guidance,
            "wildcard_mode": (
                _WILDCARD_MODE_LABELS[1]
                if wildcard_mode_key == _WILDCARD_MODE_SEQUENTIAL
                else _WILDCARD_MODE_LABELS[0]
            ),
            "wildcard_seed": base.wildcard_seed,
            "wildcard_seed_after_generate": _normalize_prompt_studio_wildcard_seed_control(
                base.wildcard_seed_after_generate, base.wildcard_mode
            ),
            "resolution_bucket": base.resolution_bucket,
            "resolution_size": base.resolution_size,
            "resolution_custom_width": base.resolution_custom_width,
            "resolution_custom_height": base.resolution_custom_height,
            "artist_mix_mode": request.artist_mix_mode,
            "artist_mix_start_percent": request.artist_mix_start_percent,
            "artist_mix_strength_scale": request.artist_mix_strength_scale,
            "artist_mix_style_gain": request.artist_mix_style_gain,
            "artist_mix_rms_scale_cap": request.artist_mix_rms_scale_cap,
            "artist_mix_exact_top_k": request.artist_mix_exact_top_k,
            "artist_mix_cluster_count": request.artist_mix_cluster_count,
            "artist_mix_dominant_isolation": request.artist_mix_dominant_isolation,
            "artist_mix_dominant_threshold": request.artist_mix_dominant_threshold,
            **base.field_inputs,
        },
        ui_payload,
    )
    if base.seed_execution is None:
        raise RuntimeError("Advanced v2 seed execution was not reserved")
    parameters["wildcard_seed"] = base.seed_execution.execution_seed
    return parameters


def _build_prompt_studio_advanced_v2(
    request: _AdvancedV2BuildRequest,
    *,
    base_build: _Callback,
    input_types: _Callback,
) -> dict[str, Any]:
    base_request = request.base
    if base_request.seed_execution is None:
        raise RuntimeError("Advanced v2 seed execution was not reserved")
    snapshots: list[_AdvancedExecutionSnapshot] = []
    base = _base_build(request, base_build, snapshots.append)
    if len(snapshots) != 1:
        raise RuntimeError("Advanced v2 base execution snapshot was not captured exactly once")
    snapshot = snapshots[0]
    compat_result = cast(PromptDataCompatResult, tuple(base.get("result") or ()))
    ui_payloads = base.get("ui", {}).get("prompt_studio_advanced", [])
    ui_payload = ui_payloads[0] if ui_payloads and isinstance(ui_payloads[0], dict) else {}
    ui_payload.update(_artist_mix_ui_values(request))
    saved_fields = _normalize_advanced_fields(snapshot.saved_fields_json)
    effective_fields = _normalize_advanced_fields(snapshot.effective_fields_json)
    effective_field_inputs = dict(snapshot.effective_field_inputs)
    effective_fields, lora_directives = _extract_a1111_loras_from_fields(effective_fields)
    wildcard_updates = dict(ui_payload)
    wildcard_updates.update({
        "wildcard_changed": snapshot.wildcard_changed,
        "wildcard_used_keys": list(snapshot.wildcard_used_keys),
        "wildcard_missing_keys": list(snapshot.wildcard_missing_keys),
    })
    compat_result = cast(
        PromptDataCompatResult,
        (
            *_build_advanced_prompts(
                effective_fields,
                base_request.use_anima_mod_guidance,
                base_request.use_negative_anima_mod_guidance,
                base_request.pin_trigger_tags_to_front,
            ),
            compat_result[-2],
            compat_result[-1],
        ),
    )
    prompt_data = _build_advanced_prompt_data(
        compat_result,
        effective_fields,
        saved_fields,
        effective_field_inputs,
        str(ui_payload.get("resolution_bucket", base_request.resolution_bucket)),
        str(ui_payload.get("resolution_size", base_request.resolution_size)),
        _as_int(
            ui_payload.get("resolution_custom_width", base_request.resolution_custom_width),
            base_request.resolution_custom_width,
        ),
        _as_int(
            ui_payload.get("resolution_custom_height", base_request.resolution_custom_height),
            base_request.resolution_custom_height,
        ),
        str(ui_payload.get("wildcard_mode", base_request.wildcard_mode)),
        base_request.seed_execution.execution_seed,
        str(ui_payload.get("wildcard_seed_after_generate", base_request.wildcard_seed_after_generate)),
        wildcard_updates,
        base_request.pin_trigger_tags_to_front,
        parameters=_v2_parameter_snapshot(request, ui_payload, input_types),
        artist_mix_mode=request.artist_mix_mode,
        artist_mix_start_percent=request.artist_mix_start_percent,
        artist_mix_strength_scale=request.artist_mix_strength_scale,
        artist_mix_style_gain=request.artist_mix_style_gain,
        artist_mix_rms_scale_cap=request.artist_mix_rms_scale_cap,
        artist_mix_exact_top_k=request.artist_mix_exact_top_k,
        artist_mix_cluster_count=request.artist_mix_cluster_count,
        artist_mix_dominant_isolation=request.artist_mix_dominant_isolation,
        artist_mix_dominant_threshold=request.artist_mix_dominant_threshold,
    )
    prompt_data["lora"] = {"syntax": "a1111", "directives": lora_directives}
    return {**base, "result": (prompt_data,)}


__all__ = ()
