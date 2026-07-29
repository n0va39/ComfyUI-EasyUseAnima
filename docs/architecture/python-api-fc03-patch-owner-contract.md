# FC-03 Root API Patch-Owner Compatibility Contract

## Status and authority

- Status: FC-03A and FC-03B complete; FC-04A is next after this Move merges.
- Owner: Issue #593.
- Baseline: `e6f509879054854a3dec49eae29d44ca5bd98dc6`.
- Parent evidence:
  [`python-api-papi01-e09-lifecycle-gate.md`](python-api-papi01-e09-lifecycle-gate.md),
  [`python-runtime-e09-lifecycle-contract.md`](python-runtime-e09-lifecycle-contract.md),
  and [`backend-final-convergence-roadmap.md`](backend-final-convergence-roadmap.md).
- Type: production-free compatibility Contract.

P-API-01 retained root `api.py` because its handlers and registrar deliberately
observed root module globals at call time. FC-03A satisfies that audit's first
revisit event: the observation cells move before the application moves. This
Contract changes the supported patch owner, not route or lifecycle behavior.

## 1. Decision

FC-03B introduces the private canonical owner
`easyuse_anima.api.dependencies.ApiApplicationDependencies` and one exact
process-lifetime bundle identity.

```text
easyuse_anima.api.dependencies
  -> defines import-pure private dependency bundle types
  -> holds one private _APPLICATION_DEPENDENCIES cell

current root api.py application composition
  -> builds executor/helpers and uncalled handler closures
  -> fixes the 21 route definitions and signature
  -> constructs one fully populated ApiApplicationDependencies instance
  -> publishes that exact instance to the canonical private cell once
  -> exposes the same object as root _APPLICATION_DEPENDENCIES
  -> builds the registrar whose closures read bundle leaf fields

future canonical application (FC-04)
  -> reuses the same bundle type, cell, and field contract
  -> root api.py becomes an exact compatibility facade
```

The canonical module imports only standard-library typing/dataclass support. It
does not import root `api.py`, bootstrap, runtime, the future application owner,
route factories, feature services, ComfyUI host modules, or `aiohttp`. Direct
canonical import creates no executor, handlers, routes, registration, runtime,
lock, atexit callback, I/O, or host lookup.

The private cell is not a service locator or lifecycle registry. It is unbound
until the one application composition publishes its fully constructed bundle.
Publishing the same identity is idempotent; publishing a different identity is
an error. It has process/application lifetime, no close operation, no lock, no
reset API, and no E-09 cleanup item. Production hot reload remains unsupported.

`easyuse_anima.api.dependencies.__all__` remains empty. The bundle object may be
patched only through its named leaf fields; replacing the bundle cell is not a
supported compatibility operation.

## 2. Exact classification and migration

The complete current root inventory remains owned by P-API-01. FC-03A does not
duplicate its constants, factories, handlers, or canonical mirrors. It assigns
the following migration disposition to those existing families.

| Classification | Existing root family | FC-03B disposition |
| --- | --- | --- |
| supported host/API behavior | route methods, paths, order, handler identity, marker/signature, payload/error shape, request correlation | unchanged; still produced by the current root application |
| supported named dynamic compatibility seam | injected `ProfileMutationError`; canonical `PromptTranslationError` base plus unregistered/root-derived descendant metadata | call-time bundle leaves; concrete exception policy tables remain canonical/static |
| transitional private patch seam | server/web, registrar resolvers, request/payload callbacks, feature operations and timeouts listed below | consumer moves from root globals to the corresponding bundle leaf; direct tests patch that leaf |
| unsupported test-only owner inspection | `_build_*` factories, `_api_router`, `_api_responses`, route-module aliases | tests inspect the canonical owner directly; no new compatibility alias is created |
| unsupported test-only canonical mirror | profile constants, directories, limits, repository/path/normalization aliases | production does not consume the mirror; existing compatibility ledger is untouched |
| production-only implementation detail | executor/sync/route-translation identities, request correlator, 21 handlers, definitions/signature, routes and registrar | remains in the current root application during FC-03B; FC-04 owns application movement |

### Canonical bundle leaves

The top-level bundle groups mutable leaves by the factory dictionary that
consumes them. Names below are exact; FC-03B must not add a generic string map or
catch-all resolver.

| Bundle family | Exact leaf fields | Observation |
| --- | --- | --- |
| `host` | `server`, `web`, `get_prompt_routes`, `route_definitions`, `route_signature`, `register_route_definitions` | registration call time; `web` also at response call time, while the existing import-time `web is not None` handler-construction decision is unchanged |
| `request` | `create_request_id`, `run_file_io`, `error_response`, `contract_error_response`, `profile_error_response`, `profile_mutation_error_type`, `safe_profile_validation_messages` | request/error call time |
| `settings` | `public_settings`, `save_setting`, `load_long_text_settings`, `save_long_text_settings`, `get_settings_payload`, `save_setting_payload`, `get_long_text_settings_payload`, `save_long_text_settings_payload` | payload or request call time |
| `wildcard_autocomplete` | `get_runtime`, `resolve_wildcard_roots`, `list_wildcards`, `resolve_autocomplete_source`, `resolve_autocomplete_source_path`, `resolve_autocomplete_limit`, `available_autocomplete_sources`, `autocomplete_status`, `search_autocomplete`, `classify_prompt_text`, `wildcards_payload`, `autocomplete_status_payload`, `search_autocomplete_payload`, `classify_prompt_payload`, `public_autocomplete_status`, `public_autocomplete_payload` | payload or request call time; installed runtime identity is not moved |
| `profiles` | `list_loras`, `list_lora_profiles`, `list_aio_profiles`, `load_lora_profile`, `load_aio_profile`, `save_lora_profile`, `save_aio_profile`, `delete_aio_profile`, `rename_aio_profile`, `fix_lora_profile_payload`, `resolve_lora_preview_path` | request call time |
| `translation` | `translate_prompt_markers`, `resolve_prompt_translation_settings`, `route_timeout_seconds`, `prompt_translation_error_type`, `prompt_translation_error_response` | translation execution/error call time; executor and sync-function identities remain application-owned |
| `torch_compile` | `collect_diagnostics`, `recommend_torch_compile` | request/file-I/O dispatch call time |

Static parsing functions, canonical concrete error tables, path primitives and
factory implementations are not compatibility cells merely because root
`api.py` currently imports them. They remain direct canonical inputs.

### Dynamic error rules

- `request.profile_mutation_error_type` accepts the existing injected error
  type contract. `profile_error_response` reads this leaf and
  `safe_profile_validation_messages` at handler call time.
- `translation.prompt_translation_error_type` is the canonical
  `PromptTranslationError` base or a compatible descendant type. The translation
  handler resolves it inside the request error boundary, not when the handler is
  built.
- Known concrete translation exceptions and descendants keep their ordered
  static mapping. The exact base keeps canonical status 500. An unregistered
  descendant continues to supply its existing status/code/message semantic
  fields at response call time.
- No HTTP status, code, message, details, logging, redaction, or request-ID rule
  changes in FC-03B.

The private translation route factory may replace its build-time
`translation_error_type` argument with an exact call-time
`get_translation_error_type` resolver. This is the only permitted route-factory
signature adjustment and does not change the public HTTP route signature.

## 3. Patch and root-facade rules

After FC-03B, supported tests and compatibility injection patch an exact bundle
leaf, for example:

```text
easyuse_anima.api.dependencies._APPLICATION_DEPENDENCIES
  .profiles.save_aio_profile

easyuse_anima.api.dependencies._APPLICATION_DEPENDENCIES
  .request.profile_mutation_error_type
```

The root spelling may remain as an identity/read-only compatibility alias, but
assignment such as `api._save_aio_profile = replacement` is no longer a
supported patch operation after its consumer moves. FC-03B does not implement
module assignment interception, duplicate root cells, proxy modules, deprecation
warnings, telemetry, or fallback reads from root globals.

Production callbacks read the canonical private cell through its private getter;
they do not read the root `_APPLICATION_DEPENDENCIES` alias. Reassigning that
root alias is therefore neither a patch point nor a second mutable owner.

FC-03B deletes no root symbol. The minimum root surface that must survive this
lane is:

1. all current host/application identities until FC-04: executor helpers, 21
   handlers, route definitions/signature, `routes`, and `register_routes`;
2. one exact root alias to the canonical dependency bundle identity;
3. existing supported error-class and root compatibility aliases governed by
   their current ledgers.

Unsupported factory/mirror names may remain inert for rollback compatibility,
but production and updated direct tests do not use them as patch owners. Their
removal is not authorized by FC-03.

## 4. Preserved lifecycle and application boundary

FC-03B changes neither application placement nor construction order:

```text
root api.py import
  -> translation executor/runtime creation
  -> response/payload helper creation
  -> 21 uncalled handler closures and route definition/signature creation
  -> one fully populated dependency bundle publication
  -> initial route-table resolution and registrar creation
  -> root entrypoint calls bootstrap.initialize
  -> RuntimeServices freezes the same executor shutdown as cleanup item 1
```

All E-09 invariants remain exact: one bootstrap lifecycle owner and lock, atexit
once, terminal/idempotent shutdown, no callback after shutdown, repeated
initialize with the same runtime and route refresh, one executor identity, fixed
seven-step cleanup, expected-identity rollback with original-error preservation,
no route deregistration/marker clear, no limiter/provider close, and no reset or
hot reinitialize API.

Package entrypoint import followed by a late ordinary root `api.py` import still
resolves cached application, executor, handler, registrar, dependency-bundle,
runtime, and facade identities without duplicate registration or lifecycle
state.

Handler closure creation necessarily precedes publication because the host
family contains the final route definitions and signature. No handler, payload
helper, or translation callback is invoked before publication. This is the only
ordering correction from FC-03A wording; runtime initialization and every
observable E-09 event remain in their original order.

FC-03B temporarily raises the reviewed `api.py` module-size ledger because the
single canonical dependency owner exists before FC-04B moves application
construction out of the root facade. The ledger is owned by #593 and names
FC-04B as its exact decomposition boundary; increasing it again is forbidden.
Reflection, positional field wiring, and duplicate mutable cells are not valid
ways to hide this transitional composition cost.

## 5. FC-03B task card

```text
Task / Issue: #593 / FC-03B
Base SHA: latest dev after FC-03A merges
Goal: move request/registration-time API patch ownership from root globals to
  the single private canonical ApiApplicationDependencies bundle
Allowed production:
  api.py
  easyuse_anima/api/dependencies.py (new private owner)
  easyuse_anima/api/routes/translation.py
Allowed tests/evidence:
  tests/test_python_api_dependencies_contract.py (new direct owner)
  tests/test_api_contract.py
  tests/test_prompt_translation_api.py
  tests/test_python_api_facade_lifecycle_contract.py
  tests/test_python_runtime_lifecycle_contract.py
  tests/test_python_package_skeleton.py
  tests/test_python_import_boundaries.py
  tests/test_python_backend_analyzer.py
  tests/test_python_size_complexity.py
  tests/test_comfy_host_wiring.py
  tests/test_python_autocomplete_runtime_contract.py
  tests/test_python_repository_filesystem_contract.py
  tests/test_python_compatibility_surface.py
  tests/test_python_feature_error_contract.py
  tests/test_aio_profiles.py
  tests/test_lora_profiles.py
  tests/test_lora_preview.py
  directly required analyzer/error/compatibility/size/runtime/repository fixtures
  and this Contract,
  P-API-01, the final-convergence roadmap, and compatibility wording
Preserve:
  every route method/path/order/signature/marker and all 21 handler identities;
  payload/error/request-ID/logging/redaction and file-I/O dispatch behavior;
  named profile/translation dynamic error compatibility at call time;
  executor/application/runtime/facade identity and every E-09 invariant;
  root aliases, package/no-host behavior, repeated initialize and route refresh
Forbidden:
  canonical application construction or movement; bootstrap/runtime/lifecycle
  changes; a second bundle/cell/lock/atexit/cleanup owner; canonical-to-root
  import; bundle replacement/reset; root symbol deletion; public __all__ change;
  repository/schema/persistence/error-policy change; route deregistration;
  unrelated cleanup; release/tag/Registry work
Focused tests and purpose:
  ApiDependencies direct owner: exact leaves, canonical/root identity, one-time
  publication, import purity, and representative call-time patch observation;
  full direct API contract module: every migrated request/registration seam;
  PromptTranslationApiTests: call-time translation dependencies/error types;
  PythonApiFacadeLifecycleContractTests and E-09 lifecycle owner: executor first,
  late import, repeated initialize, rollback and fixed cleanup;
  package/no-host, import-boundary, analyzer and feature-error contracts
Promotion gates:
  changed-file static, direct focused owners, git diff --check, official full
  once on final SHA; validate/pack/archive and isolated packaged no-host/late-api
  identity smoke because a shipped module/import closure is added; no browser or
  canvas matrix unless host-visible behavior changes
Rollback boundary:
  one cohesive Move commit/PR; revert restores root-global patch ownership;
  no data or migration rollback
Stop conditions:
  preserving a supported seam requires canonical-to-root import, root assignment
  interception, a second mutable owner, lifecycle/cleanup mutation, application
  movement, handler/route/executor identity change, or a newly proven root seam
  outside the P-API-01 inventory
Next: FC-04A only after FC-03B merges
```

## 6. Validation and verdict

FC-03A reuses the existing direct registration, dynamic profile/translation,
late-import, lifecycle, package/no-host, compatibility, import, and analyzer
owners. No new executable fixture is required because P-API-01 already owns the
exact symbol inventory and current direct tests prove each observation class.

Verdict: **FC-03B complete**. Direct evidence leaves one acyclic design and no
PRO trigger. FC-04A is the only next task after this Move merges. FC-04B
application movement, D-14/root removal, release, tag, and Registry work remain
forbidden until their own gates.
