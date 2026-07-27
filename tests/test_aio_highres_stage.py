from __future__ import annotations

import json
import unittest
from dataclasses import replace

from easyuse_anima.aio.generation_highres import (
    AIOHighresStage,
    HighresRuntime,
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
    highres_enabled: bool,
    intermediate_preview: bool = False,
    negpip_mode: str = "off",
) -> GenerationRequest:
    normalized = _normalize_aio_generation_settings(json.dumps({
        "negpip": {"mode": negpip_mode},
        "highres": {"enabled": highres_enabled},
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
            model="highres-model",
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


class AIOHighresStageTests(unittest.TestCase):
    def test_turbo_uses_effective_cfg_one_for_sampler_and_highres_copies(self):
        observed: list[tuple[float, float]] = []
        request = _request(highres_enabled=True, negpip_mode="turbo")
        saved_sampler_cfg = request.config.sampler.to_dict()["cfg"]
        saved_highres_cfg = request.config.highres.to_dict()["cfg"]

        def run_highres(*args):
            observed.append((args[9]["cfg"], args[10]["cfg"]))
            return args[6], args[5], args[7], args[8], {"enabled": True}

        AIOHighresStage(
            runtime=HighresRuntime(run_highres=run_highres),
            use_mod_guidance=False,
        ).run(
            request,
            GenerationState(
                latent="first-latent",
                image="first-image",
                width=64,
                height=96,
            ),
        )

        self.assertEqual(observed, [(1.0, 1.0)])
        self.assertEqual(request.config.sampler.to_dict()["cfg"], saved_sampler_cfg)
        self.assertEqual(request.config.highres.to_dict()["cfg"], saved_highres_cfg)

    def test_disabled_stage_preserves_identity_dimensions_and_metadata(self):
        calls: list[tuple[object, ...]] = []
        image = object()
        latent = object()

        def run_highres(*args):
            calls.append(args)
            return latent, image, 64, 96, {"enabled": False}

        stage: GenerationStage = AIOHighresStage(
            runtime=HighresRuntime(run_highres=run_highres),
            use_mod_guidance=False,
        )
        state = GenerationState(
            latent=latent,
            image=image,
            width=64,
            height=96,
        )
        request = _request(highres_enabled=False)

        stage.validate(request, {"sampler_backend": ""})
        stage.run(request, state)

        self.assertEqual(len(calls), 1)
        self.assertIs(calls[0][5], image)
        self.assertIs(calls[0][6], latent)
        self.assertFalse(calls[0][10]["enabled"])
        self.assertIs(state.latent, latent)
        self.assertIs(state.image, image)
        self.assertEqual((state.width, state.height), (64, 96))
        self.assertEqual(state.metadata, {"highres": {"enabled": False}})

    def test_enabled_stage_transfers_arguments_result_metadata_and_preview(self):
        trace: list[str] = []
        preview: list[tuple[str, object]] = []

        def run_highres(*args):
            trace.append("run_highres")
            self.assertEqual(args[:9], (
                "highres-model",
                "clip",
                "vae",
                "positive-conditioning",
                "negative-conditioning",
                "first-image",
                "first-latent",
                64,
                96,
            ))
            self.assertEqual(args[9]["backend"], "comfy_ksampler")
            self.assertTrue(args[10]["enabled"])
            self.assertEqual(args[11]["mode"], "prompt_data")
            self.assertEqual(args[12:], (True, "quality", "quality-negative"))
            return (
                "highres-latent",
                "highres-image",
                128,
                192,
                {
                    "enabled": True,
                    "width": 128,
                    "height": 192,
                    "sampler": {"backend": "comfy_ksampler"},
                },
            )

        state = GenerationState(
            latent="first-latent",
            image="first-image",
            width=64,
            height=96,
        )
        AIOHighresStage(
            runtime=HighresRuntime(run_highres=run_highres),
            use_mod_guidance=True,
            add_preview=lambda name, image: (
                trace.append(f"preview:{name}")
                or preview.append((name, image))
            ),
            preview_before_detailer=True,
        ).run(
            _request(
                highres_enabled=True,
                intermediate_preview=True,
            ),
            state,
        )

        self.assertEqual(trace, ["run_highres", "preview:highres"])
        self.assertEqual(state.latent, "highres-latent")
        self.assertEqual(state.image, "highres-image")
        self.assertEqual((state.width, state.height), (128, 192))
        self.assertEqual(
            state.metadata["highres"],
            {
                "enabled": True,
                "width": 128,
                "height": 192,
                "sampler": {"backend": "comfy_ksampler"},
            },
        )
        self.assertEqual(preview, [("highres", "highres-image")])

    def test_preview_requires_sampler_metadata_and_detailer_boundary(self):
        preview: list[tuple[str, object]] = []

        def execute(metadata, *, before_detailer):
            state = GenerationState(
                latent="first-latent",
                image="first-image",
                width=64,
                height=96,
            )
            AIOHighresStage(
                runtime=HighresRuntime(
                    run_highres=lambda *_args: (
                        "highres-latent",
                        "highres-image",
                        128,
                        192,
                        metadata,
                    )
                ),
                use_mod_guidance=False,
                add_preview=lambda name, image: preview.append((name, image)),
                preview_before_detailer=before_detailer,
            ).run(
                _request(
                    highres_enabled=True,
                    intermediate_preview=True,
                ),
                state,
            )

        execute({"enabled": True}, before_detailer=True)
        execute(
            {"enabled": True, "sampler": {"backend": "comfy_ksampler"}},
            before_detailer=False,
        )
        self.assertEqual(preview, [])

    def test_validation_and_runner_failure_do_not_publish_partial_state(self):
        request = _request(highres_enabled=True)
        invalid_request = replace(
            request,
            config=replace(request.config, mode="img2img"),
        )
        stage = AIOHighresStage(
            runtime=HighresRuntime(
                run_highres=lambda *_args: (_ for _ in ()).throw(
                    RuntimeError("highres failed")
                )
            ),
            use_mod_guidance=False,
        )
        state = GenerationState(
            latent="first-latent",
            image="first-image",
            width=64,
            height=96,
        )

        with self.assertRaisesRegex(RuntimeError, "supports txt2img only"):
            stage.validate(invalid_request, {})
        with self.assertRaisesRegex(RuntimeError, "highres failed"):
            stage.run(request, state)

        self.assertEqual(state.latent, "first-latent")
        self.assertEqual(state.image, "first-image")
        self.assertEqual((state.width, state.height), (64, 96))
        self.assertEqual(state.metadata, {})


if __name__ == "__main__":
    unittest.main()
