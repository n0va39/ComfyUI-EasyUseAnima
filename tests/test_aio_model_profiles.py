from __future__ import annotations

import copy
import json
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from easyuse_anima.aio import (
    capabilities, first_pass_cache, generation_defaults, generation_normalization,
    legacy_generation, model_preparation, model_profiles, resources, sampling,
)
from tests.comfy_host_fakes import FakeComfyHostProvider, use_fake_comfy_host, patch_comfy_helper
from easyuse_anima.nodes.aio_nodes import (
    EasyUseAnimaAIOGenerator, EasyUseMossAIOGenerator, EasyUseKrea2AIOGenerator,
)


class NativeMossProvider:
    SPECTRUM_CAPABILITIES = {
        **capabilities.NATIVE_MOSS_SPECTRUM_CONTRACT,
        "stages": list(capabilities.SAMPLING_STAGES),
    }
    RETURN_TYPES = ("MODEL",)
    FUNCTION = "patch"

    def patch(
        self, model, steps, window_size, flex_window, warmup_steps,
        tail_actual_steps, blend_w, cheby_degree, ridge_lambda, history_size,
        enabled, one_sampler_only, verbose, compat_policy,
    ):
        return (("native", model, steps, compat_policy),)


class AIOCapabilityTests(unittest.TestCase):
    def settings(self, **overrides):
        return generation_normalization._normalize_aio_generation_settings(
            {"model_family": "moss_image", "sampler": {"spectrum": {"enabled": True}}, **overrides}
        )

    def test_missing_provider_and_unknown_contract_do_not_enable_forecasting(self):
        for cls, status in ((None, "missing_dependency"), (object, "incompatible")):
            support = capabilities.aio_feature_support(
                "moss_image", "spectrum", node_lookup=lambda _: cls,
            )
            self.assertFalse(support["supported"])
            self.assertEqual(support["status"], status)
        marker = dict(NativeMossProvider.SPECTRUM_CAPABILITIES, contract_version=2)
        with patch.object(NativeMossProvider, "SPECTRUM_CAPABILITIES", marker):
            self.assertIsNone(capabilities.native_moss_spectrum_provider(lambda _: NativeMossProvider)[0])

    def test_provider_requires_native_loader_forecast_stage_and_explicit_inputs(self):
        for field, value in (
            ("loader", "moss-image"), ("model_family", "krea2"),
            ("features", ["mod_guidance"]), ("stages", ["highres"]),
        ):
            with self.subTest(field=field):
                marker = dict(NativeMossProvider.SPECTRUM_CAPABILITIES, **{field: value})
                with patch.object(NativeMossProvider, "SPECTRUM_CAPABILITIES", marker):
                    self.assertEqual(
                        capabilities.native_moss_spectrum_provider(lambda _: NativeMossProvider),
                        (None, "incompatible"),
                    )
        with patch.object(NativeMossProvider, "patch", lambda self, **kwargs: None):
            self.assertEqual(
                capabilities.native_moss_spectrum_provider(lambda _: NativeMossProvider),
                (None, "incompatible"),
            )
        with patch.object(NativeMossProvider, "RETURN_TYPES", ("IMAGE",)):
            self.assertEqual(
                capabilities.native_moss_spectrum_provider(lambda _: NativeMossProvider),
                (None, "incompatible"),
            )

    def test_provider_availability_is_live_and_manifest_is_not_mutable_policy(self):
        lookup = Mock(side_effect=[NativeMossProvider, None])
        self.assertTrue(capabilities.aio_feature_support("moss_image", "spectrum", node_lookup=lookup)["supported"])
        self.assertFalse(capabilities.aio_feature_support("moss_image", "spectrum", node_lookup=lookup)["supported"])
        manifest = capabilities.aio_capability_manifest("moss_image", node_lookup=lambda _: NativeMossProvider)
        manifest["features"]["spectrum"]["stages"].clear()
        self.assertEqual(
            capabilities.aio_feature_support("moss_image", "spectrum", node_lookup=lambda _: NativeMossProvider)["stages"],
            list(capabilities.SAMPLING_STAGES),
        )

    def test_native_forecast_stages_do_not_unlock_other_features(self):
        settings = self.settings()
        original = copy.deepcopy(settings)
        model_profiles.validate_aio_model_settings(settings, node_lookup=lambda _: NativeMossProvider)
        self.assertEqual(settings, original)
        for family, feature, stage in (
            ("krea2", "spectrum", "sampler"),
            ("moss_image", "mod_guidance", "sampler"), ("moss_image", "dit_corrections", "sampler"),
        ):
            with self.subTest(family=family, feature=feature, stage=stage):
                self.assertFalse(capabilities.aio_feature_support(
                    family, feature, stage, node_lookup=lambda _: NativeMossProvider,
                )["supported"])
        for stage in capabilities.SAMPLING_STAGES:
            self.assertTrue(capabilities.aio_feature_support(
                "moss_image", "spectrum", stage, node_lookup=lambda _: NativeMossProvider,
            )["supported"])
        for stage in ("highres", "upscale"):
            settings[stage]["enabled"] = True
            settings[stage]["spectrum"]["enabled"] = True
        settings["detailer"]["enabled"] = True
        settings["detailer"]["face"]["enabled"] = True
        settings["detailer"]["face"]["spectrum"]["enabled"] = True
        settings["detailer"]["custom"] = copy.deepcopy(settings["detailer"]["face"])
        settings["detailer"]["order"].append("custom")
        model_profiles.validate_aio_model_settings(settings, node_lookup=lambda _: NativeMossProvider)

    def test_provider_stages_are_intersected_with_reviewed_stages(self):
        marker = dict(
            NativeMossProvider.SPECTRUM_CAPABILITIES,
            stages=["sampler", "highres", "future_stage"],
        )
        with patch.object(NativeMossProvider, "SPECTRUM_CAPABILITIES", marker):
            manifest = capabilities.aio_capability_manifest(
                "moss_image", node_lookup=lambda _: NativeMossProvider,
            )
            self.assertEqual(manifest["features"]["spectrum"]["stages"], ["sampler", "highres"])
            self.assertTrue(capabilities.aio_feature_support(
                "moss_image", "spectrum", "highres", node_lookup=lambda _: NativeMossProvider,
            )["supported"])
            for stage in ("detailer", "upscale", "future_stage"):
                support = capabilities.aio_feature_support(
                    "moss_image", "spectrum", stage, node_lookup=lambda _: NativeMossProvider,
                )
                self.assertFalse(support["supported"])
                self.assertEqual(support["reason_code"], "stage_not_supported")

    def test_first_pass_only_provider_preserves_old_contract_and_saved_settings(self):
        settings = self.settings()
        settings["highres"]["enabled"] = True
        settings["highres"]["spectrum"]["enabled"] = True
        with patch.object(
            NativeMossProvider, "SPECTRUM_CAPABILITIES",
            capabilities.NATIVE_MOSS_SPECTRUM_CONTRACT,
        ):
            self.assertTrue(capabilities.aio_feature_support(
                "moss_image", "spectrum", node_lookup=lambda _: NativeMossProvider,
            )["supported"])
            with self.assertRaisesRegex(ValueError, "stage_not_supported"):
                model_profiles.validate_aio_model_settings(settings, node_lookup=lambda _: NativeMossProvider)
            for stage in ("highres", "detailer", "upscale"):
                self.assertFalse(capabilities.aio_feature_support(
                    "moss_image", "spectrum", stage, node_lookup=lambda _: NativeMossProvider,
                )["supported"])
        settings["highres"]["enabled"] = False
        model_profiles.validate_aio_model_settings(settings, node_lookup=lambda _: NativeMossProvider)
        self.assertTrue(settings["highres"]["spectrum"]["enabled"])

    def test_native_dispatch_uses_only_reviewed_provider_and_preserves_sampling(self):
        model = SimpleNamespace(model=SimpleNamespace(
            model_config=SimpleNamespace(unet_config={"image_model": "moss_image"}),
            model_sampling=object(),
        ))
        sampling_before = model.model.model_sampling
        with patch_comfy_helper(model_preparation, "_find_comfy_node_class", return_value=NativeMossProvider) as find:
            result = model_preparation._apply_aio_spectrum_forecast_patch_for_comfy_sampler(
                model, self.settings()["sampler"],
            )
        find.assert_called_once_with("NativeMossSpectrumPatch")
        self.assertEqual(result, ("native", model, 25, "conservative"))
        self.assertIs(model.model.model_sampling, sampling_before)
        with patch_comfy_helper(model_preparation, "_find_comfy_node_class", return_value=None):
            with self.assertRaisesRegex(RuntimeError, "missing_dependency"):
                model_preparation._apply_aio_spectrum_forecast_patch_for_comfy_sampler(model, self.settings()["sampler"])

    def test_object_info_manifest_does_not_change_serialized_defaults(self):
        with patch.object(capabilities, "_find_provider", return_value=NativeMossProvider):
            options = EasyUseMossAIOGenerator.INPUT_TYPES()["required"]["generation_settings"][1]
        self.assertTrue(options["aio_capabilities"]["features"]["spectrum"]["supported"])
        self.assertNotIn("aio_capabilities", json.loads(options["default"]))
        self.assertFalse(json.loads(options["default"])["sampler"]["spectrum"]["enabled"])


class AIOModelProfileTests(unittest.TestCase):
    def setUp(self):
        self.host = use_fake_comfy_host(generation_normalization, FakeComfyHostProvider())
        self.host.__enter__()
        self.addCleanup(self.host.__exit__, None, None, None)

    def settings(self, **overrides):
        return generation_normalization._normalize_aio_generation_settings(
            {"model_family": "moss_image", **overrides}
        )

    def test_fixed_node_defaults_and_missing_family_restore(self):
        for cls, family, steps, cfg, shift in (
            (EasyUseAnimaAIOGenerator, "anima", 32, 5.0, 3.0),
            (EasyUseMossAIOGenerator, "moss_image", 25, 2.5, 5.0),
            (EasyUseKrea2AIOGenerator, "krea2", 8, 1.0, 1.15),
        ):
            with self.subTest(family=family):
                defaults = json.loads(cls.INPUT_TYPES()["required"]["generation_settings"][1]["default"])
                self.assertEqual(defaults["model_family"], family)
                self.assertEqual(defaults["sampler"]["steps"], steps)
                self.assertEqual(defaults["sampler"]["cfg"], cfg)
                self.assertEqual(defaults["model_patches"]["aura_flow"]["shift"], shift)
                restored = generation_normalization._normalize_aio_generation_settings(
                    {"sampler": {"seed": 123, "steps": 17}}, model_family=cls.MODEL_FAMILY,
                )
                self.assertEqual(restored["model_family"], family)
                self.assertEqual(restored["sampler"]["steps"], 17)
                self.assertEqual(restored["sampler"]["cfg"], cfg)
                self.assertEqual(restored["sampler"]["seed"], 123)
                model_profiles.validate_aio_model_settings(restored)

    def test_fixed_node_rejects_cross_family_before_loading(self):
        for cls, other in (
            (EasyUseAnimaAIOGenerator, "moss_image"),
            (EasyUseMossAIOGenerator, "krea2"),
            (EasyUseKrea2AIOGenerator, "anima"),
        ):
            with self.subTest(node=cls.__name__):
                with self.assertRaisesRegex(ValueError, "matching model-specific"):
                    cls.IS_CHANGED(generation_settings={"model_family": other})

    def test_krea2_uses_flux_sampling_and_core_empty_latent(self):
        settings = self.settings(model_family="krea2")
        self.assertEqual(settings["sampler"]["sampler_name"], "euler")
        model_profiles.validate_aio_model_settings(settings)
        plan = model_preparation._aio_stage_model_patch_plan(settings, "first_pass")
        self.assertEqual(plan.patch_ids, ("flux",))
        patch_flux = Mock(return_value=("shifted",))
        cls = Mock(return_value=SimpleNamespace(patch=patch_flux))
        with patch_comfy_helper(model_preparation, "_find_comfy_node_class", return_value=cls) as find:
            result = model_preparation._apply_aio_stage_model_patch_plan("base", plan)
        find.assert_called_once_with("ModelSamplingFlux")
        patch_flux.assert_called_once_with(
            "base", max_shift=1.15, base_shift=1.15, width=1024, height=1024,
        )
        self.assertEqual(result, "shifted")
        with patch.object(sampling, "_generate_empty_latent_with_comfy", return_value={"samples": "core"}) as generate:
            self.assertEqual(
                sampling._generate_empty_model_latent_with_comfy(1024, 768, model_family="krea2"),
                {"samples": "core"},
            )
        generate.assert_called_once_with(1024, 768)

    def test_krea2_rejects_moss_resources_and_unreviewed_features(self):
        context = {"resource_info": {"clip_type": "krea2"}}
        config = SimpleNamespace(unet_config={"image_model": "krea2"})
        model = SimpleNamespace(model=SimpleNamespace(model_config=config))
        model_profiles.validate_aio_model_resources("krea2", context, model=model)
        config.unet_config["image_model"] = "moss_image"
        with self.assertRaisesRegex(ValueError, "Krea2 diffusion model"):
            model_profiles.validate_aio_model_resources("krea2", context, model=model)
        with self.assertRaisesRegex(ValueError, "CLIP type 'krea2'"):
            model_profiles.validate_aio_model_resources("krea2", {"resource_info": {"clip_type": "moss_image"}})
        with self.assertRaisesRegex(ValueError, "multiples of 16"):
            model_profiles.validate_aio_model_dimensions("krea2", 1000, 1024)
        model_profiles.validate_aio_model_settings(
            self.settings(model_family="krea2", highres={"enabled": True})
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
        ):
            with self.subTest(path=path):
                settings = self.settings()
                target = settings
                for key in path[:-1]:
                    target = target[key]
                target[path[-1]] = True
                with self.assertRaisesRegex(ValueError, "unsupported options"):
                    model_profiles.validate_aio_model_settings(settings)
        model_profiles.validate_aio_model_settings(self.settings(), aio_hook=object())

    def test_common_extras_are_allowed_and_use_family_defaults(self):
        for family, steps, cfg in (("moss_image", 25, 2.5), ("krea2", 8, 1.0)):
            settings = self.settings(
                model_family=family, highres={"enabled": True},
                upscale={"enabled": True}, detailer={"enabled": True, "custom_1": {"enabled": True}},
                model_patches={"kj": {
                    "sage_attention": "auto", "fp16_accumulation": True,
                    "torch_compile": {"enabled": family == "krea2"},
                }},
            )
            model_profiles.validate_aio_model_settings(settings, aio_hook=object())
            for stage in (settings["highres"], settings["upscale"], settings["detailer"]["custom_1"]):
                self.assertEqual(stage["steps"], steps)
                self.assertEqual(stage["cfg"], cfg)
                self.assertEqual(stage["scheduler"], "simple")
                self.assertFalse(stage["spectrum"]["enabled"])

    def test_nested_patches_cannot_bypass_family_validation(self):
        for family in ("moss_image", "krea2"):
            for section in ("highres", "upscale", "custom_1"):
                for feature in ("spectrum", "dit_corrections"):
                    with self.subTest(family=family, section=section, feature=feature):
                        if section == "custom_1":
                            override = {"detailer": {"enabled": True, section: {
                                "enabled": True, feature: {"enabled": True},
                            }}}
                        else:
                            override = {section: {"enabled": True, feature: {"enabled": True}}}
                        settings = self.settings(model_family=family, **override)
                        with self.assertRaisesRegex(ValueError, "unsupported options"):
                            model_profiles.validate_aio_model_settings(settings)
                        settings["detailer" if section == "custom_1" else section]["enabled"] = False
                        model_profiles.validate_aio_model_settings(settings)

    def test_explicit_stage_tuning_preserved_and_negpip_is_family_specific(self):
        settings = self.settings(
            model_family="krea2", highres={"steps": 31, "cfg": 4.5},
            detailer={"custom_1": {"steps": 19, "cfg": 3.5}},
        )
        self.assertEqual(settings["highres"]["steps"], 31)
        self.assertEqual(settings["highres"]["cfg"], 4.5)
        self.assertEqual(settings["detailer"]["custom_1"]["steps"], 19)
        self.assertEqual(settings["detailer"]["custom_1"]["cfg"], 3.5)
        settings["negpip"]["mode"] = "on"
        with self.assertRaisesRegex(ValueError, "NegPip"):
            model_profiles.validate_aio_model_settings(settings)
        settings["model_family"] = "moss_image"
        model_profiles.validate_aio_model_settings(settings)

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
