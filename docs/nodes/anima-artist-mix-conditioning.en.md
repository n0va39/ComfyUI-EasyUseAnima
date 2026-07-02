# Anima Artist Mix Conditioning

Category: `EasyUse Anima/Prompt`

Inputs:

- `clip`
- `prompt`
- `artist_tags`
- `artist_position`
- `artist_mix_mode`
- artist mix tuning inputs

Output:

- `positive`

This standalone artist mix node takes a regular positive prompt plus separate
artist tags and outputs positive `CONDITIONING`. Use it when a workflow does
not use Prompt Studio Advanced v2 but still needs the same artist mix methods.

Artist tags here means the text entered in the `artist_tags` input, not tokens
marked with `@`.

## Position Handling

`artist_position` controls where artist tags are applied.

| Value | Behavior |
| --- | --- |
| `correct` | Default. Combines `prompt` and `artist_tags`, then applies ANIMA prompt ordering. |
| `front` | Pins artist tags before the prompt. |
| `back` | Pins artist tags after the prompt. |

Use `correct` for normal ANIMA syntax. Use `front` or `back` only when another
conditioning workflow requires a fixed artist-tag position.

## Artist Mix Mode

| Value | Cost | Behavior |
| --- | --- | --- |
| `prompt` | 1 positive branch | Inserts artist tags into the prompt and encodes once. |
| `average` | 1 positive branch | Blends per-artist conditionings by weighted average. |
| `delta_rms` | 1 positive branch | Mixes artist deltas from the base prompt and restores RMS style energy. |
| `hybrid` | top K + 1 branches | Keeps strongest artists as exact branches and compresses the tail. |
| `clustered` | cluster_count branches | Groups similar artist deltas into compressed branches. |
| `exact` | N artist branches | Creates one conditioning branch per artist. Most faithful, highest cost. |

`composite_exact`, `late_exact`, `average_late_exact`, and
`scheduled_average` are compatibility modes shared with Prompt Data
Conditioning.

## Tuning Inputs

- `artist_mix_start_percent`: sampling start percent for late/scheduled modes.
- `artist_mix_strength_scale`: strength multiplier for exact-style branches.
- `artist_mix_style_gain`: style gain for `delta_rms`, `hybrid`, and `clustered` compressed branches.
- `artist_mix_rms_scale_cap`: maximum RMS style-energy restore scale.
- `artist_mix_exact_top_k`: number of strongest artists kept exact in `hybrid`.
- `artist_mix_cluster_count`: compressed branch count for `clustered`.
- `artist_mix_dominant_isolation`: keeps dominant artists as exact branches instead of clustering them.
- `artist_mix_dominant_threshold`: normalized artist-weight threshold for dominant isolation.

## Difference From Advanced v2

`Anima Prompt Data Conditioning` reads artist fields and artist mix settings
from `EASYUSE_ANIMA_PROMPT_DATA`. `Anima Artist Mix Conditioning` is standalone:
it only needs `prompt` and `artist_tags` and returns the resulting positive
conditioning.
