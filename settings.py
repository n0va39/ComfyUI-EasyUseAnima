from __future__ import annotations

import json

try:
    from .anima_prompt.knowledge import PACKAGE_DATA_DIR
except ImportError:
    from anima_prompt.knowledge import PACKAGE_DATA_DIR

SETTINGS_FILE = PACKAGE_DATA_DIR / "settings.json"

DEFAULT_SETTINGS = {
    "prompt.metadata_filter_words": "",
    "autocomplete.source": "kr_modified",
    "prompt_studio.typo_indicator": "true",
    "prompt_studio.colors": "",
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
        "prompt.metadata_filter_words": settings.get("prompt.metadata_filter_words", ""),
        "autocomplete.source": settings.get(
            "autocomplete.source",
            DEFAULT_SETTINGS["autocomplete.source"],
        ),
        "prompt_studio.typo_indicator": settings.get(
            "prompt_studio.typo_indicator",
            DEFAULT_SETTINGS["prompt_studio.typo_indicator"],
        ),
        "prompt_studio.colors": settings.get(
            "prompt_studio.colors",
            DEFAULT_SETTINGS["prompt_studio.colors"],
        ),
    }


def resolve_metadata_filter_words() -> str:
    settings = get_settings()
    return settings.get(
        "prompt.metadata_filter_words",
        DEFAULT_SETTINGS["prompt.metadata_filter_words"],
    )


def resolve_autocomplete_source() -> str:
    settings = get_settings()
    return settings.get("autocomplete.source", DEFAULT_SETTINGS["autocomplete.source"])
