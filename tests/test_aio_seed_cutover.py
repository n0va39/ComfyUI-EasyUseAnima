from __future__ import annotations

import unittest
from contextlib import contextmanager
from unittest.mock import patch

from easyuse_anima.nodes import aio_nodes
from easyuse_anima.nodes.seed_adapters import AioSeedExecution


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


if __name__ == "__main__":
    unittest.main()
