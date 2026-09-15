"""Generic image saving and metadata adapters for the native output engine."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ..aio.native_image_output import (
    NativeImageMetadata,
    _build_native_metadata,
    _comfy_metadata_enabled,
    _save_native_images,
)


@dataclass(frozen=True, slots=True)
class _ImageMetadataInput:
    metadata: NativeImageMetadata


class EasyUseAnimaImageMetadata:
    """Build model-independent A1111 metadata without saving an image."""

    DESCRIPTION = (
        "Builds A1111-compatible generation metadata for Easy Save Image. Connect the "
        "same final images to both nodes so the recorded dimensions match. PNG uses "
        "text metadata; JPEG and WebP use EXIF. Works with any diffusion model. "
        "ComfyUI's disable-metadata setting suppresses metadata and resource hashing."
    )
    OUTPUT_TOOLTIPS = (
        "A1111 generation metadata only; workflow saving is configured on Easy Save Image.",
        "Human-readable A1111 generation parameters.",
    )

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "images": ("IMAGE", {"tooltip": "Final images whose dimensions are recorded."}),
                "positive": ("STRING", {"default": "", "multiline": True}),
                "negative": ("STRING", {"default": "", "multiline": True}),
                "modelname": ("STRING", {
                    "default": "", "tooltip": "Model name from ComfyUI's model inventory; no arbitrary file paths.",
                }),
                "seed": ("INT", {
                    "default": 0, "min": 0, "max": 0xFFFFFFFFFFFFFFFF,
                    "control_after_generate": False,
                    "tooltip": "The seed used to generate the image; never randomized by this metadata node.",
                }),
                "steps": ("INT", {"default": 20, "min": 1, "max": 10000}),
                "cfg": ("FLOAT", {"default": 7.0, "min": 0.0, "max": 100.0, "step": 0.1}),
                "sampler_name": ("STRING", {"default": "euler"}),
                "scheduler_name": ("STRING", {"default": "normal"}),
                "denoise": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 1.0, "step": 0.01}),
                "clip_skip": ("INT", {"default": 0, "min": 0, "max": 256}),
                "custom": ("STRING", {"default": "", "multiline": True}),
            },
            "optional": {
                "additional_hashes": ("STRING", {
                    "forceInput": True,
                    "tooltip": "Optional name:hash:weight entries from Easy Civitai Lookup.",
                }),
            },
        }

    RETURN_TYPES = ("EASYUSE_IMAGE_METADATA", "STRING")
    RETURN_NAMES = ("exif_metadata", "parameters")
    FUNCTION = "build"
    CATEGORY = "EasyUse Anima/Image"

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        return _comfy_metadata_enabled()

    def build(
        self, images, positive="", negative="", modelname="", seed=0,
        steps=20, cfg=7.0, sampler_name="euler", scheduler_name="normal",
        denoise=1.0, clip_skip=0, custom="", additional_hashes="",
        **_legacy_workflow_options,
    ):
        shape = getattr(images, "shape", ())
        if len(shape) != 4 or any(int(size) <= 0 for size in shape):
            raise ValueError("[EasyUseAnima] Metadata requires a non-empty IMAGE batch.")
        metadata = NativeImageMetadata(parameters="", final_hashes="", hashes={})
        if _comfy_metadata_enabled():
            metadata = _build_native_metadata(
                modelname=modelname, positive=positive, negative=negative,
                width=int(shape[2]), height=int(shape[1]), seed=seed,
                steps=steps, cfg=cfg, sampler_name=sampler_name,
                scheduler_name=scheduler_name, denoise=denoise,
                clip_skip=clip_skip, custom=custom, additional_hashes=additional_hashes,
                applied_loras=None, download_civitai_data=False, easy_remix=False,
                include_resource_weights=True,
            )
        return (
            _ImageMetadataInput(metadata),
            metadata.parameters,
        )


class EasyUseAnimaSaveImage:
    """Save images with optional metadata supplied through a dedicated socket."""

    DESCRIPTION = (
        "Saves images to ComfyUI's output directory using PNG, JPEG or WebP. "
        "Connect Easy Image Metadata to exif_metadata to include A1111 generation data. "
        "Workflow embedding and JSON sidecars are controlled here independently. "
        "Existing files are preserved by allocating a numbered filename."
    )

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "images": ("IMAGE",),
                "path": ("STRING", {
                    "default": "", "tooltip": "Optional subfolder under ComfyUI's output directory.",
                }),
                "filename": ("STRING", {
                    "default": "Easy", "tooltip": "Filename without extension. Existing files receive a numbered suffix.",
                }),
                "extension": (["png", "jpg", "jpeg", "webp"],),
                "quality": ("INT", {
                    "default": 95, "min": 1, "max": 100,
                    "tooltip": "JPEG/WebP quality. PNG is always lossless.",
                }),
                "lossless_webp": ("BOOLEAN", {"default": False}),
                "optimize_png": ("BOOLEAN", {
                    "default": False, "tooltip": "Use slower PNG compression to reduce file size.",
                }),
                "embed_workflow": ("BOOLEAN", {"default": True}),
                "save_workflow_as_json": ("BOOLEAN", {"default": False}),
            },
            "optional": {
                "exif_metadata": ("EASYUSE_IMAGE_METADATA", {
                    "tooltip": "Optional A1111 metadata from Easy Image Metadata. Workflow options are independent.",
                }),
            },
            "hidden": {"prompt": "PROMPT", "extra_pnginfo": "EXTRA_PNGINFO"},
        }

    RETURN_TYPES = ()
    FUNCTION = "save_images"
    OUTPUT_NODE = True
    CATEGORY = "EasyUse Anima/Image"

    def save_images(
        self, images, path="", filename="Easy", extension="png", quality=95,
        lossless_webp=False, optimize_png=False, exif_metadata=None,
        prompt=None, extra_pnginfo=None, embed_workflow=True,
        save_workflow_as_json=False,
    ):
        import folder_paths  # type: ignore

        if exif_metadata is not None and not isinstance(exif_metadata, _ImageMetadataInput):
            raise ValueError("[EasyUseAnima] Connect Easy Image Metadata to exif_metadata.")
        metadata_enabled = _comfy_metadata_enabled() and bool(
            exif_metadata is not None or embed_workflow or save_workflow_as_json
        )
        metadata = NativeImageMetadata(parameters="", final_hashes="", hashes={})
        if metadata_enabled and exif_metadata is not None:
            metadata = exif_metadata.metadata
        result = _save_native_images(
            images, output_root=Path(folder_paths.get_output_directory()),
            path=path, filename=filename, extension=extension,
            quality_jpeg_or_webp=quality, lossless_webp=lossless_webp,
            optimize_png=optimize_png,
            embed_workflow=embed_workflow,
            save_workflow_as_json=save_workflow_as_json,
            metadata=metadata, prompt=prompt, extra_pnginfo=extra_pnginfo,
            metadata_enabled=metadata_enabled,
        )
        return {"ui": result["ui"]}


__all__ = ("EasyUseAnimaImageMetadata", "EasyUseAnimaSaveImage")
