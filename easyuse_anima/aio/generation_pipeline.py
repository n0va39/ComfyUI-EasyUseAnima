# pyright: strict
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import ClassVar, Protocol, TypeAlias

from .generation_settings import AIOGenerationConfig

AIO_GENERATION_STAGE_ORDER = (
    "first_pass",
    "highres",
    "detailer",
    "upscale",
    "postprocess",
    "save_output",
)


def _new_metadata() -> dict[str, object]:
    return {}


def _new_previews() -> list[dict[str, object]]:
    return []


def _new_extensions() -> dict[str, object]:
    return {}


@dataclass(frozen=True, slots=True)
class PromptExecutionData:
    prompt_data: Mapping[str, object]
    positive_prompt: str
    negative_prompt: str
    quality_tags: str
    quality_negative: str
    metadata_positive_prompt: str
    metadata_negative_prompt: str
    use_anima_mod_guidance: bool
    use_negative_anima_mod_guidance: bool


@dataclass(frozen=True, slots=True)
class ResourceBundle:
    base_model: object
    base_clip: object
    model_with_lora: object
    model: object
    clip: object
    vae: object
    applied_loras: tuple[Mapping[str, object], ...]


@dataclass(frozen=True, slots=True)
class ConditioningBundle:
    positive: object
    negative: object


@dataclass(frozen=True, slots=True)
class WorkflowContext:
    input_context: Mapping[str, object]
    lora_stack: object | None
    workflow_prompt: object | None
    extra_pnginfo: object | None
    unique_id: object | None
    cache_scope: str


@dataclass(frozen=True, slots=True)
class GenerationRequest:
    config: AIOGenerationConfig
    prompts: PromptExecutionData
    resources: ResourceBundle
    conditioning: ConditioningBundle
    workflow: WorkflowContext


@dataclass(slots=True)
class GenerationState:
    latent: object | None
    image: object | None
    width: int
    height: int
    metadata: dict[str, object] = field(default_factory=_new_metadata)
    previews: list[dict[str, object]] = field(default_factory=_new_previews)
    extensions: dict[str, object] = field(default_factory=_new_extensions)


GenerationCapabilities: TypeAlias = Mapping[str, object]


class GenerationStage(Protocol):
    name: ClassVar[str]

    def validate(
        self,
        request: GenerationRequest,
        capabilities: GenerationCapabilities,
    ) -> None: ...

    def run(
        self,
        request: GenerationRequest,
        state: GenerationState,
    ) -> None: ...


__all__ = (
    "AIO_GENERATION_STAGE_ORDER",
    "ConditioningBundle",
    "GenerationCapabilities",
    "GenerationRequest",
    "GenerationStage",
    "GenerationState",
    "PromptExecutionData",
    "ResourceBundle",
    "WorkflowContext",
)
