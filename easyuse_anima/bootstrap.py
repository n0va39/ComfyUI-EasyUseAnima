"""Guard startup work owned by the ComfyUI package entrypoint."""

from __future__ import annotations

import atexit
import logging
import threading
import time
from collections.abc import Callable

from .api.routes.aio_torch_compile import (
    build_aio_torch_compile_recommend_handler as _build_aio_torch_compile_recommend_handler,
)
from .api.routes.aio_profile_mutations import (
    build_aio_profile_mutation_handlers as _build_aio_profile_mutation_handlers,
)
from .api.routes.autocomplete import (
    build_autocomplete_handlers as _build_autocomplete_handlers,
)
from .api.routes.autocomplete import (
    build_classify_prompt_handler as _build_classify_prompt_handler,
)
from .api.routes.long_text_settings import (
    build_long_text_settings_handlers as _build_long_text_settings_handlers,
)
from .api.routes.lora_catalog import build_loras_handler as _build_loras_handler
from .api.routes.lora_preview import (
    build_lora_preview_handler as _build_lora_preview_handler,
)
from .api.routes.lora_profile_fix import (
    build_lora_profile_fix_handler as _build_lora_profile_fix_handler,
)
from .api.routes.profile_lists import (
    build_profile_list_handlers as _build_profile_list_handlers,
)
from .api.routes.profile_loads import (
    build_profile_load_handlers as _build_profile_load_handlers,
)
from .api.routes.profile_saves import (
    build_profile_save_handlers as _build_profile_save_handlers,
)
from .api.routes.settings import build_settings_handlers as _build_settings_handlers
from .api.routes.translation import (
    build_translation_runtime as _build_translation_runtime,
    build_translate_prompt_handler as _build_translate_prompt_handler,
)
from .api.routes.translation_execution import (
    PromptTranslationRouteExecutor as _PromptTranslationRouteExecutor,
)
from .api.routes.wildcards import (
    build_wildcards_handler as _build_wildcards_handler,
)
from .aio.first_pass_cache import _DEFAULT_AIO_FIRST_PASS_CACHE
from .autocomplete.dataset import _DEFAULT_AUTOCOMPLETE_SNAPSHOTS
from .autocomplete.index import _DEFAULT_AUTOCOMPLETE_INDEX_STORE
from .autocomplete.service import _AutocompleteService
from .infrastructure.comfy.provider import DefaultComfyHostProvider
from .runtime import (
    RuntimeConfig,
    RuntimeServices,
    _RuntimeCleanupPlan,
    _detach_runtime,
    install_runtime,
)
from .seed.service import InMemorySeedReservationService
from .translation.contracts import (
    PromptTranslationError,
    PromptTranslationLimitError,
    TranslationBusyError,
    TranslationCancelledError,
    TranslationMarkerCountError,
    TranslationMarkerSizeError,
    TranslationProviderUnavailableError,
    TranslationTimeoutError,
    TranslationTotalSizeError,
    TranslationUpstreamError,
)
from .translation.ports import PromptTranslationPort
from .translation.service import (
    BoundedTranslationCache,
    PromptTranslationService,
    _install_default_translation_service,
    _restore_default_translation_service,
)
from .wildcard.snapshot import _DEFAULT_WILDCARD_SNAPSHOTS

_LOGGER = logging.getLogger("ComfyUI-EasyUseAnima")
_INITIALIZE_LOCK = threading.Lock()
_WILDCARDS_INITIALIZED = False
_DEFAULT_RUNTIME: RuntimeServices | None = None
_TRANSLATION_ROUTE_EXECUTOR: _PromptTranslationRouteExecutor | None = None
_ATEXIT_REGISTERED = False
_SHUTDOWN = False


class _SystemClock:
    __slots__ = ()

    def monotonic(self) -> float:
        return time.monotonic()


def _load_runtime_config() -> RuntimeConfig:
    from .infrastructure.filesystem.paths import (
        PACKAGE_DATA_DIR,
        PACKAGE_ROOT,
        USER_DATA_DIR,
    )

    return RuntimeConfig(
        package_root=PACKAGE_ROOT,
        package_data_dir=PACKAGE_DATA_DIR,
        user_data_dir=USER_DATA_DIR,
    )


def _missing_comfy_nodes() -> None:
    return None


def build_settings_route_group(
    *,
    request_correlated,
    settings_dependencies,
    long_text_settings_dependencies,
):
    """Compose the correlated settings route group from canonical factories."""

    handlers = (
        *_build_settings_handlers(**settings_dependencies),
        *_build_long_text_settings_handlers(**long_text_settings_dependencies),
    )
    return tuple(request_correlated(handler) for handler in handlers)


def build_wildcard_autocomplete_route_group(
    *,
    request_correlated,
    wildcards_dependencies,
    autocomplete_dependencies,
    classify_prompt_dependencies,
):
    """Compose correlated wildcard and autocomplete routes."""

    handlers = (
        _build_wildcards_handler(**wildcards_dependencies),
        *_build_autocomplete_handlers(**autocomplete_dependencies),
        _build_classify_prompt_handler(**classify_prompt_dependencies),
    )
    return tuple(request_correlated(handler) for handler in handlers)


def build_translation_route_handler(
    *,
    request_correlated,
    translation_dependencies,
):
    """Compose the correlated translation route."""

    return request_correlated(
        _build_translate_prompt_handler(**translation_dependencies)
    )


def build_translation_route_runtime(
    *,
    translate_prompt_markers,
    resolve_prompt_translation_settings,
    get_worker,
    get_translate_prompt_sync,
    get_timeout_seconds,
    error_response,
):
    """Compose one translation route executor and its process cleanup."""

    global _TRANSLATION_ROUTE_EXECUTOR

    runtime = _build_translation_runtime(
        executor_type=_PromptTranslationRouteExecutor,
        busy_error_type=TranslationBusyError,
        cancelled_error_type=TranslationCancelledError,
        timeout_error_type=TranslationTimeoutError,
        translate_prompt_markers=translate_prompt_markers,
        resolve_prompt_translation_settings=resolve_prompt_translation_settings,
        get_worker=get_worker,
        get_translate_prompt_sync=get_translate_prompt_sync,
        get_timeout_seconds=get_timeout_seconds,
        translation_error_types={
            "marker_count": TranslationMarkerCountError,
            "marker_size": TranslationMarkerSizeError,
            "total_size": TranslationTotalSizeError,
            "limit": PromptTranslationLimitError,
            "provider_unavailable": TranslationProviderUnavailableError,
            "timeout": TranslationTimeoutError,
            "cancelled": TranslationCancelledError,
            "busy": TranslationBusyError,
            "upstream": TranslationUpstreamError,
            "base": PromptTranslationError,
        },
        error_response=error_response,
    )
    _TRANSLATION_ROUTE_EXECUTOR = runtime[0]
    return runtime


def build_aio_torch_compile_route_handler(
    *,
    request_correlated,
    aio_torch_compile_dependencies,
):
    """Compose the correlated AiO Torch Compile recommendation route."""

    return request_correlated(
        _build_aio_torch_compile_recommend_handler(
            **aio_torch_compile_dependencies
        )
    )


def build_lora_read_route_group(
    *,
    request_correlated,
    lora_preview_dependencies,
    lora_catalog_dependencies,
):
    """Compose the correlated LoRA preview and catalog routes."""

    handlers = (
        _build_lora_preview_handler(**lora_preview_dependencies),
        _build_loras_handler(**lora_catalog_dependencies),
    )
    return tuple(request_correlated(handler) for handler in handlers)


def build_profile_list_route_group(
    *,
    request_correlated,
    profile_list_dependencies,
):
    """Compose the correlated LoRA and AiO profile list routes."""

    return tuple(
        request_correlated(handler)
        for handler in _build_profile_list_handlers(
            **profile_list_dependencies
        )
    )


def build_profile_route_group(
    *,
    request_correlated,
    profile_load_dependencies,
    profile_save_dependencies,
    aio_profile_mutation_dependencies,
    lora_profile_fix_dependencies,
):
    """Compose the correlated profile load, save, mutation, and fix routes."""

    handlers = (
        *_build_profile_load_handlers(**profile_load_dependencies),
        *_build_profile_save_handlers(**profile_save_dependencies),
        *_build_aio_profile_mutation_handlers(
            **aio_profile_mutation_dependencies
        ),
        _build_lora_profile_fix_handler(**lora_profile_fix_dependencies),
    )
    return tuple(request_correlated(handler) for handler in handlers)


def initialize(
    *,
    register_routes: Callable[[], bool],
    initialize_wildcards: Callable[[], object],
    load_comfy_nodes: Callable[[], object | None] = _missing_comfy_nodes,
) -> None:
    """Initialize routes and the default wildcard root without duplicate work."""

    global _ATEXIT_REGISTERED, _DEFAULT_RUNTIME, _WILDCARDS_INITIALIZED
    with _INITIALIZE_LOCK:
        if _SHUTDOWN:
            raise RuntimeError(
                "[EasyUseAnima] RuntimeServices has already been shut down."
            )
        if not _ATEXIT_REGISTERED:
            atexit.register(shutdown)
            _ATEXIT_REGISTERED = True

        runtime = _DEFAULT_RUNTIME
        created_runtime = runtime is None
        previous_translation = None
        previous_translation_holder: list[
            PromptTranslationPort | None
        ] | None = None
        translation_bound = False
        try:
            if runtime is None:
                clock = _SystemClock()
                translation = PromptTranslationService(
                    cache=BoundedTranslationCache(
                        time_func=clock.monotonic,
                    )
                )
                autocomplete = _AutocompleteService(
                    snapshots=_DEFAULT_AUTOCOMPLETE_SNAPSHOTS,
                    index_store=_DEFAULT_AUTOCOMPLETE_INDEX_STORE,
                )
                previous_translation_holder = [None]

                def restore_translation_facade() -> None:
                    previous = previous_translation_holder[0]
                    if previous is not None:
                        _restore_default_translation_service(
                            translation,
                            previous,
                        )

                cleanup_callbacks = []
                if _TRANSLATION_ROUTE_EXECUTOR is not None:
                    cleanup_callbacks.append(
                        _TRANSLATION_ROUTE_EXECUTOR.shutdown
                    )
                cleanup_callbacks.extend(
                    (
                        _DEFAULT_AIO_FIRST_PASS_CACHE.clear,
                        _DEFAULT_WILDCARD_SNAPSHOTS.clear,
                        _DEFAULT_AUTOCOMPLETE_INDEX_STORE.close,
                        _DEFAULT_AUTOCOMPLETE_SNAPSHOTS.clear,
                        restore_translation_facade,
                        translation.close,
                    )
                )
                runtime = RuntimeServices(
                    comfy=DefaultComfyHostProvider(load_comfy_nodes),
                    seed_reservations=InMemorySeedReservationService(),
                    config=_load_runtime_config(),
                    clock=clock,
                    translation=translation,
                    autocomplete=autocomplete,
                    wildcard_snapshots=_DEFAULT_WILDCARD_SNAPSHOTS,
                    aio_first_pass_cache=_DEFAULT_AIO_FIRST_PASS_CACHE,
                    _cleanup_plan=_RuntimeCleanupPlan(
                        tuple(cleanup_callbacks)
                    ),
                )
            install_runtime(runtime)
            previous_translation = _install_default_translation_service(
                runtime.translation
            )
            translation_bound = True
            if previous_translation_holder is not None:
                previous_translation_holder[0] = previous_translation
            _DEFAULT_RUNTIME = runtime
            register_routes()
            if _WILDCARDS_INITIALIZED:
                return
            try:
                initialize_wildcards()
            except OSError as exc:
                _LOGGER.warning(
                    "EasyUse Anima wildcard folder could not be initialized: %s",
                    exc,
                )
                return
            _WILDCARDS_INITIALIZED = True
        except BaseException:
            if (
                created_runtime
                and runtime is not None
                and _DEFAULT_RUNTIME is runtime
            ):
                _DEFAULT_RUNTIME = None
            if created_runtime and runtime is not None:
                try:
                    _detach_runtime(runtime)
                except BaseException:
                    _LOGGER.exception(
                        "EasyUse Anima runtime detach failed during startup rollback."
                    )
            if (
                translation_bound
                and runtime is not None
                and previous_translation is not None
            ):
                try:
                    _restore_default_translation_service(
                        runtime.translation,
                        previous_translation,
                    )
                except BaseException:
                    _LOGGER.exception(
                        "EasyUse Anima translation facade rollback failed."
                    )
            if created_runtime and runtime is not None:
                try:
                    runtime.translation.close()
                except BaseException:
                    _LOGGER.exception(
                        "EasyUse Anima translation cleanup failed during startup rollback."
                    )
            raise


def shutdown() -> None:
    """Terminally close the installed default runtime at most once."""

    global _DEFAULT_RUNTIME, _SHUTDOWN

    with _INITIALIZE_LOCK:
        if _SHUTDOWN:
            return
        _SHUTDOWN = True
        runtime = _DEFAULT_RUNTIME
        if runtime is None:
            return
        if _DEFAULT_RUNTIME is runtime:
            _DEFAULT_RUNTIME = None
        _detach_runtime(runtime)
        runtime.close()


__all__ = ["initialize", "shutdown"]
