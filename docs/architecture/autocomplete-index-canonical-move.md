# Autocomplete index canonical package move

- Owner issue: [#186](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/186)
- Prerequisite behavior owner:
  [#162](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/162) — complete
- Roadmap unit: D-11a
- Parent roadmap unit: D-11 Autocomplete
- PR type: Move
- Baseline: `dev@8183aaf472d5cf88978c1dfe20f7bc5ca7d1895c`
- State: READY
- Behavior changes: forbidden

## Responsibility boundary

The root `autocomplete_index.py` is the dependency leaf of D-11. It owns the
versioned SQLite index model, metadata validation, ranked query, atomic rebuild,
corruption recovery, and per-index-path process-local locks.

D-11a moves that file unchanged to:

- `easyuse_anima.autocomplete.index`.

The root module becomes an explicit direct re-export shim. The still-root
`autocomplete_dataset.py` imports the canonical index owner but otherwise
remains unchanged. Dataset source discovery, CSV snapshot/cache, prompt
classification, fallback ranking, and public search/status behavior belong to
D-11b.

## Symbol inventory

Supported module-owned root symbols:

- `AUTOCOMPLETE_INDEX_SCHEMA_VERSION`;
- `AutocompleteIndexSource`;
- `IndexedAutocompleteEntry`;
- `AutocompleteIndexDiagnostics`;
- `AutocompleteIndexResult`;
- `AutocompleteIndexUnavailable`; and
- `search_autocomplete_index`.

The root shim must list exactly these seven names in `__all__` and bind each as
the identical canonical object. It must not wrap, proxy, use `import *`, or
re-export imported `sqlite3`, `tempfile`, hashing, path, or typing objects.

Unsupported private/test seams remain canonical-owner details:

- `_InvalidAutocompleteIndex`;
- `_INDEX_LOCKS`, `_INDEX_LOCKS_GUARD`, and `_SQLITE_TIMEOUT_SECONDS`;
- `_index_path`, `_index_lock`, `_is_locked_error`, `_readonly_connection`,
  `_read_metadata`, `_prefix_upper_bound`, `_glob_pattern`,
  `_category_clause`, `_fetch_tier`, `_query_rows`, `_query_index`,
  `_create_schema`, `_build_index`, and `_query_or_invalid`.

## Caller and alias inventory

Production:

- `autocomplete_dataset.py` is the only production consumer. Its four index
  imports move from the root module to `easyuse_anima.autocomplete.index`.
- No API route, node, frontend, or benchmark imports the index directly.

Tests/tools:

- `tests/test_autocomplete_index.py` imports the root index module and patches
  private lock/build/query seams. It moves behavior patches to the canonical
  module and adds root/canonical identity coverage.
- `tools/benchmark_autocomplete.py` imports only `autocomplete_dataset` and is
  unchanged.
- package skeleton, Registry scanner, backend analyzer, and exact archive
  fixtures gain the canonical package/module and retain the root shim.

The root `autocomplete_dataset.py` retains its standalone-import fallback, but
both branches target the canonical package. No canonical module may import the
root index shim.

## Global state and lifecycle inventory

- `AUTOCOMPLETE_INDEX_SCHEMA_VERSION` remains integer `1`.
- `_SQLITE_TIMEOUT_SECONDS` remains `0.1`.
- `_INDEX_LOCKS` remains one module-owned mutable `dict` keyed by normalized
  absolute index path.
- `_INDEX_LOCKS_GUARD` remains one module-owned `threading.Lock`.
- `_index_lock` retains call-time lock creation and does not resolve a path
  before the directory exists.
- SQLite connections remain operation-local and close on the same paths.
- atomic rebuild continues to use same-directory temporary files and
  `os.replace`; temporary cleanup remains in the same `finally` boundary.
- No import-time directory creation, source/index read, SQLite connection,
  lock acquisition, rebuild, background worker, or cleanup is introduced.
- Lock/runtime ownership migration is deferred to E-05.

## Behavior constraints

- Preserve schema/user version, metadata fields, source identity/revision, and
  backend validation.
- Preserve FTS5/prefix fallback selection, query tiers, deduplication, category
  filter, ranking/order, limit, and diagnostics.
- Preserve lock/busy classification, readonly URI, rebuild retry, atomic
  replace, corruption/schema/source mismatch recovery, and exceptions.
- Preserve exact dataclass fields, frozen/slots behavior, return types, and
  result tuples.
- Preserve Windows/Linux path behavior and package import side-effect freedom.

## Allowed-file boundary

Production:

- root `autocomplete_index.py`;
- index import lines only in root `autocomplete_dataset.py`;
- new `easyuse_anima/autocomplete/__init__.py`; and
- new `easyuse_anima/autocomplete/index.py`.

Supporting:

- `tests/test_autocomplete_index.py`;
- Python package skeleton, Registry scanner, backend analyzer, import boundary,
  and their exact fixtures;
- `docs/architecture/python-compatibility-shims.md`;
- this document; and
- `docs/architecture/python-backend-execution-roadmap.md`.

## Forbidden changes

- index schema/version/metadata, query/ranking, rebuild/fallback, timeout,
  locking, cache, diagnostics, path, error, API, or return behavior;
- dataset source discovery, CSV load/snapshot/cache, classification, fallback
  search, API offload, frontend, workflow, node, Registry metadata, release, or
  instance behavior;
- D-11b dataset/search/cache, D-12+, API route, or E-series lifecycle work; and
- server, browser, live-instance, benchmark, model, or provider execution.

## Validation and exit

- focused index query/rebuild/fallback/concurrency tests;
- exact root/canonical identity for seven supported symbols;
- pre-move/canonical AST parity;
- package skeleton, import boundary, Registry scanner, backend analyzer, and
  actual packed-archive closure;
- official full runner once at the PR checkpoint; and
- root `autocomplete_index.py` contains only explicit direct re-exports while
  the production dataset consumer imports the canonical index.
