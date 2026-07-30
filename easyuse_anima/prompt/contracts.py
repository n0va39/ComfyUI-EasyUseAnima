"""Internal typed contracts for Prompt Studio feature data."""

from collections.abc import Mapping
from typing import TypeAlias, TypedDict

JsonValue: TypeAlias = (
    None
    | bool
    | int
    | float
    | str
    | list["JsonValue"]
    | dict[str, "JsonValue"]
)


class PromptField(TypedDict):
    """Fields shared by Advanced and Regional Prompt Studio flows."""

    id: str
    pane: str
    type: str
    label: str
    text: str
    height: int
    enabled: bool


class AdvancedField(PromptField, total=False):
    """Advanced field preserving the legacy Extend adapter's omitted pin."""

    pin: bool


class _RegionalFieldRequired(PromptField):
    mask_ids: list[int]


class RegionalField(_RegionalFieldRequired, total=False):
    """Regional field preserving the legacy default's omitted optional flags."""

    pin: bool
    collapsed: bool


class PromptDataOutputs(TypedDict):
    positive_prompt: str
    negative_prompt: str
    anima_mod_guidance_quality_tags: str
    anima_mod_guidance_negative_prompt: str
    use_anima_mod_guidance: bool
    use_negative_anima_mod_guidance: bool
    metadata_prompt: str
    metadata_negative_prompt: str
    width: int
    height: int


class PromptDataModGuidance(TypedDict):
    enabled: bool
    negative_enabled: bool
    quality_tags: str
    negative_prompt: str


class PromptDataAnimaModGuidance(TypedDict):
    use_positive: bool
    use_negative: bool
    quality_tags: str
    negative_prompt: str


class PromptDataArtistTag(TypedDict):
    tag: str
    weight: float
    source: str
    grouped: bool


class PromptDataArtist(TypedDict):
    source: str
    handling: str
    conditioning_mode: str
    include_in_positive: bool
    text: str
    weighted_text: str
    tags: list[PromptDataArtistTag]
    positive_prompt: str
    negative_prompt: str
    positive_prompt_without_artist: str
    negative_prompt_without_artist: str
    positive_count_hint: int
    negative_count_hint: int


class PromptDataArtistMix(TypedDict):
    enabled: bool
    mode: str
    base_source: str
    base_prompt: str
    start_percent: float
    strength_scale: float
    style_gain: float
    rms_scale_cap: float
    exact_top_k: int
    cluster_count: int
    dominant_isolation: bool
    dominant_threshold: float
    artist_prompt: str
    artist_count_hint: int


class PromptDataResolution(TypedDict):
    width: int
    height: int
    bucket: str
    size: str
    custom_width: int
    custom_height: int


class PromptDataNaia(TypedDict):
    use_naia: bool
    consume_on_queue: bool
    resolution_bucket: str


class PromptDataWildcard(TypedDict):
    mode: str
    seed: int
    seed_after_generate: str
    next_seed: int | None
    used_keys: list[str]
    missing_keys: list[str]


class PromptDataCompatibility(TypedDict):
    return_names: list[str]
    return_types: list[str]


class PromptData(TypedDict):
    schema: str
    version: int
    type: str
    source: str
    parameters: dict[str, JsonValue]
    prompt: str
    positive_prompt: str
    global_prompt: str
    positive_without_artist_section: str
    negative_prompt: str
    negative_without_artist_section: str
    metadata_prompt: str
    metadata_prompt_without_artist: str
    metadata_negative_prompt: str
    width: int
    height: int
    pin_trigger_tags_to_front: bool
    outputs: PromptDataOutputs
    mod_guidance: PromptDataModGuidance
    anima_mod_guidance: PromptDataAnimaModGuidance
    artist: PromptDataArtist
    artist_mix: PromptDataArtistMix
    resolution: PromptDataResolution
    naia: PromptDataNaia
    fields: list[AdvancedField]
    saved_fields: list[AdvancedField]
    field_inputs: dict[str, str]
    wildcard: PromptDataWildcard
    compatibility: PromptDataCompatibility


PromptDataRead: TypeAlias = Mapping[str, object]
PromptDataCompatResult: TypeAlias = tuple[
    str,
    str,
    str,
    str,
    bool,
    bool,
    str,
    str,
    int,
    int,
]


__all__ = ()
