from __future__ import annotations


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
