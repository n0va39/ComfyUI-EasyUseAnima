"""Internal ComfyUI adapters for SAM3 detection and Impact detailing."""

from __future__ import annotations

from ..aio.resources import (
    _load_checkpoint_with_comfy,
    _preferred_checkpoint_default,
)
from ..image.sam3 import _sam3_context
from ..image.sam3_detailer import _run_sam3_detailer
from ..infrastructure.comfy.resources import _comfy_checkpoint_names
from ..infrastructure.comfy.wiring import resolve_comfy_host_helper
from .impact_detailer_nodes import _EasyUseAnimaImpactDetailerDelegate


def _missing_host_helper(name: str):
    raise RuntimeError(f"SAM3 node Comfy host helper is unavailable: {name}")


def _comfy_max_resolution() -> int:
    helper = resolve_comfy_host_helper(
        "_comfy_max_resolution",
        _missing_host_helper,
    )
    return helper()


class EasyUseAnimaSAM3Context:
    """Load a native ComfyUI SAM3 checkpoint and expose it as ctx_SAM3."""

    DESCRIPTION = (
        "Loads a SAM3 checkpoint with ComfyUI's native checkpoint loader and returns "
        "an rgthree-compatible context containing the SAM3 model, CLIP, and VAE."
    )
    OUTPUT_TOOLTIPS = (
        "Context dict containing SAM3 model, CLIP, VAE, and checkpoint name.",
        "SAM3 model loaded from the selected checkpoint.",
        "SAM3 CLIP loaded from the selected checkpoint.",
        "VAE loaded from the selected checkpoint.",
    )

    @classmethod
    def INPUT_TYPES(cls):
        checkpoint_names = _comfy_checkpoint_names()
        return {
            "required": {
                "ckpt_name": (checkpoint_names, {
                    "default": _preferred_checkpoint_default(checkpoint_names, "sam3.1_multiplex_fp16.safetensors"),
                    "tooltip": "SAM3 checkpoint to load, for example sam3.1_multiplex_fp16.safetensors.",
                }),
            },
        }

    RETURN_TYPES = ("RGTHREE_CONTEXT", "MODEL", "CLIP", "VAE")
    RETURN_NAMES = ("ctx_SAM3", "sam3_model", "sam3_clip", "sam3_vae")
    FUNCTION = "load"
    CATEGORY = "EasyUse Anima/Detailer"

    def load(self, ckpt_name):
        model, clip, vae = _load_checkpoint_with_comfy(str(ckpt_name))
        return (_sam3_context(model, clip, vae, str(ckpt_name)), model, clip, vae)


class EasyUseAnimaSAM3Detailer:
    """Native SAM3 detection + Impact MaskToSEGS + ANIMA detailer."""

    DESCRIPTION = (
        "Runs native ComfyUI SAM3 text detection, converts the resulting mask to Impact Pack SEGS, "
        "then delegates detailing to Impact Pack DetailerForEach."
    )
    OUTPUT_TOOLTIPS = (
        "Detailed image. If disabled or no SEGS are detected, this is the original image.",
        "Impact-compatible SEGS generated from the SAM3 mask.",
        "SAM3 mask used to build SEGS.",
        "Original input image before detailing.",
    )

    @classmethod
    def INPUT_TYPES(cls):
        max_resolution = _comfy_max_resolution()
        detailer_inputs = _EasyUseAnimaImpactDetailerDelegate.INPUT_TYPES()
        required = {
            "enabled": ("BOOLEAN", {
                "default": True,
                "label_on": "enabled",
                "label_off": "bypass",
                "tooltip": "Disable to return the original image and an empty SEGS output.",
            }),
            "image": ("IMAGE",),
            "ctx_SAM3": ("RGTHREE_CONTEXT", {
                "tooltip": "ctx_SAM3 from the AiO SAM3 detailer path or a compatible rgthree context containing model and clip.",
            }),
            "detect_prompt": ("STRING", {
                "default": "face",
                "multiline": False,
                "dynamicPrompts": False,
                "tooltip": "SAM3 text target. Use comma-separated targets or target:count for per-target detection count.",
            }),
            "detect_count": ("INT", {
                "default": 1,
                "min": 1,
                "max": 64,
                "step": 1,
                "tooltip": "Maximum detections per target when detect_prompt does not already include :count.",
            }),
            "threshold": ("FLOAT", {
                "default": 0.5,
                "min": 0.0,
                "max": 1.0,
                "step": 0.01,
                "tooltip": "SAM3 detection threshold.",
            }),
            "refine_iterations": ("INT", {
                "default": 2,
                "min": 0,
                "max": 5,
                "step": 1,
                "tooltip": "SAM decoder refinement passes. 0 uses raw detector masks.",
            }),
            "individual_masks": ("BOOLEAN", {
                "default": False,
                "label_on": "enabled",
                "label_off": "combined",
                "tooltip": "Ask SAM3 for per-object masks. MaskToSEGS can still split a combined mask by contours.",
            }),
            "combined": ("BOOLEAN", {
                "default": False,
                "label_on": "combined",
                "label_off": "separate",
                "tooltip": "Impact MaskToSEGS combined option.",
            }),
            "crop_factor": ("FLOAT", {
                "default": 3.0,
                "min": 1.0,
                "max": 100.0,
                "step": 0.1,
                "tooltip": "Impact MaskToSEGS crop factor.",
            }),
            "bbox_fill": ("BOOLEAN", {
                "default": False,
                "label_on": "enabled",
                "label_off": "disabled",
                "tooltip": "Impact MaskToSEGS bbox_fill option.",
            }),
            "drop_size": ("INT", {
                "default": 10,
                "min": 1,
                "max": max_resolution,
                "step": 1,
                "tooltip": "Drop detected regions smaller than this size.",
            }),
            "contour_fill": ("BOOLEAN", {
                "default": False,
                "label_on": "enabled",
                "label_off": "disabled",
                "tooltip": "Impact MaskToSEGS contour_fill option.",
            }),
        }

        for key, value in detailer_inputs["required"].items():
            if key in ("image", "segs"):
                continue
            required[key] = value

        return {
            "required": required,
            "optional": detailer_inputs.get("optional", {}),
        }

    RETURN_TYPES = ("IMAGE", "SEGS", "MASK", "IMAGE")
    RETURN_NAMES = ("image", "segs", "mask", "raw_image")
    FUNCTION = "doit"
    CATEGORY = "EasyUse Anima/Detailer"

    def doit(
        self,
        enabled,
        image,
        ctx_SAM3,
        detect_prompt,
        detect_count,
        threshold,
        refine_iterations,
        individual_masks,
        combined,
        crop_factor,
        bbox_fill,
        drop_size,
        contour_fill,
        model,
        clip,
        vae,
        guide_size,
        guide_size_for,
        max_size,
        seed,
        steps,
        cfg,
        sampler_name,
        scheduler,
        positive,
        negative,
        denoise,
        feather,
        noise_mask,
        force_inpaint,
        wildcard,
        cycle=1,
        alignment="impact",
        preserve_conditioning_metadata=True,
        fail_on_unsupported_opt=False,
        detailer_hook=None,
        inpaint_model=False,
        noise_mask_feather=0,
        scheduler_func_opt=None,
        tiled_encode=False,
        tiled_decode=False,
    ):
        return _run_sam3_detailer(
            enabled=enabled,
            image=image,
            ctx_SAM3=ctx_SAM3,
            detect_prompt=detect_prompt,
            detect_count=detect_count,
            threshold=threshold,
            refine_iterations=refine_iterations,
            individual_masks=individual_masks,
            combined=combined,
            crop_factor=crop_factor,
            bbox_fill=bbox_fill,
            drop_size=drop_size,
            contour_fill=contour_fill,
            model=model,
            clip=clip,
            vae=vae,
            guide_size=guide_size,
            guide_size_for=guide_size_for,
            max_size=max_size,
            seed=seed,
            steps=steps,
            cfg=cfg,
            sampler_name=sampler_name,
            scheduler=scheduler,
            positive=positive,
            negative=negative,
            denoise=denoise,
            feather=feather,
            noise_mask=noise_mask,
            force_inpaint=force_inpaint,
            wildcard=wildcard,
            cycle=cycle,
            alignment=alignment,
            preserve_conditioning_metadata=preserve_conditioning_metadata,
            fail_on_unsupported_opt=fail_on_unsupported_opt,
            detailer_hook=detailer_hook,
            inpaint_model=inpaint_model,
            noise_mask_feather=noise_mask_feather,
            scheduler_func_opt=scheduler_func_opt,
            tiled_encode=tiled_encode,
            tiled_decode=tiled_decode,
        )


__all__ = ()
