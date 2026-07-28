# Python Backend Architecture

These documents define the target backend architecture, migration rules, and reviewed
cross-surface contracts. They do not imply that every target state is implemented.

Before selecting work, read the bounded execution policy in
[`../development/codex-execution-efficiency.md`](../development/codex-execution-efficiency.md),
then only the active task section, owning Issue, direct source, and direct tests.

## Active sequencing

- Issue [#187](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/187)
  owns Phase E. E-01 through E-09 are complete; E-10a fixes the isolated-runtime
  fixture Contract and E-10b is the next READY task.
  Issue #186 retains D-14/shim decisions.
- [`backend-roadmap-resume-0.6.2.md`](backend-roadmap-resume-0.6.2.md)
  is the current execution source of truth. Read it before the older accumulated
  roadmap.
- E-10a Contract base: E-09c / PR #558 at
  `5e99b702731b896ce6a424b7315e98eaff21133f`.
- D-08 is complete and D-08v is not required.
- D-14 readiness retains every root surface; retirement/final-freeze work is blocked.
- E-01 inventory Contract:
  [`python-runtime-state-inventory.md`](python-runtime-state-inventory.md).
- E-02b base Contract:
  [`python-runtime-base-contract.md`](python-runtime-base-contract.md).
- E-02c composition is recorded in the same base Contract: RuntimeConfig and a
  private system clock are installed in the default runtime without moving feature
  consumers.
- E-02 completion audit:
  [`python-runtime-e02-completion-audit.md`](python-runtime-e02-completion-audit.md).
- E-02d canonicalizes the prompt knowledge package-data alias and completes E-02.
- E-03 repository/filesystem Contract and completion result:
  [`python-runtime-e03-repository-filesystem-contract.md`](python-runtime-e03-repository-filesystem-contract.md).
- Completed E-04 translation runtime ownership Contract and audit:
  [`python-runtime-e04-translation-contract.md`](python-runtime-e04-translation-contract.md).
- Completed E-05 autocomplete runtime ownership Contract and audit:
  [`python-runtime-e05-autocomplete-contract.md`](python-runtime-e05-autocomplete-contract.md).
- Completed E-06 wildcard snapshot runtime ownership Contract and audit:
  [`python-runtime-e06-wildcard-contract.md`](python-runtime-e06-wildcard-contract.md).
- E-08 AiO first-pass cache ownership Contract and bounded Move queue:
  [`python-runtime-e08-aio-cache-contract.md`](python-runtime-e08-aio-cache-contract.md).
- E-09 runtime shutdown and cleanup Contract and bounded queue:
  [`python-runtime-e09-lifecycle-contract.md`](python-runtime-e09-lifecycle-contract.md).
- E-10 isolated runtime test fixture Contract and bounded queue:
  [`python-runtime-e10-test-isolation-contract.md`](python-runtime-e10-test-isolation-contract.md).
- E-09 is complete with `ambiguous_state_owners=[]`; E-10b is the next READY task.
- Completed #470 and the #413/#414/#415 queue/live-UI lanes remain contract references,
  not active blockers.
- Released code baseline: 0.6.2. Registry activation is external administration and
  does not block `dev`; do not republish or mutate the release.
- Completed #409/#410/#411 and deferred #440/#441 do not alter the E-01 boundary.
- Root removal, release, and Registry remain governed by the active roadmap; E-10a
  authorizes only the E-10b test-infrastructure migration next.

## Current code boundary

After D-08u:

- root `api.py` is a temporary compatibility/composition facade;
- canonical route implementations live under `easyuse_anima/api/routes/`;
- `api/router.py` owns injected route order, definitions/signature, resolver,
  registrar, and idempotent registration;
- `bootstrap.py` owns migrated concrete factory/dependency/correlation composition and
  the production initialization call site;
- all 21 route handlers retain their locked composition/registration contract;
- root `api.py` remains a transitional imported runtime facade;
- root `wildcard_engine.py` retains snapshot lifecycle and direct production consumers;
- no reviewed evidence requires changing routes, payloads, persistence, error policy,
  workflow contracts, or optional-dependency behavior.

This is transitional debt, not a reason for a broad rewrite. The E-01 inventory
records ownership, lifetime, locking, cleanup, and test evidence without removing
aliases or absorbing feature behavior.

## Core documents

- [`backend-roadmap-resume-0.6.2.md`](backend-roadmap-resume-0.6.2.md):
  completed D-08 evidence, D-14 readiness verdict, completed Phase E units, and the
  bounded E-08 handoff.
- [`python-backend.md`](python-backend.md): target ownership and dependency direction.
  Its early implementation snapshot is historical where the active checkpoint differs.
- [`python-backend-execution-roadmap.md`](python-backend-execution-roadmap.md):
  accumulated progress and historical task details; not the current immediate queue.
- [`python-compatibility-shims.md`](python-compatibility-shims.md): supported root/shim
  inventory and removal evidence.
- [`python-runtime-state-inventory.md`](python-runtime-state-inventory.md): E-01
  runtime-owned/declarative state partition, lifecycle gaps, and target phases.
- [`python-runtime-base-contract.md`](python-runtime-base-contract.md): E-02b
  base types plus the E-02c private bootstrap composition and feature-port boundary.
- [`python-runtime-e02-completion-audit.md`](python-runtime-e02-completion-audit.md):
  E-02 path-owner disposition, E-02d completion, and E-03 Contract handoff.
- [`python-runtime-e03-repository-filesystem-contract.md`](python-runtime-e03-repository-filesystem-contract.md):
  repository/path/lock/patch boundaries and the completed E-03 queue.
- [`python-runtime-e04-translation-contract.md`](python-runtime-e04-translation-contract.md):
  completed translation provider/client, service cache/single-flight, route executor
  owners, lifecycle gaps, and the E-04 completion audit.
- [`python-runtime-e05-autocomplete-contract.md`](python-runtime-e05-autocomplete-contract.md):
  autocomplete declarative source policy, completed snapshot/Future and
  index-store owner Moves, compatibility seams, and bounded queue.
- [`python-runtime-e06-wildcard-contract.md`](python-runtime-e06-wildcard-contract.md):
  wildcard snapshot LRU/single-flight ownership, compatibility seams, cleanup
  disposition, and bounded Move queue.
- [`python-runtime-e08-aio-cache-contract.md`](python-runtime-e08-aio-cache-contract.md):
  AiO first-pass cache state ownership, direct compatibility surfaces, cleanup
  disposition, caller boundary, and bounded Move queue.
- [`python-runtime-e09-lifecycle-contract.md`](python-runtime-e09-lifecycle-contract.md):
  bootstrap terminal lifecycle, reverse cleanup order, partial-initialization
  rollback, retained no-op resources, and the bounded E-09a/b/c queue.
- [`python-runtime-e10-test-isolation-contract.md`](python-runtime-e10-test-isolation-contract.md):
  current test reset inventory, one test-only fixture owner, isolation modes, and the
  bounded E-10a/b/c queue.
- [`adr-001-modular-monolith.md`](adr-001-modular-monolith.md): feature-oriented modular
  monolith decision.
- [`adr-002-compatibility-shims.md`](adr-002-compatibility-shims.md): shim lifecycle and
  retirement policy.
- [`../development/codex-execution-efficiency.md`](../development/codex-execution-efficiency.md):
  context budget, focused test ladder, invalidation, evidence reuse, and reporting.

## Cross-surface contract references

Read only when the task touches the surface:

- [`queue-ui-two-phase-correlation-addendum.md`](queue-ui-two-phase-correlation-addendum.md):
  queue identity, revision, executed envelope, mapped result, and cleanup.
- [`prompt-studio-execution-derived-projection.md`](prompt-studio-execution-derived-projection.md):
  completed linked-input/NAIA projection contract.
- [`seed-ui-semantics-gate.md`](seed-ui-semantics-gate.md): Prompt Studio concrete seed
  versus AiO persistent special-token semantics.
- [`aio-advanced-integrations-roadmap.md`](aio-advanced-integrations-roadmap.md): completed
  DAVE/Torch Compile/NegPip plan; patch follow-ups remain separate.
- [`comfy-host-provider-bridge.md`](comfy-host-provider-bridge.md): completed historical
  host-provider bridge.

## Authority

- Repository branch/release/validation policy: [`MAINTAINING.md`](../../MAINTAINING.md)
- Development entrypoint: [`../development/README.md`](../development/README.md)
- Active immediate queue: `backend-roadmap-resume-0.6.2.md`
- Target architecture: `python-backend.md`, ADR-001, ADR-002
- Feature-specific behavior: owning Issue

The efficiency protocol chooses the smallest sufficient evidence; it does not weaken
correctness, compatibility, package, live, or release gates.

The D-14 readiness audit authorizes no deletion. Root removal still needs the recorded
consumer/release/lifecycle gates and a separate breaking-change decision. The E-01
inventory authorizes no behavior change, release publication, tag, or Registry action.
