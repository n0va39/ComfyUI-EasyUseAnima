from __future__ import annotations

import json
import uuid
from typing import Any, Mapping


REQUEST_ID_HEADER = "X-Request-ID"


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


__all__ = (
    "REQUEST_ID_HEADER",
    "error_payload",
    "create_request_id",
    "attach_request_id_header",
    "correlate_response",
)
