# AiO Detailer stage connection

- Owner issue: [#169](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/169)
- Roadmap unit: A169-04
- PR type: Behavior
- Baseline: `dev` commit
  `a1e3e109b8707f35e7b3aac6eef53f636f39b45f`
- State: VALIDATED

A169-04 connects exactly the existing Detailer helper to the stage Protocol. It
does not move either Detailer helper implementation or connect a later stage.

## Symbol, caller, alias, and state inventory

### Current owner and callers

- `_run_aio_detailer_stage` and `_run_aio_detailer_target` remain implemented
  by `easyuse_anima.aio.legacy_generation`.
- `_run_aio_normalized_legacy_generation` is the stage helper's sole
  production orchestration caller.
- The stage helper remains the only production caller of the target helper.
- Root `nodes.py` and package entry modes expose the exact canonical helper
  objects. Tests and compatibility consumers also call them directly.
- AiO generator tests patch the canonical legacy helper. A169-04 preserves this
  seam by injecting that current stage helper object through `DetailerRuntime`.

### Current ordered boundary

The stage helper's exact enabled order is:

1. resolve the Detailer enabled flag;
2. derive the configured target order;
3. filter enabled target dictionaries without changing that order;
4. return the existing no-target reason when the filtered list is empty;
5. load one request-local SAM3 context;
6. pass each enabled target's output image into the next target;
7. publish the existing per-target preview immediately after that target;
8. preserve ordered target metadata; and
9. return the final image plus enabled, checkpoint, order and target metadata.

When disabled it returns the incoming image and `{"enabled": false}` without
loading SAM3 or invoking a target.

The orchestrator currently resolves the Detailer model/Mod Guidance ownership,
calls the helper, publishes `stages.detailer`, then refreshes dimensions only
when the returned metadata is enabled.

### Compatibility and cleanup

- `_run_aio_detailer_stage` and `_run_aio_detailer_target` implementations,
  signatures, modules, root aliases and identities do not move or change.
- `DetailerRuntime` carries the current stage helper object and image-size
  helper into `AIODetailerStage`, preserving patch behavior.
- The target helper continues to own detector/detailer cleanup in its existing
  boundaries.
- The outer orchestrator continues to clean request-level sample/Mod Guidance,
  patched and LoRA models in its existing `finally`.
- Model selection before the call remains with the outer orchestrator until
  A169-08. A stage-specific frozen request replaces only the request's active
  model reference; it does not mutate the shared request or model object.

### Mutable and process state

- `GenerationState` owns the Detailer image, dimensions and metadata after the
  call. Its latent remains unchanged.
- The existing preview callback owns temp file/event publication and appends to
  the same request-local preview list.
- The existing SAM3 context is request-local to one stage helper call.
- No process-global state, registry, hook, queue or cache is added or changed.

## Behavior boundary

The new `AIODetailerStage` structurally implements `GenerationStage`:

- `validate` repeats only the already-enforced `txt2img` mode invariant;
- `run` converts the frozen sampler and Detailer configs back to fresh mutable
  dictionaries for the unchanged helper;
- `run` transfers the helper result and metadata into `GenerationState`;
- enabled Detailer refreshes dimensions through the existing image-size helper;
- disabled Detailer preserves image identity and dimensions; and
- the current intermediate-preview predicate and per-target order remain exact.

## Allowed-file boundary

A169-04 may change only:

- `easyuse_anima/aio/generation_detailer_stage.py`;
- `easyuse_anima/aio/legacy_generation.py`;
- `tests/test_aio_detailer_stage.py`;
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

- moving or changing either Detailer helper or any root alias;
- changing target enable/order/filter behavior, SAM3 context loading,
  detector/detailer calls, chaining, preview, metadata or cleanup behavior;
- connecting or changing Upscale, Postprocess, cleanup or Save/output stages;
- cache, settings/defaults/migrations, seed, workflow/schema, node adapter,
  frontend, release or Registry changes; and
- compatibility alias retirement.

## Required validation

Focused tests must prove:

- disabled no-op identity and dimensions;
- enabled argument/result transfer, metadata and dimension refresh;
- pre-call validation;
- intermediate-preview callback injection and existing per-target order;
- helper exception propagation plus target and outer cleanup boundaries;
- unchanged exact legacy trace/output cases;
- direct root/canonical helper identity;
- package import and analyzer closure; and
- no later stage connection.

This Behavior PR receives one official full validation after focused tests pass.
The full suite is not repeated after deterministic component failures; failed
stages are resumed directly. Server/model/browser smoke is required only if the
connection exposes an integration risk not covered by the exact trace and full
suite.

Validated on the A169-04 worktree:

- Detailer stage: 4 focused tests passed;
- legacy generation: 21 focused tests passed, including direct helper identity,
  enabled/disabled target behavior, exact trace and outer cleanup;
- stage pipeline contract: 5 focused tests passed;
- direct package import: 1 focused test passed;
- backend analyzer: 18 focused tests passed with 101 shipped and 101 reachable
  modules and no unreachable module;
- targeted Pyright: 0 errors for both production files;
- targeted Ruff: clean for both production files;
- Python import-boundary gate: 6 package groups, 0 violations;
- official full: Python 1066 tests passed, Pyright baseline passed, all 112
  JavaScript files passed with TypeScript 6.0.3, and `git diff --check` passed;
  and
- no ComfyUI server, model-backed generation or browser smoke was run because
  the exact runtime trace and full suite exposed no integration risk.
