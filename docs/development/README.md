# EasyUse Anima Development Entry

Use this file as the first development-doc entry point for a new Codex session. Read
only the current READY or event task and its direct owners; do not reopen a completed
lane when neither exists.

## Read order

1. `docs/development/current-policies.md`
2. [`codex-execution-efficiency.md`](codex-execution-efficiency.md)
   - create one bounded task card;
   - use focused edit-loop tests;
   - run official full once on the final candidate SHA;
   - run package/live/benchmark only when triggered.
3. Current final-convergence status and event queue:
   [`../architecture/backend-final-convergence-roadmap.md`](../architecture/backend-final-convergence-roadmap.md)
4. Total Python Convergence Contract:
   [`../architecture/python-total-convergence-contract.md`](../architecture/python-total-convergence-contract.md).
   Active owner #593 and parent #185; compatibility inventory remains Issue #186.
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
COMPLETE  SEC-01 through SEC-05 security/admin lane
COMPLETE  #593 FC-01, FC-02 and FC-03 prerequisites
COMPLETE  FC-04A canonical API application/E-09 lifecycle Contract
COMPLETE  FC-04B canonical API application cohesive Move
COMPLETE  FC-05 technical architecture completion

COMPLETE  PTC-01 through PTC-09A total structure, support and cutover Contract
READY     PTC-09B canonical cutover/legacy removal
NEXT      PTC-10 final audit

EVENT     next ordinary release N
```

## FC completion and active total convergence

FC-05 closes the original ownership/lifecycle Definition of Done. PTC-01 adds the
broader blocking goal: every shipped Python file and size exception has a final owner,
16 responsibility-owned canonical modules are extracted, and all 16 non-entrypoint
legacy root/`anima_prompt` modules are removed after a canonical caller cutover.

## Current execution boundary

PTC-09B is READY after the production-free PTC-09A Contract merges. Do not repeat FC-01
through FC-05 or the completed PTC Move tasks. PTC-09B follows the fixed private
bootstrap package-start sequence, migrates callers to canonical owners and deletes the
exact 16 legacy paths without a replacement facade.

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
- canonical identity and 0.5.2 workflow/profile/settings/API behavior. Root import-path
  identity is preserved only until the reviewed PTC-09B cutover.

FC-03 may migrate patch ownership but does not change behavior. FC-04 application
construction remains outside `initialize()` unless a separate reviewed Behavior Contract
explicitly changes rollback semantics.

FC-04A selects one canonical publish-once immutable application identity, bootstrap
private outer composition and a root exact binder. Its executable Move boundary is
[`../architecture/python-api-fc04-application-lifecycle-contract.md`](../architecture/python-api-fc04-application-lifecycle-contract.md).

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

- Documentation-only roadmap/navigation corrections reuse current valid code evidence.
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

The Total Python Convergence Contract authorizes only the staged PTC-09B root import-path
break after PTC-09A. No roadmap document alone authorizes release, tag or Registry
publication.
