from __future__ import annotations


def build_profile_load_handlers(
    *,
    run_file_io,
    load_lora_profile,
    load_aio_profile,
    lora_load_error_types,
    aio_load_error_types,
    profile_error_response,
    json_response,
):
    """Build read-only profile load routes without loading mutation adapters."""

    async def load_lora_profile_handler(request):
        try:
            payload = await run_file_io(
                load_lora_profile,
                request.query.get("name", ""),
            )
        except lora_load_error_types as exc:
            return profile_error_response(exc)
        return json_response({"status": "ok", "profile": payload})

    async def load_aio_profile_handler(request):
        try:
            payload = await run_file_io(
                load_aio_profile,
                request.query.get("name", ""),
            )
        except aio_load_error_types as exc:
            return profile_error_response(exc)
        return json_response({"status": "ok", "profile": payload})

    return load_lora_profile_handler, load_aio_profile_handler


__all__ = ("build_profile_load_handlers",)
