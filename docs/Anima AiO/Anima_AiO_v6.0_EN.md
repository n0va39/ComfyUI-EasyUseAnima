# Anima AiO v6.0 English Guide

Anima AiO v6.0 is an ANIMA-based ComfyUI workflow. It includes T2I, I2I, HighRes, Inpainting, Face/Eye Detailer, Upscale, and Image Save paths in one workflow file.

## Workflow File

- [Anima_AiO_v6.0_release_en.json](../example_workflows/Anima_AiO_v6.0_release_en.json)

After loading the workflow in ComfyUI, read the Markdown guide note at the top of each major section.

## Required Models

Place each file in the matching ComfyUI model folder for the sections you use.

| Purpose | File | Location |
|---|---|---|
| Text encoder | [qwen_3_06b_base.safetensors](https://huggingface.co/circlestone-labs/Anima/resolve/main/split_files/text_encoders/qwen_3_06b_base.safetensors?download=true) | `models/text_encoders/` |
| Diffusion model | [anima-base-v1.0.safetensors](https://huggingface.co/circlestone-labs/Anima/resolve/main/split_files/diffusion_models/anima-base-v1.0.safetensors) | `models/diffusion_models/` |
| VAE | [qwen_image_vae.safetensors](https://huggingface.co/circlestone-labs/Anima/resolve/main/split_files/vae/qwen_image_vae.safetensors?download=true) | `models/vae/` |
| Utility LoRA | [Cosmos-Predict2.5-2B-base-distilled-LoRA.safetensors](https://huggingface.co/hanzogak/Anima-Comradeship/resolve/main/LoRA/Cosmos-Predict2.5-2B-base-distilled-LoRA.safetensors?download=true) | `models/loras/` |
| Inpainting | [anima-lllite-inpainting-v1.safetensors](https://huggingface.co/kohya-ss/Anima-LLLite/resolve/main/anima-lllite-inpainting-v1.safetensors) | `models/controlnet/` |
| Upscale | [2x-AnimeSharpV4_Fast_RCAN_PU.safetensors](https://huggingface.co/Kim2091/2x-AnimeSharpV4/resolve/main/2x-AnimeSharpV4_Fast_RCAN_PU.safetensors?download=true) | `models/upscale_models/` |

## Custom Nodes

If ComfyUI Manager automatic installation misses a dependency, install the repository manually and restart ComfyUI.

- [ComfyUI-EasyUseAnima](https://github.com/n0va39/ComfyUI-EasyUseAnima)
- [ComfyUI-Anima-DAVE](https://github.com/sorryhyun/ComfyUI-Anima-DAVE)
- [ComfyUI-Anima-LLLite](https://github.com/kohya-ss/ComfyUI-Anima-LLLite)
- [ComfyUI-DCW](https://github.com/namemechan/ComfyUI-DCW)
- [ComfyUI-Spectrum-KSampler](https://github.com/sorryhyun/ComfyUI-Spectrum-KSampler)
- [ComfyUI-Spectrum-sdxl](https://github.com/ruwwww/ComfyUI-Spectrum-sdxl)
- [ComfyUI-KJNodes](https://github.com/kijai/ComfyUI-KJNodes)
- [ComfyUI-Impact-Pack](https://github.com/ltdrdata/ComfyUI-Impact-Pack)
- [rgthree-comfy](https://github.com/rgthree/rgthree-comfy)
- [ComfyUI Image Saver](https://github.com/alexopus/ComfyUI-Image-Saver)

## Basic Flow

1. Check the style LoRA preset and trigger prompt in the `LoRA` section.
2. Use `T2I` for new images or `I2I` when starting from an input image.
3. `2. Model Load` and `3. ANIMA Generation` are the base generation path.
4. After the base path works, enable `HighRes`, `Inpainting`, `Face/Eye Detailer`, and `Upscale` only as needed.
5. Check filename and metadata options in the `Image Save` section.

## Section Summary

### LoRA

To reproduce the release preset style, check the preset LoRA links note inside the workflow and install the listed LoRAs. `Anima LoRA Preset` `FIX` can repair paths only when the filename matches.

### T2I / I2I

`width` and `height` define the base generation resolution. Test with the release defaults first. For I2I, replace `example.png` in `LoadImage` with your actual input image.

### Model Load

Check that `unet_name`, `clip_name`, and `vae_name` point to the ANIMA base model files. SageAttention may require environment-specific package installation. If the install does not match your CUDA / PyTorch environment, keep it disabled while testing the base path.

### ANIMA Generation

This is the base sampling path. DCW, Spectrum, and Modulation Guidance patches may fail depending on the environment and model combination. If an error occurs, disable those switches first and verify the plain sampler path.

### HighRes

HighRes resamples the base result at a larger size. It is sensitive to resolution and VAE behavior, so enable it only after base generation is stable.

### Inpainting / Anima LLLite

Use `PreviewBridge` to edit the mask, then use the `Anima LLLite` model to guide the inpainting path. Mask editing and preview images may depend on current ComfyUI session state.

### Face / Eye Detailer

These are Impact Pack SEGS detailers. `guide_size`, `max_size`, `denoise`, `feather`, and `SEGS_crop_factor` strongly affect the result. The face and eye detailers use the same structure with different detail parameters.

### Upscale

Upscale runs the final image through the configured upscale model. It can fail if the model file is missing or VRAM is insufficient, so enable it after the save path is confirmed.

### Image Save

This section controls filename, output format, and metadata saving. Keeping metadata enabled is recommended so prompts and LoRA information can be checked later.

## Troubleshooting

- Disable optional optimization blocks first: Torch Compile, SageAttention, fp16 accumulation, DCW, Spectrum.
- Then disable HighRes, Inpainting, Detailer, and Upscale sections one by one and verify the base generation path.
- Check model filenames and folder locations.
- Restart ComfyUI after installing or updating custom nodes.
