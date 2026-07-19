import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

function sourceModule(source) {
  return "data:text/javascript;base64," + Buffer.from(source).toString("base64");
}

const seedContractUrl = sourceModule(readFileSync(
  new URL("../web/js/prompt_studio/wildcard_seed_contract.js", import.meta.url),
  "utf8",
));
const widgetHelpersUrl = sourceModule(`
  export function findWidget(node, name) {
    return node?.widgets?.find((widget) => widget?.name === name) || null;
  }
  export function findInputEl(widget) { return widget?.inputEl || null; }
  export function firstValue(value, fallback) {
    const first = Array.isArray(value) ? value[0] : value;
    return first == null ? fallback : first;
  }
`);
const valuesSource = readFileSync(
  new URL("../web/js/prompt_studio/wildcard_values.js", import.meta.url),
  "utf8",
)
  .replace('from "./widgets.js"', `from "${widgetHelpersUrl}"`)
  .replace('from "./wildcard_seed_contract.js"', `from "${seedContractUrl}"`);
const values = await import(sourceModule(valuesSource));

assert.deepEqual(Object.keys(values).sort(), [
  "applyWildcardExecutedInputs",
  "hookWildcardSeedWidget",
  "setRegularWidgetValue",
  "syncWildcardSerialization",
]);

const callbackValues = [];
const node = {
  widgets: [
    { name: "text", value: "__samples/flower__" },
    { name: "populated_text", value: "", inputEl: { disabled: false, value: "" } },
    { name: "mode", value: "재현", callback(value) { callbackValues.push(["mode", value]); } },
    { name: "seed", value: 7, options: {}, callback(value) { callbackValues.push(["seed", value]); } },
    {
      name: "control_after_generate",
      value: "increment",
      callback(value) { callbackValues.push(["control", value]); },
    },
  ],
};

assert.equal(values.hookWildcardSeedWidget(node, { resetSeedControl: false }), true);
assert.equal(node.widgets[2].value, "고정", "legacy reproduce must load as Fixed");
assert.equal(node.widgets[1].inputEl.disabled, false, "Fixed must expose populated_text");
assert.equal(node.widgets[4].value, "increment", "creation must preserve native seed control");
assert.equal(node.widgets[3].options.max, Number.MAX_SAFE_INTEGER);

assert.equal(values.hookWildcardSeedWidget(node, { resetSeedControl: true }), true);
assert.equal(node.widgets[4].value, "fixed", "workflow configure must reset native seed control");

node.widgets[2].callback("일반");
assert.equal(node.widgets[2].value, "일반");
assert.equal(node.widgets[1].inputEl.disabled, true, "General must make populated_text read-only");

values.applyWildcardExecutedInputs(node, {
  wildcard: [{
    populated_text: "rose",
    mode: "일반",
    seed: 99,
  }],
});
assert.equal(node.widgets[1].value, "rose");
assert.equal(node.widgets[1].inputEl.value, "rose");
assert.equal(node.widgets[3].value, 7, "backend feedback must not replace the native seed widget");
assert.equal(node.__easyuseAnimaWildcardHasPopulatedResult, true);

const serialized = { widgets_values: node.widgets.map((widget) => widget.value) };
assert.equal(values.syncWildcardSerialization(node, serialized), true);
assert.equal(serialized.widgets_values[2], "고정");
assert.equal(serialized.widgets_values[4], "fixed");
assert.equal(node.widgets[2].value, "일반", "save normalization must not change the live mode");

const freshNode = { widgets: node.widgets.map((widget) => ({ ...widget })) };
const freshSerialized = { widgets_values: freshNode.widgets.map((widget) => widget.value) };
assert.equal(values.syncWildcardSerialization(freshNode, freshSerialized), false);
assert.deepEqual(
  freshSerialized.widgets_values,
  freshNode.widgets.map((widget) => widget.value),
);

assert(
  callbackValues.some(([name, value]) => name === "control" && value === "fixed"),
  "native seed control callback did not observe workflow-load reset",
);

console.log("Standalone wildcard populated-text and serialization smoke passed.");
