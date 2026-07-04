# Issue 14 Frontend JS Maintenance Plan

## Scope

Issue #14 is accepted as a frontend maintainability improvement, not as an
immediate user-facing feature change. The safe implementation path is:

1. Split JavaScript helpers without changing runtime behavior.
2. Add stronger JS type checking with `// @ts-check` and JSDoc.
3. Consider a Vite/TypeScript build only after module boundaries are stable.

The current PR covers the first, low-risk part of that path by centralizing
shared frontend API helpers. It does not introduce a build system or convert the
runtime JavaScript to TypeScript.

## Current PR Plan

This PR keeps the existing ComfyUI `WEB_DIRECTORY` ES module loading model and
adds a shared helper module under `web/js/`.

Implemented scope:

- Add `web/js/easyuse_anima_api.js` as the shared frontend API helper module.
- Centralize JSON fetch handling, settings loading, JSON POST requests, prompt
  classification requests, and RFC3986 query encoding.
- Replace repeated `/easyuse_anima/settings` and
  `/easyuse_anima/classify_prompt` request code in feature scripts with the
  shared helper functions.
- Add source-level regression tests so direct settings/classify endpoint calls
  do not drift back into feature modules.

Touched frontend areas:

- Autocomplete settings loading.
- LoRA preset settings loading and profile API error handling.
- Prompt Studio settings loading and prompt classification.
- Prompt Studio common highlighting prompt classification.
- Settings UI long-text editor load/save helpers.

## Non-Goals For This PR

- No Python node behavior changes.
- No API endpoint rename or route behavior change.
- No ComfyUI node type, widget name, input socket name, or serialized workflow
  key changes.
- No Vite, TypeScript, npm, or pnpm dependency addition.
- No React/Vue-style frontend framework introduction.
- No large Prompt Studio file split in the same PR.
- No live ComfyUI instance sync.

## Compatibility Rules

Frontend structure work must preserve existing workflow compatibility.

- Entry files may keep ComfyUI registration side effects.
- Helper modules should export functions/constants and avoid
  `app.registerExtension()` or top-level ComfyUI hook registration.
- Existing serialized workflow keys must remain readable.
- Queue prompt payloads must keep the same field names and values.
- UI-only refactors must not change saved `widgets_values` or workflow
  `properties`.
- Frontend JS changes require a browser hard refresh for manual validation.

## Follow-Up Roadmap

### Phase 1: Shared Helpers

Status: current PR.

- Keep helper extraction small and behavior-preserving.
- Prefer shared modules for repeated request, settings, encoding, and parsing
  helpers.
- Add source guards for high-risk duplication points.

### Phase 2: Prompt Studio Module Boundaries

Split `easyuse_anima_prompt_studio.js` gradually after this PR is merged and
stable.

Suggested module layout:

```text
web/js/
  easyuse_anima_prompt_studio.js
  prompt_studio/
    constants.js
    schema.js
    state.js
    serialization.js
    node_hooks.js
    layout.js
    textarea.js
    wheel.js
    dom.js
    fields.js
    styles.js
    utils.js
```

Rules for that phase:

- Keep `easyuse_anima_prompt_studio.js` as the entry file.
- Move one responsibility at a time.
- Keep ComfyUI extension registration in the entry file.
- Avoid changing UI behavior while moving code.
- Validate workflow load/save after each meaningful extraction.

### Phase 3: JS Type Checking

After module boundaries are stable:

- Add `// @ts-check` to new or extracted helper modules.
- Add JSDoc typedefs for Prompt Studio field state, editor state, Comfy widgets,
  and node layout inputs.
- Add `jsconfig.json` or `tsconfig.json` with `allowJs`, `checkJs`, and
  `noEmit`.
- Keep runtime output as JavaScript.

### Phase 4: Optional Vite/TypeScript Build

Only consider this after phases 1-3 are stable.

Decision points:

- Whether built `dist` files are committed for ComfyUI Manager users.
- Whether contributors must run `pnpm build`.
- How to preserve ComfyUI frontend loading order.
- Whether typecheck/build commands become required validation before release.

## Prompt Studio Layout Invariants

Future Prompt Studio refactors must preserve these behavior rules:

- Node width resize changes editor width, not field schema.
- Node height resize changes editor viewport, not textarea field height.
- Textarea manual resize is the only manual `field.height` source.
- Auto textarea input may update height only while in auto height mode.
- Render/load must respect saved field height.
- Queue/serialize should collect current DOM values without rewriting field
  structure when the structure did not change.
- Wheel events over textarea, input, or select controls must not be forwarded to
  canvas panning.
- Resize/layout scheduling must guard against render-layout-resize loops.

## Validation Checklist

For the current PR:

- `Get-ChildItem -File web\js\*.js | ForEach-Object { node --check $_.FullName }`
- `.venv\Scripts\python.exe -m unittest tests.test_frontend_modules tests.test_frontend_lora_preset tests.test_aio_frontend`
- `.venv\Scripts\python.exe -m unittest discover -s tests`
- `.venv\Scripts\python.exe -m compileall -q .`
- `git diff --check`

For later Prompt Studio splitting:

- Start ComfyUI with no browser console module-loading errors.
- Create a new Prompt Studio node.
- Load an existing workflow with Prompt Studio nodes.
- Add, delete, move, and rename fields.
- Resize the node and textareas separately.
- Save, reload, queue, copy, and paste the node.
- Confirm serialized workflow data does not change from layout-only actions.

## References

- Issue #14: `https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/14`
- PBandDev ComfyUI TypeScript template:
  `https://github.com/PBandDev/comfyui-custom-node-template`
- ComfyUI frontend modernization announcement:
  `https://github.com/Comfy-Org/ComfyUI/issues/4169`
- ComfyUI React extension template:
  `https://github.com/Comfy-Org/ComfyUI-React-Extension-Template`
