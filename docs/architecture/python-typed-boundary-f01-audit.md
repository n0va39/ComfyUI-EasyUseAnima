# F-01 Typed-Boundary Completion Audit

## Status

- Owner: Issue #563
- Base: `789c29075f6a0651bd2da5c9abe6d0619e7cf8b7`
- Class: Contract/gate
- Production changes: none
- Result: Phase F remains open; G-04A is not READY

This audit reuses the current Pyright, import-boundary, API, profile, workflow,
Autocomplete, Wildcard, and AiO schema/migration evidence. The Prompt/Wildcard/
Autocomplete row was re-audited after F-02c merged as PR #571, and the settings,
profile, and workflow row was re-audited after F-02d merged as PR #573. It adds no
second machine-readable inventory because the current deterministic fixtures and
direct owner tests can express every finding below.

## Classification

| Area | Canonical typed owner and evidence | Intentional raw boundary | Classification and exact finding |
| --- | --- | --- | --- |
| Settings, profile, and workflow schema/migration | Profile v2 identity/revision and pure read migration are owned by `easyuse_anima/profiles/contract.py`; the strict Pyright owner is fixed by `tests/fixtures/pyright_baseline.json`. Settings typed values, v1 persisted documents, detection/migration, persistence, and projection are owned by `easyuse_anima/settings/schema.py`, `repository.py`, and `service.py`. Read-only ComfyUI workflow lookup is owned by `easyuse_anima/workflow.py`. Direct evidence is in `tests/test_prompt_corrector.py`, `tests/test_autocomplete_locale_settings.py`, `tests/test_profile_contract.py`, `tests/test_lora_profiles.py`, `tests/test_aio_profiles.py`, `tests/test_api_contract.py`, and `tests/test_node_contracts.py`. | Settings accept legacy flat ordinary mappings and raw long-text mappings only at pure read-migration boundaries. Profile payload mappings preserve legacy and future fields at the persisted JSON migration boundary. `_get_workflow_node` accepts dynamic host `extra_pnginfo` and returns a raw workflow node only at the ComfyUI adapter boundary. | **complete.** F-02d adds typed normalized settings values, strict v1 detection, and pure legacy/raw-to-v1 reads while new ordinary, long-text, and first-run initialization writes use the v1 envelope. Existing settings payloads and profile/workflow compatibility boundaries remain unchanged. |
| API request/result/error | `easyuse_anima/api/requests.py` validates JSON-object bodies and produces typed scalar fields; `easyuse_anima/api/errors.py` owns `ApiContractError`; `easyuse_anima/api/responses.py` owns the stable error envelope and request correlation. `tests/test_api_contract_compatibility.py` and the direct route classes in `tests/test_api_contract.py` freeze the behavior. | Request bodies and success/error dictionaries exist at the JSON serialization adapter. Profile and settings sub-objects remain mappings only while they are validated or handed to their persisted-schema boundary. | **intentional adapter/migration boundary.** Malformed/body/schema/conflict/not-found mappings and request-id correlation are typed or tested before feature calls; raw response dictionaries do not become feature-service state. |
| Prompt, Wildcard, and Autocomplete | Prompt correction owns `TagInfo`, `TagToken`, `ParsedPrompt`, and `CorrectionResult` in `easyuse_anima/prompt/anima/models.py`. `easyuse_anima/prompt/contracts.py` owns the `PromptField` family plus canonical `PromptData` nested/output contracts and the feature-side `PromptDataRead` mapping. Wildcard owns `WildcardOption`, `WildcardExpansionBudget`, and `WildcardExpansionResult` in `easyuse_anima/wildcard/models.py`. Autocomplete source/status/search/classification payloads are owned by `easyuse_anima/autocomplete/contracts.py`. Direct evidence is in the Prompt, Regional, AiO-conditioning, Wildcard, Autocomplete, Pyright, and analyzer owner tests. | Prompt Data JSON accepts old layouts, malformed nested values, and future keys at the workflow/node adapter boundary. The legacy Extend adapter intentionally omits optional `pin`, and legacy Regional fallback may omit optional `pin`/`collapsed`; Wildcard and Autocomplete payload dictionaries are serialized by API adapters after typed feature results. | **complete.** F-02a through F-02c type the Autocomplete results, shared Prompt field family, canonical Prompt Data output, and feature-side read mapping. Raw workflow/node JSON stays at the intentional adapter/migration boundary and no untyped Prompt feature-state leak remains. |
| AiO config/request/state/result | `AIOGenerationConfig` and its section dataclasses are owned by `easyuse_anima/aio/generation_settings.py` and adjacent strict generation modules. `GenerationRequest`, `GenerationState`, and `GenerationStage` are owned by `easyuse_anima/aio/generation_pipeline.py`; version detection and pure v1-to-v4 migration are owned by `generation_migrations.py`. Evidence is in the v1-v4 schema/surface fixtures and `tests/test_aio_schema_contract.py`, `tests/test_aio_generation_settings.py`, and `tests/test_aio_generation_migrations.py`. | `Mapping[str, object]` is retained only for JSON freeze/thaw, unknown-field preservation, host capability maps, prompt/workflow context, and final ComfyUI result serialization. Tensor/model values remain `object` at host boundaries. | **complete.** Normalized settings enter the generation pipeline as a typed config and typed request/state objects; strict per-file Pyright directives cover the generation contract modules. |
| Node adapter raw input/output conversion | `easyuse_anima/nodes/aio_nodes.py`, `prompt_nodes.py`, and `wildcard_nodes.py` convert ComfyUI inputs into the typed AiO, Prompt, and Wildcard owners before feature work. `tests/test_node_contracts.py` and the 0.5.2 node/workflow fixtures freeze the public socket and result shapes. | Dynamic ComfyUI objects, tensor/model values, workflow metadata, input dictionaries, UI dictionaries, and output tuples are host adapter values. | **intentional adapter/migration boundary.** Their dynamic shape is not feature-service typing debt and no broad `Any` removal is justified. |
| Common feature error taxonomy and adapter mappings | Existing concrete errors include `ProfileContractError`, `ProfileMutationError`, `InvalidProfileDataError`, `AutocompleteIndexUnavailable`, `KnowledgeBaseNotFound`, `AIOGenerationMigrationError`, and API-only `ApiContractError`. Their current behavior is covered by profile, Autocomplete, AiO migration, and API tests. | `ApiContractError` is allowed to carry HTTP status/code because it is an API request-adapter error. Node adapters may translate feature errors to the existing host-visible `RuntimeError` or UI status at the final adapter. | **exact F-02 follow-up required.** The documented `EasyUseAnimaError` category hierarchy does not exist, feature errors have no shared category base, and `ProfileMutationError` currently owns HTTP status alongside feature conflict meaning. Category-to-API/node mapping is therefore not a common tested contract. |

The current Pyright baseline remains valid rather than being rewritten: the global
package stays on `basic`, the reviewed profile contract/mutation group is strict,
and the AiO generation contract modules use existing file-local strict directives.
The audit does not turn unrelated Prompt diagnostics into an annotation-cleanup
project.

## G-04A handoff surface

G-04A should snapshot these supported schema/result/error surfaces after the
selected F-02 row is complete:

- public settings projection and long-text settings response envelopes;
- profile v2 envelope, profile list item, mutation result, and legacy v1 additive
  read view;
- API error envelope (`status`, `code`, `message`, optional `details`, and
  `request_id`) plus `X-Request-ID` correlation;
- Prompt correction models and the serialized Prompt Data/Advanced field shapes;
- Wildcard expansion result plus list/source-signature API payloads;
- Autocomplete source/status/search/classification payloads owned by the F-02a
  canonical typed result contracts;
- AiO generation settings v4, `AIOGenerationConfig`, `GenerationRequest`,
  `GenerationState`, and final node/API serialization shapes;
- common feature error categories only after their adapter mapping follow-up is
  complete.

Root shims, deprecation warnings, telemetry, release metadata, tags, and Registry
state are not part of this handoff.

## F-02a completion re-audit

F-02a merged as PR #566 at `3a306498325c48126325aadc6d31665acf3517b4`.
Its final candidate passed the 1,435-test official full gate, Pyright/import checks,
frontend checks, and `git diff --check`; package/live were not triggered. The runtime
port and core methods now use canonical Autocomplete payload contracts, while the API
adapter preserves the exact dictionaries, redaction, future-key seam, and public
exports. Autocomplete is therefore **complete** and Wildcard remains **complete**.

## F-02b completion re-audit

F-02b merged as PR #569 at `4cf0c82ee459d37e67fa0b8d7b80cd162e111658`.
Its final candidate passed 1,438 Python tests, 120-file frontend validation,
Pyright/import-boundary checks, and `git diff --check`; package/live were not
triggered. The shared Prompt field family now crosses Advanced, Regional, AiO,
wildcard, translation, and artist-mix consumers without changing runtime
dictionaries. The legacy optional-key forms remain intentional workflow adapters.

## F-02c completion re-audit

F-02c merged as PR #571 at `789c29075f6a0651bd2da5c9abe6d0619e7cf8b7`.
Its final candidate passed 1,439 Python tests, 120-file frontend validation,
Pyright/import-boundary checks, and `git diff --check`; package/live were not
triggered. Canonical Prompt Data builders and feature-side reads now use the shared
typed contracts. Legacy, future, and malformed workflow/node JSON remains raw only at
the intentional adapter boundary. The Prompt/Wildcard/Autocomplete row is therefore
**complete**.

## F-02d completion re-audit

F-02d merged as PR #573 at `e9640c4db951939173ff5ffb8d54472795599383`.
Its final candidate passed 1,442 Python tests, 120-file frontend validation,
Pyright/import-boundary checks, and `git diff --check`; package/live were not
triggered. Ordinary settings and long-text settings now share typed normalized values,
strict v1 persisted-document detection, and pure accepted legacy/raw-to-v1 reads. New
ordinary, long-text, and first-run initialization writes use v1 envelopes. Public/API
payloads, defaults, aliases, Comfy overlay precedence, unknown-key behavior, atomic
locking, and root identities remain unchanged. Profile future-field preservation and
raw ComfyUI workflow lookup remain intentional migration/adapter boundaries. The
settings/profile/workflow row is therefore **complete**.

## F-02e selected contract task

Common feature error taxonomy is the only remaining Phase F finding. The first unit is
a production-free executable Contract so the shared categories, built-in exception
compatibility, and adapter mappings are fixed before any cross-feature inheritance or
HTTP-metadata move.

```text
Task ID: F-02e common feature error taxonomy contract
Owner Issue: #563
Primary class: CONTRACT/GATE; production-free
Base SHA: latest origin/dev after this completion re-audit merges
Goal: define one machine-readable contract for the documented `EasyUseAnimaError`
      hierarchy; classify every current feature error; freeze built-in exception
      compatibility plus exact API/node status, code, message, details, redaction,
      and request-correlation behavior; emit the smallest implementation card(s).
Prerequisites: merged F-02d and this settings-row completion re-audit
Allowed files:
  docs/architecture/python-feature-error-taxonomy-contract.md
  docs/architecture/python-typed-boundary-f01-audit.md
  docs/architecture/post-phase-e-maintenance-roadmap.md
  docs/architecture/README.md
  docs/development/README.md
  tests/fixtures/python_feature_error_contract.v1.json
  tests/test_python_feature_error_contract.py
  tests/test_python_package_skeleton.py only if needed to freeze the planned
    canonical private/public surface; no production files
Required inventory:
  profile contract/repository/mutation errors
  Autocomplete index unavailable
  Prompt knowledge-base compatibility error
  AiO generation migration error
  translation contract errors
  seed contract/identity/reservation errors
  API-only ApiContractError and direct API/node mappers
Forbidden changes: production inheritance or behavior, status/code/message/details,
  public/root exports, exception construction/catch order, broad error redesign,
  migration/storage semantics, Any cleanup, ignore additions
Preserved invariants: exact concrete exception identity and built-in catch
  compatibility; profile dynamic monkeypatch seams; translation and profile HTTP
  responses; Autocomplete fallback diagnostics; seed conflict/capacity behavior;
  AiO migration messages; Prompt compatibility imports; request correlation/redaction
Focused tests and purpose:
  new taxonomy contract owner — category/inheritance/mapping completeness
  direct profile and translation API error owners — frozen adapter mapping evidence
  direct Autocomplete/AiO/seed/Prompt error owners — concrete behavior evidence
  tests.test_pyright_baseline, package skeleton, analyzer, and import-boundary owners
Promotion gates: changed-file syntax/static, exact direct focused targets,
  git diff --check, official full once on the final test/tool SHA; no package/live
Stop conditions: direct evidence cannot select one inheritance/mapping design while
  preserving built-in and public identity compatibility; a new public root export,
  API payload change, or feature behavior change is required
Next task: one cohesive implementation if the contract proves one safe inheritance
  and adapter cutover; otherwise the smallest ordered implementation slices; then
  re-audit the error row and mark Phase F complete before G-04A
```

## F-02e contract decision and selected next task

F-02e fixes the production-free executable contract in
[`python-feature-error-taxonomy-contract.md`](python-feature-error-taxonomy-contract.md)
and `tests/fixtures/python_feature_error_contract.v1.json`. The inventory covers all
24 current feature errors across profile, Autocomplete, Prompt knowledge, AiO
migration, translation, and seed owners. `ApiContractError` remains API-only and the
private `_InvalidAutocompleteIndex` remains internal repair control flow.

The contract selects the documented seven-category hierarchy in
`easyuse_anima/errors.py`, no root exports, in-place concrete classes, and additive
multiple inheritance that preserves every current `ValueError`, `RuntimeError`, and
`FileNotFoundError` catch. HTTP mappings become API-authoritative in a later adapter
slice; current exception metadata remains a passive compatibility mirror rather than
being removed during Phase F.

The ordered implementation is:

```text
READY F-02f canonical categories and additive feature inheritance
  -> F-02g authoritative profile/translation API mappings
  -> F-02h production-free error-row and Phase F completion audit
  -> G-04A
```

F-02f is the next task. Its complete task card is in
`python-feature-error-taxonomy-contract.md`. It must not perform the F-02g adapter
cutover, change any exception constructor/attribute/message, add a root export, or
change feature/API/node behavior.
