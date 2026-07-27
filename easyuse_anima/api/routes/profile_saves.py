from __future__ import annotations


def build_profile_save_handlers(
    *,
    parse_json_object,
    json_string,
    json_boolean,
    json_object,
    json_uuid_string,
    json_integer,
    contract_error_type,
    contract_error_response,
    run_file_io,
    save_lora_profile,
    save_aio_profile,
    save_error_types,
    profile_error_response,
    json_response,
):
    """Build profile save routes without loading profile persistence owners."""

    async def save_lora_profile_handler(request):
        try:
            data = await parse_json_object(request)
            name = json_string(data, "name", allow_empty=False)
            overwrite = json_boolean(data, "overwrite")
            if "profile_data" in data:
                json_object(data, "profile_data")
            profile_id = json_uuid_string(
                data,
                "profile_id",
                required=False,
            )
            revision = json_integer(
                data,
                "revision",
                default=None,
                minimum=0,
            )
        except contract_error_type as exc:
            return contract_error_response(exc)
        try:
            payload = await run_file_io(
                save_lora_profile,
                name,
                data,
                overwrite=overwrite,
                profile_id=profile_id,
                revision=revision,
            )
        except save_error_types as exc:
            return profile_error_response(exc)
        return json_response({"status": "ok", "profile": payload})

    async def save_aio_profile_handler(request):
        try:
            data = await parse_json_object(request)
            name = json_string(data, "name", allow_empty=False)
            json_object(data, "settings")
            overwrite = json_boolean(data, "overwrite")
            profile_id = json_uuid_string(
                data,
                "profile_id",
                required=False,
            )
            revision = json_integer(
                data,
                "revision",
                default=None,
                minimum=0,
            )
        except contract_error_type as exc:
            return contract_error_response(exc)
        try:
            payload = await run_file_io(
                save_aio_profile,
                name,
                data,
                overwrite=overwrite,
                profile_id=profile_id,
                revision=revision,
            )
        except save_error_types as exc:
            return profile_error_response(exc)
        return json_response({"status": "ok", "profile": payload})

    return save_lora_profile_handler, save_aio_profile_handler


__all__ = ("build_profile_save_handlers",)
