import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import {
  createFakeDocument,
  descendants,
} from "./frontend_support/fake_dom.mjs";

function dataModule(relativePath) {
  const source = readFileSync(new URL(relativePath, import.meta.url), "utf8");
  return "data:text/javascript;base64," + Buffer.from(source).toString("base64");
}

function clone(value) {
  return value == null ? value : JSON.parse(JSON.stringify(value));
}

function find(root, predicate) {
  return [root, ...descendants(root)].find(predicate) || null;
}

function findByClass(root, className) {
  return find(root, (element) => element.classList.contains(className));
}

function findByText(root, textContent) {
  return find(root, (element) => element.textContent === textContent);
}

const panelModule = await import(dataModule("../web/js/aio/generator_panel_runtime.js"));
const settingsModule = await import(dataModule("../web/js/aio/settings.js"));
assert.deepEqual(
  Object.keys(panelModule),
  ["aioCreateGeneratorPanelRuntime"],
  "Generator panel runtime must expose only its factory contract",
);

function createFixture() {
  let dependencyCalls = 0;
  const trace = [];
  const animationFrames = [];
  const actionCalls = [];
  const document = createFakeDocument();
  const windowListeners = new Map();
  const window = {
    addEventListener(type, listener) {
      dependencyCalls += 1;
      const listeners = windowListeners.get(type) || [];
      listeners.push(listener);
      windowListeners.set(type, listeners);
    },
    removeEventListener(type, listener) {
      dependencyCalls += 1;
      const listeners = windowListeners.get(type) || [];
      windowListeners.set(type, listeners.filter((candidate) => candidate !== listener));
    },
  };

  function numberInput(value, step = "1") {
    dependencyCalls += 1;
    const input = document.createElement("input");
    input.type = "number";
    input.step = step;
    input.value = String(value ?? "");
    return input;
  }

  function checkbox(value) {
    dependencyCalls += 1;
    const input = document.createElement("input");
    input.type = "checkbox";
    input.checked = !!value;
    return input;
  }

  function selectInput(options, value) {
    dependencyCalls += 1;
    const select = document.createElement("select");
    for (const optionSpec of options) {
      const option = document.createElement("option");
      option.value = typeof optionSpec === "object"
        ? String(optionSpec.value ?? "")
        : String(optionSpec ?? "");
      option.textContent = typeof optionSpec === "object"
        ? String(optionSpec.label ?? option.value)
        : option.value;
      option.disabled = !!(typeof optionSpec === "object" && optionSpec?.disabled);
      option.selected = option.value === String(value ?? "");
      select.append(option);
    }
    return select;
  }

  function createNodeField(label, control, className = "", tooltipKey = "") {
    dependencyCalls += 1;
    const field = document.createElement("label");
    field.className = ("easyuse-anima-aio-node-field " + className).trim();
    field.setAttribute("data-test-label", label);
    field.setAttribute("data-test-tooltip", tooltipKey);
    field.append(control);
    return field;
  }

  function text(key) {
    dependencyCalls += 1;
    return "text:" + key;
  }

  function format(key, values = {}) {
    dependencyCalls += 1;
    return "format:" + key + ":" + JSON.stringify(values);
  }

  function applyTooltip(element, key) {
    dependencyCalls += 1;
    if (key) {
      element.title = text(key);
    }
    return element;
  }

  const defaultSettings = clone(settingsModule.AIO_DEFAULT_GENERATION_SETTINGS);
  const settingsCore = {
    defaultGenerationSettings: defaultSettings,
    specialSeedRandom: settingsModule.AIO_GENERATOR_SPECIAL_SEED_RANDOM,
    fallbackSamplerNames: ["er_sde", "euler"],
    fallbackSchedulerNames: ["simple", "karras"],
    mergeDefaults: settingsModule.aioMergeDefaults,
    normalizeSeedControl: settingsModule.aioNormalizeSeedControl,
    normalizeSeedValue: settingsModule.aioNormalizeSeedValue,
    clampNumber(value, fallback, min, max) {
      const parsed = Number(value);
      return Math.max(min, Math.min(max, Number.isFinite(parsed) ? parsed : fallback));
    },
    normalizeUsduAutoTileRange(usdu) {
      return {
        ...clone(defaultSettings.upscale.usdu),
        ...clone(usdu || {}),
      };
    },
    setUsduAutoTileTarget(settings, value) {
      settings.upscale ||= {};
      settings.upscale.usdu ||= {};
      settings.upscale.usdu.auto_tile_target = Math.trunc(value);
    },
    normalizeDetailerOrder(order) {
      return Array.isArray(order) ? [...order] : [];
    },
    detailerTargetDefaults(targetName) {
      return clone(defaultSettings.detailer[targetName] || {
        enabled: false,
        inherit_sampler_settings: true,
        steps: 20,
        denoise: 0.3,
      });
    },
    detailerTargetTitle(targetName, target) {
      return String(target?.label || targetName);
    },
  };

  const nodeAdapter = {
    getSettings(node) {
      dependencyCalls += 1;
      trace.push("get-settings");
      return clone(node.settings);
    },
    applyVisibleSettings(node, settings) {
      dependencyCalls += 1;
      trace.push("apply-visible");
      node.visibleSettings = clone(settings);
    },
    writeSettings(node, settings, markDirty = true) {
      dependencyCalls += 1;
      trace.push("write:" + markDirty);
      node.settings = clone(settings);
    },
    syncSettingsFromVisible(node) {
      dependencyCalls += 1;
      trace.push("sync-visible");
      if (Object.hasOwn(node.widgetValues, "seed")) {
        node.settings.sampler.seed = node.widgetValues.seed;
      }
    },
    widgetValue(node, name, fallback) {
      dependencyCalls += 1;
      return Object.hasOwn(node.widgetValues, name) ? node.widgetValues[name] : fallback;
    },
    widgetOptions(_node, _name, fallback) {
      dependencyCalls += 1;
      return [...fallback];
    },
    setWidgetValueIfChanged(node, name, value) {
      dependencyCalls += 1;
      trace.push("set-widget:" + name + ":" + value);
      node.widgetValues[name] = value;
    },
    markDirty(node) {
      dependencyCalls += 1;
      trace.push("dirty");
      node.dirtyCount = (node.dirtyCount || 0) + 1;
    },
    ensureStyle() {
      dependencyCalls += 1;
      trace.push("ensure-style");
    },
    suppressDefaultPreview(_node, options) {
      dependencyCalls += 1;
      trace.push("suppress:" + JSON.stringify(options));
    },
    markNativePreviewHidden() {
      dependencyCalls += 1;
      trace.push("native-hidden");
    },
    imageUrl(image) {
      dependencyCalls += 1;
      return image?.filename ? "/view/" + image.filename : "";
    },
    randomSeed() {
      dependencyCalls += 1;
      trace.push("random-seed");
      return 123456;
    },
    forwardPanelWheel(event) {
      dependencyCalls += 1;
      trace.push("forward-wheel");
      event.preventDefault?.();
      return true;
    },
  };

  const profileAdapter = {
    syncValue(node) {
      dependencyCalls += 1;
      trace.push("sync-profile");
      return node.profileValue || "custom";
    },
    displayLabel(value) {
      dependencyCalls += 1;
      return String(value).startsWith("user:")
        ? String(value).slice(5)
        : "text:profile.custom";
    },
  };

  function selectedIndex(node, images) {
    dependencyCalls += 1;
    const requested = Number(node.__easyuseAnimaSelectedPreviewIndex);
    return Number.isInteger(requested) && requested >= 0 && requested < images.length
      ? requested
      : Math.max(0, images.length - 1);
  }

  const previewAdapter = {
    selectedIndex,
    mainImage(node, images) {
      dependencyCalls += 1;
      return images[selectedIndex(node, images)] || null;
    },
    imageLabel(image) {
      dependencyCalls += 1;
      return String(image?.label || image?.filename || "");
    },
    imageName(image) {
      dependencyCalls += 1;
      return String(image?.name || image?.filename || "-");
    },
    imageResolution(image) {
      dependencyCalls += 1;
      return image?.width && image?.height ? image.width + "x" + image.height : "-";
    },
    imageFileSize(image) {
      dependencyCalls += 1;
      return String(image?.fileSize || "-");
    },
  };

  const actions = {};
  for (const name of [
    "openProfileSettings",
    "openSaveSettings",
    "openSamplerSettings",
    "openAdvancedSettings",
    "openHighresSettings",
    "openDetailerSettings",
    "openUpscaleSettings",
    "openPostprocessSettings",
    "openPreviewSettings",
  ]) {
    actions[name] = (node) => {
      dependencyCalls += 1;
      actionCalls.push({ name, node });
    };
  }

  const runtime = panelModule.aioCreateGeneratorPanelRuntime({
    document,
    window,
    requestAnimationFrame(callback) {
      dependencyCalls += 1;
      animationFrames.push(callback);
    },
    panelMinHeight: 430,
    controls: {
      numberInput,
      checkbox,
      selectInput,
      createNodeField,
    },
    text: {
      get: text,
      format,
      applyTooltip,
    },
    settingsCore,
    nodeAdapter,
    profileAdapter,
    previewAdapter,
    actions,
  });

  return {
    runtime,
    document,
    trace,
    animationFrames,
    actionCalls,
    defaultSettings,
    dependencyCalls: () => dependencyCalls,
  };
}

const fixture = createFixture();
assert.deepEqual(Object.keys(fixture.runtime).sort(), [
  "ensurePanel",
  "refreshSeedButtons",
  "renderPanel",
  "scheduleLayout",
  "updateSummary",
]);
assert.equal(fixture.dependencyCalls(), 0, "factory creation must have no side effects");

const settings = clone(fixture.defaultSettings);
settings.sampler.spectrum.enabled = true;
settings.sampler.dit_corrections.enabled = true;
settings.highres.enabled = true;
settings.highres.inherit_sampler_settings = false;
settings.detailer.enabled = true;
settings.detailer.face.enabled = true;
settings.detailer.eye.enabled = true;
settings.upscale.enabled = true;
settings.upscale.backend = "usdu";
settings.upscale.usdu.auto_tile_size = true;
settings.postprocess.enabled = true;
settings.save.enabled = true;
settings.preview.image_feed = true;
settings.preview.compare_previous = true;

const images = [
  {
    filename: "first.png",
    name: "first",
    label: "First image",
    width: 512,
    height: 768,
    fileSize: "1 MB",
  },
  {
    filename: "second.png",
    name: "second",
    label: "Second image",
    width: 768,
    height: 512,
    fileSize: "2 MB",
  },
];
const widgetCalls = [];
const node = {
  settings,
  widgetValues: {
    seed: settings.sampler.seed,
    steps: settings.sampler.steps,
    cfg: settings.sampler.cfg,
    denoise: settings.sampler.denoise,
    sampler_name: settings.sampler.sampler_name,
    scheduler: settings.sampler.scheduler,
  },
  profileValue: "user:Portrait",
  size: [500, 700],
  minWidth: 400,
  __easyuseAnimaGeneratorPreviewImages: images,
  __easyuseAnimaSelectedPreviewIndex: 1,
  addDOMWidget(name, type, element, options) {
    widgetCalls.push({ name, type, element, options });
  },
};

const firstEnsureStart = fixture.trace.length;
fixture.runtime.ensurePanel(node);
const firstEnsureTrace = fixture.trace.slice(firstEnsureStart);
const panel = node.__easyuseAnimaGeneratorPanelEl;
const firstMain = panel.children[0];
const secondEnsureStart = fixture.trace.length;
fixture.runtime.ensurePanel(node);
const secondEnsureTrace = fixture.trace.slice(secondEnsureStart);
const assertEnsureOrder = (runTrace) => {
  const ensureStyleIndex = runTrace.indexOf("ensure-style");
  const suppressIndex = runTrace.indexOf('suppress:{"markDirty":false}');
  const firstNativeHiddenIndex = runTrace.indexOf("native-hidden");
  const renderStartIndex = runTrace.indexOf("get-settings");
  const lastNativeHiddenIndex = runTrace.lastIndexOf("native-hidden");
  assert.ok(ensureStyleIndex < suppressIndex);
  assert.ok(suppressIndex < firstNativeHiddenIndex);
  assert.ok(firstNativeHiddenIndex < renderStartIndex);
  assert.ok(renderStartIndex < lastNativeHiddenIndex);
};
assertEnsureOrder(firstEnsureTrace);
assertEnsureOrder(secondEnsureTrace);
assert.equal(node.__easyuseAnimaGeneratorPanelEl, panel, "panel root identity must be stable");
assert.equal(panel.className, "easyuse-anima-aio-node-panel");
assert.equal(firstMain.parentElement, null, "rerender must replace children without replacing the root");
assert.equal(widgetCalls.length, 1, "repeated ensure must not add another DOM widget");
assert.equal(node.serialize_widgets, true);
assert.equal(node.minWidth, 560);
assert.deepEqual(node.size, [620, 700]);
assert.equal(widgetCalls[0].name, "easyuse_anima_generator_panel");
assert.equal(widgetCalls[0].type, "EasyUseAnimaGeneratorPanel");
assert.equal(widgetCalls[0].element, panel);
assert.equal(widgetCalls[0].options.serialize, false);
assert.equal(widgetCalls[0].options.hideOnZoom, false);
assert.equal(widgetCalls[0].options.getMinHeight(), 430);
assert.equal(fixture.trace.filter((value) => value === "ensure-style").length, 2);
assert.equal(
  fixture.trace.filter((value) => value === "suppress:{\"markDirty\":false}").length,
  2,
);
assert.equal(fixture.trace.filter((value) => value === "native-hidden").length, 4);
for (const eventName of [
  "pointerdown",
  "mousedown",
  "pointerup",
  "mouseup",
  "click",
  "dblclick",
  "keydown",
  "keyup",
  "wheel",
]) {
  assert.equal(panel.listeners.get(eventName)?.length, 1, eventName + " listener must bind once");
}

assert.equal(fixture.animationFrames.length, 1, "two renders before a frame must coalesce layout");
panel.style.height = "999px";
panel.style["max-height"] = "999px";
const dirtyBeforeFirstLayout = node.dirtyCount || 0;
fixture.animationFrames.shift()();
assert.equal(node.__easyuseAnimaGeneratorLayoutScheduled, false);
assert.equal(panel.style.width, "600px");
assert.equal(panel.style.maxWidth, "600px");
assert.equal(panel.style.getPropertyValue("height"), "");
assert.equal(panel.style.getPropertyValue("max-height"), "");
assert.equal(node.dirtyCount, dirtyBeforeFirstLayout + 1);
fixture.runtime.scheduleLayout(node);
fixture.runtime.scheduleLayout(node);
assert.equal(fixture.animationFrames.length, 1, "explicit layout requests must coalesce");
fixture.animationFrames.shift()();
assert.equal(node.dirtyCount, dirtyBeforeFirstLayout + 2);

const controlClick = panel.emit("click", {
  target: panel.querySelector("[data-aio-seed-input]"),
});
assert.equal(controlClick.propagationStopped, true);
const backgroundClick = panel.emit("click", { target: panel });
assert.equal(backgroundClick.propagationStopped, false);
const backgroundPointer = panel.emit("pointerdown", { target: panel });
assert.equal(backgroundPointer.propagationStopped, false);
panel.emit("wheel", { target: panel });
assert.equal(fixture.trace.includes("forward-wheel"), true);

const main = panel.children[0];
assert.equal(main.className, "easyuse-anima-aio-node-main");
const samplerCard = main.children[0];
const previewCard = main.children[1];
assert.equal(samplerCard.classList.contains("easyuse-anima-aio-node-settings"), true);
assert.equal(previewCard.classList.contains("easyuse-anima-aio-node-preview"), true);
const samplerHeader = samplerCard.children[0];
const samplerActions = samplerHeader.children[1];
assert.equal(samplerActions.children[0].getAttribute("data-aio-profile-button"), "");
assert.equal(samplerActions.children[0].textContent, "Portrait");
assert.equal(samplerActions.children[3].getAttribute("data-aio-save-button"), "");
assert.equal(samplerActions.children[3].classList.contains("active"), true);
assert.equal(samplerActions.children[3].title, "text:button.saveOn");
assert.equal(
  panel.querySelector("[data-aio-backend-summary]").textContent,
  "Spectrum Patch + Corrections / Comfy KSampler",
);

const settingsScroll = samplerCard.children[1];
assert.equal(settingsScroll.className, "easyuse-anima-aio-node-settings-scroll");
assert.equal(settingsScroll.children.length, 5);
assert.equal(
  settingsScroll.children.slice(1).every(
    (block) => block.className === "easyuse-anima-aio-node-stage-block",
  ),
  true,
);
assert.deepEqual(
  settingsScroll.children.slice(1).map((block) => block.children[0].children[0].textContent),
  [
    "text:title.highres",
    "text:title.detailer",
    "text:title.upscale",
    "text:title.postprocess",
  ],
);
assert.equal(
  panel.querySelector("[data-aio-preview-box]").className,
  "easyuse-anima-aio-node-preview-box",
);
assert.equal(
  panel.querySelector("[data-aio-preview-feed]").className,
  "easyuse-anima-aio-node-preview-feed",
);

node.profileValue = "custom";
node.settings.save.enabled = false;
node.settings.sampler.backend = "spectrum_spd_speed";
fixture.runtime.updateSummary(node);
assert.equal(samplerActions.children[0].textContent, "text:profile.custom");
assert.equal(samplerActions.children[0].title, "text:profile.selectTip");
assert.equal(samplerActions.children[3].classList.contains("active"), false);
assert.equal(samplerActions.children[3].title, "text:button.saveOff");
assert.equal(
  panel.querySelector("[data-aio-backend-summary]").textContent,
  "Spectrum SPD / SPEED",
);
assert.equal(
  panel.querySelector("[data-aio-backend-summary]").title,
  "Spectrum SPD / SPEED",
);

samplerActions.children[0].emit("click");
samplerActions.children[1].emit("click");
samplerActions.children[2].emit("click");
samplerActions.children[3].emit("click");
for (const stageBlock of settingsScroll.children.slice(1)) {
  stageBlock.children[0].children[1].children[0].emit("click");
}
previewCard.children[0].children[1].children[0].emit("click");
assert.deepEqual(
  fixture.actionCalls.map((call) => call.name),
  [
    "openProfileSettings",
    "openSamplerSettings",
    "openAdvancedSettings",
    "openSaveSettings",
    "openHighresSettings",
    "openDetailerSettings",
    "openUpscaleSettings",
    "openPostprocessSettings",
    "openPreviewSettings",
  ],
);
assert.equal(fixture.actionCalls.every((call) => call.node === node), true);

let previewBox = panel.querySelector("[data-aio-preview-box]");
let previewMeta = panel.querySelector("[data-aio-preview-meta]");
let previewFeed = panel.querySelector("[data-aio-preview-feed]");
const compare = previewBox.children[0];
assert.equal(compare.className, "easyuse-anima-aio-node-preview-compare");
assert.equal(compare.style.getPropertyValue("--aio-compare-x"), "50%");
assert.equal(
  compare.children[0].className,
  "easyuse-anima-aio-node-preview-layer before",
);
assert.equal(compare.children[0].children[0].src, "/view/second.png");
assert.equal(
  compare.children[1].className,
  "easyuse-anima-aio-node-preview-layer after",
);
assert.equal(compare.children[1].children[0].src, "/view/first.png");
assert.equal(
  compare.children[2].className,
  "easyuse-anima-aio-node-preview-divider",
);
assert.equal(
  compare.children[3].children[0].textContent,
  "text:text.previewCurrent · Second image",
);
assert.equal(
  compare.children[3].children[1].textContent,
  "text:text.previewPrevious · First image",
);
compare.boundingClientRect = { left: 10, top: 0, width: 200, height: 100 };
const compareDown = compare.emit("pointerdown", { clientX: 60 });
assert.equal(compareDown.propagationStopped, true);
assert.equal(compare.style.getPropertyValue("--aio-compare-x"), "25.00%");
compare.emit("pointermove", { clientX: 210 });
assert.equal(compare.style.getPropertyValue("--aio-compare-x"), "100.00%");
assert.equal(previewMeta.textContent, "second · 768x512 · 2 MB");
assert.equal(previewFeed.hidden, false);
assert.equal(previewFeed.children.length, 2);
assert.equal(previewFeed.children[0].children[0].src, "/view/first.png");
assert.equal(previewFeed.children[1].children[0].src, "/view/second.png");
assert.equal(previewFeed.children[1].classList.contains("active"), true);
assert.equal(previewFeed.children[1].scrollIntoViewCalls.length, 1);
previewFeed.children[0].emit("click");
assert.equal(node.__easyuseAnimaSelectedPreviewIndex, 0);
assert.equal(previewBox.children[0].tagName, "IMG");
assert.equal(previewBox.children[0].src, "/view/first.png");
assert.equal(previewMeta.textContent, "first · 512x768 · 1 MB");

node.__easyuseAnimaGeneratorDenoisePreview = {
  url: "blob:denoise",
  value: 3,
  max: 8,
};
fixture.runtime.updateSummary(node);
assert.equal(
  previewBox.children[0].className,
  "easyuse-anima-aio-node-denoise-preview",
);
assert.equal(previewBox.children[0].children[0].src, "blob:denoise");
assert.equal(previewBox.children[0].children[0].decoding, "async");
assert.equal(
  previewBox.children[0].children[1].textContent,
  "text:text.previewDenoise · 3/8",
);
assert.equal(previewMeta.textContent, "");
assert.equal(previewFeed.children.length, 3);
const pendingThumb = previewFeed.children.at(-1);
assert.equal(pendingThumb.classList.contains("pending"), true);
assert.equal(pendingThumb.disabled, true);
assert.equal(pendingThumb.scrollIntoViewCalls.length, 1);

delete node.__easyuseAnimaGeneratorDenoisePreview;
node.__easyuseAnimaGeneratorPreviewImages = [];
fixture.runtime.updateSummary(node);
assert.equal(previewFeed.hidden, true);
assert.equal(previewMeta.textContent, "-");
assert.equal(
  previewBox.children[0].className,
  "easyuse-anima-aio-node-denoise-preview",
  "mechanical extraction must preserve the current no-image placeholder behavior",
);

node.__easyuseAnimaLastQueuedSeed = 777;
fixture.runtime.refreshSeedButtons(node);
let seedLast = panel.querySelector("[data-aio-seed-last]");
assert.equal(seedLast.disabled, false);
assert.equal(seedLast.textContent, 'format:button.useLast:{"seed":777}');
fixture.trace.length = 0;
findByText(panel, "text:button.newFixed").emit("click");
assert.equal(node.widgetValues.seed, 123456);
assert.equal(node.settings.sampler.seed, 123456);
assert.equal(fixture.trace.includes("random-seed"), true);
assert.ok(fixture.trace.indexOf("set-widget:seed:123456") < fixture.trace.indexOf("sync-visible"));
assert.ok(fixture.trace.indexOf("sync-visible") < fixture.trace.indexOf("get-settings"));
assert.ok(fixture.trace.indexOf("get-settings") < fixture.trace.lastIndexOf("dirty"));
fixture.trace.length = 0;
findByText(panel, "text:button.randomEach").emit("click");
assert.equal(node.widgetValues.seed, -1);
assert.equal(node.settings.sampler.seed, -1);
assert.ok(fixture.trace.indexOf("set-widget:seed:-1") < fixture.trace.indexOf("sync-visible"));
const seedInput = panel.querySelector("[data-aio-seed-input]");
seedInput.value = "314";
fixture.trace.length = 0;
seedInput.emit("input");
assert.equal(node.widgetValues.seed, 314);
assert.equal(node.settings.sampler.seed, 314);
assert.ok(fixture.trace.indexOf("set-widget:seed:314") < fixture.trace.indexOf("sync-visible"));
assert.ok(fixture.trace.indexOf("sync-visible") < fixture.trace.indexOf("get-settings"));
assert.ok(fixture.trace.indexOf("get-settings") < fixture.trace.lastIndexOf("dirty"));
seedLast = panel.querySelector("[data-aio-seed-last]");
seedLast.emit("click");
assert.equal(node.widgetValues.seed, 777);
assert.equal(node.settings.sampler.seed, 777);
assert.equal(seedLast.disabled, true);

const highresBlock = settingsScroll.children[1];
const highresToggle = highresBlock.children[0].children[1].children[1].children[0];
highresToggle.checked = false;
node.settings.sampler.seed_after_generate = "invalid";
fixture.trace.length = 0;
highresToggle.emit("change");
assert.equal(node.settings.highres.enabled, false);
assert.equal(node.settings.sampler.seed_after_generate, "fixed");
assert.deepEqual(fixture.trace.slice(0, 3), [
  "get-settings",
  "apply-visible",
  "write:true",
]);
assert.ok(
  fixture.trace.indexOf("write:true") < fixture.trace.indexOf("sync-profile"),
  "settings write must complete before summary/profile refresh",
);
assert.notEqual(panel.children[0], main, "rerendering a stage toggle must replace panel children");

assert.equal(findByClass(panel, "easyuse-anima-aio-node-main") != null, true);
console.log("AiO generator panel runtime smoke passed.");
