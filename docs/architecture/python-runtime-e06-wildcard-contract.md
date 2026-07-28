# E-06 Wildcard Snapshot Runtime Ownership Contract

## Scope and authority

E-06a is a production-free Contract created from
`dev@1df6cab58df7abaec9cc86522e89b982b813bd79` after the completed E-05
autocomplete ownership audit. It freezes the verified wildcard snapshot LRU,
building-key single-flight state, Condition, source-state rescan/publication loop,
direct callers, compatibility seams, and the only authorized bounded Move order.
E-06e completes that sequence with a production-free audit from
`dev@1919f1670a7074a33d1f51612bf70b830f76f57e`.

The executable source is
`tests/fixtures/python_wildcard_runtime_contract.v1.json`, checked by
`tests/test_python_wildcard_runtime_contract.py`. Existing wildcard behavior,
package/no-host, import-boundary, analyzer, API, node, workflow, and compatibility
tests remain the behavior authorities.

E-06a changed no production. E-06b moves only lifecycle ownership between
`wildcard_engine.py` and `easyuse_anima/wildcard/snapshot.py`, with direct tests and
actual-code analyzer/inventory evidence. It changes no public export, cache policy,
source parsing, expansion behavior, bootstrap composition, or directory lifecycle.
E-06c adds the private canonical `easyuse_anima.wildcard.service`, moves the five
snapshot-backed facade callers there, and redirects canonical node, prompt, and seed
consumers away from the root module. Root adapters preserve the existing signatures,
results, and dynamic source/build seams without a canonical-to-root back-reference.

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

E-06b installs one private
`easyuse_anima.wildcard.snapshot._WildcardSnapshotStore` referenced by
`_DEFAULT_WILDCARD_SNAPSHOTS`. The owner holds the completed LRU, building-key set,
Condition, and immutable capacity value. Root `_wildcard_snapshot()` delegates to
that exact identity and supplies the current root-bound source scanner and build
function at call time until their later canonical Move.

The idempotent `clear()` removes completed snapshots only. It does not cancel,
remove, replace, or notify an active building key/waiter. An admitted build therefore
settles and may publish normally after a concurrent clear. Whole-runtime reverse
close ordering and partial initialization cleanup remain E-09.

Bootstrap wildcard-directory initialization, its retry state, default root creation,
and package import effects are separate E-09 resources. E-06 does not absorb them
into the snapshot owner.

## Compatibility and caller inventory

Root `wildcard_engine.py` remains a compatibility facade after E-06c. Its public
listing/signature/expansion functions preserve signatures and results. The private
`_WildcardSnapshot` and `_build_wildcard_snapshot` names remain exact canonical
identities, and its private default-owner dependency is the exact canonical identity.
The root-bound `_wildcard_sources` and build names remain call-time test seams. The
raw root `_SNAPSHOT_CACHE`, `_SNAPSHOT_BUILDING`, and `_SNAPSHOT_CONDITION` globals
are removed rather than retained as duplicate aliases.

The canonical direct snapshot callers are now in
`easyuse_anima.wildcard.service`:

- `_load_wildcard_map()` — mutable-copy compatibility helper;
- `list_wildcards()` — sorted relative wildcard names;
- `wildcard_sources_signature()` — public roots/files revision payload;
- `_WildcardLibrary.__init__()` — immutable mapping reuse; and
- `expand_wildcard_texts()` — one snapshot per ordered expansion batch.

`expand_wildcards()` delegates to the ordered-text entrypoint. Empty text batches
still return before snapshot lifecycle. Root API and `nodes.py` retain their
compatibility/composition imports. Canonical Wildcard, Prompt Studio
Advanced/Regional, and seed-compatibility modules import the canonical mode, seed,
expansion, and service owners directly. Their module-local patch names remain
patchable, and all list/signature/expansion behavior is unchanged.

E-06c completes the remaining lifecycle/service facade and internal caller Move while
retaining the root compatibility surface. E-06d installs the exact
`_DEFAULT_WILDCARD_SNAPSHOTS` identity directly as the private
`RuntimeServices.wildcard_snapshots` capability typed by `WildcardSnapshotPort`.
The port describes only `snapshot_for_roots`; it creates no wrapper or replacement
owner. Feature code does not receive or import the complete `RuntimeServices` object,
and canonical/root callers keep their existing call-time resolver paths.

## Completion audit

E-06e reconciles the E-01 `wildcard-snapshot-cache` entry with exactly one
feature-private owner:
`easyuse_anima.wildcard.snapshot._DEFAULT_WILDCARD_SNAPSHOTS`. No raw root cache,
building set, Condition, wrapper owner, or replacement runtime identity remains.
The owner exposes completed-cache-only idempotent `clear()` while active admission,
waiter settlement, and whole-runtime reverse cleanup remain unchanged; whole-runtime
ordering and wildcard-directory lifecycle stay assigned to E-09.

All canonical wildcard feature modules remain free of root `wildcard_engine`,
`RuntimeServices`, and bootstrap back-references. Package/no-host evidence covers
import-time host and directory I/O. Root private snapshot names remain direct imports
of the canonical identities, and the runtime field is the exact default owner behind
the narrow `WildcardSnapshotPort`. The executable audit therefore records
`ambiguous_state_owners=[]` and changes no production file.

The earlier “before E-07” wording described logical feature order. The E-02a/E-07a/
E-07b Comfy provider bridge was already completed through #323, so the next remaining
owner after E-06 is the separate E-08a AiO first-pass cache ownership Contract. This
queue correction does not reopen or repeat E-07.

## Bounded Move queue

1. **E-06a Contract — complete:** current state, behavior authorities, one target
   owner, direct callers, compatibility seams, cleanup gap, and Move order are
   versioned.
2. **E-06b Move — snapshot owner — complete:** the completed LRU, building-key set,
   and Condition are behind one feature-private default owner; source verification,
   publication, failure, clear, and call-time seam behavior are executable evidence.
3. **E-06c Move — canonical service and internal callers — complete:** canonicalize the
   lifecycle/service facade, convert internal consumers to that owner, and retain the
   exact root compatibility surface.
4. **E-06d Move — bootstrap composition — complete:** install the exact default owner
   behind one feature-specific narrow wildcard capability without changing
   initialization or directory lifecycle.
5. **E-06e Contract — completion audit — complete:** reconcile E-01, cleanup,
   import direction, root identities, and zero ambiguous wildcard snapshot state
   before the next remaining E-08 owner.

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

E-06a focused validation covered the executable Contract, E-01 reconciliation,
direct wildcard snapshot/cache/concurrency behavior, package/no-host import, current
import boundaries/analyzer, JSON/Python syntax, document links, and `git diff
--check`. E-06b additionally covers the isolated owner, active-build clear
settlement, exact root/default identity, raw-state removal, and actual-code analyzer
inventory. E-06c covers canonical/root service parity, root signatures and dynamic
seams, canonical internal import direction, direct node/Prompt Studio/seed behavior,
and shipped archive/no-host closure. E-06d covers the narrow port shape, exact
default-owner identity in the installed runtime, bootstrap reuse, feature import
direction, and unchanged directory initialization order/retry behavior. It adds no
new public surface or cleanup policy. E-06e additionally covers exact E-01 owner
reconciliation, the cleanup disposition, feature import safety, direct root identity
bindings, and zero ambiguous wildcard state. Because E-06e changes no production,
import closure, metadata, or host-visible behavior, E-06d package/live/validate/pack
evidence remains valid.

Run the official full profile once on each final candidate SHA. E-06c adds one shipped
private module and changes canonical import closure without changing dependencies,
public/route/bootstrap/RuntimeServices/metadata surfaces, or host-visible behavior.
It therefore refreshes package/no-host, validate, pack/archive, and isolated test-
instance wildcard smoke evidence before promotion.

## Stop conditions

Stop the owning Move if the three raw states do not converge on one owner, a target
owner requires canonical-to-root/runtime/bootstrap back-references, source or
expansion behavior changes, a root/public identity or call-time seam disappears
without an equivalent seam, active builders must be cancelled or replaced, package
import starts host/directory I/O, or bootstrap directory lifecycle must move with the
snapshot owner.

Direct source, E-01, D-12c, and concurrency tests select one owner and one Move
order. E-06a therefore does not trigger additional PRO review.
