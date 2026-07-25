"""LoRA path, metadata, trigger-word, and missing-model services."""

from __future__ import annotations

import json
import logging
import os

_TRIGGER_WORD_KEYS = ("trainedWords", "trained_words", "trigger_words", "activation_text")


class _RuntimeLoggerProxy:
    def __init__(self, resolve_logger):
        self._resolve_logger = resolve_logger

    def __getattr__(self, name):
        return getattr(self._resolve_logger(), name)


def _resolve_logger():
    return logging.getLogger("ComfyUI-EasyUseAnima")


logger = _RuntimeLoggerProxy(lambda: _resolve_logger())


def _prompt_tokens(*args, **kwargs):
    from ..prompt.fields import _prompt_tokens as prompt_tokens

    return prompt_tokens(*args, **kwargs)


def _apply_lora_syntax_format(name: str) -> str:
    try:
        from py.nodes.utils import apply_lora_syntax_format  # type: ignore

        return str(apply_lora_syntax_format(name))
    except Exception:
        base_name = str(name).replace("\\", "/").rstrip("/").split("/")[-1]
        return os.path.splitext(base_name)[0]


def _fallback_lora_path(lora_name: str) -> str:
    try:
        import folder_paths  # type: ignore

        for candidate in (
            lora_name,
            f"{lora_name}.safetensors",
            f"{lora_name}.pt",
            f"{lora_name}.ckpt",
        ):
            path = folder_paths.get_full_path("loras", candidate)
            if path:
                return path
    except Exception:
        pass
    return lora_name


def _lora_stack_name(lora_name: str) -> str:
    value = str(lora_name or "").strip()
    if not value:
        return value

    try:
        import folder_paths  # type: ignore

        absolute_value = os.path.abspath(value)
        for root in folder_paths.get_folder_paths("loras"):
            absolute_root = os.path.abspath(root)
            try:
                relative = os.path.relpath(absolute_value, absolute_root)
            except ValueError:
                continue
            if relative == "." or relative.startswith(f"..{os.sep}") or relative == "..":
                continue
            return relative.replace("/", os.sep)
    except Exception:
        pass

    normalized = value.replace("\\", "/")
    marker = "/models/loras/"
    marker_index = normalized.casefold().rfind(marker)
    if marker_index >= 0:
        normalized = normalized[marker_index + len(marker):]
    return normalized.replace("/", os.sep)


def _dedupe_text_values(values) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        text = str(value or "").strip()
        if not text:
            continue
        key = text.casefold()
        if key in seen:
            continue
        seen.add(key)
        result.append(text)
    return result


def _trigger_words_from_value(value) -> list[str]:
    if isinstance(value, str):
        return _dedupe_text_values(_prompt_tokens(value))
    if isinstance(value, dict):
        for key in ("word", "name", "tag", "text"):
            if key in value:
                return _trigger_words_from_value(value.get(key))
        return []
    if isinstance(value, (list, tuple, set)):
        words: list[str] = []
        for item in value:
            words.extend(_trigger_words_from_value(item))
        return _dedupe_text_values(words)
    return []


def _metadata_json_paths_for_lora(lora_path: str) -> list[str]:
    path = str(lora_path or "").strip()
    if not path:
        return []
    base, _ext = os.path.splitext(path)
    candidates = [f"{base}.metadata.json", f"{path}.metadata.json"]
    return _dedupe_text_values(candidates)


def _load_lora_manager_metadata(lora_path: str) -> dict:
    for metadata_path in _metadata_json_paths_for_lora(lora_path):
        if not os.path.isfile(metadata_path):
            continue
        try:
            with open(metadata_path, "r", encoding="utf-8") as handle:
                data = json.load(handle)
        except (OSError, json.JSONDecodeError) as exc:
            logger.warning("[EasyUse Anima] failed to read LoRA metadata JSON %s: %s", metadata_path, exc)
            continue
        if isinstance(data, dict):
            return data
    return {}


def _lora_manager_trigger_words_from_metadata(metadata: dict) -> list[str]:
    if not isinstance(metadata, dict):
        return []

    words: list[str] = []
    for key in _TRIGGER_WORD_KEYS:
        words.extend(_trigger_words_from_value(metadata.get(key)))

    civitai = metadata.get("civitai")
    if isinstance(civitai, dict):
        for key in _TRIGGER_WORD_KEYS:
            words.extend(_trigger_words_from_value(civitai.get(key)))

    return _dedupe_text_values(words)


def _get_lora_manager_trigger_words(lora_path: str) -> list[str]:
    metadata = _load_lora_manager_metadata(lora_path)
    return _lora_manager_trigger_words_from_metadata(metadata)


def _get_lora_info(lora_name: str) -> tuple[str, list[str]]:
    fallback_path = _fallback_lora_path(lora_name)
    trigger_words = _get_lora_manager_trigger_words(fallback_path)
    if trigger_words:
        return fallback_path, trigger_words

    try:
        from py.utils.utils import get_lora_info  # type: ignore

        path, trigger_words = get_lora_info(lora_name)
        if not isinstance(trigger_words, list):
            trigger_words = []
        trigger_words = _dedupe_text_values(trigger_words)
        if trigger_words:
            return str(path), trigger_words
        json_trigger_words = _get_lora_manager_trigger_words(str(path))
        return str(path), json_trigger_words
    except Exception:
        return fallback_path, []


def _lora_combo_values() -> list[str]:
    try:
        import folder_paths  # type: ignore

        names = [str(name) for name in folder_paths.get_filename_list("loras")]
    except Exception:
        names = []
    values = ["None"]
    seen = {"none"}
    for name in names:
        text = str(name or "").strip()
        if not text:
            continue
        key = text.casefold()
        if key in seen:
            continue
        seen.add(key)
        values.append(text)
    return values


def _lora_model_exists(lora_name: str) -> bool | None:
    name = str(lora_name or "").strip()
    if not name or name == "None":
        return True

    try:
        import folder_paths  # type: ignore
    except Exception:
        return None

    candidates = _dedupe_text_values((
        name,
        name.replace("\\", "/"),
        name.replace("/", os.sep),
    ))
    for candidate in candidates:
        if folder_paths.get_full_path("loras", candidate):
            return True
    return False


def _missing_lora_display_name(input_name: str, stack_name: str) -> str:
    input_text = str(input_name or "").strip()
    stack_text = str(stack_name or "").strip()
    if not input_text or input_text == stack_text:
        return stack_text
    normalized_input = input_text.replace("\\", "/").casefold()
    normalized_stack = stack_text.replace("\\", "/").casefold()
    if normalized_input == normalized_stack:
        return stack_text
    return f"{stack_text} (input: {input_text})"


def _raise_missing_loras(profile_index: int, missing_loras: list[str]):
    if not missing_loras:
        return
    lines = "\n".join(f"- {name}" for name in missing_loras)
    message = (
        "[EasyUse Anima] LoRA Preset profile "
        f"{profile_index} contains missing LoRA model(s):\n"
        f"{lines}\n"
        "Install the missing file under ComfyUI/models/loras or remove it from the profile."
    )
    logger.error(message)
    raise RuntimeError(message)


__all__ = ()
