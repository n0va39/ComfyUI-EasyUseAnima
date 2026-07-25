# pyright: strict
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, ClassVar, Protocol, TypeAlias, cast

from .generation_pipeline import (
    GenerationCapabilities,
    GenerationRequest,
    GenerationState,
)

UpscalePreview: TypeAlias = Callable[[str, object], None]
ImageSizeResolver: TypeAlias = Callable[[object, int, int], tuple[int, int]]
ImageEncoder: TypeAlias = Callable[[object, object], object]


class UpscaleRunner(Protocol):
    def __call__(
        self,
        model: object,
        clip: object,
        vae: object,
        positive: object,
        negative: object,
        image: object,
        sampler_settings: dict[str, Any],
        upscale_settings: dict[str, Any],
        quality_tags: str = "",
        quality_neg: str = "",
        prompt_data: str | dict[str, Any] | None = None,
        *,
        exclude_positive_quality: bool = False,
        exclude_negative_quality: bool = False,
    ) -> tuple[object, dict[str, Any]]: ...


@dataclass(frozen=True, slots=True)
class UpscaleRuntime:
    run_upscale: UpscaleRunner
    image_size: ImageSizeResolver
    encode_image: ImageEncoder


@dataclass(frozen=True, slots=True)
class AIOUpscaleStage:
    runtime: UpscaleRuntime
    exclude_positive_quality: bool
    exclude_negative_quality: bool
    add_preview: UpscalePreview | None = None

    name: ClassVar[str] = "upscale"

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
        upscale = cast(dict[str, Any], request.config.upscale.to_dict())
        prompt_data = cast(dict[str, Any], request.prompts.prompt_data)

        image, metadata = self.runtime.run_upscale(
            request.resources.model,
            request.resources.clip,
            request.resources.vae,
            request.conditioning.positive,
            request.conditioning.negative,
            state.image,
            sampler,
            upscale,
            request.prompts.quality_tags,
            request.prompts.quality_negative,
            prompt_data,
            exclude_positive_quality=self.exclude_positive_quality,
            exclude_negative_quality=self.exclude_negative_quality,
        )
        latent = state.latent
        width = state.width
        height = state.height
        if metadata.get("enabled"):
            width, height = self.runtime.image_size(image, width, height)
            latent = self.runtime.encode_image(request.resources.vae, image)
            if (
                request.config.preview.intermediate_images
                and self.add_preview is not None
            ):
                self.add_preview(self.name, image)

        state.latent = latent
        state.image = image
        state.width = width
        state.height = height
        state.metadata[self.name] = metadata


__all__ = ()
