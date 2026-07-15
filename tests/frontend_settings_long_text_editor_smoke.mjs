import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

function dataModule(relativePath) {
  const source = readFileSync(new URL(relativePath, import.meta.url), "utf8");
  return "data:text/javascript;base64," + Buffer.from(source).toString("base64");
}

const longTextEditorModule = await import(
  dataModule("../web/js/settings/long_text_editor.js")
);
const definitionData = await import(
  dataModule("../web/js/settings/definition_data.js")
);

assert.deepEqual(Object.keys(longTextEditorModule), [
  "createLongTextEditorButtonFactory",
]);

class FakeElement {
  constructor(tagName) {
    this.tagName = String(tagName).toUpperCase();
    this.children = [];
    this.parentElement = null;
    this.style = { cssText: "" };
    this.listeners = new Map();
    this.className = "";
    this.textContent = "";
    this.type = "";
    this.value = "";
    this.rows = 0;
    this.spellcheck = true;
    this.disabled = false;
    this.focused = false;
    this.removed = false;
    this.onclick = null;
  }

  append(...children) {
    for (const child of children) {
      child.parentElement = this;
      this.children.push(child);
    }
  }

  prepend(...children) {
    for (const child of [...children].reverse()) {
      child.parentElement = this;
      this.children.unshift(child);
    }
  }

  addEventListener(type, handler) {
    const handlers = this.listeners.get(type) || [];
    handlers.push(handler);
    this.listeners.set(type, handlers);
  }

  emit(type, event = {}) {
    const nextEvent = {
      target: this,
      stopPropagation() {},
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

  remove() {
    if (this.parentElement) {
      const index = this.parentElement.children.indexOf(this);
      if (index >= 0) {
        this.parentElement.children.splice(index, 1);
      }
    }
    this.parentElement = null;
    this.removed = true;
  }
}

class FakeDocument {
  constructor() {
    this.body = new FakeElement("body");
    this.createdElements = [];
    this.listeners = new Map();
  }

  createElement(tagName) {
    const element = new FakeElement(tagName);
    this.createdElements.push(element);
    return element;
  }

  addEventListener(type, handler, capture = false) {
    const entries = this.listeners.get(type) || [];
    entries.push({ handler, capture });
    this.listeners.set(type, entries);
  }

  removeEventListener(type, handler, capture = false) {
    const entries = this.listeners.get(type) || [];
    this.listeners.set(
      type,
      entries.filter((entry) => entry.handler !== handler || entry.capture !== capture),
    );
  }

  dispatchKey(key) {
    for (const entry of [...(this.listeners.get("keydown") || [])]) {
      entry.handler({ key });
    }
  }

  listenerCount(type) {
    return (this.listeners.get(type) || []).length;
  }
}

function descendants(root) {
  const values = [];
  for (const child of root.children) {
    values.push(child, ...descendants(child));
  }
  return values;
}

function findOne(root, predicate, message) {
  const found = [root, ...descendants(root)].find(predicate);
  assert.ok(found, message);
  return found;
}

function findAll(root, predicate) {
  return [root, ...descendants(root)].filter(predicate);
}

function button(root, label) {
  return findOne(
    root,
    (element) => element.tagName === "BUTTON" && element.textContent === label,
    `Missing button: ${label}`,
  );
}

function overlay(document) {
  return findOne(
    document.body,
    (element) => element.className === "easyuse-anima-long-text-overlay",
    "Missing long-text overlay",
  );
}

function deferred() {
  let resolve;
  let reject;
  const promise = new Promise((resolvePromise, rejectPromise) => {
    resolve = resolvePromise;
    reject = rejectPromise;
  });
  return { promise, resolve, reject };
}

async function flushPromises() {
  await Promise.resolve();
  await Promise.resolve();
}

const TEXT = {
  openEditor: "Open editor",
  cancel: "Cancel",
  save: "Save",
  saved: "Saved",
  saveFailed: "Save failed",
  editPromptStudioLongText: "Prompt Studio long text",
  editPromptStudioLongTextTip: "Prompt Studio long text help",
  editNaiaLongText: "NAIA long text",
  editNaiaLongTextTip: "NAIA long text help",
  metadataFilter: "Metadata filter",
  metadataFilterTip: "Metadata filter help",
  prePrompt: "Pre prompt",
  postPrompt: "Post prompt",
  autoHide: "Auto hide",
};

const document = new FakeDocument();
const loadCalls = [];
const saveCalls = [];
const scheduled = [];

function loadSettings() {
  const task = deferred();
  loadCalls.push(task);
  return task.promise;
}

function saveSettings(values) {
  const task = deferred();
  saveCalls.push({ values: structuredClone(values), task });
  return task.promise;
}

function schedule(callback, delay) {
  scheduled.push({ callback, delay });
}

const createLongTextEditorButton = (
  longTextEditorModule.createLongTextEditorButtonFactory({
    document,
    fieldGroups: definitionData.LONG_TEXT_FIELD_GROUPS,
    text: (key) => TEXT[key] || key,
    loadSettings,
    saveSettings,
    schedule,
  })
);

assert.equal(document.createdElements.length, 0, "factory creation must not touch the DOM");
assert.equal(document.listenerCount("keydown"), 0);
assert.equal(loadCalls.length, 0);
assert.equal(saveCalls.length, 0);
assert.equal(scheduled.length, 0);

const promptButtonRow = createLongTextEditorButton("promptStudio");
assert.equal(button(promptButtonRow, "Open editor").type, "button");
assert.ok(
  descendants(promptButtonRow).some(
    (element) => element.textContent === "Prompt Studio long text help",
  ),
);

button(promptButtonRow, "Open editor").onclick();
let currentOverlay = overlay(document);
let currentPanel = findOne(
  currentOverlay,
  (element) => element.className === "comfy-settings easyuse-anima-long-text-panel",
  "Missing long-text panel",
);
assert.equal(document.listenerCount("keydown"), 1);
assert.equal(document.listeners.get("keydown")[0].capture, true);
assert.equal(loadCalls.length, 1);

const promptTextareas = findAll(
  currentPanel,
  (element) => element.tagName === "TEXTAREA",
);
assert.equal(promptTextareas.length, 1);
assert.equal(promptTextareas[0].rows, 8);
assert.equal(promptTextareas[0].spellcheck, false);
loadCalls[0].resolve({
  "prompt.metadata_filter_words": "line one\n초기값 初音",
});
await flushPromises();
assert.equal(promptTextareas[0].value, "line one\n초기값 初音");
assert.equal(promptTextareas[0].focused, true);
assert.ok(
  descendants(currentPanel).some(
    (element) => element.textContent === "Metadata filter help",
  ),
);

let panelStopped = false;
currentPanel.emit("mousedown", {
  target: currentPanel,
  stopPropagation() {
    panelStopped = true;
  },
});
assert.equal(panelStopped, true);
currentOverlay.emit("mousedown", { target: currentPanel });
assert.equal(currentOverlay.removed, false, "panel mousedown must not close the dialog");

button(currentPanel, "Cancel").onclick();
assert.equal(currentOverlay.removed, true);
assert.equal(document.listenerCount("keydown"), 0);
assert.equal(saveCalls.length, 0);

button(promptButtonRow, "Open editor").onclick();
currentOverlay = overlay(document);
currentPanel = findOne(
  currentOverlay,
  (element) => element.className === "comfy-settings easyuse-anima-long-text-panel",
  "Missing reopened panel",
);
const staleTextarea = findAll(currentPanel, (element) => element.tagName === "TEXTAREA")[0];
currentOverlay.emit("mousedown", { target: currentOverlay });
assert.equal(currentOverlay.removed, true);
assert.equal(document.listenerCount("keydown"), 0);
loadCalls[1].resolve({ "prompt.metadata_filter_words": "stale response" });
await flushPromises();
assert.equal(staleTextarea.value, "", "closed dialog must ignore a stale load response");
assert.equal(staleTextarea.focused, false);

button(promptButtonRow, "Open editor").onclick();
currentOverlay = overlay(document);
loadCalls[2].resolve({});
await flushPromises();
document.dispatchKey("Escape");
assert.equal(currentOverlay.removed, true);
assert.equal(document.listenerCount("keydown"), 0);

const naiaButtonRow = createLongTextEditorButton("naia");
button(naiaButtonRow, "Open editor").onclick();
currentOverlay = overlay(document);
currentPanel = findOne(
  currentOverlay,
  (element) => element.className === "comfy-settings easyuse-anima-long-text-panel",
  "Missing NAIA panel",
);
const naiaTextareas = findAll(currentPanel, (element) => element.tagName === "TEXTAREA");
assert.equal(naiaTextareas.length, 3);
assert.deepEqual(naiaTextareas.map((textarea) => textarea.rows), [7, 7, 7]);
loadCalls[3].resolve({
  "naia.pre_prompt": "pre\n한글",
  "naia.post_prompt": "post 初音",
  "naia.auto_hide": "hide\nvalue",
});
await flushPromises();
assert.deepEqual(
  naiaTextareas.map((textarea) => textarea.value),
  ["pre\n한글", "post 初音", "hide\nvalue"],
);
assert.equal(naiaTextareas[0].focused, true);
button(currentPanel, "Cancel").onclick();

button(promptButtonRow, "Open editor").onclick();
currentOverlay = overlay(document);
currentPanel = findOne(
  currentOverlay,
  (element) => element.className === "comfy-settings easyuse-anima-long-text-panel",
  "Missing save panel",
);
loadCalls[4].resolve({ "prompt.metadata_filter_words": "before" });
await flushPromises();
const saveTextarea = findAll(currentPanel, (element) => element.tagName === "TEXTAREA")[0];
saveTextarea.value = "  line one\n저장 初音  ";
const saveButton = button(currentPanel, "Save");
const savePromise = saveButton.onclick();
assert.equal(saveButton.disabled, true);
assert.equal(saveCalls.length, 1);
assert.deepEqual(saveCalls[0].values, {
  "prompt.metadata_filter_words": "  line one\n저장 初音  ",
});
assert.ok(
  descendants(currentPanel).some((element) => element.textContent === "..."),
);
saveCalls[0].task.resolve({});
await savePromise;
assert.equal(saveButton.disabled, false);
assert.equal(scheduled.length, 1);
assert.equal(scheduled[0].delay, 150);
assert.ok(
  descendants(currentPanel).some(
    (element) => element.textContent === "Saved" && element.style.color === "#16a34a",
  ),
);

button(naiaButtonRow, "Open editor").onclick();
const newerOverlay = overlay(document);
assert.notEqual(newerOverlay, currentOverlay);
assert.equal(currentOverlay.removed, true);
scheduled[0].callback();
assert.equal(newerOverlay.removed, false, "an older delayed close must not close a newer dialog");
loadCalls[5].resolve({});
await flushPromises();
button(findOne(
  newerOverlay,
  (element) => element.className === "comfy-settings easyuse-anima-long-text-panel",
  "Missing newer panel",
), "Cancel").onclick();

button(promptButtonRow, "Open editor").onclick();
currentOverlay = overlay(document);
currentPanel = findOne(
  currentOverlay,
  (element) => element.className === "comfy-settings easyuse-anima-long-text-panel",
  "Missing close-after-save panel",
);
loadCalls[6].resolve({});
await flushPromises();
const closeSaveButton = button(currentPanel, "Save");
const closeSavePromise = closeSaveButton.onclick();
saveCalls[1].task.resolve({});
await closeSavePromise;
assert.equal(scheduled[1].delay, 150);
scheduled[1].callback();
assert.equal(currentOverlay.removed, true);
assert.equal(document.listenerCount("keydown"), 0);

button(promptButtonRow, "Open editor").onclick();
currentOverlay = overlay(document);
currentPanel = findOne(
  currentOverlay,
  (element) => element.className === "comfy-settings easyuse-anima-long-text-panel",
  "Missing failure panel",
);
loadCalls[7].resolve({});
await flushPromises();
const failedSaveButton = button(currentPanel, "Save");
const failedSavePromise = failedSaveButton.onclick();
saveCalls[2].task.reject(new Error("backend unavailable"));
await failedSavePromise;
assert.equal(failedSaveButton.disabled, false);
assert.equal(currentOverlay.removed, false);
assert.ok(
  descendants(currentPanel).some(
    (element) => element.textContent === "Save failed: backend unavailable"
      && element.style.color === "#dc2626",
  ),
);
assert.equal(scheduled.length, 2, "failed saves must not schedule a close");
button(currentPanel, "Cancel").onclick();

assert.equal(document.body.children.length, 0);
assert.equal(document.listenerCount("keydown"), 0);
console.log("Settings long-text editor smoke passed.");
