# Python Compatibility Shim Registry

## Registry status

- Inventory baseline: `dev` commit
  `14015769634d387fe5afa6a74a5594007e86346c`
- Compatibility provenance: package/workflow version 0.5.2
- Policy: [ADR-002](adr-002-compatibility-shims.md)
- Machine-readable audit:
  [`python_compatibility_surface.v1.json`](../../tests/fixtures/python_compatibility_surface.v1.json)
- Current state: B-11a through B-11c30e / PR #355 are integrated in the
  reviewed sequence, and B-11d / PR #356 implements the final explicit root
  shim with package/pack/live gates pending. S167-01a / PR #344 supplies the
  canonical reserved-seed compatibility consumer while retaining its root
  aliases. No runtime binder, resolver, or residual root implementation
  remains.

This is an actionable registry, not a removal schedule. `N` means the first
published Registry release containing both a canonical target and its root
shim. `N+1 gate` means no earlier than a later release and only after every
removal gate passes; it does not promise removal in that release.

## Required fields

Every shim entry records:

- **Surface/symbols:** the supported root import path and exact public scope.
- **Classification:** permanent entrypoint, supported public re-export,
  transitional private seam, or unsupported/test-only.
- **Current/canonical target:** the current binding owner, canonical owner when
  assigned, and whether that target is canonical, legacy-owned, or unassigned.
- **Identity requirement:** stable entrypoint object, direct alias identity, or
  not applicable for root-owned residual implementation and
  unsupported/test-only bindings that carry no compatibility guarantee.
- **Binding shape/import target:** entrypoint, direct import, or root definition,
  plus the exact imported module for every direct binding in both import modes.
- **Owner:** the issue responsible for the canonical move and future decisions.
- **Canonical target:** the only implementation path after conversion.
- **Introduced/conversion:** when the current surface existed and the PR phase
  that converts it to a shim.
- **Known dependents:** current repository/runtime consumers and any confirmed
  external consumer.
- **Evidence:** static imports, fixtures, docs, issues, package smoke, or other
  privacy-safe consumer evidence.
- **Minimum support:** at least all of release `N` after canonical introduction.
- **Removal gate:** specific checks in addition to ADR-002.
- **Earliest release:** a gate expression, never an unsupported date promise.
- **State:** implementation, planned shim, supported shim, deprecated, retained,
  or removal-approved.

The B-10a fixture freezes symbol scope until B-11 can add the final explicit
root `__all__`. New private helpers are not added to a shim merely because tests
import them.

## Current inventory summary

| Surface | Current role | Canonical target | Owner | Introduced / conversion | Known dependents and evidence | Earliest removal |
| --- | --- | --- | --- | --- | --- | --- |
| Root `__init__.py` exports | Permanent ComfyUI entrypoint, not a shim | root entrypoint plus `easyuse_anima.registration`/`bootstrap` | #184/#185 | Existing 0.5.2 surface; B-11 rewires internals | ComfyUI loader; node contract fixture | Not removable as a package entrypoint |
| `nodes.py` mapped public classes | 18 direct compatibility re-exports plus audited private/residual debt | `easyuse_anima.nodes.*_nodes` | #184 B-04 through B-11, #188 | Existing 0.5.2 surface; B-04 through B-09b2 canonicalized all mapped adapters; B-11 completes the shim | Root mappings and workflows; repository tests are not public-support evidence; no confirmed external direct importer | No scheduled removal; public breaking-change gate after N+1 at earliest |
| `api.py` route-registration surface | Partial route adapter after D-03a/D-03b/D-04a/D-05 plus explicit D-10 profile aliases; planned API shim | `easyuse_anima.profiles.*`, `easyuse_anima.api.routes.translation`, `.aio_torch_compile`, `.autocomplete`, then remaining routes/router | #162, #163, #165, #186 D-10/D-02-D-07 | Existing 0.5.2 route surface; D-03 canonicalizes translation handler/executor, D-04a the read-only AiO Torch Compile handler, and D-05 the autocomplete status/search/classification adapters while root retains lifecycle/correlation/registration composition | Root entrypoint side-effect import, frontend endpoints, profile/API tests | Unscheduled; remaining route ownership, N+1 gate, and route parity |
| `api_contract.py` request/error helpers | Explicit 12-symbol request/error/response identity shim (D-02); D-14 freeze decision pending | `easyuse_anima.api.requests`, `.responses`, and `.errors` | #165, #186 D-02/D-14 | #165 contract canonicalized in D-02; exact root surface and flat/package identity fixture | External/legacy imports and compatibility tests; production `api.py` uses canonical owners | Unscheduled; first canonical+shim release N not yet recorded, then D-14/N+1 gate and request/error/frontend parity |
| `settings.py` | Explicit direct re-export shim (D-09) | `easyuse_anima.settings.schema`, `.repository`, and `.service` | #163, #186 D-09 | Existing 0.5.2 module-owned public surface; exact `__all__` and identity fixture | External/legacy imports and settings compatibility tests; production callers use canonical modules | Unscheduled; first canonical+shim release N not yet recorded, then N+1 gate and settings migration/round-trip |
| `storage.py` | Explicit direct re-export shim (D-08) | `easyuse_anima.infrastructure.filesystem.atomic_json` and `.paths` | #163, #186 D-08 | Existing 0.5.2 supported module-owned public surface; exact `__all__` and identity fixture | External/legacy imports and storage compatibility tests; production callers use canonical modules | Unscheduled; first canonical+shim release N not yet recorded, then N+1 gate and last-known-good/atomic-write parity |
| `autocomplete_index.py` | Explicit direct re-export shim (D-11a) | `easyuse_anima.autocomplete.index` | #162, #186 D-11a | Existing indexed-search surface; exact seven-name `__all__` and identity fixture | External/legacy imports; `autocomplete_dataset.py` now uses the canonical owner | Unscheduled; first canonical+shim release N not yet recorded, then N+1 gate and index/ranking/rebuild parity |
| `autocomplete_dataset.py` | Explicit 15-symbol dataset/search/classification identity shim (D-11) | `easyuse_anima.autocomplete.dataset`, `.search`, and `.classification` | #162, #186 D-11 | Existing 0.5.2 dataset/search surface canonicalized in PR #386; final classification Move completed after D-13 removed its root dependency | External/legacy imports and direct compatibility tests; production API uses canonical owners | Unscheduled; first complete canonical+shim release N not yet recorded, then N+1 gate and classification/result/API parity |
| `wildcard_engine.py` | Partial compatibility module after D-12f2; snapshot lifecycle/expansion remain root-owned | `easyuse_anima.wildcard.models`, `.sources`, `.snapshot`, `.seed`, `.mode`, `.selector`, then lifecycle/expansion modules | #184, #186 D-12 | Existing 0.5.2 models in PR #387, sources in #388, snapshot materialization in #389, seed control in #390, mode contract in #391, selector import contract in #392, and selector Move in #393 with direct aliases | root entrypoint, `nodes.py`, `api.py`, wildcard/workflow tests | Unscheduled; full D-12 move, final identity surface, N+1 gate, and seed/expansion/workflow parity |
| `prompt_translation.py` | Explicit direct re-export shim (D-01) | `easyuse_anima.translation.*` | #164, #186 D-01 | Existing 0.5.2 supported module-owned public surface; exact `__all__` and identity fixture | External/legacy imports and translation compatibility tests; production callers use canonical modules | Unscheduled; first canonical+shim release N not yet recorded, then N+1 gate and provider-off/API parity |
| `anima_prompt/` package | Explicit package and submodule identity shims (D-13); D-14 freeze decision pending | `easyuse_anima.prompt.anima.*` | #184, #186 D-13/D-14 | Existing 0.5.2 surface canonicalized in D-13 with explicit public `__all__`, flat/package import parity, and packed closure | External/legacy imports and direct compatibility tests; production callers use the canonical package | Unscheduled; first canonical+shim release N not yet recorded, then D-14/N+1 gate and prompt correction/parser parity |

## Entry details

### B-10a machine-readable root audit

The versioned fixture records the exact post-B-09b2 surface rather than
inferring public support from spelling or test imports:

- root `__init__.py` permanent entrypoints: 3;
- `nodes.py` preamble implementation imports: 1 (`logging`), excluded from
  compatibility classification
  by an exact AST allowlist and drift gate;
- `nodes.py` bindings with an `easyuse_anima` canonical target: 289 in
  B-11c30e (258 at the integrated B-10b20 baseline), with exact
  relative-package/flat-fallback parity;
- bindings still owned by `anima_prompt`, `settings`, `prompt_translation`, or
  `wildcard_engine`: 27, with the same fallback parity;
- mapped supported public class re-exports: 18;
- unmapped root classes: `EasyUseAnimaSAM3Context` and
  `EasyUseAnimaSAM3Detailer`; the canonical legacy Extend class remains in its
  owner module without a root alias or backend mapping;
- root-owned residual implementation: 0 functions, 0 classes, and 2 assigned
  globals in B-11c30e (41/2/33 at the integrated B-10b20 baseline).
- import-time runtime binders: 0;
- no string runtime resolver or explicit callback installation remains;
- retired private bindings: `_comfy_checkpoint_names`,
  `_EasyUseAnimaAlignedDetailerHook`, and
  `_EasyUseAnimaImpactDetailerDelegate`, plus `_impact_core_module`,
  `_align_up`, `_aligned_size_near_scale`, `_alignment_value`,
  `_image_scale_by_multiple_size`, `_max_long_edge_value`,
  `_normalize_image_scale_options`, `_scale_by_value`, and
  `_clear_aio_first_pass_cache`, plus `WILDCARD_SEED_RANGE_NOTE`, the seven
  B-10b9 SAM3 helpers, the two B-10b10 prompt-default constants, and the
  B-10b11 legacy Extend class root alias, the nine B-10b12 prompt-data aliases,
  the 13 B-10b13 NAIA client aliases, the 16 B-10b14 NAIA resolution aliases,
  the five B-10b15 conditioning aliases, the 12 B-10b16 Prompt Advanced aliases,
  the 12 B-10b17 Regional aliases, the 11 B-10b18 Artist Mix parsing/config
  aliases, the 21 B-10b19 Artist Mix mode/key/tag-position aliases, and the 21
  B-10b20 Artist Mix conditioning/tensor aliases, plus the B-11c29a-d and
  B-11c29b3
  `_comfy_max_resolution`, direct mapping, loaded lookup, and two requirement
  root helpers, the CLIP invocation helper, and general node lookup; their production
  consumers import or call the corresponding canonical owners directly;
- repository test files with a direct `nodes` import: 21, recorded as migration
  consumers rather than public-support evidence.

Each target-module/classification group records its current and canonical
target, identity requirement, owner, unpublished `first_release: null`, known
consumers, evidence, removal gates, and lifecycle state. An AST gate rejects
symbol drift, duplicate coverage, fallback mismatches, unknown metadata enums,
mapped-public classification drift, and silent promotion of residual root
implementation. A repository test import can justify migration work, but never
supported-public classification by itself.

The single preamble import is an implementation dependency of the remaining
root body, not compatibility aliases or supported exports. Any addition,
removal, or retargeting fails the fixture build until it is deliberately
classified; B-10b must not treat these imports as private-alias cleanup.

The fixture retains retired private-binding metadata separately from the live
root surface. A retired name cannot silently return to either compatibility
import branch without failing the audit gate.

The audit follows every import-time `_bind_*_runtime` target and records literal
root-name lookups made through its runtime resolver. This keeps production seams
such as legacy AiO generation, first-pass cache state, resource loading, and
sampling out of the unsupported/test-only bucket even when `nodes.py` does not
load their names directly. `EasyUseAnimaSAM3Context` is also retained as a
transitional alias because the 0.1.6 Detailer plan documents its historical
convenience-node compatibility; it remains unmapped and is not public support.

### Root `__init__.py` entrypoint

- Surface/symbols: `NODE_CLASS_MAPPINGS`, `NODE_DISPLAY_NAME_MAPPINGS`, and
  `WEB_DIRECTORY` through the ComfyUI package entrypoint.
- State: permanent entrypoint; its implementation must become thin, but the
  entrypoint itself is not a retirement candidate.
- Removal gate: not applicable. B-11 must move mapping composition to
  `easyuse_anima.registration` and guarded lifecycle work to bootstrap without
  changing the exported objects or introducing duplicate initialization.
- B-11a PR #292 moves the two literal mapping dictionaries to the pure
  registration owner and re-exports the same objects from the root entrypoint.
  The root class imports, runtime binders, and `WEB_DIRECTORY` remain unchanged.
- B-11b PR #293 makes `api.py` import registration-free, registers the same 20
  handlers once per shared ComfyUI route table, and guards successful wildcard
  startup through `easyuse_anima.bootstrap`. Handler bodies, URL/order,
  correlation wrappers, and wildcard implementation remain unchanged.

### B-11c1 private input-type aliases

- Canonical owner: `easyuse_anima.nodes.input_types`.
- `_FlexibleOptionalInputType` and `_ANY_TYPE` remain transitional direct root
  aliases because the Regional, Prompt Advanced, and LoRA runtime binders load
  them during root composition. Their signatures and call timing are unchanged.
- `_AnyType` has no remaining root production load after `_ANY_TYPE` moves, so
  the machine-readable audit correctly classifies its retained direct alias as
  unsupported/test-only rather than public support. It remains in PR #294 only
  to keep this Move rollback-safe; removal requires a separate compatibility
  review.
- LoRA, Prompt Advanced, Regional, and Wildcard adapters import the shared
  owner instead of retaining duplicate local definitions. Socket values,
  workflow payloads, and mapped node-class identity do not change.

### B-11c2 workflow lookup alias

- Canonical owner: `easyuse_anima.workflow._get_workflow_node`.
- The private root name remains a transitional direct alias. Existing Wildcard
  and NAIA callback binders plus Prompt Advanced and Regional string resolvers
  still resolve through the root at call time, preserving monkeypatch seams.
- The owner reads top-level and nested subgraph workflow metadata without
  mutation or global state. Traversal order, return values, and adapter binder
  signatures do not change in PR #295.
- Reserved wildcard next-seed consumption remains root-owned because moving it
  before D-12 would require a new dependency contract, canonical-to-legacy
  import, or duplicated seed behavior.

### B-11c3 image tensor size alias

- Canonical owner: `easyuse_anima.image.geometry._image_tensor_size`.
- The private root name remains a transitional direct alias. Root AiO resize,
  tile, fit, postprocess, and upscale callers continue to resolve the same root
  binding, while the existing legacy-generation and preview resolvers preserve
  call-time monkeypatch behavior.
- The owner reads BHWC shape width/height and falls back to the supplied integer
  dimensions on the same broad exception boundary. It has no module state,
  mutation, Comfy provider, cache, or I/O dependency.
- `_resize_image_to_size_if_needed` and all stage/postprocess execution remain
  root-owned so this PR does not alter their internal patch seams or behavior.

### B-11c4 AiO LoRA stack signature alias

- Canonical owner:
  `easyuse_anima.aio.model_preparation._aio_lora_stack_signature`.
- The private root name remains a transitional direct alias. AiO `IS_CHANGED`
  and first-pass cache-key generation continue resolving it through their
  existing root runtime resolvers, preserving call-time replacement.
- The canonical owner resolves `_normalize_aio_lora_stack` through the existing
  model-preparation runtime seam, so root monkeypatches and normalized tuple
  ordering remain unchanged in PR #297.
- The helper only projects normalized entries into the existing ordered
  `name`/`strength_model`/`strength_clip` dictionaries. Cache state, eviction,
  node change-key behavior, random state, and I/O remain unchanged.

### B-11c5 AiO Spectrum settings normalizer alias

- Canonical owner:
  `easyuse_anima.aio.generation_normalization._normalize_aio_spectrum_settings`.
- The private root name remains a transitional direct alias. The canonical
  generation normalizer continues resolving that root name at call time for
  highres, upscale, and detailer target settings.
- The moved helper resolves `_as_bool`, `_as_float`, `_as_int`, and `_choice`
  through the existing generation-normalization runtime seam, preserving root
  monkeypatch behavior without adding a binder or canonical-to-root import.
- Dict identity/in-place mutation, unknown keys, defaults, clamp bounds,
  compatibility policy choices, and nested fallback order remain unchanged in
  PR #298. DiT correction, seed, schema/default, and sampler execution stay
  outside this Move.

### B-11c6 AiO DiT correction settings normalizer alias

- Canonical owner:
  `easyuse_anima.aio.generation_normalization._normalize_aio_dit_corrections_settings`.
- The private root name remains a transitional direct alias. The canonical
  generation normalizer continues resolving that root name at call time for
  highres, upscale, and detailer target settings.
- The moved helper resolves `_as_bool`, `_as_float`, `_as_int`, and `_choice`
  through the existing generation-normalization runtime seam, preserving root
  monkeypatch behavior without adding a binder or canonical-to-root import.
- Dict identity/in-place mutation, unknown keys, defaults, and the exact
  DCW/SMC/CFG++/FSG choices, clamp bounds, and nested fallback order remain
  unchanged in PR #299. Spectrum, seed, schema/default, and sampler execution
  stay outside this Move.

### B-11c7a AiO special-seed settings aliases

- Canonical owner:
  `easyuse_anima.aio.generation_normalization` for
  `AIO_SPECIAL_SEED_RANDOM`, `AIO_SPECIAL_SEED_INCREMENT`,
  `AIO_SPECIAL_SEED_DECREMENT`, `AIO_SPECIAL_SEEDS`, and
  `_normalize_aio_seed`.
- The private root names remain transitional direct aliases in both relative
  package and flat import modes. The mutable special-seed set keeps exact
  root/canonical object identity.
- The moved normalizer resolves root `_as_int`, `MAX_SEED`, and the lower-bound
  constant through the existing generation-normalization runtime seam, so
  call-time replacement and the `[-3, MAX_SEED]` clamp remain unchanged.
- PR #300 does not move or alter `_new_aio_random_seed`,
  `_resolve_aio_runtime_seed`, Python RNG consumption, `seed_after_generate`,
  increment/decrement behavior, cache keys, or backend seed reservation.

### B-11c7b AiO runtime-seed aliases

- Canonical owner: `easyuse_anima.aio.sampling` for
  `_new_aio_random_seed` and `_resolve_aio_runtime_seed`.
- The private root names remain transitional direct aliases in both relative
  package and flat import modes. Existing root stages and the legacy-generation,
  output, sampling, and AiO-node runtime resolvers keep calling those root
  names.
- The moved functions resolve root `random`, `MAX_SEED`, `_normalize_aio_seed`,
  mutable `AIO_SPECIAL_SEEDS`, and `_new_aio_random_seed` at call time through
  the existing sampling runtime seam. Root binding replacement and in-place set
  mutation therefore remain visible.
- PR #301 preserves one inclusive `random.randint(0, MAX_SEED)` call for every
  special seed and the existing non-special `[0, MAX_SEED]` clamp. It does not
  add increment/decrement, previous-seed, queue reservation, cache, or browser
  behavior.

### B-11c8 AiO hidden-widget JSON serializer aliases

- Canonical owner: `easyuse_anima.nodes.aio_nodes` for
  `_aio_input_settings_json` and `_aio_generation_settings_json`.
- The private root names remain transitional direct aliases in both relative
  package and flat import modes. The existing AiO node runtime resolver keeps
  calling those root names from the two hidden multiline widget defaults.
- The moved functions resolve root `json`, `AIO_INPUT_DEFAULT_SETTINGS`, and
  `AIO_GENERATION_DEFAULT_SETTINGS` at call time. Root binding replacement and
  in-place default-dict mutation remain visible without a new binder.
- PR #302 preserves `ensure_ascii=False`, compact `(",", ":")` separators,
  insertion order, and no indent/newline. It does not clone, normalize, mutate,
  or move defaults, schemas, widget metadata, or workflow serialization.

### B-11c9 AiO input-settings normalizer alias

- Canonical owner: `easyuse_anima.aio.resources` for
  `_normalize_aio_input_settings`.
- The private root name remains a transitional direct alias in both relative
  package and flat import modes. The resource loader and both AiO Input adapter
  callers keep resolving the root name at call time.
- The moved function resolves root `_merge_versioned_settings`, mutable input
  defaults, schema/version, `_as_int`, `_choice`, dtype choices, and device
  choices through the existing resource runtime seam. Root binding replacement
  therefore remains visible without a new binder.
- PR #303 preserves unknown keys, merge-result mutation, `loader_mode="split"`,
  the single clip-loader choice, and dtype/device fallback order. It does not
  move defaults or schemas, add typed settings, or change widget, workflow,
  resource-loading, cache, seed, or stage behavior.

### B-11c10 dead root JSON helper retirement

- `_settings_json` was a root-only private definition with no production caller,
  runtime resolver, binder, test import, documented compatibility consumer, or
  canonical target. It is therefore removed rather than promoted into the
  canonical package.
- The compatibility fixture and flat/package contract record its absence.
  Root `json`, `_aio_input_settings_json`, and `_aio_generation_settings_json`
  remain present and unchanged.
- PR #304 changes no JSON shape, default, schema, widget/workflow serialization,
  registration/bootstrap, stage, cache, seed, or resource behavior.

### B-11c11 AiO Detailer target normalization aliases

- Canonical owner: `easyuse_anima.aio.generation_normalization` for
  `_AIO_DETAILER_RESERVED_KEYS`, `_AIO_DETAILER_CUSTOM_RE`,
  `_is_aio_detailer_target_name`, `_aio_detailer_target_defaults`, and
  `_aio_detailer_target_order`.
- The five private root names remain transitional direct aliases in both
  relative package and flat import modes. Existing generation normalization,
  Detailer stage/enabled consumers, and schema-contract coverage retain the
  root names.
- The moved functions resolve the mutable reserved-key set and generation
  defaults plus the regex, target-name helper, and JSON clone helper from root
  at call time. Binding replacement and in-place mutation remain visible
  without a new binder.
- PR #305 preserves `custom_\d+` matching, trim/deduplication and explicit/dict/
  face/eye order, reserved/non-dict exclusion, deep cloning, and custom numeric
  label suffixes. It does not move or change Detailer execution/enabled gates,
  schema/default ownership, SAM3, Impact, USDU, or final-fit behavior.

### B-11c12 AiO USDU tile-planning aliases

- Canonical owner: `easyuse_anima.aio.usdu` for
  `_aio_usdu_auto_tile_dimension` and `_aio_usdu_tile_plan`.
- The two private root names remain transitional direct aliases in both
  relative package and flat import modes. The root USDU stage and retained dead
  tile-size wrapper keep calling the root tile-plan alias.
- The dedicated USDU planning binder resolves root `ceil`, `_align_nearest`,
  `_image_tensor_size`, `_as_bool`, `_as_int`, and the nested auto-dimension
  helper at call time. Root binding replacement remains visible without
  importing root `nodes` from the canonical package.
- PR #306 preserves clamp and alignment order, the two `ceil` calls, image-size
  fallback, scale floor and rounding, manual/auto return fields and insertion
  order, and input non-mutation. It does not move USDU model loading,
  conditioning, sampling, logging, metadata, or stage execution. The unused
  `_aio_usdu_tile_size` stayed root-owned pending separate cleanup.

### B-11c13 dead USDU tile-size wrapper retirement

- `_aio_usdu_tile_size` was a root-only private definition with no production
  caller, runtime resolver, public mapping/export, documented user consumer, or
  canonical target. It is removed rather than promoted into the canonical
  package.
- The compatibility fixture and flat/package contract record its absence.
  `_aio_usdu_auto_tile_dimension`, `_aio_usdu_tile_plan`, their binder, and the
  live USDU stage remain present and unchanged.
- PR #307 changes no tile calculation, clamp, rounding, alignment, stage,
  model, conditioning, sampling, logging, metadata, or workflow behavior.

### B-11c14 Detailer enabled-target predicate alias

- Canonical owner: `easyuse_anima.aio.generation_normalization` for
  `_aio_detailer_has_enabled_targets`.
- The private root name remains a transitional direct alias in both relative
  package and flat import modes. Legacy generation continues to resolve and
  invoke that root name at call time.
- The existing generation-normalization binder resolves root `_as_bool` and
  `_aio_detailer_target_order` at use time. The overall disabled short-circuit,
  dict-only target check, target order, per-target coercion, and `any()` lazy
  evaluation are preserved.
- PR #308 changes no Detailer defaults/normalization, stage/target execution,
  SAM3/Impact behavior, metadata, preview, schema, or workflow behavior.

### B-11c15 final-fit size-planning alias

- Canonical owner: `easyuse_anima.aio.postprocess` for
  `_aio_final_fit_size`.
- The private root function remains a transitional direct alias in relative
  package and flat import modes. Root `_apply_aio_final_fit` continues to call
  that alias.
- The postprocess binder resolves `_as_bool`, `_as_float`, `_as_int`, `sqrt`,
  `_align_down`, and `LATENT_ALIGN` at use time. Width/height clamp order,
  disabled and no-downscale short-circuits, mode fallback, strict pixel/edge
  comparisons, Python rounding, alignment call order, and settings immutability
  are preserved.
- PR #309 does not move or change `AIO_FINAL_FIT_MODES`, final-fit application,
  resize behavior, postprocess stage execution, logging, metadata, schema, or
  workflow behavior.

### B-11c16 final-fit application alias

- Canonical owner: `easyuse_anima.aio.postprocess` for
  `_apply_aio_final_fit`.
- The private root function remains a transitional direct alias in relative
  package and flat import modes. Root `_run_aio_postprocess_stage` continues to
  call that alias, so its existing replacement seam is preserved.
- The existing postprocess binder resolves `_as_bool`, `_image_tensor_size`,
  `_aio_final_fit_size`, `_as_int`, `_as_float`, and
  `_resize_image_to_size_if_needed` at use time. Fit-copy behavior, metadata
  insertion and coercion order, no-scale short-circuit, resize method fallback,
  and the actual resize-result `applied` override are unchanged.
- PR #310 does not move or change the shared resize helper, postprocess stage,
  `AIO_FINAL_FIT_MODES`, logging, schema, defaults, or workflow behavior.

### B-11c17 diffusion-model name wrapper alias

- Canonical owner: `easyuse_anima.aio.resources` for
  `_comfy_diffusion_model_names`.
- The private root wrapper remains a transitional direct alias in relative
  package and flat import modes. `EasyUseAnimaInput.INPUT_TYPES` continues to
  resolve that root name at call time.
- The existing resource binder resolves
  `ANIMA_DEFAULT_DIFFUSION_MODEL_CANDIDATES`,
  `_adapter_comfy_diffusion_model_names`, and `_folder_path_names` at use time.
  Candidate order, folder key, fallback type/copy policy, and adapter result are
  unchanged.
- PR #311 does not move or change the infrastructure adapter, constants, folder
  lookup, other resource-name wrappers, INPUT_TYPES, schema, defaults, or
  workflow behavior.

### B-11c18 text-encoder name wrapper alias

- Canonical owner: `easyuse_anima.aio.resources` for
  `_comfy_text_encoder_names`.
- The private root wrapper remains a transitional direct alias in relative
  package and flat import modes. `EasyUseAnimaInput.INPUT_TYPES` continues to
  resolve that root name at call time.
- The existing resource binder resolves `_adapter_comfy_text_encoder_names`,
  `ANIMA_DEFAULT_CLIP_CANDIDATES`, and `_folder_path_names` at use time.
  Candidate order, folder key, fallback type/copy policy, and adapter result are
  unchanged.
- PR #312 does not move or change the infrastructure adapter, constants, folder
  lookup, other resource-name wrappers, INPUT_TYPES, schema, defaults, or
  workflow behavior.

### B-11c19 VAE name wrapper alias

- Canonical owner: `easyuse_anima.aio.resources` for `_comfy_vae_names`.
- The private root wrapper remains a transitional direct alias in relative
  package and flat import modes. `EasyUseAnimaInput.INPUT_TYPES` continues to
  resolve that root name at call time.
- The existing resource binder resolves `_adapter_comfy_vae_names`,
  `ANIMA_DEFAULT_VAE_CANDIDATES`, `_find_comfy_node_class`, and
  `_folder_path_names` at use time. VAELoader-first discovery, exception
  fallback, candidate order/copy policy, folder key, and adapter result are
  unchanged.
- PR #313 does not move or change the infrastructure adapter, constants,
  node-class finder, folder lookup, other resource-name wrappers, INPUT_TYPES,
  schema, defaults, or workflow behavior.

### B-11c20 CLIP loader-type wrapper alias

- Canonical owner: `easyuse_anima.aio.resources` for
  `_comfy_clip_loader_types`.
- The private root wrapper remains a transitional direct alias in relative
  package and flat import modes. `EasyUseAnimaInput.INPUT_TYPES` continues to
  resolve that root name at call time.
- The existing resource binder resolves `_adapter_comfy_clip_loader_types`,
  `ANIMA_CLIP_TYPES`, and `_find_comfy_node_class` at use time. CLIPLoader-first
  discovery, finder exception propagation, loader-processing exception
  fallback, allowed-type order/copy policy, and adapter result are unchanged.
- PR #314 does not move or change the infrastructure adapter, constants,
  node-class finder, other resource-name wrappers, INPUT_TYPES, schema,
  defaults, or workflow behavior.

### B-11c21 AiO postprocess stage alias

- Canonical owner: `easyuse_anima.aio.postprocess` for
  `_run_aio_postprocess_stage`.
- The private root stage remains a transitional direct alias in relative
  package and flat import modes. `easyuse_anima.aio.legacy_generation`
  continues to resolve that root name at call time.
- The existing postprocess binder resolves `_as_bool`, `_image_tensor_size`,
  `_apply_aio_final_fit`, and `logger` at use time. Disabled short-circuit,
  final-fit metadata identity, dimension fallback, limit formatting, logging,
  and return metadata order are unchanged.
- PR #315 does not move or change the host-provider contract for
  `_comfy_max_resolution`, final-fit/resize helpers, legacy-generation caller,
  postprocess schema, defaults, or workflow behavior.

### B-11c22 AiO highres stage alias

- Canonical owner: `easyuse_anima.aio.legacy_generation` for
  `_run_aio_highres_stage`.
- The private root stage remains a transitional direct alias in relative
  package and flat import modes. The canonical legacy-generation caller keeps
  resolving the root name at call time to preserve its monkeypatch seam.
- The existing legacy-generation binder resolves boolean coercion, stage
  sampler planning, scaler construction, VAE encode/decode, model patching,
  sampling, cleanup, resize, and metadata serialization at use time. Disabled
  short-circuit, patch-before-try, sampling-only cleanup, conditional re-encode,
  argument order, and metadata order are unchanged.
- PR #316 does not move or change sampling helpers, the stage protocol, schema,
  defaults, workflow behavior, or the later #169 Contract/Behavior work.

### B-11c23 AiO upscale dispatcher alias

- Canonical owner: `easyuse_anima.aio.legacy_generation` for
  `_run_aio_upscale_stage`.
- The private root dispatcher remains a transitional direct alias in relative
  package and flat import modes. The canonical legacy-generation caller keeps
  resolving the root name at call time to preserve its monkeypatch seam.
- The existing legacy-generation binder resolves boolean coercion and only the
  selected USDU or ResShift leaf at use time. Disabled short-circuit, falsy-
  backend USDU default, exact leaf argument order, unsupported-backend error,
  result identity, and leaf exception propagation are unchanged.
- PR #317 does not move or change either leaf stage, settings/schema/defaults,
  workflow behavior, or the later #169 Contract/Behavior work.

### B-11c24 AiO Detailer stage alias

- Canonical owner: `easyuse_anima.aio.legacy_generation` for
  `_run_aio_detailer_stage`.
- The private root coordinator remains a transitional direct alias in relative
  package and flat import modes. The canonical legacy-generation caller keeps
  resolving the root name at call time to preserve its monkeypatch seam.
- The existing legacy-generation binder resolves boolean coercion, target-order
  planning, SAM3 context loading, the selected Detailer target leaf, and context
  metadata access at use time. Disabled/no-target short-circuits, saved order,
  output chaining, callback timing, metadata identity/order, and exception
  propagation are unchanged.
- PR #318 does not move or change the Detailer target leaf, SAM3 resources,
  settings/schema/defaults, workflow behavior, or the later #169
  Contract/Behavior work.

### B-11c25 AiO ResShift leaf alias

- Canonical owner: `easyuse_anima.aio.legacy_generation` for
  `_run_aio_resshift_upscale_stage`.
- The private root leaf remains a transitional direct alias in relative package
  and flat import modes. The canonical upscale dispatcher keeps resolving the
  root name at call time to preserve its monkeypatch seam.
- The existing legacy-generation binder resolves provider lookup, output tuple
  normalization, runtime seed, integer coercion, and image-size access at use
  time. Provider order, loader/upscaler method validation, tuple-helper lookup
  timing, argument order, exact errors, result identity, and exception
  propagation are unchanged.
- PR #319 does not move or change the USDU leaf, dispatcher,
  settings/schema/defaults, workflow behavior, or the later #169
  Contract/Behavior work.

### B-11c26 AiO Detailer target leaf alias

- Canonical owner: `easyuse_anima.aio.legacy_generation` for
  `_run_aio_detailer_target`.
- The private root leaf remains a transitional direct alias in relative package
  and flat import modes. The canonical Detailer coordinator keeps resolving the
  root name per enabled target to preserve its monkeypatch seam.
- The existing legacy-generation binder resolves enabled coercion, sampler
  planning, Spectrum model patching, the SAM3 Detailer class, argument coercion,
  cleanup, SEGS detection, and sampler metadata conversion at use time. Keyword
  order/defaults, cleanup timing and exception precedence, result identity and
  parsing, metadata order, and exception propagation are unchanged.
- PR #320 does not move or change the Detailer coordinator, SAM3/SEGS helpers,
  settings/schema/defaults, workflow behavior, the USDU leaf, or the later #169
  Contract/Behavior work.

### B-11c27 AiO USDU upscale leaf alias

- Canonical owner: `easyuse_anima.aio.legacy_generation` for
  `_run_aio_usdu_upscale_stage`.
- The private root leaf remains a transitional direct alias in relative package
  and flat import modes. The canonical upscale dispatcher keeps resolving the
  root name at call time to preserve its monkeypatch seam.
- The existing legacy-generation binder resolves provider/model loading, stage
  planning, coercion, tile/log/conditioning/model-patch operations, runtime seed,
  cleanup, tuple/image-size handling, the prompt-mode default, and sampler
  metadata conversion at use time. Provider and log order, external call kwargs,
  cleanup timing and exception precedence, exact empty-output error, result
  identity, lazy default lookup, and metadata order are unchanged.
- The temporary owner remains over the roadmap size review trigger; #169 owns
  later stage decomposition after its Contract work. PR #321 does not split the
  function or change USDU planning/conditioning/provider ownership, schema,
  defaults, seed/tile/log behavior, dispatcher behavior, or public `__all__`.

### B-11c28 shared AiO image-resize helper alias

- Canonical owner: `easyuse_anima.aio.postprocess` for
  `_resize_image_to_size_if_needed`.
- The private root helper remains a transitional direct alias in relative
  package and flat import modes. Postprocess and legacy-generation consumers
  continue to resolve the root name at call time, preserving the existing
  monkeypatch seam.
- The existing postprocess binder resolves `_image_tensor_size` and
  `_common_upscale_image` at use time. Width/height clamp order, BHWC-to-BCHW
  and BCHW-to-BHWC moves, same-size image identity and `False` result, bicubic
  fallback, resize boolean, and raw exception propagation are unchanged.
- PR #322 does not move or change the Comfy upscale adapter, image-size helper,
  final-fit/highres/stage logic, schema/defaults, provider/RuntimeServices
  contract, wildcard seed reservation, or public `__all__`.

### B-11c29a max-resolution root-wrapper retirement

- `_comfy_max_resolution` is an unsupported/test-only private root seam with no
  root monkeypatch consumer, confirmed external consumer, or call-time root
  replacement requirement.
- PR #329 removes the root definition and both adapter imports. Installed
  runtime consumers continue to resolve `ComfyHostProvider.max_resolution`.
- Flat pre-bootstrap imports resolve a fresh `DefaultComfyHostProvider` bound
  method at call time. Host lookup order, integer conversion, and the `16384`
  fallback remain unchanged without importing canonical code from root.
- No provider cache, mutable override, schema change, or other host-helper Move
  is included.

### B-11c29b1 direct mapping node-lookup retirement

- `_find_comfy_node_mapping_class` is an unsupported/test-only private root seam
  with one provider-wired SAM3 consumer and no repository replacement or
  confirmed external consumer.
- PR #330 removes only the root definition. There was no adapter alias for this
  mapping-only wrapper.
- Installed runtime uses `ComfyHostProvider.find_node_mapping_class`; flat
  pre-bootstrap imports resolve a fresh default provider at call time.
- Lookup remains limited to `NODE_CLASS_MAPPINGS.get(node_id)`. Host attributes
  and loaded modules are not scanned, missing/invalid host state returns
  `None`, and no cache or mutable override is added.
- Loaded lookup, requirement helpers, CLIP invocation, and the general node
  lookup remain separate retirement units.

### B-11c29b2 loaded node-lookup retirement

- `_find_loaded_node_class` is an unsupported/test-only private root seam with
  one provider-wired conditioning consumer and no repository replacement or
  confirmed external consumer.
- PR #331 removes the root definition and relative/flat
  `_adapter_find_loaded_node_class` imports.
- Installed runtime uses `ComfyHostProvider.find_loaded_node_class`; flat
  pre-bootstrap imports resolve a fresh default provider at call time.
- General node lookup remains first, followed by current `sys.modules` order
  for `NODE_CLASS_MAPPINGS[node_id]`. Missing classes return `None`; optional
  packs are not imported and no cache or mutable override is added.
- Requirement helpers and CLIP invocation must retire before the general root
  lookup.

### B-11c29c required-node helper retirement

- `_require_custom_node_class` and `_require_any_custom_node_class` are
  unsupported/test-only pure root seams with provider-injected canonical
  implementations, no repository replacement, and no confirmed external
  consumer.
- PR #332 removes both root definitions and their four relative/flat adapter
  imports as one rollback unit.
- Installed-runtime consumers keep the canonical pure helpers with
  `ComfyHostProvider.find_node_class` injected. Flat pre-bootstrap calls use a
  fresh default provider lookup at call time.
- Single lookup identity, multi-candidate order and tuple result, exact missing
  `RuntimeError` text, raw finder exception propagation, and use-time-only
  optional dependency behavior remain unchanged.
- The provider interface and canonical capability helpers are unchanged. CLIP
  invocation retires next, before the general root lookup.

### B-11c29d CLIP invocation retirement

- `_encode_with_comfy_clip` is an unsupported/test-only pure root seam with six
  provider-wired production modules, no repository replacement, and no
  confirmed external consumer.
- PR #333 removes the root definition and both relative/flat adapter imports.
  The redundant direct root invocation assertion retires; canonical and flat
  wiring tests retain the behavior evidence.
- Installed-runtime consumers keep the canonical invocation helper with
  `ComfyHostProvider.find_node_class` injected. Flat pre-bootstrap calls use a
  fresh default provider lookup at call time.
- `CLIPTextEncode` lookup, construction, method resolution, invocation, tuple
  validation, first-result identity, exact errors, and raw exception
  propagation remain unchanged.
- The provider interface, canonical invocation helper, and six production
  consumers are unchanged. General lookup retires next as B-11c29b3.

### B-11c29b3 general node-lookup retirement

- `_find_comfy_node_class` is an unsupported/test-only provider-owned root seam
  with six provider-wired production binder modules, 17 lookup call sites, no
  repository replacement, and no confirmed external consumer.
- The retirement removes the root definition and both relative/flat
  `_adapter_find_comfy_node_class` imports.
- Installed runtime keeps `ComfyHostProvider.find_node_class`; flat
  pre-bootstrap imports use a fresh default provider at call time.
- Host mapping, host attribute, and current loaded-module lookup order,
  exception fallthrough, first non-`None` result identity, missing `None`
  result, and use-time-only optional dependency behavior remain unchanged.
- The provider interface, canonical capability helper, six production
  consumers, and their binder-owned runtime state remain unchanged.

### B-11c30 runtime binder/resolver audit

- Production files are unchanged. The machine-readable compatibility surface
  now records every root binder call, canonical target module, owner family,
  root keyword, bound global, direct root dependency, string resolver name,
  provider virtual name, call-time observation mode, and repository replacement
  file.
- The exact baseline is 30 binders in five owner families: AiO 12,
  Image/SAM3/Impact 3, Prompt/Regional 10, Wildcard/NAIA 2, and LoRA 3.
- Resolution modes are 15 provider-then-root, 13 root-only, and two explicit
  callback binders. There are 295 unique resolved names: 288 root names and all
  seven E-07 provider virtual seams.
- Provider use remains 22 slots in 15 canonical modules. The provider does not
  accept arbitrary feature names; every non-provider name remains classified
  as a root compatibility/residual or preamble dependency.
- Repository tests replace 165 root names in 20 files. This is exact migration
  impact evidence, not external/public support evidence.
- Cleanup proceeds by owner family. Image/SAM3/Impact is the first candidate;
  Prompt/Regional and AiO require further sub-splitting, while Wildcard/NAIA
  remains separate from D-12 behavior.

### B-11c30a Image/SAM3/Impact binder retirement

- The three root binder imports/calls and the three canonical binder
  definitions are removed.
- Five E-07 provider slots remain call-time direct consumers in their canonical
  modules. The Comfy host ledger keeps the same 22 slots and 15 modules.
- `_impact_scheduler_names`, `_load_checkpoint_with_comfy`, and
  `_preferred_checkpoint_default` use their existing canonical owners; their
  other root consumers and aliases are unchanged.
- The remaining binder audit contains 27 binders in four owner families. It no
  longer treats the retired family or its bind-time module globals as active
  compatibility state.
- No node schema, workflow, optional-dependency timing, or SAM3/Impact behavior
  changes in this Move.

### B-11c30b LoRA binder retirement

- The three root LoRA binder imports/calls and canonical binder definitions are
  removed.
- Metadata and preset keep use-time canonical-module helper lookup. Prompt
  tokenization and prompt correction remain lazy callbacks, and the logger
  remains a use-time proxy.
- The LoRA node adapter keeps direct canonical helper imports and exact shared
  input-type identity.
- Root helper/class aliases remain direct canonical aliases. Only tests that
  used root replacement to drive LoRA canonical consumers move to the owning
  module.
- The remaining binder audit contains 24 binders in three owner families. No
  LoRA schema, workflow, stack/trigger order, missing-model policy, or optional
  dependency behavior changes in this Move.

### B-11c30c Prompt/Regional split gate

- PR #339 / `d0188b5` changes no production code. It decomposes the ten
  Prompt/Regional binders into six feature-service owners and four node-adapter
  owners without changing their symbols, callers, resolver names, bound
  globals, provider slots, or replacement evidence.
- The service and adapter subgroups are separate rollback units. A Move may not
  retire both subgroups together.

### B-11c30c1 Prompt/Regional service binder retirement

- The six root binder imports/calls and canonical service binder definitions
  for Regional, Advanced, Conditioning, Artist Mix, Prompt Fields, and Prompt
  Correction are removed.
- Canonical service calls now resolve canonical module globals directly.
  Advanced keeps the still-legacy `wildcard_engine` behind call-time wrappers,
  preserving the package skeleton's no-eager-NumPy import boundary before D-12.
  Artist Mix CLIP encoding and Conditioning loaded-node lookup remain direct
  call-time E-07 provider consumers; the Comfy host ledger remains 22 slots
  across 15 modules.
- Root helper aliases remain direct canonical aliases. Tests that replaced root
  only to drive a canonical service now replace that service owner, while all
  four node-adapter binders retain their existing root seams for B-11c30c2.
- The remaining audit is 18 binders in three families: ten
  provider-then-root, six root-only, and two explicit callbacks. No schema,
  workflow, prompt/conditioning behavior, provider lookup order, warning-once
  state, or optional-dependency timing changes in this Move.

### B-11c30c2 Prompt/Regional node-adapter split gate

- This production-free gate retains all four node-adapter binders and their
  current resolver/global state.
- B-11c30c2a owns `_bind_prompt_data_node_runtime` and
  `_bind_prompt_node_runtime`: 30 root resolver slots over 27 unique names and
  one provider slot. Their canonical/common/provider owners already exist.
- B-11c30c2b owns `_bind_prompt_advanced_node_runtime` and
  `_bind_regional_node_runtime`: 69 root resolver slots over 53 unique names and
  one provider slot. Both observe `_consume_reserved_wildcard_next_seed` at
  call time from their real build path.
- The residual seed function remains root-owned under #167/D-12. Removing the
  c2b binders before that owner exists would require a new callback contract,
  canonical-to-root import, or duplicated seed behavior, all of which are
  forbidden in this Move series.
- Test replacement evidence remains migration cost, not supported-public
  compatibility. Schema, workflow, mapped-class/input-type identity, provider
  timing, and wildcard seed payloads remain unchanged.

### B-11c30c2a Prompt Data / Classic Prompt adapter binder retirement

- Root no longer imports or invokes `_bind_prompt_data_node_runtime` or
  `_bind_prompt_node_runtime`; their canonical definitions and bind-time
  mutation state are absent.
- Prompt Data imports its canonical prompt/AiO helpers directly and keeps CLIP
  encoding behind the existing call-time E-07 provider. The Comfy host ledger
  remains 22 slots across 15 modules.
- Classic Prompt uses canonical common/prompt helpers and the existing
  `anima_prompt`/`settings` fallback imports directly. Tests that previously
  patched root only to drive either adapter now patch the adapter owner.
- The remaining audit is 16 binders in three families: nine
  provider-then-root, five root-only, and two explicit callbacks.
- The two Advanced/Regional binders stay unchanged for B-11c30c2b.
  S167-01a owns the separate behavior-preserving consumer Move; no schema,
  saved-workflow, output, provider order, optional-dependency timing, or
  wildcard seed behavior changes in either Move.

### S167-01a reserved Wildcard seed consumer Move

- Canonical owner:
  `easyuse_anima.seed.compatibility._consume_reserved_wildcard_next_seed`.
- Root `nodes.py` retains direct aliases for the consumer, hidden input name,
  and public-safe queue seed bound. B-11c30c2b adapters import the canonical
  consumer directly while those root aliases remain compatibility surface.
- The canonical owner imports `_single_value` directly and resolves the
  pre-D-12 `wildcard_engine` only at call time. It does not import root
  `nodes.py`, add a callback contract, eagerly import NumPy, or copy Wildcard
  normalization behavior.
- The machine-readable audit moves three symbols into canonical direct imports:
  canonical bindings are 284, root residual functions are zero, root residual
  globals are 24, and runtime binders remain 16.
- Version-1 payload bytes, pop order, accepted mode/control/seed values, return
  values, workflows, and browser reservation behavior remain unchanged.

### B-11c30c2b Advanced / Regional adapter binder retirement

- Root no longer imports or invokes `_bind_prompt_advanced_node_runtime` or
  `_bind_regional_node_runtime`; both canonical binder definitions and their
  bind-time mutation state are absent.
- Advanced imports canonical common, Prompt, seed, workflow, NAIA, and
  input-type owners directly. It reuses the Prompt service's call-time
  Wildcard module resolver and keeps the existing flat settings fallback.
- Regional imports canonical Prompt/seed/workflow owners directly and resolves
  `_encode_with_comfy_clip` through the existing E-07 provider at call time.
  The Comfy host ledger remains 22 slots across 15 modules.
- Tests that previously patched root only to drive either adapter now patch the
  canonical adapter owner.
- Canonical root bindings are 282, root residual functions remain zero, root
  residual globals remain 24, and the runtime audit is 14 binders in two
  families: eight provider-then-root, four root-only, and two explicit
  callbacks.
- Schema, mapped-class/input-type identity, outputs, provider timing, seed
  payload/pop order, Wildcard arithmetic, workflows, and optional-dependency
  timing remain unchanged.

### B-11c30d AiO binder split gate

- Production files and all fourteen remaining binders are unchanged.
- The twelve AiO binders are classified exactly once into six non-overlapping
  rollback units: d1 cache state; d2 normalization/planning; d3 I/O boundary;
  d4 execution services; d5 legacy orchestration; and d6 node adapter.
- The machine-readable audit freezes each subgroup's binder names, binding
  modes, bound globals, root/provider/direct dependency slots, replacement
  slots, and replacement files. Later retirement tests select their frozen
  subgroup rather than rebuilding the full AiO inventory.
- d1 is READY. Its cache dictionary/list identity, order, limit, key, clone,
  hit, and eviction behavior remain under #169 and are not changed by the
  binder Move.
- d0a is a separate pure-owner Move for the two output-settings normalizers.
  It breaks the output/sampling/generation-normalization import cycle before
  d2 through d4.
- d0b is a separate pure-owner Move for the two input-context helpers. It
  breaks the legacy-generation/node-adapter import cycle before d5 and d6.
- Neither prerequisite Move is implemented by this gate. No schema, setting,
  workflow, stage, seed, cache, model, sampling, preview, save, conditioning,
  provider, optional-dependency, or error behavior changes.

### B-11c30d1 AiO cache-state binder retirement

- Root no longer imports or invokes `_bind_aio_first_pass_cache_runtime`; the
  canonical binder, `_RUNTIME_RESOLVER`, and `_runtime_helper` are removed.
- `easyuse_anima.aio.first_pass_cache` uses its module-owned limit, dictionary,
  order list, and recursive clone function directly. It imports the stable-key,
  Prompt Data JSON-safe, and LoRA-signature helpers from their existing
  canonical owners without a root dependency.
- Root limit/state/clone/key/get/put bindings remain direct canonical aliases.
  The already-retired cache-clear root alias remains absent.
- Cache-specific tests replace the canonical owner. Root replacements owned by
  still-active legacy-generation, node-adapter, or preview binders do not move.
- The incremental split gate marks d1 retired and keeps d2 through d6 as the
  exact active AiO set. The total audit is 13 binders in two families.
- Cache object identity, key schema/order, clone behavior, falsey miss, hit
  refresh, overwrite, limit 2, oldest-first eviction, stage metadata, and #169
  Behavior remain unchanged.

### B-11c30d0a AiO output-settings owner Move

- `_normalize_aio_hash_bundles` and
  `_normalize_aio_civitai_hash_fetchers` have one definition owner in
  `easyuse_anima.aio.output_settings`.
- `easyuse_anima.aio.generation_normalization` imports both normalizers
  directly, removing their two root runtime-resolver edges without retiring
  the generation-normalization binder.
- `easyuse_anima.aio.output` re-exports the same two objects and retains its
  existing d3 save-time runtime calls. Root `nodes.py` imports the canonical
  owner in both package and flat modes, so both root aliases preserve exact
  identity.
- The new owner directly imports stateless
  `easyuse_anima.common.values._as_bool`; the previous test-only root patch seam
  moves to the canonical owner.
- Accepted settings, JSON fallback, row filtering and trimming, default boolean
  conversion, schema/workflow, save metadata, provider/error behavior, seed,
  cache, and stage order remain unchanged.

### B-11c30d2 AiO normalization/planning binder retirement

- Root and the three canonical modules no longer carry
  `_bind_aio_generation_normalization_runtime`,
  `_bind_aio_usdu_planning_runtime`, or
  `_bind_aio_postprocess_runtime`; their resolver globals/helpers are absent.
- `easyuse_anima.aio.generation_defaults` is the single owner of the mutable
  generation default payload and its schema, special-seed, final-fit/upscale,
  USDU, and ResShift values. Root and generation normalization retain exact
  identity aliases to those owner objects.
- Generation normalization imports common, Prompt, image, capability,
  migration/settings, and output-settings owners directly. Only
  `_comfy_max_resolution` remains a call-time E-07 provider lookup.
- USDU and postprocess planning use direct math, value, geometry, invocation,
  logging, and same-module calls. The now-unused root `ceil`/`sqrt` preamble
  imports are removed with their binders.
- The split gate marks d1 and d2 retired while d3 through d6 remain active.
  Ten binders remain in two families: eight AiO and two Wildcard/NAIA.
- Settings shape/order, normalization, seed semantics, tile/final-fit behavior,
  provider observation, schema/workflow, and stage order remain unchanged.

### B-11c30d3 AiO I/O-boundary binder retirement

- PR #350 retires exactly `_bind_aio_resource_runtime`,
  `_bind_aio_preview_runtime`, and `_bind_aio_output_runtime`.
- The pre-edit surface is 49 root-resolver slots over 46 names, four E-07
  provider slots, three direct root-helper dependencies, and 45 repository
  replacement slots over 43 names in eight files.
- Mutable `AIO_INPUT_DEFAULT_SETTINGS` and its declarative input/resource
  values move to one pure `easyuse_anima.aio.input_defaults` owner. Root
  remains an exact compatibility alias; the d0b input-context Move does not
  begin here.
- Resource, preview, and output implementations import existing canonical
  stateless owners directly. Comfy node lookup remains call-time
  provider-owned, and optional filesystem/server/image dependencies retain
  their current call-time imports and fallbacks.
- Only d3-owner tests move their patch ownership to the canonical modules.
  Root patches that drive d4 through d6 remain until those retirement units.
- Resource discovery/loading, preview and save I/O, metadata/event payloads,
  filenames, errors, logs, schemas/workflows, and stage behavior are frozen.
- The d3 binder definitions, resolver globals/helpers, and root imports/calls
  are absent. Seven binders remain in two families: five AiO and two
  Wildcard/NAIA. The active AiO split now contains only d4 through d6.
- The compatibility inventory contains 296 canonical root bindings, three
  residual root globals, 92 shipped and reachable Python modules, and a
  1,182-line root shim.

### B-11c30d4 AiO execution-service binder retirement

- PR #351 retires exactly `_bind_aio_model_preparation_runtime`,
  `_bind_aio_sampling_runtime`, and `_bind_aio_conditioning_runtime`.
- The current surface is 43 root-resolver slots over 37 names, six E-07
  provider slots over four names, three direct root-helper dependencies, and
  23 repository replacement slots over 21 names in six files.
- The three binders own only three `_RUNTIME_RESOLVER` globals. Root imports
  all 26 canonical execution functions as exact package/flat aliases and calls
  each binder once.
- Model preparation consumes existing common-value, Comfy invocation, LoRA,
  and E-07 owners. Sampling consumes common serialization/value, generation
  default/normalization, Prompt conditioning, seed, invocation, and E-07
  owners. Conditioning consumes common value, Prompt Data/Advanced,
  generation-default, and E-07 owners.
- Same-module calls become direct and only d4 owner tests move patch ownership
  to the canonical modules. Root replacements that drive d5/d6 remain.
- Model patches/cleanup, LoRA, random/effective seeds, Comfy/Spectrum sampling,
  VAE encode/decode, stage settings, Prompt Data selection, CLIP conditioning,
  provider timing, errors/logs, schemas/workflows, cache, and stage behavior
  are frozen.
- The d4 binder definitions, resolver globals/helpers, and root imports/calls
  are absent. Four binders remain: d5, d6, and the two Wildcard/NAIA callbacks.
- The compatibility inventory contains 293 canonical root bindings, three
  residual root globals, 92 shipped and reachable Python modules, and a
  1,158-line root shim.

### B-11c30d0b AiO input-context owner Move

- PR #352 moves exactly `_easy_use_anima_input_signature` and
  `_require_easy_use_anima_input` from
  `easyuse_anima.nodes.aio_nodes` to
  `easyuse_anima.aio.input_context`.
- The new owner imports only
  `easyuse_anima.prompt.data._prompt_data_json_safe` and owns no mutable state.
  Signature shape, JSON-safe conversion, required-key order, and exact errors
  are unchanged.
- Legacy generation and the node adapter import the owner directly. The node
  adapter re-exports the same function objects, and root imports the owner in
  both package and flat modes, preserving exact alias identity.
- The d5 legacy-orchestration resolver falls from 59 to 58 root slots, and the
  d6 node-adapter resolver falls from 30 to 29. Neither binder, resolver
  global, nor any other resolver edge is retired in this Move.
- All four remaining binders stay active. The audit contains 84 unique
  resolver names, 82 root names, two provider names, and 69 repository
  replacement names across five files.
- The compatibility inventory still contains 293 canonical root bindings and
  three residual root globals. The package contains 93 shipped and reachable
  Python modules, and the root shim is 1,162 lines.
- B-11c30d5 legacy orchestration is the next separate Move; d6, Wildcard/NAIA,
  #168/#169 Behavior, and final root-shim work remain outside PR #352.

### B-11c30d5 AiO legacy-orchestration binder retirement

- PR #353 retires exactly `_bind_aio_legacy_generation_runtime`, its single
  `_RUNTIME_RESOLVER`, and `_runtime_helper`.
- `easyuse_anima.aio.legacy_generation` imports the existing common, Prompt,
  AiO, image, invocation, and node-adapter owners directly. Same-module stage
  calls are direct, and JSON, logging, and random access are module-owned.
- CLIP encoding and optional custom-node requirements still resolve through
  the existing E-07 provider at call time. Their lookup order, lazy failure,
  and exact feature errors are unchanged.
- All seven legacy execution functions remain exact package/flat root aliases.
  The d6 adapter remains the sole production consumer of
  `_run_aio_legacy_generation` through its separate active resolver.
- Tests patch the canonical consumer rather than installing and restoring a
  process-global resolver. This removes cross-test resolver state while
  preserving short circuits, cleanup order, metadata order, provider timing,
  and the frozen legacy execution trace.
- Three binders remain: d6 and the two Wildcard/NAIA callbacks. The audit now
  contains 29 unique resolver/root names, no provider-resolver slot, and 32
  repository replacement names across five files.
- The compatibility inventory contains 291 canonical root bindings and three
  residual root globals. The package remains at 93 shipped and reachable
  Python modules, and the root shim is 1,147 lines.
- B-11c30d6 is the next separate Move; Wildcard/NAIA, #168/#169 Behavior, and
  final root-shim work remain outside PR #353.

### B-11c30d6 AiO node-adapter binder retirement

- PR #354 retires exactly `_bind_aio_node_runtime`, its single
  `_RUNTIME_RESOLVER`, and `_runtime_helper`.
- `easyuse_anima.nodes.aio_nodes` imports existing common, Prompt Data, AiO
  defaults/normalization/resources/model/sampling/input-context/orchestration
  owners directly and owns the existing JSON serializers locally.
- `EASY_USE_ANIMA_INPUT_TYPE` moves from the residual root assignment to the
  canonical adapter, while root retains exact package/flat identity.
- Tests patch the canonical consumer rather than process-global resolver state.
  Node signatures, hidden widget serialization, change keys, seed handling,
  input context/copy behavior, generation forwarding, mappings, schemas,
  workflows, and exact errors remain unchanged.
- The AiO family and all string runtime resolvers are now absent. Two explicit
  Wildcard/NAIA callback binders remain in one family, with eight unique direct
  callback dependencies and five repository replacement names in three files.
- The compatibility inventory contains 291 canonical root bindings, two
  residual root globals, one preamble implementation import, 93 shipped and
  reachable Python modules, and a 1,142-line root shim.
- B-11c30e Wildcard/NAIA is the next separate Move; #168/#169 Behavior and the
  final root shim remain outside PR #354.

### B-11c30e Wildcard/NAIA callback-binder retirement

- PR #355 retires exactly `_bind_wildcard_node_runtime` and
  `_bind_naia_node_runtime`.
- Both adapters import `easyuse_anima.workflow._get_workflow_node` directly.
  Wildcard keeps its existing package/flat legacy-engine imports. NAIA imports
  the existing settings owner with the same fallback and retains its direct
  client imports.
- The nine bind-time callback installations over eight unique names are
  absent. Root no longer imports or invokes either binder.
- Tests patch canonical consumers rather than root callbacks. Wildcard
  syntax/sources/modes/seeds/expansion/metadata, NAIA
  settings/HTTP/cache/results, mapped classes, package/flat imports, workflows,
  and exact errors remain unchanged.
- Runtime binder families, string resolvers, direct callback dependencies, and
  binder-owned repository replacement names all reach zero.
- The compatibility inventory contains 289 canonical root bindings, two
  residual root globals, one preamble implementation import, 93 shipped and
  reachable Python modules, and a 1,123-line root shim.
- B-11d final root shim is the next separate Move; #167/#236 Behavior and
  D-09/D-12 consolidation remain outside PR #355.

### B-11d final root-shim cutover inventory

- Pre-edit `nodes.py` contains 289 canonical and 27 legacy direct bindings,
  18 mapped supported classes, two unmapped class aliases, no
  functions/classes/binders/resolvers, and two residual globals.
- The supported `nodes.py.__all__` is exactly the 18 mapped classes in
  registration order. Existing audited private/test-only aliases remain
  explicit direct bindings outside `__all__`; B-11d does not promote or remove
  them.
- Root `__init__.py` preserves its mapped class attributes and permanent
  mapping/display/`WEB_DIRECTORY` entrypoints through
  `easyuse_anima.registration`, without consuming the compatibility
  `nodes.py`.
- `logger`, `_TRIGGER_WORD_KEYS`, and their `logging` import are unused root
  implementation residue and are the only production symbols retired here.
- Any private alias retirement still follows ADR-002 as a separate reviewed
  unit after maintained-consumer, published-release, and packed-archive gates.
- The implemented B-11d surface has zero preamble implementation imports and
  zero residual functions/classes/globals. `nodes.py.__all__` is exactly the
  18 mapped classes, while all 316 audited direct alias bindings remain
  unchanged outside that supported list.
- Root `__init__.py` obtains the same class objects from
  `easyuse_anima.registration` rather than consuming the compatibility shim.
  The backend analyzer treats both root modules as Registry entry modules and
  records all 93 shipped Python modules as reachable.
- The B-11d exit evidence passes in PR #356: one official full run, Registry
  validate/pack with exact Python archive closure, all 18 live mapped node
  registrations, and representative same-seed Wildcard queue execution.

### `nodes.py` public node-class surface

The confirmed 0.5.2 mapped classes are:

```text
EasyUseAnimaAIOGenerator
EasyUseAnimaDetailerAlignHook
EasyUseAnimaArtistMixConditioning
EasyUseAnimaInput
EasyUseAnimaImageScaleByMultiple
EasyUseAnimaLoraPreset
EasyUseAnimaNAIARandomPrompt
EasyUseAnimaPromptDataConditioning
EasyUseAnimaPromptDataUnpack
EasyUseAnimaPromptBuilder
EasyUseAnimaPromptCorrector
EasyUseAnimaPromptCorrectorSimple
EasyUseAnimaPromptStudio
EasyUseAnimaPromptStudioAdvanced
EasyUseAnimaPromptStudioAdvancedV2
EasyUseAnimaPromptStudioRegional
EasyUseAnimaRegionalConditioning
EasyUseAnimaWildcard
```

- Canonical target: corresponding modules under `easyuse_anima.nodes`.
- Supported-shim shape: explicit direct imports and `__all__`; each root class
  must be identical to the mapped canonical class.
- Excluded by default: unmapped/private helpers and historical classes not in
  the 0.5.2 public mapping. A separate consumer audit is required before
  deciding that an unmapped symbol is supported.
- B-04 compatibility exception: `_align_nearest`, `_align_down`, and the two
  image scaling constants remain explicit direct aliases to their canonical
  modules because root residual code or a canonical runtime resolver consumes
  them. They are not wrappers.
- B-07f internal SAM3 transition: `EasyUseAnimaSAM3Context` and
  `EasyUseAnimaSAM3Detailer` remain direct root aliases to
  `easyuse_anima.nodes.sam3_nodes`. SAM3 resolver, formatting, context,
  mask/SEGS, and Impact-call helpers moved to
  `easyuse_anima.image.sam3` and remain direct root aliases through the B-10
  compatibility audit. These names are internal transition surfaces for the
  root AiO caller, historical convenience-node compatibility, and focused
  monkeypatch tests; they are not mapped public nodes and are not added to
  locales or a canonical public `__all__`.
- B-08a internal AiO resource transition: resource default selection, ComfyUI
  model/CLIP/VAE/upscale loading, SAM3 context loading, and AiO resource bundle
  helpers move to `easyuse_anima.aio.resources`; Impact core/scheduler lookup
  moves to `easyuse_anima.infrastructure.comfy.capabilities`. Eleven root
  private names remain direct identity aliases because the current root AiO,
  SAM3, Impact detailer, and normalization callers and their focused
  monkeypatch seams still consume them. `_impact_core_module` is excluded after
  B-10b4 because the canonical scheduler helper calls it within the same module
  and the root alias was only a test identity seam. The remaining names stay
  internal transition surfaces and are not added to public package `__all__`.
- B-08b1 internal AiO model-preparation transition: LoRA normalization and
  application, AuraFlow/DAVE/Safe PAG/KJ base-model patching, and USDU
  conditioning preparation move to `easyuse_anima.aio.model_preparation` and
  `easyuse_anima.aio.conditioning`. Their ten root private names remain direct
  identity aliases so the current root generator/stages and focused monkeypatch
  seams preserve call-time behavior. Shared CLIP encoding moves to
  `easyuse_anima.infrastructure.comfy.invocation` behind the existing root
  injection wrapper. These are internal transition surfaces through the B-10
  compatibility audit and are not added to public package `__all__`.
- B-10b1 checkpoint-name cleanup: `_comfy_checkpoint_names` is no longer a root
  alias. `easyuse_anima.nodes.sam3_nodes` already imports the canonical
  `easyuse_anima.infrastructure.comfy.resources` function directly, and tests
  patch that real consumer rather than retaining a root-only monkeypatch seam.
- B-10b2 Detailer-hook cleanup: `_EasyUseAnimaAlignedDetailerHook` is no longer
  a root alias. The image and Impact Detailer adapters already import the
  canonical `easyuse_anima.image.detailer` class directly; normal-package and
  synthetic package-entrypoint tests preserve class identity and hook
  construction without a root-only private import.
- B-10b3 Impact-delegate cleanup: `_EasyUseAnimaImpactDetailerDelegate` is no
  longer a root alias. The SAM3 adapter already imports the canonical
  `easyuse_anima.nodes.impact_detailer_nodes` class directly; normal-package
  and synthetic package-entrypoint tests preserve class identity,
  `INPUT_TYPES`, and the existing canonical delegation path.
- B-10b4 Impact-core cleanup: `_impact_core_module` is no longer a root alias.
  The canonical `_impact_scheduler_names` implementation calls the helper in
  `easyuse_anima.infrastructure.comfy.capabilities` directly; normal-package
  and synthetic package-entrypoint tests preserve Impact discovery, scheduler
  lookup, and optional-dependency fallback behavior.
- B-10b5 image-geometry cleanup: `_align_up`, `_aligned_size_near_scale`, and
  `_alignment_value` are no longer root aliases. Geometry, scaling, image-node,
  and Detailer production consumers already import
  `easyuse_anima.image.geometry` directly; normal-package and synthetic
  package-entrypoint tests preserve canonical geometry behavior. Root
  `_align_nearest` and `_align_down` remain for residual runtime callers.
- B-10b6 image-scaling cleanup: `_image_scale_by_multiple_size`,
  `_max_long_edge_value`, `_normalize_image_scale_options`, and
  `_scale_by_value` are no longer root aliases. The canonical image adapter and
  scaling policy already consume `easyuse_anima.image.scaling` directly;
  normal-package and synthetic package-entrypoint tests preserve size,
  max-edge, and legacy shifted-widget normalization behavior. The two scaling
  constants and mapped image-scale node class remain root compatibility seams.
- B-10b7 AiO cache-clear cleanup: `_clear_aio_first_pass_cache` is no longer a
  root alias. Repository tests call the canonical
  `easyuse_anima.aio.first_pass_cache` owner directly; normal-package and
  synthetic package-entrypoint tests reject the retired root name. Mutable
  cache state and the remaining binder/resolver seams stay unchanged.
- B-10b8 wildcard-note cleanup: `WILDCARD_SEED_RANGE_NOTE` is no longer a root
  alias. The canonical Wildcard adapter owns and consumes the immutable tooltip
  string directly; normal-package and synthetic package-entrypoint tests reject
  the retired root name while preserving the canonical tooltip and mapped class.
- B-10b9 SAM3 helper cleanup: `_call_impact_detailer`,
  `_empty_mask_for_image`, `_empty_segs_for_image`,
  `_find_impact_detailer_class`, `_find_impact_mask_to_segs_class`,
  `_find_sam3_detect_class`, and `_format_sam3_detection_prompt` are no longer
  root aliases. Canonical SAM3 and Impact adapters import the owner directly;
  normal-package and synthetic package tests reject the retired names while
  preserving resolver timing, formatting, masks/SEGS, and delegation contracts.
- B-10b10 prompt-default cleanup: `DEFAULT_QUALITY_TAGS` and
  `DEFAULT_TRAILING_QUALITY_TAGS` are no longer root aliases. Prompt Builder,
  Prompt Studio, and advanced-prompt consumers import their immutable defaults
  directly from `easyuse_anima.prompt.fields`; normal-package and synthetic
  package tests reject the retired names while preserving the exact strings and
  input defaults.
- B-10b11 legacy Extend cleanup: `EasyUseAnimaPromptStudioExtend` is no longer
  a root alias. Its canonical class and frontend type hooks remain unchanged;
  normal-package and synthetic package tests reject the retired root name while
  behavior tests import the canonical class directly. Backend node/display
  mappings and the reviewed workflow fixture continue to omit Extend.
- B-10b12 prompt-data cleanup: the nine audited unsupported aliases for compat
  output tuples, schema/version, and internal nested/output/set helpers are no
  longer root aliases. Canonical prompt-data adapters and services import or
  call the owner directly; normal-package and synthetic package tests reject
  the retired names while preserving the retained prompt-data type, runtime
  helpers, mapped classes, schema values, socket contract, and fallback behavior.
- B-10b13 NAIA client cleanup: the 13 audited unsupported aliases for host/port,
  timeout, resolution bounds, preprocessing metadata, URL/host validation,
  prompt cleanup, and 1MP fitting are no longer root aliases. Canonical client
  and node-adapter consumers import or call the owner directly; normal-package
  and synthetic package tests reject the retired names while preserving
  `LATENT_ALIGN`, response parsing, HTTP posting, runtime binding, mapped class,
  settings, and workflow behavior.
- B-10b14 NAIA resolution cleanup: the 16 audited unsupported aliases for the
  bucket table/default labels, resolution modes, scale/max-long-edge policy,
  snapping, sorting, and bucket fitting are no longer root aliases. Canonical
  resolution and prompt consumers import or call the owner directly;
  normal-package and synthetic package tests reject the retired names while
  preserving five runtime-resolved label/selection seams, bucket contents/order,
  input defaults, mapped classes, settings, and workflow behavior.
- B-10b15 conditioning cleanup: the five audited unsupported aliases for the
  enabled/disabled mode constants, profile choices, and Spectrum old-signature
  warning state/dispatch are no longer root aliases. Canonical conditioning and
  Prompt Data consumers import or call the owner directly; normal-package and
  synthetic package tests reject the retired names while preserving nine
  runtime-resolved conditioning seams, profile/mode values, mapped classes,
  Spectrum fallback, warning-once behavior, and saved-workflow contracts.
- B-10b16 Prompt Advanced cleanup: the 12 audited unsupported aliases for field
  schema metadata, workflow property, legacy Extend slots, return tuples,
  wildcard seed-control normalization, artist override, pane assembly, and
  prompt-data serialization are no longer root aliases. Canonical services and
  adapters consume their owner directly; normal-package and synthetic package
  tests reject the retired names while preserving 22 runtime-resolved Advanced
  seams, exact schema/order/payloads, mapped classes, prompt behavior, and
  saved-workflow contracts.
- B-10b17 Regional cleanup: the 12 audited unsupported aliases for schema/type
  metadata, workflow properties, default config/fields, mask normalization,
  and field prompt assembly are no longer root aliases. Canonical services and
  adapters consume their owner directly; normal-package and synthetic package
  tests reject the retired names while preserving 14 runtime-resolved Regional
  seams, exact serialized strings/payloads, mask/prompt behavior, mapped
  classes, frontend properties, and saved-workflow contracts.
- B-10b18 Artist Mix parsing/config cleanup: 11 audited private helpers for
  token/block/item/group parsing and prompt-data artist config are no longer
  root aliases. Canonical Artist Mix code calls the owner helpers lexically;
  normal-package and synthetic package tests reject the retired names while
  preserving the remaining 42 audited aliases, 25 runtime-resolved seams,
  exact parser/config/tensor/mode behavior, mappings, and workflow contracts.
- B-10b19 Artist Mix mode/constants cleanup: 21 audited metadata-key, mode,
  mode-description, and artist-tag-position constants are no longer root
  aliases. Production adapters already import the canonical owner directly;
  the sole repository root test consumer imports the canonical constants now.
  Normal-package and synthetic package tests reject the retired names while
  preserving the remaining 21 conditioning/tensor aliases, all 25 transitional
  seams, exact values/order/descriptions, mappings, and workflow contracts.
- B-10b20 Artist Mix conditioning/tensor cleanup: the final 21 unsupported
  Artist Mix helpers are no longer root aliases. Canonical code consumes them
  lexically, while the 25 documented transitional seams remain direct aliases.
  Normal-package and synthetic package tests reject the retired names; exact
  tensor math, dtype/device handling, weight normalization, branch/metadata
  behavior, fallback control flow, mappings, and workflow contracts remain
  unchanged. The Artist Mix unsupported group is now removed; the separate
  legacy Wildcard unsupported alias remains outside this lane.
- B-08b2 internal AiO model-variant transition: Spectrum correction/forecast
  model patching and ephemeral model cleanup move to
  `easyuse_anima.aio.model_preparation`. Their four root private names remain
  direct identity aliases so the current sampler/stage/generator callers and
  focused monkeypatch seams preserve call-time behavior. These are internal
  transition surfaces through the B-10 compatibility audit and are not added
  to public package `__all__`.
- B-08c internal AiO sampling transition: latent creation, Comfy and Spectrum
  sampler invocation, backend dispatch, VAE encode/decode, stage sampler
  selection, and highres backend selection move to
  `easyuse_anima.aio.sampling`. Their nine root private names remain direct
  identity aliases so current generator/stage callers and focused monkeypatch
  seams preserve call-time behavior. These are internal transition surfaces
  through the B-10 compatibility audit and are not added to public package
  `__all__`.
- B-08d1 internal AiO preview transition: preview labels and format/event
  constants, path/file-size tagging, event delivery, and temporary WebP/PNG
  fallback saving move to `easyuse_anima.aio.preview`. Their nine root names
  remain direct identity aliases so generator callers and focused monkeypatch
  seams preserve call-time behavior. These are internal transition surfaces
  through the B-10 compatibility audit and are not added to public package
  `__all__`.
- B-08d2 internal AiO output transition: Image Saver hash normalization and
  fetching, LoRA prompt metadata, ComfyUI/Image Saver adapters, and filename
  prefix handling move to `easyuse_anima.aio.output`. Their nine root private
  names remain direct identity aliases so normalization/generator callers and
  focused monkeypatch seams preserve call-time behavior. These are internal
  transition surfaces through the B-10 compatibility audit and are not added
  to public package `__all__`.
- B-08e internal AiO first-pass cache transition: current cache state,
  cache-key generation, clone/reset, and LRU helpers move to
  `easyuse_anima.aio.first_pass_cache`. Their eight root names remain direct
  identity aliases so generator callers, mutable-state rebinding, and focused
  monkeypatch seams preserve call-time behavior. These are internal transition
  surfaces through the B-10 compatibility audit and are not added to public
  package `__all__`. The shared root `_aio_lora_stack_signature` was not part
  of B-08e; B-11c4 now gives it a canonical model-preparation owner while the
  cache key continues resolving the retained root alias at call time.
- B-09a public AiO input-adapter transition: `EasyUseAnimaInput` moves to
  `easyuse_anima.nodes.aio_nodes` and remains a direct root alias, so direct
  imports and the package `NODE_CLASS_MAPPINGS` entry retain class identity.
  Its narrow call-time runtime seam preserves root monkeypatches for resource
  candidates, normalization, stable change keys, schema/version values, and
  prompt-data copying. The adapter does not import `nodes.py`.
- B-09b1 internal AiO orchestration transition: the current-order
  `EasyUseAnimaAIOGenerator.generate` body moves to
  `easyuse_anima.aio.legacy_generation` while the public class and exact method
  signature remain root-owned for the B-09b2 adapter slice. Root retains direct
  private identity aliases for the binder and orchestration function; the
  canonical module imports no root module and resolves every legacy helper,
  constant, and module at its original call site through one resolver slot.
  These aliases are transitional internal seams for B-10 and are not public
  package `__all__` entries.
- B-09b2 public AiO generator-adapter transition: `EasyUseAnimaAIOGenerator`,
  `_easy_use_anima_input_signature`, and `_require_easy_use_anima_input` move to
  `easyuse_anima.nodes.aio_nodes` and remain direct root identity aliases in both
  import modes. `EasyUseAnimaInput` and `EasyUseAnimaAIOGenerator` are the only
  public names in the canonical module `__all__`; the two private aliases remain
  transitional B-10 seams. The existing resolver slot preserves call-time root
  lookup for the settings default, mutable special-seed set, normalization,
  clone/runtime-seed/signature/LoRA/change-key helpers, prompt-data JSON safety,
  and legacy orchestration. The canonical module does not import `nodes.py`.
- Removal gate: 0.5.2 node/workflow fixture, mapping identity, direct import,
  Registry archive closure, consumer evidence, separate breaking-change issue,
  and release note. With no external-consumer evidence, retain these exports.

### `api.py`

- Candidate scope: the route registration compatibility surface. The current
  frontend endpoint URLs and payloads are compatibility contracts, even if
  Python route helpers are not declared as public.
- D-10 moves shared profile repository helpers, AiO profile operations, and
  LoRA profile operations/repair to `easyuse_anima.profiles.repository`,
  `.aio`, and `.lora`. Existing envelope/CAS owners remain `.contract` and
  `.mutation`.
- `api.py` keeps explicit identical aliases for the synchronous profile
  operations called by its handlers. Request parsing, the bounded file-I/O
  adapter, error-to-response mapping, response construction, preview handling,
  and route registration remain root API responsibilities until D-02-D-07.
- Directory, size, mutation, and storage test seams move to their canonical
  owner. The aliases are not promoted into a declared public `api.py`
  `__all__`; D-14 decides the supported root surface after consumer evidence.
- Canonical target: `easyuse_anima.api.router`, requests/responses/errors, and
  feature route modules.
- D-03a moves the translation handler body to a pure canonical factory. Root
  composition passes dynamic callables so the established translation service,
  timeout worker, error response, and test patch seams remain effective.
- D-03b moves the bounded worker implementation and wait/cancel/timeout policy
  to a side-effect-free canonical executor. Root constructs the singleton,
  registers shutdown, and keeps the established worker and timeout patch seams.
- D-04a moves the read-only AiO Torch Compile recommendation handler to a pure
  canonical factory while root keeps diagnostics/recommendation patch seams,
  correlation, route order, and registration composition.
- Removal gate: root entrypoint no longer imports `api.py`; repeated initialize
  registers no duplicate routes; the #165 request/error matrix and 0.5.2 API
  parity pass; actual package import succeeds.

### `api_contract.py`

- Candidate scope: the internal JSON-object parser, typed field validators,
  stable error type, and additive error-payload helper introduced by #165.
- State: D-02 moves the implementation and `api.py` consumer to
  `easyuse_anima.api.requests`, `.responses`, and `.errors`. Root
  `api_contract.py` retains an explicit 12-symbol identity shim; D-14 decides
  whether consumer evidence requires retaining that supported surface after the
  first canonical+shim release.
- Removal gate: the #165 request/error and frontend compatibility matrices pass,
  internal imports are canonical, and the actual Registry package retains
  import closure. If a root shim is retained, ADR-002 identity and N+1 gates
  apply.

### `settings.py`

- D-09 moves 11 module-owned schema/default/key-map containers to
  `easyuse_anima.settings.schema`, two import-time file paths and four public
  file-backed operations to `.repository`, and 22 public projection/resolver
  functions to `.service`.
- The root module lists exactly those 39 module-owned public symbols in
  `__all__` and binds each as the identical canonical object.
- Raw JSON, long-text normalization, Comfy settings discovery/overlay,
  string-conversion, and private resolver helpers remain unsupported
  canonical-owner test seams. Imported filesystem and translation objects are
  not promoted into the root compatibility surface.
- Internal production imports use precise canonical owners. Canonical node and
  prompt modules no longer fall back through the root settings shim.
- D-09 preserves import-time paths, mutable schema-container identity,
  call-time store construction, candidate order, precedence, round-trip,
  clamping, error, and return behavior. It introduces no migration, cache,
  repository singleton, or RuntimeServices lifecycle.
- Removal gate: all internal imports are canonical; 0.5.2 settings and long-text
  fixtures migrate and round-trip; original data survives migration/write
  failure; root/canonical supported-symbol identity passes.

### `storage.py`

- Supported root symbols are `PACKAGE_ROOT`, `PACKAGE_DATA_DIR`,
  `SYSTEM_USER_NAME`, `USER_DATA_DIR`, and `AtomicJsonStore`.
- D-08 moves path discovery to
  `easyuse_anima.infrastructure.filesystem.paths` and durable JSON operations,
  shared path locks, recovery, and rollback to
  `easyuse_anima.infrastructure.filesystem.atomic_json`.
- The root module lists only those supported symbols in `__all__` and binds
  each as the identical canonical object. Imported `os`/`tempfile`, lock
  registries, sentinels, and private path/fsync helpers remain unsupported
  test-only seams and are not re-exported.
- Internal production imports use canonical modules directly. The root shim
  remains shipped for external/legacy imports through the ADR-002 support
  window; release N has not yet been recorded.
- Runtime-config path injection, repository factories, and lock lifecycle are
  E-03 follow-ups and are not part of D-08.
- Removal gate: settings/profile/wildcard consumers are canonical; lock and
  atomic last-known-good behavior remains compatible; Windows path fixtures and
  Registry archive closure pass.

### `autocomplete_index.py`

- D-11a moves the SQLite schema, metadata validation, ranked query, atomic
  rebuild, recovery, and per-index-path locks to
  `easyuse_anima.autocomplete.index`.
- The root module directly re-exports the seven supported names with identical
  object identity. It remains a Registry runtime entry for external and legacy
  imports; production dataset search imports the canonical module.
- Index/cache lifecycle ownership remains an E-05 follow-up. D-11a does not
  alter schema version, ranking, timeout, rebuild, recovery, or lock behavior.

### `autocomplete_dataset.py`

- Confirmed current API consumers use `autocomplete_status`,
  `available_autocomplete_sources`, `classify_prompt_text`,
  `resolve_autocomplete_source`, and `search_autocomplete`.
- D-11b moves source metadata, CSV parsing, immutable snapshots,
  single-flight cache, status, indexed-search orchestration, and exact fallback
  ranking to `easyuse_anima.autocomplete.dataset` and `.search`.
- The root module directly aliases the 13 supported dataset names and
  `search_autocomplete` to the canonical owners. It retains prompt
  classification only because that implementation still imports root
  `anima_prompt`.
- Canonical classification and the final explicit root shim wait for D-13;
  D-11b does not add a canonical-to-root import or G-03 exception.
- Removal gate: ranking/classification/source/result parity, API parity,
  canonical internal imports, public snapshot, and archive closure.

### `wildcard_engine.py`

- Confirmed current consumers include root initialization, node expansion and
  seed constants/helpers, and API list/root helpers.
- D-12a moves immutable `WildcardOption`, `WildcardExpansionBudget`,
  `WildcardExpansionResult`, and their fixed budget constants to
  `easyuse_anima.wildcard.models`.
- D-12b moves root discovery, extra-path resolution, TXT/YAML parsing,
  immutable source metadata, and source scanning to
  `easyuse_anima.wildcard.sources`.
- D-12c moves immutable `_WildcardSnapshot` and stateless
  `_build_wildcard_snapshot` materialization to
  `easyuse_anima.wildcard.snapshot`.
- D-12d moves the five seed-control names, two seed ranges,
  `normalize_seed`, and `next_seed` to `easyuse_anima.wildcard.seed`.
- D-12e moves the four mode constants, three mode/label tuples, mutable alias
  lookup, and two normalization functions to `easyuse_anima.wildcard.mode`.
- D-12f1 changes no production code. It freezes D-12f2 so root keeps eager
  `numpy as np` and its current binding, while direct canonical selector import
  loads no NumPy and non-sequential construction still creates
  `Generator(PCG64(normalized_seed))`.
- D-12f2 moves only `_Selector` under that contract. Root retains direct class
  identity, its NumPy binding, and every expansion caller.
- Root binds the 12 model names, eight supported source names, two private
  snapshot seams, and nine seed-control names directly to canonical objects.
  D-12e adds ten direct mode aliases, including the identical mutable alias
  dictionary. D-12f2 adds the direct private selector alias while preserving
  root eager NumPy. Source verification, snapshot publication/cache/condition/
  single-flight/retry, expansion, enforcement, and diagnostics remain
  root-owned for later D-12 slices and E-06.
- Canonical target for the remaining implementation:
  `easyuse_anima.wildcard` sources/snapshot/expansion modules. Snapshot
  lifecycle/factory/cleanup remains E-06.
- Removal gate: #159/#160 behavior fixtures, seed and expansion parity,
  0.5.2 workflow load/save/reload, root/canonical identity, and archive closure.

### `prompt_translation.py`

- Confirmed current consumers use settings/default normalization, marker
  parsing, translation execution, and the translation error classes.
- Canonical target: `easyuse_anima.translation.contracts`, `markers`, `service`,
  and `providers.google` after #164 behavior is stable.
- D-01 moves the implementation to those canonical owners. The root module
  lists only the reviewed module-owned public symbols in `__all__` and binds
  each as the identical canonical object. Private provider registries, locks,
  cache sentinels, flight state, and the default service are unsupported
  test-only seams and are not re-exported.
- Internal production imports use the canonical modules directly. The root shim
  remains shipped for external/legacy imports through the ADR-002 support
  window; release N has not yet been recorded.
- Removal gate: provider-off imports create no client or optional dependency,
  timeout/cache/error/API parity passes, internal imports are canonical, and
  both paths are present in the actual release archive through the support
  window.

### `anima_prompt/`

- Confirmed current package `__all__`: `CorrectionResult`,
  `KnowledgeBaseNotFound`, `ParsedPrompt`, `PromptKnowledgeBase`, `TagInfo`,
  `TagToken`, `correct_prompt`, `inspect_prompt`, and `load_knowledge_base`.
- Canonical target: `easyuse_anima.prompt.anima` after the #184 Prompt slices
  stabilize.
- Removal gate: Prompt correction/parser/order/knowledge tests use the
  canonical package, supported objects retain identity, current prompt behavior
  fixtures pass, and consumer evidence supports removal. Otherwise retain the
  package shim.

## Evidence and update procedure

For every Move PR that creates or changes a shim:

1. update the relevant entry in this file;
2. list exact supported symbols in `__all__`;
3. record the first published release `N` only after Registry publication;
4. add root/canonical identity and archive-closure evidence;
5. keep compatibility-only tests clearly separated from canonical service
   tests; and
6. do not change `Earliest removal` to a version/date unless the ADR-002 gates
   have evidence and the appropriate breaking-change decision exists.
