from __future__ import annotations

import subprocess
import sys
import unittest
from dataclasses import FrozenInstanceError
from pathlib import Path

from easyuse_anima.aio import generation_normalization
from easyuse_anima.seed import reservation


ROOT = Path(__file__).resolve().parents[1]


def _request_payload(**updates: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "schema": reservation.SEED_RESERVATION_REQUEST_SCHEMA,
        "version": reservation.SEED_RESERVATION_CONTRACT_VERSION,
        "stream_id": "node:42",
        "request_id": "queue:abc",
        "selection": reservation.SEED_SELECTION_CONCRETE,
        "seed": 123,
        "after_generate": reservation.SEED_CONTROL_FIXED,
        "next_seed_max": (1 << 50),
        "overflow": reservation.SEED_OVERFLOW_CLAMP,
    }
    payload.update(updates)
    return payload


class SeedReservationContractTests(unittest.TestCase):
    def test_concrete_request_parses_to_an_immutable_normalized_value(self):
        parsed = reservation.parse_seed_reservation_request(
            _request_payload(stream_id=" node:42 ", request_id=" queue:abc ")
        )

        self.assertEqual(
            parsed,
            reservation.SeedReservationRequest(
                schema=reservation.SEED_RESERVATION_REQUEST_SCHEMA,
                version=2,
                stream_id="node:42",
                request_id="queue:abc",
                selection="concrete",
                seed=123,
                after_generate="fixed",
                next_seed_max=(1 << 50),
                overflow="clamp",
            ),
        )
        with self.assertRaises(FrozenInstanceError):
            parsed.seed = 456

    def test_non_concrete_request_has_no_browser_authoritative_seed(self):
        for selection in ("randomize", "increment", "decrement"):
            with self.subTest(selection=selection):
                parsed = reservation.parse_seed_reservation_request(
                    _request_payload(selection=selection, seed=None)
                )
                self.assertEqual(parsed.selection, selection)
                self.assertIsNone(parsed.seed)

    def test_request_carries_each_reviewed_arithmetic_domain_explicitly(self):
        cases = (
            ((1 << 50), "clamp"),
            (((1 << 53) - 1), "wrap"),
        )

        for next_seed_max, overflow in cases:
            with self.subTest(
                next_seed_max=next_seed_max,
                overflow=overflow,
            ):
                parsed = reservation.parse_seed_reservation_request(
                    _request_payload(
                        next_seed_max=next_seed_max,
                        overflow=overflow,
                    )
                )
                self.assertEqual(parsed.next_seed_max, next_seed_max)
                self.assertEqual(parsed.overflow, overflow)

    def test_uint64_concrete_seed_is_independent_from_the_arithmetic_domain(self):
        parsed = reservation.parse_seed_reservation_request(
            _request_payload(
                seed=reservation.SEED_MAX_UINT64,
                next_seed_max=(1 << 50),
                overflow="clamp",
            )
        )

        self.assertEqual(parsed.seed, reservation.SEED_MAX_UINT64)
        self.assertEqual(parsed.next_seed_max, (1 << 50))

    def test_legacy_sentinels_map_to_distinct_selection_intents(self):
        expected = {
            generation_normalization.AIO_SPECIAL_SEED_RANDOM: "randomize",
            generation_normalization.AIO_SPECIAL_SEED_INCREMENT: "increment",
            generation_normalization.AIO_SPECIAL_SEED_DECREMENT: "decrement",
        }

        self.assertEqual(set(expected), {-1, -2, -3})
        for legacy_seed, selection in expected.items():
            with self.subTest(legacy_seed=legacy_seed):
                parsed = reservation.parse_legacy_seed_reservation_request(
                    stream_id="aio:7",
                    request_id=f"queue:{legacy_seed}",
                    normalized_seed=legacy_seed,
                    after_generate="fixed",
                    next_seed_max=(1 << 50),
                    overflow="clamp",
                )
                self.assertEqual(parsed.selection, selection)
                self.assertIsNone(parsed.seed)

    def test_legacy_concrete_seed_preserves_the_exact_python_integer(self):
        legacy_uint64_max = (1 << 64) - 1

        parsed = reservation.parse_legacy_seed_reservation_request(
            stream_id="aio:7",
            request_id="queue:concrete",
            normalized_seed=legacy_uint64_max,
            after_generate="increment",
            next_seed_max=(1 << 50),
            overflow="clamp",
        )

        self.assertEqual(parsed.selection, "concrete")
        self.assertEqual(parsed.seed, legacy_uint64_max)
        self.assertEqual(parsed.after_generate, "increment")

    def test_request_taxonomy_rejects_ambiguous_or_invalid_values(self):
        invalid_payloads = (
            [],
            _request_payload(schema="other"),
            _request_payload(version=True),
            _request_payload(version=1),
            _request_payload(version=3),
            _request_payload(stream_id=" "),
            _request_payload(request_id=None),
            _request_payload(selection="random"),
            _request_payload(selection="randomize", seed=1),
            _request_payload(seed=None),
            _request_payload(seed=True),
            _request_payload(seed=-1),
            _request_payload(seed=reservation.SEED_MAX_UINT64 + 1),
            _request_payload(after_generate="accept"),
            _request_payload(next_seed_max=None),
            _request_payload(next_seed_max=True),
            _request_payload(next_seed_max=-1),
            _request_payload(
                next_seed_max=reservation.SEED_MAX_UINT64 + 1,
            ),
            _request_payload(overflow="cycle"),
        )

        for payload in invalid_payloads:
            with self.subTest(payload=payload), self.assertRaises(
                reservation.SeedReservationContractError
            ):
                reservation.parse_seed_reservation_request(payload)

    def test_legacy_parser_requires_an_already_normalized_supported_integer(self):
        for seed in (-4, True, 1.5, "-1"):
            with self.subTest(seed=seed), self.assertRaises(
                reservation.SeedReservationContractError
            ):
                reservation.parse_legacy_seed_reservation_request(
                    stream_id="aio:7",
                    request_id="queue:invalid",
                    normalized_seed=seed,
                    after_generate="fixed",
                    next_seed_max=(1 << 50),
                    overflow="clamp",
                )

        with self.assertRaises(reservation.SeedReservationContractError):
            reservation.parse_legacy_seed_reservation_request(
                stream_id="aio:7",
                request_id="queue:invalid-control",
                normalized_seed=1,
                after_generate="unknown",
                next_seed_max=(1 << 50),
                overflow="clamp",
            )

        with self.assertRaises(reservation.SeedReservationContractError):
            reservation.parse_legacy_seed_reservation_request(
                stream_id="aio:7",
                request_id="queue:invalid-domain",
                normalized_seed=1,
                after_generate="fixed",
                next_seed_max=(1 << 50),
                overflow="unknown",
            )

    def test_reservation_result_is_concrete_immutable_and_versioned(self):
        result = reservation.SeedReservation(
            version=2,
            reservation_id=" reservation:1 ",
            stream_id=" node:42 ",
            request_id=" queue:abc ",
            execution_seed=123,
            next_seed=124,
        )

        self.assertEqual(result.reservation_id, "reservation:1")
        self.assertEqual(result.stream_id, "node:42")
        self.assertEqual(result.request_id, "queue:abc")
        with self.assertRaises(FrozenInstanceError):
            result.next_seed = 125

        for updates in (
            {"version": 1},
            {"reservation_id": ""},
            {"execution_seed": -1},
            {"execution_seed": True},
            {"execution_seed": reservation.SEED_MAX_UINT64 + 1},
            {"next_seed": -1},
            {"next_seed": reservation.SEED_MAX_UINT64 + 1},
        ):
            values = {
                "version": 2,
                "reservation_id": "reservation:1",
                "stream_id": "node:42",
                "request_id": "queue:abc",
                "execution_seed": 123,
                "next_seed": 124,
                **updates,
            }
            with self.subTest(values=values), self.assertRaises(
                reservation.SeedReservationContractError
            ):
                reservation.SeedReservation(**values)

    def test_service_port_has_no_implicit_runtime_or_state_owner(self):
        class FakeService:
            def __init__(self) -> None:
                self.calls: list[tuple[str, object]] = []

            def reserve(
                self,
                request: reservation.SeedReservationRequest,
            ) -> reservation.SeedReservation:
                self.calls.append(("reserve", request))
                return reservation.SeedReservation(
                    version=2,
                    reservation_id="reservation:1",
                    stream_id=request.stream_id,
                    request_id=request.request_id,
                    execution_seed=10,
                    next_seed=11,
                )

            def settle(
                self,
                reservation_id: str,
                settlement: reservation.SeedReservationSettlement,
            ) -> None:
                self.calls.append((reservation_id, settlement))

        service: reservation.SeedReservationService = FakeService()
        request = reservation.parse_seed_reservation_request(_request_payload())
        reserved = service.reserve(request)
        service.settle(reserved.reservation_id, "accepted")

        self.assertEqual(reserved.execution_seed, 10)
        self.assertEqual(
            service.calls,
            [("reserve", request), ("reservation:1", "accepted")],
        )

    def test_contract_import_is_side_effect_free_in_a_fresh_process(self):
        script = (
            f"import sys; sys.path.insert(0, {str(ROOT)!r}); "
            "import easyuse_anima.seed.reservation; "
            "blocked = {'nodes', 'wildcard_engine'} & set(sys.modules); "
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
