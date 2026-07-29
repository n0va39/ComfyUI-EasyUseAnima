# P-API-01 API Facade / E-09 Lifecycle Compatibility Gate

## Status and authority

- Status: P-API-01 completed with a **RETAIN** verdict.
- Completed task: Issue #582.
- Parent/compatibility ledger: Issues #185 and #186.
- Lifecycle authority: [`python-runtime-e09-lifecycle-contract.md`](python-runtime-e09-lifecycle-contract.md).
- Audited baseline: `ffa986df7a477ff68af08cae4dfe834e01bf3aa4` after PR #583.
- Type: production-free Contract/gate.

This gate does not reopen E-09. It prevents an API facade move from accidentally
changing the lifecycle that E-09 deliberately made terminal, serialized, and
bootstrap-owned.

## 1. Current creation sequence

The current package startup order is significant:

```text
root __init__.py
  -> import root api.py
       -> build translation route runtime/executor
       -> publish bootstrap._TRANSLATION_ROUTE_EXECUTOR
       -> build error/request/payload helpers
       -> build 21 handlers and route definitions
       -> build root register_routes closure
  -> import bootstrap.initialize
  -> initialize(register_routes=api.register_routes, ...)
       -> register bootstrap.shutdown with atexit once
       -> construct RuntimeServices
       -> snapshot fixed cleanup plan
            first item = existing translation route executor shutdown
       -> install runtime and translation facade
       -> call the current register_routes closure
       -> initialize wildcard directory once/retry OSError
```

Moving API application construction changes lifecycle behavior when it changes any of
these relative times or identities. P-API-01 must model this sequence before choosing a
canonical owner.

## 2. Frozen E-09 invariants

P-API-01 and any later P-API-02 must preserve all of the following.

### Single owner and terminal state

- `easyuse_anima.bootstrap` is the only production lifecycle owner.
- `initialize()` and `shutdown()` share `_INITIALIZE_LOCK`.
- `atexit.register(bootstrap.shutdown)` occurs exactly once.
- `shutdown(); shutdown()` performs cleanup at most once.
- `initialize()` after shutdown raises before route, wildcard, or host callbacks.
- No API application object owns another lifecycle lock, atexit hook, shutdown/reset,
  terminal flag, or closeable process-state registry.

### Repeated initialize

Before shutdown:

- repeated initialize preserves the exact installed RuntimeServices identity;
- the current route registrar is called on every initialize;
- the wildcard directory initializes once, with existing `OSError` warning/retry;
- `register_routes() == False` remains nonterminal;
- concurrent initialize remains serialized with shutdown.

### Translation route executor

- exactly one process translation route executor exists;
- it is the executor used by the root-compatible translation route callbacks;
- it exists before the default RuntimeServices cleanup plan is frozen;
- its `shutdown` callback remains the first cleanup-plan item;
- late import of root `api.py` after package initialization must not construct a second
  executor or replace the executor captured by the runtime plan.

A design that requires appending the executor to an already-created cleanup plan is an
E-09 behavior change, not a P-API Move.

### Fixed cleanup order

The seven-step order remains:

1. translation route executor shutdown;
2. AiO first-pass cache clear;
3. wildcard snapshot clear;
4. autocomplete index no-op close;
5. autocomplete snapshot clear;
6. expected-identity translation facade restore;
7. translation service cache close.

P-API must not add an API application cleanup step or reorder these owners.

### Startup rollback

Unexpected route/wildcard failure preserves the original exception and only rolls back
attempt-created runtime/facade state by expected identity. It does not:

- deregister routes or clear the route marker;
- drain active requests;
- clear/cancel/release API file-I/O limiters;
- close provider/client objects without a proven protocol;
- support hot shutdown-to-reinitialize.

Moving application construction from import time into `initialize()` changes which
failure is covered by bootstrap rollback. That timing change must be rejected or owned
by a separate Behavior Contract.

## 3. P-API collision inventory

P-API-01 must explicitly inspect the following conflict classes.

### Import order and cycles

The candidate must avoid:

```text
bootstrap -> canonical API application -> bootstrap
canonical internal module -> root api.py
root api.py late import -> second canonical application
```

A canonical application may depend on router, route adapters, feature owners, and
injected bootstrap composition primitives only when the resulting direction is acyclic.

### Root late-bound compatibility seams

Current root tests and compatibility consumers can patch or inspect values such as:

```text
server / web / routes
_ROUTE_DEFINITIONS / _ROUTE_SIGNATURE
_register_route_definitions
request/error/payload callbacks
profile/translation dependencies
register_routes
```

P-API-01 must classify each seam as:

```text
supported identity
transitional private compatibility seam
unsupported test-only seam
production-only implementation detail
```

A canonical owner must not import root `api.py` to preserve patchability. Unsupported
seams may be retired only through their existing compatibility gate, not silently inside
P-API-02.

### Registrar identity and refresh

The current root `register_routes` is a canonical router-owned closure whose resolver
reads root globals at call time. P-API must preserve:

- one-argument callable behavior;
- current route publication into `routes`;
- exact route marker/signature;
- same-table idempotence, new-table refresh, and mismatch behavior;
- `web is None` returning false without terminal startup failure;
- no marker removal on shutdown.

### No-host and late import

The candidate must remain safe when `server`/`aiohttp` are absent. It also must prove:

```text
package entrypoint imported first
  -> runtime installed
  -> root api.py imported later by a compatibility consumer
  -> same application/handlers/registrar/executor identities
  -> no second registration or lifecycle resource
```

### Reload and test isolation

E-09 does not support production hot shutdown/reinitialize. E-10 removed module reload
and direct private runtime mutation from ordinary tests. Therefore P-API/G-06/release
work must not add:

- `importlib.reload()` of production lifecycle/application modules;
- a production reset API;
- tests that call shutdown and then expect initialize to succeed in the same process;
- private state mutation outside `tests/runtime_test_support.py`.

## 4. Candidate shapes

P-API-01 compares only evidence-backed shapes.

### A. Canonical API application singleton + root exact aliases

Feasible only when:

- one canonical application is constructed exactly once;
- entrypoint and root facade resolve the same object identities;
- translation executor construction precedes runtime cleanup-plan composition;
- late root import does not construct another application;
- root supported seams remain exact aliases or intentionally retained compatibility
  adapters without a canonical-to-root back-reference.

### B. Bootstrap-owned production application + root compatibility facade

Feasible only when:

- bootstrap remains the sole lifecycle owner without becoming a feature monolith;
- no bootstrap/application import cycle appears;
- application construction timing preserves current startup/rollback semantics;
- no new public bootstrap export is required solely for the root facade;
- root facade later import resolves existing application identity instead of creating
  state.

### C. Retain current root production facade

This is a valid result when A/B cannot preserve lifecycle and compatibility without a
cycle, duplicate state, or behavior change. RETAIN must record maintenance cost and a
specific future evidence trigger; it is not a failed audit.

## 5. Required P-API-01 result

The production-free Contract must produce:

1. exact root API symbol/consumer/classification/identity/patch-time inventory;
2. sequence diagrams for package import, no-host import, late root API import, repeated
   initialize, route failure, shutdown, and process exit;
3. identity graph for application, translation executor, handlers, route definitions,
   registrar, route registry, runtime, and translation facade;
4. candidate A/B/C compatibility matrix against every E-09 invariant;
5. `FEASIBLE` or `RETAIN` verdict;
6. if FEASIBLE, one bounded P-API-02 task card with allowed files, forbidden changes,
   focused tests, package/live triggers, and rollback boundary;
7. if RETAIN, exact revisit events.

P-API-01 must not change production behavior.

## 6. Required evidence

Focused evidence must cover:

```text
bootstrap repeated initialize identity
atexit once
shutdown terminal/idempotent
initialize-after-shutdown callback suppression
initialize/shutdown serialization
seven-step cleanup order
translation executor exact identity and first position
route false nonterminal
route exception rollback and original error
wildcard OSError retry
route marker/signature/idempotence/new-table refresh
no route deregistration
no-host/package import
late root API import creates no duplicate application/executor
root/canonical compatibility identity
import boundary and analyzer
```

Use existing tests when they already prove the invariant. Add a new deterministic test
only for an unproven sequence, especially late root import after package initialization.

Validation timing:

- docs-only inventory with no test/tool/fixture change: focused evidence + diff check;
- new/changed executable fixture or test: official full once on final SHA;
- P-API-02 import/registration/archive change: validate/pack/archive and isolated import
  or API live smoke as triggered by its final task card.

## 7. P-API-01 completed inventory

### Identity and ownership graph

There is no separate current `Application` class. The imported root `api.py` module is
the application/composition container. Its exact process identities are:

| Identity | Created or selected by | Published/consumed by | Cleanup ownership |
| --- | --- | --- | --- |
| application | Python import system as the single root `api.py` module object | root entrypoint and compatibility importers | no application cleanup item |
| translation executor | `bootstrap.build_translation_route_runtime`, invoked once by root `api.py` import | root `_PROMPT_TRANSLATION_WORKER`, bootstrap `_TRANSLATION_ROUTE_EXECUTOR`, translation handler callbacks | executor `shutdown` is cleanup item 1 |
| 21 handlers | private bootstrap composition factories, invoked by root `api.py` | root handler globals and `_ROUTE_DEFINITIONS` | no deregistration or handler cleanup |
| route definitions | canonical router builder, invoked by root `api.py` | root `_ROUTE_DEFINITIONS`, registrar resolver, host route registry | retained after shutdown |
| registrar | canonical router registrar builder, invoked by root `api.py` | root `register_routes`, root entrypoint, repeated initialize | no separate cleanup; marker remains |
| route registry | host `PromptServer.instance.routes`, selected at registrar call time | registrar and host | host-owned; never closed or cleared here |
| runtime | `bootstrap.initialize` | bootstrap `_DEFAULT_RUNTIME` and runtime `_RUNTIME_SERVICES` as the same object | bootstrap terminal shutdown invokes `RuntimeServices.close` |
| translation facade | bootstrap installs `runtime.translation` into the canonical service facade | route translation service calls | expected-identity restore is cleanup item 6 |

The identity edges are therefore:

```text
root api module (current application identity)
  -> executor == api._PROMPT_TRANSLATION_WORKER
              == bootstrap._TRANSLATION_ROUTE_EXECUTOR
              == cleanup_plan.callbacks[0].__self__
  -> handlers == each _ROUTE_DEFINITIONS[*].handler
  -> registrar == api.register_routes
  -> registrar resolves api.routes / definitions / signature / web at call time

bootstrap._DEFAULT_RUNTIME == runtime._RUNTIME_SERVICES
runtime.translation == canonical translation default facade after initialize
```

The narrow executable owner
`PythonApiFacadeLifecycleContractTests.test_package_then_late_api_import_reuses_every_application_identity`
proves the current integrated sequence in an isolated package namespace. It imports the
actual entrypoint, actual root `api.py`, bootstrap, router, runtime, handlers, and
registrar with only host registration objects stubbed. A later ordinary
`import_module(<package>.api)` resolves the cached module and preserves application,
executor, handlers, definitions, registrar, runtime, cleanup plan, facade, route marker,
and the exact 21 registrations. A repeated initialize keeps the runtime and route table
unchanged and does not register a second atexit callback.

### Creation and cleanup sequences

Package entrypoint:

```text
import root package
  -> import root api.py
     -> create executor and publish both root/bootstrap references
     -> create callbacks, handlers, definitions, and registrar
  -> bootstrap.initialize under _INITIALIZE_LOCK
     -> register atexit once
     -> create and install RuntimeServices
     -> snapshot executor shutdown as cleanup item 1 of 7
     -> install translation facade
     -> register routes
     -> initialize Wildcard once or retain the OSError retry
```

Direct no-host canonical import:

```text
import easyuse_anima.bootstrap/router/route owners
  -> no root api module
  -> no application/executor construction
  -> no host I/O, route registration, runtime, atexit, or lifecycle state
```

Current late root API import:

```text
package entrypoint already imported root api.py
  -> later ordinary import resolves sys.modules entry
  -> no module execution
  -> no second executor/application/lifecycle state/route registration
```

This cached-import proof is a current baseline, not evidence that an entrypoint which no
longer eagerly imports `api.py` can preserve the same root patch semantics.

Repeated initialize, route failure, shutdown, and process exit remain:

```text
initialize / initialize
  -> same lock and runtime
  -> registrar runs each call; route marker makes the same table idempotent
  -> a new table receives the 21 definitions
  -> Wildcard success stays once; OSError remains retryable

unexpected register-routes or Wildcard failure
  -> preserve original error
  -> restore only attempt-created runtime and attempt-bound facade identities
  -> do not roll back executor, routes, marker, caches, or directories

shutdown / shutdown or process atexit
  -> same initialize lock
  -> terminal/idempotent state
  -> detach expected runtime identity
  -> execute fixed seven-item cleanup
  -> retain routes/marker; no file-I/O limiter or provider close
```

### Root symbol classification and patch time

Root `api.py` declares no `__all__`. Endpoint paths, payloads, handler behavior, and
registration are supported host contracts, but most Python names below are not declared
public exports. The exact current buckets are:

| Classification | Exact symbols or symbol family | Consumer and observation time |
| --- | --- | --- |
| supported compatibility input | `PromptTranslationError` base and unregistered/root-derived subclasses; injected `ProfileMutationError` | profile/translation error adapters read the injected type or dynamic fields at handler call time |
| production application identity | `_PROMPT_TRANSLATION_WORKER`, `_translate_prompt_sync`, `_translate_prompt_for_route`, `_prompt_translation_error_response`; all 21 `*_handler` globals; `_ROUTE_DEFINITIONS`, `_ROUTE_SIGNATURE`, `routes`, `register_routes` | root entrypoint, registered host routes, bootstrap cleanup; objects are created at root import except `routes`, which the registrar republishes at call time |
| transitional late-bound dependency seam | `server`, `web`, `_get_prompt_routes`, `_register_route_definitions`, `create_request_id`, `_run_file_io`, `public_settings`, `save_setting`, `list_wildcards`, `resolve_wildcard_roots`, `autocomplete_status`, `available_autocomplete_sources`, `search_autocomplete`, `classify_prompt_text`, `resolve_autocomplete_source`, `resolve_autocomplete_limit`, `_get_runtime`, `_collect_torch_compile_diagnostics`, `_recommend_torch_compile`, `translate_prompt_markers`, `resolve_prompt_translation_settings`, `PROMPT_TRANSLATION_ROUTE_TIMEOUT_SECONDS` | registrar and handler closures resolve root module globals at each registration or request call; direct owner tests intentionally patch these names |
| transitional profile operation seam | `_list_loras`, `_list_lora_profiles`, `_list_aio_profiles`, `_load_lora_profile`, `_load_aio_profile`, `_save_lora_profile`, `_save_aio_profile`, `_delete_aio_profile`, `_rename_aio_profile`, `_fix_lora_profile_payload`, `_resolve_lora_preview_path` | profile route closures resolve them at request call time; prior Move contracts preserved the root patch point |
| transitional payload seam | `_get_settings_payload_sync`, `_save_setting_payload_sync`, `_wildcards_payload_sync`, runtime autocomplete wrapper functions, and the profile/settings/autocomplete/translation dependency dictionaries passed to bootstrap factories | root-created lambdas resolve the module globals at request call time |
| unsupported/test-only owner inspection | `_build_route_definitions`, `_build_route_signature`, `_build_*_route_group`, `_build_translation_route_runtime`, `_build_translation_route_handler`, `_api_router`, `_api_responses`, and feature route module aliases | direct owner tests inspect canonical factory ownership; production callers do not import these names |
| unsupported/test-only canonical mirrors | `PROFILE_KIND_*`, profile directories/limits, repository/path/normalization helpers, and canonical profile document aliases | direct API compatibility tests inspect or invoke them; they are not in a root public export list and production route callbacks use only the subset explicitly injected above |

The 21 handler identities, in canonical route order, are:

```text
get_settings_handler
set_setting_handler
get_long_text_settings_handler
get_wildcards_handler
autocomplete_status_handler
autocomplete_handler
classify_prompt_handler
translate_prompt_handler
lora_preview_handler
loras_handler
lora_profiles_handler
aio_profiles_handler
load_lora_profile_handler
load_aio_profile_handler
save_lora_profile_handler
save_aio_profile_handler
delete_aio_profile_handler
rename_aio_profile_handler
fix_lora_profile_handler
save_long_text_settings_handler
aio_torch_compile_handler
```

The key distinction is not leading underscore versus public spelling. Supported host
behavior and the two named dynamic error seams are compatibility requirements;
repository-only factory/constant inspection is test-only. The late-bound dependency
families are private/transitional, but they cannot be silently converted to build-time
canonical values because their prior task cards and direct tests deliberately preserve
request-time patch observation.

## 8. Candidate matrix and verdict

| E-09 / compatibility gate | A. canonical singleton | B. bootstrap-owned application | C. current root facade |
| --- | --- | --- | --- |
| one bootstrap lifecycle owner, one lock, atexit once | conditional | yes in principle | **pass** |
| terminal/idempotent shutdown; fail before callbacks after shutdown | conditional | yes in principle | **pass** |
| repeated initialize keeps runtime identity and route refresh | conditional | conditional | **pass** |
| one executor exists before cleanup-plan composition | requires a pre-initialize publish path into bootstrap | requires pre-initialize private application construction | **pass** |
| executor shutdown is cleanup item 1; fixed seven-item plan | fails if construction moves into initialize or the plan is mutated later | fails if application is lazy inside initialize or attached after the plan snapshot | **pass** |
| expected-identity rollback and original error | construction outside initialize is non-rollback as today; moving it inside changes the contract | same timing conflict | **pass** |
| no route deregistration/marker clear, limiter/provider close, reset/hot reinitialize | achievable | achievable | **pass** |
| late root import resolves existing application/executor/handler/registrar identities | achievable only with a canonical owner that root aliases | achievable only with a private bootstrap accessor | **pass** through normal import caching |
| no canonical-to-root or bootstrap/application cycle | fails if canonical handlers read root globals; `easyuse_anima.api` importing bootstrap also violates the enrolled outer-owner boundary | avoids a root import, but cannot read root globals without a back-reference | **pass** |
| supported and transitional call-time root seams keep the same patch time | **fail** unless the canonical application imports root `api.py` or adds a new proxy/migration contract | **fail** because an application built before late root import cannot close over that later module's globals | **pass** |
| no new public bootstrap export or import-time no-host application side effect | conditional and requires a new injection path | fails for a public accessor; import-time construction changes direct-bootstrap behavior | **pass** |

Verdict: **RETAIN candidate C**.

A and B each preserve portions of E-09 in isolation, but neither preserves both required
facts at once:

1. the executor/application must exist before `RuntimeServices` freezes cleanup item 1;
2. the current handler and registrar closures intentionally resolve root `api.py`
   globals at registration/request time.

Making the root module genuinely late breaks the second fact. Restoring it requires a
canonical-to-root back-reference, a second mutable proxy/state owner, or an explicit
compatibility migration that changes patch ownership. Constructing the application in
`initialize`, or adding it to an already-created cleanup plan, changes E-09 rollback and
cleanup-plan timing. Those are forbidden P-API-01/P-API-02 changes, not implementation
details.

Only C satisfies every current gate, so no focused technical PRO review is required.
P-API-02 is **not allowed** from this result.

### Retention cost and revisit events

Current cost:

- root entrypoint keeps an eager production import of the 698-line root facade;
- application identity remains implicit in a module namespace rather than one typed
  bundle;
- route composition and compatibility callback cells remain coupled to root globals;
- direct API tests continue to patch the root facade, and package import keeps its broad
  API composition closure.

These costs do not justify weakening E-09 or changing preserved request behavior.
Revisit P-API only after at least one of these evidence events:

1. a separate compatibility Contract migrates every preserved root call-time patch seam
   to an exact canonical patch owner and updates its consumers;
2. direct consumer evidence proves a named seam unsupported and its existing
   compatibility gate explicitly retires it;
3. an acyclic private pre-initialize application publication path is demonstrated
   without a new public bootstrap export or no-host import side effect; or
4. an explicit lifecycle Behavior Contract authorizes different application creation,
   rollback, or cleanup-plan timing.

The next ordinary roadmap task is G-05A. P-API-02, D-14, release, and Registry work stay
parked.

The later FC-03A Contract satisfies revisit event 1 without starting P-API-02:
[`python-api-fc03-patch-owner-contract.md`](python-api-fc03-patch-owner-contract.md)
fixes one private canonical dependency-bundle owner before any application move.
FC-03B performs only that patch-owner migration; FC-04 separately re-evaluates
the application identity under every E-09 gate.

## 9. Future conflict guards

### G-05 size ratchet

E-09 intentionally treats initialization, shutdown ordering, and rollback as one
cohesive concurrency contract. Size thresholds are review triggers, not permission to
split lifecycle state among modules. A size exception should reference E-09 when a
mechanical split would create a second owner or obscure cleanup order.

### G-06 test ownership

Lifecycle tests remain jointly owned by bootstrap/runtime and may exercise API registrar
callbacks as integration evidence. G-06 must not move them into feature tests in a way
that duplicates private runtime setup, adds module reload, or weakens exact ordering.

### Release N and package smoke

- terminal shutdown tests run in a fresh process;
- package reload/repeated initialization before shutdown may be tested separately;
- shutdown followed by production reinitialize is not a supported release gate;
- root API and canonical application import parity must be read back from the packed
  artifact;
- no dedicated release is created merely to start a shim window.

### Wildcard direct shim

P-WC-02 moved production consumers to canonical wildcard owners. E-09 still clears the
same `_DEFAULT_WILDCARD_SNAPSHOTS` identity at cleanup step 3. P-API must consume the
canonical wildcard facade and must not recreate a root-owned wildcard lifecycle.

## 10. Stop and PRO conditions

Codex performs ordinary source inventory and Contract work without PRO review.

Request focused technical PRO review only when, after direct evidence:

- two or more candidate shapes still satisfy every lifecycle and compatibility gate;
- preserving a supported late-bound seam requires an unavoidable canonical-to-root
  back-reference or import cycle;
- translation executor identity cannot be available before cleanup-plan composition;
- a dynamic cleanup-plan mutation or second lifecycle owner appears necessary;
- current import-time application construction must move into initialize and changes
  rollback semantics;
- compatibility evidence cannot distinguish supported from test-only behavior.

Routine test failures, helper placement, function names, or documentation choices do
not require PRO review.

## 11. Codex resume instruction

```text
P-API-01 is complete with RETAIN. Do not start P-API-02 from this result.

For the next task, start Issue #188 / G-05A from latest origin/dev and read only:
- current-policies.md
- codex-execution-efficiency.md universal rules
- post-phase-e-maintenance-roadmap.md G-05A and validation sections
- Issue #188 latest G-05A checkpoint
- tools/analyze_python_backend.py metric owners
- existing analyzer fixture and direct analyzer/tool tests

Do not reopen P-API-02, D-14, release, or Registry work.
Do not reread all D/E history or every production module.

Freeze the existing analyzer size/complexity baseline and add only the reviewed
changed-path ratchet. Size thresholds remain review triggers and must not split the
single E-09 lifecycle owner.

Follow the G-05A task card and validation boundary in the active roadmap.
```
