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
   - first READY task: Issue #563 / F-02d settings typed migration contract;
   - D-14/H root removal is parked, not failed.
4. Backend target architecture and compatibility policy:
   [`../architecture/README.md`](../architecture/README.md)
5. Read [`codex-blocker-escalation.md`](codex-blocker-escalation.md) only after a
   documented hard stop or unresolved cross-owner architecture ambiguity. Ordinary
   implementation and test failures remain local task work.
6. Read a topic guide only when the active task touches it:
   - completed D/E execution record: `../architecture/backend-roadmap-resume-0.6.2.md`
   - F-01 typed-boundary audit: `../architecture/python-typed-boundary-f01-audit.md`
   - runtime base/state inventory: `../architecture/python-runtime-base-contract.md`,
     `../architecture/python-runtime-state-inventory.md`
   - repository/filesystem runtime contract: `../architecture/python-runtime-e03-repository-filesystem-contract.md`
   - translation runtime contract: `../architecture/python-runtime-e04-translation-contract.md`
   - Autocomplete runtime contract: `../architecture/python-runtime-e05-autocomplete-contract.md`
   - Wildcard runtime contract: `../architecture/python-runtime-e06-wildcard-contract.md`
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
COMPLETE  #563 F-02a Autocomplete typed result contracts
COMPLETE  #563 F-02b Prompt field-family typed contract
COMPLETE  #563 F-02c canonical Prompt Data typed read/output contract
COMPLETE  #563 affected Prompt-row re-audit
READY     #563 F-02d settings typed migration contract
BLOCKED   #188 G-04 public API snapshot audit until Phase F closes
LATER     G-05 size ratchet / G-06 test ownership
EVENT     next ordinary release N -> later D-14 re-audit
```

The D-14 stop is correct:

- root `__init__.py` still imports root `api.py` for production registration;
- `api.py` and `nodes.py` still consume `wildcard_engine.py`;
- final forms completed after 0.6.2 have no release N;
- consumer evidence and public breaking-change approval do not support removal.

That stop applies only to removal. It does not complete Phase F or G.

## Active F-02d source map

Start with targeted owners rather than the full repository:

```text
docs/architecture/python-typed-boundary-f01-audit.md  # F-02d task card
Issue #563 latest checkpoint
easyuse_anima/settings/schema.py, repository.py, service.py
direct SettingsTests, settings/long-text API routes, Pyright, and import fixtures
```

F-02d gives ordinary and long-text settings one typed normalized model and one pure
v0/raw-to-v1 persisted-document migration. It preserves existing defaults, aliases,
Comfy overlay precedence, first-run autocomplete initialization, atomic locking,
public/API payloads, and root identities. Do not expand into profile/workflow migration
or common error-taxonomy work.

## Following queue

After F-02d:

1. re-audit the affected settings row;
2. execute the next smallest F-02 while any Phase F finding remains;
3. only after Phase F closes, run #188 G-04A against existing
   compatibility/node/API/package fixtures;
4. audit Wildcard and API pure-shim feasibility without deleting root modules;
5. add G-05 changed-path size growth and G-06 test-ownership gates;
6. let the next ordinary release containing final shims become release N;
7. re-audit D-14 only after an event-gate changes.

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
