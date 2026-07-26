from __future__ import annotations

import unittest
from dataclasses import replace
from types import SimpleNamespace
from unittest.mock import Mock, patch

from easyuse_anima.nodes.seed_adapters import (
    AioSeedExecution,
    aio_seed_execution,
    prompt_studio_seed_execution,
)
from easyuse_anima.seed.execution_identity import SeedExecutionIdentity
from easyuse_anima.seed.reservation import (
    SEED_CONTROL_FIXED,
    SEED_OVERFLOW_CLAMP,
    SEED_SELECTION_CONCRETE,
    SEED_SETTLEMENT_ACCEPTED,
    SeedReservation,
    parse_legacy_seed_reservation_request,
)
from easyuse_anima.seed.service import InMemorySeedReservationService


AIO_CONTRACT_MAX_SEED = 1 << 50
AIO_SPECIAL_SELECTIONS = {
    -1: "randomize",
    -2: "increment",
    -3: "decrement",
}
AIO_STORED_AFTER_GENERATE_CONTROLS = (
    "fixed",
    "randomize",
    "increment",
    "decrement",
)
AIO_CONTRACT_NORMALIZATION_OWNER = "aio_seed_execution"
AIO_MISSING_IDENTITY_SPECIAL_POLICY = (
    "one-concrete-seed-per-invocation-no-persistent-stream-or-double-advance"
)


def _aio_contract_request(
    *,
    stream_id: str,
    request_id: str,
    normalized_seed: int,
    stored_after_generate: str,
):
    request = parse_legacy_seed_reservation_request(
        stream_id=stream_id,
        request_id=request_id,
        normalized_seed=normalized_seed,
        after_generate=stored_after_generate,
        next_seed_max=AIO_CONTRACT_MAX_SEED,
        overflow=SEED_OVERFLOW_CLAMP,
    )
    if request.selection != SEED_SELECTION_CONCRETE:
        return replace(request, after_generate=SEED_CONTROL_FIXED)
    return request


def _aio_contract_missing_identity_execution(
    *,
    invocation_id: str,
    normalized_seed: int,
    stored_after_generate: str,
    select_concrete_seed,
):
    """Model aio_seed_execution normalization before its branch decision."""
    request = _aio_contract_request(
        stream_id="compatibility:isolated",
        request_id=invocation_id,
        normalized_seed=normalized_seed,
        stored_after_generate=stored_after_generate,
    )
    if request.selection == SEED_SELECTION_CONCRETE:
        raise AssertionError("missing-identity fixture only models special intent")
    execution_seed = select_concrete_seed()
    return request, AioSeedExecution(
        execution_seed=execution_seed,
        next_seed=execution_seed,
    )


class SeedAdapterTests(unittest.TestCase):
    def test_aio_missing_identity_contract_normalizes_before_fallback(self):
        self.assertEqual(
            AIO_CONTRACT_NORMALIZATION_OWNER,
            "aio_seed_execution",
        )
        self.assertEqual(
            AIO_MISSING_IDENTITY_SPECIAL_POLICY,
            (
                "one-concrete-seed-per-invocation-"
                "no-persistent-stream-or-double-advance"
            ),
        )
        for normalized_seed, selection in AIO_SPECIAL_SELECTIONS.items():
            for stored_after_generate in AIO_STORED_AFTER_GENERATE_CONTROLS:
                with self.subTest(
                    normalized_seed=normalized_seed,
                    stored_after_generate=stored_after_generate,
                ):
                    select_concrete_seed = Mock(side_effect=(7, 7))
                    observed = []
                    for invocation_index in range(2):
                        request, execution = (
                            _aio_contract_missing_identity_execution(
                                invocation_id=f"invocation:{invocation_index}",
                                normalized_seed=normalized_seed,
                                stored_after_generate=stored_after_generate,
                                select_concrete_seed=select_concrete_seed,
                            )
                        )
                        self.assertEqual(request.selection, selection)
                        self.assertEqual(
                            request.after_generate,
                            SEED_CONTROL_FIXED,
                        )
                        observed.append(
                            (execution.execution_seed, execution.next_seed)
                        )

                    self.assertEqual(observed, [(7, 7), (7, 7)])
                    self.assertEqual(select_concrete_seed.call_count, 2)

    def test_aio_runtime_normalizes_special_control_before_service_branch(self):
        service = Mock()
        service.reserve.return_value = SeedReservation(
            version=2,
            reservation_id="reservation:aio",
            stream_id="stream:aio",
            request_id="request:aio",
            execution_seed=12,
            next_seed=13,
        )
        identity = SeedExecutionIdentity(
            stream_id="stream:aio",
            request_id="request:aio",
        )
        with (
            patch(
                "easyuse_anima.nodes.seed_adapters.resolve_seed_execution_identity",
                return_value=identity,
            ),
            patch(
                "easyuse_anima.nodes.seed_adapters.get_runtime",
                return_value=SimpleNamespace(seed_reservations=service),
            ),
        ):
            with aio_seed_execution(
                unique_id="8",
                normalized_seed=-2,
                after_generate="increment",
            ) as execution:
                self.assertEqual(
                    (execution.execution_seed, execution.next_seed),
                    (12, 13),
                )

        request = service.reserve.call_args.args[0]
        self.assertEqual(request.selection, "increment")
        self.assertIsNone(request.seed)
        self.assertEqual(request.after_generate, "fixed")
        self.assertEqual(request.next_seed_max, 1 << 50)
        self.assertEqual(request.overflow, "clamp")
        service.settle.assert_called_once_with(
            "reservation:aio",
            SEED_SETTLEMENT_ACCEPTED,
        )

    def test_aio_runtime_result_carries_normalized_intent_identity(self):
        service = Mock()
        service.reserve.return_value = SeedReservation(
            version=2,
            reservation_id="reservation:aio",
            stream_id="stream:aio",
            request_id="request:aio",
            execution_seed=12,
            next_seed=12,
        )
        identity = SeedExecutionIdentity(
            stream_id="stream:aio",
            request_id="request:aio",
        )
        with (
            patch(
                "easyuse_anima.nodes.seed_adapters.resolve_seed_execution_identity",
                return_value=identity,
            ),
            patch(
                "easyuse_anima.nodes.seed_adapters.get_runtime",
                return_value=SimpleNamespace(seed_reservations=service),
            ),
        ):
            with aio_seed_execution(
                unique_id="8",
                normalized_seed=-3,
                after_generate="randomize",
            ) as execution:
                self.assertEqual(
                    execution.ui_payload(),
                    {
                        "requested_seed": "-3",
                        "selection": "decrement",
                        "effective_after_generate": "fixed",
                        "execution_seed": "12",
                        "next_seed": "12",
                    },
                )

    def test_aio_missing_identity_selects_special_seed_once_per_invocation(self):
        for normalized_seed in AIO_SPECIAL_SELECTIONS:
            with self.subTest(normalized_seed=normalized_seed):
                fallback_execution_seed = Mock(return_value=7)
                random_next_seed = Mock(return_value=11)
                with (
                    patch(
                        "easyuse_anima.nodes.seed_adapters.resolve_seed_execution_identity",
                        return_value=None,
                    ),
                    patch(
                        "easyuse_anima.nodes.seed_adapters.get_runtime"
                    ) as get_runtime,
                ):
                    with aio_seed_execution(
                        unique_id=None,
                        normalized_seed=normalized_seed,
                        after_generate="randomize",
                        fallback_execution_seed=fallback_execution_seed,
                        random_next_seed=random_next_seed,
                    ) as execution:
                        self.assertEqual(
                            (execution.execution_seed, execution.next_seed),
                            (7, 7),
                        )
                        self.assertEqual(
                            execution.effective_after_generate,
                            "fixed",
                        )

                fallback_execution_seed.assert_called_once_with()
                random_next_seed.assert_not_called()
                get_runtime.assert_not_called()

    def test_aio_increment_selection_advances_on_completed_backend_execution(self):
        ids = iter(("reservation:1", "reservation:2"))
        service = InMemorySeedReservationService(
            random_seed=lambda _upper_bound: 4,
            reservation_id_factory=lambda: next(ids),
        )
        identities = [
            SeedExecutionIdentity("stream:aio", "request:1"),
            SeedExecutionIdentity("stream:aio", "request:2"),
        ]
        with (
            patch(
                "easyuse_anima.nodes.seed_adapters.resolve_seed_execution_identity",
                side_effect=identities,
            ),
            patch(
                "easyuse_anima.nodes.seed_adapters.get_runtime",
                return_value=SimpleNamespace(seed_reservations=service),
            ),
        ):
            observed = []
            for _ in range(2):
                with aio_seed_execution(
                    unique_id="8",
                    normalized_seed=-2,
                    after_generate="fixed",
                ) as execution:
                    observed.append(
                        (execution.execution_seed, execution.next_seed)
                    )

        self.assertEqual(observed, [(4, 4), (5, 5)])

    def test_aio_concrete_selection_resets_after_completed_special_selection(self):
        ids = iter(
            (
                "reservation:concrete",
                "reservation:special",
                "reservation:reset",
            )
        )
        service = InMemorySeedReservationService(
            reservation_id_factory=lambda: next(ids),
        )
        identities = [
            SeedExecutionIdentity("stream:aio", "request:concrete"),
            SeedExecutionIdentity("stream:aio", "request:special"),
            SeedExecutionIdentity("stream:aio", "request:reset"),
        ]
        with (
            patch(
                "easyuse_anima.nodes.seed_adapters.resolve_seed_execution_identity",
                side_effect=identities,
            ),
            patch(
                "easyuse_anima.nodes.seed_adapters.get_runtime",
                return_value=SimpleNamespace(seed_reservations=service),
            ),
        ):
            observed = []
            for normalized_seed, after_generate in (
                (7, "increment"),
                (-2, "fixed"),
                (7, "increment"),
            ):
                with aio_seed_execution(
                    unique_id="8",
                    normalized_seed=normalized_seed,
                    after_generate=after_generate,
                ) as execution:
                    observed.append(
                        (execution.execution_seed, execution.next_seed)
                    )

        self.assertEqual(observed, [(7, 8), (8, 8), (7, 8)])

    def test_aio_special_selection_and_stored_control_golden_matrix(self):
        expected_execution_seeds = {
            -1: [10, 10, 30],
            -2: [10, 11, 12],
            -3: [10, 9, 8],
        }
        expected_random_draws = {-1: 3, -2: 1, -3: 1}

        for normalized_seed, selection in AIO_SPECIAL_SELECTIONS.items():
            for stored_after_generate in AIO_STORED_AFTER_GENERATE_CONTROLS:
                with self.subTest(
                    normalized_seed=normalized_seed,
                    stored_after_generate=stored_after_generate,
                ):
                    draws = iter((10, 10, 30))
                    random_calls = []
                    reservation_ids = iter(
                        f"reservation:{index}" for index in range(3)
                    )

                    def random_seed(upper_bound):
                        random_calls.append(upper_bound)
                        return next(draws)

                    service = InMemorySeedReservationService(
                        random_seed=random_seed,
                        reservation_id_factory=lambda: next(reservation_ids),
                    )
                    observed = []
                    stream_id = (
                        f"stream:{normalized_seed}:{stored_after_generate}"
                    )
                    for index in range(3):
                        request = _aio_contract_request(
                            stream_id=stream_id,
                            request_id=f"request:{index}",
                            normalized_seed=normalized_seed,
                            stored_after_generate=stored_after_generate,
                        )
                        self.assertEqual(request.selection, selection)
                        self.assertEqual(
                            request.after_generate,
                            SEED_CONTROL_FIXED,
                        )
                        reservation = service.reserve(request)
                        observed.append(
                            (
                                reservation.execution_seed,
                                reservation.next_seed,
                            )
                        )
                        service.settle(
                            reservation.reservation_id,
                            SEED_SETTLEMENT_ACCEPTED,
                        )

                    execution_seeds = expected_execution_seeds[normalized_seed]
                    self.assertEqual(
                        observed,
                        [(seed, seed) for seed in execution_seeds],
                    )
                    self.assertEqual(
                        len(random_calls),
                        expected_random_draws[normalized_seed],
                    )

    def test_aio_concrete_seed_and_after_generate_golden_matrix(self):
        expected_next_seed = {
            "fixed": 7,
            "randomize": 91,
            "increment": 8,
            "decrement": 6,
        }
        for stored_after_generate, next_seed in expected_next_seed.items():
            with self.subTest(stored_after_generate=stored_after_generate):
                random_calls = []

                def random_seed(upper_bound):
                    random_calls.append(upper_bound)
                    return 91

                service = InMemorySeedReservationService(
                    random_seed=random_seed,
                    reservation_id_factory=lambda: "reservation:concrete",
                )
                request = _aio_contract_request(
                    stream_id=f"stream:concrete:{stored_after_generate}",
                    request_id="request:concrete",
                    normalized_seed=7,
                    stored_after_generate=stored_after_generate,
                )
                self.assertEqual(request.selection, SEED_SELECTION_CONCRETE)
                self.assertEqual(request.seed, 7)
                self.assertEqual(
                    request.after_generate,
                    stored_after_generate,
                )
                reservation = service.reserve(request)
                self.assertEqual(reservation.execution_seed, 7)
                self.assertEqual(reservation.next_seed, next_seed)
                self.assertEqual(
                    len(random_calls),
                    1 if stored_after_generate == "randomize" else 0,
                )

    def test_missing_identity_uses_compatibility_values_without_runtime_lookup(self):
        with (
            patch(
                "easyuse_anima.nodes.seed_adapters.resolve_seed_execution_identity",
                return_value=None,
            ),
            patch("easyuse_anima.nodes.seed_adapters.get_runtime") as get_runtime,
        ):
            with prompt_studio_seed_execution(
                feature="prompt_studio_advanced",
                unique_id=None,
                seed=7,
                after_generate="increment",
                fallback_next_seed=lambda: 8,
            ) as execution:
                self.assertEqual(
                    (execution.execution_seed, execution.next_seed),
                    (7, 8),
                )

        get_runtime.assert_not_called()

    def test_installed_runtime_owns_request_and_acceptance(self):
        service = Mock()
        fallback_next_seed = Mock(return_value=8)
        service.reserve.return_value = SeedReservation(
            version=2,
            reservation_id="reservation:1",
            stream_id="stream:1",
            request_id="request:1",
            execution_seed=9,
            next_seed=10,
        )
        identity = SeedExecutionIdentity(
            stream_id="stream:1",
            request_id="request:1",
        )
        with (
            patch(
                "easyuse_anima.nodes.seed_adapters.resolve_seed_execution_identity",
                return_value=identity,
            ),
            patch(
                "easyuse_anima.nodes.seed_adapters.get_runtime",
                return_value=SimpleNamespace(seed_reservations=service),
            ),
        ):
            with prompt_studio_seed_execution(
                feature="prompt_studio_advanced",
                unique_id="41",
                seed=7,
                after_generate="increment",
                fallback_next_seed=fallback_next_seed,
            ) as execution:
                self.assertEqual(
                    (execution.execution_seed, execution.next_seed),
                    (9, 10),
                )

        request = service.reserve.call_args.args[0]
        self.assertEqual(request.seed, 7)
        self.assertEqual(request.after_generate, "increment")
        self.assertEqual(request.next_seed_max, (1 << 53) - 1)
        fallback_next_seed.assert_not_called()
        service.settle.assert_called_once_with(
            "reservation:1",
            SEED_SETTLEMENT_ACCEPTED,
        )


if __name__ == "__main__":
    unittest.main()
