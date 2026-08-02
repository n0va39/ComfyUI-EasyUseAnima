"""Run-scoped validation and dispatch for explicitly connected AiO hooks."""

from __future__ import annotations

import json
import logging
import math
import re
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import cast

from ..generation_pipeline import (
    GenerationCapabilities,
    GenerationRequest,
    GenerationStage,
    GenerationState,
)
from .contracts import (
    AIO_HOOK_API_VERSION,
    UNSET,
    AioHookChain,
    AioHookContractError,
    AioHookDescriptor,
    AioHookExecutionError,
    AioHookPatch,
    AioHookPoint,
    AioHookRequestView,
    AioHookServices,
    AioHookSessionContext,
    AioHookStateView,
    AioStage,
    AioStageEvent,
    AioStagePhase,
)

logger = logging.getLogger("ComfyUI-EasyUseAnima")

_SUPPORTED_POINTS = frozenset({
    AioHookPoint(AioStage.POSTPROCESS, AioStagePhase.BEFORE),
    AioHookPoint(AioStage.POSTPROCESS, AioStagePhase.AFTER),
})
_MAX_FINGERPRINT_BYTES = 16 * 1024
_MAX_METADATA_BYTES = 64 * 1024
_HOOK_ID_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}\Z")


@dataclass(frozen=True, slots=True)
class _PreparedHook:
    definition: object
    hook_id: str
    hook_version: str
    api_version: int
    points: frozenset[AioHookPoint]
    fingerprint: object | None


@dataclass(slots=True)
class _ActiveHook:
    prepared: _PreparedHook
    session: object
    services: _RunHookServices
    metadata_key: str


def _json_value(value: object, path: str) -> object:
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise AioHookContractError(f"{path} must not contain NaN or infinity")
        return value
    if isinstance(value, list):
        return [_json_value(item, f"{path}[]") for item in value]
    if isinstance(value, Mapping):
        copied: dict[str, object] = {}
        for key, item in value.items():
            if not isinstance(key, str):
                raise AioHookContractError(f"{path} keys must be strings")
            copied[key] = _json_value(item, f"{path}.{key}")
        return copied
    raise AioHookContractError(
        f"{path} must be JSON-safe, got {type(value).__name__}"
    )


def _bounded_json_value(value: object, path: str, limit: int) -> object:
    copied = _json_value(value, path)
    encoded = json.dumps(
        copied,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    if len(encoded) > limit:
        raise AioHookContractError(f"{path} exceeds the {limit}-byte limit")
    return copied


def _flatten_hook_value(value: object | None) -> tuple[object, ...]:
    definitions: list[object] = []
    chain_stack: set[int] = set()

    def visit(item: object | None) -> None:
        if item is None:
            return
        if isinstance(item, AioHookChain):
            identity = id(item)
            if identity in chain_stack:
                raise AioHookContractError("AiO hook chain contains a cycle")
            chain_stack.add(identity)
            for nested in item.definitions:
                visit(nested)
            chain_stack.remove(identity)
            return
        definitions.append(item)

    visit(value)
    identities = [id(definition) for definition in definitions]
    if len(identities) != len(set(identities)):
        raise AioHookContractError(
            "The same AiO hook definition object appears more than once"
        )
    return tuple(definitions)


def _copy_points(value: object, hook_id: str) -> frozenset[AioHookPoint]:
    if not isinstance(value, (set, frozenset, tuple, list)):
        raise AioHookContractError(
            f"AiO hook {hook_id}: descriptor.points must be a collection"
        )
    points: set[AioHookPoint] = set()
    for item in value:
        if not isinstance(item, AioHookPoint):
            raise AioHookContractError(
                f"AiO hook {hook_id}: descriptor.points must contain AioHookPoint values"
            )
        try:
            point = AioHookPoint(AioStage(item.stage), AioStagePhase(item.phase))
        except (TypeError, ValueError) as exc:
            raise AioHookContractError(
                f"AiO hook {hook_id}: descriptor.points contains an unknown value"
            ) from exc
        points.add(point)
    if not points:
        raise AioHookContractError(
            f"AiO hook {hook_id}: descriptor.points must not be empty"
        )
    unsupported = points - _SUPPORTED_POINTS
    if unsupported:
        names = ", ".join(
            f"{point.stage.value}/{point.phase.value}"
            for point in sorted(
                unsupported,
                key=lambda point: (point.stage.value, point.phase.value),
            )
        )
        raise AioHookContractError(
            f"AiO hook {hook_id} requests unsupported hook points: {names}"
        )
    return frozenset(points)


def _prepare_definition(definition: object) -> _PreparedHook:
    describe = getattr(definition, "describe", None)
    create_session = getattr(definition, "create_session", None)
    if not callable(describe) or not callable(create_session):
        raise AioHookContractError(
            "AiO hook definitions must implement describe() and create_session()"
        )
    try:
        descriptor = describe()
    except Exception as exc:
        raise AioHookExecutionError(
            f"AiO hook describe() failed: {exc}"
        ) from exc
    if not isinstance(descriptor, AioHookDescriptor):
        raise AioHookContractError(
            "describe() must return easyuse_anima.extensions.aio.AioHookDescriptor"
        )
    if not isinstance(descriptor.hook_id, str):
        raise AioHookContractError("descriptor.hook_id must be a string")
    if not isinstance(descriptor.hook_version, str):
        raise AioHookContractError(
            f"AiO hook {descriptor.hook_id}: hook_version must be a string"
        )
    hook_id = descriptor.hook_id.strip()
    hook_version = descriptor.hook_version.strip()
    if not _HOOK_ID_RE.fullmatch(hook_id) or hook_id != descriptor.hook_id:
        raise AioHookContractError(
            "descriptor.hook_id must use 1-128 ASCII letters, digits, dots, "
            "underscores, or hyphens without surrounding whitespace"
        )
    if not hook_version or len(hook_version) > 64 or hook_version != descriptor.hook_version:
        raise AioHookContractError(
            f"AiO hook {hook_id}: hook_version must contain 1-64 characters"
        )
    if (
        type(descriptor.api_version) is not int
        or descriptor.api_version != AIO_HOOK_API_VERSION
    ):
        raise AioHookContractError(
            f"AiO hook {hook_id} uses API v{descriptor.api_version}; "
            f"this runtime supports v{AIO_HOOK_API_VERSION}"
        )
    points = _copy_points(descriptor.points, hook_id)
    fingerprint = None
    if descriptor.fingerprint is not None:
        fingerprint = _bounded_json_value(
            descriptor.fingerprint,
            f"AiO hook {hook_id} fingerprint",
            _MAX_FINGERPRINT_BYTES,
        )
    return _PreparedHook(
        definition=definition,
        hook_id=hook_id,
        hook_version=hook_version,
        api_version=descriptor.api_version,
        points=points,
        fingerprint=fingerprint,
    )


def prepare_aio_hook(value: object | None) -> tuple[_PreparedHook, ...]:
    """Validate a connected definition or chain without creating run state."""

    return tuple(
        _prepare_definition(definition)
        for definition in _flatten_hook_value(value)
    )


def aio_hook_change_token(value: object | None) -> tuple[bool, object]:
    """Return whether the whole-node change token is stable and its JSON value."""

    prepared = prepare_aio_hook(value)
    if any(item.fingerprint is None for item in prepared):
        return False, None
    return True, [
        {
            "hook_id": item.hook_id,
            "hook_version": item.hook_version,
            "api_version": item.api_version,
            "points": [
                {"stage": point.stage.value, "phase": point.phase.value}
                for point in sorted(
                    item.points,
                    key=lambda point: (point.stage.value, point.phase.value),
                )
            ],
            "fingerprint": _json_value(item.fingerprint, "prepared fingerprint"),
        }
        for item in prepared
    ]


def _freeze(value: object) -> object:
    if isinstance(value, Mapping):
        return MappingProxyType({
            str(key): _freeze(item) for key, item in value.items()
        })
    if isinstance(value, (list, tuple)):
        return tuple(_freeze(item) for item in value)
    return value


def _image_shape(image: object | None) -> tuple[int, ...] | None:
    shape = getattr(image, "shape", None)
    if shape is None:
        return None
    try:
        return tuple(int(value) for value in shape)
    except (TypeError, ValueError):
        return None


class _RunHookServices(AioHookServices):
    def __init__(self, owner: AioHookRun, prepared: _PreparedHook) -> None:
        self._owner = owner
        self._prepared = prepared

    def emit_preview(
        self,
        stage: AioStage | str,
        image: object,
        label: str | None = None,
    ) -> None:
        self._owner.emit_preview(self._prepared, stage, image, label)

    def register_cleanup(self, callback: Callable[[], None]) -> None:
        self._owner.register_cleanup(self._prepared, callback)


class AioHookRun:
    """Create, dispatch, and close one chain of run-scoped hook sessions."""

    def __init__(
        self,
        prepared: tuple[_PreparedHook, ...],
        request: GenerationRequest,
        state: GenerationState,
        run_id: str,
        emit_preview: Callable[[str, object], None] | None,
    ) -> None:
        self._prepared = prepared
        self._request = request
        self._state = state
        self._run_id = run_id
        self._emit_preview = emit_preview
        self._active: list[_ActiveHook] = []
        self._cleanups: list[tuple[_PreparedHook, Callable[[], None]]] = []
        self._closed = False

    def __enter__(self) -> AioHookRun:
        if not self._prepared:
            return self
        request_view = self._request_view()
        hook_counts: dict[str, int] = {}
        summaries: list[dict[str, object]] = []
        self._state.extensions = {
            **self._state.extensions,
            "hooks": summaries,
            "hook_data": {},
        }
        creating: _PreparedHook | None = None
        try:
            for prepared in self._prepared:
                creating = prepared
                ordinal = hook_counts.get(prepared.hook_id, 0)
                hook_counts[prepared.hook_id] = ordinal + 1
                services = _RunHookServices(self, prepared)
                context = AioHookSessionContext(
                    run_id=self._run_id,
                    request=request_view,
                    services=services,
                )
                session = prepared.definition.create_session(context)  # type: ignore[attr-defined]
                if session is None:
                    raise AioHookContractError(
                        f"AiO hook {prepared.hook_id} create_session() returned None"
                    )
                self._active.append(_ActiveHook(
                    prepared=prepared,
                    session=session,
                    services=services,
                    metadata_key=f"{prepared.hook_id}#{ordinal}",
                ))
                summaries.append(self._descriptor_summary(prepared, ordinal))
        except BaseException as exc:
            self._close_preserving(exc)
            if not isinstance(exc, Exception) or isinstance(exc, AioHookContractError):
                raise
            hook_id = "unknown" if creating is None else creating.hook_id
            raise AioHookExecutionError(
                f"AiO hook {hook_id} failed during session creation: {exc}"
            ) from exc
        return self

    def __exit__(self, exc_type, exc, traceback) -> bool:
        del exc_type, traceback
        if exc is None:
            self.close()
        else:
            self._close_preserving(exc)
        return False

    def _request_view(self) -> AioHookRequestView:
        settings = cast(Mapping[str, object], self._request.config.to_dict())
        unique_id = self._request.workflow.unique_id
        return AioHookRequestView(
            mode=self._request.config.mode,
            node_id=None if unique_id is None else str(unique_id),
            settings=cast(Mapping[str, object], _freeze(settings)),
        )

    @staticmethod
    def _descriptor_summary(
        prepared: _PreparedHook,
        ordinal: int,
    ) -> dict[str, object]:
        return {
            "hook_id": prepared.hook_id,
            "hook_version": prepared.hook_version,
            "api_version": prepared.api_version,
            "ordinal": ordinal,
            "points": [
                {"stage": point.stage.value, "phase": point.phase.value}
                for point in sorted(
                    prepared.points,
                    key=lambda point: (point.stage.value, point.phase.value),
                )
            ],
        }

    def _state_view(self) -> AioHookStateView:
        return AioHookStateView(
            image=self._state.image,
            width=self._state.width,
            height=self._state.height,
            metadata=cast(Mapping[str, object], _freeze(self._state.metadata)),
            extension_metadata=cast(
                Mapping[str, object],
                _freeze(self._state.extensions),
            ),
        )

    def _dispatch(self, stage: AioStage, phase: AioStagePhase) -> None:
        point = AioHookPoint(stage, phase)
        matching = [
            active for active in self._active if point in active.prepared.points
        ]
        if phase is AioStagePhase.AFTER:
            matching.reverse()
        for active in matching:
            event = AioStageEvent(
                run_id=self._run_id,
                stage=stage,
                phase=phase,
                request=self._request_view(),
                state=self._state_view(),
                services=active.services,
            )
            callback_name = (
                "before_stage"
                if phase is AioStagePhase.BEFORE
                else "after_stage"
            )
            callback = getattr(active.session, callback_name, None)
            if not callable(callback):
                raise AioHookContractError(
                    f"AiO hook {active.prepared.hook_id} session must implement "
                    f"{callback_name}()"
                )
            try:
                patch = callback(event)
                self._apply_patch(active, point, patch)
            except AioHookContractError:
                raise
            except Exception as exc:
                raise AioHookExecutionError(
                    f"AiO hook {active.prepared.hook_id} v{active.prepared.hook_version} "
                    f"failed at {stage.value}/{phase.value}: {exc}"
                ) from exc

    def _apply_patch(
        self,
        active: _ActiveHook,
        point: AioHookPoint,
        patch: object,
    ) -> None:
        if patch is None:
            return
        if not isinstance(patch, AioHookPatch):
            raise AioHookContractError(
                f"AiO hook {active.prepared.hook_id} returned "
                f"{type(patch).__name__} at {point.stage.value}/{point.phase.value}; "
                "expected AioHookPatch or None"
            )
        if patch.image is not UNSET:
            if patch.image is None:
                raise AioHookContractError(
                    f"AiO hook {active.prepared.hook_id} returned a null image"
                )
            previous_shape = _image_shape(self._state.image)
            next_shape = _image_shape(patch.image)
            if previous_shape is None or next_shape is None:
                raise AioHookContractError(
                    f"AiO hook {active.prepared.hook_id} returned an image "
                    "without a readable tensor shape"
                )
            if previous_shape != next_shape:
                raise AioHookContractError(
                    f"AiO hook {active.prepared.hook_id} changed image shape "
                    f"from {previous_shape} to {next_shape}; API v1 image patches "
                    "must preserve shape"
                )
            self._state.image = patch.image
        if not isinstance(patch.metadata, Mapping):
            raise AioHookContractError(
                f"AiO hook {active.prepared.hook_id} metadata must be a mapping"
            )
        if patch.metadata:
            copied = cast(
                dict[str, object],
                _bounded_json_value(
                    patch.metadata,
                    f"AiO hook {active.prepared.hook_id} metadata",
                    _MAX_METADATA_BYTES,
                ),
            )
            hook_data = cast(
                dict[str, dict[str, object]],
                self._state.extensions.setdefault("hook_data", {}),
            )
            existing = hook_data.setdefault(active.metadata_key, {})
            duplicates = sorted(existing.keys() & copied.keys())
            if duplicates:
                raise AioHookContractError(
                    f"AiO hook {active.prepared.hook_id} repeated metadata keys: "
                    + ", ".join(duplicates)
                )
            existing.update(copied)

    def run_stage(
        self,
        stage: GenerationStage,
        request: GenerationRequest,
        state: GenerationState,
        capabilities: GenerationCapabilities,
    ) -> None:
        stage_id = AioStage(stage.name)
        stage.validate(request, capabilities)
        self._dispatch(stage_id, AioStagePhase.BEFORE)
        stage.run(request, state)
        self._dispatch(stage_id, AioStagePhase.AFTER)

    def emit_preview(
        self,
        prepared: _PreparedHook,
        stage: AioStage | str,
        image: object,
        label: str | None,
    ) -> None:
        self._ensure_open(prepared)
        try:
            stage_id = AioStage(stage)
        except (TypeError, ValueError) as exc:
            raise AioHookContractError(
                f"AiO hook {prepared.hook_id} requested an unknown preview stage"
            ) from exc
        if not any(point.stage is stage_id for point in prepared.points):
            raise AioHookContractError(
                f"AiO hook {prepared.hook_id} cannot emit a preview for "
                f"undeclared stage {stage_id.value}"
            )
        if self._emit_preview is None:
            return
        clean_label = re.sub(
            r"[^A-Za-z0-9._-]+",
            "_",
            "" if label is None else str(label).strip()[:48],
        )
        suffix = "" if not clean_label else f"_{clean_label}"
        self._emit_preview(
            f"hook_{stage_id.value}_{prepared.hook_id}{suffix}",
            image,
        )

    def register_cleanup(
        self,
        prepared: _PreparedHook,
        callback: Callable[[], None],
    ) -> None:
        self._ensure_open(prepared)
        if not callable(callback):
            raise AioHookContractError("AiO hook cleanup must be callable")
        self._cleanups.append((prepared, callback))

    def _ensure_open(self, prepared: _PreparedHook) -> None:
        if self._closed:
            raise AioHookContractError(
                f"AiO hook {prepared.hook_id} used services after close"
            )

    def _close_preserving(self, original: BaseException) -> None:
        try:
            self.close()
        except BaseException:
            logger.exception(
                "[EasyUseAnima][AiO Hook] cleanup failed while preserving %s",
                type(original).__name__,
            )

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        first_error: tuple[_PreparedHook, BaseException] | None = None
        for active in reversed(self._active):
            callback = getattr(active.session, "close", None)
            if not callable(callback):
                continue
            try:
                callback()
            except BaseException as exc:
                if first_error is None:
                    first_error = (active.prepared, exc)
        for prepared, callback in reversed(self._cleanups):
            try:
                callback()
            except BaseException as exc:
                if first_error is None:
                    first_error = (prepared, exc)
        if first_error is None:
            return
        prepared, error = first_error
        if not isinstance(error, Exception):
            raise error
        raise AioHookExecutionError(
            f"AiO hook {prepared.hook_id} failed during cleanup: {error}"
        ) from error


def run_aio_postprocess_hook_stage(
    prepared: tuple[_PreparedHook, ...],
    request: GenerationRequest,
    state: GenerationState,
    run_id: str,
    emit_preview: Callable[[str, object], None] | None,
    stage: GenerationStage,
) -> None:
    """Run the v1 postprocess boundary inside a scoped hook session."""

    with AioHookRun(
        prepared,
        request,
        state,
        run_id,
        emit_preview,
    ) as hook_run:
        hook_run.run_stage(stage, request, state, {})


__all__ = ()
