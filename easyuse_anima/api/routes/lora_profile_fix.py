from __future__ import annotations


def build_lora_profile_fix_handler(
    *,
    parse_json_object,
    json_object,
    contract_error_type,
    contract_error_response,
    run_file_io,
    fix_lora_profile,
    json_response,
):
    """Build the LoRA profile fix route without loading its domain owner."""

    async def fix_lora_profile_handler(request):
        try:
            data = await parse_json_object(request)
            if "profile_data" in data:
                json_object(data, "profile_data")
        except contract_error_type as exc:
            return contract_error_response(exc)
        payload = await run_file_io(fix_lora_profile, data)
        return json_response({"status": "ok", "profile": payload})

    return fix_lora_profile_handler


__all__ = ("build_lora_profile_fix_handler",)
