# Python Feature Error Taxonomy Contract

## Status

- Owner: Issue #563
- Base: `e5e0329cd64afa9894d631f9b6baa6514a81ab48`
- Task: F-02e
- Class: Contract/gate
- Production changes: none
- Fixture: `tests/fixtures/python_feature_error_contract.v1.json`
- Gate: `tests/test_python_feature_error_contract.py`

This contract resolves the final Phase F finding without changing production
inheritance, exceptions, API payloads, node behavior, or public exports. The fixture is
the executable inventory; this document records the decisions and ordered
implementation boundaries.

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

Current profile and translation adapters read status/code/message metadata directly
from feature exceptions. F-02g makes API mapping tables or equivalent injected
adapter callbacks authoritative by exact exception kind and preserved MRO fallback.
The externally observable response remains unchanged:

```text
status
code
message
optional details
request_id
X-Request-ID
```

The existing feature exception metadata is retained as a passive compatibility mirror
during the current support window. Production API adapters must no longer use that
mirror after F-02g. This preserves existing direct Python consumers and root aliases
without leaving HTTP policy authoritative in feature behavior. Removing a mirror is a
later compatibility/removal decision, not Phase F work.

Profile mutation mapping retains the dynamic root monkeypatch seam. Canonical
precondition, identity, and revision errors use exact adapter mappings; a deliberately
patched compatibility error type may continue through the existing injected fallback.
No raw unexpected `ValueError` gains a new mapping, and current redaction/order rules
remain fixed.

Translation adapters continue to map only `PromptTranslationError` instances. Custom
limit messages remain semantic instance messages, while status and code are selected
by the adapter. Cancellation remains a stable 499 response and request cancellation
outside that exception family remains unnormalized.

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
- retain current exception metadata as compatibility mirrors, but prove production
  mappers do not read it;
- do not change Autocomplete fallback, seed behavior, migration behavior, or node
  payloads.

### F-02h — Completion audit

A production-free audit must reconcile every fixture-owned feature error, record zero
unmapped errors, mark the common error row and Phase F complete, and transition Issue
#188 to G-04A READY. Production corrections require a separate task instead of being
hidden in the audit.

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
