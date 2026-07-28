from __future__ import annotations


ROUTE_REGISTRATION_MARKER = "_easyuse_anima_registered_routes_v1"


def build_prompt_routes_resolver(*, resolve_server):
    """Build the compatibility resolver for the active ComfyUI route table."""

    def _get_prompt_routes():
        server = resolve_server()
        if server is None:
            return None
        prompt_server = getattr(
            getattr(server, "PromptServer", None),
            "instance",
            None,
        )
        return getattr(prompt_server, "routes", None)

    return _get_prompt_routes


def build_route_registrar(
    *,
    resolve_prompt_routes,
    publish_routes,
    resolve_web,
    resolve_route_definitions,
    resolve_route_signature,
    register_route_definitions,
    marker=ROUTE_REGISTRATION_MARKER,
):
    """Build the root-compatible facade around canonical route registration."""

    def register_routes(route_table=None) -> bool:
        target = (
            resolve_prompt_routes()
            if route_table is None
            else route_table
        )
        publish_routes(target)
        if resolve_web() is None or target is None:
            return False
        return register_route_definitions(
            target,
            resolve_route_definitions(),
            signature=resolve_route_signature(),
            marker=marker,
        )

    return register_routes


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
