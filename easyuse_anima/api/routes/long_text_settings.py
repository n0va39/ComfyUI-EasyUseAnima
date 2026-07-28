from __future__ import annotations


def build_long_text_settings_payloads(
    *,
    load_long_text_settings,
    save_long_text_settings,
    public_settings,
):
    """Build long-text payload helpers with runtime-resolved dependencies."""

    def _get_long_text_settings_payload_sync() -> dict:
        return {
            "status": "ok",
            "values": load_long_text_settings(),
            "settings": public_settings(),
        }

    def _save_long_text_settings_payload_sync(values: dict) -> dict:
        return {
            "status": "ok",
            "values": save_long_text_settings(values),
            "settings": public_settings(),
        }

    return (
        _get_long_text_settings_payload_sync,
        _save_long_text_settings_payload_sync,
    )


def build_long_text_settings_handlers(
    *,
    parse_json_object,
    json_object,
    contract_error_type,
    contract_error_response,
    run_file_io,
    get_long_text_settings_payload,
    save_long_text_settings_payload,
    json_response,
):
    """Build long-text settings routes without loading persistence adapters."""

    async def get_long_text_settings_handler(request):
        return json_response(
            await run_file_io(get_long_text_settings_payload)
        )

    async def save_long_text_settings_handler(request):
        try:
            data = await parse_json_object(request)
            values = json_object(data, "values") if "values" in data else data
        except contract_error_type as exc:
            return contract_error_response(exc)
        return json_response(
            await run_file_io(save_long_text_settings_payload, values)
        )

    return get_long_text_settings_handler, save_long_text_settings_handler


__all__ = ("build_long_text_settings_handlers",)
