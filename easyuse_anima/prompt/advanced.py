"""Advanced Prompt Studio field and prompt-data service facade."""

from __future__ import annotations

from typing import Any, TypeVar, cast

from ..common.values import _as_bool
from ..naia.resolution import (
    NAIA_ADVANCED_RESOLUTION_BUCKET,
    _normalize_resolution_bucket,
)
from ..settings.service import resolve_metadata_filter_words
from ..translation.markers import has_prompt_translation_markers
from ..wildcard.expansion import has_wildcard_syntax
from ..wildcard.mode import normalize_prompt_studio_wildcard_mode
from ..wildcard.seed import normalize_seed as normalize_seed
from ..wildcard.service import expand_wildcard_texts
from .advanced_builder import (
    PROMPT_STUDIO_ADVANCED_RETURN_NAMES as PROMPT_STUDIO_ADVANCED_RETURN_NAMES,
)
from .advanced_builder import (
    PROMPT_STUDIO_ADVANCED_RETURN_TYPES as PROMPT_STUDIO_ADVANCED_RETURN_TYPES,
)
from .advanced_builder import (
    PROMPT_STUDIO_WILDCARD_MODE_LABELS as PROMPT_STUDIO_WILDCARD_MODE_LABELS,
)
from .advanced_builder import (
    SEED_CONTROL_FIXED,
    SEED_CONTROL_INCREMENT,
    SEED_CONTROL_RANDOMIZE,
)
from .advanced_builder import (
    _advanced_prompt_data_fields as _advanced_prompt_data_fields,
)
from .advanced_builder import (
    _build_advanced_prompt_data as _build_advanced_prompt_data,
)
from .advanced_fields import (
    ADVANCED_FIELD_LABELS as ADVANCED_FIELD_LABELS,
)
from .advanced_fields import (
    ADVANCED_FIELD_PANES as ADVANCED_FIELD_PANES,
)
from .advanced_fields import (
    ADVANCED_FIELD_TYPES as ADVANCED_FIELD_TYPES,
)
from .advanced_fields import (
    ADVANCED_FIELDS_WORKFLOW_PROPERTY as ADVANCED_FIELDS_WORKFLOW_PROPERTY,
)
from .advanced_fields import (
    _advanced_artist_field_prompt as _advanced_artist_field_prompt,
)
from .advanced_fields import (
    _advanced_default_fields as _advanced_default_fields,
)
from .advanced_fields import (
    _advanced_enabled_pane_fields,
    _advanced_pane_parts,
    _correct_advanced_field_sequence,
    _normalize_advanced_fields,
)
from .advanced_fields import (
    _advanced_field_input_values as _advanced_field_input_values,
)
from .advanced_fields import (
    _advanced_field_socket_name as _advanced_field_socket_name,
)
from .advanced_fields import (
    _advanced_fields_json as _advanced_fields_json,
)
from .advanced_fields import (
    _advanced_fields_with_artist_override as _advanced_fields_with_artist_override,
)
from .advanced_fields import (
    _advanced_prompt_with_artist_override as _advanced_prompt_with_artist_override,
)
from .advanced_fields import (
    _apply_advanced_field_inputs as _apply_advanced_field_inputs,
)
from .advanced_fields import (
    _as_advanced_height as _as_advanced_height,
)
from .advanced_fields import (
    _clone_advanced_fields as _clone_advanced_fields,
)
from .artist_mix_primitives import (
    ARTIST_MIX_DEFAULT_CLUSTER_COUNT as ARTIST_MIX_DEFAULT_CLUSTER_COUNT,
)
from .artist_mix_primitives import (
    ARTIST_MIX_DEFAULT_DOMINANT_ISOLATION as ARTIST_MIX_DEFAULT_DOMINANT_ISOLATION,
)
from .artist_mix_primitives import (
    ARTIST_MIX_DEFAULT_DOMINANT_THRESHOLD as ARTIST_MIX_DEFAULT_DOMINANT_THRESHOLD,
)
from .artist_mix_primitives import (
    ARTIST_MIX_DEFAULT_EXACT_TOP_K as ARTIST_MIX_DEFAULT_EXACT_TOP_K,
)
from .artist_mix_primitives import (
    ARTIST_MIX_DEFAULT_RMS_SCALE_CAP as ARTIST_MIX_DEFAULT_RMS_SCALE_CAP,
)
from .artist_mix_primitives import (
    ARTIST_MIX_DEFAULT_START_PERCENT as ARTIST_MIX_DEFAULT_START_PERCENT,
)
from .artist_mix_primitives import (
    ARTIST_MIX_DEFAULT_STRENGTH_SCALE as ARTIST_MIX_DEFAULT_STRENGTH_SCALE,
)
from .artist_mix_primitives import (
    ARTIST_MIX_DEFAULT_STYLE_GAIN as ARTIST_MIX_DEFAULT_STYLE_GAIN,
)
from .artist_mix_primitives import (
    ARTIST_MIX_MODE_OFF as ARTIST_MIX_MODE_OFF,
)
from .artist_mix_primitives import (
    ARTIST_MIX_MODE_PROMPT as ARTIST_MIX_MODE_PROMPT,
)
from .artist_mix_primitives import (
    _artist_mix_inline_prompt as _artist_mix_inline_prompt,
)
from .artist_mix_primitives import (
    _artist_tags_from_prompt as _artist_tags_from_prompt,
)
from .artist_mix_primitives import (
    _bounded_artist_mix_float as _bounded_artist_mix_float,
)
from .artist_mix_primitives import (
    _bounded_artist_mix_int as _bounded_artist_mix_int,
)
from .artist_mix_primitives import (
    _join_artist_mix_source_prompts as _join_artist_mix_source_prompts,
)
from .artist_mix_primitives import (
    _normalize_artist_mix_mode as _normalize_artist_mix_mode,
)
from .artist_mix_primitives import (
    _parse_artist_mix_items as _parse_artist_mix_items,
)
from .contracts import AdvancedField, PromptField
from .correction import _translate_prompt_text
from .fields import (
    DEFAULT_QUALITY_TAGS,
    DEFAULT_TRAILING_QUALITY_TAGS,
    _filter_metadata_prompt,
    _join_prompt_tokens,
)

WILDCARD_MODE_FIXED = "fixed"
PROMPT_STUDIO_WILDCARD_SEED_CONTROL_ALIASES = {
    "fixed": SEED_CONTROL_FIXED,
    "고정": SEED_CONTROL_FIXED,
    "random": SEED_CONTROL_RANDOMIZE,
    "randomize": SEED_CONTROL_RANDOMIZE,
    "매번 랜덤": SEED_CONTROL_RANDOMIZE,
    "increase": SEED_CONTROL_INCREMENT,
    "increment": SEED_CONTROL_INCREMENT,
    "증가": SEED_CONTROL_INCREMENT,
}
PROMPT_STUDIO_LEGACY_FIXED_WILDCARD_MODES = {
    WILDCARD_MODE_FIXED,
    "고정",
    "reproduce",
    "재현",
}
EXTEND_PROMPT_SLOT_SPECS = [
    ("quality_tags_1", "positive", "quality", "Quality Tags 1", DEFAULT_QUALITY_TAGS, 72),
    ("quality_tags_2", "positive", "quality", "Quality Tags 2", "", 72),
    ("naia_prompt_3", "positive", "general", "NAIA Prompt 3", "", 150),
    ("general_tags_4", "positive", "general", "General Tags 4", "", 120),
    ("general_tags_5", "positive", "general", "General Tags 5", "", 120),
    ("general_tags_6", "positive", "general", "General Tags 6", "", 120),
    ("general_tags_7", "positive", "general", "General Tags 7", "", 120),
    ("general_tags_8", "positive", "general", "General Tags 8", "", 120),
    ("general_tags_9", "positive", "general", "General Tags 9", "", 120),
    (
        "trailing_tags_10",
        "positive",
        "general",
        "Trailing Quality Tags 10",
        DEFAULT_TRAILING_QUALITY_TAGS,
        72,
    ),
    ("trailing_tags_11", "positive", "general", "Trailing Quality Tags 11", "", 72),
    ("negative_prompt_1", "negative", "quality", "Negative Prompt 1", "", 120),
    ("negative_prompt_2", "negative", "quality", "Negative Prompt 2", "", 120),
    ("negative_prompt_3", "negative", "general", "Negative Prompt 3", "", 120),
    ("negative_prompt_4", "negative", "general", "Negative Prompt 4", "", 120),
]

_PromptFieldT = TypeVar("_PromptFieldT", bound=PromptField)


def _normalize_prompt_studio_wildcard_seed_control(
    value: Any,
    wildcard_mode: Any = None,
) -> str:
    loaded_mode = str(wildcard_mode or "").strip().lower()
    if loaded_mode in PROMPT_STUDIO_LEGACY_FIXED_WILDCARD_MODES:
        return SEED_CONTROL_FIXED
    return PROMPT_STUDIO_WILDCARD_SEED_CONTROL_ALIASES.get(
        str(value or "").strip().lower(),
        SEED_CONTROL_FIXED,
    )


def _translate_prompt_fields(fields: list[_PromptFieldT]) -> list[_PromptFieldT]:
    translated: list[_PromptFieldT] = []
    for field in fields:
        item = cast(_PromptFieldT, dict(field))
        text = str(item.get("text") or "")
        if text and has_prompt_translation_markers(text):
            item["text"] = _translate_prompt_text(text)
        translated.append(item)
    return translated


def _advanced_enabled_naia_panes(fields: list[AdvancedField]) -> set[str]:
    return {
        str(field.get("pane") or "positive")
        for field in fields
        if field.get("type") == "naia" and field.get("enabled") is not False
    }


def _advanced_has_enabled_naia(fields: list[AdvancedField]) -> bool:
    return bool(_advanced_enabled_naia_panes(fields))


def _advanced_uses_naia_resolution(bucket) -> bool:
    return _normalize_resolution_bucket(bucket) == NAIA_ADVANCED_RESOLUTION_BUCKET


def _set_naia_field_text(
    fields: list[AdvancedField],
    pane: str,
    prompt: str,
) -> list[AdvancedField]:
    normalized = _normalize_advanced_fields(fields)
    for field in normalized:
        if field["pane"] == pane and field["type"] == "naia":
            field["text"] = prompt
            field["enabled"] = True
            return normalized
    return normalized


def _advanced_naia_field_updates(
    fields: list[AdvancedField],
    prompts_by_pane: dict[str, str],
) -> dict[str, str]:
    updates: dict[str, str] = {}
    for field in fields:
        pane = str(field.get("pane") or "positive")
        field_id = str(field.get("id") or "")
        if (
            field_id
            and field.get("type") == "naia"
            and field.get("enabled") is not False
            and pane in prompts_by_pane
        ):
            updates[field_id] = str(prompts_by_pane[pane])
    return updates


def _build_advanced_prompts(
    fields: list[AdvancedField],
    use_anima_mod_guidance: bool,
    use_negative_anima_mod_guidance: bool,
    pin_trigger_tags_to_front: bool,
) -> tuple[str, str, str, str, bool, bool, str, str]:
    use_amg = _as_bool(use_anima_mod_guidance, False)
    use_negative_amg = _as_bool(use_negative_anima_mod_guidance, False)
    force_pin_triggers = _as_bool(pin_trigger_tags_to_front, False)
    positive = _advanced_pane_parts(fields, "positive")
    negative = _advanced_pane_parts(fields, "negative")
    positive_fields = _advanced_enabled_pane_fields(fields, "positive")
    negative_fields = _advanced_enabled_pane_fields(fields, "negative")

    quality_prompt = _join_prompt_tokens(*positive["quality"])
    artist_prompt = _join_prompt_tokens(*positive["artist"])
    regular_prompt = _correct_advanced_field_sequence(
        positive_fields,
        include_quality=True,
        artist_overrides=artist_prompt,
        force_pin_triggers=force_pin_triggers,
    )
    amg_prompt = _correct_advanced_field_sequence(
        positive_fields,
        include_quality=False,
        artist_overrides=artist_prompt,
        force_pin_triggers=force_pin_triggers,
    )
    metadata_prompt = regular_prompt

    negative_quality_prompt = _join_prompt_tokens(*negative["quality"])
    negative_artist_prompt = _join_prompt_tokens(*negative["artist"])
    negative_regular_prompt = _correct_advanced_field_sequence(
        negative_fields,
        include_quality=True,
        artist_overrides=negative_artist_prompt,
    )
    negative_amg_prompt = _correct_advanced_field_sequence(
        negative_fields,
        include_quality=False,
        artist_overrides=negative_artist_prompt,
    )

    filter_words = resolve_metadata_filter_words()
    metadata_prompt = _filter_metadata_prompt(metadata_prompt, filter_words)
    metadata_negative_prompt = _filter_metadata_prompt(negative_regular_prompt, filter_words)
    output_prompt = amg_prompt if use_amg else regular_prompt
    output_negative_prompt = negative_amg_prompt if use_negative_amg else negative_regular_prompt
    return (
        output_prompt,
        output_negative_prompt,
        quality_prompt,
        negative_quality_prompt,
        use_amg,
        use_negative_amg,
        metadata_prompt,
        metadata_negative_prompt,
    )


def _expand_advanced_wildcard_fields(
    fields: list[_PromptFieldT],
    seed: int,
    mode: str,
) -> tuple[list[_PromptFieldT], dict[str, Any]]:
    mode_key = normalize_prompt_studio_wildcard_mode(mode)
    expanded_fields = [cast(_PromptFieldT, dict(field)) for field in fields]

    wildcard_fields = []
    wildcard_texts = []
    for field in expanded_fields:
        text = str(field.get("text") or "")
        if has_wildcard_syntax(text):
            wildcard_fields.append(field)
            wildcard_texts.append(text)

    expansions = expand_wildcard_texts(
        wildcard_texts,
        seed=seed,
        mode=mode_key,
    )
    changed = False
    used_keys: list[str] = []
    missing_keys: list[str] = []
    for field, text, result in zip(
        wildcard_fields,
        wildcard_texts,
        expansions,
        strict=True,
    ):
        if result.text != text:
            field["text"] = result.text
            changed = True
        for key in result.used_keys:
            if key not in used_keys:
                used_keys.append(key)
        for key in result.missing_keys:
            if key not in missing_keys:
                missing_keys.append(key)

    return expanded_fields, {
        "changed": changed,
        "used_keys": tuple(used_keys),
        "missing_keys": tuple(missing_keys),
    }


__all__ = ()
