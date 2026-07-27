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


__all__ = ("build_autocomplete_handlers",)
