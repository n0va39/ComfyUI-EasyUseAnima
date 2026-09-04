from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import numpy as np
from PIL import ExifTags, Image

from easyuse_anima.aio import native_civitai as civitai
from easyuse_anima.aio import native_image_output as native


class FakeTensor:
    def __init__(self, value: np.ndarray):
        self.value = value

    def detach(self):
        return self

    def cpu(self):
        return self

    def numpy(self):
        return self.value


def fake_folder_paths(files: dict[tuple[str, str], Path]) -> types.ModuleType:
    module = types.ModuleType("folder_paths")
    module.supported_pt_extensions = {
        ".safetensors",
        ".pt",
        ".ckpt",
        ".bin",
        ".pth",
    }
    module.get_full_path = lambda folder, name: str(files[(folder, name)]) if (folder, name) in files else None
    return module


def decode_user_comment(value: bytes) -> str:
    assert value.startswith(b"UNICODE\0")
    return value[8:].decode("utf-16-be")


def exif_user_comment(exif: Image.Exif) -> bytes:
    return exif.get_ifd(ExifTags.IFD.Exif)[0x9286]


class AIONativeImageOutputTests(unittest.TestCase):
    def setUp(self):
        native._hash_file_revision.cache_clear()
        civitai._fetch_civitai_autov3_hash.cache_clear()
        civitai._cached_civitai_resource_by_hash.cache_clear()

    def test_a1111_metadata_contains_local_model_lora_and_manual_civitai_hashes(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            model_path = root / "anima.safetensors"
            lora_path = root / "style.safetensors"
            model_path.write_bytes(b"model-weights")
            lora_path.write_bytes(b"lora-weights")
            folder_paths = fake_folder_paths({
                ("diffusion_models", "models/anima.safetensors"): model_path,
                ("loras", "styles/style.safetensors"): lora_path,
            })
            with patch.dict(sys.modules, {"folder_paths": folder_paths}):
                metadata = native._build_native_metadata(
                    modelname="models/anima.safetensors",
                    positive="portrait <lora:styles/style:0.75>",
                    negative="bad anatomy",
                    width=768,
                    height=1024,
                    seed=42,
                    steps=30,
                    cfg=5.5,
                    sampler_name="dpmpp_2m",
                    scheduler_name="karras",
                    denoise=0.8,
                    clip_skip=-2,
                    custom="Model type: Anima",
                    additional_hashes="Reference:ABCDEF1234:0.5",
                    applied_loras=[{
                        "name": "styles/style.safetensors",
                        "strength_model": 0.75,
                    }],
                    download_civitai_data=False,
                    easy_remix=True,
                )
            resource_files = {path.name for path in root.iterdir()}

        model_hash = hashlib.sha256(b"model-weights").hexdigest()[:10]
        lora_hash = hashlib.sha256(b"lora-weights").hexdigest()[:10]
        self.assertEqual(metadata.hashes, {
            "model": model_hash,
            "LORA:styles/style": lora_hash,
            "Reference": "ABCDEF1234",
        })
        self.assertNotIn("<lora:", metadata.parameters)
        self.assertIn("portrait\nNegative prompt: bad anatomy", metadata.parameters)
        self.assertIn("Steps: 30", metadata.parameters)
        self.assertIn("Sampler: DPM++ 2M Karras", metadata.parameters)
        self.assertIn("CFG scale: 5.5", metadata.parameters)
        self.assertIn("Seed: 42", metadata.parameters)
        self.assertIn("Size: 768x1024", metadata.parameters)
        self.assertIn("Denoising strength: 0.8", metadata.parameters)
        self.assertIn("Clip skip: 2", metadata.parameters)
        self.assertIn(f"Model hash: {model_hash}", metadata.parameters)
        self.assertIn("Model: anima", metadata.parameters)
        self.assertIn('"LORA:styles/style"', metadata.parameters)
        self.assertEqual(
            metadata.final_hashes,
            f"anima:{model_hash},styles/style:{lora_hash}:0.75,Reference:ABCDEF1234:0.5",
        )
        self.assertEqual(
            resource_files,
            {"anima.safetensors", "style.safetensors"},
            "hashing must not write cache files beside model resources",
        )

    def test_civitai_resource_lookup_is_opt_in_and_keeps_hashes(self):
        with tempfile.TemporaryDirectory() as temp:
            model_path = Path(temp) / "anima.safetensors"
            model_path.write_bytes(b"model")
            folder_paths = fake_folder_paths({
                ("diffusion_models", "anima.safetensors"): model_path,
            })
            with (
                patch.dict(sys.modules, {"folder_paths": folder_paths}),
                patch.object(
                    native,
                    "_fetch_civitai_resource_by_hash",
                    return_value=civitai.CivitaiResourceDescriptor(
                        model_name="Anima",
                        version_name="v1",
                        air="",
                        model_version_id=123,
                    ),
                ) as fetch,
            ):
                metadata = native._build_native_metadata(
                    modelname="anima.safetensors",
                    positive="prompt",
                    negative="",
                    width=1,
                    height=1,
                    seed=1,
                    steps=1,
                    cfg=1.0,
                    sampler_name="euler",
                    scheduler_name="normal",
                    denoise=1.0,
                    clip_skip=0,
                    custom="",
                    additional_hashes="",
                    applied_loras=[],
                    download_civitai_data=True,
                    easy_remix=False,
                )

        fetch.assert_called_once()
        self.assertIn("Hashes:", metadata.parameters)
        self.assertIn('Civitai resources: [{"modelName":"Anima","versionName":"v1","modelVersionId":123}]', metadata.parameters)
        self.assertLess(
            metadata.parameters.index("Version: ComfyUI"),
            metadata.parameters.index("Civitai resources:"),
        )

    def test_a1111_metadata_without_prompts_starts_with_parameters(self):
        metadata = native._build_native_metadata(
            modelname="",
            positive="",
            negative="",
            width=1,
            height=1,
            seed=1,
            steps=2,
            cfg=3.0,
            sampler_name="euler",
            scheduler_name="normal",
            denoise=1.0,
            clip_skip=0,
            custom="",
            additional_hashes="",
            applied_loras=[],
            download_civitai_data=False,
            easy_remix=False,
        )

        self.assertTrue(metadata.parameters.startswith("Steps: 2"))
        self.assertFalse(metadata.parameters.startswith("\n"))

    def test_manual_hash_parser_rejects_ambiguous_and_non_finite_entries(self):
        with self.assertLogs("ComfyUI-EasyUseAnima", level="WARNING"):
            resources = native._manual_resource_hashes(
                "valid:ABCDEF1234,ambiguous:name:hash,bad:ABCDEF1234:nan,weighted:1234567890:0.25"
            )

        self.assertEqual(
            [(item.display_name, item.sha256, item.weight) for item in resources],
            [
                ("valid", "ABCDEF1234", None),
                ("weighted", "1234567890", 0.25),
            ],
        )

    def test_native_civitai_hash_fetcher_uses_fixed_endpoints(self):
        calls = []

        def request(endpoint, *, params=None):
            calls.append((endpoint, params))
            if endpoint.endswith("/models"):
                return {
                    "items": [{
                        "name": "Target Model",
                        "modelVersions": [
                            {"id": 10, "name": "old"},
                            {"id": 11, "name": "release v2"},
                        ],
                    }],
                }
            return {"files": [{"hashes": {"AutoV3": "ABCDEF1234"}}]}

        with patch.object(civitai, "_request_civitai_json", side_effect=request):
            result = civitai._fetch_civitai_autov3_hash(
                "creator",
                "Target Model",
                "v2",
            )

        self.assertEqual(result, "ABCDEF1234")
        self.assertEqual(calls[0][0], "https://civitai.com/api/v1/models")
        self.assertEqual(calls[0][1]["username"], "creator")
        self.assertEqual(calls[1], (
            "https://civitai.com/api/v1/model-versions/11",
            None,
        ))
        with self.assertRaisesRegex(RuntimeError, "printable characters"):
            civitai._fetch_civitai_autov3_hash("crea\ntor", "model", "")

        civitai._fetch_civitai_autov3_hash.cache_clear()
        with patch.object(civitai, "_request_civitai_json", return_value={
            "items": [{
                "name": "Target Model",
                "modelVersions": [{"id": 10, "name": "old"}],
            }],
        }) as no_match_request:
            self.assertIsNone(
                civitai._fetch_civitai_autov3_hash(
                    "creator",
                    "Target Model",
                    "missing-version",
                )
            )
        no_match_request.assert_called_once()

    def test_civitai_stream_failures_are_bounded_nonfatal_and_not_cached(self):
        response = Mock(status_code=200, headers={})
        response.iter_content.side_effect = OSError("connection reset")
        requests_module = types.ModuleType("requests")
        requests_module.get = Mock(return_value=response)
        with patch.dict(sys.modules, {"requests": requests_module}):
            with self.assertRaisesRegex(RuntimeError, "could not be read") as raised:
                civitai._request_civitai_json(
                    "https://civitai.com/api/v1/model-versions/by-hash/" + "a" * 64
                )
        self.assertNotIn("connection reset", str(raised.exception))
        response.close.assert_called_once_with()

        requests_module.get = Mock(side_effect=OSError("proxy-password"))
        with patch.dict(sys.modules, {"requests": requests_module}):
            with self.assertRaisesRegex(RuntimeError, "request failed") as raised:
                civitai._request_civitai_json("https://civitai.com/api/v1/models")
        self.assertNotIn("proxy-password", str(raised.exception))

        request = Mock(side_effect=RuntimeError("offline"))
        with (
            patch.object(civitai, "_request_civitai_json", request),
            self.assertLogs("ComfyUI-EasyUseAnima", level="WARNING"),
        ):
            self.assertIsNone(civitai._fetch_civitai_resource_by_hash("a" * 64))
            self.assertIsNone(civitai._fetch_civitai_resource_by_hash("a" * 64))
        self.assertEqual(request.call_count, 2, "transient failures must not be cached")

    def test_civitai_response_limit_is_enforced_before_parsing(self):
        response = Mock(status_code=200, headers={})
        response.iter_content.return_value = [b'{"data":', b'"too large"}']
        requests_module = types.ModuleType("requests")
        requests_module.get = Mock(return_value=response)
        with (
            patch.dict(sys.modules, {"requests": requests_module}),
            patch.object(civitai, "_CIVITAI_RESPONSE_LIMIT", 8),
            self.assertRaisesRegex(RuntimeError, "size limit"),
        ):
            civitai._request_civitai_json("https://civitai.com/api/v1/models")
        response.close.assert_called_once_with()

    def test_civitai_response_cleanup_failure_does_not_discard_valid_metadata(self):
        response = Mock(status_code=200, headers={})
        response.iter_content.return_value = [b'{"items":[]}']
        response.close.side_effect = OSError("cleanup failed")
        requests_module = types.ModuleType("requests")
        requests_module.get = Mock(return_value=response)
        with (
            patch.dict(sys.modules, {"requests": requests_module}),
            self.assertLogs("ComfyUI-EasyUseAnima", level="WARNING") as logs,
        ):
            result = civitai._request_civitai_json(
                "https://civitai.com/api/v1/models"
            )

        self.assertEqual(result, {"items": []})
        self.assertIn("cleanup failed (OSError)", "\n".join(logs.output))

    def test_civitai_resource_cache_retains_only_validated_descriptor(self):
        remote = {
            "id": 123,
            "name": "v1",
            "air": "urn:air:sdxl:checkpoint:civitai:1@123",
            "model": {"name": "Anima"},
            "images": [{"url": "x" * 100_000}],
        }
        with patch.object(civitai, "_request_civitai_json", return_value=remote):
            descriptor = civitai._fetch_civitai_resource_by_hash("b" * 64)

        self.assertEqual(
            descriptor,
            civitai.CivitaiResourceDescriptor(
                model_name="Anima",
                version_name="v1",
                air="urn:air:sdxl:checkpoint:civitai:1@123",
                model_version_id=123,
            ),
        )
        self.assertFalse(hasattr(descriptor, "images"))

        civitai._cached_civitai_resource_by_hash.cache_clear()
        remote["air"] = "urn:air:invalid value"
        with patch.object(civitai, "_request_civitai_json", return_value=remote):
            descriptor = civitai._fetch_civitai_resource_by_hash("c" * 64)
        self.assertEqual(descriptor.air, "")
        self.assertEqual(descriptor.model_version_id, 123)

    def test_png_jpeg_and_webp_round_trip_a1111_and_comfy_workflow_metadata(self):
        metadata = native.NativeImageMetadata(
            parameters="prompt\nNegative prompt: bad\nSteps: 2, Seed: 7",
            final_hashes="model:ABCDEF1234",
            hashes={"model": "ABCDEF1234"},
        )
        pixels = np.linspace(0, 1, 8 * 8 * 3, dtype=np.float32).reshape(8, 8, 3)
        prompt = {"1": {"class_type": "KSampler"}}
        workflow = {"nodes": [{"id": 1, "type": "KSampler"}]}
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for extension in ("png", "jpeg", "webp"):
                with self.subTest(extension=extension):
                    result = native._save_native_images(
                        [FakeTensor(pixels)],
                        output_root=root,
                        path=extension,
                        filename="image",
                        extension=extension,
                        quality_jpeg_or_webp=80,
                        lossless_webp=False,
                        optimize_png=True,
                        embed_workflow=True,
                        save_workflow_as_json=True,
                        metadata=metadata,
                        prompt=prompt,
                        extra_pnginfo={"workflow": workflow},
                    )
                    image_record = result["ui"]["images"][0]
                    image_path = root / extension / image_record["filename"]
                    self.assertTrue(image_path.is_file())
                    self.assertEqual(image_record["subfolder"], extension)
                    self.assertEqual(json.loads(image_path.with_suffix(".json").read_text("utf-8")), workflow)
                    with Image.open(image_path) as saved:
                        if extension == "png":
                            self.assertEqual(saved.info["parameters"], metadata.parameters)
                            self.assertEqual(json.loads(saved.info["prompt"]), prompt)
                            self.assertEqual(json.loads(saved.info["workflow"]), workflow)
                        else:
                            exif = saved.getexif()
                            self.assertEqual(
                                decode_user_comment(exif_user_comment(exif)),
                                metadata.parameters,
                            )
                            self.assertEqual(
                                json.loads(str(exif[0x0110]).removeprefix("prompt:")),
                                prompt,
                            )
                            self.assertEqual(
                                json.loads(str(exif[0x010F]).removeprefix("workflow:")),
                                workflow,
                            )

    def test_png_extra_metadata_cannot_override_owned_parameters_or_prompt(self):
        metadata = native.NativeImageMetadata("owned parameters", "", {})
        pixels = np.zeros((2, 2, 3), dtype=np.float32)
        prompt = {"owned": True}
        workflow = {"nodes": []}
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            native._save_native_images(
                [FakeTensor(pixels)],
                output_root=root,
                path="",
                filename="reserved-keys",
                extension="png",
                quality_jpeg_or_webp=80,
                lossless_webp=False,
                optimize_png=False,
                embed_workflow=True,
                save_workflow_as_json=False,
                metadata=metadata,
                prompt=prompt,
                extra_pnginfo={
                    "workflow": workflow,
                    "parameters": "forged parameters",
                    "prompt": {"forged": True},
                },
            )

            with Image.open(root / "reserved-keys.png") as saved:
                self.assertEqual(saved.info["parameters"], metadata.parameters)
                self.assertEqual(json.loads(saved.info["prompt"]), prompt)
                self.assertEqual(json.loads(saved.info["workflow"]), workflow)

    def test_lossy_webp_uses_quality_while_lossless_webp_preserves_pixels(self):
        rng = np.random.default_rng(7)
        pixels_u8 = rng.integers(0, 256, (64, 64, 3), dtype=np.uint8)
        pixels = pixels_u8.astype(np.float32) / 255.0
        metadata = native.NativeImageMetadata("", "", {})
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for filename, lossless in (("lossless", True), ("lossy", False)):
                native._save_native_images(
                    [FakeTensor(pixels)],
                    output_root=root,
                    path="",
                    filename=filename,
                    extension="webp",
                    quality_jpeg_or_webp=20,
                    lossless_webp=lossless,
                    optimize_png=False,
                    embed_workflow=False,
                    save_workflow_as_json=False,
                    metadata=metadata,
                    prompt=None,
                    extra_pnginfo=None,
                )
            with Image.open(root / "lossless.webp") as image:
                lossless_pixels = np.asarray(image)
            with Image.open(root / "lossy.webp") as image:
                lossy_pixels = np.asarray(image)

            lossless_size = (root / "lossless.webp").stat().st_size
            lossy_size = (root / "lossy.webp").stat().st_size

        expected = np.clip(pixels * 255.0, 0, 255).astype(np.uint8)
        self.assertTrue(np.array_equal(lossless_pixels, expected))
        self.assertFalse(np.array_equal(lossy_pixels, expected))
        self.assertLess(lossy_size, lossless_size)

    def test_batch_allocates_distinct_image_and_sidecar_names(self):
        metadata = native.NativeImageMetadata("parameters", "", {})
        pixels = np.zeros((2, 2, 3), dtype=np.float32)
        workflow = {"nodes": []}
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            result = native._save_native_images(
                [FakeTensor(pixels), FakeTensor(pixels)],
                output_root=root,
                path="",
                filename="batch",
                extension="webp",
                quality_jpeg_or_webp=80,
                lossless_webp=False,
                optimize_png=False,
                embed_workflow=True,
                save_workflow_as_json=True,
                metadata=metadata,
                prompt=None,
                extra_pnginfo={"workflow": workflow},
            )

            names = [item["filename"] for item in result["ui"]["images"]]
            self.assertEqual(names, ["batch_01.webp", "batch_02.webp"])
            for name in names:
                image_path = root / name
                self.assertTrue(image_path.is_file())
                self.assertEqual(
                    json.loads(image_path.with_suffix(".json").read_text("utf-8")),
                    workflow,
                )

    def test_invalid_workflow_json_fails_before_image_commit(self):
        metadata = native.NativeImageMetadata("parameters", "", {})
        pixels = np.zeros((2, 2, 3), dtype=np.float32)
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            with self.assertRaises(ValueError):
                native._save_native_images(
                    [FakeTensor(pixels)],
                    output_root=root,
                    path="",
                    filename="invalid-workflow",
                    extension="png",
                    quality_jpeg_or_webp=80,
                    lossless_webp=False,
                    optimize_png=False,
                    embed_workflow=True,
                    save_workflow_as_json=True,
                    metadata=metadata,
                    prompt=None,
                    extra_pnginfo={"workflow": {"value": float("nan")}},
                )
            self.assertFalse((root / "invalid-workflow.png").exists())

    def test_unrequested_workflow_is_not_serialized_or_allowed_to_block_image(self):
        metadata = native.NativeImageMetadata("parameters", "", {})
        pixels = np.zeros((2, 2, 3), dtype=np.float32)
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            result = native._save_native_images(
                [FakeTensor(pixels)],
                output_root=root,
                path="",
                filename="image-only",
                extension="png",
                quality_jpeg_or_webp=80,
                lossless_webp=False,
                optimize_png=False,
                embed_workflow=False,
                save_workflow_as_json=False,
                metadata=metadata,
                prompt={"value": float("nan")},
                extra_pnginfo={"workflow": {"value": float("nan")}},
            )

            self.assertEqual(result["ui"]["images"][0]["filename"], "image-only.png")
            self.assertTrue((root / "image-only.png").is_file())
            self.assertFalse((root / "image-only.json").exists())

    def test_large_jpeg_workflow_falls_back_to_json_before_image_commit(self):
        metadata = native.NativeImageMetadata("short parameters", "", {})
        workflow = {"nodes": [], "padding": "x" * 70_000}
        pixels = np.zeros((8, 8, 3), dtype=np.float32)
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            with self.assertLogs("ComfyUI-EasyUseAnima", level="WARNING"):
                native._save_native_images(
                    [FakeTensor(pixels)],
                    output_root=root,
                    path="",
                    filename="large",
                    extension="jpeg",
                    quality_jpeg_or_webp=90,
                    lossless_webp=False,
                    optimize_png=False,
                    embed_workflow=True,
                    save_workflow_as_json=False,
                    metadata=metadata,
                    prompt={"1": {}},
                    extra_pnginfo={"workflow": workflow},
                )
            with Image.open(root / "large.jpeg") as saved:
                exif = saved.getexif()
                self.assertEqual(
                    decode_user_comment(exif_user_comment(exif)),
                    "short parameters",
                )
                self.assertNotIn(0x010F, exif)
            self.assertEqual(
                json.loads((root / "large.json").read_text("utf-8")),
                workflow,
            )

    def test_native_writer_rejects_escape_before_creating_outside_directory(self):
        metadata = native.NativeImageMetadata("", "", {})
        pixels = np.zeros((1, 1, 3), dtype=np.float32)
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "output"
            outside = Path(temp) / "outside"
            for unsafe_path in ("../outside", "nested/../outside", "/absolute", "C:\\absolute"):
                with self.subTest(path=unsafe_path), self.assertRaisesRegex(
                    RuntimeError, "output directory"
                ):
                    native._save_native_images(
                        [FakeTensor(pixels)],
                        output_root=root,
                        path=unsafe_path,
                        filename="image",
                        extension="png",
                        quality_jpeg_or_webp=90,
                        lossless_webp=False,
                        optimize_png=False,
                        embed_workflow=False,
                        save_workflow_as_json=False,
                        metadata=metadata,
                        prompt=None,
                        extra_pnginfo=None,
                    )
            self.assertFalse(outside.exists())

    def test_workflow_sidecar_participates_in_collision_allocation(self):
        metadata = native.NativeImageMetadata("parameters", "", {})
        pixels = np.zeros((2, 2, 3), dtype=np.float32)
        workflow = {"nodes": []}
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            orphan = root / "image.json"
            orphan.write_text('{"preserve":true}', encoding="utf-8")
            result = native._save_native_images(
                [FakeTensor(pixels)],
                output_root=root,
                path="",
                filename="image",
                extension="webp",
                quality_jpeg_or_webp=80,
                lossless_webp=False,
                optimize_png=False,
                embed_workflow=True,
                save_workflow_as_json=True,
                metadata=metadata,
                prompt=None,
                extra_pnginfo={"workflow": workflow},
            )

            self.assertEqual(result["ui"]["images"][0]["filename"], "image_01.webp")
            self.assertEqual(orphan.read_text(encoding="utf-8"), '{"preserve":true}')
            self.assertEqual(
                json.loads((root / "image_01.json").read_text(encoding="utf-8")),
                workflow,
            )

    def test_sidecar_failure_removes_just_committed_image(self):
        metadata = native.NativeImageMetadata("parameters", "", {})
        pixels = np.zeros((2, 2, 3), dtype=np.float32)
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            with (
                patch.object(native, "_atomic_write_text", side_effect=OSError("disk full")),
                self.assertRaisesRegex(OSError, "disk full"),
            ):
                native._save_native_images(
                    [FakeTensor(pixels)],
                    output_root=root,
                    path="",
                    filename="image",
                    extension="png",
                    quality_jpeg_or_webp=80,
                    lossless_webp=False,
                    optimize_png=False,
                    embed_workflow=True,
                    save_workflow_as_json=True,
                    metadata=metadata,
                    prompt=None,
                    extra_pnginfo={"workflow": {"nodes": []}},
                )
            self.assertFalse((root / "image.png").exists())


if __name__ == "__main__":
    unittest.main()
