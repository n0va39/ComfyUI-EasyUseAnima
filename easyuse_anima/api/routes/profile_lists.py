from __future__ import annotations


def build_profile_list_handlers(
    *,
    run_file_io,
    list_lora_profiles,
    list_aio_profiles,
    profile_data_error_type,
    profile_error_response,
    json_response,
):
    """Build read-only profile list routes without loading mutation adapters."""

    async def lora_profiles_handler(request):
        try:
            payload = await run_file_io(list_lora_profiles)
        except profile_data_error_type as exc:
            return profile_error_response(exc)
        return json_response({"profiles": payload})

    async def aio_profiles_handler(request):
        try:
            payload = await run_file_io(list_aio_profiles)
        except profile_data_error_type as exc:
            return profile_error_response(exc)
        return json_response({"status": "ok", "profiles": payload})

    return lora_profiles_handler, aio_profiles_handler


__all__ = ("build_profile_list_handlers",)
