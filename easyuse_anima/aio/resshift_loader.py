"""Local checkpoint boundary for the optional ResShift inference provider.

Network definitions and inference remain in ComfyUI-Distilled-ResShift. Its
downloading/checkpoint-loading helpers are deliberately not called here.
"""

from __future__ import annotations

import sys
from pathlib import Path, PureWindowsPath
from typing import Any

DEFAULT_STUDENTS = {
    "x2": "rsd_student_18k.safetensors",
    "x4": "rsd_student_final.safetensors",
}
VQGAN_NAME = "autoencoder_vq_f4.pth"
CHECKPOINT_EXTENSIONS = {".safetensors", ".pth", ".pt", ".ckpt", ".bin"}


def resolve_model_path(name: str, folder_paths: Any) -> str:
    """Resolve an inventory name, never an arbitrary checkpoint path."""
    normalized = str(name).replace("\\", "/")
    if (
        not normalized
        or "\x00" in normalized
        or PureWindowsPath(normalized).drive
        or normalized.startswith("/")
        or any(part in {"", ".", ".."} for part in normalized.split("/"))
        or ":" in normalized
        or Path(normalized).suffix.lower() not in CHECKPOINT_EXTENSIONS
    ):
        raise ValueError("[EasyUseAnima] ResShift requires a registered local model name.")
    inventory = {
        str(entry).replace("\\", "/"): entry
        for entry in folder_paths.get_filename_list("resshift")
    }
    original = inventory.get(normalized)
    path = folder_paths.get_full_path("resshift", original) if original else None
    if path is None:
        raise FileNotFoundError(
            f"[EasyUseAnima] ResShift model '{normalized}' is not installed. "
            "Place it in a registered models/resshift folder and refresh the model list. "
            "AiO does not download ResShift models."
        )
    resolved = Path(path).resolve(strict=True)
    roots = [Path(root).resolve() for root in folder_paths.get_folder_paths("resshift")]
    if not resolved.is_file() or not any(resolved.is_relative_to(root) for root in roots):
        raise ValueError("[EasyUseAnima] ResShift model is outside its registered model folders.")
    return str(resolved)


def _state_dict(value: Any, torch: Any) -> dict[str, Any]:
    if not isinstance(value, dict) or not value or any(
        not isinstance(key, str) or not torch.is_tensor(tensor)
        for key, tensor in value.items()
    ):
        raise ValueError("[EasyUseAnima] ResShift checkpoint must contain tensor weights.")
    return {key.removeprefix("module."): tensor for key, tensor in value.items()}


def _student_data(weights: Any, metadata: Any, torch: Any):
    metadata = metadata or {}
    if isinstance(weights, dict) and "ema" in weights:
        metadata = weights
        weights = weights["ema"]
    state = _state_dict(weights, torch)
    noise_mode = metadata.get("noise_mode", "concat")
    cond_lq = metadata.get("cond_lq", "latent")
    channels = metadata.get("noise_channels")
    channels = int(channels) if channels is not None else None
    if noise_mode not in {"concat", "add"} or cond_lq not in {"latent", "pixel"}:
        raise ValueError("[EasyUseAnima] Unsupported ResShift student architecture metadata.")
    if channels is not None and channels <= 0:
        raise ValueError("[EasyUseAnima] ResShift noise_channels must be positive.")
    return state, noise_mode, channels, cond_lq


def load_local_resshift_model(loader_class: Any, settings: dict[str, Any]) -> Any:
    """Build the external RESSHIFT_MODEL using only ComfyUI safe checkpoint reads."""
    import folder_paths  # type: ignore

    scale = str(settings.get("scale") or "x2")
    dtype_name = str(settings.get("dtype") or "bf16")
    if scale not in DEFAULT_STUDENTS or dtype_name not in {"bf16", "fp32"}:
        raise ValueError("[EasyUseAnima] Unsupported ResShift scale or dtype.")
    student_name = str(settings.get("student_name") or "(auto-download)")
    if student_name == "(auto-download)":
        student_name = DEFAULT_STUDENTS[scale]
    if Path(student_name).name == VQGAN_NAME:
        raise ValueError("[EasyUseAnima] Select a ResShift student, not the VQGAN checkpoint.")
    # Validate BOTH names before any checkpoint read or model construction.
    student_path = resolve_model_path(student_name, folder_paths)
    vqgan_path = resolve_model_path(VQGAN_NAME, folder_paths)

    provider = sys.modules.get(loader_class.__module__)
    inference = getattr(provider, "R", None)
    model_class = getattr(provider, "ResShiftModel", None)
    if inference is None or not callable(model_class) or not all(
        callable(getattr(inference, name, None))
        for name in ("load_configs", "build_student", "build_diffusion", "swin_align")
    ):
        raise RuntimeError(
            "[EasyUseAnima] Unsupported ComfyUI-Distilled-ResShift provider. "
            "Update the external pack; AiO will not fall back to its checkpoint loader."
        )

    import comfy.model_management as management  # type: ignore
    import torch  # type: ignore
    from comfy.model_patcher import ModelPatcher  # type: ignore
    from comfy.utils import load_torch_file  # type: ignore
    from resshift.ldm.models.autoencoder import VQModelTorch  # type: ignore

    weights, metadata = load_torch_file(student_path, safe_load=True, return_metadata=True)
    student_state, noise_mode, noise_channels, cond_lq = _student_data(weights, metadata, torch)
    vqgan_state = _state_dict(load_torch_file(vqgan_path, safe_load=True), torch)

    cfg = inference.load_configs(vqgan_path, config_path=inference.CONFIGS[scale])
    if cfg.autoencoder.target != "resshift.ldm.models.autoencoder.VQModelTorch":
        raise RuntimeError("[EasyUseAnima] Unsupported ResShift autoencoder architecture.")
    if int(cfg.diffusion.params.sf) != int(scale[1:]):
        raise RuntimeError("[EasyUseAnima] ResShift configuration does not match the selected scale.")
    offload_device = management.unet_offload_device()
    dtype = torch.bfloat16 if dtype_name == "bf16" else torch.float32
    student = inference.build_student(
        cfg, offload_device, dtype=torch.float32,
        noise_mode=noise_mode, noise_channels=noise_channels,
    )
    student.load_state_dict(student_state, strict=True)
    # Pass only construction parameters, never a checkpoint/remap path or target
    # supplied by a model file. In particular, do not call build_autoencoder().
    params = cfg.autoencoder.params
    vqgan = VQModelTorch(
        ddconfig=dict(params.ddconfig), n_embed=params.n_embed, embed_dim=params.embed_dim,
    )
    incompatible = vqgan.load_state_dict(vqgan_state, strict=False)
    if incompatible.missing_keys:
        raise ValueError("[EasyUseAnima] ResShift VQGAN checkpoint is missing required weights.")
    vqgan.to(device=offload_device, dtype=dtype).eval().requires_grad_(False)
    bundle = torch.nn.Module()
    bundle.add_module("student", student)
    bundle.add_module("vqgan", vqgan)
    patcher = ModelPatcher(
        bundle, load_device=management.get_torch_device(), offload_device=offload_device,
    )
    return model_class(
        patcher, cfg, inference.build_diffusion(cfg), int(scale[1:]),
        inference.swin_align(cfg), dtype_name == "bf16", cond_lq,
    )
