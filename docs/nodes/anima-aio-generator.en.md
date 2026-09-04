# Anima AiO Generator

Category: `EasyUse Anima/AiO`

![Anima AiO Generator](../images/aio-generator-node.png)

`Anima AiO Generator` consumes the dedicated context from `Easy Use Anima Input`
and runs prompt encoding, first-pass sampling, optional Highres, optional
Detailer, and image saving in one output node. Prompt editing stays upstream in
Prompt Studio, so the generator UI does not expose prompt fields.

## Basic Wiring

1. Connect prompt data from `Anima Prompt Studio Advanced v2` to `Easy Use Anima Input`.
2. In `Easy Use Anima Input`, select the ANIMA diffusion model, VAE, and CLIP separately.
3. Connect `Easy Use Anima Input` to the generator's `easy use anima input` socket.
4. Optionally connect `LORA_STACK` from `Anima LoRA Preset` to `lora_stack`.
5. Only for a third-party AiO extension, connect its `EASYUSE_ANIMA_AIO_HOOK`
   output to `aio_hook`. Compose multiple hooks with `Anima AiO Hook Combine`.

## Extension hooks

`aio_hook` is optional; leaving it disconnected preserves existing generation
and save behavior. Version 1 exposes first-pass MODEL and allowlisted sampler
patches, final postprocess before/after callbacks, same-shape `IMAGE` patches,
extension metadata, and optional previews. A postprocess hook-modified `IMAGE`
is not re-encoded to make the Generator's `LATENT` output match it.

To build a hook node, see the [AiO Hook API v1 developer guide](../extensions/aio-hooks.en.md)
and the [copyable example](../../examples/third_party_aio_hook/).

## Generation Profiles

The profile button in the `SAMPLER` header applies one complete generation
settings snapshot.

- `Normal` keeps the standard defaults and disables optional Spectrum/DCW and
  KJ execution optimizations.
- `Turbo` uses `steps=10`, `CFG=1`, `er_sde`, and `simple`.
- `Optimized` enables Spectrum/DCW across sampling stages plus the recommended
  KJ FP16 accumulation, SageAttention, Sage compile, and Torch Compile values.
  DAVE and Safe PAG remain separate choices and stay disabled.

If the current settings do not exactly match a built-in profile, the button
shows `Custom`. A named user profile stores the complete current settings in
ComfyUI user data and can be loaded, overwritten, renamed, or deleted after a
restart. Editing an applied user profile changes the label back to `Custom`.

Workflows serialize the complete generation settings, not the selected profile
name. This preserves the generated setup even when the named profile is not
available on another ComfyUI installation.

## Sampler Modes

The `Mode` field in Sampler settings selects the actual execution path.

Initial defaults are `steps=32`, `sampler=er_sde`, `scheduler=simple`, and
`shift=3.0`. `shift=3.0` is the Anima model-recommended default and is always
applied.

| Mode | Call path | Required node pack |
| --- | --- | --- |
| `comfy_ksampler` | ComfyUI built-in KSampler. Optional Spectrum model patches and corrections can be applied before sampling | Built-in ComfyUI, optional `ComfyUI-Spectrum-KSampler` |
| `spectrum_mod_guidance_advanced` | Direct call to `KSampler (Spectrum + Mod Guidance Advanced)` | `ComfyUI-Spectrum-KSampler` |
| `spectrum_spd_speed` | Direct call to `KSampler (Spectrum + SPD / SPEED)` | `ComfyUI-Spectrum-KSampler` |

Integrated Spectrum sampler modes do not also call the model-patch path meant for
the normal KSampler. Highres reuses the first-pass sampler path by default, but
overrides only `Steps` and `Denoise` with the Highres values. When the first pass
uses `spectrum_spd_speed`, Highres does not reuse SPD/SPEED and falls back to the
general KSampler path. When main-sampler reuse is disabled, Highres always uses
the general KSampler path.

Calls to `SpectrumKSamplerAdvanced` and `SpectrumSPDKSampler` are filtered
against the installed Spectrum node pack's actual `sample()` signature so
unsupported parameters are not passed. Sampler Details also reads `/object_info`
to show discovered extra inputs under `Detected inputs` and uses node-pack
tooltips when they are available.

`Anima DAVE`, AuraFlow shift, KJNodes FP16 accumulation, SageAttention, and
Torch Compile are not sampler modes. They are model patch/optimization controls
in Advanced Options and are applied before the selected first-pass sampler when
enabled.

Highres defaults are `Scale by=1.5` and `Denoise=0.25`. Highres and Detailer settings use a
single-column scroll layout so long option sets remain readable.

Detailer Settings show Face/Eye processing blocks as tabs. Each tab can be
renamed and moved left or right to change execution order. Tab names are UI
metadata; runtime dispatch uses stable internal keys plus `detailer.order`.

## Saving And Reproducibility

Save Options are enabled by default and use EasyUse's native output backend.
The serialized backend ID remains `image_saver` so existing workflows and
profiles keep loading, but `ComfyUI-Image-Saver` is no longer required.

PNG, JPEG, and WebP all store an A1111-style `parameters` block. PNG stores the
ComfyUI prompt and workflow as text chunks; JPEG and WebP use the same EXIF
Make/Model representation that ComfyUI understands. Keep `Embed workflow`
enabled when saved images should reload into the same generation setup. Enable
`Save workflow JSON` for a sidecar copy. If a JPEG workflow exceeds EXIF's size
limit, EasyUse preserves the A1111 metadata and writes the workflow sidecar
automatically instead of leaving a partially written image.

Metadata is bounded independently of ComfyUI's request-size setting: A1111
parameters are limited to 512 KiB, prompt JSON to 2 MiB, workflow JSON to 4 MiB,
embedded metadata to 8 MiB per image, and repeated batch metadata to 64 MiB per
save. JSON also has depth, item, string, and `extra_pnginfo` key limits. An
oversized payload fails before image publication instead of producing a partial
or unexpectedly large output.

WebP is lossy when `Lossless WebP` is off; `JPEG/WebP quality` controls its
quality/file-size tradeoff. When lossless mode is on, WebP preserves the pixel
values supplied to the saver.

Saved metadata uses first-pass sampler values for `Steps`, `CFG`, `Sampler`,
`Scheduler`, `Seed`, and `Denoise`. `Size` uses the final image resolution after
Highres and Detailer. EasyUse hashes the locally resolved diffusion model,
applied `lora_stack` files, and `embedding:name` references in either prompt.
Embedding subdirectories and `(embedding:name:0.8)` attention weights are
supported; missing, unsafe, or ambiguous inventory names are skipped.

SHA-256 results use an in-memory cache plus a bounded, atomic cache under the
ComfyUI user-data directory, with progress shown for uncached files. EasyUse
never creates cache files beside model resources. Locally calculated hashes are
shortened for A1111 compatibility; validated manual hash values are preserved
and cannot replace the locally owned `model` hash. `Civitai data` is disabled by
default; explicitly enable it to enrich local and manual hashes through fixed
`https://civitai.com/api/v1` endpoints. A short-hash result is accepted only
when the response contains an exact matching file hash. Failures are logged and
do not block image saving. Hash Fetcher and local/manual enrichment share a
12-second, 16-request budget per save; remaining lookups are skipped when
either limit is reached. Civitai Hash Fetcher rows likewise store username,
model name, and version and add `model_name:AutoV3` entries.

## Required Node Packs

- Required: `ComfyUI-EasyUseAnima`
- Sample workflow defaults: `ComfyUI-Spectrum-KSampler`
- Optional features: `ComfyUI-KJNodes` for SageAttention/Torch Compile, `ComfyUI-Impact-Pack` for the AiO SAM3 detailer path, `ComfyUI-Anima-DAVE` for the Anima DAVE model patch

When an optional node pack is not installed, the related UI is locked and queue
preparation disables that option before execution.

Example workflows:

- [ANIMA_Easy_Use_workflow_v1_release_en.json](../example_workflows/ANIMA_Easy_Use_workflow_v1_release_en.json)
- [ANIMA_Easy_Use_workflow_v1_release_ko.json](../example_workflows/ANIMA_Easy_Use_workflow_v1_release_ko.json)
- [EasyUse_Anima_AiO_generator_release_ko.json](../example_workflows/EasyUse_Anima_AiO_generator_release_ko.json)

Usage guide: [ANIMA Easy Use workflow v1](../Anima%20AiO/ANIMA_Easy_Use_workflow_v1_EN.md)
