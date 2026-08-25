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
  return findByText(dialog.body, `static:${heading}`)?.parentElement || null;
}

function rowByLabel(root, label) {
  return find(root, (element) => element.getAttribute?.("data-test-label") === label);
}

function control(dialog, label, index = 0) {
  const values = dialog.controls.get(label) || [];
  assert.ok(values[index], `missing control: ${label}[${index}]`);
  return values[index];
}

function action(dialog, key) {
  const button = findByText(dialog.actions, `text:${key}`);
  assert.ok(button, `missing action: ${key}`);
  return button;
}

function setSelectValue(select, value) {
  select.value = String(value);
  for (const option of select.options || []) {
    option.selected = option.value === select.value;
  }
}

async function flushPromises() {
  await Promise.resolve();
  await Promise.resolve();
}

const stageDialogModule = await import(dataModule("../web/js/aio/stage_settings_dialogs.js"));
const settingsModule = await import(dataModule("../web/js/aio/settings.js"));
const numericLimits = {
  samplerSteps: { min: 1, max: 10000 },
  samplerCfg: { min: 0, max: 100 },
  auraFlowShift: { min: 0, max: 100 },
  highresScaleBy: { min: 0.01, max: 8 },
  upscaleScaleBy: { min: 0.05, max: 4 },
  resolution: { min: 64, max: 16384 },
};
assert.deepEqual(
  Object.keys(stageDialogModule),
  ["aioCreateStageSettingsDialogs"],
  "Stage settings dialogs must expose only their factory contract",
);

function createFixture({
  settings = {},
  available = {},
  missingByBackend = {},
  choiceOptions = {},
  deferLoads = false,
} = {}) {
  let dependencyCalls = 0;
  let currentDialog = null;
  const trace = [];
  const dialogs = [];
  const loadCalls = [];
  const loadResolvers = [];
  const optionCalls = [];
  const choiceCalls = [];
  const notifications = [];
  let catalogLoaded = !deferLoads;
  const writes = [];
  const renders = [];
  const document = createFakeDocument();
  const availabilityState = { ...available };
  const missingByBackendState = Object.fromEntries(
    Object.entries(missingByBackend).map(([backend, packs]) => [backend, [...packs]]),
  );
  const defaultSettings = clone(settingsModule.AIO_DEFAULT_GENERATION_SETTINGS);
  const node = {
    settings: settingsModule.aioMergeDefaults(defaultSettings, settings),
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
      controls: new Map(),
      tooltips: new Map(),
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
    row.append(element);
    section.append(row);
    if (currentDialog) {
      const values = currentDialog.controls.get(label) || [];
      values.push(element);
      currentDialog.controls.set(label, values);
      currentDialog.tooltips.set(label, tooltipKey);
    }
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

  function reconcileSelectInput(select, options) {
    dependencyCalls += 1;
    const current = String(select.value ?? "");
    const values = [...new Set(options.map((option) => String(option?.value ?? option ?? "")))];
    if (current && !values.includes(current)) {
      values.unshift(current);
    }
    select.replaceChildren();
    select.options = [];
    for (const value of values) {
      const option = document.createElement("option");
      option.value = value;
      option.textContent = value;
      option.selected = value === current;
      select.options.push(option);
      select.append(option);
    }
    select.value = current;
    return select;
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

  function clampNumber(value, fallback, min, max) {
    dependencyCalls += 1;
    const parsed = Number(value);
    const next = Number.isFinite(parsed) ? parsed : fallback;
    return Math.max(min, Math.min(max, next));
  }

  function normalizeUsduAutoTileRange(usdu) {
    dependencyCalls += 1;
    const defaults = defaultSettings.upscale.usdu;
    const target = Math.trunc(clampNumber(usdu.auto_tile_target, defaults.auto_tile_target, 64, 16384));
    let min = Math.trunc(clampNumber(usdu.auto_tile_min, defaults.auto_tile_min, 64, 16384));
    let max = Math.trunc(clampNumber(usdu.auto_tile_max, defaults.auto_tile_max, 64, 16384));
    max = Math.max(min, max);
    if (target < min) {
      min = target;
    }
    if (target > max) {
      max = target;
    }
    usdu.auto_tile_target = target;
    usdu.auto_tile_min = min;
    usdu.auto_tile_max = Math.max(min, max);
    return usdu;
  }

  function findWidget(targetNode, name) {
    dependencyCalls += 1;
    return targetNode.widgets?.find((widget) => widget.name === name);
  }

  function getSettings(targetNode) {
    dependencyCalls += 1;
    trace.push("get-settings");
    return clone(targetNode.settings);
  }

  function widgetOptions(_targetNode, name, fallback) {
    dependencyCalls += 1;
    optionCalls.push(name);
    return [...new Set([...fallback, name === "sampler_name" ? "custom_sampler" : "custom_scheduler"])];
  }

  function nodeInputChoiceOptions(dependencyKey, inputName, current, fallback = []) {
    dependencyCalls += 1;
    choiceCalls.push({ dependencyKey, inputName, current, fallback: [...fallback] });
    const key = `${dependencyKey}:${inputName}`;
    const catalog = catalogLoaded ? (choiceOptions[key] || []) : [];
    const values = [...new Set((catalog.length ? catalog : fallback).filter(Boolean))];
    const normalizedCurrent = String(current ?? "");
    if (normalizedCurrent && !values.includes(normalizedCurrent)) {
      values.unshift(normalizedCurrent);
    }
    return values;
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

  const runtime = stageDialogModule.aioCreateStageSettingsDialogs({
    document,
    controls: {
      createDialog,
      field,
      numberInput,
      checkbox,
      selectInput,
      reconcileSelectInput,
    },
    text: {
      staticText,
      get: text,
      format,
    },
    settingsCore: {
      defaultGenerationSettings: defaultSettings,
      fallbackSamplerNames: ["euler", "er_sde"],
      fallbackSchedulerNames: ["simple", "karras"],
      numericLimits,
      mergeDefaults: settingsModule.aioMergeDefaults,
      clampNumber,
      normalizeUsduAutoTileRange,
    },
    nodeAdapter: {
      generatorSettingsWidget: "generation_settings",
      findWidget,
      getSettings,
      widgetOptions,
      nodeInputChoiceOptions,
      writeSettings,
      renderPanel,
    },
    dependencyAdapter: {
      available(key) {
        dependencyCalls += 1;
        return Object.hasOwn(availabilityState, key) ? !!availabilityState[key] : true;
      },
      pack(key) {
        dependencyCalls += 1;
        return `pack:${key}`;
      },
      upscaleBackendMissingPacks(backend) {
        dependencyCalls += 1;
        return [...(missingByBackendState[backend] || [])];
      },
      upscaleBackendMissingKeys(backend) {
        return (missingByBackendState[backend] || []).length ? [`${backend}Dependency`] : [];
      },
      markMissingControl(control, missing, message = "") {
        control.disabled = false;
        control.parentElement?.classList.toggle("easyuse-anima-aio-unsupported", missing);
        control.title = missing ? message : "";
      },
      notifyMissing(backend, keys) {
        notifications.push({ backend, keys: [...keys] });
        return true;
      },
      load(options) {
        dependencyCalls += 1;
        loadCalls.push(options);
        if (!deferLoads) {
          catalogLoaded = true;
          return Promise.resolve();
        }
        return new Promise((resolve) => loadResolvers.push(resolve));
      },
    },
  });

  return {
    runtime,
    node,
    document,
    defaultSettings,
    dialogs,
    loadCalls,
    availabilityState,
    missingByBackendState,
    optionCalls,
    choiceCalls,
    notifications,
    writes,
    renders,
    trace,
    resolveLoads() {
      catalogLoaded = true;
      for (const resolve of loadResolvers.splice(0)) {
        resolve();
      }
    },
    dependencyCallCount: () => dependencyCalls,
  };
}

{
  const fixture = createFixture();
  assert.equal(fixture.dependencyCallCount(), 0, "Factory composition must be side-effect free");
  const editor = fixture.runtime.createStageOptimizationEditor(
    "Standalone Optimization",
    fixture.defaultSettings.highres,
    fixture.defaultSettings.highres,
  );
  await flushPromises();
  assert.equal(findByText(editor.section, "static:Standalone Optimization")?.tagName, "H3");
  assert.equal(typeof editor.values, "function");
  assert.equal(typeof editor.setIntegratedMode, "function");
  assert.equal(editor.values().spectrum.window_size, fixture.defaultSettings.highres.spectrum.window_size);
  editor.setIntegratedMode(true);
  assert.equal(rowByLabel(editor.section, "Spectrum patch").style.display, "none");
  assert.equal(rowByLabel(editor.section, "Compat").style.display, "none");
  assert.equal(fixture.dialogs.length, 0);
  assert.equal(fixture.writes.length, 0);
  assert.equal(fixture.renders.length, 0);
}

{
  const fixture = createFixture({
    available: { spectrumPatch: true },
    deferLoads: true,
    settings: {
      sampler: { backend: "spectrum_spd_speed" },
      highres: {
        enabled: true,
        scale_by: 1.75,
        upscale_method: "lanczos",
        multiple: "64",
        max_long_edge: 4096,
        steps: 33,
        inherit_sampler_settings: true,
        cfg: 7.5,
        sampler_name: "custom_sampler",
        scheduler: "custom_scheduler",
        denoise: 0.44,
        spectrum: { enabled: true },
        dit_corrections: { enabled: true },
        preserved_highres_key: "keep-highres",
      },
      preserved_root_key: "keep-root",
    },
  });
  assert.deepEqual(
    Object.keys(fixture.runtime).sort(),
    ["createStageOptimizationEditor", "openHighresSettings", "openUpscaleSettings"].sort(),
    "Stage dialog runtime must expose the shared editor and two opener facades",
  );

  fixture.runtime.openHighresSettings(fixture.node);
  const dialog = fixture.dialogs[0];
  assert.equal(control(dialog, "Spectrum patch").disabled, false);
  assert.equal(control(dialog, "Spectrum patch").checked, true);
  assert.equal(control(dialog, "Use corrections").disabled, false);
  assert.equal(control(dialog, "Use corrections").checked, true);
  fixture.availabilityState.spectrumPatch = false;
  fixture.resolveLoads();
  await flushPromises();
  assert.equal(dialog.title, "Highres Settings");
  assert.equal(dialog.subtitle, "Image scaling and Highres resampling settings are saved with the node.");
  assert.ok(dialog.body.classList.contains("easyuse-anima-aio-one-column"));
  assert.ok(fixture.loadCalls.length > 0, "Highres optimization must refresh dependencies asynchronously");
  assert.equal(control(dialog, "Enable highres").checked, true);
  assert.equal(control(dialog, "Scale by").value, "1.75");
  assert.equal(control(dialog, "Method").value, "lanczos");
  assert.equal(control(dialog, "Multiple").value, "64");
  assert.equal(control(dialog, "Max long edge").value, "4096");
  assert.equal(control(dialog, "Steps").value, "33");
  assert.equal(control(dialog, "Steps").max, "10000");
  assert.equal(control(dialog, "Follow main sampler").checked, true);
  assert.equal(control(dialog, "CFG").value, "7.5");
  assert.equal(control(dialog, "CFG").min, "0");
  assert.equal(control(dialog, "CFG").max, "100");
  assert.equal(control(dialog, "Sampler").value, "custom_sampler");
  assert.equal(control(dialog, "Scheduler").value, "custom_scheduler");
  assert.equal(control(dialog, "Denoise").value, "0.44");
  assert.equal(control(dialog, "CFG").parentElement.style.display, "none");
  assert.equal(control(dialog, "Sampler").parentElement.style.display, "none");
  assert.equal(control(dialog, "Scheduler").parentElement.style.display, "none");
  assert.equal(control(dialog, "Spectrum patch").disabled, false);
  assert.equal(control(dialog, "Spectrum patch").checked, false);
  assert.equal(control(dialog, "Use corrections").disabled, false);
  assert.equal(control(dialog, "Use corrections").checked, false);
  const warnings = findAll(dialog.body, (element) => element.classList.contains("easyuse-anima-aio-warning"));
  const spdWarning = warnings.find((element) => element.textContent === "text:text.highresSpdManualRequired");
  assert.ok(spdWarning);
  assert.ok(warnings.some((element) => element.textContent.includes("pack:spectrumPatch")));
  assert.deepEqual(fixture.notifications, [], "Dependency refresh must not notify by itself");
  const spectrumToggle = control(dialog, "Spectrum patch");
  spectrumToggle.checked = true;
  spectrumToggle.emit("change");
  assert.deepEqual(fixture.notifications, [{
    backend: "Highres Optimization",
    keys: ["spectrumPatch"],
  }]);
  assert.equal(spectrumToggle.checked, false);

  const inheritSampler = control(dialog, "Follow main sampler");
  inheritSampler.checked = false;
  inheritSampler.emit("change");
  assert.equal(control(dialog, "CFG").parentElement.style.display, "");
  assert.equal(control(dialog, "Sampler").parentElement.style.display, "");
  assert.equal(control(dialog, "Scheduler").parentElement.style.display, "");
  assert.equal(spdWarning.textContent, "");
  assert.equal(spdWarning.hidden, true);

  const beforeCancel = clone(fixture.node.settings);
  action(dialog, "button.cancel").emit("click");
  assert.deepEqual(fixture.node.settings, beforeCancel, "Cancel must not mutate Highres settings");
  assert.equal(fixture.writes.length, 0);
  assert.equal(fixture.renders.length, 0);
  assert.deepEqual(dialog.trace, ["remove"]);

  fixture.runtime.openHighresSettings(fixture.node);
  fixture.resolveLoads();
  await flushPromises();
  const applyDialog = fixture.dialogs[1];
  control(applyDialog, "Scale by").value = "9";
  control(applyDialog, "Steps").value = "120";
  control(applyDialog, "CFG").value = "20";
  control(applyDialog, "Denoise").value = "-1";
  control(applyDialog, "Follow main sampler").checked = false;
  action(applyDialog, "button.apply").emit("click");
  assert.equal(fixture.writes.length, 1);
  assert.equal(fixture.renders.length, 1);
  assert.deepEqual(applyDialog.trace.slice(-3), ["write", "render", "remove"]);
  assert.equal(fixture.node.settings.highres.scale_by, 8);
  assert.equal(fixture.node.settings.highres.steps, 120);
  assert.equal(fixture.node.settings.highres.cfg, 20);
  assert.equal(fixture.node.settings.highres.denoise, 0);
  assert.equal(fixture.node.settings.highres.inherit_sampler_settings, false);
  assert.equal(fixture.node.settings.highres.spectrum.enabled, false);
  assert.equal(fixture.node.settings.highres.dit_corrections.enabled, false);
  assert.equal(fixture.node.settings.highres.preserved_highres_key, "keep-highres");
  assert.equal(fixture.node.settings.preserved_root_key, "keep-root");
  assert.deepEqual(JSON.parse(fixture.node.widgets[0].value), fixture.node.settings);
}

{
  const fixture = createFixture({
    missingByBackend: { resshift: [] },
    choiceOptions: {
      "upscaleModelLoader:model_name": ["installed-a.pth", "installed-b.pth"],
      "resShiftLoader:student_name": ["student.safetensors", "other-student.safetensors"],
    },
    deferLoads: true,
    settings: {
      upscale: {
        enabled: true,
        backend: "resshift",
        scale_by: 2.5,
        inherit_sampler_settings: false,
        prompt_mode: "ignored-legacy-root",
        usdu: {
          upscale_model_name: "legacy-missing.pth",
          auto_tile_size: false,
          prompt_mode: "quality_tags_only",
          auto_tile_target: 900,
          auto_tile_min: 500,
          auto_tile_max: 1500,
        },
        resshift: {
          scale: "x4",
          student_name: "student.safetensors",
          dtype: "fp32",
          chop: 768,
          overlap: 96,
          tile_batch: 3,
        },
        preserved_upscale_key: "keep-upscale",
      },
    },
  });
  assert.equal(fixture.dependencyCallCount(), 0, "Second factory composition must also be side-effect free");
  fixture.runtime.openUpscaleSettings(fixture.node);
  const dialog = fixture.dialogs[0];
  const backend = control(dialog, "Upscale backend");
  const resshiftOption = backend.options.find((option) => option.value === "resshift");
  assert.equal(resshiftOption.disabled, false);
  assert.equal(control(dialog, "Enable upscale").checked, true);
  assert.deepEqual(
    control(dialog, "Upscale model").options.map((option) => option.value),
    ["legacy-missing.pth"],
    "First-open upscale choices must initially preserve the saved fallback",
  );
  fixture.missingByBackendState.resshift = ["ComfyUI-ResShift"];
  fixture.resolveLoads();
  await flushPromises();
  assert.equal(dialog.title, "Upscale Settings");
  assert.ok(fixture.loadCalls.length > 0, "Upscale must refresh dependencies asynchronously");
  assert.deepEqual(new Set(fixture.optionCalls), new Set(["sampler_name", "scheduler"]));
  assert.deepEqual(
    new Set(fixture.choiceCalls.map(({ dependencyKey, inputName }) => `${dependencyKey}:${inputName}`)),
    new Set(["upscaleModelLoader:model_name", "resShiftLoader:student_name"]),
  );
  assert.equal(resshiftOption.disabled, false, "Missing backend remains selectable for an explicit notice");
  assert.ok(resshiftOption.textContent.includes("ComfyUI-ResShift"));
  assert.equal(control(dialog, "Enable upscale").checked, false, "Missing selected backend must disable upscale");
  assert.deepEqual(
    control(dialog, "Upscale model").options.map((option) => option.value),
    ["legacy-missing.pth", "installed-a.pth", "installed-b.pth"],
    "Async object-info load must hydrate all installed upscale choices",
  );
  assert.equal(
    control(dialog, "Upscale model").value,
    "legacy-missing.pth",
    "Hydration must preserve a saved value that is absent from the current catalog",
  );
  assert.ok(findAll(dialog.body, (element) => element.classList.contains("easyuse-anima-aio-warning"))
    .some((element) => element.textContent.includes("ComfyUI-ResShift")));
  assert.ok(sectionByHeading(dialog, "USDU Upscale").classList.contains("hidden"));
  assert.ok(sectionByHeading(dialog, "USDU Sampler").classList.contains("hidden"));
  assert.ok(!sectionByHeading(dialog, "ResShift Upscale").classList.contains("hidden"));
  assert.equal(control(dialog, "Auto tile target").parentElement.style.display, "none");
  assert.equal(control(dialog, "Tile width").parentElement.style.display, "");
  assert.equal(control(dialog, "CFG").parentElement.style.display, "");
  assert.equal(control(dialog, "Scale by").value, "2.5");
  assert.equal(control(dialog, "USDU prompt").value, "no_general");
  assert.equal(control(dialog, "Auto tile size").checked, false);
  assert.equal(control(dialog, "Auto tile target").value, "900");
  assert.equal(control(dialog, "Auto tile min").value, "500");
  assert.equal(control(dialog, "Auto tile max").value, "1500");
  assert.equal(control(dialog, "Scale").value, "x4");
  assert.equal(control(dialog, "Student").value, "student.safetensors");
  assert.equal(control(dialog, "Dtype").value, "fp32");
  assert.equal(control(dialog, "Chop").value, "768");
  assert.equal(control(dialog, "Overlap").value, "96");
  assert.equal(control(dialog, "Tile batch", 1).value, "3");

  assert.deepEqual(fixture.notifications, [], "Async backend refresh must stay silent");
  backend.emit("change");
  assert.deepEqual(fixture.notifications, [{
    backend: "resshift",
    keys: ["resshiftDependency"],
  }]);
  assert.equal(backend.value, "usdu", "Rejected backend selection must restore an available fallback");

  setSelectValue(backend, "usdu");
  backend.emit("change");
  control(dialog, "Enable upscale").checked = true;
  assert.ok(!sectionByHeading(dialog, "USDU Upscale").classList.contains("hidden"));
  assert.ok(!sectionByHeading(dialog, "USDU Sampler").classList.contains("hidden"));
  assert.ok(sectionByHeading(dialog, "ResShift Upscale").classList.contains("hidden"));
  const autoTile = control(dialog, "Auto tile size");
  autoTile.checked = true;
  autoTile.emit("change");
  assert.equal(control(dialog, "Auto tile target").parentElement.style.display, "");
  assert.equal(control(dialog, "Auto tile min").parentElement.style.display, "");
  assert.equal(control(dialog, "Auto tile max").parentElement.style.display, "");
  assert.equal(control(dialog, "Tile width").parentElement.style.display, "none");
  const inheritSampler = control(dialog, "Follow main sampler");
  inheritSampler.checked = true;
  inheritSampler.emit("change");
  assert.equal(control(dialog, "CFG").parentElement.style.display, "none");
  assert.equal(control(dialog, "Sampler").parentElement.style.display, "none");
  assert.equal(control(dialog, "Scheduler").parentElement.style.display, "none");

  control(dialog, "Scale by").value = "5";
  control(dialog, "Steps").value = "2000";
  control(dialog, "Denoise").value = "2";
  control(dialog, "Auto tile target").value = "300";
  control(dialog, "Auto tile min").value = "500";
  control(dialog, "Auto tile max").value = "100";
  setSelectValue(control(dialog, "USDU prompt"), "no_general");
  action(dialog, "button.apply").emit("click");
  assert.deepEqual(dialog.trace.slice(-3), ["write", "render", "remove"]);
  assert.equal(fixture.node.settings.upscale.enabled, true);
  assert.equal(fixture.node.settings.upscale.backend, "usdu");
  assert.equal(fixture.node.settings.upscale.scale_by, 4);
  assert.equal(fixture.node.settings.upscale.steps, 2000);
  assert.equal(fixture.node.settings.upscale.denoise, 1);
  assert.equal(fixture.node.settings.upscale.inherit_sampler_settings, true);
  assert.equal(fixture.node.settings.upscale.usdu.prompt_mode, "no_general");
  assert.equal(fixture.node.settings.upscale.usdu.auto_tile_target, 300);
  assert.equal(fixture.node.settings.upscale.usdu.auto_tile_min, 300);
  assert.equal(fixture.node.settings.upscale.usdu.auto_tile_max, 500);
  assert.equal(fixture.node.settings.upscale.usdu.upscale_model_name, "legacy-missing.pth");
  assert.equal(fixture.node.settings.upscale.resshift.student_name, "student.safetensors");
  assert.equal(fixture.node.settings.upscale.preserved_upscale_key, "keep-upscale");

  const writesAfterApply = fixture.writes.length;
  const rendersAfterApply = fixture.renders.length;
  const settingsBeforeCancel = clone(fixture.node.settings);
  const widgetBeforeCancel = fixture.node.widgets[0].value;
  fixture.runtime.openUpscaleSettings(fixture.node);
  fixture.resolveLoads();
  await flushPromises();
  const cancelDialog = fixture.dialogs[1];
  action(cancelDialog, "button.cancel").emit("click");
  assert.equal(fixture.writes.length, writesAfterApply, "Upscale Cancel must not add a write");
  assert.equal(fixture.renders.length, rendersAfterApply, "Upscale Cancel must not render");
  assert.deepEqual(fixture.node.settings, settingsBeforeCancel, "Upscale Cancel must not mutate settings");
  assert.equal(fixture.node.widgets[0].value, widgetBeforeCancel, "Upscale Cancel must not rewrite the hidden widget");
  assert.deepEqual(cancelDialog.trace, ["remove"]);
}

{
  const fixture = createFixture({
    choiceOptions: {
      "upscaleModelLoader:model_name": ["installed-after-close.pth"],
    },
    deferLoads: true,
    settings: {
      upscale: {
        usdu: { upscale_model_name: "saved-before-close.pth" },
      },
    },
  });
  fixture.runtime.openUpscaleSettings(fixture.node);
  const dialog = fixture.dialogs[0];
  const upscaleModel = control(dialog, "Upscale model");
  action(dialog, "button.cancel").emit("click");
  fixture.resolveLoads();
  await flushPromises();
  assert.deepEqual(
    upscaleModel.options.map((option) => option.value),
    ["saved-before-close.pth"],
    "A late catalog callback must not mutate a closed dialog",
  );
}

console.log("AiO stage settings dialogs smoke passed.");
