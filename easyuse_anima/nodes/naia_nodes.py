"""ComfyUI adapter for the NAIA random prompt client."""

from __future__ import annotations

from ..common.serialization import _stable_change_key
from ..common.values import _as_bool, _as_int, _single_value
from ..naia.client import (
    DEFAULT_HOST,
    DEFAULT_PORT,
    NAIA_MAX_RESOLUTION,
    PP_STATE_CHOICES,
    PREPROCESSING_KEYS,
    _parse_random_response,
    _post_random,
)
from ..naia.random_prompt import (
    _apply_overrides,
    _cached_tuple,
    _make_request_body,
    _make_signature,
    _request_random_prompt,
    _ui,
)
from ..settings.service import resolve_naia_settings
from ..workflow import _get_workflow_node


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
                    "Legacy hidden workflow-schema compatibility value. EasyUse Anima Settings "
                    "globally controls whether desktop Prompt Engineering overrides are sent."
                ),
            }),
            "pre_prompt": ("STRING", {
                "multiline": True,
                "default": "",
                "placeholder": "pre_prompt",
                "tooltip": "Legacy hidden workflow-schema compatibility value; configure the global EasyUse Anima NAIA settings.",
            }),
            "post_prompt": ("STRING", {
                "multiline": True,
                "default": "",
                "placeholder": "post_prompt",
                "tooltip": "Legacy hidden workflow-schema compatibility value; configure the global EasyUse Anima NAIA settings.",
            }),
            "auto_hide": ("STRING", {
                "multiline": True,
                "default": "",
                "placeholder": "auto_hide",
                "tooltip": "Legacy hidden workflow-schema compatibility value; configure the global EasyUse Anima NAIA settings.",
            }),
        }

        pp_tooltip = (
            "Legacy hidden workflow-schema compatibility value. Configure preprocessing in "
            "the global EasyUse Anima NAIA settings."
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
            "tooltip": "Legacy hidden workflow-schema compatibility value; the global EasyUse Anima NAIA host is used.",
        })
        required["port"] = ("INT", {
            "default": DEFAULT_PORT, "min": 1, "max": 65535,
            "tooltip": "Legacy hidden workflow-schema compatibility value; the global EasyUse Anima NAIA port is used.",
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
        self._cache_signature: str | None = None
        self._cache_value: tuple[str, str, int, int] | None = None

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

    _cached_tuple = staticmethod(_cached_tuple)
    _make_signature = staticmethod(_make_signature)
    _make_request_body = staticmethod(_make_request_body)
    _apply_overrides = staticmethod(_apply_overrides)
    _ui = staticmethod(_ui)

    @classmethod
    def _widget_input_names(cls) -> list[str]:
        return list(cls.INPUT_TYPES()["required"].keys())

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
        return _request_random_prompt(
            self,
            use_naia_bridge=use_naia_bridge,
            freeze_naia_output=freeze_naia_output,
            cached_prompt=cached_prompt,
            cached_negative_prompt=cached_negative_prompt,
            cached_width=cached_width,
            cached_height=cached_height,
            cached_signature=cached_signature,
            prompt=prompt,
            override_prompt=override_prompt,
            negative_prompt=negative_prompt,
            override_negative=override_negative,
            width=width,
            override_width=override_width,
            height=height,
            override_height=override_height,
            workflow_prompt=workflow_prompt,
            extra_pnginfo=extra_pnginfo,
            unique_id=unique_id,
            resolve_settings=resolve_naia_settings,
            post_random=_post_random,
            parse_random_response=_parse_random_response,
            update_metadata_cache=self._update_metadata_cache,
            make_signature=self._make_signature,
            cached_tuple=self._cached_tuple,
            make_request_body=self._make_request_body,
            apply_overrides=self._apply_overrides,
            render_ui=self._ui,
        )

__all__ = ("EasyUseAnimaNAIARandomPrompt",)
