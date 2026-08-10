import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

function dataModule(relativePath, replacements = {}) {
  let source = readFileSync(new URL(relativePath, import.meta.url), "utf8");
  for (const [specifier, replacement] of Object.entries(replacements)) {
    source = source.replaceAll(`"${specifier}"`, `"${replacement}"`);
  }
  return `data:text/javascript;base64,${Buffer.from(source).toString("base64")}`;
}

function inlineModule(source) {
  return `data:text/javascript;base64,${Buffer.from(source).toString("base64")}`;
}

const constantsUrl = inlineModule(`
  export const ADVANCED_NODE_TYPE = "EasyUseAnimaPromptStudioAdvanced";
  export const ADVANCED_V2_NODE_TYPE = "EasyUseAnimaPromptStudioAdvancedV2";
  export const EXTEND_NODE_TYPE = "EasyUseAnimaPromptStudioExtend";
  export const NODE_TYPE = "EasyUseAnimaPromptStudio";
  export const WILDCARD_NODE_TYPE = "EasyUseAnimaWildcard";
`);
const hostHookRegistryUrl = inlineModule(`
  export function registerHostHookCallbacks() { return () => {}; }
`);
const highlightUrl = inlineModule(`
  export function copyInputTextMetrics() {}
  export function ensureHighlightOverlay() { return null; }
  export function highlightOverlayHtml() { return ""; }
  export function syncOverlayBounds() {}
`);
const settingsUrl = inlineModule(`
  export function applyPromptStudioTextStyle() {}
`);
const highlightWidgetsUrl = inlineModule(`
  export function findInputEl(widget) {
    return widget?.inputEl || null;
  }
  export function isWidgetInputLinked(node, name) {
    return node?.inputs?.some((input) => input?.name === name && input?.link != null) || false;
  }
`);
const nodeHooksUrl = dataModule(
  "../web/js/prompt_studio/node_hooks.js",
  {
    "./constants.js": constantsUrl,
    "../lifecycle/host_hook_registry.js": hostHookRegistryUrl,
  },
);
const { registerPromptStudioNodeHooks } = await import(nodeHooksUrl);
const highlightRevisionUrl = dataModule(
  "../web/js/prompt_studio/highlight_revision.js",
);
const highlightUiUrl = dataModule(
  "../web/js/prompt_studio/highlight_ui.js",
  {
    "./highlight.js": highlightUrl,
    "./highlight_revision.js": highlightRevisionUrl,
    "./settings.js": settingsUrl,
    "./widgets.js": highlightWidgetsUrl,
  },
);
const { displayText } = await import(highlightUiUrl);

function textWidget(name, value) {
  return {
    name,
    value,
    inputEl: { value },
  };
}

function executionFixture(nodeTypeName, state) {
  function NodeType() {
    Object.assign(this, state);
    this.__originalExecutedMessages = [];
  }
  const originalOnExecuted = function (message) {
    this.__originalExecutedMessages.push(message);
  };
  NodeType.prototype.onExecuted = originalOnExecuted;
  assert.equal(
    registerPromptStudioNodeHooks(NodeType, { name: nodeTypeName }, {}),
    true,
  );
  assert.equal(
    NodeType.prototype.onExecuted,
    originalOnExecuted,
    `${nodeTypeName} must retain the host's original onExecuted owner`,
  );
  return new NodeType();
}

// QSTATE-04A Classic preservation fixture: the production node hook keeps the
// host's original onExecuted callback but no longer publishes submitted text
// into current editor or linked-input presentation state.
const classicPrompt = textWidget("prompt", "current classic edit");
const classicNode = executionFixture("EasyUseAnimaPromptStudio", {
  widgets: [classicPrompt],
  inputs: [{ name: "prompt", link: 17 }],
});
const classicMessage = {
  prompt_studio_inputs: [{
    prompt: "queued classic text",
  }],
};
classicNode.onExecuted(classicMessage);
assert.deepEqual(classicNode.__originalExecutedMessages, [classicMessage]);
assert.equal(classicPrompt.value, "current classic edit");
assert.equal(classicPrompt.inputEl.value, "current classic edit");
assert.equal(
  classicPrompt.__easyuseAnimaExecutedText,
  undefined,
  "stale Classic result created executed presentation state",
);
assert.equal(
  displayText(classicNode, classicPrompt),
  "current classic edit",
  "stale Classic result replaced linked-input presentation",
);

// QSTATE-04A Extend preservation fixture: submitted slot text, visibility, and
// NAIA state are execution history, not current editor authority.
const extendQuality = textWidget("quality_tags_1", "current extend edit");
const extendFillNaia = { name: "fill_naia_prompt", value: false };
const extendNode = executionFixture("EasyUseAnimaPromptStudioExtend", {
  widgets: [extendQuality, extendFillNaia],
  __visibleSlots: new Set(["quality_tags_1", "general_tags_4"]),
});
const extendMessage = {
  prompt_studio_slots: [{
    quality_tags_1: "queued extend text",
    active_slots: ["quality_tags_1"],
    fill_naia_prompt: true,
  }],
};
extendNode.onExecuted(extendMessage);
assert.deepEqual(extendNode.__originalExecutedMessages, [extendMessage]);
assert.equal(
  extendQuality.value,
  "current extend edit",
  "stale Extend result replaced the current widget value",
);
assert.equal(
  extendQuality.inputEl.value,
  "current extend edit",
  "stale Extend result replaced the current DOM value",
);
assert.deepEqual(
  [...extendNode.__visibleSlots],
  ["quality_tags_1", "general_tags_4"],
);
assert.equal(extendFillNaia.value, false);

console.log("Prompt Studio Classic/Extend executed values smoke passed.");
