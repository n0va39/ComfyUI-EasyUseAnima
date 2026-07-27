"""Compatibility exports for the canonical API contract package."""

from __future__ import annotations

try:
    from .easyuse_anima.api.errors import ApiContractError
    from .easyuse_anima.api.requests import (
        json_boolean,
        json_integer,
        json_object,
        json_string,
        json_uuid_string,
        parse_json_object,
    )
    from .easyuse_anima.api.responses import (
        REQUEST_ID_HEADER,
        attach_request_id_header,
        correlate_response,
        create_request_id,
        error_payload,
    )
except ImportError:
    from easyuse_anima.api.errors import ApiContractError
    from easyuse_anima.api.requests import (
        json_boolean,
        json_integer,
        json_object,
        json_string,
        json_uuid_string,
        parse_json_object,
    )
    from easyuse_anima.api.responses import (
        REQUEST_ID_HEADER,
        attach_request_id_header,
        correlate_response,
        create_request_id,
        error_payload,
    )


__all__ = [
    "REQUEST_ID_HEADER",
    "ApiContractError",
    "error_payload",
    "create_request_id",
    "attach_request_id_header",
    "correlate_response",
    "parse_json_object",
    "json_object",
    "json_string",
    "json_boolean",
    "json_integer",
    "json_uuid_string",
]
