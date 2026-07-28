from __future__ import annotations

import atexit
import asyncio
import json
import logging
import os

try:
    import server
    from aiohttp import web
except ImportError:
    server = None
    web = None

from .easyuse_anima.settings.repository import (
    load_long_text_settings,
    save_long_text_settings,
    save_setting,
)
from .easyuse_anima.settings.service import (
    public_settings,
    resolve_autocomplete_limit,
    resolve_autocomplete_source,
    resolve_prompt_translation_settings,
)
from .easyuse_anima.autocomplete.dataset import (
    autocomplete_status,
    available_autocomplete_sources,
    resolve_autocomplete_source as resolve_autocomplete_source_path,
)
from .easyuse_anima.autocomplete.search import (
    search_autocomplete,
)
from .easyuse_anima.autocomplete.classification import classify_prompt_text
from .easyuse_anima.wildcard.sources import resolve_wildcard_roots
from .wildcard_engine import list_wildcards
from .easyuse_anima.translation.contracts import (
    PromptTranslationError,
    TranslationBusyError,
    TranslationCancelledError,
    TranslationTimeoutError,
)
from .easyuse_anima.translation.service import (
    translate_prompt_markers,
)
from .easyuse_anima.api.errors import ApiContractError
from .easyuse_anima.api.file_io import (
    FILE_IO_MAX_IN_FLIGHT,
    _FILE_IO_LIMITERS,
    _FILE_IO_LIMITERS_LOCK,
    file_io_limiter as _file_io_limiter,
    release_file_io_slot as _release_file_io_slot,
    run_file_io as _run_file_io,
)
from .easyuse_anima.api.requests import (
    json_boolean,
    json_integer,
    json_object,
    json_string,
    json_uuid_string,
    parse_json_object,
)
from .easyuse_anima.api import responses as _api_responses
from .easyuse_anima.api.responses import (
    attach_request_id_header,
    correlate_response,
    create_request_id,
    error_payload,
)
from .easyuse_anima.api import router as _api_router
from .easyuse_anima.api.router import (
    ROUTE_REGISTRATION_MARKER as _ROUTE_REGISTRATION_MARKER,
    build_route_definitions as _build_route_definitions,
    build_route_signature as _build_route_signature,
    register_route_definitions as _register_route_definitions,
)
from .easyuse_anima.bootstrap import (
    build_aio_torch_compile_route_handler as _build_aio_torch_compile_route_handler,
    build_lora_read_route_group as _build_lora_read_route_group,
    build_settings_route_group as _build_settings_route_group,
    build_translation_route_handler as _build_translation_route_handler,
    build_wildcard_autocomplete_route_group as _build_wildcard_autocomplete_route_group,
)
from .easyuse_anima.api.routes.aio_profile_mutations import (
    build_aio_profile_mutation_handlers as _build_aio_profile_mutation_handlers,
)
from .easyuse_anima.api.routes import autocomplete as _api_autocomplete_routes
from .easyuse_anima.api.routes import long_text_settings as _api_long_text_routes
from .easyuse_anima.api.routes import lora_preview as _api_lora_preview_routes
from .easyuse_anima.api.routes.lora_profile_fix import (
    build_lora_profile_fix_handler as _build_lora_profile_fix_handler,
)
from .easyuse_anima.api.routes.profile_lists import (
    build_profile_list_handlers as _build_profile_list_handlers,
)
from .easyuse_anima.api.routes.profile_loads import (
    build_profile_load_handlers as _build_profile_load_handlers,
)
from .easyuse_anima.api.routes.profile_saves import (
    build_profile_save_handlers as _build_profile_save_handlers,
)
from .easyuse_anima.api.routes import settings as _api_settings_routes
from .easyuse_anima.api.routes import wildcards as _api_wildcard_routes
from .easyuse_anima.api.routes import translation as _api_translation_routes
from .easyuse_anima.api.routes.translation_execution import (
    PromptTranslationRouteExecutor as _PromptTranslationRouteExecutor,
)
from .easyuse_anima.aio.torch_compile_diagnostics import (
    collect_torch_compile_diagnostics as _collect_torch_compile_diagnostics,
)
from .easyuse_anima.aio.torch_compile_recommendation import (
    recommend_torch_compile as _recommend_torch_compile,
)
from .easyuse_anima.profiles import aio as _aio_profiles
from .easyuse_anima.profiles import contract as _profile_contract
from .easyuse_anima.profiles import lora as _lora_profiles
from .easyuse_anima.profiles import mutation as _profile_mutation
from .easyuse_anima.profiles import repository as _profile_repository

PROFILE_KIND_AIO = _profile_contract.PROFILE_KIND_AIO
PROFILE_KIND_LORA = _profile_contract.PROFILE_KIND_LORA
ProfileContractError = _profile_contract.ProfileContractError
build_profile_document = _profile_contract.build_profile_document
create_profile_document = _profile_contract.create_profile_document
interpret_profile_document = _profile_contract.interpret_profile_document
legacy_profile_id = _profile_contract.legacy_profile_id
normalize_profile_filename_identity = (
    _profile_contract.normalize_profile_filename_identity
)
rename_profile_document = _profile_contract.rename_profile_document
update_profile_document = _profile_contract.update_profile_document

PROFILE_MUTATION_COORDINATOR = _profile_mutation.PROFILE_MUTATION_COORDINATOR
ProfileMutationError = _profile_mutation.ProfileMutationError
ProfileRevisionConflictError = _profile_mutation.ProfileRevisionConflictError
require_profile_precondition = _profile_mutation.require_profile_precondition
verify_profile_precondition = _profile_mutation.verify_profile_precondition

INVALID_PROFILE_NAME_CHARS = _profile_repository.INVALID_PROFILE_NAME_CHARS
WINDOWS_RESERVED_FILE_BASENAMES = (
    _profile_repository.WINDOWS_RESERVED_FILE_BASENAMES
)
InvalidProfileDataError = _profile_repository.InvalidProfileDataError
_windows_profile_filename_identity = (
    _profile_repository._windows_profile_filename_identity
)
_sanitize_profile_name = _profile_repository._sanitize_profile_name
_read_profile_json = _profile_repository._read_profile_json
_profile_list_item = _profile_repository._profile_list_item

LORA_PROFILE_DIR = _lora_profiles.LORA_PROFILE_DIR
MAX_LORA_PROFILES = _lora_profiles.MAX_LORA_PROFILES
_sanitize_lora_profile_name = _lora_profiles._sanitize_lora_profile_name
_lora_profile_path = _lora_profiles._lora_profile_path
_find_lora_profile_path = _lora_profiles._find_lora_profile_path
_as_lora_profile_count = _lora_profiles._as_lora_profile_count
_as_lora_profile_index = _lora_profiles._as_lora_profile_index
_normalize_lora_profile_data = _lora_profiles._normalize_lora_profile_data
_normalize_lora_profile_payload = _lora_profiles._normalize_lora_profile_payload
_list_lora_profiles = _lora_profiles._list_lora_profiles
_clear_folder_paths_cache = _lora_profiles._clear_folder_paths_cache
_list_loras = _lora_profiles._list_loras
_lora_full_path = _lora_profiles._lora_full_path
_dedupe_text_values = _lora_profiles._dedupe_text_values
_lora_file_key = _lora_profiles._lora_file_key
_put_unique = _lora_profiles._put_unique
_lora_path_exists = _lora_profiles._lora_path_exists
_build_lora_fix_index = _lora_profiles._build_lora_fix_index
_resolve_lora_for_fix = _lora_profiles._resolve_lora_for_fix
_apply_lora_fix = _lora_profiles._apply_lora_fix
_fix_lora_profile_payload = _lora_profiles._fix_lora_profile_payload
_save_lora_profile = _lora_profiles._save_lora_profile
_load_lora_profile = _lora_profiles._load_lora_profile

AIO_PROFILE_DIR = _aio_profiles.AIO_PROFILE_DIR
MAX_AIO_PROFILES = _aio_profiles.MAX_AIO_PROFILES
MAX_AIO_PROFILE_BYTES = _aio_profiles.MAX_AIO_PROFILE_BYTES
AIO_RESERVED_PROFILE_NAMES = _aio_profiles.AIO_RESERVED_PROFILE_NAMES
_sanitize_aio_profile_name = _aio_profiles._sanitize_aio_profile_name
_aio_profile_path = _aio_profiles._aio_profile_path
_find_aio_profile_path = _aio_profiles._find_aio_profile_path
_normalize_aio_profile_payload = _aio_profiles._normalize_aio_profile_payload
_list_aio_profiles = _aio_profiles._list_aio_profiles
_validate_aio_profile_size = _aio_profiles._validate_aio_profile_size
_save_aio_profile = _aio_profiles._save_aio_profile
_normalize_stored_aio_profile_payload = (
    _aio_profiles._normalize_stored_aio_profile_payload
)
_load_aio_profile = _aio_profiles._load_aio_profile
_delete_aio_profile = _aio_profiles._delete_aio_profile
_rename_aio_profile = _aio_profiles._rename_aio_profile
_rename_aio_profile_payload = _aio_profiles._rename_aio_profile_payload


LORA_PREVIEW_EXTENSIONS = _api_lora_preview_routes.LORA_PREVIEW_EXTENSIONS
PROMPT_TRANSLATION_ROUTE_TIMEOUT_SECONDS = (
    _api_translation_routes.PROMPT_TRANSLATION_ROUTE_TIMEOUT_SECONDS
)
_LOGGER = logging.getLogger(__name__)


(
    _PROMPT_TRANSLATION_WORKER,
    _translate_prompt_sync,
    _translate_prompt_for_route,
    _prompt_translation_error_response,
) = _api_translation_routes.build_translation_runtime(
    executor_type=_PromptTranslationRouteExecutor,
    busy_error_type=TranslationBusyError,
    cancelled_error_type=TranslationCancelledError,
    timeout_error_type=TranslationTimeoutError,
    register_shutdown=lambda callback: atexit.register(callback),
    translate_prompt_markers=lambda text, settings: translate_prompt_markers(
        text,
        settings,
    ),
    resolve_prompt_translation_settings=lambda: resolve_prompt_translation_settings(),
    get_worker=lambda: _PROMPT_TRANSLATION_WORKER,
    get_translate_prompt_sync=lambda: _translate_prompt_sync,
    get_timeout_seconds=lambda: PROMPT_TRANSLATION_ROUTE_TIMEOUT_SECONDS,
    error_response=lambda *args, **kwargs: _error_response(*args, **kwargs),
)


_error_response = _api_responses.build_error_response(
    json_response=lambda payload, **kwargs: web.json_response(payload, **kwargs),
    build_error_payload=lambda code, message, **kwargs: error_payload(
        code,
        message,
        **kwargs,
    ),
)
_contract_error_response = _api_responses.build_contract_error_response(
    error_response=lambda *args, **kwargs: _error_response(*args, **kwargs),
)
_request_correlated = _api_responses.build_request_correlator(
    create_id=lambda: create_request_id(),
    get_http_exception_type=lambda: getattr(web, "HTTPException", ()),
    attach_id_header=lambda response, request_id: attach_request_id_header(
        response,
        request_id,
    ),
    correlate=lambda response, request_id: correlate_response(response, request_id),
    get_logger=lambda: _LOGGER,
    error_response=lambda *args, **kwargs: _error_response(*args, **kwargs),
)


_resolve_lora_preview_path = _api_lora_preview_routes.build_lora_preview_path_resolver(
    get_extensions=lambda: LORA_PREVIEW_EXTENSIONS,
    abspath=lambda path: os.path.abspath(path),
    dirname=lambda path: os.path.dirname(path),
    splitext=lambda path: os.path.splitext(path),
    commonpath=lambda paths: os.path.commonpath(paths),
    isfile=lambda path: os.path.isfile(path),
)


(
    _SAFE_PROFILE_VALIDATION_MESSAGES,
    _profile_error_response,
) = _api_responses.build_profile_error_response(
    max_aio_profiles=MAX_AIO_PROFILES,
    is_profile_mutation_error=lambda exc: isinstance(exc, ProfileMutationError),
    is_file_exists_error=lambda exc: isinstance(exc, FileExistsError),
    is_file_not_found_error=lambda exc: isinstance(exc, FileNotFoundError),
    is_invalid_profile_data_error=lambda exc: isinstance(
        exc,
        (json.JSONDecodeError, UnicodeDecodeError, InvalidProfileDataError),
    ),
    is_value_error=lambda exc: isinstance(exc, ValueError),
    get_safe_validation_messages=lambda: _SAFE_PROFILE_VALIDATION_MESSAGES,
    error_response=lambda *args, **kwargs: _error_response(*args, **kwargs),
)


(
    _get_settings_payload_sync,
    _save_setting_payload_sync,
) = _api_settings_routes.build_settings_payloads(
    public_settings=lambda: public_settings(),
    save_setting=lambda key, value: save_setting(key, value),
)


(
    _get_long_text_settings_payload_sync,
    _save_long_text_settings_payload_sync,
) = _api_long_text_routes.build_long_text_settings_payloads(
    load_long_text_settings=lambda: load_long_text_settings(),
    save_long_text_settings=lambda values: save_long_text_settings(values),
    public_settings=lambda: public_settings(),
)


_wildcards_payload_sync = _api_wildcard_routes.build_wildcards_payload(
    public_settings=lambda: public_settings(),
    resolve_wildcard_roots=lambda extra_paths: resolve_wildcard_roots(extra_paths),
    list_wildcards=lambda **kwargs: list_wildcards(**kwargs),
)


(
    _autocomplete_status_payload_sync,
    _public_autocomplete_status,
    _public_autocomplete_payload,
    _search_autocomplete_payload_sync,
    _classify_prompt_payload_sync,
) = _api_autocomplete_routes.build_autocomplete_payloads(
    resolve_autocomplete_source=lambda: resolve_autocomplete_source(),
    resolve_autocomplete_source_path=lambda source: resolve_autocomplete_source_path(
        source
    ),
    autocomplete_status=lambda path: autocomplete_status(path),
    available_autocomplete_sources=lambda source: available_autocomplete_sources(
        source
    ),
    resolve_autocomplete_limit=lambda: resolve_autocomplete_limit(),
    search_autocomplete=lambda query, **kwargs: search_autocomplete(query, **kwargs),
    classify_prompt_text=lambda text, **kwargs: classify_prompt_text(text, **kwargs),
    public_autocomplete_status=lambda status: _public_autocomplete_status(status),
    public_autocomplete_payload=lambda payload: _public_autocomplete_payload(payload),
)


_get_prompt_routes = _api_router.build_prompt_routes_resolver(
    resolve_server=lambda: server,
)


routes = _get_prompt_routes()


if web is not None:
    (
        get_settings_handler,
        set_setting_handler,
        get_long_text_settings_handler,
        save_long_text_settings_handler,
    ) = _build_settings_route_group(
        request_correlated=_request_correlated,
        settings_dependencies={
            "parse_json_object": parse_json_object,
            "json_string": json_string,
            "contract_error_type": ApiContractError,
            "contract_error_response": lambda exc: _contract_error_response(exc),
            "run_file_io": lambda function, *args, **kwargs: _run_file_io(
                function,
                *args,
                **kwargs,
            ),
            "get_settings_payload": lambda: _get_settings_payload_sync(),
            "save_setting_payload": lambda key, value: _save_setting_payload_sync(
                key,
                value,
            ),
            "unknown_setting_error_type": KeyError,
            "unknown_setting_response": lambda: _error_response(
                422,
                "unknown_setting",
                "Unknown setting",
            ),
            "json_response": lambda payload: web.json_response(payload),
        },
        long_text_settings_dependencies={
            "parse_json_object": lambda request: parse_json_object(request),
            "json_object": lambda data, field: json_object(data, field),
            "contract_error_type": ApiContractError,
            "contract_error_response": lambda exc: _contract_error_response(exc),
            "run_file_io": lambda function, *args: _run_file_io(function, *args),
            "get_long_text_settings_payload": lambda: _get_long_text_settings_payload_sync(),
            "save_long_text_settings_payload": lambda values: _save_long_text_settings_payload_sync(
                values
            ),
            "json_response": lambda payload: web.json_response(payload),
        },
    )

    (
        get_wildcards_handler,
        autocomplete_status_handler,
        autocomplete_handler,
        classify_prompt_handler,
    ) = _build_wildcard_autocomplete_route_group(
        request_correlated=_request_correlated,
        wildcards_dependencies={
            "run_file_io": lambda function, *args: _run_file_io(function, *args),
            "wildcards_payload": lambda: _wildcards_payload_sync(),
            "json_response": lambda payload: web.json_response(payload),
        },
        autocomplete_dependencies={
            "run_file_io": lambda function, *args: _run_file_io(function, *args),
            "autocomplete_status_payload": lambda: _autocomplete_status_payload_sync(),
            "search_autocomplete_payload": lambda *args: _search_autocomplete_payload_sync(
                *args
            ),
            "json_response": lambda payload: web.json_response(payload),
        },
        classify_prompt_dependencies={
            "parse_json_object": lambda request: parse_json_object(request),
            "json_string": lambda data, field: json_string(data, field),
            "json_integer": lambda data, field, **kwargs: json_integer(
                data,
                field,
                **kwargs,
            ),
            "contract_error_type": ApiContractError,
            "contract_error_response": lambda exc: _contract_error_response(exc),
            "run_file_io": lambda function, *args: _run_file_io(function, *args),
            "classify_prompt_payload": lambda *args: _classify_prompt_payload_sync(
                *args
            ),
            "json_response": lambda payload: web.json_response(payload),
        },
    )

    translate_prompt_handler = _build_translation_route_handler(
        request_correlated=_request_correlated,
        translation_dependencies={
            "parse_json_object": lambda request: parse_json_object(request),
            "json_string": lambda data, field: json_string(data, field),
            "contract_error_type": ApiContractError,
            "contract_error_response": lambda exc: _contract_error_response(exc),
            "translate_prompt": lambda text: _translate_prompt_for_route(text),
            "translation_error_type": PromptTranslationError,
            "translation_error_response": lambda exc: _prompt_translation_error_response(
                exc
            ),
            "json_response": lambda payload: web.json_response(payload),
        },
    )

    aio_torch_compile_recommend_handler = _build_aio_torch_compile_route_handler(
        request_correlated=_request_correlated,
        aio_torch_compile_dependencies={
            "parse_json_object": lambda request: parse_json_object(request),
            "json_object": lambda data, field: json_object(data, field),
            "json_integer": lambda data, field, **kwargs: json_integer(
                data,
                field,
                **kwargs,
            ),
            "contract_error_type": ApiContractError,
            "contract_error_response": lambda exc: _contract_error_response(exc),
            "collect_diagnostics": lambda: _collect_torch_compile_diagnostics(),
            "recommend_torch_compile": lambda *args: _recommend_torch_compile(*args),
            "json_response": lambda payload: web.json_response(payload),
        },
    )

    (
        lora_preview_handler,
        loras_handler,
    ) = _build_lora_read_route_group(
        request_correlated=_request_correlated,
        lora_preview_dependencies={
            "run_file_io": lambda function, *args: _run_file_io(function, *args),
            "resolve_lora_preview_path": lambda name: _resolve_lora_preview_path(
                name
            ),
            "empty_response": lambda **kwargs: web.Response(**kwargs),
            "file_response": lambda path, **kwargs: web.FileResponse(
                path,
                **kwargs,
            ),
            "basename": lambda path: os.path.basename(path),
        },
        lora_catalog_dependencies={
            "run_file_io": lambda function, *args: _run_file_io(function, *args),
            "list_loras": lambda: _list_loras(),
            "json_response": lambda payload: web.json_response(payload),
        },
    )

    (
        lora_profiles_handler,
        aio_profiles_handler,
    ) = (
        _request_correlated(handler)
        for handler in _build_profile_list_handlers(
            run_file_io=lambda function, *args: _run_file_io(function, *args),
            list_lora_profiles=lambda: _list_lora_profiles(),
            list_aio_profiles=lambda: _list_aio_profiles(),
            profile_data_error_type=InvalidProfileDataError,
            profile_error_response=lambda exc: _profile_error_response(exc),
            json_response=lambda payload: web.json_response(payload),
        )
    )

    (
        load_lora_profile_handler,
        load_aio_profile_handler,
    ) = (
        _request_correlated(handler)
        for handler in _build_profile_load_handlers(
            run_file_io=lambda function, *args: _run_file_io(function, *args),
            load_lora_profile=lambda name: _load_lora_profile(name),
            load_aio_profile=lambda name: _load_aio_profile(name),
            lora_load_error_types=(
                json.JSONDecodeError,
                UnicodeDecodeError,
                FileNotFoundError,
                ValueError,
            ),
            aio_load_error_types=(FileNotFoundError, ValueError),
            profile_error_response=lambda exc: _profile_error_response(exc),
            json_response=lambda payload: web.json_response(payload),
        )
    )

    (
        save_lora_profile_handler,
        save_aio_profile_handler,
    ) = (
        _request_correlated(handler)
        for handler in _build_profile_save_handlers(
            parse_json_object=parse_json_object,
            json_string=json_string,
            json_boolean=json_boolean,
            json_object=json_object,
            json_uuid_string=json_uuid_string,
            json_integer=json_integer,
            contract_error_type=ApiContractError,
            contract_error_response=lambda exc: _contract_error_response(exc),
            run_file_io=lambda function, *args, **kwargs: _run_file_io(
                function,
                *args,
                **kwargs,
            ),
            save_lora_profile=lambda name, data, **kwargs: _save_lora_profile(
                name,
                data,
                **kwargs,
            ),
            save_aio_profile=lambda name, data, **kwargs: _save_aio_profile(
                name,
                data,
                **kwargs,
            ),
            save_error_types=(FileExistsError, FileNotFoundError, ValueError),
            profile_error_response=lambda exc: _profile_error_response(exc),
            json_response=lambda payload: web.json_response(payload),
        )
    )

    (
        delete_aio_profile_handler,
        rename_aio_profile_handler,
    ) = (
        _request_correlated(handler)
        for handler in _build_aio_profile_mutation_handlers(
            parse_json_object=parse_json_object,
            json_string=json_string,
            json_boolean=json_boolean,
            json_uuid_string=json_uuid_string,
            json_integer=json_integer,
            contract_error_type=ApiContractError,
            contract_error_response=lambda exc: _contract_error_response(exc),
            run_file_io=lambda function, *args, **kwargs: _run_file_io(
                function,
                *args,
                **kwargs,
            ),
            delete_aio_profile=lambda name, **kwargs: _delete_aio_profile(
                name,
                **kwargs,
            ),
            rename_aio_profile=lambda old_name, new_name, **kwargs: (
                _rename_aio_profile(
                    old_name,
                    new_name,
                    **kwargs,
                )
            ),
            delete_error_types=(FileNotFoundError, ValueError),
            rename_error_types=(FileExistsError, FileNotFoundError, ValueError),
            profile_error_response=lambda exc: _profile_error_response(exc),
            json_response=lambda payload: web.json_response(payload),
        )
    )

    fix_lora_profile_handler = _request_correlated(
        _build_lora_profile_fix_handler(
            parse_json_object=parse_json_object,
            json_object=json_object,
            contract_error_type=ApiContractError,
            contract_error_response=lambda exc: _contract_error_response(exc),
            run_file_io=lambda function, *args, **kwargs: _run_file_io(
                function,
                *args,
                **kwargs,
            ),
            fix_lora_profile=lambda data: _fix_lora_profile_payload(data),
            json_response=lambda payload: web.json_response(payload),
        )
    )

    _ROUTE_DEFINITIONS = _build_route_definitions(
        get_settings_handler=get_settings_handler,
        set_setting_handler=set_setting_handler,
        get_long_text_settings_handler=get_long_text_settings_handler,
        get_wildcards_handler=get_wildcards_handler,
        save_long_text_settings_handler=save_long_text_settings_handler,
        autocomplete_status_handler=autocomplete_status_handler,
        autocomplete_handler=autocomplete_handler,
        classify_prompt_handler=classify_prompt_handler,
        translate_prompt_handler=translate_prompt_handler,
        aio_torch_compile_recommend_handler=aio_torch_compile_recommend_handler,
        lora_preview_handler=lora_preview_handler,
        loras_handler=loras_handler,
        lora_profiles_handler=lora_profiles_handler,
        save_lora_profile_handler=save_lora_profile_handler,
        load_lora_profile_handler=load_lora_profile_handler,
        aio_profiles_handler=aio_profiles_handler,
        save_aio_profile_handler=save_aio_profile_handler,
        load_aio_profile_handler=load_aio_profile_handler,
        delete_aio_profile_handler=delete_aio_profile_handler,
        rename_aio_profile_handler=rename_aio_profile_handler,
        fix_lora_profile_handler=fix_lora_profile_handler,
    )
else:
    _ROUTE_DEFINITIONS = ()


_ROUTE_SIGNATURE = _build_route_signature(_ROUTE_DEFINITIONS)


register_routes = _api_router.build_route_registrar(
    resolve_prompt_routes=lambda: _get_prompt_routes(),
    publish_routes=lambda target: globals().__setitem__("routes", target),
    resolve_web=lambda: web,
    resolve_route_definitions=lambda: _ROUTE_DEFINITIONS,
    resolve_route_signature=lambda: _ROUTE_SIGNATURE,
    register_route_definitions=lambda *args, **kwargs: _register_route_definitions(
        *args,
        **kwargs,
    ),
    marker=_ROUTE_REGISTRATION_MARKER,
)
