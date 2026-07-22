"""AiO sampler, latent, and VAE invocation helpers."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, TypeAlias

_RuntimeResolver: TypeAlias = Callable[[str], Any]
_RUNTIME_RESOLVER: _RuntimeResolver | None = None


def _bind_aio_sampling_runtime(*, resolve_helper: _RuntimeResolver) -> None:
    """Bind root compatibility helpers without importing the root module."""

    global _RUNTIME_RESOLVER
    _RUNTIME_RESOLVER = resolve_helper


def _runtime_helper(name: str) -> Any:
    resolver = _RUNTIME_RESOLVER
    if resolver is None:
        raise RuntimeError(
            f"[EasyUseAnima] AiO sampling runtime helper is not bound: {name}"
        )
    return resolver(name)


def _new_aio_random_seed() -> int:
    random_module = _runtime_helper("random")
    return random_module.randint(0, _runtime_helper("MAX_SEED"))


def _resolve_aio_runtime_seed(value) -> int:
    seed = _runtime_helper("_normalize_aio_seed")(value)
    if seed in _runtime_helper("AIO_SPECIAL_SEEDS"):
        return _runtime_helper("_new_aio_random_seed")()
    return max(0, min(_runtime_helper("MAX_SEED"), seed))


def _generate_empty_latent_with_comfy(width: int, height: int):
    latent_cls = _runtime_helper("_find_comfy_node_class")("EmptyLatentImage")
    if latent_cls is None:
        raise RuntimeError("[EasyUseAnima] Could not find ComfyUI EmptyLatentImage.")
    latent_node = latent_cls()
    generate = getattr(latent_node, "generate", None)
    if generate is None:
        raise RuntimeError(
            "[EasyUseAnima] EmptyLatentImage does not expose generate()."
        )
    result = generate(max(16, int(width)), max(16, int(height)), 1)
    values = _runtime_helper("_node_output_tuple")(result)
    if not values:
        raise RuntimeError("[EasyUseAnima] EmptyLatentImage returned no LATENT.")
    return values[0]


def _sample_latent_with_comfy(
    model,
    seed: int,
    steps: int,
    cfg: float,
    sampler_name: str,
    scheduler: str,
    positive,
    negative,
    latent_image,
    denoise: float,
):
    sampler_cls = _runtime_helper("_find_comfy_node_class")("KSampler")
    if sampler_cls is None:
        raise RuntimeError("[EasyUseAnima] Could not find ComfyUI KSampler.")
    sampler = sampler_cls()
    sample = getattr(sampler, "sample", None)
    if sample is None:
        raise RuntimeError("[EasyUseAnima] KSampler does not expose sample().")
    result = sample(
        model,
        _runtime_helper("_resolve_aio_runtime_seed")(seed),
        max(1, int(steps)),
        float(cfg),
        str(sampler_name),
        str(scheduler),
        positive,
        negative,
        latent_image,
        float(denoise),
    )
    values = _runtime_helper("_node_output_tuple")(result)
    if not values:
        raise RuntimeError("[EasyUseAnima] KSampler returned no LATENT.")
    return values[0]


def _sample_latent_with_spectrum_mod_guidance_advanced(
    model,
    clip,
    sampler_settings: dict[str, Any],
    mod_guidance_settings: dict[str, Any],
    use_mod_guidance: bool,
    positive,
    negative,
    latent_image,
    quality_tags: str,
    quality_neg: str,
):
    sampler_cls = _runtime_helper("_require_custom_node_class")(
        "SpectrumKSamplerAdvanced",
        "ComfyUI-Spectrum-KSampler",
        "Repository: https://github.com/blepping/ComfyUI-Spectrum-KSampler",
    )
    spectrum = sampler_settings.get("spectrum", {})
    if not isinstance(spectrum, dict):
        spectrum = {}
    corrections = sampler_settings.get("dit_corrections", {})
    if not isinstance(corrections, dict):
        corrections = {}
    use_corrections = _runtime_helper("_as_bool")(corrections.get("enabled"), False)
    use_smc = use_corrections and _runtime_helper("_as_bool")(
        corrections.get("smc_cfg"), False
    )
    use_cfgpp = use_corrections and _runtime_helper("_as_bool")(
        corrections.get("cfgpp"), False
    )
    use_fsg = use_corrections and _runtime_helper("_as_bool")(
        corrections.get("fsg"), False
    )
    advanced_mod = mod_guidance_settings.get("advanced", {})
    if not isinstance(advanced_mod, dict):
        advanced_mod = {}
    profile = _runtime_helper("_normalize_anima_mod_guidance_profile")(
        mod_guidance_settings.get(
            "profile", _runtime_helper("ANIMA_MOD_GUIDANCE_DEFAULT_PROFILE")
        )
    )
    mod_w = _runtime_helper("_as_float")(advanced_mod.get("mod_w"), 3.0)
    if not use_mod_guidance or profile == _runtime_helper(
        "ANIMA_MOD_GUIDANCE_PROFILE_OFF"
    ):
        mod_w = 0.0
    sampler = sampler_cls()
    sampler_kwargs = {
        "model": model,
        "clip": clip,
        "seed": _runtime_helper("_resolve_aio_runtime_seed")(
            sampler_settings.get("seed")
        ),
        "steps": _runtime_helper("_as_int")(sampler_settings.get("steps"), 28),
        "cfg": _runtime_helper("_as_float")(sampler_settings.get("cfg"), 5.0),
        "sampler_name": str(sampler_settings.get("sampler_name") or "euler_ancestral"),
        "scheduler": str(sampler_settings.get("scheduler") or "normal"),
        "positive": positive,
        "negative": negative,
        "latent_image": latent_image,
        "adapter": str(advanced_mod.get("adapter") or "(auto-download default)"),
        "quality_tags": str(quality_tags or advanced_mod.get("quality_tags") or ""),
        "mod_w": mod_w,
        "quality_neg": str(quality_neg or ""),
        "mod_start_layer": _runtime_helper("_as_int")(
            advanced_mod.get("mod_start_layer"), 8
        ),
        "mod_end_layer": _runtime_helper("_as_int")(
            advanced_mod.get("mod_end_layer"), 27
        ),
        "mod_taper": _runtime_helper("_as_int")(advanced_mod.get("mod_taper"), 0),
        "mod_taper_scale": _runtime_helper("_as_float")(
            advanced_mod.get("mod_taper_scale"), 0.25
        ),
        "mod_final_w": _runtime_helper("_as_float")(
            advanced_mod.get("mod_final_w"), 0.0
        ),
        "denoise": _runtime_helper("_as_float")(sampler_settings.get("denoise"), 1.0),
        "window_size": _runtime_helper("_as_float")(spectrum.get("window_size"), 2.0),
        "flex_window": _runtime_helper("_as_float")(spectrum.get("flex_window"), 0.25),
        "warmup_steps": _runtime_helper("_as_int")(spectrum.get("warmup_steps"), 6),
        "blend_w": _runtime_helper("_as_float")(spectrum.get("blend_w"), 0.3),
        "cheby_degree": _runtime_helper("_as_int")(spectrum.get("cheby_degree"), 3),
        "ridge_lambda": _runtime_helper("_as_float")(spectrum.get("ridge_lambda"), 0.1),
        "dcw_mode": str(corrections.get("dcw_mode") or "off")
        if use_corrections
        else "off",
        "dcw_lambda": _runtime_helper("_as_float")(corrections.get("dcw_lambda"), 0.01)
        if use_corrections
        else 0.0,
        "dcw_band_mask": str(corrections.get("dcw_band_mask") or "LL")
        if use_corrections
        else "LL",
        "dcw_calibrator": str(
            corrections.get("dcw_calibrator") or "(auto-download default)"
        ),
        "cfgpp_lambda": _runtime_helper("_as_float")(
            corrections.get("cfgpp_lambda"), 0.0
        )
        if use_cfgpp
        else 0.0,
        "fsg": use_fsg,
        "fsg_band_lo": _runtime_helper("_as_float")(
            corrections.get("fsg_band_lo"), 0.59
        )
        if use_fsg
        else 0.59,
        "fsg_band_hi": _runtime_helper("_as_float")(
            corrections.get("fsg_band_hi"), 0.75
        )
        if use_fsg
        else 0.75,
        "fsg_k": _runtime_helper("_as_int")(corrections.get("fsg_k"), 3)
        if use_fsg
        else 3,
        "fsg_d_sigma": _runtime_helper("_as_float")(corrections.get("fsg_d_sigma"), 0.1)
        if use_fsg
        else 0.1,
        "fsg_gamma": _runtime_helper("_as_float")(corrections.get("fsg_gamma"), 0.0)
        if use_fsg
        else 0.0,
        "adaptive_smc_alpha": _runtime_helper("_as_float")(
            corrections.get("adaptive_smc_alpha"), 0.0
        )
        if use_smc
        else 0.0,
        "smc_cfg_lambda": _runtime_helper("_as_float")(
            corrections.get("smc_cfg_lambda"), 5.0
        )
        if use_smc
        else 0.0,
    }
    extra = sampler_settings.get("spectrum_extra")
    if isinstance(extra, dict):
        for key, value in extra.items():
            text_key = str(key or "")
            if text_key and text_key not in sampler_kwargs:
                sampler_kwargs[text_key] = value
    values = _runtime_helper("_node_output_tuple")(
        _runtime_helper("_call_with_supported_kwargs")(
            sampler.sample,
            (),
            sampler_kwargs,
            "SpectrumKSamplerAdvanced.sample()",
        )
    )
    if not values:
        raise RuntimeError(
            "[EasyUseAnima] SpectrumKSamplerAdvanced returned no LATENT."
        )
    return values[0]


def _sample_latent_with_spectrum_spd(
    model,
    sampler_settings: dict[str, Any],
    positive,
    negative,
    latent_image,
):
    spd_cls = _runtime_helper("_require_custom_node_class")(
        "SpectrumSPDKSampler",
        "ComfyUI-Spectrum-KSampler",
        "Repository: https://github.com/blepping/ComfyUI-Spectrum-KSampler",
    )
    spd = sampler_settings.get("spd", {})
    if not isinstance(spd, dict):
        spd = {}
    # Spectrum SPEED/SPD is Euler-only. Normalize before calling the node so
    # saved workflows do not emit a misleading "ignoring requested sampler" warning.
    sampler_name = "euler"
    sampler = spd_cls()
    sampler_kwargs = {
        "model": model,
        "seed": _runtime_helper("_resolve_aio_runtime_seed")(
            sampler_settings.get("seed")
        ),
        "steps": _runtime_helper("_as_int")(sampler_settings.get("steps"), 28),
        "cfg": _runtime_helper("_as_float")(sampler_settings.get("cfg"), 5.0),
        "sampler_name": sampler_name,
        "scheduler": str(sampler_settings.get("scheduler") or "simple"),
        "positive": positive,
        "negative": negative,
        "latent_image": latent_image,
        "split_mode": str(spd.get("split_mode") or "single"),
        "spd_scale": _runtime_helper("_as_float")(spd.get("scale"), 0.5),
        "spd_sigma": _runtime_helper("_as_float")(spd.get("sigma"), 0.7),
        "denoise": _runtime_helper("_as_float")(sampler_settings.get("denoise"), 1.0),
        "adaptive_smc_alpha": _runtime_helper("_as_float")(
            spd.get("adaptive_smc_alpha"), 0.0
        ),
    }
    extra = sampler_settings.get("spd_extra")
    if isinstance(extra, dict):
        for key, value in extra.items():
            text_key = str(key or "")
            if text_key and text_key not in sampler_kwargs:
                sampler_kwargs[text_key] = value
    values = _runtime_helper("_node_output_tuple")(
        _runtime_helper("_call_with_supported_kwargs")(
            sampler.sample,
            (),
            sampler_kwargs,
            "SpectrumSPDKSampler.sample()",
        )
    )
    if not values:
        raise RuntimeError("[EasyUseAnima] SpectrumSPDKSampler returned no LATENT.")
    return values[0]


def _sample_latent_with_aio_backend(
    model,
    clip,
    positive,
    negative,
    latent_image,
    sampler_settings: dict[str, Any],
    mod_guidance_settings: dict[str, Any],
    use_mod_guidance: bool,
    quality_tags: str,
    quality_neg: str,
):
    backend = str(sampler_settings.get("backend") or "comfy_ksampler")
    if backend == "spectrum_mod_guidance_advanced":
        return _runtime_helper("_sample_latent_with_spectrum_mod_guidance_advanced")(
            model,
            clip,
            sampler_settings,
            mod_guidance_settings,
            use_mod_guidance,
            positive,
            negative,
            latent_image,
            quality_tags,
            quality_neg,
        )
    if backend == "spectrum_spd_speed":
        return _runtime_helper("_sample_latent_with_spectrum_spd")(
            model,
            sampler_settings,
            positive,
            negative,
            latent_image,
        )
    return _runtime_helper("_sample_latent_with_comfy")(
        model,
        sampler_settings["seed"],
        sampler_settings["steps"],
        sampler_settings["cfg"],
        sampler_settings["sampler_name"],
        sampler_settings["scheduler"],
        positive,
        negative,
        latent_image,
        sampler_settings["denoise"],
    )


def _decode_latent_with_comfy(vae, samples):
    decoder_cls = _runtime_helper("_find_comfy_node_class")("VAEDecode")
    if decoder_cls is None:
        raise RuntimeError("[EasyUseAnima] Could not find ComfyUI VAEDecode.")
    decoder = decoder_cls()
    decode = getattr(decoder, "decode", None)
    if decode is None:
        raise RuntimeError("[EasyUseAnima] VAEDecode does not expose decode().")
    result = decode(vae, samples)
    values = _runtime_helper("_node_output_tuple")(result)
    if not values:
        raise RuntimeError("[EasyUseAnima] VAEDecode returned no IMAGE.")
    return values[0]


def _encode_image_with_comfy_vae(vae, image):
    encoder_cls = _runtime_helper("_find_comfy_node_class")("VAEEncode")
    if encoder_cls is None:
        raise RuntimeError("[EasyUseAnima] Could not find ComfyUI VAEEncode.")
    encoder = encoder_cls()
    encode = getattr(encoder, "encode", None)
    if encode is None:
        raise RuntimeError("[EasyUseAnima] VAEEncode does not expose encode().")
    values = _runtime_helper("_node_output_tuple")(encode(vae, image))
    if not values:
        raise RuntimeError("[EasyUseAnima] VAEEncode returned no LATENT.")
    return values[0]


def _aio_stage_sampler_settings(
    base_sampler: dict[str, Any],
    stage_settings: dict[str, Any],
    *,
    scheduler_default: str,
    inherit_backend: bool = False,
) -> dict[str, Any]:
    inherit_sampler = _runtime_helper("_as_bool")(
        stage_settings.get("inherit_sampler_settings"), False
    )
    inherited_spd_fallback = False
    if inherit_backend and inherit_sampler:
        inherited_backend = str(base_sampler.get("backend") or "comfy_ksampler")
        if inherited_backend == "spectrum_spd_speed":
            backend = "comfy_ksampler"
            inherited_spd_fallback = True
        else:
            backend = inherited_backend
    elif inherit_backend:
        backend = "comfy_ksampler"
    else:
        backend = "comfy_ksampler"
    return {
        "backend": backend,
        "seed": _runtime_helper("_resolve_aio_runtime_seed")(base_sampler.get("seed")),
        "seed_after_generate": _runtime_helper("SEED_CONTROL_FIXED"),
        "steps": _runtime_helper("_as_int")(
            stage_settings.get("steps"),
            _runtime_helper("_as_int")(base_sampler.get("steps"), 28),
        ),
        "cfg": (
            _runtime_helper("_as_float")(base_sampler.get("cfg"), 5.0)
            if inherit_sampler
            else _runtime_helper("_as_float")(
                stage_settings.get("cfg"),
                _runtime_helper("_as_float")(base_sampler.get("cfg"), 5.0),
            )
        ),
        "sampler_name": (
            (
                "euler"
                if inherited_spd_fallback
                else str(base_sampler.get("sampler_name") or "euler")
            )
            if inherit_sampler
            else str(
                stage_settings.get("sampler_name")
                or base_sampler.get("sampler_name")
                or "euler"
            )
        ),
        "scheduler": (
            str(base_sampler.get("scheduler") or scheduler_default)
            if inherit_sampler
            else str(stage_settings.get("scheduler") or scheduler_default)
        ),
        "denoise": _runtime_helper("_as_float")(stage_settings.get("denoise"), 1.0),
        "spectrum": _runtime_helper("_json_clone")(
            stage_settings.get("spectrum") or {}
        ),
        "dit_corrections": _runtime_helper("_json_clone")(
            stage_settings.get("dit_corrections") or {}
        ),
        "spd": _runtime_helper("_json_clone")(stage_settings.get("spd") or {}),
        "spectrum_extra": {},
        "spd_extra": {},
    }


def _aio_highres_effective_backend(
    sampler_settings: dict[str, Any],
    highres_settings: dict[str, Any],
) -> str:
    if not _runtime_helper("_as_bool")(highres_settings.get("enabled"), False):
        return ""
    if _runtime_helper("_as_bool")(
        highres_settings.get("inherit_sampler_settings"), False
    ):
        backend = str(sampler_settings.get("backend") or "comfy_ksampler")
        return "comfy_ksampler" if backend == "spectrum_spd_speed" else backend
    return "comfy_ksampler"


__all__ = ()
