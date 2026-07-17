import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { createFakeDocument, descendants } from "./frontend_support/fake_dom.mjs";

function dataModule(relativePath, replacements = {}) {
  let source = readFileSync(new URL(relativePath, import.meta.url), "utf8");
  for (const [from, to] of Object.entries(replacements)) {
    source = source.replaceAll(from, to);
  }
  return "data:text/javascript;base64," + Buffer.from(source).toString("base64");
}

const definitionDataUrl = dataModule("../web/js/settings/definition_data.js");
const wildcardPathEditorModule = await import(
  dataModule("../web/js/settings/wildcard_path_editor.js", {
    "./definition_data.js": definitionDataUrl,
  })
);

assert.deepEqual(
  Object.keys(wildcardPathEditorModule),
  ["createWildcardExtraPathsEditorFactory"],
);

function findAll(root, tagName) {
  return [root, ...descendants(root)].filter(
    (element) => element.tagName === tagName,
  );
}

function findOne(root, tagName) {
  const matches = findAll(root, tagName);
  assert.equal(matches.length, 1, `Expected one ${tagName}, got ${matches.length}`);
  return matches[0];
}

function buttonsByText(root, text) {
  return findAll(root, "BUTTON").filter((button) => button.textContent === text);
}

const TEXT = {
  wildcardExtraPathsTip: "Path list help",
  wildcardExtraPathPlaceholder: "D:/wildcards",
  removeWildcardPath: "Remove path",
  addWildcardPath: "Add path",
};

const document = createFakeDocument();
const internalValues = new Map([
  ["wildcard.extra_paths", '  first path  \r\n"second path"'],
]);
const readCalls = [];
const updateCalls = [];
const setterCalls = [];

const createWildcardExtraPathsEditor =
  wildcardPathEditorModule.createWildcardExtraPathsEditorFactory({
    document,
    text: (key) => TEXT[key] ?? key,
    readInternalSetting(key, fallback) {
      readCalls.push({ key, fallback });
      return internalValues.has(key) ? internalValues.get(key) : fallback;
    },
    updateInternalSetting(id, value, type) {
      updateCalls.push({ id, value, type });
    },
  });

assert.equal(typeof createWildcardExtraPathsEditor, "function");
assert.equal(document.createdElements.length, 0, "Factory must not create DOM eagerly");

const row = createWildcardExtraPathsEditor(
  "Extra wildcard paths",
  (value) => setterCalls.push(value),
  "renderer path",
);
const label = findOne(row, "LABEL");
let inputs = findAll(row, "INPUT");
let removeButtons = buttonsByText(row, "x");
const addButton = buttonsByText(row, "+")[0];

assert.deepEqual(row.children.map((child) => child.tagName), ["TD", "TD"]);
assert.equal(label.textContent, "Extra wildcard paths");
assert.equal(label.title, "Path list help");
assert.deepEqual(inputs.map((input) => input.value), ["first path", "second path"]);
assert.ok(inputs.every((input) => input.type === "text"));
assert.ok(inputs.every((input) => input.placeholder === "D:/wildcards"));
assert.ok(inputs.every((input) => input.spellcheck === false));
assert.deepEqual(removeButtons.map((button) => button.title), [
  "Remove path",
  "Remove path",
]);
assert.equal(addButton.title, "Add path");
assert.deepEqual(readCalls, [
  { key: "wildcard.extra_paths", fallback: "renderer path" },
]);
assert.deepEqual(updateCalls, [], "Initial render must not update internal settings");
assert.deepEqual(setterCalls, [], "Initial render must not call the setter");

inputs[0].value = "  changed path  ";
inputs[0].emit("input");
assert.deepEqual(updateCalls.at(-1), {
  id: "EasyUseAnima.Wildcard.ExtraPaths",
  value: "changed path\nsecond path",
  type: "text",
});
assert.equal(inputs[0].value, "  changed path  ", "Raw input must stay visible");
assert.deepEqual(setterCalls, [], "Input must only sync internal state");

inputs[0].emit("change");
assert.deepEqual(setterCalls, ["changed path\nsecond path"]);
inputs[0].emit("blur");
assert.deepEqual(
  setterCalls,
  ["changed path\nsecond path"],
  "Change followed by blur must not persist twice",
);

inputs[1].value = "enter path";
inputs[1].emit("input");
inputs[1].focus();
const enterEvent = inputs[1].emit("keydown", { key: "Enter" });
assert.equal(enterEvent.defaultPrevented, true);
assert.equal(inputs[1].focused, false);
assert.deepEqual(setterCalls, [
  "changed path\nsecond path",
  "changed path\nenter path",
]);

const updateCountBeforeAdd = updateCalls.length;
const setterCountBeforeAdd = setterCalls.length;
addButton.emit("click");
inputs = findAll(row, "INPUT");
assert.equal(inputs.length, 3);
assert.equal(inputs[2].value, "");
assert.equal(inputs[2].focused, true, "Added row input must receive focus");
assert.equal(updateCalls.length, updateCountBeforeAdd, "Add must not persist eagerly");
assert.equal(setterCalls.length, setterCountBeforeAdd, "Add must not call the setter");

inputs[2].value = "third path";
inputs[2].emit("input");
inputs[2].emit("change");
assert.equal(setterCalls.at(-1), "changed path\nenter path\nthird path");

removeButtons = buttonsByText(row, "x");
removeButtons[1].emit("click");
inputs = findAll(row, "INPUT");
assert.deepEqual(inputs.map((input) => input.value), ["  changed path  ", "third path"]);
assert.equal(setterCalls.at(-1), "changed path\nthird path");

removeButtons = buttonsByText(row, "x");
removeButtons[0].emit("click");
inputs = findAll(row, "INPUT");
assert.deepEqual(inputs.map((input) => input.value), ["third path"]);
assert.equal(setterCalls.at(-1), "third path");

removeButtons = buttonsByText(row, "x");
removeButtons[0].emit("click");
inputs = findAll(row, "INPUT");
assert.deepEqual(inputs.map((input) => input.value), [""]);
assert.equal(setterCalls.at(-1), "");

const setterCountBeforeEmptyRemove = setterCalls.length;
buttonsByText(row, "x")[0].emit("click");
assert.equal(findAll(row, "INPUT").length, 1);
assert.equal(setterCalls.length, setterCountBeforeEmptyRemove);
assert.equal(updateCalls.at(-1).value, "", "Empty-row removal must still sync internal state");
assert.ok(
  updateCalls.every((call) => call.type === "text"),
  "Every internal update must preserve the text setting type",
);

const fallbackDocument = createFakeDocument();
const fallbackEditor = wildcardPathEditorModule.createWildcardExtraPathsEditorFactory({
  document: fallbackDocument,
  text: (key) => TEXT[key] ?? key,
  readInternalSetting: (_key, fallback) => fallback,
  updateInternalSetting() {},
});
const explicitRow = fallbackEditor("Paths", null, ' explicit one \n"explicit two"');
assert.deepEqual(findAll(explicitRow, "INPUT").map((input) => input.value), [
  "explicit one",
  "explicit two",
]);
const emptyRow = fallbackEditor("Paths", null, undefined);
assert.deepEqual(findAll(emptyRow, "INPUT").map((input) => input.value), [""]);

const emptyInternalEditor = wildcardPathEditorModule.createWildcardExtraPathsEditorFactory({
  document: createFakeDocument(),
  text: (key) => TEXT[key] ?? key,
  readInternalSetting: () => "",
  updateInternalSetting() {},
});
const emptyInternalRow = emptyInternalEditor("Paths", null, "must be ignored");
assert.deepEqual(
  findAll(emptyInternalRow, "INPUT").map((input) => input.value),
  [""],
  "An explicit empty internal value must win over the renderer value",
);

console.log("Settings wildcard path editor smoke passed.");
