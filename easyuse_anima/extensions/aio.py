"""Stable public API for explicitly connected AiO Generator hooks.

Third-party providers should import from this module.  The canonical objects
are exact aliases of the internal contracts so runtime validation never depends
on adapter wrappers or duplicate protocol types.
"""

from ..aio.hooks.contracts import (
    AIO_HOOK_API_VERSION,
    EASYUSE_ANIMA_AIO_HOOK_TYPE,
    UNSET,
    AioHookChain,
    AioHookContractError,
    AioHookDefinition,
    AioHookDescriptor,
    AioHookError,
    AioHookExecutionError,
    AioHookPatch,
    AioHookPoint,
    AioHookRequestView,
    AioHookServices,
    AioHookSession,
    AioHookSessionBase,
    AioHookSessionContext,
    AioHookStateView,
    AioStage,
    AioStageEvent,
    AioStagePhase,
    JsonValue,
    combine_aio_hooks,
)

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
