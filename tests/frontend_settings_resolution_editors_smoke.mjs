import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

function dataModule(relativePath, replacements = {}) {
  let source = readFileSync(new URL(relativePath, import.meta.url), "utf8");
  for (const [from, to] of Object.entries(replacements)) {
    source = source.replaceAll(from, to);
  }
  return "data:text/javascript;base64," + Buffer.from(source).toString("base64");
}

const definitionDataUrl = dataModule("../web/js/settings/definition_data.js");
const resolutionEditorsModule = await import(
  dataModule("../web/js/settings/resolution_editors.js", {
    "./definition_data.js": definitionDataUrl,
  })
);

assert.deepEqual(Object.keys(resolutionEditorsModule), ["createResolutionEditors"]);

class FakeElement {
  constructor(tagName) {
    this.tagName = String(tagName).toUpperCase();
    this.children = [];
    this.parentElement = null;
    this.style = { cssText: "" };
    this.listeners = new Map();
    this.attributes = new Map();
    this.textContent = "";
    this.title = "";
    this.type = "";
    this.inputMode = "";
    this.value = "";
    this.placeholder = "";
    this.spellcheck = true;
    this.selected = false;
    this.focused = false;
  }

  append(...children) {
    for (const child of children) {
      child.parentElement = this;
      this.children.push(child);
      if (this.tagName === "SELECT" && child.tagName === "OPTION" && child.selected) {
        this.value = child.value;
      }
    }
  }

  setAttribute(name, value) {
    this.attributes.set(name, String(value));
  }

  getAttribute(name) {
    return this.attributes.get(name) ?? null;
  }

  addEventListener(type, handler) {
    const handlers = this.listeners.get(type) || [];
    handlers.push(handler);
    this.listeners.set(type, handlers);
  }

  emit(type, event = {}) {
    const nextEvent = {
      target: this,
      defaultPrevented: false,
      preventDefault() {
        this.defaultPrevented = true;
      },
      ...event,
    };
    for (const handler of this.listeners.get(type) || []) {
      handler(nextEvent);
    }
    return nextEvent;
  }

  focus() {
    this.focused = true;
  }

  blur() {
    this.focused = false;
    this.emit("blur");
  }
}

class FakeDocument {
  constructor() {
    this.createdElements = [];
  }

  createElement(tagName) {
    const element = new FakeElement(tagName);
    this.createdElements.push(element);
    return element;
  }
}

function descendants(root) {
  const values = [];
  for (const child of root.children) {
    values.push(child, ...descendants(child));
  }
  return values;
}

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

const TEXT = {
  naiaResolutionModeTip: "Mode help",
  naiaResolutionModeOriginalScale: "Original scale",
  naiaResolutionModeBucketFit: "Bucket fit",
  naiaResolutionScaleTip: "Scale help",
};

const document = new FakeDocument();
const internalValues = new Map([
  ["naia.resolution_mode", "bucket_fit"],
  ["naia.resolution_scale", "1,75"],
]);
const readCalls = [];
const updateCalls = [];
const modeSetterCalls = [];
const scaleSetterCalls = [];

const editors = resolutionEditorsModule.createResolutionEditors({
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

assert.deepEqual(Object.keys(editors), [
  "createNaiaResolutionModeEditor",
  "createNaiaResolutionScaleEditor",
]);
assert.equal(document.createdElements.length, 0, "Factory must not create DOM eagerly");

const modeRow = editors.createNaiaResolutionModeEditor(
  "Resolution mode",
  (value) => modeSetterCalls.push(value),
  "scale",
);
const modeLabel = findOne(modeRow, "LABEL");
const modeSelect = findOne(modeRow, "SELECT");
const modeOptions = findAll(modeRow, "OPTION");

assert.equal(modeLabel.textContent, "Resolution mode");
assert.equal(modeLabel.title, "Mode help");
assert.equal(modeSelect.getAttribute("aria-label"), "Resolution mode");
assert.equal(modeSelect.value, "bucket", "Internal bucket_fit alias must win");
assert.deepEqual(modeOptions.map((option) => option.value), ["scale", "bucket"]);
assert.deepEqual(modeOptions.map((option) => option.textContent), [
  "Original scale",
  "Bucket fit",
]);
assert.deepEqual(updateCalls, [
  {
    id: "EasyUseAnima.NAIA.ResolutionMode",
    value: "bucket",
    type: "text",
  },
]);
assert.deepEqual(modeSetterCalls, []);

modeSelect.value = "scale";
modeSelect.emit("change");
assert.equal(updateCalls.at(-1).value, "scale");
assert.deepEqual(modeSetterCalls, ["scale"]);
modeSelect.emit("change");
assert.deepEqual(modeSetterCalls, ["scale"], "Unchanged mode must not persist twice");

const scaleRow = editors.createNaiaResolutionScaleEditor(
  "Resolution scale",
  (value) => scaleSetterCalls.push(value),
  "3.0",
);
const scaleLabel = findOne(scaleRow, "LABEL");
const scaleInput = findOne(scaleRow, "INPUT");

assert.equal(scaleLabel.textContent, "Resolution scale");
assert.equal(scaleLabel.title, "Scale help");
assert.equal(scaleInput.type, "text");
assert.equal(scaleInput.inputMode, "decimal");
assert.equal(scaleInput.placeholder, "1.5");
assert.equal(scaleInput.spellcheck, false);
assert.equal(scaleInput.value, "1.75", "Internal comma decimal must win");
assert.equal(updateCalls.at(-1).id, "EasyUseAnima.NAIA.ResolutionScale");
assert.equal(updateCalls.at(-1).value, "1.75");
assert.deepEqual(scaleSetterCalls, []);

scaleInput.value = "2,375";
scaleInput.emit("input");
assert.equal(updateCalls.at(-1).value, "2.375", "Input must sync raw comma form");
assert.deepEqual(scaleSetterCalls, [], "Raw input must not call the setter");
scaleInput.emit("change");
assert.equal(scaleInput.value, "2.375");
assert.deepEqual(scaleSetterCalls, ["2.375"]);

scaleInput.value = "9";
scaleInput.emit("blur");
assert.equal(scaleInput.value, "4.0");
assert.deepEqual(scaleSetterCalls, ["2.375", "4.0"]);

scaleInput.value = "0,1";
const enterEvent = scaleInput.emit("keydown", { key: "Enter" });
assert.equal(enterEvent.defaultPrevented, true);
assert.equal(scaleInput.value, "0.25");
assert.deepEqual(scaleSetterCalls, ["2.375", "4.0", "0.25"]);

scaleInput.value = "invalid";
scaleInput.emit("change");
assert.equal(scaleInput.value, "1.0");
assert.deepEqual(scaleSetterCalls, ["2.375", "4.0", "0.25", "1.0"]);

assert.deepEqual(readCalls, [
  { key: "naia.resolution_mode", fallback: "scale" },
  { key: "naia.resolution_scale", fallback: "3.0" },
]);
assert.ok(
  updateCalls.every((call) => call.type === "text"),
  "Every internal update must preserve the text setting type",
);

const fallbackDocument = new FakeDocument();
const fallbackEditors = resolutionEditorsModule.createResolutionEditors({
  document: fallbackDocument,
  text: (key) => TEXT[key] ?? key,
  readInternalSetting: (_key, fallback) => fallback,
  updateInternalSetting() {},
});
const explicitMode = findOne(
  fallbackEditors.createNaiaResolutionModeEditor("Mode", null, "bucket_fit"),
  "SELECT",
);
const explicitScale = findOne(
  fallbackEditors.createNaiaResolutionScaleEditor("Scale", null, "2,5"),
  "INPUT",
);
assert.equal(explicitMode.value, "bucket");
assert.equal(explicitScale.value, "2.5");

const fallbackMode = findOne(
  fallbackEditors.createNaiaResolutionModeEditor("Mode", null, undefined),
  "SELECT",
);
const fallbackScale = findOne(
  fallbackEditors.createNaiaResolutionScaleEditor("Scale", null, undefined),
  "INPUT",
);
assert.equal(fallbackMode.value, "scale");
assert.equal(fallbackScale.value, "1.0");

console.log("Settings resolution editors smoke passed.");
