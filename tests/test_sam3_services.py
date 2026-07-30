from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from easyuse_anima.image import sam3 as sam3_service
from easyuse_anima.image import sam3_detailer as sam3_detailer_service
from tests.comfy_host_fakes import patch_comfy_helper


class SAM3ServiceTests(unittest.TestCase):
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

    def test_detection_prompt_formatting_is_preserved(self):
        self.assertEqual(
            sam3_service._format_sam3_detection_prompt(" face, hand:2\neyes ", 3),
            "face:3, hand:2, eyes:3",
        )
        with self.assertRaisesRegex(ValueError, "SAM3 detect prompt is empty"):
            sam3_service._format_sam3_detection_prompt("  ", 1)

    def test_context_shape_is_preserved(self):
        self.assertEqual(
            sam3_service._sam3_context("model", "clip", "vae", "sam3.ckpt"),
            {
                "model": "model",
                "clip": "clip",
                "vae": "vae",
                "ckpt_name": "sam3.ckpt",
            },
        )

    def test_sam3_lookup_uses_call_time_provider(self):
        sentinel = object()
        with patch_comfy_helper(
            sam3_service,
            "_find_comfy_node_class",
            return_value=sentinel,
        ) as find:
            self.assertIs(sam3_service._find_sam3_detect_class(), sentinel)
        find.assert_called_once_with("SAM3_Detect")

        with patch_comfy_helper(
            sam3_service,
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

    def test_disabled_detailer_preserves_original_outputs(self):
        with (
            patch.object(
                sam3_detailer_service,
                "_empty_mask_for_image",
                return_value="empty-mask",
            ),
            patch.object(
                sam3_detailer_service,
                "_empty_segs_for_image",
                return_value="empty-segs",
            ),
        ):
            result = sam3_detailer_service._run_sam3_detailer(
                **self._detailer_kwargs(enabled=False)
            )

        self.assertEqual(
            result,
            ("input-image", "empty-segs", "empty-mask", "input-image"),
        )

    def test_detector_mask_and_impact_delegation_arguments_are_preserved(self):
        sam3_detect = SimpleNamespace(execute=Mock(return_value=("mask",)))
        mask_to_segs = SimpleNamespace(
            doit=Mock(return_value=(((64, 64), ["seg"]),))
        )
        with (
            patch.object(
                sam3_detailer_service,
                "_empty_mask_for_image",
                return_value="empty-mask",
            ),
            patch.object(
                sam3_detailer_service,
                "_empty_segs_for_image",
                return_value="empty-segs",
            ),
            patch.object(
                sam3_detailer_service,
                "_encode_with_comfy_clip",
                return_value="conditioning",
            ) as encode,
            patch.object(
                sam3_detailer_service,
                "_find_sam3_detect_class",
                return_value=sam3_detect,
            ),
            patch.object(
                sam3_detailer_service,
                "_find_impact_mask_to_segs_class",
                return_value=mask_to_segs,
            ),
            patch.object(
                sam3_detailer_service,
                "_run_impact_detailer",
                return_value=("detailed-image",),
            ) as detail,
        ):
            result = sam3_detailer_service._run_sam3_detailer(
                **self._detailer_kwargs()
            )

        self.assertEqual(
            result,
            ("detailed-image", ((64, 64), ["seg"]), "mask", "input-image"),
        )
        encode.assert_called_once_with("sam3-clip", "face:3, hand:2")
        sam3_detect.execute.assert_called_once_with(
            model="sam3-model",
            image="input-image",
            conditioning="conditioning",
            threshold=0.63,
            refine_iterations=2,
            individual_masks=True,
        )
        mask_to_segs.doit.assert_called_once_with(
            "mask", False, 4.0, False, 16, True
        )
        self.assertEqual(detail.call_args.kwargs["model"], "detail-model")
        self.assertEqual(detail.call_args.kwargs["scheduler"], "scheduler")
        self.assertEqual(detail.call_args.kwargs["seed"], 17)

    def test_no_segs_preserves_original_image_and_skips_impact(self):
        sam3_detect = SimpleNamespace(execute=Mock(return_value=("mask",)))
        mask_to_segs = SimpleNamespace(doit=Mock(return_value=(((64, 64), []),)))
        with (
            patch.object(
                sam3_detailer_service,
                "_empty_mask_for_image",
                return_value="empty-mask",
            ),
            patch.object(
                sam3_detailer_service,
                "_empty_segs_for_image",
                return_value="empty-segs",
            ),
            patch.object(
                sam3_detailer_service,
                "_encode_with_comfy_clip",
                return_value="conditioning",
            ),
            patch.object(
                sam3_detailer_service,
                "_find_sam3_detect_class",
                return_value=sam3_detect,
            ),
            patch.object(
                sam3_detailer_service,
                "_find_impact_mask_to_segs_class",
                return_value=mask_to_segs,
            ),
            patch.object(sam3_detailer_service, "_run_impact_detailer") as detail,
        ):
            result = sam3_detailer_service._run_sam3_detailer(
                **self._detailer_kwargs()
            )

        self.assertEqual(
            result,
            ("input-image", ((64, 64), []), "mask", "input-image"),
        )
        detail.assert_not_called()

    def test_impact_call_filters_unknown_keywords_without_changing_order(self):
        class Detailer:
            def __init__(self):
                self.called = False

            def doit(self):
                self.called = True
                return "result"

        detailer = Detailer()
        result = sam3_service._call_impact_detailer(
            detailer,
            image="image",
            unknown="drop",
        )

        self.assertEqual(result, "result")
        self.assertTrue(detailer.called)


if __name__ == "__main__":
    unittest.main()
