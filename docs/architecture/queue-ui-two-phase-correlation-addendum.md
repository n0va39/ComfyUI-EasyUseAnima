# Queue UI Two-Phase Correlation Addendum

## Status and authority

- Status: active sequencing correction for Issues #413 and #415
- Snapshot branch: `dev`
- Snapshot commit: `0caf4e7cd79f01ab5f65bd9c6171b8bdfe31ec7f`
- Completed prerequisites:
  - PR #412 merged as `c3d97ccf9a390220c887542b3249315a12fe6284`
  - PR #417 merged as `0caf4e7cd79f01ab5f65bd9c6171b8bdfe31ec7f`
- Supersedes: the exact-identity-at-submission assumption in the QSTATE-01/QSTATE-02 sections of `queue-ui-execution-state-hotfix.md`
- Does not supersede: the stale-result preservation rule, feature ownership boundaries, hotfix release gate, or test-escalation policy

QSTATE-02A correctly stopped before production changes. It proved that ComfyUI does
not know the effective `list_index` when the frontend captures the user's queue
snapshot. `list_index` is created later inside the backend node invocation. The
previous Contract therefore required information before the host could produce it.

This addendum removes that false dependency without weakening stale-result safety.

## 1. Verified host facts

The following facts were checked against the current Easy Use Anima `dev` tree and
the inspected ComfyUI/ComfyUI_frontend versions.

1. The frontend knows the local node instance and edit revisions before queueing.
2. `queuePrompt()` returns an accepted `prompt_id` only after the server accepts the
   submission.
3. The ComfyUI backend creates `list_index` inside `CurrentNodeContext` while mapping
   one effective node invocation.
4. The websocket `executed` event carries the current `prompt_id`, execution node id,
   display node id, and output object.
5. ComfyUI core passes only `detail.output` to `node.onExecuted()` and drops the outer
   envelope at that boundary.
6. `ComfyApi` is an `EventTarget`; its `addEventListener()` forwards capture options.
7. UI output is cacheable. A volatile `prompt_id` or provisional submission token
   must not be stamped into cacheable UI output merely to recover frontend identity.
8. Mapped UI values are flattened in invocation order. An output array with multiple
   items is ambiguous for an editable next-state commit unless a feature explicitly
   defines aggregation.
9. For subgraphs, the backend execution node id and the frontend display node may be
   different. Core routing to the frontend node is authoritative for local UI
   ownership.

## 2. Corrected identity model

The hotfix uses two required identity phases and one optional invocation phase.

### 2.1 Provisional submission

Created before `queuePrompt()` calls the host.

```text
local transaction id
frontend node object / node epoch
opaque feature surface tokens
captured edit revisions
local queue sequence
```

This phase does not contain `prompt_id` or `list_index`.

### 2.2 Accepted submission

Created only after `queuePrompt()` succeeds.

```text
provisional transaction
+ accepted promptId
```

A rejected queue cancels the provisional transaction. A result without a matching
accepted `promptId` cannot mutate editable state.

### 2.3 Executed-event envelope

Recovered from the outer ComfyUI `executed` event rather than from cacheable feature
payloads.

```text
promptId
executionNodeId
optional displayNodeId
exact output object passed to node.onExecuted()
```

A narrow capture-phase listener records the envelope in a `WeakMap` keyed by the
output object. `node.onExecuted(message)` consumes that envelope synchronously. The
entry is removed on consume and by bounded fallback cleanup.

### 2.4 Optional per-invocation identity

`listIndex` is required only when a feature intends to commit one specific mapped
invocation to editable state.

For this hotfix:

- one feature payload item may use the accepted submission identity;
- zero payload items perform no commit;
- multiple payload items are history/diagnostic only by default;
- mapped editable commit remains fail-closed until that feature defines and tests an
  aggregation or backend invocation-stamp Contract.

The critical path therefore does not require backend `list_index` stamping.

## 3. Cache, subgraph, and compatibility rules

### Cache

- The executed-event envelope `promptId` is authoritative for the current run.
- Do not place `promptId`, a random frontend transaction token, or another volatile
  submission id in cacheable UI output.
- A cached result may update preview/history when its current event envelope matches.
- A cached result may update editable next state only when the accepted transaction,
  feature revision, and single-item policy all pass.

### Subgraph and display routing

- Key editable ownership by the actual frontend node object and a node lifecycle
  epoch, not by assuming that its id equals the backend execution node id.
- Preserve `executionNodeId` and `displayNodeId` as diagnostics and optional feature
  checks.
- When ComfyUI cannot route an output to the intended frontend node, do not search the
  whole graph and guess a target.

### Missing host data

- Missing event envelope, missing `promptId`, cloned output identity, or disposed node
  means no editable commit.
- These paths may still publish safe global diagnostics that do not reference a live
  node.
- Do not add public sockets, workflow fields, a generic event bus, or a backend server
  patch to recover identity in this hotfix.

## 4. Revised critical path

```text
DONE: QSTATE-01   characterization and original Contract fixtures (PR #417)
DONE: QSTATE-02A  host feasibility probe; exact listIndex-at-capture rejected
  -> READY: QSTATE-02B  two-phase submission/envelope Contract amendment
  -> QSTATE-02C  shared transaction core
       +
     QSTATE-02D  narrow executed-event envelope bridge
  -> QSTATE-03  LoRA execution-result replay retirement
       +
     QSTATE-04  Prompt Studio feature-owned cutover
  -> AIO-SEED-UI-01/02/03
  -> HOTFIX-RC-01
  -> 0.5.6 preparation/publication
```

After QSTATE-02B is merged, QSTATE-03 may proceed in parallel with QSTATE-02C/D if it
removes live profile replay and does not introduce a second transaction framework.
QSTATE-04 and AIO frontend compare-and-commit wait for QSTATE-02C/D.

## 5. QSTATE-02B — Two-phase Contract amendment

### Type

`CONTRACT`. No production behavior change.

### Required changes

Update the reference transaction fixture so it proves:

- provisional capture does not require host-generated identity;
- successful queue acceptance binds an exact `promptId`;
- rejection cancels provisional state;
- the executed envelope is matched by `promptId` and frontend node ownership;
- edit revision, latest queue ordering, settlement, and node disposal remain intact;
- multiple mapped payload items cannot commit editable state by default;
- missing envelope and cloned/unknown output fail closed;
- terminal transactions and ordering references are bounded and released.

Add a focused executed-event context fixture that models this ordering:

```text
ComfyUI core registers a normal executed listener
Easy Use Anima later registers a capture listener
executed event dispatch
capture listener records detail.output -> envelope
core listener invokes node.onExecuted(detail.output)
node adapter consumes the exact envelope
entry is released
```

### Candidate files

```text
tests/frontend_queue_ui_transaction_smoke.mjs
tests/frontend_executed_event_context_smoke.mjs
tools/check_frontend.ps1                 # only when registering the new smoke
```

### Focused validation

```powershell
node --check tests/frontend_queue_ui_transaction_smoke.mjs
node --check tests/frontend_executed_event_context_smoke.mjs
node tests/frontend_queue_ui_transaction_smoke.mjs
node tests/frontend_executed_event_context_smoke.mjs
git diff --check
```

Run the official full runner once on the final Contract PR SHA. Package and live
ComfyUI checks are not triggered.

### Exit gate

- the fixture no longer requires `listIndex` during provisional capture;
- event-envelope and output-object correlation is deterministic in the fixture;
- mapped/multiple-result behavior is explicitly fail-closed;
- no production module or feature adapter is implemented;
- QSTATE-02C/D file boundaries and stop conditions are frozen.

## 6. QSTATE-02C — Shared transaction core

### Candidate owner

```text
web/js/lifecycle/queue_ui_transaction.js
```

### Minimum responsibilities

```text
captureProvisional(node, surfaces)
acceptPrompt(transaction, promptId)
markEdited(node, surfaces)
canCommit(transaction, envelope, surface)
settle(transaction)
cancel(transaction, reason)
finishPrompt(promptId)
disposeNode(node)
```

Names may change, but responsibilities may not expand.

The core owns only:

- local node lifecycle epoch;
- opaque surface revisions;
- prompt acceptance;
- latest submission ordering;
- compare eligibility;
- terminal cleanup and bounded retention.

It does not own feature fields, profile data, prompt schemas, payload parsing, or DOM
mutation.

### Focused validation

```powershell
node --check web/js/lifecycle/queue_ui_transaction.js
node tests/frontend_queue_ui_transaction_smoke.mjs
git diff --check
```

No browser smoke is required before a feature adapter consumes the core. Run the
full runner once on the final PR SHA.

## 7. QSTATE-02D — Executed-event envelope bridge

### Candidate owner

```text
web/js/lifecycle/executed_event_context.js
```

### Responsibilities

- idempotently install one `executed` capture listener on the Comfy API host;
- record only the current event envelope keyed by the exact output object;
- expose synchronous consume/peek behavior to node adapters;
- delete entries on consume and bounded fallback cleanup;
- publish prompt terminal cleanup for `execution_success`, `execution_error`, and
  `execution_interrupted` when available;
- remove listeners on runtime retirement.

It is not a generic event bus and does not register feature callbacks.

### Focused validation

```powershell
node --check web/js/lifecycle/executed_event_context.js
node tests/frontend_executed_event_context_smoke.mjs
node tests/frontend_queue_ui_transaction_smoke.mjs
git diff --check
```

Add `frontend_host_hook_registry_smoke.mjs` only if that existing owner is modified.
Live validation waits for QSTATE-03/04.

### Stop conditions

Stop and record a blocker if:

- the supported frontend does not run a later-registered capture listener before the
  core normal listener;
- core clones `detail.output` before calling `node.onExecuted()`;
- the bridge requires patching ComfyUI core or replacing `api.dispatchEvent`;
- a public workflow field or node socket becomes necessary;
- the implementation starts collecting feature-specific payloads.

Only these conditions justify another PRO-level review.

## 8. Feature cutover corrections

### QSTATE-03 — LoRA Preset

The backend `profile_index` result is execution metadata, not authority over the
current profile editor.

Default implementation:

- retire execution-result calls to `saveProfile`, `setProfileIndex`, `loadProfile`,
  profile scrolling, and editable rerender;
- optionally store the executed index in a non-editable history/status field;
- do not add transaction complexity unless a real editable next-state requirement is
  demonstrated.

This task can proceed after QSTATE-02B without waiting for the envelope bridge when it
only removes live replay.

### QSTATE-04 — Prompt Studio

Classify result fields before wiring the transaction owner.

Never replay these submitted snapshots into current editable state:

```text
advanced_fields / field_inputs
base resolution selection
Artist Mix settings
Classic/Extend widget and slot state
current profile-like editor structure
```

Feature-owned compare-and-commit is reserved for intentional next state such as:

```text
accepted NAIA fill result
wildcard next seed/control where still current
non-editable previous-execution history
linked-input execution presentation
```

A payload containing multiple mapped items performs no editable commit unless a
separate feature Contract defines aggregation.

### AiO seed

- special tokens `-1/-2/-3` never require `listIndex` to remain visible;
- concrete execution seed stays history/last-seed state;
- only a concrete editable after-generate update uses prompt transaction revision;
- use the executed-event envelope for `promptId`; do not stamp it into cacheable UI
  payloads.

## 9. Terminal cleanup and practical bounds

Deterministic host signals should be used when available, but the hotfix does not wrap
every queue-management API merely to observe pending-job deletion.

Required cleanup:

- queue rejection cancels provisional state;
- node remove/reconfigure/workflow reload disposes node state;
- execution success/error/interrupted finishes accepted prompt state;
- settlement removes completed transactions;
- a small per-node/per-prompt cap evicts superseded transactions that receive no
  terminal host event.

Do not introduce polling, long-lived timers, or an unbounded history map.

## 10. Codex continuation instruction

```text
Use the existing clean branch/worktree codex/qstate-02-transaction-owner.
Read only this addendum, Issues #413/#415 latest decisions, the merged QSTATE-01
fixture, ComfyUI executed-event adapter, and the direct tests.

Start QSTATE-02B only. Amend the reference Contract from exact identity at provisional
capture to provisional -> accepted promptId -> executed envelope. Add the narrow
EventTarget ordering/output-object fixture. Do not implement production modules.

Run changed-file syntax, the two focused smokes, and git diff --check during the edit
loop. Run the official full runner once on the final candidate SHA. Push and open a
dev-targeting Draft PR with compact evidence.

After QSTATE-02B review/merge, continue with QSTATE-02C and QSTATE-02D as separate PRs.
Request another PRO review only if a listed QSTATE-02D stop condition is observed.
```
