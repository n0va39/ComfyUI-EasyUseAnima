from __future__ import annotations

import json
import unittest
from dataclasses import replace

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
from easyuse_anima.aio.generation_upscale_stage import (
    AIOUpscaleStage,
    UpscaleRuntime,
)


def _request(
    *,
    upscale_enabled: bool,
    intermediate_preview: bool = False,
) -> GenerationRequest:
    normalized = _normalize_aio_generation_settings(json.dumps({
        "upscale": {"enabled": upscale_enabled},
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
            model="upscale-model",
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


def _state() -> GenerationState:
    return GenerationState(
        latent="detailer-latent",
        image="detailer-image",
        width=64,
        height=96,
    )


class AIOUpscaleStageTests(unittest.TestCase):
    def test_disabled_stage_preserves_identity_dimensions_and_metadata(self):
        calls: list[tuple[tuple[object, ...], dict[str, object]]] = []

        def run_upscale(*args, **kwargs):
            calls.append((args, kwargs))
            return args[5], {"enabled": False}

        def unexpected(*_args):
            self.fail("disabled Upscale must not run post-dispatch work")

        stage: GenerationStage = AIOUpscaleStage(
            runtime=UpscaleRuntime(
                run_upscale=run_upscale,
                image_size=unexpected,
                encode_image=unexpected,
            ),
            exclude_positive_quality=False,
            exclude_negative_quality=False,
        )
        state = _state()
        request = _request(upscale_enabled=False)

        stage.validate(request, {})
        stage.run(request, state)

        self.assertEqual(len(calls), 1)
        args, kwargs = calls[0]
        self.assertEqual(
            args[:6],
            (
                "upscale-model",
                "clip",
                "vae",
                "positive-conditioning",
                "negative-conditioning",
                "detailer-image",
            ),
        )
        self.assertEqual(args[6]["backend"], "comfy_ksampler")
        self.assertFalse(args[7]["enabled"])
        self.assertEqual(args[8:11], (
            "quality",
            "quality-negative",
            {"positive_prompt": "prompt"},
        ))
        self.assertEqual(
            kwargs,
            {
                "exclude_positive_quality": False,
                "exclude_negative_quality": False,
            },
        )
        self.assertEqual(state.latent, "detailer-latent")
        self.assertEqual(state.image, "detailer-image")
        self.assertEqual((state.width, state.height), (64, 96))
        self.assertEqual(state.metadata, {"upscale": {"enabled": False}})

    def test_enabled_stage_transfers_result_metadata_dimensions_latent_and_preview(self):
        trace: list[str] = []
        preview: list[tuple[str, object]] = []

        def run_upscale(*args, **kwargs):
            trace.append("run_upscale")
            self.assertEqual(
                args[:6],
                (
                    "upscale-model",
                    "clip",
                    "vae",
                    "positive-conditioning",
                    "negative-conditioning",
                    "detailer-image",
                ),
            )
            self.assertEqual(args[6]["backend"], "comfy_ksampler")
            self.assertTrue(args[7]["enabled"])
            self.assertEqual(args[8:11], (
                "quality",
                "quality-negative",
                {"positive_prompt": "prompt"},
            ))
            self.assertEqual(
                kwargs,
                {
                    "exclude_positive_quality": True,
                    "exclude_negative_quality": True,
                },
            )
            return "upscaled-image", {
                "enabled": True,
                "backend": "usdu",
                "width": 128,
                "height": 192,
            }

        def image_size(image, fallback_width, fallback_height):
            trace.append("image_size")
            self.assertEqual(image, "upscaled-image")
            self.assertEqual((fallback_width, fallback_height), (64, 96))
            return 128, 192

        def encode_image(vae, image):
            trace.append("encode_image")
            self.assertEqual((vae, image), ("vae", "upscaled-image"))
            return "upscaled-latent"

        state = _state()
        AIOUpscaleStage(
            runtime=UpscaleRuntime(
                run_upscale=run_upscale,
                image_size=image_size,
                encode_image=encode_image,
            ),
            exclude_positive_quality=True,
            exclude_negative_quality=True,
            add_preview=lambda name, image: (
                trace.append(f"preview:{name}")
                or preview.append((name, image))
            ),
        ).run(
            _request(
                upscale_enabled=True,
                intermediate_preview=True,
            ),
            state,
        )

        self.assertEqual(
            trace,
            ["run_upscale", "image_size", "encode_image", "preview:upscale"],
        )
        self.assertEqual(state.latent, "upscaled-latent")
        self.assertEqual(state.image, "upscaled-image")
        self.assertEqual((state.width, state.height), (128, 192))
        self.assertEqual(
            state.metadata["upscale"],
            {
                "enabled": True,
                "backend": "usdu",
                "width": 128,
                "height": 192,
            },
        )
        self.assertEqual(preview, [("upscale", "upscaled-image")])

    def test_preview_is_not_published_when_intermediate_preview_is_disabled(self):
        preview: list[tuple[str, object]] = []
        state = _state()

        AIOUpscaleStage(
            runtime=UpscaleRuntime(
                run_upscale=lambda *args, **_kwargs: (
                    "upscaled-image",
                    {"enabled": True},
                ),
                image_size=lambda *_args: (128, 192),
                encode_image=lambda *_args: "upscaled-latent",
            ),
            exclude_positive_quality=False,
            exclude_negative_quality=False,
            add_preview=lambda name, image: preview.append((name, image)),
        ).run(
            _request(upscale_enabled=True),
            state,
        )

        self.assertEqual(preview, [])
        self.assertEqual(state.latent, "upscaled-latent")
        self.assertEqual(state.image, "upscaled-image")

    def test_validation_and_runtime_failures_do_not_publish_partial_state(self):
        request = _request(
            upscale_enabled=True,
            intermediate_preview=True,
        )
        invalid_request = replace(
            request,
            config=replace(request.config, mode="img2img"),
        )

        def assert_unchanged(state):
            self.assertEqual(state.latent, "detailer-latent")
            self.assertEqual(state.image, "detailer-image")
            self.assertEqual((state.width, state.height), (64, 96))
            self.assertEqual(state.metadata, {})

        stage = AIOUpscaleStage(
            runtime=UpscaleRuntime(
                run_upscale=lambda *_args, **_kwargs: (_ for _ in ()).throw(
                    RuntimeError("upscale failed")
                ),
                image_size=lambda *_args: (128, 192),
                encode_image=lambda *_args: "upscaled-latent",
            ),
            exclude_positive_quality=False,
            exclude_negative_quality=False,
        )
        state = _state()
        with self.assertRaisesRegex(RuntimeError, "supports txt2img only"):
            stage.validate(invalid_request, {})
        with self.assertRaisesRegex(RuntimeError, "upscale failed"):
            stage.run(request, state)
        assert_unchanged(state)

        failure_cases = (
            (
                "size failed",
                lambda *_args: (_ for _ in ()).throw(
                    RuntimeError("size failed")
                ),
                lambda *_args: "upscaled-latent",
                None,
            ),
            (
                "encode failed",
                lambda *_args: (128, 192),
                lambda *_args: (_ for _ in ()).throw(
                    RuntimeError("encode failed")
                ),
                None,
            ),
            (
                "preview failed",
                lambda *_args: (128, 192),
                lambda *_args: "upscaled-latent",
                lambda *_args: (_ for _ in ()).throw(
                    RuntimeError("preview failed")
                ),
            ),
        )
        for message, image_size, encode_image, preview in failure_cases:
            with self.subTest(message=message):
                state = _state()
                stage = AIOUpscaleStage(
                    runtime=UpscaleRuntime(
                        run_upscale=lambda *_args, **_kwargs: (
                            "upscaled-image",
                            {"enabled": True},
                        ),
                        image_size=image_size,
                        encode_image=encode_image,
                    ),
                    exclude_positive_quality=False,
                    exclude_negative_quality=False,
                    add_preview=preview,
                )
                with self.assertRaisesRegex(RuntimeError, message):
                    stage.run(request, state)
                assert_unchanged(state)


if __name__ == "__main__":
    unittest.main()
