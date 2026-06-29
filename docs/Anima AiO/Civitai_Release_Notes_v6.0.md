# Anima AiO v6.0 Civitai Release Notes

This file keeps the copy-paste release notes for the Civitai uploads of the
Anima All in One workflow.

## Civitai Resource Mapping

Use the same Civitai model for both language variants.

| Language | Civitai model name | Civitai version | Workflow file |
|---|---|---|---|
| Korean | `Anima All in One workflow` | `v6.0_kr` | `Anima_AiO_v6.0_release_ko.json` |
| English | `Anima All in One workflow` | `v6.0_en` | `Anima_AiO_v6.0_release_en.json` |

The workflow metadata uses `Civitai Hash Fetcher (Image Saver)` with:

- `username`: `N0VA39`
- `model_name`: `Anima All in One workflow`
- `version`: `v6.0_kr` or `v6.0_en`

## Short Model Description Update

```markdown
ANIMA all in one workflow.

[English guide](https://civitai.red/articles/30996/anima-all-in-one-workflow-v5-guide)

[Korean guide](https://arca.live/b/aiart/171941799)

[NAIA2.0](https://github.com/DNT-LAB/NAIA2.0)

[Easy Use Anima custom node](https://github.com/n0va39/ComfyUI-EasyUseAnima)

[V5.5 Release](https://arca.live/b/aiart/174429584)

## V6.0 Release

v6.0 focuses on release cleanup, bilingual distribution, and easier workflow use.

There are two Civitai versions:

- Korean workflow: `v6.0_kr`
- English workflow: `v6.0_en`

Main updates:

- Added separate Korean and English release workflow files.
- Added section guide nodes directly inside the workflow.
- Added a dedicated preset LoRA / Civitai links guide node.
- Added Civitai metadata settings for `Anima All in One workflow` with `v6.0_kr` / `v6.0_en`.
- Cleaned up the AiO layout for release distribution.
- Matched the face and eye detailer subgraph structure.
- Fixed the missing `SEGS_crop_factor` connection in the detailer subgraph.
- Updated DCW, CWM, SMC, Spectrum, Mod Guidance, DAVE, SageAttention, and compile notes based on the original custom-node defaults/recommendations.
- Removed temporary preview / clipspace / local session state from the release workflows.

Note

v6.0 uses the Easy Use Anima custom node pack and several external custom nodes.

Some optional optimization nodes such as Torch Compile, SageAttention, fp16 accumulation, DCW, and Spectrum may depend on your GPU, CUDA, PyTorch, and installed package versions.

If you run into errors, first disable optional optimization blocks and test the base generation path.

For prompt metadata, LoRA information, and Civitai links, you can use an EXIF viewer such as:

[https://github.com/n0va39/ComfyUI-EXIF-viewer](https://github.com/n0va39/ComfyUI-EXIF-viewer)
```

## Release Checks

Before posting either version, confirm:

- `example_workflows/Anima_AiO_v6.0_release_ko.json` is the file uploaded as `v6.0_kr`.
- `example_workflows/Anima_AiO_v6.0_release_en.json` is the file uploaded as `v6.0_en`.
- `Civitai Hash Fetcher (Image Saver)` uses the exact model name `Anima All in One workflow`.
- The version field is `v6.0_kr` for Korean and `v6.0_en` for English.
- Image Saver metadata is preserved in sample images used for Civitai posts.
