from __future__ import annotations

import sys
import types
import unittest
from unittest.mock import Mock, patch

import nodes
from easyuse_anima.aio import preview
from tests.comfy_host_fakes import patch_comfy_helper


class AIOPreviewMoveTests(unittest.TestCase):
    def test_root_constants_and_functions_are_direct_canonical_aliases(self):
        for name in (
            "AIO_PREVIEW_STAGE_LABELS",
            "AIO_PREVIEW_EVENT",
            "AIO_PREVIEW_CACHE_FORMAT",
            "AIO_PREVIEW_CACHE_QUALITY",
            "_aio_preview_base_directory",
            "_aio_preview_file_size_bytes",
            "_tag_aio_preview_images",
            "_send_aio_preview_event",
            "_save_aio_temp_preview_image",
        ):
            with self.subTest(name=name):
                self.assertIs(getattr(nodes, name), getattr(preview, name))

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
            patch_comfy_helper(
                nodes,
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


if __name__ == "__main__":
    unittest.main()
