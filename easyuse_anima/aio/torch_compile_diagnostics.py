"""Read-only environment and KJNodes contract diagnostics for Torch Compile."""

from __future__ import annotations

import importlib
import inspect
import platform
from collections.abc import Callable, Mapping, Sequence
from typing import Any

from ..infrastructure.comfy.capabilities import _find_loaded_node_class

AIO_TORCH_COMPILE_DIAGNOSTICS_SCHEMA_VERSION = 1
AIO_TORCH_COMPILE_DIAGNOSTICS_POLICY_VERSION = "diagnostics-v1"
TORCH_COMPILE_NODE_ID = "TorchCompileModelAdvanced"

_EXPECTED_PATCH_PARAMETERS = (
    "model",
    "backend",
    "fullgraph",
    "mode",
    "dynamic",
    "dynamo_cache_size_limit",
    "compile_transformer_blocks_only",
    "debug_compile_keys",
    "disable_dynamic_vram",
)
_REQUIRED_NODE_INPUTS = _EXPECTED_PATCH_PARAMETERS[:-1]
_OPTIONAL_NODE_INPUTS = (_EXPECTED_PATCH_PARAMETERS[-1],)
_CHOICE_INPUTS = ("backend", "mode", "dynamic")
_MAX_TEXT_LENGTH = 160
_MAX_INPUT_NAMES = 64
_MAX_CHOICES = 32


def _bounded_text(value: object, *, fallback: str = "") -> str:
    try:
        text = str(value or fallback)
    except Exception:
        text = fallback
    return text[:_MAX_TEXT_LENGTH]


def _torch_module():
    return importlib.import_module("torch")


def _input_map(value: object) -> dict[str, object]:
    if not isinstance(value, Mapping):
        return {}
    merged: dict[str, object] = {}
    for section in ("required", "optional"):
        inputs = value.get(section)
        if not isinstance(inputs, Mapping):
            continue
        for name, spec in inputs.items():
            if isinstance(name, str) and len(merged) < _MAX_INPUT_NAMES:
                merged[name] = spec
    return merged


def _choice_values(spec: object) -> list[str]:
    if not isinstance(spec, Sequence) or isinstance(spec, (str, bytes)) or not spec:
        return []
    source: object = spec[0]
    if source == "COMBO" and len(spec) > 1 and isinstance(spec[1], Mapping):
        source = spec[1].get("options")
    if not isinstance(source, Sequence) or isinstance(source, (str, bytes)):
        return []
    values: list[str] = []
    for value in source:
        if not isinstance(value, (str, int, float, bool)):
            continue
        normalized = _bounded_text(value)
        if normalized and normalized not in values:
            values.append(normalized)
        if len(values) >= _MAX_CHOICES:
            break
    return values


def _patch_signature_compatible(node_class: type) -> bool:
    patch = getattr(node_class, "patch", None)
    if not callable(patch):
        return False
    try:
        parameters = list(inspect.signature(patch).parameters.values())
    except (TypeError, ValueError):
        return False
    if parameters and parameters[0].name in {"self", "cls"}:
        parameters = parameters[1:]
    positional = [
        parameter
        for parameter in parameters
        if parameter.kind
        in (inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD)
    ]
    if tuple(parameter.name for parameter in positional[: len(_EXPECTED_PATCH_PARAMETERS)]) != (
        _EXPECTED_PATCH_PARAMETERS
    ):
        return False
    return not any(
        parameter.default is inspect.Parameter.empty
        and parameter.kind
        in (
            inspect.Parameter.POSITIONAL_ONLY,
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
            inspect.Parameter.KEYWORD_ONLY,
        )
        for parameter in parameters[len(_EXPECTED_PATCH_PARAMETERS) :]
    )


def _kj_contract(
    find_node_class: Callable[[str], Any],
) -> dict[str, object]:
    try:
        node_class = find_node_class(TORCH_COMPILE_NODE_ID)
    except Exception:
        node_class = None
    if node_class is None:
        return {
            "available": False,
            "compatible": False,
            "supported_inputs": [],
            "input_options": {},
            "missing_inputs": list(_REQUIRED_NODE_INPUTS + _OPTIONAL_NODE_INPUTS),
            "unexpected_required_inputs": [],
            "signature_compatible": False,
            "inspection_error": False,
        }

    try:
        input_types = node_class.INPUT_TYPES()
        required = input_types.get("required", {}) if isinstance(input_types, Mapping) else {}
        if not isinstance(required, Mapping):
            required = {}
        inputs = _input_map(input_types)
        missing_inputs = [
            name
            for name in _REQUIRED_NODE_INPUTS + _OPTIONAL_NODE_INPUTS
            if name not in inputs
        ]
        unexpected_required = sorted(
            str(name)
            for name in required
            if isinstance(name, str) and name not in _EXPECTED_PATCH_PARAMETERS
        )[:_MAX_INPUT_NAMES]
        signature_compatible = _patch_signature_compatible(node_class)
        return {
            "available": True,
            "compatible": not missing_inputs
            and not unexpected_required
            and signature_compatible,
            "supported_inputs": sorted(inputs)[:_MAX_INPUT_NAMES],
            "input_options": {
                name: _choice_values(inputs.get(name)) for name in _CHOICE_INPUTS
            },
            "missing_inputs": missing_inputs,
            "unexpected_required_inputs": unexpected_required,
            "signature_compatible": signature_compatible,
            "inspection_error": False,
        }
    except Exception:
        return {
            "available": True,
            "compatible": False,
            "supported_inputs": [],
            "input_options": {},
            "missing_inputs": list(_REQUIRED_NODE_INPUTS + _OPTIONAL_NODE_INPUTS),
            "unexpected_required_inputs": [],
            "signature_compatible": False,
            "inspection_error": True,
        }


def _accelerator_environment(torch: Any) -> tuple[dict[str, object], list[str]]:
    warnings: list[str] = []
    version = getattr(torch, "version", None)
    cuda_version = _bounded_text(getattr(version, "cuda", None)) or None
    rocm_version = _bounded_text(getattr(version, "hip", None)) or None
    cuda = getattr(torch, "cuda", None)
    cuda_is_available = getattr(cuda, "is_available", None)
    try:
        cuda_available = bool(callable(cuda_is_available) and cuda_is_available())
    except Exception:
        cuda_available = False
        warnings.append("accelerator_probe_failed")

    accelerator = "cpu"
    device_name = None
    compute_capability = None
    total_vram_mb = None
    if cuda_available:
        accelerator = "rocm" if rocm_version else "cuda"
        try:
            current_device = getattr(cuda, "current_device", None)
            get_device_properties = getattr(cuda, "get_device_properties", None)
            if not callable(current_device) or not callable(get_device_properties):
                raise AttributeError("CUDA device property API is unavailable")
            device_index = current_device()
            if type(device_index) is not int:
                raise TypeError("CUDA current_device() did not return an integer")
            properties = get_device_properties(device_index)
            device_name = _bounded_text(getattr(properties, "name", None)) or None
            major = getattr(properties, "major", None)
            minor = getattr(properties, "minor", None)
            if accelerator == "cuda" and isinstance(major, int) and isinstance(minor, int):
                compute_capability = f"{major}.{minor}"
            total_memory = getattr(properties, "total_memory", None)
            if isinstance(total_memory, int) and total_memory >= 0:
                total_vram_mb = total_memory // (1024 * 1024)
        except Exception:
            warnings.append("device_properties_unavailable")
    else:
        mps = getattr(getattr(torch, "backends", None), "mps", None)
        mps_is_available = getattr(mps, "is_available", None)
        try:
            if callable(mps_is_available) and bool(mps_is_available()):
                accelerator = "mps"
        except Exception:
            warnings.append("accelerator_probe_failed")

    return (
        {
            "accelerator": accelerator,
            "cuda_runtime_version": cuda_version,
            "rocm_runtime_version": rocm_version,
            "device_name": device_name,
            "compute_capability": compute_capability,
            "total_vram_mb": total_vram_mb,
        },
        warnings,
    )


def collect_torch_compile_diagnostics(
    *,
    load_torch: Callable[[], Any] = _torch_module,
    find_node_class: Callable[[str], Any] = _find_loaded_node_class,
    python_version: Callable[[], str] = platform.python_version,
) -> dict[str, object]:
    """Return bounded facts only; this never compiles, benchmarks, or persists."""

    reason_codes: list[str] = []
    warnings: list[str] = ["recommendation_policy_pending"]
    try:
        torch = load_torch()
    except Exception:
        torch = None
        reason_codes.append("torch_unavailable")

    if torch is None:
        accelerator = {
            "accelerator": "unknown",
            "cuda_runtime_version": None,
            "rocm_runtime_version": None,
            "device_name": None,
            "compute_capability": None,
            "total_vram_mb": None,
        }
        torch_version = None
        torch_compile_available = False
    else:
        accelerator, accelerator_warnings = _accelerator_environment(torch)
        warnings.extend(accelerator_warnings)
        torch_version = _bounded_text(getattr(torch, "__version__", None)) or None
        torch_compile_available = callable(getattr(torch, "compile", None))
        if not torch_compile_available:
            reason_codes.append("torch_compile_unavailable")

    if accelerator["accelerator"] != "cuda":
        reason_codes.append("cuda_unavailable")

    kj = _kj_contract(find_node_class)
    if not kj["available"]:
        reason_codes.append("kj_torch_compile_missing")
    elif kj["inspection_error"]:
        reason_codes.append("kj_input_contract_unreadable")
    else:
        if kj["missing_inputs"] or kj["unexpected_required_inputs"]:
            reason_codes.append("kj_input_contract_drift")
        if not kj["signature_compatible"]:
            reason_codes.append("kj_patch_signature_drift")

    supported = bool(
        torch is not None
        and torch_compile_available
        and accelerator["accelerator"] == "cuda"
        and kj["compatible"]
    )
    if supported:
        reason_codes.append("diagnostics_ready")

    return {
        "schema_version": AIO_TORCH_COMPILE_DIAGNOSTICS_SCHEMA_VERSION,
        "policy_version": AIO_TORCH_COMPILE_DIAGNOSTICS_POLICY_VERSION,
        "supported": supported,
        "profile": "diagnostics_only" if supported else "unsupported",
        "values": {},
        "environment": {
            "python_version": _bounded_text(python_version(), fallback="unknown"),
            "torch_version": torch_version,
            **accelerator,
            "kj_node_available": kj["available"],
            "kj_contract_compatible": kj["compatible"],
            "supported_inputs": kj["supported_inputs"],
            "input_options": kj["input_options"],
        },
        "reason_codes": reason_codes,
        "warnings": list(dict.fromkeys(warnings)),
    }


__all__ = [
    "AIO_TORCH_COMPILE_DIAGNOSTICS_POLICY_VERSION",
    "AIO_TORCH_COMPILE_DIAGNOSTICS_SCHEMA_VERSION",
    "TORCH_COMPILE_NODE_ID",
    "collect_torch_compile_diagnostics",
]
