# pyright: strict
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, Protocol, TypeAlias

ModelCleanup: TypeAlias = Callable[[object, object | None], None]
StandaloneModGuidance: TypeAlias = Callable[
    [object, object, object, object, str, str, str],
    object,
]
ComfyModelPatcher: TypeAlias = Callable[
    [object, object, object, dict[str, Any]],
    object,
]
PreviewSender: TypeAlias = Callable[
    [object, str, str, list[dict[str, Any]]],
    None,
]


@dataclass(frozen=True, slots=True)
class StageModelPatchPlan:
    signature: str
    patch_ids: tuple[str, ...]
    payload: object


StageModelPlanFactory: TypeAlias = Callable[
    [dict[str, Any], str],
    StageModelPatchPlan,
]
StageModelPatcher: TypeAlias = Callable[
    [object, StageModelPatchPlan],
    object,
]


def _new_model_list() -> list[object]:
    return []


def _new_variant_cache() -> dict[str, object]:
    return {}


def _new_stage_patch_map() -> dict[str, tuple[str, ...]]:
    return {}


class PreviewSaver(Protocol):
    def __call__(
        self,
        image: object,
        stage: str,
        *,
        workflow_prompt: object | None = None,
        extra_pnginfo: object | None = None,
    ) -> list[dict[str, Any]]: ...


@dataclass(slots=True)
class EphemeralModelRegistry:
    base_model: object
    cleanup_model: ModelCleanup
    base_sample_model: object | None = None
    mod_guidance_model: object | None = None
    model: object | None = None
    model_with_lora: object | None = None
    _registered_models: list[object] = field(
        init=False,
        default_factory=_new_model_list,
    )
    _closed: bool = field(init=False, default=False)

    def register_model(self, model: object) -> object:
        if self._closed:
            raise RuntimeError("AiO model registry is already closed")
        self._registered_models.append(model)
        return model

    @property
    def closed(self) -> bool:
        return self._closed

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        seen_model_ids: set[int] = set()
        for ephemeral_model in (
            self.base_sample_model,
            self.mod_guidance_model,
            self.model,
            *self._registered_models,
            self.model_with_lora,
        ):
            if ephemeral_model is None:
                continue
            key = id(ephemeral_model)
            if key in seen_model_ids:
                continue
            seen_model_ids.add(key)
            self.cleanup_model(ephemeral_model, self.base_model)


@dataclass(frozen=True, slots=True)
class ModelVariantRuntime:
    apply_standalone_mod_guidance: StandaloneModGuidance
    apply_comfy_sampler_patches: ComfyModelPatcher


@dataclass(slots=True)
class ModelVariantResolver:
    runtime: ModelVariantRuntime
    registry: EphemeralModelRegistry
    model: object
    clip: object
    positive: object
    negative: object
    quality_tags: str
    quality_negative: str
    profile: str
    use_mod_guidance: bool
    can_apply_standalone_mod_guidance: bool
    _mod_guidance_model: object = field(init=False)

    def __post_init__(self) -> None:
        self._mod_guidance_model = self.model
        self.registry.mod_guidance_model = self.model
        self.registry.register_model(self.model)

    @property
    def mod_guidance_model(self) -> object:
        return self._mod_guidance_model

    def standalone_model(self) -> object:
        if (
            not self.can_apply_standalone_mod_guidance
            or self._mod_guidance_model is not self.model
        ):
            return self._mod_guidance_model
        resolved = self.runtime.apply_standalone_mod_guidance(
            self.model,
            self.clip,
            self.positive,
            self.negative,
            self.quality_tags,
            self.quality_negative,
            self.profile,
        )
        self._mod_guidance_model = resolved
        self.registry.mod_guidance_model = resolved
        self.registry.register_model(resolved)
        return resolved

    def for_backend(self, backend: str) -> tuple[object, bool]:
        if backend == "spectrum_mod_guidance_advanced":
            if self._mod_guidance_model is not self.model:
                return self._mod_guidance_model, False
            return self.model, self.use_mod_guidance
        return self.standalone_model(), False

    def prepare_first_pass(
        self,
        backend: str,
        sampler_settings: dict[str, Any],
    ) -> tuple[object, bool]:
        sample_model, use_mod_guidance = self.for_backend(backend)
        if backend == "comfy_ksampler":
            sample_model = self.runtime.apply_comfy_sampler_patches(
                sample_model,
                self.clip,
                self.positive,
                sampler_settings,
            )
        self.registry.base_sample_model = sample_model
        self.registry.register_model(sample_model)
        return sample_model, use_mod_guidance


@dataclass(frozen=True, slots=True)
class StageModelVariantRuntime:
    build_plan: StageModelPlanFactory
    apply_plan: StageModelPatcher


@dataclass(slots=True)
class StageModelVariantResolver:
    runtime: StageModelVariantRuntime
    registry: EphemeralModelRegistry
    model_with_lora: object
    settings: dict[str, Any]
    max_variants: int = 4
    _variants: dict[str, object] = field(
        init=False,
        default_factory=_new_variant_cache,
    )
    _patches_by_stage: dict[str, tuple[str, ...]] = field(
        init=False,
        default_factory=_new_stage_patch_map,
    )

    def resolve(self, stage_id: str) -> object:
        if self.registry.closed:
            raise RuntimeError("AiO model registry is already closed")
        plan = self.runtime.build_plan(self.settings, stage_id)
        self._patches_by_stage[stage_id] = plan.patch_ids
        existing = self._variants.get(plan.signature)
        if existing is not None:
            return existing
        if len(self._variants) >= self.max_variants:
            raise RuntimeError("AiO stage MODEL variant limit exceeded")
        resolved = self.runtime.apply_plan(self.model_with_lora, plan)
        self._variants[plan.signature] = resolved
        if self.registry.model is None:
            self.registry.model = resolved
        self.registry.register_model(resolved)
        return resolved

    def patch_ids(self, stage_id: str) -> tuple[str, ...]:
        return self._patches_by_stage.get(stage_id, ())


@dataclass(frozen=True, slots=True)
class PreviewRuntime:
    save_temp_preview: PreviewSaver
    send_preview_event: PreviewSender


@dataclass(frozen=True, slots=True)
class PreviewCollector:
    runtime: PreviewRuntime
    previews: list[dict[str, object]]
    node_id: object
    run_id: str
    workflow_prompt: object | None
    extra_pnginfo: object | None

    def add(self, stage: str, image: object) -> None:
        images = self.runtime.save_temp_preview(
            image,
            stage,
            workflow_prompt=self.workflow_prompt,
            extra_pnginfo=self.extra_pnginfo,
        )
        if images:
            self.previews.extend(images)
            self.runtime.send_preview_event(
                self.node_id,
                self.run_id,
                stage,
                images,
            )


__all__ = ()
