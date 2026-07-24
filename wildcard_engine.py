from __future__ import annotations

import bisect
from collections import OrderedDict
import fnmatch
import hashlib
import math
import re
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

# NumPy is mandatory in supported ComfyUI runtimes and defines the seeded
# wildcard sampling contract. A stdlib fallback would produce different results.
import numpy as np

try:
    from .easyuse_anima.wildcard.models import (
        DEFAULT_MAX_EXPANSION_DEPTH,
        DEFAULT_MAX_EXPANSION_GROWTH_PER_PASS,
        DEFAULT_MAX_EXPANSION_OUTPUT_CHARS,
        DEFAULT_MAX_EXPANSION_REPLACEMENTS,
        MAX_EXPANSION_DEPTH,
        MAX_EXPANSION_GROWTH_PER_PASS,
        MAX_EXPANSION_OUTPUT_CHARS,
        MAX_EXPANSION_REPLACEMENTS,
        REPLACE_DEPTH,
        WildcardExpansionBudget,
        WildcardExpansionResult,
        WildcardOption,
    )
except ImportError:
    from easyuse_anima.wildcard.models import (
        DEFAULT_MAX_EXPANSION_DEPTH,
        DEFAULT_MAX_EXPANSION_GROWTH_PER_PASS,
        DEFAULT_MAX_EXPANSION_OUTPUT_CHARS,
        DEFAULT_MAX_EXPANSION_REPLACEMENTS,
        MAX_EXPANSION_DEPTH,
        MAX_EXPANSION_GROWTH_PER_PASS,
        MAX_EXPANSION_OUTPUT_CHARS,
        MAX_EXPANSION_REPLACEMENTS,
        REPLACE_DEPTH,
        WildcardExpansionBudget,
        WildcardExpansionResult,
        WildcardOption,
    )

try:
    from .easyuse_anima.wildcard import sources as _wildcard_sources
    from .easyuse_anima.wildcard.sources import (
        DEFAULT_TEST_WILDCARD_FILE,
        DEFAULT_TEST_WILDCARD_TEXT,
        WILDCARD_DIR_NAME,
        WILDCARD_EXTENSIONS,
        default_wildcard_root,
        ensure_default_wildcard_root,
        parse_wildcard_extra_paths,
        resolve_wildcard_roots,
    )
except ImportError:
    from easyuse_anima.wildcard import sources as _wildcard_sources
    from easyuse_anima.wildcard.sources import (
        DEFAULT_TEST_WILDCARD_FILE,
        DEFAULT_TEST_WILDCARD_TEXT,
        WILDCARD_DIR_NAME,
        WILDCARD_EXTENSIONS,
        default_wildcard_root,
        ensure_default_wildcard_root,
        parse_wildcard_extra_paths,
        resolve_wildcard_roots,
    )

try:
    from .easyuse_anima.wildcard.snapshot import (
        _build_wildcard_snapshot,
        _WildcardSnapshot,
    )
except ImportError:
    from easyuse_anima.wildcard.snapshot import (
        _build_wildcard_snapshot,
        _WildcardSnapshot,
    )

try:
    from .easyuse_anima.wildcard.seed import (
        MAX_SEED,
        PUBLIC_MAX_SEED,
        SEED_CONTROL_DECREMENT,
        SEED_CONTROL_FIXED,
        SEED_CONTROL_INCREMENT,
        SEED_CONTROL_MODES,
        SEED_CONTROL_RANDOMIZE,
        next_seed,
        normalize_seed,
    )
except ImportError:
    from easyuse_anima.wildcard.seed import (
        MAX_SEED,
        PUBLIC_MAX_SEED,
        SEED_CONTROL_DECREMENT,
        SEED_CONTROL_FIXED,
        SEED_CONTROL_INCREMENT,
        SEED_CONTROL_MODES,
        SEED_CONTROL_RANDOMIZE,
        next_seed,
        normalize_seed,
    )

try:
    from .easyuse_anima.wildcard.mode import (
        PROMPT_STUDIO_WILDCARD_MODE_LABELS,
        WILDCARD_MODE_ALIASES,
        WILDCARD_MODE_FIXED,
        WILDCARD_MODE_LABELS,
        WILDCARD_MODE_POPULATE,
        WILDCARD_MODE_REPRODUCE,
        WILDCARD_MODE_SEQUENTIAL,
        WILDCARD_MODES,
        normalize_prompt_studio_wildcard_mode,
        normalize_wildcard_mode,
    )
except ImportError:
    from easyuse_anima.wildcard.mode import (
        PROMPT_STUDIO_WILDCARD_MODE_LABELS,
        WILDCARD_MODE_ALIASES,
        WILDCARD_MODE_FIXED,
        WILDCARD_MODE_LABELS,
        WILDCARD_MODE_POPULATE,
        WILDCARD_MODE_REPRODUCE,
        WILDCARD_MODE_SEQUENTIAL,
        WILDCARD_MODES,
        normalize_prompt_studio_wildcard_mode,
        normalize_wildcard_mode,
    )

COMMENT_RE = re.compile(r"^\s*#.*(?:\n|$)", re.MULTILINE)
DYNAMIC_RE = re.compile(r"(?<![\\%])\{((?:[^{}]|(?<=\\)[{}])*?)(?<!\\)\}")
WILDCARD_RE = re.compile(r"__(?P<keyword>[\w.\-+/*\\]+?)__", re.IGNORECASE)
WILDCARD_FULL_RE = re.compile(r"^__(?P<keyword>[\w.\-+/*\\]+?)__$", re.IGNORECASE)
WILDCARD_QUANTIFIER_RE = re.compile(
    r"(?P<quantifier>\d+)#__(?P<keyword>[\w.\-+/*\\]+?)__",
    re.IGNORECASE,
)
COUNT_SPEC_RE = re.compile(
    r"(?:(?P<fixed>\d+)|(?P<minimum>\d*)\s*-\s*(?P<maximum>\d*))"
)

_SNAPSHOT_CACHE_LIMIT = 16
_SNAPSHOT_CONDITION = threading.Condition()
_SNAPSHOT_CACHE: OrderedDict[tuple, _WildcardSnapshot] = OrderedDict()
_SNAPSHOT_BUILDING: set[tuple] = set()


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
                key = _wildcard_sources._normalize_wildcard_key(
                    match.group("keyword")
                )
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


def has_wildcard_syntax(text: str) -> bool:
    value = str(text or "")
    return bool(DYNAMIC_RE.search(value) or WILDCARD_RE.search(value) or WILDCARD_QUANTIFIER_RE.search(value))


def _wildcard_snapshot(roots: Iterable[Path]) -> _WildcardSnapshot:
    resolved_roots = tuple(Path(root) for root in roots)
    while True:
        source_state = _wildcard_sources._scan_wildcard_sources(resolved_roots)
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
            verified_state = _wildcard_sources._scan_wildcard_sources(resolved_roots)
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
        key = _wildcard_sources._normalize_wildcard_key(raw_key)
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
        parsed = _wildcard_sources._parse_option(option)
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
    return (
        library.options_for(raw_key),
        _wildcard_sources._normalize_wildcard_key(raw_key),
    )


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
        key = _wildcard_sources._normalize_wildcard_key(raw_key)
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
        key = _wildcard_sources._normalize_wildcard_key(raw_key)
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
