# Codex Blocker Triage and Technical PRO Review

## Status and purpose

- Status: active cross-roadmap policy
- Read only when a documented stop condition, repeated final live failure, or
  predeclared technical review gate is reached.
- Complements `codex-execution-efficiency.md`; it does not replace task correctness,
  compatibility, or release gates.

A stop condition starts **bounded triage**. It is not an automatic whole-roadmap stop
or PRO request.

## 1. PRO review definition

PRO review is a **technical-depth escalation**. Use it when the remaining problem
requires one or more of the following:

- comparison of multiple primary implementations or host contracts;
- deep event-ordering, concurrency, lifecycle, cache, graph, or serialization reasoning;
- discrimination among several technically credible root causes;
- proof of a cross-layer invariant that direct focused tests cannot establish;
- security, licensing, untrusted execution, destructive migration, or release-critical
  runtime analysis.

PRO review is not:

- a request for the user to choose an internal implementation;
- a substitute for reading direct owner code;
- an approval ritual after every failed test;
- a whole-repository re-audit;
- a reason to stop when Codex can safely diagnose and correct the task locally.

Product ambiguity is handled separately through the accepted Issue, roadmap, and
compatibility baseline. An irreducible product choice may be returned to the user, but
it is not labelled a PRO review.

A focused PRO review must return an executable result:

```text
verified facts
ranked hypotheses
discriminating evidence
selected minimum correction boundary
rejected alternatives
focused/full/live proof
resume point or hard blocker
```

## 2. Default flow

```text
observed mismatch
  -> classify
  -> localize the first divergent phase
  -> apply the smallest contract-preserving correction
  -> focused test
  -> rerun only the failed live path
  -> continue when green
```

Do not escalate merely because:

- a fixture assumed the wrong host callback order;
- Legacy and Node 2.0 expose the same data at different points;
- one host signal is missing but a deterministic local handoff exists;
- an allowed helper/file boundary needs a small adjustment;
- an environment failure requires one approved rerun;
- the first implementation attempt fails;
- two attempts failed but the failing phase has not been localized.

## 3. Triage levels

### Level 0 — Environment or evidence issue

Examples: stale installed files, browser cache, server lifecycle, process permission,
or a fixture that does not model the supported host.

Action: correct the environment/fixture and rerun the exact failed path once. Do not
change product behavior or request PRO review.

### Level 1 — Local implementation mismatch

Use when the fix remains inside the current owner or an approved adjacent owner, public
contracts stay unchanged, fail-closed remains possible, and rollback remains one bounded
PR.

Action:

- amend the task card;
- implement the minimum deterministic correction;
- update direct tests;
- rerun focused checks and the failed live flow;
- continue to the normal PR gate.

### Level 2 — Bounded contract amendment

Use when one task-local assumption is false but accepted product semantics and public
compatibility remain preservable without a new subsystem.

Examples:

- one deterministic event-turn handoff;
- an internal callback shape change;
- cleanup moved to its existing lifecycle owner;
- an opaque surface token;
- a broad rerender replaced by a narrow feature-owned synchronizer.

Codex may amend contract and implementation together only when inseparable and still one
rollback boundary. Otherwise split one small contract PR from one implementation PR.

### Level 3 — Focused technical PRO review

Request it only when evidence shows routine bounded work is insufficient:

1. The failure spans multiple technical layers and needs primary-source comparison,
   event/concurrency reasoning, or discriminating instrumentation.
2. Multiple credible root causes remain after direct tests and a localization pass.
3. Progress requires ComfyUI core, public node socket, workflow/profile/settings schema,
   external API, Registry/package contract, or unstable external integration changes.
4. Security, privacy, destructive data loss, licensing, or untrusted execution is
   involved.
5. Legacy and Node 2.0 appear to require incompatible persistent behavior.
6. Frozen invariants conflict and no safe fail-closed behavior remains.
7. A release-blocking package/runtime failure cannot be isolated.
8. A predeclared cross-layer review gate is reached, such as `AIO-SEED-UI-01`.

Two failed corrections are evidence, not an automatic trigger. Perform one bounded
diagnostic-localization pass first unless that pass would cross a public, security, or
destructive boundary.

PRO stays limited to the exact blocker and direct owners. It selects a technical
resolution; it does not ask the user to choose among internal designs.

## 4. Diagnostic-localization checkpoint

When a live result is wrong but its layer is unclear, do not make another speculative
behavior change. Record the first divergence:

```text
queue capture
prompt acceptance
backend payload
executed envelope
transaction selection
canCommit result and reason
feature commit callback
canonical widget state
visible DOM/summary state
history/metadata state
terminal cleanup
```

Rules:

- prefer injected diagnostic callbacks or test-only traces over permanent logging;
- record reason codes at the owner making the decision;
- never log prompt text, credentials, tokens, or user data;
- inspect one exact queue before expanding the matrix;
- remove temporary diagnostics before the reviewable PR;
- return to Level 1/2 once the failing phase is proven.

## 5. Self-resolution budget

Codex may try up to two materially different bounded corrections before localization.

Record only:

```text
hypothesis
changed boundary
focused proof
failed live result
why the next attempt is different
```

Do not run official full between failed attempts, retain multiple experiments, or add
unrelated cleanup. If two attempts fail without locating the phase, localize instead of
declaring a hard blocker by count.

## 6. Reporting states

```text
LOCAL TRIAGE
  An owner-local correction or localization pass is available.

TECHNICAL PRO REVIEW
  A technical-depth criterion is named and bounded evidence is attached.

HARD BLOCKER
  Focused review proves that progress needs a forbidden/public/incompatible boundary
  or no viable correction remains.
```

Update an Issue/PR only when the critical path changes, a review candidate is ready, a
technical review starts/completes, a hard blocker is confirmed, or work is handed off.

## 7. QSTATE-04B focused technical review

### 7.1 What the current run proves

```text
backend produced the next Wildcard seed
previous-execution/history publication occurred
visible Advanced Wildcard UI still showed the previous seed/control
```

QSTATE-02D1 already supports exact-output `consumeWithinTurn()` for either listener
order. The failed Node 2.0 run does not by itself prove that envelope delivery or the
transaction gate failed.

QSTATE-04B's commit callback currently changes the hidden canonical `wildcard_seed`
widget. The visible Advanced UI is a separately rendered summary/popup. Historical
working code changed the widget and rerendered the editor, but QSTATE-04A now forbids
broad executed-result rerenders because they can disturb prompt fields and caret state.

Strongest current hypothesis:

```text
transaction succeeds and hidden widget changes
  -> feature-owned visible Wildcard presentation remains stale
```

Other credible hypotheses:

1. `canCommit` rejects because a programmatic callback increments the edit revision.
2. Captured and executed Node 2.0 node objects differ.
3. Queue acceptance, envelope delivery, or terminal cleanup still races.
4. Mapped-count or duplicate protection rejects the commit.

This qualifies for a focused technical PRO review because the observed output does not
identify the first divergent phase. It does not require user input.

### 7.2 Required one-run trace

Before another behavior correction, record:

```text
transaction state/promptId
captured node === onExecuted node
message === executed detail.output
mapped item count
envelope delivered
canCommit + reason
commit callback invoked
hidden wildcard_seed before/after
visible summary before/after
open non-dirty popup input before/after
revision origin
terminal event order
```

Decision table:

| First divergence | Resume action |
| --- | --- |
| hidden widget changes; visible view stays old | add a narrow Wildcard view synchronizer; leave bridge unchanged |
| commit is not invoked; canCommit rejects | correct the named node/revision/acceptance reason |
| envelope missing for exact output | review bridge/event integration |
| terminal cleanup wins | correct queue/terminal ordering |
| mapped count is not one | stay fail-closed; add aggregation only through a separate contract |

### 7.3 Preferred correction if view sync is confirmed

A Prompt Studio-owned adapter should atomically:

```text
set canonical wildcard_seed
update only the Wildcard summary
update an open, non-dirty Wildcard seed input
preserve prompt fields, caret, resolution, Artist Mix, and layout
avoid renderAdvancedEditor()
avoid user-edit callbacks and revision increments
```

Candidate owners:

```text
web/js/prompt_studio/advanced_controls.js
web/js/prompt_studio/advanced_values.js
web/js/prompt_studio/extension_runtime.js
direct Wildcard view-sync smoke
```

### 7.4 Validation and stop point

Focused checks:

```text
executed-event context smoke
queue UI transaction smoke
Prompt Studio Wildcard transaction smoke
Advanced executed-values smoke
narrow Wildcard view-sync smoke
git diff --check
```

Run Node 2.0 first. Run Legacy after Node 2.0 passes. Run official full once on the final
candidate, then create the Draft PR.

Stop again only if localization proves:

- exact output/prompt correlation is unavailable;
- Node 2.0 routes to a different node with no stable mapping;
- ComfyUI core or a public workflow/socket change is required;
- safe view sync requires a broad rerender that violates QSTATE-04A;
- Wildcard and AiO seed semantics must be merged;
- the bounded reason-coded trace still cannot locate the failure.

Otherwise Codex continues with the proven owner-local correction.

## 8. Planned AiO seed review

The focused PRO review after `AIO-SEED-UI-01` remains mandatory because it validates a
cross-layer semantic matrix:

```text
AiO -1/-2/-3 x stored after_generate
AiO concrete seed x after_generate
backend reservation advancement
frontend special-token / last-seed / serialization
non-sharing with Prompt Studio Wildcard
```

It selects or rejects the technical implementation from evidence. It does not ask the
user to choose among equivalent internal designs.
