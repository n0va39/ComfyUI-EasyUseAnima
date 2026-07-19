"""Impact Pack Detailer hook behavior owned by the image feature."""

from __future__ import annotations

import logging
from typing import Optional

from .geometry import _align_up


logger = logging.getLogger("ComfyUI-EasyUseAnima")


class _EasyUseAnimaAlignedDetailerHook:
    def __init__(self, base_hook, alignment: Optional[int]):
        self.base_hook = base_hook
        self.alignment = int(alignment) if alignment is not None else None

    def __getattr__(self, name):
        if self.base_hook is not None:
            return getattr(self.base_hook, name)
        raise AttributeError(name)

    def touch_scaled_size(self, width, height):
        if self.base_hook is not None and hasattr(self.base_hook, "touch_scaled_size"):
            width, height = self.base_hook.touch_scaled_size(width, height)
        if self.alignment is None:
            return width, height
        aligned_width = _align_up(width, self.alignment)
        aligned_height = _align_up(height, self.alignment)
        if aligned_width != width or aligned_height != height:
            logger.info(
                "[EasyUseAnima] Detailer hook aligned crop size %sx%s -> %sx%s (alignment=%s)",
                width,
                height,
                aligned_width,
                aligned_height,
                self.alignment,
            )
        return aligned_width, aligned_height

    def post_upscale(self, image, noise_mask):
        if self.base_hook is not None and hasattr(self.base_hook, "post_upscale"):
            return self.base_hook.post_upscale(image, noise_mask)
        return image

    def get_skip_sampling(self):
        if self.base_hook is not None and hasattr(self.base_hook, "get_skip_sampling"):
            return self.base_hook.get_skip_sampling()
        return False

    def post_encode(self, latent):
        if self.base_hook is not None and hasattr(self.base_hook, "post_encode"):
            return self.base_hook.post_encode(latent)
        return latent

    def get_custom_sampler(self):
        if self.base_hook is not None and hasattr(self.base_hook, "get_custom_sampler"):
            return self.base_hook.get_custom_sampler()
        return None

    def set_steps(self, steps):
        if self.base_hook is not None and hasattr(self.base_hook, "set_steps"):
            return self.base_hook.set_steps(steps)
        return None

    def cycle_latent(self, latent):
        if self.base_hook is not None and hasattr(self.base_hook, "cycle_latent"):
            return self.base_hook.cycle_latent(latent)
        return latent

    def pre_ksample(self, model, seed, steps, cfg, sampler_name, scheduler, positive, negative, latent, denoise):
        if self.base_hook is not None and hasattr(self.base_hook, "pre_ksample"):
            return self.base_hook.pre_ksample(
                model, seed, steps, cfg, sampler_name, scheduler, positive, negative, latent, denoise
            )
        return model, seed, steps, cfg, sampler_name, scheduler, positive, negative, latent, denoise

    def get_custom_noise(self, seed, noise, is_touched):
        if self.base_hook is not None and hasattr(self.base_hook, "get_custom_noise"):
            return self.base_hook.get_custom_noise(seed, noise, is_touched)
        return noise, is_touched

    def pre_decode(self, latent):
        if self.base_hook is not None and hasattr(self.base_hook, "pre_decode"):
            return self.base_hook.pre_decode(latent)
        return latent

    def post_decode(self, image):
        if self.base_hook is not None and hasattr(self.base_hook, "post_decode"):
            return self.base_hook.post_decode(image)
        return image

    def post_paste(self, image):
        if self.base_hook is not None and hasattr(self.base_hook, "post_paste"):
            return self.base_hook.post_paste(image)
        return image


__all__ = ()
