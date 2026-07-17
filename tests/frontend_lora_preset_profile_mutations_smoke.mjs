import assert from "node:assert/strict";
import { createLoraPresetProfileMutations } from "../web/js/lora_preset/profile_mutations.js";
import { createLoraPresetSaveSync } from "../web/js/lora_preset/save_sync.js";

function createProfileNode() {
  const widgets = new Map([
    ["style_prompt", { value: "first prompt" }],
    ["profile_index", { value: 1 }],
    ["profile_count", { value: "2" }],
    ["loras", { value: '[{"name":"first.safetensors","on":true,"strength":1,"strengthTwo":null}]' }],
    ["profile_data", { value: JSON.stringify({
      "1": {
        style_prompt: "first prompt",
        loras: [{ name: "first.safetensors", on: true, strength: 1, strengthTwo: null }],
        saved_name: "saved-set",
        saved_snapshot: "old snapshot",
      },
      "2": { style_prompt: "second prompt", loras: [] },
    }) }],
  ]);
  return {
    widgets,
    dirty: 0,
    __easyuseAnimaProfileBar: { scrollOffset: 0 },
    setDirtyCanvas() { this.dirty += 1; },
  };
}

const renderCalls = { profile: 0, loras: 0 };
const canvasWidgets = {
  profileVisibleRows: 2,
  renderProfileBar() { renderCalls.profile += 1; },
  renderLoraWidgets() { renderCalls.loras += 1; },
};
const host = { alerts: [], confirm: () => true, alert(message) { this.alerts.push(message); } };
const findWidget = (node, name) => node.widgets.get(name);
const widgetValue = (widget, fallback) => widget?.value ?? fallback;
const setWidgetValue = (widget, value) => { widget.value = value; };
const lorasWidgetValue = (node) => JSON.parse(widgetValue(findWidget(node, "loras"), "[]"));
const setLorasWidgetValue = (node, loras) => {
  setWidgetValue(findWidget(node, "loras"), JSON.stringify(loras));
};
const mutations = createLoraPresetProfileMutations({
  findWidget,
  widgetValue,
  setWidgetValue,
  lorasWidgetValue,
  setLorasWidgetValue,
  getCanvasWidgets: () => canvasWidgets,
  text: (key) => key,
  formatText: (key) => key,
  apiClient: {},
  host,
});

const node = createProfileNode();
mutations.mutateLoras(node, (loras) => { loras[0].strength = 0.75; });
let profileData = mutations.parseProfileData(findWidget(node, "profile_data"));
assert.equal(profileData["1"].loras[0].strength, 0.75);
assert.equal(profileData["1"].saved_name, "saved-set");
assert.equal(profileData["1"].saved_snapshot, "old snapshot");

mutations.switchProfile(node, 2);
assert.equal(widgetValue(findWidget(node, "style_prompt")), "second prompt");
mutations.addLoraEntry(node, { name: "second.safetensors", strength: 0.5 });
profileData = mutations.parseProfileData(findWidget(node, "profile_data"));
assert.equal(profileData["2"].loras[0].name, "second.safetensors");
mutations.deleteProfile(node, 1);
assert.equal(mutations.profileCount(node), 1);
assert.equal(widgetValue(findWidget(node, "style_prompt")), "second prompt");
assert.ok(renderCalls.profile > 0);

const syncCalls = [];
const graphPrototype = {
  serialize(value) {
    if (value === "throw") {
      throw new Error("serialize failure");
    }
    return { receiver: this, value };
  },
};
const graph = { _nodes: [{ comfyClass: "EasyUseAnimaLoraPreset", id: 1 }, { comfyClass: "Other", id: 2 }] };
const secondaryGraph = { _nodes: [{ comfyClass: "EasyUseAnimaLoraPreset", id: 3 }] };
const pendingResult = Promise.resolve({ queued: true });
const rejectedResult = Promise.reject(new Error("queue failure"));
const app = {
  graph,
  queuePrompt(value) {
    if (value === "throw") {
      throw new Error("queue throw");
    }
    if (value === "promise") {
      return pendingResult;
    }
    if (value === "reject") {
      return rejectedResult;
    }
    return { receiver: this, value };
  },
};
const saveSync = createLoraPresetSaveSync({
  app,
  nodeTypeName: "EasyUseAnimaLoraPreset",
  saveCurrentProfile: (profileNode) => syncCalls.push(profileNode.id),
  getGraphPrototype: () => graphPrototype,
});
saveSync.install();
saveSync.install();
const serialized = graphPrototype.serialize.call(secondaryGraph, "serialize-value");
const queued = app.queuePrompt.call(app, "queue-value");
assert.deepEqual(syncCalls, [3, 1]);
assert.strictEqual(serialized.receiver, secondaryGraph);
assert.equal(serialized.value, "serialize-value");
assert.strictEqual(queued.receiver, app);
assert.equal(queued.value, "queue-value");

const previousSerialize = graphPrototype.serialize;
let serializeWrapperThis = null;
let serializeWrapperArgs = null;
graphPrototype.serialize = function () {
  serializeWrapperThis = this;
  serializeWrapperArgs = [...arguments];
  return previousSerialize.apply(this, arguments);
};
const previousQueuePrompt = app.queuePrompt;
let queueWrapperThis = null;
let queueWrapperArgs = null;
app.queuePrompt = function () {
  queueWrapperThis = this;
  queueWrapperArgs = [...arguments];
  return previousQueuePrompt.apply(this, arguments);
};

saveSync.install();
saveSync.install();
syncCalls.length = 0;
const reinstalledSerialized = graphPrototype.serialize.call(secondaryGraph, "reinstall-value");
const reinstalledQueued = app.queuePrompt.call(app, "reinstall-queue");
assert.deepEqual(syncCalls, [3, 1], "reinstall must not stack stale synchronization wrappers");
assert.strictEqual(serializeWrapperThis, secondaryGraph);
assert.deepEqual(serializeWrapperArgs, ["reinstall-value"]);
assert.strictEqual(reinstalledSerialized.receiver, secondaryGraph);
assert.strictEqual(queueWrapperThis, app);
assert.deepEqual(queueWrapperArgs, ["reinstall-queue"]);
assert.strictEqual(reinstalledQueued.receiver, app);

assert.throws(() => graphPrototype.serialize.call(secondaryGraph, "throw"), /serialize failure/);
assert.throws(() => app.queuePrompt.call(app, "throw"), /queue throw/);
const returnedPromise = app.queuePrompt.call(app, "promise");
assert.strictEqual(returnedPromise, pendingResult);
assert.deepEqual(await returnedPromise, { queued: true });
const returnedRejection = app.queuePrompt.call(app, "reject");
assert.strictEqual(returnedRejection, rejectedResult);
await assert.rejects(returnedRejection, /queue failure/);

console.log("LoRA profile mutation and save-sync smoke passed");
