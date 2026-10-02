"""ComfyUI node adapter for the optional first-pass IP-Adapter hook."""

from ..aio.hooks.contracts import EASYUSE_ANIMA_AIO_HOOK_TYPE
from ..aio.ipadapter_hook import IPAdapterHook


class EasyAnimaIPAdapterHook:
    DESCRIPTION = (
        "Connect LuciferTC's Anima IP-Adapter Loader and one reference image to AiO aio_hook. "
        "First pass only; 28-block Anima, default CUDA, standard CFG, no Compile/dynamic VRAM. "
        "Requires the reviewed external node version; see the IP-Adapter Hook guide."
    )

    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "ip_adapter": ("ANIMA_IP_ADAPTER",),
            "ref_image": ("IMAGE",),
            "strength": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 2.0, "step": 0.05}),
            "ref_image_size": ("INT", {"default": 512, "min": 224, "max": 2048, "step": 16}),
            "siglip_layer": ("INT", {"default": -1, "min": -1, "max": 24}),
            "ip_cfg_scale": ("FLOAT", {"default": 4.0, "min": 1.0, "max": 10.0, "step": 0.05}),
            "ip_cfg_separate": ("BOOLEAN", {"default": False}),
            "gray_null": ("BOOLEAN", {"default": False}),
            "use_lora": ("BOOLEAN", {"default": True}),
        }}

    RETURN_TYPES = (EASYUSE_ANIMA_AIO_HOOK_TYPE,)
    RETURN_NAMES = ("aio_hook",)
    FUNCTION = "build"
    CATEGORY = "EasyUse Anima/AiO/Extensions"

    def build(self, ip_adapter, ref_image, strength, ref_image_size=512, siglip_layer=-1,
              ip_cfg_scale=4.0, ip_cfg_separate=False, gray_null=False, use_lora=True):
        if ref_image_size % 16:
            raise ValueError("Reference image size must be a multiple of 16.")
        return (IPAdapterHook(ip_adapter, ref_image, {
            "strength": strength, "ref_image_size": ref_image_size,
            "siglip_layer": siglip_layer, "ip_cfg_scale": ip_cfg_scale,
            "ip_cfg_separate": ip_cfg_separate, "gray_null": gray_null, "use_lora": use_lora,
        }),)


__all__ = ("EasyAnimaIPAdapterHook",)
