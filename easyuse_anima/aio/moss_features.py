"""MOSS settings and adapters for ComfyUI's public prompt and SLG nodes."""

from __future__ import annotations

import inspect
import json
import math
import re
from copy import deepcopy

from ..infrastructure.comfy.invocation import _node_output_tuple
from ..infrastructure.comfy.wiring import resolve_comfy_host_helper

MOSS_FEATURE_DEFAULTS = {
    "slg": {
        "mode": "off", "layers": "22", "scale": 3.0,
        "start_percent": 0.0, "end_percent": 1.0,
        "stage_scope": {"first_pass": True, "highres": True, "detailer": True, "upscale": True},
    },
    "prompt": {
        "mode": "original", "layout_json": "", "max_length": 512, "seed": 0,
        "temperature": 0.7, "top_k": 64, "top_p": 0.95, "min_p": 0.05,
        "repetition_penalty": 1.05,
    },
}
MOSS_PROMPT_SYSTEM = (
    "Expand the user's image idea into one precise English scene caption. "
    "Preserve all requested subjects, relationships, style, and visible text exactly. "
    "Describe spatial placement clearly. Do not add unrequested people or rewrite quoted text. "
    "Return only the caption, without explanations, headings, JSON, or markdown."
)


def _merge(defaults, value):
    if value is None:
        value = {}
    if not isinstance(value, dict):
        raise ValueError("[EasyUseAnima] MOSS feature settings must be an object.")
    result = deepcopy(value)
    for key, default in defaults.items():
        result[key] = _merge(default, value.get(key)) if isinstance(default, dict) else value.get(key, default)
    return result


def _number(value, low, high, name, *, integer=False):
    try:
        number = int(value) if integer else float(value)
        valid = not isinstance(value, bool) and math.isfinite(number) and low <= number <= high
        if integer and isinstance(value, float):
            valid = valid and value.is_integer()
    except (TypeError, ValueError, OverflowError):
        valid = False
    if not valid:
        raise ValueError(f"[EasyUseAnima] MOSS {name} must be between {low} and {high}.")
    return number


def normalize_moss_settings(value):
    """Fill missing fields without touching inactive model banks or future fields."""
    result = _merge(MOSS_FEATURE_DEFAULTS, value)
    slg, prompt = result["slg"], result["prompt"]
    if slg["mode"] not in ("off", "uncond", "standard"):
        raise ValueError("[EasyUseAnima] Unknown MOSS SLG mode; select off, uncond, or standard.")
    if prompt["mode"] not in ("original", "enhance", "layout"):
        raise ValueError("[EasyUseAnima] Unknown MOSS prompt mode; select original, enhance, or layout.")
    if slg["mode"] != "off":
        if not isinstance(slg["layers"], str) or not re.fullmatch(r"\s*\d+(?:\s*,\s*\d+)*\s*", slg["layers"]):
            raise ValueError("[EasyUseAnima] MOSS SLG layers must be comma-separated, zero-based indices.")
        for name, high in (("scale", 10), ("start_percent", 1), ("end_percent", 1)):
            slg[name] = _number(slg[name], 0, high, name)
        if slg["start_percent"] > slg["end_percent"]:
            raise ValueError("[EasyUseAnima] MOSS SLG start_percent must not exceed end_percent.")
        if any(type(slg["stage_scope"][stage]) is not bool for stage in MOSS_FEATURE_DEFAULTS["slg"]["stage_scope"]):
            raise ValueError("[EasyUseAnima] MOSS SLG stage switches must be booleans.")
    if prompt["mode"] == "enhance":
        for name, low, high, integer in (
            ("max_length", 1, 32768, True), ("seed", 0, 0xffffffffffffffff, True),
            ("temperature", 0.01, 2, False), ("top_k", 0, 1000, True),
            ("top_p", 0, 1, False), ("min_p", 0, 1, False), ("repetition_penalty", 0, 5, False),
        ):
            number = _number(prompt[name], low, high, name, integer=integer)
            # Preserve uint64 strings through JavaScript's finite-precision JSON numbers.
            prompt[name] = str(number) if name == "seed" and isinstance(prompt[name], str) else number
    return result


def moss_settings(settings):
    banks = settings.get("model_settings", {})
    return normalize_moss_settings(banks.get("moss_image", {}))


def moss_slg_settings(settings, stage_id):
    if settings.get("model_family", "anima") != "moss_image":
        return None
    slg = moss_settings(settings)["slg"]
    if slg["mode"] == "off" or not slg["stage_scope"].get(stage_id, False):
        return None
    return {key: value for key, value in slg.items() if key != "stage_scope"}


def moss_feature_provider(feature, mode=None, node_lookup=None):
    if feature == "slg":
        node_id = "SkipLayerGuidanceDiT" if mode == "standard" else "SkipLayerGuidanceDiTSimple"
        names = ("model", "start_percent", "end_percent", "double_layers", "single_layers")
        if mode == "standard":
            names = (*names, "scale", "rescaling_scale")
    elif feature == "prompt_enhance":
        node_id = "TextGenerate"
        names = ("clip", "prompt", "max_length", "sampling_mode", "thinking", "use_default_template", "system_prompt")
    else:
        return None, "unsupported"
    lookup = node_lookup or resolve_comfy_host_helper("_find_comfy_node_class", lambda _name: None)
    node = lookup(node_id)
    if node is None:
        return None, "missing_dependency"
    try:
        signature = inspect.signature(node.execute)
        if not all(name in signature.parameters for name in names):
            return None, "incompatible"
        signature.bind(**dict.fromkeys(names))
    except (AttributeError, TypeError, ValueError):
        return None, "incompatible"
    return node, "available"


def apply_moss_slg(model, slg_settings, node_lookup=None):
    if not slg_settings or slg_settings.get("mode", "off") == "off":
        return model
    mode = slg_settings["mode"]
    node, status = moss_feature_provider("slg", mode, node_lookup)
    if node is None:
        raise RuntimeError(f"[EasyUseAnima] MOSS {mode} SLG node is {status}; update ComfyUI.")
    dit = model.get_model_object("diffusion_model")
    layers = getattr(dit, "layers", ())
    if any(int(layer) >= len(layers) for layer in slg_settings["layers"].split(",")):
        raise ValueError("[EasyUseAnima] MOSS SLG layer index exceeds this model's layer count.")
    kwargs = {
        "model": model, "single_layers": slg_settings["layers"], "double_layers": "",
        "start_percent": slg_settings["start_percent"], "end_percent": slg_settings["end_percent"],
    }
    if mode == "standard":
        kwargs.update(scale=slg_settings["scale"], rescaling_scale=0.0)
    values = _node_output_tuple(node.execute(**kwargs))
    if len(values) != 1:
        raise RuntimeError("[EasyUseAnima] MOSS SLG must return one MODEL.")
    return values[0]


def _layout_object(text, *, required=False):
    try:
        value = json.loads(text)
    except (TypeError, ValueError):
        value = None
    error = "[EasyUseAnima] MOSS Layout needs summary.caption and items with label, caption, and four finite yxyx bbox coordinates in abs_centralized pixels."
    if not isinstance(value, dict) or "summary" not in value or "items" not in value:
        if required:
            raise ValueError(error)
        return None
    valid = isinstance(value["summary"], dict) and isinstance(value["summary"].get("caption"), str) and isinstance(value["items"], list)
    if valid:
        valid = value.get("bbox_format", "yxyx") == "yxyx" and value.get("bbox_coord_space", "abs_centralized") == "abs_centralized"
    for item in value["items"] if valid else ():
        bbox = item.get("bbox") if isinstance(item, dict) else None
        valid = isinstance(bbox, list) and len(bbox) == 4 and all(type(n) in (int, float) and math.isfinite(n) for n in bbox)
        valid = valid and isinstance(item.get("label"), str) and isinstance(item.get("caption"), str)
        if not valid:
            break
    if not valid:
        raise ValueError(error)
    return value


def validate_moss_prompt(positive_prompt, settings):
    """Validate incompatible text transformations before loading model resources."""
    if settings.get("model_family", "anima") != "moss_image":
        return "original", positive_prompt
    prompt = moss_settings(settings)["prompt"]
    mode = prompt["mode"]
    source = str(prompt["layout_json"] or positive_prompt) if mode == "layout" else positive_prompt
    layout = _layout_object(source, required=mode == "layout")
    if layout is not None:
        if mode == "enhance":
            raise ValueError("[EasyUseAnima] MOSS Layout JSON must use Original or Layout mode; caption enhancement would rewrite the layout.")
        mode = "layout"
        if settings.get("negpip", {}).get("mode", "off") != "off":
            raise ValueError("[EasyUseAnima] MOSS Layout JSON requires NegPip off to preserve its structured text.")
    if mode != "original" and settings.get("artist_mix", {}).get("mode", "off") != "off":
        raise ValueError("[EasyUseAnima] MOSS caption enhancement and Layout use the complete prompt; Artist Mix must be off.")
    return mode, source


def prepare_moss_prompt(clip, positive_prompt, settings, node_lookup=None):
    mode, source = validate_moss_prompt(positive_prompt, settings)
    if mode == "original":
        return positive_prompt, None
    effective = source
    if mode == "enhance":
        node, status = moss_feature_provider("prompt_enhance", node_lookup=node_lookup)
        if node is None:
            raise RuntimeError(f"[EasyUseAnima] MOSS TextGenerate node is {status}; update ComfyUI.")
        prompt = moss_settings(settings)["prompt"]
        sampling = {name: prompt[name] for name in ("temperature", "top_k", "top_p", "min_p", "repetition_penalty")}
        sampling.update(sampling_mode="on", seed=int(prompt["seed"]))
        values = _node_output_tuple(node.execute(
            clip=clip, prompt=source, max_length=prompt["max_length"], sampling_mode=sampling,
            thinking=False, use_default_template=True, system_prompt=MOSS_PROMPT_SYSTEM,
        ))
        if not values or not isinstance(values[0], str) or not values[0].strip():
            raise RuntimeError("[EasyUseAnima] MOSS prompt enhancement returned no caption; increase max_length or use Original mode.")
        effective = values[0]
    return effective, {"mode": mode, "source_prompt": positive_prompt, "used_prompt": effective}


__all__ = ()
