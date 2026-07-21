// @ts-check

/**
 * @typedef {object} AioSamplerDialogControls
 * @property {(title: any, subtitle: any) => {backdrop: any, body: any, actions: any}} createDialog
 * @property {(section: any, label: any, control: any, tooltipKey?: string) => any} field
 * @property {(value: any, step?: string) => any} numberInput
 * @property {(options: any[], value: any) => any} selectInput
 * @property {(value: any) => any} checkbox
 * @property {(value: any) => any} textInput
 * @property {(spec: any, current: any) => any} nodeInputControlForSpec
 * @property {(control: any) => any} valueFromNodeInputControl
 */

/**
 * @typedef {object} AioSamplerDialogText
 * @property {(value: any) => string} staticText
 * @property {(key: string) => string} get
 * @property {(key: string, values?: Record<string, any>) => string} format
 * @property {(element: any, value: any) => any} applyTooltipText
 */

/**
 * @typedef {object} AioSamplerDialogSettingsCore
 * @property {any} defaultGenerationSettings
 * @property {any[]} seedControls
 * @property {number} specialSeedRandom
 * @property {any[]} fallbackSamplerNames
 * @property {any[]} fallbackSchedulerNames
 * @property {(defaults: any, current: any) => any} mergeDefaults
 * @property {(value: any) => string} normalizeSeedControl
 * @property {(value: any, fallback: number) => number} normalizeSeedValue
 * @property {(value: any, fallback: number, min: number, max: number) => number} clampNumber
 */

/**
 * @typedef {object} AioSamplerDialogNodeAdapter
 * @property {string} generatorSettingsWidget
 * @property {(node: any, name: string) => any} findWidget
 * @property {(widget: any, defaults: any) => any} parseSettings
 * @property {(node: any, settings: any) => any} mergeVisibleSettings
 * @property {(node: any, name: string, fallback: any[]) => any[]} widgetOptions
 * @property {(node: any, settings: any) => void} applyVisibleSettings
 * @property {(node: any, widget: any, settings: any) => void} writeSettings
 * @property {(node: any) => void} renderPanel
 */

/**
 * @typedef {object} AioSamplerDialogDependencyAdapter
 * @property {Record<string, string>} backendDependencies
 * @property {() => boolean} isLoaded
 * @property {(key: string) => boolean} available
 * @property {(key: string) => string} pack
 * @property {(key: string) => Record<string, any>} nodeInputMap
 * @property {(key: string, inputName: string) => string} nodeInputTooltip
 * @property {(key: string, inputName: string) => boolean} nodeInputSupported
 * @property {(control: any, missing: boolean, message?: string) => void} markMissingControl
 * @property {(backend: string, keys: string[]) => boolean} notifyMissing
 * @property {(options?: Record<string, any>) => Promise<any>} load
 */

/**
 * @typedef {object} AioSamplerSettingsDialogDependencies
 * @property {any} document
 * @property {AioSamplerDialogControls} controls
 * @property {AioSamplerDialogText} text
 * @property {AioSamplerDialogSettingsCore} settingsCore
 * @property {AioSamplerDialogNodeAdapter} nodeAdapter
 * @property {AioSamplerDialogDependencyAdapter} dependencyAdapter
 */

const SPECTRUM_ADVANCED_KNOWN_INPUTS = new Set([
  "model",
  "clip",
  "seed",
  "steps",
  "cfg",
  "sampler_name",
  "scheduler",
  "positive",
  "negative",
  "latent_image",
  "adapter",
  "quality_tags",
  "mod_w",
  "quality_neg",
  "mod_start_layer",
  "mod_end_layer",
  "mod_taper",
  "mod_taper_scale",
  "mod_final_w",
  "denoise",
  "window_size",
  "flex_window",
  "warmup_steps",
  "blend_w",
  "cheby_degree",
  "ridge_lambda",
  "dcw_mode",
  "dcw_lambda",
  "dcw_band_mask",
  "dcw_calibrator",
  "cfgpp_lambda",
  "fsg",
  "fsg_band_lo",
  "fsg_band_hi",
  "fsg_k",
  "fsg_d_sigma",
  "fsg_gamma",
  "adaptive_smc_alpha",
  "smc_cfg_lambda",
]);
const SPECTRUM_SPD_KNOWN_INPUTS = new Set([
  "model",
  "seed",
  "steps",
  "cfg",
  "sampler_name",
  "scheduler",
  "positive",
  "negative",
  "latent_image",
  "split_mode",
  "spd_scale",
  "spd_sigma",
  "denoise",
  "adaptive_smc_alpha",
]);

/**
 * Own the Sampler settings dialog, dynamic optional-node inputs, dependency
 * locks, and Apply/Cancel lifecycle. Extension registration, dependency
 * discovery, generator-panel rendering, and durable storage remain adapters.
 *
 * @param {AioSamplerSettingsDialogDependencies} dependencies
 * @returns {(node: any) => void}
 */
export function aioCreateSamplerSettingsDialog(dependencies) {
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
    selectInput,
    checkbox,
    textInput,
    nodeInputControlForSpec,
    valueFromNodeInputControl,
  } = controls;
  const {
    staticText: aioStaticText,
    get: aioText,
    format: aioFormat,
    applyTooltipText,
  } = text;
  const {
    defaultGenerationSettings: DEFAULT_GENERATION_SETTINGS,
    seedControls: GENERATOR_SEED_CONTROLS,
    specialSeedRandom: GENERATOR_SPECIAL_SEED_RANDOM,
    fallbackSamplerNames: GENERATOR_FALLBACK_SAMPLER_NAMES,
    fallbackSchedulerNames: GENERATOR_FALLBACK_SCHEDULER_NAMES,
    mergeDefaults,
    normalizeSeedControl,
    normalizeSeedValue,
    clampNumber: clampGeneratorNumber,
  } = settingsCore;
  const {
    generatorSettingsWidget: GENERATOR_SETTINGS_WIDGET,
    findWidget,
    parseSettings,
    mergeVisibleSettings: mergeVisibleGeneratorSettings,
    widgetOptions,
    applyVisibleSettings: applyVisibleGeneratorSettings,
    writeSettings,
    renderPanel: renderGeneratorPanel,
  } = nodeAdapter;
  const {
    backendDependencies: AIO_BACKEND_DEPENDENCIES,
    isLoaded: optionalDependenciesLoaded,
    available: optionalDependencyAvailable,
    pack: optionalDependencyPack,
    nodeInputMap,
    nodeInputTooltip,
    nodeInputSupported,
    markMissingControl: aioMarkMissingDependencyControl,
    notifyMissing: notifyMissingDependency,
    load: loadGeneratorOptionalDependencies,
  } = dependencyAdapter;

  function applyNodeInputInfo(control, dependencyKey, inputName, fallbackTooltipKey = "") {
    if (!control) {
      return control;
    }
    const objectTooltip = nodeInputTooltip(dependencyKey, inputName);
    const fallback = fallbackTooltipKey ? aioText(fallbackTooltipKey) : "";
    const supported = nodeInputSupported(dependencyKey, inputName);
    control.disabled = !supported;
    control.title = supported
      ? (objectTooltip || fallback || control.title || "")
      : aioFormat("warning.optionalDependencyMissing", {
        backend: inputName,
        pack: optionalDependencyPack(dependencyKey),
      });
    const row = control.parentElement?.classList?.contains("easyuse-anima-aio-field")
      ? control.parentElement
      : null;
    if (row) {
      row.title = control.title;
      row.classList.toggle("easyuse-anima-aio-unsupported", !supported);
    }
    return control;
  }

  function createDynamicNodeInputEditor(title, dependencyKey, knownInputs, values = {}) {
    const section = document.createElement("div");
    section.className = "easyuse-anima-aio-subsection";
    section.append(Object.assign(document.createElement("h4"), { textContent: aioStaticText(title) }));
    const controls = new Map();
    const currentValues = new Map(
      values && typeof values === "object" && !Array.isArray(values)
        ? Object.entries(values)
        : [],
    );
    const render = () => {
      for (const [name, control] of controls.entries()) {
        currentValues.set(name, valueFromNodeInputControl(control));
      }
      controls.clear();
      section.replaceChildren(Object.assign(document.createElement("h4"), { textContent: aioStaticText(title) }));
      if (!optionalDependenciesLoaded() || !optionalDependencyAvailable(dependencyKey)) {
        section.classList.add("hidden");
        return;
      }
      const inputMap = nodeInputMap(dependencyKey);
      const dynamicNames = Object.keys(inputMap).filter((name) => !knownInputs.has(name));
      if (!dynamicNames.length) {
        section.classList.add("hidden");
        return;
      }
      section.classList.remove("hidden");
      for (const name of dynamicNames) {
        const spec = inputMap[name];
        const control = nodeInputControlForSpec(spec, currentValues.get(name));
        if (!control) {
          continue;
        }
        controls.set(name, control);
        field(section, name, control);
        applyTooltipText(control, nodeInputTooltip(dependencyKey, name));
      }
      if (!controls.size) {
        section.classList.add("hidden");
      }
    };
    render();
    loadGeneratorOptionalDependencies().then(render);
    return {
      section,
      values() {
        const output = new Map(currentValues);
        for (const [name, control] of controls.entries()) {
          output.set(name, valueFromNodeInputControl(control));
        }
        return Object.fromEntries(output);
      },
    };
  }


  function openSamplerSettings(node) {
    const widget = findWidget(node, GENERATOR_SETTINGS_WIDGET);
    const settings = mergeVisibleGeneratorSettings(node, parseSettings(widget, DEFAULT_GENERATION_SETTINGS));
    const { backdrop, body, actions } = createDialog(
      "Sampler Details",
      "Choose one of three sampler paths. Selecting an unavailable path shows its required node pack."
    );

    const makeSection = (title, className = "easyuse-anima-aio-section full") => {
      const section = document.createElement("section");
      section.className = className;
      section.append(Object.assign(document.createElement("h3"), { textContent: aioStaticText(title) }));
      return section;
    };
    const makeSubsection = (title) => {
      const section = document.createElement("div");
      section.className = "easyuse-anima-aio-subsection";
      section.append(Object.assign(document.createElement("h4"), { textContent: aioStaticText(title) }));
      return section;
    };

    const base = makeSection("Base Parameters");
    const seed = field(base, "Seed", numberInput(settings.sampler.seed));
    const seedControl = field(
      base,
      "Seed mode",
      selectInput(GENERATOR_SEED_CONTROLS, normalizeSeedControl(settings.sampler.seed_after_generate))
    );
    const steps = field(base, "Steps", numberInput(settings.sampler.steps));
    steps.min = "1";
    steps.max = "75";
    const cfg = field(base, "CFG", numberInput(settings.sampler.cfg, "0.1"));
    cfg.min = "1";
    cfg.max = "10";
    const denoise = field(base, "Denoise", numberInput(settings.sampler.denoise, "0.01"));

    const sampler = makeSection("Sampler Backend");
    const backendValues = [
      "comfy_ksampler",
      "spectrum_mod_guidance_advanced",
      "spectrum_spd_speed",
    ];
    const backend = field(
      sampler,
      "Mode",
      selectInput(backendValues, settings.sampler.backend || "comfy_ksampler")
    );
    const dependencyWarning = document.createElement("div");
    dependencyWarning.className = "easyuse-anima-aio-warning";
    dependencyWarning.hidden = true;
    sampler.append(dependencyWarning);
    const samplerName = field(
      sampler,
      "Sampler",
      selectInput(widgetOptions(node, "sampler_name", GENERATOR_FALLBACK_SAMPLER_NAMES), settings.sampler.sampler_name)
    );
    const scheduler = field(
      sampler,
      "Scheduler",
      selectInput(widgetOptions(node, "scheduler", GENERATOR_FALLBACK_SCHEDULER_NAMES), settings.sampler.scheduler)
    );

    const modGuidance = makeSubsection("Mod Guidance");
    const modMode = field(
      modGuidance,
      "Mode",
      selectInput(["prompt_data", "enabled", "disabled"], settings.mod_guidance.mode),
      "tip.modMode",
    );
    const modProfile = field(
      modGuidance,
      "Profile",
      selectInput(["off", "step_i8_skip27", "step_i14", "uniform_w3"], settings.mod_guidance.profile)
    );
    const modAdvanced = document.createElement("div");
    modGuidance.append(modAdvanced);
    const modAdapter = field(modAdvanced, "Adapter", textInput(settings.mod_guidance.advanced.adapter));
    const modW = field(modAdvanced, "Mod W", numberInput(settings.mod_guidance.advanced.mod_w, "0.1"));
    const modStart = field(modAdvanced, "Start layer", numberInput(settings.mod_guidance.advanced.mod_start_layer));
    const modEnd = field(modAdvanced, "End layer", numberInput(settings.mod_guidance.advanced.mod_end_layer));
    const modTaper = field(modAdvanced, "Taper", numberInput(settings.mod_guidance.advanced.mod_taper));
    const modTaperScale = field(modAdvanced, "Taper scale", numberInput(settings.mod_guidance.advanced.mod_taper_scale, "0.05"));
    const modFinalW = field(modAdvanced, "Final W", numberInput(settings.mod_guidance.advanced.mod_final_w, "0.1"));
    sampler.append(modGuidance);

    const backendDetails = document.createElement("div");
    const spectrum = makeSubsection("Spectrum Patch / Advanced Sampler");
    const spectrumPatchEnabled = field(spectrum, "Use Spectrum patch", checkbox(settings.sampler.spectrum.enabled));
    const windowSize = field(spectrum, "Window size", numberInput(settings.sampler.spectrum.window_size, "0.25"));
    const flexWindow = field(spectrum, "Flex window", numberInput(settings.sampler.spectrum.flex_window, "0.05"));
    const warmupSteps = field(spectrum, "Warmup steps", numberInput(settings.sampler.spectrum.warmup_steps));
    const tailSteps = field(spectrum, "Tail actual", numberInput(settings.sampler.spectrum.tail_actual_steps));
    const blendW = field(spectrum, "Blend W", numberInput(settings.sampler.spectrum.blend_w, "0.05"));
    const chebyDegree = field(spectrum, "Cheby degree", numberInput(settings.sampler.spectrum.cheby_degree));
    const ridgeLambda = field(spectrum, "Ridge lambda", numberInput(settings.sampler.spectrum.ridge_lambda, "0.01"));
    const spectrumCompat = field(
      spectrum,
      "Compat policy",
      selectInput(["conservative", "legacy", "strict"], settings.sampler.spectrum.compat_policy || "conservative")
    );

    const corrections = makeSubsection("Spectrum Advanced Corrections");
    const correctionsEnabled = field(corrections, "Use corrections", checkbox(settings.sampler.dit_corrections.enabled));
    const dcwMode = field(corrections, "DCW mode", selectInput(["off", "manual", "auto"], settings.sampler.dit_corrections.dcw_mode));
    const dcwLambda = field(corrections, "DCW lambda", numberInput(settings.sampler.dit_corrections.dcw_lambda, "0.001"));
    const dcwBand = field(corrections, "DCW band", selectInput(["LL", "all", "HH", "LH+HL+HH"], settings.sampler.dit_corrections.dcw_band_mask));
    const smcCfg = field(corrections, "SMC-CFG", checkbox(settings.sampler.dit_corrections.smc_cfg));
    const smcAlpha = field(corrections, "SMC alpha", numberInput(settings.sampler.dit_corrections.adaptive_smc_alpha, "0.01"));
    const smcLambda = field(corrections, "SMC lambda", numberInput(settings.sampler.dit_corrections.smc_cfg_lambda, "0.1"));
    const cfgpp = field(corrections, "CFG++", checkbox(settings.sampler.dit_corrections.cfgpp));
    const cfgppLambda = field(corrections, "CFG++ lambda", numberInput(settings.sampler.dit_corrections.cfgpp_lambda, "0.1"));
    const fsg = field(corrections, "FSG", checkbox(settings.sampler.dit_corrections.fsg));
    spectrum.append(corrections);
    const spectrumExtra = createDynamicNodeInputEditor(
      "Detected Spectrum Inputs",
      "spectrumAdvanced",
      SPECTRUM_ADVANCED_KNOWN_INPUTS,
      settings.sampler.spectrum_extra || {},
    );
    spectrum.append(spectrumExtra.section);

    const spd = makeSubsection("Spectrum + SPD / SPEED");
    const spdScale = field(spd, "Scale", numberInput(settings.sampler.spd.scale, "0.05"));
    const spdSigma = field(spd, "Sigma", numberInput(settings.sampler.spd.sigma, "0.01"));
    const spdSmc = field(spd, "SMC alpha", numberInput(settings.sampler.spd.adaptive_smc_alpha, "0.01"));
    const spdExtra = createDynamicNodeInputEditor(
      "Detected SPD Inputs",
      "spectrumSpd",
      SPECTRUM_SPD_KNOWN_INPUTS,
      settings.sampler.spd_extra || {},
    );
    spd.append(spdExtra.section);
    backendDetails.append(spectrum, spd);
    sampler.append(backendDetails);
    body.append(base, sampler);

    const refreshBackendDetails = () => {
      const isComfy = backend.value === "comfy_ksampler";
      const isSpectrumAdvanced = backend.value === "spectrum_mod_guidance_advanced";
      spectrum.classList.toggle("hidden", !(isComfy || isSpectrumAdvanced));
      spectrumPatchEnabled.parentElement.style.display = isComfy ? "" : "none";
      spectrumCompat.parentElement.style.display = isComfy ? "" : "none";
      modAdvanced.style.display = isSpectrumAdvanced ? "" : "none";
      spd.classList.toggle("hidden", backend.value !== "spectrum_spd_speed");
    };
    const refreshDependencyLocks = () => {
      const messages = [];
      for (const option of Array.from(backend.options)) {
        const dependencyKey = AIO_BACKEND_DEPENDENCIES[option.value];
        const pack = optionalDependencyPack(dependencyKey);
        const missing = !!dependencyKey && !optionalDependencyAvailable(dependencyKey);
        option.disabled = false;
        option.textContent = missing ? `${option.value} (${pack} missing)` : option.value;
        option.classList?.toggle("easyuse-anima-aio-missing-option", missing);
        option.title = missing
          ? aioFormat("warning.optionalDependencyMissing", { backend: option.value, pack })
          : "";
        if (missing && option.selected) {
          messages.push(aioFormat("warning.optionalDependencyMissing", {
            backend: option.value,
            pack,
          }));
          backend.value = "comfy_ksampler";
        }
      }
      const spectrumPatchMissing = !optionalDependencyAvailable("spectrumPatch");
      const spectrumPatchMessage = aioFormat("warning.optionalDependencyMissing", {
        backend: "Spectrum Patch",
        pack: optionalDependencyPack("spectrumPatch"),
      });
      aioMarkMissingDependencyControl(spectrumPatchEnabled, spectrumPatchMissing, spectrumPatchMessage);
      aioMarkMissingDependencyControl(correctionsEnabled, spectrumPatchMissing, spectrumPatchMessage);
      const spectrumInputDependency = backend.value === "comfy_ksampler" ? "spectrumPatch" : "spectrumAdvanced";
      const correctionInputDependency = backend.value === "comfy_ksampler" ? "spectrumCorrections" : "spectrumAdvanced";
      const spectrumControls = [
        [windowSize, "window_size", "tip.spectrumWindow"],
        [flexWindow, "flex_window", "tip.spectrumFlex"],
        [warmupSteps, "warmup_steps", "tip.spectrumWarmup"],
        [tailSteps, "tail_actual_steps", "tip.spectrumTail"],
        [blendW, "blend_w", "tip.spectrumBlend"],
        [chebyDegree, "cheby_degree", "tip.spectrumCheby"],
        [ridgeLambda, "ridge_lambda", "tip.spectrumRidge"],
        [dcwMode, "dcw_mode", "tip.dcwMode"],
        [dcwLambda, "dcw_lambda", "tip.dcwLambda"],
        [dcwBand, "dcw_band_mask", "tip.dcwBand"],
        [cfgppLambda, "cfgpp_lambda", "tip.cfgppLambda"],
        [fsg, "fsg", "tip.fsg"],
        [smcAlpha, "adaptive_smc_alpha", "tip.smcAlpha"],
        [smcLambda, "smc_cfg_lambda", "tip.smcLambda"],
      ];
      for (const [control, inputName, tooltipKey] of spectrumControls.slice(0, 7)) {
        applyNodeInputInfo(control, spectrumInputDependency, inputName, tooltipKey);
      }
      for (const [control, inputName, tooltipKey] of spectrumControls.slice(7)) {
        applyNodeInputInfo(control, correctionInputDependency, inputName, tooltipKey);
      }
      applyNodeInputInfo(spdScale, "spectrumSpd", "spd_scale", "tip.spdScale");
      applyNodeInputInfo(spdSigma, "spectrumSpd", "spd_sigma", "tip.spdSigma");
      applyNodeInputInfo(spdSmc, "spectrumSpd", "adaptive_smc_alpha", "tip.smcAlpha");
      if (spectrumPatchMissing && (spectrumPatchEnabled.checked || correctionsEnabled.checked)) {
        messages.push(aioFormat("warning.optionalDependencyMissing", {
          backend: "Spectrum Patch",
          pack: optionalDependencyPack("spectrumPatch"),
        }));
        spectrumPatchEnabled.checked = false;
        correctionsEnabled.checked = false;
      }
      dependencyWarning.hidden = messages.length === 0;
      dependencyWarning.textContent = messages.join(" ");
      refreshBackendDetails();
    };
    backend.addEventListener("change", () => {
      const dependencyKey = AIO_BACKEND_DEPENDENCIES[backend.value];
      if (dependencyKey && !optionalDependencyAvailable(dependencyKey)) {
        notifyMissingDependency(backend.value, [dependencyKey]);
        backend.value = "comfy_ksampler";
      }
      refreshDependencyLocks();
    });
    const guardSpectrumToggle = (control) => {
      if (control.checked && !optionalDependencyAvailable("spectrumPatch")) {
        notifyMissingDependency("Spectrum Patch", ["spectrumPatch"]);
        control.checked = false;
      }
      refreshDependencyLocks();
    };
    spectrumPatchEnabled.addEventListener("change", () => guardSpectrumToggle(spectrumPatchEnabled));
    correctionsEnabled.addEventListener("change", () => guardSpectrumToggle(correctionsEnabled));
    refreshBackendDetails();
    refreshDependencyLocks();
    loadGeneratorOptionalDependencies().then(refreshDependencyLocks);

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
      const selectedBackend = backend.value || "comfy_ksampler";
      const selectedBackendDependency = AIO_BACKEND_DEPENDENCIES[selectedBackend];
      next.sampler.backend = selectedBackendDependency
        && !optionalDependencyAvailable(selectedBackendDependency)
        ? "comfy_ksampler"
        : selectedBackend;
      next.sampler.seed = normalizeSeedValue(seed.value, GENERATOR_SPECIAL_SEED_RANDOM);
      next.sampler.seed_after_generate = normalizeSeedControl(seedControl.value);
      next.sampler.steps = Math.trunc(clampGeneratorNumber(steps.value, DEFAULT_GENERATION_SETTINGS.sampler.steps, 1, 75));
      next.sampler.cfg = clampGeneratorNumber(cfg.value, DEFAULT_GENERATION_SETTINGS.sampler.cfg, 1, 10);
      next.sampler.denoise = clampGeneratorNumber(denoise.value, DEFAULT_GENERATION_SETTINGS.sampler.denoise, 0, 1);
      next.sampler.sampler_name = samplerName.value || DEFAULT_GENERATION_SETTINGS.sampler.sampler_name;
      next.sampler.scheduler = scheduler.value || DEFAULT_GENERATION_SETTINGS.sampler.scheduler;
      next.sampler.spectrum.enabled = (
        next.sampler.backend === "spectrum_mod_guidance_advanced"
        || (next.sampler.backend === "comfy_ksampler"
          && spectrumPatchEnabled.checked
          && optionalDependencyAvailable("spectrumPatch"))
      );
      next.sampler.spectrum.window_size = Number(windowSize.value || 2);
      next.sampler.spectrum.flex_window = Number(flexWindow.value || 0.25);
      next.sampler.spectrum.warmup_steps = Number(warmupSteps.value || 6);
      next.sampler.spectrum.tail_actual_steps = Number(tailSteps.value || 3);
      next.sampler.spectrum.blend_w = Number(blendW.value || 0.3);
      next.sampler.spectrum.cheby_degree = Number(chebyDegree.value || 3);
      next.sampler.spectrum.ridge_lambda = Number(ridgeLambda.value || 0.1);
      next.sampler.spectrum.compat_policy = spectrumCompat.value || "conservative";
      next.sampler.spd.scale = Number(spdScale.value || 0.5);
      next.sampler.spd.sigma = Number(spdSigma.value || 0.7);
      next.sampler.spd.adaptive_smc_alpha = Number(spdSmc.value || 0);
      next.sampler.spectrum_extra = spectrumExtra.values();
      next.sampler.spd_extra = spdExtra.values();
      next.sampler.dit_corrections.enabled = correctionsEnabled.checked
        && optionalDependencyAvailable("spectrumPatch");
      next.sampler.dit_corrections.dcw_mode = dcwMode.value || "off";
      next.sampler.dit_corrections.dcw_lambda = Number(dcwLambda.value || 0.01);
      next.sampler.dit_corrections.dcw_band_mask = dcwBand.value || "LL";
      next.sampler.dit_corrections.smc_cfg = smcCfg.checked;
      next.sampler.dit_corrections.adaptive_smc_alpha = Number(smcAlpha.value || 0);
      next.sampler.dit_corrections.smc_cfg_lambda = Number(smcLambda.value || 6);
      next.sampler.dit_corrections.cfgpp = cfgpp.checked;
      next.sampler.dit_corrections.cfgpp_lambda = Number(cfgppLambda.value || 0);
      next.sampler.dit_corrections.fsg = fsg.checked;
      next.mod_guidance.mode = modMode.value || "prompt_data";
      next.mod_guidance.profile = modProfile.value || "step_i8_skip27";
      next.mod_guidance.advanced.adapter = modAdapter.value || "(auto-download default)";
      next.mod_guidance.advanced.mod_w = Number(modW.value || 3);
      next.mod_guidance.advanced.mod_start_layer = Number(modStart.value || 8);
      next.mod_guidance.advanced.mod_end_layer = Number(modEnd.value || 27);
      next.mod_guidance.advanced.mod_taper = Number(modTaper.value || 0);
      next.mod_guidance.advanced.mod_taper_scale = Number(modTaperScale.value || 0.25);
      next.mod_guidance.advanced.mod_final_w = Number(modFinalW.value || 0);
      applyVisibleGeneratorSettings(node, next);
      writeSettings(node, widget, next);
      renderGeneratorPanel(node);
      backdrop.remove();
    });
  }


  return openSamplerSettings;
}
