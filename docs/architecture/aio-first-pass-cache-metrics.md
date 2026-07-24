# AiO first-pass cache process-local metrics

- Owner issue: [#169](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/169)
- Roadmap unit: A169-CACHE-05b
- PR type: Behavior
- Baseline: `dev` commit
  `a34b7c07a07829c9f7bb65c7d0e3a5c4dd0eb46a`
- State: INVENTORY

CACHE-05b adds bounded process-local hit/miss/skip/eviction counters to the
thread-safe first-pass cache. It does not expose metrics through API, settings,
frontend, logs, or workflow data and does not change cache decisions.

## Symbol, caller, alias, and global-state inventory

### Current cache state and operations

- `easyuse_anima.aio.first_pass_cache` owns mapping/order/enabled/generation
  state and one reentrant lock.
- Get linearizes disabled, missing, expired, and hit decisions under the lock,
  then clones a validated entry outside the lock.
- Put performs an initial enabled/generation snapshot, estimates/captures
  outside the lock, and linearizes final skip/store/eviction under the lock.
- Clear and enabled transitions are lock-protected mutation barriers.
- There is no metrics state, snapshot, or reset seam.

### Callers and compatibility aliases

- The typed First-pass stage and benchmark use canonical get/put/clear
  functions without observing counters.
- Root `nodes.py` retains its existing direct mapping/order/key/get/put aliases.
- Metrics state, frozen snapshots, and reset/snapshot helpers are new private
  canonical-owner seams and are not added to root or package exports.
- No caller, function signature, return value, entry, key, or workflow contract
  changes in CACHE-05b.

## Target metrics contract

Provide one frozen snapshot with non-negative integer fields:

- `hits`: an enabled get found a non-expired canonical or readable legacy
  entry and linearized its LRU update. The hit is counted before independent
  checkout cloning.
- `misses`: an enabled get found no entry/falsey legacy entry, or expired a
  canonical entry. Expiration increments both `misses` and `evictions`.
- `skips`: an operation deliberately bypassed cache work or storage:
  - get while disabled;
  - put disabled at its initial check;
  - put rejected by pre-capture or captured single-entry size;
  - put rejected at final commit because disabled/generation changed.
- `evictions`: each entry removed by TTL expiration or count/total-byte budget.
  Same-key overwrite, explicit clear, disable-clear, and metrics reset are not
  evictions.

Additional rules:

- Counter mutation, snapshot, and reset use the existing reentrant lock.
- Snapshot returns a frozen independent value; callers cannot mutate internal
  counters.
- Reset zeros counters only and does not clear, enable/disable, reorder, or
  otherwise mutate cache entries.
- Clear and enable/disable do not reset accumulated metrics.
- Successful put/store has no new counter. Timing, latency, byte-volume,
  histogram, and per-key labels are outside this bounded contract.
- Counter updates must not add tensor cloning, filesystem access, logging,
  background work, or failure paths to normal cache operations.

## Allowed-file boundary

CACHE-05b may change only:

- `easyuse_anima/aio/first_pass_cache.py`;
- `tests/test_aio_first_pass_cache.py`;
- `tests/test_aio_first_pass_cache_benchmark.py` for explicit metrics reset
  isolation only;
- `tests/test_python_backend_analyzer.py` only if analyzer assertions require
  enrollment;
- `tests/fixtures/python_backend_baseline.json`, regenerated from source;
- this document; and
- `docs/architecture/python-backend-execution-roadmap.md`.

Read-only evidence:

- `easyuse_anima/aio/generation_first_pass.py`;
- `easyuse_anima/aio/legacy_generation.py`;
- root `nodes.py`;
- `tools/benchmark_aio_first_pass_cache.py`;
- `tests/test_aio_first_pass_stage.py`;
- `tests/test_python_import_boundaries.py`; and
- `tests/fixtures/python_compatibility_surface.v1.json`.

Forbidden:

- API route, settings, frontend, log/event/telemetry export, persistence, or
  workflow/metadata serialization;
- latency/timing, byte-throughput, per-key/resource labels, histograms, or
  unbounded metric dimensions;
- changing cache key/resource revision, entry layout, TTL, lock/generation,
  count/byte caps, eviction decisions, clone/copy-on-write, or storage;
- changing caller, stage, root aliases, sampling, seed, preview, Save, cleanup,
  server startup, model execution, browser, release, Registry, or
  user-instance work.

## Required validation

Focused validation must prove:

- exact default/reset/snapshot schema and frozen independence;
- hit, missing, disabled, TTL, oversize, stale-generation, and capacity/byte
  counter deltas;
- clear/disable do not count eviction or reset metrics;
- reset does not mutate cache/enabled/LRU state;
- exact aggregate counter totals under bounded concurrent operations;
- existing cache concurrency, lifecycle, key/resource revision, clone/mutation
  benchmark, stage caller, analyzer, and import boundary contracts remain
  valid.

Use existing bounded test runners only. Run one official full validation after
focused checks pass; no server, model, browser, or user-instance smoke is
required.
