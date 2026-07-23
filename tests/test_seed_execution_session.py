from __future__ import annotations

import subprocess
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch

from easyuse_anima.seed import execution_session
from easyuse_anima.seed.reservation import (
    SEED_CONTROL_FIXED,
    SEED_OVERFLOW_CLAMP,
    SEED_RESERVATION_CONTRACT_VERSION,
    SEED_RESERVATION_REQUEST_SCHEMA,
    SEED_SELECTION_CONCRETE,
    SEED_SETTLEMENT_ACCEPTED,
    SEED_SETTLEMENT_CANCELLED,
    SEED_SETTLEMENT_REJECTED,
    SeedReservation,
    SeedReservationRequest,
    SeedReservationSettlement,
)


ROOT = Path(__file__).resolve().parents[1]


def make_request(request_id: str = "request:1") -> SeedReservationRequest:
    return SeedReservationRequest(
        schema=SEED_RESERVATION_REQUEST_SCHEMA,
        version=SEED_RESERVATION_CONTRACT_VERSION,
        stream_id="stream:7",
        request_id=request_id,
        selection=SEED_SELECTION_CONCRETE,
        seed=7,
        after_generate=SEED_CONTROL_FIXED,
        next_seed_max=(1 << 50),
        overflow=SEED_OVERFLOW_CLAMP,
    )


class RecordingService:
    def __init__(self, *, reserve_error: BaseException | None = None) -> None:
        self.reserve_error = reserve_error
        self.calls: list[tuple[str, object]] = []
        self.reservation = SeedReservation(
            version=SEED_RESERVATION_CONTRACT_VERSION,
            reservation_id="reservation:1",
            stream_id="stream:7",
            request_id="request:1",
            execution_seed=7,
            next_seed=7,
        )

    def reserve(self, request: SeedReservationRequest) -> SeedReservation:
        self.calls.append(("reserve", request))
        if self.reserve_error is not None:
            raise self.reserve_error
        return self.reservation

    def settle(
        self,
        reservation_id: str,
        settlement: SeedReservationSettlement,
    ) -> None:
        self.calls.append((reservation_id, settlement))


class SeedExecutionSessionTests(unittest.TestCase):
    def test_normal_return_settles_accepted_after_the_body(self):
        service = RecordingService()
        observations: list[object] = []

        with execution_session.seed_execution_session(
            service,
            make_request(),
        ) as reservation:
            observations.append(reservation)
            observations.append(tuple(service.calls))

        self.assertIs(observations[0], service.reservation)
        self.assertEqual(
            observations[1],
            (("reserve", make_request()),),
        )
        self.assertEqual(
            service.calls,
            [
                ("reserve", make_request()),
                ("reservation:1", SEED_SETTLEMENT_ACCEPTED),
            ],
        )

    def test_regular_exception_settles_rejected_and_is_reraised(self):
        service = RecordingService()
        original = RuntimeError("generation failed")

        with self.assertRaises(RuntimeError) as captured:
            with execution_session.seed_execution_session(
                service,
                make_request(),
                is_interruption=lambda _error: False,
            ):
                raise original

        self.assertIs(captured.exception, original)
        self.assertEqual(
            service.calls[-1],
            ("reservation:1", SEED_SETTLEMENT_REJECTED),
        )

    def test_comfy_base_exception_settles_cancelled_and_is_reraised(self):
        class InterruptProcessingException(BaseException):
            pass

        module = types.SimpleNamespace(
            InterruptProcessingException=InterruptProcessingException,
        )
        original = InterruptProcessingException()
        service = RecordingService()

        with self.assertRaises(InterruptProcessingException) as captured:
            with execution_session.seed_execution_session(
                service,
                make_request(),
                is_interruption=lambda error: (
                    execution_session.is_comfy_processing_interruption(
                        error,
                        load_module=lambda _module_name: module,
                    )
                ),
            ):
                raise original

        self.assertIs(captured.exception, original)
        self.assertEqual(
            service.calls[-1],
            ("reservation:1", SEED_SETTLEMENT_CANCELLED),
        )
        with patch.dict(
            sys.modules,
            {"comfy.model_management": module},
        ):
            self.assertTrue(
                execution_session.is_comfy_processing_interruption(original)
            )

    def test_non_comfy_base_exception_is_rejected(self):
        service = RecordingService()

        with self.assertRaises(KeyboardInterrupt):
            with execution_session.seed_execution_session(
                service,
                make_request(),
                is_interruption=lambda _error: False,
            ):
                raise KeyboardInterrupt()

        self.assertEqual(
            service.calls[-1],
            ("reservation:1", SEED_SETTLEMENT_REJECTED),
        )

    def test_classifier_failure_does_not_mask_the_execution_error(self):
        service = RecordingService()
        original = ValueError("body failed")

        def classifier(_error: BaseException) -> bool:
            raise LookupError("host classifier failed")

        with self.assertRaises(ValueError) as captured:
            with execution_session.seed_execution_session(
                service,
                make_request(),
                is_interruption=classifier,
            ):
                raise original

        self.assertIs(captured.exception, original)
        self.assertEqual(
            service.calls[-1],
            ("reservation:1", SEED_SETTLEMENT_REJECTED),
        )

    def test_reserve_failure_does_not_attempt_settlement(self):
        original = RuntimeError("capacity exhausted")
        service = RecordingService(reserve_error=original)

        with self.assertRaises(RuntimeError) as captured:
            with execution_session.seed_execution_session(
                service,
                make_request(),
            ):
                self.fail("session body must not run")

        self.assertIs(captured.exception, original)
        self.assertEqual(service.calls, [("reserve", make_request())])

    def test_duplicate_success_session_remains_service_idempotent(self):
        from easyuse_anima.seed.service import InMemorySeedReservationService

        service = InMemorySeedReservationService(
            reservation_id_factory=lambda: "reservation:stable",
        )
        request = make_request()

        with execution_session.seed_execution_session(
            service,
            request,
        ) as first:
            self.assertEqual(first.execution_seed, 7)
        with execution_session.seed_execution_session(
            service,
            request,
        ) as second:
            self.assertIs(second, first)

    def test_rejected_session_allows_same_request_retry(self):
        from easyuse_anima.seed.service import InMemorySeedReservationService

        ids = iter(("reservation:1", "reservation:2"))
        service = InMemorySeedReservationService(
            reservation_id_factory=lambda: next(ids),
        )
        request = make_request()

        with self.assertRaises(ValueError):
            with execution_session.seed_execution_session(
                service,
                request,
                is_interruption=lambda _error: False,
            ) as first:
                raise ValueError(first.reservation_id)

        with execution_session.seed_execution_session(
            service,
            request,
        ) as retried:
            self.assertEqual(retried.reservation_id, "reservation:2")
            self.assertEqual(retried.execution_seed, 7)

    def test_host_classifier_handles_absent_or_malformed_modules(self):
        error = RuntimeError("failed")

        def unavailable(_module_name: str) -> object:
            raise ImportError("Comfy is unavailable")

        self.assertFalse(
            execution_session.is_comfy_processing_interruption(
                error,
                load_module=unavailable,
            )
        )
        self.assertFalse(
            execution_session.is_comfy_processing_interruption(
                error,
                load_module=lambda _module_name: types.SimpleNamespace(
                    InterruptProcessingException="not-a-type",
                ),
            )
        )

    def test_contract_import_does_not_import_comfy_in_a_fresh_process(self):
        script = (
            f"import sys; sys.path.insert(0, {str(ROOT)!r}); "
            "import easyuse_anima.seed.execution_session; "
            "print(int('comfy' in sys.modules))"
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
        self.assertEqual(result.stdout.strip(), "0")


if __name__ == "__main__":
    unittest.main()
