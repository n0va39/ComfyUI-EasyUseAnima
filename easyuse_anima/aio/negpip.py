"""Public ComfyUI-ppm NegPip adapter for AiO generation."""

from __future__ import annotations

import hashlib
import inspect
import re
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any

from ..infrastructure.comfy.invocation import _node_output_tuple
from ..infrastructure.comfy.wiring import resolve_comfy_host_helper
from .generation_values import ObjectState, expect_object, expect_str, required

NEGPIP_NODE_ID = "CLIPNegPip"
NEGPIP_NODE_PACK = "ComfyUI-ppm"
NEGPIP_REPOSITORY = "https://github.com/pamparamm/ComfyUI-ppm"
NEGPIP_CONTRACT_REVISION = 1
NEGPIP_TURBO_POLICY_REVISION = 1
NEGPIP_TURBO_NEGATIVE_SCALE = -1.0

NEGPIP_MODE_OFF = "off"
NEGPIP_MODE_ON = "on"
NEGPIP_MODE_TURBO = "turbo"
NEGPIP_MODES = (
    NEGPIP_MODE_OFF,
    NEGPIP_MODE_ON,
    NEGPIP_MODE_TURBO,
)
NEGPIP_TURBO_MALFORMED_REASON = "negpip_turbo_prompt_malformed"

_EXPECTED_INPUTS = {
    "model": "MODEL",
    "clip": "CLIP",
}
_EXPECTED_OUTPUTS = ("MODEL", "CLIP")
_OPEN_TO_CLOSE = {"(": ")", "{": "}", "[": "]"}
_CLOSE_TO_OPEN = {value: key for key, value in _OPEN_TO_CLOSE.items()}
_NUMERIC_WEIGHT_RE = re.compile(
    r"(?P<prefix>:\s*)"
    r"(?P<sign>[+-]?)"
    r"(?P<number>(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?)"
    r"(?P<suffix>\s*)(?=\))"
)


@dataclass(frozen=True, slots=True)
class AIOGenerationNegPipConfig:
    state: ObjectState
    mode: str

    @classmethod
    def from_value(
        cls,
        value: object,
        key: str = "negpip",
    ) -> AIOGenerationNegPipConfig:
        source = expect_object(value, key)
        return cls(
            state=ObjectState.from_source(source, ("mode",)),
            mode=expect_str(required(source, "mode"), f"{key}.mode"),
        )

    @property
    def is_turbo(self) -> bool:
        return self.mode == NEGPIP_MODE_TURBO

    def effective_cfg(self, stored: object) -> object:
        return 1.0 if self.is_turbo else stored

    def to_dict(self) -> dict[str, object]:
        return self.state.compose({"mode": self.mode})


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


def _is_escaped(text: str, index: int) -> bool:
    slash_count = 0
    cursor = index - 1
    while cursor >= 0 and text[cursor] == "\\":
        slash_count += 1
        cursor -= 1
    return slash_count % 2 == 1


def _line_ending(line: str) -> str:
    if line.endswith("\r\n"):
        return "\r\n"
    if line.endswith("\n"):
        return "\n"
    if line.endswith("\r"):
        return "\r"
    return ""


def _turbo_prompt_error() -> RuntimeError:
    return RuntimeError(
        "[EasyUseAnima] AiO NegPip Turbo prompt is malformed: "
        f"{NEGPIP_TURBO_MALFORMED_REASON}. Fix mismatched prompt delimiters "
        "or select Off/On."
    )


def _strip_top_level_comments_and_validate(text: str) -> str:
    stack: list[str] = []
    output: list[str] = []
    for line in text.splitlines(keepends=True):
        if not stack and line.lstrip(" \t").startswith("#"):
            output.append(_line_ending(line))
            continue

        for index, char in enumerate(line):
            if _is_escaped(line, index):
                continue
            if char in _OPEN_TO_CLOSE:
                stack.append(char)
            elif char in _CLOSE_TO_OPEN:
                if not stack or stack[-1] != _CLOSE_TO_OPEN[char]:
                    raise _turbo_prompt_error()
                stack.pop()
        output.append(line)

    if stack:
        raise _turbo_prompt_error()
    return "".join(output)


def _split_top_level_prompt_items(text: str) -> list[str]:
    stack: list[str] = []
    items: list[str] = []
    start = 0
    for index, char in enumerate(text):
        if _is_escaped(text, index):
            continue
        if char in _OPEN_TO_CLOSE:
            stack.append(char)
        elif char in _CLOSE_TO_OPEN:
            stack.pop()
        elif not stack and char in ",\r\n":
            item = text[start:index].strip()
            if item:
                items.append(item)
            start = index + 1
    final_item = text[start:].strip()
    if final_item:
        items.append(final_item)
    return items


def _toggle_numeric_weight(match: re.Match[str]) -> str:
    sign = "" if match.group("sign") == "-" else "-"
    return (
        f"{match.group('prefix')}{sign}{match.group('number')}"
        f"{match.group('suffix')}"
    )


def _derive_aio_negpip_turbo_negative_contribution(
    negative_prompt: str,
) -> str:
    cleaned = _strip_top_level_comments_and_validate(str(negative_prompt or ""))
    items = _split_top_level_prompt_items(cleaned)
    if not items:
        return ""
    prompt = ", ".join(items)
    prompt = _NUMERIC_WEIGHT_RE.sub(_toggle_numeric_weight, prompt)
    return f"({prompt}:-1)"


def _aio_negpip_execution_prompts(
    positive_prompt: str,
    negative_prompt: str,
    mode: str,
) -> tuple[str, str, str]:
    positive_source = str(positive_prompt or "")
    negative_source = str(negative_prompt or "")
    if mode in (NEGPIP_MODE_OFF, NEGPIP_MODE_ON):
        return positive_source, negative_source, ""
    if mode != NEGPIP_MODE_TURBO:
        raise RuntimeError(
            f"[EasyUseAnima] Unsupported normalized AiO NegPip mode: {mode!r}."
        )
    derived = _derive_aio_negpip_turbo_negative_contribution(negative_source)
    positive_execution = ", ".join(
        part for part in (positive_source, derived) if part
    )
    return positive_execution, "", derived


def _aio_negpip_turbo_fingerprint(negative_prompt: str) -> str:
    derived = _derive_aio_negpip_turbo_negative_contribution(negative_prompt)
    return hashlib.sha256(derived.encode("utf-8")).hexdigest()


def _aio_negpip_mode(value: object) -> str:
    if value is None:
        return NEGPIP_MODE_OFF
    if not isinstance(value, Mapping):
        raise RuntimeError(
            "[EasyUseAnima] AiO NegPip settings are malformed; "
            "disable NegPip or select a supported mode."
        )
    mode = value.get("mode")
    if mode not in NEGPIP_MODES:
        raise RuntimeError(
            f"[EasyUseAnima] Unsupported AiO NegPip mode: {mode!r}. "
            "Select 'off', 'on', or 'turbo'."
        )
    return str(mode)


def _aio_negpip_cache_signature(
    value: object,
    *,
    negative_prompt: str | None = None,
) -> dict[str, object] | None:
    mode = _aio_negpip_mode(value)
    if mode == NEGPIP_MODE_OFF:
        return None
    signature: dict[str, object] = {
        "mode": mode,
        "contract_revision": NEGPIP_CONTRACT_REVISION,
    }
    if mode == NEGPIP_MODE_TURBO:
        if negative_prompt is None:
            raise RuntimeError(
                "[EasyUseAnima] AiO NegPip Turbo cache identity requires "
                "the execution negative prompt."
            )
        signature.update(
            {
                "policy_revision": NEGPIP_TURBO_POLICY_REVISION,
                "negative_scale": NEGPIP_TURBO_NEGATIVE_SCALE,
                "derived_prompt_fingerprint": (
                    _aio_negpip_turbo_fingerprint(negative_prompt)
                ),
                "effective_first_pass_cfg": 1.0,
            }
        )
    return signature


def _aio_negpip_metadata(
    mode: str,
    *,
    negative_prompt: str | None = None,
) -> dict[str, object] | None:
    if mode == NEGPIP_MODE_OFF:
        return None
    if mode not in (NEGPIP_MODE_ON, NEGPIP_MODE_TURBO):
        raise RuntimeError(
            f"[EasyUseAnima] Unsupported normalized AiO NegPip mode: {mode!r}."
        )
    metadata: dict[str, object] = {
        "mode": mode,
        "contract_revision": NEGPIP_CONTRACT_REVISION,
    }
    if mode == NEGPIP_MODE_TURBO:
        if negative_prompt is None:
            raise RuntimeError(
                "[EasyUseAnima] AiO NegPip Turbo metadata requires the "
                "execution negative prompt."
            )
        metadata.update(
            {
                "policy_revision": NEGPIP_TURBO_POLICY_REVISION,
                "negative_scale": NEGPIP_TURBO_NEGATIVE_SCALE,
                "derived_prompt_fingerprint": (
                    _aio_negpip_turbo_fingerprint(negative_prompt)
                ),
                "effective_cfg": {
                    "first_pass": 1.0,
                    "highres": 1.0,
                    "detailer": 1.0,
                    "upscale_usdu": 1.0,
                },
            }
        )
    return metadata


def apply_aio_negpip(model: Any, clip: Any, mode: str) -> tuple[Any, Any]:
    """Apply the public NegPip adapter once for normalized On or Turbo mode."""

    if mode == NEGPIP_MODE_OFF:
        return model, clip
    if mode not in (NEGPIP_MODE_ON, NEGPIP_MODE_TURBO):
        raise RuntimeError(
            f"[EasyUseAnima] Unsupported normalized AiO NegPip mode: {mode!r}."
        )
    node_class = _require_custom_node_class(
        NEGPIP_NODE_ID,
        NEGPIP_NODE_PACK,
        f"Required for AiO NegPip {mode} mode. Repository: {NEGPIP_REPOSITORY}",
    )
    return invoke_negpip_node(node_class, model, clip)


__all__ = ()
