from __future__ import annotations


ROUTE_REGISTRATION_MARKER = "_easyuse_anima_registered_routes_v1"

_ROUTE_DEFINITION_SPECS = (
    ("get", "/easyuse_anima/settings", "get_settings_handler"),
    ("post", "/easyuse_anima/set_setting", "set_setting_handler"),
    ("get", "/easyuse_anima/long_text_settings", "get_long_text_settings_handler"),
    ("get", "/easyuse_anima/wildcards", "get_wildcards_handler"),
    (
        "post",
        "/easyuse_anima/long_text_settings/save",
        "save_long_text_settings_handler",
    ),
    ("get", "/easyuse_anima/autocomplete_status", "autocomplete_status_handler"),
    ("get", "/easyuse_anima/autocomplete", "autocomplete_handler"),
    ("post", "/easyuse_anima/classify_prompt", "classify_prompt_handler"),
    ("post", "/easyuse_anima/translate_prompt", "translate_prompt_handler"),
    (
        "post",
        "/easyuse_anima/aio/torch-compile/recommend",
        "aio_torch_compile_recommend_handler",
    ),
    ("get", "/easyuse_anima/lora_preview", "lora_preview_handler"),
    ("get", "/easyuse_anima/loras", "loras_handler"),
    ("get", "/easyuse_anima/lora_profiles", "lora_profiles_handler"),
    ("post", "/easyuse_anima/lora_profiles/save", "save_lora_profile_handler"),
    ("get", "/easyuse_anima/lora_profiles/load", "load_lora_profile_handler"),
    ("get", "/easyuse_anima/aio_profiles", "aio_profiles_handler"),
    ("post", "/easyuse_anima/aio_profiles/save", "save_aio_profile_handler"),
    ("get", "/easyuse_anima/aio_profiles/load", "load_aio_profile_handler"),
    ("post", "/easyuse_anima/aio_profiles/delete", "delete_aio_profile_handler"),
    ("post", "/easyuse_anima/aio_profiles/rename", "rename_aio_profile_handler"),
    ("post", "/easyuse_anima/lora_profiles/fix", "fix_lora_profile_handler"),
)


def build_route_definitions(**handlers):
    """Bind the canonical ordered route specs to their composed handlers."""

    return tuple(
        (method, path, handlers[handler_name])
        for method, path, handler_name in _ROUTE_DEFINITION_SPECS
    )


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
