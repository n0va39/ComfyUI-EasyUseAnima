# ComfyUI EasyUse Anima

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

Autocomplete:

- Prompt Builder and Prompt Corrector text fields use a bundled Korean Danbooru
  CSV under `__easyuse_anima__`.
- The CSV used for autocomplete and Prompt Studio tag highlighting can be
  selected in ComfyUI Settings -> `EasyUse Anima: Autocomplete CSV`.
- Generic multiline `STRING` prompt/text nodes, including primitive multiline
  string nodes, can also use the same autocomplete.
- Type English tags or Korean words from the description/keywords, then use
  arrow keys and Enter/Tab to insert a suggestion.
- Nodes or inputs that already expose LoRA/autocomplete-specific widgets, such
  as LoRA Manager / Lora Stacker nodes, are excluded.

Bundled autocomplete CSV sources:

- `KR_danbooru_tags_with_description v3_modified.csv`: included with
  permission from its author.
- `danbooru_tags_classified.csv`: from
  `Localsmile/danbooru_KR_wiki_tag_search`.

### Anima Prompt Studio

Category: `EasyUse Anima/Prompt`

This node has the same outputs and prompt-building behavior as `Anima Prompt
Builder`, but adds front-end editing helpers:

- LoRA trigger input is placed near the top of the node.
- Prompt text fields can be resized vertically in the node UI.
- A tag analysis panel highlights detected tokens by category:
  - `인원수`
  - `캐릭터`
  - `작가`
  - `작품`
  - `학습 태그`
  - `미확인`
- Tags found in the bundled Korean Danbooru CSV are marked as learned tags.

### Anima Prompt Corrector

Category: `EasyUse Anima/Prompt`

Outputs:

- `corrected_prompt`
- `report`

The node accepts a comma-separated prompt and returns a normalized
ANIMA-ordered prompt plus a JSON report. It uses the vendored `anima_prompt`
MVP core and does not depend on external character/artist exports.

Main controls:

- `artist_overrides`: manual comma- or newline-separated artist triggers.
- `artist_exclusions`: tags that must not be treated as artists.

Prompt syntax:

- Unescaped parentheses are treated as prompt weighting syntax and are preserved,
  for example `(long_hair:1.2)`.
- Literal parentheses in tag names are escaped as `\(` and `\)` in the corrected
  output.
- Commas inside unescaped parentheses are not split as top-level tag separators.
- Natural-language prompt text keeps its original casing.
- If a natural-language sentence is immediately followed by a count tag such as
  `1girl`, the count tag is split out and reordered normally.

Dataset download, token storage, and character/artist index loading are not
included. Prompt Studio highlighting and autocomplete use the bundled Korean
Danbooru CSV sources instead.

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
