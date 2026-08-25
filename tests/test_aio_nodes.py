from __future__ import annotations

import json
import sys
import unittest
from unittest.mock import patch

from easyuse_anima.aio import (
    conditioning,
    first_pass_cache,
    generation_defaults,
    generation_normalization,
    input_defaults,
    input_context,
    legacy_generation,
    model_preparation,
    output,
    postprocess,
    resources,
    sampling,
    usdu,
)
from easyuse_anima.nodes import aio_nodes
from easyuse_anima.extensions.aio import (
    AioHookDescriptor,
    AioHookPatch,
    AioHookPoint,
    AioHookSessionBase,
    AioStage,
    AioStagePhase,
)
from easyuse_anima.prompt.data import PROMPT_DATA_TYPE
from easyuse_anima.wildcard.seed import SEED_CONTROL_FIXED
from tests.comfy_host_fakes import (
    FakeComfyHostProvider,
    patch_comfy_helper,
    use_fake_comfy_host,
)
from tests.test_node_contracts import _loaded_package_entrypoint

_DEFAULT_COMFY_HOST = use_fake_comfy_host(aio_nodes, FakeComfyHostProvider())
_ISOLATED_AIO_SEED_COMPATIBILITY = patch(
    "easyuse_anima.nodes.seed_adapters.resolve_seed_execution_identity",
    return_value=None,
)


def setUpModule():
    _DEFAULT_COMFY_HOST.__enter__()
    _ISOLATED_AIO_SEED_COMPATIBILITY.start()


def tearDownModule():
    _ISOLATED_AIO_SEED_COMPATIBILITY.stop()
    _DEFAULT_COMFY_HOST.__exit__(None, None, None)


class AIONodeContractTests(unittest.TestCase):
    def test_aio_nodes_are_the_canonical_public_adapters_in_both_import_modes(self):
        self.assertEqual(
            aio_nodes.__all__,
            ("EasyUseAnimaInput", "EasyUseAnimaAIOGenerator"),
        )
        self.assertIs(
            aio_nodes._easy_use_anima_input_signature,
            input_context._easy_use_anima_input_signature,
        )
        self.assertIs(
            aio_nodes._require_easy_use_anima_input,
            input_context._require_easy_use_anima_input,
        )

        with _loaded_package_entrypoint() as (package_entrypoint, _):
            canonical_module = sys.modules[
                f"{package_entrypoint.__name__}.easyuse_anima.nodes.aio_nodes"
            ]
            canonical_input_context = sys.modules[
                f"{package_entrypoint.__name__}.easyuse_anima.aio.input_context"
            ]
            self.assertEqual(
                canonical_module.__all__,
                ("EasyUseAnimaInput", "EasyUseAnimaAIOGenerator"),
            )
            self.assertIs(
                package_entrypoint.NODE_CLASS_MAPPINGS["EasyUseAnimaInput"],
                canonical_module.EasyUseAnimaInput,
            )
            self.assertIs(
                package_entrypoint.NODE_CLASS_MAPPINGS["EasyUseAnimaAIOGenerator"],
                canonical_module.EasyUseAnimaAIOGenerator,
            )
            self.assertIs(
                canonical_module._easy_use_anima_input_signature,
                canonical_input_context._easy_use_anima_input_signature,
            )
            self.assertIs(
                canonical_module._require_easy_use_anima_input,
                canonical_input_context._require_easy_use_anima_input,
            )
    def test_input_types_resolve_root_runtime_values_at_call_time(self):
        calls = []
        unet_names = ["unet-b", "unet-a"]
        vae_names = ["vae-b", "vae-a"]
        clip_names = ["clip-b", "clip-a"]
        clip_types = ["stable_cascade", "qwen_image"]

        def names(label, values):
            def resolve():
                calls.append(label)
                return values

            return resolve

        def preferred_name(values, candidates):
            calls.append(("preferred_name", values, candidates))
            return candidates[0]

        def preferred_clip_type(values):
            calls.append(("preferred_clip_type", values))
            return "qwen_image"

        def input_settings_json():
            calls.append("input_settings_json")
            return '{"schema":"input-test"}'

        with patch.multiple(
            aio_nodes,
            PROMPT_DATA_TYPE="PROMPT_DATA_TEST",
            ANIMA_DEFAULT_DIFFUSION_MODEL_CANDIDATES=("unet-a",),
            ANIMA_DEFAULT_VAE_CANDIDATES=("vae-a",),
            ANIMA_DEFAULT_CLIP_CANDIDATES=("clip-a",),
            _comfy_diffusion_model_names=names("unet_names", unet_names),
            _comfy_vae_names=names("vae_names", vae_names),
            _comfy_text_encoder_names=names("clip_names", clip_names),
            _comfy_clip_loader_types=names("clip_types", clip_types),
            _preferred_name_default=preferred_name,
            _preferred_clip_type_default=preferred_clip_type,
            _aio_input_settings_json=input_settings_json,
        ):
            input_types = aio_nodes.EasyUseAnimaInput.INPUT_TYPES()

        self.assertEqual(
            calls,
            [
                "unet_names",
                "vae_names",
                "clip_names",
                "clip_types",
                ("preferred_name", unet_names, ("unet-a",)),
                ("preferred_name", vae_names, ("vae-a",)),
                ("preferred_name", clip_names, ("clip-a",)),
                ("preferred_clip_type", clip_types),
                "input_settings_json",
            ],
        )
        self.assertEqual(
            input_types,
            {
                "required": {
                    "PROMPT_DATA_TEST": ("PROMPT_DATA_TEST", {
                        "forceInput": True,
                        "tooltip": "Structured prompt data from Anima Prompt Studio Advanced v2.",
                    }),
                    "unet_name": (unet_names, {
                        "default": "unet-a",
                        "tooltip": "ANIMA diffusion model loaded with ComfyUI UNETLoader.",
                    }),
                    "vae_name": (vae_names, {
                        "default": "vae-a",
                        "tooltip": "VAE loaded with ComfyUI VAELoader.",
                    }),
                    "clip_name": (clip_names, {
                        "default": "clip-a",
                        "tooltip": "Text encoder loaded with ComfyUI CLIPLoader.",
                    }),
                    "clip_type": (clip_types, {
                        "default": "qwen_image",
                        "tooltip": "ComfyUI CLIPLoader type. Core ANIMA uses qwen_image.",
                    }),
                    "input_settings": ("STRING", {
                        "multiline": True,
                        "default": '{"schema":"input-test"}',
                        "hidden": True,
                        "tooltip": "Hidden versioned JSON storage for future resource settings. Kept serialized for workflow compatibility.",
                    }),
                },
            },
        )

    def test_input_change_key_preserves_payload_and_runtime_call_order(self):
        calls = []

        def normalize_prompt(value):
            calls.append(("normalize_prompt", value))
            return {"normalized": value}

        def json_safe(value):
            calls.append(("json_safe", value))
            return {"safe": value}

        def normalize_settings(value):
            calls.append(("normalize_settings", value))
            return {"settings": value}

        def stable_key(value):
            calls.append(("stable_key", value))
            return "change-key"

        with patch.multiple(
            aio_nodes,
            _normalize_prompt_data=normalize_prompt,
            _prompt_data_json_safe=json_safe,
            _normalize_aio_input_settings=normalize_settings,
            _stable_change_key=stable_key,
        ):
            result = aio_nodes.EasyUseAnimaInput.IS_CHANGED(
                {"prompt": "raw"},
                unet_name=None,
                vae_name=3,
                clip_name="clip",
                clip_type=False,
                input_settings="settings-json",
                ignored="compatibility",
            )

        expected_payload = {
            "mode": "easy_use_anima_input",
            "prompt_data": {"safe": {"normalized": {"prompt": "raw"}}},
            "unet_name": "",
            "vae_name": "3",
            "clip_name": "clip",
            "clip_type": "",
            "input_settings": {"settings": "settings-json"},
        }
        self.assertEqual(result, "change-key")
        self.assertEqual(
            calls,
            [
                ("normalize_prompt", {"prompt": "raw"}),
                ("json_safe", {"normalized": {"prompt": "raw"}}),
                ("normalize_settings", "settings-json"),
                ("stable_key", expected_payload),
            ],
        )

    def test_input_build_preserves_exact_context_and_copy_boundaries(self):
        source_prompt = {"positive_prompt": "p", "nested": {"value": 1}}
        settings = {
            "schema": "settings-schema",
            "resources": {
                "unet_weight_dtype": "fp8_e4m3fn",
                "clip_device": "cpu",
            },
        }

        with (
            patch.object(
                aio_nodes,
                "_normalize_aio_input_settings",
                return_value=settings,
            ) as normalize_settings,
            patch.object(
                aio_nodes,
                "_copy_prompt_data_for_update",
                wraps=aio_nodes._copy_prompt_data_for_update,
            ) as copy_prompt,
        ):
            context = aio_nodes.EasyUseAnimaInput().build(
                source_prompt,
                7,
                "vae.safetensors",
                "clip.safetensors",
                "",
                "settings-json",
            )[0]

        resource_info = {
            "loader_mode": "split",
            "unet_name": "7",
            "vae_name": "vae.safetensors",
            "clip_name": "clip.safetensors",
            "clip_type": "qwen_image",
            "unet_weight_dtype": "fp8_e4m3fn",
            "clip_device": "cpu",
        }
        self.assertEqual(
            context,
            {
                "schema": input_defaults.EASY_USE_ANIMA_INPUT_SCHEMA,
                "version": input_defaults.EASY_USE_ANIMA_INPUT_SETTINGS_VERSION,
                "prompt_data": {
                    "positive_prompt": "p",
                    "nested": {"value": 1},
                    "easy_use_anima_input": {
                        "schema": input_defaults.EASY_USE_ANIMA_INPUT_SCHEMA,
                        "version": input_defaults.EASY_USE_ANIMA_INPUT_SETTINGS_VERSION,
                        "resource_info": resource_info,
                    },
                },
                "resource_info": resource_info,
                "input_settings": settings,
            },
        )
        normalize_settings.assert_called_once_with("settings-json")
        copy_prompt.assert_called_once_with(source_prompt)
        self.assertNotIn("easy_use_anima_input", source_prompt)
        self.assertIsNot(context["prompt_data"], source_prompt)
        self.assertIsNot(
            context["prompt_data"]["easy_use_anima_input"]["resource_info"],
            context["resource_info"],
        )

    def test_input_node_contract_uses_dedicated_context_socket(self):
        required = aio_nodes.EasyUseAnimaInput.INPUT_TYPES()["required"]

        self.assertIn(PROMPT_DATA_TYPE, required)
        self.assertIn("unet_name", required)
        self.assertIn("vae_name", required)
        self.assertIn("clip_name", required)
        self.assertIn("clip_type", required)
        self.assertIn("input_settings", required)
        self.assertEqual(aio_nodes.EasyUseAnimaInput.RETURN_TYPES, (aio_nodes.EASY_USE_ANIMA_INPUT_TYPE,))
        self.assertEqual(aio_nodes.EasyUseAnimaInput.RETURN_NAMES, ("easy use anima input",))

    def test_generator_contract_keeps_mutable_settings_in_one_json_widget(self):
        required = aio_nodes.EasyUseAnimaAIOGenerator.INPUT_TYPES()["required"]

        self.assertEqual(
            required["easy_use_anima_input"][0],
            aio_nodes.EASY_USE_ANIMA_INPUT_TYPE,
        )
        self.assertEqual(
            aio_nodes.EasyUseAnimaAIOGenerator.INPUT_TYPES()["optional"]["lora_stack"][0],
            "LORA_STACK",
        )
        for name in (
            "seed",
            "steps",
            "cfg",
            "sampler_name",
            "scheduler",
            "denoise",
            "save_image",
        ):
            self.assertNotIn(name, required)
        self.assertIn("generation_settings", required)
        self.assertTrue(required["generation_settings"][1]["hidden"])
        self.assertEqual(
            aio_nodes.EasyUseAnimaAIOGenerator.RETURN_TYPES,
            ("IMAGE", "LATENT", "STRING"),
        )
        self.assertTrue(aio_nodes.EasyUseAnimaAIOGenerator.OUTPUT_NODE)
        self.assertEqual(
            aio_nodes.EasyUseAnimaAIOGenerator.RETURN_NAMES,
            ("image", "latent", "metadata_json"),
        )

    def test_generator_input_types_resolve_root_runtime_values_at_call_time(self):
        calls = []

        def generation_settings_json():
            calls.append("generation_settings_json")
            return '{"schema":"generation-test"}'

        with patch.multiple(
            aio_nodes,
            EASY_USE_ANIMA_INPUT_TYPE="EASY_USE_ANIMA_INPUT_TEST",
            _aio_generation_settings_json=generation_settings_json,
        ):
            input_types = aio_nodes.EasyUseAnimaAIOGenerator.INPUT_TYPES()

        self.assertEqual(calls, ["generation_settings_json"])
        self.assertEqual(
            input_types["required"]["easy_use_anima_input"][0],
            "EASY_USE_ANIMA_INPUT_TEST",
        )
        self.assertEqual(
            input_types["required"]["generation_settings"][1]["default"],
            '{"schema":"generation-test"}',
        )
        self.assertEqual(
            list(input_types),
            ["required", "hidden", "optional"],
        )
        self.assertEqual(
            list(input_types["required"]),
            ["easy_use_anima_input", "generation_settings"],
        )
        self.assertEqual(
            list(input_types["hidden"]),
            ["workflow_prompt", "extra_pnginfo", "unique_id"],
        )
        self.assertEqual(
            list(input_types["optional"]),
            ["lora_stack", "aio_hook"],
        )

    def test_generator_change_key_forces_only_nonfixed_seed_execution(self):
        calls = []
        special_seeds = set()
        normalized = {
            "sampler": {
                "seed": "runtime",
                "seed_after_generate": "fixed",
            },
            "future": {"kept": True},
        }

        def normalize(value):
            calls.append(("normalize", value))
            return json.loads(json.dumps(normalized))

        def input_signature(value):
            calls.append(("input_signature", value))
            return {"input": value}

        def lora_signature(value):
            calls.append(("lora_signature", value))
            return [{"lora": value}]

        def stable_key(value):
            calls.append(("stable_key", value))
            return "change-key"

        def hook_change_token(value):
            calls.append(("hook_change_token", value))
            return True, {"hook": value}

        with (
            patch.multiple(
                aio_nodes,
                AIO_SPECIAL_SEEDS=special_seeds,
                _normalize_aio_generation_settings=normalize,
                _aio_lora_stack_signature=lora_signature,
                aio_hook_change_token=hook_change_token,
                _stable_change_key=stable_key,
            ),
            patch.object(
                aio_nodes,
                "_easy_use_anima_input_signature",
                input_signature,
            ),
        ):
            fixed_result = aio_nodes.EasyUseAnimaAIOGenerator.IS_CHANGED(
                "context",
                "lora",
                "settings",
                aio_hook="hook",
                ignored="compatibility",
            )
            fixed_calls = list(calls)
            calls.clear()
            no_hook_result = aio_nodes.EasyUseAnimaAIOGenerator.IS_CHANGED(
                "context",
                "lora",
                "settings",
            )
            no_hook_calls = list(calls)
            calls.clear()
            special_seeds.add("runtime")
            special_result = aio_nodes.EasyUseAnimaAIOGenerator.IS_CHANGED(
                "context",
                "lora",
                "settings",
            )
            calls.clear()
            special_seeds.clear()
            normalized["sampler"]["seed"] = 7
            normalized["sampler"]["seed_after_generate"] = "increment"
            advancing_result = aio_nodes.EasyUseAnimaAIOGenerator.IS_CHANGED(
                "context",
                "lora",
                "settings",
            )

        fixed_payload = {
            "mode": "easy_use_anima_generator",
            "input": {"input": "context"},
            "lora_stack": [{"lora": "lora"}],
            "generation_settings": {
                "sampler": {
                    "seed": "runtime",
                    "seed_after_generate": "fixed",
                },
                "future": {"kept": True},
            },
            "aio_hook": {"hook": "hook"},
        }
        self.assertEqual(fixed_result, "change-key")
        self.assertEqual(
            fixed_calls,
            [
                ("normalize", "settings"),
                ("input_signature", "context"),
                ("lora_signature", "lora"),
                ("hook_change_token", "hook"),
                ("stable_key", fixed_payload),
            ],
        )
        no_hook_payload = dict(fixed_payload)
        no_hook_payload.pop("aio_hook")
        self.assertEqual(no_hook_result, "change-key")
        self.assertEqual(
            no_hook_calls,
            [
                ("normalize", "settings"),
                ("input_signature", "context"),
                ("lora_signature", "lora"),
                ("stable_key", no_hook_payload),
            ],
        )
        self.assertNotEqual(special_result, special_result)
        self.assertNotEqual(advancing_result, advancing_result)
        self.assertEqual(calls, [("normalize", "settings")])

    def test_input_signature_and_validator_preserve_exact_contract(self):
        calls = []

        def json_safe(value):
            calls.append(value)
            return {"safe": value}

        value = {
            "schema": "schema",
            "version": 2,
            "resource_info": {"resource": 1},
            "input_settings": {"setting": 2},
            "prompt_data": {"prompt": 3},
        }
        with patch.object(
            input_context,
            "_prompt_data_json_safe",
            side_effect=json_safe,
        ):
            signature = input_context._easy_use_anima_input_signature(value)
            non_mapping = input_context._easy_use_anima_input_signature("context")

        self.assertEqual(
            calls,
            [
                {"resource": 1},
                {"setting": 2},
                {"prompt": 3},
            ],
        )
        self.assertEqual(
            signature,
            {
                "schema": "schema",
                "version": 2,
                "resource_info": {"safe": {"resource": 1}},
                "input_settings": {"safe": {"setting": 2}},
                "prompt_data": {"safe": {"prompt": 3}},
            },
        )
        self.assertEqual(non_mapping, {"type": "str"})
        self.assertIs(input_context._require_easy_use_anima_input(value), value)
        with self.assertRaisesRegex(
            RuntimeError,
            r"^\[EasyUseAnima\] easy use anima input is missing or invalid\.$",
        ):
            input_context._require_easy_use_anima_input(None)
        with self.assertRaisesRegex(
            RuntimeError,
            r"^\[EasyUseAnima\] easy use anima input is missing required value\(s\): resource_info, input_settings$",
        ):
            input_context._require_easy_use_anima_input({"prompt_data": {}})

    def test_input_context_is_serializable_and_does_not_embed_model_objects(self):
        context = aio_nodes.EasyUseAnimaInput().build(
            {
                "positive_prompt": "p",
                "negative_prompt": "n",
                "width": 512,
                "height": 768,
            },
            "anima_model.safetensors",
            "anima_vae.safetensors",
            "anima_clip.safetensors",
            "qwen_image",
            "{}",
        )[0]

        self.assertNotIn("model", context)
        self.assertNotIn("clip", context)
        self.assertNotIn("vae", context)
        self.assertEqual(context["resource_info"]["unet_name"], "anima_model.safetensors")
        json.dumps(context)


class AIOSettingsStorageTests(unittest.TestCase):
    def test_input_settings_default_merge_preserves_unknown_future_keys(self):
        settings = resources._normalize_aio_input_settings(json.dumps({
            "version": 1,
            "resources": {
                "future_loader_mode": "external",
            },
            "future_root": {
                "enabled": True,
            },
        }))

        self.assertEqual(settings["schema"], input_defaults.EASY_USE_ANIMA_INPUT_SCHEMA)
        self.assertEqual(settings["resources"]["loader_mode"], "split")
        self.assertEqual(settings["resources"]["clip_loader"], "single")
        self.assertEqual(settings["resources"]["unet_weight_dtype"], "default")
        self.assertEqual(settings["resources"]["clip_device"], "default")
        self.assertEqual(settings["resources"]["future_loader_mode"], "external")
        self.assertTrue(settings["future_root"]["enabled"])

    def test_generation_settings_default_merge_preserves_unknown_future_keys(self):
        settings = generation_normalization._normalize_aio_generation_settings(json.dumps({
            "version": 1,
            "sampler": {
                "steps": 0,
                "future_sampler_key": "kept",
            },
            "save": {
                "enabled": True,
            },
            "future_section": {
                "value": 42,
            },
        }))

        self.assertEqual(settings["schema"], generation_defaults.AIO_GENERATION_SETTINGS_SCHEMA)
        self.assertEqual(settings["sampler"]["backend"], "comfy_ksampler")
        self.assertEqual(settings["sampler"]["seed"], generation_defaults.AIO_SPECIAL_SEED_RANDOM)
        self.assertEqual(settings["sampler"]["steps"], 1)
        self.assertEqual(settings["sampler"]["seed_after_generate"], SEED_CONTROL_FIXED)
        self.assertEqual(settings["sampler"]["future_sampler_key"], "kept")
        self.assertNotIn("enabled", settings["model_patches"]["aura_flow"])
        self.assertEqual(settings["model_patches"]["aura_flow"]["shift"], 3.0)
        self.assertFalse(settings["model_patches"]["safe_pag"]["enabled"])
        self.assertEqual(settings["model_patches"]["safe_pag"]["block_indices"], "18")
        self.assertEqual(settings["model_patches"]["kj"]["torch_compile"]["mode"], "max-autotune-no-cudagraphs")
        self.assertTrue(settings["save"]["enabled"])
        self.assertEqual(settings["save"]["backend"], "image_saver")
        self.assertNotIn("filename_prefix", settings["save"])
        self.assertEqual(settings["save"]["image_saver"]["extension"], "webp")
        self.assertEqual(settings["save"]["image_saver"]["quality_jpeg_or_webp"], 97)
        self.assertTrue(settings["save"]["image_saver"]["save_prompt_metadata"])
        self.assertEqual(settings["save"]["image_saver"]["additional_hash_bundles"], [])
        self.assertEqual(settings["save"]["image_saver"]["civitai_hash_fetchers"], [])
        self.assertNotIn("show_preview", settings["save"]["image_saver"])
        self.assertFalse(settings["preview"]["intermediate_images"])
        self.assertFalse(settings["preview"]["compare_previous"])
        self.assertTrue(settings["preview"]["image_feed"])
        self.assertEqual(settings["preview"]["feed_count"], 12)
        self.assertEqual(settings["future_section"]["value"], 42)

    def test_generation_settings_normalize_final_upscale(self):
        settings = generation_normalization._normalize_aio_generation_settings(json.dumps({
            "upscale": {
                "enabled": True,
                "backend": "invalid",
                "scale_by": 9,
                "spectrum": {
                    "enabled": True,
                    "window_size": 5,
                },
                "dit_corrections": {
                    "enabled": True,
                    "dcw_mode": "manual",
                },
                "usdu": {
                    "auto_tile_size": True,
                    "prompt_mode": "quality_tags_only",
                    "auto_tile_target": 9000,
                    "auto_tile_min": 128,
                    "auto_tile_max": 256,
                    "tile_width": 4,
                },
                "fit": {
                    "enabled": True,
                    "mode": "megapixels",
                    "max_long_edge": 8,
                    "max_megapixels": 999,
                    "method": "bad",
                },
                "resshift": {
                    "scale": "x9",
                    "dtype": "bad",
                    "tile_batch": 128,
                },
            },
        }))

        self.assertTrue(settings["upscale"]["enabled"])
        self.assertEqual(settings["upscale"]["backend"], "usdu")
        self.assertEqual(settings["upscale"]["scale_by"], 4.0)
        self.assertTrue(settings["upscale"]["spectrum"]["enabled"])
        self.assertEqual(settings["upscale"]["spectrum"]["window_size"], 5.0)
        self.assertTrue(settings["upscale"]["dit_corrections"]["enabled"])
        self.assertEqual(settings["upscale"]["dit_corrections"]["dcw_mode"], "manual")
        self.assertTrue(settings["upscale"]["usdu"]["auto_tile_size"])
        self.assertEqual(settings["upscale"]["usdu"]["prompt_mode"], "no_general")
        self.assertEqual(settings["upscale"]["usdu"]["auto_tile_target"], 9000)
        self.assertEqual(settings["upscale"]["usdu"]["auto_tile_min"], 128)
        self.assertEqual(settings["upscale"]["usdu"]["auto_tile_max"], 9000)
        self.assertEqual(settings["upscale"]["usdu"]["tile_width"], 64)
        self.assertNotIn("fit", settings["upscale"])
        self.assertTrue(settings["postprocess"]["enabled"])
        self.assertEqual(settings["postprocess"]["fit"]["mode"], "megapixels")
        self.assertEqual(settings["postprocess"]["fit"]["max_long_edge"], 64)
        self.assertEqual(settings["postprocess"]["fit"]["max_megapixels"], 256.0)
        self.assertEqual(settings["postprocess"]["fit"]["method"], "bicubic")
        self.assertEqual(settings["upscale"]["resshift"]["scale"], "x2")
        self.assertEqual(settings["upscale"]["resshift"]["dtype"], "bf16")
        self.assertEqual(settings["upscale"]["resshift"]["tile_batch"], 32)

    def test_generation_settings_preserve_custom_detailer_blocks(self):
        settings = generation_normalization._normalize_aio_generation_settings(json.dumps({
            "detailer": {
                "enabled": True,
                "order": ["custom_1", "eye", "face"],
                "custom_1": {
                    "label": "Hand Detailer",
                    "enabled": True,
                    "detect_prompt": "hand",
                    "spectrum": {
                        "enabled": True,
                        "window_size": 4.0,
                    },
                    "dit_corrections": {
                        "enabled": True,
                        "dcw_mode": "manual",
                    },
                },
            },
        }))

        self.assertEqual(settings["detailer"]["order"], ["custom_1", "eye", "face"])
        self.assertEqual(settings["detailer"]["custom_1"]["label"], "Hand Detailer")
        self.assertEqual(settings["detailer"]["custom_1"]["detect_prompt"], "hand")
        self.assertTrue(settings["detailer"]["custom_1"]["spectrum"]["enabled"])
        self.assertEqual(settings["detailer"]["custom_1"]["spectrum"]["window_size"], 4.0)
        self.assertEqual(settings["detailer"]["custom_1"]["dit_corrections"]["dcw_mode"], "manual")

    def test_generation_settings_clamp_detailer_thresholds(self):
        settings = generation_normalization._normalize_aio_generation_settings(json.dumps({
            "detailer": {
                "face": {"threshold": -1},
                "eye": {"threshold": 2},
                "custom_1": {"threshold": 0.63},
            },
        }))

        self.assertEqual(settings["detailer"]["face"]["threshold"], 0.0)
        self.assertEqual(settings["detailer"]["eye"]["threshold"], 1.0)
        self.assertEqual(settings["detailer"]["custom_1"]["threshold"], 0.63)

    def test_legacy_filename_prefix_is_not_kept_in_generation_settings(self):
        settings = generation_normalization._normalize_aio_generation_settings(json.dumps({
            "save": {
                "filename_prefix": "legacy/prefix",
                "image_saver": {
                    "filename": "name",
                    "path": "path",
                },
            },
        }))

        self.assertNotIn("filename_prefix", settings["save"])
        self.assertEqual(settings["save"]["image_saver"]["filename"], "name")
        self.assertEqual(settings["save"]["image_saver"]["path"], "path")

    def test_comfy_save_prefix_comes_from_image_saver_files(self):
        settings = generation_normalization._normalize_aio_generation_settings(json.dumps({
            "save": {
                "backend": "comfy_save_image",
                "image_saver": {
                    "filename": "frame_%time",
                    "path": "EasyUseAnima/Test",
                },
            },
        }))

        self.assertEqual(output._aio_save_filename_prefix(settings["save"]), "EasyUseAnima/Test/frame_%time")

    def test_image_saver_show_preview_is_not_kept_in_aio_settings(self):
        settings = generation_normalization._normalize_aio_generation_settings(json.dumps({
            "save": {
                "image_saver": {
                    "show_preview": True,
                },
            },
        }))

        self.assertNotIn("show_preview", settings["save"]["image_saver"])

    def test_preview_compare_can_use_feed_history_without_intermediate_previews(self):
        settings = generation_normalization._normalize_aio_generation_settings(json.dumps({
            "preview": {
                "intermediate_images": False,
                "compare_previous": True,
                "image_feed": False,
                "feed_count": 0,
            },
        }))

        self.assertFalse(settings["preview"]["intermediate_images"])
        self.assertTrue(settings["preview"]["compare_previous"])
        self.assertFalse(settings["preview"]["image_feed"])
        self.assertEqual(settings["preview"]["feed_count"], 1)

    def test_invalid_generation_settings_fall_back_to_versioned_defaults(self):
        settings = generation_normalization._normalize_aio_generation_settings("{")

        self.assertEqual(settings["schema"], generation_defaults.AIO_GENERATION_SETTINGS_SCHEMA)
        self.assertEqual(settings["version"], generation_defaults.AIO_GENERATION_SETTINGS_VERSION)
        self.assertEqual(settings["mode"], "txt2img")
        self.assertEqual(settings["sampler"]["steps"], 32)
        self.assertEqual(settings["sampler"]["sampler_name"], "er_sde")
        self.assertEqual(settings["sampler"]["scheduler"], "simple")
        self.assertEqual(settings["sampler"]["seed"], generation_defaults.AIO_SPECIAL_SEED_RANDOM)
        self.assertTrue(settings["save"]["enabled"])

    def test_aura_flow_is_shift_only_and_always_normalized_on(self):
        settings = generation_normalization._normalize_aio_generation_settings(json.dumps({
            "model_patches": {
                "aura_flow": {
                    "enabled": False,
                    "shift": 4.5,
                },
            },
        }))

        self.assertNotIn("enabled", settings["model_patches"]["aura_flow"])
        self.assertEqual(settings["model_patches"]["aura_flow"]["shift"], 4.5)

    def test_sampler_values_use_comfy_runtime_ranges_instead_of_slider_ranges(self):
        settings = generation_normalization._normalize_aio_generation_settings(json.dumps({
            "sampler": {
                "steps": 120,
                "cfg": 25,
            },
            "model_patches": {
                "aura_flow": {
                    "shift": 18,
                },
            },
        }))

        self.assertEqual(settings["sampler"]["steps"], 120)
        self.assertEqual(settings["sampler"]["cfg"], 25.0)
        self.assertEqual(settings["model_patches"]["aura_flow"]["shift"], 18.0)

        settings = generation_normalization._normalize_aio_generation_settings(json.dumps({
            "sampler": {
                "steps": 12000,
                "cfg": 125,
            },
            "model_patches": {
                "aura_flow": {
                    "shift": 125,
                },
            },
        }))

        self.assertEqual(settings["sampler"]["steps"], 10000)
        self.assertEqual(settings["sampler"]["cfg"], 100.0)
        self.assertEqual(settings["model_patches"]["aura_flow"]["shift"], 100.0)

        settings = generation_normalization._normalize_aio_generation_settings(json.dumps({
            "sampler": {"cfg": -1},
            "model_patches": {"aura_flow": {"shift": -1}},
        }))

        self.assertEqual(settings["sampler"]["cfg"], 0.0)
        self.assertEqual(settings["model_patches"]["aura_flow"]["shift"], 0.0)

    def test_stage_sampler_values_preserve_manual_entries_beyond_slider_ranges(self):
        settings = generation_normalization._normalize_aio_generation_settings(json.dumps({
            "highres": {
                "scale_by": 0.5,
                "steps": 120,
                "cfg": 25,
            },
            "upscale": {
                "scale_by": 0.5,
                "steps": 2000,
                "cfg": 25,
                "usdu": {"auto_tile_target": 9000},
            },
            "detailer": {
                "face": {
                    "steps": 120,
                    "cfg": 25,
                },
            },
        }))

        self.assertEqual(settings["highres"]["scale_by"], 0.5)
        self.assertEqual(settings["highres"]["steps"], 120)
        self.assertEqual(settings["highres"]["cfg"], 25.0)
        self.assertEqual(settings["upscale"]["scale_by"], 0.5)
        self.assertEqual(settings["upscale"]["steps"], 2000)
        self.assertEqual(settings["upscale"]["cfg"], 25.0)
        self.assertEqual(settings["upscale"]["usdu"]["auto_tile_target"], 9000)
        self.assertEqual(settings["detailer"]["face"]["steps"], 120)
        self.assertEqual(settings["detailer"]["face"]["cfg"], 25.0)

    def test_default_settings_json_is_compact_dict_storage(self):
        value = aio_nodes._aio_generation_settings_json()

        self.assertNotIn("\n", value)
        self.assertEqual(json.loads(value)["schema"], generation_defaults.AIO_GENERATION_SETTINGS_SCHEMA)

    def test_sampler_backend_is_limited_to_supported_paths(self):
        settings = generation_normalization._normalize_aio_generation_settings(json.dumps({
            "sampler": {
                "backend": "not_supported",
            },
        }))

        self.assertEqual(settings["sampler"]["backend"], "comfy_ksampler")

        settings = generation_normalization._normalize_aio_generation_settings(json.dumps({
            "sampler": {
                "backend": "anima_dave",
            },
        }))

        self.assertEqual(settings["sampler"]["backend"], "comfy_ksampler")
        self.assertFalse(settings["model_patches"]["dave"]["enabled"])
        self.assertEqual(settings["model_patches"]["dave"]["mask"], "dave_alpha.npz")

    def test_aio_seed_accepts_rgthree_special_values(self):
        settings = generation_normalization._normalize_aio_generation_settings(json.dumps({
            "sampler": {
                "seed": generation_defaults.AIO_SPECIAL_SEED_RANDOM,
            },
        }))
        self.assertEqual(settings["sampler"]["seed"], generation_defaults.AIO_SPECIAL_SEED_RANDOM)

        settings = generation_normalization._normalize_aio_generation_settings(json.dumps({
            "sampler": {
                "seed": generation_defaults.AIO_SPECIAL_SEED_INCREMENT,
            },
        }))
        self.assertEqual(settings["sampler"]["seed"], generation_defaults.AIO_SPECIAL_SEED_INCREMENT)

        settings = generation_normalization._normalize_aio_generation_settings(json.dumps({
            "sampler": {
                "seed": -999,
            },
        }))
        self.assertEqual(settings["sampler"]["seed"], generation_defaults.AIO_SPECIAL_SEED_DECREMENT)

    def test_runtime_special_seed_resolves_to_concrete_seed(self):
        with patch.object(sampling.random, "randint", return_value=123456):
            self.assertEqual(
                sampling._resolve_aio_runtime_seed(generation_defaults.AIO_SPECIAL_SEED_RANDOM),
                123456,
            )

    def test_generation_scheduler_uses_comfy_ksampler_choices(self):
        with patch.object(
            generation_normalization,
            "_comfy_scheduler_names",
            return_value=["normal", "sgm_uniform"],
        ):
            settings = generation_normalization._normalize_aio_generation_settings(json.dumps({
                "sampler": {
                    "scheduler": "er_sde",
                },
            }))

        self.assertEqual(settings["sampler"]["scheduler"], "normal")

    def test_detailer_labels_are_saved_as_ui_metadata(self):
        settings = generation_normalization._normalize_aio_generation_settings(json.dumps({
            "detailer": {
                "face": {
                    "label": "Portrait pass",
                },
                "eye": {
                    "label": "",
                },
            },
        }))

        self.assertEqual(settings["detailer"]["face"]["label"], "Portrait pass")
        self.assertEqual(settings["detailer"]["eye"]["label"], "Eye Detailer")


class AIOImageSaverDependencyTests(unittest.TestCase):
    def test_missing_image_saver_dependency_names_required_node_pack(self):
        with patch_comfy_helper(aio_nodes, "_find_comfy_node_class", return_value=None):
            with self.assertRaisesRegex(RuntimeError, "ComfyUI-Image-Saver"):
                output._save_image_with_image_saver(
                    images=None,
                    save_settings=generation_normalization._normalize_aio_generation_settings("{}")["save"],
                    positive_prompt="positive",
                    negative_prompt="negative",
                    width=512,
                    height=512,
                    sampler_settings=generation_defaults.AIO_GENERATION_DEFAULT_SETTINGS["sampler"],
                    resource_info={},
                    workflow_prompt=None,
                    extra_pnginfo=None,
                )

    def test_image_saver_additional_hash_bundles_are_combined_at_runtime(self):
        fetch_calls = []

        class FakeCivitaiHashFetcher:
            def get_autov3_hash(self, username, model_name, version=""):
                fetch_calls.append((username, model_name, version))
                return ("ABCDEF1234",)

        with patch_comfy_helper(
            aio_nodes,
            "_find_comfy_node_class",
            return_value=FakeCivitaiHashFetcher,
        ):
            result = output._aio_image_saver_additional_hashes({
                "additional_hashes": "Base:AAAAAAAA",
                "additional_hash_bundles": [
                    "LoraA:BBBBBBBB:0.8",
                    "CCCCCCCC:1.0",
                ],
                "civitai_hash_fetchers": [
                    {
                        "enabled": True,
                        "username": "N0VA39",
                        "model_name": "Anima All in One workflow",
                        "version": "",
                    },
                ],
            })

        self.assertEqual(
            result,
            "Base:AAAAAAAA,LoraA:BBBBBBBB:0.8,CCCCCCCC:1.0,Anima All in One workflow:ABCDEF1234",
        )
        self.assertEqual(fetch_calls, [("N0VA39", "Anima All in One workflow", "")])

    def test_image_saver_civitai_hash_fetcher_api_errors_are_skipped(self):
        class FakeCivitaiHashFetcher:
            def get_autov3_hash(self, username, model_name, version=""):
                return ("Error: API request failed with status 503",)

        with patch_comfy_helper(
            aio_nodes,
            "_find_comfy_node_class",
            return_value=FakeCivitaiHashFetcher,
        ):
            with self.assertLogs("ComfyUI-EasyUseAnima", level="WARNING") as logs:
                result = output._aio_image_saver_additional_hashes({
                    "additional_hashes": "Base:AAAAAAAA",
                    "civitai_hash_fetchers": [
                        {
                            "enabled": True,
                            "username": "N0VA39",
                            "model_name": "ANIMA Easy Use workflow",
                            "version": "",
                        },
                    ],
                })

        self.assertEqual(result, "Base:AAAAAAAA")
        self.assertIn("skipping metadata hash", "\n".join(logs.output))

    def test_image_saver_civitai_hash_fetcher_exceptions_are_skipped(self):
        class FakeCivitaiHashFetcher:
            def get_autov3_hash(self, username, model_name, version=""):
                raise RuntimeError("temporary upstream failure")

        with patch_comfy_helper(
            aio_nodes,
            "_find_comfy_node_class",
            return_value=FakeCivitaiHashFetcher,
        ):
            with self.assertLogs("ComfyUI-EasyUseAnima", level="WARNING") as logs:
                result = output._aio_image_saver_additional_hashes({
                    "additional_hashes": "Base:AAAAAAAA",
                    "civitai_hash_fetchers": [
                        {
                            "enabled": True,
                            "username": "N0VA39",
                            "model_name": "ANIMA Easy Use workflow",
                            "version": "",
                        },
                    ],
                })

        self.assertEqual(result, "Base:AAAAAAAA")
        self.assertIn("temporary upstream failure", "\n".join(logs.output))

    def test_image_saver_save_files_receives_workflow_metadata_flags(self):
        calls = []

        class FakeImageSaver:
            def save_files(self, **kwargs):
                calls.append(kwargs)
                return {"ui": {"images": [{"filename": "preview.webp"}]}}

        class FakeCivitaiHashFetcher:
            def get_autov3_hash(self, username, model_name, version=""):
                return ("ABCDEF1234",)

        settings = generation_normalization._normalize_aio_generation_settings(json.dumps({
            "save": {
                "enabled": True,
                "image_saver": {
                    "filename": "sample",
                    "path": "EasyUseAnima/Test",
                    "extension": "webp",
                    "embed_workflow": True,
                    "save_workflow_as_json": True,
                    "additional_hashes": "Base:AAAAAAAA",
                    "additional_hash_bundles": [
                        "LoraA:BBBBBBBB:0.8",
                        "CCCCCCCC:1.0",
                    ],
                    "civitai_hash_fetchers": [
                        {
                            "enabled": True,
                            "username": "N0VA39",
                            "model_name": "Anima All in One workflow",
                            "version": "",
                        },
                    ],
                },
            },
        }))

        def fake_find(node_id):
            return {
                "Image Saver": FakeImageSaver,
                "Civitai Hash Fetcher (Image Saver)": FakeCivitaiHashFetcher,
            }.get(node_id)

        with patch_comfy_helper(
            aio_nodes,
            "_find_comfy_node_class",
            side_effect=fake_find,
        ):
            result = output._save_image_with_image_saver(
                images="images",
                save_settings=settings["save"],
                positive_prompt="positive",
                negative_prompt="negative",
                width=768,
                height=1024,
                sampler_settings=settings["sampler"],
                resource_info={"unet_name": "anima"},
                workflow_prompt={"1": {}},
                extra_pnginfo={"workflow": {}},
            )

        self.assertEqual(result["ui"]["images"][0]["filename"], "preview.webp")
        self.assertEqual(calls[0]["filename"], "sample")
        self.assertEqual(calls[0]["path"], "EasyUseAnima/Test")
        self.assertTrue(calls[0]["embed_workflow"])
        self.assertTrue(calls[0]["save_workflow_as_json"])
        self.assertEqual(calls[0]["positive"], "positive")
        self.assertEqual(calls[0]["negative"], "negative")
        self.assertFalse(calls[0]["show_preview"])
        self.assertEqual(calls[0]["modelname"], "anima")
        self.assertEqual(calls[0]["width"], 768)
        self.assertEqual(calls[0]["height"], 1024)
        self.assertEqual(
            calls[0]["additional_hashes"],
            "Base:AAAAAAAA,LoraA:BBBBBBBB:0.8,CCCCCCCC:1.0,Anima All in One workflow:ABCDEF1234",
        )

    def test_image_saver_metadata_prompt_includes_applied_loras(self):
        calls = []

        class FakeImageSaver:
            def save_files(self, **kwargs):
                calls.append(kwargs)
                return {"ui": {"images": [{"filename": "preview.webp"}]}}

        with patch_comfy_helper(
            aio_nodes,
            "_find_comfy_node_class",
            return_value=FakeImageSaver,
        ):
            output._save_image_with_image_saver(
                images="images",
                save_settings=generation_normalization._normalize_aio_generation_settings("{}")["save"],
                positive_prompt="positive prompt",
                negative_prompt="negative prompt",
                width=768,
                height=1024,
                sampler_settings=generation_normalization._normalize_aio_generation_settings("{}")["sampler"],
                applied_loras=[
                    {"name": "styles\\foo.safetensors", "strength_model": 0.75, "strength_clip": 1.0},
                    {"name": "bar", "strength_model": 1.0, "strength_clip": 1.0},
                ],
                resource_info={"unet_name": "anima"},
                workflow_prompt=None,
                extra_pnginfo=None,
            )

        self.assertIn("<lora:styles/foo:0.75>", calls[0]["positive"])
        self.assertIn("<lora:bar:1>", calls[0]["positive"])

    def test_image_saver_can_skip_prompt_metadata(self):
        calls = []

        class FakeImageSaver:
            def save_files(self, **kwargs):
                calls.append(kwargs)
                return {"ui": {"images": [{"filename": "preview.webp"}]}}

        settings = generation_normalization._normalize_aio_generation_settings(json.dumps({
            "save": {
                "image_saver": {
                    "save_prompt_metadata": False,
                },
            },
        }))

        with patch_comfy_helper(
            aio_nodes,
            "_find_comfy_node_class",
            return_value=FakeImageSaver,
        ):
            output._save_image_with_image_saver(
                images="images",
                save_settings=settings["save"],
                positive_prompt="positive prompt",
                negative_prompt="negative prompt",
                width=768,
                height=1024,
                sampler_settings=settings["sampler"],
                applied_loras=[
                    {"name": "styles\\foo.safetensors", "strength_model": 0.75, "strength_clip": 1.0},
                ],
                resource_info={"unet_name": "anima"},
                workflow_prompt={"1": {}},
                extra_pnginfo={"workflow": {}},
            )

        self.assertEqual(calls[0]["positive"], "")
        self.assertEqual(calls[0]["negative"], "")
        self.assertEqual(calls[0]["prompt"], {"1": {}})
        self.assertEqual(calls[0]["extra_pnginfo"], {"workflow": {}})


class AIOLoraStackTests(unittest.TestCase):
    def test_lora_stack_is_normalized_from_tuple_and_dict_entries(self):
        stack = model_preparation._normalize_aio_lora_stack([
            ("style/foo.safetensors", "0.8", "0.6"),
            {"name": "bar", "strength": "1.2", "clip_strength": "0.7"},
            {"name": "None", "strength": 1.0},
        ])

        self.assertEqual(stack, [
            ("style\\foo.safetensors", 0.8, 0.6),
            ("bar", 1.2, 0.7),
        ])

    def test_lora_stack_applies_core_lora_loader_in_order(self):
        calls = []

        class FakeLoraLoader:
            def load_lora(self, model, clip, lora_name, strength_model, strength_clip):
                calls.append((model, clip, lora_name, strength_model, strength_clip))
                return (f"{model}>{lora_name}", f"{clip}>{lora_name}")

        with patch_comfy_helper(
            aio_nodes,
            "_find_comfy_node_class",
            return_value=FakeLoraLoader,
        ):
            model, clip, applied = model_preparation._apply_aio_lora_stack(
                "model",
                "clip",
                [("a.safetensors", 0.5, 0.25), ("b.safetensors", 1.0, 1.0)],
            )

        self.assertEqual(model, "model>a.safetensors>b.safetensors")
        self.assertEqual(clip, "clip>a.safetensors>b.safetensors")
        self.assertEqual([call[2] for call in calls], ["a.safetensors", "b.safetensors"])
        self.assertEqual(applied[-1]["name"], "b.safetensors")


class AIOSamplerDependencyTests(unittest.TestCase):
    def test_comfy_ksampler_can_apply_spectrum_model_patches(self):
        calls = []

        class FakeCorrectionPatch:
            def patch(self, model, *args, **kwargs):
                calls.append(("correction", model, args, kwargs))
                return ("corrected_model",)

        class FakeSpectrumPatch:
            def patch(self, model, *args, **kwargs):
                calls.append(("spectrum", model, args, kwargs))
                return ("spectrum_model",)

        def fake_find(node_id):
            return {
                "DiTCFGFSGPatch": FakeCorrectionPatch,
                "DiTSpectrumPatchAdvanced": FakeSpectrumPatch,
            }.get(node_id)

        settings = generation_normalization._normalize_aio_generation_settings(json.dumps({
            "sampler": {
                "backend": "comfy_ksampler",
                "steps": 32,
                "cfg": 4.5,
                "sampler_name": "euler",
                "scheduler": "normal",
                "denoise": 0.8,
                "spectrum": {
                    "enabled": True,
                    "compat_policy": "strict",
                },
                "dit_corrections": {
                    "enabled": True,
                    "dcw_mode": "manual",
                    "dcw_lambda": 0.02,
                    "smc_cfg": True,
                    "adaptive_smc_alpha": 0.2,
                    "smc_cfg_lambda": 5.5,
                },
            },
        }))

        with patch_comfy_helper(
            aio_nodes,
            "_find_comfy_node_class",
            side_effect=fake_find,
        ):
            result = model_preparation._apply_aio_spectrum_model_patches_for_comfy_sampler(
                "base_model",
                "clip",
                "positive",
                settings["sampler"],
            )

        self.assertEqual(result, "spectrum_model")
        self.assertEqual([call[0] for call in calls], ["correction", "spectrum"])
        self.assertEqual(calls[0][1], "base_model")
        self.assertEqual(calls[1][1], "corrected_model")
        self.assertEqual(calls[1][3]["compat_policy"], "strict")

    def test_comfy_ksampler_spectrum_patch_falls_back_to_legacy_node_id(self):
        calls = []

        class LegacySpectrumPatch:
            def patch(self, *, model, steps, window_size):
                calls.append(locals())
                return ("spectrum_model",)

        def fake_find(node_id):
            return {
                "DiTSpectrumPatch": LegacySpectrumPatch,
            }.get(node_id)

        settings = generation_normalization._normalize_aio_generation_settings(json.dumps({
            "sampler": {
                "backend": "comfy_ksampler",
                "steps": 32,
                "spectrum": {
                    "enabled": True,
                    "window_size": 2.5,
                    "compat_policy": "strict",
                },
            },
        }))

        with patch_comfy_helper(
            aio_nodes,
            "_find_comfy_node_class",
            side_effect=fake_find,
        ):
            result = model_preparation._apply_aio_spectrum_model_patches_for_comfy_sampler(
                "base_model",
                "clip",
                "positive",
                settings["sampler"],
            )

        self.assertEqual(result, "spectrum_model")
        self.assertEqual(calls[0]["model"], "base_model")
        self.assertEqual(calls[0]["steps"], 32)
        self.assertEqual(calls[0]["window_size"], 2.5)
        self.assertNotIn("compat_policy", calls[0])

    def test_missing_spectrum_model_patch_dependency_names_required_node_pack(self):
        settings = generation_normalization._normalize_aio_generation_settings(json.dumps({
            "sampler": {
                "backend": "comfy_ksampler",
                "spectrum": {
                    "enabled": True,
                },
            },
        }))

        with patch_comfy_helper(aio_nodes, "_find_comfy_node_class", return_value=None):
            with self.assertRaisesRegex(RuntimeError, "ComfyUI-Spectrum-KSampler"):
                model_preparation._apply_aio_spectrum_model_patches_for_comfy_sampler(
                    "base_model",
                    "clip",
                    "positive",
                    settings["sampler"],
                )

    def test_missing_spectrum_sampler_dependency_names_required_node_pack(self):
        settings = generation_normalization._normalize_aio_generation_settings(json.dumps({
            "sampler": {
                "backend": "spectrum_mod_guidance_advanced",
            },
        }))

        with patch_comfy_helper(aio_nodes, "_find_comfy_node_class", return_value=None):
            with self.assertRaisesRegex(RuntimeError, "ComfyUI-Spectrum-KSampler"):
                sampling._sample_latent_with_aio_backend(
                    model=None,
                    clip=None,
                    positive=None,
                    negative=None,
                    latent_image=None,
                    sampler_settings=settings["sampler"],
                    mod_guidance_settings=settings["mod_guidance"],
                    use_mod_guidance=True,
                    quality_tags="quality",
                    quality_neg="negative quality",
                )

    def test_spectrum_advanced_sampler_filters_unsupported_keywords(self):
        calls = []

        class LegacySpectrumAdvanced:
            def sample(
                self,
                *,
                model,
                clip,
                seed,
                steps,
                cfg,
                sampler_name,
                scheduler,
                positive,
                negative,
                latent_image,
                adapter,
                quality_tags,
                mod_w,
                denoise=1.0,
                window_size=2.0,
            ):
                calls.append(locals())
                return ("latent",)

        settings = generation_normalization._normalize_aio_generation_settings(json.dumps({
            "sampler": {
                "backend": "spectrum_mod_guidance_advanced",
                "dit_corrections": {
                    "enabled": True,
                    "cfgpp": True,
                    "cfgpp_lambda": 1.5,
                    "fsg": True,
                },
                "spectrum_extra": {
                    "future_optional": 123,
                },
            },
        }))

        with patch_comfy_helper(
            aio_nodes,
            "_require_custom_node_class",
            return_value=LegacySpectrumAdvanced,
        ):
            result = sampling._sample_latent_with_spectrum_mod_guidance_advanced(
                "model",
                "clip",
                settings["sampler"],
                settings["mod_guidance"],
                True,
                "positive",
                "negative",
                "latent_image",
                "quality",
                "quality_neg",
            )

        self.assertEqual(result, "latent")
        self.assertEqual(calls[0]["model"], "model")
        self.assertEqual(calls[0]["window_size"], 2.0)
        self.assertNotIn("cfgpp_lambda", calls[0])
        self.assertNotIn("future_optional", calls[0])

    def test_sampler_backend_dispatches_only_selected_path(self):
        cases = (
            ("comfy_ksampler", "comfy"),
            ("spectrum_mod_guidance_advanced", "advanced"),
            ("spectrum_spd_speed", "spd"),
        )

        for backend, expected_call in cases:
            with self.subTest(backend=backend):
                settings = generation_normalization._normalize_aio_generation_settings(json.dumps({
                    "sampler": {
                        "backend": backend,
                    },
                }))
                calls = []

                with (
                    patch.object(sampling, "_sample_latent_with_comfy", side_effect=lambda *args: calls.append("comfy") or f"{backend}_latent"),
                    patch.object(sampling, "_sample_latent_with_spectrum_spd", side_effect=lambda *args: calls.append("spd") or f"{backend}_latent"),
                    patch.object(sampling, "_sample_latent_with_spectrum_mod_guidance_advanced", side_effect=lambda *args: calls.append("advanced") or f"{backend}_latent"),
                ):
                    result = sampling._sample_latent_with_aio_backend(
                        model="model",
                        clip="clip",
                        positive="positive",
                        negative="negative",
                        latent_image="latent_image",
                        sampler_settings=settings["sampler"],
                        mod_guidance_settings=settings["mod_guidance"],
                        use_mod_guidance=False,
                        quality_tags="",
                        quality_neg="",
                    )

                self.assertEqual(result, f"{backend}_latent")
                self.assertEqual(calls, [expected_call])

    def test_spectrum_spd_sampler_is_normalized_to_euler(self):
        calls = []

        class FakeSpectrumSPDKSampler:
            def sample(self, *args, **kwargs):
                calls.append((args, kwargs))
                return ("latent",)

        settings = generation_normalization._normalize_aio_generation_settings(json.dumps({
            "sampler": {
                "sampler_name": "er_sde",
                "scheduler": "sgm_uniform",
            },
        }))

        with patch_comfy_helper(
            aio_nodes,
            "_require_custom_node_class",
            return_value=FakeSpectrumSPDKSampler,
        ):
            result = sampling._sample_latent_with_spectrum_spd(
                model="model",
                sampler_settings=settings["sampler"],
                positive="positive",
                negative="negative",
                latent_image="latent_image",
            )

        self.assertEqual(result, "latent")
        self.assertEqual(calls[0][1]["sampler_name"], "euler")
        self.assertEqual(calls[0][1]["scheduler"], "sgm_uniform")

    def test_spd_sampler_filters_unsupported_keywords(self):
        calls = []

        class LegacySpd:
            def sample(
                self,
                *,
                model,
                seed,
                steps,
                cfg,
                sampler_name,
                scheduler,
                positive,
                negative,
                latent_image,
                split_mode,
                spd_scale,
                spd_sigma,
            ):
                calls.append(locals())
                return ("latent",)

        settings = generation_normalization._normalize_aio_generation_settings(json.dumps({
            "sampler": {
                "backend": "spectrum_spd_speed",
                "spd_extra": {
                    "future_optional": 123,
                },
            },
        }))

        with patch_comfy_helper(
            aio_nodes,
            "_require_custom_node_class",
            return_value=LegacySpd,
        ):
            result = sampling._sample_latent_with_spectrum_spd(
                "model",
                settings["sampler"],
                "positive",
                "negative",
                "latent_image",
            )

        self.assertEqual(result, "latent")
        self.assertEqual(calls[0]["sampler_name"], "euler")
        self.assertNotIn("adaptive_smc_alpha", calls[0])
        self.assertNotIn("future_optional", calls[0])

    def test_anima_dave_patch_uses_dave_node_pack_settings(self):
        calls = []

        class FakeAnimaDAVE:
            def patch(self, *args):
                calls.append(args)
                return ("dave_model",)

        settings = generation_normalization._normalize_aio_generation_settings(json.dumps({
            "model_patches": {
                "dave": {
                    "enabled": True,
                    "mask": "custom_mask.npz",
                    "strength": 0.42,
                    "tau": 0.08,
                },
            },
        }))

        with patch_comfy_helper(
            aio_nodes,
            "_require_custom_node_class",
            return_value=FakeAnimaDAVE,
        ):
            result = model_preparation._apply_aio_anima_dave_patch("base_model", settings["model_patches"]["dave"])

        self.assertEqual(result, "dave_model")
        self.assertEqual(calls, [("base_model", "custom_mask.npz", 0.42, 0.08)])

    def test_safe_pag_patch_uses_anima_safe_pag_node_settings(self):
        calls = []

        class FakeAnimaSafePAG:
            def patch(self, *args):
                calls.append(args)
                return ("safe_pag_model",)

        settings = generation_normalization._normalize_aio_generation_settings(json.dumps({
            "model_patches": {
                "safe_pag": {
                    "enabled": True,
                    "scale": 5.5,
                    "block_indices": "12,18",
                    "perturbation_strength": 0.61,
                    "head_indices": "0,2",
                    "start_percent": 0.1,
                    "end_percent": 0.8,
                    "rescale": 0.35,
                    "rescale_mode": "partial",
                },
            },
        }))

        with patch_comfy_helper(
            aio_nodes,
            "_require_custom_node_class",
            return_value=FakeAnimaSafePAG,
        ):
            result = model_preparation._apply_aio_safe_pag_patch("base_model", settings["model_patches"]["safe_pag"])

        self.assertEqual(result, "safe_pag_model")
        self.assertEqual(calls, [(
            "base_model",
            5.5,
            "12,18",
            0.61,
            "0,2",
            0.1,
            0.8,
            0.35,
            "partial",
        )])

    def test_safe_pag_settings_are_clamped_to_node_ranges(self):
        settings = generation_normalization._normalize_aio_generation_settings(json.dumps({
            "model_patches": {
                "safe_pag": {
                    "enabled": True,
                    "scale": 250,
                    "block_indices": "",
                    "perturbation_strength": 9,
                    "start_percent": -1,
                    "end_percent": 3,
                    "rescale": 4,
                    "rescale_mode": "invalid",
                },
            },
        }))

        safe_pag = settings["model_patches"]["safe_pag"]
        self.assertTrue(safe_pag["enabled"])
        self.assertEqual(safe_pag["scale"], 100.0)
        self.assertEqual(safe_pag["block_indices"], "18")
        self.assertEqual(safe_pag["perturbation_strength"], 1.0)
        self.assertEqual(safe_pag["start_percent"], 0.0)
        self.assertEqual(safe_pag["end_percent"], 1.0)
        self.assertEqual(safe_pag["rescale"], 1.0)
        self.assertEqual(safe_pag["rescale_mode"], "full")

    def test_model_patches_apply_anima_dave_as_advanced_option(self):
        settings = generation_normalization._normalize_aio_generation_settings(json.dumps({
            "model_patches": {
                "dave": {
                    "enabled": True,
                    "mask": "custom_mask.npz",
                    "strength": 0.42,
                    "tau": 0.08,
                },
            },
        }))

        with (
            patch.object(model_preparation, "_patch_model_sampling_aura_flow", return_value="aura_model") as aura,
            patch.object(model_preparation, "_apply_aio_anima_dave_patch", return_value="dave_model") as dave,
            patch.object(model_preparation, "_apply_aio_safe_pag_patch", return_value="safe_pag_model") as safe_pag,
            patch.object(model_preparation, "_apply_aio_kj_model_patches", return_value="kj_model") as kj,
        ):
            result = model_preparation._apply_aio_model_patches("base_model", settings)

        self.assertEqual(result, "kj_model")
        self.assertEqual(aura.call_args.args[0], "base_model")
        self.assertEqual(dave.call_args.args[0], "aura_model")
        self.assertEqual(dave.call_args.args[1]["mask"], "custom_mask.npz")
        safe_pag.assert_not_called()
        self.assertEqual(kj.call_args.args[0], "dave_model")

    def test_model_patches_apply_safe_pag_before_kj_compile(self):
        settings = generation_normalization._normalize_aio_generation_settings(json.dumps({
            "model_patches": {
                "safe_pag": {
                    "enabled": True,
                    "scale": 4.5,
                },
            },
        }))

        with (
            patch.object(model_preparation, "_patch_model_sampling_aura_flow", return_value="aura_model") as aura,
            patch.object(model_preparation, "_apply_aio_anima_dave_patch", return_value="dave_model") as dave,
            patch.object(model_preparation, "_apply_aio_safe_pag_patch", return_value="safe_pag_model") as safe_pag,
            patch.object(model_preparation, "_apply_aio_kj_model_patches", return_value="kj_model") as kj,
        ):
            result = model_preparation._apply_aio_model_patches("base_model", settings)

        self.assertEqual(result, "kj_model")
        self.assertEqual(aura.call_args.args[0], "base_model")
        dave.assert_not_called()
        self.assertEqual(safe_pag.call_args.args[0], "aura_model")
        self.assertEqual(safe_pag.call_args.args[1]["scale"], 4.5)
        self.assertEqual(kj.call_args.args[0], "safe_pag_model")


class AIOHighresDetailerStageTests(unittest.TestCase):
    def test_highres_stage_resamples_scaled_image_with_stage_sampler(self):
        settings = generation_normalization._normalize_aio_generation_settings(json.dumps({
            "highres": {
                "enabled": True,
            },
        }))
        calls = []

        def fake_sample(*args):
            calls.append(args)
            return "high_latent"

        with (
            patch.object(legacy_generation, "_upscale_image_by_multiple", return_value=("scaled_image", 640, 960, 1.25)),
            patch.object(legacy_generation, "_encode_image_with_comfy_vae", return_value="high_latent_image"),
            patch.object(legacy_generation, "_apply_aio_spectrum_model_patches_for_comfy_sampler", return_value="stage_model"),
            patch.object(legacy_generation, "_sample_latent_with_aio_backend", side_effect=fake_sample),
            patch.object(legacy_generation, "_decode_latent_with_comfy", return_value="high_image"),
            patch.object(legacy_generation, "_cleanup_aio_ephemeral_model"),
        ):
            latent, image, width, height, metadata = legacy_generation._run_aio_highres_stage(
                "model",
                "clip",
                "vae",
                "positive",
                "negative",
                "base_image",
                "base_latent",
                512,
                768,
                settings["sampler"],
                settings["highres"],
            )

        self.assertEqual(latent, "high_latent")
        self.assertEqual(image, "high_image")
        self.assertEqual((width, height), (640, 960))
        self.assertTrue(metadata["enabled"])
        self.assertEqual(calls[0][0], "stage_model")
        self.assertEqual(calls[0][5]["backend"], "comfy_ksampler")
        self.assertEqual(calls[0][5]["sampler_name"], settings["sampler"]["sampler_name"])
        self.assertEqual(calls[0][5]["scheduler"], settings["sampler"]["scheduler"])
        self.assertEqual(calls[0][5]["steps"], settings["highres"]["steps"])
        self.assertEqual(calls[0][4], "high_latent_image")
        self.assertEqual(calls[0][5]["denoise"], 0.25)

    def test_highres_stage_can_override_main_sampler_when_inherit_is_disabled(self):
        settings = generation_normalization._normalize_aio_generation_settings(json.dumps({
            "sampler": {
                "sampler_name": "euler_ancestral",
                "scheduler": "normal",
                "cfg": 5,
            },
            "highres": {
                "enabled": True,
                "inherit_sampler_settings": False,
                "sampler_name": "euler",
                "scheduler": "simple",
                "cfg": 8,
            },
        }))
        calls = []

        def fake_sample(*args):
            calls.append(args)
            return "high_latent"

        with (
            patch.object(legacy_generation, "_upscale_image_by_multiple", return_value=("scaled_image", 640, 960, 1.25)),
            patch.object(legacy_generation, "_encode_image_with_comfy_vae", return_value="high_latent_image"),
            patch.object(legacy_generation, "_apply_aio_spectrum_model_patches_for_comfy_sampler", return_value="stage_model"),
            patch.object(legacy_generation, "_sample_latent_with_aio_backend", side_effect=fake_sample),
            patch.object(legacy_generation, "_decode_latent_with_comfy", return_value="high_image"),
            patch.object(legacy_generation, "_cleanup_aio_ephemeral_model"),
        ):
            legacy_generation._run_aio_highres_stage(
                "model",
                "clip",
                "vae",
                "positive",
                "negative",
                "base_image",
                "base_latent",
                512,
                768,
                settings["sampler"],
                settings["highres"],
            )

        self.assertEqual(calls[0][5]["cfg"], 8.0)
        self.assertEqual(calls[0][5]["sampler_name"], "euler")
        self.assertEqual(calls[0][5]["scheduler"], "simple")
        self.assertEqual(calls[0][5]["backend"], "comfy_ksampler")
        self.assertFalse(calls[0][5]["spectrum"].get("enabled", False))

    def test_highres_stage_reuses_integrated_sampler_backend(self):
        settings = generation_normalization._normalize_aio_generation_settings(json.dumps({
            "sampler": {
                "backend": "spectrum_mod_guidance_advanced",
                "spectrum": {
                    "window_size": 3,
                },
            },
            "highres": {
                "enabled": True,
                "spectrum": {
                    "window_size": 4,
                },
                "dit_corrections": {
                    "enabled": True,
                    "dcw_mode": "manual",
                },
            },
        }))

        with (
            patch.object(legacy_generation, "_upscale_image_by_multiple", return_value=("scaled_image", 640, 960, 1.25)),
            patch.object(legacy_generation, "_encode_image_with_comfy_vae", return_value="high_latent_image"),
            patch.object(legacy_generation, "_apply_aio_spectrum_model_patches_for_comfy_sampler") as comfy_patch,
            patch.object(legacy_generation, "_sample_latent_with_aio_backend", return_value="high_latent") as sample,
            patch.object(legacy_generation, "_decode_latent_with_comfy", return_value="high_image"),
            patch.object(legacy_generation, "_cleanup_aio_ephemeral_model"),
        ):
            legacy_generation._run_aio_highres_stage(
                "model",
                "clip",
                "vae",
                "positive",
                "negative",
                "base_image",
                "base_latent",
                512,
                768,
                settings["sampler"],
                settings["highres"],
                settings["mod_guidance"],
                True,
                "quality",
                "quality_neg",
            )

        comfy_patch.assert_not_called()
        self.assertEqual(sample.call_args.args[0], "model")
        self.assertEqual(sample.call_args.args[5]["backend"], "spectrum_mod_guidance_advanced")
        self.assertEqual(sample.call_args.args[5]["steps"], settings["highres"]["steps"])
        self.assertEqual(sample.call_args.args[5]["spectrum"]["window_size"], 4.0)
        self.assertEqual(sample.call_args.args[5]["dit_corrections"]["dcw_mode"], "manual")
        self.assertEqual(sample.call_args.args[7], True)
        self.assertEqual(sample.call_args.args[8], "quality")
        self.assertEqual(sample.call_args.args[9], "quality_neg")

    def test_highres_stage_keeps_stage_spectrum_when_following_main_sampler(self):
        settings = generation_normalization._normalize_aio_generation_settings(json.dumps({
            "sampler": {
                "spectrum": {
                    "enabled": False,
                    "window_size": 2,
                },
                "dit_corrections": {
                    "enabled": False,
                    "dcw_mode": "off",
                },
            },
            "highres": {
                "enabled": True,
                "inherit_sampler_settings": True,
                "spectrum": {
                    "enabled": True,
                    "window_size": 5,
                },
                "dit_corrections": {
                    "enabled": True,
                    "dcw_mode": "manual",
                },
            },
        }))

        with (
            patch.object(legacy_generation, "_upscale_image_by_multiple", return_value=("scaled_image", 640, 960, 1.25)),
            patch.object(legacy_generation, "_encode_image_with_comfy_vae", return_value="high_latent_image"),
            patch.object(legacy_generation, "_apply_aio_spectrum_model_patches_for_comfy_sampler", return_value="stage_model") as comfy_patch,
            patch.object(legacy_generation, "_sample_latent_with_aio_backend", return_value="high_latent"),
            patch.object(legacy_generation, "_decode_latent_with_comfy", return_value="high_image"),
            patch.object(legacy_generation, "_cleanup_aio_ephemeral_model"),
        ):
            legacy_generation._run_aio_highres_stage(
                "model",
                "clip",
                "vae",
                "positive",
                "negative",
                "base_image",
                "base_latent",
                512,
                768,
                settings["sampler"],
                settings["highres"],
            )

        stage_sampler = comfy_patch.call_args.args[3]
        self.assertTrue(stage_sampler["spectrum"]["enabled"])
        self.assertEqual(stage_sampler["spectrum"]["window_size"], 5.0)
        self.assertTrue(stage_sampler["dit_corrections"]["enabled"])
        self.assertEqual(stage_sampler["dit_corrections"]["dcw_mode"], "manual")

    def test_highres_stage_falls_back_to_comfy_when_main_sampler_is_spd(self):
        settings = generation_normalization._normalize_aio_generation_settings(json.dumps({
            "sampler": {
                "backend": "spectrum_spd_speed",
                "steps": 32,
                "scheduler": "sgm_uniform",
            },
            "highres": {
                "enabled": True,
                "steps": 18,
                "denoise": 0.22,
            },
        }))

        with (
            patch.object(legacy_generation, "_upscale_image_by_multiple", return_value=("scaled_image", 640, 960, 1.25)),
            patch.object(legacy_generation, "_encode_image_with_comfy_vae", return_value="high_latent_image"),
            patch.object(legacy_generation, "_apply_aio_spectrum_model_patches_for_comfy_sampler", return_value="stage_model"),
            patch.object(legacy_generation, "_sample_latent_with_aio_backend", return_value="high_latent") as sample,
            patch.object(legacy_generation, "_decode_latent_with_comfy", return_value="high_image"),
            patch.object(legacy_generation, "_cleanup_aio_ephemeral_model"),
        ):
            legacy_generation._run_aio_highres_stage(
                "model",
                "clip",
                "vae",
                "positive",
                "negative",
                "base_image",
                "base_latent",
                512,
                768,
                settings["sampler"],
                settings["highres"],
            )

        stage_sampler = sample.call_args.args[5]
        self.assertEqual(stage_sampler["backend"], "comfy_ksampler")
        self.assertEqual(stage_sampler["sampler_name"], "euler")
        self.assertEqual(stage_sampler["scheduler"], "sgm_uniform")
        self.assertEqual(stage_sampler["steps"], 18)
        self.assertEqual(stage_sampler["denoise"], 0.22)
        self.assertFalse(stage_sampler["spectrum"].get("enabled", False))

    def test_highres_stage_reencodes_when_decoded_image_size_needs_correction(self):
        settings = generation_normalization._normalize_aio_generation_settings(json.dumps({
            "highres": {
                "enabled": True,
            },
        }))

        with (
            patch.object(legacy_generation, "_upscale_image_by_multiple", return_value=("scaled_image", 640, 960, 1.25)),
            patch.object(legacy_generation, "_encode_image_with_comfy_vae", side_effect=["high_latent_image", "corrected_latent"]) as encode,
            patch.object(legacy_generation, "_apply_aio_spectrum_model_patches_for_comfy_sampler", return_value="stage_model"),
            patch.object(legacy_generation, "_sample_latent_with_aio_backend", return_value="high_latent"),
            patch.object(legacy_generation, "_decode_latent_with_comfy", return_value="undersized_image"),
            patch.object(legacy_generation, "_resize_image_to_size_if_needed", return_value=("corrected_image", True)) as resize,
            patch.object(legacy_generation, "_cleanup_aio_ephemeral_model"),
        ):
            latent, image, width, height, metadata = legacy_generation._run_aio_highres_stage(
                "model",
                "clip",
                "vae",
                "positive",
                "negative",
                "base_image",
                "base_latent",
                512,
                768,
                settings["sampler"],
                settings["highres"],
            )

        self.assertEqual(latent, "corrected_latent")
        self.assertEqual(image, "corrected_image")
        self.assertEqual((width, height), (640, 960))
        self.assertTrue(metadata["enabled"])
        self.assertEqual(encode.call_args_list[-1].args, ("vae", "corrected_image"))
        self.assertEqual(resize.call_args.args[1:3], (640, 960))

    def test_detailer_target_uses_stage_spectrum_patched_model(self):
        settings = generation_normalization._normalize_aio_generation_settings(json.dumps({
            "sampler": {
                "spectrum": {
                    "enabled": False,
                    "window_size": 2,
                },
            },
            "detailer": {
                "face": {
                    "enabled": True,
                    "threshold": 0.63,
                    "spectrum": {
                        "enabled": True,
                        "window_size": 4,
                    },
                    "dit_corrections": {
                        "enabled": True,
                        "dcw_mode": "manual",
                    },
                },
            },
        }))

        with (
            patch.object(legacy_generation, "_apply_aio_spectrum_model_patches_for_comfy_sampler", return_value="detail_model") as comfy_patch,
            patch.object(legacy_generation, "_run_sam3_detailer", return_value=("detailed_image", ((1, 1), ["seg"]), "mask", "raw_image")) as detailer,
            patch.object(legacy_generation, "_cleanup_aio_ephemeral_model"),
        ):
            image, metadata = legacy_generation._run_aio_detailer_target(
                "face",
                settings["detailer"]["face"],
                "image",
                "model",
                "clip",
                "vae",
                "positive",
                "negative",
                settings["sampler"],
                {"model": "sam3_model", "clip": "sam3_clip"},
            )

        self.assertEqual(image, "detailed_image")
        self.assertTrue(metadata["enabled"])
        self.assertTrue(metadata["detected"])
        self.assertEqual(detailer.call_args.kwargs["model"], "detail_model")
        self.assertEqual(detailer.call_args.kwargs["scheduler"], settings["sampler"]["scheduler"])
        self.assertEqual(detailer.call_args.kwargs["threshold"], 0.63)
        stage_sampler = comfy_patch.call_args.args[3]
        self.assertTrue(stage_sampler["spectrum"]["enabled"])
        self.assertEqual(stage_sampler["spectrum"]["window_size"], 4.0)
        self.assertTrue(stage_sampler["dit_corrections"]["enabled"])
        self.assertEqual(stage_sampler["dit_corrections"]["dcw_mode"], "manual")

    def test_detailer_stage_runs_targets_in_saved_order(self):
        settings = generation_normalization._normalize_aio_generation_settings(json.dumps({
            "detailer": {
                "enabled": True,
                "order": ["eye", "face"],
                "face": {
                    "enabled": True,
                },
                "eye": {
                    "enabled": True,
                },
            },
        }))
        calls = []

        def fake_detailer_target(target_name, target_settings, image, *args):
            calls.append((target_name, image))
            return f"{target_name}_image", {"enabled": True}

        with (
            patch.object(legacy_generation, "_load_aio_sam3_context", return_value={"ckpt_name": "sam3"}),
            patch.object(legacy_generation, "_run_aio_detailer_target", side_effect=fake_detailer_target),
        ):
            image, metadata = legacy_generation._run_aio_detailer_stage(
                "model",
                "clip",
                "vae",
                "positive",
                "negative",
                "base_image",
                settings["sampler"],
                settings["detailer"],
            )

        self.assertEqual([call[0] for call in calls], ["eye", "face"])
        self.assertEqual(calls[1][1], "eye_image")
        self.assertEqual(image, "face_image")
        self.assertEqual(metadata["order"], ["eye", "face"])

    def test_detailer_stage_runs_custom_targets_in_saved_order(self):
        settings = generation_normalization._normalize_aio_generation_settings(json.dumps({
            "detailer": {
                "enabled": True,
                "order": ["face", "custom_1", "eye"],
                "face": {
                    "enabled": True,
                },
                "custom_1": {
                    "label": "Hand Detailer",
                    "enabled": True,
                    "detect_prompt": "hand",
                },
                "eye": {
                    "enabled": True,
                },
            },
        }))
        calls = []

        def fake_detailer_target(target_name, target_settings, image, *args):
            calls.append((target_name, target_settings.get("detect_prompt"), image))
            return f"{target_name}_image", {"enabled": True}

        with (
            patch.object(legacy_generation, "_load_aio_sam3_context", return_value={"ckpt_name": "sam3"}),
            patch.object(legacy_generation, "_run_aio_detailer_target", side_effect=fake_detailer_target),
        ):
            image, metadata = legacy_generation._run_aio_detailer_stage(
                "model",
                "clip",
                "vae",
                "positive",
                "negative",
                "base_image",
                settings["sampler"],
                settings["detailer"],
            )

        self.assertEqual([call[0] for call in calls], ["face", "custom_1", "eye"])
        self.assertEqual(calls[1], ("custom_1", "hand", "face_image"))
        self.assertEqual(image, "eye_image")
        self.assertEqual(metadata["order"], ["face", "custom_1", "eye"])


class AIOFinalUpscaleStageTests(unittest.TestCase):
    class _Image:
        def __init__(self, width=512, height=768):
            self.shape = (1, height, width, 3)

    def test_usdu_auto_tile_size_has_practical_floor_and_alignment(self):
        for target in (64, 512, 1536, 3072):
            tile_size = usdu._aio_usdu_auto_tile_dimension(target)
            self.assertGreaterEqual(tile_size, 512)
            self.assertLessEqual(tile_size, 2048)
            self.assertEqual(tile_size % 64, 0)

    def test_usdu_auto_tile_size_uses_configurable_bounds(self):
        tile_size = usdu._aio_usdu_auto_tile_dimension(
            4096,
            preferred_size=640,
            min_size=384,
            max_size=768,
        )

        self.assertGreaterEqual(tile_size, 384)
        self.assertLessEqual(tile_size, 768)
        self.assertEqual(tile_size % 64, 0)

    def test_final_fit_size_downscales_by_long_edge_or_megapixels(self):
        self.assertEqual(
            postprocess._aio_final_fit_size(4096, 2048, {
                "enabled": True,
                "mode": "max_long_edge",
                "max_long_edge": 2048,
            })[:2],
            (2048, 1024),
        )
        width, height, scale = postprocess._aio_final_fit_size(4000, 3000, {
            "enabled": True,
            "mode": "megapixels",
            "max_megapixels": 4,
        })

        self.assertLess(scale, 1.0)
        self.assertLessEqual(width * height, 4_000_000)
        self.assertEqual(width % 8, 0)
        self.assertEqual(height % 8, 0)

    def test_postprocess_stage_applies_final_fit(self):
        with (
            patch.object(
                postprocess,
                "_apply_aio_final_fit",
                return_value=(
                    AIOFinalUpscaleStageTests._Image(2048, 1536),
                    {
                        "enabled": True,
                        "applied": True,
                        "mode": "max_long_edge",
                        "max_long_edge": 2048,
                        "max_megapixels": 4.0,
                        "method": "bicubic",
                        "width": 4096,
                        "height": 3072,
                        "target_width": 2048,
                        "target_height": 1536,
                    },
                ),
            ) as fit,
            self.assertLogs("ComfyUI-EasyUseAnima", level="INFO") as logs,
        ):
            image, metadata = postprocess._run_aio_postprocess_stage(
                AIOFinalUpscaleStageTests._Image(4096, 3072),
                {
                    "enabled": True,
                    "fit": {
                        "mode": "max_long_edge",
                        "max_long_edge": 2048,
                    },
                },
            )

        self.assertIsInstance(image, AIOFinalUpscaleStageTests._Image)
        fit.assert_called_once()
        self.assertTrue(metadata["enabled"])
        self.assertTrue(metadata["fit"]["applied"])
        self.assertEqual(metadata["width"], 2048)
        self.assertEqual(metadata["height"], 1536)
        self.assertIn("Postprocess final fit", "\n".join(logs.output))

    def test_usdu_no_general_prompt_keeps_artist_and_trigger_without_duplicate_quality(self):
        prompt_data = {
            "pin_trigger_tags_to_front": True,
            "fields": [
                {"pane": "positive", "type": "quality", "text": "best quality", "enabled": True},
                {"pane": "positive", "type": "artist", "text": "@sample artist", "enabled": True},
                {"pane": "positive", "type": "trigger", "text": "lora trigger", "enabled": True, "pin": True},
                {"pane": "positive", "type": "general", "text": "1girl, city background", "enabled": True},
            ],
        }

        prompt, has_fields = conditioning._aio_usdu_prompt_without_general(
            prompt_data,
            "positive",
            include_quality=False,
        )

        self.assertTrue(has_fields)
        self.assertIn("@sample artist", prompt)
        self.assertIn("lora trigger", prompt)
        self.assertNotIn("best quality", prompt)
        self.assertNotIn("1girl", prompt)
        self.assertNotIn("city background", prompt)

    def test_upscale_stage_runs_usdu_with_no_general_prompt_and_stage_patches(self):
        settings = generation_normalization._normalize_aio_generation_settings(json.dumps({
            "sampler": {
                "seed": 123,
                "steps": 30,
                "cfg": 5,
            },
            "upscale": {
                "enabled": True,
                "backend": "usdu",
                "scale_by": 2,
                "spectrum": {
                    "enabled": True,
                    "window_size": 6,
                },
                "dit_corrections": {
                    "enabled": True,
                    "dcw_mode": "manual",
                },
                "usdu": {
                    "prompt_mode": "no_general",
                    "auto_tile_size": True,
                    "auto_tile_target": 768,
                    "upscale_model_name": "model.safetensors",
                },
            },
        }))
        prompt_data = {
            "fields": [
                {"pane": "positive", "type": "quality", "text": "quality tags", "enabled": True},
                {"pane": "positive", "type": "artist", "text": "@artist", "enabled": True},
                {"pane": "positive", "type": "trigger", "text": "trigger word", "enabled": True, "pin": True},
                {"pane": "positive", "type": "general", "text": "removed content", "enabled": True},
                {"pane": "negative", "type": "quality", "text": "quality negative", "enabled": True},
                {"pane": "negative", "type": "general", "text": "removed negative content", "enabled": True},
            ],
        }
        calls = {}

        class FakeUSDU:
            def upscale(self, **kwargs):
                calls["usdu"] = kwargs
                return (AIOFinalUpscaleStageTests._Image(1024, 1536),)

        with (
            patch_comfy_helper(
                aio_nodes,
                "_require_custom_node_class",
                return_value=FakeUSDU,
            ) as require,
            patch.object(legacy_generation, "_load_upscale_model_with_comfy", return_value="upscale_model") as load_upscale,
            patch_comfy_helper(
                aio_nodes,
                "_encode_with_comfy_clip",
                side_effect=lambda clip, prompt: f"encoded:{prompt}",
            ) as encode,
            patch.object(legacy_generation, "_apply_aio_spectrum_model_patches_for_comfy_sampler", return_value="stage_model") as patch_stage,
            patch.object(legacy_generation, "_cleanup_aio_ephemeral_model") as cleanup,
            self.assertLogs("ComfyUI-EasyUseAnima", level="INFO") as logs,
        ):
            image, metadata = legacy_generation._run_aio_upscale_stage(
                "model",
                "clip",
                "vae",
                "positive",
                "negative",
                self._Image(512, 768),
                settings["sampler"],
                settings["upscale"],
                "quality tags",
                "quality negative",
                prompt_data,
                exclude_positive_quality=True,
            )

        self.assertIsInstance(image, self._Image)
        require.assert_called_once()
        load_upscale.assert_called_once_with("model.safetensors")
        self.assertEqual(encode.call_args_list[0].args, ("clip", "@artist, trigger word"))
        self.assertEqual(encode.call_args_list[1].args, ("clip", "quality negative"))
        self.assertEqual(patch_stage.call_args.args[2], "encoded:@artist, trigger word")
        stage_sampler = patch_stage.call_args.args[3]
        self.assertTrue(stage_sampler["spectrum"]["enabled"])
        self.assertEqual(stage_sampler["spectrum"]["window_size"], 6.0)
        self.assertTrue(stage_sampler["dit_corrections"]["enabled"])
        self.assertEqual(stage_sampler["dit_corrections"]["dcw_mode"], "manual")
        self.assertEqual(calls["usdu"]["model"], "stage_model")
        self.assertEqual(calls["usdu"]["positive"], "encoded:@artist, trigger word")
        self.assertEqual(calls["usdu"]["negative"], "encoded:quality negative")
        self.assertEqual(calls["usdu"]["upscale_model"], "upscale_model")
        self.assertEqual(calls["usdu"]["tile_width"], 512)
        self.assertEqual(calls["usdu"]["tile_height"], 768)
        self.assertEqual(metadata["backend"], "usdu")
        self.assertEqual(metadata["prompt_mode"], "no_general")
        self.assertTrue(metadata["tile_auto"])
        self.assertEqual(metadata["tile_target_width"], 1024)
        self.assertEqual(metadata["tile_target_height"], 1536)
        self.assertNotIn("fit", metadata)
        log_text = "\n".join(logs.output)
        self.assertIn("USDU auto tile", log_text)
        self.assertIn("resolved_tile=512x768", log_text)
        self.assertIn("USDU sampler: steps=20", log_text)
        cleanup.assert_called_once_with("stage_model", "model")

    def test_upscale_stage_runs_only_resshift_when_selected(self):
        settings = generation_normalization._normalize_aio_generation_settings(json.dumps({
            "sampler": {
                "seed": 321,
            },
            "upscale": {
                "enabled": True,
                "backend": "resshift",
                "resshift": {
                    "scale": "x4",
                    "student_name": "student.ckpt",
                    "dtype": "fp32",
                    "chop": 1024,
                    "overlap": 96,
                    "tile_batch": 2,
                },
            },
        }))
        calls = {}

        class FakeLoader:
            def load(self, scale, student_name, dtype):
                calls["loader"] = (scale, student_name, dtype)
                return ("resshift_model",)

        class FakeUpscale:
            def upscale(self, *args):
                calls["upscale"] = args
                return (AIOFinalUpscaleStageTests._Image(2048, 3072),)

        def fake_require(node_id, *_args):
            if node_id == "ResShiftLoader":
                return FakeLoader
            if node_id == "ResShiftUpscale":
                return FakeUpscale
            raise AssertionError(f"unexpected node lookup: {node_id}")

        input_image = self._Image(512, 768)
        with (
            patch_comfy_helper(
                aio_nodes,
                "_require_custom_node_class",
                side_effect=fake_require,
            ) as require,
            patch.object(legacy_generation, "_load_upscale_model_with_comfy") as load_upscale,
            patch.object(legacy_generation, "_apply_aio_spectrum_model_patches_for_comfy_sampler") as patch_stage,
        ):
            image, metadata = legacy_generation._run_aio_upscale_stage(
                "model",
                "clip",
                "vae",
                "positive",
                "negative",
                input_image,
                settings["sampler"],
                settings["upscale"],
            )

        self.assertIsInstance(image, self._Image)
        self.assertEqual(require.call_count, 2)
        load_upscale.assert_not_called()
        patch_stage.assert_not_called()
        self.assertEqual(calls["loader"], ("x4", "student.ckpt", "fp32"))
        self.assertEqual(calls["upscale"][0], "resshift_model")
        self.assertIs(calls["upscale"][1], input_image)
        self.assertEqual(calls["upscale"][2:], (321, 1024, 96, 2))
        self.assertEqual(metadata["backend"], "resshift")
        self.assertEqual(metadata["scale"], "x4")


class AIOGeneratorRuntimeTests(unittest.TestCase):
    def setUp(self):
        first_pass_cache._clear_aio_first_pass_cache()

    def _context(self):
        return {
            "prompt_data": {},
            "resource_info": {
                "unet_name": "anima_model.safetensors",
                "vae_name": "anima_vae.safetensors",
                "clip_name": "anima_clip.safetensors",
                "clip_type": "qwen_image",
            },
            "input_settings": {},
        }

    def test_generator_exposes_standard_images_and_custom_preview_key(self):
        context = self._context()

        class MetadataSession(AioHookSessionBase):
            def after_stage(self, event):
                del event
                return AioHookPatch(metadata={"integration": True})

        class MetadataHook:
            def describe(self):
                return AioHookDescriptor(
                    hook_id="tests.metadata",
                    hook_version="1",
                    points=frozenset({
                        AioHookPoint(
                            AioStage.POSTPROCESS,
                            AioStagePhase.AFTER,
                        )
                    }),
                    fingerprint={"test": 1},
                )

            def create_session(self, context):
                del context
                return MetadataSession()

        with (
            patch.object(legacy_generation, "_load_aio_resources_from_input_context", return_value=("base_model", "base_clip", "vae")),
            patch.object(legacy_generation, "_apply_aio_lora_stack", return_value=("lora_model", "lora_clip", [{"name": "a"}])),
            patch.object(legacy_generation, "_apply_aio_stage_model_patch_plan", return_value="patched_model"),
            patch.object(legacy_generation, "_advanced_outputs_from_prompt_data", return_value=("p", "n", "q", "qn", False, False, "", "", 512, 768)),
            patch.object(legacy_generation, "_encode_prompt_data_positive_conditioning", return_value="positive"),
            patch_comfy_helper(aio_nodes, "_encode_with_comfy_clip", return_value="negative"),
            patch.object(legacy_generation, "_generate_empty_latent_with_comfy", return_value="latent_image"),
            patch.object(legacy_generation, "_sample_latent_with_aio_backend", return_value="latent"),
            patch.object(legacy_generation, "_decode_latent_with_comfy", return_value="image"),
            patch.object(legacy_generation, "_save_image_with_image_saver", return_value={"ui": {"images": [{"filename": "preview.webp"}]}}),
            patch.object(legacy_generation, "_cleanup_aio_ephemeral_model"),
        ):
            result = aio_nodes.EasyUseAnimaAIOGenerator().generate(
                context,
                generation_settings=json.dumps({"save": {"enabled": True}}),
                lora_stack=[("a.safetensors", 1.0, 1.0)],
                aio_hook=MetadataHook(),
            )

        self.assertEqual(result["ui"]["images"][0]["filename"], "preview.webp")
        self.assertEqual(result["ui"]["easyuse_anima_preview"][0]["filename"], "preview.webp")
        self.assertEqual(result["ui"]["sampler_backend"], ["comfy_ksampler"])
        self.assertIn("easyuse_anima_run_id", result["ui"])
        metadata = json.loads(result["result"][2])
        self.assertTrue(
            metadata["extensions"]["hook_data"]["tests.metadata#0"]["integration"]
        )

    def test_generator_applies_first_pass_hook_model_and_sampler_overrides(self):
        context = self._context()
        lifecycle = []

        class SamplingSession(AioHookSessionBase):
            def before_stage(self, event):
                lifecycle.append(("before", event.state.model))
                return AioHookPatch(
                    model="third_party_model",
                    settings={
                        "sampler": {
                            "steps": 18,
                            "cfg": 4.5,
                            "sampler_name": "euler",
                            "scheduler": "normal",
                            "denoise": 0.8,
                        }
                    },
                    metadata={"sampling_override": True},
                )

            def close(self):
                lifecycle.append(("close",))

        class SamplingHook:
            def describe(self):
                return AioHookDescriptor(
                    hook_id="tests.sampling",
                    hook_version="1",
                    points=frozenset({
                        AioHookPoint(
                            AioStage.FIRST_PASS,
                            AioStagePhase.BEFORE,
                        )
                    }),
                    fingerprint={"test": "sampling"},
                )

            def create_session(self, hook_context):
                lifecycle.append(("create", hook_context.request.node_id))
                return SamplingSession()

        with (
            patch.object(legacy_generation, "_load_aio_resources_from_input_context", return_value=("base_model", "base_clip", "vae")),
            patch.object(legacy_generation, "_apply_aio_lora_stack", return_value=("lora_model", "lora_clip", [])),
            patch.object(legacy_generation, "_apply_aio_stage_model_patch_plan", return_value="patched_model"),
            patch.object(legacy_generation, "_advanced_outputs_from_prompt_data", return_value=("p", "n", "q", "qn", False, False, "", "", 512, 768)),
            patch.object(legacy_generation, "_encode_prompt_data_positive_conditioning", return_value="positive"),
            patch_comfy_helper(aio_nodes, "_encode_with_comfy_clip", return_value="negative"),
            patch.object(legacy_generation, "_generate_empty_latent_with_comfy", return_value="latent_image"),
            patch.object(legacy_generation, "_sample_latent_with_aio_backend", return_value="latent") as sample,
            patch.object(legacy_generation, "_decode_latent_with_comfy", return_value="image"),
            patch.object(legacy_generation, "_save_image_with_image_saver", return_value={"ui": {"images": [{"filename": "hook.webp"}]}}),
            patch.object(legacy_generation, "_cleanup_aio_ephemeral_model"),
        ):
            result = aio_nodes.EasyUseAnimaAIOGenerator().generate(
                context,
                generation_settings=json.dumps({"save": {"enabled": True}}),
                aio_hook=SamplingHook(),
            )

        sampler = sample.call_args.args[5]
        self.assertEqual(sample.call_args.args[0], "third_party_model")
        self.assertEqual(
            {
                key: sampler[key]
                for key in (
                    "steps",
                    "cfg",
                    "sampler_name",
                    "scheduler",
                    "denoise",
                )
            },
            {
                "steps": 18,
                "cfg": 4.5,
                "sampler_name": "euler",
                "scheduler": "normal",
                "denoise": 0.8,
            },
        )
        self.assertEqual(
            lifecycle,
            [("create", None), ("before", "patched_model"), ("close",)],
        )
        metadata = json.loads(result["result"][2])
        self.assertTrue(
            metadata["extensions"]["hook_data"]["tests.sampling#0"][
                "sampling_override"
            ]
        )

    def test_generator_reencodes_first_pass_when_decoded_image_size_needs_correction(self):
        context = self._context()

        with (
            patch.object(legacy_generation, "_load_aio_resources_from_input_context", return_value=("base_model", "base_clip", "vae")),
            patch.object(legacy_generation, "_apply_aio_lora_stack", return_value=("lora_model", "lora_clip", [])),
            patch.object(legacy_generation, "_apply_aio_stage_model_patch_plan", return_value="patched_model"),
            patch.object(legacy_generation, "_advanced_outputs_from_prompt_data", return_value=("p", "n", "q", "qn", False, False, "", "", 512, 768)),
            patch.object(legacy_generation, "_encode_prompt_data_positive_conditioning", return_value="positive"),
            patch_comfy_helper(aio_nodes, "_encode_with_comfy_clip", return_value="negative"),
            patch.object(legacy_generation, "_generate_empty_latent_with_comfy", return_value="latent_image"),
            patch.object(legacy_generation, "_sample_latent_with_aio_backend", return_value="latent"),
            patch.object(legacy_generation, "_decode_latent_with_comfy", return_value="undersized_image"),
            patch.object(legacy_generation, "_resize_image_to_size_if_needed", return_value=("corrected_image", True)) as resize,
            patch.object(legacy_generation, "_encode_image_with_comfy_vae", return_value="corrected_latent") as encode,
            patch.object(legacy_generation, "_run_aio_highres_stage", return_value=("corrected_latent", "corrected_image", 512, 768, {"enabled": False})),
            patch.object(legacy_generation, "_save_image_with_image_saver", return_value={"ui": {"images": [{"filename": "final.webp"}]}}),
            patch.object(legacy_generation, "_cleanup_aio_ephemeral_model"),
        ):
            result = aio_nodes.EasyUseAnimaAIOGenerator().generate(
                context,
                generation_settings=json.dumps({
                    "save": {
                        "enabled": True,
                    },
                }),
                unique_id=201,
            )

        self.assertEqual(result["result"][0], "corrected_image")
        self.assertEqual(result["result"][1], "corrected_latent")
        self.assertEqual(resize.call_args.args[1:3], (512, 768))
        self.assertEqual(encode.call_args.args, ("vae", "corrected_image"))

    def test_generator_sampler_backend_applies_only_selected_model_path(self):
        cases = (
            ("comfy_ksampler", "sampler_patch_model", True, True, False),
            ("spectrum_mod_guidance_advanced", "patched_model", False, False, True),
            ("spectrum_spd_speed", "mod_guidance_model", True, False, False),
        )

        for index, (backend, expected_model, expect_standalone_mod, expect_comfy_patch, expect_internal_mod) in enumerate(cases):
            with self.subTest(backend=backend):
                first_pass_cache._clear_aio_first_pass_cache()
                context = self._context()

                with (
                    patch.object(legacy_generation, "_load_aio_resources_from_input_context", return_value=("base_model", "base_clip", "vae")),
                    patch.object(legacy_generation, "_apply_aio_lora_stack", return_value=("lora_model", "lora_clip", [])),
            patch.object(legacy_generation, "_apply_aio_stage_model_patch_plan", return_value="patched_model"),
                    patch.object(legacy_generation, "_advanced_outputs_from_prompt_data", return_value=("p", "n", "q", "qn", True, False, "", "", 512, 768)),
                    patch.object(legacy_generation, "_encode_prompt_data_positive_conditioning", return_value="positive"),
                    patch_comfy_helper(aio_nodes, "_encode_with_comfy_clip", return_value="negative"),
                    patch.object(legacy_generation, "_generate_empty_latent_with_comfy", return_value="latent_image"),
                    patch.object(legacy_generation, "_apply_spectrum_anima_mod_guidance", return_value="mod_guidance_model") as standalone_mod,
                    patch.object(legacy_generation, "_apply_aio_spectrum_model_patches_for_comfy_sampler", return_value="sampler_patch_model") as comfy_patch,
                    patch.object(legacy_generation, "_sample_latent_with_aio_backend", return_value="latent") as sample,
                    patch.object(legacy_generation, "_decode_latent_with_comfy", return_value="image"),
                    patch.object(legacy_generation, "_save_image_with_image_saver", return_value={"ui": {"images": [{"filename": "final.webp"}]}}),
                    patch.object(legacy_generation, "_cleanup_aio_ephemeral_model"),
                ):
                    result = aio_nodes.EasyUseAnimaAIOGenerator().generate(
                        context,
                        generation_settings=json.dumps({
                            "sampler": {
                                "backend": backend,
                                "spectrum": {
                                    "enabled": True,
                                },
                                "dit_corrections": {
                                    "enabled": True,
                                },
                            },
                            "save": {
                                "enabled": True,
                            },
                        }),
                        unique_id=200 + index,
                    )

                self.assertEqual(result["ui"]["sampler_backend"], [backend])
                self.assertEqual(sample.call_args.args[0], expected_model)
                self.assertEqual(sample.call_args.args[5]["backend"], backend)
                self.assertEqual(sample.call_args.args[7], expect_internal_mod)
                self.assertEqual(standalone_mod.called, expect_standalone_mod)
                self.assertEqual(comfy_patch.called, expect_comfy_patch)
                if expect_comfy_patch:
                    self.assertEqual(comfy_patch.call_args.args[0], "mod_guidance_model")

    def test_generator_integrated_sampler_reuses_integrated_mod_guidance_for_highres_stage(self):
        context = self._context()
        stage_sampler = generation_normalization._normalize_aio_generation_settings("{}")["sampler"]

        with (
            patch.object(legacy_generation, "_load_aio_resources_from_input_context", return_value=("base_model", "base_clip", "vae")),
            patch.object(legacy_generation, "_apply_aio_lora_stack", return_value=("lora_model", "lora_clip", [])),
            patch.object(legacy_generation, "_apply_aio_stage_model_patch_plan", return_value="patched_model"),
            patch.object(legacy_generation, "_advanced_outputs_from_prompt_data", return_value=("p", "n", "q", "qn", True, False, "", "", 512, 768)),
            patch.object(legacy_generation, "_encode_prompt_data_positive_conditioning", return_value="positive"),
            patch_comfy_helper(aio_nodes, "_encode_with_comfy_clip", return_value="negative"),
            patch.object(legacy_generation, "_generate_empty_latent_with_comfy", return_value="latent_image"),
            patch.object(legacy_generation, "_apply_spectrum_anima_mod_guidance", return_value="mod_guidance_model") as standalone_mod,
            patch.object(legacy_generation, "_apply_aio_spectrum_model_patches_for_comfy_sampler") as comfy_patch,
            patch.object(legacy_generation, "_sample_latent_with_aio_backend", return_value="latent") as sample,
            patch.object(legacy_generation, "_decode_latent_with_comfy", return_value="image"),
            patch.object(legacy_generation, "_run_aio_highres_stage", return_value=("high_latent", "high_image", 640, 960, {"enabled": True, "sampler": stage_sampler})) as highres,
            patch.object(legacy_generation, "_save_image_with_image_saver", return_value={"ui": {"images": [{"filename": "final.webp"}]}}),
            patch.object(legacy_generation, "_cleanup_aio_ephemeral_model"),
        ):
            aio_nodes.EasyUseAnimaAIOGenerator().generate(
                context,
                generation_settings=json.dumps({
                    "sampler": {
                        "backend": "spectrum_mod_guidance_advanced",
                    },
                    "highres": {
                        "enabled": True,
                    },
                    "save": {
                        "enabled": True,
                    },
                }),
                unique_id=210,
        )

        standalone_mod.assert_not_called()
        comfy_patch.assert_not_called()
        self.assertEqual(sample.call_args.args[0], "patched_model")
        self.assertEqual(highres.call_args.args[0], "patched_model")
        self.assertEqual(highres.call_args.args[12], True)

    def test_generator_integrated_sampler_keeps_standalone_mod_guidance_for_detailer_stage(self):
        context = self._context()

        with (
            patch.object(legacy_generation, "_load_aio_resources_from_input_context", return_value=("base_model", "base_clip", "vae")),
            patch.object(legacy_generation, "_apply_aio_lora_stack", return_value=("lora_model", "lora_clip", [])),
            patch.object(legacy_generation, "_apply_aio_stage_model_patch_plan", return_value="patched_model"),
            patch.object(legacy_generation, "_advanced_outputs_from_prompt_data", return_value=("p", "n", "q", "qn", True, False, "", "", 512, 768)),
            patch.object(legacy_generation, "_encode_prompt_data_positive_conditioning", return_value="positive"),
            patch_comfy_helper(aio_nodes, "_encode_with_comfy_clip", return_value="negative"),
            patch.object(legacy_generation, "_generate_empty_latent_with_comfy", return_value="latent_image"),
            patch.object(legacy_generation, "_apply_spectrum_anima_mod_guidance", return_value="mod_guidance_model") as standalone_mod,
            patch.object(legacy_generation, "_apply_aio_spectrum_model_patches_for_comfy_sampler") as comfy_patch,
            patch.object(legacy_generation, "_sample_latent_with_aio_backend", return_value="latent") as sample,
            patch.object(legacy_generation, "_decode_latent_with_comfy", return_value="image"),
            patch.object(legacy_generation, "_run_aio_highres_stage", return_value=("latent", "image", 512, 768, {"enabled": False})),
            patch.object(legacy_generation, "_run_aio_detailer_stage", return_value=("detail_image", {"enabled": True})) as detailer,
            patch.object(legacy_generation, "_save_image_with_image_saver", return_value={"ui": {"images": [{"filename": "final.webp"}]}}),
            patch.object(legacy_generation, "_cleanup_aio_ephemeral_model"),
        ):
            aio_nodes.EasyUseAnimaAIOGenerator().generate(
                context,
                generation_settings=json.dumps({
                    "sampler": {
                        "backend": "spectrum_mod_guidance_advanced",
                    },
                    "detailer": {
                        "enabled": True,
                        "face": {
                            "enabled": True,
                        },
                    },
                    "save": {
                        "enabled": True,
                    },
                }),
                unique_id=211,
            )

        standalone_mod.assert_called_once()
        comfy_patch.assert_not_called()
        self.assertEqual(sample.call_args.args[0], "patched_model")
        self.assertEqual(detailer.call_args.args[0], "mod_guidance_model")

    def test_generator_runs_postprocess_after_upscale_before_save(self):
        context = self._context()
        events = []
        upscaled_image = AIOFinalUpscaleStageTests._Image(1024, 1536)

        def fake_detailer(*_args):
            events.append("detailer")
            return "detail_image", {"enabled": True}

        def fake_upscale(*_args, **_kwargs):
            events.append("upscale")
            return upscaled_image, {"enabled": True, "backend": "usdu", "width": 1024, "height": 1536}

        def fake_postprocess(*_args, **_kwargs):
            events.append("postprocess")
            return AIOFinalUpscaleStageTests._Image(900, 1350), {
                "enabled": True,
                "width": 900,
                "height": 1350,
                "fit": {
                    "applied": True,
                },
            }

        def fake_save(*_args, **_kwargs):
            events.append("save")
            return {"ui": {"images": [{"filename": "final.webp"}]}}

        with (
            patch.object(legacy_generation, "_load_aio_resources_from_input_context", return_value=("base_model", "base_clip", "vae")),
            patch.object(legacy_generation, "_apply_aio_lora_stack", return_value=("lora_model", "lora_clip", [])),
            patch.object(legacy_generation, "_apply_aio_stage_model_patch_plan", return_value="patched_model"),
            patch.object(legacy_generation, "_advanced_outputs_from_prompt_data", return_value=("p", "n", "q", "qn", False, False, "", "", 512, 768)),
            patch.object(legacy_generation, "_encode_prompt_data_positive_conditioning", return_value="positive"),
            patch_comfy_helper(aio_nodes, "_encode_with_comfy_clip", return_value="negative"),
            patch.object(legacy_generation, "_generate_empty_latent_with_comfy", return_value="latent_image"),
            patch.object(legacy_generation, "_sample_latent_with_aio_backend", return_value="latent"),
            patch.object(legacy_generation, "_decode_latent_with_comfy", return_value="first_image"),
            patch.object(legacy_generation, "_run_aio_highres_stage", return_value=("latent", "first_image", 512, 768, {"enabled": False})),
            patch.object(legacy_generation, "_run_aio_detailer_stage", side_effect=fake_detailer),
            patch.object(legacy_generation, "_run_aio_upscale_stage", side_effect=fake_upscale) as upscale,
            patch.object(legacy_generation, "_run_aio_postprocess_stage", side_effect=fake_postprocess) as postprocess,
            patch.object(legacy_generation, "_encode_image_with_comfy_vae", side_effect=["upscaled_latent", "postprocess_latent"]) as encode,
            patch.object(legacy_generation, "_save_image_with_image_saver", side_effect=fake_save) as save,
            patch.object(legacy_generation, "_cleanup_aio_ephemeral_model"),
        ):
            result = aio_nodes.EasyUseAnimaAIOGenerator().generate(
                context,
                generation_settings=json.dumps({
                    "detailer": {
                        "enabled": True,
                        "face": {
                            "enabled": True,
                        },
                    },
                    "upscale": {
                        "enabled": True,
                        "backend": "usdu",
                    },
                    "postprocess": {
                        "enabled": True,
                    },
                    "save": {
                        "enabled": True,
                    },
                }),
                unique_id=213,
            )

        self.assertEqual(events, ["detailer", "upscale", "postprocess", "save"])
        self.assertIsInstance(result["result"][0], AIOFinalUpscaleStageTests._Image)
        self.assertEqual(result["result"][1], "postprocess_latent")
        self.assertEqual(upscale.call_args.args[5], "detail_image")
        self.assertIs(postprocess.call_args.args[0], upscaled_image)
        self.assertEqual(encode.call_count, 2)
        self.assertEqual(save.call_args.kwargs["width"], 900)
        self.assertEqual(save.call_args.kwargs["height"], 1350)

    def test_generator_save_metadata_uses_first_pass_sampler_and_final_size(self):
        context = self._context()
        save_calls = []
        highres_sampler = generation_normalization._normalize_aio_generation_settings(json.dumps({
            "sampler": {
                "seed": 999,
                "steps": 12,
                "cfg": 3.0,
                "sampler_name": "ddim",
                "scheduler": "simple",
                "denoise": 0.4,
            }
        }))["sampler"]

        def fake_save(*args, **kwargs):
            save_calls.append(kwargs)
            return {"ui": {"images": [{"filename": "final.webp"}]}}

        with (
            patch.object(legacy_generation, "_load_aio_resources_from_input_context", return_value=("base_model", "base_clip", "vae")),
            patch.object(legacy_generation, "_apply_aio_lora_stack", return_value=("lora_model", "lora_clip", [{"name": "style/foo.safetensors", "strength_model": 0.8}])),
            patch.object(legacy_generation, "_apply_aio_stage_model_patch_plan", return_value="patched_model"),
            patch.object(legacy_generation, "_advanced_outputs_from_prompt_data", return_value=("p", "n", "q", "qn", False, False, "", "", 512, 768)),
            patch.object(legacy_generation, "_encode_prompt_data_positive_conditioning", return_value="positive"),
            patch_comfy_helper(aio_nodes, "_encode_with_comfy_clip", return_value="negative"),
            patch.object(legacy_generation, "_generate_empty_latent_with_comfy", return_value="latent_image"),
            patch.object(legacy_generation, "_sample_latent_with_aio_backend", return_value="latent"),
            patch.object(legacy_generation, "_decode_latent_with_comfy", return_value="image"),
            patch.object(legacy_generation, "_run_aio_highres_stage", return_value=("high_latent", "high_image", 1024, 1536, {"enabled": True, "sampler": highres_sampler})),
            patch.object(legacy_generation, "_save_image_with_image_saver", side_effect=fake_save),
            patch.object(legacy_generation, "_cleanup_aio_ephemeral_model"),
        ):
            aio_nodes.EasyUseAnimaAIOGenerator().generate(
                context,
                generation_settings=json.dumps({
                    "sampler": {
                        "seed": 123,
                        "steps": 32,
                        "cfg": 5.5,
                        "sampler_name": "euler_ancestral",
                        "scheduler": "sgm_uniform",
                        "denoise": 1.0,
                    },
                    "highres": {
                        "enabled": True,
                    },
                    "save": {
                        "enabled": True,
                    },
                }),
                unique_id=211,
            )

        self.assertEqual(save_calls[0]["width"], 1024)
        self.assertEqual(save_calls[0]["height"], 1536)
        self.assertEqual(save_calls[0]["sampler_settings"]["seed"], 123)
        self.assertEqual(save_calls[0]["sampler_settings"]["steps"], 32)
        self.assertEqual(save_calls[0]["sampler_settings"]["cfg"], 5.5)
        self.assertEqual(save_calls[0]["sampler_settings"]["sampler_name"], "euler_ancestral")
        self.assertEqual(save_calls[0]["sampler_settings"]["scheduler"], "sgm_uniform")
        self.assertEqual(save_calls[0]["sampler_settings"]["denoise"], 1.0)
        self.assertEqual(save_calls[0]["applied_loras"], [{"name": "style/foo.safetensors", "strength_model": 0.8}])

    def test_generator_image_saver_uses_metadata_prompt_outputs_with_mod_guidance(self):
        context = self._context()
        save_calls = []

        def fake_save(*args, **kwargs):
            save_calls.append(kwargs)
            return {"ui": {"images": [{"filename": "final.webp"}]}}

        with (
            patch.object(legacy_generation, "_load_aio_resources_from_input_context", return_value=("base_model", "base_clip", "vae")),
            patch.object(legacy_generation, "_apply_aio_lora_stack", return_value=("lora_model", "lora_clip", [])),
            patch.object(legacy_generation, "_apply_aio_stage_model_patch_plan", return_value="patched_model"),
            patch.object(
                legacy_generation,
                "_advanced_outputs_from_prompt_data",
                return_value=(
                    "generation positive",
                    "generation negative",
                    "quality for mod guidance",
                    "negative quality for mod guidance",
                    True,
                    True,
                    "metadata positive with quality",
                    "metadata negative with quality",
                    512,
                    768,
                ),
            ),
            patch.object(legacy_generation, "_encode_prompt_data_positive_conditioning", return_value="positive") as encode_positive,
            patch_comfy_helper(
                aio_nodes,
                "_encode_with_comfy_clip",
                return_value="negative",
            ) as encode_negative,
            patch.object(legacy_generation, "_generate_empty_latent_with_comfy", return_value="latent_image"),
            patch.object(legacy_generation, "_apply_spectrum_anima_mod_guidance", return_value="mod_guidance_model"),
            patch.object(legacy_generation, "_apply_aio_spectrum_model_patches_for_comfy_sampler", return_value="sampler_patch_model"),
            patch.object(legacy_generation, "_sample_latent_with_aio_backend", return_value="latent") as sample,
            patch.object(legacy_generation, "_decode_latent_with_comfy", return_value="image"),
            patch.object(legacy_generation, "_run_aio_highres_stage", return_value=("latent", "image", 512, 768, {"enabled": False})),
            patch.object(legacy_generation, "_save_image_with_image_saver", side_effect=fake_save),
            patch.object(legacy_generation, "_cleanup_aio_ephemeral_model"),
        ):
            aio_nodes.EasyUseAnimaAIOGenerator().generate(
                context,
                generation_settings=json.dumps({
                    "save": {
                        "enabled": True,
                    },
                }),
                unique_id=212,
            )

        self.assertEqual(encode_positive.call_args.args[2], "generation positive")
        self.assertEqual(encode_negative.call_args.args[1], "generation negative")
        self.assertEqual(sample.call_args.args[8], "quality for mod guidance")
        self.assertEqual(sample.call_args.args[9], "negative quality for mod guidance")
        self.assertEqual(save_calls[0]["positive_prompt"], "metadata positive with quality")
        self.assertEqual(save_calls[0]["negative_prompt"], "metadata negative with quality")

    def test_generator_reuses_first_pass_cache_when_only_later_stages_change(self):
        context = {
            "prompt_data": {},
            "resource_info": {
                "unet_name": "anima_model.safetensors",
                "vae_name": "anima_vae.safetensors",
                "clip_name": "anima_clip.safetensors",
                "clip_type": "qwen_image",
            },
            "input_settings": {},
        }

        with (
            patch.object(legacy_generation, "_load_aio_resources_from_input_context", return_value=("base_model", "base_clip", "vae")),
            patch.object(legacy_generation, "_apply_aio_lora_stack", return_value=("lora_model", "lora_clip", [])),
            patch.object(legacy_generation, "_apply_aio_stage_model_patch_plan", return_value="patched_model"),
            patch.object(legacy_generation, "_advanced_outputs_from_prompt_data", return_value=("p", "n", "q", "qn", False, False, "", "", 512, 768)),
            patch.object(legacy_generation, "_encode_prompt_data_positive_conditioning", return_value="positive"),
            patch_comfy_helper(aio_nodes, "_encode_with_comfy_clip", return_value="negative"),
            patch.object(legacy_generation, "_generate_empty_latent_with_comfy", return_value="latent_image") as empty_latent,
            patch.object(legacy_generation, "_sample_latent_with_aio_backend", return_value="latent") as sample,
            patch.object(legacy_generation, "_decode_latent_with_comfy", return_value="image") as decode,
            patch.object(legacy_generation, "_run_aio_highres_stage", side_effect=[
                ("high_latent_1", "high_image_1", 640, 960, {"enabled": True, "sampler": generation_normalization._normalize_aio_generation_settings("{}")["sampler"]}),
                ("high_latent_2", "high_image_2", 768, 1152, {"enabled": True, "sampler": generation_normalization._normalize_aio_generation_settings("{}")["sampler"]}),
            ]) as highres,
            patch.object(legacy_generation, "_save_image_with_image_saver", return_value={"ui": {"images": [{"filename": "final.webp"}]}}),
            patch.object(legacy_generation, "_cleanup_aio_ephemeral_model"),
        ):
            generator = aio_nodes.EasyUseAnimaAIOGenerator()
            for scale in (1.25, 1.5):
                generator.generate(
                    context,
                    generation_settings=json.dumps({
                        "sampler": {
                            "seed": 123,
                        },
                        "highres": {
                            "enabled": True,
                            "scale_by": scale,
                        },
                    }),
                    unique_id=86,
                )

        self.assertEqual(empty_latent.call_count, 1)
        self.assertEqual(sample.call_count, 1)
        self.assertEqual(decode.call_count, 1)
        self.assertEqual(highres.call_count, 2)

    def test_generator_preview_avoids_duplicate_highres_and_final_images(self):
        context = {
            "prompt_data": {},
            "resource_info": {
                "unet_name": "anima_model.safetensors",
                "vae_name": "anima_vae.safetensors",
                "clip_name": "anima_clip.safetensors",
                "clip_type": "qwen_image",
            },
            "input_settings": {},
        }
        preview_calls = []

        def fake_preview(image, stage, **kwargs):
            preview_calls.append((stage, image))
            return [{"filename": f"{stage}.png", "type": "temp", "stage": stage, "label": stage}]

        with (
            patch.object(legacy_generation, "_load_aio_resources_from_input_context", return_value=("base_model", "base_clip", "vae")),
            patch.object(legacy_generation, "_apply_aio_lora_stack", return_value=("lora_model", "lora_clip", [])),
            patch.object(legacy_generation, "_apply_aio_stage_model_patch_plan", return_value="patched_model"),
            patch.object(legacy_generation, "_advanced_outputs_from_prompt_data", return_value=("p", "n", "q", "qn", False, False, "", "", 512, 768)),
            patch.object(legacy_generation, "_encode_prompt_data_positive_conditioning", return_value="positive"),
            patch_comfy_helper(aio_nodes, "_encode_with_comfy_clip", return_value="negative"),
            patch.object(legacy_generation, "_generate_empty_latent_with_comfy", return_value="latent_image"),
            patch.object(legacy_generation, "_sample_latent_with_aio_backend", return_value="latent"),
            patch.object(legacy_generation, "_decode_latent_with_comfy", return_value="image"),
            patch.object(legacy_generation, "_run_aio_highres_stage", return_value=(
                "highres_latent",
                "highres_image",
                768,
                1024,
                {
                    "enabled": True,
                    "sampler": generation_normalization._normalize_aio_generation_settings("{}")["sampler"],
                },
            )),
            patch.object(legacy_generation, "_save_image_with_image_saver", return_value={"ui": {"images": [{"filename": "final.webp"}]}}),
            patch.object(legacy_generation, "_save_aio_temp_preview_image", side_effect=fake_preview),
            patch.object(legacy_generation, "_cleanup_aio_ephemeral_model"),
        ):
            result = aio_nodes.EasyUseAnimaAIOGenerator().generate(
                context,
                generation_settings=json.dumps({
                    "save": {"enabled": True},
                    "highres": {
                        "enabled": True,
                    },
                    "preview": {
                        "intermediate_images": True,
                        "compare_previous": True,
                        "image_feed": True,
                    },
                }),
            )

        self.assertEqual([item["stage"] for item in result["ui"]["images"]], ["final"])
        self.assertEqual(result["ui"]["images"][0]["filename"], "final.webp")
        self.assertEqual(preview_calls, [("first_pass", "image")])
        self.assertEqual(
            [item["stage"] for item in result["ui"]["easyuse_anima_preview"]],
            ["first_pass", "final"],
        )
        self.assertEqual(result["ui"]["easyuse_anima_preview"][1]["filename"], "final.webp")

    def test_generator_intermediate_preview_includes_first_pass_when_enabled(self):
        context = {
            "prompt_data": {},
            "resource_info": {
                "unet_name": "anima_model.safetensors",
                "vae_name": "anima_vae.safetensors",
                "clip_name": "anima_clip.safetensors",
                "clip_type": "qwen_image",
            },
            "input_settings": {},
        }
        preview_calls = []

        def fake_preview(image, stage, **kwargs):
            preview_calls.append((stage, image))
            return [{"filename": f"{stage}.webp", "type": "temp", "stage": stage, "label": stage}]

        with (
            patch.object(legacy_generation, "_load_aio_resources_from_input_context", return_value=("base_model", "base_clip", "vae")),
            patch.object(legacy_generation, "_apply_aio_lora_stack", return_value=("lora_model", "lora_clip", [])),
            patch.object(legacy_generation, "_apply_aio_stage_model_patch_plan", return_value="patched_model"),
            patch.object(legacy_generation, "_advanced_outputs_from_prompt_data", return_value=("p", "n", "q", "qn", False, False, "", "", 512, 768)),
            patch.object(legacy_generation, "_encode_prompt_data_positive_conditioning", return_value="positive"),
            patch_comfy_helper(aio_nodes, "_encode_with_comfy_clip", return_value="negative"),
            patch.object(legacy_generation, "_generate_empty_latent_with_comfy", return_value="latent_image"),
            patch.object(legacy_generation, "_sample_latent_with_aio_backend", return_value="latent"),
            patch.object(legacy_generation, "_decode_latent_with_comfy", return_value="image"),
            patch.object(legacy_generation, "_save_image_with_image_saver", return_value={"ui": {"images": [{"filename": "final.webp"}]}}),
            patch.object(legacy_generation, "_save_aio_temp_preview_image", side_effect=fake_preview),
            patch.object(legacy_generation, "_send_aio_preview_event") as send_preview_event,
            patch.object(legacy_generation, "_cleanup_aio_ephemeral_model"),
        ):
            result = aio_nodes.EasyUseAnimaAIOGenerator().generate(
                context,
                generation_settings=json.dumps({
                    "save": {"enabled": True},
                    "preview": {
                        "intermediate_images": True,
                        "compare_previous": True,
                        "image_feed": True,
                    },
                }),
                unique_id=86,
            )

        self.assertEqual(preview_calls, [("first_pass", "image")])
        send_preview_event.assert_called_once()
        self.assertEqual(send_preview_event.call_args.args[0], 86)
        self.assertEqual(send_preview_event.call_args.args[2], "first_pass")
        self.assertEqual(send_preview_event.call_args.args[3][0]["filename"], "first_pass.webp")
        self.assertEqual(
            [item["stage"] for item in result["ui"]["easyuse_anima_preview"]],
            ["first_pass", "final"],
        )


if __name__ == "__main__":
    unittest.main()
