import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

function dataModule(relativePath) {
  const source = readFileSync(new URL(relativePath, import.meta.url), "utf8");
  return "data:text/javascript;base64," + Buffer.from(source).toString("base64");
}

const loraState = await import(dataModule("../web/js/lora_preset/lora_state.js"));

assert.deepEqual(Object.keys(loraState).sort(), [
  "buildLoraLookup",
  "comboEntryText",
  "hasLoraPathProblem",
  "isAnyLoraFixPending",
  "isLoraFixPending",
  "localLoraMatch",
  "loraFileKey",
  "loraFixPendingSet",
  "normalizeLoraKey",
  "normalizeLoraNameList",
  "validComboEntryText",
].sort());

const {
  buildLoraLookup,
  comboEntryText,
  hasLoraPathProblem,
  isAnyLoraFixPending,
  isLoraFixPending,
  localLoraMatch,
  loraFileKey,
  loraFixPendingSet,
  normalizeLoraKey,
  normalizeLoraNameList,
  validComboEntryText,
} = loraState;

const pendingNode = {};
const firstPendingSet = loraFixPendingSet(pendingNode);
assert.ok(firstPendingSet instanceof Set);
assert.strictEqual(loraFixPendingSet(pendingNode), firstPendingSet);
assert.equal(isLoraFixPending(pendingNode, 2), false);
assert.equal(isAnyLoraFixPending(pendingNode), false);
firstPendingSet.add(2);
assert.equal(isLoraFixPending(pendingNode, 2), true);
assert.equal(isLoraFixPending(pendingNode, 3), false);
assert.equal(isAnyLoraFixPending(pendingNode), true);
firstPendingSet.delete(2);
pendingNode.__easyuseAnimaProfileFixPending = true;
assert.equal(isLoraFixPending(pendingNode, 3), true);
assert.equal(isAnyLoraFixPending(pendingNode), true);
pendingNode.__easyuseAnimaProfileFixPending = false;
assert.equal(isAnyLoraFixPending(pendingNode), false);

assert.equal(comboEntryText("  style/foo.safetensors  "), "style/foo.safetensors");
assert.equal(comboEntryText(42), "42");
assert.equal(
  comboEntryText([null, { content: " nested/path.safetensors " }]),
  "nested/path.safetensors",
);
assert.equal(comboEntryText({ filename: "file-only.safetensors" }), "file-only.safetensors");
assert.equal(comboEntryText({ unknown: "ignored" }), "");
assert.equal(validComboEntryText("None"), "");
assert.equal(validComboEntryText("None", { allowNone: true }), "None");
assert.equal(validComboEntryText("[object Object]"), "");
assert.equal(validComboEntryText({ label: " labeled.safetensors " }), "labeled.safetensors");

const rawNames = [
  " Style\\Foo.safetensors ",
  "style/Foo.safetensors",
  { name: "Other/Bar.safetensors" },
  { value: "other\\bar.safetensors" },
  "None",
  "",
  42,
];
const rawNamesSnapshot = structuredClone(rawNames);
assert.deepEqual(normalizeLoraNameList(rawNames), [
  "Style\\Foo.safetensors",
  "Other/Bar.safetensors",
  "42",
]);
assert.deepEqual(rawNames, rawNamesSnapshot);

assert.equal(
  normalizeLoraKey(" C:\\ComfyUI\\models\\loras\\Style\\Foo.safetensors "),
  "style/foo.safetensors",
);
assert.equal(normalizeLoraKey("/Style/Foo.safetensors/"), "style/foo.safetensors");
assert.equal(normalizeLoraKey(""), "");
assert.equal(loraFileKey("Style\\Foo.safetensors"), "foo.safetensors");
assert.equal(loraFileKey(""), "");

const lookupValues = [
  "Style\\Foo.safetensors",
  "Other/Bar.safetensors",
  "SetA/Shared.safetensors",
  "SetB/Shared.safetensors",
];
const lookupValuesSnapshot = [...lookupValues];
const lookup = buildLoraLookup(lookupValues);
assert.deepEqual(lookupValues, lookupValuesSnapshot);
assert.equal(lookup.byName.get("style/foo.safetensors"), "Style\\Foo.safetensors");
assert.equal(lookup.byFile.get("foo.safetensors"), "Style\\Foo.safetensors");
assert.equal(lookup.byFile.get("shared.safetensors"), null);

assert.deepEqual(
  localLoraMatch({ name: "Style\\Foo.safetensors" }, lookup),
  {
    state: "ok",
    match: "Style\\Foo.safetensors",
    reason: "name",
  },
);
assert.deepEqual(
  localLoraMatch({ lora: "style/foo.safetensors" }, lookup),
  {
    state: "fixable",
    match: "Style\\Foo.safetensors",
    reason: "name",
  },
);
assert.deepEqual(
  localLoraMatch({ lora: "Style/Foo.safetensors" }, lookup),
  {
    state: "ok",
    match: "Style\\Foo.safetensors",
    reason: "name",
  },
);
assert.deepEqual(
  localLoraMatch(
    { name: "D:\\ComfyUI\\models\\loras\\Style\\Foo.safetensors" },
    lookup,
  ),
  {
    state: "fixable",
    match: "Style\\Foo.safetensors",
    reason: "name",
  },
);
assert.deepEqual(
  localLoraMatch({ name: "legacy/path/Bar.safetensors" }, lookup),
  {
    state: "fixable",
    match: "Other/Bar.safetensors",
    reason: "file",
  },
);
assert.deepEqual(
  localLoraMatch({ name: "legacy/path/Shared.safetensors" }, lookup),
  {
    state: "missing",
    match: "",
    reason: "",
  },
);
assert.deepEqual(
  localLoraMatch({ name: "missing/Unknown.safetensors" }, lookup),
  {
    state: "missing",
    match: "",
    reason: "",
  },
);
assert.deepEqual(
  localLoraMatch({ name: "" }, lookup),
  {
    state: "unknown",
    match: "",
    reason: "",
  },
);
assert.deepEqual(
  localLoraMatch({ name: "Style/Foo.safetensors" }, null),
  {
    state: "unknown",
    match: "",
    reason: "",
  },
);

const conflictingLookup = buildLoraLookup([
  "Style/Foo.safetensors",
  "style\\foo.safetensors",
]);
assert.equal(conflictingLookup.byName.get("style/foo.safetensors"), null);
assert.equal(conflictingLookup.byFile.get("foo.safetensors"), null);
assert.deepEqual(
  localLoraMatch({ name: "Style/Foo.safetensors" }, conflictingLookup),
  {
    state: "missing",
    match: "",
    reason: "",
  },
);

assert.equal(hasLoraPathProblem({ state: "ok" }), false);
assert.equal(hasLoraPathProblem({ state: "unknown" }), false);
assert.equal(hasLoraPathProblem({ state: "fixable" }), true);
assert.equal(hasLoraPathProblem({ state: "missing" }), true);
assert.equal(hasLoraPathProblem(null), false);
