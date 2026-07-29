# Post-Phase-E Backend Maintenance Roadmap

## Status and authority

- Status: active execution plan after Phase D and Phase E completion.
- Primary parent: Issue #185.
- Active first task: Issue #186 / P-WC-02 wildcard internal-consumer and facade Move.
- Quality owner: Issue #188.
- Compatibility ledger: Issue #186.
- D-14/H status: parked by compatibility gates, not failed.
- Released baseline: 0.6.2.
- Phase E completion and post-Phase-E D-14 audit: PRs #561 and #562.

This plan separates two facts that must not be collapsed:

```text
D-14 root removal has no READY task
!=
the entire backend roadmap has no remaining work
```

D-14/H waits for production-import, release-window, consumer, rollback, and
breaking-change evidence. Phase F completion and G-04 through G-06 remain executable
without deleting a root surface.

## 1. Current verified state

### Completed

- Phase A baseline and ADRs
- Phase B `nodes.py` extraction and compatibility registry
- Phase C feature contracts/behavior used by later moves
- Phase D canonical package consolidation and route composition
- Phase E RuntimeServices ownership, lifecycle, cleanup, and isolated runtime fixture
- official full/package/live integration gates for the completed D/E boundaries

### Correct normal stop

The post-Phase-E D-14 audit records zero removal-approved root surfaces.

| Surface | Current blocker |
| --- | --- |
| root `__init__.py` | permanent ComfyUI entrypoint; still imports root `api.py` for production route registration |
| `api.py` | transitional production facade; current complete canonical/facade form has not shipped and root entrypoint/runtime consumers remain |
| `wildcard_engine.py` | behavior-bearing compatibility adapter; `api.py` and `nodes.py` still consume it and final form has not shipped |
| `api_contract.py` | final direct shim form completed after 0.6.2; release N has not started |
| `autocomplete_dataset.py` | final direct shim form completed after 0.6.2; release N has not started |
| `anima_prompt/` | final package shim form completed after 0.6.2; release N has not started |
| older direct/public shims | minimum release window may have passed, but consumer evidence and public breaking-change approval do not support removal |

This is not a Registry, scanner, test, or runtime failure. Retention is the required
ADR-002 result when evidence is absent or ambiguous.

### Remaining global roadmap work

- G-04 public API snapshot coverage is complete; no G-04B gate was required.
- G-05 size/complexity growth ratchet is not implemented as a blocking incremental gate.
- G-06 canonical test ownership is not completed.
- `api.py` and `wildcard_engine.py` have not reached a proven pure-shim form that can
  begin a final support window.

## 2. Execution lanes

### Lane A — Active maintainability work

```text
COMPLETE F-02a Autocomplete typed result contracts             #563 / PR #566
  -> COMPLETE affected-row re-audit
  -> COMPLETE F-02b Prompt field-family typed contract         #563 / PR #569
  -> COMPLETE affected Prompt-row re-audit
  -> COMPLETE F-02c canonical Prompt Data typed read/output    #563 / PR #571
  -> COMPLETE affected Prompt-row re-audit
  -> COMPLETE F-02d settings typed migration contract          #563 / PR #573
  -> COMPLETE affected settings/profile/workflow row re-audit
  -> COMPLETE F-02e common feature error taxonomy Contract     #563
  -> COMPLETE F-02f canonical categories and feature inheritance #563
  -> COMPLETE F-02g authoritative profile/translation API mappings #563 / PR #577
  -> COMPLETE F-02h affected error-row re-audit and Phase F close #563
  -> COMPLETE G-04A public API snapshot coverage audit         #188
  -> NOT REQUIRED G-04B minimal missing public-surface gate
  -> COMPLETE P-WC-01 wildcard pure-shim feasibility Contract  #186
  -> READY P-WC-02 internal consumer/facade Move               #186
  -> P-API-01 API production-facade feasibility Contract      #186
  -> OPTIONAL P-API-02 canonical production-entry Move
  -> G-05A    size/complexity baseline and changed-path ratchet #188
  -> G-06A    canonical test-ownership Contract               #188
  -> G-CLOSE  Phase F/G completion audit
```

One task is active at a time unless allowed-file sets and evidence owners are proven
disjoint. No task above removes a public root module.

### Lane B — Event-gated compatibility runway

```text
final pure-shim form available
  -> next ordinary release becomes release N
  -> package/read-back proves canonical + shim paths
  -> support window and consumer evidence accumulate
  -> H-01 / D-14 removal re-audit in a later release
```

Do not publish a release solely to advance the shim clock. The next normal bug-fix or
feature release that contains the final canonical-plus-shim form starts release N.
If no normal release occurs, the shims remain supported.

## 3. F-01 — Typed-boundary completion audit

Owner: Issue #563.

Type: Contract/gate; production-free.

The audit classifies each area as:

```text
complete
intentional adapter/migration boundary
targeted follow-up required
```

Areas:

- persisted settings/profile/workflow schema and migrations
- API request/result/error payloads
- Prompt, Wildcard, and Autocomplete boundaries
- AiO config/request/state/result boundaries
- node adapter raw input/output conversion
- common feature error taxonomy and adapter mappings

Rules:

- reuse current Pyright, import-boundary, schema, API, and migration fixtures;
- do not create a second manifest when existing deterministic evidence is sufficient;
- do not treat ComfyUI/tensor adapter `Any` as feature-service debt merely because it
  is dynamic;
- do not perform a repository-wide annotation rewrite;
- produce exact F-02 task cards only for real leaks beyond adapters/migrations.

Exit:

- no gap: record Phase F complete and start G-04A;
- gap: execute only the smallest F-02, re-audit the affected row, then select the
  next smallest remaining finding or start G-04A when Phase F closes.

Audit result, updated after F-02d merged at
`e9640c4db951939173ff5ffb8d54472795599383`:

- [`python-typed-boundary-f01-audit.md`](python-typed-boundary-f01-audit.md)
  records the production-free six-area inventory and reuses the existing
  deterministic fixtures;
- Autocomplete and Wildcard are complete after F-02a; the Prompt field family and
  canonical Prompt Data are complete after F-02b/F-02c;
- legacy/future Prompt Data JSON remains intentionally raw only at the workflow and
  node adapter boundary;
- the Prompt/Wildcard/Autocomplete row is complete;
- typed v1 ordinary/long-text settings persistence plus pure legacy/raw reads close
  the settings/profile/workflow row while profile future fields and raw host workflow
  lookup remain intentional migration/adapter boundaries;
- the common feature error taxonomy row is complete after F-02e fixes the executable
  inventory, F-02f adds category inheritance, F-02g makes fixture-known concrete HTTP
  policy API-authoritative, and F-02h records zero unmapped errors;
- Phase F is complete and Issue #188 / G-04A is READY.

## 4. G-04A — Public API snapshot coverage audit

Owner: Issue #188.

Type: Contract/gate; production-free first.

Existing evidence already covers significant G-04 scope:

- `tests/fixtures/python_compatibility_surface.v1.json`
- `tests/test_python_compatibility_surface.py`
- node/workflow contracts
- API/schema contracts
- package skeleton and Registry archive closure

G-04A must map, not duplicate, those sources against the required public surface:

```text
permanent package entrypoint
NODE_CLASS_MAPPINGS / NODE_DISPLAY_NAME_MAPPINGS / WEB_DIRECTORY
supported mapped node classes and exact root/canonical identity
explicit root and canonical __all__
public schema/result/error types identified by F-01
actual packed canonical/shim import closure
```

Required decisions:

1. extend the compatibility fixture only if its schema naturally owns the missing data;
2. otherwise add one narrow public-snapshot fixture with references to existing owners;
3. do not copy full node/API schemas into another large JSON document;
4. update stale metadata such as `first_release: null` only from verified published-tag
   and packed-artifact evidence;
5. classify each root name as permanent, supported, transitional, or unsupported.

Exit:

- existing gates already complete G-04: record completion without a synthetic rewrite;
- gaps exist: create one bounded G-04B Contract/tool PR.

Audit result:

- [`python-public-api-g04a-audit.md`](python-public-api-g04a-audit.md) maps every
  required surface to its existing deterministic owner;
- the three permanent root entrypoint names, 18 supported mapped-node identities,
  explicit root/canonical `__all__`, F-01 schema/result/error boundaries, and shipped
  archive closure are already covered;
- private/transitional bindings remain excluded or compatibility-ledger-owned, and no
  unsupported name is promoted;
- G-04A is complete without a synthetic fixture, so G-04B is not required;
- the next READY task is Issue #186 / P-WC-01.

## 5. Pre-retirement preparation without removal

These tasks may begin only after G-04A fixes the supported public surface. They reduce
internal production dependencies; they do not remove shims or start the support window.

### P-WC-01 — Wildcard facade feasibility Contract

Inventory:

- exact `api.py`, `nodes.py`, node-adapter, test, and external/document consumers;
- root `wildcard_engine.py` call-time snapshot/source/build seams;
- canonical service/facade functions capable of preserving deterministic NumPy seed,
  snapshot cache, expansion budget, error, and object-identity behavior;
- package and flat-import compatibility requirements.

Result must be one of:

```text
FEASIBLE
- canonical facade owner
- direct internal consumer migration
- root direct re-export shape
- exact Move files/tests

RETAIN
- seam that cannot be represented without behavior or compatibility change
- maintenance/security/package cost of retention
- next evidence trigger
```

If feasible, P-WC-02 moves internal production consumers to the canonical facade and
turns the root module into explicit direct imports. It does not delete the file.

P-WC-01 result:

- [`python-wildcard-pwc01-facade-feasibility.md`](python-wildcard-pwc01-facade-feasibility.md)
  records **FEASIBLE** without adding a duplicate fixture;
- `easyuse_anima.wildcard.service` is the existing canonical facade owner; no new
  production module or cross-boundary design is needed;
- `api.py` and `nodes.py` are the only remaining root consumers;
- the four root facade functions remain supported, while root snapshot/build patching
  is an E-06-classified private test seam with an equivalent canonical service patch
  owner;
- P-WC-02 is the one bounded Move in the Contract task card. It preserves the root
  file and does not start the release-N support window.

### P-API-01 — API facade feasibility Contract

Inventory:

- root entrypoint dependency on `api.register_routes`;
- production route composition, payload/runtime helpers, registrar and lifecycle;
- supported public names versus transitional private monkeypatch/test seams;
- direct importer and object-identity evidence;
- import-cycle constraints between entrypoint, bootstrap, router, routes, runtime, and
  root compatibility module.

Compare only evidence-backed candidate shapes, for example:

```text
canonical api application/composition owner + root direct aliases
bootstrap-owned production application + root compatibility facade
intentional long-term retained root facade
```

The Contract must not select a design merely because it deletes more root code.
Production must not silently stop honoring a supported root seam.

A focused technical PRO review is appropriate after P-API-01 only when two or more
valid shapes remain after direct source/test/consumer evidence. User preference is not
used as a substitute for technical ownership analysis.

If a safe shape is selected, P-API-02 migrates the production entrypoint and leaves a
compatible root facade. Public removal remains forbidden.

## 6. G-05A — Size and complexity ratchet

Owner: Issue #188.

Type: Contract/tool.

Reuse `tools/analyze_python_backend.py` module/function metrics. Do not introduce a
second repository inventory.

Initial policy:

- freeze the current baseline;
- block growth only for new or changed production modules/functions;
- require an owner issue and decomposition boundary for reviewed exceptions;
- use 800 module / 400 adapter / 120 function lines as review triggers, not automatic
  reasons for meaningless file splitting;
- do not combine the gate with broad production cleanup.

A baseline decrease is accepted. A path rename or deliberate owner Move updates the
fixture in the same reviewed PR.

## 7. G-06A — Canonical test ownership

Owner: Issue #188.

Type: Contract/gate first.

Create a compact ownership map from feature packages to:

```text
pure/service unit tests
adapter/API/node integration tests
migration/compatibility tests
package/archive tests
live/host tests
```

Rules:

- retain `unittest` as the repository runner;
- do not move every historical test for cosmetic symmetry;
- eliminate direct root-private imports only when a canonical owner is available and
  the test is not explicitly a compatibility test;
- each compatibility, package, migration, and live matrix has one named owner;
- new canonical packages must identify their direct test owner.

## 8. Release N and H/D-14 re-audit

Release N starts only when the next ordinary published package contains the reviewed
final shim forms. Release preparation records:

- exact tag/commit/archive hash;
- root and canonical import parity;
- internal production import scan;
- maintained docs/examples canonical-path scan;
- package validate/pack/import closure;
- available support issues and best-effort public code-search evidence.

No outbound telemetry is added. A lack of public search hits is not proof of zero
consumers.

Removal is no earlier than a later release and requires all ADR-002 gates. Public
removal also requires a separate breaking-change issue, impact statement, release
notes, and rollback plan. Low-cost shims may be deliberately retained indefinitely.

Re-audit triggers are event-based:

- release N is published and read back;
- a production root consumer reaches zero;
- new consumer evidence appears;
- a supported shim creates demonstrated startup, security, or packaging harm;
- a breaking-change release is explicitly planned.

Do not periodically poll or reopen D-14 without one of these changes.

## 9. Validation and escalation

### Contract/audit PRs

- targeted fixture and source consistency checks
- direct owner tests
- `git diff --check`
- official full once on the final test/tool candidate when repository tests change
- no package/live unless package/runtime surface changes

### Move PRs

- changed-file syntax and focused parity
- direct compatibility/object-identity tests
- import-boundary and package-skeleton tests
- official full once on final SHA
- package/live only when import closure, entrypoint, registration, or host-visible
  behavior is changed

### Stop conditions

Stop the current task, not the whole roadmap, when:

- a Contract cannot distinguish public support from test-only monkeypatch behavior;
- a canonical production move requires importing a root shim;
- object identity, route registration, workflow, persisted data, or deterministic
  Wildcard output must change;
- a pure-shim conversion requires a new public socket/API/schema;
- several technically valid cross-boundary designs remain after evidence collection.

Only the last condition or an equivalent deep architecture ambiguity calls for focused
technical PRO review. Ordinary test failures and small owner-local design choices stay
with Codex.

## 10. Codex resume instruction

```text
Start Issue #186 / P-WC-02 only from latest origin/dev after P-WC-01 merges.

Read:
- current-policies.md
- codex-execution-efficiency.md universal rules
- this document's P-WC-02 card and validation sections
- python-wildcard-pwc01-facade-feasibility.md
- Issue #186 latest P-WC-02 checkpoint
- api.py, nodes.py, wildcard_engine.py
- direct wildcard/API/route/compatibility/identity/determinism/package/import owners

Do not read all historical D/E PRs and do not start D-14 removal.

In one cohesive Move, import api.py list_wildcards and the 19 nodes.py wildcard names
from their existing canonical modules. Replace wildcard_engine.py's seven service
wrappers/classes with direct canonical service imports while retaining eager numpy,
all other root identities, package/flat fallback, signatures, results, cache/retry,
determinism, budgets, errors, API callback monkeypatching, and node behavior. Move
private root lifecycle patch targets to the equivalent canonical service owner.

Run only targeted consistency/focused checks during the edit loop and git diff check.
Run official full exactly once on the final candidate SHA. Run validate/pack/archive
because the production import closure changes. Live is not triggered because no
host-visible behavior changes.

Push a dev-targeted Draft PR, review, and squash merge. Record the final shim form on
Issue #186, then select P-API-01. Do not start release N merely for the shim.

Do not change canonical wildcard behavior, public/root exports, API/node payloads,
migration semantics, RuntimeServices/bootstrap, deprecation warnings/telemetry,
release/tag, or Registry state. Do not delete the root file.
```
