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
- `Inline autocomplete preview`
- `Preview closing brackets`

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

### `danbooru_2025-09-01.csv`

Setting key: `dbr_danbooru_2025_09_01`

- Default and recommended source for most users.
- Based on `DraconicDragon/dbr-e621-lists-archive`.
- Source license: Unlicense.
- Covers current Danbooru tag names and aliases without Korean descriptions.
- Recommended for non-Korean users and general Danbooru prompt autocomplete.

### `e621_2025-09-01.csv`

Setting key: `dbr_e621_2025_09_01`

- Based on `DraconicDragon/dbr-e621-lists-archive`.
- Source license: Unlicense.
- Covers e621 tag names and aliases.
- e621 species and lore categories are mapped to the existing trained-tag
  highlight class because EasyUse Anima does not expose separate species/lore
  colors.

### `danbooru_e621_merged_2025-09-01.csv`

Setting key: `dbr_danbooru_e621_merged_2025_09_01`

- Based on `DraconicDragon/dbr-e621-lists-archive`.
- Source license: Unlicense.
- Combines Danbooru and e621 into one CSV for broader autocomplete.
- Use only when you need a single mixed source. The upstream archive warns that
  the merged format is not future-proof: e621 category numbers are offset into a
  Danbooru-invalid range, so future category changes can cause merge/category
  collisions.

### `danbooru_tags_classified.csv`

Setting key: `localsmile_kr_wiki`

- Korean search source.
- Based on `Localsmile/danbooru_KR_wiki_tag_search`.
- Includes useful category separation for Prompt Studio highlighting.
- Recommended when Korean search is the main use case.

## Search Behavior

Autocomplete searches:

- English tag names
- Space/underscore variants of tag names
- CSV description or wiki text
- Korean descriptions and keywords when the selected CSV includes Korean text

For example, if a row description contains `장발`, searching that Korean word can
return `long hair`.

Prompt Studio highlighting uses both the selected CSV and built-in meta tag
rules. Built-in meta/quality tags are not added as autocomplete candidates, but
they are used for typo checks and color highlighting.

When inline autocomplete preview is enabled, the remaining text that the
selected suggestion would insert is shown as ghost text in the Prompt Studio
highlight overlay. With that option enabled, suggestions are shown more
strictly: the caret must be on real tag text, not on syntax-only characters such
as brackets or commas.

Closing bracket preview is an editor helper. Typing an opening bracket inserts
the matching closing bracket at the caret, but committing an autocomplete
suggestion does not force-close multi-item groups.

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

The current settings UI uses the maintained bundled CSV source. It does not
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
