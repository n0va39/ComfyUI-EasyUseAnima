"""Reviewed model-family policy for AiO; inactive settings never drive execution."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class AIOModelProfile:
    name: str
    node_type: str
    clip_type: str
    latent_node: str
    dimension_multiple: int
    sampler_backends: tuple[str, ...]
    sampling_node: str
    steps: int
    cfg: float
    shift: float
    sampler_name: str
    scheduler: str
    resource_hint: str
    anima_features: bool = False


AIO_MODEL_PROFILES = {
    "anima": AIOModelProfile(
        "Anima", "EasyUseAnimaAIOGenerator", "qwen_image", "EmptyLatentImage", 1,
        ("comfy_ksampler", "spectrum_mod_guidance_advanced", "spectrum_spd_speed"),
        "ModelSamplingAuraFlow", 32, 5.0, 3.0, "er_sde", "simple",
        "Anima diffusion model, Qwen3 0.6B encoder and Qwen Image VAE", True,
    ),
    "moss_image": AIOModelProfile(
        "MOSS", "EasyUseMossAIOGenerator", "moss_image", "EmptyFlux2LatentImage", 16,
        ("comfy_ksampler",),
        "ModelSamplingAuraFlow", 25, 2.5, 5.0, "er_sde", "simple",
        "native MOSS-Image diffusion model, Qwen3.5 9B encoder and FLUX.2 VAE",
    ),
    "krea2": AIOModelProfile(
        "Krea2", "EasyUseKrea2AIOGenerator", "krea2", "EmptyLatentImage", 16,
        ("comfy_ksampler",),
        "ModelSamplingFlux", 8, 1.0, 1.15, "euler", "simple",
        "Krea2 diffusion model, Qwen3-VL 4B encoder and Qwen Image VAE",
    ),
}


def aio_model_profile(family: str = "anima") -> AIOModelProfile:
    if not isinstance(family, str) or family not in AIO_MODEL_PROFILES:
        raise ValueError(f"[EasyUseAnima] Unsupported AiO model family: {family!r}")
    return AIO_MODEL_PROFILES[family]


def aio_model_defaults(defaults: dict[str, Any], family: str) -> dict[str, Any]:
    """Supply only missing settings; never replace a saved explicit tuning value."""
    profile = aio_model_profile(family)
    result = deepcopy(defaults)
    result["model_family"] = family
    if not profile.anima_features:
        result["sampler"].update(
            steps=profile.steps, cfg=profile.cfg,
            sampler_name=profile.sampler_name, scheduler=profile.scheduler,
        )
        result["model_patches"]["aura_flow"]["shift"] = profile.shift
        result["mod_guidance"]["mode"] = "disabled"
        result["artist_mix"]["mode"] = "off"
        for target in ("face", "eye"):
            result["detailer"][target]["spectrum"]["enabled"] = False
    return result


def validate_aio_model_settings(settings: dict[str, Any], *, aio_hook=None) -> None:
    family = settings.get("model_family", "anima")
    profile = aio_model_profile(family)
    if settings["sampler"]["backend"] not in profile.sampler_backends:
        detail = (
            "Native MOSS currently requires ComfyUI KSampler; upstream Spectrum "
            "2.12.1 targets a different MOSS loader and time-embedding contract."
            if family == "moss_image" else "Use ComfyUI KSampler."
        )
        raise ValueError(
            f"[EasyUseAnima] {profile.name} does not support this sampler backend. "
            + detail
        )
    if profile.anima_features:
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
            f"[EasyUseAnima] {profile.name} support is limited to basic txt2img. "
            "Disable unsupported options: " + ", ".join(unsupported)
        )


def validate_aio_model_resources(
    family: str, context: dict[str, Any], *, model=None,
) -> None:
    profile = aio_model_profile(family)
    if family != "anima" and context.get("resource_info", {}).get("clip_type") != profile.clip_type:
        raise ValueError(
            f"[EasyUseAnima] {profile.name} requires CLIP type '{profile.clip_type}', "
            f"with {profile.resource_hint} in Easy Use Anima Input."
        )
    if model is None:
        return
    config = getattr(getattr(getattr(model, "model", None), "model_config", None), "unet_config", None)
    actual = config.get("image_model") if isinstance(config, dict) else None
    if family != "anima" and actual != family:
        raise ValueError(f"[EasyUseAnima] AiO Generator ({profile.name}) requires {profile.resource_hint}.")
    if family == "anima" and actual in AIO_MODEL_PROFILES and actual != family:
        target = aio_model_profile(actual)
        raise ValueError(f"[EasyUseAnima] Select {target.name}: use AiO Generator ({target.name}) for this model.")


def validate_aio_model_dimensions(family: str, width: int, height: int) -> None:
    profile = aio_model_profile(family)
    multiple = profile.dimension_multiple
    if family != "anima" and (width <= 0 or height <= 0 or width % multiple or height % multiple):
        raise ValueError(f"[EasyUseAnima] {profile.name} width and height must be positive multiples of {multiple}.")


__all__ = ()
