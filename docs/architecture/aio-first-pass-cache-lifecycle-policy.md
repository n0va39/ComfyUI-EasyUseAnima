# AiO first-pass cache TTL and enable lifecycle

- Owner issue: [#169](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/169)
- Roadmap unit: A169-CACHE-04a
- PR type: Behavior
- Baseline: `dev` commit
  `fcab2fa92dad164812c2c4961c4f580c77f54acc`
- State: INVENTORY

CACHE-04a adds an explicit process-local enable lifecycle and absolute TTL. It
does not change resource keys; CACHE-04b separately owns resolved resource
revision invalidation.

## Symbol, caller, alias, and state inventory

### Current entry and cache state

- Each frozen entry owns latent/image snapshots and deterministic
  `size_bytes`.
- The canonical mapping and LRU order list have process lifetime.
- Get refreshes LRU order but entries have no timestamps.
- Put enforces single-entry, total-byte, and count limits.
- `_clear_aio_first_pass_cache` clears mapping/order in place.
- There is no enabled flag, setter, clock seam, TTL, or expiration path.

### Callers and compatibility aliases

- The canonical pipeline and First-pass stage use get/put only.
- Root `nodes.py` retains its current direct aliases for count, mapping/order,
  clone/key/get/put. No new root alias is added.
- Existing mapping/order/count/byte-cap monkeypatch seams remain call-time.
- Get stays `(latent, image) | None`; put and clear stay `None`.
- Disabled and expired entries must look like ordinary misses to the stage.

## Target lifecycle contract

- Default enabled: `True`.
- Absolute TTL: `300.0` seconds from `created_at`.
- Clock: private call-time monotonic function seam.
- Canonical entries record `created_at` and `last_access_at`.
- Put reads the clock once for an admitted capture and sets both timestamps.
- Get reads the clock once for a canonical entry:
  - if `now - created_at >= TTL`, remove the key from mapping/order and return
    `None`;
  - otherwise replace the frozen entry with the same snapshot metadata and an
    updated `last_access_at`, refresh LRU order, then return an independent
    checkout copy.
- Legacy mapping fallback remains readable and has no synthetic TTL metadata.
- Disabling clears mapping/order in place. While disabled, get is a miss and
  put skips before size estimation/cloning.
- Re-enabling starts empty and permits normal put/get.
- Explicit clear remains idempotent and does not change enabled state.

Absolute rather than sliding TTL prevents frequently accessed entries from
living forever. `last_access_at` is recorded for later metrics/diagnostics but
does not extend the TTL.

## Decomposition boundary

CACHE-04a owns only time and enable lifecycle. CACHE-04b separately changes the
cache-key resource revision. This avoids mixing resource filesystem semantics
with entry expiration and preserves an independent rollback point.

## Allowed-file boundary

CACHE-04a may change only:

- `easyuse_anima/aio/first_pass_cache.py`;
- `tests/test_aio_first_pass_cache.py`;
- `tests/test_aio_first_pass_cache_benchmark.py` only if lifecycle isolation
  needs an explicit assertion;
- `tests/test_python_backend_analyzer.py`;
- `tests/fixtures/python_backend_baseline.json`, regenerated from source;
- this document;
- `docs/architecture/aio-first-pass-cache-byte-budget.md`; and
- `docs/architecture/python-backend-execution-roadmap.md`.

Read-only evidence:

- `easyuse_anima/aio/generation_first_pass.py`;
- `easyuse_anima/aio/legacy_generation.py`;
- root `nodes.py`;
- `tools/benchmark_aio_first_pass_cache.py`;
- `tests/test_aio_first_pass_stage.py`;
- `tests/test_aio_legacy_generation.py`; and
- `tests/fixtures/python_compatibility_surface.v1.json`.

Forbidden:

- changing resource_info/resource paths, cache key, resource revision, mtime,
  size, registry generation, or resolved resource lookup;
- changing clone, byte estimation, budgets, cap, caller, root alias, stage,
  seed, sampling, preview, metadata, Save, workflow, or socket behavior;
- metrics, lock, concurrency, runtime owner, serialized settings, or frontend;
- module Move, release, Registry, server, Torch/model, browser, or
  user-instance work.

## Required validation

Focused validation must prove:

- exact default enabled/TTL policy and one clock read per canonical put/get;
- hit before TTL, miss/removal at and after TTL, and no sliding extension;
- last-access replacement plus LRU refresh without snapshot mutation;
- disabled get miss and put clone/estimation zero work;
- disable clear, re-enable, explicit clear idempotence, and enabled-state
  preservation;
- legacy mapping fallback remains readable;
- byte/count policy, clone/mutation baseline, root aliases, stage caller,
  analyzer, and import-boundary contracts remain valid.

One official full validation follows focused success. No server, model,
browser, or user-instance smoke is required.
