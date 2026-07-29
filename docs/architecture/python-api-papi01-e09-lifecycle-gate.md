# P-API-01 API Facade / E-09 Lifecycle Compatibility Gate

## Status and authority

- Status: active prerequisite for P-API-01.
- Active task: Issue #582.
- Parent/compatibility ledger: Issues #185 and #186.
- Lifecycle authority: [`python-runtime-e09-lifecycle-contract.md`](python-runtime-e09-lifecycle-contract.md).
- Baseline: `dev` after P-WC-02 / PR #581.
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

## 7. Future conflict guards

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

## 8. Stop and PRO conditions

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

## 9. Codex resume instruction

```text
Start Issue #582 / P-API-01 from latest origin/dev.

Read only:
- current-policies.md
- codex-execution-efficiency.md universal rules
- post-phase-e-maintenance-roadmap.md P-API-01 section
- this E-09 compatibility gate
- Issue #582 and #186 latest checkpoints
- root __init__.py and api.py
- easyuse_anima/bootstrap.py, runtime.py, api/router.py
- E-09 lifecycle, API route-owner, compatibility, package/no-host direct tests

Do not implement P-API-02.
Do not reread all D/E history or every route module.

Inventory exact identities, creation order, late root import behavior, public/private
seams, and import cycles. Compare candidate A/B/C against every E-09 invariant.
Return FEASIBLE or RETAIN and, only if feasible, one bounded P-API-02 task card.

No production change, root removal, reset/hot-reload support, deprecation warning,
release, tag, or Registry action.
```
