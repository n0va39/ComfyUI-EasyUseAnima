from __future__ import annotations

import itertools
import subprocess
import sys
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from easyuse_anima.seed.reservation import (
    SEED_CONTROL_FIXED,
    SEED_MAX_UINT64,
    SEED_OVERFLOW_CLAMP,
    SEED_OVERFLOW_WRAP,
    SEED_RESERVATION_CONTRACT_VERSION,
    SEED_RESERVATION_REQUEST_SCHEMA,
    SEED_SELECTION_CONCRETE,
    SEED_SELECTION_DECREMENT,
    SEED_SELECTION_INCREMENT,
    SEED_SELECTION_RANDOMIZE,
    SEED_SETTLEMENT_ACCEPTED,
    SEED_SETTLEMENT_CANCELLED,
    SEED_SETTLEMENT_REJECTED,
    SeedReservationContractError,
    SeedReservationRequest,
)
from easyuse_anima.seed.service import (
    InMemorySeedReservationService,
    SeedReservationCapacityError,
    SeedReservationConflictError,
    SeedReservationServiceError,
)


def make_request(
    request_id: str,
    *,
    stream_id: str = "node:1",
    selection: str = SEED_SELECTION_CONCRETE,
    seed: int | None = 7,
    after_generate: str = SEED_CONTROL_FIXED,
    next_seed_max: int = 10,
    overflow: str = SEED_OVERFLOW_CLAMP,
) -> SeedReservationRequest:
    if selection != SEED_SELECTION_CONCRETE:
        seed = None
    return SeedReservationRequest(
        schema=SEED_RESERVATION_REQUEST_SCHEMA,
        version=SEED_RESERVATION_CONTRACT_VERSION,
        stream_id=stream_id,
        request_id=request_id,
        selection=selection,
        seed=seed,
        after_generate=after_generate,
        next_seed_max=next_seed_max,
        overflow=overflow,
    )


class DrawSequence:
    def __init__(self, *values: object) -> None:
        self.values = iter(values)
        self.upper_bounds: list[int] = []

    def __call__(self, upper_bound: int) -> int:
        self.upper_bounds.append(upper_bound)
        return next(self.values)  # type: ignore[return-value]


def sequential_ids(prefix: str = "reservation"):
    counter = itertools.count(1)
    return lambda: f"{prefix}:{next(counter)}"


class SeedReservationServiceTests(unittest.TestCase):
    def test_concrete_fixed_is_reproducible_after_acceptance(self):
        service = InMemorySeedReservationService(
            reservation_id_factory=sequential_ids(),
        )

        first = service.reserve(make_request("q1", seed=7))
        service.settle(first.reservation_id, SEED_SETTLEMENT_ACCEPTED)
        second = service.reserve(make_request("q2", seed=7))

        self.assertEqual(
            (first.execution_seed, first.next_seed),
            (7, 7),
        )
        self.assertEqual(
            (second.execution_seed, second.next_seed),
            (7, 7),
        )

    def test_repeated_concrete_increment_reserves_unique_fifo_sequence(self):
        service = InMemorySeedReservationService(
            reservation_id_factory=sequential_ids(),
        )
        requests = [
            make_request(
                f"q{index}",
                seed=7,
                after_generate=SEED_SELECTION_INCREMENT,
            )
            for index in range(1, 5)
        ]

        reservations = [service.reserve(request) for request in requests[:3]]
        self.assertEqual(
            [
                (value.execution_seed, value.next_seed)
                for value in reservations
            ],
            [(7, 8), (8, 9), (9, 10)],
        )

        for value in reversed(reservations):
            service.settle(value.reservation_id, SEED_SETTLEMENT_ACCEPTED)
        fourth = service.reserve(requests[3])
        self.assertEqual((fourth.execution_seed, fourth.next_seed), (10, 10))

    def test_idle_concrete_edit_resets_and_pending_edit_is_deferred(self):
        service = InMemorySeedReservationService(
            reservation_id_factory=sequential_ids(),
        )
        first = service.reserve(
            make_request(
                "q1",
                seed=7,
                after_generate=SEED_SELECTION_INCREMENT,
                next_seed_max=100,
            )
        )
        pending_edit = service.reserve(
            make_request(
                "q2",
                seed=20,
                after_generate=SEED_SELECTION_INCREMENT,
                next_seed_max=100,
            )
        )

        self.assertEqual(pending_edit.execution_seed, 8)
        service.settle(first.reservation_id, SEED_SETTLEMENT_ACCEPTED)
        service.settle(pending_edit.reservation_id, SEED_SETTLEMENT_ACCEPTED)
        applied_edit = service.reserve(
            make_request(
                "q3",
                seed=20,
                after_generate=SEED_SELECTION_INCREMENT,
                next_seed_max=100,
            )
        )
        self.assertEqual(
            (applied_edit.execution_seed, applied_edit.next_seed),
            (20, 21),
        )

    def test_random_selection_and_after_generate_use_explicit_domain(self):
        draws = DrawSequence(3, 7)
        service = InMemorySeedReservationService(
            random_seed=draws,
            reservation_id_factory=sequential_ids(),
        )

        result = service.reserve(
            make_request(
                "q1",
                selection=SEED_SELECTION_RANDOMIZE,
                after_generate=SEED_SELECTION_RANDOMIZE,
            )
        )

        self.assertEqual((result.execution_seed, result.next_seed), (3, 7))
        self.assertEqual(draws.upper_bounds, [11, 11])

    def test_increment_and_decrement_selection_use_last_execution_seed(self):
        draws = DrawSequence(4)
        service = InMemorySeedReservationService(
            random_seed=draws,
            reservation_id_factory=sequential_ids(),
        )
        first = service.reserve(
            make_request(
                "q1",
                selection=SEED_SELECTION_INCREMENT,
                after_generate=SEED_SELECTION_INCREMENT,
            )
        )
        service.settle(first.reservation_id, SEED_SETTLEMENT_ACCEPTED)
        second = service.reserve(
            make_request(
                "q2",
                selection=SEED_SELECTION_INCREMENT,
                after_generate=SEED_CONTROL_FIXED,
            )
        )
        service.settle(second.reservation_id, SEED_SETTLEMENT_ACCEPTED)
        third = service.reserve(
            make_request(
                "q3",
                selection=SEED_SELECTION_DECREMENT,
                after_generate=SEED_CONTROL_FIXED,
            )
        )

        self.assertEqual((first.execution_seed, first.next_seed), (4, 5))
        self.assertEqual((second.execution_seed, second.next_seed), (5, 5))
        self.assertEqual((third.execution_seed, third.next_seed), (4, 4))
        self.assertEqual(draws.upper_bounds, [11])

    def test_after_generate_arithmetic_clamps_or_wraps(self):
        cases = (
            ("inc-clamp", 10, SEED_SELECTION_INCREMENT, SEED_OVERFLOW_CLAMP, 10),
            ("inc-wrap", 10, SEED_SELECTION_INCREMENT, SEED_OVERFLOW_WRAP, 0),
            ("dec-clamp", 0, SEED_SELECTION_DECREMENT, SEED_OVERFLOW_CLAMP, 0),
            ("dec-wrap", 0, SEED_SELECTION_DECREMENT, SEED_OVERFLOW_WRAP, 10),
            ("above-clamp", 100, SEED_SELECTION_DECREMENT, SEED_OVERFLOW_CLAMP, 9),
            ("above-wrap", 100, SEED_SELECTION_INCREMENT, SEED_OVERFLOW_WRAP, 2),
        )

        for request_id, seed, control, overflow, expected in cases:
            with self.subTest(request_id=request_id):
                service = InMemorySeedReservationService(
                    reservation_id_factory=sequential_ids(request_id),
                )
                result = service.reserve(
                    make_request(
                        request_id,
                        seed=seed,
                        after_generate=control,
                        overflow=overflow,
                    )
                )
                self.assertEqual(result.next_seed, expected)

    def test_fixed_preserves_uint64_seed_above_next_seed_domain(self):
        service = InMemorySeedReservationService(
            reservation_id_factory=sequential_ids(),
        )

        result = service.reserve(
            make_request(
                "q1",
                seed=SEED_MAX_UINT64,
                next_seed_max=10,
            )
        )

        self.assertEqual(result.execution_seed, SEED_MAX_UINT64)
        self.assertEqual(result.next_seed, SEED_MAX_UINT64)

    def test_pending_and_accepted_duplicates_are_idempotent(self):
        draws = DrawSequence(3)
        ids = sequential_ids()
        service = InMemorySeedReservationService(
            random_seed=draws,
            reservation_id_factory=ids,
        )
        request = make_request(
            "q1",
            selection=SEED_SELECTION_RANDOMIZE,
        )

        first = service.reserve(request)
        self.assertIs(service.reserve(request), first)
        service.settle(first.reservation_id, SEED_SETTLEMENT_ACCEPTED)
        self.assertIs(service.reserve(request), first)
        self.assertEqual(draws.upper_bounds, [11])

    def test_duplicate_identity_with_different_request_conflicts(self):
        service = InMemorySeedReservationService(
            reservation_id_factory=sequential_ids(),
        )
        service.reserve(make_request("q1", seed=7))

        with self.assertRaises(SeedReservationConflictError):
            service.reserve(make_request("q1", seed=8))

    def test_stream_domain_change_conflicts_until_inactive_state_is_evicted(self):
        service = InMemorySeedReservationService(
            reservation_id_factory=sequential_ids(),
            max_streams=1,
        )
        first = service.reserve(make_request("q1", stream_id="a"))
        service.settle(first.reservation_id, SEED_SETTLEMENT_ACCEPTED)

        with self.assertRaises(SeedReservationConflictError):
            service.reserve(
                make_request(
                    "q2",
                    stream_id="a",
                    next_seed_max=20,
                )
            )

        second = service.reserve(make_request("q1", stream_id="b"))
        service.settle(second.reservation_id, SEED_SETTLEMENT_ACCEPTED)
        changed = service.reserve(
            make_request(
                "q3",
                stream_id="a",
                next_seed_max=20,
            )
        )
        self.assertEqual(changed.execution_seed, 7)

    def test_out_of_order_acceptance_commits_only_after_fifo_head_settles(self):
        service = InMemorySeedReservationService(
            reservation_id_factory=sequential_ids(),
        )
        first = service.reserve(
            make_request(
                "q1",
                after_generate=SEED_SELECTION_INCREMENT,
            )
        )
        second = service.reserve(
            make_request(
                "q2",
                after_generate=SEED_SELECTION_INCREMENT,
            )
        )
        service.settle(second.reservation_id, SEED_SETTLEMENT_ACCEPTED)
        self.assertIs(service.reserve(make_request(
            "q2",
            after_generate=SEED_SELECTION_INCREMENT,
        )), second)

        service.settle(first.reservation_id, SEED_SETTLEMENT_REJECTED)
        third = service.reserve(
            make_request(
                "q3",
                after_generate=SEED_SELECTION_INCREMENT,
            )
        )
        self.assertEqual((third.execution_seed, third.next_seed), (9, 10))

    def test_rejected_tail_collapses_and_request_identity_is_retryable(self):
        service = InMemorySeedReservationService(
            reservation_id_factory=sequential_ids(),
        )
        first = service.reserve(
            make_request(
                "q1",
                after_generate=SEED_SELECTION_INCREMENT,
            )
        )
        second_request = make_request(
            "q2",
            after_generate=SEED_SELECTION_INCREMENT,
        )
        second = service.reserve(second_request)
        third = service.reserve(
            make_request(
                "q3",
                after_generate=SEED_SELECTION_INCREMENT,
            )
        )

        service.settle(third.reservation_id, SEED_SETTLEMENT_REJECTED)
        service.settle(second.reservation_id, SEED_SETTLEMENT_REJECTED)
        retried = service.reserve(second_request)

        self.assertNotEqual(retried.reservation_id, second.reservation_id)
        self.assertEqual((retried.execution_seed, retried.next_seed), (8, 9))
        service.settle(first.reservation_id, SEED_SETTLEMENT_ACCEPTED)

    def test_cancel_then_late_accept_is_noop_and_retry_reuses_candidate(self):
        service = InMemorySeedReservationService(
            reservation_id_factory=sequential_ids(),
        )
        request = make_request(
            "q1",
            after_generate=SEED_SELECTION_INCREMENT,
        )
        first = service.reserve(request)

        service.settle(first.reservation_id, SEED_SETTLEMENT_CANCELLED)
        service.settle(first.reservation_id, SEED_SETTLEMENT_ACCEPTED)
        retried = service.reserve(request)

        self.assertNotEqual(retried.reservation_id, first.reservation_id)
        self.assertEqual(
            (retried.execution_seed, retried.next_seed),
            (first.execution_seed, first.next_seed),
        )

    def test_duplicate_and_unknown_settlements_are_noops(self):
        service = InMemorySeedReservationService(
            reservation_id_factory=sequential_ids(),
        )
        result = service.reserve(make_request("q1"))

        service.settle(result.reservation_id, SEED_SETTLEMENT_ACCEPTED)
        service.settle(result.reservation_id, SEED_SETTLEMENT_REJECTED)
        service.settle("unknown", SEED_SETTLEMENT_ACCEPTED)

        self.assertIs(service.reserve(make_request("q1")), result)

    def test_invalid_settlement_fails_before_state_change(self):
        service = InMemorySeedReservationService(
            reservation_id_factory=sequential_ids(),
        )
        result = service.reserve(make_request("q1"))

        with self.assertRaises(SeedReservationContractError):
            service.settle(result.reservation_id, "unknown")  # type: ignore[arg-type]

        service.settle(result.reservation_id, SEED_SETTLEMENT_ACCEPTED)
        self.assertIs(service.reserve(make_request("q1")), result)

    def test_active_capacity_fails_before_rng_or_stream_mutation(self):
        draws = DrawSequence(4)
        service = InMemorySeedReservationService(
            random_seed=draws,
            reservation_id_factory=sequential_ids(),
            max_active_reservations=1,
        )
        first = service.reserve(make_request("q1", stream_id="a"))

        with self.assertRaises(SeedReservationCapacityError):
            service.reserve(
                make_request(
                    "q1",
                    stream_id="b",
                    selection=SEED_SELECTION_RANDOMIZE,
                )
            )
        self.assertEqual(draws.upper_bounds, [])

        service.settle(first.reservation_id, SEED_SETTLEMENT_REJECTED)
        second = service.reserve(
            make_request(
                "q1",
                stream_id="b",
                selection=SEED_SELECTION_RANDOMIZE,
            )
        )
        self.assertEqual(second.execution_seed, 4)

    def test_active_stream_is_never_evicted(self):
        service = InMemorySeedReservationService(
            reservation_id_factory=sequential_ids(),
            max_streams=1,
        )
        service.reserve(make_request("q1", stream_id="a"))

        with self.assertRaises(SeedReservationCapacityError):
            service.reserve(make_request("q1", stream_id="b"))

    def test_inactive_stream_eviction_is_lru(self):
        service = InMemorySeedReservationService(
            reservation_id_factory=sequential_ids(),
            max_streams=2,
        )
        first_a = service.reserve(make_request("a1", stream_id="a"))
        service.settle(first_a.reservation_id, SEED_SETTLEMENT_ACCEPTED)
        first_b = service.reserve(make_request("b1", stream_id="b"))
        service.settle(first_b.reservation_id, SEED_SETTLEMENT_ACCEPTED)
        touch_a = service.reserve(make_request("a2", stream_id="a"))
        service.settle(touch_a.reservation_id, SEED_SETTLEMENT_ACCEPTED)

        first_c = service.reserve(make_request("c1", stream_id="c"))
        service.settle(first_c.reservation_id, SEED_SETTLEMENT_ACCEPTED)

        with self.assertRaises(SeedReservationConflictError):
            service.reserve(
                make_request(
                    "a3",
                    stream_id="a",
                    next_seed_max=20,
                )
            )
        recreated_b = service.reserve(
            make_request(
                "b2",
                stream_id="b",
                next_seed_max=20,
            )
        )
        self.assertEqual(recreated_b.execution_seed, 7)

    def test_accepted_idempotency_history_is_bounded_lru(self):
        service = InMemorySeedReservationService(
            reservation_id_factory=sequential_ids(),
            max_idempotency_records=1,
        )
        first_request = make_request("q1")
        first = service.reserve(first_request)
        service.settle(first.reservation_id, SEED_SETTLEMENT_ACCEPTED)
        second = service.reserve(make_request("q2"))
        service.settle(second.reservation_id, SEED_SETTLEMENT_ACCEPTED)

        repeated = service.reserve(first_request)

        self.assertNotEqual(repeated.reservation_id, first.reservation_id)

    def test_retired_id_history_is_bounded(self):
        service = InMemorySeedReservationService(
            reservation_id_factory=sequential_ids(),
            max_retired_reservation_ids=2,
        )
        for index in range(3):
            result = service.reserve(make_request(f"q{index}"))
            service.settle(result.reservation_id, SEED_SETTLEMENT_REJECTED)

        self.assertEqual(len(service._retired_ids), 2)
        self.assertNotIn("reservation:1", service._retired_ids)

    def test_invalid_random_source_does_not_leave_stream_or_reservation_state(self):
        draws = DrawSequence(11, 5)
        service = InMemorySeedReservationService(
            random_seed=draws,
            reservation_id_factory=sequential_ids(),
            max_streams=1,
        )

        with self.assertRaises(SeedReservationServiceError):
            service.reserve(
                make_request(
                    "q1",
                    stream_id="a",
                    selection=SEED_SELECTION_RANDOMIZE,
                )
            )

        result = service.reserve(
            make_request(
                "q1",
                stream_id="b",
                selection=SEED_SELECTION_RANDOMIZE,
            )
        )
        self.assertEqual(result.execution_seed, 5)
        self.assertNotIn("a", service._streams)

    def test_concurrent_reservations_are_atomic_and_unique(self):
        count = 12
        barrier = Barrier(count)
        service = InMemorySeedReservationService()

        def reserve(index: int):
            barrier.wait()
            return service.reserve(
                make_request(
                    f"q{index}",
                    seed=7,
                    after_generate=SEED_SELECTION_INCREMENT,
                    next_seed_max=100,
                )
            )

        with ThreadPoolExecutor(max_workers=count) as executor:
            reservations = list(executor.map(reserve, range(count)))

        self.assertEqual(
            sorted(value.execution_seed for value in reservations),
            list(range(7, 7 + count)),
        )
        self.assertEqual(
            len({value.reservation_id for value in reservations}),
            count,
        )

    def test_constructor_rejects_unbounded_or_invalid_configuration(self):
        for values in (
            {"max_streams": 0},
            {"max_active_reservations": 0},
            {"max_idempotency_records": 0},
            {"max_retired_reservation_ids": 0},
        ):
            with self.subTest(values=values), self.assertRaises(ValueError):
                InMemorySeedReservationService(**values)

    def test_service_import_is_host_and_filesystem_side_effect_free(self):
        script = (
            f"import sys; sys.path.insert(0, {str(ROOT)!r}); "
            "import easyuse_anima.seed.service; "
            "blocked = {'comfy', 'folder_paths', 'nodes', 'server'} & set(sys.modules); "
            "print(','.join(sorted(blocked)))"
        )

        result = subprocess.run(
            [sys.executable, "-I", "-B", "-c", script],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=10,
        )

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(result.stdout.strip(), "")


if __name__ == "__main__":
    unittest.main()
