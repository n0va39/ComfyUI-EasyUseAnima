# Anima AiO Workflow Management

This document is the operating guide for managing Anima AiO workflow files,
documentation, and Civitai release metadata.

## Current Release Set

| Purpose | Korean | English |
|---|---|---|
| Public workflow template | `example_workflows/Anima_AiO_v6.0_release_ko.json` | `example_workflows/Anima_AiO_v6.0_release_en.json` |
| Reference workflow copy | `docs/workflows/Anima_AiO_v6.0_release_ko.json` | `docs/workflows/Anima_AiO_v6.0_release_en.json` |
| Civitai model name | `Anima All in One workflow` | `Anima All in One workflow` |
| Civitai version | `v6.0_kr` | `v6.0_en` |
| Workflow metadata id | `anima-aio-v6.0-ko` | `anima-aio-v6.0-en` |

## Source of Truth

- The editable live workflow can be updated in ComfyUI first.
- For v6.0, the Korean live file is treated as the layout/source base:
  `D:\ComfyUI\ComfyUI_main\user\default\workflows\Anima_AiO_v6.0_release_ko.json`
- After manual edits, sync the release-suffixed live file into:
  `example_workflows/` and `docs/workflows/`.
- Build the English workflow from the final Korean workflow so node ids, links,
  layout, group bounds, and preset LoRA guide placement stay identical.

Do not overwrite unsuffixed or user-renamed workflow files. Only overwrite
release-suffixed files such as `_release_ko` and `_release_en`.

## Naming Rules

- GitHub / Registry workflow files use:
  - `Anima_AiO_v6.0_release_ko.json`
  - `Anima_AiO_v6.0_release_en.json`
- Civitai version labels use:
  - `v6.0_kr`
  - `v6.0_en`
- `Civitai Hash Fetcher (Image Saver)` must keep:
  - `username`: `N0VA39`
  - `model_name`: `Anima All in One workflow`
  - `version`: language-specific Civitai version

The Civitai model name is not a display title. Do not change it to `Anima AiO`
or language-specific titles.

## Documentation Files

- Readable user documentation lives in `docs/Anima AiO/`.
- User-facing entry point:
  `docs/Anima AiO/README.md`
- User-facing workflow guides:
  - `docs/Anima AiO/Anima_AiO_v6.0_KO.md`
  - `docs/Anima AiO/Anima_AiO_v6.0_EN.md`
- The root `README.md` should link to the user-facing workflow guide.
- Workflow JSON reference copies live in `docs/workflows/`.
- Civitai copy-paste notes for v6.0 live in:
  `docs/Anima AiO/Civitai_Release_Notes_v6.0.md`
- Civitai release notes are release-maintainer material and should not be linked
  from the user-facing workflow guide.
- This management guide lives in:
  `docs/Anima AiO/Workflow_Management.md`

## Workflow Content Rules

- Release workflow guide text should use `MarkdownNote` nodes.
- Each major section should have one guide node near the top of the group.
- Long repeated optimization explanations should appear once in the first
  relevant guide node, then later sections should reference that guide.
- Required model/download links may use a taller note node.
- Preset LoRA / Civitai links should stay in a separate note node.
- Do not store session-local preview state in release workflows:
  - temporary PreviewBridge image ids
  - rgthree comparison image URLs
  - clipspace references
  - local temp paths

## Version-Specific Rules for v6.0

- The `Preset LoRA / Civitai Links` node is part of the release layout and
  should keep the final manually adjusted position and size when generating EN.
- The Korean and English workflows should have matching node ids, link ids,
  group count, and release layout.
- Detailer subgraphs 1530 and 1836 should keep matching topology. Only detail
  parameters should differ.
- `SEGS_crop_factor` must be connected consistently in the detailer subgraphs.
- Civitai release uploads are separate versions of the same model:
  - Korean: `v6.0_kr`
  - English: `v6.0_en`

## Validation Checklist

Run these checks before committing or posting to Civitai.

```powershell
python -m json.tool example_workflows\Anima_AiO_v6.0_release_ko.json > $null
python -m json.tool example_workflows\Anima_AiO_v6.0_release_en.json > $null
git diff --check
```

Also verify:

- `example_workflows/` and `docs/workflows/` copies match for each language.
- Live ComfyUI workflow copies match the corresponding repo release file when
  they are intended to be updated.
- Link integrity check reports zero missing links.
- No release workflow contains `view?filename=`, `clipspace`, `data:image/`, or
  local temp paths.
- `Civitai Hash Fetcher (Image Saver)` fields match the table in this document.

## Release Procedure

1. Edit and test the Korean live release workflow in ComfyUI.
2. Copy the final Korean release workflow to `example_workflows/` and
   `docs/workflows/`.
3. Generate the English release workflow from the final Korean workflow.
4. Translate Markdown guide node text and user-facing group/title text.
5. Set Civitai Hash Fetcher version to `v6.0_kr` or `v6.0_en`.
6. Validate JSON syntax, link integrity, release hygiene, and SHA256 equality
   between synced copies.
7. Update `Civitai_Release_Notes_v6.0.md` when release-facing behavior changes.
8. Commit only intended workflow and documentation files.
