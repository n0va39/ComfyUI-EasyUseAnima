from __future__ import annotations


def build_aio_torch_compile_recommend_handler(
    *,
    parse_json_object,
    json_object,
    json_integer,
    contract_error_type,
    contract_error_response,
    collect_diagnostics,
    recommend_torch_compile,
    json_response,
):
    """Build the read-only recommendation route without registering adapters."""

    async def aio_torch_compile_recommend_handler(request):
        try:
            data = await parse_json_object(request)
            generation_settings = (
                json_object(data, "generation_settings")
                if "generation_settings" in data
                else {}
            )
            resolution = (
                json_object(data, "resolution") if "resolution" in data else {}
            )
            width = json_integer(
                resolution,
                "width",
                default=None,
                minimum=1,
                maximum=16384,
            )
            height = json_integer(
                resolution,
                "height",
                default=None,
                minimum=1,
                maximum=16384,
            )
            batch_size = json_integer(
                data,
                "batch_size",
                default=1,
                minimum=1,
                maximum=4096,
            )
        except contract_error_type as exc:
            return contract_error_response(exc)
        return json_response(
            recommend_torch_compile(
                collect_diagnostics(),
                generation_settings,
                {"width": width, "height": height},
                batch_size if batch_size is not None else 1,
            )
        )

    return aio_torch_compile_recommend_handler


__all__ = ("build_aio_torch_compile_recommend_handler",)
