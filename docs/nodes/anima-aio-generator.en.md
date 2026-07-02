# Anima AiO Generator

Category: `EasyUse Anima/AiO`

`Anima AiO Generator` consumes the dedicated context from `Easy Use Anima Input`
and runs prompt encoding, first-pass sampling, optional Highres, optional
Detailer, and image saving in one output node. Prompt editing stays upstream in
Prompt Studio, so the generator UI does not expose prompt fields.

## Basic Wiring

1. Connect prompt data from `Anima Prompt Studio Advanced v2` to `Easy Use Anima Input`.
2. In `Easy Use Anima Input`, select the ANIMA diffusion model, VAE, and CLIP separately.
3. Connect `Easy Use Anima Input` to the generator's `easy use anima input` socket.
4. Optionally connect `LORA_STACK` from `Anima LoRA Preset` to `lora_stack`.

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
the normal KSampler. Highres and Detailer stages run through stage samplers and
follow the main CFG, sampler, and scheduler by default.

`Anima DAVE`, AuraFlow shift, KJNodes FP16 accumulation, SageAttention, and
Torch Compile are not sampler modes. They are model patch/optimization controls
in Advanced Options and are applied before the selected first-pass sampler when
enabled.

Highres follows the main CFG, sampler, and scheduler by default. Its defaults
are `Scale by=1.5` and `Denoise=0.25`. Highres and Detailer settings use a
single-column scroll layout so long option sets remain readable.

Detailer Settings show Face/Eye processing blocks as tabs. Each tab can be
renamed and moved left or right to change execution order. Tab names are UI
metadata; runtime dispatch uses stable internal keys plus `detailer.order`.

## Saving And Reproducibility

Save Options are enabled by default and use the `ComfyUI-Image-Saver` backend.
Keep `Embed workflow` enabled when saved images should reload into the same
generation setup. Civitai Hash Fetcher rows store username, model name, and
version, then pass `model_name:AutoV3` into Image Saver `additional_hashes`.

Saved metadata uses first-pass sampler values for `Steps`, `CFG`, `Sampler`,
`Scheduler`, `Seed`, and `Denoise`. `Size` uses the final image resolution after
Highres and Detailer. LoRAs applied through `lora_stack` are appended to the
Image Saver metadata prompt as `<lora:name:weight>` tokens so Image Saver can
write Civitai LoRA resources and weights.

## Required Node Packs

- Required: `ComfyUI-EasyUseAnima`
- Sample workflow defaults: `ComfyUI-Spectrum-KSampler`, `ComfyUI-Image-Saver`
- Optional features: `ComfyUI-KJNodes` for SageAttention/Torch Compile, `ComfyUI-Impact-Pack` for SAM3 Detailer, `ComfyUI-Anima-DAVE` for the Anima DAVE model patch

When an optional node pack is not installed, the related UI is locked and queue
preparation disables that option before execution.

Example workflows:

- [ANIMA_Easy_Use_workflow_v1_release_ko.json](../example_workflows/ANIMA_Easy_Use_workflow_v1_release_ko.json)
- [EasyUse_Anima_AiO_generator_release_ko.json](../example_workflows/EasyUse_Anima_AiO_generator_release_ko.json)

Usage draft: [ANIMA Easy Use workflow v1](../Anima%20AiO/ANIMA_Easy_Use_workflow_v1_KO.md)
