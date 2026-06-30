import unittest

from nodes import (
    EasyUseAnimaImageScaleByMultiple,
    _image_scale_by_multiple_size,
    _normalize_image_scale_options,
)


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


if __name__ == "__main__":
    unittest.main()
