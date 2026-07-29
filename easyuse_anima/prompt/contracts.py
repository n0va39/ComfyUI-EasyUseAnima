"""Internal typed contracts for Prompt Studio feature data."""

from typing import TypedDict


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


__all__ = ()
