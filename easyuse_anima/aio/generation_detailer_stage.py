# pyright: strict
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, ClassVar, TypeAlias, cast

from .generation_pipeline import (
    GenerationCapabilities,
    GenerationRequest,
    GenerationState,
)

DetailerPreview: TypeAlias = Callable[[str, object], None]
DetailerRunner: TypeAlias = Callable[
    [
        object,
        object,
        object,
        object,
        object,
        object,
        dict[str, Any],
        dict[str, Any],
        DetailerPreview | None,
    ],
    tuple[object, dict[str, Any]],
]
ImageSizeResolver: TypeAlias = Callable[[object, int, int], tuple[int, int]]


@dataclass(frozen=True, slots=True)
class DetailerRuntime:
    run_detailer: DetailerRunner
    image_size: ImageSizeResolver


@dataclass(frozen=True, slots=True)
class AIODetailerStage:
    runtime: DetailerRuntime
    add_preview: DetailerPreview | None = None

    name: ClassVar[str] = "detailer"

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
        detailer = cast(dict[str, Any], request.config.detailer.to_dict())
        preview_callback = (
            self.add_preview
            if request.config.preview.intermediate_images
            else None
        )

        image, metadata = self.runtime.run_detailer(
            request.resources.model,
            request.resources.clip,
            request.resources.vae,
            request.conditioning.positive,
            request.conditioning.negative,
            state.image,
            sampler,
            detailer,
            preview_callback,
        )
        width = state.width
        height = state.height
        if metadata.get("enabled"):
            width, height = self.runtime.image_size(image, width, height)

        state.image = image
        state.width = width
        state.height = height
        state.metadata[self.name] = metadata


__all__ = ()
