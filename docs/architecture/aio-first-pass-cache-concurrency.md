# AiO first-pass cache thread-safe mutation

- Owner issue: [#169](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/169)
- Roadmap unit: A169-CACHE-05a
- PR type: Behavior
- Baseline: `dev` commit
  `beade4ff73575c927efd50dc5b125f9de120c392`
- State: VALIDATED

CACHE-05a makes process-local first-pass cache mutation thread-safe without
changing key, entry, budget, TTL, clone, or hit/miss behavior. CACHE-05b
separately owns metrics so lock correctness and observability retain independent
review and rollback boundaries.

## Symbol, caller, alias, and global-state inventory

### Canonical mutable state

- `easyuse_anima.aio.first_pass_cache` owns one process-local mapping, one LRU
  order list, and one enabled flag.
- `_clear_aio_first_pass_cache`, `_set_aio_first_pass_cache_enabled`,
  `_get_aio_first_pass_cache`, and `_put_aio_first_pass_cache` mutate or
  coordinate that shared state.
- `_aio_first_pass_cache_total_bytes` reads the full mapping and is used by put
  while enforcing count and byte budgets.
- No lock currently protects multi-step mapping/order/enabled operations.

### Callers and compatibility aliases

- The typed First-pass stage calls get/put through its existing runtime.
- Root `nodes.py` retains direct aliases for count, mapping/order, clone,
  key/get/put. The clear and enabled setter are canonical test/internal seams
  and are not root aliases.
- Repository benchmark/tests call the canonical owner directly.
- No caller, function signature, root alias, package export, or workflow
  contract changes in CACHE-05a.

### Entry and expensive-work boundary

- Canonical entries are frozen and own independent snapshots. Mapping removal
  or replacement does not mutate an entry already observed by a get.
- Size estimation, capture cloning, and checkout cloning may be expensive.
- Key construction and resource revision stat calls happen before cache get/put
  and do not touch cache mutable state.

## Target concurrency contract

- Add one private module-owned reentrant lock and one private monotonic mutation
  generation. Neither is exported or aliased through root.
- Clear and enable/disable transitions linearize under the lock. Disabling sets
  disabled and clears mapping/order in the same critical section. Explicit
  clear and enabled-state transitions advance the mutation generation.
- Total-byte reads observe one locked mapping snapshot.
- Get linearizes while locked:
  - disabled/missing/expired decisions;
  - expiration removal;
  - canonical last-access replacement; and
  - LRU remove/append.
- Checkout cloning occurs after the lock is released. A hit linearized before a
  later clear/disable may finish its independent checkout; clear/disable does
  not wait for tensor cloning.
- Put performs an initial locked enabled/generation snapshot, then size
  estimation and immutable capture outside the lock. It rechecks both under the
  lock before insertion.
- Clear or disable that completes during an in-flight capture wins: the
  captured value is discarded. A disable/re-enable cycle cannot admit a stale
  capture from the prior enabled generation.
- Insert/overwrite, LRU update, and all count/byte evictions occur in one final
  critical section. Concurrent same-key puts leave at most one key/order entry.
- Existing disabled zero-work behavior remains: a put that observes disabled at
  its initial check performs no estimation, clone, or clock work.

These linearization points avoid holding the shared lock across tensor copies
while preserving deterministic mapping/order/enabled invariants.

## Allowed-file boundary

CACHE-05a may change only:

- `easyuse_anima/aio/first_pass_cache.py`;
- `tests/test_aio_first_pass_cache.py`;
- `tests/test_aio_first_pass_cache_benchmark.py` only if concurrent test
  isolation requires an explicit reset;
- `tests/test_python_backend_analyzer.py` only if analyzer assertions require
  enrollment;
- `tests/fixtures/python_backend_baseline.json`, regenerated from source;
- this document; and
- `docs/architecture/python-backend-execution-roadmap.md`.

Read-only evidence:

- `easyuse_anima/aio/generation_first_pass.py`;
- `easyuse_anima/aio/legacy_generation.py`;
- `easyuse_anima/infrastructure/comfy/resources.py`;
- root `nodes.py`;
- `tools/benchmark_aio_first_pass_cache.py`;
- `tests/test_aio_first_pass_stage.py`;
- `tests/test_aio_first_pass_cache_benchmark.py`;
- `tests/test_python_import_boundaries.py`; and
- `tests/fixtures/python_compatibility_surface.v1.json`.

Forbidden:

- metrics/counters/snapshots/logging or settings/frontend observability;
- changing cache key/resource revision, entry layout, TTL, count/byte caps,
  eviction policy, clone/copy-on-write, CPU/GPU storage, or benchmark budgets;
- changing caller, stage, root aliases, loader/context, workflow/output,
  sampling, seed, preview, Save, or cleanup behavior;
- new worker threads, executors, background tasks, persistent state, server
  startup, model execution, browser, release, Registry, or user-instance work.

## Required validation

Focused validation must prove:

- lock/generation ownership is private and root aliases stay unchanged;
- clear/disable/re-enable and total-byte reads preserve existing results;
- get/put/eviction maintain mapping/order/count/byte invariants under bounded
  concurrent hit/put activity;
- checkout and capture cloning do not hold the shared lock;
- clear or disable/re-enable completed during in-flight capture prevents the
  final stale insert;
- existing TTL/LRU, resource revision, disabled zero-work, clone/mutation
  isolation, benchmark, stage caller, analyzer, and import boundary contracts
  remain valid.

Use bounded events/barriers with explicit timeouts; do not start a server or
long-running worker. Run one official full validation only after focused checks
pass.

## Validation result

Validated on the CACHE-05a worktree:

- private lock/generation ownership, clear and disable/re-enable capture
  barriers, checkout/capture outside-lock behavior, bounded concurrent
  hit/put/eviction invariants, and all existing cache contracts: 25 focused
  cache tests passed in 0.009 seconds;
- existing bounded clone/mutation benchmark: 4 focused tests passed;
- unchanged First-pass stage caller: 5 focused tests passed;
- targeted Ruff 0.15.22: changed production file passed all rules and changed
  test file passed fatal rules;
- targeted Pyright 1.1.411: changed production file passed with 0 errors;
- Python backend analyzer: 18 focused tests passed;
- Python import-boundary gate: 6 completed package groups, 0 violations; and
- official full: 1,120 Python tests plus 112 frontend JavaScript files passed,
  with the reviewed Pyright baseline unchanged at 88 files and 14 errors.

No metrics, key/resource revision, entry/TTL/budget/clone/storage, caller/root
alias, server, model, browser, frontend, workflow, or user-instance behavior
was changed.
