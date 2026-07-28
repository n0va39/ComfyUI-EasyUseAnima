from __future__ import annotations

PROMPT_TRANSLATION_ROUTE_TIMEOUT_SECONDS = 15.0


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
    error_response,
):
    """Build the translation runtime without module-import side effects."""

    worker = executor_type(
        busy_error_type=busy_error_type,
        cancelled_error_type=cancelled_error_type,
        timeout_error_type=timeout_error_type,
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

    def _prompt_translation_error_response(exc):
        return error_response(
            exc.status,
            exc.code,
            exc.message,
        )

    return (
        worker,
        _translate_prompt_sync,
        _translate_prompt_for_route,
        _prompt_translation_error_response,
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
