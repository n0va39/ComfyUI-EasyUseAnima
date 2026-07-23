# pyright: strict
"""Comfy node adapters for authoritative Prompt Studio seed execution."""

from __future__ import annotations

from collections.abc import Callable, Generator
from contextlib import contextmanager
from dataclasses import dataclass
from typing import cast

from ..runtime import get_runtime
from ..seed.execution_identity import resolve_seed_execution_identity
from ..seed.execution_session import seed_execution_session
from ..seed.reservation import (
    SEED_OVERFLOW_WRAP,
    SEED_RESERVATION_CONTRACT_VERSION,
    SEED_RESERVATION_REQUEST_SCHEMA,
    SEED_SELECTION_CONCRETE,
    SeedControl,
    SeedReservationRequest,
)

PROMPT_STUDIO_ADVANCED_SEED_FEATURE = "prompt_studio_advanced"
PROMPT_STUDIO_REGIONAL_SEED_FEATURE = "prompt_studio_regional"
PROMPT_STUDIO_MAX_SAFE_SEED = (1 << 53) - 1


@dataclass(frozen=True, slots=True)
class PromptStudioSeedExecution:
    """Concrete execution and next-run seeds visible to a Prompt Studio node."""

    execution_seed: int
    next_seed: int


@contextmanager
def prompt_studio_seed_execution(
    *,
    feature: str,
    unique_id: object,
    seed: int,
    after_generate: str,
    fallback_next_seed: Callable[[], int],
) -> Generator[PromptStudioSeedExecution, None, None]:
    """Use the process service when host identity exists, otherwise run compatibly."""

    identity = resolve_seed_execution_identity(feature, unique_id=unique_id)
    if identity is None:
        yield PromptStudioSeedExecution(
            execution_seed=seed,
            next_seed=fallback_next_seed(),
        )
        return

    try:
        service = get_runtime().seed_reservations
    except RuntimeError:
        yield PromptStudioSeedExecution(
            execution_seed=seed,
            next_seed=fallback_next_seed(),
        )
        return

    request = SeedReservationRequest(
        schema=SEED_RESERVATION_REQUEST_SCHEMA,
        version=SEED_RESERVATION_CONTRACT_VERSION,
        stream_id=identity.stream_id,
        request_id=identity.request_id,
        selection=SEED_SELECTION_CONCRETE,
        seed=seed,
        after_generate=cast(SeedControl, after_generate),
        next_seed_max=PROMPT_STUDIO_MAX_SAFE_SEED,
        overflow=SEED_OVERFLOW_WRAP,
    )
    with seed_execution_session(service, request) as reservation:
        yield PromptStudioSeedExecution(
            execution_seed=reservation.execution_seed,
            next_seed=reservation.next_seed,
        )


__all__ = (
    "PROMPT_STUDIO_ADVANCED_SEED_FEATURE",
    "PROMPT_STUDIO_REGIONAL_SEED_FEATURE",
    "PromptStudioSeedExecution",
    "prompt_studio_seed_execution",
)
