import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

function dataModule(relativePath) {
  const source = readFileSync(new URL(relativePath, import.meta.url), "utf8");
  return "data:text/javascript;base64," + Buffer.from(source).toString("base64");
}

const colorEditorModule = await import(
  dataModule("../web/js/settings/color_editor.js")
);

assert.deepEqual(Object.keys(colorEditorModule), [
  "createPromptStudioColorEditorButtonFactory",
]);

class FakeElement {
  constructor(tagName) {
    this.tagName = String(tagName).toUpperCase();
    this.children = [];
    this.parentElement = null;
    this.style = { cssText: "", background: "", borderColor: "" };
    this.listeners = new Map();
    this.attributes = new Map();
    this.className = "";
    this.textContent = "";
    this.type = "";
    this.value = "";
    this.removed = false;
    this.onclick = null;
  }

  append(...children) {
    for (const child of children) {
      child.parentElement = this;
      this.children.push(child);
    }
  }

  replaceChildren(...children) {
    for (const child of this.children) {
      child.parentElement = null;
    }
    this.children = [];
    this.append(...children);
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
      propagationStopped: false,
      stopPropagation() {
        this.propagationStopped = true;
      },
      ...event,
    };
    for (const handler of this.listeners.get(type) || []) {
      handler(nextEvent);
    }
    return nextEvent;
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

function findAll(root, predicate) {
  return [root, ...descendants(root)].filter(predicate);
}

function findOne(root, predicate, message) {
  const matches = findAll(root, predicate);
  assert.equal(matches.length, 1, `${message}: found ${matches.length}`);
  return matches[0];
}

function button(root, text) {
  return findOne(
    root,
    (element) => element.tagName === "BUTTON" && element.textContent === text,
    `Missing button ${text}`,
  );
}

function overlay(document) {
  return findOne(
    document.body,
    (element) => element.className === "easyuse-anima-prompt-color-overlay",
    "Missing color overlay",
  );
}

function panel(root) {
  return findOne(
    root,
    (element) => element.className === "comfy-settings easyuse-anima-prompt-color-panel",
    "Missing color panel",
  );
}

function tabButtons(root) {
  return findAll(
    root,
    (element) => element.tagName === "BUTTON" && element.getAttribute("role") === "tab",
  );
}

function colorInputs(root) {
  return findAll(
    root,
    (element) => element.tagName === "INPUT" && element.type === "color",
  );
}

const TEXT = {
  openEditor: "Open editor",
  highlightColorEditor: "Highlight colors",
  highlightColorEditorTip: "Highlight color help",
  highlightColorTabTags: "Tags",
  highlightColorTabSyntax: "Syntax",
  reset: "Reset",
  close: "Close",
};

const TAG_LABELS = [
  "Quality",
  "Rating",
  "Year",
  "Count",
  "Trained tag",
  "Character",
  "Artist",
  "Unregistered artist",
  "Copyright",
  "Meta",
  "Unknown",
];
const TAG_DEFAULTS = [
  "#facc15",
  "#38bdf8",
  "#2dd4bf",
  "#60a5fa",
  "#4ade80",
  "#f472b6",
  "#a78bfa",
  "#f87171",
  "#fb923c",
  "#94a3b8",
  "#cbd5e1",
];
const SYNTAX_LABELS = [
  "Natural language",
  "Translation marker",
  "Wildcard",
  "Comment",
];
const SYNTAX_DEFAULTS = ["#cbd5e1", "#22d3ee", "#c084fc", "#9ca3af"];

const document = new FakeDocument();
const internalValues = new Map([
  ["prompt_studio.colors", '{"quality":"#000000"}'],
]);
const readCalls = [];
const updateCalls = [];
const firstSetterCalls = [];
const secondSetterCalls = [];
const callOrder = [];

const createPromptStudioColorEditorButton =
  colorEditorModule.createPromptStudioColorEditorButtonFactory({
    document,
    text: (key) => TEXT[key] ?? key,
    label: (item) => item?.en ?? "",
    tip: (item) => item?.tip?.en ?? "",
    readInternalSetting(key, fallback) {
      readCalls.push({ key, fallback });
      return internalValues.has(key) ? internalValues.get(key) : fallback;
    },
    updateInternalSetting(id, value, type) {
      updateCalls.push({ id, value, type });
      callOrder.push(`update:${value}`);
      if (id === "EasyUseAnima.Prompt.HighlightColors") {
        internalValues.set("prompt_studio.colors", value);
      }
    },
  });

assert.equal(typeof createPromptStudioColorEditorButton, "function");
assert.equal(document.createdElements.length, 0, "Factory must not create DOM eagerly");
assert.equal(document.body.children.length, 0);
assert.equal(document.listenerCount("keydown"), 0);

const rendererValue = '{"quality":"#010101"}';
const firstTrigger = createPromptStudioColorEditorButton(
  "Colors",
  (value) => {
    firstSetterCalls.push(value);
    callOrder.push(`setter:${value}`);
  },
  rendererValue,
);
assert.equal(button(firstTrigger, "Open editor").type, "button");
assert.ok(
  descendants(firstTrigger).some((element) => element.textContent === "Highlight color help"),
);
assert.deepEqual(readCalls, [], "Creating a trigger must not read settings");
assert.deepEqual(updateCalls, [], "Creating a trigger must not persist settings");

internalValues.set(
  "prompt_studio.colors",
  JSON.stringify({
    quality: "#ABCDEF",
    bogus: "#111111",
    safety: "#123",
    copyright: " #A1B2C3 ",
    natural: null,
  }),
);
button(firstTrigger, "Open editor").onclick();

let currentOverlay = overlay(document);
let currentPanel = panel(currentOverlay);
let tabs = tabButtons(currentPanel);
let inputs = colorInputs(currentPanel);

assert.equal(document.body.children.length, 1);
assert.equal(document.listenerCount("keydown"), 1);
assert.equal(document.listeners.get("keydown")[0].capture, true);
assert.deepEqual(readCalls, [
  { key: "prompt_studio.colors", fallback: rendererValue },
]);
assert.deepEqual(updateCalls, [], "Opening the editor must not persist settings");
assert.deepEqual(firstSetterCalls, []);
assert.deepEqual(tabs.map((tab) => tab.textContent), ["Tags", "Syntax"]);
assert.deepEqual(tabs.map((tab) => tab.getAttribute("aria-selected")), ["true", "false"]);
assert.deepEqual(inputs.map((input) => input.getAttribute("aria-label")), TAG_LABELS);
assert.deepEqual(inputs.map((input) => input.value), [
  "#ABCDEF",
  ...TAG_DEFAULTS.slice(1),
]);
assert.ok(
  descendants(inputs[0].parentElement).some(
    (element) => element.textContent.startsWith("ANIMA quality/meta tags"),
  ),
  "Locale tip output must be rendered",
);

inputs[0].value = "#123456";
inputs[0].emit("input");
const firstSerialized = '{"quality":"#123456","copyright":"#A1B2C3"}';
assert.deepEqual(updateCalls.at(-1), {
  id: "EasyUseAnima.Prompt.HighlightColors",
  value: firstSerialized,
  type: "text",
});
assert.deepEqual(firstSetterCalls, [firstSerialized]);
assert.deepEqual(callOrder.slice(-2), [
  `update:${firstSerialized}`,
  `setter:${firstSerialized}`,
]);

inputs[0].emit("change");
assert.deepEqual(
  firstSetterCalls,
  [firstSerialized, firstSerialized],
  "Input and change must each preserve the existing immediate-save behavior",
);

const resetQuality = button(inputs[0].parentElement, "Reset");
resetQuality.emit("click");
const resetSerialized = '{"quality":"#facc15","copyright":"#A1B2C3"}';
assert.equal(inputs[0].value, "#facc15");
assert.equal(firstSetterCalls.at(-1), resetSerialized);

const updatesBeforeTab = updateCalls.length;
tabs[1].onclick();
tabs = tabButtons(currentPanel);
inputs = colorInputs(currentPanel);
assert.deepEqual(tabs.map((tab) => tab.getAttribute("aria-selected")), ["false", "true"]);
assert.deepEqual(inputs.map((input) => input.getAttribute("aria-label")), SYNTAX_LABELS);
assert.deepEqual(inputs.map((input) => input.value), SYNTAX_DEFAULTS);
assert.equal(updateCalls.length, updatesBeforeTab, "Tab changes must not persist settings");

inputs[0].value = "#654321";
inputs[0].emit("input");
const syntaxSerialized =
  '{"quality":"#facc15","copyright":"#A1B2C3","natural":"#654321"}';
assert.equal(firstSetterCalls.at(-1), syntaxSerialized);

tabs[0].onclick();
inputs = colorInputs(currentPanel);
assert.equal(inputs.length, 11, "Tab content must replace rather than accumulate rows");
assert.equal(inputs[0].value, "#facc15", "Color state must survive a tab round trip");

const panelEvent = currentPanel.emit("mousedown", { target: currentPanel });
assert.equal(panelEvent.propagationStopped, true);
currentOverlay.emit("mousedown", { target: currentPanel });
assert.equal(currentOverlay.removed, false, "Panel mousedown must not close the editor");

const secondTrigger = createPromptStudioColorEditorButton(
  "Colors two",
  (value) => {
    secondSetterCalls.push(value);
    callOrder.push(`setter-two:${value}`);
  },
  '{"quality":"#020202"}',
);
const firstSetterCountBeforeReopen = firstSetterCalls.length;
button(secondTrigger, "Open editor").onclick();
assert.equal(currentOverlay.removed, true, "Opening another trigger must close the old overlay");
assert.equal(document.body.children.length, 1);
assert.equal(document.listenerCount("keydown"), 1, "Reopen must not leak key listeners");
assert.equal(firstSetterCalls.length, firstSetterCountBeforeReopen);

currentOverlay = overlay(document);
currentPanel = panel(currentOverlay);
inputs = colorInputs(currentPanel);
assert.equal(inputs[0].value, "#facc15", "Reopen must read the latest internal value");
assert.equal(inputs[8].value, "#A1B2C3");
inputs[1].value = "#112233";
inputs[1].emit("input");
assert.equal(secondSetterCalls.length, 1);
assert.equal(firstSetterCalls.length, firstSetterCountBeforeReopen);

const updateCountBeforeBackdrop = updateCalls.length;
const setterCountBeforeBackdrop = secondSetterCalls.length;
currentOverlay.emit("mousedown", { target: currentOverlay });
assert.equal(currentOverlay.removed, true);
assert.equal(document.body.children.length, 0);
assert.equal(document.listenerCount("keydown"), 0);
assert.equal(updateCalls.length, updateCountBeforeBackdrop, "Backdrop close must not persist");
assert.equal(secondSetterCalls.length, setterCountBeforeBackdrop);

button(secondTrigger, "Open editor").onclick();
currentOverlay = overlay(document);
document.dispatchKey("Escape");
assert.equal(currentOverlay.removed, true);
assert.equal(document.listenerCount("keydown"), 0);

button(secondTrigger, "Open editor").onclick();
currentOverlay = overlay(document);
currentPanel = panel(currentOverlay);
const closeButton = button(currentPanel, "Close");
closeButton.onclick();
assert.equal(currentOverlay.removed, true);
assert.equal(document.listenerCount("keydown"), 0);
closeButton.onclick();
assert.equal(document.listenerCount("keydown"), 0, "Closing an already closed editor is a no-op");

internalValues.delete("prompt_studio.colors");
const fallbackTrigger = createPromptStudioColorEditorButton(
  "Fallback",
  null,
  '{"quality":"#010203"}',
);
button(fallbackTrigger, "Open editor").onclick();
currentOverlay = overlay(document);
assert.equal(colorInputs(panel(currentOverlay))[0].value, "#010203");
currentOverlay.emit("mousedown", { target: currentOverlay });

internalValues.set("prompt_studio.colors", "");
const emptyInternalTrigger = createPromptStudioColorEditorButton(
  "Empty internal",
  null,
  '{"quality":"#040506"}',
);
button(emptyInternalTrigger, "Open editor").onclick();
currentOverlay = overlay(document);
currentPanel = panel(currentOverlay);
inputs = colorInputs(currentPanel);
assert.equal(inputs[0].value, "#facc15", "Explicit empty internal state must win");
inputs[0].value = "#0a0b0c";
inputs[0].emit("change");
assert.equal(updateCalls.at(-1).value, '{"quality":"#0a0b0c"}');
button(currentPanel, "Close").onclick();

internalValues.delete("prompt_studio.colors");
const malformedSetterCalls = [];
const malformedTrigger = createPromptStudioColorEditorButton(
  "Malformed",
  (value) => malformedSetterCalls.push(value),
  "{not json",
);
button(malformedTrigger, "Open editor").onclick();
currentOverlay = overlay(document);
currentPanel = panel(currentOverlay);
inputs = colorInputs(currentPanel);
assert.deepEqual(inputs.map((input) => input.value), TAG_DEFAULTS);
assert.deepEqual(readCalls.at(-1), {
  key: "prompt_studio.colors",
  fallback: "{not json",
});
inputs[0].value = "invalid";
inputs[0].emit("input");
assert.equal(updateCalls.at(-1).value, "", "No valid colors must serialize to empty text");
assert.deepEqual(malformedSetterCalls, [""]);
button(currentPanel, "Close").onclick();

internalValues.delete("prompt_studio.colors");
const undefinedTrigger = createPromptStudioColorEditorButton(
  "Undefined",
  null,
  undefined,
);
button(undefinedTrigger, "Open editor").onclick();
currentOverlay = overlay(document);
assert.deepEqual(colorInputs(panel(currentOverlay)).map((input) => input.value), TAG_DEFAULTS);
assert.deepEqual(readCalls.at(-1), {
  key: "prompt_studio.colors",
  fallback: "",
});
button(panel(currentOverlay), "Close").onclick();

assert.equal(document.body.children.length, 0);
assert.equal(document.listenerCount("keydown"), 0);
assert.ok(
  updateCalls.every((call) => call.type === "text"),
  "Every color update must preserve the text setting type",
);

console.log("Settings color editor smoke passed.");
