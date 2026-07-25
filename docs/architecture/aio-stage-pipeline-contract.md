# AiO stage pipeline contract

- Owner issue: [#169](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/169)
- Roadmap unit: A169-01
- PR type: Contract/gate
- State: VALIDATED
- Baseline: `dev` commit
  `89aa20fbde744ce4877f3123eec2061d3193df4d`
- Production stage callers after this unit: zero

This gate freezes the current orchestration order and the request/state/stage
types before any generation behavior is moved. It does not call a stage,
replace legacy orchestration, alter validation timing, or change output.

## Symbol, caller, alias, and global-state inventory

### Current owner and callers

- `EasyUseAnimaAIOGenerator.generate` validates the AiO input, normalizes
  settings, reserves one backend execution seed, then calls
  `_run_aio_normalized_legacy_generation`.
- `_run_aio_legacy_generation` remains the root compatibility entry point. It
  performs input/settings/legacy-seed normalization and delegates to the same
  normalized owner.
- `_run_aio_normalized_legacy_generation` is the sole production orchestrator.
  It prepares resources, prompt data and conditioning; executes first pass,
  Highres, Detailer, Upscale and Postprocess; cleans ephemeral model variants;
  saves the final image; then assembles metadata, previews, UI and three result
  sockets.
- `_run_aio_highres_stage`, `_run_aio_detailer_stage`,
  `_run_aio_upscale_stage`, and `_run_aio_postprocess_stage` are direct
  orchestration callees. First pass and save/output remain inline.

### Current ordered boundary

The stable high-level order is:

1. validate and normalize at the node/compatibility adapter;
2. load base resources, apply LoRA and model patches;
3. normalize prompts and build positive/negative conditioning;
4. resolve stage enablement, sampler backends and lazy Mod Guidance ownership;
5. calculate preview/run and first-pass cache identities;
6. first-pass cache lookup or sample/decode, resize, cache publication and
   optional preview;
7. Highres;
8. Detailer;
9. Upscale and latent refresh;
10. Postprocess and conditional latent refresh;
11. cleanup unique ephemeral model variants in a `finally` block;
12. save/output, final-preview reconciliation, metadata and result assembly.

`tests/fixtures/aio_legacy_execution_trace.v1.json` already freezes two exact
execution traces and output payloads: base txt2img and Upscale with intermediate
previews. A169-01 reuses that fixture rather than introducing a second golden
source.

### Compatibility aliases

- Root `nodes.py` retains direct aliases for the legacy entry point and
  Highres/Detailer/Upscale/Postprocess helpers.
- `easyuse_anima.nodes.aio_nodes` calls the canonical normalized legacy owner
  directly.
- A169-01 adds no root alias and changes no existing alias identity or
  signature. Later stage Behavior units continue to preserve the root
  compatibility registry until its D-series owner retires it.

### Mutable and process state

- `easyuse_anima.aio.first_pass_cache` owns the current process-global cache
  mapping and order list. A169-01 and all stage Moves leave its behavior
  unchanged; the separate A169-CACHE series owns policy changes.
- `legacy_generation` owns request-local `stage_metadata`, preview lists,
  generated run ID, first-pass hit flag, lazy Mod Guidance model and the set
  used to deduplicate cleanup.
- Backend seed reservation is already owned by #167 outside the stage
  orchestrator. A169 does not reinterpret or reserve seeds.
- No stage registry, singleton pipeline, hook, route, queue interceptor or new
  mutable global is allowed in A169-01.

## Frozen zero-caller contract

`easyuse_anima.aio.generation_pipeline` will be a pure, side-effect-free module
containing:

- `AIO_GENERATION_STAGE_ORDER`, fixed to `first_pass`, `highres`, `detailer`,
  `upscale`, `postprocess`, `save_output`;
- frozen `PromptExecutionData`, `ResourceBundle`, `ConditioningBundle` and
  `WorkflowContext` ownership records matching values already assembled by the
  legacy owner;
- frozen `GenerationRequest`, containing the typed `AIOGenerationConfig` plus
  those four records;
- mutable request-local `GenerationState`, containing image, latent, width,
  height, stage metadata and preview records; and
- `GenerationStage`, a structural `validate(request, capabilities)` /
  `run(request, state)` Protocol.

The outer request records are frozen. This does not claim that Comfy
MODEL/CLIP/VAE/tensor objects or nested mappings are deeply immutable. Mutation
and cleanup ownership remains with the current legacy function until the
corresponding Behavior unit migrates it.

A169-08 keeps those model objects and all existing helper implementations
unchanged while connecting request-local `ModelVariantResolver`,
`EphemeralModelRegistry`, and `PreviewCollector` owners. The legacy orchestrator
remains the sole production caller, stage-internal temporary models remain with
their existing helpers, and Save/output remains after request-level cleanup.

A169-01 introduced these contracts with no production caller and temporarily
allowed exactly this one shipped module outside the runtime import closure.
A169-02 connects the First pass stage through the contract and removes that
allowance: all shipped Python modules are again reachable from the runtime
entry surface. Later stages remain on the legacy owner.

## Allowed-file boundary

A169-01 may change only:

- `easyuse_anima/aio/generation_pipeline.py`;
- `tests/test_aio_stage_pipeline_contract.py`;
- `tests/test_python_package_skeleton.py`;
- `tests/test_python_backend_analyzer.py` only when analyzer enrollment needs
  an explicit assertion;
- `tests/fixtures/python_backend_baseline.json`, regenerated only from the
  implemented source;
- this document; and
- `docs/architecture/python-backend-execution-roadmap.md`.

The existing legacy trace fixture is read-only in this unit.

Forbidden:

- edits to `legacy_generation.py`, `aio_nodes.py`, root `nodes.py`, settings,
  defaults, migration, cache, preview, save, stage helpers or frontend code;
- any production caller, orchestrator, stage instance, registry or mutable
  global;
- changing stage order, validation timing, sampling, cache, cleanup, metadata,
  preview, UI, socket, workflow or seed behavior; and
- A169-02 or later stage Behavior, A169-CACHE, D-series, release or Registry
  work.

## Validation and rollback

Focused validation must prove:

- the exact stage order and dataclass/Protocol surface;
- frozen request records and isolated mutable state containers;
- no production caller or root alias;
- both existing trace cases contain the ordered stage/cleanup/save checkpoints;
- direct package import remains side-effect-free and avoids Comfy/Torch; and
- analyzer/import closure matches the source.

This zero-caller Contract does not require a model-backed generation or browser
smoke. Reverting the unit removes only unused types, their tests and this
record; runtime behavior and serialized contracts remain byte-for-byte owned by
the existing implementation.

Validated on the A169-01 worktree:

- stage contract: 5 focused tests passed;
- direct package import: 1 focused test passed;
- analyzer fixture and tracked Registry surface: focused assertions passed;
- Pyright 1.1.411: 0 errors for `generation_pipeline.py`;
- Ruff 0.15.22 import ordering: passed for `generation_pipeline.py`;
- Python import-boundary gate: 6 package groups, 0 violations; and
- no ComfyUI server, model generation or browser smoke was run or required.

## Final connected state after A169-09

A169-02 through A169-08 connected the six stages and request-local lifecycle
owners without changing their order or behavior. A169-09 names that existing
owner `_run_aio_generation_pipeline`:

- `EasyUseAnimaAIOGenerator.generate` calls the canonical pipeline directly
  after input normalization and backend seed reservation;
- `_run_aio_normalized_legacy_generation` remains an exact-signature adapter
  and test seam;
- `_run_aio_legacy_generation` remains the root compatibility adapter and
  preserves its normalization and runtime-seed behavior;
- root/package aliases and leaf helper identities remain unchanged; and
- the canonical pipeline retains all six stages plus
  `EphemeralModelRegistry`, `ModelVariantResolver`, and `PreviewCollector`.

The final adapter is a Contract/cleanup boundary, not a module Move. Cache
policy remains owned by the separate A169-CACHE Behavior series, and canonical
module consolidation remains owned by the D-series.
