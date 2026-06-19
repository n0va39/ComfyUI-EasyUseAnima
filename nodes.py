# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import logging
import os
import re
from typing import Any, Optional

try:
    from .anima_prompt import correct_prompt, load_knowledge_base
    from .anima_prompt.parser import parse_prompt
    from .settings import resolve_metadata_filter_words, resolve_naia_settings
except ImportError:  # allows simple local import tests outside ComfyUI's package loader
    from anima_prompt import correct_prompt, load_knowledge_base
    from anima_prompt.parser import parse_prompt
    from settings import resolve_metadata_filter_words, resolve_naia_settings

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
ADVANCED_FIELD_TYPES = {"quality", "artist", "general", "naia"}
ADVANCED_FIELD_PANES = {"positive", "negative"}
ADVANCED_FIELD_LABELS = {
    "quality": "Quality Tags",
    "artist": "Artist Tags",
    "general": "General Tags",
    "naia": "NAIA Prompt",
}
FIXED_PROMPT_SLOT_SPECS = [
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
    ("negative_prompt_1", "negative", "general", "Negative Prompt 1", "", 120),
    ("negative_prompt_2", "negative", "general", "Negative Prompt 2", "", 120),
    ("negative_prompt_3", "negative", "general", "Negative Prompt 3", "", 120),
    ("negative_prompt_4", "negative", "general", "Negative Prompt 4", "", 120),
]
FIXED_TIMEOUT = 30.0
HTTP_TIMEOUT = FIXED_TIMEOUT + 5.0

NAI_1MP = 1024 * 1024
LATENT_ALIGN = 8

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


def _clean_prompt(value: str) -> str:
    if not value:
        return value
    value = _HASH_COMMENT_RE.sub("", value)
    value = _MULTI_COMMA_RE.sub(",", value)
    return value.strip(" ,\n\t")


def _stable_change_key(payload: dict) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


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
    normalized = str(value).replace("\r\n", "\n").replace("\r", "\n")
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
    seen_naia = False
    for index, item in enumerate(raw):
        if not isinstance(item, dict):
            continue
        pane = str(item.get("pane") or "positive").strip().lower()
        if pane not in ADVANCED_FIELD_PANES:
            pane = "positive"
        field_type = str(item.get("type") or "general").strip().lower()
        if field_type not in ADVANCED_FIELD_TYPES:
            field_type = "general"
        if pane == "negative" and field_type == "naia":
            field_type = "general"
        if field_type == "naia":
            if seen_naia:
                continue
            seen_naia = True
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


def _upsert_positive_naia_field(fields: list[dict], prompt: str) -> list[dict]:
    normalized = _normalize_advanced_fields(fields)
    for field in normalized:
        if field["pane"] == "positive" and field["type"] == "naia":
            field["text"] = prompt
            field["enabled"] = True
            return normalized
    normalized.append({
        "id": "positive_naia",
        "pane": "positive",
        "type": "naia",
        "label": ADVANCED_FIELD_LABELS["naia"],
        "text": prompt,
        "height": 150,
        "enabled": True,
    })
    return normalized


def _advanced_pane_parts(fields: list[dict], pane: str) -> dict[str, list[str]]:
    parts = {"quality": [], "artist": [], "body": []}
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
        else:
            parts["body"].append(text)
    return parts


def _build_advanced_prompts(
    fields: list[dict],
    use_anima_mod_guidance: bool,
    pin_trigger_tags_to_front: bool,
) -> tuple[str, str, str, bool, str, str]:
    use_amg = _as_bool(use_anima_mod_guidance, False)
    pin_triggers = _as_bool(pin_trigger_tags_to_front, False)
    positive = _advanced_pane_parts(fields, "positive")
    negative = _advanced_pane_parts(fields, "negative")

    quality_prompt = _join_prompt_tokens(*positive["quality"])
    artist_prompt = _join_prompt_tokens(*positive["artist"])
    body_prompt = _join_prompt_tokens(*positive["body"])

    if pin_triggers:
        metadata_body = _correct_builder_prompt(_join_prompt_tokens(quality_prompt, body_prompt))
        regular_prompt = _join_prompt_tokens(artist_prompt, metadata_body)
        amg_prompt = _join_prompt_tokens(artist_prompt, _correct_builder_prompt(body_prompt))
        metadata_prompt = regular_prompt
    else:
        metadata_core = _correct_builder_prompt(
            _join_prompt_tokens(quality_prompt, artist_prompt, body_prompt),
            artist_overrides=artist_prompt,
        )
        metadata_prompt = metadata_core
        amg_prompt = _correct_builder_prompt(
            _join_prompt_tokens(artist_prompt, body_prompt),
            artist_overrides=artist_prompt,
        )
        regular_prompt = metadata_prompt

    negative_artist = _join_prompt_tokens(*negative["artist"])
    negative_prompt = _correct_builder_prompt(
        _join_prompt_tokens(*negative["quality"], negative_artist, *negative["body"]),
        artist_overrides=negative_artist,
    )

    filter_words = resolve_metadata_filter_words()
    metadata_prompt = _filter_metadata_prompt(metadata_prompt, filter_words)
    metadata_negative_prompt = _filter_metadata_prompt(negative_prompt, filter_words)
    output_prompt = amg_prompt if use_amg else regular_prompt
    return (
        output_prompt,
        negative_prompt,
        quality_prompt,
        use_amg,
        metadata_prompt,
        metadata_negative_prompt,
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
    return names or ["None"]


class EasyUseAnimaPromptCorrector:
    """ANIMA prompt order correction node."""

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


class EasyUseAnimaPromptBuilder:
    """Build cleaned ANIMA prompts for NAIA and Anima Mod Guidance workflows."""

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
                        "through anima_mod_guidance_quality_tags."
                    ),
                }),
                "pin_trigger_tags_to_front": ("BOOLEAN", {
                    "default": False,
                    "tooltip": "true: keep positive artist/trigger fields at the front.",
                }),
                "advanced_fields": ("STRING", {
                    "multiline": True,
                    "default": _advanced_fields_json(),
                    "tooltip": "Internal JSON payload for Advanced Prompt Studio fields.",
                }),
            },
            "optional": _FlexibleOptionalInputType("STRING"),
            "hidden": {
                "workflow_prompt": "PROMPT",
                "extra_pnginfo": "EXTRA_PNGINFO",
                "unique_id": "UNIQUE_ID",
            },
        }

    RETURN_TYPES = ("STRING", "STRING", "STRING", "BOOLEAN", "STRING", "STRING")
    RETURN_NAMES = (
        "positive_prompt",
        "negative_prompt",
        "anima_mod_guidance_quality_tags",
        "use_anima_mod_guidance",
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
        use_naia: bool = False,
        consume_naia_on_queue: bool = True,
        use_anima_mod_guidance: bool = False,
        pin_trigger_tags_to_front: bool = False,
        advanced_fields: str = "",
        **kwargs,
    ):
        if _as_bool(use_naia, False):
            return float("nan")
        fields = _normalize_advanced_fields(advanced_fields)
        effective_fields = _apply_advanced_field_inputs(fields, kwargs)
        return _stable_change_key({
            "mode": "prompt_studio_advanced",
            "metadata_filter_words": resolve_metadata_filter_words(),
            "use_anima_mod_guidance": _as_bool(use_anima_mod_guidance, False),
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
    ) -> None:
        node_id = _single_value(unique_id)
        if node_id is None:
            return
        node_id = str(node_id)
        updates = {
            "use_naia": _as_bool(use_naia, False),
            "advanced_fields": advanced_fields,
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
    def _ui(advanced_fields: str, use_naia: bool, field_inputs: dict | None = None):
        return {
            "prompt_studio_advanced": [{
                "advanced_fields": advanced_fields,
                "use_naia": _as_bool(use_naia, False),
                "field_inputs": field_inputs or {},
            }]
        }

    def build(
        self,
        use_naia: bool,
        consume_naia_on_queue: bool,
        use_anima_mod_guidance: bool,
        pin_trigger_tags_to_front: bool,
        advanced_fields: str,
        workflow_prompt=None,
        extra_pnginfo=None,
        unique_id=None,
        **field_inputs,
    ):
        fields = _normalize_advanced_fields(advanced_fields)
        saved_fields = _clone_advanced_fields(fields)
        effective_fields = _apply_advanced_field_inputs(fields, field_inputs)
        effective_field_inputs = _advanced_field_input_values(field_inputs)
        live_use_naia = _as_bool(use_naia, False)
        metadata_use_naia = live_use_naia

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
            naia_prompt, _naia_negative, _naia_width, _naia_height = _parse_random_response(resp)
            saved_fields = _upsert_positive_naia_field(saved_fields, naia_prompt)
            effective_fields = _upsert_positive_naia_field(effective_fields, naia_prompt)
            metadata_use_naia = False

        fields_json = _advanced_fields_json(saved_fields)
        if live_use_naia:
            self._update_metadata_fields(
                workflow_prompt,
                extra_pnginfo,
                unique_id,
                fields_json,
                metadata_use_naia,
            )

        result = _build_advanced_prompts(
            effective_fields,
            use_anima_mod_guidance,
            pin_trigger_tags_to_front,
        )
        return {
            "ui": self._ui(fields_json, live_use_naia, effective_field_inputs),
            "result": result,
        }


class EasyUseAnimaPromptStudioFixed:
    """Fixed-socket Prompt Studio with numbered positive/negative prompt rows."""

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
        for name, _pane, _field_type, label, default, height in FIXED_PROMPT_SLOT_SPECS:
            required[name] = ("STRING", {
                "multiline": True,
                "default": default,
                "tooltip": label,
                "placeholder": label,
                "height": height,
            })
        return {
            "required": required,
            "hidden": {
                "workflow_prompt": "PROMPT",
                "extra_pnginfo": "EXTRA_PNGINFO",
                "unique_id": "UNIQUE_ID",
            },
        }

    RETURN_TYPES = ("STRING", "STRING", "STRING", "BOOLEAN", "STRING", "STRING")
    RETURN_NAMES = (
        "positive_prompt",
        "negative_prompt",
        "anima_mod_guidance_quality_tags",
        "use_anima_mod_guidance",
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
        **kwargs,
    ):
        if _as_bool(fill_naia_prompt, False):
            return float("nan")
        return _stable_change_key({
            "mode": "prompt_studio_fixed",
            "metadata_filter_words": resolve_metadata_filter_words(),
            "use_anima_mod_guidance": _as_bool(use_anima_mod_guidance, False),
            "pin_trigger_tags_to_front": _as_bool(pin_trigger_tags_to_front, False),
            **{
                name: str(kwargs.get(name, ""))
                for name, *_rest in FIXED_PROMPT_SLOT_SPECS
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
    def _fields_from_slots(values: dict[str, str]) -> list[dict]:
        fields = []
        for name, pane, field_type, label, _default, height in FIXED_PROMPT_SLOT_SPECS:
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
    def _ui(slot_values: dict[str, str], fill_naia_prompt: bool):
        return {
            "prompt_studio_slots": [{
                **slot_values,
                "fill_naia_prompt": _as_bool(fill_naia_prompt, False),
            }]
        }

    def build(
        self,
        fill_naia_prompt: bool,
        use_anima_mod_guidance: bool,
        pin_trigger_tags_to_front: bool,
        workflow_prompt=None,
        extra_pnginfo=None,
        unique_id=None,
        **slot_values,
    ):
        values = {
            name: str(slot_values.get(name, default) or "")
            for name, _pane, _field_type, _label, default, _height in FIXED_PROMPT_SLOT_SPECS
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
            self._fields_from_slots(values),
            use_anima_mod_guidance,
            pin_trigger_tags_to_front,
        )
        return {
            "ui": self._ui(values, live_fill_naia),
            "result": result,
        }


class EasyUseAnimaLoraPreset:
    """Multi-profile LoRA stack preset node for ANIMA style prompts."""

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

            dedupe_key = (lora_name, model_strength, clip_strength)
            if dedupe_key in seen:
                continue
            seen.add(dedupe_key)

            lora_path, lora_trigger_words = _get_lora_info(lora_name)
            stack.append((str(lora_path).replace("/", os.sep), model_strength, clip_strength))
            trigger_words.extend(lora_trigger_words)
            active_loras.append((active_lora_name, model_strength, clip_strength))

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


class EasyUseAnimaNAIARandomPrompt:
    """NAIA random prompt node with bypass and frozen-output cache."""

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
            "timeout": FIXED_TIMEOUT,
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
