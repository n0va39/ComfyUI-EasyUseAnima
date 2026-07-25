# Current Development Policies

This document records decisions that supersede earlier experimental notes.

## Prompt and Tag Rules

- Ordinary Danbooru, meta, and artist tags use spaces in final prompt text.
- Pony score tags are the only underscore-preserving exception.
  - Keep `score_9`, `score_8`, `score_7`, `score_7:`, `score_6`, `score_5`, and `score_4`.
- Manual trigger text and explicit override text are preserved literally.
- Artist tags are artist-category data.
  - `@artist name` is the expected prompt form.
  - Do not implement a runtime fallback that treats general tags as artist tags.
  - If an artist is present as a general tag in a CSV, fix or replace the CSV data source instead.

## Autocomplete and Highlighting

- Autocomplete insertion, Prompt Studio preview, and prompt correction output must not disagree on tag spelling.
- Prompt Studio highlighting, autocomplete replacement, and prompt correction
  must share the same grammar decisions. Do not add syntax support to only one
  surface.
- The selected autocomplete CSV is search/highlight data, not a LoRA trigger source and not a NAIA output source.
- Built-in meta and quality tags can be used for typo/highlight classification without becoming autocomplete suggestions.
- Weighted prompt syntax is `(tag:weight)`. `[[artist_a, artist_b:weight]]`
  belongs to Artist Mix and the final weight is conditioning mix weight, not
  prompt-string weight.
- Unweighted parenthesized tags, for example `(@artist name)` or
  `(highres, long hair)`, should classify and highlight their inner tags rather
  than becoming one unknown token.
- Autocomplete should preserve surrounding syntax such as parentheses and
  weights when replacing the active token.

## Frontend UI Compatibility

- Treat ComfyUI Node 2.0 UI and the legacy canvas UI as supported surfaces for
  frontend changes that touch custom DOM widgets, canvas forwarding, node
  sizing, native previews, hidden widgets, or workflow serialization.
- Keep DOM widget layout contracts explicit. `getMinHeight`, `getHeight`,
  `computeLayoutSize`, CSS `height`/`max-height`/`overflow`, and any
  `node.setSize()` path must describe the same viewport model.
- Do not rely on browser natural content height, a Node 2.0-only wrapper, or a
  legacy-only canvas fallback to make layout appear correct.
- For scrollable editors, separate content height from viewport height. Long
  content should scroll inside the intended element rather than forcing
  uncontrolled node growth or disappearing behind `overflow: hidden`.
- Preview panes must not force node height through `height: 100%`, min-height,
  or native-preview suppression unless that behavior is intentional and
  verified in both Node 2.0 and legacy canvas surfaces.
- Hidden required widgets remain serialized. Visual hiding, socket visibility,
  and queue/workflow storage are separate compatibility concerns.
- Every PR that changes frontend layout, DOM widgets, canvas forwarding, native
  preview handling, or hidden widget serialization must state whether Node 2.0
  and legacy canvas smoke checks were run. If one surface is not checked, state
  the gap explicitly.

## Frontend Maintenance Workflow

- Keep each PR at one reviewable ownership boundary. Group two or three related
  pure helpers or one complete UI lifecycle instead of creating a PR for every
  mechanical extraction.
- Keep observable behavior changes separate from mechanical moves. Preserve the
  original order, return values, `this`, serialization keys, API payloads, and
  registration count in extraction-only slices.
- For a mechanical move, require independent behavior and test-contract audits.
  Add an architecture/lifecycle audit when behavior changes or the UI lifecycle
  is complex.
- After each maintenance PR is merged, append its completed boundary, merge PR,
  validation evidence, and deferred findings to the owning Issue ledger. At the
  close checkpoint, reconcile the cumulative ledger with every completion item.
- If a GitHub push, PR, or merge mutation reports abort or timeout, read the
  remote branch or PR state before retrying. Do not assume the mutation failed.
- Follow `docs/development/browser-smoke-matrix.md` for focused, full,
  dual-canvas, and final user-instance validation timing.

## Codex Execution Efficiency

- Follow [`codex-execution-efficiency.md`](codex-execution-efficiency.md) for
  every roadmap and implementation task.
- Start from one bounded task card. Read the active task section, owning Issue,
  direct owner files, direct tests, and targeted callers; do not reread the full
  repository or all historical plans by default.
- During implementation, run changed-file syntax checks and focused tests only.
- The `quick` project profile is a broad repository check, not a per-edit focused
  command.
- Run the official `full` project check once on the final candidate SHA. Rerun it
  only after an invalidating code, test, runner, shared fixture, configuration,
  or overlapping-rebase change.
- Run package validation only when import/registration/archive/metadata closure
  can change. Run live ComfyUI only for host-visible behavior. Run benchmarks
  only for performance or output-quality policy work.
- Reuse evidence for the same SHA and environment. Documentation, PR text,
  labels, and comments do not invalidate code or live evidence.
- Every test command must state the invariant it proves. Do not run broad suites
  merely because they share a high-level feature name.
- Stop at the first focused failure, identify the root cause, and do not rerun
  the complete suite until the focused failure passes.
- Use one implementation agent by default. Parallel workers require disjoint
  file ownership, a frozen shared contract, and bounded handoff output.
- PR and Issue completion records use the compact evidence template from the
  efficiency protocol instead of duplicating full logs or roadmap bodies.

## Detailer and SAM3

- Do not copy or reimplement Impact Pack `DetailerForEach` core logic in EasyUse Anima.
- Do not copy or reimplement Impact Pack `MaskToSEGS` core logic in EasyUse Anima.
- Use Impact Pack delegation for detailer loops and SEGS conversion.
- EasyUse Anima provides `Anima Detailer Align Hook` for crop sampling size alignment and AiO-internal SAM3 wiring only.
- Standalone `Anima SAM3 Context` and `Anima SAM3 Detailer` nodes are not public nodes after the Registry cleanup.
- Impact Pack is a ComfyUI custom-node runtime dependency for AiO SAM3/detailer features, not a Python package dependency.

## Documentation Cleanup

- Old exploratory plans can be deleted or rewritten when they conflict with current implementation decisions.
- Keep version plans focused on the current implementation path and explicit exclusions.
- Do not keep duplicated workflow JSON outside the managed example workflow directory.
- Public and documentation-linked example workflow assets live under `docs/example_workflows/`; readable workflow documentation lives under `docs/Anima AiO/`.
- If an old workflow JSON was used only for implementation reference, keep the relevant node ids or decisions in a plan document instead of retaining the full JSON copy.

## Version Planning

- Track what will be reflected in each upcoming package version under `docs/development/<version>.md`.
- Treat these files as development plans, not release announcements.
- `pyproject.toml` may be bumped early to the next intended Registry version to avoid reusing a published version number.
- Do not publish to Comfy Registry, create release tags, or convert `RELEASE.md` entries into final release notes unless explicitly requested.

## Registry Scanner Safety

- Runtime files must not use `eval`, `exec`, dynamic package installation, shell
  execution, obfuscation-like decoding, or user-controlled dynamic imports.
- Optional ComfyUI integrations should use explicit `try`/`except` imports for
  known module paths instead of `importlib.import_module`.
- External calls must be opt-in or localhost-only by default, timeout-bound, and
  parsed as data. Do not execute response content.
- Do not auto-read API keys from environment variables for optional external
  providers. External providers must be selected explicitly in settings.
- Keep `.comfyignore` focused on shipping runtime files only: exclude tests,
  development docs, examples, workflow samples, generated media, local caches,
  logs, and CI files. Keep root README files available.
- Before Registry publish, run the scanner checks in
  `docs/development/registry-scanner-safety.md` and `comfy node validate`.

## Local ComfyUI Instance Usage

- Implement changes in the assigned `codex/*` worktree. Use the
  workspace-managed Codex test instance only for API, queue, and browser
  validation.
- Treat the user-side instance as a separate manual surface. The current manual
  baseline is ComfyUI v0.27.0 unless the user explicitly changes it.
- Agent-run frontend smoke must record the legacy canvas and Node 2.0 as
  separate surfaces by following
  `docs/development/browser-smoke-matrix.md`.
- Sync or update the user instance only when explicitly requested or once at
  the end of the active maintenance goal.
- When both instances may be running, use separate ports and state clearly which
  instance was used for validation.
- Do not overwrite user-edited workflow files while syncing to an agent-only
  instance.

## Release Workflow Management

- Public workflow templates live under `docs/example_workflows/`.
- Example workflow JSON and its preview/source image should share the same basename when both are kept.
- Extracted workflow JSON from a saved PNG should be normalized with `extra.easyuse_anima_workflow` metadata before being used as a sample.
- Release workflow filenames must stay language release-suffixed, for example `_release_ko`, `_release_en`, `_release_ja`, or `_release_zh`, before `.json`.
- User-facing AiO workflow documentation lives under `docs/Anima AiO/`.
- AiO documentation files use version and language in the filename, for example `Anima_AiO_v5_1_EN.html`.
- Keep `docs/Anima AiO/` for readable workflow documentation only.
- AiO release workflows should use one `MarkdownNote` guide at the top of each section group.
- Do not use plain `Note` nodes for release workflow guide text.
- Before shipping release workflows, clear session-local preview state such as rgthree comparison image URLs and PreviewBridge temporary ids.
- Unsuffixed workflow names are treated as local working/user-edited files and must not be used as GitHub release workflow filenames.
- Live ComfyUI syncs may overwrite release-suffixed files only. Do not overwrite user-edited workflow filenames.
