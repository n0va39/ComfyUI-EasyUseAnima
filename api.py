from __future__ import annotations

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

from .easyuse_anima.aio.torch_compile_diagnostics import (
    collect_torch_compile_diagnostics as _collect_torch_compile_diagnostics,
)
from .easyuse_anima.aio.torch_compile_recommendation import (
    recommend_torch_compile as _recommend_torch_compile,
)
from .easyuse_anima.api import responses as _api_responses
from .easyuse_anima.api import router as _api_router
from .easyuse_anima.api.dependencies import (
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
from .easyuse_anima.api.dependencies import (
    _late_application_attribute as _late_attr,
)
from .easyuse_anima.api.dependencies import (
    _late_application_dependency as _late,
)
from .easyuse_anima.api.dependencies import (
    _late_application_value as _late_value,
)
from .easyuse_anima.api.dependencies import (
    _read_application_dependency as _read,
)
from .easyuse_anima.api.errors import ApiContractError
from .easyuse_anima.api.file_io import (
    _FILE_IO_LIMITERS,
    _FILE_IO_LIMITERS_LOCK,
    FILE_IO_MAX_IN_FLIGHT,
)
from .easyuse_anima.api.file_io import (
    file_io_limiter as _file_io_limiter,
)
from .easyuse_anima.api.file_io import (
    release_file_io_slot as _release_file_io_slot,
)
from .easyuse_anima.api.file_io import (
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
from .easyuse_anima.api.responses import (
    attach_request_id_header,
    correlate_response,
    create_request_id,
    error_payload,
)
from .easyuse_anima.api.router import (
    ROUTE_REGISTRATION_MARKER as _ROUTE_REGISTRATION_MARKER,
)
from .easyuse_anima.api.router import (
    build_route_definitions as _build_route_definitions,
)
from .easyuse_anima.api.router import (
    build_route_signature as _build_route_signature,
)
from .easyuse_anima.api.router import (
    register_route_definitions as _register_route_definitions,
)
from .easyuse_anima.api.routes import autocomplete as _api_autocomplete_routes
from .easyuse_anima.api.routes import long_text_settings as _api_long_text_routes
from .easyuse_anima.api.routes import lora_preview as _api_lora_preview_routes
from .easyuse_anima.api.routes import settings as _api_settings_routes
from .easyuse_anima.api.routes import translation as _api_translation_routes
from .easyuse_anima.api.routes import wildcards as _api_wildcard_routes
from .easyuse_anima.autocomplete.classification import (
    classify_prompt_text as _canonical_classify_prompt_text,
)
from .easyuse_anima.autocomplete.dataset import (
    AUTOCOMPLETE_CSV,
)
from .easyuse_anima.autocomplete.dataset import (
    autocomplete_status as _canonical_autocomplete_status,
)
from .easyuse_anima.autocomplete.dataset import (
    available_autocomplete_sources as _canonical_available_autocomplete_sources,
)
from .easyuse_anima.autocomplete.dataset import (
    resolve_autocomplete_source as _canonical_resolve_autocomplete_source_path,
)
from .easyuse_anima.autocomplete.search import (
    search_autocomplete as _canonical_search_autocomplete,
)
from .easyuse_anima.bootstrap import (
    build_aio_torch_compile_route_handler as _build_aio_torch_compile_route_handler,
)
from .easyuse_anima.bootstrap import (
    build_lora_read_route_group as _build_lora_read_route_group,
)
from .easyuse_anima.bootstrap import (
    build_profile_list_route_group as _build_profile_list_route_group,
)
from .easyuse_anima.bootstrap import (
    build_profile_route_group as _build_profile_route_group,
)
from .easyuse_anima.bootstrap import (
    build_settings_route_group as _build_settings_route_group,
)
from .easyuse_anima.bootstrap import (
    build_translation_route_handler as _build_translation_route_handler,
)
from .easyuse_anima.bootstrap import (
    build_translation_route_runtime as _build_translation_route_runtime,
)
from .easyuse_anima.bootstrap import (
    build_wildcard_autocomplete_route_group as _build_wildcard_autocomplete_route_group,
)
from .easyuse_anima.profiles import aio as _aio_profiles
from .easyuse_anima.profiles import contract as _profile_contract
from .easyuse_anima.profiles import lora as _lora_profiles
from .easyuse_anima.profiles import mutation as _profile_mutation
from .easyuse_anima.profiles import repository as _profile_repository
from .easyuse_anima.runtime import get_runtime as _get_runtime
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
from .easyuse_anima.translation.contracts import (
    PromptTranslationError,
    TranslationBusyError,
    TranslationCancelledError,
    TranslationTimeoutError,
)
from .easyuse_anima.translation.service import (
    translate_prompt_markers,
)
from .easyuse_anima.wildcard.service import list_wildcards
from .easyuse_anima.wildcard.sources import resolve_wildcard_roots

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
_ROOT_COMPATIBILITY_ALIASES = (
    asyncio,
    TranslationBusyError,
    TranslationCancelledError,
    TranslationTimeoutError,
    FILE_IO_MAX_IN_FLIGHT,
    _FILE_IO_LIMITERS,
    _FILE_IO_LIMITERS_LOCK,
    _file_io_limiter,
    _release_file_io_slot,
)


def _runtime_autocomplete():
    try:
        return _read("wildcard_autocomplete", "get_runtime")().autocomplete
    except RuntimeError as exc:
        if str(exc) != "[EasyUseAnima] RuntimeServices has not been installed.":
            raise
        return None


def resolve_autocomplete_source_path(source=None):
    autocomplete = _runtime_autocomplete()
    if autocomplete is None:
        return _canonical_resolve_autocomplete_source_path(source)
    return autocomplete.resolve_source(source)


def available_autocomplete_sources(selected=None):
    autocomplete = _runtime_autocomplete()
    if autocomplete is None:
        return _canonical_available_autocomplete_sources(selected)
    return autocomplete.available_sources(selected)


def autocomplete_status(path=AUTOCOMPLETE_CSV):
    autocomplete = _runtime_autocomplete()
    if autocomplete is None:
        return _canonical_autocomplete_status(path)
    return autocomplete.status(path)


def search_autocomplete(
    query,
    limit=20,
    path=AUTOCOMPLETE_CSV,
    category=None,
):
    autocomplete = _runtime_autocomplete()
    if autocomplete is None:
        return _canonical_search_autocomplete(
            query,
            limit=limit,
            path=path,
            category=category,
        )
    return autocomplete.search(
        query,
        limit=limit,
        path=path,
        category=category,
    )


def classify_prompt_text(
    text,
    limit=240,
    path=AUTOCOMPLETE_CSV,
):
    autocomplete = _runtime_autocomplete()
    if autocomplete is None:
        return _canonical_classify_prompt_text(
            text,
            limit=limit,
            path=path,
        )
    return autocomplete.classify(
        text,
        limit=limit,
        path=path,
    )


(
    _PROMPT_TRANSLATION_WORKER,
    _translate_prompt_sync,
    _translate_prompt_for_route,
    _prompt_translation_error_response,
) = _build_translation_route_runtime(
    translate_prompt_markers=_late("translation", "translate_prompt_markers"),
    resolve_prompt_translation_settings=_late(
        "translation", "resolve_prompt_translation_settings"
    ),
    get_worker=lambda: _PROMPT_TRANSLATION_WORKER,
    get_translate_prompt_sync=lambda: _translate_prompt_sync,
    get_timeout_seconds=_late_value("translation", "route_timeout_seconds"),
    error_response=_late("request", "error_response"),
)


_error_response = _api_responses.build_error_response(
    json_response=_late_attr("host", "web", "json_response"),
    build_error_payload=lambda code, message, **kwargs: error_payload(
        code,
        message,
        **kwargs,
    ),
)
_contract_error_response = _api_responses.build_contract_error_response(
    error_response=_late("request", "error_response"),
)
_request_correlated = _api_responses.build_request_correlator(
    create_id=_late("request", "create_request_id"),
    get_http_exception_type=lambda: getattr(
        _read("host", "web"),
        "HTTPException",
        (),
    ),
    attach_id_header=attach_request_id_header,
    correlate=correlate_response,
    get_logger=lambda: _LOGGER,
    error_response=_late("request", "error_response"),
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
    profile_mutation_error_types={
        "precondition_required": _profile_mutation.ProfilePreconditionRequiredError,
        "identity_mismatch": _profile_mutation.ProfileIdentityMismatchError,
        "revision_conflict": _profile_mutation.ProfileRevisionConflictError,
    },
    is_profile_mutation_error=lambda exc: isinstance(
        exc,
        _read("request", "profile_mutation_error_type"),
    ),
    is_file_exists_error=lambda exc: isinstance(exc, FileExistsError),
    is_file_not_found_error=lambda exc: isinstance(exc, FileNotFoundError),
    is_invalid_profile_data_error=lambda exc: isinstance(
        exc,
        (json.JSONDecodeError, UnicodeDecodeError, InvalidProfileDataError),
    ),
    is_value_error=lambda exc: isinstance(exc, ValueError),
    get_safe_validation_messages=_late_value(
        "request", "safe_profile_validation_messages"
    ),
    error_response=_late("request", "error_response"),
)


(
    _get_settings_payload_sync,
    _save_setting_payload_sync,
) = _api_settings_routes.build_settings_payloads(
    public_settings=_late("settings", "public_settings"),
    save_setting=_late("settings", "save_setting"),
)


(
    _get_long_text_settings_payload_sync,
    _save_long_text_settings_payload_sync,
) = _api_long_text_routes.build_long_text_settings_payloads(
    load_long_text_settings=_late("settings", "load_long_text_settings"),
    save_long_text_settings=_late("settings", "save_long_text_settings"),
    public_settings=_late("settings", "public_settings"),
)


_wildcards_payload_sync = _api_wildcard_routes.build_wildcards_payload(
    public_settings=_late("settings", "public_settings"),
    resolve_wildcard_roots=_late("wildcard_autocomplete", "resolve_wildcard_roots"),
    list_wildcards=_late("wildcard_autocomplete", "list_wildcards"),
)


(
    _autocomplete_status_payload_sync,
    _public_autocomplete_status,
    _public_autocomplete_payload,
    _search_autocomplete_payload_sync,
    _classify_prompt_payload_sync,
) = _api_autocomplete_routes.build_autocomplete_payloads(
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


_get_prompt_routes = _api_router.build_prompt_routes_resolver(
    resolve_server=_late_value("host", "server"),
)


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
            "contract_error_response": _late("request", "contract_error_response"),
            "run_file_io": _late("request", "run_file_io"),
            "get_settings_payload": _late("settings", "get_settings_payload"),
            "save_setting_payload": _late("settings", "save_setting_payload"),
            "unknown_setting_error_type": KeyError,
            "unknown_setting_response": lambda: _read("request", "error_response")(
                422,
                "unknown_setting",
                "Unknown setting",
            ),
            "json_response": _late_attr("host", "web", "json_response"),
        },
        long_text_settings_dependencies={
            "parse_json_object": parse_json_object,
            "json_object": json_object,
            "contract_error_type": ApiContractError,
            "contract_error_response": _late("request", "contract_error_response"),
            "run_file_io": _late("request", "run_file_io"),
            "get_long_text_settings_payload": _late(
                "settings", "get_long_text_settings_payload"
            ),
            "save_long_text_settings_payload": _late(
                "settings", "save_long_text_settings_payload"
            ),
            "json_response": _late_attr("host", "web", "json_response"),
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
            "run_file_io": _late("request", "run_file_io"),
            "wildcards_payload": _late(
                "wildcard_autocomplete", "wildcards_payload"
            ),
            "json_response": _late_attr("host", "web", "json_response"),
        },
        autocomplete_dependencies={
            "run_file_io": _late("request", "run_file_io"),
            "autocomplete_status_payload": _late(
                "wildcard_autocomplete", "autocomplete_status_payload"
            ),
            "search_autocomplete_payload": _late(
                "wildcard_autocomplete", "search_autocomplete_payload"
            ),
            "json_response": _late_attr("host", "web", "json_response"),
        },
        classify_prompt_dependencies={
            "parse_json_object": parse_json_object,
            "json_string": json_string,
            "json_integer": json_integer,
            "contract_error_type": ApiContractError,
            "contract_error_response": _late("request", "contract_error_response"),
            "run_file_io": _late("request", "run_file_io"),
            "classify_prompt_payload": _late(
                "wildcard_autocomplete", "classify_prompt_payload"
            ),
            "json_response": _late_attr("host", "web", "json_response"),
        },
    )

    translate_prompt_handler = _build_translation_route_handler(
        request_correlated=_request_correlated,
        translation_dependencies={
            "parse_json_object": parse_json_object,
            "json_string": json_string,
            "contract_error_type": ApiContractError,
            "contract_error_response": _late("request", "contract_error_response"),
            "translate_prompt": lambda text: _translate_prompt_for_route(text),
            "get_translation_error_type": _late_value(
                "translation", "prompt_translation_error_type"
            ),
            "translation_error_response": _late(
                "translation", "prompt_translation_error_response"
            ),
            "json_response": _late_attr("host", "web", "json_response"),
        },
    )

    aio_torch_compile_recommend_handler = _build_aio_torch_compile_route_handler(
        request_correlated=_request_correlated,
        aio_torch_compile_dependencies={
            "parse_json_object": parse_json_object,
            "json_object": json_object,
            "json_integer": json_integer,
            "contract_error_type": ApiContractError,
            "contract_error_response": _late("request", "contract_error_response"),
            "collect_diagnostics": _late("torch_compile", "collect_diagnostics"),
            "recommend_torch_compile": _late(
                "torch_compile", "recommend_torch_compile"
            ),
            "json_response": _late_attr("host", "web", "json_response"),
        },
    )

    (
        lora_preview_handler,
        loras_handler,
    ) = _build_lora_read_route_group(
        request_correlated=_request_correlated,
        lora_preview_dependencies={
            "run_file_io": _late("request", "run_file_io"),
            "resolve_lora_preview_path": _late(
                "profiles", "resolve_lora_preview_path"
            ),
            "empty_response": _late_attr("host", "web", "Response"),
            "file_response": _late_attr("host", "web", "FileResponse"),
            "basename": os.path.basename,
        },
        lora_catalog_dependencies={
            "run_file_io": _late("request", "run_file_io"),
            "list_loras": _late("profiles", "list_loras"),
            "json_response": _late_attr("host", "web", "json_response"),
        },
    )

    (
        lora_profiles_handler,
        aio_profiles_handler,
    ) = _build_profile_list_route_group(
        request_correlated=_request_correlated,
        profile_list_dependencies={
            "run_file_io": _late("request", "run_file_io"),
            "list_lora_profiles": _late("profiles", "list_lora_profiles"),
            "list_aio_profiles": _late("profiles", "list_aio_profiles"),
            "profile_data_error_type": InvalidProfileDataError,
            "profile_error_response": _late("request", "profile_error_response"),
            "json_response": _late_attr("host", "web", "json_response"),
        },
    )

    (
        load_lora_profile_handler,
        load_aio_profile_handler,
        save_lora_profile_handler,
        save_aio_profile_handler,
        delete_aio_profile_handler,
        rename_aio_profile_handler,
        fix_lora_profile_handler,
    ) = _build_profile_route_group(
        request_correlated=_request_correlated,
        profile_load_dependencies={
            "run_file_io": _late("request", "run_file_io"),
            "load_lora_profile": _late("profiles", "load_lora_profile"),
            "load_aio_profile": _late("profiles", "load_aio_profile"),
            "lora_load_error_types": (
                json.JSONDecodeError,
                UnicodeDecodeError,
                FileNotFoundError,
                ValueError,
            ),
            "aio_load_error_types": (FileNotFoundError, ValueError),
            "profile_error_response": _late("request", "profile_error_response"),
            "json_response": _late_attr("host", "web", "json_response"),
        },
        profile_save_dependencies={
            "parse_json_object": parse_json_object,
            "json_string": json_string,
            "json_boolean": json_boolean,
            "json_object": json_object,
            "json_uuid_string": json_uuid_string,
            "json_integer": json_integer,
            "contract_error_type": ApiContractError,
            "contract_error_response": _late("request", "contract_error_response"),
            "run_file_io": _late("request", "run_file_io"),
            "save_lora_profile": _late("profiles", "save_lora_profile"),
            "save_aio_profile": _late("profiles", "save_aio_profile"),
            "save_error_types": (
                FileExistsError,
                FileNotFoundError,
                ValueError,
            ),
            "profile_error_response": _late("request", "profile_error_response"),
            "json_response": _late_attr("host", "web", "json_response"),
        },
        aio_profile_mutation_dependencies={
            "parse_json_object": parse_json_object,
            "json_string": json_string,
            "json_boolean": json_boolean,
            "json_uuid_string": json_uuid_string,
            "json_integer": json_integer,
            "contract_error_type": ApiContractError,
            "contract_error_response": _late("request", "contract_error_response"),
            "run_file_io": _late("request", "run_file_io"),
            "delete_aio_profile": _late("profiles", "delete_aio_profile"),
            "rename_aio_profile": _late("profiles", "rename_aio_profile"),
            "delete_error_types": (FileNotFoundError, ValueError),
            "rename_error_types": (
                FileExistsError,
                FileNotFoundError,
                ValueError,
            ),
            "profile_error_response": _late("request", "profile_error_response"),
            "json_response": _late_attr("host", "web", "json_response"),
        },
        lora_profile_fix_dependencies={
            "parse_json_object": parse_json_object,
            "json_object": json_object,
            "contract_error_type": ApiContractError,
            "contract_error_response": _late("request", "contract_error_response"),
            "run_file_io": _late("request", "run_file_io"),
            "fix_lora_profile": _late("profiles", "fix_lora_profile_payload"),
            "json_response": _late_attr("host", "web", "json_response"),
        },
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


_APPLICATION_DEPENDENCIES = _publish_application_dependencies(
    ApiApplicationDependencies(
        host=ApiHostDependencies(
            server=server,
            web=web,
            get_prompt_routes=_get_prompt_routes,
            route_definitions=_ROUTE_DEFINITIONS,
            route_signature=_ROUTE_SIGNATURE,
            register_route_definitions=_register_route_definitions,
        ),
        request=ApiRequestDependencies(
            create_request_id=create_request_id,
            run_file_io=_run_file_io,
            error_response=_error_response,
            contract_error_response=_contract_error_response,
            profile_error_response=_profile_error_response,
            profile_mutation_error_type=ProfileMutationError,
            safe_profile_validation_messages=_SAFE_PROFILE_VALIDATION_MESSAGES,
        ),
        settings=ApiSettingsDependencies(
            public_settings=public_settings,
            save_setting=save_setting,
            load_long_text_settings=load_long_text_settings,
            save_long_text_settings=save_long_text_settings,
            get_settings_payload=_get_settings_payload_sync,
            save_setting_payload=_save_setting_payload_sync,
            get_long_text_settings_payload=_get_long_text_settings_payload_sync,
            save_long_text_settings_payload=_save_long_text_settings_payload_sync,
        ),
        wildcard_autocomplete=ApiWildcardAutocompleteDependencies(
            get_runtime=_get_runtime,
            resolve_wildcard_roots=resolve_wildcard_roots,
            list_wildcards=list_wildcards,
            resolve_autocomplete_source=resolve_autocomplete_source,
            resolve_autocomplete_source_path=resolve_autocomplete_source_path,
            resolve_autocomplete_limit=resolve_autocomplete_limit,
            available_autocomplete_sources=available_autocomplete_sources,
            autocomplete_status=autocomplete_status,
            search_autocomplete=search_autocomplete,
            classify_prompt_text=classify_prompt_text,
            wildcards_payload=_wildcards_payload_sync,
            autocomplete_status_payload=_autocomplete_status_payload_sync,
            search_autocomplete_payload=_search_autocomplete_payload_sync,
            classify_prompt_payload=_classify_prompt_payload_sync,
            public_autocomplete_status=_public_autocomplete_status,
            public_autocomplete_payload=_public_autocomplete_payload,
        ),
        profiles=ApiProfileDependencies(
            list_loras=_list_loras,
            list_lora_profiles=_list_lora_profiles,
            list_aio_profiles=_list_aio_profiles,
            load_lora_profile=_load_lora_profile,
            load_aio_profile=_load_aio_profile,
            save_lora_profile=_save_lora_profile,
            save_aio_profile=_save_aio_profile,
            delete_aio_profile=_delete_aio_profile,
            rename_aio_profile=_rename_aio_profile,
            fix_lora_profile_payload=_fix_lora_profile_payload,
            resolve_lora_preview_path=_resolve_lora_preview_path,
        ),
        translation=ApiTranslationDependencies(
            translate_prompt_markers=translate_prompt_markers,
            resolve_prompt_translation_settings=resolve_prompt_translation_settings,
            route_timeout_seconds=PROMPT_TRANSLATION_ROUTE_TIMEOUT_SECONDS,
            prompt_translation_error_type=PromptTranslationError,
            prompt_translation_error_response=_prompt_translation_error_response,
        ),
        torch_compile=ApiTorchCompileDependencies(
            collect_diagnostics=_collect_torch_compile_diagnostics,
            recommend_torch_compile=_recommend_torch_compile,
        ),
    )
)


routes = _read("host", "get_prompt_routes")()


register_routes = _api_router.build_route_registrar(
    resolve_prompt_routes=_late("host", "get_prompt_routes"),
    publish_routes=lambda target: globals().__setitem__("routes", target),
    resolve_web=_late_value("host", "web"),
    resolve_route_definitions=_late_value("host", "route_definitions"),
    resolve_route_signature=_late_value("host", "route_signature"),
    register_route_definitions=_late("host", "register_route_definitions"),
    marker=_ROUTE_REGISTRATION_MARKER,
)
