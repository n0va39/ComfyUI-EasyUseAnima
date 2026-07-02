# ComfyUI EasyUse Anima

Language: [English](README.en.md) | [한국어](README.ko.md) | [Home](README.md)

ComfyUI custom nodes for prompt editing, ANIMA prompt correction, NAIA prompt
integration, LoRA preset management, wildcard expansion, and detailer helpers
for ANIMA/Spectrum workflows.

This package is independent from `comfyui-naia-bridge`. It does not import or
override that node pack, so both can be installed at the same time.

Reference baseline:

- `DNT-LAB/comfyui-naia-bridge` master `b82f98e`
- NAIA API endpoints used:
  - `POST /api/comfyui/random`
  - `peng_override` request field

## Documentation Entry Points

- Per-node details: [Node Guide](docs/nodes/README.en.md)
- Wildcard syntax and examples: [Wildcard Guide](docs/wildcards.en.md)
- Autocomplete CSV selection: [Autocomplete CSV Guide](docs/autocomplete-csv.en.md)
- Example workflows: [docs/example_workflows](docs/example_workflows/)
- Versioned changes: [RELEASE.md](RELEASE.md)

## Nodes

| Node | Category | Summary |
| --- | --- | --- |
| [Anima NAIA Random Prompt](docs/nodes/anima-naia-random-prompt.en.md) | `NAIA Bridge/API` | Requests prompt, negative prompt, and resolution from the NAIA remote API. |
| [Anima Prompt Corrector](docs/nodes/anima-prompt-corrector.en.md) | `EasyUse Anima/Prompt` | Normalizes comma-separated prompts into ANIMA order and returns a JSON report. |
| [Anima Prompt Builder](docs/nodes/anima-prompt-builder.en.md) | `EasyUse Anima/Prompt` | Combines prompt fields and separates AMG quality output. |
| [Anima Prompt Studio](docs/nodes/anima-prompt-studio.en.md) | `EasyUse Anima/Prompt` | Adds UI editing, autocomplete, and highlighting to Prompt Builder. |
| [Anima Prompt Studio Advanced](docs/nodes/anima-prompt-studio-advanced.en.md) | `EasyUse Anima/Prompt` | Provides positive/negative fields, NAIA, resolution, and wildcard controls. |
| [Anima Artist Mix Conditioning](docs/nodes/anima-artist-mix-conditioning.en.md) | `EasyUse Anima/Prompt` | Outputs artist mix positive CONDITIONING from a prompt and separate artist_tags input. |
| [Anima Wildcard](docs/nodes/anima-wildcard.en.md) | `EasyUse Anima/Prompt` | Expands wildcard text without Prompt Studio. |
| [Anima LoRA Preset](docs/nodes/anima-lora-preset.en.md) | `EasyUse Anima/LoRA` | Stores and outputs LoRA profiles, style prompts, and trigger words. |
| [Anima Detailer Align Hook](docs/nodes/anima-detailer-align-hook.en.md) | `EasyUse Anima/Detailer` | Aligns Impact detailer crop sampling sizes to a selected multiple. |
| [Anima SAM3 Context](docs/nodes/anima-sam3-context.en.md) | `EasyUse Anima/Detailer` | Loads a SAM3 checkpoint as an rgthree-compatible context. |
| [Anima SAM3 Detailer](docs/nodes/anima-sam3-detailer.en.md) | `EasyUse Anima/Detailer` | Connects SAM3 text detection, Impact MaskToSEGS, and DetailerForEach. |

## Shared Front-End Features

Autocomplete:

- Prompt Builder, Prompt Corrector, Prompt Studio, Prompt Studio Advanced, and
  generic multiline `STRING` prompt/text widgets can use the bundled Korean
  Danbooru autocomplete.
- The autocomplete scope can be selected in ComfyUI Settings with `off`,
  `easyuse_nodes`, or `compatible_global`.
- The CSV used for autocomplete and Prompt Studio highlighting can be selected
  in ComfyUI Settings -> `EasyUse Anima: Autocomplete CSV`.
- Typing `__` or `__partial` opens wildcard autocomplete and inserts
  `__relative/key__`.
- For source selection and CSV format details, see the
  [Autocomplete CSV Guide](docs/autocomplete-csv.en.md).

Prompt Studio highlighting:

- Quality, safety/rating, year, count, character, artist, copyright, metadata,
  learned general tags, natural language, syntax errors, and unknown tags use
  separate highlight classes.
- Wildcard syntax uses a separate color instead of normal tag colors, and the
  color can be changed in Settings.

ComfyUI Settings:

- NAIA request host, port, Prompt Engineering options, and preprocessing options
  are configured in the EasyUse Anima settings panel.
- EasyUse Anima does not store its own language setting. Node info, input/output
  hints, settings entries, custom DOM buttons, and tooltips follow the ComfyUI
  language setting.
- Prompt metadata filter words are applied only to metadata prompt outputs.
- Prompt Studio typo indicators and category/wildcard colors can be changed
  manually.
- Prompt Studio can auto-toggle general fields above the NAIA field.
- Wildcard extra paths use an add-item editor to register existing
  user-managed wildcard folders.
- LoRA Preset row labels can show file names only or full paths.

## Requirements

NAIA must expose the ComfyUI remote API used by `comfyui-naia-bridge`.

SAM3 detailer nodes require `ComfyUI-Impact-Pack` at runtime. This is a ComfyUI
custom-node dependency, not a Python package dependency, so it is not listed in
`pyproject.toml` Python dependencies.

Install Python dependency:

```bash
pip install -r requirements.txt
```

ComfyUI restart is required after installing or updating this node pack.

## Installation

Clone into `ComfyUI/custom_nodes`:

```bash
git clone https://github.com/n0va39/ComfyUI-EasyUseAnima
```

Then install dependencies in the ComfyUI Python environment:

```bash
pip install -r ComfyUI-EasyUseAnima/requirements.txt
```

Restart ComfyUI after installation.

Settings, LoRA preset profiles, and the default wildcard folder are stored in
the ComfyUI user data directory, not inside the custom node installation folder.
This keeps user data stable across Manager updates and git reinstalls.

## ComfyUI Manager / Registry

This repository includes `pyproject.toml` metadata for future Comfy Registry
registration. The Registry node id is `comfyui-easyuse-anima`.

Before publishing to the Registry, verify that `[tool.comfy].PublisherId` matches
the actual Comfy Registry publisher id.
