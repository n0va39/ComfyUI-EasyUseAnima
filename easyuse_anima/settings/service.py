"""Public settings projection and feature-specific value resolvers."""

from __future__ import annotations

from ..translation.contracts import (
    DEFAULT_PROMPT_TRANSLATION_SOURCE,
    DEFAULT_PROMPT_TRANSLATION_TARGET,
    PromptTranslationSettings,
    normalize_prompt_translation_language,
    normalize_prompt_translation_provider,
)
from .repository import get_settings
from .schema import (
    AUTOCOMPLETE_COMMIT_KEYS,
    AUTOCOMPLETE_COMMIT_MODES,
    AUTOCOMPLETE_MODES,
    DEFAULT_SETTINGS,
    NAIA_PREPROCESSING_KEYS,
    NAIA_RESOLUTION_BUCKETS,
    NAIA_RESOLUTION_MODES,
    _SettingsRead,
)

_PublicSettingsValue = str | int | float
_PublicSettings = dict[str, _PublicSettingsValue]


def public_settings() -> _PublicSettings:
    settings = get_settings()
    return {
        "prompt.metadata_filter_words": settings.get(
            "prompt.metadata_filter_words", ""
        ),
        "autocomplete.source": settings.get(
            "autocomplete.source",
            DEFAULT_SETTINGS["autocomplete.source"],
        ),
        "autocomplete.limit": resolve_autocomplete_limit(settings),
        "autocomplete.mode": resolve_autocomplete_mode(settings),
        "autocomplete.artist_prefix": _resolve_autocomplete_artist_prefix(settings),
        "autocomplete.commit_key": resolve_autocomplete_commit_key(settings),
        "autocomplete.commit_mode": resolve_autocomplete_commit_mode(settings),
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
        "autocomplete.preview_completion": settings.get(
            "autocomplete.preview_completion",
            DEFAULT_SETTINGS["autocomplete.preview_completion"],
        ),
        "autocomplete.preview_closing_brackets": settings.get(
            "autocomplete.preview_closing_brackets",
            DEFAULT_SETTINGS["autocomplete.preview_closing_brackets"],
        ),
        "lora_preset.name_display": settings.get(
            "lora_preset.name_display",
            DEFAULT_SETTINGS["lora_preset.name_display"],
        ),
        "lora_preset.menu_mode": resolve_lora_preset_menu_mode(settings),
        "lora_preset.strength_button_step": (
            resolve_lora_preset_strength_button_step(settings)
        ),
        "lora_preset.strength_drag_step": (
            resolve_lora_preset_strength_drag_step(settings)
        ),
        "lora_preset.strength_drag_pixels": (
            resolve_lora_preset_strength_drag_pixels(settings)
        ),
        "prompt_studio.typo_indicator": settings.get(
            "prompt_studio.typo_indicator",
            DEFAULT_SETTINGS["prompt_studio.typo_indicator"],
        ),
        "prompt_studio.weight_syntax_underline": settings.get(
            "prompt_studio.weight_syntax_underline",
            DEFAULT_SETTINGS["prompt_studio.weight_syntax_underline"],
        ),
        "prompt_studio.selection_parenthesis_weight": settings.get(
            "prompt_studio.selection_parenthesis_weight",
            DEFAULT_SETTINGS["prompt_studio.selection_parenthesis_weight"],
        ),
        "prompt_studio.comment_italic": settings.get(
            "prompt_studio.comment_italic",
            DEFAULT_SETTINGS["prompt_studio.comment_italic"],
        ),
        "prompt_studio.font_override": settings.get(
            "prompt_studio.font_override",
            DEFAULT_SETTINGS["prompt_studio.font_override"],
        ),
        "prompt_studio.font_family": resolve_prompt_studio_font_family(settings),
        "prompt_studio.font_size": resolve_prompt_studio_font_size(settings),
        "prompt_studio.colors": settings.get(
            "prompt_studio.colors",
            DEFAULT_SETTINGS["prompt_studio.colors"],
        ),
        "prompt_studio.trained_tag_tooltip": settings.get(
            "prompt_studio.trained_tag_tooltip",
            DEFAULT_SETTINGS["prompt_studio.trained_tag_tooltip"],
        ),
        "prompt_studio.naia_general_above_auto_toggle": settings.get(
            "prompt_studio.naia_general_above_auto_toggle",
            DEFAULT_SETTINGS["prompt_studio.naia_general_above_auto_toggle"],
        ),
        "prompt_translation.provider": resolve_prompt_translation_provider(settings),
        "prompt_translation.source": resolve_prompt_translation_source(settings),
        "prompt_translation.target": resolve_prompt_translation_target(settings),
        "wildcard.extra_paths": settings.get(
            "wildcard.extra_paths",
            DEFAULT_SETTINGS["wildcard.extra_paths"],
        ),
        "naia.host": settings.get("naia.host", DEFAULT_SETTINGS["naia.host"]),
        "naia.port": resolve_naia_port(settings),
        "naia.allow_remote_api": settings.get(
            "naia.allow_remote_api",
            DEFAULT_SETTINGS["naia.allow_remote_api"],
        ),
        "naia.use_naia_settings": settings.get(
            "naia.use_naia_settings",
            DEFAULT_SETTINGS["naia.use_naia_settings"],
        ),
        "naia.resolution_mode": resolve_naia_resolution_mode(settings),
        "naia.resolution_bucket": resolve_naia_resolution_bucket(settings),
        "naia.resolution_scale": resolve_naia_resolution_scale(settings),
        "naia.resolution_max_long_edge": resolve_naia_resolution_max_long_edge(
            settings
        ),
        "naia.pre_prompt": settings.get("naia.pre_prompt", ""),
        "naia.post_prompt": settings.get("naia.post_prompt", ""),
        "naia.auto_hide": settings.get("naia.auto_hide", ""),
        **{
            f"naia.{key}": settings.get(
                f"naia.{key}", DEFAULT_SETTINGS[f"naia.{key}"]
            )
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
    return settings.get(
        "autocomplete.source",
        DEFAULT_SETTINGS["autocomplete.source"],
    )


def resolve_autocomplete_limit(settings: _SettingsRead | None = None) -> int:
    settings = settings or get_settings()
    try:
        value = int(
            settings.get(
                "autocomplete.limit",
                DEFAULT_SETTINGS["autocomplete.limit"],
            )
        )
    except (TypeError, ValueError):
        value = int(DEFAULT_SETTINGS["autocomplete.limit"])
    return max(1, min(100, value))


def resolve_autocomplete_mode(settings: _SettingsRead | None = None) -> str:
    settings = settings or get_settings()
    value = str(
        settings.get("autocomplete.mode", DEFAULT_SETTINGS["autocomplete.mode"])
        or DEFAULT_SETTINGS["autocomplete.mode"]
    ).strip()
    if value in AUTOCOMPLETE_MODES:
        return value
    return DEFAULT_SETTINGS["autocomplete.mode"]


def _resolve_autocomplete_artist_prefix(
    settings: _SettingsRead | None = None,
) -> str:
    settings = settings or get_settings()
    default = DEFAULT_SETTINGS["autocomplete.artist_prefix"]
    value = str(settings.get("autocomplete.artist_prefix", default) or "").strip()
    if (
        not value
        or len(value) > 32
        or "," in value
        or any(ord(character) < 32 or 127 <= ord(character) <= 159 for character in value)
    ):
        return default
    return value


def resolve_autocomplete_commit_key(settings: _SettingsRead | None = None) -> str:
    settings = settings or get_settings()
    value = str(
        settings.get(
            "autocomplete.commit_key",
            DEFAULT_SETTINGS["autocomplete.commit_key"],
        )
        or DEFAULT_SETTINGS["autocomplete.commit_key"]
    ).strip()
    if value in AUTOCOMPLETE_COMMIT_KEYS:
        return value
    return DEFAULT_SETTINGS["autocomplete.commit_key"]


def resolve_autocomplete_commit_mode(settings: _SettingsRead | None = None) -> str:
    settings = settings or get_settings()
    value = str(
        settings.get(
            "autocomplete.commit_mode",
            DEFAULT_SETTINGS["autocomplete.commit_mode"],
        )
        or DEFAULT_SETTINGS["autocomplete.commit_mode"]
    ).strip()
    if value in AUTOCOMPLETE_COMMIT_MODES:
        return value
    return DEFAULT_SETTINGS["autocomplete.commit_mode"]


def _resolve_lora_preset_strength_step(
    settings: _SettingsRead,
    key: str,
    max_value: float,
) -> float:
    try:
        value = float(settings.get(key, DEFAULT_SETTINGS[key]))
    except (TypeError, ValueError):
        value = float(DEFAULT_SETTINGS[key])
    return max(0.001, min(max_value, value))


def resolve_lora_preset_strength_button_step(
    settings: _SettingsRead | None = None,
) -> float:
    settings = settings or get_settings()
    return _resolve_lora_preset_strength_step(
        settings,
        "lora_preset.strength_button_step",
        0.5,
    )


def resolve_lora_preset_strength_drag_step(
    settings: _SettingsRead | None = None,
) -> float:
    settings = settings or get_settings()
    return _resolve_lora_preset_strength_step(
        settings,
        "lora_preset.strength_drag_step",
        0.2,
    )


def resolve_lora_preset_strength_drag_pixels(
    settings: _SettingsRead | None = None,
) -> int:
    settings = settings or get_settings()
    try:
        value = int(
            float(
                settings.get(
                    "lora_preset.strength_drag_pixels",
                    DEFAULT_SETTINGS["lora_preset.strength_drag_pixels"],
                )
            )
        )
    except (TypeError, ValueError):
        value = int(DEFAULT_SETTINGS["lora_preset.strength_drag_pixels"])
    return max(1, min(100, value))


def resolve_lora_preset_menu_mode(settings: _SettingsRead | None = None) -> str:
    settings = settings or get_settings()
    value = str(
        settings.get(
            "lora_preset.menu_mode",
            DEFAULT_SETTINGS["lora_preset.menu_mode"],
        )
        or DEFAULT_SETTINGS["lora_preset.menu_mode"]
    ).strip()
    if value in {"tree", "list"}:
        return value
    return DEFAULT_SETTINGS["lora_preset.menu_mode"]


def resolve_prompt_studio_font_family(
    settings: _SettingsRead | None = None,
) -> str:
    settings = settings or get_settings()
    value = str(settings.get("prompt_studio.font_family", "") or "")
    for token in (";", "{", "}", "\r", "\n"):
        value = value.replace(token, "")
    return value.strip()[:160]


def resolve_prompt_studio_font_size(settings: _SettingsRead | None = None) -> int:
    settings = settings or get_settings()
    try:
        value = int(
            float(
                settings.get(
                    "prompt_studio.font_size",
                    DEFAULT_SETTINGS["prompt_studio.font_size"],
                )
            )
        )
    except (TypeError, ValueError):
        value = int(DEFAULT_SETTINGS["prompt_studio.font_size"])
    return max(8, min(24, value))


def resolve_prompt_translation_provider(
    settings: _SettingsRead | None = None,
) -> str:
    settings = settings or get_settings()
    return normalize_prompt_translation_provider(
        settings.get(
            "prompt_translation.provider",
            DEFAULT_SETTINGS["prompt_translation.provider"],
        )
    )


def resolve_prompt_translation_source(
    settings: _SettingsRead | None = None,
) -> str:
    settings = settings or get_settings()
    return normalize_prompt_translation_language(
        settings.get(
            "prompt_translation.source",
            DEFAULT_SETTINGS["prompt_translation.source"],
        ),
        DEFAULT_PROMPT_TRANSLATION_SOURCE,
    )


def resolve_prompt_translation_target(
    settings: _SettingsRead | None = None,
) -> str:
    settings = settings or get_settings()
    return normalize_prompt_translation_language(
        settings.get(
            "prompt_translation.target",
            DEFAULT_SETTINGS["prompt_translation.target"],
        ),
        DEFAULT_PROMPT_TRANSLATION_TARGET,
    )


def resolve_prompt_translation_settings(
    settings: _SettingsRead | None = None,
) -> PromptTranslationSettings:
    settings = settings or get_settings()
    return PromptTranslationSettings(
        provider=resolve_prompt_translation_provider(settings),
        source=resolve_prompt_translation_source(settings),
        target=resolve_prompt_translation_target(settings),
    )


def _resolve_settings_bool(settings: _SettingsRead, key: str) -> bool:
    return str(settings.get(key, DEFAULT_SETTINGS[key])).strip().lower() in {
        "true",
        "1",
        "yes",
        "on",
        "enabled",
    }


def resolve_naia_port(settings: _SettingsRead | None = None) -> int:
    settings = settings or get_settings()
    try:
        value = int(settings.get("naia.port", DEFAULT_SETTINGS["naia.port"]))
    except (TypeError, ValueError):
        value = int(DEFAULT_SETTINGS["naia.port"])
    return max(1, min(65535, value))


def resolve_naia_resolution_mode(settings: _SettingsRead | None = None) -> str:
    settings = settings or get_settings()
    value = str(
        settings.get(
            "naia.resolution_mode",
            DEFAULT_SETTINGS["naia.resolution_mode"],
        )
        or DEFAULT_SETTINGS["naia.resolution_mode"]
    ).strip().lower()
    if value in NAIA_RESOLUTION_MODES:
        return value
    if value == "bucket_fit":
        return "bucket"
    return DEFAULT_SETTINGS["naia.resolution_mode"]


def resolve_naia_resolution_bucket(settings: _SettingsRead | None = None) -> str:
    settings = settings or get_settings()
    value = str(
        settings.get(
            "naia.resolution_bucket",
            DEFAULT_SETTINGS["naia.resolution_bucket"],
        )
        or DEFAULT_SETTINGS["naia.resolution_bucket"]
    ).strip()
    return (
        value
        if value in NAIA_RESOLUTION_BUCKETS
        else DEFAULT_SETTINGS["naia.resolution_bucket"]
    )


def resolve_naia_resolution_scale(settings: _SettingsRead | None = None) -> float:
    settings = settings or get_settings()
    try:
        value = float(
            settings.get(
                "naia.resolution_scale",
                DEFAULT_SETTINGS["naia.resolution_scale"],
            )
        )
    except (TypeError, ValueError):
        value = float(DEFAULT_SETTINGS["naia.resolution_scale"])
    return max(0.25, min(4.0, value))


def resolve_naia_resolution_max_long_edge(
    settings: _SettingsRead | None = None,
) -> int:
    settings = settings or get_settings()
    try:
        value = int(
            float(
                settings.get(
                    "naia.resolution_max_long_edge",
                    DEFAULT_SETTINGS["naia.resolution_max_long_edge"],
                )
            )
        )
    except (TypeError, ValueError):
        value = int(DEFAULT_SETTINGS["naia.resolution_max_long_edge"])
    if value <= 0:
        return 0
    return max(32, min(16384, value))


def resolve_naia_settings() -> dict:
    settings = get_settings()
    use_naia_settings = _resolve_settings_bool(settings, "naia.use_naia_settings")
    preprocessing: dict[str, str] = {}
    for key in NAIA_PREPROCESSING_KEYS:
        value = settings.get(
            f"naia.{key}",
            DEFAULT_SETTINGS[f"naia.{key}"],
        )
        preprocessing[key] = value if value in ("skip", "on", "off") else "skip"
    return {
        "host": settings.get("naia.host", DEFAULT_SETTINGS["naia.host"])
        or DEFAULT_SETTINGS["naia.host"],
        "port": resolve_naia_port(settings),
        "allow_remote_api": _resolve_settings_bool(settings, "naia.allow_remote_api"),
        "use_naia_settings": use_naia_settings,
        "resolution_mode": resolve_naia_resolution_mode(settings),
        "resolution_bucket": resolve_naia_resolution_bucket(settings),
        "resolution_scale": resolve_naia_resolution_scale(settings),
        "resolution_max_long_edge": resolve_naia_resolution_max_long_edge(settings),
        "pre_prompt": settings.get("naia.pre_prompt", ""),
        "post_prompt": settings.get("naia.post_prompt", ""),
        "auto_hide": settings.get("naia.auto_hide", ""),
        "preprocessing": preprocessing,
    }


__all__ = (
    "public_settings",
    "resolve_autocomplete_commit_key",
    "resolve_autocomplete_commit_mode",
    "resolve_autocomplete_limit",
    "resolve_autocomplete_mode",
    "resolve_autocomplete_source",
    "resolve_lora_preset_menu_mode",
    "resolve_lora_preset_strength_button_step",
    "resolve_lora_preset_strength_drag_pixels",
    "resolve_lora_preset_strength_drag_step",
    "resolve_metadata_filter_words",
    "resolve_naia_port",
    "resolve_naia_resolution_bucket",
    "resolve_naia_resolution_max_long_edge",
    "resolve_naia_resolution_mode",
    "resolve_naia_resolution_scale",
    "resolve_naia_settings",
    "resolve_prompt_studio_font_family",
    "resolve_prompt_studio_font_size",
    "resolve_prompt_translation_provider",
    "resolve_prompt_translation_settings",
    "resolve_prompt_translation_source",
    "resolve_prompt_translation_target",
)
