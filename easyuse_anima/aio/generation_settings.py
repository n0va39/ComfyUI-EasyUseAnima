# pyright: strict
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from .generation_detailer import AIOGenerationDetailerConfig
from .generation_features import (
    AIOGenerationArtistMixConfig,
    AIOGenerationHighresConfig,
    AIOGenerationModelPatchesConfig,
    AIOGenerationModGuidanceConfig,
    AIOGenerationPostprocessConfig,
    AIOGenerationUpscaleConfig,
)
from .generation_output import AIOGenerationPreviewConfig, AIOGenerationSaveConfig
from .generation_sampling import AIOGenerationSamplerConfig
from .generation_values import ObjectState, expect_int, expect_str, required


@dataclass(frozen=True, slots=True)
class AIOGenerationConfig:
    state: ObjectState
    schema: str
    version: int
    mode: str
    sampler: AIOGenerationSamplerConfig
    model_patches: AIOGenerationModelPatchesConfig
    mod_guidance: AIOGenerationModGuidanceConfig
    artist_mix: AIOGenerationArtistMixConfig
    highres: AIOGenerationHighresConfig
    upscale: AIOGenerationUpscaleConfig
    postprocess: AIOGenerationPostprocessConfig
    detailer: AIOGenerationDetailerConfig
    save: AIOGenerationSaveConfig
    preview: AIOGenerationPreviewConfig

    @classmethod
    def from_dict(cls, source: Mapping[str, object]) -> AIOGenerationConfig:
        known = (
            "schema", "version", "mode", "sampler", "model_patches", "mod_guidance",
            "artist_mix", "highres", "upscale", "postprocess", "detailer", "save", "preview",
        )
        return cls(
            state=ObjectState.from_source(source, known),
            schema=expect_str(required(source, "schema"), "schema"),
            version=expect_int(required(source, "version"), "version"),
            mode=expect_str(required(source, "mode"), "mode"),
            sampler=AIOGenerationSamplerConfig.from_value(required(source, "sampler")),
            model_patches=AIOGenerationModelPatchesConfig.from_value(required(source, "model_patches")),
            mod_guidance=AIOGenerationModGuidanceConfig.from_value(required(source, "mod_guidance")),
            artist_mix=AIOGenerationArtistMixConfig.from_value(required(source, "artist_mix")),
            highres=AIOGenerationHighresConfig.from_value(required(source, "highres")),
            upscale=AIOGenerationUpscaleConfig.from_value(required(source, "upscale")),
            postprocess=AIOGenerationPostprocessConfig.from_value(required(source, "postprocess")),
            detailer=AIOGenerationDetailerConfig.from_value(required(source, "detailer")),
            save=AIOGenerationSaveConfig.from_value(required(source, "save")),
            preview=AIOGenerationPreviewConfig.from_value(required(source, "preview")),
        )

    def to_dict(self) -> dict[str, object]:
        return self.state.compose({
            "schema": self.schema, "version": self.version, "mode": self.mode,
            "sampler": self.sampler.to_dict(),
            "model_patches": self.model_patches.to_dict(),
            "mod_guidance": self.mod_guidance.to_dict(),
            "artist_mix": self.artist_mix.to_dict(), "highres": self.highres.to_dict(),
            "upscale": self.upscale.to_dict(), "postprocess": self.postprocess.to_dict(),
            "detailer": self.detailer.to_dict(), "save": self.save.to_dict(),
            "preview": self.preview.to_dict(),
        })


def _aio_generation_config_from_dict(
    value: Mapping[str, object],
) -> AIOGenerationConfig:
    """Freeze one already-normalized payload into its typed v1 representation."""

    return AIOGenerationConfig.from_dict(value)


def _aio_generation_config_to_dict(
    config: AIOGenerationConfig,
) -> dict[str, object]:
    """Return a new mutable JSON object without sharing nested state."""

    return config.to_dict()


def round_trip_aio_generation_settings(
    value: Mapping[str, object],
) -> dict[str, object]:
    return _aio_generation_config_to_dict(_aio_generation_config_from_dict(value))


__all__ = ()
