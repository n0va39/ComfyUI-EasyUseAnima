# pyright: strict
"""Exception-safe lifetime for one authoritative seed reservation."""

from __future__ import annotations

import sys
from collections.abc import Callable, Generator
from contextlib import contextmanager
from typing import TypeAlias

from .reservation import (
    SEED_SETTLEMENT_ACCEPTED,
    SEED_SETTLEMENT_CANCELLED,
    SEED_SETTLEMENT_REJECTED,
    SeedReservation,
    SeedReservationRequest,
    SeedReservationService,
    SeedReservationSettlement,
)

_COMFY_MODEL_MANAGEMENT = "comfy.model_management"
_COMFY_INTERRUPTION = "InterruptProcessingException"

_HostModuleLoader: TypeAlias = Callable[[str], object | None]
_InterruptionClassifier: TypeAlias = Callable[[BaseException], bool]


def _loaded_host_module(module_name: str) -> object | None:
    return sys.modules.get(module_name)


def is_comfy_processing_interruption(
    error: BaseException,
    *,
    load_module: _HostModuleLoader = _loaded_host_module,
) -> bool:
    """Match Comfy's already-loaded execution interruption signal."""

    try:
        module = load_module(_COMFY_MODEL_MANAGEMENT)
        interruption_type = getattr(module, _COMFY_INTERRUPTION)
        if not isinstance(interruption_type, type):
            return False
        return isinstance(error, interruption_type)
    except Exception:
        return False


def _settlement_for_error(
    error: BaseException,
    is_interruption: _InterruptionClassifier,
) -> SeedReservationSettlement:
    try:
        interrupted = is_interruption(error)
    except Exception:
        interrupted = False
    return (
        SEED_SETTLEMENT_CANCELLED
        if interrupted
        else SEED_SETTLEMENT_REJECTED
    )


@contextmanager
def seed_execution_session(
    service: SeedReservationService,
    request: SeedReservationRequest,
    *,
    is_interruption: _InterruptionClassifier = is_comfy_processing_interruption,
) -> Generator[SeedReservation, None, None]:
    """Reserve once and settle from the wrapped execution outcome."""

    reservation = service.reserve(request)
    try:
        yield reservation
    except BaseException as error:
        service.settle(
            reservation.reservation_id,
            _settlement_for_error(error, is_interruption),
        )
        raise
    else:
        service.settle(
            reservation.reservation_id,
            SEED_SETTLEMENT_ACCEPTED,
        )


__all__ = (
    "is_comfy_processing_interruption",
    "seed_execution_session",
)
