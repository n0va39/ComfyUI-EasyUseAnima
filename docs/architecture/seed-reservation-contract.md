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
