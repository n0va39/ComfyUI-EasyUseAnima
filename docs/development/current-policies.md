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
- Reference workflows under `docs/workflows/` are implementation references, not authoritative product documentation.

## Version Planning

- Track what will be reflected in each upcoming package version under `docs/development/<version>.md`.
- Treat these files as development plans, not release announcements.
- `pyproject.toml` may be bumped early to the next intended Registry version to avoid reusing a published version number.
- Do not publish to Comfy Registry, create release tags, or convert `RELEASE.md` entries into final release notes unless explicitly requested.

## Release Workflow Management

- Public workflow templates live under `example_workflows/`.
- Release workflow filenames must use `_release_ko` or `_release_en` before `.json`.
- Use the same release-suffixed basename for any matching copy under `docs/workflows/`.
- Unsuffixed workflow names are treated as local working/user-edited files and must not be used as GitHub release workflow filenames.
- Live ComfyUI syncs may overwrite release-suffixed files only. Do not overwrite user-edited workflow filenames.
