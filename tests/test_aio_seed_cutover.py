from __future__ import annotations

import unittest
from contextlib import contextmanager
from unittest.mock import patch

from easyuse_anima.nodes import aio_nodes
from easyuse_anima.nodes.seed_adapters import AioSeedExecution


SPECIAL_SELECTION_BY_SEED = {
    -1: "randomize",
    -2: "increment",
    -3: "decrement",
}
STORED_AFTER_GENERATE_CONTROLS = (
    "fixed",
    "randomize",
    "increment",
    "decrement",
)
AIO_SEED_RESULT_CONTRACT_FIELDS = (
    "requested_seed",
    "selection",
    "effective_after_generate",
    "execution_seed",
    "next_seed",
)


def _contract_seed_payload(
    *,
    requested_seed: int,
    stored_after_generate: str,
    execution_seed: int,
    next_seed: int,
) -> dict[str, str]:
    selection = SPECIAL_SELECTION_BY_SEED.get(requested_seed, "concrete")
    special = selection != "concrete"
    return {
        "requested_seed": str(requested_seed),
        "selection": selection,
        "effective_after_generate": (
            "fixed" if special else stored_after_generate
        ),
        "execution_seed": str(execution_seed),
        "next_seed": str(next_seed),
    }


class AioSeedCutoverTests(unittest.TestCase):
    def test_generate_uses_reserved_seed_and_publishes_backend_display(self):
        settings = {
            "sampler": {
                "seed": -1,
                "seed_after_generate": "increment",
            },
        }
        legacy_output = {
            "ui": {"status": ["generated"]},
            "result": ("image", "latent", '{"schema":"metadata"}'),
        }

        @contextmanager
        def reserved_seed(**kwargs):
            fallback_execution_seed = kwargs.pop(
                "fallback_execution_seed"
            )
            self.assertEqual(
                kwargs,
                {
                    "unique_id": "41",
                    "normalized_seed": -1,
                    "after_generate": "increment",
                },
            )
            self.assertTrue(callable(fallback_execution_seed))
            yield AioSeedExecution(execution_seed=17, next_seed=18)

        with (
            patch.object(
                aio_nodes,
                "_normalize_aio_generation_settings",
                return_value=settings,
            ),
            patch.object(
                aio_nodes,
                "_require_easy_use_anima_input",
                return_value="normalized input",
            ),
            patch.object(
                aio_nodes,
                "aio_seed_execution",
                reserved_seed,
            ),
            patch.object(
                aio_nodes,
                "_run_aio_generation_pipeline",
                return_value=legacy_output,
            ) as legacy_generation,
        ):
            output = aio_nodes.EasyUseAnimaAIOGenerator().generate(
                "input",
                "serialized settings",
                lora_stack="lora",
                workflow_prompt={"41": {}},
                extra_pnginfo={"workflow": {}},
                unique_id="41",
            )

        passed_settings = legacy_generation.call_args.args[2]
        self.assertEqual(
            legacy_generation.call_args.args[1],
            "normalized input",
        )
        self.assertEqual(legacy_generation.call_args.kwargs, {})
        self.assertEqual(passed_settings["sampler"]["seed"], 17)
        self.assertEqual(
            passed_settings["sampler"]["seed_after_generate"],
            "increment",
        )
        self.assertEqual(
            output["result"],
            ("image", "latent", '{"schema":"metadata"}'),
        )
        self.assertEqual(output["ui"]["status"], ["generated"])
        self.assertEqual(
            output["ui"]["easyuse_anima_aio_seed"],
            [{"execution_seed": "17", "next_seed": "18"}],
        )

    def test_result_contract_uses_five_canonical_backend_fields(self):
        for requested_seed, selection in SPECIAL_SELECTION_BY_SEED.items():
            for stored_after_generate in STORED_AFTER_GENERATE_CONTROLS:
                with self.subTest(
                    requested_seed=requested_seed,
                    stored_after_generate=stored_after_generate,
                ):
                    payload = _contract_seed_payload(
                        requested_seed=requested_seed,
                        stored_after_generate=stored_after_generate,
                        execution_seed=17,
                        next_seed=17,
                    )
                    self.assertEqual(
                        tuple(payload),
                        AIO_SEED_RESULT_CONTRACT_FIELDS,
                    )
                    self.assertEqual(payload["selection"], selection)
                    self.assertEqual(
                        payload["effective_after_generate"],
                        "fixed",
                    )
                    self.assertEqual(
                        payload["next_seed"],
                        payload["execution_seed"],
                    )

        concrete_next_by_control = {
            "fixed": 7,
            "randomize": 91,
            "increment": 8,
            "decrement": 6,
        }
        for stored_after_generate, next_seed in concrete_next_by_control.items():
            with self.subTest(stored_after_generate=stored_after_generate):
                payload = _contract_seed_payload(
                    requested_seed=7,
                    stored_after_generate=stored_after_generate,
                    execution_seed=7,
                    next_seed=next_seed,
                )
                self.assertEqual(payload["selection"], "concrete")
                self.assertEqual(
                    payload["effective_after_generate"],
                    stored_after_generate,
                )
                self.assertEqual(
                    payload["next_seed"],
                    str(next_seed),
                )


if __name__ == "__main__":
    unittest.main()
