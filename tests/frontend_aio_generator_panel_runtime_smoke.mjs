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

function findByAttribute(root, name, value) {
  return find(root, (element) => element.getAttribute(name) === value);
}

function findField(root, label) {
  return find(root, (element) => element.getAttribute("data-test-label") === label);
}

const PANEL_EVENT_NAMES = [
  "pointerdown",
  "mousedown",
  "pointerup",
  "mouseup",
  "click",
  "dblclick",
  "keydown",
  "keyup",
  "wheel",
];

function listenerCapture(options = false) {
  return typeof options === "boolean" ? options : !!options?.capture;
}

const panelModule = await import(dataModule("../web/js/aio/generator_panel_runtime.js"));
const settingsModule = await import(dataModule("../web/js/aio/settings.js"));
assert.deepEqual(
  Object.keys(panelModule),
  ["aioCreateGeneratorPanelRuntime"],
  "Generator panel runtime must expose only its factory contract",
);

{
  const document = createFakeDocument();
  const input = document.createElement("input");
  const textarea = document.createElement("textarea");
  input.value = "first\nsecond";
  textarea.value = "first\nsecond";
  assert.equal(input.value, "firstsecond", "Fake input must model browser newline stripping");
  assert.equal(textarea.value, "first\nsecond", "Fake textarea must preserve multiline values");
}

{
  const entrySource = readFileSync(
    new URL("../web/js/easyuse_anima_aio.js", import.meta.url),
    "utf8",
  );
  assert.match(
    entrySource,
    /\.easyuse-anima-aio-node-info-button:focus-visible\s*\{/,
    "info icons must publish a keyboard-visible focus ring",
  );
  assert.match(
    entrySource,
    /\.easyuse-anima-aio-node-info-tooltip\s*\{[^}]*pointer-events:\s*none;/s,
    "tooltip portals must not intercept panel wheel or pointer routing",
  );
  for (const removedTextKey of [
    "text.highresDisabled",
    "text.detailerDisabled",
    "text.upscaleDisabled",
    "text.postprocessDisabled",
    "text.inheritsMainSampler",
    "text.usesStageSamplerOverride",
  ]) {
    assert.equal(
      entrySource.includes(`"${removedTextKey}"`),
      false,
      removedTextKey + " must not remain duplicated as inline text",
    );
  }
  for (const localizedTipKey of [
    "label.info",
    "tip.highresDisabled",
    "tip.detailerDisabled",
    "tip.upscaleDisabled",
    "tip.postprocessDisabled",
    "tip.stageSamplerOverride",
  ]) {
    assert.equal(
      entrySource.split(`"${localizedTipKey}"`).length - 1,
      4,
      localizedTipKey + " must preserve en/ko/ja/zh meaning",
    );
  }
  const functionStart = entrySource.indexOf("function commitGeneratorSeedValue");
  const functionEnd = entrySource.indexOf(
    "\nfunction syncGeneratorSerializedWidgets",
    functionStart,
  );
  assert.ok(functionStart >= 0 && functionEnd > functionStart);
  const commitGeneratorSeedValue = new Function(
    "findWidget",
    "GENERATOR_SETTINGS_WIDGET",
    "generatorSettings",
    `"use strict";\n${entrySource.slice(functionStart, functionEnd)}\nreturn commitGeneratorSeedValue;`,
  )(
    (node, name) => node.widgets.find((widget) => widget.name === name),
    "generation_settings",
    (node) => clone(node.settings),
  );
  const seedCallbackError = new Error("seed callback failed");
  const settingsCallbackError = new Error("settings callback failed");
  const callbackTrace = [];
  const seedWidget = {
    name: "seed",
    value: 10,
    callback() {
      callbackTrace.push("seed");
      throw seedCallbackError;
    },
  };
  const settingsWidget = {
    name: "generation_settings",
    value: JSON.stringify({ sampler: { seed: 10 } }),
    callback() {
      callbackTrace.push("settings");
      throw settingsCallbackError;
    },
  };
  const atomicNode = {
    widgets: [seedWidget, settingsWidget],
    settings: { sampler: { seed: 10, seed_after_generate: "increment" } },
    __easyuseAnimaGeneratorUiValues: { seed: 10 },
  };
  assert.doesNotThrow(() => commitGeneratorSeedValue(atomicNode, 11));
  assert.deepEqual(callbackTrace, ["seed", "settings"]);
  assert.equal(seedWidget.value, 11);
  assert.equal(atomicNode.__easyuseAnimaGeneratorUiValues.seed, 11);
  assert.equal(JSON.parse(settingsWidget.value).sampler.seed, 11);
}

function createFixture() {
  let dependencyCalls = 0;
  let nextAnimationFrameId = 1;
  const trace = [];
  const animationFrames = [];
  const canceledAnimationFrames = [];
  const staleAnimationFrames = [];
  const domWidgetStore = new Set();
  const actionCalls = [];
  const document = createFakeDocument();
  const windowListeners = new Map();
  const window = {
    addEventListener(type, handler, options = false) {
      dependencyCalls += 1;
      const entries = windowListeners.get(type) || [];
      const capture = listenerCapture(options);
      if (!entries.some((entry) => entry.handler === handler && entry.capture === capture)) {
        entries.push({ handler, capture });
      }
      windowListeners.set(type, entries);
    },
    removeEventListener(type, handler, options = false) {
      dependencyCalls += 1;
      const entries = windowListeners.get(type) || [];
      const capture = listenerCapture(options);
      windowListeners.set(
        type,
        entries.filter((entry) => entry.handler !== handler || entry.capture !== capture),
      );
    },
  };

  function requestAnimationFrame(callback) {
    dependencyCalls += 1;
    callback.__frameId = nextAnimationFrameId;
    nextAnimationFrameId += 1;
    animationFrames.push(callback);
    return callback.__frameId;
  }

  function cancelAnimationFrame(frameId) {
    dependencyCalls += 1;
    canceledAnimationFrames.push(frameId);
    const index = animationFrames.findIndex(
      (callback) => callback.__frameId === frameId,
    );
    if (index >= 0) {
      staleAnimationFrames.push(...animationFrames.splice(index, 1));
    }
  }

  function windowListenerCount(type, options) {
    const entries = windowListeners.get(type) || [];
    if (arguments.length < 2) {
      return entries.length;
    }
    const capture = listenerCapture(options);
    return entries.filter((entry) => entry.capture === capture).length;
  }

  function dispatchWindow(type, event = {}) {
    for (const entry of [...(windowListeners.get(type) || [])]) {
      entry.handler(event);
    }
  }

  function dispatchDocument(type, event = {}) {
    const nextEvent = {
      target: document.body,
      defaultPrevented: false,
      preventDefault() {
        this.defaultPrevented = true;
      },
      ...event,
    };
    for (const entry of [...(document.listeners.get(type) || [])]) {
      entry.handler(nextEvent);
    }
    return nextEvent;
  }

  function runStaleAnimationFrames() {
    for (const callback of staleAnimationFrames.splice(0)) {
      callback();
    }
  }

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

  function textareaInput(value) {
    dependencyCalls += 1;
    const textarea = document.createElement("textarea");
    textarea.value = String(value ?? "");
    return textarea;
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
    commitSeedValue(node, seed) {
      dependencyCalls += 1;
      trace.push("commit-seed:" + seed);
      if (node.failSeedCommit) {
        throw node.failSeedCommit;
      }
      node.widgetValues.seed = seed;
      node.settings.sampler.seed = seed;
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
    requestAnimationFrame,
    cancelAnimationFrame,
    panelMinHeight: 430,
    controls: {
      numberInput,
      checkbox,
      textareaInput,
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
    window,
    trace,
    animationFrames,
    canceledAnimationFrames,
    domWidgetStore,
    runStaleAnimationFrames,
    windowListenerCount,
    dispatchWindow,
    dispatchDocument,
    actionCalls,
    defaultSettings,
    dependencyCalls: () => dependencyCalls,
  };
}

function createOwnerTestNode(fixture, settings) {
  const nodeSettings = clone(settings);
  return {
    settings: nodeSettings,
    widgets: [],
    widgets_values: ["owner-test-widget-state"],
    widgetValues: {
      seed: nodeSettings.sampler.seed,
      steps: nodeSettings.sampler.steps,
      cfg: nodeSettings.sampler.cfg,
      denoise: nodeSettings.sampler.denoise,
      sampler_name: nodeSettings.sampler.sampler_name,
      scheduler: nodeSettings.sampler.scheduler,
    },
    profileValue: "custom",
    size: [620, 700],
    minWidth: 560,
    __easyuseAnimaGeneratorPreviewImages: [],
    __easyuseAnimaSelectedPreviewIndex: 0,
    addDOMWidget(name, type, element, options) {
      const widget = {
        name,
        type,
        element,
        options,
        onRemoveCalls: 0,
        onRemove() {
          this.onRemoveCalls += 1;
          fixture.domWidgetStore.delete(this);
        },
      };
      this.widgets.push(widget);
      fixture.domWidgetStore.add(widget);
      fixture.document.body.append(element);
      return widget;
    },
  };
}

function infoTooltipFor(fixture, button) {
  return findByAttribute(
    fixture.document.body,
    "id",
    button.getAttribute("aria-describedby"),
  );
}

function visibleInfoTooltips(fixture) {
  return fixture.document
    .querySelectorAll("[data-aio-info-tooltip]")
    .filter((tooltip) => !tooltip.hidden);
}

function clickInfoTrigger(fixture, button) {
  fixture.dispatchDocument("pointerdown", { target: button });
  fixture.dispatchDocument("click", { target: button });
  button.emit("click");
}

const OWNER_DOCUMENT_EVENT_NAMES = ["pointerdown", "click", "touchstart", "keydown"];

function assertOwnerDocumentListenerCount(fixture, expected, message) {
  for (const eventName of OWNER_DOCUMENT_EVENT_NAMES) {
    assert.equal(
      fixture.document.listenerCount(eventName, true),
      expected,
      message + ": " + eventName,
    );
  }
}

{
  const ownerFixture = createFixture();
  const ownerSettings = clone(ownerFixture.defaultSettings);
  ownerSettings.highres.enabled = true;
  ownerSettings.highres.inherit_sampler_settings = false;
  ownerSettings.detailer.enabled = true;
  ownerSettings.detailer.face.enabled = true;
  const firstNode = createOwnerTestNode(ownerFixture, ownerSettings);
  const secondNode = createOwnerTestNode(ownerFixture, ownerSettings);
  ownerFixture.runtime.ensurePanel(firstNode);
  ownerFixture.runtime.ensurePanel(secondNode);
  const firstPanel = firstNode.__easyuseAnimaGeneratorPanelEl;
  const secondPanel = secondNode.__easyuseAnimaGeneratorPanelEl;
  const firstHighres = findByAttribute(firstPanel, "data-aio-focus-key", "highres.info");
  const firstDetailer = findByAttribute(
    firstPanel,
    "data-aio-focus-key",
    "detailer.face.follow-main.info",
  );
  const secondDetailer = findByAttribute(
    secondPanel,
    "data-aio-focus-key",
    "detailer.face.follow-main.info",
  );
  assert.ok(firstHighres && firstDetailer && secondDetailer);
  const firstHighresTooltip = infoTooltipFor(ownerFixture, firstHighres);
  const firstDetailerTooltip = infoTooltipFor(ownerFixture, firstDetailer);
  const secondDetailerTooltip = infoTooltipFor(ownerFixture, secondDetailer);
  assert.ok(firstHighresTooltip && firstDetailerTooltip && secondDetailerTooltip);
  assertOwnerDocumentListenerCount(ownerFixture, 0, "closed tooltips must not own document listeners");

  clickInfoTrigger(ownerFixture, firstHighres);
  assert.equal(visibleInfoTooltips(ownerFixture).length, 1);
  assert.equal(firstHighres.getAttribute("aria-expanded"), "true");
  clickInfoTrigger(ownerFixture, firstDetailer);
  assert.equal(
    visibleInfoTooltips(ownerFixture).length,
    1,
    "opening Detailer after Highres must leave exactly one visible portal",
  );
  assert.equal(firstHighresTooltip.hidden, true);
  assert.equal(firstHighres.getAttribute("aria-expanded"), "false");
  assert.equal(firstDetailerTooltip.hidden, false);
  assert.equal(firstDetailer.getAttribute("aria-expanded"), "true");
  assertOwnerDocumentListenerCount(ownerFixture, 1, "the current owner must bind once");

  clickInfoTrigger(ownerFixture, firstDetailer);
  assert.equal(visibleInfoTooltips(ownerFixture).length, 0, "trigger click must toggle closed");
  clickInfoTrigger(ownerFixture, firstDetailer);
  assert.equal(visibleInfoTooltips(ownerFixture).length, 1, "trigger click must toggle open");
  ownerFixture.dispatchDocument("pointerdown", { target: firstDetailerTooltip });
  ownerFixture.dispatchDocument("click", { target: firstDetailerTooltip });
  ownerFixture.dispatchDocument("touchstart", { target: firstDetailerTooltip });
  assert.equal(
    firstDetailerTooltip.hidden,
    false,
    "tooltip-contained interaction must preserve the current owner",
  );

  const outside = ownerFixture.document.createElement("div");
  ownerFixture.document.body.append(outside);
  ownerFixture.dispatchDocument("pointerdown", { target: outside });
  assert.equal(visibleInfoTooltips(ownerFixture).length, 0);
  assert.equal(firstDetailer.getAttribute("aria-expanded"), "false");
  clickInfoTrigger(ownerFixture, firstDetailer);
  ownerFixture.dispatchDocument("click", { target: outside });
  assert.equal(visibleInfoTooltips(ownerFixture).length, 0);
  clickInfoTrigger(ownerFixture, firstDetailer);
  ownerFixture.dispatchDocument("touchstart", { target: outside });
  assert.equal(visibleInfoTooltips(ownerFixture).length, 0);
  assertOwnerDocumentListenerCount(ownerFixture, 0, "outside close must release document listeners");

  clickInfoTrigger(ownerFixture, firstHighres);
  clickInfoTrigger(ownerFixture, firstDetailer);
  const escapeEvent = ownerFixture.dispatchDocument("keydown", {
    key: "Escape",
    target: outside,
  });
  assert.equal(escapeEvent.defaultPrevented, true);
  assert.equal(visibleInfoTooltips(ownerFixture).length, 0, "Escape must close the global owner");
  assert.equal(firstHighres.getAttribute("aria-expanded"), "false");
  assert.equal(firstDetailer.getAttribute("aria-expanded"), "false");

  clickInfoTrigger(ownerFixture, firstHighres);
  const staleOutsideHandler = ownerFixture.document.listeners.get("click")[0].handler;
  clickInfoTrigger(ownerFixture, secondDetailer);
  assert.equal(firstHighresTooltip.hidden, true);
  assert.equal(secondDetailerTooltip.hidden, false);
  staleOutsideHandler({ target: outside });
  assert.equal(
    secondDetailerTooltip.hidden,
    false,
    "a stale owner close callback must not close the newer owner",
  );
  ownerFixture.runtime.disposePanel(firstNode);
  assert.equal(
    secondDetailerTooltip.hidden,
    false,
    "stale panel dispose must not close the newer owner",
  );
  assertOwnerDocumentListenerCount(ownerFixture, 1, "stale cleanup must preserve the newer listener owner");
  ownerFixture.runtime.ensurePanel(firstNode);

  const otherFixture = createFixture();
  const otherNode = createOwnerTestNode(otherFixture, ownerSettings);
  otherFixture.runtime.ensurePanel(otherNode);
  const otherHighres = findByAttribute(
    otherNode.__easyuseAnimaGeneratorPanelEl,
    "data-aio-focus-key",
    "highres.info",
  );
  const otherHighresTooltip = infoTooltipFor(otherFixture, otherHighres);
  assert.ok(otherHighres && otherHighresTooltip);
  clickInfoTrigger(otherFixture, otherHighres);
  assert.equal(visibleInfoTooltips(ownerFixture).length, 1);
  assert.equal(visibleInfoTooltips(otherFixture).length, 1);
  assert.equal(secondDetailerTooltip.hidden, false);
  assert.equal(otherHighresTooltip.hidden, false, "different documents must retain independent owners");

  const rerenderedFirstHighres = findByAttribute(
    firstNode.__easyuseAnimaGeneratorPanelEl,
    "data-aio-focus-key",
    "highres.info",
  );
  clickInfoTrigger(ownerFixture, rerenderedFirstHighres);
  assert.equal(secondDetailerTooltip.hidden, true);
  assert.equal(otherHighresTooltip.hidden, false);
  ownerFixture.runtime.disposePanel(firstNode);
  assert.equal(visibleInfoTooltips(ownerFixture).length, 0);
  assert.equal(otherHighresTooltip.hidden, false, "disposing another document must not close its owner");
  assertOwnerDocumentListenerCount(ownerFixture, 0, "current panel dispose must restore baseline");
  ownerFixture.runtime.disposePanel(secondNode);
  assert.equal(ownerFixture.document.querySelectorAll("[data-aio-info-tooltip]").length, 0);

  otherFixture.runtime.renderPanel(otherNode);
  assert.equal(otherHighresTooltip.parentElement, null, "rerender must remove the owned portal");
  assertOwnerDocumentListenerCount(otherFixture, 0, "current panel rerender must restore baseline");
  otherFixture.runtime.disposePanel(otherNode);
  assert.equal(otherFixture.document.querySelectorAll("[data-aio-info-tooltip]").length, 0);
}

const fixture = createFixture();
assert.deepEqual(Object.keys(fixture.runtime).sort(), [
  "activatePanel",
  "disposePanel",
  "ensurePanel",
  "refreshSeedButtons",
  "renderPanel",
  "scheduleLayout",
  "scheduleSummary",
  "updateSeed",
  "updateSummary",
]);
assert.equal(fixture.dependencyCalls(), 0, "factory creation must have no side effects");

const captureProbe = () => {};
const captureElement = fixture.document.createElement("div");
captureElement.addEventListener("probe", captureProbe, { capture: true });
captureElement.removeEventListener("probe", captureProbe, false);
assert.equal(
  captureElement.listenerCount("probe", true),
  1,
  "element listener removal with the wrong capture flag must be a no-op",
);
captureElement.removeEventListener("probe", captureProbe, true);
assert.equal(captureElement.listenerCount("probe"), 0);
fixture.window.addEventListener("probe", captureProbe, { capture: true });
fixture.window.removeEventListener("probe", captureProbe, false);
assert.equal(
  fixture.windowListenerCount("probe", true),
  1,
  "window listener removal with the wrong capture flag must be a no-op",
);
fixture.window.removeEventListener("probe", captureProbe, true);
assert.equal(fixture.windowListenerCount("probe"), 0);

const settings = clone(fixture.defaultSettings);
settings.sampler.spectrum.enabled = true;
settings.sampler.dit_corrections.enabled = true;
settings.highres.enabled = true;
settings.highres.inherit_sampler_settings = false;
settings.detailer.enabled = true;
settings.detailer.face.enabled = true;
settings.detailer.face.preserved_unknown = { nested: "keep-panel" };
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
  widgets: [],
  widgets_values: ["serialized-widget-state"],
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
    const widget = {
      name,
      type,
      element,
      options,
      onRemoveCalls: 0,
      onRemoveError: null,
      onRemove() {
        this.onRemoveCalls += 1;
        fixture.domWidgetStore.delete(this);
        if (this.onRemoveError) {
          throw this.onRemoveError;
        }
      },
    };
    widgetCalls.push(widget);
    this.widgets.push(widget);
    fixture.domWidgetStore.add(widget);
    fixture.document.body.append(element);
    return widget;
  },
};

const firstEnsureStart = fixture.trace.length;
fixture.runtime.ensurePanel(node);
const firstEnsureTrace = fixture.trace.slice(firstEnsureStart);
const panel = node.__easyuseAnimaGeneratorPanelEl;
const firstMain = panel.children[0];
const firstInfoButtons = panel.querySelectorAll("[data-aio-info-button]");
const firstInfoTooltips = fixture.document.querySelectorAll("[data-aio-info-tooltip]");
assert.equal(firstInfoButtons.length, firstInfoTooltips.length);
assert.equal(firstInfoButtons.length, 8, "each static stage/field hint must own one info icon");
const secondEnsureStart = fixture.trace.length;
fixture.runtime.ensurePanel(node);
const secondEnsureTrace = fixture.trace.slice(secondEnsureStart);
assert.equal(
  firstInfoTooltips.every((tooltip) => tooltip.parentElement == null),
  true,
  "rerender must remove every tooltip portal owned by the previous render",
);
assert.equal(
  firstInfoButtons.every((button) => button.listenerCount("click") === 0),
  true,
  "rerender must dispose old info-button listeners",
);
assert.equal(
  panel.querySelectorAll("[data-aio-info-button]").length,
  fixture.document.querySelectorAll("[data-aio-info-tooltip]").length,
  "rerender must not duplicate info buttons or tooltip portals",
);
const initialPanelLifecycle = fixture.runtime.activatePanel(node);
assert.equal(fixture.runtime.activatePanel(node), initialPanelLifecycle);
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
const panelWidget = widgetCalls[0];
assert.equal(node.__easyuseAnimaGeneratorPanelWidget, panelWidget);
assert.equal(fixture.domWidgetStore.size, 1);
assert.equal(fixture.domWidgetStore.has(panelWidget), true);
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
for (const eventName of PANEL_EVENT_NAMES) {
  assert.equal(panel.listeners.get(eventName)?.length, 1, eventName + " listener must bind once");
  assert.equal(
    panel.listenerCount(eventName, eventName === "wheel"),
    1,
    eventName + " listener must bind with the expected capture flag",
  );
}

assert.equal(fixture.animationFrames.length, 1, "two renders before a frame must coalesce layout");
panel.style.height = "999px";
panel.style["max-height"] = "999px";
const dirtyBeforeFirstLayout = node.dirtyCount || 0;
fixture.animationFrames.shift()();
assert.equal(fixture.animationFrames.length, 0);
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
const serializedBeforeInfoInteraction = node.widgets_values;
const settingsBeforeInfoInteraction = clone(node.settings);
const highresFollowInfo = findByAttribute(
  panel,
  "data-aio-focus-key",
  "highres.follow-main.info",
);
assert.ok(highresFollowInfo, "Highres follow-main field must expose an info icon");
assert.equal(highresFollowInfo.textContent, "i");
assert.equal(highresFollowInfo.type, "button");
assert.equal(highresFollowInfo.getAttribute("data-aio-info-key"), "tip.stageSamplerOverride");
assert.equal(highresFollowInfo.getAttribute("aria-label"), "text:label.info");
assert.equal(highresFollowInfo.getAttribute("aria-expanded"), "false");
assert.equal(highresFollowInfo.title, "", "custom info tooltip must not compete with native title UI");
const highresFollowTooltip = findByAttribute(
  fixture.document.body,
  "id",
  highresFollowInfo.getAttribute("aria-describedby"),
);
assert.ok(highresFollowTooltip, "aria-describedby must own a live tooltip portal");
assert.equal(highresFollowInfo.getAttribute("aria-controls"), highresFollowTooltip.getAttribute("id"));
assert.equal(highresFollowTooltip.getAttribute("role"), "tooltip");
assert.equal(highresFollowTooltip.textContent, "text:tip.stageSamplerOverride");
assert.equal(highresFollowTooltip.hidden, true);
highresFollowInfo.emit("pointerenter");
assert.equal(highresFollowTooltip.hidden, false, "mouse/pointer hover must open the tooltip");
assert.equal(highresFollowInfo.getAttribute("aria-expanded"), "true");
assert.equal(fixture.windowListenerCount("resize"), 1);
assert.equal(fixture.windowListenerCount("scroll", true), 1);
highresFollowInfo.boundingClientRect = { left: 120, top: 80, width: 22, height: 22 };
fixture.dispatchWindow("scroll");
assert.equal(highresFollowTooltip.style.left, "120px");
assert.equal(highresFollowTooltip.style.top, "108px");
highresFollowInfo.boundingClientRect = { left: 160, top: 40, width: 22, height: 22 };
fixture.dispatchWindow("resize");
assert.equal(highresFollowTooltip.style.left, "160px");
assert.equal(highresFollowTooltip.style.top, "68px");
fixture.window.innerHeight = 320;
highresFollowInfo.boundingClientRect = { left: 160, top: 280, width: 22, height: 22 };
highresFollowTooltip.boundingClientRect = { left: 0, top: 0, width: 240, height: 80 };
fixture.dispatchWindow("scroll");
assert.equal(
  highresFollowTooltip.style.top,
  "194px",
  "a bottom-edge tooltip must flip above its info icon",
);
assert.ok(
  Number.parseInt(highresFollowTooltip.style.top, 10) + 80 <= fixture.window.innerHeight - 8,
  "a flipped tooltip must retain the viewport bottom margin",
);
fixture.window.innerHeight = 100;
highresFollowInfo.boundingClientRect = { left: 160, top: 90, width: 22, height: 22 };
highresFollowTooltip.boundingClientRect = { left: 0, top: 0, width: 84, height: 84 };
fixture.dispatchWindow("resize");
assert.equal(
  highresFollowTooltip.style.top,
  "8px",
  "a flipped tooltip must clamp to the viewport top margin",
);
assert.equal(
  Number.parseInt(highresFollowTooltip.style.top, 10) + 84,
  fixture.window.innerHeight - 8,
  "the clamped tooltip must stay inside the viewport bottom margin when it fits",
);
fixture.window.innerHeight = 768;
highresFollowInfo.emit("pointerleave");
assert.equal(highresFollowTooltip.hidden, true);
assert.equal(fixture.windowListenerCount("resize"), 0);
assert.equal(fixture.windowListenerCount("scroll"), 0);
highresFollowInfo.emit("focus");
assert.equal(highresFollowTooltip.hidden, false, "keyboard focus must open the tooltip");
highresFollowInfo.emit("keydown", { key: "Enter" });
assert.equal(highresFollowTooltip.hidden, true, "Enter must close a focused open tooltip");
highresFollowInfo.emit("keydown", { key: "Enter" });
assert.equal(highresFollowTooltip.hidden, false, "a second Enter must reopen the tooltip");
highresFollowInfo.emit("keydown", { key: " " });
assert.equal(highresFollowTooltip.hidden, true, "Space must close the tooltip");
highresFollowInfo.emit("keydown", { key: " " });
assert.equal(highresFollowTooltip.hidden, false, "a second Space must reopen the tooltip");
highresFollowInfo.emit("keydown", { key: "Escape" });
assert.equal(highresFollowTooltip.hidden, true, "Escape must close the tooltip");
highresFollowInfo.emit("blur");
highresFollowInfo.emit("click");
assert.equal(highresFollowTooltip.hidden, false, "click/touch activation must open the tooltip");
highresFollowInfo.emit("click");
assert.equal(highresFollowTooltip.hidden, true, "a second click must close the tooltip");
assert.deepEqual(node.settings, settingsBeforeInfoInteraction);
assert.equal(node.widgets_values, serializedBeforeInfoInteraction);
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
const stablePreviewThumbs = [...previewFeed.children];
const stableSelectedScrollCalls = stablePreviewThumbs[1].scrollIntoViewCalls.length;
previewFeed.scrollLeft = 47;
fixture.runtime.updateSummary(node);
assert.equal(previewFeed.children[0], stablePreviewThumbs[0]);
assert.equal(previewFeed.children[1], stablePreviewThumbs[1]);
assert.equal(previewFeed.scrollLeft, 47);
assert.equal(
  stablePreviewThumbs[1].scrollIntoViewCalls.length,
  stableSelectedScrollCalls,
  "an unchanged preview signature must not auto-scroll the selected thumbnail again",
);
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

const staleDenoisePreview = previewBox.children[0];
delete node.__easyuseAnimaGeneratorDenoisePreview;
node.__easyuseAnimaGeneratorPreviewImages = [];
fixture.runtime.updateSummary(node);
assert.equal(previewFeed.hidden, true);
assert.equal(previewFeed.children.length, 0);
assert.equal(previewMeta.textContent, "-");
assert.equal(previewMeta.title, "");
assert.equal(staleDenoisePreview.parentElement, null);
assert.equal(
  previewBox.children[0].className,
  "easyuse-anima-aio-node-preview-placeholder",
  "no image must restore the standard preview placeholder",
);
assert.equal(previewBox.children[0].children[0].textContent, "text:text.previewTitle");
assert.equal(previewBox.children[0].children[1].textContent, "text:text.previewSubtitle");
assert.equal(previewBox.querySelector("img"), null);

node.__easyuseAnimaGeneratorPreviewImages = [images[0]];
fixture.runtime.updateSummary(node);
const staleValidPreview = previewBox.children[0];
assert.equal(staleValidPreview.tagName, "IMG");
node.__easyuseAnimaGeneratorPreviewImages = [images[0], { label: "Missing URL" }];
node.__easyuseAnimaSelectedPreviewIndex = 1;
fixture.runtime.updateSummary(node);
assert.equal(staleValidPreview.parentElement, null);
assert.equal(previewBox.children[0].className, "easyuse-anima-aio-node-preview-placeholder");
assert.equal(previewBox.querySelector("img"), null);
assert.equal(previewFeed.hidden, false);
assert.equal(previewFeed.children.length, 1);
assert.equal(previewFeed.children[0].children[0].src, "/view/first.png");
assert.equal(previewMeta.textContent, "-");
assert.equal(previewMeta.title, "");
previewFeed.children[0].emit("click");
assert.equal(node.__easyuseAnimaSelectedPreviewIndex, 0);
assert.equal(previewBox.children[0].tagName, "IMG");
assert.equal(previewBox.children[0].src, "/view/first.png");
assert.equal(previewMeta.textContent, "first · 512x768 · 1 MB");

const recoveredValidPreview = previewBox.children[0];
node.__easyuseAnimaGeneratorPreviewImages = [
  { label: "Missing URL A" },
  { label: "Missing URL B" },
];
node.__easyuseAnimaSelectedPreviewIndex = 1;
fixture.runtime.updateSummary(node);
assert.equal(recoveredValidPreview.parentElement, null);
assert.equal(previewBox.children[0].className, "easyuse-anima-aio-node-preview-placeholder");
assert.equal(previewFeed.hidden, true);
assert.equal(previewFeed.children.length, 0);
assert.equal(previewMeta.textContent, "-");
assert.equal(previewMeta.title, "");

fixture.trace.length = 0;
node.__easyuseAnimaLastQueuedSeed = 777;
assert.equal(
  fixture.runtime.updateSeed(node, 776, {
    markDirty: false,
  }),
  776,
);
assert.equal(node.__easyuseAnimaLastQueuedSeed, 777);
assert.equal(node.widgetValues.seed, 776);
assert.equal(node.settings.sampler.seed, 776);
assert.equal(panel.querySelector("[data-aio-seed-input]").value, 776);
assert.equal(
  fixture.trace.includes("dirty"),
  false,
  "accepted queue seed updates must not mark the workflow dirty",
);
assert.equal(
  panel.querySelector("[data-aio-seed-last]").textContent,
  'format:button.useLast:{"seed":777}',
);
const seedCommitFailure = new Error("seed callback failed");
node.failSeedCommit = seedCommitFailure;
assert.throws(
  () => fixture.runtime.updateSeed(node, 888, {
    markDirty: false,
  }),
  (error) => error === seedCommitFailure,
);
delete node.failSeedCommit;
assert.equal(node.__easyuseAnimaLastQueuedSeed, 777);
assert.equal(node.widgetValues.seed, 776);
assert.equal(node.settings.sampler.seed, 776);
assert.equal(panel.querySelector("[data-aio-seed-input]").value, 776);

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
assert.ok(fixture.trace.indexOf("random-seed") < fixture.trace.indexOf("commit-seed:123456"));
assert.ok(fixture.trace.indexOf("commit-seed:123456") < fixture.trace.indexOf("get-settings"));
assert.ok(fixture.trace.indexOf("get-settings") < fixture.trace.lastIndexOf("dirty"));
fixture.trace.length = 0;
findByText(panel, "text:button.randomEach").emit("click");
assert.equal(node.widgetValues.seed, -1);
assert.equal(node.settings.sampler.seed, -1);
assert.ok(fixture.trace.indexOf("commit-seed:-1") < fixture.trace.indexOf("get-settings"));
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
const disabledHighresBlock = panel.querySelector(
  ".easyuse-anima-aio-node-settings-scroll",
).children[1];
assert.equal(disabledHighresBlock.children[1].children.length, 0);
assert.equal(findByText(disabledHighresBlock, "text:tip.highresDisabled"), null);
assert.equal(
  findByAttribute(disabledHighresBlock, "data-aio-focus-key", "highres.info")
    .getAttribute("data-aio-info-key"),
  "tip.highresDisabled",
  "disabled Highres guidance must move from body note to the header info icon",
);
assert.equal(
  panel.querySelectorAll("[data-aio-info-button]").length,
  fixture.document.querySelectorAll("[data-aio-info-tooltip]").length,
  "stage on/off rerender must keep one owned tooltip per icon",
);

while (fixture.animationFrames.length) {
  fixture.animationFrames.shift()();
}

const detailerScroll = panel.querySelector(".easyuse-anima-aio-node-settings-scroll");
const detailerStage = detailerScroll.children[2];
const faceTitle = findByText(detailerStage, "1. Face Detailer");
const faceBlock = faceTitle.parentElement.parentElement;
const faceThreshold = findField(faceBlock, "text:field.threshold");
const faceThresholdInput = faceThreshold.children[0].children[0];
const faceWildcard = findField(faceBlock, "text:field.wildcard");
const faceWildcardInput = faceWildcard.children[0];
assert.equal(faceThresholdInput.value, "0.52");
assert.equal(faceThresholdInput.min, "0");
assert.equal(faceThresholdInput.max, "1");
assert.equal(faceThresholdInput.step, "0.01");
assert.equal(faceThreshold.getAttribute("data-test-tooltip"), "tip.detailerThreshold");
assert.equal(faceWildcardInput.value, "");
assert.equal(faceWildcardInput.tagName, "TEXTAREA");
assert.equal(
  faceWildcardInput.getAttribute("data-aio-focus-key"),
  "detailer.face.wildcard",
  "Detailer wildcard textarea must retain its stable focus key",
);
assert.equal(faceWildcard.getAttribute("data-test-tooltip"), "tip.detailerWildcard");

faceThresholdInput.value = "0.63";
faceThresholdInput.emit("input");
assert.equal(node.settings.detailer.face.threshold, 0.63);
const multilineFaceWildcard = "codex_live_face\nsecond_line";
faceWildcardInput.value = multilineFaceWildcard;
faceWildcardInput.emit("input");
assert.equal(
  node.settings.detailer.face.wildcard,
  multilineFaceWildcard,
  "Detailer wildcard input must immediately write the exact multiline value",
);
assert.deepEqual(node.settings.detailer.face.preserved_unknown, { nested: "keep-panel" });

const serializedDetailerSettings = JSON.stringify(node.settings);
node.settings = JSON.parse(serializedDetailerSettings);
fixture.runtime.renderPanel(node);
let reloadedDetailerStage = panel.querySelector(
  ".easyuse-anima-aio-node-settings-scroll",
).children[2];
let reloadedFaceTitle = findByText(reloadedDetailerStage, "1. Face Detailer");
let reloadedFaceBlock = reloadedFaceTitle.parentElement.parentElement;
assert.equal(
  findField(reloadedFaceBlock, "text:field.threshold").children[0].children[0].value,
  "0.63",
  "serialized Detailer threshold must reload into the external target card",
);
assert.equal(
  findField(reloadedFaceBlock, "text:field.wildcard").children[0].tagName,
  "TEXTAREA",
  "serialized Detailer wildcard must reload into a textarea",
);
assert.equal(
  findField(reloadedFaceBlock, "text:field.wildcard").children[0].value,
  multilineFaceWildcard,
  "serialized Detailer wildcard must reload into the external target card",
);

const reloadedFaceEnabled = findField(reloadedFaceBlock, "text:label.enabled").children[0];
reloadedFaceEnabled.checked = false;
reloadedFaceEnabled.emit("change");
reloadedDetailerStage = panel.querySelector(
  ".easyuse-anima-aio-node-settings-scroll",
).children[2];
reloadedFaceTitle = findByText(reloadedDetailerStage, "1. Face Detailer");
reloadedFaceBlock = reloadedFaceTitle.parentElement.parentElement;
assert.equal(node.settings.detailer.face.enabled, false);
assert.equal(findField(reloadedFaceBlock, "text:field.threshold"), null);

const disabledFaceEnabled = findField(reloadedFaceBlock, "text:label.enabled").children[0];
disabledFaceEnabled.checked = true;
disabledFaceEnabled.emit("change");
reloadedDetailerStage = panel.querySelector(
  ".easyuse-anima-aio-node-settings-scroll",
).children[2];
reloadedFaceTitle = findByText(reloadedDetailerStage, "1. Face Detailer");
reloadedFaceBlock = reloadedFaceTitle.parentElement.parentElement;
assert.equal(node.settings.detailer.face.enabled, true);
assert.equal(
  findField(reloadedFaceBlock, "text:field.threshold").children[0].children[0].value,
  "0.63",
  "re-enabling a Detailer target must preserve its threshold",
);
assert.equal(
  findField(reloadedFaceBlock, "text:field.wildcard").children[0].value,
  multilineFaceWildcard,
  "re-enabling a Detailer target must preserve its wildcard",
);

while (fixture.animationFrames.length) {
  fixture.animationFrames.shift()();
}

const beforeStatefulRenderMain = panel.children[0];
const beforeStatefulRenderScroll = panel.querySelector(
  ".easyuse-anima-aio-node-settings-scroll",
);
const beforeStatefulRenderFeed = panel.querySelector("[data-aio-preview-feed]");
const beforeStatefulRenderSeed = panel.querySelector("[data-aio-seed-input]");
beforeStatefulRenderScroll.scrollTop = 137;
beforeStatefulRenderScroll.scrollLeft = 11;
beforeStatefulRenderFeed.scrollLeft = 29;
beforeStatefulRenderSeed.focus();
const beforeStatefulRenderSlider = findByClass(
  panel,
  "easyuse-anima-aio-node-slider-track",
);
const beforeStatefulRenderSliderInput = beforeStatefulRenderSlider.parentElement.children[0];
beforeStatefulRenderSlider.emit("pointerdown", {
  pointerId: 17,
  clientX: 40,
});
assert.equal(fixture.windowListenerCount("pointermove"), 1);
assert.equal(fixture.windowListenerCount("pointerup"), 1);
assert.equal(fixture.windowListenerCount("pointercancel"), 1);
assert.equal(fixture.windowListenerCount("blur"), 1);
for (const eventName of ["pointermove", "pointerup", "pointercancel", "blur"]) {
  assert.equal(
    fixture.windowListenerCount(eventName, true),
    1,
    eventName + " drag listener must use capture",
  );
}
assert.equal(
  fixture.animationFrames.length,
  1,
  "slider pointerdown must schedule the initial summary frame",
);
fixture.animationFrames.shift()();
assert.equal(fixture.animationFrames.length, 0);
for (const clientX of [50, 60, 70]) {
  fixture.dispatchWindow("pointermove", {
    clientX,
    preventDefault() {},
    stopPropagation() {},
  });
}
assert.equal(
  fixture.animationFrames.length,
  1,
  "multiple slider pointer moves must schedule one new coalesced summary frame",
);
assert.equal(
  beforeStatefulRenderSliderInput.value,
  "53",
  "the final slider input value must reflect the last pointer position",
);
fixture.dispatchWindow("pointercancel");
assert.equal(fixture.windowListenerCount("pointermove"), 0);
assert.equal(fixture.windowListenerCount("pointerup"), 0);
assert.equal(fixture.windowListenerCount("pointercancel"), 0);
assert.equal(fixture.windowListenerCount("blur"), 0);
beforeStatefulRenderSlider.emit("pointerdown", {
  pointerId: 18,
  clientX: 45,
});
assert.equal(fixture.windowListenerCount("pointermove"), 1);
assert.equal(fixture.windowListenerCount("pointerup"), 1);
assert.equal(fixture.windowListenerCount("pointercancel"), 1);
assert.equal(fixture.windowListenerCount("blur"), 1);

fixture.runtime.renderPanel(node);
const restoredScroll = panel.querySelector(".easyuse-anima-aio-node-settings-scroll");
const restoredFeed = panel.querySelector("[data-aio-preview-feed]");
const restoredSeed = panel.querySelector("[data-aio-seed-input]");
assert.notEqual(panel.children[0], beforeStatefulRenderMain);
assert.notEqual(restoredScroll, beforeStatefulRenderScroll);
assert.notEqual(restoredSeed, beforeStatefulRenderSeed);
assert.equal(restoredScroll.scrollTop, 137);
assert.equal(restoredScroll.scrollLeft, 11);
assert.notEqual(restoredFeed, beforeStatefulRenderFeed);
assert.equal(restoredFeed.scrollLeft, 29);
assert.equal(fixture.document.activeElement, restoredSeed);
assert.equal(restoredSeed.focused, true);
assert.equal(beforeStatefulRenderSeed.focused, false);
assert.equal(fixture.windowListenerCount("pointermove"), 0);
assert.equal(fixture.windowListenerCount("pointerup"), 0);
assert.equal(fixture.windowListenerCount("pointercancel"), 0);
assert.equal(fixture.windowListenerCount("blur"), 0);
for (const eventName of PANEL_EVENT_NAMES) {
  assert.equal(panel.listenerCount(eventName), 1, eventName + " listener must remain singular");
}

while (fixture.animationFrames.length) {
  fixture.animationFrames.shift()();
}
const tooltipSettingsSnapshot = clone(node.settings);
const tooltipSerializedSnapshot = node.widgets_values;
node.settings.highres.enabled = false;
node.settings.detailer.enabled = false;
node.settings.upscale.enabled = false;
node.settings.postprocess.enabled = false;
fixture.runtime.renderPanel(node);
const disabledStages = panel.querySelector(
  ".easyuse-anima-aio-node-settings-scroll",
).children.slice(1);
assert.equal(disabledStages.length, 4);
assert.equal(
  disabledStages.every((stage) => stage.children[1].children.length === 0),
  true,
  "disabled stages must not reserve body rows for static help notes",
);
assert.equal(
  panel.querySelectorAll(".easyuse-anima-aio-node-stage-note").length,
  0,
  "static disabled guidance must not remain inline",
);
assert.deepEqual(
  disabledStages.map(
    (stage) => stage.children[0].children[0].children[0].getAttribute("data-aio-info-key"),
  ),
  [
    "tip.highresDisabled",
    "tip.detailerDisabled",
    "tip.upscaleDisabled",
    "tip.postprocessDisabled",
  ],
);

node.settings.highres.enabled = true;
node.settings.highres.inherit_sampler_settings = true;
node.settings.sampler.backend = "spectrum_spd_speed";
fixture.runtime.renderPanel(node);
const inlineWarnings = panel.querySelectorAll("[data-aio-inline-warning]");
assert.equal(inlineWarnings.length, 1, "the SPD/SPEED fallback must remain inline");
assert.equal(inlineWarnings[0].textContent, "text:text.highresSpdManualRequired");
assert.equal(inlineWarnings[0].classList.contains("warning"), true);
assert.equal(
  findByAttribute(panel, "data-aio-focus-key", "highres.follow-main.info")
    .getAttribute("data-aio-info-key"),
  "tip.highresFollow",
);

const profileTooltips = fixture.document.querySelectorAll("[data-aio-info-tooltip]");
node.profileValue = "user:Tooltip profile";
fixture.runtime.renderPanel(node);
assert.equal(
  profileTooltips.every((tooltip) => tooltip.parentElement == null),
  true,
  "profile-driven rerender must clean stale tooltip portals",
);
assert.equal(
  panel.querySelectorAll("[data-aio-info-button]").length,
  fixture.document.querySelectorAll("[data-aio-info-tooltip]").length,
  "profile-driven rerender must not duplicate tooltips",
);

node.settings = tooltipSettingsSnapshot;
fixture.runtime.renderPanel(node);
assert.equal(node.widgets_values, tooltipSerializedSnapshot);
assert.deepEqual(node.settings, tooltipSettingsSnapshot);
while (fixture.animationFrames.length) {
  fixture.animationFrames.shift()();
}
const summaryTraceStart = fixture.trace.length;
fixture.runtime.scheduleSummary(node);
fixture.runtime.scheduleSummary(node);
assert.equal(fixture.animationFrames.length, 1, "summary requests must coalesce per frame");
fixture.animationFrames.shift()();
assert.equal(fixture.animationFrames.length, 0);
assert.equal(
  fixture.trace.slice(summaryTraceStart).includes("get-settings"),
  true,
  "scheduled summary must run the normal summary update",
);

fixture.runtime.scheduleLayout(node);
fixture.runtime.scheduleLayout(node);
fixture.runtime.scheduleSummary(node);
fixture.runtime.scheduleSummary(node);
assert.equal(
  fixture.animationFrames.length,
  2,
  "layout and summary must retain independent keyed frame ownership",
);
const pendingFrameIds = fixture.animationFrames
  .map((callback) => callback.__frameId)
  .sort((left, right) => left - right);
const activeDisposeSlider = findByClass(panel, "easyuse-anima-aio-node-slider-track");
const activeDisposeInfo = findByAttribute(panel, "data-aio-focus-key", "highres.info");
activeDisposeInfo.emit("click");
assert.equal(fixture.windowListenerCount("resize"), 1);
assert.equal(fixture.windowListenerCount("scroll", true), 1);
activeDisposeSlider.emit("pointerdown", {
  pointerId: 23,
  clientX: 60,
});
assert.equal(fixture.windowListenerCount("pointermove"), 1);
assert.equal(fixture.windowListenerCount("pointerup"), 1);
assert.equal(fixture.windowListenerCount("pointercancel"), 1);
assert.equal(fixture.windowListenerCount("blur"), 1);

const serializedWidgetValues = node.widgets_values;
const finalPreviewImages = node.__easyuseAnimaGeneratorPreviewImages;
const widgetCleanupError = new Error("injected DOM widget cleanup failure");
panelWidget.onRemoveError = widgetCleanupError;
const canceledBeforeDispose = fixture.canceledAnimationFrames.length;
let observedDisposeError = null;
try {
  fixture.runtime.disposePanel(node);
} catch (error) {
  observedDisposeError = error;
}
assert.equal(
  observedDisposeError == null || observedDisposeError === widgetCleanupError,
  true,
  "dispose may propagate the injected cleanup error only after completing teardown",
);
assert.deepEqual(
  fixture.canceledAnimationFrames
    .slice(canceledBeforeDispose)
    .sort((left, right) => left - right),
  pendingFrameIds,
  "dispose must cancel the exact pending layout and summary frames",
);
assert.equal(fixture.animationFrames.length, 0);
assert.equal(fixture.windowListenerCount("pointermove"), 0);
assert.equal(fixture.windowListenerCount("pointerup"), 0);
assert.equal(fixture.windowListenerCount("pointercancel"), 0);
assert.equal(fixture.windowListenerCount("blur"), 0);
assert.equal(fixture.windowListenerCount("resize"), 0);
assert.equal(fixture.windowListenerCount("scroll"), 0);
for (const eventName of PANEL_EVENT_NAMES) {
  assert.equal(panel.listenerCount(eventName), 0, eventName + " listener must be disposed");
}
assert.equal(panel.parentElement, null);
assert.equal(panel.removed, true);
assert.equal(Object.hasOwn(node, "__easyuseAnimaGeneratorPanelEl"), false);
assert.equal(Object.hasOwn(node, "__easyuseAnimaGeneratorPanelWidget"), false);
assert.equal(node.widgets.length, 0);
assert.equal(panelWidget.onRemoveCalls, 1);
assert.equal(fixture.domWidgetStore.size, 0);
assert.equal(fixture.domWidgetStore.has(panelWidget), false);
assert.equal(
  fixture.document.querySelectorAll("[data-aio-info-tooltip]").length,
  0,
  "dispose must remove every tooltip portal",
);
assert.equal(node.widgets_values, serializedWidgetValues);
assert.equal(node.__easyuseAnimaGeneratorPreviewImages, finalPreviewImages);

const styleAfterDispose = {
  width: panel.style.width,
  maxWidth: panel.style.maxWidth,
  height: panel.style.getPropertyValue("height"),
  maxHeight: panel.style.getPropertyValue("max-height"),
};
const childrenAfterDispose = panel.children.length;
const forwardWheelBeforeStale = fixture.trace.filter(
  (value) => value === "forward-wheel",
).length;
panel.emit("wheel", { target: panel });
assert.equal(
  fixture.trace.filter((value) => value === "forward-wheel").length,
  forwardWheelBeforeStale,
  "disposed delegated listeners must stay inert",
);

const canceledBeforeSecondDispose = fixture.canceledAnimationFrames.length;
fixture.runtime.disposePanel(node);
fixture.runtime.scheduleLayout(node);
fixture.runtime.scheduleSummary(node);
assert.equal(fixture.canceledAnimationFrames.length, canceledBeforeSecondDispose);
assert.equal(fixture.animationFrames.length, 0);
assert.equal(fixture.windowListenerCount("pointermove"), 0);
assert.equal(fixture.windowListenerCount("pointerup"), 0);
assert.equal(fixture.windowListenerCount("pointercancel"), 0);
assert.equal(fixture.windowListenerCount("blur"), 0);
assert.equal(panelWidget.onRemoveCalls, 1);
assert.equal(fixture.domWidgetStore.size, 0);

const widgetCallsBeforeReactivate = widgetCalls.length;
fixture.runtime.ensurePanel(node);
const reactivatedLifecycle = fixture.runtime.activatePanel(node);
assert.notEqual(reactivatedLifecycle, initialPanelLifecycle);
assert.equal(fixture.runtime.activatePanel(node), reactivatedLifecycle);
const reactivatedPanel = node.__easyuseAnimaGeneratorPanelEl;
assert.notEqual(reactivatedPanel, panel);
assert.equal(reactivatedPanel.parentElement, fixture.document.body);
assert.equal(widgetCalls.length, widgetCallsBeforeReactivate + 1);
assert.equal(node.widgets.length, 1);
const reactivatedWidget = widgetCalls.at(-1);
assert.notEqual(reactivatedWidget, panelWidget);
assert.equal(reactivatedWidget.onRemoveCalls, 0);
assert.equal(fixture.domWidgetStore.size, 1);
assert.equal(fixture.domWidgetStore.has(reactivatedWidget), true);
assert.equal(fixture.domWidgetStore.has(panelWidget), false);
assert.equal(
  fixture.document.body.querySelectorAll(".easyuse-anima-aio-node-panel").length,
  1,
);
assert.equal(node.widgets_values, serializedWidgetValues);
assert.equal(node.__easyuseAnimaGeneratorPreviewImages, finalPreviewImages);
for (const eventName of PANEL_EVENT_NAMES) {
  assert.equal(
    reactivatedPanel.listenerCount(eventName),
    1,
    eventName + " listener must reactivate exactly once",
  );
  assert.equal(
    reactivatedPanel.listenerCount(eventName, eventName === "wheel"),
    1,
    eventName + " listener must reactivate with the expected capture flag",
  );
}
assert.equal(fixture.animationFrames.length, 1, "reactivation must restore layout scheduling");
const reactivatedMain = reactivatedPanel.children[0];
const reactivatedPreview = reactivatedPanel
  .querySelector("[data-aio-preview-box]")
  .children[0];
const reactivatedFrameIds = fixture.animationFrames.map((callback) => callback.__frameId);
const traceBeforeStaleGeneration = fixture.trace.length;
const dirtyBeforeStaleGeneration = node.dirtyCount || 0;
fixture.runStaleAnimationFrames();
assert.equal(reactivatedPanel.children[0], reactivatedMain);
assert.equal(
  reactivatedPanel.querySelector("[data-aio-preview-box]").children[0],
  reactivatedPreview,
);
assert.deepEqual(
  fixture.animationFrames.map((callback) => callback.__frameId),
  reactivatedFrameIds,
  "callbacks canceled by the old lifecycle must not consume the new layout frame",
);
assert.equal(fixture.trace.length, traceBeforeStaleGeneration);
assert.equal(node.dirtyCount || 0, dirtyBeforeStaleGeneration);
assert.deepEqual({
  width: panel.style.width,
  maxWidth: panel.style.maxWidth,
  height: panel.style.getPropertyValue("height"),
  maxHeight: panel.style.getPropertyValue("max-height"),
}, styleAfterDispose);
assert.equal(panel.children.length, childrenAfterDispose);

fixture.runtime.renderPanel(node, initialPanelLifecycle);
assert.equal(
  reactivatedPanel.children[0],
  reactivatedMain,
  "a continuation holding the old lifecycle token must not rerender the new panel",
);
assert.deepEqual(
  fixture.animationFrames.map((callback) => callback.__frameId),
  reactivatedFrameIds,
);
fixture.animationFrames.shift()();
assert.equal(reactivatedPanel.style.width, "600px");
assert.equal(
  reactivatedPanel.querySelector("[data-aio-preview-box]").children[0].className,
  "easyuse-anima-aio-node-preview-placeholder",
);
assert.equal(findByClass(reactivatedPanel, "easyuse-anima-aio-node-main") != null, true);
console.log("AiO generator panel runtime smoke passed.");
