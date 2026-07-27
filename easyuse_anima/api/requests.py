from __future__ import annotations

import json
import uuid
from typing import Any, Mapping

from .errors import ApiContractError, _field_error


async def parse_json_object(request) -> dict[str, Any]:
    try:
        data = await request.json()
    except (json.JSONDecodeError, UnicodeDecodeError, ValueError) as exc:
        raise ApiContractError(
            400,
            "malformed_json",
            "Request body must contain valid JSON.",
        ) from exc
    if not isinstance(data, dict):
        raise ApiContractError(
            400,
            "json_object_required",
            "Request body must be a JSON object.",
        )
    return data


def json_object(
    data: Mapping[str, Any],
    field: str,
    *,
    required: bool = True,
    default: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    if field not in data:
        if required:
            raise _field_error(field, "a JSON object")
        return dict(default or {})
    value = data[field]
    if not isinstance(value, dict):
        raise _field_error(field, "a JSON object")
    return value


def json_string(
    data: Mapping[str, Any],
    field: str,
    *,
    required: bool = True,
    default: str = "",
    allow_empty: bool = True,
) -> str:
    if field not in data:
        if required:
            raise _field_error(field, "a JSON string")
        return default
    value = data[field]
    if not isinstance(value, str):
        raise _field_error(field, "a JSON string")
    if not allow_empty and not value.strip():
        raise _field_error(field, "a non-empty JSON string")
    return value


def json_boolean(
    data: Mapping[str, Any],
    field: str,
    *,
    default: bool = False,
) -> bool:
    if field not in data:
        return default
    value = data[field]
    if type(value) is not bool:
        raise _field_error(field, "a JSON boolean")
    return value


def json_integer(
    data: Mapping[str, Any],
    field: str,
    *,
    default: int | None,
    minimum: int | None = None,
    maximum: int | None = None,
) -> int | None:
    if field not in data:
        return default
    value = data[field]
    if type(value) is not int:
        raise _field_error(field, "a JSON integer")
    if minimum is not None and value < minimum:
        raise _field_error(field, f"an integer greater than or equal to {minimum}")
    if maximum is not None and value > maximum:
        raise _field_error(field, f"an integer less than or equal to {maximum}")
    return value


def json_uuid_string(
    data: Mapping[str, Any],
    field: str,
    *,
    required: bool = True,
    default: str | None = None,
) -> str | None:
    if field not in data:
        if required:
            raise _field_error(field, "a UUID string")
        return default
    value = data[field]
    if not isinstance(value, str):
        raise _field_error(field, "a UUID string")
    try:
        return str(uuid.UUID(value))
    except (AttributeError, ValueError) as exc:
        raise _field_error(field, "a UUID string") from exc


__all__ = (
    "parse_json_object",
    "json_object",
    "json_string",
    "json_boolean",
    "json_integer",
    "json_uuid_string",
)
