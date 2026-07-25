from __future__ import annotations

import json
import unittest

from easyuse_anima.seed import compatibility


class SeedCompatibilityConsumerTests(unittest.TestCase):
    def _consume(
        self,
        *,
        current_seed: int,
        next_seed: int,
        reservation_mode: str,
        wildcard_mode: str,
        control: str,
    ) -> int | None:
        reservation = json.dumps(
            {
                "version": 1,
                "current_seed": current_seed,
                "next_seed": next_seed,
                "mode": reservation_mode,
                "control": control,
            }
        )
        reservation_inputs = {
            compatibility.WILDCARD_RESERVED_NEXT_SEED_INPUT: reservation,
            "field": "preserved",
        }
        workflow_prompt = {
            "42": {
                "inputs": {
                    compatibility.WILDCARD_RESERVED_NEXT_SEED_INPUT: reservation,
                    "field": "preserved",
                }
            }
        }

        result = compatibility._consume_reserved_wildcard_next_seed(
            reservation_inputs,
            workflow_prompt,
            ["42"],
            current_seed,
            wildcard_mode,
            control,
        )

        self.assertNotIn(
            compatibility.WILDCARD_RESERVED_NEXT_SEED_INPUT,
            reservation_inputs,
        )
        self.assertNotIn(
            compatibility.WILDCARD_RESERVED_NEXT_SEED_INPUT,
            workflow_prompt["42"]["inputs"],
        )
        self.assertEqual(reservation_inputs["field"], "preserved")
        self.assertEqual(workflow_prompt["42"]["inputs"]["field"], "preserved")
        return result

    def test_valid_control_matrix_preserves_next_seed_results(self):
        cases = (
            ("populate", "일반", "fixed", 7, 7),
            ("populate", "일반", "randomize", 7, 91),
            ("sequential", "순차", "increment", 7, 8),
            ("sequential", "순차", "decrement", 7, 6),
            (
                "sequential",
                "순차",
                "increment",
                compatibility.WILDCARD_QUEUE_MAX_SAFE_SEED,
                0,
            ),
            (
                "sequential",
                "순차",
                "decrement",
                0,
                compatibility.WILDCARD_QUEUE_MAX_SAFE_SEED,
            ),
        )
        for reservation_mode, wildcard_mode, control, current_seed, next_seed in cases:
            with self.subTest(
                reservation_mode=reservation_mode,
                control=control,
                current_seed=current_seed,
            ):
                self.assertEqual(
                    self._consume(
                        current_seed=current_seed,
                        next_seed=next_seed,
                        reservation_mode=reservation_mode,
                        wildcard_mode=wildcard_mode,
                        control=control,
                    ),
                    next_seed,
                )

    def test_mismatch_returns_none_after_scrubbing_both_inputs(self):
        self.assertIsNone(
            self._consume(
                current_seed=7,
                next_seed=8,
                reservation_mode="populate",
                wildcard_mode="순차",
                control="increment",
            )
        )

    def test_malformed_payload_returns_none_after_scrubbing_both_inputs(self):
        key = compatibility.WILDCARD_RESERVED_NEXT_SEED_INPUT
        reservation_inputs = {key: "{malformed", "field": "preserved"}
        workflow_prompt = {
            "42": {"inputs": {key: "{malformed", "field": "preserved"}}
        }

        result = compatibility._consume_reserved_wildcard_next_seed(
            reservation_inputs,
            workflow_prompt,
            "42",
            7,
            "populate",
            "fixed",
        )

        self.assertIsNone(result)
        self.assertEqual(reservation_inputs, {"field": "preserved"})
        self.assertEqual(
            workflow_prompt["42"]["inputs"],
            {"field": "preserved"},
        )

    def test_non_mapping_reservation_inputs_do_not_mutate_workflow_prompt(self):
        key = compatibility.WILDCARD_RESERVED_NEXT_SEED_INPUT
        workflow_prompt = {"42": {"inputs": {key: "preserved"}}}

        result = compatibility._consume_reserved_wildcard_next_seed(
            None,
            workflow_prompt,
            "42",
            7,
            "populate",
            "fixed",
        )

        self.assertIsNone(result)
        self.assertEqual(
            workflow_prompt,
            {"42": {"inputs": {key: "preserved"}}},
        )


if __name__ == "__main__":
    unittest.main()
