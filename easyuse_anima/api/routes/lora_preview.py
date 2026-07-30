from __future__ import annotations

LORA_PREVIEW_EXTENSIONS = (".webp", ".png", ".jpg", ".jpeg")


def build_lora_preview_path_resolver(
    *,
    get_extensions,
    abspath,
    dirname,
    splitext,
    commonpath,
    isfile,
):
    """Build the preview resolver with runtime-resolved path adapters."""

    def _resolve_lora_preview_path(lora_name: str):
        try:
            import folder_paths  # type: ignore
        except Exception:
            return None

        name = str(lora_name or "").strip()
        if not name or name == "None":
            return None
        lora_path = folder_paths.get_full_path("loras", name)
        if not lora_path:
            return None

        lora_abs = abspath(lora_path)
        lora_dir = dirname(lora_abs)
        preview_base = splitext(lora_abs)[0]
        for extension in get_extensions():
            preview_abs = abspath(preview_base + extension)
            try:
                if commonpath((lora_dir, preview_abs)) != lora_dir:
                    continue
            except ValueError:
                continue
            if isfile(preview_abs):
                return preview_abs
        return None

    return _resolve_lora_preview_path


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
