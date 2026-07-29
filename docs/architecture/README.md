# Python Backend Architecture

These documents define the target backend architecture, migration rules, and reviewed
cross-surface contracts. They do not imply that every target state is implemented.

Before selecting work, read the bounded execution policy in
[`../development/codex-execution-efficiency.md`](../development/codex-execution-efficiency.md),
then only the active task section, owning Issue, direct source, and direct tests.

## Active sequencing

- Phase D root/package consolidation is complete.
- Issue [#187](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/187)
  and Phase E runtime ownership/lifecycle/test isolation are complete.
- D-14/Phase H root removal is correctly parked: all root surfaces remain retained by
  production-import, release-window, consumer, rollback, or breaking-change gates.
- [`post-phase-e-maintenance-roadmap.md`](post-phase-e-maintenance-roadmap.md)
  owns the current queue.
- First READY task: Issue [#563](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/563)
  / F-01 typed-boundary completion audit.
- After Phase F handoff, Issue
  [#188](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/188)
  owns G-04 public API snapshot, G-05 size/complexity ratchet, and G-06 test ownership.
- Issue [#186](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/186)
  remains the retained compatibility ledger. It owns pre-retirement feasibility and
  later D-14 decisions, not an immediately executable deletion task.
- Released baseline: 0.6.2. Registry activation is external administration and does
  not block `dev`; do not republish or mutate the release.

```text
READY  F-01 typed-boundary completion audit
  -> optional smallest F-02
  -> G-04A public API snapshot coverage audit
  -> optional G-04B gap
  -> Wildcard pure-shim feasibility Contract
  -> API production-facade feasibility Contract
  -> approved internal-consumer Moves only
  -> G-05 size ratchet
  -> G-06 test ownership
  -> next ordinary release N
  -> later H/D-14 re-audit
```

## Current code boundary

The current backend is functional and validated, but two root surfaces are not yet pure
compatibility shims:

- root `__init__.py` imports root `api.py` and passes `api.register_routes` into
  bootstrap initialization;
- root `api.py` remains a production route/payload/runtime facade;
- root `api.py` and `nodes.py` consume `wildcard_engine.py`;
- root `wildcard_engine.py` retains call-time snapshot/source/build adapters over the
  canonical Wildcard package.

Other final shim forms completed after 0.6.2 and therefore have no release N yet.
Older direct/public shims may already satisfy a minimum version window, but absence of
consumer evidence requires conservative retention under ADR-002.

This is not a test or Registry failure. It is an evidence-based compatibility stop.
Root modules may remain indefinitely when their cost is low; deletion is not a measure
of architectural success by itself.

## Core documents

- [`post-phase-e-maintenance-roadmap.md`](post-phase-e-maintenance-roadmap.md):
  active Phase F/G queue, pre-retirement feasibility, release N runway, D-14 triggers,
  validation, and Codex start instruction.
- [`backend-roadmap-resume-0.6.2.md`](backend-roadmap-resume-0.6.2.md):
  completed D-08 and Phase E execution record plus post-Phase-E D-14 verdict.
- [`python-backend.md`](python-backend.md): target ownership, phase definitions, and
  overall Definition of Done.
- [`python-backend-execution-roadmap.md`](python-backend-execution-roadmap.md):
  accumulated historical execution detail; not the current immediate queue.
- [`python-compatibility-shims.md`](python-compatibility-shims.md): current root/shim
  inventory, known consumers, release evidence, and removal gates.
- [`adr-001-modular-monolith.md`](adr-001-modular-monolith.md): feature-oriented modular
  monolith decision.
- [`adr-002-compatibility-shims.md`](adr-002-compatibility-shims.md): support-window,
  evidence, staged-retirement, and public-breaking-change policy.
- [`python-runtime-state-inventory.md`](python-runtime-state-inventory.md) and
  `python-runtime-e02-*` through `python-runtime-e10-*`: completed Phase E contracts.
- [`../development/codex-execution-efficiency.md`](../development/codex-execution-efficiency.md):
  context budget, focused test ladder, evidence reuse, and reporting.

## Cross-surface references

Read only when the task touches the surface:

- [`queue-ui-two-phase-correlation-addendum.md`](queue-ui-two-phase-correlation-addendum.md)
- [`prompt-studio-execution-derived-projection.md`](prompt-studio-execution-derived-projection.md)
- [`seed-ui-semantics-gate.md`](seed-ui-semantics-gate.md)
- [`aio-advanced-integrations-roadmap.md`](aio-advanced-integrations-roadmap.md)
- [`comfy-host-provider-bridge.md`](comfy-host-provider-bridge.md)

## Authority

- Branch/release/validation policy: [`MAINTAINING.md`](../../MAINTAINING.md)
- Development entrypoint: [`../development/README.md`](../development/README.md)
- Active immediate queue: `post-phase-e-maintenance-roadmap.md`
- Target architecture: `python-backend.md`, ADR-001, ADR-002
- Feature behavior: owning Issue
- Compatibility decisions: Issue #186 plus the shim registry
- Quality ratchets: Issue #188

The efficiency protocol chooses the smallest sufficient evidence; it does not weaken
correctness, compatibility, package, live, or release gates.

No document in this directory authorizes root deletion, public breaking changes,
release publication, tags, or Registry actions by itself.
