"""Execution adapters for Advanced Prompt Studio node classes."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from contextlib import nullcontext
from dataclasses import dataclass
from typing import Any, cast

from ..common.values import _as_bool, _as_int
from ..naia.resolution import (
    CUSTOM_ADVANCED_RESOLUTION_BUCKET,
    NAIA_ADVANCED_RESOLUTION_BUCKET,
    _advanced_resolution_from_selection,
    _resolution_label,
)
from ..prompt.advanced import (
    _advanced_enabled_naia_panes,
    _advanced_field_input_values,
    _advanced_fields_json,
    _advanced_naia_field_updates,
    _advanced_uses_naia_resolution,
    _apply_advanced_field_inputs,
    _build_advanced_prompt_data,
    _build_advanced_prompts,
    _clone_advanced_fields,
    _normalize_advanced_fields,
    _normalize_prompt_studio_wildcard_seed_control,
    _set_naia_field_text,
    _translate_prompt_fields,
    normalize_prompt_studio_wildcard_mode,
    normalize_seed,
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
from ..prompt.contracts import AdvancedField, PromptDataCompatResult
from ..prompt.data import _prompt_data_parameter_snapshot
from ..seed.compatibility import _scrub_reserved_wildcard_next_seed
from .seed_adapters import (
    PROMPT_STUDIO_ADVANCED_SEED_FEATURE,
    PromptStudioSeedExecution,
)

_WILDCARD_MODE_SEQUENTIAL = "sequential"
_WILDCARD_MODE_LABELS = ("일반", "순차")
_SEED_CONTROL_FIXED = "fixed"

_Callback = Callable[..., Any]


@dataclass(frozen=True)
class _AdvancedBuildRequest:
    use_naia: bool
    consume_naia_on_queue: bool
    use_anima_mod_guidance: bool
    pin_trigger_tags_to_front: bool
    advanced_fields: str
    use_negative_anima_mod_guidance: bool
    wildcard_mode: str
    wildcard_seed: int
    wildcard_seed_after_generate: str
    resolution_bucket: str
    resolution_size: str
    resolution_custom_width: int
    resolution_custom_height: int
    workflow_prompt: Any
    extra_pnginfo: Any
    unique_id: Any
    seed_execution: PromptStudioSeedExecution | None
    field_inputs: dict[str, Any]


@dataclass(frozen=True)
class _AdvancedExecutionBindings:
    update_metadata_fields: _Callback
    render_ui: _Callback
    seed_execution: _Callback
    next_seed: _Callback
    expand_fields: _Callback
    resolve_settings: Callable[[], Mapping[str, Any]]
    make_request_body: _Callback
    post_random: _Callback
    parse_random_response: _Callback
    resolve_naia_resolution: _Callback


@dataclass
class _AdvancedBuildState:
    fields: list[AdvancedField]
    saved_fields: list[AdvancedField]
    effective_fields: list[AdvancedField]
    effective_field_inputs: dict[str, str]
    requested_use_naia: bool
    enabled_naia_panes: tuple[str, ...]
    use_naia_resolution: bool
    live_use_naia: bool
    metadata_use_naia: bool
    metadata_updates: dict[str, Any]
    ui_updates: dict[str, Any]
    wildcard_mode_key: str
    wildcard_mode_label: str
    wildcard_seed_value: int
    wildcard_seed_control: str
    width: int
    height: int


def _prepare_advanced_build(request: _AdvancedBuildRequest) -> _AdvancedBuildState:
    fields = _normalize_advanced_fields(request.advanced_fields)
    saved_fields = _clone_advanced_fields(fields)
    effective_field_inputs = _advanced_field_input_values(request.field_inputs)
    requested_use_naia = _as_bool(request.use_naia, False)
    enabled_naia_panes = tuple(_advanced_enabled_naia_panes(fields))
    use_naia_resolution = _advanced_uses_naia_resolution(request.resolution_bucket)
    live_use_naia = requested_use_naia and (bool(enabled_naia_panes) or use_naia_resolution)
    wildcard_mode_key = normalize_prompt_studio_wildcard_mode(request.wildcard_mode)
    wildcard_mode_label = (
        _WILDCARD_MODE_LABELS[1]
        if wildcard_mode_key == _WILDCARD_MODE_SEQUENTIAL
        else _WILDCARD_MODE_LABELS[0]
    )
    effective_fields = _apply_advanced_field_inputs(fields, effective_field_inputs)
    wildcard_seed_value = normalize_seed(request.wildcard_seed)
    wildcard_seed_control = _normalize_prompt_studio_wildcard_seed_control(
        request.wildcard_seed_after_generate,
        request.wildcard_mode,
    )
    _scrub_reserved_wildcard_next_seed(
        request.field_inputs,
        request.workflow_prompt,
        request.unique_id,
    )
    width, height = _advanced_resolution_from_selection(
        request.resolution_bucket,
        request.resolution_size,
        request.resolution_custom_width,
        request.resolution_custom_height,
    )
    return _AdvancedBuildState(
        fields=fields,
        saved_fields=saved_fields,
        effective_fields=effective_fields,
        effective_field_inputs=effective_field_inputs,
        requested_use_naia=requested_use_naia,
        enabled_naia_panes=enabled_naia_panes,
        use_naia_resolution=use_naia_resolution,
        live_use_naia=live_use_naia,
        metadata_use_naia=live_use_naia,
        metadata_updates={},
        ui_updates={},
        wildcard_mode_key=wildcard_mode_key,
        wildcard_mode_label=wildcard_mode_label,
        wildcard_seed_value=wildcard_seed_value,
        wildcard_seed_control=wildcard_seed_control,
        width=width,
        height=height,
    )


def _apply_naia(
    state: _AdvancedBuildState,
    bindings: _AdvancedExecutionBindings,
) -> None:
    settings = bindings.resolve_settings()
    body = bindings.make_request_body(
        _as_bool(settings["use_naia_settings"], True),
        settings["pre_prompt"],
        settings["post_prompt"],
        settings["auto_hide"],
        settings["preprocessing"],
    )
    response = bindings.post_random(
        settings["host"],
        settings["port"],
        body,
        allow_remote_api=bool(settings.get("allow_remote_api", False)),
    )
    prompt, negative, width, height = bindings.parse_random_response(response)
    field_updates = _advanced_naia_field_updates(
        state.fields,
        {"positive": prompt, "negative": negative},
    )
    if field_updates:
        state.ui_updates["naia_field_updates"] = field_updates
    if "positive" in state.enabled_naia_panes:
        state.saved_fields = _set_naia_field_text(state.saved_fields, "positive", prompt)
        state.effective_fields = _set_naia_field_text(state.effective_fields, "positive", prompt)
    if "negative" in state.enabled_naia_panes:
        state.saved_fields = _set_naia_field_text(state.saved_fields, "negative", negative)
        state.effective_fields = _set_naia_field_text(state.effective_fields, "negative", negative)
    if state.use_naia_resolution:
        state.width, state.height = bindings.resolve_naia_resolution(width, height, settings)
        resolution_label = _resolution_label(state.width, state.height)
        state.ui_updates.update({
            "naia_resolution_update": {"width": state.width, "height": state.height},
            "resolution_bucket": NAIA_ADVANCED_RESOLUTION_BUCKET,
            "resolution_size": resolution_label,
            "resolution_custom_width": state.width,
            "resolution_custom_height": state.height,
        })
        state.metadata_updates.update({
            "resolution_bucket": CUSTOM_ADVANCED_RESOLUTION_BUCKET,
            "resolution_size": resolution_label,
            "resolution_custom_width": state.width,
            "resolution_custom_height": state.height,
        })
    state.metadata_use_naia = False


def _finish_advanced_build(
    request: _AdvancedBuildRequest,
    state: _AdvancedBuildState,
    bindings: _AdvancedExecutionBindings,
    seed_execution: PromptStudioSeedExecution,
) -> dict[str, Any]:
    ui_fields = _clone_advanced_fields(state.saved_fields)
    state.effective_fields, effective_wildcard = bindings.expand_fields(
        state.effective_fields,
        seed_execution.execution_seed,
        state.wildcard_mode_key,
    )
    state.effective_fields = _translate_prompt_fields(state.effective_fields)
    state.ui_updates.update({
        "wildcard_mode": state.wildcard_mode_label,
        "wildcard_execution_seed": seed_execution.execution_seed,
        "wildcard_seed": seed_execution.next_seed,
        "wildcard_seed_after_generate": state.wildcard_seed_control,
        "wildcard_used_keys": list(effective_wildcard["used_keys"]),
        "wildcard_missing_keys": list(effective_wildcard["missing_keys"]),
    })
    state.metadata_updates.update({
        "wildcard_mode": state.wildcard_mode_label,
        "wildcard_seed": seed_execution.execution_seed,
        "wildcard_seed_after_generate": _SEED_CONTROL_FIXED,
    })
    fields_json = _advanced_fields_json(state.saved_fields)
    ui_fields_json = _advanced_fields_json(ui_fields)
    if state.live_use_naia or state.metadata_updates:
        bindings.update_metadata_fields(
            request.workflow_prompt,
            request.extra_pnginfo,
            request.unique_id,
            fields_json,
            state.metadata_use_naia,
            state.metadata_updates,
        )
    result = _build_advanced_prompts(
        state.effective_fields,
        request.use_anima_mod_guidance,
        request.use_negative_anima_mod_guidance,
        request.pin_trigger_tags_to_front,
    )
    return {
        "ui": bindings.render_ui(
            ui_fields_json,
            state.requested_use_naia,
            state.effective_field_inputs,
            state.ui_updates,
        ),
        "result": (*result, state.width, state.height),
    }


def _build_prompt_studio_advanced(
    request: _AdvancedBuildRequest,
    bindings: _AdvancedExecutionBindings,
) -> dict[str, Any]:
    state = _prepare_advanced_build(request)
    seed_context = (
        nullcontext(request.seed_execution)
        if request.seed_execution is not None
        else bindings.seed_execution(
            feature=PROMPT_STUDIO_ADVANCED_SEED_FEATURE,
            unique_id=request.unique_id,
            seed=state.wildcard_seed_value,
            after_generate=state.wildcard_seed_control,
            fallback_next_seed=lambda: bindings.next_seed(
                state.wildcard_seed_value,
                state.wildcard_seed_control,
            ),
        )
    )
    with seed_context as seed_execution:
        if seed_execution is None:
            raise RuntimeError("Advanced seed execution was not reserved")
        if state.live_use_naia:
            _apply_naia(state, bindings)
        return _finish_advanced_build(request, state, bindings, seed_execution)


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


def _base_build(request: _AdvancedV2BuildRequest, base_build: _Callback) -> dict[str, Any]:
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
    expand_fields: _Callback,
) -> dict[str, Any]:
    base_request = request.base
    if base_request.seed_execution is None:
        raise RuntimeError("Advanced v2 seed execution was not reserved")
    base = _base_build(request, base_build)
    compat_result = cast(PromptDataCompatResult, tuple(base.get("result") or ()))
    ui_payloads = base.get("ui", {}).get("prompt_studio_advanced", [])
    ui_payload = ui_payloads[0] if ui_payloads and isinstance(ui_payloads[0], dict) else {}
    ui_payload.update(_artist_mix_ui_values(request))
    saved_fields = _normalize_advanced_fields(
        ui_payload.get("advanced_fields", base_request.advanced_fields)
    )
    effective_field_inputs = _advanced_field_input_values(
        ui_payload.get("field_inputs") or base_request.field_inputs
    )
    wildcard_mode_key = normalize_prompt_studio_wildcard_mode(base_request.wildcard_mode)
    effective_fields = _apply_advanced_field_inputs(saved_fields, effective_field_inputs)
    effective_fields, _wildcard = expand_fields(
        effective_fields,
        base_request.seed_execution.execution_seed,
        wildcard_mode_key,
    )
    effective_fields = _translate_prompt_fields(effective_fields)
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
        ui_payload,
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
    return {**base, "result": (prompt_data,)}


__all__ = ()
