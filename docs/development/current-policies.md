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
- Keep the four size concepts separate:
  - `node.size`: saved node box size.
  - DOM widget allocation: height ComfyUI assigns to the widget wrapper.
  - editor or panel viewport: visible area inside the custom DOM.
  - child content height: textarea, preview pane, or other resizable child
    state.
- Do not rely on browser natural content height, a Node 2.0-only wrapper, or a
  legacy-only canvas fallback to make layout appear correct.
- Choose the resize policy per node type before editing layout code.
  - Single-surface nodes such as `Anima AiO Generator` should map user node
    height to the internal panel viewport and rebalance settings/preview areas
    against that viewport.
  - Multi-field editors such as `Anima Prompt Studio Advanced` and
    `Anima Prompt Studio Advanced v2` should map user node height to the
    editor viewport only. Individual textarea heights remain owned by textarea
    autosize/manual resize, not by node resize, render, layout, serialize, or
    queue collection.
- For scrollable editors, separate content height from viewport height. Long
  content should scroll inside the intended element rather than forcing
  uncontrolled node growth or disappearing behind `overflow: hidden`.
- Do not reserve scrollbar space with `scrollbar-gutter: stable` in node
  editors unless persistent scrollbar alignment is intentionally required and
  verified. Empty scrollbar gutters are treated as layout regressions.
- Wheel routing must be conditional. Native controls keep wheel events only
  while the target control can scroll in the wheel direction. If the target
  control and editor cannot scroll, the event may forward to the ComfyUI canvas
  so normal canvas zoom/pan still works.
- Preview panes must not force node height through `height: 100%`, min-height,
  or native-preview suppression unless that behavior is intentional and
  verified in both Node 2.0 and legacy canvas surfaces.
- Hidden required widgets remain serialized. Visual hiding, socket visibility,
  and queue/workflow storage are separate compatibility concerns.
- Every PR that changes frontend layout, DOM widgets, canvas forwarding, native
  preview handling, or hidden widget serialization must state whether Node 2.0
  and legacy canvas smoke checks were run. If one surface is not checked, state
  the gap explicitly.

## Detailer and SAM3

- Do not copy or reimplement Impact Pack `DetailerForEach` core logic in EasyUse Anima.
- Do not copy or reimplement Impact Pack `MaskToSEGS` core logic in EasyUse Anima.
- Use Impact Pack delegation for detailer loops and SEGS conversion.
- EasyUse Anima provides `Anima Detailer Align Hook` for crop sampling size alignment and convenience SAM3 wiring only.
- Impact Pack is a ComfyUI custom-node runtime dependency for SAM3/detailer features, not a Python package dependency.

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

## Local ComfyUI Instance Usage

- Use the ComfyUI 0.24 instance for Codex agent implementation and queue
  validation only.
- Reserve the ComfyUI 0.25 instance for user-side manual testing.
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
