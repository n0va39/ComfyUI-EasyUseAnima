"""Public ComfyUI-ppm NegPip adapter for AiO generation."""

from __future__ import annotations

import inspect
from collections.abc import Callable, Mapping
from typing import Any

from ..infrastructure.comfy.invocation import _node_output_tuple
from ..infrastructure.comfy.wiring import resolve_comfy_host_helper

NEGPIP_NODE_ID = "CLIPNegPip"
NEGPIP_NODE_PACK = "ComfyUI-ppm"
NEGPIP_REPOSITORY = "https://github.com/pamparamm/ComfyUI-ppm"
NEGPIP_CONTRACT_REVISION = 1

NEGPIP_MODE_OFF = "off"
NEGPIP_MODE_ON = "on"

_EXPECTED_INPUTS = {
    "model": "MODEL",
    "clip": "CLIP",
}
_EXPECTED_OUTPUTS = ("MODEL", "CLIP")


def _missing_host_helper(name: str):
    raise RuntimeError(
        f"[EasyUseAnima] AiO NegPip Comfy host helper is unavailable: {name}"
    )


def _require_custom_node_class(
    node_id: str,
    node_pack: str,
    install_hint: str,
):
    helper = resolve_comfy_host_helper(
        "_require_custom_node_class",
        _missing_host_helper,
    )
    return helper(node_id, node_pack, install_hint)


def _payload(*, available: bool, reason_codes: list[str]) -> dict[str, Any]:
    return {
        "available": available,
        "compatible": (
            available and reason_codes == ["ppm_negpip_contract_ready"]
        ),
        "node_id": NEGPIP_NODE_ID,
        "node_pack": NEGPIP_NODE_PACK,
        "repository": NEGPIP_REPOSITORY,
        "contract_revision": NEGPIP_CONTRACT_REVISION,
        "reason_codes": reason_codes,
    }


def _input_type_name(value: Any) -> str | None:
    if not isinstance(value, (list, tuple)) or not value:
        return None
    input_type = value[0]
    return input_type if isinstance(input_type, str) else None


def _execute_contract_is_compatible(method: Any) -> bool:
    if not callable(method):
        return False
    try:
        parameters = inspect.signature(method).parameters
    except (TypeError, ValueError):
        return False

    accepts_kwargs = any(
        parameter.kind == inspect.Parameter.VAR_KEYWORD
        for parameter in parameters.values()
    )
    for name in _EXPECTED_INPUTS:
        parameter = parameters.get(name)
        if parameter is None:
            if not accepts_kwargs:
                return False
            continue
        if parameter.kind == inspect.Parameter.POSITIONAL_ONLY:
            return False

    for name, parameter in parameters.items():
        if name in _EXPECTED_INPUTS or parameter.kind in (
            inspect.Parameter.VAR_POSITIONAL,
            inspect.Parameter.VAR_KEYWORD,
        ):
            continue
        if parameter.default is inspect.Parameter.empty:
            return False
    return True


def _inspect_negpip_node_class(node_class: Any) -> list[str]:
    reasons: list[str] = []
    try:
        input_types = node_class.INPUT_TYPES()
        required = input_types.get("required", {})
        if not isinstance(required, dict):
            raise TypeError("required inputs must be a mapping")
        if set(required) != set(_EXPECTED_INPUTS) or any(
            _input_type_name(required.get(name)) != input_type
            for name, input_type in _EXPECTED_INPUTS.items()
        ):
            reasons.append("ppm_negpip_input_contract_drift")

        return_types = tuple(node_class.RETURN_TYPES)
        if return_types != _EXPECTED_OUTPUTS:
            reasons.append("ppm_negpip_output_contract_drift")

        if not _execute_contract_is_compatible(
            getattr(node_class, "execute", None)
        ):
            reasons.append("ppm_negpip_execute_contract_drift")
    except Exception:
        return ["ppm_negpip_contract_unreadable"]
    return reasons or ["ppm_negpip_contract_ready"]


def collect_negpip_contract(
    find_node_class: Callable[[str], Any],
) -> dict[str, Any]:
    """Inspect the loaded public node class without importing its package."""

    try:
        node_class = find_node_class(NEGPIP_NODE_ID)
    except Exception:
        return _payload(
            available=False,
            reason_codes=["ppm_negpip_contract_unreadable"],
        )
    if node_class is None:
        return _payload(
            available=False,
            reason_codes=["ppm_negpip_missing"],
        )
    return _payload(
        available=True,
        reason_codes=_inspect_negpip_node_class(node_class),
    )


def invoke_negpip_node(node_class: Any, model: Any, clip: Any) -> tuple[Any, Any]:
    """Invoke one compatible public CLIPNegPip node call."""

    if node_class is None:
        raise RuntimeError(
            "[EasyUseAnima] Missing required custom node 'CLIPNegPip'. "
            "Install/enable ComfyUI-ppm, then restart ComfyUI. "
            f"Repository: {NEGPIP_REPOSITORY}"
        )

    reason_codes = _inspect_negpip_node_class(node_class)
    if reason_codes != ["ppm_negpip_contract_ready"]:
        raise RuntimeError(
            "[EasyUseAnima] CLIPNegPip public node contract is incompatible: "
            f"{', '.join(reason_codes)}. Update ComfyUI-ppm or disable NegPip."
        )

    result = node_class.execute(model=model, clip=clip)
    values = _node_output_tuple(result)
    if len(values) != 2 or values[0] is None or values[1] is None:
        raise RuntimeError(
            "[EasyUseAnima] CLIPNegPip returned an invalid MODEL/CLIP result."
        )
    if values[0] is model or values[1] is clip:
        raise RuntimeError(
            "[EasyUseAnima] CLIPNegPip did not return cloned MODEL/CLIP outputs."
        )
    return values[0], values[1]


def _aio_negpip_mode(value: object) -> str:
    if value is None:
        return NEGPIP_MODE_OFF
    if not isinstance(value, Mapping):
        raise RuntimeError(
            "[EasyUseAnima] AiO NegPip settings are malformed; "
            "disable NegPip or select a supported mode."
        )
    mode = value.get("mode")
    if mode not in (NEGPIP_MODE_OFF, NEGPIP_MODE_ON):
        raise RuntimeError(
            f"[EasyUseAnima] Unsupported AiO NegPip mode: {mode!r}. "
            "AIO-NEGPIP-02 supports only 'off' and 'on'."
        )
    return str(mode)


def _aio_negpip_cache_signature(value: object) -> dict[str, object] | None:
    mode = _aio_negpip_mode(value)
    if mode == NEGPIP_MODE_OFF:
        return None
    return {
        "mode": mode,
        "contract_revision": NEGPIP_CONTRACT_REVISION,
    }


def _aio_negpip_metadata(mode: str) -> dict[str, object] | None:
    if mode == NEGPIP_MODE_OFF:
        return None
    if mode != NEGPIP_MODE_ON:
        raise RuntimeError(
            f"[EasyUseAnima] Unsupported normalized AiO NegPip mode: {mode!r}."
        )
    return {
        "mode": mode,
        "contract_revision": NEGPIP_CONTRACT_REVISION,
    }


def apply_aio_negpip(model: Any, clip: Any, mode: str) -> tuple[Any, Any]:
    """Apply the public NegPip adapter once when the normalized mode is On."""

    if mode == NEGPIP_MODE_OFF:
        return model, clip
    if mode != NEGPIP_MODE_ON:
        raise RuntimeError(
            f"[EasyUseAnima] Unsupported normalized AiO NegPip mode: {mode!r}."
        )
    node_class = _require_custom_node_class(
        NEGPIP_NODE_ID,
        NEGPIP_NODE_PACK,
        f"Required for AiO NegPip On mode. Repository: {NEGPIP_REPOSITORY}",
    )
    return invoke_negpip_node(node_class, model, clip)


__all__ = ()
