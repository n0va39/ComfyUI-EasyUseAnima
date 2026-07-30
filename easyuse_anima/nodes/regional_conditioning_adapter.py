"""Execution adapter for Regional Prompt Studio conditioning."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from ..common.values import _as_bool, _as_float
from ..prompt.regional import (
    _conditioning_set_values,
    _normalize_mask_ids,
    _parse_json_object,
    _regional_mask_bounds_area,
    _regional_payload_canvas,
    _regional_union_mask_for_ids,
)

_EncodeWithComfyClip = Callable[..., Any]


def _encode_regional_conditioning(
    regional_prompt_data: str | dict,
    clip: Any,
    mask_strength: float,
    set_cond_area: str,
    *,
    encode_with_comfy_clip: _EncodeWithComfyClip,
):
    payload = _parse_json_object(regional_prompt_data)
    width, height = _regional_payload_canvas(payload)
    positive_prompt = str(payload.get("global_prompt") or payload.get("positive_prompt") or "")
    negative_prompt = str(payload.get("negative_prompt") or "")

    positive = list(encode_with_comfy_clip(clip, positive_prompt))
    negative = encode_with_comfy_clip(clip, negative_prompt)

    if _as_bool(payload.get("regional_enabled"), False):
        use_mask_bounds = str(set_cond_area or "mask bounds") != "default"
        mask_prompts_value = payload.get("mask_prompts")
        mask_prompts = mask_prompts_value if isinstance(mask_prompts_value, list) else []
        for entry in mask_prompts:
            if not isinstance(entry, dict):
                continue
            valid_mask_ids = _normalize_mask_ids(entry.get("valid_mask_ids") or entry.get("mask_ids"))
            prompt = str(entry.get("prompt") or entry.get("text") or "").strip()
            if not valid_mask_ids or not prompt:
                continue
            mask = _regional_union_mask_for_ids(payload, valid_mask_ids, width, height)
            regional_conditioning = encode_with_comfy_clip(clip, prompt)
            conditioning_values = {
                "mask": mask,
                "set_area_to_bounds": False,
                "mask_strength": _as_float(mask_strength, 1.0),
                "easyuse_anima_region": {
                    "field_id": str(entry.get("field_id") or ""),
                    "mask_ids": valid_mask_ids,
                },
            }
            if use_mask_bounds:
                area = _regional_mask_bounds_area(mask, width, height)
                if area is not None:
                    conditioning_values["area"] = area
            positive.extend(_conditioning_set_values(regional_conditioning, conditioning_values))

    return (positive, negative)


__all__ = ()
