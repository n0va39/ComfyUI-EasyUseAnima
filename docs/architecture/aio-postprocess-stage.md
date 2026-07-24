# AiO Postprocess stage connection

- Owner issue: [#169](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/169)
- Roadmap unit: A169-06
- PR type: Behavior
- Baseline: `dev` commit
  `8a2f0439cfa647516fd8bd061fbf109ce0e43537`
- State: INVENTORY

A169-06 connects exactly the existing final Postprocess helper to the stage
Protocol. It does not move or change the helper and does not connect a later
stage.

## Symbol, caller, alias, and state inventory

### Current owner and callers

- `_run_aio_postprocess_stage` remains implemented by
  `easyuse_anima.aio.postprocess`.
- `easyuse_anima.aio.legacy_generation` imports that exact object, and
  `_run_aio_normalized_legacy_generation` is its sole production orchestration
  caller.
- Root `nodes.py` and package entry modes expose the exact canonical helper
  object. Tests and compatibility consumers also call it directly.
- AiO generator tests patch the helper as observed from the legacy module.
  A169-06 preserves this seam by injecting that current imported object through
  `PostprocessRuntime`.

### Current ordered boundary

The helper's exact order is:

1. resolve the final Postprocess enabled flag;
2. when disabled, report the incoming image dimensions and return the image;
3. when enabled, apply the existing final-fit policy;
4. resolve output dimensions using the fit target as fallback;
5. log the existing input/limit/method/applied/output summary; and
6. return image plus enabled, dimensions and fit metadata.

The orchestrator currently publishes `stages.postprocess`, then only for enabled
metadata refreshes dimensions, resolves `fit.applied`, conditionally re-encodes
the image to latent and publishes the `postprocess` preview only when
intermediate previews and configured Postprocess are both enabled.

### Compatibility and cleanup

- `_run_aio_postprocess_stage` implementation, signature, module, root aliases
  and identity do not move or change.
- `PostprocessRuntime` carries the current helper, `_as_bool`, image-size and VAE
  encode helper objects into `AIOPostprocessStage`, preserving patch behavior.
- The helper's resize implementation, geometry policy and logger remain with
  the canonical Postprocess owner.
- The outer orchestrator continues to clean request-level sample/Mod Guidance,
  patched and LoRA models in its existing `finally`.

### Mutable and process state

- `GenerationState` owns the Postprocess image, metadata and, when enabled,
  refreshed dimensions. Its latent changes only when `fit.applied` is true.
- The existing preview callback owns temp file/event publication and appends to
  the same request-local preview list.
- The helper's logger is the only existing module-global collaborator.
- No process-global state, registry, hook, queue or cache is added or changed.

## Behavior boundary

The new `AIOPostprocessStage` structurally implements `GenerationStage`:

- `validate` repeats only the already-enforced `txt2img` mode invariant;
- `run` converts the frozen Postprocess config back to a fresh mutable
  dictionary for the unchanged helper;
- enabled output refreshes dimensions;
- `fit.applied` uses the injected existing boolean normalizer;
- changed output re-encodes latent, then preserves the existing
  intermediate-preview/configured-stage predicate and order;
- disabled or unchanged output preserves latent identity; and
- the helper result and metadata transfer into `GenerationState`.

## Allowed-file boundary

A169-06 may change only:

- `easyuse_anima/aio/generation_postprocess_stage.py`;
- `easyuse_anima/aio/legacy_generation.py`;
- `tests/test_aio_postprocess_stage.py`;
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

- moving or changing `_run_aio_postprocess_stage` or any root alias;
- changing final-fit enable, sizing, alignment, resize, metadata, logging or
  error behavior;
- changing dimension fallback, fit-applied normalization, VAE re-encode or
  preview policy/order;
- connecting or changing cleanup or Save/output stages;
- cache, settings/defaults/migrations, seed, workflow/schema, node adapter,
  frontend, release or Registry changes; and
- compatibility alias retirement.

## Required validation

Focused tests must prove:

- disabled image/latent identity, dimensions and metadata;
- enabled unchanged and enabled applied result/metadata/dimension/latent paths;
- pre-call validation;
- intermediate-preview predicate and post-encode order;
- helper, size, applied-normalization, encode and preview exception boundaries
  plus outer cleanup;
- unchanged exact legacy trace/output cases;
- direct root/canonical helper identity;
- package import and analyzer closure; and
- no later stage connection.

This Behavior PR receives one official full validation after focused tests pass.
The full suite is not repeated after deterministic component failures; failed
stages are resumed directly. Server/model/browser smoke is required only if the
connection exposes an integration risk not covered by the exact trace and full
suite.
