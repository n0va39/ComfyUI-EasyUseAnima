# AiO Save/output stage connection

- Owner issue: [#169](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/169)
- Roadmap unit: A169-07
- PR type: Behavior
- Baseline: `dev` commit
  `78ad02337313f95d5512d3014cabc428fcdce255`
- State: VALIDATED

A169-07 connects the existing inline Save/output boundary to the stage Protocol.
It does not move or change either save backend helper, preview helper, serializer
or outer cleanup ownership.

## Symbol, caller, alias, and state inventory

### Current owner and callers

- `_run_aio_normalized_legacy_generation` currently owns the inline Save/output
  block after its model-cleanup `finally`.
- `_save_image_with_comfy`, `_save_image_with_image_saver` and
  `_aio_save_filename_prefix` remain implemented by
  `easyuse_anima.aio.output`.
- `_tag_aio_preview_images`, `_save_aio_temp_preview_image` and
  `_prompt_data_json_safe` remain with their existing preview/prompt owners.
- Root/package compatibility aliases for all existing helpers remain exact.
- A169-07 preserves the legacy patch seams by injecting the exact helper
  objects observed by the legacy module through `SaveOutputRuntime`.

### Current ordered boundary

The exact Save/output order is:

1. read normalized Save settings after outer model cleanup completes;
2. when enabled, select Image Saver only for the explicit `image_saver`
   backend, otherwise use Comfy SaveImage with the existing filename prefix;
3. accept only a dictionary `ui` result from the selected saver;
4. tag saved images as the final preview;
5. fall back to one temporary final preview when no saved image is available;
6. replace the last Detailer intermediate with the first final preview and
   remove that consumed final entry;
7. build the schema/version/final-size/resource/input/LoRA/settings/stage/prompt
   metadata object through the existing JSON-safe helper;
8. serialize metadata with the existing Unicode/sorted-key policy;
9. build status, dimensions, model, sampler backend and run-ID UI fields;
10. attach final images and the combined intermediate/final preview payload
    only when present; and
11. return UI plus the final image, latent and metadata JSON sockets.

### Compatibility and cleanup

- Both save backend helpers, filename policy, preview helpers, serializer calls,
  signatures, modules, root aliases and identities remain unchanged.
- `SaveOutputRuntime` carries the current helper objects into
  `AIOSaveOutputStage`, preserving patch behavior.
- The stage is created once per request and retains only its just-built final
  output for the caller to return. This avoids changing the A169-01
  `GenerationState` Contract in a Behavior PR.
- The original applied-LoRA list is passed separately so Image Saver metadata
  retains its existing list contract instead of the frozen request tuple.
- The outer orchestrator's model cleanup remains before Save/output. A169-08
  exclusively owns cleanup/resource lifetime changes.

### Mutable and process state

- `GenerationState` continues to own final image, latent, dimensions, stage
  metadata and request-local preview records.
- Final Detailer reconciliation mutates only the existing request-local preview
  list.
- The request-local stage instance stores the final returned payload after a
  successful run; no singleton or process-global output slot is introduced.
- Existing save backends retain their filesystem and optional dependency side
  effects.
- No process-global registry, hook, queue or cache is added or changed.

## Behavior boundary

The new `AIOSaveOutputStage` structurally implements `GenerationStage`:

- `validate` repeats only the already-enforced `txt2img` mode invariant;
- `run` converts the frozen sampler, Save and full generation configs back to
  fresh mutable dictionaries;
- `run` preserves backend selection, keyword arguments and original applied
  LoRA list identity;
- `run` preserves final-preview fallback/reconciliation and state preview
  mutation order;
- `run` builds the same JSON metadata, UI payload and three result sockets; and
- the legacy caller returns the stage's completed request-local output
  immediately.

## Allowed-file boundary

A169-07 may change only:

- `easyuse_anima/aio/generation_save_output_stage.py`;
- `easyuse_anima/aio/legacy_generation.py`;
- `tests/test_aio_save_output_stage.py`;
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

- moving or changing any existing Save/preview/serialization helper or alias;
- changing Save enabled/backend fallback, filename, keyword arguments,
  Image Saver metadata, filesystem behavior or errors;
- changing final-preview tag/fallback/Detailer reconciliation order;
- changing metadata schema/content/serialization, UI keys/shapes or result
  socket order;
- changing `GenerationRequest`, `GenerationState` or stage Protocol;
- changing resource/model cleanup ownership or timing;
- cache, settings/defaults/migrations, seed, workflow/schema, node adapter,
  frontend, release or Registry changes; and
- compatibility alias retirement.

## Required validation

Focused tests must prove:

- disabled Save with temporary final-preview fallback;
- Comfy and Image Saver backend argument/result parity;
- invalid saver UI fallback behavior;
- final preview tagging and Detailer replacement order;
- metadata JSON, UI and socket result parity;
- helper/serialization failure propagation after unchanged outer cleanup;
- unchanged exact legacy trace/output cases;
- package import and analyzer closure; and
- all six stages connected without changing the pipeline Contract.

This Behavior PR receives one official full validation after focused tests pass.
The full suite is not repeated after deterministic component failures; failed
stages are resumed directly. Server/model/browser smoke is required only if the
connection exposes an integration risk not covered by existing Save integration
tests, the exact trace and full suite.

## Validation result

- `tests.test_aio_save_output_stage`: 5 passed;
- `tests.test_aio_legacy_generation`: 24 passed, including the read-only exact
  legacy trace/output fixture and Save failure after outer cleanup;
- `tests.test_aio_stage_pipeline_contract`: 5 passed;
- `tests.test_python_package_skeleton`: 1 passed;
- `tests.test_python_backend_analyzer`: 18 passed with 104 shipped/runtime
  modules;
- targeted Ruff: passed for the new stage and legacy connector;
- targeted Pyright: 2 files, 0 diagnostics;
- Python import boundary: 6 package groups, 0 violations;
- official full validation was started once with the repository/workspace
  runner. It stopped deterministically at the Pyright baseline because the new
  request-local stage output was still typed as optional at the existing node
  caller. A runtime-neutral return cast restored the existing dictionary
  contract; the failed Pyright component then passed for 87 files with the
  reviewed 14-error baseline;
- the remaining official components were resumed without repeating the full
  runner: Python `unittest discover` passed 1082 tests and frontend validation
  passed 112 JavaScript files with TypeScript 6.0.3; and
- diff checks passed. No server, model or browser smoke was run because the
  connection does not add a host/runtime integration surface beyond the
  covered Save helpers and exact legacy trace.
