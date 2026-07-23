"""Guard startup work owned by the ComfyUI package entrypoint."""

from __future__ import annotations

import logging
import threading
from collections.abc import Callable

from .infrastructure.comfy.provider import DefaultComfyHostProvider
from .runtime import RuntimeServices, install_runtime

_LOGGER = logging.getLogger("ComfyUI-EasyUseAnima")
_INITIALIZE_LOCK = threading.Lock()
_WILDCARDS_INITIALIZED = False
_DEFAULT_RUNTIME = RuntimeServices(comfy=DefaultComfyHostProvider())


def initialize(
    *,
    register_routes: Callable[[], bool],
    initialize_wildcards: Callable[[], object],
) -> None:
    """Initialize routes and the default wildcard root without duplicate work."""

    global _WILDCARDS_INITIALIZED
    with _INITIALIZE_LOCK:
        install_runtime(_DEFAULT_RUNTIME)
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
