# Registry Scanner Safety

Use this checklist before publishing a Comfy Registry package version or
updating a release branch that will be scanned by Registry automation.

## Runtime Rules

- Do not use `eval`, `exec`, shell execution, runtime package installation, or
  obfuscation-like decode-and-load patterns in runtime files.
- Do not use `importlib.import_module` for optional integrations. Use explicit
  `try`/`except` imports for known ComfyUI or custom-node module paths.
- Keep optional external providers disabled by default. A provider that can call
  the network must require an explicit user setting.
- Do not auto-read API keys from environment variables for optional providers.
  Users should configure external providers intentionally.
- Network calls must have a timeout, must parse responses as data, and must not
  execute response text.
- Remote HTTP endpoints must be disabled by default or guarded by an explicit
  allow setting. Localhost-only defaults are preferred.

## EasyUse Anima Rules

- NAIA API calls default to `127.0.0.1`. Non-local hosts require
  `EasyUseAnima.NAIA.AllowRemoteAPI`.
- Prompt translation defaults to `off`. Google translation requires explicit
  provider selection and uses the optional `googletrans` dependency only.
- AiO SAM3 support must stay internal to AiO settings. Public standalone
  `Anima SAM3 Context` and `Anima SAM3 Detailer` nodes are not shipped.
- SAM3 and Impact Pack integrations must use explicit optional imports for known
  classes. Do not dynamically import user-provided module names.

## Archive Surface

`.comfyignore` should exclude non-runtime files before Registry publish:

- `docs/`
- `tests/`
- `.github/`
- development and maintenance documents
- workflow samples and generated assets
- videos, screenshots, preview images, HTML exports, and archives
- local/user-generated folders such as `workflow/`, `wildcards/`, `styles/`,
  `autocomplete/`, and development-only frontend builds
- local caches, virtual environments, logs, and temporary directories

Keep runtime Python files, `anima_prompt/`, `__easyuse_anima__/`, `web/`,
`locales/`, `requirements.txt`, `pyproject.toml`, `README*`, and `LICENSE`
available to the package.

Tests are required for repository and CI validation, but they are not required
in the Registry package archive unless a runtime self-test feature imports them.

Do not add a blanket `*.md` ignore unless the Registry ignore implementation is
verified to preserve `README.md`, `README.en.md`, and `README.ko.md`.

## Preflight Commands

Run from the repository root:

```powershell
rg -n "importlib\.import_module|__import__\(|eval\(|exec\(|os\.system|subprocess|pickle\.loads|marshal\.loads|base64\.b64decode|GOOGLE_TRANSLATION_API_KEY|os\.environ" nodes.py prompt_translation.py settings.py api.py __init__.py
rg -n "requests\.post" nodes.py prompt_translation.py settings.py api.py
rg -n "fetch\(|XMLHttpRequest|new Function|eval\(" web/js -g "!easyuse_anima_api.js"
git diff --check
python -m unittest discover -s tests
python -m compileall -q .
node --check web/js/easyuse_anima_settings.js
comfy node validate
```

Expected exception: `nodes.py` contains one NAIA `requests.post` call. It must
remain timeout-bound, localhost-only by default, and guarded by the explicit
remote API allow setting.
