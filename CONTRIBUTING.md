# Contributing

Language: [English](CONTRIBUTING.md) | [한국어](CONTRIBUTING.ko.md)

Thanks for helping improve ComfyUI EasyUse Anima. This project is a ComfyUI
custom node pack, so contributions should preserve existing workflows, saved
settings, and user data whenever possible.

Before participating, read the [Code of Conduct](CODE_OF_CONDUCT.md).

## Language / 언어

Issues, discussions, and pull request descriptions may be written in English or
Korean. If Korean is more comfortable for explaining a bug, feature request, or
contribution, please use Korean. This is optional; English contributions are
also welcome.

한국어가 더 편하다면 이슈, 토론, PR 설명을 한국어로 작성해도 됩니다.
한국어 사용은 선택 사항이며, 영어 기여도 환영합니다.

## Project Scope

This repository focuses on:

- Prompt editing and correction for ANIMA/Spectrum workflows.
- NAIA prompt import and reusable prompt metadata.
- Wildcard expansion and autocomplete behavior.
- LoRA preset management.
- AiO generation helpers and detailer convenience nodes.
- Public example workflows and node documentation.

Large unrelated framework changes, runtime package installation from node
execution, obfuscated code, or features that require storing private user data
are out of scope.

## Reporting Issues

Before opening an issue, check the README, existing issues, and recent release
notes. A good bug report should include:

- The EasyUse Anima version, commit, or installation source.
- The ComfyUI version or Manager install mode.
- Operating system and Python version when relevant.
- Required custom nodes involved in the workflow.
- Clear steps to reproduce the problem.
- Expected behavior and actual behavior.
- ComfyUI console logs or browser errors, trimmed to the relevant lines.
- A minimal workflow JSON or screenshot when it helps reproduce the issue.

Do not post API keys, tokens, private paths, private model sources, or personal
data. If logs contain secrets, remove them before posting.

For security vulnerabilities, follow the [Security Policy](SECURITY.md) instead
of posting public exploit details.

## Requesting Features

Feature requests are easier to evaluate when they describe:

- The workflow problem being solved.
- The node or UI surface affected.
- How the feature should behave in a saved and reloaded workflow.
- Whether it changes existing node inputs, outputs, metadata, or settings.
- Any related custom nodes or upstream ComfyUI behavior.

If a feature affects existing workflows, explain the compatibility expectation.
Backward-compatible changes are strongly preferred.

## Pull Requests

Use `dev` as the base branch for normal development pull requests. `main` is the
stable user/install branch.

For PRs:

- Keep the change focused.
- Preserve existing node class ids, input names, output types, and workflow
  serialization unless a breaking change is intentional and discussed first.
- Add or update tests for behavior changes.
- Update user-facing docs when UI, node behavior, workflow templates, or settings
  change.
- Include before/after behavior in the PR description.
- List the validation commands you ran.
- Call out anything not tested.

Avoid mixing unrelated refactors, formatting-only edits, and behavior changes in
one PR.

## Local Setup

Clone the repository into a ComfyUI custom node directory for manual testing:

```bash
cd ComfyUI/custom_nodes
git clone https://github.com/n0va39/ComfyUI-EasyUseAnima
cd ComfyUI-EasyUseAnima
```

Install dependencies in the same Python environment used by ComfyUI:

```bash
pip install -r requirements.txt
```

Restart ComfyUI after installing, updating, or changing Python files. For
frontend JavaScript changes, a browser hard refresh may also be required.

## Validation

Run focused checks for the files you changed. From the repository root:

```bash
python -m unittest discover -s tests
python -m compileall -q .
git diff --check
```

For changed frontend JavaScript files:

```bash
node --check web/js/<changed-file>.js
```

For changed workflow templates:

```bash
python -m unittest tests.test_workflows
```

If a change depends on live ComfyUI behavior, also test it in a real ComfyUI
instance and mention the tested ComfyUI version in the PR.

## Coding Guidelines

- Keep changes scoped to the node, setting, route, or UI behavior being fixed.
- Prefer existing helpers and patterns in this repository.
- Keep Python node definitions stable and explicit: `INPUT_TYPES`,
  `RETURN_TYPES`, `RETURN_NAMES`, `FUNCTION`, and `CATEGORY`.
- Do not use Python `hash()` for persistent cache keys or saved workflow data.
- Do not run shell commands from node execution.
- Do not add dependencies unless they are necessary and documented in both
  `pyproject.toml` and `requirements.txt`.
- Keep user data outside the repository. Settings, LoRA profiles, and wildcards
  should remain in ComfyUI user data paths.

## Frontend Guidelines

- Put ComfyUI frontend extensions under `web/js/`.
- Keep hidden widgets serialized when Python inputs still require their values.
- Update workflow serialization explicitly. DOM state alone is not enough.
- Avoid repeated API polling from input, mousemove, render, or layout loops.
- Use ComfyUI frontend APIs where practical.
- Verify saved workflow reload behavior when changing custom DOM widgets.

## Documentation and Workflows

- User-facing node docs live under `docs/nodes/`.
- Public example workflow files and preview/source images live under
  `docs/example_workflows/`.
- Release workflow filenames should stay language release-suffixed, such as
  `*_release_en.json`, `*_release_ko.json`, `*_release_ja.json`, or
  `*_release_zh.json`.
- Do not commit personal test workflows, local LoRA paths, temporary preview
  URLs, clipspace images, or private model paths.
- Keep workflow metadata under `extra.easyuse_anima_workflow` current when
  updating release workflow templates.

## Localization

Standard node localization should use ComfyUI locale files under
`locales/<lang>/nodeDefs.json`. Keep English fallback text in Python node
definitions. Use frontend text maps only for custom DOM widgets, menus, alerts,
prompts, and settings panels that ComfyUI locale files cannot cover.

When changing locale files, validate the JSON:

```bash
python -m json.tool locales/ko/nodeDefs.json
```

Adjust the path for the language you changed.

## Maintainer-Only Work

Release publishing, Comfy Registry publishing, version tagging, and changes to
published release history are maintainer tasks. Do not include API keys,
publisher tokens, or release secrets in issues, PRs, docs, workflow files, or
test data.
