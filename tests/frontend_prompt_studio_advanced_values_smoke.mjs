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

function assert(condition, message) {
  if (!condition) {
    throw new Error(message);
  }
}

const wildcardSeedContractUrl = dataModule(
  "../web/js/prompt_studio/wildcard_seed_contract.js",
);
const wildcardSeedHistoryUrl = dataModule(
  "../web/js/prompt_studio/wildcard_seed_history.js",
  { "./wildcard_seed_contract.js": wildcardSeedContractUrl },
);
const constantsUrl = inlineModule(`
  export const ADVANCED_FIELDS_PROPERTY = "easyuse_anima_advanced_fields";
  export const ADVANCED_WIDGET_INDEX = {};
`);
const schemaUrl = inlineModule(`
  export function normalizeAdvancedWidgetQueueValue(_name, value) { return value; }
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
const widgetsUrl = inlineModule(`
  export function findWidget(node, name) {
    return node?.widgets?.find((widget) => widget.name === name) || null;
  }
  export function firstValue(value, fallback) {
    return Array.isArray(value) ? (value[0] ?? fallback) : (value ?? fallback);
  }
`);
const advancedValuesUrl = dataModule(
  "../web/js/prompt_studio/advanced_values.js",
  {
    "./constants.js": constantsUrl,
    "./schema.js": schemaUrl,
    "./state.js": stateUrl,
    "./serialization.js": serializationUrl,
    "./widgets.js": widgetsUrl,
    "./wildcard_seed_history.js": wildcardSeedHistoryUrl,
  },
);
const { applyAdvancedExecutedInputs } = await import(advancedValuesUrl);

const node = {
  properties: {},
  widgets: [
    { name: "advanced_fields", value: "[]" },
    { name: "use_naia", value: false },
    { name: "wildcard_mode", value: "일반" },
    { name: "wildcard_seed", value: 900 },
    { name: "wildcard_seed_after_generate", value: "fixed" },
  ],
};
let dirtyCount = 0;
let renderCount = 0;
applyAdvancedExecutedInputs(
  node,
  {
    prompt_studio_advanced: [{
      advanced_fields: "[]",
      field_inputs: {},
      wildcard_mode: "순차",
      wildcard_execution_seed: 41,
      wildcard_seed: 42,
      wildcard_seed_after_generate: "increment",
    }],
  },
  {
    advancedWidget: (target) => target.widgets[0],
    markNodeDirty: () => { dirtyCount += 1; },
    parseAdvancedFields: () => [],
    renderAdvancedEditor: () => { renderCount += 1; },
  },
);

assert(
  node.widgets.find((widget) => widget.name === "wildcard_seed").value === 42,
  "Advanced did not apply the backend next seed",
);
const previous = JSON.parse(
  node.properties.easyuse_anima_previous_wildcard_execution,
);
assert(previous.seed === 41, "Advanced history did not store the execution seed");
assert(previous.mode === "sequential", "Advanced history did not normalize the mode");
assert(dirtyCount === 1, "Advanced history publication did not dirty once");
assert(renderCount === 1, "Advanced editor was not refreshed once");

console.log("Prompt Studio Advanced executed values smoke passed.");
