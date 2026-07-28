# E-05 Autocomplete Runtime Ownership Contract

## Scope and authority

E-05a is a production-free Contract created from
`dev@e8f3b5b3abb7633aa122dc28956c65f664b017c6` after the completed E-04
translation audit. It classifies current autocomplete source metadata, dataset
snapshot and single-flight state, SQLite index publication state, production
callers, compatibility seams, and the only authorized bounded Move order.
E-05b moves the dataset snapshot/cache/Future state behind its selected
feature-private owner. E-05c moves the immutable index root and retained path-lock
registry behind the second selected owner.

The executable source is
`tests/fixtures/python_autocomplete_runtime_contract.v1.json`, checked by
`tests/test_python_autocomplete_runtime_contract.py`. Existing autocomplete index,
dataset compatibility, locale settings, API, package, and import tests remain the
behavior authorities.

E-05a changes no production Python, analyzer, public export, import closure, cache
policy, index schema, payload, or persistence behavior.

## Declarative source policy

`AUTOCOMPLETE_SOURCES` and the category-name maps remain declarative dataset
metadata. `resolve_autocomplete_source()` selects the requested source and falls
back to the default source when the Korean asset is absent.
`available_autocomplete_sources()` reports the effective selection. The fallback
does not rewrite the stored setting.

These tables are not cache state and must not be absorbed into a mutable runtime
repository. CSV parsing, header detection, category mapping, normalization, and
entry ordering also remain feature behavior owned by the canonical dataset module.

## Two runtime resource boundaries

### Dataset snapshots and Future single-flight

`_DEFAULT_AUTOCOMPLETE_SNAPSHOTS` is the process owner. Its private
`_AutocompleteSnapshotStore` instance owns one Lock, the resolved-path completed
snapshot cache, and the cache-key Future map. Snapshots remain keyed by the resolved
source path plus `mtime_ns`, size, and cache schema version. One loader publishes a
snapshot for a cache key while followers await the same `Future`. Loader exceptions
propagate through that Future, stale snapshots are not published, and a source that
changes during load is retried up to the existing four-attempt bound.

The module `_snapshot_for_key()` and `_cached_snapshot_for_key()` facades resolve
the current default owner at call time. The owner method likewise resolves
`_build_snapshot`, `_cache_key_from_resolved_path`, and `_await_snapshot` at call
time, preserving the direct monkeypatch seams. `clear()` idempotently clears only
completed snapshots; it does not invent a terminal close policy or cancel, remove,
or replace an in-flight Future. Future settlement and whole-runtime shutdown
disposition remain explicit later gates. Classification, search fallback, and
public status continue to observe the same snapshot identity and status semantics.

### Index store root and publication locks

`_DEFAULT_AUTOCOMPLETE_INDEX_STORE` is the process owner. Its private
`_AutocompleteIndexStore` instance owns the immutable Path-or-None root, one guard,
and the retained normalized-path Lock registry. The default root is still resolved
once from the process user-data boundary. When user data and package data resolve to
the same standalone boundary, persistent indexing remains disabled so a package
import cannot write to its source tree.

The lock key still uses `normcase(abspath(path))` without `Path.resolve()` before
the directory exists; changing that can split first Windows access across two locks
for the same eventual file. One per-path lock protects the second validity check,
rebuild, atomic publication, and concurrent reuse. `search.py` resolves its private
store reference at call time, so tests inject an isolated root by replacing the
store instead of mutating a raw root constant.

The public `search_autocomplete_index(*, root, ...)` signature and identity remain
unchanged. Its explicit-root compatibility path delegates to the same default owner
and therefore retains the process-wide per-path lock registry. No generic filesystem
lock service is added. Read-only hit behavior, source/schema/corrupt invalidation,
temporary SQLite construction, backend selection, atomic replace, diagnostics, and
exact Python snapshot fallback remain unchanged. `close()` is an idempotent no-op
because the proven owner has no disposable handle.

The dataset owner and index-store owner are not merged. Their locks protect
different invariants, their failures have different meanings, and index
unavailability intentionally falls back to a valid dataset snapshot.

## Composition and compatibility target

E-05d composes the two feature-private owners in bootstrap and exposes one narrow
autocomplete-owned port through `RuntimeServices`. API adapters may receive or
resolve that port at the adapter boundary. Autocomplete feature modules do not
import the complete runtime, bootstrap, API adapters, or root shims.

The following surfaces remain compatible throughout E-05:

- `autocomplete_dataset.py` and `autocomplete_index.py` remain exact canonical
  identity shims with unchanged `__all__`;
- canonical `search_autocomplete`, `classify_prompt_text`, source-resolution, and
  status functions retain their public identity and result contracts;
- root `api.py` retains call-time callback seams for source resolution, status,
  search, and classification;
- the former import-stable index-root patch seam is replaced by the equivalent
  private isolated-store injection seam;
- package/no-host imports do not create directories or require ComfyUI host state.

E-05 does not add a public runtime/bootstrap/root export or a generic cache/lock
port.

## Bounded Move queue

1. **E-05a Contract — complete:** current state, two target owners, callers,
   compatibility seams, lifecycle gaps, and Move order are versioned.
2. **E-05b Move — dataset snapshot and single-flight ownership — complete:**
   `_AutocompleteSnapshotStore` owns the cache, Future map, and Lock behind one
   default reference while preserving parser, source-change, Future settlement,
   status, and call-time patch behavior.
3. **E-05c Move — index-store root and path-lock ownership — complete:**
   `_AutocompleteIndexStore` owns the immutable root, guard, and retained
   normalized-path Locks behind one default reference.
4. **E-05d Move — bootstrap composition and adapter wiring:** compose both owners,
   add only a narrow autocomplete port to RuntimeServices, and preserve every
   canonical/root identity and call-time adapter seam.
5. **E-05e Contract — completion audit:** reconcile E-01 targets, cleanup
   dispositions, import safety, root identities, and zero ambiguous autocomplete
   state before E-06.

Each Move is a separate PR and rollback boundary. E-09 retains whole-runtime reverse
close ordering and partial-initialization cleanup. E-05 supplies only the
feature-owned resources and their proven cleanup shapes.

E-05b leaves no duplicate module cache/lock/Future map, and E-05c leaves no raw
module root or index-lock registry. The next READY unit is the separate E-05d
bootstrap composition and narrow adapter wiring Move.

## Preserved behavior

All E-05 Moves preserve:

- source selection, missing-source fallback, settings non-persistence, manifest
  count fast path, and arbitrary-path exact count;
- CSV parsing, category normalization, tag/search normalization, duplicate handling,
  ranking, category filtering, and limit clamping;
- snapshot cache key, source-change retry, single-loader publication, follower wait,
  Future exception propagation, and stale-publication rejection;
- SQLite schema/version, source identity/revision, FTS5 or prefix backend,
  corruption/schema/source rebuild, read-only queries, temporary build, atomic
  replace, and diagnostics;
- locked/unreadable/build-failed fallback to exact Python snapshot results;
- public payload/status/error meaning, root identities, API callback timing,
  package/no-host import, and no import-time host I/O.

Repository/schema/persistence/error/ranking policy changes are Behavior and remain
out of scope.

## Stop conditions

Stop the owning Move if it requires a feature-to-runtime/API/bootstrap/root
back-reference, a generic cache/lock abstraction, changed source or index behavior,
loss of a public identity or dynamic seam, import-time directory/host I/O, merging
the two lock lifecycles, or cancellation/replacement of a shared Future.

Direct source and tests select one snapshot owner, one index-store owner, and one
declarative policy. E-05a therefore does not trigger additional PRO review.
E-05b preserves that partition and does not trigger a new PRO review.
E-05c preserves that partition and does not trigger a new PRO review.
