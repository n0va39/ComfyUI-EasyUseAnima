from __future__ import annotations

import json
from typing import Any, Mapping


class ApiContractError(ValueError):
    """A public request-contract error with a stable HTTP mapping."""

    def __init__(
        self,
        status: int,
        code: str,
        message: str,
        *,
        details: Mapping[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.status = status
        self.code = code
        self.message = message
        self.details = dict(details) if details is not None else None


def error_payload(
    code: str,
    message: str,
    *,
    details: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Keep the legacy status/message shape while adding a stable code."""

    payload: dict[str, Any] = {
        "status": "error",
        "code": code,
        "message": message,
    }
    if details is not None:
        payload["details"] = dict(details)
    return payload


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


def _field_error(field: str, expectation: str) -> ApiContractError:
    return ApiContractError(
        422,
        "invalid_request",
        f"{field} must be {expectation}.",
        details={"field": field},
    )


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
    default: int,
    minimum: int | None = None,
    maximum: int | None = None,
) -> int:
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
