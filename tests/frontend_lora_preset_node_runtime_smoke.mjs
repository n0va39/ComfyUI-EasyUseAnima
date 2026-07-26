import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

function dataModule(relativePath) {
  const source = readFileSync(new URL(relativePath, import.meta.url), "utf8");
  return `data:text/javascript;base64,${Buffer.from(source).toString("base64")}`;
}

const { createLoraPresetNodeRuntime } = await import(
  dataModule("../web/js/lora_preset/node_runtime.js"),
);

const events = [];
const animationFrames = [];
const widgetIndex = {
  profileIndex: 1,
  profileCount: 2,
  loraName: 3,
  loras: 4,
  profileData: 5,
};
const internalWidgetDefaults = {
  profile_count: "4",
  lora_name: "None",
  loras: "[]",
  profile_data: "{}",
};

function findWidget(node, name) {
  return node.__easyuseAnimaHiddenWidgets?.[name]
    || node.widgets?.find((widget) => widget.name === name);
}

function widgetValue(widget, fallback = "") {
  return widget?.value ?? fallback;
}

function ensureWidgetValue(node, name) {
  const widget = findWidget(node, name);
  if (widget && (widget.value == null || widget.value === "")) {
    widget.value = internalWidgetDefaults[name];
  }
}

function resetInternalLoraSelector(node) {
  const widget = findWidget(node, "lora_name");
  if (widget) {
    widget.value = internalWidgetDefaults.lora_name;
  }
}

function profileCount(node) {
  return Number.parseInt(widgetValue(findWidget(node, "profile_count"), "4"), 10) || 4;
}

function selectedProfileIndex(node) {
  return Number.parseInt(widgetValue(findWidget(node, "profile_index"), 1), 10) || 1;
}

function activeProfileIndex(node) {
  return node.__easyuseAnimaActiveProfileIndex || selectedProfileIndex(node);
}

function wrapProfileIndex(index, count) {
  return ((Number(index) - 1) % count + count) % count + 1;
}

const canvasWidgets = {
  ensureProfileBar(node) { events.push(`bar:${node.id}`); },
  renderProfileBar(node) { events.push(`profile:${node.id}`); },
  renderLoraWidgets(node) { events.push(`loras:${node.id}`); },
};

const runtime = createLoraPresetNodeRuntime({
  nodeTypeName: "EasyUseAnimaLoraPreset",
  internalWidgetDefaults,
  widgetIndex,
  findWidget,
  findInputEl: () => null,
  widgetValue,
  ensureWidgetValue,
  resetInternalLoraSelector,
  normalizeSerializedWidgets(info) { events.push("normalize"); info.normalized = true; },
  profileCount,
  selectedProfileIndex,
  activeProfileIndex,
  wrapProfileIndex,
  setProfileIndex(node, index) {
    events.push(`set:${index}`);
    findWidget(node, "profile_index").value = index;
  },
  lorasWidgetValue: () => [{ name: "styles/example.safetensors", on: true, strength: 1 }],
  saveProfile(node, index) { events.push(`save:${node.id}:${index}`); },
  saveCurrentProfile(node) { events.push(`save-current:${node.id}`); },
  loadProfile(node, index, options) { events.push(`load:${node.id}:${index}:${Boolean(options?.initializeFromCurrent)}`); },
  verifyProfileProvenance(node) { events.push(`verify:${node.id}`); },
  scrollProfileBarTo(node, index) { events.push(`scroll:${node.id}:${index}`); },
  refreshLoraAvailability(node) { events.push(`availability:${node.id}`); },
  canvasWidgets,
  enforceNodeLayout(node) { events.push(`layout:${node.id}`); },
  requestAnimationFrame(callback) { animationFrames.push(callback); },
});

function makeWidget(name, value) {
  return { name, value };
}

function makeNode(id) {
  return Object.assign(new NodeType(), {
    id,
    widgets: [
      makeWidget("style_prompt", "style"),
      makeWidget("profile_index", 1),
      makeWidget("profile_count", "4"),
      makeWidget("lora_name", "legacy"),
      makeWidget("loras", "[]"),
      makeWidget("profile_data", "{}"),
    ],
    inputs: [],
    addInput(name, type) { this.inputs.push({ name, type }); },
    setDirtyCanvas() { events.push(`dirty:${this.id}`); },
  });
}

function NodeType() {}
NodeType.prototype.configure = function (info) {
  events.push(`configure:${this.id}:${info.normalized}:${this.widgets.map((widget) => widget.name).join(",")}`);
  return "configured";
};
NodeType.prototype.onNodeCreated = function () {
  events.push(`created:${this.id}`);
  return "created-result";
};
NodeType.prototype.onConfigure = function () {
  events.push(`node-configure:${this.id}`);
};
NodeType.prototype.onExecuted = function () {
  events.push(`executed:${this.id}`);
};
NodeType.prototype.onSerialize = function () {
  events.push(`serialized:${this.id}`);
};

runtime.beforeRegisterNodeDef(NodeType, { name: "OtherNode" });
assert.equal(NodeType.prototype.configure.name, "");
runtime.beforeRegisterNodeDef(NodeType, { name: "EasyUseAnimaLoraPreset" });

const node = makeNode("node-a");
assert.equal(node.onNodeCreated(), "created-result");
assert.equal(node.onNodeCreated(), "created-result");
assert.deepEqual(node.inputs, [{ name: "lora_stack", type: "LORA_STACK" }]);
assert.equal(animationFrames.length, 1);
assert.equal(node.serialize_widgets, true);
assert.equal(node.widgets.filter((widget) => widget.__easyuseAnimaLoraWrapped).length, 4);

animationFrames.shift()();
assert.ok(events.includes("verify:node-a"));
assert.deepEqual(node.widgets.map((widget) => widget.name), [
  "style_prompt", "profile_index", "profile_count", "lora_name", "loras", "profile_data",
]);
for (const index of [2, 3, 4, 5]) {
  assert.equal(node.widgets[index].hidden, true);
  assert.equal(node.widgets[index].serialize, true);
  assert.equal(node.widgets[index].options.hidden, true);
}

node.widgets.splice(3, 0, { name: "easyuse_anima_profile_bar", value: null, serialize: false });
const serialized = { widgets_values: ["", 1, "4", null, "legacy", "[]", "{}"] };
node.onSerialize(serialized);
assert.deepEqual(serialized.widgets_values, [
  "",
  1,
  "4",
  "None",
  JSON.stringify([{ name: "styles/example.safetensors", on: true, strength: 1 }]),
  "{}",
]);
assert.equal(serialized.widgets_values.length, 6);
assert.ok(events.indexOf("save-current:node-a") < events.indexOf("serialized:node-a"));

node.widgets = [node.widgets[0], node.widgets[1]];
const configureResult = node.configure({ widgets_values: [], normalized: false });
assert.equal(configureResult, "configured");
assert.deepEqual(node.widgets.map((widget) => widget.name), [
  "style_prompt", "profile_index", "profile_count", "lora_name", "loras", "profile_data",
]);
assert.deepEqual(node.widgets.slice(2).map((widget) => widget.hidden), [true, true, true, true]);
assert.ok(events.indexOf("normalize") < events.findIndex((event) => event.startsWith("configure:node-a:true:")));
node.onConfigure();
assert.equal(animationFrames.length, 1);
assert.ok(events.includes("node-configure:node-a"));
animationFrames.shift()();

events.length = 0;
node.onExecuted({ lora_preset_profile: [{ profile_index: 2 }] });
assert.deepEqual(events, ["executed:node-a"]);
assert.equal(node.__easyuseAnimaActiveProfileIndex, 1);

// Simulate a real user profile switch after the queued snapshot was captured.
findWidget(node, "profile_index").value = 2;
findWidget(node, "profile_index").callback();
assert.equal(node.__easyuseAnimaActiveProfileIndex, 2);
findWidget(node, "style_prompt").value = "new unsaved style";
findWidget(node, "loras").value = JSON.stringify([{
  name: "styles/new.safetensors",
  on: false,
  strength: 0.25,
}]);
const preservedWidgets = node.widgets.map((widget) => widget.value);

events.length = 0;
node.onExecuted({ lora_preset_profile: [{ profile_index: 2 }] });
assert.deepEqual(events, ["executed:node-a"]);
assert.equal(node.__easyuseAnimaActiveProfileIndex, 2);
assert.deepEqual(node.widgets.map((widget) => widget.value), preservedWidgets);

// Profile 1 was queued before the user switched to and edited profile 2. The
// stale result remains execution metadata and cannot replay profile 1 into the
// current editor.
events.length = 0;
node.onExecuted({ lora_preset_profile: [{ profile_index: 1 }] });
assert.deepEqual(events, ["executed:node-a"]);
assert.equal(node.__easyuseAnimaActiveProfileIndex, 2);
assert.deepEqual(node.widgets.map((widget) => widget.value), preservedWidgets);
