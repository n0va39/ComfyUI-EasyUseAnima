# ComfyUI EasyUse Anima

Language: [English](README.en.md) | [한국어](README.ko.md) | [Home](README.md)

Small ComfyUI custom node pack for NAIA/Anima workflows.

This package is independent from `comfyui-naia-bridge`. It does not import or
override that node pack, so both can be installed at the same time.

Reference baseline:

- `DNT-LAB/comfyui-naia-bridge` master `b82f98e`
- NAIA API endpoints used:
  - `POST /api/comfyui/random`
  - `peng_override` request field

## Nodes

### Anima NAIA Random Prompt

Category: `NAIA Bridge/API`

Outputs:

- `prompt`
- `negative_prompt`
- `width`
- `height`

Main controls:

- `use_naia_bridge=false`: bypass NAIA and return input `prompt`,
  `negative_prompt`, `width`, `height` as-is. If the inputs are unchanged,
  this mode does not break ComfyUI caching.
- `freeze_naia_output=true`: if cached output is valid, return it without
  calling NAIA. This keeps downstream cache stable for the same fixed output.
- `show_preview=false`: hide the large read-only preview widget.
- Saved-image workflow reproduction: after a fresh NAIA response, saved image
  metadata is written with `freeze_naia_output=true` and cached output values.
  Loading that workflow reproduces the same output without another NAIA call.
- `use_naia_settings=false`: send this node's `pre_prompt`, `post_prompt`,
  `auto_hide`, and preprocessing options to NAIA for this request.

The `remove_*` preprocessing options are marked as advanced inputs.

### Anima Prompt Corrector

Category: `EasyUse Anima/Prompt`

Outputs:

- `corrected_prompt`
- `report`

This node accepts a comma-separated prompt and returns a normalized
ANIMA-ordered prompt plus a JSON report. It uses the vendored `anima_prompt`
MVP core and does not depend on external character/artist exports.

Main controls:

- `artist_overrides`: manual comma- or newline-separated artist triggers.
- `artist_exclusions`: tags that must not be treated as artists.

Prompt syntax:

- Unescaped parentheses are treated as prompt weighting syntax and are preserved,
  for example `(long_hair:1.2)`.
- Literal parentheses in tag names are escaped as `\(` and `\)`.
- Commas inside unescaped weighted parentheses are not split as top-level prompt
  separators by the corrector.
- Natural-language prompt text keeps its original casing.
- If a natural-language sentence is immediately followed by a count tag such as
  `1girl`, the count tag is split out and reordered normally.

### Anima Prompt Builder

Category: `EasyUse Anima/Prompt`

Outputs:

- `prompt`
- `anima_mod_guidance_quality_tags`
- `use_anima_mod_guidance`
- `metadata_prompt`

This node assembles a cleaned prompt from separate prompt fields for NAIA and
Anima Mod Guidance workflows.

Input fields:

- `lora_trigger_tags`: one-line trigger tags received from a LoRA manager.
- `quality_tags`: leading quality tags.
- `trigger_and_artist_tags`: manual model triggers and `@artist` tags.
- `prompt`: main prompt body, including NAIA output.
- `trailing_quality_tags`: trailing quality or style tags.

Behavior:

- Line breaks are treated as comma separators.
- Empty comma groups and duplicate whitespace are cleaned.
- Combined prompt text is passed through ANIMA prompt ordering.
- `use_anima_mod_guidance=true`: `prompt` output excludes the quality fields;
  quality fields are returned through `anima_mod_guidance_quality_tags`.
- `metadata_prompt` always includes quality fields regardless of AMG mode.
- `pin_trigger_tags_to_front=true`: trigger fields are fixed at the front before
  quality tags instead of being placed after leading quality tags.

### Anima Prompt Studio

Category: `EasyUse Anima/Prompt`

This node has the same outputs and prompt-building behavior as `Anima Prompt
Builder`, but adds front-end editing helpers:

- LoRA trigger input is placed near the top of the node.
- Prompt text fields can be resized vertically in the node UI.
- Text fields use tag autocomplete and category highlighting.
- The preview/highlight overlay follows the current text, including externally
  connected text after workflow execution.
- The node keeps its text in workflow serialization.

### Anima Prompt Studio Advanced

Category: `EasyUse Anima/Prompt`

Outputs:

- `positive_prompt`
- `negative_prompt`
- `anima_mod_guidance_quality_tags`
- `use_anima_mod_guidance`
- `metadata_prompt`
- `metadata_negative_prompt`
- `width`
- `height`

This node is the flexible Prompt Studio variant for larger workflows.

Example UI:

**Advanced node overview**
Shows the full advanced prompt layout with connected outputs, prompt fields,
resolution controls, and positive/negative prompt sections.

![Anima Prompt Studio Advanced overview](docs/images/prompt-studio-advanced-overview.png)

**Inputs and top controls**
Shows the main input sockets, `mod guidance` toggle, resolution bucket selector,
and editable prompt field controls.

![Anima Prompt Studio Advanced inputs and controls](docs/images/prompt-studio-advanced-controls.png)

**NAIA prompt field**
Shows the NAIA field used to fill prompt text from a NAIA response while keeping
the stored result editable and reproducible.

![Anima Prompt Studio Advanced NAIA field](docs/images/prompt-studio-advanced-naia.png)

**Resolution bucket selector**
Shows bucket and resolution selection, including the `NAIA` and `Custom` modes
used for saved workflow reproduction.

![Anima Prompt Studio Advanced resolution bucket selector](docs/images/prompt-studio-advanced-resolution.png)

Field model:

- Positive and negative prompts are edited as separate field groups.
- Fields can be added, removed, reordered, enabled, or disabled.
- Supported positive field types are quality, artist, trigger, general, and
  NAIA. Negative prompts also support one NAIA field.
- Negative fields use the same prompt correction and metadata flow as positive
  fields where applicable.
- The NAIA field stores the last NAIA result in the workflow and can be edited
  after it has been filled.
- The trigger field can display a connected `trigger_words` input, remains
  editable after execution, and can be pinned to the front or allowed to follow
  ANIMA ordering.
- The latent image resolution selector is shown below `mod guidance`. It uses a
  bucket selector plus a resolution selector formatted as `width * height
  (ratio)`, sorted by aspect ratio.
- Resolution buckets group sizes by area close to the bucket edge squared
  (`512`, `768`, `896`, `1024`, `1280`, `1536`), expose only dimensions aligned
  to multiples of 32, and keep landscape/portrait pairs together.
- The `Custom` bucket stores editable width and height values in the workflow.
  Custom values are snapped to multiples of 32 so reloaded workflows keep a
  compatible latent size.
- The `NAIA` bucket uses width and height from the same NAIA response that fills
  prompt fields. Saved-image workflows store that resolved size as `Custom`.

NAIA behavior:

- `Fill from NAIA` keeps requesting fresh NAIA text while enabled.
- Positive NAIA, negative NAIA, and NAIA resolution share one NAIA request per
  queue execution.
- Saved-image workflows store the filled text and turn the request flag off, so
  reloaded workflows reuse the saved result.
- A setting can automatically disable general fields above the NAIA field while
  the NAIA field is enabled, then re-enable them when the field is disabled.

Highlighting and syntax:

- Quality, safety/rating, year, count, character, artist, copyright, metadata,
  learned general tags, natural language, syntax errors, and unknown tags use
  separate colors.
- The highlight color settings are shared with `Anima Prompt Studio`.
- Escaped literal prompt characters such as `\(` and `\)` are treated as normal
  tag text and are not considered typos.
- Weighted groups such as `(score_8:0.65)` highlight only the tag text and the
  weight number. Parentheses and `:` are left unhighlighted.
- Weighted groups containing comma-separated tags, for example
  `(highres, absurdres, very aesthetic:0.8)`, classify each inner tag
  separately.
- Unclosed prompt parentheses are shown as syntax errors.
- Long prompts use the Advanced editor's main scroll area instead of per-textarea
  vertical scrollbars. Each textarea keeps enough height for its current text,
  so scrollbars do not cover the text or highlight overlay.
- Highlight overlays copy font family, size, spacing, and wrapping-related
  settings from the source input to keep highlights aligned across font
  settings.

### Anima LoRA Preset

Category: `EasyUse Anima/LoRA`

Outputs:

- `style_prompt`
- `LORA_STACK`
- `trigger_words`
- `active_loras`
- `profile_index`

This node stores reusable LoRA/style profiles for ANIMA workflows.

Example UI:

**LoRA preset node**
Shows a profile with selected LoRAs, strengths, active state, trigger-word output,
and profile save/load controls.

![Anima LoRA Preset node](docs/images/lora-preset-node.png)

**LoRA search**
Shows the folder-tree LoRA chooser with search support for selecting LoRAs from
ComfyUI LoRA paths.

![Anima LoRA Preset LoRA search](docs/images/lora-preset-search.png)

**Profile load**
Shows loading a saved profile from the node-pack profile folder and appending it
as a new profile.

![Anima LoRA Preset profile load](docs/images/lora-preset-profile-load.png)

Main behavior:

- Multiple profiles are stored in one node.
- `profile_index` can be controlled manually or through an input. Out-of-range
  indexes wrap across the available profile count.
- Profiles keep style prompt text, selected LoRAs, LoRA strengths, and enabled
  state in the workflow.
- Profiles can also be saved to and loaded from JSON files under the ComfyUI
  user data directory for `easyuse_anima`.
- Loading a saved profile appends it as a new profile instead of overwriting the
  current profile.

LoRA UI:

- `Add LoRA` opens a folder-tree chooser based on ComfyUI LoRA paths.
- The chooser supports searching.
- Selected LoRAs are shown in a compact list similar to rgthree Power Lora
  Loader.
- Rows support enable/disable, strength adjustment, right-click or menu-button
  actions for move up, move down, and remove.
- The `i` preview button looks for same-name image previews near the LoRA file,
  such as `.webp` previews.
- The row label can display either only the file name or the full relative path
  through ComfyUI Settings.

Trigger words:

- Trigger words are read from LoRA Manager-style metadata JSON sidecars when
  available.
- Trigger words are deduplicated and output as a comma-separated string for
  Prompt Studio trigger fields.

### Anima Detailer Align Hook

Category: `EasyUse Anima/Detailer`

Output:

- `detailer_hook`

Creates an Impact Pack compatible `DETAILER_HOOK` that aligns the crop sampling
size used by Impact detailers. Connect it to `detailer_hook` on Impact
`DetailerForEach` or other Impact-compatible SEGS detailers.

Main behavior:

- `alignment=32` rounds crop sampling width and height upward to 32-multiples.
  This is intended for ANIMA/Spectrum workflows where 16-channel or special VAE
  paths can fail on non-32-multiple crop sizes.
- If another `detailer_hook` is connected, the existing hook runs first and the
  alignment adjustment is applied afterward.
- `alignment=none` keeps the original Impact Pack crop size.

### Anima SAM3 Detailer

Category: `EasyUse Anima/Detailer`

This node is a convenience wrapper for SAM3-based Impact Pack detailer workflows.
`Anima SAM3 Detailer` connects ComfyUI native SAM3 detection, Impact
`MaskToSEGS`, and Impact Pack `DetailerForEach`.

This node requires ComfyUI-Impact-Pack at runtime. The dependency is checked
when the node runs so the rest of EasyUse Anima can still import without Impact
Pack installed.

## Shared Front-End Features

Autocomplete:

- Prompt Builder, Prompt Corrector, Prompt Studio, Prompt Studio Advanced, and
  generic multiline `STRING` prompt/text widgets can use the bundled Korean
  Danbooru autocomplete.
- The autocomplete scope can be selected in ComfyUI Settings with `off`,
  `easyuse_nodes`, or `compatible_global`.
  - `off`: disables EasyUse Anima autocomplete and autocomplete API requests.
  - `easyuse_nodes`: enables autocomplete only for EasyUse Anima prompt nodes.
  - `compatible_global`: default mode; also hooks compatible generic
    prompt/text widgets as before.
- The CSV used for autocomplete and Prompt Studio highlighting can be selected
  in ComfyUI Settings -> `EasyUse Anima: Autocomplete CSV`.
- Type English tags or Korean words from the description/keywords, then use
  arrow keys and Enter/Tab to insert a suggestion.
- Nodes or inputs that already expose LoRA/autocomplete-specific widgets, such
  as LoRA Manager / Lora Stacker nodes, are excluded.

Bundled autocomplete CSV sources:

- Default: `danbooru_tags_classified.csv`.
- `KR_danbooru_tags_with_description v3_modified.csv`: included with
  permission from its author.
- `danbooru_tags_classified.csv`: from
  `Localsmile/danbooru_KR_wiki_tag_search`.

For source selection, search behavior, and developer CSV format details, see the
[Autocomplete CSV Guide](docs/autocomplete-csv.en.md).

ComfyUI Settings:

- NAIA request host, port, Prompt Engineering options, and preprocessing options
  are configured in the EasyUse Anima settings panel.
- EasyUse Anima does not store its own language setting. Node info, input/output
  hints, settings entries, custom DOM buttons, and tooltips follow the ComfyUI
  language setting.
- Prompt metadata filter words are applied only to metadata prompt outputs.
- Prompt Studio typo indicators and category colors can be changed manually.
- Prompt Studio can auto-toggle general fields above the NAIA field.
- LoRA Preset row labels can show file names only or full paths.

## Release Notes

See [RELEASE.md](RELEASE.md) for versioned release notes.

## Requirements

NAIA must expose the ComfyUI remote API used by `comfyui-naia-bridge`.

SAM3 detailer nodes require `ComfyUI-Impact-Pack` at runtime. This is a ComfyUI
custom-node dependency, not a Python package dependency, so it is not listed in
`pyproject.toml` Python dependencies.

Install Python dependency:

```bash
pip install -r requirements.txt
```

ComfyUI restart is required after installing or updating this node pack.

## Installation

Clone into `ComfyUI/custom_nodes`:

```bash
git clone https://github.com/n0va39/ComfyUI-EasyUseAnima
```

Then install dependencies in the ComfyUI Python environment:

```bash
pip install -r ComfyUI-EasyUseAnima/requirements.txt
```

Restart ComfyUI after installation.

Settings and LoRA preset profiles are stored in the ComfyUI user data directory
through `folder_paths.get_system_user_directory("easyuse_anima")`, not inside the
custom node installation folder. This keeps user data stable across Manager
updates and git reinstalls.

## ComfyUI Manager / Registry

This repository includes `pyproject.toml` metadata for future Comfy Registry
registration. The Registry node id is `ComfyUI-EasyUseAnima`.

Before publishing to the Registry, verify that `[tool.comfy].PublisherId` matches
the actual Comfy Registry publisher id.
