# Maintaining ComfyUI EasyUse Anima

This repository is prepared for future ComfyUI Manager / Comfy Registry registration.

## Release Rules

- Keep `pyproject.toml` version in semantic version format: `X.Y.Z`.
- Patch version: bug fixes and documentation-only changes.
- Minor version: backward-compatible node inputs, UI, or behavior additions.
- Major version: breaking node class names, input names, output types, or workflow behavior.
- Once a version is published to Comfy Registry, do not rewrite that release. Publish a newer version instead.

## Branch Rules

- Keep `main` as the stable user/install branch.
- Do regular development, UI experiments, Node 2.0 compatibility work, and compatibility investigations on `dev` or short-lived `feature/*` branches.
- Merge into `main` only after local tests, custom-node checks, and at least one ComfyUI instance validation pass.
- Create release tags only from `main` commits. Do not tag `dev`.
- If `main` breaks after release, fix from a short-lived `hotfix/*` branch, merge into `main`, bump the patch version, and create a new tag.
- Treat ComfyUI Manager nightly/latest installs as `main` consumers, so do not push unvalidated development work directly to `main`.

## Registry Rules

- `pyproject.toml` `[project].name` is the Registry node id. Use the lowercase repository-style name: `comfyui-easyuse-anima`.
- Write each new Registry changelog for installing users: lead with the outcome
  and include only user-visible changes and required actions in plain text.
  Keep PRs, commits, internal file/module work, test bookkeeping, scanner
  findings, and release mechanics in maintainer notes instead.
- `[tool.comfy].PublisherId` must match the Comfy Registry publisher id. It is currently set to `n0va39`.
- Comfy Registry display name for the publisher is `N0VA`; this is informational. The publish identity is the publisher id `n0va39`.
- Keep `[project.urls].Repository` pointed at the public GitHub repository.
- Keep install dependencies in `pyproject.toml` and `requirements.txt`; do not install packages at runtime.
- Use `.comfyignore` for files that should stay in git but not ship in the Registry archive.
- Reference: https://docs.comfy.org/registry/publishing

## Workflow File Rules

- Store user-facing Registry workflow templates and preview/source images under
  `docs/example_workflows/`.
- Use `docs/development/README.md` as the development-document entry point before changing workflow or release-template policy.
- Keep workflow filenames release-suffixed so they do not collide with user-edited local workflow names:
  - Korean release files: `*_release_ko.json`
  - English release files: `*_release_en.json`
- Do not commit bare working names such as `Anima_AiO_v6.0.json` for release workflows.
- Do not keep duplicate workflow JSON outside `docs/example_workflows/`; keep implementation notes or node ids in development docs instead.
- When syncing to a live ComfyUI user workflow folder, copy from the release-suffixed repository file and keep the same basename. Overwrite only release-suffixed copies; never overwrite unsuffixed or user-named working files.
- Keep `extra.easyuse_anima_workflow` metadata in release workflows current, including `workflow_id`, `language`, `kind`, `release_filename`, and `release_suffix`.
- Before publishing or syncing, validate workflow JSON syntax, link integrity, and absence of local-only LoRA paths, temporary preview URLs, clipspace image references, or personal test filenames.

## Compatibility Rules

- Do not rely on the installed folder name for imports.
- Keep node class ids stable unless a breaking release is intended.
- Do not conflict with `comfyui-naia-bridge` class ids or display names.
- Keep this node pack usable with or without `comfyui-naia-bridge` installed.
- Test compatibility issues against both the active ComfyUI instance and an unused older instance when available.
- When using Comfy CLI for compatibility checks, install into an unused instance and verify the installed git commit, `pyproject.toml` version, and Manager cache behavior separately.
- Do not dereference `server.PromptServer.instance` at module import time without a guard. Some ComfyUI, Manager, or validation import paths can import custom nodes before `PromptServer.instance` exists.
- If ComfyUI Manager reports a nightly/latest install, confirm the actual installed commit with `git rev-parse HEAD`; Registry versions and Manager nightly installs can point to different refs.

## Security Rules

- Do not use `eval` or `exec`.
- Do not add obfuscated code.
- Do not run arbitrary shell commands from node execution.
- Do not store API keys, tokens, or personal data in the repository.

## Checks

Run the checked-in validation entrypoint from the repository root:

```powershell
powershell -ExecutionPolicy Bypass -File tools\check_project.ps1 -Profile full
```

Use `-Profile quick` for Python compile, frontend, and diff checks. The `full`
profile additionally runs the complete Python suite. Pass
`-Python <path-to-python>` when the ComfyUI environment is not the default
`python` command.

The checked-in Python suite is based on `unittest`. Do not substitute
`python -m pytest tests -q`: with this custom-node package layout, pytest tries
to import the repository-root `__init__.py` as a top-level module and fails
before test bodies run. Supporting pytest would require a separate package and
runner design change.

Before publishing, also install and test the node pack in a supported ComfyUI
instance. Record the tested ComfyUI and frontend versions instead of relying on
a fixed local instance path.

## Comfy Registry Release Procedure

Use this procedure when publishing a release to Comfy Registry / ComfyUI Manager.

### 1. Prepare Metadata

- Confirm `pyproject.toml` has:
  - `[project].name = "comfyui-easyuse-anima"`
  - `[project].version = "X.Y.Z"` with semantic versioning.
  - `[project].description` matches the intended Comfy Registry summary.
  - `[project.urls].Repository = "https://github.com/n0va39/ComfyUI-EasyUseAnima"`
  - `[tool.comfy].PublisherId = "n0va39"`
  - `[tool.comfy].DisplayName = "ComfyUI EasyUse Anima"`
- If a version was already published, never reuse it. Bump to a new version.
- Confirm the current package version has a `changelog_file`, that the file
  exists, and that its copy follows the user-facing plain-text rule above.
- Keep the top summary in `README.md`, `README.en.md`, and `README.ko.md`
  aligned with `[project].description`.
- Keep the GitHub repository description aligned with `[project].description`
  before publishing, because external listing pages may display either source.
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
powershell -ExecutionPolicy Bypass -File tools\check_project.ps1 -Profile full
comfy node validate
```

Also verify ComfyUI starts with the intended test installation after applying
the candidate changes.

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

The checked-in workflow accepts a required `mode`, an optional `version`, and
a `dry_run` switch used by metadata mode. Its release-relevant shape is shown
below; `.github/workflows/publish_action.yml` remains the executable source of
truth:

```yaml
name: Publish to Comfy registry

on:
  workflow_dispatch:
    inputs:
      mode:
        type: choice
        options: [publish, metadata]
      version:
        required: false
      dry_run:
        type: choice
        options: [true, false]

jobs:
  publish-node:
    name: Publish Custom Node to registry
    runs-on: ubuntu-latest
    steps:
      - name: Check out code
        uses: actions/checkout@v4
      - name: Install uv
        if: ${{ inputs.mode == 'publish' }}
        uses: astral-sh/setup-uv@v5
      - name: Extract Registry changelog
        if: ${{ inputs.mode == 'publish' }}
        run: |
          python .github/scripts/extract_release_changelog.py \
            --version "${{ inputs.version }}" \
            --output "$RUNNER_TEMP/comfy-node-changelog.md"
      - name: Validate node package
        if: ${{ inputs.mode == 'publish' }}
        run: |
          uvx --from comfy-cli comfy --skip-prompt node validate
      - name: Publish Custom Node
        if: ${{ inputs.mode == 'publish' }}
        env:
          REGISTRY_ACCESS_TOKEN: ${{ secrets.REGISTRY_ACCESS_TOKEN }}
        run: |
          uvx --from comfy-cli comfy --skip-prompt node publish \
            --token "$REGISTRY_ACCESS_TOKEN" \
            --changelog-file "$RUNNER_TEMP/comfy-node-changelog.md"
      - name: Sync existing metadata
        if: ${{ inputs.mode == 'metadata' }}
        env:
          REGISTRY_ACCESS_TOKEN: ${{ secrets.REGISTRY_ACCESS_TOKEN }}
        run: |
          python .github/scripts/sync_comfy_registry_metadata.py \
            --dry-run "${{ inputs.dry_run }}"
```

For a new version, merge the validated release metadata to protected `main`,
create and read back the matching immutable annotated tag, then dispatch
`publish_action.yml` from `main` with `mode=publish` and the exact version.
After Registry read-back, dispatch `registry_metadata.yml` with
`dry_run=false`, then run a final local metadata dry-run and verify that it is a
no-op. Do not add an automatic push trigger without a separately reviewed
release-policy change.

### 6. After Publishing

- Confirm the Registry page for publisher `n0va39` shows the new version.
- Confirm install through ComfyUI Manager / Registry.
- Confirm the already-pushed annotated tag resolves to the released `main`
  commit. Tag creation is a pre-publish gate, not a post-publish repair step.
- Download the Registry `node.zip` and compare every packaged file with the
  tagged Git blobs. Also download the GitHub manual-install asset and verify its
  recorded SHA256 and top-level custom-node folder.
- Copy a public SHA256 only from the freshly built artifact or the live asset
  digest. Do not expand a shortened value from a handoff, log, or summary; after
  editing release copy, read it back and compare the complete value with the
  live asset.
- Do not rewrite the tag after public release. Use a new patch version for fixes.
