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

HighresRunner: TypeAlias = Callable[
    [
        object,
        object,
        object,
        object,
        object,
        object,
        object,
        int,
        int,
        dict[str, Any],
        dict[str, Any],
        dict[str, Any],
        bool,
        str,
        str,
    ],
    tuple[object, object, int, int, dict[str, Any]],
]
HighresPreview: TypeAlias = Callable[[str, object], None]


@dataclass(frozen=True, slots=True)
class HighresRuntime:
    run_highres: HighresRunner


@dataclass(frozen=True, slots=True)
class AIOHighresStage:
    runtime: HighresRuntime
    use_mod_guidance: bool
    add_preview: HighresPreview | None = None
    preview_before_detailer: bool = False

    name: ClassVar[str] = "highres"

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
        highres = cast(dict[str, Any], request.config.highres.to_dict())
        sampler["cfg"] = request.config.negpip.effective_cfg(sampler.get("cfg"))
        highres["cfg"] = request.config.negpip.effective_cfg(highres.get("cfg"))
        mod_guidance = cast(
            dict[str, Any],
            request.config.mod_guidance.to_dict(),
        )
        quality_negative = (
            request.prompts.quality_negative
            if request.prompts.use_negative_anima_mod_guidance
            else ""
        )

        latent, image, width, height, metadata = self.runtime.run_highres(
            request.resources.model,
            request.resources.clip,
            request.resources.vae,
            request.conditioning.positive,
            request.conditioning.negative,
            state.image,
            state.latent,
            state.width,
            state.height,
            sampler,
            highres,
            mod_guidance,
            self.use_mod_guidance,
            request.prompts.quality_tags,
            quality_negative,
        )
        state.latent = latent
        state.image = image
        state.width = width
        state.height = height
        state.metadata[self.name] = metadata
        if (
            metadata.get("enabled")
            and isinstance(metadata.get("sampler"), dict)
            and request.config.preview.intermediate_images
            and self.preview_before_detailer
            and self.add_preview is not None
        ):
            self.add_preview(self.name, image)


__all__ = ()
