"""Wildcard seed domains and after-generate transitions."""

from __future__ import annotations

import random

SEED_CONTROL_FIXED = "fixed"
SEED_CONTROL_RANDOMIZE = "randomize"
SEED_CONTROL_INCREMENT = "increment"
SEED_CONTROL_DECREMENT = "decrement"
SEED_CONTROL_MODES = (
    SEED_CONTROL_FIXED,
    SEED_CONTROL_RANDOMIZE,
    SEED_CONTROL_INCREMENT,
    SEED_CONTROL_DECREMENT,
)

MAX_SEED = 0xFFFFFFFFFFFFFFFF
PUBLIC_MAX_SEED = (1 << 53) - 1

__all__ = (
    "SEED_CONTROL_FIXED",
    "SEED_CONTROL_RANDOMIZE",
    "SEED_CONTROL_INCREMENT",
    "SEED_CONTROL_DECREMENT",
    "SEED_CONTROL_MODES",
    "MAX_SEED",
    "PUBLIC_MAX_SEED",
    "normalize_seed",
    "next_seed",
)


def normalize_seed(value) -> int:
    try:
        seed = int(value)
    except (TypeError, ValueError):
        seed = 0
    return max(0, min(MAX_SEED, seed))


def next_seed(seed, control: str) -> int:
    """Return the next public wildcard seed without breaking legacy inputs.

    Existing workflows may contain uint64 values that JavaScript cannot
    represent exactly. The current generation still consumes that legacy
    value, and ``fixed`` preserves it. Controls that advance the state first
    project the value onto the public JavaScript-safe range so every returned
    non-fixed seed uses the same inclusive range in Python and JavaScript.
    """
    seed = normalize_seed(seed)
    control = str(control or SEED_CONTROL_FIXED).strip()
    if control == SEED_CONTROL_FIXED:
        return seed
    if control == SEED_CONTROL_RANDOMIZE:
        return random.SystemRandom().randrange(0, PUBLIC_MAX_SEED + 1)
    public_seed = min(seed, PUBLIC_MAX_SEED)
    if control == SEED_CONTROL_INCREMENT:
        return 0 if public_seed >= PUBLIC_MAX_SEED else public_seed + 1
    if control == SEED_CONTROL_DECREMENT:
        return PUBLIC_MAX_SEED if public_seed <= 0 else public_seed - 1
    return seed
