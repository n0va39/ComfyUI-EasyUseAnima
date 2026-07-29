from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any

from ..profiles.repository import InvalidProfileDataError
from .application_compatibility import ApiApplicationCompatibilityParts
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
from .errors import ApiContractError
from .requests import (
    json_boolean,
    json_integer,
    json_object,
    json_string,
    json_uuid_string,
    parse_json_object,
)


@dataclass(frozen=True, slots=True)
class ApiRouteHandlers:
    get_settings_handler: Any = None
    set_setting_handler: Any = None
    get_long_text_settings_handler: Any = None
    get_wildcards_handler: Any = None
    save_long_text_settings_handler: Any = None
    autocomplete_status_handler: Any = None
    autocomplete_handler: Any = None
    classify_prompt_handler: Any = None
    translate_prompt_handler: Any = None
    aio_torch_compile_recommend_handler: Any = None
    lora_preview_handler: Any = None
    loras_handler: Any = None
    lora_profiles_handler: Any = None
    save_lora_profile_handler: Any = None
    load_lora_profile_handler: Any = None
    aio_profiles_handler: Any = None
    save_aio_profile_handler: Any = None
    load_aio_profile_handler: Any = None
    delete_aio_profile_handler: Any = None
    rename_aio_profile_handler: Any = None
    fix_lora_profile_handler: Any = None


def _build_settings_handlers(parts, build_settings_route_group):
    return build_settings_route_group(
        request_correlated=parts.request_correlated,
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
                422, "unknown_setting", "Unknown setting"
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


def _build_wildcard_autocomplete_handlers(
    parts,
    build_wildcard_autocomplete_route_group,
):
    return build_wildcard_autocomplete_route_group(
        request_correlated=parts.request_correlated,
        wildcards_dependencies={
            "run_file_io": _late("request", "run_file_io"),
            "wildcards_payload": _late("wildcard_autocomplete", "wildcards_payload"),
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


def _build_translation_handler(parts, build_translation_route_handler):
    return build_translation_route_handler(
        request_correlated=parts.request_correlated,
        translation_dependencies={
            "parse_json_object": parse_json_object,
            "json_string": json_string,
            "contract_error_type": ApiContractError,
            "contract_error_response": _late("request", "contract_error_response"),
            "translate_prompt": lambda text: parts.translate_prompt_for_route(text),
            "get_translation_error_type": _late_value(
                "translation", "prompt_translation_error_type"
            ),
            "translation_error_response": _late(
                "translation", "prompt_translation_error_response"
            ),
            "json_response": _late_attr("host", "web", "json_response"),
        },
    )


def _build_torch_compile_handler(parts, build_aio_torch_compile_route_handler):
    return build_aio_torch_compile_route_handler(
        request_correlated=parts.request_correlated,
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


def _build_lora_read_handlers(parts, build_lora_read_route_group):
    return build_lora_read_route_group(
        request_correlated=parts.request_correlated,
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


def _build_profile_list_handlers(parts, build_profile_list_route_group):
    return build_profile_list_route_group(
        request_correlated=parts.request_correlated,
        profile_list_dependencies={
            "run_file_io": _late("request", "run_file_io"),
            "list_lora_profiles": _late("profiles", "list_lora_profiles"),
            "list_aio_profiles": _late("profiles", "list_aio_profiles"),
            "profile_data_error_type": InvalidProfileDataError,
            "profile_error_response": _late("request", "profile_error_response"),
            "json_response": _late_attr("host", "web", "json_response"),
        },
    )


def _build_profile_handlers(parts, build_profile_route_group):
    return build_profile_route_group(
        request_correlated=parts.request_correlated,
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
            "save_error_types": (FileExistsError, FileNotFoundError, ValueError),
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
            "rename_error_types": (FileExistsError, FileNotFoundError, ValueError),
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


def _build_application_handlers(
    *,
    parts: ApiApplicationCompatibilityParts,
    build_settings_route_group: Any,
    build_wildcard_autocomplete_route_group: Any,
    build_translation_route_handler: Any,
    build_aio_torch_compile_route_handler: Any,
    build_lora_read_route_group: Any,
    build_profile_list_route_group: Any,
    build_profile_route_group: Any,
) -> ApiRouteHandlers:
    if parts.web is None:
        return ApiRouteHandlers()
    settings = _build_settings_handlers(parts, build_settings_route_group)
    wildcard = _build_wildcard_autocomplete_handlers(
        parts, build_wildcard_autocomplete_route_group
    )
    translation = _build_translation_handler(parts, build_translation_route_handler)
    torch_compile = _build_torch_compile_handler(
        parts, build_aio_torch_compile_route_handler
    )
    lora_read = _build_lora_read_handlers(parts, build_lora_read_route_group)
    profile_list = _build_profile_list_handlers(parts, build_profile_list_route_group)
    profile = _build_profile_handlers(parts, build_profile_route_group)
    return ApiRouteHandlers(
        get_settings_handler=settings[0],
        set_setting_handler=settings[1],
        get_long_text_settings_handler=settings[2],
        get_wildcards_handler=wildcard[0],
        save_long_text_settings_handler=settings[3],
        autocomplete_status_handler=wildcard[1],
        autocomplete_handler=wildcard[2],
        classify_prompt_handler=wildcard[3],
        translate_prompt_handler=translation,
        aio_torch_compile_recommend_handler=torch_compile,
        lora_preview_handler=lora_read[0],
        loras_handler=lora_read[1],
        lora_profiles_handler=profile_list[0],
        save_lora_profile_handler=profile[2],
        load_lora_profile_handler=profile[0],
        aio_profiles_handler=profile_list[1],
        save_aio_profile_handler=profile[3],
        load_aio_profile_handler=profile[1],
        delete_aio_profile_handler=profile[4],
        rename_aio_profile_handler=profile[5],
        fix_lora_profile_handler=profile[6],
    )


__all__: tuple[str, ...] = ()
