from __future__ import annotations

import asyncio
import json
import uuid
from functools import wraps
from typing import Any, Mapping, cast


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


def build_error_response(*, json_response, build_error_payload):
    """Build the root-compatible JSON error response boundary."""

    def _error_response(
        status: int,
        code: str,
        message: str,
        *,
        details: dict | None = None,
    ):
        return json_response(
            build_error_payload(code, message, details=details),
            status=status,
        )

    return _error_response


def build_contract_error_response(*, error_response):
    """Build the root-compatible request contract error mapper."""

    def _contract_error_response(exc):
        return error_response(
            exc.status,
            exc.code,
            exc.message,
            details=exc.details,
        )

    return _contract_error_response


def build_profile_error_response(
    *,
    max_aio_profiles,
    is_profile_mutation_error,
    is_file_exists_error,
    is_file_not_found_error,
    is_invalid_profile_data_error,
    is_value_error,
    get_safe_validation_messages,
    error_response,
):
    """Build the shared profile error mapper without profile-domain imports."""

    safe_validation_messages = frozenset(
        {
            "Profile name is required",
            "Profile name is reserved on Windows",
            "Invalid profile path",
            "System profile names are reserved",
            "Profile settings must be an object",
            "Profile settings are too large",
            f"A maximum of {max_aio_profiles} profiles can be saved",
        }
    )

    def _profile_error_response(exc: Exception):
        if is_profile_mutation_error(exc):
            mutation_error = cast(Any, exc)
            return error_response(
                mutation_error.status,
                mutation_error.code,
                mutation_error.message,
                details=mutation_error.details,
            )
        if is_file_exists_error(exc):
            return error_response(
                409,
                "profile_exists",
                "Profile already exists",
            )
        if is_file_not_found_error(exc):
            return error_response(
                404,
                "profile_not_found",
                "Profile not found",
            )
        if is_invalid_profile_data_error(exc):
            return error_response(
                422,
                "invalid_profile_data",
                "Profile data is invalid",
            )
        if is_value_error(exc):
            message = str(exc)
            if message not in get_safe_validation_messages():
                message = "Request validation failed"
            return error_response(422, "invalid_request", message)
        raise exc

    return safe_validation_messages, _profile_error_response


def build_request_correlator(
    *,
    create_id,
    get_http_exception_type,
    attach_id_header,
    correlate,
    get_logger,
    error_response,
):
    """Build the root-compatible cancellation and correlation boundary."""

    def _request_correlated(handler):
        @wraps(handler)
        async def correlated_handler(request):
            request_id = create_id()
            try:
                response = await handler(request)
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                if isinstance(exc, get_http_exception_type()):
                    attach_id_header(exc, request_id)
                    raise
                get_logger().exception(
                    "Unhandled EasyUseAnima API error (request_id=%s)",
                    request_id,
                )
                response = error_response(
                    500,
                    "internal_error",
                    "An unexpected server error occurred.",
                )
            return correlate(response, request_id)

        setattr(correlated_handler, "_easyuse_anima_request_correlation", True)
        return correlated_handler

    return _request_correlated


__all__ = (
    "REQUEST_ID_HEADER",
    "error_payload",
    "create_request_id",
    "attach_request_id_header",
    "correlate_response",
)
