from __future__ import annotations

import json
import uuid
from typing import Any, Mapping


REQUEST_ID_HEADER = "X-Request-ID"


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


def create_request_id() -> str:
    """Create one server-owned correlation ID for an API request."""

    return str(uuid.uuid4())


def attach_request_id_header(response, request_id: str):
    """Attach correlation metadata without requiring a global middleware."""

    headers = getattr(response, "headers", None)
    if headers is not None:
        headers[REQUEST_ID_HEADER] = request_id
    return response


def correlate_response(response, request_id: str):
    """Correlate JSON errors while preserving non-JSON response bodies."""

    attach_request_id_header(response, request_id)
    if (
        getattr(response, "status", 0) < 400
        or getattr(response, "content_type", "") != "application/json"
    ):
        return response

    try:
        payload = json.loads(response.text)
    except (AttributeError, json.JSONDecodeError, TypeError, UnicodeDecodeError):
        return response
    if not isinstance(payload, dict):
        return response

    payload["request_id"] = request_id
    response.text = json.dumps(payload, ensure_ascii=False)
    return response


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
