from __future__ import annotations

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
        _DEFAULT_WILDCARD_SNAPSHOTS,
        _SNAPSHOT_CACHE_LIMIT,
        _build_wildcard_snapshot,
        _WildcardSnapshot,
    )
except ImportError:
    from easyuse_anima.wildcard.snapshot import (
        _DEFAULT_WILDCARD_SNAPSHOTS,
        _SNAPSHOT_CACHE_LIMIT,
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

try:
    from .easyuse_anima.wildcard.selector import _Selector
except ImportError:
    from easyuse_anima.wildcard.selector import _Selector

try:
    from .easyuse_anima.wildcard.expansion import (
        COMMENT_RE as COMMENT_RE,
        COUNT_SPEC_RE as COUNT_SPEC_RE,
        DYNAMIC_RE as DYNAMIC_RE,
        WILDCARD_FULL_RE as WILDCARD_FULL_RE,
        WILDCARD_QUANTIFIER_RE as WILDCARD_QUANTIFIER_RE,
        WILDCARD_RE as WILDCARD_RE,
        _bounded_output_prefix as _bounded_output_prefix,
        _expand_multiselect_options as _expand_multiselect_options,
        _expand_snapshot_texts,
        _expansion_state_signature as _expansion_state_signature,
        _ExpansionLane as _ExpansionLane,
        _ExpansionSegment as _ExpansionSegment,
        _ExpansionState as _ExpansionState,
        _ExpansionText as _ExpansionText,
        _parse_count_spec as _parse_count_spec,
        _parse_dynamic_options as _parse_dynamic_options,
        _replace_dynamic as _replace_dynamic,
        _replace_file_wildcards as _replace_file_wildcards,
        _Replacement as _Replacement,
        _replace_quantified_wildcards as _replace_quantified_wildcards,
        _split_unescaped as _split_unescaped,
        _utf8_length as _utf8_length,
        _utf8_width as _utf8_width,
        has_wildcard_syntax as has_wildcard_syntax,
    )
except ImportError:
    from easyuse_anima.wildcard.expansion import (
        COMMENT_RE as COMMENT_RE,
        COUNT_SPEC_RE as COUNT_SPEC_RE,
        DYNAMIC_RE as DYNAMIC_RE,
        WILDCARD_FULL_RE as WILDCARD_FULL_RE,
        WILDCARD_QUANTIFIER_RE as WILDCARD_QUANTIFIER_RE,
        WILDCARD_RE as WILDCARD_RE,
        _bounded_output_prefix as _bounded_output_prefix,
        _expand_multiselect_options as _expand_multiselect_options,
        _expand_snapshot_texts,
        _expansion_state_signature as _expansion_state_signature,
        _ExpansionLane as _ExpansionLane,
        _ExpansionSegment as _ExpansionSegment,
        _ExpansionState as _ExpansionState,
        _ExpansionText as _ExpansionText,
        _parse_count_spec as _parse_count_spec,
        _parse_dynamic_options as _parse_dynamic_options,
        _replace_dynamic as _replace_dynamic,
        _replace_file_wildcards as _replace_file_wildcards,
        _Replacement as _Replacement,
        _replace_quantified_wildcards as _replace_quantified_wildcards,
        _split_unescaped as _split_unescaped,
        _utf8_length as _utf8_length,
        _utf8_width as _utf8_width,
        has_wildcard_syntax as has_wildcard_syntax,
    )

try:
    from .easyuse_anima.wildcard.library import (
        _WildcardLibrary as _WildcardLibraryCore,
    )
except ImportError:
    from easyuse_anima.wildcard.library import (
        _WildcardLibrary as _WildcardLibraryCore,
    )

def _wildcard_snapshot(roots: Iterable[Path]) -> _WildcardSnapshot:
    return _DEFAULT_WILDCARD_SNAPSHOTS.snapshot_for_roots(
        roots,
        scan_sources=_wildcard_sources._scan_wildcard_sources,
        build_snapshot=_build_wildcard_snapshot,
    )


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


class _WildcardLibrary(_WildcardLibraryCore):
    def __init__(
        self,
        roots: Iterable[Path] | None = None,
        *,
        snapshot: _WildcardSnapshot | None = None,
    ):
        if snapshot is None:
            snapshot = _wildcard_snapshot(roots or ())
        super().__init__(snapshot)


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
    return _expand_snapshot_texts(
        sources,
        selector,
        snapshot,
        expansion_budget,
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
