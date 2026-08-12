"""AiO adapter for structured Prompt Data LoRA directives."""

from __future__ import annotations

from ..lora.prompt_syntax import (
    _lora_directives_from_prompt_data,
    _merge_prompt_data_lora_stack,
)
from ..prompt.data import _normalize_prompt_data


def _prepare_aio_prompt_loras(
    prompt_data_value,
    lora_stack,
    *,
    normalize_prompt_data=_normalize_prompt_data,
):
    prompt_data = normalize_prompt_data(prompt_data_value)
    if not _lora_directives_from_prompt_data(prompt_data):
        return prompt_data, lora_stack
    return prompt_data, _merge_prompt_data_lora_stack(lora_stack, prompt_data)


__all__ = ()
