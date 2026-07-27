# Prompt Studio Execution-Derived Projection Roadmap

## Status and authority

- Status: active P1 regression plan.
- Owner: Issue #470.
- Released baseline: 0.6.0.
- Default patch candidate: 0.6.1.
- Priority: before #440/#441, ordinary backend refactoring, and opportunistic work.
- Completed #413/#415 remain closed.
- The two-phase queue identity and stale-edit contract remains authoritative.
- This document supersedes only the old QSTATE-04 assumption that linked
  `field_inputs` and NAIA responses are non-projectable submitted snapshots.

```text
submitted editor snapshot != execution-derived result delta
```

Submitted snapshots never regain authority over the current editor. Linked input and
NAIA values may project only through the latest accepted queue transaction and the
relevant field revision.

## 1. Regression and state classes

QSTATE-04A removed broad execution replay. It fixed stale overwrites but also removed:

- linked socket values from Advanced linked textareas;
- NAIA-generated prompt adoption;
- NAIA runtime-resolution adoption.

Do not restore the old `applyAdvancedExecutedInputs()` path. It replaced every mutable
group and rerendered the full editor.

Classify each result field before publication.

### User-authored editable state

```text
ordinary field text and structure
resolution / Artist Mix / editable controls
use_naia request state
linked field local fallback text
```

A submitted snapshot never restores this state.

### Execution-derived projection

```text
resolved linked input string
NAIA-generated prompt
NAIA runtime resolution
Wildcard next-seed result
```

Projection requires latest accepted ownership, current surface revision, current field
structure, one mapped item, and a live node lifecycle.

### Non-editable history

```text
previous Wildcard execution
execution diagnostics/status
```

History does not own editor revisions and does not trigger broad rerender.

## 2. Queue ownership contract

No separate single-queue/multi-queue mode is required.

### Single queue

```text
Q1 accepted
Q1 result arrives
relevant surface unchanged
-> Q1 may project
```

### Rapid queues

```text
Q1=A, Q2=B, Q3=C
Q1 result -> no editable projection
Q2 result -> no editable projection
Q3 result -> C may project
```

Ownership follows latest accepted queue sequence, not completion order.

- A queue rejected before acceptance never becomes owner.
- Once Q3 is accepted, Q1/Q2 remain superseded even if Q3 fails/cancels.
- Failure does not make an older result reappear.
- A user edit after Q3 capture blocks Q3 only for that edited surface.
- Editing field A does not block a current result for field B.

## 3. Linked input contract

Linked execution values are presentation overlays, not automatic local field storage.

On a valid commit:

```text
update linked execution overlay
update the exact mounted textarea
refresh only that field highlight
resize/grow only that textarea when needed
```

Do not:

```text
rewrite advanced_fields
renderAdvancedEditor()
replace other fields
move caret/selection
change resolution or Artist Mix
invoke user-edit callbacks
increment edit revision for the projection itself
```

The linked textarea stays editable.

- User typing updates the local fallback and increments that field revision.
- A pre-edit queue result cannot overwrite it.
- Disconnecting later reveals/preserves the user fallback.
- A later queue may project a new upstream value.
- Execution projection itself is not serialized as the fallback.

Commit-time checks:

```text
field ID still exists
input name still maps to that field
socket still linked to the captured connection generation/fingerprint
field type/pane unchanged
node epoch current
mapped item count == 1
surface revision current
```

Connect, disconnect, or source replacement increments the structure revision.

## 4. NAIA contract

NAIA is a requested generated result, so the accepted latest response becomes canonical
field text.

On a valid commit:

```text
locate exact NAIA field ID
replace only that field text
persist that advanced_fields update
update only its textarea/highlight/height
keep it editable
```

Do not replay other fields, `use_naia`, resolution selection, Wildcard controls,
Artist Mix, or editor structure.

### Multiple NAIA queues

All accepted jobs execute independently; ComfyUI queue submission is not serialized.

```text
Q1/Q2/Q3 generate independently
Q1/Q2 results -> images only, no canvas adoption
Q3 result -> canvas adoption when current
Q3 failure -> no Q1/Q2 fallback
```

### NAIA resolution

Use a separate atomic surface:

```text
prompt.execution.naia_resolution
```

Apply the runtime width/height only when the resolution revision is current. A stale
resolution result does not block an unrelated current NAIA field result.

## 5. Backend UI delta

Do not infer execution changes by diffing full `advanced_fields`.

Retain linked values:

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

Rules:

- NAIA updates are keyed by stable field ID.
- Include only fields actually generated in this execution.
- Omit resolution delta unless NAIA resolution mode produced it.
- Full `advanced_fields` may remain for compatibility/history but is never current
  editable authority.
- Do not stamp prompt IDs or frontend transaction tokens into cacheable UI payloads.
- Do not change public sockets, return order, or workflow schema.
- Multiple mapped payload items remain fail-closed.

## 6. Unified Prompt Studio execution transaction

The exact executed output envelope is consumed once, then feature gates fan out.

```text
capture node + surfaces
-> accept promptId
-> consume exact executed envelope once
-> validate mapped count
-> Wildcard gate
-> linked field gates
-> NAIA field gates
-> NAIA resolution gate
-> settle once
```

Do not create independent Wildcard/linked/NAIA envelope consumers.

### Ownership boundary

`queue_ui_transaction.js` and `executed_event_context.js` remain feature-agnostic. They
own identity, ordering, revisions, lifecycle, settlement, and bounded cleanup.

The Prompt Studio adapter owns field IDs, input mapping, payload parsing, connection
fingerprints, NAIA validation, narrow DOM updates, and existing Wildcard semantics.

### Existing module

Inventory imports before renaming `wildcard_seed_transaction.js`.

- Internal-only: generalize with a move-only unit to `execution_transaction.js`.
- Existing consumer: retain a thin re-export facade.
- Do not combine an avoidable rename with linked/NAIA behavior.
- Do not add a second transaction framework.

### Surfaces

```text
prompt.execution.linked:<fieldId>
prompt.execution.naia:<fieldId>
prompt.execution.naia_resolution
prompt.wildcard_seed_control
```

Increment revisions on user text input, connect/disconnect/source replacement, field
remove/type/pane/enable changes, NAIA structure changes, resolution edits, reconfigure,
and removal.

## 7. Implementation units

Each unit is an independent rollback boundary.

### QSTATE-04C1 — Projection Contract

Type: `CONTRACT`; production unchanged.

Freeze:

- the three state classes;
- latest-accepted ownership and no old-result fallback;
- field-specific revisions and connection fingerprints;
- linked overlay versus NAIA canonical persistence;
- one-envelope fan-out and one settlement;
- mapped/duplicate/missing-identity fail-closed behavior.

Candidate tests:

```text
tests/frontend_prompt_studio_execution_projection_smoke.mjs
tests/frontend_prompt_studio_advanced_values_smoke.mjs
tests/test_prompt_advanced_nodes.py
```

Edit loop: changed-file syntax, projection contract smoke, directly affected existing
Prompt Studio fixtures, `git diff --check`. Run official full once on the final SHA.
Package/live are not triggered.

### QSTATE-04C2 — Unified execution transaction

Type: move-only or narrow `LIFECYCLE`.

- Generalize the Wildcard transaction without visible behavior change.
- Preserve Wildcard queue/revision/duplicate/mapped-item semantics.
- Consume one envelope and expose feature-owned commit callbacks.
- Shared lifecycle does not parse feature payloads.

Candidate files:

```text
web/js/prompt_studio/wildcard_seed_transaction.js
web/js/prompt_studio/execution_transaction.js
web/js/prompt_studio/extension_runtime.js
direct transaction/module-boundary tests
```

Run official full once. Live is required only if behavior changed rather than a pure
move.

### QSTATE-04C3 — Backend delta and linked projection

Type: `BEHAVIOR`.

- Emit explicit NAIA field/resolution deltas.
- Retain `field_inputs` as the linked execution delta.
- Capture linked surfaces and connection fingerprints.
- Project only from the latest accepted transaction.
- Update overlay and exact textarea without full rerender.
- Preserve local fallback serialization.

Candidate owners, confirmed by targeted search:

```text
easyuse_anima/nodes/prompt_advanced_nodes.py
easyuse_anima/prompt/advanced.py
web/js/prompt_studio/advanced_values.js
web/js/prompt_studio/advanced_fields_ui.js
web/js/prompt_studio/serialization.js
web/js/prompt_studio/extension_runtime.js
```

Focused proof:

```text
backend delta active/inactive shape
single linked result
Q1/Q2/Q3 latest ownership
post-queue edit
field A/B independent revisions
disconnect/reconnect/remove/type change
no fallback serialization
mapped/duplicate/missing-envelope no-op
Wildcard parity
```

Run Node 2.0 and Legacy changed flows once, then official full once.

### QSTATE-04C4 — NAIA canonical adoption

Type: `BEHAVIOR/UI`.

- Adopt only explicit NAIA deltas from the latest accepted queue.
- Persist exact NAIA fields while preserving unrelated state.
- Gate runtime resolution separately.
- Keep text editable without broad rerender.

Focused/live proof:

```text
single positive/negative NAIA update
Q1/Q2/Q3 -> Q3 canvas/save only
Q3 failure -> no older fallback
post-queue field edit
field structure/type/pane change
resolution current/stale cases
other field/resolution/Artist Mix preservation
workflow save/reload
```

Use a deterministic local NAIA fixture/server. Run Node 2.0 first, then Legacy, then
official full once.

### QSTATE-04C5 — 0.6.1 patch gate

On one exact integrated `dev` SHA:

```powershell
powershell -ExecutionPolicy Bypass -File tools\check_project.ps1 -Profile full
comfy node validate
comfy node pack
```

Inspect archive closure and run:

```text
Legacy / Node 2.0
single and rapid linked queues
single and rapid deterministic NAIA queues
edit during execution
disconnect/reconnect/remove/reconfigure
reject/cancel where reproducible
workflow save/reload
clean user data / 0.6.0 update user data
Wildcard next-seed regression
AiO special-seed regression
```

Release preparation is metadata-only after production freeze. A production failure
returns to a separate fix PR.

## 8. Test economy

| Unit | Edit loop | Final promotion |
| --- | --- | --- |
| C1 | contract/source fixtures | full once; no live/package |
| C2 | transaction/envelope/Wildcard parity | full once; live only if behavior changed |
| C3 | backend delta + linked fixtures | Node 2.0 + Legacy changed flow; full once |
| C4 | NAIA delta/adoption fixtures | deterministic dual-canvas flow; full once |
| C5 | integrated regressions | full + package + archive + live matrix |

Code/test/runner/shared-fixture changes invalidate relevant evidence. Docs, labels,
comments, and PR prose do not.

## 9. Focused technical-review conditions

Codex resolves ordinary owner-local failures without asking the user to choose an
implementation. Request technical-depth review only if evidence shows:

- one-envelope fan-out requires ComfyUI core/public socket changes;
- stable field identity cannot survive capture and current editor structure;
- NAIA delta cannot be represented without full snapshot replay;
- Legacy and Node 2.0 require incompatible persistent semantics;
- narrow view sync is impossible without destructive full rerender;
- a workflow/settings migration has multiple credible policies;
- reason-coded diagnostics cannot identify the first divergent owner.

A wrong fixture, DOM lookup, listener order, or one bounded implementation failure is
not a review trigger.

## 10. Execution order

```text
READY  QSTATE-04C1  Projection Contract
  -> QSTATE-04C2  unified execution transaction
  -> QSTATE-04C3  backend delta + linked projection
  -> QSTATE-04C4  NAIA adoption + dual-canvas live
  -> QSTATE-04C5  integrated 0.6.1 patch gate
  -> re-audit/resume #440/#441 and ordinary backend queue
```

## 11. Codex start instruction

```text
Read current-policies.md, the universal/task-card parts of
codex-execution-efficiency.md, this document's QSTATE-04C1 section, Issue #470 latest
decision, and direct Prompt Studio payload/transaction tests.

From latest origin/dev, create one QSTATE-04C1 task card. Do not change production.

Freeze fixtures for:
- submitted snapshot vs execution-derived delta;
- single linked/NAIA eligibility;
- Q1/Q2/Q3 latest accepted ownership independent of completion order;
- newer accepted failure with no older fallback;
- field-specific edit/structure revision;
- linked overlay not serialized as fallback;
- NAIA canonical persistence;
- one envelope fan-out/settlement;
- mapped/duplicate/missing identity fail-closed.

During edits run changed-file syntax, the projection contract smoke, directly affected
Prompt Studio fixtures, and git diff --check. Run official full once on the final
Contract SHA. Do not run package/live or start QSTATE-04C2 in the same PR.

Push a dev-target Draft PR with compact evidence. Continue only after review/merge.
PRO review is not pre-scheduled; use it only when the technical conditions above are
evidenced.
```
