from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

import nodes
from easyuse_anima.image import sam3 as sam3_service
from easyuse_anima.nodes import impact_detailer_nodes
from easyuse_anima.nodes import sam3_nodes
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

    def test_root_symbols_are_direct_canonical_aliases(self):
        retired_service_names = (
            "_call_impact_detailer",
            "_empty_mask_for_image",
            "_empty_segs_for_image",
            "_find_impact_detailer_class",
            "_find_impact_mask_to_segs_class",
            "_find_sam3_detect_class",
            "_format_sam3_detection_prompt",
        )
        for name in retired_service_names:
            with self.subTest(retired=name):
                self.assertFalse(hasattr(nodes, name))

        retained_service_names = (
            "_context_value",
            "_sam3_context",
            "_segs_has_items",
        )
        for name in retained_service_names:
            with self.subTest(name=name):
                self.assertIs(getattr(nodes, name), getattr(sam3_service, name))

        node_names = (
            "EasyUseAnimaSAM3Context",
            "EasyUseAnimaSAM3Detailer",
        )
        for name in node_names:
            with self.subTest(name=name):
                self.assertIs(getattr(nodes, name), getattr(sam3_nodes, name))
        self.assertFalse(hasattr(nodes, "_EasyUseAnimaImpactDetailerDelegate"))
        self.assertIs(
            sam3_nodes._EasyUseAnimaImpactDetailerDelegate,
            impact_detailer_nodes._EasyUseAnimaImpactDetailerDelegate,
        )
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
            nodes,
            "_find_comfy_node_class",
            return_value=sentinel,
        ) as find:
            self.assertIs(sam3_service._find_sam3_detect_class(), sentinel)
        find.assert_called_once_with("SAM3_Detect")

        with patch_comfy_helper(
            nodes,
            "_find_comfy_node_mapping_class",
            return_value=sentinel,
        ) as find:
            self.assertIs(sam3_service._find_impact_detailer_class(), sentinel)
        find.assert_called_once_with("DetailerForEach")

    def test_impact_primary_lookup_uses_mapping_only(self):
        direct_attribute = object()
        with (
            patch.object(nodes, "NODE_CLASS_MAPPINGS", {}, create=True),
            patch.object(nodes, "DetailerForEach", direct_attribute, create=True),
        ):
            with self.assertRaisesRegex(
                RuntimeError,
                "SAM3 Detailer requires ComfyUI Impact Pack",
            ):
                sam3_service._find_impact_detailer_class()

    def test_context_node_keeps_call_time_checkpoint_loader(self):
        with patch.object(
            nodes,
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
            patch.object(sam3_nodes, "_empty_mask_for_image", return_value="empty-mask"),
            patch.object(sam3_nodes, "_empty_segs_for_image", return_value="empty-segs"),
        ):
            result = sam3_nodes.EasyUseAnimaSAM3Detailer().doit(
                **self._detailer_kwargs(enabled=False)
            )

        self.assertEqual(result, ("input-image", "empty-segs", "empty-mask", "input-image"))

    def test_detector_mask_and_impact_delegation_arguments_are_preserved(self):
        sam3_detect = SimpleNamespace(execute=Mock(return_value=("mask",)))
        mask_to_segs = SimpleNamespace(doit=Mock(return_value=(((64, 64), ["seg"]),)))

        with (
            patch.object(sam3_nodes, "_empty_mask_for_image", return_value="empty-mask"),
            patch.object(sam3_nodes, "_empty_segs_for_image", return_value="empty-segs"),
            patch_comfy_helper(
                nodes,
                "_encode_with_comfy_clip",
                return_value="conditioning",
            ) as encode,
            patch.object(sam3_nodes, "_find_sam3_detect_class", return_value=sam3_detect),
            patch.object(sam3_nodes, "_find_impact_mask_to_segs_class", return_value=mask_to_segs),
            patch.object(
                sam3_nodes._EasyUseAnimaImpactDetailerDelegate,
                "doit",
                return_value=("detailed-image",),
            ) as detail,
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
            patch.object(sam3_nodes, "_empty_mask_for_image", return_value="empty-mask"),
            patch.object(sam3_nodes, "_empty_segs_for_image", return_value="empty-segs"),
            patch_comfy_helper(
                nodes,
                "_encode_with_comfy_clip",
                return_value="conditioning",
            ),
            patch.object(sam3_nodes, "_find_sam3_detect_class", return_value=sam3_detect),
            patch.object(sam3_nodes, "_find_impact_mask_to_segs_class", return_value=mask_to_segs),
            patch.object(sam3_nodes._EasyUseAnimaImpactDetailerDelegate, "doit") as detail,
        ):
            result = sam3_nodes.EasyUseAnimaSAM3Detailer().doit(**self._detailer_kwargs())

        self.assertEqual(result, ("input-image", ((64, 64), []), "mask", "input-image"))
        detail.assert_not_called()

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
