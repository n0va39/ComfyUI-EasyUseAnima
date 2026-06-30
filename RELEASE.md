# Release Notes

## 0.1.9

### Added

- Added `Anima Wildcard`, a standalone string-expansion node for EasyUse Anima
  wildcard and dynamic prompt syntax.
- Added wildcard controls to `Anima Prompt Studio Advanced` below `mod guidance`:
  mode, seed, and seed after generate.
- Added wildcard modes: `일반 채우기`, `고정`, `순차`, and `재현`.
- Added sequential wildcard expansion. Sequential mode selects
  `seed % candidate_count` for each candidate list and uses incrementing seed
  behavior.
- Added Impact Pack-oriented string wildcard syntax support:
  - file wildcards such as `__name__`, `__*/name__`, `__folder/*__`, and
    `N#__name__`
  - dynamic prompts such as `{a|b|c}`
  - weighted options such as `{2::a|5::b|c}` and `2::candidate`
  - multi-select prompts such as `{2$$a|b|c}` and `{1-3$$, $$a|b|c}`
  - `.txt`, `.yaml`, and `.yml` wildcard files
- Added default user wildcard folder creation with `easyuse_anima_test.txt`.
  The default folder is `ComfyUI/user/__easyuse_anima/wildcards`.
- Added `wildcard.extra_paths` so existing user-managed wildcard folders can be
  registered from EasyUse Anima settings with one path per list item.
- Added wildcard autocomplete for `__` input and a wildcard list API.
- Added separate Prompt Studio wildcard highlighting with a configurable
  wildcard syntax color.
- Added user documentation for wildcard syntax and split detailed node
  documentation into `docs/nodes/`.

### Changed

- `Anima Prompt Studio Advanced` saved-image workflows now store expanded
  wildcard text in reproduction mode, while the live workflow keeps source
  wildcard text and the next seed state.
- `Anima Prompt Studio Advanced` applies NAIA fill before wildcard expansion
  when both features are used.
- Top-level README files now act as entry points and link to per-node detail
  pages instead of carrying all node documentation inline.
- Package and workflow documentation now use `example_workflows/` as the public
  workflow JSON source and avoid the removed duplicate `docs/workflows/` layout.
- Wildcard extra path settings now use an add/remove list editor instead of a
  delimiter-based text field.

### Fixed

- Fixed `Anima Prompt Studio Advanced` NAIA resolution mode so repeated live
  queue runs can keep requesting fresh NAIA dimensions. Saved-result workflows
  still store the resolved size as `Custom` for reproduction.
- Fixed Prompt Studio highlight overlay alignment in browsers where highlighted
  text and the input caret could drift apart.
- Fixed fixed-mode wildcard expansion so inline multi-select syntax such as
  `{2$$red|blue|green}` expands instead of remaining literal.
- Fixed wildcard highlight priority so wildcard syntax is rendered with the
  dedicated wildcard color instead of being swallowed by normal prompt tag
  highlighting.
- Fixed wildcard extra path editing so typing in a path input does not lose
  focus after the first character.

### Deferred

- Wildcard controls for Prompt Builder, base Prompt Studio, and Prompt Studio
  Extend remain out of the 0.1.9 scope.
- `<lora:...>` is preserved as text. 0.1.9 does not add MODEL/CLIP LoRA
  application from wildcard expansion.
- Impact Pack detailer wildcard features such as `[LAB]`, `[ASC]`, `[DSC]`,
  `[RND]`, and `[SEP]` are not included.

### Validation

- `node --check web\js\easyuse_anima_prompt_studio.js`
- `node --check web\js\easyuse_anima_autocomplete.js`
- `node --check web\js\easyuse_anima_settings.js`
- JavaScript syntax checks for all EasyUse Anima frontend extensions
- `.venv\Scripts\python.exe -m json.tool locales\ko\nodeDefs.json`
- `.venv\Scripts\python.exe -m unittest discover -s tests`
- `.venv\Scripts\python.exe -m compileall -q .`
- `git diff --check`
- `powershell -ExecutionPolicy Bypass -File tools\check_custom_node.ps1 -Project ComfyUI-EasyUseAnima`
- Local markdown link check for README, wildcard docs, and `docs/nodes/`

## 0.1.6

### Added

- Added an autocomplete mode setting with `off`, `easyuse_nodes`, and
  `compatible_global` modes.
- Added shared frontend i18n helpers so custom DOM labels, buttons, tooltips,
  alerts, prompts, and settings follow the ComfyUI language setting.
- Added Korean custom-node locale definitions for node descriptions, input
  labels, input tooltips, output labels, and output tooltips.
- Added regression coverage for literal manual trigger text, LoRA trigger text,
  Advanced trigger fields, and Detailer Align Hook alignment values.

### Changed

- Prompt Studio Advanced now uses editor-level scrolling for long prompts
  instead of per-textarea vertical scrollbars.
- Prompt Studio highlight overlays copy more font metrics from the source input
  so highlights stay aligned when font settings differ.
- Autocomplete insertion, Prompt Studio previews, and Prompt Corrector output
  share the same prompt text rules.
- EasyUse Anima no longer exposes a separate language setting. UI language is
  selected from ComfyUI's own language setting.
- The 0.1.6 detailer scope is the Impact-compatible `Anima Detailer Align Hook`;
  SAM3 convenience-node cleanup and `MaskToSEGS` delegation cleanup were left
  out of this release scope.

### Validation

- `python -m unittest discover -s tests`
- `python -m compileall -q .`
- `git diff --check`
- `powershell -ExecutionPolicy Bypass -File tools\check_custom_node.ps1 -Project ComfyUI-EasyUseAnima`
- JavaScript syntax checks for EasyUse Anima frontend extensions
