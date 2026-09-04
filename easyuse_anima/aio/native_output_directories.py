"""Parent-bound directory creation for native image output paths."""

from __future__ import annotations

import ctypes
import logging
import os
import stat as stat_module
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger("ComfyUI-EasyUseAnima")


class OutputDirectoryIntegrityError(OSError):
    """The output directory tree could not be bound without following links."""


@dataclass(frozen=True, slots=True)
class PreparedOutputDirectory:
    """A verified output directory whose ancestry handles remain open."""

    path: Path
    identity: tuple[int, int]
    directory_descriptor: int | None = None
    windows_handle: int | None = None


@dataclass(frozen=True, slots=True)
class _DirectoryIdentity:
    device: int
    inode: int


@dataclass(slots=True)
class _PosixDirectory:
    descriptor: int


@dataclass(slots=True)
class _WindowsDirectory:
    handle: int
    name: str
    identity: _DirectoryIdentity
    created: bool


def _identity_from_stat(value: os.stat_result) -> _DirectoryIdentity:
    return _DirectoryIdentity(int(value.st_dev), int(value.st_ino))


def _existing_anchor(path: Path) -> tuple[Path, tuple[str, ...]]:
    requested = Path(os.path.abspath(os.fspath(path)))
    missing: list[str] = []
    probe = requested
    while True:
        try:
            anchor = probe.resolve(strict=True)
            return anchor, tuple(reversed(missing))
        except FileNotFoundError:
            parent = probe.parent
            if parent == probe:
                raise
            missing.append(probe.name)
            probe = parent


def _require_posix_directory_operations() -> None:
    required = (os.open, os.mkdir, os.stat)
    if (
        any(operation not in os.supports_dir_fd for operation in required)
        or not getattr(os, "O_DIRECTORY", 0)
        or not getattr(os, "O_NOFOLLOW", 0)
    ):
        raise OutputDirectoryIntegrityError(
            "secure parent-relative directory operations are unavailable"
        )


def _posix_directory_flags() -> int:
    return (
        os.O_RDONLY
        | getattr(os, "O_DIRECTORY", 0)
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_NOFOLLOW", 0)
    )


def _assert_posix_directory(descriptor: int) -> _DirectoryIdentity:
    current = os.fstat(descriptor)
    if not stat_module.S_ISDIR(current.st_mode):
        raise OutputDirectoryIntegrityError("output path component is not a directory")
    return _identity_from_stat(current)


def _open_or_create_posix_directory(
    parent_descriptor: int,
    name: str,
    *,
    expected_parent: Path,
) -> int:
    flags = _posix_directory_flags()
    _verify_posix_path_identity(expected_parent, parent_descriptor)
    try:
        descriptor = os.open(name, flags, dir_fd=parent_descriptor)
    except FileNotFoundError:
        _verify_posix_path_identity(expected_parent, parent_descriptor)
        try:
            os.mkdir(name, 0o777, dir_fd=parent_descriptor)
        except FileExistsError:
            pass
        descriptor = os.open(name, flags, dir_fd=parent_descriptor)
    _verify_posix_path_identity(expected_parent, parent_descriptor)
    return descriptor


def _verify_posix_path_identity(
    path: Path,
    descriptor: int,
) -> _DirectoryIdentity:
    opened = _assert_posix_directory(descriptor)
    try:
        named = path.stat(follow_symlinks=False)
        resolved = path.resolve(strict=True)
    except OSError as exc:
        raise OutputDirectoryIntegrityError(
            "output directory changed during creation"
        ) from exc
    if (
        not stat_module.S_ISDIR(named.st_mode)
        or stat_module.S_ISLNK(named.st_mode)
        or _identity_from_stat(named) != opened
        or resolved != path
    ):
        raise OutputDirectoryIntegrityError(
            "output directory changed during creation"
        )
    return opened


def _close_posix_directories(entries: list[_PosixDirectory]) -> None:
    for entry in reversed(entries):
        os.close(entry.descriptor)


@contextmanager
def _resolve_posix_directory(
    anchor: Path,
    root_parts: tuple[str, ...],
    output_parts: tuple[str, ...],
) -> Iterator[PreparedOutputDirectory]:
    _require_posix_directory_operations()
    try:
        anchor_descriptor = os.open(anchor, _posix_directory_flags())
    except OSError as exc:
        raise OutputDirectoryIntegrityError(
            "output directory anchor could not be opened safely"
        ) from exc
    entries: list[_PosixDirectory] = []
    expected_root = anchor.joinpath(*root_parts)
    expected_final = expected_root.joinpath(*output_parts)
    try:
        anchor_identity = _assert_posix_directory(anchor_descriptor)
        _verify_posix_path_identity(anchor, anchor_descriptor)
        current_descriptor = anchor_descriptor
        root_descriptor = anchor_descriptor
        all_parts = root_parts + output_parts
        for index, name in enumerate(all_parts):
            expected_parent = anchor.joinpath(*all_parts[:index])
            descriptor = _open_or_create_posix_directory(
                current_descriptor,
                name,
                expected_parent=expected_parent,
            )
            try:
                _assert_posix_directory(descriptor)
            except BaseException:
                os.close(descriptor)
                raise
            entries.append(
                _PosixDirectory(
                    descriptor=descriptor,
                )
            )
            current_descriptor = descriptor
            if index + 1 == len(root_parts):
                root_descriptor = descriptor

        if not root_parts:
            root_descriptor = anchor_descriptor
        if _assert_posix_directory(anchor_descriptor) != anchor_identity:
            raise OutputDirectoryIntegrityError(
                "output directory anchor changed during creation"
            )
        _verify_posix_path_identity(expected_root, root_descriptor)
        final_identity = _verify_posix_path_identity(
            expected_final,
            current_descriptor,
        )
        prepared = PreparedOutputDirectory(
            path=expected_final,
            identity=(final_identity.device, final_identity.inode),
            directory_descriptor=current_descriptor,
        )
    except OutputDirectoryIntegrityError:
        _close_posix_directories(entries)
        os.close(anchor_descriptor)
        raise
    except OSError as exc:
        _close_posix_directories(entries)
        os.close(anchor_descriptor)
        raise OutputDirectoryIntegrityError(
            "output directory could not be created safely"
        ) from exc
    except BaseException:
        _close_posix_directories(entries)
        os.close(anchor_descriptor)
        raise

    try:
        yield prepared
    finally:
        _close_posix_directories(entries)
        os.close(anchor_descriptor)


def _windows_extended_path(path: Path) -> str:
    value = os.path.abspath(os.fspath(path))
    if value.startswith("\\\\?\\"):
        return value
    if value.startswith("\\\\"):
        return "\\\\?\\UNC\\" + value[2:]
    return "\\\\?\\" + value


def _close_windows_handle(handle: int | None) -> None:
    if handle is None:
        return
    from ctypes import wintypes

    close_handle = ctypes.WinDLL("kernel32", use_last_error=True).CloseHandle
    close_handle.argtypes = (wintypes.HANDLE,)
    close_handle.restype = wintypes.BOOL
    close_handle(handle)


def _open_windows_anchor(
    path: Path,
    *,
    allow_child_creation: bool = False,
    share_delete: bool = False,
) -> int:
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
    file_list_directory = 0x0001
    file_add_subdirectory = 0x0004
    file_traverse = 0x0020
    file_read_attributes = 0x0080
    synchronize = 0x00100000
    share_read_write = 0x00000001 | 0x00000002
    if share_delete:
        share_read_write |= 0x00000004
    open_existing = 3
    backup_semantics = 0x02000000
    open_reparse_point = 0x00200000
    desired_access = (
        file_list_directory
        | file_traverse
        | file_read_attributes
        | synchronize
    )
    if allow_child_creation:
        desired_access |= file_add_subdirectory
    handle = create_file(
        _windows_extended_path(path),
        desired_access,
        share_read_write,
        None,
        open_existing,
        backup_semantics | open_reparse_point,
        None,
    )
    invalid_handle = ctypes.c_void_p(-1).value
    if handle in (None, invalid_handle):
        raise ctypes.WinError(ctypes.get_last_error())
    return int(handle)


def _nt_open_relative_directory(
    parent_handle: int,
    name: str,
    *,
    create: bool,
    allow_child_creation: bool,
) -> int:
    from ctypes import wintypes

    class UnicodeString(ctypes.Structure):
        _fields_ = (
            ("Length", wintypes.USHORT),
            ("MaximumLength", wintypes.USHORT),
            ("Buffer", wintypes.LPWSTR),
        )

    class ObjectAttributes(ctypes.Structure):
        _fields_ = (
            ("Length", wintypes.ULONG),
            ("RootDirectory", wintypes.HANDLE),
            ("ObjectName", ctypes.POINTER(UnicodeString)),
            ("Attributes", wintypes.ULONG),
            ("SecurityDescriptor", wintypes.LPVOID),
            ("SecurityQualityOfService", wintypes.LPVOID),
        )

    class IoStatusBlockUnion(ctypes.Union):
        _fields_ = (("Status", wintypes.LONG), ("Pointer", wintypes.LPVOID))

    class IoStatusBlock(ctypes.Structure):
        _anonymous_ = ("value",)
        _fields_ = (("value", IoStatusBlockUnion), ("Information", ctypes.c_size_t))

    name_buffer = ctypes.create_unicode_buffer(name)
    name_bytes = len(name.encode("utf-16-le"))
    object_name = UnicodeString(
        name_bytes,
        name_bytes + 2,
        ctypes.cast(name_buffer, wintypes.LPWSTR),
    )
    attributes = ObjectAttributes(
        ctypes.sizeof(ObjectAttributes),
        parent_handle,
        ctypes.pointer(object_name),
        0x00000040,
        None,
        None,
    )
    status_block = IoStatusBlock()
    handle = wintypes.HANDLE()
    ntdll = ctypes.WinDLL("ntdll")
    nt_create_file = ntdll.NtCreateFile
    nt_create_file.argtypes = (
        ctypes.POINTER(wintypes.HANDLE),
        wintypes.DWORD,
        ctypes.POINTER(ObjectAttributes),
        ctypes.POINTER(IoStatusBlock),
        wintypes.LPVOID,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.LPVOID,
        wintypes.DWORD,
    )
    nt_create_file.restype = wintypes.LONG
    desired_access = 0x0001 | 0x0020 | 0x0080 | 0x00100000
    if allow_child_creation:
        desired_access |= 0x0004
    if create:
        desired_access |= 0x00010000
    status = int(
        nt_create_file(
            ctypes.byref(handle),
            desired_access,
            ctypes.byref(attributes),
            ctypes.byref(status_block),
            None,
            0x00000010,
            0x00000001 | 0x00000002,
            2 if create else 1,
            0x00000001 | 0x00000020 | 0x00200000,
            None,
            0,
        )
    )
    if status >= 0:
        if handle.value is None:
            raise OutputDirectoryIntegrityError(
                "Windows returned an empty output directory handle"
            )
        return int(handle.value)

    unsigned_status = status & 0xFFFFFFFF
    if unsigned_status in {0xC0000034, 0xC000003A}:
        raise FileNotFoundError(name)
    if unsigned_status == 0xC0000035:
        raise FileExistsError(name)
    rtl_status_to_error = ntdll.RtlNtStatusToDosError
    rtl_status_to_error.argtypes = (wintypes.LONG,)
    rtl_status_to_error.restype = wintypes.ULONG
    raise ctypes.WinError(int(rtl_status_to_error(status)))


def _open_or_create_windows_directory(
    parent_handle: int,
    name: str,
    *,
    allow_child_creation: bool,
) -> tuple[int, bool]:
    try:
        return (
            _nt_open_relative_directory(
                parent_handle,
                name,
                create=False,
                allow_child_creation=allow_child_creation,
            ),
            False,
        )
    except FileNotFoundError:
        pass
    try:
        return (
            _nt_open_relative_directory(
                parent_handle,
                name,
                create=True,
                allow_child_creation=allow_child_creation,
            ),
            True,
        )
    except FileExistsError:
        return (
            _nt_open_relative_directory(
                parent_handle,
                name,
                create=False,
                allow_child_creation=allow_child_creation,
            ),
            False,
        )


def _windows_directory_information(handle: int) -> tuple[_DirectoryIdentity, int]:
    from ctypes import wintypes

    class FileTime(ctypes.Structure):
        _fields_ = (("Low", wintypes.DWORD), ("High", wintypes.DWORD))

    class ByHandleFileInformation(ctypes.Structure):
        _fields_ = (
            ("FileAttributes", wintypes.DWORD),
            ("CreationTime", FileTime),
            ("LastAccessTime", FileTime),
            ("LastWriteTime", FileTime),
            ("VolumeSerialNumber", wintypes.DWORD),
            ("FileSizeHigh", wintypes.DWORD),
            ("FileSizeLow", wintypes.DWORD),
            ("NumberOfLinks", wintypes.DWORD),
            ("FileIndexHigh", wintypes.DWORD),
            ("FileIndexLow", wintypes.DWORD),
        )

    value = ByHandleFileInformation()
    get_information = ctypes.WinDLL(
        "kernel32", use_last_error=True
    ).GetFileInformationByHandle
    get_information.argtypes = (
        wintypes.HANDLE,
        ctypes.POINTER(ByHandleFileInformation),
    )
    get_information.restype = wintypes.BOOL
    if not get_information(handle, ctypes.byref(value)):
        raise ctypes.WinError(ctypes.get_last_error())
    identity = _DirectoryIdentity(
        int(value.VolumeSerialNumber),
        (int(value.FileIndexHigh) << 32) | int(value.FileIndexLow),
    )
    return identity, int(value.FileAttributes)


def _assert_windows_directory(handle: int) -> _DirectoryIdentity:
    identity, attributes = _windows_directory_information(handle)
    if not attributes & 0x00000010:
        raise OutputDirectoryIntegrityError("output path component is not a directory")
    if attributes & 0x00000400:
        raise OutputDirectoryIntegrityError(
            "output path component is a Windows reparse point"
        )
    return identity


def _windows_handle_path(handle: int) -> Path:
    from ctypes import wintypes

    get_final_path = ctypes.WinDLL(
        "kernel32", use_last_error=True
    ).GetFinalPathNameByHandleW
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


def _same_windows_path(left: Path, right: Path) -> bool:
    return os.path.normcase(os.path.normpath(str(left))) == os.path.normcase(
        os.path.normpath(str(right))
    )


def _verify_windows_path_identity(
    path: Path,
    handle: int,
) -> _DirectoryIdentity:
    opened_identity = _assert_windows_directory(handle)
    verification_handle: int | None = None
    try:
        verification_handle = _open_windows_anchor(path, share_delete=True)
        if _assert_windows_directory(verification_handle) != opened_identity:
            raise OutputDirectoryIntegrityError(
                "output directory changed during creation"
            )
        if not _same_windows_path(_windows_handle_path(handle), path):
            raise OutputDirectoryIntegrityError(
                "output directory moved during creation"
            )
        named = path.stat(follow_symlinks=False)
        if not stat_module.S_ISDIR(named.st_mode):
            raise OutputDirectoryIntegrityError(
                "output directory name is not a directory"
            )
        return _identity_from_stat(named)
    except OutputDirectoryIntegrityError:
        raise
    except OSError as exc:
        raise OutputDirectoryIntegrityError(
            "output directory changed during creation"
        ) from exc
    finally:
        _close_windows_handle(verification_handle)


def _delete_windows_directory_handle(handle: int) -> None:
    from ctypes import wintypes

    class FileDispositionInfo(ctypes.Structure):
        _fields_ = (("DeleteFile", ctypes.c_ubyte),)

    value = FileDispositionInfo(1)
    set_information = ctypes.WinDLL(
        "kernel32", use_last_error=True
    ).SetFileInformationByHandle
    set_information.argtypes = (
        wintypes.HANDLE,
        ctypes.c_int,
        wintypes.LPVOID,
        wintypes.DWORD,
    )
    set_information.restype = wintypes.BOOL
    if not set_information(
        handle,
        4,
        ctypes.byref(value),
        ctypes.sizeof(value),
    ):
        raise ctypes.WinError(ctypes.get_last_error())


def _cleanup_windows_directories(entries: list[_WindowsDirectory]) -> None:
    for entry in reversed(entries):
        try:
            if (
                entry.created
                and _assert_windows_directory(entry.handle) == entry.identity
            ):
                _delete_windows_directory_handle(entry.handle)
        except OSError as exc:
            logger.warning(
                "[EasyUseAnima] Native output directory cleanup failed (%s).",
                type(exc).__name__,
            )
        finally:
            _close_windows_handle(entry.handle)


def _close_windows_directories(entries: list[_WindowsDirectory]) -> None:
    for entry in reversed(entries):
        _close_windows_handle(entry.handle)


@contextmanager
def _resolve_windows_directory(
    anchor: Path,
    root_parts: tuple[str, ...],
    output_parts: tuple[str, ...],
) -> Iterator[PreparedOutputDirectory]:
    all_parts = root_parts + output_parts
    anchor_handle = _open_windows_anchor(
        anchor,
        allow_child_creation=bool(all_parts),
    )
    entries: list[_WindowsDirectory] = []
    expected_root = anchor.joinpath(*root_parts)
    expected_final = expected_root.joinpath(*output_parts)
    try:
        anchor_identity = _assert_windows_directory(anchor_handle)
        _verify_windows_path_identity(anchor, anchor_handle)
        current_handle = anchor_handle
        root_handle = anchor_handle
        for index, name in enumerate(all_parts):
            handle, created = _open_or_create_windows_directory(
                current_handle,
                name,
                allow_child_creation=index + 1 < len(all_parts),
            )
            try:
                identity = _assert_windows_directory(handle)
            except BaseException:
                if created:
                    try:
                        _delete_windows_directory_handle(handle)
                    except OSError:
                        pass
                _close_windows_handle(handle)
                raise
            entries.append(
                _WindowsDirectory(
                    handle=handle,
                    name=name,
                    identity=identity,
                    created=created,
                )
            )
            current_handle = handle
            if index + 1 == len(root_parts):
                root_handle = handle

        if not root_parts:
            root_handle = anchor_handle
        if _assert_windows_directory(anchor_handle) != anchor_identity:
            raise OutputDirectoryIntegrityError(
                "output directory anchor changed during creation"
            )
        _verify_windows_path_identity(expected_root, root_handle)
        final_identity = _verify_windows_path_identity(
            expected_final,
            current_handle,
        )
        prepared = PreparedOutputDirectory(
            path=_windows_handle_path(current_handle),
            identity=(final_identity.device, final_identity.inode),
            windows_handle=current_handle,
        )
    except OutputDirectoryIntegrityError:
        _cleanup_windows_directories(entries)
        _close_windows_handle(anchor_handle)
        raise
    except OSError as exc:
        _cleanup_windows_directories(entries)
        _close_windows_handle(anchor_handle)
        raise OutputDirectoryIntegrityError(
            "output directory could not be created safely"
        ) from exc
    except BaseException:
        _cleanup_windows_directories(entries)
        _close_windows_handle(anchor_handle)
        raise

    try:
        yield prepared
    finally:
        _close_windows_directories(entries)
        _close_windows_handle(anchor_handle)


@contextmanager
def prepare_output_directory(
    output_root: Path,
    parts: Sequence[str],
) -> Iterator[PreparedOutputDirectory]:
    """Hold the verified root-to-output chain open for the caller's operation."""

    anchor, root_parts = _existing_anchor(Path(output_root))
    output_parts = tuple(str(part) for part in parts)
    resolver = (
        _resolve_windows_directory
        if os.name == "nt"
        else _resolve_posix_directory
    )
    with resolver(anchor, root_parts, output_parts) as prepared:
        yield prepared


def resolve_output_directory(output_root: Path, parts: Sequence[str]) -> Path:
    """Create ``parts`` beneath ``output_root`` while holding each parent open."""

    with prepare_output_directory(output_root, parts) as prepared:
        return prepared.path


__all__ = ()
