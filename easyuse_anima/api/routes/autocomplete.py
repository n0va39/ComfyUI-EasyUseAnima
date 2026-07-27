from __future__ import annotations


def build_autocomplete_handlers(
    *,
    run_file_io,
    autocomplete_status_payload,
    search_autocomplete_payload,
    json_response,
):
    """Build the read-only autocomplete routes without loading dataset adapters."""

    async def autocomplete_status_handler(request):
        return json_response(
            await run_file_io(autocomplete_status_payload)
        )

    async def autocomplete_handler(request):
        query = request.query.get("q", "")
        category = request.query.get("category", "")
        category_filter = {
            "artist": "artist",
            "artist_or_general": "artist,general",
        }.get(category)
        return json_response(
            await run_file_io(
                search_autocomplete_payload,
                query,
                request.query.get("limit"),
                category_filter,
            )
        )

    return autocomplete_status_handler, autocomplete_handler


def build_classify_prompt_handler(
    *,
    parse_json_object,
    json_string,
    json_integer,
    contract_error_type,
    contract_error_response,
    run_file_io,
    classify_prompt_payload,
    json_response,
):
    """Build the prompt-classification route without loading feature adapters."""

    async def classify_prompt_handler(request):
        try:
            data = await parse_json_object(request)
            text = json_string(data, "text")
            limit = json_integer(
                data,
                "limit",
                default=240,
                minimum=1,
                maximum=500,
            )
        except contract_error_type as exc:
            return contract_error_response(exc)
        return json_response(
            await run_file_io(classify_prompt_payload, text, limit)
        )

    return classify_prompt_handler


__all__ = (
    "build_autocomplete_handlers",
    "build_classify_prompt_handler",
)
