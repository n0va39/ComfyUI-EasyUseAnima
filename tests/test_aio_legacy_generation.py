from __future__ import annotations

import copy
import inspect
import json
import sys
import unittest
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import nodes
from easyuse_anima.aio import legacy_generation
from easyuse_anima.nodes import aio_nodes
from tests.comfy_host_fakes import patch_comfy_helper
from tests.test_node_contracts import _loaded_package_entrypoint

ROOT = Path(__file__).resolve().parents[1]
TRACE_FIXTURE_PATH = ROOT / "tests" / "fixtures" / "aio_legacy_execution_trace.v1.json"


class _Token:
    def __init__(self, name: str):
        self.name = name


class AIOGeneratorLegacyMoveTests(unittest.TestCase):
    def test_normalized_legacy_adapter_forwards_exactly_to_canonical_pipeline(self):
        expected = object()
        generator = object()
        context = {"prompt_data": {}}
        settings = {"mode": "txt2img"}

        with patch.object(
            legacy_generation,
            "_run_aio_generation_pipeline",
            return_value=expected,
        ) as run:
            actual = legacy_generation._run_aio_normalized_legacy_generation(
                generator,
                context,
                settings,
                "lora",
                "workflow",
                "pnginfo",
                "node-id",
            )

        self.assertIs(actual, expected)
        run.assert_called_once_with(
            generator,
            context,
            settings,
            "lora",
            "workflow",
            "pnginfo",
            "node-id",
        )

    def test_current_normalized_settings_enter_typed_stage_boundary_before_resources(self):
        settings = nodes._normalize_aio_generation_settings("{}")

        with patch.object(
            legacy_generation,
            "_load_aio_resources_from_input_context",
            side_effect=RuntimeError("resource boundary"),
        ):
            with self.assertRaisesRegex(RuntimeError, "resource boundary"):
                legacy_generation._run_aio_normalized_legacy_generation(
                    object(),
                    {"prompt_data": {}},
                    settings,
                )

    def test_private_implementation_aliases_are_canonical_in_both_import_modes(self):
        self.assertEqual(legacy_generation.__all__, ())
        self.assertIs(
            nodes._run_aio_legacy_generation,
            legacy_generation._run_aio_legacy_generation,
        )
        self.assertIs(
            nodes._run_aio_resshift_upscale_stage,
            legacy_generation._run_aio_resshift_upscale_stage,
        )
        self.assertIs(
            nodes._run_aio_detailer_stage,
            legacy_generation._run_aio_detailer_stage,
        )
        self.assertIs(
            nodes._run_aio_detailer_target,
            legacy_generation._run_aio_detailer_target,
        )
        self.assertIs(
            nodes._run_aio_highres_stage,
            legacy_generation._run_aio_highres_stage,
        )
        self.assertIs(
            nodes._run_aio_upscale_stage,
            legacy_generation._run_aio_upscale_stage,
        )
        self.assertIs(
            nodes._run_aio_usdu_upscale_stage,
            legacy_generation._run_aio_usdu_upscale_stage,
        )

        with _loaded_package_entrypoint() as (package_entrypoint, package_nodes):
            canonical_module = sys.modules[
                f"{package_entrypoint.__name__}.easyuse_anima.aio.legacy_generation"
            ]
            self.assertIs(
                package_nodes._run_aio_legacy_generation,
                canonical_module._run_aio_legacy_generation,
            )
            self.assertIs(
                package_nodes._run_aio_resshift_upscale_stage,
                canonical_module._run_aio_resshift_upscale_stage,
            )
            self.assertIs(
                package_nodes._run_aio_detailer_stage,
                canonical_module._run_aio_detailer_stage,
            )
            self.assertIs(
                package_nodes._run_aio_detailer_target,
                canonical_module._run_aio_detailer_target,
            )
            self.assertIs(
                package_nodes._run_aio_highres_stage,
                canonical_module._run_aio_highres_stage,
            )
            self.assertIs(
                package_nodes._run_aio_upscale_stage,
                canonical_module._run_aio_upscale_stage,
            )
            self.assertIs(
                package_nodes._run_aio_usdu_upscale_stage,
                canonical_module._run_aio_usdu_upscale_stage,
            )

    def test_highres_stage_disabled_short_circuits_after_as_bool(self):
        trace: list[str] = []
        image = object()
        base_latent = object()

        with patch.object(
            legacy_generation,
            "_as_bool",
            side_effect=lambda value, default: trace.append("as_bool") or False,
        ):
            result = nodes._run_aio_highres_stage(
                object(),
                object(),
                object(),
                object(),
                object(),
                image,
                base_latent,
                "64",
                "96",
                {},
                {"enabled": False},
            )

        self.assertIs(result[0], base_latent)
        self.assertIs(result[1], image)
        self.assertEqual(result[2:], (64, 96, {"enabled": False}))
        self.assertEqual(trace, ["as_bool"])

    def test_highres_stage_preserves_dependency_and_metadata_order(self):
        trace: list[str] = []
        model = _Token("model")
        stage_model = _Token("stage_model")
        clip = _Token("clip")
        vae = _Token("vae")
        positive = _Token("positive")
        negative = _Token("negative")
        image = _Token("image")
        scaled_image = _Token("scaled_image")
        initial_latent = _Token("initial_latent")
        sampled_latent = _Token("sampled_latent")
        decoded_image = _Token("decoded_image")
        resized_image = _Token("resized_image")
        resized_latent = _Token("resized_latent")
        stage_sampler = {"backend": "comfy_ksampler", "steps": 9}
        test_case = self

        def as_bool(value, default):
            trace.append("call:_as_bool")
            self.assertEqual((value, default), (True, False))
            return True

        def stage_sampler_settings(base, highres, **kwargs):
            trace.append("call:_aio_stage_sampler_settings")
            self.assertEqual(base, {"steps": 20})
            self.assertEqual(highres["enabled"], True)
            self.assertEqual(
                kwargs,
                {"scheduler_default": "simple", "inherit_backend": True},
            )
            return stage_sampler

        class ScaleByMultiple:
            def __init__(self):
                trace.append("construct:scaler")

            def upscale(self, *args):
                trace.append("call:upscale")
                test_case.assertEqual(args, (image, 1.5, "lanczos", "64", 2048))
                return scaled_image, 128, 192, 1.5

        def encode(source_vae, source_image):
            trace.append(f"call:encode:{source_image.name}")
            self.assertIs(source_vae, vae)
            if source_image is scaled_image:
                return initial_latent
            self.assertIs(source_image, resized_image)
            return resized_latent

        def apply_patch(source_model, source_clip, conditioning, sampler):
            trace.append("call:patch")
            self.assertEqual(
                (source_model, source_clip, conditioning, sampler),
                (model, clip, positive, stage_sampler),
            )
            return stage_model

        def sample(*args):
            trace.append("call:sample")
            self.assertEqual(
                args,
                (
                    stage_model,
                    clip,
                    positive,
                    negative,
                    initial_latent,
                    stage_sampler,
                    {"scale": 3.0},
                    True,
                    "quality",
                    "quality-neg",
                ),
            )
            return sampled_latent

        def cleanup(current_model, original_model):
            trace.append("call:cleanup")
            self.assertEqual((current_model, original_model), (stage_model, model))

        def decode(source_vae, latent):
            trace.append("call:decode")
            self.assertEqual((source_vae, latent), (vae, sampled_latent))
            return decoded_image

        def resize(source_image, width, height, method):
            trace.append("call:resize")
            self.assertEqual(
                (source_image, width, height, method),
                (decoded_image, 128, 192, "lanczos"),
            )
            return resized_image, True

        def json_safe(value):
            trace.append("call:json_safe")
            self.assertIs(value, stage_sampler)
            return {"backend": value["backend"], "steps": value["steps"]}

        helpers = {
            "_as_bool": as_bool,
            "_aio_stage_sampler_settings": stage_sampler_settings,
            "EasyUseAnimaImageScaleByMultiple": ScaleByMultiple,
            "_encode_image_with_comfy_vae": encode,
            "_apply_aio_spectrum_model_patches_for_comfy_sampler": apply_patch,
            "_sample_latent_with_aio_backend": sample,
            "_cleanup_aio_ephemeral_model": cleanup,
            "_decode_latent_with_comfy": decode,
            "_resize_image_to_size_if_needed": resize,
            "_prompt_data_json_safe": json_safe,
        }

        with patch.multiple(legacy_generation, **helpers):
            result = nodes._run_aio_highres_stage(
                model,
                clip,
                vae,
                positive,
                negative,
                image,
                object(),
                64,
                96,
                {"steps": 20},
                {
                    "enabled": True,
                    "scale_by": 1.5,
                    "upscale_method": "lanczos",
                    "multiple": "64",
                    "max_long_edge": 2048,
                },
                {"scale": 3.0},
                True,
                "quality",
                "quality-neg",
            )

        self.assertEqual(
            result,
            (
                resized_latent,
                resized_image,
                128,
                192,
                {
                    "enabled": True,
                    "width": 128,
                    "height": 192,
                    "applied_scale": 1.5,
                    "sampler": {"backend": "comfy_ksampler", "steps": 9},
                },
            ),
        )
        self.assertEqual(
            trace,
            [
                "call:_as_bool",
                "call:_aio_stage_sampler_settings",
                "construct:scaler",
                "call:upscale",
                "call:encode:scaled_image",
                "call:patch",
                "call:sample",
                "call:cleanup",
                "call:decode",
                "call:resize",
                "call:encode:resized_image",
                "call:json_safe",
            ],
        )

    def test_highres_stage_sampling_failure_cleans_original_model_boundary(self):
        trace: list[str] = []
        model = _Token("model")
        stage_sampler = {"backend": "spectrum_mod_guidance_advanced"}

        class ScaleByMultiple:
            def upscale(self, *args):
                trace.append("upscale")
                return _Token("scaled"), 64, 96, 1.0

        def sample(*args):
            trace.append("sample")
            raise RuntimeError("sample failed")

        def cleanup(current_model, original_model):
            trace.append("cleanup")
            self.assertIs(current_model, model)
            self.assertIs(original_model, model)

        helpers = {
            "_as_bool": lambda value, default: True,
            "_aio_stage_sampler_settings": lambda *args, **kwargs: stage_sampler,
            "EasyUseAnimaImageScaleByMultiple": ScaleByMultiple,
            "_encode_image_with_comfy_vae": lambda vae, image: _Token("latent"),
            "_sample_latent_with_aio_backend": sample,
            "_cleanup_aio_ephemeral_model": cleanup,
        }

        with patch.multiple(legacy_generation, **helpers):
            with self.assertRaisesRegex(RuntimeError, "sample failed"):
                nodes._run_aio_highres_stage(
                    model,
                    object(),
                    object(),
                    object(),
                    object(),
                    object(),
                    object(),
                    64,
                    96,
                    {},
                    {"enabled": True},
                )

        self.assertEqual(
            trace[-2:],
            [
                "sample",
                "cleanup",
            ],
        )

    def test_detailer_stage_preserves_lazy_filter_and_no_target_short_circuits(self):
        image = _Token("image")

        def execute(detailer_settings, target_order):
            trace = []

            def as_bool(value, default):
                trace.append(("call", "_as_bool", value, default))
                return bool(value)

            helpers = {
                "_as_bool": as_bool,
                "_aio_detailer_target_order": lambda settings: (
                    trace.append(("call", "_aio_detailer_target_order"))
                    or target_order
                ),
            }

            with patch.multiple(legacy_generation, **helpers):
                result = nodes._run_aio_detailer_stage(
                    object(),
                    object(),
                    object(),
                    object(),
                    object(),
                    image,
                    {},
                    detailer_settings,
                )
            return result, trace

        disabled_result, disabled_trace = execute({"enabled": False}, [])
        self.assertIs(disabled_result[0], image)
        self.assertEqual(disabled_result[1], {"enabled": False})
        self.assertEqual(
            disabled_trace,
            [
                ("call", "_as_bool", False, False),
            ],
        )

        no_target_result, no_target_trace = execute(
            {
                "enabled": True,
                "face": {"enabled": False},
                "missing": "not-a-dict",
            },
            ["face", "missing"],
        )
        self.assertIs(no_target_result[0], image)
        self.assertEqual(
            no_target_result[1],
            {"enabled": False, "reason": "no target enabled"},
        )
        self.assertEqual(
            no_target_trace,
            [
                ("call", "_as_bool", True, False),
                ("call", "_aio_detailer_target_order"),
                ("call", "_as_bool", False, False),
            ],
        )

    def test_detailer_stage_preserves_order_chaining_callback_and_metadata(self):
        trace = []
        model = _Token("model")
        clip = _Token("clip")
        vae = _Token("vae")
        positive = _Token("positive")
        negative = _Token("negative")
        image = _Token("image")
        eye_image = _Token("eye_image")
        face_image = _Token("face_image")
        sampler_settings = {"seed": 17}
        detailer_settings = {
            "enabled": True,
            "eye": {"enabled": True},
            "disabled": {"enabled": False},
            "missing": "not-a-dict",
            "face": {"enabled": True},
        }
        target_order = ["eye", "disabled", "missing", "face"]
        sam3_context = {"ckpt_name": "sam3.safetensors"}
        eye_metadata = {"enabled": True, "target": "eye"}
        face_metadata = {"enabled": True, "target": "face"}

        def as_bool(value, default):
            trace.append(("call", "_as_bool", value, default))
            return bool(value)

        def target_order_helper(settings):
            trace.append(("call", "_aio_detailer_target_order"))
            self.assertIs(settings, detailer_settings)
            return target_order

        def load_context(settings):
            trace.append(("call", "_load_aio_sam3_context"))
            self.assertIs(settings, detailer_settings)
            return sam3_context

        def run_target(*args):
            target_name = args[0]
            trace.append(("call", "_run_aio_detailer_target", target_name))
            expected_image = image if target_name == "eye" else eye_image
            self.assertEqual(
                args,
                (
                    target_name,
                    detailer_settings[target_name],
                    expected_image,
                    model,
                    clip,
                    vae,
                    positive,
                    negative,
                    sampler_settings,
                    sam3_context,
                ),
            )
            if target_name == "eye":
                return eye_image, eye_metadata
            return face_image, face_metadata

        def context_value(context, key):
            trace.append(("call", "_context_value", key))
            self.assertIs(context, sam3_context)
            return context[key]

        helpers = {
            "_as_bool": as_bool,
            "_aio_detailer_target_order": target_order_helper,
            "_load_aio_sam3_context": load_context,
            "_run_aio_detailer_target": run_target,
            "_context_value": context_value,
        }

        def preview(stage, output):
            trace.append(("callback", stage, output.name))

        with patch.multiple(legacy_generation, **helpers):
            result = nodes._run_aio_detailer_stage(
                model,
                clip,
                vae,
                positive,
                negative,
                image,
                sampler_settings,
                detailer_settings,
                preview,
            )

        self.assertIs(result[0], face_image)
        self.assertIs(result[1]["order"], target_order)
        self.assertIs(result[1]["targets"]["eye"], eye_metadata)
        self.assertIs(result[1]["targets"]["face"], face_metadata)
        self.assertEqual(
            result[1],
            {
                "enabled": True,
                "sam3_checkpoint": "sam3.safetensors",
                "order": target_order,
                "targets": {"eye": eye_metadata, "face": face_metadata},
            },
        )
        self.assertEqual(
            trace,
            [
                ("call", "_as_bool", True, False),
                ("call", "_aio_detailer_target_order"),
                ("call", "_as_bool", True, False),
                ("call", "_as_bool", False, False),
                ("call", "_as_bool", True, False),
                ("call", "_load_aio_sam3_context"),
                ("call", "_run_aio_detailer_target", "eye"),
                ("callback", "detailer_eye", "eye_image"),
                ("call", "_run_aio_detailer_target", "face"),
                ("callback", "detailer_face", "face_image"),
                ("call", "_context_value", "ckpt_name"),
            ],
        )

    def test_detailer_stage_propagates_target_and_callback_failures_in_place(self):
        detailer_settings = {
            "enabled": True,
            "eye": {"enabled": True},
            "face": {"enabled": True},
        }

        def execute(run_target, preview_callback, trace):
            helpers = {
                "_as_bool": lambda value, default: bool(value),
                "_aio_detailer_target_order": lambda settings: ["eye", "face"],
                "_load_aio_sam3_context": lambda settings: {},
                "_run_aio_detailer_target": run_target(trace),
                "_context_value": lambda context, key: trace.append("context_value"),
            }

            with patch.multiple(legacy_generation, **helpers):
                nodes._run_aio_detailer_stage(
                    object(),
                    object(),
                    object(),
                    object(),
                    object(),
                    _Token("image"),
                    {},
                    detailer_settings,
                    preview_callback(trace),
                )
            return trace

        def failing_target(trace):
            def run(target_name, *args):
                trace.append(f"target:{target_name}")
                raise ValueError("target failed")

            return run

        target_trace = []
        with self.assertRaisesRegex(ValueError, "target failed"):
            execute(
                failing_target,
                lambda trace: lambda *args: trace.append("preview"),
                target_trace,
            )
        self.assertEqual(
            target_trace[-1:],
            ["target:eye"],
        )
        self.assertNotIn("preview", target_trace)
        self.assertNotIn("target:face", target_trace)
        self.assertNotIn("context_value", target_trace)

        def short_target(trace):
            def run(target_name, *args):
                trace.append(f"target:{target_name}")
                return (_Token("only_value"),)

            return run

        unpack_trace = []
        with self.assertRaisesRegex(ValueError, "not enough values to unpack"):
            execute(
                short_target,
                lambda trace: lambda *args: trace.append("preview"),
                unpack_trace,
            )
        self.assertEqual(
            unpack_trace[-1:],
            ["target:eye"],
        )
        self.assertNotIn("preview", unpack_trace)
        self.assertNotIn("target:face", unpack_trace)
        self.assertNotIn("context_value", unpack_trace)

        def successful_target(trace):
            def run(target_name, *args):
                trace.append(f"target:{target_name}")
                return _Token(f"{target_name}_image"), {"target": target_name}

            return run

        def failing_preview(trace):
            def preview(*args):
                trace.append("preview:eye")
                raise LookupError("preview failed")

            return preview

        callback_trace = []
        with self.assertRaisesRegex(LookupError, "preview failed"):
            execute(successful_target, failing_preview, callback_trace)
        self.assertEqual(
            callback_trace[-3:],
            [
                "target:eye",
                "preview:eye",
            ],
        )
        self.assertNotIn("target:face", callback_trace)
        self.assertNotIn("context_value", callback_trace)

    def test_detailer_target_disabled_short_circuits_after_as_bool(self):
        trace: list[str] = []
        image = object()

        with patch.object(
            legacy_generation,
            "_as_bool",
            side_effect=lambda value, default: trace.append("call:_as_bool") or False,
        ):
            result = nodes._run_aio_detailer_target(
                "face",
                {"enabled": False},
                image,
                object(),
                object(),
                object(),
                object(),
                object(),
                {},
                {},
            )

        self.assertIs(result[0], image)
        self.assertEqual(result[1], {"enabled": False})
        self.assertEqual(trace, ["call:_as_bool"])

    def test_detailer_target_preserves_kwargs_cleanup_and_metadata_order(self):
        trace: list[str] = []
        captured_kwargs = {}
        model = _Token("model")
        stage_model = _Token("stage_model")
        clip = _Token("clip")
        vae = _Token("vae")
        positive = _Token("positive")
        negative = _Token("negative")
        image = _Token("image")
        detailed_image = _Token("detailed_image")
        sam3_context = {"model": _Token("sam3_model")}
        segs = ((1, 1), ["seg"])
        sampler_settings = {"seed": 11}
        stage_sampler = {
            "seed": 101,
            "steps": 22,
            "cfg": 6.5,
            "sampler_name": "euler",
            "scheduler": "sgm_uniform",
            "denoise": 0.31,
        }
        target_settings = {
            "enabled": True,
            "detect_prompt": "portrait face",
            "detect_count": "2",
            "threshold": "0.63",
            "refine_iterations": "3",
            "individual_masks": True,
            "combined": False,
            "crop_factor": "3.5",
            "bbox_fill": True,
            "drop_size": "88",
            "contour_fill": False,
            "guide_size": "896",
            "guide_size_for": True,
            "max_size": "1792",
            "feather": "7",
            "noise_mask": False,
            "force_inpaint": True,
            "wildcard": "detail wildcard",
            "cycle": "2",
            "alignment": "64",
            "inpaint_model": True,
            "noise_mask_feather": "4",
            "tiled_encode": True,
            "tiled_decode": False,
        }

        def as_bool(value, default):
            trace.append(("call", "_as_bool", value, default))
            return bool(value)

        def as_int(value, default):
            trace.append(("call", "_as_int", value, default))
            return int(value)

        def as_float(value, default):
            trace.append(("call", "_as_float", value, default))
            return float(value)

        def stage_sampler_settings(base, target, **kwargs):
            trace.append("call:_aio_stage_sampler_settings")
            self.assertIs(base, sampler_settings)
            self.assertIs(target, target_settings)
            self.assertEqual(kwargs, {"scheduler_default": "sgm_uniform"})
            return stage_sampler

        def apply_patch(source_model, source_clip, conditioning, sampler):
            trace.append("call:_apply_patch")
            self.assertEqual(
                (source_model, source_clip, conditioning, sampler),
                (model, clip, positive, stage_sampler),
            )
            return stage_model

        class Detailer:
            def __init__(self):
                trace.append("construct:detailer")

            def doit(self, **kwargs):
                trace.append("call:doit")
                captured_kwargs.update(kwargs)
                return detailed_image, segs, object(), object()

        def cleanup(current_model, original_model):
            trace.append("call:cleanup")
            self.assertEqual((current_model, original_model), (stage_model, model))

        def segs_has_items(value):
            trace.append("call:_segs_has_items")
            self.assertIs(value, segs)
            return True

        safe_sampler = {"safe": True}

        def json_safe(value):
            trace.append("call:_prompt_data_json_safe")
            self.assertIs(value, stage_sampler)
            return safe_sampler

        helpers = {
            "_as_bool": as_bool,
            "_as_int": as_int,
            "_as_float": as_float,
            "_aio_stage_sampler_settings": stage_sampler_settings,
            "_apply_aio_spectrum_model_patches_for_comfy_sampler": apply_patch,
            "EasyUseAnimaSAM3Detailer": Detailer,
            "_cleanup_aio_ephemeral_model": cleanup,
            "_segs_has_items": segs_has_items,
            "_prompt_data_json_safe": json_safe,
        }

        with patch.multiple(legacy_generation, **helpers):
            result = nodes._run_aio_detailer_target(
                "face",
                target_settings,
                image,
                model,
                clip,
                vae,
                positive,
                negative,
                sampler_settings,
                sam3_context,
            )

        self.assertIs(result[0], detailed_image)
        self.assertEqual(
            result[1],
            {"enabled": True, "detected": True, "sampler": safe_sampler},
        )
        self.assertEqual(list(result[1]), ["enabled", "detected", "sampler"])
        self.assertIs(result[1]["sampler"], safe_sampler)
        self.assertEqual(
            list(captured_kwargs),
            [
                "enabled", "image", "ctx_SAM3", "detect_prompt", "detect_count",
                "threshold", "refine_iterations", "individual_masks", "combined",
                "crop_factor", "bbox_fill", "drop_size", "contour_fill", "model",
                "clip", "vae", "guide_size", "guide_size_for", "max_size", "seed",
                "steps", "cfg", "sampler_name", "scheduler", "positive", "negative",
                "denoise", "feather", "noise_mask", "force_inpaint", "wildcard",
                "cycle", "alignment", "preserve_conditioning_metadata",
                "fail_on_unsupported_opt", "detailer_hook", "inpaint_model",
                "noise_mask_feather", "scheduler_func_opt", "tiled_encode",
                "tiled_decode",
            ],
        )
        self.assertEqual(
            captured_kwargs,
            {
                "enabled": True,
                "image": image,
                "ctx_SAM3": sam3_context,
                "detect_prompt": "portrait face",
                "detect_count": 2,
                "threshold": 0.63,
                "refine_iterations": 3,
                "individual_masks": True,
                "combined": False,
                "crop_factor": 3.5,
                "bbox_fill": True,
                "drop_size": 88,
                "contour_fill": False,
                "model": stage_model,
                "clip": clip,
                "vae": vae,
                "guide_size": 896,
                "guide_size_for": True,
                "max_size": 1792,
                "seed": 101,
                "steps": 22,
                "cfg": 6.5,
                "sampler_name": "euler",
                "scheduler": "sgm_uniform",
                "positive": positive,
                "negative": negative,
                "denoise": 0.31,
                "feather": 7,
                "noise_mask": False,
                "force_inpaint": True,
                "wildcard": "detail wildcard",
                "cycle": 2,
                "alignment": "64",
                "preserve_conditioning_metadata": True,
                "fail_on_unsupported_opt": False,
                "detailer_hook": None,
                "inpaint_model": True,
                "noise_mask_feather": 4,
                "scheduler_func_opt": None,
                "tiled_encode": True,
                "tiled_decode": False,
            },
        )
        self.assertLess(trace.index("call:cleanup"), trace.index("call:_segs_has_items"))
        self.assertLess(
            trace.index("call:_segs_has_items"),
            trace.index("call:_prompt_data_json_safe"),
        )

    def test_detailer_target_preserves_cleanup_and_metadata_failure_boundaries(self):
        image = _Token("image")
        model = _Token("model")
        stage_model = _Token("stage_model")
        stage_sampler = {
            "seed": 1,
            "steps": 2,
            "cfg": 3.0,
            "sampler_name": "euler",
            "scheduler": "sgm_uniform",
            "denoise": 0.4,
        }

        def execute(overrides, trace):
            class Detailer:
                def doit(self, **kwargs):
                    trace.append("doit")
                    return _Token("output"), ((1, 1), ["seg"])

            helpers = {
                "_as_bool": lambda value, default: bool(value),
                "_as_int": lambda value, default: default,
                "_as_float": lambda value, default: default,
                "_aio_stage_sampler_settings": lambda *args, **kwargs: stage_sampler,
                "_apply_aio_spectrum_model_patches_for_comfy_sampler": (
                    lambda *args: stage_model
                ),
                "EasyUseAnimaSAM3Detailer": Detailer,
                "_cleanup_aio_ephemeral_model": (
                    lambda current, original: trace.append("cleanup")
                ),
                "_segs_has_items": lambda value: True,
                "_prompt_data_json_safe": lambda value: value,
                **overrides,
            }

            with patch.multiple(legacy_generation, **helpers):
                return nodes._run_aio_detailer_target(
                    "face",
                    {"enabled": True},
                    image,
                    model,
                    object(),
                    object(),
                    object(),
                    object(),
                    {},
                    {},
                )

        planner_trace = []

        def fail_planner(*args, **kwargs):
            planner_trace.append("planner")
            raise ValueError("planner failed")

        with self.assertRaisesRegex(ValueError, "planner failed"):
            execute({"_aio_stage_sampler_settings": fail_planner}, planner_trace)
        self.assertNotIn("cleanup", planner_trace)

        class_trace = []

        def fail_class():
            class_trace.append("construct")
            raise LookupError("class failed")

        with self.assertRaisesRegex(LookupError, "class failed"):
            execute({"EasyUseAnimaSAM3Detailer": fail_class}, class_trace)
        self.assertEqual(class_trace[-1:], ["cleanup"])

        cleanup_trace = []

        class FailingDetailer:
            def doit(self, **kwargs):
                cleanup_trace.append("doit")
                raise ValueError("detailer failed")

        def fail_cleanup(current, original):
            cleanup_trace.append("cleanup")
            raise RuntimeError("cleanup failed")

        with self.assertRaisesRegex(RuntimeError, "cleanup failed"):
            execute(
                {
                    "EasyUseAnimaSAM3Detailer": FailingDetailer,
                    "_cleanup_aio_ephemeral_model": fail_cleanup,
                },
                cleanup_trace,
            )
        self.assertEqual(cleanup_trace[-2:], ["doit", "cleanup"])

        metadata_trace = []

        def fail_segs(value):
            metadata_trace.append("segs")
            raise ArithmeticError("segs failed")

        with self.assertRaisesRegex(ArithmeticError, "segs failed"):
            execute({"_segs_has_items": fail_segs}, metadata_trace)
        self.assertIn("cleanup", metadata_trace)
        self.assertEqual(metadata_trace[-1:], ["segs"])

    def test_usdu_stage_preserves_dependencies_kwargs_cleanup_and_metadata_order(self):
        trace = []
        captured_kwargs = {}
        model = _Token("model")
        stage_model = _Token("stage_model")
        clip = _Token("clip")
        vae = _Token("vae")
        positive = _Token("positive")
        negative = _Token("negative")
        usdu_positive = _Token("usdu_positive")
        usdu_negative = _Token("usdu_negative")
        image = _Token("image")
        output = _Token("output")
        upscale_model = _Token("upscale_model")
        sampler_settings = {"seed": "base-seed"}
        stage_sampler = {
            "seed": "stage-seed",
            "steps": "30",
            "cfg": "5.5",
            "sampler_name": "dpmpp_2m",
            "scheduler": "simple",
            "denoise": "0.25",
        }
        usdu_settings = {
            "upscale_model_name": "upscale.safetensors",
            "mode_type": "Chess",
            "mask_blur": "9",
            "tile_padding": "48",
            "seam_fix_mode": "Band Pass",
            "seam_fix_denoise": "0.8",
            "seam_fix_mask_blur": "7",
            "seam_fix_width": "80",
            "seam_fix_padding": "20",
            "force_uniform_tiles": True,
            "tiled_decode": False,
            "batch_size": "3",
            "prompt_mode": "no_general",
        }
        upscale_settings = {"scale_by": "2.5", "usdu": usdu_settings}
        tile_plan = {
            "auto": True,
            "input_width": 512,
            "input_height": 768,
            "target_width": 1280,
            "target_height": 1920,
            "preferred": 768,
            "min": 512,
            "max": 1536,
            "tile_width": 640,
            "tile_height": 960,
        }
        safe_sampler = {"safe": True}

        class Logger:
            def info(self, *args):
                trace.append(("call", "logger.info", args))

        class USDU:
            def __init__(self):
                trace.append("construct:usdu")

            def upscale(self, **kwargs):
                trace.append("call:upscale")
                captured_kwargs.update(kwargs)
                return "raw-usdu-result"

        def require(node_id, node_pack, install_hint):
            trace.append("call:_require_custom_node_class")
            self.assertEqual(
                (node_id, node_pack, install_hint),
                (
                    "UltimateSDUpscale",
                    "ComfyUI_UltimateSDUpscale",
                    "Required for AiO Generator final Upscale > USDU.",
                ),
            )
            return USDU

        def load_upscale(name):
            trace.append("call:_load_upscale_model_with_comfy")
            self.assertEqual(name, "upscale.safetensors")
            return upscale_model

        def stage_sampler_settings(base, stage, **kwargs):
            trace.append("call:_aio_stage_sampler_settings")
            self.assertIs(base, sampler_settings)
            self.assertIs(stage, upscale_settings)
            self.assertEqual(kwargs, {"scheduler_default": "simple"})
            return stage_sampler

        def as_int(value, default):
            trace.append(("call", "_as_int", value, default))
            return int(value)

        def as_float(value, default):
            trace.append(("call", "_as_float", value, default))
            return float(value)

        def as_bool(value, default):
            trace.append(("call", "_as_bool", value, default))
            return bool(value)

        def plan_tiles(source_image, scale, settings):
            trace.append("call:_aio_usdu_tile_plan")
            self.assertEqual((source_image, scale, settings), (image, 2.5, usdu_settings))
            return tile_plan

        def conditioning(*args):
            trace.append("call:_aio_usdu_conditioning")
            self.assertEqual(
                args,
                (
                    clip,
                    positive,
                    negative,
                    usdu_settings,
                    "quality",
                    "quality-neg",
                    {"fields": []},
                    True,
                    False,
                ),
            )
            return usdu_positive, usdu_negative

        def apply_patch(source_model, source_clip, conditioning_value, sampler):
            trace.append("call:_apply_patch")
            self.assertEqual(
                (source_model, source_clip, conditioning_value, sampler),
                (model, clip, usdu_positive, stage_sampler),
            )
            return stage_model

        def resolve_seed(value):
            trace.append("call:_resolve_aio_runtime_seed")
            self.assertEqual(value, "stage-seed")
            return 123

        def cleanup(current_model, original_model):
            trace.append("call:cleanup")
            self.assertEqual((current_model, original_model), (stage_model, model))

        def output_tuple(value):
            trace.append("call:_node_output_tuple")
            self.assertEqual(value, "raw-usdu-result")
            return (output,)

        def image_size(value, fallback_width, fallback_height):
            trace.append("call:_image_tensor_size")
            self.assertEqual((value, fallback_width, fallback_height), (output, 0, 0))
            return 1280, 1920

        def json_safe(value):
            trace.append("call:_prompt_data_json_safe")
            self.assertIs(value, stage_sampler)
            return safe_sampler

        helpers = {
            "_require_custom_node_class": require,
            "_load_upscale_model_with_comfy": load_upscale,
            "_aio_stage_sampler_settings": stage_sampler_settings,
            "_as_int": as_int,
            "_as_float": as_float,
            "_as_bool": as_bool,
            "_aio_usdu_tile_plan": plan_tiles,
            "logger": Logger(),
            "_aio_usdu_conditioning": conditioning,
            "_apply_aio_spectrum_model_patches_for_comfy_sampler": apply_patch,
            "_resolve_aio_runtime_seed": resolve_seed,
            "_cleanup_aio_ephemeral_model": cleanup,
            "_node_output_tuple": output_tuple,
            "_image_tensor_size": image_size,
            "_prompt_data_json_safe": json_safe,
        }

        with patch.multiple(legacy_generation, **helpers):
            result = nodes._run_aio_usdu_upscale_stage(
                model,
                clip,
                vae,
                positive,
                negative,
                image,
                sampler_settings,
                upscale_settings,
                "quality",
                "quality-neg",
                {"fields": []},
                True,
                False,
            )

        self.assertIs(result[0], output)
        self.assertEqual(
            result[1],
            {
                "enabled": True,
                "backend": "usdu",
                "width": 1280,
                "height": 1920,
                "scale_by": 2.5,
                "tile_width": 640,
                "tile_height": 960,
                "tile_auto": True,
                "tile_target_width": 1280,
                "tile_target_height": 1920,
                "prompt_mode": "no_general",
                "sampler": safe_sampler,
            },
        )
        self.assertEqual(
            list(result[1]),
            [
                "enabled", "backend", "width", "height", "scale_by",
                "tile_width", "tile_height", "tile_auto", "tile_target_width",
                "tile_target_height", "prompt_mode", "sampler",
            ],
        )
        self.assertEqual(
            list(captured_kwargs),
            [
                "image", "model", "positive", "negative", "vae", "upscale_by",
                "seed", "steps", "cfg", "sampler_name", "scheduler", "denoise",
                "upscale_model", "mode_type", "tile_width", "tile_height",
                "mask_blur", "tile_padding", "seam_fix_mode", "seam_fix_denoise",
                "seam_fix_mask_blur", "seam_fix_width", "seam_fix_padding",
                "force_uniform_tiles", "tiled_decode", "batch_size",
            ],
        )
        self.assertEqual(
            captured_kwargs,
            {
                "image": image,
                "model": stage_model,
                "positive": usdu_positive,
                "negative": usdu_negative,
                "vae": vae,
                "upscale_by": 2.5,
                "seed": 123,
                "steps": 30,
                "cfg": 5.5,
                "sampler_name": "dpmpp_2m",
                "scheduler": "simple",
                "denoise": 0.25,
                "upscale_model": upscale_model,
                "mode_type": "Chess",
                "tile_width": 640,
                "tile_height": 960,
                "mask_blur": 9,
                "tile_padding": 48,
                "seam_fix_mode": "Band Pass",
                "seam_fix_denoise": 0.8,
                "seam_fix_mask_blur": 7,
                "seam_fix_width": 80,
                "seam_fix_padding": 20,
                "force_uniform_tiles": True,
                "tiled_decode": False,
                "batch_size": 3,
            },
        )
        log_calls = [item for item in trace if isinstance(item, tuple) and item[:2] == ("call", "logger.info")]
        self.assertEqual(len(log_calls), 2)
        self.assertIn("USDU auto tile", log_calls[0][2][0])
        self.assertIn("USDU sampler", log_calls[1][2][0])
        self.assertLess(trace.index("call:cleanup"), trace.index("call:_node_output_tuple"))

    def test_usdu_stage_preserves_cleanup_output_and_lazy_default_boundaries(self):
        model = _Token("model")
        stage_model = _Token("stage_model")
        output = _Token("output")
        stage_sampler = {
            "seed": 1,
            "steps": 2,
            "cfg": 3.0,
            "sampler_name": "euler",
            "scheduler": "simple",
            "denoise": 0.4,
        }

        class Logger:
            def info(self, *args):
                return None

        class USDU:
            def upscale(self, **kwargs):
                return "raw-result"

        def execute(overrides, trace):
            helpers = {
                "_require_custom_node_class": lambda *args: USDU,
                "_load_upscale_model_with_comfy": lambda name: object(),
                "_aio_stage_sampler_settings": lambda *args, **kwargs: stage_sampler,
                "_as_float": lambda value, default: default,
                "_as_int": lambda value, default: default,
                "_as_bool": lambda value, default: default,
                "_aio_usdu_tile_plan": lambda *args: {
                    "auto": False,
                    "tile_width": 512,
                    "tile_height": 512,
                },
                "logger": Logger(),
                "_aio_usdu_conditioning": lambda *args: (object(), object()),
                "_apply_aio_spectrum_model_patches_for_comfy_sampler": (
                    lambda *args: stage_model
                ),
                "_resolve_aio_runtime_seed": lambda value: 1,
                "_cleanup_aio_ephemeral_model": (
                    lambda current, original: trace.append("cleanup")
                ),
                "_node_output_tuple": lambda value: (output,),
                "_image_tensor_size": lambda *args: (1024, 1024),
                "AIO_USDU_PROMPT_FULL": "full",
                "_prompt_data_json_safe": lambda value: {"safe": True},
                **overrides,
            }

            with patch.multiple(legacy_generation, **helpers):
                return nodes._run_aio_usdu_upscale_stage(
                    model,
                    object(),
                    object(),
                    object(),
                    object(),
                    object(),
                    {},
                    {"usdu": {}},
                )

        patch_trace = []

        def fail_patch(*args):
            raise ValueError("patch failed")

        with self.assertRaisesRegex(ValueError, "patch failed"):
            execute(
                {"_apply_aio_spectrum_model_patches_for_comfy_sampler": fail_patch},
                patch_trace,
            )
        self.assertNotIn("cleanup", patch_trace)

        construct_trace = []

        class FailingConstructor:
            def __init__(self):
                construct_trace.append("construct")
                raise LookupError("constructor failed")

        with self.assertRaisesRegex(LookupError, "constructor failed"):
            execute(
                {"_require_custom_node_class": lambda *args: FailingConstructor},
                construct_trace,
            )
        self.assertEqual(construct_trace[-1:], ["cleanup"])

        cleanup_trace = []

        class FailingUSDU:
            def upscale(self, **kwargs):
                cleanup_trace.append("upscale")
                raise ValueError("upscale failed")

        def fail_cleanup(current, original):
            cleanup_trace.append("cleanup")
            raise RuntimeError("cleanup failed")

        with self.assertRaisesRegex(RuntimeError, "cleanup failed"):
            execute(
                {
                    "_require_custom_node_class": lambda *args: FailingUSDU,
                    "_cleanup_aio_ephemeral_model": fail_cleanup,
                },
                cleanup_trace,
            )
        self.assertEqual(cleanup_trace[-2:], ["upscale", "cleanup"])

        empty_trace = []
        with self.assertRaisesRegex(
            RuntimeError,
            r"^\[EasyUseAnima\] UltimateSDUpscale returned no IMAGE\.$",
        ):
            execute({"_node_output_tuple": lambda value: ()}, empty_trace)
        self.assertIn("cleanup", empty_trace)

        default_trace = []
        result = execute({}, default_trace)
        self.assertIs(result[0], output)
        self.assertEqual(result[1]["prompt_mode"], "full")

    def test_resshift_stage_preserves_provider_argument_and_metadata_order(self):
        trace = []
        image = _Token("image")
        output = _Token("output")
        model = _Token("resshift_model")
        sampler_settings = {"seed": "seed-input"}
        upscale_settings = {
            "resshift": {
                "scale": "x4",
                "student_name": "student.ckpt",
                "dtype": "fp32",
                "chop": "1024",
                "overlap": "96",
                "tile_batch": "2",
            }
        }

        class Loader:
            def __init__(self):
                trace.append("construct:loader")

            def load(self, *args):
                trace.append(("call", "load", args))
                return "loader-result"

        class Upscaler:
            def __init__(self):
                trace.append("construct:upscaler")

            def upscale(self, *args):
                trace.append(("call", "upscale", args))
                return "upscale-result"

        def require(node_id, node_pack, install_hint):
            trace.append(("call", "_require_custom_node_class", node_id))
            self.assertEqual(node_pack, "ComfyUI-Distilled-ResShift")
            self.assertEqual(
                install_hint,
                "Required for AiO Generator final Upscale > ResShift.",
            )
            return Loader if node_id == "ResShiftLoader" else Upscaler

        tuple_results = iter(((model,), (output,)))

        def node_output_tuple(value):
            trace.append(("call", "_node_output_tuple", value))
            return next(tuple_results)

        def resolve_seed(value):
            trace.append(("call", "_resolve_aio_runtime_seed", value))
            return 321

        def as_int(value, default):
            trace.append(("call", "_as_int", value, default))
            return int(value)

        def image_size(value, fallback_width, fallback_height):
            trace.append(("call", "_image_tensor_size"))
            self.assertIs(value, output)
            self.assertEqual((fallback_width, fallback_height), (0, 0))
            return 2048, 3072

        helpers = {
            "_require_custom_node_class": require,
            "_node_output_tuple": node_output_tuple,
            "_resolve_aio_runtime_seed": resolve_seed,
            "_as_int": as_int,
            "_image_tensor_size": image_size,
        }

        with patch.multiple(legacy_generation, **helpers):
            result = nodes._run_aio_resshift_upscale_stage(
                image,
                sampler_settings,
                upscale_settings,
                "unused-quality",
                "unused-negative",
                {"unused": True},
                True,
                True,
            )

        self.assertIs(result[0], output)
        self.assertEqual(
            result[1],
            {
                "enabled": True,
                "backend": "resshift",
                "width": 2048,
                "height": 3072,
                "scale": "x4",
            },
        )
        self.assertEqual(
            list(result[1]),
            ["enabled", "backend", "width", "height", "scale"],
        )
        self.assertEqual(
            trace,
            [
                ("call", "_require_custom_node_class", "ResShiftLoader"),
                ("call", "_require_custom_node_class", "ResShiftUpscale"),
                "construct:loader",
                (
                    "call",
                    "load",
                    ("x4", "student.ckpt", "fp32"),
                ),
                ("call", "_node_output_tuple", "loader-result"),
                "construct:upscaler",
                ("call", "_resolve_aio_runtime_seed", "seed-input"),
                ("call", "_as_int", "1024", 512),
                ("call", "_as_int", "96", 64),
                ("call", "_as_int", "2", 4),
                (
                    "call",
                    "upscale",
                    (model, image, 321, 1024, 96, 2),
                ),
                ("call", "_node_output_tuple", "upscale-result"),
                ("call", "_image_tensor_size"),
            ],
        )

    def test_resshift_stage_preserves_failure_boundaries(self):
        image = _Token("image")

        def execute(helpers, trace):
            with patch.multiple(legacy_generation, **helpers):
                return nodes._run_aio_resshift_upscale_stage(
                    image,
                    {"seed": 7},
                    {"resshift": {}},
                )

        first_provider_trace = []

        def fail_first_provider(*args):
            first_provider_trace.append("require:loader")
            raise LookupError("provider failed")

        with self.assertRaisesRegex(LookupError, "provider failed"):
            execute(
                {"_require_custom_node_class": fail_first_provider},
                first_provider_trace,
            )
        self.assertEqual(
            first_provider_trace,
            ["require:loader"],
        )

        missing_load_trace = []

        class MissingLoad:
            def __init__(self):
                missing_load_trace.append("construct:loader")

        class UnusedUpscaler:
            def __init__(self):
                missing_load_trace.append("construct:upscaler")

        def missing_load_provider(node_id, *args):
            missing_load_trace.append(f"require:{node_id}")
            return MissingLoad if node_id == "ResShiftLoader" else UnusedUpscaler

        with self.assertRaisesRegex(
            RuntimeError,
            r"^\[EasyUseAnima\] ResShiftLoader does not expose load\(\)\.$",
        ):
            execute(
                {"_require_custom_node_class": missing_load_provider},
                missing_load_trace,
            )
        self.assertEqual(
            missing_load_trace,
            [
                "require:ResShiftLoader",
                "require:ResShiftUpscale",
                "construct:loader",
            ],
        )

        empty_model_trace = []

        class EmptyLoader:
            def load(self, *args):
                empty_model_trace.append("load")
                return "loader-result"

        class NeverConstructedUpscaler:
            def __init__(self):
                empty_model_trace.append("construct:upscaler")

        def empty_model_provider(node_id, *args):
            return EmptyLoader if node_id == "ResShiftLoader" else NeverConstructedUpscaler

        def empty_tuple(value):
            empty_model_trace.append(f"tuple:{value}")
            return ()

        with self.assertRaisesRegex(
            RuntimeError,
            r"^\[EasyUseAnima\] ResShiftLoader returned no RESSHIFT_MODEL\.$",
        ):
            execute(
                {
                    "_require_custom_node_class": empty_model_provider,
                    "_node_output_tuple": empty_tuple,
                },
                empty_model_trace,
            )
        self.assertNotIn("construct:upscaler", empty_model_trace)

        seed_failure_trace = []

        class Loader:
            def load(self, *args):
                seed_failure_trace.append("load")
                return "loader-result"

        class Upscaler:
            def __init__(self):
                seed_failure_trace.append("construct:upscaler")

            def upscale(self, *args):
                seed_failure_trace.append("upscale")
                return "upscale-result"

        def provider(node_id, *args):
            return Loader if node_id == "ResShiftLoader" else Upscaler

        tuple_results = iter(((object(),), (object(),)))

        def tuple_helper(value):
            seed_failure_trace.append(f"tuple:{value}")
            return next(tuple_results)

        def fail_seed(value):
            seed_failure_trace.append("seed")
            raise ValueError("seed failed")

        with self.assertRaisesRegex(ValueError, "seed failed"):
            execute(
                {
                    "_require_custom_node_class": provider,
                    "_node_output_tuple": tuple_helper,
                    "_resolve_aio_runtime_seed": fail_seed,
                },
                seed_failure_trace,
            )
        self.assertIn("construct:upscaler", seed_failure_trace)
        self.assertEqual(
            seed_failure_trace[-1:],
            ["seed"],
        )
        self.assertNotIn("upscale", seed_failure_trace)

    def test_upscale_dispatcher_preserves_lazy_branch_and_exception_contract(self):
        model = _Token("model")
        clip = _Token("clip")
        vae = _Token("vae")
        positive = _Token("positive")
        negative = _Token("negative")
        image = _Token("image")
        sampler_settings = {"seed": 17}
        prompt_data = {"fields": []}
        quality_tags = "quality"
        quality_neg = "quality-neg"

        def execute(upscale_settings, leaf_helpers, trace):
            def as_bool(value, default):
                trace.append(("call", "_as_bool", value, default))
                return bool(value)

            helpers = {"_as_bool": as_bool, **leaf_helpers}

            with patch.multiple(legacy_generation, **helpers):
                return nodes._run_aio_upscale_stage(
                    model,
                    clip,
                    vae,
                    positive,
                    negative,
                    image,
                    sampler_settings,
                    upscale_settings,
                    quality_tags,
                    quality_neg,
                    prompt_data,
                    True,
                    False,
                )

        disabled_trace = []
        disabled_result = execute({"enabled": False}, {}, disabled_trace)
        self.assertIs(disabled_result[0], image)
        self.assertEqual(disabled_result[1], {"enabled": False})
        self.assertEqual(
            disabled_trace,
            [
                ("call", "_as_bool", False, False),
            ],
        )

        usdu_settings = {"enabled": True, "backend": ""}
        usdu_output = _Token("usdu_output")
        usdu_metadata = {"backend": "usdu"}
        usdu_trace = []

        def run_usdu(*args):
            usdu_trace.append(("call", "usdu"))
            self.assertEqual(
                args,
                (
                    model,
                    clip,
                    vae,
                    positive,
                    negative,
                    image,
                    sampler_settings,
                    usdu_settings,
                    quality_tags,
                    quality_neg,
                    prompt_data,
                    True,
                    False,
                ),
            )
            return usdu_output, usdu_metadata

        usdu_result = execute(
            usdu_settings,
            {"_run_aio_usdu_upscale_stage": run_usdu},
            usdu_trace,
        )
        self.assertEqual(usdu_result, (usdu_output, usdu_metadata))
        self.assertIs(usdu_result[0], usdu_output)
        self.assertIs(usdu_result[1], usdu_metadata)
        self.assertEqual(
            usdu_trace,
            [
                ("call", "_as_bool", True, False),
                ("call", "usdu"),
            ],
        )

        resshift_settings = {"enabled": True, "backend": "resshift"}
        resshift_output = _Token("resshift_output")
        resshift_metadata = {"backend": "resshift"}
        resshift_trace = []

        def run_resshift(*args):
            resshift_trace.append(("call", "resshift"))
            self.assertEqual(
                args,
                (
                    image,
                    sampler_settings,
                    resshift_settings,
                    quality_tags,
                    quality_neg,
                    prompt_data,
                    True,
                    False,
                ),
            )
            return resshift_output, resshift_metadata

        resshift_result = execute(
            resshift_settings,
            {"_run_aio_resshift_upscale_stage": run_resshift},
            resshift_trace,
        )
        self.assertEqual(
            resshift_result,
            (resshift_output, resshift_metadata),
        )
        self.assertIs(resshift_result[0], resshift_output)
        self.assertIs(resshift_result[1], resshift_metadata)
        self.assertEqual(
            resshift_trace,
            [
                ("call", "_as_bool", True, False),
                ("call", "resshift"),
            ],
        )

        unsupported_trace = []
        with self.assertRaisesRegex(
            RuntimeError,
            r"^\[EasyUseAnima\] Unsupported final upscale backend: unknown$",
        ):
            execute(
                {"enabled": True, "backend": "unknown"},
                {},
                unsupported_trace,
            )
        self.assertEqual(
            unsupported_trace,
            [
                ("call", "_as_bool", True, False),
            ],
        )

        failure_trace = []

        def fail_usdu(*args):
            failure_trace.append(("call", "usdu"))
            raise ValueError("leaf failed")

        with self.assertRaisesRegex(ValueError, "leaf failed"):
            execute(
                {"enabled": True, "backend": "usdu"},
                {"_run_aio_usdu_upscale_stage": fail_usdu},
                failure_trace,
            )
        self.assertEqual(
            failure_trace,
            [
                ("call", "_as_bool", True, False),
                ("call", "usdu"),
            ],
        )

    def test_root_generate_keeps_signature_and_forwards_normalized_execution(self):
        signature = inspect.signature(nodes.EasyUseAnimaAIOGenerator.generate)
        self.assertEqual(
            list(signature.parameters),
            [
                "self",
                "easy_use_anima_input",
                "generation_settings",
                "lora_stack",
                "workflow_prompt",
                "extra_pnginfo",
                "unique_id",
            ],
        )
        self.assertIsNone(signature.parameters["generation_settings"].default)
        for name in (
            "lora_stack",
            "workflow_prompt",
            "extra_pnginfo",
            "unique_id",
        ):
            self.assertIsNone(signature.parameters[name].default)

        generator = nodes.EasyUseAnimaAIOGenerator()
        normalized = {
            "sampler": {
                "seed": 7,
                "seed_after_generate": "fixed",
            },
        }
        forwarded = {
            "ui": {"status": ["forwarded"]},
            "result": ("image", "latent", "metadata"),
        }

        @contextmanager
        def reserved_seed(**_kwargs):
            yield SimpleNamespace(execution_seed=7, next_seed=7)

        with (
            patch.object(
                aio_nodes,
                "_normalize_aio_generation_settings",
                return_value=normalized,
            ),
            patch.object(
                aio_nodes,
                "_require_easy_use_anima_input",
                return_value="input",
            ),
            patch.object(
                aio_nodes,
                "aio_seed_execution",
                reserved_seed,
            ),
            patch.object(
                aio_nodes,
                "_run_aio_generation_pipeline",
                return_value=forwarded,
            ) as run,
        ):
            result = generator.generate(
                "input",
                {"settings": True},
                "lora",
                "workflow",
                "pnginfo",
                "node-id",
            )

        self.assertIs(result, forwarded)
        self.assertEqual(
            result["ui"]["easyuse_anima_aio_seed"],
            [{"execution_seed": "7", "next_seed": "7"}],
        )
        run.assert_called_once_with(
            generator,
            "input",
            normalized,
            "lora",
            "workflow",
            "pnginfo",
            "node-id",
        )

    def test_execution_trace_matches_move_boundary_fixture(self):
        fixture = json.loads(TRACE_FIXTURE_PATH.read_text(encoding="utf-8"))

        self.assertEqual(
            fixture,
            {
                "schema": "easyuse_anima_aio_legacy_execution_trace",
                "version": 1,
                "cases": fixture["cases"],
            },
        )
        actual = {
            "base_txt2img": self._execute_case(
                upscale_enabled=False,
                intermediate_preview=False,
                unique_id=None,
            ),
            "upscale_with_intermediate_preview": self._execute_case(
                upscale_enabled=True,
                intermediate_preview=True,
                unique_id="node-7",
            ),
        }
        self.assertEqual(actual, fixture["cases"])

    def test_first_pass_failure_keeps_outer_model_cleanup_boundary(self):
        trace: list[str] = []
        with patch.object(
            legacy_generation.AIOFirstPassStage,
            "run",
            side_effect=RuntimeError("first pass failed"),
        ):
            with self.assertRaisesRegex(RuntimeError, "first pass failed"):
                self._execute_case(
                    upscale_enabled=False,
                    intermediate_preview=False,
                    unique_id=None,
                    trace_sink=trace,
                )

        self.assertEqual(
            trace[-3:],
            [
                "cleanup:sample",
                "cleanup:model",
                "cleanup:lora",
            ],
        )

    def test_highres_stage_failure_keeps_outer_model_cleanup_boundary(self):
        trace: list[str] = []
        with patch.object(
            legacy_generation.AIOHighresStage,
            "run",
            side_effect=RuntimeError("highres stage failed"),
        ):
            with self.assertRaisesRegex(RuntimeError, "highres stage failed"):
                self._execute_case(
                    upscale_enabled=False,
                    intermediate_preview=False,
                    unique_id=None,
                    trace_sink=trace,
                )

        self.assertEqual(
            trace[-3:],
            [
                "cleanup:sample",
                "cleanup:model",
                "cleanup:lora",
            ],
        )

    def test_detailer_stage_failure_keeps_outer_model_cleanup_boundary(self):
        trace: list[str] = []
        with patch.object(
            legacy_generation.AIODetailerStage,
            "run",
            side_effect=RuntimeError("detailer stage failed"),
        ):
            with self.assertRaisesRegex(RuntimeError, "detailer stage failed"):
                self._execute_case(
                    upscale_enabled=False,
                    intermediate_preview=False,
                    unique_id=None,
                    trace_sink=trace,
                )

        self.assertEqual(
            trace[-3:],
            [
                "cleanup:sample",
                "cleanup:model",
                "cleanup:lora",
            ],
        )

    def test_upscale_stage_failure_keeps_outer_model_cleanup_boundary(self):
        trace: list[str] = []
        with patch.object(
            legacy_generation.AIOUpscaleStage,
            "run",
            side_effect=RuntimeError("upscale stage failed"),
        ):
            with self.assertRaisesRegex(RuntimeError, "upscale stage failed"):
                self._execute_case(
                    upscale_enabled=False,
                    intermediate_preview=False,
                    unique_id=None,
                    trace_sink=trace,
                )

        self.assertEqual(
            trace[-3:],
            [
                "cleanup:sample",
                "cleanup:model",
                "cleanup:lora",
            ],
        )

    def test_postprocess_stage_failure_keeps_outer_model_cleanup_boundary(self):
        trace: list[str] = []
        with patch.object(
            legacy_generation.AIOPostprocessStage,
            "run",
            side_effect=RuntimeError("postprocess stage failed"),
        ):
            with self.assertRaisesRegex(RuntimeError, "postprocess stage failed"):
                self._execute_case(
                    upscale_enabled=False,
                    intermediate_preview=False,
                    unique_id=None,
                    trace_sink=trace,
                )

        self.assertEqual(
            trace[-3:],
            [
                "cleanup:sample",
                "cleanup:model",
                "cleanup:lora",
            ],
        )

    def test_save_output_stage_failure_runs_after_outer_model_cleanup_boundary(self):
        trace: list[str] = []
        with patch.object(
            legacy_generation.AIOSaveOutputStage,
            "run",
            side_effect=RuntimeError("save output stage failed"),
        ):
            with self.assertRaisesRegex(RuntimeError, "save output stage failed"):
                self._execute_case(
                    upscale_enabled=False,
                    intermediate_preview=False,
                    unique_id=None,
                    trace_sink=trace,
                )

        self.assertEqual(
            trace[-3:],
            [
                "cleanup:sample",
                "cleanup:model",
                "cleanup:lora",
            ],
        )

    def test_intermediate_preview_failure_keeps_outer_model_cleanup_boundary(self):
        trace: list[str] = []
        with patch.object(
            legacy_generation.PreviewCollector,
            "add",
            side_effect=RuntimeError("preview failed"),
        ):
            with self.assertRaisesRegex(RuntimeError, "preview failed"):
                self._execute_case(
                    upscale_enabled=False,
                    intermediate_preview=True,
                    unique_id=None,
                    trace_sink=trace,
                )

        self.assertEqual(
            trace[-3:],
            [
                "cleanup:sample",
                "cleanup:model",
                "cleanup:lora",
            ],
        )

    def _execute_case(
        self,
        *,
        upscale_enabled: bool,
        intermediate_preview: bool,
        unique_id,
        trace_sink: list[str] | None = None,
    ) -> dict:
        trace = trace_sink if trace_sink is not None else []
        generator = nodes.EasyUseAnimaAIOGenerator()
        context = {
            "prompt_data": {"positive_prompt": "prompt"},
            "resource_info": {"unet_name": "model.safetensors"},
            "input_settings": {"schema": "input-settings"},
        }
        settings = {
            "mode": "txt2img",
            "sampler": {"seed": -1, "backend": "comfy_ksampler"},
            "artist_mix": {
                "mode": "sequential",
                "start_percent": 0.0,
                "strength_scale": 1.0,
                "style_gain": 1.0,
                "rms_scale_cap": 1.0,
                "exact_top_k": 0,
                "cluster_count": 1,
                "dominant_isolation": False,
                "dominant_threshold": 0.0,
            },
            "mod_guidance": {"profile": "off", "mode": "auto"},
            "highres": {"enabled": False},
            "detailer": {},
            "upscale": {"enabled": upscale_enabled},
            "postprocess": {"enabled": False},
            "preview": {"intermediate_images": intermediate_preview},
            "save": {
                "enabled": True,
                "backend": "comfy",
                "filename_prefix": "Anima",
            },
        }

        base_model = _Token("base")
        lora_model = _Token("lora")
        patched_model = _Token("model")
        sample_model = _Token("sample")
        base_clip = _Token("base_clip")
        clip = _Token("clip")
        vae = _Token("vae")
        model_names = {
            id(lora_model): "lora",
            id(patched_model): "model",
            id(sample_model): "sample",
        }

        def phase(name, result):
            def run(*args, **kwargs):
                trace.append(name)
                return result

            return run

        def require(value):
            trace.append("require_input")
            self.assertIs(value, context)
            return value

        def normalize_settings(value):
            trace.append("normalize_settings")
            self.assertEqual(value, "settings-json")
            return copy.deepcopy(settings)

        def typed_config(normalized_settings):
            return SimpleNamespace(
                to_dict=lambda: copy.deepcopy(normalized_settings),
                mode=normalized_settings["mode"],
                sampler=SimpleNamespace(
                    to_dict=lambda: copy.deepcopy(
                        normalized_settings["sampler"]
                    )
                ),
                mod_guidance=SimpleNamespace(
                    to_dict=lambda: copy.deepcopy(
                        normalized_settings["mod_guidance"]
                    )
                ),
                preview=SimpleNamespace(
                    intermediate_images=normalized_settings[
                        "preview"
                    ]["intermediate_images"]
                ),
                highres=SimpleNamespace(
                    to_dict=lambda: copy.deepcopy(
                        normalized_settings["highres"]
                    )
                ),
                detailer=SimpleNamespace(
                    to_dict=lambda: copy.deepcopy(
                        normalized_settings["detailer"]
                    )
                ),
                upscale=SimpleNamespace(
                    to_dict=lambda: copy.deepcopy(
                        normalized_settings["upscale"]
                    )
                ),
                postprocess=SimpleNamespace(
                    to_dict=lambda: copy.deepcopy(
                        normalized_settings["postprocess"]
                    )
                ),
                save=SimpleNamespace(
                    to_dict=lambda: copy.deepcopy(
                        normalized_settings["save"]
                    )
                ),
            )

        def resolve_seed(value):
            trace.append("resolve_seed")
            self.assertEqual(value, -1)
            return 17

        def load_resources(value):
            trace.append("load_resources")
            self.assertIs(value, context)
            return base_model, base_clip, vae

        def apply_lora(model, source_clip, stack):
            trace.append("apply_lora")
            self.assertIs(model, base_model)
            self.assertIs(source_clip, base_clip)
            self.assertEqual(stack, "lora-stack")
            return lora_model, clip, [{"name": "style.safetensors"}]

        def apply_model_patches(model, normalized_settings):
            trace.append("apply_model_patches")
            self.assertIs(model, lora_model)
            self.assertEqual(normalized_settings["sampler"]["seed"], 17)
            return patched_model

        def advanced_outputs(prompt_data):
            trace.append("advanced_outputs")
            return (
                "positive",
                "negative",
                "quality",
                "quality-neg",
                False,
                False,
                "metadata-positive",
                "metadata-negative",
                64,
                96,
            )

        def apply_spectrum_model(model, source_clip, positive, sampler):
            trace.append("apply_spectrum_model_patches")
            self.assertIs(model, patched_model)
            return sample_model

        class _Random:
            @staticmethod
            def getrandbits(bits):
                trace.append("random_run_id")
                self.assertEqual(bits, 64)
                return 0x1234

        def cache_key(**kwargs):
            scope = kwargs["cache_scope"]
            if unique_id is None:
                self.assertEqual(scope, str(id(generator)))
                scope = "generator-id"
            trace.append(f"cache_key:{scope}")
            return "cache-key"

        def run_highres(
            model,
            source_clip,
            source_vae,
            positive,
            negative,
            image,
            latent,
            width,
            height,
            *args,
        ):
            trace.append("run_highres")
            return latent, image, width, height, {"enabled": False}

        def run_detailer(*args):
            trace.append("run_detailer")
            return args[5], {"enabled": False}

        def run_upscale(*args, **kwargs):
            trace.append("run_upscale")
            if upscale_enabled:
                return "upscaled-image", {"enabled": True, "backend": "stub"}
            return args[5], {"enabled": False}

        def run_postprocess(image, postprocess):
            trace.append("run_postprocess")
            return image, {"enabled": False}

        def image_size(image, fallback_width, fallback_height):
            trace.append("image_size")
            self.assertEqual(image, "upscaled-image")
            return 128, 192

        def encode_image(source_vae, image):
            trace.append("encode_upscaled_image")
            self.assertIs(source_vae, vae)
            return "upscaled-latent"

        def cleanup(model, original_model):
            trace.append(f"cleanup:{model_names[id(model)]}")
            self.assertIs(original_model, base_model)

        def save_temp(image, stage, **kwargs):
            trace.append(f"temp_preview:{stage}")
            return [{"filename": f"{stage}.png", "stage": stage, "type": "temp"}]

        def send_preview(node_id, run_id, stage, images):
            trace.append(f"send_preview:{stage}")

        def save_prefix(save_settings):
            trace.append("save_prefix")
            return save_settings["filename_prefix"]

        def save_comfy(image, prefix, **kwargs):
            trace.append("save_comfy")
            self.assertTrue(all(item.startswith("cleanup:") for item in trace[-5:-2]))
            return {
                "ui": {
                    "images": [
                        {"filename": "final.png", "subfolder": "", "type": "output"}
                    ]
                }
            }

        def tag_images(images, stage, *, width, height):
            trace.append(f"tag:{stage}")
            return [
                {**item, "stage": stage, "width": width, "height": height}
                for item in images
            ]

        def unexpected(*args, **kwargs):
            self.fail("standalone Mod Guidance must remain lazy for the fixture cases")

        with (
            patch(
                "easyuse_anima.nodes.seed_adapters.resolve_seed_execution_identity",
                return_value=None,
            ),
            patch.multiple(
                aio_nodes,
                _require_easy_use_anima_input=require,
                _normalize_aio_generation_settings=normalize_settings,
                _resolve_aio_runtime_seed=resolve_seed,
            ),
            patch.multiple(
                legacy_generation,
                _normalize_aio_generation_settings=normalize_settings,
                _resolve_aio_runtime_seed=resolve_seed,
                _aio_generation_config_from_dict=typed_config,
                _load_aio_resources_from_input_context=load_resources,
                _apply_aio_lora_stack=apply_lora,
                _apply_aio_model_patches=apply_model_patches,
                _normalize_prompt_data=phase(
                    "normalize_prompt",
                    context["prompt_data"],
                ),
                _advanced_outputs_from_prompt_data=advanced_outputs,
                _encode_prompt_data_positive_conditioning=phase(
                    "encode_positive",
                    "positive-conditioning",
                ),
                _as_bool=lambda value, default: bool(value),
                _aio_detailer_has_enabled_targets=phase("detailer_enabled", False),
                _normalize_anima_mod_guidance_profile=phase("normalize_profile", "off"),
                _resolve_anima_mod_guidance_enabled=phase("resolve_guidance", False),
                _aio_highres_effective_backend=phase(
                    "resolve_highres_backend",
                    "comfy_ksampler",
                ),
                _apply_spectrum_anima_mod_guidance=unexpected,
                _apply_aio_spectrum_model_patches_for_comfy_sampler=apply_spectrum_model,
                _single_value=lambda value: value,
                random=_Random,
                _aio_first_pass_cache_key=cache_key,
                _get_aio_first_pass_cache=phase("get_cache", None),
                _generate_empty_latent_with_comfy=phase("empty_latent", "empty-latent"),
                _sample_latent_with_aio_backend=phase("sample", "sampled-latent"),
                _decode_latent_with_comfy=phase("decode", "decoded-image"),
                _resize_image_to_size_if_needed=phase(
                    "resize_first_pass",
                    ("decoded-image", False),
                ),
                _put_aio_first_pass_cache=phase("put_cache", None),
                _run_aio_highres_stage=run_highres,
                _run_aio_detailer_stage=run_detailer,
                _run_aio_upscale_stage=run_upscale,
                _image_tensor_size=image_size,
                _encode_image_with_comfy_vae=encode_image,
                _run_aio_postprocess_stage=run_postprocess,
                _cleanup_aio_ephemeral_model=cleanup,
                _save_aio_temp_preview_image=save_temp,
                _send_aio_preview_event=send_preview,
                _aio_save_filename_prefix=save_prefix,
                _save_image_with_comfy=save_comfy,
                _tag_aio_preview_images=tag_images,
                _prompt_data_json_safe=copy.deepcopy,
            ),
            patch.object(
                legacy_generation,
                "_require_easy_use_anima_input",
                require,
            ),
            patch_comfy_helper(
                nodes,
                "_encode_with_comfy_clip",
                phase("encode_negative", "negative-conditioning"),
            ),
        ):
            output = generator.generate(
                context,
                "settings-json",
                "lora-stack",
                {"workflow": True},
                {"pnginfo": True},
                unique_id,
            )

        image, latent, metadata_json = output["result"]
        metadata = json.loads(metadata_json)
        return {
            "trace": trace,
            "result": {
                "image": image,
                "latent": latent,
                "metadata": metadata,
                "ui": output["ui"],
            },
        }


if __name__ == "__main__":
    unittest.main()
