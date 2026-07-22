from __future__ import annotations

import unittest
from unittest.mock import Mock, patch

import nodes
from easyuse_anima.aio import model_preparation


class AIOModelPreparationMoveTests(unittest.TestCase):
    def test_root_symbols_are_direct_canonical_aliases(self):
        for name in (
            "_patch_model_sampling_aura_flow",
            "_apply_aio_kj_model_patches",
            "_apply_aio_model_patches",
            "_normalize_aio_lora_stack",
            "_apply_aio_lora_stack",
            "_apply_aio_anima_dave_patch",
            "_apply_aio_safe_pag_patch",
        ):
            with self.subTest(name=name):
                self.assertIs(getattr(nodes, name), getattr(model_preparation, name))

    def test_lora_normalization_and_application_preserve_order_and_identity(self):
        stack = {
            "__value__": [
                {"name": "style/foo.safetensors", "strength": "0.8", "clip_strength": "0.6"},
                ("skip.safetensors", 0, 0),
                {"lora_name": "bar.safetensors", "model_strength": 1.2, "strengthTwo": 0.7},
                {"name": "None", "strength": 1.0},
            ]
        }
        self.assertEqual(
            model_preparation._normalize_aio_lora_stack(stack),
            [
                ("style\\foo.safetensors", 0.8, 0.6),
                ("skip.safetensors", 0.0, 0.0),
                ("bar.safetensors", 1.2, 0.7),
            ],
        )

        calls: list[tuple[object, ...]] = []

        class LoraLoader:
            def load_lora(self, model, clip, name, model_strength, clip_strength):
                calls.append((model, clip, name, model_strength, clip_strength))
                return f"{model}>{name}", f"{clip}>{name}"

        with patch.object(nodes, "_find_comfy_node_class", return_value=LoraLoader):
            model, clip, applied = model_preparation._apply_aio_lora_stack(
                "model", "clip", stack
            )

        self.assertEqual(model, "model>style\\foo.safetensors>bar.safetensors")
        self.assertEqual(clip, "clip>style\\foo.safetensors>bar.safetensors")
        self.assertEqual([item[2] for item in calls], ["style\\foo.safetensors", "bar.safetensors"])
        self.assertEqual([item["name"] for item in applied], ["style\\foo.safetensors", "bar.safetensors"])

        original_model = object()
        original_clip = object()
        result_model, result_clip, applied = model_preparation._apply_aio_lora_stack(
            original_model, original_clip, []
        )
        self.assertIs(result_model, original_model)
        self.assertIs(result_clip, original_clip)
        self.assertEqual(applied, [])

    def test_model_patch_aggregate_re_resolves_each_root_subcall_in_order(self):
        trace: list[tuple[str, object]] = []
        replacement_dave = Mock(
            side_effect=lambda model, _settings: trace.append(("dave", model)) or "dave"
        )

        def apply_aura(model, _settings):
            trace.append(("aura", model))
            nodes._apply_aio_anima_dave_patch = replacement_dave
            return "aura"

        stale_dave = Mock(return_value="stale")

        def apply_safe_pag(model, _settings):
            trace.append(("safe_pag", model))
            return "safe_pag"

        def apply_kj(model, _settings):
            trace.append(("kj", model))
            return "kj"

        with (
            patch.object(nodes, "_patch_model_sampling_aura_flow", side_effect=apply_aura),
            patch.object(nodes, "_apply_aio_anima_dave_patch", stale_dave),
            patch.object(nodes, "_apply_aio_safe_pag_patch", side_effect=apply_safe_pag),
            patch.object(nodes, "_apply_aio_kj_model_patches", side_effect=apply_kj),
        ):
            result = model_preparation._apply_aio_model_patches(
                "base",
                {
                    "model_patches": {
                        "aura_flow": {"shift": 3.0},
                        "dave": {"enabled": True},
                        "safe_pag": {"enabled": True},
                        "kj": {"fp16_accumulation": True},
                    }
                },
            )

        self.assertEqual(result, "kj")
        self.assertEqual(
            trace,
            [
                ("aura", "base"),
                ("dave", "aura"),
                ("safe_pag", "dave"),
                ("kj", "safe_pag"),
            ],
        )
        stale_dave.assert_not_called()

    def test_kj_patch_chain_preserves_fp16_sage_compile_order_and_arguments(self):
        calls: list[tuple[object, ...]] = []

        class TorchSettings:
            def patch(self, *args):
                calls.append(("fp16", *args))
                return ("fp16",)

        class SageAttention:
            def patch(self, *args):
                calls.append(("sage", *args))
                return ("sage",)

        class TorchCompile:
            def patch(self, *args):
                calls.append(("compile", *args))
                return ("compile",)

        classes = {
            "ModelPatchTorchSettings": TorchSettings,
            "PathchSageAttentionKJ": SageAttention,
            "TorchCompileModelAdvanced": TorchCompile,
        }
        with patch.object(nodes, "_require_custom_node_class", side_effect=lambda node_id, *_: classes[node_id]):
            result = model_preparation._apply_aio_kj_model_patches(
                "base",
                {
                    "fp16_accumulation": True,
                    "sage_attention": "sageattn",
                    "sage_allow_compile": True,
                    "torch_compile": {
                        "enabled": True,
                        "backend": "inductor",
                        "fullgraph": True,
                        "mode": "reduce-overhead",
                        "dynamic": "false",
                        "dynamo_cache_size_limit": 32,
                        "compile_transformer_blocks_only": False,
                        "debug_compile_keys": True,
                        "disable_dynamic_vram": True,
                    },
                },
            )

        self.assertEqual(result, "compile")
        self.assertEqual(calls[0], ("fp16", "base", True))
        self.assertEqual(calls[1], ("sage", "fp16", "sageattn", True))
        self.assertEqual(
            calls[2],
            (
                "compile",
                "sage",
                "inductor",
                True,
                "reduce-overhead",
                "false",
                32,
                False,
                True,
                True,
            ),
        )


if __name__ == "__main__":
    unittest.main()
