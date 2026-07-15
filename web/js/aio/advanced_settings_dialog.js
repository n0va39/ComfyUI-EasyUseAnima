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
 * @property {(options?: Record<string, any>) => Promise<any>} load
 */

/**
 * @typedef {object} AioAdvancedSettingsDialogDependencies
 * @property {any} document
 * @property {AioAdvancedDialogControls} controls
 * @property {AioAdvancedDialogText} text
 * @property {AioAdvancedDialogSettingsCore} settingsCore
 * @property {AioAdvancedDialogNodeAdapter} nodeAdapter
 * @property {AioAdvancedDialogDependencyAdapter} dependencyAdapter
 */

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
    load: loadGeneratorOptionalDependencies,
  } = dependencyAdapter;

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

    const modelPatches = document.createElement("section");
    modelPatches.className = "easyuse-anima-aio-section full";
    modelPatches.append(Object.assign(document.createElement("h3"), { textContent: aioStaticText("Model Patch / Optimization") }));

    const auraShift = field(
      modelPatches,
      "AuraFlow shift",
      numberInput(settings.model_patches.aura_flow.shift, "0.5"),
      "tip.shift",
    );
    auraShift.min = "1";
    auraShift.max = "10";

    const dave = makeSubsection("Anima DAVE");
    const daveEnabled = field(dave, "Use DAVE", checkbox(settings.model_patches.dave.enabled), "tip.daveEnabled");
    const daveMask = field(dave, "Mask", textInput(settings.model_patches.dave.mask || "dave_alpha.npz"), "tip.daveMask");
    const daveStrength = field(dave, "DAVE strength", numberInput(settings.model_patches.dave.strength ?? 0.30, "0.01"), "tip.daveStrength");
    const daveTau = field(dave, "DAVE tau", numberInput(settings.model_patches.dave.tau ?? 0.10, "0.01"), "tip.daveTau");
    daveStrength.min = "0";
    daveTau.min = "0";
    daveTau.max = "1";

    const safePag = makeSubsection("Anima Safe PAG");
    const safePagSettings = settings.model_patches.safe_pag || DEFAULT_GENERATION_SETTINGS.model_patches.safe_pag;
    const safePagEnabled = field(safePag, "Use Safe PAG", checkbox(safePagSettings.enabled), "tip.safePagEnabled");
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
        "sageattn",
        "sageattn_qk_int8_pv_fp16_cuda",
        "sageattn_qk_int8_pv_fp8_cuda",
      ], settings.model_patches.kj.sage_attention),
      "tip.kjSageMode",
    );
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
      selectInput(["false", "true", "default"], settings.model_patches.kj.torch_compile.dynamic),
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
    torch.append(torchDetails);
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
      sageAllowCompile.parentElement.style.display = sageAttention.value === "disabled" ? "none" : "";
    };
    const refreshTorchDetails = () => {
      torchDetails.style.display = torchCompileEnabled.checked ? "" : "none";
    };
    const setControlsDisabled = (controls, disabled) => {
      for (const control of controls) {
        if (control) {
          control.disabled = disabled;
        }
      }
    };
    const refreshAdvancedDependencyLocks = () => {
      const messages = [];

      const daveMissing = !optionalDependencyAvailable("dave");
      setControlsDisabled([daveEnabled, daveMask, daveStrength, daveTau], daveMissing);
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
        safePagEnabled,
        safePagScale,
        safePagBlocks,
        safePagPerturbation,
        safePagHeads,
        safePagStart,
        safePagEnd,
        safePagRescale,
        safePagRescaleMode,
      ], safePagMissing);
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
      fp16Accum.disabled = kjFp16Missing;
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
      setControlsDisabled([sageAttention, sageAllowCompile], kjSageMissing);
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
        torchCompileEnabled,
        torchCompileBackend,
        torchCompileFullgraph,
        torchCompileMode,
        torchCompileDynamic,
        torchCompileBlocksOnly,
        torchCompileCache,
        torchCompileDebug,
        torchCompileDisableVram,
      ], kjCompileMissing);
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
      refreshSageDetails();
      refreshTorchDetails();
    };
    sageAttention.addEventListener("change", refreshSageDetails);
    torchCompileEnabled.addEventListener("change", refreshTorchDetails);
    refreshSageDetails();
    refreshTorchDetails();
    refreshAdvancedDependencyLocks();
    loadGeneratorOptionalDependencies().then(refreshAdvancedDependencyLocks);

    const cancel = document.createElement("button");
    cancel.textContent = aioText("button.cancel");
    const apply = document.createElement("button");
    apply.className = "primary";
    apply.textContent = aioText("button.apply");
    actions.append(cancel, apply);
    cancel.addEventListener("click", () => backdrop.remove());
    apply.addEventListener("click", () => {
      const next = mergeDefaults(DEFAULT_GENERATION_SETTINGS, settings);
      delete next.sampler.dave;
      delete next.model_patches.aura_flow.enabled;
      next.model_patches.aura_flow.shift = clampGeneratorNumber(
        auraShift.value,
        DEFAULT_GENERATION_SETTINGS.model_patches.aura_flow.shift,
        1,
        10,
      );
      next.model_patches.dave.enabled = daveEnabled.checked && !daveEnabled.disabled;
      next.model_patches.dave.mask = daveMask.value || "dave_alpha.npz";
      next.model_patches.dave.strength = Number(daveStrength.value || 0.30);
      next.model_patches.dave.tau = Number(daveTau.value || 0.10);
      next.model_patches.safe_pag ||= {};
      next.model_patches.safe_pag.enabled = safePagEnabled.checked && !safePagEnabled.disabled;
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
      next.model_patches.kj.fp16_accumulation = fp16Accum.checked && !fp16Accum.disabled;
      next.model_patches.kj.sage_attention = sageAttention.disabled ? "disabled" : (sageAttention.value || "disabled");
      next.model_patches.kj.sage_allow_compile = sageAllowCompile.checked && !sageAttention.disabled;
      next.model_patches.kj.torch_compile.enabled = torchCompileEnabled.checked && !torchCompileEnabled.disabled;
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

