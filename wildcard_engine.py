from __future__ import annotations

import fnmatch
import os
import random
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

try:
    import numpy as np
except Exception:  # pragma: no cover - ComfyUI normally provides numpy.
    np = None

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
WILDCARD_MODE_REPRODUCE = "reproduce"
WILDCARD_MODES = (
    WILDCARD_MODE_POPULATE,
    WILDCARD_MODE_FIXED,
    WILDCARD_MODE_SEQUENTIAL,
    WILDCARD_MODE_REPRODUCE,
)
WILDCARD_MODE_LABELS = (
    "일반 채우기",
    "고정",
    "순차",
    "재현",
)
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
    WILDCARD_MODE_REPRODUCE: WILDCARD_MODE_REPRODUCE,
    "재현": WILDCARD_MODE_REPRODUCE,
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
REPLACE_DEPTH = 100
WILDCARD_EXTENSIONS = {".txt", ".yaml", ".yml"}

COMMENT_RE = re.compile(r"^\s*#.*(?:\n|$)", re.MULTILINE)
DYNAMIC_RE = re.compile(r"(?<!\\)\{((?:[^{}]|(?<=\\)[{}])*?)(?<!\\)\}")
WILDCARD_RE = re.compile(r"__(?P<keyword>[\w.\-+/*\\]+?)__", re.IGNORECASE)
WILDCARD_FULL_RE = re.compile(r"^__(?P<keyword>[\w.\-+/*\\]+?)__$", re.IGNORECASE)
WILDCARD_QUANTIFIER_RE = re.compile(
    r"(?P<quantifier>\d+)#__(?P<keyword>[\w.\-+/*\\]+?)__",
    re.IGNORECASE,
)
WEIGHT_PREFIX_RE = re.compile(r"^\s*([+-]?(?:\d+(?:\.\d*)?|\.\d+))::(.*)$", re.DOTALL)


@dataclass(frozen=True)
class WildcardOption:
    text: str
    weight: float = 1.0


@dataclass(frozen=True)
class WildcardExpansionResult:
    text: str
    changed: bool
    used_keys: tuple[str, ...] = ()
    missing_keys: tuple[str, ...] = ()


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


def normalize_seed(value) -> int:
    try:
        seed = int(value)
    except (TypeError, ValueError):
        seed = 0
    return max(0, min(MAX_SEED, seed))


def next_seed(seed, control: str) -> int:
    seed = normalize_seed(seed)
    control = str(control or SEED_CONTROL_FIXED).strip()
    if control == SEED_CONTROL_RANDOMIZE:
        return random.SystemRandom().randrange(0, MAX_SEED + 1)
    if control == SEED_CONTROL_INCREMENT:
        return (seed + 1) & MAX_SEED
    if control == SEED_CONTROL_DECREMENT:
        return (seed - 1) & MAX_SEED
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
    if isinstance(data, dict):
        aggregate = []
        for raw_key, value in data.items():
            child_key = _normalize_wildcard_key(raw_key)
            if child_key is None:
                continue
            path_key = f"{prefix}/{child_key}" if prefix else child_key
            child_entries = _yaml_entries(value, path_key)
            for key, options in child_entries.items():
                entries.setdefault(key, []).extend(options)
                aggregate.extend(options)
        if prefix and aggregate:
            entries.setdefault(prefix, []).extend(aggregate)
        return entries
    if isinstance(data, list):
        options = []
        for item in data:
            if isinstance(item, (dict, list)):
                child_entries = _yaml_entries(item, prefix)
                for key, child_options in child_entries.items():
                    entries.setdefault(key, []).extend(child_options)
                    options.extend(child_options)
                continue
            option = _parse_option(_stringify_yaml_scalar(item))
            if option is not None:
                options.append(option)
        if prefix and options:
            entries.setdefault(prefix, []).extend(options)
        return entries
    if prefix:
        option = _parse_option(_stringify_yaml_scalar(data))
        if option is not None:
            entries[prefix] = [option]
    return entries


def _load_yaml_entries(path: Path) -> dict[str, list[WildcardOption]]:
    if yaml is None:
        return {}
    try:
        data = yaml.safe_load(_read_text_file(path))
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


def _load_wildcard_map(roots: Iterable[Path]) -> dict[str, list[WildcardOption]]:
    mapping: dict[str, list[WildcardOption]] = {}
    for root in roots:
        if not root.is_dir():
            continue
        for path in sorted(root.rglob("*"), key=lambda item: item.as_posix().lower()):
            if not path.is_file() or path.suffix.lower() not in WILDCARD_EXTENSIONS:
                continue
            try:
                entries = _load_wildcard_file(root, path)
            except OSError:
                continue
            for key, options in entries.items():
                if key not in mapping and options:
                    mapping[key] = options
    return mapping


def list_wildcards(extra_paths: str | None = None, roots: Iterable[Path] | None = None) -> list[str]:
    mapping = _load_wildcard_map(roots if roots is not None else resolve_wildcard_roots(extra_paths))
    return sorted(mapping)


def wildcard_sources_signature(extra_paths: str | None = None, roots: Iterable[Path] | None = None) -> dict:
    resolved_roots = [Path(root) for root in (roots if roots is not None else resolve_wildcard_roots(extra_paths))]
    files = []
    for root in resolved_roots:
        if not root.is_dir():
            continue
        for path in sorted(root.rglob("*"), key=lambda item: item.as_posix().lower()):
            if not path.is_file() or path.suffix.lower() not in WILDCARD_EXTENSIONS:
                continue
            try:
                stat = path.stat()
                relative = path.relative_to(root).as_posix()
            except OSError:
                continue
            files.append({
                "root": str(root),
                "path": relative,
                "mtime_ns": stat.st_mtime_ns,
                "size": stat.st_size,
            })
    return {"roots": [str(root) for root in resolved_roots], "files": files}


class _Selector:
    def __init__(self, seed: int, sequential: bool):
        self.seed = normalize_seed(seed)
        self.sequential = sequential
        if np is not None:
            self.rng = np.random.default_rng(self.seed)
        else:
            self.rng = random.Random(self.seed)

    def count_from_range(self, minimum: int, maximum: int) -> int:
        minimum = max(0, minimum)
        maximum = max(minimum, maximum)
        if minimum == maximum:
            return minimum
        if self.sequential:
            return minimum + (self.seed % (maximum - minimum + 1))
        if np is not None:
            return int(self.rng.integers(minimum, maximum + 1))
        return self.rng.randint(minimum, maximum)

    def choose_one(self, options: list[WildcardOption]) -> WildcardOption | None:
        selected = self.choose_many(options, 1)
        return selected[0] if selected else None

    def choose_many(self, options: list[WildcardOption], count: int) -> list[WildcardOption]:
        if not options or count <= 0:
            return []
        count = min(count, len(options))
        if self.sequential:
            start = self.seed % len(options)
            return [options[(start + offset) % len(options)] for offset in range(count)]

        weights = [max(0.0, option.weight) for option in options]
        total = sum(weights)
        if np is not None:
            probabilities = [weight / total for weight in weights] if total > 0 else None
            indices = self.rng.choice(len(options), size=count, replace=False, p=probabilities)
            return [options[int(index)] for index in indices]

        if total > 0:
            selected = []
            pool = list(options)
            pool_weights = weights[:]
            for _ in range(count):
                choice = self.rng.choices(pool, weights=pool_weights, k=1)[0]
                index = pool.index(choice)
                selected.append(choice)
                pool.pop(index)
                pool_weights.pop(index)
            return selected
        return self.rng.sample(options, count)


class _WildcardLibrary:
    def __init__(self, roots: Iterable[Path]):
        self.mapping = _load_wildcard_map(roots)
        self.used: list[str] = []
        self.missing: list[str] = []

    def _record_used(self, key: str) -> None:
        if key not in self.used:
            self.used.append(key)

    def _record_missing(self, key: str) -> None:
        if key not in self.missing:
            self.missing.append(key)

    def options_for(self, raw_key: str) -> list[WildcardOption]:
        key = _normalize_wildcard_key(raw_key)
        if key is None:
            return []
        options = self._options_for_normalized_key(key)
        if options:
            self._record_used(key)
        else:
            self._record_missing(key)
        return options

    def _options_for_normalized_key(self, key: str) -> list[WildcardOption]:
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


def _parse_count_spec(spec: str, selector: _Selector) -> int:
    text = str(spec or "").strip()
    if not text:
        return 1
    if "-" in text:
        left, _, right = text.partition("-")
        minimum = int(left) if left.strip() else 0
        maximum = int(right) if right.strip() else minimum
        return selector.count_from_range(minimum, maximum)
    try:
        return max(0, int(text))
    except ValueError:
        return 1


def _expand_multiselect_options(options: list[WildcardOption], library: _WildcardLibrary) -> list[WildcardOption]:
    if len(options) != 1:
        return options
    match = WILDCARD_FULL_RE.match(options[0].text.strip())
    if not match:
        return options
    return library.options_for(match.group("keyword"))


def _replace_dynamic(text: str, selector: _Selector, library: _WildcardLibrary) -> str:
    def replace(match: re.Match) -> str:
        body = match.group(1)
        raw_options = _split_unescaped(body, "|")
        if not raw_options:
            return match.group(0)
        first_parts = raw_options[0].split("$$")
        if len(first_parts) > 1:
            count = _parse_count_spec(first_parts[0], selector)
            separator = ", "
            if len(first_parts) == 2:
                first_candidate = first_parts[1]
            else:
                separator = first_parts[1]
                first_candidate = "$$".join(first_parts[2:])
            candidate_text = "|".join([first_candidate, *raw_options[1:]])
            options = _expand_multiselect_options(_parse_dynamic_options(candidate_text), library)
            selected = selector.choose_many(options, count)
            return separator.join(option.text for option in selected) if selected else match.group(0)

        options = _parse_dynamic_options(body)
        selected = selector.choose_one(options)
        return selected.text if selected is not None else match.group(0)

    return DYNAMIC_RE.sub(replace, text)


def _replace_quantified_wildcards(text: str, selector: _Selector, library: _WildcardLibrary) -> str:
    def replace(match: re.Match) -> str:
        count = max(0, int(match.group("quantifier")))
        options = library.options_for(match.group("keyword"))
        selected = selector.choose_many(options, count)
        return ", ".join(option.text for option in selected) if selected else match.group(0)

    return WILDCARD_QUANTIFIER_RE.sub(replace, text)


def _replace_file_wildcards(text: str, selector: _Selector, library: _WildcardLibrary) -> str:
    def replace(match: re.Match) -> str:
        options = library.options_for(match.group("keyword"))
        selected = selector.choose_one(options)
        return selected.text if selected is not None else match.group(0)

    return WILDCARD_RE.sub(replace, text)


def expand_wildcards(
    text: str,
    seed=0,
    mode: str = WILDCARD_MODE_POPULATE,
    extra_paths: str | None = None,
    roots: Iterable[Path] | None = None,
) -> WildcardExpansionResult:
    mode = normalize_wildcard_mode(mode)
    selector = _Selector(normalize_seed(seed), sequential=mode == WILDCARD_MODE_SEQUENTIAL)
    library = _WildcardLibrary(roots if roots is not None else resolve_wildcard_roots(extra_paths))

    current = COMMENT_RE.sub("", str(text or ""))
    for _ in range(REPLACE_DEPTH):
        previous = current
        current = _replace_dynamic(current, selector, library)
        current = _replace_quantified_wildcards(current, selector, library)
        current = _replace_file_wildcards(current, selector, library)
        if current == previous:
            break
    return WildcardExpansionResult(
        text=current,
        changed=current != str(text or ""),
        used_keys=tuple(library.used),
        missing_keys=tuple(library.missing),
    )
