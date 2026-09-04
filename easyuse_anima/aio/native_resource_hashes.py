"""Inventory-bound resource discovery and contained SHA-256 caching."""

from __future__ import annotations

import hashlib
import json
import logging
import math
import os
import re
import tempfile
import threading
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import cast

logger = logging.getLogger("ComfyUI-EasyUseAnima")

_HASH_BLOCK_SIZE = 1024 * 1024
_HASH_CACHE_SCHEMA = 1
_HASH_CACHE_MAX_BYTES = 1024 * 1024
_HASH_CACHE_MAX_ENTRIES = 128
_HASH_CACHE_FILENAME = "resource-hashes.v1.json"
_MAX_LOCAL_EMBEDDINGS = 32
_MAX_MANUAL_HASHES = 30
_MAX_MANUAL_HASH_TEXT = 8_192
_EMBEDDING_RE = re.compile(r"embedding:([^,\s():]+)", re.IGNORECASE)
_SAFE_HASH_RE = re.compile(r"^[A-Za-z0-9_-]{1,128}$")
_HEX_HASH_RE = re.compile(r"^[0-9A-Fa-f]{8,128}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_CONTROL_RE = re.compile(r"[\x00-\x1f\x7f]")
_RESERVED_METADATA_KEYS = frozenset({"model"})
_HASH_CACHE_LOCK = threading.Lock()


@dataclass(frozen=True, slots=True)
class _ResourceHash:
    display_name: str
    metadata_key: str
    path: Path | None
    sha256: str
    weight: float | None = None
    preserve_hash: bool = False

    @property
    def metadata_hash(self) -> str:
        return self.sha256 if self.preserve_hash else self.sha256[:10]


def _supported_model_extensions() -> set[str]:
    try:
        import folder_paths  # type: ignore

        return set(getattr(folder_paths, "supported_pt_extensions", ())) | {".gguf"}
    except Exception:
        return {".safetensors", ".pt", ".ckpt", ".bin", ".pth", ".gguf"}


def _resource_name(value: str) -> str:
    filename = str(value or "").strip().replace("\\", "/").strip("/").rsplit("/", 1)[-1]
    stem, extension = os.path.splitext(filename)
    return stem if extension.casefold() in _supported_model_extensions() else filename


def _lora_metadata_name(value: str) -> str:
    normalized = str(value or "").strip().replace("\\", "/").strip("/")
    stem, extension = os.path.splitext(normalized)
    return stem if extension.casefold() in _supported_model_extensions() else normalized


def _resolve_resource_path(folder_names: Sequence[str], name: str) -> Path | None:
    if not str(name or "").strip():
        return None
    try:
        import folder_paths  # type: ignore
    except Exception:
        return None

    get_full_path = getattr(folder_paths, "get_full_path", None)
    if not callable(get_full_path):
        return None
    for folder_name in folder_names:
        try:
            value = get_full_path(folder_name, name)
        except Exception as exc:
            logger.warning(
                "[EasyUseAnima] Could not resolve %s resource %r: %s",
                folder_name,
                name,
                exc,
            )
            continue
        if not value:
            continue
        path = Path(str(value)).resolve(strict=False)
        if path.is_file():
            return path
    return None


def _hash_cache_path() -> Path | None:
    try:
        import folder_paths  # type: ignore
    except Exception:
        return None

    get_user_directory = getattr(folder_paths, "get_user_directory", None)
    if not callable(get_user_directory):
        return None
    try:
        user_root = Path(str(get_user_directory())).resolve(strict=True)
        cache_parent = (user_root / "easyuse_anima" / "cache").resolve(strict=False)
        cache_parent.relative_to(user_root)
    except (OSError, RuntimeError, ValueError):
        logger.warning(
            "[EasyUseAnima] Persistent resource hash cache is unavailable; "
            "continuing with the in-memory cache."
        )
        return None
    return cache_parent / _HASH_CACHE_FILENAME


def _read_hash_cache(cache_path: Path) -> dict[str, dict[str, int | str]]:
    if not cache_path.exists():
        return {}
    if cache_path.is_symlink():
        raise OSError("resource hash cache path must not be a symbolic link")
    if cache_path.stat().st_size > _HASH_CACHE_MAX_BYTES:
        raise ValueError("resource hash cache exceeds its size limit")
    payload = json.loads(cache_path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping) or payload.get("version") != _HASH_CACHE_SCHEMA:
        raise ValueError("resource hash cache schema is invalid")
    raw_entries = payload.get("entries")
    if not isinstance(raw_entries, Mapping):
        raise ValueError("resource hash cache entries are invalid")

    entries: dict[str, dict[str, int | str]] = {}
    for key, raw_entry in list(raw_entries.items())[-_HASH_CACHE_MAX_ENTRIES:]:
        if not isinstance(key, str) or not _SHA256_RE.fullmatch(key):
            continue
        if not isinstance(raw_entry, Mapping):
            continue
        size = raw_entry.get("size")
        modified_ns = raw_entry.get("modified_ns")
        changed_ns = raw_entry.get("changed_ns")
        device = raw_entry.get("device")
        inode = raw_entry.get("inode")
        sha256 = raw_entry.get("sha256")
        if (
            isinstance(size, int)
            and not isinstance(size, bool)
            and size >= 0
            and isinstance(modified_ns, int)
            and not isinstance(modified_ns, bool)
            and modified_ns >= 0
            and isinstance(changed_ns, int)
            and not isinstance(changed_ns, bool)
            and changed_ns >= 0
            and isinstance(device, int)
            and not isinstance(device, bool)
            and device >= 0
            and isinstance(inode, int)
            and not isinstance(inode, bool)
            and inode >= 0
            and isinstance(sha256, str)
            and _SHA256_RE.fullmatch(sha256.casefold())
        ):
            entries[key] = {
                "size": size,
                "modified_ns": modified_ns,
                "changed_ns": changed_ns,
                "device": device,
                "inode": inode,
                "sha256": sha256.casefold(),
            }
    return entries


def _atomic_write_hash_cache(
    cache_path: Path,
    entries: Mapping[str, Mapping[str, int | str]],
) -> None:
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    resolved_parent = cache_path.parent.resolve(strict=True)
    verified_path = _hash_cache_path()
    if (
        verified_path is None
        or os.path.normcase(str(verified_path.parent.resolve(strict=True)))
        != os.path.normcase(str(resolved_parent))
        or verified_path.name != cache_path.name
    ):
        raise OSError("resource hash cache escaped its user-data root")
    target = verified_path
    if target.is_symlink():
        raise OSError("resource hash cache path must not be a symbolic link")
    value = json.dumps(
        {"version": _HASH_CACHE_SCHEMA, "entries": dict(entries)},
        allow_nan=False,
        ensure_ascii=True,
        separators=(",", ":"),
    )
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=".easyuse-anima-hashes-",
        suffix=".tmp",
        dir=resolved_parent,
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(value)
        os.replace(temporary, target)
    finally:
        temporary.unlink(missing_ok=True)


def _hash_cache_key(path: Path) -> str:
    normalized = os.path.normcase(str(path.resolve(strict=True)))
    return hashlib.sha256(normalized.encode("utf-8", errors="surrogatepass")).hexdigest()


def _new_hash_progress(total: int) -> object | None:
    try:
        from comfy.utils import ProgressBar  # type: ignore

        return ProgressBar(total)
    except Exception:
        return None


def _stat_revision(stat: os.stat_result) -> tuple[int, int, int, int, int]:
    return (
        stat.st_size,
        stat.st_mtime_ns,
        stat.st_ctime_ns,
        stat.st_dev,
        stat.st_ino,
    )


def _calculate_file_sha256(
    path: Path,
    size: int,
    modified_ns: int,
    changed_ns: int,
    device: int,
    inode: int,
) -> str:
    del changed_ns
    digest = hashlib.sha256()
    progress = _new_hash_progress(size)
    consumed = 0
    with path.open("rb") as handle:
        before = os.fstat(handle.fileno())
        expected_stable_fields = (size, modified_ns, device, inode)
        before_stable_fields = (
            before.st_size,
            before.st_mtime_ns,
            before.st_dev,
            before.st_ino,
        )
        if before_stable_fields != expected_stable_fields:
            raise OSError("resource changed before hashing began")
        for block in iter(lambda: handle.read(_HASH_BLOCK_SIZE), b""):
            digest.update(block)
            consumed += len(block)
            if progress is not None:
                try:
                    update_absolute = getattr(progress, "update_absolute")
                    update_absolute(consumed, size)
                except Exception:
                    progress = None
        after = os.fstat(handle.fileno())
        after_stable_fields = (
            after.st_size,
            after.st_mtime_ns,
            after.st_dev,
            after.st_ino,
        )
        if (
            after_stable_fields != expected_stable_fields
            or after.st_ctime_ns != before.st_ctime_ns
        ):
            raise OSError("resource changed while it was being hashed")
    return digest.hexdigest()


@lru_cache(maxsize=128)
def _hash_file_revision(
    path_text: str,
    size: int,
    modified_ns: int,
    changed_ns: int,
    device: int,
    inode: int,
) -> str:
    path = Path(path_text)
    cache_key = _hash_cache_key(path)
    with _HASH_CACHE_LOCK:
        cache_path = _hash_cache_path()
        entries: dict[str, dict[str, int | str]] = {}
        if cache_path is not None:
            try:
                entries = _read_hash_cache(cache_path)
            except (OSError, UnicodeError, ValueError, json.JSONDecodeError) as exc:
                logger.warning(
                    "[EasyUseAnima] Ignoring invalid persistent resource hash cache (%s).",
                    type(exc).__name__,
                )
        cached = entries.get(cache_key)
        if (
            cached is not None
            and cached.get("size") == size
            and cached.get("modified_ns") == modified_ns
            and cached.get("changed_ns") == changed_ns
            and cached.get("device") == device
            and cached.get("inode") == inode
        ):
            cached_hash = cached.get("sha256")
            if isinstance(cached_hash, str) and _SHA256_RE.fullmatch(cached_hash):
                return cached_hash

        sha256 = _calculate_file_sha256(
            path,
            size,
            modified_ns,
            changed_ns,
            device,
            inode,
        )
        if cache_path is not None:
            entries.pop(cache_key, None)
            entries[cache_key] = {
                "size": size,
                "modified_ns": modified_ns,
                "changed_ns": changed_ns,
                "device": device,
                "inode": inode,
                "sha256": sha256,
            }
            while len(entries) > _HASH_CACHE_MAX_ENTRIES:
                entries.pop(next(iter(entries)))
            try:
                _atomic_write_hash_cache(cache_path, entries)
            except OSError as exc:
                logger.warning(
                    "[EasyUseAnima] Could not update the persistent resource hash cache (%s); "
                    "continuing with the calculated hash.",
                    type(exc).__name__,
                )
        return sha256


def _hash_file(path: Path) -> str:
    resolved = path.resolve(strict=True)
    stat = resolved.stat()
    return _hash_file_revision(str(resolved), *_stat_revision(stat))


def _safe_inventory_name(value: object) -> str:
    name = str(value or "").strip().replace("\\", "/")
    posix_path = PurePosixPath(name)
    windows_path = PureWindowsPath(name)
    if (
        not name
        or len(name) > 512
        or _CONTROL_RE.search(name)
        or name.startswith("/")
        or name.endswith("/")
        or posix_path.is_absolute()
        or windows_path.drive
        or windows_path.root
        or any(part in {"", ".", ".."} or ":" in part for part in posix_path.parts)
    ):
        return ""
    return "/".join(posix_path.parts)


def _without_supported_extension(value: str) -> str:
    suffix = PurePosixPath(value).suffix
    if suffix.casefold() in _supported_model_extensions():
        return value[:-len(suffix)]
    return value


def _inventory_resource_name(folder_name: str, requested_name: str) -> str | None:
    requested = _safe_inventory_name(requested_name)
    if not requested:
        return None
    try:
        import folder_paths  # type: ignore
    except Exception:
        return None
    get_filename_list = getattr(folder_paths, "get_filename_list", None)
    if not callable(get_filename_list):
        return None
    try:
        values = cast(Iterable[object], get_filename_list(folder_name))
        inventory = [
            safe_name
            for value in values
            if (safe_name := _safe_inventory_name(value))
        ]
    except Exception as exc:
        logger.warning(
            "[EasyUseAnima] Could not read the %s inventory: %s",
            folder_name,
            exc,
        )
        return None

    requested_folded = requested.casefold()
    exact = [name for name in inventory if name.casefold() == requested_folded]
    if len(exact) == 1:
        return exact[0]
    requested_stem = _without_supported_extension(requested).casefold()
    stem_matches = [
        name
        for name in inventory
        if _without_supported_extension(name).casefold() == requested_stem
    ]
    if len(stem_matches) == 1:
        return stem_matches[0]
    if "/" not in requested:
        basename_matches = [
            name
            for name in inventory
            if PurePosixPath(_without_supported_extension(name)).name.casefold()
            == requested_stem
        ]
        if len(basename_matches) == 1:
            return basename_matches[0]
        if len(basename_matches) > 1:
            logger.warning(
                "[EasyUseAnima] Embedding reference %r is ambiguous; skipping its hash.",
                requested_name,
            )
    return None


def _weighted_prompt_segments(prompt: str) -> Iterable[tuple[str, float]]:
    value = str(prompt or "")
    try:
        from comfy.sd1_clip import (  # type: ignore
            escape_important,
            token_weights,
            unescape_important,
        )

        parsed = token_weights(escape_important(value), 1.0)
    except Exception:
        return ((value, 1.0),)

    segments: list[tuple[str, float]] = []
    try:
        for text, weight in parsed:
            numeric_weight = float(weight)
            if not math.isfinite(numeric_weight):
                numeric_weight = 1.0
            segments.append((str(unescape_important(text)), numeric_weight))
    except Exception:
        return ((value, 1.0),)
    return tuple(segments)


def _embedding_resource_hashes(prompts: Sequence[str]) -> list[_ResourceHash]:
    resources: list[_ResourceHash] = []
    seen_names: set[str] = set()
    for prompt in prompts:
        for segment, weight in _weighted_prompt_segments(prompt):
            for match in _EMBEDDING_RE.finditer(segment):
                if len(resources) >= _MAX_LOCAL_EMBEDDINGS:
                    logger.warning(
                        "[EasyUseAnima] Ignoring embedding references beyond the %d-resource limit.",
                        _MAX_LOCAL_EMBEDDINGS,
                    )
                    return resources
                requested_name = match.group(1)
                inventory_name = _inventory_resource_name("embeddings", requested_name)
                if inventory_name is None:
                    continue
                metadata_name = _lora_metadata_name(inventory_name)
                normalized_name = metadata_name.casefold()
                if not metadata_name or normalized_name in seen_names:
                    continue
                path = _resolve_resource_path(("embeddings",), inventory_name)
                if path is None:
                    continue
                try:
                    sha256 = _hash_file(path)
                except OSError as exc:
                    logger.warning(
                        "[EasyUseAnima] Could not hash embedding %r; continuing without its hash: %s",
                        inventory_name,
                        exc,
                    )
                    continue
                seen_names.add(normalized_name)
                resources.append(
                    _ResourceHash(
                        display_name=metadata_name,
                        metadata_key=f"embed:{metadata_name}",
                        path=path,
                        sha256=sha256,
                        weight=weight,
                    )
                )
    return resources


def _local_resource_hashes(
    modelname: str,
    applied_loras: object,
    prompts: Sequence[str] = (),
) -> list[_ResourceHash]:
    resources: list[_ResourceHash] = []
    model_path = _resolve_resource_path(("diffusion_models", "checkpoints"), modelname)
    if model_path is not None:
        try:
            resources.append(
                _ResourceHash(
                    display_name=_resource_name(modelname),
                    metadata_key="model",
                    path=model_path,
                    sha256=_hash_file(model_path),
                )
            )
        except OSError as exc:
            logger.warning(
                "[EasyUseAnima] Could not hash model %r; continuing without its hash: %s",
                modelname,
                exc,
            )

    values = applied_loras if isinstance(applied_loras, (list, tuple)) else ()
    seen_names: set[str] = set()
    for item in values:
        if not isinstance(item, Mapping):
            continue
        source_name = str(item.get("name") or "").strip()
        metadata_name = _lora_metadata_name(source_name)
        if not metadata_name or metadata_name.casefold() in seen_names:
            continue
        seen_names.add(metadata_name.casefold())
        lora_path = _resolve_resource_path(("loras",), source_name)
        if lora_path is None:
            logger.warning(
                "[EasyUseAnima] Could not locate LoRA %r; continuing without its Civitai hash.",
                source_name,
            )
            continue
        try:
            strength = float(item.get("strength_model", 1.0))
        except (TypeError, ValueError):
            strength = 1.0
        if not math.isfinite(strength):
            strength = 1.0
        try:
            sha256 = _hash_file(lora_path)
        except OSError as exc:
            logger.warning(
                "[EasyUseAnima] Could not hash LoRA %r; continuing without its hash: %s",
                source_name,
                exc,
            )
            continue
        resources.append(
            _ResourceHash(
                display_name=metadata_name,
                metadata_key=f"LORA:{metadata_name}",
                path=lora_path,
                sha256=sha256,
                weight=strength,
            )
        )
    resources.extend(_embedding_resource_hashes(prompts))
    return resources


def _manual_resource_hashes(value: str) -> list[_ResourceHash]:
    text = str(value or "")[:_MAX_MANUAL_HASH_TEXT]
    resources: list[_ResourceHash] = []
    unnamed_index = 0
    seen_hashes: set[str] = set()
    for raw_entry in text.replace("\r", "\n").replace("\n", ",").split(","):
        entry = raw_entry.strip()
        if not entry:
            continue
        pieces = [part.strip() for part in entry.split(":")]
        if not all(pieces):
            logger.warning("[EasyUseAnima] Skipping malformed additional Civitai hash entry: %r", entry)
            continue
        if len(pieces) > 3:
            logger.warning("[EasyUseAnima] Skipping ambiguous additional Civitai hash entry: %r", entry)
            continue
        weight: float | None = None
        if len(pieces) == 3:
            try:
                weight = float(pieces[-1])
            except ValueError:
                logger.warning("[EasyUseAnima] Skipping ambiguous additional Civitai hash entry: %r", entry)
                continue
            if not math.isfinite(weight):
                logger.warning("[EasyUseAnima] Skipping non-finite additional Civitai hash weight: %r", entry)
                continue
            name, hash_value = pieces[0], pieces[1]
        elif len(pieces) == 2:
            first, second = pieces
            try:
                shorthand_weight = float(second)
            except ValueError:
                shorthand_weight = None
            if shorthand_weight is not None and _HEX_HASH_RE.fullmatch(first):
                if not math.isfinite(shorthand_weight):
                    logger.warning("[EasyUseAnima] Skipping non-finite additional Civitai hash weight: %r", entry)
                    continue
                unnamed_index += 1
                name = f"manual{unnamed_index}"
                hash_value = first
                weight = shorthand_weight
            else:
                name, hash_value = first, second
        else:
            unnamed_index += 1
            name = f"manual{unnamed_index}"
            hash_value = pieces[0]
        if not name or _CONTROL_RE.search(name) or not _SAFE_HASH_RE.fullmatch(hash_value):
            logger.warning("[EasyUseAnima] Skipping invalid additional Civitai hash entry: %r", entry)
            continue
        if name.casefold() in _RESERVED_METADATA_KEYS:
            logger.warning(
                "[EasyUseAnima] Skipping additional Civitai hash entry with reserved key %r.",
                name,
            )
            continue
        normalized_hash = hash_value.casefold()
        if normalized_hash in seen_hashes:
            continue
        seen_hashes.add(normalized_hash)
        resources.append(
            _ResourceHash(
                display_name=name,
                metadata_key=name,
                path=None,
                sha256=hash_value,
                weight=weight,
                preserve_hash=True,
            )
        )
        if len(resources) >= _MAX_MANUAL_HASHES:
            break
    return resources


__all__ = ()
