# ANIMA Prompt Correction Core

Dependency-light prompt correction helpers for ANIMA-style tag order.

This vendored copy is scoped for the ComfyUI EasyUse Anima node pack MVP. It
does not import ComfyUI, torch, model loading code, taggers, or a general tag DB.

## MVP Scope

- Danbooru-style comma-separated prompt parsing
- ComfyUI/NovelAI prompt weighting syntax preservation
- tag normalization
- built-in ANIMA count tag recognition
- ANIMA ordering
- correction report data

## Ordering

The default ordering is:

```text
quality / meta / year / safety
-> character count / person type
-> character
-> series / copyright
-> artist
-> general or unknown tags
```

## Prompt Syntax

- Unescaped parentheses are prompt weighting syntax and are preserved, for
  example `(long_hair:1.2)`.
- Literal parentheses in tag names are rendered escaped as `\(` and `\)`.
- Commas inside unescaped parentheses are preserved inside the weighted token.
- Natural-language prompt text keeps its original casing.
- Count tags such as `1girl` are split from a preceding sentence ending when the
  source text omitted a comma after the sentence.

Example:

```text
masterpiece, best quality, newest, safe,
1girl,
hatsune miku,
vocaloid,
@artist_name,
aqua eyes, twintails, detached sleeves
```

## Data Sources

This core does not load external character/artist exports or a general tag
database. It uses only built-in ANIMA ordering rules and manual artist
override/exclusion inputs.

Prompt Studio highlighting and autocomplete are implemented outside this core
through the node pack's bundled Korean Danbooru CSV sources.
