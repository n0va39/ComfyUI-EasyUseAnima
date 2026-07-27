# EasyUse Anima Development Entry

Use this file as the first development-doc entry point when starting from a new
conversation.

## Read Order

1. `docs/development/current-policies.md`
2. [`docs/development/codex-execution-efficiency.md`](codex-execution-efficiency.md)
   - create one bounded task card;
   - use focused edit-loop tests;
   - run the official full runner once per final candidate SHA;
   - escalate to package, live, and benchmark evidence only when triggered.
3. Only after a documented stop condition or final live-gate failure, read
   [`docs/development/codex-blocker-escalation.md`](codex-blocker-escalation.md)
   before requesting PRO review. A stop condition starts bounded local triage; it
   is not an automatic whole-roadmap stop.
4. While Issue #470 is open, read
   [`docs/architecture/prompt-studio-execution-derived-projection.md`](../architecture/prompt-studio-execution-derived-projection.md)
   and only the current QSTATE-04C task section. It owns the 0.6.0 regression
   correction that distinguishes submitted editor snapshots from linked-input and
   NAIA execution deltas.
5. Queue identity or stale-result lifecycle work may also require
   [`docs/architecture/queue-ui-two-phase-correlation-addendum.md`](../architecture/queue-ui-two-phase-correlation-addendum.md).
   It remains the identity/revision foundation, but its older QSTATE-04 field-input
   classification is superseded by the Issue #470 projection roadmap.
6. Python backend architecture or migration work:
   [`docs/architecture/README.md`](../architecture/README.md)
7. Active frontend maintenance execution plan:
   `docs/development/frontend-maintenance-execution-plan.md`
8. Current released baseline: `docs/development/0.6.0.md`
9. Relevant topic guide:
   - Registry publish or flagged-version prevention:
     `docs/development/registry-scanner-safety.md`
   - workflow docs or release templates: `docs/Anima AiO/Workflow_Management.md`
   - user-facing AiO docs: `docs/Anima AiO/README.md`
   - custom-node model patch integrations: `docs/development/custom-node-integrations.md`
   - current frontend maintenance roadmap and Issue #14 close boundary:
     `docs/development/frontend-maintenance-roadmap.md`
   - repeatable legacy-canvas and Node 2.0 browser validation:
     `docs/development/browser-smoke-matrix.md`
   - Safe PAG stage-scope risk-based live evidence:
     `docs/development/aio-safe-pag-live-matrix.md`
   - SageAttention stage-scope risk-based live evidence:
     `docs/development/aio-sage-live-matrix.md`
   - historical Issue #14 PR #18 execution plan:
     `docs/development/issue-14-frontend-js-maintenance.md`
   - deferred Node 2.0 DOM widget resize investigation:
     `docs/development/node2-dom-widget-resize-limitation.md`
   - language or locale work: `docs/development/language-management.md`
10. `git status --short`
11. Relevant source and tests for the target area.

Do not read every roadmap or historical document by default. The efficiency
protocol defines the maximum initial context and the conditions that justify
expanding it. The blocker-escalation document is conditional context and should
not be loaded during ordinary successful tasks.

## Source Map

- Current policy baseline: `docs/development/current-policies.md`
- Codex work-packet, test-escalation, evidence-reuse, and token policy:
  [`docs/development/codex-execution-efficiency.md`](codex-execution-efficiency.md)
- Conditional stop-triage, self-resolution budget, and hard-PRO criteria:
  [`docs/development/codex-blocker-escalation.md`](codex-blocker-escalation.md)
- Active Prompt Studio linked-input/NAIA projection correction:
  [`docs/architecture/prompt-studio-execution-derived-projection.md`](../architecture/prompt-studio-execution-derived-projection.md)
- Queue/live-UI identity and revision foundation:
  [`docs/architecture/queue-ui-two-phase-correlation-addendum.md`](../architecture/queue-ui-two-phase-correlation-addendum.md)
- Python backend architecture and compatibility-shim registry:
  [`docs/architecture/README.md`](../architecture/README.md)
- Active frontend maintenance execution ledger:
  `docs/development/frontend-maintenance-execution-plan.md`
- Current released baseline: `docs/development/0.6.0.md`
- Registry scanner safety: `docs/development/registry-scanner-safety.md`
- Older implementation history: `docs/version-plans/`
- Public workflow JSON templates and preview/source images: `docs/example_workflows/`
- User-facing workflow documentation: `docs/Anima AiO/`
- User-facing node documentation: `docs/nodes/`
- User-facing wildcard syntax: `docs/wildcards.ko.md` /
  `docs/wildcards.en.md`
- Current frontend maintenance roadmap:
  `docs/development/frontend-maintenance-roadmap.md`
- Dual-canvas browser smoke matrix:
  `docs/development/browser-smoke-matrix.md`
- Safe PAG stage-scope live matrix:
  `docs/development/aio-safe-pag-live-matrix.md`
- SageAttention stage-scope live matrix:
  `docs/development/aio-sage-live-matrix.md`
- Historical Issue #14 PR #18 execution plan:
  `docs/development/issue-14-frontend-js-maintenance.md`
- Deferred Node 2.0 DOM widget resize investigation:
  `docs/development/node2-dom-widget-resize-limitation.md`

## Area-Specific Files

- LoRA preset bugs:
  - `api.py`
  - `web/js/easyuse_anima_lora_preset.js`
  - `tests/test_lora_profiles.py`
  - `tests/test_frontend_lora_preset.py`
- Prompt Studio execution-derived projection / Issue #470:
  - `easyuse_anima/nodes/prompt_advanced_nodes.py`
  - `easyuse_anima/prompt/advanced.py`
  - `web/js/prompt_studio/extension_runtime.js`
  - `web/js/prompt_studio/advanced_values.js`
  - `web/js/prompt_studio/advanced_fields_ui.js`
  - `web/js/prompt_studio/serialization.js`
  - `web/js/prompt_studio/wildcard_seed_transaction.js`
  - `web/js/lifecycle/queue_ui_transaction.js`
  - `web/js/lifecycle/executed_event_context.js`
  - direct Prompt Studio projection, Wildcard, transaction, and backend payload tests
- Other Prompt Studio or wildcard work:
  - confirm the current canonical Python owner under `easyuse_anima/prompt/` and
    `easyuse_anima/nodes/` before using a root compatibility shim;
  - `web/js/easyuse_anima_autocomplete.js`
  - `web/js/easyuse_anima_prompt_studio.js`
  - `web/js/easyuse_anima_prompt_studio_common.js`
  - `web/js/easyuse_anima_settings.js`
  - `docs/development/frontend-maintenance-roadmap.md`
  - prompt-related tests
  - `tests/test_wildcards.py`
  - `docs/nodes/anima-prompt-studio-advanced.*.md`
  - `docs/nodes/anima-wildcard.*.md`
  - `docs/wildcards.ko.md` / `docs/wildcards.en.md`
  - workflow serialization paths
- Workflow template work:
  - `docs/example_workflows/`
  - `tests/test_workflows.py`
  - `docs/Anima AiO/Workflow_Management.md`
- Custom-node integration work:
  - `docs/development/custom-node-integrations.md`
  - `nodes.py`
  - `web/js/easyuse_anima_aio.js`
  - `tests/test_aio_nodes.py`
  - `tests/test_workflows.py`

Use this map only as an initial hint. Confirm the current canonical owner with a
targeted symbol search; do not automatically read every listed file.

## Current Policy Notes

- Issue #470 is the first READY production lane. Start QSTATE-04C1 Contract work
  before #440/#441, ordinary backend refactoring, or opportunistic feature work.
- Do not keep duplicated workflow JSON outside `docs/example_workflows/`.
- `docs/workflows/` has been removed; use `docs/example_workflows/` as the
  workflow JSON and preview/source image source.
- Example workflow JSON and matching PNG/JPG assets should share a basename.
- If another document conflicts with `docs/development/current-policies.md`,
  update or treat the conflicting document as stale before using it as a basis
  for implementation.
- `pyproject.toml` may be bumped early as a next-version marker, but it is not a
  release or publish step by itself.

## Validation Shortlist

### Edit loop

Use only changed-file syntax checks and the task-specific focused tests listed in
`codex-execution-efficiency.md`, the active Issue #470 projection roadmap, the
two-phase addendum, or the owning Issue.

```text
node --check web/js/<changed-file>.js
node tests/<focused-frontend-smoke>.mjs
python -m unittest <focused test modules>
git diff --check
```

The repository `quick` profile is still broad: it runs repository-wide Python
quality, all frontend syntax/smoke checks, TypeScript, and diff checks. Do not run
it after every edit.

A failed stop condition or live path should follow the bounded self-resolution
budget in `codex-blocker-escalation.md`. Do not request PRO review until a hard
technical-depth criterion is evidenced.

### Final PR candidate

- Official full, once per final code/test diff:
  `powershell -ExecutionPolicy Bypass -File tools\check_project.ps1 -Profile full`
- Rerun only when an invalidating code, test, runner, shared fixture, or
  configuration change occurs.
- Frontend behavior changes: follow
  `docs/development/browser-smoke-matrix.md` once per final diff.
- `comfy node validate` and `comfy node pack` only when package/import/registration,
  `.comfyignore`, dependency, release, or runtime closure can change.
- Registry scanner grep from `docs/development/registry-scanner-safety.md` only
  for scanner-sensitive or release work.
- Workflow JSON parse and package-version checks for
  `docs/example_workflows/*.json` only when workflow/release metadata changes.
