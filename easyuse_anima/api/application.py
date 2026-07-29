from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..aio.torch_compile_diagnostics import collect_torch_compile_diagnostics
from ..aio.torch_compile_recommendation import recommend_torch_compile
from ..profiles import aio as _aio_profiles
from ..profiles import lora as _lora_profiles
from ..profiles.mutation import ProfileMutationError
from ..runtime import get_runtime
from ..settings.repository import (
    load_long_text_settings,
    save_long_text_settings,
    save_setting,
)
from ..settings.service import (
    public_settings,
    resolve_autocomplete_limit,
    resolve_autocomplete_source,
    resolve_prompt_translation_settings,
)
from ..translation.contracts import PromptTranslationError
from ..translation.service import translate_prompt_markers
from ..wildcard.service import list_wildcards
from ..wildcard.sources import resolve_wildcard_roots
from .application_compatibility import (
    ApiApplicationCompatibilityParts,
    _build_application_compatibility,
)
from .application_routes import ApiRouteHandlers, _build_application_handlers
from .dependencies import (
    ApiApplicationDependencies,
    ApiHostDependencies,
    ApiProfileDependencies,
    ApiRequestDependencies,
    ApiSettingsDependencies,
    ApiTorchCompileDependencies,
    ApiTranslationDependencies,
    ApiWildcardAutocompleteDependencies,
    _publish_application_dependencies,
)
from .dependencies import (
    _late_application_dependency as _late,
)
from .dependencies import (
    _late_application_value as _late_value,
)
from .file_io import run_file_io
from .responses import create_request_id
from .router import (
    ROUTE_REGISTRATION_MARKER,
    build_route_definitions,
    build_route_registrar,
    build_route_signature,
    register_route_definitions,
)
from .routes.translation import PROMPT_TRANSLATION_ROUTE_TIMEOUT_SECONDS


@dataclass(frozen=True, slots=True)
class ApiCompatibilityIdentityView:
    parts: ApiApplicationCompatibilityParts
    initial_routes: Any


@dataclass(frozen=True, slots=True)
class ApiApplication:
    dependencies: ApiApplicationDependencies
    translation_executor: Any
    handlers: ApiRouteHandlers
    route_definitions: tuple[Any, ...]
    route_signature: tuple[tuple[str, str], ...]
    register_routes: Any
    compatibility: ApiCompatibilityIdentityView


_APPLICATION: ApiApplication | None = None


def _publish_application(application: ApiApplication) -> ApiApplication:
    global _APPLICATION

    current = _APPLICATION
    if current is None:
        _APPLICATION = application
        return application
    if current is application:
        return current
    raise RuntimeError("[EasyUseAnima] API application already installed.")


def _get_application() -> ApiApplication:
    current = _APPLICATION
    if current is None:
        raise RuntimeError("[EasyUseAnima] API application is not installed.")
    return current


def _route_definitions(handlers: ApiRouteHandlers) -> tuple[Any, ...]:
    if handlers.get_settings_handler is None:
        return ()
    return build_route_definitions(
        get_settings_handler=handlers.get_settings_handler,
        set_setting_handler=handlers.set_setting_handler,
        get_long_text_settings_handler=handlers.get_long_text_settings_handler,
        get_wildcards_handler=handlers.get_wildcards_handler,
        save_long_text_settings_handler=handlers.save_long_text_settings_handler,
        autocomplete_status_handler=handlers.autocomplete_status_handler,
        autocomplete_handler=handlers.autocomplete_handler,
        classify_prompt_handler=handlers.classify_prompt_handler,
        translate_prompt_handler=handlers.translate_prompt_handler,
        aio_torch_compile_recommend_handler=(
            handlers.aio_torch_compile_recommend_handler
        ),
        lora_preview_handler=handlers.lora_preview_handler,
        loras_handler=handlers.loras_handler,
        lora_profiles_handler=handlers.lora_profiles_handler,
        save_lora_profile_handler=handlers.save_lora_profile_handler,
        load_lora_profile_handler=handlers.load_lora_profile_handler,
        aio_profiles_handler=handlers.aio_profiles_handler,
        save_aio_profile_handler=handlers.save_aio_profile_handler,
        load_aio_profile_handler=handlers.load_aio_profile_handler,
        delete_aio_profile_handler=handlers.delete_aio_profile_handler,
        rename_aio_profile_handler=handlers.rename_aio_profile_handler,
        fix_lora_profile_handler=handlers.fix_lora_profile_handler,
    )


def _application_dependencies(
    *,
    parts: ApiApplicationCompatibilityParts,
    route_definitions: tuple[Any, ...],
    route_signature: tuple[tuple[str, str], ...],
) -> ApiApplicationDependencies:
    return ApiApplicationDependencies(
        host=ApiHostDependencies(
            server=parts.server,
            web=parts.web,
            get_prompt_routes=parts.get_prompt_routes,
            route_definitions=route_definitions,
            route_signature=route_signature,
            register_route_definitions=register_route_definitions,
        ),
        request=ApiRequestDependencies(
            create_request_id=create_request_id,
            run_file_io=run_file_io,
            error_response=parts.error_response,
            contract_error_response=parts.contract_error_response,
            profile_error_response=parts.profile_error_response,
            profile_mutation_error_type=ProfileMutationError,
            safe_profile_validation_messages=parts.safe_profile_validation_messages,
        ),
        settings=ApiSettingsDependencies(
            public_settings=public_settings,
            save_setting=save_setting,
            load_long_text_settings=load_long_text_settings,
            save_long_text_settings=save_long_text_settings,
            get_settings_payload=parts.get_settings_payload_sync,
            save_setting_payload=parts.save_setting_payload_sync,
            get_long_text_settings_payload=parts.get_long_text_settings_payload_sync,
            save_long_text_settings_payload=parts.save_long_text_settings_payload_sync,
        ),
        wildcard_autocomplete=ApiWildcardAutocompleteDependencies(
            get_runtime=get_runtime,
            resolve_wildcard_roots=resolve_wildcard_roots,
            list_wildcards=list_wildcards,
            resolve_autocomplete_source=resolve_autocomplete_source,
            resolve_autocomplete_source_path=parts.resolve_autocomplete_source_path,
            resolve_autocomplete_limit=resolve_autocomplete_limit,
            available_autocomplete_sources=parts.available_autocomplete_sources,
            autocomplete_status=parts.autocomplete_status,
            search_autocomplete=parts.search_autocomplete,
            classify_prompt_text=parts.classify_prompt_text,
            wildcards_payload=parts.wildcards_payload_sync,
            autocomplete_status_payload=parts.autocomplete_status_payload_sync,
            search_autocomplete_payload=parts.search_autocomplete_payload_sync,
            classify_prompt_payload=parts.classify_prompt_payload_sync,
            public_autocomplete_status=parts.public_autocomplete_status,
            public_autocomplete_payload=parts.public_autocomplete_payload,
        ),
        profiles=ApiProfileDependencies(
            list_loras=_lora_profiles._list_loras,
            list_lora_profiles=_lora_profiles._list_lora_profiles,
            list_aio_profiles=_aio_profiles._list_aio_profiles,
            load_lora_profile=_lora_profiles._load_lora_profile,
            load_aio_profile=_aio_profiles._load_aio_profile,
            save_lora_profile=_lora_profiles._save_lora_profile,
            save_aio_profile=_aio_profiles._save_aio_profile,
            delete_aio_profile=_aio_profiles._delete_aio_profile,
            rename_aio_profile=_aio_profiles._rename_aio_profile,
            fix_lora_profile_payload=_lora_profiles._fix_lora_profile_payload,
            resolve_lora_preview_path=parts.resolve_lora_preview_path,
        ),
        translation=ApiTranslationDependencies(
            translate_prompt_markers=translate_prompt_markers,
            resolve_prompt_translation_settings=resolve_prompt_translation_settings,
            route_timeout_seconds=PROMPT_TRANSLATION_ROUTE_TIMEOUT_SECONDS,
            prompt_translation_error_type=PromptTranslationError,
            prompt_translation_error_response=(
                parts.prompt_translation_error_response
            ),
        ),
        torch_compile=ApiTorchCompileDependencies(
            collect_diagnostics=collect_torch_compile_diagnostics,
            recommend_torch_compile=recommend_torch_compile,
        ),
    )


def _build_api_application(
    *,
    logger: Any,
    publish_routes: Any,
    build_settings_route_group: Any,
    build_wildcard_autocomplete_route_group: Any,
    build_translation_route_runtime: Any,
    build_translation_route_handler: Any,
    build_aio_torch_compile_route_handler: Any,
    build_lora_read_route_group: Any,
    build_profile_list_route_group: Any,
    build_profile_route_group: Any,
) -> ApiApplication:
    if _APPLICATION is not None:
        return _APPLICATION
    compatibility = _build_application_compatibility(
        logger=logger,
        build_translation_route_runtime=build_translation_route_runtime,
        get_worker=lambda: _get_application().translation_executor,
        get_translate_prompt_sync=lambda: (
            _get_application().compatibility.parts.translate_prompt_sync
        ),
    )
    handlers = _build_application_handlers(
        parts=compatibility.parts,
        build_settings_route_group=build_settings_route_group,
        build_wildcard_autocomplete_route_group=(
            build_wildcard_autocomplete_route_group
        ),
        build_translation_route_handler=build_translation_route_handler,
        build_aio_torch_compile_route_handler=(
            build_aio_torch_compile_route_handler
        ),
        build_lora_read_route_group=build_lora_read_route_group,
        build_profile_list_route_group=build_profile_list_route_group,
        build_profile_route_group=build_profile_route_group,
    )
    definitions = _route_definitions(handlers)
    signature = build_route_signature(definitions)
    dependencies = _publish_application_dependencies(
        _application_dependencies(
            parts=compatibility.parts,
            route_definitions=definitions,
            route_signature=signature,
        )
    )
    initial_routes = compatibility.parts.get_prompt_routes()
    registrar = build_route_registrar(
        resolve_prompt_routes=_late("host", "get_prompt_routes"),
        publish_routes=publish_routes,
        resolve_web=_late_value("host", "web"),
        resolve_route_definitions=_late_value("host", "route_definitions"),
        resolve_route_signature=_late_value("host", "route_signature"),
        register_route_definitions=_late("host", "register_route_definitions"),
        marker=ROUTE_REGISTRATION_MARKER,
    )
    application = ApiApplication(
        dependencies=dependencies,
        translation_executor=compatibility.translation_executor,
        handlers=handlers,
        route_definitions=definitions,
        route_signature=signature,
        register_routes=registrar,
        compatibility=ApiCompatibilityIdentityView(
            parts=compatibility.parts,
            initial_routes=initial_routes,
        ),
    )
    return _publish_application(application)


__all__: tuple[str, ...] = ()
