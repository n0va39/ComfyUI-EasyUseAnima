"""ComfyUI adapter for the NAIA random prompt client."""

from __future__ import annotations

import json
import logging
from typing import Optional

from ..common.serialization import _stable_change_key
from ..common.values import _as_bool, _as_int, _single_value
from ..naia.client import (
    DEFAULT_HOST,
    DEFAULT_PORT,
    NAIA_MAX_RESOLUTION,
    NAIA_REQUEST_TIMEOUT,
    PP_STATE_CHOICES,
    PREPROCESSING_KEYS,
    _parse_random_response,
    _post_random,
)
from ..settings.service import resolve_naia_settings
from ..workflow import _get_workflow_node

logger = logging.getLogger("ComfyUI-EasyUseAnima")


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
                "default": 0, "min": 0, "max": NAIA_MAX_RESOLUTION, "step": 8,
                "tooltip": "Stored width used for frozen output and saved-image reproduction.",
            }),
            "cached_height": ("INT", {
                "default": 0, "min": 0, "max": NAIA_MAX_RESOLUTION, "step": 8,
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
                "default": 1024, "min": 64, "max": NAIA_MAX_RESOLUTION, "step": 8,
                "tooltip": "Returned as-is when bypassed or when override_width is false.",
            }),
            "override_width": ("BOOLEAN", {
                "default": True,
                "tooltip": "true: use NAIA width. false: preserve input width.",
            }),
            "height": ("INT", {
                "default": 1024, "min": 64, "max": NAIA_MAX_RESOLUTION, "step": 8,
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
            resp = _post_random(
                host,
                port,
                body,
                allow_remote_api=bool(naia_settings.get("allow_remote_api", False)),
            )
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

__all__ = ("EasyUseAnimaNAIARandomPrompt",)
