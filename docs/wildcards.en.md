# Wildcard Guide

EasyUse Anima wildcards expand file-backed `__name__` tokens and dynamic prompt
syntax such as `{a|b|c}` during queue execution.

Where to use them:

- `Anima Prompt Studio Advanced`: configure mode, seed, and seed after generate
  in the wildcard controls below `mod guidance`.
- `Anima Wildcard`: expand wildcard text without Prompt Studio.

## Quick Syntax Reference

| Syntax | Meaning |
| --- | --- |
| `__hair_color__` | Select one option from `hair_color.txt`, `hair_color.yaml`, or `hair_color.yml` |
| `__style/anime__` | Select one option from the nested `style/anime` key |
| `__*/hair_color__` | Search any subfolder for a key whose basename is `hair_color` |
| `__style/*__` | Select from all keys under `style/` |
| `3#__hair_color__` | Select 3 file wildcard options and join them with `, ` |
| `{red|blue|green}` | Select one inline option |
| `{2::red|5::blue|green}` | Select one weighted inline option. Missing weight is 1 |
| `{2$$red|blue|green}` | Select 2 inline options with the default `, ` separator |
| `{1-3$$, $$red|blue|green}` | Select 1 to 3 options and join them with `, ` |
| `{2$$__hair_color__}` | Expand a file wildcard into options, then select 2 |

Weighted example:

```text
{2::red|5::blue|3::green|white}
```

This gives red, blue, green, and white weights of 2, 5, 3, and 1.

Multi-select examples:

```text
{2$$red|blue|green}
{1-3$$, $$red|blue|green}
3#__hair_color__
```

The value before `$$` is the selection count. A range such as `1-3` chooses the
count from the seed. Use `count$$separator$$options` to set a custom separator.

## Default Folder

When the node pack is loaded, it creates the default wildcard folder and a small
test file.

```text
ComfyUI/user/__easyuse_anima/wildcards/easyuse_anima_test.txt
```

Test token:

```text
__easyuse_anima_test__
```

Files are read as UTF-8 text. Empty lines and lines starting with `#` are skipped.

## Extra Paths

Additional wildcard folders can be registered in ComfyUI Settings under the
EasyUse Anima `Wildcard` section.

- Enter one folder per line or separate folders with `;`.
- Absolute paths and paths relative to the ComfyUI root are supported.
- Extra paths are searched before the default folder.
- If multiple folders contain the same key, the first matching folder wins.
- Autocomplete responses expose only relative keys, not local absolute paths.

## File Syntax

Supported files:

- `.txt`
- `.yaml`
- `.yml`

Text file example:

```text
# wildcards/hair_color.txt
black hair
white hair
2::pink hair
```

Usage:

```text
__hair_color__
3#__hair_color__
```

YAML example:

```yaml
hair_color:
  - black hair
  - white hair
style:
  anime:
    - cel shading
    - flat color
```

Usage:

```text
__hair_color__
__style/anime__
```

`N::candidate` is a weighted option. Populate mode uses the weight for weighted
selection. Sequential mode counts it as one candidate and strips the `N::`
prefix.

`<lora:name:weight>` syntax is preserved as text. EasyUse Anima wildcard
expansion does not apply LoRAs to MODEL or CLIP.

## Modes

- `일반 채우기`: expands the source text with seed-based selection.
- `고정`: produces the same expanded result for the same source text, seed, and
  wildcard files.
- `순차`: selects `seed % candidate_count` for each candidate list. The seed
  control is forced to `increment`.
- `재현`: reuses expanded text stored in saved-result workflows.

Seed controls:

- `fixed`
- `randomize`
- `increment`
- `decrement`

## Prompt Studio Advanced

`Anima Prompt Studio Advanced` shows wildcard controls below `mod guidance`.

- mode
- wildcard seed
- seed after generate

At execution time, wildcard expansion is applied to `advanced_fields`. The live
workflow keeps the original wildcard text and next seed state. Saved-image
workflows store the expanded text and reproduction mode.

When NAIA fill is also enabled, the NAIA result is applied before wildcard
expansion.

## Anima Wildcard Node

Use `Anima Wildcard` when a workflow only needs string wildcard expansion without
Prompt Studio.

Outputs:

- `text`: expanded prompt text
- `seed`: next seed after applying the seed control

Saved-image workflows store the expanded result in `populated_text` and switch
the mode to `재현`.

## Autocomplete and Highlighting

- Typing `__` or `__partial` opens wildcard autocomplete.
- Selecting an item replaces the current token with `__relative/key__`.
- Prompt Studio highlighting uses a separate wildcard color instead of treating
  wildcard syntax as normal tags, and the color can be changed in ComfyUI
  Settings.
