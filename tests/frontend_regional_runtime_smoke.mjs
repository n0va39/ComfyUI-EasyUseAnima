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
const maskGeometryUrl = dataModule("../web/js/prompt_studio/regional/mask_geometry.js");
const resolutionUrl = dataModule("../web/js/prompt_studio/regional/resolution.js", {
  "./constants.js": constantsUrl,
});
const schemaUrl = dataModule("../web/js/prompt_studio/regional/schema.js", {
  "./constants.js": constantsUrl,
  "./mask_geometry.js": maskGeometryUrl,
  "./resolution.js": resolutionUrl,
});
const lifecycleUrl = dataModule("../web/js/prompt_studio/regional/lifecycle.js");
const layoutUrl = dataModule("../web/js/prompt_studio/regional/layout.js", {
  "./lifecycle.js": lifecycleUrl,
});
const extensionUrl = dataModule("../web/js/prompt_studio/regional/extension.js", {
  "./constants.js": constantsUrl,
  "./lifecycle.js": lifecycleUrl,
  "./layout.js": layoutUrl,
});
const fieldEditorUrl = dataModule("../web/js/prompt_studio/regional/field_editor.js", {
  "./constants.js": constantsUrl,
  "./resolution.js": resolutionUrl,
  "./schema.js": schemaUrl,
  "./lifecycle.js": lifecycleUrl,
});

const lifecycle = await import(lifecycleUrl);
const extension = await import(extensionUrl);
const fieldEditor = await import(fieldEditorUrl);

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
assert(hookCalls.filter(([name]) => name === "dispose").length === 1, "Node removal cleanup count changed");

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
