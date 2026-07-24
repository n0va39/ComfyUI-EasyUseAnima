# AiO Highres stage connection

- Owner issue: [#169](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/169)
- Roadmap unit: A169-03
- PR type: Behavior
- Baseline: `dev` commit
  `44e86fb7e318661686e6361ba396bb7f2d9be1e1`
- State: VALIDATED

A169-03 connects exactly the existing Highres helper to the stage Protocol. It
does not move the helper implementation or connect a later stage.

## Symbol, caller, alias, and state inventory

### Current owner and callers

- `_run_aio_highres_stage` remains implemented by
  `easyuse_anima.aio.legacy_generation`.
- `_run_aio_normalized_legacy_generation` is its sole production orchestration
  caller.
- Root `nodes.py` and package entry modes expose the exact canonical helper
  object. Tests and compatibility consumers also call it directly.
- AiO generator tests patch the canonical legacy helper. A169-03 preserves this
  seam by injecting that current object through `HighresRuntime`.

### Current ordered boundary

The helper's exact enabled order is:

1. resolve enabled;
2. derive inherited stage sampler settings;
3. scale the first-pass image and report target dimensions;
4. encode the scaled image to latent;
5. apply a sampler-specific temporary model patch when required;
6. sample inside the helper's `try/finally`;
7. clean the helper-created temporary model;
8. decode, fit to the reported dimensions and conditionally re-encode; and
9. return latent, image, width, height and JSON-safe sampler metadata.

When disabled it returns the incoming latent, image and dimensions with
`{"enabled": false}` immediately after the existing enabled check.

The orchestrator currently resolves the Highres model/Mod Guidance ownership,
calls the helper, publishes `stages.highres`, then publishes a Highres preview
only when Highres sampled, intermediate previews are enabled and Detailer will
run next.

### Compatibility and cleanup

- `_run_aio_highres_stage` implementation, signature, module, root aliases and
  identity do not move or change.
- `HighresRuntime` carries the current helper object into
  `AIOHighresStage`, preserving patch behavior.
- The helper continues to clean only its sampler-specific temporary model.
- The outer orchestrator continues to clean request-level sample/Mod Guidance,
  patched and LoRA models in its existing `finally`.
- Model selection before the call remains with the outer orchestrator until
  A169-08. A stage-specific frozen request replaces only the request's active
  model reference; it does not mutate the shared request or model object.

### Mutable and process state

- `GenerationState` owns Highres latent, image, dimensions and metadata after
  the call.
- The existing preview callback owns temp file/event publication and appends to
  the same request-local preview list.
- No process-global state, registry, hook, queue or cache is added or changed.

## Behavior boundary

The new `AIOHighresStage` structurally implements `GenerationStage`:

- `validate` repeats only the already-enforced `txt2img` mode invariant;
- `run` converts the frozen sampler, Highres and Mod Guidance configs back to
  fresh mutable dictionaries for the unchanged helper;
- `run` transfers the helper result into `GenerationState`;
- disabled Highres remains the existing helper no-op; and
- the current preview predicate and order remain exact.

## Allowed-file boundary

A169-03 may change only:

- `easyuse_anima/aio/generation_highres.py`;
- `easyuse_anima/aio/legacy_generation.py`;
- `tests/test_aio_highres_stage.py`;
- `tests/test_aio_legacy_generation.py`;
- `tests/test_aio_stage_pipeline_contract.py`;
- `tests/test_python_package_skeleton.py`;
- `tests/test_python_backend_analyzer.py`;
- `tests/fixtures/python_backend_baseline.json`, regenerated from source;
- this document;
- `docs/architecture/aio-first-pass-stage.md`; and
- `docs/architecture/python-backend-execution-roadmap.md`.

Read-only golden source:

- `tests/fixtures/aio_legacy_execution_trace.v1.json`.

Forbidden:

- moving or changing `_run_aio_highres_stage` or any root alias;
- changing Highres sampling, scale, scheduler/backend inheritance, temporary
  model cleanup, metadata, dimensions or preview policy;
- connecting or changing Detailer, Upscale, Postprocess, cleanup or
  Save/output stages;
- cache, settings/defaults/migrations, seed, workflow/schema, node adapter,
  frontend, release or Registry changes; and
- compatibility alias retirement.

## Required validation

Focused tests must prove:

- disabled no-op identity and dimensions;
- enabled argument/result transfer and metadata;
- pre-call validation;
- preview predicate and order;
- helper exception propagation plus internal and outer cleanup boundaries;
- unchanged exact legacy trace/output cases;
- direct root/canonical helper identity;
- package import and analyzer closure; and
- no later stage connection.

This Behavior PR receives one official full validation after focused tests pass.
The full suite is not repeated after deterministic component failures; failed
stages are resumed directly. Server/model/browser smoke is required only if the
move exposes an integration risk not covered by the exact trace and full suite.

Validated on the A169-03 worktree:

- Highres stage: 4 focused tests passed;
- legacy generation: 20 focused tests passed, including helper identity,
  enabled/disabled behavior, internal temporary-model cleanup, exact trace and
  outer cleanup;
- stage pipeline contract: 5 focused tests passed;
- direct package import: 1 focused test passed;
- backend analyzer: 18 focused tests passed with 100 shipped and 100 reachable
  modules and no unreachable module;
- targeted Pyright: 0 errors for both production files;
- Python import-boundary gate: 6 package groups, 0 violations;
- official full: Python 1061 tests passed, Pyright baseline passed, all 112
  JavaScript files passed with TypeScript 6.0.3, and `git diff --check` passed;
  and
- no ComfyUI server, model-backed generation or browser smoke was run because
  the exact runtime trace and full suite exposed no integration risk.
