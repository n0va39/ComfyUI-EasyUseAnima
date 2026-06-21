# Maintaining ComfyUI EasyUse Anima

This repository is prepared for future ComfyUI Manager / Comfy Registry registration.

## Release Rules

- Keep `pyproject.toml` version in semantic version format: `X.Y.Z`.
- Patch version: bug fixes and documentation-only changes.
- Minor version: backward-compatible node inputs, UI, or behavior additions.
- Major version: breaking node class names, input names, output types, or workflow behavior.
- Once a version is published to Comfy Registry, do not rewrite that release. Publish a newer version instead.

## Registry Rules

- `pyproject.toml` `[project].name` is the Registry node id. Use the lowercase repository-style name: `comfyui-easyuse-anima`.
- `[tool.comfy].PublisherId` must match the Comfy Registry publisher id. It is currently set to `n0va39`.
- Comfy Registry display name for the publisher is `N0VA`; this is informational. The publish identity is the publisher id `n0va39`.
- Keep `[project.urls].Repository` pointed at the public GitHub repository.
- Keep install dependencies in `pyproject.toml` and `requirements.txt`; do not install packages at runtime.
- Use `.comfyignore` for files that should stay in git but not ship in the Registry archive.
- Reference: https://docs.comfy.org/registry/publishing

## Compatibility Rules

- Do not rely on the installed folder name for imports.
- Keep node class ids stable unless a breaking release is intended.
- Do not conflict with `comfyui-naia-bridge` class ids or display names.
- Keep this node pack usable with or without `comfyui-naia-bridge` installed.

## Security Rules

- Do not use `eval` or `exec`.
- Do not add obfuscated code.
- Do not run arbitrary shell commands from node execution.
- Do not store API keys, tokens, or personal data in the repository.

## Checks

Run from `D:\ComfyUI\custom_nodes_workplace`:

```powershell
powershell -ExecutionPolicy Bypass -File tools\check_custom_node.ps1 -Project ComfyUI-EasyUseAnima
```

Before publishing, also test installation in the active ComfyUI instance:

```text
D:\ComfyUI\ComfyUI_main\instances\ComfyUI_v0.24.0\custom_nodes
```

## Comfy Registry Release Procedure

Use this procedure when publishing a release to Comfy Registry / ComfyUI Manager.

### 1. Prepare Metadata

- Confirm `pyproject.toml` has:
  - `[project].name = "comfyui-easyuse-anima"`
  - `[project].version = "X.Y.Z"` with semantic versioning.
  - `[project.urls].Repository = "https://github.com/n0va39/ComfyUI-EasyUseAnima"`
  - `[tool.comfy].PublisherId = "n0va39"`
  - `[tool.comfy].DisplayName = "ComfyUI EasyUse Anima"`
- If a version was already published, never reuse it. Bump to a new version.
- Keep `LICENSE`, `README.md`, `README.en.md`, and `README.ko.md` current.
- Keep `.comfyignore` committed so Registry archives exclude development-only files consistently.

### 2. Prepare Registry API Key

- Create the key from the Comfy Registry publisher page for publisher `n0va39`.
- Recommended key name: `ComfyUI-EasyUseAnima publish`.
- Recommended description: `Publish n0va39/ComfyUI-EasyUseAnima to Comfy Registry`.
- Do not commit the key or write it into local project files.
- For GitHub Actions, store it as repository secret `REGISTRY_ACCESS_TOKEN`.

### 3. Validate Before Publishing

Run from repository root:

```powershell
node --check web\js\easyuse_anima_settings.js
node --check web\js\easyuse_anima_prompt_studio.js
node --check web\js\easyuse_anima_lora_preset.js
node --check web\js\easyuse_anima_naia.js
node --check web\js\easyuse_anima_autocomplete.js
.venv\Scripts\python.exe -m unittest discover -s tests
git diff --check
git status --short
```

Also verify ComfyUI starts with the active test instance after copying changed files:

```text
D:\ComfyUI\ComfyUI_main\instances\ComfyUI_v0.24.0\custom_nodes\ComfyUI-EasyUseAnima
```

### 4. Manual Publish With Comfy CLI

Install or update Comfy CLI if needed, then run from repository root:

```powershell
comfy node publish
```

When prompted for `API Key for publisher 'n0va39'`, paste the Comfy Registry API key.
On Windows, prefer right-click paste. The official docs note that `Ctrl+V` can append an extra hidden character in some terminals.

### 5. GitHub Actions Publish Option

Use this only after adding repository secret `REGISTRY_ACCESS_TOKEN`.

This repository keeps `.github/workflows/publish_action.yml` as a manual-only
workflow to avoid accidental Registry publishing while release metadata is being
edited. Trigger it from GitHub Actions with `workflow_dispatch`.

The checked-in workflow is:

```yaml
name: Publish to Comfy registry

on:
  workflow_dispatch:

jobs:
  publish-node:
    name: Publish Custom Node to registry
    runs-on: ubuntu-latest
    steps:
      - name: Check out code
        uses: actions/checkout@v4
      - name: Publish Custom Node
        uses: Comfy-Org/publish-node-action@main
        with:
          personal_access_token: ${{ secrets.REGISTRY_ACCESS_TOKEN }}
```

If automatic publishing is wanted later, add a guarded `push` trigger for
`pyproject.toml` version changes after the release process is stable.

### 6. After Publishing

- Confirm the Registry page for publisher `n0va39` shows the new version.
- Confirm install through ComfyUI Manager / Registry.
- Create and push a matching Git tag, for example `v0.1.1`, unless the tag was already created before publishing.
- Do not rewrite the tag after public release. Use a new patch version for fixes.
