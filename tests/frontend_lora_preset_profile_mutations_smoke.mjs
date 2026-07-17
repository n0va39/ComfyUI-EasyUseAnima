import assert from "node:assert/strict";
import { createLoraPresetProfileMutations } from "../web/js/lora_preset/profile_mutations.js";
import {
  INTERNAL_WIDGET_DEFAULTS,
  MAX_PROFILES,
  WIDGET_INDEX,
} from "../web/js/lora_preset/profile_data.js";
import { createLoraPresetNodeRuntime } from "../web/js/lora_preset/node_runtime.js";
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

const apiCalls = { save: [], load: [] };
const apiMutations = createLoraPresetProfileMutations({
  findWidget,
  widgetValue,
  setWidgetValue,
  lorasWidgetValue,
  setLorasWidgetValue,
  getCanvasWidgets: () => canvasWidgets,
  text: (key) => key,
  formatText: (key) => key,
  apiClient: {
    async saveProfile(name, payload) {
      apiCalls.save.push({ name, payload });
      return { profile: { name } };
    },
    async loadProfile(name) {
      apiCalls.load.push(name);
      return {
        profile: {
          name,
          profile_count: 2,
          profile_index: 2,
          profile_data: {
            "1": { style_prompt: "loaded first", loras: [] },
            "2": { style_prompt: "loaded second", loras: [{ name: "loaded.safetensors" }] },
          },
        },
      };
    },
  },
  host: { ...host, prompt: () => " saved profile " },
});
await apiMutations.saveProfileSet(node);
assert.equal(apiCalls.save[0].name, "saved profile");
assert.equal(apiCalls.save[0].payload.profile_count, 1);
assert.equal(apiMutations.profileSaveStatus(node, 1).state, "saved");
await apiMutations.loadProfileSet(node, "loaded profile");
assert.deepEqual(apiCalls.load, ["loaded profile"]);
assert.equal(apiMutations.profileCount(node), 3);
assert.equal(apiMutations.activeProfileIndex(node), 3);
assert.equal(widgetValue(findWidget(node, "style_prompt")), "loaded second");

const partialNode = createProfileNode();
while (mutations.profileCount(partialNode) < MAX_PROFILES - 1) {
  mutations.addProfile(partialNode);
}
host.alerts.length = 0;
mutations.appendProfilePayload(partialNode, {
  profile_count: 2,
  profile_index: 2,
  profile_data: {
    "1": { style_prompt: "partial first", loras: [] },
    "2": { style_prompt: "partial second", loras: [] },
  },
});
assert.equal(mutations.profileCount(partialNode), MAX_PROFILES);
assert.equal(widgetValue(findWidget(partialNode, "style_prompt")), "partial first");
assert.equal(host.alerts.at(-1), "profile.partialLoad");
mutations.appendProfilePayload(partialNode, {
  profile_count: 1,
  profile_data: { "1": { style_prompt: "ignored", loras: [] } },
});
assert.equal(host.alerts.at(-1), "profile.maxReached");

function createWorkflowNode() {
  return {
    id: "workflow-node",
    comfyClass: "EasyUseAnimaLoraPreset",
    widgets: [
      { name: "style_prompt", value: "" },
      { name: "profile_index", value: 1 },
      { name: "profile_count", value: "2" },
      { name: "lora_name", value: "None" },
      { name: "loras", value: "[]" },
      { name: "profile_data", value: JSON.stringify({
        "1": { style_prompt: "profile-alpha", loras: [] },
        "2": { style_prompt: "profile-beta", loras: [] },
      }) },
    ],
    inputs: [],
    addInput(name, type) { this.inputs.push({ name, type }); },
    setDirtyCanvas() {},
  };
}

const workflowFindWidget = (profileNode, name) => profileNode.__easyuseAnimaHiddenWidgets?.[name]
  || profileNode.widgets.find((widget) => widget.name === name);
const workflowWidgetValue = (widget, fallback) => widget?.value ?? fallback;
const workflowSetWidgetValue = (widget, value) => {
  widget.value = value;
  widget.callback?.(value);
};
const workflowLoras = (profileNode) => JSON.parse(workflowWidgetValue(workflowFindWidget(profileNode, "loras"), "[]"));
const workflowSetLoras = (profileNode, loras) => {
  workflowSetWidgetValue(workflowFindWidget(profileNode, "loras"), JSON.stringify(loras));
};
const workflowCanvasWidgets = {
  profileVisibleRows: 2,
  ensureProfileBar() {},
  renderProfileBar() {},
  renderLoraWidgets() {},
};
const workflowMutations = createLoraPresetProfileMutations({
  findWidget: workflowFindWidget,
  widgetValue: workflowWidgetValue,
  setWidgetValue: workflowSetWidgetValue,
  lorasWidgetValue: workflowLoras,
  setLorasWidgetValue: workflowSetLoras,
  getCanvasWidgets: () => workflowCanvasWidgets,
  text: (key) => key,
  formatText: (key) => key,
  apiClient: {},
  host: { confirm: () => true },
});
function WorkflowNodeType() {}
const workflowRuntime = createLoraPresetNodeRuntime({
  nodeTypeName: "EasyUseAnimaLoraPreset",
  internalWidgetDefaults: INTERNAL_WIDGET_DEFAULTS,
  widgetIndex: WIDGET_INDEX,
  findWidget: workflowFindWidget,
  findInputEl: () => null,
  widgetValue: workflowWidgetValue,
  ensureWidgetValue(profileNode, name) {
    const widget = workflowFindWidget(profileNode, name);
    if (widget && (widget.value == null || widget.value === "")) {
      workflowSetWidgetValue(widget, INTERNAL_WIDGET_DEFAULTS[name]);
    }
  },
  resetInternalLoraSelector(profileNode) {
    workflowSetWidgetValue(workflowFindWidget(profileNode, "lora_name"), INTERNAL_WIDGET_DEFAULTS.lora_name);
  },
  normalizeSerializedWidgets() {},
  profileCount: workflowMutations.profileCount,
  selectedProfileIndex: workflowMutations.selectedProfileIndex,
  activeProfileIndex: workflowMutations.activeProfileIndex,
  wrapProfileIndex(index, count) { return ((Number(index) - 1) % count + count) % count + 1; },
  setProfileIndex: workflowMutations.setProfileIndex,
  lorasWidgetValue: workflowLoras,
  saveProfile: workflowMutations.saveProfile,
  saveCurrentProfile: workflowMutations.saveCurrentProfile,
  loadProfile: workflowMutations.loadProfile,
  scrollProfileBarTo: workflowMutations.scrollProfileBarTo,
  refreshLoraAvailability() {},
  canvasWidgets: workflowCanvasWidgets,
  enforceNodeLayout() {},
  requestAnimationFrame(callback) { callback(); },
});
workflowRuntime.beforeRegisterNodeDef(WorkflowNodeType, { name: "EasyUseAnimaLoraPreset" });
const workflowNode = Object.assign(new WorkflowNodeType(), createWorkflowNode());
workflowNode.onNodeCreated();
assert.equal(workflowWidgetValue(workflowFindWidget(workflowNode, "style_prompt")), "profile-alpha");
workflowMutations.addProfile(workflowNode);
assert.equal(workflowMutations.activeProfileIndex(workflowNode), 3);
workflowMutations.switchProfile(workflowNode, 1);
assert.equal(workflowWidgetValue(workflowFindWidget(workflowNode, "style_prompt")), "profile-alpha");
workflowMutations.switchProfile(workflowNode, 3);
workflowMutations.deleteProfile(workflowNode, 3);
assert.equal(workflowMutations.activeProfileIndex(workflowNode), 2);
assert.equal(workflowMutations.profileCount(workflowNode), 2);
assert.equal(workflowWidgetValue(workflowFindWidget(workflowNode, "style_prompt")), "profile-beta");

// The canvas-owned active index is authoritative even when a property-panel
// snapshot still exposes the deleted profile index.
workflowFindWidget(workflowNode, "profile_index").value = 3;
const workflowGraphPrototype = {
  serialize() {
    const workflowNodeSnapshot = {
      widgets_values: ["profile-alpha", 3, "3", "None", "[]", JSON.stringify({
        "1": { style_prompt: "profile-alpha", loras: [] },
        "2": { style_prompt: "profile-beta", loras: [] },
        "3": { style_prompt: "", loras: [] },
      })],
    };
    workflowNode.onSerialize(workflowNodeSnapshot);
    return workflowNodeSnapshot;
  },
};
const workflowGraph = { _nodes: [workflowNode] };
const workflowSaveSync = createLoraPresetSaveSync({
  app: { graph: workflowGraph, queuePrompt() {} },
  nodeTypeName: "EasyUseAnimaLoraPreset",
  saveCurrentProfile: workflowMutations.saveCurrentProfile,
  getGraphPrototype: () => workflowGraphPrototype,
});
workflowSaveSync.install();
const savedWorkflowNode = workflowGraphPrototype.serialize.call(workflowGraph);
assert.equal(savedWorkflowNode.widgets_values[WIDGET_INDEX.profileIndex], 2);
assert.equal(savedWorkflowNode.widgets_values[WIDGET_INDEX.profileCount], "2");
const savedProfileData = JSON.parse(savedWorkflowNode.widgets_values[WIDGET_INDEX.profileData]);
assert.deepEqual(Object.keys(savedProfileData), ["1", "2"]);
assert.equal(savedProfileData["1"].style_prompt, "profile-alpha");
assert.equal(savedProfileData["2"].style_prompt, "profile-beta");

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

const replacementSaveSync = createLoraPresetSaveSync({
  app,
  nodeTypeName: "EasyUseAnimaLoraPreset",
  saveCurrentProfile: (profileNode) => syncCalls.push(profileNode.id),
  getGraphPrototype: () => graphPrototype,
});
replacementSaveSync.install();
replacementSaveSync.install();
syncCalls.length = 0;
const reinstalledSerialized = graphPrototype.serialize.call(secondaryGraph, "reinstall-value");
const reinstalledQueued = app.queuePrompt.call(app, "reinstall-queue");
assert.deepEqual(syncCalls, [3, 1], "new lifecycle installation must not stack stale synchronization wrappers");
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
