from __future__ import annotations

from collections.abc import Mapping

PROMPT_TRANSLATION_ROUTE_TIMEOUT_SECONDS = 15.0

_TRANSLATION_HTTP_MAPPINGS: tuple[tuple[str, int, str, str], ...] = (
    (
        "marker_count",
        413,
        "translation_marker_count_exceeded",
        "Prompt translation failed.",
    ),
    (
        "marker_size",
        413,
        "translation_marker_too_long",
        "Prompt translation failed.",
    ),
    (
        "total_size",
        413,
        "translation_marker_characters_exceeded",
        "Prompt translation failed.",
    ),
    ("limit", 413, "translation_error", "Prompt translation failed."),
    (
        "provider_unavailable",
        503,
        "translation_provider_unavailable",
        "The selected translation provider is unavailable.",
    ),
    (
        "timeout",
        504,
        "translation_timeout",
        "The translation provider timed out.",
    ),
    (
        "cancelled",
        499,
        "translation_cancelled",
        "The translation request was cancelled.",
    ),
    (
        "busy",
        503,
        "translation_busy",
        "A prompt translation request is already in progress.",
    ),
    (
        "upstream",
        502,
        "translation_upstream_error",
        "The translation provider request failed.",
    ),
    ("base", 500, "translation_error", "Prompt translation failed."),
)


def _build_translation_error_response(
    *,
    error_types: Mapping[str, type[Exception]],
    error_response,
):
    error_mappings = tuple(
        (error_types[key], status, code, default_message)
        for key, status, code, default_message in _TRANSLATION_HTTP_MAPPINGS
    )

    def _prompt_translation_error_response(exc: Exception):
        for error_type, status, code, default_message in error_mappings:
            if isinstance(exc, error_type):
                return error_response(status, code, str(exc) or default_message)
        raise exc

    return _prompt_translation_error_response


def build_translation_runtime(
    *,
    executor_type,
    busy_error_type,
    cancelled_error_type,
    timeout_error_type,
    translate_prompt_markers,
    resolve_prompt_translation_settings,
    get_worker,
    get_translate_prompt_sync,
    get_timeout_seconds,
    translation_error_types: Mapping[str, type[Exception]],
    error_response,
):
    """Build the translation runtime without module-import side effects."""

    worker = executor_type(
        busy_error_type=busy_error_type,
        cancelled_error_type=cancelled_error_type,
        timeout_error_type=timeout_error_type,
    )
    translation_error_response = _build_translation_error_response(
        error_types=translation_error_types,
        error_response=error_response,
    )

    def _translate_prompt_sync(text: str) -> str:
        return translate_prompt_markers(
            text,
            resolve_prompt_translation_settings(),
        )

    async def _translate_prompt_for_route(text: str) -> str:
        return await get_worker().execute(
            get_translate_prompt_sync(),
            text,
            timeout_seconds=get_timeout_seconds(),
        )

    return (
        worker,
        _translate_prompt_sync,
        _translate_prompt_for_route,
        translation_error_response,
    )


def build_translate_prompt_handler(
    *,
    parse_json_object,
    json_string,
    contract_error_type,
    contract_error_response,
    translate_prompt,
    translation_error_type,
    translation_error_response,
    json_response,
):
    """Build the translation route without importing or registering runtime adapters."""

    async def translate_prompt_handler(request):
        try:
            data = await parse_json_object(request)
            text = json_string(data, "text")
        except contract_error_type as exc:
            return contract_error_response(exc)
        try:
            translated = await translate_prompt(text)
        except translation_error_type as exc:
            return translation_error_response(exc)
        return json_response({"status": "ok", "text": translated})

    return translate_prompt_handler


__all__ = ("build_translate_prompt_handler",)
