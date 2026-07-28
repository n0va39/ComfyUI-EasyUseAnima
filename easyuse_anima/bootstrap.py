"""Guard startup work owned by the ComfyUI package entrypoint."""

from __future__ import annotations

import logging
import threading
from collections.abc import Callable

from .api.routes.aio_torch_compile import (
    build_aio_torch_compile_recommend_handler as _build_aio_torch_compile_recommend_handler,
)
from .api.routes.aio_profile_mutations import (
    build_aio_profile_mutation_handlers as _build_aio_profile_mutation_handlers,
)
from .api.routes.autocomplete import (
    build_autocomplete_handlers as _build_autocomplete_handlers,
)
from .api.routes.autocomplete import (
    build_classify_prompt_handler as _build_classify_prompt_handler,
)
from .api.routes.long_text_settings import (
    build_long_text_settings_handlers as _build_long_text_settings_handlers,
)
from .api.routes.lora_catalog import build_loras_handler as _build_loras_handler
from .api.routes.lora_preview import (
    build_lora_preview_handler as _build_lora_preview_handler,
)
from .api.routes.lora_profile_fix import (
    build_lora_profile_fix_handler as _build_lora_profile_fix_handler,
)
from .api.routes.profile_lists import (
    build_profile_list_handlers as _build_profile_list_handlers,
)
from .api.routes.profile_loads import (
    build_profile_load_handlers as _build_profile_load_handlers,
)
from .api.routes.profile_saves import (
    build_profile_save_handlers as _build_profile_save_handlers,
)
from .api.routes.settings import build_settings_handlers as _build_settings_handlers
from .api.routes.translation import (
    build_translate_prompt_handler as _build_translate_prompt_handler,
)
from .api.routes.wildcards import (
    build_wildcards_handler as _build_wildcards_handler,
)
from .infrastructure.comfy.provider import DefaultComfyHostProvider
from .runtime import RuntimeServices, install_runtime
from .seed.service import InMemorySeedReservationService

_LOGGER = logging.getLogger("ComfyUI-EasyUseAnima")
_INITIALIZE_LOCK = threading.Lock()
_WILDCARDS_INITIALIZED = False
_DEFAULT_RUNTIME: RuntimeServices | None = None


def _missing_comfy_nodes() -> None:
    return None


def build_settings_route_group(
    *,
    request_correlated,
    settings_dependencies,
    long_text_settings_dependencies,
):
    """Compose the correlated settings route group from canonical factories."""

    handlers = (
        *_build_settings_handlers(**settings_dependencies),
        *_build_long_text_settings_handlers(**long_text_settings_dependencies),
    )
    return tuple(request_correlated(handler) for handler in handlers)


def build_wildcard_autocomplete_route_group(
    *,
    request_correlated,
    wildcards_dependencies,
    autocomplete_dependencies,
    classify_prompt_dependencies,
):
    """Compose correlated wildcard and autocomplete routes."""

    handlers = (
        _build_wildcards_handler(**wildcards_dependencies),
        *_build_autocomplete_handlers(**autocomplete_dependencies),
        _build_classify_prompt_handler(**classify_prompt_dependencies),
    )
    return tuple(request_correlated(handler) for handler in handlers)


def build_translation_route_handler(
    *,
    request_correlated,
    translation_dependencies,
):
    """Compose the correlated translation route."""

    return request_correlated(
        _build_translate_prompt_handler(**translation_dependencies)
    )


def build_aio_torch_compile_route_handler(
    *,
    request_correlated,
    aio_torch_compile_dependencies,
):
    """Compose the correlated AiO Torch Compile recommendation route."""

    return request_correlated(
        _build_aio_torch_compile_recommend_handler(
            **aio_torch_compile_dependencies
        )
    )


def build_lora_read_route_group(
    *,
    request_correlated,
    lora_preview_dependencies,
    lora_catalog_dependencies,
):
    """Compose the correlated LoRA preview and catalog routes."""

    handlers = (
        _build_lora_preview_handler(**lora_preview_dependencies),
        _build_loras_handler(**lora_catalog_dependencies),
    )
    return tuple(request_correlated(handler) for handler in handlers)


def build_profile_list_route_group(
    *,
    request_correlated,
    profile_list_dependencies,
):
    """Compose the correlated LoRA and AiO profile list routes."""

    return tuple(
        request_correlated(handler)
        for handler in _build_profile_list_handlers(
            **profile_list_dependencies
        )
    )


def build_profile_route_group(
    *,
    request_correlated,
    profile_load_dependencies,
    profile_save_dependencies,
    aio_profile_mutation_dependencies,
    lora_profile_fix_dependencies,
):
    """Compose the correlated profile load, save, mutation, and fix routes."""

    handlers = (
        *_build_profile_load_handlers(**profile_load_dependencies),
        *_build_profile_save_handlers(**profile_save_dependencies),
        *_build_aio_profile_mutation_handlers(
            **aio_profile_mutation_dependencies
        ),
        _build_lora_profile_fix_handler(**lora_profile_fix_dependencies),
    )
    return tuple(request_correlated(handler) for handler in handlers)


def initialize(
    *,
    register_routes: Callable[[], bool],
    initialize_wildcards: Callable[[], object],
    load_comfy_nodes: Callable[[], object | None] = _missing_comfy_nodes,
) -> None:
    """Initialize routes and the default wildcard root without duplicate work."""

    global _DEFAULT_RUNTIME, _WILDCARDS_INITIALIZED
    with _INITIALIZE_LOCK:
        runtime = _DEFAULT_RUNTIME
        if runtime is None:
            runtime = RuntimeServices(
                comfy=DefaultComfyHostProvider(load_comfy_nodes),
                seed_reservations=InMemorySeedReservationService(),
            )
            install_runtime(runtime)
            _DEFAULT_RUNTIME = runtime
        else:
            install_runtime(runtime)
        register_routes()
        if _WILDCARDS_INITIALIZED:
            return
        try:
            initialize_wildcards()
        except OSError as exc:
            _LOGGER.warning(
                "EasyUse Anima wildcard folder could not be initialized: %s",
                exc,
            )
            return
        _WILDCARDS_INITIALIZED = True


__all__ = ["initialize"]
