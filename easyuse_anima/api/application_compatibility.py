from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any

from ..autocomplete.classification import (
    classify_prompt_text as _canonical_classify_prompt_text,
)
from ..autocomplete.dataset import (
    AUTOCOMPLETE_CSV,
)
from ..autocomplete.dataset import (
    autocomplete_status as _canonical_autocomplete_status,
)
from ..autocomplete.dataset import (
    available_autocomplete_sources as _canonical_available_autocomplete_sources,
)
from ..autocomplete.dataset import (
    resolve_autocomplete_source as _canonical_resolve_autocomplete_source_path,
)
from ..autocomplete.search import search_autocomplete as _canonical_search_autocomplete
from ..profiles import aio as _aio_profiles
from ..profiles import mutation as _profile_mutation
from ..profiles import repository as _profile_repository
from . import responses as _api_responses
from . import router as _api_router
from .dependencies import (
    _late_application_attribute as _late_attr,
)
from .dependencies import (
    _late_application_dependency as _late,
)
from .dependencies import (
    _late_application_value as _late_value,
)
from .dependencies import (
    _read_application_dependency as _read,
)
from .responses import (
    attach_request_id_header,
    correlate_response,
    error_payload,
)
from .routes import autocomplete as _api_autocomplete_routes
from .routes import long_text_settings as _api_long_text_routes
from .routes import lora_preview as _api_lora_preview_routes
from .routes import settings as _api_settings_routes
from .routes import wildcards as _api_wildcard_routes


@dataclass(frozen=True, slots=True)
class ApiApplicationCompatibilityParts:
    server: Any
    web: Any
    logger: Any
    get_prompt_routes: Any
    translate_prompt_sync: Any
    translate_prompt_for_route: Any
    prompt_translation_error_response: Any
    error_response: Any
    contract_error_response: Any
    request_correlated: Any
    resolve_lora_preview_path: Any
    safe_profile_validation_messages: frozenset[str]
    profile_error_response: Any
    get_settings_payload_sync: Any
    save_setting_payload_sync: Any
    get_long_text_settings_payload_sync: Any
    save_long_text_settings_payload_sync: Any
    wildcards_payload_sync: Any
    autocomplete_status_payload_sync: Any
    public_autocomplete_status: Any
    public_autocomplete_payload: Any
    search_autocomplete_payload_sync: Any
    classify_prompt_payload_sync: Any
    runtime_autocomplete: Any
    resolve_autocomplete_source_path: Any
    available_autocomplete_sources: Any
    autocomplete_status: Any
    search_autocomplete: Any
    classify_prompt_text: Any


@dataclass(frozen=True, slots=True)
class _ApiApplicationCompatibilityBuild:
    translation_executor: Any
    parts: ApiApplicationCompatibilityParts


@dataclass(frozen=True, slots=True)
class _HttpCompatibilityParts:
    error_response: Any
    contract_error_response: Any
    request_correlated: Any
    resolve_lora_preview_path: Any
    safe_profile_validation_messages: frozenset[str]
    profile_error_response: Any


@dataclass(frozen=True, slots=True)
class _PayloadCompatibilityParts:
    get_settings_payload_sync: Any
    save_setting_payload_sync: Any
    get_long_text_settings_payload_sync: Any
    save_long_text_settings_payload_sync: Any
    wildcards_payload_sync: Any
    autocomplete_status_payload_sync: Any
    public_autocomplete_status: Any
    public_autocomplete_payload: Any
    search_autocomplete_payload_sync: Any
    classify_prompt_payload_sync: Any


def _resolve_host_modules() -> tuple[Any, Any]:
    try:
        import server  # pyright: ignore[reportMissingImports]
        from aiohttp import web  # pyright: ignore[reportMissingImports]
    except (AttributeError, ImportError):
        return None, None
    return server, web


def _build_runtime_autocomplete_parts():
    def runtime_autocomplete():
        try:
            return _read("wildcard_autocomplete", "get_runtime")().autocomplete
        except RuntimeError as exc:
            if str(exc) != "[EasyUseAnima] RuntimeServices has not been installed.":
                raise
            return None

    def resolve_autocomplete_source_path(source=None):
        autocomplete = runtime_autocomplete()
        if autocomplete is None:
            return _canonical_resolve_autocomplete_source_path(source)
        return autocomplete.resolve_source(source)

    def available_autocomplete_sources(selected=None):
        autocomplete = runtime_autocomplete()
        if autocomplete is None:
            return _canonical_available_autocomplete_sources(selected)
        return autocomplete.available_sources(selected)

    def autocomplete_status(path=AUTOCOMPLETE_CSV):
        autocomplete = runtime_autocomplete()
        if autocomplete is None:
            return _canonical_autocomplete_status(path)
        return autocomplete.status(path)

    def search_autocomplete(query, limit=20, path=AUTOCOMPLETE_CSV, category=None):
        autocomplete = runtime_autocomplete()
        if autocomplete is None:
            return _canonical_search_autocomplete(
                query,
                limit=limit,
                path=path,
                category=category,
            )
        return autocomplete.search(query, limit=limit, path=path, category=category)

    def classify_prompt_text(text, limit=240, path=AUTOCOMPLETE_CSV):
        autocomplete = runtime_autocomplete()
        if autocomplete is None:
            return _canonical_classify_prompt_text(text, limit=limit, path=path)
        return autocomplete.classify(text, limit=limit, path=path)

    return (
        runtime_autocomplete,
        resolve_autocomplete_source_path,
        available_autocomplete_sources,
        autocomplete_status,
        search_autocomplete,
        classify_prompt_text,
    )


def _build_http_compatibility_parts(*, logger: Any) -> _HttpCompatibilityParts:
    error_response = _api_responses.build_error_response(
        json_response=_late_attr("host", "web", "json_response"),
        build_error_payload=lambda code, message, **kwargs: error_payload(
            code, message, **kwargs
        ),
    )
    contract_error_response = _api_responses.build_contract_error_response(
        error_response=_late("request", "error_response")
    )
    request_correlated = _api_responses.build_request_correlator(
        create_id=_late("request", "create_request_id"),
        get_http_exception_type=lambda: getattr(
            _read("host", "web"), "HTTPException", ()
        ),
        attach_id_header=attach_request_id_header,
        correlate=correlate_response,
        get_logger=lambda: logger,
        error_response=_late("request", "error_response"),
    )
    resolve_lora_preview_path = (
        _api_lora_preview_routes.build_lora_preview_path_resolver(
            get_extensions=lambda: _api_lora_preview_routes.LORA_PREVIEW_EXTENSIONS,
            abspath=lambda path: os.path.abspath(path),
            dirname=lambda path: os.path.dirname(path),
            splitext=lambda path: os.path.splitext(path),
            commonpath=lambda paths: os.path.commonpath(paths),
            isfile=lambda path: os.path.isfile(path),
        )
    )
    safe_messages, profile_error_response = _api_responses.build_profile_error_response(
        max_aio_profiles=_aio_profiles.MAX_AIO_PROFILES,
        profile_mutation_error_types={
            "precondition_required": _profile_mutation.ProfilePreconditionRequiredError,
            "identity_mismatch": _profile_mutation.ProfileIdentityMismatchError,
            "revision_conflict": _profile_mutation.ProfileRevisionConflictError,
        },
        is_profile_mutation_error=lambda exc: isinstance(
            exc, _read("request", "profile_mutation_error_type")
        ),
        is_file_exists_error=lambda exc: isinstance(exc, FileExistsError),
        is_file_not_found_error=lambda exc: isinstance(exc, FileNotFoundError),
        is_invalid_profile_data_error=lambda exc: isinstance(
            exc,
            (json.JSONDecodeError, UnicodeDecodeError, _profile_repository.InvalidProfileDataError),
        ),
        is_value_error=lambda exc: isinstance(exc, ValueError),
        get_safe_validation_messages=_late_value(
            "request", "safe_profile_validation_messages"
        ),
        error_response=_late("request", "error_response"),
    )
    return _HttpCompatibilityParts(
        error_response=error_response,
        contract_error_response=contract_error_response,
        request_correlated=request_correlated,
        resolve_lora_preview_path=resolve_lora_preview_path,
        safe_profile_validation_messages=safe_messages,
        profile_error_response=profile_error_response,
    )


def _build_payload_compatibility_parts() -> _PayloadCompatibilityParts:
    settings = _api_settings_routes.build_settings_payloads(
        public_settings=_late("settings", "public_settings"),
        save_setting=_late("settings", "save_setting"),
    )
    long_text = _api_long_text_routes.build_long_text_settings_payloads(
        load_long_text_settings=_late("settings", "load_long_text_settings"),
        save_long_text_settings=_late("settings", "save_long_text_settings"),
        public_settings=_late("settings", "public_settings"),
    )
    wildcards = _api_wildcard_routes.build_wildcards_payload(
        public_settings=_late("settings", "public_settings"),
        resolve_wildcard_roots=_late("wildcard_autocomplete", "resolve_wildcard_roots"),
        list_wildcards=_late("wildcard_autocomplete", "list_wildcards"),
    )
    autocomplete = _api_autocomplete_routes.build_autocomplete_payloads(
        resolve_autocomplete_source=_late(
            "wildcard_autocomplete", "resolve_autocomplete_source"
        ),
        resolve_autocomplete_source_path=_late(
            "wildcard_autocomplete", "resolve_autocomplete_source_path"
        ),
        autocomplete_status=_late("wildcard_autocomplete", "autocomplete_status"),
        available_autocomplete_sources=_late(
            "wildcard_autocomplete", "available_autocomplete_sources"
        ),
        resolve_autocomplete_limit=_late(
            "wildcard_autocomplete", "resolve_autocomplete_limit"
        ),
        search_autocomplete=_late("wildcard_autocomplete", "search_autocomplete"),
        classify_prompt_text=_late("wildcard_autocomplete", "classify_prompt_text"),
        public_autocomplete_status=_late(
            "wildcard_autocomplete", "public_autocomplete_status"
        ),
        public_autocomplete_payload=_late(
            "wildcard_autocomplete", "public_autocomplete_payload"
        ),
    )
    return _PayloadCompatibilityParts(
        get_settings_payload_sync=settings[0],
        save_setting_payload_sync=settings[1],
        get_long_text_settings_payload_sync=long_text[0],
        save_long_text_settings_payload_sync=long_text[1],
        wildcards_payload_sync=wildcards,
        autocomplete_status_payload_sync=autocomplete[0],
        public_autocomplete_status=autocomplete[1],
        public_autocomplete_payload=autocomplete[2],
        search_autocomplete_payload_sync=autocomplete[3],
        classify_prompt_payload_sync=autocomplete[4],
    )


def _build_application_compatibility(
    *,
    logger: Any,
    build_translation_route_runtime: Any,
    get_worker: Any,
    get_translate_prompt_sync: Any,
) -> _ApiApplicationCompatibilityBuild:
    server, web = _resolve_host_modules()
    runtime = _build_runtime_autocomplete_parts()
    translation = build_translation_route_runtime(
        translate_prompt_markers=_late("translation", "translate_prompt_markers"),
        resolve_prompt_translation_settings=_late(
            "translation", "resolve_prompt_translation_settings"
        ),
        get_worker=get_worker,
        get_translate_prompt_sync=get_translate_prompt_sync,
        get_timeout_seconds=_late_value("translation", "route_timeout_seconds"),
        error_response=_late("request", "error_response"),
    )
    http = _build_http_compatibility_parts(logger=logger)
    payloads = _build_payload_compatibility_parts()
    get_prompt_routes = _api_router.build_prompt_routes_resolver(
        resolve_server=_late_value("host", "server")
    )
    parts = ApiApplicationCompatibilityParts(
        server=server,
        web=web,
        logger=logger,
        get_prompt_routes=get_prompt_routes,
        translate_prompt_sync=translation[1],
        translate_prompt_for_route=translation[2],
        prompt_translation_error_response=translation[3],
        error_response=http.error_response,
        contract_error_response=http.contract_error_response,
        request_correlated=http.request_correlated,
        resolve_lora_preview_path=http.resolve_lora_preview_path,
        safe_profile_validation_messages=http.safe_profile_validation_messages,
        profile_error_response=http.profile_error_response,
        get_settings_payload_sync=payloads.get_settings_payload_sync,
        save_setting_payload_sync=payloads.save_setting_payload_sync,
        get_long_text_settings_payload_sync=payloads.get_long_text_settings_payload_sync,
        save_long_text_settings_payload_sync=payloads.save_long_text_settings_payload_sync,
        wildcards_payload_sync=payloads.wildcards_payload_sync,
        autocomplete_status_payload_sync=payloads.autocomplete_status_payload_sync,
        public_autocomplete_status=payloads.public_autocomplete_status,
        public_autocomplete_payload=payloads.public_autocomplete_payload,
        search_autocomplete_payload_sync=payloads.search_autocomplete_payload_sync,
        classify_prompt_payload_sync=payloads.classify_prompt_payload_sync,
        runtime_autocomplete=runtime[0],
        resolve_autocomplete_source_path=runtime[1],
        available_autocomplete_sources=runtime[2],
        autocomplete_status=runtime[3],
        search_autocomplete=runtime[4],
        classify_prompt_text=runtime[5],
    )
    return _ApiApplicationCompatibilityBuild(
        translation_executor=translation[0],
        parts=parts,
    )


__all__: tuple[str, ...] = ()
