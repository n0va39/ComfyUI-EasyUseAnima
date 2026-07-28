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
3. For the active backend continuation owned by Issue #186, read
   [`docs/architecture/backend-roadmap-resume-0.6.2.md`](../architecture/backend-roadmap-resume-0.6.2.md)
   and only the current D-08 task section. It supersedes the stale immediate queue
   and broad preflight command in the older execution roadmap.
4. Python backend architecture or migration work:
   [`docs/architecture/README.md`](../architecture/README.md)
5. Only after a documented hard stop or unresolved cross-owner failure, read
   [`docs/development/codex-blocker-escalation.md`](codex-blocker-escalation.md)
   before requesting a technical PRO review. Ordinary test failures remain local
   task work.
6. Queue identity or stale-result lifecycle work may require
   [`docs/architecture/queue-ui-two-phase-correlation-addendum.md`](../architecture/queue-ui-two-phase-correlation-addendum.md).
   Prompt Studio linked-input/NAIA projection Issue #470 is completed; its roadmap
   is now a behavior-contract reference, not the active implementation queue.
7. Active frontend maintenance execution plan:
   `docs/development/frontend-maintenance-execution-plan.md`
8. Current released baseline: `RELEASE.md` / `pyproject.toml` version 0.6.2.
9. Relevant topic guide:
   - Registry scanner prevention for a future release:
     `docs/development/registry-scanner-safety.md`
   - workflow docs or release templates: `docs/Anima AiO/Workflow_Management.md`
   - user-facing AiO docs: `docs/Anima AiO/README.md`
   - custom-node model patch integrations: `docs/development/custom-node-integrations.md`
   - frontend maintenance roadmap and Issue #14 close boundary:
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
expanding it. Registry activation is external release administration; do not poll
or modify an immutable release while performing ordinary `dev` roadmap work.

## Source Map

- Current policy baseline: `docs/development/current-policies.md`
- Codex work-packet, test-escalation, evidence-reuse, and token policy:
  [`docs/development/codex-execution-efficiency.md`](codex-execution-efficiency.md)
- Active backend D-08 continuation and exact resume point:
  [`docs/architecture/backend-roadmap-resume-0.6.2.md`](../architecture/backend-roadmap-resume-0.6.2.md)
- Conditional stop-triage and technical-PRO criteria:
  [`docs/development/codex-blocker-escalation.md`](codex-blocker-escalation.md)
- Python backend architecture and compatibility-shim registry:
  [`docs/architecture/README.md`](../architecture/README.md)
- Completed Prompt Studio execution-derived projection contract:
  [`docs/architecture/prompt-studio-execution-derived-projection.md`](../architecture/prompt-studio-execution-derived-projection.md)
- Queue/live-UI identity and revision foundation:
  [`docs/architecture/queue-ui-two-phase-correlation-addendum.md`](../architecture/queue-ui-two-phase-correlation-addendum.md)
- Active frontend maintenance execution ledger:
  `docs/development/frontend-maintenance-execution-plan.md`
- Current release notes: `RELEASE.md`
- Registry scanner safety for future changes: `docs/development/registry-scanner-safety.md`
- Older implementation history: `docs/version-plans/`
- Public workflow JSON templates and preview/source images: `docs/example_workflows/`
- User-facing workflow documentation: `docs/Anima AiO/`
- User-facing node documentation: `docs/nodes/`
- User-facing wildcard syntax: `docs/wildcards.ko.md` /
  `docs/wildcards.en.md`
- Frontend maintenance roadmap: `docs/development/frontend-maintenance-roadmap.md`
- Dual-canvas browser smoke matrix: `docs/development/browser-smoke-matrix.md`

## Area-Specific Files

- Active D-08 API root consolidation / Issue #186:
  - `api.py`
  - `easyuse_anima/bootstrap.py`
  - `easyuse_anima/api/router.py`
  - the current `easyuse_anima/api/routes/*` owner
  - `tests/test_api_contract.py`
  - bootstrap/runtime owner tests
  - `tests/fixtures/python_backend_baseline.json`
  - compatibility-shim and package-skeleton tests when the task triggers them
- LoRA preset bugs:
  - `web/js/easyuse_anima_lora_preset.js`
  - `tests/test_frontend_lora_preset.py`
  - canonical profile/API owners confirmed by targeted symbol search
- Prompt Studio execution-derived projection reference:
  - `easyuse_anima/nodes/prompt_advanced_nodes.py`
  - `easyuse_anima/prompt/advanced.py`
  - `web/js/prompt_studio/extension_runtime.js`
  - `web/js/prompt_studio/advanced_values.js`
  - `web/js/prompt_studio/advanced_fields_ui.js`
  - `web/js/prompt_studio/serialization.js`
  - `web/js/lifecycle/queue_ui_transaction.js`
  - `web/js/lifecycle/executed_event_context.js`
- Other Prompt Studio or wildcard work:
  - confirm the current canonical Python owner under `easyuse_anima/prompt/` and
    `easyuse_anima/nodes/` before using a root compatibility shim;
  - relevant modular frontend owner and direct smoke tests;
  - workflow serialization paths when the behavior is persisted.
- Workflow template work:
  - `docs/example_workflows/`
  - `tests/test_workflows.py`
  - `docs/Anima AiO/Workflow_Management.md`
- Custom-node integration work:
  - `docs/development/custom-node-integrations.md`
  - canonical AiO owner under `easyuse_anima/aio/`
  - direct AiO/integration/workflow tests.

Use this map only as an initial hint. Confirm the current canonical owner with a
targeted symbol search; do not automatically read every listed file.

## Current Policy Notes

- The first READY roadmap task is D-08t under Issue #186. Do not resume from the
  old #470 or 0.6.1 patch queue.
- D-08t through D-08w move only handler factory invocation and correlation into
  private bootstrap composition helpers. They do not change route behavior,
  persistence, error policy, runtime lifecycle, or root compatibility aliases.
- D-08x is the integrated exit audit. D-14 or Phase E starts only after that gate
  records its prerequisites.
- Comfy Registry review of 0.6.2 does not block `dev` work and does not authorize
  republishing or mutating the released artifact.
- Do not keep duplicated workflow JSON outside `docs/example_workflows/`.
- If another document conflicts with `docs/development/current-policies.md` or the
  active resume checkpoint, update or treat it as historical before implementation.
- `pyproject.toml` may be bumped early as a next-version marker, but it is not a
  release or publish step by itself.

## Validation Shortlist

### Edit loop

Use only changed-file syntax checks and the task-specific focused tests listed in
the efficiency protocol, active resume checkpoint, or owning Issue.

```text
node --check web/js/<changed-file>.js
python -m unittest <one focused target>
git diff --check
```

The repository `quick` profile is broad and is not a task preflight or per-edit
command.

### Final PR candidate

- Official full, once per final code/test diff:
  `powershell -ExecutionPolicy Bypass -File tools\check_project.ps1 -Profile full`
- Rerun only when an invalidating code, test, runner, shared fixture,
  configuration, or overlapping-rebase change occurs.
- For D-08 composition-only slices, follow the evidence-reuse and escalation
  rules in `backend-roadmap-resume-0.6.2.md`; do not repeat package/live checks
  without a trigger.
- Frontend behavior changes: follow
  `docs/development/browser-smoke-matrix.md` once per final diff.
- `comfy node validate` and `comfy node pack` only when package/import/registration,
  `.comfyignore`, dependency, release, or runtime closure can materially change,
  or at an explicit integrated exit gate.
- Registry scanner grep only for scanner-sensitive source changes or future
  release preparation.
- Workflow JSON parse and package-version checks only when workflow/release
  metadata changes.
