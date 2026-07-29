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
- Phase F and Issue
  [#188](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/188) / G-04 public
  API snapshot coverage and G-05 size/complexity ratchet are complete. Issue #188
  continues to own G-06 test ownership.
- P-WC-01/P-WC-02 completed the Wildcard direct-shim conversion with the existing
  canonical service owner. The final form has not shipped, so release N and removal
  remain parked.
- P-API-01 / Issue
  [#582](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/582) completed with a
  **RETAIN** verdict. P-API-02 is not READY.
- The completed evidence and revisit gates are recorded in
  [`python-api-papi01-e09-lifecycle-gate.md`](python-api-papi01-e09-lifecycle-gate.md)
  and preserve the E-09 application/executor timing and root call-time seams.
- First READY task: Issue
  [#188](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/188) / G-06A canonical
  test-ownership Contract.
- Issue [#186](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/186)
  remains the compatibility ledger. It owns pre-retirement evidence and later D-14
  decisions, not an immediately executable deletion task.
- Released baseline: 0.6.2. Registry activation is external administration and does
  not block `dev`; do not republish or mutate the release.

```text
COMPLETE Phase F typed-boundary and feature-error work
  -> COMPLETE G-04A public API snapshot coverage audit
  -> COMPLETE P-WC-01 Wildcard facade feasibility Contract
  -> COMPLETE P-WC-02 Wildcard internal-consumer/facade Move
  -> COMPLETE #582 P-API-01 API facade / E-09 lifecycle Contract (RETAIN)
  -> PARKED P-API-02 until a recorded revisit event
  -> COMPLETE G-05 size ratchet
  -> READY G-06 test ownership
  -> next ordinary release N
  -> later H/D-14 re-audit
```

## Current code boundary

The current backend is functional and validated. The API root surface is not yet a
pure compatibility shim:

- root `__init__.py` imports root `api.py` and passes `api.register_routes` into
  bootstrap initialization;
- importing root `api.py` creates the translation route executor and route application
  before bootstrap freezes the RuntimeServices cleanup plan;
- root `api.py` remains a production route/payload/runtime facade;
- root `wildcard_engine.py` is an import-only compatibility shim over canonical
  Wildcard owners, but its final form has not shipped and release N has not begun.

The API import order is part of the E-09 lifecycle contract, not merely a file-layout
choice. Any candidate canonical owner must preserve one application/executor identity,
executor-before-cleanup-plan timing, repeated initialize behavior, terminal shutdown,
and late root-import safety without a canonical-to-root back-reference.

Other final shim forms completed after 0.6.2 and therefore have no release N yet.
Older direct/public shims may already satisfy a minimum version window, but absence of
consumer evidence requires conservative retention under ADR-002.

This is not a test or Registry failure. It is an evidence-based compatibility stop.
Root modules may remain indefinitely when their cost is low; deletion is not a measure
of architectural success by itself.

## Core documents

- [`post-phase-e-maintenance-roadmap.md`](post-phase-e-maintenance-roadmap.md):
  active queue, pre-retirement feasibility, release N runway, D-14 triggers,
  validation, and Codex start instruction.
- [`python-api-papi01-e09-lifecycle-gate.md`](python-api-papi01-e09-lifecycle-gate.md):
  mandatory P-API-01 creation-order, identity, terminal lifecycle, cleanup, rollback,
  candidate, evidence, G-05/G-06, and release guardrails.
- [`python-runtime-e09-lifecycle-contract.md`](python-runtime-e09-lifecycle-contract.md):
  authoritative bootstrap lifecycle, fixed cleanup order, startup rollback, retained
  no-op boundaries, and terminal shutdown contract.
- [`python-typed-boundary-f01-audit.md`](python-typed-boundary-f01-audit.md):
  completed Phase F typed-boundary inventory and classifications.
- [`python-public-api-g04a-audit.md`](python-public-api-g04a-audit.md):
  completed public-surface owner map, root-name classifications, and no-G-04B decision.
- [`python-size-complexity-g05a-contract.md`](python-size-complexity-g05a-contract.md):
  analyzer-owned line metrics, compact reviewed-overage ledger, and incremental growth
  ratchet.
- [`python-wildcard-pwc01-facade-feasibility.md`](python-wildcard-pwc01-facade-feasibility.md):
  FEASIBLE Wildcard direct-shim decision and P-WC-02 boundary.
- [`python-feature-error-taxonomy-contract.md`](python-feature-error-taxonomy-contract.md):
  executable error inventory, canonical categories, compatibility, and adapter authority.
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
- [`python-runtime-base-contract.md`](python-runtime-base-contract.md) and
  [`python-runtime-state-inventory.md`](python-runtime-state-inventory.md):
  base runtime contract and process-state owner inventory.
- Other completed Phase E feature/test contracts:
  [`python-runtime-e03-repository-filesystem-contract.md`](python-runtime-e03-repository-filesystem-contract.md),
  [`python-runtime-e04-translation-contract.md`](python-runtime-e04-translation-contract.md),
  [`python-runtime-e05-autocomplete-contract.md`](python-runtime-e05-autocomplete-contract.md),
  [`python-runtime-e06-wildcard-contract.md`](python-runtime-e06-wildcard-contract.md),
  [`python-runtime-e08-aio-cache-contract.md`](python-runtime-e08-aio-cache-contract.md), and
  [`python-runtime-e10-test-isolation-contract.md`](python-runtime-e10-test-isolation-contract.md).
- [`../development/codex-execution-efficiency.md`](../development/codex-execution-efficiency.md):
  context budget, focused test ladder, evidence reuse, and reporting.

## E-09 conflict guardrails for later phases

- G-05 thresholds are review triggers and must not split the cohesive lifecycle owner,
  lock, cleanup order, or rollback merely to reduce line counts.
- G-06 keeps lifecycle integration evidence with bootstrap/runtime and must not add a
  production reset API, production module reload, or private state mutation outside
  `tests/runtime_test_support.py`.
- Release/package shutdown evidence runs in a fresh process. Shutdown followed by
  production reinitialize is not supported.
- P-API must not create a second lock, atexit hook, application cleanup registry,
  translation route executor, or runtime owner.

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
- Active immediate queue: `post-phase-e-maintenance-roadmap.md` + Issue #188
- P-API lifecycle compatibility: `python-api-papi01-e09-lifecycle-gate.md`
- Target architecture: `python-backend.md`, ADR-001, ADR-002
- Feature behavior: owning Issue
- Compatibility decisions: Issue #186 plus the shim registry
- Quality ratchets: Issue #188

The efficiency protocol chooses the smallest sufficient evidence; it does not weaken
correctness, compatibility, package, live, or release gates.

No document in this directory authorizes root deletion, public breaking changes,
release publication, tags, or Registry actions by itself.
