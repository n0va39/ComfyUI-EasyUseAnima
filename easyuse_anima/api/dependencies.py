from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

DependencyCallable = Callable[..., Any]


@dataclass(slots=True)
class ApiHostDependencies:
    server: Any
    web: Any
    get_prompt_routes: DependencyCallable
    route_definitions: tuple[Any, ...]
    route_signature: tuple[tuple[str, str], ...]
    register_route_definitions: DependencyCallable


@dataclass(slots=True)
class ApiRequestDependencies:
    create_request_id: DependencyCallable
    run_file_io: DependencyCallable
    error_response: DependencyCallable
    contract_error_response: DependencyCallable
    profile_error_response: DependencyCallable
    profile_mutation_error_type: type[Exception]
    safe_profile_validation_messages: frozenset[str]


@dataclass(slots=True)
class ApiSettingsDependencies:
    public_settings: DependencyCallable
    save_setting: DependencyCallable
    load_long_text_settings: DependencyCallable
    save_long_text_settings: DependencyCallable
    get_settings_payload: DependencyCallable
    save_setting_payload: DependencyCallable
    get_long_text_settings_payload: DependencyCallable
    save_long_text_settings_payload: DependencyCallable


@dataclass(slots=True)
class ApiWildcardAutocompleteDependencies:
    get_runtime: DependencyCallable
    resolve_wildcard_roots: DependencyCallable
    list_wildcards: DependencyCallable
    resolve_autocomplete_source: DependencyCallable
    resolve_autocomplete_source_path: DependencyCallable
    resolve_autocomplete_limit: DependencyCallable
    available_autocomplete_sources: DependencyCallable
    autocomplete_status: DependencyCallable
    search_autocomplete: DependencyCallable
    classify_prompt_text: DependencyCallable
    wildcards_payload: DependencyCallable
    autocomplete_status_payload: DependencyCallable
    search_autocomplete_payload: DependencyCallable
    classify_prompt_payload: DependencyCallable
    public_autocomplete_status: DependencyCallable
    public_autocomplete_payload: DependencyCallable


@dataclass(slots=True)
class ApiProfileDependencies:
    list_loras: DependencyCallable
    list_lora_profiles: DependencyCallable
    list_aio_profiles: DependencyCallable
    load_lora_profile: DependencyCallable
    load_aio_profile: DependencyCallable
    save_lora_profile: DependencyCallable
    save_aio_profile: DependencyCallable
    delete_aio_profile: DependencyCallable
    rename_aio_profile: DependencyCallable
    fix_lora_profile_payload: DependencyCallable
    resolve_lora_preview_path: DependencyCallable


@dataclass(slots=True)
class ApiTranslationDependencies:
    translate_prompt_markers: DependencyCallable
    resolve_prompt_translation_settings: DependencyCallable
    route_timeout_seconds: float
    prompt_translation_error_type: type[Exception]
    prompt_translation_error_response: DependencyCallable


@dataclass(slots=True)
class ApiTorchCompileDependencies:
    collect_diagnostics: DependencyCallable
    recommend_torch_compile: DependencyCallable


@dataclass(slots=True)
class ApiApplicationDependencies:
    host: ApiHostDependencies
    request: ApiRequestDependencies
    settings: ApiSettingsDependencies
    wildcard_autocomplete: ApiWildcardAutocompleteDependencies
    profiles: ApiProfileDependencies
    translation: ApiTranslationDependencies
    torch_compile: ApiTorchCompileDependencies


_APPLICATION_DEPENDENCIES: ApiApplicationDependencies | None = None


def _publish_application_dependencies(
    dependencies: ApiApplicationDependencies,
) -> ApiApplicationDependencies:
    global _APPLICATION_DEPENDENCIES

    current = _APPLICATION_DEPENDENCIES
    if current is None:
        _APPLICATION_DEPENDENCIES = dependencies
        return dependencies
    if current is dependencies:
        return current
    raise RuntimeError("[EasyUseAnima] API application dependencies already installed.")


def _get_application_dependencies() -> ApiApplicationDependencies:
    current = _APPLICATION_DEPENDENCIES
    if current is None:
        raise RuntimeError("[EasyUseAnima] API application dependencies are not installed.")
    return current


def _read_application_dependency(family: str, name: str) -> Any:
    return getattr(getattr(_get_application_dependencies(), family), name)


def _late_application_dependency(family: str, name: str) -> DependencyCallable:
    def invoke(*args: Any, **kwargs: Any) -> Any:
        return _read_application_dependency(family, name)(*args, **kwargs)

    return invoke


def _late_application_value(family: str, name: str) -> DependencyCallable:
    def read() -> Any:
        return _read_application_dependency(family, name)

    return read


def _late_application_attribute(
    family: str,
    name: str,
    attribute: str,
) -> DependencyCallable:
    def invoke(*args: Any, **kwargs: Any) -> Any:
        owner = _read_application_dependency(family, name)
        return getattr(owner, attribute)(*args, **kwargs)

    return invoke


__all__: tuple[str, ...] = ()
