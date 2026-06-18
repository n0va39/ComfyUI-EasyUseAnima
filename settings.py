from __future__ import annotations

import json

try:
    from .anima_prompt.knowledge import PACKAGE_DATA_DIR
except ImportError:
    from anima_prompt.knowledge import PACKAGE_DATA_DIR

SETTINGS_FILE = PACKAGE_DATA_DIR / "settings.json"

DEFAULT_SETTINGS = {
    "prompt.metadata_filter_words": "",
    "autocomplete.source": "localsmile_kr_wiki",
    "autocomplete.limit": "20",
    "lora_preset.name_display": "name",
    "prompt_studio.typo_indicator": "true",
    "prompt_studio.colors": "",
    "naia.host": "127.0.0.1",
    "naia.port": "7243",
    "naia.use_naia_settings": "true",
    "naia.pre_prompt": "",
    "naia.post_prompt": "",
    "naia.auto_hide": "",
    "naia.remove_author": "skip",
    "naia.remove_work_title": "skip",
    "naia.remove_character_name": "skip",
    "naia.remove_character_features": "skip",
    "naia.remove_clothes": "skip",
    "naia.remove_color": "skip",
    "naia.remove_location_and_background_color": "skip",
    "naia.remove_expression": "skip",
    "naia.remove_pose_action": "skip",
    "naia.remove_meta_tags": "skip",
    "naia.remove_object_tags": "skip",
    "naia.remove_noise_tags": "skip",
    "naia.e621_auto_boost": "skip",
    "naia.danbooru_auto_weight": "skip",
    "naia.tag_implication_compression": "skip",
}

NAIA_PREPROCESSING_KEYS = [
    "remove_author",
    "remove_work_title",
    "remove_character_name",
    "remove_character_features",
    "remove_clothes",
    "remove_color",
    "remove_location_and_background_color",
    "remove_expression",
    "remove_pose_action",
    "remove_meta_tags",
    "remove_object_tags",
    "remove_noise_tags",
    "e621_auto_boost",
    "danbooru_auto_weight",
    "tag_implication_compression",
]


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
        "autocomplete.limit": resolve_autocomplete_limit(settings),
        "lora_preset.name_display": settings.get(
            "lora_preset.name_display",
            DEFAULT_SETTINGS["lora_preset.name_display"],
        ),
        "prompt_studio.typo_indicator": settings.get(
            "prompt_studio.typo_indicator",
            DEFAULT_SETTINGS["prompt_studio.typo_indicator"],
        ),
        "prompt_studio.colors": settings.get(
            "prompt_studio.colors",
            DEFAULT_SETTINGS["prompt_studio.colors"],
        ),
        "naia.host": settings.get("naia.host", DEFAULT_SETTINGS["naia.host"]),
        "naia.port": resolve_naia_port(settings),
        "naia.use_naia_settings": settings.get(
            "naia.use_naia_settings",
            DEFAULT_SETTINGS["naia.use_naia_settings"],
        ),
        "naia.pre_prompt": settings.get("naia.pre_prompt", ""),
        "naia.post_prompt": settings.get("naia.post_prompt", ""),
        "naia.auto_hide": settings.get("naia.auto_hide", ""),
        **{
            f"naia.{key}": settings.get(f"naia.{key}", DEFAULT_SETTINGS[f"naia.{key}"])
            for key in NAIA_PREPROCESSING_KEYS
        },
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


def resolve_autocomplete_limit(settings: dict | None = None) -> int:
    settings = settings or get_settings()
    try:
        value = int(settings.get("autocomplete.limit", DEFAULT_SETTINGS["autocomplete.limit"]))
    except (TypeError, ValueError):
        value = int(DEFAULT_SETTINGS["autocomplete.limit"])
    return max(1, min(100, value))


def resolve_naia_port(settings: dict | None = None) -> int:
    settings = settings or get_settings()
    try:
        value = int(settings.get("naia.port", DEFAULT_SETTINGS["naia.port"]))
    except (TypeError, ValueError):
        value = int(DEFAULT_SETTINGS["naia.port"])
    return max(1, min(65535, value))


def resolve_naia_settings() -> dict:
    settings = get_settings()
    use_naia_settings = settings.get(
        "naia.use_naia_settings",
        DEFAULT_SETTINGS["naia.use_naia_settings"],
    ).strip().lower() not in ("false", "0", "no", "off", "disabled")
    preprocessing = {}
    for key in NAIA_PREPROCESSING_KEYS:
        value = settings.get(f"naia.{key}", DEFAULT_SETTINGS[f"naia.{key}"])
        preprocessing[key] = value if value in ("skip", "on", "off") else "skip"
    return {
        "host": settings.get("naia.host", DEFAULT_SETTINGS["naia.host"]) or DEFAULT_SETTINGS["naia.host"],
        "port": resolve_naia_port(settings),
        "use_naia_settings": use_naia_settings,
        "pre_prompt": settings.get("naia.pre_prompt", ""),
        "post_prompt": settings.get("naia.post_prompt", ""),
        "auto_hide": settings.get("naia.auto_hide", ""),
        "preprocessing": preprocessing,
    }
