# EasyUse Anima Development Entry

Use this file as the first development-doc entry point for a new Codex session. Read
only the active task section and its direct owners.

## Read order

1. `docs/development/current-policies.md`
2. [`codex-execution-efficiency.md`](codex-execution-efficiency.md)
   - create one bounded task card;
   - use focused edit-loop tests;
   - run official full once on the final candidate SHA;
   - run package/live/benchmark only when triggered.
3. Active final-convergence queue:
   [`../architecture/backend-final-convergence-roadmap.md`](../architecture/backend-final-convergence-roadmap.md)
4. Active owner: Issue #593.
5. Target architecture and original Definition of Done:
   [`../architecture/python-backend.md`](../architecture/python-backend.md)
6. Read [`codex-blocker-escalation.md`](codex-blocker-escalation.md) only after a
   documented hard stop or unresolved cross-owner architecture ambiguity.
7. Confirm branch/worktree status, direct source and direct tests.

Do not reread all historical roadmaps, closed PRs or completed Phase D/E/F/G/security
lanes. Registry activation is external release administration and does not block
ordinary `dev` work.

## Current state

```text
COMPLETE  Phase D package/root consolidation
COMPLETE  Phase E runtime ownership/lifecycle/test isolation
COMPLETE  Phase F typed boundaries and feature errors
COMPLETE  G-04 public API / G-05 size ratchet / G-06 test ownership
COMPLETE  P-WC Wildcard direct-shim conversion
RETAIN    P-API-01 current root API production facade
COMPLETE  SEC-01 through SEC-05 security/admin lane

READY     #593 FC-01 original Definition-of-Done closure audit
NEXT      FC-02 complete canonical owner-boundary gate
NEXT      FC-03 root API patch-owner migration
NEXT      FC-04 canonical API application/E-09 convergence
NEXT      FC-05 technical completion audit

EVENT     next ordinary release N
LATER     H/D-14 compatibility re-audit
```

The former `no READY task` statement applied to the completed F/G/security and
compatibility-removal lanes. It did not close the original backend Definition of Done.

## Why final convergence remains

The current backend is functional and validated, but two technical gaps remain:

1. the blocking import-boundary gate covers a reviewed subset while the G-06 owner map
   covers the complete canonical package/test surface;
2. root `api.py` still creates the production API application, translation route
   executor, handlers, route definitions and registrar.

P-API-01 retained that facade because the then-current canonical candidates could not
preserve both request-time root patch seams and E-09 executor/cleanup timing. The same
Contract explicitly allows a later revisit after those patch seams move to exact
canonical owners. FC-03 performs that prerequisite before FC-04 reevaluates application
placement.

Actual shim deletion remains release/consumer gated and is not required for technical
architecture completion.

## FC-01 direct reading scope

```text
docs/architecture/backend-final-convergence-roadmap.md      # FC-01 only
docs/architecture/python-backend.md                         # Overall DoD
docs/architecture/python-phase-fg-completion-audit.md
docs/architecture/python-api-papi01-e09-lifecycle-gate.md
docs/architecture/python-compatibility-shims.md
tools/check_python_import_boundaries.py
tests/fixtures/python_import_boundary_contract.v1.json
tests/fixtures/python_test_ownership_contract.v1.json
```

Read direct tests or analyzer output only when the closure matrix needs to verify a
specific row. Do not read every production package during FC-01.

## FC-01 boundary

Production, test, tool and fixture changes are forbidden unless the audit proves that
existing deterministic evidence cannot express one required row.

Classify every original Definition-of-Done item as:

```text
complete
technical gap
compatibility event
deliberate retain
```

Required outputs:

- one compact closure matrix;
- exact gap between import-boundary and G-06 owner coverage;
- confirmed FC-02 owner/role model;
- confirmed FC-03 root patch-owner migration boundary;
- confirmed FC-04 E-09 application/lifecycle boundary;
- corrected next task card if the evidence disproves an assumption.

Do not implement FC-02 or later work in the FC-01 PR.

## Fixed lifecycle and compatibility guards

Later FC tasks must preserve:

- bootstrap as the single lifecycle owner;
- one initialize/shutdown lock and one atexit registration;
- terminal/idempotent shutdown and no hot reinitialize;
- one translation route executor created before cleanup-plan composition;
- executor shutdown as cleanup item 1 and the fixed seven-step cleanup order;
- expected-identity rollback and original startup error;
- route marker retention and no route deregistration;
- no file-I/O limiter or provider/client cleanup invention;
- root/canonical identity and 0.5.2 workflow/profile/settings/API compatibility.

FC-03 may migrate patch ownership but does not change behavior. FC-04 application
construction remains outside `initialize()` unless a separate reviewed Behavior Contract
explicitly changes rollback semantics.

## Validation

### Edit loop

```text
changed-file syntax/static check
one direct focused owner at a time
current analyzer/contract projection
git diff --check
```

The broad quick/full profiles are not edit-loop commands.

### Promotion

- Documentation-only FC-01 reuses current valid code evidence.
- Run official full once when code, tests, tools or shared fixtures change.
- Run validate/pack/archive for import, entrypoint, registration, dependency, archive or
  release changes.
- Run isolated live ComfyUI only for host-visible behavior or FC-05 integration.
- Terminal lifecycle smoke runs in a fresh process; shutdown followed by production
  reinitialize is not supported.

## Technical PRO boundary

Request focused technical PRO review only when direct evidence leaves multiple valid
API/lifecycle designs, the complete owner gate exposes an unresolvable role/cycle
ambiguity, or preserving a supported seam requires a canonical-to-root dependency,
dynamic cleanup-plan mutation or second lifecycle owner.

Routine test failures, helper names, fixture placement and owner-local implementation
choices remain with Codex.

## Completed reference lanes

Read only when a current task touches the boundary:

- completed D/E record: `../architecture/backend-roadmap-resume-0.6.2.md`
- runtime state inventory: `../architecture/python-runtime-state-inventory.md`
- repository/filesystem ownership: `../architecture/python-runtime-e03-repository-filesystem-contract.md`
- translation runtime: `../architecture/python-runtime-e04-translation-contract.md`
- autocomplete runtime: `../architecture/python-runtime-e05-autocomplete-contract.md`
- wildcard runtime: `../architecture/python-runtime-e06-wildcard-contract.md`
- AiO first-pass cache: `../architecture/python-runtime-e08-aio-cache-contract.md`
- E-09 lifecycle: `../architecture/python-runtime-e09-lifecycle-contract.md`
- runtime test isolation: `../architecture/python-runtime-e10-test-isolation-contract.md`
- Phase F/G close: `../architecture/python-phase-fg-completion-audit.md`
- security/admin: `../architecture/security-admin-settings-roadmap.md`
- queue/live UI identity: `../architecture/queue-ui-two-phase-correlation-addendum.md`
- Prompt Studio projection: `../architecture/prompt-studio-execution-derived-projection.md`
- dual-canvas UI: `browser-smoke-matrix.md`
- Registry scanner safety: [`docs/development/registry-scanner-safety.md`](registry-scanner-safety.md)
- workflows: `../Anima AiO/Workflow_Management.md`

No roadmap document alone authorizes root deletion, public breaking changes, release,
tag or Registry publication.
