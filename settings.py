from __future__ import annotations

import json
import os
from pathlib import Path

try:
    from .anima_prompt.knowledge import PACKAGE_DATA_DIR
except ImportError:
    from anima_prompt.knowledge import PACKAGE_DATA_DIR

SETTINGS_FILE = PACKAGE_DATA_DIR / "settings.json"

DEFAULT_SETTINGS = {
    "animadex.token": "",
    "animadex.token_file": "",
    "animadex.site": "https://animadex.net",
}


def get_settings() -> dict:
    settings = dict(DEFAULT_SETTINGS)
    if not SETTINGS_FILE.is_file():
        return settings
    try:
        data = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return settings
    if isinstance(data, dict):
        for key in DEFAULT_SETTINGS:
            if key in data:
                settings[key] = str(data[key] or "")
    return settings


def save_setting(key: str, value) -> dict:
    if key not in DEFAULT_SETTINGS:
        raise KeyError(f"Unknown setting: {key}")
    settings = get_settings()
    settings[key] = str(value or "")
    SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    SETTINGS_FILE.write_text(
        json.dumps(settings, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return settings


def public_settings() -> dict:
    settings = get_settings()
    return {
        "animadex.token_configured": bool(settings.get("animadex.token")),
        "animadex.token_file": settings.get("animadex.token_file", ""),
        "animadex.site": settings.get("animadex.site", DEFAULT_SETTINGS["animadex.site"]),
    }


def resolve_animadex_token() -> str:
    settings = get_settings()
    token = settings.get("animadex.token", "").strip()
    if token:
        return token
    token_file = settings.get("animadex.token_file", "").strip()
    if token_file:
        path = Path(token_file)
        if not path.is_file():
            raise RuntimeError(f"[EasyUse Anima] token_file does not exist: {path}")
        return path.read_text(encoding="utf-8").strip()
    return os.environ.get("ANIMADEX_IMPORT_TOKEN", "").strip()


def resolve_animadex_site(site_override: str = "") -> str:
    if str(site_override or "").strip():
        return str(site_override).strip()
    settings = get_settings()
    return settings.get("animadex.site", DEFAULT_SETTINGS["animadex.site"]).strip()
