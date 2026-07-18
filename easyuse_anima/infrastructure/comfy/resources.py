"""Domain-neutral ComfyUI model-resource adapters."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from typing import Any


def _comfy_checkpoint_names() -> list[str]:
    try:
        import folder_paths  # type: ignore

        names = [str(name) for name in folder_paths.get_filename_list("checkpoints")]
        if names:
            return names
    except Exception:
        pass
    return ["sam3.1_multiplex_fp16.safetensors"]


def _folder_path_names(folder_name: str, fallback: list[str]) -> list[str]:
    try:
        import folder_paths  # type: ignore

        names = [str(name) for name in folder_paths.get_filename_list(folder_name)]
        if names:
            return names
    except Exception:
        pass
    return list(fallback)


def _comfy_diffusion_model_names(
    fallback: Iterable[str],
    folder_path_names: Callable[[str, list[str]], list[str]] = _folder_path_names,
) -> list[str]:
    return folder_path_names("diffusion_models", list(fallback))


def _comfy_text_encoder_names(
    fallback: Iterable[str],
    folder_path_names: Callable[[str, list[str]], list[str]] = _folder_path_names,
) -> list[str]:
    return folder_path_names("text_encoders", list(fallback))


def _comfy_vae_names(
    fallback: Iterable[str],
    find_node_class: Callable[[str], Any],
    folder_path_names: Callable[[str, list[str]], list[str]] = _folder_path_names,
) -> list[str]:
    loader_cls = find_node_class("VAELoader")
    if loader_cls is not None:
        try:
            required = loader_cls.INPUT_TYPES().get("required", {})
            names = [str(name) for name in required.get("vae_name", ([],))[0]]
            if names:
                return names
        except Exception:
            pass
    return folder_path_names("vae", list(fallback))


def _comfy_clip_loader_types(
    fallback: Iterable[str],
    find_node_class: Callable[[str], Any],
) -> list[str]:
    loader_cls = find_node_class("CLIPLoader")
    if loader_cls is not None:
        try:
            required = loader_cls.INPUT_TYPES().get("required", {})
            names = [str(name) for name in required.get("type", ([],))[0]]
            if names:
                return names
        except Exception:
            pass
    return list(fallback)


__all__ = ()
