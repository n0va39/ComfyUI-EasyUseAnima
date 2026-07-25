# pyright: strict
from __future__ import annotations

from dataclasses import dataclass

from .generation_values import (
    FrozenJsonObject,
    JsonNumber,
    ObjectState,
    expect_bool,
    expect_int,
    expect_number,
    expect_object,
    expect_str,
    freeze_object,
    required,
    thaw_object,
)


@dataclass(frozen=True, slots=True)
class AIOGenerationSpectrumConfig:
    state: ObjectState
    enabled: bool
    window_size: JsonNumber
    flex_window: JsonNumber
    warmup_steps: int
    tail_actual_steps: int
    blend_w: JsonNumber
    cheby_degree: int
    ridge_lambda: JsonNumber
    history_size: int
    one_sampler_only: bool
    verbose: bool
    compat_policy: str

    @classmethod
    def from_value(cls, value: object, key: str) -> AIOGenerationSpectrumConfig:
        source = expect_object(value, key)
        known = (
            "enabled", "window_size", "flex_window", "warmup_steps",
            "tail_actual_steps", "blend_w", "cheby_degree", "ridge_lambda",
            "history_size", "one_sampler_only", "verbose", "compat_policy",
        )
        return cls(
            state=ObjectState.from_source(source, known),
            enabled=expect_bool(required(source, "enabled"), f"{key}.enabled"),
            window_size=expect_number(required(source, "window_size"), f"{key}.window_size"),
            flex_window=expect_number(required(source, "flex_window"), f"{key}.flex_window"),
            warmup_steps=expect_int(required(source, "warmup_steps"), f"{key}.warmup_steps"),
            tail_actual_steps=expect_int(required(source, "tail_actual_steps"), f"{key}.tail_actual_steps"),
            blend_w=expect_number(required(source, "blend_w"), f"{key}.blend_w"),
            cheby_degree=expect_int(required(source, "cheby_degree"), f"{key}.cheby_degree"),
            ridge_lambda=expect_number(required(source, "ridge_lambda"), f"{key}.ridge_lambda"),
            history_size=expect_int(required(source, "history_size"), f"{key}.history_size"),
            one_sampler_only=expect_bool(required(source, "one_sampler_only"), f"{key}.one_sampler_only"),
            verbose=expect_bool(required(source, "verbose"), f"{key}.verbose"),
            compat_policy=expect_str(required(source, "compat_policy"), f"{key}.compat_policy"),
        )

    def to_dict(self) -> dict[str, object]:
        return self.state.compose({
            "enabled": self.enabled, "window_size": self.window_size,
            "flex_window": self.flex_window, "warmup_steps": self.warmup_steps,
            "tail_actual_steps": self.tail_actual_steps, "blend_w": self.blend_w,
            "cheby_degree": self.cheby_degree, "ridge_lambda": self.ridge_lambda,
            "history_size": self.history_size, "one_sampler_only": self.one_sampler_only,
            "verbose": self.verbose, "compat_policy": self.compat_policy,
        })


@dataclass(frozen=True, slots=True)
class AIOGenerationSPDConfig:
    state: ObjectState
    split_mode: str
    scale: JsonNumber
    sigma: JsonNumber
    adaptive_smc_alpha: JsonNumber

    @classmethod
    def from_value(cls, value: object, key: str) -> AIOGenerationSPDConfig:
        source = expect_object(value, key)
        known = ("split_mode", "scale", "sigma", "adaptive_smc_alpha")
        return cls(
            state=ObjectState.from_source(source, known),
            split_mode=expect_str(required(source, "split_mode"), f"{key}.split_mode"),
            scale=expect_number(required(source, "scale"), f"{key}.scale"),
            sigma=expect_number(required(source, "sigma"), f"{key}.sigma"),
            adaptive_smc_alpha=expect_number(
                required(source, "adaptive_smc_alpha"), f"{key}.adaptive_smc_alpha"
            ),
        )

    def to_dict(self) -> dict[str, object]:
        return self.state.compose({
            "split_mode": self.split_mode, "scale": self.scale, "sigma": self.sigma,
            "adaptive_smc_alpha": self.adaptive_smc_alpha,
        })


@dataclass(frozen=True, slots=True)
class AIOGenerationDiTCorrectionsConfig:
    state: ObjectState
    enabled: bool
    dcw_mode: str
    dcw_lambda: JsonNumber
    dcw_band_mask: str
    dcw_calibrator: str
    smc_cfg: bool
    adaptive_smc_alpha: JsonNumber
    smc_cfg_lambda: JsonNumber
    cfgpp: bool
    cfgpp_lambda: JsonNumber
    fsg: bool
    fsg_band_lo: JsonNumber
    fsg_band_hi: JsonNumber
    fsg_k: int
    fsg_d_sigma: JsonNumber
    fsg_gamma: JsonNumber
    replace_existing_cfg: bool

    @classmethod
    def from_value(cls, value: object, key: str) -> AIOGenerationDiTCorrectionsConfig:
        source = expect_object(value, key)
        known = (
            "enabled", "dcw_mode", "dcw_lambda", "dcw_band_mask", "dcw_calibrator",
            "smc_cfg", "adaptive_smc_alpha", "smc_cfg_lambda", "cfgpp", "cfgpp_lambda",
            "fsg", "fsg_band_lo", "fsg_band_hi", "fsg_k", "fsg_d_sigma", "fsg_gamma",
            "replace_existing_cfg",
        )
        return cls(
            state=ObjectState.from_source(source, known),
            enabled=expect_bool(required(source, "enabled"), f"{key}.enabled"),
            dcw_mode=expect_str(required(source, "dcw_mode"), f"{key}.dcw_mode"),
            dcw_lambda=expect_number(required(source, "dcw_lambda"), f"{key}.dcw_lambda"),
            dcw_band_mask=expect_str(required(source, "dcw_band_mask"), f"{key}.dcw_band_mask"),
            dcw_calibrator=expect_str(required(source, "dcw_calibrator"), f"{key}.dcw_calibrator"),
            smc_cfg=expect_bool(required(source, "smc_cfg"), f"{key}.smc_cfg"),
            adaptive_smc_alpha=expect_number(required(source, "adaptive_smc_alpha"), f"{key}.adaptive_smc_alpha"),
            smc_cfg_lambda=expect_number(required(source, "smc_cfg_lambda"), f"{key}.smc_cfg_lambda"),
            cfgpp=expect_bool(required(source, "cfgpp"), f"{key}.cfgpp"),
            cfgpp_lambda=expect_number(required(source, "cfgpp_lambda"), f"{key}.cfgpp_lambda"),
            fsg=expect_bool(required(source, "fsg"), f"{key}.fsg"),
            fsg_band_lo=expect_number(required(source, "fsg_band_lo"), f"{key}.fsg_band_lo"),
            fsg_band_hi=expect_number(required(source, "fsg_band_hi"), f"{key}.fsg_band_hi"),
            fsg_k=expect_int(required(source, "fsg_k"), f"{key}.fsg_k"),
            fsg_d_sigma=expect_number(required(source, "fsg_d_sigma"), f"{key}.fsg_d_sigma"),
            fsg_gamma=expect_number(required(source, "fsg_gamma"), f"{key}.fsg_gamma"),
            replace_existing_cfg=expect_bool(
                required(source, "replace_existing_cfg"), f"{key}.replace_existing_cfg"
            ),
        )

    def to_dict(self) -> dict[str, object]:
        return self.state.compose({
            "enabled": self.enabled, "dcw_mode": self.dcw_mode,
            "dcw_lambda": self.dcw_lambda, "dcw_band_mask": self.dcw_band_mask,
            "dcw_calibrator": self.dcw_calibrator, "smc_cfg": self.smc_cfg,
            "adaptive_smc_alpha": self.adaptive_smc_alpha,
            "smc_cfg_lambda": self.smc_cfg_lambda, "cfgpp": self.cfgpp,
            "cfgpp_lambda": self.cfgpp_lambda, "fsg": self.fsg,
            "fsg_band_lo": self.fsg_band_lo, "fsg_band_hi": self.fsg_band_hi,
            "fsg_k": self.fsg_k, "fsg_d_sigma": self.fsg_d_sigma,
            "fsg_gamma": self.fsg_gamma, "replace_existing_cfg": self.replace_existing_cfg,
        })


@dataclass(frozen=True, slots=True)
class AIOGenerationSamplerConfig:
    state: ObjectState
    backend: str
    seed: int
    seed_after_generate: str
    steps: int
    cfg: JsonNumber
    sampler_name: str
    scheduler: str
    denoise: JsonNumber
    spectrum: AIOGenerationSpectrumConfig
    spd: AIOGenerationSPDConfig
    spectrum_extra: FrozenJsonObject
    spd_extra: FrozenJsonObject
    dit_corrections: AIOGenerationDiTCorrectionsConfig

    @classmethod
    def from_value(cls, value: object) -> AIOGenerationSamplerConfig:
        key = "sampler"
        source = expect_object(value, key)
        known = (
            "backend", "seed", "seed_after_generate", "steps", "cfg", "sampler_name",
            "scheduler", "denoise", "spectrum", "spd", "spectrum_extra", "spd_extra",
            "dit_corrections",
        )
        return cls(
            state=ObjectState.from_source(source, known),
            backend=expect_str(required(source, "backend"), f"{key}.backend"),
            seed=expect_int(required(source, "seed"), f"{key}.seed"),
            seed_after_generate=expect_str(required(source, "seed_after_generate"), f"{key}.seed_after_generate"),
            steps=expect_int(required(source, "steps"), f"{key}.steps"),
            cfg=expect_number(required(source, "cfg"), f"{key}.cfg"),
            sampler_name=expect_str(required(source, "sampler_name"), f"{key}.sampler_name"),
            scheduler=expect_str(required(source, "scheduler"), f"{key}.scheduler"),
            denoise=expect_number(required(source, "denoise"), f"{key}.denoise"),
            spectrum=AIOGenerationSpectrumConfig.from_value(required(source, "spectrum"), f"{key}.spectrum"),
            spd=AIOGenerationSPDConfig.from_value(required(source, "spd"), f"{key}.spd"),
            spectrum_extra=freeze_object(expect_object(required(source, "spectrum_extra"), f"{key}.spectrum_extra")),
            spd_extra=freeze_object(expect_object(required(source, "spd_extra"), f"{key}.spd_extra")),
            dit_corrections=AIOGenerationDiTCorrectionsConfig.from_value(
                required(source, "dit_corrections"), f"{key}.dit_corrections"
            ),
        )

    def to_dict(self) -> dict[str, object]:
        return self.state.compose({
            "backend": self.backend, "seed": self.seed,
            "seed_after_generate": self.seed_after_generate, "steps": self.steps,
            "cfg": self.cfg, "sampler_name": self.sampler_name,
            "scheduler": self.scheduler, "denoise": self.denoise,
            "spectrum": self.spectrum.to_dict(), "spd": self.spd.to_dict(),
            "spectrum_extra": thaw_object(self.spectrum_extra),
            "spd_extra": thaw_object(self.spd_extra),
            "dit_corrections": self.dit_corrections.to_dict(),
        })
__all__ = ()
