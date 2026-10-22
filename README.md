# ComfyUI EasyUse Anima

> **1.8.0-beta.1 — TEST / 테스트 버전.** Requires the paired Spectrum fork with
> MOSS and Krea2 model patches. Use the exact downloads and installation steps
> in the [test release](https://github.com/n0va39/ComfyUI-EasyUseAnima/releases/tag/v1.8.0.dev1).
> RAW checkpoint quality/performance remains unverified. This is a Registry beta.
> Betas may appear as latest; current ComfyUI-Manager versions may fail to recognize this beta version.

Prompt editing, ANIMA prompt correction, NAIA prompt integration, LoRA presets,
wildcards, model-specific AiO generation for Anima, MOSS and Krea2, and
ANIMA/Spectrum workflow helpers for ComfyUI.

## License

ComfyUI EasyUse Anima is licensed under **GPL-3.0-or-later**.
See [LICENSE](LICENSE) for the full terms and [NOTICE](NOTICE) for the license
grant and third-party notices. Previously MIT-licensed code remains available
under its original terms; its notice is preserved in [LICENSE-MIT](LICENSE-MIT).
Separately installed models and node packs retain their own licenses.

## Language / 언어

- [한국어 문서](README.ko.md)
- [English documentation](README.en.md)
- [Local and authenticated remote API access](docs/api-access.md)

## Anima AiO Workflow

- [Korean README quick guide](README.ko.md#빠른-가이드-anima-aio-생성-흐름)
- [English README quick guide](README.en.md#quick-guide-anima-aio-generation)
- [Easy Anima Safe PAG](docs/nodes/easy-anima-safe-pag.en.md)
- [AiO Generator (Anima) node guide](docs/nodes/anima-aio-generator.en.md)
- [ANIMA Easy Use workflow v1 guide](docs/Anima%20AiO/ANIMA_Easy_Use_workflow_v1_KO.md)
- [ANIMA Easy Use workflow v1 JSON](docs/example_workflows/ANIMA_Easy_Use_workflow_v1_release_ko.json)
- [Workflow guide](docs/Anima%20AiO/README.md)
- [Korean v6.0 guide](docs/Anima%20AiO/Anima_AiO_v6.0_KO.md)
- [English v6.0 guide](docs/Anima%20AiO/Anima_AiO_v6.0_EN.md)
- [Example workflows](docs/example_workflows/)

## Summary

EasyUse Anima is a ComfyUI node pack for building ANIMA workflows with less
repeated wiring. It groups prompt editing, Korean autocomplete, prompt
correction, NAIA prompt import, wildcard expansion, LoRA presets, AiO
generation, image-size helpers, and detailer helpers into one package.

The main workflow is:

1. Write and normalize prompts in Prompt Studio.
2. Bundle prompt data, ANIMA model, VAE, and CLIP with Easy Use Anima Input.
3. Run first pass, Highres, Detailer, preview, and saving through AiO Generator (Anima).

Separate `AiO Generator (MOSS)` and `AiO Generator (Krea2)` nodes share the Input,
seed and saving architecture, including compatible Highres, Detailer, Upscale,
Artist Mix and KJ options. Spectrum forecasting uses the optional model-specific
Spectrum MODEL patches when their capability contracts are available.
See the [model-specific guide](docs/nodes/anima-aio-generator.en.md)
for optional dependencies and unsupported model patches.

## Demo Videos

### Autocomplete

<video src="https://github.com/n0va39/ComfyUI-EasyUseAnima/raw/main/docs/assets/videos/easyuse-anima-autocomplete.mp4" controls muted loop playsinline width="720"></video>

[Open autocomplete demo](docs/assets/videos/easyuse-anima-autocomplete.mp4)

### NAIA Prompt Fill

<video src="https://github.com/n0va39/ComfyUI-EasyUseAnima/raw/main/docs/assets/videos/easyuse-anima-naia-fill.mp4" controls muted loop playsinline width="720"></video>

[Open NAIA demo](docs/assets/videos/easyuse-anima-naia-fill.mp4)

### Wildcard Autocomplete

<video src="https://github.com/n0va39/ComfyUI-EasyUseAnima/raw/main/docs/assets/videos/easyuse-anima-wildcard-autocomplete.mp4" controls muted loop playsinline width="720"></video>

[Open wildcard demo](docs/assets/videos/easyuse-anima-wildcard-autocomplete.mp4)

Detailed node documentation is kept under [docs/nodes](docs/nodes/README.en.md).
Wildcard syntax is documented in [docs/wildcards.en.md](docs/wildcards.en.md)
and [docs/wildcards.ko.md](docs/wildcards.ko.md). Release notes are kept in
[RELEASE.md](RELEASE.md).
