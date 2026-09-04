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

function sectionByHeading(root, heading) {
  const title = findByText(root, `static:${heading}`);
  assert.ok(title?.parentElement, `missing section: ${heading}`);
  return title.parentElement;
}

function hashRows(editor) {
  return findAll(
    editor,
    (element) => element.classList.contains("easyuse-anima-aio-hash-bundle-row"),
  );
}

function hashValue(row) {
  const textarea = row.querySelector("textarea");
  assert.ok(textarea, "missing hash bundle textarea");
  return textarea;
}

function civitaiRows(editor) {
  return findAll(
    editor,
    (element) => element.classList.contains("easyuse-anima-aio-civitai-fetcher-row"),
  );
}

function civitaiInputs(row) {
  const inputs = row.querySelectorAll("input");
  assert.equal(inputs.length, 4, "Civitai row must expose enabled, username, model, and version inputs");
  return inputs;
}

function removeRow(row) {
  const button = findByText(row, "text:button.remove");
  assert.ok(button, "missing row remove action");
  button.emit("click");
}

function addRow(editor, key) {
  const button = findByText(editor, `text:${key}`);
  assert.ok(button, `missing row add action: ${key}`);
  button.emit("click");
}

async function flushPromises() {
  await Promise.resolve();
  await Promise.resolve();
}

const saveDialogModule = await import(dataModule("../web/js/aio/save_settings_dialog.js"));
const settingsModule = await import(dataModule("../web/js/aio/settings.js"));
assert.deepEqual(
  Object.keys(saveDialogModule),
  ["aioCreateSaveSettingsDialog"],
  "Save settings dialog must expose only its lifecycle factory",
);

function configuredSettings() {
  return {
    save: {
      enabled: true,
      backend: "image_saver",
      future_save_key: "keep-save",
      image_saver: {
        filename: "configured-name",
        path: "Configured/Path",
        extension: "png",
        quality_jpeg_or_webp: 88,
        lossless_webp: true,
        optimize_png: false,
        counter: 7,
        clip_skip: -2,
        time_format: "%Y-custom",
        embed_workflow: false,
        save_workflow_as_json: true,
        save_prompt_metadata: false,
        additional_hashes: "Base:AAAA",
        additional_hash_bundles: '["  constructor:HASH,  ","","ModelB:BBBB:0.8"]',
        civitai_hash_fetchers: '[{"enabled":"false","username":" user-a ","model_name":" Model A ","version":" v1 ","constructor":"ignore","toString":"ignore","__proto__":"ignore"},{"enabled":true,"username":"user-b","model_name":"Model B","version":""}]',
        download_civitai_data: false,
        easy_remix: false,
        custom: "configured metadata",
        future_image_saver_key: "drop-on-apply",
      },
    },
    future_root_key: "keep-root",
  };
}

function createFixture({ settings = {}, available = {}, deferLoads = false } = {}) {
  let dependencyCalls = 0;
  let currentDialog = null;
  const dialogs = [];
  const loadCalls = [];
  const loadResolvers = [];
  const notifications = [];
  const writes = [];
  const renders = [];
  const visibleApplies = [];
  const document = createFakeDocument();
  const availabilityState = { ...available };
  const defaultSettings = clone(settingsModule.AIO_DEFAULT_GENERATION_SETTINGS);
  const node = {
    settings: settingsModule.aioMergeDefaults(defaultSettings, settings),
    widgets: [{ name: "generation_settings", value: "" }],
    visibleSettings: null,
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

  function numberInput(value, step = "1") {
    dependencyCalls += 1;
    const input = document.createElement("input");
    input.type = "number";
    input.step = step;
    input.value = String(value ?? "");
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

  function applyTooltipText(element, value) {
    dependencyCalls += 1;
    element.title = String(value ?? "");
    return element;
  }

  function mergeDefaults(defaults, current) {
    dependencyCalls += 1;
    if (currentDialog) {
      currentDialog.trace.push("merge");
    }
    return settingsModule.aioMergeDefaults(defaults, current);
  }

  function findWidget(targetNode, name) {
    dependencyCalls += 1;
    return targetNode.widgets?.find((widget) => widget.name === name);
  }

  function getSettings(targetNode) {
    dependencyCalls += 1;
    return clone(targetNode.settings);
  }

  function applyVisibleSettings(targetNode, nextSettings) {
    dependencyCalls += 1;
    const snapshot = clone(nextSettings);
    targetNode.visibleSettings = snapshot;
    visibleApplies.push(snapshot);
    currentDialog.trace.push("apply-visible");
  }

  function writeSettings(targetNode, widget, nextSettings) {
    dependencyCalls += 1;
    const snapshot = clone(nextSettings);
    targetNode.settings = snapshot;
    widget.value = JSON.stringify(snapshot);
    writes.push(snapshot);
    currentDialog.trace.push("write");
  }

  function renderPanel(targetNode) {
    dependencyCalls += 1;
    renders.push(targetNode);
    currentDialog.trace.push("render");
  }

  const openSaveSettings = saveDialogModule.aioCreateSaveSettingsDialog({
    document,
    controls: {
      createDialog,
      field,
      checkbox,
      selectInput,
      textInput,
      numberInput,
      textareaInput,
    },
    text: {
      staticText,
      get: text,
      format,
      applyTooltip,
      applyTooltipText,
    },
    settingsCore: {
      defaultGenerationSettings: defaultSettings,
      asBool(value, fallback) {
        dependencyCalls += 1;
        return settingsModule.aioAsBool(value, fallback);
      },
      mergeDefaults,
    },
    nodeAdapter: {
      generatorSettingsWidget: "generation_settings",
      findWidget,
      getSettings,
      applyVisibleSettings,
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
          return Promise.resolve();
        }
        return new Promise((resolve) => loadResolvers.push(resolve));
      },
    },
  });

  return {
    openSaveSettings,
    document,
    node,
    defaultSettings,
    dialogs,
    loadCalls,
    availabilityState,
    notifications,
    writes,
    renders,
    visibleApplies,
    dependencyCallCount: () => dependencyCalls,
    resolveLoads() {
      for (const resolve of loadResolvers.splice(0)) {
        resolve();
      }
    },
  };
}

{
  const fixture = createFixture({ settings: configuredSettings() });
  const originalSettings = clone(fixture.node.settings);
  const originalWidget = fixture.node.widgets[0].value;
  assert.equal(fixture.dependencyCallCount(), 0, "Factory composition must be side-effect free");
  assert.equal(fixture.dialogs.length, 0);
  assert.equal(fixture.writes.length, 0);
  assert.equal(fixture.renders.length, 0);
  assert.equal(fixture.document.createdElements.length, 0, "Factory composition must not create DOM elements");
  assert.equal(fixture.document.body.children.length, 0, "Factory composition must not attach DOM elements");

  fixture.openSaveSettings(fixture.node);
  await flushPromises();
  const dialog = fixture.dialogs[0];
  assert.equal(dialog.title, "Save Options");
  assert.equal(
    dialog.subtitle,
    "EasyUse native output saves A1111 metadata and ComfyUI workflows in PNG, JPEG, and WebP.",
  );
  assert.ok(dialog.body.classList.contains("easyuse-anima-aio-save-body"));
  const main = sectionByHeading(dialog.body, "Save Backend");
  const files = sectionByHeading(dialog.body, "Native Image Files");
  const metadata = sectionByHeading(dialog.body, "Native Image Metadata");
  assert.equal(controlIn(main, "Save image").checked, true);
  assert.equal(controlIn(main, "Backend").value, "image_saver");
  assert.equal(controlIn(files, "Filename").value, "configured-name");
  assert.equal(controlIn(files, "JPEG/WebP quality").value, "88");
  assert.equal(controlIn(metadata, "Custom metadata").value, "configured metadata");

  const hashEditor = controlIn(metadata, "Manual hash bundles");
  assert.deepEqual(
    hashRows(hashEditor).map((row) => hashValue(row).value),
    ["constructor:HASH", "ModelB:BBBB:0.8"],
    "JSON-string hash bundles must hydrate, trim edge punctuation, and drop blank rows",
  );
  const civitaiEditor = controlIn(metadata, "Civitai Hash Fetchers");
  assert.equal(civitaiRows(civitaiEditor).length, 2);
  const firstCivitaiInputs = civitaiInputs(civitaiRows(civitaiEditor)[0]);
  assert.equal(firstCivitaiInputs[0].checked, false);
  assert.deepEqual(
    firstCivitaiInputs.slice(1).map((input) => input.value),
    ["user-a", "Model A", "v1"],
    "JSON-string Civitai rows must hydrate only the fixed visible fields",
  );
  assert.equal(
    find(civitaiRows(civitaiEditor)[0], (element) => (
      element.classList.contains("easyuse-anima-aio-civitai-fetcher-preview")
    )).textContent,
    'format:text.civitaiHashPreview:{"model":"Model A"}',
  );

  hashValue(hashRows(hashEditor)[0]).value = "cancelled:HASH";
  addRow(hashEditor, "button.addHashBundle");
  hashValue(hashRows(hashEditor).at(-1)).value = "cancelled-new:HASH";
  removeRow(hashRows(hashEditor)[1]);
  assert.deepEqual(
    hashRows(hashEditor).map((row) => hashValue(row).value),
    ["cancelled:HASH", "cancelled-new:HASH"],
    "Hash remove must detach exactly the selected row",
  );

  firstCivitaiInputs[0].checked = true;
  firstCivitaiInputs[2].value = "Cancelled Model";
  firstCivitaiInputs[2].emit("input");
  assert.equal(
    find(civitaiRows(civitaiEditor)[0], (element) => (
      element.classList.contains("easyuse-anima-aio-civitai-fetcher-preview")
    )).textContent,
    'format:text.civitaiHashPreview:{"model":"Cancelled Model"}',
  );
  addRow(civitaiEditor, "button.addCivitaiFetcher");
  const cancelledNewInputs = civitaiInputs(civitaiRows(civitaiEditor).at(-1));
  cancelledNewInputs[1].value = "cancelled-user";
  cancelledNewInputs[2].value = "cancelled-model";
  removeRow(civitaiRows(civitaiEditor)[1]);
  assert.deepEqual(
    civitaiRows(civitaiEditor).map((row) => civitaiInputs(row)[1].value),
    ["user-a", "cancelled-user"],
    "Civitai remove must detach exactly the selected row",
  );
  controlIn(files, "Filename").value = "cancelled-name";

  action(dialog, "button.cancel").emit("click");
  assert.deepEqual(fixture.node.settings, originalSettings, "Cancel must not mutate settings");
  assert.equal(fixture.node.widgets[0].value, originalWidget, "Cancel must not rewrite the hidden widget");
  assert.equal(fixture.writes.length, 0);
  assert.equal(fixture.renders.length, 0);
  assert.equal(fixture.visibleApplies.length, 0);
  assert.deepEqual(dialog.trace, ["remove"]);
}

{
  const fixture = createFixture({
    settings: configuredSettings(),
    available: { imageSaver: true },
    deferLoads: true,
  });
  assert.equal(fixture.dependencyCallCount(), 0, "Deferred fixture factory must also be side-effect free");
  fixture.openSaveSettings(fixture.node);
  const dialog = fixture.dialogs[0];
  const main = sectionByHeading(dialog.body, "Save Backend");
  const files = sectionByHeading(dialog.body, "Native Image Files");
  const metadata = sectionByHeading(dialog.body, "Native Image Metadata");
  const backend = controlIn(main, "Backend");
  const nativeOption = backend.options.find((option) => option.value === "image_saver");
  assert.ok(nativeOption);
  assert.equal(nativeOption.disabled, false);
  assert.equal(nativeOption.textContent, "EasyUse Native");
  assert.equal(backend.value, "image_saver");
  assert.equal(fixture.loadCalls.length, 0, "Native output must not query optional node packs");
  fixture.resolveLoads();
  await flushPromises();
  assert.equal(backend.value, "image_saver");
  assert.deepEqual(fixture.notifications, []);
  backend.value = "comfy_save_image";

  controlIn(main, "Save image").checked = false;
  controlIn(files, "Filename").value = "";
  controlIn(files, "Path").value = "";
  controlIn(files, "Extension").value = "jpeg";
  controlIn(files, "JPEG/WebP quality").value = "";
  controlIn(files, "Lossless WebP").checked = false;
  controlIn(files, "Optimize PNG").checked = true;
  controlIn(files, "Counter").value = "";
  controlIn(metadata, "Time format").value = "";
  controlIn(metadata, "Clip skip").value = "";
  controlIn(metadata, "Embed workflow").checked = true;
  controlIn(metadata, "Workflow JSON").checked = false;
  controlIn(metadata, "Save prompt metadata").checked = true;
  controlIn(metadata, "Additional hashes").value = "Base:UPDATED";
  controlIn(metadata, "Civitai data").checked = true;
  controlIn(metadata, "Easy remix").checked = true;
  controlIn(metadata, "Custom metadata").value = "updated metadata";

  const hashEditor = controlIn(metadata, "Manual hash bundles");
  hashValue(hashRows(hashEditor)[1]).value = "  Updated:BBBB,  ";
  addRow(hashEditor, "button.addHashBundle");
  hashValue(hashRows(hashEditor).at(-1)).value = "Third:CCCC";
  addRow(hashEditor, "button.addHashBundle");

  const civitaiEditor = controlIn(metadata, "Civitai Hash Fetchers");
  const secondInputs = civitaiInputs(civitaiRows(civitaiEditor)[1]);
  secondInputs[1].value = " user-b-updated ";
  secondInputs[2].value = " Model B Updated ";
  secondInputs[3].value = " v2 ";
  addRow(civitaiEditor, "button.addCivitaiFetcher");
  const thirdInputs = civitaiInputs(civitaiRows(civitaiEditor).at(-1));
  thirdInputs[0].checked = false;
  thirdInputs[1].value = "user-c";
  thirdInputs[2].value = "Model C";
  thirdInputs[3].value = "v3";
  addRow(civitaiEditor, "button.addCivitaiFetcher");

  action(dialog, "button.apply").emit("click");
  assert.deepEqual(dialog.trace, ["merge", "apply-visible", "write", "render", "remove"]);
  assert.equal(fixture.visibleApplies.length, 1);
  assert.equal(fixture.writes.length, 1);
  assert.equal(fixture.renders.length, 1);
  assert.equal(fixture.node.settings.future_root_key, "keep-root");
  assert.equal(fixture.node.settings.save.future_save_key, "keep-save");
  assert.equal(fixture.node.settings.save.enabled, false);
  assert.equal(fixture.node.settings.save.backend, "comfy_save_image");

  const imageSaver = fixture.node.settings.save.image_saver;
  assert.deepEqual(
    Object.keys(imageSaver),
    [
      "filename",
      "path",
      "extension",
      "lossless_webp",
      "quality_jpeg_or_webp",
      "optimize_png",
      "counter",
      "clip_skip",
      "time_format",
      "save_workflow_as_json",
      "embed_workflow",
      "save_prompt_metadata",
      "additional_hashes",
      "additional_hash_bundles",
      "civitai_hash_fetchers",
      "download_civitai_data",
      "easy_remix",
      "custom",
    ],
    "Apply must replace Image Saver settings with the fixed schema and stable key order",
  );
  assert.equal(imageSaver.filename, "%time_%basemodelname");
  assert.equal(imageSaver.path, "EasyUseAnima/AiO");
  assert.equal(imageSaver.extension, "jpeg");
  assert.equal(imageSaver.quality_jpeg_or_webp, 97);
  assert.equal(imageSaver.counter, 0);
  assert.equal(imageSaver.clip_skip, 0);
  assert.equal(imageSaver.time_format, "%Y-%m-%d-%H%M%S");
  assert.equal(imageSaver.lossless_webp, false);
  assert.equal(imageSaver.optimize_png, true);
  assert.equal(imageSaver.embed_workflow, true);
  assert.equal(imageSaver.save_workflow_as_json, false);
  assert.equal(imageSaver.save_prompt_metadata, true);
  assert.equal(imageSaver.additional_hashes, "Base:UPDATED");
  assert.equal(imageSaver.download_civitai_data, true);
  assert.equal(imageSaver.easy_remix, true);
  assert.equal(imageSaver.custom, "updated metadata");
  assert.deepEqual(
    imageSaver.additional_hash_bundles,
    ["constructor:HASH", "Updated:BBBB", "Third:CCCC"],
    "Hash bundle serialization must preserve content order, including a literal constructor hash",
  );
  assert.deepEqual(
    imageSaver.civitai_hash_fetchers,
    [
      { enabled: false, username: "user-a", model_name: "Model A", version: "v1" },
      { enabled: true, username: "user-b-updated", model_name: "Model B Updated", version: "v2" },
      { enabled: false, username: "user-c", model_name: "Model C", version: "v3" },
    ],
    "Civitai serialization must trim, filter blank rows, and preserve visible row order",
  );
  for (const fetcher of imageSaver.civitai_hash_fetchers) {
    assert.deepEqual(
      Object.keys(fetcher),
      ["enabled", "username", "model_name", "version"],
      "Civitai rows must serialize only the fixed allowlist",
    );
    assert.equal(Object.hasOwn(fetcher, "constructor"), false);
    assert.equal(Object.hasOwn(fetcher, "toString"), false);
    assert.equal(Object.hasOwn(fetcher, "__proto__"), false);
  }
  assert.equal(
    Object.hasOwn(imageSaver, "future_image_saver_key"),
    false,
    "Unknown Image Saver siblings must be removed by fixed-schema serialization",
  );
  assert.deepEqual(fixture.visibleApplies[0], fixture.node.settings);
  assert.deepEqual(fixture.writes[0], fixture.node.settings);
  assert.deepEqual(JSON.parse(fixture.node.widgets[0].value), fixture.node.settings);
}

console.log("AiO Save settings dialog smoke passed.");
