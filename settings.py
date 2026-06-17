from __future__ import annotations

import json
import os

try:
    from .anima_prompt.knowledge import LEGACY_PACKAGE_DATA_DIR, PACKAGE_DATA_DIR
except ImportError:
    from anima_prompt.knowledge import LEGACY_PACKAGE_DATA_DIR, PACKAGE_DATA_DIR

SETTINGS_FILE = PACKAGE_DATA_DIR / "settings.json"
LEGACY_SETTINGS_FILE = LEGACY_PACKAGE_DATA_DIR / "settings.json"

DEFAULT_SETTINGS = {
    "animadex.token": "",
    "animadex.site": "https://animadex.net",
    "prompt.metadata_filter_words": "",
    "autocomplete.source": "kr_modified",
}


def get_settings() -> dict:
    settings = dict(DEFAULT_SETTINGS)
    source = SETTINGS_FILE if SETTINGS_FILE.is_file() else LEGACY_SETTINGS_FILE
    if not source.is_file():
        return settings
    try:
        data = json.loads(source.read_text(encoding="utf-8"))
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
        "animadex.site": settings.get("animadex.site", DEFAULT_SETTINGS["animadex.site"]),
        "prompt.metadata_filter_words": settings.get("prompt.metadata_filter_words", ""),
        "autocomplete.source": settings.get(
            "autocomplete.source",
            DEFAULT_SETTINGS["autocomplete.source"],
        ),
    }


def resolve_animadex_token() -> str:
    settings = get_settings()
    token = settings.get("animadex.token", "").strip()
    if token:
        return token
    return os.environ.get("ANIMADEX_IMPORT_TOKEN", "").strip()


def resolve_animadex_site(site_override: str = "") -> str:
    if str(site_override or "").strip():
        return str(site_override).strip()
    settings = get_settings()
    return settings.get("animadex.site", DEFAULT_SETTINGS["animadex.site"]).strip()


def resolve_metadata_filter_words() -> str:
    settings = get_settings()
    return settings.get(
        "prompt.metadata_filter_words",
        DEFAULT_SETTINGS["prompt.metadata_filter_words"],
    )


def resolve_autocomplete_source() -> str:
    settings = get_settings()
    return settings.get("autocomplete.source", DEFAULT_SETTINGS["autocomplete.source"])
