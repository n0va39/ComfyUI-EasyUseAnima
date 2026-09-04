"""Resource budgets for workflow and image metadata serialization."""

from __future__ import annotations

import json
import logging
import math
import re
from collections.abc import Mapping
from dataclasses import dataclass

logger = logging.getLogger("ComfyUI-EasyUseAnima")

_MAX_JSON_DEPTH = 64
_MAX_JSON_ITEMS = 100_000
_MAX_JSON_STRING_BYTES = 1 * 1024 * 1024
_MAX_EXTRA_PNGINFO_KEYS = 128
_MAX_EXTRA_KEY_BYTES = 256

_MAX_PARAMETERS_BYTES = 512 * 1024
_MAX_PROMPT_JSON_BYTES = 2 * 1024 * 1024
_MAX_WORKFLOW_JSON_BYTES = 4 * 1024 * 1024
_MAX_EXTRA_PNGINFO_JSON_BYTES = 6 * 1024 * 1024
_MAX_EMBEDDED_METADATA_BYTES = 8 * 1024 * 1024
_MAX_SAVE_METADATA_BYTES = 64 * 1024 * 1024

_TEXT_CHUNK_CHARACTERS = 64 * 1024
_CONTROL_RE = re.compile(r"[\x00-\x1f\x7f]")
_RESERVED_EXTRA_PNGINFO_KEYS = frozenset({"parameters", "prompt", "workflow"})


class MetadataLimitError(RuntimeError):
    """A workflow-controlled metadata payload exceeded its explicit budget."""


def _utf8_size(value: str, *, limit: int, label: str) -> int:
    total = 0
    for offset in range(0, len(value), _TEXT_CHUNK_CHARACTERS):
        total += len(
            value[offset : offset + _TEXT_CHUNK_CHARACTERS].encode("utf-8")
        )
        if total > limit:
            raise MetadataLimitError(
                f"[EasyUseAnima] AiO {label} exceeds the {limit}-byte metadata limit."
            )
    return total


def _scalar_size(value: object) -> int:
    if value is None:
        return 4
    if isinstance(value, bool):
        return 5
    if isinstance(value, int):
        if value == 0:
            return 1
        return max(1, math.ceil(abs(value).bit_length() * math.log10(2))) + int(
            value < 0
        )
    if isinstance(value, float):
        return 32
    return 64


def _validate_json_structure(
    value: object,
    *,
    label: str,
    byte_limit: int,
) -> None:
    items_seen = 0
    estimated_bytes = 0
    active_containers: set[int] = set()
    stack: list[tuple[object, int, bool]] = [(value, 0, False)]

    def add_bytes(amount: int) -> None:
        nonlocal estimated_bytes
        estimated_bytes += amount
        if estimated_bytes > byte_limit:
            raise MetadataLimitError(
                f"[EasyUseAnima] AiO {label} exceeds the {byte_limit}-byte metadata limit."
            )

    while stack:
        current, depth, exiting = stack.pop()
        if exiting:
            active_containers.remove(id(current))
            continue

        items_seen += 1
        if items_seen > _MAX_JSON_ITEMS:
            raise MetadataLimitError(
                f"[EasyUseAnima] AiO {label} exceeds the {_MAX_JSON_ITEMS}-item metadata limit."
            )
        if depth > _MAX_JSON_DEPTH:
            raise MetadataLimitError(
                f"[EasyUseAnima] AiO {label} exceeds the {_MAX_JSON_DEPTH}-level metadata limit."
            )
        if isinstance(current, str):
            add_bytes(
                _utf8_size(
                    current,
                    limit=_MAX_JSON_STRING_BYTES,
                    label=f"{label} string",
                )
                + 2
            )
            continue

        if isinstance(current, Mapping):
            identity = id(current)
            if identity in active_containers:
                raise ValueError("Circular reference detected")
            if items_seen + len(current) * 2 > _MAX_JSON_ITEMS:
                raise MetadataLimitError(
                    f"[EasyUseAnima] AiO {label} exceeds the {_MAX_JSON_ITEMS}-item metadata limit."
                )
            active_containers.add(identity)
            stack.append((current, depth, True))
            add_bytes(2 + max(0, len(current) - 1))
            for key, child in current.items():
                items_seen += 1
                key_text = key if isinstance(key, str) else str(key)
                add_bytes(
                    _utf8_size(
                        key_text,
                        limit=_MAX_JSON_STRING_BYTES,
                        label=f"{label} key",
                    )
                    + 3
                )
                stack.append((child, depth + 1, False))
            continue

        if isinstance(current, (list, tuple)):
            identity = id(current)
            if identity in active_containers:
                raise ValueError("Circular reference detected")
            if items_seen + len(current) > _MAX_JSON_ITEMS:
                raise MetadataLimitError(
                    f"[EasyUseAnima] AiO {label} exceeds the {_MAX_JSON_ITEMS}-item metadata limit."
                )
            active_containers.add(identity)
            stack.append((current, depth, True))
            add_bytes(2 + max(0, len(current) - 1))
            for child in current:
                stack.append((child, depth + 1, False))
            continue

        add_bytes(_scalar_size(current))


def _json_dumps_limited(
    value: object,
    *,
    label: str,
    byte_limit: int,
    ascii_only: bool,
    pretty: bool = False,
) -> tuple[str, int]:
    _validate_json_structure(value, label=label, byte_limit=byte_limit)
    if pretty:
        encoder = json.JSONEncoder(
            allow_nan=False,
            ensure_ascii=ascii_only,
            indent=2,
        )
    else:
        encoder = json.JSONEncoder(
            allow_nan=False,
            ensure_ascii=ascii_only,
            separators=(",", ":"),
        )
    parts: list[str] = []
    total = 0
    for part in encoder.iterencode(value):
        part_size = _utf8_size(
            part,
            limit=byte_limit,
            label=label,
        )
        if total > byte_limit - part_size:
            raise MetadataLimitError(
                f"[EasyUseAnima] AiO {label} exceeds the {byte_limit}-byte metadata limit."
            )
        total += part_size
        parts.append(part)
    return "".join(parts), total


def _metadata_text_size(value: str, *, label: str, limit: int) -> int:
    return _utf8_size(str(value or ""), limit=limit, label=label)


def _validate_parameter_sources(*values: object) -> None:
    total = 0
    for value in values:
        size = _utf8_size(
            str(value or ""),
            limit=_MAX_PARAMETERS_BYTES,
            label="A1111 parameters",
        )
        if total > _MAX_PARAMETERS_BYTES - size:
            raise MetadataLimitError(
                "[EasyUseAnima] AiO A1111 parameters exceed the "
                f"{_MAX_PARAMETERS_BYTES}-byte metadata limit."
            )
        total += size


def _extra_pnginfo_key(value: object) -> str:
    text = str(value)
    if not text or _CONTROL_RE.search(text):
        raise MetadataLimitError(
            "[EasyUseAnima] AiO extra_pnginfo key is empty or contains control characters."
        )
    _utf8_size(text, limit=_MAX_EXTRA_KEY_BYTES, label="extra_pnginfo key")
    return text


def _validate_extra_pnginfo_count(value: Mapping[str, object]) -> None:
    if len(value) > _MAX_EXTRA_PNGINFO_KEYS:
        raise MetadataLimitError(
            f"[EasyUseAnima] AiO extra_pnginfo exceeds the {_MAX_EXTRA_PNGINFO_KEYS}-key metadata limit."
        )


@dataclass(slots=True)
class _PreparedMetadataPayload:
    workflow: object | None
    prompt_json: str | None
    extra_json: list[tuple[str, str]]
    workflow_json: str | None
    workflow_json_size: int
    embedded_size: int

    def ensure_workflow_sidecar(self) -> None:
        if self.workflow is None or self.workflow_json is not None:
            return
        self.workflow_json, self.workflow_json_size = _json_dumps_limited(
            self.workflow,
            label="workflow JSON sidecar",
            byte_limit=_MAX_WORKFLOW_JSON_BYTES,
            ascii_only=False,
            pretty=True,
        )


def _prepare_metadata_payload(
    *,
    parameters: str,
    prompt: object | None,
    extra_pnginfo: Mapping[str, object] | None,
    embed_workflow: bool,
    save_workflow_as_json: bool,
) -> _PreparedMetadataPayload:
    parameters_size = _metadata_text_size(
        parameters,
        label="A1111 parameters",
        limit=_MAX_PARAMETERS_BYTES,
    )
    workflow = (
        extra_pnginfo.get("workflow")
        if isinstance(extra_pnginfo, Mapping)
        else None
    )
    workflow_compact: str | None = None
    workflow_compact_size = 0
    if workflow is not None and embed_workflow:
        workflow_compact, workflow_compact_size = _json_dumps_limited(
            workflow,
            label="workflow JSON",
            byte_limit=_MAX_WORKFLOW_JSON_BYTES,
            ascii_only=True,
        )

    prompt_json: str | None = None
    prompt_json_size = 0
    if embed_workflow and prompt is not None:
        prompt_json, prompt_json_size = _json_dumps_limited(
            prompt,
            label="prompt JSON",
            byte_limit=_MAX_PROMPT_JSON_BYTES,
            ascii_only=True,
        )

    extra_json: list[tuple[str, str]] = []
    extra_json_size = 0
    if embed_workflow:
        extra_values = extra_pnginfo or {}
        _validate_extra_pnginfo_count(extra_values)
        for key, value in extra_values.items():
            key_text = _extra_pnginfo_key(key)
            canonical_key = key_text.casefold()
            is_reserved = any(
                canonical_key == reserved or canonical_key.startswith(f"{reserved}:")
                for reserved in _RESERVED_EXTRA_PNGINFO_KEYS
            )
            if is_reserved and key_text != "workflow":
                logger.warning(
                    "[EasyUseAnima] Ignoring reserved extra_pnginfo key %r.",
                    key_text,
                )
                continue
            if key_text == "workflow" and workflow_compact is not None:
                value_json = workflow_compact
                value_size = workflow_compact_size
            else:
                value_json, value_size = _json_dumps_limited(
                    value,
                    label="extra_pnginfo value",
                    byte_limit=_MAX_EXTRA_PNGINFO_JSON_BYTES,
                    ascii_only=True,
                )
            key_size = _metadata_text_size(
                key_text,
                label="extra_pnginfo key",
                limit=_MAX_EXTRA_PNGINFO_JSON_BYTES,
            )
            if (
                extra_json_size
                > _MAX_EXTRA_PNGINFO_JSON_BYTES - key_size - value_size
            ):
                raise MetadataLimitError(
                    "[EasyUseAnima] AiO extra_pnginfo exceeds the "
                    f"{_MAX_EXTRA_PNGINFO_JSON_BYTES}-byte metadata limit."
                )
            extra_json_size += key_size + value_size
            extra_json.append((key_text, value_json))

    payload = _PreparedMetadataPayload(
        workflow=workflow,
        prompt_json=prompt_json,
        extra_json=extra_json,
        workflow_json=None,
        workflow_json_size=0,
        embedded_size=parameters_size + prompt_json_size + extra_json_size,
    )
    _validate_embedded_metadata_size(payload.embedded_size)
    if save_workflow_as_json:
        payload.ensure_workflow_sidecar()
    return payload


def _validate_embedded_metadata_size(size: int) -> None:
    if size > _MAX_EMBEDDED_METADATA_BYTES:
        raise MetadataLimitError(
            "[EasyUseAnima] AiO embedded image metadata exceeds the "
            f"{_MAX_EMBEDDED_METADATA_BYTES}-byte limit."
        )


def _validate_save_metadata_size(*, per_image: int, batch_count: int) -> None:
    if per_image * batch_count > _MAX_SAVE_METADATA_BYTES:
        raise MetadataLimitError(
            "[EasyUseAnima] AiO batch metadata exceeds the "
            f"{_MAX_SAVE_METADATA_BYTES}-byte per-save limit."
        )


def _sidecar_required_and_validate_batch(
    *,
    workflow_json: str | None,
    force_workflow_sidecar: bool,
    save_workflow_as_json: bool,
    embedded_size: int,
    sidecar_size: int,
    batch_count: int,
) -> bool:
    required = workflow_json is not None and (
        save_workflow_as_json or force_workflow_sidecar
    )
    _validate_save_metadata_size(
        per_image=embedded_size + (sidecar_size if required else 0),
        batch_count=batch_count,
    )
    return required


__all__ = ()
