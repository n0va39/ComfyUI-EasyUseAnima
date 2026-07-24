# D-12b Wildcard sources canonical Move

- Owner issue: [#186](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/186)
- Behavior prerequisites:
  [#159](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/159) and
  [#160](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/160) — complete
- Roadmap unit: D-12b
- Parent roadmap unit: D-12 Wildcard
- PR type: Move
- Baseline: `dev@105a3ae2c4d89bbf6ea2b7369a627e63fbd92847`
- State: READY
- Production behavior changes: forbidden

## Responsibility boundary

After D-12a, root `wildcard_engine.py` still owns source discovery/parsing,
snapshot publication/cache, selector/seed, and expansion. Source discovery and
file parsing form a dependency-free leaf below snapshot and expansion:

- they read roots and TXT/YAML files;
- they produce immutable source metadata and `WildcardOption` lists; and
- they own no mutable cache, lock, selector, or expansion state.

D-12b moves that leaf to:

- `easyuse_anima.wildcard.sources`.

Snapshot construction/publication, cache/condition/single-flight behavior,
listing/signature, selector/PRNG, seed control, and expansion remain in root.

## Supported moved surface

Source constants:

- `WILDCARD_DIR_NAME`;
- `DEFAULT_TEST_WILDCARD_FILE`;
- `DEFAULT_TEST_WILDCARD_TEXT`; and
- `WILDCARD_EXTENSIONS`.

Public source/path helpers:

- `default_wildcard_root`;
- `ensure_default_wildcard_root`;
- `parse_wildcard_extra_paths`; and
- `resolve_wildcard_roots`.

Root binds every moved supported name directly to the identical canonical
object. No wrapper, proxy, duplicate constant, `import *`, or lazy module hook
is allowed.

## Private symbol inventory

Source metadata:

- `_WildcardSourceFile`;
- `_WildcardSourceState`; and
- their existing `cache_key` properties.

Path/source helpers:

- `_comfy_base_path`;
- `_resolve_path`;
- `_normalize_wildcard_key`;
- `_wildcard_root_identity`; and
- `_scan_wildcard_sources`.

Parser/loader helpers:

- `WEIGHT_PREFIX_RE`;
- `_read_text_file`;
- `_parse_option`;
- `_options_from_lines`;
- `_stringify_yaml_scalar`;
- `_yaml_entries`;
- `_load_yaml_entries`; and
- `_load_wildcard_file`.

These private names become canonical snapshot/expansion test seams. They are
not newly supported public API.

## Caller and alias inventory

Production:

- root `wildcard_engine.py` imports the canonical source metadata and private
  helpers needed by snapshot and expansion, while retaining snapshot/selector/
  expansion implementation;
- root `api.py` imports `resolve_wildcard_roots` directly from canonical
  sources and keeps `list_wildcards` from root snapshot behavior;
- root `__init__.py` imports `ensure_default_wildcard_root` directly from
  canonical sources; and
- node source/signature/expansion callers remain root-owned in this slice.

Tests:

- `tests/test_wildcards.py` moves private source/YAML patches to canonical
  sources and keeps root public identity/behavior coverage;
- API and bootstrap tests patch their direct module-bound aliases unchanged;
- package skeleton, Registry scanner, and backend analyzer gain the canonical
  source module and exact graph/fixture evidence.

## Global-state inventory

D-12b moves no mutable runtime state.

Canonical sources has only:

- immutable constants;
- optional module binding `yaml`;
- pure/path/file helper functions; and
- immutable source-state instances created per scan.

Root retains:

- `_SNAPSHOT_CONDITION`;
- `_SNAPSHOT_CACHE`;
- `_SNAPSHOT_BUILDING`;
- `_SNAPSHOT_CACHE_LIMIT`; and
- snapshot, library, selector, expansion-lane, and per-call expansion state.

Snapshot lifecycle/factory/cleanup belongs to the later snapshot slice and
E-06. D-12b creates no cache, singleton, lock, background task, cleanup hook,
factory, or dependency-injection seam.

## Compatibility and behavior invariants

- default root location, sample file name/text, create-on-demand policy, and
  error propagation are unchanged;
- extra-path newline parsing, quote stripping, environment/user expansion,
  Comfy base fallback, resolution, deduplication, and default-root ordering are
  unchanged;
- UTF-8/ISO-8859-1 fallback, comment/blank-line policy, weight parsing and
  clamping, key normalization/rejection, YAML scalar conversion, alias
  aggregation, malformed-YAML handling, extension policy, and root precedence
  are unchanged;
- recursive scan ordering, file filtering, stat metadata, root identity, and
  cache-key shape are unchanged;
- optional PyYAML behavior and import timing are unchanged for source users;
- snapshot/cache/lock/retry/atomic-publish, selector/seed/PCG64, expansion,
  output, diagnostics, API, node, workflow, and frontend behavior are
  unchanged.

## Allowed-file boundary

Production:

- root `wildcard_engine.py`;
- wildcard import lines only in root `api.py`;
- wildcard initialization import line only in root `__init__.py`; and
- new `easyuse_anima/wildcard/sources.py`.

Supporting:

- wildcard source/identity behavior tests;
- package skeleton, Registry scanner, backend analyzer, and exact fixture;
- this inventory, compatibility-shim ledger, and execution roadmap.

## Forbidden

- snapshot construction/publication/cache/lock/single-flight/lifecycle changes;
- list/signature payload changes;
- selector, PRNG, seed, mode, parsing outside source option/YAML parsing,
  expansion, budget enforcement, or diagnostics behavior changes;
- moving snapshot or expansion implementation in this PR;
- G-03 completed-package enrollment before full D-12 completion;
- API route, node, bootstrap behavior, frontend, workflow, Registry metadata,
  release, or instance changes; and
- server, browser, live-instance, model, provider, or network execution.

## Validation and exit

- exact root/canonical identity for every moved supported name;
- source roots, paths, TXT/YAML parsing, scan metadata/order, and source key
  behavior;
- wildcard snapshot/cache/expansion behavior suite remains unchanged;
- package skeleton, Registry scanner, backend analyzer, and packed archive
  include canonical `sources.py`;
- canonical sources has zero root imports;
- official full runner once at the PR checkpoint; and
- root retains all snapshot/cache/selector/seed/expansion implementation.
