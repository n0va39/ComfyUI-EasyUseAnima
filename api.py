from __future__ import annotations

import atexit
import asyncio
import json
import os
import re
import threading
import weakref
from concurrent.futures import Future, ThreadPoolExecutor
from pathlib import Path

try:
    import server
    from aiohttp import web
except ImportError:
    server = None
    web = None

from .settings import (
    load_long_text_settings,
    public_settings,
    resolve_autocomplete_limit,
    resolve_autocomplete_source,
    resolve_prompt_translation_settings,
    save_setting,
    save_long_text_settings,
)
from .autocomplete_dataset import (
    autocomplete_status,
    available_autocomplete_sources,
    classify_prompt_text,
    resolve_autocomplete_source as resolve_autocomplete_source_path,
    search_autocomplete,
)
from .wildcard_engine import list_wildcards, resolve_wildcard_roots
from .prompt_translation import (
    PromptTranslationError,
    TranslationBusyError,
    TranslationCancelledError,
    TranslationTimeoutError,
    translate_prompt_markers,
)
from .api_contract import (
    ApiContractError,
    error_payload,
    json_boolean,
    json_integer,
    json_object,
    json_string,
    parse_json_object,
)
try:
    from .storage import AtomicJsonStore, USER_DATA_DIR
except ImportError:
    from storage import AtomicJsonStore, USER_DATA_DIR


LORA_PREVIEW_EXTENSIONS = (".webp", ".png", ".jpg", ".jpeg")
LORA_PROFILE_DIR = USER_DATA_DIR / "profiles"
MAX_LORA_PROFILES = 16
INVALID_PROFILE_NAME_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]+')
AIO_PROFILE_DIR = USER_DATA_DIR / "aio_profiles"
MAX_AIO_PROFILES = 64
MAX_AIO_PROFILE_BYTES = 1024 * 1024
AIO_RESERVED_PROFILE_NAMES = {
    "normal",
    "turbo",
    "optimized",
    "custom",
    "일반",
    "터보",
    "최적화",
    "커스텀",
    "通常",
    "最適化",
    "カスタム",
    "普通",
    "优化",
    "自定义",
}
WINDOWS_RESERVED_FILE_BASENAMES = {
    "con",
    "prn",
    "aux",
    "nul",
    *(f"com{index}" for index in range(1, 10)),
    *(f"lpt{index}" for index in range(1, 10)),
    *(f"com{index}" for index in ("¹", "²", "³")),
    *(f"lpt{index}" for index in ("¹", "²", "³")),
}
PROMPT_TRANSLATION_ROUTE_TIMEOUT_SECONDS = 15.0
FILE_IO_MAX_IN_FLIGHT = 4


class InvalidProfileDataError(ValueError):
    pass


_FILE_IO_LIMITERS_LOCK = threading.Lock()
_FILE_IO_LIMITERS: weakref.WeakKeyDictionary = weakref.WeakKeyDictionary()


class _PromptTranslationWorker:
    """Own one lazy worker and never queue behind a timed-out sync call."""

    def __init__(self):
        self._lock = threading.RLock()
        self._executor: ThreadPoolExecutor | None = None
        self._in_flight: Future | None = None
        self._closed = False

    @property
    def has_in_flight(self) -> bool:
        with self._lock:
            return self._in_flight is not None and not self._in_flight.done()

    def submit(self, function, *args) -> Future:
        with self._lock:
            if self._closed:
                raise RuntimeError("Prompt translation worker is shut down.")
            if self._in_flight is not None and not self._in_flight.done():
                raise TranslationBusyError()
            if self._executor is None:
                self._executor = ThreadPoolExecutor(
                    max_workers=1,
                    thread_name_prefix="easyuse-anima-translation",
                )
            future = self._executor.submit(function, *args)
            self._in_flight = future
        future.add_done_callback(self._release)
        return future

    def _release(self, future: Future) -> None:
        with self._lock:
            if self._in_flight is future:
                self._in_flight = None

    def shutdown(self) -> None:
        with self._lock:
            if self._closed:
                return
            self._closed = True
            executor = self._executor
            self._executor = None
        if executor is not None:
            executor.shutdown(wait=False, cancel_futures=True)


_PROMPT_TRANSLATION_WORKER = _PromptTranslationWorker()
atexit.register(_PROMPT_TRANSLATION_WORKER.shutdown)


def _translate_prompt_sync(text: str) -> str:
    return translate_prompt_markers(text, resolve_prompt_translation_settings())


async def _translate_prompt_for_route(text: str) -> str:
    future = _PROMPT_TRANSLATION_WORKER.submit(_translate_prompt_sync, text)
    wrapped_future = asyncio.wrap_future(future)
    try:
        done, _pending = await asyncio.wait(
            (wrapped_future,),
            timeout=PROMPT_TRANSLATION_ROUTE_TIMEOUT_SECONDS,
        )
    except asyncio.CancelledError as exc:
        # Waiting stops immediately, while admission remains occupied until the
        # bounded sync worker really exits.
        wrapped_future.cancel()
        raise TranslationCancelledError() from exc
    if not done:
        wrapped_future.cancel()
        raise TranslationTimeoutError()
    return wrapped_future.result()


def _prompt_translation_error_response(exc: PromptTranslationError):
    return web.json_response(
        {
            "status": "error",
            "code": exc.code,
            "message": exc.message,
        },
        status=exc.status,
    )


def _error_response(
    status: int,
    code: str,
    message: str,
    *,
    details: dict | None = None,
):
    return web.json_response(
        error_payload(code, message, details=details),
        status=status,
    )


def _contract_error_response(exc: ApiContractError):
    return _error_response(
        exc.status,
        exc.code,
        exc.message,
        details=exc.details,
    )


def _file_io_limiter() -> asyncio.Semaphore:
    loop = asyncio.get_running_loop()
    with _FILE_IO_LIMITERS_LOCK:
        limiter_ref = _FILE_IO_LIMITERS.get(loop)
        limiter = limiter_ref() if limiter_ref is not None else None
        if limiter is None:
            limiter = asyncio.Semaphore(FILE_IO_MAX_IN_FLIGHT)
            # A contended Semaphore binds itself to the event loop. Store only
            # a weak value so the registry cannot root a closed loop through
            # registry -> semaphore -> loop. Active/waiting calls and worker
            # callbacks keep their limiter alive until the real work finishes.
            _FILE_IO_LIMITERS[loop] = weakref.ref(limiter)
        return limiter


def _release_file_io_slot(limiter: asyncio.Semaphore, worker: asyncio.Task) -> None:
    limiter.release()
    if worker.cancelled():
        return
    # Retrieve failures even when the request that submitted the worker was
    # cancelled. A live caller still receives the same exception from await.
    worker.exception()


async def _run_file_io(function, /, *args, **kwargs):
    limiter = _file_io_limiter()
    await limiter.acquire()
    worker = asyncio.create_task(asyncio.to_thread(function, *args, **kwargs))
    worker.add_done_callback(
        lambda completed, owned_limiter=limiter: _release_file_io_slot(
            owned_limiter,
            completed,
        )
    )
    return await asyncio.shield(worker)


def _windows_profile_filename_identity(name: str) -> str:
    return str(name or "").rstrip(" .").casefold()


def _sanitize_profile_name(name: str) -> str:
    safe_name = INVALID_PROFILE_NAME_CHARS.sub("_", str(name or "")).strip(" ._")
    if not safe_name:
        raise ValueError("Profile name is required")
    safe_name = safe_name[:80].rstrip(" .")
    if not safe_name:
        raise ValueError("Profile name is required")
    windows_basename = safe_name.split(".", 1)[0].casefold()
    if windows_basename in WINDOWS_RESERVED_FILE_BASENAMES:
        raise ValueError("Profile name is reserved on Windows")
    return safe_name


def _sanitize_lora_profile_name(name: str) -> str:
    return _sanitize_profile_name(name)


def _lora_profile_path(name: str, profile_dir: Path | None = None) -> Path:
    safe_name = _sanitize_lora_profile_name(name)
    root = (profile_dir or LORA_PROFILE_DIR).resolve()
    path = (root / f"{safe_name}.json").resolve()
    if os.path.commonpath((str(root), str(path))) != str(root):
        raise ValueError("Invalid profile path")
    return path


def _find_lora_profile_path(name: str, profile_dir: Path | None = None) -> Path | None:
    safe_name = _sanitize_lora_profile_name(name)
    root = profile_dir or LORA_PROFILE_DIR
    if not root.is_dir():
        return None
    expected = _windows_profile_filename_identity(safe_name)
    return next(
        (
            path
            for path in sorted(root.glob("*.json"), key=lambda item: (item.name.casefold(), item.name))
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
        "profile_index": _as_lora_profile_index(data.get("profile_index", 1), count),
        "profile_data": _normalize_lora_profile_data(data.get("profile_data", {})),
    }


def _list_lora_profiles() -> list[dict]:
    if not LORA_PROFILE_DIR.is_dir():
        return []
    profiles = []
    for path in sorted(LORA_PROFILE_DIR.glob("*.json"), key=lambda item: item.stem.lower()):
        if path.name == ".gitignore":
            continue
        profiles.append(
            {
                "name": path.stem,
                "modified": int(path.stat().st_mtime),
            }
        )
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
    candidates = _dedupe_text_values((
        text,
        text.replace("\\", "/"),
        text.replace("/", os.sep),
    ))
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


def _apply_lora_fix(next_lora: dict, profile_key: str, raw_name: str, match: str, reason: str, fixed: list):
    changed = raw_name != match
    next_lora["name"] = match
    next_lora.pop("lora", None)
    if changed:
        fixed.append({
            "profile": profile_key,
            "from": raw_name,
            "to": match,
            "reason": reason,
        })


def _fix_lora_profile_payload(data: dict) -> dict:
    payload = _normalize_lora_profile_payload(data if isinstance(data, dict) else {})
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
            raw_name = str(next_lora.get("name", next_lora.get("lora", "")) or "").strip()
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
                _apply_lora_fix(next_lora, profile_key, raw_name, match, reason, fixed)
            else:
                unresolved.append({"profile": profile_key, "name": raw_name})

    payload["fixed"] = fixed
    payload["unresolved"] = unresolved
    payload["checked"] = sum(len(profile.get("loras") or []) for profile in payload["profile_data"].values() if isinstance(profile, dict))
    payload["missing"] = len(missing_entries)
    return payload


def _read_profile_json(path: Path):
    store = AtomicJsonStore(path)
    with store.locked():
        try:
            return store.read()
        except json.JSONDecodeError:
            if path.read_text(encoding="utf-8") == "":
                return {}
            raise


def _save_lora_profile(name: str, data: dict, *, overwrite: bool = False) -> dict:
    safe_name = _sanitize_lora_profile_name(name)
    payload = _normalize_lora_profile_payload(data)
    LORA_PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    requested_path = _lora_profile_path(safe_name)
    with AtomicJsonStore(requested_path).locked():
        existing = _find_lora_profile_path(safe_name)
        if existing is not None and not overwrite:
            raise FileExistsError("Profile already exists")
        path = existing or requested_path
        payload["name"] = path.stem
        AtomicJsonStore(path).write(payload)
    return payload


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
    payload["name"] = path.stem
    return payload


def _sanitize_aio_profile_name(name: str) -> str:
    safe_name = _sanitize_profile_name(name)
    if safe_name.casefold() in {item.casefold() for item in AIO_RESERVED_PROFILE_NAMES}:
        raise ValueError("System profile names are reserved")
    return safe_name


def _aio_profile_path(name: str, profile_dir: Path | None = None) -> Path:
    safe_name = _sanitize_aio_profile_name(name)
    root = (profile_dir or AIO_PROFILE_DIR).resolve()
    path = (root / f"{safe_name}.json").resolve()
    if os.path.commonpath((str(root), str(path))) != str(root):
        raise ValueError("Invalid profile path")
    return path


def _find_aio_profile_path(name: str, profile_dir: Path | None = None) -> Path | None:
    safe_name = _sanitize_aio_profile_name(name)
    root = profile_dir or AIO_PROFILE_DIR
    if not root.is_dir():
        return None
    expected = _windows_profile_filename_identity(safe_name)
    return next(
        (
            path
            for path in sorted(root.glob("*.json"), key=lambda item: (item.name.casefold(), item.name))
            if _windows_profile_filename_identity(path.stem) == expected
        ),
        None,
    )


def _normalize_aio_profile_payload(name: str, data: dict) -> dict:
    safe_name = _sanitize_aio_profile_name(name)
    settings = data.get("settings") if isinstance(data, dict) else None
    if not isinstance(settings, dict):
        raise ValueError("Profile settings must be an object")
    payload = {
        "version": 1,
        "name": safe_name,
        "settings": settings,
    }
    encoded = json.dumps(payload, ensure_ascii=False, indent=2)
    if len(encoded.encode("utf-8")) > MAX_AIO_PROFILE_BYTES:
        raise ValueError("Profile settings are too large")
    return payload


def _list_aio_profiles(profile_dir: Path | None = None) -> list[dict]:
    root = profile_dir or AIO_PROFILE_DIR
    if not root.is_dir():
        return []
    return [
        {
            "name": path.stem,
            "modified": int(path.stat().st_mtime),
        }
        for path in sorted(root.glob("*.json"), key=lambda item: item.stem.casefold())
    ]


def _save_aio_profile(name: str, data: dict, *, overwrite: bool = False) -> dict:
    payload = _normalize_aio_profile_payload(name, data)
    AIO_PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    requested_path = _aio_profile_path(payload["name"])
    with AtomicJsonStore(requested_path).locked():
        existing = _find_aio_profile_path(payload["name"])
        if existing is not None and not overwrite:
            raise FileExistsError("Profile already exists")
        if existing is None and len(_list_aio_profiles()) >= MAX_AIO_PROFILES:
            raise ValueError(f"A maximum of {MAX_AIO_PROFILES} profiles can be saved")
        path = existing or requested_path
        payload["name"] = path.stem
        AtomicJsonStore(path).write(payload)
    return payload


def _normalize_stored_aio_profile_payload(name: str, data) -> dict:
    if not isinstance(data, dict):
        raise InvalidProfileDataError("Profile data is invalid")
    try:
        return _normalize_aio_profile_payload(name, data)
    except ValueError as exc:
        raise InvalidProfileDataError(str(exc)) from exc


def _load_aio_profile(name: str) -> dict:
    path = _find_aio_profile_path(name)
    if path is None or not path.is_file():
        raise FileNotFoundError("Profile not found")
    try:
        data = _read_profile_json(path)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise InvalidProfileDataError("Profile data is invalid") from exc
    return _normalize_stored_aio_profile_payload(path.stem, data)


def _delete_aio_profile(name: str) -> dict:
    path = _find_aio_profile_path(name)
    if path is None or not path.is_file():
        raise FileNotFoundError("Profile not found")
    deleted_name = path.stem
    try:
        AtomicJsonStore(path).delete()
    except FileNotFoundError as exc:
        raise FileNotFoundError("Profile not found") from exc
    return {"name": deleted_name}


def _rename_aio_profile(old_name: str, new_name: str, *, overwrite: bool = False) -> dict:
    source = _find_aio_profile_path(old_name)
    if source is None or not source.is_file():
        raise FileNotFoundError("Profile not found")
    safe_new_name = _sanitize_aio_profile_name(new_name)
    if source.stem.casefold() == safe_new_name.casefold():
        return _load_aio_profile(source.stem)

    target = _find_aio_profile_path(safe_new_name)
    if target is not None and not overwrite:
        raise FileExistsError("Profile already exists")

    target_path = target or _aio_profile_path(safe_new_name)
    return AtomicJsonStore(target_path).replace_from(
        AtomicJsonStore(source),
        overwrite=overwrite,
        backup_target=True,
        transform=lambda data: _normalize_stored_aio_profile_payload(
            target_path.stem,
            data,
        ),
    )


def _resolve_lora_preview_path(lora_name: str):
    try:
        import folder_paths  # type: ignore
    except Exception:
        return None

    name = str(lora_name or "").strip()
    if not name or name == "None":
        return None
    lora_path = folder_paths.get_full_path("loras", name)
    if not lora_path:
        return None

    lora_abs = os.path.abspath(lora_path)
    lora_dir = os.path.dirname(lora_abs)
    preview_base = os.path.splitext(lora_abs)[0]
    for extension in LORA_PREVIEW_EXTENSIONS:
        preview_abs = os.path.abspath(preview_base + extension)
        try:
            if os.path.commonpath((lora_dir, preview_abs)) != lora_dir:
                continue
        except ValueError:
            continue
        if os.path.isfile(preview_abs):
            return preview_abs
    return None


_SAFE_PROFILE_VALIDATION_MESSAGES = frozenset(
    {
        "Profile name is required",
        "Profile name is reserved on Windows",
        "Invalid profile path",
        "System profile names are reserved",
        "Profile settings must be an object",
        "Profile settings are too large",
        f"A maximum of {MAX_AIO_PROFILES} profiles can be saved",
    }
)


def _profile_error_response(exc: Exception):
    if isinstance(exc, FileExistsError):
        return _error_response(409, "profile_exists", "Profile already exists")
    if isinstance(exc, FileNotFoundError):
        return _error_response(404, "profile_not_found", "Profile not found")
    if isinstance(
        exc,
        (json.JSONDecodeError, UnicodeDecodeError, InvalidProfileDataError),
    ):
        return _error_response(422, "invalid_profile_data", "Profile data is invalid")
    if isinstance(exc, ValueError):
        message = str(exc)
        if message not in _SAFE_PROFILE_VALIDATION_MESSAGES:
            message = "Request validation failed"
        return _error_response(422, "invalid_request", message)
    raise exc


def _get_settings_payload_sync() -> dict:
    return public_settings()


def _save_setting_payload_sync(key: str, value) -> dict:
    save_setting(key, value)
    return {"status": "ok", **public_settings()}


def _get_long_text_settings_payload_sync() -> dict:
    return {
        "status": "ok",
        "values": load_long_text_settings(),
        "settings": public_settings(),
    }


def _save_long_text_settings_payload_sync(values: dict) -> dict:
    return {
        "status": "ok",
        "values": save_long_text_settings(values),
        "settings": public_settings(),
    }


def _wildcards_payload_sync() -> dict:
    settings = public_settings()
    extra_paths = settings.get("wildcard.extra_paths", "")
    roots = resolve_wildcard_roots(extra_paths)
    sources = [
        {
            "id": f"wildcard:{index}",
            "label": f"Wildcard source {index}",
            "exists": root.is_dir(),
        }
        for index, root in enumerate(roots, start=1)
    ]
    return {
        "status": "ok",
        "items": list_wildcards(roots=roots),
        # Preserve the legacy list-of-strings type without publishing paths.
        "roots": [source["id"] for source in sources],
        "sources": sources,
    }


def _autocomplete_status_payload_sync() -> dict:
    selected_source = resolve_autocomplete_source()
    source_key, path = resolve_autocomplete_source_path(selected_source)
    status = _public_autocomplete_status(autocomplete_status(path))
    sources = []
    source_label = source_key
    for source in available_autocomplete_sources(source_key):
        public_source = {
            key: value
            for key, value in source.items()
            if key != "path"
        }
        sources.append(public_source)
        if public_source.get("selected"):
            source_label = str(public_source.get("label") or source_key)
    return {
        **status,
        "source": source_key,
        "source_label": source_label,
        "sources": sources,
    }


def _public_autocomplete_status(status) -> dict:
    public_status = dict(status) if isinstance(status, dict) else {}
    public_status.pop("path", None)
    return public_status


def _public_autocomplete_payload(payload) -> dict:
    public_payload = dict(payload) if isinstance(payload, dict) else {}
    if "status" in public_payload:
        public_payload["status"] = _public_autocomplete_status(
            public_payload["status"]
        )
    return public_payload


def _search_autocomplete_payload_sync(
    query: str,
    requested_limit: str | None,
    category_filter: str | None,
):
    default_limit = resolve_autocomplete_limit()
    try:
        limit = int(requested_limit) if requested_limit is not None else default_limit
    except ValueError:
        limit = default_limit
    _, path = resolve_autocomplete_source_path(resolve_autocomplete_source())
    return _public_autocomplete_payload(
        search_autocomplete(
            query,
            limit=limit,
            path=path,
            category=category_filter,
        )
    )


def _classify_prompt_payload_sync(text: str, limit: int):
    _, path = resolve_autocomplete_source_path(resolve_autocomplete_source())
    return _public_autocomplete_payload(
        classify_prompt_text(text, limit=limit, path=path)
    )


def _get_prompt_routes():
    if server is None:
        return None
    prompt_server = getattr(getattr(server, "PromptServer", None), "instance", None)
    return getattr(prompt_server, "routes", None)


routes = _get_prompt_routes()


if web is not None and routes is not None:

    @routes.get("/easyuse_anima/settings")
    async def get_settings_handler(request):
        return web.json_response(await _run_file_io(_get_settings_payload_sync))

    @routes.post("/easyuse_anima/set_setting")
    async def set_setting_handler(request):
        try:
            data = await parse_json_object(request)
            key = json_string(data, "key", allow_empty=False)
        except ApiContractError as exc:
            return _contract_error_response(exc)
        try:
            payload = await _run_file_io(
                _save_setting_payload_sync,
                key,
                data.get("value", ""),
            )
        except KeyError:
            return _error_response(422, "unknown_setting", "Unknown setting")
        return web.json_response(payload)

    @routes.get("/easyuse_anima/long_text_settings")
    async def get_long_text_settings_handler(request):
        return web.json_response(
            await _run_file_io(_get_long_text_settings_payload_sync)
        )

    @routes.get("/easyuse_anima/wildcards")
    async def get_wildcards_handler(request):
        return web.json_response(await _run_file_io(_wildcards_payload_sync))

    @routes.post("/easyuse_anima/long_text_settings/save")
    async def save_long_text_settings_handler(request):
        try:
            data = await parse_json_object(request)
            values = json_object(data, "values") if "values" in data else data
        except ApiContractError as exc:
            return _contract_error_response(exc)
        return web.json_response(
            await _run_file_io(_save_long_text_settings_payload_sync, values)
        )

    @routes.get("/easyuse_anima/autocomplete_status")
    async def autocomplete_status_handler(request):
        return web.json_response(await _run_file_io(_autocomplete_status_payload_sync))

    @routes.get("/easyuse_anima/autocomplete")
    async def autocomplete_handler(request):
        query = request.query.get("q", "")
        category = request.query.get("category", "")
        category_filter = {
            "artist": "artist",
            "artist_or_general": "artist,general",
        }.get(category)
        return web.json_response(
            await _run_file_io(
                _search_autocomplete_payload_sync,
                query,
                request.query.get("limit"),
                category_filter,
            )
        )

    @routes.post("/easyuse_anima/classify_prompt")
    async def classify_prompt_handler(request):
        try:
            data = await parse_json_object(request)
            text = json_string(data, "text")
            limit = json_integer(
                data,
                "limit",
                default=240,
                minimum=1,
                maximum=500,
            )
        except ApiContractError as exc:
            return _contract_error_response(exc)
        return web.json_response(
            await _run_file_io(_classify_prompt_payload_sync, text, limit)
        )

    @routes.post("/easyuse_anima/translate_prompt")
    async def translate_prompt_handler(request):
        try:
            data = await parse_json_object(request)
            text = json_string(data, "text")
        except ApiContractError as exc:
            return _contract_error_response(exc)
        try:
            translated = await _translate_prompt_for_route(text)
        except PromptTranslationError as exc:
            return _prompt_translation_error_response(exc)
        return web.json_response({"status": "ok", "text": translated})

    @routes.get("/easyuse_anima/lora_preview")
    async def lora_preview_handler(request):
        preview_path = await _run_file_io(
            _resolve_lora_preview_path,
            request.query.get("name", ""),
        )
        if not preview_path:
            return web.Response(status=404)
        return web.FileResponse(
            preview_path,
            headers={"Content-Disposition": f'filename="{os.path.basename(preview_path)}"'},
        )

    @routes.get("/easyuse_anima/loras")
    async def loras_handler(request):
        return web.json_response({"loras": await _run_file_io(_list_loras)})

    @routes.get("/easyuse_anima/lora_profiles")
    async def lora_profiles_handler(request):
        return web.json_response({"profiles": await _run_file_io(_list_lora_profiles)})

    @routes.post("/easyuse_anima/lora_profiles/save")
    async def save_lora_profile_handler(request):
        try:
            data = await parse_json_object(request)
            name = json_string(data, "name", allow_empty=False)
            overwrite = json_boolean(data, "overwrite")
            if "profile_data" in data:
                json_object(data, "profile_data")
        except ApiContractError as exc:
            return _contract_error_response(exc)
        try:
            payload = await _run_file_io(
                _save_lora_profile,
                name,
                data,
                overwrite=overwrite,
            )
        except (FileExistsError, ValueError) as exc:
            return _profile_error_response(exc)
        return web.json_response({"status": "ok", "profile": payload})

    @routes.get("/easyuse_anima/lora_profiles/load")
    async def load_lora_profile_handler(request):
        try:
            payload = await _run_file_io(
                _load_lora_profile,
                request.query.get("name", ""),
            )
        except (
            json.JSONDecodeError,
            UnicodeDecodeError,
            FileNotFoundError,
            ValueError,
        ) as exc:
            return _profile_error_response(exc)
        return web.json_response({"status": "ok", "profile": payload})

    @routes.get("/easyuse_anima/aio_profiles")
    async def aio_profiles_handler(request):
        return web.json_response(
            {"status": "ok", "profiles": await _run_file_io(_list_aio_profiles)}
        )

    @routes.post("/easyuse_anima/aio_profiles/save")
    async def save_aio_profile_handler(request):
        try:
            data = await parse_json_object(request)
            name = json_string(data, "name", allow_empty=False)
            json_object(data, "settings")
            overwrite = json_boolean(data, "overwrite")
        except ApiContractError as exc:
            return _contract_error_response(exc)
        try:
            payload = await _run_file_io(
                _save_aio_profile,
                name,
                data,
                overwrite=overwrite,
            )
        except (FileExistsError, ValueError) as exc:
            return _profile_error_response(exc)
        return web.json_response({"status": "ok", "profile": payload})

    @routes.get("/easyuse_anima/aio_profiles/load")
    async def load_aio_profile_handler(request):
        try:
            payload = await _run_file_io(
                _load_aio_profile,
                request.query.get("name", ""),
            )
        except (FileNotFoundError, ValueError) as exc:
            return _profile_error_response(exc)
        return web.json_response({"status": "ok", "profile": payload})

    @routes.post("/easyuse_anima/aio_profiles/delete")
    async def delete_aio_profile_handler(request):
        try:
            data = await parse_json_object(request)
            name = json_string(data, "name", allow_empty=False)
        except ApiContractError as exc:
            return _contract_error_response(exc)
        try:
            payload = await _run_file_io(_delete_aio_profile, name)
        except (FileNotFoundError, ValueError) as exc:
            return _profile_error_response(exc)
        return web.json_response({"status": "ok", "profile": payload})

    @routes.post("/easyuse_anima/aio_profiles/rename")
    async def rename_aio_profile_handler(request):
        try:
            data = await parse_json_object(request)
            old_name = json_string(data, "old_name", allow_empty=False)
            new_name = json_string(data, "new_name", allow_empty=False)
            overwrite = json_boolean(data, "overwrite")
        except ApiContractError as exc:
            return _contract_error_response(exc)
        try:
            payload = await _run_file_io(
                _rename_aio_profile,
                old_name,
                new_name,
                overwrite=overwrite,
            )
        except (FileExistsError, FileNotFoundError, ValueError) as exc:
            return _profile_error_response(exc)
        return web.json_response({"status": "ok", "profile": payload})

    @routes.post("/easyuse_anima/lora_profiles/fix")
    async def fix_lora_profile_handler(request):
        try:
            data = await parse_json_object(request)
            if "profile_data" in data:
                json_object(data, "profile_data")
        except ApiContractError as exc:
            return _contract_error_response(exc)
        payload = await _run_file_io(_fix_lora_profile_payload, data)
        return web.json_response({"status": "ok", "profile": payload})
