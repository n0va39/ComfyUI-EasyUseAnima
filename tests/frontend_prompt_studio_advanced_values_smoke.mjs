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
const { publishAdvancedExecution } = await import(advancedValuesUrl);

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
let consumedMappedItemCount = null;
let wildcardViewCommitCount = 0;
let linkedViewCommitCount = 0;
let naiaFieldCommitCount = 0;
let naiaResolutionCommitCount = 0;
publishAdvancedExecution(
  node,
  {
    prompt_studio_advanced: [{
      advanced_fields: "[]",
      field_inputs: { field_positive_general: "resolved linked text" },
      naia_field_updates: {
        positive_naia: "resolved positive NAIA",
        negative_naia: "resolved negative NAIA",
      },
      naia_resolution_update: { width: 832, height: 1216 },
      wildcard_mode: "순차",
      wildcard_execution_seed: 41,
      wildcard_seed: 42,
      wildcard_seed_after_generate: "increment",
    }],
  },
  {
    advancedWidget: (target) => target.widgets[0],
    commitAdvancedWildcardSeedView: (target, seed) => {
      wildcardViewCommitCount += 1;
      target.widgets.find((widget) => widget.name === "wildcard_seed").value = seed;
    },
    consumePromptStudioExecution: (_target, _message, mappedItemCount, committers) => {
      consumedMappedItemCount = mappedItemCount;
      for (const committer of committers) {
        committer.commit({ transaction: {} });
      }
      return true;
    },
    createLinkedExecutionCommitter: (target, inputName, value) => ({
      surface: "prompt.execution.linked:positive_general",
      commit: () => {
        linkedViewCommitCount += 1;
        target.__easyuseAnimaAdvancedFieldInputValues ||= {};
        target.__easyuseAnimaAdvancedFieldInputValues[inputName] = value;
      },
    }),
    createNaiaExecutionCommitter: (_target, fieldId, value) => ({
      surface: `prompt.execution.naia:${fieldId}`,
      commit: () => {
        naiaFieldCommitCount += 1;
        assert(value.includes("NAIA"), "Advanced lost an explicit NAIA field delta");
      },
    }),
    createNaiaResolutionExecutionCommitter: (_target, value) => ({
      surface: "prompt.execution.naia_resolution",
      commit: () => {
        naiaResolutionCommitCount += 1;
        assert(value.width === 832 && value.height === 1216, "Advanced lost the NAIA resolution delta");
      },
    }),
    markNodeDirty: () => { dirtyCount += 1; },
    parseAdvancedFields: () => [],
    renderAdvancedEditor: () => { renderCount += 1; },
  },
);

assert(
  node.widgets.find((widget) => widget.name === "wildcard_seed").value === 42,
  "Advanced did not apply the backend next seed",
);
assert(consumedMappedItemCount === 1, "Advanced did not report one mapped payload");
assert(wildcardViewCommitCount === 1, "Advanced did not delegate the next seed to the narrow view owner");
assert(linkedViewCommitCount === 1, "Advanced did not delegate linked input to a feature committer");
assert(naiaFieldCommitCount === 2, "Advanced did not fan out exact NAIA field committers");
assert(naiaResolutionCommitCount === 1, "Advanced did not fan out the NAIA resolution committer");
assert(
  node.__easyuseAnimaAdvancedFieldInputValues.field_positive_general
    === "resolved linked text",
  "Advanced did not publish the linked execution overlay",
);
const previous = JSON.parse(
  node.properties.easyuse_anima_previous_wildcard_execution,
);
assert(previous.seed === 41, "Advanced history did not store the execution seed");
assert(previous.mode === "sequential", "Advanced history did not normalize the mode");
assert(dirtyCount === 1, "Advanced history publication did not dirty once");
assert(renderCount === 0, "execution publication must not rerender the Advanced editor");

// QSTATE-04A preservation fixture: an Advanced/AdvancedV2 queue captured the
// submitted values below, then the user edited every mutable surface group.
// Execution publication may retain wildcard history/next-seed behavior for the
// QSTATE-04B cutover, but it must not replay submitted editor state.
const submittedFields = JSON.stringify([
  { id: "positive_general", text: "queued old tags" },
]);
const editedFields = JSON.stringify([
  { id: "positive_general", text: "current edited tags" },
]);
const staleNode = {
  properties: {},
  __easyuseAnimaAdvancedFieldInputValues: {
    field_positive_general: "current socket edit",
  },
  widgets: [
    { name: "advanced_fields", value: editedFields },
    { name: "use_naia", value: false },
    { name: "resolution_bucket", value: "Custom" },
    { name: "resolution_size", value: "1344 * 768" },
    { name: "resolution_custom_width", value: 1344 },
    { name: "resolution_custom_height", value: 768 },
    { name: "wildcard_mode", value: "일반" },
    { name: "wildcard_seed", value: 900 },
    { name: "wildcard_seed_after_generate", value: "fixed" },
    { name: "artist_mix_mode", value: "exact" },
    { name: "artist_mix_start_percent", value: 0.75 },
  ],
};
publishAdvancedExecution(
  staleNode,
  {
    prompt_studio_advanced: [{
      advanced_fields: submittedFields,
      field_inputs: { field_positive_general: "queued socket value" },
      use_naia: true,
      resolution_bucket: "1024",
      resolution_size: "1024 * 1024 (1:1)",
      resolution_custom_width: 1024,
      resolution_custom_height: 1024,
      wildcard_mode: "순차",
      wildcard_execution_seed: 40,
      wildcard_seed: 41,
      wildcard_seed_after_generate: "increment",
      artist_mix_mode: "average",
      artist_mix_start_percent: 0.25,
    }],
  },
  {
    advancedWidget: (target) => target.widgets[0],
    consumePromptStudioExecution: () => false,
    createLinkedExecutionCommitter: () => ({
      surface: "prompt.execution.linked:positive_general",
      commit: () => { throw new Error("stale linked committer must not run"); },
    }),
    parseAdvancedFields: (target) => JSON.parse(target.widgets[0].value),
    renderAdvancedEditor: () => {},
  },
);

const staleWidgetValue = (name) => staleNode.widgets.find(
  (widget) => widget.name === name,
)?.value;
assert(
  staleWidgetValue("advanced_fields") === editedFields,
  "stale Advanced fields replaced the current editor state",
);
assert(
  staleNode.__easyuseAnimaAdvancedFieldInputValues.field_positive_general
    === "current socket edit",
  "stale Advanced field inputs replaced the current socket state",
);
assert(
  staleWidgetValue("use_naia") === false,
  "stale Advanced NAIA state replaced the current selection",
);
assert(
  staleWidgetValue("resolution_bucket") === "Custom"
    && staleWidgetValue("resolution_size") === "1344 * 768"
    && staleWidgetValue("resolution_custom_width") === 1344
    && staleWidgetValue("resolution_custom_height") === 768,
  "stale Advanced resolution replaced the current atomic group",
);
assert(
  staleWidgetValue("wildcard_mode") === "일반"
    && staleWidgetValue("wildcard_seed_after_generate") === "fixed",
  "stale Advanced wildcard settings replaced the current mode/control",
);
assert(
  staleWidgetValue("wildcard_seed") === 900,
  "stale Advanced execution replaced the current editable next seed",
);
const stalePrevious = JSON.parse(
  staleNode.properties.easyuse_anima_previous_wildcard_execution,
);
assert(
  stalePrevious.seed === 40 && stalePrevious.mode === "sequential",
  "stale execution must still update non-editable wildcard history",
);
assert(
  staleWidgetValue("artist_mix_mode") === "exact"
    && staleWidgetValue("artist_mix_start_percent") === 0.75,
  "stale Advanced Artist Mix state replaced the current atomic group",
);

const missingIdentityNode = {
  properties: {},
  widgets: [{ name: "wildcard_seed", value: 50 }],
};
publishAdvancedExecution(
  missingIdentityNode,
  {
    prompt_studio_advanced: [{
      wildcard_execution_seed: 50,
      wildcard_seed: 51,
      wildcard_mode: "일반",
    }],
  },
  { markNodeDirty: () => {} },
);
assert(
  missingIdentityNode.widgets[0].value === 50,
  "missing transaction identity must fail closed for next-seed publication",
);

let mappedCount = null;
const mappedNode = {
  properties: {},
  widgets: [{ name: "wildcard_seed", value: 60 }],
};
publishAdvancedExecution(
  mappedNode,
  {
    prompt_studio_advanced: [
      { wildcard_execution_seed: 60, wildcard_seed: 61, wildcard_mode: "일반" },
      { wildcard_execution_seed: 70, wildcard_seed: 71, wildcard_mode: "일반" },
    ],
  },
  {
    consumePromptStudioExecution: (_target, _message, count) => {
      mappedCount = count;
      return false;
    },
    markNodeDirty: () => {},
  },
);
assert(mappedCount === 2, "Advanced did not expose multiple mapped payloads");
assert(
  mappedNode.widgets[0].value === 60,
  "multiple mapped payloads must not publish an editable next seed",
);

console.log("Prompt Studio Advanced executed values smoke passed.");
