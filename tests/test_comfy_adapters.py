from __future__ import annotations

import builtins
import sys
import types
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from easyuse_anima.aio import input_defaults, resources as aio_resources
from easyuse_anima.infrastructure.comfy import capabilities, invocation, resources
from easyuse_anima.nodes import sam3_nodes


class ComfyCapabilityAdapterTests(unittest.TestCase):
    def test_max_resolution_and_sampler_scheduler_fallbacks_are_preserved(self):
        self.assertEqual(capabilities._comfy_max_resolution(None), 16384)
        self.assertEqual(
            capabilities._comfy_max_resolution(SimpleNamespace(MAX_RESOLUTION="8192")),
            8192,
        )

        real_import = builtins.__import__

        def import_without_comfy(name, globals=None, locals=None, fromlist=(), level=0):
            if name == "comfy.samplers":
                raise ImportError("ComfyUI is unavailable")
            return real_import(name, globals, locals, fromlist, level)

        with patch("builtins.__import__", side_effect=import_without_comfy):
            self.assertEqual(
                capabilities._comfy_sampler_names(),
                [
                    "er_sde",
                    "euler",
                    "euler_ancestral",
                    "heun",
                    "dpm_2",
                    "dpm_2_ancestral",
                    "dpmpp_2m",
                    "dpmpp_sde",
                    "ddim",
                ],
            )
            self.assertEqual(
                capabilities._comfy_scheduler_names(),
                [
                    "simple",
                    "sgm_uniform",
                    "karras",
                    "exponential",
                    "ddim_uniform",
                    "beta",
                    "normal",
                    "linear_quadratic",
                    "kl_optimal",
                    "AYS SDXL",
                    "AYS SD1",
                    "AYS SVD",
                    "GITS[coeff=1.2]",
                    "LTXV[default]",
                    "OSS FLUX",
                    "OSS Wan",
                    "OSS Chroma",
                ],
            )

    def test_impact_scheduler_lookup_preserves_loaded_module_and_comfy_fallbacks(self):
        loaded_core = SimpleNamespace(get_schedulers=lambda: ("impact-a", "impact-b"))
        with patch.dict(sys.modules, {"impact.core": loaded_core}):
            self.assertIs(capabilities._impact_core_module(), loaded_core)
            self.assertEqual(
                capabilities._impact_scheduler_names(),
                ["impact-a", "impact-b"],
            )

        real_import = builtins.__import__

        def import_without_impact_or_comfy(name, globals=None, locals=None, fromlist=(), level=0):
            if name in {"impact.core", "modules.impact", "comfy.samplers"}:
                raise ImportError(f"{name} is unavailable")
            return real_import(name, globals, locals, fromlist, level)

        with (
            patch.dict(sys.modules, {"impact.core": None}),
            patch("builtins.__import__", side_effect=import_without_impact_or_comfy),
        ):
            self.assertIsNone(capabilities._impact_core_module())
            self.assertEqual(
                capabilities._impact_scheduler_names(),
                ["normal", "karras", "exponential", "sgm_uniform", "simple", "ddim_uniform"],
            )

    def test_node_discovery_checks_injected_and_loaded_module_mappings(self):
        direct_class = type("DirectNode", (), {})
        attribute_class = type("AttributeNode", (), {})
        loaded_class = type("LoadedNode", (), {})
        comfy_nodes = SimpleNamespace(
            NODE_CLASS_MAPPINGS={"DirectNode": direct_class},
            AttributeNode=attribute_class,
        )
        loaded_module = types.ModuleType("easyuse_anima_test_loaded_nodes")
        loaded_module.NODE_CLASS_MAPPINGS = {"UniqueLoadedNode": loaded_class}

        with patch.dict(sys.modules, {loaded_module.__name__: loaded_module}):
            self.assertIs(
                capabilities._find_comfy_node_class("DirectNode", comfy_nodes),
                direct_class,
            )
            self.assertIs(
                capabilities._find_comfy_node_class("AttributeNode", comfy_nodes),
                attribute_class,
            )
            self.assertIs(
                capabilities._find_comfy_node_class("UniqueLoadedNode"),
                loaded_class,
            )
            self.assertIs(
                capabilities._find_loaded_node_class("UniqueLoadedNode", lambda _node_id: None),
                loaded_class,
            )

    def test_required_node_errors_and_candidate_order_are_preserved(self):
        found_class = type("FoundNode", (), {})
        calls = []

        def find_node(node_id):
            calls.append(node_id)
            return found_class if node_id == "SecondNode" else None

        self.assertEqual(
            capabilities._require_any_custom_node_class(
                ("FirstNode", "SecondNode", "ThirdNode"),
                "Example Pack",
                "Repository: https://example.invalid",
                find_node,
            ),
            ("SecondNode", found_class),
        )
        self.assertEqual(calls, ["FirstNode", "SecondNode"])

        with self.assertRaises(RuntimeError) as missing_one:
            capabilities._require_custom_node_class(
                "MissingNode",
                "Example Pack",
                "Install hint.",
                lambda _node_id: None,
            )
        self.assertEqual(
            str(missing_one.exception),
            "[EasyUseAnima] Missing required custom node 'MissingNode'. "
            "Install/enable Example Pack, then restart ComfyUI. Install hint.",
        )

        with self.assertRaises(RuntimeError) as missing_any:
            capabilities._require_any_custom_node_class(
                ("FirstNode", "SecondNode"),
                "Example Pack",
                "Install hint.",
                lambda _node_id: None,
            )
        self.assertEqual(
            str(missing_any.exception),
            "[EasyUseAnima] Missing required custom node. Tried 'FirstNode', 'SecondNode'. "
            "Install/enable Example Pack, then restart ComfyUI. Install hint.",
        )


class ComfyResourceAdapterTests(unittest.TestCase):
    def test_resource_file_revision_uses_resolved_path_size_and_mtime(self):
        calls = []
        folder_paths = SimpleNamespace(
            get_full_path=lambda folder_name, filename: (
                calls.append((folder_name, filename))
                or "models/runtime.safetensors"
            ),
        )
        resolved_path = Path("canonical/runtime.safetensors")
        with (
            patch.dict(sys.modules, {"folder_paths": folder_paths}),
            patch.object(
                resources.Path,
                "resolve",
                return_value=resolved_path,
            ) as resolve,
            patch.object(
                resources.Path,
                "stat",
                return_value=SimpleNamespace(
                    st_size=1234,
                    st_mtime_ns=5678,
                ),
            ) as stat,
        ):
            revision = resources._comfy_resource_file_revision(
                "diffusion_models",
                "anima.safetensors",
            )

        self.assertEqual(
            revision,
            {
                "path": str(resolved_path),
                "size": 1234,
                "mtime_ns": 5678,
            },
        )
        self.assertEqual(
            calls,
            [("diffusion_models", "anima.safetensors")],
        )
        resolve.assert_called_once_with(strict=False)
        stat.assert_called_once_with()

    def test_resource_file_revision_supports_legacy_resolver_and_safe_fallbacks(self):
        legacy_calls = []
        legacy_folder_paths = SimpleNamespace(
            get_full_path_or_raise=lambda folder_name, filename: (
                legacy_calls.append((folder_name, filename))
                or "models/legacy.safetensors"
            ),
        )
        with (
            patch.dict(sys.modules, {"folder_paths": legacy_folder_paths}),
            patch.object(
                resources.Path,
                "resolve",
                return_value=Path("canonical/legacy.safetensors"),
            ),
            patch.object(
                resources.Path,
                "stat",
                return_value=SimpleNamespace(
                    st_size=10,
                    st_mtime_ns=20,
                ),
            ),
        ):
            self.assertEqual(
                resources._comfy_resource_file_revision(
                    "vae",
                    "legacy.safetensors",
                ),
                {
                    "path": str(Path("canonical/legacy.safetensors")),
                    "size": 10,
                    "mtime_ns": 20,
                },
            )
        self.assertEqual(
            legacy_calls,
            [("vae", "legacy.safetensors")],
        )

        self.assertIsNone(
            resources._comfy_resource_file_revision("", "model")
        )
        self.assertIsNone(
            resources._comfy_resource_file_revision("vae", "")
        )
        for folder_paths in (
            SimpleNamespace(),
            SimpleNamespace(get_full_path=lambda *_args: None),
            SimpleNamespace(get_full_path=lambda *_args: object()),
            SimpleNamespace(
                get_full_path=lambda *_args: (
                    _ for _ in ()
                ).throw(RuntimeError("unavailable"))
            ),
        ):
            with self.subTest(folder_paths=folder_paths), patch.dict(
                sys.modules,
                {"folder_paths": folder_paths},
            ):
                self.assertIsNone(
                    resources._comfy_resource_file_revision(
                        "vae",
                        "missing.safetensors",
                    )
                )

        folder_paths = SimpleNamespace(
            get_full_path=lambda *_args: "models/broken.safetensors",
        )
        with (
            patch.dict(sys.modules, {"folder_paths": folder_paths}),
            patch.object(
                resources.Path,
                "resolve",
                return_value=Path("canonical/broken.safetensors"),
            ),
            patch.object(
                resources.Path,
                "stat",
                side_effect=OSError("stat failed"),
            ),
        ):
            self.assertIsNone(
                resources._comfy_resource_file_revision(
                    "vae",
                    "broken.safetensors",
                )
            )

    def test_folder_resources_use_runtime_names_and_preserve_fallbacks(self):
        folder_paths = SimpleNamespace(
            get_filename_list=lambda folder_name: {
                "checkpoints": ["runtime.ckpt"],
                "diffusion_models": ["runtime.diffusion"],
            }.get(folder_name, []),
        )
        with patch.dict(sys.modules, {"folder_paths": folder_paths}):
            self.assertEqual(resources._comfy_checkpoint_names(), ["runtime.ckpt"])
            self.assertEqual(
                resources._folder_path_names("diffusion_models", ["fallback.diffusion"]),
                ["runtime.diffusion"],
            )
            fallback = ["fallback.vae"]
            self.assertEqual(resources._folder_path_names("vae", fallback), fallback)
            self.assertIsNot(resources._folder_path_names("vae", fallback), fallback)

        failing_folder_paths = SimpleNamespace(
            get_filename_list=lambda _folder_name: (_ for _ in ()).throw(RuntimeError("failed")),
        )
        with patch.dict(sys.modules, {"folder_paths": failing_folder_paths}):
            self.assertEqual(
                resources._comfy_checkpoint_names(),
                ["sam3.1_multiplex_fp16.safetensors"],
            )

    def test_feature_fallbacks_and_discovery_are_injected(self):
        folder_calls = []

        def folder_names(folder_name, fallback):
            folder_calls.append((folder_name, fallback))
            return fallback

        self.assertEqual(
            resources._comfy_diffusion_model_names(("diffusion.safetensors",), folder_names),
            ["diffusion.safetensors"],
        )
        self.assertEqual(
            resources._comfy_text_encoder_names(("clip.safetensors",), folder_names),
            ["clip.safetensors"],
        )

        class VaeLoader:
            @classmethod
            def INPUT_TYPES(cls):
                return {"required": {"vae_name": (["runtime.vae"],)}}

        class ClipLoader:
            @classmethod
            def INPUT_TYPES(cls):
                return {"required": {"type": (["qwen_image", "flux2"],)}}

        loaders = {"VAELoader": VaeLoader, "CLIPLoader": ClipLoader}
        find_node = loaders.get
        self.assertEqual(
            resources._comfy_vae_names(("fallback.vae",), find_node, folder_names),
            ["runtime.vae"],
        )
        self.assertEqual(
            resources._comfy_clip_loader_types(("fallback",), find_node),
            ["qwen_image", "flux2"],
        )
        self.assertEqual(
            folder_calls,
            [
                ("diffusion_models", ["diffusion.safetensors"]),
                ("text_encoders", ["clip.safetensors"]),
            ],
        )


class ComfyInvocationAdapterTests(unittest.TestCase):
    def test_clip_encoding_uses_injected_call_time_node_lookup(self):
        calls = []

        class ClipTextEncode:
            def encode(self, clip, text):
                calls.append((clip, text))
                return ("conditioning", "ignored")

        self.assertEqual(
            invocation._encode_with_comfy_clip(
                "clip",
                "prompt",
                lambda node_id: ClipTextEncode if node_id == "CLIPTextEncode" else None,
            ),
            "conditioning",
        )
        self.assertEqual(calls, [("clip", "prompt")])

        with self.assertRaises(RuntimeError) as missing_class:
            invocation._encode_with_comfy_clip("clip", "prompt", lambda _node_id: None)
        self.assertEqual(
            str(missing_class.exception),
            "[EasyUseAnima] Could not find ComfyUI CLIPTextEncode.",
        )

        class MissingEncode:
            pass

        with self.assertRaises(RuntimeError) as missing_method:
            invocation._encode_with_comfy_clip(
                "clip",
                "prompt",
                lambda _node_id: MissingEncode,
            )
        self.assertEqual(
            str(missing_method.exception),
            "[EasyUseAnima] CLIPTextEncode does not expose encode.",
        )

        for invalid_result in ((), ["conditioning"]):
            class InvalidResult:
                def encode(self, _clip, _text):
                    return invalid_result

            with self.subTest(invalid_result=invalid_result):
                with self.assertRaises(RuntimeError) as invalid:
                    invocation._encode_with_comfy_clip(
                        "clip",
                        "prompt",
                        lambda _node_id: InvalidResult,
                    )
                self.assertEqual(
                    str(invalid.exception),
                    "[EasyUseAnima] CLIPTextEncode returned no conditioning.",
                )

        def failing_lookup(_node_id):
            raise LookupError("lookup failed")

        with self.assertRaisesRegex(LookupError, "lookup failed"):
            invocation._encode_with_comfy_clip("clip", "prompt", failing_lookup)

        class FailingEncode:
            def encode(self, _clip, _text):
                raise KeyError("encode failed")

        with self.assertRaisesRegex(KeyError, "encode failed"):
            invocation._encode_with_comfy_clip(
                "clip",
                "prompt",
                lambda _node_id: FailingEncode,
            )

    def test_signature_filtering_var_kwargs_and_missing_required_are_preserved(self):
        calls = []

        def filtered(model, *, steps=20):
            calls.append((model, steps))
            return "filtered"

        self.assertEqual(
            invocation._call_with_supported_kwargs(
                filtered,
                ("model",),
                {"steps": 30, "unsupported": True},
                "Filtered node",
            ),
            "filtered",
        )
        self.assertEqual(calls, [("model", 30)])

        def accepts_all(model, **kwargs):
            return model, kwargs

        self.assertEqual(
            invocation._call_with_supported_kwargs(
                accepts_all,
                ("model",),
                {"future_input": 1},
                "Flexible node",
            ),
            ("model", {"future_input": 1}),
        )

        def missing(model, *, required_input):
            return model, required_input

        with self.assertRaises(RuntimeError) as raised:
            invocation._call_with_supported_kwargs(
                missing,
                ("model",),
                {"unsupported": True},
                "Changed node",
            )
        self.assertEqual(
            str(raised.exception),
            "[EasyUseAnima] Changed node requires unsupported new input(s): required_input. "
            "Update ComfyUI-EasyUseAnima or disable that node option.",
        )

    def test_output_tuple_normalization_is_preserved(self):
        self.assertEqual(invocation._node_output_tuple(SimpleNamespace(result=[1, 2])), (1, 2))
        self.assertEqual(invocation._node_output_tuple({"result": [3, 4]}), (3, 4))
        original = (5, 6)
        self.assertIs(invocation._node_output_tuple(original), original)
        self.assertEqual(invocation._node_output_tuple("value"), ("value",))


class ComfyCanonicalOwnerTests(unittest.TestCase):
    def test_checkpoint_names_are_owned_by_the_canonical_sam3_consumer(self):
        self.assertIs(
            sam3_nodes._comfy_checkpoint_names,
            resources._comfy_checkpoint_names,
        )
        checkpoint_names = ["sam3-b.safetensors", "sam3-a.safetensors"]
        with (
            patch.object(
                sam3_nodes,
                "_comfy_checkpoint_names",
                return_value=checkpoint_names,
            ) as names,
            patch.object(
                sam3_nodes,
                "_preferred_checkpoint_default",
                return_value="sam3-a.safetensors",
            ) as preferred,
        ):
            input_types = sam3_nodes.EasyUseAnimaSAM3Context.INPUT_TYPES()

        self.assertIs(input_types["required"]["ckpt_name"][0], checkpoint_names)
        self.assertEqual(
            input_types["required"]["ckpt_name"][1]["default"],
            "sam3-a.safetensors",
        )
        names.assert_called_once_with()
        preferred.assert_called_once_with(
            checkpoint_names,
            "sam3.1_multiplex_fp16.safetensors",
        )

    def test_aio_resource_wrappers_inject_canonical_constants_and_aliases(self):
        folder_calls = []

        def folder_names(folder_name, fallback):
            folder_calls.append((folder_name, fallback))
            return fallback

        with patch.object(
            aio_resources,
            "_folder_path_names",
            side_effect=folder_names,
        ):
            self.assertEqual(
                aio_resources._comfy_diffusion_model_names(),
                list(input_defaults.ANIMA_DEFAULT_DIFFUSION_MODEL_CANDIDATES),
            )
            self.assertEqual(
                aio_resources._comfy_text_encoder_names(),
                list(input_defaults.ANIMA_DEFAULT_CLIP_CANDIDATES),
            )
        self.assertEqual(
            folder_calls,
            [
                (
                    "diffusion_models",
                    list(input_defaults.ANIMA_DEFAULT_DIFFUSION_MODEL_CANDIDATES),
                ),
                (
                    "text_encoders",
                    list(input_defaults.ANIMA_DEFAULT_CLIP_CANDIDATES),
                ),
            ],
        )

    def test_adapter_modules_remain_below_production_module_loc_guidance(self):
        for path in (
            ROOT / "easyuse_anima" / "infrastructure" / "comfy" / "capabilities.py",
            ROOT / "easyuse_anima" / "infrastructure" / "comfy" / "resources.py",
            ROOT / "easyuse_anima" / "infrastructure" / "comfy" / "invocation.py",
        ):
            with self.subTest(path=path.name):
                self.assertLessEqual(len(path.read_text(encoding="utf-8").splitlines()), 400)


if __name__ == "__main__":
    unittest.main()
