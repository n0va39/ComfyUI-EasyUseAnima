from __future__ import annotations

import asyncio
import json
import logging
import os

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
from .easyuse_anima.api.file_io import file_io_limiter as _file_io_limiter
from .easyuse_anima.api.file_io import release_file_io_slot as _release_file_io_slot
from .easyuse_anima.api.file_io import run_file_io as _run_file_io
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
from .easyuse_anima.api.router import build_route_signature as _build_route_signature
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
from .easyuse_anima.autocomplete.dataset import AUTOCOMPLETE_CSV
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
from .easyuse_anima.bootstrap import _compose_api_application
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
from .easyuse_anima.translation.service import translate_prompt_markers
from .easyuse_anima.wildcard.service import list_wildcards
from .easyuse_anima.wildcard.sources import resolve_wildcard_roots

PROFILE_KIND_AIO = _profile_contract.PROFILE_KIND_AIO
PROFILE_KIND_LORA = _profile_contract.PROFILE_KIND_LORA
ProfileContractError = _profile_contract.ProfileContractError
build_profile_document = _profile_contract.build_profile_document
create_profile_document = _profile_contract.create_profile_document
interpret_profile_document = _profile_contract.interpret_profile_document
legacy_profile_id = _profile_contract.legacy_profile_id
normalize_profile_filename_identity = _profile_contract.normalize_profile_filename_identity
rename_profile_document = _profile_contract.rename_profile_document
update_profile_document = _profile_contract.update_profile_document

PROFILE_MUTATION_COORDINATOR = _profile_mutation.PROFILE_MUTATION_COORDINATOR
ProfileMutationError = _profile_mutation.ProfileMutationError
ProfileRevisionConflictError = _profile_mutation.ProfileRevisionConflictError
require_profile_precondition = _profile_mutation.require_profile_precondition
verify_profile_precondition = _profile_mutation.verify_profile_precondition

INVALID_PROFILE_NAME_CHARS = _profile_repository.INVALID_PROFILE_NAME_CHARS
WINDOWS_RESERVED_FILE_BASENAMES = _profile_repository.WINDOWS_RESERVED_FILE_BASENAMES
InvalidProfileDataError = _profile_repository.InvalidProfileDataError
_windows_profile_filename_identity = _profile_repository._windows_profile_filename_identity
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
_normalize_stored_aio_profile_payload = _aio_profiles._normalize_stored_aio_profile_payload
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
    json,
    os,
    _collect_torch_compile_diagnostics,
    _recommend_torch_compile,
    _api_responses,
    _api_router,
    ApiApplicationDependencies,
    ApiHostDependencies,
    ApiProfileDependencies,
    ApiRequestDependencies,
    ApiSettingsDependencies,
    ApiTorchCompileDependencies,
    ApiTranslationDependencies,
    ApiWildcardAutocompleteDependencies,
    _publish_application_dependencies,
    _late_attr,
    _late,
    _late_value,
    _read,
    ApiContractError,
    _run_file_io,
    json_boolean,
    json_integer,
    json_object,
    json_string,
    json_uuid_string,
    parse_json_object,
    attach_request_id_header,
    correlate_response,
    create_request_id,
    error_payload,
    _ROUTE_REGISTRATION_MARKER,
    _build_route_definitions,
    _build_route_signature,
    _register_route_definitions,
    _api_autocomplete_routes,
    _api_long_text_routes,
    _api_settings_routes,
    _api_translation_routes,
    _api_wildcard_routes,
    AUTOCOMPLETE_CSV,
    _canonical_autocomplete_status,
    _canonical_available_autocomplete_sources,
    _canonical_resolve_autocomplete_source_path,
    _canonical_search_autocomplete,
    _canonical_classify_prompt_text,
    _build_aio_torch_compile_route_handler,
    _build_lora_read_route_group,
    _build_profile_list_route_group,
    _build_profile_route_group,
    _build_settings_route_group,
    _build_translation_route_handler,
    _build_translation_route_runtime,
    _build_wildcard_autocomplete_route_group,
    _get_runtime,
    load_long_text_settings,
    save_long_text_settings,
    save_setting,
    public_settings,
    resolve_autocomplete_limit,
    resolve_autocomplete_source,
    resolve_prompt_translation_settings,
    PromptTranslationError,
    translate_prompt_markers,
    list_wildcards,
    resolve_wildcard_roots,
    TranslationBusyError,
    TranslationCancelledError,
    TranslationTimeoutError,
    FILE_IO_MAX_IN_FLIGHT,
    _FILE_IO_LIMITERS,
    _FILE_IO_LIMITERS_LOCK,
    _file_io_limiter,
    _release_file_io_slot,
)


def _publish_routes(target):
    globals()["routes"] = target


_APPLICATION = _compose_api_application(
    logger=_LOGGER,
    publish_routes=_publish_routes,
)
_APPLICATION_DEPENDENCIES = _APPLICATION.dependencies
_PROMPT_TRANSLATION_WORKER = _APPLICATION.translation_executor
_ROUTE_DEFINITIONS = _APPLICATION.route_definitions
_ROUTE_SIGNATURE = _APPLICATION.route_signature
register_routes = _APPLICATION.register_routes

_COMPATIBILITY = _APPLICATION.compatibility
_COMPATIBILITY_PARTS = _COMPATIBILITY.parts
server = _COMPATIBILITY_PARTS.server
web = _COMPATIBILITY_PARTS.web
routes = _COMPATIBILITY.initial_routes
_get_prompt_routes = _COMPATIBILITY_PARTS.get_prompt_routes
_translate_prompt_sync = _COMPATIBILITY_PARTS.translate_prompt_sync
_translate_prompt_for_route = _COMPATIBILITY_PARTS.translate_prompt_for_route
_prompt_translation_error_response = (
    _COMPATIBILITY_PARTS.prompt_translation_error_response
)
_error_response = _COMPATIBILITY_PARTS.error_response
_contract_error_response = _COMPATIBILITY_PARTS.contract_error_response
_request_correlated = _COMPATIBILITY_PARTS.request_correlated
_resolve_lora_preview_path = _COMPATIBILITY_PARTS.resolve_lora_preview_path
_SAFE_PROFILE_VALIDATION_MESSAGES = (
    _COMPATIBILITY_PARTS.safe_profile_validation_messages
)
_profile_error_response = _COMPATIBILITY_PARTS.profile_error_response
_get_settings_payload_sync = _COMPATIBILITY_PARTS.get_settings_payload_sync
_save_setting_payload_sync = _COMPATIBILITY_PARTS.save_setting_payload_sync
_get_long_text_settings_payload_sync = (
    _COMPATIBILITY_PARTS.get_long_text_settings_payload_sync
)
_save_long_text_settings_payload_sync = (
    _COMPATIBILITY_PARTS.save_long_text_settings_payload_sync
)
_wildcards_payload_sync = _COMPATIBILITY_PARTS.wildcards_payload_sync
_autocomplete_status_payload_sync = (
    _COMPATIBILITY_PARTS.autocomplete_status_payload_sync
)
_public_autocomplete_status = _COMPATIBILITY_PARTS.public_autocomplete_status
_public_autocomplete_payload = _COMPATIBILITY_PARTS.public_autocomplete_payload
_search_autocomplete_payload_sync = (
    _COMPATIBILITY_PARTS.search_autocomplete_payload_sync
)
_classify_prompt_payload_sync = _COMPATIBILITY_PARTS.classify_prompt_payload_sync
_runtime_autocomplete = _COMPATIBILITY_PARTS.runtime_autocomplete
resolve_autocomplete_source_path = (
    _COMPATIBILITY_PARTS.resolve_autocomplete_source_path
)
available_autocomplete_sources = _COMPATIBILITY_PARTS.available_autocomplete_sources
autocomplete_status = _COMPATIBILITY_PARTS.autocomplete_status
search_autocomplete = _COMPATIBILITY_PARTS.search_autocomplete
classify_prompt_text = _COMPATIBILITY_PARTS.classify_prompt_text

if web is not None:
    get_settings_handler = _APPLICATION.handlers.get_settings_handler
    set_setting_handler = _APPLICATION.handlers.set_setting_handler
    get_long_text_settings_handler = _APPLICATION.handlers.get_long_text_settings_handler
    get_wildcards_handler = _APPLICATION.handlers.get_wildcards_handler
    save_long_text_settings_handler = (
        _APPLICATION.handlers.save_long_text_settings_handler
    )
    autocomplete_status_handler = _APPLICATION.handlers.autocomplete_status_handler
    autocomplete_handler = _APPLICATION.handlers.autocomplete_handler
    classify_prompt_handler = _APPLICATION.handlers.classify_prompt_handler
    translate_prompt_handler = _APPLICATION.handlers.translate_prompt_handler
    aio_torch_compile_recommend_handler = (
        _APPLICATION.handlers.aio_torch_compile_recommend_handler
    )
    lora_preview_handler = _APPLICATION.handlers.lora_preview_handler
    loras_handler = _APPLICATION.handlers.loras_handler
    lora_profiles_handler = _APPLICATION.handlers.lora_profiles_handler
    save_lora_profile_handler = _APPLICATION.handlers.save_lora_profile_handler
    load_lora_profile_handler = _APPLICATION.handlers.load_lora_profile_handler
    aio_profiles_handler = _APPLICATION.handlers.aio_profiles_handler
    save_aio_profile_handler = _APPLICATION.handlers.save_aio_profile_handler
    load_aio_profile_handler = _APPLICATION.handlers.load_aio_profile_handler
    delete_aio_profile_handler = _APPLICATION.handlers.delete_aio_profile_handler
    rename_aio_profile_handler = _APPLICATION.handlers.rename_aio_profile_handler
    fix_lora_profile_handler = _APPLICATION.handlers.fix_lora_profile_handler
