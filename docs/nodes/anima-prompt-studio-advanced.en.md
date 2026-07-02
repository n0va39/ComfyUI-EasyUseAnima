# Anima Prompt Studio Advanced

Category: `EasyUse Anima/Prompt`

Outputs:

- `positive_prompt`
- `negative_prompt`
- `anima_mod_guidance_quality_tags`
- `anima_mod_guidance_negative_prompt`
- `use_anima_mod_guidance`
- `use_negative_anima_mod_guidance`
- `metadata_prompt`
- `metadata_negative_prompt`
- `width`
- `height`

This is the flexible Prompt Studio variant for larger workflows.

![Anima Prompt Studio Advanced](../images/nodes/anima-prompt-studio-advanced.png)

## Field Model

- Positive and negative prompts are edited as separate field groups.
- Fields can be added, removed, reordered, enabled, or disabled.
- Positive field types are quality, artist, trigger, general, and NAIA.
- Negative prompts can also contain one NAIA field.
- The NAIA field stores the last NAIA result in the workflow and remains editable
  after it is filled.
- The trigger field can display connected `trigger_words` and can be pinned to
  the front or passed through ANIMA ordering.

## Resolution

- Latent image resolution controls are shown below `mod guidance`.
- Buckets support `512`, `768`, `896`, `1024`, `1280`, and `1536`.
- `Custom` stores editable width and height values in the workflow.
- `NAIA` uses width and height from the same NAIA response that fills prompt
  fields.
- Saved-image workflows store the resolved size as `Custom` so the result can be
  reproduced.

## Wildcards

The wildcard control row below `mod guidance` sets mode, seed, and seed after
generate.

- The live workflow keeps original wildcard text and the next seed state.
- Saved-image workflows store expanded text in `재현` mode.
- When NAIA fill is also enabled, NAIA text is applied before wildcard expansion.

See the [Wildcard Guide](../wildcards.en.md) for syntax.

## Artist Mix

`Anima Prompt Studio Advanced v2` outputs one `EASYUSE_ANIMA_PROMPT_DATA` socket
instead of the older string outputs. The prompt data stores artist-field text
and `artist_mix` settings under dedicated keys.

Prompt data also includes `outputs` for old compatibility values and
`parameters` keyed by every required v2 node input. Downstream nodes should read
dict keys instead of relying on output slot order when new fields are added.

- Artist field means the Advanced artist-tag input field, not tokens marked
  with `@`.
- When artist mix is disabled, artist-field text stays in the positive prompt.
- When artist mix is enabled, artist-field text is removed from the base prompt,
  and `Anima Prompt Data Conditioning` creates positive `CONDITIONING` with the
  selected artist mix mode.
- For workflows that do not use Prompt Data, use
  [Anima Artist Mix Conditioning](anima-artist-mix-conditioning.en.md) with a
  regular prompt and separate artist tags.

## Prompt Data Helper Nodes

- `Anima Prompt Studio Advanced v2`: outputs one `EASYUSE_ANIMA_PROMPT_DATA`
  socket.
- `EASYUSE_ANIMA_PROMPT_DATA`: passes prompt data through, applies optional
  compatibility-output overrides, and unfolds strings, booleans, width, and
  height.
- `Anima Prompt Data Conditioning`: reads prompt data and outputs
  positive/negative `CONDITIONING`, a batch-size-1 `latent_image`, and the model
  after Spectrum Mod Guidance patching when enabled.

## Highlighting

- Quality, safety/rating, year, count, character, artist, copyright, metadata,
  learned general tags, natural language, syntax errors, and unknown tags use
  separate highlight classes.
- Wildcard syntax such as `__wildcard__`, `3#__wildcard__`, and `{a|b|c}` uses a
  separate wildcard color.
- Highlight overlays synchronize font family, size, spacing, and wrapping with
  the source input.
