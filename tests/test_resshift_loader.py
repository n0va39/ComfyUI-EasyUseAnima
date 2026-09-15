from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from easyuse_anima.aio import resshift_loader as loader


class ResShiftLoaderTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.student = self.root / "nested" / "student.safetensors"
        self.student.parent.mkdir()
        self.student.touch()
        self.vqgan = self.root / loader.VQGAN_NAME
        self.vqgan.touch()
        self.folders = SimpleNamespace(
            get_filename_list=Mock(return_value=["nested/student.safetensors", loader.VQGAN_NAME]),
            get_full_path=Mock(side_effect=lambda category, name: str(self.root / name)),
            get_folder_paths=Mock(return_value=[str(self.root)]),
        )

    def test_inventory_subfolder_and_windows_separator(self):
        self.assertEqual(
            loader.resolve_model_path("nested\\student.safetensors", self.folders),
            str(self.student.resolve()),
        )

    def test_untrusted_names_never_reach_model_lookup(self):
        for name in ("../student.pth", "C:/student.pth", "C:student.pth", "/student.pth",
                     "//server/share/a.pth", "nested/../a.pth", "a.pth:stream",
                     "https://example.com/a.pth", "a\x00.pth", "(auto-download)evil", "a.py"):
            with self.subTest(name=name), self.assertRaises(ValueError):
                loader.resolve_model_path(name, self.folders)
        self.folders.get_filename_list.assert_not_called()
        self.folders.get_full_path.assert_not_called()

    def test_missing_model_and_inventory_path_escape_are_rejected(self):
        with self.assertRaises(FileNotFoundError):
            loader.resolve_model_path("missing.pth", self.folders)
        self.folders.get_full_path.return_value = None
        self.folders.get_full_path.side_effect = lambda *_: str(self.root.parent)
        with self.assertRaises(ValueError):
            loader.resolve_model_path(loader.VQGAN_NAME, self.folders)

    def _host(self):
        tensor = object()
        student = Mock()
        vqgan = Mock()
        vqgan.load_state_dict.return_value = SimpleNamespace(missing_keys=[])
        bundle = Mock()
        torch = SimpleNamespace(
            is_tensor=lambda value: value is tensor, float32="fp32", bfloat16="bf16",
            nn=SimpleNamespace(Module=Mock(return_value=bundle)),
        )
        cfg = SimpleNamespace(
            autoencoder=SimpleNamespace(
                target="resshift.ldm.models.autoencoder.VQModelTorch",
                params=SimpleNamespace(ddconfig={"z_channels": 3}, n_embed=8192, embed_dim=3),
            ),
            diffusion=SimpleNamespace(params=SimpleNamespace(sf=2)),
        )
        inference = SimpleNamespace(
            load_configs=Mock(return_value=cfg), build_student=Mock(return_value=student),
            build_diffusion=Mock(return_value="diffusion"), swin_align=Mock(return_value=256),
            CONFIGS={"x2": "fixed-x2.yaml"},
            build_autoencoder=Mock(side_effect=AssertionError("unsafe loader called")),
        )
        provider = SimpleNamespace(R=inference, ResShiftModel=Mock(return_value="model"))
        management = SimpleNamespace(
            unet_offload_device=Mock(return_value="cpu"), get_torch_device=Mock(return_value="gpu"),
        )
        read = Mock(side_effect=[({"module.weight": tensor}, {"cond_lq": "pixel"}), {"weight": tensor}])
        utils = SimpleNamespace(load_torch_file=read)
        patcher = SimpleNamespace(ModelPatcher=Mock(return_value="patcher"))
        comfy = SimpleNamespace(model_management=management)
        modules = {
            "folder_paths": self.folders, "torch": torch, "comfy": comfy,
            "comfy.model_management": management, "comfy.model_patcher": patcher,
            "comfy.utils": utils, "test_resshift_provider": provider,
            "resshift.ldm.models.autoencoder": SimpleNamespace(VQModelTorch=Mock(return_value=vqgan)),
        }
        loader_class = type("ResShiftLoader", (), {"__module__": "test_resshift_provider"})
        settings = {"student_name": "nested/student.safetensors", "scale": "x2", "dtype": "bf16"}
        return SimpleNamespace(**locals())

    def test_both_models_use_safe_reads_and_preserve_metadata_and_precision(self):
        host = self._host()
        with patch.dict("sys.modules", host.modules):
            self.assertEqual(loader.load_local_resshift_model(host.loader_class, host.settings), "model")
        self.assertEqual(host.read.call_count, 2)
        host.read.assert_any_call(str(self.student.resolve()), safe_load=True, return_metadata=True)
        host.read.assert_any_call(str(self.vqgan.resolve()), safe_load=True)
        host.student.load_state_dict.assert_called_once_with({"weight": host.tensor}, strict=True)
        host.inference.build_student.assert_called_once_with(
            host.cfg, "cpu", dtype="fp32", noise_mode="concat", noise_channels=None,
        )
        host.provider.ResShiftModel.assert_called_once_with(
            "patcher", host.cfg, "diffusion", 2, 256, True, "pixel",
        )
        host.inference.build_autoencoder.assert_not_called()

    def test_missing_vqgan_stops_before_reading_student(self):
        host = self._host()
        self.folders.get_filename_list.return_value = ["nested/student.safetensors"]
        with patch.dict("sys.modules", host.modules), self.assertRaises(FileNotFoundError):
            loader.load_local_resshift_model(host.loader_class, host.settings)
        host.read.assert_not_called()
        host.inference.build_student.assert_not_called()

    def test_weights_only_failure_has_no_retry_or_unsafe_fallback(self):
        host = self._host()
        host.read.side_effect = RuntimeError("weights-only rejected object")
        with patch.dict("sys.modules", host.modules), self.assertRaisesRegex(RuntimeError, "weights-only"):
            loader.load_local_resshift_model(host.loader_class, host.settings)
        host.read.assert_called_once()
        host.inference.build_student.assert_not_called()
        host.inference.build_autoencoder.assert_not_called()

    def test_saved_auto_download_resolves_only_installed_default(self):
        host = self._host()
        default = self.root / loader.DEFAULT_STUDENTS["x2"]
        default.touch()
        self.folders.get_filename_list.return_value = [default.name, loader.VQGAN_NAME]
        host.settings["student_name"] = "(auto-download)"
        with patch.dict("sys.modules", host.modules):
            loader.load_local_resshift_model(host.loader_class, host.settings)
        self.assertEqual(host.read.call_args_list[0].args, (str(default.resolve()),))

    def test_pytorch_ema_metadata_and_tensor_only_validation(self):
        host = self._host()
        state, mode, channels, cond = loader._student_data(
            {"ema": {"module.weight": host.tensor}, "noise_mode": "add", "noise_channels": 3},
            None, host.torch,
        )
        self.assertEqual((state, mode, channels, cond), ({"weight": host.tensor}, "add", 3, "latent"))
        for value in ({}, {"weight": "not a tensor"}, None):
            with self.subTest(value=value), self.assertRaises(ValueError):
                loader._state_dict(value, host.torch)

    def test_bad_metadata_or_missing_vqgan_weights_fails_before_patcher(self):
        host = self._host()
        with self.assertRaises(ValueError):
            loader._student_data({"w": host.tensor}, {"cond_lq": "unknown"}, host.torch)
        host.vqgan.load_state_dict.return_value = SimpleNamespace(missing_keys=["encoder.weight"])
        with patch.dict("sys.modules", host.modules), self.assertRaisesRegex(ValueError, "missing required"):
            loader.load_local_resshift_model(host.loader_class, host.settings)
        host.patcher.ModelPatcher.assert_not_called()

    def test_unsupported_provider_never_uses_legacy_loader(self):
        host = self._host()
        host.provider.ResShiftModel = None
        with patch.dict("sys.modules", host.modules), self.assertRaisesRegex(RuntimeError, "Unsupported"):
            loader.load_local_resshift_model(host.loader_class, host.settings)
        host.read.assert_not_called()
