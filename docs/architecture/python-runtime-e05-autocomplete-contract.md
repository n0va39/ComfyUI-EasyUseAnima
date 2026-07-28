# E-05 Autocomplete Runtime Ownership Contract

## Scope and authority

E-05a is a production-free Contract created from
`dev@e8f3b5b3abb7633aa122dc28956c65f664b017c6` after the completed E-04
translation audit. It classifies current autocomplete source metadata, dataset
snapshot and single-flight state, SQLite index publication state, production
callers, compatibility seams, and the only authorized bounded Move order.

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

The current dataset module owns `_CACHE`, `_INFLIGHT`, and `_CACHE_LOCK`.
Snapshots are keyed by the resolved source path plus `mtime_ns`, size, and cache
schema version. One loader publishes a snapshot for a cache key while followers
await the same `Future`. Loader exceptions propagate through that Future, stale
snapshots are not published, and a source that changes during load is retried up to
the existing four-attempt bound.

E-05b moves this state behind one feature-private snapshot owner. The owner provides
an idempotent completed-snapshot clear for isolated tests, but it does not invent a
terminal close policy or cancel, remove, or replace an in-flight Future. Future
settlement and whole-runtime shutdown disposition remain explicit later gates.
Parser calls and current dynamic test seams remain call-time dependencies.
Classification, search fallback, and public status continue to observe the same
snapshot identity and status semantics.

### Index store root and publication locks

The current search module resolves `_AUTOCOMPLETE_INDEX_DIR` once from the process
user-data boundary. When user data and package data resolve to the same standalone
boundary, persistent indexing remains disabled so a package import cannot write to
its source tree.

The current index module owns `_INDEX_LOCKS`, `_INDEX_LOCKS_GUARD`, and the
per-path publication critical section. The lock key deliberately uses
`normcase(abspath(path))` without `Path.resolve()` before the directory exists;
changing that can split first Windows access across two locks for the same eventual
file. One per-path lock protects the second validity check, rebuild, atomic
publication, and concurrent reuse.

E-05c moves the immutable root and retained path-lock registry behind one
feature-private index-store owner. It does not create a generic filesystem lock
service. Read-only hit behavior, source/schema/corrupt invalidation, temporary
SQLite construction, backend selection, atomic replace, diagnostics, and exact
Python snapshot fallback remain unchanged. The proven resource has no disposable
handle, so its feature close shape is an idempotent no-op unless later direct
evidence proves otherwise.

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
- the import-stable index-root patch seam remains available until E-05c replaces it
  with an equivalent isolated owner seam;
- package/no-host imports do not create directories or require ComfyUI host state.

E-05 does not add a public runtime/bootstrap/root export or a generic cache/lock
port.

## Bounded Move queue

1. **E-05a Contract — complete:** current state, two target owners, callers,
   compatibility seams, lifecycle gaps, and Move order are versioned.
2. **E-05b Move — dataset snapshot and single-flight ownership:** encapsulate
   `_CACHE`, `_INFLIGHT`, and `_CACHE_LOCK` behind one feature-private owner while
   preserving parser, source-change, Future settlement, and status behavior.
3. **E-05c Move — index-store root and path-lock ownership:** encapsulate the
   immutable Path-or-None root and normalized-path lock registry behind one
   feature-private index store.
4. **E-05d Move — bootstrap composition and adapter wiring:** compose both owners,
   add only a narrow autocomplete port to RuntimeServices, and preserve every
   canonical/root identity and call-time adapter seam.
5. **E-05e Contract — completion audit:** reconcile E-01 targets, cleanup
   dispositions, import safety, root identities, and zero ambiguous autocomplete
   state before E-06.

Each Move is a separate PR and rollback boundary. E-09 retains whole-runtime reverse
close ordering and partial-initialization cleanup. E-05 supplies only the
feature-owned resources and their proven cleanup shapes.

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
