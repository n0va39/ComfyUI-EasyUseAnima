from __future__ import annotations

import copy
import inspect
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

import nodes
from easyuse_anima.aio import legacy_generation
from tests.test_node_contracts import _loaded_package_entrypoint

ROOT = Path(__file__).resolve().parents[1]
TRACE_FIXTURE_PATH = ROOT / "tests" / "fixtures" / "aio_legacy_execution_trace.v1.json"


class _Token:
    def __init__(self, name: str):
        self.name = name


class AIOGeneratorLegacyMoveTests(unittest.TestCase):
    def test_private_implementation_aliases_are_canonical_in_both_import_modes(self):
        self.assertEqual(legacy_generation.__all__, ())
        self.assertIs(
            nodes._bind_aio_legacy_generation_runtime,
            legacy_generation._bind_aio_legacy_generation_runtime,
        )
        self.assertIs(
            nodes._run_aio_legacy_generation,
            legacy_generation._run_aio_legacy_generation,
        )

        with _loaded_package_entrypoint() as (package_entrypoint, package_nodes):
            canonical_module = sys.modules[
                f"{package_entrypoint.__name__}.easyuse_anima.aio.legacy_generation"
            ]
            self.assertIs(
                package_nodes._bind_aio_legacy_generation_runtime,
                canonical_module._bind_aio_legacy_generation_runtime,
            )
            self.assertIs(
                package_nodes._run_aio_legacy_generation,
                canonical_module._run_aio_legacy_generation,
            )

    def test_root_generate_keeps_signature_and_forwards_without_adaptation(self):
        signature = inspect.signature(nodes.EasyUseAnimaAIOGenerator.generate)
        self.assertEqual(
            list(signature.parameters),
            [
                "self",
                "easy_use_anima_input",
                "generation_settings",
                "lora_stack",
                "workflow_prompt",
                "extra_pnginfo",
                "unique_id",
            ],
        )
        self.assertIsNone(signature.parameters["generation_settings"].default)
        for name in (
            "lora_stack",
            "workflow_prompt",
            "extra_pnginfo",
            "unique_id",
        ):
            self.assertIsNone(signature.parameters[name].default)

        generator = nodes.EasyUseAnimaAIOGenerator()
        forwarded = object()
        with patch.object(
            nodes,
            "_run_aio_legacy_generation",
            return_value=forwarded,
        ) as run:
            result = generator.generate(
                "input",
                {"settings": True},
                "lora",
                "workflow",
                "pnginfo",
                "node-id",
            )

        self.assertIs(result, forwarded)
        run.assert_called_once_with(
            generator,
            "input",
            {"settings": True},
            "lora",
            "workflow",
            "pnginfo",
            "node-id",
        )

    def test_execution_trace_matches_move_boundary_fixture(self):
        fixture = json.loads(TRACE_FIXTURE_PATH.read_text(encoding="utf-8"))

        self.assertEqual(
            fixture,
            {
                "schema": "easyuse_anima_aio_legacy_execution_trace",
                "version": 1,
                "cases": fixture["cases"],
            },
        )
        actual = {
            "base_txt2img": self._execute_case(
                upscale_enabled=False,
                intermediate_preview=False,
                unique_id=None,
            ),
            "upscale_with_intermediate_preview": self._execute_case(
                upscale_enabled=True,
                intermediate_preview=True,
                unique_id="node-7",
            ),
        }
        self.assertEqual(actual, fixture["cases"])

    def _execute_case(
        self,
        *,
        upscale_enabled: bool,
        intermediate_preview: bool,
        unique_id,
    ) -> dict:
        trace: list[str] = []
        generator = nodes.EasyUseAnimaAIOGenerator()
        context = {
            "prompt_data": {"positive_prompt": "prompt"},
            "resource_info": {"unet_name": "model.safetensors"},
            "input_settings": {"schema": "input-settings"},
        }
        settings = {
            "mode": "txt2img",
            "sampler": {"seed": "random", "backend": "comfy_ksampler"},
            "artist_mix": {
                "mode": "sequential",
                "start_percent": 0.0,
                "strength_scale": 1.0,
                "style_gain": 1.0,
                "rms_scale_cap": 1.0,
                "exact_top_k": 0,
                "cluster_count": 1,
                "dominant_isolation": False,
                "dominant_threshold": 0.0,
            },
            "mod_guidance": {"profile": "off", "mode": "auto"},
            "highres": {"enabled": False},
            "detailer": {},
            "upscale": {"enabled": upscale_enabled},
            "postprocess": {"enabled": False},
            "preview": {"intermediate_images": intermediate_preview},
            "save": {
                "enabled": True,
                "backend": "comfy",
                "filename_prefix": "Anima",
            },
        }

        base_model = _Token("base")
        lora_model = _Token("lora")
        patched_model = _Token("model")
        sample_model = _Token("sample")
        base_clip = _Token("base_clip")
        clip = _Token("clip")
        vae = _Token("vae")
        model_names = {
            id(lora_model): "lora",
            id(patched_model): "model",
            id(sample_model): "sample",
        }

        def phase(name, result):
            def run(*args, **kwargs):
                trace.append(name)
                return result

            return run

        def require(value):
            trace.append("require_input")
            self.assertIs(value, context)
            return value

        def normalize_settings(value):
            trace.append("normalize_settings")
            self.assertEqual(value, "settings-json")
            return copy.deepcopy(settings)

        def resolve_seed(value):
            trace.append("resolve_seed")
            self.assertEqual(value, "random")
            return 17

        def load_resources(value):
            trace.append("load_resources")
            self.assertIs(value, context)
            return base_model, base_clip, vae

        def apply_lora(model, source_clip, stack):
            trace.append("apply_lora")
            self.assertIs(model, base_model)
            self.assertIs(source_clip, base_clip)
            self.assertEqual(stack, "lora-stack")
            return lora_model, clip, [{"name": "style.safetensors"}]

        def apply_model_patches(model, normalized_settings):
            trace.append("apply_model_patches")
            self.assertIs(model, lora_model)
            self.assertEqual(normalized_settings["sampler"]["seed"], 17)
            return patched_model

        def advanced_outputs(prompt_data):
            trace.append("advanced_outputs")
            return (
                "positive",
                "negative",
                "quality",
                "quality-neg",
                False,
                False,
                "metadata-positive",
                "metadata-negative",
                64,
                96,
            )

        def apply_spectrum_model(model, source_clip, positive, sampler):
            trace.append("apply_spectrum_model_patches")
            self.assertIs(model, patched_model)
            return sample_model

        class _Random:
            @staticmethod
            def getrandbits(bits):
                trace.append("random_run_id")
                self.assertEqual(bits, 64)
                return 0x1234

        def cache_key(**kwargs):
            scope = kwargs["cache_scope"]
            if unique_id is None:
                self.assertEqual(scope, str(id(generator)))
                scope = "generator-id"
            trace.append(f"cache_key:{scope}")
            return "cache-key"

        def run_highres(
            model,
            source_clip,
            source_vae,
            positive,
            negative,
            image,
            latent,
            width,
            height,
            *args,
        ):
            trace.append("run_highres")
            return latent, image, width, height, {"enabled": False}

        def run_detailer(*args):
            trace.append("run_detailer")
            return args[5], {"enabled": False}

        def run_upscale(*args, **kwargs):
            trace.append("run_upscale")
            if upscale_enabled:
                return "upscaled-image", {"enabled": True, "backend": "stub"}
            return args[5], {"enabled": False}

        def run_postprocess(image, postprocess):
            trace.append("run_postprocess")
            return image, {"enabled": False}

        def image_size(image, fallback_width, fallback_height):
            trace.append("image_size")
            self.assertEqual(image, "upscaled-image")
            return 128, 192

        def encode_image(source_vae, image):
            trace.append("encode_upscaled_image")
            self.assertIs(source_vae, vae)
            return "upscaled-latent"

        def cleanup(model, original_model):
            trace.append(f"cleanup:{model_names[id(model)]}")
            self.assertIs(original_model, base_model)

        def save_temp(image, stage, **kwargs):
            trace.append(f"temp_preview:{stage}")
            return [{"filename": f"{stage}.png", "stage": stage, "type": "temp"}]

        def send_preview(node_id, run_id, stage, images):
            trace.append(f"send_preview:{stage}")

        def save_prefix(save_settings):
            trace.append("save_prefix")
            return save_settings["filename_prefix"]

        def save_comfy(image, prefix, **kwargs):
            trace.append("save_comfy")
            self.assertTrue(all(item.startswith("cleanup:") for item in trace[-5:-2]))
            return {
                "ui": {
                    "images": [
                        {"filename": "final.png", "subfolder": "", "type": "output"}
                    ]
                }
            }

        def tag_images(images, stage, *, width, height):
            trace.append(f"tag:{stage}")
            return [
                {**item, "stage": stage, "width": width, "height": height}
                for item in images
            ]

        def unexpected(*args, **kwargs):
            self.fail("standalone Mod Guidance must remain lazy for the fixture cases")

        with patch.multiple(
            nodes,
            _require_easy_use_anima_input=require,
            _normalize_aio_generation_settings=normalize_settings,
            _resolve_aio_runtime_seed=resolve_seed,
            _load_aio_resources_from_input_context=load_resources,
            _apply_aio_lora_stack=apply_lora,
            _apply_aio_model_patches=apply_model_patches,
            _normalize_prompt_data=phase("normalize_prompt", context["prompt_data"]),
            _advanced_outputs_from_prompt_data=advanced_outputs,
            _encode_prompt_data_positive_conditioning=phase(
                "encode_positive", "positive-conditioning"
            ),
            _encode_with_comfy_clip=phase("encode_negative", "negative-conditioning"),
            _as_bool=lambda value, default: bool(value),
            _aio_detailer_has_enabled_targets=phase("detailer_enabled", False),
            _normalize_anima_mod_guidance_profile=phase("normalize_profile", "off"),
            _resolve_anima_mod_guidance_enabled=phase("resolve_guidance", False),
            _aio_highres_effective_backend=phase(
                "resolve_highres_backend", "comfy_ksampler"
            ),
            _apply_spectrum_anima_mod_guidance=unexpected,
            _apply_aio_spectrum_model_patches_for_comfy_sampler=apply_spectrum_model,
            _single_value=lambda value: value,
            random=_Random,
            _aio_first_pass_cache_key=cache_key,
            _get_aio_first_pass_cache=phase("get_cache", None),
            _generate_empty_latent_with_comfy=phase("empty_latent", "empty-latent"),
            _sample_latent_with_aio_backend=phase("sample", "sampled-latent"),
            _decode_latent_with_comfy=phase("decode", "decoded-image"),
            _resize_image_to_size_if_needed=phase(
                "resize_first_pass", ("decoded-image", False)
            ),
            _put_aio_first_pass_cache=phase("put_cache", None),
            _run_aio_highres_stage=run_highres,
            _run_aio_detailer_stage=run_detailer,
            _run_aio_upscale_stage=run_upscale,
            _image_tensor_size=image_size,
            _encode_image_with_comfy_vae=encode_image,
            _run_aio_postprocess_stage=run_postprocess,
            _cleanup_aio_ephemeral_model=cleanup,
            _save_aio_temp_preview_image=save_temp,
            _send_aio_preview_event=send_preview,
            _aio_save_filename_prefix=save_prefix,
            _save_image_with_comfy=save_comfy,
            _tag_aio_preview_images=tag_images,
            _prompt_data_json_safe=copy.deepcopy,
        ):
            output = generator.generate(
                context,
                "settings-json",
                "lora-stack",
                {"workflow": True},
                {"pnginfo": True},
                unique_id,
            )

        image, latent, metadata_json = output["result"]
        metadata = json.loads(metadata_json)
        return {
            "trace": trace,
            "result": {
                "image": image,
                "latent": latent,
                "metadata": metadata,
                "ui": output["ui"],
            },
        }


if __name__ == "__main__":
    unittest.main()
