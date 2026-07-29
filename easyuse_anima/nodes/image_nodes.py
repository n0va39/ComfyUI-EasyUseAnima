"""ComfyUI adapters for image scaling and Detailer alignment."""

from __future__ import annotations

from ..image.detailer import _EasyUseAnimaAlignedDetailerHook
from ..image.geometry import _alignment_value
from ..image.scaling import (
    IMAGE_SCALE_MULTIPLES,
    IMAGE_UPSCALE_METHODS,
)
from ..image.upscale import _upscale_image_by_multiple


class EasyUseAnimaImageScaleByMultiple:
    """Scale an image by the nearest ratio that produces valid size multiples."""

    DESCRIPTION = (
        "Scales an IMAGE by the nearest valid ratio that keeps the source aspect ratio and makes "
        "the output width and height multiples of the selected size. The optional max long edge "
        "limits the selected valid output size. Use multiple 32 for highres or optimization nodes "
        "that require 32-multiple sizes."
    )
    OUTPUT_TOOLTIPS = (
        "Scaled image using the nearest valid ratio.",
        "Final valid image width.",
        "Final valid image height.",
        "Actual scale ratio applied to the image.",
    )

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE", {
                    "tooltip": "Input image to upscale.",
                }),
                "scale_by": ("FLOAT", {
                    "default": 1.5,
                    "min": 0.01,
                    "max": 8.0,
                    "step": 0.01,
                    "tooltip": "Requested image scale ratio. The node uses the nearest valid ratio for the selected multiple.",
                }),
                "upscale_method": (IMAGE_UPSCALE_METHODS, {
                    "default": "bicubic",
                    "tooltip": "Interpolation method used for resizing.",
                }),
                "multiple": (IMAGE_SCALE_MULTIPLES, {
                    "default": "32",
                    "tooltip": "Output width and height must be multiples of this value.",
                }),
                "max_long_edge": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 16384,
                    "step": 32,
                    "tooltip": "Maximum output long edge. Set 0 to disable this limit.",
                }),
            },
        }

    RETURN_TYPES = ("IMAGE", "INT", "INT", "FLOAT")
    RETURN_NAMES = ("image", "width", "height", "applied_scale")
    FUNCTION = "upscale"
    CATEGORY = "EasyUse Anima/Image"

    def upscale(self, image, scale_by=1.5, upscale_method="bicubic", multiple="32", max_long_edge=0):
        return _upscale_image_by_multiple(
            image,
            scale_by,
            upscale_method,
            multiple,
            max_long_edge,
        )


class EasyUseAnimaDetailerAlignHook:
    """Impact Pack DETAILER_HOOK that aligns detail crop sampling sizes upward."""

    DESCRIPTION = (
        "Creates an Impact Pack compatible DETAILER_HOOK that aligns the detailer crop sampling "
        "size upward to a selected multiple. Use alignment 32 for ANIMA/Spectrum workflows that "
        "require 32-multiple latent-safe crop sizes."
    )
    OUTPUT_TOOLTIPS = (
        "Impact Pack compatible DETAILER_HOOK. Connect it to an Impact DetailerForEach-compatible detailer_hook input.",
    )

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "alignment": (["none", "8", "16", "32", "64"], {
                    "default": "32",
                    "tooltip": (
                        "Crop sampling size alignment. 32 is recommended for ANIMA/Spectrum safety; "
                        "none keeps the original Impact Pack size."
                    ),
                }),
            },
            "optional": {
                "detailer_hook": ("DETAILER_HOOK", {
                    "tooltip": "Optional existing Impact Pack detailer hook. It runs before the alignment adjustment.",
                }),
            },
        }

    RETURN_TYPES = ("DETAILER_HOOK",)
    RETURN_NAMES = ("detailer_hook",)
    FUNCTION = "build"
    CATEGORY = "EasyUse Anima/Detailer"

    def build(self, alignment="32", detailer_hook=None):
        alignment_int = _alignment_value(alignment)
        return (_EasyUseAnimaAlignedDetailerHook(detailer_hook, alignment_int),)


__all__ = (
    "EasyUseAnimaDetailerAlignHook",
    "EasyUseAnimaImageScaleByMultiple",
)
