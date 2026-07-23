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

- State: READY
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
