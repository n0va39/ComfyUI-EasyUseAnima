# Release Notes

## 1.1.2

### Fixed

- Long file-backed wildcard candidates containing many comma-separated tags
  and natural-language text now expand normally instead of falling back to the
  wildcard filename.
- Prompt Studio Advanced v2 now passes the expanded wildcard content to Prompt
  Corrector, preventing an unresolved token such as `__name__` from becoming a
  filename-like phrase.

### Safety and Compatibility

- The relative growth guard remains active for candidates that can recursively
  expand, while terminal file contents are bounded by the existing absolute
  output, depth, replacement-count, and cycle limits.
- Existing wildcard syntax, sequential/random selection, seeds, workflows, and
  public node contracts remain compatible.

### Update

- After updating, restart ComfyUI. Existing wildcard files do not need to be
  rewritten.

## 1.1.1

### Added

- Easy Use Anima Input and Anima AiO Generator can now load the 40-block
  Anima 2.9B model without the external ComfyUI-Anima-2.9B custom node.
- Anima AiO Generator can automatically adapt compatible LoRA stacks trained
  for the original 28-block ANIMA model when Anima 2.9B is selected.
- Anima 2.9B LoRA Stack Loader provides an explicit path for applying regular
  ANIMA LoRA stacks to the expanded model.

### Fixed

- AiO Upscale now identifies an externally enabled FlashAttention backend when
  it causes a USDU failure and explains which ComfyUI or KJNodes setting to
  disable.

### Compatibility

- Legacy LoRA adaptation does not copy learned weights into the 12 newly added
  blocks. It reconnects the LoRA weights only to the new positions of the 28
  blocks inherited from the original ANIMA model, leaving the added blocks at
  their native Anima 2.9B behavior.
- This is a structural compatibility conversion, not retraining. The visual
  effect can differ from the original model, and a LoRA trained specifically
  for Anima 2.9B remains the recommended option for best results.
- Existing workflows and the original 28-block ANIMA loading path remain
  compatible. Ambiguous partial legacy LoRAs require the dedicated Anima 2.9B
  LoRA Stack Loader instead of automatic AiO detection.

### Update

- After updating, restart ComfyUI and hard-refresh the browser.
- Select the Anima 2.9B diffusion model in Easy Use Anima Input. Existing
  compatible LoRA stacks connected to AiO are adapted automatically; use the
  dedicated loader when an older LoRA has a partial or ambiguous block layout.

## 1.1.0

### Added

- Prompt Studio Advanced V2 can now recognize A1111 and LoraManager-style
  LoRA tags after wildcard expansion, keep them in structured Prompt Data, and
  let Anima AiO Generator apply them automatically.
- Anima Prompt Studio Advanced LoRA and Anima Wildcard LoRA provide additive
  LoRA-enabled variants with LORA_STACK input and output sockets.
- LoRA fields now offer installed-LoRA autocomplete from `<:` and `<<:`, close
  completed tags automatically, and use a dedicated configurable highlight
  color.
- The public AiO Hook v1 API can replace the first-pass MODEL and override the
  allowed first-pass sampler settings: steps, CFG, sampler, scheduler, and
  denoise.

### Fixed

- LoRA tags returned by wildcard files are extracted from the same Prompt
  Studio Advanced V2 execution snapshot and reach AiO without a second
  wildcard expansion.
- LoRA parsing and highlighting remain separate from `<|>` and `<|...|>`
  prompt syntax.

### Compatibility

- Existing workflows, node identifiers, settings, profiles, and socket order
  remain compatible. The new LoRA nodes and AiO Hook controls are additive.
- Existing LORA_STACK entries remain first and prompt-derived LoRAs are
  appended in source order.
- AiO applies prompt-derived LoRAs only from structured Prompt Data; it does
  not reinterpret an unrelated raw positive prompt.

### Update

- After updating, restart ComfyUI and hard-refresh the browser.
- To apply a wildcard-produced LoRA in AiO, route the prompt through Prompt
  Studio Advanced V2 or one of the new LoRA-enabled nodes.

## 1.0.3

### Fixed

- Prompt Corrector and Prompt Builder now use the same selected autocomplete
  data as Prompt Studio for character, series/work, artist, and learned tags.
- Recognized character and work tags are no longer reported as unknown or
  ordered after artist tags.
- If the selected autocomplete data cannot be read, Prompt Corrector and Prompt
  Builder fall back to the existing built-in rules.

### Compatibility

- Existing workflows, node inputs and outputs, settings, artist overrides and
  exclusions, and the natural-language unknown-tag policy remain compatible.

### Update

- After updating, restart ComfyUI.

## 1.0.2

### Fixed

- Prompt Corrector now treats an explicit `@artist` tag as a known artist when
  artist validation is disabled, so it is no longer reported as unknown while
  also being moved into the artist section.
- Prompt Studio Classic, Advanced, Advanced V2, and Regional highlights no
  longer apply cached classification from earlier text after paste or rapid
  text replacement.

### Compatibility

- Existing workflows, prompt text, artist overrides and exclusions, settings,
  public node identifiers, and socket order remain compatible.
- General tags and natural-language prompt phrases keep the existing unknown
  tag policy.

### Update

- After updating, restart ComfyUI and hard-refresh the browser.

## 1.0.1

### Fixed

- AiO and LoRA profile files are now kept inside their designated profile
  folders, including on Windows paths and when symbolic links are present.
- Increment Each and Decrement Each seed state is now isolated per workflow so
  one workflow does not advance another workflow's sequence. Legacy or headless
  callers without a workflow id retain the previous shared behavior.
- Prompt Studio Advanced V2 now uses one wildcard snapshot throughout a queued
  execution so every projected field reflects the same expansion.
- A failed startup attempt can no longer leave stale cleanup state that shuts
  down services used by a successful retry.

### Changed

- Documentation and tooltips now clarify that NAIA Random Prompt uses the
  global EasyUse Anima Settings contract.
- Bundled release workflows now report the current package name, version, and
  release filename consistently.

### Compatibility

- Existing workflows, profiles, settings, public node identifiers, and socket
  order remain compatible.
- Legacy and headless seed callers without a workflow id keep their previous
  process-shared sequence behavior.

### Update

- After updating, restart ComfyUI. A browser hard refresh is not required for
  these fixes.

## 1.0.0

### Changed

- EasyUse Anima now keeps its Python implementation under the canonical
  `easyuse_anima` package, with the repository root reserved for the ComfyUI
  entrypoint.
- The legacy root modules `api`, `api_contract`, `autocomplete_dataset`,
  `autocomplete_index`, `nodes`, `prompt_translation`, `settings`, `storage`,
  and `wildcard_engine`, together with the legacy `anima_prompt` package, have
  been removed. Third-party Python integrations must import the matching
  canonical owners under `easyuse_anima`.

### Fixed

- Prompt Studio highlight overlays now wrap at the same width as the editable
  text when no scrollbar is present, preventing highlighted and transparent
  text from splitting onto different lines.
### Compatibility

- Existing ComfyUI workflows, public node identifiers, input and output socket
  order, HTTP routes and payloads, settings, profiles, and saved data remain
  compatible.
- Python import compatibility is intentionally broken only for the removed
  legacy root modules and `anima_prompt` package. Ordinary ComfyUI workflows do
  not require migration.
- The stable 1.0 public contract is the ComfyUI entrypoint, mapped nodes,
  workflows, HTTP payloads, settings, profiles, and saved data. The
  `easyuse_anima` package root does not re-export private implementation names;
  advanced Python integrations import the exact canonical owner they use.

### Update

- After updating, restart ComfyUI and hard-refresh the browser.
- Before installing 1.0.0, update third-party Python code that imports a
  removed legacy module to use its canonical `easyuse_anima` owner.

## 0.6.2

### Fixed

- LoRA Preset now opens and draws its profile bar and menus when supported
  ComfyUI frontends provide LiteGraph through their host runtime binding.

### Compatibility

- Existing LoRA presets, saved profiles, workflows, public node identifiers,
  socket ordering, and the other 0.6.1 features remain unchanged.

### Update

- After updating, restart ComfyUI and hard-refresh the browser.

## 0.6.1

### Added

- Safe PAG and SageAttention settings can target the first pass, Highres,
  Detailer, and Upscale stages independently. Existing workflows keep their
  previous all-stage behavior unless a stage scope is selected.

### Fixed

- Prompt Studio now projects connected STRING inputs into the exact linked
  fields for the accepted queue without saving execution-only values as local
  fallback text.
- Successful NAIA queue results now update the matching positive and negative
  NAIA fields and the accepted resolution together, and those canonical values
  persist through workflow save and reload.
- Newer accepted queues keep ownership of editable Prompt Studio fields.
  Out-of-order, duplicate, missing, or mismatched execution identities fail
  closed instead of restoring an older result.
- Wildcard, linked-input, and NAIA projections now share one queue transaction,
  so one accepted execution is settled once across all affected fields.

### Compatibility

- Existing workflows, public node identifiers, socket ordering, settings, and
  profile schemas remain compatible.
- Linked execution overlays remain non-serialized. Successful NAIA results are
  intentionally stored as the current canonical NAIA field and resolution
  values.

### Update

- After updating, restart ComfyUI and hard-refresh the browser.

## 0.6.0

### Added

- DAVE model patch settings can target the first pass, Highres, Detailer, and
  Upscale stages independently. Existing workflows keep their previous
  all-stage behavior unless a stage scope is selected.
- AiO Advanced settings can inspect the current KJNodes and Torch environment,
  explain relevant compatibility constraints, and apply a compatible Torch
  Compile recommendation without changing unrelated settings.
- NegPip now provides Off, On, and Turbo modes through the public ComfyUI-ppm
  integration. Off preserves the existing conditioning path, and On applies
  standard NegPip processing.
- NegPip Turbo turns the negative prompt into an inverted contribution and uses
  effective CFG 1 for the first pass, Highres, Detailer, and USDU while keeping
  the saved prompts and CFG values unchanged.

### Fixed

- Torch Compile recommendations avoid incompatible choices for known
  variable-size stages instead of applying one unsafe configuration broadly.
- Missing or incompatible optional dependencies now fail before partial model
  patch state can leak into generation.

### Compatibility

- Existing workflows default to NegPip Off and retain their saved model-patch
  behavior. Unknown stage-scope values remain fail-closed instead of being
  reinterpreted.
- Public node identifiers, socket ordering, workflow schemas, and saved prompt
  and CFG values remain compatible.

### Update

- After updating, restart ComfyUI and hard-refresh the browser.
- Install or update ComfyUI-ppm to use NegPip On or Turbo. A compatible KJNodes
  version is required for Torch Compile recommendations.

## 0.5.6

### Fixed

- Older queue results no longer overwrite newer LoRA Preset or Prompt Studio
  edits. Out-of-order and duplicate completions preserve the current editable
  state.
- Prompt Studio Wildcard advances its displayed next seed only when the result
  still matches the queued edit revision. The narrow seed summary and an open,
  unedited seed input stay synchronized without rebuilding the editor.
- AiO Random Each, Increment Each, and Decrement Each keep their `-1`, `-2`,
  and `-3` selections after execution while recording the concrete execution
  seed separately as the last seed.
- AiO concrete seeds publish their next value only when no newer edit exists.
  Use Last and New Fixed Random switch the seed and its control to one concrete,
  fixed value.
- Returning to a concrete AiO seed after a special seed stream now starts from
  the explicitly entered value instead of continuing the previous stream.

### Compatibility

- Existing workflows keep special seed selections and stored seed controls.
- Public node sockets, workflow schemas, profiles, settings, and backend API
  contracts remain compatible.
- Release validation covers ComfyUI 0.27.0 with frontend 1.45.20 on Legacy
  Canvas and Node 2.0.

### Update

- After updating, restart ComfyUI and hard-refresh the browser.

## 0.5.5

### Added

- Prompt Studio Advanced and AdvancedV2 can swap width and height in one
  action for inverse presets and custom resolutions. NAIA-backed dimensions
  remain protected when a deterministic swap is not available.
- Artist-only autocomplete supports a configurable prefix while keeping `@` as
  the default. Prompt completion can preserve or safely replace text to the
  right of the caret according to the selected commit mode.
- Prompt Studio can wrap selected text with `()`, `{}`, or `[[ ]]`. An optional
  setting adds `(selection:1)` and selects the numeric weight for immediate
  editing.

### Fixed

- LoRA Preset no longer treats profile metadata embedded by another user's
  workflow as proof that the profile is saved locally. Saved state now requires
  the current local profile identity and content to match.
- The LoRA Preset profile scrollbar now supports track clicks and thumb drags
  through the actual Legacy Canvas and Node 2.0 host geometry.
- Long pasted text grows Prompt Studio Classic, Extend, Advanced, and
  AdvancedV2 text areas after layout without shrinking a newer revision.
- A Korean autocomplete source is selected only for a fresh Korean locale with
  no explicit source setting. Existing user choices remain unchanged.
- Mid-text autocomplete preserves protected suffixes, prompt weights, closing
  syntax, and separate tags instead of replacing an oversized segment.

### Compatibility

- Existing workflows, settings, profiles, public node identifiers, and
  backend API contracts remain compatible.
- New settings use compatibility-preserving defaults and do not rewrite
  existing prompt text or stored workflow data.
- Release validation covers ComfyUI 0.27.0 Legacy Canvas and Node 2.0.

### Update

- After updating, restart ComfyUI and hard-refresh the browser.

## 0.5.4

### Fixed

- The standalone Anima Wildcard node again provides Normal, Fixed,
  Sequential, and Reproduce modes. Saved workflows preserve the selected mode
  and its deterministic seed behavior.
- Prompt Studio resolution buckets now include exact 2:3 and 3:2 choices for
  the 512, 768, 896, 1024, and 1536 tiers.
- AiO optional-dependency notices stay silent during ordinary loading and
  queueing, and appear only when an unavailable feature is selected.
- AiO profiles can be saved in ComfyUI Desktop without the
  `prompt() is not supported` error. Profile and missing-dependency dialogs
  remain visible above the AiO settings window.

### Compatibility

- Existing workflows, settings, profiles, and public node identifiers remain
  compatible.
- The final AiO dialog behavior was checked in the ComfyUI 0.27.0 Node 2.0
  interface.

### Update

- After updating, restart ComfyUI and hard-refresh the browser.

## 0.5.3

### Fixed

- Anima Wildcard now expands file wildcards such as `__samples/flower__`
  with the Impact Pack-compatible wildcard rules instead of returning the
  wildcard key, and exposes the filled text used for generation.
- Wildcard and Prompt Studio selections now reproduce the same result for the
  same seed. Fixed, randomize, increment, sequential, and previous-seed reuse
  controls preserve the intended seed and result.
- Saved workflows keep their wildcard seed fixed when loaded, so running the
  workflow again reproduces the saved expanded prompt.
- The Wildcard Seed dialog now separates concise seed controls from the full
  rule reference and keeps the help text readable.
- Profile, settings, autocomplete, translation, and API error paths are more
  reliable without changing existing node or workflow contracts.

### Compatibility

- Existing workflows, settings, profiles, and public node identifiers remain
  compatible.
- Wildcard and seed behavior was checked on both Legacy canvas and Node 2.0.

### Update

- After updating, restart ComfyUI and hard-refresh the browser.

## 0.5.2

### Fixed

- Autocomplete can show up to 100 suggestions, preserves nested prompt syntax
  when a suggestion is selected, and reconnects after workflow reloads.
- AiO Generator keeps simultaneous queue seeds distinct, keeps preview scrolling
  inside the preview, exposes the Detailer threshold, and preserves valid
  resource and Detailer choices as options load.
- LoRA Preset saves and restores profiles consistently and keeps Node 2.0 list
  scrolling from zooming the canvas.

### Compatibility

- Existing workflows and settings remain compatible.
- Compatibility was confirmed on ComfyUI 0.27.0 with LoRA Manager enabled.

### Update

- After updating, restart ComfyUI and hard-refresh the browser.

## 0.5.1

### Fixed

- Fixed Autocomplete suggestions that did not open in the withdrawn 0.5.0
  package.

### Update

- If you installed 0.5.0, update to 0.5.1 or later, restart ComfyUI, and
  hard-refresh the browser.
- Existing workflows and settings remain compatible.

## 0.5.0

### Changed

- Split the AiO Generator, LoRA Preset, Autocomplete, Settings, Prompt Studio,
  and Regional Prompt Studio frontends into smaller lifecycle and pure-data
  modules while preserving existing node, workflow, and API contracts.
- Unified the public Wildcard and Prompt Studio seed range at
  `0..9007199254740991`, including increment/decrement wrapping and full-range
  randomization, while preserving loaded legacy Python `uint64` workflow seeds.
- Expanded the checked-in frontend semantic-smoke runner, TypeScript checking,
  dual-canvas browser matrix, and maintenance handoff ledger.
- Updated maintained release workflow metadata to package version `0.5.0`.

### Fixed

- Fixed rapid consecutive queue seed ownership for native Wildcard and Regional
  Prompt Studio queues, and for Advanced queues including nodes inside attached
  subgraphs, with queue rejection, graph clear, and workflow re-entry boundaries.
- Fixed AiO Generator queue transactions and extension re-entry so missing or
  empty prompt IDs do not commit state, duplicate hooks do not queue twice, and
  sampler hydration refreshes top-level and attached-subgraph panels once.
- Fixed AiO preview, settings-dialog, panel-render, profile, resize, and scroll
  lifecycle ownership without changing saved generation-settings contracts.
- Fixed Autocomplete input, IME composition, keyboard, popup geometry, and
  request/source epoch handling so stale or failed responses cannot replace or
  close the current suggestion list after a source change.
- Fixed LoRA Preset menu, preview, and canvas-widget lifecycle ownership,
  including escaped folder labels, idempotent installation/disposal, and
  preview cleanup when the current node changes.

### Validation Notes

- Reused the frozen production-tree evidence from the final 0.5.0 maintenance
  checkpoint: Python unittest 398/398, 104 frontend JavaScript files,
  TypeScript 6.0.3, and diff checks.
- Verified the final Autocomplete source-switch, keyboard, commit, and
  save/reload matrix on both legacy canvas and Node 2.0 in the Codex test
  instance, with no EasyUse Anima browser errors.
- Release preparation changes only version, changelog, Registry, workflow
  metadata, and maintenance documentation; no production Python or JavaScript
  is changed in the release-prep slice.

## 0.4.0

### Added

- Added built-in AiO generation profiles in the `SAMPLER` header:
  `Normal`, `Turbo`, and `Optimized`.
- Added named user profiles that save the complete AiO generation settings and
  can be loaded, overwritten, renamed, or deleted across ComfyUI restarts.
- Added exact profile-state detection. Settings that do not match a built-in
  profile are shown as `Custom`, and edited user profiles return to `Custom`.
- Added regression coverage for AiO profile storage, built-in settings,
  profile-state fingerprints, wheel ownership, and frontend placement.

### Changed

- AiO optional dependency discovery now distinguishes available, missing, and
  query-failed states and reports the result instead of silently disabling
  settings after a lookup failure.
- Prompt Studio Advanced and AiO Generator now let ComfyUI own the current node
  and DOM-widget viewport height while EasyUse Anima declares only the required
  minimum layout.
- Scrollbars now exclusively own wheel input, including at their boundaries.
  Canvas zoom receives wheel input only when the relevant editor or AiO panel
  has no intended scrollbar.
- Updated maintained release workflow metadata to package version `0.4.0`.

### Fixed

- Fixed Prompt Studio Advanced height recalculation after node-width changes
  alter textarea wrapping.
- Fixed repeated or conflicting height updates between ComfyUI, Prompt Studio
  Advanced, and AiO Generator in Node 2.0 and legacy canvas.
- Fixed AiO panel resize behavior so settings can scroll without the preview
  forcing the node back to a larger height.
- Kept AiO final images in ComfyUI queue/history output while suppressing the
  duplicate legacy canvas image label.

### Validation Notes

- Verified Python unit tests, compile checks, all frontend JavaScript syntax,
  locale JSON, workflow JSON/link/package metadata, Registry scanner patterns,
  and `comfy node validate`.
- Verified the profile, resize, text-wrap, and wheel ownership changes on
  ComfyUI 0.27.0 Node 2.0 and legacy canvas during the feature PRs.
- Verified the user-facing ComfyUI 0.27.0 instance after the final profile
  integration.

## 0.3.2

### Fixed

- Fixed Registry and Manager dependency metadata for Google prompt translation
  by declaring `googletrans-py==4.0.0` in both `pyproject.toml` and
  `requirements.txt`.

### Validation Notes

- Verified `pyproject.toml` parsing and dependency metadata alignment.
- Verified the release diff with `git diff --check`.

## 0.3.1

### Added

- Added the AiO Generator final Upscale stage after Detailer and before Save,
  with mutually exclusive USDU and ResShift backends.
- Added USDU helpers for practical final upscaling: automatic tile sizing with
  target/min/max controls, no-general prompt rebuilding that keeps quality,
  artist, and trigger fields, required sampler controls in the main settings,
  per-USDU Spectrum/DCW settings, and info logs for resolved tile and sampler
  decisions.
- Added a Postprocess stage for final size fitting after Detailer/Upscale and
  before Save, with long-edge and megapixel caps.
- Added AiO Generator controls for the Anima Safe PAG model patch.
- Added an Image Saver prompt metadata toggle so positive/negative prompt text
  can be omitted from saved metadata when needed.
- Added bundled autocomplete CSV sources from
  `DraconicDragon/dbr-e621-lists-archive`: Danbooru 2025-09-01, e621
  2025-09-01, and a Danbooru+e621 merged CSV. The source license is
  Unlicense.

### Changed

- Moved legacy Upscale final-fit settings into the dedicated Postprocess stage
  during settings normalization.
- Registry publishing now uses checked-in plain text changelog files for the
  release changelog path.
- Changed the default autocomplete CSV to `danbooru_2025-09-01.csv`, with the
  previous `danbooru_tags_classified.csv` documented as the Korean-search
  source.
- Documented that the Danbooru+e621 merged CSV has upstream merge/category
  collision risk and should be used only when a single mixed source is needed.

### Fixed

- Fixed wildcard syntax reference table rendering by escaping literal pipe
  characters in the English and Korean wildcard docs.
- Normalized e621 and merged e621 category offsets into EasyUse Anima's
  existing Prompt Studio highlight sections.

### Validation Notes

- Added AiO Generator regression coverage for final Upscale, USDU tile
  normalization and logging, ResShift dispatch, Postprocess final-fit ordering,
  Safe PAG patch routing, and Image Saver prompt metadata toggling.
- Added frontend source guards for the new Upscale/Postprocess dialogs, USDU
  sampler controls, Safe PAG labels, and Image Saver metadata toggle.
- Added autocomplete source-list and e621 category-normalization regression
  coverage.
- Validated during 0.3.1 release preparation with Python unit tests, compile
  checks, JavaScript syntax checks, JSON/TOML metadata checks, Registry
  changelog extraction, and `git diff --check`.

## 0.3.0

### Changed

- Prepared the package for Comfy Registry publication by tightening the shipped
  archive surface with `.comfyignore`, documenting Registry scanner safety
  rules, and keeping Registry metadata aligned in `pyproject.toml`.
- Removed the standalone public `Anima SAM3 Context` and `Anima SAM3 Detailer`
  node registrations and their user-facing node docs. AiO Generator's internal
  SAM3 detailer path remains available through AiO Detailer settings.
- Kept optional external-provider paths safer by default: prompt translation is
  off unless selected, NAIA remote hosts require an explicit allow setting, and
  API-key environment auto-detection was removed.
- Set AiO release workflow optimization defaults to conservative values:
  FP16 accumulation off, SageAttention disabled, Sage compile disabled, and
  TorchCompile off. The v6 workflow guide markdown now explains when to enable
  those options manually.

### Fixed

- Fixed AiO Generator Image Saver metadata so saved positive/negative prompts
  use Prompt Studio metadata prompt outputs when available, while generation and
  Mod Guidance still use the generation prompt outputs.

### Validation Notes

- Added Registry scanner safety regression coverage and documentation.
- Added AiO Generator metadata prompt regression coverage.
- Validated release workflow JSON syntax, workflow safe defaults, Python tests,
  compile checks, Registry scanner grep checks, JavaScript syntax checks, and
  `git diff --check` during 0.3.0 release preparation.

## 0.2.7

### Fixed

- Fixed global autocomplete attachment in ComfyUI Nodes 2.0 so prompt text
  fields that are created or re-rendered after extension startup still receive
  EasyUse Anima autocomplete behavior.
- Fixed autocomplete search for escaped prompt parentheses so inputs such as
  `\(blue archive\)` search the inner literal tag text, matching tags like
  `asuna \(blue archive\)`.
- Fixed autocomplete popup scroll reset timing after popup hide/show cycles so
  new suggestion lists reopen at the top instead of preserving a previous
  scrolled position.

### Changed

- Autocomplete popup reset now runs after the popup becomes visible and once
  more on the next animation frame, avoiding browser scroll restoration while
  the menu is `display: none`.
- Disabled scroll anchoring for the autocomplete popup to keep result-list
  replacement from preserving stale scroll offsets.

### Validation Notes

- Added frontend source guards for Nodes 2.0 autocomplete attachment, prompt
  syntax stripping, popup hide/show scroll reset order, and outside-click state
  cleanup.
- Added regression coverage for escaped literal parenthesis search.
- Validated the autocomplete JavaScript with syntax checks and verified the
  focused autocomplete regression tests during 0.2.7 preparation.

## 0.2.6

### Added

- Added hover tooltips for trained Prompt Studio highlight tags, using
  autocomplete metadata when it is available.
- Added the `prompt_studio.trained_tag_tooltip` setting and matching Comfy
  setting key so tag hover tooltips can be enabled or disabled from Prompt
  Studio settings.
- Added a dedicated tabbed Prompt Studio highlight color editor so the growing
  highlight color controls are managed outside the main Prompt Studio settings
  list.
- Added Community Standards documentation for GitHub, including Code of
  Conduct, English/Korean contributing guides, Security Policy, issue forms,
  and a pull request template.

### Changed

- Reused autocomplete tooltip formatting for Prompt Studio tag highlights so
  hover text stays consistent between autocomplete suggestions and highlighted
  prompt tokens.
- Registered the tag tooltip and highlight color settings in backend defaults,
  frontend settings UI, and settings key mapping.
- Shared Prompt Studio highlight color handling across the main Prompt Studio
  editor and the common highlighter path.
- Documented that issues, discussions, and pull requests may be written in
  English or Korean.

### Validation Notes

- Added regression coverage for Prompt Studio tag tooltip settings.
- Validated the changed Prompt Studio, common highlighter, autocomplete, and
  settings JavaScript with syntax checks during 0.2.6 preparation.
- Validated the GitHub issue template YAML files with PyYAML and checked the
  Community Standards documentation for trailing whitespace.

## 0.2.5

### Added

- Added prompt translation marker support for Prompt Studio and autocomplete
  flows, backed by the new prompt translation runtime helper and settings.
- Added English ANIMA Easy Use workflow documentation alongside the existing
  Korean guide.

### Changed

- Prompt Studio text areas now use the system UI font and root font size by
  default instead of forcing the Advanced editor to a fixed 12px monospace
  font.
- Prompt Studio highlight overlays re-copy input text metrics after settings
  changes so input text and overlay rendering stay aligned.
- Added manual Prompt Studio font correction settings for display mismatch
  cases:
  - `prompt_studio.font_override`
  - `prompt_studio.font_family`
  - `prompt_studio.font_size`
- AiO Generator preview handling was refined so Comfy native denoising previews
  are rendered in the EasyUse Anima preview panel while duplicate native overlay
  previews are suppressed.

### Fixed

- Fixed AiO native preview overlay cleanup so stale overlay state is cleared
  when preview ownership changes.
- Updated workflow validation coverage for the native preview suppression path.

### Validation Notes

- Added regression coverage for prompt translation marker handling in prompt
  correction and autocomplete-related flows.
- Added regression coverage for Prompt Studio font setting defaults and AiO
  native preview suppression behavior.

## 0.2.4

### Fixed

- Fixed `Anima AiO Generator` Image Saver integration so Civitai Hash Fetcher
  API failures, empty results, or temporary upstream errors skip only the
  optional metadata hash instead of failing the completed image save.

### Changed

- Included the post-0.2.3 documentation refresh for EasyUseAnima guides,
  README demo videos, and the ANIMA Easy Use workflow guide.

### Validation Notes

- Added regression coverage for Civitai Hash Fetcher `Error:` responses and
  raised exceptions during AiO Image Saver metadata assembly.
- Reviewed the Image Saver/Civitai integration path against the upstream
  Image Saver behavior and kept missing local configuration errors fatal while
  treating external Civitai lookup failures as best-effort metadata.

## 0.2.3

### Fixed

- Fixed `Anima AiO Generator` Detailer Settings so Face/Eye detailer blocks
  render again after opening the popup.
- Fixed Detailer Settings so custom detailer blocks can be added, saved,
  reordered, and executed after the built-in Face/Eye blocks.
- Fixed Highres and Detailer stage optimization so Spectrum/DCW settings are
  saved and applied per stage/block even when CFG, sampler, and scheduler follow
  the main sampler.
- Restored broader autocomplete suggestions when inline autocomplete preview is
  disabled, while keeping strict token-range behavior for preview mode.
- Fixed inline autocomplete preview filtering so Korean description/keyword
  searches such as `하츠네 미쿠` keep the matched tag suggestion.
- Fixed IME composition refresh so Korean input can update autocomplete
  suggestions while composing instead of waiting for a space or refocus.
- Fixed keyboard navigation in the autocomplete menu so the active suggestion
  scrolls into view with at least one adjacent item visible when possible.
- Fixed wildcard autocomplete for empty `__` prompts, Korean wildcard keys, and
  normalized space/underscore/path searches.
- Fixed wildcard and dynamic-prompt highlight classification, including Korean
  wildcard syntax and comma-containing dynamic prompts such as
  `{1-3$$, $$red|blue}`.

### Changed

- Updated bundled Korean AiO workflow JSON files with refreshed embedded
  workflow defaults and `0.2.3` package metadata.

### Validation Notes

- Added regression coverage for IME autocomplete refresh, arrow-key menu
  scrolling, wildcard autocomplete token detection, Korean wildcard keys, and
  wildcard/dynamic-prompt highlight classification.
- Added regression coverage for custom Detailer blocks and stage-specific
  Highres/Detailer Spectrum/DCW settings.

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
- Added `Anima Prompt Corrector Simple`, a compact one-input and one-output
  prompt correction node for regular multiline string workflows.
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
- Added popup-based Prompt Studio Advanced controls for Artist Mix,
  Mod Guidance, wildcard seed, and resolution bucket settings so the node body
  stays compact.
- Added Artist Mix group syntax such as `[[artist_a, artist_b:0.7]]` for
  keeping multiple artists in one conditioning branch. The final `:0.7` is an
  Artist Mix conditioning weight, not a prompt-string weight.
- Added inline autocomplete ghost preview and optional editor-style closing
  bracket insertion settings.
- Added optional underline rendering for weighted prompt syntax such as
  `(tag:1.2)` and Artist Mix groups.
- Added a maintained AiO generator sample workflow:
  `docs/example_workflows/EasyUse_Anima_AiO_generator_release_ko.json`.
- Added the compact release workflow:
  `docs/example_workflows/ANIMA_Easy_Use_workflow_v1_release_ko.json`.
- Added `required_node_packs` metadata to release workflow templates so
  required custom nodes are visible from the workflow JSON itself.
- Added user-facing AiO node documentation in Korean and English.
- Added an ANIMA Easy Use workflow v1 usage draft and Simple prompt corrector
  node screenshot.

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
- Changed Prompt Studio Advanced wildcard seed and resolution controls to show a
  single popup button plus a compact current-setting summary in the node body.
- Changed Prompt Studio autocomplete, correction, and highlight handling to
  share the same prompt text rules for spaces, escaped parentheses,
  Pony score tags, artist tags, and weighted syntax.
- Replaced the old `KR_danbooru_tags_with_description v3_modified.csv` source
  with the maintained `danbooru_tags_classified.csv` autocomplete/highlight
  source.
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
  Guidance model patching is created once and reused by KSampler-based stages
  instead of being stacked repeatedly.
- Changed AiO Highres sampling to either reuse the first-pass sampler path or
  use the general KSampler path. SPD/SPEED first passes now use general KSampler
  for Highres, and Highres keeps its own `Steps` and `Denoise`.
- Hardened Spectrum sampler calls against node-pack API drift by filtering
  `SpectrumKSamplerAdvanced` and `SpectrumSPDKSampler` keyword arguments against
  the installed `sample()` signature. Sampler Details also reads `/object_info`
  to show detected extra inputs and node-pack tooltips when available.
- Fixed general KSampler + Spectrum Patch routing so installed node packs that
  expose `DiTSpectrumPatch` instead of `DiTSpectrumPatchAdvanced` are supported.
- Fixed AiO SPD/SPEED preview and Highres handoff sizing so the node output,
  preview feed, and Highres target resolution stay aligned with the requested
  workflow resolution.
- Fixed AiO preview result handling so ComfyUI's default `images` UI payload is
  suppressed and only the dedicated `easyuse_anima_preview` payload is used.
- Hardened intermediate preview feed updates so live preview events are tagged
  by run and displayed in the node feed immediately.
- Fixed Image Saver metadata routing so `Steps`, `CFG`, `Sampler`,
  `Scheduler`, `Seed`, and `Denoise` come from the first-pass sampler while
  `Size` uses the final Highres/Detailer output resolution.
- Fixed Prompt Studio highlighting and autocomplete replacement around weighted
  prompt syntax so applying a suggestion does not delete surrounding
  parentheses or weights.
- Fixed unweighted parenthesized tags such as `(@artist name)` or
  `(highres, long hair)` so their inner tags are classified and highlighted by
  category.
- Fixed autocomplete popup activation so syntax-only caret positions, including
  plain brackets, do not open irrelevant suggestions.
- Fixed middle-click behavior on Prompt Studio inputs so it is forwarded to
  canvas panning instead of selecting a text caret.

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
- Added regression coverage for Artist Mix grouped branches, group-weight
  flattening, invalid weight syntax, weighted tag groups, and unweighted
  parenthesized tag classification across meta, character, general, and artist
  tags.
- Ran `python -m unittest discover -s tests`, `python -m compileall -q .`,
  frontend `node --check`, workflow/locale tests, Markdown link checks, and
  Registry metadata sanity checks during release validation.

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
