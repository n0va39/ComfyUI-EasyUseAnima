# Issue 14 Frontend JS Maintenance Plan

## Position

Issue #14 is accepted as a frontend maintainability track. It should not be
closed by the current PR alone.

The active PR is:

```text
Issue #14 Phase 1 + staged Phase 2 frontend module boundary work
```

The active PR starts the Issue #14 work by centralizing shared frontend API
helpers and then continues the Prompt Studio JavaScript module split in tested
commits. It does not complete JS type-checking work or the Vite/TypeScript
build decision.

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
    utils.js
    settings.js
    text.js
    highlight.js
    schema.js
    state.js
    canvas_forwarding.js
    serialization.js
    layout.js
    textarea.js
    wheel.js
    dom.js
    extend_slots.js
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
2. `settings.js`
3. `text.js`
4. `highlight.js`
5. `schema.js`
6. `state.js`
7. `canvas_forwarding.js`
8. `serialization.js`
9. `layout.js`
10. `textarea.js`
11. `wheel.js`
12. `dom.js`
13. `extend_slots.js`
14. `extend_slot_controls.js`
15. `style.js`
16. `tooltip.js`
17. `widgets.js`
18. `legend.js`
19. `fields.js`
20. `node_hooks.js`
21. entry file slim-down

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

- Wheel over textarea, input, or select stays with the DOM control.
- Wheel over empty editor surface may use the existing canvas forwarding path.
- `preventDefault` conditions are explicit.
- Passive listener behavior is considered.

Acceptance criteria:

- Wheel over textarea does not pan or zoom canvas.
- Wheel over input/select does not pan or zoom canvas.
- Wheel over empty editor area keeps existing behavior.

### Phase 2-8: DOM And Styles

Move DOM builders and CSS injection.

Rules:

- DOM helpers create elements but do not automatically attach them globally.
- Style injection happens only through an explicit ensure function.
- Top-level style injection is not allowed.
- Style IDs prevent duplicate insertion.
- CSS class names come from constants where practical.

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

## Phase 4: Vite/TypeScript Decision

### Goal

Decide whether a build system is justified after modules and JS type checks are
stable.

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

### Regression

- Layout-only action does not change workflow JSON.
- Textarea resize and node resize are separate.
- Wheel events over textarea/input/select do not reach canvas pan/zoom.

## Issue #14 Tracking Template

Use this in Issue #14 or follow-up PR tracking comments.

```text
### Phase 1: Shared frontend API helper
[ ] easyuse_anima_api.js added
[ ] settings API calls centralized
[ ] classify_prompt API calls centralized
[ ] source guard tests added
[ ] Phase 1 PR merged

### Phase 1.5: Runtime smoke
[ ] hard refresh tested
[ ] browser console clean
[ ] existing workflow load tested
[ ] queue tested
[ ] API failure fallback tested

### Phase 2: Prompt Studio module split
[ ] constants.js extracted
[ ] utils.js extracted
[ ] settings.js extracted
[ ] text.js extracted
[ ] highlight.js extracted
[ ] schema.js extracted
[ ] state.js extracted
[ ] canvas_forwarding.js extracted
[ ] serialization.js extracted
[ ] layout.js extracted
[ ] textarea.js extracted
[ ] wheel.js extracted
[ ] dom.js extracted
[ ] extend_slots.js extracted
[ ] extend_slot_controls.js extracted
[ ] style.js extracted
[ ] tooltip.js extracted
[ ] widgets.js extracted
[ ] legend.js extracted
[ ] fields.js extracted
[ ] node_hooks.js extracted
[ ] entry file slimmed down

### Phase 3: JS type checking
[ ] // @ts-check added to new modules
[ ] JSDoc typedefs added
[ ] jsconfig/tsconfig added
[ ] typecheck command documented
[ ] typecheck warnings resolved

### Phase 4: Vite/TypeScript decision
[ ] dist commit policy decided
[ ] build command decided
[ ] ComfyUI loading order verified
[ ] ComfyUI Manager install behavior verified
[ ] decision documented

### Close criteria
[ ] workflow compatibility verified
[ ] runtime smoke test passed
[ ] docs linked from development README
[ ] no open Phase 2/3 blockers
```

## References

- Issue #14: `https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/14`
- PBandDev ComfyUI TypeScript template:
  `https://github.com/PBandDev/comfyui-custom-node-template`
- ComfyUI frontend modernization announcement:
  `https://github.com/Comfy-Org/ComfyUI/issues/4169`
- ComfyUI React extension template:
  `https://github.com/Comfy-Org/ComfyUI-React-Extension-Template`
