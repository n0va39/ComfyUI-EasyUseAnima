# pyright: strict
from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, ClassVar, TypeAlias, cast

from .generation_pipeline import (
    GenerationCapabilities,
    GenerationRequest,
    GenerationState,
)

FirstPassCacheGetter: TypeAlias = Callable[
    [str],
    tuple[object, object] | None,
]
FirstPassCacheSetter: TypeAlias = Callable[[str, object, object], None]
FirstPassEmptyLatent: TypeAlias = Callable[[int, int], object]
FirstPassSampler: TypeAlias = Callable[
    [
        object,
        object,
        object,
        object,
        object,
        dict[str, Any],
        dict[str, Any],
        bool,
        str,
        str,
    ],
    object,
]
FirstPassDecoder: TypeAlias = Callable[[object, object], object]
FirstPassResizer: TypeAlias = Callable[
    [object, int, int, str],
    tuple[object, bool],
]
FirstPassEncoder: TypeAlias = Callable[[object, object], object]
FirstPassPreview: TypeAlias = Callable[[str, object], None]

logger = logging.getLogger("ComfyUI-EasyUseAnima")


@dataclass(frozen=True, slots=True)
class FirstPassRuntime:
    get_cache: FirstPassCacheGetter
    put_cache: FirstPassCacheSetter
    generate_empty_latent: FirstPassEmptyLatent
    sample_latent: FirstPassSampler
    decode_latent: FirstPassDecoder
    resize_image: FirstPassResizer
    encode_image: FirstPassEncoder


@dataclass(frozen=True, slots=True)
class AIOFirstPassStage:
    runtime: FirstPassRuntime
    cache_key: str
    use_mod_guidance: bool
    add_preview: FirstPassPreview | None = None

    name: ClassVar[str] = "first_pass"

    def validate(
        self,
        request: GenerationRequest,
        capabilities: GenerationCapabilities,
    ) -> None:
        del capabilities
        if request.config.mode != "txt2img":
            raise RuntimeError(
                "[EasyUseAnima] AiO Generator draft currently supports txt2img only."
            )

    def run(
        self,
        request: GenerationRequest,
        state: GenerationState,
    ) -> None:
        sampler = cast(dict[str, Any], request.config.sampler.to_dict())
        sampler["cfg"] = request.config.negpip.effective_cfg(sampler.get("cfg"))
        mod_guidance = cast(
            dict[str, Any],
            request.config.mod_guidance.to_dict(),
        )
        quality_negative = (
            request.prompts.quality_negative
            if request.prompts.use_negative_anima_mod_guidance
            else ""
        )

        cached_first_pass = self.runtime.get_cache(self.cache_key)
        cache_hit = cached_first_pass is not None
        if cached_first_pass is not None:
            latent, image = cached_first_pass
        else:
            latent_image = self.runtime.generate_empty_latent(
                state.width,
                state.height,
            )
            latent = self.runtime.sample_latent(
                request.resources.model,
                request.resources.clip,
                request.conditioning.positive,
                request.conditioning.negative,
                latent_image,
                sampler,
                mod_guidance,
                self.use_mod_guidance,
                request.prompts.quality_tags,
                quality_negative,
            )
            image = self.runtime.decode_latent(
                request.resources.vae,
                latent,
            )

        image, resized = self.runtime.resize_image(
            image,
            state.width,
            state.height,
            "bicubic",
        )
        if resized:
            latent = self.runtime.encode_image(
                request.resources.vae,
                image,
            )
        if not cache_hit or resized:
            try:
                self.runtime.put_cache(self.cache_key, latent, image)
            except Exception as exc:
                logger.debug(
                    "[EasyUseAnima] failed to store AiO first-pass cache: %s",
                    exc,
                )

        state.latent = latent
        state.image = image
        state.metadata[self.name] = {"cache_hit": cache_hit}
        if (
            request.config.preview.intermediate_images
            and self.add_preview is not None
        ):
            self.add_preview(self.name, image)


__all__ = ()
