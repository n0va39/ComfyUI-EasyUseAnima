"""LoRA profile normalization, persistence, and installed-file repair."""

from __future__ import annotations

import json
import os
from pathlib import Path

from ..infrastructure.filesystem.atomic_json import AtomicJsonStore
from ..infrastructure.filesystem.paths import USER_DATA_DIR
from .contract import (
    PROFILE_KIND_LORA,
    ProfileContractError,
    build_profile_document,
    create_profile_document,
    interpret_profile_document,
    update_profile_document,
)
from .mutation import (
    PROFILE_MUTATION_COORDINATOR,
    require_profile_precondition,
    verify_profile_precondition,
)
from .repository import (
    InvalidProfileDataError,
    _profile_list_item,
    _read_profile_json,
    _sanitize_profile_name,
    _windows_profile_filename_identity,
)

LORA_PROFILE_DIR = USER_DATA_DIR / "profiles"
MAX_LORA_PROFILES = 16


def _sanitize_lora_profile_name(name: str) -> str:
    return _sanitize_profile_name(name)


def _lora_profile_path(name: str, profile_dir: Path | None = None) -> Path:
    safe_name = _sanitize_lora_profile_name(name)
    root = (profile_dir or LORA_PROFILE_DIR).resolve()
    path = (root / f"{safe_name}.json").resolve()
    if os.path.commonpath((str(root), str(path))) != str(root):
        raise ValueError("Invalid profile path")
    return path


def _find_lora_profile_path(
    name: str,
    profile_dir: Path | None = None,
) -> Path | None:
    safe_name = _sanitize_lora_profile_name(name)
    root = profile_dir or LORA_PROFILE_DIR
    if not root.is_dir():
        return None
    expected = _windows_profile_filename_identity(safe_name)
    return next(
        (
            path
            for path in sorted(
                root.glob("*.json"),
                key=lambda item: (item.name.casefold(), item.name),
            )
            if _windows_profile_filename_identity(path.stem) == expected
        ),
        None,
    )


def _as_lora_profile_count(value) -> int:
    try:
        count = int(value)
    except (TypeError, ValueError):
        count = 1
    return max(1, min(MAX_LORA_PROFILES, count))


def _as_lora_profile_index(value, count: int) -> int:
    try:
        index = int(value)
    except (TypeError, ValueError):
        index = 1
    index = max(1, index)
    return ((index - 1) % count) + 1


def _normalize_lora_profile_data(value) -> dict:
    if isinstance(value, str):
        try:
            value = json.loads(value or "{}")
        except (TypeError, ValueError):
            value = {}
    if not isinstance(value, dict):
        return {}
    normalized: dict[str, dict] = {}
    for key, profile in value.items():
        if not isinstance(profile, dict):
            continue
        style_prompt = str(profile.get("style_prompt") or "")
        loras = profile.get("loras")
        if not isinstance(loras, list):
            loras = []
        normalized[str(key)] = {
            "style_prompt": style_prompt,
            "loras": [item for item in loras if isinstance(item, dict)],
        }
    return normalized


def _normalize_lora_profile_payload(data: dict) -> dict:
    count = _as_lora_profile_count(data.get("profile_count", 1))
    return {
        "version": 1,
        "profile_count": count,
        "profile_index": _as_lora_profile_index(
            data.get("profile_index", 1),
            count,
        ),
        "profile_data": _normalize_lora_profile_data(
            data.get("profile_data", {}),
        ),
    }


def _list_lora_profiles() -> list[dict]:
    if not LORA_PROFILE_DIR.is_dir():
        return []
    profiles = []
    for path in sorted(
        LORA_PROFILE_DIR.glob("*.json"),
        key=lambda item: item.stem.lower(),
    ):
        if path.name == ".gitignore":
            continue
        profiles.append(_profile_list_item(PROFILE_KIND_LORA, path))
    return profiles


def _clear_folder_paths_cache(folder_paths, folder_name: str):
    cache = getattr(folder_paths, "filename_list_cache", None)
    if isinstance(cache, dict):
        cache.pop(folder_name, None)
    cache_helper = getattr(folder_paths, "cache_helper", None)
    if cache_helper is not None and not getattr(cache_helper, "active", False):
        clear = getattr(cache_helper, "clear", None)
        if callable(clear):
            clear()


def _list_loras() -> list[str]:
    try:
        import folder_paths  # type: ignore
    except Exception:
        return []

    _clear_folder_paths_cache(folder_paths, "loras")
    try:
        names = folder_paths.get_filename_list("loras")
    except Exception:
        names = []

    loras = []
    seen = set()
    for name in names:
        text = str(name or "").strip()
        if not text or text == "None":
            continue
        key = text.replace("\\", "/").casefold()
        if key in seen:
            continue
        seen.add(key)
        loras.append(text)
    return loras


def _lora_full_path(name: str) -> str | None:
    try:
        import folder_paths  # type: ignore
    except Exception:
        return None

    text = str(name or "").strip()
    if not text or text == "None":
        return None
    candidates = _dedupe_text_values(
        (
            text,
            text.replace("\\", "/"),
            text.replace("/", os.sep),
        )
    )
    for candidate in candidates:
        try:
            path = folder_paths.get_full_path("loras", candidate)
        except Exception:
            path = None
        if path:
            return str(path)
    return None


def _dedupe_text_values(values) -> list[str]:
    seen = set()
    result = []
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


def _lora_file_key(value: str) -> str:
    name = os.path.basename(str(value or "").replace("\\", "/").strip())
    return name.casefold()


def _put_unique(mapping: dict[str, str | None], key: str, value: str):
    if not key:
        return
    if key not in mapping:
        mapping[key] = value
        return
    current = mapping[key]
    if current is None:
        return
    if current and current != value:
        mapping[key] = None
        return
    mapping[key] = value


def _lora_path_exists(name: str) -> bool:
    path = _lora_full_path(name)
    return bool(path and os.path.isfile(path))


def _build_lora_fix_index(lora_names: list[str] | None = None) -> dict:
    by_file: dict[str, str | None] = {}
    names = list(lora_names) if lora_names is not None else _list_loras()

    for name in names:
        _put_unique(by_file, _lora_file_key(name), name)

    return {
        "by_file": by_file,
        "names": names,
    }


def _resolve_lora_for_fix(entry: dict, index: dict) -> tuple[str, str]:
    raw_name = str(entry.get("name", entry.get("lora", "")) or "").strip()
    match = index["by_file"].get(_lora_file_key(raw_name))
    return (match, "file") if match else ("", "")


def _apply_lora_fix(
    next_lora: dict,
    profile_key: str,
    raw_name: str,
    match: str,
    reason: str,
    fixed: list,
):
    changed = raw_name != match
    next_lora["name"] = match
    next_lora.pop("lora", None)
    if changed:
        fixed.append(
            {
                "profile": profile_key,
                "from": raw_name,
                "to": match,
                "reason": reason,
            }
        )


def _fix_lora_profile_payload(data: dict) -> dict:
    payload = _normalize_lora_profile_payload(
        data if isinstance(data, dict) else {},
    )
    fixed = []
    unresolved = []
    missing_entries = []

    for profile_key, profile in payload["profile_data"].items():
        if not isinstance(profile, dict):
            continue
        next_loras = []
        for lora in profile.get("loras") or []:
            if not isinstance(lora, dict):
                continue
            next_lora = dict(lora)
            raw_name = str(
                next_lora.get("name", next_lora.get("lora", "")) or ""
            ).strip()
            if not raw_name:
                continue
            next_loras.append(next_lora)
            if _lora_path_exists(raw_name):
                if "name" not in next_lora and "lora" in next_lora:
                    next_lora["name"] = raw_name
                    next_lora.pop("lora", None)
                continue
            missing_entries.append((profile_key, next_lora, raw_name))
        profile["loras"] = next_loras

    if missing_entries:
        lora_names = _list_loras()
        index = _build_lora_fix_index(lora_names=lora_names)
        for profile_key, next_lora, raw_name in missing_entries:
            match, reason = _resolve_lora_for_fix(next_lora, index)
            if match:
                _apply_lora_fix(
                    next_lora,
                    profile_key,
                    raw_name,
                    match,
                    reason,
                    fixed,
                )
            else:
                unresolved.append({"profile": profile_key, "name": raw_name})

    payload["fixed"] = fixed
    payload["unresolved"] = unresolved
    payload["checked"] = sum(
        len(profile.get("loras") or [])
        for profile in payload["profile_data"].values()
        if isinstance(profile, dict)
    )
    payload["missing"] = len(missing_entries)
    return payload


def _save_lora_profile(
    name: str,
    data: dict,
    *,
    overwrite: bool = False,
    profile_id: str | None = None,
    revision: int | None = None,
) -> dict:
    safe_name = _sanitize_lora_profile_name(name)
    payload = _normalize_lora_profile_payload(data)
    requested_path = _lora_profile_path(safe_name)
    if overwrite:
        require_profile_precondition(profile_id, revision)
    with PROFILE_MUTATION_COORDINATOR.locked(LORA_PROFILE_DIR):
        existing = _find_lora_profile_path(safe_name)
        if existing is not None and not overwrite:
            raise FileExistsError("Profile already exists")
        if existing is None and overwrite:
            raise FileNotFoundError("Profile not found")
        path = existing or requested_path
        try:
            if existing is None:
                document = create_profile_document(
                    PROFILE_KIND_LORA,
                    path.stem,
                    payload,
                )
            else:
                current = _read_profile_json(path)
                if not isinstance(current, dict):
                    raise ProfileContractError("Profile data is invalid")
                verify_profile_precondition(
                    PROFILE_KIND_LORA,
                    path.stem,
                    current,
                    profile_id=profile_id,
                    revision=revision,
                )
                document = update_profile_document(
                    PROFILE_KIND_LORA,
                    path.stem,
                    current,
                    payload,
                )
        except ProfileContractError as exc:
            raise InvalidProfileDataError(str(exc)) from exc
        AtomicJsonStore(path).write(document)
    return document


def _load_lora_profile(name: str) -> dict:
    path = _find_lora_profile_path(name)
    if path is None or not path.is_file():
        raise FileNotFoundError("Profile not found")
    data = _read_profile_json(path)
    if not isinstance(data, dict):
        raise InvalidProfileDataError("Profile data is invalid")
    profile_data = data.get("profile_data", {})
    if isinstance(profile_data, str):
        try:
            decoded_profile_data = json.loads(profile_data or "{}")
        except (TypeError, ValueError) as exc:
            raise InvalidProfileDataError("Profile data is invalid") from exc
        if not isinstance(decoded_profile_data, dict):
            raise InvalidProfileDataError("Profile data is invalid")
    elif not isinstance(profile_data, dict):
        raise InvalidProfileDataError("Profile data is invalid")
    payload = _normalize_lora_profile_payload(data)
    try:
        interpreted = interpret_profile_document(
            PROFILE_KIND_LORA,
            path.stem,
            data,
        )
        return build_profile_document(
            name=path.stem,
            profile_id=interpreted["profile_id"],
            revision=interpreted["revision"],
            payload=payload,
        )
    except ProfileContractError as exc:
        raise InvalidProfileDataError(str(exc)) from exc


__all__ = ()
