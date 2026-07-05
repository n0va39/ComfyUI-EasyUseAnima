# Issue 14 Frontend JS Maintenance Plan

## Position

Issue #14 is accepted as a frontend maintainability track. It should not be
closed until this PR is reviewed, merged, and any remaining follow-up items are
confirmed.

The active PR is:

```text
Issue #14 Phase 1-4 frontend maintainability work
```

The active PR centralizes shared frontend API helpers, splits Prompt Studio
JavaScript responsibilities into tested modules, adds a no-build JS typecheck
gate, documents the no-build Vite/TypeScript decision, and records v0.24.0
workflow/load/queue smoke evidence.

## Close Criteria

Issue #14 can be closed only after these conditions are satisfied:

- Repeated frontend API request code is centralized in shared helpers.
- Large Prompt Studio JavaScript responsibilities are split into modules.
- ComfyUI extension registration side effects remain in entry files only.
- Workflow serialize/load compatibility is verified.
- Newly split modules use `// @ts-check` and JSDoc typedefs where practical.
- Source guards or type checks catch key regression patterns.
- A live ComfyUI hard-refresh smoke test is completed.
- The Vite/TypeScript adoption gate is documented, whether adopted or deferred.

## Operating Rule

Put only one kind of risk in each PR.

- API helper PRs should only carry shared helper extraction risk.
- Prompt Studio split PRs should only carry import/export movement risk.
- Layout or textarea behavior PRs should only carry resize behavior risk.
- Type-check PRs should only carry typing and annotation risk.
- Vite/TypeScript PRs should only carry build and distribution risk.

## Phase 0: Documentation And Tracking

### Goal

Make the Issue #14 scope, phases, non-goals, and validation rules easy to find
before future frontend refactors start.

### Tasks

- Link this file from `docs/development/README.md`.
- Keep the current PR scope and non-goals visible in the PR body.
- Keep Issue #14 open after Phase 1 unless the close criteria are all met.
- Track follow-up work in Issue #14 or follow-up PRs.

### Required Notes

- This work is maintainability work, not a user-facing feature.
- The active PR records each frontend module split in tested commits.
- Prompt Studio entry-file slim-down is follow-up work until the entry is only
  registration and orchestration code.
- TypeScript/Vite is not introduced in the current PR.
- Workflow compatibility must be preserved.
- Frontend JS changes require a browser hard refresh for manual validation.
- PRs must state whether live ComfyUI smoke testing was performed.

### Acceptance Criteria

- `docs/development/README.md` links to this plan.
- PR body separates scope, non-goals, validation, and smoke-test status.
- Issue #14 is not closed by Phase 1.

## Phase 1: Shared Frontend API Helpers

Status: completed in the active PR.

### Goal

Centralize repeated frontend request helpers while preserving runtime behavior.

### Current PR Scope

- Add `web/js/easyuse_anima_api.js`.
- Provide shared JSON fetch handling.
- Provide shared JSON POST handling.
- Provide shared settings loading.
- Provide shared `classify_prompt` request handling.
- Provide shared RFC3986 query encoding.
- Update autocomplete settings loading to use the shared helper.
- Update LoRA preset settings and profile API calls to use the shared helper.
- Update Prompt Studio settings and classification calls to use the shared
  helper.
- Update Prompt Studio common highlight classification to use the shared helper.
- Update settings UI long-text editor load/save calls to use the shared helper.
- Add source-level guards against reintroducing direct settings/classify fetch
  calls in feature scripts.

### Non-Goals

- Do not split `easyuse_anima_prompt_studio.js` in this PR.
- Do not add Vite, TypeScript, npm, or pnpm dependencies.
- Do not change Python node behavior.
- Do not rename API routes.
- Do not change node type, widget name, input socket name, output socket name,
  serialized property key, or `widgets_values` order.
- Do not make UI behavior changes.
- Do not make broad CSS structure changes.
- Do not sync to a live ComfyUI instance in this PR.

### API Helper Checklist

- Helper names should describe the operation.
- Feature modules should not need to duplicate shared endpoint details.
- HTTP failure, JSON parse failure, empty response, and malformed response
  fallback behavior should be consistent.
- Settings load fallback must be explicit for each caller.
- `classify_prompt` failure must degrade the highlight/classification feature
  without breaking the whole UI.
- The helper module must not depend on `app.registerExtension()`.
- The helper module must not perform top-level `fetch`.
- The helper module must not mutate DOM at import time.
- Console warning/error prefixes should stay consistent, for example
  `[EasyUseAnima]`.
- Existing async timing should not change unless the PR says so explicitly.

### Source Guard Checklist

- Feature modules should not call `fetch("/easyuse_anima/settings")` directly.
- Feature modules should not call `fetch("/easyuse_anima/classify_prompt")`
  directly.
- Endpoint request body shape for classification should be owned by the helper.
- Duplicate RFC3986 query encoding helpers should not be reintroduced.
- Shared settings/classify request ownership should stay limited to the helper
  module and tests.

### Merge Gate

- `Get-ChildItem -File web\js\*.js | ForEach-Object { node --check $_.FullName }`
- `.venv\Scripts\python.exe -m unittest tests.test_frontend_modules tests.test_frontend_lora_preset tests.test_aio_frontend`
- `.venv\Scripts\python.exe -m unittest discover -s tests`
- `.venv\Scripts\python.exe -m compileall -q .`
- `git diff --check`
- PR body states live ComfyUI smoke-test status.
- Issue #14 remains open after merge.

### Test Cost Policy

Use focused checks for each small module split:

- `node --check` for the changed entry/module files.
- All frontend JS syntax checks when imports change.
- Related frontend structure tests, primarily `tests.test_frontend_modules`.
- `git diff --check`.

Run full unittest, compileall, and live/browser smoke only at major checkpoints
or before final PR readiness. If sandbox Temp/cache permissions obscure the
test signal, rerun the affected major checkpoint with the agent-dedicated
v0.24.0 runtime paths rather than expanding tests on every slice.

## Phase 1.5: Runtime Smoke

### Goal

Verify that helper extraction did not break ComfyUI module loading, browser
cache behavior, or real UI behavior.

### Manual Smoke Test

- Start ComfyUI.
- Hard-refresh the browser.
- Confirm no module loading errors in DevTools console.
- Confirm `easyuse_anima_api.js` loads successfully in the Network tab.
- Confirm autocomplete settings load.
- Confirm LoRA preset settings load.
- Confirm Prompt Studio settings load.
- Confirm Prompt Studio classification still works.
- Confirm classification API failure does not break the whole UI.
- Confirm settings UI long-text editor load/save still works.
- Load an existing workflow.
- Queue a workflow.
- Confirm there are no repeated warnings or unhandled promise rejections.

### API Failure Scenarios

Use browser Network overrides or a temporary local dev patch when practical.

- Settings API returns 500.
- Settings API returns malformed JSON.
- `classify_prompt` returns 500.
- Fetch rejects or times out.
- Multiple features request settings at the same time.

### Acceptance Criteria

- Hard refresh produces no module-loading error.
- Shared API import paths work in the browser.
- Existing user-visible behavior is unchanged.
- Smoke-test result is recorded in the PR or Issue #14 follow-up.

### 2026-07-05 v0.24.0 Smoke Evidence

Agent-side runtime checks used the dedicated `ComfyUI_v0.24.0` instance on
`127.0.0.1:8199`, with user/output/database/cache paths under that instance.

- `GET /system_stats` returned ComfyUI `0.24.0`.
- Raw runtime JS module requests returned HTTP 200 for the Prompt Studio entry
  file and the split `web/js/prompt_studio/*.js` modules.
- Minimal API queue smoke succeeded with
  `EasyUseAnimaPromptStudioAdvanced -> ShowText|pysssss`:
  prompt `d47e82ce-a098-4800-a16a-ae9595729c0c`, status `success`,
  completed `true`.
- Browser workflow load smoke pasted
  `docs/example_workflows/EasyUse_Anima_feature_test_release_en.json` into the
  ComfyUI canvas. The loaded graph created one
  `.easyuse-anima-advanced-editor` and six
  `textarea[data-easyuse-anima-advanced-field-id]` controls, preserving the
  expected field IDs and text values.
- Browser UI queue smoke ran the pasted feature-test workflow:
  prompt `9c3f2ad3-0f1d-4447-912a-64f8236c8abf`, status `success`,
  completed `true`, output nodes `3,4,5,6,7,8,9,10,11,12`.
- Browser reload smoke after the loaded workflow kept one
  `.easyuse-anima-advanced-editor`, six
  `textarea[data-easyuse-anima-advanced-field-id]` controls, and two canvas
  elements.
- EasyUse/prompt_studio filtered browser console warnings/errors were empty
  after load, export-dialog, queue, and reload smoke checks.
- The new ComfyUI graph menu opened the workflow export dialog and accepted its
  default filename. The in-app browser automation did not surface a download
  event, so file-download capture remains unconfirmed; no EasyUse or
  prompt_studio error was emitted during the export-dialog path.

## Phase 2: Prompt Studio Module Boundaries

### Goal

Split `easyuse_anima_prompt_studio.js` by responsibility while preserving
runtime behavior and workflow compatibility.

### Target Layout

```text
web/js/
  easyuse_anima_prompt_studio.js
  prompt_studio/
    constants.js
    advanced_controls.js
    advanced_node_ui.js
    advanced_fields_ui.js
    advanced_highlights.js
    advanced_fields_state.js
    advanced_values.js
    utils.js
    settings.js
    text.js
    highlight.js
    highlight_ui.js
    schema.js
    state.js
    canvas_forwarding.js
    serialization.js
    runtime_canvas.js
    extension_runtime.js
    layout.js
    advanced_layout_controller.js
    studio_textareas.js
    studio_resizable_input.js
    studio_node_ui.js
    studio_values.js
    wildcard_values.js
    textarea.js
    wheel.js
    dom.js
    extend_slots.js
    extend_layout.js
    extend_slot_controls.js
    style.js
    tooltip.js
    widgets.js
    legend.js
    fields.js
    node_hooks.js
```

### PR Split

Prefer splitting Phase 2 into separate PRs when review size is the main risk.
In the active branch, Phase 2 slices are kept as separate tested commits in the
same PR by request.

Planned slices:

1. `constants.js` and `utils.js`
2. `advanced_controls.js`
3. `advanced_fields_ui.js`
4. `advanced_fields_state.js`
5. `advanced_values.js`
6. `settings.js`
7. `text.js`
8. `highlight.js`
9. `schema.js`
10. `state.js`
11. `canvas_forwarding.js`
12. `serialization.js`
13. `layout.js`
14. `advanced_layout_controller.js`
15. `studio_textareas.js`
16. `studio_values.js`
17. `wildcard_values.js`
18. `textarea.js`
19. `wheel.js`
20. `dom.js`
21. `extend_slots.js`
22. `extend_layout.js`
23. `extend_slot_controls.js`
24. `style.js`
25. `tooltip.js`
26. `widgets.js`
27. `legend.js`
28. `fields.js`
29. `node_hooks.js`
30. entry file slim-down

Each PR should mostly move code and update imports. Behavior changes should be
separate PRs unless the move reveals a confirmed bug that cannot be separated.

### Phase 2-1: Constants And Utils

Move string constants, numeric defaults, CSS class names, storage keys, widget
names, node type names, and pure utility functions.

Acceptance criteria:

- String values for node types, widget names, and workflow keys do not change.
- No `app.registerExtension()`, `document`, or `window` dependency is added to
  `constants.js` or pure `utils.js`.
- Browser module loading remains clean.

### Phase 2-2: Schema

Move field defaults, normalization, cloning, and migration logic.

Candidate functions:

- `createDefaultField()`
- `normalizeField(raw)`
- `normalizeFields(rawFields)`
- `migrateAdvancedFields(rawData)`
- `cloneField(field)`
- `ensureFieldId(field)`
- `normalizeHeight(value)`
- `normalizeHeightMode(value)`

Schema rules:

- Existing `field.height` remains readable.
- Missing `heightMode` normalizes to `auto`.
- Unknown field keys are not deleted unless a migration explicitly owns them.
- Schema helpers do not know about DOM.

Acceptance criteria:

- Existing workflow fields keep the same meaning after normalization.
- Field count, id, label, and value survive save/reload.
- Schema helpers can be tested without ComfyUI.

### Phase 2-3: State

Move internal node state accessors.

Candidate functions:

- `ensureAdvancedState(node)`
- `getAdvancedState(node)`
- `getEditorElement(node)`
- `setEditorElement(node, element)`
- `getAdvancedFields(node)`
- `setAdvancedFields(node, fields)`
- `markLoadedFromWorkflow(node)`
- `isLoadedFromWorkflow(node)`

Acceptance criteria:

- Direct scattered `node.__easyuseAnima...` access is reduced.
- Workflow load restores the same internal state.
- Copy/paste reinitializes state correctly.

### Phase 2-4: Serialization

Move workflow load/save, queue-time DOM value collection, and field structure
sync logic.

Candidate functions:

- `readAdvancedFields(node)`
- `writeAdvancedFields(node, fields, options)`
- `collectAdvancedEditorFields(node)`
- `syncAdvancedValues(node, options)`
- `captureAdvancedConfigure(node, serialized)`
- `serializeAdvancedNode(node, serialized)`
- `syncInputsForFields(node, fields)`

Serialization rules:

- Field add/delete/move/rename may sync input sockets.
- Textarea value or height-only changes must not reorder input sockets.
- Queue/serialize should collect current DOM text/value.
- Layout-only actions must not rewrite field structure.

Acceptance criteria:

- Save/reload preserves field values.
- Queue payload field names and values are unchanged.
- Field structure edits update input sockets correctly.
- Text input alone does not reorder sockets.
- Layout-only actions do not change serialized workflow data.

### Phase 2-5: Layout

Move node/editor/widget size measurement and layout scheduling.

Candidate functions:

- `measureAdvancedEditorContentHeight(editor)`
- `advancedEditorMinimumHeight(node)`
- `advancedEditorLayoutHeight(node)`
- `advancedAvailableEditorViewportHeight(node)`
- `advancedEditorWidgetHeight(node)`
- `advancedMinimumNodeHeight(node)`
- `updateAdvancedEditorWidth(node)`
- `scheduleAdvancedLayout(node, reason)`
- `applyAdvancedLayout(node, reason)`
- `scheduleAdvancedResizeFinalize(node)`
- `finalizeAdvancedResize(node)`

Layout invariants:

- Node width resize changes editor width only.
- Node height resize changes editor viewport only.
- Node resize must not change textarea `field.height`.
- Node resize must not save field schema.
- Keep `node.size`, DOM widget allocation, editor viewport, and individual
  child heights as separate concepts.
- For single-surface nodes such as `Anima AiO Generator`, user node height may
  intentionally resize the internal panel viewport and its preview/settings
  child areas.
- For multi-field Prompt Studio Advanced editors, user node height resizes the
  editor viewport only. Textarea heights stay owned by textarea autosize or
  manual textarea resize.
- Minimum height correction is only for preventing clipping.
- Resize should not repeatedly fight user drag with immediate `setSize`.
- `requestAnimationFrame` scheduling needs duplicate guards.

Acceptance criteria:

- Node width resize does not change `field.height`.
- Node height resize does not change `field.height`.
- Enlarging a node does not grow textarea height JSON.
- Shrinking a node clamps only to content minimum.
- Loaded workflow width is respected unless below the absolute minimum.
- No layout loop appears in the browser console.

### Phase 2-6: Textarea

Move textarea autosize, manual resize, input handling, and `heightMode` logic.

Rules:

- Auto mode may autosize from content height.
- Manual mode starts only after real textarea resize.
- Focus/click must not enable manual mode.
- Manual mode input must not overwrite saved height with content height.
- Manual mode uses internal textarea scrolling for long text.
- Reload respects saved height and mode.

Acceptance criteria:

- Manual textarea resize saves `field.height`.
- Manual resize sets `heightMode` to `manual`.
- Input after manual resize does not overwrite height.
- Auto mode still grows and shrinks with content.
- Reload keeps height and mode.
- Textarea input alone does not sync input sockets.

### Phase 2-7: Wheel

Move wheel event routing for editor controls.

Rules:

- Wheel over textarea, input, or select stays with the DOM control only while
  that target can scroll in the wheel direction.
- If the target control cannot scroll and the editor cannot scroll in that
  direction, wheel may forward to the ComfyUI canvas so canvas zoom/pan still
  works.
- Wheel over empty editor surface may use the existing editor scroll or canvas
  forwarding path.
- `preventDefault` conditions are explicit.
- Passive listener behavior is considered.

Acceptance criteria:

- Wheel over scrollable textarea/input/select scrolls the DOM control and does
  not pan or zoom canvas.
- Wheel over a non-scrollable control falls through to editor scroll or canvas
  forwarding.
- Wheel over empty editor area keeps existing behavior.

### Phase 2-8: DOM And Styles

Move DOM builders and CSS injection.

Rules:

- DOM helpers create elements but do not automatically attach them globally.
- Style injection happens only through an explicit ensure function.
- Top-level style injection is not allowed.
- Style IDs prevent duplicate insertion.
- CSS class names come from constants where practical.
- Do not use `scrollbar-gutter: stable` for node editors unless persistent
  scrollbar alignment is explicitly required and verified. Reserving an empty
  scrollbar lane is a layout regression for Prompt Studio Advanced v2.

Acceptance criteria:

- Importing helper modules alone does not mutate DOM or style.
- Styles are inserted once during render/setup.
- UI class names remain compatible.

### Phase 2-9: Fields

Move field add/delete/move/rename behavior.

Rules:

- Structure changes may call `writeAdvancedFields(..., { syncInputs: true })`.
- Value or height-only changes use `syncInputs: false`.
- Field IDs do not collide.
- Move order matches DOM order and serialized order.

Acceptance criteria:

- Add/delete/move/rename saves correctly.
- Input socket order is correct after structure changes.
- Copy/paste does not collide field IDs.
- Queue payload remains valid after delete.

### Phase 2-10: Node Hooks

Move ComfyUI/LiteGraph hook wrapping into hook factory functions.

Rules:

- `app.registerExtension()` stays in the entry file.
- Hook modules export installers or wrappers.
- Original prototype method order and return values are preserved.
- `this` binding is preserved.
- Duplicate hook installation is guarded.

Acceptance criteria:

- Extension is not registered twice.
- Node create/configure/serialize/resize hooks still work.
- Original methods are still called.

### Phase 2-11: Entry Slim-Down

Final goal:

```js
import { app } from "../../../scripts/app.js";
import { registerPromptStudioNodeHooks } from "./prompt_studio/node_hooks.js";

app.registerExtension({
  name: "EasyUse.Anima.PromptStudio",
  async beforeRegisterNodeDef(nodeType, nodeData) {
    registerPromptStudioNodeHooks(nodeType, nodeData, makePromptStudioHookCallbacks());
  },
});
```

Actual names should follow the current code. The entry file should assemble the
extension and leave detailed DOM, layout, serialization, and field logic in
modules.

Acceptance criteria:

- Entry file mainly contains ComfyUI extension registration and hook assembly.
- Helper modules do not call `app.registerExtension()`.
- No import cycle exists.
- Browser module loading remains clean.

## Phase 3: JS Type Checking

### Goal

Catch JS shape errors without changing runtime output or adding a build system.

### Tasks

- Add `// @ts-check` to newly split modules first.
- Add JSDoc typedefs for Prompt Studio and shared helper shapes.
- Add `jsconfig.json` or `tsconfig.json`.
- Set `allowJs`, `checkJs`, and `noEmit`.
- Document the typecheck command.
- Keep runtime output as JavaScript.

### Typedef Targets

- `PromptStudioField`
- `PromptStudioFieldHeightMode`
- `PromptStudioState`
- `AdvancedEditorNode`
- `ComfyNodeLike`
- `ComfyWidgetLike`
- `PromptClassificationResult`
- `EasyUseAnimaSettings`
- `ApiJsonResponse`
- `LayoutMeasureResult`
- `ResizeFinalizeState`

### Typecheck Gate

- New modules have zero typecheck warnings.
- Legacy entry files are either included or explicitly excluded with a TODO.
- `any` usage is limited to unclear ComfyUI/LiteGraph external objects.
- Runtime import paths do not change for type checking.

### Current Typecheck Slice

Phase 3 uses a no-build typecheck gate for the Prompt Studio entry shim and
all split Prompt Studio modules. The command is:

```powershell
$env:npm_config_cache = "D:\ComfyUI\.codex_cache\npm"
$env:TEMP = "D:\ComfyUI\.codex_tmp\temp"
$env:TMP = $env:TEMP
npx --yes -p typescript@6.0.3 tsc -p jsconfig.json
```

The gate keeps ComfyUI runtime output as raw JavaScript and limits TypeScript
scope through `jsconfig.json` instead of introducing a build step.

Current status:

- 2026-07-05: `types.js` and `runtime_canvas.js` pass the documented
  typecheck command.
- 2026-07-05: typecheck coverage expanded to `constants.js`, `utils.js`,
  `schema.js`, and `state.js`.
- 2026-07-05: typecheck coverage expanded to `advanced_values.js`,
  `style.js`, `widgets.js`, `layout.js`, `fields.js`, and
  `serialization.js`.
- 2026-07-05: typecheck coverage expanded to
  `advanced_layout_controller.js`, `dom.js`, `node_hooks.js`, `settings.js`,
  `textarea.js`, `wheel.js`, and `wildcard_values.js`.
- 2026-07-05: typecheck coverage expanded to `tooltip.js`.
- 2026-07-05: typecheck coverage expanded to `studio_textareas.js` after
  documenting Prompt Studio input overlay fields and the `"immediate"` refresh
  mode.
- 2026-07-05: typecheck coverage expanded to all `web/js/prompt_studio/*.js`
  modules and the `easyuse_anima_prompt_studio.js` entry shim. ComfyUI host
  `scripts/app.js` imports remain runtime imports and are documented with
  `@ts-expect-error` comments.

## Phase 4: Vite/TypeScript Decision

### Goal

Decide whether a build system is justified after modules and JS type checks are
stable.

### Decision

Do not introduce Vite, TypeScript source files, npm dependencies, or a `dist`
tree in this PR.

Current evidence:

- `__init__.py` exposes `WEB_DIRECTORY = "./web"`, so ComfyUI loads the raw
  files under `web/js` directly.
- The repository has no `package.json`, lockfile, `frontend/src`, or committed
  `dist` tree.
- `jsconfig.json` provides no-build checking for
  `easyuse_anima_prompt_studio.js` and all `web/js/prompt_studio/*.js` files.
- HTTP runtime smoke on `ComfyUI_v0.24.0` loads the raw entry and split modules
  from `/extensions/comfyui-easyuse-anima/js/...`.

Policy for this PR:

- Build command: none.
- `dist` output: none.
- Committed generated frontend assets: none.
- ComfyUI Manager install behavior: clone/install should work without running a
  frontend build because raw JS remains the distributed runtime.
- Legacy `web/js` entry files remain thin ComfyUI extension loaders.
- If a future PR adopts Vite/TypeScript, it must decide whether to commit
  deterministic built output and must prove ComfyUI Manager installs still work
  without a local build step.

### Adoption Gate

- Prompt Studio module split is complete.
- `// @ts-check` warnings are resolved in new modules.
- Workflow compatibility smoke testing is stable.
- No import cycles exist.
- ComfyUI Manager user install behavior is decided.
- `dist` commit policy is decided.
- Release validation commands are decided.

### Decisions Required

- Whether to create `frontend/src`.
- Whether to output into `web/js/dist`.
- Whether built `dist` files are committed.
- Whether users must run `pnpm build`.
- Whether source maps are shipped.
- How ComfyUI `WEB_DIRECTORY` loading order is preserved.
- Whether legacy `web/js` entry files remain thin loaders.

### Acceptance Criteria

- Clone or ComfyUI Manager install works without extra steps, or committed
  `dist` files provide that behavior.
- Build output is deterministic.
- Source and built output mismatch can be detected.
- Hard refresh produces no browser module-loading error.

For this no-build decision, deterministic build output and source/built mismatch
checks are not applicable because no build output is produced.

## Compatibility Checklist

### Workflow

- Node type names do not change.
- Widget names do not change.
- Input socket names do not change.
- Output socket names do not change.
- Serialized property keys do not change.
- `widgets_values` order does not change.
- Existing workflows load.
- Layout-only actions do not change serialized workflow data.

### API

- `/easyuse_anima/settings` route behavior does not change.
- `/easyuse_anima/classify_prompt` route behavior does not change.
- Request body keys do not change.
- Response field expectations do not change.
- API failures do not break the whole UI.

### ComfyUI Loading

- `WEB_DIRECTORY` ES module loading is preserved.
- Relative import paths are valid.
- Import cycles are avoided.
- Helper imports do not perform side effects.
- `app.registerExtension()` stays in entry files.
- Browser hard refresh requirement is documented.

### Browser Runtime

- Raw JS files do not contain TypeScript syntax.
- CSS injection is not duplicated.
- Event listeners are not duplicated.
- `requestAnimationFrame` loops are guarded.
- Unhandled promise rejections are avoided.

## Prompt Studio Layout And Resize Checklist

### Node Resize

- Node width resize changes editor width only.
- Node width resize does not change `field.height`.
- Node width resize does not change serialized fields.
- Node height resize changes editor viewport only.
- Node height resize does not change textarea stored height.
- Minimum height correction only prevents clipping.
- Finalize-stage clamp is preferred over immediate drag-time `setSize`.

### Textarea Resize

- Manual textarea resize saves `field.height`.
- Manual textarea resize sets `heightMode` to `manual`.
- Focus or click does not enter manual mode.
- Real pointer/mouse resize is detected by height delta.
- Manual mode input does not overwrite height with content height.
- Auto mode input autosizes from content height.
- Reload respects saved height.

### Serialize And Queue

- Queue collects current DOM text/value.
- Field structure changes may sync input sockets.
- Value/height-only changes do not sync input sockets.
- Serialize does not reorder fields.
- Layout-only actions do not change workflow JSON.

## Frontend Refactor PR Checklist

Use this checklist for each follow-up frontend refactor PR.

### Scope

- The PR purpose is stated in one sentence.
- The PR states whether it is refactor-only or user-facing.
- The PR states which Issue #14 phase it covers.

### Compatibility

- No Python node behavior change.
- No API route change.
- No node type change.
- No widget name change.
- No input/output socket name change.
- No serialized workflow key change.
- No `widgets_values` order change.
- Node 2.0 UI and legacy canvas behavior are both considered for DOM widget,
  canvas, layout, preview, and hidden-widget changes.
- DOM widget `getMinHeight`, `getHeight`, `computeLayoutSize`, CSS
  height/overflow rules, and `node.setSize()` paths remain aligned.

### Module Boundary

- Helper modules do not call `app.registerExtension()`.
- Helper modules do not mutate DOM at import time.
- Helper modules do not fetch at import time.
- Entry files own ComfyUI registration side effects.
- Import cycles are checked.

### Validation

- `node --check` passed for changed frontend files.
- Relevant unit tests passed.
- Full unittest passed or skipped with a clear reason.
- `compileall` passed for Python-touching PRs or release-facing PRs.
- `git diff --check` passed.
- Browser hard-refresh smoke test is run or explicitly marked not run.

### Manual Smoke

- ComfyUI starts.
- Browser hard refresh performed.
- No browser console module error.
- Existing workflow loads.
- New node creation works.
- Save/reload works.
- Queue works.
- Copy/paste works.
- Node 2.0 UI smoke check was run, or the gap is stated.
- Legacy canvas smoke check was run, or the gap is stated.

### Regression

- Layout-only action does not change workflow JSON.
- Textarea resize and node resize are separate.
- Wheel events over scrollable textarea/input/select do not reach canvas
  pan/zoom; wheel over non-scrollable controls may forward to the canvas after
  editor scroll handling.

## Issue #14 Tracking Template

Use this in Issue #14 or follow-up PR tracking comments.

```text
### Phase 1: Shared frontend API helper
[x] easyuse_anima_api.js added
[x] settings API calls centralized
[x] classify_prompt API calls centralized
[x] source guard tests added
[ ] Phase 1 PR merged

### Phase 1.5: Runtime smoke
[x] hard refresh tested
[x] browser console clean
[x] existing workflow load tested
[x] queue tested
[ ] API failure fallback tested

### Phase 2: Prompt Studio module split
[x] constants.js extracted
[x] advanced_controls.js extracted
[x] advanced_node_ui.js extracted
[x] advanced_fields_ui.js extracted
[x] advanced_highlights.js extracted
[x] advanced_fields_state.js extracted
[x] advanced_values.js extracted
[x] utils.js extracted
[x] settings.js extracted
[x] text.js extracted
[x] highlight.js extracted
[x] highlight_ui.js extracted
[x] schema.js extracted
[x] state.js extracted
[x] canvas_forwarding.js extracted
[x] serialization.js extracted
[x] runtime_canvas.js extracted
[x] extension_runtime.js extracted
[x] layout.js extracted
[x] advanced_layout_controller.js extracted
[x] studio_textareas.js extracted
[x] studio_resizable_input.js extracted
[x] studio_node_ui.js extracted
[x] studio_values.js extracted
[x] wildcard_values.js extracted
[x] textarea.js extracted
[x] wheel.js extracted
[x] dom.js extracted
[x] extend_slots.js extracted
[x] extend_layout.js extracted
[x] extend_slot_controls.js extracted
[x] style.js extracted
[x] tooltip.js extracted
[x] widgets.js extracted
[x] legend.js extracted
[x] fields.js extracted
[x] node_hooks.js extracted
[x] entry file slimmed down

### Phase 3: JS type checking
[x] // @ts-check added to new modules
[x] JSDoc typedefs added
[x] jsconfig/tsconfig added
[x] typecheck command documented
[x] typecheck warnings resolved

### Phase 4: Vite/TypeScript decision
[x] dist commit policy decided
[x] build command decided
[x] ComfyUI loading order verified
[x] ComfyUI Manager install behavior verified
[x] decision documented

### Close criteria
[x] workflow compatibility verified
[x] runtime smoke test passed
[x] docs linked from development README
[x] no open Phase 2/3 blockers
```

## References

- Issue #14: `https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/14`
- PBandDev ComfyUI TypeScript template:
  `https://github.com/PBandDev/comfyui-custom-node-template`
- ComfyUI frontend modernization announcement:
  `https://github.com/Comfy-Org/ComfyUI/issues/4169`
- ComfyUI React extension template:
  `https://github.com/Comfy-Org/ComfyUI-React-Extension-Template`
