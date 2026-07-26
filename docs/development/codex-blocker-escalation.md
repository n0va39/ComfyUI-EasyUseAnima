# Codex Blocker Triage and PRO Escalation

## Status and purpose

- Status: active cross-roadmap policy
- Read only when a task reaches a documented stop condition or a final live gate fails.
- Complements `codex-execution-efficiency.md`; it does not replace task-specific correctness or release gates.

A stop condition starts **bounded triage**. It does not automatically stop the whole
roadmap, request PRO review, open another planning issue, or ask the user to choose an
implementation detail that Codex can resolve safely.

## 1. Default rule

Codex continues the current task when all required behavior can still be achieved by a
small change inside the existing ownership and compatibility boundaries.

```text
observed mismatch
  -> classify
  -> try the smallest contract-preserving correction
  -> focused test
  -> rerun only the failed live path
  -> continue when green
```

Do not escalate merely because:

- a test fixture assumed the wrong host callback order;
- Legacy Canvas and Node 2.0 expose the same data at different points in one event turn;
- one optional host signal is missing but a deterministic local handoff exists;
- an allowed file or helper name must change without widening behavior;
- a sandbox/process-spawn failure requires one approved rerun;
- the first implementation attempt fails while the contract remains satisfiable.

## 2. Triage levels

### Level 0 — Environment or evidence issue

Examples:

- sandbox process creation or permission error;
- stale installed node-pack copy;
- browser cache or server lifecycle mismatch;
- test harness differs from the supported browser event model.

Action:

- correct the environment or fixture;
- rerun the exact failed command or live path once;
- do not change production behavior or request PRO review.

### Level 1 — Local implementation mismatch

The observed host behavior differs from an implementation assumption, but all of the
following remain true:

- required user behavior and compatibility invariants are unchanged;
- the fix stays in the current owner or one already-approved adjacent lifecycle owner;
- no public socket, workflow/profile/settings schema, package contract, or ComfyUI core
  patch is required;
- fail-closed behavior remains available;
- rollback remains one bounded PR.

Action:

- amend the task card locally;
- implement the smallest deterministic correction;
- update the direct fixture;
- run focused validation and the failed live scenario;
- continue to the normal PR gate when it passes.

This level does not require a new roadmap document, a new issue, or PRO review.

### Level 2 — Bounded contract amendment

One task-local contract assumption is false, but the accepted product semantics and
public compatibility can still be preserved without expanding to a new subsystem.

Action:

- Codex may amend the direct contract and implementation in the same branch when the
  correction is inseparable and remains one rollback boundary;
- otherwise create one small contract PR followed by the implementation PR;
- record the changed assumption and evidence once in the owning Issue or PR;
- continue without PRO review after focused/full/live gates pass.

Examples:

- replacing synchronous consumption with one deterministic microtask handoff;
- changing an internal callback return shape;
- moving cleanup to the existing lifecycle owner;
- adding one opaque surface token while keeping feature semantics outside the shared
  owner.

### Level 3 — Hard blocker requiring PRO review

Request focused PRO review only when at least one of these conditions is evidenced:

1. The fix requires changing a public node socket, workflow/profile/settings schema,
   external API, Registry/package contract, or ComfyUI core.
2. Backward compatibility or data migration has more than one credible policy choice.
3. The change crosses feature semantics that must remain independent, such as Prompt
   Studio Wildcard concrete next-seed behavior and AiO special-token behavior.
4. Security, credentials, privacy, destructive data loss, licensing, or untrusted code
   execution is involved.
5. Two distinct bounded corrections have both failed the same supported live gate and
   no third correction stays inside the approved boundary.
6. Legacy Canvas and Node 2.0 require incompatible persistent behavior rather than a
   local adapter difference.
7. The required invariant conflicts with another frozen invariant and there is no safe
   fail-closed behavior.
8. A release-blocking package/runtime failure cannot be isolated to the current owner.

PRO review remains focused on the exact blocker and direct owners. Do not request a
whole-repository re-audit.

## 3. Self-resolution budget

Before Level 3 escalation, Codex may try at most **two distinct bounded corrections**.

For each attempt record only:

```text
hypothesis
changed boundary
focused proof
failed live path result
why the next attempt is materially different
```

Rules:

- do not run the official full suite between failed attempts;
- do not broaden the task to unrelated cleanup;
- do not keep multiple experimental implementations;
- use the first correction that satisfies the frozen contract;
- after production/test changes stabilize, run official full once on the final SHA;
- rerun only the affected Legacy/Node 2.0 flow before the integrated release matrix.

If the first bounded correction passes, do not explore a second design for theoretical
completeness.

## 4. Reporting policy

Do not report `PRO review requested` at the first stop-condition observation.

Use these states:

```text
LOCAL TRIAGE
  A contract-preserving correction is available and is being tested.

HARD BLOCKER
  The Level 3 criterion is named, two bounded attempts are exhausted when applicable,
  and production expansion has stopped.
```

Issue/PR updates are required only when:

- the critical path or frozen contract changes;
- a candidate is ready for review;
- a hard blocker is confirmed;
- a task is completed or handed off.

Do not add a new checkpoint comment for every local test failure.

## 5. Current QSTATE-04B application

Observed live behavior:

```text
ComfyUI core normal `executed` listener
  -> node.onExecuted(detail.output)
  -> later Easy Use Anima `executed` listener captures the envelope
```

This invalidates the earlier same-target capture-order fixture, but it does not require
ComfyUI core changes and does not invalidate the two-phase transaction model.

Treat it as Level 1/2 local correction.

### Preferred correction

Use one microtask handoff owned by the existing executed-event context or transaction
adapter:

```text
node.onExecuted(message)
  -> schedule exactly one microtask for editable-result correlation
  -> remaining listeners in the current `executed` dispatch run
  -> envelope is stored for the exact output object
  -> microtask consumes it and runs the existing revision/ordering gate
```

Requirements:

- use `queueMicrotask` or an injected equivalent;
- no `setTimeout`, polling, repeated animation frames, or retry loop;
- keep the exact output-object identity contract;
- consume at most once;
- if the envelope is still missing after the one microtask, fail closed;
- user edit, node disposal, prompt finish, duplicate callback, and mapped multi-result
  checks still run at commit time;
- the shared owner remains seed- and feature-agnostic;
- reuse the bridge for later AiO publication rather than adding a Prompt-Studio-only
  global event mechanism.

### Required focused scenarios

```text
bridge listener before node adapter -> consumes once
node adapter before bridge listener -> one microtask consumes once
cloned output -> no commit
missing envelope after one microtask -> no commit
user edit before microtask -> no commit
node dispose before microtask -> no commit
duplicate callback -> one commit maximum
multiple mapped payload items -> no editable commit
Legacy Canvas and Node 2.0 live changed flow -> pass
```

### Escalate only if

- the exact output object is unavailable even after the current event dispatch;
- the supported frontend does not provide a deterministic microtask boundary;
- solving the mismatch requires replacing `api.dispatchEvent`, patching ComfyUI core,
  or adding a public workflow/socket field;
- two bounded bridge corrections fail in both supported canvases;
- feature-specific payload parsing must move into the shared bridge.

The current observation alone is not a PRO blocker.

## 6. Planned mandatory review remains

The planned focused PRO review after `AIO-SEED-UI-01` remains mandatory because it
validates cross-layer seed semantics, not because of a routine implementation mismatch.

Its scope stays limited to:

```text
AiO -1/-2/-3 x stored after_generate matrix
AiO concrete seed x after_generate matrix
backend reservation advancement
frontend special-token / last-seed / serialization behavior
non-sharing with Prompt Studio Wildcard concrete next-seed behavior
```

All other tasks continue under the Level 0-3 policy above.