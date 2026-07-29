# Backend Final Convergence Roadmap

## Status and authority

- Status: active final-convergence plan.
- Active owner: Issue #593.
- Parent architecture: Issue #185.
- Compatibility ledger: Issue #186 and ADR-002.
- Lifecycle authority: E-09 / Issue #187.
- Current released baseline: 0.6.2.
- Current completed lanes: Phase D, Phase E, Phase F, G-04/G-05/G-06, P-WC,
  P-API-01, G-CLOSE, and SEC-01 through SEC-05.
- First READY task: FC-01, production-free Definition-of-Done closure audit.

This document supersedes the `no READY task` conclusion only for the initial backend
architecture Definition of Done. It does not reopen completed Phase F/G or security
work, and it does not authorize P-API-02, root deletion, release, tag, or Registry work.

## 1. Current stop and the remaining gap

The current event-gated stop is correct for compatibility retirement:

- P-API-01 retained root `api.py` because current request-time root patch seams and the
  E-09 executor-before-cleanup-plan timing cannot both be preserved by the previously
  evaluated canonical application shapes;
- P-API-02 is not READY from that verdict;
- final direct shims have not all shipped in a release N;
- consumer evidence and public breaking-change approval do not authorize removal.

The stop is not identical to the original technical Definition of Done:

1. The blocking import-boundary checker covers a reviewed subset of canonical package
   groups, while the G-06 owner map covers the complete current package/test surface.
2. Root `api.py` is still a production application/composition container rather than an
   explicit compatibility facade.
3. The P-API-01 retention document names a separate compatibility patch-owner migration
   as a valid revisit event; that prerequisite has not been attempted.
4. Several large-module exceptions have reviewed decomposition boundaries but no final
   disposition. They are not all mandatory splits, but they need one finite audit.

## 2. Two completion states

### Technical architecture completion

This state may be reached before release N:

- `easyuse_anima` owns all production implementation;
- root Python files are the permanent entrypoint or explicit compatibility
  facades/shims;
- every canonical owner group has a blocking role-aware import/dependency gate;
- root `api.py` no longer creates the production application/runtime composition;
- bootstrap remains the single E-09 lifecycle owner;
- route, payload, error, workflow, profile, settings, node and object-identity contracts
  remain compatible;
- full, package/archive, no-host, lifecycle and representative host/API gates pass.

### Compatibility retirement completion

This state is event-gated:

- an ordinary release publishes the final canonical-plus-shim forms as release N;
- support-window, consumer, harm and rollback evidence are collected;
- eligible private shims may be removed first;
- public removal requires a reviewed breaking-change Issue and release note;
- low-cost public shims may be deliberately retained indefinitely.

Technical completion does not require deletion of every public shim.

## 3. Ordered execution queue

```text
READY FC-01  original Definition-of-Done closure audit
  -> FC-02   complete canonical owner-boundary gate
  -> FC-03A  root API patch-owner compatibility Contract
  -> FC-03B  canonical dependency/patch-owner Move
  -> FC-04A  canonical API application + E-09 lifecycle Contract
  -> FC-04B  cohesive production application Move
  -> FC-05   technical completion audit

EVENT FC-06  next ordinary release N
  -> FC-07   later H/D-14 compatibility re-audit
```

Only one FC task is active by default.

## 4. FC-01 — Original Definition-of-Done closure audit

Type: Contract/audit; production-free.

Map every checkbox in `python-backend.md` to current deterministic evidence and classify
it as:

```text
complete
technical gap
compatibility event
deliberate retain
```

Required checks:

- compare the import-boundary checker's reviewed groups with the complete G-06 owner
  groups and exact top-level canonical owners;
- confirm whether adapters, feature packages, infrastructure, nodes/registration and
  runtime/bootstrap have the intended role rules;
- map each root file to permanent entrypoint, explicit shim/facade, or remaining
  implementation;
- reuse P-API-01's exact root symbol and patch-time inventory;
- map E-09, typed/migration, public identity, package/archive, validation and shim gates;
- identify the exact technical tasks required before FC-05.

Do not create a duplicate inventory when the analyzer, compatibility fixture, G-06 map,
Pyright/import ledgers or direct tests already own the evidence.

Exit:

- confirm or correct the FC-02 through FC-04 task boundaries;
- publish one compact closure matrix;
- select FC-02 as READY unless the audit proves a smaller prerequisite.

## 5. FC-02 — Complete canonical owner-boundary gate

Type: Contract/tool. A real violation may require a separate smallest correction Move.

### Source of truth

Use the G-06 production-path groups as the current complete owner inventory and the
existing AST analyzer as the only import graph. Do not create a second repository
inventory.

### Required coverage

The current role-aware gate must account for at least:

```text
feature/service:
  aio, autocomplete, image, lora, naia, profiles, prompt, seed, settings,
  translation, wildcard

common:
  common and canonical error primitives

infrastructure:
  the complete infrastructure package, with reviewed subroles where needed

adapter:
  api/routes and nodes

composition/entry:
  bootstrap, runtime, registration, API application/router, workflow adapter
```

The exact role rules are fixed by FC-01. Adapter and composition modules must not be
forced through feature-only rules merely to increase coverage.

### Implementation rules

- extend the existing import-boundary contract/checker rather than adding another tool;
- reject canonical-to-root imports, new runtime SCCs, feature-to-adapter/bootstrap/
  registration back references, compatibility fallback imports and unowned side effects;
- preserve intentional adapter-to-feature and composition-to-adapter directions;
- do not broad-allowlist actual violations;
- if violations exist, fix one cohesive owner group at a time before enabling its gate.

Exit: every current canonical production path is included in a blocking role-specific
owner gate or an explicitly reviewed permanent entry/compatibility rule.

## 6. FC-03 — Root API patch-owner migration

P-API-01 retained root `api.py` because canonical candidates could not preserve both
E-09 timing and request-time root-global patch semantics. FC-03 intentionally satisfies
its first recorded revisit event before reevaluating application placement.

### FC-03A — Compatibility Contract

Production-free.

For each root API symbol family, classify:

```text
supported host/API behavior
supported named dynamic compatibility seam
transitional private patch seam
unsupported test-only owner inspection
production-only implementation detail
```

Required decisions:

- retain route methods, paths, order, signature, marker, response/error and request-ID
  behavior;
- retain the specifically supported dynamic profile/translation error seams;
- move repository-only owner inspection to canonical tests;
- assign request/registration-time mutable dependencies to one canonical patch/injection
  owner;
- define the minimum long-lived root facade surface;
- forbid a canonical-to-root back reference.

### FC-03B — Dependency/patch-owner Move

Introduce one typed/private canonical dependency owner, such as an
`ApiApplicationDependencies` bundle or a reviewed equivalent.

- handlers and registrar resolve supported call-time dependencies through that owner;
- root compatibility patching, where deliberately retained, targets the same canonical
  owner rather than a second root-owned cell;
- test-only root mirrors are migrated to direct canonical owner tests;
- application construction remains in its current location during FC-03B;
- route behavior, payloads, errors, lifecycle, public exports and execution order remain
  unchanged.

Exit: a future canonical application can preserve every supported seam without importing
root `api.py`.

## 7. FC-04 — Canonical API application and E-09 convergence

### FC-04A — Lifecycle Contract

Production-free first. Define one immutable application bundle containing the exact
translation route executor, handlers, route definitions/signature, registrar and
compatibility identity view.

Frozen requirements:

- exactly one application and one translation route executor per process;
- application creation occurs before `bootstrap.initialize()` freezes the RuntimeServices
  cleanup plan;
- executor shutdown remains cleanup item 1;
- application construction remains outside initialize unless a separate Behavior
  Contract explicitly changes rollback timing;
- bootstrap remains the only lock/atexit/terminal/cleanup owner;
- no application `close`, reset registry, second lifecycle lock or hot reinitialize;
- entrypoint and late root API import resolve the same application identities;
- no canonical module imports a root compatibility module;
- direct canonical/no-host imports do not create the application or lifecycle state.

Compare only evidence-backed shapes after FC-03. Request focused technical PRO review
only when at least two shapes satisfy every lifecycle and compatibility condition.

### FC-04B — Cohesive Move

Expected production surface, subject to FC-04A:

```text
__init__.py
api.py
easyuse_anima/api/application.py or the selected canonical owner
easyuse_anima/bootstrap.py
```

Together with direct tests, analyzer/contract fixtures and docs.

- move production application construction into the canonical package;
- make root `api.py` an explicit compatibility facade/binder over exact canonical
  objects;
- preserve E-09 cleanup order, rollback, repeated initialize, route refresh, terminal
  shutdown and late-import identity;
- preserve package/flat import and all supported host/API contracts.

This is one rollback unit. Do not split executor/application identity and entrypoint
wiring across separately deployable intermediate states.

## 8. FC-05 — Technical completion audit

Type: integrated Contract/gate.

Reconcile the original Definition of Done after FC-04 and any mandatory FC-02 correction.

Required promotion evidence on one integrated candidate:

```text
official full
pinned Pyright/Ruff and complete owner-boundary gates
comfy node validate
actual comfy node pack and archive/CRC/import closure
root/canonical identity and no internal root implementation imports
no-host canonical imports
fresh-process E-09 terminal lifecycle
0.5.2 workflow/profile/settings/API compatibility fixtures
representative isolated ComfyUI API/node execution smoke
```

Record technical architecture completion and close the implementation lane of #185.
Issue #186 remains open only as the compatibility/release ledger.

## 9. Optional MD lane — large-module disposition

After FC-01, audit the current G-05 exception ledger without changing production.
Classify each exception as:

```text
cohesive-retain
split-ready
blocked-by-contract
event-driven
```

Priority review candidates:

- `easyuse_anima/aio/generation_normalization.py`
- `easyuse_anima/aio/legacy_generation.py`
- `easyuse_anima/prompt/artist_mix.py`
- `easyuse_anima/nodes/prompt_advanced_nodes.py`
- `easyuse_anima/prompt/advanced.py`

Do not split the E-09 bootstrap lifecycle, the atomic JSON transaction owner or root
compatibility shims merely to satisfy a line threshold.

A split is allowed only when it has:

- independently named responsibility and owner;
- direct behavior/contract tests;
- measurable reduction in change collision or review scope;
- one bounded rollback unit;
- no new generic `utils`, `misc` or service-locator module.

The MD lane is not an FC-05 blocker unless it finds an owner/import violation or a
module that prevents FC-03/FC-04 convergence.

## 10. Release N and H/D-14

### FC-06 — Ordinary release N

Do not publish solely to start a shim clock. The next normal feature/bug release that
contains the final canonical-plus-shim forms becomes release N. Record exact tag, SHA,
archive hash, identity parity, internal root-import scan and validate/pack/read-back.

### FC-07 — Later compatibility re-audit

Run only after an ADR-002 event changes. Consider private shims first. Public removal
requires breaking-change approval, impact, release notes and rollback. Deliberate
long-term retention of low-cost shims is a valid completed outcome.

## 11. Validation efficiency

### Edit loop

```text
changed-file syntax/static
direct task-specific focused owners
current analyzer/contract projection
git diff --check
```

Do not run the broad quick/full suite in the edit loop.

### Promotion

- official full once on the exact final code/test/tool/fixture SHA;
- validate/pack/archive for import, entrypoint, registration, package or release changes;
- isolated live ComfyUI only for host-visible behavior or the FC-05 integrated gate;
- reuse evidence when only documentation changes and its source tree is unchanged.

Keep one active task by default. FC-02 and the optional MD audit may run in parallel
only when their allowed files and evidence owners are explicitly disjoint.

## 12. Stop and PRO conditions

Codex resolves ordinary implementation and focused-test failures inside the current
owner. Stop and request focused technical PRO review only when:

- FC-03 leaves multiple API application/lifecycle shapes that all satisfy E-09 and
  compatibility gates;
- executor-before-cleanup timing requires dynamic cleanup-plan mutation or a second
  lifecycle owner;
- a supported root seam cannot be represented without canonical-to-root import;
- the full owner gate exposes an actual cycle or ownership ambiguity not expressible by
  the reviewed role model;
- a behavior-preserving Move cannot be separated from lifecycle/compatibility Behavior.

## 13. Codex resume instruction

```text
Start Issue #593 / FC-01 from latest origin/dev.

Read only:
- current-policies.md
- codex-execution-efficiency.md universal rules
- this document's FC-01 and validation sections
- Issue #593 latest checkpoint
- python-backend.md Overall Definition of Done
- current import-boundary checker/ledger
- G-06 test ownership map
- P-API-01 completed inventory/revisit events
- compatibility registry and direct evidence named by those documents

Do not implement FC-02+ during FC-01. Do not reopen completed F/G/security lanes.
Do not start P-API-02, root removal, release, tag or Registry work.

Produce one closure matrix, confirm or correct the next task boundaries, run only direct
consistency/focused checks and git diff check, then create a dev-targeted Draft PR.
Documentation-only FC-01 does not trigger official full/package/live.
```
