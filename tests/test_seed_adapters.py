from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from easyuse_anima.nodes.seed_adapters import (
    aio_seed_execution,
    prompt_studio_seed_execution,
)
from easyuse_anima.seed.execution_identity import SeedExecutionIdentity
from easyuse_anima.seed.reservation import (
    SEED_SETTLEMENT_ACCEPTED,
    SeedReservation,
)
from easyuse_anima.seed.service import InMemorySeedReservationService


class SeedAdapterTests(unittest.TestCase):
    def test_aio_missing_identity_uses_isolated_legacy_selection(self):
        fallback_execution_seed = Mock(return_value=7)
        random_next_seed = Mock(return_value=11)
        with (
            patch(
                "easyuse_anima.nodes.seed_adapters.resolve_seed_execution_identity",
                return_value=None,
            ),
            patch("easyuse_anima.nodes.seed_adapters.get_runtime") as get_runtime,
        ):
            with aio_seed_execution(
                unique_id=None,
                normalized_seed=-1,
                after_generate="randomize",
                fallback_execution_seed=fallback_execution_seed,
                random_next_seed=random_next_seed,
            ) as execution:
                self.assertEqual(
                    (execution.execution_seed, execution.next_seed),
                    (7, 11),
                )

        get_runtime.assert_not_called()
        fallback_execution_seed.assert_called_once_with()
        random_next_seed.assert_called_once_with()

    def test_aio_installed_runtime_translates_legacy_selection_and_domain(self):
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
        self.assertEqual(request.after_generate, "increment")
        self.assertEqual(request.next_seed_max, 1 << 50)
        self.assertEqual(request.overflow, "clamp")
        service.settle.assert_called_once_with(
            "reservation:aio",
            SEED_SETTLEMENT_ACCEPTED,
        )

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
