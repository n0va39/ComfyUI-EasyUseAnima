# AiO first-pass cache immutable entry contract

- Owner issue: [#169](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/169)
- Roadmap unit: A169-CACHE-02
- PR type: Behavior
- Baseline: `dev` commit
  `366c4709edb5da8bcf450891221fbcdd474b29f8`
- State: INVENTORY

A169-CACHE-02 turns each cache value into a structurally frozen, cache-owned
snapshot and defines overwrite as whole-entry replacement. It keeps the
A169-CACHE-01 clone count and bidirectional mutation isolation. It does not
remove cloning or add eviction/resource policy.

## Symbol, caller, alias, and state inventory

### Current entry and operations

- `_AIO_FIRST_PASS_CACHE` is currently typed as
  `dict[str, dict[str, Any]]`.
- Put recursively clones caller-owned latent/image values, stores them in a
  mutable `{"latent": ..., "image": ...}` dictionary, refreshes order, and
  evicts oldest keys beyond the fixed cap.
- Get returns `None` for a missing/falsey patched entry, refreshes order, then
  recursively clones the stored latent/image values.
- Overwriting a key replaces its dictionary but no type expresses that the
  stored values are cache-owned and must not be exposed or mutated in place.

### Callers and compatibility aliases

- `_run_aio_generation_pipeline` injects canonical get/put functions into
  `FirstPassRuntime`.
- `AIOFirstPassStage.run` sees only `(latent, image)` or `None`; it does not
  inspect the entry representation.
- Root `nodes.py` directly aliases the max-entry constant, canonical mapping,
  order list, clone/key/get/put helpers. The mapping and order object identities
  remain unchanged.
- Existing tests replace the canonical mapping/order/cap at call time and rely
  on falsey entries being treated as misses.
- No production caller consumes `entry["latent"]` or `entry["image"]`
  directly.

### Mutable and global state

- The process-global mapping and order list retain their current lifetime.
- Clear mutates both canonical containers in place.
- Stored tensor/container snapshots are mutable objects, but only the cache
  mapping can reach them until get creates an independent checkout copy.
- LRU refresh, fixed two-entry cap, key schema, clone helper, and call-time
  monkeypatch seams remain unchanged.

## Target contract

A private frozen/slots entry value owns two fields: `latent` and `image`.

- Capture clones caller-owned values exactly once per field and stores the
  resulting cache-owned snapshots.
- Checkout clones both stored fields exactly once and returns the existing
  `(latent, image)` tuple.
- Get never exposes either stored field.
- Overwrite constructs a new entry and replaces the mapping value; it never
  mutates an existing entry.
- Frozen means structural field reassignment is rejected. It does not claim
  deep immutability of tensor/container objects.
- A non-empty legacy mapping value remains readable through a narrow fallback
  so call-time test/compatibility replacement does not become a hidden
  migration boundary. New puts always create the canonical frozen entry.

This is the copy-on-write boundary for later policy work: cache-owned snapshots
remain stable, callers mutate only checkout copies, and new results replace
entries wholesale.

## Allowed-file boundary

A169-CACHE-02 may change only:

- `easyuse_anima/aio/first_pass_cache.py`;
- `tests/test_aio_first_pass_cache.py`;
- `tests/test_aio_first_pass_cache_benchmark.py` only if the frozen baseline
  needs an explicit assertion;
- `tests/test_python_backend_analyzer.py`;
- `tests/fixtures/python_backend_baseline.json`, regenerated from source;
- this document;
- `docs/architecture/aio-first-pass-cache-benchmark.md`; and
- `docs/architecture/python-backend-execution-roadmap.md`.

Read-only evidence:

- `easyuse_anima/aio/generation_first_pass.py`;
- `easyuse_anima/aio/legacy_generation.py`;
- root `nodes.py`;
- `tools/benchmark_aio_first_pass_cache.py`;
- `tests/test_aio_legacy_generation.py`;
- `tests/test_aio_nodes.py`; and
- `tests/fixtures/python_compatibility_surface.v1.json`.

Forbidden:

- changing clone helper semantics/order/count or removing put/get cloning;
- changing key, miss, LRU, cap, clear, caller, alias, stage, seed, sampling,
  preview, metadata, Save, workflow, or socket behavior;
- byte budget, single-entry cap, TTL, resource revision, metrics, lock,
  enabled flag, runtime owner, configuration, or concurrency work;
- module Move, root shim change, frontend, release, or Registry work; and
- ComfyUI server, Torch/model workload, browser, or user-instance changes.

## Required validation

Focused validation must prove:

- capture/checkout preserve the A169-CACHE-01 clone count and logical bytes;
- structural field reassignment fails;
- source and returned-hit mutations cannot reach the stored snapshot;
- overwrite replaces entry identity without mutating the previous entry;
- get preserves a canonical entry identity while returning independent copies;
- falsey patched entries remain misses and non-empty legacy mapping entries
  remain readable;
- exact LRU/cap/clear/root alias behavior remains unchanged; and
- analyzer/import-boundary/package contracts remain valid.

One official full validation follows focused success. No server, model,
browser, or user-instance smoke is required.
