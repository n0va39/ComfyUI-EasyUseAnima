from __future__ import annotations

import copy
import unittest
from types import SimpleNamespace

from easyuse_anima.aio import (
    capabilities, first_pass_cache, generation_normalization, model_preparation, model_profiles, optimization,
)
from tests.comfy_host_fakes import patch_comfy_helper


class BlockCompile:
    RETURN_TYPES = ("MODEL",)
    FUNCTION = "patch"

    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {"model": ("MODEL",)}}

    def patch(self, model):
        return (("compiled", model),)


class KJCompile(BlockCompile):
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {name: ("CONTROL",) for name in (
            "model", "backend", "fullgraph", "mode", "dynamic", "dynamo_cache_size_limit",
            "compile_transformer_blocks_only", "debug_compile_keys",
        )}, "optional": {"disable_dynamic_vram": ("BOOLEAN",)}}

    def patch(self, model, backend, fullgraph, mode, dynamic, dynamo_cache_size_limit,
              compile_transformer_blocks_only, debug_compile_keys, disable_dynamic_vram=False):
        return (model,)


class Dave(BlockCompile):
    masks = ["auto", "dave_alpha.npz", "moss_dave_alpha.npz"]

    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {"model": ("MODEL",), "mask": (cls.masks,),
                             "strength": ("FLOAT",), "tau": ("FLOAT",)}}

    def patch(self, model, mask, strength, tau):
        return ((model, mask, strength, tau),)


def lookup(name):
    return {"TorchCompileModelAdvanced": KJCompile, "AnimaBlockCompile": BlockCompile,
            "AnimaDAVE": Dave}.get(name)


class AIOOptimizationTests(unittest.TestCase):
    def settings(self, family="anima", **compile_values):
        return generation_normalization._normalize_aio_generation_settings({
            "model_family": family,
            "model_patches": {"kj": {"torch_compile": compile_values}},
        })

    def test_model_specific_providers_and_old_dave_masks(self):
        for family in ("anima", "moss_image", "krea2"):
            self.assertEqual(optimization.optimization_provider(
                family, "torch_compile", "kj", lookup,
            ), (KJCompile, "available"))
        self.assertEqual(optimization.optimization_provider(
            "moss_image", "torch_compile", "anima_block_compile", lookup,
        ), (None, "unsupported"))
        self.assertEqual(optimization.optimization_provider(
            "krea2", "dave", "anima_dave", lookup,
        ), (None, "unsupported"))
        class OldDave(Dave):
            masks = ["dave_alpha.npz"]
        self.assertEqual(optimization.optimization_provider(
            "moss_image", "dave", "anima_dave", lambda _: OldDave,
        ), (None, "incompatible"))
        self.assertEqual(optimization.resolve_dave_mask(OldDave, "anima", "auto"), "dave_alpha.npz")
        with self.assertRaisesRegex(ValueError, "Anima mask"):
            optimization.resolve_dave_mask(Dave, "moss_image", "dave_alpha.npz")

    def test_provider_manifest_is_detached_and_available_is_not_a_kernel_test(self):
        manifest = capabilities.aio_capability_manifest("moss_image", node_lookup=lookup)
        self.assertTrue(manifest["features"]["dave"]["supported"])
        self.assertTrue(manifest["features"]["torch_compile"]["supported"])
        manifest["optimization_providers"]["torch_compile"][0]["models"].clear()
        self.assertEqual(optimization.optimization_provider(
            "moss_image", "torch_compile", "kj", lookup,
        )[1], "available")

    def test_selected_provider_is_validated_and_inactive_unknown_is_preserved(self):
        for family in ("anima", "moss_image", "krea2"):
            settings = self.settings(family, enabled=False, provider="future_compiler")
            before = copy.deepcopy(settings)
            model_profiles.validate_aio_model_settings(settings, node_lookup=lookup)
            self.assertEqual(settings, before)
            settings["model_patches"]["kj"]["torch_compile"]["enabled"] = True
            with self.assertRaisesRegex(ValueError, "future_compiler"):
                model_profiles.validate_aio_model_settings(settings, node_lookup=lookup)
        model_profiles.validate_aio_model_settings(
            self.settings("anima", enabled=True, provider="anima_block_compile"), node_lookup=lookup,
        )
        with self.assertRaisesRegex(ValueError, "anima_block_compile.*unsupported"):
            model_profiles.validate_aio_model_settings(
                self.settings("moss_image", enabled=True, provider="anima_block_compile"), node_lookup=lookup,
            )

    def test_explicit_old_compile_and_dave_settings_round_trip(self):
        saved = {"enabled": False, "mode": "max-autotune-no-cudagraphs", "dynamic": "false",
                 "disable_dynamic_vram": True}
        settings = self.settings("moss_image", **saved)
        actual = settings["model_patches"]["kj"]["torch_compile"]
        self.assertEqual({key: actual[key] for key in saved}, saved)
        self.assertEqual(actual["provider"], "kj")
        settings["model_patches"]["dave"].update(mask="dave_alpha.npz", tau=0.1)
        restored = generation_normalization._normalize_aio_generation_settings(settings)
        self.assertEqual(restored["model_patches"]["dave"], settings["model_patches"]["dave"])

    def test_first_pass_cache_tracks_only_enabled_compile_provider(self):
        patches = self.settings(enabled=True)["model_patches"]
        first = first_pass_cache._aio_first_pass_model_patch_plan(patches)
        patches["kj"]["torch_compile"]["provider"] = "anima_block_compile"
        self.assertNotEqual(first, first_pass_cache._aio_first_pass_model_patch_plan(patches))
        patches["kj"]["torch_compile"]["enabled"] = False
        disabled = first_pass_cache._aio_first_pass_model_patch_plan(patches)
        patches["kj"]["torch_compile"]["provider"] = "future_compiler"
        self.assertEqual(disabled, first_pass_cache._aio_first_pass_model_patch_plan(patches))

    def test_block_compile_delegates_without_kj_options_and_moss_dave_uses_auto(self):
        model = SimpleNamespace(model=SimpleNamespace(
            model_config=SimpleNamespace(unet_config={"image_model": "anima"}),
        ))
        with patch_comfy_helper(model_preparation, "_find_comfy_node_class", side_effect=lookup):
            result = model_preparation._apply_aio_kj_torch_compile_patch(
                model, {"torch_compile": {"enabled": True, "provider": "anima_block_compile"}},
            )
            self.assertEqual(result, ("compiled", model))
            model.model.model_config.unet_config["image_model"] = "moss_image"
            result = model_preparation._apply_aio_anima_dave_patch(model, {})
            self.assertEqual(result, (model, "auto", 0.3, 0.06))
