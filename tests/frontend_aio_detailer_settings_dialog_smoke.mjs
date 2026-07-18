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

function rowByLabel(root, label) {
  return find(root, (element) => element.getAttribute?.("data-test-label") === label);
}

function controlIn(root, label) {
  const row = rowByLabel(root, label);
  assert.ok(row, `missing field row: ${label}`);
  assert.ok(row.children[0], `missing field control: ${label}`);
  return row.children[0];
}

function action(dialog, key) {
  const button = findByText(dialog.actions, `text:${key}`);
  assert.ok(button, `missing action: ${key}`);
  return button;
}

function tabs(dialog) {
  return findAll(dialog.body, (element) => element.classList.contains("easyuse-anima-aio-tab"));
}

function tabLabel(tab) {
  return find(tab, (element) => element.classList.contains("easyuse-anima-aio-tab-label"))?.textContent || "";
}

function tabByLabel(dialog, label) {
  const tab = tabs(dialog).find((candidate) => tabLabel(candidate) === label);
  assert.ok(tab, `missing detailer tab: ${label}`);
  return tab;
}

function tabButtons(tab) {
  return findAll(tab, (element) => element.tagName === "BUTTON");
}

function activeEditor(dialog) {
  const panel = find(dialog.body, (element) => element.classList.contains("easyuse-anima-aio-tab-panel"));
  assert.ok(panel?.children[0], "missing active detailer editor");
  return panel.children[0];
}

async function flushPromises() {
  await Promise.resolve();
  await Promise.resolve();
}

const detailerDialogModule = await import(dataModule("../web/js/aio/detailer_settings_dialog.js"));
const settingsModule = await import(dataModule("../web/js/aio/settings.js"));
assert.deepEqual(
  Object.keys(detailerDialogModule),
  ["aioCreateDetailerSettingsDialog"],
  "Detailer settings dialog must expose only its lifecycle factory",
);

function createFixture({
  settings = {},
  available = {},
  choiceOptions = {},
  deferLoads = false,
} = {}) {
  let dependencyCalls = 0;
  let currentDialog = null;
  const trace = [];
  const dialogs = [];
  const loadResolvers = [];
  const loadCalls = [];
  const writes = [];
  const renders = [];
  const stageCalls = [];
  let catalogLoaded = !deferLoads;
  const document = createFakeDocument();
  const availabilityState = { ...available };
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

  function checkbox(value) {
    dependencyCalls += 1;
    const input = document.createElement("input");
    input.type = "checkbox";
    input.checked = !!value;
    return input;
  }

  function textInput(value) {
    dependencyCalls += 1;
    const input = document.createElement("input");
    input.type = "text";
    input.value = String(value ?? "");
    return input;
  }

  function textareaInput(value) {
    dependencyCalls += 1;
    const textarea = document.createElement("textarea");
    textarea.value = String(value ?? "");
    return textarea;
  }

  function numberInput(value, step = "1") {
    dependencyCalls += 1;
    const input = document.createElement("input");
    input.type = "number";
    input.step = step;
    input.value = String(value ?? "");
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

  function applyTooltip(element, key) {
    dependencyCalls += 1;
    element.setAttribute("data-test-tooltip", key);
    return element;
  }

  function mergeDefaults(defaults, current) {
    dependencyCalls += 1;
    return settingsModule.aioMergeDefaults(defaults, current);
  }

  function clampNumber(value, fallback, min, max) {
    dependencyCalls += 1;
    const parsed = Number(value);
    const next = Number.isFinite(parsed) ? parsed : fallback;
    return Math.max(min, Math.min(max, next));
  }

  function isDetailerTargetName(name) {
    return name === "face" || name === "eye" || /^custom_\d+$/.test(name);
  }

  function isCustomDetailerTargetName(name) {
    dependencyCalls += 1;
    return /^custom_\d+$/.test(String(name || ""));
  }

  function detailerTargetDefaults(targetName) {
    dependencyCalls += 1;
    const defaults = targetName === "eye"
      ? defaultSettings.detailer.eye
      : defaultSettings.detailer.face;
    const output = clone(defaults);
    if (/^custom_\d+$/.test(String(targetName || ""))) {
      output.label = `Detailer Block ${String(targetName).split("_").pop()}`;
    }
    return output;
  }

  function detailerTargetTitle(targetName, target, index = 0) {
    dependencyCalls += 1;
    if (target?.label) {
      return String(target.label);
    }
    if (targetName === "face") {
      return text("label.face");
    }
    if (targetName === "eye") {
      return text("label.eye");
    }
    const suffix = String(targetName || "").split("_").pop();
    return `Detailer Block ${suffix || index + 1}`;
  }

  function normalizeDetailerOrder(order, detailer = null) {
    dependencyCalls += 1;
    const output = [];
    const appendTarget = (name) => {
      const normalized = String(name || "").trim();
      if (isDetailerTargetName(normalized) && !output.includes(normalized)) {
        output.push(normalized);
      }
    };
    for (const name of Array.isArray(order) ? order : defaultSettings.detailer.order) {
      appendTarget(name);
    }
    if (detailer && typeof detailer === "object") {
      for (const [name, value] of Object.entries(detailer)) {
        if (["enabled", "order", "sam3"].includes(name) || !value || typeof value !== "object" || Array.isArray(value)) {
          continue;
        }
        appendTarget(name);
      }
    }
    for (const name of defaultSettings.detailer.order) {
      appendTarget(name);
    }
    return output;
  }

  function nextDetailerTargetName(order, detailer = null) {
    dependencyCalls += 1;
    const used = new Set(normalizeDetailerOrder(order, detailer));
    if (detailer && typeof detailer === "object") {
      for (const key of Object.keys(detailer)) {
        used.add(key);
      }
    }
    for (let index = 1; index < 1000; index += 1) {
      const candidate = `custom_${index}`;
      if (!used.has(candidate)) {
        return candidate;
      }
    }
    return `custom_${Date.now()}`;
  }

  function createStageOptimizationEditor(title, values, defaults) {
    dependencyCalls += 1;
    stageCalls.push({ title, values: clone(values), defaults: clone(defaults) });
    const section = document.createElement("section");
    section.className = "test-stage-optimization";
    section.append(Object.assign(document.createElement("h4"), { textContent: `optimization:${title}` }));
    return {
      section,
      values() {
        dependencyCalls += 1;
        return {
          spectrum: clone(values.spectrum ?? defaults.spectrum),
          dit_corrections: clone(values.dit_corrections ?? defaults.dit_corrections),
          optimization_marker: `optimized:${title}`,
        };
      },
      setIntegratedMode() {},
    };
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
    return [...new Set([...fallback, name === "sampler_name" ? "custom_sampler" : "custom_scheduler"])];
  }

  function nodeInputChoiceOptions(dependencyKey, inputName, current, fallback = []) {
    dependencyCalls += 1;
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

  const openDetailerSettings = detailerDialogModule.aioCreateDetailerSettingsDialog({
    document,
    controls: {
      createDialog,
      field,
      checkbox,
      textInput,
      textareaInput,
      numberInput,
      selectInput,
      reconcileSelectInput,
    },
    text: {
      staticText,
      get: text,
      format,
      applyTooltip,
    },
    settingsCore: {
      defaultGenerationSettings: defaultSettings,
      fallbackSamplerNames: ["euler", "er_sde"],
      fallbackSchedulerNames: ["simple", "sgm_uniform"],
      mergeDefaults,
      clampNumber,
      normalizeDetailerOrder,
      isCustomDetailerTargetName,
      nextDetailerTargetName,
      detailerTargetDefaults,
      detailerTargetTitle,
    },
    stageOptimizationEditor: createStageOptimizationEditor,
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
    openDetailerSettings,
    document,
    node,
    defaultSettings,
    dialogs,
    loadCalls,
    availabilityState,
    writes,
    renders,
    stageCalls,
    trace,
    dependencyCallCount: () => dependencyCalls,
    resolveLoads() {
      catalogLoaded = true;
      for (const resolve of loadResolvers.splice(0)) {
        resolve();
      }
    },
  };
}

{
  const multilineFaceWildcard = "configured face wildcard\nsecond line";
  const fixture = createFixture({
    choiceOptions: {
      "checkpointLoader:ckpt_name": [
        "configured-sam3.safetensors",
        "updated-sam3.safetensors",
      ],
    },
    settings: {
      detailer: {
        enabled: true,
        order: ["face", "custom_1", "eye"],
        sam3: { checkpoint: "configured-sam3.safetensors" },
        face: {
          enabled: true,
          guide_size_for: true,
          wildcard: multilineFaceWildcard,
          inpaint_model: true,
          tiled_encode: true,
          tiled_decode: true,
          preserved_face_key: "keep-face",
        },
        eye: { enabled: true },
        custom_1: {
          ...clone(settingsModule.AIO_DEFAULT_GENERATION_SETTINGS.detailer.face),
          label: "Custom One",
          enabled: true,
          detect_prompt: "configured custom prompt",
          inherit_sampler_settings: true,
        },
        custom_9: "obsolete-stale-custom",
      },
      preserved_root_key: "keep-root",
    },
  });
  const originalSettings = clone(fixture.node.settings);
  const originalWidget = fixture.node.widgets[0].value;
  assert.equal(fixture.dependencyCallCount(), 0, "Factory composition must be side-effect free");
  assert.equal(fixture.dialogs.length, 0);
  assert.equal(fixture.writes.length, 0);
  assert.equal(fixture.renders.length, 0);
  assert.equal(fixture.document.createdElements.length, 0, "Factory composition must not create DOM elements");
  assert.equal(fixture.document.body.children.length, 0, "Factory composition must not attach DOM elements");

  fixture.openDetailerSettings(fixture.node);
  await flushPromises();
  const cancelDialog = fixture.dialogs[0];
  assert.equal(cancelDialog.title, "Detailer Settings");
  assert.equal(cancelDialog.subtitle, "SAM3 detection and Impact detailer settings are saved with the node.");
  assert.ok(cancelDialog.body.classList.contains("easyuse-anima-aio-one-column"));
  assert.equal(controlIn(cancelDialog.body, "Enable detailer").checked, true);
  assert.equal(controlIn(cancelDialog.body, "SAM3 checkpoint").value, "configured-sam3.safetensors");
  assert.deepEqual(tabs(cancelDialog).map(tabLabel), ["Face Detailer", "Custom One", "Eye Detailer"]);
  assert.ok(tabByLabel(cancelDialog, "Face Detailer").classList.contains("active"));
  assert.equal(controlIn(activeEditor(cancelDialog), "Block name").value, "Face Detailer");
  assert.equal(controlIn(activeEditor(cancelDialog), "Guide size basis").value, "bbox");
  assert.equal(controlIn(activeEditor(cancelDialog), "Wildcard").value, multilineFaceWildcard);
  assert.equal(controlIn(activeEditor(cancelDialog), "Wildcard").tagName, "TEXTAREA");
  assert.equal(controlIn(activeEditor(cancelDialog), "Inpaint model").checked, true);
  assert.equal(controlIn(activeEditor(cancelDialog), "Tiled encode").checked, true);
  assert.equal(controlIn(activeEditor(cancelDialog), "Tiled decode").checked, true);

  tabByLabel(cancelDialog, "Custom One").emit("click");
  const cancelledName = controlIn(activeEditor(cancelDialog), "Block name");
  cancelledName.value = "Cancelled Rename";
  cancelledName.emit("input");
  assert.ok(tabByLabel(cancelDialog, "Cancelled Rename"));
  findByText(cancelDialog.body, "text:button.addDetailerBlock").emit("click");
  let cancelledNewTab = tabByLabel(cancelDialog, "Detailer Block 2");
  assert.ok(cancelledNewTab);
  tabButtons(cancelledNewTab)[0].emit("click");
  assert.deepEqual(
    tabs(cancelDialog).map(tabLabel),
    ["Face Detailer", "Cancelled Rename", "Detailer Block 2", "Eye Detailer"],
  );
  cancelledNewTab = tabByLabel(cancelDialog, "Detailer Block 2");
  tabButtons(cancelledNewTab)[2].emit("click");
  assert.equal(
    tabs(cancelDialog).some((tab) => tabLabel(tab) === "Detailer Block 2"),
    false,
  );
  controlIn(cancelDialog.body, "SAM3 checkpoint").value = "updated-sam3.safetensors";
  action(cancelDialog, "button.cancel").emit("click");
  assert.deepEqual(fixture.node.settings, originalSettings, "Cancel must not mutate settings");
  assert.equal(fixture.node.widgets[0].value, originalWidget, "Cancel must not rewrite the hidden widget");
  assert.equal(fixture.writes.length, 0);
  assert.equal(fixture.renders.length, 0);
  assert.deepEqual(cancelDialog.trace, ["remove"]);

  fixture.openDetailerSettings(fixture.node);
  await flushPromises();
  const dialog = fixture.dialogs[1];

  const faceTab = tabByLabel(dialog, "Face Detailer");
  const faceRemove = tabButtons(faceTab)[2];
  assert.equal(faceRemove.disabled, true, "Built-in Face block removal must stay disabled");
  faceRemove.emit("click");
  assert.ok(tabByLabel(dialog, "Face Detailer"), "Built-in Face block must not be removable");

  const eyeKeyEvent = tabByLabel(dialog, "Eye Detailer").emit("keydown", { key: "Enter" });
  assert.equal(eyeKeyEvent.defaultPrevented, true);
  assert.ok(tabByLabel(dialog, "Eye Detailer").classList.contains("active"));
  const customKeyEvent = tabByLabel(dialog, "Custom One").emit("keydown", { key: " " });
  assert.equal(customKeyEvent.defaultPrevented, true);
  assert.ok(tabByLabel(dialog, "Custom One").classList.contains("active"));

  let editor = activeEditor(dialog);
  assert.equal(controlIn(editor, "Prompt").value, "configured custom prompt");
  const followMain = controlIn(editor, "Follow main sampler");
  assert.equal(followMain.checked, true);
  assert.equal(rowByLabel(editor, "CFG").style.display, "none");
  assert.equal(rowByLabel(editor, "Sampler").style.display, "none");
  assert.equal(rowByLabel(editor, "Scheduler").style.display, "none");
  followMain.checked = false;
  followMain.emit("change");
  assert.equal(rowByLabel(editor, "CFG").style.display, "");
  assert.equal(rowByLabel(editor, "Sampler").style.display, "");
  assert.equal(rowByLabel(editor, "Scheduler").style.display, "");

  const addBlock = findByText(dialog.body, "text:button.addDetailerBlock");
  assert.ok(addBlock);
  addBlock.emit("click");
  assert.deepEqual(tabs(dialog).map(tabLabel), ["Face Detailer", "Custom One", "Eye Detailer", "Detailer Block 2"]);
  assert.ok(tabByLabel(dialog, "Detailer Block 2").classList.contains("active"));

  editor = activeEditor(dialog);
  const blockName = controlIn(editor, "Block name");
  blockName.value = "Portrait Detailer";
  blockName.emit("input");
  assert.ok(tabByLabel(dialog, "Portrait Detailer").classList.contains("active"));

  let portraitTab = tabByLabel(dialog, "Portrait Detailer");
  let moveEvent = tabButtons(portraitTab)[0].emit("click");
  assert.equal(moveEvent.propagationStopped, true);
  portraitTab = tabByLabel(dialog, "Portrait Detailer");
  moveEvent = tabButtons(portraitTab)[0].emit("click");
  assert.equal(moveEvent.propagationStopped, true);
  assert.deepEqual(tabs(dialog).map(tabLabel), ["Face Detailer", "Portrait Detailer", "Custom One", "Eye Detailer"]);

  const customOneTab = tabByLabel(dialog, "Custom One");
  const removeEvent = tabButtons(customOneTab)[2].emit("click");
  assert.equal(removeEvent.propagationStopped, true);
  assert.deepEqual(tabs(dialog).map(tabLabel), ["Face Detailer", "Portrait Detailer", "Eye Detailer"]);

  tabByLabel(dialog, "Portrait Detailer").emit("click");
  editor = activeEditor(dialog);
  controlIn(editor, "Prompt").value = "new portrait prompt";
  controlIn(editor, "Steps").value = "100";
  controlIn(editor, "CFG").value = "0";
  controlIn(editor, "Denoise").value = "2";
  const portraitFollowMain = controlIn(editor, "Follow main sampler");
  portraitFollowMain.checked = false;
  portraitFollowMain.emit("change");
  controlIn(editor, "Guide size basis").value = "bbox";
  controlIn(editor, "Wildcard").value = "__portrait_style__";
  controlIn(editor, "Inpaint model").checked = true;
  controlIn(editor, "Tiled encode").checked = true;
  controlIn(editor, "Tiled decode").checked = true;
  controlIn(dialog.body, "SAM3 checkpoint").value = "updated-sam3.safetensors";
  controlIn(dialog.body, "Enable detailer").checked = true;

  action(dialog, "button.apply").emit("click");
  assert.equal(fixture.writes.length, 1);
  assert.equal(fixture.renders.length, 1);
  assert.deepEqual(dialog.trace.slice(-3), ["write", "render", "remove"]);
  assert.equal(fixture.node.settings.preserved_root_key, "keep-root");
  assert.equal(fixture.node.settings.detailer.face.preserved_face_key, "keep-face");
  assert.equal(fixture.node.settings.detailer.face.guide_size_for, true);
  assert.equal(fixture.node.settings.detailer.face.wildcard, multilineFaceWildcard);
  assert.equal(fixture.node.settings.detailer.face.inpaint_model, true);
  assert.equal(fixture.node.settings.detailer.face.tiled_encode, true);
  assert.equal(fixture.node.settings.detailer.face.tiled_decode, true);
  assert.equal(fixture.node.settings.detailer.enabled, true);
  assert.equal(fixture.node.settings.detailer.sam3.context, "load_checkpoint");
  assert.equal(fixture.node.settings.detailer.sam3.checkpoint, "updated-sam3.safetensors");
  assert.deepEqual(fixture.node.settings.detailer.order, ["face", "custom_2", "eye"]);
  assert.equal(Object.hasOwn(fixture.node.settings.detailer, "custom_1"), false, "Removed custom block must be deleted");
  assert.equal(Object.hasOwn(fixture.node.settings.detailer, "custom_9"), false, "Stale custom key must be deleted");
  assert.equal(fixture.node.settings.detailer.custom_2.label, "Portrait Detailer");
  assert.equal(fixture.node.settings.detailer.custom_2.detect_prompt, "new portrait prompt");
  assert.equal(fixture.node.settings.detailer.custom_2.steps, 75);
  assert.equal(fixture.node.settings.detailer.custom_2.cfg, 1);
  assert.equal(fixture.node.settings.detailer.custom_2.denoise, 1);
  assert.equal(fixture.node.settings.detailer.custom_2.inherit_sampler_settings, false);
  assert.equal(fixture.node.settings.detailer.custom_2.guide_size_for, true);
  assert.equal(fixture.node.settings.detailer.custom_2.wildcard, "__portrait_style__");
  assert.equal(fixture.node.settings.detailer.custom_2.inpaint_model, true);
  assert.equal(fixture.node.settings.detailer.custom_2.tiled_encode, true);
  assert.equal(fixture.node.settings.detailer.custom_2.tiled_decode, true);
  assert.equal(
    fixture.node.settings.detailer.custom_2.optimization_marker,
    "optimized:Detailer Block 2 Optimization",
  );
  assert.ok(fixture.node.settings.detailer.custom_2.spectrum);
  assert.ok(fixture.node.settings.detailer.custom_2.dit_corrections);
  assert.deepEqual(JSON.parse(fixture.node.widgets[0].value), fixture.node.settings);
  assert.ok(fixture.stageCalls.some(({ title }) => title === "Detailer Block 2 Optimization"));
}

{
  const fixture = createFixture({
    settings: {
      detailer: {
        enabled: true,
        order: ["custom_7", "face", "eye"],
        face: { enabled: false },
        eye: { enabled: false },
        custom_7: {
          label: "Sparse Custom",
          enabled: false,
          guide_size_for: true,
          wildcard: "__saved_sparse__",
          inpaint_model: true,
          tiled_encode: true,
          tiled_decode: true,
          preserved_sparse_key: { nested: "keep-custom" },
        },
      },
    },
  });
  fixture.openDetailerSettings(fixture.node);
  await flushPromises();
  const dialog = fixture.dialogs[0];
  assert.deepEqual(tabs(dialog).map(tabLabel), ["Sparse Custom", "Face Detailer", "Eye Detailer"]);
  tabByLabel(dialog, "Sparse Custom").emit("click");
  const editor = activeEditor(dialog);
  assert.equal(controlIn(editor, "Enable").checked, false);
  assert.equal(controlIn(editor, "Guide size basis").value, "bbox");
  assert.equal(controlIn(editor, "Wildcard").value, "__saved_sparse__");
  assert.equal(controlIn(editor, "Inpaint model").checked, true);
  assert.equal(controlIn(editor, "Tiled encode").checked, true);
  assert.equal(controlIn(editor, "Tiled decode").checked, true);

  action(dialog, "button.apply").emit("click");
  assert.deepEqual(fixture.node.settings.detailer.order, ["custom_7", "face", "eye"]);
  assert.equal(fixture.node.settings.detailer.custom_7.enabled, false);
  assert.equal(fixture.node.settings.detailer.custom_7.guide_size_for, true);
  assert.equal(fixture.node.settings.detailer.custom_7.wildcard, "__saved_sparse__");
  assert.equal(fixture.node.settings.detailer.custom_7.inpaint_model, true);
  assert.equal(fixture.node.settings.detailer.custom_7.tiled_encode, true);
  assert.equal(fixture.node.settings.detailer.custom_7.tiled_decode, true);
  assert.deepEqual(
    fixture.node.settings.detailer.custom_7.preserved_sparse_key,
    { nested: "keep-custom" },
    "Untouched custom-target fields outside the known schema must survive Apply",
  );
  assert.equal(fixture.node.settings.detailer.face.enabled, false);
  assert.equal(fixture.node.settings.detailer.eye.enabled, false);
}

{
  const fixture = createFixture({
    available: { impactDetailer: true, impactMaskToSegs: true },
    choiceOptions: {
      "checkpointLoader:ckpt_name": ["installed-a.safetensors", "installed-b.safetensors"],
    },
    deferLoads: true,
    settings: {
      detailer: {
        enabled: true,
        sam3: { checkpoint: "legacy-missing.safetensors" },
        face: { enabled: true },
        eye: { enabled: true },
      },
    },
  });
  assert.equal(fixture.dependencyCallCount(), 0, "Deferred fixture factory must also be side-effect free");
  fixture.openDetailerSettings(fixture.node);
  const dialog = fixture.dialogs[0];
  const enabled = controlIn(dialog.body, "Enable detailer");
  const checkpoint = controlIn(dialog.body, "SAM3 checkpoint");
  const warning = find(dialog.body, (element) => element.classList.contains("easyuse-anima-aio-warning"));
  assert.equal(enabled.disabled, false);
  assert.equal(enabled.checked, true);
  assert.equal(warning.hidden, true);
  assert.equal(fixture.loadCalls.length, 1);
  assert.equal(checkpoint.tagName, "SELECT", "SAM3 checkpoint must use a native catalog select");
  assert.deepEqual(
    checkpoint.options.map((option) => option.value),
    ["legacy-missing.safetensors"],
    "First-open SAM3 choices must initially preserve the saved fallback",
  );

  fixture.availabilityState.impactDetailer = false;
  fixture.availabilityState.impactMaskToSegs = false;
  fixture.resolveLoads();
  await flushPromises();
  assert.deepEqual(
    checkpoint.options.map((option) => option.value),
    ["legacy-missing.safetensors", "installed-a.safetensors", "installed-b.safetensors"],
    "CheckpointLoaderSimple object info must hydrate installed SAM3 choices",
  );
  assert.equal(
    checkpoint.value,
    "legacy-missing.safetensors",
    "SAM3 hydration must preserve a saved value missing from the current catalog",
  );
  assert.equal(enabled.disabled, true, "Missing dependencies must lock Detailer after async refresh");
  assert.equal(enabled.checked, false, "Missing dependencies must clear an enabled Detailer toggle");
  assert.equal(warning.hidden, false);
  assert.equal(
    warning.textContent,
    'format:warning.optionalDependencyMissing:{"backend":"Detailer","pack":"pack:impactDetailer, pack:impactMaskToSegs"}',
  );

  action(dialog, "button.apply").emit("click");
  assert.deepEqual(dialog.trace.slice(-3), ["write", "render", "remove"]);
  assert.equal(fixture.node.settings.detailer.enabled, false);
  assert.equal(fixture.node.settings.detailer.face.enabled, false);
  assert.equal(fixture.node.settings.detailer.eye.enabled, false);
}

{
  const fixture = createFixture({
    choiceOptions: {
      "checkpointLoader:ckpt_name": ["installed-after-close.safetensors"],
    },
    deferLoads: true,
    settings: {
      detailer: {
        sam3: { checkpoint: "saved-before-close.safetensors" },
      },
    },
  });
  fixture.openDetailerSettings(fixture.node);
  const dialog = fixture.dialogs[0];
  const checkpoint = controlIn(dialog.body, "SAM3 checkpoint");
  action(dialog, "button.cancel").emit("click");
  fixture.resolveLoads();
  await flushPromises();
  assert.deepEqual(
    checkpoint.options.map((option) => option.value),
    ["saved-before-close.safetensors"],
    "A late checkpoint catalog callback must not mutate a closed dialog",
  );
}

console.log("AiO Detailer settings dialog smoke passed.");
