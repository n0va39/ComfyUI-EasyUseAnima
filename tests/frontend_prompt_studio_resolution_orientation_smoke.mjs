import { readFileSync } from "node:fs";
import {
  createFakeDocument,
} from "./frontend_support/fake_dom.mjs";

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

function assert(condition, message) {
  if (!condition) {
    throw new Error(message);
  }
}

function assertEqual(actual, expected, message) {
  if (actual !== expected) {
    throw new Error(`${message}: expected ${JSON.stringify(expected)}, got ${JSON.stringify(actual)}`);
  }
}

const orientationUrl = new URL(
  "../web/js/prompt_studio/advanced_resolution_orientation.js",
  import.meta.url,
).href;
const schemaUrl = new URL(
  "../web/js/prompt_studio/schema.js",
  import.meta.url,
).href;
const utilsUrl = new URL(
  "../web/js/prompt_studio/utils.js",
  import.meta.url,
).href;

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
  export const ADVANCED_RESOLUTION_BUCKETS = {
    "1024": [
      [672, 1536], [1536, 672],
      [896, 1152], [1152, 896],
      [1024, 1024],
    ],
  };
  export const ARTIST_MIX_MODES = ["off"];
  export const CUSTOM_ADVANCED_RESOLUTION_BUCKET = "Custom";
  export const NAIA_ADVANCED_RESOLUTION_BUCKET = "NAIA";
`);
const domUrl = inlineModule(`
  const PROTECTED_EVENTS = ["pointerdown", "mousedown", "pointerup", "mouseup", "click", "dblclick"];
  export function stopAdvancedControlEvent(event) { event.stopPropagation(); }
  export function protectAdvancedNativeControl(element) {
    for (const eventName of PROTECTED_EVENTS) {
      element.addEventListener(eventName, stopAdvancedControlEvent);
    }
    return element;
  }
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
  export function findInputEl(widget) { return widget?.inputEl || null; }
  export function isWidgetInputLinked(node, name) {
    return !!node.inputs?.some((input) => input.widget?.name === name && input.link != null);
  }
`);
const wildcardSeedContractUrl = inlineModule(`
  export function bindWildcardSeedInput() {}
  export function normalizeWildcardSeedControl(value) { return String(value || "fixed"); }
  export function syncBoundWildcardSeedInput() { return false; }
`);
const wildcardSeedHistoryUrl = inlineModule(`
  export function readPreviousWildcardExecution() { return null; }
  export function wildcardModeWidgetValue(value) { return value; }
`);

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
    "./wildcard_seed_contract.js": wildcardSeedContractUrl,
    "./wildcard_seed_history.js": wildcardSeedHistoryUrl,
  },
);

globalThis.document = createFakeDocument();
globalThis.HTMLElement = Object;
globalThis.HTMLInputElement = Object;
globalThis.HTMLTextAreaElement = Object;

const {
  createAdvancedResolutionSettingsBody,
} = await import(advancedControlsUrl);
const {
  advancedResolutionOrientationPlan,
} = await import(orientationUrl);

function widgetSnapshot(node) {
  return Object.fromEntries(node.widgets.map((widget) => [widget.name, widget.value]));
}

function createResolutionNode({
  type = "EasyUseAnimaPromptStudioAdvanced",
  bucket = "1024",
  size = "896 * 1152 (7:9)",
  width = 896,
  height = 1152,
  linked = [],
} = {}) {
  const callbackSnapshots = [];
  const node = {
    type,
    comfyClass: type,
    inputs: linked.map((name, index) => ({
      name,
      widget: { name },
      link: index + 1,
    })),
    dirtyCount: 0,
    properties: {},
    setDirtyCanvas() {
      this.dirtyCount += 1;
    },
    widgets: [],
  };
  const addWidget = (name, value) => {
    const widget = {
      name,
      value,
      callback() {
        callbackSnapshots.push({
          name,
          snapshot: widgetSnapshot(node),
        });
      },
    };
    node.widgets.push(widget);
    return widget;
  };
  addWidget("use_naia", true);
  addWidget("consume_naia_on_queue", false);
  addWidget("resolution_bucket", bucket);
  addWidget("resolution_size", size);
  addWidget("resolution_custom_width", width);
  addWidget("resolution_custom_height", height);
  addWidget("advanced_fields", "[]");
  node.callbackSnapshots = callbackSnapshots;
  return node;
}

function resolutionFixture(options = {}) {
  const node = createResolutionNode(options);
  const body = createAdvancedResolutionSettingsBody(node);
  const button = body.querySelector(
    '[data-easyuse-anima-resolution-orientation="true"]',
  );
  return {
    body,
    button,
    node,
    selects: body.querySelectorAll("select"),
    inputs: body.querySelectorAll("input"),
  };
}

for (const type of [
  "EasyUseAnimaPromptStudioAdvanced",
  "EasyUseAnimaPromptStudioAdvancedV2",
]) {
  const fixture = resolutionFixture({ type });
  assertEqual(fixture.button.tagName, "BUTTON", `${type} orientation control must be a native button`);
  assertEqual(fixture.button.type, "button", `${type} orientation control type`);
  assertEqual(
    fixture.button.getAttribute("aria-label"),
    "advanced.swapOrientation",
    `${type} orientation aria-label`,
  );
  assertEqual(
    fixture.button.getAttribute("aria-disabled"),
    "false",
    `${type} exact inverse must be enabled`,
  );
  const pointerEvent = fixture.button.emit("pointerdown");
  assert(pointerEvent.propagationStopped, `${type} pointer event escaped the native control`);
  const keyboardClick = fixture.button.emit("click", { detail: 0 });
  assert(keyboardClick.defaultPrevented, `${type} keyboard click did not stay in the control`);
  assert(keyboardClick.propagationStopped, `${type} keyboard click escaped the control`);
  assertEqual(
    widgetSnapshot(fixture.node).resolution_size,
    "1152 * 896 (9:7)",
    `${type} portrait preset did not swap to exact landscape`,
  );
  fixture.button.emit("click");
  assertEqual(
    widgetSnapshot(fixture.node).resolution_size,
    "896 * 1152 (7:9)",
    `${type} landscape preset did not swap back to exact portrait`,
  );
}

const square = resolutionFixture({
  size: "1024 * 1024 (1:1)",
  width: 1024,
  height: 1024,
});
assertEqual(square.button.getAttribute("aria-disabled"), "true", "Square preset must be disabled");
assertEqual(
  square.button.title,
  "advanced.swapOrientationSquareTitle",
  "Square preset explanation",
);
square.button.emit("click");
assertEqual(
  widgetSnapshot(square.node).resolution_size,
  "1024 * 1024 (1:1)",
  "Square preset must be a no-op",
);

const missingInverse = advancedResolutionOrientationPlan({
  bucket: "test",
  size: "640 * 960 (2:3)",
  buckets: {
    test: [[640, 960], [1024, 1024]],
  },
});
assertEqual(missingInverse.enabled, false, "Missing inverse must disable the command");
assertEqual(missingInverse.reason, "missing-inverse", "Missing inverse reason");
assertEqual(missingInverse.nextSize, null, "Missing inverse must not approximate");

const custom = resolutionFixture({
  bucket: "Custom",
  size: "896 * 1152 (7:9)",
  width: 897,
  height: 1149,
});
custom.node.callbackSnapshots.length = 0;
custom.button.emit("click", { detail: 0 });
const customValues = widgetSnapshot(custom.node);
assertEqual(customValues.resolution_custom_width, 1152, "Custom width swap");
assertEqual(customValues.resolution_custom_height, 896, "Custom height swap");
assertEqual(customValues.resolution_size, "1152 * 896 (9:7)", "Custom size label swap");
assertEqual(custom.inputs[0].value, "1152", "Custom width input sync");
assertEqual(custom.inputs[1].value, "896", "Custom height input sync");
assertEqual(
  custom.node.__summaries.resolution,
  "Custom · 1152 * 896 (9:7)",
  "Custom summary sync",
);
assertEqual(custom.node.callbackSnapshots.length, 3, "Custom swap callback count");
for (const callback of custom.node.callbackSnapshots) {
  assertEqual(
    callback.snapshot.resolution_custom_width,
    1152,
    `${callback.name} callback observed an intermediate width`,
  );
  assertEqual(
    callback.snapshot.resolution_custom_height,
    896,
    `${callback.name} callback observed an intermediate height`,
  );
  assertEqual(
    callback.snapshot.resolution_size,
    "1152 * 896 (9:7)",
    `${callback.name} callback observed an intermediate size`,
  );
}

const reopenedCustom = createAdvancedResolutionSettingsBody(custom.node);
const reopenedInputs = reopenedCustom.querySelectorAll("input");
assertEqual(reopenedInputs[0].value, "1152", "Popup reopen width");
assertEqual(reopenedInputs[1].value, "896", "Popup reopen height");

const advancedValuesConstantsUrl = inlineModule(`
  export const ADVANCED_FIELDS_PROPERTY = "easyuse_anima_advanced_fields";
  export const ADVANCED_WIDGET_INDEX = {
    resolution_bucket: 3,
    resolution_size: 4,
    resolution_custom_width: 5,
    resolution_custom_height: 6,
    advanced_fields: 8,
  };
`);
const stateUrl = inlineModule(`
  export function getAdvancedFields() { return []; }
  export function setAdvancedFields(node, fields) { node.__fields = fields; }
`);
const serializationUrl = inlineModule(`
  export function collectAdvancedEditorFields(_node, fields) { return fields; }
  export function mergeAdvancedFieldInputValues() { return false; }
  export function syncAdvancedFieldsBackup(node, value) { node.__backup = value; }
`);
const advancedValueWidgetsUrl = inlineModule(`
  export function findWidget(node, name) {
    return node.widgets?.find((widget) => widget.name === name) || null;
  }
  export function firstValue(value, fallback) {
    return Array.isArray(value) ? (value[0] ?? fallback) : (value ?? fallback);
  }
`);
const serializationHistoryUrl = inlineModule(`
  export function serializePreviousWildcardExecution() {}
  export function writePreviousWildcardExecution() { return false; }
`);
const advancedValuesUrl = dataModule(
  "../web/js/prompt_studio/advanced_values.js",
  {
    "./constants.js": advancedValuesConstantsUrl,
    "./schema.js": schemaUrl,
    "./state.js": stateUrl,
    "./serialization.js": serializationUrl,
    "./widgets.js": advancedValueWidgetsUrl,
    "./wildcard_seed_history.js": serializationHistoryUrl,
  },
);
const {
  syncAdvancedValues,
} = await import(advancedValuesUrl);
const serialized = { widgets_values: [] };
syncAdvancedValues(custom.node, serialized, {
  advancedWidget: (node) => node.widgets.find((widget) => widget.name === "advanced_fields"),
  parseAdvancedFields: () => [],
  repairAdvancedInternalWidgetValues: () => {},
  writeAdvancedFields: () => {},
});
assertEqual(serialized.widgets_values[3], "Custom", "Serialized bucket");
assertEqual(serialized.widgets_values[4], "1152 * 896 (9:7)", "Serialized size");
assertEqual(serialized.widgets_values[5], 1152, "Serialized custom width");
assertEqual(serialized.widgets_values[6], 896, "Serialized custom height");

const reloaded = resolutionFixture({
  bucket: serialized.widgets_values[3],
  size: serialized.widgets_values[4],
  width: serialized.widgets_values[5],
  height: serialized.widgets_values[6],
});
assertEqual(reloaded.inputs[0].value, "1152", "Reloaded custom width");
assertEqual(reloaded.inputs[1].value, "896", "Reloaded custom height");
assertEqual(
  reloaded.node.widgets.find((widget) => widget.name === "resolution_size").value,
  "1152 * 896 (9:7)",
  "Reloaded queue value",
);

const linked = resolutionFixture({
  bucket: "Custom",
  size: "896 * 1152 (7:9)",
  width: 896,
  height: 1152,
  linked: ["resolution_custom_width"],
});
linked.node.callbackSnapshots.length = 0;
assertEqual(linked.button.getAttribute("aria-disabled"), "true", "Linked custom swap must be disabled");
assertEqual(
  linked.button.title,
  "advanced.swapOrientationLinkedTitle",
  "Linked custom explanation",
);
assert(linked.inputs.every((input) => input.disabled), "Linked custom inputs must stay host-owned");
linked.button.emit("click");
assertEqual(widgetSnapshot(linked.node).resolution_custom_width, 896, "Linked width was overwritten");
assertEqual(widgetSnapshot(linked.node).resolution_custom_height, 1152, "Linked height was overwritten");
assertEqual(linked.node.callbackSnapshots.length, 0, "Linked swap invoked widget callbacks");

const naia = resolutionFixture({
  bucket: "NAIA",
  size: "896 * 1152 (7:9)",
  width: 896,
  height: 1152,
});
const beforeNaia = widgetSnapshot(naia.node);
assertEqual(naia.button.getAttribute("aria-disabled"), "true", "NAIA swap must be disabled");
assertEqual(
  naia.button.title,
  "advanced.swapOrientationNaiaTitle",
  "NAIA explanation",
);
naia.button.emit("click");
const afterNaia = widgetSnapshot(naia.node);
assertEqual(afterNaia.resolution_bucket, "NAIA", "NAIA was silently changed to Custom");
assertEqual(afterNaia.resolution_custom_width, beforeNaia.resolution_custom_width, "NAIA width changed");
assertEqual(afterNaia.resolution_custom_height, beforeNaia.resolution_custom_height, "NAIA height changed");

console.log("Prompt Studio resolution orientation smoke passed.");
