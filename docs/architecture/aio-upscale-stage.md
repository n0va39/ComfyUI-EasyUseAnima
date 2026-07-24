# AiO Upscale stage connection

- Owner issue: [#169](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/169)
- Roadmap unit: A169-05
- PR type: Behavior
- Baseline: `dev` commit
  `6fb03b677551c9b4112d5302020a09bd129a5b82`
- State: VALIDATED

A169-05 connects exactly the existing final Upscale dispatcher to the stage
Protocol. It does not move or change the dispatcher or either backend helper,
and it does not connect a later stage.

## Symbol, caller, alias, and state inventory

### Current owner and callers

- `_run_aio_upscale_stage`, `_run_aio_usdu_upscale_stage` and
  `_run_aio_resshift_upscale_stage` remain implemented by
  `easyuse_anima.aio.legacy_generation`.
- `_run_aio_normalized_legacy_generation` is the dispatcher helper's sole
  production orchestration caller.
- The dispatcher remains the production owner of lazy USDU/ResShift backend
  selection and calls the corresponding existing leaf helper.
- Root `nodes.py` and package entry modes expose the exact canonical helper
  objects. Tests and compatibility consumers also call them directly.
- AiO generator tests patch the canonical dispatcher. A169-05 preserves this
  seam by injecting that current object through `UpscaleRuntime`.

### Current ordered boundary

The dispatcher helper's exact order is:

1. resolve the final Upscale enabled flag;
2. return the incoming image and `{"enabled": false}` when disabled;
3. normalize an empty backend to `usdu`;
4. lazily invoke the existing USDU or ResShift helper;
5. raise the existing unsupported-backend error before invoking a leaf; and
6. return the leaf image and metadata unchanged.

The orchestrator currently resolves the Upscale model/Mod Guidance ownership,
passes quality/prompt exclusion inputs to the dispatcher, publishes
`stages.upscale`, then only for enabled output refreshes dimensions, re-encodes
the image to latent and conditionally publishes the `upscale` preview.

### Compatibility and cleanup

- All three Upscale helper implementations, signatures, modules, root aliases
  and identities do not move or change.
- `UpscaleRuntime` carries the current dispatcher, image-size and VAE encode
  helper objects into `AIOUpscaleStage`, preserving patch behavior.
- The USDU helper continues to own its sampler-specific temporary-model
  cleanup. ResShift dependency/model loading remains inside its existing leaf.
- The outer orchestrator continues to clean request-level sample/Mod Guidance,
  patched and LoRA models in its existing `finally`.
- Model selection before the call remains with the outer orchestrator until
  A169-08. A stage-specific frozen request replaces only the request's active
  model reference; it does not mutate the shared request or model object.

### Mutable and process state

- `GenerationState` owns the Upscale image, metadata and, when enabled,
  refreshed dimensions and re-encoded latent after the call.
- The existing preview callback owns temp file/event publication and appends to
  the same request-local preview list.
- Optional custom-node lookup, model loading and any dependency caches remain
  behind the existing leaf helpers.
- No process-global state, registry, hook, queue or cache is added or changed.

## Behavior boundary

The new `AIOUpscaleStage` structurally implements `GenerationStage`:

- `validate` repeats only the already-enforced `txt2img` mode invariant;
- `run` converts the frozen sampler and Upscale configs back to fresh mutable
  dictionaries for the unchanged dispatcher;
- `run` passes the existing prompt/quality inputs and exclusion flags unchanged;
- enabled output refreshes dimensions, re-encodes latent, then preserves the
  existing intermediate-preview predicate and order;
- disabled output preserves image/latent identity and dimensions; and
- the helper result and metadata transfer into `GenerationState`.

## Allowed-file boundary

A169-05 may change only:

- `easyuse_anima/aio/generation_upscale_stage.py`;
- `easyuse_anima/aio/legacy_generation.py`;
- `tests/test_aio_upscale_stage.py`;
- `tests/test_aio_legacy_generation.py`;
- `tests/test_aio_stage_pipeline_contract.py`;
- `tests/test_python_package_skeleton.py`;
- `tests/test_python_backend_analyzer.py`;
- `tests/fixtures/python_backend_baseline.json`, regenerated from source;
- this document; and
- `docs/architecture/python-backend-execution-roadmap.md`.

Read-only golden source:

- `tests/fixtures/aio_legacy_execution_trace.v1.json`.

Forbidden:

- moving or changing any Upscale helper or root alias;
- changing enabled/backend dispatch, USDU/ResShift dependency lookup, sampling,
  tiling, prompt conditioning, model loading, errors, metadata or cleanup;
- changing dimension fallback, VAE re-encode or preview policy/order;
- connecting or changing Postprocess, cleanup or Save/output stages;
- cache, settings/defaults/migrations, seed, workflow/schema, node adapter,
  frontend, release or Registry changes; and
- compatibility alias retirement.

## Required validation

Focused tests must prove:

- disabled no-op image/latent identity and dimensions;
- enabled argument/result transfer, metadata, dimensions and latent re-encode;
- pre-call validation;
- intermediate-preview predicate and post-encode order;
- dispatcher, size, encode and preview exception boundaries plus USDU and outer
  cleanup;
- unchanged exact legacy trace/output cases;
- direct root/canonical helper identity;
- package import and analyzer closure; and
- no later stage connection.

This Behavior PR receives one official full validation after focused tests pass.
The full suite is not repeated after deterministic component failures; failed
stages are resumed directly. Server/model/browser smoke is required only if the
connection exposes an integration risk not covered by the exact trace and full
suite.

Validated on the A169-05 worktree:

- Upscale stage: 4 focused tests passed;
- legacy generation: 22 focused tests passed, including direct helper identity,
  backend dispatch, USDU cleanup, exact trace and outer cleanup;
- stage pipeline contract: 5 focused tests passed;
- direct package import: 1 focused test passed;
- backend analyzer: 18 focused tests passed with 102 shipped and 102 reachable
  modules and no unreachable module;
- targeted Pyright: 0 errors for both production files;
- targeted Ruff: clean for both production files;
- Python import-boundary gate: 6 package groups, 0 violations;
- official full: Python 1071 tests passed, Pyright baseline passed, all 112
  JavaScript files passed with TypeScript 6.0.3, and `git diff --check` passed;
  and
- no ComfyUI server, model-backed generation or browser smoke was run because
  the exact runtime trace and full suite exposed no integration risk.
