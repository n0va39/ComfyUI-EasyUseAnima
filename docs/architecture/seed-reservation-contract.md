# Backend seed reservation contract

- Owner issue: [#167](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/167)
- Roadmap unit: S167-01
- PR type: Contract
- Inventory baseline: `dev` commit
  `ddcc2517f0286fd4e249ff18b09e80a8a64e3dc7`

This document freezes the request and service boundary needed before backend
seed reservation behavior is implemented. S167-01 does not reserve, advance,
commit, release, retry, or cancel a seed.

## Current inventory

### Symbols and owners

| Surface | Current owner | Contract evidence |
| --- | --- | --- |
| AiO legacy sentinels | `easyuse_anima.aio.generation_normalization` | `AIO_SPECIAL_SEED_RANDOM = -1`, `AIO_SPECIAL_SEED_INCREMENT = -2`, `AIO_SPECIAL_SEED_DECREMENT = -3` |
| AiO input normalization | `easyuse_anima.aio.generation_normalization._normalize_aio_seed` | Values are normalized into the legacy `-3..MAX_SEED` range |
| AiO execution seed | `easyuse_anima.aio.sampling._resolve_aio_runtime_seed` | All three legacy sentinels currently become a fresh random seed in backend execution |
| AiO browser reservation | `web/js/aio/generator_queue_runtime.js` | A per-runtime `WeakMap` reserves concrete seeds and settles accepted/rejected calls in FIFO order |
| Prompt Studio browser reservation | `web/js/prompt_studio/advanced_queue_seed_runtime.js` | A separate runtime injects a version-1 hidden next-seed payload |
| Prompt Studio backend payload consumer | root `nodes.py._consume_reserved_wildcard_next_seed` | Consumes and removes the hidden payload from request-local inputs and the workflow prompt |
| Prompt Studio seed arithmetic | root `wildcard_engine.py` and `web/js/prompt_studio/wildcard_seed_contract.js` | Fixed/randomize/increment/decrement use the JavaScript-safe public range for advanced controls |
| Runtime composition | `easyuse_anima.runtime.RuntimeServices` | Only the Comfy host provider is composed; no backend seed-reservation service exists |

### Callers and aliases

- `_resolve_aio_runtime_seed` is called by AiO sampling, legacy generation, and
  output paths. Root `nodes.py` retains direct compatibility aliases for the
  AiO special-seed constants and normalization/sampling helpers.
- `_consume_reserved_wildcard_next_seed` has exactly two production callers:
  `easyuse_anima.nodes.prompt_advanced_nodes` and
  `easyuse_anima.nodes.regional_nodes`.
- Those two node adapters receive the root consumer through
  `_bind_prompt_advanced_node_runtime` and `_bind_regional_node_runtime`.
  B-11c30c2b cannot retire those binders until a separate Move supplies a
  canonical behavior-preserving consumer.
- No Python service or request object currently represents a reservation.

### Existing payloads

The Prompt Studio hidden payload is version 1:

```json
{
  "version": 1,
  "current_seed": 42,
  "next_seed": 43,
  "mode": "populate",
  "control": "increment"
}
```

It is a browser-computed compatibility payload, not an authoritative backend
reservation. AiO has no equivalent reservation payload: its serialized sampler
settings contain `seed` and `seed_after_generate`, and the browser replaces a
legacy sentinel with a concrete seed before queue submission when the extension
is loaded.

### Mutable and request-local state

- AiO browser reservation state is a `WeakMap` local to one queue runtime.
- Prompt Studio browser reservation state is local to its queue runtime and
  settles the hidden payload after the queue result.
- Backend execution owns no reservation map, lock, token, or lifecycle state.
- The root Prompt Studio consumer mutates only the passed request dictionaries
  by removing its hidden compatibility input.
- `RuntimeServices` owns no seed state.

## S167-01 contract

The canonical package boundary is `easyuse_anima.seed.reservation`.

### Request

`SeedReservationRequest` carries:

- `schema`: `easyuse_anima_seed_reservation_request`;
- `version`: contract version 1;
- `stream_id`: stable logical seed stream identity;
- `request_id`: idempotency identity for one queue request;
- `selection`: `concrete`, `randomize`, `increment`, or `decrement`;
- `seed`: a non-negative concrete seed only when `selection` is `concrete`;
- `after_generate`: `fixed`, `randomize`, `increment`, or `decrement`.

The request contains intent only. It does not contain a browser-authoritative
`next_seed`.

### Reservation and settlement

`SeedReservation` carries the service-selected concrete execution seed,
candidate accepted `next_seed`, and opaque reservation identity.
`SeedReservationSettlement` is one of `accepted`, `rejected`, or `cancelled`.

`SeedReservationService` exposes only:

1. `reserve(request) -> SeedReservation`;
2. `settle(reservation_id, settlement) -> None`.

Atomic ordering, seed arithmetic, random generation, idempotent settlement,
late acceptance, retry, cancellation, storage lifetime, and cleanup are
S167-02 Behavior. The browser compatibility/display cutover is S167-03.

### Legacy compatibility parsing

The compatibility parser accepts an already normalized legacy seed value:

| Legacy value | Selection |
| --- | --- |
| `-1` | `randomize` |
| `-2` | `increment` |
| `-3` | `decrement` |
| `0` or greater | `concrete` with the same seed |

Other negative values are invalid at this boundary. Existing AiO normalization
continues to own coercion and clamping until a later separately classified
migration. The parser does not select a concrete seed or consult mutable state.

## Allowed-file boundary

S167-01 may change only:

- `easyuse_anima/__init__.py`;
- `easyuse_anima/seed/__init__.py`;
- `easyuse_anima/seed/reservation.py`;
- `tests/test_seed_reservation_contract.py`;
- `tests/test_python_backend_analyzer.py`;
- `tests/fixtures/python_backend_baseline.json`;
- `docs/architecture/seed-reservation-contract.md`;
- `docs/architecture/python-backend-execution-roadmap.md`.

The root and seed package initializers may privately import only the
side-effect-free seed contract modules needed to keep shipped modules inside
the runtime import closure. Their existing empty public `__all__` surfaces must
remain unchanged. The analyzer test and baseline fixture may change only by
that deterministic module-inventory delta. These are contract/gate
maintenance, not a Move or Behavior change.

S167-01 must not change:

- root `nodes.py` or `wildcard_engine.py`;
- AiO generation, sampling, or output modules;
- Prompt Studio or AiO frontend files;
- `RuntimeServices`, bootstrap, registration, routes, or workflow schemas;
- existing hidden payload bytes;
- seed arithmetic, random generation, queue ordering, failure, retry, or
  cancellation behavior;
- B-11c30c2b binders.

## Follow-up rollback units

1. **S167-01 Contract:** add the pure request/result/service types and legacy
   parser described here.
2. **S167-01a Seed consumer Move:** move the existing root hidden-payload
   consumer to a canonical owner without changing bytes, mutations, validation,
   or return values.
3. **B-11c30c2b Move:** retire the Advanced and Regional node-adapter binders
   against that canonical owner.
4. **S167-02 Behavior:** implement the authoritative atomic backend service and
   lifecycle.
5. **S167-03 Adapter:** reduce browser interceptors to compatibility/display
   adapters and prove browser/headless parity.

No step may copy the current root consumer, import root `nodes.py` from the
canonical package, or mix reservation behavior into a Move.

## S167-01a seed consumer Move gate

- PR type: Move
- Implementation: PR #344
- Inventory baseline: `dev` commit
  `55376cb121fc05817c42d459983ab3c988fd13fb`
- Canonical target:
  `easyuse_anima.seed.compatibility._consume_reserved_wildcard_next_seed`

### Symbol, caller, alias, and state inventory

- Root `nodes.py` owns the consumer plus
  `WILDCARD_RESERVED_NEXT_SEED_INPUT` and
  `WILDCARD_QUEUE_MAX_SAFE_SEED`.
- The consumer uses `_single_value`, JSON parsing, and call-time Wildcard mode,
  control, normalization, and public-safe seed values. It owns no mutable global
  state.
- The only production callers remain the Advanced and Regional build paths.
  Both observe the root name through their existing runtime binders.
- Tests exercise valid reservation acceptance, invalid-reservation scrubbing,
  fallback seed generation, workflow-prompt mutation, and root patch seams.
- `wildcard_engine.py` remains the pre-D-12 owner of Wildcard mode and seed
  normalization. The canonical compatibility consumer may resolve that module
  at call time, matching the existing no-eager-NumPy wrapper pattern; it may not
  import root `nodes.py`, copy Wildcard behavior, or add a callback contract.

### Allowed-file boundary

S167-01a may change only:

- `nodes.py`;
- `easyuse_anima/seed/__init__.py`;
- `easyuse_anima/seed/compatibility.py`;
- `tests/test_seed_compatibility.py`;
- `tests/test_wildcards.py`;
- `tests/test_nodes_module_analyzer.py`;
- `tests/test_python_backend_analyzer.py`;
- `tests/test_python_compatibility_surface.py`;
- `tests/fixtures/python_backend_baseline.json`;
- `tests/fixtures/python_compatibility_surface.v1.json`;
- `docs/architecture/seed-reservation-contract.md`;
- `docs/architecture/python-backend-execution-roadmap.md`;
- `docs/architecture/python-compatibility-shims.md`;
- `docs/architecture/comfy-host-provider-bridge.md`.

S167-01a must preserve:

- the exact hidden input name and version-1 JSON payload;
- input and workflow-prompt pop order;
- accepted modes, controls, seed bounds, and normalization;
- every `None`/seed return value;
- Advanced/Regional binder definitions and import-time calls;
- browser, AiO, reservation-service, RNG, arithmetic, queue, retry,
  cancellation, and settlement behavior.

The root function and constants remain direct compatibility aliases during this
Move. B-11c30c2b owns their node-adapter binder retirement separately.

The deterministic compatibility audit records 284 canonical root bindings,
zero residual root functions, 24 residual root globals, and the unchanged 16
runtime binders. The whole-backend inventory records 89 shipped and reachable
Python modules with no missing internal imports.

## S167-01b seed-domain Contract gate

- State: COMPLETE IN PR #357
- PR type: Contract
- Baseline: `dev` commit
  `8cde31a9db6968bd71a45c3bfc19c086179caf66`
- Production consumers: none; S167-02 and S167-03 have not started

### Blocker found before S167-02

The version-1 request distinguishes selection and after-generate intent but
does not identify the arithmetic domain. The existing consumers cannot share
one implicit rule:

- AiO's editable browser domain is `0..1125899906842624` and its current queue
  arithmetic clamps at both ends;
- Prompt Studio's editable browser domain is
  `0..9007199254740991` and its current queue arithmetic wraps at both ends;
  and
- Python keeps accepting a concrete legacy seed through
  `18446744073709551615`. Fixed mode preserves that value, while browser
  arithmetic cannot safely publish the full uint64 range.

Inferring a policy from `stream_id`, node names, or the current seed would make
the service feature-aware and would make extension-loaded and headless requests
diverge. S167-02 therefore remains blocked until the request carries an
explicit arithmetic maximum and overflow policy.

### Symbol, caller, alias, and state inventory

- `SeedReservationRequest`, `parse_seed_reservation_request`, and
  `parse_legacy_seed_reservation_request` are the only contract symbols that
  need the missing domain.
- No production caller constructs either parser request. Current callers are
  the contract tests only, so the pre-adapter contract can advance without
  workflow or payload migration.
- `SeedReservation`, `SeedReservationService`, and settlement values do not
  need a signature change.
- No root compatibility alias exposes the reservation contract.
- Backend reservation maps, locks, RNG, counters, stream state, and cleanup
  state are still absent. This Contract must not add them.

### Contract amendment

Advance the contract version and add two required request values:

- `next_seed_max`: the inclusive maximum used only for random selection and
  increment/decrement arithmetic; and
- `overflow`: `clamp` or `wrap`.

Concrete execution seeds remain valid through uint64 maximum. Fixed
after-generate preserves the concrete execution seed even when it is above the
arithmetic maximum. S167-02 owns the exact arithmetic and lifecycle tests;
S167-03 supplies each adapter's existing reviewed domain explicitly.

### Implementation result

- the contract version advances from 1 to 2 before any production consumer is
  connected;
- `SeedReservationRequest` requires validated `next_seed_max` and `overflow`;
- concrete request and result seeds are bounded to uint64, independently from
  the smaller next-seed arithmetic maximum;
- both existing domains are representable without feature-name inference:
  AiO's `2^50` clamp domain and Prompt Studio's JavaScript-safe wrap domain;
- version 1, missing/invalid domains, booleans, negative bounds, and values
  above uint64 fail closed; and
- no production caller, state owner, RNG, lock, runtime, workflow, node, or
  frontend surface changes in this Contract.

### Validation result

- focused contract/import/analyzer checkpoint: 13 tests passed;
- additional uint64 result-boundary check: 1 test passed;
- Python compile and `git diff --check`: passed; and
- the official full runner passed once in 50.2 seconds: 988 Python tests and
  frontend checks for 114 JavaScript files, with the Pyright baseline and all
  six import-boundary groups passing.

### Allowed-file boundary

S167-01b may change only:

- `easyuse_anima/seed/reservation.py`;
- `tests/test_seed_reservation_contract.py`;
- `tests/fixtures/python_backend_baseline.json`;
- `docs/architecture/seed-reservation-contract.md`; and
- `docs/architecture/python-backend-execution-roadmap.md`.

The analyzer fixture may change only by the deterministic contract-symbol and
signature delta in the existing module.

Forbidden:

- reservation maps, locks, RNG, counters, settlement, retry, cancellation, or
  cleanup behavior;
- `RuntimeServices`, bootstrap, routes, node adapters, AiO/Prompt execution,
  root shims, frontend files, workflows, or hidden payload bytes;
- changing current AiO or Prompt Studio seed bounds/arithmetic; and
- beginning S167-02 Behavior or S167-03 Adapter work.

Exit:

- the request cannot be constructed without an explicit domain;
- version-1 requests fail closed before any state exists;
- uint64 concrete seeds and both reviewed arithmetic domains are represented
  without JavaScript-unsafe numeric policy inference; and
- focused contract/import/analyzer gates pass.

## S167-02 authoritative service Behavior gate

- State: VALIDATED in PR #358; `dev` merge pending
- PR type: Behavior
- Baseline: `dev` commit
  `e187f4949651e88057403517e3305cc4150e44d9`
- Prerequisites: S167-01, S167-01a, B-11c30c2b, and S167-01b complete

### Symbol, caller, alias, and global-state inventory

- The existing public port is
  `easyuse_anima.seed.reservation.SeedReservationService`; no implementation
  exists.
- `RuntimeServices` currently owns only `ComfyHostProvider`. Bootstrap creates
  one process runtime and has no seed state.
- Production callers of `reserve` and `settle` remain zero. S167-03 owns node,
  route, prompt-payload, and browser adapters.
- No root compatibility alias exposes the port or a future implementation.
- Backend reservation maps, locks, reservation IDs, stream state, accepted
  idempotency history, RNG, and cleanup state are all absent.
- Current frontend owners provide the behavior reference only: per logical
  stream, reservations are allocated synchronously, settle in FIFO order,
  accepted entries advance state, rejected trailing entries become reusable,
  and accepted state remains authoritative after publication failure.

### Locked behavior

One process-lifetime `InMemorySeedReservationService` is injected explicitly
into `RuntimeServices`. Its single re-entrant lock owns every state transition.

Reservation:

- an exact duplicate `(stream_id, request_id)` returns the same pending or
  accepted result without consuming RNG or advancing state;
- reusing the identity with different request data is a conflict;
- concrete selection establishes or explicitly resets an idle stream. Repeated
  requests carrying the last observed concrete seed consume the service's
  accepted/tail state so concurrent increment/randomize controls do not reuse a
  seed. A concrete edit made while requests are pending takes effect only after
  the pending epoch drains, matching current browser ownership;
- random selection always draws from `0..next_seed_max`;
- increment/decrement selection uses the reserved tail, then committed state,
  and falls back to one random draw when neither exists; and
- fixed preserves the execution seed. Other after-generate controls compute
  `next_seed` from the explicit version-2 domain. Clamp saturates; wrap cycles.

Settlement:

- the first settlement is terminal and later/duplicate/unknown settlements are
  no-ops;
- accepted results commit only when every earlier reservation in the same
  stream has settled;
- rejected and cancelled results never commit and make their request identity
  immediately retryable;
- contiguous rejected/cancelled tails collapse immediately so a retry can reuse
  the earliest uncommitted candidate; and
- a caller cancellation followed by a late acceptance cannot resurrect or
  advance the cancelled reservation.

Lifetime and bounds:

- the implementation is process-local and has no persistence or implicit
  timeout;
- active reservation records are bounded; capacity exhaustion fails before
  mutating stream state;
- accepted idempotency records and retired reservation IDs use bounded LRU
  histories;
- inactive streams use bounded LRU retention, while streams with active
  reservations are never evicted; and
- S167-03 must settle every reservation. Runtime shutdown/route lifecycle and
  persistence remain separate E-09 work.

### Allowed-file boundary

Production:

- `easyuse_anima/seed/service.py`;
- `easyuse_anima/runtime.py`; and
- `easyuse_anima/bootstrap.py`.

Supporting:

- `tests/test_seed_reservation_service.py`;
- `tests/test_runtime_services.py`;
- `tests/comfy_host_fakes.py`;
- `tests/test_comfy_host_wiring.py`;
- `tests/test_python_package_skeleton.py`;
- `tests/test_python_backend_analyzer.py`;
- `tests/fixtures/python_backend_baseline.json`;
- `docs/architecture/seed-reservation-contract.md`; and
- `docs/architecture/python-backend-execution-roadmap.md`.

Forbidden:

- changing the version-2 request/result/port Contract;
- root shims, node adapters, routes, workflow schemas, hidden payloads, AiO or
  Prompt Studio execution paths, or frontend files;
- browser/headless cutover, queue-hook replacement, or UI publication;
- persistent storage, cross-process coordination, background cleanup threads,
  implicit timeout settlement, or broad RuntimeServices lifecycle work; and
- #169 stage/cache Behavior or Phase D consolidation.

Exit:

- focused arithmetic, idempotency, concurrency, out-of-order FIFO,
  reject/retry, cancel/late-accept, capacity, LRU, and runtime-composition tests
  pass;
- import/package/analyzer gates include the implementation without host or
  filesystem side effects;
- the official full runner passes once; and
- S167-03 receives one composed backend owner without frontend or node behavior
  changing in this PR.

### Implementation checkpoint

PR #358 adds `InMemorySeedReservationService` as the sole process-local owner
and injects one instance through bootstrap into `RuntimeServices`.

- The service uses one re-entrant lock and keeps no module-level mutable state.
- Default bounds are 1,024 retained streams, 4,096 queued reservation records,
  4,096 accepted idempotency records, and 4,096 retired reservation IDs.
- Stream arithmetic domains are immutable while retained; a different
  `next_seed_max` or overflow policy is an explicit conflict rather than an
  inferred migration.
- Focused service, concurrency, runtime-composition, package-import, and
  analyzer gates pass. The production files also pass strict Pyright.
- The official full gate passed once: 1,012 Python tests, 114 frontend files,
  the 77-file Pyright baseline ratchet, and all six import-boundary groups.
- Production `reserve` and `settle` callers remain zero. S167-03 still owns all
  adapters and behavior cutover.

## S167-03a adapter cutover Contract/docs gate

- State: READY
- PR type: Contract/docs/gate
- Baseline: `dev` commit
  `d61749a5a1e40714037c7b00741bd92a209ff8e2`
- Production changes: forbidden

### Blocker found before adapter implementation

The version-2 service Contract defines idempotent request identities and
terminal settlement values, but it does not define how a headless Comfy
execution obtains its request identity or when a reservation becomes accepted.
The current browser interceptors settle on the `/prompt` response. A node-only
backend adapter instead first runs after queue validation and can observe
execution success, failure, or interruption.

Inferring these missing rules independently in the AiO and Prompt Studio
adapters would create two authorities and make browser/headless parity
unprovable. S167-03 therefore starts with this production-free gate.

### Symbol, caller, alias, and state inventory

Backend:

- `RuntimeServices.seed_reservations` owns the sole process service.
  Production `reserve` and `settle` callers are still zero.
- `EasyUseAnimaAIOGenerator.generate` receives Comfy `UNIQUE_ID`, `PROMPT`, and
  `EXTRA_PNGINFO`, but no prompt/request ID. Its `IS_CHANGED` and
  `_run_aio_legacy_generation` paths still resolve special seeds through
  `_resolve_aio_runtime_seed`.
- Advanced and Regional Prompt Studio nodes receive `UNIQUE_ID`. Their
  `IS_CHANGED` and `build` methods still use browser-mutated concrete seed
  inputs and the version-1 hidden next-seed compatibility payload.
- Comfy v0.27.0 exposes `prompt_id`, effective `node_id`, and `list_index`
  through `comfy_execution.utils.get_executing_context()`. EasyUseAnima has no
  canonical execution-context adapter and must not import that host module at
  package import time.
- Root `nodes.py` retains direct compatibility aliases for
  `_resolve_aio_runtime_seed`, `_consume_reserved_wildcard_next_seed`, and the
  two hidden-payload constants. D-12, not S167-03, owns their final root
  retirement.

Frontend:

- `web/js/aio/generator_queue_runtime.js` owns a `WeakMap` reservation queue,
  rewrites queued generation settings/workflow values, and publishes accepted
  seed state.
- `web/js/prompt_studio/advanced_queue_seed_runtime.js` owns a second state
  machine, injects the version-1 hidden next-seed payload, rewrites prompt and
  workflow values, and guards executed seed publication.
- Prompt Studio already consumes backend `onExecuted` wildcard seed values.
  AiO `onExecuted` currently updates status/preview only and has no backend seed
  display payload.
- Both interceptors are installed through the replacement-safe host-hook
  registry. Their state and queue callbacks must be retired, not left as a
  second fallback authority.

Global state:

- backend state is bounded and process-local inside
  `InMemorySeedReservationService`;
- browser AiO state is weakly keyed per node;
- browser Prompt Studio state is keyed by graph/node identity and also retains
  detached-state guards; and
- no shared execution-identity, adapter-session, or backend UI-publication
  state exists.

### Locked execution identity

S167-03b defines one side-effect-free execution identity contract and one
call-time Comfy host adapter.

- Effective identity fields are `prompt_id`, `node_id`, and optional
  `list_index`.
- A backend request ID is namespaced by feature and encodes all three fields.
  The list index distinguishes repeated mapped calls in one prompt.
- A stream ID is namespaced by feature and stable effective node ID. It never
  includes the prompt ID, so accepted state continues across queues.
- Comfy execution context is authoritative when available. The hidden
  `UNIQUE_ID` is the compatibility fallback and must not override a different
  effective context node ID.
- Older/test hosts with a stable `UNIQUE_ID` but no execution context use a
  fresh opaque request ID and retain the stable stream ID.
- A call with neither an execution-context node ID nor a usable `UNIQUE_ID`
  does not mutate the authoritative service and follows the existing isolated
  legacy/test path.
- The host adapter imports `comfy_execution.utils` only at call time, returns a
  validated value or `None`, owns no mutable state, and does not expand the
  four-method `ComfyHostProvider` E-02a contract.

### Locked settlement and cache timing

S167-03c supplies one shared backend execution-session adapter.

- reserve occurs after input normalization and before the first seed-dependent
  operation;
- a normal adapter return settles `accepted`;
- a host interruption settles `cancelled` and is re-raised;
- every other `BaseException` settles `rejected` and is re-raised;
- retry of the same Comfy execution identity is therefore allowed after
  rejection/cancellation, while duplicate successful callbacks remain
  idempotent; and
- browser queue acceptance alone no longer advances seed state. Browser and
  headless paths both commit on successful backend node execution.

Cache policy is explicit:

- concrete selection with `fixed` after-generate remains cacheable;
- randomize/increment/decrement selection or any non-fixed after-generate
  control must force node execution;
- cache forcing belongs to the feature node adapter, not the shared service;
  and
- accepted service state remains authoritative if UI publication fails.

### Compatibility and publication

- Existing AiO `-1/-2/-3` serialized settings remain valid and are translated
  through the version-2 legacy parser.
- Existing concrete seeds and the AiO `2^50` clamp domain remain unchanged.
- Prompt Studio keeps its JavaScript-safe wrap domain and existing wildcard
  mode normalization.
- Old browser bundles may continue sending concrete queue rewrites and the
  version-1 hidden Prompt Studio payload. Backend adapters scrub that payload
  but never accept its browser-selected next seed as authoritative.
- No workflow schema, node socket, widget order, hidden-input name, or saved
  workflow byte is added for the new service.
- Prompt Studio continues publishing the accepted `next_seed` through its
  existing `onExecuted` payload.
- AiO adds one backend executed-seed display payload without changing its three
  output sockets or metadata JSON schema.
- New browser code consumes executed display values and retires queue seed
  reservation/state transitions. It may keep only serialization, control, and
  display adapters.

### Rollback units

1. **S167-03a Contract/docs gate:** this production-free identity, settlement,
   cache, compatibility, and validation ownership gate.
2. **S167-03b Execution identity Contract:** pure types plus the call-time Comfy
   execution-context adapter; no reservation caller.
3. **S167-03c Execution session Behavior:** shared reserve/settle exception-safe
   adapter; no feature-node or browser caller.
4. **S167-03d Prompt Studio cutover Behavior:** Advanced and Regional backend
   callers, cache policy, hidden-payload scrub, executed display publication,
   and Prompt Studio interceptor retirement.
5. **S167-03e AiO cutover Behavior:** AiO backend caller, cache policy, executed
   display publication, AiO interceptor retirement, and final
   browser/headless/old-bundle parity evidence.

S167-03d and S167-03e may not share a PR. Both are Behavior units, but they
modify different node schemas, domains, display payloads, frontend owners, and
regression matrices.

### Validation ownership

- S167-03a: Markdown/diff/cross-reference checks only; no production surface
  changed, so PR #358 full evidence is reused.
- S167-03b and S167-03c: focused contract/import/service tests. They have zero
  feature production callers, so they do not repeat the official full.
- S167-03d: focused Prompt Studio Python/Node smoke plus one official full.
- S167-03e: focused AiO Python/Node smoke, one official full, and final isolated
  Legacy/Node 2.0 browser plus headless API parity.
- A failed official full is classified once. Deterministic docs/fixture drift
  after a successful full does not trigger another full run.

### Allowed-file boundary

S167-03a may change only:

- `docs/architecture/seed-reservation-contract.md`; and
- `docs/architecture/python-backend-execution-roadmap.md`.

Forbidden:

- every Python, JavaScript, JSON fixture, workflow, metadata, and test file;
- creating a service caller, execution-context adapter, route, hidden payload,
  node input, browser hook, or migration;
- changing service state, bounds, arithmetic, settlement, or compatibility
  aliases; and
- #169 stage/cache Behavior, D-12 root retirement, E-09 lifecycle, release, or
  Registry work.

Exit:

- execution identity, settlement timing, cache forcing, old-bundle policy,
  display ownership, rollback units, and validation ownership are explicit;
- the diff contains only the two allowed Markdown files; and
- S167-03b can begin without feature-specific inference.

## S167-03b execution identity Contract record

- State: VALIDATED; `dev` merge pending
- PR type: Contract
- Baseline: `dev` commit
  `eedaea110612c4cb0523e5b45fa470e1b786f7b0`
- Feature reservation callers: zero

### Implemented boundary

`easyuse_anima.seed.execution_identity` now owns:

- immutable validated `SeedExecutionContext` and `SeedExecutionIdentity`
  values;
- call-time-only discovery of
  `comfy_execution.utils.get_executing_context()` with no host import or cache
  at package import time;
- context-authoritative request identity from feature, `prompt_id`, effective
  `node_id`, and optional `list_index`;
- stream identity from feature and stable effective node ID;
- stable hidden `UNIQUE_ID` fallback streams with a fresh opaque request ID;
  and
- collision-safe, versioned JSON component encoding instead of delimiter
  concatenation.

Malformed or unavailable host context returns `None` from the host adapter.
When neither that context nor a usable hidden node ID exists, identity
resolution also returns `None`; no reservation service can be mutated by this
Contract alone.

### Caller, alias, and state delta

- `reserve` and `settle` production caller counts remain zero.
- The seed package privately imports the new module so the shipped runtime
  closure remains complete; no public package re-export was added.
- `ComfyHostProvider` remains the frozen four-method E-02a capability port.
- Root `nodes.py`, feature nodes, browser hooks, workflow schemas, and
  compatibility aliases are unchanged.
- The module owns no mutable global, context cache, reservation, or background
  lifecycle.

### Validation

- focused identity, package-skeleton, analyzer-fixture, and import-boundary
  checks: 22 tests passed;
- strict Pyright on the new production module: 0 errors and 0 warnings;
- Python compile: passed;
- Comfy v0.27.0 call-time host import smoke outside active execution: safely
  returned `None`; and
- official full: intentionally not run because this unit has zero feature
  callers and S167-03a assigns full ownership to the cutover Behavior units.

### Allowed-file boundary

S167-03b may change only:

- `easyuse_anima/seed/__init__.py`;
- `easyuse_anima/seed/execution_identity.py`;
- `tests/test_seed_execution_identity.py`;
- `tests/test_python_package_skeleton.py`;
- `tests/test_python_backend_analyzer.py`;
- `tests/fixtures/python_backend_baseline.json`;
- `docs/architecture/seed-reservation-contract.md`; and
- `docs/architecture/python-backend-execution-roadmap.md`.

Forbidden:

- a production `reserve` or `settle` caller;
- feature-node, browser, workflow, metadata, route, or hidden-input changes;
- changes to reservation arithmetic, settlement, capacity, or cache policy;
- expanding `ComfyHostProvider`; and
- S167-03c session behavior, S167-03d/03e cutover, #169, D-12, release, or
  Registry work.

Exit:

- one canonical context/identity adapter exists with no mutable state;
- headless, mapped-call, older-host, malformed-host, and missing-identity
  behavior is explicit and focused-tested; and
- S167-03c can own reserve/settle exception behavior without inferring host
  identity rules.

## S167-03c execution session Behavior record

- State: VALIDATED; `dev` merge pending
- PR type: Behavior
- Baseline: `dev` commit
  `dc4b81f3252111bc202bbad730e72aaab32fc56e`
- Feature reservation callers: zero

### Implemented boundary

`easyuse_anima.seed.execution_session.seed_execution_session()` now owns the
complete lifetime of one already-normalized reservation request:

- `reserve` occurs before the wrapped body starts;
- normal body return settles `accepted`;
- Comfy's `InterruptProcessingException` settles `cancelled`;
- every other `BaseException` settles `rejected`;
- the original body exception is re-raised after settlement;
- a reserve failure never attempts settlement; and
- interruption-classifier failure cannot mask the body exception and falls
  back to `rejected`.

The interruption classifier consults only an already-loaded
`comfy.model_management` module through `sys.modules`. It never imports Comfy,
Torch, or another host dependency. This is sufficient during a real Comfy
execution because the raised exception's defining module is already loaded.

### Procedure correction from observed validation

An isolated Comfy v0.27.0 interpreter probe imported
`comfy.model_management`, printed a successful `True` match, but exceeded the
10-second watchdog while the heavy Torch host finished initialization. That
probe is not counted as a passing smoke and was not repeated. The production
classifier was changed to loaded-module lookup, and final live classification
ownership remains with S167-03d/03e where Comfy is already running.

### Caller, alias, and state delta

- Production `reserve` and `settle` feature caller counts remain zero.
- The seed package privately imports the session module only to keep the
  shipped runtime closure complete.
- No mutable global, pending session registry, reservation duplicate, or
  background lifecycle was added.
- `RuntimeServices`, `ComfyHostProvider`, root aliases, feature nodes, browser
  hooks, workflow schemas, and cache behavior remain unchanged.

### Validation

- focused session, reservation-service, package-skeleton, analyzer-fixture,
  and import-boundary checks: 46 tests passed;
- strict Pyright on the new production module: 0 errors and 0 warnings;
- Python compile: passed; and
- official full: intentionally not run because this unit has zero feature
  callers and S167-03a assigns full ownership to S167-03d/03e.

### Allowed-file boundary

S167-03c may change only:

- `easyuse_anima/seed/__init__.py`;
- `easyuse_anima/seed/execution_session.py`;
- `tests/test_seed_execution_session.py`;
- `tests/test_python_package_skeleton.py`;
- `tests/test_python_backend_analyzer.py`;
- `tests/fixtures/python_backend_baseline.json`;
- `docs/architecture/seed-reservation-contract.md`; and
- `docs/architecture/python-backend-execution-roadmap.md`.

Forbidden:

- a feature-node or browser reservation caller;
- workflow, metadata, route, socket, widget, or hidden-input changes;
- changes to identity, reservation arithmetic, capacity, or cache policy;
- adding a second state owner or importing Comfy/Torch during package import;
  and
- S167-03d/03e cutover, #169, D-12, release, or Registry work.

Exit:

- one shared session owns reserve/settle success, failure, and interruption
  timing;
- service retry and duplicate-idempotency behavior remains focused-tested;
- no heavy host import is needed to classify an active Comfy interruption; and
- S167-03d can connect Prompt Studio without duplicating lifetime logic.

## S167-03d Prompt Studio cutover Behavior record

- State: COMPLETE on `dev` in PR #362
- PR type: Behavior
- Baseline: `dev` commit
  `23cd9990f5b33ec33a02a66bad9e4f77f874bcdc`
- Feature reservation callers: Advanced, Advanced v2, and Regional Prompt
  Studio

### Implemented boundary

`easyuse_anima.nodes.seed_adapters` is the feature adapter between Prompt
Studio and the shared identity/session/service contracts.

- Advanced and Regional use distinct stable feature namespaces.
- A concrete input seed and normalized after-generate control become one
  version-2 reservation request in the Prompt Studio JavaScript-safe wrap
  domain.
- Compatibility execution without a usable host identity or installed runtime
  keeps the former local next-seed behavior. Its fallback is evaluated lazily,
  so an authoritative random reservation does not consume a discarded browser
  compatibility draw.
- Advanced v2 keeps one session open through both its compatibility output and
  structured prompt-data construction. Both wildcard expansion passes use the
  same authoritative execution seed.
- Fixed concrete requests always execute and publish their supplied seed,
  including after an accepted increment/randomize stream. This preserves saved
  workflow replay instead of inheriting retained advancing state.
- Non-fixed Prompt Studio controls return an unstable `IS_CHANGED` value so
  backend reservation cannot be skipped by cache reuse.

The backend executed payload publishes both `wildcard_execution_seed` and the
accepted next-run `wildcard_seed`. Advanced and Regional browser adapters apply
the latter unconditionally and persist the former through the existing
previous-execution workflow property. The browser no longer selects, reserves,
guards, or commits a seed.

### Compatibility and retirement

- The version-1 hidden
  `easyuse_anima_reserved_wildcard_next_seed` input is scrubbed from both
  execution inputs and prompt metadata but its next seed is ignored.
- The root compatibility consumer and constants remain direct aliases for
  D-12; production Prompt Studio callers no longer use the consumer.
- `advanced_queue_seed_runtime.js`, `queue_seed_bridge.js`, their queue/graph
  hooks, and the obsolete 2,494-line browser authority smoke are removed.
- Prompt Studio no longer imports Comfy's frontend `api` module because the
  retired queue interceptor was its only caller.
- Node sockets, widget order, saved workflow schema, public seed range, wildcard
  mode normalization, and AiO behavior are unchanged.

### Validation

- focused service/adapter/Prompt Studio/Regional tests: 40 passed, followed by
  32 post-review service-integration tests;
- backend analyzer/import/package/Registry gate: 43 passed;
- frontend module contract: 50 passed;
- Advanced executed-values, Regional lifecycle, and host-hook Node smokes:
  passed;
- Python quality gate: Pyright baseline ratchet passed for 80 files with no new
  diagnostics; import boundary gate passed with zero violations;
- official full attempt completed compile, quality, and import gates, then
  exposed 11 focused contract/test-isolation failures in the Python suite;
- after correction, the official Python suite passed 1,039 behavior tests with
  only one deterministic analyzer fixture drift, whose exact regenerated
  fixture check passed; and
- every frontend smoke passed, followed by a successful TypeScript 6.0.3 check
  after removing the retired API argument. The full entrypoint was not
  restarted solely to repeat already-passed stages.

### Allowed-file boundary and rollback

This unit changes only Prompt Studio Advanced/Regional node adapters, the
feature seed adapter, fixed replay selection, retired hidden-payload scrubbing,
Prompt Studio frontend authority/display modules, their focused tests and
analyzer fixtures, and these two architecture records.

It does not change AiO callers, AiO domains or frontend hooks, reservation
capacity, execution identity, settlement classification, workflow schemas,
root compatibility aliases, #169 stages, D-12, release, or Registry behavior.
S167-03e remains a separate AiO Behavior PR and the next rollback unit.

## S167-03e AiO cutover Behavior record

- State: VALIDATED; isolated runtime parity passed and `dev` merge pending
- PR type: Behavior
- Baseline: `dev` commit
  `b486d0efb758af9d17fedc2e0aa9dcdb2a4d5896`
- Feature reservation caller: `EasyUseAnimaAIOGenerator`

### Symbol, caller, alias, and global-state inventory

- `EasyUseAnimaAIOGenerator.IS_CHANGED` and
  `_run_aio_legacy_generation` were the two backend special-seed
  interpreters. The generation adapter had no reservation/session caller.
- `web/js/aio/generator_queue_runtime.js` owned a second per-node `WeakMap`
  reservation service, queue-payload/workflow rewriting, FIFO settlement, and
  accepted seed publication.
- `web/js/aio/extension_runtime.js` retained a replacement-safe global queue
  lease solely for that browser service.
- The panel's `__easyuseAnimaLastQueuedSeed` state described browser queue
  acceptance rather than completed backend execution.
- Root `_resolve_aio_runtime_seed` compatibility remains a direct D-12 alias.
  This rollback unit does not change the root compatibility registry.

### Implemented boundary

`easyuse_anima.nodes.seed_adapters.aio_seed_execution` translates normalized
legacy AiO `-1/-2/-3` values through the version-2 parser and opens the shared
identity/session/service lifetime.

- AiO supplies its existing inclusive `2^50` editable maximum and clamp
  overflow policy explicitly.
- A normal node return settles accepted; failure and active Comfy interruption
  use the shared rejected/cancelled settlement behavior.
- Execution without a usable host identity or installed runtime remains an
  isolated compatibility path. It preserves concrete values, resolves legacy
  special selection through the former runtime resolver, and applies
  fixed/randomize/clamped increment/decrement next-seed rules without mutating
  process service state.
- `IS_CHANGED` forces execution for every special selection and every
  non-fixed after-generate control. A concrete fixed request remains cacheable.
- The reserved concrete seed is written into the normalized generation
  settings before legacy orchestration starts, so sampling, first-pass cache,
  saving, and the existing metadata JSON all observe one execution seed.
- A dedicated normalized legacy helper avoids repeating input/settings
  normalization inside the reservation while the root
  `_run_aio_legacy_generation` compatibility alias and signature remain
  unchanged for D-12.

The existing three result sockets and metadata JSON schema are unchanged. One
Comfy executed UI payload, `easyuse_anima_aio_seed`, publishes decimal-string
`execution_seed` and `next_seed` values. Decimal strings preserve uint64
compatibility values across JSON; the browser writes only values inside its
smaller editable domain.

### Browser authority retirement

- `generator_queue_runtime.js`, its `WeakMap`/FIFO state machine, prompt and
  workflow rewriting, host-hook registration, and the 1,035-line queue smoke
  are removed.
- `extension_runtime.js` no longer imports the host-hook registry or owns a
  global queue lease.
- `executed_seed_runtime.js` is a DOM-free display adapter. It records the last
  completed backend seed, applies the accepted next seed without dirtying the
  workflow, and cannot affect backend settlement when a stale panel rejects
  publication.
- The panel's reusable seed state is renamed to
  `__easyuseAnimaLastExecutedSeed`, and its user-facing text now describes a
  completed execution.
- Optional dependency checks remain attached to feature dialogs. Queueing no
  longer performs the retired blanket dependency refresh.

Old browser bundles may still rewrite a legacy special seed to a concrete
value before submission. The backend accepts that concrete compatibility
input through the same service/session boundary; new bundles leave selection
and settlement entirely to the backend.

### Validation

- focused AiO node runtime tests: 77 passed;
- focused reservation/identity/session/adapter/AiO cutover tests: 62 passed;
- focused frontend module/AiO contracts: 85 passed;
- executed-seed, extension, panel, and host-hook Node smokes: passed;
- backend import/package/Registry gates passed with only the expected analyzer
  fixture delta, which was regenerated from the implemented source; and
- the official full reached Python after compile, Pyright, and all six import
  boundary groups passed. It stopped in 38.6 seconds on two legacy fixture/mock
  assertions, not runner timeout or cleanup;
- after the exact contract correction, all 1,044 Python tests passed in 29.5
  seconds; and
- the not-yet-run frontend stage then passed every smoke and TypeScript 6.0.3
  for 112 JavaScript files. The full entrypoint was not restarted solely to
  repeat already-passed stages; and
- an isolated ComfyUI 0.27.0 instance loaded the canonical node pack once,
  exposed the unchanged AiO object-info socket contract, served the new entry
  and executed-seed modules with HTTP 200, returned HTTP 404 for the retired
  queue module, and completed a browser UI load without an EasyUseAnima module
  error. A model-backed generation and separate Legacy/Node 2.0 node-render
  interaction were not run.

### Allowed-file boundary and rollback

This unit may change only the AiO generation adapter/default-domain constant,
the shared feature seed adapter, AiO entry/panel/extension/display modules,
their focused tests and runner manifest, deterministic analyzer fixture, and
these two architecture records.

It does not change node sockets, widget order, saved workflow schema, metadata
JSON schema, reservation capacity, identity/session contracts, Prompt Studio,
root compatibility aliases, #169 stage/cache ownership, D-12, release, or
Registry behavior. Reverting this unit restores only the AiO browser queue
authority and pre-cutover backend interpretation.
