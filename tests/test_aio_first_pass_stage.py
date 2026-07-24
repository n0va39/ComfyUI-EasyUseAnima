from __future__ import annotations

import json
import unittest
from dataclasses import replace

from easyuse_anima.aio.generation_first_pass import (
    AIOFirstPassStage,
    FirstPassRuntime,
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


def _request(*, intermediate_preview: bool = False) -> GenerationRequest:
    normalized = _normalize_aio_generation_settings(json.dumps({
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
            use_negative_anima_mod_guidance=False,
        ),
        resources=ResourceBundle(
            base_model="base-model",
            base_clip="base-clip",
            model_with_lora="lora-model",
            model="sample-model",
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


def _unexpected(*_args, **_kwargs):
    raise AssertionError("unexpected first-pass runtime call")


class AIOFirstPassStageTests(unittest.TestCase):
    def test_cache_miss_samples_decodes_stores_metadata_and_preview_in_order(self):
        trace: list[str] = []
        preview: list[tuple[str, object]] = []

        def sample(*args):
            trace.append("sample")
            self.assertEqual(
                args,
                (
                    "sample-model",
                    "clip",
                    "positive-conditioning",
                    "negative-conditioning",
                    "empty-latent",
                    args[5],
                    args[6],
                    True,
                    "quality",
                    "",
                ),
            )
            self.assertEqual(args[5]["backend"], "comfy_ksampler")
            self.assertEqual(args[6]["mode"], "prompt_data")
            return "sampled-latent"

        runtime = FirstPassRuntime(
            get_cache=lambda key: trace.append(f"get:{key}") or None,
            put_cache=lambda key, latent, image: trace.append(
                f"put:{key}:{latent}:{image}"
            ),
            generate_empty_latent=lambda width, height: (
                trace.append(f"empty:{width}x{height}") or "empty-latent"
            ),
            sample_latent=sample,
            decode_latent=lambda vae, latent: (
                trace.append(f"decode:{vae}:{latent}") or "decoded-image"
            ),
            resize_image=lambda image, width, height, method: (
                trace.append(f"resize:{image}:{width}x{height}:{method}")
                or (image, False)
            ),
            encode_image=_unexpected,
        )
        stage: GenerationStage = AIOFirstPassStage(
            runtime=runtime,
            cache_key="cache-key",
            use_mod_guidance=True,
            add_preview=lambda name, image: (
                trace.append(f"preview:{name}")
                or preview.append((name, image))
            ),
        )
        request = _request(intermediate_preview=True)
        state = GenerationState(
            latent=None,
            image=None,
            width=64,
            height=96,
        )

        stage.validate(request, {"sampler_backend": "comfy_ksampler"})
        stage.run(request, state)

        self.assertEqual(
            trace,
            [
                "get:cache-key",
                "empty:64x96",
                "sample",
                "decode:vae:sampled-latent",
                "resize:decoded-image:64x96:bicubic",
                "put:cache-key:sampled-latent:decoded-image",
                "preview:first_pass",
            ],
        )
        self.assertEqual(state.latent, "sampled-latent")
        self.assertEqual(state.image, "decoded-image")
        self.assertEqual((state.width, state.height), (64, 96))
        self.assertEqual(state.metadata, {"first_pass": {"cache_hit": False}})
        self.assertEqual(preview, [("first_pass", "decoded-image")])

    def test_cache_hit_is_no_sampling_path_and_does_not_republish(self):
        trace: list[str] = []
        runtime = FirstPassRuntime(
            get_cache=lambda key: (
                trace.append(f"get:{key}")
                or ("cached-latent", "cached-image")
            ),
            put_cache=_unexpected,
            generate_empty_latent=_unexpected,
            sample_latent=_unexpected,
            decode_latent=_unexpected,
            resize_image=lambda image, width, height, method: (
                trace.append(f"resize:{image}:{width}x{height}:{method}")
                or (image, False)
            ),
            encode_image=_unexpected,
        )
        state = GenerationState(
            latent=None,
            image=None,
            width=64,
            height=96,
        )

        AIOFirstPassStage(
            runtime=runtime,
            cache_key="cache-key",
            use_mod_guidance=False,
        ).run(_request(), state)

        self.assertEqual(
            trace,
            [
                "get:cache-key",
                "resize:cached-image:64x96:bicubic",
            ],
        )
        self.assertEqual(state.latent, "cached-latent")
        self.assertEqual(state.image, "cached-image")
        self.assertEqual(state.metadata, {"first_pass": {"cache_hit": True}})

    def test_resize_reencodes_and_cache_write_failure_remains_non_fatal(self):
        trace: list[str] = []

        def fail_put(key, latent, image):
            trace.append(f"put:{key}:{latent}:{image}")
            raise OSError("cache unavailable")

        runtime = FirstPassRuntime(
            get_cache=lambda key: (
                trace.append(f"get:{key}")
                or ("cached-latent", "cached-image")
            ),
            put_cache=fail_put,
            generate_empty_latent=_unexpected,
            sample_latent=_unexpected,
            decode_latent=_unexpected,
            resize_image=lambda image, width, height, method: (
                trace.append(f"resize:{image}:{width}x{height}:{method}")
                or ("resized-image", True)
            ),
            encode_image=lambda vae, image: (
                trace.append(f"encode:{vae}:{image}") or "resized-latent"
            ),
        )
        state = GenerationState(
            latent=None,
            image=None,
            width=64,
            height=96,
        )

        AIOFirstPassStage(
            runtime=runtime,
            cache_key="cache-key",
            use_mod_guidance=False,
        ).run(_request(), state)

        self.assertEqual(
            trace,
            [
                "get:cache-key",
                "resize:cached-image:64x96:bicubic",
                "encode:vae:resized-image",
                "put:cache-key:resized-latent:resized-image",
            ],
        )
        self.assertEqual(state.latent, "resized-latent")
        self.assertEqual(state.image, "resized-image")
        self.assertEqual(state.metadata, {"first_pass": {"cache_hit": True}})

    def test_validation_rejects_unsupported_mode_before_runtime_calls(self):
        request = _request()
        request = replace(
            request,
            config=replace(request.config, mode="img2img"),
        )
        stage = AIOFirstPassStage(
            runtime=FirstPassRuntime(
                get_cache=_unexpected,
                put_cache=_unexpected,
                generate_empty_latent=_unexpected,
                sample_latent=_unexpected,
                decode_latent=_unexpected,
                resize_image=_unexpected,
                encode_image=_unexpected,
            ),
            cache_key="cache-key",
            use_mod_guidance=False,
        )

        with self.assertRaisesRegex(RuntimeError, "supports txt2img only"):
            stage.validate(request, {})

    def test_sampling_exception_propagates_without_partial_state_publication(self):
        def fail_sample(*_args):
            raise RuntimeError("sample failed")

        stage = AIOFirstPassStage(
            runtime=FirstPassRuntime(
                get_cache=lambda _key: None,
                put_cache=_unexpected,
                generate_empty_latent=lambda _width, _height: "empty-latent",
                sample_latent=fail_sample,
                decode_latent=_unexpected,
                resize_image=_unexpected,
                encode_image=_unexpected,
            ),
            cache_key="cache-key",
            use_mod_guidance=False,
        )
        state = GenerationState(
            latent=None,
            image=None,
            width=64,
            height=96,
        )

        with self.assertRaisesRegex(RuntimeError, "sample failed"):
            stage.run(_request(), state)

        self.assertIsNone(state.latent)
        self.assertIsNone(state.image)
        self.assertEqual(state.metadata, {})


if __name__ == "__main__":
    unittest.main()
