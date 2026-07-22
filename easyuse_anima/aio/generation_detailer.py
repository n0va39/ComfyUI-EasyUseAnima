# pyright: strict
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import cast

from .generation_sampling import (
    AIOGenerationDiTCorrectionsConfig,
    AIOGenerationSpectrumConfig,
)
from .generation_values import (
    JsonNumber,
    ObjectState,
    expect_bool,
    expect_int,
    expect_number,
    expect_object,
    expect_str,
    expect_string_list,
    required,
)


@dataclass(frozen=True, slots=True)
class AIOGenerationSAM3Config:
    state: ObjectState
    context: str
    checkpoint: str

    @classmethod
    def from_value(cls, value: object, key: str) -> AIOGenerationSAM3Config:
        source = expect_object(value, key)
        known = ("context", "checkpoint")
        return cls(
            state=ObjectState.from_source(source, known),
            context=expect_str(required(source, "context"), f"{key}.context"),
            checkpoint=expect_str(required(source, "checkpoint"), f"{key}.checkpoint"),
        )

    def to_dict(self) -> dict[str, object]:
        return self.state.compose({"context": self.context, "checkpoint": self.checkpoint})


@dataclass(frozen=True, slots=True)
class AIOGenerationDetailerTargetConfig:
    state: ObjectState
    label: str
    enabled: bool
    detect_prompt: str
    detect_count: int
    threshold: JsonNumber
    refine_iterations: int
    individual_masks: bool
    combined: bool
    crop_factor: JsonNumber
    bbox_fill: bool
    drop_size: int
    contour_fill: bool
    guide_size: int
    guide_size_for: bool
    max_size: int
    steps: int
    inherit_sampler_settings: bool
    cfg: JsonNumber
    sampler_name: str
    scheduler: str
    denoise: JsonNumber
    feather: int
    noise_mask: bool
    force_inpaint: bool
    wildcard: str
    cycle: int
    alignment: str
    inpaint_model: bool
    noise_mask_feather: int
    tiled_encode: bool
    tiled_decode: bool
    spectrum: AIOGenerationSpectrumConfig
    dit_corrections: AIOGenerationDiTCorrectionsConfig

    @classmethod
    def from_value(cls, value: object, key: str) -> AIOGenerationDetailerTargetConfig:
        source = expect_object(value, key)
        known = (
            "label", "enabled", "detect_prompt", "detect_count", "threshold",
            "refine_iterations", "individual_masks", "combined", "crop_factor",
            "bbox_fill", "drop_size", "contour_fill", "guide_size", "guide_size_for",
            "max_size", "steps", "inherit_sampler_settings", "cfg", "sampler_name",
            "scheduler", "denoise", "feather", "noise_mask", "force_inpaint", "wildcard",
            "cycle", "alignment", "inpaint_model", "noise_mask_feather", "tiled_encode",
            "tiled_decode", "spectrum", "dit_corrections",
        )
        return cls(
            state=ObjectState.from_source(source, known),
            label=expect_str(required(source, "label"), f"{key}.label"),
            enabled=expect_bool(required(source, "enabled"), f"{key}.enabled"),
            detect_prompt=expect_str(required(source, "detect_prompt"), f"{key}.detect_prompt"),
            detect_count=expect_int(required(source, "detect_count"), f"{key}.detect_count"),
            threshold=expect_number(required(source, "threshold"), f"{key}.threshold"),
            refine_iterations=expect_int(required(source, "refine_iterations"), f"{key}.refine_iterations"),
            individual_masks=expect_bool(required(source, "individual_masks"), f"{key}.individual_masks"),
            combined=expect_bool(required(source, "combined"), f"{key}.combined"),
            crop_factor=expect_number(required(source, "crop_factor"), f"{key}.crop_factor"),
            bbox_fill=expect_bool(required(source, "bbox_fill"), f"{key}.bbox_fill"),
            drop_size=expect_int(required(source, "drop_size"), f"{key}.drop_size"),
            contour_fill=expect_bool(required(source, "contour_fill"), f"{key}.contour_fill"),
            guide_size=expect_int(required(source, "guide_size"), f"{key}.guide_size"),
            guide_size_for=expect_bool(required(source, "guide_size_for"), f"{key}.guide_size_for"),
            max_size=expect_int(required(source, "max_size"), f"{key}.max_size"),
            steps=expect_int(required(source, "steps"), f"{key}.steps"),
            inherit_sampler_settings=expect_bool(
                required(source, "inherit_sampler_settings"), f"{key}.inherit_sampler_settings"
            ),
            cfg=expect_number(required(source, "cfg"), f"{key}.cfg"),
            sampler_name=expect_str(required(source, "sampler_name"), f"{key}.sampler_name"),
            scheduler=expect_str(required(source, "scheduler"), f"{key}.scheduler"),
            denoise=expect_number(required(source, "denoise"), f"{key}.denoise"),
            feather=expect_int(required(source, "feather"), f"{key}.feather"),
            noise_mask=expect_bool(required(source, "noise_mask"), f"{key}.noise_mask"),
            force_inpaint=expect_bool(required(source, "force_inpaint"), f"{key}.force_inpaint"),
            wildcard=expect_str(required(source, "wildcard"), f"{key}.wildcard"),
            cycle=expect_int(required(source, "cycle"), f"{key}.cycle"),
            alignment=expect_str(required(source, "alignment"), f"{key}.alignment"),
            inpaint_model=expect_bool(required(source, "inpaint_model"), f"{key}.inpaint_model"),
            noise_mask_feather=expect_int(
                required(source, "noise_mask_feather"), f"{key}.noise_mask_feather"
            ),
            tiled_encode=expect_bool(required(source, "tiled_encode"), f"{key}.tiled_encode"),
            tiled_decode=expect_bool(required(source, "tiled_decode"), f"{key}.tiled_decode"),
            spectrum=AIOGenerationSpectrumConfig.from_value(required(source, "spectrum"), f"{key}.spectrum"),
            dit_corrections=AIOGenerationDiTCorrectionsConfig.from_value(
                required(source, "dit_corrections"), f"{key}.dit_corrections"
            ),
        )

    def to_dict(self) -> dict[str, object]:
        return self.state.compose({
            "label": self.label, "enabled": self.enabled,
            "detect_prompt": self.detect_prompt, "detect_count": self.detect_count,
            "threshold": self.threshold, "refine_iterations": self.refine_iterations,
            "individual_masks": self.individual_masks, "combined": self.combined,
            "crop_factor": self.crop_factor, "bbox_fill": self.bbox_fill,
            "drop_size": self.drop_size, "contour_fill": self.contour_fill,
            "guide_size": self.guide_size, "guide_size_for": self.guide_size_for,
            "max_size": self.max_size, "steps": self.steps,
            "inherit_sampler_settings": self.inherit_sampler_settings, "cfg": self.cfg,
            "sampler_name": self.sampler_name, "scheduler": self.scheduler,
            "denoise": self.denoise, "feather": self.feather,
            "noise_mask": self.noise_mask, "force_inpaint": self.force_inpaint,
            "wildcard": self.wildcard, "cycle": self.cycle,
            "alignment": self.alignment, "inpaint_model": self.inpaint_model,
            "noise_mask_feather": self.noise_mask_feather,
            "tiled_encode": self.tiled_encode, "tiled_decode": self.tiled_decode,
            "spectrum": self.spectrum.to_dict(),
            "dit_corrections": self.dit_corrections.to_dict(),
        })


@dataclass(frozen=True, slots=True)
class AIOGenerationDetailerTarget:
    name: str
    settings: AIOGenerationDetailerTargetConfig


def _is_detailer_target_name(name: str) -> bool:
    return name in {"face", "eye"} or (
        name.startswith("custom_") and name[len("custom_") :].isdecimal()
    )


@dataclass(frozen=True, slots=True)
class AIOGenerationDetailerConfig:
    state: ObjectState
    enabled: bool
    order: tuple[str, ...]
    sam3: AIOGenerationSAM3Config
    targets: tuple[AIOGenerationDetailerTarget, ...]

    @classmethod
    def from_value(cls, value: object) -> AIOGenerationDetailerConfig:
        key = "detailer"
        source = expect_object(value, key)
        targets = tuple(
            AIOGenerationDetailerTarget(
                name=name,
                settings=AIOGenerationDetailerTargetConfig.from_value(
                    cast(object, target_value), f"{key}.{name}"
                ),
            )
            for name, target_value in source.items()
            if _is_detailer_target_name(name) and isinstance(target_value, Mapping)
        )
        known = ("enabled", "order", "sam3", *(target.name for target in targets))
        return cls(
            state=ObjectState.from_source(source, known),
            enabled=expect_bool(required(source, "enabled"), f"{key}.enabled"),
            order=expect_string_list(required(source, "order"), f"{key}.order"),
            sam3=AIOGenerationSAM3Config.from_value(required(source, "sam3"), f"{key}.sam3"),
            targets=targets,
        )

    def to_dict(self) -> dict[str, object]:
        known_values: dict[str, object] = {
            "enabled": self.enabled, "order": list(self.order), "sam3": self.sam3.to_dict(),
        }
        known_values.update({target.name: target.settings.to_dict() for target in self.targets})
        return self.state.compose(known_values)
__all__ = ()
