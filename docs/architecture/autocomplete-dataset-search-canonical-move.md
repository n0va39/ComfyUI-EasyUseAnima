# D-11b Autocomplete dataset and search canonical Move

- Owner issue: [#186](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/186)
- Behavior prerequisite:
  [#162](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/162) — complete
- Roadmap unit: D-11b
- Parent roadmap unit: D-11 Autocomplete
- PR type: Move
- Baseline: `dev@9c293ee744c137f4722408213f3514260e029dc4`
- State: READY
- Production behavior changes: forbidden

## Responsibility boundary

The remaining root `autocomplete_dataset.py` combines three responsibilities:

1. source metadata, CSV parsing, immutable snapshots, single-flight cache, and
   status;
2. indexed search orchestration and exact Python fallback ranking; and
3. prompt-token parsing and classification, which still depends on the
   temporary root `anima_prompt` package.

Moving the whole file now would make the enrolled canonical autocomplete
package import a root implementation and violate G-03. D-11b therefore moves
only the first two dependency-safe owners:

- `easyuse_anima.autocomplete.dataset`; and
- `easyuse_anima.autocomplete.search`.

Root `autocomplete_dataset.py` keeps prompt classification until D-13
canonicalizes `anima_prompt`. A later D-11 completion slice may then move
classification and convert the root module into its final explicit shim.

## Supported moved surface

Dataset/source/cache/status:

- `DBR_TAG_ARCHIVE_SOURCE`;
- `DBR_TAG_ARCHIVE_LICENSE`;
- `DBR_DANBOORU_AUTOCOMPLETE_CSV`;
- `DBR_E621_AUTOCOMPLETE_CSV`;
- `DBR_MERGED_AUTOCOMPLETE_CSV`;
- `LOCALSMILE_AUTOCOMPLETE_CSV`;
- `AUTOCOMPLETE_CSV`;
- `DEFAULT_AUTOCOMPLETE_SOURCE`;
- `AUTOCOMPLETE_SOURCES`;
- `AutocompleteEntry`;
- `resolve_autocomplete_source`;
- `available_autocomplete_sources`; and
- `autocomplete_status`.

Search:

- `search_autocomplete`.

Root binds each moved supported name directly to the identical canonical
object. No wrapper, proxy, subclass, duplicate constant, `import *`, or lazy
module hook is allowed.

`classify_prompt_text` remains root-owned in this slice.

## Private owner inventory

Dataset private data and helpers:

- `_AutocompleteCacheKey`, `_AutocompleteSnapshot`,
  `_AutocompleteSourceChanged`;
- `_AUTOCOMPLETE_CACHE_SCHEMA_VERSION`,
  `_AUTOCOMPLETE_CACHE_LOAD_ATTEMPTS`, `_MISSING_FILE_STAT`;
- `_INLINE_SPACE_RE`, category maps, CSV/category normalization and entry
  construction helpers;
- `_load_entries`, cache-key construction, snapshot construction/loading,
  snapshot/entry/status accessors, and built-in manifest count lookup.

Search private data and helpers:

- `_AUTOCOMPLETE_INDEX_DIR` and its default-path resolver;
- exact match scoring, bounded `heapq.nsmallest` fallback ranking;
- index source/revision validation and fallback diagnostics; and
- `_search_autocomplete_with_diagnostics`.

Private names are canonical test and benchmark seams, not newly supported
public API.

## Caller and alias inventory

Production:

- `api.py` imports source/status/search directly from canonical owners and
  continues importing `classify_prompt_text` from root.
- root `autocomplete_dataset.py` imports canonical dataset internals needed by
  classification and directly aliases all moved supported names.
- canonical search imports canonical dataset and index owners only.
- no node or frontend module imports these Python implementations directly.

Tests and tools:

- `tests/test_autocomplete_index.py` moves cache/search private patches to
  canonical owners and retains root/canonical public identity coverage.
- `tests/test_prompt_corrector.py` moves dataset/search private patches to
  canonical owners. Public root imports remain compatibility coverage.
- `tools/benchmark_autocomplete.py` uses canonical owners because it exercises
  private cache/index seams.
- package skeleton, Registry scanner, backend analyzer, import boundary, and
  exact fixtures gain both canonical modules while retaining the root partial
  compatibility module.

## Global-state inventory

Dataset owner:

- `_CACHE_LOCK`: one process-local `threading.Lock`;
- `_CACHE`: resolved-path keyed immutable snapshot dictionary; and
- `_INFLIGHT`: cache-key keyed `Future` dictionary for single-flight loading.

Search owner:

- `_AUTOCOMPLETE_INDEX_DIR`: import-time default derived from canonical package
  and user-data paths; `None` preserves standalone read-only behavior.

The state moves without changing lifetime, initialization time, keying,
locking, retry count, exception propagation, invalidation, or test reset
semantics. Runtime factories, cleanup, dependency injection, and lifecycle
ownership remain E-05.

## Compatibility and behavior invariants

- source keys, labels, paths, entry counts, source/license metadata, and
  selection fallback are unchanged;
- CSV encoding/header detection, category normalization, sort order, immutable
  entry map, stat revision, missing/non-file policy, four-attempt retry, and
  single-flight behavior are unchanged;
- status path/existence/count/mtime payloads and built-in manifest fast path
  are unchanged;
- indexed query parameters, revision validation, fallback reasons, result
  ordering, limit clamping, category filtering, elapsed rounding, and payload
  shape are unchanged;
- the D-11a SQLite schema/query/rebuild owner is unchanged;
- prompt parsing, token classification, labels, comments, wildcard/dynamic
  syntax, and `classify_prompt_text` remain unchanged in root; and
- API offload, route, response redaction, frontend, workflow, and node behavior
  are unchanged.

## Allowed-file boundary

Production:

- root `autocomplete_dataset.py`;
- autocomplete import lines only in root `api.py`;
- `easyuse_anima/autocomplete/dataset.py`; and
- `easyuse_anima/autocomplete/search.py`.

Supporting:

- autocomplete behavior/index tests and benchmark imports;
- package skeleton, Registry scanner, backend analyzer, import boundary, and
  their exact fixtures;
- this inventory, the compatibility-shim ledger, and execution roadmap.

## Forbidden

- moving or changing prompt classification or any root `anima_prompt` module;
- schema, ranking, cache, retry, concurrency, path, timing, diagnostics, error,
  API, or return behavior;
- adding a G-03 exception or canonical-to-root import;
- E-05 lifecycle/service factories, background cleanup, lock eviction, new
  dependency injection, or state reset API;
- D-12+, API route extraction, frontend, workflow, node, Registry metadata,
  release, or instance changes; and
- server, browser, live-instance, model, provider, or network execution.

## Validation and exit

- dataset source/CSV/cache/snapshot/status focused behavior;
- indexed and fallback search/ranking/concurrency focused behavior;
- exact root/canonical identity for every moved supported name;
- canonical modules have zero root imports and zero G-03 violations;
- package skeleton, Registry scanner, backend analyzer, and packed archive
  include both canonical modules;
- official full runner once at the PR checkpoint; and
- root retains only prompt classification implementation plus explicit
  canonical aliases for the moved surface.
