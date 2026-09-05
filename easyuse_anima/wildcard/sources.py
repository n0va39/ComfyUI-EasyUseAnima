"""Wildcard root discovery, source metadata, and TXT/YAML parsing."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path

try:
    import yaml
except Exception:  # pragma: no cover - YAML files are skipped without PyYAML.
    yaml = None

from ..infrastructure.filesystem.paths import USER_DATA_DIR
from .models import WildcardOption

WILDCARD_DIR_NAME = "wildcards"
DEFAULT_TEST_WILDCARD_FILE = "easyuse_anima_test.txt"
DEFAULT_TEST_WILDCARD_TEXT = (
    "# EasyUse Anima test wildcard\nsimple wildcard\nanima wildcard\n"
)
WILDCARD_EXTENSIONS = {".txt", ".yaml", ".yml"}

# Per-source limits apply before creating options. Reference/character costs
# include temporary aggregates and every published parent alias, not only leaves.
MAX_YAML_SOURCE_DEPTH = 64
MAX_YAML_SOURCE_VISITS = 65_536
MAX_YAML_SOURCE_OPTION_REFERENCES = 65_536
MAX_YAML_SOURCE_OUTPUT_CHARACTERS = 8 * 1024 * 1024

__all__ = (
    "WILDCARD_DIR_NAME",
    "DEFAULT_TEST_WILDCARD_FILE",
    "DEFAULT_TEST_WILDCARD_TEXT",
    "WILDCARD_EXTENSIONS",
    "default_wildcard_root",
    "ensure_default_wildcard_root",
    "parse_wildcard_extra_paths",
    "resolve_wildcard_roots",
)

WEIGHT_PREFIX_RE = re.compile(
    r"^\s*([+-]?(?:\d+(?:\.\d*)?|\.\d+))::(.*)$",
    re.DOTALL,
)


@dataclass(frozen=True)
class _WildcardSourceFile:
    root_index: int
    root: str
    relative_path: str
    path: Path
    mtime_ns: int
    size: int

    @property
    def cache_key(self) -> tuple[int, str, int, int]:
        return (self.root_index, self.relative_path, self.mtime_ns, self.size)


@dataclass(frozen=True)
class _WildcardSourceState:
    roots: tuple[Path, ...]
    root_identities: tuple[str, ...]
    files: tuple[_WildcardSourceFile, ...]

    @property
    def cache_key(self) -> tuple:
        roots = tuple(
            (identity, str(root))
            for identity, root in zip(self.root_identities, self.roots)
        )
        return roots, tuple(source.cache_key for source in self.files)


def default_wildcard_root() -> Path:
    return USER_DATA_DIR / WILDCARD_DIR_NAME


def ensure_default_wildcard_root(create_sample: bool = True) -> Path:
    root = default_wildcard_root()
    root.mkdir(parents=True, exist_ok=True)
    if create_sample:
        sample_path = root / DEFAULT_TEST_WILDCARD_FILE
        if not sample_path.exists():
            sample_path.write_text(DEFAULT_TEST_WILDCARD_TEXT, encoding="utf-8")
    return root


def parse_wildcard_extra_paths(value: str) -> list[str]:
    paths = []
    for line in str(value or "").splitlines():
        path = line.strip().strip('"')
        if path:
            paths.append(path)
    return paths


def _comfy_base_path() -> Path:
    try:
        import folder_paths  # type: ignore

        base_path = getattr(folder_paths, "base_path", None)
        if base_path:
            return Path(base_path)
    except Exception:
        pass
    return Path.cwd()


def _resolve_path(value: str, base_path: Path) -> Path:
    expanded = os.path.expandvars(os.path.expanduser(value))
    path = Path(expanded)
    if not path.is_absolute():
        path = base_path / path
    return path.resolve()


def resolve_wildcard_roots(extra_paths: str | None = None) -> list[Path]:
    if extra_paths is None:
        from ..settings.repository import get_settings

        extra_paths = get_settings().get("wildcard.extra_paths", "")

    base_path = _comfy_base_path()
    roots: list[Path] = []
    seen = set()
    for raw_path in parse_wildcard_extra_paths(extra_paths or ""):
        try:
            root = _resolve_path(raw_path, base_path)
        except (OSError, RuntimeError, ValueError):
            continue
        key = os.path.normcase(str(root))
        if key not in seen:
            seen.add(key)
            roots.append(root)

    default_root = default_wildcard_root().resolve()
    default_key = os.path.normcase(str(default_root))
    if default_key not in seen:
        roots.append(default_root)
    return roots


def _normalize_wildcard_key(value: str) -> str | None:
    key = str(value or "").replace("\\", "/").replace(" ", "-").strip().strip("/")
    if not key:
        return None
    if key.startswith("/") or re.match(r"^[a-zA-Z]:", key):
        return None
    parts = [part for part in key.split("/") if part]
    if any(part == ".." for part in parts):
        return None
    return "/".join(parts).lower()


def _read_text_file(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="iso-8859-1")


def _parse_option(value) -> WildcardOption | None:
    text = "" if value is None else str(value).strip()
    if not text:
        return None
    match = WEIGHT_PREFIX_RE.match(text)
    if not match:
        return WildcardOption(text=text, weight=1.0)
    try:
        weight = float(match.group(1))
    except ValueError:
        return WildcardOption(text=text, weight=1.0)
    return WildcardOption(text=match.group(2).strip(), weight=max(0.0, weight))


def _options_from_lines(text: str) -> list[WildcardOption]:
    options = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        option = _parse_option(line)
        if option is not None:
            options.append(option)
    return options


def _stringify_yaml_scalar(value) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    return "" if value is None else str(value)


class _YamlSourceLimitError(ValueError):
    """A YAML source cannot be materialized within the per-source budget."""


def _validate_yaml_source(data, prefix: str) -> None:
    visits = 0
    option_references = 0
    characters = len(prefix)
    active: set[int] = set()

    def visit(value, path_prefix: str, depth: int, copies: int, publish: bool):
        nonlocal visits, option_references, characters
        visits += 1
        if visits > MAX_YAML_SOURCE_VISITS or depth > MAX_YAML_SOURCE_DEPTH:
            raise _YamlSourceLimitError("YAML traversal budget exceeded")
        if isinstance(value, (dict, list)):
            identity = id(value)
            if identity in active:
                raise _YamlSourceLimitError("Cyclic YAML alias")
            active.add(identity)
            copies += 1 + int(publish and bool(path_prefix))
            if isinstance(value, dict):
                for raw_key, child in value.items():
                    visits += 1
                    if visits > MAX_YAML_SOURCE_VISITS:
                        raise _YamlSourceLimitError("YAML traversal budget exceeded")
                    key = _normalize_wildcard_key(raw_key)
                    if key is None:
                        continue
                    characters += len(key) + len(path_prefix) + bool(path_prefix)
                    if characters > MAX_YAML_SOURCE_OUTPUT_CHARACTERS:
                        raise _YamlSourceLimitError("YAML output budget exceeded")
                    child_prefix = f"{path_prefix}/{key}" if path_prefix else key
                    visit(child, child_prefix, depth + 1, copies, True)
            else:
                for item in value:
                    visit(item, path_prefix, depth + 1, copies, False)
            active.remove(identity)
            return

        text = _stringify_yaml_scalar(value).strip()
        if text:
            # Dictionary scalars have their own collect frame; list scalars
            # append directly to the containing frame. Shared aliases are
            # charged on each visit so explicit duplicate weights stay intact.
            references = copies + (1 + int(bool(path_prefix)) if publish else 0)
            option_references += references
            characters += len(text) * references
            if (
                option_references > MAX_YAML_SOURCE_OPTION_REFERENCES
                or characters > MAX_YAML_SOURCE_OUTPUT_CHARACTERS
            ):
                raise _YamlSourceLimitError("YAML output budget exceeded")

    visit(data, prefix, 0, 0, True)


def _yaml_entries(data, prefix: str = "") -> dict[str, list[WildcardOption]]:
    _validate_yaml_source(data, prefix)
    entries: dict[str, list[WildcardOption]] = {}

    def collect(
        value,
        path_prefix: str,
        publish_alias: bool = True,
    ) -> list[WildcardOption]:
        aggregate: list[WildcardOption] = []
        if isinstance(value, dict):
            for raw_key, child_value in value.items():
                child_key = _normalize_wildcard_key(raw_key)
                if child_key is None:
                    continue
                path_key = f"{path_prefix}/{child_key}" if path_prefix else child_key
                aggregate.extend(collect(child_value, path_key))
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, (dict, list)):
                    # The containing list owns this alias. Nested containers
                    # still publish their distinct child paths, but not the
                    # same prefix again through an intermediate frame.
                    aggregate.extend(collect(item, path_prefix, publish_alias=False))
                    continue
                option = _parse_option(_stringify_yaml_scalar(item))
                if option is not None:
                    aggregate.append(option)
        else:
            option = _parse_option(_stringify_yaml_scalar(value))
            if option is not None:
                aggregate.append(option)

        if publish_alias and path_prefix and aggregate:
            entries.setdefault(path_prefix, []).extend(aggregate)
        return aggregate

    collect(data, prefix)
    return entries


def _load_yaml_entries(path: Path) -> dict[str, list[WildcardOption]]:
    if yaml is None:
        return {}
    text = _read_text_file(path)
    try:
        data = yaml.safe_load(text)
    except Exception:
        return {}
    try:
        return _yaml_entries(data)
    except _YamlSourceLimitError:
        # Keep the malformed-YAML policy: skip this source, retaining siblings.
        return {}


def _load_wildcard_file(
    root: Path,
    path: Path,
) -> dict[str, list[WildcardOption]]:
    suffix = path.suffix.lower()
    if suffix not in WILDCARD_EXTENSIONS:
        return {}
    if suffix in {".yaml", ".yml"}:
        return _load_yaml_entries(path)
    try:
        relative_key = path.relative_to(root).with_suffix("").as_posix()
    except ValueError:
        return {}
    key = _normalize_wildcard_key(relative_key)
    if key is None:
        return {}
    return {key: _options_from_lines(_read_text_file(path))}


def _wildcard_root_identity(root: Path) -> str:
    try:
        return os.path.normcase(os.path.abspath(os.fspath(root)))
    except (OSError, TypeError, ValueError):
        return os.path.normcase(str(root))


def _scan_wildcard_sources(roots: tuple[Path, ...]) -> _WildcardSourceState:
    files: list[_WildcardSourceFile] = []
    for root_index, root in enumerate(roots):
        if not root.is_dir():
            continue
        try:
            candidates = sorted(
                root.rglob("*"),
                key=lambda item: item.as_posix().lower(),
            )
        except OSError:
            continue
        for path in candidates:
            if path.suffix.lower() not in WILDCARD_EXTENSIONS:
                continue
            try:
                if not path.is_file():
                    continue
                stat = path.stat()
                relative = path.relative_to(root).as_posix()
            except (OSError, ValueError):
                continue
            files.append(
                _WildcardSourceFile(
                    root_index=root_index,
                    root=str(root),
                    relative_path=relative,
                    path=path,
                    mtime_ns=stat.st_mtime_ns,
                    size=stat.st_size,
                )
            )
    return _WildcardSourceState(
        roots=roots,
        root_identities=tuple(_wildcard_root_identity(root) for root in roots),
        files=tuple(files),
    )
