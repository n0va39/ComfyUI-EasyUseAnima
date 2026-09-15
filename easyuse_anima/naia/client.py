"""NAIA Remote API transport and response normalization."""

from __future__ import annotations

import re
from math import sqrt

from ..infrastructure.comfy.wiring import resolve_naia_endpoints
from .endpoint_policy import DEFAULT_NAIA_ENDPOINTS, normalize_naia_host

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 7243
NAIA_LOCAL_HOSTS = {"127.0.0.1", "localhost", "::1"}
NAIA_REQUEST_TIMEOUT = 30.0
HTTP_TIMEOUT = NAIA_REQUEST_TIMEOUT + 5.0
NAI_1MP = 1024 * 1024
LATENT_ALIGN = 8
NAIA_MAX_RESOLUTION = 8192
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


def _clean_prompt(value: str) -> str:
    if not value:
        return value
    value = _HASH_COMMENT_RE.sub("", value)
    value = _MULTI_COMMA_RE.sub(",", value)
    return value.strip(" ,\n\t")


def _fit_to_1mp(width: int, height: int) -> tuple[int, int]:
    if width <= 0 or height <= 0:
        return width, height
    if width * height <= NAI_1MP:
        return width, height

    scale = sqrt(NAI_1MP / (width * height))
    new_w = max(LATENT_ALIGN, round(width * scale / LATENT_ALIGN) * LATENT_ALIGN)
    new_h = max(LATENT_ALIGN, round(height * scale / LATENT_ALIGN) * LATENT_ALIGN)
    if new_w * new_h > NAI_1MP:
        if new_w >= new_h:
            new_w = (NAI_1MP // new_h // LATENT_ALIGN) * LATENT_ALIGN
        else:
            new_h = (NAI_1MP // new_w // LATENT_ALIGN) * LATENT_ALIGN
    return new_w, new_h


def _is_local_naia_host(host: str) -> bool:
    return normalize_naia_host(host) in NAIA_LOCAL_HOSTS


def _build_naia_random_url(host: str, port: int, allow_remote_api: bool = False) -> str:
    try:
        host_value = normalize_naia_host(host or DEFAULT_HOST)
    except ValueError:
        raise RuntimeError("[EasyUse Anima] NAIA host must be a hostname or IP address, not a URL.") from None
    if not allow_remote_api and not _is_local_naia_host(host_value):
        raise RuntimeError(
            "[EasyUse Anima] Remote NAIA API access is disabled. "
            "Enable 'Allow remote API' in EasyUse Anima NAIA settings to use a non-local host."
        )
    endpoints = resolve_naia_endpoints()
    if endpoints is None:
        endpoints = DEFAULT_NAIA_ENDPOINTS
    for approved_host, approved_port, address in endpoints:
        if host_value == approved_host and type(port) is int and port == approved_port:
            url_host = f"[{address}]" if ":" in address else address
            return f"http://{url_host}:{port}/api/comfyui/random"
    raise RuntimeError(
        "[EasyUse Anima] NAIA endpoint is not approved by the ComfyUI operator. "
        "Configure EASYUSE_ANIMA_NAIA_ENDPOINTS before starting ComfyUI."
    )


def _reject_naia_redirect(response, **_kwargs):
    # Requests prepares the next request even with allow_redirects=False.
    # Reject before it parses an untrusted Location header.
    if 300 <= response.status_code < 400:
        try:
            response.close()
        finally:
            raise RuntimeError("[EasyUse Anima] NAIA API redirects are not allowed.") from None
    return response


def _post_random(host: str, port: int, body: dict, allow_remote_api: bool = False) -> dict:
    try:
        import requests
    except ImportError:
        raise RuntimeError("[EasyUse Anima] requests is not installed. Install requirements.txt.")

    url = _build_naia_random_url(host, port, allow_remote_api=allow_remote_api)
    host_value = normalize_naia_host(host or DEFAULT_HOST)
    authority = f"[{host_value}]:{port}" if ":" in host_value else f"{host_value}:{port}"
    # Localhost-only defaults; allow_remote_api=True is a user preference and
    # cannot expand the operator allowlist. Do not inherit proxies or netrc.
    try:
        with requests.Session() as session:
            session.trust_env = False
            with session.post(
                url, json=body, timeout=HTTP_TIMEOUT, allow_redirects=False,
                headers={"Host": authority},
                hooks={"response": _reject_naia_redirect},
            ) as response:
                if not response.ok:
                    raise RuntimeError(
                        f"[EasyUse Anima] NAIA API error HTTP {response.status_code}."
                    )
                try:
                    data = response.json()
                except ValueError:
                    raise RuntimeError("[EasyUse Anima] NAIA API returned invalid JSON.") from None
    except requests.RequestException:
        raise RuntimeError("[EasyUse Anima] NAIA API request failed.") from None

    if not isinstance(data, dict) or not data.get("ok", True):
        raise RuntimeError("[EasyUse Anima] NAIA API returned an error response.")
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
    if not (
        1 <= raw_width <= NAIA_MAX_RESOLUTION
        and 1 <= raw_height <= NAIA_MAX_RESOLUTION
    ):
        raise RuntimeError(
            f"[EasyUse Anima] Invalid NAIA width/height: {w_raw!r}, {h_raw!r}; "
            f"expected values from 1 to {NAIA_MAX_RESOLUTION}."
        )
    width, height = _fit_to_1mp(raw_width, raw_height)
    return prompt, negative, width, height

__all__ = ()
