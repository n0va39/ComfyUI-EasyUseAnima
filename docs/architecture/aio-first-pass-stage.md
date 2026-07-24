# AiO first-pass stage move

- Owner issue: [#169](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/169)
- Roadmap unit: A169-02
- PR type: Behavior
- Baseline: `dev` commit
  `7893a8f338731d34f3c04852ae4c6d70fc2abd1e`
- State: VALIDATED

A169-02 connects exactly the mandatory first-pass stage to the A169-01
request/state Protocol. It does not move a later stage or change cache policy.

## Symbol, caller, alias, and state inventory

### Current owner and caller

- `_run_aio_normalized_legacy_generation` is the sole production caller and
  owns the current inline first-pass block.
- `_aio_first_pass_cache_key` computes the current version-1 identity before
  the orchestration `try/finally`.
- The inline block calls `_get_aio_first_pass_cache`; on a miss it calls
  `_generate_empty_latent_with_comfy`, `_sample_latent_with_aio_backend`, and
  `_decode_latent_with_comfy`.
- Every hit or miss is passed through `_resize_image_to_size_if_needed`.
  Resized images are encoded again with `_encode_image_with_comfy_vae`.
- A miss or resize calls `_put_aio_first_pass_cache`; write failures remain
  debug-only and do not fail generation.
- The block publishes `stages.first_pass.cache_hit` and optionally calls the
  existing preview callback before Highres.

### Current ordered boundary

The exact first-pass order frozen by
`tests/fixtures/aio_legacy_execution_trace.v1.json` is:

1. calculate cache identity;
2. enter the existing cleanup `try/finally`;
3. cache lookup;
4. on miss: empty latent, sample, decode;
5. fit decoded/cached image to requested width and height;
6. on resize: encode the fitted image back to latent;
7. on miss or resize: best-effort cache publication;
8. publish first-pass metadata;
9. optionally publish the first-pass preview; and
10. continue to Highres with the resulting image, latent and dimensions.

The cache key remains outside the `try/finally`, matching the current exception
boundary. Stage validation runs inside the existing `try/finally` and before
cache lookup or sampling.

### Compatibility aliases and monkeypatch seams

- Root `nodes.py` aliases for first-pass cache helpers remain direct aliases to
  `easyuse_anima.aio.first_pass_cache`.
- Highres still uses the shared sampling/decode/resize/encode helpers from
  `legacy_generation`; A169-02 does not move or retire those aliases.
- A frozen `FirstPassRuntime` dependency record carries the current
  `legacy_generation` helper objects into the new stage. This preserves the
  existing transition-time patch seam while giving the stage one explicit
  runtime boundary.
- No root alias or public node/workflow name is added.

### Mutable and process state

- `_AIO_FIRST_PASS_CACHE` and `_AIO_FIRST_PASS_CACHE_ORDER` remain owned by
  `first_pass_cache.py`. Entry count, cloning, LRU order, key schema, hit/miss
  semantics and exception policy do not change.
- `GenerationState` owns request-local image, latent, width, height, metadata
  and preview lists after the move.
- Model variants and their cleanup set remain owned by the legacy
  orchestrator until A169-08.
- No new singleton, registry, hook, queue state or process-global mutable value
  is allowed.

## Behavior boundary

The new `AIOFirstPassStage` structurally implements `GenerationStage`:

- `validate` repeats only the already-enforced `txt2img` mode invariant and is
  called before cache lookup/sampling;
- `run` performs the existing first-pass block against one
  `GenerationRequest` and `GenerationState`;
- the caller continues to compute the current cache key and injects the
  current helper identities through `FirstPassRuntime`; and
- cache hits remain the no-sampling path.

First pass is mandatory and has no disabled setting. A169-02 therefore does
not invent a disabled/no-op mode. Its equivalent no-sampling proof is an
existing cache hit with unchanged metadata, preview and output dimensions.

## Allowed-file boundary

A169-02 may change only:

- `easyuse_anima/aio/generation_first_pass.py`;
- `easyuse_anima/aio/legacy_generation.py`;
- `tests/test_aio_first_pass_stage.py`;
- `tests/test_aio_legacy_generation.py`;
- `tests/test_aio_stage_pipeline_contract.py`;
- `tests/test_python_package_skeleton.py`;
- `tests/test_python_backend_analyzer.py`;
- `tests/fixtures/python_backend_baseline.json`, regenerated from source;
- this document;
- `docs/architecture/aio-stage-pipeline-contract.md`; and
- `docs/architecture/python-backend-execution-roadmap.md`.

Read-only golden source:

- `tests/fixtures/aio_legacy_execution_trace.v1.json`.

Forbidden:

- edits to `first_pass_cache.py` or any cache key, clone, capacity, LRU, TTL,
  byte-budget, concurrency or invalidation policy;
- moving or changing Highres, Detailer, Upscale, Postprocess, cleanup or
  Save/output behavior;
- root `nodes.py`, node adapters, settings/defaults/migrations, seed,
  workflow/schema, frontend, release or Registry changes; and
- compatibility alias retirement.

## Required validation

Focused tests must prove:

- miss and hit paths, including no sampling on a hit;
- pre-sampling validation;
- resize/re-encode and best-effort cache-write behavior;
- exception propagation while the existing outer cleanup still runs;
- first-pass metadata, preview order and image/latent/dimension parity;
- the two exact legacy trace/output fixtures remain unchanged;
- the A169-01 zero-caller analyzer allowance returns to zero; and
- package import and analyzer closure stay valid.

This Behavior PR receives one official full validation after focused tests pass.
The full suite is not repeated after deterministic component failures; failed
stages are resumed directly. Model-backed generation and browser smoke are
required only if the move exposes a runtime integration risk not covered by the
existing exact trace and full suite.

Validated on the A169-02 worktree:

- first-pass stage: 5 focused tests passed; the one initial assertion failure
  was a test assumption about the normalized Mod Guidance default and its
  corrected method passed;
- legacy generation: 18 focused tests passed, including both unchanged exact
  trace/output cases and the outer cleanup boundary;
- current normalized settings entered the real typed request boundary before
  resource loading;
- stage pipeline contract: 5 focused tests passed;
- direct package import: 1 focused test passed;
- backend analyzer: 18 focused tests passed with 99 shipped and 99 reachable
  modules and no unreachable module;
- targeted Pyright: 0 errors for both production files;
- Python import-boundary gate: 6 package groups, 0 violations;
- official full: Python 1056 tests passed, Pyright baseline passed, all 112
  JavaScript files passed with TypeScript 6.0.3, and `git diff --check` passed;
  and
- no ComfyUI server, model-backed generation or browser smoke was run because
  the exact runtime trace and full suite exposed no integration risk.
