# Release Notes

## 0.2.2

### Highlights

- Added the first release-ready `Anima AiO Generator` path: `Easy Use Anima
  Input` loads ANIMA diffusion model, VAE, and CLIP separately, then passes a
  dedicated context socket into the generator.
- The generator keeps the compact node UI focused on seed, steps, CFG, denoise,
  sampler/scheduler, Highres, Detailer, preview, and save controls. Sampler
  backend controls, model patch/optimization controls, save metadata, and
  detailer controls stay in popup settings.
- AiO generation settings are stored as keyed versioned JSON so changing
  parameter order does not shift saved workflow data.

### Added

- Added `Anima AiO Generator` with three sampler execution modes:
  `comfy_ksampler`, `spectrum_mod_guidance_advanced`, and
  `spectrum_spd_speed`.
- Added optional Anima DAVE model patch controls in Advanced Options.
- Added `Easy Use Anima Input`, which consumes prompt data and stores split
  ANIMA resource selections for diffusion model, VAE, and CLIP.
- Added optional `LORA_STACK` support on the AiO generator, including Image
  Saver-compatible Civitai LoRA resource/weight metadata.
- Added Image Saver integration with default saving enabled, workflow embedding,
  manual `additional_hashes`, and Civitai Hash Fetcher bundle rows.
- Added AiO preview UI with WebP temp previews, current/previous comparison,
  image feed history, selected image metadata, and feed-count settings.
- Added Highres and SAM3/Impact Detailer settings to the AiO generator.
- Added Chrome-style Detailer tabs with user-editable block names and left/right
  order controls.
- Added a maintained AiO generator sample workflow:
  `docs/example_workflows/EasyUse_Anima_AiO_generator_release_ko.json`.
- Added user-facing AiO node documentation in Korean and English.

### Changed

- Bumped package metadata to `0.2.2`.
- Updated AiO defaults: first-pass steps `32`, sampler `er_sde`, scheduler
  `simple`, AuraFlow shift `3.0` as the Anima model-recommended default,
  Highres scale `1.5`, and Highres denoise `0.25`.
- Moved KJNodes FP16 accumulation, SageAttention, Torch Compile, AuraFlow shift,
  and optional DAVE controls into `Advanced Options`. `Sampler Details` now
  keeps only sampler backend, Mod Guidance, Spectrum, and SPD/SPEED controls.
- Changed Highres and Detailer popup bodies to a single-column layout so long
  settings stay readable and scroll vertically instead of forming cramped grids.
- Updated AiO frontend tooltips so popup settings describe the actual runtime
  effect instead of only saying that a value is saved. The new tooltip keys are
  available in English, Korean, Japanese, and Chinese.
- Split AiO dependencies into required and optional feature packs. Missing
  optional packs are locked in the settings UI and sanitized out of queued
  `generation_settings` before execution.

### Fixed

- Fixed AiO sampler dispatch so the selected sampler mode is the only first-pass
  sampler path called.
- Fixed the `spectrum_mod_guidance_advanced` mode so it no longer creates an
  unused standalone Mod Guidance model clone for the first pass. Standalone Mod
  Guidance is still retained when later Highres or Detailer stages need it.
- Fixed AiO preview result handling so ComfyUI's default `images` UI payload is
  suppressed and only the dedicated `easyuse_anima_preview` payload is used.
- Hardened intermediate preview feed updates so live preview events are tagged
  by run and displayed in the node feed immediately.
- Fixed Image Saver metadata routing so `Steps`, `CFG`, `Sampler`,
  `Scheduler`, `Seed`, and `Denoise` come from the first-pass sampler while
  `Size` uses the final Highres/Detailer output resolution.

### Required And Optional Node Packs

- Required for this package: `ComfyUI-EasyUseAnima`.
- Required by the included AiO sample defaults: `ComfyUI-Spectrum-KSampler`
  and `ComfyUI-Image-Saver`.
- Optional: `ComfyUI-Anima-DAVE` for the DAVE model patch in Advanced Options.
- Optional: `ComfyUI-KJNodes` for SageAttention and Torch Compile options.
- Optional: `ComfyUI-Impact-Pack` for AiO SAM3 Detailer.

### Validation Notes

- Added regression coverage for all three AiO sampler modes so
  `comfy_ksampler`, `spectrum_mod_guidance_advanced`,
  and `spectrum_spd_speed` dispatch to their intended paths only.
- Added regression coverage for generator-level sampler/model-patch routing,
  including the integrated Spectrum Mod Guidance sampler and Highres stage
  model reuse.
- Ran `python -m unittest discover -s tests`, `python -m py_compile`, and
  `node --check web/js/easyuse_anima_aio.js` during release validation.

## 0.2.1

### Highlights

- Prepare `Anima Prompt Studio Advanced v2` with structured prompt data output.
- Downstream nodes should read Prompt Studio data by dict keys instead of
  positional output indexes so future output changes remain compatible.
- Add artist-field handling modes so text from Prompt Studio's artist-tag input
  fields can stay inline or be routed as separate structured data for
  artist-conditioning nodes, following the `ComfyUI-AnimaPromptEditor`
  artist-mix payload as the default compatibility target.
- Keep the existing `Anima Prompt Studio Advanced` node compatible while v2
  output contracts are introduced.

### Added

- Added `Anima Prompt Studio Advanced v2` with a single output socket of type
  `EASYUSE_ANIMA_PROMPT_DATA`.
- The v2 prompt data output is a Python dict with keyed compatibility outputs,
  node parameter state, resolution data, wildcard state, Mod Guidance flags,
  and artist-field data.
- Added `EASYUSE_ANIMA_PROMPT_DATA` helper node to pass prompt data through,
  optionally override compatibility fields, and unfold it into the existing
  Prompt Studio compatibility outputs.
- Added `Anima Prompt Data Conditioning` to consume `EASYUSE_ANIMA_PROMPT_DATA`,
  encode positive/negative CONDITIONING, create a batch-size-1 latent image
  from prompt-data width/height, and apply the `comfyui-spectrum-ksampler`
  `AnimaModGuidance` MODEL patch when enabled.
- `Anima Prompt Data Conditioning` now supports artist mix modes from
  prompt-data or node controls. `off`/`prompt` preserve the inline positive
  prompt, while `average` and `exact` separate Advanced artist-field text from
  the base prompt and rebuild artist variants through EasyUseAnima's Anima
  prompt ordering rules.
- Added approximate artist mix modes for cheaper exact-like mixing:
  `delta_rms`, `hybrid`, and `clustered`. These reduce positive conditioning
  branch count by compressing artist deltas while preserving the existing
  `average` and `exact` behavior.
- Artist mix controls now expose tuning values for style gain, RMS scale cap,
  hybrid top-K, clustered branch count, and clustered dominant-artist
  isolation.
- Artist mix mode tooltips now describe the method and expected conditioning
  branch cost.
- Added `Anima Artist Mix Conditioning` as a standalone artist mix node. It
  accepts a regular prompt plus separate `artist_tags`, supports
  `correct`/`front`/`back` artist positioning, and outputs positive
  `CONDITIONING` without requiring Prompt Data.
- Added user-facing artist mix documentation covering Advanced v2 Prompt Data
  routing, standalone artist tag positioning, artist mix modes, and branch cost
  tradeoffs.
- Added an Artist Mix example workflow and preview under
  `docs/example_workflows/`.
- Prompt data now stores `global_prompt` /
  `positive_without_artist_section`, structured `artist.tags`, and
  `artist_mix` routing values for artist-conditioning nodes.
- Prompt data now stores a `parameters` dict generated from every required
  `Anima Prompt Studio Advanced v2` input, so new v2 parameters are caught by
  tests instead of being silently omitted from `EASYUSE_ANIMA_PROMPT_DATA`.
- `Anima Prompt Studio Advanced v2` now exposes inline foldout controls for
  Mod Guidance and Artist Mix, with Artist Mix mode written into prompt data.
- Prompt-data socket names are fixed to English identifiers across locales so
  displayed socket names match the Python node contract.
- Added NAIA resolution bucket fit mode for `Anima Prompt Studio Advanced`.
  NAIA width/height can now resolve to the nearest aspect ratio inside a
  configured saved resolution bucket.
- Added `naia.resolution_mode` and `naia.resolution_bucket` settings plus
  localized frontend controls for original-scale and bucket-fit modes.

### Changed

- Bumped package metadata and maintained example workflow `package_version`
  metadata to `0.2.1`.

### Fixed

- Fixed Regional Prompt Studio dynamic field sockets so field input sockets stay
  synchronized with node fields and connection changes.
- Connected Regional Prompt Studio `STRING` inputs can now override masked
  prompt text at queue time without overwriting the saved field text.
- Foldout controls in Prompt Studio keep their open state across internal
  re-renders so clicks inside the control do not immediately collapse them.
- Advanced Prompt Studio native controls such as resolution bucket, wildcard,
  and Artist Mix dropdowns now consistently stop canvas event propagation so
  opened dropdowns stay open while selecting values.
- `Anima Prompt Data Conditioning` now calls Spectrum
  `AnimaModGuidance.patch()` with the installed node's supported signature, so
  current Spectrum builds no longer raise an argument-count `TypeError`.
- Older Spectrum `AnimaModGuidance` builds now emit a warning when their
  signature cannot receive separate negative quality tags. Execution continues,
  but negative Mod Guidance quality tags are ignored by that model patch.

### Validation Notes

- Added regression coverage for the Advanced v2 prompt data socket, dict
  payload, `EASYUSE_ANIMA_PROMPT_DATA` helper outputs and overrides, and
  artist-field-only artist data extraction.
- Added regression coverage that every required Advanced v2 input is present
  in prompt data `parameters`.
- Added regression coverage for prompt-data conditioning and Spectrum
  `AnimaModGuidance` patcher invocation.
- Added regression coverage for current Spectrum `AnimaModGuidance` invocation
  without a separate negative quality-tag argument and for future-compatible
  invocation when that argument is supported.
- Added regression coverage for the old Spectrum warning path.
- Added regression coverage for prompt-data latent image creation with fixed
  batch size 1.
- Added regression coverage for artist-field-only prompt data, artist-free
  base prompts, artist mix prompt rebuilding, and exact-mode conditioning
  metadata.
- Added regression coverage for duplicate artist coalescing, hybrid top-K tail
  compression, approximate artist mix mode routing, and prompt-data storage of
  artist mix tuning values.
- Added regression coverage for the standalone artist mix conditioning node,
  including default corrected placement and fixed front/back placement.
- Added regression coverage for Regional Prompt Studio field socket overrides.
- Added regression coverage for NAIA resolution mode/bucket validation and
  bucket-fit output sizing.

## 0.2.0

### Added

- Added `Anima Prompt Studio Regional`, a mask-scoped Prompt Studio variant
  for authoring numbered masks, per-field mask assignments, and regional
  prompt metadata.
- Added `Anima Regional Conditioning`, which consumes `CLIP` plus the dedicated
  `EASYUSE_ANIMA_REGIONAL_PROMPT_DATA` socket and produces positive/negative
  `CONDITIONING` outputs for KSampler workflows.
- Added a regional mask editor UI with numbered mask storage, mask preview,
  shape controls, and per-positive-field mask selectors.
- Added NAIA resolution scaling settings for `Anima Prompt Studio Advanced` so
  NAIA-sourced dimensions can be scaled and clamped by a maximum long edge.
- Added `Anima Image Scale By Multiple`, an image upscaling helper that aligns
  output dimensions to a selected multiple and can clamp the long edge.
- Added a regional prompt example workflow and source PNG under
  `docs/example_workflows/`.

### Changed

- Bumped the package version to `0.2.0`.
- Moved maintained example workflow assets from the root `example_workflows/`
  directory to `docs/example_workflows/`.
- Updated workflow metadata policy and workflow tests for the new
  `docs/example_workflows/` location.
- Regional Prompt Studio now outputs metadata prompt strings, width, height, and
  a dedicated regional data socket instead of exposing regional runtime payloads
  as plain string sockets.

### Fixed

- Fixed regional conditioning mask metadata for ComfyUI/Qwen/Wan-style latent
  dimensions by attaching full image-space masks and explicit latent mask
  bounds instead of relying on ComfyUI's `set_area_to_bounds` conversion path.
- Fixed Regional Prompt Studio UI layout issues around field controls, mask
  selector popups, and node sizing so prompt rows and selectors stay aligned.
- Added regression coverage for regional prompt data sockets, mask bounds,
  image scale option compatibility, and example workflow metadata.

### Deferred

- Regional Prompt Studio intentionally does not call NAIA in 0.2.0.
- Per-region Mod Guidance and a dedicated Regional Model Patch node remain
  deferred.
- Mask-scoped negative prompts remain out of the initial regional conditioning
  contract.

### Validation

- `node --check` for EasyUse Anima frontend JavaScript files
- `.venv\Scripts\python.exe -m json.tool` for locale JSON files
- `.venv\Scripts\python.exe -m unittest discover -s tests`
- `.venv\Scripts\python.exe -m compileall -q .`
- `git diff --check`
- JSON parse and hygiene scan for `docs/example_workflows/*.json`
- Live ComfyUI queue validation with a two-mask regional prompt sample

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
- Package and workflow documentation now use `docs/example_workflows/` as the public
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
