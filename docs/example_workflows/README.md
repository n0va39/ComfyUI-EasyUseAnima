# Example Workflows

This directory is the canonical location for maintained EasyUse Anima example
workflow assets.

## Policy

- Keep example workflow JSON files and their preview or source images together
  in this directory.
- Use meaningful release-style basenames, for example
  `EasyUse_Anima_regional_prompt_release_ko`.
- When a workflow is extracted from a saved PNG, save the extracted JSON next to
  the source PNG and give both files the same basename.
- Keep `extra.easyuse_anima_workflow` metadata current for maintained JSON
  samples.
- Do not keep a separate root-level `example_workflows/` directory.
- Do not use `docs/workflows/`.

## Files

- `Anima_AiO_v6.0_release_ko.json`
- `Anima_AiO_v6.0_release_en.json`
- `Anima_AiO_v6.0_release_ja.json`
- `Anima_AiO_v6.0_release_zh.json`
- `EasyUse_Anima_feature_test_release_ko.json`
- `EasyUse_Anima_feature_test_release_ko.png`
- `EasyUse_Anima_feature_test_release_ko.jpg`
- `EasyUse_Anima_feature_test_release_en.json`
- `EasyUse_Anima_feature_test_release_en.png`
- `EasyUse_Anima_feature_test_release_en.jpg`
- `EasyUse_Anima_regional_prompt_release_ko.json`
- `EasyUse_Anima_regional_prompt_release_ko.png`
- `EasyUse_Anima_artist_mix_release_ko.json`
- `EasyUse_Anima_artist_mix_release_ko.png`
- `EasyUse_Anima_AiO_generator_release_ko.json`
- `ANIMA_Easy_Use_workflow_v1_release_ko.json`

## ANIMA Easy Use Workflow v1

- Workflow: [ANIMA_Easy_Use_workflow_v1_release_ko.json](ANIMA_Easy_Use_workflow_v1_release_ko.json)
- Usage draft: [ANIMA Easy Use workflow v1](../Anima%20AiO/ANIMA_Easy_Use_workflow_v1_KO.md)
- Node guide: [Anima AiO Generator](../nodes/anima-aio-generator.ko.md)

This compact release workflow uses `Anima Prompt Studio Advanced v2`,
`Anima LoRA Preset`, `Easy Use Anima Input`, and `Anima AiO Generator`.
The workflow metadata lists required node packs under
`extra.easyuse_anima_workflow.required_node_packs`.

The default execution path uses split ANIMA model loading, LoRA Stack routing,
`spectrum_mod_guidance_advanced` sampling, Image Saver WebP output, embedded
workflow metadata, and the AiO node's preview feed.

## AiO Generator Example

- Workflow: [EasyUse_Anima_AiO_generator_release_ko.json](EasyUse_Anima_AiO_generator_release_ko.json)
- Node guide: [Anima AiO Generator](../nodes/anima-aio-generator.ko.md)

This workflow wires `Anima Prompt Studio Advanced v2` into `Easy Use Anima
Input`, then sends the dedicated context into `Anima AiO Generator`. The sample
uses the `spectrum_mod_guidance_advanced` sampler path and Image Saver metadata
embedding. Required node-pack information is stored in
`extra.easyuse_anima_workflow.required_node_packs`.

The AiO generator sample uses the 0.2.2 defaults: first-pass steps `32`,
sampler `er_sde`, scheduler `simple`, AuraFlow shift `3.0`, Highres scale
`1.5`, and Highres denoise `0.25`.

Required sample defaults are `ComfyUI-EasyUseAnima`,
`ComfyUI-Spectrum-KSampler`, and `ComfyUI-Image-Saver`. Optional features are
listed in the same metadata with `required_for_sample: false`, including
`ComfyUI-Anima-DAVE`, `ComfyUI-KJNodes`, and `ComfyUI-Impact-Pack`.

## Artist Mix Example

- Workflow: [EasyUse_Anima_artist_mix_release_ko.json](EasyUse_Anima_artist_mix_release_ko.json)
- Preview: [EasyUse_Anima_artist_mix_release_ko.png](EasyUse_Anima_artist_mix_release_ko.png)
- Node guide: [Anima Artist Mix Conditioning](../nodes/anima-artist-mix-conditioning.ko.md)

This workflow shows the Advanced v2 prompt-data route: artist fields are stored
in `EASYUSE_ANIMA_PROMPT_DATA`, then `Anima Prompt Data Conditioning` applies an
artist mix mode before the sampler.
