"""Native Anima Safe PAG, adapted from iljung1106/comfyui-anima-safe-pag.

Upstream 905b0107d1f924fc6acbcac3b6a879b566ff671c; MIT notice and changes are
shipped in third_party/anima-safe-pag/. No extra model weights are required.
"""

from contextlib import contextmanager
from contextvars import ContextVar
from threading import RLock
from types import MethodType
from typing import Any

import torch  # type: ignore
import torch.nn.functional as F  # type: ignore


def _calculate_condition_batch(args):
    import comfy.samplers  # type: ignore

    return comfy.samplers.calc_cond_batch(
        args["model"],
        args["conds"],
        args["input"],
        args["sigma"],
        args["model_options"],
    )


def _sigma_to_float(sigma):
    if torch.is_tensor(sigma):
        return float(sigma.flatten()[0].item())
    return float(sigma)


def _sigma_active(sigma, sigma_start, sigma_end):
    sigma_start = _sigma_to_float(sigma_start)
    sigma_end = _sigma_to_float(sigma_end)
    if sigma_start < sigma_end:
        sigma_start, sigma_end = sigma_end, sigma_start

    value = _sigma_to_float(sigma)
    return sigma_end <= value <= sigma_start


def _percent_range_to_sigmas(model, start_percent, end_percent):
    start_percent = max(0.0, min(1.0, float(start_percent)))
    end_percent = max(0.0, min(1.0, float(end_percent)))
    if start_percent > end_percent:
        start_percent, end_percent = end_percent, start_percent

    model_sampling = model.get_model_object("model_sampling")
    sigma_start = model_sampling.percent_to_sigma(start_percent)
    sigma_end = model_sampling.percent_to_sigma(end_percent)
    return sigma_start, sigma_end, start_percent, end_percent


def _parse_indices(text, max_index):
    values = set()
    for raw_part in str(text).split(","):
        part = raw_part.strip()
        if not part:
            continue

        if "-" in part:
            pieces = [p.strip() for p in part.split("-", 1)]
            if len(pieces) != 2 or not pieces[0] or not pieces[1]:
                raise RuntimeError(
                    f"Invalid block range '{part}'. Use values like 18 or 18,20,22."
                )
            start, end = int(pieces[0]), int(pieces[1])
            if end < start:
                start, end = end, start
            values.update(range(start, end + 1))
        else:
            values.add(int(part))

    indices = sorted(i for i in values if 0 <= i <= max_index)
    if not indices:
        raise RuntimeError(
            f"No valid block indices found. Valid range is 0 to {max_index}."
        )
    return indices


def _parse_optional_indices(text, max_index):
    if text is None or not str(text).strip():
        return None
    return _parse_indices(text, max_index)


def _get_anima_blocks(model):
    getter = getattr(model, "get_model_object", None)
    diffusion_model = (
        getter("diffusion_model") if callable(getter) else getattr(model, "diffusion_model", None)
    )
    blocks = getattr(diffusion_model, "blocks", None)
    if blocks is None:
        raise RuntimeError(
            "Anima Safe PAG expects an Anima/Cosmos/Predict2-style model with diffusion_model.blocks."
        )
    return blocks


def _expand_cond_labels(transformer_options, batch_size, device):
    labels = transformer_options.get("anima_safe_pag_cond_or_uncond", None)
    if labels is None:
        labels = transformer_options.get("cond_or_uncond", None)
    if not isinstance(labels, (list, tuple)) or len(labels) == 0:
        return None

    if len(labels) == batch_size:
        expanded = list(labels)
    elif batch_size % len(labels) == 0:
        repeat = batch_size // len(labels)
        expanded = []
        for label in labels:
            expanded.extend([label] * repeat)
    else:
        return None

    return torch.tensor(expanded, device=device)


def _project_attention(attn_module, attn):
    value = attn.reshape(*attn.shape[:-2], attn.shape[-2] * attn.shape[-1])
    if hasattr(attn_module, "output_proj"):
        value = attn_module.output_proj(value)
        if hasattr(attn_module, "output_dropout"):
            value = attn_module.output_dropout(value)
        return value

    if hasattr(attn_module, "o_proj"):
        return attn_module.o_proj(value)

    raise RuntimeError("Unsupported attention module: no output projection found.")


def _sdpa_attention(q, k, v):
    return F.scaled_dot_product_attention(
        q.transpose(1, 2),
        k.transpose(1, 2),
        v.transpose(1, 2),
        dropout_p=0.0,
        is_causal=False,
    ).transpose(1, 2)


def _lerp_heads(base, target, strength, heads):
    strength = max(0.0, min(1.0, float(strength)))
    if strength <= 0:
        return base

    if heads is None:
        return base.lerp(target, strength)

    out = base.clone()
    out[:, :, heads, :] = base[:, :, heads, :].lerp(target[:, :, heads, :], strength)
    return out


def _soft_pag_attention(attn_module, q, k, v, strength, heads):
    normal = _sdpa_attention(q, k, v)
    weak = _lerp_heads(normal, v, strength, heads)
    return _project_attention(attn_module, weak)


def _make_pag_compute_attention(
    attn_module, original_compute, pag_index, perturbation_strength, head_indices, token
):
    def compute_attention(self, q, k, v, transformer_options=None):
        transformer_options = transformer_options or {}
        if transformer_options.get("easyuse_anima_safe_pag_token") is not token:
            return original_compute(q, k, v, transformer_options=transformer_options)
        labels = _expand_cond_labels(transformer_options, q.shape[0], q.device)
        if labels is None:
            return original_compute(q, k, v, transformer_options=transformer_options)

        pag_mask = labels == pag_index
        if not bool(pag_mask.any()):
            return original_compute(q, k, v, transformer_options=transformer_options)

        perturbed = _soft_pag_attention(
            self, q, k, v, perturbation_strength, head_indices
        )
        if bool(pag_mask.all()):
            return perturbed

        normal = original_compute(q, k, v, transformer_options=transformer_options)
        normal = normal.clone()
        normal[pag_mask] = perturbed[pag_mask]
        return normal

    return MethodType(compute_attention, attn_module)


# All native Safe PAG instances share model modules through ModelPatcher clones.
# Serialize temporary replacement; a per-call token also isolates unpatched calls.
_ATTENTION_LOCK = RLock()


@contextmanager
def _patch_anima_attention(
    blocks, indices, pag_index, perturbation_strength, head_indices, token
):
    patched = []
    seen = set()
    with _ATTENTION_LOCK:
        try:
            for idx in indices:
                attn = getattr(blocks[idx], "self_attn", None)
                if attn is None or not callable(
                    getattr(attn, "compute_attention", None)
                ):
                    raise RuntimeError(
                        f"Block {idx} does not expose self_attn.compute_attention."
                    )
                if id(attn) in seen:
                    continue
                seen.add(id(attn))
                original = attn.compute_attention
                heads = _parse_optional_indices(head_indices, attn.n_heads - 1)
                replacement = _make_pag_compute_attention(
                    attn,
                    original,
                    pag_index,
                    perturbation_strength,
                    heads,
                    token,
                )
                patched.append(
                    (
                        attn,
                        "compute_attention" in vars(attn),
                        vars(attn).get("compute_attention"),
                    )
                )
                attn.compute_attention = replacement
            yield
        finally:
            for attn, had_instance_value, original_value in reversed(patched):
                if had_instance_value:
                    attn.compute_attention = original_value
                else:
                    delattr(attn, "compute_attention")


def _rescale_guidance(guidance, cond_pred, cfg_result, rescale, mode):
    rescale = float(rescale)
    if rescale <= 0:
        return guidance

    guidance_result = cfg_result + guidance if mode == "full" else cond_pred + guidance
    reduce_dims = tuple(range(1, guidance_result.ndim))
    std_cond = torch.std(cond_pred, dim=reduce_dims, keepdim=True).clamp_min(1e-6)
    std_guidance = torch.std(guidance_result, dim=reduce_dims, keepdim=True).clamp_min(
        1e-6
    )
    factor = std_cond / std_guidance
    factor = rescale * factor + (1.0 - rescale)
    return guidance * factor


class _PAGRun:
    def __init__(
        self,
        model,
        scale,
        block_indices,
        perturbation_strength,
        head_indices,
        start_percent,
        end_percent,
        rescale,
        rescale_mode,
    ):
        self.scale = scale
        self.perturbation_strength = perturbation_strength
        self.head_indices = head_indices
        self.rescale = rescale
        self.rescale_mode = rescale_mode
        self.sigma_start, self.sigma_end, self.start_percent, self.end_percent = (
            _percent_range_to_sigmas(model, start_percent, end_percent)
        )
        self.indices = _parse_indices(block_indices, len(_get_anima_blocks(model)) - 1)
        previous = model.model_options.get("sampler_calc_cond_batch_function")
        previous_owner = getattr(previous, "__self__", None)
        self.previous_calc = (
            previous_owner.previous_calc
            if isinstance(previous_owner, _PAGRun)
            else previous
        )
        self.prediction: ContextVar[Any] = ContextVar(
            "easyuse_safe_pag_prediction", default=None
        )
        self.token = object()
        self.state = dict(
            warned_short_output=False,
            warned_shape=False,
            printed_active=False,
            printed_delta=False,
        )

    def default_calc(self, args):
        return _calculate_condition_batch(args)

    def calc_with_previous_if_possible(self, args, expected_len):
        if self.previous_calc is None:
            return self.default_calc(args)

        outputs = self.previous_calc(args)
        if len(outputs) >= expected_len:
            return outputs

        if not self.state["warned_short_output"]:
            print(
                "[Easy Anima Safe PAG] Previous sampler_calc_cond_batch_function returned too few "
                "predictions for the padded batch. Falling back to ComfyUI calc_cond_batch."
            )
            self.state["warned_short_output"] = True
        return self.default_calc(args)

    def calc_cond_batch_with_pag(self, args):
        conds = list(args["conds"])
        self.prediction.set(None)

        if self.scale == 0 or not conds or conds[0] is None:
            if self.previous_calc is not None:
                return self.previous_calc(args)
            return self.default_calc(args)

        active = _sigma_active(args["sigma"], self.sigma_start, self.sigma_end)
        pag_index = len(conds)
        extended_args = dict(args)
        extended_args["conds"] = conds + [conds[0]]

        model_options = dict(args.get("model_options", {}))
        previous_wrapper = model_options.get("model_function_wrapper", None)

        def pag_model_wrapper(model_function, kwargs):
            kwargs = kwargs.copy()
            true_labels = list(kwargs.get("cond_or_uncond", []))
            kwargs["cond_or_uncond"] = true_labels

            c = kwargs.get("c", {}).copy()
            transformer_options = c.get("transformer_options", {}).copy()
            transformer_options["easyuse_anima_safe_pag_token"] = self.token
            transformer_options["anima_safe_pag_cond_or_uncond"] = true_labels
            transformer_options["cond_or_uncond"] = true_labels
            c["transformer_options"] = transformer_options
            kwargs["c"] = c

            if previous_wrapper is not None:
                return previous_wrapper(model_function, kwargs)
            return model_function(kwargs["input"], kwargs["timestep"], **kwargs["c"])

        model_options["model_function_wrapper"] = pag_model_wrapper
        extended_args["model_options"] = model_options

        if active:
            live_blocks = _get_anima_blocks(args["model"])
            with _patch_anima_attention(
                live_blocks,
                self.indices,
                pag_index,
                self.perturbation_strength,
                self.head_indices,
                self.token,
            ):
                outputs = self.calc_with_previous_if_possible(
                    extended_args, pag_index + 1
                )
        else:
            outputs = self.calc_with_previous_if_possible(extended_args, pag_index + 1)

        if len(outputs) <= pag_index:
            raise RuntimeError(
                "Anima Safe PAG did not receive the padded prediction. "
                "This usually means another sampler_calc_cond_batch_function consumed the extended condition list."
            )

        if active:
            self.prediction.set(outputs[pag_index])
            if not self.state["printed_active"]:
                print(
                    "[Easy Anima Safe PAG] active: "
                    f"blocks={self.indices}, strength={float(self.perturbation_strength):.3f}, "
                    f"heads={'all' if not str(self.head_indices).strip() else str(self.head_indices).strip()}, "
                    f"range={float(self.start_percent):.3f}-{float(self.end_percent):.3f}, "
                    f"conds={len(conds)}+pag"
                )
                self.state["printed_active"] = True
        return outputs[: len(conds)]

    def post_cfg_function(self, args):
        cfg_result = args["denoised"]
        if self.scale == 0 or not _sigma_active(
            args["sigma"], self.sigma_start, self.sigma_end
        ):
            return cfg_result

        pag_pred = self.prediction.get()
        self.prediction.set(None)
        if pag_pred is None:
            return cfg_result

        cond_pred = args["cond_denoised"]
        if pag_pred.shape != cond_pred.shape:
            if not self.state["warned_shape"]:
                print(
                    "[Easy Anima Safe PAG] Skipping this step because the perturbed prediction "
                    f"shape {tuple(pag_pred.shape)} does not match cond shape {tuple(cond_pred.shape)}."
                )
                self.state["warned_shape"] = True
            return cfg_result

        guidance = (cond_pred - pag_pred) * float(self.scale)
        if not self.state["printed_delta"]:
            delta = (cond_pred - pag_pred).detach().abs().mean().item()
            print(
                "[Easy Anima Safe PAG] first-step mean |cond - pag| = "
                f"{delta:.8f}; scale={float(self.scale):.3f}"
            )
            self.state["printed_delta"] = True

        guidance = _rescale_guidance(
            guidance, cond_pred, cfg_result, float(self.rescale), self.rescale_mode
        )
        return cfg_result + guidance


class NativeSafePAG:
    def patch(
        self,
        model,
        scale,
        block_indices,
        perturbation_strength,
        head_indices,
        start_percent,
        end_percent,
        rescale,
        rescale_mode,
    ):
        if float(scale) == 0:
            return (model,)
        patched = model.clone()
        run = _PAGRun(
            patched,
            scale,
            block_indices,
            perturbation_strength,
            head_indices,
            start_percent,
            end_percent,
            rescale,
            rescale_mode,
        )
        patched.model_options["sampler_post_cfg_function"] = [
            callback
            for callback in patched.model_options.get("sampler_post_cfg_function", [])
            if not isinstance(getattr(callback, "__self__", None), _PAGRun)
        ]
        patched.set_model_sampler_calc_cond_batch_function(run.calc_cond_batch_with_pag)
        patched.set_model_sampler_post_cfg_function(run.post_cfg_function)
        return (patched,)
