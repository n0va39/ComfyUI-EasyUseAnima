from __future__ import annotations

import types
import unittest

from easyuse_anima.aio.torch_compile_diagnostics import (
    TORCH_COMPILE_NODE_ID,
    collect_torch_compile_diagnostics,
)


def _input_types():
    return {
        "required": {
            "model": ("MODEL",),
            "backend": (["inductor", "cudagraphs"], {"default": "inductor"}),
            "fullgraph": ("BOOLEAN", {"default": False}),
            "mode": (
                [
                    "default",
                    "max-autotune",
                    "max-autotune-no-cudagraphs",
                    "reduce-overhead",
                ],
                {"default": "default"},
            ),
            "dynamic": (["auto", "true", "false"], {"default": "auto"}),
            "compile_transformer_blocks_only": ("BOOLEAN", {"default": True}),
            "dynamo_cache_size_limit": ("INT", {"default": 64}),
            "debug_compile_keys": ("BOOLEAN", {"default": False}),
        },
        "optional": {
            "disable_dynamic_vram": ("BOOLEAN", {"default": False}),
        },
    }


class CompatibleTorchCompile:
    @classmethod
    def INPUT_TYPES(cls):
        return _input_types()

    def patch(
        self,
        model,
        backend,
        fullgraph,
        mode,
        dynamic,
        dynamo_cache_size_limit,
        compile_transformer_blocks_only,
        debug_compile_keys,
        disable_dynamic_vram=False,
    ):
        raise AssertionError("diagnostics must not invoke patch()")


class FakeCuda:
    def __init__(self, *, available: bool):
        self.available = available
        self.property_calls = 0

    def is_available(self):
        return self.available

    def current_device(self):
        if not self.available:
            raise AssertionError("unavailable CUDA must not inspect a device")
        return 0

    def get_device_properties(self, index):
        self.property_calls += 1
        if index != 0:
            raise AssertionError("unexpected device index")
        return types.SimpleNamespace(
            name="Fake CUDA Device",
            major=9,
            minor=0,
            total_memory=24 * 1024 * 1024 * 1024,
        )


class CompileSentinel:
    def __call__(self, *args, **kwargs):
        raise AssertionError("diagnostics must not invoke torch.compile")


def _fake_torch(*, cuda_available=True, include_compile=True):
    cuda = FakeCuda(available=cuda_available)
    values = {
        "__version__": "2.12.0+cu132",
        "version": types.SimpleNamespace(cuda="13.2", hip=None),
        "cuda": cuda,
        "backends": types.SimpleNamespace(
            mps=types.SimpleNamespace(is_available=lambda: False),
        ),
    }
    if include_compile:
        values["compile"] = CompileSentinel()
    return types.SimpleNamespace(**values), cuda


class TorchCompileDiagnosticsTests(unittest.TestCase):
    def _collect(self, torch, node_class=CompatibleTorchCompile):
        requested = []

        def find_node_class(node_id):
            requested.append(node_id)
            return node_class

        payload = collect_torch_compile_diagnostics(
            load_torch=lambda: torch,
            find_node_class=find_node_class,
            python_version=lambda: "3.13.5",
        )
        self.assertEqual(requested, [TORCH_COMPILE_NODE_ID])
        return payload

    def test_supported_fake_cuda_inventory_is_bounded_and_deterministic(self):
        torch, cuda = _fake_torch()

        first = self._collect(torch)
        second = self._collect(torch)

        self.assertEqual(first, second)
        self.assertTrue(first["supported"])
        self.assertEqual(first["profile"], "diagnostics_only")
        self.assertEqual(first["values"], {})
        self.assertEqual(first["reason_codes"], ["diagnostics_ready"])
        self.assertEqual(first["warnings"], ["recommendation_policy_pending"])
        self.assertEqual(
            first["environment"],
            {
                "python_version": "3.13.5",
                "torch_version": "2.12.0+cu132",
                "accelerator": "cuda",
                "cuda_runtime_version": "13.2",
                "rocm_runtime_version": None,
                "device_name": "Fake CUDA Device",
                "compute_capability": "9.0",
                "total_vram_mb": 24576,
                "kj_node_available": True,
                "kj_contract_compatible": True,
                "supported_inputs": sorted(
                    [
                        "model",
                        "backend",
                        "fullgraph",
                        "mode",
                        "dynamic",
                        "compile_transformer_blocks_only",
                        "dynamo_cache_size_limit",
                        "debug_compile_keys",
                        "disable_dynamic_vram",
                    ]
                ),
                "input_options": {
                    "backend": ["inductor", "cudagraphs"],
                    "mode": [
                        "default",
                        "max-autotune",
                        "max-autotune-no-cudagraphs",
                        "reduce-overhead",
                    ],
                    "dynamic": ["auto", "true", "false"],
                },
            },
        )
        self.assertEqual(cuda.property_calls, 2)

    def test_cuda_unavailable_fails_closed_without_device_probe(self):
        torch, cuda = _fake_torch(cuda_available=False)

        payload = self._collect(torch)

        self.assertFalse(payload["supported"])
        self.assertEqual(payload["profile"], "unsupported")
        self.assertEqual(payload["reason_codes"], ["cuda_unavailable"])
        self.assertEqual(payload["environment"]["accelerator"], "cpu")
        self.assertIsNone(payload["environment"]["device_name"])
        self.assertEqual(cuda.property_calls, 0)

    def test_missing_kj_node_fails_closed_with_installable_identity(self):
        torch, _cuda = _fake_torch()

        payload = collect_torch_compile_diagnostics(
            load_torch=lambda: torch,
            find_node_class=lambda _node_id: None,
            python_version=lambda: "3.13.5",
        )

        self.assertFalse(payload["supported"])
        self.assertEqual(payload["reason_codes"], ["kj_torch_compile_missing"])
        self.assertFalse(payload["environment"]["kj_node_available"])
        self.assertEqual(payload["environment"]["supported_inputs"], [])

    def test_old_torch_without_compile_fails_closed_without_calling_any_compile(self):
        torch, _cuda = _fake_torch(include_compile=False)

        payload = self._collect(torch)

        self.assertFalse(payload["supported"])
        self.assertEqual(payload["reason_codes"], ["torch_compile_unavailable"])

    def test_kj_input_contract_drift_is_reported_without_importing_private_source(self):
        class InputDrift(CompatibleTorchCompile):
            @classmethod
            def INPUT_TYPES(cls):
                inputs = _input_types()
                del inputs["required"]["debug_compile_keys"]
                inputs["required"]["new_required"] = ("BOOLEAN", {"default": False})
                return inputs

        torch, _cuda = _fake_torch()
        payload = self._collect(torch, InputDrift)

        self.assertFalse(payload["supported"])
        self.assertEqual(payload["reason_codes"], ["kj_input_contract_drift"])
        self.assertFalse(payload["environment"]["kj_contract_compatible"])

    def test_kj_patch_signature_drift_is_fail_closed_even_with_matching_schema(self):
        class SignatureDrift:
            @classmethod
            def INPUT_TYPES(cls):
                return _input_types()

            def patch(
                self,
                model,
                backend,
                fullgraph,
                mode,
                dynamic,
                compile_transformer_blocks_only,
                dynamo_cache_size_limit,
                debug_compile_keys,
            ):
                raise AssertionError("diagnostics must not invoke patch()")

        torch, _cuda = _fake_torch()
        payload = self._collect(torch, SignatureDrift)

        self.assertFalse(payload["supported"])
        self.assertEqual(payload["reason_codes"], ["kj_patch_signature_drift"])

    def test_unreadable_node_contract_and_missing_torch_remain_serializable(self):
        class Unreadable:
            @classmethod
            def INPUT_TYPES(cls):
                raise RuntimeError(r"C:\Users\alice\private-token")

        def missing_torch():
            raise ImportError("torch is unavailable")

        payload = collect_torch_compile_diagnostics(
            load_torch=missing_torch,
            find_node_class=lambda _node_id: Unreadable,
            python_version=lambda: "3.13.5",
        )

        self.assertFalse(payload["supported"])
        self.assertEqual(
            payload["reason_codes"],
            ["torch_unavailable", "cuda_unavailable", "kj_input_contract_unreadable"],
        )
        self.assertNotIn("alice", str(payload))
        self.assertNotIn("private-token", str(payload))


if __name__ == "__main__":
    unittest.main()
