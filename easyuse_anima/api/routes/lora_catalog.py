from __future__ import annotations


def build_loras_handler(
    *,
    run_file_io,
    list_loras,
    json_response,
):
    """Build the LoRA catalog route without loading profile adapters."""

    async def loras_handler(request):
        return json_response({"loras": await run_file_io(list_loras)})

    return loras_handler


__all__ = ("build_loras_handler",)
