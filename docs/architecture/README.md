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
- Phase F typed boundaries and Issue
  [#188](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/188) G-04/G-05/G-06
  quality gates are complete. G-CLOSE records zero unfinished executable Phase F/G
  tasks.
- P-WC-01/P-WC-02 completed the Wildcard direct-shim conversion.
- P-API-01 / Issue
  [#582](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/582) completed with a
  **RETAIN** verdict. P-API-02 is not READY.
- D-14/Phase H root removal is correctly parked by production-import, release-window,
  consumer, rollback, and breaking-change gates.
- The completed compatibility lane is recorded in
  [`post-phase-e-maintenance-roadmap.md`](post-phase-e-maintenance-roadmap.md).
- First READY independent task: Issue
  [#199](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/199) / SEC-01 host
  capability and settings threat-model Contract.
- [`security-admin-settings-roadmap.md`](security-admin-settings-roadmap.md) owns that
  active lane. It does not reopen Phase F/G, P-API-02, or D-14.
- Released baseline: 0.6.2. Registry activation is external administration and does
  not block `dev`; do not republish or mutate the release.

```text
COMPLETE Phase D/E/F/G
  -> COMPLETE P-WC direct-shim preparation
  -> RETAIN P-API current root production facade
  -> PARKED H/D-14 compatibility retirement

READY #199 SEC-01 security/admin Contract
  -> CONDITIONAL exact SEC-02
  -> CONDITIONAL narrow implementation/audit

EVENT next ordinary release N
  -> later H/D-14 re-audit
```

## Current code boundary

The current backend is functional and validated.

### Compatibility/lifecycle boundary

- root `__init__.py` imports root `api.py` and passes `api.register_routes` into
  bootstrap initialization;
- importing root `api.py` creates the translation route executor and route application
  before bootstrap freezes the RuntimeServices cleanup plan;
- root `api.py` remains a production route/payload/runtime facade;
- root `wildcard_engine.py` is an import-only compatibility shim over canonical
  Wildcard owners, but its final form has not shipped and release N has not begun.

The API import order is part of the E-09 lifecycle contract. Any future candidate must
preserve one application/executor identity, executor-before-cleanup-plan timing,
repeated initialize behavior, terminal shutdown, and late root-import safety without a
canonical-to-root back-reference.

### Security/admin boundary

Current ComfyUI source provides user-profile selection, origin/host controls, and
optional CORS, but no demonstrated authenticated administrator capability for
custom-node routes. The `comfy-user` header is a user-data selector, not proof of
administrator authority.

Current EasyUseAnima settings routes read and mutate the settings projection. The
projection contains ordinary UI choices together with local/network configuration,
including `wildcard.extra_paths`, `naia.host`, `naia.port`, and
`naia.allow_remote_api`.

SEC-01 must classify deployment trust, route/field sensitivity, authorization owner,
and logging/redaction before any access-control or diagnostics implementation. It must
not assume `request.remote`, Host, Origin, `comfy-user`, or forwarded headers are
administrator authentication.

## Core documents

### Active

- [`security-admin-settings-roadmap.md`](security-admin-settings-roadmap.md):
  Issue #199 deployment/threat matrix, host-capability audit, settings-field
  classification, E-09 guard, verdicts, validation, and Codex start instruction.

### Completed backend and compatibility plan

- [`post-phase-e-maintenance-roadmap.md`](post-phase-e-maintenance-roadmap.md):
  completed Phase F/G plan, P-WC/P-API results, release-N runway, and D-14 event gates.
- [`python-api-papi01-e09-lifecycle-gate.md`](python-api-papi01-e09-lifecycle-gate.md):
  P-API creation-order, identity, terminal lifecycle, cleanup, rollback, RETAIN result,
  and revisit events.
- [`python-runtime-e09-lifecycle-contract.md`](python-runtime-e09-lifecycle-contract.md):
  authoritative bootstrap lifecycle, fixed cleanup order, startup rollback, retained
  no-op boundaries, and terminal shutdown contract.
- [`python-phase-fg-completion-audit.md`](python-phase-fg-completion-audit.md):
  final Phase F/G evidence reconciliation and zero-follow-up decision.
- [`python-size-complexity-g05a-contract.md`](python-size-complexity-g05a-contract.md):
  analyzer-owned line metrics and incremental growth ratchet.
- [`python-test-ownership-g06a-contract.md`](python-test-ownership-g06a-contract.md):
  canonical package direct test owners and shared matrix ownership.
- [`python-public-api-g04a-audit.md`](python-public-api-g04a-audit.md):
  completed public-surface owner map and no-G-04B decision.
- [`python-wildcard-pwc01-facade-feasibility.md`](python-wildcard-pwc01-facade-feasibility.md):
  FEASIBLE Wildcard direct-shim decision and P-WC-02 boundary.
- [`backend-roadmap-resume-0.6.2.md`](backend-roadmap-resume-0.6.2.md):
  completed D-08 and Phase E execution record plus post-Phase-E D-14 verdict.

### Target architecture and policy

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
- [`../development/codex-execution-efficiency.md`](../development/codex-execution-efficiency.md):
  context budget, focused test ladder, evidence reuse, and reporting.

## E-09 conflict guardrails

- A security capability, when justified by a later Contract, is immutable process-start
  configuration owned through RuntimeConfig/bootstrap.
- It does not add a second lifecycle lock, atexit hook, shutdown/reset API, closeable
  registry, or hot reinitialize behavior.
- G-05 thresholds do not split the cohesive lifecycle owner merely to reduce line
  counts.
- G-06 keeps lifecycle integration evidence with bootstrap/runtime and does not add
  production reload/reset behavior.
- Release/package shutdown evidence runs in a fresh process.

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
- Active security/admin queue: `security-admin-settings-roadmap.md`
- Completed Phase F/G and compatibility event gates: `post-phase-e-maintenance-roadmap.md`
- Target architecture: `python-backend.md`, ADR-001, ADR-002
- Feature behavior: owning Issue
- Compatibility decisions: Issue #186 plus the shim registry
- Security/admin settings boundary: Issue #199

The efficiency protocol chooses the smallest sufficient evidence; it does not weaken
correctness, compatibility, package, live, security, or release gates.

No document in this directory authorizes root deletion, public breaking changes,
release publication, tags, Registry actions, or an authentication mechanism by itself.
