# EasyUse Anima Development Entry

Use this file as the first development-doc entry point for a new Codex session.
Read only the sections needed by the active task.

## Read order

1. `docs/development/current-policies.md`
2. [`codex-execution-efficiency.md`](codex-execution-efficiency.md)
   - create one bounded task card;
   - use focused edit-loop tests;
   - run official full once on the final candidate SHA;
   - run package/live/benchmark only when triggered.
3. Current backend queue:
   [`../architecture/post-phase-e-maintenance-roadmap.md`](../architecture/post-phase-e-maintenance-roadmap.md)
   - first READY task: Issue #186 / P-API-01 API facade feasibility Contract;
   - D-14/H root removal is parked, not failed.
4. Backend target architecture and compatibility policy:
   [`../architecture/README.md`](../architecture/README.md)
5. Read [`codex-blocker-escalation.md`](codex-blocker-escalation.md) only after a
   documented hard stop or unresolved cross-owner architecture ambiguity. Ordinary
   implementation and test failures remain local task work.
6. Read a topic guide only when the active task touches it:
   - completed D/E execution record: `../architecture/backend-roadmap-resume-0.6.2.md`
   - F-01 typed-boundary audit: `../architecture/python-typed-boundary-f01-audit.md`
   - feature error taxonomy: `../architecture/python-feature-error-taxonomy-contract.md`
   - runtime base/state inventory: `../architecture/python-runtime-base-contract.md`,
     `../architecture/python-runtime-state-inventory.md`
   - repository/filesystem runtime contract: `../architecture/python-runtime-e03-repository-filesystem-contract.md`
   - translation runtime contract: `../architecture/python-runtime-e04-translation-contract.md`
   - Autocomplete runtime contract: `../architecture/python-runtime-e05-autocomplete-contract.md`
   - Wildcard runtime contract: `../architecture/python-runtime-e06-wildcard-contract.md`
   - Wildcard facade feasibility: `../architecture/python-wildcard-pwc01-facade-feasibility.md`
   - AiO cache runtime contract: `../architecture/python-runtime-e08-aio-cache-contract.md`
   - lifecycle runtime contract: `../architecture/python-runtime-e09-lifecycle-contract.md`
   - test-isolation runtime contract: `../architecture/python-runtime-e10-test-isolation-contract.md`
   - compatibility registry: `../architecture/python-compatibility-shims.md`
   - queue identity: `../architecture/queue-ui-two-phase-correlation-addendum.md`
   - Prompt Studio execution projection: `../architecture/prompt-studio-execution-derived-projection.md`
   - dual-canvas UI checks: `browser-smoke-matrix.md`
   - custom-node integrations: `custom-node-integrations.md`
   - Registry scanner prevention for a future release:
     [`docs/development/registry-scanner-safety.md`](registry-scanner-safety.md)
   - workflows: `../Anima AiO/Workflow_Management.md`
7. Confirm `git status --short`, current branch/worktree, direct source, and direct
   tests.

Do not read every roadmap, closed Issue, or historical PR. Registry activation is
external release administration; do not poll or modify an immutable release during
ordinary `dev` work.

## Current state

```text
COMPLETE  Phase D package/root consolidation
COMPLETE  Phase E runtime ownership/lifecycle/test isolation
PARKED    D-14 / Phase H root removal
COMPLETE  #563 Phase F typed-boundary and feature-error work
COMPLETE  #188 G-04 public API snapshot coverage audit
COMPLETE  #186 P-WC-01 Wildcard facade feasibility Contract
COMPLETE  #186 P-WC-02 Wildcard direct-shim Move
READY     #186 P-API-01 API facade feasibility Contract
LATER     G-05 size ratchet / G-06 test ownership
EVENT     next ordinary release N -> later D-14 re-audit
```

The D-14 stop is correct:

- root `__init__.py` still imports root `api.py` for production registration;
- root `api.py` remains a production route/payload/runtime facade;
- `wildcard_engine.py` is a direct shim, but that final form has not shipped;
- final forms completed after 0.6.2 have no release N;
- consumer evidence and public breaking-change approval do not support removal.

That stop applies only to removal. It does not complete Phase F or G.

## Active P-API-01 source map

Start with targeted owners rather than the full repository:

```text
docs/architecture/post-phase-e-maintenance-roadmap.md  # P-API-01 task card
Issue #186 latest checkpoint
root __init__.py and api.py production entry/composition
easyuse_anima/bootstrap.py and easyuse_anima/api/router.py
direct route/API compatibility, entrypoint, package, and import owners
```

P-API-01 is a production-free feasibility Contract. It inventories the root entrypoint,
bootstrap composition, route/payload/runtime helpers, public names, private test seams,
object identities, and import-cycle constraints. It selects one bounded Move only when
the evidence converges; otherwise it records RETAIN. It does not implement the Move.

## Following queue

After P-API-01:

1. run only the bounded P-API-02 Move when P-API-01 is FEASIBLE;
2. add G-05 changed-path size growth and G-06 test-ownership gates;
3. let the next ordinary release containing final shims become release N;
4. re-audit D-14 only after an event-gate changes.

No dedicated release, outbound telemetry, import-time deprecation warning, or public
root removal is authorized by this queue.

## Validation

### Edit loop

```text
changed-file syntax/static check
one task-specific focused target at a time
current direct contract/analyzer fixture
git diff --check
```

The repository `quick` profile is broad and is not a task preflight or per-edit
command.

### Final candidate

- Run official full once on the exact final code/test diff when tests, tools, shared
  fixtures, or production change.
- Documentation-only changes reuse the latest valid code evidence.
- Run package validation only for import/registration/archive/dependency/release
  closure changes.
- Run live ComfyUI only for host-visible behavior.
- Run benchmark only for performance/output-quality policy.

## Technical PRO boundary

Request focused technical PRO review only when direct evidence leaves multiple valid
cross-boundary designs, an import cycle cannot be avoided by the existing injection
pattern, or compatibility evidence cannot distinguish public support from test-only
seams. User preference is not a substitute for technical analysis.

Routine test failures, helper layout, type annotation choices, and owner-local
implementation decisions remain with Codex.
