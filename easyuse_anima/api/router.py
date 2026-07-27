from __future__ import annotations


ROUTE_REGISTRATION_MARKER = "_easyuse_anima_registered_routes_v1"


def build_route_signature(route_definitions):
    """Return the stable public signature for an ordered route definition set."""

    return tuple(
        (method.upper(), path)
        for method, path, _handler in route_definitions
    )


def register_route_definitions(
    route_table,
    route_definitions,
    *,
    signature=None,
    marker=ROUTE_REGISTRATION_MARKER,
) -> bool:
    """Register one ordered route set exactly once on a ComfyUI route table."""

    if route_table is None:
        return False

    route_signature = (
        build_route_signature(route_definitions)
        if signature is None
        else signature
    )
    existing_signature = getattr(route_table, marker, None)
    if existing_signature == route_signature:
        return True
    if existing_signature is not None:
        raise RuntimeError("EasyUse Anima route registration signature mismatch")

    for method, path, handler in route_definitions:
        getattr(route_table, method)(path)(handler)
    setattr(route_table, marker, route_signature)
    return True


__all__ = (
    "ROUTE_REGISTRATION_MARKER",
    "build_route_signature",
    "register_route_definitions",
)
