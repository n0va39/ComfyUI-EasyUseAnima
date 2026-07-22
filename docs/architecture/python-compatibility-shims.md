# Python Compatibility Shim Registry

## Registry status

- Inventory baseline: `dev` commit
  `3c49e6c02489fa5d467c1a5028bcb2392c47bc83`
- Compatibility provenance: package/workflow version 0.5.2
- Policy: [ADR-002](adr-002-compatibility-shims.md)
- Machine-readable audit:
  [`python_compatibility_surface.v1.json`](../../tests/fixtures/python_compatibility_surface.v1.json)
- Current state: B-10b11 is integrated; B-10b12 in PR #283 removes one audited
  unsupported/test-only prompt-data root-alias group

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
| `api.py` route-registration surface | Current implementation; planned API shim | `easyuse_anima.api.router` and `easyuse_anima.api.routes.*` | #165, #186 D-02-D-07 | Existing 0.5.2 surface; convert during D-02-D-07/D-14 | Root entrypoint side-effect import, frontend endpoints, API tests | Unscheduled; N+1 gate and route parity |
| `api_contract.py` request/error helpers | Phase C temporary implementation; D-02 move and D-14 shim decision pending | `easyuse_anima.api.requests`, `responses`, and `errors` | #165, #186 D-02/D-14 | Introduced by #165; convert in D-02 and freeze any required root shim in D-14 | `api.py`, API contract tests, Registry package-closure test | Unscheduled; internal consumers canonical and contract/package parity pass |
| `settings.py` | Current implementation; planned settings shim | `easyuse_anima.settings.*` | #163, #186 D-09 | Existing 0.5.2 surface; convert in D-09/D-14 | `api.py`, `nodes.py`, `wildcard_engine.py`, settings tests | Unscheduled; N+1 gate and settings migration/round-trip |
| `storage.py` | Current implementation; planned filesystem shim | `easyuse_anima.infrastructure.filesystem.*` | #163, #186 D-08 | Existing 0.5.2 surface; convert in D-08/D-14 | `api.py`, `settings.py`, `wildcard_engine.py`, storage/profile tests | Unscheduled; N+1 gate and last-known-good/atomic-write parity |
| `autocomplete_dataset.py` | Current implementation; planned autocomplete shim | `easyuse_anima.autocomplete.*` | #162, #186 D-11 | Existing 0.5.2 surface; convert in D-11/D-14 | `api.py`, autocomplete/frontend API tests | Unscheduled; N+1 gate and result/ranking/API parity |
| `wildcard_engine.py` | Current implementation; planned wildcard shim | `easyuse_anima.wildcard.*` | #184, #186 D-12 | Existing 0.5.2 surface; convert in D-12/D-14 | root entrypoint, `nodes.py`, `api.py`, wildcard/workflow tests | Unscheduled; N+1 gate and seed/expansion/workflow parity |
| `prompt_translation.py` | Current implementation; planned translation shim | `easyuse_anima.translation.*` | #164, #186 D-01 | Existing 0.5.2 surface; convert in D-01/D-14 | `settings.py`, `nodes.py`, `api.py`, `autocomplete_dataset.py`, translation tests | Unscheduled; N+1 gate and provider-off/API parity |
| `anima_prompt/` package | Current implementation; planned package shim | `easyuse_anima.prompt.anima.*` | #184, #186 D-13 | Existing 0.5.2 surface; convert in D-13/D-14 | `nodes.py`, `autocomplete_dataset.py`, prompt tests | Unscheduled; N+1 gate and prompt correction/parser parity |

## Entry details

### B-10a machine-readable root audit

The versioned fixture records the exact post-B-09b2 surface rather than
inferring public support from spelling or test imports:

- root `__init__.py` permanent entrypoints: 3;
- `nodes.py` preamble implementation imports: 7 (`json`, `logging`, `random`,
  `re`, `ceil`, `sqrt`, and `Any`), excluded from compatibility classification
  by an exact AST allowlist and drift gate;
- `nodes.py` bindings with an `easyuse_anima` canonical target: 369 at the
  B-10b12 PR head, with exact
  relative-package/flat-fallback parity;
- bindings still owned by `anima_prompt`, `settings`, `prompt_translation`, or
  `wildcard_engine`: 27, with the same fallback parity;
- mapped supported public class re-exports: 18;
- unmapped root classes: `EasyUseAnimaSAM3Context` and
  `EasyUseAnimaSAM3Detailer`; the canonical legacy Extend class remains in its
  owner module without a root alias or backend mapping;
- root-owned residual implementation: 41 functions, 2 classes, and 33 assigned
  globals.
- import-time runtime binders: 28 exact top-level `_bind_*_runtime` calls;
- root names reached by those canonical runtime resolvers: 256, including
  literal lookups and binder-owned helper-name/default collections;
- retired private bindings: `_comfy_checkpoint_names`,
  `_EasyUseAnimaAlignedDetailerHook`, and
  `_EasyUseAnimaImpactDetailerDelegate`, plus `_impact_core_module`,
  `_align_up`, `_aligned_size_near_scale`, `_alignment_value`,
  `_image_scale_by_multiple_size`, `_max_long_edge_value`,
  `_normalize_image_scale_options`, `_scale_by_value`, and
  `_clear_aio_first_pass_cache`, plus `WILDCARD_SEED_RANGE_NOTE`, the seven
  B-10b9 SAM3 helpers, the two B-10b10 prompt-default constants, and the
  B-10b11 legacy Extend class root alias, and the nine B-10b12 prompt-data
  aliases; their production
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

The seven preamble imports are implementation dependencies of the remaining
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
  package `__all__`. The shared root `_aio_lora_stack_signature` is not part of
  this move; the canonical cache key resolves it at call time.
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
- Canonical target: `easyuse_anima.api.router`, requests/responses/errors, and
  feature route modules.
- Removal gate: root entrypoint no longer imports `api.py`; repeated initialize
  registers no duplicate routes; the #165 request/error matrix and 0.5.2 API
  parity pass; actual package import succeeds.

### `api_contract.py`

- Candidate scope: the internal JSON-object parser, typed field validators,
  stable error type, and additive error-payload helper introduced by #165.
- State: temporary Phase C root implementation, not a declared public Python
  API. D-02 moves the implementation and `api.py` consumer to
  `easyuse_anima.api.requests`, `responses`, and `errors`; D-14 decides whether
  consumer evidence requires a supported root re-export shim.
- Removal gate: the #165 request/error and frontend compatibility matrices pass,
  internal imports are canonical, and the actual Registry package retains
  import closure. If a root shim is retained, ADR-002 identity and N+1 gates
  apply.

### `settings.py`

- Confirmed current internal consumers use settings load/save/public helpers,
  long-text helpers, autocomplete/NAIA/metadata/translation resolvers, and
  translation defaults/types.
- Canonical target: `easyuse_anima.settings.schema`, `migrations`,
  `repository`, and `service`.
- Removal gate: all internal imports are canonical; 0.5.2 settings and long-text
  fixtures migrate and round-trip; original data survives migration/write
  failure; root/canonical supported-symbol identity passes.

### `storage.py`

- Confirmed candidate symbols: `AtomicJsonStore` and `USER_DATA_DIR`. Private
  path-lock and fsync helpers are not automatically public.
- Canonical target: `easyuse_anima.infrastructure.filesystem.atomic_json`,
  `locks`, and `paths`, with user-path resolution supplied by runtime config.
- Removal gate: settings/profile/wildcard consumers are canonical; lock and
  atomic last-known-good behavior remains compatible; Windows path fixtures and
  Registry archive closure pass.

### `autocomplete_dataset.py`

- Confirmed current API consumers use `autocomplete_status`,
  `available_autocomplete_sources`, `classify_prompt_text`,
  `resolve_autocomplete_source`, and `search_autocomplete`.
- Canonical target: `easyuse_anima.autocomplete` feature modules after #162.
- Removal gate: ranking/classification/source/result parity, API parity,
  canonical internal imports, public snapshot, and archive closure.

### `wildcard_engine.py`

- Confirmed current consumers include root initialization, node expansion and
  seed constants/helpers, and API list/root helpers.
- Canonical target: `easyuse_anima.wildcard` models/sources/snapshot/expansion/
  service modules.
- Removal gate: #159/#160 behavior fixtures, seed and expansion parity,
  0.5.2 workflow load/save/reload, root/canonical identity, and archive closure.

### `prompt_translation.py`

- Confirmed current consumers use settings/default normalization, marker
  parsing, translation execution, and the translation error classes.
- Canonical target: `easyuse_anima.translation.contracts`, `markers`, `service`,
  and `providers.google` after #164 behavior is stable.
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
