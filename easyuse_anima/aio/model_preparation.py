"""AiO LoRA application, model patching, and variant lifecycle helpers."""

from __future__ import annotations

import json
import logging
from typing import Any

from ..common.serialization import _stable_change_key
from ..common.values import _as_bool, _as_float, _as_int
from ..infrastructure.comfy.invocation import (
    _call_with_supported_kwargs,
    _node_output_tuple,
)
from ..infrastructure.comfy.wiring import resolve_comfy_host_helper
from ..lora.metadata import _lora_stack_name
from .generation_lifecycle import StageModelPatchPlan
from .generation_migrations import (
    AIO_GENERATION_STAGE_IDS,
    AIO_MODEL_PATCH_ORDER_REVISION,
)

logger = logging.getLogger("ComfyUI-EasyUseAnima")


def _missing_host_helper(name: str):
    raise RuntimeError(
        f"[EasyUseAnima] AiO model preparation Comfy host helper is unavailable: {name}"
    )


def _find_comfy_node_class(node_id: str):
    helper = resolve_comfy_host_helper(
        "_find_comfy_node_class",
        _missing_host_helper,
    )
    return helper(node_id)


def _require_custom_node_class(
    node_id: str,
    node_pack: str,
    install_hint: str,
):
    helper = resolve_comfy_host_helper(
        "_require_custom_node_class",
        _missing_host_helper,
    )
    return helper(node_id, node_pack, install_hint)


def _require_any_custom_node_class(
    node_ids: tuple[str, ...],
    node_pack: str,
    install_hint: str,
):
    helper = resolve_comfy_host_helper(
        "_require_any_custom_node_class",
        _missing_host_helper,
    )
    return helper(node_ids, node_pack, install_hint)


def _patch_model_sampling_aura_flow(model, aura_settings: dict[str, Any]):
    aura_cls = _find_comfy_node_class("ModelSamplingAuraFlow")
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
        _as_float(aura_settings.get("shift"), 3.0),
    )
    values = _node_output_tuple(result)
    if not values:
        raise RuntimeError("[EasyUseAnima] ModelSamplingAuraFlow returned no MODEL.")
    return values[0]


def _apply_aio_kj_non_compile_patches(model, kj_settings: dict[str, Any]):
    patched = model
    if kj_settings.get("fp16_accumulation"):
        torch_settings_cls = _require_custom_node_class(
            "ModelPatchTorchSettings",
            "ComfyUI-KJNodes",
            "Repository: https://github.com/kijai/ComfyUI-KJNodes",
        )
        values = _node_output_tuple(torch_settings_cls().patch(patched, True))
        if not values:
            raise RuntimeError("[EasyUseAnima] ModelPatchTorchSettings returned no MODEL.")
        patched = values[0]

    sage_attention = str(kj_settings.get("sage_attention") or "disabled")
    if sage_attention != "disabled":
        sage_cls = _require_custom_node_class(
            "PathchSageAttentionKJ",
            "ComfyUI-KJNodes",
            "Repository: https://github.com/kijai/ComfyUI-KJNodes",
        )
        values = _node_output_tuple(
            sage_cls().patch(
                patched,
                sage_attention,
                _as_bool(kj_settings.get("sage_allow_compile"), False),
            )
        )
        if not values:
            raise RuntimeError("[EasyUseAnima] PathchSageAttentionKJ returned no MODEL.")
        patched = values[0]

    return patched


def _apply_aio_kj_torch_compile_patch(model, kj_settings: dict[str, Any]):
    compile_settings = kj_settings.get("torch_compile", {})
    if isinstance(compile_settings, dict) and compile_settings.get("enabled"):
        compile_cls = _require_custom_node_class(
            "TorchCompileModelAdvanced",
            "ComfyUI-KJNodes",
            "Repository: https://github.com/kijai/ComfyUI-KJNodes",
        )
        values = _node_output_tuple(
            compile_cls().patch(
                model,
                str(compile_settings.get("backend") or "inductor"),
                _as_bool(compile_settings.get("fullgraph"), False),
                str(compile_settings.get("mode") or "default"),
                str(compile_settings.get("dynamic") or "auto"),
                _as_int(compile_settings.get("dynamo_cache_size_limit"), 64),
                _as_bool(
                    compile_settings.get("compile_transformer_blocks_only"), True
                ),
                _as_bool(compile_settings.get("debug_compile_keys"), False),
                _as_bool(compile_settings.get("disable_dynamic_vram"), False),
            )
        )
        if not values:
            raise RuntimeError("[EasyUseAnima] TorchCompileModelAdvanced returned no MODEL.")
        return values[0]
    return model


def _apply_aio_kj_model_patches(model, kj_settings: dict[str, Any]):
    patched = _apply_aio_kj_non_compile_patches(model, kj_settings)
    return _apply_aio_kj_torch_compile_patch(patched, kj_settings)


def _aio_stage_model_patch_plan(
    settings: dict[str, Any],
    stage_id: str,
) -> StageModelPatchPlan:
    if stage_id not in AIO_GENERATION_STAGE_IDS:
        raise ValueError(f"Unknown AiO sampling stage: {stage_id}")
    model_patches = settings.get("model_patches", {})
    if not isinstance(model_patches, dict):
        model_patches = {}
    aura_settings = model_patches.get("aura_flow", {})
    if not isinstance(aura_settings, dict):
        aura_settings = {}
    dave_settings = model_patches.get("dave", {})
    if not isinstance(dave_settings, dict):
        dave_settings = {}
    safe_pag_settings = model_patches.get("safe_pag", {})
    if not isinstance(safe_pag_settings, dict):
        safe_pag_settings = {}
    kj_settings = model_patches.get("kj", {})
    if not isinstance(kj_settings, dict):
        kj_settings = {}

    dave_enabled = _as_bool(dave_settings.get("enabled"), False)
    stage_scope = dave_settings.get("stage_scope")
    dave_in_stage = dave_enabled and (
        _as_bool(stage_scope.get(stage_id), True)
        if isinstance(stage_scope, dict)
        else True
    )
    compile_settings = kj_settings.get("torch_compile", {})
    compile_enabled = (
        isinstance(compile_settings, dict)
        and _as_bool(compile_settings.get("enabled"), False)
    )
    safe_pag_enabled = _as_bool(safe_pag_settings.get("enabled"), False)
    fp16_enabled = _as_bool(kj_settings.get("fp16_accumulation"), False)
    sage_enabled = str(kj_settings.get("sage_attention") or "disabled") != "disabled"
    compile_before_dave = dave_in_stage and compile_enabled

    patch_ids = ["aura_flow"]
    if compile_before_dave:
        patch_ids.append("kj.torch_compile")
    if dave_in_stage:
        patch_ids.append("dave")
    if safe_pag_enabled:
        patch_ids.append("safe_pag")
    if fp16_enabled:
        patch_ids.append("kj.fp16_accumulation")
    if sage_enabled:
        patch_ids.append("kj.sage_attention")
    if compile_enabled and not compile_before_dave:
        patch_ids.append("kj.torch_compile")

    payload = {
        "order_revision": AIO_MODEL_PATCH_ORDER_REVISION,
        "aura_flow": dict(aura_settings),
        "dave": dict(dave_settings) if dave_in_stage else None,
        "safe_pag": dict(safe_pag_settings),
        "kj": dict(kj_settings),
        "compile_before_dave": compile_before_dave,
    }
    return StageModelPatchPlan(
        signature=_stable_change_key(payload),
        patch_ids=tuple(patch_ids),
        payload=payload,
    )


def _apply_aio_stage_model_patch_plan(model, plan: StageModelPatchPlan):
    payload = plan.payload
    if not isinstance(payload, dict):
        raise TypeError("AiO stage MODEL patch plan payload must be an object")
    aura_settings = payload.get("aura_flow", {})
    dave_settings = payload.get("dave")
    safe_pag_settings = payload.get("safe_pag", {})
    kj_settings = payload.get("kj", {})
    if not isinstance(aura_settings, dict):
        aura_settings = {}
    if not isinstance(safe_pag_settings, dict):
        safe_pag_settings = {}
    if not isinstance(kj_settings, dict):
        kj_settings = {}

    patched = _patch_model_sampling_aura_flow(
        model,
        aura_settings,
    )
    compile_before_dave = bool(payload.get("compile_before_dave"))
    if compile_before_dave:
        patched = _apply_aio_kj_torch_compile_patch(patched, kj_settings)
    if isinstance(dave_settings, dict):
        patched = _apply_aio_anima_dave_patch(patched, dave_settings)
    if _as_bool(
        safe_pag_settings.get("enabled"), False
    ):
        patched = _apply_aio_safe_pag_patch(patched, safe_pag_settings)
    if compile_before_dave:
        patched = _apply_aio_kj_non_compile_patches(patched, kj_settings)
    else:
        patched = _apply_aio_kj_model_patches(patched, kj_settings)
    return patched


def _apply_aio_model_patches(model, settings: dict[str, Any]):
    plan = _aio_stage_model_patch_plan(settings, "first_pass")
    return _apply_aio_stage_model_patch_plan(model, plan)


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
                _lora_stack_name(name),
                _as_float(model_strength, 1.0),
                _as_float(
                    clip_strength,
                    _as_float(model_strength, 1.0),
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
        for name, model_strength, clip_strength in _normalize_aio_lora_stack(
            lora_stack
        )
    ]


def _apply_aio_lora_stack(model, clip, lora_stack):
    entries = _normalize_aio_lora_stack(lora_stack)
    if not entries:
        return model, clip, []

    loader_cls = _find_comfy_node_class("LoraLoader")
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
        values = _node_output_tuple(
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
    dave_cls = _require_custom_node_class(
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
        _as_float(dave_settings.get("strength"), 0.30),
        _as_float(dave_settings.get("tau"), 0.10),
    )
    values = _node_output_tuple(result)
    if not values:
        raise RuntimeError("[EasyUseAnima] AnimaDAVE returned no MODEL.")
    return values[0]


def _apply_aio_safe_pag_patch(model, safe_pag_settings: dict[str, Any]):
    safe_pag_cls = _require_custom_node_class(
        "AnimaSafePAG",
        "Anima Safe PAG",
        "Repository: https://github.com/iljung1106/comfyui-anima-safe-pag",
    )
    if not isinstance(safe_pag_settings, dict):
        safe_pag_settings = {}
    result = safe_pag_cls().patch(
        model,
        _as_float(safe_pag_settings.get("scale"), 4.0),
        str(safe_pag_settings.get("block_indices") or "18"),
        _as_float(safe_pag_settings.get("perturbation_strength"), 0.75),
        str(safe_pag_settings.get("head_indices") or ""),
        _as_float(safe_pag_settings.get("start_percent"), 0.0),
        _as_float(safe_pag_settings.get("end_percent"), 0.7),
        _as_float(safe_pag_settings.get("rescale"), 0.2),
        str(safe_pag_settings.get("rescale_mode") or "full"),
    )
    values = _node_output_tuple(result)
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
            logger.debug(
                "[EasyUseAnima] failed to detach ephemeral AiO model clone: %s", exc
            )
    try:
        import comfy.model_management as model_management  # type: ignore

        unload = getattr(model_management, "unload_model_and_clones", None)
        if callable(unload):
            unload(model, unload_additional_models=True)
            return
    except Exception as exc:
        logger.debug(
            "[EasyUseAnima] failed to unload ephemeral AiO model clone: %s", exc
        )


def _apply_aio_spectrum_correction_patch_for_comfy_sampler(
    model,
    clip,
    positive,
    sampler_settings: dict[str, Any],
):
    corrections = sampler_settings.get("dit_corrections", {})
    if not isinstance(corrections, dict) or not _as_bool(
        corrections.get("enabled"), False
    ):
        return model
    patch_cls = _require_custom_node_class(
        "DiTCFGFSGPatch",
        "ComfyUI-Spectrum-KSampler",
        "Repository: https://github.com/blepping/ComfyUI-Spectrum-KSampler",
    )
    use_smc = _as_bool(corrections.get("smc_cfg"), False)
    use_cfgpp = _as_bool(corrections.get("cfgpp"), False)
    use_fsg = _as_bool(corrections.get("fsg"), False)
    values = _node_output_tuple(
        patch_cls().patch(
            model,
            True,
            str(corrections.get("dcw_mode") or "off"),
            _as_float(corrections.get("dcw_lambda"), 0.01),
            str(corrections.get("dcw_band_mask") or "LL"),
            str(corrections.get("dcw_calibrator") or "(auto-download default)"),
            use_smc,
            _as_float(corrections.get("adaptive_smc_alpha"), 0.0)
            if use_smc
            else 0.0,
            _as_float(corrections.get("smc_cfg_lambda"), 6.0)
            if use_smc
            else 0.0,
            use_cfgpp,
            _as_float(corrections.get("cfgpp_lambda"), 0.0)
            if use_cfgpp
            else 0.0,
            use_fsg,
            _as_float(corrections.get("fsg_band_lo"), 0.59),
            _as_float(corrections.get("fsg_band_hi"), 0.75),
            _as_int(corrections.get("fsg_k"), 3),
            _as_float(corrections.get("fsg_d_sigma"), 0.1),
            _as_float(corrections.get("fsg_gamma"), 0.0),
            _as_bool(corrections.get("replace_existing_cfg"), False),
            steps=_as_int(sampler_settings.get("steps"), 28),
            cfg=_as_float(sampler_settings.get("cfg"), 5.0),
            sampler_name=str(
                sampler_settings.get("sampler_name") or "euler_ancestral"
            ),
            scheduler=str(sampler_settings.get("scheduler") or "normal"),
            denoise=_as_float(sampler_settings.get("denoise"), 1.0),
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
    if not isinstance(spectrum, dict) or not _as_bool(
        spectrum.get("enabled"), False
    ):
        return model
    node_id, patch_cls = _require_any_custom_node_class(
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
        "steps": _as_int(sampler_settings.get("steps"), 28),
        "window_size": _as_float(spectrum.get("window_size"), 2.0),
        "flex_window": _as_float(spectrum.get("flex_window"), 0.25),
        "warmup_steps": _as_int(spectrum.get("warmup_steps"), 6),
        "tail_actual_steps": _as_int(spectrum.get("tail_actual_steps"), 3),
        "blend_w": _as_float(spectrum.get("blend_w"), 0.3),
        "cheby_degree": _as_int(spectrum.get("cheby_degree"), 3),
        "ridge_lambda": _as_float(spectrum.get("ridge_lambda"), 0.1),
        "history_size": _as_int(spectrum.get("history_size"), 100),
        "enabled": True,
        "one_sampler_only": _as_bool(spectrum.get("one_sampler_only"), False),
        "verbose": _as_bool(spectrum.get("verbose"), False),
        "compat_policy": str(spectrum.get("compat_policy") or "conservative"),
    }
    values = _node_output_tuple(
        _call_with_supported_kwargs(
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
    patched = _apply_aio_spectrum_correction_patch_for_comfy_sampler(
        model,
        clip,
        positive,
        sampler_settings,
    )
    return _apply_aio_spectrum_forecast_patch_for_comfy_sampler(
        patched,
        sampler_settings,
    )


__all__ = ()
