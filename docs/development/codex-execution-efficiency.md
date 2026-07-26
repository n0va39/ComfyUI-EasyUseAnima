# Codex Execution Efficiency and Test Escalation Protocol

## Status and authority

- Status: active cross-roadmap execution policy
- Applies to: all implementation, maintenance, bug-fix, migration, quality, and release work
- Current active lane: `docs/architecture/queue-ui-execution-state-hotfix.md`
- Follow-on lane: `docs/architecture/aio-advanced-integrations-roadmap.md`
- Ordinary backend lane: `docs/architecture/python-backend-execution-roadmap.md`

This document reduces unnecessary repository reading, agent reasoning, tool calls,
and repeated validation without weakening correctness or release gates.

Use the following authority order:

1. repository policy in `MAINTAINING.md` and `docs/development/current-policies.md`;
2. the current owning Issue and its latest accepted task manifest;
3. the active sequencing document for that task;
4. this execution-efficiency protocol;
5. area-specific implementation documents and historical plans.

A task-specific requirement may add tests or evidence. It may not silently remove a
repository or release gate. When two documents disagree, use the newer explicit
Issue decision and update the stale document before implementing.

## 1. Core rule

Use the smallest evidence set that can disprove the current change, then escalate
only when the change is stable.

```text
inspect
  -> syntax/static check for changed files
  -> focused behavior/contract tests
  -> adjacent-boundary tests only when shared ownership changed
  -> official full once on the final PR candidate
  -> package validation only when package closure can change
  -> live ComfyUI only when host-visible behavior can change
  -> benchmarks only when performance policy is the task
```

Do not use the official `quick` or `full` runner as an edit-loop command. The
current `quick` profile still runs repository-wide Python quality, all frontend
JavaScript syntax checks, all frontend smoke files, TypeScript, and diff checks.
The `full` profile adds the complete Python unittest suite. They are promotion
gates, not substitutes for focused tests.

## 2. Bounded work packet

Before editing, create one compact task card. Do not repeatedly reread every parent
roadmap or issue comment after the card is grounded.

```text
Task ID:
Owner Issue:
Primary class:
Base SHA:
Goal:
Prerequisites:
Allowed production files:
Allowed test/docs files:
Forbidden changes:
Behavior/invariants to preserve:
Focused tests and purpose:
Promotion gates:
Stop conditions:
Next task:
```

The card must be sufficient for a fresh Codex session to continue the work. Link
to the detailed Issue instead of copying its full body into every PR or handoff.

### 2.1 Default context budget

Read only:

1. this policy once per work session;
2. the active sequencing document's current task section;
3. the owning Issue and its latest completion/blocker comment;
4. direct owner source files and their direct tests; and
5. callers/imports found by targeted search.

Do not read the full repository, all historical plans, all closed Issues, or every
test file unless the task is explicitly an inventory/audit task.

### 2.2 Search policy

Prefer bounded commands and exact ranges:

```powershell
git diff --name-only <base>...HEAD
rg -n "<symbol-or-payload>" <known-directories>
git grep -n "<symbol>" -- <known-paths>
```

Avoid broad recursive file dumps and repeated searches that answer the same
question. Record the discovered owner and callers once in the task card.

### 2.3 Existing evidence reuse

Reuse an inventory, golden fixture, browser result, package result, or benchmark
when all of the following hold:

- it was produced from the same commit SHA;
- the relevant code, test, runner, and environment contract did not change;
- the evidence states its command and purpose; and
- no newly discovered failure invalidates it.

Documentation, PR-body, label, and comment-only changes do not invalidate code,
package, browser, or benchmark evidence.

## 3. Primary change classes

Every PR has one primary class. Split a PR when it would require two independent
rollback boundaries.

| Class | Meaning | Typical examples |
| --- | --- | --- |
| `DOC` | Documentation or task ordering only | roadmap, ADR, changelog draft |
| `CONTRACT` | Fixtures/types/contracts with no intended production behavior change | schema fixture, failure reproduction, protocol |
| `PURE` | Deterministic helper or domain logic | parser, normalization, recommendation policy |
| `MOVE` | Mechanical ownership relocation with behavior parity | canonical module extraction, direct alias |
| `ADAPTER` | ComfyUI/custom-node/API boundary | node result payload, provider invocation |
| `UI` | DOM/canvas/editor/current-state behavior | Prompt Studio, LoRA Preset, AiO panel |
| `SCHEMA` | Settings/profile/workflow migration or serialization | versioned generation settings |
| `LIFECYCLE` | Runtime ownership, concurrency, cache, transaction state | queue transaction, provider lifetime |
| `PERF` | Performance policy or benchmark-driven optimization | Torch Compile recommendation |
| `RELEASE` | Version/package/publication metadata only | patch release prep |

Do not mix `MOVE` with observable behavior. Do not mix `RELEASE` with production
code. A `CONTRACT` PR may add a minimal test seam, but must not quietly complete
the later behavior task.

## 4. Test ladder

### E0 — Inspection only

**Purpose:** establish ownership, callers, current behavior, and exact diff.

Required for every task. No command output needs to be pasted in full. Record only
the relevant paths, symbols, and decisions.

### E1 — Changed-file syntax/static sanity

**Purpose:** catch syntax, import, and malformed-diff failures immediately.

Typical commands:

```powershell
python -m py_compile <changed-python-files>
node --check <changed-js-files>
git diff --check
```

Use changed directories with `compileall -q` when several adjacent Python files
changed. Do not compile the entire repository after every edit.

Run targeted Ruff/Pyright only when the task explicitly adds or enrolls a strict
module. Repository-wide quality ratchets remain part of the final official runner.

### E2 — Focused contract/behavior tests

**Purpose:** prove the exact requirement and its nearest regressions.

Typical commands:

```powershell
python -m unittest tests.test_<owner>
python -m unittest tests.test_<owner>.<Class>.<test>
node tests/frontend_<owner>_smoke.mjs
```

A focused test must have a stated purpose. Do not run a test merely because its
name is in the same broad feature area.

### E3 — Adjacent-boundary tests

**Purpose:** protect a shared contract changed by the task.

Run only when the diff changes one of these boundaries:

- shared lifecycle/transaction owner;
- settings/schema/migration used by multiple surfaces;
- API or custom-node invocation adapter;
- registration/import/package boundary;
- shared serialization or cache-key contract.

Choose the direct consumers. Do not run every feature suite.

### E4 — Official full runner

**Purpose:** prove repository-wide integration after the final candidate diff is
stable.

```powershell
powershell -ExecutionPolicy Bypass -File tools\check_project.ps1 -Profile full
```

Rules:

- run once per final PR candidate SHA;
- rerun only after production, tests, runners, shared fixtures, or configuration
  changes that can affect the result;
- do not rerun after PR text, labels, comments, or docs-only follow-up changes;
- if the full runner fails, reproduce the first relevant failure with E2/E3 and
  fix it before running full again;
- do not repeatedly run full to gather the same failure log.

### E5 — Package/import closure

**Purpose:** prove the shipped archive and ComfyUI validation include the required
runtime files and metadata.

```powershell
comfy node validate
comfy node pack
```

Required only when the diff can affect:

- Python package/import/registration closure;
- `.comfyignore`;
- `pyproject.toml`, dependencies, Registry metadata, or version;
- runtime file paths or optional integration files;
- release candidate publication.

Not required for isolated frontend logic, test-only contracts, or ordinary docs.
The integrated release candidate still runs E5 once.

### E6 — Live ComfyUI

**Purpose:** prove host behavior that repository tests cannot model reliably.

Required only for changes to:

- DOM/canvas/pointer/keyboard/focus lifecycle;
- queue submission or execution-result UI behavior;
- node sizing, hidden widgets, workflow serialization, or Node 2.0 compatibility;
- real optional custom-node invocation;
- GPU/model/sampler behavior or output quality.

Run after the final diff is stable, once on Legacy Canvas and once on Node 2.0,
using only the changed flow plus required persistence/queue assertions. Follow
`docs/development/browser-smoke-matrix.md` and reuse evidence for the same SHA.

Pure helpers, contract-only PRs, mechanical moves, and test infrastructure normally
omit E6 with an explicit reason.

### E7 — Benchmark or quality comparison

**Purpose:** support a performance or output-quality policy.

Run only for `PERF` work or when the Issue requires comparative evidence. Correctness
must pass first. Separate cold and warm measurements, record environment, and do
not repeat an expensive benchmark after docs-only changes.

## 5. Promotion schedule

### During implementation

Run E1 and the smallest E2 test after a coherent edit. Stop at the first failure.
Do not run E4, E5, or E6 while the design is still changing.

### Before opening or updating a reviewable PR

Run all required E2 tests and E3 only for changed shared boundaries. Review the
final diff and remove diagnostics, temporary files, and accidental scope changes.

### Final candidate

Run E4 once. Then run E5 and E6 only when their trigger conditions apply. Record
the exact tested SHA.

### Issue-close or release checkpoint

Do not repeat valid per-PR evidence. Run only the integrated checks that require
all child PRs on one exact head. A release candidate runs E4, E5, and the stated
integrated E6 matrix once.

## 6. Test invalidation rules

| Change after a pass | Focused evidence | Full | Package | Live | Benchmark |
| --- | --- | --- | --- | --- | --- |
| PR body, labels, comments | reuse | reuse | reuse | reuse | reuse |
| docs only | reuse unless docs test changed | reuse | reuse | reuse | reuse |
| test expectation/fixture | rerun affected test | rerun before merge | usually reuse | usually reuse | if fixture drives benchmark |
| production in same owner | rerun owner tests | invalidated | if package trigger | if UI/host trigger | if perf logic |
| shared lifecycle/schema/API | rerun direct consumers | invalidated | often invalidated for runtime paths | if host-visible | if perf logic |
| runner/configuration | rerun affected ladder | invalidated | if packaging config | if environment contract | if benchmark harness |
| rebase with disjoint upstream diff | reuse E2/E3; inspect merge | final E4 on rebased SHA | final E5 if required | reuse only if tested code identical | reuse only if code/env identical |
| rebase with overlapping owner | rerun relevant E2/E3 | invalidated | as triggered | as triggered | as triggered |

Evidence cache key:

```text
commit SHA + command + test purpose + relevant environment
```

## 7. Test-purpose record

For each command in a task card or PR, record one line:

```text
<command> — proves <specific invariant>; required because <changed boundary>
```

Example:

```text
node tests/frontend_lora_preset_node_runtime_smoke.mjs
— proves stale completion cannot save/load the current profile after LoRA runtime cutover.
```

Do not paste entire passing logs. Record pass/fail, test count when useful, and the
first actionable failure. Preserve raw logs only when needed for CI/debugging.

## 8. Active hotfix test map

This section applies while Issue #415 owns the active queue.

### QSTATE-01 — Contract and failure fixtures

Primary class: `CONTRACT`.

Edit loop:

```powershell
node --check <new-or-changed-contract-js>
node tests/frontend_lora_preset_node_runtime_smoke.mjs
node tests/frontend_prompt_studio_advanced_values_smoke.mjs
node tests/<new-classic-extend-stale-result-smoke>.mjs
git diff --check
```

Purpose:

- reproduce the stale LoRA profile mutation;
- reproduce Advanced/AdvancedV2 field and settings overwrite;
- reproduce Classic/Extend slot overwrite;
- freeze duplicate, out-of-order, removal, and cancellation decisions.

Do not run live ComfyUI or package checks. Run E4 once when the contract PR is final
because shared frontend test registration may change.

### QSTATE-02 — Shared queue transaction owner

Primary class: `LIFECYCLE`.

Edit loop:

```powershell
node --check web/js/lifecycle/queue_ui_transaction.js
node tests/<queue-ui-transaction-smoke>.mjs
node tests/frontend_host_hook_registry_smoke.mjs  # only if host-hook wiring changes
git diff --check
```

Purpose:

- prove capture, revision, settlement, cancellation, disposal, duplicate, and
  out-of-order semantics without feature-specific UI noise.

No live browser test is required until a feature adapter uses the owner. Run E4
once on the final PR candidate.

### QSTATE-03 — LoRA Preset cutover

Primary class: `UI`.

Edit loop:

```powershell
node tests/<queue-ui-transaction-smoke>.mjs
node tests/frontend_lora_preset_node_runtime_smoke.mjs
node tests/frontend_lora_preset_profile_mutations_smoke.mjs
git diff --check
```

Add entry-lifecycle or save-sync smoke only when those files change.

Live purpose on each canvas:

1. queue Profile A, edit/switch to B, finish A, verify B remains;
2. queue A then B, edit C, deliver out-of-order fixture/result where supported,
   verify C remains;
3. save/reload and verify current profile data is serialized.

Do not rerun unrelated Prompt Studio, AiO, autocomplete, or settings browser flows.

### QSTATE-04 — Prompt Studio cutover

Primary class: `UI`.

Edit loop:

```powershell
node tests/<queue-ui-transaction-smoke>.mjs
node tests/frontend_prompt_studio_advanced_values_smoke.mjs
node tests/<classic-extend-executed-values-smoke>.mjs
git diff --check
```

Run host-hook registry smoke only if hook registration changes. Run autosize,
resolution, autocomplete, or regional tests only when their owners are touched.

Live purpose on each canvas:

1. queue old fields, edit current text/field structure, complete old queue;
2. repeat for resolution/wildcard/Artist Mix atomic groups;
3. verify Classic/Extend slot and visibility edits remain;
4. save/reload and verify current state and caret-safe rerender behavior.

### AIO-SEED-UI-01 — Intent/display Contract

Primary class: `CONTRACT`.

```powershell
node tests/frontend_aio_executed_seed_runtime_smoke.mjs
python -m unittest tests.test_aio_seed_cutover tests.test_seed_adapters
git diff --check
```

Purpose: freeze `requested`, `execution`, `next reservation`, `next display`, and
last-seed meanings for `-1/-2/-3` and concrete seeds. No live or package check.

### AIO-SEED-UI-02 — Backend result identity

Primary class: `ADAPTER`.

```powershell
python -m unittest tests.test_aio_seed_cutover tests.test_seed_adapters tests.test_aio_nodes
node tests/frontend_aio_executed_seed_runtime_smoke.mjs  # when payload parsing changes
git diff --check
```

Add `tests.test_aio_legacy_generation` only if generation-pipeline metadata or
result construction outside the node adapter changes. E5 is not required unless
registration/import/package closure changes.

### AIO-SEED-UI-03 — Frontend compare-and-commit

Primary class: `UI`.

```powershell
node tests/<queue-ui-transaction-smoke>.mjs
node tests/frontend_aio_executed_seed_runtime_smoke.mjs
node tests/frontend_aio_generator_panel_runtime_smoke.mjs
git diff --check
```

Add extension-runtime smoke only if extension hook ownership changes.

Live purpose on each canvas:

1. `-1` across Q1/Q2/Q3: widget remains `-1`, concrete seeds differ;
2. intervening user seed edit: old completion cannot overwrite it;
3. `Use Last` and `New Fixed Random` are the only explicit concrete transitions;
4. workflow save/reload preserves the special token.

### HOTFIX-RC-01

Run once on one exact integrated `dev` SHA:

```powershell
powershell -ExecutionPolicy Bypass -File tools\check_project.ps1 -Profile full
comfy node validate
comfy node pack
```

Then run the exact #413/#414 Legacy/Node 2.0 matrix. Do not repeat every child PR's
manual steps if the integrated flow covers the same invariant.

## 9. Follow-on AiO advanced integration test map

This section becomes active only after the hotfix lane exits and the dependency
order is re-audited.

### #409 — Stage-scoped model patches

#### AIO-SCOPE-01 Contract/migration

```powershell
python -m unittest tests.test_aio_generation_migrations tests.test_aio_generation_settings tests.test_aio_schema_contract
python -m unittest tests.test_aio_first_pass_cache
```

Purpose: legacy missing-scope parity, new-default semantics, patch-order revision,
and cache-key sensitivity. No live test.

#### AIO-SCOPE-02 Variant owner

```powershell
python -m unittest tests.test_aio_generation_lifecycle tests.test_aio_stage_integration_matrix tests.test_aio_model_preparation
```

Add individual stage tests only for stages whose request/model wiring changes.
Purpose: clean base lineage, lazy variant reuse, precedence, and cleanup. No UI
browser test.

#### AIO-SCOPE-03 DAVE UI/cutover

```powershell
node tests/frontend_aio_advanced_settings_dialog_smoke.mjs
node tests/frontend_aio_profile_core_smoke.mjs
python -m unittest tests.test_aio_model_preparation tests.test_aio_generation_settings
```

Live only the changed flows: first-pass-only, all-stage legacy parity, one custom
scope, Compile-before-DAVE, save/reload, and both canvas surfaces. Output/color
comparison is required because the user-visible defect is stage-dependent color
degradation.

#### AIO-SCOPE-04 Other patch audit

Test only each patch whose stage support is being approved. Do not run an exhaustive
Cartesian product of every optional integration.

### #410 — Torch Compile recommendation

#### AIO-COMPILE-01 Diagnostics

Use fake host/environment fixtures. Do not allocate large GPU tensors or compile a
model. Test missing CUDA/KJNodes, input-contract drift, and read-only environment
reporting.

#### AIO-COMPILE-02 Recommendation policy

Use pure policy tests for fixed/variable/unknown shapes and VRAM tiers. Benchmark
only after correctness is stable, on explicitly selected representative systems.
Record cold compile time, warm time, peak VRAM, recompiles, and graph breaks once
per policy revision/environment.

#### AIO-COMPILE-03 UI

Run the Advanced settings dialog smoke and a dedicated recommendation UI smoke.
Live test only button loading/error/supported states, draft-only changes, Cancel,
Apply, and persistence on both canvas modes. Clicking the button must not compile.

#### AIO-COMPILE-04 Integration

Use a risk-based matrix, not every parameter combination. Cover one fixed-shape,
one Highres/variable-shape, one Detailer/USDU case, and the highest-risk approved
patch combination.

### #411 — NegPip Off/On/Turbo

#### AIO-NEGPIP-01 External contract/license boundary

Use fake `CLIPNegPip` node info and result objects. Test dependency absence, V3
output adaptation, contract drift, no eager import, and no vendored upstream code.
No real PPM live test yet.

#### AIO-NEGPIP-02 On mode

Test one adapter invocation, MODEL/CLIP lineage, unchanged positive/negative CFG,
cache separation, metadata, repeat execution, and cleanup. Run one real Anima +
ComfyUI-ppm live smoke after focused/full pass.

#### AIO-NEGPIP-03 Turbo Contract

Use pure parser/conditioning fixtures for top-level items, nesting, escapes,
existing weights, empty input, malformed syntax, neutral negative conditioning,
and stage CFG=1. No UI browser test.

#### AIO-NEGPIP-04 UI/integration

Run mode/persistence UI smoke and a selected compatibility matrix. Prefer pairwise
highest-risk combinations over a full Cartesian product:

- Turbo + Artist Mix;
- Turbo + Mod Guidance;
- Turbo + DAVE/Torch Compile approved order;
- Turbo + Highres;
- Turbo + Detailer;
- Turbo + USDU.

Run Off parity once, On once, and Turbo once per required canvas/model surface.

## 10. Ordinary backend roadmap test map

| Work type | Focused proof | Final additions | Normally omit |
| --- | --- | --- | --- |
| Contract-only | new fixture/contract tests | E4 once if runner/shared fixture changes | live, package |
| Mechanical Move | identity, direct callers, import boundary, package skeleton | E4; E5 when runtime path changes | live |
| Pure domain/service | owner unit tests, targeted syntax/type | E4 | live, package unless closure changes |
| Behavior change | owner golden/error tests, direct consumers | E4; E6 if host-visible | unrelated feature suites |
| Runtime/lifecycle | concurrency, cleanup, retry, fake provider/clock | E4; E6 only for actual host lifecycle | broad UI matrix |
| Settings/schema | defaults, normalization, migration golden, frontend/backend parity | E4; E6 only when UI changes | unrelated model/sampler tests |
| Quality ratchet | exact analyzer/ruff/pyright/import gate | E4 once | live |
| Release-only | metadata/changelog/workflow/version checks | E4 + E5 + required release live/read-back | production edits |

For ordinary roadmap tasks, do not repeat old Move inventories unless `dev` changed
the same owner or the task's stop condition is triggered.

## 11. Agent and token policy

### Default single-agent execution

Use one implementation agent by default. Parallel workers are justified only when:

- file ownership is disjoint;
- no worker depends on another worker's undecided contract;
- each worker receives a bounded task card and exact output format; and
- merging the results is cheaper than one sequential implementation.

Do not spawn multiple agents to reread the same roadmap, independently rediscover
the same owner, or produce overlapping design opinions for a small task.

### Handoff size

Worker handoff should contain only:

```text
finding/decision
files and symbols inspected
specific evidence
patch or recommended change
tests run/not run
blocker or next action
```

Do not include hidden reasoning, full logs, or copied issue bodies.

### External research

Use external upstream research only when the task depends on a current external
contract, version, license, or API. Pin the inspected commit. Do not repeatedly
browse upstream after its contract is frozen unless a version drift is detected.

### Output discipline

- Summarize passing logs; do not paste them.
- Report the first root cause before secondary cascades.
- Link to existing decisions instead of rewriting them.
- Keep one decision ledger per owner Issue.
- Remove temporary diagnostics before final validation.
- Do not create speculative tests for behavior outside the task's accepted scope.

## 12. Compact evidence template

Use this format in PRs and Issue completion comments:

```text
Task: <id / owner>
Class: <primary class>
Base -> Head: <sha> -> <sha>
Changed boundary: <paths/owner>
Preserved invariants: <short list>
Focused: <commands and purpose; pass/fail>
Adjacent: <commands and purpose | not required>
Full: <command, tested SHA, result | not yet required>
Package: <validate/pack result | not triggered>
Live: <Legacy/Node 2.0 changed flow | not triggered>
Benchmark: <environment/result | not triggered>
Rollback: <single boundary>
Next: <task or blocker>
```

The PR body should remain a review aid, not a duplicate architecture document.

## 13. Stop conditions

Stop and record a blocker instead of expanding the search or test scope when:

- required changes exceed the task's allowed production files;
- a shared contract is still undecided;
- current `dev` or an open PR overlaps the same owner;
- a focused failure shows the root cause belongs to another Issue;
- the external custom-node/API contract differs from the frozen fixture;
- package or live validation requires an unavailable dependency/environment;
- a proposed test needs a generic framework larger than the behavior under test;
- the change would combine Move, Behavior, and Release ownership.

A blocker report must identify the missing decision and the smallest next Contract,
not request a broad repository re-audit by default.

## 14. Future scoped-runner automation

The manual protocol above is immediately usable. A future maintenance task may add
a scope-aware wrapper such as:

```text
tools/check_scope.ps1 -Scope <name> -ChangedFrom <sha> -List|-Run
```

A valid implementation must:

- use a reviewed manifest mapping path globs to focused tests and purposes;
- print the selected tests before running them;
- include shared-boundary escalation rules;
- fail closed on unknown runtime paths;
- never claim to replace the final official full runner; and
- keep results deterministic and reviewable.

Do not delay current hotfix work waiting for that automation. Use the task-specific
commands in this document now.
