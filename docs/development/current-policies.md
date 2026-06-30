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
- The selected autocomplete CSV is search/highlight data, not a LoRA trigger source and not a NAIA output source.
- Built-in meta and quality tags can be used for typo/highlight classification without becoming autocomplete suggestions.

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
