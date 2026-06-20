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

Field model:

- Positive and negative prompts are edited as separate field groups.
- Fields can be added, removed, reordered, enabled, or disabled.
- Supported positive field types are quality, artist, trigger, general, and
  NAIA.
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
- Resolution buckets follow the crop preprocess tier style (`512`, `768`,
  `896`, `1024`, `1280`, `1536`) and only expose dimensions aligned to
  multiples of 32.
- The `Custom` bucket stores editable width and height values in the workflow.
  Custom values are snapped to multiples of 32 so reloaded workflows keep a
  compatible latent size.

NAIA behavior:

- `Fill from NAIA` keeps requesting fresh NAIA text while enabled.
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

### Anima LoRA Preset

Category: `EasyUse Anima/LoRA`

Outputs:

- `style_prompt`
- `LORA_STACK`
- `trigger_words`
- `active_loras`
- `profile_index`

This node stores reusable LoRA/style profiles for ANIMA workflows.

Main behavior:

- Multiple profiles are stored in one node.
- `profile_index` can be controlled manually or through an input. Out-of-range
  indexes wrap across the available profile count.
- Profiles keep style prompt text, selected LoRAs, LoRA strengths, and enabled
  state in the workflow.
- Profiles can also be saved to and loaded from JSON files under
  `__easyuse_anima__/profiles`.
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

## Shared Front-End Features

Autocomplete:

- Prompt Builder, Prompt Corrector, Prompt Studio, Prompt Studio Advanced, and
  generic multiline `STRING` prompt/text widgets can use the bundled Korean
  Danbooru autocomplete.
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

ComfyUI Settings:

- NAIA request host, port, Prompt Engineering options, and preprocessing options
  are configured in the EasyUse Anima settings panel.
- Prompt metadata filter words are applied only to metadata prompt outputs.
- Prompt Studio typo indicators and category colors can be changed manually.
- Prompt Studio can auto-toggle general fields above the NAIA field.
- LoRA Preset row labels can show file names only or full paths.

## Requirements

NAIA must expose the ComfyUI remote API used by `comfyui-naia-bridge`.

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

## ComfyUI Manager / Registry

This repository includes `pyproject.toml` metadata for future Comfy Registry
registration. The Registry node id is `easyuse-anima`.

Before publishing to the Registry, verify that `[tool.comfy].PublisherId` matches
the actual Comfy Registry publisher id.
