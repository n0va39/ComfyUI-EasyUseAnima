from __future__ import annotations

import json
import unittest
from dataclasses import replace

from easyuse_anima.aio.generation_detailer_stage import (
    AIODetailerStage,
    DetailerRuntime,
)
from easyuse_anima.aio.generation_normalization import (
    _normalize_aio_generation_settings,
)
from easyuse_anima.aio.generation_pipeline import (
    ConditioningBundle,
    GenerationRequest,
    GenerationStage,
    GenerationState,
    PromptExecutionData,
    ResourceBundle,
    WorkflowContext,
)
from easyuse_anima.aio.generation_settings import (
    _aio_generation_config_from_dict,
)


def _request(
    *,
    detailer_enabled: bool,
    intermediate_preview: bool = False,
    negpip_mode: str = "off",
) -> GenerationRequest:
    normalized = _normalize_aio_generation_settings(json.dumps({
        "negpip": {"mode": negpip_mode},
        "detailer": {"enabled": detailer_enabled},
        "preview": {"intermediate_images": intermediate_preview},
    }))
    return GenerationRequest(
        config=_aio_generation_config_from_dict(normalized),
        prompts=PromptExecutionData(
            prompt_data={"positive_prompt": "prompt"},
            positive_prompt="prompt",
            negative_prompt="negative",
            quality_tags="quality",
            quality_negative="quality-negative",
            metadata_positive_prompt="metadata prompt",
            metadata_negative_prompt="metadata negative",
            use_anima_mod_guidance=True,
            use_negative_anima_mod_guidance=True,
        ),
        resources=ResourceBundle(
            base_model="base-model",
            base_clip="base-clip",
            model_with_lora="lora-model",
            model="detailer-model",
            clip="clip",
            vae="vae",
            applied_loras=({"name": "style.safetensors"},),
        ),
        conditioning=ConditioningBundle(
            positive="positive-conditioning",
            negative="negative-conditioning",
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


class AIODetailerStageTests(unittest.TestCase):
    def test_turbo_uses_effective_cfg_one_for_sampler_and_detailer_targets(self):
        observed: list[tuple[float, set[float]]] = []
        request = _request(detailer_enabled=True, negpip_mode="turbo")
        saved_detailer = request.config.detailer.to_dict()

        def run_detailer(*args):
            target_cfgs = {
                target["cfg"]
                for target in args[7].values()
                if isinstance(target, dict) and "cfg" in target
            }
            observed.append((args[6]["cfg"], target_cfgs))
            return args[5], {"enabled": True}

        AIODetailerStage(
            runtime=DetailerRuntime(
                run_detailer=run_detailer,
                image_size=lambda *_args: (64, 96),
            ),
        ).run(
            request,
            GenerationState(
                latent="highres-latent",
                image="highres-image",
                width=64,
                height=96,
            ),
        )

        self.assertEqual(observed, [(1.0, {1.0})])
        self.assertEqual(request.config.detailer.to_dict(), saved_detailer)

    def test_disabled_stage_preserves_identity_dimensions_and_metadata(self):
        calls: list[tuple[object, ...]] = []
        image = object()
        latent = object()

        def run_detailer(*args):
            calls.append(args)
            return image, {"enabled": False}

        def unexpected_image_size(*_args):
            self.fail("disabled Detailer must not inspect output dimensions")

        stage: GenerationStage = AIODetailerStage(
            runtime=DetailerRuntime(
                run_detailer=run_detailer,
                image_size=unexpected_image_size,
            ),
        )
        state = GenerationState(
            latent=latent,
            image=image,
            width=64,
            height=96,
        )
        request = _request(detailer_enabled=False)

        stage.validate(request, {})
        stage.run(request, state)

        self.assertEqual(len(calls), 1)
        self.assertEqual(
            calls[0][:6],
            (
                "detailer-model",
                "clip",
                "vae",
                "positive-conditioning",
                "negative-conditioning",
                image,
            ),
        )
        self.assertEqual(calls[0][6]["backend"], "comfy_ksampler")
        self.assertFalse(calls[0][7]["enabled"])
        self.assertIsNone(calls[0][8])
        self.assertIs(state.latent, latent)
        self.assertIs(state.image, image)
        self.assertEqual((state.width, state.height), (64, 96))
        self.assertEqual(state.metadata, {"detailer": {"enabled": False}})

    def test_enabled_stage_transfers_result_metadata_dimensions_and_preview(self):
        trace: list[str] = []
        preview: list[tuple[str, object]] = []

        def run_detailer(*args):
            trace.append("run_detailer")
            self.assertEqual(
                args[:6],
                (
                    "detailer-model",
                    "clip",
                    "vae",
                    "positive-conditioning",
                    "negative-conditioning",
                    "highres-image",
                ),
            )
            self.assertEqual(args[6]["backend"], "comfy_ksampler")
            self.assertTrue(args[7]["enabled"])
            callback = args[8]
            self.assertIsNotNone(callback)
            callback("detailer_face", "detailer-image")
            return "detailer-image", {
                "enabled": True,
                "order": ["face"],
                "targets": {"face": {"enabled": True}},
            }

        def image_size(image, fallback_width, fallback_height):
            trace.append("image_size")
            self.assertEqual(image, "detailer-image")
            self.assertEqual((fallback_width, fallback_height), (64, 96))
            return 128, 192

        state = GenerationState(
            latent="highres-latent",
            image="highres-image",
            width=64,
            height=96,
        )
        AIODetailerStage(
            runtime=DetailerRuntime(
                run_detailer=run_detailer,
                image_size=image_size,
            ),
            add_preview=lambda name, image: (
                trace.append(f"preview:{name}")
                or preview.append((name, image))
            ),
        ).run(
            _request(
                detailer_enabled=True,
                intermediate_preview=True,
            ),
            state,
        )

        self.assertEqual(
            trace,
            ["run_detailer", "preview:detailer_face", "image_size"],
        )
        self.assertEqual(state.latent, "highres-latent")
        self.assertEqual(state.image, "detailer-image")
        self.assertEqual((state.width, state.height), (128, 192))
        self.assertEqual(
            state.metadata["detailer"],
            {
                "enabled": True,
                "order": ["face"],
                "targets": {"face": {"enabled": True}},
            },
        )
        self.assertEqual(preview, [("detailer_face", "detailer-image")])

    def test_preview_is_not_injected_when_intermediate_preview_is_disabled(self):
        received_callbacks: list[object] = []
        preview: list[tuple[str, object]] = []

        def run_detailer(*args):
            received_callbacks.append(args[8])
            return args[5], {"enabled": False}

        state = GenerationState(
            latent="highres-latent",
            image="highres-image",
            width=64,
            height=96,
        )
        AIODetailerStage(
            runtime=DetailerRuntime(
                run_detailer=run_detailer,
                image_size=lambda *_args: (128, 192),
            ),
            add_preview=lambda name, image: preview.append((name, image)),
        ).run(
            _request(detailer_enabled=False),
            state,
        )

        self.assertEqual(received_callbacks, [None])
        self.assertEqual(preview, [])

    def test_validation_and_runtime_failures_do_not_publish_partial_state(self):
        request = _request(detailer_enabled=True)
        invalid_request = replace(
            request,
            config=replace(request.config, mode="img2img"),
        )
        stage = AIODetailerStage(
            runtime=DetailerRuntime(
                run_detailer=lambda *_args: (_ for _ in ()).throw(
                    RuntimeError("detailer failed")
                ),
                image_size=lambda *_args: (128, 192),
            ),
        )
        state = GenerationState(
            latent="highres-latent",
            image="highres-image",
            width=64,
            height=96,
        )

        with self.assertRaisesRegex(RuntimeError, "supports txt2img only"):
            stage.validate(invalid_request, {})
        with self.assertRaisesRegex(RuntimeError, "detailer failed"):
            stage.run(request, state)

        self.assertEqual(state.latent, "highres-latent")
        self.assertEqual(state.image, "highres-image")
        self.assertEqual((state.width, state.height), (64, 96))
        self.assertEqual(state.metadata, {})


if __name__ == "__main__":
    unittest.main()
