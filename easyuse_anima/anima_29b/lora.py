"""Legacy 28-block Anima LoRA adaptation for the 40-block Anima 2.9B model."""

from __future__ import annotations

import logging
import re
from collections.abc import Mapping
from typing import Any

from ..infrastructure.comfy.invocation import _call_with_supported_kwargs
from .architecture import (
    ANIMA_29B_LEGACY_BLOCK_MAP,
    ANIMA_BASE_BLOCK_COUNT,
    _is_anima_29b_model,
)

ANIMA_29B_LORA_LAYOUT_AUTO = "auto"
ANIMA_29B_LORA_LAYOUT_LEGACY = "legacy_28_block"

_ANIMA_FLAT_BLOCK_KEY = re.compile(
    r"^(?P<prefix>lora_unet_{1,2}blocks_)(?P<index>\d+)(?P<suffix>_.+)$"
)
_ANIMA_DOTTED_BLOCK_KEYS = (
    re.compile(
        r"^(?P<prefix>(?:model\.)?diffusion_model\.blocks\.)"
        r"(?P<index>\d+)(?P<suffix>\..+)$"
    ),
    re.compile(r"^(?P<prefix>blocks\.)(?P<index>\d+)(?P<suffix>\..+)$"),
)

logger = logging.getLogger("ComfyUI-EasyUseAnima")


def _anima_lora_block_match(key: str):
    match = _ANIMA_FLAT_BLOCK_KEY.match(key)
    if match is not None:
        return match
    for pattern in _ANIMA_DOTTED_BLOCK_KEYS:
        match = pattern.match(key)
        if match is not None:
            return match
    return None


def _anima_lora_block_indices(state_dict: Mapping[str, Any]) -> set[int]:
    indices: set[int] = set()
    for raw_key in state_dict:
        match = _anima_lora_block_match(str(raw_key))
        if match is not None:
            indices.add(int(match.group("index")))
    return indices


def _remap_legacy_anima_lora_key(key: str) -> str:
    match = _anima_lora_block_match(key)
    if match is None:
        return key
    old_index = int(match.group("index"))
    if old_index < 0 or old_index >= ANIMA_BASE_BLOCK_COUNT:
        return key
    new_index = ANIMA_29B_LEGACY_BLOCK_MAP[old_index]
    prefix = match.group("prefix")
    suffix = match.group("suffix")
    if prefix.startswith("lora_unet_"):
        return f"lora_unet_blocks_{new_index}{suffix}"
    return f"diffusion_model.blocks.{new_index}{suffix}"


def _prepare_anima_29b_lora_state_dict(
    state_dict: Mapping[str, Any],
    source_layout: str = ANIMA_29B_LORA_LAYOUT_AUTO,
) -> tuple[dict[str, Any], int]:
    if source_layout not in {
        ANIMA_29B_LORA_LAYOUT_AUTO,
        ANIMA_29B_LORA_LAYOUT_LEGACY,
    }:
        raise ValueError(f"Unsupported Anima 2.9B LoRA source layout: {source_layout}")

    indices = _anima_lora_block_indices(state_dict)
    if source_layout == ANIMA_29B_LORA_LAYOUT_AUTO and any(
        index >= ANIMA_BASE_BLOCK_COUNT for index in indices
    ):
        return dict(state_dict), 0
    if (
        source_layout == ANIMA_29B_LORA_LAYOUT_AUTO
        and indices
        and indices != set(range(ANIMA_BASE_BLOCK_COUNT))
    ):
        raise RuntimeError(
            "[EasyUseAnima] This Anima 2.9B LoRA layout is ambiguous: it only "
            "contains part of blocks 0-27. Use the dedicated Anima 2.9B legacy "
            "LoRA stack node when the LoRA is known to target original Anima, "
            "or the regular ComfyUI LoRA loader for a native 2.9B LoRA."
        )
    if source_layout == ANIMA_29B_LORA_LAYOUT_LEGACY and any(
        index >= ANIMA_BASE_BLOCK_COUNT for index in indices
    ):
        raise RuntimeError(
            "[EasyUseAnima] This LoRA already contains Anima 2.9B block indices. "
            "Apply it with the regular ComfyUI LoRA loader instead."
        )

    remapped: dict[str, Any] = {}
    remapped_count = 0
    for raw_key, value in state_dict.items():
        key = str(raw_key)
        new_key = _remap_legacy_anima_lora_key(key)
        remapped[new_key] = value
        if new_key != key:
            remapped_count += 1
    return remapped, remapped_count


def _load_lora_file(lora_name: str):
    import folder_paths  # type: ignore
    from comfy import utils as comfy_utils  # type: ignore

    lora_path = folder_paths.get_full_path_or_raise("loras", lora_name)
    loaded = _call_with_supported_kwargs(
        comfy_utils.load_torch_file,
        (lora_path,),
        {"safe_load": True, "return_metadata": True},
        "ComfyUI load_torch_file",
    )
    if isinstance(loaded, tuple) and len(loaded) == 2:
        state_dict, metadata = loaded
    else:
        state_dict, metadata = loaded, None
    if not isinstance(state_dict, Mapping):
        raise RuntimeError(
            f"[EasyUseAnima] LoRA file did not contain a state dictionary: {lora_name}"
        )
    return state_dict, metadata


def _apply_anima_29b_lora_stack(
    model,
    clip,
    entries,
    *,
    source_layout: str = ANIMA_29B_LORA_LAYOUT_AUTO,
):
    if not _is_anima_29b_model(model):
        raise RuntimeError(
            "[EasyUseAnima] Anima 2.9B LoRA conversion requires a 40-block "
            "Anima MODEL."
        )

    active_entries = [
        (str(name), float(model_strength), float(clip_strength))
        for name, model_strength, clip_strength in entries
        if model_strength != 0 or clip_strength != 0
    ]
    if not active_entries:
        return model, clip, []

    from comfy import sd as comfy_sd  # type: ignore

    patched_model = model
    patched_clip = clip
    applied: list[dict[str, Any]] = []
    for name, model_strength, clip_strength in active_entries:
        state_dict, metadata = _load_lora_file(name)
        converted, remapped_count = _prepare_anima_29b_lora_state_dict(
            state_dict,
            source_layout,
        )
        result = _call_with_supported_kwargs(
            comfy_sd.load_lora_for_models,
            (
                patched_model,
                patched_clip,
                converted,
                model_strength,
                clip_strength,
            ),
            {"lora_metadata": metadata},
            "ComfyUI load_lora_for_models",
        )
        if not isinstance(result, (list, tuple)) or len(result) < 2:
            raise RuntimeError(
                "[EasyUseAnima] ComfyUI LoRA loader returned no MODEL/CLIP pair."
            )
        patched_model, patched_clip = result[0], result[1]
        if remapped_count:
            logger.info(
                "[EasyUseAnima] Anima 2.9B remapped %d legacy LoRA keys for %s.",
                remapped_count,
                name,
            )
        applied.append(
            {
                "name": name,
                "strength_model": model_strength,
                "strength_clip": clip_strength,
            }
        )
    return patched_model, patched_clip, applied


def _apply_anima_29b_aio_lora_stack(model, clip, entries):
    if not _is_anima_29b_model(model):
        return None
    return _apply_anima_29b_lora_stack(
        model,
        clip,
        entries,
        source_layout=ANIMA_29B_LORA_LAYOUT_AUTO,
    )


__all__ = ()
