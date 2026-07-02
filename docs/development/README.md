# EasyUse Anima Development Entry

Use this file as the first development-doc entry point when starting from a new
conversation.

## Read Order

1. `docs/development/current-policies.md`
2. Active version plan, currently `docs/development/0.2.1.md`
3. Latest released baseline, currently `docs/development/0.2.0.md`
4. Relevant topic guide:
   - workflow docs or release templates: `docs/Anima AiO/Workflow_Management.md`
   - user-facing AiO docs: `docs/Anima AiO/README.md`
   - language or locale work: `docs/development/language-management.md`
5. `git status --short`
6. Relevant source and tests for the target area.

## Source Map

- Current policy baseline: `docs/development/current-policies.md`
- Active next-version plan: `docs/development/0.2.1.md`
- Latest released baseline: `docs/development/0.2.0.md`
- Older implementation history: `docs/version-plans/`
- Public workflow JSON templates and preview/source images: `docs/example_workflows/`
- User-facing workflow documentation: `docs/Anima AiO/`
- User-facing node documentation: `docs/nodes/`
- User-facing wildcard syntax: `docs/wildcards.ko.md` /
  `docs/wildcards.en.md`

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
  - `web/js/easyuse_anima_settings.js`
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

- `python -m unittest discover -s tests`
- `python -m compileall -q .`
- `git diff --check`
- `node --check web/js/<changed-file>.js`
- Workflow JSON parse and package-version checks for
  `docs/example_workflows/*.json`
