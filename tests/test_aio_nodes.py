from __future__ import annotations

import json
import unittest
from unittest.mock import patch

import nodes


class AIONodeContractTests(unittest.TestCase):
    def test_input_node_contract_uses_dedicated_context_socket(self):
        required = nodes.EasyUseAnimaInput.INPUT_TYPES()["required"]

        self.assertIn(nodes.PROMPT_DATA_TYPE, required)
        self.assertIn("unet_name", required)
        self.assertIn("vae_name", required)
        self.assertIn("clip_name", required)
        self.assertIn("clip_type", required)
        self.assertIn("input_settings", required)
        self.assertEqual(nodes.EasyUseAnimaInput.RETURN_TYPES, (nodes.EASY_USE_ANIMA_INPUT_TYPE,))
        self.assertEqual(nodes.EasyUseAnimaInput.RETURN_NAMES, ("easy use anima input",))

    def test_generator_contract_keeps_mutable_settings_in_one_json_widget(self):
        required = nodes.EasyUseAnimaAIOGenerator.INPUT_TYPES()["required"]

        self.assertEqual(
            required["easy_use_anima_input"][0],
            nodes.EASY_USE_ANIMA_INPUT_TYPE,
        )
        self.assertEqual(
            nodes.EasyUseAnimaAIOGenerator.INPUT_TYPES()["optional"]["lora_stack"][0],
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
            nodes.EasyUseAnimaAIOGenerator.RETURN_TYPES,
            ("IMAGE", "LATENT", "STRING"),
        )
        self.assertTrue(nodes.EasyUseAnimaAIOGenerator.OUTPUT_NODE)
        self.assertEqual(
            nodes.EasyUseAnimaAIOGenerator.RETURN_NAMES,
            ("image", "latent", "metadata_json"),
        )

    def test_input_context_is_serializable_and_does_not_embed_model_objects(self):
        context = nodes.EasyUseAnimaInput().build(
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
        settings = nodes._normalize_aio_input_settings(json.dumps({
            "version": 1,
            "resources": {
                "future_loader_mode": "external",
            },
            "future_root": {
                "enabled": True,
            },
        }))

        self.assertEqual(settings["schema"], nodes.EASY_USE_ANIMA_INPUT_SCHEMA)
        self.assertEqual(settings["resources"]["loader_mode"], "split")
        self.assertEqual(settings["resources"]["clip_loader"], "single")
        self.assertEqual(settings["resources"]["unet_weight_dtype"], "default")
        self.assertEqual(settings["resources"]["clip_device"], "default")
        self.assertEqual(settings["resources"]["future_loader_mode"], "external")
        self.assertTrue(settings["future_root"]["enabled"])

    def test_generation_settings_default_merge_preserves_unknown_future_keys(self):
        settings = nodes._normalize_aio_generation_settings(json.dumps({
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

        self.assertEqual(settings["schema"], nodes.AIO_GENERATION_SETTINGS_SCHEMA)
        self.assertEqual(settings["sampler"]["backend"], "comfy_ksampler")
        self.assertEqual(settings["sampler"]["seed"], nodes.AIO_SPECIAL_SEED_RANDOM)
        self.assertEqual(settings["sampler"]["steps"], 1)
        self.assertEqual(settings["sampler"]["seed_after_generate"], nodes.SEED_CONTROL_FIXED)
        self.assertEqual(settings["sampler"]["future_sampler_key"], "kept")
        self.assertNotIn("enabled", settings["model_patches"]["aura_flow"])
        self.assertEqual(settings["model_patches"]["aura_flow"]["shift"], 3.0)
        self.assertEqual(settings["model_patches"]["kj"]["torch_compile"]["mode"], "max-autotune-no-cudagraphs")
        self.assertTrue(settings["save"]["enabled"])
        self.assertEqual(settings["save"]["backend"], "image_saver")
        self.assertNotIn("filename_prefix", settings["save"])
        self.assertEqual(settings["save"]["image_saver"]["extension"], "webp")
        self.assertEqual(settings["save"]["image_saver"]["quality_jpeg_or_webp"], 97)
        self.assertEqual(settings["save"]["image_saver"]["additional_hash_bundles"], [])
        self.assertEqual(settings["save"]["image_saver"]["civitai_hash_fetchers"], [])
        self.assertNotIn("show_preview", settings["save"]["image_saver"])
        self.assertFalse(settings["preview"]["intermediate_images"])
        self.assertFalse(settings["preview"]["compare_previous"])
        self.assertTrue(settings["preview"]["image_feed"])
        self.assertEqual(settings["preview"]["feed_count"], 12)
        self.assertEqual(settings["future_section"]["value"], 42)

    def test_legacy_filename_prefix_is_not_kept_in_generation_settings(self):
        settings = nodes._normalize_aio_generation_settings(json.dumps({
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
        settings = nodes._normalize_aio_generation_settings(json.dumps({
            "save": {
                "backend": "comfy_save_image",
                "image_saver": {
                    "filename": "frame_%time",
                    "path": "EasyUseAnima/Test",
                },
            },
        }))

        self.assertEqual(nodes._aio_save_filename_prefix(settings["save"]), "EasyUseAnima/Test/frame_%time")

    def test_image_saver_show_preview_is_not_kept_in_aio_settings(self):
        settings = nodes._normalize_aio_generation_settings(json.dumps({
            "save": {
                "image_saver": {
                    "show_preview": True,
                },
            },
        }))

        self.assertNotIn("show_preview", settings["save"]["image_saver"])

    def test_preview_compare_can_use_feed_history_without_intermediate_previews(self):
        settings = nodes._normalize_aio_generation_settings(json.dumps({
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
        settings = nodes._normalize_aio_generation_settings("{")

        self.assertEqual(settings["schema"], nodes.AIO_GENERATION_SETTINGS_SCHEMA)
        self.assertEqual(settings["version"], nodes.AIO_GENERATION_SETTINGS_VERSION)
        self.assertEqual(settings["mode"], "txt2img")
        self.assertEqual(settings["sampler"]["steps"], 28)
        self.assertEqual(settings["sampler"]["seed"], nodes.AIO_SPECIAL_SEED_RANDOM)
        self.assertTrue(settings["save"]["enabled"])

    def test_aura_flow_is_shift_only_and_always_normalized_on(self):
        settings = nodes._normalize_aio_generation_settings(json.dumps({
            "model_patches": {
                "aura_flow": {
                    "enabled": False,
                    "shift": 4.5,
                },
            },
        }))

        self.assertNotIn("enabled", settings["model_patches"]["aura_flow"])
        self.assertEqual(settings["model_patches"]["aura_flow"]["shift"], 4.5)

    def test_main_sampler_values_are_clamped_to_ui_ranges(self):
        settings = nodes._normalize_aio_generation_settings(json.dumps({
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

        self.assertEqual(settings["sampler"]["steps"], 75)
        self.assertEqual(settings["sampler"]["cfg"], 10.0)
        self.assertEqual(settings["model_patches"]["aura_flow"]["shift"], 10.0)

        settings = nodes._normalize_aio_generation_settings(json.dumps({
            "sampler": {
                "cfg": 0,
            },
            "model_patches": {
                "aura_flow": {
                    "shift": 0,
                },
            },
        }))

        self.assertEqual(settings["sampler"]["cfg"], 1.0)
        self.assertEqual(settings["model_patches"]["aura_flow"]["shift"], 1.0)

    def test_default_settings_json_is_compact_dict_storage(self):
        value = nodes._aio_generation_settings_json()

        self.assertNotIn("\n", value)
        self.assertEqual(json.loads(value)["schema"], nodes.AIO_GENERATION_SETTINGS_SCHEMA)

    def test_sampler_backend_is_limited_to_three_supported_paths(self):
        settings = nodes._normalize_aio_generation_settings(json.dumps({
            "sampler": {
                "backend": "not_supported",
            },
        }))

        self.assertEqual(settings["sampler"]["backend"], "comfy_ksampler")

    def test_aio_seed_accepts_rgthree_special_values(self):
        settings = nodes._normalize_aio_generation_settings(json.dumps({
            "sampler": {
                "seed": nodes.AIO_SPECIAL_SEED_RANDOM,
            },
        }))
        self.assertEqual(settings["sampler"]["seed"], nodes.AIO_SPECIAL_SEED_RANDOM)

        settings = nodes._normalize_aio_generation_settings(json.dumps({
            "sampler": {
                "seed": nodes.AIO_SPECIAL_SEED_INCREMENT,
            },
        }))
        self.assertEqual(settings["sampler"]["seed"], nodes.AIO_SPECIAL_SEED_INCREMENT)

        settings = nodes._normalize_aio_generation_settings(json.dumps({
            "sampler": {
                "seed": -999,
            },
        }))
        self.assertEqual(settings["sampler"]["seed"], nodes.AIO_SPECIAL_SEED_DECREMENT)

    def test_runtime_special_seed_resolves_to_concrete_seed(self):
        with patch.object(nodes.random, "randint", return_value=123456):
            self.assertEqual(
                nodes._resolve_aio_runtime_seed(nodes.AIO_SPECIAL_SEED_RANDOM),
                123456,
            )

    def test_generation_scheduler_uses_comfy_ksampler_choices(self):
        with patch.object(nodes, "_comfy_scheduler_names", return_value=["normal", "sgm_uniform"]):
            settings = nodes._normalize_aio_generation_settings(json.dumps({
                "sampler": {
                    "scheduler": "er_sde",
                },
            }))

        self.assertEqual(settings["sampler"]["scheduler"], "normal")


class AIOImageSaverDependencyTests(unittest.TestCase):
    def test_missing_image_saver_dependency_names_required_node_pack(self):
        with patch.object(nodes, "_find_comfy_node_class", return_value=None):
            with self.assertRaisesRegex(RuntimeError, "ComfyUI-Image-Saver"):
                nodes._save_image_with_image_saver(
                    images=None,
                    save_settings=nodes._normalize_aio_generation_settings("{}")["save"],
                    positive_prompt="positive",
                    negative_prompt="negative",
                    width=512,
                    height=512,
                    sampler_settings=nodes.AIO_GENERATION_DEFAULT_SETTINGS["sampler"],
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

        with patch.object(nodes, "_find_comfy_node_class", return_value=FakeCivitaiHashFetcher):
            result = nodes._aio_image_saver_additional_hashes({
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

    def test_image_saver_save_files_receives_workflow_metadata_flags(self):
        calls = []

        class FakeImageSaver:
            def save_files(self, **kwargs):
                calls.append(kwargs)
                return {"ui": {"images": [{"filename": "preview.webp"}]}}

        class FakeCivitaiHashFetcher:
            def get_autov3_hash(self, username, model_name, version=""):
                return ("ABCDEF1234",)

        settings = nodes._normalize_aio_generation_settings(json.dumps({
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

        with patch.object(nodes, "_find_comfy_node_class", side_effect=fake_find):
            result = nodes._save_image_with_image_saver(
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
        self.assertFalse(calls[0]["show_preview"])
        self.assertEqual(calls[0]["modelname"], "anima")
        self.assertEqual(calls[0]["width"], 768)
        self.assertEqual(calls[0]["height"], 1024)
        self.assertEqual(
            calls[0]["additional_hashes"],
            "Base:AAAAAAAA,LoraA:BBBBBBBB:0.8,CCCCCCCC:1.0,Anima All in One workflow:ABCDEF1234",
        )


class AIOLoraStackTests(unittest.TestCase):
    def test_lora_stack_is_normalized_from_tuple_and_dict_entries(self):
        stack = nodes._normalize_aio_lora_stack([
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

        with patch.object(nodes, "_find_comfy_node_class", return_value=FakeLoraLoader):
            model, clip, applied = nodes._apply_aio_lora_stack(
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

        settings = nodes._normalize_aio_generation_settings(json.dumps({
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

        with patch.object(nodes, "_find_comfy_node_class", side_effect=fake_find):
            result = nodes._apply_aio_spectrum_model_patches_for_comfy_sampler(
                "base_model",
                "clip",
                "positive",
                settings["sampler"],
            )

        self.assertEqual(result, "spectrum_model")
        self.assertEqual([call[0] for call in calls], ["correction", "spectrum"])
        self.assertEqual(calls[0][1], "base_model")
        self.assertEqual(calls[1][1], "corrected_model")
        self.assertEqual(calls[1][2][-1], "strict")

    def test_missing_spectrum_model_patch_dependency_names_required_node_pack(self):
        settings = nodes._normalize_aio_generation_settings(json.dumps({
            "sampler": {
                "backend": "comfy_ksampler",
                "spectrum": {
                    "enabled": True,
                },
            },
        }))

        with patch.object(nodes, "_find_comfy_node_class", return_value=None):
            with self.assertRaisesRegex(RuntimeError, "ComfyUI-Spectrum-KSampler"):
                nodes._apply_aio_spectrum_model_patches_for_comfy_sampler(
                    "base_model",
                    "clip",
                    "positive",
                    settings["sampler"],
                )

    def test_missing_spectrum_sampler_dependency_names_required_node_pack(self):
        settings = nodes._normalize_aio_generation_settings(json.dumps({
            "sampler": {
                "backend": "spectrum_mod_guidance_advanced",
            },
        }))

        with patch.object(nodes, "_find_comfy_node_class", return_value=None):
            with self.assertRaisesRegex(RuntimeError, "ComfyUI-Spectrum-KSampler"):
                nodes._sample_latent_with_aio_backend(
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

    def test_sampler_backend_dispatches_only_selected_path(self):
        settings = nodes._normalize_aio_generation_settings("{}")
        settings["sampler"]["backend"] = "comfy_ksampler"
        calls = []

        with (
            patch.object(nodes, "_sample_latent_with_comfy", side_effect=lambda *args: calls.append("comfy") or "latent"),
            patch.object(nodes, "_sample_latent_with_spectrum_spd", side_effect=lambda *args: calls.append("spd") or "latent"),
            patch.object(nodes, "_sample_latent_with_spectrum_mod_guidance_advanced", side_effect=lambda *args: calls.append("advanced") or "latent"),
        ):
            result = nodes._sample_latent_with_aio_backend(
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

        self.assertEqual(result, "latent")
        self.assertEqual(calls, ["comfy"])


class AIOHighresDetailerStageTests(unittest.TestCase):
    def test_highres_stage_resamples_scaled_image_with_stage_sampler(self):
        settings = nodes._normalize_aio_generation_settings(json.dumps({
            "highres": {
                "enabled": True,
            },
        }))
        calls = []

        def fake_sample(*args):
            calls.append(args)
            return "high_latent"

        with (
            patch.object(nodes.EasyUseAnimaImageScaleByMultiple, "upscale", return_value=("scaled_image", 640, 960, 1.25)),
            patch.object(nodes, "_encode_image_with_comfy_vae", return_value="high_latent_image"),
            patch.object(nodes, "_apply_aio_spectrum_model_patches_for_comfy_sampler", return_value="stage_model"),
            patch.object(nodes, "_sample_latent_with_comfy", side_effect=fake_sample),
            patch.object(nodes, "_decode_latent_with_comfy", return_value="high_image"),
            patch.object(nodes, "_cleanup_aio_ephemeral_model"),
        ):
            latent, image, width, height, metadata = nodes._run_aio_highres_stage(
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
        self.assertEqual(calls[0][4], settings["sampler"]["sampler_name"])
        self.assertEqual(calls[0][5], settings["sampler"]["scheduler"])
        self.assertEqual(calls[0][8], "high_latent_image")
        self.assertEqual(calls[0][9], 0.31)

    def test_highres_stage_can_override_main_sampler_when_inherit_is_disabled(self):
        settings = nodes._normalize_aio_generation_settings(json.dumps({
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
            patch.object(nodes.EasyUseAnimaImageScaleByMultiple, "upscale", return_value=("scaled_image", 640, 960, 1.25)),
            patch.object(nodes, "_encode_image_with_comfy_vae", return_value="high_latent_image"),
            patch.object(nodes, "_apply_aio_spectrum_model_patches_for_comfy_sampler", return_value="stage_model"),
            patch.object(nodes, "_sample_latent_with_comfy", side_effect=fake_sample),
            patch.object(nodes, "_decode_latent_with_comfy", return_value="high_image"),
            patch.object(nodes, "_cleanup_aio_ephemeral_model"),
        ):
            nodes._run_aio_highres_stage(
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

        self.assertEqual(calls[0][3], 8.0)
        self.assertEqual(calls[0][4], "euler")
        self.assertEqual(calls[0][5], "simple")

    def test_detailer_target_uses_stage_spectrum_patched_model(self):
        settings = nodes._normalize_aio_generation_settings(json.dumps({
            "detailer": {
                "face": {
                    "enabled": True,
                },
            },
        }))

        with (
            patch.object(nodes, "_apply_aio_spectrum_model_patches_for_comfy_sampler", return_value="detail_model"),
            patch.object(nodes.EasyUseAnimaSAM3Detailer, "doit", return_value=("detailed_image", ((1, 1), ["seg"]), "mask", "raw_image")) as detailer,
            patch.object(nodes, "_cleanup_aio_ephemeral_model"),
        ):
            image, metadata = nodes._run_aio_detailer_target(
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

    def test_detailer_stage_runs_targets_in_saved_order(self):
        settings = nodes._normalize_aio_generation_settings(json.dumps({
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
            patch.object(nodes, "_load_aio_sam3_context", return_value={"ckpt_name": "sam3"}),
            patch.object(nodes, "_run_aio_detailer_target", side_effect=fake_detailer_target),
        ):
            image, metadata = nodes._run_aio_detailer_stage(
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


class AIOGeneratorRuntimeTests(unittest.TestCase):
    def setUp(self):
        nodes._clear_aio_first_pass_cache()

    def test_generator_uses_custom_preview_key_instead_of_default_images(self):
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
            patch.object(nodes, "_load_aio_resources_from_input_context", return_value=("base_model", "base_clip", "vae")),
            patch.object(nodes, "_apply_aio_lora_stack", return_value=("lora_model", "lora_clip", [{"name": "a"}])),
            patch.object(nodes, "_apply_aio_model_patches", return_value="patched_model"),
            patch.object(nodes, "_advanced_outputs_from_prompt_data", return_value=("p", "n", "q", "qn", False, False, "", "", 512, 768)),
            patch.object(nodes, "_encode_prompt_data_positive_conditioning", return_value="positive"),
            patch.object(nodes, "_encode_with_comfy_clip", return_value="negative"),
            patch.object(nodes, "_generate_empty_latent_with_comfy", return_value="latent_image"),
            patch.object(nodes, "_sample_latent_with_aio_backend", return_value="latent"),
            patch.object(nodes, "_decode_latent_with_comfy", return_value="image"),
            patch.object(nodes, "_save_image_with_image_saver", return_value={"ui": {"images": [{"filename": "preview.webp"}]}}),
            patch.object(nodes, "_cleanup_aio_ephemeral_model"),
        ):
            result = nodes.EasyUseAnimaAIOGenerator().generate(
                context,
                generation_settings=json.dumps({"save": {"enabled": True}}),
                lora_stack=[("a.safetensors", 1.0, 1.0)],
            )

        self.assertNotIn("images", result["ui"])
        self.assertEqual(result["ui"]["easyuse_anima_preview"][0]["filename"], "preview.webp")
        self.assertEqual(result["ui"]["sampler_backend"], ["comfy_ksampler"])
        self.assertIn("easyuse_anima_run_id", result["ui"])

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
            patch.object(nodes, "_load_aio_resources_from_input_context", return_value=("base_model", "base_clip", "vae")),
            patch.object(nodes, "_apply_aio_lora_stack", return_value=("lora_model", "lora_clip", [])),
            patch.object(nodes, "_apply_aio_model_patches", return_value="patched_model"),
            patch.object(nodes, "_advanced_outputs_from_prompt_data", return_value=("p", "n", "q", "qn", False, False, "", "", 512, 768)),
            patch.object(nodes, "_encode_prompt_data_positive_conditioning", return_value="positive"),
            patch.object(nodes, "_encode_with_comfy_clip", return_value="negative"),
            patch.object(nodes, "_generate_empty_latent_with_comfy", return_value="latent_image") as empty_latent,
            patch.object(nodes, "_sample_latent_with_aio_backend", return_value="latent") as sample,
            patch.object(nodes, "_decode_latent_with_comfy", return_value="image") as decode,
            patch.object(nodes, "_run_aio_highres_stage", side_effect=[
                ("high_latent_1", "high_image_1", 640, 960, {"enabled": True, "sampler": nodes._normalize_aio_generation_settings("{}")["sampler"]}),
                ("high_latent_2", "high_image_2", 768, 1152, {"enabled": True, "sampler": nodes._normalize_aio_generation_settings("{}")["sampler"]}),
            ]) as highres,
            patch.object(nodes, "_save_image_with_image_saver", return_value={"ui": {"images": [{"filename": "final.webp"}]}}),
            patch.object(nodes, "_cleanup_aio_ephemeral_model"),
        ):
            generator = nodes.EasyUseAnimaAIOGenerator()
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
            patch.object(nodes, "_load_aio_resources_from_input_context", return_value=("base_model", "base_clip", "vae")),
            patch.object(nodes, "_apply_aio_lora_stack", return_value=("lora_model", "lora_clip", [])),
            patch.object(nodes, "_apply_aio_model_patches", return_value="patched_model"),
            patch.object(nodes, "_advanced_outputs_from_prompt_data", return_value=("p", "n", "q", "qn", False, False, "", "", 512, 768)),
            patch.object(nodes, "_encode_prompt_data_positive_conditioning", return_value="positive"),
            patch.object(nodes, "_encode_with_comfy_clip", return_value="negative"),
            patch.object(nodes, "_generate_empty_latent_with_comfy", return_value="latent_image"),
            patch.object(nodes, "_sample_latent_with_aio_backend", return_value="latent"),
            patch.object(nodes, "_decode_latent_with_comfy", return_value="image"),
            patch.object(nodes, "_run_aio_highres_stage", return_value=(
                "highres_latent",
                "highres_image",
                768,
                1024,
                {
                    "enabled": True,
                    "sampler": nodes._normalize_aio_generation_settings("{}")["sampler"],
                },
            )),
            patch.object(nodes, "_save_image_with_image_saver", return_value={"ui": {"images": [{"filename": "final.webp"}]}}),
            patch.object(nodes, "_save_aio_temp_preview_image", side_effect=fake_preview),
            patch.object(nodes, "_cleanup_aio_ephemeral_model"),
        ):
            result = nodes.EasyUseAnimaAIOGenerator().generate(
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

        self.assertNotIn("images", result["ui"])
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
            patch.object(nodes, "_load_aio_resources_from_input_context", return_value=("base_model", "base_clip", "vae")),
            patch.object(nodes, "_apply_aio_lora_stack", return_value=("lora_model", "lora_clip", [])),
            patch.object(nodes, "_apply_aio_model_patches", return_value="patched_model"),
            patch.object(nodes, "_advanced_outputs_from_prompt_data", return_value=("p", "n", "q", "qn", False, False, "", "", 512, 768)),
            patch.object(nodes, "_encode_prompt_data_positive_conditioning", return_value="positive"),
            patch.object(nodes, "_encode_with_comfy_clip", return_value="negative"),
            patch.object(nodes, "_generate_empty_latent_with_comfy", return_value="latent_image"),
            patch.object(nodes, "_sample_latent_with_aio_backend", return_value="latent"),
            patch.object(nodes, "_decode_latent_with_comfy", return_value="image"),
            patch.object(nodes, "_save_image_with_image_saver", return_value={"ui": {"images": [{"filename": "final.webp"}]}}),
            patch.object(nodes, "_save_aio_temp_preview_image", side_effect=fake_preview),
            patch.object(nodes, "_send_aio_preview_event") as send_preview_event,
            patch.object(nodes, "_cleanup_aio_ephemeral_model"),
        ):
            result = nodes.EasyUseAnimaAIOGenerator().generate(
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
