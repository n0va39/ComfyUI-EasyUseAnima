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
