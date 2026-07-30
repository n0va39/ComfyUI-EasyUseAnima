from __future__ import annotations

import os
import threading
import weakref
from collections.abc import Generator, Mapping
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from ..errors import ConflictError, ValidationError
from .contract import read_profile_metadata


class ProfileMutationError(ConflictError, ValueError):
    """A public optimistic-concurrency failure with a stable API mapping."""

    status: int
    code: str
    message: str

    def __init__(
        self,
        *,
        status: int,
        code: str,
        message: str,
        details: Mapping[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.status = status
        self.code = code
        self.message = message
        self.details = dict(details) if details is not None else None


class ProfilePreconditionRequiredError(ProfileMutationError, ValidationError):
    def __init__(self, fields: tuple[str, ...], *, profile: str = "profile") -> None:
        super().__init__(
            status=428,
            code="profile_precondition_required",
            message="Profile precondition is required",
            details={"profile": profile, "fields": list(fields)},
        )


class ProfileIdentityMismatchError(ProfileMutationError):
    def __init__(self, *, profile: str = "profile") -> None:
        super().__init__(
            status=409,
            code="profile_identity_mismatch",
            message="Profile identity does not match",
            details={"profile": profile},
        )


class ProfileRevisionConflictError(ProfileMutationError):
    def __init__(self, *, profile: str = "profile") -> None:
        super().__init__(
            status=409,
            code="profile_revision_conflict",
            message="Profile revision does not match",
            details={"profile": profile},
        )


class DirectoryMutationCoordinator:
    """Serialize profile discovery, CAS verification, and mutation per directory."""

    def __init__(self) -> None:
        self._guard = threading.Lock()
        self._locks: weakref.WeakValueDictionary[str, threading.RLock] = (
            weakref.WeakValueDictionary()
        )

    @staticmethod
    def _key(directory: str | os.PathLike[str]) -> str:
        return os.path.normcase(str(Path(directory).resolve(strict=False)))

    def _lock(self, directory: str | os.PathLike[str]) -> threading.RLock:
        key = self._key(directory)
        with self._guard:
            lock = self._locks.get(key)
            if lock is None:
                lock = threading.RLock()
                self._locks[key] = lock
            return lock

    @contextmanager
    def locked(self, directory: str | os.PathLike[str]) -> Generator[None, None, None]:
        lock = self._lock(directory)
        with lock:
            yield


def require_profile_precondition(
    profile_id: str | None,
    revision: int | None,
    *,
    id_field: str = "profile_id",
    revision_field: str = "revision",
    profile: str = "profile",
) -> None:
    missing = tuple(
        field
        for field, value in (
            (id_field, profile_id),
            (revision_field, revision),
        )
        if value is None
    )
    if missing:
        raise ProfilePreconditionRequiredError(missing, profile=profile)


def verify_profile_precondition(
    profile_kind: str,
    filename: str,
    current_document: Mapping[str, Any],
    *,
    profile_id: str | None,
    revision: int | None,
    id_field: str = "profile_id",
    revision_field: str = "revision",
    profile: str = "profile",
) -> tuple[str, int]:
    """Verify identity before revision against the document read under the lock."""

    require_profile_precondition(
        profile_id,
        revision,
        id_field=id_field,
        revision_field=revision_field,
        profile=profile,
    )
    current_profile_id, current_revision = read_profile_metadata(
        profile_kind,
        filename,
        current_document,
    )
    if profile_id != current_profile_id:
        raise ProfileIdentityMismatchError(profile=profile)
    if revision != current_revision:
        raise ProfileRevisionConflictError(profile=profile)
    return current_profile_id, current_revision


PROFILE_MUTATION_COORDINATOR = DirectoryMutationCoordinator()


__all__ = ()
