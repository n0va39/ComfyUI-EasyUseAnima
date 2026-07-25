# AiO first-pass cache resource revision invalidation

- Owner issue: [#169](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/169)
- Roadmap unit: A169-CACHE-04b
- PR type: Behavior
- Baseline: `dev` commit
  `7de7d604a40627abcb3bfcb38bc6918424d7093f`
- State: VALIDATED

CACHE-04b invalidates first-pass cache entries when a resolved UNET, VAE,
text-encoder, or LoRA file changes without changing its logical ComfyUI name.
It does not change resource loading, entry lifecycle, concurrency, metrics, or
storage policy.

## Symbol, caller, alias, and global-state inventory

### Cache key owner and caller

- `easyuse_anima.aio.first_pass_cache._aio_first_pass_cache_key` is the
  canonical key owner. Its version-1 payload already includes logical
  `resource_info`, normalized input settings, prompt data, LoRA names and
  strengths, sampler/model-patch settings, prompts, and dimensions.
- `easyuse_anima.aio.legacy_generation._run_aio_generation_pipeline` is the
  only production caller. It loads the three base resources, applies LoRAs and
  model patches, builds conditioning, and then creates one first-pass key
  before constructing the typed generation request.
- The First-pass stage consumes only the resulting opaque key through the
  existing get/put functions. Its signature and hit/miss contract do not need
  to change.

### Resource identity and host adapter

- `easyuse_anima.nodes.aio_nodes.EasyUseAnimaInput.build` records logical
  `unet_name`, `vae_name`, `clip_name`, loader mode/type, weight dtype, and
  clip device. It does not resolve filesystem paths.
- `easyuse_anima.aio.resources` passes those same logical names to ComfyUI
  loaders. Changing that context or loader contract is outside this task.
- `easyuse_anima.infrastructure.comfy.resources` is the canonical lazy host
  adapter for ComfyUI resource discovery. It imports `folder_paths` only inside
  call-time functions and currently owns no cache or mutable global state.
- Required ComfyUI categories are `diffusion_models`, `vae`,
  `text_encoders`, and `loras`.

### Compatibility aliases and state

- Root `nodes.py` retains the direct `_aio_first_pass_cache_key` alias. The
  function identity, signature, and root binding remain unchanged.
- No new root alias or package export is introduced.
- The new file-revision helper is private to the canonical host adapter and
  owns no cache, registry, generation counter, or mutable global state.
- Existing cache mapping/order/enabled state, TTL, byte budgets, clone
  boundaries, and frozen entry layout remain unchanged.

## Target behavior contract

- Resolve each non-empty logical resource name at key-build time through the
  lazy ComfyUI host adapter.
- A resolved regular resource contributes a deterministic descriptor with:
  - canonical resolved path;
  - non-negative file size; and
  - nanosecond modification time (`mtime_ns`).
- Base roles resolve as UNET → `diffusion_models`, VAE → `vae`, and CLIP →
  `text_encoders`.
- Each normalized LoRA signature contributes a `loras` revision in the same
  order as its existing name/strength signature.
- Empty names, unavailable host modules/helpers, unresolved files, and stat
  failures return no revision and do not raise. The existing logical names and
  settings remain in the key, so hostless/package tests and unsupported
  resources retain deterministic name-based behavior.
- The key schema version advances from 1 to 2 and includes one
  `resource_revision` field. A path, size, or `mtime_ns` change must produce a
  different key; unchanged descriptors must produce the same key.
- Revision data is internal to the opaque stable key. It is not added to
  workflow data, metadata, API responses, logs, or user-visible errors.

## Allowed-file boundary

CACHE-04b may change only:

- `easyuse_anima/infrastructure/comfy/resources.py`;
- `easyuse_anima/aio/first_pass_cache.py`;
- `tests/test_comfy_adapters.py`;
- `tests/test_aio_first_pass_cache.py`;
- `tests/test_python_backend_analyzer.py` only if analyzer assertions require
  enrollment;
- `tests/fixtures/python_backend_baseline.json`, regenerated from source;
- this document; and
- `docs/architecture/python-backend-execution-roadmap.md`.

Read-only evidence:

- `easyuse_anima/nodes/aio_nodes.py`;
- `easyuse_anima/aio/resources.py`;
- `easyuse_anima/aio/model_preparation.py`;
- `easyuse_anima/aio/legacy_generation.py`;
- `easyuse_anima/aio/generation_first_pass.py`;
- root `nodes.py`;
- `tests/test_aio_first_pass_stage.py`;
- `tests/test_aio_legacy_generation.py`;
- `tests/test_python_import_boundaries.py`; and
- `tests/test_python_package_skeleton.py`.

Forbidden:

- changing input-context/resource-info schemas or ComfyUI loader behavior;
- changing the cache-key function signature, caller, root alias, stage
  signature, or workflow/output serialization;
- adding resource registries, persistent caches, watchers, threads, locks,
  metrics, generation counters, or new mutable global state;
- changing TTL/LRU/clear/disable, clone/copy-on-write, byte/count budgets,
  CPU/GPU storage, seeds, sampling, conditioning, preview, Save, or cleanup;
- frontend, release, Registry, server startup, model execution, browser, or
  user-instance work.

## Required validation

Focused validation must prove:

- exact category/name forwarding and resolved path/size/`mtime_ns` descriptor;
- modern/legacy host resolver fallback, empty/missing/unresolved/stat-failure
  no-revision behavior, and no import-time host dependency;
- unchanged resources produce the same version-2 key;
- base resource path/size/`mtime_ns` changes each produce a different key;
- LoRA revision order follows the normalized signature and LoRA file changes
  produce a different key;
- the existing key signature/root alias, cache lifecycle, clone/isolation,
  byte/count policy, stage caller, analyzer, and import boundary stay valid.

Run one official full validation only after focused checks pass. Server startup,
model loading/execution, browser smoke, and user-instance reflection are not
required for this deterministic adapter/key Behavior.

## Validation result

Validated on the CACHE-04b worktree:

- exact category/name forwarding, canonical path/size/`mtime_ns`, legacy
  resolver support, and safe host/helper/path/stat fallbacks: 4 focused Comfy
  resource adapter tests passed;
- version-2 payload, base and ordered LoRA revisions, unchanged-key stability,
  and path/size/`mtime_ns` invalidation: 21 focused cache tests passed;
- unchanged First-pass stage hit/miss consumer: 5 focused tests passed;
- hostless package import: 1 focused test passed;
- targeted Ruff 0.15.22: changed production files passed all rules and changed
  test files passed fatal rules;
- targeted Pyright 1.1.411: changed production files passed with 0 errors;
- Python backend analyzer: 18 focused tests passed;
- Python import-boundary gate: 6 completed package groups, 0 violations; and
- official full: 1,116 Python tests plus 112 frontend JavaScript files passed,
  with the reviewed Pyright baseline unchanged at 88 files and 14 errors.

No resource loader/context schema, caller/root alias, entry lifecycle, cache
budget/clone/storage, concurrency, metrics, server, model, browser, frontend,
workflow, or user-instance behavior was changed.
