from __future__ import annotations


def build_lora_preview_handler(
    *,
    run_file_io,
    resolve_lora_preview_path,
    empty_response,
    file_response,
    basename,
):
    """Build the LoRA preview route without loading path adapters."""

    async def lora_preview_handler(request):
        preview_path = await run_file_io(
            resolve_lora_preview_path,
            request.query.get("name", ""),
        )
        if not preview_path:
            return empty_response(status=404)
        return file_response(
            preview_path,
            headers={"Content-Disposition": f'filename="{basename(preview_path)}"'},
        )

    return lora_preview_handler


__all__ = ("build_lora_preview_handler",)
