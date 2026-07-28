# Python Backend Architecture

These documents define the target Python backend architecture, migration rules,
and explicitly reviewed cross-surface execution plans for ComfyUI EasyUse Anima.

They are contracts for future work, not a claim that every target package or
feature already exists. Before selecting a task, read the bounded execution and
test-escalation policy in
[`../development/codex-execution-efficiency.md`](../development/codex-execution-efficiency.md).
Then follow the active sequencing notes below and read only the current task
section, owning Issue, direct owner files, and direct tests.

## Active sequencing notes

- [`codex-execution-efficiency.md`](../development/codex-execution-efficiency.md)
  applies to every roadmap. It defines the bounded task card, focused edit loop,
  final-full-once rule, evidence reuse, and package/live/benchmark triggers.
- Issue [#186](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/186)
  currently owns the active backend queue. Read
  [`backend-roadmap-resume-0.6.2.md`](backend-roadmap-resume-0.6.2.md) before the
  older execution roadmap. The first READY task is D-08t, profile-load route
  composition.
- The reviewed baseline is `dev@a509e87c7021257d514e66710f4ca4afb74c4a05`
  after D-08s / PR #520. D-08q, D-08r, and D-08s are complete.
- Issue [#470](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/470) and
  the 0.6.1 Prompt Studio patch lane are complete. Its projection roadmap remains
  a behavior-contract reference and no longer blocks backend work.
- Issues [#413](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/413),
  [#414](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/414), and
  [#415](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/415) are historical
  queue/live-UI contract sources.
- The current released code baseline is 0.6.2. Comfy Registry manual review or
  activation is external release administration and does not block the `dev`
  refactor queue. Do not republish or mutate the immutable 0.6.2 artifact.
- Before Prompt Studio wildcard next-seed publication or AiO seed work, read
  [`seed-ui-semantics-gate.md`](seed-ui-semantics-gate.md). Prompt Studio and AiO
  seed meanings remain separate.
- Issues #409, #410, #411 and the 0.6.0 advanced-integration release lane are
  complete. Deferred #440/#441, opportunistic cleanup, and unrelated feature work
  do not jump the active D-08 queue.
- The former B-11 host-provider bridge is complete and remains historical.

## Documents

- [`../development/codex-execution-efficiency.md`](../development/codex-execution-efficiency.md):
  cross-roadmap context budget, work-packet format, test ladder, invalidation
  rules, evidence format, and scoped test maps.
- [`backend-roadmap-resume-0.6.2.md`](backend-roadmap-resume-0.6.2.md):
  active Issue #186 checkpoint after D-08s; current code review, D-08t through
  D-08x boundaries, package/live evidence reuse, stop conditions, and Codex start
  instruction.
- [`python-backend.md`](python-backend.md): target architecture, ownership,
  execution phases, validation gates, and overall Definition of Done. Its older
  implementation snapshot is historical where the active resume checkpoint says
  otherwise.
- [`python-backend-execution-roadmap.md`](python-backend-execution-roadmap.md):
  accumulated backend progress and historical task details. For the current
  immediate queue and preflight rules, the 0.6.2 resume checkpoint takes priority.
- [`python-compatibility-shims.md`](python-compatibility-shims.md): compatibility
  surface registry and removal evidence.
- [`adr-001-modular-monolith.md`](adr-001-modular-monolith.md): why the backend
  converges on a feature-oriented modular monolith under `easyuse_anima`.
- [`adr-002-compatibility-shims.md`](adr-002-compatibility-shims.md): policy for
  introducing, supporting, and retiring root compatibility shims.
- [`prompt-studio-execution-derived-projection.md`](prompt-studio-execution-derived-projection.md):
  completed #470 contract separating submitted snapshots from linked-input and
  NAIA execution-derived deltas.
- [`queue-ui-two-phase-correlation-addendum.md`](queue-ui-two-phase-correlation-addendum.md):
  provisional submission, accepted `promptId`, executed-envelope, cache,
  subgraph, mapped-result, and transaction-core contracts.
- [`seed-ui-semantics-gate.md`](seed-ui-semantics-gate.md): Prompt Studio concrete
  after-generate seed versus AiO persistent special-token contract.
- [`queue-ui-execution-state-hotfix.md`](queue-ui-execution-state-hotfix.md):
  historical base runbook for #413/#414/#415.
- [`aio-advanced-integrations-roadmap.md`](aio-advanced-integrations-roadmap.md):
  completed DAVE, Torch Compile recommendation, and NegPip sequencing plan.
- [`aio-hook-extensibility-plan.md`](aio-hook-extensibility-plan.md): follow-on AiO
  extension contract. It does not override a higher-priority bug or active
  backend queue.
- [`comfy-host-provider-bridge.md`](comfy-host-provider-bridge.md): completed
  historical host-provider sequencing addendum.

## Current code boundary

At the D-08s checkpoint:

- root `api.py` remains a temporary compatibility/composition facade;
- canonical route implementations live under `easyuse_anima/api/routes/`;
- `api/router.py` owns injected route definition/signature/registration mechanics;
- `bootstrap.py` owns concrete factory/dependency/correlation composition already
  migrated through D-08s and the production initialization call site;
- seven profile handlers remain directly composed in root `api.py` and are the
  exact D-08t through D-08w queue;
- no current evidence requires changing public routes, payloads, persistence,
  error policy, workflow contracts, or optional-dependency behavior.

This is reviewed transitional debt, not a reason to perform a broad rewrite.
Bootstrap must not import root `api.py`, and D-08 must not remove compatibility
aliases or absorb runtime-lifecycle work.

## Authority and scope

- Repository policy remains authoritative for branches, releases, Registry
  publication, and validation: [`MAINTAINING.md`](../../MAINTAINING.md).
- The development-document entry point remains
  [`docs/development/README.md`](../development/README.md).
- The efficiency protocol selects the smallest sufficient evidence and timing;
  it does not weaken explicit correctness, compatibility, package, live, or
  release gates.
- The active resume checkpoint owns the current D-08 order. The accumulated
  execution roadmap owns historical details; `python-backend.md` and the ADRs own
  target architecture.
- Cross-surface plans may cover frontend state, queue identity, workflow/profile
  compatibility, packaging, and live evidence when inseparable from the feature
  contract.
- Long-term work remains tracked by
  [#184](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/184),
  [#185](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/185),
  [#186](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/186),
  [#187](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/187), and
  [#188](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/188).
- D-14 shim retirement is not authorized by D-08 completion alone. It requires a
  separate compatibility-evidence gate.
- A roadmap note does not itself authorize behavior changes, release publication,
  tag creation, or root-shim deletion.
