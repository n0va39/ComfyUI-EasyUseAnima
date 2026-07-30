from __future__ import annotations


def build_aio_profile_mutation_handlers(
    *,
    parse_json_object,
    json_string,
    json_boolean,
    json_uuid_string,
    json_integer,
    contract_error_type,
    contract_error_response,
    run_file_io,
    delete_aio_profile,
    rename_aio_profile,
    delete_error_types,
    rename_error_types,
    profile_error_response,
    json_response,
):
    """Build AiO delete/rename routes without loading profile domain owners."""

    async def delete_aio_profile_handler(request):
        try:
            data = await parse_json_object(request)
            name = json_string(data, "name", allow_empty=False)
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
                delete_aio_profile,
                name,
                profile_id=profile_id,
                revision=revision,
            )
        except delete_error_types as exc:
            return profile_error_response(exc)
        return json_response({"status": "ok", "profile": payload})

    async def rename_aio_profile_handler(request):
        try:
            data = await parse_json_object(request)
            old_name = json_string(data, "old_name", allow_empty=False)
            new_name = json_string(data, "new_name", allow_empty=False)
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
            target_profile_id = json_uuid_string(
                data,
                "target_profile_id",
                required=False,
            )
            target_revision = json_integer(
                data,
                "target_revision",
                default=None,
                minimum=0,
            )
        except contract_error_type as exc:
            return contract_error_response(exc)
        try:
            payload = await run_file_io(
                rename_aio_profile,
                old_name,
                new_name,
                overwrite=overwrite,
                profile_id=profile_id,
                revision=revision,
                target_profile_id=target_profile_id,
                target_revision=target_revision,
            )
        except rename_error_types as exc:
            return profile_error_response(exc)
        return json_response({"status": "ok", "profile": payload})

    return delete_aio_profile_handler, rename_aio_profile_handler


__all__ = ("build_aio_profile_mutation_handlers",)
