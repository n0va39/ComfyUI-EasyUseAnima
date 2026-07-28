# E-08 AiO First-Pass Cache Runtime Ownership Contract

## Scope and authority

E-08a is a production-free Contract created from
`dev@b84fba7ed976e0775f241c5ff4350b47e77ceac9` after the completed E-06
wildcard ownership audit and the already-completed E-07 Comfy provider bridge. It
freezes the AiO first-pass cache process state, policy and behavior authorities,
typed caller boundary, root compatibility identities, cleanup semantics, and the only
authorized bounded Move order. E-08b implements the selected owner from
`dev@2c5aefeae16dd0f1411516f659bfef6659712243` without changing cache
behavior or runtime composition.

The executable source is
`tests/fixtures/python_aio_first_pass_cache_contract.v1.json`, checked by
`tests/test_python_aio_first_pass_cache_contract.py`. Issue #169 and the existing
cache, benchmark, First-pass stage, legacy-generation, package, analyzer, and import-
boundary tests remain the behavior authorities.

E-08 changes ownership only. E-08b changes one production module and does not reopen
#169 cache policy, stage execution, workflow results, or queue/live evidence.

## Completed #169 behavior boundary

Issue #169 completed the AiO stage pipeline and the first-pass cache policy before
E-08:

- immutable cache-owned entries and mutable checkout copies;
- bidirectional mutation isolation with frozen clone-count and logical-copy evidence;
- count, total-byte, and single-entry caps;
- 300-second absolute TTL and LRU refresh/oldest eviction;
- resolved UNET/VAE/CLIP/LoRA path, size, and `mtime_ns` key revisions;
- enable/disable, explicit clear, and mutation-generation stale-put rejection;
- one `RLock` for concurrent mutation and exact hit/miss/skip/eviction metrics;
- bounded 4K batch allocation, latency, RSS, and peak evidence; and
- actual Legacy, Node 2.0, workflow, package, release, and live queue integration.

Those are behavior contracts, not invitations to optimize cloning, alter eviction,
change key schema, add telemetry, or move tensor storage between CPU and GPU.

## One runtime resource boundary

The current canonical module owns six mutable process states:

- `_AIO_FIRST_PASS_CACHE`;
- `_AIO_FIRST_PASS_CACHE_ORDER`;
- `_AIO_FIRST_PASS_CACHE_ENABLED`;
- `_AIO_FIRST_PASS_CACHE_GENERATION`;
- `_AIO_FIRST_PASS_CACHE_METRICS`; and
- `_AIO_FIRST_PASS_CACHE_LOCK`.

They form one AiO-specific resource. Get, put, clear, enable transitions, stale-
capture rejection, LRU publication, eviction, and metrics all share the same lock
and mutation-generation invariant. Splitting metrics, generation, or order from the
entry mapping would create multiple coordination owners for one atomic operation.

The four count/byte/entry/TTL constants are immutable policy. The frozen entry type,
clone and size helpers, resource revision/key materialization, and First-pass stage
are behavior or adapter boundaries rather than additional mutable owners. A generic
cache/lock port is rejected because this cache has AiO-specific tensor cloning,
resource revision, stage fallback, stale-capture, and metric semantics.

## Target owner and compatibility injection

E-08b installs one private
`easyuse_anima.aio.first_pass_cache._AIOFirstPassCacheStore` referenced by
`_DEFAULT_AIO_FIRST_PASS_CACHE`. It owns entries, order, enabled state, generation,
metrics, and the `RLock`.

The canonical module functions remain the compatibility and feature facades. Root
`nodes.py` retains the exact direct canonical identities for:

- `AIO_FIRST_PASS_CACHE_MAX_ENTRIES`;
- `_AIO_FIRST_PASS_CACHE`;
- `_AIO_FIRST_PASS_CACHE_ORDER`;
- `_clone_aio_cache_value`;
- `_aio_first_pass_cache_key`;
- `_get_aio_first_pass_cache`; and
- `_put_aio_first_pass_cache`.

The root does not gain lock, generation, metrics, clear, reset, or runtime-owner
aliases. The module-level mapping and order names are compatibility aliases to the
exact default owner's objects. Canonical facades pass those names into the owner at
call time, preserving replacement mapping/order tests without a second production
owner. Policy, clock, entry capture, size, and clone helpers remain dynamically
resolved. Isolated stores own distinct collections, metrics, generation, enabled
state, and locks.

## Cleanup and concurrency

Current cleanup has three distinct operations:

1. explicit clear advances generation and clears entries/order in place while
   preserving enabled state and metrics;
2. an enabled-state transition advances generation when the state changes, clears
   entries/order when disabled, and preserves metrics; and
3. metrics reset changes only hits/misses/skips/evictions.

Capture and checkout clone remain outside the lock. Clear or disable/re-enable during
capture invalidates stale publication without waiting for capture. Clear does not wait
for checkout cloning. Same-key overwrite is not an eviction, and clear, disable, or
metrics reset does not invent eviction counts.

E-08b preserves these feature cleanup dispositions. E-08c may expose only a narrow
AiO cache capability backed by the exact default owner. Whole-runtime reverse close,
partial-initialization cleanup, and shutdown idempotence remain E-09.

## Caller and import direction

`easyuse_anima.aio.legacy_generation._run_aio_legacy_generation()` normalizes the
request and delegates through `_run_aio_normalized_legacy_generation()` to
`_run_aio_generation_pipeline()`. The pipeline creates the key with the canonical
key helper and injects canonical get/put callables into the existing frozen
`FirstPassRuntime`. `AIOFirstPassStage.run()` uses only those callables. A hit skips
sampling; a miss samples and decodes; resize may re-encode; store remains best
effort; metadata and preview order remain unchanged.

The cache module, First-pass stage, and legacy orchestrator do not import root
`nodes.py`, bootstrap, or `RuntimeServices`. E-08c must preserve that direction:
bootstrap may compose the exact default owner, but feature code does not receive or
import the complete runtime.

## Bounded Move queue

1. **E-08a Contract — complete:** current state, #169 behavior authorities, one
   target owner, caller and root seams, cleanup, and Move order are versioned.
2. **E-08b Move — mutable cache owner — complete:** entries, order, enabled state,
   generation, metrics, and `RLock` are behind one feature-private default owner;
   direct aliases and call-time replacement seams remain executable evidence.
3. **E-08c Move — bootstrap composition:** install the exact default owner behind one
   feature-specific narrow RuntimeServices capability without changing the existing
   `FirstPassRuntime` caller path.
4. **E-08d Contract — completion audit:** reconcile E-01, cleanup, import direction,
   root identities, runtime composition, and zero ambiguous AiO cache state before
   E-09.

Each Move is a separate PR and rollback boundary. Do not combine the owner Move,
runtime composition, completion audit, or E-09 shutdown.

## Preserved behavior

All E-08 Moves preserve:

- cache-key schema, scope, resource revisions, normalized patch plan, NegPip identity,
  prompt/config inputs, and stable serialization;
- immutable entry capture, mutable checkout, recursive cloning, best-effort tensor
  size estimation, and legacy mapping fallback;
- count, byte, single-entry, TTL, LRU, overwrite, falsey-miss, and oldest-eviction
  behavior;
- enabled/disabled fast paths, generation invalidation, clear, metric reset, exact
  metric meanings, and bounded concurrency;
- clone outside the lock, clear during capture/checkout, and exception behavior;
- First-pass cache-hit/miss sampling, resize/re-encode, best-effort store, metadata,
  preview, output, cleanup, and exact trace;
- direct root identities and supported monkeypatch or equivalent isolated-owner seams;
  and
- public node, workflow serialization, API/result, package/no-host, Legacy, and Node
  2.0 behavior.

## Validation and evidence reuse

E-08a focused validation covers the executable Contract, E-01 reconciliation, direct
cache/concurrency/metrics behavior, benchmark and mutation-isolation evidence,
First-pass stage and legacy adapter behavior, package/no-host import, import
boundaries/analyzer, JSON/Python syntax, document links, and `git diff --check`.
E-08b additionally covers isolated-owner separation, exact default mapping/order
identity, raw module-state removal, facade delegation, preserved replacement seams,
and actual-code inventory/analyzer evidence.

Run the official full profile once on the final candidate SHA. E-08b changes only
private in-module ownership and does not change import closure, archive contents,
metadata, or host-visible behavior, so the E-06d validate/pack/isolated-live evidence
remains valid unless a promotion gate proves otherwise.

## Stop conditions

Stop the owning Move if the six raw states do not converge on one owner; get/put,
clear/disable, generation, or metrics require multiple locks or owners; root direct
identities or required patch seams cannot be retained or replaced by an explicit
equivalent isolated-owner seam; clone, size, key, cache, stage, metadata, or queue
behavior changes; canonical feature code must import root/runtime/bootstrap; package
import starts host I/O; or E-09 shutdown must be implemented to finish E-08.

Direct source, #169, E-01, and concurrency tests select one owner and one bounded
Move sequence. E-08a and E-08b therefore do not trigger additional PRO review.
