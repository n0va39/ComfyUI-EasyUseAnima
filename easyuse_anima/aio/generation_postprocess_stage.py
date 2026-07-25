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

PostprocessRunner: TypeAlias = Callable[
    [object, dict[str, Any]],
    tuple[object, dict[str, Any]],
]
BoolNormalizer: TypeAlias = Callable[[object, bool], bool]
ImageSizeResolver: TypeAlias = Callable[[object, int, int], tuple[int, int]]
ImageEncoder: TypeAlias = Callable[[object, object], object]
PostprocessPreview: TypeAlias = Callable[[str, object], None]


@dataclass(frozen=True, slots=True)
class PostprocessRuntime:
    run_postprocess: PostprocessRunner
    as_bool: BoolNormalizer
    image_size: ImageSizeResolver
    encode_image: ImageEncoder


@dataclass(frozen=True, slots=True)
class AIOPostprocessStage:
    runtime: PostprocessRuntime
    will_run_postprocess: bool
    add_preview: PostprocessPreview | None = None

    name: ClassVar[str] = "postprocess"

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
        postprocess = cast(
            dict[str, Any],
            request.config.postprocess.to_dict(),
        )
        image, metadata = self.runtime.run_postprocess(
            state.image,
            postprocess,
        )

        latent = state.latent
        width = state.width
        height = state.height
        if metadata.get("enabled"):
            width, height = self.runtime.image_size(image, width, height)
            fit_metadata = cast(
                dict[str, Any],
                metadata.get("fit") or {},
            )
            changed = self.runtime.as_bool(
                fit_metadata.get("applied"),
                False,
            )
            if changed:
                latent = self.runtime.encode_image(
                    request.resources.vae,
                    image,
                )
            if (
                request.config.preview.intermediate_images
                and changed
                and self.will_run_postprocess
                and self.add_preview is not None
            ):
                self.add_preview(self.name, image)

        state.latent = latent
        state.image = image
        state.width = width
        state.height = height
        state.metadata[self.name] = metadata


__all__ = ()
