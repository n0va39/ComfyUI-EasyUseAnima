# Python Feature Error Taxonomy Contract

## Status

- Owner: Issue #563
- Contract base: `e5e0329cd64afa9894d631f9b6baa6514a81ab48`
- F-02f implementation base: `878a86f739a37a000a56b9e76ee2179aa86271f1`
- F-02g implementation base: `d5e6512c110b2ae6654e57013a32dff39944de5a`
- F-02h audit base: `d618bb705f9ec28f89fdbce8ba80a94847932c92`
- Status: F-02e through F-02h complete; Phase F complete
- Current class: Contract/gate completion audit
- Production changes: F-02f inheritance plus the F-02g API-adapter cutover only
- Fixture: `tests/fixtures/python_feature_error_contract.v1.json`
- Gate: `tests/test_python_feature_error_contract.py`

This contract resolves the final Phase F finding in ordered slices. F-02f implemented
the categories and additive inheritance without changing concrete exception identity,
API payloads, node behavior, or public exports. F-02g completed the API-authority
cutover with the named compatibility seams below. The fixture is the executable
inventory, and F-02h records zero unmapped errors and closes Phase F.

## Canonical categories

The canonical owner will be `easyuse_anima/errors.py` with one explicit module
`__all__` and no root-package export:

```text
EasyUseAnimaError
|-- ValidationError
|-- ConflictError
|-- NotFoundError
|-- CapabilityUnavailableError
|-- UpstreamTimeoutError
`-- StorageError
```

The category classes contain no HTTP status, API code, JSON details, ComfyUI UI
payload, or feature-specific default message. They are semantic catch categories.
Concrete exceptions remain defined in their current feature modules so their class
object, `__module__`, `__name__`, feature-specific subclass relation, constructor, and
export identity do not move.

F-02f adds category ancestry with compatibility-preserving multiple inheritance.
Every existing `ValueError`, `RuntimeError`, or `FileNotFoundError` catch must continue
to match. Category classes therefore do not replace built-in ancestry.

## Current inventory and target category

| Feature family | Current concrete errors | Target category | Adapter disposition |
| --- | --- | --- | --- |
| Profile schema/storage | `ProfileContractError`, `InvalidProfileDataError` | `ValidationError` | contract failures convert before the API; stored-data failures keep the exact 422 mapping |
| Profile mutation | `ProfileMutationError`; precondition, identity, and revision subclasses | conflict base; precondition adds `ValidationError`; identity/revision add `ConflictError` | exact 428/409 mappings remain API-owned targets |
| Autocomplete index | `AutocompleteIndexUnavailable` | `CapabilityUnavailableError` | still converts to existing typed fallback diagnostics, not HTTP |
| Prompt knowledge compatibility | `KnowledgeBaseNotFound` | `NotFoundError` | remains a `FileNotFoundError`-compatible import surface |
| AiO generation migration | `AIOGenerationMigrationError` | `ValidationError` | still propagates with the same migration messages |
| Seed request/identity | `SeedReservationContractError`, `SeedExecutionIdentityError` | `ValidationError` | current node/queue propagation remains |
| Seed service | service base, conflict, and capacity errors | root, `ConflictError`, and `CapabilityUnavailableError` | current reservation behavior and catches remain |
| Translation limits | limit base and marker count/size/total errors | `ValidationError` | exact 413 codes/messages remain |
| Translation availability | provider unavailable, timeout, and busy | capability, upstream-timeout, and conflict categories | exact 503/504 mappings remain |
| Translation general | base, cancelled, and upstream errors | `EasyUseAnimaError` | exact 500/499/502 mappings remain |

`StorageError` has no current concrete assignment. It remains part of the documented
taxonomy for a future real storage error; F-02f must not reclassify invalid profile
data or invent a new storage behavior merely to populate every category.

`ApiContractError` remains an API request-adapter error and does not inherit the
feature taxonomy. `_InvalidAutocompleteIndex` remains private repair control flow and
does not cross a feature boundary.

## HTTP mapping authority and compatibility

F-02g makes API mapping tables authoritative for concrete status, code, and default
message by exact exception kind and ordered MRO fallback. The externally observable
response remains unchanged:

```text
status
code
message
optional details
request_id
X-Request-ID
```

The existing fixture-owned concrete feature exception status/code/message metadata is
retained as a passive compatibility mirror during the current support window, but its
fixed mappings do not read it after F-02g. Removing that mirror or either named dynamic
compatibility seam is a later compatibility decision, not Phase F work.

The focused F-02g PRO review and final full gate found that the original absolute
no-metadata-read wording conflicted with three preserved contracts. Concrete profile
errors store their dynamic `profile` and `fields` values only in `details`; the generic
or root-injected `ProfileMutationError` seam deliberately supplies arbitrary
status/code/message/details; and the public root `PromptTranslationError` base supports
unregistered derived types whose status/code/message were already mapped dynamically.
The corrected invariant therefore names these adapter inputs instead of calling them
passive mirrors:

- concrete profile `details` remains semantic instance data read by the adapter;
- generic or injected `ProfileMutationError` status/code/message/details remains a
  dynamic-compatibility adapter input;
- unregistered or root-derived `PromptTranslationError` status/code/message remains a
  dynamic-compatibility adapter input after known concrete and exact-base resolution.

This exception does not return concrete HTTP policy to feature behavior: all known
concrete profile status/code/default-message values still come from the API table.

Profile mutation mapping retains the dynamic root monkeypatch seam. Canonical
precondition, identity, and revision errors use exact adapter mappings plus their
semantic details; a deliberately patched compatibility error type continues through
the existing injected fallback. No raw unexpected `ValueError` gains a new mapping,
and current redaction/order rules remain fixed.

Translation adapters continue to map only `PromptTranslationError` instances. Known
fixture-owned concrete kinds and their descendants use the ordered API table, and the
exact canonical base uses its 500 mapping. Custom message text remains semantic
instance data. An unregistered or root-derived subclass that reaches only the base
fallback retains its status/code/message as a named dynamic-compatibility input; this
preserves the existing public root subclass contract without returning known concrete
HTTP policy to feature behavior. Cancellation remains a stable 499 response and
request cancellation outside that exception family remains unnormalized.

## Ordered implementation

### F-02f — Category inheritance

One additive Contract implementation:

- add `easyuse_anima/errors.py` with the seven category classes and explicit
  `__all__`;
- add category ancestry to every fixture-owned feature exception in place;
- preserve current built-in catches, feature-specific subclass relations,
  constructors, attributes, messages, details, reasons, and exports;
- add no root export and change no API/node adapter behavior.

### F-02g — Authoritative API adapter mapping

One adapter cutover after F-02f:

- make profile and translation API mappings authoritative outside feature behavior;
- preserve exact status/code/message/details, request correlation, redaction, catch
  order, and dynamic profile dependency seams;
- prove concrete status/code/default-message mappings do not read their compatibility
  mirrors while preserving the explicitly named semantic/dynamic adapter inputs;
- do not change Autocomplete fallback, seed behavior, migration behavior, or node
  payloads.

## F-02f completion

F-02f is complete. `easyuse_anima/errors.py` owns the seven categories with an
explicit module `__all__` and no root export. All 24 fixture-owned feature errors keep
their original module, name, concrete object identity, feature-specific subclass
relations, constructor/metadata/message behavior, and built-in exception catches while
also inheriting the selected semantic category. F-02g changes only API mapping
authority; those feature contracts remain unchanged.

### F-02h — Completion audit

The production-free audit at `d618bb705f9ec28f89fdbce8ba80a94847932c92`
reconciles 11 owner modules into 24 fixture-owned feature errors and two explicit
adapter/private exclusions. All 15 HTTP errors have one recorded API mapping, all
feature errors have one canonical category, and the executable inventory reports zero
unmapped errors. No production correction is required.

The common feature-error row and Phase F are complete. Issue #188 / G-04A is the next
READY task.

## F-02f task card

```text
Task ID: F-02f common category inheritance
Owner Issue: #563
Primary class: CONTRACT
Base SHA: latest origin/dev after F-02e merges
Goal: add the canonical feature-error categories and additive category inheritance to
      every fixture-owned concrete feature error without changing behavior or identity.
Allowed production:
  easyuse_anima/errors.py
  easyuse_anima/profiles/contract.py
  easyuse_anima/profiles/repository.py
  easyuse_anima/profiles/mutation.py
  easyuse_anima/autocomplete/index.py
  easyuse_anima/prompt/anima/knowledge.py
  easyuse_anima/aio/generation_migrations.py
  easyuse_anima/translation/contracts.py
  easyuse_anima/seed/reservation.py
  easyuse_anima/seed/execution_identity.py
  easyuse_anima/seed/service.py
Allowed tests/config/docs:
  tests/test_python_feature_error_contract.py
  tests/fixtures/python_feature_error_contract.v1.json
  direct profile/Autocomplete/Prompt/AiO/translation/seed error owners
  tests/test_python_package_skeleton.py
  tests/test_pyright_baseline.py
  tests/test_python_backend_analyzer.py
  tests/fixtures/python_backend_baseline.json only as generated analyzer evidence
  import-boundary owners and current queue/audit docs
Forbidden: API mapper authority cutover, exception metadata/constructor/message change,
  public root export, behavior/migration/storage changes, broad error cleanup, Any
  cleanup, ignore addition
Preserve: concrete class module/name/object identity, feature-specific base graph,
  ValueError/RuntimeError/FileNotFoundError catches, all current exports and root
  aliases, profile/translation HTTP payloads, profile dynamic seam, Autocomplete
  diagnostics, AiO messages, seed behavior
Focused: new taxonomy contract; direct profile, translation, Autocomplete, AiO, seed,
  Prompt compatibility owners; package skeleton; Pyright; analyzer; import boundary;
  changed-file syntax/static; git diff --check
Promotion: official full exactly once on final production/test/tool SHA; no package/live
Stop: MRO conflict, public/root export change, concrete identity/catch change, API or
  feature behavior change, or canonical-to-root import is required
Next: F-02g adapter authority cutover only
```

## F-02g task card

```text
Task ID: F-02g authoritative profile/translation API mappings
Owner Issue: #563
Primary class: ADAPTER
Base SHA: latest origin/dev after F-02f merges
Goal: make canonical API adapters authoritative for every fixture-owned concrete
      profile and translation status/code/default-message mapping without changing any
      response or feature behavior, while retaining the named dynamic profile seam.
Allowed production:
  api.py
  easyuse_anima/bootstrap.py
  easyuse_anima/api/responses.py
  easyuse_anima/api/routes/translation.py
Allowed tests/config/docs:
  tests/test_python_feature_error_contract.py
  tests/fixtures/python_feature_error_contract.v1.json
  tests/test_api_contract.py
  tests/test_prompt_translation_api.py
  tests/test_python_translation_runtime_contract.py
  direct bootstrap/package/Pyright/analyzer/import owners
  tests/fixtures/python_backend_baseline.json only as generated analyzer evidence
  current queue/audit docs
Forbidden: feature exception or category changes, exception metadata removal, root
  alias/export changes, route/runtime lifecycle changes, Autocomplete/seed/migration/
  node behavior changes, broad error cleanup, Any cleanup, ignore addition
Preserve: exact profile/translation status/code/message/details, request correlation,
  redaction and catch order, profile details as semantic adapter input, arbitrary
  dynamic ProfileMutationError status/code/message/details dependency seam, concrete
  exception identity and compatibility metadata, unregistered or root-derived
  PromptTranslationError status/code/message dependency seam, translation worker
  identity, route identity/order/signature/registration, repeated initialize behavior
Focused: taxonomy authority contract; direct profile error response and Prompt
  translation API/runtime owners; bootstrap/package; Pyright; analyzer; import boundary;
  changed-file syntax/static; git diff --check
Promotion: official full exactly once on final production/test/tool SHA; no package/live
Stop: a fixed concrete mapping still requires feature-owned status/code/message,
  exact profile details cannot use the existing semantic details input, a canonical
  adapter must import root api.py, exception metadata/payload/identity must change, or
  route/runtime lifecycle behavior must change
Next: F-02h production-free completion audit only
```

### F-02g focused PRO contract correction

The original requirements could not all hold simultaneously. With an exception as the
only mapper input, removing every metadata read loses dynamic concrete profile details,
the arbitrary generic/root-monkeypatched profile payload, and the already-supported
public root-derived translation mapping. Adding new semantic feature fields or a
registration API would cross the forbidden feature/public boundary.

Only two material designs remained:

1. A pure static table could remove every read but would change profile payloads or
   either dynamic seam.
2. Static concrete tables plus the named compatibility fallbacks preserve behavior and
   keep fixture-owned concrete HTTP policy API-owned.

F-02g selects the second design. The invariant changes from "production reads no
feature metadata" to "production reads no fixture-owned concrete
status/code/default-message compatibility mirror; profile semantic details,
translation message text, generic or injected `ProfileMutationError` dynamic fields,
and unregistered or root-derived `PromptTranslationError` dynamic fields are explicit
adapter inputs." No feature exception, constructor, attribute, payload, root alias, or
lifecycle changes.

## Validation and stop policy

F-02e runs the new contract owner, direct profile and translation API owners, direct
Autocomplete/AiO/seed/Prompt owners, package/import/analyzer/Pyright gates,
`git diff --check`, and official full once on its final test/fixture SHA. Package/live
are not triggered.

No additional PRO review is required for the inheritance contract: the documented
hierarchy, exact built-in catches, identity rules, and API compatibility policy select
one additive design. Stop and request focused architecture review only if F-02f proves
an actual MRO/identity conflict or F-02g cannot preserve both adapter authority and the
dynamic profile seam.
