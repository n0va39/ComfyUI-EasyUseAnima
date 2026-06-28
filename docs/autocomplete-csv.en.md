# Autocomplete CSV Guide

EasyUse Anima uses bundled Danbooru CSV files for prompt autocomplete and
Prompt Studio highlighting.

These CSV files do not generate LoRA files, LoRA trigger words, or NAIA results.
LoRA triggers are handled through the LoRA Preset/LoRA Manager metadata flow,
and NAIA output comes from the NAIA request result.

## Settings

Open ComfyUI Settings and use the EasyUse Anima entries:

- `Autocomplete mode`
- `Autocomplete CSV`
- `Autocomplete suggestions`

Changing the CSV affects new autocomplete requests immediately. The open
autocomplete popup is closed and the in-browser search cache is cleared. A
browser refresh is normally not required.

## Autocomplete Mode

- `off`
  - Disables all EasyUse Anima autocomplete behavior.
  - No autocomplete API requests are sent.
- `easyuse_nodes`
  - Enables autocomplete only for EasyUse Anima prompt nodes.
  - Generic multiline `STRING` widgets are not hooked.
- `compatible_global`
  - Default mode.
  - Applies autocomplete to EasyUse Anima nodes and compatible prompt/text
    widgets.
  - Nodes with their own LoRA/autocomplete widgets, such as LoRA Manager or
    LoRA Stacker nodes, are excluded.

## Bundled CSV Sources

### `danbooru_tags_classified.csv`

Setting key: `localsmile_kr_wiki`

- Default source.
- Based on `Localsmile/danbooru_KR_wiki_tag_search`.
- Includes useful category separation for Prompt Studio highlighting.
- Recommended when Korean search is the main use case.

### `KR_danbooru_tags_with_description v3_modified.csv`

Setting key: `kr_modified`

- Bundled with permission from its author.
- Can be used for Korean description-based search.
- Search order and category classification can differ from the default CSV.

## Search Behavior

Autocomplete searches:

- English tag names
- Space/underscore variants of tag names
- CSV description or wiki text
- Korean descriptions and keywords

For example, if a row description contains `장발`, searching that Korean word can
return `long hair`.

Prompt Studio highlighting uses both the selected CSV and built-in meta tag
rules. Built-in meta/quality tags are not added as autocomplete candidates, but
they are used for typo checks and color highlighting.

## Artist Tag Policy

Artist tags are treated as artist-category data.

- The expected prompt form is `@artist name`.
- General-category tags are not treated as artist candidates at runtime.
- If an artist appears as a general-category tag, fix the CSV data or select a
  better data source instead of adding a runtime fallback.

## Prompt Text Rules

- Ordinary Danbooru/meta/artist tags use spaces in prompt output.
  - Example: `very_aesthetic` -> `very aesthetic`
  - Example: `@artist_name` -> `@artist name`
- Pony score tags are the only underscore-preserving exception.
  - Example: `score_9`, `score_8`, `score_7:`
- Literal parentheses in tag names are escaped when inserted by autocomplete.
  - Example: `western comics (style)` -> `western comics \(style\)`

These rules are shared by autocomplete insertion, Prompt Studio preview, and
prompt correction output so the three views do not disagree.

## Developer CSV Format

The current settings UI selects between the two bundled CSV sources. It does not
provide a user-facing arbitrary CSV path picker.

When adding a new source in code, use UTF-8 or UTF-8 with BOM. Two formats are
supported.

Four-column format without a header:

```csv
tag,category,count,description
long hair,0,100,"[Fashion] long hair"
artist name,1,80,"[Artist] artist description"
```

Header format:

```csv
name,category,post_count,description
long hair,0,100,"[Fashion] long hair"
hatsune miku,4,90,"[Character] Hatsune Miku"
```

Supported category values:

- `0`: general
- `1`: artist
- `3`: copyright
- `4`: character
- `5`: meta

In the header format, `tag` can be used instead of `name`, `count` instead of
`post_count`, and `wiki` instead of `description`.
