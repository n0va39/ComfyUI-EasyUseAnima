from __future__ import annotations


def build_wildcards_payload(
    *,
    public_settings,
    resolve_wildcard_roots,
    list_wildcards,
):
    """Build the redacted wildcard payload with runtime-resolved owners."""

    def _wildcards_payload_sync() -> dict:
        settings = public_settings()
        extra_paths = settings.get("wildcard.extra_paths", "")
        roots = resolve_wildcard_roots(extra_paths)
        sources = [
            {
                "id": f"wildcard:{index}",
                "label": f"Wildcard source {index}",
                "exists": root.is_dir(),
            }
            for index, root in enumerate(roots, start=1)
        ]
        return {
            "status": "ok",
            "items": list_wildcards(roots=roots),
            # Preserve the legacy list-of-strings type without publishing paths.
            "roots": [source["id"] for source in sources],
            "sources": sources,
        }

    return _wildcards_payload_sync


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
