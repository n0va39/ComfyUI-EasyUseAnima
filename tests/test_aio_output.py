from __future__ import annotations

import sys
import types
import unittest
from unittest.mock import Mock, patch

import nodes
from easyuse_anima.aio import output


class AIOOutputMoveTests(unittest.TestCase):
    def test_root_functions_are_direct_canonical_aliases(self):
        for name in (
            "_normalize_aio_hash_bundles",
            "_normalize_aio_civitai_hash_fetchers",
            "_aio_image_saver_civitai_hash_fetcher_entries",
            "_aio_image_saver_additional_hashes",
            "_aio_lora_metadata_name",
            "_aio_prompt_with_lora_metadata",
            "_save_image_with_comfy",
            "_aio_save_filename_prefix",
            "_save_image_with_image_saver",
        ):
            with self.subTest(name=name):
                self.assertIs(getattr(nodes, name), getattr(output, name))

    def test_normalizers_preserve_json_fallback_filtering_and_root_bool_seam(self):
        self.assertEqual(output._normalize_aio_hash_bundles(" raw, "), ["raw"])
        self.assertEqual(output._normalize_aio_hash_bundles('"json-string"'), [])

        bool_calls = []

        def as_bool(value, default):
            bool_calls.append((value, default))
            return value == "yes"

        with patch.object(nodes, "_as_bool", side_effect=as_bool):
            result = output._normalize_aio_civitai_hash_fetchers([
                {"enabled": "yes", "username": " user ", "model_name": " model ", "version": " v1 "},
                {"enabled": "no", "version": "only-version"},
                {"ignored": True},
                "skip",
            ])

        self.assertEqual(
            result,
            [
                {"enabled": True, "username": "user", "model_name": "model", "version": "v1"},
                {"enabled": False, "username": "", "model_name": "", "version": "only-version"},
            ],
        )
        self.assertEqual(bool_calls, [("yes", True), ("no", True)])
        self.assertEqual(output._normalize_aio_civitai_hash_fetchers("not-json"), [])

    def test_civitai_hashes_preserve_order_success_and_soft_skip_paths(self):
        calls = []

        class Fetcher:
            def get_autov3_hash(self, username, model_name, version):
                calls.append((username, model_name, version))
                if model_name == "raises":
                    raise RuntimeError("temporary")
                return {
                    "empty": ("No matching model",),
                    "good": ("ABC123",),
                    "last": ("XYZ789",),
                }[model_name]

        settings = {
            "civitai_hash_fetchers": [
                {"enabled": True, "username": "u", "model_name": "good", "version": "v1"},
                {"enabled": False, "username": "u", "model_name": "disabled", "version": ""},
                {"enabled": True, "username": "u", "model_name": "empty", "version": ""},
                {"enabled": True, "username": "u", "model_name": "raises", "version": ""},
                {"enabled": True, "username": "u", "model_name": "last", "version": "v2"},
            ]
        }
        with (
            patch.object(nodes, "_require_custom_node_class", return_value=Fetcher) as require,
            patch.object(nodes.logger, "warning") as warning,
        ):
            result = output._aio_image_saver_civitai_hash_fetcher_entries(settings)

        self.assertEqual(result, ["good:ABC123", "last:XYZ789"])
        self.assertEqual(
            calls,
            [("u", "good", "v1"), ("u", "empty", ""), ("u", "raises", ""), ("u", "last", "v2")],
        )
        self.assertEqual(require.call_count, 1)
        self.assertEqual(warning.call_count, 2)

    def test_civitai_empty_and_hard_error_paths_keep_dependency_boundaries(self):
        require = Mock(side_effect=AssertionError("must not resolve dependency"))
        with patch.object(nodes, "_require_custom_node_class", require):
            self.assertEqual(
                output._aio_image_saver_civitai_hash_fetcher_entries(
                    {"civitai_hash_fetchers": [{"enabled": False, "username": "u", "model_name": "m"}]}
                ),
                [],
            )
        require.assert_not_called()

        class Fetcher:
            def get_autov3_hash(self, *_args):
                return ("unused",)

        with patch.object(nodes, "_require_custom_node_class", return_value=Fetcher):
            with self.assertRaisesRegex(RuntimeError, "both username and model_name"):
                output._aio_image_saver_civitai_hash_fetcher_entries(
                    {"civitai_hash_fetchers": [{"enabled": True, "username": "u", "version": "v"}]}
                )

    def test_additional_hash_and_lora_metadata_re_resolve_root_helpers(self):
        with (
            patch.object(nodes, "_normalize_aio_hash_bundles", return_value=["Bundle:B"]),
            patch.object(nodes, "_aio_image_saver_civitai_hash_fetcher_entries", return_value=["Model:C"]),
        ):
            hashes = output._aio_image_saver_additional_hashes({
                "additional_hashes": " Base:A, ",
                "additional_hash_bundles": "ignored",
            })
        self.assertEqual(hashes, "Base:A,Bundle:B,Model:C")

        folder_paths = types.ModuleType("folder_paths")
        folder_paths.supported_pt_extensions = {".custom"}
        with patch.dict(sys.modules, {"folder_paths": folder_paths}):
            self.assertEqual(output._aio_lora_metadata_name(" styles\\foo.custom "), "styles/foo")
            self.assertEqual(output._aio_lora_metadata_name("styles/foo.safetensors"), "styles/foo.safetensors")
        with patch.dict(sys.modules, {"folder_paths": None}):
            self.assertEqual(output._aio_lora_metadata_name("styles/foo.safetensors"), "styles/foo")

        with (
            patch.object(nodes, "_aio_lora_metadata_name", side_effect=lambda value: value.replace(".safetensors", "")),
            patch.object(nodes, "_as_float", return_value=0.75),
            patch.object(nodes, "_format_strength", return_value="0.75"),
        ):
            prompt = output._aio_prompt_with_lora_metadata(
                "base", [{"name": "foo.safetensors", "strength_model": "0.75"}]
            )
        self.assertEqual(prompt, "base <lora:foo:0.75>")

    def test_comfy_save_preserves_lookup_signature_and_return(self):
        calls = []

        class SaveImage:
            def save_images(self, *args, **kwargs):
                calls.append((args, kwargs))
                return {"ui": {"images": ["saved"]}}

        with patch.object(nodes, "_find_comfy_node_class", return_value=SaveImage) as find:
            result = output._save_image_with_comfy(
                "images", "", workflow_prompt="prompt", extra_pnginfo={"workflow": True}
            )

        find.assert_called_once_with("SaveImage")
        self.assertEqual(
            calls,
            [(('images', "EasyUseAnima/AiO"), {"prompt": "prompt", "extra_pnginfo": {"workflow": True}})],
        )
        self.assertEqual(result, {"ui": {"images": ["saved"]}})

    def test_filename_prefix_uses_call_time_defaults_without_path_drift(self):
        defaults = {"save": {"image_saver": {"path": "Default/Path", "filename": "default_name"}}}
        with patch.object(nodes, "AIO_GENERATION_DEFAULT_SETTINGS", defaults):
            self.assertEqual(
                output._aio_save_filename_prefix({"image_saver": {"path": " /Custom/ ", "filename": " frame "}}),
                "Custom/frame",
            )
            self.assertEqual(output._aio_save_filename_prefix({"image_saver": "invalid"}), "Default/Path/default_name")

    def test_image_saver_preserves_exact_kwargs_and_resolves_special_seed_once(self):
        calls = []

        class ImageSaver:
            def save_files(self, **kwargs):
                calls.append(kwargs)
                return "saved"

        save_settings = {
            "image_saver": {
                **nodes.AIO_GENERATION_DEFAULT_SETTINGS["save"]["image_saver"],
                "filename": "frame",
                "path": "EasyUseAnima/Test",
                "extension": "webp",
                "quality_jpeg_or_webp": 150,
                "counter": -3,
                "save_prompt_metadata": True,
                "additional_hashes": "Base:A",
            }
        }
        seed = Mock(return_value=987654321)
        with (
            patch.object(nodes, "_require_custom_node_class", return_value=ImageSaver),
            patch.object(nodes, "_resolve_aio_runtime_seed", seed),
            patch.object(nodes, "_aio_prompt_with_lora_metadata", return_value="positive <lora:x:1>"),
            patch.object(nodes, "_aio_image_saver_additional_hashes", return_value="Base:A,Model:B"),
        ):
            result = output._save_image_with_image_saver(
                images="images",
                save_settings=save_settings,
                positive_prompt="positive",
                negative_prompt="negative",
                width=768,
                height=1024,
                sampler_settings={
                    "steps": 30,
                    "cfg": 6.5,
                    "sampler_name": "euler",
                    "scheduler": "normal",
                    "seed": -1,
                    "denoise": 0.8,
                },
                applied_loras=[{"name": "x", "strength_model": 1}],
                resource_info={"unet_name": "anima.safetensors"},
                workflow_prompt={"1": {}},
                extra_pnginfo={"workflow": {}},
            )

        self.assertEqual(result, "saved")
        seed.assert_called_once_with(-1)
        self.assertEqual(
            calls[0],
            {
                "images": "images",
                "filename": "frame",
                "path": "EasyUseAnima/Test",
                "extension": "webp",
                "steps": 30,
                "cfg": 6.5,
                "modelname": "anima.safetensors",
                "sampler_name": "euler",
                "scheduler_name": "normal",
                "positive": "positive <lora:x:1>",
                "negative": "negative",
                "seed_value": 987654321,
                "width": 768,
                "height": 1024,
                "lossless_webp": save_settings["image_saver"]["lossless_webp"],
                "quality_jpeg_or_webp": 100,
                "optimize_png": save_settings["image_saver"]["optimize_png"],
                "counter": 0,
                "denoise": 0.8,
                "clip_skip": save_settings["image_saver"]["clip_skip"],
                "time_format": save_settings["image_saver"]["time_format"],
                "save_workflow_as_json": save_settings["image_saver"]["save_workflow_as_json"],
                "embed_workflow": save_settings["image_saver"]["embed_workflow"],
                "additional_hashes": "Base:A,Model:B",
                "download_civitai_data": save_settings["image_saver"]["download_civitai_data"],
                "easy_remix": save_settings["image_saver"]["easy_remix"],
                "show_preview": False,
                "custom": save_settings["image_saver"]["custom"],
                "prompt": {"1": {}},
                "extra_pnginfo": {"workflow": {}},
            },
        )


if __name__ == "__main__":
    unittest.main()
