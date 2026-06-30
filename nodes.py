# -*- coding: utf-8 -*-
from __future__ import annotations

import importlib
import inspect
import json
import logging
import os
import re
import sys
from math import gcd, isfinite, lcm
from typing import Any, Optional

try:
    from .anima_prompt import correct_prompt, load_knowledge_base
    from .anima_prompt.parser import parse_prompt
    from .settings import resolve_metadata_filter_words, resolve_naia_settings
    from .wildcard_engine import (
        MAX_SEED,
        SEED_CONTROL_FIXED,
        SEED_CONTROL_INCREMENT,
        SEED_CONTROL_MODES,
        SEED_CONTROL_RANDOMIZE,
        WILDCARD_MODE_FIXED,
        WILDCARD_MODE_LABELS,
        WILDCARD_MODE_POPULATE,
        WILDCARD_MODE_REPRODUCE,
        WILDCARD_MODE_SEQUENTIAL,
        expand_wildcards,
        has_wildcard_syntax,
        next_seed,
        normalize_seed,
        normalize_wildcard_mode,
        wildcard_sources_signature,
    )
except ImportError:  # allows simple local import tests outside ComfyUI's package loader
    from anima_prompt import correct_prompt, load_knowledge_base
    from anima_prompt.parser import parse_prompt
    from settings import resolve_metadata_filter_words, resolve_naia_settings
    from wildcard_engine import (
        MAX_SEED,
        SEED_CONTROL_FIXED,
        SEED_CONTROL_INCREMENT,
        SEED_CONTROL_MODES,
        SEED_CONTROL_RANDOMIZE,
        WILDCARD_MODE_FIXED,
        WILDCARD_MODE_LABELS,
        WILDCARD_MODE_POPULATE,
        WILDCARD_MODE_REPRODUCE,
        WILDCARD_MODE_SEQUENTIAL,
        expand_wildcards,
        has_wildcard_syntax,
        next_seed,
        normalize_seed,
        normalize_wildcard_mode,
        wildcard_sources_signature,
    )

logger = logging.getLogger("ComfyUI-EasyUseAnima")

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 7243
DEFAULT_QUALITY_TAGS = (
    "newest, masterpiece, best quality, score_8, score_7:, highres, absurdres, very aesthetic"
)
DEFAULT_TRAILING_QUALITY_TAGS = (
    "location, (A highly aesthetic Pixiv style illustration, clean composition, "
    "high-quality digital art, detailed background, sharp focus on facial expressions.:0.6)"
)
ADVANCED_FIELD_TYPES = {"quality", "artist", "trigger", "general", "naia"}
ADVANCED_FIELD_PANES = {"positive", "negative"}
ADVANCED_FIELD_LABELS = {
    "quality": "Quality Tags",
    "artist": "Artist Tags",
    "trigger": "Trigger Words",
    "general": "General Tags",
    "naia": "NAIA Prompt",
}
ADVANCED_FIELDS_WORKFLOW_PROPERTY = "easyuse_anima_advanced_fields"
REGIONAL_FIELDS_WORKFLOW_PROPERTY = "easyuse_anima_regional_fields"
REGIONAL_CONFIG_WORKFLOW_PROPERTY = "easyuse_anima_regional_config"
REGIONAL_FIELD_TYPES = {"quality", "artist", "trigger", "general"}
REGIONAL_CONFIG_VERSION = 1
REGIONAL_PROMPT_DATA_TYPE = "EASYUSE_ANIMA_REGIONAL_PROMPT_DATA"
REGIONAL_PROMPT_DATA_SCHEMA = "easyuse_anima_prompt_studio_regional"
REGIONAL_PROMPT_BUNDLE_SCHEMA = "easyuse_anima_prompt_studio_regional_bundle"
EXTEND_PROMPT_SLOT_SPECS = [
    ("quality_tags_1", "positive", "quality", "Quality Tags 1", DEFAULT_QUALITY_TAGS, 72),
    ("quality_tags_2", "positive", "quality", "Quality Tags 2", "", 72),
    ("naia_prompt_3", "positive", "general", "NAIA Prompt 3", "", 150),
    ("general_tags_4", "positive", "general", "General Tags 4", "", 120),
    ("general_tags_5", "positive", "general", "General Tags 5", "", 120),
    ("general_tags_6", "positive", "general", "General Tags 6", "", 120),
    ("general_tags_7", "positive", "general", "General Tags 7", "", 120),
    ("general_tags_8", "positive", "general", "General Tags 8", "", 120),
    ("general_tags_9", "positive", "general", "General Tags 9", "", 120),
    ("trailing_tags_10", "positive", "general", "Trailing Quality Tags 10", DEFAULT_TRAILING_QUALITY_TAGS, 72),
    ("trailing_tags_11", "positive", "general", "Trailing Quality Tags 11", "", 72),
    ("negative_prompt_1", "negative", "quality", "Negative Prompt 1", "", 120),
    ("negative_prompt_2", "negative", "quality", "Negative Prompt 2", "", 120),
    ("negative_prompt_3", "negative", "general", "Negative Prompt 3", "", 120),
    ("negative_prompt_4", "negative", "general", "Negative Prompt 4", "", 120),
]
NAIA_REQUEST_TIMEOUT = 30.0
HTTP_TIMEOUT = NAIA_REQUEST_TIMEOUT + 5.0

NAI_1MP = 1024 * 1024
LATENT_ALIGN = 8
IMAGE_UPSCALE_METHODS = ["nearest-exact", "bilinear", "area", "bicubic", "lanczos"]
IMAGE_SCALE_MULTIPLES = ["8", "16", "32", "64"]
ADVANCED_RESOLUTION_BUCKETS = {
    "512": (
        (256, 1024), (1024, 256),
        (288, 896), (896, 288),
        (384, 672), (672, 384),
        (512, 512),
        (448, 576), (576, 448),
    ),
    "768": (
        (384, 1440), (1440, 384),
        (480, 1152), (1152, 480),
        (576, 960), (960, 576),
        (640, 864), (864, 640),
        (768, 768),
    ),
    "896": (
        (448, 1728), (1728, 448),
        (480, 1600), (1600, 480),
        (576, 1344), (1344, 576),
        (672, 1152), (1152, 672),
        (800, 960), (960, 800),
        (896, 896),
    ),
    "1024": (
        (512, 2016), (2016, 512),
        (576, 1792), (1792, 576),
        (672, 1536), (1536, 672),
        (672, 1600), (1600, 672),
        (768, 1344), (1344, 768),
        (800, 1344), (1344, 800),
        (896, 1152), (1152, 896),
        (960, 1120), (1120, 960),
        (1024, 1024),
    ),
    "1280": (
        (672, 2400), (2400, 672),
        (800, 2016), (2016, 800),
        (1024, 1536), (1536, 1024),
        (1024, 1600), (1600, 1024),
        (1120, 1440), (1440, 1120),
        (1280, 1280),
    ),
    "1536": (
        (1440, 1536), (1536, 1440),
        (1280, 1728), (1728, 1280),
        (1152, 1920), (1920, 1152),
        (1024, 2176), (2176, 1024),
        (960, 2304), (2304, 960),
        (864, 2560), (2560, 864),
        (768, 2880), (2880, 768),
        (1536, 1536),
    ),
}
CUSTOM_ADVANCED_RESOLUTION_BUCKET = "Custom"
NAIA_ADVANCED_RESOLUTION_BUCKET = "NAIA"
DEFAULT_ADVANCED_RESOLUTION_BUCKET = "1024"
DEFAULT_ADVANCED_RESOLUTION_SIZE = "1024 * 1024 (1:1)"

PREPROCESSING_KEYS = [
    "remove_author",
    "remove_work_title",
    "remove_character_name",
    "remove_character_features",
    "remove_clothes",
    "remove_color",
    "remove_location_and_background_color",
    "remove_expression",
    "remove_pose_action",
    "remove_meta_tags",
    "remove_object_tags",
    "remove_noise_tags",
    "e621_auto_boost",
    "danbooru_auto_weight",
    "tag_implication_compression",
]
PP_STATE_CHOICES = ["skip", "on", "off"]

_HASH_COMMENT_RE = re.compile(r"^[ \t]*#[^\n]*", re.MULTILINE)
_MULTI_COMMA_RE = re.compile(r"(\s*,){2,}")
_INLINE_SPACE_RE = re.compile(r"[ \t]+")
_WEIGHTED_TOKEN_RE = re.compile(r"^\(([^(),]+):[-+]?\d+(?:\.\d+)?\)$")
_RESOLUTION_LABEL_RE = re.compile(r"(\d+)\s*(?:\*|x|×)\s*(\d+)")
_TRIGGER_WORD_KEYS = ("trainedWords", "trained_words", "trigger_words", "activation_text")
_ADVANCED_FIELD_SOCKET_PREFIX = "field_"
_ADVANCED_FIELD_SOCKET_RE = re.compile(r"[^A-Za-z0-9_]")


class _AnyType(str):
    def __ne__(self, __value: object) -> bool:
        return False


class _FlexibleOptionalInputType(dict):
    def __init__(self, input_type):
        self.input_type = input_type

    def __getitem__(self, key):
        return (self.input_type,)

    def __contains__(self, key):
        return True


_ANY_TYPE = _AnyType("*")


def _single_value(value):
    if isinstance(value, (list, tuple)):
        if not value:
            return None
        return value[0]
    return value


def _as_bool(value, default: bool = False) -> bool:
    value = _single_value(value)
    if value is None:
        return default
    if isinstance(value, str):
        return value.strip().lower() in ("true", "1", "yes", "on", "enable", "enabled")
    return bool(value)


def _as_int(value, default: int = 0) -> int:
    value = _single_value(value)
    if value is None:
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _as_float(value, default: float = 0.0) -> float:
    value = _single_value(value)
    if value is None:
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _ratio_label(width: int, height: int) -> str:
    divisor = gcd(max(1, int(width)), max(1, int(height)))
    return f"{int(width) // divisor}:{int(height) // divisor}"


def _resolution_label(width: int, height: int) -> str:
    return f"{int(width)} * {int(height)} ({_ratio_label(width, height)})"


def _sorted_resolution_options(bucket: str) -> list[tuple[int, int]]:
    values = ADVANCED_RESOLUTION_BUCKETS.get(bucket) or ADVANCED_RESOLUTION_BUCKETS[DEFAULT_ADVANCED_RESOLUTION_BUCKET]
    return sorted(values, key=lambda item: (item[0] / item[1], item[0], item[1]))


def _normalize_resolution_bucket(value) -> str:
    value = str(_single_value(value) or "").strip()
    if value in {CUSTOM_ADVANCED_RESOLUTION_BUCKET, NAIA_ADVANCED_RESOLUTION_BUCKET}:
        return value
    return value if value in ADVANCED_RESOLUTION_BUCKETS else DEFAULT_ADVANCED_RESOLUTION_BUCKET


def _snap_resolution_32(value, default: int = 1024) -> int:
    raw = _as_int(value, default)
    if raw <= 0:
        raw = default
    return max(32, int(round(raw / 32)) * 32)


def _resolve_naia_resolution_scale(naia_settings: dict | None) -> float:
    value = _as_float((naia_settings or {}).get("resolution_scale", 1.0), 1.0)
    return max(0.25, min(4.0, value))


def _resolve_naia_resolution_max_long_edge(naia_settings: dict | None) -> int:
    value = _as_int((naia_settings or {}).get("resolution_max_long_edge", 0), 0)
    if value <= 0:
        return 0
    return max(32, min(16384, value))


def _snap_scaled_resolution_32(value: float, max_value: int = 0, default: int = 1024) -> int:
    raw = _as_float(value, float(default))
    if raw <= 0:
        raw = float(default)
    snapped = max(32, int(round(raw / 32)) * 32)
    if max_value > 0 and snapped > max_value:
        snapped = max(32, int(max_value // 32) * 32)
    return snapped


def _scale_naia_resolution(
    width: int,
    height: int,
    naia_settings: dict | None,
) -> tuple[int, int]:
    scale = _resolve_naia_resolution_scale(naia_settings)
    max_long_edge = _resolve_naia_resolution_max_long_edge(naia_settings)
    scaled_width = max(1.0, _as_float(width, 1024.0) * scale)
    scaled_height = max(1.0, _as_float(height, 1024.0) * scale)

    if max_long_edge > 0:
        long_edge = max(scaled_width, scaled_height)
        if long_edge > max_long_edge:
            ratio = max_long_edge / long_edge
            scaled_width *= ratio
            scaled_height *= ratio

    return (
        _snap_scaled_resolution_32(scaled_width, max_long_edge, 1024),
        _snap_scaled_resolution_32(scaled_height, max_long_edge, 1024),
    )


def _advanced_resolution_from_selection(
    bucket,
    size,
    custom_width: int | str = 1024,
    custom_height: int | str = 1024,
) -> tuple[int, int]:
    bucket_name = _normalize_resolution_bucket(bucket)
    if bucket_name in {CUSTOM_ADVANCED_RESOLUTION_BUCKET, NAIA_ADVANCED_RESOLUTION_BUCKET}:
        return (
            _snap_resolution_32(custom_width, 1024),
            _snap_resolution_32(custom_height, 1024),
        )
    raw_size = str(_single_value(size) or "").strip()
    match = _RESOLUTION_LABEL_RE.search(raw_size)
    if match:
        width, height = int(match.group(1)), int(match.group(2))
        if (width, height) in ADVANCED_RESOLUTION_BUCKETS.get(bucket_name, ()):
            return width, height
    default_width, default_height = 1024, 1024
    if (default_width, default_height) in ADVANCED_RESOLUTION_BUCKETS.get(bucket_name, ()):
        return default_width, default_height
    return _sorted_resolution_options(bucket_name)[0]


def _clean_prompt(value: str) -> str:
    if not value:
        return value
    value = _HASH_COMMENT_RE.sub("", value)
    value = _MULTI_COMMA_RE.sub(",", value)
    return value.strip(" ,\n\t")


def _stable_change_key(payload: dict) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _comfy_max_resolution() -> int:
    try:
        import nodes as comfy_nodes  # type: ignore

        return int(getattr(comfy_nodes, "MAX_RESOLUTION", 16384))
    except Exception:
        return 16384


def _comfy_sampler_names() -> list[str]:
    try:
        import comfy.samplers  # type: ignore

        return list(comfy.samplers.KSampler.SAMPLERS)
    except Exception:
        return [
            "euler",
            "euler_ancestral",
            "heun",
            "dpm_2",
            "dpm_2_ancestral",
            "dpmpp_2m",
            "dpmpp_sde",
            "ddim",
        ]


def _comfy_checkpoint_names() -> list[str]:
    try:
        import folder_paths  # type: ignore

        names = [str(name) for name in folder_paths.get_filename_list("checkpoints")]
        if names:
            return names
    except Exception:
        pass
    return ["sam3.1_multiplex_fp16.safetensors"]


def _preferred_checkpoint_default(names: list[str], preferred: str) -> str:
    return preferred if preferred in names else names[0]


def _impact_core_module():
    module = sys.modules.get("impact.core")
    if module is not None:
        return module
    for module_name in ("impact.core", "modules.impact.core"):
        try:
            return importlib.import_module(module_name)
        except Exception:
            continue
    return None


def _impact_scheduler_names() -> list[str]:
    core = _impact_core_module()
    if core is not None:
        try:
            return list(core.get_schedulers())
        except Exception:
            pass
    try:
        import comfy.samplers  # type: ignore

        return list(comfy.samplers.KSampler.SCHEDULERS)
    except Exception:
        return ["normal", "karras", "exponential", "sgm_uniform", "simple", "ddim_uniform"]


def _find_impact_detailer_class():
    try:
        import nodes as comfy_nodes  # type: ignore

        cls = getattr(comfy_nodes, "NODE_CLASS_MAPPINGS", {}).get("DetailerForEach")
        if cls is not None:
            return cls
    except Exception:
        pass

    for module in list(sys.modules.values()):
        mappings = getattr(module, "NODE_CLASS_MAPPINGS", None)
        if isinstance(mappings, dict):
            cls = mappings.get("DetailerForEach")
            if cls is not None:
                return cls

    for module_name in ("impact.impact_pack", "modules.impact.impact_pack"):
        try:
            module = importlib.import_module(module_name)
        except Exception:
            continue
        cls = getattr(module, "DetailerForEach", None)
        if cls is not None:
            return cls

    raise RuntimeError(
        "[EasyUseAnima] SAM3 Detailer requires ComfyUI Impact Pack's DetailerForEach. "
        "Install/enable ComfyUI-Impact-Pack, then restart ComfyUI."
    )


def _find_comfy_node_class(node_id: str):
    try:
        import nodes as comfy_nodes  # type: ignore

        mappings = getattr(comfy_nodes, "NODE_CLASS_MAPPINGS", {})
        cls = mappings.get(node_id)
        if cls is not None:
            return cls
        cls = getattr(comfy_nodes, node_id, None)
        if cls is not None:
            return cls
    except Exception:
        pass
    return None


def _load_checkpoint_with_comfy(ckpt_name: str):
    loader_cls = _find_comfy_node_class("CheckpointLoaderSimple")
    if loader_cls is None:
        raise RuntimeError("[EasyUseAnima] Could not find ComfyUI CheckpointLoaderSimple.")
    loader = loader_cls()
    method = getattr(loader, "load_checkpoint", None)
    if method is None:
        raise RuntimeError("[EasyUseAnima] CheckpointLoaderSimple does not expose load_checkpoint.")
    return method(ckpt_name)


def _encode_with_comfy_clip(clip, text: str):
    encoder_cls = _find_comfy_node_class("CLIPTextEncode")
    if encoder_cls is None:
        raise RuntimeError("[EasyUseAnima] Could not find ComfyUI CLIPTextEncode.")
    encoder = encoder_cls()
    method = getattr(encoder, "encode", None)
    if method is None:
        raise RuntimeError("[EasyUseAnima] CLIPTextEncode does not expose encode.")
    result = method(clip, text)
    if not isinstance(result, tuple) or not result:
        raise RuntimeError("[EasyUseAnima] CLIPTextEncode returned no conditioning.")
    return result[0]


def _find_sam3_detect_class():
    cls = _find_comfy_node_class("SAM3_Detect")
    if cls is not None:
        return cls
    try:
        module = importlib.import_module("comfy_extras.nodes_sam3")
        cls = getattr(module, "SAM3_Detect", None)
        if cls is not None:
            return cls
    except Exception:
        pass
    raise RuntimeError(
        "[EasyUseAnima] SAM3_Detect was not found. "
        "Use a ComfyUI build with native SAM3 support, then restart ComfyUI."
    )


def _find_impact_mask_to_segs_class():
    cls = _find_comfy_node_class("MaskToSEGS")
    if cls is not None:
        return cls

    for module in list(sys.modules.values()):
        mappings = getattr(module, "NODE_CLASS_MAPPINGS", None)
        if isinstance(mappings, dict):
            cls = mappings.get("MaskToSEGS")
            if cls is not None:
                return cls

    for module_name in ("impact.segs_nodes", "modules.impact.segs_nodes", "impact.impact_pack", "modules.impact.impact_pack"):
        try:
            module = importlib.import_module(module_name)
        except Exception:
            continue
        cls = getattr(module, "MaskToSEGS", None)
        if cls is not None:
            return cls

    raise RuntimeError(
        "[EasyUseAnima] Anima SAM3 Detailer requires ComfyUI Impact Pack's MaskToSEGS. "
        "Install/enable ComfyUI-Impact-Pack, then restart ComfyUI."
    )


def _node_output_tuple(result) -> tuple:
    value = getattr(result, "result", None)
    if value is not None:
        return tuple(value)
    if isinstance(result, tuple):
        return result
    return (result,)


def _format_sam3_detection_prompt(detect_prompt: str, detect_count: int) -> str:
    prompt = str(detect_prompt or "").strip()
    if not prompt:
        raise ValueError("[EasyUseAnima] SAM3 detect prompt is empty.")

    max_det = max(1, int(detect_count))
    parts = [part.strip() for part in re.split(r"[,\n]+", prompt) if part.strip()]
    formatted = []
    for part in parts:
        if re.search(r":\s*[\d.]+\s*$", part):
            formatted.append(part)
        else:
            formatted.append(f"{part}:{max_det}")
    return ", ".join(formatted)


def _sam3_context(model, clip, vae, ckpt_name: str = "") -> dict[str, Any]:
    return {
        "model": model,
        "clip": clip,
        "vae": vae,
        "ckpt_name": ckpt_name,
    }


def _context_value(ctx, key: str):
    if isinstance(ctx, dict):
        return ctx.get(key)
    return None


def _empty_mask_for_image(image):
    try:
        import torch  # type: ignore
    except Exception as exc:
        raise RuntimeError("[EasyUseAnima] torch is required to create an empty mask.") from exc

    batch = int(image.shape[0])
    height = int(image.shape[1])
    width = int(image.shape[2])
    device = getattr(image, "device", None)
    return torch.zeros((batch, height, width), dtype=torch.float32, device=device)


def _empty_segs_for_image(image):
    return ((int(image.shape[1]), int(image.shape[2])), [])


def _segs_has_items(segs) -> bool:
    try:
        return len(segs[1]) > 0
    except Exception:
        return False


def _call_impact_detailer(detailer, **kwargs):
    method = getattr(detailer, "doit", None)
    if method is None:
        raise RuntimeError("[EasyUseAnima] Impact DetailerForEach does not expose a doit method.")
    signature = inspect.signature(method)
    parameters = signature.parameters
    accepts_kwargs = any(param.kind == inspect.Parameter.VAR_KEYWORD for param in parameters.values())
    call_kwargs = kwargs if accepts_kwargs else {key: value for key, value in kwargs.items() if key in parameters}
    return method(**call_kwargs)


def _alignment_value(value) -> Optional[int]:
    text = str(_single_value(value) or "").strip().lower()
    if text in ("", "impact", "none", "0"):
        return None
    try:
        alignment = int(text)
    except ValueError:
        return None
    return alignment if alignment > 1 else None


def _align_up(value: int, alignment: int) -> int:
    value = int(value)
    alignment = int(alignment)
    return max(alignment, ((value + alignment - 1) // alignment) * alignment)


def _align_nearest(value: int, alignment: int) -> int:
    value = max(1, int(value))
    alignment = max(1, int(alignment))
    lower = max(alignment, (value // alignment) * alignment)
    upper = _align_up(value, alignment)
    if (value - lower) < (upper - value):
        return lower
    return upper


def _scale_by_value(value, default: float = 1.0) -> float:
    scale = _as_float(value, default)
    if not isfinite(scale):
        scale = default
    return max(0.01, min(8.0, scale))


def _max_long_edge_value(value) -> int:
    max_long_edge = _as_int(value, 0)
    if max_long_edge <= 0:
        return 0
    return max(1, min(16384, max_long_edge))


def _aligned_size_near_scale(
    source_width: int,
    source_height: int,
    scale: float,
    alignment: int,
    max_long_edge: int,
) -> Optional[tuple[int, int, float]]:
    source_long_edge = max(source_width, source_height)
    target_scale = scale
    if max_long_edge > 0 and source_long_edge * target_scale > max_long_edge:
        target_scale = max_long_edge / source_long_edge
    if target_scale <= 0:
        return None

    target_width = max(1, round(source_width * target_scale))
    target_height = max(1, round(source_height * target_scale))
    width_candidates = {
        max(alignment, (target_width // alignment) * alignment),
        _align_up(target_width, alignment),
    }
    height_candidates = {
        max(alignment, (target_height // alignment) * alignment),
        _align_up(target_height, alignment),
    }

    candidates: list[tuple[int, int, float]] = []
    for candidate_width in width_candidates:
        for candidate_height in height_candidates:
            if max_long_edge > 0 and max(candidate_width, candidate_height) > max_long_edge:
                continue
            if scale > 1.0 and max_long_edge > source_long_edge:
                if candidate_width <= source_width or candidate_height <= source_height:
                    continue
            applied_scale = (candidate_width / source_width + candidate_height / source_height) / 2.0
            candidates.append((candidate_width, candidate_height, applied_scale))
    if not candidates:
        return None

    source_ratio = source_width / source_height
    return min(
        candidates,
        key=lambda item: (
            abs((item[0] / source_width) - target_scale) + abs((item[1] / source_height) - target_scale),
            abs((item[0] / item[1]) - source_ratio),
            -item[0] * item[1],
        ),
    )


def _image_scale_by_multiple_size(
    width: int,
    height: int,
    scale_by,
    multiple,
    max_long_edge=0,
) -> tuple[int, int, float]:
    source_width = max(1, int(width))
    source_height = max(1, int(height))
    scale = _scale_by_value(scale_by, 1.0)
    max_long_edge = _max_long_edge_value(max_long_edge)
    alignment = _alignment_value(multiple)
    if alignment is None:
        applied_scale = scale
        if max_long_edge > 0:
            applied_scale = min(applied_scale, max_long_edge / max(source_width, source_height))
        target_width = max(1, round(source_width * applied_scale))
        target_height = max(1, round(source_height * applied_scale))
        if max_long_edge > 0 and max(target_width, target_height) > max_long_edge:
            applied_scale = max_long_edge / max(target_width, target_height) * applied_scale
            target_width = max(1, round(source_width * applied_scale))
            target_height = max(1, round(source_height * applied_scale))
        return target_width, target_height, applied_scale

    ratio_gcd = gcd(source_width, source_height)
    base_width = source_width // ratio_gcd
    base_height = source_height // ratio_gcd
    base_long_edge = max(base_width, base_height)
    width_unit = alignment // gcd(base_width, alignment)
    height_unit = alignment // gcd(base_height, alignment)
    valid_unit_step = lcm(width_unit, height_unit)

    max_valid_unit = int((ratio_gcd * 8.0) // valid_unit_step)
    if max_long_edge > 0:
        max_valid_unit = min(max_valid_unit, max_long_edge // (base_long_edge * valid_unit_step))
    if max_valid_unit >= 1:
        desired_unit = (ratio_gcd * scale) / valid_unit_step
        lower_unit = max(1, min(max_valid_unit, int(desired_unit)))
        candidates = {lower_unit}
        if lower_unit < max_valid_unit:
            candidates.add(lower_unit + 1)
        if lower_unit > 1:
            candidates.add(lower_unit - 1)

        valid_unit = min(
            candidates,
            key=lambda unit: (
                abs(((unit * valid_unit_step) / ratio_gcd) - scale),
                -unit,
            ),
        )
        applied_scale = (valid_unit * valid_unit_step) / ratio_gcd
        candidate = (
            base_width * valid_unit * valid_unit_step,
            base_height * valid_unit * valid_unit_step,
            applied_scale,
        )
        if max_long_edge > 0:
            aligned_candidate = _aligned_size_near_scale(
                source_width,
                source_height,
                scale,
                alignment,
                max_long_edge,
            )
            if aligned_candidate is not None:
                source_long_edge = max(source_width, source_height)
                target_long_edge = min(source_long_edge * scale, max_long_edge)
                candidate_long_error = abs(max(candidate[0], candidate[1]) - target_long_edge)
                aligned_long_error = abs(max(aligned_candidate[0], aligned_candidate[1]) - target_long_edge)
                candidate_upscales = candidate[0] > source_width and candidate[1] > source_height
                aligned_upscales = aligned_candidate[0] > source_width and aligned_candidate[1] > source_height
                if scale > 1.0 and aligned_upscales and not candidate_upscales:
                    return aligned_candidate
                if aligned_long_error < candidate_long_error:
                    return aligned_candidate
            if max(source_width, source_height) * scale > max_long_edge and aligned_candidate is not None:
                return aligned_candidate
        return candidate

    aligned_candidate = _aligned_size_near_scale(
        source_width,
        source_height,
        scale,
        alignment,
        max_long_edge,
    )
    if aligned_candidate is not None:
        return aligned_candidate

    target_width = _align_nearest(round(source_width * scale), alignment)
    target_height = _align_nearest(round(source_height * scale), alignment)
    applied_scale = (target_width / source_width + target_height / source_height) / 2.0
    return target_width, target_height, applied_scale


def _normalize_image_scale_options(upscale_method, multiple, max_long_edge):
    method = str(_single_value(upscale_method) or "").strip()
    size_multiple = str(_single_value(multiple) or "").strip()
    max_edge = max_long_edge

    # Compatibility for workflows created before max_long_edge existed, or while it was inserted
    # before upscale_method: widget values can shift into the wrong input names.
    if size_multiple in IMAGE_UPSCALE_METHODS and str(_single_value(max_long_edge) or "").strip() in IMAGE_SCALE_MULTIPLES:
        shifted_max_edge = upscale_method
        method = size_multiple
        size_multiple = str(_single_value(max_long_edge) or "").strip()
        max_edge = shifted_max_edge
    if str(_single_value(max_long_edge) or "").strip() in IMAGE_UPSCALE_METHODS:
        shifted_method = str(_single_value(max_long_edge) or "").strip()
        if method in IMAGE_SCALE_MULTIPLES:
            size_multiple = method
        method = shifted_method
        max_edge = 0

    if method not in IMAGE_UPSCALE_METHODS:
        method = "bicubic"
    if size_multiple not in IMAGE_SCALE_MULTIPLES:
        size_multiple = "32"
    return method, size_multiple, max_edge


def _common_upscale_image(samples, width: int, height: int, upscale_method: str):
    try:
        import comfy.utils  # type: ignore

        return comfy.utils.common_upscale(samples, width, height, upscale_method, "disabled")
    except Exception:
        import torch.nn.functional as F  # type: ignore

        method = "bicubic" if str(upscale_method) == "lanczos" else str(upscale_method)
        if method in {"bilinear", "bicubic"}:
            return F.interpolate(samples, size=(height, width), mode=method, align_corners=False)
        return F.interpolate(samples, size=(height, width), mode=method)


class _EasyUseAnimaAlignedDetailerHook:
    def __init__(self, base_hook, alignment: Optional[int]):
        self.base_hook = base_hook
        self.alignment = int(alignment) if alignment is not None else None

    def __getattr__(self, name):
        if self.base_hook is not None:
            return getattr(self.base_hook, name)
        raise AttributeError(name)

    def touch_scaled_size(self, width, height):
        if self.base_hook is not None and hasattr(self.base_hook, "touch_scaled_size"):
            width, height = self.base_hook.touch_scaled_size(width, height)
        if self.alignment is None:
            return width, height
        aligned_width = _align_up(width, self.alignment)
        aligned_height = _align_up(height, self.alignment)
        if aligned_width != width or aligned_height != height:
            logger.info(
                "[EasyUseAnima] Detailer hook aligned crop size %sx%s -> %sx%s (alignment=%s)",
                width,
                height,
                aligned_width,
                aligned_height,
                self.alignment,
            )
        return aligned_width, aligned_height

    def post_upscale(self, image, noise_mask):
        if self.base_hook is not None and hasattr(self.base_hook, "post_upscale"):
            return self.base_hook.post_upscale(image, noise_mask)
        return image

    def get_skip_sampling(self):
        if self.base_hook is not None and hasattr(self.base_hook, "get_skip_sampling"):
            return self.base_hook.get_skip_sampling()
        return False

    def post_encode(self, latent):
        if self.base_hook is not None and hasattr(self.base_hook, "post_encode"):
            return self.base_hook.post_encode(latent)
        return latent

    def get_custom_sampler(self):
        if self.base_hook is not None and hasattr(self.base_hook, "get_custom_sampler"):
            return self.base_hook.get_custom_sampler()
        return None

    def set_steps(self, steps):
        if self.base_hook is not None and hasattr(self.base_hook, "set_steps"):
            return self.base_hook.set_steps(steps)
        return None

    def cycle_latent(self, latent):
        if self.base_hook is not None and hasattr(self.base_hook, "cycle_latent"):
            return self.base_hook.cycle_latent(latent)
        return latent

    def pre_ksample(self, model, seed, steps, cfg, sampler_name, scheduler, positive, negative, latent, denoise):
        if self.base_hook is not None and hasattr(self.base_hook, "pre_ksample"):
            return self.base_hook.pre_ksample(
                model, seed, steps, cfg, sampler_name, scheduler, positive, negative, latent, denoise
            )
        return model, seed, steps, cfg, sampler_name, scheduler, positive, negative, latent, denoise

    def get_custom_noise(self, seed, noise, is_touched):
        if self.base_hook is not None and hasattr(self.base_hook, "get_custom_noise"):
            return self.base_hook.get_custom_noise(seed, noise, is_touched)
        return noise, is_touched

    def pre_decode(self, latent):
        if self.base_hook is not None and hasattr(self.base_hook, "pre_decode"):
            return self.base_hook.pre_decode(latent)
        return latent

    def post_decode(self, image):
        if self.base_hook is not None and hasattr(self.base_hook, "post_decode"):
            return self.base_hook.post_decode(image)
        return image

    def post_paste(self, image):
        if self.base_hook is not None and hasattr(self.base_hook, "post_paste"):
            return self.base_hook.post_paste(image)
        return image


def _split_tag_text(value: str) -> list[str]:
    if not value:
        return []
    parts: list[str] = []
    for line in str(value).splitlines():
        parts.extend(part.strip() for part in line.split(","))
    return [part for part in parts if part]


def _prompt_tokens(value: str) -> list[str]:
    if not value:
        return []
    cleaned_val = _HASH_COMMENT_RE.sub("", value)
    normalized = str(cleaned_val).replace("\r\n", "\n").replace("\r", "\n")
    normalized = normalized.replace("，", ",").replace("\n", ",")
    tokens: list[str] = []
    for token in parse_prompt(normalized, profile="prompt").tokens:
        cleaned = _INLINE_SPACE_RE.sub(" ", str(token).strip(" ,\n\t"))
        if cleaned:
            tokens.append(cleaned)
    return tokens


def _join_prompt_tokens(*parts: str) -> str:
    tokens: list[str] = []
    for part in parts:
        tokens.extend(_prompt_tokens(part))
    return ", ".join(tokens)


def _correct_builder_prompt(prompt: str, artist_overrides: str = "") -> str:
    if not prompt:
        return ""
    result = correct_prompt(
        prompt,
        profile="prompt",
        knowledge_base=load_knowledge_base(allow_missing=True),
        validate_artist_tags=False,
        artist_overrides=_prompt_tokens(artist_overrides),
    )
    return result.text


def _metadata_filter_key(value: str) -> str:
    value = _INLINE_SPACE_RE.sub(" ", str(value or "").strip(" ,\n\t"))
    return value.replace("_", " ").casefold()


def _metadata_filter_keys(value: str) -> set[str]:
    keys = {_metadata_filter_key(value)}
    weighted = _WEIGHTED_TOKEN_RE.match(str(value or "").strip())
    if weighted:
        keys.add(_metadata_filter_key(weighted.group(1)))
    return {key for key in keys if key}


def _filter_metadata_prompt(prompt: str, filter_words: str) -> str:
    filter_keys: set[str] = set()
    for word in _prompt_tokens(filter_words):
        filter_keys.update(_metadata_filter_keys(word))
    if not prompt or not filter_keys:
        return prompt

    kept = [
        token
        for token in _prompt_tokens(prompt)
        if _metadata_filter_keys(token).isdisjoint(filter_keys)
    ]
    return ", ".join(kept)


def _advanced_default_fields() -> list[dict]:
    return [
        {
            "id": "positive_quality",
            "pane": "positive",
            "type": "quality",
            "label": ADVANCED_FIELD_LABELS["quality"],
            "text": DEFAULT_QUALITY_TAGS,
            "height": 72,
            "enabled": True,
        },
        {
            "id": "positive_artist",
            "pane": "positive",
            "type": "artist",
            "label": ADVANCED_FIELD_LABELS["artist"],
            "text": "",
            "height": 72,
            "enabled": True,
        },
        {
            "id": "positive_trigger",
            "pane": "positive",
            "type": "trigger",
            "label": ADVANCED_FIELD_LABELS["trigger"],
            "text": "",
            "height": 72,
            "enabled": True,
            "pin": True,
        },
        {
            "id": "positive_general",
            "pane": "positive",
            "type": "general",
            "label": ADVANCED_FIELD_LABELS["general"],
            "text": "",
            "height": 150,
            "enabled": True,
        },
        {
            "id": "positive_trailing",
            "pane": "positive",
            "type": "general",
            "label": ADVANCED_FIELD_LABELS["general"],
            "text": DEFAULT_TRAILING_QUALITY_TAGS,
            "height": 72,
            "enabled": True,
        },
        {
            "id": "negative_general",
            "pane": "negative",
            "type": "general",
            "label": ADVANCED_FIELD_LABELS["general"],
            "text": "",
            "height": 120,
            "enabled": True,
        },
    ]


def _advanced_fields_json(fields: list[dict] | None = None) -> str:
    return json.dumps(
        fields if fields is not None else _advanced_default_fields(),
        ensure_ascii=False,
        separators=(",", ":"),
    )


def _as_advanced_height(value, default: int = 72) -> int:
    return max(36, _as_int(value, default))


def _normalize_advanced_fields(value: str | list | None) -> list[dict]:
    raw = value
    if isinstance(value, str):
        try:
            raw = json.loads(value or "[]")
        except json.JSONDecodeError:
            raw = []
    if not isinstance(raw, list):
        raw = []
    if not raw:
        raw = _advanced_default_fields()

    fields: list[dict] = []
    seen_naia_panes: set[str] = set()
    seen_trigger = False
    for index, item in enumerate(raw):
        if not isinstance(item, dict):
            continue
        pane = str(item.get("pane") or "positive").strip().lower()
        if pane not in ADVANCED_FIELD_PANES:
            pane = "positive"
        field_type = str(item.get("type") or "general").strip().lower()
        if field_type not in ADVANCED_FIELD_TYPES:
            field_type = "general"
        if pane == "negative" and field_type == "trigger":
            field_type = "general"
        if field_type == "naia":
            if pane in seen_naia_panes:
                continue
            seen_naia_panes.add(pane)
        if field_type == "trigger":
            if seen_trigger:
                continue
            seen_trigger = True
            pane = "positive"
        default_label = ADVANCED_FIELD_LABELS.get(field_type, ADVANCED_FIELD_LABELS["general"])
        label = str(item.get("label") or default_label).strip() or default_label
        field_id = str(item.get("id") or f"{pane}_{field_type}_{index + 1}").strip()
        if not field_id:
            field_id = f"{pane}_{field_type}_{index + 1}"
        fields.append({
            "id": field_id,
            "pane": pane,
            "type": field_type,
            "label": label,
            "text": str(item.get("text") or ""),
            "height": _as_advanced_height(item.get("height"), 72),
            "enabled": _as_bool(item.get("enabled"), True),
            "pin": _as_bool(item.get("pin"), field_type == "trigger"),
        })

    return fields or _advanced_default_fields()


def _clone_advanced_fields(fields: list[dict]) -> list[dict]:
    return [dict(field) for field in fields]


def _advanced_field_socket_name(field: dict) -> str:
    raw = _ADVANCED_FIELD_SOCKET_RE.sub("_", str(field.get("id") or "field")).strip("_")
    return f"{_ADVANCED_FIELD_SOCKET_PREFIX}{raw or 'field'}"


def _advanced_field_input_values(field_inputs: dict) -> dict[str, str]:
    values: dict[str, str] = {}
    for key, value in field_inputs.items():
        if not str(key).startswith(_ADVANCED_FIELD_SOCKET_PREFIX):
            continue
        single = _single_value(value)
        if single is None:
            continue
        values[str(key)] = str(single)
    return values


def _apply_advanced_field_inputs(fields: list[dict], field_inputs: dict) -> list[dict]:
    values = _advanced_field_input_values(field_inputs)
    if not values:
        return _clone_advanced_fields(fields)

    effective = _clone_advanced_fields(fields)
    for field in effective:
        name = _advanced_field_socket_name(field)
        if name in values:
            field["text"] = values[name]
    return effective


def _advanced_enabled_naia_panes(fields: list[dict]) -> set[str]:
    return {
        str(field.get("pane") or "positive")
        for field in fields
        if field.get("type") == "naia" and field.get("enabled") is not False
    }


def _advanced_has_enabled_naia(fields: list[dict]) -> bool:
    return bool(_advanced_enabled_naia_panes(fields))


def _advanced_uses_naia_resolution(bucket) -> bool:
    return _normalize_resolution_bucket(bucket) == NAIA_ADVANCED_RESOLUTION_BUCKET


def _set_naia_field_text(fields: list[dict], pane: str, prompt: str) -> list[dict]:
    normalized = _normalize_advanced_fields(fields)
    for field in normalized:
        if field["pane"] == pane and field["type"] == "naia":
            field["text"] = prompt
            field["enabled"] = True
            return normalized
    return normalized


def _advanced_pane_parts(fields: list[dict], pane: str) -> dict[str, list[str]]:
    parts = {"quality": [], "artist": [], "trigger_fixed": [], "trigger_auto": [], "body": []}
    for field in fields:
        if not _as_bool(field.get("enabled"), True):
            continue
        if field.get("pane") != pane:
            continue
        field_type = field.get("type")
        text = str(field.get("text") or "")
        if field_type == "quality":
            parts["quality"].append(text)
        elif field_type == "artist":
            parts["artist"].append(text)
        elif field_type == "trigger":
            if _as_bool(field.get("pin"), True):
                parts["trigger_fixed"].append(text)
            else:
                parts["trigger_auto"].append(text)
        else:
            parts["body"].append(text)
    return parts


def _advanced_enabled_pane_fields(fields: list[dict], pane: str) -> list[dict]:
    return [
        field
        for field in fields
        if _as_bool(field.get("enabled"), True) and field.get("pane") == pane
    ]


def _correct_advanced_field_sequence(
    fields: list[dict],
    include_quality: bool,
    artist_overrides: str,
    force_pin_triggers: bool = False,
) -> str:
    chunks: list[str] = []
    pending: list[str] = []

    def flush_pending() -> None:
        if not pending:
            return
        corrected = _correct_builder_prompt(
            _join_prompt_tokens(*pending),
            artist_overrides=artist_overrides,
        )
        if corrected:
            chunks.append(corrected)
        pending.clear()

    for field in fields:
        field_type = field.get("type")
        text = str(field.get("text") or "")
        if field_type == "quality" and not include_quality:
            continue
        if field_type == "trigger" and (
            _as_bool(field.get("pin"), True) or force_pin_triggers
        ):
            flush_pending()
            trigger_prompt = _join_prompt_tokens(text)
            if trigger_prompt:
                chunks.append(trigger_prompt)
            continue
        pending.append(text)

    flush_pending()
    return _join_prompt_tokens(*chunks)


def _build_advanced_prompts(
    fields: list[dict],
    use_anima_mod_guidance: bool,
    use_negative_anima_mod_guidance: bool,
    pin_trigger_tags_to_front: bool,
) -> tuple[str, str, str, str, bool, bool, str, str]:
    use_amg = _as_bool(use_anima_mod_guidance, False)
    use_negative_amg = _as_bool(use_negative_anima_mod_guidance, False)
    force_pin_triggers = _as_bool(pin_trigger_tags_to_front, False)
    positive = _advanced_pane_parts(fields, "positive")
    negative = _advanced_pane_parts(fields, "negative")
    positive_fields = _advanced_enabled_pane_fields(fields, "positive")
    negative_fields = _advanced_enabled_pane_fields(fields, "negative")

    quality_prompt = _join_prompt_tokens(*positive["quality"])
    artist_prompt = _join_prompt_tokens(*positive["artist"])
    regular_prompt = _correct_advanced_field_sequence(
        positive_fields,
        include_quality=True,
        artist_overrides=artist_prompt,
        force_pin_triggers=force_pin_triggers,
    )
    amg_prompt = _correct_advanced_field_sequence(
        positive_fields,
        include_quality=False,
        artist_overrides=artist_prompt,
        force_pin_triggers=force_pin_triggers,
    )
    metadata_prompt = regular_prompt

    negative_quality_prompt = _join_prompt_tokens(*negative["quality"])
    negative_artist_prompt = _join_prompt_tokens(*negative["artist"])
    negative_regular_prompt = _correct_advanced_field_sequence(
        negative_fields,
        include_quality=True,
        artist_overrides=negative_artist_prompt,
    )
    negative_amg_prompt = _correct_advanced_field_sequence(
        negative_fields,
        include_quality=False,
        artist_overrides=negative_artist_prompt,
    )

    filter_words = resolve_metadata_filter_words()
    metadata_prompt = _filter_metadata_prompt(metadata_prompt, filter_words)
    metadata_negative_prompt = _filter_metadata_prompt(negative_regular_prompt, filter_words)
    output_prompt = amg_prompt if use_amg else regular_prompt
    output_negative_prompt = negative_amg_prompt if use_negative_amg else negative_regular_prompt
    return (
        output_prompt,
        output_negative_prompt,
        quality_prompt,
        negative_quality_prompt,
        use_amg,
        use_negative_amg,
        metadata_prompt,
        metadata_negative_prompt,
    )


def _expand_advanced_wildcard_fields(
    fields: list[dict],
    seed: int,
    mode: str,
) -> tuple[list[dict], dict[str, Any]]:
    mode_key = normalize_wildcard_mode(mode)
    expanded_fields = _clone_advanced_fields(fields)
    if mode_key == WILDCARD_MODE_REPRODUCE:
        return expanded_fields, {
            "changed": False,
            "used_keys": (),
            "missing_keys": (),
        }

    changed = False
    used_keys: list[str] = []
    missing_keys: list[str] = []
    for field in expanded_fields:
        text = str(field.get("text") or "")
        if not has_wildcard_syntax(text):
            continue
        result = expand_wildcards(text, seed=seed, mode=mode_key)
        if result.text != text:
            field["text"] = result.text
            changed = True
        for key in result.used_keys:
            if key not in used_keys:
                used_keys.append(key)
        for key in result.missing_keys:
            if key not in missing_keys:
                missing_keys.append(key)

    return expanded_fields, {
        "changed": changed,
        "used_keys": tuple(used_keys),
        "missing_keys": tuple(missing_keys),
    }


def _regional_default_fields() -> list[dict]:
    fields = []
    for field in _advanced_default_fields():
        if field.get("type") == "naia":
            continue
        item = dict(field)
        item["mask_ids"] = []
        fields.append(item)
    return fields


def _regional_fields_json(fields: list[dict] | None = None) -> str:
    return json.dumps(
        fields if fields is not None else _regional_default_fields(),
        ensure_ascii=False,
        separators=(",", ":"),
    )


def _normalize_mask_ids(value) -> list[int]:
    value = _single_value(value)
    if value is None:
        return []
    if isinstance(value, str):
        raw_values = re.split(r"[,;\s]+", value.strip())
    elif isinstance(value, (list, tuple, set)):
        raw_values = list(value)
    else:
        raw_values = [value]

    mask_ids: list[int] = []
    for raw in raw_values:
        mask_id = _as_int(raw, 0)
        if mask_id > 0 and mask_id not in mask_ids:
            mask_ids.append(mask_id)
    return mask_ids


def _normalize_regional_fields(value: str | list | None) -> list[dict]:
    raw = value
    if isinstance(value, str):
        try:
            raw = json.loads(value or "[]")
        except json.JSONDecodeError:
            raw = []
    if not isinstance(raw, list):
        raw = []
    if not raw:
        raw = _regional_default_fields()

    fields: list[dict] = []
    seen_trigger = False
    for index, item in enumerate(raw):
        if not isinstance(item, dict):
            continue
        pane = str(item.get("pane") or "positive").strip().lower()
        if pane not in ADVANCED_FIELD_PANES:
            pane = "positive"
        field_type = str(item.get("type") or "general").strip().lower()
        if field_type not in REGIONAL_FIELD_TYPES:
            field_type = "general"
        if pane == "negative" and field_type == "trigger":
            field_type = "general"
        if field_type == "trigger":
            if seen_trigger:
                continue
            seen_trigger = True
            pane = "positive"
        default_label = ADVANCED_FIELD_LABELS.get(field_type, ADVANCED_FIELD_LABELS["general"])
        label = str(item.get("label") or default_label).strip() or default_label
        field_id = str(item.get("id") or f"{pane}_{field_type}_{index + 1}").strip()
        if not field_id:
            field_id = f"{pane}_{field_type}_{index + 1}"
        mask_ids = _normalize_mask_ids(item.get("mask_ids"))
        if pane != "positive":
            mask_ids = []
        fields.append({
            "id": field_id,
            "pane": pane,
            "type": field_type,
            "label": label,
            "text": str(item.get("text") or ""),
            "height": _as_advanced_height(item.get("height"), 72),
            "enabled": _as_bool(item.get("enabled"), True),
            "pin": _as_bool(item.get("pin"), field_type == "trigger"),
            "collapsed": _as_bool(item.get("collapsed"), False),
            "mask_ids": mask_ids,
        })

    return fields or _regional_default_fields()


def _clone_regional_fields(fields: list[dict]) -> list[dict]:
    return [
        {
            **dict(field),
            "mask_ids": list(field.get("mask_ids") or []),
        }
        for field in fields
    ]


def _apply_regional_field_inputs(fields: list[dict], field_inputs: dict) -> list[dict]:
    values = _advanced_field_input_values(field_inputs)
    if not values:
        return _clone_regional_fields(fields)

    effective = _clone_regional_fields(fields)
    for field in effective:
        name = _advanced_field_socket_name(field)
        if name in values:
            field["text"] = values[name]
    return effective


def _regional_default_config(width: int = 1024, height: int = 1024) -> dict[str, Any]:
    return {
        "version": REGIONAL_CONFIG_VERSION,
        "canvas": {
            "width": int(width),
            "height": int(height),
            "aspect_ratio": _ratio_label(width, height),
            "source": "resolution_fields",
        },
        "mask_authoring": {
            "render_space": "image_pixels",
            "storage_space": "normalized_canvas",
            "preview_enabled": True,
        },
        "global_prompt": "",
        "negative_prompt": "",
        "next_mask_id": 1,
        "masks": [],
        "regional_enabled": False,
        "mask_prompts": [],
        "assignments": [],
        "artist_mix": {},
        "conditioning_settings": {},
        "regional_settings": {},
    }


def _normalize_mask_geometry(value) -> dict[str, float]:
    if not isinstance(value, dict):
        value = {}
    shape = str(value.get("type") or "rect").strip().lower()
    if shape not in {"rect", "ellipse"}:
        shape = "rect"
    x = max(0.0, min(0.99, _as_float(value.get("x"), 0.1)))
    y = max(0.0, min(0.99, _as_float(value.get("y"), 0.1)))
    width = max(0.01, min(1.0, _as_float(value.get("width"), 0.35)))
    height = max(0.01, min(1.0, _as_float(value.get("height"), 0.35)))
    if x + width > 1.0:
        width = max(0.01, 1.0 - x)
    if y + height > 1.0:
        height = max(0.01, 1.0 - y)
    return {
        "type": shape,
        "x": round(x, 6),
        "y": round(y, 6),
        "width": round(width, 6),
        "height": round(height, 6),
    }


def _normalize_regional_mask(value, fallback_id: int) -> dict[str, Any] | None:
    if not isinstance(value, dict):
        return None
    mask_id = _as_int(value.get("mask_id", value.get("id")), fallback_id)
    if mask_id <= 0:
        return None
    default_label = f"Mask {mask_id}"
    name = str(value.get("name") or "").strip()
    label = str(value.get("label") or name or default_label).strip() or default_label
    color = str(value.get("color") or "#3b82f6").strip() or "#3b82f6"
    if not re.fullmatch(r"#[0-9A-Fa-f]{6}", color):
        color = "#3b82f6"
    mask = {
        "mask_id": mask_id,
        "label": label,
        "name": name,
        "color": color,
        "enabled": _as_bool(value.get("enabled"), True),
        "geometry": _normalize_mask_geometry(value.get("geometry")),
    }
    if isinstance(value.get("strokes"), list):
        mask["strokes"] = value["strokes"]
    if isinstance(value.get("shapes"), list):
        mask["shapes"] = value["shapes"]
    return mask


def _normalize_regional_config(
    value: str | dict | None,
    width: int = 1024,
    height: int = 1024,
) -> dict[str, Any]:
    raw = value
    if isinstance(value, str):
        try:
            raw = json.loads(value or "{}")
        except json.JSONDecodeError:
            raw = {}
    if not isinstance(raw, dict):
        raw = {}

    config = _regional_default_config(width, height)
    for key in ("artist_mix", "conditioning_settings", "regional_settings"):
        if isinstance(raw.get(key), dict):
            config[key] = raw[key]
    authoring = raw.get("mask_authoring")
    if isinstance(authoring, dict):
        merged = dict(config["mask_authoring"])
        merged.update({k: v for k, v in authoring.items() if isinstance(k, str)})
        config["mask_authoring"] = merged

    masks: list[dict[str, Any]] = []
    used_ids: set[int] = set()
    raw_masks = raw.get("masks")
    if not isinstance(raw_masks, list):
        raw_masks = raw.get("regions") if isinstance(raw.get("regions"), list) else []
    for index, item in enumerate(raw_masks):
        mask = _normalize_regional_mask(item, index + 1)
        if mask is None or mask["mask_id"] in used_ids:
            continue
        used_ids.add(mask["mask_id"])
        masks.append(mask)
    next_mask_id = max([_as_int(raw.get("next_mask_id"), 1), 1, *(mask["mask_id"] + 1 for mask in masks)])
    config["next_mask_id"] = next_mask_id
    config["masks"] = masks
    config["canvas"] = {
        "width": int(width),
        "height": int(height),
        "aspect_ratio": _ratio_label(width, height),
        "source": "resolution_fields",
    }
    return config


def _regional_config_json(config: dict[str, Any] | None = None) -> str:
    return json.dumps(
        config if config is not None else _regional_default_config(),
        ensure_ascii=False,
        separators=(",", ":"),
    )


def _regional_field_prompt(field: dict, artist_overrides: str = "") -> str:
    return _correct_advanced_field_sequence(
        [field],
        include_quality=True,
        artist_overrides=artist_overrides,
        force_pin_triggers=True,
    )


def _build_regional_outputs(
    fields: list[dict],
    config: dict[str, Any],
    width: int,
    height: int,
) -> tuple[str, str, str, str, dict[str, Any]]:
    positive_fields = [
        field
        for field in fields
        if field.get("pane") == "positive" and _as_bool(field.get("enabled"), True)
    ]
    negative_fields = [
        field
        for field in fields
        if field.get("pane") == "negative" and _as_bool(field.get("enabled"), True)
    ]
    global_positive_fields = [
        field for field in positive_fields if not _normalize_mask_ids(field.get("mask_ids"))
    ]
    mask_positive_fields = [
        field for field in positive_fields if _normalize_mask_ids(field.get("mask_ids"))
    ]

    global_artist_prompt = _join_prompt_tokens(
        *(str(field.get("text") or "") for field in global_positive_fields if field.get("type") == "artist")
    )
    all_artist_prompt = _join_prompt_tokens(
        *(str(field.get("text") or "") for field in positive_fields if field.get("type") == "artist")
    )
    negative_artist_prompt = _join_prompt_tokens(
        *(str(field.get("text") or "") for field in negative_fields if field.get("type") == "artist")
    )

    positive_prompt = _correct_advanced_field_sequence(
        global_positive_fields,
        include_quality=True,
        artist_overrides=global_artist_prompt,
        force_pin_triggers=True,
    )
    negative_prompt = _correct_advanced_field_sequence(
        negative_fields,
        include_quality=True,
        artist_overrides=negative_artist_prompt,
    )
    metadata_prompt = _correct_advanced_field_sequence(
        positive_fields,
        include_quality=True,
        artist_overrides=all_artist_prompt,
        force_pin_triggers=True,
    )

    filter_words = resolve_metadata_filter_words()
    metadata_prompt = _filter_metadata_prompt(metadata_prompt, filter_words)
    metadata_negative_prompt = _filter_metadata_prompt(negative_prompt, filter_words)

    masks = config.get("masks") if isinstance(config.get("masks"), list) else []
    enabled_mask_ids = {
        _as_int(mask.get("mask_id"), 0)
        for mask in masks
        if isinstance(mask, dict) and _as_bool(mask.get("enabled"), True)
    }
    assignments: list[dict[str, Any]] = []
    mask_prompts: list[dict[str, Any]] = []
    for field in mask_positive_fields:
        mask_ids = _normalize_mask_ids(field.get("mask_ids"))
        valid_mask_ids = [mask_id for mask_id in mask_ids if mask_id in enabled_mask_ids]
        missing_mask_ids = [mask_id for mask_id in mask_ids if mask_id not in enabled_mask_ids]
        prompt = _regional_field_prompt(field, all_artist_prompt)
        assignments.append({
            "field_id": str(field.get("id") or ""),
            "mask_ids": mask_ids,
            "valid_mask_ids": valid_mask_ids,
            "missing_mask_ids": missing_mask_ids,
        })
        mask_prompts.append({
            "field_id": str(field.get("id") or ""),
            "type": str(field.get("type") or "general"),
            "label": str(field.get("label") or ""),
            "text": str(field.get("text") or ""),
            "prompt": prompt,
            "mask_ids": mask_ids,
            "valid_mask_ids": valid_mask_ids,
            "missing_mask_ids": missing_mask_ids,
        })

    regional_enabled = any(entry["valid_mask_ids"] for entry in mask_prompts)
    regional_prompt_data = {
        **config,
        "version": REGIONAL_CONFIG_VERSION,
        "schema": REGIONAL_PROMPT_BUNDLE_SCHEMA,
        "canvas": {
            "width": int(width),
            "height": int(height),
            "aspect_ratio": _ratio_label(width, height),
            "source": "resolution_fields",
        },
        "global_prompt": positive_prompt,
        "negative_prompt": negative_prompt,
        "metadata_prompt": metadata_prompt,
        "metadata_negative_prompt": metadata_negative_prompt,
        "masks": masks,
        "regional_enabled": regional_enabled,
        "mask_prompts": mask_prompts,
        "assignments": assignments,
    }
    model_patch_data = {
        "version": REGIONAL_CONFIG_VERSION,
        "regional_attention": {
            "enabled": regional_enabled,
            "assignments": assignments,
            "masks": [
                {
                    "mask_id": mask.get("mask_id"),
                    "label": mask.get("label"),
                    "name": mask.get("name"),
                    "enabled": _as_bool(mask.get("enabled"), True),
                }
                for mask in masks
                if isinstance(mask, dict)
            ],
        },
        "layout_control": {
            "canvas": regional_prompt_data["canvas"],
        },
        "global_mod_guidance": {},
        "artist_mix": config.get("artist_mix") if isinstance(config.get("artist_mix"), dict) else {},
        "compatibility": {
            "schema": REGIONAL_PROMPT_DATA_SCHEMA,
            "version": REGIONAL_CONFIG_VERSION,
            "mask_scoped_prompts": True,
        },
    }
    regional_prompt_data["model_patch_data"] = model_patch_data
    return (
        positive_prompt,
        negative_prompt,
        metadata_prompt,
        metadata_negative_prompt,
        regional_prompt_data,
    )


def _parse_json_object(value: str | dict | None) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value or "{}")
        except json.JSONDecodeError as exc:
            raise ValueError("[EasyUseAnima] regional_prompt_data is not valid JSON.") from exc
        if isinstance(parsed, dict):
            return parsed
    return {}


def _regional_payload_canvas(payload: dict[str, Any]) -> tuple[int, int]:
    canvas = payload.get("canvas") if isinstance(payload.get("canvas"), dict) else {}
    width = max(8, _as_int(canvas.get("width"), 1024))
    height = max(8, _as_int(canvas.get("height"), 1024))
    return width, height


def _conditioning_set_values(conditioning, values: dict[str, Any]) -> list:
    out = []
    for item in conditioning or []:
        if isinstance(item, (list, tuple)) and len(item) >= 2 and isinstance(item[1], dict):
            metadata = dict(item[1])
            metadata.update(values)
            out.append([item[0], metadata])
        else:
            out.append(item)
    return out


def _regional_union_mask_for_ids(
    payload: dict[str, Any],
    mask_ids: list[int],
    width: int,
    height: int,
):
    try:
        import torch  # type: ignore
    except Exception as exc:
        raise RuntimeError("[EasyUseAnima] torch is required to convert regional masks to conditioning.") from exc

    selected_ids = set(mask_ids)
    mask_tensor = torch.zeros((height, width), dtype=torch.float32)
    masks = payload.get("masks") if isinstance(payload.get("masks"), list) else []
    for mask in masks:
        if not isinstance(mask, dict) or not _as_bool(mask.get("enabled"), True):
            continue
        mask_id = _as_int(mask.get("mask_id"), 0)
        if mask_id not in selected_ids:
            continue
        geometry = _normalize_mask_geometry(mask.get("geometry"))
        x0 = max(0, min(width - 1, int(round(geometry["x"] * width))))
        y0 = max(0, min(height - 1, int(round(geometry["y"] * height))))
        x1 = max(x0 + 1, min(width, int(round((geometry["x"] + geometry["width"]) * width))))
        y1 = max(y0 + 1, min(height, int(round((geometry["y"] + geometry["height"]) * height))))
        if geometry["type"] == "ellipse":
            yy = torch.arange(y0, y1, dtype=torch.float32).unsqueeze(1)
            xx = torch.arange(x0, x1, dtype=torch.float32).unsqueeze(0)
            cx = (x0 + x1 - 1) / 2.0
            cy = (y0 + y1 - 1) / 2.0
            rx = max(0.5, (x1 - x0) / 2.0)
            ry = max(0.5, (y1 - y0) / 2.0)
            ellipse = (((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2) <= 1.0
            mask_tensor[y0:y1, x0:x1] = torch.maximum(mask_tensor[y0:y1, x0:x1], ellipse.to(torch.float32))
        else:
            mask_tensor[y0:y1, x0:x1] = 1.0
    return mask_tensor.unsqueeze(0)


def _regional_mask_bounds_area(mask, canvas_width: int | None = None, canvas_height: int | None = None) -> tuple | None:
    try:
        import torch  # type: ignore
    except Exception:
        return None

    if not hasattr(mask, "shape"):
        return None
    if len(mask.shape) == 3:
        mask_2d = torch.max(torch.abs(mask), dim=0).values
    elif len(mask.shape) == 2:
        mask_2d = mask
    else:
        return None

    if mask_2d.numel() == 0 or torch.max(mask_2d != 0) == False:
        return None
    y, x = torch.where(mask_2d != 0)
    height = max(1, int(canvas_height or mask_2d.shape[-2]))
    width = max(1, int(canvas_width or mask_2d.shape[-1]))
    y0 = int(torch.min(y).item())
    y1 = int(torch.max(y).item())
    x0 = int(torch.min(x).item())
    x1 = int(torch.max(x).item())
    latent_height = max(1, height // 8)
    latent_width = max(1, width // 8)
    area_y = max(0, min(latent_height - 1, round(y0 / height * latent_height)))
    area_x = max(0, min(latent_width - 1, round(x0 / width * latent_width)))
    area_height = max(1, round((y1 - y0 + 1) / height * latent_height))
    area_width = max(1, round((x1 - x0 + 1) / width * latent_width))
    area_height = min(area_height, latent_height - area_y)
    area_width = min(area_width, latent_width - area_x)
    return (
        area_height,
        area_width,
        area_y,
        area_x,
    )


def _fit_to_1mp(width: int, height: int) -> tuple[int, int]:
    if width <= 0 or height <= 0:
        return width, height
    if width * height <= NAI_1MP:
        return width, height

    ratio = width / height
    target_w = (NAI_1MP * ratio) ** 0.5
    target_h = (NAI_1MP / ratio) ** 0.5
    new_w = max(LATENT_ALIGN, round(target_w / LATENT_ALIGN) * LATENT_ALIGN)
    new_h = max(LATENT_ALIGN, round(target_h / LATENT_ALIGN) * LATENT_ALIGN)
    while new_w * new_h > NAI_1MP and new_w > LATENT_ALIGN and new_h > LATENT_ALIGN:
        if new_w >= new_h:
            new_w -= LATENT_ALIGN
        else:
            new_h -= LATENT_ALIGN
    return new_w, new_h


def _post_random(host: str, port: int, body: dict) -> dict:
    try:
        import requests
    except ImportError:
        raise RuntimeError("[EasyUse Anima] requests is not installed. Install requirements.txt.")

    url = f"http://{host}:{int(port)}/api/comfyui/random"
    try:
        response = requests.post(url, json=body, timeout=HTTP_TIMEOUT)
    except requests.RequestException as exc:
        raise RuntimeError(f"[EasyUse Anima] NAIA API request failed: {exc}")

    if not response.ok:
        raise RuntimeError(
            f"[EasyUse Anima] NAIA API error HTTP {response.status_code}: {response.text[:300]}"
        )
    try:
        data = response.json()
    except ValueError:
        raise RuntimeError(f"[EasyUse Anima] NAIA API returned non-JSON: {response.text[:300]}")

    if not data.get("ok", True):
        raise RuntimeError(f"[EasyUse Anima] NAIA API returned error: {data}")
    return data


def _parse_random_response(resp: dict) -> tuple[str, str, int, int]:
    prompt = _clean_prompt(resp.get("prompt", "") or "")
    negative = _clean_prompt(resp.get("negative_prompt", "") or "")
    w_raw, h_raw = resp.get("width"), resp.get("height")
    if w_raw is None or h_raw is None:
        raise RuntimeError("[EasyUse Anima] NAIA response is missing width/height.")
    try:
        raw_width, raw_height = int(w_raw), int(h_raw)
    except (TypeError, ValueError):
        raise RuntimeError(f"[EasyUse Anima] Invalid NAIA width/height: {w_raw!r}, {h_raw!r}")
    width, height = _fit_to_1mp(raw_width, raw_height)
    return prompt, negative, width, height


def _get_workflow_node(extra_pnginfo, node_id: str):
    pnginfo = _single_value(extra_pnginfo)
    if not isinstance(pnginfo, dict):
        return None
    workflow = pnginfo.get("workflow")
    if not isinstance(workflow, dict):
        return None

    node_ids = str(node_id).split(":")
    nodes_list = workflow.get("nodes", [])
    definitions = workflow.get("definitions", {})
    if not isinstance(definitions, dict):
        definitions = {}
    subgraphs = definitions.get("subgraphs", [])
    if not isinstance(subgraphs, list):
        subgraphs = []

    found = None
    for individual_node_id in node_ids:
        if not isinstance(nodes_list, list):
            return None
        found = next(
            (
                node
                for node in nodes_list
                if isinstance(node, dict) and str(node.get("id")) == individual_node_id
            ),
            None,
        )
        if isinstance(found, dict):
            subgraph = next(
                (
                    graph
                    for graph in subgraphs
                    if isinstance(graph, dict) and str(graph.get("id")) == str(found.get("type"))
                ),
                None,
            )
            if isinstance(subgraph, dict) and isinstance(subgraph.get("nodes"), list):
                nodes_list = subgraph["nodes"]
    return found


def _profile_key(profile_index: int) -> str:
    return str(max(1, _as_int(profile_index, 1)))


def _wrap_profile_index(profile_index: int, profile_count: int) -> int:
    count = max(1, min(16, _as_int(profile_count, 1)))
    index = max(1, _as_int(profile_index, 1))
    return ((index - 1) % count) + 1


def _load_profile_data(profile_data: Any) -> dict[str, dict]:
    if isinstance(profile_data, dict):
        raw = profile_data
    else:
        try:
            raw = json.loads(str(profile_data or "{}"))
        except (TypeError, ValueError):
            raw = {}
    if not isinstance(raw, dict):
        return {}
    profiles: dict[str, dict] = {}
    for key, value in raw.items():
        if isinstance(value, dict):
            profiles[str(key)] = value
    return profiles


def _get_loras_list(kwargs: dict) -> list[dict]:
    loras_data = kwargs.get("loras")
    if isinstance(loras_data, dict) and "__value__" in loras_data:
        loras_data = loras_data["__value__"]
    if isinstance(loras_data, str):
        try:
            loras_data = json.loads(loras_data or "[]")
        except (TypeError, ValueError):
            loras_data = []
    if not isinstance(loras_data, list):
        return []
    return [item for item in loras_data if isinstance(item, dict)]


def _apply_lora_syntax_format(name: str) -> str:
    try:
        from py.nodes.utils import apply_lora_syntax_format  # type: ignore

        return str(apply_lora_syntax_format(name))
    except Exception:
        base_name = str(name).replace("\\", "/").rstrip("/").split("/")[-1]
        return os.path.splitext(base_name)[0]


def _fallback_lora_path(lora_name: str) -> str:
    try:
        import folder_paths  # type: ignore

        for candidate in (
            lora_name,
            f"{lora_name}.safetensors",
            f"{lora_name}.pt",
            f"{lora_name}.ckpt",
        ):
            path = folder_paths.get_full_path("loras", candidate)
            if path:
                return path
    except Exception:
        pass
    return lora_name


def _lora_stack_name(lora_name: str) -> str:
    value = str(lora_name or "").strip()
    if not value:
        return value

    try:
        import folder_paths  # type: ignore

        absolute_value = os.path.abspath(value)
        for root in folder_paths.get_folder_paths("loras"):
            absolute_root = os.path.abspath(root)
            try:
                relative = os.path.relpath(absolute_value, absolute_root)
            except ValueError:
                continue
            if relative == "." or relative.startswith(f"..{os.sep}") or relative == "..":
                continue
            return relative.replace("/", os.sep)
    except Exception:
        pass

    normalized = value.replace("\\", "/")
    marker = "/models/loras/"
    marker_index = normalized.casefold().rfind(marker)
    if marker_index >= 0:
        normalized = normalized[marker_index + len(marker):]
    return normalized.replace("/", os.sep)


def _dedupe_text_values(values) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        text = str(value or "").strip()
        if not text:
            continue
        key = text.casefold()
        if key in seen:
            continue
        seen.add(key)
        result.append(text)
    return result


def _trigger_words_from_value(value) -> list[str]:
    if isinstance(value, str):
        return _dedupe_text_values(_prompt_tokens(value))
    if isinstance(value, dict):
        for key in ("word", "name", "tag", "text"):
            if key in value:
                return _trigger_words_from_value(value.get(key))
        return []
    if isinstance(value, (list, tuple, set)):
        words: list[str] = []
        for item in value:
            words.extend(_trigger_words_from_value(item))
        return _dedupe_text_values(words)
    return []


def _metadata_json_paths_for_lora(lora_path: str) -> list[str]:
    path = str(lora_path or "").strip()
    if not path:
        return []
    base, _ext = os.path.splitext(path)
    candidates = [f"{base}.metadata.json", f"{path}.metadata.json"]
    return _dedupe_text_values(candidates)


def _load_lora_manager_metadata(lora_path: str) -> dict:
    for metadata_path in _metadata_json_paths_for_lora(lora_path):
        if not os.path.isfile(metadata_path):
            continue
        try:
            with open(metadata_path, "r", encoding="utf-8") as handle:
                data = json.load(handle)
        except (OSError, json.JSONDecodeError) as exc:
            logger.warning("[EasyUse Anima] failed to read LoRA metadata JSON %s: %s", metadata_path, exc)
            continue
        if isinstance(data, dict):
            return data
    return {}


def _lora_manager_trigger_words_from_metadata(metadata: dict) -> list[str]:
    if not isinstance(metadata, dict):
        return []

    words: list[str] = []
    for key in _TRIGGER_WORD_KEYS:
        words.extend(_trigger_words_from_value(metadata.get(key)))

    civitai = metadata.get("civitai")
    if isinstance(civitai, dict):
        for key in _TRIGGER_WORD_KEYS:
            words.extend(_trigger_words_from_value(civitai.get(key)))

    return _dedupe_text_values(words)


def _get_lora_manager_trigger_words(lora_path: str) -> list[str]:
    return _lora_manager_trigger_words_from_metadata(_load_lora_manager_metadata(lora_path))


def _get_lora_info(lora_name: str) -> tuple[str, list[str]]:
    fallback_path = _fallback_lora_path(lora_name)
    trigger_words = _get_lora_manager_trigger_words(fallback_path)
    if trigger_words:
        return fallback_path, trigger_words

    try:
        from py.utils.utils import get_lora_info  # type: ignore

        path, trigger_words = get_lora_info(lora_name)
        if not isinstance(trigger_words, list):
            trigger_words = []
        trigger_words = _dedupe_text_values(trigger_words)
        if trigger_words:
            return str(path), trigger_words
        json_trigger_words = _get_lora_manager_trigger_words(str(path))
        return str(path), json_trigger_words
    except Exception:
        return fallback_path, []


def _correct_style_prompt(prompt: str) -> str:
    return _correct_builder_prompt(prompt)



def _format_strength(value: float) -> str:
    text = f"{float(value):.6f}".rstrip("0").rstrip(".")
    return text or "0"


def _select_profile_values(
    profile_index: int,
    profile_count: int,
    profile_data: str,
    style_prompt: str,
    kwargs: dict,
) -> tuple[str, list[dict], int]:
    selected_index = _wrap_profile_index(profile_index, profile_count)
    profile = _load_profile_data(profile_data).get(_profile_key(selected_index), {})
    selected_style = str(profile.get("style_prompt", style_prompt or ""))
    profile_loras = profile.get("loras")
    if isinstance(profile_loras, list):
        loras = [item for item in profile_loras if isinstance(item, dict)]
    else:
        loras = _get_loras_list(kwargs)
    return selected_style, loras, selected_index


def _lora_combo_values() -> list[str]:
    try:
        import folder_paths  # type: ignore

        names = [str(name) for name in folder_paths.get_filename_list("loras")]
    except Exception:
        names = []
    values = ["None"]
    seen = {"none"}
    for name in names:
        text = str(name or "").strip()
        if not text:
            continue
        key = text.casefold()
        if key in seen:
            continue
        seen.add(key)
        values.append(text)
    return values


def _lora_model_exists(lora_name: str) -> bool | None:
    name = str(lora_name or "").strip()
    if not name or name == "None":
        return True

    try:
        import folder_paths  # type: ignore
    except Exception:
        return None

    candidates = _dedupe_text_values((
        name,
        name.replace("\\", "/"),
        name.replace("/", os.sep),
    ))
    for candidate in candidates:
        if folder_paths.get_full_path("loras", candidate):
            return True
    return False


def _missing_lora_display_name(input_name: str, stack_name: str) -> str:
    input_text = str(input_name or "").strip()
    stack_text = str(stack_name or "").strip()
    if not input_text or input_text == stack_text:
        return stack_text
    normalized_input = input_text.replace("\\", "/").casefold()
    normalized_stack = stack_text.replace("\\", "/").casefold()
    if normalized_input == normalized_stack:
        return stack_text
    return f"{stack_text} (input: {input_text})"


def _raise_missing_loras(profile_index: int, missing_loras: list[str]):
    if not missing_loras:
        return
    lines = "\n".join(f"- {name}" for name in missing_loras)
    message = (
        "[EasyUse Anima] LoRA Preset profile "
        f"{profile_index} contains missing LoRA model(s):\n"
        f"{lines}\n"
        "Install the missing file under ComfyUI/models/loras or remove it from the profile."
    )
    logger.error(message)
    raise RuntimeError(message)


class EasyUseAnimaPromptCorrector:
    """ANIMA prompt order correction node."""

    DESCRIPTION = (
        "Normalizes ANIMA prompt text, keeps natural-language casing, reorders known "
        "ANIMA sections, and reports unknown or duplicate tags."
    )
    OUTPUT_TOOLTIPS = (
        "Prompt text after ANIMA ordering and syntax cleanup.",
        "JSON report containing changed state, unknown tags, duplicate tags, warnings, and sections.",
    )

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "prompt": ("STRING", {
                    "multiline": True,
                    "default": "",
                    "tooltip": "Comma-separated prompt text to normalize and reorder for ANIMA.",
                }),
                "artist_overrides": ("STRING", {
                    "multiline": True,
                    "default": "",
                    "tooltip": "Comma- or newline-separated manual triggers to treat like artist tags.",
                }),
                "artist_exclusions": ("STRING", {
                    "multiline": True,
                    "default": "",
                    "tooltip": "Comma- or newline-separated triggers that must not be treated as artists.",
                }),
            }
        }

    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("corrected_prompt", "report")
    FUNCTION = "correct"
    CATEGORY = "EasyUse Anima/Prompt"

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        return _stable_change_key({
            "mode": "prompt_corrector",
            **{key: str(value) for key, value in sorted(kwargs.items())},
        })

    def correct(
        self,
        prompt: str,
        artist_overrides: str,
        artist_exclusions: str,
    ):
        try:
            kb = load_knowledge_base(allow_missing=True)
            result = correct_prompt(
                str(prompt or ""),
                profile="prompt",
                knowledge_base=kb,
                validate_artist_tags=False,
                artist_overrides=_split_tag_text(artist_overrides),
                artist_exclusions=_split_tag_text(artist_exclusions),
            )
        except Exception as exc:
            raise RuntimeError(f"[EasyUse Anima] prompt correction failed: {exc}") from exc

        report = {
            "changed": result.changed,
            "unknown_tags": list(result.unknown_tags),
            "duplicate_tags": list(result.duplicate_tags),
            "warnings": list(result.warnings),
            "sections": result.report.get("sections", []),
        }
        return (
            result.text,
            json.dumps(report, ensure_ascii=False, indent=2),
        )


class EasyUseAnimaWildcard:
    """Expand Impact Pack compatible wildcard and dynamic prompt syntax."""

    DESCRIPTION = (
        "Expands EasyUse Anima wildcard files and dynamic prompt syntax with fixed, sequential, "
        "and reproducible modes."
    )
    OUTPUT_TOOLTIPS = (
        "Expanded prompt text.",
        "Seed after applying the seed control option.",
    )

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "text": ("STRING", {
                    "multiline": True,
                    "default": "",
                    "tooltip": "Prompt text with wildcard syntax such as __style__ or {2::a|5::b|c}.",
                }),
                "populated_text": ("STRING", {
                    "multiline": True,
                    "default": "",
                    "tooltip": "Cached expanded prompt used by fixed and reproduce modes.",
                }),
                "mode": (WILDCARD_MODE_LABELS, {
                    "default": WILDCARD_MODE_LABELS[0],
                    "tooltip": (
                        "일반 채우기: seed-based random fill. 고정/재현: cached text. "
                        "순차: seed modulo each wildcard option count."
                    ),
                }),
                "seed": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": MAX_SEED,
                    "tooltip": "Wildcard seed. Sequential mode uses seed % option_count for each wildcard.",
                }),
                "seed_after_generate": (SEED_CONTROL_MODES, {
                    "default": SEED_CONTROL_FIXED,
                    "tooltip": "Seed control after generation: fixed, randomize, increment, or decrement.",
                }),
            },
            "hidden": {
                "workflow_prompt": "PROMPT",
                "extra_pnginfo": "EXTRA_PNGINFO",
                "unique_id": "UNIQUE_ID",
            },
        }

    RETURN_TYPES = ("STRING", "INT")
    RETURN_NAMES = ("text", "seed")
    FUNCTION = "generate"
    CATEGORY = "EasyUse Anima/Prompt"

    @classmethod
    def _widget_input_names(cls):
        return tuple(cls.INPUT_TYPES().get("required", {}).keys())

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        mode = normalize_wildcard_mode(kwargs.get("mode", WILDCARD_MODE_LABELS[0]))
        seed_control = str(kwargs.get("seed_after_generate", SEED_CONTROL_FIXED) or "")
        text = str(kwargs.get("text", "") or "")
        if (
            mode in {WILDCARD_MODE_POPULATE, WILDCARD_MODE_FIXED, WILDCARD_MODE_SEQUENTIAL}
            and seed_control == SEED_CONTROL_RANDOMIZE
            and has_wildcard_syntax(text)
        ):
            return float("nan")
        return _stable_change_key({
            "mode": "wildcard",
            "wildcard_sources": wildcard_sources_signature(),
            **{key: str(value) for key, value in sorted(kwargs.items())},
        })

    @classmethod
    def _update_metadata_cache(
        cls,
        workflow_prompt,
        extra_pnginfo,
        unique_id,
        populated_text: str,
        mode: str,
        seed: int,
    ) -> None:
        node_id = _single_value(unique_id)
        if node_id is None:
            return
        node_id = str(node_id)
        updates = {
            "populated_text": populated_text,
            "mode": mode,
            "seed": int(seed),
        }

        if isinstance(workflow_prompt, dict):
            prompt_node = workflow_prompt.get(node_id)
            if isinstance(prompt_node, dict):
                inputs = prompt_node.setdefault("inputs", {})
                for name, value in updates.items():
                    inputs[name] = value

        workflow_node = _get_workflow_node(extra_pnginfo, node_id)
        if workflow_node is None:
            return

        input_names = cls._widget_input_names()
        widgets_values = workflow_node.setdefault("widgets_values", [])
        for name, value in updates.items():
            if name not in input_names:
                continue
            index = input_names.index(name)
            while len(widgets_values) <= index:
                widgets_values.append(None)
            widgets_values[index] = value

    @staticmethod
    def _ui(
        populated_text: str,
        mode: str,
        seed: int,
        status: str,
        used_keys: tuple[str, ...],
        missing_keys: tuple[str, ...],
    ):
        return {
            "wildcard": [{
                "populated_text": populated_text,
                "mode": mode,
                "seed": seed,
                "status": status,
                "used_keys": list(used_keys),
                "missing_keys": list(missing_keys),
            }]
        }

    def generate(
        self,
        text: str,
        populated_text: str,
        mode: str,
        seed: int,
        seed_after_generate: str,
        workflow_prompt=None,
        extra_pnginfo=None,
        unique_id=None,
    ):
        mode_key = normalize_wildcard_mode(mode)
        seed_value = normalize_seed(seed)
        used_keys: tuple[str, ...] = ()
        missing_keys: tuple[str, ...] = ()

        if mode_key == WILDCARD_MODE_REPRODUCE:
            output_text = str(populated_text if populated_text else text or "")
            status = mode_key
            metadata_mode = str(mode or WILDCARD_MODE_LABELS[3])
        else:
            expansion = expand_wildcards(str(text or ""), seed=seed_value, mode=mode_key)
            output_text = expansion.text
            used_keys = expansion.used_keys
            missing_keys = expansion.missing_keys
            status = WILDCARD_MODE_SEQUENTIAL if mode_key == WILDCARD_MODE_SEQUENTIAL else mode_key
            metadata_mode = WILDCARD_MODE_LABELS[3]

        effective_seed_control = (
            SEED_CONTROL_INCREMENT
            if mode_key == WILDCARD_MODE_SEQUENTIAL
            else seed_after_generate
        )
        next_seed_value = next_seed(seed_value, effective_seed_control)
        self._update_metadata_cache(
            workflow_prompt,
            extra_pnginfo,
            unique_id,
            output_text,
            metadata_mode,
            seed_value,
        )
        return {
            "ui": self._ui(
                output_text,
                str(mode or WILDCARD_MODE_LABELS[0]),
                next_seed_value,
                status,
                used_keys,
                missing_keys,
            ),
            "result": (output_text, next_seed_value),
        }


class EasyUseAnimaPromptBuilder:
    """Build cleaned ANIMA prompts for NAIA and Anima Mod Guidance workflows."""

    DESCRIPTION = (
        "Combines quality, trigger, LoRA trigger, body, and trailing prompt fields into "
        "ANIMA-friendly prompt outputs, including metadata and Mod Guidance outputs."
    )
    OUTPUT_TOOLTIPS = (
        "Final positive prompt. When Mod Guidance is enabled, leading quality tags are excluded.",
        "Quality prompt text intended for Anima Mod Guidance.",
        "Boolean flag passed through for Anima Mod Guidance workflow control.",
        "Prompt text for metadata, independent from Mod Guidance routing and metadata filters.",
    )

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "use_anima_mod_guidance": ("BOOLEAN", {
                    "default": False,
                    "tooltip": (
                        "true: output prompt excludes quality fields and sends them "
                        "through anima_mod_guidance_quality_tags."
                    ),
                }),
                "pin_trigger_tags_to_front": ("BOOLEAN", {
                    "default": False,
                    "tooltip": (
                        "true: keep trigger/artist and LoRA trigger fields at the very front "
                        "instead of placing quality tags before them."
                    ),
                }),
                "lora_trigger_tags": ("STRING", {
                    "multiline": False,
                    "default": "",
                    "tooltip": "One-line trigger tags received from a LoRA manager or pasted manually.",
                }),
                "quality_tags": ("STRING", {
                    "multiline": True,
                    "default": DEFAULT_QUALITY_TAGS,
                    "tooltip": "Leading quality tags. With AMG enabled, these are excluded from prompt output.",
                }),
                "trigger_and_artist_tags": ("STRING", {
                    "multiline": True,
                    "default": "",
                    "tooltip": "Manual model triggers and @artist tags.",
                }),
                "prompt": ("STRING", {
                    "multiline": True,
                    "default": "",
                    "tooltip": "Main prompt body. This is the expected place for NAIA output.",
                }),
                "trailing_quality_tags": ("STRING", {
                    "multiline": True,
                    "default": DEFAULT_TRAILING_QUALITY_TAGS,
                    "tooltip": "Trailing quality or style tags.",
                }),
            }
        }

    RETURN_TYPES = ("STRING", "STRING", "BOOLEAN", "STRING")
    RETURN_NAMES = (
        "prompt",
        "anima_mod_guidance_quality_tags",
        "use_anima_mod_guidance",
        "metadata_prompt",
    )
    FUNCTION = "build"
    CATEGORY = "EasyUse Anima/Prompt"

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        return _stable_change_key({
            "mode": "prompt_builder",
            "metadata_filter_words": resolve_metadata_filter_words(),
            **{key: str(value) for key, value in sorted(kwargs.items())},
        })

    def build(
        self,
        use_anima_mod_guidance: bool,
        pin_trigger_tags_to_front: bool,
        quality_tags: str,
        trigger_and_artist_tags: str,
        lora_trigger_tags: str,
        prompt: str,
        trailing_quality_tags: str,
    ):
        use_amg = _as_bool(use_anima_mod_guidance, False)
        pin_triggers = _as_bool(pin_trigger_tags_to_front, False)

        trigger_prompt = _join_prompt_tokens(trigger_and_artist_tags, lora_trigger_tags)
        quality_prompt = _join_prompt_tokens(quality_tags)
        body_prompt = _join_prompt_tokens(prompt)
        trailing_prompt = _join_prompt_tokens(trailing_quality_tags)

        if pin_triggers:
            metadata_body = _correct_builder_prompt(
                _join_prompt_tokens(quality_tags, body_prompt)
            )
            regular_prompt = _join_prompt_tokens(trigger_prompt, metadata_body, trailing_prompt)
            amg_prompt = _join_prompt_tokens(
                trigger_prompt,
                _correct_builder_prompt(body_prompt),
                trailing_prompt,
            )
            metadata_prompt = regular_prompt
        else:
            metadata_core = _correct_builder_prompt(
                _join_prompt_tokens(
                    quality_tags,
                    trigger_prompt,
                    body_prompt,
                ),
                artist_overrides=trigger_prompt,
            )
            metadata_prompt = _join_prompt_tokens(metadata_core, trailing_prompt)
            regular_prompt = metadata_prompt
            amg_core = _correct_builder_prompt(
                _join_prompt_tokens(trigger_prompt, body_prompt),
                artist_overrides=trigger_prompt,
            )
            amg_prompt = _join_prompt_tokens(amg_core, trailing_prompt)

        metadata_prompt = _filter_metadata_prompt(
            metadata_prompt,
            resolve_metadata_filter_words(),
        )
        output_prompt = amg_prompt if use_amg else regular_prompt

        return (
            output_prompt,
            quality_prompt,
            use_amg,
            metadata_prompt,
        )


class EasyUseAnimaPromptStudio(EasyUseAnimaPromptBuilder):
    """Prompt Builder variant with enhanced front-end editing helpers."""

    DESCRIPTION = (
        "An enhanced Prompt Builder with front-end editing, autocomplete, and tag highlighting helpers."
    )

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "use_anima_mod_guidance": ("BOOLEAN", {
                    "default": False,
                    "tooltip": (
                        "true: output prompt excludes quality fields and sends them "
                        "through anima_mod_guidance_quality_tags."
                    ),
                }),
                "pin_trigger_tags_to_front": ("BOOLEAN", {
                    "default": False,
                    "tooltip": (
                        "true: keep trigger/artist and LoRA trigger fields at the very front "
                        "instead of placing quality tags before them."
                    ),
                }),
                "lora_trigger_tags": ("STRING", {
                    "multiline": False,
                    "default": "",
                    "tooltip": "One-line trigger tags received from a LoRA manager or pasted manually.",
                }),
                "quality_tags": ("STRING", {
                    "multiline": True,
                    "default": DEFAULT_QUALITY_TAGS,
                    "tooltip": "Leading quality tags. With AMG enabled, these are excluded from prompt output.",
                }),
                "trigger_and_artist_tags": ("STRING", {
                    "multiline": True,
                    "default": "",
                    "tooltip": "Manual model triggers and @artist tags.",
                }),
                "prompt": ("STRING", {
                    "multiline": True,
                    "default": "",
                    "tooltip": "Main prompt body. This is the expected place for NAIA output.",
                }),
                "trailing_quality_tags": ("STRING", {
                    "multiline": True,
                    "default": DEFAULT_TRAILING_QUALITY_TAGS,
                    "tooltip": "Trailing quality or style tags.",
                }),
            }
        }

    CATEGORY = "EasyUse Anima/Prompt"

    def build(
        self,
        use_anima_mod_guidance: bool,
        pin_trigger_tags_to_front: bool,
        quality_tags: str,
        trigger_and_artist_tags: str,
        lora_trigger_tags: str,
        prompt: str,
        trailing_quality_tags: str,
    ):
        result = super().build(
            use_anima_mod_guidance,
            pin_trigger_tags_to_front,
            quality_tags,
            trigger_and_artist_tags,
            lora_trigger_tags,
            prompt,
            trailing_quality_tags,
        )
        return {
            "ui": {
                "prompt_studio_inputs": [{
                    "lora_trigger_tags": str(lora_trigger_tags or ""),
                    "quality_tags": str(quality_tags or ""),
                    "trigger_and_artist_tags": str(trigger_and_artist_tags or ""),
                    "prompt": str(prompt or ""),
                    "trailing_quality_tags": str(trailing_quality_tags or ""),
                }]
            },
            "result": result,
        }


class EasyUseAnimaPromptStudioAdvanced:
    """Dynamic positive/negative Prompt Studio with serialized field blocks."""

    DESCRIPTION = (
        "Advanced Prompt Studio with reorderable positive and negative fields, NAIA fill support, "
        "trigger input handling, Mod Guidance routing, metadata outputs, and latent resolution output."
    )
    OUTPUT_TOOLTIPS = (
        "Final positive prompt assembled from enabled positive fields.",
        "Final negative prompt assembled from enabled negative fields.",
        "Positive quality fields routed to Anima Mod Guidance.",
        "Negative quality fields routed to Anima Mod Guidance.",
        "Boolean flag passed through for Anima Mod Guidance workflow control.",
        "Boolean flag passed through for negative Anima Mod Guidance workflow control.",
        "Positive metadata prompt with metadata filters applied.",
        "Negative metadata prompt with metadata filters applied.",
        "Selected latent width.",
        "Selected latent height.",
    )

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "use_naia": ("BOOLEAN", {
                    "default": False,
                    "tooltip": (
                        "Internal request flag. The front-end exposes this as the NAIA Prompt field's "
                        "'Fill from NAIA' button, which fills that field with a fresh NAIA random prompt."
                    ),
                }),
                "consume_naia_on_queue": ("BOOLEAN", {
                    "default": True,
                    "tooltip": (
                        "Internal one-shot mode. Successful NAIA fills are saved with the request flag off "
                        "so loaded workflows reuse the stored prompt."
                    ),
                }),
                "use_anima_mod_guidance": ("BOOLEAN", {
                    "default": False,
                    "tooltip": (
                        "true: positive output excludes quality fields and sends them "
                        "through the mod guidance quality output."
                    ),
                }),
                "resolution_bucket": ("STRING", {
                    "default": DEFAULT_ADVANCED_RESOLUTION_BUCKET,
                    "tooltip": "Internal selected latent resolution bucket.",
                }),
                "resolution_size": ("STRING", {
                    "default": DEFAULT_ADVANCED_RESOLUTION_SIZE,
                    "tooltip": "Internal selected latent resolution, formatted as width * height (ratio).",
                }),
                "resolution_custom_width": ("INT", {
                    "default": 1024,
                    "min": 32,
                    "max": 8192,
                    "step": 32,
                    "tooltip": "Internal custom latent width. Values are snapped to multiples of 32.",
                }),
                "resolution_custom_height": ("INT", {
                    "default": 1024,
                    "min": 32,
                    "max": 8192,
                    "step": 32,
                    "tooltip": "Internal custom latent height. Values are snapped to multiples of 32.",
                }),
                "pin_trigger_tags_to_front": ("BOOLEAN", {
                    "default": False,
                    "tooltip": "Legacy internal flag. Trigger field Pin buttons control trigger placement.",
                }),
                "advanced_fields": ("STRING", {
                    "multiline": True,
                    "default": _advanced_fields_json(),
                    "tooltip": "Internal JSON payload for Advanced Prompt Studio fields.",
                }),
                "use_negative_anima_mod_guidance": ("BOOLEAN", {
                    "default": False,
                    "tooltip": (
                        "true: negative output excludes negative quality fields and sends them "
                        "through the negative Mod Guidance output."
                    ),
                }),
                "wildcard_mode": (WILDCARD_MODE_LABELS, {
                    "default": WILDCARD_MODE_LABELS[1],
                    "tooltip": "Wildcard mode. 고정 is the compatibility default; 순차 uses seed % option_count and increments seed after queue.",
                }),
                "wildcard_seed": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": MAX_SEED,
                    "tooltip": "Wildcard seed used by Advanced Prompt Studio fields.",
                }),
                "wildcard_seed_after_generate": (SEED_CONTROL_MODES, {
                    "default": SEED_CONTROL_FIXED,
                    "tooltip": "Seed control after wildcard generation.",
                }),
            },
            "optional": _FlexibleOptionalInputType("STRING"),
            "hidden": {
                "workflow_prompt": "PROMPT",
                "extra_pnginfo": "EXTRA_PNGINFO",
                "unique_id": "UNIQUE_ID",
            },
        }

    RETURN_TYPES = (
        "STRING",
        "STRING",
        "STRING",
        "STRING",
        "BOOLEAN",
        "BOOLEAN",
        "STRING",
        "STRING",
        "INT",
        "INT",
    )
    RETURN_NAMES = (
        "positive_prompt",
        "negative_prompt",
        "anima_mod_guidance_quality_tags",
        "anima_mod_guidance_negative_prompt",
        "use_anima_mod_guidance",
        "use_negative_anima_mod_guidance",
        "metadata_prompt",
        "metadata_negative_prompt",
        "width",
        "height",
    )
    FUNCTION = "build"
    CATEGORY = "EasyUse Anima/Prompt"

    @classmethod
    def _widget_input_names(cls) -> list[str]:
        return list(cls.INPUT_TYPES()["required"].keys())

    @classmethod
    def IS_CHANGED(
        cls,
        use_naia: bool = False,
        consume_naia_on_queue: bool = True,
        use_anima_mod_guidance: bool = False,
        pin_trigger_tags_to_front: bool = False,
        use_negative_anima_mod_guidance: bool = False,
        advanced_fields: str = "",
        resolution_bucket: str = DEFAULT_ADVANCED_RESOLUTION_BUCKET,
        resolution_size: str = DEFAULT_ADVANCED_RESOLUTION_SIZE,
        resolution_custom_width: int = 1024,
        resolution_custom_height: int = 1024,
        wildcard_mode: str = WILDCARD_MODE_LABELS[1],
        wildcard_seed: int = 0,
        wildcard_seed_after_generate: str = SEED_CONTROL_FIXED,
        **kwargs,
    ):
        fields = _normalize_advanced_fields(advanced_fields)
        if _as_bool(use_naia, False) and (
            _advanced_has_enabled_naia(fields)
            or _advanced_uses_naia_resolution(resolution_bucket)
        ):
            return float("nan")
        effective_fields = _apply_advanced_field_inputs(fields, kwargs)
        wildcard_mode_key = normalize_wildcard_mode(wildcard_mode)
        wildcard_active = wildcard_mode_key in {WILDCARD_MODE_POPULATE, WILDCARD_MODE_FIXED, WILDCARD_MODE_SEQUENTIAL}
        wildcard_text = "\n".join(str(field.get("text") or "") for field in effective_fields)
        if (
            wildcard_active
            and str(wildcard_seed_after_generate or "") == SEED_CONTROL_RANDOMIZE
            and has_wildcard_syntax(wildcard_text)
        ):
            return float("nan")
        return _stable_change_key({
            "mode": "prompt_studio_advanced",
            "metadata_filter_words": resolve_metadata_filter_words(),
            "wildcard_sources": wildcard_sources_signature() if wildcard_active else {},
            "wildcard_mode": wildcard_mode_key,
            "wildcard_seed": normalize_seed(wildcard_seed),
            "wildcard_seed_after_generate": str(wildcard_seed_after_generate or SEED_CONTROL_FIXED),
            "use_anima_mod_guidance": _as_bool(use_anima_mod_guidance, False),
            "use_negative_anima_mod_guidance": _as_bool(use_negative_anima_mod_guidance, False),
            "resolution": _advanced_resolution_from_selection(
                resolution_bucket,
                resolution_size,
                resolution_custom_width,
                resolution_custom_height,
            ),
            "pin_trigger_tags_to_front": _as_bool(pin_trigger_tags_to_front, False),
            "advanced_fields": _advanced_fields_json(effective_fields),
        })

    @classmethod
    def _update_metadata_fields(
        cls,
        workflow_prompt,
        extra_pnginfo,
        unique_id,
        advanced_fields: str,
        use_naia: bool,
        extra_updates: dict[str, Any] | None = None,
    ) -> None:
        node_id = _single_value(unique_id)
        if node_id is None:
            return
        node_id = str(node_id)
        updates = {
            "use_naia": _as_bool(use_naia, False),
            "advanced_fields": advanced_fields,
        }
        if extra_updates:
            updates.update(extra_updates)

        if isinstance(workflow_prompt, dict):
            prompt_node = workflow_prompt.get(node_id)
            if isinstance(prompt_node, dict):
                inputs = prompt_node.setdefault("inputs", {})
                for name, value in updates.items():
                    inputs[name] = value

        workflow_node = _get_workflow_node(extra_pnginfo, node_id)
        if workflow_node is None:
            return

        if "advanced_fields" in updates:
            properties = workflow_node.setdefault("properties", {})
            if not isinstance(properties, dict):
                properties = {}
                workflow_node["properties"] = properties
            properties[ADVANCED_FIELDS_WORKFLOW_PROPERTY] = updates["advanced_fields"]

        input_names = cls._widget_input_names()
        widgets_values = workflow_node.setdefault("widgets_values", [])
        for name, value in updates.items():
            if name not in input_names:
                continue
            index = input_names.index(name)
            while len(widgets_values) <= index:
                widgets_values.append(None)
            widgets_values[index] = value

    @staticmethod
    def _ui(
        advanced_fields: str,
        use_naia: bool,
        field_inputs: dict | None = None,
        extra_payload: dict[str, Any] | None = None,
    ):
        payload = {
            "prompt_studio_advanced": [{
                "advanced_fields": advanced_fields,
                "use_naia": _as_bool(use_naia, False),
                "field_inputs": field_inputs or {},
            }]
        }
        if extra_payload:
            payload["prompt_studio_advanced"][0].update(extra_payload)
        return payload

    def build(
        self,
        use_naia: bool,
        consume_naia_on_queue: bool,
        use_anima_mod_guidance: bool,
        pin_trigger_tags_to_front: bool,
        advanced_fields: str,
        use_negative_anima_mod_guidance: bool = False,
        wildcard_mode: str = WILDCARD_MODE_LABELS[1],
        wildcard_seed: int = 0,
        wildcard_seed_after_generate: str = SEED_CONTROL_FIXED,
        resolution_bucket: str = DEFAULT_ADVANCED_RESOLUTION_BUCKET,
        resolution_size: str = DEFAULT_ADVANCED_RESOLUTION_SIZE,
        resolution_custom_width: int = 1024,
        resolution_custom_height: int = 1024,
        workflow_prompt=None,
        extra_pnginfo=None,
        unique_id=None,
        **field_inputs,
    ):
        fields = _normalize_advanced_fields(advanced_fields)
        saved_fields = _clone_advanced_fields(fields)
        effective_fields = _apply_advanced_field_inputs(fields, field_inputs)
        effective_field_inputs = _advanced_field_input_values(field_inputs)
        requested_use_naia = _as_bool(use_naia, False)
        enabled_naia_panes = _advanced_enabled_naia_panes(fields)
        use_naia_resolution = _advanced_uses_naia_resolution(resolution_bucket)
        live_use_naia = requested_use_naia and (bool(enabled_naia_panes) or use_naia_resolution)
        metadata_use_naia = live_use_naia
        metadata_updates: dict[str, Any] = {}
        ui_updates: dict[str, Any] = {}
        wildcard_mode_key = normalize_wildcard_mode(wildcard_mode)
        wildcard_seed_value = normalize_seed(wildcard_seed)
        wildcard_effective_seed_control = (
            SEED_CONTROL_INCREMENT
            if wildcard_mode_key == WILDCARD_MODE_SEQUENTIAL
            else str(wildcard_seed_after_generate or SEED_CONTROL_FIXED)
        )
        width, height = _advanced_resolution_from_selection(
            resolution_bucket,
            resolution_size,
            resolution_custom_width,
            resolution_custom_height,
        )

        if live_use_naia:
            naia_settings = resolve_naia_settings()
            body = EasyUseAnimaNAIARandomPrompt._make_request_body(
                _as_bool(naia_settings["use_naia_settings"], True),
                naia_settings["pre_prompt"],
                naia_settings["post_prompt"],
                naia_settings["auto_hide"],
                naia_settings["preprocessing"],
            )
            resp = _post_random(naia_settings["host"], naia_settings["port"], body)
            naia_prompt, naia_negative, naia_width, naia_height = _parse_random_response(resp)
            if "positive" in enabled_naia_panes:
                saved_fields = _set_naia_field_text(saved_fields, "positive", naia_prompt)
                effective_fields = _set_naia_field_text(effective_fields, "positive", naia_prompt)
            if "negative" in enabled_naia_panes:
                saved_fields = _set_naia_field_text(saved_fields, "negative", naia_negative)
                effective_fields = _set_naia_field_text(effective_fields, "negative", naia_negative)
            if use_naia_resolution:
                width, height = _scale_naia_resolution(naia_width, naia_height, naia_settings)
                resolution_label = _resolution_label(width, height)
                metadata_updates.update({
                    "resolution_bucket": CUSTOM_ADVANCED_RESOLUTION_BUCKET,
                    "resolution_size": resolution_label,
                    "resolution_custom_width": width,
                    "resolution_custom_height": height,
                })
                ui_updates.update({
                    "resolution_bucket": NAIA_ADVANCED_RESOLUTION_BUCKET,
                    "resolution_size": resolution_label,
                    "resolution_custom_width": width,
                    "resolution_custom_height": height,
                })
            metadata_use_naia = False

        ui_fields = _clone_advanced_fields(saved_fields)
        saved_fields, saved_wildcard = _expand_advanced_wildcard_fields(
            saved_fields,
            wildcard_seed_value,
            wildcard_mode_key,
        )
        effective_fields, effective_wildcard = _expand_advanced_wildcard_fields(
            effective_fields,
            wildcard_seed_value,
            wildcard_mode_key,
        )
        wildcard_changed = bool(saved_wildcard["changed"] or effective_wildcard["changed"])
        if wildcard_mode_key in {WILDCARD_MODE_POPULATE, WILDCARD_MODE_FIXED, WILDCARD_MODE_SEQUENTIAL}:
            next_wildcard_seed = next_seed(wildcard_seed_value, wildcard_effective_seed_control)
            ui_updates.update({
                "wildcard_mode": str(wildcard_mode or WILDCARD_MODE_LABELS[1]),
                "wildcard_seed": next_wildcard_seed,
                "wildcard_seed_after_generate": wildcard_effective_seed_control,
                "wildcard_used_keys": list(effective_wildcard["used_keys"]),
                "wildcard_missing_keys": list(effective_wildcard["missing_keys"]),
            })
            if wildcard_changed:
                metadata_updates.update({
                    "wildcard_mode": WILDCARD_MODE_LABELS[3],
                    "wildcard_seed": wildcard_seed_value,
                    "wildcard_seed_after_generate": SEED_CONTROL_FIXED,
                })

        fields_json = _advanced_fields_json(saved_fields)
        ui_fields_json = _advanced_fields_json(ui_fields if wildcard_changed else saved_fields)
        if live_use_naia or wildcard_changed:
            self._update_metadata_fields(
                workflow_prompt,
                extra_pnginfo,
                unique_id,
                fields_json,
                metadata_use_naia,
                metadata_updates,
            )

        result = _build_advanced_prompts(
            effective_fields,
            use_anima_mod_guidance,
            use_negative_anima_mod_guidance,
            pin_trigger_tags_to_front,
        )
        return {
            "ui": self._ui(ui_fields_json, requested_use_naia, effective_field_inputs, ui_updates),
            "result": (*result, width, height),
        }


class EasyUseAnimaPromptStudioRegional:
    """Mask-scoped Prompt Studio with serialized prompt fields and mask config."""

    DESCRIPTION = (
        "Regional Prompt Studio that stores numbered user masks and applies selected "
        "positive prompt fields only inside those masks. Connect regional_prompt_data "
        "to Anima Regional Conditioning to create KSampler-ready conditionings."
    )
    OUTPUT_TOOLTIPS = (
        "Metadata positive prompt with global and mask-scoped prompt fields included.",
        "Metadata negative prompt with metadata filters applied.",
        "Selected latent width used by the mask editor canvas.",
        "Selected latent height used by the mask editor canvas.",
        "Bundled regional prompt, mask, and model-patch data for Anima Regional Conditioning.",
    )

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "regional_fields": ("STRING", {
                    "multiline": True,
                    "default": _regional_fields_json(),
                    "tooltip": "Internal JSON payload for Regional Prompt Studio fields.",
                }),
                "regional_config": ("STRING", {
                    "multiline": True,
                    "default": _regional_config_json(),
                    "tooltip": "Internal JSON payload for numbered masks and mask editor settings.",
                }),
                "resolution_bucket": ("STRING", {
                    "default": DEFAULT_ADVANCED_RESOLUTION_BUCKET,
                    "tooltip": "Internal selected latent resolution bucket.",
                }),
                "resolution_size": ("STRING", {
                    "default": DEFAULT_ADVANCED_RESOLUTION_SIZE,
                    "tooltip": "Internal selected latent resolution, formatted as width * height (ratio).",
                }),
                "resolution_custom_width": ("INT", {
                    "default": 1024,
                    "min": 32,
                    "max": 8192,
                    "step": 32,
                    "tooltip": "Internal custom latent width. Values are snapped to multiples of 32.",
                }),
                "resolution_custom_height": ("INT", {
                    "default": 1024,
                    "min": 32,
                    "max": 8192,
                    "step": 32,
                    "tooltip": "Internal custom latent height. Values are snapped to multiples of 32.",
                }),
                "wildcard_mode": (WILDCARD_MODE_LABELS, {
                    "default": WILDCARD_MODE_LABELS[1],
                    "tooltip": "Wildcard mode for prompt fields.",
                }),
                "wildcard_seed": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": MAX_SEED,
                    "tooltip": "Wildcard seed used by Regional Prompt Studio fields.",
                }),
                "wildcard_seed_after_generate": (SEED_CONTROL_MODES, {
                    "default": SEED_CONTROL_FIXED,
                    "tooltip": "Seed control after wildcard generation.",
                }),
            },
            "optional": _FlexibleOptionalInputType("STRING"),
            "hidden": {
                "workflow_prompt": "PROMPT",
                "extra_pnginfo": "EXTRA_PNGINFO",
                "unique_id": "UNIQUE_ID",
            },
        }

    RETURN_TYPES = (
        "STRING",
        "STRING",
        "INT",
        "INT",
        REGIONAL_PROMPT_DATA_TYPE,
    )
    RETURN_NAMES = (
        "metadata_prompt",
        "metadata_negative_prompt",
        "width",
        "height",
        "regional_prompt_data",
    )
    FUNCTION = "build"
    CATEGORY = "EasyUse Anima/Prompt"

    @classmethod
    def _widget_input_names(cls) -> list[str]:
        return list(cls.INPUT_TYPES()["required"].keys())

    @classmethod
    def IS_CHANGED(
        cls,
        regional_fields: str = "",
        regional_config: str = "",
        resolution_bucket: str = DEFAULT_ADVANCED_RESOLUTION_BUCKET,
        resolution_size: str = DEFAULT_ADVANCED_RESOLUTION_SIZE,
        resolution_custom_width: int = 1024,
        resolution_custom_height: int = 1024,
        wildcard_mode: str = WILDCARD_MODE_LABELS[1],
        wildcard_seed: int = 0,
        wildcard_seed_after_generate: str = SEED_CONTROL_FIXED,
        **kwargs,
    ):
        width, height = _advanced_resolution_from_selection(
            resolution_bucket,
            resolution_size,
            resolution_custom_width,
            resolution_custom_height,
        )
        fields = _normalize_regional_fields(regional_fields)
        effective_fields = _apply_regional_field_inputs(fields, kwargs)
        config = _normalize_regional_config(regional_config, width, height)
        wildcard_mode_key = normalize_wildcard_mode(wildcard_mode)
        wildcard_active = wildcard_mode_key in {WILDCARD_MODE_POPULATE, WILDCARD_MODE_FIXED, WILDCARD_MODE_SEQUENTIAL}
        wildcard_text = "\n".join(str(field.get("text") or "") for field in effective_fields)
        if (
            wildcard_active
            and str(wildcard_seed_after_generate or "") == SEED_CONTROL_RANDOMIZE
            and has_wildcard_syntax(wildcard_text)
        ):
            return float("nan")
        return _stable_change_key({
            "mode": "prompt_studio_regional",
            "metadata_filter_words": resolve_metadata_filter_words(),
            "wildcard_sources": wildcard_sources_signature() if wildcard_active else {},
            "wildcard_mode": wildcard_mode_key,
            "wildcard_seed": normalize_seed(wildcard_seed),
            "wildcard_seed_after_generate": str(wildcard_seed_after_generate or SEED_CONTROL_FIXED),
            "resolution": (width, height),
            "regional_fields": _regional_fields_json(effective_fields),
            "regional_config": _regional_config_json(config),
        })

    @classmethod
    def _update_metadata_fields(
        cls,
        workflow_prompt,
        extra_pnginfo,
        unique_id,
        regional_fields: str,
        regional_config: str,
        extra_updates: dict[str, Any] | None = None,
    ) -> None:
        node_id = _single_value(unique_id)
        if node_id is None:
            return
        node_id = str(node_id)
        updates = {
            "regional_fields": regional_fields,
            "regional_config": regional_config,
        }
        if extra_updates:
            updates.update(extra_updates)

        if isinstance(workflow_prompt, dict):
            prompt_node = workflow_prompt.get(node_id)
            if isinstance(prompt_node, dict):
                inputs = prompt_node.setdefault("inputs", {})
                for name, value in updates.items():
                    inputs[name] = value

        workflow_node = _get_workflow_node(extra_pnginfo, node_id)
        if workflow_node is None:
            return

        properties = workflow_node.setdefault("properties", {})
        if not isinstance(properties, dict):
            properties = {}
            workflow_node["properties"] = properties
        properties[REGIONAL_FIELDS_WORKFLOW_PROPERTY] = regional_fields
        properties[REGIONAL_CONFIG_WORKFLOW_PROPERTY] = regional_config

        input_names = cls._widget_input_names()
        widgets_values = workflow_node.setdefault("widgets_values", [])
        for name, value in updates.items():
            if name not in input_names:
                continue
            index = input_names.index(name)
            while len(widgets_values) <= index:
                widgets_values.append(None)
            widgets_values[index] = value

    @staticmethod
    def _ui(
        regional_fields: str,
        regional_config: str,
        field_inputs: dict | None = None,
        extra_payload: dict[str, Any] | None = None,
    ):
        payload = {
            "prompt_studio_regional": [{
                "regional_fields": regional_fields,
                "regional_config": regional_config,
                "field_inputs": field_inputs or {},
            }]
        }
        if extra_payload:
            payload["prompt_studio_regional"][0].update(extra_payload)
        return payload

    def build(
        self,
        regional_fields: str,
        regional_config: str,
        resolution_bucket: str = DEFAULT_ADVANCED_RESOLUTION_BUCKET,
        resolution_size: str = DEFAULT_ADVANCED_RESOLUTION_SIZE,
        resolution_custom_width: int = 1024,
        resolution_custom_height: int = 1024,
        wildcard_mode: str = WILDCARD_MODE_LABELS[1],
        wildcard_seed: int = 0,
        wildcard_seed_after_generate: str = SEED_CONTROL_FIXED,
        workflow_prompt=None,
        extra_pnginfo=None,
        unique_id=None,
        **field_inputs,
    ):
        width, height = _advanced_resolution_from_selection(
            resolution_bucket,
            resolution_size,
            resolution_custom_width,
            resolution_custom_height,
        )
        fields = _normalize_regional_fields(regional_fields)
        saved_fields = _clone_regional_fields(fields)
        effective_fields = _apply_regional_field_inputs(fields, field_inputs)
        effective_field_inputs = _advanced_field_input_values(field_inputs)
        config = _normalize_regional_config(regional_config, width, height)

        wildcard_mode_key = normalize_wildcard_mode(wildcard_mode)
        wildcard_seed_value = normalize_seed(wildcard_seed)
        wildcard_effective_seed_control = (
            SEED_CONTROL_INCREMENT
            if wildcard_mode_key == WILDCARD_MODE_SEQUENTIAL
            else str(wildcard_seed_after_generate or SEED_CONTROL_FIXED)
        )
        ui_updates: dict[str, Any] = {}
        metadata_updates: dict[str, Any] = {}

        saved_fields, saved_wildcard = _expand_advanced_wildcard_fields(
            saved_fields,
            wildcard_seed_value,
            wildcard_mode_key,
        )
        effective_fields, effective_wildcard = _expand_advanced_wildcard_fields(
            effective_fields,
            wildcard_seed_value,
            wildcard_mode_key,
        )
        wildcard_changed = bool(saved_wildcard["changed"] or effective_wildcard["changed"])
        if wildcard_mode_key in {WILDCARD_MODE_POPULATE, WILDCARD_MODE_FIXED, WILDCARD_MODE_SEQUENTIAL}:
            next_wildcard_seed = next_seed(wildcard_seed_value, wildcard_effective_seed_control)
            ui_updates.update({
                "wildcard_mode": str(wildcard_mode or WILDCARD_MODE_LABELS[1]),
                "wildcard_seed": next_wildcard_seed,
                "wildcard_seed_after_generate": wildcard_effective_seed_control,
                "wildcard_used_keys": list(effective_wildcard["used_keys"]),
                "wildcard_missing_keys": list(effective_wildcard["missing_keys"]),
            })
            if wildcard_changed:
                metadata_updates.update({
                    "wildcard_mode": WILDCARD_MODE_LABELS[3],
                    "wildcard_seed": wildcard_seed_value,
                    "wildcard_seed_after_generate": SEED_CONTROL_FIXED,
                })

        fields_json = _regional_fields_json(saved_fields)
        config_json = _regional_config_json(config)
        self._update_metadata_fields(
            workflow_prompt,
            extra_pnginfo,
            unique_id,
            fields_json,
            config_json,
            metadata_updates,
        )

        (
            positive_prompt,
            negative_prompt,
            metadata_prompt,
            metadata_negative_prompt,
            regional_prompt_data,
        ) = _build_regional_outputs(effective_fields, config, width, height)

        return {
            "ui": self._ui(fields_json, config_json, effective_field_inputs, ui_updates),
            "result": (
                metadata_prompt,
                metadata_negative_prompt,
                width,
                height,
                regional_prompt_data,
            ),
        }


class EasyUseAnimaRegionalConditioning:
    """Convert Regional Prompt Studio JSON into KSampler-ready conditionings."""

    DESCRIPTION = (
        "Encodes Anima Prompt Studio Regional data with CLIP and attaches mask metadata "
        "to mask-scoped positive conditioning entries."
    )
    OUTPUT_TOOLTIPS = (
        "Positive conditioning containing the global prompt plus mask-scoped regional entries.",
        "Negative conditioning encoded from the bundled negative prompt.",
    )

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "clip": ("CLIP", {
                    "tooltip": "CLIP model used to encode the bundled global and regional prompts.",
                }),
                "regional_prompt_data": (REGIONAL_PROMPT_DATA_TYPE, {
                    "forceInput": True,
                    "tooltip": "Bundled structured data from Anima Prompt Studio Regional.",
                }),
                "mask_strength": ("FLOAT", {
                    "default": 1.0,
                    "min": 0.0,
                    "max": 10.0,
                    "step": 0.01,
                    "tooltip": "Strength applied to mask-scoped conditioning entries.",
                }),
                "set_cond_area": (["mask bounds", "default"], {
                    "default": "mask bounds",
                    "tooltip": "mask bounds mirrors ComfyUI ConditioningSetMask area behavior.",
                }),
            },
        }

    RETURN_TYPES = ("CONDITIONING", "CONDITIONING")
    RETURN_NAMES = ("positive", "negative")
    FUNCTION = "encode"
    CATEGORY = "EasyUse Anima/Prompt"

    @classmethod
    def IS_CHANGED(
        cls,
        regional_prompt_data: str | dict = "",
        mask_strength: float = 1.0,
        set_cond_area: str = "mask bounds",
        **kwargs,
    ):
        return _stable_change_key({
            "mode": "regional_conditioning",
            "regional_prompt_data": (
                regional_prompt_data
                if isinstance(regional_prompt_data, dict)
                else str(regional_prompt_data or "")
            ),
            "mask_strength": _as_float(mask_strength, 1.0),
            "set_cond_area": str(set_cond_area or "mask bounds"),
        })

    def encode(
        self,
        regional_prompt_data: str | dict,
        clip,
        mask_strength: float = 1.0,
        set_cond_area: str = "mask bounds",
    ):
        payload = _parse_json_object(regional_prompt_data)
        width, height = _regional_payload_canvas(payload)
        positive_prompt = str(payload.get("global_prompt") or payload.get("positive_prompt") or "")
        negative_prompt = str(payload.get("negative_prompt") or "")

        positive = list(_encode_with_comfy_clip(clip, positive_prompt))
        negative = _encode_with_comfy_clip(clip, negative_prompt)

        if _as_bool(payload.get("regional_enabled"), False):
            use_mask_bounds = str(set_cond_area or "mask bounds") != "default"
            mask_prompts = payload.get("mask_prompts") if isinstance(payload.get("mask_prompts"), list) else []
            for entry in mask_prompts:
                if not isinstance(entry, dict):
                    continue
                valid_mask_ids = _normalize_mask_ids(entry.get("valid_mask_ids") or entry.get("mask_ids"))
                prompt = str(entry.get("prompt") or entry.get("text") or "").strip()
                if not valid_mask_ids or not prompt:
                    continue
                mask = _regional_union_mask_for_ids(payload, valid_mask_ids, width, height)
                regional_conditioning = _encode_with_comfy_clip(clip, prompt)
                conditioning_values = {
                    "mask": mask,
                    "set_area_to_bounds": False,
                    "mask_strength": _as_float(mask_strength, 1.0),
                    "easyuse_anima_region": {
                        "field_id": str(entry.get("field_id") or ""),
                        "mask_ids": valid_mask_ids,
                    },
                }
                if use_mask_bounds:
                    area = _regional_mask_bounds_area(mask, width, height)
                    if area is not None:
                        conditioning_values["area"] = area
                positive.extend(_conditioning_set_values(regional_conditioning, conditioning_values))

        return (positive, negative)


class EasyUseAnimaPromptStudioExtend:
    """Extended Prompt Studio with numbered positive/negative prompt rows."""

    @classmethod
    def INPUT_TYPES(cls):
        required = {
            "fill_naia_prompt": ("BOOLEAN", {
                "default": False,
                "tooltip": (
                    "When enabled, slot 3 is filled from NAIA on each queue. "
                    "Saved-image workflows are written with this off and the current slot 3 text stored."
                ),
            }),
            "use_anima_mod_guidance": ("BOOLEAN", {
                "default": False,
                "tooltip": (
                    "true: positive output excludes slots 1-2 quality tags and sends them "
                    "through anima_mod_guidance_quality_tags."
                ),
            }),
            "pin_trigger_tags_to_front": ("BOOLEAN", {
                "default": False,
                "tooltip": "true: keep prompt correction trigger-like tags at the front where applicable.",
            }),
        }
        for name, _pane, _field_type, label, default, height in EXTEND_PROMPT_SLOT_SPECS:
            required[name] = ("STRING", {
                "multiline": True,
                "default": default,
                "tooltip": label,
                "placeholder": label,
                "height": height,
            })
        required["active_slots"] = ("STRING", {
            "default": json.dumps(["quality_tags_1", "general_tags_4", "trailing_tags_10"]),
            "tooltip": "Internal Prompt Studio Extend visible slot state.",
        })
        required["use_negative_anima_mod_guidance"] = ("BOOLEAN", {
            "default": False,
            "tooltip": (
                "true: negative output excludes negative quality slots and sends them "
                "through the negative Mod Guidance output."
            ),
        })
        return {
            "required": required,
            "hidden": {
                "workflow_prompt": "PROMPT",
                "extra_pnginfo": "EXTRA_PNGINFO",
                "unique_id": "UNIQUE_ID",
            },
        }

    RETURN_TYPES = (
        "STRING",
        "STRING",
        "STRING",
        "STRING",
        "BOOLEAN",
        "BOOLEAN",
        "STRING",
        "STRING",
    )
    RETURN_NAMES = (
        "positive_prompt",
        "negative_prompt",
        "anima_mod_guidance_quality_tags",
        "anima_mod_guidance_negative_prompt",
        "use_anima_mod_guidance",
        "use_negative_anima_mod_guidance",
        "metadata_prompt",
        "metadata_negative_prompt",
    )
    FUNCTION = "build"
    CATEGORY = "EasyUse Anima/Prompt"

    @classmethod
    def _widget_input_names(cls) -> list[str]:
        return list(cls.INPUT_TYPES()["required"].keys())

    @classmethod
    def IS_CHANGED(
        cls,
        fill_naia_prompt: bool = False,
        use_anima_mod_guidance: bool = False,
        pin_trigger_tags_to_front: bool = False,
        use_negative_anima_mod_guidance: bool = False,
        **kwargs,
    ):
        if _as_bool(fill_naia_prompt, False):
            return float("nan")
        return _stable_change_key({
            "mode": "prompt_studio_extend",
            "metadata_filter_words": resolve_metadata_filter_words(),
            "use_anima_mod_guidance": _as_bool(use_anima_mod_guidance, False),
            "use_negative_anima_mod_guidance": _as_bool(use_negative_anima_mod_guidance, False),
            "pin_trigger_tags_to_front": _as_bool(pin_trigger_tags_to_front, False),
            "active_slots": str(kwargs.get("active_slots", "")),
            **{
                name: str(kwargs.get(name, ""))
                for name, *_rest in EXTEND_PROMPT_SLOT_SPECS
            },
        })

    @classmethod
    def _update_metadata_slots(
        cls,
        workflow_prompt,
        extra_pnginfo,
        unique_id,
        updates: dict[str, Any],
    ) -> None:
        node_id = _single_value(unique_id)
        if node_id is None:
            return
        node_id = str(node_id)

        if isinstance(workflow_prompt, dict):
            prompt_node = workflow_prompt.get(node_id)
            if isinstance(prompt_node, dict):
                inputs = prompt_node.setdefault("inputs", {})
                for name, value in updates.items():
                    inputs[name] = value

        workflow_node = _get_workflow_node(extra_pnginfo, node_id)
        if workflow_node is None:
            return

        input_names = cls._widget_input_names()
        widgets_values = workflow_node.setdefault("widgets_values", [])
        for name, value in updates.items():
            if name not in input_names:
                continue
            index = input_names.index(name)
            while len(widgets_values) <= index:
                widgets_values.append(None)
            widgets_values[index] = value

    @staticmethod
    @staticmethod
    def _active_slot_set(active_slots: Any) -> set[str] | None:
        if active_slots is None:
            return None
        parsed = active_slots
        if isinstance(active_slots, str):
            if not active_slots.strip():
                return None
            try:
                parsed = json.loads(active_slots)
            except json.JSONDecodeError:
                return None
        if not isinstance(parsed, list):
            return None
        valid_names = {name for name, *_rest in EXTEND_PROMPT_SLOT_SPECS}
        return {str(name) for name in parsed if str(name) in valid_names}

    @staticmethod
    def _fields_from_slots(values: dict[str, str], active_slots: Any = None) -> list[dict]:
        active_slot_names = EasyUseAnimaPromptStudioExtend._active_slot_set(active_slots)
        fields = []
        for name, pane, field_type, label, _default, height in EXTEND_PROMPT_SLOT_SPECS:
            if active_slot_names is not None and name not in active_slot_names:
                continue
            text = str(values.get(name, "") or "")
            fields.append({
                "id": name,
                "pane": pane,
                "type": field_type,
                "label": label,
                "text": text,
                "height": height,
                "enabled": bool(text.strip()),
            })
        return fields

    @staticmethod
    def _ui(slot_values: dict[str, str], fill_naia_prompt: bool, active_slots: Any = None):
        return {
            "prompt_studio_slots": [{
                **slot_values,
                "fill_naia_prompt": _as_bool(fill_naia_prompt, False),
                "active_slots": active_slots,
            }]
        }

    def build(
        self,
        fill_naia_prompt: bool,
        use_anima_mod_guidance: bool,
        pin_trigger_tags_to_front: bool,
        use_negative_anima_mod_guidance: bool = False,
        workflow_prompt=None,
        extra_pnginfo=None,
        unique_id=None,
        **slot_values,
    ):
        active_slots = slot_values.get("active_slots")
        values = {
            name: str(slot_values.get(name, default) or "")
            for name, _pane, _field_type, _label, default, _height in EXTEND_PROMPT_SLOT_SPECS
        }
        live_fill_naia = _as_bool(fill_naia_prompt, False)
        metadata_fill_naia = live_fill_naia

        if live_fill_naia:
            naia_settings = resolve_naia_settings()
            body = EasyUseAnimaNAIARandomPrompt._make_request_body(
                _as_bool(naia_settings["use_naia_settings"], True),
                naia_settings["pre_prompt"],
                naia_settings["post_prompt"],
                naia_settings["auto_hide"],
                naia_settings["preprocessing"],
            )
            resp = _post_random(naia_settings["host"], naia_settings["port"], body)
            naia_prompt, _naia_negative, _naia_width, _naia_height = _parse_random_response(resp)
            values["naia_prompt_3"] = naia_prompt
            metadata_fill_naia = False

        if live_fill_naia:
            self._update_metadata_slots(
                workflow_prompt,
                extra_pnginfo,
                unique_id,
                {
                    "fill_naia_prompt": metadata_fill_naia,
                    "naia_prompt_3": values["naia_prompt_3"],
                },
            )

        result = _build_advanced_prompts(
            self._fields_from_slots(values, active_slots),
            use_anima_mod_guidance,
            use_negative_anima_mod_guidance,
            pin_trigger_tags_to_front,
        )
        return {
            "ui": self._ui(values, live_fill_naia, active_slots),
            "result": result,
        }


class EasyUseAnimaLoraPreset:
    """Multi-profile LoRA stack preset node for ANIMA style prompts."""

    DESCRIPTION = (
        "Stores multiple ANIMA LoRA preset profiles, builds a LoRA stack, emits trigger words, "
        "and preserves profile data in workflow metadata."
    )
    OUTPUT_TOOLTIPS = (
        "Corrected style prompt for artist tags, model triggers, or short style directions.",
        "LoRA stack compatible with LoRA stack loaders.",
        "Trigger words collected from selected LoRA metadata.",
        "Text representation of enabled LoRAs and strengths.",
        "Currently selected profile index after wrapping to the available profile count.",
    )

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "style_prompt": ("STRING", {
                    "multiline": True,
                    "default": "",
                    "tooltip": "Style prompt for artist tags, model triggers, or short style directions.",
                }),
                "profile_index": ("INT", {
                    "default": 1,
                    "min": 1,
                    "max": 16,
                    "step": 1,
                    "tooltip": "Selected LoRA preset profile. Can be connected from another node.",
                }),
                "profile_count": ("STRING", {
                    "default": "4",
                    "tooltip": "Internal profile count managed by the front-end profile buttons.",
                }),
                "lora_name": (_lora_combo_values(), {
                    "default": "None",
                    "tooltip": "Internal LoRA selector source. Hidden by the EasyUse Anima front-end.",
                }),
                "loras": ("STRING", {
                    "multiline": True,
                    "default": "[]",
                    "tooltip": "Internal serialized LoRA rows for the selected profile.",
                }),
                "profile_data": ("STRING", {
                    "multiline": True,
                    "default": "{}",
                    "tooltip": "Internal serialized profile data.",
                }),
            },
            "optional": _FlexibleOptionalInputType(_ANY_TYPE),
        }

    RETURN_TYPES = ("STRING", "LORA_STACK", "STRING", "STRING", "INT")
    RETURN_NAMES = ("style_prompt", "LORA_STACK", "trigger_words", "active_loras", "profile_index")
    FUNCTION = "build"
    CATEGORY = "EasyUse Anima/LoRA"

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        return _stable_change_key({
            "mode": "lora_preset",
            **{key: str(value) for key, value in sorted(kwargs.items())},
        })

    def build(
        self,
        style_prompt: str,
        profile_index: int,
        profile_count=4,
        lora_name: str = "None",
        loras="[]",
        profile_data: str = "{}",
        **kwargs,
    ):
        kwargs = dict(kwargs)
        if loras is not None:
            kwargs["loras"] = loras

        selected_style, selected_loras, selected_index = _select_profile_values(
            profile_index,
            profile_count,
            profile_data,
            style_prompt,
            kwargs,
        )
        corrected_style = _correct_style_prompt(selected_style)

        stack = []
        trigger_words: list[str] = []
        active_loras: list[tuple[str, float, float]] = []

        lora_stack = kwargs.get("lora_stack")
        if lora_stack:
            stack.extend(lora_stack)
            for lora_path, _model_strength, _clip_strength in lora_stack:
                lora_base = os.path.splitext(os.path.basename(str(lora_path).replace("\\", "/")))[0]
                _path, existing_trigger_words = _get_lora_info(lora_base)
                trigger_words.extend(existing_trigger_words)

        seen: set[tuple[str, float, float]] = set()
        missing_loras: list[str] = []
        for lora in selected_loras:
            enabled_value = lora.get("on", lora.get("active", True))
            if not _as_bool(enabled_value, True):
                continue
            raw_name = str(lora.get("name", lora.get("lora", ""))).strip()
            if not raw_name or raw_name == "None":
                continue
            lora_name = raw_name.replace("\\", "/")
            active_lora_name = _apply_lora_syntax_format(lora_name)
            try:
                model_strength = float(lora.get("strength", 1.0))
            except (TypeError, ValueError):
                model_strength = 1.0
            clip_raw = lora.get("strengthTwo", lora.get("clipStrength", model_strength))
            try:
                clip_strength = float(clip_raw if clip_raw is not None else model_strength)
            except (TypeError, ValueError):
                clip_strength = model_strength

            stack_lora_name = _lora_stack_name(lora_name)
            dedupe_key = (stack_lora_name, model_strength, clip_strength)
            if dedupe_key in seen:
                continue
            seen.add(dedupe_key)

            if _lora_model_exists(stack_lora_name) is False:
                missing_loras.append(_missing_lora_display_name(raw_name, stack_lora_name))
                continue

            _lora_path, lora_trigger_words = _get_lora_info(lora_name)
            stack.append((stack_lora_name, model_strength, clip_strength))
            trigger_words.extend(lora_trigger_words)
            active_loras.append((active_lora_name, model_strength, clip_strength))

        _raise_missing_loras(selected_index, missing_loras)

        active_loras_text_parts = []
        for name, model_strength, clip_strength in active_loras:
            model_text = _format_strength(model_strength)
            clip_text = _format_strength(clip_strength)
            if abs(model_strength - clip_strength) > 0.001:
                active_loras_text_parts.append(f"<lora:{name}:{model_text}:{clip_text}>")
            else:
                active_loras_text_parts.append(f"<lora:{name}:{model_text}>")

        return {
            "ui": {
                "lora_preset_profile": [{
                    "profile_index": selected_index,
                }],
            },
            "result": (
                corrected_style,
                stack,
                ", ".join(trigger_words) if trigger_words else "",
                " ".join(active_loras_text_parts),
                selected_index,
            ),
        }


class EasyUseAnimaSAM3Context:
    """Load a native ComfyUI SAM3 checkpoint and expose it as ctx_SAM3."""

    DESCRIPTION = (
        "Loads a SAM3 checkpoint with ComfyUI's native checkpoint loader and returns "
        "an rgthree-compatible context containing the SAM3 model, CLIP, and VAE."
    )
    OUTPUT_TOOLTIPS = (
        "Context dict containing SAM3 model, CLIP, VAE, and checkpoint name.",
        "SAM3 model loaded from the selected checkpoint.",
        "SAM3 CLIP loaded from the selected checkpoint.",
        "VAE loaded from the selected checkpoint.",
    )

    @classmethod
    def INPUT_TYPES(cls):
        checkpoint_names = _comfy_checkpoint_names()
        return {
            "required": {
                "ckpt_name": (checkpoint_names, {
                    "default": _preferred_checkpoint_default(checkpoint_names, "sam3.1_multiplex_fp16.safetensors"),
                    "tooltip": "SAM3 checkpoint to load, for example sam3.1_multiplex_fp16.safetensors.",
                }),
            },
        }

    RETURN_TYPES = ("RGTHREE_CONTEXT", "MODEL", "CLIP", "VAE")
    RETURN_NAMES = ("ctx_SAM3", "sam3_model", "sam3_clip", "sam3_vae")
    FUNCTION = "load"
    CATEGORY = "EasyUse Anima/Detailer"

    def load(self, ckpt_name):
        model, clip, vae = _load_checkpoint_with_comfy(str(ckpt_name))
        return (_sam3_context(model, clip, vae, str(ckpt_name)), model, clip, vae)


class EasyUseAnimaImageScaleByMultiple:
    """Scale an image by the nearest ratio that produces valid size multiples."""

    DESCRIPTION = (
        "Scales an IMAGE by the nearest valid ratio that keeps the source aspect ratio and makes "
        "the output width and height multiples of the selected size. The optional max long edge "
        "limits the selected valid output size. Use multiple 32 for highres or optimization nodes "
        "that require 32-multiple sizes."
    )
    OUTPUT_TOOLTIPS = (
        "Scaled image using the nearest valid ratio.",
        "Final valid image width.",
        "Final valid image height.",
        "Actual scale ratio applied to the image.",
    )

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE", {
                    "tooltip": "Input image to upscale.",
                }),
                "scale_by": ("FLOAT", {
                    "default": 1.5,
                    "min": 0.01,
                    "max": 8.0,
                    "step": 0.01,
                    "tooltip": "Requested image scale ratio. The node uses the nearest valid ratio for the selected multiple.",
                }),
                "upscale_method": (IMAGE_UPSCALE_METHODS, {
                    "default": "bicubic",
                    "tooltip": "Interpolation method used for resizing.",
                }),
                "multiple": (IMAGE_SCALE_MULTIPLES, {
                    "default": "32",
                    "tooltip": "Output width and height must be multiples of this value.",
                }),
                "max_long_edge": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 16384,
                    "step": 32,
                    "tooltip": "Maximum output long edge. Set 0 to disable this limit.",
                }),
            },
        }

    RETURN_TYPES = ("IMAGE", "INT", "INT", "FLOAT")
    RETURN_NAMES = ("image", "width", "height", "applied_scale")
    FUNCTION = "upscale"
    CATEGORY = "EasyUse Anima/Image"

    def upscale(self, image, scale_by=1.5, upscale_method="bicubic", multiple="32", max_long_edge=0):
        upscale_method, multiple, max_long_edge = _normalize_image_scale_options(
            upscale_method,
            multiple,
            max_long_edge,
        )
        samples = image.movedim(-1, 1)
        width, height, applied_scale = _image_scale_by_multiple_size(
            int(samples.shape[3]),
            int(samples.shape[2]),
            scale_by,
            multiple,
            max_long_edge,
        )
        scaled = _common_upscale_image(samples, width, height, str(upscale_method))
        return (scaled.movedim(1, -1), width, height, applied_scale)


class EasyUseAnimaDetailerAlignHook:
    """Impact Pack DETAILER_HOOK that aligns detail crop sampling sizes upward."""

    DESCRIPTION = (
        "Creates an Impact Pack compatible DETAILER_HOOK that aligns the detailer crop sampling "
        "size upward to a selected multiple. Use alignment 32 for ANIMA/Spectrum workflows that "
        "require 32-multiple latent-safe crop sizes."
    )
    OUTPUT_TOOLTIPS = (
        "Impact Pack compatible DETAILER_HOOK. Connect it to an Impact DetailerForEach-compatible detailer_hook input.",
    )

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "alignment": (["none", "8", "16", "32", "64"], {
                    "default": "32",
                    "tooltip": (
                        "Crop sampling size alignment. 32 is recommended for ANIMA/Spectrum safety; "
                        "none keeps the original Impact Pack size."
                    ),
                }),
            },
            "optional": {
                "detailer_hook": ("DETAILER_HOOK", {
                    "tooltip": "Optional existing Impact Pack detailer hook. It runs before the alignment adjustment.",
                }),
            },
        }

    RETURN_TYPES = ("DETAILER_HOOK",)
    RETURN_NAMES = ("detailer_hook",)
    FUNCTION = "build"
    CATEGORY = "EasyUse Anima/Detailer"

    def build(self, alignment="32", detailer_hook=None):
        alignment_int = _alignment_value(alignment)
        return (_EasyUseAnimaAlignedDetailerHook(detailer_hook, alignment_int),)


class _EasyUseAnimaImpactDetailerDelegate:
    """Internal Impact Pack DetailerForEach delegate used by SAM3 nodes."""

    DESCRIPTION = (
        "Internal Impact Pack DetailerForEach delegate used by EasyUse Anima SAM3 nodes."
    )
    OUTPUT_TOOLTIPS = (
        "Enhanced image returned by Impact Pack DetailerForEach.",
    )

    @classmethod
    def INPUT_TYPES(cls):
        max_resolution = _comfy_max_resolution()
        return {
            "required": {
                "image": ("IMAGE",),
                "segs": ("SEGS",),
                "model": ("MODEL", {
                    "tooltip": "Model passed through to Impact Pack DetailerForEach.",
                }),
                "clip": ("CLIP",),
                "vae": ("VAE",),
                "guide_size": ("FLOAT", {
                    "default": 512,
                    "min": 64,
                    "max": max_resolution,
                    "step": 8,
                    "tooltip": "Target guide size for the detailed crop.",
                }),
                "guide_size_for": ("BOOLEAN", {
                    "default": True,
                    "label_on": "bbox",
                    "label_off": "crop_region",
                    "tooltip": "Use the bbox or crop region as the guide-size basis.",
                }),
                "max_size": ("FLOAT", {
                    "default": 1024,
                    "min": 64,
                    "max": max_resolution,
                    "step": 8,
                    "tooltip": "Maximum crop size before sampling.",
                }),
                "seed": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 0xffffffffffffffff,
                }),
                "steps": ("INT", {
                    "default": 20,
                    "min": 1,
                    "max": 10000,
                }),
                "cfg": ("FLOAT", {
                    "default": 8.0,
                    "min": 0.0,
                    "max": 100.0,
                }),
                "sampler_name": (_comfy_sampler_names(),),
                "scheduler": (_impact_scheduler_names(),),
                "positive": ("CONDITIONING",),
                "negative": ("CONDITIONING",),
                "denoise": ("FLOAT", {
                    "default": 0.5,
                    "min": 0.0001,
                    "max": 1.0,
                    "step": 0.01,
                }),
                "feather": ("INT", {
                    "default": 5,
                    "min": 0,
                    "max": 100,
                    "step": 1,
                }),
                "noise_mask": ("BOOLEAN", {
                    "default": True,
                    "label_on": "enabled",
                    "label_off": "disabled",
                }),
                "force_inpaint": ("BOOLEAN", {
                    "default": True,
                    "label_on": "enabled",
                    "label_off": "disabled",
                }),
                "wildcard": ("STRING", {
                    "multiline": True,
                    "default": "",
                    "dynamicPrompts": False,
                }),
                "cycle": ("INT", {
                    "default": 1,
                    "min": 1,
                    "max": 10,
                    "step": 1,
                }),
                "alignment": (["impact", "none", "8", "16", "32", "64"], {
                    "default": "impact",
                    "tooltip": (
                        "Align the Impact detail crop sampling size upward. "
                        "Use 32 for ANIMA/Spectrum safety, or impact/none for pass-through."
                    ),
                }),
                "preserve_conditioning_metadata": ("BOOLEAN", {
                    "default": True,
                    "tooltip": (
                        "Reserved safety flag for the native ANIMA backend. "
                        "The current Impact backend passes conditioning through to Impact Pack."
                    ),
                }),
                "fail_on_unsupported_opt": ("BOOLEAN", {
                    "default": False,
                    "tooltip": "Raise an error instead of warning when a native-backend-only option is requested.",
                }),
            },
            "optional": {
                "detailer_hook": ("DETAILER_HOOK",),
                "inpaint_model": ("BOOLEAN", {
                    "default": False,
                    "label_on": "enabled",
                    "label_off": "disabled",
                }),
                "noise_mask_feather": ("INT", {
                    "default": 20,
                    "min": 0,
                    "max": 100,
                    "step": 1,
                }),
                "scheduler_func_opt": ("SCHEDULER_FUNC",),
                "tiled_encode": ("BOOLEAN", {
                    "default": False,
                    "label_on": "enabled",
                    "label_off": "disabled",
                }),
                "tiled_decode": ("BOOLEAN", {
                    "default": False,
                    "label_on": "enabled",
                    "label_off": "disabled",
                }),
            },
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("image",)
    FUNCTION = "doit"
    CATEGORY = "EasyUse Anima/Detailer"

    def doit(
        self,
        image,
        segs,
        model,
        clip,
        vae,
        guide_size,
        guide_size_for,
        max_size,
        seed,
        steps,
        cfg,
        sampler_name,
        scheduler,
        positive,
        negative,
        denoise,
        feather,
        noise_mask,
        force_inpaint,
        wildcard,
        cycle=1,
        alignment="impact",
        preserve_conditioning_metadata=True,
        fail_on_unsupported_opt=False,
        detailer_hook=None,
        inpaint_model=False,
        noise_mask_feather=0,
        scheduler_func_opt=None,
        tiled_encode=False,
        tiled_decode=False,
    ):
        alignment_text = str(alignment or "impact")
        alignment_int = _alignment_value(alignment_text)

        if not _as_bool(preserve_conditioning_metadata, True):
            logger.warning(
                "[EasyUseAnima] preserve_conditioning_metadata=false is reserved for a native backend; "
                "the Impact backend leaves conditioning handling to Impact Pack."
            )

        effective_detailer_hook = detailer_hook
        if alignment_int is not None:
            effective_detailer_hook = _EasyUseAnimaAlignedDetailerHook(detailer_hook, alignment_int)

        detailer_cls = _find_impact_detailer_class()
        detailer = detailer_cls()
        result = _call_impact_detailer(
            detailer,
            image=image,
            segs=segs,
            model=model,
            clip=clip,
            vae=vae,
            guide_size=guide_size,
            guide_size_for=guide_size_for,
            max_size=max_size,
            seed=seed,
            steps=steps,
            cfg=cfg,
            sampler_name=sampler_name,
            scheduler=scheduler,
            positive=positive,
            negative=negative,
            denoise=denoise,
            feather=feather,
            noise_mask=noise_mask,
            force_inpaint=force_inpaint,
            wildcard=wildcard,
            cycle=cycle,
            detailer_hook=effective_detailer_hook,
            inpaint_model=inpaint_model,
            noise_mask_feather=noise_mask_feather,
            scheduler_func_opt=scheduler_func_opt,
            tiled_encode=tiled_encode,
            tiled_decode=tiled_decode,
        )
        if isinstance(result, dict):
            value = result.get("result")
            if isinstance(value, tuple) and value:
                return (value[0],)
        if isinstance(result, tuple):
            if not result:
                raise RuntimeError("[EasyUseAnima] Impact DetailerForEach returned an empty tuple.")
            return (result[0],)
        return (result,)


class EasyUseAnimaSAM3Detailer:
    """Native SAM3 detection + Impact MaskToSEGS + ANIMA detailer."""

    DESCRIPTION = (
        "Runs native ComfyUI SAM3 text detection, converts the resulting mask to Impact Pack SEGS, "
        "then delegates detailing to Impact Pack DetailerForEach."
    )
    OUTPUT_TOOLTIPS = (
        "Detailed image. If disabled or no SEGS are detected, this is the original image.",
        "Impact-compatible SEGS generated from the SAM3 mask.",
        "SAM3 mask used to build SEGS.",
        "Original input image before detailing.",
    )

    @classmethod
    def INPUT_TYPES(cls):
        max_resolution = _comfy_max_resolution()
        detailer_inputs = _EasyUseAnimaImpactDetailerDelegate.INPUT_TYPES()
        required = {
            "enabled": ("BOOLEAN", {
                "default": True,
                "label_on": "enabled",
                "label_off": "bypass",
                "tooltip": "Disable to return the original image and an empty SEGS output.",
            }),
            "image": ("IMAGE",),
            "ctx_SAM3": ("RGTHREE_CONTEXT", {
                "tooltip": "ctx_SAM3 from Anima SAM3 Context or a compatible rgthree context containing model and clip.",
            }),
            "detect_prompt": ("STRING", {
                "default": "face",
                "multiline": False,
                "dynamicPrompts": False,
                "tooltip": "SAM3 text target. Use comma-separated targets or target:count for per-target detection count.",
            }),
            "detect_count": ("INT", {
                "default": 1,
                "min": 1,
                "max": 64,
                "step": 1,
                "tooltip": "Maximum detections per target when detect_prompt does not already include :count.",
            }),
            "threshold": ("FLOAT", {
                "default": 0.5,
                "min": 0.0,
                "max": 1.0,
                "step": 0.01,
                "tooltip": "SAM3 detection threshold.",
            }),
            "refine_iterations": ("INT", {
                "default": 2,
                "min": 0,
                "max": 5,
                "step": 1,
                "tooltip": "SAM decoder refinement passes. 0 uses raw detector masks.",
            }),
            "individual_masks": ("BOOLEAN", {
                "default": False,
                "label_on": "enabled",
                "label_off": "combined",
                "tooltip": "Ask SAM3 for per-object masks. MaskToSEGS can still split a combined mask by contours.",
            }),
            "combined": ("BOOLEAN", {
                "default": False,
                "label_on": "combined",
                "label_off": "separate",
                "tooltip": "Impact MaskToSEGS combined option.",
            }),
            "crop_factor": ("FLOAT", {
                "default": 3.0,
                "min": 1.0,
                "max": 100.0,
                "step": 0.1,
                "tooltip": "Impact MaskToSEGS crop factor.",
            }),
            "bbox_fill": ("BOOLEAN", {
                "default": False,
                "label_on": "enabled",
                "label_off": "disabled",
                "tooltip": "Impact MaskToSEGS bbox_fill option.",
            }),
            "drop_size": ("INT", {
                "default": 10,
                "min": 1,
                "max": max_resolution,
                "step": 1,
                "tooltip": "Drop detected regions smaller than this size.",
            }),
            "contour_fill": ("BOOLEAN", {
                "default": False,
                "label_on": "enabled",
                "label_off": "disabled",
                "tooltip": "Impact MaskToSEGS contour_fill option.",
            }),
        }

        for key, value in detailer_inputs["required"].items():
            if key in ("image", "segs"):
                continue
            required[key] = value

        return {
            "required": required,
            "optional": detailer_inputs.get("optional", {}),
        }

    RETURN_TYPES = ("IMAGE", "SEGS", "MASK", "IMAGE")
    RETURN_NAMES = ("image", "segs", "mask", "raw_image")
    FUNCTION = "doit"
    CATEGORY = "EasyUse Anima/Detailer"

    def doit(
        self,
        enabled,
        image,
        ctx_SAM3,
        detect_prompt,
        detect_count,
        threshold,
        refine_iterations,
        individual_masks,
        combined,
        crop_factor,
        bbox_fill,
        drop_size,
        contour_fill,
        model,
        clip,
        vae,
        guide_size,
        guide_size_for,
        max_size,
        seed,
        steps,
        cfg,
        sampler_name,
        scheduler,
        positive,
        negative,
        denoise,
        feather,
        noise_mask,
        force_inpaint,
        wildcard,
        cycle=1,
        alignment="impact",
        preserve_conditioning_metadata=True,
        fail_on_unsupported_opt=False,
        detailer_hook=None,
        inpaint_model=False,
        noise_mask_feather=0,
        scheduler_func_opt=None,
        tiled_encode=False,
        tiled_decode=False,
    ):
        empty_mask = _empty_mask_for_image(image)
        empty_segs = _empty_segs_for_image(image)
        if not _as_bool(enabled, True):
            return (image, empty_segs, empty_mask, image)

        sam3_model = _context_value(ctx_SAM3, "model")
        sam3_clip = _context_value(ctx_SAM3, "clip")
        if sam3_model is None or sam3_clip is None:
            raise RuntimeError(
                "[EasyUseAnima] ctx_SAM3 must contain SAM3 model and CLIP. "
                "Use the Anima SAM3 Context node or a compatible rgthree context."
            )

        sam3_text = _format_sam3_detection_prompt(detect_prompt, detect_count)
        conditioning = _encode_with_comfy_clip(sam3_clip, sam3_text)

        sam3_cls = _find_sam3_detect_class()
        sam3_result = sam3_cls.execute(
            model=sam3_model,
            image=image,
            conditioning=conditioning,
            threshold=float(threshold),
            refine_iterations=int(refine_iterations),
            individual_masks=_as_bool(individual_masks, False),
        )
        sam3_values = _node_output_tuple(sam3_result)
        if len(sam3_values) < 1:
            raise RuntimeError("[EasyUseAnima] SAM3_Detect returned no mask.")
        mask = sam3_values[0]

        mask_to_segs_cls = _find_impact_mask_to_segs_class()
        mask_to_segs_result = mask_to_segs_cls.doit(
            mask,
            _as_bool(combined, False),
            float(crop_factor),
            _as_bool(bbox_fill, False),
            int(drop_size),
            _as_bool(contour_fill, False),
        )
        segs_values = _node_output_tuple(mask_to_segs_result)
        if len(segs_values) < 1:
            raise RuntimeError("[EasyUseAnima] MaskToSEGS returned no SEGS.")
        segs = segs_values[0]

        if not _segs_has_items(segs):
            logger.info("[EasyUseAnima] SAM3 Detailer detected no SEGS for prompt %r.", sam3_text)
            return (image, segs, mask, image)

        detailed_image = _EasyUseAnimaImpactDetailerDelegate().doit(
            image=image,
            segs=segs,
            model=model,
            clip=clip,
            vae=vae,
            guide_size=guide_size,
            guide_size_for=guide_size_for,
            max_size=max_size,
            seed=seed,
            steps=steps,
            cfg=cfg,
            sampler_name=sampler_name,
            scheduler=scheduler,
            positive=positive,
            negative=negative,
            denoise=denoise,
            feather=feather,
            noise_mask=noise_mask,
            force_inpaint=force_inpaint,
            wildcard=wildcard,
            cycle=cycle,
            alignment=alignment,
            preserve_conditioning_metadata=preserve_conditioning_metadata,
            fail_on_unsupported_opt=fail_on_unsupported_opt,
            detailer_hook=detailer_hook,
            inpaint_model=inpaint_model,
            noise_mask_feather=noise_mask_feather,
            scheduler_func_opt=scheduler_func_opt,
            tiled_encode=tiled_encode,
            tiled_decode=tiled_decode,
        )[0]

        return (detailed_image, segs, mask, image)


class EasyUseAnimaNAIARandomPrompt:
    """NAIA random prompt node with bypass and frozen-output cache."""

    DESCRIPTION = (
        "Requests a random prompt from NAIA Remote API, supports bypass and frozen output reuse, "
        "and stores generated values so saved-image workflows can reproduce the same result."
    )
    OUTPUT_TOOLTIPS = (
        "Prompt text from NAIA or the original input when bypassed or not overridden.",
        "Negative prompt text from NAIA or the original input when bypassed or not overridden.",
        "Width from NAIA or the original input when bypassed or not overridden.",
        "Height from NAIA or the original input when bypassed or not overridden.",
    )

    @classmethod
    def INPUT_TYPES(cls):
        required = {
            "use_naia_bridge": ("BOOLEAN", {
                "default": True,
                "tooltip": (
                    "false: bypass NAIA and return prompt/negative_prompt/width/height as-is. "
                    "This mode keeps ComfyUI cache stable when inputs are unchanged."
                ),
            }),
            "freeze_naia_output": ("BOOLEAN", {
                "default": False,
                "tooltip": (
                    "true: if cached output is valid, return it without calling NAIA. "
                    "Saved-image workflows are written with this enabled."
                ),
            }),
            "show_preview": ("BOOLEAN", {
                "default": True,
                "tooltip": "Show the large read-only preview widget in the node UI.",
            }),
            "cached_prompt": ("STRING", {
                "multiline": True,
                "default": "",
                "tooltip": "Stored prompt used for frozen output and saved-image reproduction.",
            }),
            "cached_negative_prompt": ("STRING", {
                "multiline": True,
                "default": "",
                "tooltip": "Stored negative prompt used for frozen output and saved-image reproduction.",
            }),
            "cached_width": ("INT", {
                "default": 0, "min": 0, "max": 8192, "step": 8,
                "tooltip": "Stored width used for frozen output and saved-image reproduction.",
            }),
            "cached_height": ("INT", {
                "default": 0, "min": 0, "max": 8192, "step": 8,
                "tooltip": "Stored height used for frozen output and saved-image reproduction.",
            }),
            "cached_signature": ("STRING", {
                "multiline": True,
                "default": "",
                "tooltip": "Internal signature for validating cached output.",
            }),
            "prompt": ("STRING", {
                "multiline": False,
                "default": "",
                "placeholder": "prompt",
                "tooltip": "Returned as-is when bypassed or when override_prompt is false.",
            }),
            "override_prompt": ("BOOLEAN", {
                "default": True,
                "tooltip": "true: use NAIA prompt. false: preserve input prompt.",
            }),
            "negative_prompt": ("STRING", {
                "multiline": False,
                "default": "",
                "placeholder": "negative_prompt",
                "tooltip": "Returned as-is when bypassed or when override_negative is false.",
            }),
            "override_negative": ("BOOLEAN", {
                "default": True,
                "tooltip": "true: use NAIA negative prompt. false: preserve input negative_prompt.",
            }),
            "width": ("INT", {
                "default": 1024, "min": 64, "max": 8192, "step": 8,
                "tooltip": "Returned as-is when bypassed or when override_width is false.",
            }),
            "override_width": ("BOOLEAN", {
                "default": True,
                "tooltip": "true: use NAIA width. false: preserve input width.",
            }),
            "height": ("INT", {
                "default": 1024, "min": 64, "max": 8192, "step": 8,
                "tooltip": "Returned as-is when bypassed or when override_height is false.",
            }),
            "override_height": ("BOOLEAN", {
                "default": True,
                "tooltip": "true: use NAIA height. false: preserve input height.",
            }),
            "use_naia_settings": ("BOOLEAN", {
                "default": True,
                "tooltip": (
                    "true: use NAIA desktop Prompt Engineering settings. "
                    "false: send this node's pre/post/auto_hide and preprocessing options."
                ),
            }),
            "pre_prompt": ("STRING", {
                "multiline": True,
                "default": "",
                "placeholder": "pre_prompt",
                "tooltip": "Used only when use_naia_settings is false.",
            }),
            "post_prompt": ("STRING", {
                "multiline": True,
                "default": "",
                "placeholder": "post_prompt",
                "tooltip": "Used only when use_naia_settings is false.",
            }),
            "auto_hide": ("STRING", {
                "multiline": True,
                "default": "",
                "placeholder": "auto_hide",
                "tooltip": "Used only when use_naia_settings is false.",
            }),
        }

        pp_tooltip = (
            "Used only when use_naia_settings is false.\n"
            "skip: do not send this key\n"
            "on: remove this category\n"
            "off: explicitly keep this category"
        )
        for key in PREPROCESSING_KEYS:
            required[key] = (PP_STATE_CHOICES, {
                "default": "skip",
                "tooltip": pp_tooltip,
                "advanced": key.startswith("remove_"),
                "socketless": key.startswith("remove_"),
            })

        required["host"] = ("STRING", {
            "default": DEFAULT_HOST,
            "tooltip": "NAIA Remote API host.",
        })
        required["port"] = ("INT", {
            "default": DEFAULT_PORT, "min": 1, "max": 65535,
            "tooltip": "NAIA Remote API port.",
        })
        return {
            "required": required,
            "hidden": {
                "workflow_prompt": "PROMPT",
                "extra_pnginfo": "EXTRA_PNGINFO",
                "unique_id": "UNIQUE_ID",
            },
        }

    RETURN_TYPES = ("STRING", "STRING", "INT", "INT")
    RETURN_NAMES = ("prompt", "negative_prompt", "width", "height")
    FUNCTION = "request"
    CATEGORY = "NAIA Bridge/API"

    def __init__(self):
        self._cache_signature: Optional[str] = None
        self._cache_value: Optional[tuple[str, str, int, int]] = None

    @classmethod
    def IS_CHANGED(
        cls,
        use_naia_bridge: bool = True,
        freeze_naia_output: bool = False,
        show_preview: bool = True,
        cached_prompt: str = "",
        cached_negative_prompt: str = "",
        cached_width: int = 0,
        cached_height: int = 0,
        cached_signature: str = "",
        prompt: str = "",
        override_prompt: bool = True,
        negative_prompt: str = "",
        override_negative: bool = True,
        width: int = 1024,
        override_width: bool = True,
        height: int = 1024,
        override_height: bool = True,
        use_naia_settings: bool = True,
        pre_prompt: str = "",
        post_prompt: str = "",
        auto_hide: str = "",
        host: str = DEFAULT_HOST,
        port: int = DEFAULT_PORT,
        **kwargs,
    ):
        naia_settings = resolve_naia_settings()
        use_naia_settings = naia_settings["use_naia_settings"]
        pre_prompt = naia_settings["pre_prompt"]
        post_prompt = naia_settings["post_prompt"]
        auto_hide = naia_settings["auto_hide"]
        host = naia_settings["host"]
        port = naia_settings["port"]
        pp_kwargs = naia_settings["preprocessing"]

        if not _as_bool(use_naia_bridge, True):
            return _stable_change_key({
                "mode": "disabled",
                "prompt": str(prompt),
                "negative_prompt": str(negative_prompt),
                "width": _as_int(width, 1024),
                "height": _as_int(height, 1024),
            })

        signature = cls._make_signature(
            prompt,
            override_prompt,
            negative_prompt,
            override_negative,
            width,
            override_width,
            height,
            override_height,
            use_naia_settings,
            pre_prompt,
            post_prompt,
            auto_hide,
            host,
            port,
            pp_kwargs,
        )

        if _as_bool(freeze_naia_output, False):
            cached = cls._cached_tuple(
                cached_prompt,
                cached_negative_prompt,
                cached_width,
                cached_height,
            )
            if cached is not None and str(cached_signature) == signature:
                return _stable_change_key({
                    "mode": "frozen",
                    "signature": signature,
                    "prompt": cached[0],
                    "negative_prompt": cached[1],
                    "width": cached[2],
                    "height": cached[3],
                })
            return float("nan")

        return float("nan")

    @staticmethod
    def _cached_tuple(
        cached_prompt: str,
        cached_negative_prompt: str,
        cached_width: int,
        cached_height: int,
    ) -> Optional[tuple[str, str, int, int]]:
        width = _as_int(cached_width, 0)
        height = _as_int(cached_height, 0)
        if width <= 0 or height <= 0:
            return None
        if not cached_prompt and not cached_negative_prompt:
            return None
        return (str(cached_prompt), str(cached_negative_prompt), width, height)

    @classmethod
    def _widget_input_names(cls) -> list[str]:
        return list(cls.INPUT_TYPES()["required"].keys())

    @staticmethod
    def _make_signature(
        prompt: str,
        override_prompt: bool,
        negative_prompt: str,
        override_negative: bool,
        width: int,
        override_width: bool,
        height: int,
        override_height: bool,
        use_naia_settings: bool,
        pre_prompt: str,
        post_prompt: str,
        auto_hide: str,
        host: str,
        port: int,
        pp_kwargs: dict,
    ) -> str:
        use_settings = _as_bool(use_naia_settings, True)
        preprocessing = {}
        if not use_settings:
            preprocessing = {
                key: str(pp_kwargs.get(key, "skip"))
                for key in PREPROCESSING_KEYS
            }
        payload = {
            "prompt": str(prompt),
            "override_prompt": _as_bool(override_prompt, True),
            "negative_prompt": str(negative_prompt),
            "override_negative": _as_bool(override_negative, True),
            "width": _as_int(width, 1024),
            "override_width": _as_bool(override_width, True),
            "height": _as_int(height, 1024),
            "override_height": _as_bool(override_height, True),
            "use_naia_settings": use_settings,
            "pre_prompt": "" if use_settings else str(pre_prompt),
            "post_prompt": "" if use_settings else str(post_prompt),
            "auto_hide": "" if use_settings else str(auto_hide),
            "preprocessing": preprocessing,
            "host": str(host),
            "port": _as_int(port, DEFAULT_PORT),
        }
        return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))

    @staticmethod
    def _make_request_body(
        use_naia_settings: bool,
        pre_prompt: str,
        post_prompt: str,
        auto_hide: str,
        pp_kwargs: dict,
    ) -> dict:
        body = {
            "timeout": NAIA_REQUEST_TIMEOUT,
            "respect_naia_autogen": True,
            "force_naia_skip_generate": False,
        }
        if not use_naia_settings:
            preprocessing_options = {}
            for key in PREPROCESSING_KEYS:
                state = pp_kwargs.get(key, "skip")
                if state == "on":
                    preprocessing_options[key] = True
                elif state == "off":
                    preprocessing_options[key] = False
            body["peng_override"] = {
                "pre_prompt": pre_prompt,
                "post_prompt": post_prompt,
                "auto_hide": auto_hide,
                "preprocessing_options": preprocessing_options,
            }
        return body

    @staticmethod
    def _apply_overrides(
        naia_value: tuple[str, str, int, int],
        prompt: str,
        override_prompt: bool,
        negative_prompt: str,
        override_negative: bool,
        width: int,
        override_width: bool,
        height: int,
        override_height: bool,
    ) -> tuple[str, str, int, int]:
        naia_prompt, naia_negative, naia_width, naia_height = naia_value
        return (
            naia_prompt if override_prompt else str(prompt),
            naia_negative if override_negative else str(negative_prompt),
            naia_width if override_width else _as_int(width, 1024),
            naia_height if override_height else _as_int(height, 1024),
        )

    @classmethod
    def _update_metadata_cache(
        cls,
        workflow_prompt,
        extra_pnginfo,
        unique_id,
        output_value: tuple[str, str, int, int],
        signature: str,
    ) -> None:
        node_id = _single_value(unique_id)
        if node_id is None:
            return
        node_id = str(node_id)
        out_prompt, out_negative, out_width, out_height = output_value
        updates = {
            "use_naia_bridge": True,
            "freeze_naia_output": True,
            "cached_prompt": out_prompt,
            "cached_negative_prompt": out_negative,
            "cached_width": int(out_width),
            "cached_height": int(out_height),
            "cached_signature": signature,
        }

        if isinstance(workflow_prompt, dict):
            prompt_node = workflow_prompt.get(node_id)
            if isinstance(prompt_node, dict):
                inputs = prompt_node.setdefault("inputs", {})
                for name, value in updates.items():
                    inputs[name] = value

        workflow_node = _get_workflow_node(extra_pnginfo, node_id)
        if workflow_node is None:
            return

        input_names = cls._widget_input_names()
        widgets_values = workflow_node.setdefault("widgets_values", [])
        for name, value in updates.items():
            if name not in input_names:
                continue
            index = input_names.index(name)
            while len(widgets_values) <= index:
                widgets_values.append(None)
            widgets_values[index] = value

    @staticmethod
    def _ui(prompt: str, negative: str, width: int, height: int, status: str, signature: str):
        return {
            "prompt": [prompt],
            "negative_prompt": [negative],
            "width": [width],
            "height": [height],
            "status": [status],
            "cached_signature": [signature],
        }

    def request(
        self,
        use_naia_bridge: bool,
        freeze_naia_output: bool,
        show_preview: bool,
        cached_prompt: str,
        cached_negative_prompt: str,
        cached_width: int,
        cached_height: int,
        cached_signature: str,
        prompt: str,
        override_prompt: bool,
        negative_prompt: str,
        override_negative: bool,
        width: int,
        override_width: bool,
        height: int,
        override_height: bool,
        use_naia_settings: bool,
        pre_prompt: str,
        post_prompt: str,
        auto_hide: str,
        host: str,
        port: int,
        workflow_prompt=None,
        extra_pnginfo=None,
        unique_id=None,
        **pp_kwargs,
    ):
        naia_settings = resolve_naia_settings()
        use_naia_settings = naia_settings["use_naia_settings"]
        pre_prompt = naia_settings["pre_prompt"]
        post_prompt = naia_settings["post_prompt"]
        auto_hide = naia_settings["auto_hide"]
        host = naia_settings["host"]
        port = naia_settings["port"]
        pp_kwargs = naia_settings["preprocessing"]

        bridge_enabled = _as_bool(use_naia_bridge, True)
        freeze_output = _as_bool(freeze_naia_output, False)
        use_settings = _as_bool(use_naia_settings, True)
        override_prompt = _as_bool(override_prompt, True)
        override_negative = _as_bool(override_negative, True)
        override_width = _as_bool(override_width, True)
        override_height = _as_bool(override_height, True)

        signature = self._make_signature(
            prompt,
            override_prompt,
            negative_prompt,
            override_negative,
            width,
            override_width,
            height,
            override_height,
            use_settings,
            pre_prompt,
            post_prompt,
            auto_hide,
            host,
            port,
            pp_kwargs,
        )

        if not bridge_enabled:
            out_prompt = str(prompt)
            out_negative = str(negative_prompt)
            out_width = _as_int(width, 1024)
            out_height = _as_int(height, 1024)
            return {
                "ui": self._ui(out_prompt, out_negative, out_width, out_height, "disabled", signature),
                "result": (out_prompt, out_negative, out_width, out_height),
            }

        saved_cache = self._cached_tuple(
            cached_prompt,
            cached_negative_prompt,
            cached_width,
            cached_height,
        )
        if freeze_output and saved_cache is not None and str(cached_signature) == signature:
            out_prompt, out_negative, out_width, out_height = saved_cache
            return {
                "ui": self._ui(out_prompt, out_negative, out_width, out_height, "frozen", signature),
                "result": (out_prompt, out_negative, out_width, out_height),
            }

        if self._cache_signature != signature:
            self._cache_signature = signature
            self._cache_value = (
                saved_cache if saved_cache is not None and str(cached_signature) == signature else None
            )

        if self._cache_value is None or not freeze_output:
            body = self._make_request_body(use_settings, pre_prompt, post_prompt, auto_hide, pp_kwargs)
            resp = _post_random(host, port, body)
            naia_value = _parse_random_response(resp)
            self._cache_value = self._apply_overrides(
                naia_value,
                prompt,
                override_prompt,
                negative_prompt,
                override_negative,
                width,
                override_width,
                height,
                override_height,
            )
            logger.debug(
                "request_id=%s prompt_len=%d size=%dx%d use_naia_settings=%s",
                resp.get("request_id"),
                len(self._cache_value[0]),
                self._cache_value[2],
                self._cache_value[3],
                use_settings,
            )

        if self._cache_value is None:
            raise RuntimeError("[EasyUse Anima] Internal cache creation failed.")

        out_prompt, out_negative, out_width, out_height = self._cache_value
        self._update_metadata_cache(
            workflow_prompt,
            extra_pnginfo,
            unique_id,
            (out_prompt, out_negative, out_width, out_height),
            signature,
        )
        return {
            "ui": self._ui(out_prompt, out_negative, out_width, out_height, "fresh", signature),
            "result": (out_prompt, out_negative, out_width, out_height),
        }
