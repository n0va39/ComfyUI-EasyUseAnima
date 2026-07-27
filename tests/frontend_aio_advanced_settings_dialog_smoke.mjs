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

function sectionByHeading(root, heading) {
  const title = findByText(root, `static:${heading}`);
  assert.ok(title?.parentElement, `missing section: ${heading}`);
  assert.equal(title.tagName, "H3", `expected section heading for: ${heading}`);
  return title.parentElement;
}

function subsectionByHeading(root, heading) {
  const title = findByText(root, `static:${heading}`);
  assert.ok(title?.parentElement, `missing subsection: ${heading}`);
  assert.equal(title.tagName, "H4", `expected subsection heading for: ${heading}`);
  return title.parentElement;
}

function action(dialog, key) {
  const button = findByText(dialog.actions, `text:${key}`);
  assert.ok(button, `missing action: ${key}`);
  return button;
}

function assertValues(entries) {
  for (const [root, label, expected] of entries) {
    assert.equal(controlIn(root, label).value, String(expected), `unexpected value for: ${label}`);
  }
}

function assertChecked(entries) {
  for (const [root, label, expected] of entries) {
    assert.equal(controlIn(root, label).checked, expected, `unexpected checked state for: ${label}`);
  }
}

function assertDisabled(entries, expected = true) {
  for (const [root, label] of entries) {
    assert.equal(controlIn(root, label).disabled, expected, `unexpected disabled state for: ${label}`);
  }
}

async function flushPromises() {
  await Promise.resolve();
  await Promise.resolve();
}

const advancedDialogModule = await import(dataModule("../web/js/aio/advanced_settings_dialog.js"));
const settingsModule = await import(dataModule("../web/js/aio/settings.js"));
assert.deepEqual(
  Object.keys(advancedDialogModule),
  ["aioCreateAdvancedSettingsDialog"],
  "Advanced settings dialog must expose only its lifecycle factory",
);

function configuredSettings() {
  return {
    sampler: {
      dave: { legacy: true },
      future_sampler_key: "keep-sampler",
    },
    model_patches: {
      future_model_patch_key: "keep-model-patches",
      aura_flow: {
        enabled: true,
        shift: 6.5,
        future_aura_key: "keep-aura",
      },
      dave: {
        enabled: true,
        mask: "configured-dave.npz",
        strength: 0.42,
        tau: 0.21,
        stage_scope: {
          first_pass: true,
          highres: true,
          detailer: false,
          upscale: true,
        },
        future_dave_key: "keep-dave",
      },
      safe_pag: {
        enabled: true,
        scale: 5.5,
        block_indices: "3, 7",
        perturbation_strength: 0.35,
        head_indices: "1, 2",
        start_percent: 0.1,
        end_percent: 0.9,
        rescale: 0.4,
        rescale_mode: "partial",
        future_safe_pag_key: "keep-safe-pag",
      },
      kj: {
        fp16_accumulation: true,
        sage_attention: "auto",
        sage_allow_compile: true,
        future_kj_key: "keep-kj",
        torch_compile: {
          enabled: true,
          backend: "configured-backend",
          fullgraph: true,
          mode: "reduce-overhead",
          dynamic: "default",
          compile_transformer_blocks_only: false,
          dynamo_cache_size_limit: 128,
          debug_compile_keys: true,
          disable_dynamic_vram: false,
          future_torch_key: "keep-torch",
        },
      },
    },
    artist_mix: {
      mode: "exact",
      start_percent: 0.2,
      strength_scale: 1.4,
      future_artist_key: "keep-artist",
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
  const mergeCalls = [];
  const clampCalls = [];
  const writes = [];
  const renders = [];
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

  function mergeDefaults(defaults, current) {
    dependencyCalls += 1;
    mergeCalls.push({ defaults: clone(defaults), current: clone(current) });
    if (currentDialog) {
      currentDialog.trace.push("merge");
    }
    return settingsModule.aioMergeDefaults(defaults, current);
  }

  function clampNumber(value, fallback, min, max) {
    dependencyCalls += 1;
    clampCalls.push([value, fallback, min, max]);
    const parsed = Number(value);
    const next = Number.isFinite(parsed) ? parsed : fallback;
    return Math.max(min, Math.min(max, next));
  }

  function findWidget(targetNode, name) {
    dependencyCalls += 1;
    return targetNode.widgets?.find((widget) => widget.name === name);
  }

  function getSettings(targetNode) {
    dependencyCalls += 1;
    return clone(targetNode.settings);
  }

  function writeSettings(targetNode, widget, nextSettings) {
    dependencyCalls += 1;
    const snapshot = clone(nextSettings);
    targetNode.settings = snapshot;
    widget.value = JSON.stringify(snapshot);
    writes.push({ node: targetNode, widget, settings: snapshot });
    currentDialog.trace.push("write");
  }

  function renderPanel(targetNode) {
    dependencyCalls += 1;
    renders.push(targetNode);
    currentDialog.trace.push("render");
  }

  const openAdvancedSettings = advancedDialogModule.aioCreateAdvancedSettingsDialog({
    document,
    controls: {
      createDialog,
      field,
      numberInput,
      checkbox,
      textInput,
      selectInput,
    },
    text: {
      staticText,
      get: text,
      format,
    },
    settingsCore: {
      defaultGenerationSettings: defaultSettings,
      mergeDefaults,
      clampNumber,
    },
    nodeAdapter: {
      generatorSettingsWidget: "generation_settings",
      findWidget,
      getSettings,
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
    openAdvancedSettings,
    document,
    node,
    defaultSettings,
    dialogs,
    loadCalls,
    availabilityState,
    notifications,
    mergeCalls,
    clampCalls,
    writes,
    renders,
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
  const originalDefaults = clone(fixture.defaultSettings);
  assert.equal(fixture.dependencyCallCount(), 0, "Factory composition must be side-effect free");
  assert.equal(fixture.dialogs.length, 0);
  assert.equal(fixture.loadCalls.length, 0);
  assert.equal(fixture.mergeCalls.length, 0);
  assert.equal(fixture.writes.length, 0);
  assert.equal(fixture.renders.length, 0);
  assert.equal(fixture.document.createdElements.length, 0, "Factory composition must not create DOM elements");
  assert.equal(fixture.document.body.children.length, 0, "Factory composition must not attach DOM elements");

  fixture.openAdvancedSettings(fixture.node);
  await flushPromises();
  const cancelDialog = fixture.dialogs[0];
  assert.equal(cancelDialog.title, "Advanced Options");
  assert.equal(
    cancelDialog.subtitle,
    "Advanced generation options stay in a popup and are serialized as versioned settings.",
  );
  const modelPatches = sectionByHeading(cancelDialog.body, "Model Patch / Optimization");
  const artistMix = sectionByHeading(cancelDialog.body, "Artist Mix");
  const dave = subsectionByHeading(modelPatches, "Anima DAVE");
  const daveCustomStages = subsectionByHeading(dave, "Custom DAVE stages");
  const safePag = subsectionByHeading(modelPatches, "Anima Safe PAG");
  const kj = subsectionByHeading(modelPatches, "KJNodes Optimization");
  const sage = subsectionByHeading(kj, "SageAttention (KJNodes)");
  const torch = subsectionByHeading(kj, "Torch Compile (KJNodes)");
  const torchDetails = subsectionByHeading(torch, "Torch Compile Parameters");
  const warning = find(
    modelPatches,
    (element) => element.classList.contains("easyuse-anima-aio-warning"),
  );
  assert.ok(warning);
  assert.equal(warning.hidden, true);
  assert.equal(warning.textContent, "");
  assert.equal(fixture.loadCalls.length, 1);

  assertValues([
    [modelPatches, "AuraFlow shift", 6.5],
    [dave, "Mask", "configured-dave.npz"],
    [dave, "DAVE strength", 0.42],
    [dave, "DAVE tau", 0.21],
    [dave, "DAVE stages", "custom"],
    [safePag, "Safe PAG scale", 5.5],
    [safePag, "Safe PAG blocks", "3, 7"],
    [safePag, "PAG perturbation", 0.35],
    [safePag, "PAG heads", "1, 2"],
    [safePag, "PAG start percent", 0.1],
    [safePag, "PAG end percent", 0.9],
    [safePag, "PAG rescale", 0.4],
    [safePag, "PAG rescale mode", "partial"],
    [sage, "Mode", "auto"],
    [torchDetails, "Backend", "configured-backend"],
    [torchDetails, "Mode", "reduce-overhead"],
    [torchDetails, "Dynamic", "default"],
    [torchDetails, "Dynamo cache limit", 128],
    [artistMix, "Mode", "exact"],
    [artistMix, "Start", 0.2],
    [artistMix, "Strength", 1.4],
  ]);
  assertChecked([
    [dave, "Use DAVE", true],
    [daveCustomStages, "First pass", true],
    [daveCustomStages, "Highres", true],
    [daveCustomStages, "Detailer", false],
    [daveCustomStages, "Upscale (USDU)", true],
    [safePag, "Use Safe PAG", true],
    [kj, "KJNodes FP16 accum", true],
    [sage, "Allow compile", true],
    [torch, "Use Torch compile", true],
    [torchDetails, "Fullgraph", true],
    [torchDetails, "Transformer blocks only", false],
    [torchDetails, "Debug keys", true],
    [torchDetails, "Disable dynamic VRAM", false],
  ]);
  assert.equal(controlIn(modelPatches, "AuraFlow shift").min, "1");
  assert.equal(controlIn(modelPatches, "AuraFlow shift").max, "10");
  assert.equal(controlIn(safePag, "Safe PAG scale").min, "0");
  assert.equal(controlIn(safePag, "Safe PAG scale").max, "100");
  assert.equal(rowByLabel(sage, "Allow compile").style.display, "");
  assert.equal(torchDetails.style.display, "");
  assert.equal(daveCustomStages.style.display, "");

  const sageMode = controlIn(sage, "Mode");
  sageMode.value = "disabled";
  sageMode.emit("change");
  assert.equal(rowByLabel(sage, "Allow compile").style.display, "none");
  sageMode.value = "auto";
  sageMode.emit("change");
  assert.equal(rowByLabel(sage, "Allow compile").style.display, "");
  const torchEnabled = controlIn(torch, "Use Torch compile");
  torchEnabled.checked = false;
  torchEnabled.emit("change");
  assert.equal(torchDetails.style.display, "none");
  torchEnabled.checked = true;
  torchEnabled.emit("change");
  assert.equal(torchDetails.style.display, "");

  controlIn(modelPatches, "AuraFlow shift").value = "9";
  controlIn(dave, "Use DAVE").checked = false;
  controlIn(dave, "DAVE stages").value = "all_sampling_stages";
  controlIn(dave, "DAVE stages").emit("change");
  assert.equal(daveCustomStages.style.display, "none");
  controlIn(safePag, "PAG rescale mode").value = "full";
  controlIn(kj, "KJNodes FP16 accum").checked = false;
  sageMode.value = "disabled";
  sageMode.emit("change");
  torchEnabled.checked = false;
  torchEnabled.emit("change");
  controlIn(artistMix, "Start").value = "0.9";
  action(cancelDialog, "button.cancel").emit("click");
  assert.deepEqual(cancelDialog.trace, ["remove"]);
  assert.deepEqual(fixture.node.settings, originalSettings, "Cancel must not mutate node settings");
  assert.equal(fixture.node.widgets[0].value, originalWidget, "Cancel must not rewrite the hidden widget");
  assert.deepEqual(fixture.defaultSettings, originalDefaults, "Cancel must not mutate injected defaults");
  assert.equal(fixture.mergeCalls.length, 0);
  assert.equal(fixture.writes.length, 0);
  assert.equal(fixture.renders.length, 0);

  fixture.openAdvancedSettings(fixture.node);
  await flushPromises();
  const applyDialog = fixture.dialogs[1];
  const applyModelPatches = sectionByHeading(applyDialog.body, "Model Patch / Optimization");
  const applyArtistMix = sectionByHeading(applyDialog.body, "Artist Mix");
  const applyDave = subsectionByHeading(applyModelPatches, "Anima DAVE");
  const applyDaveCustomStages = subsectionByHeading(applyDave, "Custom DAVE stages");
  const applySafePag = subsectionByHeading(applyModelPatches, "Anima Safe PAG");
  const applyKj = subsectionByHeading(applyModelPatches, "KJNodes Optimization");
  const applySage = subsectionByHeading(applyKj, "SageAttention (KJNodes)");
  const applyTorch = subsectionByHeading(applyKj, "Torch Compile (KJNodes)");
  const applyTorchDetails = subsectionByHeading(applyTorch, "Torch Compile Parameters");

  controlIn(applyModelPatches, "AuraFlow shift").value = "99";
  controlIn(applyDave, "Use DAVE").checked = true;
  const applyDaveStagePreset = controlIn(applyDave, "DAVE stages");
  applyDaveStagePreset.value = "all_sampling_stages";
  applyDaveStagePreset.emit("change");
  assert.equal(applyDaveCustomStages.style.display, "none");
  controlIn(applyDave, "Mask").value = "";
  controlIn(applyDave, "DAVE strength").value = "0";
  controlIn(applyDave, "DAVE tau").value = "";
  controlIn(applySafePag, "Use Safe PAG").checked = true;
  controlIn(applySafePag, "Safe PAG scale").value = "101";
  controlIn(applySafePag, "Safe PAG blocks").value = "";
  controlIn(applySafePag, "PAG perturbation").value = "-1";
  controlIn(applySafePag, "PAG heads").value = "2, 4";
  controlIn(applySafePag, "PAG start percent").value = "2";
  controlIn(applySafePag, "PAG end percent").value = "-1";
  controlIn(applySafePag, "PAG rescale").value = "2";
  controlIn(applySafePag, "PAG rescale mode").value = "";
  controlIn(applyKj, "KJNodes FP16 accum").checked = true;
  const applySageMode = controlIn(applySage, "Mode");
  applySageMode.value = "sageattn";
  applySageMode.emit("change");
  controlIn(applySage, "Allow compile").checked = true;
  const applyTorchEnabled = controlIn(applyTorch, "Use Torch compile");
  applyTorchEnabled.checked = true;
  applyTorchEnabled.emit("change");
  controlIn(applyTorchDetails, "Backend").value = "";
  controlIn(applyTorchDetails, "Fullgraph").checked = false;
  controlIn(applyTorchDetails, "Mode").value = "";
  controlIn(applyTorchDetails, "Dynamic").value = "";
  controlIn(applyTorchDetails, "Transformer blocks only").checked = true;
  controlIn(applyTorchDetails, "Dynamo cache limit").value = "";
  controlIn(applyTorchDetails, "Debug keys").checked = false;
  controlIn(applyTorchDetails, "Disable dynamic VRAM").checked = true;
  controlIn(applyArtistMix, "Mode").value = "";
  controlIn(applyArtistMix, "Start").value = "0";
  controlIn(applyArtistMix, "Strength").value = "";

  action(applyDialog, "button.apply").emit("click");
  assert.deepEqual(applyDialog.trace, ["merge", "write", "render", "remove"]);
  assert.equal(fixture.mergeCalls.length, 1);
  assert.equal(fixture.writes.length, 1);
  assert.equal(fixture.renders.length, 1);
  assert.equal(fixture.writes[0].node, fixture.node);
  assert.equal(fixture.writes[0].widget, fixture.node.widgets[0]);
  assert.equal(fixture.renders[0], fixture.node);
  assert.deepEqual(
    fixture.clampCalls,
    [
      ["99", 3, 1, 10],
      ["101", 4, 0, 100],
      ["-1", 0.75, 0, 1],
      ["2", 0, 0, 1],
      ["-1", 0.7, 0, 1],
      ["2", 0.2, 0, 1],
    ],
    "Apply must preserve the exact clamp inputs, defaults, and bounds",
  );

  const written = fixture.node.settings;
  assert.equal(written.model_patches.aura_flow.shift, 10);
  assert.equal(Object.hasOwn(written.model_patches.aura_flow, "enabled"), false);
  assert.deepEqual(
    {
      enabled: written.model_patches.dave.enabled,
      mask: written.model_patches.dave.mask,
      strength: written.model_patches.dave.strength,
      tau: written.model_patches.dave.tau,
      stage_scope: written.model_patches.dave.stage_scope,
    },
    {
      enabled: true,
      mask: "dave_alpha.npz",
      strength: 0,
      tau: 0.1,
      stage_scope: {
        first_pass: true,
        highres: true,
        detailer: true,
        upscale: true,
      },
    },
  );
  assert.deepEqual(
    {
      enabled: written.model_patches.safe_pag.enabled,
      scale: written.model_patches.safe_pag.scale,
      block_indices: written.model_patches.safe_pag.block_indices,
      perturbation_strength: written.model_patches.safe_pag.perturbation_strength,
      head_indices: written.model_patches.safe_pag.head_indices,
      start_percent: written.model_patches.safe_pag.start_percent,
      end_percent: written.model_patches.safe_pag.end_percent,
      rescale: written.model_patches.safe_pag.rescale,
      rescale_mode: written.model_patches.safe_pag.rescale_mode,
    },
    {
      enabled: true,
      scale: 100,
      block_indices: "18",
      perturbation_strength: 0,
      head_indices: "2, 4",
      start_percent: 1,
      end_percent: 0,
      rescale: 1,
      rescale_mode: "full",
    },
  );
  assert.equal(written.model_patches.kj.fp16_accumulation, true);
  assert.equal(written.model_patches.kj.sage_attention, "sageattn");
  assert.equal(written.model_patches.kj.sage_allow_compile, true);
  assert.deepEqual(
    {
      enabled: written.model_patches.kj.torch_compile.enabled,
      backend: written.model_patches.kj.torch_compile.backend,
      fullgraph: written.model_patches.kj.torch_compile.fullgraph,
      mode: written.model_patches.kj.torch_compile.mode,
      dynamic: written.model_patches.kj.torch_compile.dynamic,
      compile_transformer_blocks_only: (
        written.model_patches.kj.torch_compile.compile_transformer_blocks_only
      ),
      dynamo_cache_size_limit: written.model_patches.kj.torch_compile.dynamo_cache_size_limit,
      debug_compile_keys: written.model_patches.kj.torch_compile.debug_compile_keys,
      disable_dynamic_vram: written.model_patches.kj.torch_compile.disable_dynamic_vram,
    },
    {
      enabled: true,
      backend: "inductor",
      fullgraph: false,
      mode: "max-autotune-no-cudagraphs",
      dynamic: "false",
      compile_transformer_blocks_only: true,
      dynamo_cache_size_limit: 64,
      debug_compile_keys: false,
      disable_dynamic_vram: true,
    },
  );
  assert.equal(written.artist_mix.mode, "prompt_data");
  assert.equal(written.artist_mix.start_percent, 0, "String zero must remain a valid Artist Mix start");
  assert.equal(written.artist_mix.strength_scale, 1);
  assert.equal(Object.hasOwn(written.sampler, "dave"), false, "Apply must remove legacy sampler.dave");
  assert.equal(written.future_root_key, "keep-root");
  assert.equal(written.sampler.future_sampler_key, "keep-sampler");
  assert.equal(written.model_patches.future_model_patch_key, "keep-model-patches");
  assert.equal(written.model_patches.aura_flow.future_aura_key, "keep-aura");
  assert.equal(written.model_patches.dave.future_dave_key, "keep-dave");
  assert.equal(written.model_patches.safe_pag.future_safe_pag_key, "keep-safe-pag");
  assert.equal(written.model_patches.kj.future_kj_key, "keep-kj");
  assert.equal(written.model_patches.kj.torch_compile.future_torch_key, "keep-torch");
  assert.equal(written.artist_mix.future_artist_key, "keep-artist");
  assert.deepEqual(fixture.writes[0].settings, written);
  assert.deepEqual(JSON.parse(fixture.node.widgets[0].value), written);
  assert.deepEqual(fixture.defaultSettings, originalDefaults, "Apply must not mutate injected defaults");
}

{
  const fresh = createFixture();
  fresh.openAdvancedSettings(fresh.node);
  await flushPromises();
  const dialog = fresh.dialogs[0];
  const modelPatches = sectionByHeading(dialog.body, "Model Patch / Optimization");
  const dave = subsectionByHeading(modelPatches, "Anima DAVE");
  const customStages = subsectionByHeading(dave, "Custom DAVE stages");
  assert.equal(controlIn(dave, "DAVE stages").value, "first_pass_only");
  assert.equal(customStages.style.display, "none");
}

{
  const custom = createFixture({ settings: configuredSettings() });
  custom.openAdvancedSettings(custom.node);
  await flushPromises();
  const dialog = custom.dialogs[0];
  const modelPatches = sectionByHeading(dialog.body, "Model Patch / Optimization");
  const dave = subsectionByHeading(modelPatches, "Anima DAVE");
  const customStages = subsectionByHeading(dave, "Custom DAVE stages");
  assert.equal(controlIn(dave, "DAVE stages").value, "custom");
  controlIn(customStages, "First pass").checked = false;
  controlIn(customStages, "Highres").checked = true;
  controlIn(customStages, "Detailer").checked = true;
  controlIn(customStages, "Upscale (USDU)").checked = false;
  action(dialog, "button.apply").emit("click");
  assert.deepEqual(custom.node.settings.model_patches.dave.stage_scope, {
    first_pass: false,
    highres: true,
    detailer: true,
    upscale: false,
  });
}

for (const dependencyCase of [
  { key: "dave", backend: "Anima DAVE" },
  { key: "safePag", backend: "Anima Safe PAG" },
  { key: "kjFp16", backend: "KJNodes FP16 accum" },
  { key: "kjSage", backend: "SageAttention" },
  { key: "kjTorchCompile", backend: "Torch Compile" },
]) {
  const fixture = createFixture({
    settings: configuredSettings(),
    available: {
      dave: true,
      safePag: true,
      kjFp16: true,
      kjSage: true,
      kjTorchCompile: true,
    },
    deferLoads: true,
  });
  fixture.openAdvancedSettings(fixture.node);
  const dialog = fixture.dialogs[0];
  const modelPatches = sectionByHeading(dialog.body, "Model Patch / Optimization");
  const dave = subsectionByHeading(modelPatches, "Anima DAVE");
  const daveCustomStages = subsectionByHeading(dave, "Custom DAVE stages");
  const safePag = subsectionByHeading(modelPatches, "Anima Safe PAG");
  const kj = subsectionByHeading(modelPatches, "KJNodes Optimization");
  const sage = subsectionByHeading(kj, "SageAttention (KJNodes)");
  const torch = subsectionByHeading(kj, "Torch Compile (KJNodes)");
  const torchDetails = subsectionByHeading(torch, "Torch Compile Parameters");
  const warning = find(
    modelPatches,
    (element) => element.classList.contains("easyuse-anima-aio-warning"),
  );
  assert.ok(warning);
  const controlGroups = {
    dave: [
      [dave, "Use DAVE"],
      [dave, "Mask"],
      [dave, "DAVE strength"],
      [dave, "DAVE tau"],
      [dave, "DAVE stages"],
      [daveCustomStages, "First pass"],
      [daveCustomStages, "Highres"],
      [daveCustomStages, "Detailer"],
      [daveCustomStages, "Upscale (USDU)"],
    ],
    safePag: [
      [safePag, "Use Safe PAG"],
      [safePag, "Safe PAG scale"],
      [safePag, "Safe PAG blocks"],
      [safePag, "PAG perturbation"],
      [safePag, "PAG heads"],
      [safePag, "PAG start percent"],
      [safePag, "PAG end percent"],
      [safePag, "PAG rescale"],
      [safePag, "PAG rescale mode"],
    ],
    kjFp16: [
      [kj, "KJNodes FP16 accum"],
    ],
    kjSage: [
      [sage, "Mode"],
      [sage, "Allow compile"],
    ],
    kjTorchCompile: [
      [torch, "Use Torch compile"],
      [torchDetails, "Backend"],
      [torchDetails, "Fullgraph"],
      [torchDetails, "Mode"],
      [torchDetails, "Dynamic"],
      [torchDetails, "Transformer blocks only"],
      [torchDetails, "Dynamo cache limit"],
      [torchDetails, "Debug keys"],
      [torchDetails, "Disable dynamic VRAM"],
    ],
  };
  assert.equal(fixture.loadCalls.length, 1);
  assert.equal(warning.hidden, true);

  fixture.availabilityState[dependencyCase.key] = false;
  fixture.resolveLoads();
  await flushPromises();

  for (const [groupKey, controls] of Object.entries(controlGroups)) {
    const [primary, ...details] = controls;
    assertDisabled([primary], false);
    assertDisabled(details, groupKey === dependencyCase.key);
  }
  assert.equal(warning.hidden, false);
  assert.equal(
    warning.textContent,
    `format:warning.optionalDependencyMissing:${JSON.stringify({
      backend: dependencyCase.backend,
      pack: `pack:${dependencyCase.key}`,
    })}`,
    `Only ${dependencyCase.key} must contribute its warning`,
  );
  assert.deepEqual(fixture.notifications, [], "Async dependency refresh must stay silent");
  const primaryControls = {
    dave: controlIn(dave, "Use DAVE"),
    safePag: controlIn(safePag, "Use Safe PAG"),
    kjFp16: controlIn(kj, "KJNodes FP16 accum"),
    kjSage: controlIn(sage, "Mode"),
    kjTorchCompile: controlIn(torch, "Use Torch compile"),
  };
  const primary = primaryControls[dependencyCase.key];
  if (dependencyCase.key === "kjSage") {
    primary.value = "auto";
  } else {
    primary.checked = true;
  }
  primary.emit("change");
  assert.deepEqual(fixture.notifications, [{
    backend: dependencyCase.backend,
    keys: [dependencyCase.key],
  }]);
}

{
  const fixture = createFixture({
    settings: configuredSettings(),
    available: {
      dave: true,
      safePag: true,
      kjFp16: true,
      kjSage: true,
      kjTorchCompile: true,
    },
    deferLoads: true,
  });
  assert.equal(fixture.dependencyCallCount(), 0, "Deferred fixture factory must be side-effect free");
  fixture.openAdvancedSettings(fixture.node);
  const dialog = fixture.dialogs[0];
  const modelPatches = sectionByHeading(dialog.body, "Model Patch / Optimization");
  const dave = subsectionByHeading(modelPatches, "Anima DAVE");
  const daveCustomStages = subsectionByHeading(dave, "Custom DAVE stages");
  const safePag = subsectionByHeading(modelPatches, "Anima Safe PAG");
  const kj = subsectionByHeading(modelPatches, "KJNodes Optimization");
  const sage = subsectionByHeading(kj, "SageAttention (KJNodes)");
  const torch = subsectionByHeading(kj, "Torch Compile (KJNodes)");
  const torchDetails = subsectionByHeading(torch, "Torch Compile Parameters");
  const warning = find(
    modelPatches,
    (element) => element.classList.contains("easyuse-anima-aio-warning"),
  );
  assert.ok(warning);
  assert.equal(fixture.loadCalls.length, 1);
  assert.equal(warning.hidden, true);
  assertDisabled([
    [dave, "Use DAVE"],
    [safePag, "Use Safe PAG"],
    [kj, "KJNodes FP16 accum"],
    [sage, "Mode"],
    [torch, "Use Torch compile"],
  ], false);

  for (const key of ["dave", "safePag", "kjFp16", "kjSage", "kjTorchCompile"]) {
    fixture.availabilityState[key] = false;
  }
  fixture.resolveLoads();
  await flushPromises();

  assertDisabled([
    [dave, "Use DAVE"],
    [safePag, "Use Safe PAG"],
    [kj, "KJNodes FP16 accum"],
    [sage, "Mode"],
    [torch, "Use Torch compile"],
  ], false);
  assertDisabled([
    [dave, "Mask"],
    [dave, "DAVE strength"],
    [dave, "DAVE tau"],
    [dave, "DAVE stages"],
    [daveCustomStages, "First pass"],
    [daveCustomStages, "Highres"],
    [daveCustomStages, "Detailer"],
    [daveCustomStages, "Upscale (USDU)"],
    [safePag, "Safe PAG scale"],
    [safePag, "Safe PAG blocks"],
    [safePag, "PAG perturbation"],
    [safePag, "PAG heads"],
    [safePag, "PAG start percent"],
    [safePag, "PAG end percent"],
    [safePag, "PAG rescale"],
    [safePag, "PAG rescale mode"],
    [sage, "Allow compile"],
    [torchDetails, "Backend"],
    [torchDetails, "Fullgraph"],
    [torchDetails, "Mode"],
    [torchDetails, "Dynamic"],
    [torchDetails, "Transformer blocks only"],
    [torchDetails, "Dynamo cache limit"],
    [torchDetails, "Debug keys"],
    [torchDetails, "Disable dynamic VRAM"],
  ], true);
  assertChecked([
    [dave, "Use DAVE", false],
    [safePag, "Use Safe PAG", false],
    [kj, "KJNodes FP16 accum", false],
    [sage, "Allow compile", false],
    [torch, "Use Torch compile", false],
  ]);
  assert.equal(controlIn(sage, "Mode").value, "disabled");
  assert.equal(rowByLabel(sage, "Allow compile").style.display, "none");
  assert.equal(torchDetails.style.display, "none");
  assert.equal(warning.hidden, false);
  assert.equal(
    warning.textContent,
    [
      'format:warning.optionalDependencyMissing:{"backend":"Anima DAVE","pack":"pack:dave"}',
      'format:warning.optionalDependencyMissing:{"backend":"Anima Safe PAG","pack":"pack:safePag"}',
      'format:warning.optionalDependencyMissing:{"backend":"KJNodes FP16 accum","pack":"pack:kjFp16"}',
      'format:warning.optionalDependencyMissing:{"backend":"SageAttention","pack":"pack:kjSage"}',
      'format:warning.optionalDependencyMissing:{"backend":"Torch Compile","pack":"pack:kjTorchCompile"}',
    ].join(" "),
    "Missing dependency warning order and pack mapping must remain stable",
  );

  controlIn(dave, "Use DAVE").checked = true;
  controlIn(safePag, "Use Safe PAG").checked = true;
  controlIn(kj, "KJNodes FP16 accum").checked = true;
  controlIn(sage, "Mode").value = "auto";
  controlIn(sage, "Allow compile").checked = true;
  controlIn(torch, "Use Torch compile").checked = true;
  action(dialog, "button.apply").emit("click");

  assert.deepEqual(dialog.trace, ["merge", "write", "render", "remove"]);
  assert.equal(fixture.writes.length, 1);
  assert.equal(fixture.renders.length, 1);
  assert.equal(fixture.node.settings.model_patches.dave.enabled, false);
  assert.equal(fixture.node.settings.model_patches.safe_pag.enabled, false);
  assert.equal(fixture.node.settings.model_patches.kj.fp16_accumulation, false);
  assert.equal(fixture.node.settings.model_patches.kj.sage_attention, "disabled");
  assert.equal(fixture.node.settings.model_patches.kj.sage_allow_compile, false);
  assert.equal(fixture.node.settings.model_patches.kj.torch_compile.enabled, false);
  assert.deepEqual(JSON.parse(fixture.node.widgets[0].value), fixture.node.settings);
}

console.log("AiO Advanced settings dialog smoke passed.");
