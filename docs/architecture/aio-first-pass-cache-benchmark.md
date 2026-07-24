# AiO first-pass cache benchmark and mutation-isolation gate

- Owner issue: [#169](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/169)
- Roadmap unit: A169-CACHE-01
- PR type: Contract/docs/gate
- Baseline: `dev` commit
  `f067d12ff9662f9463c6b6c5bd2754805db4042e`
- State: VALIDATED
- Production changes: forbidden

A169-CACHE-01 records the current first-pass cache cost and proves its mutation
isolation before any cache Behavior changes. It adds a deterministic,
timeboxed, fake-tensor harness. It does not optimize cloning or change cache
policy.

## Symbol, caller, alias, and state inventory

### Canonical symbols

`easyuse_anima.aio.first_pass_cache` owns:

- `AIO_FIRST_PASS_CACHE_MAX_ENTRIES`, currently `2`;
- `_AIO_FIRST_PASS_CACHE`, the process-global entry mapping;
- `_AIO_FIRST_PASS_CACHE_ORDER`, the process-global oldest-to-newest key list;
- `_clone_aio_cache_value`, the recursive container/tensor clone helper;
- `_clear_aio_first_pass_cache`;
- `_aio_first_pass_cache_key`;
- `_get_aio_first_pass_cache`; and
- `_put_aio_first_pass_cache`.

The current implementation clones tensor-like leaves on both put and hit:
`detach()`, `clone()`, then best-effort `cpu()`. Dictionaries, lists, and tuples
are recursively rebuilt. Non-container, non-tensor values retain identity.

### Callers and compatibility aliases

- `_run_aio_generation_pipeline` injects canonical get/put functions into
  `FirstPassRuntime`.
- `AIOFirstPassStage.run` gets before sampling, puts after a miss, and puts a
  resized result again when its latent/image shape changes.
- Root `nodes.py` retains direct aliases for the max-entry constant, mapping,
  order list, clone/key/get/put helpers. The private clear helper is not a root
  alias.
- Existing tests patch the canonical mapping, order, max-entry constant, and
  stage runtime callables at call time. A169-CACHE-01 preserves every seam and
  identity.

### Mutable and global state

- Entries and LRU order live for the Python process lifetime.
- Clear mutates the canonical containers in place.
- Put clones caller-owned values before storage.
- Get refreshes LRU order and clones stored values before returning them.
- The current cache has no byte budget, TTL, resource revision, metrics, lock,
  explicit enabled flag, or runtime owner.
- The fixed two-entry cap and list-based LRU behavior are unchanged by this
  unit.

## Harness contract

The harness uses an in-memory fake tensor with `detach`, `clone`, `cpu`, a
mutable byte payload, and deterministic clone counters. It exercises the real
canonical put/get/clear functions without importing Torch or starting ComfyUI.

One run reports:

- schema/version and input payload/iteration counts;
- per-operation detach/clone/cpu counts;
- logical payload bytes copied by tensor clones;
- elapsed nanoseconds and peak traced Python bytes as informational
  measurements; and
- source-after-put and returned-hit mutation-isolation results.

Tests assert schema, deterministic operation/count/byte math, and isolation.
They do not gate on wall-clock duration or `tracemalloc` peak values because
those vary by host and interpreter. The CLI receives bounded positive inputs,
and focused execution remains under the repository's 45-second unittest
watchdog.

## Allowed-file boundary

A169-CACHE-01 may change only:

- `tools/benchmark_aio_first_pass_cache.py`;
- `tests/test_aio_first_pass_cache_benchmark.py`;
- this document; and
- `docs/architecture/python-backend-execution-roadmap.md`.

Read-only evidence:

- `easyuse_anima/aio/first_pass_cache.py`;
- `easyuse_anima/aio/generation_first_pass.py`;
- `easyuse_anima/aio/legacy_generation.py`;
- root `nodes.py`;
- `tests/test_aio_first_pass_cache.py`;
- `tests/test_aio_legacy_generation.py`;
- `tests/test_aio_nodes.py`; and
- `tests/fixtures/python_compatibility_surface.v1.json`.

Forbidden:

- any production Python or frontend change;
- changing clone, key, get, put, clear, LRU, cap, alias, stage, seed, sampling,
  preview, metadata, Save, workflow, or socket behavior;
- adding a cache owner, lock, policy, TTL, budget, metrics, invalidation, or
  configuration;
- committing host-specific latency/peak-allocation thresholds;
- Torch/model-backed allocation, ComfyUI server, browser, release, or Registry
  work; and
- A169-CACHE-02 or later Behavior.

## Required validation

Focused validation must prove:

- current put/get clone counts and logical bytes for bounded fake payloads;
- source mutation after put cannot change the stored entry;
- mutation of one returned hit cannot change the next hit;
- CLI output is deterministic in schema/count fields and valid JSON;
- production/read-only files are untouched; and
- package/analyzer/import-boundary contracts remain unchanged.

One official full validation follows focused success. No server, model,
browser, or user-instance smoke is required.

## Validation result

Validated on the A169-CACHE-01 worktree:

- benchmark/mutation-isolation harness: 3 focused tests passed in 0.082 seconds;
- existing first-pass cache contract: 7 focused tests passed;
- Python backend analyzer: 18 focused tests passed;
- targeted Ruff 0.15.22 and Python compile: passed for the new tool/test;
- Python import-boundary gate: 6 completed package groups, 0 violations;
- default bounded run: 64 KiB per tensor, 25 operations, 50 clones and
  3,276,800 logical copied bytes for both put-overwrite and get-hit, with both
  isolation checks true; and
- official full: 1,099 Python tests plus 112 frontend JavaScript files passed,
  with the reviewed Pyright baseline unchanged at 88 files and 14 errors.

Elapsed and peak traced-byte fields were observed but are intentionally not
committed as pass/fail thresholds. No production/read-only file, ComfyUI
server, Torch/model workload, browser, or user instance was changed or used.
