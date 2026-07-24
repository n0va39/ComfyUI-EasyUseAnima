# AiO first-pass cache byte budget and single-entry cap

- Owner issue: [#169](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/169)
- Roadmap unit: A169-CACHE-03
- PR type: Behavior
- Baseline: `dev` commit
  `2b54ee0a803dfdf90a5da0c36147258298659d2f`
- State: INVENTORY

A169-CACHE-03 adds deterministic payload-byte accounting, a total cache
budget, and a single-entry cap. It leaves time, invalidation, metrics,
concurrency, and runtime ownership to later units.

## Symbol, caller, alias, and state inventory

### Current state and policy

- `_AIO_FIRST_PASS_CACHE` maps keys to frozen cache-owned entries or a narrow
  legacy mapping fallback.
- `_AIO_FIRST_PASS_CACHE_ORDER` records oldest-to-newest access order.
- `AIO_FIRST_PASS_CACHE_MAX_ENTRIES` remains `2`.
- Each canonical entry owns latent/image snapshots but has no size metadata.
- Put captures before insertion, refreshes LRU order, then evicts only by entry
  count.
- Get returns an independent checkout copy and refreshes order.
- Clear mutates the canonical mapping/order objects in place.

### Callers and compatibility aliases

- The canonical pipeline and First-pass stage use only get/put return behavior.
- Root `nodes.py` aliases the existing count constant, mapping/order objects,
  clone/key/get/put helpers. Those identities and names remain unchanged.
- Put returns `None`; an oversized skip must retain that return contract.
- Existing call-time replacement of mapping/order/count remains valid.
- No caller currently consumes entry size or total cache bytes.

## Byte-accounting contract

The estimator reports deterministic logical payload bytes, not Python object
overhead or process RSS:

1. count each object identity at most once per estimate;
2. recursively traverse dictionaries, lists, and tuples;
3. count `bytes`, `bytearray`, and `memoryview` length;
4. prefer callable tensor-style `numel() * element_size()`;
5. otherwise accept a non-negative integer `nbytes`;
6. treat unsupported or failing objects as zero bytes.

This intentionally over- or under-approximates some storage-sharing objects;
it is a stable admission/eviction key, not an RSS claim. CACHE-06 owns real
4K/batch peak allocation and RSS evidence.

Each frozen canonical entry records `size_bytes` after capture. Legacy mapping
entries are estimated at read/eviction time.

## Policy decision

- Total logical payload budget: `512 MiB`.
- Single-entry logical payload cap: `256 MiB`.
- Existing maximum entry count: `2`.

The total budget matches two maximum-size entries and the current two-entry
policy. The single cap is intended to admit a typical 4K batch-1 image/latent
payload while preventing one larger batch from monopolizing CPU cache memory.
These are explicit private-policy constants, not serialized user settings.
CACHE-06 may revise them with model-backed 4K/RSS evidence in a separate PR.

Put behavior:

1. capture caller values with the unchanged clone contract;
2. record deterministic entry bytes;
3. if entry bytes exceed the single cap, skip insertion without mutating
   mapping/order or an existing same-key entry;
4. otherwise insert/replace and refresh LRU order; and
5. evict oldest entries until both count and total-byte budgets are satisfied.

Get, key, clone, clear, root aliases, return shape, and stage metadata remain
unchanged.

## Allowed-file boundary

A169-CACHE-03 may change only:

- `easyuse_anima/aio/first_pass_cache.py`;
- `tests/test_aio_first_pass_cache.py`;
- `tools/benchmark_aio_first_pass_cache.py` only to expose deterministic fake
  tensor bytes;
- `tests/test_aio_first_pass_cache_benchmark.py`;
- `tests/test_python_backend_analyzer.py`;
- `tests/fixtures/python_backend_baseline.json`, regenerated from source;
- this document;
- `docs/architecture/aio-first-pass-cache-entry-contract.md`; and
- `docs/architecture/python-backend-execution-roadmap.md`.

Read-only evidence:

- `easyuse_anima/aio/generation_first_pass.py`;
- `easyuse_anima/aio/legacy_generation.py`;
- root `nodes.py`;
- `tests/test_aio_first_pass_stage.py`;
- `tests/test_aio_legacy_generation.py`;
- `tests/test_aio_nodes.py`; and
- `tests/fixtures/python_compatibility_surface.v1.json`.

Forbidden:

- removing or reordering put/get clones;
- changing key, miss, get, clear, caller, alias, stage, seed, sampling,
  preview, metadata, Save, workflow, or socket behavior;
- TTL, clock, explicit enable/disable, resource revision, metrics, lock,
  concurrency, runtime owner, or serialized configuration;
- claiming real GPU/CPU allocation, latency, or RSS from logical bytes;
- module Move, root shim, frontend, release, or Registry work; and
- ComfyUI server, Torch/model workload, browser, or user-instance changes.

## Required validation

Focused validation must prove:

- byte estimation for nested tensor/bytes values, shared identities, failures,
  and unsupported values;
- canonical entry size matches captured payloads;
- entries over 256 MiB are skipped without mutating mapping/order;
- total budget and count cap evict oldest entries independently and together;
- overwrite and legacy mapping fallback participate in byte accounting;
- clone count, logical copied bytes, mutation isolation, get, key, clear, LRU,
  root aliases, stage caller, and return contracts remain unchanged; and
- analyzer/import-boundary/package contracts remain valid.

One official full validation follows focused success. No server, model,
browser, or user-instance smoke is required.
