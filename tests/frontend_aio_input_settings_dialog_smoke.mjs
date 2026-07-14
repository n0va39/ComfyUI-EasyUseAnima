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

class FakeElement {
  constructor(tagName) {
    this.tagName = String(tagName).toUpperCase();
    this.className = "";
    this.textContent = "";
    this.value = "";
    this.children = [];
    this.parentElement = null;
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

const inputSettingsDialogModule = await import(dataModule("../web/js/aio/input_settings_dialog.js"));
assertJsonEqual(
  Object.keys(inputSettingsDialogModule),
  ["aioCreateInputSettingsDialog"],
  "Input Settings dialog must expose only its factory contract",
);

const defaultInputSettings = {
  resources: {
    loader_mode: "split",
    clip_loader: "single",
    unet_weight_dtype: "default",
    clip_device: "default",
    default_only: "preserved",
  },
};

let dependencyCalls = 0;
let currentDialog = null;
const dialogs = [];
const findCalls = [];
const parseCalls = [];
const parsedValues = [];
const mergeCalls = [];
const writeAttempts = [];
const writes = [];

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
    trace: [],
  };
  dialog.backdrop = new FakeElement("div");
  dialog.backdrop.remove = () => dialog.trace.push("remove");
  dialogs.push(dialog);
  currentDialog = dialog;
  return dialog;
}

function field(section, label, control) {
  dependencyCalls += 1;
  const wrapper = new FakeElement("div");
  wrapper.append(control);
  section.append(wrapper);
  currentDialog.controls.set(label, control);
  return control;
}

function selectInput(options, value) {
  dependencyCalls += 1;
  const control = new FakeElement("select");
  control.options = clone(options);
  control.value = String(value ?? "");
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

function parseSettings(widget, defaults) {
  dependencyCalls += 1;
  parseCalls.push({ widget, defaults });
  if (!widget) {
    const parsed = clone(defaults);
    parsedValues.push(parsed);
    return parsed;
  }
  let current = widget.value || {};
  if (typeof current === "string") {
    try {
      current = JSON.parse(current);
    } catch (_error) {
      current = {};
    }
  }
  const parsed = merge(defaults, current);
  parsedValues.push(parsed);
  return parsed;
}

function mergeDefaults(defaults, current) {
  dependencyCalls += 1;
  currentDialog.trace.push("merge");
  mergeCalls.push({ defaults, current });
  return merge(defaults, current);
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

const openInputSettings = inputSettingsDialogModule.aioCreateInputSettingsDialog({
  document: fakeDocument,
  createDialog,
  field,
  selectInput,
  staticText,
  text,
  defaultInputSettings,
  inputSettingsWidget: "input_settings",
  findWidget,
  parseSettings,
  mergeDefaults,
  writeSettings,
});

assert(typeof openInputSettings === "function", "Factory must return the Input Settings opener");
assert(openInputSettings.name === "openInputSettings", "Returned opener must retain its controller name");
assert(
  dependencyCalls === 0 && dialogs.length === 0 && writeAttempts.length === 0,
  "Factory creation must not touch DOM, settings, or lifecycle adapters",
);

function latestDialog() {
  return dialogs[dialogs.length - 1];
}

function cancel(dialog) {
  dialog.actions.children[0].dispatch("click");
}

function apply(dialog) {
  dialog.actions.children[1].dispatch("click");
}

const inputNode = {
  widgets: [{
    name: "input_settings",
    value: JSON.stringify({
      resources: {
        unet_weight_dtype: "fp8_e4m3fn",
        clip_device: "cpu",
        future_resource: "preserved",
      },
      schema_version: 7,
      metadata: { future_owner: "preserved" },
      future_root: { keep: true },
    }),
  }],
};
const defaultsBeforeInteractions = clone(defaultInputSettings);
const beforeCancel = clone(inputNode.widgets[0].value);
openInputSettings(inputNode);
let dialog = latestDialog();
assert(
  findCalls[0].node === inputNode && findCalls[0].name === "input_settings",
  "Opener must resolve the Input Settings widget by its injected name",
);
assert(
  parseCalls[0].widget === inputNode.widgets[0] && parseCalls[0].defaults === defaultInputSettings,
  "Opener must parse the resolved widget against the injected defaults",
);
assert(dialog.title === "Easy Use Anima Input Settings", "Dialog title must remain stable");
assert(
  dialog.subtitle === "Advanced resource options are saved internally with the workflow.",
  "Dialog subtitle must remain stable",
);
assertJsonEqual(
  dialog.controls.get("UNET weight dtype").options,
  ["default", "fp8_e4m3fn", "fp8_e4m3fn_fast", "fp8_e5m2"],
  "UNET dtype options must remain stable",
);
assertJsonEqual(
  dialog.controls.get("CLIP device").options,
  ["default", "cpu"],
  "CLIP device options must remain stable",
);
assert(
  dialog.controls.get("UNET weight dtype").value === "fp8_e4m3fn"
    && dialog.controls.get("CLIP device").value === "cpu",
  "Saved resource settings must hydrate their matching controls",
);
dialog.controls.get("UNET weight dtype").value = "fp8_e5m2";
dialog.controls.get("CLIP device").value = "default";
cancel(dialog);
assertJsonEqual(dialog.trace, ["remove"], "Cancel must only close the dialog");
assert(mergeCalls.length === 0, "Cancel must not merge an applied settings snapshot");
assert(writeAttempts.length === 0, "Cancel must not attempt a settings write");
assertJsonEqual(inputNode.widgets[0].value, beforeCancel, "Cancel must not mutate saved settings");

openInputSettings(inputNode);
dialog = latestDialog();
dialog.controls.get("UNET weight dtype").value = "fp8_e5m2";
dialog.controls.get("CLIP device").value = "";
apply(dialog);
assertJsonEqual(dialog.trace, ["merge", "write", "remove"], "Apply must merge, write, then close");
assert(writeAttempts.length === 1 && writes.length === 1, "Apply must persist exactly one settings write");
assert(writeAttempts[0].widget === inputNode.widgets[0], "Apply must target the hidden input settings widget");
const written = writes[0].settings;
assertJsonEqual(JSON.parse(inputNode.widgets[0].value), written, "Write adapter must serialize the applied settings");
assert(
  written.resources.loader_mode === "split"
    && written.resources.clip_loader === "single"
    && written.resources.unet_weight_dtype === "fp8_e5m2"
    && written.resources.clip_device === "default",
  "Apply must preserve forced loader values and selected resources",
);
assert(
  written.resources.default_only === "preserved"
    && written.resources.future_resource === "preserved"
    && written.schema_version === 7
    && written.metadata.future_owner === "preserved"
    && written.future_root.keep === true,
  "Apply must preserve schema metadata, defaults, and unknown future settings",
);
assertJsonEqual(defaultInputSettings, defaultsBeforeInteractions, "Apply must not mutate injected defaults");
assert(
  parsedValues[1].resources.unet_weight_dtype === "fp8_e4m3fn"
    && parsedValues[1].resources.clip_device === "cpu",
  "Apply must not mutate the parsed settings snapshot captured at open time",
);

const missingWidgetNode = { widgets: [], untouched: true };
const beforeMissingApply = clone(missingWidgetNode);
openInputSettings(missingWidgetNode);
dialog = latestDialog();
assert(
  dialog.controls.get("UNET weight dtype").value === "default"
    && dialog.controls.get("CLIP device").value === "default",
  "Missing widgets must hydrate controls from defaults",
);
dialog.controls.get("UNET weight dtype").value = "";
dialog.controls.get("CLIP device").value = "";
apply(dialog);
assertJsonEqual(
  dialog.trace,
  ["merge", "write-noop", "remove"],
  "Missing-widget Apply must merge, attempt the no-op write, then close",
);
assert(writeAttempts.length === 2, "Missing-widget Apply must invoke the write adapter exactly once");
assert(writeAttempts[1].widget === undefined, "Missing-widget Apply must pass the unresolved widget to the adapter");
assert(writes.length === 1, "Missing-widget Apply must not report a persisted write");
assert(
  writeAttempts[1].settings.resources.unet_weight_dtype === "default"
    && writeAttempts[1].settings.resources.clip_device === "default",
  "Empty selections must normalize to default resource values",
);
assertJsonEqual(missingWidgetNode, beforeMissingApply, "Missing-widget Apply must not mutate the node directly");

console.log("AiO Input Settings dialog smoke passed.");
