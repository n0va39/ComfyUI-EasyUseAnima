# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import logging
import re
from typing import Optional

try:
    from .animadex_dataset import download_animadex_dataset
    from .anima_prompt import correct_prompt, load_knowledge_base
    from .anima_prompt.knowledge import PACKAGE_DATA_DIR
    from .anima_prompt.parser import parse_prompt
    from .settings import resolve_animadex_site, resolve_metadata_filter_words
except ImportError:  # allows simple local import tests outside ComfyUI's package loader
    from animadex_dataset import download_animadex_dataset
    from anima_prompt import correct_prompt, load_knowledge_base
    from anima_prompt.knowledge import PACKAGE_DATA_DIR
    from anima_prompt.parser import parse_prompt
    from settings import resolve_animadex_site, resolve_metadata_filter_words

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
DEFAULT_ANIMADEX_SITE = "https://animadex.net"


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
                "validate_artist_tags": ("BOOLEAN", {
                    "default": True,
                    "tooltip": "Only AnimaDex artists and manual overrides are treated as @artist tags.",
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
                "animadex_characters_csv": ("STRING", {
                    "multiline": False,
                    "default": "",
                    "tooltip": "Optional explicit AnimaDex characters.csv path.",
                }),
                "animadex_artists_csv": ("STRING", {
                    "multiline": False,
                    "default": "",
                    "tooltip": "Optional explicit AnimaDex artists.csv path.",
                }),
                "animadex_character_index": ("STRING", {
                    "multiline": False,
                    "default": "",
                    "tooltip": "Optional explicit AnimaDex character_index.jsonl path.",
                }),
                "animadex_artist_index": ("STRING", {
                    "multiline": False,
                    "default": "",
                    "tooltip": "Optional explicit AnimaDex artist_index.jsonl path.",
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
        validate_artist_tags: bool,
        artist_overrides: str,
        artist_exclusions: str,
        animadex_characters_csv: str,
        animadex_artists_csv: str,
        animadex_character_index: str,
        animadex_artist_index: str,
    ):
        try:
            kb = load_knowledge_base(
                animadex_characters_csv=animadex_characters_csv.strip() or None,
                animadex_artists_csv=animadex_artists_csv.strip() or None,
                animadex_character_index=animadex_character_index.strip() or None,
                animadex_artist_index=animadex_artist_index.strip() or None,
                allow_missing=True,
            )
            result = correct_prompt(
                str(prompt or ""),
                profile="prompt",
                knowledge_base=kb,
                validate_artist_tags=_as_bool(validate_artist_tags, True),
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


class EasyUseAnimaAnimaDexDatasetDownload:
    """Download AnimaDex CSV exports into the node pack local dataset store."""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "site_override": ("STRING", {
                    "multiline": False,
                    "default": "",
                    "tooltip": "Optional AnimaDex site override. Empty uses the ComfyUI settings value.",
                }),
                "force_refresh": ("BOOLEAN", {
                    "default": False,
                    "tooltip": "Download again even if local index files already exist.",
                }),
                "full_manifest": ("BOOLEAN", {
                    "default": False,
                    "tooltip": "Request the full AnimaDex export manifest.",
                }),
            }
        }

    RETURN_TYPES = ("STRING", "STRING", "STRING", "STRING")
    RETURN_NAMES = ("status", "report", "character_index", "artist_index")
    FUNCTION = "download"
    CATEGORY = "EasyUse Anima/Data"

    @classmethod
    def IS_CHANGED(
        cls,
        site_override: str = "",
        force_refresh=False,
        full_manifest=False,
    ):
        if _as_bool(force_refresh, False):
            return float("nan")
        data_dir = PACKAGE_DATA_DIR
        character_index = data_dir / "index" / "character_index.jsonl"
        artist_index = data_dir / "index" / "artist_index.jsonl"
        return _stable_change_key({
            "mode": "animadex_dataset",
            "site": resolve_animadex_site(site_override),
            "full_manifest": _as_bool(full_manifest, False),
            "character_index_exists": character_index.is_file(),
            "artist_index_exists": artist_index.is_file(),
            "character_index_mtime": character_index.stat().st_mtime if character_index.is_file() else 0,
            "artist_index_mtime": artist_index.stat().st_mtime if artist_index.is_file() else 0,
        })

    def download(
        self,
        site_override: str,
        force_refresh: bool,
        full_manifest: bool,
    ):
        data_dir = PACKAGE_DATA_DIR
        import_dir = data_dir / "import"
        index_dir = data_dir / "index"
        character_index = index_dir / "character_index.jsonl"
        artist_index = index_dir / "artist_index.jsonl"

        if (
            not _as_bool(force_refresh, False)
            and character_index.is_file()
            and artist_index.is_file()
        ):
            report = {
                "status": "cached",
                "data_dir": str(data_dir),
                "character_index": str(character_index),
                "artist_index": str(artist_index),
            }
            return (
                "cached",
                json.dumps(report, ensure_ascii=False, indent=2),
                str(character_index),
                str(artist_index),
            )

        return download_animadex_dataset(
            force_refresh=_as_bool(force_refresh, False),
            full_manifest=_as_bool(full_manifest, False),
            site_override=site_override,
        )


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
            kwargs,
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
