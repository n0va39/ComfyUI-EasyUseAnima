from __future__ import annotations

import bisect
from collections import OrderedDict
import fnmatch
import hashlib
import math
import os
import random
import re
import threading
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Iterable, Mapping, Sequence

# NumPy is mandatory in supported ComfyUI runtimes and defines the seeded
# wildcard sampling contract. A stdlib fallback would produce different results.
import numpy as np

try:
    import yaml
except Exception:  # pragma: no cover - YAML files are skipped without PyYAML.
    yaml = None

try:
    from .storage import USER_DATA_DIR
except ImportError:
    from storage import USER_DATA_DIR


WILDCARD_DIR_NAME = "wildcards"
DEFAULT_TEST_WILDCARD_FILE = "easyuse_anima_test.txt"
DEFAULT_TEST_WILDCARD_TEXT = "# EasyUse Anima test wildcard\nsimple wildcard\nanima wildcard\n"
WILDCARD_MODE_POPULATE = "populate"
WILDCARD_MODE_FIXED = "fixed"
WILDCARD_MODE_SEQUENTIAL = "sequential"
# Legacy workflow value. It is no longer exposed as a mode; standalone
# wildcard nodes normalize it to Fixed and Prompt Studio normalizes it to
# Populate.
WILDCARD_MODE_REPRODUCE = "reproduce"
WILDCARD_MODES = (
    WILDCARD_MODE_POPULATE,
    WILDCARD_MODE_FIXED,
    WILDCARD_MODE_SEQUENTIAL,
)
WILDCARD_MODE_LABELS = (
    "일반",
    "고정",
)
PROMPT_STUDIO_WILDCARD_MODE_LABELS = ("일반", "순차")
WILDCARD_MODE_ALIASES = {
    WILDCARD_MODE_POPULATE: WILDCARD_MODE_POPULATE,
    "normal": WILDCARD_MODE_POPULATE,
    "fill": WILDCARD_MODE_POPULATE,
    "일반": WILDCARD_MODE_POPULATE,
    "일반 채우기": WILDCARD_MODE_POPULATE,
    WILDCARD_MODE_FIXED: WILDCARD_MODE_FIXED,
    "고정": WILDCARD_MODE_FIXED,
    WILDCARD_MODE_SEQUENTIAL: WILDCARD_MODE_SEQUENTIAL,
    "순차": WILDCARD_MODE_SEQUENTIAL,
    WILDCARD_MODE_REPRODUCE: WILDCARD_MODE_FIXED,
    "재현": WILDCARD_MODE_FIXED,
}

SEED_CONTROL_FIXED = "fixed"
SEED_CONTROL_RANDOMIZE = "randomize"
SEED_CONTROL_INCREMENT = "increment"
SEED_CONTROL_DECREMENT = "decrement"
SEED_CONTROL_MODES = (
    SEED_CONTROL_FIXED,
    SEED_CONTROL_RANDOMIZE,
    SEED_CONTROL_INCREMENT,
    SEED_CONTROL_DECREMENT,
)

MAX_SEED = 0xFFFFFFFFFFFFFFFF
PUBLIC_MAX_SEED = (1 << 53) - 1
# Defaults stop exponential inputs well before they become memory hazards while
# leaving ample room for ordinary nested wildcard libraries.  The old depth is
# retained as a hard ceiling for callers that provide a custom budget.
MAX_EXPANSION_DEPTH = 100
REPLACE_DEPTH = MAX_EXPANSION_DEPTH
DEFAULT_MAX_EXPANSION_DEPTH = 32
DEFAULT_MAX_EXPANSION_REPLACEMENTS = 4096
DEFAULT_MAX_EXPANSION_OUTPUT_CHARS = 256 * 1024
DEFAULT_MAX_EXPANSION_GROWTH_PER_PASS = 8.0
MAX_EXPANSION_REPLACEMENTS = 65536
MAX_EXPANSION_OUTPUT_CHARS = 1024 * 1024
MAX_EXPANSION_GROWTH_PER_PASS = 32.0
WILDCARD_EXTENSIONS = {".txt", ".yaml", ".yml"}

COMMENT_RE = re.compile(r"^\s*#.*(?:\n|$)", re.MULTILINE)
DYNAMIC_RE = re.compile(r"(?<![\\%])\{((?:[^{}]|(?<=\\)[{}])*?)(?<!\\)\}")
WILDCARD_RE = re.compile(r"__(?P<keyword>[\w.\-+/*\\]+?)__", re.IGNORECASE)
WILDCARD_FULL_RE = re.compile(r"^__(?P<keyword>[\w.\-+/*\\]+?)__$", re.IGNORECASE)
WILDCARD_QUANTIFIER_RE = re.compile(
    r"(?P<quantifier>\d+)#__(?P<keyword>[\w.\-+/*\\]+?)__",
    re.IGNORECASE,
)
WEIGHT_PREFIX_RE = re.compile(r"^\s*([+-]?(?:\d+(?:\.\d*)?|\.\d+))::(.*)$", re.DOTALL)
COUNT_SPEC_RE = re.compile(
    r"(?:(?P<fixed>\d+)|(?P<minimum>\d*)\s*-\s*(?P<maximum>\d*))"
)


@dataclass(frozen=True)
class WildcardOption:
    text: str
    weight: float = 1.0


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


@dataclass(frozen=True)
class _WildcardSnapshot:
    cache_key: tuple
    mapping: Mapping[str, tuple[WildcardOption, ...]]
    wildcard_names: tuple[str, ...]
    roots: tuple[str, ...]
    files: tuple[_WildcardSourceFile, ...]
    cacheable: bool

    def public_signature(self) -> dict:
        return {
            "roots": list(self.roots),
            "files": [
                {
                    "root": source.root,
                    "path": source.relative_path,
                    "mtime_ns": source.mtime_ns,
                    "size": source.size,
                }
                for source in self.files
            ],
        }


_SNAPSHOT_CACHE_LIMIT = 16
_SNAPSHOT_CONDITION = threading.Condition()
_SNAPSHOT_CACHE: OrderedDict[tuple, _WildcardSnapshot] = OrderedDict()
_SNAPSHOT_BUILDING: set[tuple] = set()


def _bounded_int(value, default: int, minimum: int, maximum: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError, OverflowError):
        parsed = default
    return max(minimum, min(maximum, parsed))


def _bounded_float(value, default: float, minimum: float, maximum: float) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError, OverflowError):
        parsed = default
    if not math.isfinite(parsed):
        parsed = default
    return max(minimum, min(maximum, parsed))


@dataclass(frozen=True)
class WildcardExpansionBudget:
    max_depth: int = DEFAULT_MAX_EXPANSION_DEPTH
    max_replacements: int = DEFAULT_MAX_EXPANSION_REPLACEMENTS
    max_output_chars: int = DEFAULT_MAX_EXPANSION_OUTPUT_CHARS
    max_growth_per_pass: float = DEFAULT_MAX_EXPANSION_GROWTH_PER_PASS

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "max_depth",
            _bounded_int(self.max_depth, DEFAULT_MAX_EXPANSION_DEPTH, 0, MAX_EXPANSION_DEPTH),
        )
        object.__setattr__(
            self,
            "max_replacements",
            _bounded_int(
                self.max_replacements,
                DEFAULT_MAX_EXPANSION_REPLACEMENTS,
                0,
                MAX_EXPANSION_REPLACEMENTS,
            ),
        )
        object.__setattr__(
            self,
            "max_output_chars",
            _bounded_int(
                self.max_output_chars,
                DEFAULT_MAX_EXPANSION_OUTPUT_CHARS,
                1,
                MAX_EXPANSION_OUTPUT_CHARS,
            ),
        )
        object.__setattr__(
            self,
            "max_growth_per_pass",
            _bounded_float(
                self.max_growth_per_pass,
                DEFAULT_MAX_EXPANSION_GROWTH_PER_PASS,
                1.0,
                MAX_EXPANSION_GROWTH_PER_PASS,
            ),
        )


@dataclass(frozen=True)
class WildcardExpansionResult:
    text: str
    changed: bool
    used_keys: tuple[str, ...] = ()
    missing_keys: tuple[str, ...] = ()
    replacement_count: int = 0
    limit_reason: str | None = None


def _utf8_width(char: str) -> int:
    codepoint = ord(char)
    if codepoint <= 0x7F:
        return 1
    if codepoint <= 0x7FF:
        return 2
    if codepoint <= 0xFFFF:
        return 3
    return 4


def _utf8_length(value: str) -> int:
    return sum(_utf8_width(char) for char in value)


@dataclass(frozen=True)
class _ExpansionSegment:
    text: str
    key_stack: tuple[str, ...] = ()


class _ExpansionText:
    def __init__(self, segments: Iterable[_ExpansionSegment]):
        merged: list[_ExpansionSegment] = []
        pending_parts: list[str] = []
        pending_stack: tuple[str, ...] | None = None

        def flush_pending() -> None:
            nonlocal pending_parts, pending_stack
            if pending_parts:
                merged.append(_ExpansionSegment("".join(pending_parts), pending_stack or ()))
            pending_parts = []
            pending_stack = None

        for segment in segments:
            if not segment.text:
                continue
            if pending_parts and pending_stack != segment.key_stack:
                flush_pending()
            pending_stack = segment.key_stack
            pending_parts.append(segment.text)
        flush_pending()
        self.segments = tuple(merged)
        self.text = "".join(segment.text for segment in self.segments)
        self.char_count = len(self.text)
        self.byte_count = _utf8_length(self.text)
        ends = []
        total = 0
        for segment in self.segments:
            total += len(segment.text)
            ends.append(total)
        self._ends = tuple(ends)

    @classmethod
    def from_text(cls, text: str) -> "_ExpansionText":
        return cls((_ExpansionSegment(text),))

    def slice_segments(self, start: int, end: int) -> list[_ExpansionSegment]:
        if start >= end or not self.segments:
            return []
        index = bisect.bisect_right(self._ends, start)
        segment_start = 0 if index == 0 else self._ends[index - 1]
        sliced = []
        while index < len(self.segments) and segment_start < end:
            segment = self.segments[index]
            local_start = max(0, start - segment_start)
            local_end = min(len(segment.text), end - segment_start)
            if local_start < local_end:
                sliced.append(_ExpansionSegment(segment.text[local_start:local_end], segment.key_stack))
            segment_start = self._ends[index]
            index += 1
        return sliced

    def key_stack_for_span(self, start: int, end: int) -> tuple[str, ...]:
        stacks = [segment.key_stack for segment in self.slice_segments(start, end)]
        if not stacks:
            return ()
        common = list(stacks[0])
        for stack in stacks[1:]:
            shared = 0
            while shared < len(common) and shared < len(stack) and common[shared] == stack[shared]:
                shared += 1
            del common[shared:]
            if not common:
                break
        return tuple(common)


@dataclass(frozen=True)
class _Replacement:
    parts: tuple[str, ...]
    separator: str
    key_stack: tuple[str, ...]

    @property
    def char_count(self) -> int:
        return sum(len(part) for part in self.parts) + len(self.separator) * max(0, len(self.parts) - 1)

    @property
    def byte_count(self) -> int:
        return sum(_utf8_length(part) for part in self.parts) + _utf8_length(self.separator) * max(
            0,
            len(self.parts) - 1,
        )

    def materialize(self) -> str:
        if len(self.parts) == 1:
            return self.parts[0]
        return self.separator.join(self.parts)


class _ExpansionState:
    def __init__(self, budget: WildcardExpansionBudget):
        self.budget = budget
        self.replacement_count = 0
        self.limit_reason: str | None = None
        self.cycle_detected = False
        self._pass_base_chars = 0
        self._pass_base_bytes = 0

    def begin_pass(self, current: _ExpansionText) -> None:
        self._pass_base_chars = current.char_count
        self._pass_base_bytes = current.byte_count

    def stop(self, reason: str) -> None:
        if self.limit_reason is None:
            self.limit_reason = reason

    def candidate(
        self,
        parts: Iterable[str],
        separator: str,
        key_stack: tuple[str, ...],
    ) -> _Replacement | None:
        candidate = _Replacement(tuple(parts), separator, key_stack)
        cycle_parts = candidate.parts
        if len(candidate.parts) > 1 and candidate.separator:
            cycle_parts = (*candidate.parts, candidate.separator)
        for part in cycle_parts:
            for match in WILDCARD_RE.finditer(part):
                key = _normalize_wildcard_key(match.group("keyword"))
                if key is not None and key in key_stack:
                    self.cycle_detected = True
                    return None
        return candidate

    def _replacement_limit_reason(
        self,
        current: _ExpansionText,
        stage_delta_chars: int,
        stage_delta_bytes: int,
        matched_text: str,
        replacement: _Replacement,
    ) -> str | None:
        if self.replacement_count >= self.budget.max_replacements:
            return "max_replacements"
        projected_chars = (
            current.char_count
            + stage_delta_chars
            - len(matched_text)
            + replacement.char_count
        )
        projected_bytes = (
            current.byte_count
            + stage_delta_bytes
            - _utf8_length(matched_text)
            + replacement.byte_count
        )
        # One conservative cap bounds both logical characters and UTF-8 bytes.
        if projected_chars > self.budget.max_output_chars or projected_bytes > self.budget.max_output_chars:
            return "max_output_chars"
        growth = self.budget.max_growth_per_pass
        if (
            projected_chars > math.floor(max(1, self._pass_base_chars) * growth)
            or projected_bytes > math.floor(max(1, self._pass_base_bytes) * growth)
        ):
            return "max_growth_per_pass"
        return None

    def replace_matches(
        self,
        current: _ExpansionText,
        pattern: re.Pattern,
        resolver,
    ) -> _ExpansionText:
        source = current.text
        output: list[_ExpansionSegment] = []
        cursor = 0
        stage_delta_chars = 0
        stage_delta_bytes = 0
        for match in pattern.finditer(source):
            output.extend(current.slice_segments(cursor, match.start()))
            key_stack = current.key_stack_for_span(match.start(), match.end())
            replacement = resolver(match, key_stack)
            if self.limit_reason is not None:
                output.extend(current.slice_segments(match.start(), len(source)))
                return _ExpansionText(output)
            if replacement is None:
                output.extend(current.slice_segments(match.start(), match.end()))
                cursor = match.end()
                continue
            matched_text = match.group(0)
            reason = self._replacement_limit_reason(
                current,
                stage_delta_chars,
                stage_delta_bytes,
                matched_text,
                replacement,
            )
            if reason is not None:
                self.stop(reason)
                output.extend(current.slice_segments(match.start(), len(source)))
                return _ExpansionText(output)
            replacement_text = replacement.materialize()
            output.append(_ExpansionSegment(replacement_text, replacement.key_stack))
            self.replacement_count += 1
            stage_delta_chars += replacement.char_count - len(matched_text)
            stage_delta_bytes += replacement.byte_count - _utf8_length(matched_text)
            cursor = match.end()
        output.extend(current.slice_segments(cursor, len(source)))
        return _ExpansionText(output)


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


def normalize_wildcard_mode(mode: str) -> str:
    value = str(mode or "").strip()
    return WILDCARD_MODE_ALIASES.get(value, WILDCARD_MODE_POPULATE)


def normalize_prompt_studio_wildcard_mode(mode: str) -> str:
    """Normalize Prompt Studio to its two source-expansion modes."""
    return (
        WILDCARD_MODE_SEQUENTIAL
        if normalize_wildcard_mode(mode) == WILDCARD_MODE_SEQUENTIAL
        else WILDCARD_MODE_POPULATE
    )


def normalize_seed(value) -> int:
    try:
        seed = int(value)
    except (TypeError, ValueError):
        seed = 0
    return max(0, min(MAX_SEED, seed))


def next_seed(seed, control: str) -> int:
    """Return the next public wildcard seed without breaking legacy inputs.

    Existing workflows may contain uint64 values that JavaScript cannot
    represent exactly.  The current generation still consumes that legacy
    value, and ``fixed`` preserves it.  Controls that advance the state first
    project the value onto the public JavaScript-safe range so every returned
    non-fixed seed uses the same inclusive range in Python and JavaScript.
    """
    seed = normalize_seed(seed)
    control = str(control or SEED_CONTROL_FIXED).strip()
    if control == SEED_CONTROL_FIXED:
        return seed
    if control == SEED_CONTROL_RANDOMIZE:
        return random.SystemRandom().randrange(0, PUBLIC_MAX_SEED + 1)
    public_seed = min(seed, PUBLIC_MAX_SEED)
    if control == SEED_CONTROL_INCREMENT:
        return 0 if public_seed >= PUBLIC_MAX_SEED else public_seed + 1
    if control == SEED_CONTROL_DECREMENT:
        return PUBLIC_MAX_SEED if public_seed <= 0 else public_seed - 1
    return seed


def has_wildcard_syntax(text: str) -> bool:
    value = str(text or "")
    return bool(DYNAMIC_RE.search(value) or WILDCARD_RE.search(value) or WILDCARD_QUANTIFIER_RE.search(value))


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
        try:
            from .settings import get_settings
        except ImportError:
            from settings import get_settings

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

    try:
        default_root = ensure_default_wildcard_root().resolve()
    except OSError:
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


def _yaml_entries(data, prefix: str = "") -> dict[str, list[WildcardOption]]:
    entries: dict[str, list[WildcardOption]] = {}

    def collect(value, path_prefix: str, publish_alias: bool = True) -> list[WildcardOption]:
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
                    # The containing list owns this alias. Nested containers still
                    # publish their distinct child paths, but not the same prefix
                    # again through an intermediate recursion frame.
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
    return _yaml_entries(data)


def _load_wildcard_file(root: Path, path: Path) -> dict[str, list[WildcardOption]]:
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
            candidates = sorted(root.rglob("*"), key=lambda item: item.as_posix().lower())
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


def _build_wildcard_snapshot(source_state: _WildcardSourceState) -> _WildcardSnapshot:
    mapping: dict[str, list[WildcardOption]] = {}
    cacheable = True
    for source in source_state.files:
        root = source_state.roots[source.root_index]
        try:
            entries = _load_wildcard_file(root, source.path)
        except OSError:
            cacheable = False
            continue
        for key, options in entries.items():
            if key not in mapping and options:
                mapping[key] = options

    frozen_mapping = MappingProxyType(
        {key: tuple(options) for key, options in mapping.items()}
    )
    return _WildcardSnapshot(
        cache_key=source_state.cache_key,
        mapping=frozen_mapping,
        wildcard_names=tuple(sorted(frozen_mapping)),
        roots=tuple(str(root) for root in source_state.roots),
        files=source_state.files,
        cacheable=cacheable,
    )


def _wildcard_snapshot(roots: Iterable[Path]) -> _WildcardSnapshot:
    resolved_roots = tuple(Path(root) for root in roots)
    while True:
        source_state = _scan_wildcard_sources(resolved_roots)
        cache_key = source_state.cache_key
        with _SNAPSHOT_CONDITION:
            cached = _SNAPSHOT_CACHE.get(cache_key)
            if cached is not None:
                _SNAPSHOT_CACHE.move_to_end(cache_key)
                return cached
            if cache_key in _SNAPSHOT_BUILDING:
                _SNAPSHOT_CONDITION.wait()
                continue
            _SNAPSHOT_BUILDING.add(cache_key)

        snapshot = None
        failure: BaseException | None = None
        try:
            candidate = _build_wildcard_snapshot(source_state)
            verified_state = _scan_wildcard_sources(resolved_roots)
            if verified_state.cache_key == cache_key:
                snapshot = candidate
        except BaseException as exc:
            failure = exc
        finally:
            with _SNAPSHOT_CONDITION:
                _SNAPSHOT_BUILDING.discard(cache_key)
                if snapshot is not None and snapshot.cacheable:
                    _SNAPSHOT_CACHE[cache_key] = snapshot
                    _SNAPSHOT_CACHE.move_to_end(cache_key)
                    while len(_SNAPSHOT_CACHE) > _SNAPSHOT_CACHE_LIMIT:
                        _SNAPSHOT_CACHE.popitem(last=False)
                _SNAPSHOT_CONDITION.notify_all()

        if failure is not None:
            raise failure
        if snapshot is not None:
            return snapshot


def _load_wildcard_map(roots: Iterable[Path]) -> dict[str, list[WildcardOption]]:
    snapshot = _wildcard_snapshot(roots)
    return {key: list(options) for key, options in snapshot.mapping.items()}


def list_wildcards(extra_paths: str | None = None, roots: Iterable[Path] | None = None) -> list[str]:
    snapshot = _wildcard_snapshot(
        roots if roots is not None else resolve_wildcard_roots(extra_paths)
    )
    return list(snapshot.wildcard_names)


def wildcard_sources_signature(extra_paths: str | None = None, roots: Iterable[Path] | None = None) -> dict:
    snapshot = _wildcard_snapshot(
        roots if roots is not None else resolve_wildcard_roots(extra_paths)
    )
    return snapshot.public_signature()


class _Selector:
    def __init__(self, seed: int, sequential: bool):
        self.seed = normalize_seed(seed)
        self.sequential = sequential
        self.rng = (
            None
            if self.sequential
            else np.random.Generator(np.random.PCG64(self.seed))
        )

    def count_from_range(self, minimum: int, maximum: int) -> int:
        minimum = max(0, minimum)
        maximum = max(minimum, maximum)
        if minimum == maximum:
            return minimum
        if self.sequential:
            return minimum + (self.seed % (maximum - minimum + 1))
        return int(self.rng.integers(minimum, maximum + 1))

    def choose_one(self, options: Sequence[WildcardOption]) -> WildcardOption | None:
        selected = self.choose_many(options, 1)
        return selected[0] if selected else None

    def choose_many(
        self,
        options: Sequence[WildcardOption],
        count: int,
    ) -> list[WildcardOption]:
        if not options or count <= 0:
            return []
        if self.sequential:
            count = min(count, len(options))
            start = self.seed % len(options)
            return [options[(start + offset) % len(options)] for offset in range(count)]

        weights = [max(0.0, option.weight) for option in options]
        positive = [
            (option, weight)
            for option, weight in zip(options, weights)
            if weight > 0
        ]
        if positive:
            pool = [option for option, _weight in positive]
            pool_weights = [weight for _option, weight in positive]
        else:
            pool = list(options)
            pool_weights = None

        count = min(count, len(pool))
        probabilities = None
        if pool_weights is not None:
            total = sum(pool_weights)
            probabilities = [weight / total for weight in pool_weights]
        indices = self.rng.choice(len(pool), size=count, replace=False, p=probabilities)
        return [pool[int(index)] for index in indices]


class _WildcardLibrary:
    def __init__(
        self,
        roots: Iterable[Path] | None = None,
        *,
        snapshot: _WildcardSnapshot | None = None,
    ):
        if snapshot is None:
            snapshot = _wildcard_snapshot(roots or ())
        self.mapping = snapshot.mapping
        self.used: list[str] = []
        self.missing: list[str] = []

    def _record_used(self, key: str) -> None:
        if key not in self.used:
            self.used.append(key)

    def _record_missing(self, key: str) -> None:
        if key not in self.missing:
            self.missing.append(key)

    def options_for(self, raw_key: str) -> Sequence[WildcardOption]:
        key = _normalize_wildcard_key(raw_key)
        if key is None:
            return []
        options = self._options_for_normalized_key(key)
        if options:
            self._record_used(key)
        else:
            self._record_missing(key)
        return options

    def _options_for_normalized_key(self, key: str) -> Sequence[WildcardOption]:
        if key in self.mapping:
            return self.mapping[key]
        if "/" not in key and "*" not in key:
            nested = self._options_for_pattern(f"*/{key}", include_basename=True)
            if nested:
                return nested
        if "*" in key:
            return self._options_for_pattern(key, include_basename=False)
        return []

    def _options_for_pattern(self, pattern: str, include_basename: bool) -> list[WildcardOption]:
        options = []
        for key in sorted(self.mapping):
            if fnmatch.fnmatchcase(key, pattern) or (
                include_basename and (key == pattern[2:] or key.endswith(f"/{pattern[2:]}"))
            ):
                options.extend(self.mapping[key])
        return options


def _split_unescaped(value: str, separator: str) -> list[str]:
    parts = []
    current = []
    escaped = False
    for char in value:
        if escaped:
            current.append(char)
            escaped = False
            continue
        if char == "\\":
            current.append(char)
            escaped = True
            continue
        if char == separator:
            parts.append("".join(current))
            current = []
            continue
        current.append(char)
    parts.append("".join(current))
    return parts


def _parse_dynamic_options(value: str) -> list[WildcardOption]:
    options = []
    for option in _split_unescaped(value, "|"):
        parsed = _parse_option(option)
        if parsed is not None:
            options.append(parsed)
    return options


def _parse_count_spec(spec: str, selector: _Selector) -> int | None:
    text = str(spec or "").strip()
    if not text:
        return 1
    match = COUNT_SPEC_RE.fullmatch(text)
    if match is None:
        return None
    fixed = match.group("fixed")
    if fixed is not None:
        return int(fixed)
    left = match.group("minimum")
    right = match.group("maximum")
    if not left and not right:
        return None
    minimum = int(left) if left else 0
    maximum = int(right) if right else minimum
    return selector.count_from_range(minimum, maximum)


def _expand_multiselect_options(
    options: list[WildcardOption],
    library: _WildcardLibrary,
) -> tuple[Sequence[WildcardOption], str | None]:
    if len(options) != 1:
        return options, None
    match = WILDCARD_FULL_RE.match(options[0].text.strip())
    if not match:
        return options, None
    raw_key = match.group("keyword")
    return library.options_for(raw_key), _normalize_wildcard_key(raw_key)


def _replace_dynamic(
    current: _ExpansionText,
    state: _ExpansionState,
    selector: _Selector,
    library: _WildcardLibrary,
) -> _ExpansionText:
    def replace(match: re.Match, key_stack: tuple[str, ...]) -> _Replacement | None:
        body = match.group(1)
        raw_options = _split_unescaped(body, "|")
        if not raw_options:
            return None
        first_parts = raw_options[0].split("$$")
        if len(first_parts) > 1:
            count = _parse_count_spec(first_parts[0], selector)
            if count is None:
                return None
            separator = ", "
            if len(first_parts) == 2:
                first_candidate = first_parts[1]
            else:
                separator = first_parts[1]
                first_candidate = "$$".join(first_parts[2:])
            candidate_text = "|".join([first_candidate, *raw_options[1:]])
            options, expanded_key = _expand_multiselect_options(
                _parse_dynamic_options(candidate_text),
                library,
            )
            selected = selector.choose_many(options, count)
            if not selected:
                return None
            candidate_stack = key_stack + ((expanded_key,) if expanded_key is not None else ())
            return state.candidate(
                (option.text for option in selected),
                separator,
                candidate_stack,
            )

        options = _parse_dynamic_options(body)
        selected = selector.choose_one(options)
        if selected is None:
            return None
        return state.candidate((selected.text,), "", key_stack)

    return state.replace_matches(current, DYNAMIC_RE, replace)


def _replace_quantified_wildcards(
    current: _ExpansionText,
    state: _ExpansionState,
    selector: _Selector,
    library: _WildcardLibrary,
) -> _ExpansionText:
    def replace(match: re.Match, key_stack: tuple[str, ...]) -> _Replacement | None:
        count = max(0, int(match.group("quantifier")))
        raw_key = match.group("keyword")
        options = library.options_for(raw_key)
        selected = selector.choose_many(options, count)
        key = _normalize_wildcard_key(raw_key)
        if not selected or key is None:
            return None
        return state.candidate(
            (option.text for option in selected),
            ", ",
            key_stack + (key,),
        )

    return state.replace_matches(current, WILDCARD_QUANTIFIER_RE, replace)


def _replace_file_wildcards(
    current: _ExpansionText,
    state: _ExpansionState,
    selector: _Selector,
    library: _WildcardLibrary,
) -> _ExpansionText:
    def replace(match: re.Match, key_stack: tuple[str, ...]) -> _Replacement | None:
        raw_key = match.group("keyword")
        options = library.options_for(raw_key)
        selected = selector.choose_one(options)
        key = _normalize_wildcard_key(raw_key)
        if selected is None or key is None:
            return None
        return state.candidate((selected.text,), "", key_stack + (key,))

    return state.replace_matches(current, WILDCARD_RE, replace)


def _bounded_output_prefix(text: str, limit: int) -> str:
    chars = []
    byte_count = 0
    for char in text:
        width = _utf8_width(char)
        if len(chars) >= limit or byte_count + width > limit:
            break
        chars.append(char)
        byte_count += width
    return "".join(chars)


def _expansion_state_signature(text: str) -> tuple[int, bytes]:
    digest = hashlib.blake2b(text.encode("utf-8", errors="surrogatepass"), digest_size=16)
    return len(text), digest.digest()


@dataclass
class _ExpansionLane:
    source: str
    current: _ExpansionText
    state: _ExpansionState
    library: _WildcardLibrary


def expand_wildcard_texts(
    texts: Sequence[str],
    seed=0,
    mode: str = WILDCARD_MODE_POPULATE,
    extra_paths: str | None = None,
    roots: Iterable[Path] | None = None,
    budget: WildcardExpansionBudget | None = None,
) -> tuple[WildcardExpansionResult, ...]:
    """Expand ordered texts through one deterministic selector stream.

    Each text keeps its existing recursion and safety budget, while expansion
    stages run across the texts in order. This matches expanding one Prompt
    Studio prompt without joining fields through a lossy delimiter.
    """
    sources = tuple(str(text or "") for text in texts)
    if not sources:
        return ()

    mode = normalize_wildcard_mode(mode)
    selector = _Selector(
        normalize_seed(seed),
        sequential=mode == WILDCARD_MODE_SEQUENTIAL,
    )
    resolved_roots = tuple(
        Path(root)
        for root in (
            roots if roots is not None else resolve_wildcard_roots(extra_paths)
        )
    )
    snapshot = _wildcard_snapshot(resolved_roots)
    expansion_budget = (
        budget
        if isinstance(budget, WildcardExpansionBudget)
        else WildcardExpansionBudget()
    )
    lanes: list[_ExpansionLane] = []
    for source in sources:
        state = _ExpansionState(expansion_budget)
        cleaned = COMMENT_RE.sub("", source)
        if (
            len(cleaned) > expansion_budget.max_output_chars
            or _utf8_length(cleaned) > expansion_budget.max_output_chars
        ):
            cleaned = _bounded_output_prefix(
                cleaned,
                expansion_budget.max_output_chars,
            )
            state.stop("max_output_chars")
        current = _ExpansionText.from_text(cleaned)
        lanes.append(
            _ExpansionLane(
                source=source,
                current=current,
                state=state,
                library=_WildcardLibrary(snapshot=snapshot),
            )
        )

    seen_batch_states = {
        tuple(_expansion_state_signature(lane.current.text) for lane in lanes)
    }
    if expansion_budget.max_depth == 0:
        for lane in lanes:
            if lane.state.limit_reason is None and has_wildcard_syntax(lane.current.text):
                lane.state.stop("max_depth")
    else:
        for depth in range(expansion_budget.max_depth):
            active_lanes = [
                lane for lane in lanes if lane.state.limit_reason is None
            ]
            if not active_lanes:
                break
            replacements_before_pass = sum(
                lane.state.replacement_count for lane in lanes
            )
            for lane in active_lanes:
                lane.state.begin_pass(lane.current)

            for replace_stage in (
                _replace_dynamic,
                _replace_quantified_wildcards,
                _replace_file_wildcards,
            ):
                for lane in active_lanes:
                    if lane.state.limit_reason is None:
                        lane.current = replace_stage(
                            lane.current,
                            lane.state,
                            selector,
                            lane.library,
                        )

            replacements_after_pass = sum(
                lane.state.replacement_count for lane in lanes
            )
            if replacements_after_pass == replacements_before_pass:
                break
            unresolved_lanes = [
                lane
                for lane in lanes
                if lane.state.limit_reason is None
                and has_wildcard_syntax(lane.current.text)
            ]
            if not unresolved_lanes:
                break
            batch_signature = tuple(
                _expansion_state_signature(lane.current.text)
                for lane in lanes
            )
            if batch_signature in seen_batch_states:
                for lane in unresolved_lanes:
                    lane.state.stop("repeated_state")
                break
            seen_batch_states.add(batch_signature)
            if depth + 1 >= expansion_budget.max_depth:
                for lane in unresolved_lanes:
                    lane.state.stop("max_depth")
                break

    return tuple(
        WildcardExpansionResult(
            text=lane.current.text,
            changed=lane.current.text != lane.source,
            used_keys=tuple(lane.library.used),
            missing_keys=tuple(lane.library.missing),
            replacement_count=lane.state.replacement_count,
            limit_reason=(
                lane.state.limit_reason
                or ("cycle" if lane.state.cycle_detected else None)
            ),
        )
        for lane in lanes
    )



def expand_wildcards(
    text: str,
    seed=0,
    mode: str = WILDCARD_MODE_POPULATE,
    extra_paths: str | None = None,
    roots: Iterable[Path] | None = None,
    budget: WildcardExpansionBudget | None = None,
) -> WildcardExpansionResult:
    return expand_wildcard_texts(
        (text,),
        seed=seed,
        mode=mode,
        extra_paths=extra_paths,
        roots=roots,
        budget=budget,
    )[0]
