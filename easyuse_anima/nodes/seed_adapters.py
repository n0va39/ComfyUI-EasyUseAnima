# pyright: strict
"""Comfy node adapters for authoritative feature seed execution."""

from __future__ import annotations

import random
from collections.abc import Callable, Generator
from contextlib import contextmanager
from dataclasses import dataclass, replace
from typing import cast

from ..aio.generation_defaults import (
    AIO_GENERATOR_MAX_EDITABLE_SEED,
    AIO_SPECIAL_SEEDS,
)
from ..runtime import get_runtime
from ..seed.execution_identity import resolve_seed_execution_identity
from ..seed.execution_session import seed_execution_session
from ..seed.reservation import (
    SEED_CONTROL_FIXED,
    SEED_OVERFLOW_CLAMP,
    SEED_OVERFLOW_WRAP,
    SEED_RESERVATION_CONTRACT_VERSION,
    SEED_RESERVATION_REQUEST_SCHEMA,
    SEED_SELECTION_CONCRETE,
    SEED_SELECTION_DECREMENT,
    SEED_SELECTION_INCREMENT,
    SEED_SELECTION_RANDOMIZE,
    SeedControl,
    SeedReservationRequest,
    SeedSelection,
    parse_legacy_seed_reservation_request,
)

AIO_GENERATOR_SEED_FEATURE = "aio_generator"
PROMPT_STUDIO_ADVANCED_SEED_FEATURE = "prompt_studio_advanced"
PROMPT_STUDIO_REGIONAL_SEED_FEATURE = "prompt_studio_regional"
PROMPT_STUDIO_MAX_SAFE_SEED = (1 << 53) - 1


@dataclass(frozen=True, slots=True)
class AioSeedExecution:
    """Concrete execution and next-run seeds visible to the AiO node."""

    execution_seed: int
    next_seed: int
    requested_seed: int | None = None
    selection: SeedSelection | None = None
    effective_after_generate: SeedControl | None = None

    def ui_payload(self) -> dict[str, str] | None:
        """Return the canonical UI payload when intent identity is complete."""

        if (
            self.requested_seed is None
            or self.selection is None
            or self.effective_after_generate is None
        ):
            return None
        return {
            "requested_seed": str(self.requested_seed),
            "selection": self.selection,
            "effective_after_generate": self.effective_after_generate,
            "execution_seed": str(self.execution_seed),
            "next_seed": str(self.next_seed),
        }


@dataclass(frozen=True, slots=True)
class PromptStudioSeedExecution:
    """Concrete execution and next-run seeds visible to a Prompt Studio node."""

    execution_seed: int
    next_seed: int


def _new_aio_compatibility_seed() -> int:
    return random.randint(0, AIO_GENERATOR_MAX_EDITABLE_SEED)


def _aio_fallback_execution_seed(
    normalized_seed: int,
    fallback_execution_seed: Callable[[], int],
) -> int:
    if normalized_seed in AIO_SPECIAL_SEEDS:
        return fallback_execution_seed()
    return normalized_seed


def _aio_fallback_next_seed(
    execution_seed: int,
    after_generate: str,
    random_seed: Callable[[], int],
) -> int:
    if after_generate == SEED_CONTROL_FIXED:
        return execution_seed
    if after_generate == SEED_SELECTION_RANDOMIZE:
        return random_seed()
    bounded_seed = min(execution_seed, AIO_GENERATOR_MAX_EDITABLE_SEED)
    if after_generate == SEED_SELECTION_INCREMENT:
        return min(bounded_seed + 1, AIO_GENERATOR_MAX_EDITABLE_SEED)
    if after_generate == SEED_SELECTION_DECREMENT:
        return max(bounded_seed - 1, 0)
    raise ValueError(f"Unsupported AiO seed control: {after_generate}")


def _aio_compatibility_execution(
    requested_seed: int,
    request: SeedReservationRequest,
    fallback_execution_seed: Callable[[], int],
    random_next_seed: Callable[[], int],
) -> AioSeedExecution:
    execution_seed = _aio_fallback_execution_seed(
        requested_seed,
        fallback_execution_seed,
    )
    return AioSeedExecution(
        execution_seed=execution_seed,
        next_seed=_aio_fallback_next_seed(
            execution_seed,
            request.after_generate,
            random_next_seed,
        ),
        requested_seed=requested_seed,
        selection=request.selection,
        effective_after_generate=request.after_generate,
    )


def _normalize_aio_seed_request(
    normalized_seed: int,
    after_generate: str,
) -> SeedReservationRequest:
    request = parse_legacy_seed_reservation_request(
        stream_id="aio:pending",
        request_id="aio:pending",
        normalized_seed=normalized_seed,
        after_generate=cast(SeedControl, after_generate),
        next_seed_max=AIO_GENERATOR_MAX_EDITABLE_SEED,
        overflow=SEED_OVERFLOW_CLAMP,
    )
    if request.selection != SEED_SELECTION_CONCRETE:
        return replace(request, after_generate=SEED_CONTROL_FIXED)
    return request


@contextmanager
def aio_seed_execution(
    *,
    unique_id: object,
    normalized_seed: int,
    after_generate: str,
    fallback_execution_seed: Callable[[], int] = _new_aio_compatibility_seed,
    random_next_seed: Callable[[], int] = _new_aio_compatibility_seed,
) -> Generator[AioSeedExecution, None, None]:
    """Reserve AiO execution state, with an isolated compatibility fallback."""

    request = _normalize_aio_seed_request(normalized_seed, after_generate)
    identity = resolve_seed_execution_identity(
        AIO_GENERATOR_SEED_FEATURE,
        unique_id=unique_id,
    )
    if identity is None:
        yield _aio_compatibility_execution(
            normalized_seed,
            request,
            fallback_execution_seed,
            random_next_seed,
        )
        return

    try:
        service = get_runtime().seed_reservations
    except RuntimeError:
        yield _aio_compatibility_execution(
            normalized_seed,
            request,
            fallback_execution_seed,
            random_next_seed,
        )
        return

    request = replace(
        request,
        stream_id=identity.stream_id,
        request_id=identity.request_id,
    )
    with seed_execution_session(service, request) as reservation:
        yield AioSeedExecution(
            execution_seed=reservation.execution_seed,
            next_seed=reservation.next_seed,
            requested_seed=normalized_seed,
            selection=request.selection,
            effective_after_generate=request.after_generate,
        )


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
    "AIO_GENERATOR_SEED_FEATURE",
    "AioSeedExecution",
    "PROMPT_STUDIO_ADVANCED_SEED_FEATURE",
    "PROMPT_STUDIO_REGIONAL_SEED_FEATURE",
    "PromptStudioSeedExecution",
    "aio_seed_execution",
    "prompt_studio_seed_execution",
)
