from __future__ import annotations

import json
import sys
import tempfile
import types
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import ANY, Mock, patch

from easyuse_anima.aio import native_civitai as civitai
from easyuse_anima.aio import native_metadata_budget as metadata_budget
from easyuse_anima.aio import output, output_settings
from easyuse_anima.aio.generation_defaults import AIO_GENERATION_DEFAULT_SETTINGS
from tests.comfy_host_fakes import patch_comfy_helper


def fake_folder_paths(output_root: str) -> types.ModuleType:
    module = types.ModuleType("folder_paths")
    module.output_directory = output_root
    module.get_output_directory = Mock(return_value=output_root)
    module.supported_pt_extensions = {
        ".safetensors",
        ".pt",
        ".ckpt",
        ".bin",
        ".pth",
    }
    return module


class AIOOutputMoveTests(unittest.TestCase):
    def test_output_functions_are_owned_by_canonical_modules(self):
        for name in (
            "_normalize_aio_hash_bundles",
            "_normalize_aio_civitai_hash_fetchers",
        ):
            with self.subTest(name=name):
                self.assertIs(getattr(output, name), getattr(output_settings, name))

        for name in (
            "_aio_image_saver_civitai_hash_fetcher_entries",
            "_aio_image_saver_additional_hashes",
            "_aio_lora_metadata_name",
            "_aio_prompt_with_lora_metadata",
            "_save_image_with_comfy",
            "_aio_save_filename_prefix",
            "_save_image_with_image_saver",
        ):
            with self.subTest(name=name):
                self.assertEqual(getattr(output, name).__module__, output.__name__)

    def test_normalizers_preserve_json_fallback_filtering_and_canonical_bool_seam(self):
        self.assertEqual(output_settings._normalize_aio_hash_bundles(" raw, "), ["raw"])
        self.assertEqual(output_settings._normalize_aio_hash_bundles('"json-string"'), [])

        bool_calls = []

        def as_bool(value, default):
            bool_calls.append((value, default))
            return value == "yes"

        with patch.object(output_settings, "_as_bool", side_effect=as_bool):
            result = output_settings._normalize_aio_civitai_hash_fetchers([
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
        self.assertEqual(output_settings._normalize_aio_civitai_hash_fetchers("not-json"), [])

    def test_civitai_hashes_preserve_order_success_and_soft_skip_paths(self):
        calls = []

        def fetch(username, model_name, version):
            calls.append((username, model_name, version))
            if model_name == "raises":
                raise RuntimeError("temporary")
            return {
                "empty": None,
                "good": "ABC123",
                "last": "XYZ789",
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
            patch.object(
                output,
                "_fetch_civitai_autov3_hash",
                side_effect=fetch,
            ) as fetch_mock,
            patch.object(output.logger, "warning") as warning,
        ):
            result = output._aio_image_saver_civitai_hash_fetcher_entries(settings)

        self.assertEqual(result, ["good:ABC123", "last:XYZ789"])
        self.assertEqual(
            calls,
            [("u", "good", "v1"), ("u", "empty", ""), ("u", "raises", ""), ("u", "last", "v2")],
        )
        self.assertEqual(fetch_mock.call_count, 4)
        self.assertEqual(warning.call_count, 2)

    def test_civitai_empty_and_hard_error_paths_keep_dependency_boundaries(self):
        fetch = Mock(side_effect=AssertionError("must not make a network lookup"))
        with patch.object(output, "_fetch_civitai_autov3_hash", fetch):
            self.assertEqual(
                output._aio_image_saver_civitai_hash_fetcher_entries(
                    {"civitai_hash_fetchers": [{"enabled": False, "username": "u", "model_name": "m"}]}
                ),
                [],
            )
        fetch.assert_not_called()

        with patch.object(output, "_fetch_civitai_autov3_hash", fetch):
            with self.assertRaisesRegex(RuntimeError, "both username and model_name"):
                output._aio_image_saver_civitai_hash_fetcher_entries(
                    {"civitai_hash_fetchers": [{"enabled": True, "username": "u", "version": "v"}]}
                )
        fetch.assert_not_called()

    def test_civitai_hash_fetcher_rows_are_bounded(self):
        settings = {
            "civitai_hash_fetchers": [
                {
                    "enabled": True,
                    "username": "creator",
                    "model_name": f"model-{index}",
                    "version": "",
                }
                for index in range(output._MAX_CIVITAI_HASH_FETCHERS + 5)
            ]
        }
        with (
            patch.object(output, "_fetch_civitai_autov3_hash", return_value="ABC") as fetch,
            self.assertLogs("ComfyUI-EasyUseAnima", level="WARNING") as logs,
        ):
            entries = output._aio_image_saver_civitai_hash_fetcher_entries(settings)

        self.assertEqual(len(entries), output._MAX_CIVITAI_HASH_FETCHERS)
        self.assertEqual(fetch.call_count, output._MAX_CIVITAI_HASH_FETCHERS)
        self.assertIn("ignoring 5 excess rows", "\n".join(logs.output))

    def test_repeated_civitai_timeouts_stop_at_the_shared_call_budget(self):
        civitai._fetch_civitai_autov3_hash.cache_clear()
        budget = civitai.CivitaiLookupBudget(
            timeout_seconds=100.0,
            http_call_limit=3,
        )
        transport = Mock(side_effect=TimeoutError("socket stalled"))
        settings = {
            "civitai_hash_fetchers": [
                {
                    "enabled": True,
                    "username": "creator",
                    "model_name": f"timeout-{index}",
                    "version": "",
                }
                for index in range(5)
            ]
        }

        with (
            patch.object(civitai, "_default_civitai_transport", transport),
            self.assertLogs("ComfyUI-EasyUseAnima", level="WARNING") as logs,
        ):
            self.assertEqual(
                output._aio_image_saver_civitai_hash_fetcher_entries(
                    settings,
                    budget=budget,
                ),
                [],
            )

        self.assertEqual(transport.call_count, 3)
        self.assertEqual(budget.calls_started, 3)
        self.assertIn("HTTP-call budget", "\n".join(logs.output))

    def test_fetcher_and_resource_enrichment_share_budget_and_still_save(self):
        civitai._fetch_civitai_autov3_hash.cache_clear()
        civitai._cached_civitai_resource_by_hash.cache_clear()
        budget = civitai.CivitaiLookupBudget(
            timeout_seconds=100.0,
            http_call_limit=3,
        )

        def response(payload):
            value = Mock(status_code=200, headers={})
            value.iter_content.return_value = [
                json.dumps(payload).encode("utf-8")
            ]
            return value

        def transport(endpoint, *, params, timeout):
            self.assertGreater(timeout[0], 0)
            self.assertGreater(timeout[1], 0)
            if endpoint.endswith("/models"):
                self.assertEqual(params["query"], "Shared Model")
                return response({
                    "items": [{
                        "name": "Shared Model",
                        "modelVersions": [{"id": 11, "name": "v1"}],
                    }]
                })
            if endpoint.endswith("/model-versions/11"):
                return response({
                    "files": [{"hashes": {"AutoV3": "ABCDEF1234"}}]
                })
            self.assertTrue(endpoint.endswith("/by-hash/deadbeef12"))
            return response({
                "id": 22,
                "name": "manual-v1",
                "model": {"name": "Manual Resource"},
                "files": [{"hashes": {"AutoV3": "DEADBEEF12"}}],
            })

        settings = {
            "image_saver": {
                **AIO_GENERATION_DEFAULT_SETTINGS["save"]["image_saver"],
                "filename": "budgeted",
                "path": "EasyUseAnima/Test",
                "additional_hashes": "Manual:DEADBEEF12",
                "download_civitai_data": True,
                "civitai_hash_fetchers": [{
                    "enabled": True,
                    "username": "Creator",
                    "model_name": "Shared Model",
                    "version": "v1",
                }],
            }
        }

        with tempfile.TemporaryDirectory() as temp:
            with (
                patch.dict(sys.modules, {"folder_paths": fake_folder_paths(temp)}),
                patch.object(output, "CivitaiLookupBudget", return_value=budget),
                patch.object(civitai, "_default_civitai_transport", side_effect=transport) as request,
                patch.object(output, "_save_native_images", return_value="saved") as save,
                self.assertLogs("ComfyUI-EasyUseAnima", level="WARNING") as logs,
            ):
                result = output._save_image_with_image_saver(
                    images="images",
                    save_settings=settings,
                    positive_prompt="prompt",
                    negative_prompt="",
                    width=64,
                    height=64,
                    sampler_settings={"seed": 1},
                    resource_info={"unet_name": ""},
                )

        self.assertEqual(result, "saved")
        self.assertEqual(request.call_count, 3)
        self.assertEqual(budget.calls_started, 3)
        metadata = save.call_args.kwargs["metadata"]
        self.assertIn("Manual:DEADBEEF12", metadata.final_hashes)
        self.assertIn('"modelVersionId":22', metadata.parameters)
        self.assertIn("HTTP-call budget", "\n".join(logs.output))

    def test_additional_hash_and_lora_metadata_use_canonical_helpers(self):
        with (
            patch.object(
                output,
                "_normalize_aio_hash_bundles",
                return_value=["Bundle:B"],
            ),
            patch.object(
                output,
                "_aio_image_saver_civitai_hash_fetcher_entries",
                return_value=["Model:C"],
            ),
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
            patch.object(
                output,
                "_aio_lora_metadata_name",
                side_effect=lambda value: value.replace(".safetensors", ""),
            ),
            patch.object(output, "_as_float", return_value=0.75),
            patch.object(output, "_format_strength", return_value="0.75"),
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

        with tempfile.TemporaryDirectory() as temp:
            with (
                patch.dict(sys.modules, {"folder_paths": fake_folder_paths(temp)}),
                patch_comfy_helper(
                    output,
                    "_find_comfy_node_class",
                    return_value=SaveImage,
                ) as find,
            ):
                result = output._save_image_with_comfy(
                    "images", "", workflow_prompt="prompt", extra_pnginfo={"workflow": True}
                )

        find.assert_called_once_with("SaveImage")
        self.assertEqual(
            calls,
            [(('images', "EasyUseAnima/AiO"), {"prompt": "prompt", "extra_pnginfo": {"workflow": True}})],
        )
        self.assertEqual(result, {"ui": {"images": ["saved"]}})

    def test_comfy_save_rejects_output_traversal_before_node_lookup(self):
        find = Mock(side_effect=AssertionError("must reject before node lookup"))
        with tempfile.TemporaryDirectory() as temp:
            with (
                patch.dict(sys.modules, {"folder_paths": fake_folder_paths(temp)}),
                patch_comfy_helper(output, "_find_comfy_node_class", find),
            ):
                for prefix in ("../outside", "..\\outside", "C:\\outside", "/outside"):
                    with self.subTest(prefix=prefix):
                        with self.assertRaisesRegex(RuntimeError, "output directory"):
                            output._save_image_with_comfy("images", prefix)

        find.assert_not_called()

    def test_filename_prefix_uses_call_time_defaults_without_path_drift(self):
        defaults = {"save": {"image_saver": {"path": "Default/Path", "filename": "default_name"}}}
        with patch.object(output, "AIO_GENERATION_DEFAULT_SETTINGS", defaults):
            self.assertEqual(
                output._aio_save_filename_prefix({"image_saver": {"path": " /Custom/ ", "filename": " frame "}}),
                "Custom/frame",
            )
            self.assertEqual(output._aio_save_filename_prefix({"image_saver": "invalid"}), "Default/Path/default_name")

    def test_native_image_saver_preserves_settings_and_resolves_special_seed_once(self):
        save_settings = {
            "image_saver": {
                **AIO_GENERATION_DEFAULT_SETTINGS["save"]["image_saver"],
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
        metadata = object()
        with tempfile.TemporaryDirectory() as temp:
            with (
                patch.dict(sys.modules, {"folder_paths": fake_folder_paths(temp)}),
                patch.object(output, "_resolve_aio_runtime_seed", seed),
                patch.object(
                    output,
                    "_aio_prompt_with_lora_metadata",
                    return_value="positive <lora:x:1>",
                ),
                patch.object(
                    output,
                    "_aio_image_saver_additional_hashes",
                    return_value="Base:A,Model:B",
                ),
                patch.object(
                    output,
                    "_build_native_metadata",
                    return_value=metadata,
                ) as build,
                patch.object(
                    output,
                    "_save_native_images",
                    return_value="saved",
                ) as save,
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
        build.assert_called_once_with(
            modelname="anima.safetensors",
            positive="positive <lora:x:1>",
            negative="negative",
            width=768,
            height=1024,
            seed=987654321,
            steps=30,
            cfg=6.5,
            sampler_name="euler",
            scheduler_name="normal",
            denoise=0.8,
            clip_skip=save_settings["image_saver"]["clip_skip"],
            custom=save_settings["image_saver"]["custom"],
            additional_hashes="Base:A,Model:B",
            applied_loras=[{"name": "x", "strength_model": 1}],
            download_civitai_data=save_settings["image_saver"]["download_civitai_data"],
            easy_remix=save_settings["image_saver"]["easy_remix"],
            civitai_budget=ANY,
        )
        save.assert_called_once_with(
            "images",
            output_root=Path(temp).resolve(),
            filename="frame",
            path="EasyUseAnima/Test",
            extension="webp",
            lossless_webp=save_settings["image_saver"]["lossless_webp"],
            quality_jpeg_or_webp=100,
            optimize_png=save_settings["image_saver"]["optimize_png"],
            save_workflow_as_json=save_settings["image_saver"]["save_workflow_as_json"],
            embed_workflow=save_settings["image_saver"]["embed_workflow"],
            metadata=metadata,
            prompt={"1": {}},
            extra_pnginfo={"workflow": {}},
        )

    def test_image_saver_renders_templates_before_forwarding_safe_values(self):
        settings = {
            "image_saver": {
                **AIO_GENERATION_DEFAULT_SETTINGS["save"]["image_saver"],
                "path": "renders/%time_format<%Y/%m>",
                "filename": "%custom_%counter<03>_%basemodelname",
                "custom": "safe",
                "counter": 7,
            }
        }
        fixed_now = datetime(2026, 9, 4, 12, 34, 56)

        class FixedDateTime:
            @staticmethod
            def now():
                return fixed_now

        with tempfile.TemporaryDirectory() as temp:
            with (
                patch.dict(sys.modules, {"folder_paths": fake_folder_paths(temp)}),
                patch.object(output, "datetime", FixedDateTime),
                patch.object(output, "_resolve_aio_runtime_seed", return_value=11),
                patch.object(output, "_build_native_metadata", return_value=object()),
                patch.object(
                    output,
                    "_save_native_images",
                    return_value="saved",
                ) as save,
            ):
                result = output._save_image_with_image_saver(
                    images="images",
                    save_settings=settings,
                    positive_prompt="positive",
                    negative_prompt="negative",
                    width=768,
                    height=1024,
                    sampler_settings={"seed": 11},
                    resource_info={"unet_name": "models/anima.safetensors"},
                )

        self.assertEqual(result, "saved")
        self.assertEqual(save.call_args.kwargs["path"], "renders/2026/09")
        self.assertEqual(save.call_args.kwargs["filename"], "safe_007_anima")

    def test_metadata_disabled_skips_hashing_and_civitai_work(self):
        settings = {
            "image_saver": {
                **AIO_GENERATION_DEFAULT_SETTINGS["save"]["image_saver"],
                "filename": "frame",
                "path": "EasyUseAnima/Test",
            }
        }
        with tempfile.TemporaryDirectory() as temp:
            with (
                patch.dict(sys.modules, {"folder_paths": fake_folder_paths(temp)}),
                patch.object(output, "_comfy_metadata_enabled", return_value=False),
                patch.object(output, "_resolve_aio_runtime_seed", return_value=11),
                patch.object(output, "_build_native_metadata") as build,
                patch.object(output, "_aio_image_saver_additional_hashes") as hashes,
                patch.object(
                    output,
                    "_save_native_images",
                    return_value="saved",
                ) as save,
            ):
                result = output._save_image_with_image_saver(
                    images="images",
                    save_settings=settings,
                    positive_prompt="positive",
                    negative_prompt="negative",
                    width=768,
                    height=1024,
                    sampler_settings={"seed": 11},
                    applied_loras=[{"name": "x.safetensors", "strength_model": 1}],
                    resource_info={"unet_name": "anima.safetensors"},
                )

        self.assertEqual(result, "saved")
        build.assert_not_called()
        hashes.assert_not_called()
        metadata = save.call_args.kwargs["metadata"]
        self.assertEqual(metadata.parameters, "")
        self.assertEqual(metadata.final_hashes, "")
        self.assertEqual(metadata.hashes, {})

    def test_oversized_prompt_is_rejected_before_lora_metadata_expansion(self):
        settings = {
            "image_saver": {
                **AIO_GENERATION_DEFAULT_SETTINGS["save"]["image_saver"],
                "filename": "frame",
                "path": "EasyUseAnima/Test",
            }
        }
        with tempfile.TemporaryDirectory() as temp:
            with (
                patch.dict(sys.modules, {"folder_paths": fake_folder_paths(temp)}),
                patch.object(
                    output,
                    "_validate_parameter_sources",
                    side_effect=metadata_budget.MetadataLimitError("too large"),
                ),
                patch.object(output, "_aio_prompt_with_lora_metadata") as expand,
                patch.object(output, "_save_native_images") as save,
                self.assertRaises(metadata_budget.MetadataLimitError),
            ):
                output._save_image_with_image_saver(
                    images="images",
                    save_settings=settings,
                    positive_prompt="oversized",
                    negative_prompt="",
                    width=512,
                    height=512,
                    sampler_settings={"seed": 1},
                )

        expand.assert_not_called()
        save.assert_not_called()

    def test_image_saver_rejects_expanded_output_escape_before_dependency_lookup(self):
        cases = (
            {"path": "../../outside"},
            {"path": "..\\..\\outside"},
            {"path": "C:\\outside"},
            {"path": "/outside"},
            {"path": "%custom", "custom": "../../outside"},
            {"path": "%time", "time_format": "../outside"},
            {"filename": "%custom", "custom": "../outside"},
        )
        save = Mock(side_effect=AssertionError("must reject before native writer"))
        with tempfile.TemporaryDirectory() as temp:
            for override in cases:
                settings = {
                    "image_saver": {
                        **AIO_GENERATION_DEFAULT_SETTINGS["save"]["image_saver"],
                        **override,
                    }
                }
                with self.subTest(override=override):
                    with (
                        patch.dict(sys.modules, {"folder_paths": fake_folder_paths(temp)}),
                        patch.object(output, "_save_native_images", save),
                        patch.object(output, "_resolve_aio_runtime_seed", return_value=11),
                    ):
                        with self.assertRaisesRegex(RuntimeError, "output directory|single filename"):
                            output._save_image_with_image_saver(
                                images="images",
                                save_settings=settings,
                                positive_prompt="positive",
                                negative_prompt="negative",
                                width=768,
                                height=1024,
                                sampler_settings={"seed": 11},
                                resource_info={"unet_name": "anima.safetensors"},
                            )

        save.assert_not_called()


if __name__ == "__main__":
    unittest.main()
