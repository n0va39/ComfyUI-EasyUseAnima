from __future__ import annotations

try:
    import server
    from aiohttp import web
except ImportError:
    server = None
    web = None

from .settings import public_settings, resolve_autocomplete_source, save_setting
from .animadex_dataset import dataset_paths, dataset_status, download_animadex_dataset
from .autocomplete_dataset import (
    autocomplete_status,
    available_autocomplete_sources,
    classify_prompt_text,
    resolve_autocomplete_source as resolve_autocomplete_source_path,
    search_autocomplete,
)


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

    @server.PromptServer.instance.routes.post("/easyuse_anima/download_animadex")
    async def download_animadex_handler(request):
        data = await request.json()
        try:
            status, report, character_index, artist_index = download_animadex_dataset(
                force_refresh=bool(data.get("force_refresh", False)),
                full_manifest=bool(data.get("full_manifest", False)),
                site_override=str(data.get("site_override") or ""),
            )
            return web.json_response(
                {
                    "status": status,
                    "report": report,
                    "character_index": character_index,
                    "artist_index": artist_index,
                    **dataset_paths(),
                }
            )
        except Exception as exc:
            return web.json_response(
                {"status": "error", "message": str(exc), **dataset_paths()},
                status=500,
            )

    @server.PromptServer.instance.routes.get("/easyuse_anima/animadex_status")
    async def animadex_status_handler(request):
        return web.json_response(dataset_status())

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
            limit = int(request.query.get("limit", "20"))
        except ValueError:
            limit = 20
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
