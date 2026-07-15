import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

function dataModule(relativePath) {
  const source = readFileSync(new URL(relativePath, import.meta.url), "utf8");
  return `data:text/javascript;base64,${Buffer.from(source).toString("base64")}`;
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
    this.checked = false;
    this.disabled = false;
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

const previewDialogModule = await import(dataModule("../web/js/aio/preview_settings_dialog.js"));
assert.deepEqual(
  Object.keys(previewDialogModule),
  ["aioCreatePreviewSettingsDialog"],
  "Preview Settings dialog must expose only its factory contract",
);

const defaultGenerationSettings = {
  schema_version: 4,
  sampler: { seed: 0, default_sampler_field: "preserved" },
  preview: {
    intermediate_images: true,
    compare_previous: false,
    image_feed: true,
    feed_count: 12,
  },
  upscale: { enabled: false, default_upscale_field: "preserved" },
  postprocess: { enabled: false, default_postprocess_field: "preserved" },
};

let dependencyCalls = 0;
let currentDialog = null;
const dialogs = [];
const findCalls = [];
const settingsCalls = [];
const settingsSnapshots = [];
const mergeCalls = [];
const clampCalls = [];
const defaultIndexCalls = [];
const visibleCalls = [];
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

function defaultPreviewIndex(images) {
  dependencyCalls += 1;
  currentDialog.trace.push("default-index");
  defaultIndexCalls.push(images);
  return images.length ? images.length - 1 : -1;
}

function applyVisibleSettings(node, settings) {
  dependencyCalls += 1;
  currentDialog.trace.push("visible");
  visibleCalls.push({ node, settings: clone(settings) });
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

const openPreviewSettings = previewDialogModule.aioCreatePreviewSettingsDialog({
  document: fakeDocument,
  createDialog,
  field,
  checkbox,
  numberInput,
  staticText,
  text,
  defaultGenerationSettings,
  generatorSettingsWidget: "generation_settings",
  findWidget,
  generatorSettings,
  mergeDefaults,
  clampNumber,
  defaultPreviewIndex,
  applyVisibleSettings,
  writeSettings,
  renderGeneratorPanel,
});

assert.equal(typeof openPreviewSettings, "function");
assert.equal(openPreviewSettings.name, "openPreviewSettings");
assert.equal(dependencyCalls, 0, "Factory creation must have no side effects");

function open(node) {
  currentDialog = null;
  openPreviewSettings(node);
  return dialogs[dialogs.length - 1];
}

function cancel(dialog) {
  dialog.actions.children[0].dispatch("click");
}

function apply(dialog) {
  dialog.actions.children[1].dispatch("click");
}

const feedImages = ["feed-1", "feed-2", "feed-3", "feed-4", "feed-5"];
const currentRunImages = ["current-1", "current-2"];
const generatorNode = {
  widgets: [{
    name: "generation_settings",
    value: JSON.stringify({
      schema_version: 7,
      sampler: { seed: 42, future_sampler_field: "preserved" },
      preview: {
        intermediate_images: false,
        compare_previous: true,
        image_feed: false,
        feed_count: 4,
        future_preview_field: "removed-on-apply",
      },
      upscale: { enabled: true, future_upscale_field: "preserved" },
      postprocess: { enabled: true, future_postprocess_field: "preserved" },
      future_root: { keep: true },
    }),
  }],
  __easyuseAnimaGeneratorPreviewFeedImages: [...feedImages],
  __easyuseAnimaGeneratorCurrentRunImages: currentRunImages,
  __easyuseAnimaGeneratorPreviewImages: ["old-preview"],
  __easyuseAnimaSelectedPreviewIndex: 99,
};

const defaultsBeforeInteractions = clone(defaultGenerationSettings);
const nodeBeforeCancel = clone(generatorNode);
const serializedBeforeCancel = generatorNode.widgets[0].value;
const feedImagesBeforeCancel = generatorNode.__easyuseAnimaGeneratorPreviewFeedImages;
const currentRunImagesBeforeCancel = generatorNode.__easyuseAnimaGeneratorCurrentRunImages;
const previewImagesBeforeCancel = generatorNode.__easyuseAnimaGeneratorPreviewImages;
let dialog = open(generatorNode);
const firstSettingsSnapshot = clone(settingsSnapshots[0]);
assert.equal(findCalls[0].node, generatorNode);
assert.equal(findCalls[0].name, "generation_settings");
assert.equal(settingsCalls.length, 1);
assert.equal(dialog.title, "Preview Options");
assert.equal(dialog.subtitle, "text:text.previewOptionsSubtitle");
assert.equal(dialog.body.children[0].children[0].textContent, "static:Node Preview");
assert.deepEqual([...dialog.controls.keys()], [
  "Intermediate images",
  "Compare previous",
  "Image feed",
  "Feed count",
]);
assert.equal(dialog.controls.get("Intermediate images").checked, false);
assert.equal(dialog.controls.get("Compare previous").checked, true);
assert.equal(dialog.controls.get("Image feed").checked, false);
assert.equal(dialog.controls.get("Feed count").value, "4");
assert.equal(dialog.controls.get("Feed count").step, "1");
assert.equal(dialog.controls.get("Feed count").min, "1");
assert.equal(dialog.controls.get("Feed count").max, "100");
assert.equal(dialog.controls.get("Feed count").disabled, true);
assert.equal(dialog.tooltips.get("Intermediate images"), "tip.previewIntermediate");
assert.equal(dialog.tooltips.get("Compare previous"), "tip.previewComparePrevious");
assert.equal(dialog.tooltips.get("Image feed"), "tip.previewImageFeed");
assert.equal(dialog.tooltips.get("Feed count"), "tip.previewFeedCount");
assert.equal(dialog.actions.children[0].textContent, "text:button.cancel");
assert.equal(dialog.actions.children[1].textContent, "text:button.apply");
assert.equal(dialog.actions.children[1].className, "primary");

dialog.controls.get("Image feed").checked = true;
dialog.controls.get("Image feed").dispatch("change");
assert.equal(dialog.controls.get("Feed count").disabled, false);
dialog.controls.get("Image feed").checked = false;
dialog.controls.get("Image feed").dispatch("change");
assert.equal(dialog.controls.get("Feed count").disabled, true);
const mergeCountBeforeCancel = mergeCalls.length;
cancel(dialog);
assert.deepEqual(dialog.trace, ["remove"]);
assert.equal(mergeCalls.length, mergeCountBeforeCancel);
assert.equal(clampCalls.length, 0);
assert.equal(defaultIndexCalls.length, 0);
assert.equal(visibleCalls.length, 0);
assert.equal(writeAttempts.length, 0);
assert.equal(renderCalls.length, 0);
assert.equal(generatorNode.widgets[0].value, serializedBeforeCancel);
assert.deepEqual(generatorNode, nodeBeforeCancel);
assert.equal(generatorNode.__easyuseAnimaGeneratorPreviewFeedImages, feedImagesBeforeCancel);
assert.equal(generatorNode.__easyuseAnimaGeneratorCurrentRunImages, currentRunImagesBeforeCancel);
assert.equal(generatorNode.__easyuseAnimaGeneratorPreviewImages, previewImagesBeforeCancel);
assert.deepEqual(settingsSnapshots[0], firstSettingsSnapshot);

dialog = open(generatorNode);
const appliedSettingsSnapshot = clone(settingsSnapshots[1]);
dialog.controls.get("Intermediate images").checked = true;
dialog.controls.get("Compare previous").checked = false;
dialog.controls.get("Image feed").checked = true;
dialog.controls.get("Image feed").dispatch("change");
dialog.controls.get("Feed count").value = "2.9";
apply(dialog);
assert.deepEqual(dialog.trace, [
  "merge",
  "clamp",
  "default-index",
  "visible",
  "write",
  "render",
  "remove",
]);
assert.deepEqual(clampCalls[0], { value: "2.9", fallback: 4, min: 1, max: 100 });
assert.deepEqual(generatorNode.__easyuseAnimaGeneratorPreviewFeedImages, ["feed-4", "feed-5"]);
assert.equal(
  generatorNode.__easyuseAnimaGeneratorPreviewImages,
  generatorNode.__easyuseAnimaGeneratorPreviewFeedImages,
);
assert.equal(defaultIndexCalls[0], generatorNode.__easyuseAnimaGeneratorPreviewImages);
assert.equal(generatorNode.__easyuseAnimaSelectedPreviewIndex, 1);
assert.equal(visibleCalls.length, 1);
assert.equal(writeAttempts.length, 1);
assert.equal(writes.length, 1);
assert.equal(writeAttempts[0].widget, generatorNode.widgets[0]);
assert.equal(renderCalls.length, 1);
assert.equal(renderCalls[0], generatorNode);
const firstWritten = writes[0].settings;
assert.deepEqual(firstWritten.preview, {
  intermediate_images: true,
  compare_previous: false,
  image_feed: true,
  feed_count: 2,
});
assert.equal(Object.hasOwn(firstWritten.preview, "future_preview_field"), false);
assert.equal(firstWritten.future_root.keep, true);
assert.equal(firstWritten.sampler.future_sampler_field, "preserved");
assert.equal(firstWritten.sampler.default_sampler_field, "preserved");
assert.equal(firstWritten.upscale.future_upscale_field, "preserved");
assert.equal(firstWritten.postprocess.future_postprocess_field, "preserved");
assert.deepEqual(visibleCalls[0].settings, firstWritten);
assert.deepEqual(JSON.parse(generatorNode.widgets[0].value), firstWritten);
assert.deepEqual(defaultGenerationSettings, defaultsBeforeInteractions);
assert.deepEqual(settingsSnapshots[1], appliedSettingsSnapshot);

dialog = open(generatorNode);
dialog.controls.get("Image feed").checked = false;
dialog.controls.get("Image feed").dispatch("change");
dialog.controls.get("Feed count").value = "1.9";
apply(dialog);
assert.equal(dialog.controls.get("Feed count").disabled, true);
assert.deepEqual(clampCalls[1], { value: "1.9", fallback: 2, min: 1, max: 100 });
assert.deepEqual(generatorNode.__easyuseAnimaGeneratorPreviewFeedImages, ["feed-5"]);
assert.equal(generatorNode.__easyuseAnimaGeneratorPreviewImages, currentRunImages);
assert.equal(defaultIndexCalls[1], currentRunImages);
assert.equal(generatorNode.__easyuseAnimaSelectedPreviewIndex, 1);
assert.equal(writes[1].settings.preview.image_feed, false);
assert.equal(writes[1].settings.preview.feed_count, 1);

const missingWidgetNode = {
  widgets: [],
  __easyuseAnimaGeneratorPreviewFeedImages: ["only-feed"],
  __easyuseAnimaGeneratorCurrentRunImages: ["only-current"],
  unrelated: { keep: true },
};
const missingUnrelatedBefore = clone(missingWidgetNode.unrelated);
dialog = open(missingWidgetNode);
dialog.controls.get("Feed count").value = "invalid";
apply(dialog);
assert.deepEqual(dialog.trace, [
  "merge",
  "clamp",
  "default-index",
  "visible",
  "write-noop",
  "render",
  "remove",
]);
assert.equal(writeAttempts[2].widget, undefined);
assert.equal(writes.length, 2);
assert.deepEqual(clampCalls[2], { value: "invalid", fallback: 12, min: 1, max: 100 });
assert.equal(writeAttempts[2].settings.preview.feed_count, 12);
assert.equal(missingWidgetNode.__easyuseAnimaGeneratorPreviewImages.length, 1);
assert.equal(missingWidgetNode.__easyuseAnimaSelectedPreviewIndex, 0);
assert.deepEqual(missingWidgetNode.unrelated, missingUnrelatedBefore);

console.log("AiO Preview Settings dialog smoke passed.");
