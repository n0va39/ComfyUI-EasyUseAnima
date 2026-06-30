# Anima Prompt Corrector

Category: `EasyUse Anima/Prompt`

Outputs:

- `corrected_prompt`
- `report`

This node accepts a comma-separated prompt and returns an ANIMA-ordered prompt
plus a JSON report.

![Anima Prompt Corrector](../images/nodes/anima-prompt-corrector.png)

## Main Inputs

- `prompt`: source prompt to normalize.
- `artist_overrides`: manual comma- or newline-separated artist triggers.
- `artist_exclusions`: tags that must not be treated as artists.

## Prompt Handling

- Unescaped parentheses are treated as prompt weighting syntax and preserved.
- Literal parentheses in tag names should be escaped as `\(` and `\)`.
- Commas inside weighted parentheses are not split as top-level separators.
- Natural-language text keeps its original casing.
- Count tags such as `1girl` immediately after a natural-language sentence are
  split out and reordered normally.
