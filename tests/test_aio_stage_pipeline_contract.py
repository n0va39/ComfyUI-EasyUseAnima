from __future__ import annotations

import json
import unittest
from dataclasses import FrozenInstanceError
from pathlib import Path
from typing import cast

from easyuse_anima.aio.generation_pipeline import (
    AIO_GENERATION_STAGE_ORDER,
    ConditioningBundle,
    GenerationCapabilities,
    GenerationRequest,
    GenerationStage,
    GenerationState,
    PromptExecutionData,
    ResourceBundle,
    WorkflowContext,
)
from easyuse_anima.aio.generation_settings import AIOGenerationConfig


ROOT = Path(__file__).resolve().parents[1]
TRACE_FIXTURE = ROOT / "tests" / "fixtures" / "aio_legacy_execution_trace.v1.json"
EXPECTED_ALL = (
    "AIO_GENERATION_STAGE_ORDER",
    "ConditioningBundle",
    "GenerationCapabilities",
    "GenerationRequest",
    "GenerationStage",
    "GenerationState",
    "PromptExecutionData",
    "ResourceBundle",
    "WorkflowContext",
)


def _request() -> GenerationRequest:
    return GenerationRequest(
        config=cast(AIOGenerationConfig, object()),
        prompts=PromptExecutionData(
            prompt_data={"positive_prompt": "prompt"},
            positive_prompt="prompt",
            negative_prompt="negative",
            quality_tags="quality",
            quality_negative="quality negative",
            metadata_positive_prompt="metadata prompt",
            metadata_negative_prompt="metadata negative",
            use_anima_mod_guidance=True,
            use_negative_anima_mod_guidance=False,
        ),
        resources=ResourceBundle(
            base_model=object(),
            base_clip=object(),
            model_with_lora=object(),
            model=object(),
            clip=object(),
            vae=object(),
            applied_loras=({"name": "style.safetensors"},),
        ),
        conditioning=ConditioningBundle(
            positive=object(),
            negative=object(),
        ),
        workflow=WorkflowContext(
            input_context={"schema": "input-settings"},
            lora_stack=(),
            workflow_prompt=None,
            extra_pnginfo=None,
            unique_id="node-7",
            cache_scope="node-7",
        ),
    )


def _assert_ordered_subsequence(
    test: unittest.TestCase,
    actual: list[str],
    expected: tuple[str, ...],
) -> None:
    position = -1
    for checkpoint in expected:
        position = actual.index(checkpoint, position + 1)
    test.assertGreaterEqual(position, 0)


class AIOStagePipelineContractTests(unittest.TestCase):
    def test_stage_order_and_public_surface_are_exact(self):
        from easyuse_anima.aio import generation_pipeline

        self.assertEqual(
            AIO_GENERATION_STAGE_ORDER,
            (
                "first_pass",
                "highres",
                "detailer",
                "upscale",
                "postprocess",
                "save_output",
            ),
        )
        self.assertEqual(generation_pipeline.__all__, EXPECTED_ALL)

    def test_request_records_are_frozen_and_state_is_request_local(self):
        request = _request()
        with self.assertRaises(FrozenInstanceError):
            request.workflow = WorkflowContext(  # type: ignore[misc]
                input_context={},
                lora_stack=None,
                workflow_prompt=None,
                extra_pnginfo=None,
                unique_id=None,
                cache_scope="replacement",
            )
        with self.assertRaises(FrozenInstanceError):
            request.prompts.positive_prompt = "replacement"  # type: ignore[misc]

        first = GenerationState(latent=None, image=None, width=64, height=96)
        second = GenerationState(latent=None, image=None, width=64, height=96)
        first.metadata["first_pass"] = {"cache_hit": False}
        first.previews.append({"stage": "first_pass"})
        first.width = 128

        self.assertEqual(first.width, 128)
        self.assertEqual(second.width, 64)
        self.assertEqual(second.metadata, {})
        self.assertEqual(second.previews, [])

    def test_stage_protocol_is_structural_and_mutates_only_explicit_state(self):
        events: list[str] = []

        class FirstPassStage:
            name = "first_pass"

            def validate(
                self,
                request: GenerationRequest,
                capabilities: GenerationCapabilities,
            ) -> None:
                events.append(f"validate:{request.workflow.cache_scope}")
                events.append(f"capability:{capabilities['sampler']}")

            def run(
                self,
                request: GenerationRequest,
                state: GenerationState,
            ) -> None:
                events.append(f"run:{request.prompts.positive_prompt}")
                state.latent = "sampled-latent"
                state.metadata[self.name] = {"cache_hit": False}

        stage: GenerationStage = FirstPassStage()
        request = _request()
        state = GenerationState(latent=None, image=None, width=64, height=96)

        stage.validate(request, {"sampler": "comfy_ksampler"})
        stage.run(request, state)

        self.assertEqual(
            events,
            [
                "validate:node-7",
                "capability:comfy_ksampler",
                "run:prompt",
            ],
        )
        self.assertEqual(state.latent, "sampled-latent")
        self.assertEqual(state.metadata, {"first_pass": {"cache_hit": False}})

    def test_legacy_traces_preserve_stage_cleanup_and_save_order(self):
        fixture = json.loads(TRACE_FIXTURE.read_text(encoding="utf-8"))
        cases = fixture["cases"]
        checkpoints = (
            "load_resources",
            "apply_lora",
            "apply_model_patches",
            "encode_positive",
            "encode_negative",
            "get_cache",
            "sample",
            "decode",
            "run_highres",
            "run_detailer",
            "run_upscale",
            "run_postprocess",
            "cleanup:sample",
            "cleanup:model",
            "cleanup:lora",
            "save_comfy",
            "tag:final",
        )
        expected_metadata_stages = [
            "first_pass",
            "highres",
            "detailer",
            "upscale",
            "postprocess",
        ]

        self.assertEqual(
            sorted(cases),
            ["base_txt2img", "upscale_with_intermediate_preview"],
        )
        for name, case in cases.items():
            with self.subTest(case=name):
                _assert_ordered_subsequence(self, case["trace"], checkpoints)
                self.assertEqual(
                    list(case["result"]["metadata"]["stages"]),
                    expected_metadata_stages,
                )

        _assert_ordered_subsequence(
            self,
            cases["upscale_with_intermediate_preview"]["trace"],
            (
                "put_cache",
                "temp_preview:first_pass",
                "send_preview:first_pass",
                "run_highres",
                "run_detailer",
                "run_upscale",
                "temp_preview:upscale",
                "send_preview:upscale",
                "run_postprocess",
            ),
        )

    def test_through_upscale_are_the_only_connected_stages(self):
        legacy_source = (
            ROOT / "easyuse_anima" / "aio" / "legacy_generation.py"
        ).read_text(encoding="utf-8")
        first_pass_source = (
            ROOT / "easyuse_anima" / "aio" / "generation_first_pass.py"
        ).read_text(encoding="utf-8")
        highres_source = (
            ROOT / "easyuse_anima" / "aio" / "generation_highres.py"
        ).read_text(encoding="utf-8")
        detailer_source = (
            ROOT / "easyuse_anima" / "aio" / "generation_detailer_stage.py"
        ).read_text(encoding="utf-8")
        upscale_source = (
            ROOT / "easyuse_anima" / "aio" / "generation_upscale_stage.py"
        ).read_text(encoding="utf-8")
        canonical_node_source = (
            ROOT / "easyuse_anima" / "nodes" / "aio_nodes.py"
        ).read_text(encoding="utf-8")
        root_source = (ROOT / "nodes.py").read_text(encoding="utf-8")

        self.assertIn("AIOFirstPassStage", legacy_source)
        self.assertIn("GenerationRequest", legacy_source)
        self.assertIn("GenerationState", legacy_source)
        self.assertIn("GenerationRequest", first_pass_source)
        self.assertIn("GenerationState", first_pass_source)
        self.assertIn("AIOHighresStage", legacy_source)
        self.assertIn("GenerationRequest", highres_source)
        self.assertIn("GenerationState", highres_source)
        self.assertIn("AIODetailerStage", legacy_source)
        self.assertIn("GenerationRequest", detailer_source)
        self.assertIn("GenerationState", detailer_source)
        self.assertIn("AIOUpscaleStage", legacy_source)
        self.assertIn("GenerationRequest", upscale_source)
        self.assertIn("GenerationState", upscale_source)
        self.assertNotIn("generation_first_pass", canonical_node_source)
        self.assertNotIn("generation_first_pass", root_source)
        self.assertNotIn("generation_highres", canonical_node_source)
        self.assertNotIn("generation_highres", root_source)
        self.assertNotIn("generation_detailer_stage", canonical_node_source)
        self.assertNotIn("generation_detailer_stage", root_source)
        self.assertNotIn("generation_upscale_stage", canonical_node_source)
        self.assertNotIn("generation_upscale_stage", root_source)
        self.assertNotIn("AIOFirstPassStage", root_source)
        self.assertNotIn("AIOHighresStage", root_source)
        self.assertNotIn("AIODetailerStage", root_source)
        self.assertNotIn("AIOUpscaleStage", root_source)
        for later_stage in (
            "AIOPostprocessStage",
            "AIOSaveOutputStage",
        ):
            self.assertNotIn(later_stage, legacy_source)
            self.assertNotIn(later_stage, first_pass_source)
            self.assertNotIn(later_stage, highres_source)
            self.assertNotIn(later_stage, detailer_source)
            self.assertNotIn(later_stage, upscale_source)


if __name__ == "__main__":
    unittest.main()
