"""Immutable wildcard models and expansion budget contracts."""

from __future__ import annotations

import math
from dataclasses import dataclass

# Defaults stop exponential inputs well before they become memory hazards while
# leaving ample room for ordinary nested wildcard libraries. The old depth is
# retained as a hard ceiling for callers that provide a custom budget.
MAX_EXPANSION_DEPTH = 100
REPLACE_DEPTH = MAX_EXPANSION_DEPTH
DEFAULT_MAX_EXPANSION_DEPTH = 32
DEFAULT_MAX_EXPANSION_REPLACEMENTS = 4096
DEFAULT_MAX_EXPANSION_OUTPUT_CHARS = 256 * 1024
DEFAULT_MAX_EXPANSION_GROWTH_PER_PASS = 8.0
MAX_EXPANSION_REPLACEMENTS = 65536
MAX_EXPANSION_OUTPUT_CHARS = 1024 * 1024
MAX_EXPANSION_GROWTH_PER_PASS = 32.0

__all__ = (
    "MAX_EXPANSION_DEPTH",
    "REPLACE_DEPTH",
    "DEFAULT_MAX_EXPANSION_DEPTH",
    "DEFAULT_MAX_EXPANSION_REPLACEMENTS",
    "DEFAULT_MAX_EXPANSION_OUTPUT_CHARS",
    "DEFAULT_MAX_EXPANSION_GROWTH_PER_PASS",
    "MAX_EXPANSION_REPLACEMENTS",
    "MAX_EXPANSION_OUTPUT_CHARS",
    "MAX_EXPANSION_GROWTH_PER_PASS",
    "WildcardOption",
    "WildcardExpansionBudget",
    "WildcardExpansionResult",
)


@dataclass(frozen=True)
class WildcardOption:
    text: str
    weight: float = 1.0


def _bounded_int(value, default: int, minimum: int, maximum: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError, OverflowError):
        parsed = default
    return max(minimum, min(maximum, parsed))


def _bounded_float(value, default: float, minimum: float, maximum: float) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError, OverflowError):
        parsed = default
    if not math.isfinite(parsed):
        parsed = default
    return max(minimum, min(maximum, parsed))


@dataclass(frozen=True)
class WildcardExpansionBudget:
    max_depth: int = DEFAULT_MAX_EXPANSION_DEPTH
    max_replacements: int = DEFAULT_MAX_EXPANSION_REPLACEMENTS
    max_output_chars: int = DEFAULT_MAX_EXPANSION_OUTPUT_CHARS
    max_growth_per_pass: float = DEFAULT_MAX_EXPANSION_GROWTH_PER_PASS

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "max_depth",
            _bounded_int(
                self.max_depth,
                DEFAULT_MAX_EXPANSION_DEPTH,
                0,
                MAX_EXPANSION_DEPTH,
            ),
        )
        object.__setattr__(
            self,
            "max_replacements",
            _bounded_int(
                self.max_replacements,
                DEFAULT_MAX_EXPANSION_REPLACEMENTS,
                0,
                MAX_EXPANSION_REPLACEMENTS,
            ),
        )
        object.__setattr__(
            self,
            "max_output_chars",
            _bounded_int(
                self.max_output_chars,
                DEFAULT_MAX_EXPANSION_OUTPUT_CHARS,
                1,
                MAX_EXPANSION_OUTPUT_CHARS,
            ),
        )
        object.__setattr__(
            self,
            "max_growth_per_pass",
            _bounded_float(
                self.max_growth_per_pass,
                DEFAULT_MAX_EXPANSION_GROWTH_PER_PASS,
                1.0,
                MAX_EXPANSION_GROWTH_PER_PASS,
            ),
        )


@dataclass(frozen=True)
class WildcardExpansionResult:
    text: str
    changed: bool
    used_keys: tuple[str, ...] = ()
    missing_keys: tuple[str, ...] = ()
    replacement_count: int = 0
    limit_reason: str | None = None
