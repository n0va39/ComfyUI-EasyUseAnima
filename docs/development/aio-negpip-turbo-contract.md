# AiO NegPip Turbo Conditioning Contract

Status: AIO-NEGPIP-03 contract fixture. Production and UI cutover remain
AIO-NEGPIP-04.

## Execution prompt policy

Turbo consumes the execution-ready positive and negative prompts after prompt
translation and wildcard expansion. It never writes the derived text back to
prompt data, workflow inputs, profiles, or metadata fields that represent the
user's original prompt.

The negative contribution uses policy revision 1:

1. discard empty top-level items and lines whose first non-space character is
   `#`;
2. preserve escaped delimiters and nested `()`, `{}`, `[]`, and `[[ ]]` text;
3. canonicalize remaining top-level comma/newline items with `, `;
4. invert the sign of every explicit parenthetical numeric weight;
5. wrap the complete derived prompt in one outer `-1` weight group;
6. append that group to the execution-only positive prompt.

The outer whole-prompt group is selected instead of wrapping each top-level
item separately. ComfyUI's prompt-weight parser assigns the outer weight to all
unweighted text in the group. Keeping separators inside the same group avoids
leaving top-level separator tokens at positive weight. Explicit numeric weights
are absolute assignments in that parser, so their signs are inverted as well;
otherwise an inner `(text:0.5)` would escape the requested additional `-1`
multiplier.

Unbalanced or mismatched delimiters fail closed with
`negpip_turbo_prompt_malformed`. The caller retains the source text unchanged;
there is no lossy fallback.

The executable golden scenarios are in
`tests/fixtures/aio_negpip_turbo_contract.v1.json` and include commas, newlines,
comments, nesting, escapes, existing positive and negative numeric weights,
empty prompts, and malformed input.

## Conditioning ownership

Turbo uses the MODEL and CLIP returned by the existing public `CLIPNegPip`
adapter. The same patched CLIP owns both encodes:

- positive execution conditioning: original positive execution prompt plus the
  derived negative contribution;
- negative execution conditioning: an explicit empty prompt encode.

The neutral conditioning is not `None`, a zero tensor, the original negative
conditioning, or an encode from the unpatched CLIP. Artist Mix and Mod Guidance
integration remain AIO-NEGPIP-04 compatibility work; this contract does not move
their feature meaning into the shared lifecycle or prompt owners.

## Runtime CFG ownership

Turbo forces effective CFG `1.0` only at sampling calls:

- first pass;
- Highres;
- each enabled Detailer target;
- USDU upscale.

The stored sampler, Highres, Detailer, and Upscale CFG values remain unchanged.
ResShift, Postprocess, and Save Output do not acquire a synthetic CFG because
they are not CFG sampling stages. Turning Turbo off therefore exposes the
previously stored values without migration or restoration writes.

## AIO-NEGPIP-04 handoff

The implementation reuses the existing NegPip adapter, generation request,
stage sampler, first-pass cache, and metadata owners. It must consume the golden
fixture rather than introduce another parser or conditioning policy. The next
phase adds settings/profile/UI ownership, runtime conditioning and CFG cutover,
cache/metadata signatures, and the selected compatibility/live matrix. It must
not import or vendor ComfyUI-ppm private source.
