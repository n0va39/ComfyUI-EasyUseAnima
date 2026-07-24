# AiO final adapter and integration matrix

- Owner issue: [#169](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/169)
- Roadmap unit: A169-09
- PR type: Contract/cleanup
- Baseline: `dev` commit
  `3524b3789baae00d73512fc875a3ecfeb981f63d`
- State: VALIDATED

A169-09 gives the completed stage pipeline one canonical internal entry name,
keeps both legacy adapters intact, and records the integration matrix for the
stage-pipeline series. It does not move the implementation to another module or
change generation behavior.

## Symbol, caller, alias, and state inventory

### Current callers

- `EasyUseAnimaAIOGenerator.generate` is the canonical production node caller.
  It validates input, normalizes settings, opens the backend seed execution
  session, writes the concrete execution seed, calls
  `_run_aio_generation_pipeline`, then publishes the accepted
  execution/next-seed display.
- `_run_aio_legacy_generation` is the root compatibility adapter. It validates
  input, normalizes settings, resolves the legacy runtime seed, and delegates
  to `_run_aio_normalized_legacy_generation`.
- `_run_aio_normalized_legacy_generation` is the exact-signature compatibility
  and direct-test adapter for `_run_aio_generation_pipeline`.
- `_run_aio_generation_pipeline` owns the fully connected
  request/state/six-stage pipeline.
- Root `nodes.py` and package entry modes expose only
  `_run_aio_legacy_generation` plus the existing leaf helpers. The normalized
  entry is not a root compatibility export.

### Final adapter topology

A169-09 provides `_run_aio_generation_pipeline` in the existing
`legacy_generation.py` module:

1. the current normalized implementation body remains in place under the
   canonical name;
2. `EasyUseAnimaAIOGenerator.generate` imports and calls the canonical name;
3. `_run_aio_normalized_legacy_generation` remains an exact-signature adapter
   that delegates to the canonical name;
4. `_run_aio_legacy_generation` keeps its current normalization/seed behavior
   and continues through the normalized compatibility seam; and
5. root/package aliases, leaf helper identities, request/state/stage/lifecycle
   objects, Save output, and seed publication remain unchanged.

This is not a module Move. Canonical module ownership remains
`easyuse_anima.aio.legacy_generation` until its separate #184/D-series owner
changes it.

### Mutable and global state

- The canonical pipeline keeps all current request-local state:
  `GenerationState`, lifecycle owners, stage instances, preview records, run
  ID, metadata, and final output.
- The node adapter keeps the backend seed execution session and accepted seed
  display.
- The legacy adapter keeps its direct runtime-seed resolution.
- First-pass cache, Python random state, helper/module globals, Comfy host
  state, filesystem side effects, and optional dependency lookup do not
  change.
- No new registry, singleton, hook, queue, cache, lock, or background task is
  introduced.

## Read-only integration matrix

| Surface | Canonical evidence | A169-09 gate |
| --- | --- | --- |
| Stage order and result | `aio_legacy_execution_trace.v1.json` | exact two-case trace/output remains byte-unchanged |
| Node adapter and seed | `test_aio_legacy_generation`, `test_aio_seed_cutover` | canonical call plus unchanged seed session/display |
| Six stages and lifecycle | stage/pipeline/lifecycle focused tests | all owners remain connected only inside the canonical pipeline |
| 0.5.2 saved settings | `aio_generation_settings_0_5_2.json` | normalization and typed round-trip remain exact |
| Public node contract | `node_contracts_0_5_2.json` | class mapping, inputs, three outputs, workflow snapshot remain exact |
| Representative workflow | `EasyUse_Anima_AiO_generator_release_ko.json` | JSON, node type, keyed settings, links, metadata, and package list remain valid |
| Package/import safety | package skeleton, analyzer, import-boundary, bootstrap | no new unreachable module, host import, import-time side effect, or baseline drift |
| Frontend Legacy/Node 2.0 | unchanged frontend plus existing 0.5.4 matrix | no repeat browser run for a backend-only adapter rename |
| Model-backed queue | parent #169 final close gate | deferred until the separate A169-CACHE series is integrated; not claimed by this PR |
| Import time/RSS comparison | parent #169 final close gate | deferred until cache policy is integrated so the final measurement is not immediately invalidated |

The two deferred rows are parent-issue completion gates, not evidence claimed
by A169-09. A169-CACHE remains a separate Behavior series and must not be mixed
into this adapter cleanup.

## Allowed-file boundary

A169-09 may change only:

- `easyuse_anima/aio/legacy_generation.py`;
- `easyuse_anima/nodes/aio_nodes.py`;
- `tests/test_aio_legacy_generation.py`;
- `tests/test_aio_seed_cutover.py`;
- `tests/test_aio_stage_pipeline_contract.py`;
- `tests/test_aio_stage_integration_matrix.py`;
- `tests/test_python_backend_analyzer.py`;
- `tests/fixtures/python_backend_baseline.json`, regenerated from source;
- this document;
- `docs/architecture/aio-stage-pipeline-contract.md`; and
- `docs/architecture/python-backend-execution-roadmap.md`.

Read-only evidence:

- `tests/fixtures/aio_legacy_execution_trace.v1.json`;
- `tests/fixtures/aio_generation_settings_0_5_2.json`;
- `tests/fixtures/node_contracts_0_5_2.json`;
- `tests/fixtures/python_compatibility_surface.v1.json`;
- `tests/fixtures/comfy_host_compatibility.v1.json`; and
- `docs/example_workflows/EasyUse_Anima_AiO_generator_release_ko.json`.

Forbidden:

- moving the pipeline body or any helper to another module;
- changing either legacy adapter signature, root/package alias, leaf helper,
  stage, lifecycle owner, request/state/Protocol, or monkeypatch seam;
- changing normalization, migration, seed reservation, runtime seed, stage
  order, validation, cache, sampling, cleanup, preview, Save, metadata, UI, or
  socket behavior;
- modifying any read-only fixture or example workflow;
- A169-CACHE, D-series, settings/defaults/migrations, workflow/schema,
  frontend, release, or Registry changes; and
- starting a server or model-backed generation merely for the adapter rename.

## Required validation

Focused tests must prove:

- the public node imports/calls only `_run_aio_generation_pipeline`;
- both legacy adapters preserve signatures, argument order, normalization/seed
  behavior, and direct compatibility seams;
- the canonical function owns all six stages plus lifecycle owners;
- exact legacy trace/output, 0.5.2 settings round-trip, node contract, and
  representative workflow evidence remain unchanged;
- package/analyzer/import-boundary/bootstrap contracts remain valid; and
- frontend source and read-only compatibility fixtures are untouched.

This Contract/cleanup PR receives one official full validation after focused
tests pass. The full suite is not repeated after deterministic component
failures; failed components are resumed directly. No server/model/browser smoke
is required because the production body and frontend do not change.

## Validation result

Validated on the A169-09 worktree:

- normalized legacy adapter and exact execution trace: 26 focused tests passed;
- backend seed cutover: 1 focused test passed;
- six-stage pipeline contract: 6 focused tests passed;
- integration matrix and read-only JSON evidence: 4 focused tests passed;
- Python backend analyzer: 18 focused tests passed;
- targeted Ruff 0.15.22 and Pyright 1.1.411: 2 production files, 0 errors;
- Python import-boundary gate: 6 completed package groups, 0 violations; and
- official full: 1,096 Python tests plus 112 frontend JavaScript files passed,
  with the reviewed Pyright baseline unchanged at 88 files and 14 errors.

No ComfyUI server, model-backed generation, browser smoke, fixture rewrite, or
frontend runtime change was performed or required.
