from __future__ import annotations

import atexit
import asyncio
import json
import logging
import os
import threading
import weakref
from functools import wraps

try:
    import server
    from aiohttp import web
except ImportError:
    server = None
    web = None

from .easyuse_anima.settings.repository import (
    load_long_text_settings,
    save_long_text_settings,
    save_setting,
)
from .easyuse_anima.settings.service import (
    public_settings,
    resolve_autocomplete_limit,
    resolve_autocomplete_source,
    resolve_prompt_translation_settings,
)
from .easyuse_anima.autocomplete.dataset import (
    autocomplete_status,
    available_autocomplete_sources,
    resolve_autocomplete_source as resolve_autocomplete_source_path,
)
from .easyuse_anima.autocomplete.search import (
    search_autocomplete,
)
from .easyuse_anima.autocomplete.classification import classify_prompt_text
from .easyuse_anima.wildcard.sources import resolve_wildcard_roots
from .wildcard_engine import list_wildcards
from .easyuse_anima.translation.contracts import (
    PromptTranslationError,
    TranslationBusyError,
    TranslationCancelledError,
    TranslationTimeoutError,
)
from .easyuse_anima.translation.service import (
    translate_prompt_markers,
)
from .easyuse_anima.api.errors import ApiContractError
from .easyuse_anima.api.requests import (
    json_boolean,
    json_integer,
    json_object,
    json_string,
    json_uuid_string,
    parse_json_object,
)
from .easyuse_anima.api.responses import (
    attach_request_id_header,
    correlate_response,
    create_request_id,
    error_payload,
)
from .easyuse_anima.api.routes.autocomplete import (
    build_autocomplete_handlers as _build_autocomplete_handlers,
    build_classify_prompt_handler as _build_classify_prompt_handler,
)
from .easyuse_anima.api.routes.long_text_settings import (
    build_long_text_settings_handlers as _build_long_text_settings_handlers,
)
from .easyuse_anima.api.routes.lora_catalog import (
    build_loras_handler as _build_loras_handler,
)
from .easyuse_anima.api.routes.lora_preview import (
    build_lora_preview_handler as _build_lora_preview_handler,
)
from .easyuse_anima.api.routes.wildcards import (
    build_wildcards_handler as _build_wildcards_handler,
)
from .easyuse_anima.api.routes.translation import (
    build_translate_prompt_handler as _build_translate_prompt_handler,
)
from .easyuse_anima.api.routes.translation_execution import (
    PromptTranslationRouteExecutor as _PromptTranslationRouteExecutor,
)
from .easyuse_anima.api.routes.aio_torch_compile import (
    build_aio_torch_compile_recommend_handler as _build_aio_torch_compile_recommend_handler,
)
from .easyuse_anima.aio.torch_compile_diagnostics import (
    collect_torch_compile_diagnostics as _collect_torch_compile_diagnostics,
)
from .easyuse_anima.aio.torch_compile_recommendation import (
    recommend_torch_compile as _recommend_torch_compile,
)
from .easyuse_anima.profiles import aio as _aio_profiles
from .easyuse_anima.profiles import contract as _profile_contract
from .easyuse_anima.profiles import lora as _lora_profiles
from .easyuse_anima.profiles import mutation as _profile_mutation
from .easyuse_anima.profiles import repository as _profile_repository

PROFILE_KIND_AIO = _profile_contract.PROFILE_KIND_AIO
PROFILE_KIND_LORA = _profile_contract.PROFILE_KIND_LORA
ProfileContractError = _profile_contract.ProfileContractError
build_profile_document = _profile_contract.build_profile_document
create_profile_document = _profile_contract.create_profile_document
interpret_profile_document = _profile_contract.interpret_profile_document
legacy_profile_id = _profile_contract.legacy_profile_id
normalize_profile_filename_identity = (
    _profile_contract.normalize_profile_filename_identity
)
rename_profile_document = _profile_contract.rename_profile_document
update_profile_document = _profile_contract.update_profile_document

PROFILE_MUTATION_COORDINATOR = _profile_mutation.PROFILE_MUTATION_COORDINATOR
ProfileMutationError = _profile_mutation.ProfileMutationError
ProfileRevisionConflictError = _profile_mutation.ProfileRevisionConflictError
require_profile_precondition = _profile_mutation.require_profile_precondition
verify_profile_precondition = _profile_mutation.verify_profile_precondition

INVALID_PROFILE_NAME_CHARS = _profile_repository.INVALID_PROFILE_NAME_CHARS
WINDOWS_RESERVED_FILE_BASENAMES = (
    _profile_repository.WINDOWS_RESERVED_FILE_BASENAMES
)
InvalidProfileDataError = _profile_repository.InvalidProfileDataError
_windows_profile_filename_identity = (
    _profile_repository._windows_profile_filename_identity
)
_sanitize_profile_name = _profile_repository._sanitize_profile_name
_read_profile_json = _profile_repository._read_profile_json
_profile_list_item = _profile_repository._profile_list_item

LORA_PROFILE_DIR = _lora_profiles.LORA_PROFILE_DIR
MAX_LORA_PROFILES = _lora_profiles.MAX_LORA_PROFILES
_sanitize_lora_profile_name = _lora_profiles._sanitize_lora_profile_name
_lora_profile_path = _lora_profiles._lora_profile_path
_find_lora_profile_path = _lora_profiles._find_lora_profile_path
_as_lora_profile_count = _lora_profiles._as_lora_profile_count
_as_lora_profile_index = _lora_profiles._as_lora_profile_index
_normalize_lora_profile_data = _lora_profiles._normalize_lora_profile_data
_normalize_lora_profile_payload = _lora_profiles._normalize_lora_profile_payload
_list_lora_profiles = _lora_profiles._list_lora_profiles
_clear_folder_paths_cache = _lora_profiles._clear_folder_paths_cache
_list_loras = _lora_profiles._list_loras
_lora_full_path = _lora_profiles._lora_full_path
_dedupe_text_values = _lora_profiles._dedupe_text_values
_lora_file_key = _lora_profiles._lora_file_key
_put_unique = _lora_profiles._put_unique
_lora_path_exists = _lora_profiles._lora_path_exists
_build_lora_fix_index = _lora_profiles._build_lora_fix_index
_resolve_lora_for_fix = _lora_profiles._resolve_lora_for_fix
_apply_lora_fix = _lora_profiles._apply_lora_fix
_fix_lora_profile_payload = _lora_profiles._fix_lora_profile_payload
_save_lora_profile = _lora_profiles._save_lora_profile
_load_lora_profile = _lora_profiles._load_lora_profile

AIO_PROFILE_DIR = _aio_profiles.AIO_PROFILE_DIR
MAX_AIO_PROFILES = _aio_profiles.MAX_AIO_PROFILES
MAX_AIO_PROFILE_BYTES = _aio_profiles.MAX_AIO_PROFILE_BYTES
AIO_RESERVED_PROFILE_NAMES = _aio_profiles.AIO_RESERVED_PROFILE_NAMES
_sanitize_aio_profile_name = _aio_profiles._sanitize_aio_profile_name
_aio_profile_path = _aio_profiles._aio_profile_path
_find_aio_profile_path = _aio_profiles._find_aio_profile_path
_normalize_aio_profile_payload = _aio_profiles._normalize_aio_profile_payload
_list_aio_profiles = _aio_profiles._list_aio_profiles
_validate_aio_profile_size = _aio_profiles._validate_aio_profile_size
_save_aio_profile = _aio_profiles._save_aio_profile
_normalize_stored_aio_profile_payload = (
    _aio_profiles._normalize_stored_aio_profile_payload
)
_load_aio_profile = _aio_profiles._load_aio_profile
_delete_aio_profile = _aio_profiles._delete_aio_profile
_rename_aio_profile = _aio_profiles._rename_aio_profile
_rename_aio_profile_payload = _aio_profiles._rename_aio_profile_payload


LORA_PREVIEW_EXTENSIONS = (".webp", ".png", ".jpg", ".jpeg")
PROMPT_TRANSLATION_ROUTE_TIMEOUT_SECONDS = 15.0
FILE_IO_MAX_IN_FLIGHT = 4
_LOGGER = logging.getLogger(__name__)


_FILE_IO_LIMITERS_LOCK = threading.Lock()
_FILE_IO_LIMITERS: weakref.WeakKeyDictionary = weakref.WeakKeyDictionary()


_PROMPT_TRANSLATION_WORKER = _PromptTranslationRouteExecutor(
    busy_error_type=TranslationBusyError,
    cancelled_error_type=TranslationCancelledError,
    timeout_error_type=TranslationTimeoutError,
)
atexit.register(_PROMPT_TRANSLATION_WORKER.shutdown)


def _translate_prompt_sync(text: str) -> str:
    return translate_prompt_markers(text, resolve_prompt_translation_settings())


async def _translate_prompt_for_route(text: str) -> str:
    return await _PROMPT_TRANSLATION_WORKER.execute(
        _translate_prompt_sync,
        text,
        timeout_seconds=PROMPT_TRANSLATION_ROUTE_TIMEOUT_SECONDS,
    )


def _prompt_translation_error_response(exc: PromptTranslationError):
    return _error_response(
        exc.status,
        exc.code,
        exc.message,
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


def _request_correlated(handler):
    @wraps(handler)
    async def correlated_handler(request):
        request_id = create_request_id()
        try:
            response = await handler(request)
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            http_exception_type = getattr(web, "HTTPException", ())
            if isinstance(exc, http_exception_type):
                attach_request_id_header(exc, request_id)
                raise
            _LOGGER.exception(
                "Unhandled EasyUseAnima API error (request_id=%s)",
                request_id,
            )
            response = _error_response(
                500,
                "internal_error",
                "An unexpected server error occurred.",
            )
        return correlate_response(response, request_id)

    correlated_handler._easyuse_anima_request_correlation = True
    return correlated_handler


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
    if isinstance(exc, ProfileMutationError):
        return _error_response(
            exc.status,
            exc.code,
            exc.message,
            details=exc.details,
        )
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


if web is not None:

    @_request_correlated
    async def get_settings_handler(request):
        return web.json_response(await _run_file_io(_get_settings_payload_sync))

    @_request_correlated
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

    (
        get_long_text_settings_handler,
        save_long_text_settings_handler,
    ) = (
        _request_correlated(handler)
        for handler in _build_long_text_settings_handlers(
            parse_json_object=lambda request: parse_json_object(request),
            json_object=lambda data, field: json_object(data, field),
            contract_error_type=ApiContractError,
            contract_error_response=lambda exc: _contract_error_response(exc),
            run_file_io=lambda function, *args: _run_file_io(function, *args),
            get_long_text_settings_payload=lambda: _get_long_text_settings_payload_sync(),
            save_long_text_settings_payload=lambda values: _save_long_text_settings_payload_sync(
                values
            ),
            json_response=lambda payload: web.json_response(payload),
        )
    )

    get_wildcards_handler = _request_correlated(
        _build_wildcards_handler(
            run_file_io=lambda function, *args: _run_file_io(function, *args),
            wildcards_payload=lambda: _wildcards_payload_sync(),
            json_response=lambda payload: web.json_response(payload),
        )
    )

    (
        autocomplete_status_handler,
        autocomplete_handler,
    ) = (
        _request_correlated(handler)
        for handler in _build_autocomplete_handlers(
            run_file_io=lambda function, *args: _run_file_io(function, *args),
            autocomplete_status_payload=lambda: _autocomplete_status_payload_sync(),
            search_autocomplete_payload=lambda *args: _search_autocomplete_payload_sync(
                *args
            ),
            json_response=lambda payload: web.json_response(payload),
        )
    )

    classify_prompt_handler = _request_correlated(
        _build_classify_prompt_handler(
            parse_json_object=lambda request: parse_json_object(request),
            json_string=lambda data, field: json_string(data, field),
            json_integer=lambda data, field, **kwargs: json_integer(
                data,
                field,
                **kwargs,
            ),
            contract_error_type=ApiContractError,
            contract_error_response=lambda exc: _contract_error_response(exc),
            run_file_io=lambda function, *args: _run_file_io(function, *args),
            classify_prompt_payload=lambda *args: _classify_prompt_payload_sync(
                *args
            ),
            json_response=lambda payload: web.json_response(payload),
        )
    )

    translate_prompt_handler = _request_correlated(
        _build_translate_prompt_handler(
            parse_json_object=lambda request: parse_json_object(request),
            json_string=lambda data, field: json_string(data, field),
            contract_error_type=ApiContractError,
            contract_error_response=lambda exc: _contract_error_response(exc),
            translate_prompt=lambda text: _translate_prompt_for_route(text),
            translation_error_type=PromptTranslationError,
            translation_error_response=lambda exc: _prompt_translation_error_response(exc),
            json_response=lambda payload: web.json_response(payload),
        )
    )

    aio_torch_compile_recommend_handler = _request_correlated(
        _build_aio_torch_compile_recommend_handler(
            parse_json_object=lambda request: parse_json_object(request),
            json_object=lambda data, field: json_object(data, field),
            json_integer=lambda data, field, **kwargs: json_integer(
                data,
                field,
                **kwargs,
            ),
            contract_error_type=ApiContractError,
            contract_error_response=lambda exc: _contract_error_response(exc),
            collect_diagnostics=lambda: _collect_torch_compile_diagnostics(),
            recommend_torch_compile=lambda *args: _recommend_torch_compile(*args),
            json_response=lambda payload: web.json_response(payload),
        )
    )

    lora_preview_handler = _request_correlated(
        _build_lora_preview_handler(
            run_file_io=lambda function, *args: _run_file_io(function, *args),
            resolve_lora_preview_path=lambda name: _resolve_lora_preview_path(name),
            empty_response=lambda **kwargs: web.Response(**kwargs),
            file_response=lambda path, **kwargs: web.FileResponse(path, **kwargs),
            basename=lambda path: os.path.basename(path),
        )
    )

    loras_handler = _request_correlated(
        _build_loras_handler(
            run_file_io=lambda function, *args: _run_file_io(function, *args),
            list_loras=lambda: _list_loras(),
            json_response=lambda payload: web.json_response(payload),
        )
    )

    @_request_correlated
    async def lora_profiles_handler(request):
        try:
            payload = await _run_file_io(_list_lora_profiles)
        except InvalidProfileDataError as exc:
            return _profile_error_response(exc)
        return web.json_response({"profiles": payload})

    @_request_correlated
    async def save_lora_profile_handler(request):
        try:
            data = await parse_json_object(request)
            name = json_string(data, "name", allow_empty=False)
            overwrite = json_boolean(data, "overwrite")
            if "profile_data" in data:
                json_object(data, "profile_data")
            profile_id = json_uuid_string(
                data,
                "profile_id",
                required=False,
            )
            revision = json_integer(
                data,
                "revision",
                default=None,
                minimum=0,
            )
        except ApiContractError as exc:
            return _contract_error_response(exc)
        try:
            payload = await _run_file_io(
                _save_lora_profile,
                name,
                data,
                overwrite=overwrite,
                profile_id=profile_id,
                revision=revision,
            )
        except (FileExistsError, FileNotFoundError, ValueError) as exc:
            return _profile_error_response(exc)
        return web.json_response({"status": "ok", "profile": payload})

    @_request_correlated
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

    @_request_correlated
    async def aio_profiles_handler(request):
        try:
            payload = await _run_file_io(_list_aio_profiles)
        except InvalidProfileDataError as exc:
            return _profile_error_response(exc)
        return web.json_response({"status": "ok", "profiles": payload})

    @_request_correlated
    async def save_aio_profile_handler(request):
        try:
            data = await parse_json_object(request)
            name = json_string(data, "name", allow_empty=False)
            json_object(data, "settings")
            overwrite = json_boolean(data, "overwrite")
            profile_id = json_uuid_string(
                data,
                "profile_id",
                required=False,
            )
            revision = json_integer(
                data,
                "revision",
                default=None,
                minimum=0,
            )
        except ApiContractError as exc:
            return _contract_error_response(exc)
        try:
            payload = await _run_file_io(
                _save_aio_profile,
                name,
                data,
                overwrite=overwrite,
                profile_id=profile_id,
                revision=revision,
            )
        except (FileExistsError, FileNotFoundError, ValueError) as exc:
            return _profile_error_response(exc)
        return web.json_response({"status": "ok", "profile": payload})

    @_request_correlated
    async def load_aio_profile_handler(request):
        try:
            payload = await _run_file_io(
                _load_aio_profile,
                request.query.get("name", ""),
            )
        except (FileNotFoundError, ValueError) as exc:
            return _profile_error_response(exc)
        return web.json_response({"status": "ok", "profile": payload})

    @_request_correlated
    async def delete_aio_profile_handler(request):
        try:
            data = await parse_json_object(request)
            name = json_string(data, "name", allow_empty=False)
            profile_id = json_uuid_string(
                data,
                "profile_id",
                required=False,
            )
            revision = json_integer(
                data,
                "revision",
                default=None,
                minimum=0,
            )
        except ApiContractError as exc:
            return _contract_error_response(exc)
        try:
            payload = await _run_file_io(
                _delete_aio_profile,
                name,
                profile_id=profile_id,
                revision=revision,
            )
        except (FileNotFoundError, ValueError) as exc:
            return _profile_error_response(exc)
        return web.json_response({"status": "ok", "profile": payload})

    @_request_correlated
    async def rename_aio_profile_handler(request):
        try:
            data = await parse_json_object(request)
            old_name = json_string(data, "old_name", allow_empty=False)
            new_name = json_string(data, "new_name", allow_empty=False)
            overwrite = json_boolean(data, "overwrite")
            profile_id = json_uuid_string(
                data,
                "profile_id",
                required=False,
            )
            revision = json_integer(
                data,
                "revision",
                default=None,
                minimum=0,
            )
            target_profile_id = json_uuid_string(
                data,
                "target_profile_id",
                required=False,
            )
            target_revision = json_integer(
                data,
                "target_revision",
                default=None,
                minimum=0,
            )
        except ApiContractError as exc:
            return _contract_error_response(exc)
        try:
            payload = await _run_file_io(
                _rename_aio_profile,
                old_name,
                new_name,
                overwrite=overwrite,
                profile_id=profile_id,
                revision=revision,
                target_profile_id=target_profile_id,
                target_revision=target_revision,
            )
        except (FileExistsError, FileNotFoundError, ValueError) as exc:
            return _profile_error_response(exc)
        return web.json_response({"status": "ok", "profile": payload})

    @_request_correlated
    async def fix_lora_profile_handler(request):
        try:
            data = await parse_json_object(request)
            if "profile_data" in data:
                json_object(data, "profile_data")
        except ApiContractError as exc:
            return _contract_error_response(exc)
        payload = await _run_file_io(_fix_lora_profile_payload, data)
        return web.json_response({"status": "ok", "profile": payload})

    _ROUTE_DEFINITIONS = (
        ("get", "/easyuse_anima/settings", get_settings_handler),
        ("post", "/easyuse_anima/set_setting", set_setting_handler),
        ("get", "/easyuse_anima/long_text_settings", get_long_text_settings_handler),
        ("get", "/easyuse_anima/wildcards", get_wildcards_handler),
        (
            "post",
            "/easyuse_anima/long_text_settings/save",
            save_long_text_settings_handler,
        ),
        ("get", "/easyuse_anima/autocomplete_status", autocomplete_status_handler),
        ("get", "/easyuse_anima/autocomplete", autocomplete_handler),
        ("post", "/easyuse_anima/classify_prompt", classify_prompt_handler),
        ("post", "/easyuse_anima/translate_prompt", translate_prompt_handler),
        (
            "post",
            "/easyuse_anima/aio/torch-compile/recommend",
            aio_torch_compile_recommend_handler,
        ),
        ("get", "/easyuse_anima/lora_preview", lora_preview_handler),
        ("get", "/easyuse_anima/loras", loras_handler),
        ("get", "/easyuse_anima/lora_profiles", lora_profiles_handler),
        ("post", "/easyuse_anima/lora_profiles/save", save_lora_profile_handler),
        ("get", "/easyuse_anima/lora_profiles/load", load_lora_profile_handler),
        ("get", "/easyuse_anima/aio_profiles", aio_profiles_handler),
        ("post", "/easyuse_anima/aio_profiles/save", save_aio_profile_handler),
        ("get", "/easyuse_anima/aio_profiles/load", load_aio_profile_handler),
        ("post", "/easyuse_anima/aio_profiles/delete", delete_aio_profile_handler),
        ("post", "/easyuse_anima/aio_profiles/rename", rename_aio_profile_handler),
        ("post", "/easyuse_anima/lora_profiles/fix", fix_lora_profile_handler),
    )
else:
    _ROUTE_DEFINITIONS = ()


_ROUTE_REGISTRATION_MARKER = "_easyuse_anima_registered_routes_v1"
_ROUTE_SIGNATURE = tuple(
    (method.upper(), path)
    for method, path, _handler in _ROUTE_DEFINITIONS
)


def register_routes(route_table=None) -> bool:
    """Register the current route set once for each ComfyUI route table."""

    global routes
    target = _get_prompt_routes() if route_table is None else route_table
    routes = target
    if web is None or target is None:
        return False

    existing_signature = getattr(target, _ROUTE_REGISTRATION_MARKER, None)
    if existing_signature == _ROUTE_SIGNATURE:
        return True
    if existing_signature is not None:
        raise RuntimeError("EasyUse Anima route registration signature mismatch")

    for method, path, handler in _ROUTE_DEFINITIONS:
        getattr(target, method)(path)(handler)
    setattr(target, _ROUTE_REGISTRATION_MARKER, _ROUTE_SIGNATURE)
    return True
