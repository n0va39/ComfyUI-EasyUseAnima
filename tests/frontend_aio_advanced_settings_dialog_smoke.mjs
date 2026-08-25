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
  for (let index = 0; index < 6; index += 1) {
    await Promise.resolve();
  }
}

const advancedDialogModule = await import(dataModule("../web/js/aio/advanced_settings_dialog.js"));
const recommendationModule = await import(dataModule("../web/js/aio/torch_compile_recommendation.js"));
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
    negpip: {
      mode: "turbo",
      future_negpip_key: "keep-negpip",
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
        stage_scope: {
          first_pass: true,
          highres: false,
          detailer: true,
          upscale: false,
        },
        future_safe_pag_key: "keep-safe-pag",
      },
      kj: {
        fp16_accumulation: true,
        sage_attention: "auto",
        sage_allow_compile: true,
        sage_stage_scope: {
          first_pass: true,
          highres: false,
          detailer: true,
          upscale: false,
        },
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

function createFixture({
  settings = {},
  available = {},
  deferLoads = false,
  recommendationResults = [],
  deferRecommendations = false,
} = {}) {
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
  const recommendationCalls = [];
  const recommendationResolvers = [];
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

  function recommend(settingsSnapshot, context) {
    dependencyCalls += 1;
    recommendationCalls.push({
      settings: clone(settingsSnapshot),
      context: clone(context),
    });
    if (deferRecommendations) {
      return new Promise((resolve, reject) => {
        recommendationResolvers.push({ resolve, reject });
      });
    }
    const next = recommendationResults.shift();
    if (next instanceof Error) {
      throw next;
    }
    if (next === undefined) {
      throw new Error("Missing fixture recommendation result");
    }
    return clone(next);
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
      numericLimits,
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
    recommendationAdapter: {
      recommend,
      diff: recommendationModule.aioTorchCompileRecommendationDiff,
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
    recommendationCalls,
    dependencyCallCount: () => dependencyCalls,
    resolveLoads() {
      for (const resolve of loadResolvers.splice(0)) {
        resolve();
      }
    },
    resolveNextRecommendation(result) {
      const pending = recommendationResolvers.shift();
      assert.ok(pending, "missing deferred recommendation request");
      pending.resolve(clone(result));
    },
    rejectNextRecommendation(error) {
      const pending = recommendationResolvers.shift();
      assert.ok(pending, "missing deferred recommendation request");
      pending.reject(error);
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
  const conditioning = sectionByHeading(cancelDialog.body, "Conditioning");
  const modelPatches = sectionByHeading(cancelDialog.body, "Model Patch / Optimization");
  const artistMix = sectionByHeading(cancelDialog.body, "Artist Mix");
  const dave = subsectionByHeading(modelPatches, "Anima DAVE");
  const daveCustomStages = subsectionByHeading(dave, "Custom DAVE stages");
  const safePag = subsectionByHeading(modelPatches, "Anima Safe PAG");
  const safePagCustomStages = subsectionByHeading(safePag, "Custom Safe PAG stages");
  const kj = subsectionByHeading(modelPatches, "KJNodes Optimization");
  const sage = subsectionByHeading(kj, "SageAttention (KJNodes)");
  const sageCustomStages = subsectionByHeading(sage, "Custom SageAttention stages");
  const torch = subsectionByHeading(kj, "Torch Compile (KJNodes)");
  const torchDetails = subsectionByHeading(torch, "Torch Compile Parameters");
  const warning = find(
    modelPatches,
    (element) => element.classList.contains("easyuse-anima-aio-warning")
      && element.getAttribute?.("aria-live") !== "polite",
  );
  assert.ok(warning);
  assert.equal(warning.hidden, true);
  assert.equal(warning.textContent, "");
  assert.equal(fixture.loadCalls.length, 1);
  const negpipMode = controlIn(conditioning, "NegPip");
  const negpipStatus = find(
    conditioning,
    (element) => element.getAttribute?.("aria-live") === "polite",
  );
  assert.equal(negpipMode.value, "turbo");
  assert.ok(negpipStatus);
  assert.equal(negpipStatus.hidden, false);
  assert.equal(negpipStatus.textContent, "text:info.negpipTurboCfg");

  assertValues([
    [modelPatches, "AuraFlow shift", 6.5],
    [dave, "Mask", "configured-dave.npz"],
    [dave, "DAVE strength", 0.42],
    [dave, "DAVE tau", 0.21],
    [dave, "DAVE stages", "custom"],
    [safePag, "Safe PAG stages", "custom"],
    [safePag, "Safe PAG scale", 5.5],
    [safePag, "Safe PAG blocks", "3, 7"],
    [safePag, "PAG perturbation", 0.35],
    [safePag, "PAG heads", "1, 2"],
    [safePag, "PAG start percent", 0.1],
    [safePag, "PAG end percent", 0.9],
    [safePag, "PAG rescale", 0.4],
    [safePag, "PAG rescale mode", "partial"],
    [sage, "Mode", "auto"],
    [sage, "SageAttention stages", "custom"],
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
    [safePagCustomStages, "First pass", true],
    [safePagCustomStages, "Highres", false],
    [safePagCustomStages, "Detailer", true],
    [safePagCustomStages, "Upscale (USDU)", false],
    [kj, "KJNodes FP16 accum", true],
    [sageCustomStages, "First pass", true],
    [sageCustomStages, "Highres", false],
    [sageCustomStages, "Detailer", true],
    [sageCustomStages, "Upscale (USDU)", false],
    [sage, "Allow compile", true],
    [torch, "Use Torch compile", true],
    [torchDetails, "Fullgraph", true],
    [torchDetails, "Transformer blocks only", false],
    [torchDetails, "Debug keys", true],
    [torchDetails, "Disable dynamic VRAM", false],
  ]);
  assert.equal(controlIn(modelPatches, "AuraFlow shift").min, "0");
  assert.equal(controlIn(modelPatches, "AuraFlow shift").max, "100");
  assert.equal(controlIn(safePag, "Safe PAG scale").min, "0");
  assert.equal(controlIn(safePag, "Safe PAG scale").max, "100");
  assert.equal(rowByLabel(sage, "Allow compile").style.display, "");
  assert.equal(rowByLabel(sage, "SageAttention stages").style.display, "");
  assert.equal(sageCustomStages.style.display, "");
  assert.equal(torchDetails.style.display, "");
  assert.equal(daveCustomStages.style.display, "");
  assert.equal(safePagCustomStages.style.display, "");

  const sageMode = controlIn(sage, "Mode");
  sageMode.value = "disabled";
  sageMode.emit("change");
  assert.equal(rowByLabel(sage, "Allow compile").style.display, "none");
  assert.equal(rowByLabel(sage, "SageAttention stages").style.display, "none");
  assert.equal(sageCustomStages.style.display, "none");
  sageMode.value = "auto";
  sageMode.emit("change");
  assert.equal(rowByLabel(sage, "Allow compile").style.display, "");
  assert.equal(rowByLabel(sage, "SageAttention stages").style.display, "");
  assert.equal(sageCustomStages.style.display, "");
  const torchEnabled = controlIn(torch, "Use Torch compile");
  torchEnabled.checked = false;
  torchEnabled.emit("change");
  assert.equal(torchDetails.style.display, "none");
  torchEnabled.checked = true;
  torchEnabled.emit("change");
  assert.equal(torchDetails.style.display, "");
  negpipMode.value = "off";
  negpipMode.emit("change");
  assert.equal(negpipStatus.hidden, true);

  controlIn(modelPatches, "AuraFlow shift").value = "9";
  controlIn(dave, "Use DAVE").checked = false;
  controlIn(dave, "DAVE stages").value = "all_sampling_stages";
  controlIn(dave, "DAVE stages").emit("change");
  assert.equal(daveCustomStages.style.display, "none");
  controlIn(safePag, "PAG rescale mode").value = "full";
  controlIn(safePag, "Safe PAG stages").value = "all_sampling_stages";
  controlIn(safePag, "Safe PAG stages").emit("change");
  assert.equal(safePagCustomStages.style.display, "none");
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
  const applyConditioning = sectionByHeading(applyDialog.body, "Conditioning");
  const applyModelPatches = sectionByHeading(applyDialog.body, "Model Patch / Optimization");
  const applyArtistMix = sectionByHeading(applyDialog.body, "Artist Mix");
  const applyDave = subsectionByHeading(applyModelPatches, "Anima DAVE");
  const applyDaveCustomStages = subsectionByHeading(applyDave, "Custom DAVE stages");
  const applySafePag = subsectionByHeading(applyModelPatches, "Anima Safe PAG");
  const applySafePagCustomStages = subsectionByHeading(applySafePag, "Custom Safe PAG stages");
  const applyKj = subsectionByHeading(applyModelPatches, "KJNodes Optimization");
  const applySage = subsectionByHeading(applyKj, "SageAttention (KJNodes)");
  const applySageCustomStages = subsectionByHeading(
    applySage,
    "Custom SageAttention stages",
  );
  const applyTorch = subsectionByHeading(applyKj, "Torch Compile (KJNodes)");
  const applyTorchDetails = subsectionByHeading(applyTorch, "Torch Compile Parameters");

  controlIn(applyConditioning, "NegPip").value = "on";
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
  const applySafePagStagePreset = controlIn(applySafePag, "Safe PAG stages");
  applySafePagStagePreset.value = "first_pass_only";
  applySafePagStagePreset.emit("change");
  assert.equal(applySafePagCustomStages.style.display, "none");
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
  applySageMode.value = "sageattn3";
  applySageMode.emit("change");
  const applySageStagePreset = controlIn(applySage, "SageAttention stages");
  applySageStagePreset.value = "custom";
  applySageStagePreset.emit("change");
  assert.equal(applySageCustomStages.style.display, "");
  controlIn(applySageCustomStages, "First pass").checked = false;
  controlIn(applySageCustomStages, "Highres").checked = true;
  controlIn(applySageCustomStages, "Detailer").checked = false;
  controlIn(applySageCustomStages, "Upscale (USDU)").checked = true;
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
      ["99", 3, 0, 100],
      ["101", 4, 0, 100],
      ["-1", 0.75, 0, 1],
      ["2", 0, 0, 1],
      ["-1", 0.7, 0, 1],
      ["2", 0.2, 0, 1],
    ],
    "Apply must preserve the exact clamp inputs, defaults, and bounds",
  );

  const written = fixture.node.settings;
  assert.equal(written.negpip.mode, "on");
  assert.equal(written.negpip.future_negpip_key, "keep-negpip");
  assert.equal(written.model_patches.aura_flow.shift, 99);
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
      stage_scope: written.model_patches.safe_pag.stage_scope,
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
      stage_scope: {
        first_pass: true,
        highres: false,
        detailer: false,
        upscale: false,
      },
    },
  );
  assert.equal(written.model_patches.kj.fp16_accumulation, true);
  assert.equal(written.model_patches.kj.sage_attention, "sageattn3");
  assert.equal(written.model_patches.kj.sage_allow_compile, true);
  assert.deepEqual(written.model_patches.kj.sage_stage_scope, {
    first_pass: false,
    highres: true,
    detailer: false,
    upscale: true,
  });
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
  const fixture = createFixture({
    settings: { negpip: { mode: "turbo" } },
    available: { ppmNegPip: false },
  });
  fixture.openAdvancedSettings(fixture.node);
  await flushPromises();
  const dialog = fixture.dialogs[0];
  const conditioning = sectionByHeading(dialog.body, "Conditioning");
  const control = controlIn(conditioning, "NegPip");
  const status = find(
    conditioning,
    (element) => element.getAttribute?.("aria-live") === "polite",
  );
  const message = (
    'format:warning.optionalDependencyMissing:{"backend":"NegPip turbo","pack":"pack:ppmNegPip"}'
  );

  assert.equal(control.value, "turbo", "Missing PPM must preserve workflow intent");
  assert.equal(control.disabled, false, "Missing PPM must remain an editable choice");
  assert.equal(control.title, message);
  assert.equal(status.hidden, false);
  assert.equal(status.textContent, message);

  control.value = "off";
  control.emit("change");
  control.value = "turbo";
  control.emit("change");
  assert.equal(control.value, "turbo", "Dependency warning must not silently reset Turbo");
  assert.deepEqual(fixture.notifications, [{
    backend: "NegPip turbo",
    keys: ["ppmNegPip"],
  }]);
  action(dialog, "button.apply").emit("click");
  assert.equal(fixture.node.settings.negpip.mode, "turbo");
}

{
  const fresh = createFixture();
  fresh.openAdvancedSettings(fresh.node);
  await flushPromises();
  const dialog = fresh.dialogs[0];
  const modelPatches = sectionByHeading(dialog.body, "Model Patch / Optimization");
  const dave = subsectionByHeading(modelPatches, "Anima DAVE");
  const customStages = subsectionByHeading(dave, "Custom DAVE stages");
  const safePag = subsectionByHeading(modelPatches, "Anima Safe PAG");
  const safePagCustomStages = subsectionByHeading(safePag, "Custom Safe PAG stages");
  const kj = subsectionByHeading(modelPatches, "KJNodes Optimization");
  const sage = subsectionByHeading(kj, "SageAttention (KJNodes)");
  const sageCustomStages = subsectionByHeading(sage, "Custom SageAttention stages");
  assert.equal(controlIn(dave, "DAVE stages").value, "first_pass_only");
  assert.equal(customStages.style.display, "none");
  assert.equal(controlIn(safePag, "Safe PAG stages").value, "first_pass_only");
  assert.equal(safePagCustomStages.style.display, "none");
  assert.equal(controlIn(sage, "SageAttention stages").value, "first_pass_only");
  assert.equal(sageCustomStages.style.display, "none");
}

{
  const malformed = createFixture({
    settings: {
      model_patches: {
        safe_pag: { stage_scope: "all" },
        kj: { sage_stage_scope: "all" },
      },
    },
  });
  malformed.openAdvancedSettings(malformed.node);
  await flushPromises();
  const dialog = malformed.dialogs[0];
  const modelPatches = sectionByHeading(dialog.body, "Model Patch / Optimization");
  const safePag = subsectionByHeading(modelPatches, "Anima Safe PAG");
  const customStages = subsectionByHeading(safePag, "Custom Safe PAG stages");
  const kj = subsectionByHeading(modelPatches, "KJNodes Optimization");
  const sage = subsectionByHeading(kj, "SageAttention (KJNodes)");
  const sageCustomStages = subsectionByHeading(sage, "Custom SageAttention stages");
  assert.equal(controlIn(safePag, "Safe PAG stages").value, "custom");
  assertChecked([
    [customStages, "First pass", false],
    [customStages, "Highres", false],
    [customStages, "Detailer", false],
    [customStages, "Upscale (USDU)", false],
    [sageCustomStages, "First pass", false],
    [sageCustomStages, "Highres", false],
    [sageCustomStages, "Detailer", false],
    [sageCustomStages, "Upscale (USDU)", false],
  ]);
  assert.equal(controlIn(sage, "SageAttention stages").value, "custom");
}

{
  const custom = createFixture({ settings: configuredSettings() });
  custom.openAdvancedSettings(custom.node);
  await flushPromises();
  const dialog = custom.dialogs[0];
  const modelPatches = sectionByHeading(dialog.body, "Model Patch / Optimization");
  const safePag = subsectionByHeading(modelPatches, "Anima Safe PAG");
  const customStages = subsectionByHeading(safePag, "Custom Safe PAG stages");
  assert.equal(controlIn(safePag, "Safe PAG stages").value, "custom");
  controlIn(customStages, "First pass").checked = false;
  controlIn(customStages, "Highres").checked = true;
  controlIn(customStages, "Detailer").checked = false;
  controlIn(customStages, "Upscale (USDU)").checked = true;
  action(dialog, "button.apply").emit("click");
  assert.deepEqual(custom.node.settings.model_patches.safe_pag.stage_scope, {
    first_pass: false,
    highres: true,
    detailer: false,
    upscale: true,
  });
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

{
  const custom = createFixture({ settings: configuredSettings() });
  custom.openAdvancedSettings(custom.node);
  await flushPromises();
  const dialog = custom.dialogs[0];
  const modelPatches = sectionByHeading(dialog.body, "Model Patch / Optimization");
  const kj = subsectionByHeading(modelPatches, "KJNodes Optimization");
  const sage = subsectionByHeading(kj, "SageAttention (KJNodes)");
  const customStages = subsectionByHeading(sage, "Custom SageAttention stages");
  assert.equal(controlIn(sage, "SageAttention stages").value, "custom");
  controlIn(customStages, "First pass").checked = false;
  controlIn(customStages, "Highres").checked = true;
  controlIn(customStages, "Detailer").checked = false;
  controlIn(customStages, "Upscale (USDU)").checked = true;
  action(dialog, "button.apply").emit("click");
  assert.deepEqual(custom.node.settings.model_patches.kj.sage_stage_scope, {
    first_pass: false,
    highres: true,
    detailer: false,
    upscale: true,
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
  const safePagCustomStages = subsectionByHeading(safePag, "Custom Safe PAG stages");
  const kj = subsectionByHeading(modelPatches, "KJNodes Optimization");
  const sage = subsectionByHeading(kj, "SageAttention (KJNodes)");
  const sageCustomStages = subsectionByHeading(sage, "Custom SageAttention stages");
  const torch = subsectionByHeading(kj, "Torch Compile (KJNodes)");
  const torchDetails = subsectionByHeading(torch, "Torch Compile Parameters");
  const warning = find(
    modelPatches,
    (element) => element.classList.contains("easyuse-anima-aio-warning")
      && element.getAttribute?.("aria-live") !== "polite",
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
      [safePag, "Safe PAG stages"],
      [safePagCustomStages, "First pass"],
      [safePagCustomStages, "Highres"],
      [safePagCustomStages, "Detailer"],
      [safePagCustomStages, "Upscale (USDU)"],
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
      [sage, "SageAttention stages"],
      [sageCustomStages, "First pass"],
      [sageCustomStages, "Highres"],
      [sageCustomStages, "Detailer"],
      [sageCustomStages, "Upscale (USDU)"],
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
  const safePagCustomStages = subsectionByHeading(safePag, "Custom Safe PAG stages");
  const kj = subsectionByHeading(modelPatches, "KJNodes Optimization");
  const sage = subsectionByHeading(kj, "SageAttention (KJNodes)");
  const torch = subsectionByHeading(kj, "Torch Compile (KJNodes)");
  const torchDetails = subsectionByHeading(torch, "Torch Compile Parameters");
  const warning = find(
    modelPatches,
    (element) => element.classList.contains("easyuse-anima-aio-warning")
      && element.getAttribute?.("aria-live") !== "polite",
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
    [safePag, "Safe PAG stages"],
    [safePagCustomStages, "First pass"],
    [safePagCustomStages, "Highres"],
    [safePagCustomStages, "Detailer"],
    [safePagCustomStages, "Upscale (USDU)"],
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

function supportedRecommendation() {
  return {
    supported: true,
    profile: "stable_variable_shapes",
    policyVersion: "recommendation-v1",
    values: {
      enabled: true,
      backend: "inductor",
      fullgraph: false,
      mode: "default",
      dynamic: "auto",
      compile_transformer_blocks_only: true,
      dynamo_cache_size_limit: 64,
      debug_compile_keys: false,
      disable_dynamic_vram: false,
    },
    reasonCodes: ["highres_changes_shape"],
    warnings: ["first_compile_may_be_slow"],
    environment: { accelerator: "cuda", totalVramMb: 16302 },
  };
}

function torchRecommendationControls(dialog) {
  const modelPatches = sectionByHeading(dialog.body, "Model Patch / Optimization");
  const kj = subsectionByHeading(modelPatches, "KJNodes Optimization");
  const torch = subsectionByHeading(kj, "Torch Compile (KJNodes)");
  const details = subsectionByHeading(torch, "Torch Compile Parameters");
  const button = findByText(torch, "text:button.torchCompileRecommend");
  const status = find(torch, (element) => element.getAttribute?.("aria-live") === "polite");
  assert.ok(button, "missing Torch Compile recommendation button");
  assert.ok(status, "missing Torch Compile recommendation status");
  return { torch, details, button, status };
}

{
  const fixture = createFixture({
    settings: configuredSettings(),
    deferRecommendations: true,
  });
  const originalSettings = clone(fixture.node.settings);
  const originalWidget = fixture.node.widgets[0].value;
  fixture.openAdvancedSettings(fixture.node);
  await flushPromises();
  const dialog = fixture.dialogs[0];
  const controls = torchRecommendationControls(dialog);

  controls.button.emit("click");
  assert.equal(controls.button.disabled, true);
  assert.equal(controls.status.getAttribute("data-state"), "loading");
  assert.equal(controls.status.textContent, "text:status.torchCompileLoading");
  controls.button.emit("click");
  await flushPromises();
  assert.equal(fixture.recommendationCalls.length, 1, "A pending click must not duplicate requests");
  assert.deepEqual(fixture.recommendationCalls[0], {
    settings: originalSettings,
    context: {},
  });
  assert.equal(fixture.writes.length, 0, "Recommendation loading must not write node settings");

  fixture.resolveNextRecommendation(supportedRecommendation());
  await flushPromises();
  assert.equal(controls.button.disabled, false);
  assert.equal(controls.status.getAttribute("data-state"), "supported");
  assert.ok(controls.status.textContent.includes("text:status.torchCompileDraftApplied"));
  assert.ok(controls.status.textContent.includes(
    'format:status.torchCompileProfile:{"profile":"stable_variable_shapes"}',
  ));
  assert.ok(controls.status.textContent.includes(
    'format:status.torchCompileEnvironment:{"accelerator":"cuda","vram":"16302 MiB"}',
  ));
  assert.ok(controls.status.textContent.includes(
    'format:status.torchCompileReason:{"code":"highres_changes_shape"}',
  ));
  assert.ok(controls.status.textContent.includes(
    'format:status.torchCompileWarning:{"code":"first_compile_may_be_slow"}',
  ));
  assertValues([
    [controls.details, "Backend", "inductor"],
    [controls.details, "Mode", "default"],
    [controls.details, "Dynamic", "auto"],
    [controls.details, "Dynamo cache limit", 64],
  ]);
  assertChecked([
    [controls.torch, "Use Torch compile", true],
    [controls.details, "Fullgraph", false],
    [controls.details, "Transformer blocks only", true],
    [controls.details, "Debug keys", false],
    [controls.details, "Disable dynamic VRAM", false],
  ]);
  assert.deepEqual(fixture.node.settings, originalSettings, "Recommendation is draft-only");
  assert.equal(fixture.node.widgets[0].value, originalWidget);
  assert.equal(fixture.writes.length, 0);
  assert.equal(fixture.renders.length, 0);

  action(dialog, "button.cancel").emit("click");
  assert.deepEqual(dialog.trace, ["remove"]);
  assert.deepEqual(fixture.node.settings, originalSettings, "Cancel must discard recommendation draft");
  assert.equal(fixture.node.widgets[0].value, originalWidget);
}

{
  const fixture = createFixture({
    settings: configuredSettings(),
    recommendationResults: [supportedRecommendation()],
  });
  fixture.openAdvancedSettings(fixture.node);
  await flushPromises();
  const dialog = fixture.dialogs[0];
  const controls = torchRecommendationControls(dialog);
  controls.button.emit("click");
  await flushPromises();
  assert.equal(fixture.writes.length, 0);
  action(dialog, "button.apply").emit("click");
  assert.deepEqual(dialog.trace, ["merge", "write", "render", "remove"]);
  assert.deepEqual(
    {
      enabled: fixture.node.settings.model_patches.kj.torch_compile.enabled,
      backend: fixture.node.settings.model_patches.kj.torch_compile.backend,
      fullgraph: fixture.node.settings.model_patches.kj.torch_compile.fullgraph,
      mode: fixture.node.settings.model_patches.kj.torch_compile.mode,
      dynamic: fixture.node.settings.model_patches.kj.torch_compile.dynamic,
      compile_transformer_blocks_only: (
        fixture.node.settings.model_patches.kj.torch_compile.compile_transformer_blocks_only
      ),
      dynamo_cache_size_limit: (
        fixture.node.settings.model_patches.kj.torch_compile.dynamo_cache_size_limit
      ),
      debug_compile_keys: fixture.node.settings.model_patches.kj.torch_compile.debug_compile_keys,
      disable_dynamic_vram: fixture.node.settings.model_patches.kj.torch_compile.disable_dynamic_vram,
    },
    supportedRecommendation().values,
    "Only final Apply may persist a recommendation",
  );
  assert.equal(
    fixture.node.settings.model_patches.kj.torch_compile.future_torch_key,
    "keep-torch",
    "Unknown Torch Compile settings must survive final Apply",
  );
}

{
  const unsupported = {
    supported: false,
    profile: "unsupported_environment",
    policyVersion: "recommendation-v1",
    values: null,
    reasonCodes: ["unsupported_accelerator"],
    warnings: [],
    environment: { accelerator: "cpu", totalVramMb: null },
  };
  const fixture = createFixture({
    settings: configuredSettings(),
    recommendationResults: [unsupported],
  });
  fixture.openAdvancedSettings(fixture.node);
  await flushPromises();
  const dialog = fixture.dialogs[0];
  const controls = torchRecommendationControls(dialog);
  const before = {
    backend: controlIn(controls.details, "Backend").value,
    dynamic: controlIn(controls.details, "Dynamic").value,
    enabled: controlIn(controls.torch, "Use Torch compile").checked,
  };
  controls.button.emit("click");
  await flushPromises();
  assert.equal(controls.status.getAttribute("data-state"), "unsupported");
  assert.ok(controls.status.textContent.includes("text:status.torchCompileUnsupported"));
  assert.deepEqual({
    backend: controlIn(controls.details, "Backend").value,
    dynamic: controlIn(controls.details, "Dynamic").value,
    enabled: controlIn(controls.torch, "Use Torch compile").checked,
  }, before, "Unsupported responses must not mutate controls");
  assert.equal(fixture.writes.length, 0);
}

{
  const fixture = createFixture({
    settings: configuredSettings(),
    recommendationResults: [new Error("policy unavailable")],
  });
  fixture.openAdvancedSettings(fixture.node);
  await flushPromises();
  const dialog = fixture.dialogs[0];
  const controls = torchRecommendationControls(dialog);
  const before = controlIn(controls.details, "Backend").value;
  controls.button.emit("click");
  await flushPromises();
  assert.equal(controls.status.getAttribute("data-state"), "error");
  assert.equal(
    controls.status.textContent,
    'format:status.torchCompileRequestFailed:{"message":"policy unavailable"}',
  );
  assert.equal(controlIn(controls.details, "Backend").value, before);
  assert.equal(fixture.writes.length, 0);
}

{
  const fixture = createFixture({
    settings: configuredSettings(),
    deferRecommendations: true,
  });
  const originalSettings = clone(fixture.node.settings);
  fixture.openAdvancedSettings(fixture.node);
  await flushPromises();
  const dialog = fixture.dialogs[0];
  const controls = torchRecommendationControls(dialog);
  const before = controlIn(controls.details, "Backend").value;
  controls.button.emit("click");
  await flushPromises();
  action(dialog, "button.cancel").emit("click");
  fixture.resolveNextRecommendation(supportedRecommendation());
  await flushPromises();
  assert.equal(controlIn(controls.details, "Backend").value, before);
  assert.deepEqual(fixture.node.settings, originalSettings);
  assert.equal(fixture.writes.length, 0, "A late result after Cancel must be ignored");
}

console.log("AiO Advanced settings dialog smoke passed.");
