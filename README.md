# ComfyUI EasyUse Anima

Prompt editing, ANIMA prompt correction, NAIA prompt integration, LoRA preset
management, wildcard expansion, AiO generation, and detailer helpers for ANIMA/Spectrum
workflows in ComfyUI.

## Language / 언어

- [한국어 문서](README.ko.md)
- [English documentation](README.en.md)

## Anima AiO Workflow

- [Korean README quick guide](README.ko.md#빠른-가이드-anima-aio-생성-흐름)
- [English README quick guide](README.en.md#quick-guide-anima-aio-generation)
- [Anima AiO Generator node guide](docs/nodes/anima-aio-generator.en.md)
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
3. Run first pass, Highres, Detailer, preview, and saving through Anima AiO Generator.

Detailed node documentation is kept under [docs/nodes](docs/nodes/README.en.md).
Wildcard syntax is documented in [docs/wildcards.en.md](docs/wildcards.en.md)
and [docs/wildcards.ko.md](docs/wildcards.ko.md). Release notes are kept in
[RELEASE.md](RELEASE.md).
