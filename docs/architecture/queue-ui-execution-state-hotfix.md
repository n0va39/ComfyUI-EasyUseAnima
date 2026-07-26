# Queue Execution vs Live UI State Hotfix Lane

## Document status

- Status: active bug-fix execution override
- Snapshot date: 2026-07-25
- Snapshot branch: `dev`
- Snapshot commit: `df74cf9f65d481936122245e90db269113340c78`
- Release owner: [#415](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/415)
- Live-state overwrite owner: [#413](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/413)
- AiO special-seed owner: [#414](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/414)
- Follow-on advanced integrations: [#409](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/409), [#410](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/410), and [#411](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/411)

This runbook owns the next bug-fix ordering after two post-0.5.5 queue/UI
ownership regressions were reproduced from the current code. It overrides the
next-work ordering in the ordinary backend roadmap and the planned AiO advanced
integrations roadmap until the hotfix release gate exits.

It does not rewrite the immutable 0.5.5 release, undo the backend seed
reservation service, or authorize unrelated frontend/backend refactoring.

## 1. Problem statement

The current code sometimes treats a result produced from an old queue snapshot
as a command to mutate the user's current live node state.

```text
queue snapshot S0
  -> backend execution
  -> user edits live node to S1
  -> S0 result arrives
  -> current UI is mutated back toward S0
```

The accepted ownership rule is:

```text
submitted execution snapshot != current editable UI state
```

A queue result may publish preview, execution history, diagnostics, and an
explicitly allowed next state. It may not overwrite current editable inputs
unless it proves that the current relevant revision still equals the revision
that submitted the result.

## 2. Verified failure surfaces

### 2.1 LoRA Preset

`web/js/lora_preset/node_runtime.js` currently handles
`lora_preset_profile.profile_index` in `applyExecutedProfile()` by:

```text
save current profile
  -> set returned profile index
  -> load returned profile
  -> rerender profile and LoRA widgets
```

There is no queue request identity or edit-revision comparison. A user who
switches profiles or edits rows while an older job runs can be forced back to
the old queued profile. The stale path may also save the current profile before
loading the old one.

### 2.2 Prompt Studio Advanced / AdvancedV2

`web/js/prompt_studio/advanced_values.js` currently applies an execution payload
directly to the live node:

```text
advanced_fields
use_naia
resolution bucket/size/custom dimensions
wildcard mode/seed/control
Artist Mix settings
```

It then rerenders the editor. An older queue may therefore replace current text,
selection, field structure, resolution, or seed controls.

### 2.3 Classic / Extend Prompt Studio

`web/js/prompt_studio/studio_values.js` applies returned slot values and active
slot state directly to current widgets. This path requires the same stale-result
protection.

### 2.4 AiO special seed

The backend returns:

```json
{
  "execution_seed": "...",
  "next_seed": "..."
}
```

`web/js/aio/executed_seed_runtime.js` currently writes every editable
`next_seed` into the live seed widget. For `seed=-1` and the default
`seed_after_generate=fixed`, backend reservation resolves a concrete execution
seed and returns it as `next_seed`. The frontend therefore converts the
persistent `Random Each` intent into a fixed number after one completed job.

The rgthree Seed node demonstrates the desired user contract:

- keep `-1/-2/-3` in the live widget;
- resolve a concrete seed only in the submitted prompt copy;
- store the concrete last seed separately; and
- replace the live widget only after an explicit `Use Last` action.

Easy Use Anima keeps backend reservation as the authoritative execution source,
but must adopt the same separation between editable intent and concrete
execution value.

## 3. Active critical path

```text
READY: QSTATE-01  #413 Contract and failure fixtures
  ->   QSTATE-02  #413 shared queue UI transaction owner
  ->   QSTATE-03  #413 LoRA Preset cutover
       +
       QSTATE-04  #413 Prompt Studio cutover
  ->   AIO-SEED-UI-01  #414 seed intent/display Contract
  ->   AIO-SEED-UI-02  #414 backend result identity
  ->   AIO-SEED-UI-03  #414 frontend compare-and-commit
  ->   HOTFIX-RC-01    integrated validation
  ->   HOTFIX-PREP-01  patch release preparation
  ->   HOTFIX-PUBLISH-01 main/tag/Registry
  ->   re-audit and resume #409 -> #410 -> #411
```

QSTATE-03 and QSTATE-04 may run in parallel after QSTATE-02 if their shared
transaction API is merged and their production file sets stay disjoint.
AIO-SEED-UI-01/02 may be planned in parallel after QSTATE-02, but the frontend
cutover must use the reviewed shared transaction API rather than introduce an
AiO-only duplicate.

## 4. Freeze and release rules

While #415 is open:

- new D/E/G/H, AiO Hook, #409, #410, and #411 implementation remains blocked;
- completed refactors and 0.5.5 behavior outside the two bugs remain intact;
- only #413/#414 fixes, tests required to prove them, release preparation, and
  newly discovered P0/P1 regressions may start;
- one PR owns one Contract, infrastructure, feature cutover, or release unit;
- production code never changes in the release-preparation PR;
- the immutable `v0.5.5` tag is never rewritten or reused; and
- when the final scope remains bug fixes only, the default patch candidate is
  `0.5.6`.

Issue #395 may continue tracking external Registry activation of 0.5.5. Its
external checkpoint does not prevent fixing confirmed post-release regressions.
The advanced integration queue additionally remains blocked by #415 even after
#395 closes.

## 5. QSTATE-01 — Contract and failure fixtures

### Type

Contract/test only. Production behavior changes should be zero or limited to
non-observable instrumentation required to freeze the contract.

### Required fixtures

```text
LoRA Q1 profile A -> user edits profile B -> Q1 completes
LoRA Q1 A -> Q2 B -> user edits C -> completion order Q2, Q1
Advanced old fields -> user edits new fields -> old completion
Advanced resolution/wildcard/Artist Mix edits after queue
Classic/Extend old slot payload after current edit
same execution callback delivered twice
node removed/reconfigured before result
queue rejected/cancelled/cleared before result
```

### Decisions to freeze

1. Which submission identity is available in browser, backend, and compatibility
   paths.
2. Which fields are execution-history-only and which are allowed to commit a
   next state.
3. Atomic surface groups and their edit-revision sources.
4. Behavior when identity is unavailable or ambiguous.
5. Duplicate, out-of-order, cancellation, reload, and removal semantics.

Ambiguity must preserve current user input rather than apply the old result.

### Exit gate

- every destructive case is represented by a deterministic failing fixture;
- accepted transaction identity and revision shapes are documented;
- exact QSTATE-02 allowed files and API are frozen; and
- no feature adapter has yet been broadly rewritten.

## 6. QSTATE-02 — Shared queue UI transaction owner

### Candidate owner

```text
web/js/lifecycle/queue_ui_transaction.js
```

The final name may change in QSTATE-01, but it must remain a narrow owner rather
than a generic event bus or service locator.

### Minimum API responsibilities

```text
capture submission snapshot
associate prompt/request identity
mark relevant user edit revision
compare-and-commit eligibility
idempotent settlement
reject/cancel/clear cleanup
node removal/reconfigure/workflow reload disposal
out-of-order protection
```

### Identity contract

Prefer UI-only ephemeral identity from the call-time Comfy execution context:

```text
prompt_id
node_id
list_index or stable request_id
```

Do not serialize that identity into workflows or profiles. Do not change public
node sockets. When a compatibility path cannot provide exact identity, use a
submitted snapshot fingerprint and local monotonic transaction identifier only
when it is sufficient. Otherwise do not mutate the live UI.

### Revision groups

Candidate atomic groups:

```text
lora.profile
lora.rows
prompt.fields
prompt.resolution
prompt.wildcard
prompt.artist_mix
aio.seed
```

A serialization read or queue snapshot capture is not a user edit. Actual DOM,
widget, profile, row, field, or settings changes increment the relevant revision.
Do not split fields that must be committed atomically.

### Exit gate

- QSTATE fixtures cover the owner without feature-specific mocks hiding behavior;
- no document-level permanent listener or unbounded transaction history remains;
- node disposal releases all references;
- duplicate and out-of-order settlement is deterministic; and
- adapters can ask `canCommit` without importing application globals through a
  circular dependency.

## 7. QSTATE-03 — LoRA Preset cutover

### Required behavior

- stale `profile_index` never changes the current selection;
- stale completion never calls `saveProfile()`;
- current rows, strengths, toggles, style prompt, profile identity, and unsaved
  state stay intact;
- no-edit compatible completion may refresh execution-only status without
  unnecessarily loading a profile; and
- provenance, profile API, CAS/revision token, workflow serialization, and
  profile-bar interaction remain unchanged.

### Stop conditions

Stop and split the PR if the fix requires a profile storage schema migration,
profile API redesign, or unrelated profile UI refactor.

## 8. QSTATE-04 — Prompt Studio cutover

### Required behavior

- stale results cannot replace Advanced/AdvancedV2 fields;
- stale results cannot change resolution, wildcard settings, Artist Mix, or NAIA
  editable state;
- stale results cannot replace Classic/Extend slots or visibility;
- stale results cannot rerender the editor and destroy current caret/selection;
- allowed one-shot NAIA or seed state uses compare-and-commit; and
- field linking, autocomplete, highlighting, textarea autosize, workflow
  serialization, and node layout remain intact.

A result may retain previous-execution text or history in a non-editable field,
but it must not silently become the current prompt input.

## 9. AIO-SEED-UI-01 — Intent and display Contract

### Required model

```text
requested selection intent
concrete execution seed
reservation next seed
editable next display value
queue transaction identity
```

The current two-field `execution_seed`/`next_seed` payload is insufficient for
frontend display semantics.

### Special modes

```text
-1 = randomize each queue
-2 = increment the previous concrete stream seed each queue
-3 = decrement the previous concrete stream seed each queue
```

The live widget keeps the special token. The backend reservation service
continues producing the concrete execution seed. `seed_after_generate` may
advance concrete seed state, but must not replace the special mode token.
The interaction between a special token and non-fixed after-generate control is
frozen by golden fixtures to prevent double advancement.

### Concrete mode

For a concrete editable seed, fixed/randomize/increment/decrement may publish the
next concrete value only when the `aio.seed` transaction revision is still
current.

## 10. AIO-SEED-UI-02 — Backend result identity

### Required result information

Candidate shape:

```json
{
  "request_id": "...",
  "requested_seed": "-1",
  "selection": "randomize",
  "after_generate": "fixed",
  "execution_seed": "123",
  "next_seed": "456",
  "next_display_seed": "-1",
  "preserve_selection_intent": true
}
```

Field names may change in the Contract PR. Meaning may not be collapsed again.
The payload remains UI-only and decimal-string-safe for large seeds.

### Required preservation

- browser and headless execution use the same backend reservation semantics;
- cache and sampling receive the concrete execution seed;
- output metadata records the concrete execution seed;
- workflow serialization retains the user's selection intent; and
- special mode does not require frontend RNG.

## 11. AIO-SEED-UI-03 — Frontend publication

### Required behavior

- `-1/-2/-3` remain in the live seed input after any number of completions;
- each queue receives the correct concrete backend-reserved seed;
- concrete seed is published to a separate last-seed state;
- `Use Last` explicitly converts the live widget to a concrete fixed seed;
- `New Fixed Random` explicitly creates one concrete fixed seed;
- older completions do not rollback a newer last-seed record;
- concrete after-generate updates pass the shared compare-and-commit gate; and
- no queue path temporarily mutates the live widget.

The Contract PR decides whether the button label is `Last Queued` or `Last
Executed` based on the exact monotonic ownership available. The label and
implementation must describe the same event.

## 12. Integrated hotfix validation

### Automated/package

```powershell
powershell -ExecutionPolicy Bypass -File tools\check_project.ps1 -Profile full
comfy node validate
comfy node pack
```

Inspect the actual archive for all changed Python, JavaScript, fixture, locale,
and changelog files.

### Queue/live matrix

```text
Legacy Canvas
Node 2.0
single queue
rapid Q1/Q2/Q3
out-of-order callback fixture
user edit while running
queue reject/cancel/clear
node removal/reconfigure/workflow reload
subgraph or attached graph where supported
clean user-data
0.5.5 update user-data
```

### LoRA/Prompt acceptance

```text
Q1 old state -> current user edit -> completion -> current edit preserved
stale LoRA completion -> saveProfile not called
stale Prompt completion -> no field/widget/editor mutation
no-edit compatible result -> allowed update once
duplicate callback -> no-op
workflow save after stale result -> current state serialized
```

### AiO seed acceptance

```text
-1 Q1/Q2/Q3 -> distinct concrete seeds; widget remains -1
-2 stream -> concrete increments; widget remains -2
-3 stream -> concrete decrements; widget remains -3
Use Last -> exact concrete fixed seed
New Fixed Random -> concrete fixed seed
concrete after-generate update with and without intervening user edit
out-of-order and duplicate completion
workflow save/reload
headless/API parity
```

A release candidate fails if any stale execution mutates a newer editable state,
or if a special AiO seed intent is replaced by a concrete result without an
explicit user action.

## 13. Release preparation and publication

When #413 and #414 are complete and the integrated gate passes:

1. choose the patch version; default candidate is `0.5.6`;
2. create a release-only PR with no production Python/JavaScript changes;
3. update version, user-facing changelog, Registry metadata, maintained workflow
   metadata, and aligned release docs;
4. record the exact tested candidate commit and ComfyUI/frontend versions;
5. merge to `main` only after full/package/live evidence;
6. create an immutable annotated tag from the released `main` commit;
7. publish to Registry and read back version, changelog, and package state; and
8. verify update from the public 0.5.5 installation.

Do not rewrite `v0.5.5` or patch production code in the release-preparation PR.

## 14. Resumption gate

The advanced integration and ordinary backend queues become selectable only
after:

- #413 is complete;
- #414 is complete;
- HOTFIX-RC-01 passes at one exact integrated `dev` head;
- patch release preparation, `main` integration, immutable tag, Registry publish,
  and read-back complete; and
- no immediate P0/P1 post-release regression remains open.

At that point re-audit the then-current code and open PRs. The expected advanced
sequence is #409 -> #410 -> #411, but do not start it automatically if new
evidence changes the dependency graph.

## 15. Codex start instruction

```text
Read docs/architecture/queue-ui-execution-state-hotfix.md and Issues #415 and
#413 before selecting any ordinary backend or AiO advanced-feature task.

Start QSTATE-01 only. Reproduce the LoRA Preset, Advanced/AdvancedV2, and
Classic/Extend stale queue-result overwrites in deterministic frontend fixtures.
Inventory the exact onExecuted payloads, user-edit mutation points, queue identity
available from frontend/backend, atomic surface groups, cancellation/removal
boundaries, and allowed execution-derived commits.

Do not implement a broad feature cutover, modify AiO seed semantics, or refactor
LoRA/Prompt Studio structure in QSTATE-01. Freeze the transaction/revision API,
allowed files, stop conditions, and failing examples first.

Run focused tests and tools/check_project.ps1 -Profile full. Record exact
base/head SHA, failure evidence, Contract decisions, rollback boundary, and next
task QSTATE-02. Do not merge, version, tag, or publish without normal review.
```
