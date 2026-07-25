"""Domain-neutral ComfyUI model-resource adapters."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from pathlib import Path
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


def _comfy_resource_file_revision(
    folder_name: str,
    filename: str,
) -> dict[str, int | str] | None:
    category = str(folder_name or "").strip()
    name = str(filename or "").strip()
    if not category or not name:
        return None

    try:
        import folder_paths  # type: ignore

        resolve_path = getattr(folder_paths, "get_full_path", None)
        if not callable(resolve_path):
            resolve_path = getattr(
                folder_paths,
                "get_full_path_or_raise",
                None,
            )
        if not callable(resolve_path):
            return None
        raw_path = resolve_path(category, name)
        if not isinstance(raw_path, (str, Path)) or not raw_path:
            return None
        resolved_path = Path(raw_path).resolve(strict=False)
        stat = resolved_path.stat()
    except Exception:
        return None

    size = getattr(stat, "st_size", None)
    mtime_ns = getattr(stat, "st_mtime_ns", None)
    if (
        not isinstance(size, int)
        or isinstance(size, bool)
        or size < 0
        or not isinstance(mtime_ns, int)
        or isinstance(mtime_ns, bool)
    ):
        return None
    return {
        "path": str(resolved_path),
        "size": size,
        "mtime_ns": mtime_ns,
    }


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
