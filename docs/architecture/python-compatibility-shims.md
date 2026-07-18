# Python Compatibility Shim Registry

## Registry status

- Inventory baseline: `dev` commit
  `247252a97aba3d0fea3da23e5310dd1eecb8163b`
- Compatibility provenance: package/workflow version 0.5.2
- Policy: [ADR-002](adr-002-compatibility-shims.md)
- Current state: initial inventory; the root implementation modules below have
  not yet been converted to shims

This is an actionable registry, not a removal schedule. `N` means the first
published Registry release containing both a canonical target and its root
shim. `N+1 gate` means no earlier than a later release and only after every
removal gate passes; it does not promise removal in that release.

## Required fields

Every shim entry records:

- **Surface/symbols:** the supported root import path and exact public scope.
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

If a symbol list is not frozen yet, the move owner must inventory actual
consumers and add explicit `__all__` before conversion. New private helpers are
not added to a shim merely because tests import them.

## Initial inventory summary

| Surface | Current role | Canonical target | Owner | Introduced / conversion | Known dependents and evidence | Earliest removal |
| --- | --- | --- | --- | --- | --- | --- |
| Root `__init__.py` exports | Permanent ComfyUI entrypoint, not a shim | root entrypoint plus `easyuse_anima.registration`/`bootstrap` | #184/#185 | Existing 0.5.2 surface; B-11 rewires internals | ComfyUI loader; node contract fixture | Not removable as a package entrypoint |
| `nodes.py` mapped public classes | Current implementation; planned node shim | `easyuse_anima.nodes.*_nodes` | #184 B-11, #188 | Existing 0.5.2 surface; convert in B-11 | Root mappings, workflows, tests, possible external Python imports | No scheduled removal; public breaking-change gate after N+1 at earliest |
| `api.py` route-registration surface | Current implementation; planned API shim | `easyuse_anima.api.router` and `easyuse_anima.api.routes.*` | #165, #186 D-02-D-07 | Existing 0.5.2 surface; convert during D-02-D-07/D-14 | Root entrypoint side-effect import, frontend endpoints, API tests | Unscheduled; N+1 gate and route parity |
| `api_contract.py` request/error helpers | Phase C temporary implementation; D-02 move and D-14 shim decision pending | `easyuse_anima.api.requests`, `responses`, and `errors` | #165, #186 D-02/D-14 | Introduced by #165; convert in D-02 and freeze any required root shim in D-14 | `api.py`, API contract tests, Registry package-closure test | Unscheduled; internal consumers canonical and contract/package parity pass |
| `settings.py` | Current implementation; planned settings shim | `easyuse_anima.settings.*` | #163, #186 D-09 | Existing 0.5.2 surface; convert in D-09/D-14 | `api.py`, `nodes.py`, `wildcard_engine.py`, settings tests | Unscheduled; N+1 gate and settings migration/round-trip |
| `storage.py` | Current implementation; planned filesystem shim | `easyuse_anima.infrastructure.filesystem.*` | #163, #186 D-08 | Existing 0.5.2 surface; convert in D-08/D-14 | `api.py`, `settings.py`, `wildcard_engine.py`, storage/profile tests | Unscheduled; N+1 gate and last-known-good/atomic-write parity |
| `autocomplete_dataset.py` | Current implementation; planned autocomplete shim | `easyuse_anima.autocomplete.*` | #162, #186 D-11 | Existing 0.5.2 surface; convert in D-11/D-14 | `api.py`, autocomplete/frontend API tests | Unscheduled; N+1 gate and result/ranking/API parity |
| `wildcard_engine.py` | Current implementation; planned wildcard shim | `easyuse_anima.wildcard.*` | #184, #186 D-12 | Existing 0.5.2 surface; convert in D-12/D-14 | root entrypoint, `nodes.py`, `api.py`, wildcard/workflow tests | Unscheduled; N+1 gate and seed/expansion/workflow parity |
| `prompt_translation.py` | Current implementation; planned translation shim | `easyuse_anima.translation.*` | #164, #186 D-01 | Existing 0.5.2 surface; convert in D-01/D-14 | `settings.py`, `nodes.py`, `api.py`, `autocomplete_dataset.py`, translation tests | Unscheduled; N+1 gate and provider-off/API parity |
| `anima_prompt/` package | Current implementation; planned package shim | `easyuse_anima.prompt.anima.*` | #184, #186 D-13 | Existing 0.5.2 surface; convert in D-13/D-14 | `nodes.py`, `autocomplete_dataset.py`, prompt tests | Unscheduled; N+1 gate and prompt correction/parser parity |

## Entry details

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
