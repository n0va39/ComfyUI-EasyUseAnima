from __future__ import annotations

import sys
import types
import unittest
from unittest.mock import Mock, patch

from easyuse_anima.anima_29b import architecture, lora
from easyuse_anima.nodes import anima_29b_nodes


def _model_with_blocks(block_count: int):
    model_config = types.SimpleNamespace(
        unet_config={"image_model": "anima", "num_blocks": block_count}
    )
    return types.SimpleNamespace(model=types.SimpleNamespace(model_config=model_config))


def _fake_comfy_modules(*, detect_unet_config=None, load_torch_file=None, load_lora=None):
    comfy = types.ModuleType("comfy")
    comfy.__path__ = []
    modules = {"comfy": comfy}

    if detect_unet_config is not None:
        model_detection = types.ModuleType("comfy.model_detection")
        model_detection.detect_unet_config = detect_unet_config
        comfy.model_detection = model_detection
        modules["comfy.model_detection"] = model_detection
    if load_torch_file is not None:
        utils = types.ModuleType("comfy.utils")
        utils.load_torch_file = load_torch_file
        comfy.utils = utils
        modules["comfy.utils"] = utils
    if load_lora is not None:
        sd = types.ModuleType("comfy.sd")
        sd.load_lora_for_models = load_lora
        comfy.sd = sd
        modules["comfy.sd"] = sd
    return modules


class Anima29BArchitectureTests(unittest.TestCase):
    def test_manifest_block_mapping_preserves_original_expanded_positions(self):
        self.assertEqual(len(architecture.ANIMA_29B_LEGACY_BLOCK_MAP), 28)
        self.assertEqual(
            architecture.ANIMA_29B_LEGACY_BLOCK_MAP,
            (
                0,
                1,
                3,
                4,
                6,
                7,
                9,
                10,
                12,
                13,
                15,
                16,
                18,
                19,
                20,
                22,
                23,
                25,
                26,
                28,
                29,
                31,
                32,
                34,
                35,
                37,
                38,
                39,
            ),
        )

    def test_detection_patch_is_scoped_and_only_changes_complete_40_block_anima(self):
        base_detect = Mock(
            side_effect=lambda _state_dict, _prefix, metadata=None: {
                "image_model": "anima",
                "num_blocks": 28,
                "metadata": metadata,
            }
        )
        modules = _fake_comfy_modules(detect_unet_config=base_detect)
        model_detection = modules["comfy.model_detection"]
        state_dict = {
            f"diffusion_model.blocks.{index}.self_attn.qkv_proj.weight": object()
            for index in range(40)
        }

        with patch.dict(sys.modules, modules):
            with architecture._scoped_anima_29b_model_detection():
                self.assertIsNot(model_detection.detect_unet_config, base_detect)
                config = model_detection.detect_unet_config(
                    state_dict,
                    "diffusion_model.",
                    metadata={"source": "test"},
                )
            self.assertIs(model_detection.detect_unet_config, base_detect)

        self.assertEqual(config["num_blocks"], 40)
        self.assertEqual(config["metadata"], {"source": "test"})

        incomplete = dict(state_dict)
        incomplete.pop("diffusion_model.blocks.39.self_attn.qkv_proj.weight")
        self.assertEqual(
            architecture._patch_anima_29b_detected_config(
                {"image_model": "anima", "num_blocks": 28},
                incomplete,
                "diffusion_model.",
            )["num_blocks"],
            28,
        )

    def test_cached_disk_reload_reenters_scoped_detection(self):
        def base_detect(_state_dict, _prefix, metadata=None):
            return {"image_model": "anima", "num_blocks": 28}

        modules = _fake_comfy_modules(detect_unet_config=base_detect)
        model_detection = modules["comfy.model_detection"]
        reload_was_scoped: list[bool] = []
        reload_kwargs: list[dict[str, object]] = []

        def core_reload(path, options, **kwargs):
            reload_was_scoped.append(model_detection.detect_unet_config is not base_detect)
            reload_kwargs.append(kwargs)
            fresh = _model_with_blocks(40)
            fresh.cached_patcher_init = (core_reload, (path, options))
            return fresh

        model = _model_with_blocks(40)
        model.cached_patcher_init = (
            core_reload,
            ("anima-2.9b.safetensors", {"dtype": "bf16"}),
        )

        with patch.dict(sys.modules, modules):
            loaded = architecture._load_model_with_anima_29b_support(lambda: model)
            cached_factory, cached_args = loaded.cached_patcher_init
            fresh = cached_factory(*cached_args, disable_dynamic=True)

        self.assertIs(cached_factory, architecture._reload_anima_29b_model)
        self.assertEqual(reload_was_scoped, [True])
        self.assertEqual(reload_kwargs, [{"disable_dynamic": True}])
        self.assertIs(
            fresh.cached_patcher_init[0],
            architecture._reload_anima_29b_model,
        )
        self.assertIs(model_detection.detect_unet_config, base_detect)


class Anima29BLoraTests(unittest.TestCase):
    def test_legacy_keys_are_remapped_and_non_model_keys_are_preserved(self):
        original = {
            "lora_unet_blocks_2_self_attn_qkv_proj.lora_down.weight": "down",
            "lora_unet__blocks_27_cross_attn_k.lora_up.weight": "up",
            "model.diffusion_model.blocks.5.mlp.layer1.lora_down.weight": "generic",
            "blocks.6.mlp.layer2.lora_up.weight": "bare",
            "lora_te_qwen3_blocks_2_attn.lora_down.weight": "clip",
        }

        converted, count = lora._prepare_anima_29b_lora_state_dict(
            original,
            lora.ANIMA_29B_LORA_LAYOUT_LEGACY,
        )

        self.assertEqual(count, 4)
        self.assertEqual(
            converted["lora_unet_blocks_3_self_attn_qkv_proj.lora_down.weight"],
            "down",
        )
        self.assertEqual(
            converted["lora_unet_blocks_39_cross_attn_k.lora_up.weight"],
            "up",
        )
        self.assertEqual(
            converted["diffusion_model.blocks.7.mlp.layer1.lora_down.weight"],
            "generic",
        )
        self.assertEqual(
            converted["diffusion_model.blocks.9.mlp.layer2.lora_up.weight"],
            "bare",
        )
        self.assertEqual(
            converted["lora_te_qwen3_blocks_2_attn.lora_down.weight"],
            "clip",
        )

    def test_auto_layout_preserves_native_40_block_lora(self):
        native = {
            "lora_unet_blocks_3_self_attn_qkv_proj.lora_down.weight": "base",
            "lora_unet_blocks_30_self_attn_qkv_proj.lora_down.weight": "expanded",
        }

        converted, count = lora._prepare_anima_29b_lora_state_dict(native)

        self.assertEqual(converted, native)
        self.assertEqual(count, 0)
        with self.assertRaisesRegex(RuntimeError, "already contains Anima 2.9B"):
            lora._prepare_anima_29b_lora_state_dict(
                native,
                lora.ANIMA_29B_LORA_LAYOUT_LEGACY,
            )

    def test_auto_layout_remaps_complete_legacy_28_block_lora(self):
        legacy = {
            f"lora_unet_blocks_{index}_self_attn_q_proj.lora_down.weight": index
            for index in range(28)
        }

        converted, count = lora._prepare_anima_29b_lora_state_dict(legacy)

        self.assertEqual(count, 26)
        self.assertEqual(
            {
                int(key.partition("lora_unet_blocks_")[2].partition("_")[0])
                for key in converted
            },
            set(architecture.ANIMA_29B_LEGACY_BLOCK_MAP),
        )

    def test_auto_layout_rejects_sparse_low_block_layout_as_ambiguous(self):
        sparse = {
            "lora_unet_blocks_0_self_attn_qkv_proj.lora_down.weight": "down",
            "lora_unet_blocks_27_self_attn_qkv_proj.lora_up.weight": "up",
        }

        with self.assertRaisesRegex(RuntimeError, "layout is ambiguous"):
            lora._prepare_anima_29b_lora_state_dict(sparse)

        converted, count = lora._prepare_anima_29b_lora_state_dict(
            sparse,
            lora.ANIMA_29B_LORA_LAYOUT_LEGACY,
        )
        self.assertEqual(count, 1)
        self.assertIn(
            "lora_unet_blocks_39_self_attn_qkv_proj.lora_up.weight",
            converted,
        )

    def test_stack_loader_remaps_in_order_and_preserves_metadata_and_strengths(self):
        load_calls: list[tuple[object, ...]] = []
        lora_files = {
            "first.safetensors": {
                "lora_unet_blocks_2_self_attn_qkv_proj.lora_down.weight": "first"
            },
            "second.safetensors": {
                "lora_unet_blocks_27_mlp_layer2.lora_up.weight": "second"
            },
        }

        def load_torch_file(path, safe_load=True, return_metadata=True):
            name = str(path).rsplit("/", 1)[-1]
            return lora_files[name], {"name": name}

        def load_lora_for_models(
            model,
            clip,
            state_dict,
            strength_model,
            strength_clip,
            lora_metadata=None,
        ):
            load_calls.append(
                (
                    model,
                    clip,
                    state_dict,
                    strength_model,
                    strength_clip,
                    lora_metadata,
                )
            )
            name = lora_metadata["name"]
            return f"{model}>{name}", f"{clip}>{name}"

        folder_paths = types.ModuleType("folder_paths")
        folder_paths.get_full_path_or_raise = lambda _kind, name: f"C:/loras/{name}"
        modules = _fake_comfy_modules(
            load_torch_file=load_torch_file,
            load_lora=load_lora_for_models,
        )
        modules["folder_paths"] = folder_paths

        with patch.dict(sys.modules, modules):
            result = lora._apply_anima_29b_lora_stack(
                _model_with_blocks(40),
                "clip",
                [
                    ("first.safetensors", 0.8, 0.6),
                    ("skip.safetensors", 0.0, 0.0),
                    ("second.safetensors", 1.2, 0.7),
                ],
                source_layout=lora.ANIMA_29B_LORA_LAYOUT_LEGACY,
            )

        self.assertEqual(result[0].count(">"), 2)
        self.assertEqual(result[1], "clip>first.safetensors>second.safetensors")
        self.assertEqual(
            list(load_calls[0][2]),
            ["lora_unet_blocks_3_self_attn_qkv_proj.lora_down.weight"],
        )
        self.assertEqual(
            list(load_calls[1][2]),
            ["lora_unet_blocks_39_mlp_layer2.lora_up.weight"],
        )
        self.assertEqual(
            load_calls[0][3:6],
            (0.8, 0.6, {"name": "first.safetensors"}),
        )
        self.assertEqual(
            [item["name"] for item in result[2]],
            ["first.safetensors", "second.safetensors"],
        )

    def test_aio_hook_only_claims_40_block_anima_models(self):
        self.assertIsNone(
            lora._apply_anima_29b_aio_lora_stack(
                _model_with_blocks(28),
                "clip",
                [("legacy.safetensors", 1.0, 1.0)],
            )
        )


class Anima29BNodeTests(unittest.TestCase):
    def test_node_has_fixed_stack_contract_and_forces_legacy_layout(self):
        input_types = anima_29b_nodes.EasyUseAnima29BLoraStackLoader.INPUT_TYPES()
        self.assertEqual(
            list(input_types["required"]),
            ["model", "clip", "lora_stack"],
        )
        self.assertEqual(
            anima_29b_nodes.EasyUseAnima29BLoraStackLoader.RETURN_TYPES,
            ("MODEL", "CLIP"),
        )

        apply_stack = Mock(return_value=("patched-model", "patched-clip", []))
        with (
            patch.object(
                anima_29b_nodes,
                "_normalize_lora_stack",
                return_value=[("legacy.safetensors", 0.8, 0.6)],
            ),
            patch.object(
                anima_29b_nodes,
                "_apply_anima_29b_lora_stack",
                apply_stack,
            ),
        ):
            result = anima_29b_nodes.EasyUseAnima29BLoraStackLoader().apply(
                "model",
                "clip",
                ["stack"],
            )

        self.assertEqual(result, ("patched-model", "patched-clip"))
        apply_stack.assert_called_once_with(
            "model",
            "clip",
            [("legacy.safetensors", 0.8, 0.6)],
            source_layout=lora.ANIMA_29B_LORA_LAYOUT_LEGACY,
        )


if __name__ == "__main__":
    unittest.main()
