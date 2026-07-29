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
   - first READY task: Issue #582 / P-API-01 API facade and E-09 lifecycle feasibility Contract;
   - D-14/H root removal is parked, not failed.
4. Mandatory P-API lifecycle gate:
   [`../architecture/python-api-papi01-e09-lifecycle-gate.md`](../architecture/python-api-papi01-e09-lifecycle-gate.md)
   - preserve one bootstrap lifecycle owner, terminal shutdown, translation-executor
     identity, fixed cleanup order, rollback, and late root-import behavior;
   - P-API-01 is production-free and must return FEASIBLE or RETAIN before a Move.
5. Backend target architecture and compatibility policy:
   [`../architecture/README.md`](../architecture/README.md)
6. Read [`codex-blocker-escalation.md`](codex-blocker-escalation.md) only after a
   documented hard stop or unresolved cross-owner architecture ambiguity. Ordinary
   implementation and test failures remain local task work.
7. Read a topic guide only when the active task touches it:
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
8. Confirm `git status --short`, current branch/worktree, direct source, and direct
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
READY     #582 P-API-01 API facade / E-09 lifecycle Contract
OPTIONAL  P-API-02 only after FEASIBLE verdict
LATER     G-05 size ratchet / G-06 test ownership
EVENT     next ordinary release N -> later D-14 re-audit
```

The D-14 stop is correct:

- root `__init__.py` still imports root `api.py` for production registration;
- root `api.py` remains a production route/payload/runtime facade;
- `wildcard_engine.py` is a direct shim, but that final form has not shipped;
- final forms completed after 0.6.2 have no release N;
- consumer evidence and public breaking-change approval do not support removal.

That stop applies only to removal. P-API-01, G-05, and G-06 remain executable.

## Active P-API-01 source map

Start with targeted owners rather than the full repository:

```text
Issue #582 latest checkpoint
Issue #186 compatibility checkpoint
docs/architecture/post-phase-e-maintenance-roadmap.md  # P-API section
docs/architecture/python-api-papi01-e09-lifecycle-gate.md
root __init__.py and api.py
easyuse_anima/bootstrap.py and runtime.py
easyuse_anima/api/router.py
python-runtime-e09-lifecycle-contract.md
direct API route-owner, bootstrap/lifecycle, compatibility, package/no-host tests
```

P-API-01 must model the current order:

```text
import root api.py
  -> create translation route executor/application
  -> bootstrap.initialize(register_routes)
  -> freeze RuntimeServices cleanup plan
```

The audit compares canonical-application, bootstrap-owned-application, and retained-root
shapes. A move is FEASIBLE only when it preserves one application/executor identity,
creates the executor before cleanup-plan composition, avoids canonical-to-root cycles,
and makes late root `api.py` import side-effect-free with respect to application and
lifecycle state.

P-API-01 does not implement the Move.

## E-09 non-regression summary

- bootstrap is the sole lifecycle owner;
- initialize/shutdown share one lock and atexit is registered once;
- shutdown is terminal/idempotent; no hot reinitialize;
- repeated initialize before shutdown reuses runtime identity and refreshes routes;
- translation route executor is unique and cleanup item 1;
- seven-step cleanup order and expected-identity rollback remain fixed;
- routes/marker remain installed; file-I/O limiters and provider clients are not closed;
- no API application reset/close registry, second lock, second atexit, or production
  module reload is added.

## Following queue

After P-API-01:

1. run one bounded P-API-02 only when the verdict is FEASIBLE;
2. otherwise record RETAIN and continue to G-05;
3. add G-05 changed-path size growth and G-06 test-ownership gates;
4. let the next ordinary release containing final shims become release N;
5. re-audit D-14 only after an event gate changes.

G-05 must not split E-09 lifecycle ownership merely to satisfy a line threshold. G-06
must not add production reset APIs, `importlib.reload()` lifecycle tests, or private
runtime mutation outside `tests/runtime_test_support.py`.

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
- Release lifecycle smoke uses a fresh process for terminal shutdown; shutdown followed
  by production reinitialize is not a supported gate.
- Run benchmark only for performance/output-quality policy.

## Technical PRO boundary

Request focused technical PRO review only when direct evidence leaves multiple valid
cross-boundary designs, an import cycle cannot be avoided by the existing injection
pattern, translation-executor identity cannot precede cleanup-plan creation without a
new lifecycle mechanism, or compatibility evidence cannot distinguish public support
from test-only seams. User preference is not a substitute for technical analysis.

Routine test failures, helper layout, type annotation choices, and owner-local
implementation decisions remain with Codex.
