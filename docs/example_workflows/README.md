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

## Artist Mix Example

- Workflow: [EasyUse_Anima_artist_mix_release_ko.json](EasyUse_Anima_artist_mix_release_ko.json)
- Preview: [EasyUse_Anima_artist_mix_release_ko.png](EasyUse_Anima_artist_mix_release_ko.png)
- Node guide: [Anima Artist Mix Conditioning](../nodes/anima-artist-mix-conditioning.ko.md)

This workflow shows the Advanced v2 prompt-data route: artist fields are stored
in `EASYUSE_ANIMA_PROMPT_DATA`, then `Anima Prompt Data Conditioning` applies an
artist mix mode before the sampler.
