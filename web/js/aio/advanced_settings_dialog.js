// @ts-check

/**
 * @typedef {object} AioAdvancedDialogControls
 * @property {(title: any, subtitle: any) => {backdrop: any, body: any, actions: any}} createDialog
 * @property {(section: any, label: any, control: any, tooltipKey?: string) => any} field
 * @property {(value: any, step?: string) => any} numberInput
 * @property {(value: any) => any} checkbox
 * @property {(value: any) => any} textInput
 * @property {(options: any[], value: any) => any} selectInput
 */

/**
 * @typedef {object} AioAdvancedDialogText
 * @property {(value: any) => string} staticText
 * @property {(key: string) => string} get
 * @property {(key: string, values?: Record<string, any>) => string} format
 */

/**
 * @typedef {object} AioAdvancedDialogSettingsCore
 * @property {any} defaultGenerationSettings
 * @property {any} numericLimits
 * @property {(defaults: any, current: any) => any} mergeDefaults
 * @property {(value: any, fallback: number, min: number, max: number) => number} clampNumber
 */

/**
 * @typedef {object} AioAdvancedDialogNodeAdapter
 * @property {string} generatorSettingsWidget
 * @property {(node: any, name: string) => any} findWidget
 * @property {(node: any) => any} getSettings
 * @property {(node: any, widget: any, settings: any) => void} writeSettings
 * @property {(node: any) => void} renderPanel
 */

/**
 * @typedef {object} AioAdvancedDialogDependencyAdapter
 * @property {(key: string) => boolean} available
 * @property {(key: string) => string} pack
 * @property {(control: any, missing: boolean, message?: string) => void} markMissingControl
 * @property {(backend: string, keys: string[]) => boolean} notifyMissing
 * @property {(options?: Record<string, any>) => Promise<any>} load
 */

/**
 * @typedef {object} AioAdvancedDialogRecommendationAdapter
 * @property {(settings: any, context?: Record<string, any>) => Promise<any>} recommend
 * @property {(current: any, values: any) => Array<{name: string, current: any, recommended: any}>} diff
 */

/**
 * @typedef {object} AioAdvancedSettingsDialogDependencies
 * @property {any} document
 * @property {AioAdvancedDialogControls} controls
 * @property {AioAdvancedDialogText} text
 * @property {AioAdvancedDialogSettingsCore} settingsCore
 * @property {AioAdvancedDialogNodeAdapter} nodeAdapter
 * @property {AioAdvancedDialogDependencyAdapter} dependencyAdapter
 * @property {AioAdvancedDialogRecommendationAdapter} recommendationAdapter
 */

const DAVE_STAGE_IDS = Object.freeze([
  "first_pass",
  "highres",
  "detailer",
  "upscale",
]);

/** @type {Readonly<Record<string, Readonly<Record<string, boolean>>>>} */
const DAVE_STAGE_SCOPE_PRESETS = Object.freeze({
  first_pass_only: Object.freeze({
    first_pass: true,
    highres: false,
    detailer: false,
    upscale: false,
  }),
  all_sampling_stages: Object.freeze({
    first_pass: true,
    highres: true,
    detailer: true,
    upscale: true,
  }),
});

const SAFE_PAG_STAGE_IDS = Object.freeze([
  "first_pass",
  "highres",
  "detailer",
  "upscale",
]);

/** @type {Readonly<Record<string, Readonly<Record<string, boolean>>>>} */
const SAFE_PAG_STAGE_SCOPE_PRESETS = Object.freeze({
  first_pass_only: Object.freeze({
    first_pass: true,
    highres: false,
    detailer: false,
    upscale: false,
  }),
  all_sampling_stages: Object.freeze({
    first_pass: true,
    highres: true,
    detailer: true,
    upscale: true,
  }),
});

const SAGE_STAGE_IDS = Object.freeze([
  "first_pass",
  "highres",
  "detailer",
  "upscale",
]);

/** @type {Readonly<Record<string, Readonly<Record<string, boolean>>>>} */
const SAGE_STAGE_SCOPE_PRESETS = Object.freeze({
  first_pass_only: Object.freeze({
    first_pass: true,
    highres: false,
    detailer: false,
    upscale: false,
  }),
  all_sampling_stages: Object.freeze({
    first_pass: true,
    highres: true,
    detailer: true,
    upscale: true,
  }),
});

function daveStageScopePreset(scope) {
  for (const [preset, expected] of Object.entries(DAVE_STAGE_SCOPE_PRESETS)) {
    if (DAVE_STAGE_IDS.every((stageId) => !!scope?.[stageId] === expected[stageId])) {
      return preset;
    }
  }
  return "custom";
}

function safePagStageScopePreset(scope) {
  for (const [preset, expected] of Object.entries(SAFE_PAG_STAGE_SCOPE_PRESETS)) {
    if (SAFE_PAG_STAGE_IDS.every((stageId) => !!scope?.[stageId] === expected[stageId])) {
      return preset;
    }
  }
  return "custom";
}

function sageStageScopePreset(scope) {
  for (const [preset, expected] of Object.entries(SAGE_STAGE_SCOPE_PRESETS)) {
    if (SAGE_STAGE_IDS.every((stageId) => !!scope?.[stageId] === expected[stageId])) {
      return preset;
    }
  }
  return "custom";
}

/**
 * Own the Advanced settings dialog, model-patch dependency locks, visibility,
 * and Apply/Cancel lifecycle. Extension registration, dependency discovery,
 * generator-panel rendering, and durable storage remain adapters.
 *
 * @param {AioAdvancedSettingsDialogDependencies} dependencies
 * @returns {(node: any) => void}
 */
export function aioCreateAdvancedSettingsDialog(dependencies) {
  const {
    document,
    controls,
    text,
    settingsCore,
    nodeAdapter,
    dependencyAdapter,
    recommendationAdapter,
  } = dependencies;
  const {
    createDialog,
    field,
    numberInput,
    checkbox,
    textInput,
    selectInput,
  } = controls;
  const {
    staticText: aioStaticText,
    get: aioText,
    format: aioFormat,
  } = text;
  const {
    defaultGenerationSettings: DEFAULT_GENERATION_SETTINGS,
    numericLimits: GENERATOR_NUMERIC_LIMITS,
    mergeDefaults,
    clampNumber: clampGeneratorNumber,
  } = settingsCore;
  const {
    generatorSettingsWidget: GENERATOR_SETTINGS_WIDGET,
    findWidget,
    getSettings: generatorSettings,
    writeSettings,
    renderPanel: renderGeneratorPanel,
  } = nodeAdapter;
  const {
    available: optionalDependencyAvailable,
    pack: optionalDependencyPack,
    markMissingControl: aioMarkMissingDependencyControl,
    notifyMissing: notifyMissingDependency,
    load: loadGeneratorOptionalDependencies,
  } = dependencyAdapter;
  const {
    recommend: recommendTorchCompile,
    diff: torchCompileRecommendationDiff,
  } = recommendationAdapter;

  function openAdvancedSettings(node) {
    const widget = findWidget(node, GENERATOR_SETTINGS_WIDGET);
    const settings = generatorSettings(node);
    const { backdrop, body, actions } = createDialog(
      "Advanced Options",
      "Advanced generation options stay in a popup and are serialized as versioned settings."
    );

    const makeSubsection = (title) => {
      const section = document.createElement("div");
      section.className = "easyuse-anima-aio-subsection";
      section.append(Object.assign(document.createElement("h4"), { textContent: aioStaticText(title) }));
      return section;
    };

    const conditioning = document.createElement("section");
    conditioning.className = "easyuse-anima-aio-section full";
    conditioning.append(Object.assign(document.createElement("h3"), {
      textContent: aioStaticText("Conditioning"),
    }));
    const negpipSettings = settings.negpip || DEFAULT_GENERATION_SETTINGS.negpip;
    const negpipMode = field(
      conditioning,
      "NegPip",
      selectInput([
        { value: "off", label: aioText("option.negpipOff") },
        { value: "on", label: aioText("option.negpipOn") },
        { value: "turbo", label: aioText("option.negpipTurbo") },
      ], negpipSettings.mode || "off"),
      "tip.negpipMode",
    );
    const negpipWarning = document.createElement("div");
    negpipWarning.className = "easyuse-anima-aio-warning";
    negpipWarning.setAttribute("aria-live", "polite");
    negpipWarning.hidden = true;
    conditioning.append(negpipWarning);
    body.append(conditioning);

    const modelPatches = document.createElement("section");
    modelPatches.className = "easyuse-anima-aio-section full";
    modelPatches.append(Object.assign(document.createElement("h3"), { textContent: aioStaticText("Model Patch / Optimization") }));

    const auraShift = field(
      modelPatches,
      "AuraFlow shift",
      numberInput(settings.model_patches.aura_flow.shift, "0.5"),
      "tip.shift",
    );
    auraShift.min = String(GENERATOR_NUMERIC_LIMITS.auraFlowShift.min);
    auraShift.max = String(GENERATOR_NUMERIC_LIMITS.auraFlowShift.max);

    const dave = makeSubsection("Anima DAVE");
    const daveEnabled = field(dave, "Use DAVE", checkbox(settings.model_patches.dave.enabled), "tip.daveEnabled");
    const daveMask = field(dave, "Mask", textInput(settings.model_patches.dave.mask || "dave_alpha.npz"), "tip.daveMask");
    const daveStrength = field(dave, "DAVE strength", numberInput(settings.model_patches.dave.strength ?? 0.30, "0.01"), "tip.daveStrength");
    const daveTau = field(dave, "DAVE tau", numberInput(settings.model_patches.dave.tau ?? 0.10, "0.01"), "tip.daveTau");
    const daveStageScope = settings.model_patches.dave.stage_scope
      || DEFAULT_GENERATION_SETTINGS.model_patches.dave.stage_scope;
    const daveStagePreset = field(
      dave,
      "DAVE stages",
      selectInput([
        {
          value: "first_pass_only",
          label: aioText("option.daveScopeFirstPassOnly"),
        },
        {
          value: "all_sampling_stages",
          label: aioText("option.daveScopeAllSamplingStages"),
        },
        {
          value: "custom",
          label: aioText("option.daveScopeCustom"),
        },
      ], daveStageScopePreset(daveStageScope)),
      "tip.daveStagePreset",
    );
    const daveCustomStages = makeSubsection("Custom DAVE stages");
    const daveFirstPass = field(
      daveCustomStages,
      "First pass",
      checkbox(daveStageScope.first_pass),
      "tip.daveStageFirstPass",
    );
    const daveHighres = field(
      daveCustomStages,
      "Highres",
      checkbox(daveStageScope.highres),
      "tip.daveStageHighres",
    );
    const daveDetailer = field(
      daveCustomStages,
      "Detailer",
      checkbox(daveStageScope.detailer),
      "tip.daveStageDetailer",
    );
    const daveUpscale = field(
      daveCustomStages,
      "Upscale (USDU)",
      checkbox(daveStageScope.upscale),
      "tip.daveStageUpscale",
    );
    dave.append(daveCustomStages);
    daveStrength.min = "0";
    daveTau.min = "0";
    daveTau.max = "1";

    const safePag = makeSubsection("Anima Safe PAG");
    const safePagSettings = settings.model_patches.safe_pag || DEFAULT_GENERATION_SETTINGS.model_patches.safe_pag;
    const safePagEnabled = field(safePag, "Use Safe PAG", checkbox(safePagSettings.enabled), "tip.safePagEnabled");
    const safePagStageScope = (
      safePagSettings.stage_scope
      && typeof safePagSettings.stage_scope === "object"
      && !Array.isArray(safePagSettings.stage_scope)
    )
      ? safePagSettings.stage_scope
      : Object.fromEntries(SAFE_PAG_STAGE_IDS.map((stageId) => [stageId, false]));
    const safePagStagePreset = field(
      safePag,
      "Safe PAG stages",
      selectInput([
        {
          value: "first_pass_only",
          label: aioText("option.safePagScopeFirstPassOnly"),
        },
        {
          value: "all_sampling_stages",
          label: aioText("option.safePagScopeAllSamplingStages"),
        },
        {
          value: "custom",
          label: aioText("option.safePagScopeCustom"),
        },
      ], safePagStageScopePreset(safePagStageScope)),
      "tip.safePagStagePreset",
    );
    const safePagCustomStages = makeSubsection("Custom Safe PAG stages");
    const safePagFirstPass = field(
      safePagCustomStages,
      "First pass",
      checkbox(safePagStageScope.first_pass),
      "tip.safePagStageFirstPass",
    );
    const safePagHighres = field(
      safePagCustomStages,
      "Highres",
      checkbox(safePagStageScope.highres),
      "tip.safePagStageHighres",
    );
    const safePagDetailer = field(
      safePagCustomStages,
      "Detailer",
      checkbox(safePagStageScope.detailer),
      "tip.safePagStageDetailer",
    );
    const safePagUpscale = field(
      safePagCustomStages,
      "Upscale (USDU)",
      checkbox(safePagStageScope.upscale),
      "tip.safePagStageUpscale",
    );
    safePag.append(safePagCustomStages);
    const safePagScale = field(safePag, "Safe PAG scale", numberInput(safePagSettings.scale ?? 4.0, "0.1"), "tip.safePagScale");
    const safePagBlocks = field(safePag, "Safe PAG blocks", textInput(safePagSettings.block_indices || "18"), "tip.safePagBlocks");
    const safePagPerturbation = field(
      safePag,
      "PAG perturbation",
      numberInput(safePagSettings.perturbation_strength ?? 0.75, "0.01"),
      "tip.safePagPerturbation",
    );
    const safePagHeads = field(safePag, "PAG heads", textInput(safePagSettings.head_indices || ""), "tip.safePagHeads");
    const safePagStart = field(
      safePag,
      "PAG start percent",
      numberInput(safePagSettings.start_percent ?? 0.0, "0.001"),
      "tip.safePagStart",
    );
    const safePagEnd = field(
      safePag,
      "PAG end percent",
      numberInput(safePagSettings.end_percent ?? 0.7, "0.001"),
      "tip.safePagEnd",
    );
    const safePagRescale = field(safePag, "PAG rescale", numberInput(safePagSettings.rescale ?? 0.2, "0.01"), "tip.safePagRescale");
    const safePagRescaleMode = field(
      safePag,
      "PAG rescale mode",
      selectInput(["full", "partial"], safePagSettings.rescale_mode || "full"),
      "tip.safePagRescaleMode",
    );
    safePagScale.min = "0";
    safePagScale.max = "100";
    safePagPerturbation.min = "0";
    safePagPerturbation.max = "1";
    safePagStart.min = "0";
    safePagStart.max = "1";
    safePagEnd.min = "0";
    safePagEnd.max = "1";
    safePagRescale.min = "0";
    safePagRescale.max = "1";

    const kj = makeSubsection("KJNodes Optimization");
    const fp16Accum = field(kj, "KJNodes FP16 accum", checkbox(settings.model_patches.kj.fp16_accumulation), "tip.kjFp16Accum");

    const sage = makeSubsection("SageAttention (KJNodes)");
    const sageAttention = field(
      sage,
      "Mode",
      selectInput([
        "disabled",
        "auto",
        "sageattn_qk_int8_pv_fp16_cuda",
        "sageattn_qk_int8_pv_fp16_triton",
        "sageattn_qk_int8_pv_fp8_cuda",
        "sageattn_qk_int8_pv_fp8_cuda++",
        "sageattn3",
        "sageattn3_per_block_mean",
      ], settings.model_patches.kj.sage_attention),
      "tip.kjSageMode",
    );
    const sageStageScope = (
      settings.model_patches.kj.sage_stage_scope
      && typeof settings.model_patches.kj.sage_stage_scope === "object"
      && !Array.isArray(settings.model_patches.kj.sage_stage_scope)
    )
      ? settings.model_patches.kj.sage_stage_scope
      : Object.fromEntries(SAGE_STAGE_IDS.map((stageId) => [stageId, false]));
    const sageStagePreset = field(
      sage,
      "SageAttention stages",
      selectInput([
        {
          value: "first_pass_only",
          label: aioText("option.sageScopeFirstPassOnly"),
        },
        {
          value: "all_sampling_stages",
          label: aioText("option.sageScopeAllSamplingStages"),
        },
        {
          value: "custom",
          label: aioText("option.sageScopeCustom"),
        },
      ], sageStageScopePreset(sageStageScope)),
      "tip.sageStagePreset",
    );
    const sageCustomStages = makeSubsection("Custom SageAttention stages");
    const sageFirstPass = field(
      sageCustomStages,
      "First pass",
      checkbox(sageStageScope.first_pass),
      "tip.sageStageFirstPass",
    );
    const sageHighres = field(
      sageCustomStages,
      "Highres",
      checkbox(sageStageScope.highres),
      "tip.sageStageHighres",
    );
    const sageDetailer = field(
      sageCustomStages,
      "Detailer",
      checkbox(sageStageScope.detailer),
      "tip.sageStageDetailer",
    );
    const sageUpscale = field(
      sageCustomStages,
      "Upscale (USDU)",
      checkbox(sageStageScope.upscale),
      "tip.sageStageUpscale",
    );
    sage.append(sageCustomStages);
    const sageAllowCompile = field(sage, "Allow compile", checkbox(settings.model_patches.kj.sage_allow_compile), "tip.kjSageCompile");
    kj.append(sage);

    const torch = makeSubsection("Torch Compile (KJNodes)");
    const torchCompileEnabled = field(
      torch,
      "Use Torch compile",
      checkbox(settings.model_patches.kj.torch_compile.enabled),
      "tip.torchCompileEnabled",
    );
    const torchDetails = document.createElement("div");
    torchDetails.className = "easyuse-anima-aio-subsection";
    torchDetails.append(Object.assign(document.createElement("h4"), { textContent: aioStaticText("Torch Compile Parameters") }));
    const torchCompileBackend = field(torchDetails, "Backend", textInput(settings.model_patches.kj.torch_compile.backend), "tip.torchCompileBackend");
    const torchCompileFullgraph = field(torchDetails, "Fullgraph", checkbox(settings.model_patches.kj.torch_compile.fullgraph), "tip.torchCompileFullgraph");
    const torchCompileMode = field(
      torchDetails,
      "Mode",
      selectInput([
        "default",
        "reduce-overhead",
        "max-autotune",
        "max-autotune-no-cudagraphs",
      ], settings.model_patches.kj.torch_compile.mode),
      "tip.torchCompileMode",
    );
    const torchCompileDynamic = field(
      torchDetails,
      "Dynamic",
      selectInput(["auto", "false", "true", "default"], settings.model_patches.kj.torch_compile.dynamic),
      "tip.torchCompileDynamic",
    );
    const torchCompileBlocksOnly = field(
      torchDetails,
      "Transformer blocks only",
      checkbox(settings.model_patches.kj.torch_compile.compile_transformer_blocks_only),
      "tip.torchCompileBlocks",
    );
    const torchCompileCache = field(
      torchDetails,
      "Dynamo cache limit",
      numberInput(settings.model_patches.kj.torch_compile.dynamo_cache_size_limit, "1"),
      "tip.torchCompileCache",
    );
    const torchCompileDebug = field(
      torchDetails,
      "Debug keys",
      checkbox(settings.model_patches.kj.torch_compile.debug_compile_keys),
      "tip.torchCompileDebug",
    );
    const torchCompileDisableVram = field(
      torchDetails,
      "Disable dynamic VRAM",
      checkbox(settings.model_patches.kj.torch_compile.disable_dynamic_vram),
      "tip.torchCompileVram",
    );
    const torchRecommendationActions = document.createElement("div");
    torchRecommendationActions.className = "easyuse-anima-aio-dialog-actions";
    const torchRecommendButton = document.createElement("button");
    torchRecommendButton.type = "button";
    torchRecommendButton.textContent = aioText("button.torchCompileRecommend");
    torchRecommendationActions.append(torchRecommendButton);
    const torchRecommendationStatus = document.createElement("div");
    torchRecommendationStatus.className = "easyuse-anima-aio-warning";
    torchRecommendationStatus.hidden = true;
    torchRecommendationStatus.style.whiteSpace = "pre-line";
    torchRecommendationStatus.setAttribute("aria-live", "polite");
    torch.append(torchRecommendationActions, torchRecommendationStatus, torchDetails);
    kj.append(torch);

    const modelWarning = document.createElement("div");
    modelWarning.className = "easyuse-anima-aio-warning";
    modelWarning.hidden = true;
    modelPatches.append(dave, safePag, kj, modelWarning);
    body.append(modelPatches);

    const artistMix = document.createElement("section");
    artistMix.className = "easyuse-anima-aio-section full";
    artistMix.append(Object.assign(document.createElement("h3"), { textContent: aioStaticText("Artist Mix") }));
    const artistMode = field(
      artistMix,
      "Mode",
      selectInput([
        "prompt_data",
        "off",
        "prompt",
        "average",
        "delta_rms",
        "hybrid",
        "clustered",
        "exact",
        "composite_exact",
        "late_exact",
        "average_late_exact",
        "scheduled_average",
      ], settings.artist_mix.mode),
      "tip.artistMixMode",
    );
    const artistStart = field(artistMix, "Start", numberInput(settings.artist_mix.start_percent, "0.01"));
    const artistStrength = field(artistMix, "Strength", numberInput(settings.artist_mix.strength_scale, "0.01"));
    body.append(artistMix);

    const refreshSageDetails = () => {
      const enabled = sageAttention.value !== "disabled";
      sageAllowCompile.parentElement.style.display = enabled ? "" : "none";
      sageStagePreset.parentElement.style.display = enabled ? "" : "none";
      sageCustomStages.style.display = enabled && sageStagePreset.value === "custom"
        ? ""
        : "none";
    };
    const refreshTorchDetails = () => {
      torchDetails.style.display = torchCompileEnabled.checked ? "" : "none";
    };
    const torchControlValues = () => ({
      enabled: torchCompileEnabled.checked,
      backend: torchCompileBackend.value,
      fullgraph: torchCompileFullgraph.checked,
      mode: torchCompileMode.value,
      dynamic: torchCompileDynamic.value,
      compile_transformer_blocks_only: torchCompileBlocksOnly.checked,
      dynamo_cache_size_limit: Number(torchCompileCache.value),
      debug_compile_keys: torchCompileDebug.checked,
      disable_dynamic_vram: torchCompileDisableVram.checked,
    });
    const applyTorchRecommendationDraft = (values) => {
      torchCompileEnabled.checked = values.enabled;
      torchCompileBackend.value = values.backend;
      torchCompileFullgraph.checked = values.fullgraph;
      torchCompileMode.value = values.mode;
      torchCompileDynamic.value = values.dynamic;
      torchCompileBlocksOnly.checked = values.compile_transformer_blocks_only;
      torchCompileCache.value = String(values.dynamo_cache_size_limit);
      torchCompileDebug.checked = values.debug_compile_keys;
      torchCompileDisableVram.checked = values.disable_dynamic_vram;
      refreshTorchDetails();
    };
    const displayRecommendationValue = (value) => (
      value === undefined || value === null || value === "" ? "—" : String(value)
    );
    const recommendationLines = (result, changes = null) => {
      const vram = result.environment.totalVramMb == null
        ? "unknown"
        : `${result.environment.totalVramMb} MiB`;
      return [
        aioFormat("status.torchCompileProfile", { profile: result.profile }),
        aioFormat("status.torchCompileEnvironment", {
          accelerator: result.environment.accelerator,
          vram,
        }),
        ...(Array.isArray(changes) && changes.length
          ? changes.map((change) => aioFormat("status.torchCompileChange", {
              field: change.name,
              current: displayRecommendationValue(change.current),
              recommended: displayRecommendationValue(change.recommended),
            }))
          : (changes === null ? [] : [aioText("status.torchCompileNoChanges")])),
        ...result.reasonCodes.map((code) => aioFormat("status.torchCompileReason", { code })),
        ...result.warnings.map((code) => aioFormat("status.torchCompileWarning", { code })),
      ];
    };
    const showTorchRecommendationStatus = (state, lines) => {
      torchRecommendationStatus.hidden = false;
      torchRecommendationStatus.setAttribute("data-state", state);
      torchRecommendationStatus.textContent = lines.join("\n");
    };
    let recommendationClosed = false;
    let recommendationPending = false;
    torchRecommendButton.addEventListener("click", () => {
      if (recommendationClosed || recommendationPending) {
        return;
      }
      recommendationPending = true;
      torchRecommendButton.disabled = true;
      showTorchRecommendationStatus("loading", [aioText("status.torchCompileLoading")]);
      Promise.resolve()
        .then(() => recommendTorchCompile(settings, {}))
        .then((result) => {
          if (recommendationClosed) {
            return;
          }
          if (!result.supported || !result.values) {
            showTorchRecommendationStatus("unsupported", [
              aioText("status.torchCompileUnsupported"),
              ...recommendationLines(result),
            ]);
            return;
          }
          const changes = torchCompileRecommendationDiff(
            torchControlValues(),
            result.values,
          );
          applyTorchRecommendationDraft(result.values);
          showTorchRecommendationStatus("supported", [
            aioText("status.torchCompileDraftApplied"),
            ...recommendationLines(result, changes),
          ]);
        })
        .catch((error) => {
          if (!recommendationClosed) {
            showTorchRecommendationStatus("error", [
              aioFormat("status.torchCompileRequestFailed", {
                message: error?.message || "unknown error",
              }),
            ]);
          }
        })
        .finally(() => {
          recommendationPending = false;
          if (!recommendationClosed) {
            torchRecommendButton.disabled = false;
          }
        });
    });
    const refreshDaveStageScope = () => {
      const preset = DAVE_STAGE_SCOPE_PRESETS[daveStagePreset.value];
      if (preset) {
        daveFirstPass.checked = preset.first_pass;
        daveHighres.checked = preset.highres;
        daveDetailer.checked = preset.detailer;
        daveUpscale.checked = preset.upscale;
      }
      daveCustomStages.style.display = daveStagePreset.value === "custom" ? "" : "none";
    };
    const refreshSafePagStageScope = () => {
      const preset = SAFE_PAG_STAGE_SCOPE_PRESETS[safePagStagePreset.value];
      if (preset) {
        safePagFirstPass.checked = preset.first_pass;
        safePagHighres.checked = preset.highres;
        safePagDetailer.checked = preset.detailer;
        safePagUpscale.checked = preset.upscale;
      }
      safePagCustomStages.style.display = safePagStagePreset.value === "custom" ? "" : "none";
    };
    const refreshSageStageScope = () => {
      const preset = SAGE_STAGE_SCOPE_PRESETS[sageStagePreset.value];
      if (preset) {
        sageFirstPass.checked = preset.first_pass;
        sageHighres.checked = preset.highres;
        sageDetailer.checked = preset.detailer;
        sageUpscale.checked = preset.upscale;
      }
      refreshSageDetails();
    };
    const setControlsDisabled = (controls, disabled) => {
      for (const control of controls) {
        if (control) {
          control.disabled = disabled;
        }
      }
    };
    const refreshNegPipDependency = () => {
      const mode = ["off", "on", "turbo"].includes(negpipMode.value)
        ? negpipMode.value
        : "off";
      const active = mode !== "off";
      const missing = active && !optionalDependencyAvailable("ppmNegPip");
      const missingMessage = aioFormat("warning.optionalDependencyMissing", {
        backend: `NegPip ${mode}`,
        pack: optionalDependencyPack("ppmNegPip"),
      });
      aioMarkMissingDependencyControl(negpipMode, missing, missingMessage);
      negpipWarning.hidden = !missing && mode !== "turbo";
      negpipWarning.textContent = missing
        ? missingMessage
        : (mode === "turbo" ? aioText("info.negpipTurboCfg") : "");
    };

    const refreshAdvancedDependencyLocks = () => {
      const messages = [];

      const daveMissing = !optionalDependencyAvailable("dave");
      setControlsDisabled([
        daveMask,
        daveStrength,
        daveTau,
        daveStagePreset,
        daveFirstPass,
        daveHighres,
        daveDetailer,
        daveUpscale,
      ], daveMissing);
      const daveMessage = aioFormat("warning.optionalDependencyMissing", {
        backend: "Anima DAVE",
        pack: optionalDependencyPack("dave"),
      });
      aioMarkMissingDependencyControl(daveEnabled, daveMissing, daveMessage);
      if (daveMissing && daveEnabled.checked) {
        daveEnabled.checked = false;
      }
      if (daveMissing) {
        messages.push(aioFormat("warning.optionalDependencyMissing", {
          backend: "Anima DAVE",
          pack: optionalDependencyPack("dave"),
        }));
      }

      const safePagMissing = !optionalDependencyAvailable("safePag");
      setControlsDisabled([
        safePagStagePreset,
        safePagFirstPass,
        safePagHighres,
        safePagDetailer,
        safePagUpscale,
        safePagScale,
        safePagBlocks,
        safePagPerturbation,
        safePagHeads,
        safePagStart,
        safePagEnd,
        safePagRescale,
        safePagRescaleMode,
      ], safePagMissing);
      const safePagMessage = aioFormat("warning.optionalDependencyMissing", {
        backend: "Anima Safe PAG",
        pack: optionalDependencyPack("safePag"),
      });
      aioMarkMissingDependencyControl(safePagEnabled, safePagMissing, safePagMessage);
      if (safePagMissing && safePagEnabled.checked) {
        safePagEnabled.checked = false;
      }
      if (safePagMissing) {
        messages.push(aioFormat("warning.optionalDependencyMissing", {
          backend: "Anima Safe PAG",
          pack: optionalDependencyPack("safePag"),
        }));
      }

      const kjFp16Missing = !optionalDependencyAvailable("kjFp16");
      const kjFp16Message = aioFormat("warning.optionalDependencyMissing", {
        backend: "KJNodes FP16 accum",
        pack: optionalDependencyPack("kjFp16"),
      });
      aioMarkMissingDependencyControl(fp16Accum, kjFp16Missing, kjFp16Message);
      if (kjFp16Missing && fp16Accum.checked) {
        fp16Accum.checked = false;
      }
      if (kjFp16Missing) {
        messages.push(aioFormat("warning.optionalDependencyMissing", {
          backend: "KJNodes FP16 accum",
          pack: optionalDependencyPack("kjFp16"),
        }));
      }

      const kjSageMissing = !optionalDependencyAvailable("kjSage");
      setControlsDisabled([
        sageAllowCompile,
        sageStagePreset,
        sageFirstPass,
        sageHighres,
        sageDetailer,
        sageUpscale,
      ], kjSageMissing);
      const kjSageMessage = aioFormat("warning.optionalDependencyMissing", {
        backend: "SageAttention",
        pack: optionalDependencyPack("kjSage"),
      });
      aioMarkMissingDependencyControl(sageAttention, kjSageMissing, kjSageMessage);
      if (kjSageMissing && sageAttention.value !== "disabled") {
        sageAttention.value = "disabled";
        sageAllowCompile.checked = false;
      }
      if (kjSageMissing) {
        messages.push(aioFormat("warning.optionalDependencyMissing", {
          backend: "SageAttention",
          pack: optionalDependencyPack("kjSage"),
        }));
      }

      const kjCompileMissing = !optionalDependencyAvailable("kjTorchCompile");
      setControlsDisabled([
        torchCompileBackend,
        torchCompileFullgraph,
        torchCompileMode,
        torchCompileDynamic,
        torchCompileBlocksOnly,
        torchCompileCache,
        torchCompileDebug,
        torchCompileDisableVram,
      ], kjCompileMissing);
      const kjCompileMessage = aioFormat("warning.optionalDependencyMissing", {
        backend: "Torch Compile",
        pack: optionalDependencyPack("kjTorchCompile"),
      });
      aioMarkMissingDependencyControl(torchCompileEnabled, kjCompileMissing, kjCompileMessage);
      if (kjCompileMissing && torchCompileEnabled.checked) {
        torchCompileEnabled.checked = false;
      }
      if (kjCompileMissing) {
        messages.push(aioFormat("warning.optionalDependencyMissing", {
          backend: "Torch Compile",
          pack: optionalDependencyPack("kjTorchCompile"),
        }));
      }

      modelWarning.hidden = messages.length === 0;
      modelWarning.textContent = messages.join(" ");
      refreshDaveStageScope();
      refreshSafePagStageScope();
      refreshSageStageScope();
      refreshSageDetails();
      refreshTorchDetails();
    };
    const guardToggle = (control, dependencyKey, backend) => {
      if (control.checked && !optionalDependencyAvailable(dependencyKey)) {
        notifyMissingDependency(backend, [dependencyKey]);
        control.checked = false;
      }
      refreshAdvancedDependencyLocks();
    };
    daveEnabled.addEventListener("change", () => guardToggle(daveEnabled, "dave", "Anima DAVE"));
    daveStagePreset.addEventListener("change", refreshDaveStageScope);
    safePagEnabled.addEventListener("change", () => guardToggle(safePagEnabled, "safePag", "Anima Safe PAG"));
    safePagStagePreset.addEventListener("change", refreshSafePagStageScope);
    fp16Accum.addEventListener("change", () => guardToggle(fp16Accum, "kjFp16", "KJNodes FP16 accum"));
    sageAttention.addEventListener("change", () => {
      if (sageAttention.value !== "disabled" && !optionalDependencyAvailable("kjSage")) {
        notifyMissingDependency("SageAttention", ["kjSage"]);
        sageAttention.value = "disabled";
        sageAllowCompile.checked = false;
      }
      refreshAdvancedDependencyLocks();
    });
    sageStagePreset.addEventListener("change", refreshSageStageScope);
    torchCompileEnabled.addEventListener("change", () => guardToggle(
      torchCompileEnabled,
      "kjTorchCompile",
      "Torch Compile",
    ));
    negpipMode.addEventListener("change", () => {
      if (negpipMode.value !== "off" && !optionalDependencyAvailable("ppmNegPip")) {
        notifyMissingDependency(`NegPip ${negpipMode.value}`, ["ppmNegPip"]);
      }
      refreshNegPipDependency();
    });
    refreshDaveStageScope();
    refreshSafePagStageScope();
    refreshSageStageScope();
    refreshSageDetails();
    refreshTorchDetails();
    refreshNegPipDependency();
    refreshAdvancedDependencyLocks();
    loadGeneratorOptionalDependencies().then(() => {
      refreshNegPipDependency();
      refreshAdvancedDependencyLocks();
    });

    const cancel = document.createElement("button");
    cancel.textContent = aioText("button.cancel");
    const apply = document.createElement("button");
    apply.className = "primary";
    apply.textContent = aioText("button.apply");
    actions.append(cancel, apply);
    cancel.addEventListener("click", () => {
      recommendationClosed = true;
      backdrop.remove();
    });
    apply.addEventListener("click", () => {
      recommendationClosed = true;
      const next = mergeDefaults(DEFAULT_GENERATION_SETTINGS, settings);
      delete next.sampler.dave;
      next.negpip ||= {};
      next.negpip.mode = ["off", "on", "turbo"].includes(negpipMode.value)
        ? negpipMode.value
        : "off";
      delete next.model_patches.aura_flow.enabled;
      next.model_patches.aura_flow.shift = clampGeneratorNumber(
        auraShift.value,
        DEFAULT_GENERATION_SETTINGS.model_patches.aura_flow.shift,
        GENERATOR_NUMERIC_LIMITS.auraFlowShift.min,
        GENERATOR_NUMERIC_LIMITS.auraFlowShift.max,
      );
      next.model_patches.dave.enabled = daveEnabled.checked && optionalDependencyAvailable("dave");
      next.model_patches.dave.mask = daveMask.value || "dave_alpha.npz";
      next.model_patches.dave.strength = Number(daveStrength.value || 0.30);
      next.model_patches.dave.tau = Number(daveTau.value || 0.10);
      const davePresetScope = DAVE_STAGE_SCOPE_PRESETS[daveStagePreset.value];
      next.model_patches.dave.stage_scope = davePresetScope
        ? { ...davePresetScope }
        : {
            first_pass: daveFirstPass.checked,
            highres: daveHighres.checked,
            detailer: daveDetailer.checked,
            upscale: daveUpscale.checked,
          };
      next.model_patches.safe_pag ||= {};
      next.model_patches.safe_pag.enabled = safePagEnabled.checked && optionalDependencyAvailable("safePag");
      const safePagPresetScope = SAFE_PAG_STAGE_SCOPE_PRESETS[safePagStagePreset.value];
      next.model_patches.safe_pag.stage_scope = safePagPresetScope
        ? { ...safePagPresetScope }
        : {
            first_pass: safePagFirstPass.checked,
            highres: safePagHighres.checked,
            detailer: safePagDetailer.checked,
            upscale: safePagUpscale.checked,
          };
      next.model_patches.safe_pag.scale = clampGeneratorNumber(safePagScale.value, 4.0, 0, 100);
      next.model_patches.safe_pag.block_indices = safePagBlocks.value || "18";
      next.model_patches.safe_pag.perturbation_strength = clampGeneratorNumber(
        safePagPerturbation.value,
        0.75,
        0,
        1,
      );
      next.model_patches.safe_pag.head_indices = safePagHeads.value || "";
      next.model_patches.safe_pag.start_percent = clampGeneratorNumber(safePagStart.value, 0.0, 0, 1);
      next.model_patches.safe_pag.end_percent = clampGeneratorNumber(safePagEnd.value, 0.7, 0, 1);
      next.model_patches.safe_pag.rescale = clampGeneratorNumber(safePagRescale.value, 0.2, 0, 1);
      next.model_patches.safe_pag.rescale_mode = safePagRescaleMode.value || "full";
      next.model_patches.kj.fp16_accumulation = fp16Accum.checked && optionalDependencyAvailable("kjFp16");
      next.model_patches.kj.sage_attention = optionalDependencyAvailable("kjSage")
        ? (sageAttention.value || "disabled")
        : "disabled";
      next.model_patches.kj.sage_allow_compile = sageAllowCompile.checked
        && optionalDependencyAvailable("kjSage");
      const sagePresetScope = SAGE_STAGE_SCOPE_PRESETS[sageStagePreset.value];
      next.model_patches.kj.sage_stage_scope = sagePresetScope
        ? { ...sagePresetScope }
        : {
            first_pass: sageFirstPass.checked,
            highres: sageHighres.checked,
            detailer: sageDetailer.checked,
            upscale: sageUpscale.checked,
          };
      next.model_patches.kj.torch_compile.enabled = torchCompileEnabled.checked
        && optionalDependencyAvailable("kjTorchCompile");
      next.model_patches.kj.torch_compile.backend = torchCompileBackend.value || "inductor";
      next.model_patches.kj.torch_compile.fullgraph = torchCompileFullgraph.checked;
      next.model_patches.kj.torch_compile.mode = torchCompileMode.value || "max-autotune-no-cudagraphs";
      next.model_patches.kj.torch_compile.dynamic = torchCompileDynamic.value || "false";
      next.model_patches.kj.torch_compile.compile_transformer_blocks_only = torchCompileBlocksOnly.checked;
      next.model_patches.kj.torch_compile.dynamo_cache_size_limit = Number(torchCompileCache.value || 64);
      next.model_patches.kj.torch_compile.debug_compile_keys = torchCompileDebug.checked;
      next.model_patches.kj.torch_compile.disable_dynamic_vram = torchCompileDisableVram.checked;
      next.artist_mix.mode = artistMode.value || "prompt_data";
      next.artist_mix.start_percent = Number(artistStart.value || 0.5);
      next.artist_mix.strength_scale = Number(artistStrength.value || 1.0);
      writeSettings(node, widget, next);
      renderGeneratorPanel(node);
      backdrop.remove();
    });
  }

  return openAdvancedSettings;
}

