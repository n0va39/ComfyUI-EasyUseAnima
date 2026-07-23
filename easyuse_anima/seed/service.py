# pyright: strict
"""Process-local authoritative seed reservation service."""

from __future__ import annotations

import secrets
import threading
import uuid
from collections import OrderedDict, deque
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import TypeAlias

from .reservation import (
    SEED_CONTROL_FIXED,
    SEED_OVERFLOW_CLAMP,
    SEED_OVERFLOW_WRAP,
    SEED_RESERVATION_CONTRACT_VERSION,
    SEED_SELECTION_CONCRETE,
    SEED_SELECTION_DECREMENT,
    SEED_SELECTION_INCREMENT,
    SEED_SELECTION_RANDOMIZE,
    SEED_SETTLEMENT_ACCEPTED,
    SEED_SETTLEMENTS,
    SeedOverflowPolicy,
    SeedReservation,
    SeedReservationContractError,
    SeedReservationRequest,
    SeedReservationSettlement,
)

_RequestIdentity: TypeAlias = tuple[str, str]
_RandomSeed: TypeAlias = Callable[[int], int]
_ReservationIdFactory: TypeAlias = Callable[[], str]


class SeedReservationServiceError(RuntimeError):
    """The process-local reservation service cannot complete an operation."""


class SeedReservationConflictError(SeedReservationServiceError):
    """A request identity or stream domain conflicts with retained state."""


class SeedReservationCapacityError(SeedReservationServiceError):
    """A configured bounded state store has no safe capacity."""


def _require_positive_configuration(value: object, label: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValueError(f"{label} must be a positive integer")


def _require_request(value: object) -> SeedReservationRequest:
    if not isinstance(value, SeedReservationRequest):
        raise TypeError("request must be a SeedReservationRequest")
    return value


def _require_seed_draw(value: object, maximum: int) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or value < 0
        or value > maximum
    ):
        raise SeedReservationServiceError(
            "Seed random source returned a value outside the requested domain"
        )
    return value


def _require_generated_id(value: object) -> str:
    if not isinstance(value, str) or not value.strip():
        raise SeedReservationServiceError(
            "Seed reservation ID factory returned an invalid identity"
        )
    return value.strip()


def _require_settlement_id(value: object) -> str:
    if not isinstance(value, str) or not value.strip():
        raise SeedReservationContractError(
            "Seed reservation_id must be a non-empty string"
        )
    return value.strip()


@dataclass(slots=True)
class _ReservationRecord:
    request: SeedReservationRequest
    reservation: SeedReservation
    observed_seed_after: int | None
    settlement: SeedReservationSettlement | None = None


def _new_reservation_queue() -> deque[_ReservationRecord]:
    return deque()


@dataclass(slots=True)
class _StreamState:
    stream_id: str
    next_seed_max: int
    overflow: SeedOverflowPolicy
    committed_execution_seed: int | None = None
    committed_seed: int | None = None
    observed_seed: int | None = None
    reservations: deque[_ReservationRecord] = field(
        default_factory=_new_reservation_queue,
    )


@dataclass(frozen=True, slots=True)
class _AcceptedRecord:
    request: SeedReservationRequest
    reservation: SeedReservation


def _default_reservation_id() -> str:
    return uuid.uuid4().hex


class InMemorySeedReservationService:
    """Bounded, thread-safe reservation state for one backend process."""

    def __init__(
        self,
        *,
        random_seed: _RandomSeed = secrets.randbelow,
        reservation_id_factory: _ReservationIdFactory = _default_reservation_id,
        max_streams: int = 1024,
        max_active_reservations: int = 4096,
        max_idempotency_records: int = 4096,
        max_retired_reservation_ids: int = 4096,
    ) -> None:
        for label, value in (
            ("max_streams", max_streams),
            ("max_active_reservations", max_active_reservations),
            ("max_idempotency_records", max_idempotency_records),
            ("max_retired_reservation_ids", max_retired_reservation_ids),
        ):
            _require_positive_configuration(value, label)
        if not callable(random_seed):
            raise TypeError("random_seed must be callable")
        if not callable(reservation_id_factory):
            raise TypeError("reservation_id_factory must be callable")

        self._random_seed = random_seed
        self._reservation_id_factory = reservation_id_factory
        self._max_streams = max_streams
        self._max_active_reservations = max_active_reservations
        self._max_idempotency_records = max_idempotency_records
        self._max_retired_reservation_ids = max_retired_reservation_ids

        self._lock = threading.RLock()
        self._streams: dict[str, _StreamState] = {}
        self._inactive_streams: OrderedDict[str, None] = OrderedDict()
        self._request_records: dict[_RequestIdentity, _ReservationRecord] = {}
        self._accepted_records: OrderedDict[
            _RequestIdentity,
            _AcceptedRecord,
        ] = OrderedDict()
        self._records_by_id: dict[str, _ReservationRecord] = {}
        self._queued_ids: set[str] = set()
        self._retired_ids: OrderedDict[str, None] = OrderedDict()
        self._record_count = 0

    def reserve(self, request: SeedReservationRequest) -> SeedReservation:
        """Reserve one concrete execution/next-seed pair atomically."""

        request = _require_request(request)

        identity = (request.stream_id, request.request_id)
        with self._lock:
            duplicate = self._request_records.get(identity)
            if duplicate is not None:
                self._require_same_request(duplicate.request, request)
                return duplicate.reservation

            accepted = self._accepted_records.get(identity)
            if accepted is not None:
                self._require_same_request(accepted.request, request)
                self._accepted_records.move_to_end(identity)
                return accepted.reservation

            state = self._streams.get(request.stream_id)
            if state is not None:
                self._require_same_domain(state, request)

            evicted_stream_id = self._capacity_preflight(
                request.stream_id,
                state,
            )
            execution_seed, observed_seed_after = self._select_execution_seed(
                state,
                request,
            )
            next_seed = self._select_next_seed(execution_seed, request)
            reservation_id = self._new_reservation_id()
            reservation = SeedReservation(
                version=SEED_RESERVATION_CONTRACT_VERSION,
                reservation_id=reservation_id,
                stream_id=request.stream_id,
                request_id=request.request_id,
                execution_seed=execution_seed,
                next_seed=next_seed,
            )
            record = _ReservationRecord(
                request=request,
                reservation=reservation,
                observed_seed_after=observed_seed_after,
            )

            if evicted_stream_id is not None:
                del self._streams[evicted_stream_id]
                del self._inactive_streams[evicted_stream_id]
            if state is None:
                state = _StreamState(
                    stream_id=request.stream_id,
                    next_seed_max=request.next_seed_max,
                    overflow=request.overflow,
                )
                self._streams[request.stream_id] = state
            self._inactive_streams.pop(request.stream_id, None)
            state.reservations.append(record)
            self._request_records[identity] = record
            self._records_by_id[reservation_id] = record
            self._queued_ids.add(reservation_id)
            self._record_count += 1
            return reservation

    def settle(
        self,
        reservation_id: str,
        settlement: SeedReservationSettlement,
    ) -> None:
        """Apply the first terminal settlement and ignore later duplicates."""

        normalized_id = self._normalize_reservation_id(reservation_id)
        if settlement not in SEED_SETTLEMENTS:
            raise SeedReservationContractError(
                "Seed reservation settlement is invalid"
            )

        with self._lock:
            record = self._records_by_id.pop(normalized_id, None)
            if record is None:
                return

            record.settlement = settlement
            self._remember_retired_id(normalized_id)
            identity = (
                record.reservation.stream_id,
                record.reservation.request_id,
            )
            if settlement != SEED_SETTLEMENT_ACCEPTED:
                self._request_records.pop(identity, None)

            state = self._streams[record.reservation.stream_id]
            self._collapse_rejected_tail(state)
            self._flush_settled_head(state)
            if not state.reservations:
                self._inactive_streams[state.stream_id] = None
                self._inactive_streams.move_to_end(state.stream_id)

    @staticmethod
    def _require_same_request(
        existing: SeedReservationRequest,
        incoming: SeedReservationRequest,
    ) -> None:
        if existing != incoming:
            raise SeedReservationConflictError(
                "Seed request identity is already used by different request data"
            )

    @staticmethod
    def _require_same_domain(
        state: _StreamState,
        request: SeedReservationRequest,
    ) -> None:
        if (
            state.next_seed_max != request.next_seed_max
            or state.overflow != request.overflow
        ):
            raise SeedReservationConflictError(
                "Seed stream arithmetic domain differs from retained state"
            )

    def _capacity_preflight(
        self,
        stream_id: str,
        state: _StreamState | None,
    ) -> str | None:
        if self._record_count >= self._max_active_reservations:
            raise SeedReservationCapacityError(
                "Seed reservation capacity is exhausted"
            )
        if state is not None or len(self._streams) < self._max_streams:
            return None
        if not self._inactive_streams:
            raise SeedReservationCapacityError(
                "Seed stream capacity is exhausted by active streams"
            )
        evicted_stream_id = next(iter(self._inactive_streams))
        if evicted_stream_id == stream_id:
            raise AssertionError("existing stream was not resolved before eviction")
        return evicted_stream_id

    def _select_execution_seed(
        self,
        state: _StreamState | None,
        request: SeedReservationRequest,
    ) -> tuple[int, int | None]:
        if request.selection == SEED_SELECTION_RANDOMIZE:
            return self._draw_seed(request.next_seed_max), self._observed_seed(state)

        if request.selection in (
            SEED_SELECTION_INCREMENT,
            SEED_SELECTION_DECREMENT,
        ):
            basis = self._execution_basis(state)
            if basis is None:
                execution_seed = self._draw_seed(request.next_seed_max)
            else:
                execution_seed = self._step_seed(
                    basis,
                    request.selection,
                    request.next_seed_max,
                    request.overflow,
                )
            return execution_seed, self._observed_seed(state)

        if request.selection != SEED_SELECTION_CONCRETE or request.seed is None:
            raise SeedReservationContractError("Seed selection is invalid")

        concrete_seed = request.seed
        if state is None:
            return concrete_seed, concrete_seed
        if state.reservations:
            tail = state.reservations[-1]
            observed_seed = tail.observed_seed_after
            if concrete_seed in (
                observed_seed,
                tail.reservation.execution_seed,
                tail.reservation.next_seed,
            ):
                observed_seed = concrete_seed
            return tail.reservation.next_seed, observed_seed

        if concrete_seed in (
            state.observed_seed,
            state.committed_execution_seed,
            state.committed_seed,
        ):
            execution_seed = (
                state.committed_seed
                if state.committed_seed is not None
                else concrete_seed
            )
        else:
            execution_seed = concrete_seed
        return execution_seed, concrete_seed

    def _select_next_seed(
        self,
        execution_seed: int,
        request: SeedReservationRequest,
    ) -> int:
        if request.after_generate == SEED_CONTROL_FIXED:
            return execution_seed
        if request.after_generate == SEED_SELECTION_RANDOMIZE:
            return self._draw_seed(request.next_seed_max)
        if request.after_generate in (
            SEED_SELECTION_INCREMENT,
            SEED_SELECTION_DECREMENT,
        ):
            return self._step_seed(
                execution_seed,
                request.after_generate,
                request.next_seed_max,
                request.overflow,
            )
        raise SeedReservationContractError("Seed after_generate is invalid")

    @staticmethod
    def _observed_seed(state: _StreamState | None) -> int | None:
        if state is None:
            return None
        if state.reservations:
            return state.reservations[-1].observed_seed_after
        return state.observed_seed

    @staticmethod
    def _execution_basis(state: _StreamState | None) -> int | None:
        if state is None:
            return None
        if state.reservations:
            return state.reservations[-1].reservation.execution_seed
        return state.committed_execution_seed

    def _draw_seed(self, maximum: int) -> int:
        return _require_seed_draw(self._random_seed(maximum + 1), maximum)

    @staticmethod
    def _step_seed(
        seed: int,
        direction: str,
        maximum: int,
        overflow: SeedOverflowPolicy,
    ) -> int:
        if overflow == SEED_OVERFLOW_WRAP:
            domain_size = maximum + 1
            normalized = seed % domain_size
            if direction == SEED_SELECTION_INCREMENT:
                return (normalized + 1) % domain_size
            return (normalized - 1) % domain_size

        if overflow != SEED_OVERFLOW_CLAMP:
            raise SeedReservationContractError("Seed overflow policy is invalid")
        normalized = min(seed, maximum)
        if direction == SEED_SELECTION_INCREMENT:
            return min(normalized + 1, maximum)
        return max(normalized - 1, 0)

    def _new_reservation_id(self) -> str:
        for _attempt in range(16):
            reservation_id = _require_generated_id(
                self._reservation_id_factory()
            )
            if (
                reservation_id not in self._queued_ids
                and reservation_id not in self._retired_ids
            ):
                return reservation_id
        raise SeedReservationServiceError(
            "Seed reservation ID factory could not produce a unique identity"
        )

    @staticmethod
    def _normalize_reservation_id(reservation_id: str) -> str:
        return _require_settlement_id(reservation_id)

    def _collapse_rejected_tail(self, state: _StreamState) -> None:
        while state.reservations:
            record = state.reservations[-1]
            if record.settlement is None:
                return
            if record.settlement == SEED_SETTLEMENT_ACCEPTED:
                return
            state.reservations.pop()
            self._forget_queued_record(record)

    def _flush_settled_head(self, state: _StreamState) -> None:
        while state.reservations:
            record = state.reservations[0]
            settlement = record.settlement
            if settlement is None:
                return
            state.reservations.popleft()
            self._forget_queued_record(record)
            if settlement != SEED_SETTLEMENT_ACCEPTED:
                continue

            reservation = record.reservation
            state.committed_execution_seed = reservation.execution_seed
            state.committed_seed = reservation.next_seed
            state.observed_seed = record.observed_seed_after
            identity = (reservation.stream_id, reservation.request_id)
            self._request_records.pop(identity, None)
            self._accepted_records[identity] = _AcceptedRecord(
                request=record.request,
                reservation=reservation,
            )
            self._accepted_records.move_to_end(identity)
            while len(self._accepted_records) > self._max_idempotency_records:
                self._accepted_records.popitem(last=False)

    def _forget_queued_record(self, record: _ReservationRecord) -> None:
        self._queued_ids.remove(record.reservation.reservation_id)
        self._record_count -= 1

    def _remember_retired_id(self, reservation_id: str) -> None:
        self._retired_ids[reservation_id] = None
        self._retired_ids.move_to_end(reservation_id)
        while len(self._retired_ids) > self._max_retired_reservation_ids:
            self._retired_ids.popitem(last=False)


__all__ = (
    "InMemorySeedReservationService",
    "SeedReservationCapacityError",
    "SeedReservationConflictError",
    "SeedReservationServiceError",
)
