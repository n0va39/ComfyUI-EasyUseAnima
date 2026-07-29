# pyright: strict
"""Call-time Comfy execution identity for authoritative seed reservations."""

from __future__ import annotations

import importlib
import json
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from typing import TypeAlias, cast

from ..errors import ValidationError

SEED_EXECUTION_IDENTITY_VERSION = 1

_REQUEST_NAMESPACE = (
    f"easyuse_anima.seed.request.v{SEED_EXECUTION_IDENTITY_VERSION}"
)
_STREAM_NAMESPACE = (
    f"easyuse_anima.seed.stream.v{SEED_EXECUTION_IDENTITY_VERSION}"
)
_COMFY_EXECUTION_UTILS = "comfy_execution.utils"

_HostModuleLoader: TypeAlias = Callable[[str], object]
_ExecutionContextLoader: TypeAlias = Callable[[], object]
_RequestIdFactory: TypeAlias = Callable[[], str]


class SeedExecutionIdentityError(ValidationError, ValueError):
    """A seed execution identity component is invalid."""


def _require_text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise SeedExecutionIdentityError(f"{label} must be a non-empty string")
    return value.strip()


def _normalize_node_id(value: object) -> str | None:
    if isinstance(value, (list, tuple)):
        if not value:
            return None
        value = cast(object, value[0])
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return str(value)
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def _require_list_index(value: object) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise SeedExecutionIdentityError(
            "Comfy execution list_index must be a non-negative integer or None"
        )
    return value


def _encoded_identity(namespace: str, *components: object) -> str:
    return (
        f"{namespace}:"
        + json.dumps(
            components,
            ensure_ascii=False,
            separators=(",", ":"),
        )
    )


@dataclass(frozen=True, slots=True)
class SeedExecutionContext:
    """Validated host identity for one effective Comfy node invocation."""

    prompt_id: str
    node_id: str
    list_index: int | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "prompt_id",
            _require_text(self.prompt_id, "Comfy execution prompt_id"),
        )
        normalized_node_id = _normalize_node_id(self.node_id)
        if normalized_node_id is None:
            raise SeedExecutionIdentityError(
                "Comfy execution node_id must be a non-empty string or integer"
            )
        object.__setattr__(self, "node_id", normalized_node_id)
        object.__setattr__(
            self,
            "list_index",
            _require_list_index(self.list_index),
        )


@dataclass(frozen=True, slots=True)
class SeedExecutionIdentity:
    """Stable stream and idempotent request identities for one execution."""

    stream_id: str
    request_id: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "stream_id",
            _require_text(self.stream_id, "Seed execution stream_id"),
        )
        object.__setattr__(
            self,
            "request_id",
            _require_text(self.request_id, "Seed execution request_id"),
        )


def _import_host_module(module_name: str) -> object:
    return importlib.import_module(module_name)


def read_comfy_execution_context(
    *,
    load_module: _HostModuleLoader = _import_host_module,
) -> SeedExecutionContext | None:
    """Read and validate current Comfy execution state without caching it."""

    try:
        module = load_module(_COMFY_EXECUTION_UTILS)
        get_context = getattr(module, "get_executing_context")
        raw_context = get_context()
        if raw_context is None:
            return None
        return SeedExecutionContext(
            prompt_id=getattr(raw_context, "prompt_id"),
            node_id=getattr(raw_context, "node_id"),
            list_index=getattr(raw_context, "list_index", None),
        )
    except Exception:
        return None


def _new_opaque_request_id() -> str:
    return uuid.uuid4().hex


def resolve_seed_execution_identity(
    feature: str,
    *,
    unique_id: object = None,
    load_context: _ExecutionContextLoader = read_comfy_execution_context,
    request_id_factory: _RequestIdFactory = _new_opaque_request_id,
) -> SeedExecutionIdentity | None:
    """Resolve the authoritative context identity or a UNIQUE_ID fallback."""

    feature_id = _require_text(feature, "Seed execution feature")
    context = load_context()

    if context is not None:
        if not isinstance(context, SeedExecutionContext):
            raise TypeError(
                "load_context must return a SeedExecutionContext or None"
            )
        return SeedExecutionIdentity(
            stream_id=_encoded_identity(
                _STREAM_NAMESPACE,
                feature_id,
                context.node_id,
            ),
            request_id=_encoded_identity(
                _REQUEST_NAMESPACE,
                feature_id,
                context.prompt_id,
                context.node_id,
                context.list_index,
            ),
        )

    fallback_node_id = _normalize_node_id(unique_id)
    if fallback_node_id is None:
        return None

    opaque_request_id = _require_text(
        request_id_factory(),
        "Opaque seed request ID",
    )
    return SeedExecutionIdentity(
        stream_id=_encoded_identity(
            _STREAM_NAMESPACE,
            feature_id,
            fallback_node_id,
        ),
        request_id=_encoded_identity(
            _REQUEST_NAMESPACE,
            feature_id,
            fallback_node_id,
            "fallback",
            opaque_request_id,
        ),
    )


__all__ = (
    "SEED_EXECUTION_IDENTITY_VERSION",
    "SeedExecutionContext",
    "SeedExecutionIdentity",
    "SeedExecutionIdentityError",
    "read_comfy_execution_context",
    "resolve_seed_execution_identity",
)
