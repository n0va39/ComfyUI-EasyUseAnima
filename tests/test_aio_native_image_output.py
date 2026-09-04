from __future__ import annotations

import hashlib
import json
import os
import subprocess
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
from easyuse_anima.aio import native_metadata_budget as metadata_budget
from easyuse_anima.aio import native_output_directories as directories
from easyuse_anima.aio import native_output_publication as publication
from easyuse_anima.aio import native_resource_hashes as resources


class FakeTensor:
    def __init__(self, value: np.ndarray):
        self.value = value

    def detach(self):
        return self

    def cpu(self):
        return self

    def numpy(self):
        return self.value


def fake_folder_paths(
    files: dict[tuple[str, str], Path],
    *,
    filenames: dict[str, list[str]] | None = None,
    user_directory: Path | None = None,
) -> types.ModuleType:
    module = types.ModuleType("folder_paths")
    module.supported_pt_extensions = {
        ".safetensors",
        ".pt",
        ".ckpt",
        ".bin",
        ".pth",
    }
    module.get_full_path = lambda folder, name: str(files[(folder, name)]) if (folder, name) in files else None
    module.get_filename_list = lambda folder: list((filenames or {}).get(folder, []))
    if user_directory is not None:
        module.get_user_directory = lambda: str(user_directory)
    return module


def decode_user_comment(value: bytes) -> str:
    assert value.startswith(b"UNICODE\0")
    return value[8:].decode("utf-16-be")


def exif_user_comment(exif: Image.Exif) -> bytes:
    return exif.get_ifd(ExifTags.IFD.Exif)[0x9286]


def create_directory_link(link: Path, target: Path) -> None:
    failure: OSError | None = None
    try:
        os.symlink(target, link, target_is_directory=True)
        return
    except OSError as exc:
        if os.name != "nt":
            raise
        failure = exc
    result = subprocess.run(
        ["cmd.exe", "/d", "/c", "mklink", "/J", str(link), str(target)],
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        timeout=10,
    )
    if result.returncode != 0:
        assert failure is not None
        raise failure


def remove_directory_link(link: Path) -> None:
    if link.is_symlink():
        link.unlink()
    else:
        link.rmdir()


class AIONativeImageOutputTests(unittest.TestCase):
    def setUp(self):
        resources._hash_file_revision.cache_clear()
        civitai._fetch_civitai_autov3_hash.cache_clear()
        civitai._cached_civitai_resource_by_hash.cache_clear()
        comfy_module = types.ModuleType("comfy")
        comfy_module.__path__ = []
        cli_args_module = types.ModuleType("comfy.cli_args")
        cli_args_module.args = types.SimpleNamespace(disable_metadata=False)
        comfy_module.cli_args = cli_args_module
        cli_args_patch = patch.dict(
            sys.modules,
            {
                "comfy": comfy_module,
                "comfy.cli_args": cli_args_module,
            },
        )
        cli_args_patch.start()
        self.addCleanup(cli_args_patch.stop)

    def test_comfy_metadata_setting_fails_closed_on_import_or_access_error(self):
        for disable_metadata, expected in ((False, True), (True, False)):
            cli_args_module = types.ModuleType("comfy.cli_args")
            cli_args_module.args = types.SimpleNamespace(
                disable_metadata=disable_metadata
            )
            with patch.dict(sys.modules, {"comfy.cli_args": cli_args_module}):
                self.assertIs(native._comfy_metadata_enabled(), expected)

        missing_attribute_module = types.ModuleType("comfy.cli_args")
        missing_attribute_module.args = object()
        with patch.dict(
            sys.modules,
            {"comfy.cli_args": missing_attribute_module},
        ):
            self.assertFalse(native._comfy_metadata_enabled())

        class RaisingArgs:
            @property
            def disable_metadata(self):
                raise RuntimeError("setting access failed")

        raising_module = types.ModuleType("comfy.cli_args")
        raising_module.args = RaisingArgs()
        with patch.dict(sys.modules, {"comfy.cli_args": raising_module}):
            self.assertFalse(native._comfy_metadata_enabled())

        with patch.dict(sys.modules, {"comfy.cli_args": None}):
            self.assertFalse(native._comfy_metadata_enabled())

    def test_disabled_metadata_snapshot_writes_image_only_without_rereading_flag(self):
        metadata = native.NativeImageMetadata("parameters", "hashes", {"model": "abc"})
        pixels = np.zeros((2, 2, 3), dtype=np.float32)
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            with patch.object(
                native,
                "_comfy_metadata_enabled",
                side_effect=AssertionError("explicit snapshot must not be reread"),
            ):
                result = native._save_native_images(
                    [FakeTensor(pixels)],
                    output_root=root,
                    path="",
                    filename="private",
                    extension="png",
                    quality_jpeg_or_webp=80,
                    lossless_webp=False,
                    optimize_png=False,
                    embed_workflow=True,
                    save_workflow_as_json=True,
                    metadata=metadata,
                    prompt={"1": {"class_type": "Test"}},
                    extra_pnginfo={"workflow": {"nodes": []}},
                    metadata_enabled=False,
                )

            image_path = root / result["ui"]["images"][0]["filename"]
            with Image.open(image_path) as saved:
                self.assertNotIn("parameters", saved.info)
                self.assertNotIn("prompt", saved.info)
                self.assertNotIn("workflow", saved.info)
            self.assertFalse(image_path.with_suffix(".json").exists())

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

    def test_embedding_hashes_use_comfy_inventory_weights_and_safe_matching(self):
        self.assertEqual(resources._safe_inventory_name("/absolute/embed.pt"), "")
        self.assertEqual(resources._safe_inventory_name(r"C:\outside\embed.pt"), "")
        self.assertEqual(resources._safe_inventory_name("../outside.pt"), "")
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            easy_path = root / "easy.pt"
            negative_path = root / "bad.safetensors"
            duplicate_one = root / "duplicate-one.pt"
            duplicate_two = root / "duplicate-two.pt"
            easy_path.write_bytes(b"easy embedding")
            negative_path.write_bytes(b"negative embedding")
            duplicate_one.write_bytes(b"duplicate one")
            duplicate_two.write_bytes(b"duplicate two")
            folder_paths = fake_folder_paths(
                {
                    ("embeddings", "sub/easy.pt"): easy_path,
                    ("embeddings", "negative/bad.safetensors"): negative_path,
                    ("embeddings", "one/duplicate.pt"): duplicate_one,
                    ("embeddings", "two/duplicate.pt"): duplicate_two,
                },
                filenames={
                    "embeddings": [
                        "sub/easy.pt",
                        "negative/bad.safetensors",
                        "one/duplicate.pt",
                        "two/duplicate.pt",
                    ]
                },
            )
            comfy = types.ModuleType("comfy")
            sd1_clip = types.ModuleType("comfy.sd1_clip")
            sd1_clip.escape_important = lambda value: value
            sd1_clip.unescape_important = lambda value: value

            def token_weights(value, _default):
                if "sub/easy" in value:
                    return [
                        ("embedding:sub/easy", 0.65),
                        ("embedding:../outside", 1.0),
                        ("embedding:duplicate", 1.0),
                    ]
                return [
                    ("embedding:negative/bad", 1.25),
                    ("embedding:sub/easy", 2.0),
                ]

            sd1_clip.token_weights = token_weights
            comfy.sd1_clip = sd1_clip
            with (
                patch.dict(
                    sys.modules,
                    {
                        "folder_paths": folder_paths,
                        "comfy": comfy,
                        "comfy.sd1_clip": sd1_clip,
                    },
                ),
                self.assertLogs("ComfyUI-EasyUseAnima", level="WARNING"),
            ):
                metadata = native._build_native_metadata(
                    modelname="",
                    positive="(embedding:sub/easy:0.65), embedding:../outside, embedding:duplicate",
                    negative="embedding:negative/bad",
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
                    download_civitai_data=False,
                    easy_remix=True,
                )

        easy_hash = hashlib.sha256(b"easy embedding").hexdigest()[:10]
        negative_hash = hashlib.sha256(b"negative embedding").hexdigest()[:10]
        self.assertEqual(
            metadata.hashes,
            {
                "embed:sub/easy": easy_hash,
                "embed:negative/bad": negative_hash,
            },
        )
        self.assertEqual(
            metadata.final_hashes,
            f"sub/easy:{easy_hash}:0.65,negative/bad:{negative_hash}:1.25",
        )
        self.assertIn("embedding:easy", metadata.parameters)
        self.assertNotIn("embed:duplicate", metadata.hashes)

    def test_embedding_lookup_attempts_are_deduplicated_bounded_and_indexed_once(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "target.pt"
            target.write_bytes(b"target embedding")
            folder_paths = fake_folder_paths(
                {("embeddings", "known/target.pt"): target},
                filenames={
                    "embeddings": [f"known/{index}.pt" for index in range(1_000)]
                    + ["known/target.pt"]
                },
            )
            get_filename_list = Mock(wraps=folder_paths.get_filename_list)
            folder_paths.get_filename_list = get_filename_list
            prompt = ", ".join(
                ["embedding:missing"] * 40
                + [f"embedding:missing-{index}" for index in range(30)]
                + ["embedding:known/target"]
            )

            with (
                patch.dict(sys.modules, {"folder_paths": folder_paths}),
                patch.object(
                    resources,
                    "_inventory_resource_name",
                    wraps=resources._inventory_resource_name,
                ) as match_inventory,
            ):
                result = resources._local_resource_hashes("", [], (prompt,))

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].metadata_key, "embed:known/target")
        self.assertEqual(
            result[0].sha256,
            hashlib.sha256(b"target embedding").hexdigest(),
        )
        get_filename_list.assert_called_once_with("embeddings")
        self.assertEqual(
            match_inventory.call_count,
            resources._MAX_LOCAL_RESOURCE_ATTEMPTS,
        )

    def test_local_resource_attempt_budget_includes_model_loras_before_embeddings(self):
        folder_paths = fake_folder_paths({}, filenames={"embeddings": ["unused.pt"]})
        get_filename_list = Mock(wraps=folder_paths.get_filename_list)
        folder_paths.get_filename_list = get_filename_list
        applied_loras = [
            {
                "name": f"style-{index}.safetensors",
                "strength_model": 1.0,
            }
            for index in range(40)
        ]
        resolved_path = Path("resource.safetensors")

        with (
            patch.dict(sys.modules, {"folder_paths": folder_paths}),
            patch.object(
                resources,
                "_resolve_resource_path",
                return_value=resolved_path,
            ) as resolve_resource,
            patch.object(resources, "_hash_file", return_value="a" * 64) as hash_file,
            self.assertLogs("ComfyUI-EasyUseAnima", level="WARNING"),
        ):
            result = resources._local_resource_hashes(
                "model.safetensors",
                applied_loras,
                ("embedding:unused",),
            )

        self.assertEqual(len(result), resources._MAX_LOCAL_RESOURCE_ATTEMPTS)
        self.assertEqual(result[0].metadata_key, "model")
        self.assertEqual(result[-1].metadata_key, "LORA:style-30")
        self.assertEqual(
            resolve_resource.call_count,
            resources._MAX_LOCAL_RESOURCE_ATTEMPTS,
        )
        self.assertEqual(hash_file.call_count, resources._MAX_LOCAL_RESOURCE_ATTEMPTS)
        get_filename_list.assert_not_called()

    def test_manual_hashes_preserve_values_and_cannot_replace_local_model_hash(self):
        first = "ABCDEF1234AAAAAA"
        second = "ABCDEF1234BBBBBB"
        with tempfile.TemporaryDirectory() as temp:
            model_path = Path(temp) / "anima.safetensors"
            model_path.write_bytes(b"verified model")
            folder_paths = fake_folder_paths({
                ("diffusion_models", "anima.safetensors"): model_path,
            })
            with (
                patch.dict(sys.modules, {"folder_paths": folder_paths}),
                self.assertLogs("ComfyUI-EasyUseAnima", level="WARNING"),
            ):
                metadata = native._build_native_metadata(
                    modelname="anima.safetensors",
                    positive="",
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
                    additional_hashes=(
                        f"first:{first},second:{second},MODEL:DEADBEEF12,"
                        "duplicate:AAAABBBB12,duplicate:CCCCDDDD34"
                    ),
                    applied_loras=[],
                    download_civitai_data=False,
                    easy_remix=False,
                )

        model_hash = hashlib.sha256(b"verified model").hexdigest()[:10]
        self.assertEqual(metadata.hashes["model"], model_hash)
        self.assertNotIn("MODEL", metadata.hashes)
        self.assertEqual(metadata.hashes["first"], first)
        self.assertEqual(metadata.hashes["second"], second)
        self.assertEqual(metadata.hashes["duplicate"], "AAAABBBB12")
        self.assertIn(f"first:{first}", metadata.final_hashes)
        self.assertIn(f"second:{second}", metadata.final_hashes)

    def test_manual_full_and_short_hashes_receive_proven_civitai_descriptors(self):
        full_hash = "a" * 64
        short_hash = "ABCDEF1234"

        def descriptor(resource_hash):
            identifier = 1 if resource_hash == full_hash else 2
            return civitai.CivitaiResourceDescriptor(
                model_name=f"Resource {identifier}",
                version_name=f"v{identifier}",
                air="",
                model_version_id=identifier,
            )

        with patch.object(
            native,
            "_fetch_civitai_resource_by_hash",
            side_effect=descriptor,
        ) as fetch:
            metadata = native._build_native_metadata(
                modelname="",
                positive="",
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
                additional_hashes=f"Full:{full_hash}:0.4,Auto:{short_hash}:0.7",
                applied_loras=[],
                download_civitai_data=True,
                easy_remix=False,
            )

        self.assertEqual([call.args[0] for call in fetch.call_args_list], [full_hash, short_hash])
        self.assertEqual(metadata.hashes["Full"], full_hash)
        self.assertEqual(metadata.hashes["Auto"], short_hash)
        self.assertIn(
            'Civitai resources: [{"modelName":"Resource 1","versionName":"v1","weight":0.4,"modelVersionId":1},{"modelName":"Resource 2","versionName":"v2","weight":0.7,"modelVersionId":2}]',
            metadata.parameters,
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
            parsed_resources = resources._manual_resource_hashes(
                "valid:ABCDEF1234,numeric:1234567890,DEADBEEF12:0.5,"
                "ambiguous:name:hash,bad:FEEDFACE12:nan,weighted:CAFEBABE10:0.25"
            )

        self.assertEqual(
            [(item.display_name, item.sha256, item.weight) for item in parsed_resources],
            [
                ("valid", "ABCDEF1234", None),
                ("numeric", "1234567890", None),
                ("manual1", "DEADBEEF12", 0.5),
                ("weighted", "CAFEBABE10", 0.25),
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
            cached_variant = civitai._fetch_civitai_autov3_hash(
                " CREATOR ",
                " target model ",
                " V2 ",
            )

        self.assertEqual(result, "ABCDEF1234")
        self.assertEqual(cached_variant, result)
        self.assertEqual(len(calls), 2, "normalized lookup variants must reuse the cache")
        self.assertEqual(calls[0][0], "https://civitai.com/api/v1/models")
        self.assertEqual(calls[0][1]["username"], "creator")
        self.assertEqual(calls[0][1]["query"], "Target Model")
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

    def test_civitai_slow_stream_stops_at_shared_wall_clock_deadline(self):
        class Clock:
            now = 0.0

            def __call__(self):
                return self.now

        clock = Clock()
        response = Mock(status_code=200, headers={})

        def chunks(*, chunk_size):
            self.assertEqual(chunk_size, 64 * 1024)
            yield b'{"items":'
            clock.now = 6.0
            yield b"[]}"

        response.iter_content.side_effect = chunks
        transport = Mock(return_value=response)
        budget = civitai.CivitaiLookupBudget(
            timeout_seconds=5.0,
            http_call_limit=4,
            clock=clock,
        )

        with self.assertRaisesRegex(
            civitai.CivitaiLookupBudgetExhausted,
            "deadline",
        ):
            civitai._request_civitai_json(
                "https://civitai.com/api/v1/models",
                budget=budget,
                transport=transport,
            )

        self.assertEqual(budget.calls_started, 1)
        self.assertEqual(transport.call_args.kwargs["timeout"], (3.05, 5.0))
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
            "files": [{"hashes": {"SHA256": "b" * 64}}],
            "images": [{"url": "x" * 100_000}],
        }
        with patch.object(civitai, "_request_civitai_json", return_value=remote) as request:
            descriptor = civitai._fetch_civitai_resource_by_hash("b" * 64)
            self.assertEqual(
                civitai._fetch_civitai_resource_by_hash("b" * 64),
                descriptor,
            )

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
        request.assert_called_once()

        civitai._cached_civitai_resource_by_hash.cache_clear()
        remote["air"] = "urn:air:invalid value"
        remote["files"] = [{"hashes": {"SHA256": "c" * 64}}]
        with patch.object(civitai, "_request_civitai_json", return_value=remote):
            descriptor = civitai._fetch_civitai_resource_by_hash("c" * 64)
        self.assertEqual(descriptor.air, "")
        self.assertEqual(descriptor.model_version_id, 123)

    def test_civitai_resource_lookup_requires_exact_hash_proof(self):
        remote = {
            "id": 123,
            "name": "v1",
            "model": {"name": "Anima"},
            "files": [{"hashes": {"AutoV3": "ABCDEF1234"}}],
        }
        with patch.object(civitai, "_request_civitai_json", return_value=remote):
            descriptor = civitai._fetch_civitai_resource_by_hash("abcdef1234")
        self.assertEqual(descriptor.model_version_id, 123)

        civitai._cached_civitai_resource_by_hash.cache_clear()
        with patch.object(civitai, "_request_civitai_json", return_value=remote):
            self.assertIsNone(civitai._fetch_civitai_resource_by_hash("deadbeef12"))

        civitai._cached_civitai_resource_by_hash.cache_clear()
        malformed = {**remote, "files": [{"hashes": ["ABCDEF1234"]}]}
        with patch.object(civitai, "_request_civitai_json", return_value=malformed):
            self.assertIsNone(civitai._fetch_civitai_resource_by_hash("abcdef1234"))

        with patch.object(civitai, "_request_civitai_json") as request:
            self.assertIsNone(civitai._fetch_civitai_resource_by_hash("not-a-hash"))
        request.assert_not_called()

    def test_civitai_resource_enrichment_attempts_are_bounded(self):
        resource_items = [
            resources._ResourceHash(
                display_name=f"resource-{index}",
                metadata_key=f"resource-{index}",
                path=None,
                sha256=f"{index + 1:064x}",
                preserve_hash=True,
            )
            for index in range(native._MAX_REMOTE_RESOURCES + 5)
        ]
        with patch.object(
            native,
            "_fetch_civitai_resource_by_hash",
            return_value=None,
        ) as fetch:
            self.assertEqual(native._civitai_resource_entries(resource_items), [])

        self.assertEqual(fetch.call_count, native._MAX_REMOTE_RESOURCES)

    def test_persistent_hash_cache_reuses_revision_and_reports_uncached_progress(self):
        progress_updates = []

        class ProgressBar:
            def __init__(self, total):
                self.total = total

            def update_absolute(self, value, total):
                progress_updates.append((value, total, self.total))

        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            user_directory = root / "user"
            model_directory = root / "models"
            user_directory.mkdir()
            model_directory.mkdir()
            model_path = model_directory / "model.safetensors"
            first_bytes = b"first revision"
            second_bytes = b"other revision"
            self.assertEqual(len(first_bytes), len(second_bytes))
            model_path.write_bytes(first_bytes)
            folder_paths = fake_folder_paths({}, user_directory=user_directory)
            comfy = types.ModuleType("comfy")
            comfy_utils = types.ModuleType("comfy.utils")
            comfy_utils.ProgressBar = ProgressBar
            comfy.utils = comfy_utils
            with patch.dict(
                sys.modules,
                {
                    "folder_paths": folder_paths,
                    "comfy": comfy,
                    "comfy.utils": comfy_utils,
                },
            ):
                first = resources._hash_file(model_path)
                cache_path = (
                    user_directory
                    / "easyuse_anima"
                    / "cache"
                    / resources._HASH_CACHE_FILENAME
                )
                self.assertTrue(cache_path.is_file())
                self.assertEqual(
                    {path.name for path in model_directory.iterdir()},
                    {"model.safetensors"},
                )
                self.assertEqual(progress_updates[-1][0], len(first_bytes))

                resources._hash_file_revision.cache_clear()
                with patch.object(
                    resources,
                    "_calculate_file_sha256",
                    side_effect=AssertionError("persistent cache miss"),
                ):
                    self.assertEqual(resources._hash_file(model_path), first)

                original_stat = model_path.stat()
                replacement = model_directory / "replacement.tmp"
                replacement.write_bytes(second_bytes)
                os.utime(
                    replacement,
                    ns=(original_stat.st_atime_ns, original_stat.st_mtime_ns),
                )
                os.replace(replacement, model_path)
                os.utime(
                    model_path,
                    ns=(original_stat.st_atime_ns, original_stat.st_mtime_ns),
                )
                replaced_stat = model_path.stat()
                self.assertEqual(replaced_stat.st_size, original_stat.st_size)
                self.assertEqual(replaced_stat.st_mtime_ns, original_stat.st_mtime_ns)
                resources._hash_file_revision.cache_clear()
                calculate = resources._calculate_file_sha256
                with patch.object(
                    resources,
                    "_calculate_file_sha256",
                    wraps=calculate,
                ) as recalculated:
                    second = resources._hash_file(model_path)
                self.assertNotEqual(second, first)
                self.assertEqual(second, hashlib.sha256(second_bytes).hexdigest())
                recalculated.assert_called_once()

                cache_path.write_text("not-json", encoding="utf-8")
                resources._hash_file_revision.cache_clear()
                with (
                    patch.object(
                        resources,
                        "_calculate_file_sha256",
                        wraps=calculate,
                    ) as recomputed,
                    self.assertLogs("ComfyUI-EasyUseAnima", level="WARNING"),
                ):
                    self.assertEqual(resources._hash_file(model_path), second)
                recomputed.assert_called_once()
                self.assertEqual(
                    json.loads(cache_path.read_text(encoding="utf-8"))["version"],
                    resources._HASH_CACHE_SCHEMA,
                )

    def test_persistent_hash_cache_is_bounded_and_write_failures_are_nonfatal(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            user_directory = root / "user"
            user_directory.mkdir()
            paths = []
            for index in range(3):
                path = root / f"resource-{index}.safetensors"
                path.write_bytes(f"resource-{index}".encode("ascii"))
                paths.append(path)
            folder_paths = fake_folder_paths({}, user_directory=user_directory)
            with (
                patch.dict(sys.modules, {"folder_paths": folder_paths}),
                patch.object(resources, "_HASH_CACHE_MAX_ENTRIES", 2),
            ):
                for path in paths:
                    resources._hash_file(path)
                cache_path = (
                    user_directory
                    / "easyuse_anima"
                    / "cache"
                    / resources._HASH_CACHE_FILENAME
                )
                payload = json.loads(cache_path.read_text(encoding="utf-8"))
                self.assertEqual(len(payload["entries"]), 2)

                resources._hash_file_revision.cache_clear()
                uncached_path = root / "write-failure.safetensors"
                uncached_path.write_bytes(b"still returns a hash")
                with (
                    patch.object(
                        resources,
                        "_atomic_write_hash_cache",
                        side_effect=OSError("read-only user directory"),
                    ),
                    self.assertLogs("ComfyUI-EasyUseAnima", level="WARNING"),
                ):
                    result = resources._hash_file(uncached_path)
                self.assertEqual(
                    result,
                    hashlib.sha256(b"still returns a hash").hexdigest(),
                )

    def test_deeply_nested_persistent_hash_cache_is_recomputed_and_replaced(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            user_directory = root / "user"
            user_directory.mkdir()
            model_path = root / "model.safetensors"
            model_path.write_bytes(b"verified model")
            cache_path = (
                user_directory
                / "easyuse_anima"
                / "cache"
                / resources._HASH_CACHE_FILENAME
            )
            cache_path.parent.mkdir(parents=True)
            depth = sys.getrecursionlimit() * 4
            cache_path.write_text("[" * depth + "0" + "]" * depth, encoding="utf-8")
            folder_paths = fake_folder_paths({}, user_directory=user_directory)
            calculate = resources._calculate_file_sha256

            with (
                patch.dict(sys.modules, {"folder_paths": folder_paths}),
                patch.object(
                    resources,
                    "_calculate_file_sha256",
                    wraps=calculate,
                ) as recomputed,
                self.assertLogs("ComfyUI-EasyUseAnima", level="WARNING") as logs,
            ):
                result = resources._hash_file(model_path)

            self.assertEqual(result, hashlib.sha256(b"verified model").hexdigest())
            recomputed.assert_called_once()
            self.assertTrue(any("RecursionError" in entry for entry in logs.output))
            replacement = json.loads(cache_path.read_text(encoding="utf-8"))
            self.assertEqual(replacement["version"], resources._HASH_CACHE_SCHEMA)
            self.assertEqual(len(replacement["entries"]), 1)

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

    def test_png_jpeg_and_webp_publish_sanitized_windows_filenames(self):
        metadata = native.NativeImageMetadata("parameters", "", {})
        pixels = np.zeros((2, 2, 3), dtype=np.float32)
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for extension in ("png", "jpeg", "webp"):
                with self.subTest(extension=extension):
                    result = native._save_native_images(
                        [FakeTensor(pixels)],
                        output_root=root,
                        path=extension,
                        filename='bad<>:"|?*name. ',
                        extension=extension,
                        quality_jpeg_or_webp=80,
                        lossless_webp=False,
                        optimize_png=False,
                        embed_workflow=False,
                        save_workflow_as_json=False,
                        metadata=metadata,
                        prompt=None,
                        extra_pnginfo=None,
                    )

                    image_record = result["ui"]["images"][0]
                    self.assertEqual(image_record["filename"], f"badname.{extension}")
                    self.assertTrue((root / extension / f"badname.{extension}").is_file())

    def test_native_writer_rejects_windows_reserved_filename_before_publication(self):
        metadata = native.NativeImageMetadata("parameters", "", {})
        pixels = np.zeros((2, 2, 3), dtype=np.float32)
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for filename in (
                "NUL.txt",
                "con",
                "aux.log",
                "CON?",
                "Com¹.txt",
                "lPT³.bin",
                "CONIN$.png",
                "conout$",
            ):
                with self.subTest(filename=filename), self.assertRaisesRegex(
                    RuntimeError, "invalid on Windows"
                ):
                    native._save_native_images(
                        [FakeTensor(pixels)],
                        output_root=root,
                        path="",
                        filename=filename,
                        extension="png",
                        quality_jpeg_or_webp=80,
                        lossless_webp=False,
                        optimize_png=False,
                        embed_workflow=False,
                        save_workflow_as_json=False,
                        metadata=metadata,
                        prompt=None,
                        extra_pnginfo=None,
                    )

            self.assertEqual(list(root.iterdir()), [])

    def test_windows_output_component_recognizes_exact_dos_device_aliases(self):
        for device_name in (
            "COM¹",
            "COM²",
            "COM³",
            "LPT¹",
            "LPT²",
            "LPT³",
            "CONIN$",
            "CONOUT$",
        ):
            for component in (device_name, f"{device_name.lower()}.txt"):
                with self.subTest(component=component):
                    self.assertFalse(native._is_windows_safe_output_component(component))

        for component in ("COM⁴", "LPT⁹", "CONIN-data", "résumé"):
            with self.subTest(component=component):
                self.assertTrue(native._is_windows_safe_output_component(component))

    def test_png_extra_metadata_case_variants_cannot_override_owned_keys(self):
        metadata = native.NativeImageMetadata("owned parameters", "", {})
        pixels = np.zeros((2, 2, 3), dtype=np.float32)
        prompt = {"owned": True}
        workflow = {"nodes": []}
        forged_workflow = {"nodes": [{"id": "forged"}]}
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            with self.assertLogs("ComfyUI-EasyUseAnima", level="WARNING"):
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
                        "Workflow": forged_workflow,
                        "WORKFLOW": forged_workflow,
                        "Prompt": {"forged": True},
                        "PARAMETERS": "forged parameters",
                        "workflow:": forged_workflow,
                        "Prompt:alias": {"forged": True},
                        "PARAMETERS:alias": "forged parameters",
                        "workflow": workflow,
                        "parameters": "forged parameters",
                        "prompt": {"forged": True},
                        "unrelated": {"kept": True},
                    },
                )

            with Image.open(root / "reserved-keys.png") as saved:
                self.assertEqual(saved.info["parameters"], metadata.parameters)
                self.assertEqual(json.loads(saved.info["prompt"]), prompt)
                self.assertEqual(json.loads(saved.info["workflow"]), workflow)
                self.assertEqual(json.loads(saved.info["unrelated"]), {"kept": True})
                for alias in (
                    "Workflow",
                    "WORKFLOW",
                    "Prompt",
                    "PARAMETERS",
                    "workflow:",
                    "Prompt:alias",
                    "PARAMETERS:alias",
                ):
                    self.assertNotIn(alias, saved.info)

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

    def test_metadata_byte_limits_accept_boundary_and_reject_next_byte(self):
        with patch.object(metadata_budget, "_MAX_PARAMETERS_BYTES", 16):
            serialized = native._serialize_metadata(
                extension="png",
                parameters="x" * 16,
                prompt=None,
                extra_pnginfo=None,
                embed_workflow=False,
                save_workflow_as_json=False,
                write_metadata=True,
            )
            self.assertEqual(serialized.embedded_size_bytes, 16)
            with self.assertRaisesRegex(
                metadata_budget.MetadataLimitError,
                "A1111 parameters",
            ):
                native._serialize_metadata(
                    extension="png",
                    parameters="x" * 17,
                    prompt=None,
                    extra_pnginfo=None,
                    embed_workflow=False,
                    save_workflow_as_json=False,
                    write_metadata=True,
                )

        with patch.object(metadata_budget, "_MAX_PROMPT_JSON_BYTES", 12):
            native._serialize_metadata(
                extension="png",
                parameters="",
                prompt="x" * 10,
                extra_pnginfo=None,
                embed_workflow=True,
                save_workflow_as_json=False,
                write_metadata=True,
            )
            with self.assertRaisesRegex(
                metadata_budget.MetadataLimitError,
                "prompt JSON",
            ):
                native._serialize_metadata(
                    extension="png",
                    parameters="",
                    prompt="x" * 11,
                    extra_pnginfo=None,
                    embed_workflow=True,
                    save_workflow_as_json=False,
                    write_metadata=True,
                )

        with patch.object(metadata_budget, "_MAX_WORKFLOW_JSON_BYTES", 12):
            serialized = native._serialize_metadata(
                extension="png",
                parameters="",
                prompt=None,
                extra_pnginfo={"workflow": "x" * 10},
                embed_workflow=True,
                save_workflow_as_json=False,
                write_metadata=True,
            )
            self.assertIsNone(
                serialized.workflow_json,
                "embedded PNG workflow must not retain an unrequested pretty sidecar copy",
            )
            with self.assertRaisesRegex(
                metadata_budget.MetadataLimitError,
                "workflow JSON",
            ):
                native._serialize_metadata(
                    extension="png",
                    parameters="",
                    prompt=None,
                    extra_pnginfo={"workflow": "x" * 11},
                    embed_workflow=True,
                    save_workflow_as_json=False,
                    write_metadata=True,
                )

    def test_metadata_structure_limits_depth_items_and_extra_keys(self):
        deeply_nested = {"level": {"level": {"level": True}}}
        with (
            patch.object(metadata_budget, "_MAX_JSON_DEPTH", 2),
            self.assertRaisesRegex(metadata_budget.MetadataLimitError, "level"),
        ):
            native._serialize_metadata(
                extension="png",
                parameters="",
                prompt=None,
                extra_pnginfo={"workflow": deeply_nested},
                embed_workflow=True,
                save_workflow_as_json=False,
                write_metadata=True,
            )

        with (
            patch.object(metadata_budget, "_MAX_JSON_ITEMS", 5),
            self.assertRaisesRegex(metadata_budget.MetadataLimitError, "item"),
        ):
            native._serialize_metadata(
                extension="png",
                parameters="",
                prompt=list(range(5)),
                extra_pnginfo=None,
                embed_workflow=True,
                save_workflow_as_json=False,
                write_metadata=True,
            )

        with (
            patch.object(metadata_budget, "_MAX_JSON_STRING_BYTES", 4),
            self.assertRaisesRegex(metadata_budget.MetadataLimitError, "string"),
        ):
            native._serialize_metadata(
                extension="png",
                parameters="",
                prompt="12345",
                extra_pnginfo=None,
                embed_workflow=True,
                save_workflow_as_json=False,
                write_metadata=True,
            )

        with (
            patch.object(metadata_budget, "_MAX_EXTRA_PNGINFO_KEYS", 2),
            self.assertRaisesRegex(metadata_budget.MetadataLimitError, "key"),
        ):
            native._serialize_metadata(
                extension="png",
                parameters="",
                prompt=None,
                extra_pnginfo={"workflow": {}, "one": 1, "two": 2},
                embed_workflow=True,
                save_workflow_as_json=False,
                write_metadata=True,
            )

        with (
            patch.object(metadata_budget, "_MAX_EXTRA_PNGINFO_JSON_BYTES", 20),
            self.assertRaisesRegex(
                metadata_budget.MetadataLimitError,
                "extra_pnginfo",
            ),
        ):
            native._serialize_metadata(
                extension="png",
                parameters="",
                prompt=None,
                extra_pnginfo={"one": "x" * 8, "two": "y" * 8},
                embed_workflow=True,
                save_workflow_as_json=False,
                write_metadata=True,
            )

    def test_batch_metadata_budget_rejects_before_image_encoding(self):
        metadata = native.NativeImageMetadata("x" * 10, "", {})
        pixels = np.zeros((2, 2, 3), dtype=np.float32)
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            with (
                patch.object(metadata_budget, "_MAX_SAVE_METADATA_BYTES", 19),
                patch.object(
                    native,
                    "_tensor_to_pil",
                    side_effect=AssertionError("must reject before image encoding"),
                ) as encode,
                self.assertRaisesRegex(
                    metadata_budget.MetadataLimitError,
                    "batch metadata",
                ),
            ):
                native._save_native_images(
                    [FakeTensor(pixels), FakeTensor(pixels)],
                    output_root=root,
                    path="",
                    filename="batch-limit",
                    extension="png",
                    quality_jpeg_or_webp=80,
                    lossless_webp=False,
                    optimize_png=False,
                    embed_workflow=False,
                    save_workflow_as_json=False,
                    metadata=metadata,
                    prompt=None,
                    extra_pnginfo=None,
                )

            encode.assert_not_called()
            self.assertEqual(list(root.iterdir()), [])

    def test_jpeg_fallback_rejects_oversized_pretty_sidecar_before_publication(self):
        metadata = native.NativeImageMetadata("parameters", "", {})
        workflow = {"nodes": list(range(20))}
        pixels = np.zeros((2, 2, 3), dtype=np.float32)
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            with (
                patch.object(native, "_JPEG_EXIF_LIMIT", 20),
                patch.object(metadata_budget, "_MAX_WORKFLOW_JSON_BYTES", 100),
                self.assertRaisesRegex(
                    metadata_budget.MetadataLimitError,
                    "workflow JSON sidecar",
                ),
            ):
                native._save_native_images(
                    [FakeTensor(pixels)],
                    output_root=root,
                    path="",
                    filename="jpeg-limit",
                    extension="jpeg",
                    quality_jpeg_or_webp=90,
                    lossless_webp=False,
                    optimize_png=False,
                    embed_workflow=True,
                    save_workflow_as_json=False,
                    metadata=metadata,
                    prompt=None,
                    extra_pnginfo={"workflow": workflow},
                )

            self.assertEqual(list(root.iterdir()), [])

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
            for unsafe_path in (
                "../outside",
                "nested/../outside",
                "/absolute",
                "C:\\absolute",
                "nested/bad?folder",
                "nested/CON",
                "nested/aux.txt",
                "nested/COM²",
                "nested/LPT¹.log",
                "nested/conin$",
                "nested/CONOUT$.txt",
                "nested/trailing./child",
            ):
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

    def test_output_directory_creation_reuses_parent_bound_nested_tree(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "output"

            resolved, relative = native._resolve_native_output_folder(
                root,
                "nested/deeper",
            )
            reused, reused_relative = native._resolve_native_output_folder(
                root,
                "nested/deeper",
            )

            self.assertEqual(resolved, (root / "nested" / "deeper").resolve())
            self.assertEqual(reused, resolved)
            self.assertEqual(relative, Path("nested", "deeper"))
            self.assertEqual(reused_relative, relative)
            self.assertTrue(resolved.is_dir())

    def test_output_directory_creation_rejects_link_component(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "output"
            outside = Path(temp) / "outside"
            root.mkdir()
            outside.mkdir()
            link = root / "linked"
            try:
                create_directory_link(link, outside)
            except OSError as exc:
                self.skipTest(f"directory links are unavailable: {exc}")

            try:
                with self.assertRaisesRegex(RuntimeError, "bound safely"):
                    native._resolve_native_output_folder(root, "linked/child")

                self.assertFalse((outside / "child").exists())
            finally:
                remove_directory_link(link)

    def test_output_directory_failure_never_removes_preexisting_parent(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "output"
            existing = root / "existing"
            existing.mkdir(parents=True)
            verify_name = (
                "_verify_windows_path_identity"
                if os.name == "nt"
                else "_verify_posix_path_identity"
            )
            original = getattr(directories, verify_name)

            def reject_final(path, handle):
                original(path, handle)
                if path.name == "created":
                    raise directories.OutputDirectoryIntegrityError(
                        "injected final verification failure"
                    )

            with (
                patch.object(directories, verify_name, new=reject_final),
                self.assertRaises(directories.OutputDirectoryIntegrityError),
            ):
                directories.resolve_output_directory(
                    root,
                    ("existing", "created"),
                )

            self.assertTrue(existing.is_dir())
            self.assertEqual(
                (existing / "created").exists(),
                os.name != "nt",
            )

    def test_parent_bound_creation_cannot_follow_replaced_component(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "output"
            nested = root / "nested"
            outside = Path(temp) / "outside"
            moved = outside / "moved"
            nested.mkdir(parents=True)
            outside.mkdir()
            helper_name = (
                "_open_or_create_windows_directory"
                if os.name == "nt"
                else "_open_or_create_posix_directory"
            )
            original = getattr(directories, helper_name)
            swapped = False
            rename_blocked = False

            def swap_then_open(parent, name, **kwargs):
                nonlocal rename_blocked, swapped
                if name == "leaf" and not swapped:
                    try:
                        nested.rename(moved)
                    except OSError:
                        rename_blocked = True
                    else:
                        nested.mkdir()
                        swapped = True
                return original(parent, name, **kwargs)

            try:
                with patch.object(directories, helper_name, new=swap_then_open):
                    try:
                        resolved = directories.resolve_output_directory(
                            root,
                            ("nested", "leaf"),
                        )
                    except directories.OutputDirectoryIntegrityError:
                        self.assertTrue(swapped)
                    else:
                        self.assertTrue(rename_blocked)
                        self.assertEqual(resolved, nested / "leaf")
                self.assertFalse((outside / "leaf").exists())
                self.assertFalse((moved / "leaf").exists())
                if swapped:
                    self.assertTrue(nested.is_dir())
                    self.assertEqual(list(nested.iterdir()), [])
            finally:
                if swapped:
                    nested.rmdir()
                    moved.rename(nested)

    def test_prepared_identity_survives_publication_handoff(self):
        metadata = native.NativeImageMetadata("parameters", "", {})
        pixels = np.zeros((2, 2, 3), dtype=np.float32)
        original_enter = publication.OutputDirectoryBinding.__enter__

        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "output"
            outside = Path(temp) / "outside"
            moved = outside / "moved"
            outside.mkdir()
            replaced = False
            rename_blocked = False

            def replace_then_enter(binding):
                nonlocal rename_blocked, replaced
                if binding.path.name == "images" and not replaced:
                    try:
                        binding.path.rename(moved)
                    except OSError:
                        rename_blocked = True
                    else:
                        binding.path.mkdir()
                        replaced = True
                return original_enter(binding)

            try:
                with patch.object(
                    publication.OutputDirectoryBinding,
                    "__enter__",
                    new=replace_then_enter,
                ):
                    try:
                        result = native._save_native_images(
                            [FakeTensor(pixels)],
                            output_root=root,
                            path="images",
                            filename="image",
                            extension="png",
                            quality_jpeg_or_webp=80,
                            lossless_webp=False,
                            optimize_png=False,
                            embed_workflow=False,
                            save_workflow_as_json=False,
                            metadata=metadata,
                            prompt=None,
                            extra_pnginfo=None,
                        )
                    except publication.PublicationIntegrityError:
                        self.assertTrue(replaced)
                    else:
                        self.assertTrue(rename_blocked)
                        self.assertEqual(
                            result["ui"]["images"][0]["filename"],
                            "image.png",
                        )

                self.assertFalse((outside / "image.png").exists())
                self.assertFalse((moved / "image.png").exists())
                if replaced:
                    self.assertEqual(list((root / "images").iterdir()), [])
            finally:
                if replaced:
                    (root / "images").rmdir()
                    moved.rename(root / "images")

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

    def test_late_image_and_sidecar_targets_are_preserved_and_reallocated(self):
        metadata = native.NativeImageMetadata("parameters", "", {})
        pixels = np.zeros((2, 2, 3), dtype=np.float32)
        workflow = {"nodes": []}
        original = publication.OutputDirectoryBinding.link_no_replace

        for collision_name in ("image.png", "image.json"):
            with self.subTest(collision_name=collision_name), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                injected = False

                def collide_once(directory, temporary, target_name):
                    nonlocal injected
                    if not injected and target_name == collision_name:
                        injected = True
                        (directory.path / target_name).write_bytes(b"late owner")
                    return original(directory, temporary, target_name)

                with patch.object(
                    publication.OutputDirectoryBinding,
                    "link_no_replace",
                    new=collide_once,
                ):
                    result = native._save_native_images(
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
                        extra_pnginfo={"workflow": workflow},
                    )

                self.assertTrue(injected)
                self.assertEqual(
                    (root / collision_name).read_bytes(),
                    b"late owner",
                )
                self.assertEqual(
                    result["ui"]["images"][0]["filename"],
                    "image_01.png",
                )
                self.assertTrue((root / "image_01.png").is_file())
                self.assertEqual(
                    json.loads((root / "image_01.json").read_text("utf-8")),
                    workflow,
                )

    def test_image_commit_failure_removes_transaction_owned_sidecar(self):
        metadata = native.NativeImageMetadata("parameters", "", {})
        pixels = np.zeros((2, 2, 3), dtype=np.float32)
        original = publication.OutputDirectoryBinding.link_no_replace
        commit_order = []

        def fail_image_commit(directory, temporary, target_name):
            commit_order.append(target_name)
            if target_name == "image.png":
                raise OSError("image commit failed")
            return original(directory, temporary, target_name)

        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            with (
                patch.object(
                    publication.OutputDirectoryBinding,
                    "link_no_replace",
                    new=fail_image_commit,
                ),
                self.assertRaisesRegex(OSError, "image commit failed"),
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

            self.assertEqual(commit_order, ["image.json", "image.png"])
            self.assertFalse((root / "image.json").exists())
            self.assertFalse((root / "image.png").exists())

    def test_unconfirmed_image_cleanup_preserves_required_sidecar(self):
        metadata = native.NativeImageMetadata("parameters", "", {})
        pixels = np.zeros((2, 2, 3), dtype=np.float32)
        original_link = publication.OutputDirectoryBinding.link_no_replace
        original_unlink = publication.OutputDirectoryBinding._unlink_name

        def fail_after_image_publish(directory, temporary, target_name):
            identity = original_link(directory, temporary, target_name)
            if target_name == "image.png":
                raise OSError("failure after image publication")
            return identity

        def keep_locked_image(directory, name):
            if name == "image.png":
                raise PermissionError("image is locked")
            return original_unlink(directory, name)

        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            with (
                patch.object(
                    publication.OutputDirectoryBinding,
                    "link_no_replace",
                    new=fail_after_image_publish,
                ),
                patch.object(
                    publication.OutputDirectoryBinding,
                    "_unlink_name",
                    new=keep_locked_image,
                ),
                patch.object(publication, "_delete_windows_file_handle"),
                self.assertLogs("ComfyUI-EasyUseAnima", level="WARNING"),
                self.assertRaisesRegex(OSError, "failure after image publication"),
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

            self.assertTrue((root / "image.png").is_file())
            self.assertEqual(
                json.loads((root / "image.json").read_text(encoding="utf-8")),
                {"nodes": []},
            )

    def test_abrupt_exit_after_first_commit_cannot_expose_image_without_sidecar(self):
        script = """
import os
import sys
from pathlib import Path

from PIL import Image
from easyuse_anima.aio import native_output_publication as publication

root = Path(sys.argv[1])
with publication.OutputDirectoryBinding(root) as directory:
    original = directory.link_no_replace

    def exit_after_first_commit(temporary, target_name):
        original(temporary, target_name)
        os._exit(73)

    directory.link_no_replace = exit_after_first_commit
    publication.publish_image_transaction(
        directory,
        Image.new("RGB", (1, 1)),
        target_name="image.png",
        image_format="PNG",
        options={},
        sidecar_text='{"nodes":[]}\\n',
    )
"""
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            completed = subprocess.run(
                [sys.executable, "-c", script, str(root)],
                cwd=Path(__file__).resolve().parents[1],
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(completed.returncode, 73, completed.stderr)
            self.assertFalse((root / "image.png").exists())
            self.assertEqual(
                json.loads((root / "image.json").read_text(encoding="utf-8")),
                {"nodes": []},
            )

    @unittest.skipUnless(os.name == "nt", "Windows handle-close ordering")
    def test_windows_second_exit_during_async_rollback_cannot_leave_image_visible(self):
        script = """
import os
import sys
from pathlib import Path

from PIL import Image
from easyuse_anima.aio import native_output_publication as publication

root = Path(sys.argv[1])
original_close = publication._OpenTemporary.close
close_count = 0

def exit_after_first_rollback_close(temporary):
    global close_count
    original_close(temporary)
    close_count += 1
    if close_count == 1:
        os._exit(74)

publication._OpenTemporary.close = exit_after_first_rollback_close
with publication.OutputDirectoryBinding(root) as directory:
    original_link = directory.link_no_replace
    link_count = 0

    def interrupt_after_second_commit(temporary, target_name):
        global link_count
        identity = original_link(temporary, target_name)
        link_count += 1
        if link_count == 2:
            raise KeyboardInterrupt
        return identity

    directory.link_no_replace = interrupt_after_second_commit
    publication.publish_image_transaction(
        directory,
        Image.new("RGB", (1, 1)),
        target_name="image.png",
        image_format="PNG",
        options={},
        sidecar_text='{"nodes":[]}\\n',
    )
"""
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            completed = subprocess.run(
                [sys.executable, "-c", script, str(root)],
                cwd=Path(__file__).resolve().parents[1],
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(completed.returncode, 74, completed.stderr)
            self.assertFalse((root / "image.png").exists())

    @unittest.skipIf(os.name == "nt", "POSIX final-name rollback ordering")
    def test_posix_second_exit_during_async_rollback_cannot_leave_image_visible(self):
        script = """
import os
import sys
from pathlib import Path

from PIL import Image
from easyuse_anima.aio import native_output_publication as publication

root = Path(sys.argv[1])
original_remove = publication.OutputDirectoryBinding._remove_name_if_owned
remove_count = 0

def exit_after_first_final_remove(directory, name, identity):
    global remove_count
    removed = original_remove(directory, name, identity)
    remove_count += 1
    if remove_count == 1:
        os._exit(75)
    return removed

publication.OutputDirectoryBinding._remove_name_if_owned = exit_after_first_final_remove
with publication.OutputDirectoryBinding(root) as directory:
    original_link = directory.link_no_replace
    link_count = 0

    def interrupt_after_second_commit(temporary, target_name):
        global link_count
        identity = original_link(temporary, target_name)
        link_count += 1
        if link_count == 2:
            raise KeyboardInterrupt
        return identity

    directory.link_no_replace = interrupt_after_second_commit
    publication.publish_image_transaction(
        directory,
        Image.new("RGB", (1, 1)),
        target_name="image.png",
        image_format="PNG",
        options={},
        sidecar_text='{"nodes":[]}\\n',
    )
"""
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            completed = subprocess.run(
                [sys.executable, "-c", script, str(root)],
                cwd=Path(__file__).resolve().parents[1],
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(completed.returncode, 75, completed.stderr)
            self.assertFalse((root / "image.png").exists())

    def test_late_last_batch_collision_keeps_suffix_naming(self):
        metadata = native.NativeImageMetadata("parameters", "", {})
        pixels = np.zeros((2, 2, 3), dtype=np.float32)
        original = publication.OutputDirectoryBinding.link_no_replace
        injected = False

        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)

            def collide_on_second(directory, temporary, target_name):
                nonlocal injected
                if not injected and target_name == "batch_02.webp":
                    injected = True
                    (directory.path / target_name).write_bytes(b"late owner")
                return original(directory, temporary, target_name)

            with patch.object(
                publication.OutputDirectoryBinding,
                "link_no_replace",
                new=collide_on_second,
            ):
                result = native._save_native_images(
                    [FakeTensor(pixels), FakeTensor(pixels)],
                    output_root=root,
                    path="",
                    filename="batch",
                    extension="webp",
                    quality_jpeg_or_webp=80,
                    lossless_webp=False,
                    optimize_png=False,
                    embed_workflow=False,
                    save_workflow_as_json=False,
                    metadata=metadata,
                    prompt=None,
                    extra_pnginfo=None,
                )

            self.assertTrue(injected)
            self.assertEqual(
                [item["filename"] for item in result["ui"]["images"]],
                ["batch_01.webp", "batch_03.webp"],
            )
            self.assertEqual((root / "batch_02.webp").read_bytes(), b"late owner")
            self.assertFalse((root / "batch.webp").exists())

    def test_open_temporary_name_swap_is_blocked_or_rejected(self):
        metadata = native.NativeImageMetadata("parameters", "", {})
        pixels = np.zeros((2, 2, 3), dtype=np.float32)
        original = publication.OutputDirectoryBinding.assert_temporary_identity
        call_count = 0
        replaced = False

        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            outside = root / "outside.bin"
            outside.write_bytes(b"outside owner")

            def swap_after_encoding(directory, temporary):
                nonlocal call_count, replaced
                call_count += 1
                if call_count == 2:
                    temporary_path = directory.path / temporary.name
                    try:
                        temporary_path.unlink()
                        os.symlink(outside, temporary_path)
                        replaced = True
                    except OSError:
                        pass
                return original(directory, temporary)

            context = patch.object(
                publication.OutputDirectoryBinding,
                "assert_temporary_identity",
                new=swap_after_encoding,
            )
            if os.name == "nt":
                with context:
                    result = native._save_native_images(
                        [FakeTensor(pixels)],
                        output_root=root,
                        path="images",
                        filename="image",
                        extension="png",
                        quality_jpeg_or_webp=80,
                        lossless_webp=False,
                        optimize_png=False,
                        embed_workflow=False,
                        save_workflow_as_json=False,
                        metadata=metadata,
                        prompt=None,
                        extra_pnginfo=None,
                    )
                self.assertFalse(replaced)
                self.assertEqual(result["ui"]["images"][0]["filename"], "image.png")
            else:
                with context, self.assertRaises(publication.PublicationIntegrityError):
                    native._save_native_images(
                        [FakeTensor(pixels)],
                        output_root=root,
                        path="images",
                        filename="image",
                        extension="png",
                        quality_jpeg_or_webp=80,
                        lossless_webp=False,
                        optimize_png=False,
                        embed_workflow=False,
                        save_workflow_as_json=False,
                        metadata=metadata,
                        prompt=None,
                        extra_pnginfo=None,
                    )
                self.assertTrue(replaced)
            self.assertEqual(outside.read_bytes(), b"outside owner")
            self.assertEqual(list((root / "images").glob("*.tmp")), [])

    def test_bound_output_directory_blocks_or_rejects_link_swap(self):
        metadata = native.NativeImageMetadata("parameters", "", {})
        pixels = np.zeros((2, 2, 3), dtype=np.float32)
        original = native.publish_image_transaction

        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "output"
            outside = Path(temp) / "outside"
            outside.mkdir()
            moved = root / "moved"
            swapped = False

            def swap_directory(directory, image, **kwargs):
                nonlocal swapped
                try:
                    directory.path.rename(moved)
                except OSError:
                    return original(directory, image, **kwargs)
                try:
                    os.symlink(outside, directory.path, target_is_directory=True)
                except OSError:
                    swapped = True
                    return original(directory, image, **kwargs)
                swapped = True
                return original(directory, image, **kwargs)

            try:
                context = patch.object(
                    native,
                    "publish_image_transaction",
                    new=swap_directory,
                )
                try:
                    with context:
                        result = native._save_native_images(
                            [FakeTensor(pixels)],
                            output_root=root,
                            path="images",
                            filename="image",
                            extension="png",
                            quality_jpeg_or_webp=80,
                            lossless_webp=False,
                            optimize_png=False,
                            embed_workflow=False,
                            save_workflow_as_json=False,
                            metadata=metadata,
                            prompt=None,
                            extra_pnginfo=None,
                        )
                except publication.PublicationIntegrityError:
                    self.assertTrue(swapped)
                else:
                    self.assertFalse(swapped)
                    self.assertEqual(
                        result["ui"]["images"][0]["filename"],
                        "image.png",
                    )
                self.assertEqual(list(outside.iterdir()), [])
            finally:
                if swapped:
                    directory_link = root / "images"
                    if directory_link.is_symlink():
                        directory_link.unlink()
                    moved.rename(directory_link)

    def test_sidecar_write_failure_prevents_image_commit(self):
        metadata = native.NativeImageMetadata("parameters", "", {})
        pixels = np.zeros((2, 2, 3), dtype=np.float32)
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            with (
                patch.object(publication, "_write_text", side_effect=OSError("disk full")),
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
