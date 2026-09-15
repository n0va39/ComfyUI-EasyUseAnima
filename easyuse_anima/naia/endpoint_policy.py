"""Pure parsing for operator-approved, IP-pinned NAIA destinations."""

from __future__ import annotations

import ipaddress
import json
import re

# (settings hostname, exact port, numeric connection address).
DEFAULT_NAIA_ENDPOINTS = (
    ("127.0.0.1", 7243, "127.0.0.1"),
    ("localhost", 7243, "127.0.0.1"),
    ("::1", 7243, "::1"),
)
_HOST_LABEL = re.compile(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?", re.ASCII)
_POLICY_ERROR = "Invalid operator NAIA endpoint policy."


def normalize_naia_host(value: object) -> str:
    host = str(value or "").strip().lower()
    if host.startswith("[") and host.endswith("]"):
        host = host[1:-1]
    # Scoped IPv6 and URL components must never reach Requests/urllib3.
    if not host or any(token in host for token in ("%", "/", "\\", "?", "#", "@")):
        raise ValueError(_POLICY_ERROR)
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        host = host.rstrip(".")
        if len(host) > 253 or not all(_HOST_LABEL.fullmatch(label) for label in host.split(".")):
            raise ValueError(_POLICY_ERROR) from None
        return host
    if isinstance(address, ipaddress.IPv6Address) and address.ipv4_mapped:
        address = address.ipv4_mapped
    return str(address)


def _connection_address(value: object) -> str:
    try:
        address = ipaddress.ip_address(normalize_naia_host(value))
    except ValueError:
        raise ValueError(_POLICY_ERROR) from None
    if (
        address.is_link_local or address.is_multicast or address.is_unspecified
        or (address.is_reserved and not address.is_loopback)
    ):
        raise ValueError(_POLICY_ERROR)
    return str(address)


def parse_naia_endpoint_policy(raw: str) -> tuple[tuple[str, int, str], ...]:
    """Read non-secret startup configuration, never ordinary persisted settings.

    Entries add exact endpoints to the standard loopback defaults. A hostname
    requires an explicit numeric address; requests never resolve it through DNS.
    """
    if not raw.strip():
        return DEFAULT_NAIA_ENDPOINTS
    try:
        entries = json.loads(raw)
    except (TypeError, ValueError):
        raise ValueError(_POLICY_ERROR) from None
    if not isinstance(entries, list):
        raise ValueError(_POLICY_ERROR)
    endpoints = {(host, port): address for host, port, address in DEFAULT_NAIA_ENDPOINTS}
    for entry in entries:
        if not isinstance(entry, dict) or set(entry) - {"host", "port", "address"}:
            raise ValueError(_POLICY_ERROR)
        host = normalize_naia_host(entry.get("host"))
        port = entry.get("port")
        if type(port) is not int or not 1 <= port <= 65535:
            raise ValueError(_POLICY_ERROR)
        address = _connection_address(entry.get("address", host))
        # Numeric and localhost selectors cannot be remapped to another machine.
        try:
            numeric_host = str(ipaddress.ip_address(host))
        except ValueError:
            numeric_host = "127.0.0.1" if host == "localhost" else None
        if numeric_host is not None and numeric_host != address:
            raise ValueError(_POLICY_ERROR)
        key = (host, port)
        if key in endpoints and endpoints[key] != address:
            raise ValueError(_POLICY_ERROR)
        endpoints[key] = address
    return tuple((host, port, address) for (host, port), address in endpoints.items())


__all__ = ()
