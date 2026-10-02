"""Sampling-scoped rollback for the reviewed LuciferTC IP-Adapter implementation."""

from contextlib import contextmanager
from threading import RLock


_LOCK = RLock()
_MISSING = object()
_MODEL_ATTRS = ("shared_ip_k_proj", "shared_ip_v_proj", "shared_ip_q_proj")
_BLOCK_ATTRS = (
    "ip_k_proj", "ip_v_proj", "adaln_ip", "use_ip_adapter", "ip_norm_keys",
    "ip_inject_before_mlp", "ip_k_norm", "ip_q_proj", "ip_q_norm",
    "_ip_hook_installed", "_ip_fwd_patched", "_x_cross_flat",
)
_LAYERS = ("q_proj", "k_proj", "v_proj", "output_proj")
_ENCODERS = ("siglip_encoder", "siglip_norm", "siglip_compressor", "ip_self_attn")


def validate_clean_model(model, adapter):
    """Reject states that upstream would overwrite without a reversible API."""
    dit = model.model.diffusion_model
    blocks = getattr(dit, "blocks", ())
    if len(blocks) != 28 or adapter.get("num_blocks") != 28:
        raise RuntimeError("Anima IP-Adapter Hook currently requires a 28-block Anima model and adapter.")
    if any(hasattr(dit, name) for name in _MODEL_ATTRS):
        raise RuntimeError("Anima IP-Adapter Hook requires a model without an existing IP-Adapter patch.")
    for block in blocks:
        if any(hasattr(block, name) for name in _BLOCK_ATTRS):
            raise RuntimeError("Anima IP-Adapter Hook requires clean blocks; restart after using external Apply.")
        if hasattr(block, "_orig_mod") or "forward" in vars(block):
            raise RuntimeError("Anima IP-Adapter Hook does not support compiled or replaced block forwards.")
        for name in _LAYERS:
            layer = getattr(block.cross_attn, name, None)
            if layer is None or type(layer).__name__ == "_LoRALinear":
                raise RuntimeError("Anima IP-Adapter Hook found an unsupported cross-attention layer.")
    for layers in adapter.get("lora_weights", {}).values():
        if set(layers) - set(_LAYERS):
            raise RuntimeError("IP-Adapter checkpoint contains unsupported LoRA target layers.")
    if adapter.get("ip_inject_before_mlp") or any(
        key.startswith("shared_ip_q_proj") for key in adapter.get("ip_weights", {})
    ):
        raise RuntimeError("This IP-Adapter checkpoint requires an unsupported injection architecture.")
    return dit


@contextmanager
def temporary_ipadapter(model, adapter):
    """Restore even partial Apply mutations before leaving the sampler.

    Only fresh IP modules may be created. No original parameter values are copied
    or overwritten. The lock serializes this integration's uses of shared modules.
    """
    with _LOCK:
        dit = validate_clean_model(model, adapter)
        snapshots = []
        for block in dit.blocks:
            attn = block.cross_attn
            snapshots.append((
                block, vars(block).get("forward", _MISSING),
                {name: getattr(attn, name) for name in _LAYERS},
                set(attn._forward_pre_hooks),
            ))
        placements = []
        for name in _ENCODERS:
            module = adapter.get(name)
            if module is not None:
                devices = {t.device for t in (*module.parameters(), *module.buffers())}
                if len(devices) != 1:
                    raise RuntimeError("IP-Adapter encoder modules must each reside on one device.")
                placements.append((module, next(iter(devices))))
        try:
            yield
        finally:
            for block, forward, layers, hook_ids in reversed(snapshots):
                attn = block.cross_attn
                for key in set(attn._forward_pre_hooks) - hook_ids:
                    attn._forward_pre_hooks.pop(key, None)
                    attn._forward_pre_hooks_with_kwargs.pop(key, None)
                for name, layer in layers.items():
                    setattr(attn, name, layer)
                if forward is _MISSING:
                    if "forward" in vars(block):
                        delattr(block, "forward")
                else:
                    block.forward = forward
                for name in _BLOCK_ATTRS:
                    if hasattr(block, name):
                        delattr(block, name)
            for name in _MODEL_ATTRS:
                if hasattr(dit, name):
                    delattr(dit, name)
            for module, device in placements:
                module.to(device)


__all__ = ()
