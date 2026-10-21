"""Reviewed model-family policy for AiO; inactive settings never drive execution."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any

from .capabilities import aio_feature_support


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


AIO_MODEL_PROFILES = {
    "anima": AIOModelProfile(
        "Anima", "EasyUseAnimaAIOGenerator", "qwen_image", "EmptyLatentImage", 1,
        ("comfy_ksampler", "spectrum_mod_guidance_advanced", "spectrum_spd_speed"),
        "ModelSamplingAuraFlow", 32, 5.0, 3.0, "er_sde", "simple",
        "Anima diffusion model, Qwen3 0.6B encoder and Qwen Image VAE",
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
    if family != "anima":
        result["sampler"].update(
            steps=profile.steps, cfg=profile.cfg,
            sampler_name=profile.sampler_name, scheduler=profile.scheduler,
        )
        result["model_patches"]["aura_flow"]["shift"] = profile.shift
        result["mod_guidance"]["mode"] = "disabled"
        result["artist_mix"]["mode"] = "off"
        for stage in (result["highres"], result["upscale"], *(
            result["detailer"][target] for target in ("face", "eye")
        )):
            stage.update(
                steps=profile.steps, cfg=profile.cfg,
                sampler_name=profile.sampler_name, scheduler=profile.scheduler,
            )
            stage["spectrum"]["enabled"] = False
            stage["dit_corrections"]["enabled"] = False
    return result


def validate_aio_model_settings(settings: dict[str, Any], *, aio_hook=None, node_lookup=None) -> None:
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
    if family == "anima":
        return
    patches = settings["model_patches"]
    unsupported = []
    checks = {
        "mod_guidance": ("Mod Guidance", settings["mod_guidance"]["mode"] != "disabled"),
        "artist_mix": ("Artist Mix", settings["artist_mix"]["mode"] != "off"),
        "negpip": ("NegPip", settings["negpip"]["mode"] != "off"),
        "dave": ("DAVE", patches["dave"]["enabled"]),
        "safe_pag": ("Safe PAG", patches["safe_pag"]["enabled"]),
        "sage_attention": ("SageAttention", patches["kj"]["sage_attention"] != "disabled"),
        "fp16_accumulation": ("KJ FP16 accumulation", patches["kj"]["fp16_accumulation"]),
        "torch_compile": ("KJ Torch Compile", patches["kj"]["torch_compile"]["enabled"]),
        "highres": ("Highres", settings["highres"]["enabled"]),
        "upscale": ("Upscale", settings["upscale"]["enabled"]),
        "detailer": ("Detailer", settings["detailer"]["enabled"]),
        "aio_hook": ("AiO hook", aio_hook is not None),
    }
    for feature, (name, enabled) in checks.items():
        if enabled and not aio_feature_support(family, feature, node_lookup=node_lookup)["supported"]:
            unsupported.append(name)
    # Check every active sampling stage, including user-created detailer blocks.
    # Inactive saved values remain intact and do not drive execution.
    stages = {"sampler": settings["sampler"]}
    stages.update({
        name: settings[name] for name in ("highres", "upscale")
        if settings[name]["enabled"]
        and (name != "upscale" or settings[name]["backend"] == "usdu")
    })
    if settings["detailer"]["enabled"]:
        stages.update({
            f"detailer.{name}": target for name, target in settings["detailer"].items()
            if isinstance(target, dict) and target.get("enabled")
        })
    for stage_name, stage in stages.items():
        for feature, label in (("spectrum", "Spectrum model patch"), ("dit_corrections", "DiT corrections")):
            support = aio_feature_support(
                family, feature, stage_name.split(".")[0], node_lookup=node_lookup,
            )
            if stage[feature]["enabled"] and not support["supported"]:
                unsupported.append(f"{stage_name}: {label} ({support['reason_code']})")
    if unsupported:
        raise ValueError(
            f"[EasyUseAnima] {profile.name} cannot use these model-specific features. "
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
