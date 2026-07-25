"""Guard startup work owned by the ComfyUI package entrypoint."""

from __future__ import annotations

import logging
import threading
from collections.abc import Callable

from .infrastructure.comfy.provider import DefaultComfyHostProvider
from .runtime import RuntimeServices, install_runtime
from .seed.service import InMemorySeedReservationService

_LOGGER = logging.getLogger("ComfyUI-EasyUseAnima")
_INITIALIZE_LOCK = threading.Lock()
_WILDCARDS_INITIALIZED = False
_DEFAULT_RUNTIME: RuntimeServices | None = None


def _missing_comfy_nodes() -> None:
    return None


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
