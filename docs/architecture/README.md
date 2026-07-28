# Python Backend Architecture

These documents define the target backend architecture, migration rules, and reviewed
cross-surface contracts. They do not imply that every target state is implemented.

Before selecting work, read the bounded execution policy in
[`../development/codex-execution-efficiency.md`](../development/codex-execution-efficiency.md),
then only the active task section, owning Issue, direct source, and direct tests.

## Active sequencing

- Issue [#186](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/186)
  owns the active backend queue.
- [`backend-roadmap-resume-0.6.2.md`](backend-roadmap-resume-0.6.2.md)
  is the current execution source of truth. Read it before the older accumulated
  roadmap.
- Reviewed code baseline: D-08s / PR #520 at
  `a509e87c7021257d514e66710f4ca4afb74c4a05`.
- First READY task: D-08t, one cohesive Move for the seven remaining profile route
  handler compositions.
- Next: D-08u integrated exit audit. Optional D-08v exists only if that audit proves a
  final production Move is necessary.
- Completed #470 and the #413/#414/#415 queue/live-UI lanes remain contract references,
  not active blockers.
- Released code baseline: 0.6.2. Registry activation is external administration and
  does not block `dev`; do not republish or mutate the release.
- Completed #409/#410/#411 and deferred #440/#441 do not jump D-08.
- D-14 or Phase E does not start before D-08u records its prerequisites.

## Current code boundary

At D-08s:

- root `api.py` is a temporary compatibility/composition facade;
- canonical route implementations live under `easyuse_anima/api/routes/`;
- `api/router.py` owns injected route order, definitions/signature, resolver,
  registrar, and idempotent registration;
- `bootstrap.py` owns migrated concrete factory/dependency/correlation composition and
  the production initialization call site;
- seven profile handlers remain directly composed in root `api.py`;
- no reviewed evidence requires changing routes, payloads, persistence, error policy,
  workflow contracts, or optional-dependency behavior.

This is transitional debt, not a reason for a broad rewrite. Bootstrap must not import
root `api.py`; D-08 must not remove compatibility aliases or absorb runtime lifecycle,
repository, translation worker, file-I/O, or behavior changes.

## Core documents

- [`backend-roadmap-resume-0.6.2.md`](backend-roadmap-resume-0.6.2.md):
  active D-08t/D-08u boundaries, current code review, validation reuse, stop conditions,
  and Codex resume instruction.
- [`python-backend.md`](python-backend.md): target ownership and dependency direction.
  Its early implementation snapshot is historical where the active checkpoint differs.
- [`python-backend-execution-roadmap.md`](python-backend-execution-roadmap.md):
  accumulated progress and historical task details; not the current immediate queue.
- [`python-compatibility-shims.md`](python-compatibility-shims.md): supported root/shim
  inventory and removal evidence.
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

D-08 completion alone does not authorize D-14. Root deletion or shim retirement needs
a separate consumer/release-evidence Contract. A roadmap note does not authorize
behavior changes, release publication, tags, or Registry actions.
