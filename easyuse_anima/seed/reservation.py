# pyright: strict
"""Pure request and service contracts for backend seed reservation."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Literal, Protocol, TypeAlias, cast

SEED_RESERVATION_REQUEST_SCHEMA = "easyuse_anima_seed_reservation_request"
SEED_RESERVATION_CONTRACT_VERSION = 2
SEED_MAX_UINT64 = 0xFFFFFFFFFFFFFFFF

SEED_SELECTION_CONCRETE = "concrete"
SEED_SELECTION_RANDOMIZE = "randomize"
SEED_SELECTION_INCREMENT = "increment"
SEED_SELECTION_DECREMENT = "decrement"
SEED_SELECTIONS = frozenset(
    {
        SEED_SELECTION_CONCRETE,
        SEED_SELECTION_RANDOMIZE,
        SEED_SELECTION_INCREMENT,
        SEED_SELECTION_DECREMENT,
    }
)

SEED_CONTROL_FIXED = "fixed"
SEED_CONTROLS = frozenset(
    {
        SEED_CONTROL_FIXED,
        SEED_SELECTION_RANDOMIZE,
        SEED_SELECTION_INCREMENT,
        SEED_SELECTION_DECREMENT,
    }
)

SEED_OVERFLOW_CLAMP = "clamp"
SEED_OVERFLOW_WRAP = "wrap"
SEED_OVERFLOW_POLICIES = frozenset(
    {
        SEED_OVERFLOW_CLAMP,
        SEED_OVERFLOW_WRAP,
    }
)

SEED_SETTLEMENT_ACCEPTED = "accepted"
SEED_SETTLEMENT_REJECTED = "rejected"
SEED_SETTLEMENT_CANCELLED = "cancelled"
SEED_SETTLEMENTS = frozenset(
    {
        SEED_SETTLEMENT_ACCEPTED,
        SEED_SETTLEMENT_REJECTED,
        SEED_SETTLEMENT_CANCELLED,
    }
)

SeedSelection: TypeAlias = Literal[
    "concrete",
    "randomize",
    "increment",
    "decrement",
]
SeedControl: TypeAlias = Literal[
    "fixed",
    "randomize",
    "increment",
    "decrement",
]
SeedOverflowPolicy: TypeAlias = Literal[
    "clamp",
    "wrap",
]
SeedReservationSettlement: TypeAlias = Literal[
    "accepted",
    "rejected",
    "cancelled",
]

_LEGACY_SELECTION_BY_SEED: Mapping[int, SeedSelection] = {
    -1: SEED_SELECTION_RANDOMIZE,
    -2: SEED_SELECTION_INCREMENT,
    -3: SEED_SELECTION_DECREMENT,
}


class SeedReservationContractError(ValueError):
    """A seed reservation request or result violates the versioned contract."""


def _require_version(value: object) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or value != SEED_RESERVATION_CONTRACT_VERSION
    ):
        raise SeedReservationContractError(
            "Seed reservation version is missing or unsupported"
        )
    return value


def _require_identity(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise SeedReservationContractError(f"{label} must be a non-empty string")
    return value.strip()


def _require_choice(
    value: object,
    choices: frozenset[str],
    label: str,
) -> str:
    if not isinstance(value, str) or value not in choices:
        raise SeedReservationContractError(f"{label} is invalid")
    return value


def _require_concrete_seed(value: object, label: str) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or value < 0
        or value > SEED_MAX_UINT64
    ):
        raise SeedReservationContractError(
            f"{label} must be an unsigned 64-bit integer"
        )
    return value


@dataclass(frozen=True, slots=True)
class SeedReservationRequest:
    """Versioned intent for one logical seed stream and queue request."""

    schema: str
    version: int
    stream_id: str
    request_id: str
    selection: SeedSelection
    seed: int | None
    after_generate: SeedControl
    next_seed_max: int
    overflow: SeedOverflowPolicy

    def __post_init__(self) -> None:
        if self.schema != SEED_RESERVATION_REQUEST_SCHEMA:
            raise SeedReservationContractError(
                "Seed reservation schema is missing or unsupported"
            )
        _require_version(self.version)
        object.__setattr__(
            self,
            "stream_id",
            _require_identity(self.stream_id, "Seed stream_id"),
        )
        object.__setattr__(
            self,
            "request_id",
            _require_identity(self.request_id, "Seed request_id"),
        )
        selection = cast(
            SeedSelection,
            _require_choice(self.selection, SEED_SELECTIONS, "Seed selection"),
        )
        object.__setattr__(self, "selection", selection)
        object.__setattr__(
            self,
            "after_generate",
            cast(
                SeedControl,
                _require_choice(
                    self.after_generate,
                    SEED_CONTROLS,
                    "Seed after_generate",
                ),
            ),
        )
        object.__setattr__(
            self,
            "next_seed_max",
            _require_concrete_seed(self.next_seed_max, "Seed next_seed_max"),
        )
        object.__setattr__(
            self,
            "overflow",
            cast(
                SeedOverflowPolicy,
                _require_choice(
                    self.overflow,
                    SEED_OVERFLOW_POLICIES,
                    "Seed overflow",
                ),
            ),
        )
        if selection == SEED_SELECTION_CONCRETE:
            object.__setattr__(
                self,
                "seed",
                _require_concrete_seed(self.seed, "Concrete seed"),
            )
        elif self.seed is not None:
            raise SeedReservationContractError(
                "Non-concrete seed selection must not carry a seed"
            )


@dataclass(frozen=True, slots=True)
class SeedReservation:
    """Opaque reservation plus service-selected concrete seed state."""

    version: int
    reservation_id: str
    stream_id: str
    request_id: str
    execution_seed: int
    next_seed: int

    def __post_init__(self) -> None:
        _require_version(self.version)
        object.__setattr__(
            self,
            "reservation_id",
            _require_identity(self.reservation_id, "Seed reservation_id"),
        )
        object.__setattr__(
            self,
            "stream_id",
            _require_identity(self.stream_id, "Seed stream_id"),
        )
        object.__setattr__(
            self,
            "request_id",
            _require_identity(self.request_id, "Seed request_id"),
        )
        object.__setattr__(
            self,
            "execution_seed",
            _require_concrete_seed(self.execution_seed, "Execution seed"),
        )
        object.__setattr__(
            self,
            "next_seed",
            _require_concrete_seed(self.next_seed, "Next seed"),
        )


class SeedReservationService(Protocol):
    """Port implemented by the authoritative S167-02 reservation owner."""

    def reserve(self, request: SeedReservationRequest) -> SeedReservation: ...

    def settle(
        self,
        reservation_id: str,
        settlement: SeedReservationSettlement,
    ) -> None: ...


def parse_seed_reservation_request(
    payload: Mapping[str, object],
) -> SeedReservationRequest:
    """Parse a version-1 concrete request without reserving or selecting a seed."""

    if not isinstance(cast(object, payload), Mapping):
        raise SeedReservationContractError(
            "Seed reservation request must be a JSON object"
        )
    return SeedReservationRequest(
        schema=cast(str, payload.get("schema")),
        version=cast(int, payload.get("version")),
        stream_id=cast(str, payload.get("stream_id")),
        request_id=cast(str, payload.get("request_id")),
        selection=cast(SeedSelection, payload.get("selection")),
        seed=cast(int | None, payload.get("seed")),
        after_generate=cast(SeedControl, payload.get("after_generate")),
        next_seed_max=cast(int, payload.get("next_seed_max")),
        overflow=cast(SeedOverflowPolicy, payload.get("overflow")),
    )


def parse_legacy_seed_reservation_request(
    *,
    stream_id: str,
    request_id: str,
    normalized_seed: int,
    after_generate: SeedControl,
    next_seed_max: int,
    overflow: SeedOverflowPolicy,
) -> SeedReservationRequest:
    """Translate an already-normalized legacy AiO seed without choosing a seed."""

    raw_seed = cast(object, normalized_seed)
    if isinstance(raw_seed, bool) or not isinstance(raw_seed, int):
        raise SeedReservationContractError(
            "Legacy normalized seed must be an integer"
        )
    if raw_seed < -3:
        raise SeedReservationContractError(
            "Legacy normalized seed is outside the supported range"
        )
    selection = _LEGACY_SELECTION_BY_SEED.get(
        raw_seed,
        SEED_SELECTION_CONCRETE,
    )
    concrete_seed = (
        raw_seed if selection == SEED_SELECTION_CONCRETE else None
    )
    return SeedReservationRequest(
        schema=SEED_RESERVATION_REQUEST_SCHEMA,
        version=SEED_RESERVATION_CONTRACT_VERSION,
        stream_id=stream_id,
        request_id=request_id,
        selection=selection,
        seed=concrete_seed,
        after_generate=after_generate,
        next_seed_max=next_seed_max,
        overflow=overflow,
    )


__all__ = (
    "SEED_CONTROL_FIXED",
    "SEED_CONTROLS",
    "SEED_MAX_UINT64",
    "SEED_OVERFLOW_CLAMP",
    "SEED_OVERFLOW_POLICIES",
    "SEED_OVERFLOW_WRAP",
    "SEED_RESERVATION_CONTRACT_VERSION",
    "SEED_RESERVATION_REQUEST_SCHEMA",
    "SEED_SELECTION_CONCRETE",
    "SEED_SELECTION_DECREMENT",
    "SEED_SELECTION_INCREMENT",
    "SEED_SELECTION_RANDOMIZE",
    "SEED_SELECTIONS",
    "SEED_SETTLEMENT_ACCEPTED",
    "SEED_SETTLEMENT_CANCELLED",
    "SEED_SETTLEMENT_REJECTED",
    "SEED_SETTLEMENTS",
    "SeedControl",
    "SeedOverflowPolicy",
    "SeedReservation",
    "SeedReservationContractError",
    "SeedReservationRequest",
    "SeedReservationService",
    "SeedReservationSettlement",
    "SeedSelection",
    "parse_legacy_seed_reservation_request",
    "parse_seed_reservation_request",
)
