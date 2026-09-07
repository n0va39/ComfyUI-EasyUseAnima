from __future__ import annotations

import json
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import numpy as np
from PIL import Image

from easyuse_anima.aio import native_metadata_budget
from easyuse_anima.aio import preview
from easyuse_anima.aio.execution_metadata import snapshot_aio_execution_metadata
from tests.comfy_host_fakes import patch_comfy_helper


class _PreviewTensor:
    def __init__(self, array):
        self.array = array
        self.shape = array.shape

    def __len__(self):
        return len(self.array)

    def __iter__(self):
        return (_PreviewTensor(image) for image in self.array)

    def detach(self):
        return self

    def cpu(self):
        return self

    def numpy(self):
        return self.array


def _temp_folder_paths(directory):
    folder_paths = types.ModuleType("folder_paths")
    folder_paths.get_temp_directory = Mock(return_value=str(directory))
    folder_paths.get_save_image_path = Mock(
        return_value=(str(directory), "preview_%batch_num%", 1, "", None)
    )
    return folder_paths


class AIOPreviewMoveTests(unittest.TestCase):
    def test_base_directory_preserves_lazy_folder_paths_selection_and_failure(self):
        folder_paths = types.ModuleType("folder_paths")
        folder_paths.get_temp_directory = Mock(return_value="temp-root")
        folder_paths.get_input_directory = Mock(return_value="input-root")
        folder_paths.get_output_directory = Mock(return_value="output-root")

        with patch.dict(sys.modules, {"folder_paths": folder_paths}):
            self.assertEqual(preview._aio_preview_base_directory("temp"), "temp-root")
            self.assertEqual(preview._aio_preview_base_directory("input"), "input-root")
            self.assertEqual(preview._aio_preview_base_directory("other"), "output-root")

        with patch.dict(sys.modules, {"folder_paths": None}):
            self.assertEqual(preview._aio_preview_base_directory("temp"), "")

    def test_file_size_re_resolves_root_base_directory_and_preserves_path_rules(self):
        replacement = Mock(return_value="preview-root")
        with (
            patch.object(preview, "_aio_preview_base_directory", replacement),
            patch.object(preview.os.path, "isfile", return_value=True) as isfile,
            patch.object(preview.os.path, "getsize", return_value=321) as getsize,
        ):
            size = preview._aio_preview_file_size_bytes(
                {"filename": "image.webp", "subfolder": "nested", "type": "temp"}
            )

        self.assertEqual(size, 321)
        replacement.assert_called_once_with("temp")
        expected_path = preview.os.path.join("preview-root", "nested", "image.webp")
        isfile.assert_called_once_with(expected_path)
        getsize.assert_called_once_with(expected_path)
        self.assertEqual(preview._aio_preview_file_size_bytes({}), 0)

    def test_tagging_re_resolves_file_size_and_preserves_metadata_order(self):
        source = {"filename": "image.webp", "type": "temp"}
        file_size = Mock(return_value=1234)
        with patch.object(preview, "_aio_preview_file_size_bytes", file_size):
            tagged = preview._tag_aio_preview_images(
                [source, "skip"], "highres", width=768, height=1024
            )

        self.assertEqual(
            tagged,
            [
                {
                    "filename": "image.webp",
                    "type": "temp",
                    "stage": "highres",
                    "label": "Highres",
                    "width": 768,
                    "height": 1024,
                    "bytes": 1234,
                }
            ],
        )
        self.assertEqual(list(tagged[0]), ["filename", "type", "stage", "label", "width", "height", "bytes"])
        self.assertNotIn("stage", source)
        file_size.assert_called_once_with(tagged[0] | {})

    def test_event_preserves_payload_client_and_call_time_root_values(self):
        send_sync = Mock()
        instance = types.SimpleNamespace(send_sync=send_sync, client_id="client-7")
        server = types.ModuleType("server")
        server.PromptServer = types.SimpleNamespace(instance=instance)
        json_safe = Mock(return_value=[{"safe": True}])

        with (
            patch.dict(sys.modules, {"server": server}),
            patch.object(preview, "_single_value", return_value=86),
            patch.object(preview, "_prompt_data_json_safe", json_safe),
            patch.object(preview, "AIO_PREVIEW_EVENT", "replacement-event"),
        ):
            preview._send_aio_preview_event(
                [86], "run-1", "first_pass", [{"filename": "preview.webp"}]
            )

        send_sync.assert_called_once_with(
            "replacement-event",
            {
                "node": "86",
                "run_id": "run-1",
                "stage": "first_pass",
                "images": [{"safe": True}],
            },
            "client-7",
        )

    def test_event_failure_is_debug_only_and_empty_inputs_do_not_import_server(self):
        with patch.object(preview, "_single_value", return_value=None):
            preview._send_aio_preview_event(None, "run", "final", [{"x": 1}])

        send_sync = Mock(side_effect=RuntimeError("send failed"))
        server = types.ModuleType("server")
        server.PromptServer = types.SimpleNamespace(
            instance=types.SimpleNamespace(send_sync=send_sync, client_id=None)
        )
        with (
            patch.dict(sys.modules, {"server": server}),
            patch.object(preview, "_single_value", return_value=1),
            patch.object(preview.logger, "debug") as debug,
        ):
            preview._send_aio_preview_event(1, "run", "final", [{"x": 1}])

        debug.assert_called_once()
        self.assertIn("failed to send AiO preview event", debug.call_args.args[0])

    def test_webp_save_preserves_filename_quality_order_and_tagging(self):
        saves: list[tuple[object, ...]] = []

        class Array:
            def __rmul__(self, _value):
                return self

            def astype(self, dtype):
                return ("pixels", dtype)

        class BatchImage:
            def detach(self):
                return self

            def cpu(self):
                return self

            def numpy(self):
                return Array()

        class SavedImage:
            def save(self, *args, **kwargs):
                saves.append((*args, kwargs))

        folder_paths = types.ModuleType("folder_paths")
        folder_paths.get_temp_directory = Mock(return_value="temp-root")
        folder_paths.get_save_image_path = Mock(
            return_value=("full-root", "preview_%batch_num%", 3, "sub", None)
        )
        numpy = types.ModuleType("numpy")
        numpy.uint8 = "uint8"
        numpy.clip = Mock(side_effect=lambda value, _lo, _hi: value)
        pil = types.ModuleType("PIL")
        pil.Image = types.SimpleNamespace(fromarray=Mock(return_value=SavedImage()))
        tag = Mock(return_value=[{"tagged": True}])

        with (
            patch.dict(sys.modules, {"folder_paths": folder_paths, "numpy": numpy, "PIL": pil}),
            patch.object(preview, "_image_tensor_size", return_value=(640, 960)),
            patch.object(preview, "_tag_aio_preview_images", tag),
            patch.object(preview, "AIO_PREVIEW_CACHE_FORMAT", "webp"),
            patch.object(preview, "AIO_PREVIEW_CACHE_QUALITY", 90),
            patch.object(preview.random, "choice", return_value="a"),
        ):
            result = preview._save_aio_temp_preview_image(
                [BatchImage(), BatchImage()], "first_pass"
            )

        self.assertEqual(result, [{"tagged": True}])
        self.assertEqual(
            folder_paths.get_save_image_path.call_args.args,
            ("EasyUseAnima_AiO_first_pass_temp_aaaaa", "temp-root", 640, 960),
        )
        self.assertEqual(
            [call[0] for call in saves],
            [
                preview.os.path.join("full-root", "preview_0_00003_.webp"),
                preview.os.path.join("full-root", "preview_1_00004_.webp"),
            ],
        )
        self.assertTrue(all(call[1] == {"format": "WEBP", "quality": 90, "method": 4} for call in saves))
        tag.assert_called_once_with(
            [
                {"filename": "preview_0_00003_.webp", "subfolder": "sub", "type": "temp"},
                {"filename": "preview_1_00004_.webp", "subfolder": "sub", "type": "temp"},
            ],
            "first_pass",
            width=640,
            height=960,
        )

    def test_png_fallback_preserves_typeerror_retry_and_tagging(self):
        calls: list[tuple[tuple[object, ...], dict[str, object]]] = []

        class PreviewImage:
            def save_images(self, *args, **kwargs):
                calls.append((args, kwargs))
                if kwargs:
                    raise TypeError("legacy signature")
                return {"ui": {"images": [{"filename": "fallback.png", "type": "temp"}]}}

        tag = Mock(return_value=[{"fallback": True}])
        with (
            patch.dict(sys.modules, {"folder_paths": None}),
            patch.object(preview, "_image_tensor_size", return_value=(512, 768)),
            patch.object(preview, "_comfy_metadata_enabled", return_value=True),
            patch_comfy_helper(
                preview,
                "_find_comfy_node_class",
                return_value=PreviewImage,
            ),
            patch.object(preview, "_tag_aio_preview_images", tag),
            patch.object(preview.logger, "warning") as warning,
        ):
            result = preview._save_aio_temp_preview_image(
                "image",
                "final",
                workflow_prompt="prompt",
                extra_pnginfo={"workflow": True},
            )

        self.assertEqual(result, [{"fallback": True}])
        self.assertEqual(len(calls), 2)
        self.assertEqual(
            calls[0],
            (
                ("image",),
                {
                    "filename_prefix": "EasyUseAnima_AiO_final",
                    "prompt": "prompt",
                    "extra_pnginfo": {"workflow": True},
                },
            ),
        )
        self.assertEqual(calls[1], (("image",), {}))
        self.assertIn("Failed to save AiO WebP preview", warning.call_args_list[0].args[0])
        tag.assert_called_once_with(
            [{"filename": "fallback.png", "type": "temp"}],
            "final",
            width=512,
            height=768,
        )

    def test_final_webp_batch_round_trips_executed_prompt_and_workflow_when_save_is_off(self):
        original_settings = {"sampler": {"seed": -1}, "save": {"enabled": False}}
        prompt = {"7": {"class_type": "EasyUseAnimaAIOGenerator", "inputs": {"generation_settings": json.dumps(original_settings)}}}
        extra = {"workflow": {"nodes": [{"id": 7, "type": "EasyUseAnimaAIOGenerator", "widgets_values": [json.dumps(original_settings)]}]}}
        settings = {"sampler": {"seed": 17}, "save": {"enabled": False}}
        prompt_snapshot, extra_snapshot = snapshot_aio_execution_metadata(prompt, extra, "7", settings, {"note": "실행 기록"})
        images = _PreviewTensor(np.zeros((2, 4, 6, 3), dtype=np.float32))
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with (
                patch.dict(sys.modules, {"folder_paths": _temp_folder_paths(root)}),
                patch.object(preview, "_comfy_metadata_enabled", return_value=True),
                patch.object(preview, "_find_comfy_node_class", side_effect=AssertionError("No PNG fallback expected")),
            ):
                results = preview._save_aio_temp_preview_image(images, "final", workflow_prompt=prompt_snapshot, extra_pnginfo=extra_snapshot)
            self.assertEqual(len(results), 2)
            for result in results:
                self.assertEqual(result["stage"], "final")
                self.assertEqual(result["type"], "temp")
                self.assertEqual((result["width"], result["height"]), (6, 4))
                with Image.open(root / result["filename"]) as saved:
                    self.assertEqual(saved.format, "WEBP")
                    self.assertEqual(saved.size, (6, 4))
                    exif = saved.getexif()
                    saved_prompt = json.loads(exif[0x0110].removeprefix("prompt:"))
                    saved_workflow = json.loads(exif[0x010F].removeprefix("workflow:"))
                    self.assertEqual(saved_prompt, prompt_snapshot)
                    self.assertEqual(saved_workflow, extra_snapshot["workflow"])
                    self.assertEqual(json.loads(saved_prompt["7"]["inputs"]["generation_settings"])["sampler"]["seed"], 17)
                    self.assertEqual(json.loads(saved_workflow["nodes"][0]["widgets_values"][0])["sampler"]["seed_after_generate"], "fixed")
            self.assertEqual(list(root.glob("*.json")), [])

    def test_intermediate_and_metadata_disabled_final_webp_remain_pixels_only(self):
        images = _PreviewTensor(np.zeros((1, 4, 6, 3), dtype=np.float32))
        for stage, metadata_enabled in (("first_pass", True), ("final", False)):
            with self.subTest(stage=stage, metadata_enabled=metadata_enabled), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                with (
                    patch.dict(sys.modules, {"folder_paths": _temp_folder_paths(root)}),
                    patch.object(preview, "_comfy_metadata_enabled", return_value=metadata_enabled),
                    patch.object(preview, "_serialize_metadata", side_effect=AssertionError("Pixels-only previews must not serialize metadata")),
                ):
                    results = preview._save_aio_temp_preview_image(images, stage, workflow_prompt={"private": "prompt"}, extra_pnginfo={"workflow": {"private": "workflow"}})
                self.assertEqual(len(results), 1)
                with Image.open(root / results[0]["filename"]) as saved:
                    self.assertEqual(saved.format, "WEBP")
                    self.assertEqual(len(saved.getexif()), 0)
                    self.assertNotIn("prompt", saved.info)
                    self.assertNotIn("workflow", saved.info)

    def test_final_metadata_size_limits_apply_before_image_publication_or_png_fallback(self):
        images = _PreviewTensor(np.zeros((2, 4, 6, 3), dtype=np.float32))
        for limit_name, message in (("_MAX_WORKFLOW_JSON_BYTES", "workflow JSON"), ("_MAX_SAVE_METADATA_BYTES", "batch metadata")):
            with self.subTest(limit_name=limit_name), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                folder_paths = _temp_folder_paths(root)
                with (
                    patch.dict(sys.modules, {"folder_paths": folder_paths}),
                    patch.object(preview, "_comfy_metadata_enabled", return_value=True),
                    patch.object(native_metadata_budget, limit_name, 1),
                    patch.object(preview, "_find_comfy_node_class", side_effect=AssertionError("Metadata limits must not fall back")),
                    self.assertRaisesRegex(native_metadata_budget.MetadataLimitError, message),
                ):
                    preview._save_aio_temp_preview_image(images, "final", workflow_prompt={}, extra_pnginfo={"workflow": {"nodes": []}})
                folder_paths.get_save_image_path.assert_not_called()
                self.assertEqual(list(root.iterdir()), [])

    def test_png_fallback_remains_pixels_only_for_intermediate_or_disabled_metadata(self):
        for stage, metadata_enabled in (("first_pass", True), ("final", False)):
            with self.subTest(stage=stage, metadata_enabled=metadata_enabled):
                save = Mock(return_value={"ui": {"images": [{"filename": "fallback.png", "type": "temp"}]}})
                fallback = Mock(return_value=types.SimpleNamespace(save_images=save))
                with (
                    patch.dict(sys.modules, {"folder_paths": None}),
                    patch.object(preview, "_comfy_metadata_enabled", return_value=metadata_enabled),
                    patch.object(preview, "_find_comfy_node_class", return_value=fallback),
                    patch.object(preview, "_tag_aio_preview_images", side_effect=lambda images, *_args, **_kwargs: images),
                    patch.object(preview.logger, "warning"),
                ):
                    results = preview._save_aio_temp_preview_image("image", stage, workflow_prompt={"private": "prompt"}, extra_pnginfo={"workflow": {"private": "workflow"}})
                self.assertEqual(len(results), 1)
                self.assertIsNone(save.call_args.kwargs["prompt"])
                self.assertIsNone(save.call_args.kwargs["extra_pnginfo"])


if __name__ == "__main__":
    unittest.main()
