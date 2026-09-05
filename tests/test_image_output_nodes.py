from __future__ import annotations

import json
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np
from PIL import ExifTags, Image

from easyuse_anima.nodes import image_output_nodes as output


class ImageOutputNodeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.images = np.full((1, 8, 12, 3), 0.5, dtype=np.float32)
        folder_paths = types.ModuleType("folder_paths")
        folder_paths.get_output_directory = lambda: str(self.root)
        folder_paths.get_filename_list = lambda _folder: []
        modules = patch.dict(sys.modules, {"folder_paths": folder_paths})
        modules.start()
        self.addCleanup(modules.stop)
        enabled = patch.object(output, "_comfy_metadata_enabled", return_value=True)
        enabled.start()
        self.addCleanup(enabled.stop)
        self.metadata_node = output.EasyUseAnimaImageMetadata()
        self.saver = output.EasyUseAnimaSaveImage()

    def metadata(self, **kwargs):
        return self.metadata_node.build(
            self.images, positive="푸른 하늘, blue sky", negative="blur", seed=42,
            sampler_name="euler_ancestral", scheduler_name="karras", **kwargs,
        )

    def saved_path(self, result):
        image = result["ui"]["images"][0]
        self.assertEqual(image["type"], "output")
        return self.root / image["subfolder"] / image["filename"]

    def test_metadata_builder_uses_final_dimensions_and_has_no_output_side_effects(self):
        metadata, parameters = self.metadata()
        self.assertEqual(metadata.metadata.parameters, parameters)
        self.assertIn("Size: 12x8", parameters)
        self.assertIn("Seed: 42", parameters)
        self.assertIn("Sampler: Euler a Karras", parameters)
        self.assertIn("Negative prompt: blur", parameters)
        self.assertEqual(list(self.root.iterdir()), [])

    def test_png_metadata_workflow_sidecar_and_collision_roundtrip(self):
        metadata, parameters = self.metadata(save_workflow_as_json=True)
        workflow = {"nodes": [], "extra": {"title": "메타데이터"}}
        prompt = {"1": {"class_type": "EasyUseAnimaSaveImage", "inputs": {}}}
        args = dict(
            path="album/session", filename="image", exif_metadata=metadata,
            prompt=prompt, extra_pnginfo={"workflow": workflow},
        )
        first = self.saved_path(self.saver.save_images(self.images, **args))
        with Image.open(first) as image:
            self.assertEqual(image.size, (12, 8))
            self.assertEqual(image.info["parameters"], parameters)
            self.assertEqual(json.loads(image.info["prompt"]), prompt)
            self.assertEqual(json.loads(image.info["workflow"]), workflow)
        self.assertEqual(json.loads(first.with_suffix(".json").read_text("utf-8")), workflow)
        original = first.read_bytes()
        second = self.saved_path(self.saver.save_images(self.images, **args))
        self.assertNotEqual(first, second)
        self.assertEqual(first.read_bytes(), original)

    def test_jpeg_and_webp_unicode_exif_roundtrip(self):
        metadata, parameters = self.metadata(embed_workflow=False)
        for extension in ("jpg", "jpeg", "webp"):
            with self.subTest(extension=extension):
                saved = self.saved_path(self.saver.save_images(
                    self.images, extension=extension, exif_metadata=metadata,
                    lossless_webp=True,
                ))
                with Image.open(saved) as image:
                    comment = image.getexif().get_ifd(ExifTags.IFD.Exif)[0x9286]
                    self.assertEqual(comment[:8], b"UNICODE\0")
                    self.assertEqual(comment[8:].decode("utf-16-be"), parameters)
                    self.assertNotIn(0x0110, image.getexif())

    def test_disconnected_metadata_saves_pixels_only_even_with_hidden_workflow(self):
        for extension in ("png", "jpeg", "webp"):
            with self.subTest(extension=extension):
                saved = self.saved_path(self.saver.save_images(
                    self.images, extension=extension, prompt={"private": "prompt"},
                    extra_pnginfo={"workflow": {"nodes": []}},
                ))
                with Image.open(saved) as image:
                    self.assertNotIn("parameters", image.info)
                    self.assertNotIn("prompt", image.info)
                    self.assertNotIn("workflow", image.info)
                    self.assertFalse(image.getexif())
                self.assertFalse(saved.with_suffix(".json").exists())

    def test_global_privacy_skips_builder_and_suppresses_cached_metadata_at_save(self):
        previous_metadata, _ = self.metadata(save_workflow_as_json=True)
        with patch.object(output, "_comfy_metadata_enabled", return_value=False):
            with patch.object(output, "_build_native_metadata") as build:
                metadata, parameters = self.metadata()
                build.assert_not_called()
                self.assertEqual(parameters, "")
                self.assertEqual(metadata.metadata.hashes, {})
            self.assertFalse(output.EasyUseAnimaImageMetadata.IS_CHANGED())
            saved = self.saved_path(self.saver.save_images(
                self.images, exif_metadata=previous_metadata,
                extra_pnginfo={"workflow": {"nodes": []}},
            ))
        with Image.open(saved) as image:
            self.assertNotIn("parameters", image.info)
            self.assertNotIn("workflow", image.info)
        self.assertFalse(saved.with_suffix(".json").exists())

    def test_unsafe_paths_and_literal_metadata_are_rejected_before_writing(self):
        for path in ("../escape", "/absolute", "C:\\outside", "safe/../../escape"):
            with self.subTest(path=path), self.assertRaises(RuntimeError):
                self.saver.save_images(self.images, path=path)
        with self.assertRaises(ValueError):
            self.saver.save_images(self.images, exif_metadata={"parameters": "untyped"})
        self.assertEqual(list(self.root.iterdir()), [])

    def test_batch_files_and_encoder_controls(self):
        from easyuse_anima.aio import native_image_output as native

        with patch.object(native, "_image_save_options", wraps=native._image_save_options) as options:
            result = self.saver.save_images(
                np.repeat(self.images, 2, axis=0), extension="webp",
                quality=73, lossless_webp=True, optimize_png=False,
            )
        self.assertEqual(len(result["ui"]["images"]), 2)
        for call in options.call_args_list:
            self.assertEqual(call.kwargs["quality"], 73)
            self.assertTrue(call.kwargs["lossless_webp"])
        for entry in result["ui"]["images"]:
            with Image.open(self.root / entry["filename"]) as image:
                self.assertEqual(image.getpixel((0, 0)), (127, 127, 127))

    def test_registration_and_socket_contract(self):
        from easyuse_anima.registration import NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS

        self.assertIs(NODE_CLASS_MAPPINGS["EasyUseAnimaSaveImage"], output.EasyUseAnimaSaveImage)
        self.assertEqual(NODE_DISPLAY_NAME_MAPPINGS["EasyUseAnimaSaveImage"], "Easy Save Image")
        self.assertEqual(NODE_DISPLAY_NAME_MAPPINGS["EasyUseAnimaImageMetadata"], "Easy Image Metadata")
        socket = self.saver.INPUT_TYPES()["optional"]["exif_metadata"][0]
        self.assertEqual(socket, self.metadata_node.RETURN_TYPES[0])
        self.assertEqual(self.saver.RETURN_TYPES, ())
        self.assertTrue(self.saver.OUTPUT_NODE)
        self.assertFalse(self.metadata_node.INPUT_TYPES()["required"]["seed"][1]["control_after_generate"])


if __name__ == "__main__":
    unittest.main()
