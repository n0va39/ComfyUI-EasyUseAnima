# Anima Prompt Data Strings

Category: `EasyUse Anima/Prompt`

Input:

- `EASYUSE_ANIMA_PROMPT_DATA`

Outputs:

- `positive_prompt`
- `negative_prompt`
- `anima_mod_guidance_quality_tags`
- `anima_mod_guidance_negative_prompt`
- `metadata_prompt`
- `metadata_negative_prompt`
- `global_prompt`
- `positive_without_artist_section`
- `negative_without_artist_section`
- `artist_tags`
- `artist_weighted_tags`
- `artist_mix_prompt`
- `artist_mix_mode`

This node extracts commonly needed string values from an
`EASYUSE_ANIMA_PROMPT_DATA` dict. Use it when a v2 prompt-data workflow needs to
feed older string-based sections or text display nodes.

The `EASYUSE_ANIMA_PROMPT_DATA` helper node passes prompt data through and also
expands older Advanced compatibility outputs, Boolean values, and width/height.
`Anima Prompt Data Strings` is the simpler extractor for string outputs only.

## Artist Outputs

- `global_prompt`: base positive prompt string for artist-mix workflows.
- `positive_without_artist_section`: positive prompt with Advanced artist fields removed.
- `artist_tags`: artist tag text from Advanced artist fields.
- `artist_weighted_tags`: artist tag text with prompt weight syntax preserved.
- `artist_mix_prompt`: artist tag string used by artist mix conditioning.
- `artist_mix_mode`: artist mix mode stored in prompt data.

Artist tags are identified by the Advanced artist field or standalone
`artist_tags` input, not by an `@` prefix.
