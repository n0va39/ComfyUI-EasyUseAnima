# E-06 Wildcard Snapshot Runtime Ownership Contract

## Scope and authority

E-06a is a production-free Contract created from
`dev@1df6cab58df7abaec9cc86522e89b982b813bd79` after the completed E-05
autocomplete ownership audit. It freezes the verified wildcard snapshot LRU,
building-key single-flight state, Condition, source-state rescan/publication loop,
direct callers, compatibility seams, and the only authorized bounded Move order.

The executable source is
`tests/fixtures/python_wildcard_runtime_contract.v1.json`, checked by
`tests/test_python_wildcard_runtime_contract.py`. Existing wildcard behavior,
package/no-host, import-boundary, analyzer, API, node, workflow, and compatibility
tests remain the behavior authorities.

E-06a changes no production Python, analyzer baseline, public export, import
closure, snapshot/cache policy, source parsing, expansion behavior, or lifecycle.

## D-12 boundary retained

D-12c moved only the immutable `_WildcardSnapshot` value and stateless
`_build_wildcard_snapshot()` materializer to
`easyuse_anima.wildcard.snapshot`. Root `wildcard_engine.py` intentionally retained:

- `_SNAPSHOT_CACHE_LIMIT = 16`;
- `_SNAPSHOT_CONDITION`;
- `_SNAPSHOT_CACHE`;
- `_SNAPSHOT_BUILDING`;
- source scan, build, rescan, retry, and publication;
- list, signature, library, and expansion entrypoints; and
- the root-bound source/build monkeypatch seams.

E-06 does not reopen immutable snapshot fields, source parsing, precedence,
normalization, selector, NumPy/PCG64, seed, mode, expansion, budget, diagnostics, or
payload behavior. The canonical snapshot module remains root-independent.

## One runtime resource boundary

The completed snapshot LRU, building-key set, and Condition are one owner. They
share one source cache-key invariant:

1. scan the ordered roots and source metadata;
2. return and refresh an exact completed-cache hit;
3. admit one builder for a missing key or wait on the same Condition;
4. build an immutable candidate without holding the Condition;
5. rescan the same ordered roots;
6. publish only if the source cache key is unchanged and the candidate is cacheable;
7. always remove the building key and notify all waiters; and
8. propagate a builder exception unchanged or retry after source drift.

Splitting the Condition, completed cache, or building set across owners would make
admission and publication non-atomic. A generic cache/Condition port is rejected;
this state has wildcard-specific rescan, cacheability, and fallback semantics.

`_SNAPSHOT_CACHE_LIMIT` is immutable policy, not a separate lifecycle resource.
Cache hits update recency, cacheable publication keeps the newest 16 keys, and
different keys remain free to build outside the shared Condition.

## Target owner and cleanup

E-06b targets one private
`easyuse_anima.wildcard.snapshot._WildcardSnapshotStore` referenced by
`_DEFAULT_WILDCARD_SNAPSHOTS`. The owner will hold the completed LRU, building-key
set, and Condition. Root lifecycle functions retain call-time source/build
dependencies or an equivalent isolated-owner injection seam until their later
canonical Move.

The target idempotent `clear()` removes completed snapshots only. It must not cancel,
remove, replace, or publish an active building key and must not wake a waiter into a
different settlement contract. Whole-runtime reverse close ordering and partial
initialization cleanup remain E-09.

Bootstrap wildcard-directory initialization, its retry state, default root creation,
and package import effects are separate E-09 resources. E-06 does not absorb them
into the snapshot owner.

## Compatibility and caller inventory

Root `wildcard_engine.py` remains a transitional facade through E-06b. Its public
listing/signature/expansion functions preserve signatures and results. The private
`_WildcardSnapshot` and `_build_wildcard_snapshot` names remain exact canonical
identities. The root-bound `_wildcard_sources` and build names remain call-time test
seams or receive an equivalent owner-injection seam before raw lifecycle globals are
removed.

The current direct snapshot callers are:

- `_load_wildcard_map()` — mutable-copy compatibility helper;
- `list_wildcards()` — sorted relative wildcard names;
- `wildcard_sources_signature()` — public roots/files revision payload;
- `_WildcardLibrary.__init__()` — immutable mapping reuse; and
- `expand_wildcard_texts()` — one snapshot per ordered expansion batch.

`expand_wildcards()` delegates to the ordered-text entrypoint. Empty text batches
still return before snapshot lifecycle. Root API, node adapters, Prompt Studio,
Regional, and workflow consumers retain current list/signature/expansion behavior.

E-06c separately moves the remaining lifecycle/service facade and internal callers to
the canonical wildcard package while retaining the root compatibility identity
surface. E-06d then installs only one feature-specific narrow wildcard snapshot
capability backed by the exact default owner. Feature code does not receive or import
the complete `RuntimeServices` object.

## Bounded Move queue

1. **E-06a Contract — complete:** current state, behavior authorities, one target
   owner, direct callers, compatibility seams, cleanup gap, and Move order are
   versioned.
2. **E-06b Move — snapshot owner:** move the completed LRU, building-key set, and
   Condition behind one feature-private default owner while preserving source
   verification, publication, failure, and call-time seam behavior.
3. **E-06c Move — canonical service and internal callers:** canonicalize the
   lifecycle/service facade, convert internal consumers to that owner, and retain the
   exact root compatibility surface.
4. **E-06d Move — bootstrap composition:** install the exact default owner behind one
   feature-specific narrow wildcard capability without changing initialization or
   directory lifecycle.
5. **E-06e Contract — completion audit:** reconcile E-01, cleanup, import direction,
   root identities, and zero ambiguous wildcard snapshot state before E-07.

Each Move is a separate PR and rollback boundary. The sequence separates state
ownership, canonical caller direction, process composition, and final audit instead
of combining the remaining D-12/E-06 surface into one high-risk Move.

## Preserved behavior

All E-06 Moves preserve:

- ordered root identity and source metadata in the cache key;
- source discovery, extension handling, TXT/YAML parsing, precedence, normalization,
  option ordering, and immutable materialization;
- LRU capacity, hit recency, eviction ordering, one-builder admission, waiter
  wakeup, different-key parallelism, source-change retry, and exception propagation;
- transient and persistent read `OSError` as non-cacheable candidates with no stale
  building key;
- malformed YAML as a cacheable empty parse;
- list/signature payload, immutable library mapping, mutable-copy helper, and
  expansion outputs;
- selector stream, NumPy/PCG64 results, seed/mode semantics, budgets, diagnostics,
  workflow serialization, and node/API behavior; and
- package/no-host import with no import-time directory creation from canonical
  wildcard modules.

Changing cache policy, source behavior, selection, expansion, errors, payloads, or
public signatures is Behavior and remains outside E-06 Moves.

## Validation and evidence reuse

E-06a focused validation covers the executable Contract, E-01 reconciliation,
direct wildcard snapshot/cache/concurrency behavior, package/no-host import, current
import boundaries/analyzer, JSON/Python syntax, document links, and `git diff
--check`.

Run the official full profile once on the final E-06a candidate SHA. Because E-06a
adds only excluded test/docs support files and changes no shipped import, archive,
metadata, or host-visible surface, package/live/validate/pack evidence remains the
unchanged E-05d production evidence unless a material trigger is discovered.

## Stop conditions

Stop the owning Move if the three raw states do not converge on one owner, a target
owner requires canonical-to-root/runtime/bootstrap back-references, source or
expansion behavior changes, a root/public identity or call-time seam disappears
without an equivalent seam, active builders must be cancelled or replaced, package
import starts host/directory I/O, or bootstrap directory lifecycle must move with the
snapshot owner.

Direct source, E-01, D-12c, and concurrency tests select one owner and one Move
order. E-06a therefore does not trigger additional PRO review.
