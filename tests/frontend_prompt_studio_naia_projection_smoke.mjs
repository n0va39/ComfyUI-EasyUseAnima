import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

function inlineModule(source) {
  return `data:text/javascript;base64,${Buffer.from(source).toString("base64")}`;
}

function dataModule(relativePath, replacements = {}) {
  let source = readFileSync(new URL(relativePath, import.meta.url), "utf8");
  for (const [specifier, replacement] of Object.entries(replacements)) {
    source = source.replaceAll(`"${specifier}"`, `"${replacement}"`);
  }
  return inlineModule(source);
}

const constantsUrl = inlineModule(`
  export const NAIA_ADVANCED_RESOLUTION_BUCKET = "NAIA";
`);
const stateUrl = inlineModule(`
  export function getAdvancedEditorElement(node) { return node.__editor || null; }
  export function getAdvancedFields(node) { return node.__fields || []; }
`);
const widgetsUrl = inlineModule(`
  export function findWidget(node, name) {
    return node?.widgets?.find((widget) => widget.name === name) || null;
  }
`);
const projection = await import(dataModule(
  "../web/js/prompt_studio/naia_projection.js",
  {
    "./constants.js": constantsUrl,
    "./state.js": stateUrl,
    "./widgets.js": widgetsUrl,
  },
));
const ownerModule = await import(dataModule(
  "../web/js/lifecycle/queue_ui_transaction.js",
));
const contextModule = await import(dataModule(
  "../web/js/lifecycle/executed_event_context.js",
));
const transactionModule = await import(dataModule(
  "../web/js/prompt_studio/execution_transaction.js",
));

class FakeApi {
  constructor() { this.listeners = new Map(); }
  addEventListener(type, listener) {
    const listeners = this.listeners.get(type) || [];
    listeners.push(listener);
    this.listeners.set(type, listeners);
  }
  removeEventListener(type, listener) {
    this.listeners.set(
      type,
      (this.listeners.get(type) || []).filter((candidate) => candidate !== listener),
    );
  }
  emit(type, detail) {
    for (const listener of this.listeners.get(type) || []) listener({ detail });
  }
}

function naiaField(id, pane, text) {
  return {
    id,
    pane,
    type: "naia",
    enabled: true,
    label: `${pane} NAIA`,
    text,
    height: 72,
  };
}

function generalField(id, pane, text) {
  return {
    id,
    pane,
    type: "general",
    enabled: true,
    label: `${pane} General`,
    text,
    height: 96,
  };
}

function createNode(id, fields, {
  bucket = "NAIA",
  width = 1024,
  height = 1024,
  artistMix = "exact",
} = {}) {
  const textareas = fields.map((field) => ({
    dataset: { easyuseAnimaAdvancedFieldId: field.id },
    value: field.text,
  }));
  const node = {
    id,
    __fields: fields,
    __editor: {
      querySelectorAll: () => textareas,
    },
    properties: {},
    textareas,
    persistCount: 0,
    renderCount: 0,
    resolutionCommitCount: 0,
    widgets: [
      { name: "advanced_fields", value: JSON.stringify(fields) },
      { name: "resolution_bucket", value: bucket },
      { name: "resolution_size", value: `${width} * ${height}` },
      { name: "resolution_custom_width", value: width },
      { name: "resolution_custom_height", value: height },
      { name: "artist_mix_mode", value: artistMix },
    ],
  };
  node.properties.easyuse_anima_advanced_fields = node.widgets[0].value;
  return node;
}

function widget(node, name) {
  return node.widgets.find((candidate) => candidate.name === name);
}

function createHarness() {
  const api = new FakeApi();
  const owner = ownerModule.createQueueUiTransactionOwner();
  let runtime;
  const executedContext = contextModule.createExecutedEventContext(api, {
    finishPrompt: (promptId) => runtime.finishPrompt(promptId),
  });
  runtime = transactionModule.createPromptStudioExecutionTransaction({
    owner,
    executedContext,
  });
  executedContext.install();
  return { api, runtime };
}

function capture(runtime, node, promptId) {
  const naia = projection.captureAdvancedNaiaFieldSnapshots(node.__fields);
  const resolution = projection.captureAdvancedNaiaResolutionSnapshot(node);
  const captured = runtime.captureQueue([{
    node,
    surfaces: [
      ...naia.map((snapshot) => snapshot.surface),
      ...(resolution ? [resolution.surface] : []),
    ],
  }]);
  assert.equal(captured.length, 1);
  assert.equal(
    runtime.acceptQueue(captured, { ok: true, result: { prompt_id: promptId } }),
    1,
  );
  return {
    naia,
    resolution,
    transaction: captured[0].transaction,
  };
}

function emit(api, promptId, node, output) {
  api.emit("executed", {
    prompt_id: promptId,
    node: String(node.id),
    output,
  });
}

function persistFields(node, fields) {
  const value = JSON.stringify(fields);
  widget(node, "advanced_fields").value = value;
  node.properties.easyuse_anima_advanced_fields = value;
  node.persistCount += 1;
}

function commitFieldView(node, _field, textarea, text) {
  assert.ok(textarea, "NAIA commit must target the exact field textarea");
  textarea.value = text;
  assert.equal(node.renderCount, 0, "NAIA commit must not broadly rerender the editor");
}

function fieldCommitter(node, snapshot, value) {
  return {
    surface: snapshot.surface,
    commit: () => projection.commitAdvancedNaiaFieldCanonical(
      node,
      snapshot,
      value,
      { persistFields, commitView: commitFieldView },
    ),
  };
}

function commitResolutionView(node, width, height) {
  widget(node, "resolution_custom_width").value = width;
  widget(node, "resolution_custom_height").value = height;
  widget(node, "resolution_size").value = `${width} * ${height}`;
  node.resolutionCommitCount += 1;
  return true;
}

function resolutionCommitter(node, snapshot, value) {
  return {
    surface: snapshot.surface,
    commit: () => projection.commitAdvancedNaiaResolution(
      node,
      snapshot,
      value,
      { commitView: commitResolutionView },
    ),
  };
}

// Exact positive/negative fields become canonical and survive workflow save/reload.
// Unrelated fields, resolution, and Artist Mix remain untouched.
{
  const { api, runtime } = createHarness();
  const node = createNode("single", [
    naiaField("positive_naia", "positive", "old positive"),
    generalField("positive_general", "positive", "keep general"),
    naiaField("negative_naia", "negative", "old negative"),
  ], { bucket: "Custom", width: 1344, height: 768, artistMix: "average" });
  const queued = capture(runtime, node, "single");
  assert.equal(queued.resolution, null, "Custom resolution must not capture a NAIA surface");
  const output = { prompt_studio_advanced: [{
    naia_field_updates: {
      positive_naia: "new positive",
      negative_naia: "new negative",
    },
  }] };
  emit(api, "single", node, output);
  assert.equal(await runtime.consumeExecution(node, output, 1, [
    fieldCommitter(node, queued.naia[0], "new positive"),
    fieldCommitter(node, queued.naia[1], "new negative"),
  ]), true);
  const saved = JSON.parse(widget(node, "advanced_fields").value);
  assert.deepEqual(saved.map((field) => [field.id, field.text]), [
    ["positive_naia", "new positive"],
    ["positive_general", "keep general"],
    ["negative_naia", "new negative"],
  ]);
  assert.deepEqual(
    JSON.parse(node.properties.easyuse_anima_advanced_fields),
    saved,
    "workflow property reload must preserve canonical NAIA text",
  );
  assert.equal(widget(node, "resolution_custom_width").value, 1344);
  assert.equal(widget(node, "resolution_custom_height").value, 768);
  assert.equal(widget(node, "artist_mix_mode").value, "average");
  assert.equal(node.textareas[0].value, "new positive");
  assert.equal(node.textareas[2].value, "new negative");
}

// Q3 owns both NAIA field and resolution surfaces regardless of completion order.
{
  const { api, runtime } = createHarness();
  const node = createNode("latest", [
    naiaField("positive_naia", "positive", "initial"),
    generalField("positive_general", "positive", "preserve"),
  ]);
  const queued = [1, 2, 3].map((number) => capture(runtime, node, `q${number}`));
  for (const number of [2, 1, 3]) {
    const promptId = `q${number}`;
    const output = { prompt_studio_advanced: [{
      naia_field_updates: { positive_naia: promptId },
      naia_resolution_update: { width: 800 + (number * 32), height: 1184 + (number * 32) },
    }] };
    emit(api, promptId, node, output);
    assert.equal(await runtime.consumeExecution(node, output, 1, [
      fieldCommitter(node, queued[number - 1].naia[0], promptId),
      resolutionCommitter(
        node,
        queued[number - 1].resolution,
        output.prompt_studio_advanced[0].naia_resolution_update,
      ),
    ]), number === 3);
  }
  assert.equal(node.__fields[0].text, "q3");
  assert.equal(node.__fields[1].text, "preserve");
  assert.equal(widget(node, "resolution_bucket").value, "NAIA");
  assert.equal(widget(node, "resolution_custom_width").value, 896);
  assert.equal(widget(node, "resolution_custom_height").value, 1280);
  assert.equal(node.persistCount, 1, "only Q3 may persist canonical field text");
  assert.equal(node.resolutionCommitCount, 1, "only Q3 may update runtime resolution");
}

// A terminal Q3 never re-opens an older accepted fallback.
{
  const { api, runtime } = createHarness();
  const node = createNode("terminal", [
    naiaField("positive_naia", "positive", "initial"),
  ]);
  const older = capture(runtime, node, "older");
  capture(runtime, node, "newer");
  api.emit("execution_error", { prompt_id: "newer" });
  const output = { prompt_studio_advanced: [{
    naia_field_updates: { positive_naia: "must-not-fallback" },
  }] };
  emit(api, "older", node, output);
  assert.equal(await runtime.consumeExecution(node, output, 1, [
    fieldCommitter(node, older.naia[0], "must-not-fallback"),
  ]), false);
  assert.equal(node.__fields[0].text, "initial");
  assert.equal(node.persistCount, 0);
}

// Post-queue field and resolution edits invalidate only their exact surfaces.
{
  const { api, runtime } = createHarness();
  const node = createNode("edited", [
    naiaField("positive_naia", "positive", "initial"),
  ]);
  const queued = capture(runtime, node, "edited");
  assert.equal(runtime.markEdited(node, [queued.naia[0].surface]), true);
  node.__fields[0].text = "manual field edit";
  assert.equal(runtime.markEdited(node, [queued.resolution.surface]), true);
  widget(node, "resolution_custom_width").value = 1152;
  const output = { prompt_studio_advanced: [{
    naia_field_updates: { positive_naia: "stale field" },
    naia_resolution_update: { width: 832, height: 1216 },
  }] };
  emit(api, "edited", node, output);
  assert.equal(await runtime.consumeExecution(node, output, 1, [
    fieldCommitter(node, queued.naia[0], "stale field"),
    resolutionCommitter(node, queued.resolution, { width: 832, height: 1216 }),
  ]), false);
  assert.equal(node.__fields[0].text, "manual field edit");
  assert.equal(widget(node, "resolution_custom_width").value, 1152);
}

// Missed revision signals still fail closed on exact field and resolution identity.
for (const mutation of [
  (node) => { node.__fields = []; },
  (node) => { node.__fields[0].type = "general"; },
  (node) => { node.__fields[0].pane = "negative"; },
  (node) => { node.__fields[0].enabled = false; },
]) {
  const node = createNode("structure", [
    naiaField("positive_naia", "positive", "initial"),
  ]);
  const [snapshot] = projection.captureAdvancedNaiaFieldSnapshots(node.__fields);
  mutation(node);
  assert.equal(
    projection.commitAdvancedNaiaFieldCanonical(
      node,
      snapshot,
      "must-not-commit",
      { persistFields },
    ),
    false,
  );
  assert.equal(node.persistCount, 0);
}

{
  const node = createNode("resolution-structure", [
    naiaField("positive_naia", "positive", "initial"),
  ]);
  const snapshot = projection.captureAdvancedNaiaResolutionSnapshot(node);
  widget(node, "resolution_bucket").value = "Custom";
  assert.equal(
    projection.commitAdvancedNaiaResolution(
      node,
      snapshot,
      { width: 832, height: 1216 },
      { commitView: commitResolutionView },
    ),
    false,
  );
  assert.equal(node.resolutionCommitCount, 0);
}

console.log("Prompt Studio NAIA canonical projection smoke passed.");
