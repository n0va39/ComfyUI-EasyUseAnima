"""AiO profile normalization, persistence, delete, and rename operations."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import cast

from ..infrastructure.filesystem.atomic_json import AtomicJsonStore
from ..infrastructure.filesystem.paths import USER_DATA_DIR
from .contract import (
    PROFILE_KIND_AIO,
    ProfileContractError,
    build_profile_document,
    create_profile_document,
    interpret_profile_document,
    rename_profile_document,
    update_profile_document,
)
from .mutation import (
    PROFILE_MUTATION_COORDINATOR,
    ProfileRevisionConflictError,
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


def _sanitize_aio_profile_name(name: str) -> str:
    safe_name = _sanitize_profile_name(name)
    if safe_name.casefold() in {
        item.casefold() for item in AIO_RESERVED_PROFILE_NAMES
    }:
        raise ValueError("System profile names are reserved")
    return safe_name


def _aio_profile_path(name: str, profile_dir: Path | None = None) -> Path:
    safe_name = _sanitize_aio_profile_name(name)
    root = (profile_dir or AIO_PROFILE_DIR).resolve()
    path = (root / f"{safe_name}.json").resolve()
    if os.path.commonpath((str(root), str(path))) != str(root):
        raise ValueError("Invalid profile path")
    return path


def _find_aio_profile_path(
    name: str,
    profile_dir: Path | None = None,
) -> Path | None:
    safe_name = _sanitize_aio_profile_name(name)
    root = profile_dir or AIO_PROFILE_DIR
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
        _profile_list_item(PROFILE_KIND_AIO, path)
        for path in sorted(
            root.glob("*.json"),
            key=lambda item: item.stem.casefold(),
        )
    ]


def _validate_aio_profile_size(document: dict) -> None:
    encoded = json.dumps(document, ensure_ascii=False, indent=2)
    if len(encoded.encode("utf-8")) > MAX_AIO_PROFILE_BYTES:
        raise ValueError("Profile settings are too large")


def _save_aio_profile(
    name: str,
    data: dict,
    *,
    overwrite: bool = False,
    profile_id: str | None = None,
    revision: int | None = None,
) -> dict:
    payload = _normalize_aio_profile_payload(name, data)
    requested_path = _aio_profile_path(payload["name"])
    if overwrite:
        require_profile_precondition(profile_id, revision)
    with PROFILE_MUTATION_COORDINATOR.locked(AIO_PROFILE_DIR):
        existing = _find_aio_profile_path(payload["name"])
        if existing is not None and not overwrite:
            raise FileExistsError("Profile already exists")
        if existing is None and overwrite:
            raise FileNotFoundError("Profile not found")
        if existing is None and len(_list_aio_profiles()) >= MAX_AIO_PROFILES:
            raise ValueError(
                f"A maximum of {MAX_AIO_PROFILES} profiles can be saved"
            )
        path = existing or requested_path
        try:
            if existing is None:
                document = create_profile_document(
                    PROFILE_KIND_AIO,
                    path.stem,
                    payload,
                )
            else:
                current = _read_profile_json(path)
                if not isinstance(current, dict):
                    raise ProfileContractError("Profile data is invalid")
                verify_profile_precondition(
                    PROFILE_KIND_AIO,
                    path.stem,
                    current,
                    profile_id=profile_id,
                    revision=revision,
                )
                document = update_profile_document(
                    PROFILE_KIND_AIO,
                    path.stem,
                    current,
                    payload,
                )
        except ProfileContractError as exc:
            raise InvalidProfileDataError(str(exc)) from exc
        _validate_aio_profile_size(document)
        AtomicJsonStore(path).write(document)
    return document


def _normalize_stored_aio_profile_payload(name: str, data) -> dict:
    if not isinstance(data, dict):
        raise InvalidProfileDataError("Profile data is invalid")
    try:
        payload = _normalize_aio_profile_payload(name, data)
        interpreted = interpret_profile_document(PROFILE_KIND_AIO, name, data)
        document = build_profile_document(
            name=name,
            profile_id=interpreted["profile_id"],
            revision=interpreted["revision"],
            payload=payload,
        )
        return document
    except (ProfileContractError, ValueError) as exc:
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


def _delete_aio_profile(
    name: str,
    *,
    profile_id: str | None = None,
    revision: int | None = None,
) -> dict:
    require_profile_precondition(profile_id, revision)
    with PROFILE_MUTATION_COORDINATOR.locked(AIO_PROFILE_DIR):
        path = _find_aio_profile_path(name)
        if path is None or not path.is_file():
            raise FileNotFoundError("Profile not found")
        store = AtomicJsonStore(path)
        try:
            data = _read_profile_json(path)
            if not isinstance(data, dict):
                raise ProfileContractError("Profile data is invalid")
            deleted_profile_id, deleted_revision = verify_profile_precondition(
                PROFILE_KIND_AIO,
                path.stem,
                data,
                profile_id=profile_id,
                revision=revision,
            )
        except ProfileContractError as exc:
            raise InvalidProfileDataError(str(exc)) from exc
        try:
            store.delete()
        except FileNotFoundError as exc:
            raise FileNotFoundError("Profile not found") from exc
    return {
        "name": path.stem,
        "profile_id": deleted_profile_id,
        "revision": deleted_revision,
    }


def _rename_aio_profile(
    old_name: str,
    new_name: str,
    *,
    overwrite: bool = False,
    profile_id: str | None = None,
    revision: int | None = None,
    target_profile_id: str | None = None,
    target_revision: int | None = None,
) -> dict:
    require_profile_precondition(profile_id, revision, profile="source")
    with PROFILE_MUTATION_COORDINATOR.locked(AIO_PROFILE_DIR):
        source = _find_aio_profile_path(old_name)
        if source is None or not source.is_file():
            raise FileNotFoundError("Profile not found")
        safe_new_name = _sanitize_aio_profile_name(new_name)
        try:
            data = _read_profile_json(source)
            if not isinstance(data, dict):
                raise ProfileContractError("Profile data is invalid")
            verify_profile_precondition(
                PROFILE_KIND_AIO,
                source.stem,
                data,
                profile_id=profile_id,
                revision=revision,
                profile="source",
            )
        except ProfileContractError as exc:
            raise InvalidProfileDataError(str(exc)) from exc

        if (
            _windows_profile_filename_identity(source.stem)
            == _windows_profile_filename_identity(safe_new_name)
        ):
            renamed = _rename_aio_profile_payload(
                source.stem,
                source.stem,
                data,
            )
            if data != renamed:
                AtomicJsonStore(source, backup=False).write(renamed)
            return renamed

        target = _find_aio_profile_path(safe_new_name)
        if target is not None and not overwrite:
            raise FileExistsError("Profile already exists")
        if target is None and (
            target_profile_id is not None or target_revision is not None
        ):
            raise ProfileRevisionConflictError(profile="target")
        if target is not None:
            require_profile_precondition(
                target_profile_id,
                target_revision,
                id_field="target_profile_id",
                revision_field="target_revision",
                profile="target",
            )
            try:
                target_data = _read_profile_json(target)
                if not isinstance(target_data, dict):
                    raise ProfileContractError("Profile data is invalid")
                verify_profile_precondition(
                    PROFILE_KIND_AIO,
                    target.stem,
                    target_data,
                    profile_id=target_profile_id,
                    revision=target_revision,
                    id_field="target_profile_id",
                    revision_field="target_revision",
                    profile="target",
                )
            except ProfileContractError as exc:
                raise InvalidProfileDataError(str(exc)) from exc

        target_path = target or _aio_profile_path(safe_new_name)
        renamed = cast(
            dict,
            AtomicJsonStore(target_path).replace_from(
                AtomicJsonStore(source),
                overwrite=overwrite,
                backup_target=True,
                transform=lambda current: _rename_aio_profile_payload(
                    source.stem,
                    target_path.stem,
                    current,
                ),
            ),
        )
        return renamed


def _rename_aio_profile_payload(
    source_name: str,
    target_name: str,
    data,
) -> dict:
    normalized = _normalize_stored_aio_profile_payload(source_name, data)
    try:
        document = rename_profile_document(
            PROFILE_KIND_AIO,
            source_name,
            target_name,
            data,
            normalized,
        )
    except ProfileContractError as exc:
        raise InvalidProfileDataError(str(exc)) from exc
    _validate_aio_profile_size(document)
    return document


__all__ = ()
