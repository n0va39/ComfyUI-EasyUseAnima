# AiO resource, model, and preview lifecycle ownership

- Owner issue: [#169](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/169)
- Roadmap unit: A169-08
- PR type: Behavior
- Baseline: `dev` commit
  `e9544ddf44c76276bfa7b4578cf2376858ca1171`
- State: VALIDATED

A169-08 replaces the legacy orchestrator's request-local model-selection,
deduplicated cleanup, and intermediate-preview closures with explicit lifecycle
owners. It does not move an existing resource, model, preview, stage, or Save
helper and does not change their behavior.

## Symbol, caller, alias, and state inventory

### Resource and model owner

- `_run_aio_normalized_legacy_generation` remains the sole production
  orchestrator and caller of the new lifecycle owners.
- `_load_aio_resources_from_input_context`, `_apply_aio_lora_stack`, and
  `_apply_aio_model_patches` still run before the current stage
  `try/finally`. Resource-preparation failure behavior therefore remains
  unchanged.
- The legacy nested `ensure_standalone_mod_guidance_model` currently lazily
  calls `_apply_spectrum_anima_mod_guidance` at most once.
- The legacy nested `model_and_mod_guidance_flag_for_backend` currently returns
  the patched request model plus the existing Mod Guidance flag only for
  `spectrum_mod_guidance_advanced` before a standalone variant exists. Every
  other backend receives the standalone variant and `False`.
- The first-pass `comfy_ksampler` path additionally calls
  `_apply_aio_spectrum_model_patches_for_comfy_sampler`; later stage requests
  replace only the frozen request's active `resources.model`.
- `ModelVariantResolver` will own only those two nested selection rules and the
  first-pass Comfy patch dispatch. All helper implementations, signatures,
  aliases, exceptions, and model objects remain unchanged and are injected
  from the legacy module.

### Cleanup owner

- The current outer `finally` considers exactly four request-level candidates
  in this order:
  `base_sample_model`, `mod_guidance_model`, `model`, `model_with_lora`.
- It skips `None`, deduplicates by object identity, then calls
  `_cleanup_aio_ephemeral_model(candidate, base_model)`.
- `EphemeralModelRegistry` will retain four named request-local slots in that
  same order and perform the same identity deduplication and cleanup calls.
- Highres, Detailer-target, and USDU helpers continue to own the temporary
  sampler/model variants they create internally. A169-08 does not register or
  clean those models a second time.
- Save/output continues to run only after outer request-level cleanup.
- A failure from a stage, preview helper, or stage validation still enters the
  same outer `finally`. Resource preparation before that boundary remains
  outside it.

### Preview owner

- The legacy orchestrator currently derives `preview_node_id` through
  `_single_value`, builds one random request-local `preview_run_id`, and closes
  over the workflow metadata and `GenerationState.previews`.
- Its `add_preview` closure calls `_save_aio_temp_preview_image`; only a truthy
  image list is appended and then sent through `_send_aio_preview_event`.
- `PreviewCollector` will own that request-local callback and exact
  save/append/send order. Run-ID generation and the intermediate-preview
  enabled predicate remain at the legacy call site.
- Final preview tagging, temporary fallback, Detailer reconciliation, Save UI,
  and metadata remain owned by `AIOSaveOutputStage`.

### Compatibility aliases and mutable/global state

- Existing root/package aliases for resource, model, preview, stage, and Save
  helpers remain direct and unchanged.
- Runtime records carry the exact helper objects observed by
  `legacy_generation`, preserving existing monkeypatch seams.
- The resolver, registry, and collector are created once per generation
  request. Their mutable model slots, identity set, closed flag, and preview
  list reference are request-local.
- The existing first-pass cache and Python `random` process state are not
  changed. No singleton, registry, hook, queue, lock, cache, or background task
  is introduced.

## Behavior boundary

A169-08 adds one strict lifecycle module containing:

- `EphemeralModelRegistry`, with the four named cleanup slots and one
  exception-transparent, identity-deduplicated `close`;
- `ModelVariantResolver`, with the current lazy standalone Mod Guidance,
  backend selection, first-pass Comfy patch, and registry slot updates; and
- `PreviewCollector`, with the current intermediate temp-preview append/event
  order.

The legacy orchestrator still constructs all typed requests and stages in the
same order. It delegates model selection and preview collection to the new
request-local owners, then calls registry cleanup from the existing `finally`.

## Allowed-file boundary

A169-08 may change only:

- `easyuse_anima/aio/generation_lifecycle.py`;
- `easyuse_anima/aio/legacy_generation.py`;
- `tests/test_aio_generation_lifecycle.py`;
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

- moving or changing any existing resource, model-patch, cleanup, preview,
  stage, Save, serializer, or root compatibility helper;
- changing resource-preparation or stage `try/finally` boundaries;
- changing cleanup candidate order, identity deduplication, failure behavior,
  stage-internal temporary-model ownership, or Save-after-cleanup order;
- changing model backend selection, lazy Mod Guidance application, first-pass
  Comfy patching, conditioning, stage request models, or flags;
- changing preview run-ID generation, enabled predicates, temp paths, event
  payload/order, final-preview reconciliation, UI, metadata, or sockets;
- changing `GenerationRequest`, `GenerationState`, or stage Protocol;
- A169-09 adapter simplification, A169-CACHE policy, settings/defaults/
  migrations, seed, workflow/schema, frontend, release, or Registry changes;
  and
- compatibility alias retirement.

## Required validation

Focused tests must prove:

- exact four-slot cleanup order, identity deduplication, `None` handling, and
  request-local/idempotent close;
- lazy standalone Mod Guidance creation and existing backend/flag selection;
- first-pass Comfy patch dispatch and cleanup-slot replacement;
- cleanup after every connected stage and preview failure without changing the
  resource-preparation boundary;
- preview save/append/send order, empty-preview no-op, and exception behavior;
- unchanged exact legacy trace/output cases and final Save-after-cleanup order;
- all six stages remain connected without taking lifecycle ownership;
- package import, analyzer closure, and import boundaries remain valid.

This Behavior PR receives one official full validation after focused tests pass.
The full suite is not repeated after deterministic component failures; failed
components are resumed directly. Server/model/browser smoke is required only if
the connection exposes a host/runtime risk not covered by lifecycle tests, the
exact trace, and the full suite.

## Validation result

- lifecycle owners: 7 focused tests passed;
- legacy generation: 25 focused tests passed, including all six connected
  stages, preview failure cleanup, final Save-after-cleanup, and both unchanged
  exact trace/output cases;
- stage pipeline contract: 6 focused tests passed;
- direct package import: 1 focused test passed;
- backend analyzer: 18 focused tests passed with 105 shipped and 105 reachable
  modules and no unreachable module;
- the analyzer's first focused run failed only because the new Python module
  was not yet in the Git index used by the tracked Registry-surface assertion.
  After staging the allowed files, the exact failed target passed without a
  production change;
- targeted Ruff: clean for both production files;
- targeted Pyright: 2 files, 0 diagnostics;
- Python import boundary: 6 package groups, 0 violations;
- official full: 1091 Python tests passed, the Pyright baseline passed for 88
  files with the reviewed 14-error baseline, all 112 JavaScript files passed
  with TypeScript 6.0.3, and diff checks passed in 43.3 seconds; and
- no ComfyUI server, model-backed generation, or browser smoke was run because
  the request-local connection adds no uncovered host/runtime surface.
