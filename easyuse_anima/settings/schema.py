"""Settings defaults, accepted values, and key mappings."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Literal, TypeAlias, TypedDict

from ..translation.contracts import (
    DEFAULT_PROMPT_TRANSLATION_SOURCE,
    DEFAULT_PROMPT_TRANSLATION_TARGET,
    PROMPT_TRANSLATION_PROVIDER_OFF,
)

_SettingsValues: TypeAlias = dict[str, str]
_SettingsRead: TypeAlias = Mapping[str, str]


class _SettingsDocumentV1(TypedDict):
    version: Literal[1]
    values: dict[str, object]


DEFAULT_SETTINGS: _SettingsValues = {
    "prompt.metadata_filter_words": "",
    "autocomplete.source": "dbr_danbooru_2025_09_01",
    "autocomplete.limit": "20",
    "autocomplete.mode": "compatible_global",
    "autocomplete.artist_prefix": "@",
    "autocomplete.commit_key": "enter",
    "autocomplete.commit_mode": "smart",
    "autocomplete.append_separator": "false",
    "autocomplete.no_comma_after_period": "true",
    "autocomplete.detect_natural_sentences": "true",
    "autocomplete.preview_completion": "false",
    "autocomplete.preview_closing_brackets": "false",
    "lora_preset.name_display": "name",
    "lora_preset.menu_mode": "tree",
    "lora_preset.strength_button_step": "0.05",
    "lora_preset.strength_drag_step": "0.05",
    "lora_preset.strength_drag_pixels": "8",
    "prompt_studio.typo_indicator": "true",
    "prompt_studio.weight_syntax_underline": "false",
    "prompt_studio.selection_parenthesis_weight": "false",
    "prompt_studio.comment_italic": "true",
    "prompt_studio.font_override": "false",
    "prompt_studio.font_family": "",
    "prompt_studio.font_size": "12",
    "prompt_studio.colors": "",
    "prompt_studio.trained_tag_tooltip": "true",
    "prompt_studio.naia_general_above_auto_toggle": "false",
    "prompt_translation.provider": PROMPT_TRANSLATION_PROVIDER_OFF,
    "prompt_translation.source": DEFAULT_PROMPT_TRANSLATION_SOURCE,
    "prompt_translation.target": DEFAULT_PROMPT_TRANSLATION_TARGET,
    "wildcard.extra_paths": "",
    "naia.host": "127.0.0.1",
    "naia.port": "7243",
    "naia.allow_remote_api": "false",
    "naia.use_naia_settings": "true",
    "naia.resolution_mode": "scale",
    "naia.resolution_bucket": "1024",
    "naia.resolution_scale": "1.0",
    "naia.resolution_max_long_edge": "0",
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

AUTOCOMPLETE_MODES: set[str] = {
    "off",
    "easyuse_nodes",
    "compatible_global",
}

AUTOCOMPLETE_COMMIT_KEYS: set[str] = {
    "enter",
    "tab",
}

AUTOCOMPLETE_COMMIT_MODES: set[str] = {
    "smart",
    "insert",
    "replace",
}

NAIA_RESOLUTION_MODES: set[str] = {
    "scale",
    "bucket",
}

NAIA_RESOLUTION_BUCKETS: set[str] = {
    "512",
    "768",
    "896",
    "1024",
    "1280",
    "1536",
}

NAIA_PREPROCESSING_KEYS: list[str] = [
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

PROMPT_STUDIO_COLOR_KEYS: list[str] = [
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
    "wildcard",
    "translation",
    "comment",
    "artist_unknown",
    "unknown",
]

COMFY_SETTING_KEYS: dict[str, str] = {
    "EasyUseAnima.Prompt.MetadataFilter": "prompt.metadata_filter_words",
    "EasyUseAnima.Prompt.AutocompleteSource": "autocomplete.source",
    "EasyUseAnima.Prompt.AutocompleteLimit": "autocomplete.limit",
    "EasyUseAnima.Prompt.AutocompleteMode": "autocomplete.mode",
    "EasyUseAnima.Prompt.AutocompleteArtistPrefix": "autocomplete.artist_prefix",
    "EasyUseAnima.Prompt.AutocompleteCommitKey": "autocomplete.commit_key",
    "EasyUseAnima.Prompt.AutocompleteCommitMode": "autocomplete.commit_mode",
    "EasyUseAnima.Prompt.AutocompleteAppendSeparator": "autocomplete.append_separator",
    "EasyUseAnima.Prompt.AutocompleteNoCommaAfterPeriod": "autocomplete.no_comma_after_period",
    "EasyUseAnima.Prompt.AutocompleteDetectNaturalSentences": "autocomplete.detect_natural_sentences",
    "EasyUseAnima.Prompt.AutocompletePreviewCompletion": "autocomplete.preview_completion",
    "EasyUseAnima.Prompt.AutocompletePreviewClosingBrackets": "autocomplete.preview_closing_brackets",
    "EasyUseAnima.Prompt.TypoIndicator": "prompt_studio.typo_indicator",
    "EasyUseAnima.Prompt.WeightSyntaxUnderline": "prompt_studio.weight_syntax_underline",
    "EasyUseAnima.Prompt.SelectionParenthesisWeight": (
        "prompt_studio.selection_parenthesis_weight"
    ),
    "EasyUseAnima.Prompt.CommentItalic": "prompt_studio.comment_italic",
    "EasyUseAnima.Prompt.FontOverride": "prompt_studio.font_override",
    "EasyUseAnima.Prompt.FontFamily": "prompt_studio.font_family",
    "EasyUseAnima.Prompt.FontSize": "prompt_studio.font_size",
    "EasyUseAnima.Prompt.HighlightColors": "prompt_studio.colors",
    "EasyUseAnima.Prompt.TrainedTagTooltip": "prompt_studio.trained_tag_tooltip",
    "EasyUseAnima.Prompt.NaiaGeneralAutoToggle": "prompt_studio.naia_general_above_auto_toggle",
    "EasyUseAnima.Prompt.TranslationProvider": "prompt_translation.provider",
    "EasyUseAnima.Prompt.TranslationSource": "prompt_translation.source",
    "EasyUseAnima.Prompt.TranslationTarget": "prompt_translation.target",
    "EasyUseAnima.Wildcard.ExtraPaths": "wildcard.extra_paths",
    "EasyUseAnima.LoraPreset.NameDisplay": "lora_preset.name_display",
    "EasyUseAnima.LoraPreset.MenuMode": "lora_preset.menu_mode",
    "EasyUseAnima.LoraPreset.StrengthButtonStep": "lora_preset.strength_button_step",
    "EasyUseAnima.LoraPreset.StrengthDragStep": "lora_preset.strength_drag_step",
    "EasyUseAnima.LoraPreset.StrengthDragPixels": "lora_preset.strength_drag_pixels",
    "EasyUseAnima.NAIA.Host": "naia.host",
    "EasyUseAnima.NAIA.Port": "naia.port",
    "EasyUseAnima.NAIA.AllowRemoteAPI": "naia.allow_remote_api",
    "EasyUseAnima.NAIA.UseDesktopPromptEngineering": "naia.use_naia_settings",
    "EasyUseAnima.NAIA.ResolutionMode": "naia.resolution_mode",
    "EasyUseAnima.NAIA.ResolutionBucket": "naia.resolution_bucket",
    "EasyUseAnima.NAIA.ResolutionScale": "naia.resolution_scale",
    "EasyUseAnima.NAIA.ResolutionMaxLongEdge": "naia.resolution_max_long_edge",
    "EasyUseAnima.NAIA.pre_prompt": "naia.pre_prompt",
    "EasyUseAnima.NAIA.post_prompt": "naia.post_prompt",
    "EasyUseAnima.NAIA.auto_hide": "naia.auto_hide",
    **{
        f"EasyUseAnima.NAIA.{key}": f"naia.{key}"
        for key in NAIA_PREPROCESSING_KEYS
    },
}

COMFY_COLOR_SETTING_KEYS: dict[str, str] = {
    f"EasyUseAnima.Prompt.HighlightColor.{key}": key
    for key in PROMPT_STUDIO_COLOR_KEYS
}

LONG_TEXT_SETTING_KEYS: set[str] = {
    "prompt.metadata_filter_words",
    "naia.pre_prompt",
    "naia.post_prompt",
    "naia.auto_hide",
}

LONG_TEXT_SETTING_ALIASES: dict[str, str] = {
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


__all__ = (
    "AUTOCOMPLETE_COMMIT_KEYS",
    "AUTOCOMPLETE_COMMIT_MODES",
    "AUTOCOMPLETE_MODES",
    "COMFY_COLOR_SETTING_KEYS",
    "COMFY_SETTING_KEYS",
    "DEFAULT_SETTINGS",
    "LONG_TEXT_SETTING_ALIASES",
    "LONG_TEXT_SETTING_KEYS",
    "NAIA_PREPROCESSING_KEYS",
    "NAIA_RESOLUTION_BUCKETS",
    "NAIA_RESOLUTION_MODES",
    "PROMPT_STUDIO_COLOR_KEYS",
)
