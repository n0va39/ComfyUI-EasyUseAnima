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

function findAll(root, predicate) {
  return [root, ...descendants(root)].filter(predicate);
}

function findByText(root, textContent) {
  return find(root, (element) => element.textContent === textContent);
}

function sectionByHeading(dialog, heading) {
  const title = findByText(dialog.body, `static:${heading}`);
  assert.ok(title?.parentElement, `missing section: ${heading}`);
  return title.parentElement;
}

function rowByLabel(root, label, index = 0) {
  return findAll(root, (element) => element.getAttribute?.("data-test-label") === label)[index] || null;
}

function controlIn(root, label, index = 0) {
  const row = rowByLabel(root, label, index);
  assert.ok(row, `missing field row: ${label}[${index}]`);
  assert.ok(row.children[0], `missing field control: ${label}[${index}]`);
  return row.children[0];
}

function action(dialog, key) {
  const button = findByText(dialog.actions, `text:${key}`);
  assert.ok(button, `missing action: ${key}`);
  return button;
}

function warningIn(dialog) {
  const warning = find(dialog.body, (element) => element.classList.contains("easyuse-anima-aio-warning"));
  assert.ok(warning, "missing dependency warning");
  return warning;
}

function setSelectValue(select, value) {
  select.value = String(value);
  for (const option of select.options || []) {
    option.selected = option.value === select.value;
  }
}

function assertBackendVisibility(dialog, backendValue) {
  const spectrum = sectionByHeading(dialog, "Spectrum Patch / Advanced Sampler");
  const spd = sectionByHeading(dialog, "Spectrum + SPD / SPEED");
  const modGuidance = sectionByHeading(dialog, "Mod Guidance");
  const modAdvanced = rowByLabel(modGuidance, "Adapter")?.parentElement;
  assert.ok(modAdvanced, "missing Mod Guidance advanced container");
  const isComfy = backendValue === "comfy_ksampler";
  const isAdvanced = backendValue === "spectrum_mod_guidance_advanced";
  assert.equal(spectrum.classList.contains("hidden"), !(isComfy || isAdvanced));
  assert.equal(rowByLabel(spectrum, "Use Spectrum patch").style.display, isComfy ? "" : "none");
  assert.equal(rowByLabel(spectrum, "Compat policy").style.display, isComfy ? "" : "none");
  assert.equal(modAdvanced.style.display, isAdvanced ? "" : "none");
  assert.equal(spd.classList.contains("hidden"), backendValue !== "spectrum_spd_speed");
}

async function flushPromises() {
  await Promise.resolve();
  await Promise.resolve();
}

const samplerDialogModule = await import(dataModule("../web/js/aio/sampler_settings_dialog.js"));
const settingsModule = await import(dataModule("../web/js/aio/settings.js"));
assert.deepEqual(
  Object.keys(samplerDialogModule),
  ["aioCreateSamplerSettingsDialog"],
  "Sampler settings dialog must expose only its lifecycle factory",
);

function createFixture({
  settings = {},
  available = {},
  loaded = true,
  nodeInputs = {},
  supported = {},
  deferLoads = false,
} = {}) {
  let dependencyCalls = 0;
  let currentDialog = null;
  const trace = [];
  const dialogs = [];
  const loadCalls = [];
  const loadResolvers = [];
  const parseCalls = [];
  const mergeVisibleCalls = [];
  const optionCalls = [];
  const supportedCalls = [];
  const writes = [];
  const renders = [];
  const applyVisibleCalls = [];
  const document = createFakeDocument();
  const availabilityState = { ...available };
  const supportedState = clone(supported);
  const nodeInputMaps = clone(nodeInputs);
  const dependencyState = { loaded: !!loaded };
  const defaultSettings = clone(settingsModule.AIO_DEFAULT_GENERATION_SETTINGS);
  const node = {
    settings: settingsModule.aioMergeDefaults(defaultSettings, settings),
    visible: {},
    widgets: [{ name: "generation_settings", value: "" }],
  };
  node.widgets[0].value = JSON.stringify(node.settings);

  function createDialog(title, subtitle) {
    dependencyCalls += 1;
    const dialog = {
      title,
      subtitle,
      backdrop: document.createElement("div"),
      body: document.createElement("div"),
      actions: document.createElement("div"),
      trace: [],
    };
    dialog.backdrop.remove = () => {
      dialog.backdrop.removed = true;
      dialog.trace.push("remove");
      trace.push("remove");
    };
    dialogs.push(dialog);
    currentDialog = dialog;
    return dialog;
  }

  function field(section, label, element, tooltipKey = "") {
    dependencyCalls += 1;
    const row = document.createElement("label");
    row.className = "easyuse-anima-aio-field";
    row.setAttribute("data-test-label", label);
    row.setAttribute("data-test-tooltip", tooltipKey);
    row.append(element);
    section.append(row);
    return element;
  }

  function numberInput(value, step = "1") {
    dependencyCalls += 1;
    const input = document.createElement("input");
    input.type = "number";
    input.step = step;
    input.value = String(value ?? "");
    return input;
  }

  function textInput(value) {
    dependencyCalls += 1;
    const input = document.createElement("input");
    input.type = "text";
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
    select.options = [];
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
      select.options.push(option);
      select.append(option);
    }
    if (!select.options.some((option) => option.selected)) {
      select.value = String(value ?? "");
    }
    return select;
  }

  function nodeInputControlForSpec(spec, current) {
    dependencyCalls += 1;
    if (!Array.isArray(spec)) {
      return null;
    }
    const type = spec[0];
    const options = spec[1] && typeof spec[1] === "object" ? spec[1] : {};
    const value = current ?? (Object.hasOwn(options, "default") ? options.default : undefined);
    if (Array.isArray(type)) {
      return selectInput(type, value ?? type[0] ?? "");
    }
    const normalized = String(type || "").toUpperCase();
    if (normalized === "BOOLEAN") {
      return checkbox(value ?? false);
    }
    if (normalized === "INT") {
      return numberInput(value ?? 0, "1");
    }
    if (normalized === "FLOAT") {
      return numberInput(value ?? 0, "0.01");
    }
    if (normalized === "STRING") {
      return textInput(value ?? "");
    }
    return null;
  }

  function valueFromNodeInputControl(control) {
    dependencyCalls += 1;
    if (!control) {
      return null;
    }
    if (control.type === "checkbox") {
      return !!control.checked;
    }
    if (control.type === "number") {
      return Number(control.value || 0);
    }
    return control.value;
  }

  function staticText(value) {
    dependencyCalls += 1;
    return `static:${value}`;
  }

  function text(key) {
    dependencyCalls += 1;
    return `text:${key}`;
  }

  function format(key, values = {}) {
    dependencyCalls += 1;
    return `format:${key}:${JSON.stringify(values)}`;
  }

  function applyTooltipText(element, value) {
    dependencyCalls += 1;
    element.title = String(value || "");
    return element;
  }

  function mergeDefaults(defaults, current) {
    dependencyCalls += 1;
    currentDialog?.trace.push("merge");
    return settingsModule.aioMergeDefaults(defaults, current);
  }

  function clampNumber(value, fallback, min, max) {
    dependencyCalls += 1;
    const parsed = Number(value);
    const next = Number.isFinite(parsed) ? parsed : fallback;
    return Math.max(min, Math.min(max, next));
  }

  function findWidget(targetNode, name) {
    dependencyCalls += 1;
    return targetNode.widgets?.find((widget) => widget.name === name);
  }

  function parseSettings(widget, defaults) {
    dependencyCalls += 1;
    parseCalls.push({ widget, defaults });
    let current = {};
    try {
      current = JSON.parse(widget?.value || "{}");
    } catch (_error) {
      current = {};
    }
    return settingsModule.aioMergeDefaults(defaults, current);
  }

  function mergeVisibleSettings(targetNode, parsed) {
    dependencyCalls += 1;
    mergeVisibleCalls.push({ node: targetNode, parsed: clone(parsed) });
    const next = clone(parsed);
    Object.assign(next.sampler, targetNode.visible || {});
    return next;
  }

  function widgetOptions(_targetNode, name, fallback) {
    dependencyCalls += 1;
    optionCalls.push(name);
    return [...new Set([...fallback, name === "sampler_name" ? "custom_sampler" : "custom_scheduler"])];
  }

  function applyVisibleSettings(targetNode, nextSettings) {
    dependencyCalls += 1;
    const snapshot = clone(nextSettings);
    targetNode.visible = {
      seed: snapshot.sampler.seed,
      steps: snapshot.sampler.steps,
      cfg: snapshot.sampler.cfg,
      sampler_name: snapshot.sampler.sampler_name,
      scheduler: snapshot.sampler.scheduler,
      denoise: snapshot.sampler.denoise,
    };
    applyVisibleCalls.push(snapshot);
    currentDialog.trace.push("apply-visible");
    trace.push("apply-visible");
  }

  function writeSettings(targetNode, widget, nextSettings) {
    dependencyCalls += 1;
    const snapshot = clone(nextSettings);
    targetNode.settings = snapshot;
    widget.value = JSON.stringify(snapshot);
    writes.push(snapshot);
    currentDialog.trace.push("write");
    trace.push("write");
  }

  function renderPanel(targetNode) {
    dependencyCalls += 1;
    renders.push(targetNode);
    currentDialog.trace.push("render");
    trace.push("render");
  }

  const openSamplerSettings = samplerDialogModule.aioCreateSamplerSettingsDialog({
    document,
    controls: {
      createDialog,
      field,
      numberInput,
      selectInput,
      checkbox,
      textInput,
      nodeInputControlForSpec,
      valueFromNodeInputControl,
    },
    text: {
      staticText,
      get: text,
      format,
      applyTooltipText,
    },
    settingsCore: {
      defaultGenerationSettings: defaultSettings,
      seedControls: settingsModule.AIO_GENERATOR_SEED_CONTROLS,
      specialSeedRandom: settingsModule.AIO_GENERATOR_SPECIAL_SEED_RANDOM,
      fallbackSamplerNames: ["euler", "er_sde"],
      fallbackSchedulerNames: ["simple", "sgm_uniform"],
      mergeDefaults,
      normalizeSeedControl: settingsModule.aioNormalizeSeedControl,
      normalizeSeedValue: settingsModule.aioNormalizeSeedValue,
      clampNumber,
    },
    nodeAdapter: {
      generatorSettingsWidget: "generation_settings",
      findWidget,
      parseSettings,
      mergeVisibleSettings,
      widgetOptions,
      applyVisibleSettings,
      writeSettings,
      renderPanel,
    },
    dependencyAdapter: {
      backendDependencies: {
        spectrum_mod_guidance_advanced: "spectrumAdvanced",
        spectrum_spd_speed: "spectrumSpd",
      },
      isLoaded() {
        dependencyCalls += 1;
        return dependencyState.loaded;
      },
      available(key) {
        dependencyCalls += 1;
        return Object.hasOwn(availabilityState, key) ? !!availabilityState[key] : true;
      },
      pack(key) {
        dependencyCalls += 1;
        return `pack:${key}`;
      },
      nodeInputMap(key) {
        dependencyCalls += 1;
        return nodeInputMaps[key] || {};
      },
      nodeInputTooltip(key, inputName) {
        dependencyCalls += 1;
        const spec = nodeInputMaps[key]?.[inputName];
        const options = Array.isArray(spec) && spec[1] && typeof spec[1] === "object" ? spec[1] : {};
        return String(options.tooltip || `tooltip:${key}:${inputName}`);
      },
      nodeInputSupported(key, inputName) {
        dependencyCalls += 1;
        supportedCalls.push({ key, inputName });
        if (Object.hasOwn(supportedState[key] || {}, inputName)) {
          return !!supportedState[key][inputName];
        }
        return !Object.hasOwn(availabilityState, key) || !!availabilityState[key];
      },
      load(options) {
        dependencyCalls += 1;
        loadCalls.push(options);
        if (!deferLoads) {
          return Promise.resolve(dependencyState);
        }
        return new Promise((resolve) => loadResolvers.push(resolve));
      },
    },
  });

  return {
    openSamplerSettings,
    document,
    node,
    defaultSettings,
    dialogs,
    loadCalls,
    parseCalls,
    mergeVisibleCalls,
    optionCalls,
    supportedCalls,
    writes,
    renders,
    applyVisibleCalls,
    trace,
    availabilityState,
    dependencyState,
    nodeInputMaps,
    dependencyCallCount: () => dependencyCalls,
    resolveLoads() {
      for (const resolve of loadResolvers.splice(0)) {
        resolve(dependencyState);
      }
    },
  };
}

{
  const fixture = createFixture({
    deferLoads: true,
    settings: {
      sampler: {
        backend: "spectrum_mod_guidance_advanced",
        seed: 1234,
        seed_after_generate: "increment",
        steps: 47,
        cfg: 6.5,
        sampler_name: "custom_sampler",
        scheduler: "custom_scheduler",
        denoise: 0.55,
        spectrum: {
          enabled: false,
          window_size: 2.75,
          compat_policy: "strict",
        },
        spectrum_extra: {
          future_gain: 1.25,
          future_mode: "quality",
        },
        spd_extra: {
          future_flag: true,
        },
      },
      mod_guidance: {
        mode: "enabled",
        profile: "uniform_w3",
        advanced: {
          adapter: "custom-adapter.safetensors",
          mod_w: 4.5,
        },
      },
      preserved_root_key: "cancel-keep-root",
    },
    nodeInputs: {
      spectrumAdvanced: {
        window_size: ["FLOAT", { default: 2 }],
        future_gain: ["FLOAT", { default: 1, tooltip: "Future gain" }],
        future_mode: [["speed", "quality"], { default: "speed" }],
      },
      spectrumSpd: {
        spd_scale: ["FLOAT", { default: 0.5 }],
        future_flag: ["BOOLEAN", { default: false }],
      },
    },
  });
  const originalSettings = clone(fixture.node.settings);
  const originalWidget = fixture.node.widgets[0].value;
  assert.equal(fixture.dependencyCallCount(), 0, "Factory composition must be side-effect free");
  assert.equal(fixture.dialogs.length, 0);
  assert.equal(fixture.loadCalls.length, 0);
  assert.equal(fixture.writes.length, 0);
  assert.equal(fixture.renders.length, 0);
  assert.equal(fixture.applyVisibleCalls.length, 0);
  assert.equal(fixture.document.createdElements.length, 0, "Factory composition must not create DOM elements");
  assert.equal(fixture.document.body.children.length, 0, "Factory composition must not attach DOM elements");

  fixture.openSamplerSettings(fixture.node);
  const dialog = fixture.dialogs[0];
  assert.equal(dialog.title, "Sampler Details");
  assert.equal(
    dialog.subtitle,
    "Choose one of three sampler paths. Missing optional node packs are locked before queue execution.",
  );
  const base = sectionByHeading(dialog, "Base Parameters");
  const sampler = sectionByHeading(dialog, "Sampler Backend");
  const modGuidance = sectionByHeading(dialog, "Mod Guidance");
  const spectrum = sectionByHeading(dialog, "Spectrum Patch / Advanced Sampler");
  assert.equal(controlIn(base, "Seed").value, "1234");
  assert.equal(controlIn(base, "Seed mode").value, "increment");
  assert.equal(controlIn(base, "Steps").value, "47");
  assert.equal(controlIn(base, "CFG").value, "6.5");
  assert.equal(controlIn(base, "Denoise").value, "0.55");
  assert.equal(controlIn(sampler, "Mode").value, "spectrum_mod_guidance_advanced");
  assert.equal(controlIn(sampler, "Sampler").value, "custom_sampler");
  assert.equal(controlIn(sampler, "Scheduler").value, "custom_scheduler");
  assert.equal(controlIn(modGuidance, "Mode").value, "enabled");
  assert.equal(controlIn(modGuidance, "Profile").value, "uniform_w3");
  assert.equal(controlIn(modGuidance, "Adapter").value, "custom-adapter.safetensors");
  assert.equal(controlIn(modGuidance, "Mod W").value, "4.5");
  assert.equal(controlIn(spectrum, "Window size").value, "2.75");
  assert.equal(controlIn(spectrum, "Compat policy").value, "strict");
  assertBackendVisibility(dialog, "spectrum_mod_guidance_advanced");
  assert.deepEqual(new Set(fixture.optionCalls), new Set(["sampler_name", "scheduler"]));
  assert.equal(fixture.loadCalls.length, 3, "Two dynamic editors and dependency locks must refresh asynchronously");

  let dynamicSpectrum = sectionByHeading(dialog, "Detected Spectrum Inputs");
  assert.equal(dynamicSpectrum.classList.contains("hidden"), false);
  assert.equal(rowByLabel(dynamicSpectrum, "window_size"), null, "Known inputs must not be duplicated dynamically");
  assert.equal(controlIn(dynamicSpectrum, "future_gain").value, "1.25");
  assert.equal(controlIn(dynamicSpectrum, "future_mode").value, "quality");
  controlIn(dynamicSpectrum, "future_gain").value = "2.75";
  fixture.resolveLoads();
  await flushPromises();
  dynamicSpectrum = sectionByHeading(dialog, "Detected Spectrum Inputs");
  assert.equal(
    controlIn(dynamicSpectrum, "future_gain").value,
    "2.75",
    "Async dynamic-editor rerender must preserve an in-progress control value",
  );

  const backend = controlIn(sampler, "Mode");
  setSelectValue(backend, "spectrum_spd_speed");
  backend.emit("change");
  assertBackendVisibility(dialog, "spectrum_spd_speed");
  const dynamicSpd = sectionByHeading(dialog, "Detected SPD Inputs");
  assert.equal(rowByLabel(dynamicSpd, "spd_scale"), null, "Known SPD inputs must not be duplicated dynamically");
  assert.equal(controlIn(dynamicSpd, "future_flag").checked, true);
  controlIn(dynamicSpd, "future_flag").checked = false;
  controlIn(base, "Seed").value = "999";
  action(dialog, "button.cancel").emit("click");
  assert.deepEqual(fixture.node.settings, originalSettings, "Cancel must not mutate Sampler settings");
  assert.equal(fixture.node.widgets[0].value, originalWidget, "Cancel must not rewrite the hidden widget");
  assert.equal(fixture.writes.length, 0);
  assert.equal(fixture.renders.length, 0);
  assert.equal(fixture.applyVisibleCalls.length, 0);
  assert.deepEqual(dialog.trace, ["remove"]);
}

for (const testCase of [
  {
    name: "advanced forces Spectrum",
    backend: "spectrum_mod_guidance_advanced",
    checked: false,
    patchAvailable: true,
    expected: true,
  },
  {
    name: "Comfy enables available Spectrum patch",
    backend: "comfy_ksampler",
    checked: true,
    patchAvailable: true,
    expected: true,
  },
  {
    name: "Comfy disables missing Spectrum patch",
    backend: "comfy_ksampler",
    checked: true,
    patchAvailable: false,
    expected: false,
  },
  {
    name: "SPD does not serialize Spectrum patch",
    backend: "spectrum_spd_speed",
    checked: true,
    patchAvailable: true,
    expected: false,
  },
]) {
  const fixture = createFixture({
    available: {
      spectrumAdvanced: true,
      spectrumSpd: true,
      spectrumPatch: testCase.patchAvailable,
    },
    settings: {
      sampler: {
        backend: testCase.backend,
        spectrum: { enabled: testCase.checked },
      },
    },
  });
  fixture.openSamplerSettings(fixture.node);
  await flushPromises();
  const dialog = fixture.dialogs[0];
  assertBackendVisibility(dialog, testCase.backend);
  action(dialog, "button.apply").emit("click");
  assert.equal(fixture.node.settings.sampler.spectrum.enabled, testCase.expected, testCase.name);
  assert.deepEqual(dialog.trace.slice(-5), ["merge", "apply-visible", "write", "render", "remove"]);
  assert.equal(fixture.writes.length, 1);
  assert.equal(fixture.renders.length, 1);
  assert.equal(fixture.applyVisibleCalls.length, 1);
}

{
  const fixture = createFixture({
    loaded: false,
    deferLoads: true,
    settings: {
      sampler: {
        spectrum_extra: {
          future_gain: 1.5,
          future_mode: "quality",
        },
        spd_extra: {
          future_flag: true,
        },
      },
    },
    nodeInputs: {
      spectrumAdvanced: {
        future_gain: ["FLOAT", { default: 1 }],
        future_mode: [["speed", "quality"], { default: "speed" }],
      },
      spectrumSpd: {
        future_flag: ["BOOLEAN", { default: false }],
      },
    },
  });
  fixture.openSamplerSettings(fixture.node);
  const dialog = fixture.dialogs[0];
  assert.equal(sectionByHeading(dialog, "Detected Spectrum Inputs").classList.contains("hidden"), true);
  assert.equal(sectionByHeading(dialog, "Detected SPD Inputs").classList.contains("hidden"), true);

  action(dialog, "button.apply").emit("click");

  assert.deepEqual(
    fixture.node.settings.sampler.spectrum_extra,
    { future_gain: 1.5, future_mode: "quality" },
    "Fast Apply before optional dependency discovery must preserve Spectrum extras",
  );
  assert.deepEqual(
    fixture.node.settings.sampler.spd_extra,
    { future_flag: true },
    "Fast Apply before optional dependency discovery must preserve SPD extras",
  );
  assert.deepEqual(dialog.trace.slice(-5), ["merge", "apply-visible", "write", "render", "remove"]);
}

{
  const fixture = createFixture({
    loaded: false,
    deferLoads: true,
    settings: {
      sampler: {
        spectrum_extra: ["invalid"],
        spd_extra: "invalid",
      },
    },
  });
  fixture.openSamplerSettings(fixture.node);
  const dialog = fixture.dialogs[0];

  action(dialog, "button.apply").emit("click");

  assert.deepEqual(
    fixture.node.settings.sampler.spectrum_extra,
    {},
    "Malformed Spectrum extras must not be serialized as numeric array keys",
  );
  assert.deepEqual(
    fixture.node.settings.sampler.spd_extra,
    {},
    "Malformed SPD extras must not be serialized as numeric string keys",
  );
}

{
  const fixture = createFixture({
    available: { spectrumAdvanced: true },
    settings: {
      sampler: {
        spectrum_extra: Object.fromEntries([
          ["constructor", 2.5],
          ["toString", "quality"],
        ]),
      },
    },
    nodeInputs: {
      spectrumAdvanced: Object.fromEntries([
        ["constructor", ["FLOAT", { default: 1 }]],
        ["toString", [["speed", "quality"], { default: "speed" }]],
        ["__proto__", ["BOOLEAN", { default: true }]],
      ]),
    },
  });
  fixture.openSamplerSettings(fixture.node);
  const dialog = fixture.dialogs[0];
  const dynamicSpectrum = sectionByHeading(dialog, "Detected Spectrum Inputs");
  assert.equal(controlIn(dynamicSpectrum, "constructor").value, "2.5");
  assert.equal(controlIn(dynamicSpectrum, "toString").value, "quality");
  assert.equal(controlIn(dynamicSpectrum, "__proto__").checked, true);

  controlIn(dynamicSpectrum, "constructor").value = "3.5";
  setSelectValue(controlIn(dynamicSpectrum, "toString"), "speed");
  controlIn(dynamicSpectrum, "__proto__").checked = false;
  action(dialog, "button.apply").emit("click");

  assert.deepEqual(
    fixture.node.settings.sampler.spectrum_extra,
    Object.fromEntries([
      ["constructor", 3.5],
      ["toString", "speed"],
      ["__proto__", false],
    ]),
    "Dynamic input values must retain own-key semantics for Object prototype names",
  );
}

{
  const fixture = createFixture({
    loaded: false,
    deferLoads: true,
    available: {
      spectrumAdvanced: true,
      spectrumSpd: true,
      spectrumPatch: true,
      spectrumCorrections: true,
    },
    settings: {
      sampler: {
        backend: "spectrum_mod_guidance_advanced",
        spectrum: { enabled: true },
        dit_corrections: { enabled: true },
        spectrum_extra: {
          future_gain: 1.5,
          retired_spectrum_input: "tracked-separately",
        },
        spd_extra: {
          future_variant: "single",
          future_strength: 1.25,
          retired_spd_input: "preserve-unrendered",
          unsupported_image: "opaque-image-ref",
        },
        dave: { legacy: true },
        preserved_sampler_key: "keep-sampler",
      },
      preserved_root_key: "keep-root",
    },
  });
  fixture.openSamplerSettings(fixture.node);
  const dialog = fixture.dialogs[0];
  const base = sectionByHeading(dialog, "Base Parameters");
  const sampler = sectionByHeading(dialog, "Sampler Backend");
  const modGuidance = sectionByHeading(dialog, "Mod Guidance");
  const spectrum = sectionByHeading(dialog, "Spectrum Patch / Advanced Sampler");
  const corrections = sectionByHeading(dialog, "Spectrum Advanced Corrections");
  const spd = sectionByHeading(dialog, "Spectrum + SPD / SPEED");
  const backend = controlIn(sampler, "Mode");
  const advancedOption = backend.options.find((option) => option.value === "spectrum_mod_guidance_advanced");
  assert.equal(backend.value, "spectrum_mod_guidance_advanced");
  assert.equal(advancedOption.disabled, false);
  assert.equal(controlIn(spectrum, "Use Spectrum patch").checked, true);
  assert.equal(controlIn(corrections, "Use corrections").checked, true);
  assert.equal(sectionByHeading(dialog, "Detected Spectrum Inputs").classList.contains("hidden"), true);
  assert.equal(sectionByHeading(dialog, "Detected SPD Inputs").classList.contains("hidden"), true);

  fixture.availabilityState.spectrumAdvanced = false;
  fixture.availabilityState.spectrumPatch = false;
  fixture.dependencyState.loaded = true;
  fixture.nodeInputMaps.spectrumAdvanced = {
    window_size: ["FLOAT", { default: 2 }],
    future_gain: ["FLOAT", { default: 1, tooltip: "Future gain" }],
  };
  fixture.nodeInputMaps.spectrumSpd = {
    spd_scale: ["FLOAT", { default: 0.5 }],
    future_variant: [["single", "dual"], { default: "single", tooltip: "Future variant" }],
    future_strength: ["FLOAT", { default: 1, tooltip: "Future strength" }],
    unsupported_image: ["IMAGE"],
  };
  fixture.resolveLoads();
  await flushPromises();

  assert.equal(advancedOption.disabled, true);
  assert.equal(advancedOption.textContent, "spectrum_mod_guidance_advanced (pack:spectrumAdvanced missing)");
  assert.equal(backend.value, "comfy_ksampler", "Missing selected backend must fall back to Comfy KSampler");
  assert.equal(controlIn(spectrum, "Use Spectrum patch").disabled, true);
  assert.equal(controlIn(spectrum, "Use Spectrum patch").checked, false);
  assert.equal(controlIn(corrections, "Use corrections").disabled, true);
  assert.equal(controlIn(corrections, "Use corrections").checked, false);
  assert.equal(
    warningIn(dialog).textContent,
    'format:warning.optionalDependencyMissing:{"backend":"spectrum_mod_guidance_advanced","pack":"pack:spectrumAdvanced"} '
      + 'format:warning.optionalDependencyMissing:{"backend":"Spectrum Patch","pack":"pack:spectrumPatch"}',
  );
  assertBackendVisibility(dialog, "comfy_ksampler");
  const latestInputInfo = fixture.supportedCalls.slice(-17);
  assert.deepEqual(
    latestInputInfo.slice(0, 7).map(({ key }) => key),
    Array(7).fill("spectrumPatch"),
    "Comfy Spectrum controls must use Spectrum patch capabilities",
  );
  assert.deepEqual(
    latestInputInfo.slice(7, 14).map(({ key }) => key),
    Array(7).fill("spectrumCorrections"),
    "Comfy correction controls must use correction capabilities",
  );
  assert.deepEqual(
    latestInputInfo.slice(14).map(({ key }) => key),
    Array(3).fill("spectrumSpd"),
    "SPD controls must keep SPD capability metadata",
  );

  const dynamicSpd = sectionByHeading(dialog, "Detected SPD Inputs");
  assert.equal(dynamicSpd.classList.contains("hidden"), false);
  assert.equal(rowByLabel(dynamicSpd, "spd_scale"), null);
  assert.equal(rowByLabel(dynamicSpd, "unsupported_image"), null);
  assert.equal(controlIn(dynamicSpd, "future_variant").value, "single");
  assert.equal(controlIn(dynamicSpd, "future_strength").value, "1.25");

  setSelectValue(backend, "spectrum_spd_speed");
  backend.emit("change");
  assertBackendVisibility(dialog, "spectrum_spd_speed");
  assert.equal(warningIn(dialog).hidden, true, "Unselected missing dependencies must not keep a warning visible");

  controlIn(base, "Seed").value = String(settingsModule.AIO_GENERATOR_MAX_SEED + 100);
  setSelectValue(controlIn(base, "Seed mode"), "");
  controlIn(base, "Steps").value = "0";
  controlIn(base, "CFG").value = "99";
  controlIn(base, "Denoise").value = "-1";
  setSelectValue(controlIn(sampler, "Sampler"), "");
  setSelectValue(controlIn(sampler, "Scheduler"), "");
  controlIn(spd, "Scale").value = "0";
  controlIn(spd, "Sigma").value = "";
  controlIn(spd, "SMC alpha").value = "0.4";
  setSelectValue(controlIn(modGuidance, "Mode"), "");
  setSelectValue(controlIn(modGuidance, "Profile"), "");
  controlIn(modGuidance, "Adapter").value = "";
  controlIn(modGuidance, "Mod W").value = "";
  setSelectValue(controlIn(dynamicSpd, "future_variant"), "dual");
  controlIn(dynamicSpd, "future_strength").value = "2.5";

  action(dialog, "button.apply").emit("click");
  assert.deepEqual(dialog.trace.slice(-5), ["merge", "apply-visible", "write", "render", "remove"]);
  assert.equal(fixture.writes.length, 1);
  assert.equal(fixture.renders.length, 1);
  assert.equal(fixture.applyVisibleCalls.length, 1);
  const written = fixture.node.settings;
  assert.equal(written.sampler.backend, "spectrum_spd_speed");
  assert.equal(written.sampler.seed, settingsModule.AIO_GENERATOR_MAX_SEED);
  assert.equal(written.sampler.seed_after_generate, "fixed");
  assert.equal(written.sampler.steps, 1);
  assert.equal(written.sampler.cfg, 10);
  assert.equal(written.sampler.denoise, 0);
  assert.equal(written.sampler.sampler_name, fixture.defaultSettings.sampler.sampler_name);
  assert.equal(written.sampler.scheduler, fixture.defaultSettings.sampler.scheduler);
  assert.equal(written.sampler.spectrum.enabled, false);
  assert.equal(written.sampler.dit_corrections.enabled, false);
  assert.equal(written.sampler.spd.scale, 0);
  assert.equal(written.sampler.spd.sigma, 0.7);
  assert.equal(written.sampler.spd.adaptive_smc_alpha, 0.4);
  assert.equal(written.mod_guidance.mode, "prompt_data");
  assert.equal(written.mod_guidance.profile, "step_i8_skip27");
  assert.equal(written.mod_guidance.advanced.adapter, "(auto-download default)");
  assert.equal(written.mod_guidance.advanced.mod_w, 3);
  assert.equal(Object.hasOwn(written.sampler, "dave"), false);
  assert.equal(written.sampler.preserved_sampler_key, "keep-sampler");
  assert.equal(written.preserved_root_key, "keep-root");
  assert.deepEqual(
    written.sampler.spectrum_extra,
    {
      future_gain: 1.5,
      retired_spectrum_input: "tracked-separately",
    },
    "Unavailable dynamic Spectrum controls must preserve existing extra values",
  );
  assert.deepEqual(written.sampler.spd_extra, {
    future_variant: "dual",
    future_strength: 2.5,
    retired_spd_input: "preserve-unrendered",
    unsupported_image: "opaque-image-ref",
  });
  assert.deepEqual(JSON.parse(fixture.node.widgets[0].value), written);
  assert.equal(fixture.applyVisibleCalls[0].sampler.seed, settingsModule.AIO_GENERATOR_MAX_SEED);
  assert.equal(fixture.node.visible.steps, 1);
  assert.equal(fixture.node.visible.cfg, 10);
  assert.equal(fixture.node.visible.denoise, 0);
}

console.log("AiO Sampler settings dialog smoke passed.");
