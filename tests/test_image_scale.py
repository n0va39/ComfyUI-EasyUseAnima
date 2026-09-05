import unittest
from unittest.mock import patch

from easyuse_anima.image.scaling import (
    _image_scale_by_multiple_size,
    _normalize_image_scale_options,
)
from easyuse_anima.nodes import image_nodes
from easyuse_anima.nodes.image_nodes import EasyUseAnimaImageScaleByMultiple


class ImageScaleByMultipleTests(unittest.TestCase):
    def test_exact_valid_scale_is_kept(self):
        width, height, applied_scale = _image_scale_by_multiple_size(1024, 1536, 1.25, "32")

        self.assertEqual((width, height), (1280, 1920))
        self.assertAlmostEqual(applied_scale, 1.25, places=6)

    def test_scale_uses_nearest_valid_ratio_for_1216_series(self):
        width, height, applied_scale = _image_scale_by_multiple_size(1216, 1824, 1.25, "32")

        self.assertEqual((width, height), (1536, 2304))
        self.assertAlmostEqual(applied_scale, 24 / 19, places=4)

    def test_scale_uses_nearest_valid_ratio_for_1152_series(self):
        width, height, applied_scale = _image_scale_by_multiple_size(1152, 1728, 1.25, "32")

        self.assertEqual((width, height), (1472, 2208))
        self.assertAlmostEqual(applied_scale, 23 / 18, places=4)

    def test_multiple_64_uses_nearest_valid_ratio(self):
        width, height, applied_scale = _image_scale_by_multiple_size(1024, 1536, 1.5, "64")

        self.assertEqual((width, height), (1536, 2304))
        self.assertAlmostEqual(applied_scale, 1.5, places=6)

    def test_max_long_edge_limits_selected_valid_ratio(self):
        width, height, applied_scale = _image_scale_by_multiple_size(
            1216,
            1824,
            1.5,
            "32",
            max_long_edge=2304,
        )

        self.assertEqual((width, height), (1536, 2304))
        self.assertAlmostEqual(applied_scale, 24 / 19, places=4)

    def test_max_long_edge_keeps_multiple_when_exact_limit_is_not_valid(self):
        width, height, applied_scale = _image_scale_by_multiple_size(
            1024,
            1536,
            1.5,
            "32",
            max_long_edge=2048,
        )

        self.assertEqual((width, height), (1376, 2048))
        self.assertAlmostEqual(applied_scale, 1.3385, places=4)

    def test_max_long_edge_approximates_when_exact_aspect_candidate_would_not_upscale(self):
        width, height, applied_scale = _image_scale_by_multiple_size(
            1344,
            1632,
            1.25,
            "32",
            max_long_edge=2048,
        )

        self.assertEqual((width, height), (1696, 2048))
        self.assertAlmostEqual(applied_scale, 1.2584, places=4)

    def test_input_order_keeps_existing_widget_values_compatible(self):
        required = EasyUseAnimaImageScaleByMultiple.INPUT_TYPES()["required"]

        self.assertEqual(
            list(required),
            ["image", "scale_by", "upscale_method", "multiple", "max_long_edge"],
        )

    def test_max_long_edge_wins_when_no_aligned_upscale_fits(self):
        width, height, _ = _image_scale_by_multiple_size(
            2010, 1000, 1.2, "64", max_long_edge=2016,
        )

        self.assertEqual((width, height), (1984, 1024))

    def test_max_long_edge_below_multiple_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "max_long_edge.*64"):
            _image_scale_by_multiple_size(1024, 1024, 1.5, "64", 32)

    def test_positive_limits_and_multiples_hold_for_varied_source_sizes(self):
        for source in ((150, 75), (1000, 777), (2010, 1000), (2040, 2030)):
            for multiple in (8, 16, 32, 64):
                for limit in (multiple, 160, 2016, 2044):
                    for scale in (0.01, 0.75, 1.01, 1.2, 8.0):
                        with self.subTest(source=source, multiple=multiple, limit=limit, scale=scale):
                            width, height, _ = _image_scale_by_multiple_size(
                                *source, scale, str(multiple), limit,
                            )
                            self.assertLessEqual(max(width, height), limit)
                            self.assertGreater(min(width, height), 0)
                            self.assertEqual(width % multiple, 0)
                            self.assertEqual(height % multiple, 0)

    def test_node_honors_limit_before_allocating_resized_image(self):
        try:
            import torch
        except ModuleNotFoundError:
            self.skipTest("torch is not installed in this test environment")

        image = torch.zeros((1, 75, 150, 3), dtype=torch.float32)
        output, width, height, _ = EasyUseAnimaImageScaleByMultiple().upscale(
            image, scale_by=1.2, multiple="64", max_long_edge=160,
        )
        self.assertEqual((width, height), (128, 64))
        self.assertEqual(tuple(output.shape), (1, 64, 128, 3))

        with patch("easyuse_anima.image.upscale._common_upscale_image") as resize:
            with self.assertRaisesRegex(ValueError, "max_long_edge.*64"):
                EasyUseAnimaImageScaleByMultiple().upscale(image, multiple="64", max_long_edge=32)
        resize.assert_not_called()

    def test_shifted_widget_values_are_normalized(self):
        self.assertEqual(
            _normalize_image_scale_options("32", "32", "bicubic"),
            ("bicubic", "32", 0),
        )
        self.assertEqual(
            _normalize_image_scale_options(2048, "bicubic", "32"),
            ("bicubic", "32", 2048),
        )

    def test_output_dimensions_are_multiple_when_exact_ratio_is_impractical(self):
        self.assertEqual(
            _image_scale_by_multiple_size(1000, 777, 1.5, "32"),
            (1504, 1152, 1.4933127413127414),
        )

    def test_outputs_aligned_image_and_dimensions(self):
        try:
            import torch
        except ModuleNotFoundError:
            self.skipTest("torch is not installed in this test environment")

        image = torch.zeros((1, 777, 1000, 3), dtype=torch.float32)

        output, width, height, applied_scale = EasyUseAnimaImageScaleByMultiple().upscale(
            image,
            scale_by=1.5,
            max_long_edge=0,
            upscale_method="bilinear",
            multiple="32",
        )

        self.assertEqual((width, height), (1504, 1152))
        self.assertEqual(tuple(output.shape), (1, 1152, 1504, 3))
        self.assertAlmostEqual(applied_scale, 1.4933127413127414)
        self.assertEqual(output.dtype, image.dtype)

    def test_node_adapter_delegates_to_shared_operation(self):
        expected = (object(), 128, 192, 1.5)
        image = object()

        with patch.object(
            image_nodes,
            "_upscale_image_by_multiple",
            return_value=expected,
        ) as upscale:
            result = EasyUseAnimaImageScaleByMultiple().upscale(
                image,
                1.5,
                "lanczos",
                "64",
                2048,
            )

        self.assertIs(result, expected)
        upscale.assert_called_once_with(image, 1.5, "lanczos", "64", 2048)


if __name__ == "__main__":
    unittest.main()
