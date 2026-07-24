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
from easyuse_anima.aio.generation_postprocess_stage import (
    AIOPostprocessStage,
    PostprocessRuntime,
)
from easyuse_anima.aio.generation_settings import (
    _aio_generation_config_from_dict,
)


def _request(
    *,
    postprocess_enabled: bool,
    intermediate_preview: bool = False,
) -> GenerationRequest:
    normalized = _normalize_aio_generation_settings(json.dumps({
        "postprocess": {"enabled": postprocess_enabled},
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
            model="model",
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
        latent="upscaled-latent",
        image="upscaled-image",
        width=128,
        height=192,
    )


class AIOPostprocessStageTests(unittest.TestCase):
    def test_disabled_stage_preserves_identity_dimensions_and_metadata(self):
        calls: list[tuple[object, dict[str, object]]] = []

        def run_postprocess(image, settings):
            calls.append((image, settings))
            return image, {
                "enabled": False,
                "width": 128,
                "height": 192,
            }

        def unexpected(*_args):
            self.fail("disabled Postprocess must not run enabled follow-up work")

        stage: GenerationStage = AIOPostprocessStage(
            runtime=PostprocessRuntime(
                run_postprocess=run_postprocess,
                as_bool=unexpected,
                image_size=unexpected,
                encode_image=unexpected,
            ),
            will_run_postprocess=False,
        )
        state = _state()
        request = _request(postprocess_enabled=False)

        stage.validate(request, {})
        stage.run(request, state)

        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0][0], "upscaled-image")
        self.assertFalse(calls[0][1]["enabled"])
        self.assertEqual(state.latent, "upscaled-latent")
        self.assertEqual(state.image, "upscaled-image")
        self.assertEqual((state.width, state.height), (128, 192))
        self.assertEqual(
            state.metadata,
            {
                "postprocess": {
                    "enabled": False,
                    "width": 128,
                    "height": 192,
                },
            },
        )

    def test_enabled_unchanged_updates_dimensions_without_latent_or_preview(self):
        trace: list[str] = []
        preview: list[tuple[str, object]] = []

        def run_postprocess(image, settings):
            trace.append("run_postprocess")
            self.assertEqual(image, "upscaled-image")
            self.assertTrue(settings["enabled"])
            return "fit-image", {
                "enabled": True,
                "width": 120,
                "height": 184,
                "fit": {"applied": False},
            }

        def image_size(image, fallback_width, fallback_height):
            trace.append("image_size")
            self.assertEqual(image, "fit-image")
            self.assertEqual((fallback_width, fallback_height), (128, 192))
            return 120, 184

        def as_bool(value, default):
            trace.append("as_bool")
            self.assertEqual((value, default), (False, False))
            return False

        def unexpected_encode(*_args):
            self.fail("unchanged Postprocess must not re-encode latent")

        state = _state()
        AIOPostprocessStage(
            runtime=PostprocessRuntime(
                run_postprocess=run_postprocess,
                as_bool=as_bool,
                image_size=image_size,
                encode_image=unexpected_encode,
            ),
            will_run_postprocess=True,
            add_preview=lambda name, image: preview.append((name, image)),
        ).run(
            _request(
                postprocess_enabled=True,
                intermediate_preview=True,
            ),
            state,
        )

        self.assertEqual(trace, ["run_postprocess", "image_size", "as_bool"])
        self.assertEqual(state.latent, "upscaled-latent")
        self.assertEqual(state.image, "fit-image")
        self.assertEqual((state.width, state.height), (120, 184))
        self.assertFalse(state.metadata["postprocess"]["fit"]["applied"])
        self.assertEqual(preview, [])

    def test_applied_stage_reencodes_then_publishes_preview(self):
        trace: list[str] = []
        preview: list[tuple[str, object]] = []

        def run_postprocess(image, settings):
            trace.append("run_postprocess")
            return "fit-image", {
                "enabled": True,
                "width": 96,
                "height": 144,
                "fit": {"applied": True},
            }

        def image_size(image, fallback_width, fallback_height):
            trace.append("image_size")
            self.assertEqual((image, fallback_width, fallback_height), (
                "fit-image",
                128,
                192,
            ))
            return 96, 144

        def as_bool(value, default):
            trace.append("as_bool")
            self.assertEqual((value, default), (True, False))
            return True

        def encode_image(vae, image):
            trace.append("encode_image")
            self.assertEqual((vae, image), ("vae", "fit-image"))
            return "fit-latent"

        state = _state()
        AIOPostprocessStage(
            runtime=PostprocessRuntime(
                run_postprocess=run_postprocess,
                as_bool=as_bool,
                image_size=image_size,
                encode_image=encode_image,
            ),
            will_run_postprocess=True,
            add_preview=lambda name, image: (
                trace.append(f"preview:{name}")
                or preview.append((name, image))
            ),
        ).run(
            _request(
                postprocess_enabled=True,
                intermediate_preview=True,
            ),
            state,
        )

        self.assertEqual(
            trace,
            [
                "run_postprocess",
                "image_size",
                "as_bool",
                "encode_image",
                "preview:postprocess",
            ],
        )
        self.assertEqual(state.latent, "fit-latent")
        self.assertEqual(state.image, "fit-image")
        self.assertEqual((state.width, state.height), (96, 144))
        self.assertTrue(state.metadata["postprocess"]["fit"]["applied"])
        self.assertEqual(preview, [("postprocess", "fit-image")])

    def test_validation_and_runtime_failures_do_not_publish_partial_state(self):
        request = _request(
            postprocess_enabled=True,
            intermediate_preview=True,
        )
        invalid_request = replace(
            request,
            config=replace(request.config, mode="img2img"),
        )

        def assert_unchanged(state):
            self.assertEqual(state.latent, "upscaled-latent")
            self.assertEqual(state.image, "upscaled-image")
            self.assertEqual((state.width, state.height), (128, 192))
            self.assertEqual(state.metadata, {})

        stage = AIOPostprocessStage(
            runtime=PostprocessRuntime(
                run_postprocess=lambda *_args: (_ for _ in ()).throw(
                    RuntimeError("postprocess failed")
                ),
                as_bool=lambda value, default: bool(value),
                image_size=lambda *_args: (96, 144),
                encode_image=lambda *_args: "fit-latent",
            ),
            will_run_postprocess=True,
        )
        state = _state()
        with self.assertRaisesRegex(RuntimeError, "supports txt2img only"):
            stage.validate(invalid_request, {})
        with self.assertRaisesRegex(RuntimeError, "postprocess failed"):
            stage.run(request, state)
        assert_unchanged(state)

        failure_cases = (
            (
                "size failed",
                lambda *_args: (_ for _ in ()).throw(
                    RuntimeError("size failed")
                ),
                lambda value, default: bool(value),
                lambda *_args: "fit-latent",
                None,
            ),
            (
                "normalize failed",
                lambda *_args: (96, 144),
                lambda *_args: (_ for _ in ()).throw(
                    RuntimeError("normalize failed")
                ),
                lambda *_args: "fit-latent",
                None,
            ),
            (
                "encode failed",
                lambda *_args: (96, 144),
                lambda value, default: bool(value),
                lambda *_args: (_ for _ in ()).throw(
                    RuntimeError("encode failed")
                ),
                None,
            ),
            (
                "preview failed",
                lambda *_args: (96, 144),
                lambda value, default: bool(value),
                lambda *_args: "fit-latent",
                lambda *_args: (_ for _ in ()).throw(
                    RuntimeError("preview failed")
                ),
            ),
        )
        for message, image_size, as_bool, encode_image, preview in failure_cases:
            with self.subTest(message=message):
                state = _state()
                stage = AIOPostprocessStage(
                    runtime=PostprocessRuntime(
                        run_postprocess=lambda *_args: (
                            "fit-image",
                            {
                                "enabled": True,
                                "fit": {"applied": True},
                            },
                        ),
                        as_bool=as_bool,
                        image_size=image_size,
                        encode_image=encode_image,
                    ),
                    will_run_postprocess=True,
                    add_preview=preview,
                )
                with self.assertRaisesRegex(RuntimeError, message):
                    stage.run(request, state)
                assert_unchanged(state)


if __name__ == "__main__":
    unittest.main()
