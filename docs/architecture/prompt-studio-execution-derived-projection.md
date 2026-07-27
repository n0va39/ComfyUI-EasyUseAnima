# Prompt Studio Execution-Derived Projection Roadmap

## Status and authority

- Status: active P1 regression plan.
- Owner: Issue #470.
- Released baseline: 0.6.0.
- Default patch candidate: 0.6.1.
- Priority: before #440, #441, ordinary backend refactoring, and opportunistic feature work.
- This document does not reopen completed Issues #413 or #415.
- This document preserves the two-phase queue identity and stale-edit protection from
  `queue-ui-two-phase-correlation-addendum.md`.
- This document supersedes only the QSTATE-04 assumption that every
  `advanced_fields`/`field_inputs` execution result is a submitted snapshot that must
  never project to the current canvas.

The required correction is narrower:

```text
submitted editor snapshot
  != execution-derived display/result delta
```

Submitted snapshots must not regain authority over the current editor. Values that do
not exist until execution, such as a linked input value or an NAIA response, may project
only through the latest accepted queue transaction and a field-specific revision gate.

## 1. Verified current behavior

The 0.6.0 queue-ownership work removed broad execution replay from Prompt Studio.
That fixed destructive stale updates, but it also removed normal execution-result
presentation:

- linked Advanced field sockets still reach the Python node and are returned in
  `field_inputs`, but the frontend no longer projects them into the linked textarea;
- NAIA still generates prompt text and may resolve a runtime resolution, but the
  frontend no longer adopts the generated field text;
- Advanced Wildcard next-seed/history remains a separately gated execution result;
- broad `advanced_fields`, resolution, Artist Mix, and editor-state replay correctly
  remains retired.

The old `applyAdvancedExecutedInputs()` path is not a valid rollback target. It replaced
all mutable groups and rerendered the complete Advanced editor. Restoring it would
reintroduce #413, including prompt/caret loss and completion-order-driven UI changes.

## 2. State classification

Every Prompt Studio result field must be assigned to exactly one class before it can be
published.

### 2.1 User-authored editable state

Examples:

```text
ordinary field text
field order/type/pane/enabled/pin
resolution selection
Artist Mix settings
use_naia request controls
local fallback text for a linked field
```

Rules:

- current live state is authoritative;
- a submitted snapshot never restores it;
- queue completion does not rerender the whole editor;
- workflow serialization stores the current live state.

### 2.2 Execution-derived projection state

Examples:

```text
resolved linked input string
NAIA-generated field prompt
NAIA runtime resolution
Wildcard next-seed publication
```

Rules:

- it may project only from the latest accepted queue transaction for that surface;
- it must pass field/surface revision and current-structure checks at commit time;
- projection is narrow and does not grant authority to unrelated payload fields;
- missing or ambiguous identity fails closed.

### 2.3 Non-editable execution history

Examples:

```text
previous Wildcard execution seed/mode
execution diagnostics
safe result status
```

Rules:

- history does not own current editor revisions;
- it may be monotonic or append-only according to its feature contract;
- it does not trigger a broad editor replay.

## 3. User-visible queue contract

The implementation does not branch on a special "single queue" or "multi queue" mode.
Local queue sequence and latest-surface ownership make both cases deterministic.

### 3.1 Single queue

```text
Q1 captured and accepted
Q1 execution-derived value arrives
no relevant user edit or structure change since capture
-> project Q1 value
```

### 3.2 Rapid multiple queues

```text
Q1 captures A
Q2 captures B
Q3 captures C

Q1 result -> no editable projection
Q2 result -> no editable projection
Q3 result -> C may project
```

Completion order is not ownership. Once a newer accepted transaction supersedes an
older transaction for a surface, the older transaction does not regain ownership.

### 3.3 Rejection, failure, and cancellation

- A submission rejected before prompt acceptance does not become the latest owner.
- Once Q3 is accepted, Q1/Q2 remain superseded even if Q3 later fails or is cancelled.
- Failure or cancellation does not cause an older result to appear as a fallback.
- The canvas keeps its current value until a newer valid projection or user edit.

### 3.4 User edit after queue

```text
Q3 accepted
user edits the relevant field/surface
Q3 result arrives
-> preserve user edit
```

An edit to field A must not block a current result for unrelated field B. Revision
ownership therefore uses stable field IDs rather than one node-wide prompt revision.

## 4. Linked input contract

A linked input value is an execution presentation owned by the upstream connection. It
is not automatically the permanent local field text.

### 4.1 Storage

Store the latest projected value in the existing linked-input overlay/cache owned by the
node, keyed by the field input name or stable field ID.

Do not rewrite `advanced_fields` merely because a linked value executed.

### 4.2 Narrow view update

On a valid commit:

```text
update linked execution overlay
update the exact field textarea if mounted
refresh only that field's highlight
recalculate/grow only that textarea when required
```

Do not:

```text
renderAdvancedEditor()
replace other fields
move caret/selection
change resolution or Artist Mix
invoke a user-edit widget callback
mark the projection as a user edit
```

### 4.3 Editing while connected

The textarea remains editable.

- User typing updates the local fallback text and the current visible draft.
- The edit increments the linked field surface revision.
- A result from a queue captured before that edit cannot overwrite it.
- If the socket is disconnected later, the user-authored fallback remains.
- A later queue after the edit may project its newly resolved upstream value again.

Execution projection itself must not silently serialize the upstream result as the local
fallback.

### 4.4 Structure validation

Before projection, verify:

- the field ID still exists;
- its input name still maps to the same field;
- it is still linked;
- the connection generation/fingerprint captured for the transaction is still current;
- field type/pane has not changed;
- node lifecycle epoch and mapped-item policy pass.

Disconnect/reconnect counts as a new structure revision even when the displayed text is
unchanged.

## 5. NAIA contract

NAIA differs from a linked overlay. The user explicitly requests generated prompt text
for later editing and reuse, so an accepted NAIA result becomes canonical field text.

### 5.1 Field update

On a valid commit:

```text
locate the exact NAIA field ID
replace only that field's canonical text
persist advanced_fields for that field update
update only its mounted textarea/highlight/height
leave it editable
```

Do not replay the queue's other fields, `use_naia` snapshot, resolution selection,
Wildcard controls, Artist Mix, or editor structure.

### 5.2 Multiple NAIA queues

All accepted jobs execute independently. The frontend does not serialize ComfyUI queue
submission around NAIA responses.

```text
Q1/Q2/Q3 each generate their own image and NAIA response
Q1 result -> no canvas adoption
Q2 result -> no canvas adoption
Q3 result -> adopt Q3 NAIA field delta when current
```

Until Q3 returns, the existing canvas text remains. If Q3 fails, do not adopt Q1/Q2 as a
fallback.

### 5.3 NAIA resolution

When the queue used NAIA resolution mode, publish a separate runtime resolution delta.
It uses one atomic surface:

```text
prompt.execution.naia_resolution
```

Apply width/height and the corresponding resolution presentation only when that surface
is still current. A user resolution edit after queue blocks the result without blocking
an unrelated NAIA field update.

## 6. Backend UI-delta contract

The frontend must not infer execution-derived changes by diffing a full submitted
`advanced_fields` snapshot.

Retain the existing linked input map:

```json
{
  "field_inputs": {
    "field_positive_general": "resolved connected text"
  }
}
```

Add explicit NAIA deltas:

```json
{
  "naia_field_updates": {
    "positive_naia": "generated prompt"
  },
  "naia_resolution_update": {
    "width": 1024,
    "height": 1536
  }
}
```

Contract rules:

- `naia_field_updates` is keyed by stable field ID, not pane position.
- Include only fields actually generated by this execution.
- Omit `naia_resolution_update` unless NAIA resolution mode produced it.
- Keep full `advanced_fields` in the UI payload only when compatibility/history still
  needs it; it is never current editable authority.
- Do not add prompt IDs, frontend transaction tokens, or list indexes to cacheable UI
  payloads.
- Do not change public node sockets, return order, or workflow schema.
- Multiple mapped payload items remain fail-closed for editable projection unless a
  later feature contract defines aggregation.

## 7. Unified Prompt Studio execution transaction

The exact `executed` output envelope can be consumed once. Wildcard, linked inputs, and
NAIA must therefore share one Prompt Studio execution transaction instead of creating
independent envelope consumers.

```text
capture Prompt Studio node + surfaces
-> accept promptId
-> consume exact executed envelope once
-> validate payload item count
-> fan out feature-owned commit attempts
   - Wildcard gate
   - linked field gates
   - NAIA field gates
   - NAIA resolution gate
-> settle once
```

### 7.1 Shared owner boundaries

`queue_ui_transaction.js` and `executed_event_context.js` remain feature-agnostic. They
own identity, ordering, revisions, lifecycle, settlement, and bounded cleanup only.

The Prompt Studio adapter owns:

- field IDs and input names;
- payload parsing;
- linked connection fingerprints;
- NAIA field/type validation;
- narrow DOM and canonical field mutation;
- Wildcard feature semantics already frozen by the seed gate.

### 7.2 Existing Wildcard transaction module

Before changing the module name, perform one targeted import/export inventory.

- If `wildcard_seed_transaction.js` is repository-internal and has no unsupported
  consumer, use a move-only unit to generalize it to `execution_transaction.js`.
- If a consumer relies on the current import, retain a thin re-export facade and place
  behavior in the generic owner.
- Do not combine an avoidable mechanical rename with linked/NAIA behavior changes.
- Do not create a second transaction framework merely to avoid the rename.

### 7.3 Surface IDs

```text
prompt.execution.linked:<fieldId>
prompt.execution.naia:<fieldId>
prompt.execution.naia_resolution
prompt.wildcard_seed_control
```

Capture only surfaces relevant to the submitted node state. Surface revisions increase
on:

- user text input for that field;
- socket connect/disconnect or source replacement;
- field delete, type/pane change, or enable/disable;
- NAIA field structure change;
- NAIA resolution control edit;
- node reconfigure/remove lifecycle.

Commit-time validation repeats structure checks. A captured surface token alone is not
proof that the current field still matches.

## 8. Implementation units

Each unit is one rollback boundary. Do not merge contract, mechanical move, feature
behavior, and release metadata into one PR.

### QSTATE-04C1 — Projection contract

Type: `CONTRACT`.

Goals:

- freeze the three state classes;
- freeze latest-accepted-queue ownership;
- freeze no-fallback after a newer accepted failure;
- freeze linked overlay versus NAIA canonical persistence;
- freeze field-specific revisions and connection fingerprints;
- prove one envelope fan-out and one settlement;
- add failing/current characterization where useful.

Production files: none.

Candidate tests:

```text
tests/frontend_prompt_studio_execution_projection_smoke.mjs
tests/frontend_prompt_studio_advanced_values_smoke.mjs
tests/test_prompt_advanced_nodes.py
```

Validation:

```text
changed MJS syntax
projection contract smoke
existing queue transaction/envelope smoke only when imported contract changes
git diff --check
official full once on final Contract SHA
```

Package/live are not triggered.

### QSTATE-04C2 — Unified execution transaction

Type: `MOVE` or narrow `LIFECYCLE`.

Goals:

- generalize the Wildcard-only adapter without changing visible behavior;
- preserve existing Wildcard queue, revision, duplicate, mapped-item, and live evidence;
- make one executed-envelope consumption capable of feature fan-out;
- expose feature-owned commit callbacks without parsing their payloads in the shared
  lifecycle owner.

Candidate files:

```text
web/js/prompt_studio/wildcard_seed_transaction.js
web/js/prompt_studio/execution_transaction.js
web/js/prompt_studio/extension_runtime.js
related direct tests and module-boundary assertions
```

Choose rename/facade only after the targeted inventory. Run the official full once on
the final PR SHA. Live is required only if behavior changes rather than a pure move.

### QSTATE-04C3 — Backend deltas and linked projection

Type: `BEHAVIOR`.

Goals:

- emit explicit `naia_field_updates` and optional resolution delta;
- retain `field_inputs` as the linked execution delta;
- capture linked field surfaces and connection fingerprints;
- project only the latest accepted transaction;
- update linked overlay and the exact mounted textarea only;
- preserve local fallback serialization.

Candidate owners:

```text
easyuse_anima/nodes/prompt_advanced_nodes.py
easyuse_anima/prompt/advanced.py
web/js/prompt_studio/advanced_values.js
web/js/prompt_studio/advanced_fields_ui.js
web/js/prompt_studio/serialization.js
web/js/prompt_studio/extension_runtime.js
```

Use the current canonical owners found by targeted symbol search; do not fall back to a
root compatibility shim merely because an old document names it.

Focused proof:

```text
backend delta shape and absence when inactive
single linked projection
Q1/Q2/Q3 latest ownership
post-queue field edit
field A/B independent revisions
disconnect/reconnect and field removal
no local-fallback serialization
multiple mapped/duplicate/missing-envelope fail-closed
existing Wildcard parity
```

Run Node 2.0 and Legacy linked-field changed flows once on the final behavior diff, then
the official full runner once.

### QSTATE-04C4 — NAIA canonical adoption and live matrix

Type: `BEHAVIOR/UI`.

Goals:

- adopt only explicit `naia_field_updates` from the latest accepted queue;
- persist the exact NAIA field update while preserving unrelated fields;
- keep the textarea editable without a broad rerender;
- gate NAIA resolution independently;
- prove rapid queue behavior with deterministic NAIA responses.

Focused proof:

```text
single positive/negative NAIA update
Q1/Q2/Q3 -> Q3 canvas/save only
Q3 accepted failure -> no Q1/Q2 fallback
post-queue NAIA field edit
field structure/type/pane change
NAIA resolution current/stale cases
other field/resolution/Artist Mix preservation
workflow save/reload
```

Live proof uses a deterministic local NAIA fixture/server rather than relying on random
external responses. Run Node 2.0 first, then Legacy Canvas. Run official full once on the
final PR SHA.

### QSTATE-04C5 — 0.6.1 patch gate

Type: `RELEASE` after production freeze.

On one exact integrated `dev` SHA:

```powershell
powershell -ExecutionPolicy Bypass -File tools\check_project.ps1 -Profile full
comfy node validate
comfy node pack
```

Inspect archive closure and run the combined live matrix:

```text
Legacy Canvas / Node 2.0
single and rapid linked queues
single and rapid deterministic NAIA queues
edit during execution
disconnect/reconnect/remove/reconfigure
queue rejection/cancel where reproducible
workflow save/reload
clean user data
0.6.0 update user data
Wildcard next-seed regression check
AiO special-seed regression check
```

Release preparation changes version/changelog/Registry/workflow release metadata only.
Any production failure returns to a separate fix PR.

## 9. Test-economy map

Use task-specific focused tests during edits. Do not rerun the repository-wide quick or
full profile after every correction.

| Unit | Edit-loop proof | Final promotion |
| --- | --- | --- |
| C1 Contract | contract/source-boundary fixtures | full once; no live/package |
| C2 lifecycle/move | transaction, envelope, Wildcard parity | full once; live only if behavior changed |
| C3 linked behavior | backend delta + linked projection fixtures | Node 2.0 + Legacy changed flow; full once |
| C4 NAIA behavior | NAIA delta/adoption fixtures | deterministic Node 2.0 + Legacy flow; full once |
| C5 release | integrated regressions | full + package + archive + live matrix |

A code/test/runner/shared-fixture change invalidates relevant evidence. Documentation,
Issue comments, labels, and PR prose do not.

## 10. Stop and focused technical-review conditions

Codex resolves ordinary owner-local failures without asking the user to choose an
implementation. Request focused technical-depth review only when evidence shows one of
the following:

- the output envelope cannot fan out without changing ComfyUI core or the public socket;
- stable field identity cannot survive queue capture and current editor structure;
- NAIA deltas cannot be represented without replaying the complete submitted snapshot;
- Legacy Canvas and Node 2.0 require incompatible persistent semantics;
- narrow linked/NAIA view updates are impossible without a destructive full editor
  rerender;
- the fix requires a workflow/profile/settings migration with multiple credible policy
  choices;
- reason-coded diagnostics cannot identify the first divergent owner.

Do not stop merely because a fixture, DOM lookup, listener order, or one bounded
implementation attempt is wrong.

## 11. Current execution order

```text
READY  QSTATE-04C1  projection Contract
  -> QSTATE-04C2  unified Prompt Studio execution transaction
  -> QSTATE-04C3  backend delta + linked input projection
  -> QSTATE-04C4  NAIA canonical adoption + dual-canvas live
  -> QSTATE-04C5  integrated 0.6.1 patch gate
  -> resume #440/#441 and ordinary backend queue after re-audit
```

The first Codex task is QSTATE-04C1 only.

## 12. Codex start instruction

```text
Read:
- docs/development/current-policies.md
- the universal/task-card sections of codex-execution-efficiency.md
- this document's QSTATE-04C1 section
- Issue #470 latest decision
- direct Prompt Studio payload/transaction tests

Create one bounded QSTATE-04C1 task card from latest origin/dev.
Do not implement production behavior.

Freeze fixtures for:
- submitted snapshot versus execution-derived delta classification;
- single queue linked and NAIA projection eligibility;
- Q1/Q2/Q3 latest accepted ownership independent of completion order;
- newer accepted failure with no older fallback;
- field-specific edit/structure revisions;
- linked overlay not serialized as local fallback;
- NAIA canonical field persistence;
- one executed-envelope fan-out and one settlement;
- mapped/duplicate/missing identity fail-closed.

Use changed-file syntax, the new projection contract smoke, directly affected existing
Prompt Studio fixtures, and git diff --check during edits. Run official full once on the
final Contract SHA. Do not run package/live and do not start QSTATE-04C2 in the same PR.

Push a dev-target Draft PR with compact evidence. Proceed to QSTATE-04C2 only after the
Contract is reviewed and merged. PRO review is not pre-scheduled; use it only if this
document's technical stop conditions are evidenced.
```
