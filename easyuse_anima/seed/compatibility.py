"""Compatibility consumer for the browser-reserved Prompt Studio next seed."""

from __future__ import annotations

import json

from ..common.values import _single_value


WILDCARD_RESERVED_NEXT_SEED_INPUT = "easyuse_anima_reserved_wildcard_next_seed"
WILDCARD_QUEUE_MAX_SAFE_SEED = (1 << 53) - 1


def _wildcard_engine_module():
    try:
        from ... import wildcard_engine as module
    except ImportError:
        import wildcard_engine as module

    return module


def _consume_reserved_wildcard_next_seed(
    reservation_inputs,
    workflow_prompt,
    node_id,
    current_seed,
    wildcard_mode,
    seed_control,
):
    if not isinstance(reservation_inputs, dict):
        return None
    raw_reservation = _single_value(
        reservation_inputs.pop(WILDCARD_RESERVED_NEXT_SEED_INPUT, None)
    )
    node_id = _single_value(node_id)
    if isinstance(workflow_prompt, dict) and node_id is not None:
        prompt_node = workflow_prompt.get(str(node_id))
        prompt_inputs = prompt_node.get("inputs") if isinstance(prompt_node, dict) else None
        if isinstance(prompt_inputs, dict):
            prompt_inputs.pop(WILDCARD_RESERVED_NEXT_SEED_INPUT, None)
    if not isinstance(raw_reservation, str):
        return None
    try:
        reservation = json.loads(raw_reservation)
    except (TypeError, ValueError, json.JSONDecodeError):
        return None
    if (
        not isinstance(reservation, dict)
        or isinstance(reservation.get("version"), bool)
        or reservation.get("version") != 1
    ):
        return None
    required_keys = {"current_seed", "next_seed", "mode", "control"}
    if not required_keys.issubset(reservation):
        return None

    def reserved_seed(value):
        if isinstance(value, bool) or not isinstance(value, int):
            return None
        return value if 0 <= value <= WILDCARD_QUEUE_MAX_SAFE_SEED else None

    reservation_current_seed = reserved_seed(reservation.get("current_seed"))
    reservation_next_seed = reserved_seed(reservation.get("next_seed"))
    if reservation_current_seed is None or reservation_next_seed is None:
        return None

    wildcard_engine = _wildcard_engine_module()
    reservation_mode = str(reservation.get("mode") or "")
    if reservation_mode not in {
        wildcard_engine.WILDCARD_MODE_POPULATE,
        wildcard_engine.WILDCARD_MODE_FIXED,
        wildcard_engine.WILDCARD_MODE_SEQUENTIAL,
    }:
        return None
    reservation_control = str(reservation.get("control") or "")
    if reservation_control not in set(wildcard_engine.SEED_CONTROL_MODES):
        return None
    if reservation_current_seed != wildcard_engine.normalize_seed(current_seed):
        return None
    if reservation_mode != wildcard_engine.normalize_wildcard_mode(wildcard_mode):
        return None
    if reservation_control != str(
        seed_control or wildcard_engine.SEED_CONTROL_FIXED
    ):
        return None
    if reservation_control == wildcard_engine.SEED_CONTROL_RANDOMIZE:
        return reservation_next_seed
    if reservation_control == wildcard_engine.SEED_CONTROL_FIXED:
        expected_next_seed = reservation_current_seed
    elif reservation_control == wildcard_engine.SEED_CONTROL_INCREMENT:
        expected_next_seed = (
            0
            if reservation_current_seed >= WILDCARD_QUEUE_MAX_SAFE_SEED
            else reservation_current_seed + 1
        )
    elif reservation_control == wildcard_engine.SEED_CONTROL_DECREMENT:
        expected_next_seed = (
            WILDCARD_QUEUE_MAX_SAFE_SEED
            if reservation_current_seed <= 0
            else reservation_current_seed - 1
        )
    else:
        return None
    return reservation_next_seed if reservation_next_seed == expected_next_seed else None


__all__ = ()
