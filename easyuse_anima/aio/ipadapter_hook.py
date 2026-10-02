"""Optional bridge to LuciferTC's installed Anima IP-Adapter node pack."""

import hashlib
import inspect
from pathlib import Path
from typing import Any, cast

from ..infrastructure.comfy.capabilities import _find_comfy_node_class
from .hooks.contracts import (
    AioHookDescriptor, AioHookPatch, AioHookPoint, AioHookSessionBase,
    AioStage, AioStagePhase,
)
from .ipadapter_lifecycle import temporary_ipadapter, validate_clean_model


UPSTREAM_COMMIT = "6b77cd0c367d76402174ace2be50d3cb6aa77855"
_SOURCE_SHA256 = "521ce9082fa803419851820f4768fb550c0bc0f334c8d1d08199111920fd77be"
_WRAPPER_KEY = "easyuse_anima.ipadapter"


def resolve_apply():
    cls = _find_comfy_node_class("AnimaIPAdapterApply")
    if cls is None:
        raise RuntimeError(
            "Install/enable LuciferTC9527/ComfyUI-Anima_IP-Adapter and restart ComfyUI "
            "to use Easy Anima IP-Adapter Hook."
        )
    path = inspect.getsourcefile(cls)
    source = Path(path).read_bytes().replace(b"\r\n", b"\n") if path else b""
    if hashlib.sha256(source).hexdigest() != _SOURCE_SHA256:
        raise RuntimeError(
            "Unsupported Anima IP-Adapter implementation. This integration requires "
            f"LuciferTC9527/ComfyUI-Anima_IP-Adapter at {UPSTREAM_COMMIT}; "
            "other revisions require a lifecycle compatibility review."
        )
    if cls.FUNCTION != "apply" or cls.RETURN_TYPES != ("MODEL",):
        raise RuntimeError("Unexpected Anima IP-Adapter Apply node contract.")
    return cls


def validate_options(options):
    if options.get("registered_hooks"):
        raise RuntimeError("IP-Adapter Hook does not support scheduled conditioning/weight hooks.")
    if options.get("model_function_wrapper") is not None:
        raise RuntimeError("IP-Adapter cannot replace an existing model wrapper; disable the conflicting patch.")
    if any(options.get(key) for key in (
        "sampler_cfg_function", "sampler_post_cfg_function",
        "sampler_pre_cfg_function", "sampler_calc_cond_batch_function",
    )):
        raise RuntimeError("IP-Adapter Hook currently requires standard CFG (disable other CFG patches).")
    transformer = options.get("transformer_options", {})
    if transformer.get("wrappers", {}).get("sampler_sample", {}).get(_WRAPPER_KEY):
        raise RuntimeError("Connect only one IP-Adapter Hook to each AiO Generator.")


class IPAdapterSample:
    def __init__(self, adapter, image, settings):
        self.adapter, self.image, self.settings = adapter, image, settings

    def __call__(self, executor, guider, sigmas, extra_args, callback, noise, *args, **kwargs):
        import comfy.model_patcher  # type: ignore

        model = guider.model_patcher
        if getattr(model, "hook_patches", {}):
            raise RuntimeError("IP-Adapter Hook does not support scheduled weight patches.")
        if getattr(model, "additional_models", {}).get("multigpu"):
            raise RuntimeError("Anima IP-Adapter Hook does not support multi-GPU sampling.")
        if noise.shape[0] != 1:
            raise RuntimeError("Anima IP-Adapter Hook supports generation batch size 1 only.")
        if model.model.model_lowvram:
            raise RuntimeError("Anima IP-Adapter Hook requires a fully loaded model; use --highvram.")
        if any(p.device != model.load_device for p in model.model.diffusion_model.parameters()):
            raise RuntimeError("Anima IP-Adapter Hook requires all diffusion weights on the sampling GPU.")
        # The wrapper itself is expected here; reject patches added after hook construction.
        options = comfy.model_patcher.create_model_options_clone(extra_args["model_options"])
        options.get("transformer_options", {}).get("wrappers", {}).get("sampler_sample", {}).pop(_WRAPPER_KEY, None)
        validate_options(options)
        apply_cls = resolve_apply()
        with temporary_ipadapter(model, self.adapter):
            apply_model = model.clone()
            apply_model.model_options = options
            patched, = apply_cls().apply(apply_model, self.adapter, self.image, **self.settings)
            sample_args = dict(extra_args, model_options=patched.model_options)
            return executor(guider, sigmas, sample_args, callback, noise, *args, **kwargs)


class IPAdapterSession(AioHookSessionBase):
    def __init__(self, definition):
        self.definition = definition

    def before_stage(self, event):
        import torch  # type: ignore
        from comfy.patcher_extension import WrappersMP  # type: ignore

        model = cast(Any, event.state.model)
        settings = cast(dict[str, Any], event.request.settings)
        sampler = settings.get("sampler", {})
        if sampler.get("backend") != "comfy_ksampler" or sampler.get("spectrum", {}).get("enabled"):
            raise RuntimeError("IP-Adapter Hook currently requires the ComfyUI sampler with Spectrum disabled.")
        kj = settings.get("model_patches", {}).get("kj", {})
        if kj.get("torch_compile", {}).get("enabled"):
            raise RuntimeError("Disable Torch Compile when using Anima IP-Adapter Hook.")
        if model.is_dynamic():
            raise RuntimeError("Anima IP-Adapter Hook requires ComfyUI --disable-dynamic-vram.")
        device = model.load_device
        if device.type != "cuda" or device.index not in (None, torch.cuda.current_device()):
            raise RuntimeError("Anima IP-Adapter Hook requires the default CUDA device.")
        if getattr(model, "additional_models", {}).get("multigpu"):
            raise RuntimeError("Anima IP-Adapter Hook does not support multi-GPU sampling.")
        validate_options(model.model_options)
        if model.get_wrappers(WrappersMP.SAMPLER_SAMPLE, _WRAPPER_KEY):
            raise RuntimeError("Connect only one IP-Adapter Hook to each AiO Generator.")
        validate_clean_model(model, self.definition.adapter)
        patched = model.clone()
        patched.add_wrapper_with_key(
            WrappersMP.SAMPLER_SAMPLE, _WRAPPER_KEY,
            IPAdapterSample(self.definition.adapter, self.definition.image, self.definition.settings),
        )
        return AioHookPatch(model=patched, metadata={
            "upstream_commit": UPSTREAM_COMMIT, "stage": "first_pass",
            "settings": dict(self.definition.settings),
        })


class IPAdapterHook:
    def __init__(self, adapter, image, settings):
        resolve_apply()
        if len(image.shape) != 4 or image.shape[0] != 1 or image.shape[-1] != 3:
            raise RuntimeError("Anima IP-Adapter Hook requires one RGB reference image.")
        self.adapter, self.image, self.settings = adapter, image, settings

    def describe(self):
        return AioHookDescriptor(
            hook_id="easyuse_anima.ipadapter", hook_version="1.0.0",
            points=frozenset({AioHookPoint(AioStage.FIRST_PASS, AioStagePhase.BEFORE)}),
            # Mutable external weights and image tensors are not a serializable cache key.
            fingerprint=None,
        )

    def create_session(self, context):
        return IPAdapterSession(self)


__all__ = ()
