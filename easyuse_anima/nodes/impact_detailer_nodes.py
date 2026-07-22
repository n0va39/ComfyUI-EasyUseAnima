"""Internal ComfyUI adapter for Impact Pack Detailer delegation."""

from __future__ import annotations

import logging
from typing import Any

from ..common.values import _as_bool
from ..image.detailer import _EasyUseAnimaAlignedDetailerHook
from ..image.geometry import _alignment_value
from ..image.sam3 import _call_impact_detailer, _find_impact_detailer_class
from ..infrastructure.comfy.capabilities import _comfy_sampler_names

logger = logging.getLogger("ComfyUI-EasyUseAnima")


def _unbound_runtime(*_args, **_kwargs) -> Any:
    raise RuntimeError("Impact Detailer node runtime dependencies are not bound.")


_comfy_max_resolution = _unbound_runtime
_impact_scheduler_names = _unbound_runtime


def _bind_impact_detailer_node_runtime(*, resolve_helper) -> None:
    def runtime_helper(name):
        def call(*args, **kwargs):
            return resolve_helper(name)(*args, **kwargs)

        return call

    for name in ("_comfy_max_resolution", "_impact_scheduler_names"):
        globals()[name] = runtime_helper(name)


class _EasyUseAnimaImpactDetailerDelegate:
    """Internal Impact Pack DetailerForEach delegate used by SAM3 nodes."""

    DESCRIPTION = (
        "Internal Impact Pack DetailerForEach delegate used by EasyUse Anima SAM3 nodes."
    )
    OUTPUT_TOOLTIPS = (
        "Enhanced image returned by Impact Pack DetailerForEach.",
    )

    @classmethod
    def INPUT_TYPES(cls):
        max_resolution = _comfy_max_resolution()
        return {
            "required": {
                "image": ("IMAGE",),
                "segs": ("SEGS",),
                "model": ("MODEL", {
                    "tooltip": "Model passed through to Impact Pack DetailerForEach.",
                }),
                "clip": ("CLIP",),
                "vae": ("VAE",),
                "guide_size": ("FLOAT", {
                    "default": 512,
                    "min": 64,
                    "max": max_resolution,
                    "step": 8,
                    "tooltip": "Target guide size for the detailed crop.",
                }),
                "guide_size_for": ("BOOLEAN", {
                    "default": True,
                    "label_on": "bbox",
                    "label_off": "crop_region",
                    "tooltip": "Use the bbox or crop region as the guide-size basis.",
                }),
                "max_size": ("FLOAT", {
                    "default": 1024,
                    "min": 64,
                    "max": max_resolution,
                    "step": 8,
                    "tooltip": "Maximum crop size before sampling.",
                }),
                "seed": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 0xffffffffffffffff,
                }),
                "steps": ("INT", {
                    "default": 20,
                    "min": 1,
                    "max": 10000,
                }),
                "cfg": ("FLOAT", {
                    "default": 8.0,
                    "min": 0.0,
                    "max": 100.0,
                }),
                "sampler_name": (_comfy_sampler_names(),),
                "scheduler": (_impact_scheduler_names(),),
                "positive": ("CONDITIONING",),
                "negative": ("CONDITIONING",),
                "denoise": ("FLOAT", {
                    "default": 0.5,
                    "min": 0.0001,
                    "max": 1.0,
                    "step": 0.01,
                }),
                "feather": ("INT", {
                    "default": 5,
                    "min": 0,
                    "max": 100,
                    "step": 1,
                }),
                "noise_mask": ("BOOLEAN", {
                    "default": True,
                    "label_on": "enabled",
                    "label_off": "disabled",
                }),
                "force_inpaint": ("BOOLEAN", {
                    "default": True,
                    "label_on": "enabled",
                    "label_off": "disabled",
                }),
                "wildcard": ("STRING", {
                    "multiline": True,
                    "default": "",
                    "dynamicPrompts": False,
                }),
                "cycle": ("INT", {
                    "default": 1,
                    "min": 1,
                    "max": 10,
                    "step": 1,
                }),
                "alignment": (["impact", "none", "8", "16", "32", "64"], {
                    "default": "impact",
                    "tooltip": (
                        "Align the Impact detail crop sampling size upward. "
                        "Use 32 for ANIMA/Spectrum safety, or impact/none for pass-through."
                    ),
                }),
                "preserve_conditioning_metadata": ("BOOLEAN", {
                    "default": True,
                    "tooltip": (
                        "Reserved safety flag for the native ANIMA backend. "
                        "The current Impact backend passes conditioning through to Impact Pack."
                    ),
                }),
                "fail_on_unsupported_opt": ("BOOLEAN", {
                    "default": False,
                    "tooltip": "Raise an error instead of warning when a native-backend-only option is requested.",
                }),
            },
            "optional": {
                "detailer_hook": ("DETAILER_HOOK",),
                "inpaint_model": ("BOOLEAN", {
                    "default": False,
                    "label_on": "enabled",
                    "label_off": "disabled",
                }),
                "noise_mask_feather": ("INT", {
                    "default": 20,
                    "min": 0,
                    "max": 100,
                    "step": 1,
                }),
                "scheduler_func_opt": ("SCHEDULER_FUNC",),
                "tiled_encode": ("BOOLEAN", {
                    "default": False,
                    "label_on": "enabled",
                    "label_off": "disabled",
                }),
                "tiled_decode": ("BOOLEAN", {
                    "default": False,
                    "label_on": "enabled",
                    "label_off": "disabled",
                }),
            },
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("image",)
    FUNCTION = "doit"
    CATEGORY = "EasyUse Anima/Detailer"

    def doit(
        self,
        image,
        segs,
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
        alignment_text = str(alignment or "impact")
        alignment_int = _alignment_value(alignment_text)

        if not _as_bool(preserve_conditioning_metadata, True):
            logger.warning(
                "[EasyUseAnima] preserve_conditioning_metadata=false is reserved for a native backend; "
                "the Impact backend leaves conditioning handling to Impact Pack."
            )

        effective_detailer_hook = detailer_hook
        if alignment_int is not None:
            effective_detailer_hook = _EasyUseAnimaAlignedDetailerHook(detailer_hook, alignment_int)

        detailer_cls = _find_impact_detailer_class()
        detailer = detailer_cls()
        result = _call_impact_detailer(
            detailer,
            image=image,
            segs=segs,
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
            detailer_hook=effective_detailer_hook,
            inpaint_model=inpaint_model,
            noise_mask_feather=noise_mask_feather,
            scheduler_func_opt=scheduler_func_opt,
            tiled_encode=tiled_encode,
            tiled_decode=tiled_decode,
        )
        if isinstance(result, dict):
            value = result.get("result")
            if isinstance(value, tuple) and value:
                return (value[0],)
        if isinstance(result, tuple):
            if not result:
                raise RuntimeError("[EasyUseAnima] Impact DetailerForEach returned an empty tuple.")
            return (result[0],)
        return (result,)


__all__ = ()
