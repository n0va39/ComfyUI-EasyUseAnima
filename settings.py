from __future__ import annotations

import json
from pathlib import Path

try:
    from .storage import USER_DATA_DIR
except ImportError:
    from storage import USER_DATA_DIR

SETTINGS_FILE = USER_DATA_DIR / "settings.json"
LONG_TEXT_SETTINGS_FILE = USER_DATA_DIR / "long_text_settings.json"

DEFAULT_SETTINGS = {
    "prompt.metadata_filter_words": "",
    "autocomplete.source": "localsmile_kr_wiki",
    "autocomplete.limit": "20",
    "autocomplete.mode": "compatible_global",
    "autocomplete.commit_key": "enter",
    "autocomplete.append_separator": "false",
    "autocomplete.no_comma_after_period": "true",
    "autocomplete.detect_natural_sentences": "true",
    "lora_preset.name_display": "name",
    "lora_preset.menu_mode": "tree",
    "lora_preset.strength_button_step": "0.05",
    "lora_preset.strength_drag_step": "0.05",
    "lora_preset.strength_drag_pixels": "8",
    "prompt_studio.typo_indicator": "true",
    "prompt_studio.comment_italic": "true",
    "prompt_studio.colors": "",
    "prompt_studio.naia_general_above_auto_toggle": "false",
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

AUTOCOMPLETE_MODES = {
    "off",
    "easyuse_nodes",
    "compatible_global",
}

AUTOCOMPLETE_COMMIT_KEYS = {
    "enter",
    "tab",
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

PROMPT_STUDIO_COLOR_KEYS = [
    "quality",
    "safety",
    "year",
    "count",
    "character",
    "artist",
    "copyright",
    "general",
    "meta",
    "natural",
    "comment",
    "artist_unknown",
    "unknown",
]

COMFY_SETTING_KEYS = {
    "EasyUseAnima.Prompt.MetadataFilter": "prompt.metadata_filter_words",
    "EasyUseAnima.Prompt.AutocompleteSource": "autocomplete.source",
    "EasyUseAnima.Prompt.AutocompleteLimit": "autocomplete.limit",
    "EasyUseAnima.Prompt.AutocompleteMode": "autocomplete.mode",
    "EasyUseAnima.Prompt.AutocompleteCommitKey": "autocomplete.commit_key",
    "EasyUseAnima.Prompt.AutocompleteAppendSeparator": "autocomplete.append_separator",
    "EasyUseAnima.Prompt.AutocompleteNoCommaAfterPeriod": "autocomplete.no_comma_after_period",
    "EasyUseAnima.Prompt.AutocompleteDetectNaturalSentences": "autocomplete.detect_natural_sentences",
    "EasyUseAnima.Prompt.TypoIndicator": "prompt_studio.typo_indicator",
    "EasyUseAnima.Prompt.CommentItalic": "prompt_studio.comment_italic",
    "EasyUseAnima.Prompt.HighlightColors": "prompt_studio.colors",
    "EasyUseAnima.Prompt.NaiaGeneralAutoToggle": "prompt_studio.naia_general_above_auto_toggle",
    "EasyUseAnima.LoraPreset.NameDisplay": "lora_preset.name_display",
    "EasyUseAnima.LoraPreset.MenuMode": "lora_preset.menu_mode",
    "EasyUseAnima.LoraPreset.StrengthButtonStep": "lora_preset.strength_button_step",
    "EasyUseAnima.LoraPreset.StrengthDragStep": "lora_preset.strength_drag_step",
    "EasyUseAnima.LoraPreset.StrengthDragPixels": "lora_preset.strength_drag_pixels",
    "EasyUseAnima.NAIA.Host": "naia.host",
    "EasyUseAnima.NAIA.Port": "naia.port",
    "EasyUseAnima.NAIA.UseDesktopPromptEngineering": "naia.use_naia_settings",
    "EasyUseAnima.NAIA.pre_prompt": "naia.pre_prompt",
    "EasyUseAnima.NAIA.post_prompt": "naia.post_prompt",
    "EasyUseAnima.NAIA.auto_hide": "naia.auto_hide",
    **{
        f"EasyUseAnima.NAIA.{key}": f"naia.{key}"
        for key in NAIA_PREPROCESSING_KEYS
    },
}

COMFY_COLOR_SETTING_KEYS = {
    f"EasyUseAnima.Prompt.HighlightColor.{key}": key
    for key in PROMPT_STUDIO_COLOR_KEYS
}

LONG_TEXT_SETTING_KEYS = {
    "prompt.metadata_filter_words",
    "naia.pre_prompt",
    "naia.post_prompt",
    "naia.auto_hide",
}

LONG_TEXT_SETTING_ALIASES = {
    "metadata_filter": "prompt.metadata_filter_words",
    "metadataFilter": "prompt.metadata_filter_words",
    "EasyUseAnima.Prompt.MetadataFilter": "prompt.metadata_filter_words",
    "pre_prompt": "naia.pre_prompt",
    "prePrompt": "naia.pre_prompt",
    "EasyUseAnima.NAIA.pre_prompt": "naia.pre_prompt",
    "post_prompt": "naia.post_prompt",
    "postPrompt": "naia.post_prompt",
    "EasyUseAnima.NAIA.post_prompt": "naia.post_prompt",
    "auto_hide": "naia.auto_hide",
    "autoHide": "naia.auto_hide",
    "EasyUseAnima.NAIA.auto_hide": "naia.auto_hide",
}


def _read_json_file(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def _normalize_long_text_settings(data: dict) -> dict:
    values = data.get("values", data)
    if not isinstance(values, dict):
        return {}
    normalized = {}
    for key, value in values.items():
        internal_key = LONG_TEXT_SETTING_ALIASES.get(str(key), str(key))
        if internal_key in LONG_TEXT_SETTING_KEYS:
            normalized[internal_key] = "" if value is None else str(value)
    return normalized


def load_long_text_settings() -> dict:
    return _normalize_long_text_settings(_read_json_file(LONG_TEXT_SETTINGS_FILE))


def save_long_text_settings(values: dict) -> dict:
    if not isinstance(values, dict):
        values = {}
    settings = load_long_text_settings()
    settings.update(_normalize_long_text_settings(values))
    LONG_TEXT_SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    LONG_TEXT_SETTINGS_FILE.write_text(
        json.dumps(
            {
                "version": 1,
                "values": {key: settings.get(key, "") for key in sorted(LONG_TEXT_SETTING_KEYS)},
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return settings


def _comfy_settings_candidates() -> list[Path]:
    candidates: list[Path] = []
    try:
        import folder_paths  # type: ignore

        get_user_directory = getattr(folder_paths, "get_user_directory", None)
        if callable(get_user_directory):
            user_dir = Path(get_user_directory())
            candidates.extend(
                [
                    user_dir / "default" / "comfy.settings.json",
                    user_dir / "comfy.settings.json",
                ]
            )
    except Exception:
        pass
    return candidates


def _load_comfy_settings() -> dict:
    for path in _comfy_settings_candidates():
        data = _read_json_file(path)
        if data:
            return data
    return {}


def _stringify_setting_value(value) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def _apply_prompt_studio_color_settings(settings: dict, comfy_settings: dict) -> None:
    colors = {}
    current = settings.get("prompt_studio.colors", "")
    if current:
        try:
            parsed = json.loads(current)
        except json.JSONDecodeError:
            parsed = {}
        if isinstance(parsed, dict):
            colors.update({str(key): str(value) for key, value in parsed.items()})

    changed = False
    for comfy_key, color_key in COMFY_COLOR_SETTING_KEYS.items():
        if comfy_key not in comfy_settings:
            continue
        value = _stringify_setting_value(comfy_settings[comfy_key]).strip()
        if value:
            colors[color_key] = value
            changed = True

    if changed:
        settings["prompt_studio.colors"] = json.dumps(colors, ensure_ascii=False)


def _apply_comfy_settings(settings: dict) -> dict:
    comfy_settings = _load_comfy_settings()
    for comfy_key, internal_key in COMFY_SETTING_KEYS.items():
        if comfy_key in comfy_settings and internal_key in DEFAULT_SETTINGS:
            settings[internal_key] = _stringify_setting_value(comfy_settings[comfy_key])
    _apply_prompt_studio_color_settings(settings, comfy_settings)
    return settings


def _apply_long_text_settings(settings: dict) -> dict:
    settings.update(load_long_text_settings())
    return settings


def get_settings() -> dict:
    settings = dict(DEFAULT_SETTINGS)
    data = _read_json_file(SETTINGS_FILE)
    if isinstance(data, dict):
        for key in DEFAULT_SETTINGS:
            if key in data:
                value = data[key]
                settings[key] = "" if value is None else str(value)
    return _apply_long_text_settings(_apply_comfy_settings(settings))


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
        "autocomplete.mode": resolve_autocomplete_mode(settings),
        "autocomplete.commit_key": resolve_autocomplete_commit_key(settings),
        "autocomplete.append_separator": settings.get(
            "autocomplete.append_separator",
            DEFAULT_SETTINGS["autocomplete.append_separator"],
        ),
        "autocomplete.no_comma_after_period": settings.get(
            "autocomplete.no_comma_after_period",
            DEFAULT_SETTINGS["autocomplete.no_comma_after_period"],
        ),
        "autocomplete.detect_natural_sentences": settings.get(
            "autocomplete.detect_natural_sentences",
            DEFAULT_SETTINGS["autocomplete.detect_natural_sentences"],
        ),
        "lora_preset.name_display": settings.get(
            "lora_preset.name_display",
            DEFAULT_SETTINGS["lora_preset.name_display"],
        ),
        "lora_preset.menu_mode": resolve_lora_preset_menu_mode(settings),
        "lora_preset.strength_button_step": resolve_lora_preset_strength_button_step(settings),
        "lora_preset.strength_drag_step": resolve_lora_preset_strength_drag_step(settings),
        "lora_preset.strength_drag_pixels": resolve_lora_preset_strength_drag_pixels(settings),
        "prompt_studio.typo_indicator": settings.get(
            "prompt_studio.typo_indicator",
            DEFAULT_SETTINGS["prompt_studio.typo_indicator"],
        ),
        "prompt_studio.comment_italic": settings.get(
            "prompt_studio.comment_italic",
            DEFAULT_SETTINGS["prompt_studio.comment_italic"],
        ),
        "prompt_studio.colors": settings.get(
            "prompt_studio.colors",
            DEFAULT_SETTINGS["prompt_studio.colors"],
        ),
        "prompt_studio.naia_general_above_auto_toggle": settings.get(
            "prompt_studio.naia_general_above_auto_toggle",
            DEFAULT_SETTINGS["prompt_studio.naia_general_above_auto_toggle"],
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


def resolve_autocomplete_mode(settings: dict | None = None) -> str:
    settings = settings or get_settings()
    value = str(
        settings.get("autocomplete.mode", DEFAULT_SETTINGS["autocomplete.mode"])
        or DEFAULT_SETTINGS["autocomplete.mode"]
    ).strip()
    if value in AUTOCOMPLETE_MODES:
        return value
    return DEFAULT_SETTINGS["autocomplete.mode"]


def resolve_autocomplete_commit_key(settings: dict | None = None) -> str:
    settings = settings or get_settings()
    value = str(
        settings.get("autocomplete.commit_key", DEFAULT_SETTINGS["autocomplete.commit_key"])
        or DEFAULT_SETTINGS["autocomplete.commit_key"]
    ).strip()
    if value in AUTOCOMPLETE_COMMIT_KEYS:
        return value
    return DEFAULT_SETTINGS["autocomplete.commit_key"]


def _resolve_lora_preset_strength_step(settings: dict, key: str, max_value: float) -> float:
    try:
        value = float(settings.get(key, DEFAULT_SETTINGS[key]))
    except (TypeError, ValueError):
        value = float(DEFAULT_SETTINGS[key])
    return max(0.001, min(max_value, value))


def resolve_lora_preset_strength_button_step(settings: dict | None = None) -> float:
    settings = settings or get_settings()
    return _resolve_lora_preset_strength_step(settings, "lora_preset.strength_button_step", 0.5)


def resolve_lora_preset_strength_drag_step(settings: dict | None = None) -> float:
    settings = settings or get_settings()
    return _resolve_lora_preset_strength_step(settings, "lora_preset.strength_drag_step", 0.2)


def resolve_lora_preset_strength_drag_pixels(settings: dict | None = None) -> int:
    settings = settings or get_settings()
    try:
        value = int(float(settings.get(
            "lora_preset.strength_drag_pixels",
            DEFAULT_SETTINGS["lora_preset.strength_drag_pixels"],
        )))
    except (TypeError, ValueError):
        value = int(DEFAULT_SETTINGS["lora_preset.strength_drag_pixels"])
    return max(1, min(100, value))


def resolve_lora_preset_menu_mode(settings: dict | None = None) -> str:
    settings = settings or get_settings()
    value = str(
        settings.get("lora_preset.menu_mode", DEFAULT_SETTINGS["lora_preset.menu_mode"])
        or DEFAULT_SETTINGS["lora_preset.menu_mode"]
    ).strip()
    if value in {"tree", "list"}:
        return value
    return DEFAULT_SETTINGS["lora_preset.menu_mode"]


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
