"""Wildcard mode values and normalization contracts."""

from __future__ import annotations

WILDCARD_MODE_POPULATE = "populate"
WILDCARD_MODE_FIXED = "fixed"
WILDCARD_MODE_SEQUENTIAL = "sequential"
WILDCARD_MODE_REPRODUCE = "reproduce"
WILDCARD_MODES = (
    WILDCARD_MODE_POPULATE,
    WILDCARD_MODE_FIXED,
    WILDCARD_MODE_SEQUENTIAL,
    WILDCARD_MODE_REPRODUCE,
)
WILDCARD_MODE_LABELS = (
    "일반",
    "고정",
    "순차",
    "재현",
)
PROMPT_STUDIO_WILDCARD_MODE_LABELS = ("일반", "순차")
WILDCARD_MODE_ALIASES = {
    WILDCARD_MODE_POPULATE: WILDCARD_MODE_POPULATE,
    "normal": WILDCARD_MODE_POPULATE,
    "fill": WILDCARD_MODE_POPULATE,
    "일반": WILDCARD_MODE_POPULATE,
    "일반 채우기": WILDCARD_MODE_POPULATE,
    WILDCARD_MODE_FIXED: WILDCARD_MODE_FIXED,
    "고정": WILDCARD_MODE_FIXED,
    WILDCARD_MODE_SEQUENTIAL: WILDCARD_MODE_SEQUENTIAL,
    "순차": WILDCARD_MODE_SEQUENTIAL,
    WILDCARD_MODE_REPRODUCE: WILDCARD_MODE_REPRODUCE,
    "재현": WILDCARD_MODE_REPRODUCE,
}


def normalize_wildcard_mode(mode: str) -> str:
    value = str(mode or "").strip()
    return WILDCARD_MODE_ALIASES.get(value, WILDCARD_MODE_POPULATE)


def normalize_prompt_studio_wildcard_mode(mode: str) -> str:
    """Normalize Prompt Studio to its two source-expansion modes."""
    return (
        WILDCARD_MODE_SEQUENTIAL
        if normalize_wildcard_mode(mode) == WILDCARD_MODE_SEQUENTIAL
        else WILDCARD_MODE_POPULATE
    )


__all__ = (
    "WILDCARD_MODE_POPULATE",
    "WILDCARD_MODE_FIXED",
    "WILDCARD_MODE_SEQUENTIAL",
    "WILDCARD_MODE_REPRODUCE",
    "WILDCARD_MODES",
    "WILDCARD_MODE_LABELS",
    "PROMPT_STUDIO_WILDCARD_MODE_LABELS",
    "WILDCARD_MODE_ALIASES",
    "normalize_wildcard_mode",
    "normalize_prompt_studio_wildcard_mode",
)
