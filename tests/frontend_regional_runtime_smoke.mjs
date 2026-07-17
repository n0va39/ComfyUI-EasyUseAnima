import { readFileSync } from "node:fs";

function dataModule(relativePath, replacements = {}) {
  let source = readFileSync(new URL(relativePath, import.meta.url), "utf8");
  for (const [specifier, replacement] of Object.entries(replacements)) {
    source = source.replaceAll(`"${specifier}"`, `"${replacement}"`);
  }
  return `data:text/javascript;base64,${Buffer.from(source).toString("base64")}`;
}

function assert(condition, message) {
  if (!condition) {
    throw new Error(message);
  }
}

let nextFrame = 1;
const frames = new Map();
const cancelledFrames = new Set();
globalThis.requestAnimationFrame = (callback) => {
  const id = nextFrame++;
  frames.set(id, callback);
  return id;
};
globalThis.cancelAnimationFrame = (id) => {
  cancelledFrames.add(id);
  frames.delete(id);
};

function flushFrames() {
  const queued = [...frames.entries()];
  frames.clear();
  for (const [, callback] of queued) {
    callback();
  }
}

const constantsUrl = dataModule("../web/js/prompt_studio/regional/constants.js");
const wildcardSeedContractUrl = dataModule(
  "../web/js/prompt_studio/wildcard_seed_contract.js",
);
const maskGeometryUrl = dataModule("../web/js/prompt_studio/regional/mask_geometry.js");
const resolutionUrl = dataModule("../web/js/prompt_studio/regional/resolution.js", {
  "./constants.js": constantsUrl,
});
const schemaUrl = dataModule("../web/js/prompt_studio/regional/schema.js", {
  "./constants.js": constantsUrl,
  "./mask_geometry.js": maskGeometryUrl,
  "./resolution.js": resolutionUrl,
});
const serializationUrl = dataModule("../web/js/prompt_studio/regional/serialization.js", {
  "./constants.js": constantsUrl,
  "./schema.js": schemaUrl,
});
const queueSeedBridgeUrl = dataModule("../web/js/prompt_studio/queue_seed_bridge.js");
const autocompleteEntryLifecycleUrl = dataModule(
  "../web/js/autocomplete/entry_lifecycle.js",
);
const lifecycleUrl = dataModule("../web/js/prompt_studio/regional/lifecycle.js");
const layoutUrl = dataModule("../web/js/prompt_studio/regional/layout.js", {
  "./lifecycle.js": lifecycleUrl,
});
const extensionUrl = dataModule("../web/js/prompt_studio/regional/extension.js", {
  "./constants.js": constantsUrl,
  "./lifecycle.js": lifecycleUrl,
  "./layout.js": layoutUrl,
  "../queue_seed_bridge.js": queueSeedBridgeUrl,
  "../../autocomplete/entry_lifecycle.js": autocompleteEntryLifecycleUrl,
});
const regionalRuntimeUrl = dataModule("../web/js/prompt_studio/regional/runtime.js", {
  "./constants.js": constantsUrl,
  "./resolution.js": resolutionUrl,
  "./schema.js": schemaUrl,
  "./serialization.js": serializationUrl,
});
const fieldEditorUrl = dataModule("../web/js/prompt_studio/regional/field_editor.js", {
  "./constants.js": constantsUrl,
  "./resolution.js": resolutionUrl,
  "./schema.js": schemaUrl,
  "./lifecycle.js": lifecycleUrl,
  "../wildcard_seed_contract.js": wildcardSeedContractUrl,
  "../../autocomplete/entry_lifecycle.js": autocompleteEntryLifecycleUrl,
});

const lifecycle = await import(lifecycleUrl);
const extension = await import(extensionUrl);
const fieldEditor = await import(fieldEditorUrl);
const queueSeedBridgeModule = await import(queueSeedBridgeUrl);
const regionalRuntimeModule = await import(regionalRuntimeUrl);

const lifecycleNode = {};
lifecycle.activateRegionalNodeLifecycle(lifecycleNode);
let frameRuns = 0;
const originalFrame = lifecycle.scheduleRegionalNodeFrame(
  lifecycleNode,
  "layout",
  () => { frameRuns += 1; },
);
assert(
  lifecycle.scheduleRegionalNodeFrame(lifecycleNode, "layout", () => {}) === originalFrame,
  "A duplicate node frame was scheduled",
);
const replacementFrame = lifecycle.scheduleRegionalNodeFrame(
  lifecycleNode,
  "layout",
  () => { frameRuns += 10; },
  { replace: true },
);
assert(replacementFrame !== originalFrame, "A replaced node frame kept the stale id");
assert(cancelledFrames.has(originalFrame), "Replacing a node frame did not cancel the stale callback");

let cleanupRuns = 0;
lifecycle.setRegionalNodeCleanup(lifecycleNode, "popover", () => { cleanupRuns += 1; });
lifecycle.setRegionalNodeCleanup(lifecycleNode, "popover", () => { cleanupRuns += 10; });
assert(cleanupRuns === 1, "Replacing a node resource did not clean the previous resource");
lifecycle.disposeRegionalNodeLifecycle(lifecycleNode);
assert(cleanupRuns === 11, "Node removal did not run the current resource cleanup");
assert(cancelledFrames.has(replacementFrame), "Node removal did not cancel its animation frame");
flushFrames();
assert(frameRuns === 0, "A disposed node callback ran after removal");
assert(
  lifecycle.scheduleRegionalNodeFrame(lifecycleNode, "late", () => {}) === 0,
  "A disposed node accepted a new animation frame",
);

const fields = [
  { id: "p1", pane: "positive" },
  { id: "n1", pane: "negative" },
  { id: "p2", pane: "positive" },
  { id: "n2", pane: "negative" },
];
assert(
  fieldEditor.moveRegionalFieldInPane(fields, "p2", -1),
  "Regional field did not move within its pane",
);
assert(fields.map((field) => field.id).join(",") === "p2,n1,p1,n2", "Field move crossed pane identity");
assert(
  !fieldEditor.moveRegionalFieldInPane(fields, "p2", -1),
  "First field moved past its pane boundary",
);

const originalThis = [];
const returns = {
  created: Symbol("created"),
  configured: Symbol("configured"),
  resized: Symbol("resized"),
  connected: Symbol("connected"),
  serialized: Symbol("serialized"),
  executed: Symbol("executed"),
  removed: Symbol("removed"),
};
function RegionalNodeType() {}
for (const [name, value] of Object.entries({
  onNodeCreated: returns.created,
  onConfigure: returns.configured,
  onResize: returns.resized,
  onConnectionsChange: returns.connected,
  onSerialize: returns.serialized,
  onExecuted: returns.executed,
  onRemoved: returns.removed,
})) {
  RegionalNodeType.prototype[name] = function () {
    originalThis.push([name, this]);
    return value;
  };
}

const hookCalls = [];
const hooks = {
  attachQueueSeedNode: (node) => hookCalls.push(["attach", node]),
  applyRegionalExecutedInputs: (node) => hookCalls.push(["executed", node]),
  captureRegionalConfigure: (node) => hookCalls.push(["configure", node]),
  disposeRegionalNode: (node) => {
    hookCalls.push(["dispose", node]);
    lifecycle.disposeRegionalNodeLifecycle(node);
  },
  pruneDisconnectedRegionalFieldInputValues: (node) => hookCalls.push(["prune", node]),
  removeRegionalInternalInputSockets: (node) => hookCalls.push(["remove-inputs", node]),
  renderRegionalEditor: (node) => hookCalls.push(["render", node]),
  scheduleHookRegionalNode: (node) => hookCalls.push(["hook", node]),
  scheduleRegionalLayout: (node) => hookCalls.push(["layout", node]),
  syncRegionalValues: (node) => hookCalls.push(["serialize", node]),
};
assert(extension.registerRegionalNodeHooks(RegionalNodeType, hooks), "Regional hooks were not installed");
assert(!extension.registerRegionalNodeHooks(RegionalNodeType, hooks), "Regional hooks installed twice");

const node = new RegionalNodeType();
lifecycle.activateRegionalNodeLifecycle(node);
assert(node.onNodeCreated() === returns.created, "onNodeCreated return value changed");
assert(node.onConfigure({}) === returns.configured, "onConfigure return value changed");
assert(node.onResize([640, 900]) === returns.resized, "onResize return value changed");
assert(node.onConnectionsChange() === returns.connected, "onConnectionsChange return value changed");
assert(node.onSerialize({}) === returns.serialized, "onSerialize return value changed");
assert(node.onExecuted({}) === returns.executed, "onExecuted return value changed");
assert(node.onRemoved() === returns.removed, "onRemoved return value changed");
assert(originalThis.every(([, value]) => value === node), "A Regional wrapper changed original this");
flushFrames();
assert(!hookCalls.some(([name]) => name === "render"), "Connection callback ran after node removal");
assert(hookCalls.filter(([name]) => name === "attach").length === 1, "Configure did not attach Regional queue state");
assert(hookCalls.filter(([name]) => name === "dispose").length === 1, "Node removal cleanup count changed");

const runtimeApp = {
  graph: {
    links: {},
    setDirtyCanvas() {},
  },
};
const regionalRuntime = regionalRuntimeModule.createRegionalRuntime(runtimeApp);
const guardedNode = {
  widgets: [
    { name: "regional_fields", value: "[]" },
    { name: "regional_config", value: "{}" },
    { name: "resolution_bucket", value: "1024" },
    { name: "resolution_size", value: "1024 * 1024 (1:1)" },
    { name: "resolution_custom_width", value: 1024 },
    { name: "resolution_custom_height", value: 1024 },
    { name: "wildcard_mode", value: "고정" },
    { name: "wildcard_seed", value: 30 },
    { name: "wildcard_seed_after_generate", value: "fixed" },
  ],
  inputs: [],
  properties: {},
  addInput(name, type) {
    this.inputs.push({ name, type, link: null });
  },
  removeInput(index) {
    this.inputs.splice(index, 1);
  },
  setDirtyCanvas() {},
};
const executedPayload = {
  prompt_studio_regional: [{
    regional_fields: [{
      id: "p1",
      pane: "positive",
      type: "general",
      label: "General",
      text: "queued field",
      enabled: true,
    }],
    regional_config: { masks: [], next_mask_id: 1 },
    field_inputs: { field_p1: "linked field" },
    wildcard_mode: "일반 채우기",
    wildcard_seed: 8,
    wildcard_seed_after_generate: "randomize",
  }],
};
assert(
  regionalRuntime.applyRegionalExecutedInputs(guardedNode, executedPayload, {
    shouldApplyExecutedSeed: () => false,
  }),
  "Regional executed payload was not applied",
);
assert(
  regionalRuntime.findWidget(guardedNode, "wildcard_seed").value === 30,
  "A stale Regional executed seed replaced shared runtime authority",
);
assert(
  regionalRuntime.findWidget(guardedNode, "wildcard_mode").value === "일반 채우기",
  "Regional executed mode was blocked with the stale seed",
);
assert(
  regionalRuntime.findWidget(guardedNode, "wildcard_seed_after_generate").value === "randomize",
  "Regional executed control was blocked with the stale seed",
);
assert(
  guardedNode.__easyuseAnimaRegionalFieldInputValues.field_p1 === "linked field",
  "Regional executed field inputs were blocked with the stale seed",
);
assert(
  regionalRuntime.applyRegionalExecutedInputs(
    guardedNode,
    { prompt_studio_regional: [{ wildcard_seed: 31 }] },
    { shouldApplyExecutedSeed: () => true },
  ),
  "An authoritative Regional executed seed payload was not applied",
);
assert(
  regionalRuntime.findWidget(guardedNode, "wildcard_seed").value === 31,
  "An authoritative Regional executed seed stayed blocked",
);

const bridgeApp = { graph: { _nodes: [] } };
const bridge = queueSeedBridgeModule.promptStudioQueueSeedBridge(bridgeApp);
const bridgeCalls = [];
bridge.bindRuntime({
  attachNode(node) {
    bridgeCalls.push(["attach", node]);
    return true;
  },
  detachNode(node) {
    bridgeCalls.push(["detach", node]);
    return true;
  },
  shouldApplyExecutedSeed(node, value) {
    bridgeCalls.push(["guard", node, value]);
    return false;
  },
});
const bridgeRuntime = {
  applyRegionalExecutedInputs(node, message, options) {
    bridgeCalls.push([
      "executed",
      node,
      message,
      options.shouldApplyExecutedSeed(node, message.seed),
    ]);
    return true;
  },
  captureRegionalConfigure() {},
  isRegionalNode: (node) => node?.type === "EasyUseAnimaPromptStudioRegional",
  pruneDisconnectedRegionalFieldInputValues() {},
  removeRegionalInternalInputSockets() {},
  repairRegionalConditioningWidgets() {},
  setRegionalWidgetValue(node, name, value) {
    bridgeCalls.push(["publish", node, name, value]);
    return true;
  },
  syncRegionalValues() {},
};
const bridgeFieldEditor = {
  collectRegionalEditorFields: () => [],
  renderRegionalEditor: (node) => bridgeCalls.push(["render", node]),
};
const bridgeExtension = extension.createRegionalExtensionRuntime(
  bridgeApp,
  bridgeRuntime,
  {
    regionalEditorMinimumHeight: () => 0,
    regionalEditorWidgetHeight: () => 0,
    scheduleRegionalLayout() {},
  },
  bridgeFieldEditor,
  {
    ensureRegionalStyle() {},
    installRegionalAdapter() {},
  },
);
function BridgeRegionalNodeType() {}
await bridgeExtension.beforeRegisterNodeDef(BridgeRegionalNodeType, {
  name: "EasyUseAnimaPromptStudioRegional",
});
const bridgeNode = Object.assign(new BridgeRegionalNodeType(), {
  type: "EasyUseAnimaPromptStudioRegional",
});
bridgeNode.onConfigure({});
bridgeNode.onExecuted({ seed: 8 });
assert(bridge.publishRegionalSeed(bridgeNode, 9), "Regional live seed publisher was not bound");
bridgeNode.onRemoved();
assert(
  bridgeCalls.some(([name, target]) => name === "attach" && target === bridgeNode),
  "Regional configure did not reach the shared runtime owner",
);
assert(
  bridgeCalls.some(([name, target, value]) => name === "guard" && target === bridgeNode && value === 8),
  "Regional onExecuted did not use the shared authority guard",
);
assert(
  bridgeCalls.some(([name, target]) => name === "detach" && target === bridgeNode),
  "Regional removal did not detach shared queue state",
);
assert(
  bridgeCalls.some(([name, target, widgetName, value]) => (
    name === "publish"
    && target === bridgeNode
    && widgetName === "wildcard_seed"
    && value === 9
  )),
  "Accepted Regional seed did not publish through the Regional runtime",
);

function ConditioningNodeType() {}
const conditioningReturn = Symbol("conditioning");
ConditioningNodeType.prototype.onNodeCreated = function () { return conditioningReturn; };
let conditioningRepairs = 0;
assert(
  extension.registerRegionalConditioningNodeHooks(
    ConditioningNodeType,
    () => { conditioningRepairs += 1; },
  ),
  "Conditioning hooks were not installed",
);
assert(
  new ConditioningNodeType().onNodeCreated() === conditioningReturn,
  "Conditioning hook return value changed",
);
assert(conditioningRepairs === 1, "Conditioning repair hook did not run once");
assert(
  !extension.registerRegionalConditioningNodeHooks(ConditioningNodeType, () => {}),
  "Conditioning hooks installed twice",
);

class Graph {
  serialize(value) {
    return { owner: this, value };
  }
}
globalThis.LGraph = Graph;
const app = {
  graph: new Graph(),
  queuePrompt(value) {
    return { owner: this, value };
  },
};
let syncRuns = 0;
extension.installRegionalSaveSync(app, () => { syncRuns += 1; });
extension.installRegionalSaveSync(app, () => { syncRuns += 100; });
const graphResult = app.graph.serialize("save");
const queueResult = app.queuePrompt("queue");
assert(graphResult.owner === app.graph && graphResult.value === "save", "Graph serialize context or return changed");
assert(queueResult.owner === app && queueResult.value === "queue", "queuePrompt context or return changed");
assert(syncRuns === 2, "Save/queue sync wrapper installed more than once");

delete globalThis.LGraph;
let prematureGraphReads = 0;
const setupApp = {
  get graph() {
    prematureGraphReads += 1;
    throw new Error("graph is not initialized");
  },
  queuePrompt() {
    return "queued";
  },
};
extension.installRegionalSaveSync(setupApp, () => {});
assert(prematureGraphReads === 0, "Save sync read app.graph during extension setup");
assert(setupApp.queuePrompt() === "queued", "Setup queue wrapper changed return value");

console.log("Regional runtime lifecycle smoke passed.");
