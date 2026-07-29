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
3. Active independent maintenance lane:
   [`../architecture/security-admin-settings-roadmap.md`](../architecture/security-admin-settings-roadmap.md)
   - SEC-01 completed with TRUSTED_DEPLOYMENT_ONLY;
   - first READY task: Issue #199 / SEC-02 response-confidentiality Contract;
   - SEC-02 is production-free and must not implement authentication, a token,
     diagnostics, a settings split, or response changes.
4. Completed backend and compatibility state:
   [`../architecture/post-phase-e-maintenance-roadmap.md`](../architecture/post-phase-e-maintenance-roadmap.md)
   - Phase F/G and G-CLOSE are complete; there is no READY Phase F/G task;
   - D-14/H root removal and P-API-02 are event-gated, not failed.
5. E-09/P-API compatibility gate:
   [`../architecture/python-api-papi01-e09-lifecycle-gate.md`](../architecture/python-api-papi01-e09-lifecycle-gate.md)
   - preserve one bootstrap lifecycle owner, terminal shutdown, translation-executor
     identity, fixed cleanup order, rollback, and late root-import behavior;
   - P-API-01 completed with RETAIN; #199 may use RuntimeConfig/bootstrap only as an
     immutable process-capability owner and must not add another lifecycle owner.
6. Backend target architecture and compatibility policy:
   [`../architecture/README.md`](../architecture/README.md)
7. Read [`codex-blocker-escalation.md`](codex-blocker-escalation.md) only after a
   documented hard stop or unresolved cross-owner architecture ambiguity. Ordinary
   implementation and test failures remain local task work.
8. Read a topic guide only when the active task touches it:
   - completed D/E execution record: `../architecture/backend-roadmap-resume-0.6.2.md`
   - Phase F/G completion audit: `../architecture/python-phase-fg-completion-audit.md`
   - security/admin settings boundary: `../architecture/security-admin-settings-roadmap.md`
   - lifecycle runtime contract: `../architecture/python-runtime-e09-lifecycle-contract.md`
   - compatibility registry: `../architecture/python-compatibility-shims.md`
   - queue identity: `../architecture/queue-ui-two-phase-correlation-addendum.md`
   - Prompt Studio execution projection: `../architecture/prompt-studio-execution-derived-projection.md`
   - dual-canvas UI checks: `browser-smoke-matrix.md`
   - custom-node integrations: `custom-node-integrations.md`
   - Registry scanner prevention for a future release:
     [`docs/development/registry-scanner-safety.md`](registry-scanner-safety.md)
   - workflows: `../Anima AiO/Workflow_Management.md`
9. Confirm `git status --short`, current branch/worktree, direct source, and direct
   tests.

Do not read every roadmap, closed Issue, or historical PR. Registry activation is
external release administration; do not poll or modify an immutable release during
ordinary `dev` work.

## Current state

```text
COMPLETE  Phase D package/root consolidation
COMPLETE  Phase E runtime ownership/lifecycle/test isolation
COMPLETE  Phase F typed boundaries and feature errors
COMPLETE  G-04 public API / G-05 size ratchet / G-06 test ownership
COMPLETE  G-CLOSE Phase F/G completion audit
RETAIN    P-API-01; P-API-02 parked
PARKED    D-14 / Phase H root removal
COMPLETE  #199 SEC-01 security/admin host-capability Contract
READY     #199 SEC-02 response-confidentiality Contract
EVENT     next ordinary release N -> later D-14 re-audit
```

The original backend stop is correct:

- root `__init__.py` still imports root `api.py` for production registration;
- root `api.py` remains a production route/payload/runtime facade;
- `wildcard_engine.py` is a direct shim, but that final form has not shipped;
- final forms completed after 0.6.2 have no release N;
- consumer evidence and public breaking-change approval do not support removal.

That stop applies to the completed compatibility lane. It does not block the separate
Issue #199 security/admin Contract.

## Completed SEC-01 boundary

Current primary-source evidence must be treated as follows:

- ComfyUI `comfy-user` selects a user profile; it is not authenticated administrator
  identity;
- origin/host and CORS middleware are request-origin controls, not authorization;
- `request.remote`, Host, Origin, or forwarded headers alone do not prove authority;
- EasyUseAnima `GET /settings` returns the current public settings projection and
  `POST /set_setting` mutates a known setting;
- the projection currently contains local/network configuration such as
  `wildcard.extra_paths`, `naia.host`, `naia.port`, and `naia.allow_remote_api`.

SEC-01 produced:

```text
deployment/threat matrix
route and field sensitivity inventory
host capability verdict
logging/redaction contract
one primary verdict
exact SEC-02 task card only when justified
```

Allowed primary verdicts:

```text
HOST_CAPABILITY
PROCESS_CAPABILITY
TRUSTED_DEPLOYMENT_ONLY
NO_DIAGNOSTICS
```

The primary verdict is **TRUSTED_DEPLOYMENT_ONLY**. A single trusted operator on
loopback is supported; an authenticated reverse proxy is conditionally supported only
when every authenticated principal has equal operator authority and direct bypass is
prevented. Direct LAN/remote, unauthenticated proxy, and managed/multi-tenant exposure
are unsupported. `--multi-user` is not an authorization boundary.

The authoritative result is
[`../architecture/security-admin-settings-sec01-contract.md`](../architecture/security-admin-settings-sec01-contract.md).
SEC-01 added no token, diagnostics endpoint, settings split, authentication
middleware, frontend migration, or lifecycle state.

## E-09 non-regression summary

- bootstrap is the sole lifecycle owner;
- initialize/shutdown share one lock and atexit is registered once;
- shutdown is terminal/idempotent; no hot reinitialize;
- repeated initialize before shutdown reuses runtime identity and refreshes routes;
- translation route executor is unique and cleanup item 1;
- seven-step cleanup order and expected-identity rollback remain fixed;
- routes/marker remain installed; file-I/O limiters and provider clients are not closed;
- no API application or security capability may add a reset/close registry, second
  lock, second atexit, or production module reload.

SEC-01 rejected a process capability for this lane. If a future independently proven
task needs one, it must still be immutable process-start configuration loaded by
RuntimeConfig/bootstrap.

## Following state

After SEC-01:

1. run the exact production-free SEC-02 response-confidentiality Contract in the
   security roadmap;
2. keep diagnostics absent by default when no reliable authorization owner exists;
3. do not reopen Phase F/G, P-API-02, or D-14 as a side effect;
4. let the next ordinary release containing final shims become release N;
5. re-audit D-14 only after an event gate changes.

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
- Run isolated HTTP live smoke for a later backend security behavior change.
- Run browser smoke only when settings UI behavior changes.
- Release lifecycle smoke uses a fresh process; shutdown followed by production
  reinitialize is not a supported gate.

## Technical PRO boundary

Request focused technical PRO review only when primary-source evidence leaves multiple
viable security architectures with materially different trust guarantees, a capability
owner would require changing E-09 lifecycle semantics, or proxy/header normalization
cannot be resolved within the bounded route owner.

A missing ComfyUI admin capability, ordinary test failure, field classification, helper
layout, and owner-local implementation choices remain with Codex.
