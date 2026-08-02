"""Canonical contracts for explicitly connected AiO Generator hooks."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from enum import Enum
from typing import Protocol, TypeAlias

AIO_HOOK_API_VERSION = 1
EASYUSE_ANIMA_AIO_HOOK_TYPE = "EASYUSE_ANIMA_AIO_HOOK"

JsonScalar: TypeAlias = str | int | float | bool | None
JsonValue: TypeAlias = JsonScalar | list["JsonValue"] | dict[str, "JsonValue"]


class AioStage(str, Enum):
    """Stage identifiers dispatched by AiO Hook API v1."""

    POSTPROCESS = "postprocess"


class AioStagePhase(str, Enum):
    BEFORE = "before"
    AFTER = "after"


@dataclass(frozen=True, slots=True)
class AioHookPoint:
    """One explicit stage/phase pair requested by a hook."""

    stage: AioStage
    phase: AioStagePhase


@dataclass(frozen=True, slots=True, kw_only=True)
class AioHookDescriptor:
    """Stable identity, dispatch, and whole-node cache contract for a hook."""

    hook_id: str
    hook_version: str
    points: frozenset[AioHookPoint] = field(default_factory=frozenset)
    api_version: int = AIO_HOOK_API_VERSION
    fingerprint: JsonValue | None = None


class _UnsetType:
    __slots__ = ()

    def __repr__(self) -> str:
        return "UNSET"


UNSET = _UnsetType()


@dataclass(frozen=True, slots=True, kw_only=True)
class AioHookPatch:
    """A shape-preserving image replacement and namespaced metadata additions."""

    image: object = UNSET
    metadata: Mapping[str, JsonValue] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class AioHookRequestView:
    """Read-only projection of one normalized generator request."""

    mode: str
    node_id: str | None
    settings: Mapping[str, object]


@dataclass(frozen=True, slots=True)
class AioHookStateView:
    """Read-only stage state. Return an :class:`AioHookPatch` to change it."""

    image: object | None
    width: int
    height: int
    metadata: Mapping[str, object]
    extension_metadata: Mapping[str, object]


class AioHookServices(Protocol):
    """Limited run-scoped services available to one hook definition."""

    def emit_preview(
        self,
        stage: AioStage | str,
        image: object,
        label: str | None = None,
    ) -> None: ...

    def register_cleanup(self, callback: Callable[[], None]) -> None: ...


@dataclass(frozen=True, slots=True)
class AioHookSessionContext:
    run_id: str
    request: AioHookRequestView
    services: AioHookServices


@dataclass(frozen=True, slots=True)
class AioStageEvent:
    run_id: str
    stage: AioStage
    phase: AioStagePhase
    request: AioHookRequestView
    state: AioHookStateView
    services: AioHookServices


class AioHookSession(Protocol):
    def before_stage(self, event: AioStageEvent) -> AioHookPatch | None: ...

    def after_stage(self, event: AioStageEvent) -> AioHookPatch | None: ...

    def close(self) -> None: ...


class AioHookSessionBase:
    """Convenient no-op base class for sessions implementing selected callbacks."""

    def before_stage(self, event: AioStageEvent) -> AioHookPatch | None:
        del event
        return None

    def after_stage(self, event: AioStageEvent) -> AioHookPatch | None:
        del event
        return None

    def close(self) -> None:
        return None


class AioHookDefinition(Protocol):
    def describe(self) -> AioHookDescriptor: ...

    def create_session(self, context: AioHookSessionContext) -> AioHookSession: ...


@dataclass(frozen=True, slots=True)
class AioHookChain:
    definitions: tuple[object, ...]


class AioHookError(RuntimeError):
    """Base error for validation, execution, and cleanup failures."""


class AioHookContractError(AioHookError):
    """Raised when a definition, descriptor, event, or patch is invalid."""


class AioHookExecutionError(AioHookError):
    """Raised when third-party hook code fails during an AiO run."""


def combine_aio_hooks(*hooks: object | None) -> AioHookChain:
    """Combine hook definitions or chains while preserving connection order."""

    definitions: list[object] = []
    for hook in hooks:
        if hook is None:
            continue
        if isinstance(hook, AioHookChain):
            definitions.extend(hook.definitions)
        else:
            definitions.append(hook)
    return AioHookChain(tuple(definitions))


__all__ = (
    "AIO_HOOK_API_VERSION",
    "EASYUSE_ANIMA_AIO_HOOK_TYPE",
    "AioHookChain",
    "AioHookContractError",
    "AioHookDefinition",
    "AioHookDescriptor",
    "AioHookError",
    "AioHookExecutionError",
    "AioHookPatch",
    "AioHookPoint",
    "AioHookRequestView",
    "AioHookServices",
    "AioHookSession",
    "AioHookSessionBase",
    "AioHookSessionContext",
    "AioHookStateView",
    "AioStage",
    "AioStageEvent",
    "AioStagePhase",
    "JsonValue",
    "UNSET",
    "combine_aio_hooks",
)
