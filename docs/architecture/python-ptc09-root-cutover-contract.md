# Python PTC-09 Root Canonical Entrypoint Cutover Contract

## Status and authority

- Verdict: **FEASIBLE**.
- PTC-09A is a production-free Contract on
  `dev@5ab3f54c4d6eba930de5bf7a813d0fd89654ad01`.
- PTC-09B becomes READY only after this Contract merges.
- Technical owner: Issue #593; parent architecture owner: Issue #185.
- Lifecycle authority: E-09 / Issue #187 and
  [`python-runtime-e09-lifecycle-contract.md`](python-runtime-e09-lifecycle-contract.md).
- Application authority:
  [`python-api-fc04-application-lifecycle-contract.md`](python-api-fc04-application-lifecycle-contract.md).

This Contract applies the accepted breaking-boundary decision for complete Python
convergence. Root `__init__.py` remains the permanent ComfyUI package entrypoint. The
other nine root Python modules and the seven `anima_prompt` modules are legacy import
paths with no supported consumer requirement; PTC-09B removes them after callers and
tests use canonical owners. No replacement facade, alias package, module `__getattr__`,
or import hook may recreate those paths.

The decision supersedes the old release-N retention gates for these exact 16 paths. It
does not authorize changes to node IDs, workflows, settings, profiles, HTTP routes or
payloads, and it does not change any unrelated compatibility surface.

## Current evidence and identity graph

The current startup graph is:

```text
root __init__.py
  -> root api.py compatibility binder
     -> bootstrap._compose_api_application(...)
        -> api.application._build_api_application(...)
           -> one immutable application/dependencies/executor/handler graph
  -> bootstrap.initialize(register_routes=api.register_routes, ...)
     -> one RuntimeServices identity and fixed seven-item cleanup plan
```

`easyuse_anima.api.application` already owns the publish-once application cell.
`easyuse_anima.bootstrap` already owns the only concrete application-factory call site,
lifecycle lock, atexit registration, installed runtime and shutdown. Root `api.py` owns
no production implementation; it supplies a compatibility logger and route-table
publisher, then binds aliases. Root `nodes.py` is likewise not the registration owner;
`easyuse_anima.registration` owns the deterministic mappings.

The exact identities that must survive PTC-09B are the canonical application,
dependency bundle, translation executor, 21 handlers, ordered route definitions and
signature, registrar, installed runtime and translation facade. Root aliases and the
root `routes` mirror are intentionally retired.

## Root and legacy surface disposition

| Current surface | Classification through PTC-09A | PTC-09B disposition |
| --- | --- | --- |
| root `NODE_CLASS_MAPPINGS`, `NODE_DISPLAY_NAME_MAPPINGS`, `WEB_DIRECTORY` | permanent ComfyUI entrypoint surface | retain with the same values and `__all__` |
| root mapped-class attributes | undeclared compatibility attributes | retire; mappings continue to reference the exact canonical classes |
| root `api` module attribute and `api.py` aliases | legacy/private compatibility and test seams | delete; tests use exact canonical application/feature owners |
| root `_load_comfy_nodes` | private startup helper in the wrong layer | move to private bootstrap composition |
| root `routes` mirror | compatibility observability only | retire; the canonical registrar still resolves and registers the live host table |
| remaining eight flat root shims | legacy import paths | delete after direct callers use canonical owners |
| seven `anima_prompt` modules | legacy package/submodule import paths | delete after direct callers use `easyuse_anima.prompt.anima` |

Importing any deleted path after PTC-09B must fail normally. A test that needs a private
helper imports the exact canonical owner. A test that needs the complete HTTP
application uses a canonical application test harness; it must not synthesize a module
with the old root alias surface.

## Candidate decision

| Candidate | E-09 result | Verdict |
| --- | --- | --- |
| Root directly composes the application and calls `initialize` | preserves timing but leaves concrete composition and callback state in the permanent root entrypoint | reject |
| Move application construction inside `initialize` | changes pre-initialize failure ownership and can miss the executor-before-cleanup boundary | reject |
| Private bootstrap package-start composition, then existing `initialize` | preserves one application, executor-before-cleanup timing, one lifecycle owner and a minimal root entrypoint | **select** |
| New public startup/application API | adds an unnecessary supported surface and lifecycle ambiguity | reject |

Direct evidence leaves one feasible design, so no further PRO review is required.

## Selected canonical sequence

PTC-09B adds one private bootstrap package-start function. It is not added to
`bootstrap.__all__` or any package `__all__`.

```text
ComfyUI imports root __init__.py
  -> import NODE_CLASS_MAPPINGS and NODE_DISPLAY_NAME_MAPPINGS
     from easyuse_anima.registration
  -> call bootstrap._initialize_package()
     -> bootstrap._compose_api_application(
          logger = canonical easyuse_anima.api logger,
          publish_routes = stateless private sink,
        )
        -> application factory returns/publishes the one canonical identity
        -> translation executor exists and is the bootstrap-observed identity
     -> bootstrap.initialize(
          register_routes = application.register_routes,
          initialize_wildcards = canonical wildcard owner,
          load_comfy_nodes = private canonical package loader,
        )
        -> one lock and one atexit registration
        -> one RuntimeServices identity
        -> executor shutdown frozen as cleanup item 1
        -> current host route table refreshed by the canonical registrar
```

The route publisher is deliberately stateless. It does not create another route-table
cell in bootstrap or application state. The registrar continues to resolve the current
host route table on every initialize and to apply the exact marker/signature rules.

Application construction remains before and outside `initialize()`. An application
construction exception still aborts before RuntimeServices rollback begins. An
unexpected initialize failure still preserves the original exception and rolls back
only attempt-created/bound runtime resources by expected identity.

### Repeated initialize, shutdown and direct imports

- Repeated `_initialize_package()` resolves the same application and executor, then
  calls the existing `initialize()` so the same runtime is retained and routes refresh.
- After terminal shutdown, application lookup may return the existing identity, but
  `initialize()` raises before route, wildcard or host callbacks.
- Direct imports of bootstrap or canonical application modules remain import-pure: no
  application composition, host I/O, registration, runtime install or atexit callback.
- There is no supported reload, reset or shutdown-to-reinitialize path.

## E-09 invariant matrix

| Invariant | PTC-09B proof obligation |
| --- | --- |
| one bootstrap lifecycle owner | no new lifecycle state outside bootstrap |
| initialize/shutdown same lock; atexit once | existing functions and lock remain unchanged |
| terminal/idempotent shutdown | post-shutdown package-start reaches the existing pre-callback guard |
| repeated initialize same runtime plus route refresh | call the same registrar on every existing initialize invocation |
| exact one translation executor | canonical application identity is publish-once and composed before initialize |
| executor shutdown cleanup item 1 | keep construction before RuntimeServices cleanup-plan creation |
| fixed seven-step cleanup | no cleanup item or order change |
| rollback and original error | no construction move into initialize and no route rollback |
| registration persistence | no route deregistration or marker clear |
| excluded cleanup | no file-I/O limiter clear, provider close, reset or hot reinitialize |

The package-entrypoint-to-late-legacy-API sequence is intentionally replaced, not
preserved: after PTC-09B the package entrypoint installs the runtime from canonical
owners, while importing `<package>.api` fails because the legacy module is absent. The
canonical application, handler, registrar and executor identities remain available at
their exact canonical owners without creating duplicate lifecycle state.

## PTC-09B task card

```text
Task / Issue:
  PTC-09B / #593, parent #185 and lifecycle ledger #187
Base:
  PTC-09A squash merge on dev
Class:
  BREAKING IMPORT-SURFACE / COHESIVE CUTOVER
Goal:
  make root __init__.py a minimal ComfyUI entrypoint over canonical registration and
  private bootstrap package startup; migrate direct callers/tests; delete the exact 16
  legacy modules without a replacement facade.
Allowed production:
  __init__.py
  easyuse_anima/bootstrap.py
  delete: api.py, api_contract.py, autocomplete_dataset.py, autocomplete_index.py,
          nodes.py, prompt_translation.py, settings.py, storage.py, wildcard_engine.py,
          anima_prompt/__init__.py, correction.py, knowledge.py, models.py,
          normalize.py, ordering.py, parser.py
Allowed support:
  tests/api_test_support.py
  direct API/application/bootstrap/runtime/package/registry-scanner/feature/node tests
  that currently load or assert one of the 16 paths
  replace root-only compatibility tests with one legacy-path-retirement owner
  tests/fixtures/python_compatibility_surface.v1.json
  tests/fixtures/python_file_disposition_contract.v1.json
  tests/fixtures/python_size_complexity_contract.v1.json
  tests/fixtures/python_test_ownership_contract.v1.json
  tests/fixtures/python_support_ownership_contract.v1.json
  tests/fixtures/python_backend_baseline.json
  tools/analyze_nodes_module.py only if its direct target must become canonical
  current compatibility/total-convergence/roadmap/index documentation
Forbidden:
  changes to canonical feature behavior, application/router construction or public API
  new public bootstrap/package export, replacement facade/import hook
  second lifecycle lock/atexit/cleanup cell, reset/hot reload, dynamic cleanup mutation
  route deregistration/marker clear, file-I/O limiter cleanup, provider close
  node ID/workflow/schema/settings/profile/API route/payload/error-policy changes
  release, tag or Registry work
Preserve:
  canonical application/dependency/executor/handler/definition/signature/registrar identity
  exact 21-route order/signature/idempotence and current-table refresh
  repeated initialize runtime identity, fixed seven-step cleanup and rollback behavior
  root mappings and WEB_DIRECTORY values; canonical class identity and metadata
Focused edit loop:
  changed-file Python syntax/static
  legacy-path absence and minimal root-entrypoint contract
  canonical application/package-start/late-canonical identity contract
  bootstrap/runtime/E-09 lifecycle contracts
  direct API/profile/translation/wildcard/autocomplete/node contracts touched by caller migration
  import-boundary/analyzer/disposition/size/support/package-skeleton owners
  git diff --check
Promotion:
  official full exactly once on the final candidate SHA
  validate/pack/archive, extracted no-host import, installed package identity/route smoke
Live trigger:
  one isolated ComfyUI package import plus representative API and registered-node execution
Rollback:
  revert the one PTC-09B cutover/deletion PR; do not partially restore selected shims
Stop:
  a real supported external consumer of a deleted Python import path is demonstrated;
  preserving runtime behavior requires construction inside initialize, a second lifecycle
  owner, dynamic cleanup-plan mutation, canonical-to-root import, or route rollback.
Next:
  PTC-10 production-free total Python convergence completion audit
```

## PTC-09A validation and rollback

PTC-09A changes documentation only. Validate its sequence and path inventory against
the current entrypoint, bootstrap, canonical application/router, registration,
lifecycle contracts and deterministic disposition fixture, then run `git diff --check`.
Official full, package and live checks are not triggered. Rollback is one documentation
PR. PTC-09B owns executable proof of the new sequence.
