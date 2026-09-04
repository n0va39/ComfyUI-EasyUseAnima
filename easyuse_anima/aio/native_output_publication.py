"""Collision-safe publication for native image output files."""

from __future__ import annotations

import logging
import os
import secrets
import stat as stat_module
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO

logger = logging.getLogger("ComfyUI-EasyUseAnima")

_TEMP_PREFIX = ".easyuse-anima-"
_TEMP_SUFFIX = ".tmp"
_TEMP_NAME_ATTEMPTS = 32


class PublicationCollision(FileExistsError):
    """A final output name was claimed before publication."""


class PublicationIntegrityError(OSError):
    """The bound directory or an open temporary file changed unexpectedly."""


@dataclass(frozen=True, slots=True)
class _FileIdentity:
    device: int
    inode: int


@dataclass(slots=True)
class _OpenTemporary:
    directory: OutputDirectoryBinding
    name: str
    descriptor: int
    identity: _FileIdentity
    publication_target: str | None = None
    retain_on_close: bool = False

    def binary_writer(self) -> BinaryIO:
        return os.fdopen(os.dup(self.descriptor), "w+b")

    def keep(self) -> None:
        self.retain_on_close = True

    def close(self) -> bool:
        if self.descriptor < 0:
            return True
        descriptor = self.descriptor
        self.descriptor = -1
        if os.name == "nt":
            if not self.retain_on_close:
                _delete_windows_file_handle(descriptor)
            os.close(descriptor)
            if self.retain_on_close:
                return True
            target_removed = (
                self.publication_target is None
                or self.directory._remove_name_if_owned(
                    self.publication_target,
                    self.identity,
                )
            )
            temporary_removed = self.directory._remove_temporary_name(
                self.name,
                self.identity,
            )
            return target_removed and temporary_removed
        temporary_removed = self.directory._remove_temporary_name(
            self.name,
            self.identity,
        )
        os.close(descriptor)
        return temporary_removed


def _file_identity(stat_result: os.stat_result) -> _FileIdentity:
    return _FileIdentity(int(stat_result.st_dev), int(stat_result.st_ino))


def _open_windows_directory_guard(path: Path) -> int | None:
    if os.name != "nt":
        return None

    import ctypes
    from ctypes import wintypes

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    create_file = kernel32.CreateFileW
    create_file.argtypes = (
        wintypes.LPCWSTR,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.LPVOID,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.HANDLE,
    )
    create_file.restype = wintypes.HANDLE
    generic_read = 0x80000000
    file_share_read = 0x00000001
    file_share_write = 0x00000002
    open_existing = 3
    file_flag_backup_semantics = 0x02000000
    handle = create_file(
        str(path),
        generic_read,
        file_share_read | file_share_write,
        None,
        open_existing,
        file_flag_backup_semantics,
        None,
    )
    invalid_handle = ctypes.c_void_p(-1).value
    if handle in (None, invalid_handle):
        raise ctypes.WinError(ctypes.get_last_error())
    return int(handle)


def _close_windows_handle(handle: int | None) -> None:
    if handle is None:
        return

    import ctypes
    from ctypes import wintypes

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    close_handle = kernel32.CloseHandle
    close_handle.argtypes = (wintypes.HANDLE,)
    close_handle.restype = wintypes.BOOL
    close_handle(handle)


def _create_windows_temporary(path: Path) -> int:
    import ctypes
    import msvcrt
    from ctypes import wintypes

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    create_file = kernel32.CreateFileW
    create_file.argtypes = (
        wintypes.LPCWSTR,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.LPVOID,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.HANDLE,
    )
    create_file.restype = wintypes.HANDLE
    generic_read = 0x80000000
    generic_write = 0x40000000
    delete_access = 0x00010000
    file_share_read = 0x00000001
    file_share_write = 0x00000002
    create_new = 1
    file_attribute_temporary = 0x00000100
    file_flag_sequential_scan = 0x08000000
    handle = create_file(
        str(path),
        generic_read | generic_write | delete_access,
        file_share_read | file_share_write,
        None,
        create_new,
        file_attribute_temporary | file_flag_sequential_scan,
        None,
    )
    invalid_handle = ctypes.c_void_p(-1).value
    if handle in (None, invalid_handle):
        error = ctypes.get_last_error()
        if error in {80, 183}:
            raise FileExistsError(error, "temporary output already exists", str(path))
        raise ctypes.WinError(error)
    try:
        return msvcrt.open_osfhandle(
            int(handle),
            os.O_RDWR | getattr(os, "O_BINARY", 0),
        )
    except Exception:
        _close_windows_handle(int(handle))
        raise


def _publish_windows_file_handle(
    descriptor: int,
    target: Path,
) -> None:
    import ctypes
    import msvcrt
    from ctypes import wintypes

    target_text = str(target)

    class FileRenameInfo(ctypes.Structure):
        _fields_ = (
            ("Flags", wintypes.DWORD),
            ("RootDirectory", wintypes.HANDLE),
            ("FileNameLength", wintypes.DWORD),
            ("FileName", wintypes.WCHAR * (len(target_text) + 1)),
        )

    value = FileRenameInfo()
    value.Flags = 0
    value.RootDirectory = None
    value.FileNameLength = len(target_text.encode("utf-16-le"))
    value.FileName = target_text

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    set_information = kernel32.SetFileInformationByHandle
    set_information.argtypes = (
        wintypes.HANDLE,
        ctypes.c_int,
        wintypes.LPVOID,
        wintypes.DWORD,
    )
    set_information.restype = wintypes.BOOL
    file_rename_info = 3
    succeeded = set_information(
        msvcrt.get_osfhandle(descriptor),
        file_rename_info,
        ctypes.byref(value),
        ctypes.sizeof(value),
    )
    if succeeded:
        return
    error = ctypes.get_last_error()
    if error in {80, 183}:
        raise PublicationCollision(target.name)
    raise ctypes.WinError(error)


def _delete_windows_file_handle(descriptor: int) -> None:
    import ctypes
    import msvcrt
    from ctypes import wintypes

    class FileDispositionInfo(ctypes.Structure):
        _fields_ = (("DeleteFile", ctypes.c_ubyte),)

    value = FileDispositionInfo(1)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    set_information = kernel32.SetFileInformationByHandle
    set_information.argtypes = (
        wintypes.HANDLE,
        ctypes.c_int,
        wintypes.LPVOID,
        wintypes.DWORD,
    )
    set_information.restype = wintypes.BOOL
    file_disposition_info = 4
    if not set_information(
        msvcrt.get_osfhandle(descriptor),
        file_disposition_info,
        ctypes.byref(value),
        ctypes.sizeof(value),
    ):
        logger.warning(
            "[EasyUseAnima] Native temporary handle cleanup failed (WinError %d).",
            ctypes.get_last_error(),
        )


def _windows_handle_path(handle: int) -> Path:
    import ctypes
    from ctypes import wintypes

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    get_final_path = kernel32.GetFinalPathNameByHandleW
    get_final_path.argtypes = (
        wintypes.HANDLE,
        wintypes.LPWSTR,
        wintypes.DWORD,
        wintypes.DWORD,
    )
    get_final_path.restype = wintypes.DWORD
    buffer = ctypes.create_unicode_buffer(32_768)
    length = get_final_path(handle, buffer, len(buffer), 0)
    if length == 0 or length >= len(buffer):
        raise ctypes.WinError(ctypes.get_last_error())
    value = buffer.value
    if value.startswith("\\\\?\\UNC\\"):
        value = "\\\\" + value[8:]
    elif value.startswith("\\\\?\\"):
        value = value[4:]
    return Path(value)


def _windows_file_is_in_directory(
    descriptor: int,
    directory_handle: int,
) -> bool:
    import msvcrt

    file_parent = _windows_handle_path(msvcrt.get_osfhandle(descriptor)).parent
    directory = _windows_handle_path(directory_handle)
    return os.path.normcase(os.path.normpath(str(file_parent))) == os.path.normcase(
        os.path.normpath(str(directory))
    )


class OutputDirectoryBinding:
    """Keep publication anchored to one verified output directory identity."""

    def __init__(
        self,
        path: Path,
        *,
        expected_identity: tuple[int, int] | None = None,
        directory_descriptor: int | None = None,
        windows_handle: int | None = None,
    ):
        if directory_descriptor is not None and windows_handle is not None:
            raise ValueError("only one prepared directory handle may be supplied")
        self.path = Path(path)
        self._expected_identity = (
            None
            if expected_identity is None
            else _FileIdentity(*expected_identity)
        )
        self._identity: _FileIdentity | None = None
        self._directory_descriptor = directory_descriptor
        self._windows_handle = windows_handle
        self._owns_directory_descriptor = directory_descriptor is None
        self._owns_windows_handle = windows_handle is None

    def __enter__(self) -> OutputDirectoryBinding:
        resolved = self.path.resolve(strict=True)
        if os.path.normcase(str(resolved)) != os.path.normcase(str(self.path)):
            raise PublicationIntegrityError(
                "output directory changed before publication"
            )
        current = self.path.stat(follow_symlinks=False)
        if not stat_module.S_ISDIR(current.st_mode):
            raise PublicationIntegrityError("output path is not a directory")
        self._identity = _file_identity(current)
        if (
            self._expected_identity is not None
            and self._identity != self._expected_identity
        ):
            raise PublicationIntegrityError(
                "output directory changed before publication ownership"
            )

        try:
            if os.name == "nt":
                if self._windows_handle is None:
                    self._windows_handle = _open_windows_directory_guard(self.path)
                elif os.path.normcase(
                    os.path.normpath(str(_windows_handle_path(self._windows_handle)))
                ) != os.path.normcase(os.path.normpath(str(self.path))):
                    raise PublicationIntegrityError(
                        "prepared output directory moved before publication"
                    )
            elif all(
                operation in os.supports_dir_fd
                for operation in (os.link, os.open, os.stat, os.unlink)
            ) and os.link in os.supports_follow_symlinks:
                if self._directory_descriptor is None:
                    flags = os.O_RDONLY
                    flags |= getattr(os, "O_DIRECTORY", 0)
                    flags |= getattr(os, "O_CLOEXEC", 0)
                    flags |= getattr(os, "O_NOFOLLOW", 0)
                    self._directory_descriptor = os.open(self.path, flags)
                if (
                    _file_identity(os.fstat(self._directory_descriptor))
                    != self._identity
                ):
                    raise PublicationIntegrityError(
                        "output directory changed while it was being bound"
                    )
            self.assert_current()
            return self
        except Exception:
            self.close()
            raise

    def __exit__(self, _type: object, _value: object, _traceback: object) -> None:
        self.close()

    def close(self) -> None:
        descriptor = self._directory_descriptor
        self._directory_descriptor = None
        if descriptor is not None and self._owns_directory_descriptor:
            os.close(descriptor)
        handle = self._windows_handle
        self._windows_handle = None
        if self._owns_windows_handle:
            _close_windows_handle(handle)

    def assert_current(self) -> None:
        if self._identity is None:
            raise PublicationIntegrityError("output directory is not bound")
        try:
            resolved = self.path.resolve(strict=True)
            current = self.path.stat(follow_symlinks=False)
        except OSError as exc:
            raise PublicationIntegrityError(
                "output directory disappeared during publication"
            ) from exc
        if (
            os.path.normcase(str(resolved)) != os.path.normcase(str(self.path))
            or not stat_module.S_ISDIR(current.st_mode)
            or _file_identity(current) != self._identity
        ):
            raise PublicationIntegrityError(
                "output directory changed during publication"
            )

    def _path(self, name: str) -> Path:
        return self.path / name

    def _stat_name(self, name: str) -> os.stat_result:
        if self._directory_descriptor is not None:
            return os.stat(
                name,
                dir_fd=self._directory_descriptor,
                follow_symlinks=False,
            )
        return self._path(name).stat(follow_symlinks=False)

    def _unlink_name(self, name: str) -> None:
        if self._directory_descriptor is not None:
            os.unlink(name, dir_fd=self._directory_descriptor)
        else:
            self._path(name).unlink()

    def _remove_name_if_owned(
        self,
        name: str,
        identity: _FileIdentity,
    ) -> bool:
        try:
            current = self._stat_name(name)
            if (
                stat_module.S_ISREG(current.st_mode)
                and _file_identity(current) == identity
            ):
                self._unlink_name(name)
            return True
        except FileNotFoundError:
            return True
        except OSError as exc:
            logger.warning(
                "[EasyUseAnima] Native output cleanup failed (%s).",
                type(exc).__name__,
            )
            return False

    def _remove_temporary_name(
        self,
        name: str,
        identity: _FileIdentity,
    ) -> bool:
        try:
            current = self._stat_name(name)
            if (
                stat_module.S_ISLNK(current.st_mode)
                or (
                    stat_module.S_ISREG(current.st_mode)
                    and _file_identity(current) == identity
                )
            ):
                self._unlink_name(name)
            return True
        except FileNotFoundError:
            return True
        except OSError as exc:
            logger.warning(
                "[EasyUseAnima] Native temporary cleanup failed (%s).",
                type(exc).__name__,
            )
            return False

    def create_temporary(self) -> _OpenTemporary:
        self.assert_current()
        flags = os.O_RDWR | os.O_CREAT | os.O_EXCL
        flags |= getattr(os, "O_BINARY", 0)
        flags |= getattr(os, "O_CLOEXEC", 0)
        flags |= getattr(os, "O_NOFOLLOW", 0)
        for _attempt in range(_TEMP_NAME_ATTEMPTS):
            name = f"{_TEMP_PREFIX}{secrets.token_hex(16)}{_TEMP_SUFFIX}"
            try:
                if os.name == "nt":
                    descriptor = _create_windows_temporary(self._path(name))
                elif self._directory_descriptor is not None:
                    descriptor = os.open(
                        name,
                        flags,
                        0o600,
                        dir_fd=self._directory_descriptor,
                    )
                else:
                    descriptor = os.open(self._path(name), flags, 0o600)
            except FileExistsError:
                continue
            temporary: _OpenTemporary | None = None
            try:
                opened = os.fstat(descriptor)
                identity = _file_identity(opened)
                temporary = _OpenTemporary(
                    directory=self,
                    name=name,
                    descriptor=descriptor,
                    identity=identity,
                )
                if not stat_module.S_ISREG(opened.st_mode):
                    raise PublicationIntegrityError(
                        "temporary output is not a regular file"
                    )
                self.assert_current()
                self.assert_temporary_identity(temporary)
                return temporary
            except Exception:
                if temporary is not None:
                    temporary.close()
                else:
                    os.close(descriptor)
                raise
        raise OSError("could not allocate a unique native output temporary file")

    def assert_temporary_identity(self, temporary: _OpenTemporary) -> None:
        opened = os.fstat(temporary.descriptor)
        try:
            named = self._stat_name(temporary.name)
        except FileNotFoundError as exc:
            raise PublicationIntegrityError(
                "temporary output name disappeared before publication"
            ) from exc
        if (
            not stat_module.S_ISREG(opened.st_mode)
            or not stat_module.S_ISREG(named.st_mode)
            or _file_identity(opened) != temporary.identity
            or _file_identity(named) != temporary.identity
            or opened.st_nlink != 1
            or named.st_nlink != 1
        ):
            raise PublicationIntegrityError(
                "temporary output name changed before publication"
            )

    def link_no_replace(
        self,
        temporary: _OpenTemporary,
        target_name: str,
    ) -> _FileIdentity:
        self.assert_current()
        self.assert_temporary_identity(temporary)
        temporary.publication_target = target_name
        try:
            if os.name == "nt":
                if self._windows_handle is None:
                    raise PublicationIntegrityError(
                        "Windows output directory handle is unavailable"
                    )
                _publish_windows_file_handle(
                    temporary.descriptor,
                    self._path(target_name),
                )
                if not _windows_file_is_in_directory(
                    temporary.descriptor,
                    self._windows_handle,
                ):
                    raise PublicationIntegrityError(
                        "published output escaped its bound directory"
                    )
                if _file_identity(os.fstat(temporary.descriptor)) != temporary.identity:
                    raise PublicationIntegrityError(
                        "published output handle changed during publication"
                    )
                self.assert_current()
            elif self._directory_descriptor is not None:
                os.link(
                    temporary.name,
                    target_name,
                    src_dir_fd=self._directory_descriptor,
                    dst_dir_fd=self._directory_descriptor,
                    follow_symlinks=False,
                )
            else:
                os.link(self._path(temporary.name), self._path(target_name))
        except FileExistsError as exc:
            raise PublicationCollision(target_name) from exc

        try:
            published = self._stat_name(target_name)
            opened = os.fstat(temporary.descriptor)
            if (
                not stat_module.S_ISREG(published.st_mode)
                or _file_identity(published) != temporary.identity
                or _file_identity(opened) != temporary.identity
            ):
                raise PublicationIntegrityError(
                    "published output does not match its open temporary file"
                )
            self.assert_current()
            return temporary.identity
        except Exception:
            if os.name != "nt":
                self._remove_temporary_name(target_name, temporary.identity)
            raise

    def assert_published_identity(
        self,
        target_name: str,
        identity: _FileIdentity,
    ) -> None:
        self.assert_current()
        try:
            published = self._stat_name(target_name)
        except FileNotFoundError as exc:
            raise PublicationIntegrityError(
                "published output disappeared during commit"
            ) from exc
        if (
            not stat_module.S_ISREG(published.st_mode)
            or _file_identity(published) != identity
        ):
            raise PublicationIntegrityError(
                "published output identity changed during commit"
            )


def _write_image(
    temporary: _OpenTemporary,
    image: object,
    *,
    image_format: str,
    options: dict[str, object],
) -> None:
    save = getattr(image, "save", None)
    if not callable(save):
        raise RuntimeError("[EasyUseAnima] Pillow image writer is unavailable.")
    with temporary.binary_writer() as handle:
        save(handle, format=image_format, **options)
        handle.flush()


def _write_text(temporary: _OpenTemporary, value: str) -> None:
    with os.fdopen(
        os.dup(temporary.descriptor),
        "w",
        encoding="utf-8",
        newline="\n",
    ) as handle:
        handle.write(value)
        handle.flush()


def publish_image_transaction(
    directory: OutputDirectoryBinding,
    image: object,
    *,
    target_name: str,
    image_format: str,
    options: dict[str, object],
    sidecar_text: str | None,
) -> None:
    """Encode open temporaries and atomically publish without replacement."""

    image_temporary = directory.create_temporary()
    sidecar_temporary: _OpenTemporary | None = None
    image_identity: _FileIdentity | None = None
    sidecar_identity: _FileIdentity | None = None
    image_publish_started = False
    sidecar_publish_started = False
    image_rollback_confirmed = True
    sidecar_name = str(Path(target_name).with_suffix(".json"))
    try:
        _write_image(
            image_temporary,
            image,
            image_format=image_format,
            options=options,
        )
        directory.assert_temporary_identity(image_temporary)
        if sidecar_text is not None:
            sidecar_temporary = directory.create_temporary()
            _write_text(sidecar_temporary, sidecar_text)
            directory.assert_temporary_identity(sidecar_temporary)

        if sidecar_temporary is not None:
            sidecar_publish_started = True
            sidecar_identity = directory.link_no_replace(
                sidecar_temporary,
                sidecar_name,
            )
        image_publish_started = True
        image_identity = directory.link_no_replace(
            image_temporary,
            target_name,
        )
        if sidecar_temporary is not None:
            sidecar_temporary.keep()
        image_temporary.keep()
    except BaseException:
        if os.name != "nt" and image_publish_started:
            image_rollback_confirmed = directory._remove_name_if_owned(
                target_name,
                image_temporary.identity,
            )
        if (
            os.name != "nt"
            and image_rollback_confirmed
            and sidecar_publish_started
            and sidecar_temporary is not None
        ):
            directory._remove_name_if_owned(
                sidecar_name,
                sidecar_temporary.identity,
            )
        raise
    finally:
        if image_temporary.retain_on_close and sidecar_temporary is not None:
            try:
                sidecar_temporary.close()
            finally:
                image_temporary.close()
        else:
            try:
                image_cleanup_confirmed = image_temporary.close()
            except BaseException:
                if (
                    os.name == "nt"
                    and sidecar_identity is not None
                    and sidecar_temporary is not None
                ):
                    sidecar_temporary.keep()
                if sidecar_temporary is not None:
                    sidecar_temporary.close()
                raise
            if sidecar_temporary is not None:
                if (
                    os.name == "nt"
                    and not image_cleanup_confirmed
                    and sidecar_identity is not None
                ):
                    sidecar_temporary.keep()
                sidecar_temporary.close()

    try:
        if sidecar_identity is not None:
            directory.assert_published_identity(sidecar_name, sidecar_identity)
        directory.assert_published_identity(target_name, image_identity)
    except BaseException:
        image_rollback_confirmed = directory._remove_name_if_owned(
            target_name,
            image_identity,
        )
        if image_rollback_confirmed and sidecar_identity is not None:
            directory._remove_name_if_owned(sidecar_name, sidecar_identity)
        raise


__all__ = ()
