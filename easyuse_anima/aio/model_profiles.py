"""Reviewed model-family policy for AiO; inactive settings never drive execution."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class AIOModelProfile:
    name: str
    clip_type: str
    latent_node: str
    dimension_multiple: int
    sampler_backends: tuple[str, ...]


AIO_MODEL_PROFILES = {
    "anima": AIOModelProfile(
        "Anima", "qwen_image", "EmptyLatentImage", 1,
        ("comfy_ksampler", "spectrum_mod_guidance_advanced", "spectrum_spd_speed"),
    ),
    "moss_image": AIOModelProfile(
        "MOSS-Image", "moss_image", "EmptyFlux2LatentImage", 16,
        ("comfy_ksampler",),
    ),
}


def aio_model_profile(family: str = "anima") -> AIOModelProfile:
    if not isinstance(family, str) or family not in AIO_MODEL_PROFILES:
        raise ValueError(f"[EasyUseAnima] Unsupported AiO model family: {family!r}")
    return AIO_MODEL_PROFILES[family]


def aio_model_defaults(defaults: dict[str, Any], family: str) -> dict[str, Any]:
    """Supply only missing settings; never replace a saved explicit tuning value."""
    aio_model_profile(family)
    result = deepcopy(defaults)
    result["model_family"] = family
    if family == "moss_image":
        result["sampler"].update(steps=25, cfg=2.5)
        result["model_patches"]["aura_flow"]["shift"] = 5.0
        result["mod_guidance"]["mode"] = "disabled"
        result["artist_mix"]["mode"] = "off"
        for target in ("face", "eye"):
            result["detailer"][target]["spectrum"]["enabled"] = False
    return result


def validate_aio_model_settings(settings: dict[str, Any], *, aio_hook=None) -> None:
    family = settings.get("model_family", "anima")
    profile = aio_model_profile(family)
    if settings["sampler"]["backend"] not in profile.sampler_backends:
        raise ValueError(
            f"[EasyUseAnima] {profile.name} does not support this sampler backend. "
            "Native MOSS currently requires ComfyUI KSampler; upstream Spectrum "
            "2.12.1 targets a different MOSS loader and time-embedding contract."
        )
    if family == "anima":
        return
    patches = settings["model_patches"]
    unsupported = []
    checks = {
        "Mod Guidance": settings["mod_guidance"]["mode"] != "disabled",
        "Artist Mix": settings["artist_mix"]["mode"] != "off",
        "NegPip": settings["negpip"]["mode"] != "off",
        "DAVE": patches["dave"]["enabled"],
        "Safe PAG": patches["safe_pag"]["enabled"],
        "SageAttention": patches["kj"]["sage_attention"] != "disabled",
        "KJ FP16 accumulation": patches["kj"]["fp16_accumulation"],
        "KJ Torch Compile": patches["kj"]["torch_compile"]["enabled"],
        "Spectrum model patch": settings["sampler"]["spectrum"]["enabled"],
        "DiT corrections": settings["sampler"]["dit_corrections"]["enabled"],
        "Highres": settings["highres"]["enabled"],
        "Upscale": settings["upscale"]["enabled"],
        "AiO hook": aio_hook is not None,
    }
    for name, enabled in checks.items():
        if enabled:
            unsupported.append(name)
    if any(
        isinstance(value, dict) and value.get("enabled")
        for value in settings["detailer"].values()
    ):
        unsupported.append("Detailer")
    if unsupported:
        raise ValueError(
            "[EasyUseAnima] MOSS-Image support is limited to basic txt2img. "
            "Disable unsupported options: " + ", ".join(unsupported)
        )


def validate_aio_model_resources(
    family: str, context: dict[str, Any], *, model=None,
) -> None:
    profile = aio_model_profile(family)
    if family != "anima" and context.get("resource_info", {}).get("clip_type") != profile.clip_type:
        raise ValueError(
            f"[EasyUseAnima] {profile.name} requires CLIP type '{profile.clip_type}', "
            "Qwen3.5 9B text encoder and FLUX.2 VAE in Easy Use Anima Input."
        )
    if model is None:
        return
    config = getattr(getattr(getattr(model, "model", None), "model_config", None), "unet_config", None)
    actual = config.get("image_model") if isinstance(config, dict) else None
    if family == "moss_image" and actual != "moss_image":
        raise ValueError("[EasyUseAnima] Selected MOSS-Image profile requires a native MOSS-Image diffusion model.")
    if family == "anima" and actual == "moss_image":
        raise ValueError("[EasyUseAnima] Select MOSS-Image in the AiO model-family settings for this model.")


def validate_aio_model_dimensions(family: str, width: int, height: int) -> None:
    multiple = aio_model_profile(family).dimension_multiple
    if family != "anima" and (width <= 0 or height <= 0 or width % multiple or height % multiple):
        raise ValueError(f"[EasyUseAnima] MOSS-Image width and height must be positive multiples of {multiple}.")


__all__ = ()
