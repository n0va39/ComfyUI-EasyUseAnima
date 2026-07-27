# pyright: strict
from __future__ import annotations

from dataclasses import dataclass

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
    required,
)


@dataclass(frozen=True, slots=True)
class AIOGenerationAuraFlowConfig:
    state: ObjectState
    shift: JsonNumber

    @classmethod
    def from_value(cls, value: object, key: str) -> AIOGenerationAuraFlowConfig:
        source = expect_object(value, key)
        return cls(
            state=ObjectState.from_source(source, ("shift",)),
            shift=expect_number(required(source, "shift"), f"{key}.shift"),
        )

    def to_dict(self) -> dict[str, object]:
        return self.state.compose({"shift": self.shift})


@dataclass(frozen=True, slots=True)
class AIOGenerationStageScopeConfig:
    state: ObjectState
    first_pass: bool
    highres: bool
    detailer: bool
    upscale: bool

    @classmethod
    def from_value(cls, value: object, key: str) -> AIOGenerationStageScopeConfig:
        source = expect_object(value, key)
        known = ("first_pass", "highres", "detailer", "upscale")
        return cls(
            state=ObjectState.from_source(source, known),
            first_pass=expect_bool(required(source, "first_pass"), f"{key}.first_pass"),
            highres=expect_bool(required(source, "highres"), f"{key}.highres"),
            detailer=expect_bool(required(source, "detailer"), f"{key}.detailer"),
            upscale=expect_bool(required(source, "upscale"), f"{key}.upscale"),
        )

    def to_dict(self) -> dict[str, object]:
        return self.state.compose({
            "first_pass": self.first_pass,
            "highres": self.highres,
            "detailer": self.detailer,
            "upscale": self.upscale,
        })


@dataclass(frozen=True, slots=True)
class AIOGenerationDAVEConfig:
    state: ObjectState
    enabled: bool
    mask: str
    strength: JsonNumber
    tau: JsonNumber
    stage_scope: AIOGenerationStageScopeConfig

    @classmethod
    def from_value(cls, value: object, key: str) -> AIOGenerationDAVEConfig:
        source = expect_object(value, key)
        known = ("enabled", "mask", "strength", "tau", "stage_scope")
        return cls(
            state=ObjectState.from_source(source, known),
            enabled=expect_bool(required(source, "enabled"), f"{key}.enabled"),
            mask=expect_str(required(source, "mask"), f"{key}.mask"),
            strength=expect_number(required(source, "strength"), f"{key}.strength"),
            tau=expect_number(required(source, "tau"), f"{key}.tau"),
            stage_scope=AIOGenerationStageScopeConfig.from_value(
                required(source, "stage_scope"),
                f"{key}.stage_scope",
            ),
        )

    def to_dict(self) -> dict[str, object]:
        return self.state.compose({
            "enabled": self.enabled, "mask": self.mask,
            "strength": self.strength, "tau": self.tau,
            "stage_scope": self.stage_scope.to_dict(),
        })


@dataclass(frozen=True, slots=True)
class AIOGenerationSafePAGConfig:
    state: ObjectState
    enabled: bool
    scale: JsonNumber
    block_indices: str
    perturbation_strength: JsonNumber
    head_indices: str
    start_percent: JsonNumber
    end_percent: JsonNumber
    rescale: JsonNumber
    rescale_mode: str
    stage_scope: AIOGenerationStageScopeConfig

    @classmethod
    def from_value(cls, value: object, key: str) -> AIOGenerationSafePAGConfig:
        source = expect_object(value, key)
        known = (
            "enabled", "scale", "block_indices", "perturbation_strength", "head_indices",
            "start_percent", "end_percent", "rescale", "rescale_mode", "stage_scope",
        )
        return cls(
            state=ObjectState.from_source(source, known),
            enabled=expect_bool(required(source, "enabled"), f"{key}.enabled"),
            scale=expect_number(required(source, "scale"), f"{key}.scale"),
            block_indices=expect_str(required(source, "block_indices"), f"{key}.block_indices"),
            perturbation_strength=expect_number(
                required(source, "perturbation_strength"), f"{key}.perturbation_strength"
            ),
            head_indices=expect_str(required(source, "head_indices"), f"{key}.head_indices"),
            start_percent=expect_number(required(source, "start_percent"), f"{key}.start_percent"),
            end_percent=expect_number(required(source, "end_percent"), f"{key}.end_percent"),
            rescale=expect_number(required(source, "rescale"), f"{key}.rescale"),
            rescale_mode=expect_str(required(source, "rescale_mode"), f"{key}.rescale_mode"),
            stage_scope=AIOGenerationStageScopeConfig.from_value(
                required(source, "stage_scope"),
                f"{key}.stage_scope",
            ),
        )

    def to_dict(self) -> dict[str, object]:
        return self.state.compose({
            "enabled": self.enabled, "scale": self.scale,
            "block_indices": self.block_indices,
            "perturbation_strength": self.perturbation_strength,
            "head_indices": self.head_indices, "start_percent": self.start_percent,
            "end_percent": self.end_percent, "rescale": self.rescale,
            "rescale_mode": self.rescale_mode,
            "stage_scope": self.stage_scope.to_dict(),
        })


@dataclass(frozen=True, slots=True)
class AIOGenerationTorchCompileConfig:
    state: ObjectState
    enabled: bool
    backend: str
    fullgraph: bool
    mode: str
    dynamic: str
    compile_transformer_blocks_only: bool
    dynamo_cache_size_limit: int
    debug_compile_keys: bool
    disable_dynamic_vram: bool

    @classmethod
    def from_value(cls, value: object, key: str) -> AIOGenerationTorchCompileConfig:
        source = expect_object(value, key)
        known = (
            "enabled", "backend", "fullgraph", "mode", "dynamic",
            "compile_transformer_blocks_only", "dynamo_cache_size_limit",
            "debug_compile_keys", "disable_dynamic_vram",
        )
        return cls(
            state=ObjectState.from_source(source, known),
            enabled=expect_bool(required(source, "enabled"), f"{key}.enabled"),
            backend=expect_str(required(source, "backend"), f"{key}.backend"),
            fullgraph=expect_bool(required(source, "fullgraph"), f"{key}.fullgraph"),
            mode=expect_str(required(source, "mode"), f"{key}.mode"),
            dynamic=expect_str(required(source, "dynamic"), f"{key}.dynamic"),
            compile_transformer_blocks_only=expect_bool(
                required(source, "compile_transformer_blocks_only"),
                f"{key}.compile_transformer_blocks_only",
            ),
            dynamo_cache_size_limit=expect_int(
                required(source, "dynamo_cache_size_limit"), f"{key}.dynamo_cache_size_limit"
            ),
            debug_compile_keys=expect_bool(
                required(source, "debug_compile_keys"), f"{key}.debug_compile_keys"
            ),
            disable_dynamic_vram=expect_bool(
                required(source, "disable_dynamic_vram"), f"{key}.disable_dynamic_vram"
            ),
        )

    def to_dict(self) -> dict[str, object]:
        return self.state.compose({
            "enabled": self.enabled, "backend": self.backend, "fullgraph": self.fullgraph,
            "mode": self.mode, "dynamic": self.dynamic,
            "compile_transformer_blocks_only": self.compile_transformer_blocks_only,
            "dynamo_cache_size_limit": self.dynamo_cache_size_limit,
            "debug_compile_keys": self.debug_compile_keys,
            "disable_dynamic_vram": self.disable_dynamic_vram,
        })


@dataclass(frozen=True, slots=True)
class AIOGenerationKJConfig:
    state: ObjectState
    fp16_accumulation: bool
    sage_attention: str
    sage_allow_compile: bool
    torch_compile: AIOGenerationTorchCompileConfig

    @classmethod
    def from_value(cls, value: object, key: str) -> AIOGenerationKJConfig:
        source = expect_object(value, key)
        known = ("fp16_accumulation", "sage_attention", "sage_allow_compile", "torch_compile")
        return cls(
            state=ObjectState.from_source(source, known),
            fp16_accumulation=expect_bool(
                required(source, "fp16_accumulation"), f"{key}.fp16_accumulation"
            ),
            sage_attention=expect_str(required(source, "sage_attention"), f"{key}.sage_attention"),
            sage_allow_compile=expect_bool(
                required(source, "sage_allow_compile"), f"{key}.sage_allow_compile"
            ),
            torch_compile=AIOGenerationTorchCompileConfig.from_value(
                required(source, "torch_compile"), f"{key}.torch_compile"
            ),
        )

    def to_dict(self) -> dict[str, object]:
        return self.state.compose({
            "fp16_accumulation": self.fp16_accumulation,
            "sage_attention": self.sage_attention,
            "sage_allow_compile": self.sage_allow_compile,
            "torch_compile": self.torch_compile.to_dict(),
        })


@dataclass(frozen=True, slots=True)
class AIOGenerationModelPatchesConfig:
    state: ObjectState
    aura_flow: AIOGenerationAuraFlowConfig
    dave: AIOGenerationDAVEConfig
    safe_pag: AIOGenerationSafePAGConfig
    kj: AIOGenerationKJConfig

    @classmethod
    def from_value(cls, value: object) -> AIOGenerationModelPatchesConfig:
        key = "model_patches"
        source = expect_object(value, key)
        known = ("aura_flow", "dave", "safe_pag", "kj")
        return cls(
            state=ObjectState.from_source(source, known),
            aura_flow=AIOGenerationAuraFlowConfig.from_value(required(source, "aura_flow"), f"{key}.aura_flow"),
            dave=AIOGenerationDAVEConfig.from_value(required(source, "dave"), f"{key}.dave"),
            safe_pag=AIOGenerationSafePAGConfig.from_value(required(source, "safe_pag"), f"{key}.safe_pag"),
            kj=AIOGenerationKJConfig.from_value(required(source, "kj"), f"{key}.kj"),
        )

    def to_dict(self) -> dict[str, object]:

        return self.state.compose({
            "aura_flow": self.aura_flow.to_dict(), "dave": self.dave.to_dict(),
            "safe_pag": self.safe_pag.to_dict(), "kj": self.kj.to_dict(),
        })


@dataclass(frozen=True, slots=True)
class AIOGenerationModGuidanceAdvancedConfig:
    state: ObjectState
    adapter: str
    quality_tags: str
    quality_neg: str
    mod_w: JsonNumber
    mod_start_layer: int
    mod_end_layer: int
    mod_taper: int
    mod_taper_scale: JsonNumber
    mod_final_w: JsonNumber

    @classmethod
    def from_value(cls, value: object, key: str) -> AIOGenerationModGuidanceAdvancedConfig:
        source = expect_object(value, key)
        known = (
            "adapter", "quality_tags", "quality_neg", "mod_w", "mod_start_layer",
            "mod_end_layer", "mod_taper", "mod_taper_scale", "mod_final_w",
        )
        return cls(
            state=ObjectState.from_source(source, known),
            adapter=expect_str(required(source, "adapter"), f"{key}.adapter"),
            quality_tags=expect_str(required(source, "quality_tags"), f"{key}.quality_tags"),
            quality_neg=expect_str(required(source, "quality_neg"), f"{key}.quality_neg"),
            mod_w=expect_number(required(source, "mod_w"), f"{key}.mod_w"),
            mod_start_layer=expect_int(required(source, "mod_start_layer"), f"{key}.mod_start_layer"),
            mod_end_layer=expect_int(required(source, "mod_end_layer"), f"{key}.mod_end_layer"),
            mod_taper=expect_int(required(source, "mod_taper"), f"{key}.mod_taper"),
            mod_taper_scale=expect_number(required(source, "mod_taper_scale"), f"{key}.mod_taper_scale"),
            mod_final_w=expect_number(required(source, "mod_final_w"), f"{key}.mod_final_w"),
        )

    def to_dict(self) -> dict[str, object]:
        return self.state.compose({
            "adapter": self.adapter, "quality_tags": self.quality_tags,
            "quality_neg": self.quality_neg, "mod_w": self.mod_w,
            "mod_start_layer": self.mod_start_layer, "mod_end_layer": self.mod_end_layer,
            "mod_taper": self.mod_taper, "mod_taper_scale": self.mod_taper_scale,
            "mod_final_w": self.mod_final_w,
        })


@dataclass(frozen=True, slots=True)
class AIOGenerationModGuidanceConfig:
    state: ObjectState
    mode: str
    profile: str
    advanced: AIOGenerationModGuidanceAdvancedConfig

    @classmethod
    def from_value(cls, value: object) -> AIOGenerationModGuidanceConfig:
        key = "mod_guidance"
        source = expect_object(value, key)
        known = ("mode", "profile", "advanced")
        return cls(
            state=ObjectState.from_source(source, known),
            mode=expect_str(required(source, "mode"), f"{key}.mode"),
            profile=expect_str(required(source, "profile"), f"{key}.profile"),
            advanced=AIOGenerationModGuidanceAdvancedConfig.from_value(
                required(source, "advanced"), f"{key}.advanced"
            ),
        )

    def to_dict(self) -> dict[str, object]:
        return self.state.compose({
            "mode": self.mode, "profile": self.profile, "advanced": self.advanced.to_dict(),
        })


@dataclass(frozen=True, slots=True)
class AIOGenerationArtistMixConfig:
    state: ObjectState
    mode: str
    start_percent: JsonNumber
    strength_scale: JsonNumber
    style_gain: JsonNumber
    rms_scale_cap: JsonNumber
    exact_top_k: int
    cluster_count: int
    dominant_isolation: bool
    dominant_threshold: JsonNumber

    @classmethod
    def from_value(cls, value: object) -> AIOGenerationArtistMixConfig:
        key = "artist_mix"
        source = expect_object(value, key)
        known = (
            "mode", "start_percent", "strength_scale", "style_gain", "rms_scale_cap",
            "exact_top_k", "cluster_count", "dominant_isolation", "dominant_threshold",
        )
        return cls(
            state=ObjectState.from_source(source, known),
            mode=expect_str(required(source, "mode"), f"{key}.mode"),
            start_percent=expect_number(required(source, "start_percent"), f"{key}.start_percent"),
            strength_scale=expect_number(required(source, "strength_scale"), f"{key}.strength_scale"),
            style_gain=expect_number(required(source, "style_gain"), f"{key}.style_gain"),
            rms_scale_cap=expect_number(required(source, "rms_scale_cap"), f"{key}.rms_scale_cap"),
            exact_top_k=expect_int(required(source, "exact_top_k"), f"{key}.exact_top_k"),
            cluster_count=expect_int(required(source, "cluster_count"), f"{key}.cluster_count"),
            dominant_isolation=expect_bool(
                required(source, "dominant_isolation"), f"{key}.dominant_isolation"
            ),
            dominant_threshold=expect_number(
                required(source, "dominant_threshold"), f"{key}.dominant_threshold"
            ),
        )

    def to_dict(self) -> dict[str, object]:
        return self.state.compose({
            "mode": self.mode, "start_percent": self.start_percent,
            "strength_scale": self.strength_scale, "style_gain": self.style_gain,
            "rms_scale_cap": self.rms_scale_cap, "exact_top_k": self.exact_top_k,
            "cluster_count": self.cluster_count,
            "dominant_isolation": self.dominant_isolation,
            "dominant_threshold": self.dominant_threshold,
        })


@dataclass(frozen=True, slots=True)
class AIOGenerationHighresConfig:
    state: ObjectState
    enabled: bool
    scale_by: JsonNumber
    upscale_method: str
    multiple: str
    max_long_edge: int
    steps: int
    inherit_sampler_settings: bool
    cfg: JsonNumber
    sampler_name: str
    scheduler: str
    denoise: JsonNumber
    spectrum: AIOGenerationSpectrumConfig
    dit_corrections: AIOGenerationDiTCorrectionsConfig

    @classmethod
    def from_value(cls, value: object) -> AIOGenerationHighresConfig:
        key = "highres"
        source = expect_object(value, key)
        known = (
            "enabled", "scale_by", "upscale_method", "multiple", "max_long_edge",
            "steps", "inherit_sampler_settings", "cfg", "sampler_name", "scheduler",
            "denoise", "spectrum", "dit_corrections",
        )
        return cls(
            state=ObjectState.from_source(source, known),
            enabled=expect_bool(required(source, "enabled"), f"{key}.enabled"),
            scale_by=expect_number(required(source, "scale_by"), f"{key}.scale_by"),
            upscale_method=expect_str(required(source, "upscale_method"), f"{key}.upscale_method"),
            multiple=expect_str(required(source, "multiple"), f"{key}.multiple"),
            max_long_edge=expect_int(required(source, "max_long_edge"), f"{key}.max_long_edge"),
            steps=expect_int(required(source, "steps"), f"{key}.steps"),
            inherit_sampler_settings=expect_bool(
                required(source, "inherit_sampler_settings"), f"{key}.inherit_sampler_settings"
            ),
            cfg=expect_number(required(source, "cfg"), f"{key}.cfg"),
            sampler_name=expect_str(required(source, "sampler_name"), f"{key}.sampler_name"),
            scheduler=expect_str(required(source, "scheduler"), f"{key}.scheduler"),
            denoise=expect_number(required(source, "denoise"), f"{key}.denoise"),
            spectrum=AIOGenerationSpectrumConfig.from_value(required(source, "spectrum"), f"{key}.spectrum"),
            dit_corrections=AIOGenerationDiTCorrectionsConfig.from_value(
                required(source, "dit_corrections"), f"{key}.dit_corrections"
            ),
        )

    def to_dict(self) -> dict[str, object]:
        return self.state.compose({
            "enabled": self.enabled, "scale_by": self.scale_by,
            "upscale_method": self.upscale_method, "multiple": self.multiple,
            "max_long_edge": self.max_long_edge, "steps": self.steps,
            "inherit_sampler_settings": self.inherit_sampler_settings, "cfg": self.cfg,
            "sampler_name": self.sampler_name, "scheduler": self.scheduler,
            "denoise": self.denoise, "spectrum": self.spectrum.to_dict(),
            "dit_corrections": self.dit_corrections.to_dict(),
        })


@dataclass(frozen=True, slots=True)
class AIOGenerationUSDUConfig:
    state: ObjectState
    upscale_model_name: str
    auto_tile_size: bool
    prompt_mode: str
    mode_type: str
    auto_tile_target: int
    auto_tile_min: int
    auto_tile_max: int
    tile_width: int
    tile_height: int
    mask_blur: int
    tile_padding: int
    seam_fix_mode: str
    seam_fix_denoise: JsonNumber

    seam_fix_width: int
    seam_fix_mask_blur: int
    seam_fix_padding: int
    force_uniform_tiles: bool
    tiled_decode: bool
    batch_size: int

    @classmethod
    def from_value(cls, value: object, key: str) -> AIOGenerationUSDUConfig:
        source = expect_object(value, key)
        known = (
            "upscale_model_name", "auto_tile_size", "prompt_mode", "mode_type",
            "auto_tile_target", "auto_tile_min", "auto_tile_max", "tile_width",
            "tile_height", "mask_blur", "tile_padding", "seam_fix_mode",
            "seam_fix_denoise", "seam_fix_width", "seam_fix_mask_blur",
            "seam_fix_padding", "force_uniform_tiles", "tiled_decode", "batch_size",
        )
        return cls(
            state=ObjectState.from_source(source, known),
            upscale_model_name=expect_str(required(source, "upscale_model_name"), f"{key}.upscale_model_name"),
            auto_tile_size=expect_bool(required(source, "auto_tile_size"), f"{key}.auto_tile_size"),
            prompt_mode=expect_str(required(source, "prompt_mode"), f"{key}.prompt_mode"),
            mode_type=expect_str(required(source, "mode_type"), f"{key}.mode_type"),
            auto_tile_target=expect_int(required(source, "auto_tile_target"), f"{key}.auto_tile_target"),
            auto_tile_min=expect_int(required(source, "auto_tile_min"), f"{key}.auto_tile_min"),
            auto_tile_max=expect_int(required(source, "auto_tile_max"), f"{key}.auto_tile_max"),
            tile_width=expect_int(required(source, "tile_width"), f"{key}.tile_width"),
            tile_height=expect_int(required(source, "tile_height"), f"{key}.tile_height"),
            mask_blur=expect_int(required(source, "mask_blur"), f"{key}.mask_blur"),
            tile_padding=expect_int(required(source, "tile_padding"), f"{key}.tile_padding"),
            seam_fix_mode=expect_str(required(source, "seam_fix_mode"), f"{key}.seam_fix_mode"),
            seam_fix_denoise=expect_number(required(source, "seam_fix_denoise"), f"{key}.seam_fix_denoise"),
            seam_fix_width=expect_int(required(source, "seam_fix_width"), f"{key}.seam_fix_width"),
            seam_fix_mask_blur=expect_int(required(source, "seam_fix_mask_blur"), f"{key}.seam_fix_mask_blur"),
            seam_fix_padding=expect_int(required(source, "seam_fix_padding"), f"{key}.seam_fix_padding"),
            force_uniform_tiles=expect_bool(required(source, "force_uniform_tiles"), f"{key}.force_uniform_tiles"),
            tiled_decode=expect_bool(required(source, "tiled_decode"), f"{key}.tiled_decode"),
            batch_size=expect_int(required(source, "batch_size"), f"{key}.batch_size"),
        )

    def to_dict(self) -> dict[str, object]:
        return self.state.compose({
            "upscale_model_name": self.upscale_model_name,
            "auto_tile_size": self.auto_tile_size, "prompt_mode": self.prompt_mode,
            "mode_type": self.mode_type, "auto_tile_target": self.auto_tile_target,
            "auto_tile_min": self.auto_tile_min, "auto_tile_max": self.auto_tile_max,
            "tile_width": self.tile_width, "tile_height": self.tile_height,
            "mask_blur": self.mask_blur, "tile_padding": self.tile_padding,
            "seam_fix_mode": self.seam_fix_mode,
            "seam_fix_denoise": self.seam_fix_denoise,
            "seam_fix_width": self.seam_fix_width,
            "seam_fix_mask_blur": self.seam_fix_mask_blur,
            "seam_fix_padding": self.seam_fix_padding,
            "force_uniform_tiles": self.force_uniform_tiles,
            "tiled_decode": self.tiled_decode, "batch_size": self.batch_size,
        })


@dataclass(frozen=True, slots=True)
class AIOGenerationResShiftConfig:
    state: ObjectState
    scale: str
    student_name: str
    dtype: str
    chop: int
    overlap: int
    tile_batch: int

    @classmethod
    def from_value(cls, value: object, key: str) -> AIOGenerationResShiftConfig:
        source = expect_object(value, key)
        known = ("scale", "student_name", "dtype", "chop", "overlap", "tile_batch")
        return cls(
            state=ObjectState.from_source(source, known),
            scale=expect_str(required(source, "scale"), f"{key}.scale"),
            student_name=expect_str(required(source, "student_name"), f"{key}.student_name"),
            dtype=expect_str(required(source, "dtype"), f"{key}.dtype"),
            chop=expect_int(required(source, "chop"), f"{key}.chop"),
            overlap=expect_int(required(source, "overlap"), f"{key}.overlap"),
            tile_batch=expect_int(required(source, "tile_batch"), f"{key}.tile_batch"),
        )

    def to_dict(self) -> dict[str, object]:
        return self.state.compose({
            "scale": self.scale, "student_name": self.student_name, "dtype": self.dtype,
            "chop": self.chop, "overlap": self.overlap, "tile_batch": self.tile_batch,
        })


@dataclass(frozen=True, slots=True)
class AIOGenerationUpscaleConfig:
    state: ObjectState
    enabled: bool
    backend: str
    scale_by: JsonNumber
    steps: int
    inherit_sampler_settings: bool
    cfg: JsonNumber
    sampler_name: str
    scheduler: str
    denoise: JsonNumber
    spectrum: AIOGenerationSpectrumConfig
    dit_corrections: AIOGenerationDiTCorrectionsConfig
    usdu: AIOGenerationUSDUConfig
    resshift: AIOGenerationResShiftConfig

    @classmethod
    def from_value(cls, value: object) -> AIOGenerationUpscaleConfig:
        key = "upscale"
        source = expect_object(value, key)
        known = (
            "enabled", "backend", "scale_by", "steps", "inherit_sampler_settings",
            "cfg", "sampler_name", "scheduler", "denoise", "spectrum",
            "dit_corrections", "usdu", "resshift",
        )
        return cls(
            state=ObjectState.from_source(source, known),
            enabled=expect_bool(required(source, "enabled"), f"{key}.enabled"),
            backend=expect_str(required(source, "backend"), f"{key}.backend"),
            scale_by=expect_number(required(source, "scale_by"), f"{key}.scale_by"),
            steps=expect_int(required(source, "steps"), f"{key}.steps"),
            inherit_sampler_settings=expect_bool(
                required(source, "inherit_sampler_settings"), f"{key}.inherit_sampler_settings"
            ),
            cfg=expect_number(required(source, "cfg"), f"{key}.cfg"),
            sampler_name=expect_str(required(source, "sampler_name"), f"{key}.sampler_name"),
            scheduler=expect_str(required(source, "scheduler"), f"{key}.scheduler"),
            denoise=expect_number(required(source, "denoise"), f"{key}.denoise"),
            spectrum=AIOGenerationSpectrumConfig.from_value(required(source, "spectrum"), f"{key}.spectrum"),
            dit_corrections=AIOGenerationDiTCorrectionsConfig.from_value(
                required(source, "dit_corrections"), f"{key}.dit_corrections"
            ),
            usdu=AIOGenerationUSDUConfig.from_value(required(source, "usdu"), f"{key}.usdu"),
            resshift=AIOGenerationResShiftConfig.from_value(required(source, "resshift"), f"{key}.resshift"),
        )

    def to_dict(self) -> dict[str, object]:
        return self.state.compose({
            "enabled": self.enabled, "backend": self.backend, "scale_by": self.scale_by,
            "steps": self.steps, "inherit_sampler_settings": self.inherit_sampler_settings,
            "cfg": self.cfg, "sampler_name": self.sampler_name,
            "scheduler": self.scheduler, "denoise": self.denoise,
            "spectrum": self.spectrum.to_dict(),
            "dit_corrections": self.dit_corrections.to_dict(),
            "usdu": self.usdu.to_dict(), "resshift": self.resshift.to_dict(),
        })


@dataclass(frozen=True, slots=True)
class AIOGenerationFitConfig:
    state: ObjectState
    mode: str
    max_long_edge: int
    max_megapixels: JsonNumber
    method: str

    @classmethod
    def from_value(cls, value: object, key: str) -> AIOGenerationFitConfig:
        source = expect_object(value, key)
        known = ("mode", "max_long_edge", "max_megapixels", "method")
        return cls(
            state=ObjectState.from_source(source, known),
            mode=expect_str(required(source, "mode"), f"{key}.mode"),
            max_long_edge=expect_int(required(source, "max_long_edge"), f"{key}.max_long_edge"),
            max_megapixels=expect_number(required(source, "max_megapixels"), f"{key}.max_megapixels"),
            method=expect_str(required(source, "method"), f"{key}.method"),
        )

    def to_dict(self) -> dict[str, object]:
        return self.state.compose({
            "mode": self.mode, "max_long_edge": self.max_long_edge,
            "max_megapixels": self.max_megapixels, "method": self.method,
        })


@dataclass(frozen=True, slots=True)
class AIOGenerationPostprocessConfig:
    state: ObjectState
    enabled: bool
    fit: AIOGenerationFitConfig

    @classmethod
    def from_value(cls, value: object) -> AIOGenerationPostprocessConfig:
        key = "postprocess"
        source = expect_object(value, key)
        known = ("enabled", "fit")
        return cls(
            state=ObjectState.from_source(source, known),
            enabled=expect_bool(required(source, "enabled"), f"{key}.enabled"),
            fit=AIOGenerationFitConfig.from_value(required(source, "fit"), f"{key}.fit"),
        )

    def to_dict(self) -> dict[str, object]:
        return self.state.compose({"enabled": self.enabled, "fit": self.fit.to_dict()})
__all__ = ()
