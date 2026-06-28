from __future__ import annotations

import json
import os
import re
from pathlib import Path

try:
    import server
    from aiohttp import web
except ImportError:
    server = None
    web = None

from .settings import (
    load_long_text_settings,
    public_settings,
    resolve_autocomplete_limit,
    resolve_autocomplete_source,
    save_setting,
    save_long_text_settings,
)
from .autocomplete_dataset import (
    autocomplete_status,
    available_autocomplete_sources,
    classify_prompt_text,
    resolve_autocomplete_source as resolve_autocomplete_source_path,
    search_autocomplete,
)
try:
    from .storage import USER_DATA_DIR
except ImportError:
    from storage import USER_DATA_DIR


LORA_PREVIEW_EXTENSIONS = (".webp", ".png", ".jpg", ".jpeg")
LORA_PROFILE_DIR = USER_DATA_DIR / "profiles"
MAX_LORA_PROFILES = 16
INVALID_PROFILE_NAME_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]+')


def _sanitize_lora_profile_name(name: str) -> str:
    safe_name = INVALID_PROFILE_NAME_CHARS.sub("_", str(name or "")).strip(" ._")
    if not safe_name:
        raise ValueError("Profile name is required")
    return safe_name[:80]


def _lora_profile_path(name: str, profile_dir: Path | None = None) -> Path:
    safe_name = _sanitize_lora_profile_name(name)
    root = (profile_dir or LORA_PROFILE_DIR).resolve()
    path = (root / f"{safe_name}.json").resolve()
    if os.path.commonpath((str(root), str(path))) != str(root):
        raise ValueError("Invalid profile path")
    return path


def _as_lora_profile_count(value) -> int:
    try:
        count = int(value)
    except (TypeError, ValueError):
        count = 1
    return max(1, min(MAX_LORA_PROFILES, count))


def _as_lora_profile_index(value, count: int) -> int:
    try:
        index = int(value)
    except (TypeError, ValueError):
        index = 1
    index = max(1, index)
    return ((index - 1) % count) + 1


def _normalize_lora_profile_data(value) -> dict:
    if isinstance(value, str):
        try:
            value = json.loads(value or "{}")
        except (TypeError, ValueError):
            value = {}
    if not isinstance(value, dict):
        return {}
    normalized: dict[str, dict] = {}
    for key, profile in value.items():
        if not isinstance(profile, dict):
            continue
        style_prompt = str(profile.get("style_prompt") or "")
        loras = profile.get("loras")
        if not isinstance(loras, list):
            loras = []
        normalized[str(key)] = {
            "style_prompt": style_prompt,
            "loras": [item for item in loras if isinstance(item, dict)],
        }
    return normalized


def _normalize_lora_profile_payload(data: dict) -> dict:
    count = _as_lora_profile_count(data.get("profile_count", 1))
    return {
        "version": 1,
        "profile_count": count,
        "profile_index": _as_lora_profile_index(data.get("profile_index", 1), count),
        "profile_data": _normalize_lora_profile_data(data.get("profile_data", {})),
    }


def _list_lora_profiles() -> list[dict]:
    if not LORA_PROFILE_DIR.is_dir():
        return []
    profiles = []
    for path in sorted(LORA_PROFILE_DIR.glob("*.json"), key=lambda item: item.stem.lower()):
        if path.name == ".gitignore":
            continue
        profiles.append(
            {
                "name": path.stem,
                "modified": int(path.stat().st_mtime),
            }
        )
    return profiles


def _clear_folder_paths_cache(folder_paths, folder_name: str):
    cache = getattr(folder_paths, "filename_list_cache", None)
    if isinstance(cache, dict):
        cache.pop(folder_name, None)
    cache_helper = getattr(folder_paths, "cache_helper", None)
    if cache_helper is not None and not getattr(cache_helper, "active", False):
        clear = getattr(cache_helper, "clear", None)
        if callable(clear):
            clear()


def _list_loras() -> list[str]:
    try:
        import folder_paths  # type: ignore
    except Exception:
        return []

    _clear_folder_paths_cache(folder_paths, "loras")
    try:
        names = folder_paths.get_filename_list("loras")
    except Exception:
        names = []

    loras = []
    seen = set()
    for name in names:
        text = str(name or "").strip()
        if not text or text == "None":
            continue
        key = text.replace("\\", "/").casefold()
        if key in seen:
            continue
        seen.add(key)
        loras.append(text)
    return loras


def _save_lora_profile(name: str, data: dict) -> dict:
    safe_name = _sanitize_lora_profile_name(name)
    payload = _normalize_lora_profile_payload(data)
    payload["name"] = safe_name
    LORA_PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    path = _lora_profile_path(safe_name)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload


def _load_lora_profile(name: str) -> dict:
    path = _lora_profile_path(name)
    if not path.is_file():
        raise FileNotFoundError("Profile not found")
    data = json.loads(path.read_text(encoding="utf-8") or "{}")
    if not isinstance(data, dict):
        data = {}
    payload = _normalize_lora_profile_payload(data)
    payload["name"] = path.stem
    return payload


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
    lora_dir = os.path.dirname(lora_abs)
    preview_base = os.path.splitext(lora_abs)[0]
    for extension in LORA_PREVIEW_EXTENSIONS:
        preview_abs = os.path.abspath(preview_base + extension)
        try:
            if os.path.commonpath((lora_dir, preview_abs)) != lora_dir:
                continue
        except ValueError:
            continue
        if os.path.isfile(preview_abs):
            return preview_abs
    return None


def _get_prompt_routes():
    if server is None:
        return None
    prompt_server = getattr(getattr(server, "PromptServer", None), "instance", None)
    return getattr(prompt_server, "routes", None)


routes = _get_prompt_routes()


if web is not None and routes is not None:

    @routes.get("/easyuse_anima/settings")
    async def get_settings_handler(request):
        return web.json_response(public_settings())

    @routes.post("/easyuse_anima/set_setting")
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

    @routes.get("/easyuse_anima/long_text_settings")
    async def get_long_text_settings_handler(request):
        return web.json_response(
            {
                "status": "ok",
                "values": load_long_text_settings(),
                "settings": public_settings(),
            }
        )

    @routes.post("/easyuse_anima/long_text_settings/save")
    async def save_long_text_settings_handler(request):
        data = await request.json()
        values = data.get("values", data)
        if not isinstance(values, dict):
            return web.json_response(
                {"status": "error", "message": "Long text values must be an object"},
                status=400,
            )
        saved = save_long_text_settings(values)
        return web.json_response(
            {
                "status": "ok",
                "values": saved,
                "settings": public_settings(),
            }
        )

    @routes.get("/easyuse_anima/autocomplete_status")
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

    @routes.get("/easyuse_anima/autocomplete")
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

    @routes.post("/easyuse_anima/classify_prompt")
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

    @routes.get("/easyuse_anima/lora_preview")
    async def lora_preview_handler(request):
        preview_path = _resolve_lora_preview_path(request.query.get("name", ""))
        if not preview_path:
            return web.Response(status=404)
        return web.FileResponse(
            preview_path,
            headers={"Content-Disposition": f'filename="{os.path.basename(preview_path)}"'},
        )

    @routes.get("/easyuse_anima/loras")
    async def loras_handler(request):
        return web.json_response({"loras": _list_loras()})

    @routes.get("/easyuse_anima/lora_profiles")
    async def lora_profiles_handler(request):
        return web.json_response({"profiles": _list_lora_profiles()})

    @routes.post("/easyuse_anima/lora_profiles/save")
    async def save_lora_profile_handler(request):
        data = await request.json()
        try:
            payload = _save_lora_profile(str(data.get("name") or ""), data)
        except ValueError as exc:
            return web.json_response({"status": "error", "message": str(exc)}, status=400)
        return web.json_response({"status": "ok", "profile": payload})

    @routes.get("/easyuse_anima/lora_profiles/load")
    async def load_lora_profile_handler(request):
        try:
            payload = _load_lora_profile(request.query.get("name", ""))
        except ValueError as exc:
            return web.json_response({"status": "error", "message": str(exc)}, status=400)
        except FileNotFoundError as exc:
            return web.json_response({"status": "error", "message": str(exc)}, status=404)
        return web.json_response({"status": "ok", "profile": payload})
