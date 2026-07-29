# FC-04A Canonical API Application and E-09 Lifecycle Contract

## Scope and decision

FC-04A is a production-free Contract based on
`dev@498f978404a370a5d29caaa4b6bf508dd346daf0`, after FC-03B moved every
preserved request/registration-time patch seam to the single private
`ApiApplicationDependencies` owner.

The selected shape is one **canonical application identity with bootstrap-owned
outer composition**:

```text
root api.py compatibility binder
  -> calls one private bootstrap composition entrypoint
     -> calls the canonical application factory once
        -> publishes one immutable ApiApplication identity
  -> binds exact root aliases to that application and canonical owners

bootstrap.initialize
  -> remains the only lifecycle entrypoint
  -> freezes the already-created executor as cleanup item 1
```

This is the only evidence-backed shape that satisfies both the final-convergence
owner model and every E-09 invariant. The canonical module owns application
identity; bootstrap owns concrete outer wiring and lifecycle; root `api.py` owns
only compatibility binding. These are complementary responsibilities, not two
application owners.

No focused technical PRO review is required. The other concrete shapes either
create import-time canonical side effects, leave production composition in the
root facade, or make bootstrap the application identity owner instead of the
canonical package.

## Immutable application model

FC-04B introduces private, frozen, slotted application records in
`easyuse_anima.api.application`. They are not added to a package or bootstrap
`__all__`.

```text
ApiApplication
  dependencies                 exact FC-03B ApiApplicationDependencies identity
  translation_executor         exact process translation route executor
  handlers                     frozen ApiRouteHandlers record
  route_definitions            exact ordered 21-route tuple
  route_signature              exact ordered method/path tuple
  register_routes              exact canonical registrar closure
  compatibility                frozen ApiCompatibilityIdentityView
```

`ApiRouteHandlers` has these exact fields in canonical route order:

```text
get_settings_handler
set_setting_handler
get_long_text_settings_handler
get_wildcards_handler
save_long_text_settings_handler
autocomplete_status_handler
autocomplete_handler
classify_prompt_handler
translate_prompt_handler
aio_torch_compile_recommend_handler
lora_preview_handler
loras_handler
lora_profiles_handler
save_lora_profile_handler
load_lora_profile_handler
aio_profiles_handler
save_aio_profile_handler
load_aio_profile_handler
delete_aio_profile_handler
rename_aio_profile_handler
fix_lora_profile_handler
```

`ApiCompatibilityIdentityView` holds only application-created objects that the
root binder must expose by exact identity:

- the guarded initial `server` and `web` values, compatibility logger, prompt-route
  resolver and initial route table;
- `_translate_prompt_sync`, `_translate_prompt_for_route` and
  `_prompt_translation_error_response` beside the executor stored directly on the
  application;
- `_error_response`, `_contract_error_response`, `_request_correlated`,
  `_resolve_lora_preview_path` and `_profile_error_response`, including the exact
  safe validation-message identity;
- the settings, long-text, Wildcard and Autocomplete payload helpers created during
  composition; and
- the five runtime-aware Autocomplete compatibility functions currently created by
  root `api.py`.

The view does not duplicate handlers, definitions, signature, registrar or the
dependency bundle; those are direct `ApiApplication` fields. Static request helpers,
profile constants/operations, error classes, file-I/O objects and route-factory
inspection aliases remain direct root-to-canonical aliases and are not application
state.

The application record and its nested records are immutable. Handler closures and the
registrar still observe the named mutable leaves of the existing dependency bundle at
call time. Immutability therefore fixes identity and structure without freezing a
supported patch seam.

### Size and responsibility boundary

The blocking G-05 contract applies the 400-line adapter limit to every
`easyuse_anima/api/*` module. Current root application construction occupies roughly
`api.py:243-809` before adding the immutable records and publication logic. Moving it
into one new `application.py` would replace the reviewed root exception with a new
canonical exception instead of completing the decomposition.

FC-04B therefore uses these three private canonical modules in one cohesive rollback
unit:

| Module | Exact responsibility |
| --- | --- |
| `api/application.py` | frozen application identity/view records, the private publish-once cell, ordered final assembly, FC-03B dependency publication, registrar assembly and final application publication |
| `api/application_compatibility.py` | guarded host selection plus translation runtime, response/correlation/profile/preview/payload helpers and the five runtime-aware Autocomplete compatibility functions; returns one frozen parts record |
| `api/application_routes.py` | explicit typed wiring of the eight injected bootstrap composition operations into the exact 21 handlers, ordered definitions and signature |

Each module must pass the existing 400-line adapter and 120-line function limits without
a new exception. The split creates no second application or deployable phase:
`application.py` remains the only identity/publication owner, and FC-04B moves all three
modules, bootstrap wiring and the root binder together.

## Identity publication and root binding

`easyuse_anima.api.application` owns one private `_APPLICATION` cell with the same
minimal publication rules already used by FC-03B:

- direct module import leaves the cell unbound;
- the private factory publishes only after the complete application has been built;
- publishing the same identity is idempotent;
- publishing a different identity is an error; and
- there is no reset, replacement, close, lock, registry or hot-reload API.

The application cell owns a different identity from
`dependencies._APPLICATION_DEPENDENCIES`; it is not a second dependency or lifecycle
owner. `ApiApplication.dependencies` is exactly the FC-03B object already published in
that dependency cell.

Root `api.py` supplies only two compatibility inputs to the private bootstrap
composition call:

1. the existing root-named logger object, so request-ID/error log identity and direct
   patching of that logger object's methods remain unchanged; and
2. the existing `publish_routes(target)` callback, which updates the root `routes`
   global every time the canonical registrar selects an explicit or host route table.

The callback preserves `api.routes is target` without a proxy module, module
`__getattr__`, assignment interception or a second route-table cell. All other root
application spellings are assigned once as exact aliases from `ApiApplication` or its
compatibility view. Existing static root aliases remain exact canonical aliases; FC-04B
does not delete or deprecate them.

## Construction owner and import direction

The private bootstrap composition entrypoint is the sole production call site of the
canonical factory. It passes the existing eight concrete private composition
operations explicitly:

```text
settings route group
Wildcard/Autocomplete route group
translation route runtime
translation route handler
AiO Torch Compile route handler
LoRA read route group
profile-list route group
profile load/save/mutation/fix route group
```

`application_compatibility.py` imports canonical request/response and feature-service
owners. `application_routes.py` owns the explicit handler dependency wiring.
`application.py` imports those two lower application-composition modules and canonical
dependency/router owners. The application build accepts the bootstrap composition
operations as explicit keyword callables. None of the three modules imports bootstrap
or uses a generic service locator or reflection map.

The resulting direction is acyclic:

```text
root __init__.py
  -> root api.py compatibility binder
     -> easyuse_anima.bootstrap private outer composition
        -> easyuse_anima.api.application factory
           -> api.application_compatibility + api.application_routes
              -> api router/routes + feature services

easyuse_anima.api.application* -X-> bootstrap
easyuse_anima.api.application* -X-> root api.py / root __init__.py
easyuse_anima.api.dependencies -X-> application / bootstrap / root modules
canonical production modules  -X-> root compatibility modules
```

The private composition entrypoint may return the already-published application on an
ordinary repeated call, but it owns no additional lock. Python's import lock and the
publish-once identity rule cover the supported startup sequence. Production module
reload, failed-construction retry, reset and hot shutdown-to-reinitialize remain
unsupported and are not made safer speculatively in FC-04B.

## Exact construction and lifecycle sequence

### Package entrypoint and direct root API load

```text
import root package (or the supported isolated root api.py test loader)
  -> root api.py creates only its compatibility logger/publisher callback
  -> private bootstrap composition call
     -> canonical application factory
        -> guarded host selection
        -> create translation executor/runtime tuple
           -> bootstrap publishes the exact executor identity
        -> create response/payload/runtime-aware helpers
        -> create 21 uncalled handler closures
        -> create ordered definitions and signature
        -> publish the one complete dependency bundle
        -> resolve initial route table and create registrar
        -> publish the complete immutable application identity
  -> root api.py binds exact aliases and returns
  -> root entrypoint calls bootstrap.initialize
     -> same initialize/shutdown lock
     -> register bootstrap.shutdown with atexit once
     -> create/install RuntimeServices
     -> snapshot the application executor shutdown as cleanup item 1 of 7
     -> install translation facade, register routes, initialize Wildcard
```

Application construction remains outside `initialize()`. An exception during canonical
composition aborts the import before application publication and is not converted into
an initialize rollback. No new executor/application construction rollback is invented;
the current pre-initialize ownership boundary remains authoritative.

### Late root API import and repeated initialize

The root entrypoint continues to import the compatibility binder. A later ordinary
`import <package>.api` therefore resolves the cached module and the exact same
application, dependency bundle, executor, helpers, handlers, definitions, registrar,
runtime, cleanup plan, route table and translation facade. It creates no application,
executor, route registration, lifecycle state or atexit callback.

`initialize(); initialize()` remains unchanged: the same runtime and cleanup plan are
retained, the same registrar refreshes the current route table, same-table registration
is idempotent, a new table receives the same 21 definitions, and Wildcard success/OSError
retry behavior is unchanged.

### Direct canonical/no-host imports

```text
import easyuse_anima.api.application
import easyuse_anima.api.dependencies
import easyuse_anima.bootstrap/router/route owners
  -> no application or executor construction
  -> no dependency/application publication
  -> no host dereference, route registration, runtime or atexit state
```

Importing bootstrap may load the application factory definition, but does not call it.

### Failure, shutdown and process exit

Unexpected route or Wildcard failure occurs only after application creation and keeps
the E-09 attempt-created RuntimeServices/facade rollback. It preserves the original
error and does not roll back the pre-created application, executor, routes, marker,
global caches or directories.

`shutdown(); shutdown()` and process `atexit` retain the bootstrap lock and terminal
flag, detach only expected runtime identities and execute the fixed cleanup plan once:

1. application translation executor shutdown;
2. AiO first-pass cache clear;
3. completed Wildcard snapshot clear;
4. Autocomplete index no-op close;
5. completed Autocomplete snapshot clear;
6. expected-identity translation facade restore; and
7. translation service cache close.

There is no route deregistration or marker clear, file-I/O limiter mutation,
provider/client close, application close, lifecycle reset or initialize callback after
terminal shutdown.

## Candidate comparison after FC-03B

| Concrete shape | E-09 timing | canonical/no-host | patch/identity | final owner model | Verdict |
| --- | --- | --- | --- | --- | --- |
| eager singleton constructed while importing `api.application` | executor can precede initialize | **fails** direct canonical import purity | canonical seams can work | canonical identity | rejected |
| root binder directly calls the canonical factory | executor can precede initialize | passes | canonical seams can work | **fails** because root remains the production composition call site | rejected |
| bootstrap stores the application object and root uses a private bootstrap accessor | executor can precede initialize | passes if lazy | seams can work | **fails** canonical application identity ownership and couples the facade to bootstrap state | rejected |
| canonical publish-once application + private bootstrap outer composition + root binder | **passes** | **passes** | **passes** | **passes** | **selected** |
| retain current root production application | **passes** | passes | passes | **fails** original technical Definition of Done | rejected for FC-04 |

FC-03B removes the former root-global patch-time conflict. The selected row is now the
only shape satisfying all gates, so the roadmap's PRO trigger does not fire.

## FC-04B task card

```text
Task / Issue: #593 / FC-04B
Base SHA: latest dev after FC-04A merges
Goal: move the complete API application identity/construction into the private
  canonical application owner, invoke it once through bootstrap private outer
  composition before initialize, and reduce root api.py to an exact binder/facade
Allowed production:
  __init__.py (only if required to preserve the exact entrypoint order)
  api.py
  easyuse_anima/api/application.py (new private identity/publication owner)
  easyuse_anima/api/application_compatibility.py (new private compatibility-parts owner)
  easyuse_anima/api/application_routes.py (new private 21-handler wiring owner)
  easyuse_anima/bootstrap.py
Allowed tests/evidence:
  tests/test_python_api_application_lifecycle_contract.py (new direct owner)
  tests/test_python_api_facade_lifecycle_contract.py
  tests/test_python_api_dependencies_contract.py
  tests/test_api_contract.py
  tests/test_api_contract_compatibility.py
  tests/test_prompt_translation_api.py
  tests/test_python_bootstrap.py
  tests/test_python_runtime_lifecycle_contract.py
  tests/test_python_translation_runtime_contract.py
  tests/test_python_package_skeleton.py
  tests/test_python_import_boundaries.py
  tests/test_python_backend_analyzer.py
  tests/test_python_size_complexity.py
  tests/test_python_compatibility_surface.py
  directly required analyzer, size, lifecycle, compatibility and ownership fixtures
  this Contract, P-API-01, FC-03 Contract, final-convergence roadmap and indexes
Preserve:
  every root symbol and exact canonical alias currently retained by FC-03B;
  one dependency bundle identity and every named call-time leaf patch seam;
  one application/executor, helper, handler, definition, signature and registrar identity;
  exact 21-route order/signature/marker, explicit/new-table registration and root routes publication;
  request parsing, payload/error/status/message/details, request correlation and safe logging;
  profile/translation dynamic compatibility and all file-I/O dispatch behavior;
  package/flat/direct-test import behavior and no-host canonical import purity;
  one bootstrap lock/atexit/terminal owner, pre-initialize construction, cleanup item 1,
  fixed seven-step cleanup, attempt-only rollback, repeated initialize and route refresh
Forbidden:
  RuntimeServices or initialize/shutdown behavior changes; construction inside initialize;
  dynamic cleanup-plan mutation; a second lifecycle lock/atexit/terminal/close/reset owner;
  application close/reset/replacement/hot reload; executor recreation after publication;
  route deregistration/marker clear; file-I/O limiter or provider/client cleanup;
  canonical-to-root or application-to-bootstrap import; public package/bootstrap/router export;
  generic service locator/reflection wiring; root assignment interception or alias deletion;
  a new size/function exception or moving the root overage unchanged to a canonical module;
  repository/schema/persistence/error-policy changes; unrelated cleanup; release/tag/Registry
Focused tests and purpose:
  PythonApiApplicationLifecycleContractTests: import purity, immutable exact fields,
    publish-once identity, bootstrap composition call count and executor/cleanup identity;
  PythonApiFacadeLifecycleContractTests: package -> late root import, repeated initialize,
    same application/executor/handler/registrar/runtime/cleanup/facade/route identities;
  PythonApiDependenciesContractTests: exact FC-03B bundle identity and call-time leaves;
  ApiRouteRegistrationOwnerTests plus direct API module: 21 routes, publication,
    behavior, errors, correlation and current direct loader;
  PythonBootstrapTests and lifecycle/translation-runtime owners: E-09 order and rollback;
  package/no-host, compatibility, import-boundary, analyzer and size-contract owners
Promotion gates:
  changed-file Python syntax and targeted Ruff/Pyright;
  one focused target per runner; current import/analyzer/size projections;
  root api.py below 400 lines and every new api/application* module below the current
    400-line adapter and 120-line function thresholds with no new exception;
  git diff --check; official full once on the exact final candidate SHA;
  comfy node validate, actual pack/archive/CRC/import closure and one extracted-archive
    package -> late-api identity smoke because entrypoint/import/application closure changes;
  isolated live ComfyUI API registration/one representative endpoint only if package smoke
    or direct evidence reveals a host-visible import/registration difference; no browser matrix
Rollback boundary:
  one cohesive Move commit/PR; revert restores root-owned application composition;
  no data, schema, settings or profile migration rollback
Stop conditions:
  preserving an observed contract requires canonical-to-root/application-to-bootstrap import,
  dynamic cleanup-plan mutation, construction inside initialize, a second lifecycle owner,
  safe route deregistration, hot reinitialize/reset, root assignment interception,
  application/executor recreation, supported root-symbol deletion, or Behavior change
Next: FC-05 integrated technical completion audit only after FC-04B merges
```

## FC-04A validation disposition

FC-04A changes documentation only. Existing deterministic owners already prove the
current identity sequence, the FC-03B dependency cell, E-09 cleanup/rollback and
package/no-host behavior. A second machine-readable inventory would duplicate those
owners, so FC-04A adds no fixture or executable test and reuses their focused evidence.

Official full, validate/pack/archive and live/browser checks are not triggered by this
Contract. FC-04B owns the executable and package gates above.
