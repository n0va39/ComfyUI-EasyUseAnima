# EasyUse Anima Development Entry

Use this file as the first development-doc entry point when starting from a new
conversation.

## Read Order

1. `docs/development/current-policies.md`
2. Active version plan, currently `docs/development/0.5.0.md`
3. Latest released baseline, currently `docs/development/0.4.0.md`
4. Relevant topic guide:
   - Registry publish or flagged-version prevention:
     `docs/development/registry-scanner-safety.md`
   - workflow docs or release templates: `docs/Anima AiO/Workflow_Management.md`
   - user-facing AiO docs: `docs/Anima AiO/README.md`
   - custom-node model patch integrations: `docs/development/custom-node-integrations.md`
   - current frontend maintenance roadmap and Issue #14 close boundary:
     `docs/development/frontend-maintenance-roadmap.md`
   - active frontend maintenance Goal, lane ownership, and integration gates:
     `docs/development/frontend-maintenance-execution-plan.md`
   - repeatable legacy-canvas and Node 2.0 browser validation:
     `docs/development/browser-smoke-matrix.md`
   - historical Issue #14 PR #18 execution plan:
     `docs/development/issue-14-frontend-js-maintenance.md`
   - deferred Node 2.0 DOM widget resize investigation:
     `docs/development/node2-dom-widget-resize-limitation.md`
   - language or locale work: `docs/development/language-management.md`
5. `git status --short`
6. Relevant source and tests for the target area.

## Source Map

- Current policy baseline: `docs/development/current-policies.md`
- Active next-version plan: `docs/development/0.5.0.md`
- Latest released baseline: `docs/development/0.4.0.md`
- Registry scanner safety: `docs/development/registry-scanner-safety.md`
- Older implementation history: `docs/version-plans/`
- Public workflow JSON templates and preview/source images: `docs/example_workflows/`
- User-facing workflow documentation: `docs/Anima AiO/`
- User-facing node documentation: `docs/nodes/`
- User-facing wildcard syntax: `docs/wildcards.ko.md` /
  `docs/wildcards.en.md`
- Current frontend maintenance roadmap:
  `docs/development/frontend-maintenance-roadmap.md`
- Active frontend maintenance execution ledger:
  `docs/development/frontend-maintenance-execution-plan.md`
- Dual-canvas browser smoke matrix:
  `docs/development/browser-smoke-matrix.md`
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
- Prompt Studio or wildcard work:
  - `nodes.py`
  - `wildcard_engine.py`
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

## Current Policy Notes

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

- PR-ready official full, once per final diff:
  `powershell -ExecutionPolicy Bypass -File tools\check_project.ps1 -Profile full`
- Focused implementation checks as applicable:
  `node --check web/js/<changed-file>.js`,
  `node tests/<focused-frontend-smoke>.mjs`,
  `python -m unittest <focused test modules>`, and `git diff --check`
- Frontend behavior changes: follow
  `docs/development/browser-smoke-matrix.md` once per final diff
- Registry scanner grep from `docs/development/registry-scanner-safety.md`
- `comfy node validate` before Registry publish
- Workflow JSON parse and package-version checks for
  `docs/example_workflows/*.json`
