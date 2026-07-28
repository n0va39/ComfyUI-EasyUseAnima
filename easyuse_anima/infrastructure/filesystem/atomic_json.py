"""Durable atomic JSON storage primitives."""

from __future__ import annotations

import errno
import json
import os
import tempfile
import threading
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import TypeVar

_T = TypeVar("_T")
_MISSING = object()
_PATH_LOCKS: dict[str, threading.RLock] = {}
_PATH_LOCKS_GUARD = threading.Lock()
_RECOVERABLE_READ_ERRORS = (FileNotFoundError, json.JSONDecodeError, UnicodeError)
_UNSUPPORTED_DIRECTORY_FSYNC_ERRORS = {
    errno.EACCES,
    errno.EBADF,
    errno.EINVAL,
    errno.ENOTSUP,
    errno.EPERM,
}


def _resolved_path(path: str | os.PathLike[str]) -> Path:
    return Path(path).expanduser().resolve(strict=False)


def _path_lock_key(path: Path) -> str:
    return os.path.normcase(str(path))


def _path_lock(path: Path) -> threading.RLock:
    key = _path_lock_key(path)
    with _PATH_LOCKS_GUARD:
        lock = _PATH_LOCKS.get(key)
        if lock is None:
            lock = threading.RLock()
            _PATH_LOCKS[key] = lock
        return lock


@contextmanager
def _locked_paths(*paths: Path) -> Iterator[None]:
    locks = {
        _path_lock_key(path): _path_lock(path)
        for path in paths
    }
    ordered = [locks[key] for key in sorted(locks)]
    for lock in ordered:
        lock.acquire()
    try:
        yield
    finally:
        for lock in reversed(ordered):
            lock.release()


def _fsync_directory(path: Path) -> None:
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
    try:
        descriptor = os.open(path, flags)
    except OSError as exc:
        if os.name == "nt" or exc.errno in _UNSUPPORTED_DIRECTORY_FSYNC_ERRORS:
            return
        raise
    try:
        try:
            os.fsync(descriptor)
        except OSError as exc:
            if os.name != "nt" and exc.errno not in _UNSUPPORTED_DIRECTORY_FSYNC_ERRORS:
                raise
    finally:
        os.close(descriptor)


def _unlink_if_present(path: Path) -> None:
    try:
        path.unlink()
    except FileNotFoundError:
        pass


class AtomicJsonStore:
    """Durable JSON storage with atomic publication and backup recovery.

    Reads return the primary JSON document when it is valid. A missing, invalid
    UTF-8, or invalid JSON primary falls back to a valid backup without mutating
    either file. If neither document is usable, ``default`` is returned when it
    was supplied; otherwise the primary error is raised (or the backup parse
    error when the primary is missing).

    Writes publish a fully flushed and fsynced same-directory temporary file
    with ``os.replace``. When backups are enabled, a valid existing primary is
    copied to a durable backup temp and atomically published before the new
    primary. Invalid primaries never replace an existing valid backup.
    """

    def __init__(
        self,
        path: str | os.PathLike[str],
        *,
        backup: bool | str | os.PathLike[str] = True,
    ) -> None:
        self.path = _resolved_path(path)
        if backup is True:
            backup_path = self.path.with_name(f"{self.path.name}.bak")
        elif backup is False:
            backup_path = None
        else:
            backup_path = _resolved_path(backup)
            if backup_path.parent != self.path.parent:
                raise ValueError("Backup must be in the same directory as the primary")
        self.backup_path = backup_path

    @contextmanager
    def locked(self) -> Iterator[None]:
        """Hold the process-wide lock shared by all stores for this path."""

        with _locked_paths(self.path):
            yield

    def _read_path(self, path: Path):
        return json.loads(path.read_text(encoding="utf-8"))

    def _read_unlocked(self, default=_MISSING):
        try:
            return self._read_path(self.path)
        except _RECOVERABLE_READ_ERRORS as primary_error:
            backup_error = None
            if self.backup_path is not None:
                try:
                    return self._read_path(self.backup_path)
                except _RECOVERABLE_READ_ERRORS as exc:
                    backup_error = exc

            if default is not _MISSING:
                return default
            if isinstance(primary_error, FileNotFoundError) and backup_error is not None:
                if not isinstance(backup_error, FileNotFoundError):
                    raise backup_error from primary_error
            raise primary_error

    def read(self, *, default=_MISSING):
        with self.locked():
            return self._read_unlocked(default)

    def _write_temp(self, target: Path, data: bytes) -> Path:
        descriptor, temp_name = tempfile.mkstemp(
            dir=target.parent,
            prefix=f".{target.name}.",
            suffix=".tmp",
        )
        temp_path = Path(temp_name)
        try:
            try:
                with os.fdopen(descriptor, "wb") as handle:
                    descriptor = -1
                    handle.write(data)
                    handle.flush()
                    os.fsync(handle.fileno())
            finally:
                if descriptor >= 0:
                    os.close(descriptor)
        except BaseException:
            _unlink_if_present(temp_path)
            raise
        return temp_path

    def _backup_primary_unlocked(self) -> bool:
        if self.backup_path is None or not self.path.is_file():
            return False
        try:
            raw = self.path.read_bytes()
            json.loads(raw.decode("utf-8"))
        except _RECOVERABLE_READ_ERRORS:
            return False

        backup_temp: Path | None = self._write_temp(self.backup_path, raw)
        try:
            os.replace(backup_temp, self.backup_path)
            backup_temp = None
            _fsync_directory(self.path.parent)
        finally:
            if backup_temp is not None:
                _unlink_if_present(backup_temp)
        return True

    def _write_bytes_unlocked(self, encoded: bytes) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        primary_temp: Path | None = self._write_temp(self.path, encoded)
        try:
            self._backup_primary_unlocked()
            os.replace(primary_temp, self.path)
            primary_temp = None
            _fsync_directory(self.path.parent)
        finally:
            if primary_temp is not None:
                _unlink_if_present(primary_temp)

    @staticmethod
    def _encode(value, *, indent: int | None, trailing_newline: bool) -> bytes:
        encoded = json.dumps(value, ensure_ascii=False, indent=indent)
        if trailing_newline:
            encoded += "\n"
        return encoded.encode("utf-8")

    def write(
        self,
        value,
        *,
        indent: int | None = 2,
        trailing_newline: bool = False,
    ) -> None:
        encoded = self._encode(value, indent=indent, trailing_newline=trailing_newline)
        with self.locked():
            self._write_bytes_unlocked(encoded)

    def update(
        self,
        transform: Callable[[object], _T],
        *,
        default=_MISSING,
        indent: int | None = 2,
        trailing_newline: bool = False,
    ) -> _T:
        """Run a read-modify-write callback while holding the path lock."""

        with self.locked():
            value = transform(self._read_unlocked(default))
            encoded = self._encode(value, indent=indent, trailing_newline=trailing_newline)
            self._write_bytes_unlocked(encoded)
            return value

    def delete(self) -> None:
        """Delete the primary and backup under the shared primary-path lock.

        The backup is removed and its directory entry is synced before the
        primary is touched. Therefore a backup deletion failure preserves the
        primary. Any primary unlink or directory fsync failure is propagated;
        callers can inspect the files to determine the completed boundary.
        """

        with self.locked():
            if not self.path.is_file():
                raise FileNotFoundError(self.path)

            if self.backup_path is not None:
                try:
                    self.backup_path.unlink()
                except FileNotFoundError:
                    pass
                else:
                    _fsync_directory(self.path.parent)

            self.path.unlink()
            _fsync_directory(self.path.parent)

    def replace_from(
        self,
        source: AtomicJsonStore,
        *,
        overwrite: bool = True,
        backup_target: bool = True,
        transform: Callable[[object], _T] | None = None,
    ) -> object | _T:
        """Validate and move a primary while holding both path locks.

        A transformed value is encoded before either primary is changed. The
        source is then moved onto the target and the transformed bytes are
        published before the joint lock is released. If that second
        publication fails, both primaries are restored byte-for-byte. A source
        backup is consumed by a successful move and restored after any failure
        before primary publication completes. A failed overwrite also restores
        the target backup's prior existence and exact bytes.
        """

        if source.path.parent != self.path.parent:
            raise ValueError("Atomic JSON moves require the same directory")
        with _locked_paths(source.path, self.path):
            value = source._read_path(source.path)
            if self.path.exists() and not overwrite:
                raise FileExistsError("Profile already exists")
            self.path.parent.mkdir(parents=True, exist_ok=True)

            transformed_temp: Path | None = None
            target_restore_temp: Path | None = None
            target_backup_restore_temp: Path | None = None
            source_backup_restore_temp: Path | None = None
            target_backup_restore_needed = False
            source_backup_removed = False
            target_was_file = self.path.is_file()
            target_backup_existed = (
                self.backup_path is not None and self.backup_path.is_file()
            )
            if transform is not None:
                value = transform(value)
                encoded = self._encode(value, indent=2, trailing_newline=False)
                transformed_temp = self._write_temp(self.path, encoded)
            try:
                if transform is not None and target_was_file:
                    target_restore_temp = self._write_temp(
                        self.path,
                        self.path.read_bytes(),
                    )
                if (
                    backup_target
                    and target_was_file
                    and target_backup_existed
                    and self.backup_path is not None
                ):
                    target_backup_restore_temp = self._write_temp(
                        self.backup_path,
                        self.backup_path.read_bytes(),
                    )
                if source.backup_path is not None and source.backup_path.is_file():
                    source_backup_restore_temp = source._write_temp(
                        source.backup_path,
                        source.backup_path.read_bytes(),
                    )
                    try:
                        source.backup_path.unlink()
                    except FileNotFoundError:
                        pass
                    source_backup_removed = True
                    _fsync_directory(self.path.parent)
                if (
                    backup_target
                    and target_was_file
                    and self.backup_path is not None
                ):
                    target_backup_restore_needed = True
                    self._backup_primary_unlocked()

                os.replace(source.path, self.path)
                if transformed_temp is not None:
                    try:
                        os.replace(transformed_temp, self.path)
                        transformed_temp = None
                    except BaseException as publication_error:
                        try:
                            os.replace(self.path, source.path)
                            if target_restore_temp is not None:
                                os.replace(target_restore_temp, self.path)
                                target_restore_temp = None
                            _fsync_directory(self.path.parent)
                        except BaseException as rollback_error:
                            raise rollback_error from publication_error
                        raise

                source_backup_removed = False
                target_backup_restore_needed = False
                _fsync_directory(self.path.parent)
                return value
            except BaseException as transaction_error:
                rollback_error = None
                if (
                    source_backup_removed
                    and source_backup_restore_temp is not None
                    and source.backup_path is not None
                ):
                    try:
                        os.replace(source_backup_restore_temp, source.backup_path)
                        source_backup_restore_temp = None
                        source_backup_removed = False
                        _fsync_directory(self.path.parent)
                    except BaseException as exc:
                        rollback_error = exc
                if target_backup_restore_needed and self.backup_path is not None:
                    try:
                        if (
                            target_backup_existed
                            and target_backup_restore_temp is not None
                        ):
                            os.replace(
                                target_backup_restore_temp,
                                self.backup_path,
                            )
                            target_backup_restore_temp = None
                        else:
                            _unlink_if_present(self.backup_path)
                        target_backup_restore_needed = False
                        _fsync_directory(self.path.parent)
                    except BaseException as exc:
                        if rollback_error is None:
                            rollback_error = exc
                if rollback_error is not None:
                    raise rollback_error from transaction_error
                raise
            finally:
                if transformed_temp is not None:
                    _unlink_if_present(transformed_temp)
                if target_restore_temp is not None:
                    _unlink_if_present(target_restore_temp)
                if target_backup_restore_temp is not None:
                    _unlink_if_present(target_backup_restore_temp)
                if source_backup_restore_temp is not None:
                    _unlink_if_present(source_backup_restore_temp)


def create_atomic_json_store(
    path: str | os.PathLike[str],
    *,
    backup: bool | str | os.PathLike[str] = True,
) -> AtomicJsonStore:
    """Create a store that uses the canonical process path-lock owner."""

    return AtomicJsonStore(path, backup=backup)


__all__ = ("AtomicJsonStore", "create_atomic_json_store")
