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
  export const EXTEND_ACTIVE_SLOTS_WIDGET = "active_slots";
  export const EXTEND_VISIBLE_SLOTS_PROPERTY = "easyuse_anima_extend_visible_slots";
`);
const extendSlotsUrl = inlineModule(`
  export function extendVisibleSlots(node) {
    return node.__visibleSlots || new Set();
  }
  export function parseExtendSlots(value) {
    if (Array.isArray(value)) return value;
    if (typeof value !== "string") return [];
    try {
      const parsed = JSON.parse(value);
      return Array.isArray(parsed) ? parsed : [];
    } catch {
      return [];
    }
  }
  export function writeExtendVisibleSlots(node, slots) {
    node.__visibleSlots = new Set(slots);
  }
`);
const widgetsUrl = inlineModule(`
  export function findInputEl(widget) {
    return widget?.inputEl || null;
  }
  export function findWidget(node, name) {
    return node?.widgets?.find((widget) => widget.name === name) || null;
  }
  export function firstValue(value, fallback) {
    return Array.isArray(value) ? (value[0] ?? fallback) : (value ?? fallback);
  }
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
const studioValuesUrl = dataModule(
  "../web/js/prompt_studio/studio_values.js",
  {
    "./constants.js": constantsUrl,
    "./extend_slots.js": extendSlotsUrl,
    "./widgets.js": widgetsUrl,
  },
);
const { applyExecutedInputs } = await import(studioValuesUrl);
const highlightUiUrl = dataModule(
  "../web/js/prompt_studio/highlight_ui.js",
  {
    "./highlight.js": highlightUrl,
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

// QSTATE-01 Classic characterization fixture: this intentionally passes while
// the production bug exists. The real applyExecutedInputs() path keeps the
// stored edit but replaces the executed presentation state; the real
// displayText() path then selects the stale result for a linked input.
// QSTATE-04 must flip this to a preservation assertion.
const classicPrompt = textWidget("prompt", "current classic edit");
const classicNode = {
  widgets: [classicPrompt],
  inputs: [{ name: "prompt", link: 17 }],
};
applyExecutedInputs(
  classicNode,
  {
    prompt_studio_inputs: [{
      prompt: "queued classic text",
    }],
  },
  {
    studioFieldNames: () => ["prompt"],
    expandStudioInputToContent: () => {},
    hookStudioNode: () => {},
  },
);
assert.equal(classicPrompt.value, "current classic edit");
assert.equal(classicPrompt.inputEl.value, "current classic edit");
assert.equal(
  classicPrompt.__easyuseAnimaExecutedText,
  "queued classic text",
  "QSTATE-01 fixture did not reproduce the stale Classic executed-state overwrite",
);
assert.equal(
  displayText(classicNode, classicPrompt),
  "queued classic text",
  "QSTATE-01 fixture did not reproduce the stale Classic linked-input presentation",
);

// QSTATE-01 Extend characterization fixture: this intentionally passes while
// the production bug exists. The real applyExecutedInputs() path directly
// restores submitted text, visibility, and NAIA state over the user's edit.
// QSTATE-04 must flip this to a preservation assertion.
const extendQuality = textWidget("quality_tags_1", "current extend edit");
const extendFillNaia = { name: "fill_naia_prompt", value: false };
const extendNode = {
  widgets: [extendQuality, extendFillNaia],
  __visibleSlots: new Set(["quality_tags_1", "general_tags_4"]),
};
applyExecutedInputs(
  extendNode,
  {
    prompt_studio_slots: [{
      quality_tags_1: "queued extend text",
      active_slots: ["quality_tags_1"],
      fill_naia_prompt: true,
    }],
  },
  {
    studioFieldNames: () => ["quality_tags_1"],
    expandStudioInputToContent: () => {},
    hookStudioNode: () => {},
  },
);
assert.equal(
  extendQuality.value,
  "queued extend text",
  "QSTATE-01 fixture did not reproduce the stale Extend widget overwrite",
);
assert.equal(
  extendQuality.inputEl.value,
  "queued extend text",
  "QSTATE-01 fixture did not reproduce the stale Extend DOM overwrite",
);
assert.deepEqual([...extendNode.__visibleSlots], ["quality_tags_1"]);
assert.equal(extendFillNaia.value, true);

console.log("Prompt Studio Classic/Extend characterization smoke passed.");
