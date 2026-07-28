"""File-backed settings and Comfy settings overlay."""

from __future__ import annotations

import json
import os
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import cast

from ..infrastructure.filesystem.atomic_json import (
    AtomicJsonStore,
    create_atomic_json_store,
)
from ..infrastructure.filesystem.paths import USER_DATA_DIR
from .schema import (
    COMFY_COLOR_SETTING_KEYS,
    COMFY_SETTING_KEYS,
    DEFAULT_SETTINGS,
    LONG_TEXT_SETTING_ALIASES,
    LONG_TEXT_SETTING_KEYS,
)

SETTINGS_FILE = USER_DATA_DIR / "settings.json"
LONG_TEXT_SETTINGS_FILE = USER_DATA_DIR / "long_text_settings.json"
_AUTOCOMPLETE_SOURCE_KEY = "autocomplete.source"
_COMFY_AUTOCOMPLETE_SOURCE_KEY = "EasyUseAnima.Prompt.AutocompleteSource"
_COMFY_LOCALE_KEY = "Comfy.Locale"
_KOREAN_AUTOCOMPLETE_SOURCE = "localsmile_kr_wiki"


@dataclass(frozen=True, slots=True)
class _SettingsRepository:
    settings_file: Path
    long_text_settings_file: Path
    store_factory: Callable[..., AtomicJsonStore]

    def store(
        self,
        path: Path,
        *,
        backup: bool | str | os.PathLike[str] = True,
    ) -> AtomicJsonStore:
        return self.store_factory(path, backup=backup)


def _current_settings_repository() -> _SettingsRepository:
    return _SettingsRepository(
        settings_file=SETTINGS_FILE,
        long_text_settings_file=LONG_TEXT_SETTINGS_FILE,
        store_factory=create_atomic_json_store,
    )


def _read_json_file(path: Path) -> dict:
    repository = _current_settings_repository()
    try:
        data = repository.store(path).read(default={})
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
    repository = _current_settings_repository()
    return _normalize_long_text_settings(
        _read_json_file(repository.long_text_settings_file)
    )


def save_long_text_settings(values: dict) -> dict:
    repository = _current_settings_repository()
    if not isinstance(values, dict):
        values = {}
    updates = _normalize_long_text_settings(values)
    saved: dict = {}

    def merge(current) -> dict:
        settings = _normalize_long_text_settings(
            current if isinstance(current, dict) else {}
        )
        settings.update(updates)
        saved.update(settings)
        return {
            "version": 1,
            "values": {
                key: settings.get(key, "") for key in sorted(LONG_TEXT_SETTING_KEYS)
            },
        }

    repository.store(repository.long_text_settings_file).update(
        merge,
        default={},
        trailing_newline=True,
    )
    return saved


def _comfy_settings_candidates() -> list[Path]:
    candidates: list[Path] = []
    try:
        import folder_paths  # type: ignore

        get_user_directory = getattr(folder_paths, "get_user_directory", None)
        if callable(get_user_directory):
            user_dir = Path(
                cast(str | os.PathLike[str], get_user_directory())
            )
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


def _is_korean_locale(value) -> bool:
    locale = str(value or "").strip().casefold()
    return (
        locale == "ko"
        or locale.startswith("ko-")
        or "korean" in locale
        or "한국어" in locale
    )


def _initial_autocomplete_source(comfy_settings: dict) -> str:
    if _is_korean_locale(comfy_settings.get(_COMFY_LOCALE_KEY)):
        return _KOREAN_AUTOCOMPLETE_SOURCE
    return DEFAULT_SETTINGS[_AUTOCOMPLETE_SOURCE_KEY]


def _initialize_autocomplete_source(data: dict, comfy_settings: dict) -> dict:
    if (
        _AUTOCOMPLETE_SOURCE_KEY in data
        or _COMFY_AUTOCOMPLETE_SOURCE_KEY in comfy_settings
    ):
        return data

    source = _initial_autocomplete_source(comfy_settings)
    initialized = dict(data)
    initialized[_AUTOCOMPLETE_SOURCE_KEY] = source

    def merge(current) -> dict:
        if not isinstance(current, dict):
            return initialized
        if _AUTOCOMPLETE_SOURCE_KEY in current:
            return current
        current = dict(current)
        current[_AUTOCOMPLETE_SOURCE_KEY] = source
        return current

    repository = _current_settings_repository()
    try:
        persisted = repository.store(repository.settings_file).update(
            merge,
            default={},
            trailing_newline=True,
        )
    except OSError:
        return initialized
    return persisted if isinstance(persisted, dict) else initialized


def _stringify_setting_value(value) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def _apply_prompt_studio_color_settings(
    settings: dict,
    comfy_settings: dict,
) -> None:
    if "EasyUseAnima.Prompt.HighlightColors" in comfy_settings:
        return

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


def _apply_comfy_settings(
    settings: dict,
    comfy_settings: dict | None = None,
) -> dict:
    comfy_settings = (
        _load_comfy_settings()
        if comfy_settings is None
        else comfy_settings
    )
    for comfy_key, internal_key in COMFY_SETTING_KEYS.items():
        if comfy_key in comfy_settings and internal_key in DEFAULT_SETTINGS:
            settings[internal_key] = _stringify_setting_value(
                comfy_settings[comfy_key]
            )
    _apply_prompt_studio_color_settings(settings, comfy_settings)
    return settings


def _apply_long_text_settings(settings: dict) -> dict:
    settings.update(load_long_text_settings())
    return settings


def get_settings() -> dict:
    repository = _current_settings_repository()
    data = _read_json_file(repository.settings_file)
    comfy_settings = _load_comfy_settings()
    data = _initialize_autocomplete_source(data, comfy_settings)
    settings = dict(DEFAULT_SETTINGS)
    for key in DEFAULT_SETTINGS:
        if key in data:
            value = data[key]
            settings[key] = "" if value is None else str(value)
    return _apply_long_text_settings(
        _apply_comfy_settings(settings, comfy_settings)
    )


def save_setting(key: str, value) -> dict:
    if key not in DEFAULT_SETTINGS:
        raise KeyError(f"Unknown setting: {key}")
    repository = _current_settings_repository()
    store = repository.store(repository.settings_file)
    with store.locked():
        settings = get_settings()
        settings[key] = _stringify_setting_value(value)
        store.write(settings, trailing_newline=True)
    return settings


__all__ = (
    "LONG_TEXT_SETTINGS_FILE",
    "SETTINGS_FILE",
    "get_settings",
    "load_long_text_settings",
    "save_long_text_settings",
    "save_setting",
)
