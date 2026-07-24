# D-12c Wildcard snapshot materialization canonical Move

- Owner issue: [#186](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/186)
- Behavior prerequisites:
  [#159](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/159) and
  [#160](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/160) — complete
- Roadmap unit: D-12c
- Parent roadmap unit: D-12 Wildcard
- PR type: Move
- Baseline: `dev@6f32f88b3e484a7e14751f8c179daa8758c2fcd5`
- State: READY
- Production behavior changes: forbidden

## Responsibility boundary

After D-12b, `easyuse_anima.wildcard.sources` owns source discovery and
parsing, while root `wildcard_engine.py` owns both immutable snapshot
materialization and mutable snapshot publication/cache lifecycle.

D-12c separates only the immutable value/materialization leaf:

- `_WildcardSnapshot`; and
- `_build_wildcard_snapshot`.

They move to:

- `easyuse_anima.wildcard.snapshot`.

Root retains source-state verification, publication, cache lookup/eviction,
condition waiting, single-flight coordination, retry, and every public
listing/signature/expansion caller. This keeps D-12c a Move and leaves runtime
ownership/factory/cleanup decisions to the later lifecycle slice and E-06.

## Moved symbol inventory

### `_WildcardSnapshot`

Immutable fields:

- `cache_key`;
- immutable mapping of normalized names to `WildcardOption` tuples;
- sorted `wildcard_names`;
- stringified root paths;
- immutable source-file metadata tuple; and
- `cacheable`.

Its `public_signature()` projection remains part of the moved value object and
keeps the existing roots/files payload shape.

### `_build_wildcard_snapshot`

Materialization behavior:

- consumes one immutable `_WildcardSourceState`;
- loads each source through canonical source parsing;
- preserves first-root/first-key precedence;
- ignores empty option lists;
- marks a candidate non-cacheable after a transient `OSError`;
- freezes option lists into tuples and the mapping into `MappingProxyType`;
- sorts public wildcard names; and
- copies source cache key, roots, and file metadata without mutation.

The function owns no cache lookup, publication, retry loop, lock, condition,
or cleanup.

## Caller and alias inventory

Root direct aliases:

- `wildcard_engine._WildcardSnapshot`; and
- `wildcard_engine._build_wildcard_snapshot`.

These private names remain direct aliases to the identical canonical objects.
They are retained as compatibility/test seams but are not added to a supported
public `__all__`.

Root runtime callers:

- `_wildcard_snapshot` calls the root-bound build alias after acquiring the
  source-state single-flight lane;
- `_SNAPSHOT_CACHE` keeps `_WildcardSnapshot` values;
- `_load_wildcard_map` returns a mutable copy of snapshot options;
- `list_wildcards` reads `wildcard_names`;
- `wildcard_sources_signature` calls `public_signature`;
- `_WildcardLibrary` reuses the immutable mapping; and
- expansion entrypoints acquire a root-owned snapshot before selection and
  replacement.

External production callers do not import the private snapshot symbols.
Nodes and API surfaces continue to use root public listing/signature/expansion
helpers unchanged.

Tests:

- `tests/test_wildcards.py` keeps root patch seams for build blocking,
  file-change retry, single-flight, and atomic-publication coverage;
- it adds exact root/canonical identity and immutable materialization coverage;
- package skeleton and Registry scanner include the canonical module; and
- backend analyzer fixtures record the canonical dependency graph.

## Global-state inventory

D-12c moves no mutable runtime state.

Root retains:

- `_SNAPSHOT_CACHE_LIMIT`;
- `_SNAPSHOT_CONDITION`;
- `_SNAPSHOT_CACHE`;
- `_SNAPSHOT_BUILDING`;
- source-state rescan verification;
- cache hit/LRU mutation and eviction;
- wait/notify and single-flight ownership;
- exception propagation and retry; and
- publication eligibility decisions based on `cacheable`.

Canonical `snapshot.py` contains only:

- immutable type definitions;
- a stateless materialization function; and
- imports of canonical source/model types and helpers.

It creates no module-level mutable container, lock, condition, singleton,
factory, background task, cleanup hook, or dependency-injection seam.

## Compatibility and behavior invariants

- exact root private identity is retained without wrapper, proxy, duplicate
  class, or lazy module hook;
- mapping precedence, empty-option behavior, normalized keys, tuple freezing,
  mapping immutability, wildcard-name ordering, root ordering, file metadata,
  cache-key shape, and public signature shape are unchanged;
- transient loader `OSError` still returns a non-cacheable snapshot candidate;
- malformed YAML remains a cacheable empty parse as owned by canonical sources;
- source changes during build still force root rescan and retry before publish;
- same-key parallel requests still build once and publish atomically;
- failed builds still clear the root building key and notify waiters;
- cache capacity, eviction ordering, condition timing, and exception behavior
  are unchanged;
- selector, PCG64, seed control, expansion, budgets, diagnostics, API, nodes,
  workflows, and frontend behavior are unchanged; and
- import timing remains package-internal with no root import from canonical
  snapshot code.

## Allowed-file boundary

Production:

- root `wildcard_engine.py`; and
- new `easyuse_anima/wildcard/snapshot.py`.

Supporting:

- wildcard snapshot identity/materialization and existing lifecycle tests;
- package skeleton, Registry scanner, backend analyzer, and exact fixture;
- this inventory, compatibility-shim ledger, and execution roadmap.

## Forbidden

- moving or changing `_wildcard_snapshot`;
- moving or changing cache/condition/building/limit state;
- cache policy, capacity, key, eviction, retry, publication, wait/notify,
  single-flight, factory, or cleanup changes;
- source discovery/parsing changes;
- list/signature payload changes;
- selector, PRNG, seed, mode, expansion, budget, or diagnostics changes;
- G-03 completed-package enrollment before full D-12 completion;
- API, node, bootstrap, frontend, workflow, Registry metadata, release, or
  instance changes; and
- server, browser, live-instance, model, provider, or network execution.

## Validation and exit

- exact root/canonical identity for both moved private names;
- immutable mapping, tuple options, ordering, precedence, signature, and
  transient-read cacheability behavior;
- existing file-change retry, same-key single-flight, atomic publication,
  failure cleanup, and mutable-copy tests remain unchanged;
- package skeleton, Registry scanner, backend analyzer, and packed archive
  include canonical `snapshot.py`;
- canonical snapshot has zero root imports and no mutable globals;
- official full runner once at the PR checkpoint; and
- root retains every lifecycle/global-state and public behavior caller.
