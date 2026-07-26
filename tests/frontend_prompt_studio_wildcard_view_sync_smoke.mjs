import { readFileSync } from "node:fs";
import { createFakeDocument } from "./frontend_support/fake_dom.mjs";

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

function assertEqual(actual, expected, message) {
  if (actual !== expected) {
    throw new Error(`${message}: expected ${JSON.stringify(expected)}, got ${JSON.stringify(actual)}`);
  }
}

const appUrl = inlineModule(`
  export const app = {
    graph: {
      dirtyCount: 0,
      setDirtyCanvas() { this.dirtyCount += 1; },
    },
  };
`);
const constantsUrl = inlineModule(`
  export const ADVANCED_CONTROL_WIDGETS = [];
  export const ADVANCED_WILDCARD_DEFAULT_MODE = "일반";
  export const ADVANCED_WILDCARD_MODES = ["일반", "순차"];
  export const ADVANCED_WILDCARD_SEED_CONTROLS = ["fixed", "randomize", "increment"];
  export const ADVANCED_RESOLUTION_BUCKETS = {};
  export const ARTIST_MIX_MODES = ["off"];
  export const CUSTOM_ADVANCED_RESOLUTION_BUCKET = "Custom";
  export const NAIA_ADVANCED_RESOLUTION_BUCKET = "NAIA";
`);
const domUrl = inlineModule(`
  export function stopAdvancedControlEvent(event) { event.stopPropagation(); }
  export function protectAdvancedNativeControl(element) { return element; }
  export function updateAdvancedSummary(node, groupId, text) {
    node.__summaries ||= {};
    node.__summaries[groupId] = text;
  }
  export function closeAdvancedHelpPopovers() {}
  export function openAdvancedHelpPopover() {}
`);
const styleUrl = inlineModule("export function ensureAdvancedStyle() {}");
const textUrl = inlineModule("export function psText(key) { return key; }");
const widgetsUrl = inlineModule(`
  export function findWidget(node, name) {
    return node.widgets?.find((widget) => widget.name === name) || null;
  }
  export function findInputEl() { return null; }
  export function isWidgetInputLinked() { return false; }
`);
const historyUrl = inlineModule(`
  export function readPreviousWildcardExecution() { return null; }
  export function wildcardModeWidgetValue(value) { return value; }
`);
const schemaUrl = inlineModule(`
  export function advancedResolutionOptions() { return []; }
  export function normalizeAdvancedResolutionBucket(value) { return value; }
  export function normalizeAdvancedResolutionSize(_bucket, value) { return value; }
  export function normalizeAdvancedWidgetQueueValue(name, value) {
    return name === "wildcard_seed" ? Math.trunc(Number(value)) : value;
  }
  export function normalizeArtistMixMode(value) { return value; }
`);
const utilsUrl = inlineModule(`
  export function advancedResolutionLabel(width, height) { return width + " * " + height; }
  export function clampAdvancedNumber(value) { return Number(value); }
  export function snapResolution32(value) { return Number(value); }
`);
const orientationUrl = inlineModule(`
  export function advancedResolutionOrientationPlan() { return { enabled: false }; }
  export function advancedResolutionOrientationTitleKey() { return ""; }
`);
const wildcardContractUrl = new URL(
  "../web/js/prompt_studio/wildcard_seed_contract.js",
  import.meta.url,
).href;
const advancedControlsUrl = dataModule(
  "../web/js/prompt_studio/advanced_controls.js",
  {
    "../../../../scripts/app.js": appUrl,
    "./constants.js": constantsUrl,
    "./dom.js": domUrl,
    "./schema.js": schemaUrl,
    "./style.js": styleUrl,
    "./text.js": textUrl,
    "./utils.js": utilsUrl,
    "./advanced_resolution_orientation.js": orientationUrl,
    "./widgets.js": widgetsUrl,
    "./wildcard_seed_contract.js": wildcardContractUrl,
    "./wildcard_seed_history.js": historyUrl,
  },
);

globalThis.document = createFakeDocument();
globalThis.HTMLElement = Object;
globalThis.HTMLInputElement = Object;
globalThis.HTMLTextAreaElement = Object;

const {
  commitAdvancedWildcardSeedView,
  createAdvancedWildcardSettingsBody,
} = await import(advancedControlsUrl);

let callbackCount = 0;
const node = {
  dirtyCount: 0,
  properties: {},
  setDirtyCanvas() { this.dirtyCount += 1; },
  widgets: [
    { name: "wildcard_mode", value: "일반" },
    {
      name: "wildcard_seed",
      value: 1,
      callback() { callbackCount += 1; },
    },
    { name: "wildcard_seed_after_generate", value: "increment" },
    { name: "resolution_size", value: "1344 * 768" },
    { name: "artist_mix_mode", value: "exact" },
    { name: "advanced_fields", value: "current prompt fields" },
  ],
};

const body = createAdvancedWildcardSettingsBody(node);
document.body.append(body);
const seedInput = body.querySelector("input");
seedInput.isConnected = true;
assertEqual(seedInput.value, "1", "open seed input baseline");

assertEqual(commitAdvancedWildcardSeedView(node, 2), true, "next seed commit");
assertEqual(node.widgets[1].value, 2, "canonical hidden seed");
assertEqual(node.__summaries.wildcard.includes("seed 2"), true, "Wildcard summary");
assertEqual(seedInput.value, "2", "untouched open seed input");
assertEqual(callbackCount, 0, "user widget callback count");
assertEqual(node.dirtyCount, 0, "node layout/dirty mutation count");
assertEqual(node.widgets[3].value, "1344 * 768", "resolution preservation");
assertEqual(node.widgets[4].value, "exact", "Artist Mix preservation");
assertEqual(node.widgets[5].value, "current prompt fields", "prompt field preservation");

seedInput.value = "77";
seedInput.emit("input");
assertEqual(commitAdvancedWildcardSeedView(node, 3), true, "dirty-input seed commit");
assertEqual(node.widgets[1].value, 3, "canonical seed with dirty popup");
assertEqual(node.__summaries.wildcard.includes("seed 3"), true, "summary with dirty popup");
assertEqual(seedInput.value, "77", "dirty popup input ownership");
assertEqual(callbackCount, 0, "callback count after dirty popup");

console.log("Prompt Studio narrow Wildcard view-sync smoke passed.");
