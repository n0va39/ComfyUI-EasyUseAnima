from __future__ import annotations

import os

try:
    import server
    from aiohttp import web
except ImportError:
    server = None
    web = None

from .settings import (
    public_settings,
    resolve_autocomplete_limit,
    resolve_autocomplete_source,
    save_setting,
)
from .autocomplete_dataset import (
    autocomplete_status,
    available_autocomplete_sources,
    classify_prompt_text,
    resolve_autocomplete_source as resolve_autocomplete_source_path,
    search_autocomplete,
)


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

    lora_abs = os.path.abspath(lora_path)
    preview_path = os.path.splitext(lora_abs)[0] + ".webp"
    preview_abs = os.path.abspath(preview_path)
    lora_dir = os.path.dirname(lora_abs)
    try:
        if os.path.commonpath((lora_dir, preview_abs)) != lora_dir:
            return None
    except ValueError:
        return None
    if not os.path.isfile(preview_abs):
        return None
    return preview_abs


if server is not None and web is not None:

    @server.PromptServer.instance.routes.get("/easyuse_anima/settings")
    async def get_settings_handler(request):
        return web.json_response(public_settings())

    @server.PromptServer.instance.routes.post("/easyuse_anima/set_setting")
    async def set_setting_handler(request):
        data = await request.json()
        key = data.get("key")
        if key is None:
            return web.json_response(
                {"status": "error", "message": "Setting key not provided"},
                status=400,
            )
        try:
            save_setting(str(key), data.get("value", ""))
        except KeyError as exc:
            return web.json_response(
                {"status": "error", "message": str(exc)},
                status=400,
            )
        return web.json_response({"status": "ok", **public_settings()})

    @server.PromptServer.instance.routes.get("/easyuse_anima/autocomplete_status")
    async def autocomplete_status_handler(request):
        selected_source = resolve_autocomplete_source()
        source_key, path = resolve_autocomplete_source_path(selected_source)
        return web.json_response(
            {
                **autocomplete_status(path),
                "source": source_key,
                "sources": available_autocomplete_sources(source_key),
            }
        )

    @server.PromptServer.instance.routes.get("/easyuse_anima/autocomplete")
    async def autocomplete_handler(request):
        query = request.query.get("q", "")
        category = request.query.get("category", "")
        category_filter = {
            "artist": "artist",
            "artist_or_general": "artist,general",
        }.get(category)
        try:
            limit = int(request.query.get("limit", resolve_autocomplete_limit()))
        except ValueError:
            limit = resolve_autocomplete_limit()
        _, path = resolve_autocomplete_source_path(resolve_autocomplete_source())
        return web.json_response(
            search_autocomplete(
                query,
                limit=limit,
                path=path,
                category=category_filter,
            )
        )

    @server.PromptServer.instance.routes.post("/easyuse_anima/classify_prompt")
    async def classify_prompt_handler(request):
        data = await request.json()
        try:
            limit = int(data.get("limit", 240))
        except (TypeError, ValueError):
            limit = 240
        _, path = resolve_autocomplete_source_path(resolve_autocomplete_source())
        return web.json_response(
            classify_prompt_text(str(data.get("text") or ""), limit=limit, path=path)
        )

    @server.PromptServer.instance.routes.get("/easyuse_anima/lora_preview")
    async def lora_preview_handler(request):
        preview_path = _resolve_lora_preview_path(request.query.get("name", ""))
        if not preview_path:
            return web.Response(status=404)
        return web.FileResponse(
            preview_path,
            headers={"Content-Disposition": f'filename="{os.path.basename(preview_path)}"'},
        )
