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
- Do not deserialize model data with direct `torch.load`, pickle, marshal, or
  another executable object format. Route model resources through ComfyUI's
  inventoried loaders and their safe-loading contract.
- Validate a user-controlled output path after every supported template has
  been expanded. The resolved destination must remain below ComfyUI's active
  output directory before any saver or optional node is resolved.

## Request Side-Effect Boundary

- Every EasyUse Anima POST route parses its body through
  `easyuse_anima.api.requests.parse_json_object`.
- The shared parser requires `application/json`, a same-authority
  `Origin`/`Host` pair, and rejects a provided `Sec-Fetch-Site` value unless it
  is `same-origin` before parsing or dispatching work.
- GET handlers must not create, rename, or delete user-managed data. Startup
  bootstrap code owns default wildcard-directory creation; wildcard reads only
  resolve the configured paths.
- New side-effecting routes must inherit this boundary rather than parsing a
  request body directly.

## EasyUse Anima Rules

- NAIA API calls default to `127.0.0.1`. Non-local hosts require
  `EasyUseAnima.NAIA.AllowRemoteAPI`.
- Prompt translation defaults to `off`. Google translation requires explicit
  provider selection and uses the optional `googletrans` dependency only.
- AiO SAM3 support must stay internal to AiO settings. Public standalone
  `Anima SAM3 Context` and `Anima SAM3 Detailer` nodes are not shipped.
- SAM3 and Impact Pack integrations must use explicit optional imports for known
  classes. Do not dynamically import user-provided module names.
- AiO output templates are expanded inside EasyUse Anima and checked against
  the ComfyUI output root before either core `SaveImage` or the native output
  backend is called.
- Native Civitai enrichment is disabled by default. `Civitai data` is the
  explicit opt-in, and `easyuse_anima/aio/native_civitai.py` owns the only
  fixed-host GET boundary used by native image output. All fetcher and resource
  requests in one save share a 12-second deadline and a 16-call budget; budget
  exhaustion skips optional enrichment without failing image output.
- Native image metadata has explicit parameters, prompt, workflow,
  `extra_pnginfo`, depth/item/string, per-image, and per-save batch limits.
  Limit failures must occur before image publication and must not be replaced
  with unbounded fallback sidecars.
- AiO ResShift execution is fail-closed before optional-node lookup. Its saved
  settings remain readable, but re-enabling the adapter requires the safe
  loader contract tracked in issue #679.
- The native EasyUse output backend tracked in issue #678 owns format,
  workflow, metadata, and Civitai compatibility without calling the external
  Image Saver node pack.

## Archive Surface

`.comfyignore` should exclude non-runtime files before Registry publish:

- `docs/`
- `tests/`
- `.github/`
- development and maintenance documents
- workflow samples and generated assets
- videos, screenshots, preview images, HTML exports, and archives
- local/user-generated folders such as `workflow/`, `wildcards/`, `styles/`,
  root-only `/autocomplete/`, and development-only frontend builds
- local caches, virtual environments, logs, and temporary directories

Use the leading slash for `/autocomplete/`. A bare `autocomplete/` pattern also
matches `web/js/autocomplete/` in Comfy Registry packaging and can remove the
runtime controller modules while leaving unrelated tooltip metadata available.

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
rg -n "importlib\.import_module|__import__\(|eval\(|exec\(|os\.system|subprocess|pickle\.loads|marshal\.loads|base64\.b64decode|GOOGLE_TRANSLATION_API_KEY|os\.environ" __init__.py easyuse_anima -g "*.py"
rg -n "requests\.post" easyuse_anima/naia/client.py
rg -n "requests\.get" easyuse_anima/aio/native_civitai.py
rg -n "fetch\(|XMLHttpRequest|new Function|eval\(" web/js -g "!easyuse_anima_api.js"
git diff --check
python -m unittest discover -s tests
python -m compileall -q .
node --check web/js/easyuse_anima_settings.js
comfy node validate
```

Expected exception: `easyuse_anima/naia/client.py` contains one NAIA
`requests.post` call. It must remain timeout-bound, localhost-only by default,
and guarded by the explicit remote API allow setting.

Expected exception: `easyuse_anima/aio/native_civitai.py` contains one
`requests.get` call. It must remain fixed to the Civitai HTTPS API, disabled by
default behind `Civitai data`, redirect-disabled, timeout-bound, and size-bound.
It must also remain behind the per-save deadline/call budget and the bounded
process-wide draining-request slot.
