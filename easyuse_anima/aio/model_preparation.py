"""AiO LoRA application, model patching, and variant lifecycle helpers."""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any, TypeAlias

_RuntimeResolver: TypeAlias = Callable[[str], Any]
_RUNTIME_RESOLVER: _RuntimeResolver | None = None


def _bind_aio_model_preparation_runtime(*, resolve_helper: _RuntimeResolver) -> None:
    """Bind root compatibility helpers without importing the root module."""

    global _RUNTIME_RESOLVER
    _RUNTIME_RESOLVER = resolve_helper


def _runtime_helper(name: str) -> Any:
    resolver = _RUNTIME_RESOLVER
    if resolver is None:
        raise RuntimeError(
            f"[EasyUseAnima] AiO model preparation runtime helper is not bound: {name}"
        )
    return resolver(name)


def _patch_model_sampling_aura_flow(model, aura_settings: dict[str, Any]):
    find_node_class = _runtime_helper("_find_comfy_node_class")
    aura_cls = find_node_class("ModelSamplingAuraFlow")
    if aura_cls is None:
        raise RuntimeError(
            "[EasyUseAnima] Missing required core node 'ModelSamplingAuraFlow'. "
            "Use a ComfyUI build that includes ModelSamplingAuraFlow, then restart ComfyUI."
        )
    patcher = aura_cls()
    patch = getattr(patcher, "patch_aura", None)
    if patch is None:
        raise RuntimeError("[EasyUseAnima] ModelSamplingAuraFlow does not expose patch_aura().")
    result = patch(
        model,
        _runtime_helper("_as_float")(aura_settings.get("shift"), 3.0),
    )
    values = _runtime_helper("_node_output_tuple")(result)
    if not values:
        raise RuntimeError("[EasyUseAnima] ModelSamplingAuraFlow returned no MODEL.")
    return values[0]


def _apply_aio_kj_model_patches(model, kj_settings: dict[str, Any]):
    patched = model
    if kj_settings.get("fp16_accumulation"):
        torch_settings_cls = _runtime_helper("_require_custom_node_class")(
            "ModelPatchTorchSettings",
            "ComfyUI-KJNodes",
            "Repository: https://github.com/kijai/ComfyUI-KJNodes",
        )
        values = _runtime_helper("_node_output_tuple")(
            torch_settings_cls().patch(patched, True)
        )
        if not values:
            raise RuntimeError("[EasyUseAnima] ModelPatchTorchSettings returned no MODEL.")
        patched = values[0]

    sage_attention = str(kj_settings.get("sage_attention") or "disabled")
    if sage_attention != "disabled":
        sage_cls = _runtime_helper("_require_custom_node_class")(
            "PathchSageAttentionKJ",
            "ComfyUI-KJNodes",
            "Repository: https://github.com/kijai/ComfyUI-KJNodes",
        )
        values = _runtime_helper("_node_output_tuple")(
            sage_cls().patch(
                patched,
                sage_attention,
                _runtime_helper("_as_bool")(
                    kj_settings.get("sage_allow_compile"), False
                ),
            )
        )
        if not values:
            raise RuntimeError("[EasyUseAnima] PathchSageAttentionKJ returned no MODEL.")
        patched = values[0]

    compile_settings = kj_settings.get("torch_compile", {})
    if isinstance(compile_settings, dict) and compile_settings.get("enabled"):
        compile_cls = _runtime_helper("_require_custom_node_class")(
            "TorchCompileModelAdvanced",
            "ComfyUI-KJNodes",
            "Repository: https://github.com/kijai/ComfyUI-KJNodes",
        )
        values = _runtime_helper("_node_output_tuple")(
            compile_cls().patch(
                patched,
                str(compile_settings.get("backend") or "inductor"),
                _runtime_helper("_as_bool")(
                    compile_settings.get("fullgraph"), False
                ),
                str(compile_settings.get("mode") or "default"),
                str(compile_settings.get("dynamic") or "auto"),
                _runtime_helper("_as_int")(
                    compile_settings.get("dynamo_cache_size_limit"), 64
                ),
                _runtime_helper("_as_bool")(
                    compile_settings.get("compile_transformer_blocks_only"), True
                ),
                _runtime_helper("_as_bool")(
                    compile_settings.get("debug_compile_keys"), False
                ),
                _runtime_helper("_as_bool")(
                    compile_settings.get("disable_dynamic_vram"), False
                ),
            )
        )
        if not values:
            raise RuntimeError("[EasyUseAnima] TorchCompileModelAdvanced returned no MODEL.")
        patched = values[0]
    return patched


def _apply_aio_model_patches(model, settings: dict[str, Any]):
    model_patches = settings.get("model_patches", {})
    if not isinstance(model_patches, dict):
        return model
    patched = _runtime_helper("_patch_model_sampling_aura_flow")(
        model,
        model_patches.get("aura_flow", {})
        if isinstance(model_patches.get("aura_flow"), dict)
        else {},
    )
    dave_settings = model_patches.get("dave", {})
    if isinstance(dave_settings, dict) and _runtime_helper("_as_bool")(
        dave_settings.get("enabled"), False
    ):
        patched = _runtime_helper("_apply_aio_anima_dave_patch")(
            patched, dave_settings
        )
    safe_pag_settings = model_patches.get("safe_pag", {})
    if isinstance(safe_pag_settings, dict) and _runtime_helper("_as_bool")(
        safe_pag_settings.get("enabled"), False
    ):
        patched = _runtime_helper("_apply_aio_safe_pag_patch")(
            patched, safe_pag_settings
        )
    kj_settings = model_patches.get("kj", {})
    if isinstance(kj_settings, dict):
        patched = _runtime_helper("_apply_aio_kj_model_patches")(patched, kj_settings)
    return patched


def _normalize_aio_lora_stack(lora_stack) -> list[tuple[str, float, float]]:
    if isinstance(lora_stack, dict) and "__value__" in lora_stack:
        lora_stack = lora_stack["__value__"]
    if isinstance(lora_stack, str):
        try:
            lora_stack = json.loads(lora_stack or "[]")
        except json.JSONDecodeError:
            lora_stack = []
    if not isinstance(lora_stack, list):
        return []

    entries: list[tuple[str, float, float]] = []
    for item in lora_stack:
        if isinstance(item, dict):
            raw_name = item.get("name", item.get("lora", item.get("lora_name", "")))
            model_strength = item.get(
                "strength_model", item.get("model_strength", item.get("strength", 1.0))
            )
            clip_strength = item.get(
                "strength_clip",
                item.get("clip_strength", item.get("strengthTwo", model_strength)),
            )
        elif isinstance(item, (list, tuple)) and len(item) >= 3:
            raw_name, model_strength, clip_strength = item[:3]
        else:
            continue
        name = str(raw_name or "").strip()
        if not name or name.lower() == "none":
            continue
        entries.append(
            (
                _runtime_helper("_lora_stack_name")(name),
                _runtime_helper("_as_float")(model_strength, 1.0),
                _runtime_helper("_as_float")(
                    clip_strength,
                    _runtime_helper("_as_float")(model_strength, 1.0),
                ),
            )
        )
    return entries


def _aio_lora_stack_signature(lora_stack) -> list[dict[str, Any]]:
    return [
        {
            "name": name,
            "strength_model": model_strength,
            "strength_clip": clip_strength,
        }
        for name, model_strength, clip_strength in _runtime_helper(
            "_normalize_aio_lora_stack"
        )(lora_stack)
    ]


def _apply_aio_lora_stack(model, clip, lora_stack):
    entries = _runtime_helper("_normalize_aio_lora_stack")(lora_stack)
    if not entries:
        return model, clip, []

    find_node_class = _runtime_helper("_find_comfy_node_class")
    loader_cls = find_node_class("LoraLoader")
    if loader_cls is None:
        raise RuntimeError("[EasyUseAnima] Could not find ComfyUI core LoraLoader.")
    loader = loader_cls()
    load_lora = getattr(loader, "load_lora", None)
    if load_lora is None:
        raise RuntimeError("[EasyUseAnima] LoraLoader does not expose load_lora().")

    patched_model = model
    patched_clip = clip
    applied: list[dict[str, Any]] = []
    for name, model_strength, clip_strength in entries:
        if model_strength == 0 and clip_strength == 0:
            continue
        node_output_tuple = _runtime_helper("_node_output_tuple")
        values = node_output_tuple(
            load_lora(patched_model, patched_clip, name, model_strength, clip_strength)
        )
        if len(values) < 2:
            raise RuntimeError("[EasyUseAnima] LoraLoader returned no MODEL/CLIP pair.")
        patched_model, patched_clip = values[0], values[1]
        applied.append(
            {
                "name": name,
                "strength_model": model_strength,
                "strength_clip": clip_strength,
            }
        )
    return patched_model, patched_clip, applied


def _apply_aio_anima_dave_patch(model, dave_settings: dict[str, Any]):
    dave_cls = _runtime_helper("_require_custom_node_class")(
        "AnimaDAVE",
        "ComfyUI-Anima-DAVE",
        "Repository: https://github.com/sorryhyun/ComfyUI-Anima-DAVE",
    )
    if not isinstance(dave_settings, dict):
        dave_settings = {}
    patcher = dave_cls()
    patch = getattr(patcher, "patch", None)
    if patch is None:
        raise RuntimeError("[EasyUseAnima] AnimaDAVE does not expose patch().")
    result = patch(
        model,
        str(dave_settings.get("mask") or "dave_alpha.npz"),
        _runtime_helper("_as_float")(dave_settings.get("strength"), 0.30),
        _runtime_helper("_as_float")(dave_settings.get("tau"), 0.10),
    )
    values = _runtime_helper("_node_output_tuple")(result)
    if not values:
        raise RuntimeError("[EasyUseAnima] AnimaDAVE returned no MODEL.")
    return values[0]


def _apply_aio_safe_pag_patch(model, safe_pag_settings: dict[str, Any]):
    safe_pag_cls = _runtime_helper("_require_custom_node_class")(
        "AnimaSafePAG",
        "Anima Safe PAG",
        "Repository: https://github.com/iljung1106/comfyui-anima-safe-pag",
    )
    if not isinstance(safe_pag_settings, dict):
        safe_pag_settings = {}
    result = safe_pag_cls().patch(
        model,
        _runtime_helper("_as_float")(safe_pag_settings.get("scale"), 4.0),
        str(safe_pag_settings.get("block_indices") or "18"),
        _runtime_helper("_as_float")(
            safe_pag_settings.get("perturbation_strength"), 0.75
        ),
        str(safe_pag_settings.get("head_indices") or ""),
        _runtime_helper("_as_float")(
            safe_pag_settings.get("start_percent"), 0.0
        ),
        _runtime_helper("_as_float")(safe_pag_settings.get("end_percent"), 0.7),
        _runtime_helper("_as_float")(safe_pag_settings.get("rescale"), 0.2),
        str(safe_pag_settings.get("rescale_mode") or "full"),
    )
    values = _runtime_helper("_node_output_tuple")(result)
    if not values:
        raise RuntimeError("[EasyUseAnima] AnimaSafePAG returned no MODEL.")
    return values[0]


def _cleanup_aio_ephemeral_model(model, base_model=None) -> None:
    if model is None or model is base_model:
        return
    detach = getattr(model, "detach", None)
    if callable(detach):
        try:
            detach(unpatch_all=False)
            return
        except Exception as exc:
            _runtime_helper("logger").debug(
                "[EasyUseAnima] failed to detach ephemeral AiO model clone: %s", exc
            )
    try:
        import comfy.model_management as model_management  # type: ignore

        unload = getattr(model_management, "unload_model_and_clones", None)
        if callable(unload):
            unload(model, unload_additional_models=True)
            return
    except Exception as exc:
        _runtime_helper("logger").debug(
            "[EasyUseAnima] failed to unload ephemeral AiO model clone: %s", exc
        )


def _apply_aio_spectrum_correction_patch_for_comfy_sampler(
    model,
    clip,
    positive,
    sampler_settings: dict[str, Any],
):
    corrections = sampler_settings.get("dit_corrections", {})
    if not isinstance(corrections, dict) or not _runtime_helper("_as_bool")(
        corrections.get("enabled"), False
    ):
        return model
    patch_cls = _runtime_helper("_require_custom_node_class")(
        "DiTCFGFSGPatch",
        "ComfyUI-Spectrum-KSampler",
        "Repository: https://github.com/blepping/ComfyUI-Spectrum-KSampler",
    )
    use_smc = _runtime_helper("_as_bool")(corrections.get("smc_cfg"), False)
    use_cfgpp = _runtime_helper("_as_bool")(corrections.get("cfgpp"), False)
    use_fsg = _runtime_helper("_as_bool")(corrections.get("fsg"), False)
    values = _runtime_helper("_node_output_tuple")(
        patch_cls().patch(
            model,
            True,
            str(corrections.get("dcw_mode") or "off"),
            _runtime_helper("_as_float")(corrections.get("dcw_lambda"), 0.01),
            str(corrections.get("dcw_band_mask") or "LL"),
            str(corrections.get("dcw_calibrator") or "(auto-download default)"),
            use_smc,
            _runtime_helper("_as_float")(corrections.get("adaptive_smc_alpha"), 0.0)
            if use_smc
            else 0.0,
            _runtime_helper("_as_float")(corrections.get("smc_cfg_lambda"), 6.0)
            if use_smc
            else 0.0,
            use_cfgpp,
            _runtime_helper("_as_float")(corrections.get("cfgpp_lambda"), 0.0)
            if use_cfgpp
            else 0.0,
            use_fsg,
            _runtime_helper("_as_float")(corrections.get("fsg_band_lo"), 0.59),
            _runtime_helper("_as_float")(corrections.get("fsg_band_hi"), 0.75),
            _runtime_helper("_as_int")(corrections.get("fsg_k"), 3),
            _runtime_helper("_as_float")(corrections.get("fsg_d_sigma"), 0.1),
            _runtime_helper("_as_float")(corrections.get("fsg_gamma"), 0.0),
            _runtime_helper("_as_bool")(
                corrections.get("replace_existing_cfg"), False
            ),
            steps=_runtime_helper("_as_int")(sampler_settings.get("steps"), 28),
            cfg=_runtime_helper("_as_float")(sampler_settings.get("cfg"), 5.0),
            sampler_name=str(
                sampler_settings.get("sampler_name") or "euler_ancestral"
            ),
            scheduler=str(sampler_settings.get("scheduler") or "normal"),
            denoise=_runtime_helper("_as_float")(
                sampler_settings.get("denoise"), 1.0
            ),
            clip=clip,
            positive=positive,
        )
    )
    if not values:
        raise RuntimeError("[EasyUseAnima] DiTCFGFSGPatch returned no MODEL.")
    return values[0]


def _apply_aio_spectrum_forecast_patch_for_comfy_sampler(
    model,
    sampler_settings: dict[str, Any],
):
    spectrum = sampler_settings.get("spectrum", {})
    if not isinstance(spectrum, dict) or not _runtime_helper("_as_bool")(
        spectrum.get("enabled"), False
    ):
        return model
    node_id, patch_cls = _runtime_helper("_require_any_custom_node_class")(
        ("DiTSpectrumPatchAdvanced", "DiTSpectrumPatch"),
        "ComfyUI-Spectrum-KSampler",
        "Repository: https://github.com/blepping/ComfyUI-Spectrum-KSampler",
    )
    patcher = patch_cls()
    patch = getattr(patcher, "patch", None)
    if patch is None:
        raise RuntimeError(f"[EasyUseAnima] {node_id} does not expose patch().")
    patch_kwargs = {
        "model": model,
        "steps": _runtime_helper("_as_int")(sampler_settings.get("steps"), 28),
        "window_size": _runtime_helper("_as_float")(
            spectrum.get("window_size"), 2.0
        ),
        "flex_window": _runtime_helper("_as_float")(
            spectrum.get("flex_window"), 0.25
        ),
        "warmup_steps": _runtime_helper("_as_int")(
            spectrum.get("warmup_steps"), 6
        ),
        "tail_actual_steps": _runtime_helper("_as_int")(
            spectrum.get("tail_actual_steps"), 3
        ),
        "blend_w": _runtime_helper("_as_float")(spectrum.get("blend_w"), 0.3),
        "cheby_degree": _runtime_helper("_as_int")(
            spectrum.get("cheby_degree"), 3
        ),
        "ridge_lambda": _runtime_helper("_as_float")(
            spectrum.get("ridge_lambda"), 0.1
        ),
        "history_size": _runtime_helper("_as_int")(
            spectrum.get("history_size"), 100
        ),
        "enabled": True,
        "one_sampler_only": _runtime_helper("_as_bool")(
            spectrum.get("one_sampler_only"), False
        ),
        "verbose": _runtime_helper("_as_bool")(spectrum.get("verbose"), False),
        "compat_policy": str(spectrum.get("compat_policy") or "conservative"),
    }
    values = _runtime_helper("_node_output_tuple")(
        _runtime_helper("_call_with_supported_kwargs")(
            patch,
            (),
            patch_kwargs,
            f"{node_id}.patch()",
        )
    )
    if not values:
        raise RuntimeError(f"[EasyUseAnima] {node_id} returned no MODEL.")
    return values[0]


def _apply_aio_spectrum_model_patches_for_comfy_sampler(
    model,
    clip,
    positive,
    sampler_settings: dict[str, Any],
):
    patched = _runtime_helper(
        "_apply_aio_spectrum_correction_patch_for_comfy_sampler"
    )(
        model,
        clip,
        positive,
        sampler_settings,
    )
    return _runtime_helper("_apply_aio_spectrum_forecast_patch_for_comfy_sampler")(
        patched,
        sampler_settings,
    )


__all__ = ()
