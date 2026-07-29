# F-01 Typed-Boundary Completion Audit

## Status

- Owner: Issue #563
- Base: `bade01e36146456e163341998ab1a7a19a4ae0b3`
- Class: Contract/gate
- Production changes: none
- Result: Phase F remains open; G-04A is not READY

This audit reuses the current Pyright, import-boundary, API, profile, workflow,
Autocomplete, Wildcard, and AiO schema/migration evidence. It adds no second
machine-readable inventory because the current deterministic fixtures and direct
owner tests can express every finding below.

## Classification

| Area | Canonical typed owner and evidence | Intentional raw boundary | Classification and exact finding |
| --- | --- | --- | --- |
| Settings, profile, and workflow schema/migration | Profile v2 identity/revision and pure read migration are owned by `easyuse_anima/profiles/contract.py`; the strict Pyright owner is fixed by `tests/fixtures/pyright_baseline.json`. Settings persistence/projection is owned by `easyuse_anima/settings/schema.py`, `repository.py`, and `service.py`. Read-only ComfyUI workflow lookup is owned by `easyuse_anima/workflow.py`. Direct evidence is in `tests/test_profile_contract.py`, `tests/test_lora_profiles.py`, `tests/test_aio_profiles.py`, `tests/test_api_contract.py`, and `tests/test_node_contracts.py`. | Profile payload mappings preserve legacy and future fields at the persisted JSON migration boundary. `_get_workflow_node` accepts dynamic host `extra_pnginfo` and returns a raw workflow node only at the ComfyUI adapter boundary. | **exact F-02 follow-up required.** Profile and workflow boundaries are complete or intentional, but ordinary settings have no version detection, pure migration sequence, or typed post-normalization model. Long-text settings write a v1 envelope, yet their normalized value and the settings service still cross feature code as unparameterized dictionaries. |
| API request/result/error | `easyuse_anima/api/requests.py` validates JSON-object bodies and produces typed scalar fields; `easyuse_anima/api/errors.py` owns `ApiContractError`; `easyuse_anima/api/responses.py` owns the stable error envelope and request correlation. `tests/test_api_contract_compatibility.py` and the direct route classes in `tests/test_api_contract.py` freeze the behavior. | Request bodies and success/error dictionaries exist at the JSON serialization adapter. Profile and settings sub-objects remain mappings only while they are validated or handed to their persisted-schema boundary. | **intentional adapter/migration boundary.** Malformed/body/schema/conflict/not-found mappings and request-id correlation are typed or tested before feature calls; raw response dictionaries do not become feature-service state. |
| Prompt, Wildcard, and Autocomplete | Prompt correction owns `TagInfo`, `TagToken`, `ParsedPrompt`, and `CorrectionResult` in `easyuse_anima/prompt/anima/models.py`. Wildcard owns `WildcardOption`, `WildcardExpansionBudget`, and `WildcardExpansionResult` in `easyuse_anima/wildcard/models.py`. Autocomplete owns `AutocompleteEntry` and immutable snapshot/index records. Direct evidence is in `tests/test_prompt_corrector.py`, `tests/test_wildcards.py`, `tests/test_autocomplete_service.py`, and the existing Autocomplete/Wildcard runtime fixtures. | Prompt data and Advanced field JSON accept old workflow layouts and future keys at their workflow migration boundary. Wildcard status/signature and Autocomplete payload dictionaries are serialized by API adapters. | **exact F-02 follow-up required.** Wildcard and the core ANIMA correction result are complete, but `AutocompletePort` and its service/core methods expose unparameterized result dictionaries across the runtime feature port. Normalized Prompt Studio Advanced fields and prompt-data mappings also continue through feature logic as raw dictionaries after parsing. |
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
- Autocomplete source/status/search/classification payloads after F-02a assigns
  canonical typed result contracts;
- AiO generation settings v4, `AIOGenerationConfig`, `GenerationRequest`,
  `GenerationState`, and final node/API serialization shapes;
- common feature error categories only after their adapter mapping follow-up is
  complete.

Root shims, deprecation warnings, telemetry, release metadata, tags, and Registry
state are not part of this handoff.

## Selected next task: F-02a

Only the smallest confirmed leak is selected now. The settings typed migration,
Prompt workflow models, and common error taxonomy remain audit findings and are not
silently combined into this task.

```text
Task ID: F-02a Autocomplete typed result contracts
Owner Issue: #563
Primary class: CONTRACT
Base SHA: latest origin/dev after F-01 merges
Goal: define canonical TypedDict result contracts for Autocomplete source/status,
      search entry/result, and classification token/result payloads; apply them to
      the Autocomplete runtime port, service, dataset, search, classification, and
      API redaction adapter without changing any runtime dictionary.
Prerequisites: merged F-01 audit; current Autocomplete runtime contract remains valid
Allowed production files:
  easyuse_anima/autocomplete/contracts.py
  easyuse_anima/autocomplete/ports.py
  easyuse_anima/autocomplete/service.py
  easyuse_anima/autocomplete/dataset.py
  easyuse_anima/autocomplete/search.py
  easyuse_anima/autocomplete/classification.py
  easyuse_anima/api/routes/autocomplete.py
Allowed test/config files:
  tests/test_autocomplete_service.py
  tests/test_prompt_corrector.py
  tests/test_api_contract.py
  tests/test_python_autocomplete_runtime_contract.py
  tests/test_pyright_baseline.py
  pyrightconfig.json and tests/fixtures/pyright_baseline.json only if the exact
  touched owners are strict-clean and are deliberately enrolled without new debt
Forbidden changes: payload keys/order/values, path redaction, CSV/index behavior,
  runtime owner identity, root/canonical exports, request parsing, broad Any cleanup,
  ignore additions, settings/Prompt/error work
Preserved invariants: source selection, exact result/status/classification shapes,
  missing/locked/corrupt index fallback, request limits, runtime port composition,
  root signatures and identities
Focused tests and purpose:
  tests.test_autocomplete_service — runtime port uses the same snapshot/index owners
  tests.test_prompt_corrector.AutocompleteDatasetTests — source/status/search/classify
    payload values remain exact
  tests.test_api_contract.ApiAutocompleteRouteTests — redaction and API shapes remain exact
  tests.test_python_autocomplete_runtime_contract — owner/import/runtime fixture remains exact
  tests.test_pyright_baseline plus the current quality gate — no new baseline or strict debt
Promotion gates: changed-file syntax/static, focused tests, import boundary,
  git diff --check, official full once on the final test/config candidate; no package/live
Stop conditions: a runtime payload conversion, public export, root-shim change,
  schema behavior change, ignore, or cross-feature contract is required
Next task: re-audit the Prompt/Wildcard/Autocomplete row; do not start G-04A while
  any Phase F follow-up row remains
```
