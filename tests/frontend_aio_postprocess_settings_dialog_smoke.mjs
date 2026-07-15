import { readFileSync } from "node:fs";

function dataModule(relativePath) {
  const source = readFileSync(new URL(relativePath, import.meta.url), "utf8");
  return `data:text/javascript;base64,${Buffer.from(source).toString("base64")}`;
}

function assert(condition, message) {
  if (!condition) {
    throw new Error(message);
  }
}

function assertJsonEqual(actual, expected, message) {
  assert(JSON.stringify(actual) === JSON.stringify(expected), message);
}

function clone(value) {
  return value == null ? value : JSON.parse(JSON.stringify(value));
}

function merge(defaults, current) {
  if (Array.isArray(current)) {
    return clone(current);
  }
  if (!current || typeof current !== "object") {
    return current === undefined ? clone(defaults) : current;
  }
  const output = defaults && typeof defaults === "object" && !Array.isArray(defaults)
    ? clone(defaults)
    : {};
  for (const [key, value] of Object.entries(current)) {
    output[key] = merge(output[key], value);
  }
  return output;
}

class FakeClassList {
  constructor() {
    this.values = new Set();
  }

  add(...names) {
    for (const name of names) {
      this.values.add(name);
    }
  }

  contains(name) {
    return this.values.has(name);
  }
}

class FakeElement {
  constructor(tagName) {
    this.tagName = String(tagName).toUpperCase();
    this.className = "";
    this.classList = new FakeClassList();
    this.textContent = "";
    this.value = "";
    this.checked = false;
    this.children = [];
    this.parentElement = null;
    this.style = {};
    this.listeners = new Map();
  }

  append(...children) {
    for (const child of children) {
      if (child && typeof child === "object") {
        child.parentElement = this;
      }
      this.children.push(child);
    }
  }

  addEventListener(type, listener) {
    const listeners = this.listeners.get(type) || [];
    listeners.push(listener);
    this.listeners.set(type, listeners);
  }

  dispatch(type) {
    for (const listener of this.listeners.get(type) || []) {
      listener({ target: this });
    }
  }
}

const postprocessDialogModule = await import(dataModule("../web/js/aio/postprocess_settings_dialog.js"));
assertJsonEqual(
  Object.keys(postprocessDialogModule),
  ["aioCreatePostprocessSettingsDialog"],
  "Postprocess Settings dialog must expose only its factory contract",
);

const defaultGenerationSettings = {
  schema_version: 4,
  sampler: { seed: 0, default_sampler_field: "preserved" },
  upscale: { enabled: false, default_upscale_field: "preserved" },
  postprocess: {
    enabled: false,
    default_postprocess_field: "preserved",
    fit: {
      mode: "max_long_edge",
      max_long_edge: 2048,
      max_megapixels: 4,
      method: "bicubic",
      default_fit_field: "preserved",
    },
  },
};

let dependencyCalls = 0;
let currentDialog = null;
const dialogs = [];
const findCalls = [];
const settingsCalls = [];
const settingsSnapshots = [];
const mergeCalls = [];
const clampCalls = [];
const writeAttempts = [];
const writes = [];
const renderCalls = [];

const fakeDocument = {
  createElement(tagName) {
    dependencyCalls += 1;
    return new FakeElement(tagName);
  },
};

function createDialog(title, subtitle) {
  dependencyCalls += 1;
  const dialog = {
    title,
    subtitle,
    body: new FakeElement("div"),
    actions: new FakeElement("div"),
    controls: new Map(),
    tooltips: new Map(),
    trace: [],
  };
  dialog.backdrop = new FakeElement("div");
  dialog.backdrop.remove = () => dialog.trace.push("remove");
  dialogs.push(dialog);
  currentDialog = dialog;
  return dialog;
}

function field(section, label, control, tooltipKey = "") {
  dependencyCalls += 1;
  const wrapper = new FakeElement("div");
  wrapper.append(control);
  section.append(wrapper);
  currentDialog.controls.set(label, control);
  currentDialog.tooltips.set(label, tooltipKey);
  return control;
}

function checkbox(value) {
  dependencyCalls += 1;
  const control = new FakeElement("input");
  control.checked = !!value;
  return control;
}

function selectInput(options, value) {
  dependencyCalls += 1;
  const control = new FakeElement("select");
  control.options = clone(options);
  control.value = String(value ?? "");
  return control;
}

function numberInput(value, step = "1") {
  dependencyCalls += 1;
  const control = new FakeElement("input");
  control.value = String(value ?? "");
  control.step = step;
  return control;
}

function staticText(value) {
  dependencyCalls += 1;
  return `static:${value}`;
}

function text(key) {
  dependencyCalls += 1;
  return `text:${key}`;
}

function findWidget(node, name) {
  dependencyCalls += 1;
  findCalls.push({ node, name });
  return node.widgets?.find((widget) => widget.name === name);
}

function generatorSettings(node) {
  dependencyCalls += 1;
  settingsCalls.push(node);
  const widget = node.widgets?.find((candidate) => candidate.name === "generation_settings");
  let current = widget?.value || {};
  if (typeof current === "string") {
    try {
      current = JSON.parse(current);
    } catch (_error) {
      current = {};
    }
  }
  const snapshot = merge(defaultGenerationSettings, current);
  settingsSnapshots.push(snapshot);
  return snapshot;
}

function mergeDefaults(defaults, current) {
  dependencyCalls += 1;
  if (currentDialog) {
    currentDialog.trace.push("merge");
  }
  mergeCalls.push({ defaults, current });
  return merge(defaults, current);
}

function clampNumber(value, fallback, min, max) {
  dependencyCalls += 1;
  currentDialog.trace.push("clamp");
  clampCalls.push({ value, fallback, min, max });
  const parsed = Number(value);
  const next = Number.isFinite(parsed) ? parsed : fallback;
  return Math.max(min, Math.min(max, next));
}

function writeSettings(node, widget, settings) {
  dependencyCalls += 1;
  currentDialog.trace.push(widget ? "write" : "write-noop");
  const attempt = { node, widget, settings: clone(settings) };
  writeAttempts.push(attempt);
  if (!widget) {
    return;
  }
  widget.value = JSON.stringify(settings);
  writes.push(attempt);
}

function renderGeneratorPanel(node) {
  dependencyCalls += 1;
  currentDialog.trace.push("render");
  renderCalls.push(node);
}

const openPostprocessSettings = postprocessDialogModule.aioCreatePostprocessSettingsDialog({
  document: fakeDocument,
  createDialog,
  field,
  checkbox,
  selectInput,
  numberInput,
  staticText,
  text,
  defaultGenerationSettings,
  generatorSettingsWidget: "generation_settings",
  findWidget,
  generatorSettings,
  mergeDefaults,
  clampNumber,
  writeSettings,
  renderGeneratorPanel,
});

assert(typeof openPostprocessSettings === "function", "Factory must return the Postprocess Settings opener");
assert(openPostprocessSettings.name === "openPostprocessSettings", "Returned opener must retain its controller name");
assert(
  dependencyCalls === 0 && dialogs.length === 0 && writeAttempts.length === 0 && renderCalls.length === 0,
  "Factory creation must not touch DOM, settings, persistence, or lifecycle adapters",
);

function open(node) {
  currentDialog = null;
  openPostprocessSettings(node);
  return dialogs[dialogs.length - 1];
}

function cancel(dialog) {
  dialog.actions.children[0].dispatch("click");
}

function apply(dialog) {
  dialog.actions.children[1].dispatch("click");
}

function display(dialog, label) {
  return dialog.controls.get(label).parentElement.style.display;
}

const generatorNode = {
  widgets: [{
    name: "generation_settings",
    value: JSON.stringify({
      schema_version: 7,
      sampler: { seed: 42, future_sampler_field: "preserved" },
      upscale: {
        enabled: true,
        future_upscale_field: "preserved",
        fit: { enabled: true, legacy_field: "removed" },
      },
      postprocess: {
        enabled: true,
        future_postprocess_field: "preserved",
        fit: {
          mode: "max_long_edge",
          max_long_edge: 3072,
          max_megapixels: 9.5,
          method: "lanczos",
          future_fit_field: "preserved",
        },
      },
      future_root: { keep: true },
    }),
  }],
};

const defaultsBeforeInteractions = clone(defaultGenerationSettings);
const serializedBeforeCancel = generatorNode.widgets[0].value;
let dialog = open(generatorNode);
const firstSettingsSnapshot = clone(settingsSnapshots[0]);
assert(
  findCalls[0].node === generatorNode && findCalls[0].name === "generation_settings",
  "Opener must resolve the injected hidden generation settings widget once",
);
assert(settingsCalls.length === 1 && settingsCalls[0] === generatorNode, "Opener must read generator settings once");
assert(dialog.title === "Postprocess Settings", "Dialog title must remain stable");
assert(
  dialog.subtitle === "Final size fit runs after Detailer and Upscale, before Save. Cap by long edge or megapixels.",
  "Dialog subtitle must remain stable",
);
assert(dialog.body.classList.contains("easyuse-anima-aio-one-column"), "Dialog must retain one-column layout");
assert(dialog.body.children[0].children[0].textContent === "static:Final Size Fit", "Section heading must use static text");
assert(dialog.actions.children[0].textContent === "text:button.cancel", "Cancel label must use text adapter");
assert(dialog.actions.children[1].textContent === "text:button.apply", "Apply label must use text adapter");
assert(dialog.actions.children[1].className === "primary", "Apply button must remain primary");
assertJsonEqual(
  dialog.controls.get("Fit by").options,
  [
    { value: "max_long_edge", label: "Max long edge" },
    { value: "megapixels", label: "Megapixels" },
  ],
  "Fit mode options must remain stable",
);
assertJsonEqual(
  dialog.controls.get("Fit method").options,
  ["bicubic", "lanczos", "area", "bilinear", "nearest-exact"],
  "Fit method options must remain stable",
);
assert(dialog.controls.get("Enable postprocess").checked, "Saved enabled state must hydrate");
assert(dialog.controls.get("Fit by").value === "max_long_edge", "Saved fit mode must hydrate");
assert(dialog.controls.get("Max long edge").value === "3072", "Saved long edge must hydrate");
assert(dialog.controls.get("Max megapixels").value === "9.5", "Saved megapixels must hydrate");
assert(dialog.controls.get("Fit method").value === "lanczos", "Saved fit method must hydrate");
assert(display(dialog, "Fit by") === "" && display(dialog, "Fit method") === "", "Enabled fit controls must show");
assert(display(dialog, "Max long edge") === "", "Long-edge row must show in long-edge mode");
assert(display(dialog, "Max megapixels") === "none", "Megapixels row must hide in long-edge mode");
assert(dialog.tooltips.get("Enable postprocess") === "tip.postprocessEnabled", "Enable tooltip key must remain stable");
for (const label of ["Fit by", "Max long edge", "Max megapixels", "Fit method"]) {
  assert(dialog.tooltips.get(label) === "tip.finalFit", `${label} tooltip key must remain stable`);
}

dialog.controls.get("Fit by").value = "megapixels";
dialog.controls.get("Fit by").dispatch("change");
assert(display(dialog, "Max long edge") === "none", "Long-edge row must hide in megapixels mode");
assert(display(dialog, "Max megapixels") === "", "Megapixels row must show in megapixels mode");
dialog.controls.get("Enable postprocess").checked = false;
dialog.controls.get("Enable postprocess").dispatch("change");
for (const label of ["Fit by", "Max long edge", "Max megapixels", "Fit method"]) {
  assert(display(dialog, label) === "none", `${label} must hide while postprocess is disabled`);
}
const mergeCountBeforeCancel = mergeCalls.length;
cancel(dialog);
assertJsonEqual(dialog.trace, ["remove"], "Cancel must only close the dialog");
assert(mergeCalls.length === mergeCountBeforeCancel, "Cancel must not merge an applied settings snapshot");
assert(writeAttempts.length === 0 && renderCalls.length === 0, "Cancel must not write or render");
assert(generatorNode.widgets[0].value === serializedBeforeCancel, "Cancel must not mutate serialized settings");
assertJsonEqual(settingsSnapshots[0], firstSettingsSnapshot, "Cancel must not mutate the open-time settings snapshot");

dialog = open(generatorNode);
const appliedSettingsSnapshot = clone(settingsSnapshots[1]);
dialog.controls.get("Enable postprocess").checked = true;
dialog.controls.get("Fit by").value = "";
dialog.controls.get("Max long edge").value = "20000.8";
dialog.controls.get("Max megapixels").value = "not-a-number";
dialog.controls.get("Fit method").value = "";
apply(dialog);
assertJsonEqual(
  dialog.trace,
  ["merge", "clamp", "clamp", "write", "render", "remove"],
  "Apply must merge, clamp, write, render, then close",
);
assert(writeAttempts.length === 1 && writes.length === 1, "Apply must persist exactly one settings write");
assert(renderCalls.length === 1 && renderCalls[0] === generatorNode, "Apply must refresh the generator panel once");
assert(writeAttempts[0].widget === generatorNode.widgets[0], "Apply must target the hidden generation settings widget");
const written = writes[0].settings;
assertJsonEqual(JSON.parse(generatorNode.widgets[0].value), written, "Write adapter must serialize applied settings");
assert(
  written.postprocess.enabled === true
    && written.postprocess.fit.mode === "max_long_edge"
    && written.postprocess.fit.max_long_edge === 16384
    && written.postprocess.fit.max_megapixels === 4
    && written.postprocess.fit.method === "bicubic",
  "Apply must preserve fallbacks, clamps, and long-edge truncation",
);
assertJsonEqual(
  clampCalls.slice(0, 2),
  [
    { value: "20000.8", fallback: 2048, min: 64, max: 16384 },
    { value: "not-a-number", fallback: 4, min: 0.1, max: 256 },
  ],
  "Apply must retain exact numeric clamp contracts",
);
assert(
  written.future_root.keep === true
    && written.sampler.future_sampler_field === "preserved"
    && written.upscale.future_upscale_field === "preserved"
    && written.postprocess.future_postprocess_field === "preserved"
    && written.postprocess.fit.future_fit_field === "preserved"
    && written.postprocess.default_postprocess_field === "preserved"
    && written.postprocess.fit.default_fit_field === "preserved",
  "Apply must preserve root, stage, postprocess, fit, and default-compatible unknown fields",
);
assert(!Object.prototype.hasOwnProperty.call(written.upscale, "fit"), "Apply must remove legacy upscale.fit");
assertJsonEqual(defaultGenerationSettings, defaultsBeforeInteractions, "Apply must not mutate injected defaults");
assertJsonEqual(settingsSnapshots[1], appliedSettingsSnapshot, "Apply must not mutate the open-time settings snapshot");

const missingWidgetNode = { widgets: [], untouched: true };
const missingWidgetBeforeApply = clone(missingWidgetNode);
dialog = open(missingWidgetNode);
assert(!dialog.controls.get("Enable postprocess").checked, "Missing widgets must hydrate default enabled state");
for (const label of ["Fit by", "Max long edge", "Max megapixels", "Fit method"]) {
  assert(display(dialog, label) === "none", `${label} must start hidden for default disabled postprocess`);
}
dialog.controls.get("Enable postprocess").checked = true;
dialog.controls.get("Fit by").value = "megapixels";
dialog.controls.get("Max long edge").value = "";
dialog.controls.get("Max megapixels").value = "";
dialog.controls.get("Fit method").value = "area";
apply(dialog);
assertJsonEqual(
  dialog.trace,
  ["merge", "clamp", "clamp", "write-noop", "render", "remove"],
  "Missing-widget Apply must still merge, clamp, attempt write, render, then close",
);
assert(writeAttempts.length === 2, "Missing-widget Apply must invoke the write adapter exactly once");
assert(writeAttempts[1].widget === undefined, "Missing-widget Apply must pass the unresolved widget to the adapter");
assert(writes.length === 1, "Missing-widget Apply must not report a persisted write");
assert(renderCalls.length === 2 && renderCalls[1] === missingWidgetNode, "Missing-widget Apply must still refresh panel");
assert(
  writeAttempts[1].settings.postprocess.fit.mode === "megapixels"
    && writeAttempts[1].settings.postprocess.fit.max_long_edge === 64
    && writeAttempts[1].settings.postprocess.fit.max_megapixels === 0.1
    && writeAttempts[1].settings.postprocess.fit.method === "area",
  "Blank numeric controls must retain the existing minimum-clamp behavior",
);
assertJsonEqual(missingWidgetNode, missingWidgetBeforeApply, "Missing-widget Apply must not mutate the node directly");

console.log("AiO Postprocess Settings dialog smoke passed.");
