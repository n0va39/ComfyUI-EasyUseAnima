from __future__ import annotations

import unittest
from unittest.mock import Mock, patch

import nodes
from easyuse_anima.aio import resources as aio_resources
from easyuse_anima.infrastructure.comfy import capabilities
from tests.comfy_host_fakes import patch_comfy_helper


class AIOResourceMoveTests(unittest.TestCase):
    def test_root_symbols_are_direct_canonical_aliases(self):
        resource_names = (
            "_preferred_name_default",
            "_preferred_checkpoint_default",
            "_preferred_clip_type_default",
            "_load_checkpoint_with_comfy",
            "_load_diffusion_model_with_comfy",
            "_load_vae_with_comfy",
            "_load_clip_with_comfy",
            "_load_upscale_model_with_comfy",
            "_load_aio_sam3_context",
            "_load_aio_resources_from_input_context",
        )
        for name in resource_names:
            with self.subTest(name=name):
                self.assertIs(getattr(nodes, name), getattr(aio_resources, name))

        self.assertFalse(hasattr(nodes, "_impact_core_module"))
        self.assertIs(nodes._impact_scheduler_names, capabilities._impact_scheduler_names)

    def test_preferred_resource_defaults_preserve_exact_and_basename_order(self):
        names = ["models\\anima.safetensors", "fallback.safetensors"]
        self.assertEqual(
            aio_resources._preferred_name_default(
                names,
                ("missing.safetensors", "anima.safetensors"),
            ),
            "models\\anima.safetensors",
        )
        self.assertEqual(
            aio_resources._preferred_name_default([], ("first.safetensors",)),
            "first.safetensors",
        )
        self.assertEqual(
            aio_resources._preferred_checkpoint_default(["first", "preferred"], "preferred"),
            "preferred",
        )

        with patch.object(nodes, "_choice", return_value="stable_diffusion") as choice:
            self.assertEqual(
                aio_resources._preferred_clip_type_default(["flux", "stable_diffusion"]),
                "stable_diffusion",
            )
        choice.assert_called_once_with("", ["flux", "stable_diffusion"], "stable_diffusion")

    def test_split_loaders_keep_call_time_root_lookup_and_result_unwrap(self):
        calls: list[tuple[str, tuple[object, ...]]] = []

        class CheckpointLoader:
            def load_checkpoint(self, *args):
                calls.append(("checkpoint", args))
                return "model", "clip", "vae"

        class UNETLoader:
            def load_unet(self, *args):
                calls.append(("unet", args))
                return ("model",)

        class VAELoader:
            def load_vae(self, *args):
                calls.append(("vae", args))
                return ("vae",)

        class CLIPLoader:
            def load_clip(self, *args):
                calls.append(("clip", args))
                return ("clip",)

        classes = {
            "CheckpointLoaderSimple": CheckpointLoader,
            "UNETLoader": UNETLoader,
            "VAELoader": VAELoader,
            "CLIPLoader": CLIPLoader,
        }
        with (
            patch_comfy_helper(
                nodes,
                "_find_comfy_node_class",
                side_effect=classes.get,
            ),
            patch.object(nodes, "_node_output_tuple", side_effect=lambda value: tuple(value)) as output_tuple,
        ):
            self.assertEqual(
                aio_resources._load_checkpoint_with_comfy("checkpoint.safetensors"),
                ("model", "clip", "vae"),
            )
            self.assertEqual(
                aio_resources._load_diffusion_model_with_comfy("unet.safetensors", "fp8_e4m3fn"),
                "model",
            )
            self.assertEqual(aio_resources._load_vae_with_comfy("vae.safetensors"), "vae")
            self.assertEqual(
                aio_resources._load_clip_with_comfy("clip.safetensors", "qwen_image", "cpu"),
                "clip",
            )

        self.assertEqual(
            calls,
            [
                ("checkpoint", ("checkpoint.safetensors",)),
                ("unet", ("unet.safetensors", "fp8_e4m3fn")),
                ("vae", ("vae.safetensors",)),
                ("clip", ("clip.safetensors", "qwen_image", "cpu")),
            ],
        )
        self.assertEqual(output_tuple.call_count, 3)

    def test_missing_loader_error_text_is_preserved(self):
        with patch_comfy_helper(
            nodes,
            "_find_comfy_node_class",
            return_value=None,
        ):
            with self.assertRaisesRegex(
                RuntimeError,
                r"^\[EasyUseAnima\] Could not find ComfyUI UNETLoader\.$",
            ):
                aio_resources._load_diffusion_model_with_comfy("unet.safetensors")

    def test_upscale_loader_keeps_blank_validation_and_call_time_lookup(self):
        with self.assertRaisesRegex(
            RuntimeError,
            "USDU final upscale requires an upscale_model_name",
        ):
            aio_resources._load_upscale_model_with_comfy("  ")

        load_model = Mock(return_value=("upscale-model",))
        loader_cls = type("UpscaleModelLoader", (), {"load_model": load_model})
        with (
            patch_comfy_helper(
                nodes,
                "_find_comfy_node_class",
                return_value=loader_cls,
            ),
            patch.object(nodes, "_node_output_tuple", side_effect=lambda value: tuple(value)),
        ):
            self.assertEqual(
                aio_resources._load_upscale_model_with_comfy("4x-model.pth"),
                "upscale-model",
            )
        load_model.assert_called_once_with("4x-model.pth")

    def test_sam3_bundle_uses_call_time_root_helpers(self):
        with (
            patch.object(
                nodes,
                "_load_checkpoint_with_comfy",
                return_value=("model", "clip", "vae"),
            ) as load_checkpoint,
            patch.object(nodes, "_sam3_context", return_value={"context": True}) as sam3_context,
        ):
            result = aio_resources._load_aio_sam3_context(
                {"sam3": {"checkpoint": "custom-sam3.safetensors"}}
            )

        self.assertEqual(result, {"context": True})
        load_checkpoint.assert_called_once_with("custom-sam3.safetensors")
        sam3_context.assert_called_once_with(
            "model",
            "clip",
            "vae",
            "custom-sam3.safetensors",
        )

    def test_input_context_loader_preserves_validation_and_loader_order(self):
        context = {
            "resource_info": {
                "unet_name": "unet.safetensors",
                "vae_name": "vae.safetensors",
                "clip_name": "clip.safetensors",
                "clip_type": "qwen_image",
                "unet_weight_dtype": "fallback-dtype",
                "clip_device": "fallback-device",
            },
            "input_settings": {"version": 1},
        }
        calls: list[tuple[str, tuple[object, ...]]] = []

        def record(name, result):
            def call(*args):
                calls.append((name, args))
                return result

            return call

        with (
            patch.object(
                nodes,
                "_normalize_aio_input_settings",
                return_value={
                    "resources": {
                        "unet_weight_dtype": "setting-dtype",
                        "clip_device": "setting-device",
                    }
                },
            ) as normalize,
            patch.object(
                nodes,
                "_load_diffusion_model_with_comfy",
                side_effect=record("model", "model"),
            ),
            patch.object(nodes, "_load_vae_with_comfy", side_effect=record("vae", "vae")),
            patch.object(nodes, "_load_clip_with_comfy", side_effect=record("clip", "clip")),
        ):
            result = aio_resources._load_aio_resources_from_input_context(context)

        self.assertEqual(result, ("model", "clip", "vae"))
        normalize.assert_called_once_with({"version": 1})
        self.assertEqual(
            calls,
            [
                ("model", ("unet.safetensors", "setting-dtype")),
                ("vae", ("vae.safetensors",)),
                ("clip", ("clip.safetensors", "qwen_image", "setting-device")),
            ],
        )

        with self.assertRaisesRegex(
            RuntimeError,
            r"resource_info is missing required value\(s\): unet_name, vae_name, clip_name",
        ):
            aio_resources._load_aio_resources_from_input_context({})

    def test_input_context_resolves_each_loader_immediately_before_its_call(self):
        replacement_vae = Mock(return_value="replacement-vae")

        def load_model(*_args):
            nodes._load_vae_with_comfy = replacement_vae
            return "model"

        with (
            patch.object(
                nodes,
                "_normalize_aio_input_settings",
                return_value={"resources": {}},
            ),
            patch.object(
                nodes,
                "_load_diffusion_model_with_comfy",
                side_effect=load_model,
            ),
            patch.object(nodes, "_load_vae_with_comfy", return_value="stale-vae") as stale_vae,
            patch.object(nodes, "_load_clip_with_comfy", return_value="clip"),
        ):
            result = aio_resources._load_aio_resources_from_input_context(
                {
                    "resource_info": {
                        "unet_name": "unet.safetensors",
                        "vae_name": "vae.safetensors",
                        "clip_name": "clip.safetensors",
                    },
                    "input_settings": {},
                }
            )

        self.assertEqual(result, ("model", "clip", "replacement-vae"))
        stale_vae.assert_not_called()
        replacement_vae.assert_called_once_with("vae.safetensors")


if __name__ == "__main__":
    unittest.main()
