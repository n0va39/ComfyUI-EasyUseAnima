from __future__ import annotations


def build_wildcards_handler(
    *,
    run_file_io,
    wildcards_payload,
    json_response,
):
    """Build the redacted wildcard-list route without loading feature adapters."""

    async def get_wildcards_handler(request):
        return json_response(await run_file_io(wildcards_payload))

    return get_wildcards_handler


__all__ = ("build_wildcards_handler",)
