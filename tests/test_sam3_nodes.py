from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from easyuse_anima.aio import resources as aio_resources
from easyuse_anima.image import sam3 as sam3_service
from easyuse_anima.image import sam3_detailer as sam3_detailer_service
from easyuse_anima.infrastructure.comfy import capabilities
from easyuse_anima.nodes import impact_detailer_nodes, sam3_nodes
from tests.comfy_host_fakes import patch_comfy_helper


class SAM3MoveTests(unittest.TestCase):
    def _detailer_kwargs(self, **overrides):
        values = {
            "enabled": True,
            "image": "input-image",
            "ctx_SAM3": {"model": "sam3-model", "clip": "sam3-clip"},
            "detect_prompt": "face, hand:2",
            "detect_count": 3,
            "threshold": 0.63,
            "refine_iterations": 2,
            "individual_masks": True,
            "combined": False,
            "crop_factor": 4.0,
            "bbox_fill": False,
            "drop_size": 16,
            "contour_fill": True,
            "model": "detail-model",
            "clip": "detail-clip",
            "vae": "detail-vae",
            "guide_size": 1024,
            "guide_size_for": False,
            "max_size": 2048,
            "seed": 17,
            "steps": 24,
            "cfg": 6.5,
            "sampler_name": "sampler",
            "scheduler": "scheduler",
            "positive": "positive",
            "negative": "negative",
            "denoise": 0.33,
            "feather": 5,
            "noise_mask": True,
            "force_inpaint": True,
            "wildcard": "",
        }
        values.update(overrides)
        return values

    def test_sam3_adapters_use_direct_canonical_owners(self):
        self.assertIs(
            sam3_nodes._EasyUseAnimaImpactDetailerDelegate,
            impact_detailer_nodes._EasyUseAnimaImpactDetailerDelegate,
        )
        self.assertIs(
            impact_detailer_nodes._impact_scheduler_names,
            capabilities._impact_scheduler_names,
        )
        self.assertIs(
            sam3_nodes._load_checkpoint_with_comfy,
            aio_resources._load_checkpoint_with_comfy,
        )
        self.assertIs(
            sam3_nodes._preferred_checkpoint_default,
            aio_resources._preferred_checkpoint_default,
        )
        for module, binder_name in (
            (sam3_service, "_bind_sam3_runtime"),
            (impact_detailer_nodes, "_bind_impact_detailer_node_runtime"),
            (sam3_nodes, "_bind_sam3_node_runtime"),
        ):
            with self.subTest(module=module.__name__, binder=binder_name):
                self.assertFalse(hasattr(module, binder_name))
        with (
            patch.object(
                impact_detailer_nodes,
                "_comfy_max_resolution",
                return_value=4096,
            ),
            patch.object(
                impact_detailer_nodes,
                "_comfy_sampler_names",
                return_value=["sampler"],
            ),
            patch.object(
                impact_detailer_nodes,
                "_impact_scheduler_names",
                return_value=["scheduler"],
            ),
        ):
            input_types = sam3_nodes._EasyUseAnimaImpactDetailerDelegate.INPUT_TYPES()
        self.assertEqual(input_types["required"]["guide_size"][1]["max"], 4096)
        self.assertEqual(input_types["required"]["sampler_name"][0], ["sampler"])
        self.assertEqual(input_types["required"]["scheduler"][0], ["scheduler"])

    def test_detection_prompt_formatting_is_preserved(self):
        self.assertEqual(
            sam3_service._format_sam3_detection_prompt(" face, hand:2\neyes ", 3),
            "face:3, hand:2, eyes:3",
        )
        with self.assertRaisesRegex(ValueError, "SAM3 detect prompt is empty"):
            sam3_service._format_sam3_detection_prompt("  ", 1)

    def test_sam3_lookup_uses_call_time_provider(self):
        sentinel = object()
        with patch_comfy_helper(
            sam3_nodes,
            "_find_comfy_node_class",
            return_value=sentinel,
        ) as find:
            self.assertIs(sam3_service._find_sam3_detect_class(), sentinel)
        find.assert_called_once_with("SAM3_Detect")

        with patch_comfy_helper(
            sam3_nodes,
            "_find_comfy_node_mapping_class",
            return_value=sentinel,
        ) as find:
            self.assertIs(sam3_service._find_impact_detailer_class(), sentinel)
        find.assert_called_once_with("DetailerForEach")

    def test_detailer_missing_host_helper_error_is_preserved(self):
        with self.assertRaisesRegex(
            RuntimeError,
            "SAM3 node Comfy host helper is unavailable: _encode_with_comfy_clip",
        ):
            sam3_detailer_service._missing_host_helper("_encode_with_comfy_clip")

    def test_context_node_keeps_call_time_checkpoint_loader(self):
        with patch.object(
            sam3_nodes,
            "_load_checkpoint_with_comfy",
            return_value=("model", "clip", "vae"),
        ) as load:
            result = sam3_nodes.EasyUseAnimaSAM3Context().load("sam3.ckpt")

        self.assertEqual(
            result,
            ({"model": "model", "clip": "clip", "vae": "vae", "ckpt_name": "sam3.ckpt"}, "model", "clip", "vae"),
        )
        load.assert_called_once_with("sam3.ckpt")

    def test_disabled_detailer_preserves_original_outputs(self):
        with (
            patch.object(sam3_detailer_service, "_empty_mask_for_image", return_value="empty-mask"),
            patch.object(sam3_detailer_service, "_empty_segs_for_image", return_value="empty-segs"),
        ):
            result = sam3_nodes.EasyUseAnimaSAM3Detailer().doit(
                **self._detailer_kwargs(enabled=False)
            )

        self.assertEqual(result, ("input-image", "empty-segs", "empty-mask", "input-image"))

    def test_detector_mask_and_impact_delegation_arguments_are_preserved(self):
        sam3_detect = SimpleNamespace(execute=Mock(return_value=("mask",)))
        mask_to_segs = SimpleNamespace(doit=Mock(return_value=(((64, 64), ["seg"]),)))
        detail = Mock(return_value=("detailed-image",))
        detailer_cls = Mock(return_value=SimpleNamespace(doit=detail))

        with (
            patch.object(sam3_detailer_service, "_empty_mask_for_image", return_value="empty-mask"),
            patch.object(sam3_detailer_service, "_empty_segs_for_image", return_value="empty-segs"),
            patch_comfy_helper(
                sam3_nodes,
                "_encode_with_comfy_clip",
                return_value="conditioning",
            ) as encode,
            patch.object(sam3_detailer_service, "_find_sam3_detect_class", return_value=sam3_detect),
            patch.object(sam3_detailer_service, "_find_impact_mask_to_segs_class", return_value=mask_to_segs),
            patch.object(sam3_detailer_service, "_find_impact_detailer_class", return_value=detailer_cls),
        ):
            result = sam3_nodes.EasyUseAnimaSAM3Detailer().doit(**self._detailer_kwargs())

        self.assertEqual(result, ("detailed-image", ((64, 64), ["seg"]), "mask", "input-image"))
        encode.assert_called_once_with("sam3-clip", "face:3, hand:2")
        sam3_detect.execute.assert_called_once_with(
            model="sam3-model",
            image="input-image",
            conditioning="conditioning",
            threshold=0.63,
            refine_iterations=2,
            individual_masks=True,
        )
        mask_to_segs.doit.assert_called_once_with("mask", False, 4.0, False, 16, True)
        self.assertEqual(detail.call_args.kwargs["model"], "detail-model")
        self.assertEqual(detail.call_args.kwargs["scheduler"], "scheduler")
        self.assertEqual(detail.call_args.kwargs["seed"], 17)

    def test_no_segs_preserves_original_image_and_skips_impact(self):
        sam3_detect = SimpleNamespace(execute=Mock(return_value=("mask",)))
        mask_to_segs = SimpleNamespace(doit=Mock(return_value=(((64, 64), []),)))

        with (
            patch.object(sam3_detailer_service, "_empty_mask_for_image", return_value="empty-mask"),
            patch.object(sam3_detailer_service, "_empty_segs_for_image", return_value="empty-segs"),
            patch_comfy_helper(
                sam3_nodes,
                "_encode_with_comfy_clip",
                return_value="conditioning",
            ),
            patch.object(sam3_detailer_service, "_find_sam3_detect_class", return_value=sam3_detect),
            patch.object(sam3_detailer_service, "_find_impact_mask_to_segs_class", return_value=mask_to_segs),
            patch.object(sam3_detailer_service, "_run_impact_detailer") as detail,
        ):
            result = sam3_nodes.EasyUseAnimaSAM3Detailer().doit(**self._detailer_kwargs())

        self.assertEqual(result, ("input-image", ((64, 64), []), "mask", "input-image"))
        detail.assert_not_called()

    def test_impact_node_adapter_delegates_to_shared_operation(self):
        kwargs = self._detailer_kwargs()
        for key in (
            "enabled",
            "ctx_SAM3",
            "detect_prompt",
            "detect_count",
            "threshold",
            "refine_iterations",
            "individual_masks",
            "combined",
            "crop_factor",
            "bbox_fill",
            "drop_size",
            "contour_fill",
        ):
            kwargs.pop(key)
        kwargs["segs"] = "detail-segs"

        with patch.object(
            impact_detailer_nodes,
            "_run_impact_detailer",
            return_value=("detailed-image",),
        ) as run:
            result = impact_detailer_nodes._EasyUseAnimaImpactDetailerDelegate().doit(**kwargs)

        self.assertEqual(result, ("detailed-image",))
        self.assertEqual(run.call_args.kwargs["image"], "input-image")
        self.assertEqual(run.call_args.kwargs["segs"], "detail-segs")
        self.assertEqual(run.call_args.kwargs["scheduler"], "scheduler")
        self.assertEqual(run.call_args.kwargs["alignment"], "impact")
        self.assertEqual(run.call_args.kwargs["noise_mask_feather"], 0)

    def test_impact_call_filters_unknown_keywords_without_changing_order(self):
        class Detailer:
            def __init__(self):
                self.called = False

            def doit(self):
                self.called = True
                return "result"

        detailer = Detailer()

        result = sam3_service._call_impact_detailer(detailer, image="image", unknown="drop")

        self.assertEqual(result, "result")
        self.assertTrue(detailer.called)


if __name__ == "__main__":
    unittest.main()
