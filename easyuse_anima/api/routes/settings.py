from __future__ import annotations


def build_settings_payloads(*, public_settings, save_setting):
    """Build settings payload helpers with runtime-resolved dependencies."""

    def _get_settings_payload_sync() -> dict:
        return public_settings()

    def _save_setting_payload_sync(key: str, value) -> dict:
        save_setting(key, value)
        return {"status": "ok", **public_settings()}

    return _get_settings_payload_sync, _save_setting_payload_sync


def build_settings_handlers(
    *,
    parse_json_object,
    json_string,
    contract_error_type,
    contract_error_response,
    run_file_io,
    get_settings_payload,
    save_setting_payload,
    unknown_setting_error_type,
    unknown_setting_response,
    json_response,
):
    """Build settings routes without loading settings persistence owners."""

    async def get_settings_handler(request):
        payload = await run_file_io(get_settings_payload)
        return json_response(payload)

    async def set_setting_handler(request):
        try:
            data = await parse_json_object(request)
            key = json_string(data, "key", allow_empty=False)
        except contract_error_type as exc:
            return contract_error_response(exc)
        try:
            payload = await run_file_io(
                save_setting_payload,
                key,
                data.get("value", ""),
            )
        except unknown_setting_error_type:
            return unknown_setting_response()
        return json_response(payload)

    return get_settings_handler, set_setting_handler


__all__ = ("build_settings_handlers",)
