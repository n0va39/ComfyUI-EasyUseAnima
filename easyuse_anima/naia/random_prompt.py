"""NAIA random-prompt request, cache, and payload service."""

from __future__ import annotations

import json
import logging
from collections.abc import Callable, Mapping
from typing import Any, Protocol

from ..common.values import _as_bool, _as_int
from .client import DEFAULT_PORT, NAIA_REQUEST_TIMEOUT, PREPROCESSING_KEYS

logger = logging.getLogger("ComfyUI-EasyUseAnima")

_RandomPromptValue = tuple[str, str, int, int]
_ResolveSettings = Callable[[], Mapping[str, Any]]
_PostRandom = Callable[..., dict[str, Any]]
_ParseRandomResponse = Callable[[dict[str, Any]], _RandomPromptValue]
_UpdateMetadataCache = Callable[[Any, Any, Any, _RandomPromptValue, str], None]
_MakeSignature = Callable[..., str]
_CachedTuple = Callable[[str, str, int, int], _RandomPromptValue | None]
_MakeRequestBody = Callable[..., dict[str, Any]]
_ApplyOverrides = Callable[..., _RandomPromptValue]
_RenderUi = Callable[..., dict[str, list[Any]]]


class _RandomPromptCache(Protocol):
    _cache_signature: str | None
    _cache_value: _RandomPromptValue | None


def _cached_tuple(
    cached_prompt: str,
    cached_negative_prompt: str,
    cached_width: int,
    cached_height: int,
) -> _RandomPromptValue | None:
    width = _as_int(cached_width, 0)
    height = _as_int(cached_height, 0)
    if width <= 0 or height <= 0:
        return None
    if not cached_prompt and not cached_negative_prompt:
        return None
    return (str(cached_prompt), str(cached_negative_prompt), width, height)


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
    pp_kwargs: Mapping[str, Any],
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


def _make_request_body(
    use_naia_settings: bool,
    pre_prompt: str,
    post_prompt: str,
    auto_hide: str,
    pp_kwargs: Mapping[str, Any],
) -> dict[str, Any]:
    body: dict[str, Any] = {
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


def _apply_overrides(
    naia_value: _RandomPromptValue,
    prompt: str,
    override_prompt: bool,
    negative_prompt: str,
    override_negative: bool,
    width: int,
    override_width: bool,
    height: int,
    override_height: bool,
) -> _RandomPromptValue:
    naia_prompt, naia_negative, naia_width, naia_height = naia_value
    return (
        naia_prompt if override_prompt else str(prompt),
        naia_negative if override_negative else str(negative_prompt),
        naia_width if override_width else _as_int(width, 1024),
        naia_height if override_height else _as_int(height, 1024),
    )


def _ui(
    prompt: str,
    negative: str,
    width: int,
    height: int,
    status: str,
    signature: str,
) -> dict[str, list[Any]]:
    return {
        "prompt": [prompt],
        "negative_prompt": [negative],
        "width": [width],
        "height": [height],
        "status": [status],
        "cached_signature": [signature],
    }


def _request_value(
    settings: Mapping[str, Any],
    *,
    prompt: str,
    override_prompt: bool,
    negative_prompt: str,
    override_negative: bool,
    width: int,
    override_width: bool,
    height: int,
    override_height: bool,
    use_settings: bool,
    pre_prompt: str,
    post_prompt: str,
    auto_hide: str,
    pp_kwargs: Mapping[str, Any],
    post_random: _PostRandom,
    parse_random_response: _ParseRandomResponse,
    make_request_body: _MakeRequestBody,
    apply_overrides: _ApplyOverrides,
) -> _RandomPromptValue:
    body = make_request_body(
        use_settings,
        pre_prompt,
        post_prompt,
        auto_hide,
        pp_kwargs,
    )
    response = post_random(
        settings["host"],
        settings["port"],
        body,
        allow_remote_api=bool(settings.get("allow_remote_api", False)),
    )
    value = apply_overrides(
        parse_random_response(response),
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
        response.get("request_id"),
        len(value[0]),
        value[2],
        value[3],
        use_settings,
    )
    return value


def _request_random_prompt(
    cache: _RandomPromptCache,
    *,
    use_naia_bridge: bool,
    freeze_naia_output: bool,
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
    workflow_prompt: Any,
    extra_pnginfo: Any,
    unique_id: Any,
    resolve_settings: _ResolveSettings,
    post_random: _PostRandom,
    parse_random_response: _ParseRandomResponse,
    update_metadata_cache: _UpdateMetadataCache,
    make_signature: _MakeSignature,
    cached_tuple: _CachedTuple,
    make_request_body: _MakeRequestBody,
    apply_overrides: _ApplyOverrides,
    render_ui: _RenderUi,
) -> dict[str, Any]:
    settings = resolve_settings()
    use_settings = _as_bool(settings["use_naia_settings"], True)
    override_prompt = _as_bool(override_prompt, True)
    override_negative = _as_bool(override_negative, True)
    override_width = _as_bool(override_width, True)
    override_height = _as_bool(override_height, True)
    signature = make_signature(
        prompt,
        override_prompt,
        negative_prompt,
        override_negative,
        width,
        override_width,
        height,
        override_height,
        use_settings,
        settings["pre_prompt"],
        settings["post_prompt"],
        settings["auto_hide"],
        settings["host"],
        settings["port"],
        settings["preprocessing"],
    )

    if not _as_bool(use_naia_bridge, True):
        value = (str(prompt), str(negative_prompt), _as_int(width, 1024), _as_int(height, 1024))
        return {"ui": render_ui(*value, "disabled", signature), "result": value}

    saved_cache = cached_tuple(
        cached_prompt,
        cached_negative_prompt,
        cached_width,
        cached_height,
    )
    freeze_output = _as_bool(freeze_naia_output, False)
    if freeze_output and saved_cache is not None and str(cached_signature) == signature:
        return {"ui": render_ui(*saved_cache, "frozen", signature), "result": saved_cache}

    if cache._cache_signature != signature:
        cache._cache_signature = signature
        cache._cache_value = (
            saved_cache if saved_cache is not None and str(cached_signature) == signature else None
        )
    if cache._cache_value is None or not freeze_output:
        cache._cache_value = _request_value(
            settings,
            prompt=prompt,
            override_prompt=override_prompt,
            negative_prompt=negative_prompt,
            override_negative=override_negative,
            width=width,
            override_width=override_width,
            height=height,
            override_height=override_height,
            use_settings=use_settings,
            pre_prompt=settings["pre_prompt"],
            post_prompt=settings["post_prompt"],
            auto_hide=settings["auto_hide"],
            pp_kwargs=settings["preprocessing"],
            post_random=post_random,
            parse_random_response=parse_random_response,
            make_request_body=make_request_body,
            apply_overrides=apply_overrides,
        )
    if cache._cache_value is None:
        raise RuntimeError("[EasyUse Anima] Internal cache creation failed.")

    value = cache._cache_value
    update_metadata_cache(workflow_prompt, extra_pnginfo, unique_id, value, signature)
    return {"ui": render_ui(*value, "fresh", signature), "result": value}


__all__ = ()
