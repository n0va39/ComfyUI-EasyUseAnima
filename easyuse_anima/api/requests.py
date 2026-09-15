from __future__ import annotations

import base64
import binascii
import hashlib
import hmac
import ipaddress
import json
import uuid
from collections.abc import Mapping
from typing import Any
from urllib.parse import urlsplit

from .errors import ApiContractError, _field_error

_JSON_CONTENT_TYPE = "application/json"


def api_token_digest(token: str) -> bytes | None:
    """Snapshot an operator secret, never a web-writable setting or user file."""
    return hashlib.sha256(token.encode("utf-8")).digest() if token else None


def _is_loopback(value: str) -> bool:
    try:
        address = ipaddress.ip_address(value)
        if isinstance(address, ipaddress.IPv6Address) and address.ipv4_mapped:
            address = address.ipv4_mapped
        return address.is_loopback
    except ValueError:
        return False


def validate_api_access(request, expected_digest: bytes | None) -> None:
    """Local trust requires the socket peer AND a literal local Host.

    A configured secret always requires HTTP Basic authentication, even for a
    loopback proxy. Forwarded headers and Comfy user selectors grant no access.
    """
    if expected_digest is not None:
        authorization = _request_header(request, "Authorization")
        scheme, _, credentials = authorization.partition(" ")
        try:
            decoded = base64.b64decode(credentials, validate=True).decode("utf-8")
        except (binascii.Error, UnicodeDecodeError, ValueError):
            decoded = ""
        username, _, token = decoded.partition(":")
        supplied_digest = api_token_digest(token)
        if (
            scheme.casefold() == "basic"
            and username == "easyuse"
            and supplied_digest is not None
            and hmac.compare_digest(supplied_digest, expected_digest)
        ):
            return
        raise ApiContractError(
            401, "api_authentication_required",
            "EasyUse API authentication is required. Use the easyuse username and the server's API token.",
        )

    transport = getattr(request, "transport", None)
    peer = transport.get_extra_info("peername") if transport is not None else None
    authority = _host_authority(_request_header(request, "Host"), "http://localhost")
    if (
        isinstance(peer, (tuple, list)) and peer and _is_loopback(str(peer[0]))
        and authority is not None
        and (authority[0] == "localhost" or _is_loopback(authority[0]))
        and not any(_request_header(request, header) for header in (
            "Forwarded", "X-Forwarded-For", "X-Forwarded-Host", "X-Forwarded-Proto",
        ))
    ):
        return
    raise ApiContractError(
        403, "local_api_access_required",
        "Use a local ComfyUI address, or configure EASYUSE_ANIMA_API_TOKEN for remote API access.",
    )


def _request_header(request, name: str) -> str:
    headers = getattr(request, "headers", None)
    if headers is None:
        return ""
    try:
        value = headers.get(name, "")
    except (AttributeError, TypeError):
        return ""
    return str(value or "").strip()


def _origin_authority(value: str) -> tuple[str, int | None] | None:
    try:
        parsed = urlsplit(value)
        port = parsed.port
    except (TypeError, ValueError):
        return None
    if (
        parsed.scheme.casefold() not in {"http", "https"}
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or parsed.path not in {"", "/"}
        or parsed.query
        or parsed.fragment
    ):
        return None
    if port is None:
        port = 443 if parsed.scheme.casefold() == "https" else 80
    return parsed.hostname.rstrip(".").casefold(), port


def _host_authority(value: str, origin: str) -> tuple[str, int | None] | None:
    try:
        parsed = urlsplit(f"//{value}")
        port = parsed.port
    except (TypeError, ValueError):
        return None
    if (
        not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or parsed.path
        or parsed.query
        or parsed.fragment
    ):
        return None
    if port is None:
        try:
            origin_scheme = urlsplit(origin).scheme.casefold()
        except (TypeError, ValueError):
            return None
        port = 443 if origin_scheme == "https" else 80
    return parsed.hostname.rstrip(".").casefold(), port


def validate_same_origin_json_request(request) -> None:
    """Reject browser-reachable POSTs before parsing or side effects."""

    fetch_site = _request_header(request, "Sec-Fetch-Site").casefold()
    if fetch_site and fetch_site != "same-origin":
        raise ApiContractError(
            403,
            "cross_origin_request",
            "Request must come from the current ComfyUI origin.",
        )

    origin = _request_header(request, "Origin")
    host = _request_header(request, "Host")
    origin_authority = _origin_authority(origin)
    host_authority = _host_authority(host, origin)
    if (
        origin_authority is None
        or host_authority is None
        or origin_authority != host_authority
    ):
        raise ApiContractError(
            403,
            "cross_origin_request",
            "Request must come from the current ComfyUI origin.",
        )

    content_type = _request_header(request, "Content-Type")
    media_type = content_type.partition(";")[0].strip().casefold()
    if media_type != _JSON_CONTENT_TYPE:
        raise ApiContractError(
            415,
            "json_content_type_required",
            "Request Content-Type must be application/json.",
        )


async def parse_json_object(request) -> dict[str, Any]:
    validate_same_origin_json_request(request)
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
