"""Execution adapters for Advanced Prompt Studio node classes."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from contextlib import nullcontext
from dataclasses import dataclass
from typing import Any

from ..common.values import _as_bool
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
    _build_advanced_prompts,
    _clone_advanced_fields,
    _normalize_advanced_fields,
    _normalize_prompt_studio_wildcard_seed_control,
    _set_naia_field_text,
    _translate_prompt_fields,
    normalize_prompt_studio_wildcard_mode,
    normalize_seed,
)
from ..prompt.contracts import AdvancedField
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
class _AdvancedExecutionSnapshot:
    effective_fields_json: str
    saved_fields_json: str
    effective_field_inputs: tuple[tuple[str, str], ...]
    wildcard_changed: bool
    wildcard_used_keys: tuple[str, ...]
    wildcard_missing_keys: tuple[str, ...]


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
    execution_capture: Callable[[_AdvancedExecutionSnapshot], None] | None = None


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
    transform_fields: _Callback | None = None


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
    transform_result: Any = None


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
    if bindings.transform_fields is not None:
        state.effective_fields, state.transform_result = bindings.transform_fields(
            state.effective_fields
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
    if request.execution_capture is not None:
        request.execution_capture(_AdvancedExecutionSnapshot(
            effective_fields_json=_advanced_fields_json(state.effective_fields),
            saved_fields_json=fields_json,
            effective_field_inputs=tuple(state.effective_field_inputs.items()),
            wildcard_changed=bool(effective_wildcard["changed"]),
            wildcard_used_keys=tuple(effective_wildcard["used_keys"]),
            wildcard_missing_keys=tuple(effective_wildcard["missing_keys"]),
        ))
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
    output = {
        "ui": bindings.render_ui(
            ui_fields_json,
            state.requested_use_naia,
            state.effective_field_inputs,
            state.ui_updates,
        ),
        "result": (*result, state.width, state.height),
    }
    if bindings.transform_fields is not None:
        output["_transform_result"] = state.transform_result
    return output


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
            extra_pnginfo=request.extra_pnginfo,
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


__all__ = ()
