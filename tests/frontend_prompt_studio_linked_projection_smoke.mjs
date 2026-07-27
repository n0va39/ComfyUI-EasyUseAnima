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
  export const ADVANCED_FIELD_SOCKET_PREFIX = "field_";
  export const ADVANCED_FIELDS_PROPERTY = "easyuse_anima_advanced_fields";
  export const ADVANCED_LEGACY_FIELDS_WIDGET_INDEXES = [];
  export const ADVANCED_WIDGET_INDEX = { advanced_fields: 0 };
`);
const schemaUrl = inlineModule(`
  export function advancedFieldInputName(field) { return \`field_\${field.id}\`; }
  export function advancedDefaultFieldsValue() { return "[]"; }
  export function normalizeAdvancedField(field) { return { ...field }; }
  export function normalizeAdvancedFieldsValue(value) { return String(value || ""); }
`);
const stateUrl = inlineModule(`
  export function clearPendingAdvancedFieldsValue() {}
  export function getAdvancedEditorElement(node) { return node.__editor || null; }
  export function getAdvancedFields(node) { return node.__fields || []; }
  export function getPendingAdvancedFieldsValue() { return ""; }
  export function setPendingAdvancedFieldsValue() {}
`);
const serialization = await import(dataModule(
  "../web/js/prompt_studio/serialization.js",
  {
    "./constants.js": constantsUrl,
    "./schema.js": schemaUrl,
    "./state.js": stateUrl,
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

function field(id, text = `fallback-${id}`) {
  return {
    id,
    pane: id.startsWith("negative") ? "negative" : "positive",
    type: "general",
    enabled: true,
    text,
  };
}

function createNode(id, fields = [field("positive_general")]) {
  const textareas = fields.map((item) => ({
    dataset: { easyuseAnimaAdvancedFieldId: item.id },
    style: { height: "72px" },
    value: item.text,
  }));
  return {
    id,
    __fields: fields,
    __editor: {
      querySelectorAll: () => textareas,
    },
    inputs: fields.map((item, index) => ({
      name: `field_${item.id}`,
      link: index + 1,
      __easyuseAnimaAdvancedFieldInput: true,
      __easyuseAnimaAdvancedFieldId: item.id,
    })),
    textareas,
  };
}

function createGraph(node) {
  const links = {};
  node.inputs.forEach((input, index) => {
    links[input.link] = { origin_id: 100 + index, origin_slot: index };
  });
  return { links };
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

function queue(runtime, node, graph, promptId) {
  const snapshots = serialization.captureAdvancedLinkedFieldSnapshots(
    node,
    node.__fields,
    graph,
  );
  const captured = runtime.captureQueue([{
    node,
    surfaces: snapshots.map((snapshot) => snapshot.surface),
  }]);
  assert.equal(captured.length, 1);
  assert.equal(
    runtime.acceptQueue(captured, { ok: true, result: { prompt_id: promptId } }),
    1,
  );
  return { snapshots, transaction: captured[0].transaction };
}

function emit(api, promptId, node, output) {
  api.emit("executed", {
    prompt_id: promptId,
    node: String(node.id),
    output,
  });
}

function committer(node, graph, snapshot, value, commits) {
  return {
    surface: snapshot.surface,
    commit: ({ transaction, envelope }) => {
      assert.equal(transaction.promptId, envelope.promptId);
      return serialization.commitAdvancedLinkedFieldOverlay(
        node,
        snapshot,
        value,
        {
          graph,
          commitView: (_node, _field, textarea, text) => {
            commits.push(snapshot.fieldId);
            assert.ok(textarea, "linked commit must target the exact field textarea");
            textarea.value = text;
          },
        },
      );
    },
  };
}

// One linked projection updates only its overlay/view. The submitted fallback
// remains canonical when the editor is collected for workflow serialization.
{
  const { api, runtime } = createHarness();
  const node = createNode("single");
  const graph = createGraph(node);
  const { snapshots } = queue(runtime, node, graph, "single-prompt");
  const output = { prompt_studio_advanced: [{
    field_inputs: { field_positive_general: "execution-derived" },
  }] };
  const commits = [];
  emit(api, "single-prompt", node, output);
  assert.equal(await runtime.consumeExecution(node, output, 1, [
    committer(node, graph, snapshots[0], "execution-derived", commits),
  ]), true);
  assert.deepEqual(commits, ["positive_general"]);
  assert.equal(node.textareas[0].value, "execution-derived");
  assert.equal(
    node.__easyuseAnimaAdvancedFieldInputValues.field_positive_general,
    "execution-derived",
  );
  assert.equal(
    serialization.collectAdvancedEditorFields(node, node.__fields)[0].text,
    "fallback-positive_general",
    "execution overlay must not serialize into the local fallback",
  );
}

// Q3 owns the latest accepted revision; Q1/Q2 cannot publish older values.
{
  const { api, runtime } = createHarness();
  const node = createNode("latest");
  const graph = createGraph(node);
  const queued = [1, 2, 3].map((number) => (
    queue(runtime, node, graph, `q${number}`)
  ));
  for (let index = 0; index < queued.length; index += 1) {
    const promptId = `q${index + 1}`;
    const output = { prompt_studio_advanced: [{ field_inputs: {
      field_positive_general: promptId,
    } }] };
    emit(api, promptId, node, output);
    const commits = [];
    assert.equal(
      await runtime.consumeExecution(node, output, 1, [
        committer(node, graph, queued[index].snapshots[0], promptId, commits),
      ]),
      index === 2,
    );
    assert.deepEqual(commits, index === 2 ? ["positive_general"] : []);
  }
  assert.equal(node.textareas[0].value, "q3");
}

// A terminal newer execution never re-opens an older accepted fallback.
{
  const { api, runtime } = createHarness();
  const node = createNode("terminal");
  const graph = createGraph(node);
  const older = queue(runtime, node, graph, "older");
  queue(runtime, node, graph, "newer");
  api.emit("execution_error", { prompt_id: "newer" });
  const output = { prompt_studio_advanced: [{ field_inputs: {
    field_positive_general: "older-value",
  } }] };
  emit(api, "older", node, output);
  const commits = [];
  assert.equal(await runtime.consumeExecution(node, output, 1, [
    committer(node, graph, older.snapshots[0], "older-value", commits),
  ]), false);
  assert.deepEqual(commits, []);
}

// Field revisions are independent: editing A blocks A while B still settles
// from the same envelope.
{
  const { api, runtime } = createHarness();
  const fields = [field("positive_a"), field("negative_b")];
  const node = createNode("field-revisions", fields);
  const graph = createGraph(node);
  const { snapshots } = queue(runtime, node, graph, "field-revisions");
  assert.equal(runtime.markEdited(node, [snapshots[0].surface]), true);
  fields[0].text = "edited-after-queue";
  node.textareas[0].value = "edited-after-queue";
  const output = { prompt_studio_advanced: [{ field_inputs: {
    field_positive_a: "execution-a",
    field_negative_b: "execution-b",
  } }] };
  emit(api, "field-revisions", node, output);
  const commits = [];
  assert.equal(await runtime.consumeExecution(node, output, 1, [
    committer(node, graph, snapshots[0], "execution-a", commits),
    committer(node, graph, snapshots[1], "execution-b", commits),
  ]), true);
  assert.deepEqual(commits, ["negative_b"]);
  assert.equal(node.textareas[0].value, "edited-after-queue");
  assert.equal(node.textareas[1].value, "execution-b");
}

// Missed UI revision signals still fail closed on structure and connection
// fingerprints: remove, type/enable changes, disconnect, and reconnect.
for (const mutation of [
  (node) => { node.__fields = []; },
  (node) => { node.__fields[0].type = "trigger"; },
  (node) => { node.__fields[0].enabled = false; },
  (node) => { node.inputs[0].link = null; },
  (_node, graph) => { delete graph.links[1]; },
  (node, graph) => {
    node.inputs[0].link = 9;
    graph.links[9] = { origin_id: 999, origin_slot: 4 };
  },
]) {
  const node = createNode("structure");
  const graph = createGraph(node);
  const [snapshot] = serialization.captureAdvancedLinkedFieldSnapshots(
    node,
    node.__fields,
    graph,
  );
  mutation(node, graph);
  assert.equal(
    serialization.commitAdvancedLinkedFieldOverlay(
      node,
      snapshot,
      "must-not-commit",
      { graph },
    ),
    false,
  );
}

console.log("Prompt Studio linked execution projection smoke passed.");
