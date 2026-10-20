from __future__ import annotations

import copy
import json
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from easyuse_anima.aio import (
    first_pass_cache, generation_defaults, generation_normalization,
    legacy_generation, model_preparation, model_profiles, resources, sampling,
)
from tests.comfy_host_fakes import FakeComfyHostProvider, use_fake_comfy_host, patch_comfy_helper


class AIOModelProfileTests(unittest.TestCase):
    def setUp(self):
        self.host = use_fake_comfy_host(generation_normalization, FakeComfyHostProvider())
        self.host.__enter__()
        self.addCleanup(self.host.__exit__, None, None, None)

    def settings(self, **overrides):
        return generation_normalization._normalize_aio_generation_settings(
            {"model_family": "moss_image", **overrides}
        )

    def test_family_defaults_preserve_explicit_values_and_inactive_settings(self):
        original = copy.deepcopy(generation_defaults.AIO_GENERATION_DEFAULT_SETTINGS)
        source = {
            "model_family": "moss_image",
            "sampler": {"seed": 1125899906842624, "steps": 37},
            "model_patches": {"aura_flow": {"shift": 4.5}},
            "model_settings": {"anima": {"sampler": {"cfg": 9.0}}},
        }
        settings = generation_normalization._normalize_aio_generation_settings(json.dumps(source))
        self.assertEqual(settings["sampler"]["steps"], 37)
        self.assertEqual(settings["sampler"]["cfg"], 2.5)
        self.assertEqual(settings["sampler"]["seed"], 1125899906842624)
        self.assertEqual(settings["model_patches"]["aura_flow"]["shift"], 4.5)
        self.assertEqual(settings["mod_guidance"]["mode"], "disabled")
        self.assertEqual(settings["artist_mix"]["mode"], "off")
        self.assertEqual(settings["model_settings"], source["model_settings"])
        self.assertEqual(generation_defaults.AIO_GENERATION_DEFAULT_SETTINGS, original)
        model_profiles.validate_aio_model_settings(settings)

    def test_legacy_settings_remain_anima_and_unknown_family_is_rejected(self):
        settings = generation_normalization._normalize_aio_generation_settings({})
        self.assertEqual(settings["model_family"], "anima")
        self.assertEqual(settings["sampler"]["steps"], 32)
        self.assertEqual(settings["model_patches"]["aura_flow"]["shift"], 3.0)
        with self.assertRaisesRegex(ValueError, "Unsupported AiO model family"):
            self.settings(model_family="unknown")

    def test_unsupported_spectrum_fails_before_any_resource_or_adapter_load(self):
        settings = self.settings(sampler={"backend": "spectrum_mod_guidance_advanced"})
        with patch.object(legacy_generation, "_load_aio_resources_from_input_context") as load:
            with self.assertRaisesRegex(ValueError, "different MOSS loader"):
                legacy_generation._run_aio_generation_pipeline(
                    object(), {"prompt_data": {}}, settings,
                )
        load.assert_not_called()

    def test_unsupported_features_and_hook_are_not_silently_ignored(self):
        for path in (
            ("model_patches", "dave", "enabled"),
            ("model_patches", "safe_pag", "enabled"),
            ("model_patches", "kj", "torch_compile", "enabled"),
            ("sampler", "spectrum", "enabled"),
            ("sampler", "dit_corrections", "enabled"),
            ("highres", "enabled"),
            ("upscale", "enabled"),
            ("detailer", "face", "enabled"),
        ):
            with self.subTest(path=path):
                settings = self.settings()
                target = settings
                for key in path[:-1]:
                    target = target[key]
                target[path[-1]] = True
                with self.assertRaisesRegex(ValueError, "unsupported options"):
                    model_profiles.validate_aio_model_settings(settings)
        with self.assertRaisesRegex(ValueError, "AiO hook"):
            model_profiles.validate_aio_model_settings(self.settings(), aio_hook=object())

    def test_model_identity_clip_type_and_dimension_contract(self):
        def model(family):
            return SimpleNamespace(model=SimpleNamespace(
                model_config=SimpleNamespace(unet_config={"image_model": family}),
            ))
        context = {"resource_info": {"clip_type": "moss_image"}}
        model_profiles.validate_aio_model_resources("moss_image", context, model=model("moss_image"))
        with self.assertRaisesRegex(ValueError, "requires CLIP type"):
            model_profiles.validate_aio_model_resources("moss_image", {})
        with self.assertRaisesRegex(ValueError, "native MOSS"):
            model_profiles.validate_aio_model_resources("moss_image", context, model=model("anima"))
        with self.assertRaisesRegex(ValueError, "Select MOSS"):
            model_profiles.validate_aio_model_resources("anima", context, model=model("moss_image"))
        model_profiles.validate_aio_model_dimensions("moss_image", 1024, 1536)
        with self.assertRaisesRegex(ValueError, "multiples of 16"):
            model_profiles.validate_aio_model_dimensions("moss_image", 1025, 1024)

    def test_moss_latent_uses_core_flux2_node(self):
        execute = Mock(return_value=({"samples": "packed-128-channel-latent"},))
        cls = SimpleNamespace(execute=execute)
        with patch_comfy_helper(sampling, "_find_comfy_node_class", return_value=cls) as find:
            result = sampling._generate_empty_model_latent_with_comfy(1024, 1536, model_family="moss_image")
        find.assert_called_once_with("EmptyFlux2LatentImage")
        execute.assert_called_once_with(1024, 1536, batch_size=1)
        self.assertEqual(result["samples"], "packed-128-channel-latent")

    def test_missing_core_clip_support_fails_before_model_loading(self):
        context = {"resource_info": {
            "unet_name": "moss.safetensors", "vae_name": "flux2.safetensors",
            "clip_name": "qwen.safetensors", "clip_type": "moss_image",
        }}
        with (
            patch.object(resources, "_comfy_clip_loader_types", return_value=["qwen_image"]),
            patch.object(resources, "_load_diffusion_model_with_comfy") as load,
        ):
            with self.assertRaisesRegex(RuntimeError, "does not support CLIP type moss_image"):
                resources._load_aio_resources_from_input_context(context)
        load.assert_not_called()

    def test_moss_shift_uses_aura_flow_contract_and_never_sd3(self):
        settings = self.settings()
        model_profiles.validate_aio_model_settings(settings)
        patch_aura = Mock(return_value=("shifted",))
        cls = Mock(return_value=SimpleNamespace(patch_aura=patch_aura))
        with patch_comfy_helper(model_preparation, "_find_comfy_node_class", return_value=cls) as find:
            result = model_preparation._patch_model_sampling_aura_flow(
                "base", settings["model_patches"]["aura_flow"],
            )
        find.assert_called_once_with("ModelSamplingAuraFlow")
        patch_aura.assert_called_once_with("base", 5.0)
        self.assertEqual(result, "shifted")

    def test_cache_separates_families_but_ignores_inactive_bank(self):
        settings = self.settings()
        args = dict(
            cache_scope="model-profile", context={}, prompt_data={}, lora_stack=None,
            settings=settings, positive_prompt="image", negative_prompt="",
            quality_tags="", quality_neg="", use_anima_mod_guidance=False,
            use_negative_anima_mod_guidance=False, width=1024, height=1024,
        )
        first = first_pass_cache._aio_first_pass_cache_key(**args)
        settings["model_settings"] = {"anima": {"sampler": {"cfg": 10}}}
        self.assertEqual(first, first_pass_cache._aio_first_pass_cache_key(**args))
        settings["model_family"] = "anima"
        self.assertNotEqual(first, first_pass_cache._aio_first_pass_cache_key(**args))
