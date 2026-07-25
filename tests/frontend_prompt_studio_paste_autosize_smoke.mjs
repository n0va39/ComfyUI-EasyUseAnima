import { readFileSync } from "node:fs";
import {
  createFakeDocument,
} from "./frontend_support/fake_dom.mjs";
import {
  createTextareaGrowStabilizer,
  TEXTAREA_FIT_TOLERANCE,
  TEXTAREA_STABILIZATION_FRAMES,
} from "../web/js/prompt_studio/textarea_stabilization.js";

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

function inlineModule(source) {
  return `data:text/javascript;base64,${Buffer.from(source).toString("base64")}`;
}

function dataModule(relativePath, replacements = {}) {
  let source = readFileSync(new URL(relativePath, import.meta.url), "utf8");
  for (const [specifier, replacement] of Object.entries(replacements)) {
    source = source.replaceAll(`"${specifier}"`, `"${replacement}"`);
  }
  return inlineModule(source);
}

let animationFrames = [];
globalThis.requestAnimationFrame = (callback) => {
  animationFrames.push(callback);
  return animationFrames.length;
};

function flushFrame() {
  const callback = animationFrames.shift();
  assert(callback, "Expected a scheduled animation frame");
  callback(0);
}

function resetFrames() {
  animationFrames = [];
}

function heightValue(style) {
  return Math.round(Number.parseFloat(style.height || "") || 0);
}

function createMeasuredTextarea(initialHeight, initialScrollHeight) {
  return {
    isConnected: true,
    scrollHeight: initialScrollHeight,
    style: {
      height: `${initialHeight}px`,
      overflowY: "auto",
    },
    get clientHeight() {
      return heightValue(this.style);
    },
  };
}

assertEqual(TEXTAREA_FIT_TOLERANCE, 2, "Fit tolerance contract");
assertEqual(TEXTAREA_STABILIZATION_FRAMES, 2, "Frame budget contract");

for (const fixture of [
  { type: "EasyUseAnimaPromptStudio", immediate: 150, first: 1680, post: 1728 },
  { type: "EasyUseAnimaPromptStudioExtend", immediate: 120, first: 1812, post: 1860 },
  { type: "EasyUseAnimaPromptStudioAdvanced", immediate: 120, first: 1920, post: 1968 },
  { type: "EasyUseAnimaPromptStudioAdvancedV2", immediate: 120, first: 2040, post: 2088 },
]) {
  resetFrames();
  const textarea = createMeasuredTextarea(fixture.immediate, fixture.immediate);
  let storedHeight = fixture.immediate;
  const stabilizer = createTextareaGrowStabilizer(textarea, () => {
    const currentHeight = textarea.clientHeight;
    const nextHeight = Math.max(currentHeight, textarea.scrollHeight);
    if (nextHeight <= currentHeight + 1) {
      return false;
    }
    textarea.style.height = `${nextHeight}px`;
    storedHeight = nextHeight;
    return true;
  });

  stabilizer.schedule();
  textarea.scrollHeight = fixture.first;
  flushFrame();
  assertEqual(storedHeight, fixture.first, `${fixture.type} first-frame grow`);
  textarea.scrollHeight = fixture.post;
  flushFrame();
  assertEqual(storedHeight, fixture.post, `${fixture.type} post-layout grow`);
  assert(
    textarea.scrollHeight <= textarea.clientHeight + TEXTAREA_FIT_TOLERANCE,
    `${fixture.type} final content does not fit`,
  );
  assertEqual(textarea.style.overflowY, "hidden", `${fixture.type} final overflow`);
}

resetFrames();
const manualTextarea = createMeasuredTextarea(480, 240);
let manualHeight = 480;
const manualStabilizer = createTextareaGrowStabilizer(manualTextarea, () => {
  const nextHeight = Math.max(manualHeight, manualTextarea.scrollHeight);
  if (nextHeight <= manualHeight + 1) {
    return false;
  }
  manualHeight = nextHeight;
  manualTextarea.style.height = `${manualHeight}px`;
  return true;
});
manualStabilizer.schedule();
flushFrame();
assertEqual(manualHeight, 480, "Manual height must not shrink");
manualTextarea.scrollHeight = 720;
manualStabilizer.schedule();
flushFrame();
manualTextarea.scrollHeight = 768;
flushFrame();
assertEqual(manualHeight, 768, "Manual height must grow when content no longer fits");

resetFrames();
const rapidTextarea = createMeasuredTextarea(120, 120);
let rapidGrowCalls = 0;
const rapidStabilizer = createTextareaGrowStabilizer(rapidTextarea, () => {
  rapidGrowCalls += 1;
  rapidTextarea.style.height = `${rapidTextarea.scrollHeight}px`;
  return true;
});
rapidStabilizer.schedule();
rapidTextarea.scrollHeight = 900;
rapidStabilizer.schedule();
flushFrame();
assertEqual(rapidGrowCalls, 0, "Stale revision must not grow");
flushFrame();
assertEqual(rapidGrowCalls, 1, "Latest revision must own growth");

resetFrames();
const removedTextarea = createMeasuredTextarea(120, 900);
let removedGrowCalls = 0;
const removedStabilizer = createTextareaGrowStabilizer(removedTextarea, () => {
  removedGrowCalls += 1;
  return true;
});
removedStabilizer.schedule();
removedTextarea.isConnected = false;
flushFrame();
assertEqual(removedGrowCalls, 0, "Disconnected textarea must be a safe no-op");

class ClassicTextarea {
  constructor(height, scrollHeight) {
    this.dataset = {};
    this.isConnected = true;
    this.listeners = new Map();
    this.scrollHeight = scrollHeight;
    this.style = {
      boxSizing: "",
      fontFamily: "",
      fontSize: "",
      height: `${height}px`,
      minHeight: "0px",
      overflowY: "hidden",
      resize: "",
    };
    this.value = "";
  }

  addEventListener(type, callback) {
    const callbacks = this.listeners.get(type) || [];
    callbacks.push(callback);
    this.listeners.set(type, callbacks);
  }

  emit(type) {
    for (const callback of this.listeners.get(type) || []) {
      callback({ target: this });
    }
  }

  getAttribute(name) {
    return name === "aria-label" ? (this.ariaLabel || null) : null;
  }

  get clientHeight() {
    return heightValue(this.style);
  }

  get offsetHeight() {
    return this.clientHeight;
  }
}

globalThis.HTMLElement = ClassicTextarea;
globalThis.HTMLTextAreaElement = ClassicTextarea;
globalThis.HTMLInputElement = ClassicTextarea;
globalThis.window = {};

const fileUrl = (relativePath) => new URL(relativePath, import.meta.url).href;
const classicResizableUrl = dataModule(
  "../web/js/prompt_studio/studio_resizable_input.js",
  {
    "./constants.js": fileUrl("../web/js/prompt_studio/constants.js"),
    "./highlight.js": inlineModule("export function requestOverlaySync() {}"),
    "./settings.js": inlineModule("export function applyPromptStudioTextStyle() {}"),
    "./studio_textareas.js": fileUrl("../web/js/prompt_studio/studio_textareas.js"),
    "./textarea_stabilization.js": fileUrl("../web/js/prompt_studio/textarea_stabilization.js"),
    "./widgets.js": fileUrl("../web/js/prompt_studio/widgets.js"),
  },
);
const {
  enhanceResizableInput,
} = await import(classicResizableUrl);
const classicOwners = await import("../web/js/prompt_studio/studio_textareas.js");
const {
  resolveStudioInput,
} = await import("../web/js/prompt_studio/studio_input_resolver.js");

const node2FieldNames = [
  "lora_trigger_tags",
  "quality_tags",
  "trigger_and_artist_tags",
  "prompt",
  "trailing_quality_tags",
];
const node2Widgets = node2FieldNames.map((name) => ({ name, options: {} }));
const node2Controls = node2FieldNames.map((name, index) => {
  const control = new ClassicTextarea(64, 64);
  if (index === 0) {
    control.ariaLabel = name;
  }
  return control;
});
const node2NodeElement = {
  dataset: { nodeId: "41" },
  querySelectorAll() {
    return node2Controls;
  },
};
const node2Canvas = {
  parentElement: {
    querySelectorAll() {
      return [node2NodeElement];
    },
  },
};
const node2Node = { id: 41, widgets: node2Widgets };
assertEqual(
  resolveStudioInput(node2Node, node2Widgets[0], node2FieldNames, node2Canvas),
  node2Controls[0],
  "Node 2.0 named field resolves inside owner node",
);
assertEqual(
  resolveStudioInput(node2Node, node2Widgets[3], node2FieldNames, node2Canvas),
  node2Controls[3],
  "Node 2.0 anonymous textarea follows visible field order",
);
assertEqual(
  node2Widgets[3].__easyuseAnimaStudioInput,
  node2Controls[3],
  "Node 2.0 resolver stores only the Prompt Studio-owned seam",
);

function classicFixture(type, name, initialHeight, manual = false, node2 = false) {
  resetFrames();
  const input = new ClassicTextarea(initialHeight, initialHeight);
  const overlay = { style: { height: "" } };
  const widget = {
    name,
    __easyuseAnimaHeight: initialHeight,
    __easyuseAnimaManualHeight: manual,
  };
  if (node2) {
    widget.element = {
      querySelector(selector) {
        return selector === "textarea, input" ? input : null;
      },
    };
  } else {
    widget.inputEl = input;
  }
  const ownerHooks = {
    refreshNodeSize() {},
    updateHighlight() {
      overlay.style.height = input.style.height;
    },
  };
  const hooks = {
    expandStudioInputToContent(node, target, refresh) {
      classicOwners.expandStudioInputToContent(node, target, refresh, ownerHooks);
    },
    growStudioManualHeightToContent(node, target, refresh) {
      return classicOwners.growStudioManualHeightToContent(node, target, refresh, ownerHooks);
    },
    setStudioInputHeight(node, target, height, refresh) {
      classicOwners.setStudioInputHeight(node, target, height, refresh, ownerHooks);
    },
    setStudioManualHeight(node, target) {
      classicOwners.setStudioManualHeight(node, target, ownerHooks);
    },
    updateHighlight: ownerHooks.updateHighlight,
  };
  enhanceResizableInput({ type }, widget, hooks);
  flushFrame();
  resetFrames();
  return { input, overlay, type, widget };
}

for (const fixture of [
  classicFixture("EasyUseAnimaPromptStudio", "prompt", 150),
  classicFixture("EasyUseAnimaPromptStudioExtend", "general_tags_4", 120),
  classicFixture("EasyUseAnimaPromptStudioNode2", "prompt", 150, false, true),
]) {
  fixture.input.value = Array.from(
    { length: 120 },
    (_, index) => `태그_${index}, english_tag_${index}, (weight_${index}:1.2), [[artist_${index}]]`,
  ).join("\n");
  fixture.input.emit("input");
  assertEqual(
    fixture.widget.__easyuseAnimaHeight,
    fixture.type.endsWith("Extend") ? 120 : 150,
    `${fixture.type} immediate stale height`,
  );
  fixture.input.scrollHeight = 1440;
  flushFrame();
  fixture.input.scrollHeight = 1512;
  flushFrame();
  assertEqual(fixture.widget.__easyuseAnimaHeight, 1512, `${fixture.type} persisted height`);
  assertEqual(fixture.overlay.style.height, fixture.input.style.height, `${fixture.type} overlay parity`);
  assertEqual(fixture.input.style.overflowY, "hidden", `${fixture.type} overflow invariant`);
}

const manualClassic = classicFixture(
  "EasyUseAnimaPromptStudio",
  "prompt",
  480,
  true,
);
manualClassic.input.emit("input");
manualClassic.input.scrollHeight = 840;
flushFrame();
manualClassic.input.scrollHeight = 888;
flushFrame();
assertEqual(manualClassic.widget.__easyuseAnimaHeight, 888, "Classic manual height grows");
assertEqual(manualClassic.widget.__easyuseAnimaManualHeight, true, "Classic manual ownership persists");

const advancedControlsUrl = inlineModule("export function setAdvancedControlValue() {}");
const debounceUrl = inlineModule("export function debounce() { return () => {}; }");
const highlightUrl = inlineModule("export function requestOverlaySync() {}");
const textUrl = inlineModule("export function psText(key) { return key; }");
const advancedFieldsUiUrl = dataModule(
  "../web/js/prompt_studio/advanced_fields_ui.js",
  {
    "./advanced_controls.js": advancedControlsUrl,
    "./constants.js": fileUrl("../web/js/prompt_studio/constants.js"),
    "./fields.js": fileUrl("../web/js/prompt_studio/fields.js"),
    "./highlight.js": highlightUrl,
    "./layout.js": fileUrl("../web/js/prompt_studio/layout.js"),
    "./schema.js": fileUrl("../web/js/prompt_studio/schema.js"),
    "./serialization.js": fileUrl("../web/js/prompt_studio/serialization.js"),
    "./state.js": fileUrl("../web/js/prompt_studio/state.js"),
    "./textarea.js": fileUrl("../web/js/prompt_studio/textarea.js"),
    "./textarea_stabilization.js": fileUrl("../web/js/prompt_studio/textarea_stabilization.js"),
    "./text.js": textUrl,
    "./utils.js": debounceUrl,
    "./widgets.js": fileUrl("../web/js/prompt_studio/widgets.js"),
  },
);

globalThis.document = createFakeDocument();
const createElement = globalThis.document.createElement.bind(globalThis.document);
globalThis.document.createElement = (tagName) => {
  const element = createElement(tagName);
  element.dataset = {};
  return element;
};
globalThis.HTMLElement = Object;
globalThis.HTMLTextAreaElement = Object;
globalThis.HTMLInputElement = Object;
globalThis.getComputedStyle = () => ({
  borderBottomWidth: "0",
  borderTopWidth: "0",
  fontSize: "12",
  lineHeight: "16",
  paddingBottom: "0",
  paddingTop: "0",
});

const {
  createAdvancedFieldElement,
} = await import(advancedFieldsUiUrl);

function advancedFixture(type, manual = false) {
  resetFrames();
  const field = {
    enabled: true,
    height: manual ? 480 : 120,
    heightMode: manual ? "manual" : "auto",
    id: "positive_general_1",
    label: "General Tags",
    pane: "positive",
    text: "",
    type: "general",
  };
  const node = {
    __easyuseAnimaAdvancedFields: [field],
    inputs: [],
    type,
    widgets: [],
  };
  let overlayHeight = "";
  const hooks = {
    advancedFieldLabel: (target) => target.label,
    applyAdvancedNaiaGeneralAutoToggle() {},
    parseAdvancedFields: () => [field],
    registerAdvancedAutocompleteInput() {},
    scheduleAdvancedFieldHighlight() {},
    scheduleAdvancedLayout() {},
    syncAdvancedFieldInputs() {},
    updateAdvancedFieldHighlight(_node, _field, textarea) {
      overlayHeight = textarea.style.height;
    },
    writeAdvancedFields() {},
  };
  const block = createAdvancedFieldElement(node, field, hooks);
  const textarea = block.querySelector("textarea");
  let scrollHeight = field.height;
  Object.defineProperties(textarea, {
    clientHeight: {
      configurable: true,
      get() {
        return heightValue(this.style);
      },
    },
    offsetHeight: {
      configurable: true,
      get() {
        return this.clientHeight;
      },
    },
    scrollHeight: {
      configurable: true,
      get() {
        return scrollHeight;
      },
      set(value) {
        scrollHeight = Number(value);
      },
    },
  });
  textarea.isConnected = true;
  flushFrame();
  resetFrames();
  return {
    field,
    get overlayHeight() {
      return overlayHeight;
    },
    textarea,
    type,
  };
}

for (const fixture of [
  advancedFixture("EasyUseAnimaPromptStudioAdvanced"),
  advancedFixture("EasyUseAnimaPromptStudioAdvancedV2"),
]) {
  fixture.textarea.value = Array.from(
    { length: 120 },
    (_, index) => `태그_${index}, english_tag_${index}, (weight_${index}:1.2), [[artist_${index}]]`,
  ).join("\n");
  fixture.textarea.emit("input");
  assertEqual(fixture.field.height, 120, `${fixture.type} immediate stale height`);
  fixture.textarea.scrollHeight = 1560;
  flushFrame();
  fixture.textarea.scrollHeight = 1632;
  flushFrame();
  assertEqual(fixture.field.height, 1632, `${fixture.type} persisted height`);
  assertEqual(fixture.overlayHeight, fixture.textarea.style.height, `${fixture.type} overlay parity`);
  assertEqual(fixture.textarea.style.overflowY, "hidden", `${fixture.type} overflow invariant`);
  assertEqual(fixture.field.text, fixture.textarea.value, `${fixture.type} save/reload value source`);
}

const manualAdvanced = advancedFixture(
  "EasyUseAnimaPromptStudioAdvancedV2",
  true,
);
manualAdvanced.textarea.emit("input");
manualAdvanced.textarea.scrollHeight = 912;
flushFrame();
manualAdvanced.textarea.scrollHeight = 960;
flushFrame();
assertEqual(manualAdvanced.field.height, 960, "Advanced manual height grows");
assertEqual(manualAdvanced.field.heightMode, "manual", "Advanced manual ownership persists");

console.log("Prompt Studio paste autosize smoke passed.");
